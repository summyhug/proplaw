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

from propra.graph.build_graph import _is_pure_heading_text
from propra.graph.build_graph import _strip_known_text_artifacts
from propra.graph.build_graph import _strip_trailing_heading_text

_INVENTORY_DIR = Path(__file__).parent / "node inventory"
_DEFAULT_INPUT = _INVENTORY_DIR / "BbgBO_node_inventory_v2.md"
_DEFAULT_OUTPUT = _INVENTORY_DIR / "BbgBO_node_inventory_fine.md"

# Sentence boundary: period + space, when period follows a letter.
# NOTE: we do NOT want to split after common legal abbreviations like "Abs.", "Nr.", "BGBl.".
# We therefore use a conservative heuristic splitter instead of relying only on a regex.
_SENTENCE_RE = re.compile(r"(?<=[a-zäöüßA-ZÄÖÜ])\.\s+")
# Line that starts a numbered list item: optional space, digits, period, space
_LIST_LINE_RE = re.compile(r"^\s*(\d+)\.\s+", re.MULTILINE)

# Abbreviations that commonly appear before a dot but are not sentence ends.
_ABBREV = {
    "abs", "nr", "satz", "art", "vgl", "z", "b", "z.b", "d.h", "u.a", "bzw",
    "ggf", "insb", "i.s.d", "i.s.v", "bgbl", "s", "i", "ii", "iii",
    "buchst", "unterabs",
}
_HEADING_TITLE_RE = re.compile(r"^###\s+§§?\s*\d+[a-zA-Z]?\s*[—\-]\s*(.+)$")
_SECTION_NUMBER_RE = re.compile(r"^§§?\s*\d+[a-zA-Z]?\s*[—\-]?\s*")
_FILLER_PUNCT_RE = re.compile(r"[.…·•_]+")
_MONTHS = {
    "januar",
    "februar",
    "maerz",
    "märz",
    "april",
    "mai",
    "juni",
    "juli",
    "august",
    "september",
    "oktober",
    "november",
    "dezember",
}
_COMPACT_SENTENCE_MARKER_RE = re.compile(r"\s+(?=\d+[A-ZÄÖÜ])")


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
            if not token:
                i += 1
                continue
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


def _split_inline_numbered_items(text: str) -> list[str]:
    """
    Split a paragraph like '... 1. foo 2. bar 3. baz' into lead-in + numbered items.

    Only triggers for a plausible sequential list that starts with 1. and continues
    with at least 2., which avoids most false positives from sentence references.
    """
    matches = []
    for match in re.finditer(r"(?<!\w)(\d+)\.\s+", text):
        next_word_match = re.match(r"([A-Za-zÄÖÜäöüß-]+)", text[match.end() :])
        next_word = next_word_match.group(1).lower() if next_word_match else ""
        if next_word in _MONTHS:
            continue
        matches.append(match)
    if len(matches) < 2:
        return []
    if matches[0].group(1) != "1" or matches[1].group(1) != "2":
        return []

    segments: list[str] = []
    head = text[:matches[0].start()].strip(" ,;:")
    if head:
        segments.append(head)

    for idx, match in enumerate(matches):
        item_start = match.start()
        item_end = matches[idx + 1].start() if idx + 1 < len(matches) else len(text)
        item = text[item_start:item_end].strip(" ,;:")
        if item:
            segments.append(item)
    return segments


def _expand_sentence_like_segments(text: str) -> list[str]:
    """Further split a segment on ordinary sentence boundaries when helpful."""
    expanded: list[str] = []
    compact_parts = [
        part.strip()
        for part in _COMPACT_SENTENCE_MARKER_RE.split(text.strip())
        if part.strip()
    ]
    if not compact_parts:
        return []

    for compact_part in compact_parts:
        parts = _split_sentences(compact_part)
        if len(parts) <= 1:
            cleaned = compact_part.strip()
            if len(compact_parts) > 1 and cleaned and not cleaned.endswith("."):
                cleaned += "."
            expanded.append(cleaned)
            continue
        for part in parts:
            cleaned = part.strip()
            if not cleaned:
                continue
            if not cleaned.endswith("."):
                cleaned += "."
            expanded.append(cleaned)
    return expanded


@dataclass
class Section:
    heading: str
    type_line: str
    source_paragraph: str
    rows: list[tuple[str, str]] = field(default_factory=list)  # (nr, text)


def _section_title_from_heading(heading: str) -> str:
    """Extract the clean section title from a markdown heading line."""
    m = _HEADING_TITLE_RE.match((heading or "").strip())
    if not m:
        return ""
    return m.group(1).strip()


def _normalize_heading_like_text(text: str) -> str:
    """Normalize a heading-like text fragment for duplicate-title comparisons."""
    cleaned = re.sub(r"\s+", " ", (text or "").strip())
    cleaned = _SECTION_NUMBER_RE.sub("", cleaned)
    cleaned = _FILLER_PUNCT_RE.sub(" ", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned.strip(" .;:-")


def _clean_segment_text(segment: str, section_title: str = "") -> str:
    """Drop heading noise and normalize obvious artifacts from fine-grained rows."""
    cleaned = re.sub(r"\s+", " ", (segment or "").strip())
    cleaned = _strip_known_text_artifacts(cleaned)
    cleaned = _strip_trailing_heading_text(cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip(" .;:-")
    if not cleaned:
        return ""
    if _is_pure_heading_text(cleaned):
        return ""
    if section_title:
        normalized_segment = _normalize_heading_like_text(cleaned)
        normalized_title = _normalize_heading_like_text(section_title)
        if normalized_segment and normalized_segment == normalized_title:
            return ""
    return cleaned


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
                # Check if first cell looks like Nr. (e.g. 1.1, 3a.2, 12.3)
                first = cells[0].strip()
                if re.match(r"^\d+[a-z]?\.\d+$", first, re.IGNORECASE):
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
                inline_segments = _split_inline_numbered_items(intro_text)
                if inline_segments:
                    for inline_segment in inline_segments:
                        segments.extend(_expand_sentence_like_segments(inline_segment))
                else:
                    # Split by sentence boundary (abbreviation-aware)
                    segments.extend(_expand_sentence_like_segments(intro_text))
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


def _law_short_from_sections(sections: list[Section]) -> str:
    """Infer the law short code from the first section's source_paragraph metadata."""
    for sec in sections:
        m = re.search(r"\*\*source_paragraph:\*\*\s+§[^\s]+\s+(.+)$", sec.source_paragraph)
        if m:
            return m.group(1).strip()
    return "LBO"


def _write_fine_inventory(sections: list[Section], out_path: Path) -> None:
    """Write refined inventory: same structure, but table rows use Absatz.Satz and split content."""
    law_short = _law_short_from_sections(sections)
    law_label = law_short.replace("_", " ")
    lines = [
        f"# {law_label} — Node Inventory (Sentence / List-Item Level)",
        "",
        "_Refined from paragraph-level inventory by split_inventory_to_sentences.py. One row per sentence or numbered list item._",
        "",
    ]
    for sec in sections:
        if not sec.heading.startswith("### "):
            continue
        section_title = _section_title_from_heading(sec.heading)
        lines.append(sec.heading)
        lines.append(sec.type_line)
        lines.append(sec.source_paragraph)
        lines.append("")
        lines.append(f"| Nr. | Regeltext ({law_label}-Wortlaut) |")
        lines.append("|---|---|")
        for nr, text in sec.rows:
            for new_nr, segment in _segment_paragraph(nr, text):
                cleaned = _clean_segment_text(segment, section_title=section_title)
                if not cleaned:
                    continue
                cell = cleaned.replace("|", "\\|").replace("\n", " ")
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
