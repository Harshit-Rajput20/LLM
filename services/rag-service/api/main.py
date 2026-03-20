
"""Refactored FastAPI app using hybrid pipelines."""


from fastapi import FastAPI, UploadFile, File, HTTPException, Form, Depends
from fastapi.responses import JSONResponse
import uvicorn
from pathlib import Path
import uuid

from config import settings
from models.models import IngestionRequest, IngestionResponse, RetrievalRequest, RetrievalResult, HybridRetrievalRequest
from ingestion.pipeline import ingest_pipeline
from retrieval.pipeline import retrieve_pipeline
from storage.vector_store import get_vector_store  # for stats
from document_parser import DocumentParser


import logging
logger = logging.getLogger(__name__)

app = FastAPI(title="Hybrid RAG Service v2", version="2.0.0")

# Async SQLAlchemy setup for metadata store (session only, engine lazy in store if needed)
# Global engine removed to avoid import-time dbapi issues

DATA_DIR = Path("data") / "documents"
DATA_DIR.mkdir(parents=True, exist_ok=True)

def get_db():
    db = None
    try:
        yield db
    finally:
        pass

@app.get("/health")
async def health_check():
    v_store = await get_vector_store()
    stats = True  # simplistic - collection exists via vector_store init
    return {"status": "healthy", "hybrid_ready": stats}

@app.get("/stats")
async def get_stats():
    return {
        "embedding_model": settings.embedding_model,
        "reranker": settings.reranker_model,
        "storage_layers": ["minio", "postgres", "qdrant", "elasticsearch", "redis"]
    }

@app.post("/ingest/text", response_model=IngestionResponse)
async def ingest_text(request: IngestionRequest):
    logger.info(f"Ingest /text: filename='{request.filename or 'unknown'}', content_len={len(request.content)}")
    try:
        result = await ingest_pipeline(request)
        logger.info(f"Ingest /text success: {result}")
        return IngestionResponse(**result)
    except Exception as e:
        logger.error(f"Ingest /text failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ingest/file")
async def ingest_file(
    file: UploadFile = File(...),
    filename: str = Form(None)
):
    upload_filename = filename or file.filename or "uploaded"
    logger.info(f"Ingest /file: filename='{upload_filename}', file_size={file.size}")
    try:
        content = await file.read()
        text = DocumentParser.parse(upload_filename, content)
        request = IngestionRequest(content=text, filename=upload_filename)
        result = await ingest_text(request)
        logger.info(f"Ingest /file success: {result}")
        return result
    except Exception as e:
        logger.error(f"Ingest /file failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/retrieve", response_model=RetrievalResult)
async def retrieve(request: HybridRetrievalRequest):
    try:
        result = await retrieve_pipeline(request.query, request.top_k, request.hybrid)
        return RetrievalResult(documents=result["documents"], scores=result["scores"])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/clear")
async def clear_store():
    # TODO impl multi-store clear
    return {"status": "todo"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)

