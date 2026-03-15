"""Expanded Pydantic models for hybrid RAG."""

from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime


# Existing v1 models
class DocumentChunk(BaseModel):
    chunk_id: str
    document_id: str
    text: str
    metadata: Dict[str, Any]
    embedding: Optional[List[float]] = None


class IngestionRequest(BaseModel):
    content: str
    filename: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = {}


class RetrievalRequest(BaseModel):
    query: str
    top_k: int = 5


class IngestionResponse(BaseModel):
    document_id: str
    num_chunks: int
    status: str


class RetrievalResult(BaseModel):
    documents: List[str]
    scores: List[float]


class ChunkMetadata(BaseModel):
    document_id: str
    filename: str
    page_num: Optional[int] = None
    source: str


# New v2 hybrid models
class HybridRetrievalRequest(RetrievalRequest):
    hybrid: bool = True
    alpha: float = 0.7  # vector:keyword fusion weight


class HybridResult(BaseModel):
    documents: List[str]
    scores: List[float]
    source_types: List[str]  # ['vector', 'keyword', 'reranked']

