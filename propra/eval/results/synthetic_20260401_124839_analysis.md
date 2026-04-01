# Synthetic User Test Analysis

Source CSV: `propra/eval/results/synthetic_20260401_124839.csv`

Date: 2026-04-01

## Scope

This report summarizes the completed synthetic user test run for Brandenburg queries comparing `rag` and `graphrag`.

Important caveat:
- These are synthetic, LLM-judged evaluations produced by the runner, not human user study results.
- The findings are useful as directional benchmarking, but they should not be treated as final product validation.

## Executive Summary

GraphRAG did not dramatically outperform RAG in this run.

What GraphRAG did better:
- It was preferred more often in pairwise comparison.
- It scored slightly better on trustworthiness, usability, and traceability.
- Its clearest advantage appeared on the more conditional `Gartenhaus` task.

What GraphRAG did worse:
- It was slower overall.
- The score differences were small in absolute terms.
- The backend showed instability, with multiple `502 Bad Gateway` errors.

Bottom line:
- GraphRAG looks directionally better, but only modestly.
- The current gap is not large enough to claim a strong quality improvement over RAG.

## Overall Results

| Metric | RAG | GraphRAG |
| --- | ---: | ---: |
| Total rows | 78 | 78 |
| Completed rows | 74 | 74 |
| Error rows | 4 | 4 |
| Completion rate | 94.9% | 94.9% |
| Avg response time | 17.46s | 19.51s |
| Avg user confidence | 3.07 / 5 | 3.08 / 5 |
| Avg trustworthiness | 4.08 / 5 | 4.11 / 5 |
| Avg clarity | 4.28 / 5 | 4.27 / 5 |
| Avg usability | 4.39 / 5 | 4.43 / 5 |
| Avg traceability | 3.96 / 5 | 4.01 / 5 |

Interpretation:
- GraphRAG is about 2.05 seconds slower on average.
- GraphRAG has only very small scoring advantages overall.
- Clarity is effectively tied.

## Pairwise Comparison

There were `71` complete side-by-side pairs where both modes finished successfully.

Pairwise preference:
- `graphrag` preferred: `49`
- `rag` preferred: `22`

Average pairwise difference, `graphrag - rag`:

| Metric | Avg Difference |
| --- | ---: |
| User confidence | +0.03 |
| Trustworthiness | +0.03 |
| Clarity | +0.00 |
| Usability | +0.04 |
| Traceability | +0.07 |
| Response time | +1248 ms |

Interpretation:
- GraphRAG wins more comparisons than RAG.
- However, the numeric evaluation deltas are small.
- This suggests the evaluator often slightly preferred the GraphRAG phrasing or framing, even when the hard rubric scores were nearly tied.

## Comparison Rubric Outcomes

The comparison section in the CSV rated trustworthiness, clarity, and usability directly between both answers.

Percentage difference means:
- `(average GraphRAG score - average RAG score) / average RAG score`

| Comparison Metric | Avg GraphRAG Minus RAG | % Difference vs RAG Avg | GraphRAG Wins | RAG Wins | Ties | GraphRAG Win Rate | GraphRAG Share of Non-Tied Wins |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Trustworthiness | +0.14 | +3.2% | 15 | 5 | 51 | 21.1% | 75.0% |
| Clarity | +0.54 | +13.1% | 42 | 4 | 25 | 59.2% | 91.3% |
| Usability | +0.45 | +10.5% | 45 | 13 | 13 | 63.4% | 77.6% |

Overall across these three comparison metrics:
- GraphRAG wins: `102`
- RAG wins: `22`
- Ties: `89`
- GraphRAG won `47.9%` of all metric comparisons
- RAG won `10.3%` of all metric comparisons
- Ties made up `41.8%`
- Excluding ties, GraphRAG won `82.3%` of decisive comparisons

Interpretation:
- In direct comparison, GraphRAG was seen as noticeably better on clarity and usability.
- This is stronger than the per-response scoring differences.
- That mismatch is worth noting: pairwise judgments liked GraphRAG more than the standalone rubric scores suggest.

## Task Breakdown

### Fenster

Task: `Fenster einbauen oder verändern - brauche ich eine Genehmigung in Brandenburg?`

Results:
- RAG completed: `25`
- GraphRAG completed: `25`
- Both modes returned `ALLOWED` in all completed cases.
- Both modes achieved `Yes` task success in all completed cases.

Average response time:
- RAG: `13.33s`
- GraphRAG: `14.77s`

Pairwise preference:
- GraphRAG: `16`
- RAG: `9`

Interpretation:
- This task was basically a tie.
- GraphRAG did not meaningfully improve the outcome, and it was slightly slower.

### Gartenhaus

Task: `Kleines Gartenhaus nahe der Grundstucksgrenze in Brandenburg bauen - was ist erlaubt?`

Results:
- RAG completed: `23`
- GraphRAG completed: `23`
- Both modes returned `CONDITIONAL` in all completed cases.
- Both modes had the same task-success split: `18 Partial`, `5 Yes`

Average scores:
- Trustworthiness: `4.09` RAG vs `4.22` GraphRAG
- Traceability: `4.65` RAG vs `4.87` GraphRAG

Average response time:
- RAG: `22.56s`
- GraphRAG: `27.88s`

Pairwise preference:
- GraphRAG: `13`
- RAG: `7`

Interpretation:
- This is the task where GraphRAG helped the most.
- The gains are still moderate, but they are more visible here than in the other tasks.
- The cost is noticeably higher latency.

### Zaun

Task: `Zaun um das Grundstuck bauen - welche Regeln gelten in Brandenburg?`

Results:
- RAG completed: `26`
- GraphRAG completed: `26`
- RAG verdicts: `18 NOT_ALLOWED`, `8 CONDITIONAL`
- GraphRAG verdicts: `17 NOT_ALLOWED`, `9 CONDITIONAL`

Task success:
- RAG: `23 Partial`, `2 No`, `1 Yes`
- GraphRAG: `22 Partial`, `2 No`, `2 Yes`

Average traceability:
- RAG: `2.35`
- GraphRAG: `2.31`

Average response time:
- RAG: `16.91s`
- GraphRAG: `16.65s`

Pairwise preference:
- GraphRAG: `20`
- RAG: `6`

Interpretation:
- This was the hardest task for both systems.
- Both struggled on traceability.
- Even though GraphRAG was preferred more often, its scored clarity and trustworthiness were slightly worse on average.

## Reliability and Error Analysis

Error totals:
- Total errors: `8`
- RAG rows with errors: `4`
- GraphRAG rows with errors: `4`

All recorded errors were:
- `502 Bad Gateway` from `https://proplaw-graphrag.onrender.com/api/assess`

Interpretation:
- The failures look like backend instability rather than a retrieval-mode-specific logic bug.
- Because the same endpoint serves both modes, these errors likely reflect service reliability rather than a pure RAG vs GraphRAG difference.

## Conclusions

Main conclusions:
- GraphRAG shows a small but real directional advantage.
- The strongest improvement is on the more conditional `Gartenhaus` scenario.
- For simpler or more direct tasks such as `Fenster`, GraphRAG offers little visible benefit.
- The overall quality gap between RAG and GraphRAG is currently modest.
- Latency and backend reliability remain important concerns.

Recommended next steps:
- Improve GraphRAG answer quality on hard tasks where legal conditions and exceptions matter.
- Reduce GraphRAG latency so the quality gains are not offset by slower responses.
- Investigate the `502` failures on the shared backend.
- Validate these findings with human users before making product claims.
