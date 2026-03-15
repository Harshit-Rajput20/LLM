"""Hybrid RAG ingestion pipeline."""

import uuid
from typing import List
from config import settings
from models.models import IngestionRequest
from utils.embeddings import get_embedding_generator
from storage.document_store import get_document_store
from storage.metadata_store import get_metadata_store
from storage.vector_store import get_vector_store
from storage.keyword_index import get_keyword_index
# Legacy imports for parser/chunker
from document_parser import DocumentParser
from chunker import chunk_text


async def ingest_pipeline(request: IngestionRequest) -> dict:
    """Full ingestion: parse → chunk → store all layers."""
    document_id = str(uuid.uuid4())
    
    # 1. Parse (file handled in endpoint)
    # text = request.content (assume plain text)
    
    # 2. Chunk
    chunks = chunk_text(
        request.content,
        document_id,
        request.filename or "doc",
        metadata=request.metadata or {}
    )
    
    if not chunks:
        return {"status": "failed", "num_chunks": 0}
    
    embedding_gen = get_embedding_generator()
    
    for chunk in chunks:
        chunk_id = chunk["chunk_id"]
        
        # 3. Embed
        vector = embedding_gen.encode_single(chunk["text"]).tolist()
        
        # 4. Store raw text (MinIO)
        doc_store = await get_document_store()
        await doc_store.store_chunk(chunk_id, chunk["text"])
        
        # 5. Metadata (PG)
        meta_store = await get_metadata_store()
        async with meta_store.session_maker() as session:
            md = {
                "chunk_id": chunk_id,
                "document_id": document_id,
                "filename": chunk["filename"],
                "metadata": chunk["metadata"]
            }
            await meta_store.store_chunk_metadata(session, md)
            await session.commit()
        
        # 6. Vector (Qdrant)
        v_store = await get_vector_store()
        await v_store.upsert_chunk(chunk_id, vector, chunk)
        
        # 7. Keyword (ES)
        kw_index = await get_keyword_index()
        await kw_index.index_chunk(chunk_id, chunk["text"], chunk["metadata"])
    
    print(f"Ingested {document_id}: {len(chunks)} chunks")
    return {
        "document_id": document_id,
        "num_chunks": len(chunks),
        "status": "success"
    }

