# PropLaw — Benchmark Findings Log

**Project:** neuefische AIPM Bootcamp Capstone 2025/2026
**Corpus:** BbgBO (DE-BB) — Phase 1 Baseline
**Methodology:** benchmark\_methodology\_v2.md

\---

## How to use this file

* One entry per finding. Assign sequential ID (F001, F002, ...).
* Status: OPEN / IN REVIEW / CLOSED
* Update status and add resolution when closed.
* Reference finding IDs in CSV notes column for traceability.
* Commit this file with every benchmark run.

\---

## Open Findings

### F001 — Q18 GraphRAG 0/6 suspicious score

**Date:** 2026-03-26
**Status:** OPEN — pending expert review
**Query:** Q18 — Welche Rolle spielen Rettungswege im Brandschutz?
**Finding:** GraphRAG scored 0/6 (Retrieval=0, Reasoning=0, Grounding=0).
Answer content is identical to RAG answer (KG chunks = 0 for this run,
meaning both systems received the same context and prompt). A 0/6 score
is inconsistent with identical content scoring 6/6 for RAG. Likely a
judge API error or empty response during the GPT-4o judge run.
**Action:** Re-run judge\_runner.py on Q18 GraphRAG row specifically.
Expert review required before including this score in aggregates.
**Impact:** Q18 GraphRAG excluded from current mean totals.
**Owner:** Matteo (expert validation)

\---

### F002 — 3 missing judge scores (API timeout)

**Date:** 2026-03-26
**Status:** OPEN — re-run required
**Affected rows:** Q5 GraphRAG, Q14 RAG, Q14 GraphRAG, Q16 GraphRAG
**Finding:** Judge runner failed to score these rows during the
2026-03-26 run. Likely Anthropic/OpenAI API timeout or rate limit.
The runner's resume support means re-running will skip already-scored
rows and only fill the missing ones.
**Action:** Re-run: python -m benchmark.judge\_runner benchmark/results/judged\_baseline\_20260326\_1357.csv
**Impact:** Missing rows excluded from aggregates. RAG mean based on
19/20 rows, GraphRAG mean based on 16/20 rows.
**Owner:** Sebastian

\---

### F003 — KG enrichment inactive (0 chunks for all queries)

**Date:** 2026-03-26
**Status:** OPEN — fix required before GraphRAG comparison is valid
**Finding:** get\_related\_chunks() returned 0 KG-derived chunks for
every query in the DE-BB run. Root cause: source\_paragraph string
matching between FAISS chunk metadata and graph node attributes is
not connecting. FAISS chunks use formats like "§ 6 BbgBO" while graph
nodes may use slightly different formats. As a result, RAG and
GraphRAG answers are identical for this entire run — the GraphRAG
vs RAG delta cannot be meaningfully measured yet.
**Action:** Sumit to investigate source\_paragraph format alignment
between rag.py chunk metadata and kg\_retriever.py node matching logic.
**Impact:** RAG vs GraphRAG comparison is invalid for this run.
GraphRAG scores reflect pure FAISS retrieval, not KG enrichment.
**Owner:** Sumit

\---

### F004 — Q13 Verfahrensfreiheit — corpus gap

**Date:** 2026-03-26
**Status:** OPEN — corpus extraction issue
**Query:** Q13 — Wann ist ein Bauvorhaben verfahrensfrei?
**Finding:** Both RAG and GraphRAG scored Retrieval=0 for this query.
The BbgBO corpus does not contain sufficient content from the
verfahrensfreie Vorhaben list (§ 61 BbgBO equivalent). Top FAISS
score was 0.70 — retrieval fired but returned wrong context.
This is a corpus extraction gap, not a pipeline failure.
**Action:** Re-extract BbgBO §61 section. Verify chunk content
covers the full list of verfahrensfreie Vorhaben.
**Impact:** Q13 scores (2/6 both systems) understate system quality.
Will improve after corpus fix.
**Owner:** Sebastian

\---

### F005 — Q1 cold-start latency outlier

**Date:** 2026-03-26
**Status:** OPEN — known, document only
**Finding:** Q1 RAG retrieval\_ms = 37,877ms (vs 20-70ms for all
subsequent queries). This is the sentence-transformer model loading
on first FAISS call. Skews RAG mean retrieval\_ms significantly.
**Action:** Document in benchmark report. Exclude Q1 from latency
aggregates or note as cold-start outlier. Consider warming the model
before benchmark runs in future.
**Impact:** Mean RAG retrieval\_ms is inflated. Real retrieval latency
is 20-70ms after warm-up.
**Owner:** Sebastian (documentation only)

\---

### F006 — Q11 GraphRAG +3 over RAG — classification layer effect

**Date:** 2026-03-26
**Status:** OPEN — positive finding, needs investigation
**Query:** Q11 — Welche Zusammenhänge bestehen zwischen
Brandschutzanforderungen und der Gebäudeklasse?
**Finding:** GraphRAG scored 6/6 vs RAG 3/6 on this cross-concept
query despite KG chunks = 0. The delta must come from the goal
classification step (kg\_query.query\_by\_category) influencing FAISS
retrieval context or the synthesis prompt. This is the strongest
single piece of evidence for KG architectural value in this run.
**Action:** Investigate what the classifier returned for Q11 and
how it affected retrieval. Document as pitch evidence.
**Impact:** Positive. Strengthens dual-retrieval hypothesis even
before KG enrichment is fully active.
**Owner:** Sebastian + Sumit

\---

## Closed Findings

### F007 — GraphRAG latency incorrectly measured (fixed)

**Date:** 2026-03-26
**Status:** CLOSED — fixed 2026-03-26
**Finding:** benchmark\_runner.py was measuring retrieval latency only,
not full pipeline latency. Two compounding bugs: (1) timer stopped
before LLM synthesis call, (2) GraphRAG FAISS call was cache-warm
after prior RAG call, causing \~44ms mean vs RAG \~769ms.
**Resolution:** Split into retrieval\_ms (retrieval only) and total\_ms
(full pipeline). Timer now wraps full retrieval + synthesis block.
Committed to feature/benchmark-runner-v2.
**Owner:** Sebastian

\---

### F008 — assess.py k=5 (updated to k=8)

**Date:** 2026-03-26
**Status:** CLOSED — fixed 2026-03-26
**Finding:** Production assess.py used k=5 for FAISS retrieval.
Annex-heavy and exception-heavy queries (e.g. Q13 Verfahrensfreiheit)
need more chunks to cover list-item content spread across multiple
chunks. k=8 increases coverage at negligible cost.
**Resolution:** k updated to 8 in assess.py and benchmark\_runner.py.
Committed to feature/benchmark-runner-v2.
**Owner:** Sebastian

\---

*Last updated: 2026-03-26 — baseline run DE-BB*

