# LBO–MBO Matching — Proposal (editable before implementation)

This document proposes how to match **Landesbauordnungen (LBO)** — here **BayBO** (Bavarian Building Code) — to the **MBO** (Musterbauordnung) in the Propra knowledge graph. You can edit the mapping table, relation types, and representation choices below; implementation will follow your approved version.

---

## 1. Legal reality: LBO is the law (MBO is not citable)

**In every German state, only the state’s LBO is binding law.** The MBO (Musterbauordnung) is a **model** agreed by the building ministers’ conference; it is **not** a federal law and **cannot be cited** as legal authority. Each state adopts its own Bauordnung (LBO), often based on the MBO’s structure and wording, but the **citable source** is always the LBO (e.g. BayBO in Bavaria).

So for the product:

- **We must never cite MBO** to the user as the legal basis.
- **We cite only the LBO** (e.g. “Art. 31 BayBO”, “§ 33 LBO BW”) for the user’s state.
- **MBO’s role in the graph** is **organizational**: a stable, shared “map” of topics (Rettungsweg, Brandwände, etc.) so we can find the right rule and then surface the **LBO** as the authority.

---

## 2. Purpose

- **User need:** For a topic (e.g. Rettungswege), show the **rule that actually applies** in the user’s state — i.e. the **LBO** (e.g. Art. 31 BayBO), with correct citation.
- **Product:** We use the **MBO structure only internally** (to know “this is the Rettungsweg topic” and to map between states). The answer we show and cite is always the **LBO**.

---

## 3. Scope

- **LBO in scope:** BayBO (Bayerische Bauordnung) — `BayBO_.md` / `BayBO_.rtf`.
- **MBO:** Already in graph (§1–§86, node inventory + section edges). Used **only as internal structure**, not as a citable source.
- **Matching level (proposal):** **Section/Article level** first (e.g. Art. 31 BayBO ↔ §33 MBO). Paragraph-level (Abs./Satz) can be added later if needed.

---

## 4. Graph structure overview (how it all fits together)

Given that **LBO reigns supreme** for citation, the structure below makes "LBO = authority" explicit and uses MBO only as the shared map.

### Two roles (not two "authorities")

| Role | What it is | How we use it |
|------|------------|----------------|
| **LBO (e.g. BayBO)** | **The actual law** in that state. This is what we **cite** to the user. | Primary: we surface LBO section anchors (and later content) as the legal source. |
| **MBO** | **Not law.** A common template/structure. Section anchors + content nodes encode "what topics exist" and how they relate. | **Internal only:** we use MBO to *find* the right topic (e.g. Rettungsweg) and to map "in Bayern that topic = Art. 31". We never cite MBO. |

So: **one graph**. MBO is the **backbone** (stable taxonomy + rich content for reasoning). LBO is the **citable layer** (section anchors that we show and cite). The edge LBO → MBO means "this LBO article is the state's rule for *this* MBO topic" — it does **not** mean MBO is the authority.

### Shape of the graph (one topic: Rettungsweg)

```
   ┌─────────────────┐
   │  BayBO_Art31    │  ← **CITABLE** (the law in Bayern). Product shows & cites this.
   │  (LBO anchor)    │
   └────────┬────────┘
            │ state_version_of / template_for
            ▼
   ┌─────────────────┐
   │   MBO_§33       │  ← **NOT CITED**. Internal: "this is the Rettungsweg topic".
   │   (backbone)     │     Used to organize and to map to other states.
   └────────┬────────┘
            │ supplements, sub_item_of, references, …
            ▼
   MBO_§33_1.1, MBO_§33_2.1, …  (MBO content: structure & logic, still not cited)
```

**Query flow in practice:**

1. User in Bayern asks about Rettungswege.
2. We use the **MBO backbone** to know "Rettungsweg = MBO_§33" (and its content nodes for logic).
3. We follow the edge to **BayBO_Art31** and surface **Art. 31 BayBO** as the **citation** and the legal source. MBO stays internal.

### Design choices

| Choice | Option A | Option B (proposal) | Option C |
|--------|----------|----------------------|----------|
| **LBO in graph?** | No LBO nodes; only a mapping file. | LBO **section anchors only**; edges to MBO (backbone). | Full LBO: anchors + content nodes. |
| **Query "what applies in Bayern for Rettungsweg?"** | App uses mapping + MBO graph; cites BayBO Art. 31 from mapping. | Use MBO_§33 as topic; follow edge to BayBO_Art31; **cite Art. 31 BayBO**. | Same, plus optional BayBO paragraph-level content. |
| **Who "reigns supreme" in the model?** | LBO (we cite it); MBO is just structure. | **LBO = citable layer**; MBO = backbone. Product always cites LBO. | Same. |

**Recommendation:** **Option B** — LBO section anchors as the **citable layer**, linked to MBO as the **organizational backbone**. The product never shows MBO as a legal source; it uses MBO to navigate and then presents the LBO.

### Summary

- **LBO = law** (cite only LBO). **MBO = template** (internal structure, not citable).
- **One relation** LBO → MBO: e.g. `state_version_of` or `template_for` ("this LBO article is the state's version of this MBO topic").
- **Mapping table** = (BayBO Art., MBO §); build turns it into LBO nodes + edges to MBO. When answering, we **always cite the LBO**.


---

## 5. Representation options (choose one or hybrid)

| Option | Description | Pros | Cons |
|--------|-------------|------|------|
| **A. Edges in graph** | Add BayBO **section anchor nodes** (e.g. `BayBO_Art31`) and edges to MBO section anchors (e.g. `MBO_§33`) with a relation like `implements` or `state_version_of`. | Single source of truth; graph queries return “MBO §33 → BayBO Art. 31”. | Requires adding LBO nodes (and possibly full LBO inventory later). |
| **B. Mapping file only** | Keep a separate file (e.g. `lbo_mbo_mapping.yaml` or table in this MD) mapping Art. ↔ §. No LBO nodes in graph. | No graph change; simple to edit. | Product must join mapping + graph at query time; no unified traversal. |
| **C. Hybrid** | Mapping file as source of truth; build edges from it when building the graph (so graph contains the links, but mapping remains the editable artifact). | Editable mapping + graph stays consistent. | Two artifacts to keep in sync (mapping file + graph build that reads it). |

**Proposal:** **C (Hybrid).** Store the canonical mapping in a structured file (e.g. `data/lbo_mbo_mapping_baybo.yaml` or a table in `docs/`). The graph build script reads this and adds **section-level** LBO anchor nodes + edges to the corresponding MBO section nodes. So: you edit the mapping; implementation turns it into nodes/edges.

---

## 6. Relation type (LBO → MBO)

| Relation | Direction | Meaning |
|----------|-----------|--------|
| **`state_version_of`** | LBO section → MBO section | “This LBO article is the Bavarian implementation of this MBO section.” |

(Already present in schema/conventions for “state version of federal”.)

- **Reverse query:** “Which MBO section does BayBO Art. 31 implement?” → follow `state_version_of` from `BayBO_Art31` to `MBO_§33`.
- **Forward query:** “Which LBO articles implement MBO §33?” → follow inverse of `state_version_of` from `MBO_§33` to `BayBO_Art31`.

**Optional:** If we want to distinguish “exact transpose” vs “Bavaria-specific extension”, we could add a second relation (e.g. `extends`) for articles like Art. 44a, 61a, 62a, 66a, 73a, 80a, 81a, 82–82c. For the first version, **one relation `state_version_of`** is enough; “Bavaria-specific” can be marked in the mapping table (see below).

---

## 7. BayBO ↔ MBO mapping table

Below: **BayBO Art.** → **MBO §** (and short title).  
**Edit this table** to correct or add mappings.  
Use `—` if there is no MBO equivalent; use `(e.g. §X)` or a note in the “Notes” column for partial / conceptual overlap.

| BayBO Art. | BayBO title (short) | MBO § | MBO title (short) | Notes |
|------------|---------------------|-------|--------------------|-------|
| 1 | Anwendungsbereich | 1 | Anwendungsbereich | |
| 2 | Begriffe | 2 | Begriffe | |
| 3 | Allgemeine Anforderungen | 3 | Allgemeine Anforderungen | |
| 4 | Bebauung der Grundstücke | 4 | Bebauung der Grundstücke | |
| 5 | Zugänge, Zufahrten | 5 | Zugänge, Zufahrten | |
| 6 | Abstandsflächen, Abstände | 6 | Abstandsflächen, Abstände | |
| 7 | Begrünung | 8 | Nicht überbaute Flächen | MBO §7 = Teilung; BayBO Begrünung often aligned with green/open space |
| 8 | Baugestaltung | 9 | Gestaltung | |
| 9 | Baustelle | 11 | Baustelle | MBO §10 = Außenwerbung |
| 10 | Standsicherheit | 12 | Standsicherheit | |
| 11 | Schutz gegen Einwirkungen | 13 | Schutz gegen schädliche Einflüsse | |
| 12 | Brandschutz | 14 | Brandschutz | |
| 13 | Wärme-, Schall-, Erschütterungsschutz | 15 | Wärme-, Schall-, Erschütterungsschutz | |
| 14 | Verkehrssicherheit | 16 | Verkehrssicherheit | |
| 15 | Bauarten | 16a | Bauarten | |
| 16 | Verwendung von Bauprodukten | 16b, 16c | Bauprodukte | |
| 17 | Verwendbarkeitsnachweise | 17 | Verwendbarkeitsnachweise | |
| 18 | Allgemeine bauaufsichtliche Zulassung | 18 | Allgemeine bauaufsichtliche Zulassung | |
| 19 | Allgemeines bauaufsichtliches Prüfzeugnis | 19 | Allgemeines bauaufsichtliches Prüfzeugnis | |
| 20 | Zustimmung im Einzelfall | 20 | Nachweis Verwendbarkeit im Einzelfall | |
| 21 | Übereinstimmungserklärung, Zertifizierung | 21, 22, 23 | Übereinstimmung, Zertifizierung | One Art. vs three §§ |
| 22 | Sachkunde- und Sorgfaltsanforderungen | 25 | Sachkunde- und Sorgfaltsanforderungen | |
| 23 | Zuständigkeiten | 24 | Prüf-, Zertifizierungsstellen | Procedure / competencies |
| 24 | Brandverhalten Baustoffe/Bauteile | 26 | Brandverhalten | |
| 25 | Tragende Wände, Stützen | 27 | Tragende Wände, Stützen | |
| 26 | Außenwände | 28 | Außenwände | |
| 27 | Trennwände | 29 | Trennwände | |
| 28 | Brandwände | 30 | Brandwände | |
| 29 | Decken | 31 | Decken | |
| 30 | Dächer | 32 | Dächer | |
| 31 | Rettungswege | 33 | Rettungsweg | |
| 32 | Treppen | 34 | Treppen | |
| 33 | Notwendige Treppenräume, Ausgänge | 35 | Notwendige Treppenräume, Ausgänge | |
| 34 | Notwendige Flure, offene Gänge | 36 | Notwendige Flure | |
| 35 | Fenster, Türen, Öffnungen | 37 | Fenster, Türen, Öffnungen | |
| 36 | Umwehrungen | 38 | Umwehrungen | |
| 37 | Aufzüge | 39 | Aufzüge | |
| 38 | Leitungsanlagen, Installationsschächte | 40 | Leitungsanlagen | |
| 39 | Lüftungsanlagen | 41 | Lüftungsanlagen | |
| 40 | Feuerungsanlagen, Wärmeerzeugung | 42 | Feuerungsanlagen | |
| 41 | Nicht durch Sammelkanalisation erschlossen | 44 | Kleinkläranlagen, Gruben | |
| 42 | Sanitäre Anlagen | 43 | Sanitäre Anlagen | |
| 43 | Aufbewahrung fester Abfallstoffe | 45 | Aufbewahrung fester Abfallstoffe | |
| 44 | Blitzschutzanlagen | 46 | Blitzschutzanlagen | |
| 44a | Solaranlagen | — | — | **Bavaria-specific**; may reference §6, §32 |
| 45 | Aufenthaltsräume | 47 | Aufenthaltsräume | |
| 46 | Wohnungen | 48 | Wohnungen | |
| 47 | Stellplätze, Verordnungsermächtigung | 49 | Stellplätze, Garagen, Fahrräder | |
| 48 | Barrierefreies Bauen | 50 | Barrierefreies Bauen | |
| (Sonderbauten) | — | 51 | Sonderbauten | BayBO may regulate in other Arts or ordinances |
| 49 | Grundpflichten | 52 | Grundpflichten | |
| 50 | Bauherr | 53 | Bauherr | |
| 51 | Entwurfsverfasser | 54 | Entwurfsverfasser | |
| 52 | Unternehmer | 55 | Unternehmer | MBO has also §56 Bauleiter |
| 53 | Aufbau und Zuständigkeit Behörden | 57 | Aufbau und Zuständigkeit | |
| 54 | Aufgaben und Befugnisse Behörden | 58 | Aufgaben und Befugnisse | |
| 55 | Grundsatz | 59 | Grundsatz | |
| 56 | Vorrang anderer Gestattungsverfahren | 60 | Vorrang anderer Gestattungsverfahren | |
| 57 | Verfahrensfreie Bauvorhaben | 61 | Verfahrensfreie Bauvorhaben | |
| 58 | Genehmigungsfreistellung | 62 | Genehmigungsfreistellung | |
| 59 | Vereinfachtes Baugenehmigungsverfahren | 63 | Vereinfachtes Verfahren | |
| 60 | Baugenehmigungsverfahren | 64 | Baugenehmigungsverfahren | |
| 61 | Bauvorlageberechtigung | 65 | Bauvorlageberechtigung | |
| 61a | Bauvorlageberechtigung Staatsangehörige anderer Staaten | — | — | **Bavaria-specific** |
| 61b | Bauvorlageberechtigung auswärtige Dienstleister | — | — | **Bavaria-specific** |
| 62 | Bautechnische Nachweise | 66 | Bautechnische Nachweise | |
| 62a | Standsicherheitsnachweis | — | — | **Bavaria-specific** (detail of Art. 62) |
| 62b | Brandschutznachweis | — | — | **Bavaria-specific** (detail of Art. 62) |
| 63 | Abweichungen | 67 | Abweichungen | |
| 64 | Bauantrag, Bauvorlagen | 68 | Bauantrag, Bauvorlagen | |
| 65 | Behandlung des Bauantrags | 69 | Behandlung des Bauantrags | |
| 66 | Beteiligung des Nachbarn | 70 | Beteiligung Nachbarn/Öffentlichkeit | |
| 66a | Beteiligung der Öffentlichkeit | — | — | **Bavaria-specific** (split from MBO §70) |
| 67 | Ersetzung des gemeindlichen Einvernehmens | 71 | Ersetzung Einvernehmen | |
| 68 | Baugenehmigung, Genehmigungsfiktion, Baubeginn | 72 | Baugenehmigung, Baubeginn | |
| 69 | Geltungsdauer Baugenehmigung | 73 | Geltungsdauer | |
| 70 | Teilbaugenehmigung | 74 | Teilbaugenehmigung | |
| 71 | Vorbescheid | 75 | Vorbescheid | |
| 72 | Genehmigung fliegender Bauten | 76 | Fliegende Bauten | |
| 73 | Bauaufsichtliche Zustimmung | 77 | Bauaufsichtliche Zustimmung | |
| 73a | Typengenehmigung | — | — | **Bavaria-specific** |
| 74 | Verbot unrechtmäßig gekennzeichneter Bauprodukte | 78 | Verbot unrechtmäßig gekennzeichneter Bauprodukte | |
| 75 | Einstellung von Arbeiten | 79 | Einstellung von Arbeiten | |
| 76 | Beseitigung von Anlagen, Nutzungsuntersagung | 80 | Beseitigung, Nutzungsuntersagung | |
| 77 | Bauüberwachung | 81 | Bauüberwachung | |
| 78 | Bauzustandsanzeigen, Aufnahme der Nutzung | 82 | Bauzustandsanzeigen, Aufnahme Nutzung | |
| (Baulasten) | — | 83 | Baulasten, Baulastenverzeichnis | BayBO: check if in Art. 80 or elsewhere |
| 79 | Ordnungswidrigkeiten | 84 | Ordnungswidrigkeiten | |
| 80 | Rechtsverordnungen | 85 | Rechtsvorschriften | |
| 80a | Digitale Baugenehmigung, digitale Verfahren | — | — | **Bavaria-specific** |
| 81 | Örtliche Bauvorschriften | 86 | Örtliche Bauvorschriften | |
| 81a | Technische Baubestimmungen | — | — | **Bavaria-specific** (implementation detail) |
| 82 | Windenergie, Nutzungsänderung ehem. Militär | — | — | **Bavaria-specific** |
| 82a | Feste Abstandsvorschriften für Windenergie | — | — | **Bavaria-specific** |
| 82b | Windenergiegebiete | — | — | **Bavaria-specific** |
| 82c | Bau-Turbo | — | — | **Bavaria-specific** |
| 83 | Übergangsvorschriften | — | — | Schlussvorschriften (no direct §) |
| 84 | Inkrafttreten | — | — | Schlussvorschriften (no direct §) |

---

## 8. Node IDs and labels (for implementation)

If we add BayBO nodes (Option A or C), proposed convention:

- **Section anchor ID:** `BayBO_Art{N}` or `BayBO_Art{N}{suffix}` for 44a, 61a, 61b, 62a, 62b, 66a, 73a, 80a, 81a, 82a, 82b, 82c.
  - Examples: `BayBO_Art1`, `BayBO_Art44a`, `BayBO_Art61a`.
- **Label / title:** From BayBO (e.g. “Anwendungsbereich”, “Solaranlagen”).
- **Jurisdiction:** `DE-BY` (or `Bayern` as in your schema).
- **source_paragraph:** e.g. `Art. 31 BayBO` (or full citation as in MBO).

**MBO side:** Existing section anchors already have IDs like `MBO_§33` (or per your current naming). Edges: `BayBO_Art31 --[state_version_of]--> MBO_§33`.

---

## 9. Implementation steps (after you approve this doc)

1. **Freeze mapping:** You edit the table above (and optionally Option A/B/C, relation type).
2. **Export mapping:** Implementer turns the table into a machine-readable format (e.g. `data/lbo_mbo_mapping_baybo.yaml`: list of `lbo_art`, `mbo_paras`, `bavaria_specific`).
3. **Graph:**
   - Add BayBO section anchor nodes for each Art. in the mapping (or only those with an MBO §).
   - For each row with an MBO §, add edge `BayBO_Art{N} --[state_version_of]--> MBO_§{n}`.
4. **Optional:** Add a small query helper or API that, given MBO § or BayBO Art., returns the other (and optionally paragraph-level later).

---

## 10. Rethink: MBO as skeleton, full replication per state

This branch already has **multiple node inventories per state** (MBO, BayBO, BauO_LSA, BW_LBO, etc.). Each inventory has the same logical shape: §/Art → numbered rows (1.1, 1.2, 2.1, …). The open design question: should we only add **state section anchors** that point at MBO (current proposal), or **replicate the full relation structure** for each state using MBO as the skeleton?

### Two ways to use MBO

| Approach | What MBO is | What each state has | Query path |
|----------|-------------|----------------------|------------|
| **A. Backbone (current proposal)** | Full graph: section + content nodes, all relations (supplements, sub_item_of, exception_of, references). | Only **section anchors** per state; one edge type to MBO (`state_version_of`). | Topic → MBO (for structure/logic) → state anchor for **citation**. Content/details come from MBO (internal) or from state text elsewhere. |
| **B. Skeleton + replicate** | **Template**: MBO defines *how* relations work (relation types, conventions). Optionally keep MBO graph as reference. | **Full graph per state**: section + content nodes, same relation types. Edges follow the same rules as MBO (supplements, sub_item_of, exception_of, references) but between **state nodes only**. | User state → that state’s subgraph only. No MBO in the query path. Cite only state. |

### Would “match and replicate” be a proper solution?

**Yes.** If we:

1. **Use MBO as the skeleton** — i.e. the authority for *relation types* and *structural conventions* (e.g. list items `sub_item_of` lead sentence, exceptions `exception_of` base rule, cross-refs `references`).
2. **Match** state sections/paragraphs to MBO (e.g. BayBO Art. 31 ↔ MBO §33, and where possible paragraph-level).
3. **Replicate** for each state: build the same *edge structure* (same relation types) between that state’s nodes, so each state has its own self-contained subgraph with the same semantics.

then we get:

- **Legally correct:** We only ever cite the state LBO; the graph we traverse for “user in Bayern” is BayBO-only.
- **Same reasoning everywhere:** “What are the exceptions?” is answered by following `exception_of` in the state graph, just like in MBO.
- **Entrance is always state:** For a given user we filter by jurisdiction and only traverse that state’s nodes. MBO is not in the query path; it only defined the rules we used to build the state graph.

So: **MBO = skeleton (relation rules + optional reference graph); each state = full graph built with those rules. Query and citation = state only.** That is a consistent and “proper” solution.

### What it means in the real world

**Graph size**  
- **Larger:** We have MBO (if we keep it) + 16 state graphs (section + content nodes + edges). So many more nodes and edges overall.  
- **Per query:** We restrict by jurisdiction (e.g. `jurisdiction = DE-BY`). So we only load or traverse the BayBO subgraph — similar in size to one MBO-sized graph. So **query time** need not be worse if we index/filter by jurisdiction; we are not walking the whole graph.

**Updates**  
- **Per state:** When Bavaria amends BayBO, we update only BayBO nodes/edges. Other states and MBO are unchanged. So updates are **local** to one state.  
- **When MBO changes:** If we use MBO only as a “relation rulebook” and build state graphs by hand (or with state-specific edge logic), we don’t have to “re-replicate” from MBO. If we ever auto-generate state edges from MBO structure, then MBO changes would require a decision: re-run replication for affected states. In practice, **state graphs are maintained independently**; MBO is the initial template and the convention source, not the live source of truth for state edges.

**Inconsistencies**  
- **Content:** State laws diverge. BayBO Art. 31 might have 4 Absätze, MBO §33 might have 5; one state might add an exception another doesn’t have. So state graphs will **not** be identical in size or wording. That’s correct: we’re modeling 16 different laws.  
- **Schema:** Relation *types* and *meaning* stay the same (supplements, sub_item_of, exception_of, references). So we have **consistent semantics** across states; only the content and exact structure differ.

**Summary**  
- **Slower?** Not necessarily — filter by state and traverse one state subgraph.  
- **Messier to update?** Each state is updated on its own; no need to touch MBO when a state changes.  
- **Inconsistencies?** Yes in *content* (states differ); no in *schema* (same relation types and conventions). That’s the right trade-off.

### How this changes the proposal

If we adopt **skeleton + replicate**:

- **Mapping** (e.g. BayBO Art. ↔ MBO §) is still needed to know *which* state section corresponds to which MBO section (and to build or check state edges).
- We add **state-level edge logic** (like `mbo_section_edges.py` but for each state, or one parameterized builder that takes state inventory + section→MBO mapping and applies MBO-style relations).
- **State graphs** are self-contained: all edges are between nodes of that state. Optional: keep `state_version_of` from state section anchor → MBO section for cross-state comparison or tooling (“this is the Rettungsweg topic; in BY it’s Art. 31, in BW it’s §33”).
- **Product:** Entrance is always state. We never traverse MBO for the answer; we only cite state. MBO has defined how we built the state graph.

---

## 11. Your edits

- **Mapping table:** Change any cell in the table; add/remove rows for Arts or §§.
- **Representation:** If you prefer “mapping file only” (no LBO nodes in graph), say so and we drop node/edge creation.
- **Relation:** If you want a different relation name or an extra one (e.g. `extends` for Bavaria-specific), add it here.
- **Node IDs / jurisdiction:** Adjust the convention in §6 if needed.

Once you are done editing, we can implement accordingly.
