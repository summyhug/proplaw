"""
Section-by-section domain edges for the MBO knowledge graph.

We define edges per § so the graph encodes structure and meaning (e.g. list items
under a parent rule, exclusions from scope). The core of each § is a section node
(e.g. MBO_§1 = "§1 Anwendungsbereich"); content nodes (1.1, 1.2, 2.1, …) hang off it.

Labelling convention (verified for §1 and §2):
  - supplements: content block or lead sentence → section anchor (e.g. 1.1, 1.2, 2.1 → MBO_§1);
    or a sub-rule that adds to another rule (e.g. 3.7, 3.8 → 3.1).
  - sub_item_of: list item or sub-point → its parent rule (e.g. 2.2–2.12 → 2.1;
    1.2–1.11 → 1.1; 4.2–4.23 → 4.1).

§1 Anwendungsbereich:
  - Core node: MBO_§1 (section title "Anwendungsbereich").
  - 1.1, 1.2 (Abs. 1), 2.1 (Abs. 2 lead) → supplement MBO_§1.
  - 2.2–2.12 → sub_item_of 2.1 (exclusion list).
"""

from propra.graph.schema import Edge

_PREFIX = "MBO_"


def _n(para: str, row: str) -> str:
    """Node ID for MBO § para, row (e.g. §1, 2.1 → MBO_§1_2.1)."""
    return f"{_PREFIX}§{para}_{row}"


def _section_node(para: str) -> str:
    """Section anchor node id (e.g. §1 → MBO_§1)."""
    return f"{_PREFIX}§{para}"


def section_1_anwendungsbereich() -> list[Edge]:
    """
    §1 Anwendungsbereich: section node MBO_§1 is core; 1.1, 1.2, 2.1 under it; 2.2–2.12 under 2.1.
    """
    edges: list[Edge] = []
    section_anchor = _section_node("1")  # MBO_§1 = §1 Anwendungsbereich
    abs2_lead = _n("1", "2.1")

    # Abs. 1 lead and Abs. 2 block belong under the section (not under 1.1)
    for row_id in ("1.1", "1.2", "2.1"):
        edges.append(
            Edge(
                source=_n("1", row_id),
                target=section_anchor,
                relation="supplements",
                sourced_from="§1 MBO",
                metadata={"reasoning": "Content block under §1 Anwendungsbereich."},
            )
        )
    # List items 2.2–2.12 under 2.1
    for i in range(2, 13):
        edges.append(
            Edge(
                source=_n("1", f"2.{i}"),
                target=abs2_lead,
                relation="sub_item_of",
                sourced_from="§1 Abs. 2 MBO",
                metadata={
                    "reasoning": "List item under §1 Abs. 2: installation/use excluded from MBO scope.",
                },
            )
        )
    return edges


def section_2_begriffe() -> list[Edge]:
    """
    §2 Begriffe: section node MBO_§2 is core.
    - 1.1 (defines building); 1.2–1.11 under it (examples). 
    - 3.1 (Gebäudeklassen); 3.2–3.6 under it (classes); 3.7, 3.8 supplement 3.1–3.6 (→ 3.1).
    - 4.1 (Sonderbauten); 4.2–4.23 under it.
    - 5.1, 6.1, 7.1, 8.1, 9.1, 11.1 → MBO_§2. 6.2→6.1, 7.2–7.3→7.1.
    - 10.1 → MBO_§2; 10.2, 10.3 → 10.1.
    """
    edges: list[Edge] = []
    section = _section_node("2")  # MBO_§2 Begriffe

    # 1.1 = definition of Bauliche Anlagen; 1.2–1.11 = examples under it
    edges.append(Edge(_n("2", "1.1"), section, "supplements", "§2 Abs. 1 MBO", metadata={"reasoning": "Defines bauliche Anlagen (buildings)."}))
    # 2.1 = definition of Gebäude (building)
    edges.append(Edge(_n("2", "2.1"), section, "supplements", "§2 Abs. 2 MBO", metadata={"reasoning": "Defines Gebäude."}))
    for i in range(2, 12):  # 1.2 .. 1.11
        edges.append(Edge(_n("2", f"1.{i}"), _n("2", "1.1"), "sub_item_of", "§2 Abs. 1 MBO", metadata={"reasoning": "Example of bauliche Anlage under §2 Abs. 1."}))

    # 3.1 = Gebäudeklassen; 3.2–3.6 = classes (sub_item_of 3.1); 3.7, 3.8 supplement 3.1–3.6 → 3.1
    edges.append(Edge(_n("2", "3.1"), section, "supplements", "§2 Abs. 3 MBO", metadata={"reasoning": "Core: Gebäudeklassen."}))
    for i in range(2, 7):  # 3.2 .. 3.6
        edges.append(Edge(_n("2", f"3.{i}"), _n("2", "3.1"), "sub_item_of", "§2 Abs. 3 MBO", metadata={"reasoning": "Gebäudeklasse definition."}))
    for i in (7, 8):  # 3.7, 3.8 supplement 3.1–3.6
        edges.append(Edge(_n("2", f"3.{i}"), _n("2", "3.1"), "supplements", "§2 Abs. 3 MBO", metadata={"reasoning": "Höhe / Grundflächen — supplement to Gebäudeklassen."}))

    # 4.1 = Sonderbauten; 4.2–4.23 under it
    edges.append(Edge(_n("2", "4.1"), section, "supplements", "§2 Abs. 4 MBO", metadata={"reasoning": "Core: Sonderbauten definition."}))
    for i in range(2, 24):  # 4.2 .. 4.23
        edges.append(Edge(_n("2", f"4.{i}"), _n("2", "4.1"), "sub_item_of", "§2 Abs. 4 MBO", metadata={"reasoning": "Sonderbauten list item."}))

    # 5.1, 6.1, 7.1, 8.1, 9.1, 11.1 → section
    for row in ("5.1", "6.1", "7.1", "8.1", "9.1", "11.1"):
        edges.append(Edge(_n("2", row), section, "supplements", "§2 MBO", metadata={"reasoning": "Definition block under Begriffe."}))

    # 6.2 under 6.1; 7.2, 7.3 under 7.1
    edges.append(Edge(_n("2", "6.2"), _n("2", "6.1"), "sub_item_of", "§2 Abs. 6 MBO", metadata={"reasoning": "Continuation of Geschosse definition."}))
    for i in (2, 3):
        edges.append(Edge(_n("2", f"7.{i}"), _n("2", "7.1"), "sub_item_of", "§2 Abs. 7 MBO", metadata={"reasoning": "Garagen / Stellplätze sub-item."}))

    # 10.1 → section; 10.2, 10.3 → 10.1
    edges.append(Edge(_n("2", "10.1"), section, "supplements", "§2 Abs. 10 MBO", metadata={"reasoning": "Bauprodukte definition."}))
    edges.append(Edge(_n("2", "10.2"), _n("2", "10.1"), "sub_item_of", "§2 Abs. 10 MBO", metadata={"reasoning": "Bauprodukte list item."}))
    edges.append(Edge(_n("2", "10.3"), _n("2", "10.1"), "sub_item_of", "§2 Abs. 10 MBO", metadata={"reasoning": "Bauprodukte list item."}))

    # Cross-references (text cites another §/Absatz)
    edges.append(Edge(_n("2", "1.11"), _n("1", "1.2"), "references", "§2 Abs. 1 MBO", metadata={"reasoning": "Text: 'im Sinne des § 1 Abs. 1 Satz 2' — cites §1 Abs. 1 second sentence."}))
    edges.append(Edge(_n("2", "4.2"), _n("2", "3.7"), "references", "§2 Abs. 4 MBO", metadata={"reasoning": "Text: 'Höhe nach Absatz 3 Satz 2' — 3.7 defines Höhe."}))
    edges.append(Edge(_n("2", "10.2"), _n("3", "3.1"), "references", "§2 Abs. 10 MBO", metadata={"reasoning": "Text: 'Anforderungen nach § 3 Satz 1' — cites §3 core requirement."}))
    edges.append(Edge(_n("2", "10.3"), _n("3", "3.1"), "references", "§2 Abs. 10 MBO", metadata={"reasoning": "Text: 'Anforderungen nach § 3 Satz 1' — cites §3 core requirement."}))

    return edges


def section_3_allgemeine_anforderungen() -> list[Edge]:
    """
    §3 Allgemeine Anforderungen: section anchor MBO_§3; only one content node 3.1 (core requirement).
    """
    edges: list[Edge] = []
    section = _section_node("3")
    edges.append(
        Edge(
            source=_n("3", "3.1"),
            target=section,
            relation="supplements",
            sourced_from="§3 MBO",
            metadata={"reasoning": "§3 single sentence: general safety/order requirement for Anlagen."},
        )
    )
    return edges


def section_4_bebauung_grundstuecke() -> list[Edge]:
    """
    §4 Bebauung der Grundstücke mit Gebäuden: section anchor MBO_§4; Abs. 1 → 1.1, Abs. 2 → 2.1.
    """
    edges: list[Edge] = []
    section = _section_node("4")
    for row_id in ("1.1", "2.1"):
        edges.append(
            Edge(
                source=_n("4", row_id),
                target=section,
                relation="supplements",
                sourced_from="§4 MBO",
                metadata={"reasoning": "Content block under §4 Bebauung der Grundstücke."},
            )
        )
    return edges


def section_5_zugaenge_zufahrten() -> list[Edge]:
    """
    §5 Zugänge und Zufahrten: section anchor MBO_§5; Abs. 1 → 1.1 + 1.2–1.4 under 1.1; Abs. 2 → 2.1 + 2.2 under 2.1.
    """
    edges: list[Edge] = []
    section = _section_node("5")
    # Abs. 1 lead; 1.2–1.4 are follow-up sentences (Satz 2–4) under 1.1
    edges.append(Edge(_n("5", "1.1"), section, "supplements", "§5 Abs. 1 MBO", metadata={"reasoning": "Lead: Zu-/Durchgang zu rückwärtigen Gebäuden."}))
    for i in range(2, 5):
        edges.append(Edge(_n("5", f"1.{i}"), _n("5", "1.1"), "sub_item_of", "§5 Abs. 1 MBO", metadata={"reasoning": "Follow-up sentence under §5 Abs. 1."}))
    # Abs. 2 lead; 2.2 is Satz 2 under 2.1
    edges.append(Edge(_n("5", "2.1"), section, "supplements", "§5 Abs. 2 MBO", metadata={"reasoning": "Lead: Befestigung, Kennzeichnung, freihalten."}))
    edges.append(Edge(_n("5", "2.2"), _n("5", "2.1"), "sub_item_of", "§5 Abs. 2 MBO", metadata={"reasoning": "Fahrzeuge nicht abstellen (Satz 2)."}))
    return edges


def section_6_abstandsflaechen() -> list[Edge]:
    """
    §6 Abstandsflächen, Abstände — meaty section; structure and exceptions as per user guidance.

    Abs. 1: 1.1 = main rule (Abstandsflächen freizuhalten); 1.2 extends to other Anlagen; 1.3 exception to 1.2;
            1.4 = exception (nicht erforderlich); 1.5, 1.6 = the two cases under 1.4.
    Abs. 2: 2.1–2.3 all connect to §6 (where Abstandsflächen may lie).
    Abs. 3: 3.1 = main (no overlap); 3.2–3.4 = exceptions where overlap allowed; conditional under 6.
    Abs. 4: 4.1 = lead (Tiefe/Wandhöhe); 4.2–4.6 interconnected measurement chain under 4.1.
    Abs. 5: 5.1, 5.2 = default depths; 5.3 = exception for GK 1+2 (references §2 Gebäudeklassen); 5.4 = Satzung override.
    Abs. 6: 6.1 = exception holder (bleiben außer Betracht); 6.2–6.4 under 6.1.
    Abs. 7: 7.1 = main (Energie/Solar außer Betracht wenn); 7.2, 7.3 = conditions under 7.1.
    Abs. 8: 8.1 = what is zulässig in Abstandsflächen; 8.2–8.5 define those exceptions.
    """
    edges: list[Edge] = []
    section = _section_node("6")

    # --- Abs. 1 ---
    edges.append(Edge(_n("6", "1.1"), section, "supplements", "§6 Abs. 1 MBO", metadata={"reasoning": "Main rule: Abstandsflächen vor Außenwänden freizuhalten."}))
    edges.append(Edge(_n("6", "1.2"), _n("6", "1.1"), "supplements", "§6 Abs. 1 MBO", metadata={"reasoning": "Satz 1 gilt entsprechend für andere Anlagen."}))
    edges.append(Edge(_n("6", "1.3"), _n("6", "1.2"), "exception_of", "§6 Abs. 1 MBO", metadata={"reasoning": "Satz 2 gilt nicht für Antennen im Außenbereich."}))
    edges.append(Edge(_n("6", "1.4"), _n("6", "1.1"), "exception_of", "§6 Abs. 1 MBO", metadata={"reasoning": "Abstandsfläche nicht erforderlich vor Außenwänden (exception holder)."}))
    edges.append(Edge(_n("6", "1.5"), _n("6", "1.4"), "sub_item_of", "§6 Abs. 1 MBO", metadata={"reasoning": "Case: Grenzbebauung nach planungsrechtlichen Vorschriften."}))
    edges.append(Edge(_n("6", "1.6"), _n("6", "1.4"), "sub_item_of", "§6 Abs. 1 MBO", metadata={"reasoning": "Case: § 34 Abs. 1 BauGB abweichende Abstände."}))

    # --- Abs. 2: all to section ---
    for row in ("2.1", "2.2", "2.3"):
        edges.append(Edge(_n("6", row), section, "supplements", "§6 Abs. 2 MBO", metadata={"reasoning": "Where Abstandsflächen/Abstände may lie (Grundstück, Verkehrsflächen, andere Grundstücke)."}))

    # --- Abs. 3: 3.1 main; 3.2–3.4 exceptions (overlap allowed) ---
    edges.append(Edge(_n("6", "3.1"), section, "supplements", "§6 Abs. 3 MBO", metadata={"reasoning": "Abstandsflächen dürfen sich nicht überdecken; exceptions listed in 3.2–3.4."}))
    for i in range(2, 5):
        edges.append(Edge(_n("6", f"3.{i}"), _n("6", "3.1"), "sub_item_of", "§6 Abs. 3 MBO", metadata={"reasoning": "Exception: overlap allowed in this case."}))
    edges.append(Edge(_n("6", "3.3"), _n("2", "3.1"), "references", "§6 Abs. 3 MBO", metadata={"reasoning": "Text: Wohngebäuden der Gebäudeklassen 1 und 2 — cites §2 Gebäudeklassen."}))

    # --- Abs. 4: 4.1 lead; 4.2–4.6 measurement chain (interconnected under 4.1) ---
    edges.append(Edge(_n("6", "4.1"), section, "supplements", "§6 Abs. 4 MBO", metadata={"reasoning": "Tiefe der Abstandsfläche nach Wandhöhe (lead)."}))
    for i in range(2, 7):
        edges.append(Edge(_n("6", f"4.{i}"), _n("6", "4.1"), "sub_item_of", "§6 Abs. 4 MBO", metadata={"reasoning": "Measurement definition chain (Wandhöhe, Dach, H)."}))

    # --- Abs. 5: 5.1, 5.2 default; 5.3 exception for GK 1+2; 5.4 Satzung override ---
    edges.append(Edge(_n("6", "5.1"), section, "supplements", "§6 Abs. 5 MBO", metadata={"reasoning": "Default Tiefe 0,4 H, mind. 3 m."}))
    edges.append(Edge(_n("6", "5.2"), section, "supplements", "§6 Abs. 5 MBO", metadata={"reasoning": "Gewerbe/Industrie: 0,2 H, mind. 3 m."}))
    edges.append(Edge(_n("6", "5.3"), _n("6", "5.1"), "exception_of", "§6 Abs. 5 MBO", metadata={"reasoning": "Exception: Wohngebäude GK 1 und 2, max 3 Geschosse → 3 m genügt."}))
    edges.append(Edge(_n("6", "5.3"), _n("6", "5.2"), "exception_of", "§6 Abs. 5 MBO", metadata={"reasoning": "Same exception applies instead of 5.2 for these building types."}))
    edges.append(Edge(_n("6", "5.3"), _n("2", "3.1"), "references", "§6 Abs. 5 MBO", metadata={"reasoning": "Text: Gebäudeklassen 1 und 2 — cites §2 Abs. 3 Gebäudeklassen."}))
    edges.append(Edge(_n("6", "5.4"), section, "supplements", "§6 Abs. 5 MBO", metadata={"reasoning": "Satzung kann Sätze 1–3 überlagern (§ 86)."}))
    edges.append(Edge(_n("6", "5.4"), _section_node("86"), "references", "§6 Abs. 5 MBO", metadata={"reasoning": "Text: Satzung nach § 86."}))

    # --- Abs. 6: 6.1 exception holder; 6.2–6.4 under it ---
    edges.append(Edge(_n("6", "6.1"), section, "supplements", "§6 Abs. 6 MBO", metadata={"reasoning": "Bei Bemessung außer Betracht (exception holder)."}))
    for i in range(2, 5):
        edges.append(Edge(_n("6", f"6.{i}"), _n("6", "6.1"), "sub_item_of", "§6 Abs. 6 MBO", metadata={"reasoning": "Element that remains out of consideration."}))

    # --- Abs. 7: 7.1 main; 7.2, 7.3 conditions ---
    edges.append(Edge(_n("6", "7.1"), section, "supplements", "§6 Abs. 7 MBO", metadata={"reasoning": "Energieeinsparung/Solaranlagen außer Betracht wenn …"}))
    edges.append(Edge(_n("6", "7.2"), _n("6", "7.1"), "sub_item_of", "§6 Abs. 7 MBO", metadata={"reasoning": "Condition: Stärke ≤ 0,25 m."}))
    edges.append(Edge(_n("6", "7.3"), _n("6", "7.1"), "sub_item_of", "§6 Abs. 7 MBO", metadata={"reasoning": "Condition: 2,50 m von Nachbargrenze."}))

    # --- Abs. 8: 8.1 what is zulässig; 8.2–8.5 define exceptions ---
    edges.append(Edge(_n("6", "8.1"), section, "supplements", "§6 Abs. 8 MBO", metadata={"reasoning": "In Abstandsflächen zulässig (exception holder)."}))
    for i in range(2, 6):
        edges.append(Edge(_n("6", f"8.{i}"), _n("6", "8.1"), "sub_item_of", "§6 Abs. 8 MBO", metadata={"reasoning": "Definition of allowed structures in Abstandsflächen."}))

    return edges


def section_7_teilung_grundstuecke() -> list[Edge]:
    """
    §7 Teilung von Grundstücken: straightforward. Abs. 1 = 1.1 (no conflicting Verhältnisse);
    Abs. 2 = 2.1 (Abweichung → §67). Both supplement section.
    """
    edges: list[Edge] = []
    section = _section_node("7")
    edges.append(Edge(_n("7", "1.1"), section, "supplements", "§7 Abs. 1 MBO", metadata={"reasoning": "Teilung darf keine widersprechenden Verhältnisse schaffen."}))
    edges.append(Edge(_n("7", "2.1"), section, "supplements", "§7 Abs. 2 MBO", metadata={"reasoning": "Abweichung bei Teilung: § 67 entsprechend."}))
    edges.append(Edge(_n("7", "2.1"), _n("7", "1.1"), "references", "§7 Abs. 2 MBO", metadata={"reasoning": "Text: 'bei einer Teilung nach Absatz 1' — conditional on Abs. 1."}))
    return edges


def section_8_nicht_ueberbaute_flaechen() -> list[Edge]:
    """
    §8 Nicht überbaute Flächen, Kinderspielplätze. Conditionals handled explicitly.

    Abs. 1: 1.1 = lead (nicht überbaute Flächen sind …); 1.2, 1.3 = the two requirements
            (wasseraufnahmefähig; begrünen/bepflanzen) under 1.1. 1.4 = exception: Satz 1
            findet keine Anwendung when Bebauungspläne/Satzungen treffen Festsetzungen
            → exception_of 1.1.
    Abs. 2: 2.1 = main (Spielplatz bei >3 Wohnungen). 2.2 = "Dies gilt nicht, wenn …"
            (exception when other Spielplatz vorhanden or not erforderlich) → exception_of 2.1.
            2.3 = Bei bestehenden Gebäuden kann Herstellung verlangt werden → supplements 2.1.
    """
    edges: list[Edge] = []
    section = _section_node("8")

    # Abs. 1: lead + two requirements + exception
    edges.append(Edge(_n("8", "1.1"), section, "supplements", "§8 Abs. 1 MBO", metadata={"reasoning": "Lead: nicht überbaute Flächen sind … (two requirements in 1.2, 1.3)."}))
    edges.append(Edge(_n("8", "1.2"), _n("8", "1.1"), "sub_item_of", "§8 Abs. 1 MBO", metadata={"reasoning": "Requirement: wasseraufnahmefähig."}))
    edges.append(Edge(_n("8", "1.3"), _n("8", "1.1"), "sub_item_of", "§8 Abs. 1 MBO", metadata={"reasoning": "Requirement: begrünen/bepflanzen, soweit …"}))
    edges.append(Edge(_n("8", "1.4"), _n("8", "1.1"), "exception_of", "§8 Abs. 1 MBO", metadata={"reasoning": "Satz 1 findet keine Anwendung, soweit Bebauungspläne/Satzungen Festsetzungen treffen."}))

    # Abs. 2: main + exception + supplement for existing buildings
    edges.append(Edge(_n("8", "2.1"), section, "supplements", "§8 Abs. 2 MBO", metadata={"reasoning": "Spielplatz bei Gebäuden mit mehr als drei Wohnungen."}))
    edges.append(Edge(_n("8", "2.2"), _n("8", "2.1"), "exception_of", "§8 Abs. 2 MBO", metadata={"reasoning": "Dies gilt nicht, wenn … Gemeinschaftsanlage/vorhanden/nicht erforderlich."}))
    edges.append(Edge(_n("8", "2.3"), _n("8", "2.1"), "supplements", "§8 Abs. 2 MBO", metadata={"reasoning": "Bei bestehenden Gebäuden kann Herstellung verlangt werden."}))
    return edges


def section_9_gestaltung() -> list[Edge]:
    """
    §9 Gestaltung — design requirements (relevant for stores/facades).
    Abs. 1: 1.1 = heading "Gestaltung"; 1.2, 1.3 = two rules for bauliche Anlagen (Form/Farbe; Bild).
    References: both rules address "Bauliche Anlagen" → §2 definition.
    """
    edges: list[Edge] = []
    section = _section_node("9")
    edges.append(Edge(_n("9", "1.1"), section, "supplements", "§9 Abs. 1 MBO", metadata={"reasoning": "Heading: Gestaltung."}))
    edges.append(Edge(_n("9", "1.2"), section, "supplements", "§9 Abs. 1 MBO", metadata={"reasoning": "Bauliche Anlagen: Form, Maßstab, Werkstoff, Farbe — nicht verunstalten."}))
    edges.append(Edge(_n("9", "1.3"), section, "supplements", "§9 Abs. 1 MBO", metadata={"reasoning": "Bauliche Anlagen dürfen Straßen-/Orts-/Landschaftsbild nicht verunstalten."}))
    edges.append(Edge(_n("9", "1.2"), _n("2", "1.1"), "references", "§9 Abs. 1 MBO", metadata={"reasoning": "Text: 'Bauliche Anlagen' — cites §2 Abs. 1 definition."}))
    edges.append(Edge(_n("9", "1.3"), _n("2", "1.1"), "references", "§9 Abs. 1 MBO", metadata={"reasoning": "Text: 'Bauliche Anlagen' — cites §2 Abs. 1 definition."}))
    return edges


def section_10_aussenwerbung_warenautomaten() -> list[Edge]:
    """
    §10 Anlagen der Außenwerbung, Warenautomaten — stores/advertising (Werbeanlagen, Hinweisschilder, Stätte der Leistung).
    Abs. 1: Definition Werbeanlagen; 1.1 lead, 1.2 examples (sub_item_of 1.1).
    Abs. 2: 2.1 = if Werbeanlage is bauliche Anlage → MBO requirements apply; 2.2 = if not, different rule; 2.3 = Häufung.
    Abs. 3: 3.1 = outside built-up unzulässig; 3.2–3.7 exceptions (Stätte der Leistung, Hinweisschilder, etc.).
    Abs. 4: 4.1, 4.2 = restrictions in Wohngebieten (only Stätte der Leistung, Hinweisschilder).
    Abs. 5: 5.1 = Abs. 1–3 apply to Warenautomaten (references back to §10 rules).
    Abs. 6: 6.1 = exclusion holder; 6.2–6.5 = cases where MBO not applicable.
    References: 2.1 to §2 (bauliche Anlagen) and §3 (Anforderungen an bauliche Anlagen).
    """
    edges: list[Edge] = []
    section = _section_node("10")

    # Abs. 1: definition + examples
    edges.append(Edge(_n("10", "1.1"), section, "supplements", "§10 Abs. 1 MBO", metadata={"reasoning": "Definition: Werbeanlagen = ortsfeste Einrichtungen …"}))
    edges.append(Edge(_n("10", "1.2"), _n("10", "1.1"), "sub_item_of", "§10 Abs. 1 MBO", metadata={"reasoning": "Hierzu zählen insbesondere Schilder, Beschriftungen, …"}))

    # Abs. 2: bauliche vs nicht-bauliche; Häufung
    edges.append(Edge(_n("10", "2.1"), section, "supplements", "§10 Abs. 2 MBO", metadata={"reasoning": "Werbeanlagen die bauliche Anlagen sind → Anforderungen dieses Gesetzes."}))
    edges.append(Edge(_n("10", "2.2"), section, "supplements", "§10 Abs. 2 MBO", metadata={"reasoning": "Werbeanlagen die keine baulichen Anlagen sind: nicht verunstalten/gefährden."}))
    edges.append(Edge(_n("10", "2.3"), section, "supplements", "§10 Abs. 2 MBO", metadata={"reasoning": "Störende Häufung von Werbeanlagen unzulässig."}))
    edges.append(Edge(_n("10", "2.1"), _n("2", "1.1"), "references", "§10 Abs. 2 MBO", metadata={"reasoning": "Text: 'Werbeanlagen, die bauliche Anlagen sind' — cites §2 Abs. 1."}))
    edges.append(Edge(_n("10", "2.1"), _n("3", "3.1"), "references", "§10 Abs. 2 MBO", metadata={"reasoning": "Text: 'Anforderungen … an bauliche Anlagen' — cites §3 general requirements."}))
    edges.append(Edge(_n("10", "2.2"), _n("2", "1.1"), "references", "§10 Abs. 2 MBO", metadata={"reasoning": "Text: 'keine baulichen Anlagen' — contrasts with §2 definition."}))

    # Abs. 3: outside built-up unzulässig; exceptions (store-relevant: Stätte der Leistung, Hinweisschilder)
    edges.append(Edge(_n("10", "3.1"), section, "supplements", "§10 Abs. 3 MBO", metadata={"reasoning": "Außerhalb im Zusammenhang bebauter Ortsteile Werbeanlagen unzulässig."}))
    for i in range(2, 8):
        edges.append(Edge(_n("10", f"3.{i}"), _n("10", "3.1"), "sub_item_of", "§10 Abs. 3 MBO", metadata={"reasoning": "Ausnahme: z.B. Stätte der Leistung, Hinweisschilder, Messen."}))

    # Abs. 4: Wohngebiete
    edges.append(Edge(_n("10", "4.1"), section, "supplements", "§10 Abs. 4 MBO", metadata={"reasoning": "In Wohngebieten nur an Stätte der Leistung, amtliche/kulturelle Anlagen."}))
    edges.append(Edge(_n("10", "4.2"), _n("10", "4.1"), "sub_item_of", "§10 Abs. 4 MBO", metadata={"reasoning": "In reinen Wohngebieten nur Hinweisschilder an Stätte der Leistung."}))

    # Abs. 5: Warenautomaten (stores)
    edges.append(Edge(_n("10", "5.1"), section, "supplements", "§10 Abs. 5 MBO", metadata={"reasoning": "Absätze 1 bis 3 gelten für Warenautomaten entsprechend."}))
    edges.append(Edge(_n("10", "5.1"), _n("10", "3.1"), "references", "§10 Abs. 5 MBO", metadata={"reasoning": "Text: 'Absätze 1 bis 3' — Warenautomaten under same rules as Werbeanlagen."}))

    # Abs. 6: exclusions (like §1 Abs. 2)
    edges.append(Edge(_n("10", "6.1"), section, "supplements", "§10 Abs. 6 MBO", metadata={"reasoning": "Vorschriften nicht anzuwenden auf … (exclusion holder)."}))
    for i in range(2, 6):
        edges.append(Edge(_n("10", f"6.{i}"), _n("10", "6.1"), "sub_item_of", "§10 Abs. 6 MBO", metadata={"reasoning": "Excluded case: genehmigte Säulen, Zeitungsstellen, Auslagen, Wahlwerbung."}))

    return edges


def _section_edges_flat(para: str, rows: list[str], sourced: str, reason: str) -> list[Edge]:
    """All given rows supplement section anchor (construction-law style, no sub_item_of)."""
    section = _section_node(para)
    return [
        Edge(_n(para, r), section, "supplements", sourced, metadata={"reasoning": reason})
        for r in rows
    ]


def section_11_baustelle() -> list[Edge]:
    """§11 Baustelle — rules when building: Einrichtung, Gefahrenzone, Schild, Bepflanzung."""
    return _section_edges_flat("11", ["1.1", "2.1", "2.2", "3.1", "4.1"], "§11 MBO", "Content under §11 Baustelle.")


def section_12_standsicherheit() -> list[Edge]:
    """§12 Standsicherheit — bauliche Anlagen standsicher; gemeinsame Bauteile."""
    return _section_edges_flat("12", ["1.1", "1.2", "2.1"], "§12 MBO", "Content under §12 Standsicherheit.")


def section_13_schutz_schaedliche_einfluesse() -> list[Edge]:
    """§13 Schutz gegen schädliche Einflüsse — Wasser, Schädlinge, Baugrund."""
    return _section_edges_flat("13", ["1.1", "1.2", "1.3"], "§13 MBO", "Content under §13.")


def section_14_brandschutz() -> list[Edge]:
    """§14 Brandschutz — single node 14.1."""
    return _section_edges_flat("14", ["14.1"], "§14 MBO", "Content under §14 Brandschutz.")


def section_15_waerme_schall_erschuetterung() -> list[Edge]:
    """§15 Wärme-, Schall-, Erschütterungsschutz."""
    edges = _section_edges_flat("15", ["1.1", "2.1", "2.2", "3.1"], "§15 MBO", "Content under §15.")
    return edges


def section_16_verkehrssicherheit() -> list[Edge]:
    """§16 Verkehrssicherheit."""
    return _section_edges_flat("16", ["1.1", "2.1"], "§16 MBO", "Content under §16.")


def section_16a_bauarten() -> list[Edge]:
    """§16a Bauarten — Anwendung, Bauartgenehmigung, Prüfzeugnis; Abs. 4–7 (was miscategorized as §85a in inventory)."""
    edges: list[Edge] = []
    section = _section_node("16a")
    edges.append(Edge(_n("16a", "1.1"), section, "supplements", "§16a MBO", metadata={"reasoning": "Bauarten nur wenn Anforderungen erfüllt."}))
    edges.append(Edge(_n("16a", "2.1"), section, "supplements", "§16a MBO", metadata={"reasoning": "Abweichende Bauarten: Genehmigung nötig."}))
    edges.append(Edge(_n("16a", "2.2"), _n("16a", "2.1"), "sub_item_of", "§16a MBO", metadata={"reasoning": "allgemeine Bauartgenehmigung."}))
    edges.append(Edge(_n("16a", "2.3"), _n("16a", "2.1"), "sub_item_of", "§16a MBO", metadata={"reasoning": "vorhabenbezogene Bauartgenehmigung."}))
    edges.append(Edge(_n("16a", "3.1"), section, "supplements", "§16a MBO", metadata={"reasoning": "Prüfzeugnis anstelle Zulassung."}))
    edges.append(Edge(_n("16a", "3.2"), _n("16a", "3.1"), "sub_item_of", "§16a MBO", metadata={"reasoning": "Verwaltungsvorschrift."}))
    # Abs. 4–7 (content was wrongly labelled §85a in inventory; now §16a)
    for row in ("4.1", "5.1", "6.1", "7.1"):
        edges.append(Edge(_n("16a", row), section, "supplements", "§16a MBO", metadata={"reasoning": "§16a Abs. 4–7: Bauartgenehmigung nicht erforderlich, Bestätigung, Sachkunde, Sorgfalt."}))
    return edges


def section_16b_bauprodukte() -> list[Edge]:
    """§16b Bauprodukte — Anforderungen; Abs. 2.2 cites § 3 Satz 1."""
    edges = _section_edges_flat("16b", ["1.1", "2.1", "2.2"], "§16b MBO", "Content under §16b.")
    edges.append(Edge(_n("16b", "2.2"), _n("3", "3.1"), "references", "§16b MBO", metadata={"reasoning": "Text: Schutzniveau gemäß § 3 Satz 1."}))
    return edges


def section_16c_ce_bauprodukte() -> list[Edge]:
    """§16c CE-gekennzeichnete Bauprodukte — single node 16c.1."""
    return _section_edges_flat("16c", ["16c.1"], "§16c MBO", "Content under §16c.")


def section_17_verwendbarkeitsnachweise() -> list[Edge]:
    """§17 Verwendbarkeitsnachweise — wann erforderlich, wann nicht."""
    edges: list[Edge] = []
    section = _section_node("17")
    edges.append(Edge(_n("17", "1.1"), section, "supplements", "§17 MBO", metadata={"reasoning": "Verwendbarkeitsnachweis erforderlich wenn …"}))
    for i in range(2, 5):
        edges.append(Edge(_n("17", f"1.{i}"), _n("17", "1.1"), "sub_item_of", "§17 MBO", metadata={"reasoning": "Condition."}))
    edges.append(Edge(_n("17", "2.1"), section, "supplements", "§17 MBO", metadata={"reasoning": "Nachweis nicht erforderlich für …"}))
    edges.append(Edge(_n("17", "2.2"), _n("17", "2.1"), "sub_item_of", "§17 MBO", metadata={"reasoning": "Abweichende Regel der Technik."}))
    edges.append(Edge(_n("17", "2.3"), _n("17", "2.1"), "sub_item_of", "§17 MBO", metadata={"reasoning": "Untergeordnete Bedeutung."}))
    edges.append(Edge(_n("17", "3.1"), section, "supplements", "§17 MBO", metadata={"reasoning": "Liste in Technischen Baubestimmungen."}))
    return edges


def section_18_zulassung() -> list[Edge]:
    """§18 Allgemeine bauaufsichtliche Zulassung — DIBt, Unterlagen, Frist, Bekanntmachung."""
    rows = ["1.1", "2.1", "2.2", "3.1", "4.1", "4.2", "4.3", "5.1", "6.1", "7.1"]
    return _section_edges_flat("18", rows, "§18 MBO", "Content under §18.")


def section_19_pruefzeugnis() -> list[Edge]:
    """§19 Allgemeines bauaufsichtliches Prüfzeugnis."""
    return _section_edges_flat("19", ["1.1", "2.1"], "§19 MBO", "Content under §19.")


def section_20_nachweis_einzelfall() -> list[Edge]:
    """§20 Nachweis im Einzelfall — Zustimmung; 1.3 cites § 3 Satz 1."""
    edges = _section_edges_flat("20", ["1.1", "1.2", "1.3"], "§20 MBO", "Content under §20.")
    edges.append(Edge(_n("20", "1.3"), _n("3", "3.1"), "references", "§20 MBO", metadata={"reasoning": "Text: Gefahren im Sinne des § 3 Satz 1."}))
    return edges


def section_21_uebereinstimmungsbestaetigung() -> list[Edge]:
    """§21 Übereinstimmungsbestätigung — Ü-Zeichen, Hersteller."""
    return _section_edges_flat("21", ["1.1", "2.1", "3.1", "4.1", "5.1"], "§21 MBO", "Content under §21.")


def section_22_uebereinstimmungserklaerung() -> list[Edge]:
    """§22 Übereinstimmungserklärung des Herstellers — Produktionskontrolle, Prüfstelle (1.2, 1.3 are now §23)."""
    rows = ["1.1", "2.1", "2.2", "3.1", "3.2", "4.1"]
    edges = _section_edges_flat("22", rows, "§22 MBO", "Content under §22.")
    return edges


def section_23_zertifizierung() -> list[Edge]:
    """§23 Zertifizierung — Übereinstimmungszertifikat, Fremdüberwachung (was wrongly §22 in inventory)."""
    return _section_edges_flat("23", ["1.1", "1.2", "1.3", "2.1", "2.2"], "§23 MBO", "Content under §23 Zertifizierung.")


def section_24_pruefstellen() -> list[Edge]:
    """§24 Prüf-, Zertifizierungs-, Überwachungsstellen — only node 24.1 (stray §24 block at line 863 was fixed to §19)."""
    return _section_edges_flat("24", ["24.1"], "§24 MBO", "Content under §24.")


def section_25_sachkunde_sorgfalt() -> list[Edge]:
    """§25 Besondere Sachkunde- und Sorgfaltsanforderungen."""
    return _section_edges_flat("25", ["1.1", "1.2", "2.1"], "§25 MBO", "Content under §25.")


def section_26_brandverhalten_baustoffe_bauteile() -> list[Edge]:
    """
    §26 Brandverhalten von Baustoffen und Bauteilen — meaty, construction-connected (brand classification).

    Abs. 1: 1.1 defines the classification; 1.2–1.4 are the three categories (nichtbrennbar, schwerentflammbar,
            normalentflammbar); 1.5 encloses with the rule (leichtentflammbare dürfen nicht verwendet werden).
    Abs. 2: 2.1 = Feuerwiderstandsfähigkeit lead; 2.2–2.5 under 2.1. 2.6 = second lead (Brandverhalten Baustoffe);
            2.9 includes 2.7–2.10 (2.7, 2.8, 2.10 → 2.9, 2.9 → 2.6). 2.11 = "Soweit ... müssen" lead;
            2.12–2.15 under 2.11.
    """
    edges: list[Edge] = []
    section = _section_node("26")

    # Abs. 1: 1.1 defines 1.2–1.4; 1.5 encloses (part of 1.1)
    edges.append(Edge(_n("26", "1.1"), section, "supplements", "§26 Abs. 1 MBO", metadata={"reasoning": "Lead: Baustoffe nach Brandverhalten unterschieden in …"}))
    for i in range(2, 5):
        edges.append(Edge(_n("26", f"1.{i}"), _n("26", "1.1"), "sub_item_of", "§26 Abs. 1 MBO", metadata={"reasoning": "Category (nichtbrennbar, schwerentflammbar, normalentflammbar)."}))
    edges.append(Edge(_n("26", "1.5"), _n("26", "1.1"), "supplements", "§26 Abs. 1 MBO", metadata={"reasoning": "Enclosing rule: leichtentflammbare dürfen nicht verwendet werden."}))

    # Abs. 2: Feuerwiderstandsfähigkeit + Brandverhalten Baustoffe + Anforderungen
    edges.append(Edge(_n("26", "2.1"), section, "supplements", "§26 Abs. 2 MBO", metadata={"reasoning": "Lead: Bauteile nach Feuerwiderstandsfähigkeit unterschieden in …"}))
    for i in range(2, 6):
        edges.append(Edge(_n("26", f"2.{i}"), _n("26", "2.1"), "sub_item_of", "§26 Abs. 2 MBO", metadata={"reasoning": "Feuerwiderstandsfähigkeit categories and definition."}))
    edges.append(Edge(_n("26", "2.6"), section, "supplements", "§26 Abs. 2 MBO", metadata={"reasoning": "Bauteile zusätzlich nach Brandverhalten ihrer Baustoffe unterschieden in …"}))
    # 2.9 includes 2.7 to 2.10
    edges.append(Edge(_n("26", "2.9"), _n("26", "2.6"), "sub_item_of", "§26 Abs. 2 MBO", metadata={"reasoning": "Group: Bauteile mit Brandschutzbekleidung / brennbare Baustoffe."}))
    for r in ("2.7", "2.8", "2.10"):
        edges.append(Edge(_n("26", r), _n("26", "2.9"), "sub_item_of", "§26 Abs. 2 MBO", metadata={"reasoning": "Sub-type under 2.9 (nichtbrennbar, tragend+Schicht, brennbar)."}))
    # 2.11 includes 2.12 to 2.15 (only 2.12–2.14 present in parsed graph; 2.15 row may be truncated in inventory)
    edges.append(Edge(_n("26", "2.11"), section, "supplements", "§26 Abs. 2 MBO", metadata={"reasoning": "Lead: Soweit nichts anderes bestimmt ist, müssen …"}))
    for i in range(12, 15):
        edges.append(Edge(_n("26", f"2.{i}"), _n("26", "2.11"), "sub_item_of", "§26 Abs. 2 MBO", metadata={"reasoning": "Requirement sub-point (feuerbeständig, hochfeuerhemmend, Abweichung)."}))
    return edges


def section_27_tragende_waende_stuetzen() -> list[Edge]:
    """
    §27 Tragende Wände, Stützen — fire resistance by Gebäudeklasse. One row deleted in inventory (no 1.2).
    Abs. 1: 1.1 lead; 1.3–1.5 = GK 5/4/2+3 requirements; 1.6 "Satz 2 gilt", 1.7–1.8 under 1.6.
    Abs. 2: 2.1 lead (Kellergeschoss); 2.2, 2.3 under 2.1.
    """
    edges: list[Edge] = []
    section = _section_node("27")
    edges.append(Edge(_n("27", "1.1"), section, "supplements", "§27 Abs. 1 MBO", metadata={"reasoning": "Lead: tragende/aussteifende Wände und Stützen standsicher, Sie müssen …"}))
    for r in ("1.3", "1.4", "1.5"):
        edges.append(Edge(_n("27", r), _n("27", "1.1"), "sub_item_of", "§27 Abs. 1 MBO", metadata={"reasoning": "Requirement by Gebäudeklasse (5/4/2+3)."}))
    edges.append(Edge(_n("27", "1.6"), _n("27", "1.1"), "supplements", "§27 Abs. 1 MBO", metadata={"reasoning": "Satz 2 gilt … (exceptions)."}))
    edges.append(Edge(_n("27", "1.7"), _n("27", "1.6"), "sub_item_of", "§27 Abs. 1 MBO", metadata={"reasoning": "Dachraum only if Aufenthaltsräume darüber."}))
    edges.append(Edge(_n("27", "1.8"), _n("27", "1.6"), "sub_item_of", "§27 Abs. 1 MBO", metadata={"reasoning": "Nicht für Balkone (außer notwendige Flure)."}))
    edges.append(Edge(_n("27", "2.1"), section, "supplements", "§27 Abs. 2 MBO", metadata={"reasoning": "Lead: Kellergeschoss …"}))
    edges.append(Edge(_n("27", "2.2"), _n("27", "2.1"), "sub_item_of", "§27 Abs. 2 MBO", metadata={"reasoning": "GK 3–5 feuerbeständig."}))
    edges.append(Edge(_n("27", "2.3"), _n("27", "2.1"), "sub_item_of", "§27 Abs. 2 MBO", metadata={"reasoning": "GK 1 und 2 feuerhemmend."}))
    # References to §2 Gebäudeklassen (3.2=GK1, 3.3=GK2, 3.4=GK3, 3.5=GK4, 3.6=GK5)
    edges.append(Edge(_n("27", "1.3"), _n("2", "3.6"), "references", "§27 Abs. 1 MBO", metadata={"reasoning": "Text: Gebäudeklasse 5 feuerbeständig."}))
    edges.append(Edge(_n("27", "1.4"), _n("2", "3.5"), "references", "§27 Abs. 1 MBO", metadata={"reasoning": "Text: Gebäudeklasse 4 hochfeuerhemmend."}))
    edges.append(Edge(_n("27", "1.5"), _n("2", "3.3"), "references", "§27 Abs. 1 MBO", metadata={"reasoning": "Text: Gebäudeklassen 2 und 3 feuerhemmend."}))
    edges.append(Edge(_n("27", "1.5"), _n("2", "3.4"), "references", "§27 Abs. 1 MBO", metadata={"reasoning": "Text: Gebäudeklassen 2 und 3 feuerhemmend."}))
    edges.append(Edge(_n("27", "2.2"), _n("2", "3.4"), "references", "§27 Abs. 2 MBO", metadata={"reasoning": "Text: Gebäudeklassen 3 bis 5 feuerbeständig."}))
    edges.append(Edge(_n("27", "2.2"), _n("2", "3.5"), "references", "§27 Abs. 2 MBO", metadata={"reasoning": "Text: Gebäudeklassen 3 bis 5 feuerbeständig."}))
    edges.append(Edge(_n("27", "2.2"), _n("2", "3.6"), "references", "§27 Abs. 2 MBO", metadata={"reasoning": "Text: Gebäudeklassen 3 bis 5 feuerbeständig."}))
    edges.append(Edge(_n("27", "2.3"), _n("2", "3.2"), "references", "§27 Abs. 2 MBO", metadata={"reasoning": "Text: Gebäudeklassen 1 und 2 feuerhemmend."}))
    edges.append(Edge(_n("27", "2.3"), _n("2", "3.3"), "references", "§27 Abs. 2 MBO", metadata={"reasoning": "Text: Gebäudeklassen 1 und 2 feuerhemmend."}))
    return edges


def section_28_aussenwaende() -> list[Edge]:
    """
    §28 Außenwände — 2.2 defines exception to 2.1; 2.3–2.6 are the exception cases. Rest straightforward.
    """
    edges: list[Edge] = []
    section = _section_node("28")
    # Abs. 1
    edges.append(Edge(_n("28", "1.1"), section, "supplements", "§28 Abs. 1 MBO", metadata={"reasoning": "Außenwände: Brandausbreitung begrenzt."}))
    # Abs. 2: 2.1 main rule; 2.2 = "Satz 1 gilt nicht für" (exception holder), 2.3–2.6 define the exceptions
    edges.append(Edge(_n("28", "2.1"), section, "supplements", "§28 Abs. 2 MBO", metadata={"reasoning": "Nichttragende Außenwände nichtbrennbar / feuerhemmend."}))
    edges.append(Edge(_n("28", "2.2"), _n("28", "2.1"), "exception_of", "§28 Abs. 2 MBO", metadata={"reasoning": "Satz 1 gilt nicht für … (exception holder)."}))
    for r in ("2.3", "2.4", "2.5", "2.6"):
        edges.append(Edge(_n("28", r), _n("28", "2.2"), "sub_item_of", "§28 Abs. 2 MBO", metadata={"reasoning": "Exception case: Türen/Fenster, Fugendichtungen, Dämmstoffe, Kleinteile."}))
    # Abs. 3–5 straightforward
    edges.append(Edge(_n("28", "3.1"), section, "supplements", "§28 Abs. 3 MBO", metadata={"reasoning": "Oberflächen/Bekleidungen schwerentflammbar."}))
    edges.append(Edge(_n("28", "3.2"), _n("28", "3.1"), "sub_item_of", "§28 Abs. 3 MBO", metadata={"reasoning": "Balkonbekleidungen, Solaranlagen."}))
    edges.append(Edge(_n("28", "3.3"), _n("28", "3.1"), "sub_item_of", "§28 Abs. 3 MBO", metadata={"reasoning": "Nicht brennend abfallen/abtropfen."}))
    edges.append(Edge(_n("28", "4.1"), section, "supplements", "§28 Abs. 4 MBO", metadata={"reasoning": "Hohl-/Lufträume: besondere Vorkehrungen."}))
    edges.append(Edge(_n("28", "4.2"), _n("28", "4.1"), "sub_item_of", "§28 Abs. 4 MBO", metadata={"reasoning": "Doppelfassaden entsprechend."}))
    edges.append(Edge(_n("28", "5.1"), section, "supplements", "§28 Abs. 5 MBO", metadata={"reasoning": "Abs. 2–4 gelten nicht für GK 1–3."}))
    edges.append(Edge(_n("28", "5.2"), section, "supplements", "§28 Abs. 5 MBO", metadata={"reasoning": "Abweichend von Abs. 3: hinterlüftete Bekleidungen."}))
    # 5.1 cites Gebäudeklassen 1 bis 3
    for gk in ("3.2", "3.3", "3.4"):
        edges.append(Edge(_n("28", "5.1"), _n("2", gk), "references", "§28 Abs. 5 MBO", metadata={"reasoning": "Text: Abs. 2–4 gelten nicht für Gebäude der Gebäudeklassen 1 bis 3."}))
    return edges


def section_29_trennwaende() -> list[Edge]:
    """
    §29 Trennwände. 2.1 notifies the hard requirements (when you need these walls); 2.2–2.4 are the cases.
    """
    edges: list[Edge] = []
    section = _section_node("29")
    edges.append(Edge(_n("29", "1.1"), section, "supplements", "§29 Abs. 1 MBO", metadata={"reasoning": "Trennwände nach Abs. 2: widerstandsfähig gegen Brandausbreitung."}))
    # 2.1 = when Trennwände are required; 2.2–2.4 = the three cases (hard requirements)
    edges.append(Edge(_n("29", "2.1"), section, "supplements", "§29 Abs. 2 MBO", metadata={"reasoning": "Trennwände sind erforderlich (notifies when these walls are required)."}))
    for r in ("2.2", "2.3", "2.4"):
        edges.append(Edge(_n("29", r), _n("29", "2.1"), "sub_item_of", "§29 Abs. 2 MBO", metadata={"reasoning": "Case when Trennwände are required: zwischen Nutzungseinheiten, Explosions-/Brandgefahr, Kellergeschoss."}))
    edges.append(Edge(_n("29", "3.1"), section, "supplements", "§29 Abs. 3 MBO", metadata={"reasoning": "Abs. 2 Nr. 1 und 3: Feuerwiderstand mind. feuerhemmend."}))
    edges.append(Edge(_n("29", "3.2"), section, "supplements", "§29 Abs. 3 MBO", metadata={"reasoning": "Abs. 2 Nr. 2: feuerbeständig."}))
    edges.append(Edge(_n("29", "4.1"), section, "supplements", "§29 Abs. 4 MBO", metadata={"reasoning": "Trennwände bis Rohdecke/Dachhaut; Decke feuerhemmend."}))
    edges.append(Edge(_n("29", "5.1"), section, "supplements", "§29 Abs. 5 MBO", metadata={"reasoning": "Öffnungen: erforderliche Zahl/Größe, feuerhemmende Abschlüsse."}))
    edges.append(Edge(_n("29", "6.1"), section, "exception_of", "§29 MBO", metadata={"reasoning": "Abs. 1–5 gelten nicht für Wohngebäude der Gebäudeklassen 1 und 2."}))
    edges.append(Edge(_n("29", "6.1"), _n("2", "3.2"), "references", "§29 Abs. 6 MBO", metadata={"reasoning": "Text: nicht für Wohngebäude GK 1 und 2."}))
    edges.append(Edge(_n("29", "6.1"), _n("2", "3.3"), "references", "§29 Abs. 6 MBO", metadata={"reasoning": "Text: nicht für Wohngebäude GK 1 und 2."}))
    return edges


def section_30_brandwaende() -> list[Edge]:
    """
    §30 Brandwände. 2.1 = when this wall type is needed (hard requirements); 2.2–2.5 = cases.
    3.2 = lead for alternatives; 3.3–3.6 = alternative cases. 4.2 = lead; 4.3–4.7 = conditions.
    Cross-refs to §2 Gebäudeklassen and §6 (Vorbauten) where cited.
    """
    edges: list[Edge] = []
    section = _section_node("30")
    edges.append(Edge(_n("30", "1.1"), section, "supplements", "§30 Abs. 1 MBO", metadata={"reasoning": "Brandwände: Brandausbreitung verhindern (Gebäudeabschlusswand / innere Brandwand)."}))
    # 2.1 = when Brandwände are required; 2.2–2.5 = the four cases
    edges.append(Edge(_n("30", "2.1"), section, "supplements", "§30 Abs. 2 MBO", metadata={"reasoning": "Brandwände sind erforderlich (notifies when this wall type is needed)."}))
    for r in ("2.2", "2.3", "2.4", "2.5"):
        edges.append(Edge(_n("30", r), _n("30", "2.1"), "sub_item_of", "§30 Abs. 2 MBO", metadata={"reasoning": "Case: Gebäudeabschlusswand, innere Brandwand 40 m, landw. 10 000 m³, Wohngebäude/landw. Anbau."}))
    edges.append(Edge(_n("30", "3.1"), section, "supplements", "§30 Abs. 3 MBO", metadata={"reasoning": "Brandwände feuerbeständig, nichtbrennbar."}))
    edges.append(Edge(_n("30", "3.2"), section, "supplements", "§30 Abs. 3 MBO", metadata={"reasoning": "Anstelle von Brandwänden zulässig (Abs. 2 Nr. 1–3): lead for alternatives."}))
    for r in ("3.3", "3.4", "3.5", "3.6"):
        edges.append(Edge(_n("30", r), _n("30", "3.2"), "sub_item_of", "§30 Abs. 3 MBO", metadata={"reasoning": "Alternative: GK 4 hochfeuerhemmend; GK 1–3 hochfeuerhemmend/feuerbeständig; Abs. 2 Nr. 4 feuerbeständig ≤2000 m³."}))
    edges.append(Edge(_n("30", "4.1"), section, "supplements", "§30 Abs. 4 MBO", metadata={"reasoning": "Brandwände bis Bedachung, geschossweise übereinander."}))
    edges.append(Edge(_n("30", "4.2"), section, "supplements", "§30 Abs. 4 MBO", metadata={"reasoning": "Abweichend: geschossweise versetzt, wenn (lead)."}))
    for r in ("4.3", "4.4", "4.5", "4.6", "4.7"):
        edges.append(Edge(_n("30", r), _n("30", "4.2"), "sub_item_of", "§30 Abs. 4 MBO", metadata={"reasoning": "Condition for versetzt: Wände Abs. 3; Decken feuerbeständig; Bauteile feuerbeständig; Außenwände; Öffnungen/Vorkehrungen."}))
    for row in ("5.1", "5.2", "5.3", "5.4"):
        edges.append(Edge(_n("30", row), section, "supplements", "§30 Abs. 5 MBO", metadata={"reasoning": "Durchführung über Bedachung; GK 1–3 bis unter Dachhaut; Hohlräume."}))
    edges.append(Edge(_n("30", "6.1"), section, "supplements", "§30 Abs. 6 MBO", metadata={"reasoning": "Abstand Brandwand von innerer Ecke mind. 5 m; Ausnahme Winkel >120° oder öffnungslose Wand."}))
    for row in ("7.1", "7.2", "7.3", "7.4"):
        edges.append(Edge(_n("30", row), section, "supplements", "§30 Abs. 7 MBO", metadata={"reasoning": "Brennbare Bauteile nicht über Brandwände; Außenwandkonstruktionen; Bekleidungen; Einwirkungen."}))
    edges.append(Edge(_n("30", "8.1"), section, "supplements", "§30 Abs. 8 MBO", metadata={"reasoning": "Öffnungen in Brandwänden unzulässig."}))
    edges.append(Edge(_n("30", "8.2"), section, "supplements", "§30 Abs. 8 MBO", metadata={"reasoning": "Innere Brandwände: Öffnungen nur erforderliche Zahl/Größe, feuerbeständige Abschlüsse."}))
    edges.append(Edge(_n("30", "9.1"), section, "supplements", "§30 Abs. 9 MBO", metadata={"reasoning": "Feuerbeständige Verglasungen in inneren Brandwänden."}))
    edges.append(Edge(_n("30", "10.1"), section, "supplements", "§30 Abs. 10 MBO", metadata={"reasoning": "Abs. 2 Nr. 1 gilt nicht für Vorbauten §6 Abs. 6; Abs. 4–10 gelten für Wände nach Abs. 3 S. 2/3."}))
    # Cross-refs: Gebäudeklassen
    edges.append(Edge(_n("30", "3.3"), _n("2", "3.5"), "references", "§30 Abs. 3 MBO", metadata={"reasoning": "Text: für Gebäude der Gebäudeklasse 4."}))
    for gk in ("3.2", "3.3", "3.4"):
        edges.append(Edge(_n("30", "3.4"), _n("2", gk), "references", "§30 Abs. 3 MBO", metadata={"reasoning": "Text: Gebäudeklassen 1 bis 3."}))
        edges.append(Edge(_n("30", "3.5"), _n("2", gk), "references", "§30 Abs. 3 MBO", metadata={"reasoning": "Text: Gebäudeklassen 1 bis 3."}))
        edges.append(Edge(_n("30", "5.2"), _n("2", gk), "references", "§30 Abs. 5 MBO", metadata={"reasoning": "Text: Bei Gebäuden der Gebäudeklassen 1 bis 3."}))
        edges.append(Edge(_n("30", "6.1"), _n("2", gk), "references", "§30 Abs. 6 MBO", metadata={"reasoning": "Text: bei Gebäuden der Gebäudeklassen 1 bis 4."}))
    edges.append(Edge(_n("30", "6.1"), _n("2", "3.5"), "references", "§30 Abs. 6 MBO", metadata={"reasoning": "Text: Gebäudeklassen 1 bis 4 (GK 4)."}))
    edges.append(Edge(_n("30", "5.3"), _n("2", "3.5"), "references", "§30 Abs. 5 MBO", metadata={"reasoning": "Text: Gebäude der Gebäudeklasse 4 (Dachausbau)."}))
    edges.append(Edge(_n("30", "6.1"), _n("2", "3.5"), "references", "§30 Abs. 6 MBO", metadata={"reasoning": "Text: Gebäudeklassen 1 bis 4."}))
    edges.append(Edge(_n("30", "10.1"), _n("6", "6.1"), "references", "§30 Abs. 10 MBO", metadata={"reasoning": "Text: Vorbauten im Sinne des § 6 Abs. 6."}))
    return edges


def section_31_decken() -> list[Edge]:
    """
    §31 Decken — fire resistance by Gebäudeklasse, Kellergeschoss, openings.
    """
    edges: list[Edge] = []
    section = _section_node("31")

    # Abs. 1: general requirement + GK-specific + exceptions
    edges.append(Edge(_n("31", "1.1"), section, "supplements", "§31 Abs. 1 MBO", metadata={"reasoning": "Decken: standsicher und widerstandsfähig gegen Brandausbreitung."}))
    edges.append(Edge(_n("31", "1.2"), section, "supplements", "§31 Abs. 1 MBO", metadata={"reasoning": "Sie müssen (lead for GK-spezifische Anforderungen)."}))
    for r, gk in (("1.3", "3.6"), ("1.4", "3.5"), ("1.5", None)):
        edges.append(Edge(_n("31", r), _n("31", "1.2"), "sub_item_of", "§31 Abs. 1 MBO", metadata={"reasoning": "Feuerwiderstand je Gebäudeklasse."}))
        if gk:
            edges.append(Edge(_n("31", r), _n("2", gk), "references", "§31 Abs. 1 MBO", metadata={"reasoning": "Text: Gebäude der Gebäudeklasse …"}))
    # GK 2 und 3 → both classes
    edges.append(Edge(_n("31", "1.5"), _n("2", "3.3"), "references", "§31 Abs. 1 MBO", metadata={"reasoning": "Gebäudeklasse 3."}))
    edges.append(Edge(_n("31", "1.5"), _n("2", "3.4"), "references", "§31 Abs. 1 MBO", metadata={"reasoning": "Gebäudeklasse 2."}))
    # Satz 2 gilt nicht in bestimmten Fällen
    edges.append(Edge(_n("31", "1.7"), _n("31", "1.2"), "exception_of", "§31 Abs. 1 MBO", metadata={"reasoning": "Satz 2 gilt für Geschosse im Dachraum nur, wenn darüber Aufenthaltsräume möglich sind; verweist auf Trennwände §29 Abs. 4."}))
    edges.append(Edge(_n("31", "1.8"), _n("31", "1.2"), "exception_of", "§31 Abs. 1 MBO", metadata={"reasoning": "Satz 2 gilt nicht für Balkone (außer offene Gänge als notwendige Flure)."}))
    edges.append(Edge(_n("31", "1.7"), _n("29", "4.1"), "references", "§31 Abs. 1 MBO", metadata={"reasoning": "Text: § 29 Abs. 4 bleibt unberührt."}))

    # Abs. 2: Kellergeschoss + besondere Fälle
    edges.append(Edge(_n("31", "2.1"), section, "supplements", "§31 Abs. 2 MBO", metadata={"reasoning": "Im Kellergeschoss müssen Decken …"}))
    for r, gks in (("2.2", ("3.4", "3.5", "3.6")), ("2.3", ("3.2", "3.3"))):
        edges.append(Edge(_n("31", r), _n("31", "2.1"), "sub_item_of", "§31 Abs. 2 MBO", metadata={"reasoning": "GK-spezifische Anforderung im Kellergeschoss."}))
        for gk in gks:
            edges.append(Edge(_n("31", r), _n("2", gk), "references", "§31 Abs. 2 MBO", metadata={"reasoning": "Text: Gebäudeklassen …"}))
    edges.append(Edge(_n("31", "2.4"), section, "supplements", "§31 Abs. 2 MBO", metadata={"reasoning": "Decken feuerbeständig unter/über Räumen mit Explosions-/erhöhter Brandgefahr …"}))
    edges.append(Edge(_n("31", "2.5"), _n("31", "2.4"), "sub_item_of", "§31 Abs. 2 MBO", metadata={"reasoning": "Ausnahme: ausgenommen Wohngebäude GK 1 und 2."}))
    edges.append(Edge(_n("31", "2.5"), _n("2", "3.2"), "references", "§31 Abs. 2 MBO", metadata={"reasoning": "Wohngebäude GK 1 und 2."}))
    edges.append(Edge(_n("31", "2.5"), _n("2", "3.3"), "references", "§31 Abs. 2 MBO", metadata={"reasoning": "Wohngebäude GK 1 und 2."}))
    edges.append(Edge(_n("31", "2.6"), _n("31", "2.4"), "sub_item_of", "§31 Abs. 2 MBO", metadata={"reasoning": "Decke zwischen landwirtschaftlichem Teil und Wohnteil."}))

    # Abs. 3–4
    edges.append(Edge(_n("31", "3.1"), section, "supplements", "§31 Abs. 3 MBO", metadata={"reasoning": "Anschluss der Decke an Außenwand."}))
    edges.append(Edge(_n("31", "4.1"), section, "supplements", "§31 Abs. 4 MBO", metadata={"reasoning": "Öffnungen in Decken nur zulässig …"}))
    for r in ("4.2", "4.3", "4.4"):
        edges.append(Edge(_n("31", r), _n("31", "4.1"), "sub_item_of", "§31 Abs. 4 MBO", metadata={"reasoning": "Bedingungen für Öffnungen (GK 1+2, Nutzungseinheit, Abschlüsse)."}))
    edges.append(Edge(_n("31", "4.2"), _n("2", "3.2"), "references", "§31 Abs. 4 MBO", metadata={"reasoning": "Gebäude GK 1 und 2."}))
    edges.append(Edge(_n("31", "4.2"), _n("2", "3.3"), "references", "§31 Abs. 4 MBO", metadata={"reasoning": "Gebäude GK 1 und 2."}))

    return edges


def section_32_daecher() -> list[Edge]:
    """
    §32 Dächer — harte/weiche Bedachung, Abstände, besondere Dachsituationen.
    """
    edges: list[Edge] = []
    section = _section_node("32")

    # Abs. 1: harte Bedachung
    edges.append(Edge(_n("32", "1.1"), section, "supplements", "§32 Abs. 1 MBO", metadata={"reasoning": "Bedachungen: harte Bedachung (widerstandsfähig gegen Brand von außen)."}))

    # Abs. 2: weiche Bedachung für GK 1–3 bei bestimmten Abständen
    edges.append(Edge(_n("32", "2.1"), section, "supplements", "§32 Abs. 2 MBO", metadata={"reasoning": "Bedachungen ohne harte Bedachung zulässig bei GK 1–3, wenn Abstände eingehalten werden."}))
    for r in ("2.2", "2.3", "2.4", "2.5"):
        edges.append(Edge(_n("32", r), _n("32", "2.1"), "sub_item_of", "§32 Abs. 2 MBO", metadata={"reasoning": "Abstandsfall (12/15/24/5 m)."}))
    for gk in ("3.2", "3.3", "3.4"):
        edges.append(Edge(_n("32", "2.1"), _n("2", gk), "references", "§32 Abs. 2 MBO", metadata={"reasoning": "Gebäude der Gebäudeklassen 1 bis 3."}))
    # Reduzierte Abstände für Wohngebäude GK 1 und 2
    edges.append(Edge(_n("32", "2.7"), _n("32", "2.1"), "exception_of", "§32 Abs. 2 MBO", metadata={"reasoning": "Wohngebäude GK 1 und 2: geringere Abstände in Fall der Nr. 1."}))
    edges.append(Edge(_n("32", "2.8"), _n("32", "2.1"), "exception_of", "§32 Abs. 2 MBO", metadata={"reasoning": "Wohngebäude GK 1 und 2: geringere Abstände in Fall der Nr. 2."}))
    edges.append(Edge(_n("32", "2.9"), _n("32", "2.1"), "exception_of", "§32 Abs. 2 MBO", metadata={"reasoning": "Wohngebäude GK 1 und 2: geringere Abstände in Fall der Nr. 3."}))
    for r in ("2.7", "2.8", "2.9"):
        edges.append(Edge(_n("32", r), _n("2", "3.2"), "references", "§32 Abs. 2 MBO", metadata={"reasoning": "Wohngebäude GK 1 und 2."}))
        edges.append(Edge(_n("32", r), _n("2", "3.3"), "references", "§32 Abs. 2 MBO", metadata={"reasoning": "Wohngebäude GK 1 und 2."}))

    # Abs. 3: Ausnahmen von Abs. 1 und 2
    edges.append(Edge(_n("32", "3.1"), section, "supplements", "§32 Abs. 3 MBO", metadata={"reasoning": "Abs. 1 und 2 gelten nicht für … (Ausnahmen)."}))
    for r in ("3.2", "3.3", "3.4", "3.5", "3.6"):
        edges.append(Edge(_n("32", r), _n("32", "3.1"), "sub_item_of", "§32 Abs. 3 MBO", metadata={"reasoning": "Fall, für den Abs. 1 und 2 nicht gelten."}))

    # Abs. 4: abweichende zulässige Bedachungen
    edges.append(Edge(_n("32", "4.1"), section, "supplements", "§32 Abs. 4 MBO", metadata={"reasoning": "Abweichend von Abs. 1 und 2 sind bestimmte Bedachungen zulässig."}))
    edges.append(Edge(_n("32", "4.2"), _n("32", "4.1"), "sub_item_of", "§32 Abs. 4 MBO", metadata={"reasoning": "Lichtdurchlässige Teilflächen aus brennbaren Baustoffen."}))
    edges.append(Edge(_n("32", "4.3"), _n("32", "4.1"), "sub_item_of", "§32 Abs. 4 MBO", metadata={"reasoning": "Begrünte Bedachungen."}))

    # Abs. 5: Dachaufbauten und Abstände zu Brandwänden
    edges.append(Edge(_n("32", "5.1"), section, "supplements", "§32 Abs. 5 MBO", metadata={"reasoning": "Dachüberstände, Dachaufbauten, Solaranlagen etc. so anordnen, dass Feuer nicht übertragen wird."}))
    edges.append(Edge(_n("32", "5.2"), section, "supplements", "§32 Abs. 5 MBO", metadata={"reasoning": "Abstände von Brandwänden und Wänden anstelle von Brandwänden."}))
    for r in ("5.3", "5.4", "5.5"):
        edges.append(Edge(_n("32", r), _n("32", "5.2"), "sub_item_of", "§32 Abs. 5 MBO", metadata={"reasoning": "Abstandskategorie für verschiedene Dachbauteile/Solaranlagen."}))
    edges.append(Edge(_n("32", "5.2"), _n("30", "1.1"), "references", "§32 Abs. 5 MBO", metadata={"reasoning": "Text: von Brandwänden und Wänden, die anstelle von Brandwänden zulässig sind — Bezug §30."}))

    # Abs. 6–8: traufseitig aneinandergebaute Gebäude, Anbauten, Vorrichtungen
    edges.append(Edge(_n("32", "6.1"), section, "supplements", "§32 Abs. 6 MBO", metadata={"reasoning": "Dächer von traufseitig aneinandergebauten Gebäuden: feuerhemmend von innen nach außen."}))
    edges.append(Edge(_n("32", "6.2"), _n("32", "6.1"), "sub_item_of", "§32 Abs. 6 MBO", metadata={"reasoning": "Abstand von Öffnungen zu Brandwand oder ersetzender Wand."}))
    edges.append(Edge(_n("32", "7.1"), section, "supplements", "§32 Abs. 7 MBO", metadata={"reasoning": "Dächer von Anbauten an Außenwände mit Öffnungen/ohne Feuerwiderstandsfähigkeit."}))
    edges.append(Edge(_n("32", "7.2"), _n("32", "7.1"), "exception_of", "§32 Abs. 7 MBO", metadata={"reasoning": "Gilt nicht für Anbauten an Wohngebäude der GK 1 bis 3."}))
    for gk in ("3.2", "3.3", "3.4"):
        edges.append(Edge(_n("32", "7.2"), _n("2", gk), "references", "§32 Abs. 7 MBO", metadata={"reasoning": "Wohngebäude der Gebäudeklassen 1 bis 3."}))
    edges.append(Edge(_n("32", "8.1"), section, "supplements", "§32 Abs. 8 MBO", metadata={"reasoning": "Sicher benutzbare Vorrichtungen für Dacharbeiten."}))

    return edges


def section_33_rettungswege() -> list[Edge]:
    """
    §33 Erster und zweiter Rettungsweg — two independent escape routes.
    """
    edges: list[Edge] = []
    section = _section_node("33")

    # Abs. 1
    edges.append(Edge(_n("33", "1.1"), section, "supplements", "§33 Abs. 1 MBO", metadata={"reasoning": "Nutzungseinheiten mit Aufenthaltsräumen: zwei Rettungswege."}))
    edges.append(Edge(_n("33", "1.2"), _n("33", "1.1"), "exception_of", "§33 Abs. 1 MBO", metadata={"reasoning": "Erdgeschossige, eingeschossige Nutzungseinheiten ohne zweiten Rettungsweg, wenn direkter Ausgang."}))

    # Abs. 2
    for r in ("2.1", "2.2", "2.3"):
        edges.append(Edge(_n("33", r), section, "supplements", "§33 Abs. 2 MBO", metadata={"reasoning": "Erster Rettungsweg über notwendige Treppe; zweiter über weitere Treppe oder Feuerwehrgeräte/Sicherheitstreppenraum."}))

    # Abs. 3
    edges.append(Edge(_n("33", "3.1"), section, "supplements", "§33 Abs. 3 MBO", metadata={"reasoning": "Gebäude mit zweitem Rettungsweg über Feuerwehrgeräte >8 m Brüstungshöhe nur bei geeigneter Ausstattung."}))
    edges.append(Edge(_n("33", "3.2"), section, "supplements", "§33 Abs. 3 MBO", metadata={"reasoning": "Bei Sonderbauten zweiter Rettungsweg über Feuerwehrgeräte nur, wenn keine Bedenken."}))
    edges.append(Edge(_n("33", "3.2"), _n("51", "1.1"), "references", "§33 Abs. 3 MBO", metadata={"reasoning": "Text: Bei Sonderbauten — Bezug §51."}))

    return edges


def section_34_treppen() -> list[Edge]:
    """
    §34 Treppen — notwendige Treppen, GK-bezogene Anforderungen.
    """
    edges: list[Edge] = []
    section = _section_node("34")

    # Abs. 1
    edges.append(Edge(_n("34", "1.1"), section, "supplements", "§34 Abs. 1 MBO", metadata={"reasoning": "Jedes Geschoss/Dachraum über notwendige Treppe zugänglich."}))
    edges.append(Edge(_n("34", "1.2"), section, "supplements", "§34 Abs. 1 MBO", metadata={"reasoning": "Statt notwendiger Treppen sind Rampen zulässig."}))

    # Abs. 2
    edges.append(Edge(_n("34", "2.1"), section, "supplements", "§34 Abs. 2 MBO", metadata={"reasoning": "Einschiebbare Treppen/Rolltreppen als notwendige Treppen unzulässig."}))
    edges.append(Edge(_n("34", "2.2"), _n("34", "2.1"), "exception_of", "§34 Abs. 2 MBO", metadata={"reasoning": "In GK 1 und 2 als Zugang zu Dachraum ohne Aufenthaltsraum zulässig."}))
    for gk in ("3.2", "3.3"):
        edges.append(Edge(_n("34", "2.2"), _n("2", gk), "references", "§34 Abs. 2 MBO", metadata={"reasoning": "Gebäude der Gebäudeklassen 1 und 2."}))

    # Abs. 3
    edges.append(Edge(_n("34", "3.1"), section, "supplements", "§34 Abs. 3 MBO", metadata={"reasoning": "Notwendige Treppen in einem Zug zu allen Geschossen; Verbindung zu Dachraum."}))
    edges.append(Edge(_n("34", "3.2"), section, "supplements", "§34 Abs. 3 MBO", metadata={"reasoning": "Dies gilt nicht für bestimmte Treppen."}))
    edges.append(Edge(_n("34", "3.3"), _n("34", "3.1"), "exception_of", "§34 Abs. 3 MBO", metadata={"reasoning": "Ausnahme für Gebäude GK 1 bis 3."}))
    for gk in ("3.2", "3.3", "3.4"):
        edges.append(Edge(_n("34", "3.3"), _n("2", gk), "references", "§34 Abs. 3 MBO", metadata={"reasoning": "Gebäude der Gebäudeklassen 1 bis 3."}))
    edges.append(Edge(_n("34", "3.4"), _n("34", "3.1"), "exception_of", "§34 Abs. 3 MBO", metadata={"reasoning": "Ausnahme für Treppen nach §35 Abs. 1 Satz 3 Nr. …"}))
    edges.append(Edge(_n("34", "3.4"), _n("35", "1.1"), "references", "§34 Abs. 3 MBO", metadata={"reasoning": "Bezug zu §35 Abs. 1 Satz 3."}))

    # Abs. 4–7
    edges.append(Edge(_n("34", "4.1"), section, "supplements", "§34 Abs. 4 MBO", metadata={"reasoning": "Tragende Teile notwendiger Treppen: Anforderungen nach GK."}))
    for r, gks in (("4.2", ("3.6",)), ("4.3", ("3.5",)), ("4.4", ("3.4",))):
        edges.append(Edge(_n("34", r), _n("34", "4.1"), "sub_item_of", "§34 Abs. 4 MBO", metadata={"reasoning": "GK-spezifische Anforderung an tragende Teile."}))
        for gk in gks:
            edges.append(Edge(_n("34", r), _n("2", gk), "references", "§34 Abs. 4 MBO", metadata={"reasoning": "Gebäudeklasse laut Text."}))
    edges.append(Edge(_n("34", "4.5"), _n("34", "4.1"), "sub_item_of", "§34 Abs. 4 MBO", metadata={"reasoning": "Tragende Teile von Außentreppen nach §35 Abs. 1 Satz 3 Nr. 3 GK 3–5 nichtbrennbar."}))
    for gk in ("3.4", "3.5", "3.6"):
        edges.append(Edge(_n("34", "4.5"), _n("2", gk), "references", "§34 Abs. 4 MBO", metadata={"reasoning": "Gebäudeklassen 3 bis 5."}))
    edges.append(Edge(_n("34", "4.5"), _n("35", "1.1"), "references", "§34 Abs. 4 MBO", metadata={"reasoning": "Außentreppen nach §35 Abs. 1 Satz 3 Nr. 3."}))

    edges.append(Edge(_n("34", "5.1"), section, "supplements", "§34 Abs. 5 MBO", metadata={"reasoning": "Nutzbare Breite der notwendigen Treppen."}))
    edges.append(Edge(_n("34", "6.1"), section, "supplements", "§34 Abs. 6 MBO", metadata={"reasoning": "Treppen müssen Handlauf haben."}))
    edges.append(Edge(_n("34", "6.2"), _n("34", "6.1"), "sub_item_of", "§34 Abs. 6 MBO", metadata={"reasoning": "Handläufe auf beiden Seiten/Zwischenhandläufe nach Verkehrssicherheit."}))
    edges.append(Edge(_n("34", "7.1"), section, "supplements", "§34 Abs. 7 MBO", metadata={"reasoning": "Keine Treppe unmittelbar hinter Tür, die in Richtung Treppe aufschlägt."}))

    return edges


def section_35_treppenraeume() -> list[Edge]:
    """
    §35 Notwendige Treppenräume, Ausgänge — Rettungswegsicherheit.
    """
    edges: list[Edge] = []
    section = _section_node("35")

    # Abs. 1
    edges.append(Edge(_n("35", "1.1"), section, "supplements", "§35 Abs. 1 MBO", metadata={"reasoning": "Jede notwendige Treppe in eigenem Treppenraum (Sicherstellung der Rettungswege)."}))
    edges.append(Edge(_n("35", "1.2"), section, "supplements", "§35 Abs. 1 MBO", metadata={"reasoning": "Treppenräume so anordnen/ausbilden, dass Nutzung im Brandfall möglich bleibt."}))
    edges.append(Edge(_n("35", "1.3"), section, "supplements", "§35 Abs. 1 MBO", metadata={"reasoning": "Notwendige Treppen ohne eigenen Treppenraum zulässig, wenn …"}))
    for r in ("1.4", "1.5", "1.6"):
        edges.append(Edge(_n("35", r), _n("35", "1.3"), "sub_item_of", "§35 Abs. 1 MBO", metadata={"reasoning": "Fall ohne eigenen Treppenraum (GK 1+2, interne Verbindung, Außentreppe)."}))
    for gk in ("3.2", "3.3"):
        edges.append(Edge(_n("35", "1.4"), _n("2", gk), "references", "§35 Abs. 1 MBO", metadata={"reasoning": "Gebäude der Gebäudeklassen 1 und 2."}))

    # Abs. 2–3
    for r in ("2.1", "2.2", "2.3", "3.1", "3.2"):
        edges.append(Edge(_n("35", r), section, "supplements", "§35 Abs. 2–3 MBO", metadata={"reasoning": "Abstand zum Treppenraum, Anzahl/Verteilung notwendiger Treppenräume, Ausgang ins Freie."}))
    for r in ("3.3", "3.4", "3.5", "3.6"):
        edges.append(Edge(_n("35", r), _n("35", "3.2"), "sub_item_of", "§35 Abs. 3 MBO", metadata={"reasoning": "Anforderungen an Raum zwischen Treppenraum und Ausgang ins Freie."}))

    # Abs. 4
    edges.append(Edge(_n("35", "4.1"), section, "supplements", "§35 Abs. 4 MBO", metadata={"reasoning": "Wände notwendiger Treppenräume als raumabschließende Bauteile; obere Abschlüsse."}))
    for r, gks in (("4.2", ("3.6",)), ("4.3", ("3.5",)), ("4.4", ("3.4",))):
        edges.append(Edge(_n("35", r), _n("35", "4.1"), "sub_item_of", "§35 Abs. 4 MBO", metadata={"reasoning": "GK-spezifische Anforderung (Bauart wie Brandwände/hochfeuerhemmend/feuerhemmend)."}))
        for gk in gks:
            edges.append(Edge(_n("35", r), _n("2", gk), "references", "§35 Abs. 4 MBO", metadata={"reasoning": "Gebäudeklasse laut Text."}))
    edges.append(Edge(_n("35", "4.5"), _n("35", "4.1"), "sub_item_of", "§35 Abs. 4 MBO", metadata={"reasoning": "Nicht erforderlich für bestimmte Außenwände von Treppenräumen."}))
    edges.append(Edge(_n("35", "4.6"), _n("35", "4.1"), "sub_item_of", "§35 Abs. 4 MBO", metadata={"reasoning": "Oberer Abschluss mit Feuerwiderstand der Decken."}))

    # Abs. 5–8
    edges.append(Edge(_n("35", "5.1"), section, "supplements", "§35 Abs. 5 MBO", metadata={"reasoning": "Baustoffanforderungen in Treppenräumen und Räumen nach Abs. 3 Satz 2."}))
    for r in ("5.2", "5.3", "5.4"):
        edges.append(Edge(_n("35", r), _n("35", "5.1"), "sub_item_of", "§35 Abs. 5 MBO", metadata={"reasoning": "Nichtbrennbare Bekleidungen, Unterdecken, Bodenbeläge."}))
    edges.append(Edge(_n("35", "6.1"), section, "supplements", "§35 Abs. 6 MBO", metadata={"reasoning": "Öffnungen in Treppenräumen: Anforderungen an Abschlüsse."}))
    for r in ("6.2", "6.3", "6.4", "6.5"):
        edges.append(Edge(_n("35", r), _n("35", "6.1"), "sub_item_of", "§35 Abs. 6 MBO", metadata={"reasoning": "Anforderungen für verschiedene Raumarten (Keller, Flure, sonstige Räume)."}))
    edges.append(Edge(_n("35", "7.1"), section, "supplements", "§35 Abs. 7 MBO", metadata={"reasoning": "Treppenräume müssen beleuchtet sein."}))
    edges.append(Edge(_n("35", "7.2"), _n("35", "7.1"), "sub_item_of", "§35 Abs. 7 MBO", metadata={"reasoning": "Sicherheitsbeleuchtung bei Höhe >13 m nach §2 Abs. 3 Satz 2."}))
    edges.append(Edge(_n("35", "7.2"), _n("2", "3.7"), "references", "§35 Abs. 7 MBO", metadata={"reasoning": "Höhe des Gebäudes nach §2 Abs. 3 Satz 2."}))
    edges.append(Edge(_n("35", "8.1"), section, "supplements", "§35 Abs. 8 MBO", metadata={"reasoning": "Treppenräume müssen belüftet/entraucht werden können."}))
    edges.append(Edge(_n("35", "8.2"), _n("35", "8.1"), "sub_item_of", "§35 Abs. 8 MBO", metadata={"reasoning": "Zwei Alternativen: Fenster oder Öffnung zur Rauchableitung."}))
    for r in ("8.3", "8.4"):
        edges.append(Edge(_n("35", r), _n("35", "8.2"), "sub_item_of", "§35 Abs. 8 MBO", metadata={"reasoning": "Ausgestaltung der Alternativen."}))
    edges.append(Edge(_n("35", "8.5"), _n("35", "8.1"), "sub_item_of", "§35 Abs. 8 MBO", metadata={"reasoning": "Sonderanforderungen GK 4 und 5."}))
    edges.append(Edge(_n("35", "8.6"), _n("35", "8.1"), "sub_item_of", "§35 Abs. 8 MBO", metadata={"reasoning": "Mindestquerschnitt und Bedienbarkeit der Rauchabzugsöffnungen."}))

    return edges


def section_36_notwendige_flure() -> list[Edge]:
    """
    §36 Notwendige Flure, offene Gänge.
    """
    edges: list[Edge] = []
    section = _section_node("36")

    # Abs. 1: wann notwendige Flure erforderlich sind (und wann nicht)
    edges.append(Edge(_n("36", "1.1"), section, "supplements", "§36 Abs. 1 MBO", metadata={"reasoning": "Definition notwendige Flure und Anforderung an Anordnung/Ausbildung."}))
    edges.append(Edge(_n("36", "1.2"), section, "supplements", "§36 Abs. 1 MBO", metadata={"reasoning": "Notwendige Flure sind nicht erforderlich, wenn …"}))
    for r in ("1.3", "1.4", "1.5", "1.6"):
        edges.append(Edge(_n("36", r), _n("36", "1.2"), "sub_item_of", "§36 Abs. 1 MBO", metadata={"reasoning": "Fall ohne notwendige Flure (GK 1+2, innerhalb kleiner Nutzungseinheiten/Büros)."}))
    for gk in ("3.2", "3.3"):
        edges.append(Edge(_n("36", "1.3"), _n("2", gk), "references", "§36 Abs. 1 MBO", metadata={"reasoning": "Wohngebäude GK 1 und 2."}))
        edges.append(Edge(_n("36", "1.4"), _n("2", gk), "references", "§36 Abs. 1 MBO", metadata={"reasoning": "Sonstige Gebäude GK 1 und 2."}))
    edges.append(Edge(_n("36", "1.6"), _n("29", "2.1"), "references", "§36 Abs. 1 MBO", metadata={"reasoning": "Bezug zu Trennwänden §29 Abs. 2 Nr. 1."}))
    edges.append(Edge(_n("36", "1.6"), _n("33", "1.1"), "references", "§36 Abs. 1 MBO", metadata={"reasoning": "Bezug zu Rettungswegen §33 Abs. 1."}))

    # Abs. 2–3
    edges.append(Edge(_n("36", "2.1"), section, "supplements", "§36 Abs. 2 MBO", metadata={"reasoning": "Breite notwendiger Flure."}))
    edges.append(Edge(_n("36", "2.2"), _n("36", "2.1"), "sub_item_of", "§36 Abs. 2 MBO", metadata={"reasoning": "Folge von weniger als drei Stufen unzulässig."}))
    edges.append(Edge(_n("36", "3.1"), section, "supplements", "§36 Abs. 3 MBO", metadata={"reasoning": "Notwendige Flure in Rauchabschnitte unterteilen."}))
    for r in ("3.2", "3.3", "3.4"):
        edges.append(Edge(_n("36", r), _n("36", "3.1"), "sub_item_of", "§36 Abs. 3 MBO", metadata={"reasoning": "Länge der Rauchabschnitte, Anschluss an Roh-/Unterdecke, maximale Länge bei nur einer Fluchtrichtung."}))
    edges.append(Edge(_n("36", "3.5"), _n("36", "3.1"), "exception_of", "§36 Abs. 3 MBO", metadata={"reasoning": "Sätze 1–4 gelten nicht für offene Gänge nach Absatz 5."}))
    edges.append(Edge(_n("36", "3.5"), _n("36", "4.1"), "references", "§36 Abs. 3 MBO", metadata={"reasoning": "Bezug: offene Gänge nach Absatz 5."}))

    # Abs. 4–6
    edges.append(Edge(_n("36", "4.1"), section, "supplements", "§36 Abs. 4 MBO", metadata={"reasoning": "Wände notwendiger Flure feuerhemmend/feuerbeständig."}))
    for r in ("4.2", "4.3", "4.4"):
        edges.append(Edge(_n("36", r), _n("36", "4.1"), "sub_item_of", "§36 Abs. 4 MBO", metadata={"reasoning": "Ausbildung der Wände und Öffnungen (bis Roh-/Unterdecke, Abschlüsse)."}))
    edges.append(Edge(_n("36", "5.1"), section, "supplements", "§36 Abs. 5 MBO", metadata={"reasoning": "Wände/Brüstungen notwendiger Flure mit nur einer Fluchtrichtung als offene Gänge vor Außenwänden."}))
    edges.append(Edge(_n("36", "5.2"), _n("36", "5.1"), "sub_item_of", "§36 Abs. 5 MBO", metadata={"reasoning": "Fenster in Außenwänden ab Brüstungshöhe 0,90 m zulässig."}))
    edges.append(Edge(_n("36", "6.1"), section, "supplements", "§36 Abs. 6 MBO", metadata={"reasoning": "Bekleidungen/Unterdecken/Dämmstoffe in notwendigen Fluren und offenen Gängen."}))
    for r in ("6.2", "6.3"):
        edges.append(Edge(_n("36", r), _n("36", "6.1"), "sub_item_of", "§36 Abs. 6 MBO", metadata={"reasoning": "Nichtbrennbare Baustoffe oder Bekleidung erforderlich."}))

    return edges


def section_37_fenster_tueren_oeffnungen() -> list[Edge]:
    """
    §37 Fenster, Türen, sonstige Öffnungen.
    """
    edges: list[Edge] = []
    section = _section_node("37")

    # Abs. 1–5: mostly simple blocks
    edges.append(Edge(_n("37", "1.1"), section, "supplements", "§37 Abs. 1 MBO", metadata={"reasoning": "Vorrichtungen zur Reinigung von Fensterflächen."}))
    edges.append(Edge(_n("37", "2.1"), section, "supplements", "§37 Abs. 2 MBO", metadata={"reasoning": "Kennzeichnung von Glasflächen bis zum Fußboden."}))
    edges.append(Edge(_n("37", "2.2"), _n("37", "2.1"), "sub_item_of", "§37 Abs. 2 MBO", metadata={"reasoning": "Weitere Schutzmaßnahmen bei größeren Glasflächen."}))
    edges.append(Edge(_n("37", "3.1"), section, "supplements", "§37 Abs. 3 MBO", metadata={"reasoning": "Mindestbreite von Eingangstüren von Wohnungen mit Aufzügen."}))
    edges.append(Edge(_n("37", "3.1"), _n("39", "4.1"), "references", "§37 Abs. 3 MBO", metadata={"reasoning": "Wohnungen, die über Aufzüge erreichbar sein müssen — Bezug §39."}))
    edges.append(Edge(_n("37", "4.1"), section, "supplements", "§37 Abs. 4 MBO", metadata={"reasoning": "Kellergeschosse ohne Fenster: Öffnung ins Freie zur Rauchableitung."}))
    edges.append(Edge(_n("37", "4.2"), _n("37", "4.1"), "sub_item_of", "§37 Abs. 4 MBO", metadata={"reasoning": "Gemeinsame Kellerlichtschächte unzulässig."}))
    edges.append(Edge(_n("37", "5.1"), section, "supplements", "§37 Abs. 5 MBO", metadata={"reasoning": "Fenster als Rettungswege: Mindestgröße und Anordnung."}))
    edges.append(Edge(_n("37", "5.2"), _n("37", "5.1"), "sub_item_of", "§37 Abs. 5 MBO", metadata={"reasoning": "Zusatzanforderungen bei Fenstern in Dachschrägen/Dachaufbauten."}))
    edges.append(Edge(_n("37", "5.1"), _n("33", "2.2"), "references", "§37 Abs. 5 MBO", metadata={"reasoning": "Text: Fenster als Rettungswege nach §33 Abs. 2 Satz 2."}))

    return edges


def section_38_umwehrungen() -> list[Edge]:
    """
    §38 Umwehrungen — Absturzsicherungen an Flächen, Treppen, Dächern.
    """
    edges: list[Edge] = []
    section = _section_node("38")

    # Abs. 1: Liste der zu sichernden Flächen/Öffnungen
    edges.append(Edge(_n("38", "1.1"), section, "supplements", "§38 Abs. 1 MBO", metadata={"reasoning": "Flächen/Öffnungen, die zu umwehren oder mit Brüstungen zu versehen sind."}))
    for r in ("1.2", "1.3", "1.4", "1.5", "1.6", "1.7", "1.8"):
        edges.append(Edge(_n("38", r), _n("38", "1.1"), "sub_item_of", "§38 Abs. 1 MBO", metadata={"reasoning": "Konkreter Fall für notwendige Umwehrung/Brüstung."}))

    # Abs. 2–4
    for r in ("2.1", "2.2", "2.3", "3.1", "3.2"):
        edges.append(Edge(_n("38", r), section, "supplements", "§38 Abs. 2–3 MBO", metadata={"reasoning": "Abdeckungen von Schächten, Sicherung von Fensterbrüstungen."}))
    edges.append(Edge(_n("38", "4.1"), section, "supplements", "§38 Abs. 4 MBO", metadata={"reasoning": "Mindesthöhen anderer notwendiger Umwehrungen."}))
    edges.append(Edge(_n("38", "4.2"), _n("38", "4.1"), "sub_item_of", "§38 Abs. 4 MBO", metadata={"reasoning": "Höhe 0,90 m für Umwehrungen bei 1–12 m Absturzhöhe."}))
    edges.append(Edge(_n("38", "4.3"), _n("38", "4.1"), "sub_item_of", "§38 Abs. 4 MBO", metadata={"reasoning": "Höhe 1,10 m für Umwehrungen bei >12 m Absturzhöhe."}))

    return edges


def section_39_aufzuege() -> list[Edge]:
    """
    §39 Aufzüge — Fahrschächte, Ausnahmen, GK-Anforderungen, Höhe §2.
    """
    edges: list[Edge] = []
    section = _section_node("39")
    edges.append(Edge(_n("39", "1.1"), section, "supplements", "§39 Abs. 1 MBO", metadata={"reasoning": "Aufzüge im Innern: eigene Fahrschächte zur Brandausbreitungsbegrenzung."}))
    edges.append(Edge(_n("39", "1.2"), section, "supplements", "§39 Abs. 1 MBO", metadata={"reasoning": "Bis zu drei Aufzüge in einem Fahrschacht."}))
    edges.append(Edge(_n("39", "1.3"), section, "supplements", "§39 Abs. 1 MBO", metadata={"reasoning": "Aufzüge ohne eigene Fahrschächte zulässig, wenn …"}))
    for r in ("1.4", "1.5", "1.6", "1.7"):
        edges.append(Edge(_n("39", r), _n("39", "1.3"), "sub_item_of", "§39 Abs. 1 MBO", metadata={"reasoning": "Fall: innerhalb Treppenraum, geschossübergreifende Räume, offen verbundene Geschosse, GK 1+2."}))
    edges.append(Edge(_n("39", "1.4"), _n("35", "1.1"), "references", "§39 Abs. 1 MBO", metadata={"reasoning": "Text: innerhalb eines notwendigen Treppenraumes — §35."}))
    for gk in ("3.2", "3.3"):
        edges.append(Edge(_n("39", "1.7"), _n("2", gk), "references", "§39 Abs. 1 MBO", metadata={"reasoning": "Gebäude der Gebäudeklassen 1 und 2."}))
    edges.append(Edge(_n("39", "2.1"), section, "supplements", "§39 Abs. 2 MBO", metadata={"reasoning": "Fahrschachtwände: Anforderungen nach GK."}))
    for r, gk in (("2.2", "3.6"), ("2.3", "3.5"), ("2.4", "3.4")):
        edges.append(Edge(_n("39", r), _n("39", "2.1"), "sub_item_of", "§39 Abs. 2 MBO", metadata={"reasoning": "GK-spezifische Anforderung an Fahrschachtwände."}))
        edges.append(Edge(_n("39", r), _n("2", gk), "references", "§39 Abs. 2 MBO", metadata={"reasoning": "Gebäudeklasse laut Text."}))
    edges.append(Edge(_n("39", "2.5"), _n("39", "2.1"), "sub_item_of", "§39 Abs. 2 MBO", metadata={"reasoning": "Fahrschachttüren/Öffnungen so herstellen, dass Abs. 1 Satz 1 nicht beeinträchtigt wird."}))
    for r in ("3.1", "3.2", "3.3"):
        edges.append(Edge(_n("39", r), section, "supplements", "§39 Abs. 3 MBO", metadata={"reasoning": "Fahrschächte: Lüftung, Rauchableitung."}))
    edges.append(Edge(_n("39", "4.1"), section, "supplements", "§39 Abs. 4 MBO", metadata={"reasoning": "Gebäude Höhe >13 m nach §2 Abs. 3 Satz 2: Aufzüge in ausreichender Zahl."}))
    edges.append(Edge(_n("39", "4.1"), _n("2", "3.7"), "references", "§39 Abs. 4 MBO", metadata={"reasoning": "Höhe nach § 2 Abs. 3 Satz 2."}))
    for r in ("4.2", "4.3", "4.4"):
        edges.append(Edge(_n("39", r), _n("39", "4.1"), "sub_item_of", "§39 Abs. 4 MBO", metadata={"reasoning": "Mindestens ein Aufzug für Kinderwagen/Rollstuhl/Krankentrage; stufenlos erreichbar; Haltestellen."}))
    for r in ("5.1", "5.2", "5.3"):
        edges.append(Edge(_n("39", r), section, "supplements", "§39 Abs. 5 MBO", metadata={"reasoning": "Fahrkorbgrößen, Türen, Bewegungsfläche."}))
    return edges


def section_40_leitungsanlagen() -> list[Edge]:
    """
    §40 Leitungsanlagen, Installationsschächte — Durchführung durch Bauteile; Ausnahmen; Bezug §35, §36, §41.
    """
    edges: list[Edge] = []
    section = _section_node("40")
    edges.append(Edge(_n("40", "1.1"), section, "supplements", "§40 Abs. 1 MBO", metadata={"reasoning": "Leitungen durch raumabschließende Bauteile mit Feuerwiderstand nur wenn Brandausbreitung nicht zu befürchten."}))
    for r in ("1.2", "1.3", "1.4"):
        edges.append(Edge(_n("40", r), _n("40", "1.1"), "exception_of", "§40 Abs. 1 MBO", metadata={"reasoning": "Dies gilt nicht: GK 1+2, innerhalb Wohnungen, Nutzungseinheit ≤400 m² in ≤2 Geschossen."}))
    for gk in ("3.2", "3.3"):
        edges.append(Edge(_n("40", "1.2"), _n("2", gk), "references", "§40 Abs. 1 MBO", metadata={"reasoning": "Gebäude der Gebäudeklassen 1 und 2."}))
    edges.append(Edge(_n("40", "2.1"), section, "supplements", "§40 Abs. 2 MBO", metadata={"reasoning": "In Treppenräumen, Räumen nach §35 Abs. 3 Satz 2, notwendigen Fluren: Leitungen nur wenn Rettungsweg nutzbar."}))
    edges.append(Edge(_n("40", "2.1"), _n("35", "1.1"), "references", "§40 Abs. 2 MBO", metadata={"reasoning": "Notwendige Treppenräume, Räume nach §35 Abs. 3 Satz 2."}))
    edges.append(Edge(_n("40", "2.1"), _n("36", "1.1"), "references", "§40 Abs. 2 MBO", metadata={"reasoning": "Notwendige Flure."}))
    edges.append(Edge(_n("40", "3.1"), section, "supplements", "§40 Abs. 3 MBO", metadata={"reasoning": "Installationsschächte/-kanäle: Abs. 1 und §41 Abs. 2 Satz 1, Abs. 3 entsprechend."}))
    edges.append(Edge(_n("40", "3.1"), _n("41", "2.1"), "references", "§40 Abs. 3 MBO", metadata={"reasoning": "§ 41 Abs. 2 Satz 1 und Abs. 3."}))
    return edges


def section_41_lueftungsanlagen() -> list[Edge]:
    """
    §41 Lüftungsanlagen — Abs. 2 und 3 gelten nicht für GK 1+2, Wohnungen, kleine Nutzungseinheiten.
    """
    edges: list[Edge] = []
    section = _section_node("41")
    edges.append(Edge(_n("41", "1.1"), section, "supplements", "§41 Abs. 1 MBO", metadata={"reasoning": "Lüftungsanlagen betriebssicher und brandsicher."}))
    edges.append(Edge(_n("41", "2.1"), section, "supplements", "§41 Abs. 2 MBO", metadata={"reasoning": "Lüftungsleitungen: nichtbrennbar; Überbrückung raumabschließender Bauteile."}))
    edges.append(Edge(_n("41", "2.2"), _n("41", "2.1"), "sub_item_of", "§41 Abs. 2 MBO", metadata={"reasoning": "Überbrückung nur wenn Brandausbreitung nicht zu befürchten."}))
    edges.append(Edge(_n("41", "3.1"), section, "supplements", "§41 Abs. 3 MBO", metadata={"reasoning": "Gerüche und Staub nicht in andere Räume übertragen."}))
    for r in ("4.1", "4.2", "4.3"):
        edges.append(Edge(_n("41", r), section, "supplements", "§41 Abs. 4 MBO", metadata={"reasoning": "Nicht in Abgasanlagen; Abluft ins Freie; keine Fremdeinrichtungen in Lüftungsleitungen."}))
    edges.append(Edge(_n("41", "5.1"), section, "supplements", "§41 Abs. 5 MBO", metadata={"reasoning": "Abs. 2 und 3 gelten nicht für … (Ausnahmen)."}))
    for r in ("5.2", "5.3", "5.4"):
        edges.append(Edge(_n("41", r), _n("41", "2.1"), "exception_of", "§41 Abs. 5 MBO", metadata={"reasoning": "Ausnahme: GK 1+2, innerhalb Wohnungen, Nutzungseinheit ≤400 m²."}))
        edges.append(Edge(_n("41", r), _n("41", "3.1"), "exception_of", "§41 Abs. 5 MBO", metadata={"reasoning": "Gleiche Ausnahme für Abs. 3."}))
    for gk in ("3.2", "3.3"):
        edges.append(Edge(_n("41", "5.2"), _n("2", gk), "references", "§41 Abs. 5 MBO", metadata={"reasoning": "Gebäude der Gebäudeklassen 1 und 2."}))
    edges.append(Edge(_n("41", "6.1"), section, "supplements", "§41 Abs. 6 MBO", metadata={"reasoning": "Raumlufttechnische Anlagen und Warmluftheizungen: Abs. 1–5 entsprechend."}))
    return edges


def section_42_feuerungsanlagen() -> list[Edge]:
    """§42 Feuerungsanlagen, Wärmeerzeugung — betriebssicher, brandsicher; Abgasanlagen; Brennstoffe."""
    edges: list[Edge] = []
    section = _section_node("42")
    edges.append(Edge(_n("42", "1.1"), section, "supplements", "§42 Abs. 1 MBO", metadata={"reasoning": "Feuerungsanlagen betriebssicher und brandsicher."}))
    edges.append(Edge(_n("42", "2.1"), section, "supplements", "§42 Abs. 2 MBO", metadata={"reasoning": "Feuerstätten in Räumen nur wenn keine Gefahren."}))
    edges.append(Edge(_n("42", "3.1"), section, "supplements", "§42 Abs. 3 MBO", metadata={"reasoning": "Abgase abführen; Abgasanlagen in Zahl und Lage."}))
    for r in ("3.2", "3.3"):
        edges.append(Edge(_n("42", r), _n("42", "3.1"), "sub_item_of", "§42 Abs. 3 MBO", metadata={"reasoning": "Anschluss Feuerstätten; leicht reinigbar."}))
    edges.append(Edge(_n("42", "3.4"), _n("42", "3.1"), "exception_of", "§42 Abs. 3 MBO", metadata={"reasoning": "Sätze 1–3 gelten nicht für Feuerungsanlagen ohne Abgaseinrichtung (Stand der Technik)."}))
    edges.append(Edge(_n("42", "4.1"), section, "supplements", "§42 Abs. 4 MBO", metadata={"reasoning": "Behälter und Rohrleitungen für brennbare Gase/Flüssigkeiten."}))
    edges.append(Edge(_n("42", "4.2"), _n("42", "4.1"), "sub_item_of", "§42 Abs. 4 MBO", metadata={"reasoning": "Aufstellung/Lagerung ohne Gefahren."}))
    edges.append(Edge(_n("42", "5.1"), section, "supplements", "§42 Abs. 5 MBO", metadata={"reasoning": "Ortsfeste Verbrennungsmotoren, BHKW, Brennstoffzellen etc.: Abs. 1–3 entsprechend."}))
    return edges


def section_43_sanitaer_wasserzaehler() -> list[Edge]:
    """§43 Sanitäre Anlagen, Wasserzähler — fensterlose Bäder/Toiletten; Wasserzähler je Wohnung."""
    edges: list[Edge] = []
    section = _section_node("43")
    edges.append(Edge(_n("43", "1.1"), section, "supplements", "§43 Abs. 1 MBO", metadata={"reasoning": "Fensterlose Bäder und Toiletten nur bei wirksamer Lüftung."}))
    edges.append(Edge(_n("43", "2.1"), section, "supplements", "§43 Abs. 2 MBO", metadata={"reasoning": "Jede Wohnung muss eigenen Wasserzähler haben."}))
    edges.append(Edge(_n("43", "2.2"), _n("43", "2.1"), "exception_of", "§43 Abs. 2 MBO", metadata={"reasoning": "Nicht bei Nutzungsänderung, wenn nur mit unverhältnismäßigem Mehraufwand."}))
    return edges


def section_44_kleinklaeranlagen_gruben() -> list[Edge]:
    """§44 Kleinkläranlagen, Gruben — wasserdicht, Abdeckung, Entlüftung, Zuleitungen."""
    edges: list[Edge] = []
    section = _section_node("44")
    edges.append(Edge(_n("44", "1.1"), section, "supplements", "§44 Abs. 1 MBO", metadata={"reasoning": "Kleinkläranlagen, Gruben (lead)."}))
    for r in ("1.2", "1.3", "1.4", "1.5", "1.6"):
        edges.append(Edge(_n("44", r), _n("44", "1.1"), "sub_item_of", "§44 Abs. 1 MBO", metadata={"reasoning": "Wasser dicht, Abdeckung, Öffnungen vom Freien, Entlüftung, Zuleitungen."}))
    return edges


def section_45_abfallstoffe() -> list[Edge]:
    """§45 Aufbewahrung fester Abfallstoffe — GK 3–5: nur in Räumen mit Trennwänden/Decken, Abschlüssen, Entleerung, Lüftung."""
    edges: list[Edge] = []
    section = _section_node("45")
    edges.append(Edge(_n("45", "1.1"), section, "supplements", "§45 Abs. 1 MBO", metadata={"reasoning": "Feste Abfallstoffe in GK 3–5 nur in dafür bestimmten Räumen, wenn …"}))
    for r in ("1.2", "1.3", "1.4", "1.5"):
        edges.append(Edge(_n("45", r), _n("45", "1.1"), "sub_item_of", "§45 Abs. 1 MBO", metadata={"reasoning": "Trennwände/Decken, Öffnungen mit Abschlüssen, vom Freien entleerbar, Lüftung."}))
    for gk in ("3.4", "3.5", "3.6"):
        edges.append(Edge(_n("45", "1.1"), _n("2", gk), "references", "§45 Abs. 1 MBO", metadata={"reasoning": "Gebäudeklassen 3 bis 5."}))
    return edges


def section_46_blitzschutz() -> list[Edge]:
    """§46 Blitzschutzanlagen — bei Anlagen mit erhöhtem Blitzschlagrisiko."""
    edges: list[Edge] = []
    section = _section_node("46")
    edges.append(Edge(_n("46", "1.1"), section, "supplements", "§46 Abs. 1 MBO", metadata={"reasoning": "Blitzschutzanlagen bei Anlagen mit Blitzschlagrisiko oder schweren Folgen."}))
    return edges


def section_47_aufenthaltsraeume() -> list[Edge]:
    """§47 Aufenthaltsräume — Raumhöhe, Belichtung; Ausnahme Wohngebäude GK 1+2."""
    edges: list[Edge] = []
    section = _section_node("47")
    edges.append(Edge(_n("47", "1.1"), section, "supplements", "§47 Abs. 1 MBO", metadata={"reasoning": "Aufenthaltsräume: lichte Raumhöhe mind. 2,40 m."}))
    edges.append(Edge(_n("47", "1.2"), section, "supplements", "§47 Abs. 1 MBO", metadata={"reasoning": "Dachraum: mind. 2,20 m über mindestens Hälfte der Netto-Raumfläche."}))
    edges.append(Edge(_n("47", "1.3"), _n("47", "1.1"), "exception_of", "§47 Abs. 1 MBO", metadata={"reasoning": "Sätze 1 und 2 gelten nicht für Aufenthaltsräume in Wohngebäuden GK 1 und 2."}))
    edges.append(Edge(_n("47", "1.3"), _n("47", "1.2"), "exception_of", "§47 Abs. 1 MBO", metadata={"reasoning": "Gleiche Ausnahme für Satz 2."}))
    for gk in ("3.2", "3.3"):
        edges.append(Edge(_n("47", "1.3"), _n("2", gk), "references", "§47 Abs. 1 MBO", metadata={"reasoning": "Wohngebäude der Gebäudeklassen 1 und 2."}))
    edges.append(Edge(_n("47", "2.1"), section, "supplements", "§47 Abs. 2 MBO", metadata={"reasoning": "Belüftung und Tageslicht."}))
    edges.append(Edge(_n("47", "2.2"), _n("47", "2.1"), "sub_item_of", "§47 Abs. 2 MBO", metadata={"reasoning": "Fenster mind. 1/8 der Netto-Raumfläche."}))
    edges.append(Edge(_n("47", "3.1"), section, "supplements", "§47 Abs. 3 MBO", metadata={"reasoning": "Bestimmte Räume ohne Fenster zulässig (Belichtung verboten, Verkaufsräume, Gaststätten, etc.)."}))
    return edges


def section_48_wohnungen() -> list[Edge]:
    """§48 Wohnungen — Küche, Abstellräume, Bad, Rauchwarnmelder; Nutzungsänderung: §§ 6, 27, 28, 30, 31, 32 nicht anzuwenden."""
    edges: list[Edge] = []
    section = _section_node("48")
    for r in ("1.1", "1.2", "2.1", "3.1", "4.1", "4.2", "5.1"):
        edges.append(Edge(_n("48", r), section, "supplements", "§48 MBO", metadata={"reasoning": "Küche/Kochnische, Abstellräume, Bad/Toilette, Rauchwarnmelder, Nutzungsänderung."}))
    for ref_sec in ("6", "27", "28", "30", "31", "32"):
        edges.append(Edge(_n("48", "5.1"), _section_node(ref_sec), "references", "§48 Abs. 5 MBO", metadata={"reasoning": "Text: §§ 6, 27, 28, 30, 31 und 32 nicht anzuwenden bei Umbau/Nutzungsänderung."}))
    return edges


def section_49_stellplaetze_garagen() -> list[Edge]:
    """§49 Stellplätze, Garagen, Fahrräder — Verpflichtung; Ausnahme bei Teilung/Aufstockung/Dachausbau."""
    edges: list[Edge] = []
    section = _section_node("49")
    edges.append(Edge(_n("49", "1.1"), section, "supplements", "§49 Abs. 1 MBO", metadata={"reasoning": "Notwendige Stellplätze, Garagen, Abstellplätze Fahrräder auf Grundstück oder in zumutbarer Entfernung."}))
    edges.append(Edge(_n("49", "1.1"), _section_node("86"), "references", "§49 Abs. 1 MBO", metadata={"reasoning": "Text: § 86 Abs. 1 Nr. 4 (Stellplätze/Fahrräder)."}))
    edges.append(Edge(_n("49", "1.2"), _n("49", "1.1"), "exception_of", "§49 Abs. 1 MBO", metadata={"reasoning": "Verpflichtung entfällt bei Wohnungsteilung, Nutzungsänderung, Aufstockung, Dachausbau."}))
    edges.append(Edge(_n("49", "2.1"), section, "supplements", "§49 Abs. 2 MBO", metadata={"reasoning": "Gemeinde verwendet Geldbetrag für Ablösung für …"}))
    edges.append(Edge(_n("49", "2.2"), _n("49", "2.1"), "sub_item_of", "§49 Abs. 2 MBO", metadata={"reasoning": "Parkeinrichtungen herstellen oder instand halten."}))
    edges.append(Edge(_n("49", "2.3"), _n("49", "2.1"), "sub_item_of", "§49 Abs. 2 MBO", metadata={"reasoning": "Maßnahmen zur Entlastung vom ruhenden Verkehr."}))
    return edges


def section_50_barrierefrei() -> list[Edge]:
    """§50 Barrierefreies Bauen — multi-unit barrierefrei; öffentliche Anlagen; Abweichungen §67."""
    edges: list[Edge] = []
    section = _section_node("50")
    edges.append(Edge(_n("50", "1.1"), section, "supplements", "§50 Abs. 1 MBO", metadata={"reasoning": "Gebäude mit mehr als zwei Wohnungen: ein Geschoss barrierefrei erreichbar."}))
    edges.append(Edge(_n("50", "1.2"), section, "supplements", "§50 Abs. 1 MBO", metadata={"reasoning": "In diesen Wohnungen: Aufenthaltsräume, Toilette, Bad, Küche, Freisitz barrierefrei; §39 Abs. 4 unberührt."}))
    edges.append(Edge(_n("50", "1.2"), _n("39", "4.1"), "references", "§50 Abs. 1 MBO", metadata={"reasoning": "Text: § 39 Abs. 4 bleibt unberührt."}))
    edges.append(Edge(_n("50", "1.3"), _n("50", "1.1"), "exception_of", "§50 Abs. 1 MBO", metadata={"reasoning": "Sätze 1 und 2 gelten nicht bei Dachausbau, Aufstockung, Teilung von Wohnungen."}))
    edges.append(Edge(_n("50", "1.3"), _n("50", "1.2"), "exception_of", "§50 Abs. 1 MBO", metadata={"reasoning": "Gleiche Ausnahme."}))
    edges.append(Edge(_n("50", "2.1"), section, "supplements", "§50 Abs. 2 MBO", metadata={"reasoning": "Öffentlich zugängliche Anlagen: barrierefrei in Besucher-/Benutzerverkehr."}))
    edges.append(Edge(_n("50", "2.2"), section, "supplements", "§50 Abs. 2 MBO", metadata={"reasoning": "Dies gilt insbesondere für … (lead)."}))
    for i in range(3, 11):
        edges.append(Edge(_n("50", f"2.{i}"), _n("50", "2.2"), "sub_item_of", "§50 Abs. 2 MBO", metadata={"reasoning": "Kultur, Sport, Gesundheit, Büro, Verkauf, Stellplätze, Toiletten etc."}))
    edges.append(Edge(_n("50", "3.1"), section, "supplements", "§50 Abs. 3 MBO", metadata={"reasoning": "Anlagen für Menschen mit Behinderung/Betreuung: Abs. 2 Satz 3 und 4 entsprechend."}))
    edges.append(Edge(_n("50", "4.1"), section, "supplements", "§50 Abs. 4 MBO", metadata={"reasoning": "Abweichungen nach §67 von Abs. 1–3 bei unverhältnismäßigem Mehraufwand."}))
    edges.append(Edge(_n("50", "4.1"), _section_node("67"), "references", "§50 Abs. 4 MBO", metadata={"reasoning": "Text: Abweichungen nach § 67."}))
    for r in ("4.2", "4.3", "4.4", "4.5"):
        edges.append(Edge(_n("50", r), _n("50", "4.1"), "sub_item_of", "§50 Abs. 4 MBO", metadata={"reasoning": "Geländeverhältnisse, Aufzug, Bebauung, Sicherheit."}))
    return edges


def section_51_sonderbauten() -> list[Edge]:
    """§51 Sonderbauten — besondere Anforderungen/Erleichterungen; Bezug §3 Abs. 1; Liste 1.5–1.27."""
    edges: list[Edge] = []
    section = _section_node("51")
    edges.append(Edge(_n("51", "1.1"), section, "supplements", "§51 Abs. 1 MBO", metadata={"reasoning": "Sonderbauten (Überschrift)."}))
    edges.append(Edge(_n("51", "1.2"), section, "supplements", "§51 Abs. 1 MBO", metadata={"reasoning": "Besondere Anforderungen zur Verwirklichung der allgemeinen Anforderungen nach §3 Abs. 1."}))
    edges.append(Edge(_n("51", "1.2"), _n("3", "3.1"), "references", "§51 Abs. 1 MBO", metadata={"reasoning": "Text: allgemeine Anforderungen nach § 3 Abs. 1."}))
    edges.append(Edge(_n("51", "1.3"), section, "supplements", "§51 Abs. 1 MBO", metadata={"reasoning": "Erleichterungen können gestattet werden, soweit nicht bedarf."}))
    edges.append(Edge(_n("51", "1.4"), section, "supplements", "§51 Abs. 1 MBO", metadata={"reasoning": "Anforderungen und Erleichterungen können sich erstrecken auf … (lead)."}))
    for i in range(5, 28):
        edges.append(Edge(_n("51", f"1.{i}"), _n("51", "1.4"), "sub_item_of", "§51 Abs. 1 MBO", metadata={"reasoning": "Themenbereich (Grundstück, Abstände, Brandschutz, Aufzüge, Treppen, Flure, Rettungswege, etc.)."}))
    return edges


# Procedure sections (§52–§86): row IDs per section (from inventory) for "what's needed" (approval, who, what to submit)
_PROCEDURE_ROWS = {
    "52": ["1.1"],
    "53": ["1.1", "1.2", "1.3", "1.4", "1.5", "1.6", "2.1", "2.2"],
    "54": ["1.1", "1.2", "1.3", "2.1", "2.2", "2.3"],
    "55": ["1.1", "1.2", "1.3", "2.1"],
    "56": ["1.1", "1.2", "1.3", "2.1", "2.2", "2.3", "2.4"],
    "57": ["1.1", "1.2", "1.3", "1.4", "1.5", "2.1", "3.1", "3.2", "3.3"],
    "58": ["1.1", "2.1", "2.2", "3.1", "4.1", "4.2"],
    "59": ["1.1", "2.1"],
    "60": ["1.1", "1.2", "1.3", "1.4", "1.5", "1.6", "1.7", "1.8", "1.9", "1.10"],
    "61": ["1.1", "1.2", "1.3", "1.4", "1.5", "1.6", "1.7", "1.8", "1.9", "1.10", "1.11", "1.12", "1.13", "1.14", "1.15", "1.16", "2.1", "2.2"],
    "62": ["1.1", "1.2", "1.3"],
    "63": ["1.1", "1.2", "1.3", "1.4", "2.1", "2.2"],
    "64": ["1.1", "1.2", "1.3", "1.4", "1.5", "3.1", "3.2", "3.3", "3.4", "3.5", "3.6", "3.7", "4.1"],
    "65": ["1.1", "1.2", "1.3", "1.4", "2.1", "2.2", "2.3", "3.1", "3.2", "3.3", "3.4", "4.1"],
    "66": ["1.1", "1.2", "2.1", "2.2", "2.3", "2.4", "2.5", "2.6", "2.7", "2.8", "2.9", "2.10", "3.1", "3.2", "3.3", "3.4", "3.5", "3.6", "3.7", "3.8", "4.1", "4.2", "4.3", "4.4", "4.5"],
    "67": ["1.1", "1.2", "1.3", "1.4", "1.5", "2.1", "2.2", "3.1", "3.2", "4.1"],
    "68": ["1.1", "2.1", "2.2", "3.1", "4.1"],
    "69": ["1.1", "1.2", "1.3", "1.4", "1.5", "2.1", "2.2", "3.1", "3.2", "3.3", "3.4", "3.5"],
    "70": ["1.1", "1.2", "1.3", "1.4", "2.1", "2.2", "3.1", "3.2", "3.3", "3.4", "3.5", "4.1", "4.2", "4.3", "4.4", "4.5", "4.6", "4.7", "4.8", "4.9", "5.1", "5.2", "5.3", "5.4", "6.1"],
    "71": ["1.1", "2.1", "3.1", "3.2", "3.3", "4.1", "4.2"],
    "72": ["1.1", "1.2", "1.3", "1.4", "1.5", "1.6", "1.7", "2.1", "3.1", "4.1", "5.1", "6.1", "6.2", "6.3", "6.4", "7.1", "7.2", "8.1"],
    "73": ["1.1", "1.2", "1.3", "1.4", "2.1", "2.2"],
    "74": ["74.1"],  # inventory has 74.1
    "75": ["1.1", "1.2", "1.3"],
    "76": ["1.1", "1.2", "2.1", "2.2", "2.3", "2.4", "2.5", "2.6", "2.7", "2.8", "2.9", "3.1", "3.2", "4.1", "5.1", "5.2", "5.3", "6.1", "6.2", "7.1", "7.2", "7.3", "8.1", "8.2", "10.1"],
    "77": ["1.1", "1.2", "1.3", "1.4", "1.5", "1.6", "1.7", "2.1", "3.1", "3.2", "3.3", "3.4", "3.5", "3.6", "4.1", "4.2", "5.1", "5.2"],
    "78": ["1.1"],
    "79": ["1.1", "1.2", "1.3", "1.4", "1.5", "1.6", "2.1"],
    "80": ["1.1", "1.2", "1.3"],
    "81": ["1.1", "2.1", "2.2", "2.3", "2.4", "3.1", "4.1", "5.1"],
    "82": ["1.1", "1.2", "2.1", "2.2", "2.3", "2.4", "2.5", "2.6"],
    "83": ["1.1", "1.2", "2.1", "3.1", "3.2", "3.3", "3.4", "4.1", "4.2", "4.3", "4.4", "5.1"],
    "84": ["1.1", "1.2", "1.3", "1.4", "1.5", "1.6", "1.7", "1.8", "1.9", "1.10", "1.11", "1.12", "1.13", "2.1", "2.2", "2.3", "2.4", "3.1", "4.1"],
    "85": ["1.1", "1.2", "1.3", "1.4", "1.5", "1.6", "1.7", "2.1", "2.2", "2.3", "2.4", "2.5", "2.6", "2.7", "2.8", "2.9", "2.10", "2.11", "2.12", "2.13"],
    "86": ["1.1", "1.2", "1.3", "1.4", "1.5", "1.6", "1.7", "1.8", "2.1", "2.2"],
}


def procedure_sections_edges() -> list[Edge]:
    """
    §52–§86 (procedure, authorities, approval): content nodes supplement section anchor.
    Enables answering 'what's needed' (who is responsible, what to submit, when approval required, Abweichungen).
    """
    edges: list[Edge] = []
    for sec, rows in _PROCEDURE_ROWS.items():
        section = _section_node(sec)
        for row in rows:
            edges.append(
                Edge(
                    _n(sec, row),
                    section,
                    "supplements",
                    f"§{sec} MBO",
                    metadata={"reasoning": "Procedure/approval: content under this section."},
                )
            )
    return edges


def edges() -> list[Edge]:
    """All MBO section-defined edges (section by section)."""
    return (
        section_1_anwendungsbereich()
        + section_2_begriffe()
        + section_3_allgemeine_anforderungen()
        + section_4_bebauung_grundstuecke()
        + section_5_zugaenge_zufahrten()
        + section_6_abstandsflaechen()
        + section_7_teilung_grundstuecke()
        + section_8_nicht_ueberbaute_flaechen()
        + section_9_gestaltung()
        + section_10_aussenwerbung_warenautomaten()
        + section_11_baustelle()
        + section_12_standsicherheit()
        + section_13_schutz_schaedliche_einfluesse()
        + section_14_brandschutz()
        + section_15_waerme_schall_erschuetterung()
        + section_16_verkehrssicherheit()
        + section_16a_bauarten()
        + section_16b_bauprodukte()
        + section_16c_ce_bauprodukte()
        + section_17_verwendbarkeitsnachweise()
        + section_18_zulassung()
        + section_19_pruefzeugnis()
        + section_20_nachweis_einzelfall()
        + section_21_uebereinstimmungsbestaetigung()
        + section_22_uebereinstimmungserklaerung()
        + section_23_zertifizierung()
        + section_24_pruefstellen()
        + section_25_sachkunde_sorgfalt()
        + section_26_brandverhalten_baustoffe_bauteile()
        + section_27_tragende_waende_stuetzen()
        + section_28_aussenwaende()
        + section_29_trennwaende()
        + section_30_brandwaende()
        + section_31_decken()
        + section_32_daecher()
        + section_33_rettungswege()
        + section_34_treppen()
        + section_35_treppenraeume()
        + section_36_notwendige_flure()
        + section_37_fenster_tueren_oeffnungen()
        + section_38_umwehrungen()
        + section_39_aufzuege()
        + section_40_leitungsanlagen()
        + section_41_lueftungsanlagen()
        + section_42_feuerungsanlagen()
        + section_43_sanitaer_wasserzaehler()
        + section_44_kleinklaeranlagen_gruben()
        + section_45_abfallstoffe()
        + section_46_blitzschutz()
        + section_47_aufenthaltsraeume()
        + section_48_wohnungen()
        + section_49_stellplaetze_garagen()
        + section_50_barrierefrei()
        + section_51_sonderbauten()
        + procedure_sections_edges()
    )
