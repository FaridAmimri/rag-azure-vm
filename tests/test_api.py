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


def test_ask_requires_api_key_when_set(client, monkeypatch):
    monkeypatch.setenv("API_KEY", "secret-test-key")
    assert client.post("/ask", json={"question": "My VM agent is not ready"}).status_code == 401
    wrong = client.post("/ask", json={"question": "My VM agent is not ready"},
                        headers={"X-API-Key": "wrong"})
    assert wrong.status_code == 401


def test_ask_accepts_valid_api_key(client, monkeypatch):
    monkeypatch.setenv("API_KEY", "secret-test-key")
    response = client.post("/ask", json={"question": "My VM agent is not ready"},
                           headers={"X-API-Key": "secret-test-key"})
    assert response.status_code == 200


def test_health_stays_public_with_api_key(client, monkeypatch):
    monkeypatch.setenv("API_KEY", "secret-test-key")
    assert client.get("/health").status_code == 200
