"""
Build a comprehensive knowledge base document from all scene analyses.
Combines yanami_profile.md depth with yanami_scene_analysis.jsonl scene data.
"""
import json
import re
from collections import defaultdict

ANALYSIS_PATH = r'D:\character\data\extracted\yanami_scene_analysis.jsonl'
PROFILE_PATH = r'D:\character\data\extracted\yanami_profile.md'
OUTPUT_PATH = r'D:\character\deploy\yanami_full_knowledge.md'

# Read all analyses
analyses = []
with open(ANALYSIS_PATH, 'r', encoding='utf-8') as f:
    for line in f:
        if line.strip():
            a = json.loads(line)
            if a.get('useful'):
                analyses.append(a)

print(f"Total useful analyses: {len(analyses)}")

# Group by volume
by_volume = defaultdict(list)
for a in analyses:
    vol = a.get('volume', '未知')
    by_volume[vol].append(a)

# Build markdown
lines = []
lines.append("# 八奈见杏菜 — 完整知识库")
lines.append("")
lines.append(f"> 基于 {len(analyses)} 个有用场景的结构化分析，覆盖第 1 卷至第 8 卷")
lines.append("")
lines.append("---")
lines.append("")

# Section 1: Core character profile (from yanami_profile.md structure)
lines.append("## 角色核心档案")
lines.append("")

# Read and append key sections from profile
with open(PROFILE_PATH, 'r', encoding='utf-8') as f:
    profile_text = f.read()

# Extract sections 1-5 (core personality) and 10 (daily details) from profile
sections_to_extract = [
    "## 1. 一句话核心",
    "## 3. 表层人格",
    "## 4. 深层人格",
    "## 5. 核心矛盾",
    "## 8. 说话风格",
    "## 10. 日常细节",
    "## 11. 阶段变化",
]

for section_header in sections_to_extract:
    # Find the section in profile
    pattern = re.compile(re.escape(section_header) + r'.*?(?=\n## |\Z)', re.DOTALL)
    match = pattern.search(profile_text)
    if match:
        section_text = match.group(0)
        # Remove scene IDs [yanami-candidate-XXXX] for cleaner reading
        section_text = re.sub(r'\[yanami-candidate-\d+\]', '', section_text)
        lines.append(section_text)
        lines.append("")
        lines.append("---")
        lines.append("")

# Section 2: Scene data by volume - detailed emotional/behavior patterns
lines.append("## 分卷场景详情")
lines.append("")
lines.append("以下是各卷中八奈见杏菜出现的具体场景分析摘要，包含她的情绪状态、行为模式和人际关系表现。")
lines.append("")

for vol in sorted(by_volume.keys()):
    scenes = by_volume[vol]
    vol_short = vol[:60] if len(vol) > 60 else vol
    lines.append(f"### {vol_short}")
    lines.append(f"共 {len(scenes)} 个场景")
    lines.append("")

    for a in scenes:
        sid = a.get('scene_id', '')
        summary = a.get('scene_summary', '')
        emotions = a.get('emotional_state', [])
        relationships = a.get('relationships', [])
        behaviors = a.get('behavior_patterns', [])
        speech = a.get('speech_patterns', [])
        defenses = a.get('defense_mechanisms', [])
        contradictions = a.get('contradictions_or_tensions', [])
        desires = a.get('desires', [])

        lines.append(f"**场景：{sid}**")
        if summary:
            lines.append(f"- 概况：{summary[:300]}")
        if emotions:
            states = [e.get('state','') for e in emotions if isinstance(e, dict)]
            if states:
                lines.append(f"- 情绪：{' → '.join(states[:3])}")
            # Add hidden layer if available
            for e in emotions:
                if isinstance(e, dict) and e.get('hidden_layer'):
                    lines.append(f"- 内心真实状态：{e['hidden_layer'][:200]}")
        if relationships:
            for r in relationships[:3]:
                if isinstance(r, dict):
                    lines.append(f"- 对{r.get('target','?')}：{r.get('attitude','')[:150]}")
        if behaviors:
            for b in behaviors[:2]:
                if isinstance(b, dict):
                    txt = b.get('description') or b.get('pattern', '')
                    if txt:
                        lines.append(f"- 行为模式：{txt[:150]}")
        if speech:
            for s in speech[:2]:
                if isinstance(s, dict):
                    lines.append(f"- 说话特征：{s.get('pattern','')[:100]}（{s.get('when_used','')[:60]}）")
        if defenses:
            for d in defenses[:1]:
                if isinstance(d, dict):
                    txt = d.get('description') or d.get('mechanism', '')
                    if txt:
                        lines.append(f"- 防御机制：{txt[:150]}")
        if contradictions:
            for c in contradictions[:1]:
                if isinstance(c, dict) and c.get('tension'):
                    lines.append(f"- 内在矛盾：{c['tension'][:200]}")
        if desires:
            desire_strs = [d if isinstance(d, str) else (d.get('desire','') or d.get('description','')) for d in desires[:3]]
            lines.append(f"- 渴望：{' | '.join(desire_strs)}")
        lines.append("")

    lines.append("---")
    lines.append("")

# Section 3: Relationship summary
lines.append("## 人际关系总览")
lines.append("")

from collections import Counter
rel_targets = defaultdict(list)
for a in analyses:
    for r in a.get('relationships', []):
        if isinstance(r, dict) and r.get('target'):
            rel_targets[r['target']].append(r.get('attitude', ''))

for target, attitudes in sorted(rel_targets.items()):
    lines.append(f"### {target}")
    # Count unique attitudes
    unique_attitudes = list(set(attitudes))
    for att in unique_attitudes[:5]:
        lines.append(f"- {att[:200]}")
    lines.append("")

lines.append("---")
lines.append("")

# Section 4: Key quotes and speech patterns (without copying long quotes)
lines.append("## 说话风格汇总")
lines.append("")

all_speech = []
for a in analyses:
    for s in a.get('speech_patterns', []):
        if isinstance(s, dict) and s.get('pattern'):
            all_speech.append(s)

seen_patterns = set()
for s in all_speech:
    pat = s.get('pattern', '')
    if pat not in seen_patterns:
        seen_patterns.add(pat)
        when = s.get('when_used', '')
        example = s.get('example_summary', '')
        line = f"- **{pat}**"
        if when:
            line += f"（{when}）"
        lines.append(line)

text = '\n'.join(lines)

with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
    f.write(text)

import os
size = os.path.getsize(OUTPUT_PATH)
print(f"\nWritten to {OUTPUT_PATH}")
print(f"Size: {size} bytes ({size/1024:.1f} KB)")
print(f"Lines: {text.count(chr(10))}")
