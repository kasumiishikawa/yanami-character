import json

for fname in ['batch_003_analysis.json', 'batch_030_analysis.json']:
    fpath = f'D:\\character\\data\\extracted\\analysis\\{fname}'
    with open(fpath, 'r', encoding='utf-8') as f:
        text = f.read()

    print(f"=== {fname} ===")
    print(f"Size: {len(text)} chars")

    # Find the JSON error position
    for strategy in ['standard']:
        try:
            json.loads(text)
            print("Valid JSON!")
        except json.JSONDecodeError as e:
            print(f"Error: {e}")
            # Show context around error
            pos = e.pos
            start = max(0, pos - 100)
            end = min(len(text), pos + 50)
            context = text[start:end]
            print(f"Context around error:")
            print(f"  ...{repr(context)}...")
            # Show line number
            line_no = text[:pos].count('\n') + 1
            print(f"  Line: {line_no}")

    # Try to use raw_decode to get partial data
    try:
        decoder = json.JSONDecoder()
        # Try to find where the valid JSON starts
        for search_start in range(min(1000, len(text))):
            if text[search_start] in '[{':
                try:
                    obj, end = decoder.raw_decode(text, search_start)
                    print(f"\nPartial decode: found valid JSON at pos {search_start}")
                    if isinstance(obj, list):
                        print(f"  Array with {len(obj)} elements")
                        print(f"  First valid scene: {obj[0].get('scene_id', '?') if obj else 'N/A'}")
                    break
                except json.JSONDecodeError:
                    continue
    except Exception:
        pass

    print()
