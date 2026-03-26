from propra.graph.build_graph import _is_pure_heading_text
from propra.graph.build_graph import _strip_known_text_artifacts
from propra.graph.build_graph import _strip_trailing_heading_text
from propra.graph.build_graph import _clean_text_artifacts
from propra.graph.build_graph import _prune_empty_content_nodes
from propra.graph.build_graph import _trim_heading_tails
from propra.graph.build_graph import _prune_heading_content_nodes
from propra.graph.builder import add_node, create_graph
from propra.graph.schema import Node


def test_is_pure_heading_text_detects_carried_over_inventory_headings():
    assert _is_pure_heading_text("Zweiter Teil Das Grundstück und seine Bebauung.")
    assert _is_pure_heading_text("Abschnitt III Genehmigungsverfahren.")
    assert _is_pure_heading_text("Teil 5 Bauaufsichtsbehörden, Verfahren Abschnitt 1 Bauaufsichtsbehörden.")
    assert _is_pure_heading_text("§§ 59 - 62, Neunter Teil - Genehmigungserfordernisse.")

    assert not _is_pure_heading_text("für Balkone nur, wenn sie Teil des Rettungsweges sind")
    assert not _is_pure_heading_text("Hat ein Nachbar Einwendungen gegen die Baumaßnahme erhoben, so ist die Baugenehmigung mit dem Teil der Bauvorlagen zuzustellen.")
    assert not _is_pure_heading_text("Die Bauaufsichtsbehörde informiert den Bauherrn unverzüglich. Achter Teil Übergangs- und Schlussvorschriften.")


def test_strip_known_text_artifacts_removes_vendor_and_page_noise():
    assert _strip_known_text_artifacts("Abschnitt 3 2130-1 39 Genehmigungsverfahren.") == "Abschnitt 3 Genehmigungsverfahren."
    assert _strip_known_text_artifacts("Bauaufsichtsbehör2130-1 17 de vorgeschrieben.") == "Bauaufsichtsbehörde vorgeschrieben."
    assert _strip_known_text_artifacts(
        "2 © 2026 Wolters Kluwer Deutschland GmbH 11 / 79 gespeichert: 11.03.2026, 19:09 Uhr Unzumutbare Belästigungen dürfen nicht entstehen."
    ) == "2 Unzumutbare Belästigungen dürfen nicht entstehen."
    assert _strip_known_text_artifacts(
        "© 2026 Wolters Kluwer Deutschland GmbH 13 / 79 gespeichert: 11.03.2026, 19:09 Uhr."
    ) == "."


def test_prune_heading_content_nodes_removes_only_heading_rows():
    G = create_graph()

    add_node(
        G,
        Node(
            id="BayBO_§59",
            type="genehmigungspflicht",
            jurisdiction="DE-BY",
            source_paragraph="§59 BayBO",
            text="§ 59 BayBO",
        ),
    )
    add_node(
        G,
        Node(
            id="BayBO_§58_4.3",
            type="genehmigungspflicht",
            jurisdiction="DE-BY",
            source_paragraph="§58 BayBO",
            text="Abschnitt III Genehmigungsverfahren.",
        ),
    )
    add_node(
        G,
        Node(
            id="BayBO_§72_5.1",
            type="typengenehmigung",
            jurisdiction="DE-BY",
            source_paragraph="§72 BayBO",
            text="Hat ein Nachbar Einwendungen gegen die Baumaßnahme erhoben, so ist die Baugenehmigung mit dem Teil der Bauvorlagen zuzustellen.",
        ),
    )

    G.add_edge("BayBO_§58_4.3", "BayBO_§59", relation="supplements", sourced_from="§58 BayBO")
    G.add_edge("BayBO_§72_5.1", "BayBO_§59", relation="supplements", sourced_from="§72 BayBO")

    removed = _prune_heading_content_nodes(G)

    assert removed == 1
    assert "BayBO_§58_4.3" not in G
    assert "BayBO_§59" in G
    assert "BayBO_§72_5.1" in G
    assert G.has_edge("BayBO_§72_5.1", "BayBO_§59")


def test_clean_text_artifacts_then_prune_empty_and_heading_rows():
    G = create_graph()

    add_node(
        G,
        Node(
            id="LBO_SL_§63_6.3",
            type="genehmigungspflicht",
            jurisdiction="DE-SL",
            source_paragraph="§63 LBO_SL",
            text="Abschnitt 3 2130-1 39 Genehmigungsverfahren.",
        ),
    )
    add_node(
        G,
        Node(
            id="NBauO_§5_1.5",
            type="abstandsflaeche",
            jurisdiction="DE-NI",
            source_paragraph="§5 NBauO",
            text="© 2026 Wolters Kluwer Deutschland GmbH 13 / 79 gespeichert: 11.03.2026, 19:09 Uhr.",
        ),
    )
    add_node(
        G,
        Node(
            id="NBauO_§5_7.2",
            type="abstandsflaeche",
            jurisdiction="DE-NI",
            source_paragraph="§5 NBauO",
            text="Ist ein Gebäude nach Absatz 5 Satz 2 an eine Grenze gebaut, so darf der Abstand weiter verringert © 2026 Wolters Kluwer Deutschland GmbH 14 / 79 gespeichert: 11.03.2026, 19:09 Uhr werden, wenn der Nachbar zugestimmt hat.",
        ),
    )

    cleaned = _clean_text_artifacts(G)
    removed_empty = _prune_empty_content_nodes(G)
    removed_headings = _prune_heading_content_nodes(G)

    assert cleaned == 3
    assert removed_empty == 1
    assert removed_headings == 1
    assert "LBO_SL_§63_6.3" not in G
    assert "NBauO_§5_1.5" not in G
    assert G.nodes["NBauO_§5_7.2"]["text"] == (
        "Ist ein Gebäude nach Absatz 5 Satz 2 an eine Grenze gebaut, so darf der Abstand weiter verringert werden, wenn der Nachbar zugestimmt hat."
    )


def test_strip_trailing_heading_text_keeps_rule_text_and_drops_heading_suffix():
    assert _strip_trailing_heading_text(
        "Die Bauaufsichtsbehörde informiert den Bauherrn unverzüglich über eintretende Änderungen nach den Abs. 1 und 2. Achter Teil Übergangs- und Schlussvorschriften."
    ) == "Die Bauaufsichtsbehörde informiert den Bauherrn unverzüglich über eintretende Änderungen nach den Abs. 1 und 2."
    assert _strip_trailing_heading_text(
        "1. wenn ihre Erfüllung im Einzelfall widerspricht. Abschnitt 5 Rettungswege, Öffnungen, Umwehrungen"
    ) == "1. wenn ihre Erfüllung im Einzelfall widerspricht."
    assert _strip_trailing_heading_text(
        "Hat ein Nachbar Einwendungen gegen die Baumaßnahme erhoben, so ist die Baugenehmigung mit dem Teil der Bauvorlagen zuzustellen."
    ) == "Hat ein Nachbar Einwendungen gegen die Baumaßnahme erhoben, so ist die Baugenehmigung mit dem Teil der Bauvorlagen zuzustellen."


def test_trim_heading_tails_updates_only_mixed_rows():
    G = create_graph()

    add_node(
        G,
        Node(
            id="BayBO_§82c_3.1",
            type="vereinfachtes_genehmigungsverfahren",
            jurisdiction="DE-BY",
            source_paragraph="§82c BayBO",
            text="Die Bauaufsichtsbehörde informiert den Bauherrn unverzüglich über eintretende Änderungen nach den Abs. 1 und 2. Achter Teil Übergangs- und Schlussvorschriften.",
        ),
    )
    add_node(
        G,
        Node(
            id="BayBO_§72_5.1",
            type="typengenehmigung",
            jurisdiction="DE-BY",
            source_paragraph="§72 BayBO",
            text="Hat ein Nachbar Einwendungen gegen die Baumaßnahme erhoben, so ist die Baugenehmigung mit dem Teil der Bauvorlagen zuzustellen.",
        ),
    )

    trimmed = _trim_heading_tails(G)

    assert trimmed == 1
    assert G.nodes["BayBO_§82c_3.1"]["text"] == (
        "Die Bauaufsichtsbehörde informiert den Bauherrn unverzüglich über eintretende Änderungen nach den Abs. 1 und 2."
    )
    assert G.nodes["BayBO_§72_5.1"]["text"] == (
        "Hat ein Nachbar Einwendungen gegen die Baumaßnahme erhoben, so ist die Baugenehmigung mit dem Teil der Bauvorlagen zuzustellen."
    )
