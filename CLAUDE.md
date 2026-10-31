# RAG Azure VM — project context

## Goal
Prepare project 7 of the OpenClassrooms AI Engineer program: design and deploy a RAG system.
Imposed stack: Python + LangChain + Mistral + Faiss. Expose results through an API, write tests.

## Stack
- Python 3.12.10, venv in `.venv` (Windows, Git Bash, VS Code)
- LangChain 1.4.4 (v1.x: avoid old 0.x imports like `langchain.chains`)
- Mistral API: `mistral-embed` (embeddings, dimension 1024) + `mistral-small-latest` (chat)
- Faiss (`faiss-cpu`), saved locally in `faiss_index/`
- FastAPI + uvicorn for the API
- Key in `.env` as `MISTRAL_API_KEY` (never print, log or commit it)

## Corpus
- Azure Virtual Machines docs from GitHub repo `MicrosoftDocs/azure-compute-docs`
  (sparse checkout of `articles/virtual-machines`, CC-BY-4.0)
- Copied into `data/virtual-machines/`: 1220 `.md` files, 9.3 MB
- 14 files contain "troubleshoot" in their name: used as the dev subset

## Budget
Mistral pay-as-you-go: EUR 8.50/month included, overage cap EUR 10.
Develop on the small subset; index the full corpus only once the pipeline works.

## Status
- [x] Setup: venv, libraries, requirements.txt, .env, .gitignore
- [x] test_mistral.py works (chat OK, embedding dim 1024)
- [x] Step 7: ingest.py (load .md, split 1000/150, embed, FAISS.save_local), DEV_MODE flag
- [x] Step 8: RAG chain (retriever + prompt + Mistral), answers with sources
- [x] Step 9: FastAPI `POST /ask`
- [x] Step 10: tests (pytest) + quality evaluation (reference Q&A set, 11/11; full corpus (1220 files, 14297 chunks): 10/11, the miss cited metadata-security-protocol/faq.md, a valid source now accepted; MAX_DISTANCE 0.45 kept (0 wrong refusals))
- [x] Step 11: Docker + deployment on Azure Container Apps (image `ghcr.io/faridamimri/rag-azure-vm:v1`, app `rag-azure-vm` in `rg-rag-azure-vm` / env `env-rag-azure-vm`, francecentral, 0.5 vCPU / 1 GiB, 0-1 replicas, secrets `mistral-api-key` + `api-key`, `POST /ask` needs `X-API-Key`)
  URL: https://rag-azure-vm.proudsea-0a9f34b1.francecentral.azurecontainerapps.io

## How to work with me
- I'm new to Python (I know Node.js / JavaScript): explain each step briefly, with JS equivalents when useful.
- Go step by step; make me run and verify each step before moving on.
- Commands are for Git Bash on Windows.
- Reply in the language I write in (usually French).
