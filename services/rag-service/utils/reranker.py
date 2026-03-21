"""Reranker using bge-reranker-large."""

from sentence_transformers import CrossEncoder
from typing import List, Dict
import torch
from config import settings
import numpy as np


class Reranker:
    """BAAI/bge-reranker-large cross-encoder (query, doc) → score."""

    def __init__(self):
        print(f"Loading local reranker: {settings.reranker_model}")
        self.model = CrossEncoder('./models_hf/reranker/bge-reranker-large')
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"Reranker loaded local on {self.device}")


    def rerank(self, query: str, docs: List[Dict], top_k: int = 5) -> List[Dict]:
        """Rerank candidates: [(query, doc_text) pairs] → top_k scored docs."""
        pairs = [[query, doc["text"]] for doc in docs]
        if not pairs:
            return []
        scores = self.model.predict(pairs)
        # Higher score better (sigmoid ~ relevance)
        scored_docs = [{"doc": docs[i], "score": float(scores[i])} for i in range(len(scores))]
        scored_docs.sort(key=lambda x: x["score"], reverse=True)
        return scored_docs[:top_k]


_reranker = None


def get_reranker() -> Reranker:
    global _reranker
    if _reranker is None:
        _reranker = Reranker()
    return _reranker

