import json

with open(r'C:\Users\31697\data\cmd_config.json', 'r', encoding='utf-8-sig') as f:
    c = json.load(f)

for ps in c.get('provider_sources', []):
    if ps['id'] == 'doubao':
        print(f'Provider: {ps["provider"]}')
        print(f'API Base: {ps["api_base"]}')
        print(f'Key: {ps["key"][0][:25]}...')
        print(f'Type: {ps["type"]}')
        print(f'Enable: {ps["enable"]}')

for p in c.get('provider', []):
    if 'doubao' in p['id']:
        print(f'\nModel entry:')
        print(f'  ID: {p["id"]}')
        print(f'  Model: {p["model"]}')
        print(f'  Max tokens: {p["max_context_tokens"]}')
        print(f'  Enable: {p["enable"]}')

print(f'\nDefault model: {c["provider_settings"]["default_provider_id"]}')
print(f'Persona enabled: {c["persona"][0]["name"]} (default)')
