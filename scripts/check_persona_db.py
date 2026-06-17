"""Check AstrBot databases for persona storage."""
import sqlite3
import os

# The main data database
db_paths = [
    r'C:\Users\31697\data\data_v4.db',
    r'C:\Users\31697\data\knowledge_base\kb.db',
]

for db_path in db_paths:
    if not os.path.exists(db_path):
        print(f"{db_path}: NOT FOUND")
        continue

    print(f"\n=== {db_path} ===")
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    # Get all tables
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cur.fetchall()]
    print(f"Tables: {tables}")

    # Check each table for persona-related content
    for table in tables:
        cur.execute(f"PRAGMA table_info({table})")
        cols = [row[1] for row in cur.fetchall()]

        # Check if this table has persona-related columns
        if any(kw in str(cols).lower() for kw in ['persona', 'personality', 'prompt', 'system']):
            print(f"\n  Table: {table}")
            print(f"  Columns: {cols}")
            cur.execute(f"SELECT * FROM {table} LIMIT 3")
            rows = cur.fetchall()
            for row in rows:
                print(f"  Data: {row}")

    conn.close()

# Also check if there are any other db files
data_dir = r'C:\Users\31697\data'
for f in os.listdir(data_dir):
    if f.endswith('.db') or f.endswith('.sqlite'):
        full = os.path.join(data_dir, f)
        size = os.path.getsize(full)
        print(f"\nDB file: {f} ({size} bytes)")
