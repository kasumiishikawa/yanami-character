"""
Fix common JSON issues in batch analysis files and merge all into a single JSONL.
Handles: unescaped quotes, control characters, trailing commas, etc.
"""
import json
import re
import os

ANALYSIS_DIR = r'D:\character\data\extracted\analysis'
OUTPUT_JSONL = r'D:\character\data\extracted\yanami_scene_analysis.jsonl'

def try_parse(text):
    """Try multiple strategies to parse JSON."""
    # Strategy 1: standard parse
    try:
        return json.loads(text), None
    except json.JSONDecodeError as e:
        pass

    # Strategy 2: remove control characters
    cleaned = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', text)
    try:
        return json.loads(cleaned), None
    except json.JSONDecodeError:
        pass

    # Strategy 3: escape unescaped double quotes inside strings
    # This handles cases where " appears inside a JSON string value
    # Pattern: look for " that is not preceded by \ and not at a JSON structural position
    # We use a simplified approach: find problematic quotes and escape them
    lines = text.split('\n')
    fixed_lines = []
    for line in lines:
        stripped = line.strip()
        # Only process lines that look like string values (contain colon)
        if ':' in stripped:
            # Find the value part (after the first colon)
            colon_idx = line.find(':')
            before_colon = line[:colon_idx+1]
            after_colon = line[colon_idx+1:]

            # Check if the value is a string (starts with ")
            value_part = after_colon.strip()
            if value_part.startswith('"') and not value_part.startswith('"[') and not value_part.startswith('"{'):
                # This is a string value - escape inner double quotes
                # Remove the outer quotes, escape inner quotes, re-add outer quotes
                # But be careful with already-escaped quotes
                inner = value_part[1:]
                # Find the closing quote (last " before , or end)
                if inner.endswith('",'):
                    inner = inner[:-2]
                    suffix = '",'
                elif inner.endswith('"'):
                    inner = inner[:-1]
                    suffix = '"'
                else:
                    suffix = ''

                # Escape any remaining unescaped quotes
                inner = inner.replace('\\"', '\x00ESCAPED\x00')
                inner = inner.replace('"', '\\"')
                inner = inner.replace('\x00ESCAPED\x00', '\\"')

                after_colon_fixed = ' "' + inner + suffix
                line = before_colon + after_colon_fixed
        fixed_lines.append(line)

    fixed_text = '\n'.join(fixed_lines)
    try:
        return json.loads(fixed_text), "fixed-unescaped-quotes"
    except json.JSONDecodeError as e:
        pass

    # Strategy 4: extremely lenient - extract individual JSON objects
    # Try to find complete JSON arrays or objects by bracket matching
    try:
        # Try parsing each top-level object/array
        decoder = json.JSONDecoder(strict=False)
        decoded, _ = decoder.raw_decode(text)
        return decoded, "lenient-decoder"
    except (json.JSONDecodeError, ValueError):
        pass

    return None, "all-strategies-failed"


all_analyses = []
error_files = []
valid_files = 0
total_scenes = 0
useful_scenes = 0

for i in range(1, 32):
    fname = f'batch_{i:03d}_analysis.json'
    fpath = os.path.join(ANALYSIS_DIR, fname)

    if not os.path.exists(fpath):
        print(f"{fname}: NOT FOUND")
        continue

    with open(fpath, 'r', encoding='utf-8') as f:
        raw = f.read()

    data, method = try_parse(raw)

    if data is None:
        print(f"{fname}: COULD NOT FIX - saving raw for inspection")
        error_files.append(fname)
        continue

    if not isinstance(data, list):
        data = [data]

    valid_files += 1
    count = len(data)
    useful = sum(1 for s in data if s and s.get('useful'))
    not_u = count - useful
    total_scenes += count
    useful_scenes += useful
    all_analyses.extend(data)

    method_str = method or "ok"
    print(f"{fname}: {count} scenes ({useful} useful, {not_u} not) [{method_str}]")

# Write merged JSONL
with open(OUTPUT_JSONL, 'w', encoding='utf-8') as f:
    for analysis in all_analyses:
        if analysis:  # skip None
            f.write(json.dumps(analysis, ensure_ascii=False) + '\n')

print(f"\n===== MERGE RESULT =====")
print(f"Valid files: {valid_files}/31")
print(f"Error files: {len(error_files)}")
print(f"Total analyses: {total_scenes}")
print(f"Useful: {useful_scenes} ({round(useful_scenes/total_scenes*100, 1) if total_scenes else 0}%)")
print(f"Output: {OUTPUT_JSONL}")

if error_files:
    print(f"\nFailed batches: {', '.join(error_files)}")
