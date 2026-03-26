"""
Generate BayBO_node_inventory_v2.md from BayBO.txt.

BayBO uses 'Art. N' numbering (not §). Art. headings are embedded inline
in BayBO.txt rather than on separate lines. This script:
  1. Locates genuine section heading positions ('Art. N TitleWord') in the text.
  2. Splits the text into per-section blocks.
  3. Splits each block into Absätze (marked by '(N)').
  4. Outputs BayBO_node_inventory_v2.md in the ### § N — Title format
     expected by split_inventory_to_sentences.py and parse_inventory.py.
  5. Node types are taken from the existing BayBO_node_inventory.md where
     available, so no API calls are needed.

Usage:
    python propra/data/generate_baybo_inventory_v2.py
"""

from __future__ import annotations

import re
from pathlib import Path

# ── paths ──────────────────────────────────────────────────────────────────────
_DATA = Path(__file__).parent
_TXT_IN = _DATA / "txt" / "BayBO.txt"
_OLD_INVENTORY = _DATA / "node inventory" / "BayBO_node_inventory.md"
_MD_TITLES = _DATA.parent.parent / "data" / "data" / "BayBO_.md"
_V2_OUT = _DATA / "node inventory" / "BayBO_node_inventory_v2.md"

# ── helpers ────────────────────────────────────────────────────────────────────

# Words after "Art. N" that signal an inline cross-reference, not a heading.
_INLINE_FIRST_WORDS = frozenset({
    "abs", "nr", "satz", "gilt", "bis", "und", "oder",
    "nach", "keine", "bleibt", "entsprechend", "entspricht",
    "findet", "finden", "in", "im", "der", "die", "des",
    "dem", "den", "eine", "einem", "einen", "einer",
    "vom", "von", "an", "zu", "ist", "sind", "hat",
    "bayvwvfg", "baukag", "baybqfg", "buchst",
    "go", "vwgo", "bgb", "bverfg", "bgbl",
})

# German verbs / function words that end a section title and start body text.
_TITLE_STOP_WORDS = frozenset({
    "sind", "wird", "werden", "ist", "hat", "haben",
    "muss", "mussen", "darf", "durfen", "soll", "sollen",
    "kann", "konnen", "bei", "dass", "soweit", "wenn",
    "fur", "durch", "unter", "aus", "so", "auch",
    "nur", "nicht", "jedoch", "insbesondere",
    "eine", "einen", "einem", "einer", "eines",
    "alle", "jede", "jeder", "jedes",
})

# Regex: "Art. N[a]" where N is 1-3 digits, optional letter suffix
_ART_RE = re.compile(r"Art\.\s+(\d+[a-zA-Z]?)\s+")


def _is_heading_word(word: str) -> bool:
    """Return True if the word after Art. N likely starts a section title."""
    if not word:
        return False
    w = word.lower().rstrip(",.:;()")
    if w in _INLINE_FIRST_WORDS:
        return False
    return word[0].isupper()


def _extract_title(rest: str) -> str:
    """
    Extract a clean section title from text just after 'Art. N '.
    Stops at a title-stop word, explicit (N) Absatz marker, digit, or newline.
    """
    title_words: list[str] = []
    for raw_word in rest.split()[:8]:  # at most 8 words for a title
        if "\n" in raw_word:
            break
        word = raw_word.rstrip(".,;:")
        if re.match(r"^\(\d+\)$", word):  # Absatz marker
            break
        if re.match(r"^\d", word):  # starts with digit
            break
        if word.lower().rstrip(",.:;") in _TITLE_STOP_WORDS:
            break
        title_words.append(word.rstrip(","))
    return " ".join(title_words)


def load_title_map_from_md(md_path: Path) -> dict[str, str]:
    """
    Parse BayBO_.md to extract official Art. N -> section title mappings.
    Format: ***Art. N** * *Title (possibly on two lines)***
    Umlauts are encoded as **X** (e.g. **ä**) in the markdown source.
    """
    title_map: dict[str, str] = {}
    if not md_path.exists():
        return title_map
    header_re = re.compile(r"^\*\*\*Art\.\s+(\d+[a-zA-Z]?)\*\*\s+\*\s+\*(.*)")
    lines = md_path.read_text(encoding="utf-8").splitlines()
    i = 0
    while i < len(lines):
        m = header_re.match(lines[i])
        if m:
            num = m.group(1)
            raw = m.group(2)
            # Title may continue on the very next line (multi-line headings)
            if not raw.rstrip().endswith("***") and i + 1 < len(lines):
                raw = raw + " " + lines[i + 1]
                i += 1
            raw = raw.rstrip("*").strip()
            # Decode **X** umlaut/special-char encoding -> X
            title = re.sub(r"\*\*([^*]+)\*\*", r"\1", raw)
            # Remove footnote superscripts like ^1^
            title = re.sub(r"\^[0-9]+\^", "", title)
            # Remove any remaining markdown * markers; normalise whitespace
            title = re.sub(r"\*+", "", title)
            title = re.sub(r"\s+", " ", title).strip()
            if title:
                title_map[num] = title
        i += 1
    return title_map


def find_sections(
    text: str, title_map: dict[str, str] | None = None
) -> list[tuple[str, str, int, int]]:
    """
    Return list of (num, title, start, end) for each genuine Art. heading.
    'start' and 'end' are character positions in text.
    Deduplicates: only the first occurrence of each Art. number is kept.
    Official titles from title_map (parsed from BayBO_.md) take precedence
    over the heuristic _extract_title() fallback.
    """
    if title_map is None:
        title_map = {}
    seen: set[str] = set()
    sections: list[tuple[str, str, int, int]] = []

    for m in _ART_RE.finditer(text):
        num = m.group(1)
        if num in seen:
            continue  # keep only first occurrence (the actual heading)
        rest = text[m.end():]
        # First word of rest (what follows the number)
        first_word = rest.split()[0] if rest.split() else ""
        if not _is_heading_word(first_word):
            continue
        # Official title takes precedence; heuristic as fallback
        title = title_map.get(num) or _extract_title(rest)
        seen.add(num)  # Always mark seen once a genuine heading is confirmed
        if not title or len(title) < 2:
            continue
        sections.append((num, title, m.start(), -1))

    # Fill in end positions
    result: list[tuple[str, str, int, int]] = []
    for i, (num, title, start, _) in enumerate(sections):
        end = sections[i + 1][2] if i + 1 < len(sections) else len(text)
        result.append((num, title, start, end))

    return result


def split_absaetze(block: str, title: str, num: str) -> list[tuple[str, str]]:
    """
    Split a section block into Absätze, returning (absatz_num, text) pairs.
    Uses the extracted title to precisely skip the heading.
    """
    # Strip everything up to and including "Art. N[a] "
    art_prefix = re.compile(
        r"^.*?Art\.\s+" + re.escape(num) + r"[a-zA-Z]?\s+",
        re.DOTALL,
    )
    body = art_prefix.sub("", block, count=1).strip()

    # Skip the exact title words from the beginning of the body
    for tw in title.split():
        m = re.match(r"^" + re.escape(tw) + r"[,.]?\s*", body, re.IGNORECASE)
        if m:
            body = body[m.end():]
        else:
            break
    body = body.strip()

    if not body:
        return []

    # Split at explicit (N) Absatz markers
    parts = re.split(r"(?=\(\d+\))", body)
    result: list[tuple[str, str]] = []
    preamble_parts: list[str] = []

    for part in parts:
        part = part.strip()
        if not part:
            continue
        m = re.match(r"^\((\d+)\)\s*", part)
        if m:
            if preamble_parts:
                preamble = " ".join(preamble_parts).strip()
                if preamble:
                    result.append(("1", preamble))
                preamble_parts = []
            abs_num = m.group(1)
            text = part[m.end():].strip()
            if text:
                result.append((abs_num, text))
        else:
            preamble_parts.append(part)

    # Flush remaining as single-absatz section
    if preamble_parts and not result:
        body_text = " ".join(preamble_parts).strip()
        if body_text:
            result.append(("1", body_text))

    return result


def load_type_map(old_inv: Path) -> dict[str, str]:
    """
    Extract {section_num: node_type} from the flat-table BayBO_node_inventory.md.
    Uses the type of the first row for each section.
    """
    type_map: dict[str, str] = {}
    if not old_inv.exists():
        return type_map

    row_re = re.compile(r"^\|\s*(\d+[a-zA-Z]?)\.\d+\s*\|[^|]+\|[^|]+\|\s*(\w+)\s*\|")
    for line in old_inv.read_text(encoding="utf-8").splitlines():
        m = row_re.match(line)
        if m:
            sec = m.group(1)
            typ = m.group(2).strip()
            if sec not in type_map:
                type_map[sec] = typ
    return type_map


def infer_section_type(
    num: str,
    title: str,
    legacy_types: dict[str, str],
) -> str:
    """
    Pick a stable BayBO section type.

    BayBO's legacy flat inventory drifts badly through large parts of the law,
    so we prefer explicit BayBO corrections for the shifted sections while
    falling back to the legacy type map elsewhere.
    """
    del title
    return _BAYBO_SECTION_TYPE_OVERRIDES.get(num, legacy_types.get(num, "allgemeine_anforderung"))


_HEADER = """\
# BayBO — Node Inventory (Paragraph Level)

_Generated by generate_baybo_inventory_v2.py from BayBO.txt. \\
One row per Absatz. Node types sourced from existing inventory._

"""

_BAYBO_SECTION_TYPE_OVERRIDES = {
    "7": "freiflaechengestaltung",
    "8": "gestaltungsanforderung",
    "9": "baustellenanforderung",
    "10": "standsicherheit",
    "11": "schutzanforderung",
    "12": "brandschutzanforderung",
    "14": "verkehrssicherheit",
    "15": "bauproduktzulassung",
    "16": "bauproduktzulassung",
    "24": "brandklassifizierung",
    "25": "tragende_wand",
    "26": "aussenwand",
    "27": "trennwand",
    "28": "brandwand",
    "29": "decke",
    "30": "dach",
    "31": "brandschutzanforderung",
    "32": "treppe",
    "33": "treppenraum",
    "34": "notwendiger_flur",
    "35": "fensteroffnung",
    "36": "allgemeine_anforderung",
    "37": "aufzugsanlage",
    "38": "technische_anlage",
    "39": "technische_anlage",
    "42": "sanitaerraum",
    "43": "technische_anlage",
    "44a": "technische_anlage",
    "45": "aufenthaltsraum",
    "46": "wohnung",
    "47": "stellplatzpflicht",
    "48": "barrierefreiheit",
    "49": "beteiligtenpflicht",
    "50": "beteiligtenpflicht",
    "51": "beteiligtenpflicht",
    "53": "behoerdenstruktur",
    "54": "behoerdenstruktur",
    "55": "genehmigungspflicht",
    "56": "genehmigungspflicht",
    "57": "verfahrensfreies_vorhaben",
    "58": "kenntnisgabeverfahren",
    "59": "vereinfachtes_genehmigungsverfahren",
    "61": "beteiligtenpflicht",
    "61a": "beteiligtenpflicht",
    "61b": "beteiligtenpflicht",
    "63": "abweichung",
    "64": "bauantrag",
    "65": "bauantrag",
    "66": "nachbarbenachrichtigung",
    "67": "baugenehmigung",
    "68": "baugenehmigung",
    "70": "baugenehmigung",
    "71": "bauvorbescheid",
    "73": "besonderes_verfahren",
    "75": "bauueberwachung",
    "76": "sanktion",
    "77": "bauueberwachung",
    "78": "baubeginn",
    "79": "sanktion",
    "80": "ermaechtigungsgrundlage",
    "80a": "baugenehmigung",
    "81": "oertliche_bauvorschrift",
    "82": "abstandsflaeche_sonderfall",
    "82a": "abstandsflaeche_sonderfall",
    "82b": "abstandsflaeche_sonderfall",
    "83": "schlussvorschrift",
    "84": "schlussvorschrift",
}


def main() -> None:
    raw = _TXT_IN.read_text(encoding="utf-8")
    legacy_type_map = load_type_map(_OLD_INVENTORY)
    title_map = load_title_map_from_md(_MD_TITLES)

    sections = find_sections(raw, title_map)
    print(f"Found {len(sections)} sections:")
    for num, title, start, end in sections:
        typ = infer_section_type(num, title, legacy_type_map)
        print(f"  Art. {num:5s} | {title[:50]:50s} | type={typ}")

    # Build output
    lines: list[str] = [_HEADER]
    written = 0

    for num, title, start, end in sections:
        block = raw[start:end]
        absaetze = split_absaetze(block, title, num)
        if not absaetze:
            continue

        node_type = infer_section_type(num, title, legacy_type_map)
        lines.append(f"### §{num} — {title}")
        lines.append(f"**type:** {node_type}")
        lines.append(f"**source_paragraph:** §{num} BayBO")
        lines.append("")
        lines.append("| Nr. | Regeltext (BayBO-Wortlaut) |")
        lines.append("|---|---|")

        for abs_num, text in absaetze:
            text_clean = text.replace("\n", " ").replace("|", "\\|").strip()
            text_clean = re.sub(r"\s{2,}", " ", text_clean)
            if text_clean:
                lines.append(f"| {num}.{abs_num} | {text_clean} |")
                written += 1

        lines.append("")
        lines.append("---")
        lines.append("")

    _V2_OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"\nWritten {written} rows across {len(sections)} sections → {_V2_OUT}")


if __name__ == "__main__":
    main()
