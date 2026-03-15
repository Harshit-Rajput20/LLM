"""Hybrid retrieval pipeline."""

from typing import List, Dict
import json
from config import settings
from utils.embeddings import get_embedding_generator
from storage.vector_store import get_vector_store
from storage.keyword_index import get_keyword_index
from utils.reranker import get_reranker
from cache.redis_client import get_cache_client
import hashlib


async def retrieve_pipeline(query: str, top_k: int = 5, hybrid: bool = True) -> dict:
    """Hybrid retrieval."""
    
    cache_client = await get_cache_client()
    cache_key = f"hybrid_query:{hashlib.sha256(f'{query}:{top_k}:{hybrid}'.encode()).hexdigest()}"
    cached = await cache_client.get(cache_key)
    if cached:
        return json.loads(cached)
    
    embedding_gen = get_embedding_generator()
    query_emb = embedding_gen.encode_single(query).tolist()
    
    # Vector search
    v_store = await get_vector_store()
    vector_results = await v_store.search(query_emb, settings.vector_top_k)
    
    if not hybrid:
        final_docs = [r["payload"]["text"] for r in vector_results[:top_k]]
        scores = [r["score"] for r in vector_results[:top_k]]
        results = {"documents": final_docs, "scores": scores}
    else:
        # Keyword search
        kw_index = await get_keyword_index()
        keyword_results = await kw_index.search(query, settings.keyword_top_k)
        
        # Simple RR F merge
        candidates = merge_candidates(vector_results, keyword_results, alpha=settings.alpha)
        
        # Rerank
        reranker = get_reranker()
        reranked = reranker.rerank(query, candidates)
        
        final_docs = [r["doc"]["text"] for r in reranked]
        scores = [r["score"] for r in reranked]
        results = {"documents": final_docs, "scores": scores}
    
    await cache_client.cache_query(query, results, settings.cache_ttl_query)
    return results


def merge_candidates(vec_results: List[Dict], kw_results: List[Dict], alpha: float = 0.7) -> List[Dict]:
    """Reciprocal Rank Fusion."""
    scores = {}
    all_chunks = set(r["payload"]["chunk_id"] for r in vec_results) | set(r["payload"]["chunk_id"] for r in kw_results)
    
    for chunk_id in all_chunks:
        vec_score = next((r["score"] for r in vec_results if r["payload"]["chunk_id"] == chunk_id), 0)
        kw_score = next((r["score"] for r in kw_results if r["payload"]["chunk_id"] == chunk_id), 0)
        fused_score = alpha * vec_score + (1 - alpha) * kw_score
        scores[chunk_id] = fused_score
    
    # Get top chunks
    sorted_chunks = sorted(scores, key=scores.get, reverse=True)[:20]  # pre-rerank
    # Fetch full payloads (simplified, assume passed)
    return [{"text": f"chunk_{cid}", "id": cid} for cid in sorted_chunks]


