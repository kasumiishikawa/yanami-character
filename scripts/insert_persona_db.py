"""
Insert Yanami persona into AstrBot database correctly.
AstrBot stores personas in data_v4.db, NOT in cmd_config.json's persona array.
"""
import sqlite3
import json
import uuid
from datetime import datetime

DB_PATH = r'C:\Users\31697\data\data_v4.db'
CONFIG_PATH = r'C:\Users\31697\data\cmd_config.json'

# Read system prompt from cmd_config (which has the latest version with emoji rules)
with open(CONFIG_PATH, 'r', encoding='utf-8-sig') as f:
    config = json.load(f)

# Get the latest system prompt (from our earlier config edits)
system_prompt = config['persona'][0]['system_prompt']

# Also get begin_dialogs if any
begin_dialogs = config['persona'][0].get('begin_dialogs', [])

# Connect to DB
conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

now = datetime.now().isoformat()

# 1. Create folder entry
folder_id = str(uuid.uuid4())
cur.execute("""
    INSERT INTO persona_folders
    (created_at, updated_at, id, folder_id, name, parent_id, description, sort_order)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
""", (
    now, now,
    1,  # id (auto-increment, but use explicit for first entry)
    folder_id,
    "八奈见杏菜",  # name — this is what displays in the dashboard
    None,  # parent_id
    "《敗北女角太多了！》八奈见杏菜的角色人格",  # description
    0  # sort_order
))
print(f"Inserted folder: 八奈见杏菜 (folder_id={folder_id})")

# 2. Create persona entry linked to folder
persona_id = str(uuid.uuid4())
cur.execute("""
    INSERT INTO personas
    (created_at, updated_at, id, persona_id, system_prompt, begin_dialogs,
     tools, skills, custom_error_message, folder_id, sort_order)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
""", (
    now, now,
    1,  # id
    persona_id,  # persona_id (UUID)
    system_prompt,  # the actual system prompt
    json.dumps(begin_dialogs, ensure_ascii=False),  # begin_dialogs as JSON string
    None,  # tools
    None,  # skills
    None,  # custom_error_message
    folder_id,  # link to folder
    0  # sort_order
))
print(f"Inserted persona (prompt: {len(system_prompt)} chars)")

conn.commit()

# 3. Verify
cur.execute("""
    SELECT pf.name, p.persona_id, p.system_prompt
    FROM personas p
    JOIN persona_folders pf ON p.folder_id = pf.folder_id
    WHERE pf.name = '八奈见杏菜'
""")
result = cur.fetchone()
if result:
    print(f"\n✅ Verification: persona '{result[0]}' found in database")
    print(f"   persona_id: {result[1]}")
    print(f"   prompt length: {len(result[2])} chars")
else:
    print("\n❌ Verification failed!")

conn.close()

# 4. Note: also update cmd_config.json's default_personality and cleanup the persona array
# Actually, the config's persona array is probably not used, but let's keep it for reference
print("\nNow restart AstrBot to pick up the DB changes.")
