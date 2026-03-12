"""LLM Client Service - connects to Ollama or OpenAI."""

from fastapi import FastAPI, HTTPException
import os
import httpx

app = FastAPI(title="LLM Client Service")

# Configuration from environment variables
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "ollama")
LLM_API_URL = os.getenv("LLM_API_URL", "http://host.docker.internal:11434")
LLM_API_KEY = os.getenv("LLM_API_KEY", "")
LLM_MODEL = os.getenv("LLM_MODEL", "tinyllama")


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.post("/generate")
async def generate(request_data: dict):
    """Generate LLM response from prompt."""
    
    prompt=request_data.get("prompt"," ")
    
    if not prompt:
        raise HTTPException(status_code=400, detail="Prompt cannot be empty")
    
    try:
        if LLM_PROVIDER=="ollama":
            async with httpx.AsyncClient(timeout=120) as client:
                response=await client.post(
                    f"{LLM_API_URL}/api/generate",
                    json={"model": LLM_MODEL,"prompt": prompt,"stream": False}
                )
                
                if response.status_code==200:
                    result=response.json()
                    return {"response": result.get("response","")}
                else:
                    return {"response":"Error:"+str(response.status_code)}
                    
        elif LLM_PROVIDER=="openai":
            async with httpx.AsyncClient(timeout=120) as client:
                headers={
                    "Authorization":"Bearer "+LLM_API_KEY,
                    "Content-Type":"application/json"
                }
                
                response=await client.post(
                    f"{LLM_API_URL}",
                    headers=headers,
                    json={"model": LLM_MODEL,"messages":[{"role":"user","content":prompt}],"temperature":0.7}
                )
               
                if response.status_code==200:
                    result=response.json()
                    return {"response":result.get("choices",[{}])[0].get("message",{}).get("content","")}
                else:
                    return {"response":"Error:"+str(response.status_code)}
        
        else:
            return {"response":"Unknown provider:"+LLM_PROVIDER}
           
    except Exception as e:
        print(f"Error generating response:{e}")
        return {"response":"Sorry, I could not generate a response."}
