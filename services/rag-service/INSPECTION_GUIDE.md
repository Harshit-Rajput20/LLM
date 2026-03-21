# RAG Ingestion Data Inspection Guide
## Overview
This document explains **where all ingested data is stored**, **how the flow works**, and **how to inspect/access each piece**. All data from ingestion is split into 4 parallel storage layers for hybrid RAG.

## Full Ingestion Flow
```
POST /ingest/text or /ingest/file
    ↓ (IngestionRequest: content:str, filename:str?, metadata:dict?)
1. chunker.py → List[ChunkDict]
   - chunk_id: UUID (PK everywhere)
   - document_id: UUID (groups chunks)
   - chunk_index: int
   - text: str (~500 tokens)
   - filename: str
   - metadata: dict
   - token_count: int
2. For EACH chunk → embed (BGE-base, 768 dim)
3. PARALLEL STORE 4 LAYERS:
   ├─ Raw text → MinIO
   ├─ Metadata → Postgres
   ├─ Vector+payload → Qdrant
   └─ Keywords → Elasticsearch
```

**Chunk Example**:
```python
{
  'chunk_id': '550e8400-e29b-41d4-a716-446655440001',
  'document_id': '123e4567-e89b-12d3-a456-426614174000',
  'chunk_index': 0,
  'text': 'This is chunk text...',
  'filename': 'doc.pdf',
  'metadata': {'page': 1},
  'token_count': 498
}
```

## Storage Details & Inspection Commands
*(docker-compose services: postgres, minio, qdrant, elasticsearch)*

### 1. Raw Text Chunks (MinIO)
- **Bucket**: `rag-documents`
- **Key**: `{chunk_id}`
- **Inspect**:
  ```
  docker exec -it llm-minio-1 mc ls rag-documents/  # list chunks
  docker exec -it llm-minio-1 mc cat rag-documents/550e8400-e29b-41d4-a716-446655440001  # get text
  ```
- **API**: `DocumentStore.get_chunk(chunk_id)`

### 2. Metadata (Postgres)
- **Table**: `public.chunk_metadata`
- **Schema**:
  | Col | Type | Desc |
  |-----|------|------|
  | chunk_id | UUID | PK |
  | document_id | UUID | Group |
  | filename | str | Source |
  | page_num | int? | Page |
  | chunk_metadata | JSONB | Extra |
- **Inspect**:
  ```
  docker exec -it llm-postgres-1 psql -U rag_user -d rag_metadata
  \dt  # tables
  SELECT COUNT(*) FROM chunk_metadata;  # total chunks
  SELECT * FROM chunk_metadata WHERE document_id='123e4567-e89b-12d3-a456-426614174000';  # per doc
  SELECT chunk_id, filename, chunk_metadata FROM chunk_metadata LIMIT 5;
  ```
- **API**: `MetadataStore.get_chunk_metadata(chunk_id)`

### 3. Vectors & Full Payload (Qdrant) - **QUADRANT**
- **Collection**: `rag_chunks`
- **Point ID**: `{chunk_id}`
- **Fields**: vector (768f), payload (full ChunkDict incl text/metadata)
- **Inspect**:
  ```
  # Dashboard: http://localhost:6333/dashboard (qdrant:6333 internal)
  # CLI:
  docker exec -it llm-qdrant-1 curl 'http://localhost:6333/collections/rag_chunks'
  docker exec -it llm-qdrant-1 curl 'http://localhost:6333/collections/rag_chunks/points/search' \
    -d '{"query": [0.1,0.2,...], "limit": 3, "with_payload": true}'
  docker exec -it llm-qdrant-1 curl 'http://localhost:6333/collections/rag_chunks/scroll' \
    -d '{"limit": 10, "with_payload": true}'
  ```
- **API**: `QdrantVectorStore.search(query_vector)` or `client.scroll()`

### 4. Keyword Index (Elasticsearch)
- **Index**: `rag_chunks`
- **Doc ID**: `{chunk_id}`
- **Fields**: `text` (analyzed), `metadata`
- **Inspect**:
  ```
  docker exec -it llm-elasticsearch-1 curl 'localhost:9200/rag_chunks/_search?pretty' \
    -H 'Content-Type: application/json' -d'{\"query\":{\"match_all\":{}},\"size\":5}'
  docker exec -it llm-elasticsearch-1 curl 'localhost:9200/rag_chunks/_count'
  docker exec -it llm-elasticsearch-1 curl 'localhost:9200/rag_chunks/_search?pretty' \
    -d'{\"query\":{\"match\":{\"text\":\"your keyword\"}}}'
  ```
- **API**: `KeywordIndex.search(query_str)`

## Quick Stats Across Stores
```
# Total chunks (should match)
docker exec llm-postgres-1 psql rag_metadata -U rag_user -t -c "SELECT COUNT(*) FROM chunk_metadata;"
docker exec llm-minio-1 mc ls --recursive --json rag-documents/ | jq 'length'

# Per document
POSTGRES: SELECT COUNT(*) FROM chunk_metadata WHERE document_id='...';
QDRANT: curl '.../scroll?filter={"must":[{"key":"document_id","match":{"value":"..."}}]}'
```

## Debug Tips
1. **Logs**: `docker logs llm-rag-service-1 | grep 'Processing chunk'`
2. **Test ingest**: `curl -X POST http://localhost:8001/ingest/text -H "Content-Type: application/json" -d '{"content":"test text"}'`
3. **Retrieval**: Inspects via `/retrieve` uses all layers (hybrid=true).
4. **Config**: Check `services/rag-service/config.py` for URLs (qdrant:6333, etc.)
5. **Cache**: Redis `rag-cache` keys for queries.

**Updated**: Based on v2 hybrid RAG (all layers active).
