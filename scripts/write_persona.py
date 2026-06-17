"""
Add Yanami Anna persona to AstrBot config and set as default.
"""
import json
import os

CONFIG_PATH = r'C:\Users\31697\data\cmd_config.json'
SYSTEM_PROMPT_PATH = r'D:\character\deploy\system_prompt.md'

# Read system prompt
with open(SYSTEM_PROMPT_PATH, 'r', encoding='utf-8') as f:
    system_prompt = f.read()

# Read config
with open(CONFIG_PATH, 'r', encoding='utf-8-sig') as f:
    config = json.load(f)

# Create persona entry
yanami_persona = {
    "name": "八奈见杏菜",
    "system_prompt": system_prompt.strip(),
    "begin_dialogs": [],
    "model": None,
    "tools": None,
    "skills": None
}

# Add to persona array
config['persona'] = [yanami_persona]

# Set as default personality
config['provider_settings']['default_personality'] = "八奈见杏菜"

# Write back
with open(CONFIG_PATH, 'w', encoding='utf-8-sig') as f:
    json.dump(config, f, ensure_ascii=False, indent=2)

print(f"Persona '八奈见杏菜' added to config")
print(f"Default personality set to: 八奈见杏菜")
print(f"System prompt length: {len(system_prompt.strip())} chars")

# Verify
with open(CONFIG_PATH, 'r', encoding='utf-8-sig') as f:
    verify = json.load(f)
print(f"\nVerification:")
print(f"  persona count: {len(verify.get('persona', []))}")
print(f"  default_personality: {verify['provider_settings']['default_personality']}")
print(f"  persona name: {verify['persona'][0]['name']}")
