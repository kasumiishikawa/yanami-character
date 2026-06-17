"""Check AstrBot knowledge base structure."""
import sqlite3
import os

db_path = r'C:\Users\31697\data\knowledge_base\kb.db'

if not os.path.exists(db_path):
    print("Knowledge base DB not found")
    exit()

conn = sqlite3.connect(db_path)
cur = conn.cursor()

# Get all tables
cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cur.fetchall()
print(f"Tables: {[t[0] for t in tables]}")

for table_name, in tables:
    print(f"\n=== {table_name} ===")
    cur.execute(f"PRAGMA table_info({table_name})")
    cols = cur.fetchall()
    for col in cols:
        print(f"  {col[1]} ({col[2]}) nullable={not col[3]}")

    # Show row count and sample
    cur.execute(f"SELECT COUNT(*) FROM {table_name}")
    count = cur.fetchone()[0]
    print(f"  Row count: {count}")

    if count > 0:
        cur.execute(f"SELECT * FROM {table_name} LIMIT 2")
        rows = cur.fetchall()
        for row in rows:
            print(f"  Sample: {row}")
