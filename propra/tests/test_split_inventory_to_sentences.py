from propra.data.split_inventory_to_sentences import Section
from propra.data.split_inventory_to_sentences import _clean_segment_text
from propra.data.split_inventory_to_sentences import _parse_inventory
from propra.data.split_inventory_to_sentences import _split_paragraph_text
from propra.data.split_inventory_to_sentences import _write_fine_inventory


def test_parse_inventory_accepts_lettered_section_row_ids(tmp_path):
    inventory = tmp_path / "NBauO_node_inventory_v2.md"
    inventory.write_text(
        "\n".join(
            [
                "### § 3a — Elektronische Kommunikation",
                "**type:** allgemeine_anforderung",
                "**source_paragraph:** §3a NBauO",
                "",
                "| Nr. | Regeltext (NBauO-Wortlaut) |",
                "|---|---|",
                "| 3a.1 | Elektronische Kommunikation ist zulaessig. |",
            ]
        ),
        encoding="utf-8",
    )

    sections = _parse_inventory(inventory)

    assert len(sections) == 1
    assert sections[0].rows == [("3a.1", "Elektronische Kommunikation ist zulaessig.")]


def test_write_fine_inventory_uses_law_label_from_source_paragraph(tmp_path):
    out_path = tmp_path / "NBauO_node_inventory_fine.md"
    sections = [
        Section(
            heading="### § 3a — Elektronische Kommunikation",
            type_line="**type:** allgemeine_anforderung",
            source_paragraph="**source_paragraph:** §3a NBauO",
            rows=[("3a.1", "Elektronische Kommunikation ist zulaessig.")],
        )
    ]

    _write_fine_inventory(sections, out_path)
    output = out_path.read_text(encoding="utf-8")

    assert "# NBauO — Node Inventory (Sentence / List-Item Level)" in output
    assert "| Nr. | Regeltext (NBauO-Wortlaut) |" in output


def test_split_paragraph_text_handles_inline_numbered_lists_without_commas():
    text = (
        "Dieses Gesetz gilt nicht für 1. Betriebsanlagen von nichtoeffentlichen Eisenbahnen "
        "2. Anlagen und Einrichtungen unter der Aufsicht der Bergbehoerden "
        "3. Leitungen, die dem Ferntransport von Stoffen dienen"
    )

    assert _split_paragraph_text(text) == [
        "Dieses Gesetz gilt nicht für",
        "1. Betriebsanlagen von nichtoeffentlichen Eisenbahnen",
        "2. Anlagen und Einrichtungen unter der Aufsicht der Bergbehoerden",
        "3. Leitungen, die dem Ferntransport von Stoffen dienen",
    ]


def test_split_paragraph_text_keeps_compact_sentence_markers_around_inline_lists():
    text = (
        "1Bauliche Anlagen sind mit dem Erdboden verbundene, aus Bauprodukten hergestellte Anlagen. "
        "2Ortsfeste Anlagen der Wirtschaftswerbung (Werbeanlagen) einschließlich Automaten sind bauliche Anlagen. "
        "3Als bauliche Anlagen gelten Anlagen, die nach ihrem Verwendungszweck dazu bestimmt sind, überwiegend ortsfest benutzt zu werden, sowie "
        "1. Aufschüttungen, soweit sie nicht unmittelbare Folge von Abgrabungen sind, "
        "2. Lagerplätze, Abstellplätze und Ausstellungsplätze, "
        "3. Campingplätze und Wochenendplätze, "
        "4. Freizeit- und Vergnügungsparks, "
        "5. Stellplätze für Kraftfahrzeuge. "
        "4Anlagen sind bauliche Anlagen sowie andere Anlagen und Einrichtungen im Sinn des Art. 1 Abs. 1 Satz 2."
    )

    assert _split_paragraph_text(text) == [
        "1Bauliche Anlagen sind mit dem Erdboden verbundene, aus Bauprodukten hergestellte Anlagen.",
        "2Ortsfeste Anlagen der Wirtschaftswerbung (Werbeanlagen) einschließlich Automaten sind bauliche Anlagen.",
        "3Als bauliche Anlagen gelten Anlagen, die nach ihrem Verwendungszweck dazu bestimmt sind, überwiegend ortsfest benutzt zu werden, sowie.",
        "1. Aufschüttungen, soweit sie nicht unmittelbare Folge von Abgrabungen sind",
        "2. Lagerplätze, Abstellplätze und Ausstellungsplätze",
        "3. Campingplätze und Wochenendplätze",
        "4. Freizeit- und Vergnügungsparks",
        "5. Stellplätze für Kraftfahrzeuge.",
        "4Anlagen sind bauliche Anlagen sowie andere Anlagen und Einrichtungen im Sinn des Art. 1 Abs. 1 Satz 2.",
    ]


def test_split_paragraph_text_does_not_split_dates_inside_inline_lists():
    text = (
        "1Die Eigentümer von Nichtwohngebäuden, deren Antrag auf Baugenehmigung oder deren vollständige Bauvorlagen "
        "1. ab dem 1. März 2023 für Gebäude, die ausschließlich gewerblicher oder industrieller Nutzung zu dienen bestimmt sind, oder "
        "2. ab dem 1. Juli 2023 für sonstige Nichtwohngebäude eingehen, haben sicherzustellen, dass Anlagen in angemessener Auslegung "
        "zur Erzeugung von Strom aus solarer Strahlungsenergie auf den hierfür geeigneten Dachflächen errichtet und betrieben werden. "
        "2Die Pflichten nach Satz 1 gelten auch bei vollständiger Erneuerung der Dachhaut eines Gebäudes, die ab dem 1. Januar 2025 begonnen wird. "
        "3Abs. 1 Satz 2 bis 4 gilt entsprechend."
    )

    assert _split_paragraph_text(text) == [
        "1Die Eigentümer von Nichtwohngebäuden, deren Antrag auf Baugenehmigung oder deren vollständige Bauvorlagen",
        "1. ab dem 1. März 2023 für Gebäude, die ausschließlich gewerblicher oder industrieller Nutzung zu dienen bestimmt sind, oder",
        "2. ab dem 1. Juli 2023 für sonstige Nichtwohngebäude eingehen, haben sicherzustellen, dass Anlagen in angemessener Auslegung zur Erzeugung von Strom aus solarer Strahlungsenergie auf den hierfür geeigneten Dachflächen errichtet und betrieben werden.",
        "2Die Pflichten nach Satz 1 gelten auch bei vollständiger Erneuerung der Dachhaut eines Gebäudes, die ab dem 1. Januar 2025 begonnen wird.",
        "3Abs. 1 Satz 2 bis 4 gilt entsprechend.",
    ]


def test_split_paragraph_text_keeps_buchst_and_unterabs_citations_together():
    text = (
        "1Antragsteller haben zum Nachweis der Voraussetzungen des Abs. 2 Unterlagen nach Art. 50 Abs. 1 der Richtlinie 2005/36/EG "
        "in Verbindung mit deren Anhang VII Nr. 1 Buchst. a und b Satz 1 sowie auf Anforderung nach Anhang VII Nr. 1 Buchst. b "
        "UnterAbs. 2 dieser Richtlinie vorzulegen. "
        "2Gibt der Antragsteller an, hierzu nicht in der Lage zu sein, wendet sich die Bayerische Ingenieurekammer-Bau zur Beschaffung "
        "der erforderlichen Unterlagen an das Beratungszentrum."
    )

    assert _split_paragraph_text(text) == [
        "1Antragsteller haben zum Nachweis der Voraussetzungen des Abs. 2 Unterlagen nach Art. 50 Abs. 1 der Richtlinie 2005/36/EG in Verbindung mit deren Anhang VII Nr. 1 Buchst. a und b Satz 1 sowie auf Anforderung nach Anhang VII Nr. 1 Buchst. b UnterAbs. 2 dieser Richtlinie vorzulegen.",
        "2Gibt der Antragsteller an, hierzu nicht in der Lage zu sein, wendet sich die Bayerische Ingenieurekammer-Bau zur Beschaffung der erforderlichen Unterlagen an das Beratungszentrum.",
    ]


def test_split_paragraph_text_splits_compact_sentence_markers_without_spaces():
    text = (
        "1Die Vorschrift zur Genehmigungsfiktion gilt fuer ab dem 1. Mai 2021 eingereichte Bauantraege "
        "2Die Vorschrift zur Genehmigungsfiktion nach Satz 2 gilt fuer ab dem 1. Oktober 2023 eingereichte Bauantraege"
    )

    assert _split_paragraph_text(text) == [
        "1Die Vorschrift zur Genehmigungsfiktion gilt fuer ab dem 1. Mai 2021 eingereichte Bauantraege.",
        "2Die Vorschrift zur Genehmigungsfiktion nach Satz 2 gilt fuer ab dem 1. Oktober 2023 eingereichte Bauantraege.",
    ]


def test_split_paragraph_text_splits_compact_sentence_markers_after_citation_periods():
    text = (
        "1Das Deutsche Institut fuer Bautechnik erteilt die allgemeine Bauartgenehmigung nach Art. 15 Abs. 2 Satz 1 Nr. 1 "
        "und die allgemeine bauaufsichtliche Zulassung nach Art. 18 Abs. 1. "
        "2Es kann vorschreiben, wann welche sachverstaendige Stelle die Pruefung durchzufuehren hat."
    )

    assert _split_paragraph_text(text) == [
        "1Das Deutsche Institut fuer Bautechnik erteilt die allgemeine Bauartgenehmigung nach Art. 15 Abs. 2 Satz 1 Nr. 1 und die allgemeine bauaufsichtliche Zulassung nach Art. 18 Abs. 1.",
        "2Es kann vorschreiben, wann welche sachverstaendige Stelle die Pruefung durchzufuehren hat.",
    ]


def test_clean_segment_text_drops_heading_only_rows_and_duplicate_section_titles():
    assert _clean_segment_text(
        "Teil 2 Das Grundstück und seine Bebauung.",
        section_title="Anwendungsbereich",
    ) == ""
    assert _clean_segment_text(
        "§ 1 Anwendungsbereich",
        section_title="Anwendungsbereich",
    ) == ""


def test_clean_segment_text_trims_trailing_heading_fragments():
    assert _clean_segment_text(
        "Die Bauaufsichtsbehörde informiert den Bauherrn unverzüglich. Achter Teil Übergangs- und Schlussvorschriften.",
        section_title="Baugenehmigung",
    ) == "Die Bauaufsichtsbehörde informiert den Bauherrn unverzüglich"


def test_write_fine_inventory_skips_heading_noise_rows(tmp_path):
    out_path = tmp_path / "BremLBO_node_inventory_fine.md"
    sections = [
        Section(
            heading="### § 1 — Anwendungsbereich",
            type_line="**type:** anwendungsbereich",
            source_paragraph="**source_paragraph:** §1 BremLBO",
            rows=[
                ("1.1", "§ 1 Anwendungsbereich"),
                ("1.2", "Teil 2 Das Grundstück und seine Bebauung."),
                ("1.3", "Dieses Gesetz gilt für bauliche Anlagen."),
            ],
        )
    ]

    _write_fine_inventory(sections, out_path)
    output = out_path.read_text(encoding="utf-8")

    assert "§ 1 Anwendungsbereich" not in output
    assert "Teil 2 Das Grundstück und seine Bebauung." not in output
    assert "Dieses Gesetz gilt für bauliche Anlagen" in output
