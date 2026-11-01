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
    monkeypatch.setattr(rag, "to_search_query", lambda question: question)
    result = rag.ask("What is the price of Azure SQL?")
    assert result == {"answer": rag.NO_ANSWER, "sources": []}


class RecordingChain:
    """Fake LLM chain: remembers what it received and returns a fixed text."""

    def __init__(self, output):
        self.output = output
        self.received = None

    def invoke(self, inputs):
        self.received = inputs
        return self.output


class RecordingStore(FakeVectorStore):
    """Fake vector store that remembers the text it was asked to search."""

    def similarity_search_with_score(self, question, k):
        self.query = question
        return super().similarity_search_with_score(question, k)


def test_ask_searches_in_english_but_answers_the_original_question(monkeypatch):
    store = RecordingStore([(make_doc("close.md"), 0.30)])
    chain = RecordingChain("Redimensionnez la VM [1].")
    monkeypatch.setattr(rag, "get_components", lambda: (store, chain))
    monkeypatch.setattr(rag, "to_search_query", lambda question: "resize a VM")

    result = rag.ask("Comment redimensionner une VM ?")

    assert store.query == "resize a VM"
    assert chain.received["question"] == "Comment redimensionner une VM ?"
    assert result["answer"] == "Redimensionnez la VM [1]."


def test_to_search_query_uses_the_llm_output(monkeypatch):
    monkeypatch.setattr(rag, "get_components", lambda: None)
    monkeypatch.setattr(rag, "_search_chain", RecordingChain("  resize a VM\n"))
    assert rag.to_search_query("Comment redimensionner une VM ?") == "resize a VM"


def test_to_search_query_falls_back_on_the_question(monkeypatch):
    monkeypatch.setattr(rag, "get_components", lambda: None)
    monkeypatch.setattr(rag, "_search_chain", RecordingChain("   "))
    assert rag.to_search_query("Comment redimensionner ?") == "Comment redimensionner ?"


DOCS = [make_doc("a.md"), make_doc("b.md"), make_doc("c.md")]


def test_cited_docs_keeps_only_cited_chunks():
    docs = rag.cited_docs("Check status.json [3]. Then restart [1, 3].", DOCS)
    assert [d.metadata["source"] for d in docs] == ["a.md", "c.md"]


def test_cited_docs_keeps_all_when_nothing_is_cited():
    assert rag.cited_docs("Restart the VM.", DOCS) == DOCS
