import json

with open(r'D:\character\data\extracted\yanami_candidate_scenes.jsonl', 'r', encoding='utf-8') as f:
    scenes = [json.loads(line) for line in f]

# Scene length distribution
lengths = [len(s['text']) for s in scenes]
total_chars = sum(lengths)
avg_chars = total_chars / len(scenes) if scenes else 0

short = sum(1 for l in lengths if l < 500)
medium = sum(1 for l in lengths if 500 <= l < 2000)
long = sum(1 for l in lengths if 2000 <= l < 5000)
very_long = sum(1 for l in lengths if l >= 5000)

print(f"Total scenes: {len(scenes)}")
print(f"Total characters: {total_chars}")
print(f"Average chars per scene: {avg_chars:.0f}")
print(f"Min chars: {min(lengths)}, Max chars: {max(lengths)}")
print()
print("Length distribution:")
print(f"  <500 chars (likely useless): {short}")
print(f"  500-2000 chars: {medium}")
print(f"  2000-5000 chars: {long}")
print(f"  5000+ chars: {very_long}")
print()

# Volume distribution
from collections import Counter
volume_counts = Counter(s.get('volume', 'unknown') for s in scenes)
print("Volume distribution:")
for vol, count in volume_counts.most_common():
    print(f"  {vol[:40] if vol else 'unknown'}: {count}")

print()
# Preview some mid-length scenes
print("Sample scene lengths (first 30):")
for i, l in enumerate(lengths[:30]):
    print(f"  scene {i+1:3d}: {l:5d} chars - {'USEFUL' if l >= 500 else 'SHORT'}")
