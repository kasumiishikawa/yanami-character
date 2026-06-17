"""
Comprehensive data audit: find contradictions and errors in scene analyses.
"""
import json
import re
from collections import defaultdict, Counter

ANALYSIS_PATH = r'D:\character\data\extracted\yanami_scene_analysis.jsonl'

analyses = []
with open(ANALYSIS_PATH, 'r', encoding='utf-8') as f:
    for line in f:
        if line.strip():
            a = json.loads(line)
            if a.get('useful'):
                analyses.append(a)

print(f"Total useful analyses: {len(analyses)}\n")

# ── 1. 佳树 gender audit ──
print("=" * 60)
print("1. 佳树 性别矛盾检查")
print("=" * 60)
jia_shu_refs = []
for a in analyses:
    text = json.dumps(a, ensure_ascii=False)
    if '佳树' in text:
        sid = a.get('scene_id', '')
        summary = a.get('scene_summary', '')
        facts = a.get('facts', [])
        rels = a.get('relationships', [])
        # Check summary
        if '妹妹' in summary:
            jia_shu_refs.append((sid, 'summary-妹妹', summary[:100]))
        if '弟弟' in summary:
            jia_shu_refs.append((sid, '❌ summary-弟弟 ✗', summary[:100]))
        # Check relationships
        for r in rels:
            if isinstance(r, dict) and '佳树' in str(r):
                target = r.get('target', '')
                if '弟弟' in target:
                    jia_shu_refs.append((sid, f'❌ rel-弟弟 ✗', target))
                elif '妹妹' in target:
                    jia_shu_refs.append((sid, f'rel-妹妹', target))

for sid, ref_type, detail in jia_shu_refs:
    print(f"  {sid:30s} {ref_type:25s} {detail[:80]}")

# ── 2. 温水 gender ──
print("\n" + "=" * 60)
print("2. 温水 称呼检查")
print("=" * 60)
onsen_refs = defaultdict(list)
for a in analyses:
    text = json.dumps(a, ensure_ascii=False)
    if '温水' in text:
        sid = a.get('scene_id', '')
        for m in re.finditer(r'温水[^一-鿿]*(?:君|君|同学|くん|さん)', text[:200]):
            pass  # just checking no issues
# Check relationships for 温水
for a in analyses:
    for r in a.get('relationships', []):
        if isinstance(r, dict) and r.get('target') == '温水':
            onsen_refs[r.get('attitude', '')[:80]].append(a.get('scene_id',''))
print(f"  温水在关系表中出现 {sum(len(v) for v in onsen_refs.values())} 次")
for att, sids in sorted(onsen_refs.items()):
    print(f"    {att[:80]:50s} ({len(sids)} scenes)")

# ── 3. 草介/华恋 关系描述 ──
print("\n" + "=" * 60)
print("3. 草介 关系描述一致性")
print("=" * 60)
kusaka_refs = defaultdict(list)
for a in analyses:
    for r in a.get('relationships', []):
        if isinstance(r, dict) and r.get('target') in ['袴田草介', '袴田']:
            kusaka_refs[r.get('attitude', '')[:60]].append(a.get('scene_id',''))
for att, sids in sorted(kusaka_refs.items()):
    print(f"    {att[:60]:50s} ({len(sids)} scenes)")

print("\n" + "=" * 60)
print("4. 华恋 关系描述一致性")
print("=" * 60)
karen_refs = defaultdict(list)
for a in analyses:
    for r in a.get('relationships', []):
        if isinstance(r, dict) and r.get('target') in ['姬宫华恋', '姬宫', '华恋']:
            karen_refs[r.get('attitude', '')[:60]].append(a.get('scene_id',''))
for att, sids in sorted(karen_refs.items()):
    print(f"    {att[:60]:50s} ({len(sids)} scenes)")

# ── 4. Check for other potential character gender/role issues ──
print("\n" + "=" * 60)
print("5. 其他角色性别角色检查")
print("=" * 60)
character_rel_targets = defaultdict(set)
for a in analyses:
    for r in a.get('relationships', []):
        if isinstance(r, dict) and r.get('target'):
            character_rel_targets[r['target']].add(r.get('attitude', '')[:60])

for char, attitudes in sorted(character_rel_targets.items()):
    if char in ['温水', '八奈见']:
        continue
    att_list = list(attitudes)[:3]
    print(f"  {char:20s}: {', '.join(att_list)}")

# ── 5. Check number of scenes per volume for coverage ──
print("\n" + "=" * 60)
print("6. 数据量统计")
print("=" * 60)
from collections import Counter
vol_counts = Counter()
for a in analyses:
    vol = a.get('volume', '未知')[:30]
    vol_counts[vol] += 1
print(f"  总有用场景: {len(analyses)}")
print(f"  覆盖卷/章节数: {len(vol_counts)}")
for vol, count in vol_counts.most_common(5):
    print(f"    {vol:30s}: {count} scenes")
