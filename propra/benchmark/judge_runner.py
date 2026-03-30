"""Judge runner for Propra benchmark.

Reads a baseline benchmark CSV, scores each row through GPT-4o as an
independent LLM judge (Stage 1 of benchmark_methodology_v2.md), and writes
draft scores to a new judged_ CSV in the same directory.

The judge prompt follows the exact template from docs/benchmark_methodology_v2.md,
including the full state LBO corpus in each call.

Usage:
    python -m propra.benchmark.judge_runner --input propra/benchmark/results/baseline_20260326_1357.csv
"""

import sys
import csv
import time
import json
import os
import argparse
from pathlib import Path

from openai import OpenAI
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding="utf-8")

# ---------------------------------------------------------------------------
# Path setup
# ---------------------------------------------------------------------------

_THIS_DIR = Path(__file__).resolve().parent          # propra/benchmark/
_PROPRA_DIR = _THIS_DIR.parent                       # propra/
_PROJECT_ROOT = _PROPRA_DIR.parent                   # repo root
_TXT_DIR = _PROPRA_DIR / "data" / "txt"

load_dotenv(_PROJECT_ROOT / ".env")

# ---------------------------------------------------------------------------
# Ground truth  (keys Q01–Q20 to match methodology doc)
# ---------------------------------------------------------------------------

GROUND_TRUTH: dict[str, dict] = {
    "Q01": {
        "section_family": "Definitionen",
        "minimum_answer_elements": "mit dem Boden verbunden; aus Bauprodukten hergestellt; bauliche Anlagen und Einrichtungen",
    },
    "Q02": {
        "section_family": "Definitionen",
        "minimum_answer_elements": "nicht nur vorübergehender Aufenthalt; geeignet für Menschen (Wohnen/Arbeiten); Abgrenzung zu Nebenräumen",
    },
    "Q03": {
        "section_family": "Stellplätze",
        "minimum_answer_elements": "Flächen zum Abstellen von Fahrzeugen; außerhalb öffentlicher Verkehrsflächen; Abgrenzung zu Garagen",
    },
    "Q04": {
        "section_family": "Genehmigungsverfahren",
        "minimum_answer_elements": "Grundsatz der Genehmigungspflicht; gesetzliche Ausnahmen definiert; Erfordernis einer Baugenehmigung vor Durchführung des Vorhabens",
    },
    "Q05": {
        "section_family": "Abstandsflächen",
        "minimum_answer_elements": "Abstand zu Grundstücksgrenzen; Einfluss auf Gebäudeanordnung; Sicherung von Belichtung und Belüftung",
    },
    "Q06": {
        "section_family": "Allgemeine Anforderungen",
        "minimum_answer_elements": "Sicherheit und Ordnung; Schutz von Leben und Gesundheit; Gebrauchstauglichkeit der Anlage",
    },
    "Q07": {
        "section_family": "Aufenthaltsräume",
        "minimum_answer_elements": "ausreichende Belichtung; ausreichende Lüftung; Mindesthöhe oder Raumgröße",
    },
    "Q08": {
        "section_family": "Brandschutz",
        "minimum_answer_elements": "Entstehung von Bränden verhindern; Ausbreitung von Feuer begrenzen; Rettung von Menschen ermöglichen",
    },
    "Q09": {
        "section_family": "Rettungswege",
        "minimum_answer_elements": "erster Rettungsweg erforderlich; zweiter Rettungsweg erforderlich; sichere Nutzung im Gefahrenfall",
    },
    "Q10": {
        "section_family": "Grundstücke / Erschließung",
        "minimum_answer_elements": "bauliche Eignung des Grundstücks; gesicherte Erschließung; Zugang für Rettungskräfte",
    },
    "Q11": {
        "section_family": "Brandschutz / Gebäudeklassen",
        "minimum_answer_elements": "Gebäudeklasse bestimmt Brandschutzanforderungen; höhere Gebäudeklassen führen zu strengeren Anforderungen; Einfluss auf Rettungswege und bauliche Ausführung",
    },
    "Q12": {
        "section_family": "Stellplätze",
        "minimum_answer_elements": "Stellplatzpflicht abhängig von Nutzung; Bereitstellung erforderlicher Stellplätze; funktionaler Zusammenhang mit Gebäude",
    },
    "Q13": {
        "section_family": "Verfahrensfreiheit",
        "minimum_answer_elements": "gesetzlich definierte Vorhaben; keine Genehmigung erforderlich; Einhaltung materieller Anforderungen bleibt bestehen",
    },
    "Q14": {
        "section_family": "Bauaufsichtliche Maßnahmen",
        "minimum_answer_elements": "Baustopp möglich; Beseitigungsanordnung möglich; Nutzungsuntersagung möglich",
    },
    "Q15": {
        "section_family": "Bauaufsichtliche Maßnahmen",
        "minimum_answer_elements": "Verstoß gegen öffentliches Recht; Gefährdung von Sicherheit oder Ordnung; behördliche Untersagung",
    },
    "Q16": {
        "section_family": "Abweichungen",
        "minimum_answer_elements": "behördliche Zulassung erforderlich; begründeter Antrag notwendig; keine Gefährdung öffentlicher Belange",
    },
    "Q17": {
        "section_family": "Abstandsflächen / Grundstücke",
        "minimum_answer_elements": "Abstandsflächen begrenzen Bebauung; bestimmen Lage des Gebäudes; Schutz von Nachbargrundstücken",
    },
    "Q18": {
        "section_family": "Rettungswege / Brandschutz",
        "minimum_answer_elements": "ermöglichen Flucht von Personen; Bestandteil des Brandschutzkonzepts; Grundlage für Rettungskräfte",
    },
    "Q19": {
        "section_family": "Genehmigungsverfahren",
        "minimum_answer_elements": "Genehmigung oder Abnahme erforderlich; Einhaltung aller Anforderungen; Fertigstellung des Bauwerks",
    },
    "Q20": {
        "section_family": "Beteiligte am Bau (Bauherr)",
        "minimum_answer_elements": "Verantwortung für Einhaltung der Vorschriften; Organisation und Koordination; Sicherstellung notwendiger Genehmigungen",
    },
}

# ---------------------------------------------------------------------------
# Corpus loader
# ---------------------------------------------------------------------------

# Maps both ISO codes and human labels to the TXT filename stem in _TXT_DIR.
# Derived from rag.py JURISDICTION_MAP.
_CORPUS_MAP: dict[str, str] = {
    # ISO 3166-2 codes
    "DE-BE":  "BauO_BE",
    "DE-HE":  "BauO_HE",
    "DE-ST":  "BauO_LSA",
    "DE-MV":  "BauO_MV",
    "DE-NW":  "BauO_NRW",
    "DE-BY":  "BayBO",
    "DE-BB":  "BbgBO",
    "DE-HH":  "HBauO",
    "DE-HB":  "LBO_HB",
    "DE-SH":  "LBO_SH",
    "DE-SL":  "LBO_SL",
    "DE-RP":  "LBauO_RLP",
    "DE-MBO": "MBO",
    "DE-NI":  "NBauO",
    "DE-SN":  "SaechsBO",
    "DE-TH":  "ThuerBO",
    "DE-BW":  "BauO_BW",
    # Human labels
    "Berlin":                   "BauO_BE",
    "Hessen":                   "BauO_HE",
    "Sachsen-Anhalt":           "BauO_LSA",
    "Mecklenburg-Vorpommern":   "BauO_MV",
    "Nordrhein-Westfalen":      "BauO_NRW",
    "Bayern":                   "BayBO",
    "Brandenburg":              "BbgBO",
    "Hamburg":                  "HBauO",
    "Bremen":                   "LBO_HB",
    "Schleswig-Holstein":       "LBO_SH",
    "Saarland":                 "LBO_SL",
    "Rheinland-Pfalz":          "LBauO_RLP",
    "Musterbauordnung":         "MBO",
    "Niedersachsen":            "NBauO",
    "Sachsen":                  "SaechsBO",
    "Thüringen":                "ThuerBO",
    "Baden-Württemberg":        "BauO_BW",
}

_CORPUS_TRUNCATE = 90_000
_CORPUS_TRUNCATE_NOTE = "\n[TRUNCATED at 90000 chars for context window]"


def load_corpus(source_state: str) -> tuple[str, bool, int]:
    """
    Load the LBO TXT corpus for source_state.

    source_state may be an ISO 3166-2 code (e.g. "DE-BB") or a human label
    (e.g. "Brandenburg").  Both are resolved via _CORPUS_MAP.

    Returns (corpus_text, corpus_loaded, corpus_chars).
    On miss: returns ("[CORPUS NOT FOUND]", False, 0) and prints a warning.
    Truncates to _CORPUS_TRUNCATE chars if the file is longer.
    """
    stem = _CORPUS_MAP.get(source_state.strip())
    if stem is None:
        print(f"WARNING: no corpus mapping for source_state '{source_state}' — scoring without corpus")
        return "[CORPUS NOT FOUND]", False, 0

    txt_path = _TXT_DIR / f"{stem}.txt"
    if not txt_path.exists():
        print(f"WARNING: corpus file not found: {txt_path} — scoring without corpus")
        return "[CORPUS NOT FOUND]", False, 0

    text = txt_path.read_text(encoding="utf-8")
    if len(text) > _CORPUS_TRUNCATE:
        text = text[:_CORPUS_TRUNCATE] + _CORPUS_TRUNCATE_NOTE
    return text, True, len(text)


# ---------------------------------------------------------------------------
# Judge prompt template  (verbatim from benchmark_methodology_v2.md)
# ---------------------------------------------------------------------------

_JUDGE_PROMPT_TEMPLATE = """\
You are evaluating a legal question-answering system against a reference corpus (German LBO).

Reference corpus:
{corpus_text}

Query: {query}
Expected section family: {section_family}
Minimum answer elements: {ground_truth_elements}
Retrieved content: {retrieved_chunks}
System answer: {answer}

Score the answer on the following three dimensions. Return only a JSON object.

Retrieval (0-2): Do the retrieved chunks come from the expected section family: {section_family}?
  Use only the retrieved content field above - do not infer retrieval quality from the answer.
  0 = retrieved content is from the wrong section family or absent
  1 = retrieved content is partially from the correct section but incomplete or mixed with irrelevant sections
  2 = retrieved content is clearly from {section_family} and covers the key passages needed

Reasoning (0-2): Does the answer correctly address all minimum answer elements?
  0 = incorrect, 1 = partial (some elements present), 2 = all elements correct

Grounding (0-2): Is every factual claim in the answer traceable to the reference corpus?
  0 = at least one claim contradicts the corpus or has no basis in it
  1 = at least one claim is a reasonable inference not directly stated in the corpus, but nothing is contradicted
  2 = every factual claim can be found verbatim or clearly paraphrased in the corpus

Do not introduce external legal knowledge. Do not assume uniform wording across German states.
Only evaluate based on the provided reference corpus.

Return: {{"retrieval": <0|1|2>, "reasoning": <0|1|2>, "grounding": <0|1|2>}}\
"""

# ---------------------------------------------------------------------------
# Output CSV columns
# ---------------------------------------------------------------------------

OUTPUT_COLUMNS = [
    "query_id", "query_type", "difficulty", "query_text", "system",
    "retrieved_chunk_ids", "retrieved_chunks_text", "retrieved_jurisdictions", "top_score", "kg_chunks_added",
    "answer", "retrieval_ms", "total_ms", "tokens",
    "retrieval_draft", "reasoning_draft", "grounding_draft", "total_draft",
    "judge_rationale",
    "retrieval_final", "reasoning_final", "grounding_final", "total_final",
    "notes",
    "corpus_loaded", "corpus_chars", "section_family", "ground_truth_elements",
    "judge_raw_response",
]

# ---------------------------------------------------------------------------
# Extraction helpers
# ---------------------------------------------------------------------------

def extract_explanation(raw_answer: str) -> str:
    """Return the explanation field from a JSON answer, or the full string."""
    try:
        data = json.loads(raw_answer)
        return data.get("explanation", raw_answer)
    except (json.JSONDecodeError, TypeError):
        return raw_answer


def extract_sources(raw_answer: str) -> str:
    """Return cited_sources as a formatted string, or empty string."""
    try:
        data = json.loads(raw_answer)
        sources = data.get("cited_sources", [])
        if not sources:
            return ""
        parts = []
        for s in sources:
            if isinstance(s, dict):
                para = s.get("source_paragraph", "")
                reg = s.get("regulation_name", "")
                parts.append(f"{para} {reg}".strip())
            else:
                parts.append(str(s))
        return "; ".join(parts)
    except (json.JSONDecodeError, TypeError):
        return ""


# ---------------------------------------------------------------------------
# Judge call
# ---------------------------------------------------------------------------

def judge_row(
    row: dict,
    client: OpenAI,
) -> tuple[int, int, int, str, bool, int, str]:
    """
    Call GPT-4o to score one answer row against the full LBO corpus.

    Returns (retrieval, reasoning, grounding, judge_rationale,
             corpus_loaded, corpus_chars, raw_response).

    On JSON parse failure, sets retrieval/reasoning/grounding to -1 so they
    are distinguishable from genuine 0 scores.
    """
    qid = row["query_id"]
    # Normalise "Q1" → "Q01" for GROUND_TRUTH lookup
    gt_key = f"Q{int(qid[1:]):02d}"
    gt = GROUND_TRUTH.get(gt_key, {})
    section_family = gt.get("section_family", "unknown")
    min_elements = gt.get("minimum_answer_elements", "")

    # Determine source state from retrieved_jurisdictions (first non-empty token)
    jurisdictions = [
        j.strip()
        for j in row.get("retrieved_jurisdictions", "").split("|")
        if j.strip()
    ]
    source_state = jurisdictions[0] if jurisdictions else ""

    corpus_text, corpus_loaded, corpus_chars = load_corpus(source_state)

    # Format retrieved chunks from chunk IDs logged in the CSV
    chunk_ids = [c for c in row.get("retrieved_chunk_ids", "").split("|") if c.strip()]
    if chunk_ids:
        retrieved_chunks = "\n".join(f"[{i + 1}] {cid}" for i, cid in enumerate(chunk_ids))
    else:
        retrieved_chunks = "none"

    explanation = extract_explanation(row["answer"])

    prompt = _JUDGE_PROMPT_TEMPLATE.format(
        corpus_text=corpus_text,
        query=row["query_text"],
        section_family=section_family,
        ground_truth_elements=min_elements,
        retrieved_chunks=retrieved_chunks,
        answer=explanation,
    )

    response = client.chat.completions.create(
        model="gpt-4o",
        temperature=0,
        max_tokens=300,
        messages=[{"role": "user", "content": prompt}],
    )

    raw = response.choices[0].message.content.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1].rsplit("```", 1)[0].strip()

    try:
        data = json.loads(raw)
        retrieval = int(data["retrieval"])
        reasoning = int(data["reasoning"])
        grounding = int(data["grounding"])
        rationale = data.get("rationale", "")
    except (json.JSONDecodeError, KeyError, ValueError):
        return -1, -1, -1, "", corpus_loaded, corpus_chars, raw

    return retrieval, reasoning, grounding, rationale, corpus_loaded, corpus_chars, raw


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Propra benchmark judge runner")
    parser.add_argument("--input", required=True, metavar="CSV", help="Path to baseline CSV file")
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.is_absolute():
        input_path = Path.cwd() / input_path
    if not input_path.exists():
        print(f"Error: file not found: {input_path}")
        sys.exit(1)

    output_path = input_path.parent / f"judged_{input_path.name}"

    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

    with open(input_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    total_rows = len(rows)
    scored_count = 0
    rag_totals: list[int] = []
    graphrag_totals: list[int] = []
    output_rows: list[dict] = []

    for i, row in enumerate(rows):
        qid = row["query_id"]
        system = row["system"]
        query_text = row["query_text"]
        half = total_rows // 2

        # Derive ground truth fields for this row (used in output whether scored or skipped)
        gt_key = f"Q{int(qid[1:]):02d}"
        gt = GROUND_TRUTH.get(gt_key, {})
        section_family = gt.get("section_family", "")
        ground_truth_elements = gt.get("minimum_answer_elements", "")

        # Resume: skip already-scored rows, carry forward existing values
        if row.get("retrieval_draft", "").strip():
            print(f"Skipping {qid} [{system}] (already scored)")
            out = {col: row.get(col, "") for col in OUTPUT_COLUMNS}
            out.setdefault("corpus_loaded", "")
            out.setdefault("corpus_chars", "")
            out["section_family"] = section_family
            out["ground_truth_elements"] = ground_truth_elements
            out.setdefault("judge_raw_response", "")
            output_rows.append(out)
            existing_total = row.get("total_draft", "")
            if existing_total.strip():
                try:
                    t = int(existing_total)
                    if system == "RAG":
                        rag_totals.append(t)
                    else:
                        graphrag_totals.append(t)
                except ValueError:
                    pass
            continue

        print(f"Judging Q{int(qid[1:])}/{half} [{system}]: {query_text[:60]}")

        retrieval_score: int | str = ""
        reasoning_score: int | str = ""
        grounding_score: int | str = ""
        total_score: int | str = ""
        rationale = ""
        corpus_loaded = False
        corpus_chars = 0
        raw_response = ""

        try:
            r, re, g, rat, corpus_loaded, corpus_chars, raw_response = judge_row(row, client)
            retrieval_score = r
            reasoning_score = re
            grounding_score = g
            rationale = rat

            if r == -1:
                # Parse error — do not include in totals
                print(f"{qid} {system} parse error. Raw: {raw_response[:120]}")
            else:
                total_score = r + re + g
                scored_count += 1
                print(
                    f"{qid} {system} scored: R={r} Re={re} G={g} Total={total_score} |"
                    f" corpus={'OK' if corpus_loaded else 'MISS'}"
                )
                if system == "RAG":
                    rag_totals.append(total_score)
                else:
                    graphrag_totals.append(total_score)

        except Exception as exc:
            print(f"Error scoring {qid} [{system}]: {exc}")

        out = {col: row.get(col, "") for col in OUTPUT_COLUMNS}
        out["retrieval_draft"] = retrieval_score
        out["reasoning_draft"] = reasoning_score
        out["grounding_draft"] = grounding_score
        out["total_draft"] = total_score
        out["judge_rationale"] = rationale
        out["corpus_loaded"] = corpus_loaded
        out["corpus_chars"] = corpus_chars
        out["section_family"] = section_family
        out["ground_truth_elements"] = ground_truth_elements
        out["judge_raw_response"] = raw_response
        output_rows.append(out)

        time.sleep(1)

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=OUTPUT_COLUMNS, quoting=csv.QUOTE_ALL)
        writer.writeheader()
        writer.writerows(output_rows)

    rag_mean = f"{sum(rag_totals) / len(rag_totals):.1f}" if rag_totals else "n/a"
    graphrag_mean = f"{sum(graphrag_totals) / len(graphrag_totals):.1f}" if graphrag_totals else "n/a"

    print("Judge run complete.")
    print(f"Rows scored: {scored_count}")
    print(f"Mean total RAG: {rag_mean} | Mean total GraphRAG: {graphrag_mean}")
    print(f"Output: {output_path}")


if __name__ == "__main__":
    main()
