import json

# Search for 佳树 in scene analyses
found = []
with open(r'D:\character\data\extracted\yanami_scene_analysis.jsonl', 'r', encoding='utf-8') as f:
    for line in f:
        a = json.loads(line)
        text = json.dumps(a, ensure_ascii=False)
        if '佳树' in text and a.get('useful'):
            found.append((a.get('scene_id', ''), a.get('scene_summary', '')[:200]))

print(f"Scenes mentioning 佳树: {len(found)}")
for sid, summary in found:
    print(f"  {sid}: {summary}")

# Also check for game/游戏 mentions
print("\n=== 游戏/console mentions ===")
found2 = []
with open(r'D:\character\data\extracted\yanami_scene_analysis.jsonl', 'r', encoding='utf-8') as f:
    for line in f:
        a = json.loads(line)
        text = json.dumps(a, ensure_ascii=False)
        if ('游戏' in text or '游戏机' in text or 'switch' in text.lower() or '任天堂' in text) and a.get('useful'):
            found2.append((a.get('scene_id', ''), a.get('scene_summary', '')[:200]))

print(f"Scenes mentioning 游戏: {len(found2)}")
for sid, summary in found2:
    print(f"  {sid}: {summary}")

# Check the knowledge base file
print("\n=== 佳树 in knowledge base ===")
with open(r'D:\character\characters\yanami\full_knowledge.md', 'r', encoding='utf-8') as f:
    text = f.read()
    if '佳树' in text:
        idx = text.index('佳树')
        print(f"Found at position {idx}")
        print(text[max(0,idx-100):idx+200])
    else:
        print("佳树 NOT FOUND in knowledge base")

    if '游戏' in text:
        print("\n游戏 mentioned in knowledge base")
    else:
        print("\n游戏 NOT in knowledge base")
