#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import re
import shutil
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


PROJECT_DIR = Path(__file__).parent.resolve()
CHARACTERS_DIR = PROJECT_DIR / "characters"
DATA_DIR = PROJECT_DIR / "data"
NOVELS_DIR = DATA_DIR / "novels"
EXTRACTED_DIR = DATA_DIR / "extracted"
PROMPTS_DIR = PROJECT_DIR / "prompts"
DEFAULT_CHARACTER = "yanami"

VOLUME_RE = re.compile(r"^\s*第[一二三四五六七八九十百零〇]+卷\b.*$")
CHAPTER_RE = re.compile(
    r"^\s*(?:序|终章|尾声|后记|特别篇|短篇|SSS?|"
    r"第[一二三四五六七八九十百零〇]+[败敗话話章]|"
    r".*～第[一二三四五六七八九十百零〇]+[败敗]～.*)\s*$"
)


@dataclass
class Paragraph:
    index: int
    text: str
    volume: str
    chapter: str


def info(message: str) -> None:
    print(f"[INFO] {message}")


def ok(message: str) -> None:
    print(f"[OK] {message}")


def warn(message: str) -> None:
    print(f"[WARN] {message}")


def fail(message: str, code: int = 1) -> None:
    print(f"[ERROR] {message}")
    raise SystemExit(code)


def slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9_-]+", "-", value)
    value = re.sub(r"-+", "-", value).strip("-")
    return value


def list_characters() -> list[str]:
    if not CHARACTERS_DIR.exists():
        return []
    return sorted(
        child.name
        for child in CHARACTERS_DIR.iterdir()
        if child.is_dir() and (child / "character.json").exists()
    )


def load_character(character_id: str) -> dict:
    path = CHARACTERS_DIR / character_id / "character.json"
    if not path.exists():
        fail(f"角色配置不存在: {path}")
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def save_character(character_id: str, config: dict) -> None:
    char_dir = CHARACTERS_DIR / character_id
    char_dir.mkdir(parents=True, exist_ok=True)
    path = char_dir / "character.json"
    path.write_text(
        json.dumps(config, ensure_ascii=False, indent=2),
        encoding="utf-8",
        newline="\n",
    )


def read_text(path: Path) -> tuple[str, str]:
    raw = path.read_bytes()
    for encoding in ("utf-8-sig", "utf-8", "gb18030", "big5", "cp950"):
        try:
            return raw.decode(encoding), encoding
        except UnicodeDecodeError:
            continue
    return raw.decode("gb18030", errors="replace"), "gb18030-replace"


def normalize_text(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n").replace("\u3000", " ")


def split_paragraphs(text: str) -> list[Paragraph]:
    paragraphs: list[Paragraph] = []
    volume = ""
    chapter = ""
    buffer: list[str] = []

    def flush() -> None:
        nonlocal buffer
        if not buffer:
            return
        joined = "\n".join(buffer).strip()
        if joined:
            paragraphs.append(Paragraph(len(paragraphs), joined, volume, chapter))
        buffer = []

    for line in text.split("\n"):
        stripped = line.strip()
        if not stripped:
            flush()
            continue
        if VOLUME_RE.match(stripped):
            flush()
            volume = stripped
            chapter = ""
            paragraphs.append(Paragraph(len(paragraphs), stripped, volume, chapter))
            continue
        if CHAPTER_RE.match(stripped) and len(stripped) <= 80:
            flush()
            chapter = stripped
            paragraphs.append(Paragraph(len(paragraphs), stripped, volume, chapter))
            continue
        buffer.append(stripped)

    flush()
    return paragraphs


def contains_alias(text: str, aliases: list[str]) -> bool:
    lowered = text.lower()
    return any(alias.lower() in lowered for alias in aliases)


def merge_ranges(ranges: list[tuple[int, int]]) -> list[tuple[int, int]]:
    if not ranges:
        return []
    ranges.sort()
    merged = [ranges[0]]
    for start, end in ranges[1:]:
        last_start, last_end = merged[-1]
        if start <= last_end + 1:
            merged[-1] = (last_start, max(last_end, end))
        else:
            merged.append((start, end))
    return merged


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as file:
        for row in rows:
            file.write(json.dumps(row, ensure_ascii=False) + "\n")


def read_jsonl(path: Path) -> list[dict]:
    rows: list[dict] = []
    with path.open("r", encoding="utf-8") as file:
        for line in file:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def character_paths(character_id: str) -> dict[str, Path]:
    base = EXTRACTED_DIR / character_id
    return {
        "base": base,
        "normalized": base / "novel_normalized_utf8.txt",
        "paragraphs": base / "paragraphs.jsonl",
        "candidates": base / "candidate_scenes.jsonl",
        "preview": base / "candidate_preview.md",
        "stats": base / "extraction_stats.json",
        "batches": base / "batches",
        "analysis": base / "scene_analysis.jsonl",
        "profile": base / "profile.md",
    }


def resolve_source_files(config: dict) -> list[Path]:
    sources = config.get("source_files") or []
    if not sources:
        fail("character.json 缺少 source_files，请先放入小说并配置路径。")
    paths = []
    for source in sources:
        path = Path(source)
        if not path.is_absolute():
            path = PROJECT_DIR / path
        if not path.exists():
            fail(f"小说文件不存在: {path}")
        paths.append(path)
    return paths


def init_character(args: argparse.Namespace) -> None:
    character_id = args.character or input("角色 ID，例如 lemon: ").strip()
    character_id = slugify(character_id)
    if not character_id:
        fail("角色 ID 不能为空。")

    char_dir = CHARACTERS_DIR / character_id
    if char_dir.exists() and not args.force:
        fail(f"角色目录已存在: {char_dir}，如需覆盖请加 --force。")

    display_name = args.display_name or input("显示名，例如 烧盐柠檬: ").strip()
    work_name = args.work_name or input("作品名: ").strip()
    aliases_raw = args.aliases or input("别名，用英文逗号分隔: ").strip()
    aliases = [item.strip() for item in aliases_raw.split(",") if item.strip()]
    if display_name and display_name not in aliases:
        aliases.insert(0, display_name)

    source_files = args.source_files
    if not source_files:
        NOVELS_DIR.mkdir(parents=True, exist_ok=True)
        detected = sorted(str(path.relative_to(PROJECT_DIR)) for path in NOVELS_DIR.glob("*.txt"))
        if detected:
            print("检测到小说文件:")
            for index, path in enumerate(detected, start=1):
                print(f"  {index}. {path}")
            choice = input("选择序号，或直接输入路径，可多项逗号分隔: ").strip()
            chosen: list[str] = []
            for item in choice.split(","):
                item = item.strip()
                if item.isdigit() and 1 <= int(item) <= len(detected):
                    chosen.append(detected[int(item) - 1])
                elif item:
                    chosen.append(item)
            source_files = chosen
        else:
            entered = input("小说文件路径，可多项逗号分隔: ").strip()
            source_files = [item.strip() for item in entered.split(",") if item.strip()]

    if not source_files:
        fail("至少需要一个小说文件。")

    config = {
        "character_id": character_id,
        "display_name": display_name,
        "work_name": work_name,
        "aliases": aliases,
        "source_files": source_files,
        "description": args.description or "",
        "deploy": {
            "persona_name": display_name,
            "knowledge_base_name": character_id,
            "system_prompt": "system_prompt.md",
            "full_knowledge": "full_knowledge.md",
            "rag": "rag.md",
        },
        "build": {
            "status": "initialized",
            "created_at": datetime.now().isoformat(timespec="seconds"),
        },
    }
    save_character(character_id, config)
    ok(f"已创建角色配置: {CHARACTERS_DIR / character_id / 'character.json'}")
    info(f"下一步: python character.py build --character {character_id}")


def extract_candidates(config: dict, before: int, after: int, max_chars: int, preview_limit: int) -> None:
    character_id = config["character_id"]
    display_name = config["display_name"]
    aliases = config.get("aliases", [])
    if not aliases:
        fail("character.json 缺少 aliases。")

    paths = character_paths(character_id)
    paths["base"].mkdir(parents=True, exist_ok=True)

    all_paragraphs: list[Paragraph] = []
    encodings: dict[str, str] = {}
    normalized_parts: list[str] = []

    for source in resolve_source_files(config):
        text, encoding = read_text(source)
        encodings[str(source.relative_to(PROJECT_DIR))] = encoding
        text = normalize_text(text)
        normalized_parts.append(f"\n\n# SOURCE: {source}\n\n{text}")
        offset = len(all_paragraphs)
        for paragraph in split_paragraphs(text):
            all_paragraphs.append(
                Paragraph(
                    index=offset + paragraph.index,
                    text=paragraph.text,
                    volume=paragraph.volume,
                    chapter=paragraph.chapter,
                )
            )

    hit_indices = [p.index for p in all_paragraphs if contains_alias(p.text, aliases)]
    ranges = [
        (max(0, index - before), min(len(all_paragraphs) - 1, index + after))
        for index in hit_indices
    ]

    scenes: list[dict] = []
    for start, end in merge_ranges(ranges):
        current_start = start
        current_texts: list[str] = []

        def emit(chunk_end: int, texts: list[str]) -> None:
            if not texts:
                return
            joined = "\n\n".join(texts)
            first = all_paragraphs[current_start]
            last = all_paragraphs[chunk_end]
            scenes.append(
                {
                    "scene_id": f"{character_id}-candidate-{len(scenes) + 1:04d}",
                    "source_range": {
                        "start_paragraph": current_start,
                        "end_paragraph": chunk_end,
                    },
                    "volume": first.volume or last.volume,
                    "chapter": first.chapter or last.chapter,
                    "matched_aliases": sorted(
                        {alias for alias in aliases if alias.lower() in joined.lower()}
                    ),
                    "text": joined,
                }
            )

        for idx in range(start, end + 1):
            paragraph_text = all_paragraphs[idx].text
            next_len = len("\n\n".join([*current_texts, paragraph_text]))
            if current_texts and next_len > max_chars:
                emit(idx - 1, current_texts)
                current_start = idx
                current_texts = [paragraph_text]
            else:
                current_texts.append(paragraph_text)
        emit(end, current_texts)

    paths["normalized"].write_text(
        "\n".join(normalized_parts).strip(),
        encoding="utf-8",
        newline="\n",
    )
    write_jsonl(
        paths["paragraphs"],
        [
            {
                "paragraph_id": p.index,
                "volume": p.volume,
                "chapter": p.chapter,
                "text": p.text,
            }
            for p in all_paragraphs
        ],
    )
    write_jsonl(paths["candidates"], scenes)

    preview_lines = [f"# {display_name}候选场景预览", ""]
    for scene in scenes[:preview_limit]:
        excerpt = scene["text"][:700] + ("..." if len(scene["text"]) > 700 else "")
        preview_lines.extend(
            [
                f"## {scene['scene_id']}",
                "",
                f"- 卷：{scene.get('volume') or '未知'}",
                f"- 章：{scene.get('chapter') or '未知'}",
                f"- 命中：{', '.join(scene['matched_aliases'])}",
                "",
                excerpt,
                "",
            ]
        )
    paths["preview"].write_text("\n".join(preview_lines), encoding="utf-8", newline="\n")

    stats = {
        "character_id": character_id,
        "display_name": display_name,
        "source_files": config.get("source_files", []),
        "detected_encodings": encodings,
        "paragraph_count": len(all_paragraphs),
        "candidate_scene_count": len(scenes),
        "alias_hit_paragraph_count": len(hit_indices),
        "aliases": aliases,
        "context_window": {"before": before, "after": after},
        "max_chars": max_chars,
        "outputs": {key: str(value.relative_to(PROJECT_DIR)) for key, value in paths.items() if key != "base"},
    }
    paths["stats"].write_text(
        json.dumps(stats, ensure_ascii=False, indent=2),
        encoding="utf-8",
        newline="\n",
    )
    ok(f"候选场景: {len(scenes)} 条 -> {paths['candidates']}")


def create_batches(config: dict, batch_size: int) -> None:
    character_id = config["character_id"]
    paths = character_paths(character_id)
    if not paths["candidates"].exists():
        fail(f"候选场景不存在，请先运行 extract/build: {paths['candidates']}")

    scenes = read_jsonl(paths["candidates"])
    batch_dir = paths["batches"]
    batch_dir.mkdir(parents=True, exist_ok=True)

    for old in batch_dir.glob("batch_*.json"):
        old.unlink()

    batch_count = math.ceil(len(scenes) / batch_size) if scenes else 0
    for index in range(batch_count):
        start = index * batch_size
        end = min(start + batch_size, len(scenes))
        batch = scenes[start:end]
        batch_info = {
            "character_id": character_id,
            "display_name": config["display_name"],
            "aliases": config.get("aliases", []),
            "batch_id": f"batch_{index + 1:03d}",
            "batch_start_scene": start + 1,
            "batch_end_scene": end,
            "scene_count": len(batch),
            "total_chars": sum(len(scene["text"]) for scene in batch),
            "scenes": [
                {
                    "scene_id": scene["scene_id"],
                    "volume": scene.get("volume", ""),
                    "chapter": scene.get("chapter", ""),
                    "matched_aliases": scene.get("matched_aliases", []),
                    "text": scene["text"],
                }
                for scene in batch
            ],
        }
        (batch_dir / f"batch_{index + 1:03d}.json").write_text(
            json.dumps(batch_info, ensure_ascii=False, indent=2),
            encoding="utf-8",
            newline="\n",
        )

    manifest = {
        "character_id": character_id,
        "display_name": config["display_name"],
        "total_scenes": len(scenes),
        "total_batches": batch_count,
        "batch_size": batch_size,
        "batches": [f"batch_{index + 1:03d}.json" for index in range(batch_count)],
    }
    (batch_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
        newline="\n",
    )
    ok(f"批次文件: {batch_count} 个 -> {batch_dir}")


def write_character_prompts(config: dict) -> None:
    character_id = config["character_id"]
    paths = character_paths(character_id)
    prompt_dir = paths["base"] / "prompts"
    prompt_dir.mkdir(parents=True, exist_ok=True)

    extract_template = (PROMPTS_DIR / "extract_character_scene.md").read_text(encoding="utf-8")
    profile_template = (PROMPTS_DIR / "build_character_profile.md").read_text(encoding="utf-8")
    replacements = {
        "{{character_id}}": character_id,
        "{{display_name}}": config["display_name"],
        "{{work_name}}": config.get("work_name", ""),
        "{{aliases}}": " / ".join(config.get("aliases", [])),
    }
    for old, new in replacements.items():
        extract_template = extract_template.replace(old, new)
        profile_template = profile_template.replace(old, new)

    (prompt_dir / "extract_scene.md").write_text(extract_template, encoding="utf-8", newline="\n")
    (prompt_dir / "build_profile.md").write_text(profile_template, encoding="utf-8", newline="\n")
    ok(f"角色 prompt: {prompt_dir}")


def extract_markdown_section(text: str, heading: str) -> str:
    pattern = re.compile(re.escape(heading) + r".*?(?=\n## |\Z)", re.DOTALL)
    match = pattern.search(text)
    if not match:
        return ""
    return match.group(0).replace(heading, "", 1).strip()


def compact_profile_for_prompt(profile_text: str) -> str:
    short_card = extract_markdown_section(profile_text, "## 13. 短人格卡")
    if short_card:
        short_card = re.sub(r"^（.*?）\s*", "", short_card.strip())
        fenced = re.search(r"```(?:[a-zA-Z0-9_-]+)?\s*(.*?)\s*```", short_card, re.DOTALL)
        if fenced:
            return fenced.group(1).strip()
        return short_card

    selected: list[str] = []
    for heading in [
        "## 1. 一句话核心",
        "## 5. 核心矛盾",
        "## 8. 说话风格",
        "## 9. 行为模式",
        "## 12. 对话扮演规则",
    ]:
        section = extract_markdown_section(profile_text, heading)
        if section:
            selected.append(f"{heading}\n\n{section}")
    return "\n\n".join(selected).strip() or profile_text[:6000].strip()


def render_system_prompt(config: dict, profile_text: str) -> str:
    display_name = config["display_name"]
    work_name = config.get("work_name", "")
    compact_profile = compact_profile_for_prompt(profile_text)
    return f"""# AstrBot System Prompt — {display_name}

你正在扮演《{work_name}》中的{display_name}。你不是 AI 助手，不是客服，不是百科。你要根据下方角色资料自然对话。

## 绝对输出规则

- 只输出中文自然语言和必要的普通标点。
- 严禁使用任何 Emoji 或 Unicode 彩色表情符号。
- 不要使用颜文字、ASCII 表情、装饰符号或符号画。
- 不要长篇解释设定，不要复述原作大段文本。

## 角色资料

{compact_profile}

## 对话原则

- 用户不是原作角色，除非用户明确设定。
- 不要默认恋爱关系，亲密关系必须逐步推进。
- 回答应像角色本人在聊天，而不是像资料解说员。
- 如果用户要求你讲设定，可以简短概括，不要变成百科。
- 回答前检查：是否像{display_name}会说的话，是否过度顺从，是否突然推进亲密关系，是否使用了 AI 客服口吻。
"""


def build_full_knowledge(config: dict, profile_text: str, analyses: list[dict]) -> str:
    display_name = config["display_name"]
    useful = [item for item in analyses if item.get("useful", True)]
    lines = [
        f"# {display_name} — 完整知识库",
        "",
        f"> 基于 {len(useful)} 个有用场景的结构化分析生成。",
        "",
        "---",
        "",
        "## 角色核心档案",
        "",
        profile_text.strip(),
        "",
        "---",
        "",
        "## 场景详情",
        "",
    ]
    for item in useful:
        lines.append(f"### {item.get('scene_id', 'unknown')}")
        if item.get("volume"):
            lines.append(f"- 卷：{item.get('volume')}")
        if item.get("chapter"):
            lines.append(f"- 章：{item.get('chapter')}")
        if item.get("scene_summary"):
            lines.append(f"- 概况：{item.get('scene_summary')}")
        for key, label in [
            ("emotional_state", "情绪"),
            ("behavior_patterns", "行为"),
            ("speech_patterns", "说话"),
            ("relationships", "关系"),
            ("defense_mechanisms", "防御"),
            ("contradictions_or_tensions", "矛盾"),
        ]:
            values = item.get(key) or []
            snippets: list[str] = []
            for value in values[:3]:
                if isinstance(value, str):
                    snippets.append(value)
                elif isinstance(value, dict):
                    snippets.append(
                        value.get("state")
                        or value.get("pattern")
                        or value.get("description")
                        or value.get("attitude")
                        or value.get("tension")
                        or ""
                    )
            snippets = [snippet for snippet in snippets if snippet]
            if snippets:
                lines.append(f"- {label}：{' | '.join(snippets)}")
        lines.append("")
    return "\n".join(lines)


def build_rag(profile_text: str) -> str:
    headings = [
        "## 1. 一句话核心",
        "## 2. 基础身份与社交位置",
        "## 3. 表层人格",
        "## 4. 深层人格",
        "## 5. 核心矛盾",
        "## 6. 关系模型",
        "## 7. 情绪触发器",
        "## 8. 说话风格",
        "## 9. 行为模式",
        "## 10. 日常细节",
        "## 11. 阶段变化",
        "## 12. 对话扮演规则",
    ]
    lines = ["# 角色知识库（精简）", ""]
    for heading in headings:
        pattern = re.compile(re.escape(heading) + r".*?(?=\n## |\Z)", re.DOTALL)
        match = pattern.search(profile_text)
        if match:
            lines.append(match.group(0).strip())
            lines.append("")
            lines.append("---")
            lines.append("")
    if len(lines) <= 2:
        lines.append(profile_text.strip())
    return "\n".join(lines).strip() + "\n"


def generate_deploy_files(config: dict, allow_placeholders: bool = False) -> None:
    character_id = config["character_id"]
    char_dir = CHARACTERS_DIR / character_id
    paths = character_paths(character_id)
    profile_path = paths["profile"]
    analysis_path = paths["analysis"]

    if not profile_path.exists():
        if not allow_placeholders:
            warn(f"角色圣经不存在，跳过部署文件生成: {profile_path}")
            info("LLM 分析和 profile 生成完成后，再运行 python character.py package --character <id>")
            return
        profile_text = f"{config['display_name']} 的角色资料尚未生成。请先完成场景分析和角色圣经构建。"
    else:
        profile_text = profile_path.read_text(encoding="utf-8")

    analyses = read_jsonl(analysis_path) if analysis_path.exists() else []
    full_knowledge = build_full_knowledge(config, profile_text, analyses) if analyses else profile_text
    rag = build_rag(profile_text)
    system_prompt = render_system_prompt(config, profile_text)

    char_dir.mkdir(parents=True, exist_ok=True)
    (char_dir / "system_prompt.md").write_text(system_prompt, encoding="utf-8", newline="\n")
    (char_dir / "full_knowledge.md").write_text(full_knowledge, encoding="utf-8", newline="\n")
    (char_dir / "rag.md").write_text(rag, encoding="utf-8", newline="\n")

    checklist = f"""# {config['display_name']} OOC 检查清单

- 是否符合角色说话方式
- 是否过度顺从用户
- 是否百科化解释设定
- 是否突然推进亲密关系
- 是否违背原作关系和经历
- 是否使用 Emoji、颜文字或装饰符号
"""
    (char_dir / "ooc_checklist.md").write_text(checklist, encoding="utf-8", newline="\n")

    report = f"""# {config['display_name']} OOC 评估报告

尚未评估。建议部署后使用 `ooc_checklist.md` 进行 20-50 轮测试。
"""
    report_path = char_dir / "ooc_eval_report.md"
    if not report_path.exists():
        report_path.write_text(report, encoding="utf-8", newline="\n")

    config.setdefault("build", {})["deploy_files_generated_at"] = datetime.now().isoformat(timespec="seconds")
    config["build"]["status"] = "packaged" if profile_path.exists() else "initialized"
    save_character(character_id, config)
    ok(f"部署文件已生成: {char_dir}")


def update_build_metadata(config: dict) -> None:
    character_id = config["character_id"]
    paths = character_paths(character_id)
    build = config.setdefault("build", {})
    previous_status = build.get("status")
    build.update(
        {
            "candidate_scenes": str(paths["candidates"].relative_to(PROJECT_DIR)),
            "batches": str(paths["batches"].relative_to(PROJECT_DIR)),
            "scene_analysis": str(paths["analysis"].relative_to(PROJECT_DIR)),
            "profile": str(paths["profile"].relative_to(PROJECT_DIR)),
            "updated_at": datetime.now().isoformat(timespec="seconds"),
        }
    )
    if previous_status != "packaged":
        build["status"] = "candidates_ready"
    save_character(character_id, config)


def build_character(args: argparse.Namespace) -> None:
    config = load_character(args.character)
    extract_candidates(
        config,
        before=args.before,
        after=args.after,
        max_chars=args.max_chars,
        preview_limit=args.preview_limit,
    )
    create_batches(config, batch_size=args.batch_size)
    write_character_prompts(config)
    update_build_metadata(config)
    generate_deploy_files(config, allow_placeholders=args.placeholders)

    character_id = config["character_id"]
    paths = character_paths(character_id)
    print("")
    info("自动化部分已完成。接下来需要 LLM 处理批次并生成角色圣经：")
    print(f"  批次目录: {paths['batches']}")
    print(f"  场景抽取 Prompt: {paths['base'] / 'prompts' / 'extract_scene.md'}")
    print(f"  角色汇总 Prompt: {paths['base'] / 'prompts' / 'build_profile.md'}")
    print(f"  期望分析输出: {paths['analysis']}")
    print(f"  期望角色圣经: {paths['profile']}")
    print("")
    info(f"当 profile.md 和 scene_analysis.jsonl 就绪后运行: python character.py package --character {character_id}")
    info(f"然后部署: python deploy/deploy.py --character {character_id}")


def package_character(args: argparse.Namespace) -> None:
    config = load_character(args.character)
    generate_deploy_files(config, allow_placeholders=args.placeholders)


def status_character(args: argparse.Namespace) -> None:
    config = load_character(args.character)
    paths = character_paths(config["character_id"])
    print(json.dumps(config, ensure_ascii=False, indent=2))
    print("")
    for label, path in paths.items():
        if label == "base":
            continue
        state = "exists" if path.exists() else "missing"
        print(f"{label:12s} {state:8s} {path}")


def wizard(args: argparse.Namespace) -> None:
    init_args = argparse.Namespace(
        character=args.character,
        display_name=None,
        work_name=None,
        aliases=None,
        source_files=None,
        description="",
        force=args.force,
    )
    init_character(init_args)
    character_id = slugify(init_args.character or "")
    if not character_id:
        character_id = list_characters()[-1]
    answer = input("是否立即构建候选场景和批次？[Y/n] ").strip().lower()
    if answer in ("", "y", "yes"):
        build_args = argparse.Namespace(
            character=character_id,
            before=4,
            after=8,
            max_chars=6500,
            preview_limit=20,
            batch_size=15,
            placeholders=True,
        )
        build_character(build_args)


def main() -> None:
    parser = argparse.ArgumentParser(description="角色构建入口")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("list", help="列出已有角色")

    init_parser = subparsers.add_parser("init", help="初始化新角色")
    init_parser.add_argument("--character", "-c", help="角色 ID，例如 lemon")
    init_parser.add_argument("--display-name", help="显示名")
    init_parser.add_argument("--work-name", help="作品名")
    init_parser.add_argument("--aliases", help="别名，英文逗号分隔")
    init_parser.add_argument("--source-files", nargs="+", help="小说文件路径")
    init_parser.add_argument("--description", default="", help="角色描述")
    init_parser.add_argument("--force", action="store_true", help="允许覆盖已有目录")

    build_parser = subparsers.add_parser("build", help="提取候选场景、切批次并生成构建提示")
    build_parser.add_argument("--character", "-c", default=DEFAULT_CHARACTER)
    build_parser.add_argument("--before", type=int, default=4)
    build_parser.add_argument("--after", type=int, default=8)
    build_parser.add_argument("--max-chars", type=int, default=6500)
    build_parser.add_argument("--preview-limit", type=int, default=20)
    build_parser.add_argument("--batch-size", type=int, default=15)
    build_parser.add_argument("--placeholders", action="store_true", help="没有 profile 时也生成占位部署文件")

    package_parser = subparsers.add_parser("package", help="根据 profile/analysis 生成部署文件")
    package_parser.add_argument("--character", "-c", default=DEFAULT_CHARACTER)
    package_parser.add_argument("--placeholders", action="store_true", help="没有 profile 时也生成占位文件")

    status_parser = subparsers.add_parser("status", help="查看角色构建状态")
    status_parser.add_argument("--character", "-c", default=DEFAULT_CHARACTER)

    wizard_parser = subparsers.add_parser("wizard", help="交互式初始化并构建")
    wizard_parser.add_argument("--character", "-c")
    wizard_parser.add_argument("--force", action="store_true")

    args = parser.parse_args()

    if args.command == "list":
        chars = list_characters()
        if not chars:
            warn("没有角色配置。")
            return
        for char in chars:
            config = load_character(char)
            print(f"{char:20s} {config.get('display_name', '')}")
    elif args.command == "init":
        init_character(args)
    elif args.command == "build":
        build_character(args)
    elif args.command == "package":
        package_character(args)
    elif args.command == "status":
        status_character(args)
    elif args.command == "wizard":
        wizard(args)


if __name__ == "__main__":
    main()
