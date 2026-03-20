# Qdrant Chunk ID Fix Plan

**Information Gathered:**
- chunker.py creates invalid `chunk_id = f"{document_id}_{chunk_num}"`
- Passed to pipeline.py chunk["chunk_id"] → vector_store.upsert_chunk(id)
- Qdrant rejects non-UUID/non-integer ID

**Plan:**
- chunker.py: Change chunk_id to `str(uuid.uuid4())`, add "chunk_index": chunk_num to payload
- No other file changes (payload carries document_id/chunk_index)

**Dependent Files:** None

**Followup:** Test /ingest/file

Approve to proceed?
