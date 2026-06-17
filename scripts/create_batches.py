"""
Split candidate scenes into batches for LLM processing.
Each batch is a JSON file with ~15 scenes.
"""
import json
import math
from pathlib import Path

SCENES_PATH = r'D:\character\data\extracted\yanami_candidate_scenes.jsonl'
BATCH_DIR = r'D:\character\data\extracted\batches'
BATCH_SIZE = 15

with open(SCENES_PATH, 'r', encoding='utf-8') as f:
    scenes = [json.loads(line) for line in f]

Path(BATCH_DIR).mkdir(parents=True, exist_ok=True)

num_batches = math.ceil(len(scenes) / BATCH_SIZE)
print(f"Total scenes: {len(scenes)}")
print(f"Batches: {num_batches}")

for i in range(num_batches):
    start = i * BATCH_SIZE
    end = min(start + BATCH_SIZE, len(scenes))
    batch = scenes[start:end]

    batch_info = {
        "batch_id": f"batch_{i+1:03d}",
        "batch_start_scene": start + 1,
        "batch_end_scene": end,
        "scene_count": len(batch),
        "total_chars": sum(len(s['text']) for s in batch),
        "scenes": [
            {
                "scene_id": s["scene_id"],
                "volume": s.get("volume", ""),
                "chapter": s.get("chapter", ""),
                "matched_aliases": s.get("matched_aliases", []),
                "text": s["text"]
            }
            for s in batch
        ]
    }

    out_path = Path(BATCH_DIR) / f"batch_{i+1:03d}.json"
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(batch_info, f, ensure_ascii=False, indent=2)

    print(f"  {out_path.name}: {len(batch)} scenes, {batch_info['total_chars']} chars")

# Write manifest
manifest = {
    "total_scenes": len(scenes),
    "total_batches": num_batches,
    "batch_size": BATCH_SIZE,
    "batches": [f"batch_{i+1:03d}.json" for i in range(num_batches)]
}
with open(Path(BATCH_DIR) / 'manifest.json', 'w', encoding='utf-8') as f:
    json.dump(manifest, f, ensure_ascii=False, indent=2)

print(f"\nManifest written to {BATCH_DIR / 'manifest.json'}")
print("Done!")
