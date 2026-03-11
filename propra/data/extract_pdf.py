"""
Extracts and cleans text from LBO/MBO PDF files using pdfplumber.

Produces a clean .txt file ready for draft_inventory.py.
Handles both § (most LBOs) and Art. (BayBO) numbering formats.

Layout strategies used per PDF type:
- Standard single-column (LBauO_RLP, BayBO, LBO_HB, BauO_NRW, MBO): default extraction.
- Comparison-table (HBauO): left 48% crop to discard the 'HBauO neu' column.
- Two-column body (e.g. truly two-column PDFs): layout=True or column crop — add
  detection logic in the pdfplumber loop below following the HBauO pattern.

Usage:
    python propra/data/extract_pdf.py propra/data/raw/LBauO_RLP.pdf
    python propra/data/extract_pdf.py propra/data/raw/BayBO.pdf
    python propra/data/extract_pdf.py propra/data/raw/MBO.pdf
"""

import re
import sys
from pathlib import Path

import pdfplumber

sys.stdout.reconfigure(encoding="utf-8")


# ─── Noise line patterns ──────────────────────────────────────────────────────

_NOISE_PATTERNS = [
    re.compile(r"^\d{2}\.\d{2}\.\d{4}$"),                          # bare dates: 01.10.2001
    re.compile(r"^\d{2}\.\d{2}\.\d{2},\s+\d{2}:\d{2}"),           # LBO_HB: "11.03.26, 19:02 …" browser header
    re.compile(r"^-\s*Seite\s+\d+\s+von\s+\d+\s*-$", re.I),       # page markers
    re.compile(r"^Seite\s+\d+$", re.I),                             # "Seite 3"
    re.compile(r"^\d+$"),                                            # bare page numbers
    re.compile(r"^www\.", re.I),                                     # URLs
    re.compile(r"^https?://", re.I),                                 # URLs
    re.compile(r"^[\ue000-\uf8ff]+$"),                               # Unicode PUA chars (web artefacts)
    re.compile(r"^(Amtliche Abkürzung|Ausfertigungsdatum|"
               r"Textnachweis ab|Dokumenttyp|Quelle|Fundstelle|"
               r"Gliederungs-Nr|Stand:|letzte berücksichtigte|"
               r"Vollzitat|BayRS|Nichtamtliches Inhaltsverzeichnis)",
               re.I),
    # NRW: standalone amendment-footnote lines ─────────────────────────────
    # "§ 2: geändert…" — colon after provision number always marks a footnote ref
    re.compile(r"^§\s*\d+[a-zA-Z]?\s*:", re.I),
    # Fragment lines that result when pdfplumber splits "in Kraft getreten am…"
    # across two PDF text-boxes ("getreten" → "ge" + "treten" on next line)
    re.compile(r"^(?:in\s+Kraft\s+)?(?:ge)?treten\s+am\s+\d", re.I),
    re.compile(r"^ten\s+am\s+\d", re.I),             # tail of "getret-en am"
    # NRW law-gazette reference fragments: "1172)," on its own line
    re.compile(r"^\d{3,}\),?\s*$"),
    re.compile(r"^Fußnoten\s+zu\s+§", re.I),
    re.compile(r"^Herausgeber:", re.I),
    # HBauO: comparison-table column headers ────────────────────────────────
    re.compile(r"^Gesamtsynopse\s+HBauO", re.I),
    re.compile(r"^(?:Nichtamtliche\s+Lesefassung|HBauO\s+aktuell|HBauO\s+neu\s*\()", re.I),
    # MBO / LBO: structural part and section ordinal headers ─────────────────
    # "Erster Teil", "Zweiter Abschnitt", etc. — purely organisational, not
    # legal content; the subtitle on the following line is handled separately.
    re.compile(
        r"^(?:Erster|Zweiter|Dritter|Vierter|Fünfter|Sechster|Siebente?r|"
        r"Achter|Neunter|Zehnter|Elfter|Zwölfter)\s+"
        r"(?:Teil|Abschnitt|Unterabschnitt|Kapitel)\b",
        re.I,
    ),
]

# Matches the ordinal line so we can drop the subtitle on the next line too
_SECTION_ORDINAL = re.compile(
    r"^(?:Erster|Zweiter|Dritter|Vierter|Fünfter|Sechster|Siebente?r|"
    r"Achter|Neunter|Zehnter|Elfter|Zwölfter)\s+"
    r"(?:Teil|Abschnitt|Unterabschnitt|Kapitel)\b",
    re.I,
)

# Provision start — § 6, §6a, Art. 6, Artikel 6
_PROVISION = re.compile(
    r"^(§\s*\d+[a-zA-Z]?|Art(?:ikel)?\.\s*\d+[a-zA-Z]?)\b"
)

# Absatz marker: (1), (2) etc.
_ABSATZ = re.compile(r"^\(\d+\)")


def _is_noise(line: str) -> bool:
    for pattern in _NOISE_PATTERNS:
        if pattern.match(line):
            return True
    return False


def extract(pdf_path: str) -> str:
    """
    Extract and clean text from an LBO PDF using pdfplumber.
    Returns cleaned text as a single string.

    Special handling:
    - HBauO: comparison-table PDFs are cropped to left 45% to drop the
      duplicate 'HBauO neu' column.
    - BauO_NRW: inline amendment footnotes are stripped from provision lines.
    - LBO_HB (Bremen): provision numbers glued to titles are normalised.
    """
    pages_text = []

    with pdfplumber.open(pdf_path) as pdf:
        # Detect HBauO comparison-table layout from first page text
        first_text = pdf.pages[0].extract_text(x_tolerance=2, y_tolerance=3) or ""
        is_comparison_table = bool(
            re.search(r"Gesamtsynopse\s+HBauO|HBauO\s+aktuell", first_text, re.I)
        )

        for page in pdf.pages:
            if is_comparison_table:
                # Crop to leftmost 48% to exclude the 'HBauO neu' right column
                # (45% truncated word endings; 48% is wide enough for full words)
                x1 = page.width * 0.48
                cropped = page.crop((0, 0, x1, page.height))
                text = cropped.extract_text(x_tolerance=2, y_tolerance=3)
            else:
                text = page.extract_text(x_tolerance=2, y_tolerance=3)
            if text:
                pages_text.append(text)

    raw = "\n".join(pages_text)

    # Step 1: normalise whitespace per line, drop noise
    lines = raw.splitlines()
    cleaned = []
    _drop_next_subtitle = False   # True after an ordinal header is dropped
    for line in lines:
        line = re.sub(r"[ \t]+", " ", line).strip()

        # Normalise Bremen-style glued provision numbers: "§ 1Titel" → "§ 1 Titel"
        # Must run BEFORE sentence-number stripping so § 1 is not destroyed.
        line = re.sub(
            r"^((?:§\s*|Art(?:ikel)?\.\s*)\d+[a-zA-Z]?)([A-ZÄÖÜ])",
            r"\1 \2",
            line,
        )

        # Strip BayBO/HBauO-style inline sentence numbers: pdfplumber renders
        # superscript "¹²³…" as plain digits glued to the next word, e.g.
        # "1Dieses", "2Es", "2Höhe", "4Anlagen".
        # Case 1: inline — after sentence-end ". " or after Absatz marker ") "
        line = re.sub(r"(?<=\. )\d+(?=[A-ZÄÖÜ])", "", line)
        line = re.sub(r"(?<=\) )\d+(?=[A-ZÄÖÜ])", "", line)
        # Case 2: line starts with a bare sentence-number digit, e.g. "2Es gilt".
        # Guard: list items are "1. " or "a) " — the digit here is immediately
        # followed by an uppercase letter (no period/paren after), so it's safe
        # to strip.  The provision-number normalisation above already inserted a
        # space in "§ 1Title", so § numbers are protected.
        line = re.sub(r"^\d(?=[A-ZÄÖÜ])", "", line)

        # Strip NRW inline amendment footnotes that pdfplumber merges onto
        # the same line as the provision heading, e.g.:
        #   "§ 2 Begriffe Absatz 3 geändert durch Gesetz vom 31. Oktober 2021"
        #   "§ 1 Anwendungsbereich in Kraft getreten am 1. Januar 2024"
        line = re.sub(
            r"\s+(?:Abs(?:atz)?\.?\s+\d+\w*\s+)?(?:geändert|eingefügt|aufgehoben|neu\s+gefasst)\s+durch\s+Gesetz\b.*$",
            "",
            line,
            flags=re.I,
        )
        line = re.sub(
            r"\s+(?:in\s+Kraft\s+)?(?:ge)?treten\s+am\s+\d.*$",
            "",
            line,
            flags=re.I,
        )
        line = re.sub(r"\s+Fußnoten\s+zu\s+§.*$", "", line, flags=re.I)
        line = re.sub(r"\s+Herausgeber:.*$", "", line, flags=re.I)
        # NRW publisher address bleeds into body text when pdfplumber merges
        # text boxes: "…dienen, falen, Friedrichstr. 62-80, 40217 Düsseldorf 7 / 123"
        # Match from any word that precedes ", Friedrichstr." (including standalone line)
        line = re.sub(r",?\s*\w+,\s+Friedrichstr\..*$", "", line)

        if not line:
            _drop_next_subtitle = False
            cleaned.append("")
            continue
        if _is_noise(line):
            # If this was an ordinal header, flag the next content line as subtitle
            if _SECTION_ORDINAL.match(line):
                _drop_next_subtitle = True
            continue
        # Drop the section subtitle that immediately follows an ordinal header
        # (e.g. "Das Grundstück und seine Bebauung" after "Zweiter Teil"),
        # unless it is a provision or Absatz line.
        if _drop_next_subtitle:
            _drop_next_subtitle = False
            if not _PROVISION.match(line) and not _ABSATZ.match(line):
                continue
        cleaned.append(line)

    # Step 1b: collapse duplicate adjacent provision headers (HBauO comparison table)
    # When the 45% crop still clips a repeated header from the right column,
    # two identical "§ N Title" lines appear back-to-back; keep only the first.
    deduped = []
    for line in cleaned:
        if (
            deduped
            and line
            and _PROVISION.match(line)
            and deduped[-1] == line
        ):
            continue
        deduped.append(line)
    cleaned = deduped

    # Step 2: drop TOC block
    # Find first provision that is followed by a real Absatz (1) within 6 lines,
    # with no other provision line intervening (TOC entries are densely packed —
    # e.g. "§ 92 … § 93 … § 1 … (1)" would incorrectly match § 92 with the old
    # logic; requiring zero intervening provisions skips straight to real body §).
    content_start = 0
    for i, line in enumerate(cleaned):
        if _PROVISION.match(line):
            lookahead = cleaned[i + 1:i + 7]
            absatz_pos = next(
                (j for j, l in enumerate(lookahead) if _ABSATZ.match(l)), None
            )
            if absatz_pos is not None:
                lines_before_absatz = lookahead[:absatz_pos]
                if not any(_PROVISION.match(l) for l in lines_before_absatz):
                    content_start = i
                    break

    cleaned = cleaned[content_start:]

    # Step 3: rejoin fragmented lines
    rejoined = []
    buffer = ""

    def is_new_block(line: str) -> bool:
        if not line:
            return True
        if _PROVISION.match(line):
            return True
        if _ABSATZ.match(line):
            return True
        if re.match(r"^\d+[a-z]?\.\s\S", line):
            return True
        if re.match(r"^[a-z]\)\s\S", line):
            return True
        if re.match(r"^-\s\S", line):
            return True
        if line.isupper() and len(line) < 80:
            return True
        return False

    for line in cleaned:
        if not line:
            if buffer:
                rejoined.append(buffer)
                buffer = ""
            rejoined.append("")
        elif is_new_block(line):
            if buffer:
                rejoined.append(buffer)
            buffer = line
        else:
            if buffer.endswith("-"):
                buffer = buffer[:-1] + line
            else:
                buffer = buffer + " " + line

    if buffer:
        rejoined.append(buffer)

    # Step 4: collapse multiple blank lines
    final = []
    prev_blank = False
    for line in rejoined:
        if not line.strip():
            if not prev_blank:
                final.append("")
            prev_blank = True
        else:
            final.append(line)
            prev_blank = False

    return "\n".join(final)


if __name__ == "__main__":
    pdf = sys.argv[1] if len(sys.argv) > 1 else "propra/data/raw/MBO.pdf"
    out = Path(pdf).with_suffix(".txt")
    text = extract(pdf)
    out.write_text(text, encoding="utf-8")
    non_empty = [l for l in text.splitlines() if l.strip()]
    print(f"Extracted {len(non_empty)} lines -> {out}")

    # Preview: first 3 provisions
    print("\n=== PREVIEW (first 3 provisions) ===")
    count = 0
    lines_shown = 0
    for line in text.splitlines():
        if _PROVISION.match(line):
            count += 1
            lines_shown = 0
            print()
        if count > 0:
            print(line)
            lines_shown += 1
        if count >= 3 and lines_shown > 8:
            break