"""
Converts MBO.txt (PDF-extracted plain text) into MBO_node_inventory.md.

Produces a structured node inventory in the same format as BW_LBO_node_inventory.md
(see that file as the reference). parse_inventory.py loads the result for the
knowledge graph. Sections are detected from § markers; (1)/(2) Absatz markers
and sentence/list numbering are used to split content into numbered rules.

Usage:
    python propra/data/txt_to_node_inventory.py

Input:  propra/data/raw/MBO.txt
Output: propra/data/MBO_node_inventory.md

After running, you can refine individual sections (e.g. §6 Abstandsflächen,
§61 Verfahrensfreiheit) manually and add numeric_values tables as in BW_LBO.
"""

import re
from pathlib import Path

# Paths
_DATA = Path(__file__).parent
_RAW = _DATA / "raw"
_MBO_TXT = _RAW / "MBO.txt"
_MBO_INVENTORY = _DATA / "MBO_node_inventory.md"

# MBO metadata (from the PDF header)
_MBO_HEADER = """# MBO — Knotenverzeichnis
## Musterbauordnung (MBO)
**source:** MBO Fassung November 2002, zuletzt geändert durch Beschluss der Bauministerkonferenz vom 26./27.9.2024
**jurisdiction:** DE-MBO
**node_prefix:** MBO_

---

> **purpose:** Vollständiges strukturiertes Verzeichnis aller Paragrafen und Regeltexte der MBO. Vorbereitungsdokument für den Wissensgraphen. Der Regeltext entspricht dem Wortlaut der MBO.

---

"""


def _section_starts(line: str) -> bool:
    """True if line is start of a § section (e.g. '§ 1' or '§ 2 Begriffe')."""
    return bool(re.match(r"^§\s+\d+[a-z]?\s", line) or re.match(r"^§\s+\d+[a-z]?\s*$", line))


def _part_or_abschnitt(line: str) -> str | None:
    """Returns part name if line is 'Erster Teil ...' or '... Abschnitt ...', else None."""
    s = line.strip()
    if re.match(r"^(Erster|Zweiter|Dritter|Vierter|Fünfter|Sechster|Siebenter)\s+Teil\s", s):
        return s
    if "Abschnitt" in s and len(s) < 120:
        return s
    return None


def _extract_para_and_title(line: str) -> tuple[str, str]:
    """From '§ 6 Abstandsflächen, Abstände' return ('6', 'Abstandsflächen, Abstände')."""
    m = re.match(r"^§\s+(\d+[a-z]?)\s*(.*)$", line.strip())
    if not m:
        return "", ""
    num, rest = m.groups()
    title = rest.strip().strip("—").strip()
    return num, title


def _is_absatz_marker(line: str) -> bool:
    return bool(re.match(r"^\(\d+\)\s*$", line.strip()))


def _merge_section_lines(lines: list[str]) -> str:
    """Merge content lines into one string; continuations get joined with space."""
    out: list[str] = []
    for line in lines:
        s = line.strip()
        if not s:
            continue
        # Continuation: line does not start with §, (1), 1., 2., a), b), or " 1" " 2" (sentence)
        if re.match(r"^§\s+\d+", s):
            continue  # skip § header in content
        if re.match(r"^\(\d+\)\s*$", s):
            out.append(f" ({s}) ")
            continue
        if re.match(r"^\d+\.\s*$", s) or re.match(r"^[a-z]\)\s*$", s):
            out.append(f" {s} ")
            continue
        if re.match(r"^\s*\d+[A-ZÄÖÜa-z]", s):  # sentence start " 1Dieses"
            out.append(" " + s)
            continue
        out.append(" " + s)
    return " ".join(out).strip()


def _split_into_rules(merged: str) -> list[str]:
    """
    Split merged section text into rule strings.
    Splits by (1), (2), then by sentence numbers ( 1… 2…) and list items (1. 2. a) b)).
    """
    if not merged or not merged.strip():
        return []
    # Normalize: single spaces
    text = re.sub(r"\s+", " ", merged).strip()
    rules: list[str] = []
    # Split by Absatz (1), (2), (3)...
    absatz_parts = re.split(r"\s*\((\d+)\)\s*", text)
    if len(absatz_parts) <= 1 and "(" not in text:
        # No (1)(2) found — treat whole as one block
        absatz_parts = ["", "1", text]
    # absatz_parts = [before_first, "1", content1, "2", content2, ...]
    i = 1
    while i < len(absatz_parts):
        absatz_num = absatz_parts[i]
        content = absatz_parts[i + 1] if i + 1 < len(absatz_parts) else ""
        i += 2
        if not content.strip():
            continue
        # Within this Absatz, split by " 1" " 2" (sentence) or " 1." " 2." (list)
        # Pattern: space + digit + (capital letter or ".") = new sentence/list
        parts = re.split(r"\s+(?=\d+[A-ZÄÖÜ.]|\d+\.\s)", content)
        sub = 0
        for p in parts:
            p = p.strip()
            if not p or len(p) < 3:
                continue
            # Remove leading "1." "2." from list items so we don't duplicate
            p = re.sub(r"^\d+\.\s*", "", p)
            p = re.sub(r"^[a-z]\)\s*", "", p)
            if not p.strip():
                continue
            sub += 1
            rules.append(p.strip())
    return rules


def _infer_type(title: str) -> str:
    """Infer **type:** from § title. Returns only labels that match schema NODE_TYPES."""
    t = title.lower()
    if "anwendungsbereich" in t:
        return "Anwendungsbereich"
    if "begriffe" in t:
        return "Begriffsbestimmung"
    if "allgemeine anforderung" in t or "allgemeine anforderungen" in t:
        return "Allgemeine Anforderung"
    if "abstandsflächen" in t or "abstände" in t:
        return "Abstandsfläche"
    if "bebauung" in t and "grundstück" in t:
        return "Grundstücksbebauung"
    if "zugänge" in t or "zufahrten" in t:
        return "Grundstücksbebauung"  # access/zufahrten → schema has no zufahrten
    if "teilung" in t and "grundstück" in t:
        return "Grundstücksteilung"
    if "gestaltung" in t or "werbung" in t or "warenautomaten" in t:
        return "Gestaltungsanforderung"
    if "baustelle" in t:
        return "Baustellenanforderung"
    if "standsicherheit" in t:
        return "Standsicherheit"
    if "brandschutz" in t or "brandverhalten" in t:
        return "Brandschutzanforderung"
    if "rettungsweg" in t or "treppen" in t or "umwehrungen" in t or "öffnungen" in t:
        return "Treppe"  # Rettungswege → treppe/treppenraum; schema has no rettungswege
    if "verfahren" in t or "genehmigung" in t or "bauaufsicht" in t:
        return "Genehmigungspflicht"
    if "ordnungswidrig" in t:
        return "Sanktion"
    if "rechtsvorschrift" in t or "baubestimmung" in t:
        return "Ermächtigungsgrundlage"
    return "Allgemeine Anforderung"  # fallback: schema has no "Vorschrift"


def _build_toc_titles(lines: list[str]) -> dict[str, str]:
    """
    From TOC block (before body), build § number -> title where possible.
    TOC has '§ 1' '§ 2' '§ 3' then next line 'Anwendungsbereich Begriffe Allgemeine Anforderungen'.
    We use body headers as primary; this is only for §§ that have no title in body.
    """
    titles: dict[str, str] = {}
    # In body we get titles from "§ N Title"; TOC is messy (multiple § on one line of titles). Skip.
    return titles


def main() -> None:
    raw = _MBO_TXT.read_text(encoding="utf-8")
    all_lines = raw.splitlines()

    # Body starts after TOC: first "§ 1 Anwendungsbereich" (with title) marks the real §1
    body_start = 0
    for i, line in enumerate(all_lines):
        s = line.strip()
        if re.match(r"^§\s+1\s+Anwendungsbereich\s*$", s):
            # Include the "Erster Teil" header just above: walk back to previous part
            body_start = i
            for j in range(i - 1, max(0, i - 15), -1):
                if "Erster Teil" in all_lines[j] and "Allgemeine" in all_lines[j]:
                    body_start = j
                    break
            break
    if body_start == 0:
        body_start = 0  # fallback to start of file

    body_lines = all_lines[body_start:]

    # Split into sections: each section starts with § N or Part/Abschnitt
    sections: list[tuple[str, str, list[str]]] = []  # (kind, title_or_num, lines)
    current: list[str] = []
    current_kind = ""
    current_title = ""

    for line in body_lines:
        stripped = line.strip()
        part = _part_or_abschnitt(line)
        if part:
            if current and (current_kind == "para" or current_kind == "part"):
                sections.append((current_kind, current_title, current))
                current = []
            current_kind = "part"
            current_title = part
            sections.append(("part", part, []))
            continue
        if _section_starts(line):
            if current and current_kind == "para":
                sections.append((current_kind, current_title, current))
                current = []
            num, title = _extract_para_and_title(line)
            current_kind = "para"
            current_title = f"{num}|{title}"  # num and optional title
            current = []
            continue
        if current_kind == "para" or (current_kind == "part" and current_title and not current):
            if current_kind == "part" and not current:
                continue
            current.append(line)

    if current and current_kind == "para":
        sections.append((current_kind, current_title, current))

    # Build markdown
    md: list[str] = [_MBO_HEADER]
    current_part = ""

    for kind, title_or_num, content in sections:
        if kind == "part":
            current_part = title_or_num
            # Drop leading page number if present (e.g. "2 Siebenter Abschnitt" -> "Siebenter Abschnitt")
            title_or_num = re.sub(r"^\d+\s+", "", title_or_num.strip()).strip()
            # "Erster Teil Allgemeine Vorschriften" -> "## ERSTER TEIL — Allgemeine Vorschriften"
            if " Teil " in title_or_num:
                a, _, b = title_or_num.partition(" Teil ")
                part_name = f"{a.strip().upper()} TEIL — {b.strip()}"
                md.append(f"\n## {part_name}\n")
            else:
                md.append(f"\n## {title_or_num.upper()}\n")
            continue
        if kind != "para":
            continue
        num, section_title = title_or_num.split("|", 1) if "|" in title_or_num else (title_or_num, "")
        section_title = section_title.strip()
        if not section_title and num:
            section_title = f"§ {num}"
        heading = f"### §{num} — {section_title}" if section_title else f"### §{num}"
        md.append(f"\n{heading}\n")
        type_label = _infer_type(section_title)
        md.append(f"**type:** {type_label}\n")
        md.append(f"**source_paragraph:** §{num} MBO\n\n")

        merged = _merge_section_lines(content)
        rules = _split_into_rules(merged)
        if not rules:
            # Fallback: single row with full merged text (truncated if very long)
            rule_text = merged[:2000] + "…" if len(merged) > 2000 else merged
            if rule_text:
                md.append("| Nr. | Regeltext (MBO-Wortlaut) |\n")
                md.append("|---|---|\n")
                md.append(f'| {num}.1 | „{rule_text}" |\n')
        else:
            md.append("| Nr. | Regeltext (MBO-Wortlaut) |\n")
            md.append("|---|---|\n")
            for idx, rule in enumerate(rules[:200], 1):  # cap 200 rules per §
                rule_esc = rule.replace("|", "\\|").replace('"', "'")
                if len(rule_esc) > 500:
                    rule_esc = rule_esc[:497] + "…"
                md.append(f'| {num}.{idx} | „{rule_esc}" |\n')
        md.append("\n---\n")

    _MBO_INVENTORY.write_text("".join(md), encoding="utf-8")
    print(f"Wrote {_MBO_INVENTORY} ({len(sections)} section blocks)")


if __name__ == "__main__":
    main()
