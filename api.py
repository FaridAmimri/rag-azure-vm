"""
api.py - Expose the RAG pipeline through a REST API (FastAPI).

Run (venv activated):  uvicorn api:app --reload
Interactive docs:      http://127.0.0.1:8000/docs
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
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


@app.get("/health")
def health():
    return {"status": "ok"}


# "def" and not "async def": ask() is blocking (FAISS + HTTP call to Mistral),
# so FastAPI runs it in a worker thread and the server stays responsive
@app.post("/ask", response_model=AskResponse)
def ask_endpoint(body: AskRequest):
    return ask(body.question)