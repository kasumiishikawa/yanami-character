import json

with open(r'D:\character\data\extracted\yanami_candidate_scenes.jsonl', 'r', encoding='utf-8') as f:
    for i, line in enumerate(f):
        if i >= 3:
            break
        s = json.loads(line)
        print(f"=== {s['scene_id']} ===")
        print(f"卷: {s.get('volume','')}")
        print(f"章: {s.get('chapter','')}")
        print(f"命中: {s.get('matched_aliases','')}")
        print(f"文本长度: {len(s['text'])} 字符")
        print(f"文本前300字: {s['text'][:300]}")
        print()
