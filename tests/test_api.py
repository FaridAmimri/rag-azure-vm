"""
tests/test_api.py - API tests with FastAPI TestClient (like supertest in Node).

The real ask() is replaced by a fake one: no Mistral call, no FAISS index,
no cost, and the result is always the same.
Run (venv activated):  pytest -v
"""
import pytest
from fastapi.testclient import TestClient

import api

FAKE_RESULT = {
    "answer": "Restart the VM agent [1].",
    "sources": [{
        "title": "Troubleshoot the VM agent",
        "source": "troubleshoot-vm-agent.md",
        "url": "https://learn.microsoft.com/azure/virtual-machines/troubleshoot-vm-agent",
    }],
}


@pytest.fixture
def client(monkeypatch):
    # monkeypatch = temporary replacement, undone after each test (like jest.spyOn)
    monkeypatch.setattr(api, "get_components", lambda: None)
    monkeypatch.setattr(api, "ask", lambda question: FAKE_RESULT)
    with TestClient(api.app) as c:   # "with" also runs the lifespan (startup)
        yield c


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_ask_returns_answer_and_sources(client):
    response = client.post("/ask", json={"question": "My VM agent is not ready"})
    assert response.status_code == 200
    body = response.json()
    assert body["answer"] == FAKE_RESULT["answer"]
    assert body["sources"][0]["source"] == "troubleshoot-vm-agent.md"


@pytest.mark.parametrize("payload", [
    {"question": "hi"},            # too short (min 3)
    {"question": "x" * 501},       # too long (max 500)
    {},                            # field missing
])
def test_ask_rejects_invalid_question(client, payload):
    response = client.post("/ask", json=payload)
    assert response.status_code == 422
