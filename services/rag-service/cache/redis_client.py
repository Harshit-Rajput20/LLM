"""Redis caching layer for queries/embeddings."""

from redis.asyncio import Redis
from typing import Optional, Any
import hashlib
import json
from config import settings


class CacheClient:
    """Async Redis cache."""

    def __init__(self):
        self.client = Redis.from_url(settings.redis_url, decode_responses=True)

    async def get(self, key: str) -> Optional[str]:
        return await self.client.get(key)

    async def set(self, key: str, value: Any, ttl: int):
        await self.client.setex(key, ttl, json.dumps(value))

    async def query_cache(self, query: str, top_k: int, ttl: int = 3600) -> Optional[list]:
        """Cache retrieval results."""
        key = f"query:{hashlib.sha256(f'{query}:{top_k}'.encode()).hexdigest()}"
        cached = await self.get(key)
        return json.loads(cached) if cached else None

    async def cache_query(self, query: str, results: list, ttl: int):
        key = f"query:{hashlib.sha256(f'{query}:5'.encode()).hexdigest()}"
        await self.set(key, results, ttl)

    async def embedding_cache(self, text: str) -> Optional[list]:
        key = f"emb:{hashlib.sha256(text.encode()).hexdigest()}"
        cached = await self.get(key)
        return json.loads(cached) if cached else None

    async def cache_embedding(self, text: str, embedding: list, ttl: int):
        key = f"emb:{hashlib.sha256(text.encode()).hexdigest()}"
        await self.set(key, embedding, ttl)


_cache_client = None


async def get_cache_client() -> CacheClient:
    global _cache_client
    if _cache_client is None:
        _cache_client = CacheClient()
    return _cache_client

