import json

with open(r'D:\character\data\extracted\yanami_candidate_scenes.jsonl', 'r', encoding='utf-8') as f:
    for i, line in enumerate(f):
        if i >= 5:
            break
        s = json.loads(line)
        out_path = f'D:\\character\\data\\extracted\\pilot_scene_{i+1:02d}_full.txt'
        with open(out_path, 'w', encoding='utf-8') as out:
            out.write(s['text'])
        print(f'Written pilot_scene_{i+1:02d}_full.txt: {len(s["text"])} chars')
