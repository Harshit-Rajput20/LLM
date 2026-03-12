"""Production RAG Service with semantic retrieval.

Architecture:
Document → Parser → Chunker → Embeddings → FAISS Vector Store → Semantic Search."""

from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.responses import JSONResponse
import uvicorn
import os
import io
from pathlib import Path
from typing import List
import uuid
import numpy as np

# Local imports (absolute imports for Docker)
import models
from document_parser import DocumentParser
from chunker import chunk_text
from embedding_generator import get_embedding_generator
from vector_store import get_vector_store
from retriever import retrieve_documents

IngestionRequest = models.IngestionRequest
RetrievalRequest = models.RetrievalRequest
IngestionResponse = models.IngestionResponse
RetrievalResult = models.RetrievalResult


app = FastAPI(title="Production RAG Service", version="1.0.0")

# Initialize global singletons at startup
vector_store = get_vector_store()
embedding_generator = get_embedding_generator()

DATA_DIR = Path("data/documents")
DATA_DIR.mkdir(exist_ok=True)

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    stats = vector_store.get_stats()
    return {
        "status": "healthy",
        "vector_store_stats": stats
    }

@app.get("/stats")
async def get_stats():
    """Get system statistics."""
    return {
        "vector_store": vector_store.get_stats(),
        "embedding_model": "all-MiniLM-L6-v2",
        "supported_formats": ["pdf", "txt", "md", "docx"]
    }

@app.post("/ingest/text", response_model=IngestionResponse)
async def ingest_text(request: IngestionRequest):
    """Ingest plain text document."""
    try:
        # Generate unique document ID
        document_id = str(uuid.uuid4())
        filename = request.filename or "text_document.txt"
        
        # Chunk text
        chunks = chunk_text(
            request.content, 
            document_id, 
            filename,
            metadata=request.metadata or {}
        )
        
        if not chunks:
            raise HTTPException(status_code=400, detail="No valid chunks created from text")
        
        # Generate embeddings
        chunk_texts = [chunk["text"] for chunk in chunks]
        embeddings = embedding_generator.encode_texts(chunk_texts)
        
        # Store in vector database
        vector_store.add_documents(embeddings, chunks)
        
        print(f"Ingested document {document_id}: {len(chunks)} chunks")
        
        return IngestionResponse(
            document_id=document_id,
            num_chunks=len(chunks),
            status="success"
        )
    
    except Exception as e:
        print(f"Ingestion error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ingest/file")
async def ingest_file(
    file: UploadFile = File(...),
    filename: str = Form(None)
):
    """Ingest document file (PDF, TXT, MD, DOCX)."""
    try:
        if not file.content_type:
            raise HTTPException(status_code=400, detail="Invalid file type")
        
        # Read file content
        content = await file.read()
        
        # Determine filename
        upload_filename = filename or file.filename
        if not upload_filename:
            upload_filename = "uploaded_document"
        
        # Parse document - pass bytes directly (parsers handle conversion)
        text_content = DocumentParser.parse(upload_filename, content)
        
        if not text_content.strip():
            raise HTTPException(status_code=400, detail="No text extracted from document")
        
        # Create ingestion request
        request = IngestionRequest(
            content=text_content,
            filename=upload_filename
        )
        
        # Process ingestion
        return await ingest_text(request)
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"File ingestion error: {e}")
        raise HTTPException(status_code=500, detail=f"File processing failed: {str(e)}")

@app.post("/retrieve", response_model=RetrievalResult)
async def retrieve(request: RetrievalRequest):
    """Semantic retrieval using FAISS vector store."""
    try:
        results = retrieve_documents(request.query, request.top_k)
        
        return RetrievalResult(
            documents=results["documents"],
            scores=results["scores"]
        )
    
    except Exception as e:
        print(f"Retrieval error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/clear")
async def clear_store():
    """Clear all documents from vector store (admin only)."""
    try:
        vector_store._index.reset()
        vector_store._metadata.clear()
        vector_store._save_index()
        return {"status": "cleared", "total_vectors": 0}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)

