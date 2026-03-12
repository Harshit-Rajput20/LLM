"""Retriever pipeline combining embedding generation and vector search."""

from typing import List, Tuple
import numpy as np
from .embedding_generator import get_embedding_generator
from .vector_store import get_vector_store


class Retriever:
    """Retrieval pipeline for semantic search."""
    
    def __init__(self, top_k: int = 5):
        self.top_k = top_k
        self.embedding_generator = get_embedding_generator()
        self.vector_store = get_vector_store()
    
    def retrieve(self, query: str) -> List[Tuple[float, dict]]:
        """Retrieve relevant chunks for query."""
        # Generate query embedding
        query_embedding = self.embedding_generator.encode_single(query)
        
        # Vector search
        results = self.vector_store.search(query_embedding, self.top_k)
        
        return results
    
    def get_retrieval_stats(self) -> dict:
        """Get retriever statistics."""
        return self.vector_store.get_stats()


def retrieve_documents(query: str, top_k: int = 5) -> dict:
    """Convenience function for document retrieval."""
    retriever = Retriever(top_k)
    results = retriever.retrieve(query)
    
    documents = [result[1]["text"] for result in results]
    scores = [result[0] for result in results]
    
    return {
        "documents": documents,
        "scores": scores
    }

