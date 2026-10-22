"""
tests/test_rag.py - Tests of the relevance filter in rag.py.

A fake vector store replaces FAISS: no Mistral call, no index on disk.
"""
from langchain_core.documents import Document

import rag


class FakeVectorStore:
    """Returns fixed (chunk, distance) pairs, like similarity_search_with_score."""

    def __init__(self, pairs):
        self.pairs = pairs

    def similarity_search_with_score(self, question, k):
        return self.pairs[:k]


def make_doc(source):
    return Document(page_content="...", metadata={"title": source, "source": source, "url": ""})


STORE = FakeVectorStore([(make_doc("close.md"), 0.30), (make_doc("far.md"), 0.80)])


def test_retrieve_keeps_all_without_threshold(monkeypatch):
    monkeypatch.setattr(rag, "MAX_DISTANCE", None)
    docs = rag.retrieve(STORE, "question")
    assert [d.metadata["source"] for d in docs] == ["close.md", "far.md"]


def test_retrieve_drops_far_chunks(monkeypatch):
    monkeypatch.setattr(rag, "MAX_DISTANCE", 0.5)
    docs = rag.retrieve(STORE, "question")
    assert [d.metadata["source"] for d in docs] == ["close.md"]


def test_ask_refuses_without_llm_when_nothing_is_close(monkeypatch):
    def fail_if_called(_):
        raise AssertionError("the LLM must not be called")

    class FakeChain:
        invoke = staticmethod(fail_if_called)

    monkeypatch.setattr(rag, "MAX_DISTANCE", 0.1)
    monkeypatch.setattr(rag, "get_components", lambda: (STORE, FakeChain()))
    result = rag.ask("What is the price of Azure SQL?")
    assert result == {"answer": rag.NO_ANSWER, "sources": []}
