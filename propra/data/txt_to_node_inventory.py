"""
Converts MBO.txt (PDF-extracted plain text) into MBO_node_inventory.md.

Preserves legal hierarchy: § (Paragraf) → (1), (2) (Absatz) → 1., 2., a) (Satz/Nummer).
Each Absatz is emitted as a #### subheading with its own table; each row is one
Satz or list item so nodes get a clear legal address (e.g. §1 Abs. 2 MBO, row 2.3).

Optional preprocessing: strip standalone page-number lines and footnote refs
(word + digit, e.g. Tageseinrichtungen1 → Tageseinrichtungen) from the raw text.

Usage:
    python propra/data/txt_to_node_inventory.py

Input:  propra/data/txt/MBO.txt
Output: propra/data/node inventory/MBO_node_inventory.md
"""

import re
from pathlib import Path

# Paths
_DATA = Path(__file__).parent
_MBO_TXT = _DATA / "txt" / "MBO.txt"
_MBO_INVENTORY = _DATA / "node inventory" / "MBO_node_inventory.md"

# Regex: line is only digits (page number)
_PAGE_NUMBER_LINE = re.compile(r"^\s*\d+\s*$")
# Footnote ref: word character(s) + 1–2 digits at word end (e.g. Tageseinrichtungen1)
_FOOTNOTE_REF = re.compile(r"([a-zA-ZäöüÄÖÜß]+)(\d{1,2})(?=\s|$|[\.,;:\)])")


def _preprocess_mbo_text(raw: str) -> str:
    """
    Clean MBO.txt before parsing: remove page-number lines and footnote refs.

    - Page numbers: lines that contain only digits and whitespace (e.g. "  6  ").
    - Footnote refs: digit(s) glued to a word (e.g. Tageseinrichtungen1 → Tageseinrichtungen).
    """
    lines = raw.splitlines()
    out = []
    for line in lines:
        if _PAGE_NUMBER_LINE.match(line.strip()):
            continue
        # Strip footnote refs (word + digit) from the line
        cleaned = _FOOTNOTE_REF.sub(r"\1", line)
        out.append(cleaned)
    return "\n".join(out)


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


def _split_into_absatz_blocks(merged: str) -> list[tuple[str, list[str]]]:
    """
    Split merged § content by hierarchy: (1), (2) = Absatz; within each, split by
    sentence (1Text, 2Text) or list (1., 2., a), b)) into rule strings.

    Returns [(absatz_num, [rule1, rule2, ...]), ...] so we can emit one #### and
    one table per Absatz with clear source_paragraph (§N Abs. K MBO).
    """
    if not merged or not merged.strip():
        return []
    text = re.sub(r"\s+", " ", merged).strip()
    # Split by Absatz (1), (2), (3)...
    absatz_parts = re.split(r"\s*\((\d+)\)\s*", text)
    if len(absatz_parts) <= 1 and "(" not in text:
        absatz_parts = ["", "1", text]
    blocks: list[tuple[str, list[str]]] = []
    i = 1
    while i < len(absatz_parts):
        absatz_num = absatz_parts[i]
        content = absatz_parts[i + 1] if i + 1 < len(absatz_parts) else ""
        i += 2
        if not content.strip():
            continue
        # Within this Absatz: split by sentence (1Text, 2Text) or list (1., 2., a), b))
        parts = re.split(r"\s+(?=\d+[A-ZÄÖÜ.]|\d+\.\s)", content)
        rules: list[str] = []
        for p in parts:
            p = p.strip()
            if not p or len(p) < 2:
                continue
            # Remove leading "1." "2." "a)" from list items
            p = re.sub(r"^\d+\.\s*", "", p)
            p = re.sub(r"^[a-z]\)\s*", "", p)
            # Remove leading sentence number (1Text → Text, 2Abweichend → Abweichend)
            p = re.sub(r"^\d+([A-ZÄÖÜ])", r"\1", p)
            if not p.strip():
                continue
            rules.append(p.strip())
        if rules:
            blocks.append((absatz_num, rules))
    return blocks


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
    raw = _preprocess_mbo_text(raw)
    all_lines = raw.splitlines()

    # Body starts after TOC: find § 1 that is followed by (1) (first Absatz), not the TOC entry
    body_start = 0
    for i, line in enumerate(all_lines):
        s = line.strip()
        if not (s == "§ 1" or re.match(r"^§\s+1\s", s)):
            continue
        # Look forward for "(1)" or "(1) 1" (first Absatz) within 15 lines
        for j in range(i + 1, min(i + 15, len(all_lines))):
            if re.match(r"^\(\d+\)", all_lines[j].strip()):
                body_start = i
                break
        if body_start:
            break
    if body_start > 0:
        # Include "Erster Teil" / part header just above
        for j in range(body_start - 1, max(0, body_start - 15), -1):
            if _part_or_abschnitt(all_lines[j]):
                body_start = j
                break
    body_lines = all_lines[body_start:]

    # Split into sections: each section starts with § N or Part/Abschnitt
    sections: list[tuple[str, str, list[str]]] = []  # (kind, title_or_num, lines)
    current: list[str] = []
    current_kind = ""
    current_title = ""

    for idx, line in enumerate(body_lines):
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
            # If title empty (e.g. "§ 1" on one line, "Anwendungsbereich" on next), use next non-empty line
            if not title.strip() and idx + 1 < len(body_lines):
                for next_line in body_lines[idx + 1 : idx + 4]:
                    t = next_line.strip()
                    if t and not _section_starts(t) and not _part_or_abschnitt(next_line) and not re.match(r"^\(\d+\)", t):
                        title = t
                        break
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

    for kind, title_or_num, content in sections:
        if kind == "part":
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
        blocks = _split_into_absatz_blocks(merged)
        if not blocks:
            # Fallback: no (1)(2) structure — single row under this §
            rule_text = merged[:2000] + "…" if len(merged) > 2000 else merged
            if rule_text:
                md.append("| Nr. | Regeltext (MBO-Wortlaut) |\n")
                md.append("|---|---|\n")
                rule_esc = rule_text.replace("|", "\\|").replace('"', "'")
                md.append(f'| {num}.1 | „{rule_esc}" |\n')
        else:
            for absatz_num, rules in blocks:
                md.append(f"\n#### §{num} Abs. {absatz_num}\n\n")
                md.append(f"**source_paragraph:** §{num} Abs. {absatz_num} MBO\n\n")
                md.append("| Nr. | Regeltext (MBO-Wortlaut) |\n")
                md.append("|---|---|\n")
                for idx, rule in enumerate(rules[:150], 1):  # cap per Absatz
                    rule_esc = rule.replace("|", "\\|").replace('"', "'")
                    if len(rule_esc) > 500:
                        rule_esc = rule_esc[:497] + "…"
                    row_id = f"{absatz_num}.{idx}"
                    md.append(f'| {row_id} | „{rule_esc}" |\n')
        md.append("\n---\n")

    _MBO_INVENTORY.write_text("".join(md), encoding="utf-8")
    print(f"Wrote {_MBO_INVENTORY} ({len(sections)} section blocks)")


if __name__ == "__main__":
    main()
