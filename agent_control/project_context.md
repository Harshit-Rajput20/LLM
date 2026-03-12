# Project Context

This project builds a distributed AI chat backend using microservices.

The system implements Retrieval Augmented Generation (RAG) and supports both local and cloud LLM providers.

The architecture is built using:

- Python 3.11
- FastAPI
- Docker
- Docker Compose
- FAISS vector database
- sentence-transformers embeddings

Default LLM:

Ollama running locally with model:
tinyllama

However the LLM must be configurable through environment variables.

Supported configuration variables:

LLM_PROVIDER
LLM_API_URL
LLM_API_KEY
LLM_MODEL

Example local configuration:

LLM_PROVIDER=ollama
LLM_API_URL=http://host.docker.internal:11434
LLM_MODEL=tinyllama

Example cloud configuration:

LLM_PROVIDER=openai
LLM_API_URL=https://api.openai.com/v1/chat/completions
LLM_API_KEY=your_key
LLM_MODEL=gpt-4o-mini

The system must support switching LLM providers without code changes.

The project must use Docker containers and FastAPI services.