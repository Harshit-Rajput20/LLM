"""Hybrid RAG ingestion pipeline with detailed logging."""

import logging
import uuid
from typing import List
from config import settings
from models.models import IngestionRequest
from utils.embeddings import get_embedding_generator
from storage.document_store import get_document_store
from storage.metadata_store import get_metadata_store
from storage.vector_store import get_vector_store
from storage.keyword_index import get_keyword_index
from document_parser import DocumentParser
from chunker import chunk_text

logger = logging.getLogger(__name__)

async def ingest_pipeline(request: IngestionRequest) -> dict:
    """Full ingestion: parse → chunk → store all layers."""
    document_id = str(uuid.uuid4())
    
    logger.info(f"Starting ingest for document_id={document_id}, filename='{request.filename or 'unknown'}', content_len={len(request.content)}")
    
    # 2. Chunk
    logger.info(f"Chunking content for {document_id}")
    chunks = chunk_text(
        request.content,
        document_id,
        request.filename or "doc",
        metadata=request.metadata or {}
    )
    
    if not chunks:
        logger.error(f"No chunks generated for {document_id}")
        return {"status": "failed", "num_chunks": 0}
    
    logger.info(f"Generated {len(chunks)} chunks for {document_id}")
    
    embedding_gen = get_embedding_generator()
    
    for i, chunk in enumerate(chunks):
        chunk_id = chunk["chunk_id"]
        logger.info(f"Processing chunk {i+1}/{len(chunks)}: {chunk_id}")
        
        try:
            # 3. Embed
            logger.info(f"Embedding chunk {chunk_id}")
            vector = embedding_gen.encode_single(chunk["text"]).tolist()
            logger.info(f"Generated vector dim={len(vector)} for {chunk_id}")
            
            # 4. Store raw text (MinIO)
            logger.info(f"Storing raw text for {chunk_id} to document_store")
            doc_store = await get_document_store()
            await doc_store.store_chunk(chunk_id, chunk["text"])
            logger.info(f"Stored raw text for {chunk_id}")
            
            # 5. Metadata (Postgres) - now enabled
            logger.info(f"Storing metadata for {chunk_id}")
            metadata_store = get_metadata_store()
            chunk_metadata = {
                "chunk_id": chunk_id,
                "document_id": document_id,
                "filename": chunk.get("filename", request.filename or "doc"),
                "page_num": chunk.get("page_num"),
                "chunk_metadata": chunk["metadata"]
            }
            metadata_store.store_chunk_metadata(chunk_metadata)
            
            # 6. Vector (Qdrant)
            logger.info(f"Upserting vector for {chunk_id} to vector_store")
            v_store = await get_vector_store()
            await v_store.upsert_chunk(chunk_id, vector, chunk)
            logger.info(f"Upserted vector for {chunk_id}")
            
            # 7. Keyword (ES)
            logger.info(f"Indexing keywords for {chunk_id} to keyword_index")
            kw_index = await get_keyword_index()
            await kw_index.index_chunk(chunk_id, chunk["text"], chunk["metadata"])
            logger.info(f"Indexed keywords for {chunk_id}")
            
        except Exception as e:
            logger.error(f"Error processing chunk {chunk_id}: {str(e)}")
            raise
    
    logger.info(f"Successfully ingested {document_id}: {len(chunks)} chunks")
    return {
        "document_id": document_id,
        "num_chunks": len(chunks),
        "status": "success"
    }

