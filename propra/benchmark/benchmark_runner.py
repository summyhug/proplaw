"""
Benchmark runner for Propra.

Runs 20 benchmark queries against two retrieval systems (RAG and GraphRAG),
synthesises answers via Claude, and logs all results to a timestamped CSV file
under propra/benchmark/results/.

Usage:
    python benchmark_runner.py
"""

import sys
import csv
import time
import os
import argparse
from pathlib import Path
from datetime import datetime

import anthropic
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding="utf-8")

# ---------------------------------------------------------------------------
# Path setup
# ---------------------------------------------------------------------------

_THIS_DIR = Path(__file__).resolve().parent          # propra/benchmark/
_PROPRA_DIR = _THIS_DIR.parent                       # propra/
_RETRIEVAL_DIR = _PROPRA_DIR / "retrieval"
_PROJECT_ROOT = _PROPRA_DIR.parent                   # repo root
_PROMPTS_DIR = _PROPRA_DIR / "prompts"
_PROMPT_PATH = _PROMPTS_DIR / "assess.txt"

sys.path.insert(0, str(_RETRIEVAL_DIR))
sys.path.insert(0, str(_PROPRA_DIR.parent))          # so propra.graph.* works

import rag  # noqa: E402
from propra.graph.kg_retriever import get_related_chunks  # noqa: E402

load_dotenv(_PROJECT_ROOT / ".env")

# ---------------------------------------------------------------------------
# Benchmark queries
# Plain ASCII in source; QUERIES_DE maps id -> proper German for runtime use.
# ---------------------------------------------------------------------------

QUERIES = [
    {"id": "Q1",  "query": "Was sind bauliche Anlagen?",                                                                              "type": "Direct",             "difficulty": 1},
    {"id": "Q2",  "query": "Was gilt als Aufenthaltsraum?",                                                                           "type": "Direct",             "difficulty": 1},
    {"id": "Q3",  "query": "Was sind Stellplaetze?",                                                                                  "type": "Structured",         "difficulty": 2},
    {"id": "Q4",  "query": "Wann ist ein Bauvorhaben genehmigungspflichtig?",                                                         "type": "Structured",         "difficulty": 2},
    {"id": "Q5",  "query": "Welche Anforderungen gelten fuer Abstandsflaechen?",                                                      "type": "Structured",         "difficulty": 2},
    {"id": "Q6",  "query": "Welche allgemeinen Anforderungen muessen bauliche Anlagen erfuellen?",                                     "type": "Structured",         "difficulty": 2},
    {"id": "Q7",  "query": "Welche Anforderungen bestehen an Aufenthaltsraeume?",                                                     "type": "Multi-step",         "difficulty": 3},
    {"id": "Q8",  "query": "Welche Anforderungen gelten fuer den Brandschutz?",                                                       "type": "Multi-step",         "difficulty": 3},
    {"id": "Q9",  "query": "Welche Anforderungen bestehen an Rettungswege in Gebaeuden?",                                             "type": "Multi-step",         "difficulty": 3},
    {"id": "Q10", "query": "Welche Voraussetzungen muessen Grundstuecke fuer eine Bebauung erfuellen?",                               "type": "Multi-step",         "difficulty": 2},
    {"id": "Q11", "query": "Welche Zusammenhaenge bestehen zwischen Brandschutzanforderungen und der Gebaeudeklasse?",                "type": "Cross-concept",      "difficulty": 3},
    {"id": "Q12", "query": "Welche Regelungen gelten fuer Stellplaetze im Zusammenhang mit Gebaeuden?",                              "type": "Structured",         "difficulty": 2},
    {"id": "Q13", "query": "Wann ist ein Bauvorhaben verfahrensfrei?",                                                               "type": "Exception/Procedure","difficulty": 3},
    {"id": "Q14", "query": "Welche Folgen kann Bauen ohne Genehmigung haben?",                                                        "type": "Multi-step",         "difficulty": 3},
    {"id": "Q15", "query": "Unter welchen Bedingungen kann die Nutzung einer baulichen Anlage untersagt werden?",                     "type": "Exception/Procedure","difficulty": 3},
    {"id": "Q16", "query": "Unter welchen Voraussetzungen sind Abweichungen von bauordnungsrechtlichen Anforderungen moeglich?",      "type": "Exception/Procedure","difficulty": 3},
    {"id": "Q17", "query": "Wie haengen Abstandsflaechen und Grundstuecksbebauung zusammen?",                                         "type": "Cross-concept",      "difficulty": 3},
    {"id": "Q18", "query": "Welche Rolle spielen Rettungswege im Brandschutz?",                                                       "type": "Cross-concept",      "difficulty": 3},
    {"id": "Q19", "query": "Welche Voraussetzungen muessen erfuellt sein, bevor eine Nutzung aufgenommen werden darf?",               "type": "Multi-step",         "difficulty": 3},
    {"id": "Q20", "query": "Welche Pflichten hat der Bauherr im Bauprozess?",                                                         "type": "Structured",         "difficulty": 2},
]

# Proper German umlaut versions for runtime (retriever + LLM).
QUERIES_DE: dict[str, str] = {
    "Q1":  "Was sind bauliche Anlagen?",
    "Q2":  "Was gilt als Aufenthaltsraum?",
    "Q3":  "Was sind Stellpl\u00e4tze?",
    "Q4":  "Wann ist ein Bauvorhaben genehmigungspflichtig?",
    "Q5":  "Welche Anforderungen gelten f\u00fcr Abstandsfl\u00e4chen?",
    "Q6":  "Welche allgemeinen Anforderungen m\u00fcssen bauliche Anlagen erf\u00fcllen?",
    "Q7":  "Welche Anforderungen bestehen an Aufenthalts\u00e4ume?",
    "Q8":  "Welche Anforderungen gelten f\u00fcr den Brandschutz?",
    "Q9":  "Welche Anforderungen bestehen an Rettungswege in Geb\u00e4uden?",
    "Q10": "Welche Voraussetzungen m\u00fcssen Grundst\u00fccke f\u00fcr eine Bebauung erf\u00fcllen?",
    "Q11": "Welche Zusammenh\u00e4nge bestehen zwischen Brandschutzanforderungen und der Geb\u00e4udeklasse?",
    "Q12": "Welche Regelungen gelten f\u00fcr Stellpl\u00e4tze im Zusammenhang mit Geb\u00e4uden?",
    "Q13": "Wann ist ein Bauvorhaben verfahrensfrei?",
    "Q14": "Welche Folgen kann Bauen ohne Genehmigung haben?",
    "Q15": "Unter welchen Bedingungen kann die Nutzung einer baulichen Anlage untersagt werden?",
    "Q16": "Unter welchen Voraussetzungen sind Abweichungen von bauordnungsrechtlichen Anforderungen m\u00f6glich?",
    "Q17": "Wie h\u00e4ngen Abstandsfl\u00e4chen und Grundst\u00fccksbebauung zusammen?",
    "Q18": "Welche Rolle spielen Rettungswege im Brandschutz?",
    "Q19": "Welche Voraussetzungen m\u00fcssen erf\u00fcllt sein, bevor eine Nutzung aufgenommen werden darf?",
    "Q20": "Welche Pflichten hat der Bauherr im Bauprozess?",
}

# ---------------------------------------------------------------------------
# CSV columns
# ---------------------------------------------------------------------------

CSV_COLUMNS = [
    "query_id", "query_type", "difficulty", "query_text", "system",
    "retrieved_chunk_ids", "retrieved_chunks_text", "retrieved_jurisdictions", "top_score", "kg_chunks_added",
    "answer", "retrieval_ms", "total_ms", "tokens",
    "retrieval_draft", "reasoning_draft", "grounding_draft", "total_draft",
    "retrieval_final", "reasoning_final", "grounding_final", "total_final",
    "notes",
]

# ---------------------------------------------------------------------------
# Retrieval
# ---------------------------------------------------------------------------

def run_rag(query: str, retriever, jurisdiction: str | None = None) -> tuple[list[dict], float]:
    """Returns (chunks, retrieval_ms). k=8. retrieval_ms covers FAISS only."""
    t0 = time.time()
    chunks = retriever.retrieve(query, k=8, jurisdiction=jurisdiction)
    retrieval_ms = (time.time() - t0) * 1000
    return chunks, retrieval_ms


def run_graphrag(query: str, retriever, jurisdiction: str | None = None) -> tuple[list[dict], float]:
    """
    FAISS retrieve k=8, then enrich with KG neighbours.
    Returns (faiss_chunks + kg_chunks, retrieval_ms).
    retrieval_ms covers FAISS + KG enrichment; does NOT include LLM synthesis.
    """
    t0 = time.time()
    faiss_chunks = retriever.retrieve(query, k=8, jurisdiction=jurisdiction)
    kg_chunks = get_related_chunks(faiss_chunks)
    retrieval_ms = (time.time() - t0) * 1000
    return faiss_chunks + kg_chunks, retrieval_ms


# ---------------------------------------------------------------------------
# LLM synthesis
# ---------------------------------------------------------------------------

_SYSTEM_PROMPT = _PROMPT_PATH.read_text(encoding="utf-8")


def synthesise(query: str, chunks: list[dict], client: anthropic.Anthropic) -> tuple[str, int]:
    """
    Returns (answer_text, total_tokens).
    Model: claude-sonnet-4-6, max_tokens: 1000.
    """
    excerpts = "\n\n".join(
        f"[{i + 1}] {c.get('jurisdiction_label', '')} - {c.get('source_paragraph', '')}\n{c.get('text', '')}"
        for i, c in enumerate(chunks)
    )
    user_message = f"Frage: {query}\n\nGesetzesausz\u00fcge:\n{excerpts}"

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1000,
        system=_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}],
    )
    answer = response.content[0].text
    total_tokens = response.usage.input_tokens + response.usage.output_tokens
    return answer, total_tokens


# ---------------------------------------------------------------------------
# Main runner
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Propra benchmark runner")
    parser.add_argument(
        "--jurisdiction",
        default=None,
        metavar="CODE",
        help="ISO 3166-2 jurisdiction filter, e.g. DE-BB",
    )
    args = parser.parse_args()
    jurisdiction: str | None = args.jurisdiction

    results_dir = _THIS_DIR / "results"
    results_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    csv_path = results_dir / f"baseline_{timestamp}.csv"

    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    rag_retrieval_ms: list[float] = []
    graphrag_retrieval_ms: list[float] = []
    rag_total_ms: list[float] = []
    graphrag_total_ms: list[float] = []
    rag_tokens: list[int] = []
    graphrag_tokens: list[int] = []

    run_start = time.time()

    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, quoting=csv.QUOTE_ALL)
        writer.writerow(CSV_COLUMNS)

        for q in QUERIES:
            qid = q["id"]
            query_de = QUERIES_DE[qid]
            display_query = q["query"]

            for system in ("RAG", "GraphRAG"):
                print(f"Running {qid}/20 [{system}]: {display_query}")

                notes = ""
                answer = ""
                retrieval_ms = 0.0
                total_ms = 0.0
                tokens = 0
                retrieved_chunk_ids = ""
                retrieved_chunks_text = ""
                retrieved_jurisdictions = ""
                top_score = ""
                kg_chunks_added = 0
                faiss_chunks: list[dict] = []
                all_chunks: list[dict] = []

                try:
                    t0 = time.time()
                    if system == "RAG":
                        all_chunks, retrieval_ms = run_rag(query_de, rag.retriever, jurisdiction)
                        faiss_chunks = all_chunks
                        kg_chunks_added = 0
                        retrieved_chunks_text = " ||| ".join(
                            c["text"] for c in faiss_chunks if "text" in c
                        )
                    else:
                        faiss_only, _ = run_rag(query_de, rag.retriever, jurisdiction)
                        all_chunks, retrieval_ms = run_graphrag(query_de, rag.retriever, jurisdiction)
                        faiss_chunks = faiss_only
                        kg_chunks_added = len(all_chunks) - len(faiss_chunks)
                        retrieved_chunks_text = " ||| ".join(
                            ("[KG] " if c.get("kg_source") is True else "") + c["text"]
                            for c in all_chunks if "text" in c
                        )

                    retrieved_chunk_ids = "|".join(
                        c["chunk_id"] for c in faiss_chunks if "chunk_id" in c
                    )
                    retrieved_jurisdictions = "|".join(
                        c.get("jurisdiction_label", "") for c in all_chunks
                    )
                    scores = [c["score"] for c in faiss_chunks if "score" in c]
                    top_score = f"{max(scores):.4f}" if scores else ""

                    answer, tokens = synthesise(query_de, all_chunks, client)
                    total_ms = (time.time() - t0) * 1000

                except Exception as exc:  # noqa: BLE001
                    notes = str(exc)
                    answer = ""
                    tokens = 0

                if system == "RAG":
                    rag_retrieval_ms.append(retrieval_ms)
                    rag_total_ms.append(total_ms)
                    rag_tokens.append(tokens)
                else:
                    graphrag_retrieval_ms.append(retrieval_ms)
                    graphrag_total_ms.append(total_ms)
                    graphrag_tokens.append(tokens)

                print(
                    f"{qid} {system} done. "
                    f"Retrieval: {int(retrieval_ms)}ms | "
                    f"Total: {int(total_ms)}ms | "
                    f"Tokens: {tokens} | "
                    f"FAISS chunks: {len(faiss_chunks)} | "
                    f"KG chunks: {kg_chunks_added}"
                )

                writer.writerow([
                    qid,
                    q["type"],
                    q["difficulty"],
                    query_de,
                    system,
                    retrieved_chunk_ids,
                    retrieved_chunks_text,
                    retrieved_jurisdictions,
                    top_score,
                    kg_chunks_added,
                    answer,
                    int(retrieval_ms),
                    int(total_ms),
                    tokens,
                    "",  # retrieval_draft
                    "",  # reasoning_draft
                    "",  # grounding_draft
                    "",  # total_draft
                    "",  # retrieval_final
                    "",  # reasoning_final
                    "",  # grounding_final
                    "",  # total_final
                    notes,
                ])

    total_runtime = int(time.time() - run_start)

    rag_mean_retrieval = int(sum(rag_retrieval_ms) / len(rag_retrieval_ms)) if rag_retrieval_ms else 0
    graphrag_mean_retrieval = int(sum(graphrag_retrieval_ms) / len(graphrag_retrieval_ms)) if graphrag_retrieval_ms else 0
    rag_mean_total = int(sum(rag_total_ms) / len(rag_total_ms)) if rag_total_ms else 0
    graphrag_mean_total = int(sum(graphrag_total_ms) / len(graphrag_total_ms)) if graphrag_total_ms else 0
    rag_mean_tokens = int(sum(rag_tokens) / len(rag_tokens)) if rag_tokens else 0
    graphrag_mean_tokens = int(sum(graphrag_tokens) / len(graphrag_tokens)) if graphrag_tokens else 0

    print("Benchmark complete.")
    print(f"Total runtime: {total_runtime}s")
    print(f"RAG mean retrieval: {rag_mean_retrieval}ms | GraphRAG mean retrieval: {graphrag_mean_retrieval}ms")
    print(f"RAG mean total: {rag_mean_total}ms | GraphRAG mean total: {graphrag_mean_total}ms")
    print(f"RAG mean tokens: {rag_mean_tokens} | GraphRAG mean tokens: {graphrag_mean_tokens}")
    print(f"Output: {csv_path}")


if __name__ == "__main__":
    main()
