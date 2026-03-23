"""Reranker using cross-encoder/ms-marco-MiniLM-L-12-v2."""

import os
from sentence_transformers import CrossEncoder
from typing import List, Dict
import torch
from config import settings
import numpy as np


class Reranker:
    """Cross-encoder reranker (query, doc) → score."""

    def __init__(self):
        reranker_path = './models_local/reranker/ms-marco-MiniLM-L-12-v2-full'
        if not os.path.exists(f"{reranker_path}/config.json") or not os.path.exists(f"{reranker_path}/model.safetensors"):
            raise ValueError(f"Missing reranker model files in {reranker_path}. Expected config.json and model.safetensors.")
        print(f"Loading local reranker from {reranker_path}")
        self.model = CrossEncoder(reranker_path)
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

