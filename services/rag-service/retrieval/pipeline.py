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


import logging

logger = logging.getLogger(__name__)

async def retrieve_pipeline(query: str, top_k: int = 5, hybrid: bool = True) -> dict:
    """Hybrid retrieval."""
    logger.info(f"Starting hybrid retrieval: query='{query[:50]}...', top_k={top_k}, hybrid={hybrid}")

    
    logger.info("Checking cache")
    cache_client = await get_cache_client()
    cache_key = f"hybrid_query:{hashlib.sha256(f'{query}:{top_k}:{hybrid}'.encode()).hexdigest()}"
    cached = await cache_client.get(cache_key)
    if cached:
        logger.info("Cache hit")
        return json.loads(cached)
    logger.info("Cache miss - computing")

    
    logger.info(f"Generating query embedding")
    embedding_gen = get_embedding_generator()
    query_emb = embedding_gen.encode_single(query).tolist()
    
    logger.info(f"Vector search top_k={settings.vector_top_k}")
    v_store = await get_vector_store()
    vector_results = await v_store.search(query_emb, settings.vector_top_k)
    logger.info(f"Got {len(vector_results)} vector results")

    
    logger.info(f"Hybrid={hybrid}, vector_results={len(vector_results)}")
    if not hybrid:
        logger.info("Pure vector retrieval")
        final_docs = [r["payload"]["text"] for r in vector_results[:top_k]]
        scores = [r["score"] for r in vector_results[:top_k]]
        results = {"documents": final_docs, "scores": scores}
    else:
        logger.info("Hybrid mode - keyword + rerank")

        # Keyword search
        logger.info(f"Keyword search top_k={settings.keyword_top_k}")
        kw_index = await get_keyword_index()
        keyword_results = await kw_index.search(query, settings.keyword_top_k)
        logger.info(f"Got {len(keyword_results)} keyword results")
        
        logger.info(f"Merging {len(vector_results)} vector + {len(keyword_results)} keyword candidates")
        alpha = getattr(settings, 'alpha', 0.7)
        candidates = merge_candidates(vector_results, keyword_results, alpha=alpha)

        
        logger.info(f"Reranking {len(candidates)} candidates")
        reranker = get_reranker()
        reranked = reranker.rerank(query, candidates)
        logger.info(f"Reranked top {len(reranked)}")
        
        final_docs = [r["doc"]["text"] for r in reranked]
        scores = [r["score"] for r in reranked]
        results = {"documents": final_docs, "scores": scores}

    
    await cache_client.cache_query(query, results, settings.cache_ttl_query)
    return results


def merge_candidates(vec_results: List[Dict], kw_results: List[Dict], alpha: float = 0.7) -> List[Dict]:
    """Reciprocal Rank Fusion."""
    scores = {}
    all_chunks = set(r["payload"].get("chunk_id") for r in vec_results) | set(r.get("payload", {}).get("chunk_id") for r in kw_results)

    for chunk_id in all_chunks:
        vec_score = next((r["score"] for r in vec_results if r["payload"].get("chunk_id") == chunk_id), 0)
        kw_score = next((r["score"] for r in kw_results if r.get("payload", {}).get("chunk_id") == chunk_id), 0)
        fused_score = alpha * vec_score + (1 - alpha) * kw_score
        scores[chunk_id] = fused_score

    
    # Get top chunks
    sorted_chunks = sorted(scores, key=scores.get, reverse=True)[:20]  # pre-rerank

    # Find best matching payload for each chunk_id
    rerank_candidates = []
    for cid in sorted_chunks:
        # Find in vector results (prefer since has full payload)
        best_match = next((r for r in vec_results if r["payload"].get("chunk_id") == cid), None)
        if not best_match:
            best_match = next((r for r in kw_results if r.get("payload", {}).get("chunk_id") == cid), None)
        if best_match:
            text = best_match["payload"].get("text", f"chunk_{cid}")
        else:
            text = f"chunk_{cid}"
        rerank_candidates.append({"text": text, "chunk_id": cid})
    
    return rerank_candidates



