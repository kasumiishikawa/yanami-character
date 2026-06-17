"""
Fix problematic JSON in batch analysis files and merge into a single JSONL file.
"""
import json
import re
import os

ANALYSIS_DIR = r'D:\character\data\extracted\analysis'
OUTPUT_JSONL = r'D:\character\data\extracted\yanami_scene_analysis.jsonl'

def fix_and_parse(text, fname):
    """
    Try multiple strategies to parse JSON.
    Returns (parsed_data, method_string) or (None, error_msg).
    """
    # Strategy 1: standard parse
    try:
        return json.loads(text), 'ok'
    except json.JSONDecodeError:
        pass

    # Strategy 2: remove control characters
    text2 = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', text)
    try:
        return json.loads(text2), 'removed-ctrl'
    except json.JSONDecodeError:
        pass

    # Strategy 3: Handle \ before non-special chars (invalid escape)
    text3 = re.sub(r'\\([^"\\/bfnrtu])', r'\\\\\1', text2)
    try:
        return json.loads(text3), 'fixed-escape'
    except json.JSONDecodeError:
        pass

    # Strategy 4: Fix unescaped quotes inside JSON string values
    # Common pattern: "...加了"大具足虫粉末"的仙贝..." where inner " breaks JSON
    # We parse character by character and escape inner quotes
    result = []
    i = 0
    in_string = False
    string_start = -1
    while i < len(text2):
        ch = text2[i]

        if not in_string:
            if ch == '"':
                # Check if this is a structural quote (key or value start)
                in_string = True
                string_start = i
                result.append(ch)
            else:
                result.append(ch)
            i += 1
        else:
            if ch == '\\':
                # Escape sequence, skip next char
                result.append(ch)
                i += 1
                if i < len(text2):
                    result.append(text2[i])
                    i += 1
            elif ch == '"':
                # Potential end of string
                # Look ahead: next non-whitespace should be , or ] or } or :
                j = i + 1
                while j < len(text2) and text2[j] in ' \t\n\r':
                    j += 1
                if j < len(text2) and text2[j] in ',]}:\n':
                    # This is the real closing quote
                    in_string = False
                    result.append(ch)
                else:
                    # This is an unescaped inner quote, escape it
                    result.append('\\"')
                i += 1
            elif ord(ch) < 0x20:
                # Control character inside string
                result.append('\\u' + format(ord(ch), '04x'))
                i += 1
            else:
                result.append(ch)
                i += 1

    fixed = ''.join(result)
    try:
        return json.loads(fixed), 'fixed-inner-quotes'
    except json.JSONDecodeError:
        pass

    # Strategy 5: Try to extract complete JSON array using greedy brace matching
    try:
        # Find the first [ and match brackets
        start = text2.find('[')
        if start >= 0:
            depth = 0
            for j in range(start, len(text2)):
                if text2[j] == '[':
                    depth += 1
                elif text2[j] == ']':
                    depth -= 1
                    if depth == 0:
                        extracted = text2[start:j+1]
                        # Try to parse
                        try:
                            return json.loads(extracted), 'extracted-array'
                        except json.JSONDecodeError:
                            # Try fixing inner quotes in extracted portion
                            return fix_and_parse(extracted, fname)
    except Exception:
        pass

    return None, 'unfixable'


all_analyses = []
error_files = []
success_files = []
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

    data, method = fix_and_parse(raw, fname)

    if data is None:
        print(f"{fname}: UNFIXABLE ({method})")
        error_files.append(fname)
        continue

    if not isinstance(data, list):
        data = [data]

    success_files.append(fname)
    count = len(data)
    useful = sum(1 for s in data if s and isinstance(s, dict) and s.get('useful'))
    not_u = count - useful
    total_scenes += count
    useful_scenes += useful
    all_analyses.extend(data)

    status = 'OK' if method == 'ok' else method
    print(f"{fname}: {count} scenes ({useful} useful, {not_u} not) [{status}]")

# Write merged JSONL
with open(OUTPUT_JSONL, 'w', encoding='utf-8') as f:
    for analysis in all_analyses:
        if analysis and isinstance(analysis, dict):
            f.write(json.dumps(analysis, ensure_ascii=False) + '\n')

# Summary
print(f"\n{'='*50}")
print(f"Success: {len(success_files)}/31")
print(f"Failed: {len(error_files)}/31")
print(f"Total analyses: {total_scenes}")
print(f"Useful: {useful_scenes} ({round(useful_scenes/total_scenes*100, 1) if total_scenes else 0}%)")
print(f"Merged: {OUTPUT_JSONL}")

if error_files:
    print(f"\nFailed files: {', '.join(error_files)}")

# Save stats
stats = {
    "success_files": len(success_files),
    "error_files": len(error_files),
    "total_analyses": total_scenes,
    "useful_scenes": useful_scenes,
}
with open(os.path.join(ANALYSIS_DIR, '..', 'analysis_stats.json'), 'w', encoding='utf-8') as f:
    json.dump(stats, f, ensure_ascii=False, indent=2)
