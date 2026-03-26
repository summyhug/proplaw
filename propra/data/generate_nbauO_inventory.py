"""
Generate NBauO_node_inventory_v2.md from NBauO.txt.

NBauO uses standard § numbering with clear section headers in the format:
  '§ N NBauO - Title'  (on their own line in the text)

This script:
  1. Parses NBauO.txt into per-section blocks split at § N NBauO lines.
  2. Splits each block into Absätze (marked by '(N)' at line-start).
  3. Looks up the node type from the existing NBauO_node_inventory.md flat table.
  4. Outputs NBauO_node_inventory_v2.md in the ### § N — Title format
     expected by split_inventory_to_sentences.py and parse_inventory.py.

No API calls needed — types are taken from the existing flat inventory.

Usage:
    python propra/data/generate_nbauO_inventory.py
"""

from __future__ import annotations

import re
import os.path
from pathlib import Path

from propra.data.generate_lbo_inventory import _clean_body_text
from propra.data.generate_lbo_inventory import _clean_section_title

# ── paths ──────────────────────────────────────────────────────────────────────
_DATA = Path(__file__).parent
_TXT_IN = _DATA / "txt" / "NBauO.txt"
_OLD_INVENTORY = _DATA / "node inventory" / "NBauO_node_inventory.md"
_V2_OUT = _DATA / "node inventory" / "NBauO_node_inventory_v2.md"

# ── regexes ────────────────────────────────────────────────────────────────────

# Matches lines like:
#   § 1 NBauO - Geltungsbereich
#   § 1 Geltungsbereich
#   § 13 Schutz gegen schädliche Einflüsse 1Bauliche Anlagen ...
# The title/body separation is cleaned later using the flat-inventory title map.
_SECTION_HEADER = re.compile(
    r"^§\s+(\d+[a-z]*)\s+(?!Abs\.)(?:NBauO\s*[-–]\s*)?(.+)$",
    re.IGNORECASE,
)

# Absatz marker: (1), (2), ... at line-start (possibly with leading whitespace)
_ABSATZ_RE = re.compile(r"^\s*\((\d+)\)\s*(.*)$")
_INLINE_BODY_HINT_RE = re.compile(
    r"\b(?:ist|sind|war|waren|wird|werden|wurde|wurden|"
    r"muss|müssen|darf|dürfen|kann|können|gilt|gelten|"
    r"hat|haben|erlischt|erlöschen|führt|führen|bedarf|bedürfen)\b",
    re.IGNORECASE,
)


def _load_flat_inventory(flat_path: Path) -> tuple[dict[str, str], dict[str, str]]:
    """
    Parse the existing flat-table NBauO_node_inventory.md to produce:
      - type_map:  section_number -> node_type
      - title_map: section_number -> official title (from the § column)

    Flat table format:
      | Row ID | § | Absatz | Node Type | Text (excerpt) |
      | 6.1    | §6 NBauO - Hinzurechnung benachbarter Grundstücke | Abs. 1 | abstandsflaeche | ... |
    """
    type_map: dict[str, str] = {}
    title_map: dict[str, str] = {}
    # Matches '§6 NBauO - Title' or '§3a NBauO - Title'
    _SEC_TITLE_RE = re.compile(r"§(\d+[a-z]*)\s+NBauO\s*[-–]\s*(.+)", re.IGNORECASE)
    for line in flat_path.read_text(encoding="utf-8").splitlines():
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 4:
            continue
        row_id = cells[0]
        sec_col = cells[1] if len(cells) > 1 else ""
        node_type = cells[3] if len(cells) > 3 else ""
        # Skip header rows
        if row_id.lower() in {"row id", "nr", "nr.", "#"}:
            continue
        if not node_type or node_type.lower() in {
            "node type", "typ", "knotentyp", "type"
        }:
            continue
        # Extract section number from row ID (e.g. "6.1" -> "6", "3a.2" -> "3a")
        m = re.match(r"^(\d+[a-z]*)\.", row_id)
        if m:
            sec = m.group(1)
            if sec not in type_map:
                type_map[sec] = node_type.strip()
            if sec not in title_map:
                mt = _SEC_TITLE_RE.search(sec_col)
                if mt:
                    title = _clean_section_title(mt.group(2).strip())
                    if title:
                        title_map[sec] = title
    return type_map, title_map


def _parse_sections(
    txt: str, title_map: dict[str, str]
) -> list[tuple[str, str, str]]:
    """
    Split NBauO.txt into (section_number, title, body_text) triples.

    Uses title_map (from the flat inventory) for official titles so that
    single-Absatz sections whose header line contains the body text inline
    are handled correctly: the excess text after the official title is
    prepended to the body.

    Returns sections in document order.
    """
    lines = txt.splitlines()
    occurrences: list[tuple[str, str, list[str]]] = []
    current_num: str = ""
    current_rest: str = ""
    body_lines: list[str] = []

    def _section_key(sec: str) -> tuple[int, str]:
        m = re.match(r"^(\d+)([a-z]?)$", sec)
        if not m:
            return (0, sec)
        return (int(m.group(1)), m.group(2))

    def _looks_like_inline_body(text: str) -> bool:
        cleaned = _clean_body_text(text)
        if not cleaned:
            return False
        if re.match(r"^(?:\(?\d+\)|\d)", cleaned):
            return True
        return bool(_INLINE_BODY_HINT_RE.search(cleaned))

    def _derive_title(num: str, raw_candidates: list[str]) -> str:
        cleaned_candidates = [
            cleaned for cleaned in (_clean_section_title(item) for item in raw_candidates) if cleaned
        ]
        official = _clean_section_title(title_map.get(num.lower(), ""))

        title = ""
        if len(cleaned_candidates) >= 2:
            common = _clean_section_title(os.path.commonprefix(cleaned_candidates))
            if common:
                title = common

        if not title and cleaned_candidates:
            shortest = min(cleaned_candidates, key=len)
            title = shortest
            if official and shortest.startswith(official):
                remainder = shortest[len(official):].lstrip()
                if remainder and not _looks_like_inline_body(remainder):
                    title = shortest
                else:
                    title = official

        if not title:
            title = official

        if cleaned_candidates:
            longest = max(cleaned_candidates, key=len)
            if title and longest.startswith(title):
                remainder = longest[len(title):].lstrip()
                if remainder and not _looks_like_inline_body(remainder):
                    title = longest

        return _clean_section_title(title)

    for line in lines:
        m = _SECTION_HEADER.match(line.strip())
        if m:
            # Save previous section
            if current_num:
                occurrences.append((current_num, current_rest, body_lines))
            current_num = m.group(1).strip()
            current_rest = m.group(2).strip()
            body_lines = []
        elif current_num:
            cleaned = _clean_body_text(line)
            if cleaned:
                body_lines.append(cleaned)

    # Flush last section
    if current_num:
        occurrences.append((current_num, current_rest, body_lines))

    grouped: dict[str, list[tuple[str, list[str]]]] = {}
    for num, raw_rest, captured_body_lines in occurrences:
        grouped.setdefault(num, []).append((raw_rest, captured_body_lines))

    sections: list[tuple[str, str, str]] = []
    for num in sorted(grouped, key=_section_key):
        raw_candidates = [raw_rest for raw_rest, _ in grouped[num]]
        title = _derive_title(num, raw_candidates)

        best_body = ""
        for raw_rest, captured_body_lines in grouped[num]:
            raw_clean = _clean_section_title(raw_rest)
            inline_parts: list[str] = []
            if title and raw_clean.startswith(title):
                remainder = raw_clean[len(title):].lstrip()
                if remainder and _looks_like_inline_body(remainder):
                    cleaned_remainder = _clean_body_text(remainder)
                    if cleaned_remainder:
                        inline_parts.append(cleaned_remainder)

            body_chunks = inline_parts + [chunk for chunk in captured_body_lines if chunk]
            body = "\n".join(body_chunks).strip()
            if len(body) > len(best_body):
                best_body = body

        sections.append((num, title, best_body))

    return sections


def _split_absaetze(body: str) -> list[tuple[str, str]]:
    """
    Split a section body into (absatz_number, text) pairs.

    Absätze are identified by '(N)' markers at line-start.
    If none are found, returns [('' , body)] so the whole text becomes one row.
    """
    lines = body.splitlines()
    absaetze: list[tuple[str, str]] = []
    current_n: str = ""
    current_lines: list[str] = []

    for line in lines:
        m = _ABSATZ_RE.match(line)
        if m:
            if current_n or current_lines:
                absaetze.append((current_n, " ".join(current_lines).strip()))
            current_n = m.group(1)
            first = m.group(2).strip()
            current_lines = [first] if first else []
        else:
            stripped = line.strip()
            if stripped:
                current_lines.append(stripped)

    if current_n or current_lines:
        absaetze.append((current_n, " ".join(current_lines).strip()))

    # Filter out empty entries
    absaetze = [(n, t) for n, t in absaetze if t.strip()]

    return absaetze or [("", body.strip())]


def _format_row_id(sec: str, abs_n: str, idx: int) -> str:
    """
    Build a row ID matching the convention used by parse_inventory.py.

    For numbered Absätze: '{sec_norm}.{abs_n}'  e.g. '6.1'
    For unnumbered:        '{sec_norm}.{idx+1}'  e.g. '85b.1'

    sec_norm: section number with letter suffix lowered, e.g. '85a', '3a'.
    """
    sec_norm = sec.lower()
    num = abs_n if abs_n else str(idx + 1)
    return f"{sec_norm}.{num}"


def generate(txt_path: Path, old_path: Path, out_path: Path) -> None:
    """Main generation function."""
    print(f"Reading {txt_path} …")
    txt = txt_path.read_text(encoding="utf-8", errors="replace")

    print(f"Loading type/title map from {old_path} …")
    type_map, title_map = _load_flat_inventory(old_path)
    print(f"  {len(type_map)} section types, {len(title_map)} titles loaded")

    sections = _parse_sections(txt, title_map)
    print(f"  {len(sections)} sections found")

    lines_out: list[str] = [
        "# NBauO — Node Inventory (Paragraph Level)",
        "",
        "_Generated by generate_nbauO_inventory.py from NBauO.txt._",
        "_Types sourced from existing flat NBauO_node_inventory.md._",
        "_Run split_inventory_to_sentences.py to produce the fine (sentence-level) version._",
        "",
    ]

    unknown_types: list[str] = []
    for sec_num, title, body in sections:
        node_type = type_map.get(sec_num.lower(), "")
        if not node_type:
            node_type = "allgemeine_anforderung"
            unknown_types.append(sec_num)

        lines_out.append(f"### § {sec_num} — {title}")
        lines_out.append(f"**type:** {node_type}")
        lines_out.append(f"**source_paragraph:** §{sec_num} NBauO")
        lines_out.append("")
        lines_out.append("| Nr. | Regeltext (NBauO-Wortlaut) |")
        lines_out.append("|---|---|")

        absaetze = _split_absaetze(body)
        for idx, (abs_n, text) in enumerate(absaetze):
            text = _clean_body_text(text)
            if not text:
                continue
            row_id = _format_row_id(sec_num, abs_n, idx)
            # Escape any pipe characters in the text
            text_clean = text.replace("|", "\\|")
            lines_out.append(f"| {row_id} | {text_clean} |")

        lines_out.append("")

    out_path.write_text("\n".join(lines_out), encoding="utf-8")
    print(f"Written to {out_path}")
    print(f"  Total sections: {len(sections)}")

    if unknown_types:
        print(
            f"  WARNING: {len(unknown_types)} sections had no type in flat inventory "
            f"(defaulted to allgemeine_anforderung): {unknown_types[:10]}"
        )


if __name__ == "__main__":
    generate(_TXT_IN, _OLD_INVENTORY, _V2_OUT)
