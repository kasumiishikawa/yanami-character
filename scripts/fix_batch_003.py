"""
Fix batch_003_analysis.json - specifically the invalid \' escape sequences.
"""
import re

fpath = r'D:\character\data\extracted\analysis\batch_003_analysis.json'

with open(fpath, 'r', encoding='utf-8') as f:
    text = f.read()

# Fix 1: Replace \' with ' (single quotes don't need escaping in JSON)
text = text.replace("\\'", "'")

# Fix 2: Replace any remaining '' with ' (double single quotes)
# But be careful - only fix within string values

# Verify it's valid now
import json
try:
    data = json.loads(text)
    print("JSON is now valid!")
    print(f"Scenes: {len(data)}")
except json.JSONDecodeError as e:
    print(f"Still invalid: {e}")
    # Show context
    ctx = text[max(0,e.pos-80):e.pos+80]
    print(f"Context: {repr(ctx)}")

# Write back
with open(fpath, 'w', encoding='utf-8') as f:
    f.write(text)

print("Done!")
