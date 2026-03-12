# API Testing Guide

This document provides comprehensive instructions for testing all microservices endpoints using both curl and Postman.

---

## Table of Contents
1. [Service Overview & Endpoints](#service-overview--endpoints)
2. [Prerequisites](#prerequisites)
3. [Testing with curl](#testing-with-curl)
4. [Testing with Postman](#testing-with-postman)
5. [Complete Workflow Testing](#complete-workflow-testing)
6. [Example Responses](#example-responses)

---

## Service Overview & Endpoints

### 1. API Gateway Service (Port 8000)
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check endpoint |
| `/chat` | POST | Main chat endpoint - orchestrates full RAG pipeline |

### 2. RAG Service (Port 8001)
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check endpoint |
| `/ingest/text` | POST | Ingest plain text documents |
| `/ingest/file` | POST | Ingest file content |
| `/retrieve` | POST | Retrieve relevant documents based on query |

### 3. Prompt Builder Service (Port 8002)
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check endpoint |
| `/build` | POST | Build prompt from context and question |

### 4. LLM Client Service (Port 8003)
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check endpoint |
| `/generate` | POST | Generate LLM response from prompt |

### 5. Response Processor Service (Port 8004)
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check endpoint |
| `/process` | POST | Process and format LLM response |

---

## Prerequisites

### Starting the Services
Before testing, ensure all services are running:

```bash
# Start Ollama first (if using local LLM)
ollama serve
ollama run tinyllama

# Start all microservices with Docker Compose
docker-compose up --build

# Or run services individually for testing
docker-compose up -d rag-service
docker-compose up -d prompt-builder
docker-compose up -d llm-client
docker-compose up -d response-processor
docker-compose up -d api-gateway
```

### Environment Variables (.env)
```
LLM_PROVIDER=ollama
LLM_API_URL=http://host.docker.internal:11434
LLM_API_KEY=
LLM_MODEL=tinyllama
```

---

## Testing with curl

### 1. Health Checks

```bash
# API Gateway Health
curl http://localhost:8000/health

# RAG Service Health
curl http://localhost:8001/health

# Prompt Builder Health
curl http://localhost:8002/health

# LLM Client Health
curl http://localhost:8003/health

# Response Processor Health
curl http://localhost:8004/health
```

**Expected Response:**
```json
{"status": "healthy"}
```

---

### 2. RAG Service - Document Ingestion

#### Ingest Text Document
```bash
curl -X POST http://localhost:8001/ingest/text \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Python is a high-level programming language. It supports multiple paradigms including procedural, object-oriented, and functional programming.",
    "metadata": {"source": "tutorial", "topic": "python"}
  }'
```

**Expected Response:**
```json
{"status":"success","document_id":0}
```

#### Ingest File Content
```bash
curl -X POST http://localhost:8001/ingest/file \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Machine learning is a subset of artificial intelligence. Deep learning is a subset of machine learning. Neural networks are used in deep learning.",
    "filename": "ml_intro.txt"
  }'
```

**Expected Response:**
```json
{"status":"success","filename":"ml_intro.txt","chars_processed":126}
```

---

### 3. RAG Service - Document Retrieval

```bash
curl -X POST http://localhost:8001/retrieve \
  -H "Content-Type: application/json" \
  -d '{
    "query": "python programming"
  }'
```

**Expected Response:**
```json
{
  "documents_retrieved_final_result_": [
    "python is a high-level programming language. it supports multiple paradigms including procedural, object-oriented, and functional programming."
  ],
  "scores_retrieved_final_result_": [0.5]
}
```

---

### 4. Prompt Builder Service

```bash
curl -X POST http://localhost:8002/build \
  -H "Content-Type: application/json" \
  -d '{
    "context": "Python is a programming language. Java is also a programming language.",
    "question": "What is Python?"
  }'
```

**Expected Response:**
```json
{
  "prompt": "Context:\nPython is a programming language. Java is also a programming language.\n\nQuestion: What is Python?\n\nAnswer:"
}
```

---

### 5. LLM Client Service

```bash
curl -X POST http://localhost:8003/generate \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "What is Python in one sentence?"
  }'
```

**Expected Response:**
```json
{
  "response": "Python is a high-level, interpreted programming language known for its simplicity and readability."
}
```

---

### 6. Response Processor Service

```bash
curl -X POST http://localhost:8004/process \
  -H "Content-Type: application/json" \
  -d '{
    "raw_output": "   This is a sample LLM response with extra whitespace.   "
  }'
```

**Expected Response:**
```json
{
  "processed": true,
  "text": "This is a sample LLM response with extra whitespace.",
  "metadata": {
    "length": 54,
    "word_count": 9
  }
}
```

---

### 7. API Gateway - Full Chat Pipeline

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What is Python?"
  }'
```

**Expected Response:**
```json
{
  "response": "Python is a high-level, interpreted programming language..."
}
```

---

## Testing with Postman

### Step 1: Set Up Postman Collection

1. Open Postman
2. Create a new Collection called "AI Chat Backend"
3. Create the following requests:

---

### Step 2: Create Requests

#### 2.1 Health Check Requests

| Request Name | Method | URL |
|--------------|--------|-----|
| Gateway Health | GET | `http://localhost:8000/health` |
| RAG Health | GET | `http://localhost:8001/health` |
| Prompt Builder Health | GET | `http://localhost:8002/health` |
| LLM Client Health | GET | `http://localhost:8003/health` |
| Response Processor Health | GET | `http://localhost:8004/health` |

**Postman Setup:**
- No headers needed
- No body needed
- Click Send and verify `{"status": "healthy"}`

---

#### 2.2 Ingest Text Document (RAG Service)

- **Request Name:** Ingest Text
- **Method:** POST
- **URL:** `http://localhost:8001/ingest/text`
- **Headers:** 
  - Content-Type: application/json
- **Body (JSON):**
```json
{
  "text": "Python is a high-level programming language. It supports multiple paradigms including procedural, object-oriented, and functional programming.",
  "metadata": {
    "source": "documentation",
    "topic": "python"
  }
}
```
- **Expected Response:**
```json
{
  "status": "success",
  "document_id": 0
}
```

---

#### 2.3 Ingest More Documents

Add more documents for better testing:

```json
{
  "text": "FastAPI is a modern, fast web framework for building APIs with Python based on standard Python type hints.",
  "metadata": {"topic": "fastapi"}
}
```

```json
{
  "text": "Docker is a platform for developing, shipping, and running applications in containers.",
  "metadata": {"topic": "docker"}
}
```

---

#### 2.4 Retrieve Documents

- **Request Name:** Retrieve Documents
- **Method:** POST
- **URL:** `http://localhost:8001/retrieve`
- **Headers:** Content-Type: application/json
- **Body (JSON):**
```json
{
  "query": "python programming"
}
```
- **Expected Response:**
```json
{
  "documents_retrieved_final_result_": [
    "python is a high-level programming language..."
  ],
  "scores_retrieved_final_result_": [0.5]
}
```

---

#### 2.5 Build Prompt

- **Request Name:** Build Prompt
- **Method:** POST
- **URL:** `http://localhost:8002/build`
- **Headers:** Content-Type: application/json
- **Body (JSON):**
```json
{
  "context": "Python is a programming language. It is widely used in web development.",
  "question": "What is Python?"
}
```
- **Expected Response:**
```json
{
  "prompt": "Context:\nPython is a programming language. It is widely used in web development.\n\nQuestion: What is Python?\n\nAnswer:"
}
```

---

#### 2.6 Generate LLM Response

- **Request Name:** Generate Response
- **Method:** POST
- **URL:** `http://localhost:8003/generate`
- **Headers:** Content-Type: application/json
- **Body (JSON):**
```json
{
  "prompt": "What is Python in one sentence?"
}
```
- **Expected Response:**
```json
{
  "response": "Python is a high-level, interpreted programming language..."
}
```

> **Note:** This will fail if Ollama is not running. Make sure to start Ollama first.

---

#### 2.7 Process Response

- **Request Name:** Process Response
- **Method:** POST
- **URL:** `http://localhost:8004/process`
- **Headers:** Content-Type: application/json
- **Body (JSON):**
```json
{
  "raw_output": "   This is the raw LLM output with extra whitespace.   "
}
```
- **Expected Response:**
```json
{
  "processed": true,
  "text": "This is the raw LLM output with extra whitespace.",
  "metadata": {
    "length": 50,
    "word_count": 9
  }
}
```

---

#### 2.8 Full Chat Pipeline (API Gateway)

- **Request Name:** Chat
- **Method:** POST
- **URL:** `http://localhost:8000/chat`
- **Headers:** Content-Type: application/json
- **Body (JSON):**
```json
{
  "message": "What is Python?"
}
```
- **Expected Response:**
```json
{
  "response": "Python is a high-level, interpreted programming language..."
}
```

---

## Complete Workflow Testing

### Workflow 1: Full RAG Pipeline Test

This tests the complete flow from document ingestion to final response.

#### Step 1: Ingest Documents
```bash
# Ingest first document
curl -X POST http://localhost:8001/ingest/text \
  -H "Content-Type: application/json" \
  -d '{"text": "Python is a high-level programming language created by Guido van Rossum.", "metadata": {"topic": "python"}}'

# Ingest second document  
curl -X POST http://localhost:8001/ingest/text \
  -H "Content-Type: application/json" \
  -d '{"text": "FastAPI is a modern Python web framework for building APIs.", "metadata": {"topic": "fastapi"}}'
```

#### Step 2: Verify Documents are Stored
```bash
curl -X POST http://localhost:8001/retrieve \
  -H "Content-Type: application/json" \
  -d '{"query": "python"}'
```

#### Step 3: Test Full Chat Pipeline
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Tell me about Python"}'
```

---

### Workflow 2: Testing Without RAG (Direct LLM)

If you want to test the LLM without document retrieval:

```bash
# Send empty query to retrieve (no context)
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What is 2 + 2?"}'
```

---

### Workflow 3: Testing with OpenAI

To use OpenAI instead of Ollama:

1. Update `.env` file:
```env
LLM_PROVIDER=openai
LLM_API_URL=https://api.openai.com/v1/chat/completions
LLM_API_KEY=your_openai_api_key_here
LLM_MODEL=gpt-4o-mini
```

2. Rebuild and restart services:
```bash
docker-compose down
docker-compose up --build
```

3. Test:
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello!"}'
```

---

## Example Responses

### Successful Chat Response
```json
{
  "response": "Python is a high-level, interpreted programming language known for its simplicity and readability. It was created by Guido van Rossum and first released in 1991. Python emphasizes code readability and allows programmers to express concepts in fewer lines of code than would be possible in languages such as C++ or Java."
}
```

### Error Responses

#### 400 - Empty Message
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": ""}'
```
**Response:** `{"detail":"Message cannot be empty"}`

#### 400 - Empty Query
```bash
curl -X POST http://localhost:8001/retrieve \
  -H "Content-Type: application/json" \
  -d '{"query": ""}'
```
**Response:** `{"detail":"Query cannot be empty"}`

#### 503 - Service Unavailable
If a service is down, you may get timeout or connection errors in the logs.

---

## Troubleshooting

### Common Issues

1. **Ollama not running**
   - Error: `"Error generating response"`
   - Solution: Start Ollama with `ollama serve` and load a model with `ollama run tinyllama`

2. **Connection refused**
   - Error: `connect: connection refused`
   - Solution: Ensure Docker containers are running with `docker-compose ps`

3. **Empty retrieval results**
   - Issue: No documents match the query
   - Solution: Ingest more documents with relevant keywords

4. **Port already in use**
   - Error: `port is already allocated`
   - Solution: Stop other services using that port or update docker-compose.yml

### Checking Service Status
```bash
# Check running containers
docker-compose ps

# View logs for specific service
docker-compose logs rag-service

# View all logs
docker-compose logs
```

---

## Postman Environment Variables

For easier testing, set up Postman environment variables:

| Variable | Initial Value |
|----------|---------------|
| `gateway_url` | http://localhost:8000 |
| `rag_url` | http://localhost:8001 |
| `prompt_url` | http://localhost:8002 |
| `llm_url` | http://localhost:8003 |
| `processor_url` | http://localhost:8004 |

Then use variables in requests: `{{gateway_url}}/chat`

---

## Summary of Test Commands

```bash
# 1. Health Checks
curl http://localhost:8000/health
curl http://localhost:8001/health
curl http://localhost:8002/health
curl http://localhost:8003/health
curl http://localhost:8004/health

# 2. Ingest Documents
curl -X POST http://localhost:8001/ingest/text \
  -H "Content-Type: application/json" \
  -d '{"text": "Your document text here"}'

# 3. Retrieve
curl -X POST http://localhost:8001/retrieve \
  -H "Content-Type: application/json" \
  -d '{"query": "your search query"}'

# 4. Test Full Pipeline
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Your question"}'
```

