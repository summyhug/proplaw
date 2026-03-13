"""
extract_pdf_clean.py
====================
Drop-in replacement for extract_pdf.py.

Extracts clean, RAG-ready plain text from German LBO/MBO PDF files.

Fixes over the original extract_pdf.py:
  - Uses pdfplumber instead of pdfminer (better line reconstruction)
  - Strips web-archive noise: URLs, timestamps, page numbers embedded in text
  - Fixes superscript artefacts: "75 m 2" -> "75 m2", "50 m 3" -> "50 m3"
  - Rejoins hyphenated line breaks correctly
  - Preserves paragraph structure (§, Absatz markers, numbered items)
  - Windows cp1252 safe: all output written as UTF-8 explicitly

Usage:
    python extract_pdf_clean.py <input.pdf> [output.txt]

    If output path is omitted, writes to <input>.txt (same folder).

Output format (suitable for FAISS chunking and KG inventory):
    - One Absatz per logical block, blank line separated
    - § headers on their own line
    - Numbered items (1., 2., a), b)) on their own line
    - No URLs, no timestamps, no page numbers
"""

import re
import sys
from pathlib import Path

import pdfplumber

sys.stdout.reconfigure(encoding="utf-8")

# ---------------------------------------------------------------------------
# Noise patterns to strip (web-archive artefacts baked into PDF text layer)
# ---------------------------------------------------------------------------
NOISE_PATTERNS = [
    # Full archive URL lines
    re.compile(r'https?://\S+'),
    # Web portal timestamp headers: "11.03.26, 18:52 Archiv: ..." or "11.03.26, 19:02 Transparenzportal ..."
    re.compile(r'\d{2}\.\d{2}\.\d{2},\s+\d{2}:\d{2}[^\n]*'),
    # Page number footers: "6/52", "1/52" etc.
    re.compile(r'^\s*\d{1,3}/\d{1,3}\s*$', re.MULTILINE),
    # Garbage Unicode private-use characters (Bremen PDF artefacts: \ueddb, \ueddc etc.)
    re.compile(r'[\uE000-\uF8FF]+'),
]

# Superscript artefacts: pdfplumber sometimes extracts "m 2" or "m 3"
# as separate tokens on the same line. Normalise to "m2" / "m3".
SUPERSCRIPT_FIX = re.compile(r'\bm\s([23])\b')

# Lone single-digit lines that are superscript page artefacts
# Only match digits that appear between lines that do NOT end in "m"
# (i.e. pure page number artefacts, not m2/m3 split across lines)
# We handle the m2/m3 case in the rejoiner instead.
LONE_DIGIT = re.compile(r'^\s*\d\s*$')


# ---------------------------------------------------------------------------
# Block boundary detection (same logic as original, extended)
# ---------------------------------------------------------------------------
def is_new_block(line: str) -> bool:
    """Return True if this line starts a new logical block."""
    if not line:
        return True
    # § paragraph header
    if re.match(r'^§\s*\d+', line):
        return True
    # Absatz marker: (1), (2) ...
    if re.match(r'^\(\d+\)', line):
        return True
    # Numbered item: 1., 2., 10.
    if re.match(r'^\d+[a-z]?\.', line):
        return True
    # Letter sub-item: a), b), aa)
    if re.match(r'^[a-z]{1,2}\)', line):
        return True
    # Dash list item
    if re.match(r'^-\s', line):
        return True
    # Section/part headings: "Teil 1", "Abschnitt 2"
    if re.match(r'^(Teil|Abschnitt)\s+\d+', line, re.IGNORECASE):
        return True
    # Short ALL-CAPS title line (section heading)
    if line.isupper() and len(line.split()) <= 6:
        return True
    return False


# ---------------------------------------------------------------------------
# Core extraction
# ---------------------------------------------------------------------------
def extract(pdf_path: str) -> str:
    raw_pages = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text(x_tolerance=2, y_tolerance=3)
            if text:
                raw_pages.append(text)

    raw = "\n".join(raw_pages)

    # --- Strip noise ---
    for pattern in NOISE_PATTERNS:
        raw = pattern.sub("", raw)

    # --- Fix superscripts ---
    raw = SUPERSCRIPT_FIX.sub(r'm\1', raw)

    # Normalise missing space between § number and title: "§ 1Anwendungsbereich" -> "§ 1 Anwendungsbereich"
    raw = re.sub(r'(§\s*\d+[a-z]?)([A-ZÜÖÄ])', r'\1 \2', raw)

    # Post-pass: catch "m Grundfläche" / "m Behälterinhalt" etc. where
    # superscript digit was on a separate line and got dropped
    # These are always m2 in LBO context (area measurements)
    raw = re.sub(r'\bm\s+(Grundfläche|Ansichtsfläche|Dachfläche|Grundriss)', r'm2 \1', raw)
    # m3 contexts (volume)
    raw = re.sub(r'\bm\s+(umbautem\s+Raum|Behälterinhalt|Beckeninhalt)', r'm3 \1', raw)

    # --- Split into lines, normalise whitespace ---
    lines = []
    prev = ""
    for line in raw.splitlines():
        line = re.sub(r'[ \t]+', ' ', line).strip()
        # Lone digit: could be page artefact OR superscript after "m"
        if LONE_DIGIT.match(line):
            if prev.rstrip().endswith('m') or prev.rstrip().endswith('M'):
                # It's a superscript — append directly to previous line
                lines[-1] = lines[-1] + line.strip()
            # else: pure page artefact — drop silently
            continue
        lines.append(line)
        prev = line

    # --- Rejoin continuation lines into logical blocks ---
    rejoined = []
    buffer = ""

    for line in lines:
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
            # Continuation line
            if buffer.endswith("-"):
                # Hyphenated word break — join without space
                buffer = buffer[:-1] + line
            else:
                buffer = buffer + " " + line

    if buffer:
        rejoined.append(buffer)

    # --- Collapse excessive blank lines ---
    text = "\n".join(rejoined)
    text = re.sub(r'\n{3,}', '\n\n', text)

    return text.strip()


# ---------------------------------------------------------------------------
# Per-file processing + stats
# ---------------------------------------------------------------------------
def process_one(pdf_path: str, out_path: str) -> dict:
    """Extract one PDF, write .txt, return stats dict."""
    text = extract(pdf_path)
    Path(out_path).write_text(text, encoding="utf-8")

    lines    = [line for line in text.splitlines() if line.strip()]
    paras    = len(re.findall(r'^§\s*\d+', text, re.MULTILINE))
    absaetze = len(re.findall(r'^\(\d+\)', text, re.MULTILINE))
    trunc    = text.count('…')
    noise_u  = len(re.findall(r'https?://', text))
    noise_t  = len(re.findall(r'\d{2}\.\d{2}\.\d{2},\s+\d{2}:\d{2}', text))

    warnings = (
        ([f"{trunc} truncation(s)"]  if trunc   > 0 else []) +
        ([f"{noise_u} URL(s)"]       if noise_u > 0 else []) +
        ([f"{noise_t} timestamp(s)"] if noise_t > 0 else [])
    )

    return {
        "pdf":        pdf_path,
        "out":        out_path,
        "lines":      len(lines),
        "paragraphs": paras,
        "absaetze":   absaetze,
        "truncations": trunc,
        "noise":      noise_u + noise_t,
        "warnings":   warnings,
    }


# ---------------------------------------------------------------------------
# Main — single file OR bulk directory
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description=(
            "Extract clean RAG-ready .txt from German LBO/MBO PDFs.\n"
            "Pass a single PDF or a directory to process all PDFs in bulk."
        )
    )
    parser.add_argument(
        "input",
        help="Path to a single .pdf file OR a directory containing PDF files.",
    )
    parser.add_argument(
        "--out-dir", "-o",
        default=None,
        help="Output directory for .txt files (default: same folder as each PDF).",
    )
    parser.add_argument(
        "--pattern", "-p",
        default="*.pdf",
        help="Glob pattern when input is a directory (default: *.pdf).",
    )
    args = parser.parse_args()

    input_path = Path(args.input)

    # --- Collect PDFs ---
    if input_path.is_dir():
        pdfs = sorted(input_path.glob(args.pattern))
        if not pdfs:
            print(f"No PDFs matched '{args.pattern}' in {input_path}")
            sys.exit(1)
    elif input_path.is_file():
        pdfs = [input_path]
    else:
        print(f"Input not found: {input_path}")
        sys.exit(1)

    # --- Output directory ---
    if args.out_dir:
        out_dir = Path(args.out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
    else:
        out_dir = None  # same folder as each PDF

    # --- Process ---
    print(f"Processing {len(pdfs)} PDF(s)...\n")
    print(f"{'File':<36} {'§§':>4} {'Abs':>5} {'Lines':>6} {'Trunc':>6} {'Noise':>6}  Status")
    print("-" * 82)

    results  = []
    errors   = []

    for pdf in pdfs:
        out_path = (out_dir or pdf.parent) / pdf.with_suffix(".txt").name
        try:
            r      = process_one(str(pdf), str(out_path))
            status = ("WARN: " + " | ".join(r["warnings"])) if r["warnings"] else "OK"
            print(
                f"{pdf.name:<36} {r['paragraphs']:>4} {r['absaetze']:>5} "
                f"{r['lines']:>6} {r['truncations']:>6} {r['noise']:>6}  {status}"
            )
            results.append(r)
        except Exception as exc:
            print(f"{pdf.name:<36} {'':>4} {'':>5} {'':>6} {'':>6} {'':>6}  ERROR: {exc}")
            errors.append((str(pdf), str(exc)))

    # --- Summary ---
    total     = len(results)
    clean     = sum(1 for r in results if not r["warnings"])
    with_warn = total - clean

    print()
    print(f"Done.  {total} extracted  |  {clean} clean  |  {with_warn} warnings  |  {len(errors)} errors")

    if errors:
        print("\nErrors:")
        for path, msg in errors:
            print(f"  {path}: {msg}")

    if with_warn:
        print("\nFiles with warnings need manual inspection (PDF source quality issue).")

    if total == 1:
        print(f"\nOutput: {results[0]['out']}")
