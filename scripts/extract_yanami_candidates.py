from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path


SOURCE_DEFAULT = Path("data/novels/1-7+sss台版.txt")
OUT_DIR_DEFAULT = Path("data/extracted")

ALIASES = (
    "八奈见",
    "八奈見",
    "杏菜",
    "Anna",
    "Yanami",
)

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


def read_text(path: Path) -> tuple[str, str]:
    raw = path.read_bytes()
    for encoding in ("utf-8-sig", "utf-8", "gb18030", "big5", "cp950"):
        try:
            return raw.decode(encoding), encoding
        except UnicodeDecodeError:
            continue
    return raw.decode("gb18030", errors="replace"), "gb18030-replace"


def normalize_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = text.replace("\u3000", " ")
    return text


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
            paragraphs.append(
                Paragraph(
                    index=len(paragraphs),
                    text=joined,
                    volume=volume,
                    chapter=chapter,
                )
            )
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


def contains_alias(text: str) -> bool:
    lowered = text.lower()
    return any(alias.lower() in lowered for alias in ALIASES)


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


def build_candidate_scenes(
    paragraphs: list[Paragraph],
    before: int,
    after: int,
    max_chars: int,
) -> list[dict]:
    hit_indices = [p.index for p in paragraphs if contains_alias(p.text)]
    ranges = [
        (max(0, index - before), min(len(paragraphs) - 1, index + after))
        for index in hit_indices
    ]
    merged = merge_ranges(ranges)

    scenes: list[dict] = []
    for scene_num, (start, end) in enumerate(merged, start=1):
        current_start = start
        current_texts: list[str] = []

        def emit(chunk_end: int, texts: list[str]) -> None:
            if not texts:
                return
            first = paragraphs[current_start]
            last = paragraphs[chunk_end]
            scenes.append(
                {
                    "scene_id": f"yanami-candidate-{len(scenes) + 1:04d}",
                    "source_range": {
                        "start_paragraph": current_start,
                        "end_paragraph": chunk_end,
                    },
                    "volume": first.volume or last.volume,
                    "chapter": first.chapter or last.chapter,
                    "matched_aliases": sorted(
                        {
                            alias
                            for alias in ALIASES
                            if alias.lower() in "\n\n".join(texts).lower()
                        }
                    ),
                    "text": "\n\n".join(texts),
                }
            )

        for idx in range(start, end + 1):
            paragraph_text = paragraphs[idx].text
            next_len = len("\n\n".join([*current_texts, paragraph_text]))
            if current_texts and next_len > max_chars:
                emit(idx - 1, current_texts)
                current_start = idx
                current_texts = [paragraph_text]
            else:
                current_texts.append(paragraph_text)
        emit(end, current_texts)

    return scenes


def write_jsonl(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as file:
        for row in rows:
            file.write(json.dumps(row, ensure_ascii=False) + "\n")


def write_preview(path: Path, scenes: list[dict], limit: int) -> None:
    lines = ["# 八奈见杏菜候选场景预览", ""]
    for scene in scenes[:limit]:
        text = scene["text"]
        excerpt = text[:700] + ("..." if len(text) > 700 else "")
        lines.extend(
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
    path.write_text("\n".join(lines), encoding="utf-8", newline="\n")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Extract candidate scenes related to Yanami Anna from a novel text."
    )
    parser.add_argument("--source", type=Path, default=SOURCE_DEFAULT)
    parser.add_argument("--out-dir", type=Path, default=OUT_DIR_DEFAULT)
    parser.add_argument("--before", type=int, default=4)
    parser.add_argument("--after", type=int, default=8)
    parser.add_argument("--max-chars", type=int, default=6500)
    parser.add_argument("--preview-limit", type=int, default=20)
    args = parser.parse_args()

    text, encoding = read_text(args.source)
    text = normalize_text(text)
    paragraphs = split_paragraphs(text)
    scenes = build_candidate_scenes(
        paragraphs=paragraphs,
        before=args.before,
        after=args.after,
        max_chars=args.max_chars,
    )

    args.out_dir.mkdir(parents=True, exist_ok=True)
    normalized_path = args.out_dir / "novel_normalized_utf8.txt"
    paragraphs_path = args.out_dir / "novel_paragraphs.jsonl"
    candidates_path = args.out_dir / "yanami_candidate_scenes.jsonl"
    preview_path = args.out_dir / "yanami_candidate_preview.md"
    stats_path = args.out_dir / "yanami_extraction_stats.json"

    normalized_path.write_text(text, encoding="utf-8", newline="\n")
    write_jsonl(
        paragraphs_path,
        [
            {
                "paragraph_id": p.index,
                "volume": p.volume,
                "chapter": p.chapter,
                "text": p.text,
            }
            for p in paragraphs
        ],
    )
    write_jsonl(candidates_path, scenes)
    write_preview(preview_path, scenes, args.preview_limit)

    stats = {
        "source": str(args.source),
        "detected_encoding": encoding,
        "paragraph_count": len(paragraphs),
        "candidate_scene_count": len(scenes),
        "alias_hit_paragraph_count": sum(1 for p in paragraphs if contains_alias(p.text)),
        "aliases": ALIASES,
        "context_window": {"before": args.before, "after": args.after},
        "max_chars": args.max_chars,
        "outputs": {
            "normalized_text": str(normalized_path),
            "paragraphs": str(paragraphs_path),
            "candidate_scenes": str(candidates_path),
            "preview": str(preview_path),
        },
    }
    stats_path.write_text(
        json.dumps(stats, ensure_ascii=False, indent=2),
        encoding="utf-8",
        newline="\n",
    )

    print(json.dumps(stats, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
