"""Text chunking utility with overlap support."""

from typing import List, Dict
import tiktoken


class TextChunker:
    """Chunks text into overlapping segments."""
    
    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.encoder = tiktoken.get_encoding("cl100k_base")
    
    def count_tokens(self, text: str) -> int:
        """Count tokens in text."""
        return len(self.encoder.encode(text))
    
    def chunk(self, text: str, document_id: str, filename: str, metadata: Dict = None) -> List[Dict]:
        """Split text into overlapping chunks."""
        if not text.strip():
            return []
        
        chunks = []
        metadata = metadata or {}
        
        # Split into sentences for better chunking
        sentences = self._split_into_sentences(text)
        
        current_chunk = ""
        chunk_num = 0
        
        for sentence in sentences:
            test_chunk = current_chunk + " " + sentence if current_chunk else sentence
            
            if self.count_tokens(test_chunk) > self.chunk_size:
                # Save current chunk
                if current_chunk.strip():
                    chunks.append({
                        "chunk_id": f"{document_id}_{chunk_num}",
                        "document_id": document_id,
                        "filename": filename,
                        "text": current_chunk.strip(),
                        "token_count": self.count_tokens(current_chunk),
                        "metadata": metadata
                    })
                    chunk_num += 1
                
                # Start new chunk with overlap
                overlap_sentences = sentence.split('.')[-self.chunk_overlap//10:] if '.' in sentence else [sentence]
                current_chunk = '. '.join(overlap_sentences)
            else:
                current_chunk = test_chunk
        
        # Add final chunk
        if current_chunk.strip():
            chunks.append({
                "chunk_id": f"{document_id}_{chunk_num}",
                "document_id": document_id,
                "filename": filename,
                "text": current_chunk.strip(),
                "token_count": self.count_tokens(current_chunk),
                "metadata": metadata
            })
        
        return chunks
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences."""
        # Simple sentence splitting
        sentences = re.split(r'(?<=[.!?])\s+', text)
        return [s.strip() for s in sentences if s.strip()]


def chunk_text(text: str, document_id: str, filename: str, chunk_size: int = 500, chunk_overlap: int = 50, metadata: Dict = None) -> List[Dict]:
    """Convenience function for chunking."""
    chunker = TextChunker(chunk_size, chunk_overlap)
    return chunker.chunk(text, document_id, filename, metadata)

