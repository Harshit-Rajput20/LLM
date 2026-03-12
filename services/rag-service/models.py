"""Data models for RAG service."""

from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime


class DocumentChunk(BaseModel):
    """Single document chunk with metadata."""
    chunk_id: str
    document_id: str
    text: str
    metadata: Dict[str, Any]
    embedding: List[float]


class IngestionRequest(BaseModel):
    """Request for document ingestion."""
    content: str
    filename: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = {}


class RetrievalRequest(BaseModel):
    """Request for document retrieval."""
    query: str
    top_k: int = 5


class RetrievalResult(BaseModel):
    """Retrieval response."""
    documents: List[str]
    scores: List[float]


class IngestionResponse(BaseModel):
    """Ingestion response."""
    document_id: str
    num_chunks: int
    status: str


class ChunkMetadata(BaseModel):
    """Metadata for document chunks."""
    document_id: str
    filename: str
    page_num: Optional[int] = None
    source: str

