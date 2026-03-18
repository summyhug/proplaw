# Benchmark Methodology — RAG vs GraphRAG

## Purpose

This benchmark is designed to evaluate and compare the performance of:

- RAG (Retrieval-Augmented Generation)
- GraphRAG

The comparison is based on how each system answers a fixed set of 20 legal queries using German Landesbauordnung (LBO).

The goal is to measure how well each system:

- retrieves relevant legal information
- reasons over that information
- avoids unsupported or fabricated content

---

## Query Set (20)

Each query is labeled with a **Type** and **Difficulty**.

- Type: Direct, Structured, Multi-step, Exception/Procedure, Cross-concept
- Difficulty: ★ (low), ★★ (medium), ★★★ (high)

| # | Query | Type | Difficulty |
|---|------|------|------------|
| 1 | Was sind bauliche Anlagen? | Direct | ★ |
| 2 | Was gilt als Aufenthaltsraum? | Direct | ★ |
| 3 | Was sind Stellplätze? | Structured | ★★ |
| 4 | Wann ist ein Bauvorhaben genehmigungspflichtig? | Structured | ★★ |
| 5 | Welche Anforderungen gelten für Abstandsflächen? | Structured | ★★ |
| 6 | Welche allgemeinen Anforderungen müssen bauliche Anlagen erfüllen? | Structured | ★★ |
| 7 | Welche Anforderungen bestehen an Aufenthaltsräume? | Multi-step | ★★★ |
| 8 | Welche Anforderungen gelten für den Brandschutz? | Multi-step | ★★★ |
| 9 | Welche Anforderungen bestehen an Rettungswege in Gebäuden? | Multi-step | ★★★ |
| 10 | Welche Voraussetzungen müssen Grundstücke für eine Bebauung erfüllen? | Multi-step | ★★ |
| 11 | Welche Anforderungen ergeben sich aus der Nutzung eines Raums als Aufenthaltsraum? | Cross-concept | ★★★ |
| 12 | Welche Regelungen gelten für Stellplätze im Zusammenhang mit Gebäuden? | Structured | ★★ |
| 13 | Wann ist ein Bauvorhaben verfahrensfrei? | Exception/Procedure | ★★★ |
| 14 | Welche Folgen kann Bauen ohne Genehmigung haben? | Multi-step | ★★★ |
| 15 | Unter welchen Bedingungen kann die Nutzung einer baulichen Anlage untersagt werden? | Exception/Procedure | ★★★ |
| 16 | Unter welchen Voraussetzungen sind Abweichungen von bauordnungsrechtlichen Anforderungen möglich? | Exception/Procedure | ★★★ |
| 17 | Wie hängen Abstandsflächen und Grundstücksbebauung zusammen? | Cross-concept | ★★★ |
| 18 | Welche Rolle spielen Rettungswege im Brandschutz? | Cross-concept | ★★★ |
| 19 | Welche Voraussetzungen müssen erfüllt sein, bevor eine Nutzung aufgenommen werden darf? | Multi-step | ★★★ |
| 20 | Welche Pflichten hat der Bauherr im Bauprozess? | Structured | ★★ |

---

## Design Rationale for Query Set

The 20 benchmark queries are intentionally **normalized and structured** rather than written in natural, user-style language.

This choice is based on the following constraints:

- **Comparability**: All systems must be evaluated on identical inputs. Normalized queries reduce variance caused by wording.
- **Isolation of reasoning**: Each query targets a specific legal concept or relationship (e.g. Abstandsflächen, Rettungswege, Abweichungen).
- **Controlled difficulty**: Queries are categorized (Direct → Cross-concept) to ensure coverage of different reasoning types.
- **Cross-state applicability**: Queries avoid state-specific phrasing so they remain valid across all LBO texts.

As a result, the benchmark measures system performance on **legal retrieval and reasoning under controlled conditions**, not on handling real-world user phrasing.

---

## Additional User-Style Queries (Not Scored)

The following queries reflect how users typically phrase questions in practice. They are included for qualitative inspection only and are not part of the scored benchmark.

1. Can I build directly on the property boundary?
2. Do I need a permit to convert my attic into a room?
3. How far does my house need to be from my neighbor’s property?
4. What happens if I already built something without approval?
5. Can the authorities stop me from using my building?

---

## Ground Truth

Each query is associated with:

- A **section family** (e.g. definitions, Abstandsflächen, Rettungswege)
- A set of **minimum answer elements** that must be present

Answers are evaluated against these requirements.

---

## Evaluation Structure

Each answer is scored on three dimensions:

### 1. Retrieval (0–2)

Did the system use the correct legal context?

- 0 = incorrect or irrelevant
- 1 = partially relevant
- 2 = correct and sufficient

### 2. Reasoning (0–2)

Did the answer correctly interpret the legal content?

- 0 = incorrect
- 1 = partially correct
- 2 = correct and complete

### 3. Grounding (0–2)

Did the answer stay grounded in the corpus?

- 0 = fabricated content
- 1 = minor unsupported claims
- 2 = fully grounded

### Total Score

Each query is scored from **0 to 6**.

---

## Evaluation Process

For each query:

1. Run RAG
2. Run GraphRAG
3. Collect both answers
4. Score each answer using the 3 dimensions

---

## Output Format

| Query | System | Retrieval | Reasoning | Grounding | Total |
|-------|--------|----------|-----------|-----------|-------|

### Example

| Query | System | Retrieval | Reasoning | Grounding | Total |
|-------|--------|----------|-----------|-----------|-------|
| Q7 – Welche Anforderungen bestehen an Aufenthaltsräume? | RAG | 1 | 1 | 2 | 4 |
| Q7 – Welche Anforderungen bestehen an Aufenthaltsräume? | GraphRAG | 2 | 2 | 2 | 6 |

---

## Rules

- Paragraphs can be used for traceability, but not as the basis for retrieval or logic, since they don’t reliably represent the required answer content
- Do not introduce external knowledge
- Do not assume uniform wording across states
- Only evaluate based on the provided TXT corpus

---

This document defines the benchmark setup and evaluation method.

