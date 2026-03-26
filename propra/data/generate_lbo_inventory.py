"""
Generate a *_node_inventory_v2.md from a state LBO .txt + flat inventory.

Works for all § N numbered state building codes (standard German format).
Handles three txt header variants found in the corpus:

  dash_date  : § N - Title [DD.MM.YYYY ...]   (BE, HE, LSA, MV, SH, LBauO_RLP, ThuerBO)
  no_dash    : § N Title                       (NRW, LBO_SL, SaechsBO)
  synoptic   : § N Title § N Title             (HBauO comparison document)

Types are sourced from the existing flat inventory (from row IDs, not § col).
Titles come from the txt header lines where possible; flat inventory as fallback.

Usage:
    python -m propra.data.generate_lbo_inventory --state BauO_NRW
    python -m propra.data.generate_lbo_inventory --state HBauO
    python -m propra.data.generate_lbo_inventory --all
"""

from __future__ import annotations

import argparse
import os.path
import re
from pathlib import Path

from propra.graph.build_graph import _is_pure_heading_text
from propra.graph.build_graph import _strip_known_text_artifacts
from propra.graph.build_graph import _strip_trailing_heading_text

# ── State configuration ────────────────────────────────────────────────────────
# header_type:
#   dash_date  – § N - Title [date]
#   no_dash    – § N Title  (title starts immediately after number, no dash)
#   synoptic   – § N Title § N Title  (HBauO comparison document)

_STATE_CONFIGS: dict[str, dict] = {
    "BauO_BE": {
        "full_name": "Bauordnung für das Land Berlin (BauO BE)",
        "jurisdiction": "DE-BE",
        "source_suffix": "BauO_BE",
        # After trimming the repeated ToC, the actual law body parses as no_dash.
        "header_type": "no_dash",
    },
    "BauO_HE": {
        "full_name": "Hessische Bauordnung (HBO)",
        "jurisdiction": "DE-HE",
        "source_suffix": "BauO_HE",
        # After dropping the repeated ToC block, the real law body parses as no_dash.
        "header_type": "no_dash",
    },
    "BauO_NRW": {
        "full_name": "Bauordnung für das Land Nordrhein-Westfalen (BauO NRW)",
        "jurisdiction": "DE-NW",
        "source_suffix": "BauO_NRW",
        "header_type": "no_dash",
    },
    "BauO_LSA": {
        "full_name": "Bauordnung des Landes Sachsen-Anhalt (BauO LSA)",
        "jurisdiction": "DE-ST",
        "source_suffix": "BauO_LSA",
        "header_type": "no_dash",
    },
    "BauO_MV": {
        "full_name": "Landesbauordnung Mecklenburg-Vorpommern (LBauO MV)",
        "jurisdiction": "DE-MV",
        "source_suffix": "BauO_MV",
        "header_type": "no_dash",
    },
    "HBauO": {
        "full_name": "Hamburger Bauordnung (HBauO)",
        "jurisdiction": "DE-HH",
        "source_suffix": "HBauO",
        # Official PDF-backed text parses as no_dash after trimming preamble/annex.
        "header_type": "no_dash",
    },
    "LBO_SH": {
        "full_name": "Landesbauordnung Schleswig-Holstein (LBO SH)",
        "jurisdiction": "DE-SH",
        "source_suffix": "LBO_SH",
        "header_type": "no_dash",
    },
    "LBO_SL": {
        "full_name": "Landesbauordnung des Saarlandes (LBO SL)",
        "jurisdiction": "DE-SL",
        "source_suffix": "LBO_SL",
        "header_type": "no_dash",
    },
    "LBauO_RLP": {
        "full_name": "Landesbauordnung Rheinland-Pfalz (LBauO RLP)",
        "jurisdiction": "DE-RP",
        "source_suffix": "LBauO_RLP",
        "header_type": "no_dash",
    },
    "SaechsBO": {
        "full_name": "Sächsische Bauordnung (SächsBO)",
        "jurisdiction": "DE-SN",
        "source_suffix": "SaechsBO",
        "header_type": "no_dash",
    },
    "ThuerBO": {
        "full_name": "Thüringer Bauordnung (ThürBO)",
        "jurisdiction": "DE-TH",
        "source_suffix": "ThuerBO",
        "header_type": "no_dash",
    },
    "BW_LBO": {
        "full_name": "Landesbauordnung für Baden-Württemberg (LBO BW)",
        "jurisdiction": "DE-BW",
        "source_suffix": "BW_LBO",
        "header_type": "from_flat",
    },
    "BremLBO": {
        "full_name": "Bremische Landesbauordnung (BremLBO)",
        "jurisdiction": "DE-HB",
        "source_suffix": "BremLBO",
        "header_type": "from_flat",
    },
}

_DATA = Path(__file__).parent
_TXT_DIR = _DATA / "txt"
_INVENTORY_DIR = _DATA / "node inventory"

# Absatz marker: (1), (2), ... at line-start
_ABSATZ_RE = re.compile(r"^\s*\((\d+)\)\s*(.*)$")

# Section header regexes per header_type
# dash_date: § N - Title [optional date like 30.12.2023 or "14.10.2025 bis"]
_HDR_DASH_DATE = re.compile(
    r"^§\s*(\d+[a-z]*)\s*[-–]\s*(.+?)(?:\s+\d{2}\.\d{2}\.\d{4}.*)?$",
    re.IGNORECASE,
)
# no_dash: § N Title  – title starts with uppercase German letter, no parens
# Length constraint (≥ 4 chars) excludes bare "§ 1 a)" type references, and
# the negative lookahead stops us matching "§ 3 Abs." references in body text.
_HDR_NO_DASH = re.compile(
    r"^§\s*(\d+[a-z]*)\s+(?!Abs\.|Absatz\s|Satz\s|Sätze\s|Nr\.\s)([A-ZÄÖÜ][^\n(]{3,100})$",
)
_HDR_FREI = re.compile(r"^§\s*(\d+[a-z]*)\s+\((frei)\)\s*$", re.IGNORECASE)

# LBO_SL has two edge-case header formats that _HDR_NO_DASH misses:
# 1) "§ 13 2130-1 13 Standsicherheit" — legislative ref number before title
# 2) "§ 14 Title Body text..."        — body text inline after the title
# This regex strips the legislative ref and this pre-processor normalises both.
_LBO_SL_LEG_REF = re.compile(
    r"^(§\s*\d+[a-z]*\s+)\d{4}-\d+\s+\d+\s+",
    re.MULTILINE,
)
_PAGE_MARKER_PREFIX_RE = re.compile(
    r"^\s*-?\s*Seite\s+\d+\s+von\s+\d+\s*-?\s*",
    re.IGNORECASE,
)
# synoptic (HBauO): § N Title § N Title  – take first title
_HDR_SYNOPTIC = re.compile(
    r"^§\s*(\d+[a-z]*)\s+([\w][^\n§]{3,100?}?)\s+§\s*\d+[a-z]*\b",
    re.IGNORECASE,
)
# standalone synoptic header when titles differ: § N OldTitle  (line ends there)
# Same as no_dash but used as fallback for synoptic mode
_HDR_SYNOPTIC_SINGLE = _HDR_NO_DASH

# Patterns in a § N Title line that indicate a ToC or page-break header (not real)
_TITLE_NOISE_RE = re.compile(
    r"\.{2,}"              # dot leaders (ToC)
    r"|\bFassung\s+vom\b"  # page-break stamp
    r"|\bSeite\s+\d+\b"    # page number
    r"|\bSächsBO\b"        # law name in page-break line
    r"|\bHBauO\b"          # same for HBauO
    r"|\bLBO\b(?:\s+SL)?"  # same for LBO
)

_TITLE_STRIP_PATTERNS = (
    re.compile(r"^\s*Seite\s+\d+\s+von\s+\d+\s+", re.IGNORECASE),
    re.compile(r"\b2130-\d+\s+\d+\b"),
    re.compile(r"\s+\d{1,2}\.\d{1,2}(?:\.\d{1,4})?$"),
    re.compile(r"\s+1\s+2\b.*$"),
    re.compile(
        r"\b(?:Erster|Erste|Zweiter|Dritter|Vierter|F(?:uenf|ünf)ter|Sechster|Siebenter|Achter|Neunter|Zehnter)\s+"
        r"(?:Teil|Abschnitt)\b.*$",
        re.IGNORECASE,
    ),
    re.compile(r"\bTeil\s+\d+\b.*$", re.IGNORECASE),
    re.compile(r"\bAbschnitt\s+(?:[IVXLC]+|\d+)\b.*$", re.IGNORECASE),
    re.compile(r"\b(?:©\s*20\d{2}\s+)?(?:Wolters|Kluwer)\b.*$", re.IGNORECASE),
    re.compile(r"\bgespeichert:\s*\d{2}\.\d{2}\.\d{4},\s*\d{2}:\d{2}\s*Uhr.*$", re.IGNORECASE),
    re.compile(r"\bFassung\s+vom\b.*$", re.IGNORECASE),
)
_INLINE_BODY_HINT_RE = re.compile(
    r"\b(?:ist|sind|war|waren|wird|werden|wurde|wurden|"
    r"muss|müssen|darf|dürfen|kann|können|gilt|gelten|"
    r"hat|haben|erlischt|erlöschen|führt|führen|bedarf|bedürfen)\b",
    re.IGNORECASE,
)
_HEADER_STAMP_RE = re.compile(
    r"^(?:Fassung\s+vom\b.*|Stand:.*|Titel\s+Gültig\s+ab\b.*|Nichtamtliche\s+Lesefassung\b.*|SächsBO\b.*)$",
    re.IGNORECASE,
)


def _is_noise_title(title: str) -> bool:
    """Return True if the title contains markers that indicate a ToC or page-break line."""
    return bool(_TITLE_NOISE_RE.search(title))


def _clean_section_title(title: str) -> str:
    """Strip obvious extraction/page noise from a section title candidate."""
    cleaned = " ".join(title.split())
    for pattern in _TITLE_STRIP_PATTERNS:
        cleaned = pattern.sub("", cleaned).strip()
    cleaned = re.sub(r"\s+", " ", cleaned).strip(" .;,:-")
    return cleaned


def _clean_body_text(text: str) -> str:
    """Strip source-text artifacts from body text and drop heading-only bleed."""
    cleaned = " ".join(text.split())
    cleaned = _strip_known_text_artifacts(cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    cleaned = _strip_trailing_heading_text(cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip(" .;,:-")
    if cleaned and _is_pure_heading_text(cleaned):
        return ""
    return cleaned


def _looks_like_inline_body_fragment(text: str) -> bool:
    """Heuristic: tell apart inline body text from a genuine section title."""
    cleaned = _clean_body_text(text)
    if not cleaned:
        return False
    if re.match(r"^(?:\(?\d+\)|\d)", cleaned):
        return True
    return bool(_INLINE_BODY_HINT_RE.search(cleaned))


def _pick_best_title(candidates: list[str]) -> str:
    """Choose the cleanest section title candidate from txt/flat duplicates."""
    cleaned_candidates = [
        cleaned for cleaned in (_clean_section_title(candidate) for candidate in candidates) if cleaned
    ]
    if not cleaned_candidates:
        return ""
    if len(cleaned_candidates) >= 2:
        common = _clean_section_title(os.path.commonprefix(cleaned_candidates))
        if common:
            cleaned_candidates.append(common)

    def score(title: str) -> tuple[int, int]:
        penalty = 0
        if _looks_like_inline_body_fragment(title):
            penalty += 6
        if re.search(r"\b(?:Teil|Abschnitt)\b", title, re.IGNORECASE):
            penalty += 4
        if re.search(r"\bAnlage\b", title, re.IGNORECASE):
            penalty += 4
        if re.search(r"\b\d+\b", title):
            penalty += 3
        if title.endswith("-"):
            penalty += 2
        if len(title) < 6:
            penalty += 2
        return (penalty, -len(title))

    return min(cleaned_candidates, key=score)


def _trim_to_occurrence(txt: str, marker: str, occurrence: int) -> str:
    """Drop everything before the Nth occurrence of a marker string."""
    if occurrence <= 1:
        return txt
    start = 0
    found = -1
    for _ in range(occurrence):
        found = txt.find(marker, start)
        if found == -1:
            return txt
        start = found + len(marker)
    return txt[found:]


def _trim_bauo_he_text(txt: str) -> str:
    """Keep the actual Hessen law body and drop the appendix after §93."""
    txt = _trim_to_second_section_one_line(txt)
    kept_lines: list[str] = []
    for line in txt.splitlines():
        if line.startswith("§ 93 Inkrafttreten"):
            kept_lines.append(re.sub(r"\s+Anlage\s*$", "", line).rstrip())
            break
        kept_lines.append(line)
    return "\n".join(kept_lines)


def _trim_hbauo_text(txt: str) -> str:
    """Keep the official HBauO law body and drop the annex after §87."""
    positions: list[int] = []
    offset = 0
    for line in txt.splitlines(keepends=True):
        if re.match(r"^§\s*1\b", line.strip()):
            positions.append(offset)
        offset += len(line)
    if len(positions) >= 3:
        txt = txt[positions[2]:]
    kept_lines: list[str] = []
    for line in txt.splitlines():
        if re.match(r"^Anlage\b", line.strip(), re.IGNORECASE):
            break
        kept_lines.append(line)
    return "\n".join(kept_lines)


def _trim_to_second_section_one_line(txt: str) -> str:
    """Drop repeated ToC text before the second line-start `§ 1 ...` block."""
    positions: list[int] = []
    offset = 0
    for line in txt.splitlines(keepends=True):
        if re.match(r"^§\s*1\b", line.strip()):
            positions.append(offset)
        offset += len(line)
    if len(positions) >= 2:
        return txt[positions[1]:]
    return txt


def _make_header_matcher(header_type: str):
    """Return a function(line) -> (sec_num, title) | None."""
    if header_type == "dash_date":
        def match(line: str):
            m = _HDR_DASH_DATE.match(line.strip())
            return (m.group(1).lower(), m.group(2).strip()) if m else None
    elif header_type == "no_dash":
        def match(line: str):
            mf = _HDR_FREI.match(line.strip())
            if mf:
                return (mf.group(1).lower(), f"({mf.group(2).lower()})")
            m = _HDR_NO_DASH.match(line.strip())
            if not m:
                return None
            title = m.group(2).strip().rstrip(".")
            if _is_noise_title(title):
                return None
            return (m.group(1).lower(), title)
    elif header_type == "synoptic":
        def match(line: str):
            m = _HDR_SYNOPTIC.match(line.strip())
            if m:
                title = m.group(2).strip()
                if not _is_noise_title(title):
                    return (m.group(1).lower(), title)
            # Fallback: plain § N Title line (single-column section)
            m2 = _HDR_SYNOPTIC_SINGLE.match(line.strip())
            if m2:
                title = m2.group(2).strip().rstrip(".")
                if not _is_noise_title(title):
                    return (m2.group(1).lower(), title)
            return None
    elif header_type == "from_flat":
        # Never match from txt — handled by generate_from_flat()
        def match(line: str):  # noqa: ARG001
            return None
    else:
        raise ValueError(f"Unknown header_type: {header_type!r}")
    return match


def _load_flat_inventory(flat_path: Path) -> tuple[dict[str, str], dict[str, str]]:
    """
    Parse flat-table inventory to get:
      type_map:  sec_num -> node_type   (from row ID prefix)
      title_map: sec_num -> title       (best-effort from § column)
    """
    type_map: dict[str, str] = {}
    title_map: dict[str, str] = {}
    _SEC_IN_COL = re.compile(r"§\s*(\d+[a-z]*)\s+([A-ZÄÖÜ][^\|]{3,})", re.IGNORECASE)

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
        if not node_type or node_type.lower() in {"node type", "typ", "knotentyp", "type"}:
            continue

        # Section number from row ID: "6.1" -> "6", "3a.2" -> "3a"
        m = re.match(r"^(\d+[a-z]*)\.", row_id)
        if not m:
            continue
        sec = m.group(1).lower()

        if sec not in type_map:
            type_map[sec] = node_type.strip()

        if sec not in title_map:
            mt = _SEC_IN_COL.search(sec_col)
            if mt and len(mt.group(2).strip()) > 3:
                # Strip trailing noise (dates, "geändert durch", etc.)
                raw = mt.group(2).strip()
                raw = re.sub(r"\s+(?:geändert|bis|ab|zuletzt)\b.*$", "", raw, flags=re.IGNORECASE)
                raw = re.sub(r"\s+\d{2}\.\d{2}\.\d{4}.*$", "", raw).strip()
                raw = _clean_section_title(raw)
                if raw and not _is_noise_title(raw):
                    title_map[sec] = raw

    return type_map, title_map


def _load_sectioned_inventory_sections(
    path: Path,
) -> list[tuple[str, str, str, list[tuple[str, str]]]]:
    """
    Parse a sectioned markdown inventory with 2-column rule tables.

    This supports inventories such as BW_LBO and BremLBO that already have
    `### § N — Title` headings and `| Nr. | Regeltext |` tables, but are not
    in the older 5-column flat-table format.
    """
    sections: list[tuple[str, str, str, list[tuple[str, str]]]] = []
    current_sec = ""
    current_title = ""
    current_type = ""
    current_rows: list[tuple[str, str]] = []

    def flush() -> None:
        if current_sec and current_rows:
            sections.append((current_sec, current_title, current_type, list(current_rows)))

    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        m = re.match(r"^###\s+§\s*(\d+[a-z]*)\s*[—\-]\s*(.+)", stripped, re.IGNORECASE)
        if m:
            flush()
            current_sec = m.group(1).lower()
            current_title = _clean_section_title(m.group(2).strip())
            current_type = ""
            current_rows = []
            continue
        if not current_sec:
            continue
        if stripped.startswith("**type:**"):
            current_type = stripped.split("**type:**", 1)[1].strip()
            continue
        if not stripped.startswith("|"):
            continue
        cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        if len(cells) < 2:
            continue
        first = cells[0]
        if first.lower() in {"nr.", "nr"} or set(first) == {"-"}:
            continue
        if not re.match(r"^\d+[a-z]?(?:\.\d+)+$", first, re.IGNORECASE):
            continue
        cleaned_text = _clean_body_text(cells[1])
        if cleaned_text:
            current_rows.append((first, cleaned_text))

    flush()
    return sections


def _dedupe_synoptic_line(line: str) -> str:
    """
    For HBauO synoptic lines where body text is doubled:
      '(1) text_old (1) text_new'  →  '(1) text_old'
    """
    m = _ABSATZ_RE.match(line)
    if not m:
        return line
    num = re.escape(m.group(1))
    # Remove everything from the second `(N)` onwards
    deduped = re.sub(rf"\s+\({num}\)\s+.*$", "", line.rstrip())
    return deduped


def _preprocess_no_dash(txt: str, title_map: dict[str, str]) -> str:
    """Normalise edge-case header lines in no_dash texts (e.g. LBO_SL).

    Handles two patterns the main regex misses:
    1) Legislative ref before title: "§ 13 2130-1 13 Standsicherheit"
       → "§ 13 Standsicherheit"
    2) Body text inline after title: "§ 14 Title Body ..."
       → "§ 14 Title\\nBody ..."
    """
    # Step 1: strip legislative reference numbers
    txt = _LBO_SL_LEG_REF.sub(r"\1", txt)

    # Step 1b: merge bare "§ N" lines with a title that spilled onto the next
    # line, optionally after a page-marker prefix.
    merged_lines = []
    lines = txt.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        if re.match(r"^§\s*\d+[a-z]*\s*$", line.strip()):
            title_line = ""
            if i + 1 < len(lines):
                title_line = _PAGE_MARKER_PREFIX_RE.sub("", lines[i + 1].strip()).strip()
            if title_line and not title_line.startswith("§") and not _ABSATZ_RE.match(title_line):
                merged_lines.append(f"{line.strip()} {title_line}".strip())
                i += 2
                continue
        merged_lines.append(line)
        i += 1
    txt = "\n".join(merged_lines)

    # Build an enriched title map: start by collecting clean titles found via
    # the header regex (e.g. from the ToC), then fill gaps from title_map.
    # Regex-matched titles are preferred because flat-inventory titles can be
    # truncated or wrong (e.g. LBO_SL §65).
    enriched: dict[str, str] = {}
    for line in txt.splitlines():
        m = _HDR_NO_DASH.match(line.strip())
        if m and not _is_noise_title(m.group(2).strip()):
            sec = m.group(1).lower()
            title = _clean_section_title(m.group(2).strip().rstrip("."))
            if not title:
                continue
            enriched[sec] = _pick_best_title([enriched.get(sec, ""), title])
    # Fill gaps from flat inventory title_map
    if title_map:
        for sec, title in title_map.items():
            cleaned = _clean_section_title(title)
            if cleaned:
                enriched[sec] = _pick_best_title([enriched.get(sec, ""), cleaned])

    # Step 2: split lines where body text follows a known title
    if not enriched:
        return txt
    out_lines = []
    for line in txt.splitlines():
        m = re.match(r"^§\s*(\d+[a-z]*)\s+", line)
        if m:
            sec = m.group(1).lower()
            title = enriched.get(sec)
            if title:
                # Try exact title match
                idx = line.find(title)
                if idx >= 0:
                    end = idx + len(title)
                    rest = line[end:].strip()
                    if rest and not rest.startswith("§") and not re.fullmatch(r"\d+(?:\s+\d+)*", rest):
                        out_lines.append(line[:end])
                        if not (_HEADER_STAMP_RE.match(rest) or _is_pure_heading_text(rest)):
                            out_lines.append(rest)
                        continue
            # Fallback: title may differ between ToC and body.  Try to find
            # the split point where a new sentence begins by looking for
            # Absatz markers or articles/verbs after the title section.
            fb = re.search(
                r"([a-zäöü)n]\s+)"
                r"((?:\(\d+\)\s+)?"          # optional Absatz marker
                r"(?:Die|Der|Das|Ein|Bei|Mit|Auf|Sind|Soweit|Bauliche|Jede|Anlagen|Verfahrensfrei|Keiner)\s)",
                line[len(m.group(0)):],
            )
            if fb:
                split_pos = len(m.group(0)) + fb.start() + len(fb.group(1))
                header = line[:split_pos].rstrip()
                body = line[split_pos:].strip()
                if body:
                    out_lines.append(header)
                    if not (_HEADER_STAMP_RE.match(body) or _is_pure_heading_text(body)):
                        out_lines.append(body)
                    continue
        out_lines.append(line)
    return "\n".join(out_lines)


def _parse_sections(
    txt: str,
    header_type: str,
    title_map: dict[str, str],
) -> list[tuple[str, str, str]]:
    """Split txt into (sec_num, title, body_text) triples."""
    if header_type == "no_dash":
        txt = _preprocess_no_dash(txt, title_map)
    match_header = _make_header_matcher(header_type)
    lines = txt.splitlines()

    sections: list[tuple[str, str, str]] = []
    current_num = ""
    current_title = ""
    body_lines: list[str] = []

    for line in lines:
        result = match_header(line)
        if result:
            sec_num, raw_title = result
            # Save previous section
            if current_num:
                sections.append((current_num, current_title, "\n".join(body_lines).strip()))
            current_num = sec_num
            # Prefer clean title from flat inventory; fall back to txt
            current_title = _pick_best_title([title_map.get(sec_num, ""), raw_title]) or _clean_section_title(raw_title)
            body_lines = []
        elif current_num:
            clean = _dedupe_synoptic_line(line) if header_type == "synoptic" else line
            clean = _clean_body_text(clean)
            if clean:
                body_lines.append(clean)

    if current_num:
        sections.append((current_num, current_title, "\n".join(body_lines).strip()))

    # Deduplicate: for repeated section numbers (e.g. ToC + body), keep the
    # occurrence with the most body content (the real body section wins).
    best: dict[str, tuple[str, str, str]] = {}
    for item in sections:
        num = item[0]
        if num not in best or len(item[2]) > len(best[num][2]):
            best[num] = item
    sections = [best[k] for k in sorted(best, key=lambda n: sections.index(best[n]))]

    return sections


def _split_absaetze(body: str) -> list[tuple[str, str]]:
    """Split section body into (absatz_num, text) pairs."""
    lines = body.splitlines()
    absaetze: list[tuple[str, str]] = []
    current_n = ""
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

    absaetze = [(n, t) for n, t in absaetze if t.strip()]
    return absaetze or [("", body.strip())]


def _format_row_id(sec: str, abs_n: str, idx: int) -> str:
    sec_norm = sec.lower()
    num = abs_n if abs_n else str(idx + 1)
    return f"{sec_norm}.{num}"


def _generate_from_flat(
    state: str,
    cfg: dict,
    flat_path: Path,
    out_path: Path,
) -> None:
    """Generate v2 from flat inventory only (no txt parsing). Used for HBauO."""
    source_suffix = cfg["source_suffix"]
    law_short = state.replace("_", " ")

    type_map, title_map = _load_flat_inventory(flat_path)

    # Read all rows preserving order
    rows: list[tuple[str, str, str, str]] = []  # (row_id, sec_num, node_type, text)
    for line in flat_path.read_text(encoding="utf-8").splitlines():
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 5:
            continue
        row_id, node_type, text = cells[0], (cells[3] if len(cells) > 3 else ""), (cells[4] if len(cells) > 4 else "")
        if row_id.lower() in {"row id", "nr", "nr.", "#"}:
            continue
        if not node_type or node_type.lower() in {"node type", "typ", "knotentyp", "type"}:
            continue
        m = re.match(r"^(\d+[a-z]*)\.", row_id)
        if not m:
            continue
        cleaned_text = _clean_body_text(text.strip())
        if not cleaned_text:
            continue
        rows.append((row_id, m.group(1).lower(), node_type.strip(), cleaned_text))

    if not rows:
        sectioned_sections = _load_sectioned_inventory_sections(flat_path)
        if sectioned_sections:
            lines_out = [
                f"# {law_short} — Node Inventory (Paragraph Level)",
                "",
                f"_Generated by generate_lbo_inventory.py from {state}_node_inventory.md (sectioned)._",
                f"_Types sourced from existing {state}_node_inventory.md._",
                "_Run split_inventory_to_sentences.py to produce the fine (sentence-level) version._",
                "",
            ]
            for sec_num, title, node_type, sec_rows in sectioned_sections:
                lines_out.append(f"### § {sec_num} — {title}")
                lines_out.append(f"**type:** {node_type or 'allgemeine_anforderung'}")
                lines_out.append(f"**source_paragraph:** §{sec_num} {source_suffix}")
                lines_out.append("")
                lines_out.append(f"| Nr. | Regeltext ({law_short}-Wortlaut) |")
                lines_out.append("|---|---|")
                for row_id, text in sec_rows:
                    lines_out.append(f"| {row_id} | {text.replace('|', chr(92) + '|')} |")
                lines_out.append("")

            out_path.write_text("\n".join(lines_out), encoding="utf-8")
            print(f"   Written  : {out_path}  ({len(sectioned_sections)} sections, from sectioned inventory)")
            return

    # Group rows by section
    from collections import OrderedDict
    sections_rows: OrderedDict[str, list[tuple[str, str, str]]] = OrderedDict()
    for row_id, sec_num, node_type, text in rows:
        if sec_num not in sections_rows:
            sections_rows[sec_num] = []
        sections_rows[sec_num].append((row_id, node_type, text))

    lines_out = [
        f"# {law_short} — Node Inventory (Paragraph Level)",
        "",
        f"_Generated by generate_lbo_inventory.py from {state}_node_inventory.md (flat)._",
        f"_Types sourced from existing flat {state}_node_inventory.md._",
        "_Run split_inventory_to_sentences.py to produce the fine (sentence-level) version._",
        "",
    ]

    for sec_num, sec_rows in sections_rows.items():
        node_type = sec_rows[0][1]
        title = title_map.get(sec_num, f"§ {sec_num}")
        lines_out.append(f"### § {sec_num} — {title}")
        lines_out.append(f"**type:** {node_type}")
        lines_out.append(f"**source_paragraph:** §{sec_num} {source_suffix}")
        lines_out.append("")
        lines_out.append(f"| Nr. | Regeltext ({law_short}-Wortlaut) |")
        lines_out.append("|---|---|")
        for row_id, _, text in sec_rows:
            lines_out.append(f"| {row_id} | {text.replace('|', chr(92) + '|')} |")
        lines_out.append("")

    out_path.write_text("\n".join(lines_out), encoding="utf-8")
    print(f"   Written  : {out_path}  ({len(sections_rows)} sections, from flat)")


def generate(state: str) -> None:
    """Run the full generation for a single state."""
    cfg = _STATE_CONFIGS[state]
    flat_path = _INVENTORY_DIR / f"{state}_node_inventory.md"
    out_path = _INVENTORY_DIR / f"{state}_node_inventory_v2.md"
    header_type = cfg["header_type"]
    source_suffix = cfg["source_suffix"]

    print(f"\n── {state} ({'–'.join([cfg['jurisdiction']])})")    

    if header_type == "from_flat":
        print("   Mode     : from_flat (txt too noisy)")
        print(f"   Flat inv : {flat_path}")
        _generate_from_flat(state, cfg, flat_path, out_path)
        return

    txt_path = _TXT_DIR / f"{state}.txt"
    print(f"   Reading  : {txt_path}")
    txt = txt_path.read_text(encoding="utf-8", errors="replace")
    if state == "BauO_HE":
        txt = _trim_bauo_he_text(txt)
    elif state == "HBauO":
        txt = _trim_hbauo_text(txt)
    elif state in {"BauO_BE", "BauO_LSA", "BauO_MV", "LBO_SH", "LBauO_RLP", "ThuerBO"}:
        txt = _trim_to_second_section_one_line(txt)
    elif state == "SaechsBO":
        txt = _trim_to_second_section_one_line(txt)

    print(f"   Flat inv : {flat_path}")
    type_map, title_map = _load_flat_inventory(flat_path)
    print(f"   Types: {len(type_map)}, titles from flat: {len(title_map)}")

    sections = _parse_sections(txt, header_type, title_map)
    print(f"   Sections found: {len(sections)}")

    law_short = state.replace("_", " ")
    lines_out = [
        f"# {law_short} — Node Inventory (Paragraph Level)",
        "",
        f"_Generated by generate_lbo_inventory.py from {state}.txt._",
        f"_Types sourced from existing flat {state}_node_inventory.md._",
        "_Run split_inventory_to_sentences.py to produce the fine (sentence-level) version._",
        "",
    ]

    unknown_types: list[str] = []
    for sec_num, title, body in sections:
        node_type = type_map.get(sec_num, "")
        if not node_type:
            node_type = "allgemeine_anforderung"
            unknown_types.append(sec_num)

        lines_out.append(f"### § {sec_num} — {title}")
        lines_out.append(f"**type:** {node_type}")
        lines_out.append(f"**source_paragraph:** §{sec_num} {source_suffix}")
        lines_out.append("")
        lines_out.append(f"| Nr. | Regeltext ({law_short}-Wortlaut) |")
        lines_out.append("|---|---|")

        absaetze = _split_absaetze(body)
        for idx, (abs_n, text) in enumerate(absaetze):
            text = _clean_body_text(text)
            if not text:
                continue
            row_id = _format_row_id(sec_num, abs_n, idx)
            text_clean = text.replace("|", "\\|")
            lines_out.append(f"| {row_id} | {text_clean} |")

        lines_out.append("")

    out_path.write_text("\n".join(lines_out), encoding="utf-8")
    print(f"   Written  : {out_path}  ({len(sections)} sections)")

    if unknown_types:
        print(
            f"   WARN: {len(unknown_types)} sections defaulted to allgemeine_anforderung:"
            f" {unknown_types[:15]}"
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate LBO v2 node inventories.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--state", choices=list(_STATE_CONFIGS), help="Single state to process.")
    group.add_argument("--all", action="store_true", help="Process all configured states.")
    args = parser.parse_args()

    states = list(_STATE_CONFIGS) if args.all else [args.state]
    for state in states:
        generate(state)

    print("\nDone.")


if __name__ == "__main__":
    main()
