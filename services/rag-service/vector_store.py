"""FAISS vector store with persistence."""

import faiss
import numpy as np
import pickle
import os
from typing import List, Tuple, Dict
from pathlib import Path


class VectorStore:
    """FAISS vector store with persistent storage."""
    
    def __init__(self, index_path: str = "data/vector_store/index.faiss", metadata_path: str = "data/vector_store/metadata.pkl"):
        self.index_path = Path(index_path)
        self.metadata_path = Path(metadata_path)
        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        self.metadata_path.parent.mkdir(parents=True, exist_ok=True)
        self._index = None
        self._metadata = {}
        self.dimension = 384  # all-MiniLM-L6-v2 dimension
        self._load_index()
    
    def _create_index(self):
        """Create new FAISS index."""
        self._index = faiss.IndexFlatIP(self.dimension)  # Inner product for cosine similarity
        print(f"Created new FAISS index with dimension {self.dimension}")
    
    def _load_index(self):
        """Load index from disk if exists."""
        if self.index_path.exists() and self.metadata_path.exists():
            try:
                self._index = faiss.read_index(str(self.index_path))
                with open(self.metadata_path, 'rb') as f:
                    self._metadata = pickle.load(f)
                print(f"Loaded FAISS index with {self._index.ntotal} vectors")
            except Exception as e:
                print(f"Failed to load index: {e}. Creating new index.")
                self._create_index()
        else:
            self._create_index()
    
    def _save_index(self):
        """Save index to disk."""
        try:
            faiss.write_index(self._index, str(self.index_path))
            with open(self.metadata_path, 'wb') as f:
                pickle.dump(self._metadata, f)
            print(f"Saved index with {self._index.ntotal} vectors")
        except Exception as e:
            print(f"Failed to save index: {e}")
    
    def add_documents(self, embeddings: np.ndarray, chunks: List[Dict]):
        """Add embeddings and metadata."""
        if embeddings.shape[0] != len(chunks):
            raise ValueError("Embeddings and chunks must have same length")
        
        # Add to FAISS index
        self._index.add(embeddings.astype('float32'))
        
        # Store metadata
        for i, chunk in enumerate(chunks):
            vector_id = self._index.ntotal - len(chunks) + i
            self._metadata[vector_id] = chunk
        
        self._save_index()
    
    def search(self, query_embedding: np.ndarray, top_k: int = 5) -> List[Tuple[float, Dict]]:
        """Search for similar chunks."""
        if self._index.ntotal == 0:
            return []
        
        # Normalize query embedding
        faiss.normalize_L2(query_embedding.reshape(1, -1))
        
        # Search
        distances, indices = self._index.search(
            query_embedding.reshape(1, -1).astype('float32'), 
            min(top_k, self._index.ntotal)
        )
        
        results = []
        for i, (dist, idx) in enumerate(zip(distances[0], indices[0])):
            if idx < len(self._metadata):
                chunk = self._metadata[idx]
                # Convert cosine distance to similarity score (0-1)
                score = float(dist)
                results.append((score, chunk))
        
        return results
    
    def get_stats(self) -> Dict:
        """Get store statistics."""
        return {
            "total_vectors": self._index.ntotal,
            "dimension": self.dimension,
            "index_path": str(self.index_path)
        }


# Global singleton
_vector_store = None


def get_vector_store() -> VectorStore:
    """Get singleton vector store."""
    global _vector_store
    if _vector_store is None:
        _vector_store = VectorStore()
    return _vector_store

