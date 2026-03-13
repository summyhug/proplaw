"""
Parser for propra/data/node inventory/*_node_inventory.md → list of Node objects.

Reads the structured markdown node inventory and emits one Node per table row.
Numeric-value rows produce nodes of type 'zahlenwert'.

Recognised patterns:
  - ### §X — Title            paragraph heading (sets current_para + type)
  - #### §X Abs. Y — Title    sub-section heading (refines source_paragraph)
  - **type:** X               node type for all rows in this section
  - **source_paragraph:** X   explicit source_paragraph override
  - **numeric_values §X:**    triggers numeric-value table mode
  - **Bold label:**           content sub-label captured as node metadata
  - | Nr. | Regeltext |       standard rule rows
  - | Knoten-ID | Regeltext | explicit-ID rows (§6 special cases, Annex)
  - ## ANHANG 1               switches to annex mode (type + source_paragraph
                              apply globally across all Gruppe sub-sections)
"""

import re
from pathlib import Path
from typing import Optional

from propra.graph.schema import NODE_TYPES, Node

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_INVENTORY_PATH = Path(__file__).parent.parent / "data" / "node inventory" / "BW_LBO_node_inventory.md"

_JURISDICTION = "DE-BW"
_DEFAULT_NODE_PREFIX = "BW_LBO_"

# German umlaut → ASCII equivalents for type-key normalisation
_UMLAUT = str.maketrans({
    "ä": "ae", "ö": "oe", "ü": "ue", "ß": "ss",
    "Ä": "ae", "Ö": "oe", "Ü": "ue",
})

# Table header keywords — rows containing these in the first two cells are skipped
_HEADER_KEYWORDS = {
    "nr", "nr.", "regeltext", "knoten-id", "größe", "wert", "quelle",
    "klasse", "bedingungen", "gebietstyp", "tiefe", "bauteil",
    "bedingung", "anrechnung", "begriff", "§",
}

# Manual overrides for type labels that don't normalise cleanly against NODE_TYPES.
# Key: normalised slug from _normalize_type(); Value: correct NODE_TYPES key.
_TYPE_OVERRIDES: dict[str, str] = {
    "fensteroeffnung":          "fensteroffnung",       # ö→oe vs NODE_TYPES ö→o
    "bestandsaenderung_tragwerk": "bestandsaenderung",  # sub-type → parent
    "bestandsaenderung_bauteile": "bestandsaenderung",  # sub-type → parent
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _normalize_type(label: str) -> str:
    """
    Convert a markdown type label to a NODE_TYPES key.

    E.g. 'Abstandsfläche Sonderfall' → 'abstandsflaeche_sonderfall'
    Falls back to the computed slug if no exact match found.
    """
    key = label.strip().lower().translate(_UMLAUT).replace(" ", "_")
    if key in _TYPE_OVERRIDES:
        return _TYPE_OVERRIDES[key]
    if key in NODE_TYPES:
        return key
    # Try normalising existing NODE_TYPES keys the same way and compare
    normalised_map = {t.lower().translate(_UMLAUT): t for t in NODE_TYPES}
    return normalised_map.get(key, key)


def _parse_numeric(raw: str) -> tuple[Optional[float], Optional[str]]:
    """
    Parse a value+unit string into (float, unit_string).

    Examples: '30 m' → (30.0, 'm'), '500.000 €' → (500000.0, '€'),
              '0,4 der Wandhöhe' → (0.4, 'der Wandhöhe')
    Returns (None, None) if the string does not start with a number.
    """
    m = re.match(r"^([0-9][0-9.,]*)\s*(.*)", raw.strip())
    if not m:
        return None, None
    num_str = m.group(1).replace(".", "").replace(",", ".")
    try:
        return float(num_str), m.group(2).strip() or None
    except ValueError:
        return None, None


def _slug(text: str, max_len: int = 28) -> str:
    """Short ASCII slug for use in node IDs."""
    return re.sub(r"[^a-z0-9]+", "_", text.lower().translate(_UMLAUT))[:max_len].strip("_")


def _extract_para(heading: str) -> str:
    """
    Extract paragraph reference from a section heading.

    '### §5 — Abstandsflächen'  → '§5'
    '### § 5 — Abstandsflächen' → '§5'  (space after § normalised)
    '### §§ 16a–25 — ...'       → '§§16a–25'
    '### §§ 77–79 — ...'        → '§§77–79'
    """
    m = re.match(r"^#{1,4}\s+(§[^—\n]+?)(?:\s*—|\s*$)", heading)
    if not m:
        return ""
    raw = m.group(1).strip()
    # Normalise "§ N" / "§§ N" → "§N" / "§§N" so node IDs are consistent
    # across inventories regardless of whether the PDF had a space after §.
    return re.sub(r"(§§?)\s+", r"\1", raw)


def _extract_subsection(heading: str) -> str:
    """Extract 'Abs. 1' from '#### §2 Abs. 1 — Bauliche Anlage'."""
    m = re.search(r"(Abs\.\s*\d+[\w\s]*?)(?:\s*—|\s*$)", heading)
    return m.group(1).strip() if m else ""


def _split_row(line: str) -> list[str]:
    """Split '| A | B | C |' → ['A', 'B', 'C']."""
    return [c.strip() for c in line.strip().strip("|").split("|")]


def _is_separator(line: str) -> bool:
    return bool(re.match(r"^\|[\s\-|]+\|$", line.strip()))


def _is_header_row(cells: list[str]) -> bool:
    return any(c.lower().strip() in _HEADER_KEYWORDS for c in cells[:2])


def _is_explicit_id(cell: str) -> bool:
    """True for cells that look like explicit Knoten-IDs (A1-01a, §6-01, etc.)."""
    return bool(re.match(r"^(A\d+-\d+\w*|§\d+[-]\d+\w*)$", cell.strip()))


# ---------------------------------------------------------------------------
# Main parser
# ---------------------------------------------------------------------------

def parse_inventory(
    path: Optional[str] = None,
    node_prefix: Optional[str] = None,
    source_suffix: Optional[str] = None,
) -> list[Node]:
    """
    Parse a node inventory markdown file and return a list of Node objects.

    Args:
        path:          Path to the markdown file. Defaults to the BW LBO inventory.
        node_prefix:   Prefix for generated node IDs (e.g. 'MBO_', 'BbgBO_'). When None,
                       the parser reads **node_prefix:** from the file header, or
                       falls back to 'BW_LBO_'.
        source_suffix: Suffix for source_paragraph (e.g. 'BbgBO', 'MBO'). When None,
                       uses 'LBO BW'. Use for state inventories so citations are correct.

    Returns:
        List of Node objects ready to be added to the graph.
    """
    src = Path(path) if path else _INVENTORY_PATH
    lines = src.read_text(encoding="utf-8").splitlines()

    nodes: list[Node] = []
    skipped: int = 0

    # --- parser state ---
    jurisdiction: str = _JURISDICTION
    active_prefix: str = node_prefix or _DEFAULT_NODE_PREFIX
    source_suffix_val: str = source_suffix if source_suffix is not None else "LBO BW"
    current_type: str = ""
    current_para: str = ""          # e.g. "§5" or "§§ 16a–25"
    current_subsection: str = ""    # e.g. "Abs. 1"
    current_source_para: str = ""   # explicit override from **source_paragraph:**
    in_numeric_table: bool = False
    in_annex: bool = False
    current_group: str = ""         # annex group label, e.g. "Gruppe 1"
    table_context: str = ""         # content sub-label within a section

    def _build_source_para() -> str:
        if current_source_para:
            return current_source_para
        base = current_para
        if current_subsection:
            base = f"{current_para} {current_subsection}"
        return f"{base} {source_suffix_val}" if base else source_suffix_val

    def _build_node_id(row_id: str) -> str:
        safe = re.sub(r"[\s/\\]", "-", row_id)
        return f"{active_prefix}{safe}"

    def _emit(node_id: str, node_type: str, text: str,
              numeric_value: Optional[float] = None,
              unit: Optional[str] = None,
              extra_meta: Optional[dict] = None) -> None:
        meta: dict = {}
        if table_context:
            meta["context"] = table_context
        if in_annex and current_group:
            meta["group"] = current_group
        if extra_meta:
            meta.update(extra_meta)

        n = Node(
            id=node_id,
            type=node_type,
            jurisdiction=jurisdiction,
            source_paragraph=_build_source_para(),
            text=text,
            numeric_value=numeric_value,
            unit=unit,
            metadata=meta,
        )
        try:
            n.validate()
            nodes.append(n)
        except ValueError as e:
            nonlocal skipped
            skipped += 1
            print(f"  [WARN] Skipped {node_id}: {e}")

    # --- line-by-line processing ---
    for line in lines:
        s = line.strip()

        # Document-level metadata (header section only)
        if s.startswith("**node_prefix:**"):
            if node_prefix is None:   # only apply if not overridden by caller
                active_prefix = s[len("**node_prefix:**"):].strip()
            continue

        if s.startswith("**jurisdiction:**"):
            raw = s[len("**jurisdiction:**"):].strip()
            m = re.search(r"\(([A-Z]{2}-[A-Z]{2})\)", raw)
            jurisdiction = m.group(1) if m else raw
            continue

        if s.startswith("**source_paragraph:**"):
            current_source_para = s[len("**source_paragraph:**"):].strip()
            continue

        # Top-level section headings (## )
        if s.startswith("## "):
            if s.startswith("## ANHANG"):
                in_annex = True
                current_para = "Anhang 1"
                current_subsection = ""
                current_source_para = ""
                current_group = ""
                table_context = ""
                in_numeric_table = False
            else:
                # Summary/reference sections (e.g. Zahlenwerte Schnellübersicht,
                # Schlüsselunterscheidung) — reset state so their tables are ignored.
                in_annex = False
                current_type = ""
                current_para = ""
                current_subsection = ""
                current_source_para = ""
                in_numeric_table = False
                table_context = ""
            continue

        # Section headings
        if s.startswith("### "):
            if in_annex:
                # Gruppe sub-sections — extract group label, keep type/source_para
                m = re.match(r"^###\s+(Gruppe\s+\d+)", s)
                current_group = m.group(1) if m else ""
                table_context = ""
                in_numeric_table = False
            else:
                current_para = _extract_para(s)
                current_subsection = ""
                current_source_para = ""
                current_type = ""
                table_context = ""
                in_numeric_table = False
            continue

        if s.startswith("#### "):
            current_subsection = _extract_subsection(s)
            table_context = ""
            in_numeric_table = False
            continue

        # Section separator
        if s == "---":
            in_numeric_table = False
            table_context = ""
            continue

        # Schema labels
        if s.startswith("**type:**"):
            current_type = _normalize_type(s[len("**type:**"):].strip())
            continue

        if s.startswith("**numeric_values"):
            in_numeric_table = True
            table_context = ""
            continue

        # Content sub-labels: **Bold label:** (ends exactly at **)
        # Excludes inline notes like **Hinweis für Propra:** text...
        if re.match(r"^\*\*[A-ZÄÖÜ][^*]+:\*\*$", s):
            table_context = s.strip("*").rstrip(":")
            in_numeric_table = False
            continue

        # Table rows
        if not s.startswith("|"):
            continue
        if _is_separator(s):
            continue

        cells = _split_row(s)
        if len(cells) < 2 or _is_header_row(cells):
            continue

        row_id_cell = cells[0]
        text_cell = cells[1]

        if not row_id_cell or not text_cell:
            continue

        # For 3-column rule tables (e.g. | Nr. | Begriff | Regeltext |),
        # concatenate the second and third columns so the node carries the
        # full definition rather than just a label word like "Bauprodukte".
        if (not in_numeric_table
                and len(cells) >= 3
                and cells[2]
                and not _is_header_row([cells[2]])):
            text_cell = f"{cells[1]}: {cells[2]}"

        # Guard: no section context means we're in a summary/ignored section
        if not current_para:
            continue

        # --- numeric values table ---
        if in_numeric_table:
            groesse, wert_raw = row_id_cell, text_cell
            quelle = cells[2] if len(cells) > 2 and cells[2] else None
            numeric_value, unit = _parse_numeric(wert_raw)
            node_id = _build_node_id(f"{current_para}_ZW_{_slug(groesse)}")
            src_override = current_source_para
            if quelle:
                current_source_para = quelle  # temporarily use row's Quelle
            _emit(node_id, "zahlenwert", f"{groesse}: {wert_raw}",
                  numeric_value=numeric_value, unit=unit,
                  extra_meta={"groesse": groesse})
            current_source_para = src_override
            continue

        # --- regular rule row ---
        if _is_explicit_id(row_id_cell):
            node_id = _build_node_id(row_id_cell)
        else:
            node_id = _build_node_id(f"{current_para}_{row_id_cell}")

        _emit(node_id, current_type or "allgemeine_anforderung", text_cell)

    print(f"Parsed {len(nodes)} nodes ({skipped} skipped) from {src.name}")
    return nodes
