"""
Fix: Add a dedicated embedding provider source for AstrBot.
Volcano ARK supports OpenAI-compatible embedding at the same base URL.
"""
import json, sqlite3

CONFIG_PATH = r'C:\Users\31697\data\cmd_config.json'
DB_PATH = r'C:\Users\31697\data\data_v4.db'

with open(CONFIG_PATH, 'r', encoding='utf-8-sig') as f:
    c = json.load(f)

# 1. Add a dedicated embedding provider source
embed_source = {
    "provider": "doubao-embed",
    "type": "openai_chat_completion",
    "provider_type": "embedding",
    "key": ["ark-b3073932-b876-4adc-990c-71191e1fdf78-280ce"],
    "api_base": "https://ark.cn-beijing.volces.com/api/v3/",
    "timeout": 120,
    "proxy": "",
    "custom_headers": {},
    "id": "doubao-embed",
    "enable": True
}

# Check if it already exists
existing_ids = [ps['id'] for ps in c['provider_sources']]
if 'doubao-embed' not in existing_ids:
    c['provider_sources'].append(embed_source)
    print("Added doubao-embed provider source")
else:
    print("doubao-embed already exists, updating...")
    for ps in c['provider_sources']:
        if ps['id'] == 'doubao-embed':
            ps.update(embed_source)

# 2. Clean up the broken yanami_kb from kb.db
kb_db = r'C:\Users\31697\data\knowledge_base\kb.db'
k_conn = sqlite3.connect(kb_db)
k_cur = k_conn.cursor()

# Find and delete yanami_kb
k_cur.execute("SELECT kb_id, kb_name FROM knowledge_bases")
for row in k_cur.fetchall():
    print(f"KB found: {row[1]} (id={row[0]})")
    if 'yanami' in row[1]:
        kb_id = row[0]
        k_cur.execute("DELETE FROM kb_media WHERE kb_id = ?", (kb_id,))
        k_cur.execute("DELETE FROM kb_documents WHERE kb_id = ?", (kb_id,))
        k_cur.execute("DELETE FROM knowledge_bases WHERE kb_id = ?", (kb_id,))
        k_conn.commit()
        print(f"Deleted yanami_kb (id={kb_id})")
k_conn.close()

# 3. Update config: remove default_kb_collection reference (let user create from UI)
c['default_kb_collection'] = ""
c['kb_names'] = []

# Write config
with open(CONFIG_PATH, 'w', encoding='utf-8-sig') as f:
    json.dump(c, f, ensure_ascii=False, indent=2)

print("\nDone! Config updated.")
print("Now restart AstrBot and create KB from the dashboard.")
print("When creating, look for 'doubao-embed' as the embedding provider.")
