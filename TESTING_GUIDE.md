# Hybrid RAG Microservice Testing Guide (Port 8001)

## Prerequisites
```bash
docker compose up --build rag-service
```
Wait for "Uvicorn running on http://0.0.0.0:8001"

## Endpoints

### 1. Health Check
```
curl http://localhost:8001/health
```
Expected: `{"status": "healthy", "hybrid_ready": true}`

**Postman:** GET http://localhost:8001/health

### 2. Stats
```
curl http://localhost:8001/stats
```
Expected: models/storage info.

**Postman:** GET http://localhost:8001/stats

### 3. Ingest Text
```
curl -X POST http://localhost:8001/ingest/text \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Test document about artificial intelligence. LLM is large language model. RAG is retrieval augmented generation.",
    "filename": "test.txt"
  }'
```

**Postman:** POST http://localhost:8001/ingest/text
Body JSON:
```json
{
  "content": "Your test text here...",
  "filename": "test.txt"
}
```
Expected: `{"chunk_ids": [...], "status": "ingested"}`

### 4. Ingest File
Upload file (test.txt already exists, create your own).

**Postman:** POST http://localhost:8001/ingest/file
- Body form-data: `file` (select txt/pdf)
- `filename` (optional)

Expected: ingestion response.

### 5. Retrieve (Hybrid RAG)
```
curl -X POST http://localhost:8001/retrieve \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is RAG?",
    "top_k": 3,
    "hybrid": true
  }'
```

**Postman:** POST http://localhost:8001/retrieve
Body JSON:
```json
{
  "query": "test query",
  "top_k": 5,
  "hybrid": true
}
```
Expected: `{"documents": [...], "scores": [...]}`

### 6. Clear Store
```
curl -X DELETE http://localhost:8001/clear
```

## Test Sequence
1. Health check OK
2. Ingest text (1-2 docs)
3. Retrieve with query matching text
4. Verify hybrid retrieval ranks relevant chunks
5. Clear and re-ingest file if needed.

## Sample Test Document
Create `services/rag-service/test_doc.txt`:
```
RAG (Retrieval Augmented Generation) combines vector search with keyword matching for better LLM context.
Hybrid stores: Minio (docs), Postgres (metadata), Qdrant (vectors), Elasticsearch (keywords), Redis (cache).
```

## Verification
- Check Docker logs: `docker compose logs rag-service`
- Browse Qdrant: http://localhost:6333/dashboard
- Postgres: `docker compose exec postgres psql -U rag_user rag_metadata -c "SELECT * FROM chunk_metadata LIMIT 5;"`

