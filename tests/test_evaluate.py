"""
tests/test_evaluate.py - Tests of the scoring helpers in evaluate.py.

Pure functions: no Mistral call, no FAISS index.
"""
from evaluate import is_refusal, keyword_score, score, source_hit

SOURCES = [{"title": "Restore points", "source": "restore-point-troubleshooting.md", "url": ""}]


def test_is_refusal():
    assert is_refusal("  I don't know, the documentation I have does not cover this.")
    assert not is_refusal("Restart the VM agent [1].")


def test_source_hit():
    assert source_hit(["restore-point-troubleshooting.md", "other.md"], SOURCES)
    assert not source_hit(["other.md"], SOURCES)


def test_keyword_score_with_variants():
    answer = "End the Shared Access Signature, then retry."
    assert keyword_score(["shared access|sas"], answer) == 1.0   # case-insensitive
    assert keyword_score(["shared access", "nouuid"], answer) == 0.5
    assert keyword_score([], answer) == 1.0


def test_score_out_of_scope_question():
    item = {"expected_sources": [], "keywords": []}
    refusal = {"answer": "I don't know, the documentation I have does not cover this.", "sources": []}
    invented = {"answer": "Azure SQL costs 5 USD.", "sources": SOURCES}
    assert score(item, refusal)["passed"]
    assert not score(item, invented)["passed"]


def test_score_in_scope_question():
    item = {"expected_sources": ["restore-point-troubleshooting.md"], "keywords": ["sas"]}
    good = {"answer": "End the SAS on the disk restore point [1].", "sources": SOURCES}
    assert score(item, good) == {
        "refused": False, "source_hit": True, "keyword_score": 1.0, "passed": True,
    }
