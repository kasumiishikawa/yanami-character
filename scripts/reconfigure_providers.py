"""
Reconfigure AstrBot providers:
- deepseek-v4-flash: default chat (keep)
- doubao seed 2.0 pro: image understanding
- doubao embedding: RAG embedding
"""
import json
import os

CONFIG_PATH = r'C:\Users\31697\data\cmd_config.json'

with open(CONFIG_PATH, 'r', encoding='utf-8-sig') as f:
    c = json.load(f)

# 1. Verify deepseek is still default chat
print("Current default:", c['provider_settings']['default_provider_id'])

# 2. Add doubao-seed-2.0-pro model (supports image input)
# Check if it already exists
existing_models = [p['id'] for p in c['provider']]
print("Existing models:", existing_models)

doubao_seed_exists = any('seed' in p['id'] for p in c['provider'])
doubao_embed_exists = any('embed' in p['id'] for p in c['provider'])

if not doubao_seed_exists:
    c['provider'].append({
        "id": "doubao/seed-2.0-pro",
        "enable": True,
        "provider_source_id": "doubao",
        "model": "seed-2.0-pro",
        "modalities": ["text", "image"],
        "custom_extra_body": {},
        "max_context_tokens": 256000,
        "reasoning": False
    })
    print("Added: doubao/seed-2.0-pro (vision)")

# 3. Set image caption provider to doubao/seed-2.0-pro
c['provider_settings']['default_image_caption_provider_id'] = "doubao/seed-2.0-pro"
print("Image caption provider -> doubao/seed-2.0-pro")

# 4. Add doubao-embedding model
if not doubao_embed_exists:
    c['provider'].append({
        "id": "doubao/doubao-embedding",
        "enable": True,
        "provider_source_id": "doubao",
        "model": "doubao-embedding",
        "modalities": ["text"],
        "custom_extra_body": {},
        "max_context_tokens": 4096,
        "reasoning": False
    })
    print("Added: doubao/doubao-embedding")

# 5. Set up knowledge base settings
# The default_kb_collection can reference a kb collection
# Set embedding for KB to use doubao
c['default_kb_collection'] = "yanami_kb"

# Verify final state
print("\n=== Final provider list ===")
for p in c['provider']:
    print(f"  {p['id']:40s} enable={p['enable']} modalities={p['modalities']}")

print(f"\nDefault model: {c['provider_settings']['default_provider_id']}")
print(f"Image caption: {c['provider_settings']['default_image_caption_provider_id']}")
print(f"Default KB: {c['default_kb_collection']}")

# Write
with open(CONFIG_PATH, 'w', encoding='utf-8-sig') as f:
    json.dump(c, f, ensure_ascii=False, indent=2)

print("\nConfig written successfully!")
