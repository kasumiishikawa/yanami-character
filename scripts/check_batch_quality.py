import json

files_to_check = [
    r'D:\character\data\extracted\analysis\batch_013_analysis.json',
    r'D:\character\data\extracted\analysis\batch_014_analysis.json',
    r'D:\character\data\extracted\analysis\batch_016_analysis.json',
]

for fpath in files_to_check:
    print(f"=== {fpath.split('\\')[-1]} ===")
    try:
        with open(fpath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        total = len(data)
        useful = sum(1 for s in data if s.get('useful'))
        not_useful = total - useful

        print(f"Total scenes: {total}, Useful: {useful}, Not useful: {not_useful}")

        # Show first useful scene
        for s in data:
            if s.get('useful'):
                sid = s.get('scene_id', '?')
                summary = s.get('scene_summary', '')[:150]

                # Count fields
                facts = len(s.get('facts', []))
                relationships = len(s.get('relationships', []))
                emotions = len(s.get('emotional_state', []))
                desires = len(s.get('desires', []))
                insecurities = len(s.get('insecurities', []))
                speech = len(s.get('speech_patterns', []))
                behaviors = len(s.get('behavior_patterns', []))
                defenses = len(s.get('defense_mechanisms', []))
                rp_notes = len(s.get('roleplay_notes', []))

                print(f"  First useful scene: {sid}")
                print(f"  Summary: {summary}")
                print(f"  Fields: facts={facts} rels={relationships} emotions={emotions}")
                print(f"          desires={desires} insecurities={insecurities}")
                print(f"          speech={speech} behaviors={behaviors}")
                print(f"          defenses={defenses} rp_notes={rp_notes}")
                break
        else:
            print("  No useful scenes found")
    except Exception as e:
        print(f"  Error: {e}")
    print()
