"""
Extracts and cleans text from LBO/MBO PDF files.

pdfminer fragments long sentences across short lines. This script rejoins them
into proper paragraphs, then saves a clean .txt file ready for manual review
and conversion to node inventory format.

Usage:
    python propra/data/extract_pdf.py propra/data/raw/MBO.pdf
"""

import re
import sys
from pathlib import Path

from pdfminer.high_level import extract_text


def clean(pdf_path: str) -> str:
    raw = extract_text(pdf_path)

    lines = raw.splitlines()
    cleaned = []

    for line in lines:
        # Normalise whitespace within the line
        line = re.sub(r"[ \t]+", " ", line).strip()
        if not line:
            cleaned.append("")
            continue
        cleaned.append(line)

    # Rejoin fragmented sentences.
    # A line is a continuation if it does NOT start with:
    #   - A paragraph marker: § / (1) / 1. / - / a)
    #   - A section heading (all caps or title-cased short line)
    #   - Empty line
    rejoined = []
    buffer = ""

    def is_new_block(line: str) -> bool:
        if not line:
            return True
        if re.match(r"^§\s*\d+", line):
            return True
        if re.match(r"^\(\d+\)", line):
            return True
        if re.match(r"^\d+[a-z]?\.", line):
            return True
        if re.match(r"^[a-z]\)", line):
            return True
        if re.match(r"^-\s", line):
            return True
        # Short all-caps title line
        if line.isupper() and len(line) < 60:
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
            # continuation — join with space, fixing hyphenation
            if buffer.endswith("-"):
                buffer = buffer[:-1] + line
            else:
                buffer = buffer + " " + line

    if buffer:
        rejoined.append(buffer)

    return "\n".join(rejoined)


if __name__ == "__main__":
    pdf = sys.argv[1] if len(sys.argv) > 1 else "propra/data/raw/MBO.pdf"
    out = Path(pdf).with_suffix(".txt")
    text = clean(pdf)
    out.write_text(text, encoding="utf-8")
    lines = [l for l in text.splitlines() if l.strip()]
    print(f"Extracted {len(lines)} lines → {out}")
    print("\n=== PREVIEW (§6 Abstandsflächen) ===")
    in_sec = False
    for l in text.splitlines():
        if re.match(r"^§\s*6\s*$", l.strip()):
            in_sec = True
        if in_sec:
            print(l)
        if in_sec and re.match(r"^§\s*7\s*$", l.strip()):
            break
