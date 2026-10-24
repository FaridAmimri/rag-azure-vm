# Dockerfile - Image of the RAG API (FastAPI + FAISS + Mistral)
#
# Build (faiss_index/ must exist: run python ingest.py first):
#   docker build -t rag-azure-vm .
# Run (the key comes from .env, it is never copied into the image):
#   docker run --rm -p 8000:8000 --env-file .env rag-azure-vm

# Small official Python image, same minor version as the local venv
FROM python:3.12-slim

# No .pyc files, logs printed immediately (not buffered)
# HF_HUB_OFFLINE=1: langchain-mistralai tries to download a (gated) tokenizer
# from Hugging Face at startup, then falls back to a simple one anyway.
# Offline mode skips that useless network call on every cold start.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    HF_HUB_OFFLINE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Dependencies first: Docker caches this layer and reuses it
# as long as requirements.txt does not change
COPY requirements.txt .
RUN pip install -r requirements.txt

# App code + prebuilt index (index built once, no embedding cost at startup)
COPY api.py rag.py ./
COPY faiss_index/ ./faiss_index/

# Run as a non-root user (security good practice)
RUN useradd --create-home appuser && chown -R appuser /app
USER appuser

EXPOSE 8000

# 0.0.0.0 = listen on all interfaces, needed to be reachable from outside the container
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]
