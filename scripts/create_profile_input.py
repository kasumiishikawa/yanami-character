"""
Create a compact, well-structured input file for the character profile building step.
Extracts only the most salient information from the analysis data.
"""
import json
from collections import defaultdict, Counter

INPUT = r'D:\character\data\extracted\yanami_scene_analysis.jsonl'
OUTPUT = r'D:\character\data\extracted\yanami_profile_input.md'

analyses = []
with open(INPUT, 'r', encoding='utf-8') as f:
    for line in f:
        if line.strip():
            analyses.append(json.loads(line))

useful = [a for a in analyses if a.get('useful')]
vols = set()
for a in useful:
    v = a.get('volume', '')
    if v:
        # Take first 30 chars to group major volumes
        vols.add(v)

print(f"Total analyses: {len(analyses)}")
print(f"Useful: {len(useful)}")
print(f"Volume sections: {len(vols)}")

# Build categories from useful analyses
all_facts = Counter()
all_relationships = defaultdict(list)
all_emotions = []
all_speech = Counter()
all_behaviors = Counter()
all_defenses = Counter()
all_desires = Counter()
all_insecurities = Counter()
all_contradictions = []
all_food = Counter()
all_growth = []
all_scene_summaries = defaultdict(list)

for a in useful:
    sid = a.get('scene_id', '')
    vol = a.get('volume', '')[:50]
    ch = a.get('chapter', '')
    summary = a.get('scene_summary', '')

    all_scene_summaries[vol].append(f"  - [{sid}] {summary[:200]}")

    for f in a.get('facts', []):
        if isinstance(f, dict) and f.get('claim'):
            all_facts[f['claim'][:150]] += 1

    for r in a.get('relationships', []):
        if isinstance(r, dict) and r.get('target'):
            all_relationships[r['target']].append({
                'attitude': r.get('attitude', '')[:100],
                'behavior': r.get('behavior', '')[:100],
                'scene': sid,
            })

    for e in a.get('emotional_state', []):
        if isinstance(e, dict) and e.get('state'):
            all_emotions.append(e)

    for s in a.get('speech_patterns', []):
        if isinstance(s, dict) and s.get('pattern'):
            all_speech[s['pattern'][:100]] += 1

    for b in a.get('behavior_patterns', []):
        if isinstance(b, dict):
            txt = b.get('description') or b.get('pattern', '')
            if txt:
                all_behaviors[txt[:120]] += 1

    for d in a.get('defense_mechanisms', []):
        if isinstance(d, dict):
            txt = d.get('description') or d.get('mechanism', '')
            if txt:
                all_defenses[txt[:120]] += 1
        elif isinstance(d, str):
            all_defenses[d[:120]] += 1

    for d in a.get('desires', []):
        if isinstance(d, str):
            all_desires[d[:100]] += 1

    for i in a.get('insecurities', []):
        if isinstance(i, str):
            all_insecurities[i[:100]] += 1

    for c in a.get('contradictions_or_tensions', []):
        if isinstance(c, dict) and c.get('tension', ''):
            all_contradictions.append({'tension': c['tension'][:200], 'scene': sid})

    for h in a.get('food_or_daily_habits', []):
        if isinstance(h, str):
            all_food[h[:100]] += 1

    for g in a.get('character_growth_or_change', []):
        if isinstance(g, str):
            all_growth.append({'note': g[:200], 'scene': sid})
        elif isinstance(g, dict):
            txt = g.get('change', '') or g.get('growth', '') or ''
            if txt:
                all_growth.append({'note': txt[:200], 'scene': sid})

# Sort by frequency
top_facts = all_facts.most_common(50)
top_speech = all_speech.most_common(30)
top_behaviors = all_behaviors.most_common(30)
top_defenses = all_defenses.most_common(20)
top_desires = all_desires.most_common(20)
top_insecurities = all_insecurities.most_common(15)
top_food = all_food.most_common(25)

# Build markdown output
lines = []

lines.append("# 八奈见杏菜角色设定素材")
lines.append(f"\n> 基于 {len(useful)} 个有用场景的结构化分析，覆盖 {len(vols)} 个卷/章节")
lines.append("")

lines.append("## 卷目概览")
lines.append("")
for vol in sorted(all_scene_summaries.keys(), key=lambda v: list(all_scene_summaries.keys()).index(v)):
    scenes = all_scene_summaries[vol]
    lines.append(f"### {vol}")
    lines.append(f"场景数：{len(scenes)}")
    for s in scenes[:3]:  # only first 3 summaries per volume
        lines.append(s)
    if len(scenes) > 3:
        lines.append(f"  + ... 还有 {len(scenes) - 3} 个场景")
    lines.append("")

lines.append("## 核心事实（高频）")
for fact, count in top_facts:
    lines.append(f"- [{count}x] {fact}")
lines.append("")

lines.append("## 关系模型")
lines.append("")
for target in sorted(all_relationships.keys()):
    rels = all_relationships[target]
    lines.append(f"### 面对 {target}")
    attitudes = list(set(r['attitude'] for r in rels))
    behaviors = list(set(r['behavior'] for r in rels if r['behavior']))
    lines.append(f"- 态度模式：{' | '.join(attitudes[:5])}")
    lines.append(f"- 行为模式：{' | '.join(behaviors[:5])}")
    lines.append(f"- 涉及场景数：{len(rels)}")
    lines.append("")
lines.append("")

lines.append("## 情感状态汇总")
lines.append("")
for e in all_emotions[:40]:
    lines.append(f"- **{e.get('state', '?')}**（触发：{e.get('trigger', '?')[:60]}）")
    lines.append(f"  - 表面：{e.get('external_expression', '')[:80]}")
    lines.append(f"  - 内里：{e.get('hidden_layer', '')[:100]}")
lines.append(f"  + ... 还有 {len(all_emotions) - 40} 条情感记录")
lines.append("")

lines.append("## 说话风格")
lines.append("")
for pattern, count in top_speech:
    lines.append(f"- [{count}x] {pattern}")
lines.append("")

lines.append("## 行为模式")
lines.append("")
for behavior, count in top_behaviors:
    lines.append(f"- [{count}x] {behavior}")
lines.append("")

lines.append("## 防御机制")
lines.append("")
for defense, count in top_defenses:
    lines.append(f"- [{count}x] {defense}")
lines.append("")

lines.append("## 欲望与需求")
lines.append("")
for desire, count in top_desires:
    lines.append(f"- [{count}x] {desire}")
lines.append("")

lines.append("## 不安与软肋")
lines.append("")
for insecurity, count in top_insecurities:
    lines.append(f"- [{count}x] {insecurity}")
lines.append("")

lines.append("## 内在矛盾")
lines.append("")
for c in all_contradictions[:25]:
    lines.append(f"- {c['tension']}（{c['scene']}）")
lines.append("")

lines.append("## 食物习惯")
lines.append("")
for habit, count in top_food:
    lines.append(f"- [{count}x] {habit}")
lines.append("")

lines.append("## 角色成长轨迹")
lines.append("")
for g in all_growth[:15]:
    lines.append(f"- {g['note']}（{g['scene']}）")
lines.append("")

text = '\n'.join(lines)

with open(OUTPUT, 'w', encoding='utf-8') as f:
    f.write(text)

print(f"\nProfile input written to {OUTPUT}")
import os
size = os.path.getsize(OUTPUT)
print(f"File size: {size} bytes ({size/1024:.0f} KB)")
print(f"Characters: {len(text)}")
