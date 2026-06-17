"""
Fix known data issues:
1. 佳树 gender: "弟弟" -> "妹妹" in scene_analysis.jsonl (2 occurrences)
2. "后鞠知花" -> "小鞠知花" (1 occurrence)
"""
import json
import re

INPUT = r'D:\character\data\extracted\yanami_scene_analysis.jsonl'
OUTPUT = r'D:\character\data\extracted\yanami_scene_analysis.jsonl'

fixes = {
    '弟弟佳树': '妹妹佳树',
    '温水弟弟佳树': '温水妹妹佳树',
    '后鞠知花': '小鞠知花',
}

with open(INPUT, 'r', encoding='utf-8') as f:
    text = f.read()

count = 0
for old, new in fixes.items():
    occurrences = text.count(old)
    if occurrences > 0:
        text = text.replace(old, new)
        count += occurrences
        print(f"  {old} -> {new}: {occurrences} occurrences fixed")

with open(OUTPUT, 'w', encoding='utf-8') as f:
    f.write(text)

# Verify no remaining issues
print(f"\n总计修复: {count} 处")
for old, new in fixes.items():
    remaining = text.count(old)
    if remaining > 0:
        print(f"⚠️  {old}: 仍有 {remaining} 处残留")
    else:
        print(f"✅ {old}: 已全部修复")
