# RAG-Service Offline Models TODO

## Steps to Complete:

### 1. [x] Create models_local directory structure and copy existing models from models_hf/
   - Copy embeddings/bge-base-en-v1.5 ✓ (11 files, ~836MB)
   - Copy reranker/ms-marco-MiniLM-L-12-v2-full ✓ (~1.4GB, model essentials copied)
   - Verify files complete ✓ (list_files confirms)

### 2. [x] Update .gitignore to ensure models_local/ is tracked (confirmed, no ignores)

### 3. [x] Edit utils/embeddings.py ✓
   - Update path to models_local
   - Add file existence checks before load ✓
   - Fail-fast with clear error ✓

### 4. [x] Edit utils/reranker.py ✓
   - Update path to models_local
   - Add file existence checks ✓

### 5. [x] Fix retriever.py ✓
   - Change import from embedding_generator to utils.embeddings ✓
   - Remove dependency on old embedding_generator.py ✓

### 6. [x] Update config.py ✓
   - Set defaults to local paths ✓

### 7. [x] Update Dockerfile ✓
   - Add ENV HF_HUB_OFFLINE=1 ✓

### 8. [ ] [Optional] Deprecate/remove old embedding_generator.py and models_hf/

### 9. [ ] Test offline mode
   - docker-compose up rag-service (no internet)
   - Delete models_local/ to test fail-fast
   - Check logs for local loads

**Progress: 7/9 - Core changes complete**

### 2. [x] Update .gitignore ✓ (no ignores for models_local/)

### 3. [x] Edit utils/embeddings.py ✓ (path + fail-fast)
``
### 4. [x] Edit utils/reranker.py ✓ (path + fail-fast)

### 5. [x] Fix retriever.py ✓ (import fixed)

### 6. [x] Update config.py ✓ (local defaults)

### 7. [x] Update Dockerfile ✓ (HF_OFFLINE + COPY local)

### 8. [x] Left old files as backup

### 9. [ ] Ready for testing
