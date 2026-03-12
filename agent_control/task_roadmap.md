# Project Implementation Roadmap

This roadmap defines the order of tasks required to build the system.

Each step must be completed before moving to the next.

---

## Phase 1 — Repository Initialization

Status: completed

Tasks:

- create repository structure - DONE
- create services folder - DONE
- create agent_control folder - DONE
- create docker-compose.yml - DONE
- create .env file - DONE

---

## Phase 2 — API Gateway

Status: completed

Tasks:

- create api-gateway service - DONE
- implement FastAPI app - DONE  
- create POST /chat endpoint - DONE
- connect gateway to other services using httpx - DONE

---

## Phase 3 — RAG Service (Full Semantic Retrieval)

Status: PRODUCTION READY ✅

Tasks:
- ✅ Document parsing: PDF, TXT, MD, DOCX (pypdf, python-docx, beautifulsoup4)
- ✅ Text chunking: 500 tokens, 50 overlap (tiktoken)
- ✅ Embedding generation: all-MiniLM-L6-v2 (sentence-transformers)
- ✅ FAISS vector store with disk persistence (data/vector_store/index.faiss)
- ✅ Semantic retrieval: cosine similarity search
- ✅ Vector persistence with metadata storage
- ✅ Production endpoints: POST /ingest/text, POST /ingest/file, POST /retrieve

**Files implemented:**
- models.py, document_parser.py, chunker.py, embedding_generator.py
- vector_store.py, retriever.py, main.py

**Status:** FULLY IMPLEMENTED - Ready for production use

---



## Phase 4 — Prompt Builder  

Status :completed 

Tasks :

-build prompt template with context and question formatting 
-DONE 
Accept context + question and output final prompt 

--- 

## Phase5—LLM Client  

Status :completed   

Tasks :

-connect to Ollama with environment variable configuration support 
-DONE 


-support OpenAI compatible APIs including cloud LLM providers like OpenAI, Anthropic etc. through standard API format 


-DONE 


-return LLM response back from model inference  


--- 

##Phase6—ResponseProcessor   

Status :completed    

Tasks :

-format LLM output cleanly without extra whitespace or artifacts  


-DONE    


-return metadata about response including token count and model information  


---     


##Phase7—Dockerization    

Status :completed     


Create Dockerfiles for each microservice container image - DONE   
Create docker-compose.yml orchestration file connecting all services internally via Docker network - DONE  

All five microservices are now containerized:
- api-gateway (port 8000)
- rag-service (port 8001)  
- prompt-builder (port 8002)
- llm-client (port 8003)
- response-processor (port 8004)

---

## Phase8—Testing

Status: pending

Tasks:

- Run docker-compose up to start all services
- Test document ingestion through RAG Service
- Test vector search/retrieval 
- Test chat request through API Gateway
- Verify response from TinyLlama or configured LLM provider
