from propra.data.generate_nbauO_inventory import _parse_sections


def test_parse_sections_accepts_pdf_style_nbauo_headings_with_and_without_inline_body():
    txt = "\n".join(
        [
            "§ 1 Geltungsbereich",
            "(1) Dieses Gesetz gilt.",
            "§ 2 Begriffe 1Bauliche Anlagen sind Anlagen.",
        ]
    )

    sections = _parse_sections(txt, {"1": "Geltungsbereich", "2": "Begriffe"})

    assert sections == [
        ("1", "Geltungsbereich", "(1) Dieses Gesetz gilt"),
        ("2", "Begriffe", "1Bauliche Anlagen sind Anlagen"),
    ]


def test_parse_sections_prefers_real_body_over_toc_duplicate():
    txt = "\n".join(
        [
            "§ 1 Geltungsbereich",
            "§ 2 Begriffe",
            "§ 1 Geltungsbereich",
            "(1) Dieses Gesetz gilt.",
        ]
    )

    sections = _parse_sections(txt, {"1": "Geltungsbereich", "2": "Begriffe"})

    matching = [item for item in sections if item[0] == "1"]

    assert matching == [("1", "Geltungsbereich", "(1) Dieses Gesetz gilt")]


def test_parse_sections_derives_clean_title_from_toc_and_inline_body_duplicate():
    txt = "\n".join(
        [
            "§ 10 Gestaltung baulicher Anlagen",
            "§ 10 Gestaltung baulicher Anlagen Bauliche Anlagen sind in der Form so durchzubilden.",
        ]
    )

    sections = _parse_sections(txt, {"10": "Gestaltung baulicher Anlagen Bau"})

    assert sections == [
        ("10", "Gestaltung baulicher Anlagen", "Bauliche Anlagen sind in der Form so durchzubilden")
    ]


def test_parse_sections_strips_part_heading_noise_from_duplicate_prefix():
    txt = "\n".join(
        [
            "§ 56 Verantwortlichkeit für den Zustand der Anlagen und Grundstücke A ch te r Tei l Behörden",
            "§ 56 Verantwortlichkeit für den Zustand der Anlagen und Grundstücke 1Die Eigentümer sind verantwortlich. A c ht er T e il Behörden",
        ]
    )

    sections = _parse_sections(
        txt,
        {"56": "Verantwortlichkeit für den Zusta"},
    )

    assert sections == [
        (
            "56",
            "Verantwortlichkeit für den Zustand der Anlagen und Grundstücke",
            "1Die Eigentümer sind verantwortlich. A c ht er T e il Behörden",
        )
    ]


def test_parse_sections_keeps_longer_pdf_heading_as_title_when_flat_title_is_truncated():
    txt = "§ 4 Zugänglichkeit des Baugrundstücks, Anordnung und Zugänglichkeit der baulichen Anlagen"

    sections = _parse_sections(txt, {"4": "Zugänglichkeit des Baugrundstück"})

    assert sections == [
        ("4", "Zugänglichkeit des Baugrundstücks, Anordnung und Zugänglichkeit der baulichen Anlagen", "")
    ]
