import json

with open(r'C:\Users\31697\data\cmd_config.json', 'r', encoding='utf-8-sig') as f:
    c = json.load(f)

sp = c['persona'][0]['system_prompt']

# Check emoji rule
if '不要使用 Emoji' in sp:
    print('✅ Emoji rule found in system prompt')
else:
    print('❌ Emoji rule NOT found!')

# Show last 3 lines of system prompt to verify
lines = sp.strip().split('\n')
print(f'\nLast 6 lines of system prompt:')
for line in lines[-6:]:
    print(f'  {line}')

# Check model names
for p in c.get('provider', []):
    if 'seed' in p['id'] or 'Seed' in p['id']:
        print(f'\nSeed model: id={p["id"]} model_name={p["model"]}')
    if 'embed' in p['id'] or 'Embed' in p['id']:
        print(f'Embed model: id={p["id"]} model_name={p["model"]}')
