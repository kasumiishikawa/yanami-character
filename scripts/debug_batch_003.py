"""
Deep debug of batch_003 JSON error.
"""
import json

fpath = r'D:\character\data\extracted\analysis\batch_003_analysis.json'

with open(fpath, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Check line 798 (0-indexed 797)
line = lines[797]
print(f"Line 798 raw repr: {repr(line)}")
print(f"Line 798 char codes: {[ord(c) for c in line]}")

# Try to find the issue manually
text = ''.join(lines)

# Strategy: use raw_decode to find the problem area
decoder = json.JSONDecoder()
pos = 0
while pos < len(text):
    try:
        # Skip whitespace
        while pos < len(text) and text[pos] in ' \t\n\r':
            pos += 1
        if pos >= len(text):
            break
        obj, end = decoder.raw_decode(text, pos)
        pos = end
    except json.JSONDecodeError as e:
        print(f"\nParse error at pos {e.pos}: {e.msg}")
        print(f"Line {text[:e.pos].count('\\n') + 1}")
        ctx_start = max(0, e.pos - 100)
        ctx_end = min(len(text), e.pos + 80)
        context = text[ctx_start:ctx_end]
        print(f"Context: {repr(context)}")
        print(f"\nChar codes around error:")
        for i in range(e.pos-10, e.pos+5):
            if 0 <= i < len(text):
                print(f"  pos {i}: {repr(text[i])} (U+{ord(text[i]):04X})")
        break
