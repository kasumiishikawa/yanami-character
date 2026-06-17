"""
Check how 佳树's gender is described across all data sources.
"""
import json
import re

# 1. Check scene analyses
print("=== scene_analysis.jsonl ===")
with open(r'D:\character\data\extracted\yanami_scene_analysis.jsonl', 'r', encoding='utf-8') as f:
    for line in f:
        a = json.loads(line)
        text = json.dumps(a, ensure_ascii=False)
        if '佳树' in text:
            mentions = re.findall(r'.{0,20}佳树.{0,20}', text)
            for m in mentions:
                if '弟弟' in m or '妹妹' in m or '弟' in m or '妹' in m or '兄弟' in m or '姐妹' in m:
                    print(f"  [{a.get('scene_id','')}] ...{m}...")

# 2. Check profile
print("\n=== yanami_profile.md ===")
with open(r'D:\character\data\extracted\yanami_profile.md', 'r', encoding='utf-8') as f:
    text = f.read()
    if '佳树' in text:
        for m in re.finditer(r'.{0,30}佳树.{0,30}', text):
            print(f"  ...{m.group()}...")

# 3. Check knowledge base
print("\n=== full_knowledge.md ===")
with open(r'D:\character\characters\yanami\full_knowledge.md', 'r', encoding='utf-8') as f:
    text = f.read()
    if '佳树' in text:
        for m in re.finditer(r'.{0,30}佳树.{0,30}', text):
            if '弟弟' in m.group() or '妹妹' in m.group() or '弟' in m.group() or '妹' in m.group():
                print(f"  ...{m.group()}...")

# 4. Check system prompt
print("\n=== system_prompt.md ===")
with open(r'D:\character\characters\yanami\system_prompt.md', 'r', encoding='utf-8') as f:
    text = f.read()
    if '佳树' in text:
        for m in re.finditer(r'.{0,30}佳树.{0,30}', text):
            print(f"  ...{m.group()}...")
    else:
        print("  (not mentioned)")
