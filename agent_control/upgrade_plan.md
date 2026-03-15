# RAG Microservice Hybrid Retrieval Upgrade Plan

## Executive Summary
This plan upgrades the production-ready FAISS-only semantic RAG (Phase 3 v1) to full hybrid retrieval architecture per architecture.md. Maintains API compatibility (/ingest/text, /ingest/file, /retrieve). Adds new infra, refactors into rag-service/api/ingestion/retrieval/storage/models/, implements pipelines, caching, new embeddings/reranker.

**Timeline:** Sequential phases with validation. Track via upgrade_state.json (mark \"in_progress\" → \"done\").

**Validation:** docker-compose up → test ingestion → hybrid retrieval → chat end-to-end.

## Information Gathered
- **Current State (RAG v1):** Complete semantic pipeline:
  | Component | File | Impl |
  |-----------|------|------|
  | Models | models.py | Pydantic (DocumentChunk, RetrievalRequest/Response) |
  | Parser | document_parser.py | PDF/TXT/MD/DOCX (pypdf, docx, bs4) |
  | Chunker | chunker.py | Semantic 500-token chunks (tiktoken) |
  | Embeddings | embedding_generator.py | all-MiniLM-L6-v2 (sentence-transformers), FAISS store |
  | Vector Store/Retriever | vector_store.py, retriever.py | FAISS disk-persist (data/vector_store/), cosine sim |
  | API | main.py | FastAPI /ingest/text, /ingest/file (upload), /retrieve |
- **Deps:** requirements.txt has sentence-transformers, faiss-cpu, etc. No hybrid deps.
- **Docker:** docker-compose.yml has rag-service:8001. No new services.
- **API Gateway:** Calls rag-service/retrieve → prompt-builder.
- **Progress:** upgrade_state.json all \"pending\", phase \"planning\".
- **Roadmap/Progress:** Phase 3 v1 ✅, hybrid \"IN PROGRESS\".

## Detailed Implementation Plan

### Phase 1: State Update & Architecture Validation (Current)
- Update upgrade_state.json: Set phase \"infra_setup\", architecture_validation → \"done\".
- Files: agent_control/upgrade_state.json, progress_state.md.

### Phase 2: Infrastructure Setup (docker-compose.yml)
**docker-compose.yml**
- Add services (all v3+, networks default, volumes persist data):
  | Service | Image/Ports/Volumes/Env | Depends |
  |---------|-------------------------|---------|
  | postgres | postgres:16 | data/pgdata:/var/lib/postgresql/data, env POSTGRES_DB=rag_metadata, USER/PASS |
  | minio | minio/minio:latest:9001 | data/minio:/data, env ROOT_USER/PASS, cmd server /data --console-address \":9001\" |
  | qdrant | qdrant/qdrant:latest:6333 | data/qdrant:/qdrant/storage |
  | elasticsearch | docker.elastic.co/elasticsearch/elasticsearch:8.15.0:9200 | data/esdata:/usr/share/elasticsearch/data, env discovery.type=single-node, xpack.security.enabled=false |
  | redis | redis:7-alpine:6379 | data/redis:/data |
- Update rag-service: depends_on all new services, env vars for connections (MINIO_*, POSTGRES_*, etc.).
- Networks: default.

**Follow-up:** docker-compose up -d new_svcs → verify health (curl ports).

### Phase 3: Dependencies Update
**services/rag-service/requirements.txt**
- Add/upgrade: qdrant-client, elasticsearch[async], psycopg2-binary, minio, redis[async], torch (bge/reranker), transformers.
- Remove: faiss-cpu (legacy support optional).
- Pin versions for prod.

### Phase 4: Code Refactor - New Structure
```
rag-service/
├── api/ (main.py → api_endpoints.py)
├── ingestion/ (new pipeline.py orchestrator)
├── retrieval/ (new pipeline.py)
├── storage/ (new layers)
│   ├── __init__.py
│   ├── document_store.py (MinIO)
│   ├── metadata_store.py (Postgres)
│   ├── vector_store.py (Qdrant, migrate FAISS?)
│   └── keyword_index.py (Elasticsearch)
├── models/ (expand pydantic)
├── cache/ (new redis_client.py)
├── utils/ (embeddings.py → new bge-base-en, reranker.py bge-reranker-large)
└── config.py (new env loader)
```
- Migrate existing: chunker.py → ingestion/, parsers → ingestion/, old vector_store.py → legacy/.

### Phase 5: Storage Layers
- **document_store.py:** MinIO client, upload/retrieve chunks by doc_id.
- **metadata_store.py:** SQLAlchemy asyncpg, tables: documents(id, metadata JSONB), chunks(id, doc_id, metadata).
- **vector_store.py:** qdrant-client async, collections with payload (metadata), upsert/search.
- **keyword_index.py:** elasticsearch async, index chunks with text/metadata, BM25 search.

### Phase 6: Ingestion Pipeline (ingestion/pipeline.py)
1. Parser/Cleaner (reuse).
2. Semantic Chunker (reuse).
3. Metadata Extractor (new: source, timestamp, etc.).
4. **NEW:** Parallel store: doc→MinIO, metadata→Postgres, embeddings→Qdrant (bge-base-en), keywords→ES.
- Tx atomicity: async pipelines.
- /ingest endpoints trigger pipeline.

### Phase 7: Retrieval Pipeline (retrieval/pipeline.py)
1. Query Processor (clean/rewrite).
2. Query Expansion (hypothetical doc → embed).
3. **Hybrid:** Vector (Qdrant top-k) + Keyword (ES top-k) → reciprocal rank fusion (RRFF) merge.
4. Reranker: bge-reranker-large score top-50 → top-5.
5. Context Builder: format chunks w/ metadata.
- Cache: Redis query_hash → results, embedding_hash → vectors.
- /retrieve: hybrid param toggle.

### Phase 8: Caching Layer (cache/redis_client.py)
- redis.asyncio: query_cache (ttl 1h), embedding_cache (ttl 24h).
- Keys: sha256(query), sha256(text).

### Phase 9: API & Integration (api/api_endpoints.py)
- main.py → import api_endpoints, config.
- Env: LLM_EMBEDDING_MODEL=bge-base-en, RERANKER_MODEL=bge-reranker-large.
- Legacy /retrieve?hybrid=false → FAISS fallback optional.

### Phase 10: Validation & Cleanup
- docker-compose build && up.
- Test: ingest file → retrieve hybrid → latency/token check.
- Migrate any existing FAISS data?
- Update progress_state.md: \"Hybrid Retrieval Architecture Complete\".
- Final: all tasks \"done\" in upgrade_state.json.

## Risks & Mitigations
- **Downtime:** Parallel infra, toggle hybrid.
- **Data Migration:** New ingest re-populates.
- **Perf:** Torch GPU? CPU fallback, monitor ES heap.
- **Compat:** API unchanged.

## Dependent Files to Edit
1. docker-compose.yml (Phase 2)
2. services/rag-service/requirements.txt (3)
3. services/rag-service/* (refactor all Phases 4-9)
4. agent_control/upgrade_state.json (update per task)
5. agent_control/progress_state.md (final)
6. services/api-gateway/main.py? (if RAG changes affect)

## Follow-up Steps After Edits
1. docker-compose build rag-service new_svcs.
2. docker-compose up -d → curl health checks (Postgres/Qdrant/ES/MinIO/Redis).
3. python -m pytest or manual: POST /ingest/file → /retrieve?hybrid=true.
4. docker-compose logs rag-service → no errors.
5. End-to-end: API gateway /chat → uses hybrid context.
6. Perf: compare v1 vs v2 retrieval latency/MRR.

Approve plan before code changes?

