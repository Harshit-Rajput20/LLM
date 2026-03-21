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

## Full Pipeline Test with Postman

**Step 1: Health Check**
```
GET http://localhost:8001/health
```

**Step 2: Ingest Test Document**
```
POST http://localhost:8001/ingest/text
Content-Type: application/json

{
  "content": "RAG is Retrieval Augmented Generation. It combines information retrieval with generative AI to provide contextually relevant responses. Key components: embedding models, vector databases, reranking.",
  "filename": "rag_guide.txt",
  "metadata": {"type": "guide", "version": "v2"}
}
```

**Step 3: Verify Ingestion**
Expected response:
```
{
  "document_id": "uuid",
  "num_chunks": 3,
  "status": "success"
}
```

**Step 4: Retrieve**
```
POST http://localhost:8001/retrieve
Content-Type: application/json

{
  "query": "What is RAG?",
  "top_k": 5,
  "hybrid": true
}
```

**Step 5: Expected Retrieval Response**
```
{
  "documents": [
    "RAG is Retrieval Augmented Generation...",
    "Key components: embedding models...",
    "..."
  ],
  "scores": [0.92, 0.85, 0.78]
}
```

**Full Postman Collection JSON (Import):**
```json
{
  "info": {"name": "RAG Service Test"},
  "item": [
    {"name": "Health", "request": {"method": "GET", "url": "http://localhost:8001/health"}},
    {
      "name": "Ingest",
      "request": {
        "method": "POST",
        "url": "http://localhost:8001/ingest/text",
        "header": [{"key": "Content-Type", "value": "application/json"}],
        "body": {"mode": "raw", "raw": "{\"content\": \"RAG is Retrieval Augmented Generation...\", \"filename\": \"rag.txt\"}"}
      }
    },
    {
      "name": "Retrieve", 
      "request": {
        "method": "POST",
        "url": "http://localhost:8001/retrieve",
        "header": [{"key": "Content-Type", "value": "application/json"}],
        "body": {"mode": "raw", "raw": "{\"query\": \"What is RAG?\", \"top_k\": 5}"}
      }
    }
  ]
}
```

**Troubleshooting:**
- "chunk_None": No data ingested or score_threshold too high
- 500 errors: Check docker logs rag-service
- Empty results: Use exact phrases from ingested text

## End-to-End RAG + LLM Query (Full Pipeline)

**Complete Flow:** Ingest → Retrieve → LLM Context → Generate Answer

**Step 1: Start Full Stack**
```bash
docker compose up api-gateway llm-client prompt-builder response-processor rag-service
```

**Step 2: Ingest via RAG (port 8001)**
(As above)

**Step 3: Query via API Gateway (port 8000)**
```
POST http://localhost:8000/query
Content-Type: application/json

{
  "query": "What is RAG and how does it work?",
  "top_k": 5
}
```

**Expected Full Response:**
```json
{
  "answer": "RAG is Retrieval Augmented Generation. It works by...",
  "sources": [
    {"chunk_id": "uuid", "score": 0.92, "text": "RAG is Retrieval..."}
  ],
  "model_used": "gpt-4o-mini"
}
```

**Postman Full Pipeline Collection Addition:**
```json
{
  "name": "Full RAG+LLM Query",
  "request": {
    "method": "POST",
    "url": "http://localhost:8000/query",
    "header": [{"key": "Content-Type", "value": "application/json"}],
    "body": {"mode": "raw", "raw": "{\"query\": \"Explain RAG\", \"top_k\": 5}"}
  }
}
```

**Microservice Flow:**
```
User Query → api-gateway (8000) → 
prompt-builder → llm-client → rag-service (8001 retrieve) → 
response-processor → Final Answer
```

**Verify Full Stack:**
```
docker compose logs api-gateway | grep "query"
docker compose ps  # all services healthy
```

## /chat Endpoint (API Gateway Port 8000)
**http://localhost:8000/chat** - **Full RAG+LLM Chat Interface**

**What it does:**
1. Takes user message
2. **RAG retrieve** (your rag-service)
3. Builds prompt with retrieved context
4. **LLM generate** response
5. Processes + returns final answer + sources

**Postman Test:**
```
POST http://localhost:8000/chat
Content-Type: application/json

{
  "message": "What is RAG?"
}
```

**Expected Response:**
```json
{
  "response": "RAG (Retrieval Augmented Generation) is a technique that..."
}
```

**Full Microservices Flow:**
```
chat → api-gateway → prompt-builder → llm-client → rag-service/retrieve 
→ response-processor → Answer
```

**Test Complete Stack:**
1. `docker compose up` (all services)
2. Ingest via rag-service:8001
3. Chat via api-gateway:8000/chat → **Uses RAG context!**

**Swagger UI:** http://localhost:8000/docs




