"""RAG Service for document ingestion and retrieval."""

from fastapi import FastAPI, HTTPException
import os

app = FastAPI(title="RAG Service")
documents = []

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.post("/ingest/text")
async def ingest_text(request_data: dict):
    """Ingest a text document into the vector store."""
    text_content = request_data.get("text", "")
    if not text_content:
        raise HTTPException(status_code=400, detail="Text cannot be empty")
    
    doc_id = len(documents)
    metadata = request_data.get("metadata", {})
    documents.append({"id": doc_id, "text": text_content, "metadata": metadata})
    
    return {"status": "success", "document_id": doc_id}

@app.post("/ingest/file")  
async def ingest_file(request_data: dict):
    """Ingest file content into the vector store."""
    file_contents = request_data.get("content", "")
    if not file_contents.strip():
        raise HTTPException(status_code=400, detail="File is empty")
    
    doc_id = len(documents)
    filename = request_data.get("filename", "unknown")
    documents.append({
        "id": doc_id,
        "text": file_contents,
        "metadata": {"source": "file", "filename": filename}
    })
    
    return {
        "status": "success",
        "filename": filename,
        "chars_processed": len(file_contents)
    }

@app.post("/retrieve")
async def retrieve(request_data: dict):
    """Retrieve relevant documents based on query using keyword matching."""
    query_text = request_data.get("query", "")
    
    if not query_text:
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    
    if not documents:
        return {"documents": [], "scores": []}
    
    results = []
    query_words = set(query_text.lower().split())
    
    for doc in documents:
        doc_text = doc.get("text", "").lower()
        doc_words = set(doc_text.split())
        
        # Calculate keyword overlap score
        common_words = query_words & doc_words
        score = float(len(common_words)) / max(len(query_words), 1)
        
        results.append({
            "text": doc.get("text", ""),
            "score": score
        })
    
    # Sort by score descending
    results.sort(key=lambda x: x["score"], reverse=True)
    
    # Take top 5 results
    top_results = results[:5]
    
    retrieved_docs = [r["text"] for r in top_results]
    retrieved_scores = [r["score"] for r in top_results]
    
    return {
        "documents": retrieved_docs,
        "scores": retrieved_scores
    }

