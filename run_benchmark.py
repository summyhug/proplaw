"""
Benchmark runner — Phase 1 (RAG only).

Runs all 20 queries from benchmark_methodology_v2.md against the local
/api/assess endpoint, logs answers + retrieved chunks + latency + tokens,
and writes two output files:

  benchmark_results_raw.json   — full machine-readable record for LLM judge
  benchmark_results_table.csv  — scoring table ready for Sumit's review

Usage:
    1. Start the backend:  uvicorn propra.main:app --reload
       (run from the proplaw/ repo root, with .env present)
    2. Run this script:    python run_benchmark.py
    3. Optional state override: python run_benchmark.py --state "Bayern"

Defaults:
    BASE_URL     = http://localhost:8000
    STATE        = Baden-Württemberg
    PROPERTY_TYPE = Wohngebäude
    HAS_BPLAN    = False
"""

from __future__ import annotations

import sys
import json
import time
import csv
import argparse
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

try:
    import httpx
except ImportError:
    print("ERROR: httpx not installed. Run: pip install httpx")
    sys.exit(1)

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

BASE_URL = "http://localhost:8000"
DEFAULT_STATE = "Baden-Württemberg"
PROPERTY_TYPE = "Wohngebäude"
HAS_BPLAN = False
TIMEOUT_SECONDS = 60

OUTPUT_DIR = Path(__file__).parent
RAW_OUTPUT = OUTPUT_DIR / "benchmark_results_raw.json"
CSV_OUTPUT = OUTPUT_DIR / "benchmark_results_table.csv"

# ---------------------------------------------------------------------------
# 20 benchmark queries (from benchmark_methodology_v2.md)
# ---------------------------------------------------------------------------

QUERIES: list[dict] = [
    {"id": "Q01", "query": "Was sind bauliche Anlagen?",                                                                             "type": "Direct",             "difficulty": 1},
    {"id": "Q02", "query": "Was gilt als Aufenthaltsraum?",                                                                          "type": "Direct",             "difficulty": 1},
    {"id": "Q03", "query": "Was sind Stellplätze?",                                                                                  "type": "Structured",         "difficulty": 2},
    {"id": "Q04", "query": "Wann ist ein Bauvorhaben genehmigungspflichtig?",                                                        "type": "Structured",         "difficulty": 2},
    {"id": "Q05", "query": "Welche Anforderungen gelten für Abstandsflächen?",                                                       "type": "Structured",         "difficulty": 2},
    {"id": "Q06", "query": "Welche allgemeinen Anforderungen müssen bauliche Anlagen erfüllen?",                                     "type": "Structured",         "difficulty": 2},
    {"id": "Q07", "query": "Welche Anforderungen bestehen an Aufenthaltsräume?",                                                     "type": "Multi-step",         "difficulty": 3},
    {"id": "Q08", "query": "Welche Anforderungen gelten für den Brandschutz?",                                                       "type": "Multi-step",         "difficulty": 3},
    {"id": "Q09", "query": "Welche Anforderungen bestehen an Rettungswege in Gebäuden?",                                             "type": "Multi-step",         "difficulty": 3},
    {"id": "Q10", "query": "Welche Voraussetzungen müssen Grundstücke für eine Bebauung erfüllen?",                                  "type": "Multi-step",         "difficulty": 2},
    {"id": "Q11", "query": "Welche Zusammenhänge bestehen zwischen Brandschutzanforderungen und der Gebäudeklasse?",                 "type": "Cross-concept",      "difficulty": 3},
    {"id": "Q12", "query": "Welche Regelungen gelten für Stellplätze im Zusammenhang mit Gebäuden?",                                 "type": "Structured",         "difficulty": 2},
    {"id": "Q13", "query": "Wann ist ein Bauvorhaben verfahrensfrei?",                                                               "type": "Exception/Procedure","difficulty": 3},
    {"id": "Q14", "query": "Welche Folgen kann Bauen ohne Genehmigung haben?",                                                       "type": "Multi-step",         "difficulty": 3},
    {"id": "Q15", "query": "Unter welchen Bedingungen kann die Nutzung einer baulichen Anlage untersagt werden?",                    "type": "Exception/Procedure","difficulty": 3},
    {"id": "Q16", "query": "Unter welchen Voraussetzungen sind Abweichungen von bauordnungsrechtlichen Anforderungen möglich?",      "type": "Exception/Procedure","difficulty": 3},
    {"id": "Q17", "query": "Wie hängen Abstandsflächen und Grundstücksbebauung zusammen?",                                          "type": "Cross-concept",      "difficulty": 3},
    {"id": "Q18", "query": "Welche Rolle spielen Rettungswege im Brandschutz?",                                                     "type": "Cross-concept",      "difficulty": 3},
    {"id": "Q19", "query": "Welche Voraussetzungen müssen erfüllt sein, bevor eine Nutzung aufgenommen werden darf?",               "type": "Multi-step",         "difficulty": 3},
    {"id": "Q20", "query": "Welche Pflichten hat der Bauherr im Bauprozess?",                                                       "type": "Structured",         "difficulty": 2},
]

# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

def run_benchmark(state: str) -> list[dict]:
    """Run all 20 queries against /api/assess and return raw results."""
    results = []

    print(f"Running benchmark against: {BASE_URL}/api/assess")
    print(f"State: {state}  |  Property type: {PROPERTY_TYPE}  |  Has B-Plan: {HAS_BPLAN}")
    print(f"Queries: {len(QUERIES)}\n")

    with httpx.Client(base_url=BASE_URL, timeout=TIMEOUT_SECONDS) as client:
        for q in QUERIES:
            payload = {
                "jurisdiction": state,
                "property_type": PROPERTY_TYPE,
                "project_description": q["query"],
                "has_bplan": HAS_BPLAN,
            }

            print(f"  [{q['id']}] {q['query'][:70]}...")

            t_start = time.perf_counter()
            try:
                response = client.post("/api/assess", json=payload)
                latency_ms = round((time.perf_counter() - t_start) * 1000)

                if response.status_code != 200:
                    print(f"         ERROR {response.status_code}: {response.text[:120]}")
                    results.append({
                        **q,
                        "state": state,
                        "status": "error",
                        "http_status": response.status_code,
                        "error": response.text,
                        "answer": None,
                        "verdict": None,
                        "confidence": None,
                        "cited_sources": [],
                        "retrieved_chunks_summary": [],
                        "latency_ms": latency_ms,
                        "tokens": None,
                    })
                    continue

                data = response.json()
                # Extract token count from response headers if available
                # (Anthropic usage not exposed through /assess — log None)
                tokens = data.get("usage", {}).get("total_tokens", None)

                cited = data.get("cited_sources", [])
                print(f"         OK  {latency_ms}ms | verdict={data.get('verdict')} | confidence={data.get('confidence')} | sources={len(cited)}")

                results.append({
                    **q,
                    "state": state,
                    "status": "ok",
                    "http_status": 200,
                    "answer": data.get("explanation", ""),
                    "verdict": data.get("verdict"),
                    "confidence": data.get("confidence"),
                    "next_action": data.get("next_action", ""),
                    "cited_sources": cited,
                    # Summarise cited sources as chunk identifiers for the judge
                    "retrieved_chunks_summary": [
                        f"{s.get('jurisdiction', '')} · {s.get('paragraph', '')}"
                        for s in cited
                    ],
                    "latency_ms": latency_ms,
                    "tokens": tokens,
                })

            except httpx.ConnectError:
                print(f"         CONNECT ERROR — is the backend running at {BASE_URL}?")
                results.append({
                    **q,
                    "state": state,
                    "status": "connect_error",
                    "answer": None,
                    "verdict": None,
                    "confidence": None,
                    "cited_sources": [],
                    "retrieved_chunks_summary": [],
                    "latency_ms": None,
                    "tokens": None,
                })
                # Abort remaining queries if first call fails — backend is down
                if q["id"] == "Q01":
                    print("\nAborted — backend unreachable on first query.")
                    break

    return results


def write_raw(results: list[dict], path: Path) -> None:
    """Write full machine-readable JSON record."""
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"system": "RAG", "results": results}, f, ensure_ascii=False, indent=2)
    print(f"\nRaw results written to: {path}")


def write_csv(results: list[dict], path: Path) -> None:
    """
    Write scoring table CSV.

    Columns match benchmark_methodology_v2.md output format:
    Query | System | State | Retrieval (draft) | Retrieval (final) |
    Reasoning (draft) | Reasoning (final) | Grounding (draft) | Grounding (final) |
    Total (final) | Latency (ms) | Tokens
    Draft score columns are left blank — filled by LLM judge in Stage 1.
    Final score columns are left blank — filled by Sumit in Stage 2.
    """
    fieldnames = [
        "Query ID", "Query", "Type", "Difficulty", "System", "State",
        "Answer (truncated)",
        "Verdict", "Confidence",
        "Retrieved Sources",
        "Retrieval (draft)", "Retrieval (final)",
        "Reasoning (draft)", "Reasoning (final)",
        "Grounding (draft)", "Grounding (final)",
        "Total (final)",
        "Latency (ms)", "Tokens",
        "Notes",
    ]

    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for r in results:
            answer_trunc = (r.get("answer") or "")[:200].replace("\n", " ")
            sources_str = " | ".join(r.get("retrieved_chunks_summary", []))
            writer.writerow({
                "Query ID": r["id"],
                "Query": r["query"],
                "Type": r["type"],
                "Difficulty": "★" * r["difficulty"],
                "System": "RAG",
                "State": r.get("state", ""),
                "Answer (truncated)": answer_trunc if r["status"] == "ok" else f"ERROR: {r.get('error', r['status'])[:80]}",
                "Verdict": r.get("verdict", ""),
                "Confidence": r.get("confidence", ""),
                "Retrieved Sources": sources_str,
                "Retrieval (draft)": "",
                "Retrieval (final)": "",
                "Reasoning (draft)": "",
                "Reasoning (final)": "",
                "Grounding (draft)": "",
                "Grounding (final)": "",
                "Total (final)": "",
                "Latency (ms)": r.get("latency_ms", ""),
                "Tokens": r.get("tokens", ""),
                "Notes": "",
            })

    print(f"Scoring table written to:  {path}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Propra RAG benchmark runner — Phase 1")
    parser.add_argument(
        "--state",
        default=DEFAULT_STATE,
        help=f"German federal state to benchmark against (default: {DEFAULT_STATE})",
    )
    parser.add_argument(
        "--url",
        default=BASE_URL,
        help=f"Backend base URL (default: {BASE_URL})",
    )
    args = parser.parse_args()

    BASE_URL = args.url

    results = run_benchmark(state=args.state)

    ok_count = sum(1 for r in results if r["status"] == "ok")
    print(f"\n{ok_count}/{len(QUERIES)} queries completed successfully.")

    write_raw(results, RAW_OUTPUT)
    write_csv(results, CSV_OUTPUT)

    if ok_count < len(QUERIES):
        print("\nWARNING: Some queries failed. Check benchmark_results_raw.json for error details.")
        sys.exit(1)
    else:
        print("\nBenchmark complete. Next step: run LLM judge (Stage 1 scoring).")