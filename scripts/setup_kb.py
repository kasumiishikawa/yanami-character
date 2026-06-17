"""
Set up AstrBot knowledge base for Yanami character:
1. Create a knowledge base collection with doubao embedding
2. Import yanami_rag.md as documents
"""
import json
import os
import uuid
from datetime import datetime

# Need to handle SQLite
import sqlite3

KB_PATH = r'C:\Users\31697\data\knowledge_base\kb.db'
RAG_PATH = r'D:\character\deploy\yanami_rag.md'
CONFIG_PATH = r'C:\Users\31697\data\cmd_config.json'

# Read config
with open(CONFIG_PATH, 'r', encoding='utf-8-sig') as f:
    config = json.load(f)

# Check if KB already has the yanami collection
conn = sqlite3.connect(KB_PATH)
cur = conn.cursor()

cur.execute("SELECT kb_id, kb_name, embedding_provider_id FROM knowledge_bases")
existing = cur.fetchall()
print(f"Existing collections: {existing}")

yanami_kb_exists = any('yanami' in row[1] for row in existing)

if not yanami_kb_exists:
    kb_id = str(uuid.uuid4())
    now = datetime.now().isoformat()

    cur.execute("""
        INSERT INTO knowledge_bases
        (id, kb_id, kb_name, description, emoji, embedding_provider_id,
         chunk_size, chunk_overlap, top_k_dense, top_k_sparse, top_m_final,
         created_at, updated_at, doc_count, chunk_count)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        1,  # id
        kb_id,  # kb_id (UUID)
        "yanami_kb",  # kb_name
        "八奈见杏菜角色知识库 - 基于原作1-8卷325个场景",  # description
        "📕",  # emoji
        "doubao",  # embedding_provider_id (use doubao provider)
        500,  # chunk_size
        50,  # chunk_overlap
        20,  # top_k_dense
        20,  # top_k_sparse
        5,  # top_m_final
        now, now,  # created_at, updated_at
        0, 0  # doc_count, chunk_count
    ))
    conn.commit()

    # Update config to set default KB
    config['default_kb_collection'] = kb_id
    with open(CONFIG_PATH, 'w', encoding='utf-8-sig') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

    print(f"Created knowledge base: yanami_kb (id={kb_id})")
    print(f"Embedding provider: doubao")
else:
    kb_id = existing[0][0]
    print(f"Knowledge base already exists: {existing[0][1]} (id={kb_id})")

# Now read the RAG markdown and create document chunks
with open(RAG_PATH, 'r', encoding='utf-8') as f:
    rag_content = f.read()

print(f"\nRAG document: {len(rag_content)} chars")

# Split by topics (## 话题)
sections = rag_content.split('\n## ')
doc_id = str(uuid.uuid4())
now = datetime.now().isoformat()

# Insert document record
cur.execute("""
    INSERT INTO kb_documents
    (id, doc_id, kb_id, doc_name, file_type, file_size, file_path,
     chunk_count, media_count, created_at, updated_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
""", (
    1,  # id
    doc_id,
    kb_id,
    "yanami_rag.md",
    "markdown",
    len(rag_content),
    RAG_PATH,
    len(sections),
    0,
    now,
    now
))

print(f"Added document: yanami_rag.md ({len(sections)} sections)")

# Update doc count
cur.execute("UPDATE knowledge_bases SET doc_count = doc_count + 1, chunk_count = chunk_count + ? WHERE kb_id = ?",
            (len(sections), kb_id))
conn.commit()

# Verify
cur.execute("SELECT kb_name, doc_count, chunk_count, embedding_provider_id FROM knowledge_bases WHERE kb_id = ?", (kb_id,))
result = cur.fetchone()
print(f"\nVerification:")
print(f"  Collection: {result[0]}")
print(f"  Documents: {result[1]}")
print(f"  Chunks: {result[2]}")
print(f"  Embedding: {result[3]}")

cur.execute("SELECT doc_name, chunk_count FROM kb_documents WHERE kb_id = ?", (kb_id,))
for row in cur.fetchall():
    print(f"  Document: {row[0]} ({row[1]} chunks)")

conn.close()
