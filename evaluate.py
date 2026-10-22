"""
evaluate.py - Measure the quality of the RAG answers on a reference Q&A set.

Run (venv activated):  python evaluate.py
Input:  evaluation/qa_reference.json  (questions + expected sources + keywords)
Output: evaluation/results.json       (detail per question + summary)

Calls the real Mistral API: about 1 embedding + 1 chat call per question.
"""
import json
import time
from pathlib import Path

from rag import ask

REFERENCE_FILE = Path("evaluation/qa_reference.json")
RESULTS_FILE = Path("evaluation/results.json")
PAUSE_SECONDS = 1.0                  # pause between questions (rate limit)


# ---------------------------------------------------------------------------
# 1. Scoring helpers (pure functions, tested in tests/test_evaluate.py)
# ---------------------------------------------------------------------------
def is_refusal(answer):
    """Same rule as rag.ask(): the model starts with "I don't know"."""
    return answer.strip().startswith("I don't know")


def source_hit(expected_sources, returned_sources):
    """True if at least one expected file is in the returned sources."""
    returned = {s["source"] for s in returned_sources}
    return any(path in returned for path in expected_sources)


def keyword_score(keywords, answer):
    """Share of keywords found in the answer (0.0 to 1.0).

    "a|b" means "a or b": the keyword counts if one of the variants is found.
    """
    if not keywords:
        return 1.0
    text = answer.lower()
    found = sum(
        any(variant.lower() in text for variant in keyword.split("|"))
        for keyword in keywords
    )
    return found / len(keywords)


def score(item, result):
    """Compare one RAG result with its reference item."""
    refused = is_refusal(result["answer"])
    out_of_scope = not item["expected_sources"]
    if out_of_scope:
        # Good behavior = refuse and give no sources
        passed = refused and not result["sources"]
        return {"refused": refused, "passed": passed}
    hit = source_hit(item["expected_sources"], result["sources"])
    keywords = keyword_score(item["keywords"], result["answer"])
    return {
        "refused": refused,
        "source_hit": hit,
        "keyword_score": keywords,
        "passed": hit and not refused and keywords == 1.0,
    }


# ---------------------------------------------------------------------------
# 2. Main: run every question, print a line per question, save the results
# ---------------------------------------------------------------------------
def main():
    items = json.loads(REFERENCE_FILE.read_text(encoding="utf-8"))
    rows = []

    for item in items:
        start = time.perf_counter()
        result = ask(item["question"])
        seconds = time.perf_counter() - start

        row = {"id": item["id"], **score(item, result), "seconds": round(seconds, 1),
               "answer": result["answer"],
               "sources": [s["source"] for s in result["sources"]]}
        rows.append(row)
        status = "PASS" if row["passed"] else "FAIL"
        print(f"{status}  {item['id']:<28} {seconds:5.1f}s  sources={row['sources']}")
        time.sleep(PAUSE_SECONDS)

    in_scope = [r for r in rows if "source_hit" in r]
    out_scope = [r for r in rows if "source_hit" not in r]
    summary = {
        "questions": len(rows),
        "passed": sum(r["passed"] for r in rows),
        "source_hit_rate": sum(r["source_hit"] for r in in_scope) / len(in_scope),
        "avg_keyword_score": sum(r["keyword_score"] for r in in_scope) / len(in_scope),
        "wrong_refusals": sum(r["refused"] for r in in_scope),
        "correct_refusals": f"{sum(r['passed'] for r in out_scope)}/{len(out_scope)}",
        "avg_seconds": round(sum(r["seconds"] for r in rows) / len(rows), 1),
    }

    print("\nSummary:")
    for key, value in summary.items():
        print(f"  {key:<18} {value:.2f}" if isinstance(value, float) else f"  {key:<18} {value}")

    RESULTS_FILE.write_text(
        json.dumps({"summary": summary, "results": rows}, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"\nDetails saved to {RESULTS_FILE}")


if __name__ == "__main__":
    main()
