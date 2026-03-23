"""Configuration loader for RAG service v2."""

import os
from typing import Optional
from pydantic_settings import BaseSettings


class RAGSettings(BaseSettings):
    """RAG hybrid service settings."""
    
    # Infra connections
    postgres_url: str = os.getenv("POSTGRES_URL", "postgresql://rag_user:rag_pass@postgres:5432/rag_metadata")
    minio_endpoint: str = os.getenv("MINIO_ENDPOINT", "minio:9000")
    minio_access_key: str = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
    minio_secret_key: str = os.getenv("MINIO_SECRET_KEY", "minioadmin")
    qdrant_url: str = os.getenv("QDRANT_URL", "http://qdrant:6333")
    elasticsearch_url: str = os.getenv("ELASTICSEARCH_URL", "http://elasticsearch:9200")
    redis_url: str = os.getenv("REDIS_URL", "redis://redis:6379")
    
    # Models
    embedding_model: str = os.getenv("EMBEDDING_MODEL", "./models_local/embeddings/bge-base-en-v1.5")
    reranker_model: str = os.getenv("RERANKER_MODEL", "./models_local/reranker/ms-marco-MiniLM-L-12-v2-full")
    embedding_dim: int = 768  # bge-base
    
    # Retrieval params
    vector_top_k: int = int(os.getenv("VECTOR_TOP_K", "20"))
    keyword_top_k: int = int(os.getenv("KEYWORD_TOP_K", "20"))
    final_top_k: int = int(os.getenv("FINAL_TOP_K", "5"))
    cache_ttl_query: int = int(os.getenv("CACHE_TTL_QUERY", "3600"))
    
    class Config:
        env_file = ".env"


settings = RAGSettings()

