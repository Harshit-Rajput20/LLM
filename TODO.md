# Fix RAG Microservice ImportError and Startup Issues

## Steps:
- [x] 1. Update Dockerfile CMD to use 'uvicorn api.main:app --host 0.0.0.0 --port 8001'
- [x] 2. Update services/rag-service/main.py to run 'uvicorn.run("api.main:app", ...)'
- [ ] 3. Fix missing DocumentParser import in services/rag-service/api/main.py
- [ ] 4. Rebuild and test: docker-compose up --build rag-service
- [ ] 5. Verify service starts without import errors and /health endpoint works

Current progress: Starting step 1.
