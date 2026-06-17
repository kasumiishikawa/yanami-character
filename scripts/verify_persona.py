import json

with open(r'C:\Users\31697\data\cmd_config.json', 'r', encoding='utf-8-sig') as f:
    c = json.load(f)

p = c['persona'][0]
print(f'Name: {p["name"]}')
print(f'System prompt length: {len(p["system_prompt"])} chars')
print(f'Default personality: {c["provider_settings"]["default_personality"]}')
print(f'Prompt prefix: {c["provider_settings"]["prompt_prefix"]}')
print(f'Begin dialogs: {len(p["begin_dialogs"])} entries')
sp = p['system_prompt']
print(f'\nPrompt start: {sp[:80]}...')
print(f'Prompt end: ...{sp[-80:]}')
