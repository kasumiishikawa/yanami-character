import json

with open(r'C:\Users\31697\data\cmd_config.json', 'r', encoding='utf-8-sig') as f:
    c = json.load(f)

print("=== Provider Models ===")
for p in c.get('provider', []):
    print(f'  {p["id"]:45s} model={p["model"]:30s} modalities={p["modalities"]}')

print(f'\n=== Key Settings ===')
print(f'Default model:       {c["provider_settings"]["default_provider_id"]}')
print(f'Image caption:       {c["provider_settings"]["default_image_caption_provider_id"]}')
print(f'Default personality: {c["provider_settings"]["default_personality"]}')

# Check KB
import sqlite3
try:
    conn = sqlite3.connect(r'C:\Users\31697\data\knowledge_base\kb.db')
    cur = conn.cursor()
    cur.execute("SELECT kb_name, embedding_provider_id, doc_count, chunk_count FROM knowledge_bases")
    for row in cur.fetchall():
        print(f'\nKnowledge Base: {row[0]}')
        print(f'  Embedding provider: {row[1]}')
        print(f'  Documents: {row[2]}, Chunks: {row[3]}')
    conn.close()
except Exception as e:
    print(f'\nKB check: {e}')
