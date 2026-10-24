"""
api.py - Expose the RAG pipeline through a REST API (FastAPI).

Run (venv activated):  uvicorn api:app --reload
Interactive docs:      http://127.0.0.1:8000/docs

If the API_KEY environment variable is set, POST /ask needs the header
"X-API-Key: <API_KEY>" (401 otherwise). Not set = no check (local dev).
"""
import os
import secrets
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Security
from fastapi.security import APIKeyHeader
from pydantic import BaseModel, Field

from rag import ask, get_components


@asynccontextmanager
async def lifespan(app):
    get_components()   # load FAISS + Mistral clients once, at startup
    yield              # the API runs here


app = FastAPI(title="Azure VM RAG API", version="0.1.0", lifespan=lifespan)


# Request / response schemas: FastAPI validates them and shows them in /docs
class AskRequest(BaseModel):
    question: str = Field(min_length=3, max_length=500)


class Source(BaseModel):
    title: str
    source: str
    url: str


class AskResponse(BaseModel):
    answer: str
    sources: list[Source]


# Adds an "Authorize" button in /docs to type the key once
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def check_api_key(key: str | None = Security(api_key_header)):
    """Reject the request if API_KEY is set and the header does not match."""
    expected = os.getenv("API_KEY")
    if not expected:
        return
    # compare_digest: constant-time comparison, avoids timing attacks
    if key is None or not secrets.compare_digest(key, expected):
        raise HTTPException(status_code=401, detail="Invalid or missing API key")


@app.get("/health")
def health():
    return {"status": "ok"}


# "def" and not "async def": ask() is blocking (FAISS + HTTP call to Mistral),
# so FastAPI runs it in a worker thread and the server stays responsive
@app.post("/ask", response_model=AskResponse, dependencies=[Depends(check_api_key)])
def ask_endpoint(body: AskRequest):
    return ask(body.question)