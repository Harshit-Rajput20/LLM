"""Prompt Builder Service - builds prompts from context and question."""

from fastapi import FastAPI
import os

app = FastAPI(title="Prompt Builder Service")


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.post("/build")
async def build_prompt(request_data: dict):
    """Build prompt from context and question."""
    
    context = request_data.get("context", "")
    question = request_data.get("question", "")
    
    # Build prompt template
    prompt = f"""Context:
{context}

Question: {question}

Answer:"""
    
    return {"prompt": prompt}
