"""
Audit extraction artifacts across txt and inventory stages.

Usage:
    python -m propra.data.audit_extraction_artifacts
    python -m propra.data.audit_extraction_artifacts --state NBauO LBO_SL
    python -m propra.data.audit_extraction_artifacts --json
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from propra.graph.build_graph import _is_pure_heading_text
from propra.graph.build_graph import _strip_known_text_artifacts
from propra.graph.build_graph import _strip_trailing_heading_text
from propra.graph.map_to_mbo import _clean_title

_DATA = Path(__file__).resolve().parent
_TXT_DIR = _DATA / "txt"
_INVENTORY_DIR = _DATA / "node inventory"
_TXT_PATH_OVERRIDES = {
    "BW_LBO": "BauO_BW.txt",
}

_RAW_PATTERNS = {
    "vendor_watermarks": re.compile(r"(?:Wolters\s+Kluwer|gespeichert:)", re.IGNORECASE),
    "page_markers": re.compile(r"\bSeite\s+\d+\s+von\s+\d+\b", re.IGNORECASE),
    "legislative_refs": re.compile(r"\b2130-\d+\s+\d+\b"),
}


def _count_pattern_matches(text: str) -> dict[str, int]:
    return {name: len(pattern.findall(text)) for name, pattern in _RAW_PATTERNS.items()}


def _iter_inventory_titles(path: Path) -> list[str]:
    titles: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        m = re.match(r"^###\s+§§?\s*\d+[a-z]?\s*[—\-]\s*(.+)", stripped, re.IGNORECASE)
        if m:
            titles.append(m.group(1).strip())
    return titles


def _iter_inventory_row_texts(path: Path) -> list[str]:
    rows: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        if len(cells) != 2:
            continue
        if cells[0].lower() in {"nr.", "nr"}:
            continue
        if set(cells[0]) == {"-"}:
            continue
        if not re.match(r"^\d+[a-z]?(?:\.\d+)?$", cells[0]):
            continue
        rows.append(cells[1])
    return rows


def audit_text_path(path: Path) -> dict[str, int]:
    counts = _count_pattern_matches(path.read_text(encoding="utf-8")) if path.exists() else {}
    counts["exists"] = int(path.exists())
    return counts


def audit_inventory_path(path: Path) -> dict[str, int]:
    if not path.exists():
        return {"exists": 0}

    titles = _iter_inventory_titles(path)
    rows = _iter_inventory_row_texts(path)
    pure_heading_rows = sum(1 for row in rows if _is_pure_heading_text(row))
    trimmed_heading_tail_rows = sum(
        1
        for row in rows
        if not _is_pure_heading_text(row) and _strip_trailing_heading_text(row) != row
    )
    rows_with_text_artifacts = sum(1 for row in rows if _strip_known_text_artifacts(row) != row)
    dirty_titles = sum(1 for title in titles if _clean_title(title) != title)

    return {
        "exists": 1,
        "titles_total": len(titles),
        "dirty_titles": dirty_titles,
        "rows_total": len(rows),
        "rows_with_text_artifacts": rows_with_text_artifacts,
        "pure_heading_rows": pure_heading_rows,
        "trimmed_heading_tail_rows": trimmed_heading_tail_rows,
    }


def discover_states() -> list[str]:
    states: set[str] = set()
    for path in _INVENTORY_DIR.glob("*_node_inventory*.md"):
        m = re.match(r"^(.+?)_node_inventory(?:_fine|_v2)?\.md$", path.name)
        if m:
            states.add(m.group(1))
    states.discard("MBO")
    return sorted(states)


def audit_state(state: str) -> dict[str, object]:
    txt_name = _TXT_PATH_OVERRIDES.get(state, f"{state}.txt")
    txt_path = _TXT_DIR / txt_name
    v2_path = _INVENTORY_DIR / f"{state}_node_inventory_v2.md"
    fine_path = _INVENTORY_DIR / f"{state}_node_inventory_fine.md"

    report = {
        "state": state,
        "txt": audit_text_path(txt_path),
        "inventory_v2": audit_inventory_path(v2_path),
        "inventory_fine": audit_inventory_path(fine_path),
    }
    report["issue_total"] = (
        report["txt"].get("vendor_watermarks", 0)
        + report["txt"].get("page_markers", 0)
        + report["txt"].get("legislative_refs", 0)
        + report["inventory_v2"].get("dirty_titles", 0)
        + report["inventory_v2"].get("rows_with_text_artifacts", 0)
        + report["inventory_v2"].get("pure_heading_rows", 0)
        + report["inventory_v2"].get("trimmed_heading_tail_rows", 0)
        + report["inventory_fine"].get("dirty_titles", 0)
        + report["inventory_fine"].get("rows_with_text_artifacts", 0)
        + report["inventory_fine"].get("pure_heading_rows", 0)
        + report["inventory_fine"].get("trimmed_heading_tail_rows", 0)
    )
    return report


def _format_table(reports: list[dict[str, object]]) -> str:
    header = (
        f"{'State':<12} {'Issues':>6} {'TXT vendor':>10} {'TXT page':>8} {'TXT ref':>7} "
        f"{'V2 dirty':>8} {'V2 rows':>7} {'V2 head':>7} {'Fine dirty':>10} {'Fine rows':>9} {'Fine head':>9} {'Fine trim':>9}"
    )
    lines = [header, "-" * len(header)]
    for report in reports:
        txt = report["txt"]
        v2 = report["inventory_v2"]
        fine = report["inventory_fine"]
        lines.append(
            f"{report['state']:<12} {report['issue_total']:>6} "
            f"{txt.get('vendor_watermarks', 0):>10} {txt.get('page_markers', 0):>8} {txt.get('legislative_refs', 0):>7} "
            f"{v2.get('dirty_titles', 0):>8} {v2.get('rows_with_text_artifacts', 0):>7} {v2.get('pure_heading_rows', 0):>7} "
            f"{fine.get('dirty_titles', 0):>10} {fine.get('rows_with_text_artifacts', 0):>9} {fine.get('pure_heading_rows', 0):>9} {fine.get('trimmed_heading_tail_rows', 0):>9}"
        )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit extraction artifacts across txt and inventory stages.")
    parser.add_argument("--state", nargs="*", help="State codes to audit (default: all discovered states).")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of a table.")
    parser.add_argument("--out", type=Path, help="Optional output path.")
    args = parser.parse_args()

    states = args.state or discover_states()
    reports = sorted((audit_state(state) for state in states), key=lambda item: (-item["issue_total"], item["state"]))

    output = json.dumps(reports, ensure_ascii=False, indent=2) if args.json else _format_table(reports)
    if args.out:
        args.out.write_text(output + "\n", encoding="utf-8")
    else:
        print(output)


if __name__ == "__main__":
    main()
