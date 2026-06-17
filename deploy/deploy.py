#!/usr/bin/env python3
"""
AstrBot 角色一键部署脚本
AstrBot One-Click Character Deployment Script

用法 / Usage:
    python deploy/deploy.py                         # 部署默认角色 (yanami)
    python deploy/deploy.py --character yanami      # 同上，显式指定
    python deploy/deploy.py --character lemon       # 部署其他角色 (需先有 characters/lemon/)
    python deploy/deploy.py --dry-run               # 模拟运行，不修改数据库
"""
import argparse
import json
import os
import shutil
import sqlite3
import subprocess
import sys
import uuid
from datetime import datetime
from pathlib import Path

# ── Constants ──────────────────────────────────────────────────────────────
SCRIPT_DIR = Path(__file__).parent.resolve()
PROJECT_DIR = SCRIPT_DIR.parent
CHARACTERS_DIR = PROJECT_DIR / "characters"
DEFAULT_CHARACTER = "yanami"

# ── ANSI colors ────────────────────────────────────────────────────────────
PINK = "\033[95m"
CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BOLD = "\033[1m"
END = "\033[0m"


def _c(color, text):
    return f"{color}{text}{END}" if sys.stdout.isatty() else text


def info(msg):
    print(f"  [INFO] {msg}")


def ok(msg):
    print(f"  [OK] {msg}")


def warn(msg):
    print(f"  [WARN] {msg}")


def err(msg):
    print(f"  [ERROR] {msg}")


def header(text):
    print(f"\n{_c(PINK + BOLD, '=' * 60)}")
    print(_c(PINK + BOLD, f"  {text}"))
    print(f"{_c(PINK + BOLD, '=' * 60)}\n")


# ── Config Loading ─────────────────────────────────────────────────────────

def load_character(character_id: str) -> dict:
    """Load character config from characters/<id>/character.json."""
    config_path = CHARACTERS_DIR / character_id / "character.json"
    if not config_path.exists():
        err(f"角色配置不存在: {config_path}")
        err(f"可用角色: {list_available_characters()}")
        sys.exit(1)
    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    # Resolve relative paths
    char_dir = CHARACTERS_DIR / character_id
    deploy_section = config.get("deploy", {})
    for key in ["system_prompt", "full_knowledge", "rag"]:
        val = deploy_section.get(key)
        if val:
            deploy_section[key] = str(char_dir / val)

    return config


def is_character_packaged(config: dict) -> bool:
    build = config.get("build", {})
    if build and build.get("status") != "packaged":
        return False
    deploy_section = config.get("deploy", {})
    required = ["system_prompt", "full_knowledge"]
    return all(
        deploy_section.get(key) and Path(deploy_section[key]).exists()
        for key in required
    )


def list_available_characters() -> list:
    """List available character IDs by scanning the characters/ directory."""
    if not CHARACTERS_DIR.exists():
        return []
    return sorted(
        d.name for d in CHARACTERS_DIR.iterdir()
        if d.is_dir() and (d / "character.json").exists()
    )


def resolve_project_path(path: str) -> str:
    """Convert a relative path to absolute using project root."""
    p = Path(path)
    if p.is_absolute():
        return str(p)
    return str(PROJECT_DIR / p)


# ── AstrBot Detection ──────────────────────────────────────────────────────

DATA_DIR_CANDIDATES = [
    Path.home() / "data",
    Path.home() / ".astrbot" / "data",
    Path("C:/Users") / os.environ.get("USERNAME", "") / "data",
    Path(os.environ.get("PROGRAMDATA", "C:/ProgramData")) / "astrbot" / "data",
]


def find_astrbot_data() -> Path | None:
    for candidate in DATA_DIR_CANDIDATES:
        config = candidate / "cmd_config.json"
        if config.exists():
            return candidate
    for root in [Path.home(), Path("C:/Users").resolve()]:
        for p in root.rglob("cmd_config.json"):
            if "astrbot" in str(p).lower():
                return p.parent
    return None


def is_astrbot_running() -> bool:
    try:
        if sys.platform == "win32":
            result = subprocess.run(
                ["tasklist", "/FI", "IMAGENAME eq astrbot.exe"],
                capture_output=True, text=True, timeout=5,
            )
            return "astrbot.exe" in result.stdout
        result = subprocess.run(["pgrep", "-x", "astrbot"], capture_output=True, timeout=5)
        return result.returncode == 0
    except Exception:
        return False


def read_config(data_dir: Path) -> dict | None:
    path = data_dir / "cmd_config.json"
    if not path.exists():
        return None
    with open(path, "r", encoding="utf-8-sig") as f:
        return json.load(f)


# ── Persona Installation ───────────────────────────────────────────────────

def install_persona(data_dir: Path, char_cfg: dict, persona_id_override: str | None = None, dry_run: bool = False) -> bool:
    """Inject character persona into AstrBot's database."""
    db_path = data_dir / "data_v4.db"
    config_path = data_dir / "cmd_config.json"
    deploy_cfg = char_cfg.get("deploy", {})
    persona_name = deploy_cfg.get("persona_name", char_cfg["display_name"])
    system_prompt_path = deploy_cfg.get("system_prompt", "")

    if not db_path.exists():
        err(f"数据库不存在: {db_path}")
        return False

    if not system_prompt_path or not Path(system_prompt_path).exists():
        err(f"System Prompt 文件不存在: {system_prompt_path}")
        return False

    system_prompt = Path(system_prompt_path).read_text(encoding="utf-8").strip()
    info(f"System Prompt: {Path(system_prompt_path).name} ({len(system_prompt)} 字)")

    if dry_run:
        ok(f"[模拟] 将注入人格「{persona_name}」到 AstrBot")
        return True

    # Backup DB
    backup_path = db_path.with_suffix(".db.backup")
    if not backup_path.exists():
        shutil.copy2(db_path, backup_path)
        info(f"数据库已备份: {backup_path}")

    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        now = datetime.now().isoformat()

        # Check if persona already exists
        cur.execute(
            "SELECT p.persona_id, p.id FROM personas p "
            "JOIN persona_folders pf ON p.folder_id = pf.folder_id "
            "WHERE pf.name = ?",
            (persona_name,),
        )
        existing = cur.fetchone()

        persona_id = persona_id_override or str(uuid.uuid4())

        if existing:
            existing_persona_id, existing_row_id = existing
            persona_id = existing_persona_id
            cur.execute(
                "UPDATE personas SET updated_at = ?, system_prompt = ? WHERE id = ?",
                (now, system_prompt, existing_row_id),
            )
            ok(f"人格「{persona_name}」已存在，已更新 System Prompt")
        else:
            # Next IDs
            cur.execute("SELECT COALESCE(MAX(id), 0) + 1 FROM persona_folders")
            folder_id_num = cur.fetchone()[0]
            cur.execute("SELECT COALESCE(MAX(id), 0) + 1 FROM personas")
            pnum = cur.fetchone()[0]

            folder_id = str(uuid.uuid4())
            cur.execute(
                "INSERT INTO persona_folders "
                "(created_at, updated_at, id, folder_id, name, parent_id, description, sort_order) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (now, now, folder_id_num, folder_id, persona_name, None,
                 f"《{char_cfg['work_name']}》{persona_name} 的角色人格", 0),
            )
            cur.execute(
                "INSERT INTO personas "
                "(created_at, updated_at, id, persona_id, system_prompt, begin_dialogs, "
                "tools, skills, custom_error_message, folder_id, sort_order) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (now, now, pnum, persona_id, system_prompt,
                 "[]", None, None, None, folder_id, 0),
            )
            ok(f"人格「{persona_name}」已安装 (persona_id={persona_id})")

        conn.commit()
        conn.close()
    except sqlite3.OperationalError as e:
        err(f"无法写入 AstrBot 数据库: {e}")
        warn("请确认 AstrBot 数据目录可写；如果服务正在占用数据库，请停止 AstrBot 后重试。")
        return False

    # Update cmd_config.json
    try:
        with open(config_path, "r", encoding="utf-8-sig") as f:
            cfg = json.load(f)

        ps = cfg.setdefault("provider_settings", {})
        if persona_id_override:
            ps["default_personality"] = persona_id_override
        else:
            ps["default_personality"] = persona_id

        arr = cfg.setdefault("persona", [])
        found = False
        for p in arr:
            if p.get("name") == persona_name:
                p["system_prompt"] = system_prompt
                found = True
                break
        if not found:
            arr.append({
                "name": persona_name,
                "system_prompt": system_prompt,
                "begin_dialogs": [],
                "model": None,
                "tools": None,
                "skills": None,
            })

        with open(config_path, "w", encoding="utf-8-sig") as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
        ok(f"已设为默认人格")
    except Exception as e:
        warn(f"更新 cmd_config.json 失败: {e}")

    return True


# ── Checks ─────────────────────────────────────────────────────────────────

def check_providers(config: dict):
    providers = config.get("provider", [])
    sources = config.get("provider_sources", [])
    info(f"Provider: {len(providers)} 个模型, {len(sources)} 个数据源")

    has_chat = any(
        "chat_completion" in s.get("provider_type", "")
        or "openai_chat_completion" in s.get("type", "")
        for s in sources
    )
    ok("聊天模型 Provider 正常") if has_chat else warn("未检测到聊天 Provider")

    default = config.get("provider_settings", {}).get("default_provider_id", "N/A")
    info(f"默认模型: {default}")

    has_embed = any("embed" in p.get("id", "").lower() for p in providers)
    ok("Embedding 模型已配置") if has_embed else warn("未配置 Embedding 模型")


def check_kb(data_dir: Path):
    kb_dir = data_dir / "knowledge_base"
    if not kb_dir.exists():
        warn("知识库目录不存在")
        return
    db_path = kb_dir / "kb.db"
    if not db_path.exists():
        warn("知识库数据库不存在")
        return
    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute("SELECT kb_name, doc_count, chunk_count FROM knowledge_bases")
        rows = cur.fetchall()
        conn.close()
        if rows:
            for name, docs, chunks in rows:
                ok(f"知识库「{name}」: {docs} 文档, {chunks} 切块")
        else:
            warn("尚未创建知识库")
    except Exception as e:
        warn(f"读取知识库失败: {e}")


def check_character_files(char_cfg: dict):
    cfg = char_cfg.get("deploy", {})
    checks = [
        ("System Prompt", cfg.get("system_prompt")),
        ("完整知识库", cfg.get("full_knowledge")),
        ("精简知识库", cfg.get("rag")),
    ]
    for name, path in checks:
        if path and Path(path).exists():
            ok(f"{name}: {Path(path).name} ({Path(path).stat().st_size / 1024:.0f} KB)")
        else:
            err(f"{name}: 文件不存在")


# ── Guide ──────────────────────────────────────────────────────────────────

def print_guide(char_cfg: dict):
    deploy_cfg = char_cfg.get("deploy", {})
    persona_name = deploy_cfg.get("persona_name", char_cfg["display_name"])
    kb_name = deploy_cfg.get("knowledge_base_name", char_cfg["character_id"])
    full_kb = deploy_cfg.get("full_knowledge", "")
    rag = deploy_cfg.get("rag", "")

    print(f"\n{_c(GREEN + BOLD, '=' * 60)}")
    print(_c(GREEN + BOLD, f"  「{persona_name}」部署完成！还差 3 步"))
    print(f"{_c(GREEN + BOLD, '=' * 60)}\n")

    print(_c(BOLD, "1. 配置 Embedding Provider (RAG 知识库需要)"))
    print(f"   进 AstrBot 仪表盘 → 模型提供商 → 嵌入 → 新增模型提供商")
    print(f"   选 OpenAI Compatible，填入:")
    print(f"     API Base URL: {_c(CYAN, 'https://api.siliconflow.cn/v1')}")
    print(f"     Model:        {_c(CYAN, 'BAAI/bge-m3')}")
    print(f"     API Key:      去 {_c(CYAN, 'https://siliconflow.cn')} 注册获取 (免费)")
    print()

    print(_c(BOLD, f"2. 上传知识库文档到「{kb_name}」"))
    print(f"   仪表盘 → 知识库 → 新建 (名称: {kb_name})")
    print(f"   选刚配好的 Embedding 模型 → 保存")
    print(f"   进入详情 → 上传文档 → 选:")
    print(f"     {_c(CYAN, full_kb)}")
    if rag:
        print(f"     或精简版 {_c(CYAN, rag)}")
    print()

    print(_c(BOLD, "3. 重启 AstrBot 服务"))
    print(f"   仪表盘右上角重启 / 命令行: {_c(YELLOW, 'Restart-Service AstrBot')}")
    print()


# ── Main ───────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="AstrBot 角色一键部署脚本",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "示例:\n"
            f"  python deploy/deploy.py                          # 部署默认角色 ({DEFAULT_CHARACTER})\n"
            f"  python deploy/deploy.py --character yanami       # 部署八奈见杏菜\n"
            f"  python deploy/deploy.py --character lemon        # 部署其他角色\n"
            f"  python deploy/deploy.py --dry-run                # 模拟运行\n"
        ),
    )
    parser.add_argument(
        "--character", "-c",
        default=None,
        help=f"角色 ID (默认: {DEFAULT_CHARACTER}；多个角色时不指定会提示选择)",
    )
    parser.add_argument(
        "--dry-run", "-n",
        action="store_true",
        help="模拟运行，不修改数据库",
    )
    parser.add_argument(
        "--list", "-l",
        action="store_true",
        help="列出可用角色",
    )
    args = parser.parse_args()

    # Handle --list
    if args.list:
        chars = list_available_characters()
        if chars:
            print("可用角色:")
            for c in chars:
                cfg_path = CHARACTERS_DIR / c / "character.json"
                try:
                    with open(cfg_path, encoding="utf-8") as f:
                        char_data = json.load(f)
                    print(f"  {_c(CYAN, c):20s} {char_data.get('display_name', '')}")
                except Exception:
                    print(f"  {_c(CYAN, c)}")
        else:
            warn("没有找到角色配置")
        return

    character_id = args.character
    if character_id is None:
        chars = list_available_characters()
        if not chars:
            err("没有找到角色配置，请先运行 python character.py init")
            return
        if len(chars) == 1:
            character_id = chars[0]
        else:
            print("可用角色:")
            for index, c in enumerate(chars, start=1):
                cfg = load_character(c)
                print(f"  {index}. {c} - {cfg.get('display_name', '')}")
            default_index = chars.index(DEFAULT_CHARACTER) + 1 if DEFAULT_CHARACTER in chars else 1
            choice = input(f"请选择要部署的角色，回车默认 {default_index}: ").strip()
            if not choice:
                character_id = chars[default_index - 1]
            elif choice.isdigit() and 1 <= int(choice) <= len(chars):
                character_id = chars[int(choice) - 1]
            else:
                character_id = choice

    # Load character
    char_cfg = load_character(character_id)
    persona_name = char_cfg.get("deploy", {}).get("persona_name", char_cfg["display_name"])
    kb_name = char_cfg.get("deploy", {}).get("knowledge_base_name", char_cfg["character_id"])

    if not is_character_packaged(char_cfg):
        warn("该角色部署文件不完整。")
        warn(f"请先运行: python character.py build --character {char_cfg['character_id']}")
        warn(f"如果已经完成 LLM 分析和 profile，再运行: python character.py package --character {char_cfg['character_id']}")
        if not args.dry_run:
            return

    if args.dry_run:
        header(f"[模拟] {persona_name} → AstrBot 部署")
    else:
        header(f"{persona_name} → AstrBot 一键部署")

    info(f"角色: {_c(CYAN, persona_name)} ({char_cfg.get('work_name', '')})")
    info(f"知识库: {_c(CYAN, kb_name)}")
    print()

    # Step 1: Check files
    print(_c(BOLD, "检查角色文件..."))
    check_character_files(char_cfg)
    print()

    # Step 2: Detect AstrBot
    print(_c(BOLD, "检测 AstrBot..."))
    data_dir = find_astrbot_data()

    if data_dir:
        ok(f"AstrBot 数据目录: {data_dir}")
    else:
        warn("未找到 AstrBot")
        print_guide(char_cfg)
        return

    running = is_astrbot_running()
    ok("AstrBot 运行中") if running else warn("AstrBot 未运行")
    if running:
        warn("安装人格后建议重启服务")

    config = read_config(data_dir)
    if config:
        info(f"配置版本: {config.get('config_version', '?')}")
        print()
        print(_c(BOLD, "检查 Provider 配置..."))
        check_providers(config)
    else:
        warn("无法读取 cmd_config.json")
    print()

    # Step 3: Check KB
    print(_c(BOLD, "检查知识库..."))
    check_kb(data_dir)
    print()

    # Step 4: Install persona
    print(_c(BOLD, "安装人格..."))
    success = install_persona(data_dir, char_cfg, dry_run=args.dry_run)
    ok("人格安装完成") if success else warn("人格安装失败")
    print()

    # Step 5: Guide
    print_guide(char_cfg)

    # Summary
    header("部署状态 / Summary")
    info(f"角色:    {persona_name}")
    info(f"人格注入: {'完成' if success else '失败'}")
    info(f"AstrBot: {'运行中' if running else '未运行'}")
    info("知识库:   需手工上传")
    info("Embedding: 需手工配置")
    info("服务重启: 需手工重启")

    if data_dir:
        config_display = f"配置文件: {data_dir / 'cmd_config.json'}"
        print(f"\n{_c(GREEN, config_display)}")

    print()


if __name__ == "__main__":
    main()
