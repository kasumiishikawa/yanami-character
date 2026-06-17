#!/usr/bin/env python3
"""
八奈见杏菜 — AstrBot 一键部署脚本
Yanami Anna — AstrBot One-Click Deployment Script

用法 / Usage:
    python deploy/deploy.py

自动检测 AstrBot 并注入人格配置。
Automatically detects AstrBot and injects personality configuration.
"""
import json
import os
import sqlite3
import subprocess
import sys
import uuid
from datetime import datetime
from pathlib import Path

PERSONA_NAME = "八奈见杏菜"

# ── Paths ──────────────────────────────────────────────────────────────────
SCRIPT_DIR = Path(__file__).parent.resolve()
PROJECT_DIR = SCRIPT_DIR.parent
SYSTEM_PROMPT_FILE = SCRIPT_DIR / "system_prompt.md"
KB_FILE = SCRIPT_DIR / "yanami_full_knowledge.md"
RAG_FILE = SCRIPT_DIR / "yanami_rag.md"

# Common AstrBot data locations
DATA_DIR_CANDIDATES = [
    Path.home() / "data",
    Path.home() / ".astrbot" / "data",
    Path("C:/Users") / os.environ.get("USERNAME", "") / "data",
    Path(os.environ.get("PROGRAMDATA", "C:/ProgramData")) / "astrbot" / "data",
]

# ── Utils ──────────────────────────────────────────────────────────────────
PINK = "\033[95m"
CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BOLD = "\033[1m"
END = "\033[0m"

def _supports_color() -> bool:
    return hasattr(sys.stdout, "isatty") and sys.stdout.isatty()

def _c(color: str, text: str) -> str:
    return f"{color}{text}{END}" if _supports_color() else text

def info(msg):
    print(f"  [INFO] {msg}")

def ok(msg):
    print(f"  [OK] {msg}")

def warn(msg):
    print(f"  [WARN] {msg}")

def err(msg):
    print(f"  [ERROR] {msg}")

def header(text):
    print(f"\n{_c(PINK + BOLD, '='*60)}")
    print(_c(PINK + BOLD, f"  {text}"))
    print(f"{_c(PINK + BOLD, '='*60)}\n")

# ── Detection ──────────────────────────────────────────────────────────────

def find_astrbot_data() -> Path | None:
    """Find AstrBot data directory by looking for cmd_config.json."""
    for candidate in DATA_DIR_CANDIDATES:
        config = candidate / "cmd_config.json"
        if config.exists():
            return candidate
    # Broader search
    for root in [Path.home(), Path("C:/Users").resolve()]:
        for p in root.rglob("cmd_config.json"):
            if "astrbot" in str(p).lower():
                return p.parent
    return None


def is_astrbot_running() -> bool:
    """Check if AstrBot process is running."""
    try:
        if sys.platform == "win32":
            result = subprocess.run(
                ["tasklist", "/FI", "IMAGENAME eq astrbot.exe"],
                capture_output=True, text=True, timeout=5
            )
            return "astrbot.exe" in result.stdout
        else:
            result = subprocess.run(
                ["pgrep", "-x", "astrbot"],
                capture_output=True, timeout=5
            )
            return result.returncode == 0
    except Exception:
        return False


def read_config(data_dir: Path) -> dict | None:
    """Read AstrBot cmd_config.json."""
    path = data_dir / "cmd_config.json"
    if not path.exists():
        return None
    with open(path, "r", encoding="utf-8-sig") as f:
        return json.load(f)


# ── Persona Installation ───────────────────────────────────────────────────

def install_persona(data_dir: Path, dry_run: bool = False) -> bool:
    """Inject Yanami persona into AstrBot's database."""
    db_path = data_dir / "data_v4.db"
    config_path = data_dir / "cmd_config.json"

    if not db_path.exists():
        err(f"数据库不存在: {db_path}")
        return False

    # Read system prompt
    if not SYSTEM_PROMPT_FILE.exists():
        err(f"System Prompt 文件不存在: {SYSTEM_PROMPT_FILE}")
        return False

    system_prompt = SYSTEM_PROMPT_FILE.read_text(encoding="utf-8").strip()
    info(f"System Prompt 长度: {len(system_prompt)} 字")

    if dry_run:
        ok("[模拟] 将写入以下内容到 AstrBot 数据库")
        return True

    # Backup DB
    backup_path = db_path.with_suffix(".db.backup")
    if not backup_path.exists():
        import shutil
        shutil.copy2(db_path, backup_path)
        info(f"数据库已备份: {backup_path}")

    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        now = datetime.now().isoformat()

        # Check if persona already exists
        cur.execute("""
            SELECT p.persona_id, p.id FROM personas p
            JOIN persona_folders pf ON p.folder_id = pf.folder_id
            WHERE pf.name = ?
        """, (PERSONA_NAME,))
        existing = cur.fetchone()

        if existing:
            persona_id, persona_row_id = existing
            cur.execute(
                "UPDATE personas SET updated_at = ?, system_prompt = ? WHERE id = ?",
                (now, system_prompt, persona_row_id),
            )
            ok(f"人格「{PERSONA_NAME}」已存在，已更新 System Prompt")
        else:
            # Get next IDs
            cur.execute("SELECT COALESCE(MAX(id), 0) + 1 FROM persona_folders")
            folder_id_num = cur.fetchone()[0]
            cur.execute("SELECT COALESCE(MAX(id), 0) + 1 FROM personas")
            persona_id_num = cur.fetchone()[0]

            # Create folder
            folder_id = str(uuid.uuid4())
            cur.execute("""
                INSERT INTO persona_folders
                (created_at, updated_at, id, folder_id, name, parent_id, description, sort_order)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                now, now, folder_id_num, folder_id,
                PERSONA_NAME,
                None,
                "《敗北女角太多了！》八奈见杏菜的角色人格",
                0
            ))

            # Create persona
            persona_id = str(uuid.uuid4())
            cur.execute("""
                INSERT INTO personas
                (created_at, updated_at, id, persona_id, system_prompt, begin_dialogs,
                 tools, skills, custom_error_message, folder_id, sort_order)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                now, now, persona_id_num, persona_id,
                system_prompt,
                "[]", None, None, None,
                folder_id, 0
            ))
            ok(f"人格「{PERSONA_NAME}」已安装 (persona_id={persona_id})")

        conn.commit()
        conn.close()
    except sqlite3.OperationalError as e:
        err(f"无法写入 AstrBot 数据库: {e}")
        warn("请确认 AstrBot 数据目录可写；如果服务正在占用数据库，请停止 AstrBot 后重试。")
        warn(f"也可以手动复制 {SYSTEM_PROMPT_FILE} 到 AstrBot 人格配置。")
        return False

    # Update cmd_config.json to set as default
    try:
        with open(config_path, "r", encoding="utf-8-sig") as f:
            config = json.load(f)
        config.setdefault("provider_settings", {})["default_personality"] = persona_id

        # Keep legacy/persona-pool config in sync for AstrBot builds that still read it.
        personas = config.setdefault("persona", [])
        for persona in personas:
            if persona.get("name") == PERSONA_NAME:
                persona["system_prompt"] = system_prompt
                break
        else:
            personas.append({
                "name": PERSONA_NAME,
                "system_prompt": system_prompt,
                "begin_dialogs": [],
                "model": None,
                "tools": None,
                "skills": None,
            })

        with open(config_path, "w", encoding="utf-8-sig") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        ok(f"已在 cmd_config.json 中设为默认人格 ({persona_id})")
    except Exception as e:
        warn(f"无法更新 cmd_config.json: {e}")

    return True


# ── Health Check ───────────────────────────────────────────────────────────

def check_providers(config: dict):
    """Check configured providers."""
    providers = config.get("provider", [])
    sources = config.get("provider_sources", [])

    info(f"Provider 数量: {len(providers)}")
    info(f"Provider Source 数量: {len(sources)}")

    # Check for chat completion provider
    has_chat = any("chat_completion" in p.get("provider_type", "") for p in sources)
    has_chat = has_chat or any("openai_chat_completion" in p.get("type", "") for p in sources)
    if has_chat:
        ok("检测到聊天模型 Provider")
    else:
        warn("未检测到聊天模型 Provider，请确认 AstrBot 已配置")

    # Check default model
    default = config.get("provider_settings", {}).get("default_provider_id", "N/A")
    info(f"默认对话模型: {default}")

    # Check for embedding provider in plugins config
    plugin_config = config.get("provider", [])
    has_embed = any("embed" in p.get("id", "").lower() for p in plugin_config)
    if has_embed:
        ok("检测到 Embedding 模型配置")
    else:
        warn("未检测到 Embedding 模型，需要手工配置（详见文档）")


def check_kb(data_dir: Path):
    """Check knowledge base status."""
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
        collections = cur.fetchall()
        conn.close()

        if collections:
            for name, docs, chunks in collections:
                ok(f"知识库「{name}」: {docs} 文档, {chunks} 切块")
        else:
            warn("尚未创建知识库")
    except Exception as e:
        warn(f"无法读取知识库: {e}")


# ── File Check ─────────────────────────────────────────────────────────────

def check_deploy_files():
    """Check that all deploy files exist."""
    files = [
        ("System Prompt", SYSTEM_PROMPT_FILE),
        ("完整知识库", KB_FILE),
        ("精简知识库", RAG_FILE),
    ]
    for name, path in files:
        if path.exists():
            ok(f"{name}: {path.name} ({path.stat().st_size / 1024:.0f} KB)")
        else:
            err(f"{name}: {path.name} 不存在")


# ── Guide ──────────────────────────────────────────────────────────────────

def print_post_install_guide():
    """Print post-installation manual steps."""
    print(f"\n{_c(GREEN + BOLD, '='*60)}")
    print(_c(GREEN + BOLD, "  部署完成！还差三步 / Almost done! 3 steps left"))
    print(f"{_c(GREEN + BOLD, '='*60)}\n")

    print(_c(BOLD, "1. 配置 Embedding Provider (RAG 知识库需要)"))
    print(f"   进 AstrBot 仪表盘 → 服务提供商 → 新增 → Embedding")
    print(f"   选 OpenAI Compatible，填入:")
    print(f"     API Base URL: {_c(CYAN, 'https://api.siliconflow.cn/v1')}")
    print(f"     Model:        {_c(CYAN, 'BAAI/bge-m3')}")
    print(f"     API Key:      去 {_c(CYAN, 'https://siliconflow.cn')} 注册获取 (免费)")
    print()

    print(_c(BOLD, "2. 上传知识库文档"))
    print(f"   仪表盘 → 知识库 → 新建")
    print(f"   取名后选刚配好的 Embedding 模型 → 保存")
    print(f"   进入知识库详情 → 上传文档 → 选:")
    print(f"     {_c(CYAN, f'deploy{os.sep}yanami_full_knowledge.md')}")
    print(f"   (或 deploy{os.sep}yanami_rag.md 精简版)")
    print()

    print(_c(BOLD, "3. 重启 AstrBot 服务"))
    print(f"   方式一: 仪表盘右上角重启按钮")
    print(f"   方式二: 命令行 {_c(YELLOW, 'Restart-Service AstrBot')}")
    print()

    print(_c(BOLD, "KB 文档位置"))
    print(f"   完整版: {_c(YELLOW, str(KB_FILE))}  (324 KB, 4399 行)")
    print(f"   精简版: {_c(YELLOW, str(RAG_FILE))}  (6.7 KB, 话题分类)")
    print()


# ── Main ───────────────────────────────────────────────────────────────────

def main():
    header("八奈见杏菜 — AstrBot 一键部署")

    # Step 1: Check deploy files
    print(_c(BOLD, "检查部署文件..."))
    check_deploy_files()
    print()

    # Step 2: Detect AstrBot
    print(_c(BOLD, "检测 AstrBot..."))
    data_dir = find_astrbot_data()

    if data_dir:
        ok(f"AstrBot 数据目录: {data_dir}")
    else:
        warn("未找到 AstrBot，可能未安装或在非标准位置")
        warn("部署脚本仍会执行文件安装，但不会注入人格到数据库")
        warn("提示: 可手动复制 deploy/system_prompt.md 到 AstrBot 仪表盘")
        print()
        print_post_install_guide()
        return

    running = is_astrbot_running()
    if running:
        ok("AstrBot 服务运行中")
        warn("修改人格后建议重启服务")
    else:
        warn("AstrBot 未运行，部署后启动即可")

    config = read_config(data_dir)
    if config:
        info(f"配置版本: {config.get('config_version')}")
        print()

        print(_c(BOLD, "检查 Provider 配置..."))
        check_providers(config)
    else:
        warn("无法读取 cmd_config.json")
    print()

    # Step 3: Check KB status
    print(_c(BOLD, "检查知识库..."))
    check_kb(data_dir)
    print()

    # Step 4: Install persona
    print(_c(BOLD, "安装人格..."))
    success = install_persona(data_dir)
    if success:
        ok("人格安装完成")
    else:
        warn("人格安装失败，请手动配置")
    print()

    # Step 5: Print guide
    print_post_install_guide()

    # Summary
    header("部署状态总结 / Summary")
    info(f"人格注入: {'完成' if success else '失败'}")
    info(f"AstrBot 运行: {'是' if running else '否'}")
    info(f"知识库文件: 已就绪 (需手工上传)")
    info("Embedding:  需手工配置")
    info("服务重启:   需手工重启")

    print(f"\n{_c(GREEN, f'配置文件路径: {data_dir / "cmd_config.json"}')}")
    print(_c(GREEN, f"知识库源文件: {KB_FILE}"))
    print(_c(GREEN, f"System Prompt: {SYSTEM_PROMPT_FILE}"))
    print()


if __name__ == "__main__":
    main()
