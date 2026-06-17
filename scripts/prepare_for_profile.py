"""
Condense the analysis JSONL into a format suitable for profile building.
Groups by volume, extracts key patterns and evidence.
"""
import json
from collections import defaultdict

INPUT = r'D:\character\data\extracted\yanami_scene_analysis.jsonl'
OUTPUT = r'D:\character\data\extracted\yanami_condensed_for_profile.json'

# Read all analyses
analyses = []
with open(INPUT, 'r', encoding='utf-8') as f:
    for line in f:
        if line.strip():
            analyses.append(json.loads(line))

# Filter useful ones
useful = [a for a in analyses if a.get('useful')]

# Group by volume
by_volume = defaultdict(dict)
for a in useful:
    vol = a.get('volume', 'Unknown')
    if vol not in by_volume:
        by_volume[vol] = {
            'volume': vol,
            'scene_ids': [],
            'scene_count': 0,
            'all_summaries': [],
            'all_facts': [],
            'all_emotions': [],
            'all_relationships': [],
            'all_speech_patterns': [],
            'all_behavior_patterns': [],
            'all_defenses': [],
            'all_desires': [],
            'all_insecurities': [],
            'all_contradictions': [],
            'all_growth': [],
            'all_rp_notes': [],
            'all_food_habits': [],
        }
    v = by_volume[vol]
    v['scene_ids'].append(a.get('scene_id', ''))
    v['scene_count'] += 1
    v['all_summaries'].append(f"[{a.get('scene_id', '')}] {a.get('scene_summary', '')}")

    for f in a.get('facts', []):
        if isinstance(f, dict) and f.get('claim'):
            v['all_facts'].append(f['claim'][:120])
    for r in a.get('relationships', []):
        if isinstance(r, dict) and r.get('target') and r.get('attitude'):
            v['all_relationships'].append({
                'target': r['target'],
                'attitude': r['attitude'][:100],
                'behavior': r.get('behavior', '')[:100],
                'evidence': r.get('evidence_summary', '')[:100],
            })
    for e in a.get('emotional_state', []):
        if isinstance(e, dict) and e.get('state'):
            v['all_emotions'].append({
                'state': e['state'][:80],
                'trigger': e.get('trigger', '')[:80],
                'external': e.get('external_expression', '')[:80],
                'hidden': e.get('hidden_layer', '')[:100],
            })
    for s in a.get('speech_patterns', []):
        if isinstance(s, dict) and s.get('pattern'):
            v['all_speech_patterns'].append({
                'pattern': s['pattern'][:80],
                'example': s.get('example_summary', '')[:80],
                'when': s.get('when_used', '')[:60],
            })
    for b in a.get('behavior_patterns', []):
        if isinstance(b, dict):
            v['all_behavior_patterns'].append(b.get('description') or b.get('pattern', '')[:120])
    for d in a.get('defense_mechanisms', []):
        if isinstance(d, dict):
            v['all_defenses'].append(d.get('description') or d.get('mechanism', '')[:120])
    for d in a.get('desires', []):
        if isinstance(d, str):
            v['all_desires'].append(d[:100])
    for i in a.get('insecurities', []):
        if isinstance(i, str):
            v['all_insecurities'].append(i[:100])
    for c in a.get('contradictions_or_tensions', []):
        if isinstance(c, dict):
            v['all_contradictions'].append(c.get('tension', '')[:150])
    for g in a.get('character_growth_or_change', []):
        if isinstance(g, str):
            v['all_growth'].append(g[:150])
        elif isinstance(g, dict):
            v['all_growth'].append(g.get('change', '')[:150])
    for r in a.get('roleplay_notes', []):
        if isinstance(r, dict):
            v['all_rp_notes'].append({
                'situation': r.get('situation', '')[:80],
                'response': r.get('likely_response', '')[:100],
                'avoid': r.get('avoid', '')[:80],
            })
    for h in a.get('food_or_daily_habits', []):
        if isinstance(h, str):
            v['all_food_habits'].append(h[:100])

# Build condensed output
condensed = {
    "total_scenes_analyzed": len(analyses),
    "useful_scenes": len(useful),
    "non_useful_scenes": len(analyses) - len(useful),
    "volumes_covered": sorted(by_volume.keys()),
    "per_volume": [],
}

for vol_name in sorted(by_volume.keys(), key=lambda v: list(by_volume.keys()).index(v)):
    v = by_volume[vol_name]
    entry = {
        'volume': v['volume'],
        'scene_count': v['scene_count'],
        'summaries': v['all_summaries'],
        'key_facts': list(set(v['all_facts']))[:30],
        'key_emotion_patterns': v['all_emotions'],
        'key_relationships': v['all_relationships'],
        'speech_patterns': list({s['pattern']: s for s in v['all_speech_patterns']}.values()),
        'behavior_patterns': list(set(v['all_behavior_patterns']))[:20],
        'defense_mechanisms': list(set(v['all_defenses']))[:15],
        'desires': list(set(v['all_desires']))[:15],
        'insecurities': list(set(v['all_insecurities']))[:10],
        'contradictions': list(set(v['all_contradictions']))[:15],
        'food_habits': list(set(v['all_food_habits']))[:15],
        'roleplay_reference': v['all_rp_notes'],
        'character_growth': list(set(v['all_growth']))[:10],
    }
    condensed['per_volume'].append(entry)

# Cross-volume summary
all_emotions = []
all_speech = {}
all_behaviors = {}
all_defenses = {}
all_desires = {}
all_insecurities = {}
all_contradictions = {}
all_growth = {}
all_food = {}
all_rp = []
all_relationships_by_target = defaultdict(list)

for vol_name in sorted(by_volume.keys()):
    v = by_volume[vol_name]
    for e in v['all_emotions']:
        all_emotions.append(e)
    for s in v['all_speech_patterns']:
        all_speech[s['pattern']] = s
    for b in v['all_behavior_patterns']:
        all_behaviors[b] = True
    for d in v['all_defenses']:
        all_defenses[d] = True
    for d in v['all_desires']:
        all_desires[d] = True
    for i in v['all_insecurities']:
        all_insecurities[i] = True
    for c in v['all_contradictions']:
        all_contradictions[c] = True
    for g in v['all_growth']:
        all_growth[g] = True
    for h in v['all_food_habits']:
        all_food[h] = True
    for r in v['all_rp_notes']:
        all_rp.append(r)
    for r in v['all_relationships']:
        all_relationships_by_target[r['target']].append(r)

condensed['cross_volume_analysis'] = {
    'all_emotion_states': list(set(e['state'] for e in all_emotions if isinstance(e, dict))),
    'all_emotions_count': len(all_emotions),
    'all_speech_patterns': list(all_speech.values()),
    'all_behavior_patterns': list(all_behaviors.keys()),
    'all_defense_mechanisms': list(all_defenses.keys()),
    'all_desires': list(all_desires.keys()),
    'all_insecurities': list(all_insecurities.keys()),
    'all_contradictions': list(all_contradictions.keys()),
    'all_growth_indicators': list(all_growth.keys()),
    'all_food_habits': list(all_food.keys()),
    'relationship_summary': {
        target: {
            'attitudes': list(set(r['attitude'] for r in rels)),
            'behaviors': list(set(r['behavior'] for r in rels if r['behavior'])),
        }
        for target, rels in sorted(all_relationships_by_target.items())
    },
}

with open(OUTPUT, 'w', encoding='utf-8') as f:
    json.dump(condensed, f, ensure_ascii=False, indent=2)

print(f"Total analyses: {len(analyses)}")
print(f"Useful: {len(useful)}")
print(f"Volumes covered: {len(condensed['volumes_covered'])}")
print(f"Condensed file size: ")
import os
size = os.path.getsize(OUTPUT)
print(f"  {size} bytes ({size/1024:.0f} KB)")

# Print per-volume scene counts
print(f"\nScenes per volume:")
for v in condensed['per_volume']:
    print(f"  {v['volume'][:50]}: {v['scene_count']} scenes")
