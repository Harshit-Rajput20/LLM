# RAG Retrieval Methods Guide
## Overview
**Hybrid Retrieval Pipeline v2**: Combines semantic (vector) + lexical (keyword) search w/ fusion, reranking, & caching. Used by `/retrieve` endpoint.

**Key Params** (config.py):
- `vector_top_k=20`, `keyword_top_k=20`, `final_top_k=5`
- `alpha=0.7` (vector weight in fusion)
- Models: `BAAI/bge-base-en-v1.5` (embed), `BAAI/bge-reranker-large` (rerank)
- Cache: Redis TTL=3600s

## Full Retrieval Flow (`retrieve_pipeline`)
```
POST /retrieve {"query": "what is RAG?", "top_k": 5, "hybrid": true}

1. CACHE CHECK (Redis)
   ↓ miss
2. EMBED QUERY → vector (BGE-base, 768 dim)
3. VECTOR SEARCH (Qdrant)
   cosine_sim(query_vec, rag_chunks vectors) → top 20
   ↓ results: [{"score": 0.85, "payload": ChunkDict}]
4. IF hybrid=true:
   a. KEYWORD SEARCH (Elasticsearch)
      BM25(query, rag_chunks.text) → top 20
   b. RECIPROCAL RANK FUSION (RRF)
      fused_score = α·vec_score + (1-α)·kw_score  (α=0.7)
      → ~20 unique chunk_ids (sorted descending)
5. RERANKING (Cross-encoder)
   BGE-reranker: relevance(query, [candidate_texts]) → top 5
6. CACHE RESULT → return {"documents": [texts], "scores": [floats]}
```

**Pure Vector** (hybrid=false): Skip 4 → direct top_k from Qdrant.

**Output Example**:
```json
{
  "documents": ["chunk text 1", "chunk text 2", ...],
  "scores": [0.92, 0.87, ...]
}
```

## Detailed Methods

### 1. Semantic Search (Qdrant)
- **Method**: Cosine similarity on dense embeddings
- **Collection**: `rag_chunks`
- **Query**: embedded `query` vs chunk vectors
- **Score**: cosine (higher=more similar)
- **Inspect**:
  ```
  docker exec llm-qdrant-1 curl 'http://localhost:6333/collections/rag_chunks/points/search' \
    --data-raw '{"vector": [0.1,0.2,...], "limit": 5, "score_threshold": 0.7}'
  ```

### 2. Keyword Search (Elasticsearch)
- **Method**: BM25 (lexical, TF-IDF variant)
- **Index**: `rag_chunks` (text analyzer: standard)
- **Query**: `match {text: query}`
- **Score**: BM25 relevance
- **Inspect**:
  ```
  docker exec llm-elasticsearch-1 curl 'localhost:9200/rag_chunks/_search?pretty' \
    -d '{"query": {"match": {"text": "your query"}}, "size": 5}'
  ```

### 3. Fusion: Reciprocal Rank Fusion (RRF)
- **Why**: Combines rankings without normalization issues
- **Formula** (per chunk_id):
  ```
  vec_score = score if ranked in vector results else 0
  kw_score  = score if ranked in keyword else 0
  fused = 0.7 * vec_score + 0.3 * kw_score
  ```
- Dedupes by chunk_id, prefers vector payloads.

### 4. Reranking (BGE-reranker-large)
- **Method**: Cross-encoder scores query-candidate pairs
- **Input**: Top ~20 fused candidates
- **Output**: Reordered relevance scores
- **Why**: Fixes fusion/embedding gaps for final selection

### 5. Caching (Redis)
- **Key**: `hybrid_query:{sha256(query+top_k+hybrid)}`
- **Value**: JSON results
- **Inspect**:
  ```
  docker exec llm-redis-1 redis-cli KEYS 'hybrid_query:*' | head
  docker exec llm-redis-1 redis-cli GET hybrid_query:abc123...
  ```

## API Usage
```bash
curl -X POST http://localhost:8001/retrieve \
  -H "Content-Type: application/json" \
  -d '{"query": "RAG explanation", "top_k": 3, "hybrid": true}'
```

## Performance Tuning
| Param | Effect | Tradeoff |
|-------|--------|----------|
| `alpha ↑` | More semantic | Misses keywords |
| `*_top_k ↑` | More recall | Slower rerank |
| `hybrid=false` | Faster | No lexical boost |

## Debug/Inspect
1. **Logs**: `docker logs llm-rag-service-1 | grep 'Vector search\|Keyword search\|Reranking'`
2. **Metrics**: Watch `Got X vector results`, `Reranked top Y`
3. **Store Counts** (see INSPECTION_GUIDE.md): Ensure chunks exist
4. **No cache**: Add `?hybrid=false` or Redis flushall

**Implements**: Hybrid RAG best practices (dense+sparse → fuse → rerank).

**Updated**: Matches v2 code (retrieval/pipeline.py).
