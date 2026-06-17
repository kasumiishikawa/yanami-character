"""
Fix Doubao model names based on Volcano ARK API model list.
Correct IDs from the API response.
"""
import json

CONFIG_PATH = r'C:\Users\31697\data\cmd_config.json'

with open(CONFIG_PATH, 'r', encoding='utf-8-sig') as f:
    c = json.load(f)

# Update model entries
model_updates = {
    'doubao/doubao-pro-32k': {
        'model': 'doubao-1-5-pro-32k-250115',
        'max_context_tokens': 131072,
    },
    'doubao/Doubao-Seed-2.0-pro': {
        'model': 'doubao-seed-2-0-pro-260215',
        'max_context_tokens': 262144,
        'modalities': ['text', 'image'],
    },
    'doubao/Doubao-embedding-large': {
        'model': 'doubao-embedding-vision-251215',
        'max_context_tokens': 131072,
    },
}

for provider in c['provider']:
    pid = provider['id']
    if pid in model_updates:
        updates = model_updates[pid]
        old_model = provider['model']
        provider.update(updates)
        print(f"{pid}: {old_model} -> {provider['model']}")

# Also update image caption provider reference if needed
# The ID stays the same (doubao/Doubao-Seed-2.0-pro), only model name changed
print(f"\nImage caption provider: {c['provider_settings']['default_image_caption_provider_id']}")

# Write
with open(CONFIG_PATH, 'w', encoding='utf-8-sig') as f:
    json.dump(c, f, ensure_ascii=False, indent=2)

print("\nDone! Model names updated from ARK API.")
