"""
Split an LBO node inventory from paragraph-level to sentence/list-item level.

Reads a markdown inventory with one row per Absatz (e.g. | 6.1 | ... |, | 6.2 | ... |)
and emits a new inventory with one row per sentence or numbered list item, using
Absatz.Satz IDs (e.g. 1.1, 1.2, 2.1, 2.2) so the structure matches MBO granularity.

Known limitations: sentence split uses period+space; "Abs.", "Nr.", "Satz." can cause
over-splitting. Numbered lists are detected only when they start on a new line.

Usage:
    python -m propra.data.split_inventory_to_sentences
    python -m propra.data.split_inventory_to_sentences --input "node inventory/BbgBO_node_inventory_v2.md" --output "node inventory/BbgBO_node_inventory_fine.md"
"""

from __future__ import annotations

import re
import argparse
from pathlib import Path
from dataclasses import dataclass, field


_INVENTORY_DIR = Path(__file__).parent / "node inventory"
_DEFAULT_INPUT = _INVENTORY_DIR / "BbgBO_node_inventory_v2.md"
_DEFAULT_OUTPUT = _INVENTORY_DIR / "BbgBO_node_inventory_fine.md"

# Sentence boundary: period + space, when period follows a letter (avoid "Nr. 1." / "1. item")
# Negative lookbehinds prevent splitting after common German legal abbreviations.
_SENTENCE_RE = re.compile(
    r"(?<!Art)(?<!Abs)(?<!Nr)(?<!Satz)(?<!bzw)(?<!ggf)(?<!Vgl)(?<!vgl)(?<!Hs)"
    r"(?<=[a-zäöüßA-ZÄÖÜ])\.\s+"
)
# Line that starts a numbered list item: optional space, digits, period, space
_LIST_LINE_RE = re.compile(r"^\s*(\d+)\.\s+", re.MULTILINE)

# Detects the start of an inline numbered list: space/colon then "1. "
# NOT preceded by common abbreviations (Nr, Abs, Art, Satz).
_INLINE_LIST_START_RE = re.compile(
    r"(?<!\bNr)(?<!\bAbs)(?<!\bArt)(?<!\bSatz)(?<!\bNo)(?<=[:\s])1\.\s+"
)
# Splits between inline list items: comma/semicolon/space then "N. "
_INLINE_LIST_ITEM_RE = re.compile(r"(?:,\s*|;\s*|\s+)(\d{1,2})\.\s+")


def _expand_inline_list(text: str) -> str:
    """If text contains an inline numbered list (e.g. '... 1. item, 2. item'),
    expand it to multi-line so the line-based list handler can process it.
    Returns unchanged text if no inline list is detected."""
    m = _INLINE_LIST_START_RE.search(text)
    if not m:
        return text
    intro = text[: m.start()].rstrip()
    rest = text[m.start():]  # starts with "1. item..."
    pieces = _INLINE_LIST_ITEM_RE.split(rest)
    # pieces: ["1. item_1_text", "2", "item_2_text", "3", "item_3_text", ...]
    lines: list[str] = []
    if intro:
        lines.append(intro)
    # First piece starts with "1. "
    first_text = pieces[0]
    if first_text.startswith("1. "):
        first_text = first_text[3:]
    lines.append(f"1. {first_text.strip().rstrip(',;').strip()}")
    i = 1
    while i + 1 < len(pieces):
        num_str = pieces[i]
        item_text = pieces[i + 1].strip().rstrip(",;").strip()
        if item_text:
            lines.append(f"{num_str}. {item_text}")
        i += 2
    return "\n".join(lines)


@dataclass
class Section:
    heading: str
    type_line: str
    source_paragraph: str
    rows: list[tuple[str, str]] = field(default_factory=list)  # (nr, text)


def _parse_inventory(path: Path) -> list[Section]:
    """Parse inventory into sections; each section has heading, type, source_paragraph, and rows (nr, full text)."""
    text = path.read_text(encoding="utf-8")
    sections: list[Section] = []
    current: Section | None = None
    in_table = False
    current_nr: str | None = None
    current_text_parts: list[str] = []

    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("### "):
            if current and (current_nr is not None or current.rows):
                if current_nr is not None and current_text_parts:
                    current.rows.append((current_nr, "\n".join(current_text_parts)))
            current = Section(heading=stripped, type_line="", source_paragraph="", rows=[])
            sections.append(current)
            in_table = False
            current_nr = None
            current_text_parts = []
            continue
        if current is None:
            continue
        if stripped.startswith("**type:**"):
            current.type_line = stripped
            continue
        if stripped.startswith("**source_paragraph:**"):
            current.source_paragraph = stripped
            continue
        if stripped == "---":
            if current_nr is not None and current_text_parts:
                current.rows.append((current_nr, "\n".join(current_text_parts)))
            current_nr = None
            current_text_parts = []
            in_table = False
            continue
        if stripped.startswith("|") and "|" in stripped[1:]:
            in_table = True
            cells = [c.strip() for c in stripped.strip("|").split("|")]
            if len(cells) >= 2 and cells[0] and cells[1]:
                if current_nr is not None and current_text_parts:
                    current.rows.append((current_nr, "\n".join(current_text_parts)))
                # Check if first cell looks like Nr. (e.g. 1.1, 6.2, 12.3)
                first = cells[0].strip()
                if re.match(r"^\d+[a-z]*\.\d+$", first):
                    current_nr = first
                    current_text_parts = [cells[1]]
                else:
                    current_nr = None
                    current_text_parts = []
            continue
        if in_table and current_nr is not None and stripped and not stripped.startswith("|"):
            current_text_parts.append(stripped)
    if current and current_nr is not None and current_text_parts:
        current.rows.append((current_nr, "\n".join(current_text_parts)))
    return sections


def _split_paragraph_text(text: str) -> list[str]:
    """
    Split one paragraph's text into segments: sentences and list items.
    Returns list of text segments (one per sentence or list item).
    """
    # Remove trailing table cell pipe if present (multiline cells end with " |")
    text = re.sub(r"\s*\|\s*$", "", text.strip())
    text = text.strip()
    if not text:
        return []
    # Expand inline numbered lists into separate lines before line-based processing
    text = _expand_inline_list(text)
    segments: list[str] = []
    lines = text.split("\n")
    # Detect list structure: lines that start with "1. ", "2. ", etc.
    i = 0
    while i < len(lines):
        line = lines[i]
        m = _LIST_LINE_RE.match(line)
        if m:
            # Start of a numbered list item; collect until next list start or end
            item_lines = [line[m.end() :].strip()]
            j = i + 1
            while j < len(lines) and not _LIST_LINE_RE.match(lines[j]):
                item_lines.append(lines[j].strip())
                j += 1
            item_text = " ".join(item_lines).strip()
            if item_text:
                segments.append(f"{m.group(1)}. {item_text}")
            i = j
        else:
            # Non-list line: accumulate into an "intro" block
            intro_lines = []
            while i < len(lines) and not _LIST_LINE_RE.match(lines[i]):
                intro_lines.append(lines[i].strip())
                i += 1
            intro_text = " ".join(intro_lines).strip()
            if intro_text:
                # Split intro by sentence boundary (period + space, letter before period)
                parts = _SENTENCE_RE.split(intro_text)
                if len(parts) == 1 and parts[0]:
                    segments.append(parts[0].strip() + ("." if not parts[0].strip().endswith(".") else ""))
                else:
                    for p in parts:
                        p = p.strip()
                        if not p:
                            continue
                        if not p.endswith("."):
                            p = p + "."
                        segments.append(p)
            # i already advanced
    if not segments:
        return [text]
    return segments


def _segment_paragraph(nr: str, text: str) -> list[tuple[str, str]]:
    """
    Given a row Nr (e.g. 6.1, 6.2) and full text, return list of (new_nr, segment_text)
    with Absatz.Satz numbering: 6.1 -> 1.1, 1.2, ...; 6.2 -> 2.1, 2.2, ...
    """
    parts = nr.split(".")
    if len(parts) != 2:
        return [(nr, text)]
    _sec, absatz = parts[0], parts[1]
    segments = _split_paragraph_text(text)
    out: list[tuple[str, str]] = []
    for idx, seg in enumerate(segments, start=1):
        out.append((f"{absatz}.{idx}", seg))
    return out


def _write_fine_inventory(sections: list[Section], out_path: Path) -> None:
    """Write refined inventory: same structure, but table rows use Absatz.Satz and split content."""
    # Derive law name from the first source_paragraph found (e.g. "§1 BbgBO" -> "BbgBO")
    law_name = "LBO"
    for sec in sections:
        if sec.source_paragraph:
            parts = sec.source_paragraph.replace("**source_paragraph:**", "").strip().split()
            if len(parts) >= 2:
                law_name = parts[-1]
                break
    lines = [
        f"# {law_name} — Node Inventory (Sentence / List-Item Level)",
        "",
        "_Refined from paragraph-level inventory by split_inventory_to_sentences.py. One row per sentence or numbered list item._",
        "",
    ]
    for sec in sections:
        if not sec.heading.startswith("### "):
            continue
        lines.append(sec.heading)
        lines.append(sec.type_line)
        lines.append(sec.source_paragraph)
        lines.append("")
        lines.append(f"| Nr. | Regeltext ({law_name}-Wortlaut) |")
        lines.append("|---|---|")
        for nr, text in sec.rows:
            for new_nr, segment in _segment_paragraph(nr, text):
                # Strip leading superscript sentence numbers (e.g. "1Dieses" -> "Dieses")
                segment = re.sub(r"^\d+(?=[A-ZÄÖÜ])", "", segment)
                # Escape pipe in text for markdown table
                cell = segment.replace("|", "\\|").replace("\n", " ")
                if len(cell) > 400:
                    cell = cell[:397] + "..."
                lines.append(f"| {new_nr} | {cell} |")
        lines.append("")
        lines.append("---")
        lines.append("")
    out_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Split LBO node inventory to sentence/list-item granularity")
    parser.add_argument("--input", type=Path, default=_DEFAULT_INPUT, help="Input inventory path")
    parser.add_argument("--output", type=Path, default=_DEFAULT_OUTPUT, help="Output inventory path")
    args = parser.parse_args()
    if not args.input.exists():
        raise SystemExit(f"Input not found: {args.input}")
    sections = _parse_inventory(args.input)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    _write_fine_inventory(sections, args.output)
    total_rows = sum(len(sec.rows) for sec in sections)
    total_fine = sum(
        len(_segment_paragraph(nr, text))
        for sec in sections
        for nr, text in sec.rows
    )
    print(f"Wrote {args.output}")
    print(f"  Sections: {len(sections)}, original rows: {total_rows}, fine rows: {total_fine}")


if __name__ == "__main__":
    main()
