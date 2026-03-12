"""API Gateway Service for AI Chat Backend.
Handles incoming chat requests and routes them through microservices.
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import httpx
import os

app = FastAPI(title="AI Chat API Gateway")

RAG_SERVICE_URL = os.getenv("RAG_SERVICE_URL", "http://rag-service:8001")
LLM_CLIENT_URL = os.getenv("LLM_CLIENT_URL", "http://llm-client:8003")
PROMPT_BUILDER_URL = os.getenv("PROMPT_BUILDER_URL", "http://prompt-builder:8002")
RESPONSE_PROCESSOR_URL = os.getenv("RESPONSE_PROCESSOR_URL", "http://response-processor:8004")


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    response: str


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.post("/chat", response_model=ChatResponse)
async def chat(request_data: dict):
    user_message=request_data.get("message"," ")
    
    if not user_message:
        raise HTTPException(status_code=400, detail="Message cannot be empty") 
    
    async with httpx.AsyncClient(timeout=120) as client:
        context_list=[]
        
        # Step 1 Retrieve context from RAG Service 
        try:
            retrieve_response=await client.post(
                f"{RAG_SERVICE_URL}/retrieve",
                json={"query": user_message}
            )
            
            if retrieve_response.status_code == 200:
                context_data=retrieve_response.json()
                context_list=context_data.get("documents",[])
                
        except Exception as e:
            print(f"RAG Service error {e}")
        
        # Step 2 Build prompt using Prompt Builder
        final_prompt=""
        
        try:
            prompt_resp = await client.post(
                f"{PROMPT_BUILDER_URL}/build",
                json={"context": chr(10).join(context_list), "question": user_message}
            )
            
            if prompt_resp.status_code == 200:
                final_prompt=prompt_resp.json().get("prompt"," ")
                
        except Exception as e:
            print(f"Prompt Builder error {e}")
        
        # Step 3: Get LLM Response
        raw_output = ""
        
        try:
            llm_resp = await client.post(
                f"{LLM_CLIENT_URL}/generate",
                json={"prompt": final_prompt}
            )
            
            if llm_resp.status_code == 200:
                raw_output = llm_resp.json().get("response", "")
        
        except Exception as e:
            print(f"LLM Client error {e}")
        
        # Step 4: Process Response
        try:
            process_resp = await client.post(
                f"{RESPONSE_PROCESSOR_URL}/process",
                json={"raw_output": raw_output}
            )
            
            if process_resp.status_code == 200 and process_resp.json().get("processed"):
                final_text = process_resp.json().get("text", raw_output)
                return ChatResponse(response=final_text)
        
        except Exception as e:
            print(f"Response Processor error {e}")
        
        return ChatResponse(response=raw_output if raw_output else "Sorry, I could not generate a response.")
