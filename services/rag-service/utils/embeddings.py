"""New embedding generator for bge-base-en-v1.5 (384→768 dim)."""

from sentence_transformers import SentenceTransformer
from typing import List
import numpy as np
import torch
from config import settings


class EmbeddingGenerator:
    """bge-base-en-v1.5 embeddings."""

    def __init__(self):
        print(f"Loading: {settings.embedding_model}")
        self.model = SentenceTransformer(settings.embedding_model)
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model.to(self.device)
        self.dim = settings.embedding_dim
        print(f"Loaded on {self.device}, dim {self.dim}")

    def encode_texts(self, texts: List[str]) -> np.ndarray:
        if not texts:
            return np.array([])
        return self.model.encode(
            texts,
            show_progress_bar=False,
            normalize_embeddings=True,
            batch_size=32
        )

    def encode_single(self, text: str) -> np.ndarray:
        if not text.strip():
            return np.zeros(self.dim)
        emb = self.model.encode([text], normalize_embeddings=True)
        return emb[0]


# Singleton
_embedding_gen = None


def get_embedding_generator() -> EmbeddingGenerator:
    global _embedding_gen
    if _embedding_gen is None:
        _embedding_gen = EmbeddingGenerator()
    return _embedding_gen

