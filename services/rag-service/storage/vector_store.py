"""Qdrant vector store layer."""

from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams, Filter, FieldCondition, MatchValue
from typing import List, Dict, Any
from config import settings
import uuid


class QdrantVectorStore:
    """Async Qdrant vector store w/ payload."""

    COLLECTION_NAME = "rag_chunks"

    def __init__(self):
        self.client = QdrantClient(settings.qdrant_url)
        self._create_collection()

    def _create_collection(self):
        """Create collection if not exists."""
        collections = self.client.get_collections()
        if self.COLLECTION_NAME not in [c.name for c in collections.collections]:
            self.client.create_collection(
                collection_name=self.COLLECTION_NAME,
                vectors_config=VectorParams(size=settings.embedding_dim, distance=Distance.COSINE)
            )

    async def upsert_chunk(self, id: str, vector: List[float], payload: Dict[str, Any]):
        """Upsert point w/ vector + payload."""
        self.client.upsert(
            collection_name=self.COLLECTION_NAME,
            points=[{
                "id": id,
                "vector": vector,
                "payload": payload
            }]
        )

    async def search(self, query_vector: List[float], top_k: int) -> List[Dict]:
        """Cosine similarity search."""

        results = self.client.search(
            collection_name=self.COLLECTION_NAME,
            query_vector=query_vector,
            limit=top_k,
            with_payload=True,
            score_threshold=0.0
        )

        return [{"score": r.score, "payload": r.payload} for r in results]


_vector_store = None


async def get_vector_store() -> QdrantVectorStore:
    global _vector_store
    if _vector_store is None:
        _vector_store = QdrantVectorStore()
    return _vector_store

