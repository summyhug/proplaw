import propra.data.audit_extraction_artifacts as audit_artifacts
from propra.data.audit_extraction_artifacts import audit_inventory_path
from propra.data.audit_extraction_artifacts import audit_state
from propra.data.audit_extraction_artifacts import audit_text_path


def test_audit_text_path_counts_known_raw_artifacts(tmp_path):
    txt = tmp_path / "NBauO.txt"
    txt.write_text(
        "\n".join(
            [
                "Seite 18 von 82",
                "2130-1 39",
                "© 2026 Wolters Kluwer Deutschland GmbH 14 / 79 gespeichert: 11.03.2026, 19:09 Uhr",
            ]
        ),
        encoding="utf-8",
    )

    report = audit_text_path(txt)

    assert report["exists"] == 1
    assert report["page_markers"] == 1
    assert report["legislative_refs"] == 1
    assert report["vendor_watermarks"] == 2


def test_audit_inventory_path_counts_dirty_titles_and_rows(tmp_path):
    inventory = tmp_path / "NBauO_node_inventory_fine.md"
    inventory.write_text(
        "\n".join(
            [
                "### § 5 - Seite 38 von 88 Umwehrungen",
                "| Nr. | Regeltext (NBauO-Wortlaut) |",
                "|---|---|",
                "| 1.1 | Abschnitt III Genehmigungsverfahren. |",
                "| 1.2 | Die Bauaufsichtsbehörde informiert den Bauherrn unverzüglich. Achter Teil Übergangs- und Schlussvorschriften. |",
                "| 1.3 | © 2026 Wolters Kluwer Deutschland GmbH 13 / 79 gespeichert: 11.03.2026, 19:09 Uhr. |",
            ]
        ),
        encoding="utf-8",
    )

    report = audit_inventory_path(inventory)

    assert report["exists"] == 1
    assert report["titles_total"] == 1
    assert report["dirty_titles"] == 1
    assert report["rows_total"] == 3
    assert report["rows_with_text_artifacts"] == 1
    assert report["pure_heading_rows"] == 1
    assert report["trimmed_heading_tail_rows"] == 1


def test_audit_state_uses_txt_path_overrides(tmp_path, monkeypatch):
    txt_dir = tmp_path / "txt"
    inventory_dir = tmp_path / "node inventory"
    txt_dir.mkdir()
    inventory_dir.mkdir()

    (txt_dir / "BauO_BW.txt").write_text("Seite 1 von 2", encoding="utf-8")
    (inventory_dir / "BW_LBO_node_inventory.md").write_text("", encoding="utf-8")

    monkeypatch.setattr(audit_artifacts, "_TXT_DIR", txt_dir)
    monkeypatch.setattr(audit_artifacts, "_INVENTORY_DIR", inventory_dir)

    report = audit_state("BW_LBO")

    assert report["txt"]["exists"] == 1
    assert report["txt"]["page_markers"] == 1
