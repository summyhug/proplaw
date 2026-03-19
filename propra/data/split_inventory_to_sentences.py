"""
Split an LBO node inventory from paragraph-level to sentence/list-item level.

Reads a markdown inventory with one row per Absatz (e.g. | 6.1 | ... |, | 6.2 | ... |)
and emits a new inventory with one row per sentence or numbered list item, using
Absatz.Satz IDs (e.g. 1.1, 1.2, 2.1, 2.2) so the structure matches MBO granularity.

Inline numbered lists in one paragraph (e.g. ", 1. ... 2. ... 3. ...") are split so each
"N. " is its own row. Newline-started "1. ", "2. " are already handled.
Limitations: "Abs.", "Nr.", "Satz." can cause over-splitting on period+space.

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

# Sentence boundary: period + space, when period follows a letter.
# NOTE: we do NOT want to split after common legal abbreviations like "Abs.", "Nr.", "BGBl.".
# We therefore use a conservative heuristic splitter instead of relying only on a regex.
_SENTENCE_RE = re.compile(r"(?<=[a-zäöüßA-ZÄÖÜ])\.\s+")
# Line that starts a numbered list item: optional space, digits, period, space
_LIST_LINE_RE = re.compile(r"^\s*(\d+)\.\s+", re.MULTILINE)
# Inline numbered list: ", 2. " or ", 3. " (comma, space, number, period, space) — same paragraph
_INLINE_LIST_RE = re.compile(r", (\d+)\.\s+")

# Abbreviations that commonly appear before a dot but are not sentence ends.
_ABBREV = {
    "abs", "nr", "satz", "art", "vgl", "z", "b", "z.b", "d.h", "u.a", "bzw",
    "ggf", "insb", "i.s.d", "i.s.v", "bgbl", "s", "i", "ii", "iii",
}


def _split_sentences(text: str) -> list[str]:
    """
    Split text into sentences using a conservative heuristic.

    Splits on '. ' only when the token before the dot is not a known abbreviation
    (e.g. avoids splitting at 'BGBl. I S. 1519').
    """
    t = re.sub(r"\s+", " ", text.strip())
    if not t:
        return []

    parts: list[str] = []
    start = 0
    i = 0
    while i < len(t) - 1:
        if t[i] == "." and t[i + 1] == " ":
            # token before the dot (letters only)
            j = i - 1
            while j >= 0 and t[j].isalpha():
                j -= 1
            token = t[j + 1 : i].lower()
            if token and token in _ABBREV:
                i += 1
                continue
            seg = t[start:i + 1].strip()
            if seg:
                parts.append(seg)
            start = i + 2
            i += 2
            continue
        i += 1
    tail = t[start:].strip()
    if tail:
        parts.append(tail)
    return parts


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
                if re.match(r"^\d+\.\d+$", first):
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
                # Scenario 1: intro ends with "... für 1. <item>, 2. <item>, ..."
                # We want the "1." item to be its own node, not glued to the intro.
                m1 = re.search(r"\b(für)\s+1\.\s+", intro_text)
                if m1:
                    head = intro_text[: m1.start(1)].rstrip()
                    fuer = intro_text[m1.start(1) : m1.end(1)].strip()  # "für"
                    rest = intro_text[m1.end(1) :].strip()  # starts with "1. ..."
                    if head:
                        segments.append(f"{head} {fuer}".strip())
                    intro_text = f"1. {rest}".strip()

                # Inline numbered list: ", 2. ", ", 3. " etc. — each N. is its own bullet
                inline_parts = _INLINE_LIST_RE.split(intro_text)
                if len(inline_parts) >= 3 and len(inline_parts) % 2 == 1:
                    # [head_with_1, "2", tail_2, "3", tail_3, ...]; head includes "1. first item"
                    segments.append(inline_parts[0].strip())
                    for i in range(1, len(inline_parts) - 1, 2):
                        num = inline_parts[i]
                        rest = inline_parts[i + 1].strip()
                        segments.append(f"{num}. {rest}")
                else:
                    # Split by sentence boundary (abbreviation-aware)
                    parts = _split_sentences(intro_text)
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
    lines = [
        "# BbgBO — Node Inventory (Sentence / List-Item Level)",
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
        lines.append("| Nr. | Regeltext (BbgBO-Wortlaut) |")
        lines.append("|---|---|")
        for nr, text in sec.rows:
            for new_nr, segment in _segment_paragraph(nr, text):
                cell = segment.replace("|", "\\|").replace("\n", " ")
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
