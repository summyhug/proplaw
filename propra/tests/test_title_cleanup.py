import propra.graph.map_to_mbo as map_to_mbo
from propra.data.generate_lbo_inventory import _clean_body_text
from propra.data.generate_lbo_inventory import _clean_section_title
from propra.data.generate_lbo_inventory import _load_sectioned_inventory_sections
from propra.data.generate_lbo_inventory import _pick_best_title
from propra.data.generate_lbo_inventory import _preprocess_no_dash
from propra.data.generate_lbo_inventory import _trim_bauo_he_text
from propra.data.generate_lbo_inventory import _trim_hbauo_text
from propra.data.generate_lbo_inventory import _trim_to_occurrence
from propra.data.generate_lbo_inventory import _trim_to_second_section_one_line
from propra.data.generate_baybo_inventory_v2 import infer_section_type
from propra.graph.map_to_mbo import _best_mbo_match
from propra.graph.map_to_mbo import _clean_title
from propra.graph.map_to_mbo import _extract_titles
from propra.graph.map_to_mbo import _find_state_inventory


def test_clean_section_title_strips_common_extraction_noise():
    assert _clean_section_title("Seite 38 von 88 Umwehrungen") == "Umwehrungen"
    assert _clean_section_title("Bebauung der Grundstücke 2130-1 7") == "Bebauung der Grundstücke"
    assert _clean_section_title("Kleinkläranlagen, Abwasserbehälter 07.07") == "Kleinkläranlagen, Abwasserbehälter"
    assert _clean_section_title("Anwendungsbereich 1 2") == "Anwendungsbereich"
    assert _clean_section_title(
        "Abweichungen Achter Teil Übergangs- und Schlussvorschriften"
    ) == "Abweichungen"


def test_clean_body_text_strips_inline_artifacts_and_heading_tails():
    assert _clean_body_text(
        "Ist ein Gebäude nach Absatz 5 Satz 2 an eine Grenze gebaut, so darf der Abstand weiter verringert © 2026 Wolters Kluwer Deutschland GmbH 14 / 79 gespeichert: 11.03.2026, 19:09 Uhr werden, wenn der Nachbar zugestimmt hat."
    ) == (
        "Ist ein Gebäude nach Absatz 5 Satz 2 an eine Grenze gebaut, so darf der Abstand weiter verringert werden, wenn der Nachbar zugestimmt hat"
    )
    assert _clean_body_text(
        "Die Bauaufsichtsbehörde informiert den Bauherrn unverzüglich. Achter Teil Übergangs- und Schlussvorschriften."
    ) == "Die Bauaufsichtsbehörde informiert den Bauherrn unverzüglich"


def test_clean_body_text_drops_heading_only_rows():
    assert _clean_body_text("Abschnitt III Genehmigungsverfahren.") == ""


def test_pick_best_title_prefers_clean_title_over_body_or_footnote_bleed():
    assert _pick_best_title(["Anwendungsbereich 1 2", "Anwendungsbereich"]) == "Anwendungsbereich"
    assert _pick_best_title(
        ["Allgemeine Anforderungen", "Allgemeine Anforderungen Anlagen sind so"]
    ) == "Allgemeine Anforderungen"
    assert _pick_best_title(
        [
            "Garagen, Stellplätze für Kraftfahrzeuge, Abstellplätze für Fahrrä-",
            "Garagen, Stellplätze für Kraftfahrzeuge, Abstellplätze für Fahrräder",
        ]
    ) == "Garagen, Stellplätze für Kraftfahrzeuge, Abstellplätze für Fahrräder"
    assert _pick_best_title(
        [
            "Inkrafttreten Anlage zu § 63: Baugenehmigungsfreie Vorhaben nach § 63",
            "Inkrafttreten 1 2 Dieses Gesetz tritt einen Monat nach der Verkündung in Kraft. Anlage",
        ]
    ) == "Inkrafttreten"


def test_trim_to_occurrence_keeps_text_from_requested_marker_instance():
    text = "\n".join(
        [
            "prefix",
            "§ 1 Anwendungsbereich",
            "toc",
            "§ 1 Anwendungsbereich",
            "toc2",
            "§ 1 Anwendungsbereich 1 2",
            "body",
        ]
    )

    assert _trim_to_occurrence(text, "§ 1 Anwendungsbereich", 3).startswith("§ 1 Anwendungsbereich 1 2")


def test_trim_bauo_he_text_drops_appendix_after_paragraph_93():
    text = "\n".join(
        [
            "intro",
            "§ 1 Anwendungsbereich",
            "toc",
            "§ 1 Anwendungsbereich 1 2",
            "(1) Dieses Gesetz gilt.",
            "§ 93 Inkrafttreten 1 2 Dieses Gesetz tritt in Kraft. Anlage",
            "- Seite 85 von 97 (zu § 63) Baugenehmigungsfreie Vorhaben nach § 63",
            "1.1 Gebäude ...",
        ]
    )

    trimmed = _trim_bauo_he_text(text)

    assert trimmed.splitlines() == [
        "§ 1 Anwendungsbereich 1 2",
        "(1) Dieses Gesetz gilt.",
        "§ 93 Inkrafttreten 1 2 Dieses Gesetz tritt in Kraft.",
    ]


def test_trim_hbauo_text_keeps_official_body_and_drops_annex():
    text = "\n".join(
        [
            "intro",
            "§ 1 - Anwendungsbereich",
            "toc 1",
            "§ 1 Anwendungsbereich",
            "toc 2",
            "§ 87 Übergangsvorschriften Erster Teil Allgemeine Vorschriften",
            "§ 1 Anwendungsbereich",
            "(1) Dieses Gesetz gilt.",
            "§ 87 Übergangsvorschriften",
            "(1) Übergangsrecht.",
            "Anlage - Verfahrensfreie Vorhaben nach § 61",
            "I - Errichtung",
        ]
    )

    trimmed = _trim_hbauo_text(text)

    assert trimmed.splitlines() == [
        "§ 1 Anwendungsbereich",
        "(1) Dieses Gesetz gilt.",
        "§ 87 Übergangsvorschriften",
        "(1) Übergangsrecht.",
    ]


def test_trim_to_second_section_one_line_skips_repeated_toc_block():
    text = "\n".join(
        [
            "Titel",
            "§ 1 Anwendungsbereich",
            "§ 2 Begriffe",
            "§ 1 Anwendungsbereich 1 2",
            "(1) Dieses Gesetz gilt.",
        ]
    )

    assert _trim_to_second_section_one_line(text).splitlines() == [
        "§ 1 Anwendungsbereich 1 2",
        "(1) Dieses Gesetz gilt.",
    ]


def test_preprocess_no_dash_merges_bare_section_line_with_following_title():
    txt = "\n".join(
        [
            "§ 56",
            "- Seite 52 von 97 Bauherrschaft",
            "(1) Der Bauherrschaft obliegen Anzeigen.",
        ]
    )

    out = _preprocess_no_dash(txt, {"56": "Bauherrschaft"})

    assert out.splitlines()[:2] == [
        "§ 56 Bauherrschaft",
        "(1) Der Bauherrschaft obliegen Anzeigen.",
    ]


def test_preprocess_no_dash_does_not_split_footnote_only_suffix_but_splits_real_inline_body():
    txt = "\n".join(
        [
            "§ 1 Anwendungsbereich 1 2",
            "(1) Dieses Gesetz gilt.",
            "§ 93 Inkrafttreten 1 2 Dieses Gesetz tritt einen Monat nach der Verkündung in Kraft und regelt außerdem die Übergangsfolge für bereits begonnene Verfahren.",
        ]
    )

    out = _preprocess_no_dash(
        txt,
        {"1": "Anwendungsbereich", "93": "Inkrafttreten"},
    )

    assert out.splitlines()[:4] == [
        "§ 1 Anwendungsbereich 1 2",
        "(1) Dieses Gesetz gilt.",
        "§ 93 Inkrafttreten",
        "1 2 Dieses Gesetz tritt einen Monat nach der Verkündung in Kraft und regelt außerdem die Übergangsfolge für bereits begonnene Verfahren.",
    ]


def test_preprocess_no_dash_splits_short_header_noise_suffixes():
    txt = "\n".join(
        [
            "§ 1 Anwendungsbereich Fassung vom 29.10.2011 Seite 3 von 45 SächsBO",
            "(1) Dieses Gesetz gilt.",
            "§ 3 Allgemeine Anforderungen Zweiter Teil Das Grundstück und seine Bebauung",
        ]
    )

    out = _preprocess_no_dash(
        txt,
        {"1": "Anwendungsbereich", "3": "Allgemeine Anforderungen"},
    )

    assert out.splitlines() == [
        "§ 1 Anwendungsbereich",
        "(1) Dieses Gesetz gilt.",
        "§ 3 Allgemeine Anforderungen",
    ]


def test_preprocess_no_dash_splits_short_titles_with_inline_body():
    txt = "\n".join(
        [
            "§ 60 Vorrang anderer Gestattungsverfahren Keiner Baugenehmigung bedürfen bestimmte Vorhaben.",
            "§ 61 Verfahrensfreie Bauvorhaben, Beseitigung von Anlagen Verfahrensfrei sind die in der Anlage bezeichneten Vorhaben.",
        ]
    )

    out = _preprocess_no_dash(
        txt,
        {
            "60": "Vorrang anderer Gestattungsverfahren",
            "61": "Verfahrensfreie Bauvorhaben, Beseitigung von Anlagen",
        },
    )

    assert out.splitlines() == [
        "§ 60 Vorrang anderer Gestattungsverfahren",
        "Keiner Baugenehmigung bedürfen bestimmte Vorhaben.",
        "§ 61 Verfahrensfreie Bauvorhaben, Beseitigung von Anlagen",
        "Verfahrensfrei sind die in der Anlage bezeichneten Vorhaben.",
    ]


def test_load_sectioned_inventory_sections_reads_bw_style_markdown(tmp_path):
    inventory = tmp_path / "BW_LBO_node_inventory.md"
    inventory.write_text(
        "\n".join(
            [
                "### §1 — Anwendungsbereich",
                "**type:** Anwendungsbereich",
                "| Nr. | Regeltext (Wortlaut LBO) |",
                "|---|---|",
                "| 1.1 | Dieses Gesetz gilt. |",
                "| 1.2 | Abschnitt III Genehmigungsverfahren. |",
                "### §2 — Begriffe",
                "**type:** Begriffsbestimmung",
                "| Nr. | Regeltext (Wortlaut LBO) |",
                "|---|---|",
                "| 2.1.1 | Bauliche Anlagen sind Anlagen. |",
            ]
        ),
        encoding="utf-8",
    )

    sections = _load_sectioned_inventory_sections(inventory)

    assert sections == [
        ("1", "Anwendungsbereich", "Anwendungsbereich", [("1.1", "Dieses Gesetz gilt")]),
        ("2", "Begriffe", "Begriffsbestimmung", [("2.1.1", "Bauliche Anlagen sind Anlagen")]),
    ]


def test_map_to_mbo_clean_title_strips_page_vendor_and_heading_bleed():
    assert _clean_title("Seite 38 von 88 Umwehrungen") == "Umwehrungen"
    assert _clean_title("Bebauung der Grundstücke 2130-1 7") == "Bebauung der Grundstücke"


def test_baybo_infer_section_type_corrects_shifted_legacy_types():
    legacy = {
        "8": "freiflaechengestaltung",
        "47": "aufenthaltsraum",
        "84": "sanktion",
    }

    assert infer_section_type("8", "Baugestaltung", legacy) == "gestaltungsanforderung"
    assert infer_section_type("47", "Stellplätze, Verordnungsermächtigung", legacy) == "stellplatzpflicht"
    assert infer_section_type("84", "Inkrafttreten", legacy) == "schlussvorschrift"
    assert infer_section_type("5", "Zugänge und Zufahrten auf den Grundstücken", legacy) == "allgemeine_anforderung"


def test_clean_body_text_strips_baybo_heading_bleed():
    assert _clean_body_text(
        "Die Bauaufsichtsbehörde informiert den Bauherrn unverzüglich über eintretende Änderungen nach den Abs. 1 und 2. Achter Teil Übergangs- und Schlussvorschriften."
    ) == "Die Bauaufsichtsbehörde informiert den Bauherrn unverzüglich über eintretende Änderungen nach den Abs. 1 und 2"
    assert _clean_title(
        "Standsicherheit © 2026 Wolters Kluwer Deutschland GmbH 11 / 79 gespeichert: 11.03.2026, 19:09 Uhr"
    ) == "Standsicherheit"
    assert _clean_title("Abweichungen Abschnitt III Genehmigungsverfahren") == "Abweichungen"


def test_extract_titles_cleans_inventory_headings_before_matching(tmp_path):
    inventory = tmp_path / "inventory.md"
    inventory.write_text(
        "\n".join(
            [
                "### § 6 - Seite 38 von 88 Umwehrungen",
                "### § 7 - Bebauung der Grundstücke 2130-1 7",
                "### § 8 - Abweichungen Achter Teil Übergangs- und Schlussvorschriften",
            ]
        ),
        encoding="utf-8",
    )

    assert _extract_titles(inventory) == {
        "6": "Umwehrungen",
        "7": "Bebauung der Grundstücke",
        "8": "Abweichungen",
    }


def test_best_mbo_match_prefers_same_section_number_when_titles_are_close():
    mbo_titles = {
        "5": "Abstandsflaechen",
        "6": "Abstandsflaechen und Abstaende",
    }

    best_num, best_title, score = _best_mbo_match("6", "Abstandsflächen und Abstände", mbo_titles)

    assert best_num == "6"
    assert best_title == "Abstandsflaechen und Abstaende"
    assert score > 0.95


def test_find_state_inventory_prefers_fine_inventory_when_available(tmp_path, monkeypatch):
    inventory_dir = tmp_path / "node inventory"
    inventory_dir.mkdir()
    fine = inventory_dir / "Test_node_inventory_fine.md"
    v2 = inventory_dir / "Test_node_inventory_v2.md"
    base = inventory_dir / "Test_node_inventory.md"
    fine.write_text("", encoding="utf-8")
    v2.write_text("", encoding="utf-8")
    base.write_text("", encoding="utf-8")

    monkeypatch.setattr(map_to_mbo, "_DATA", tmp_path)

    assert _find_state_inventory("Test") == fine
