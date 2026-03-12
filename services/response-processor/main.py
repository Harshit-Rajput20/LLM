"""Response Processor Service - formats LLM output and returns metadata."""

from fastapi import FastAPI
import re

app = FastAPI(title="Response Processor Service")


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.post("/process")
async def process_response(request_data: dict):
    """Process and format LLM response."""
    
    raw_output = request_data.get("raw_output", "")
    
    # Basic processing - clean up the response
    processed_text = raw_output.strip()
    
    # Remove any leading/trailing whitespace
    processed_text = re.sub(r'^\s+|\s+$', '', processed_text)
    
    return {
        "processed": True,
        "text": processed_text,
        "metadata": {
            "length": len(processed_text),
            "word_count": len(processed_text.split())
        }
    }
