import json
import os

ANALYSIS_DIR = r'D:\character\data\extracted\analysis'
OUTPUT_JSONL = r'D:\character\data\extracted\yanami_scene_analysis.jsonl'
OUTPUT_STATS = r'D:\character\data\extracted\analysis_stats.json'

total_scenes = 0
useful_scenes = 0
not_useful_scenes = 0
parse_errors = 0
valid_files = 0
error_files = []
all_analyses = []

for i in range(1, 32):
    fname = f'batch_{i:03d}_analysis.json'
    fpath = os.path.join(ANALYSIS_DIR, fname)

    if not os.path.exists(fpath):
        print(f"{fname}: FILE NOT FOUND")
        error_files.append(fname)
        continue

    with open(fpath, 'r', encoding='utf-8') as f:
        raw = f.read()

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"{fname}: JSON ERROR - {e}")
        # Try to fix: find and replace control characters
        import re
        fixed = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', raw)
        try:
            data = json.loads(fixed)
            print(f"  -> Fixed by removing control chars")
        except json.JSONDecodeError as e2:
            print(f"  -> Cannot fix: {e2}")
            error_files.append(fname)
            continue

    if not isinstance(data, list):
        data = [data]

    valid_files += 1
    count = len(data)
    total_scenes += count

    useful = sum(1 for s in data if s.get('useful'))
    not_u = count - useful
    useful_scenes += useful
    not_useful_scenes += not_u

    all_analyses.extend(data)
    print(f"{fname}: {count} scenes ({useful} useful, {not_u} not useful)")

# Write merged JSONL
with open(OUTPUT_JSONL, 'w', encoding='utf-8') as f:
    for analysis in all_analyses:
        f.write(json.dumps(analysis, ensure_ascii=False) + '\n')

# Stats
stats = {
    "total_batches": 31,
    "valid_files": valid_files,
    "error_files": error_files,
    "total_scenes_analyzed": total_scenes,
    "useful_scenes": useful_scenes,
    "not_useful_scenes": not_useful_scenes,
    "useful_percentage": round(useful_scenes / total_scenes * 100, 1) if total_scenes else 0,
    "output_file": OUTPUT_JSONL,
}

with open(OUTPUT_STATS, 'w', encoding='utf-8') as f:
    json.dump(stats, f, ensure_ascii=False, indent=2)

print(f"\n===== MERGE COMPLETE =====")
print(f"Valid files: {valid_files}/31")
print(f"Parse errors: {len(error_files)} files")
print(f"Total analyses: {total_scenes}")
print(f"Useful: {useful_scenes} ({stats['useful_percentage']}%)")
print(f"Not useful: {not_useful_scenes}")
print(f"Output: {OUTPUT_JSONL}")
