# Document Ingestion Module - SQLAlchemy Standardization Refactor

## Progress
**Current Status:** 0/5 steps completed

## Detailed Plan & Steps

**1. [x] Add async SQLAlchemy DB dependency to API endpoints**
   - File: services/rag-service/api/main.py
   - Status: Complete
   - File: services/rag-service/api/main.py
   - Add get_async_db() generator with AsyncSessionLocal
   - Update ingest_text and ingest_file to depend on db: AsyncSession
   - Pass db to ingest_pipeline(request, db)

**2. [x] Refactor metadata_store.py to async SQLAlchemy 2.0**
   - File: services/rag-service/storage/metadata_store.py
   - Status: Complete
   - File: services/rag-service/storage/metadata_store.py
   - Replace create_engine with create_async_engine (adjust URL to asyncpg)
   - Use async_sessionmaker, AsyncSession
   - Make store_chunk_metadata, get_chunk_metadata async, take db param
   - Remove psycopg2 docstring
   - Update get_metadata_store() to factory for db dep

**3. [x] Enable metadata storage in ingestion pipeline**
   - File: services/rag-service/ingestion/pipeline.py
   - Status: Complete (fixes applied for import/ driver)
   - File: services/rag-service/ingestion/pipeline.py
   - Update ingest_pipeline to accept db: AsyncSession
   - Remove skip logic & comment
   - After store_chunk: await metadata_store.store_chunk_metadata(extracted_metadata, db)
   - Extract metadata from chunk dict (chunk_id, document_id, filename, page_num?, chunk_metadata)

**4. [ ] Update models consistency (optional)**
   - File: services/rag-service/models/models.py
   - Ensure Pydantic aligns with SQLAlchemy model

**5. [ ] Final verification**
   - No compilation errors
   - All psycopg references removed
   - Async flow consistent
   - Metadata storage enabled

## Improvements Expected
- Full async Postgres metadata CRUD
- Proper FastAPI DB session management
- Single source of truth for sessions (no singletons)
- Transaction safety
- No psycopg instability

**Completed Steps Will Be Marked [x] and Updated Here**
