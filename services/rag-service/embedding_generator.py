"""Embedding generation using sentence-transformers."""

from sentence_transformers import SentenceTransformer
from typing import List
import numpy as np
import os
import torch


class EmbeddingGenerator:
    """Generates embeddings using sentence-transformers."""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize embedding model.
        Loads model once at startup for performance.
        """
        print(f"Loading embedding model: {model_name}")
        self.model = SentenceTransformer(model_name)
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model.to(self.device)
        print(f"Model loaded on device: {self.device}")
    
    def encode_texts(self, texts: List[str]) -> np.ndarray:
        """Generate embeddings for list of texts."""
        if not texts:
            return np.array([])
        
        embeddings = self.model.encode(
            texts,
            show_progress_bar=False,
            normalize_embeddings=True,
            batch_size=32
        )
        return embeddings
    
    def encode_single(self, text: str) -> np.ndarray:
        """Generate embedding for single text."""
        if not text.strip():
            return np.zeros(384)  # all-MiniLM-L6-v2 dimension
        
        embedding = self.model.encode(
            [text],
            show_progress_bar=False,
            normalize_embeddings=True
        )
        return embedding[0]
    
    def encode_chunks(self, chunks: List[Dict]) -> np.ndarray:
        """Encode chunk texts."""
        texts = [chunk["text"] for chunk in chunks]
        return self.encode_texts(texts)


# Global singleton for performance
_embedding_generator = None


def get_embedding_generator() -> EmbeddingGenerator:
    """Get singleton embedding generator."""
    global _embedding_generator
    if _embedding_generator is None:
        _embedding_generator = EmbeddingGenerator()
    return _embedding_generator


def generate_embeddings(texts: List[str]) -> np.ndarray:
    """Convenience function for embedding generation."""
    generator = get_embedding_generator()
    return generator.encode_texts(texts)

