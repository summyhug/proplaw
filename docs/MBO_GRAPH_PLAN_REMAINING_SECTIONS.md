# MBO Graph — Plan for Remaining Sections

This document describes how to add the remaining MBO sections (§31 onward) to the core knowledge graph: proposed edge structure, cross-sectional relations, and **residential relevance** so you can review, adjust relationships, and then implement in batch.

**Already in graph:** §1–§30 (Anwendungsbereich through Brandwände).

**Conventions used below:**
- **Lead node:** e.g. "2.1 = when X is required" → 2.1 `supplements` section; 2.2–2.x `sub_item_of` 2.1.
- **Exception:** "Abs. 1 und 2 gelten nicht für …" (or "Satz 1 gilt nicht für …") → the **listed cases** (e.g. 3.2–3.6) are **exclusions of the rules they refer to**: each list item gets `exception_of` → the node(s) it excludes (e.g. 3.2 `exception_of` 1.1 and 2.1). Optionally keep 3.1 as a textual anchor and link 3.2–3.6 `sub_item_of` 3.1 for structure, but the primary semantic relation is `exception_of` to the excluded rule(s).
- **references:** Explicit citations to other sections (e.g. Gebäudeklassen §2, Vorbauten §6, Rettungsweg §33).

---

## Residential relevance (apartment / house)

| Relevance | Meaning | Sections (examples) |
|-----------|--------|----------------------|
| **Core** | Directly applies to single-family house or apartment (building/use) | §31–§38, §47, §48, §49 (Stellplätze), §50 (multi-unit barrierefrei) |
| **Secondary** | Relevant for some residential (e.g. heating, elevators in apartment buildings, waste) | §39 Aufzüge, §40–§46 |
| **Low** | Mostly non-residential (schools, assembly, care) or only when building that type | §51 Sonderbauten (schools, Versammlungsstätten, etc.) |
| **Procedure** | How to get permission / who does what — different use case than "what rules apply" | §52–§86 |

You can still include **Low** or **Procedure** sections in the graph and tag them (e.g. node type or metadata) so the product can say "this applies to Sonderbauten" or "this is about the approval process."

---

## §31 — Decken

**Residential:** Core (floors/ceilings in every building).

**Structure:**
- **Abs. 1:** 1.1 → section. 1.2 "Sie müssen" = lead; 1.3–1.5 `sub_item_of` 1.2 (GK 5 feuerbeständig, GK 4 hochfeuerhemmend, GK 2+3 feuerhemmend). 1.6 "Satz 2 gilt" = textual anchor; 1.7, 1.8 **exception_of** 1.2 (Dachraum; Balkone — excluded from Satz 2).
- **Abs. 2:** 2.1 "Im Kellergeschoss müssen Decken" = lead; 2.2–2.3 `sub_item_of` 2.1 (GK 3–5 / GK 1–2). 2.4 "Decken müssen feuerbeständig sein" = second lead; 2.5, 2.6 `sub_item_of` 2.4 (Explosions-/Brandgefahr; landw./Wohnteil).
- **Abs. 3–4:** 3.1, 4.1 → section; 4.2–4.4 as sub-items or conditions under 4.1 (Öffnungen zulässig when …).

**Cross-references:**
- 1.3 → §2 (3.6 GK 5); 1.4 → §2 (3.5 GK 4); 1.5 → §2 (3.2, 3.3, 3.4 GK 2+3). 1.7 → §29 Abs. 4 if we want.
- 2.2, 2.3 → §2 (GK 3–5, 1–2). 2.5 → §2 (Wohngebäude GK 1+2 exception).
- 4.2 → §2 (GK 1+2); 4.3, 4.4 → section or keep as conditions.

---

## §32 — Dächer

**Residential:** Core.

**Structure:**
- **Abs. 1:** 1.1 → section (harte Bedachung).
- **Abs. 2:** 2.1 = "weiche Bedachung zulässig bei GK 1–3 wenn …" (lead); 2.2–2.5 `sub_item_of` 2.1 (Abstände 12 m, 15 m, 24 m, 5 m). 2.6 "Soweit … genügt bei Wohngebäuden GK 1 und 2" = textual anchor; 2.7–2.9 **exception_of** 2.1 (reduced distances for these cases). **NOTE: 2.1 connects back to Gebaudeklasse nodes in §2.**
- **Abs. 3:** 3.1 "Abs. 1 und 2 gelten nicht für" (textual anchor). 3.2–3.6 are **exclusions of** the rules they refer to: each → `exception_of` 1.1 and 2.1 (so the graph says "this case is excluded from hard roof / distance rules"). Optionally 3.2–3.6 `sub_item_of` 3.1 to keep list structure.
- **Abs. 4:** 4.1 = "Abweichend … zulässig" (lead); 4.2, 4.3 `sub_item_of` 4.1 (lichtdurchlässig, begrünt).
- **Abs. 5:** 5.1 → section; 5.2 = lead "Abstände von Brandwänden"; 5.3–5.5 `sub_item_of` 5.2.
- **Abs. 6–8:** 6.1, 6.2; 7.1, 7.2; 8.1 → section. 7.2 "gilt nicht für … Wohngebäude GK 1 bis …" → exception + reference §2.

**Cross-references:**
- 2.1, 2.6 → §2 (3.2, 3.3, 3.4 GK 1–3). 3.2–3.6 → section (exceptions).
- 5.2–5.5 → §30 (Brandwände / Wände anstelle von Brandwänden).
- 7.2 → §2 (GK 1–3).

---

## §33 — Erster und zweiter Rettungsweg

**Residential:** Core (every dwelling needs escape routes).

**Structure:**
- **Abs. 1:** 1.1 → section (two Rettungswege); 1.2 → 1.1 `exception_of` (eingeschossig zu ebener Erde).
- **Abs. 2:** 2.1, 2.2, 2.3 → section (erster Weg Treppe; zweiter Weg; Sicherheitstreppenraum).
- **Abs. 3:** 3.1, 3.2 → section (Feuerwehr Rettungsgeräte; Sonderbauten).

**Cross-references:**
- 3.2 → §51 (Sonderbauten) if in graph.

---

## §34 — Treppen

**Residential:** Core.

**Structure:**
- **Abs. 1:** 1.1, 1.2 → section.
- **Abs. 2:** 2.1 → section; 2.2 → 2.1 `exception_of` (einschiebbare Treppen/Leitern in GK 1+2 für Dachraum).
- **Abs. 3:** 3.1 → section; 3.2 "Dies gilt nicht" = exception lead; 3.3, 3.4 `sub_item_of` 3.2 (GK 1–3; §35 Abs. 1 Satz 3 Nr. …). **NOTE: Lets use a proper exception here, towards 3.1**
- **Abs. 4–7:** 4.1 = lead; 4.2–4.5 `sub_item_of` 4.1. 5.1, 6.1, 6.2, 7.1 → section. 4.5 → §35 (Außentreppen).

**Cross-references:**
- 2.2, 3.3 → §2 (3.2, 3.3 GK 1+2; 3.2–3.4 GK 1–3). 4.2–4.4, 4.5 → §2 (GK 5, 4, 3). 3.4 → §35.

---

## §35 — Notwendige Treppenräume, Ausgänge

**Residential:** Core.

**Structure:**
- **Abs. 1:** 1.1, 1.2 → section; 1.3 "ohne eigenen Treppenraum zulässig" = exception lead; 1.4–1.6 `sub_item_of` 1.3.
- **Abs. 2–3:** 2.1–2.3; 3.1, 3.2 lead + 3.3–3.6 `sub_item_of` 3.2.
- **Abs. 4:** 4.1 = lead (Wände Treppenräume); 4.2–4.6 `sub_item_of` 4.1.
- **Abs. 5–8:** Each paragraph: first node → section; any "Satz 2 Nr. 1/2" or list → sub_item_of first node. 6.1 = lead; 6.2–6.5 `sub_item_of` 6.1. 8.2 = lead; 8.3–8.6 `sub_item_of` 8.2.

**Cross-references:**
- 1.4 → §2 (GK 1+2). 4.2–4.4 → §2 (GK 5, 4, 3). 7.2 "Höhe nach § 2 Abs. 3 Satz 2" → §2.

---

## §36 — Notwendige Flure, offene Gänge

**Residential:** Core (especially multi-unit / apartment).

**Structure:**
- **Abs. 1:** 1.1 → section; 1.2 "Notwendige Flure sind nicht erforderlich" = exception lead; 1.3–1.6 `sub_item_of` 1.2.
- **Abs. 2–5:** 2.1, 2.2; 3.1–3.5 (3.5 "gelten nicht für offene Gänge nach Absatz …"); 4.1 lead, 4.2–4.4; 5.1, 5.2.
- **Abs. 6:** 6.1 = lead; 6.2, 6.3 `sub_item_of` 6.1.

**Cross-references:**
- 1.3, 1.4 → §2 (GK 1+2). 1.6 → §29 Abs. 2 Nr. 1, §33 Abs. 1. 3.5 → Abs. 4 (offene Gänge).

---

## §37 — Fenster, Türen, sonstige Öffnungen

**Residential:** Core.

**Structure:** Mostly one node per Absatz (1.1; 2.1, 2.2; 3.1; 4.1, 4.2; 5.1, 5.2) → section. 2.2 `sub_item_of` 2.1 if desired.

**Cross-references:**
- 3.1 (Eingangstüren Wohnungen, Aufzüge) → §39.
- 5.1, 5.2 → §33 Abs. 2 Satz 2 (Rettungswege).

---

## §38 — Umwehrungen

**Residential:** Core (balconies, stairs, roof access).

**Structure:**
- **Abs. 1:** 1.1 = "sind zu umwehren …" (lead); 1.2–1.8 `sub_item_of` 1.1 (Flächen, Oberlichte, Dächer, Öffnungen, Treppen, Kellerlichtschächte).
- **Abs. 2–4:** 2.1–2.3; 3.1, 3.2; 4.1 = lead, 4.2–4.3 `sub_item_of` 4.1.

---

## §39 — Aufzüge

**Residential:** Secondary. (Apartment owner may want to know rules; they don’t usually build the elevator.)

**Structure:**
- **Abs. 1:** 1.1, 1.2 → section; 1.3 "Aufzüge ohne eigene Fahrschächte sind zulässig" = exception lead; 1.4–1.7 `sub_item_of` 1.3.
- **Abs. 2–5:** 2.1 = lead, 2.2–2.5 `sub_item_of` 2.1. 3.1–3.3; 4.1–4.4 (4.1 "Höhe nach § 2 Abs. 3 Satz 2"); 5.1–5.3.

**Cross-references:**
- 1.4 → §35 (notwendiger Treppenraum). 1.7 → §2 (GK 1+2). 2.2–2.4 → §2 (GK 5, 4, 3). 4.1 → §2.

---

## §40 — Leitungsanlagen, Installationsschächte und -kanäle

**Residential:** Secondary (within apartment/house).

**Structure:**
- **Abs. 1:** 1.1 = main rule; 1.2–1.4 "dies gilt nicht" → 1.2–1.4 **exception_of** 1.1 (these cases excluded from the rule).
- **Abs. 2–3:** 2.1; 3.1 → §41.

**Cross-references:**
- 1.2 → §2 (GK 1+2). 2.1 → §35 (Treppenräume, Räume nach §35 Abs. 3 Satz 2), §36 (Flure). 3.1 → §41.

---

## §41 — Lüftungsanlagen

**Residential:** Secondary.

**Structure:** 1.1; 2.1, 2.2; 3.1; 4.1–4.3; 5.1 = textual anchor "Abs. 2 und 3 gelten nicht"; 5.2–5.4 **exception_of** 2.1 (and 3.1 if applicable); 6.1.

**Cross-references:**
- 5.2 → §2 (GK 1+2). 3.1 (Installationsschächte) → §41 Abs. 2 Satz 1, Abs. 3.

---

## §42 — Feuerungsanlagen, Wärmeerzeugung

**Residential:** Secondary (heating in house/apartment).

**Structure:** 1.1; 2.1; 3.1 lead, 3.2–3.4 (3.4 exception); 4.1, 4.2; 5.1.

---

## §43 — Sanitäre Anlagen, Wasserzähler

**Residential:** Core (Wohnung: Bad, Toilette; water meter).

**Structure:** 1.1; 2.1 → section, 2.2 → 2.1 `exception_of`.

---

## §44 — Kleinkläranlagen, Gruben

**Residential:** Secondary (house without public sewer).

**Structure:** 1.1 = lead (Kleinkläranlagen, Gruben); 1.2–1.6 `sub_item_of` 1.1.

---

## §45 — Aufbewahrung fester Abfallstoffe

**Residential:** Secondary (waste in building).

**Structure:** 1.1 = "dürfen … nur, wenn" (lead); 1.2–1.5 `sub_item_of` 1.1 (Trennwände/Decken, Öffnungen, Entleerung, Lüftung).

**Cross-references:** 1.1 "Gebäudeklassen 3 bis 5" → §2.

---

## §46 — Blitzschutzanlagen

**Residential:** Secondary (house/apartment building may need lightning protection).

**Structure:** 1.1 → section.

---

## §47 — Aufenthaltsräume

**Residential:** Core.

**Structure:**
- **Abs. 1:** 1.1, 1.2 → section; 1.3 "Sätze 1 und 2 gelten nicht für … Wohngebäude GK 1 und" → exception, reference §2.
- **Abs. 2–3:** 2.1, 2.2; 3.1.

**Cross-references:** 1.3 → §2 (3.2, 3.3 GK 1+2).

---

## §48 — Wohnungen

**Residential:** Core.

**Structure:** 1.1, 1.2; 2.1; 3.1; 4.1, 4.2; 5.1 → section. 5.1 "§§ 6, 27, 28, 30, 31 und 32 nicht anzuwenden" = references.

**Cross-references:** 5.1 → §6, §27, §28, §30, §31, §32 (Umbau/Nutzungsänderung).

---

## §49 — Stellplätze, Garagen, Fahrräder

**Residential:** Core (obligation and exceptions).

**Structure:** 1.1 → section; 1.2 → 1.1 `exception_of`. 2.1 = lead; 2.2, 2.3 `sub_item_of` 2.1.

**Cross-references:** 1.1 → §86 Abs. 1 Nr. 4 (if in graph).

---

## §50 — Barrierefreies Bauen

**Residential:** Core for multi-unit (one Geschoss barrierefrei); Abs. 2 is public/buildings (schools, etc.) = partly Low for pure "house/apartment" use.

**Structure:**
- **Abs. 1:** 1.1, 1.2 → section; 1.3 "Sätze 1 und 2 gelten nicht …" → exception (Dachausbau, Aufstockung, Teilung).
- **Abs. 2:** 2.1 → section; 2.2 "Dies gilt insbesondere für" = lead; 2.3–2.10 `sub_item_of` 2.2 (Kultur, Sport, Gesundheit, Büro, Verkauf, Stellplätze, Toiletten).
- **Abs. 3–4:** 3.1; 4.1 = lead (Abweichungen §67); 4.2–4.5 `sub_item_of` 4.1.

**Cross-references:** 1.2 → §39 Abs. 4. 4.1 → §67.

---

## §51 — Sonderbauten

**Residential:** Low (schools, Versammlungsstätten, care facilities — not typical apartment/house).

**Structure:** 1.1 "Sonderbauten"; 1.2, 1.3 → section; 1.4 "können sich erstrecken auf" = lead; 1.5–1.27 `sub_item_of` 1.4 (long list: Grundstück, Abstände, Brandschutz, Aufzüge, Treppen, Flure, Rettungswege, etc.).

**Cross-references:** 1.2 → §3 Abs. 1. §33 Abs. 3.2 references Sonderbauten → §51.

---

## §52–§86 (Procedure, authorities, approval)

**Residential:** Procedure use case (how to get permission, who is responsible, Bauantrag, Genehmigung, etc.). Still useful in graph for "what do I need to submit" or "who is the Bauherr."

Suggested approach:
- **Include** in graph with clear node types (e.g. `genehmigungspflicht`, `bauantrag`, `behoerdenstruktur`) so the product can distinguish "material building rules" vs "procedure."
- **§67 Abweichungen** is often cited (e.g. §50 Abs. 4) → add and link.
- **§86 Örtliche Bauvorschriften** is cited in §6, §49 → add and link.

Sections to prioritise for cross-refs: §65 (Bauvorlageberechtigung), §66 (Nachweise), §67 (Abweichungen), §68–§69 (Bauantrag), §72 (Baugenehmigung, Baubeginn), §77 (Zustimmung), §86 (örtliche Bauvorschriften).

---

## Intersectional relations summary

| From section | To section(s) | Relation / content |
|--------------|----------------|--------------------|
| §31 | §2 | GK 2–5 (fire resistance of ceilings) |
| §32 | §2, §30 | GK 1–3; distances from Brandwände |
| §33 | §51 | Sonderbauten (second Rettungsweg) |
| §34 | §2, §35 | GK 1–3; Außentreppen §35 |
| §35 | §2 | GK 3–5 (Treppenraum walls); Höhe §2 Abs. 3 |
| §36 | §2, §29, §33 | GK 1+2; Trennwände §29; Rettungswege §33 |
| §37 | §33, §39 | Rettungsweg fenster; Aufzüge |
| §39 | §2, §35 | GK 1–5; Treppenraum |
| §40 | §2, §35, §36, §41 | GK 1+2; Treppenraum, Flure; §41 |
| §41 | §2 | GK 1+2 exceptions |
| §45 | §2 | GK 3–5 |
| §47 | §2 | GK 1+2 exception |
| §48 | §6, §27, §28, §30, §31, §32 | Nutzungsänderung: these sections not applied |
| §49 | §86 | Stellplätze §86 Abs. 1 Nr. 4 |
| §50 | §39, §67 | Aufzug; Abweichungen |
| §51 | §3 | Allgemeine Anforderungen §3 Abs. 1 |

---

## Implementation notes

1. **Schema:** Ensure node types exist for new section anchors (e.g. `decke`, `dach`, `treppe`, `treppenraum`, `notwendiger_flur`, `fensteroffnung`, `umwehrung`, `aufzugsanlage`, etc.). Many already exist in `schema.py`.
2. **Large wall node:** Optional meta-node (e.g. "Bauteile: Wände") that §27, §28, §29, §30 all `supplements` can be added later without changing section logic.
3. **Batch implementation:** After you edit this plan (relationships, relevance, or skip certain sections), implement by:
   - Adding section numbers to `_SECTIONS` and `_SECTION_ANCHORS` in `build_graph.py`,
   - Adding one function per section in `mbo_section_edges.py` following the patterns above,
   - Calling all new functions in `edges()`.
4. **Residential filter:** If you want to hide or downrank "Low" or "Procedure" sections for a pure residential flow, add a node or edge metadata field (e.g. `residential_relevance: core | secondary | low | procedure`) and filter at query/UI layer.

---

*End of plan. Edit this document with your relationship changes, then implement in batch.*
