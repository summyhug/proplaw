#!/usr/bin/env python3
"""Cleanup helper for fine LBO inventories.

Removes "Bearbeitungsstand" watermarks from a fine node inventory (sentence/list-item
level markdown table), including:
  1. Watermark at end of node text  -> strip suffix
  2. Watermark mid-sentence         -> remove and reconnect text
  3. Node text is only watermark    -> delete entire row

Also strips watermarks from ### section header lines.

This script is intentionally conservative: it only touches lines that contain
the watermark patterns and the corresponding table rows.
"""

import argparse
import re
from pathlib import Path

# Matches an optional preceding letter (handles "mit86 Bearbeitungsstand:")
_WM_CONCAT = re.compile(
    r'([a-zA-ZäöüÄÖÜßa-z])\d{1,3}'
    r'\s+Bearbeitungsstand:\s+\d{2}\.\d{2}\.\d{4}\s+\d+:\d{2}\s+Uhr\.?\s*'
)
# Matches the normal case (space before page number)
_WM_NORMAL = re.compile(
    r'\s*\d{1,3}\s+Bearbeitungsstand:\s+\d{2}\.\d{2}\.\d{4}\s+\d+:\d{2}\s+Uhr\.?\s*'
)
# Matches a table data row
_ROW = re.compile(r'^\|\s*(\d+\.\d+)\s*\|\s*(.*?)\s*\|$')


def strip_watermark(text: str) -> str:
    """Remove all Bearbeitungsstand watermarks from text."""
    # Step 1: handle digits concatenated to previous word (e.g. "mit86 Bearbeitungsstand:")
    text = _WM_CONCAT.sub(r'\1', text)
    # Step 2: handle normal separated case (e.g. " 86 Bearbeitungsstand:")
    text = _WM_NORMAL.sub(' ', text)
    # Step 3: collapse any resulting double-spaces
    text = re.sub(r'  +', ' ', text)
    return text.strip()


def process(content: str) -> str:
    lines = content.split('\n')
    out = []

    for line in lines:
        # ── Section headers ────────────────────────────────────────────────
        if line.startswith('### ') and 'Bearbeitungsstand' in line:
            out.append(strip_watermark(line))
            continue

        # ── Table data rows ────────────────────────────────────────────────
        m = _ROW.match(line.strip())
        if m and 'Bearbeitungsstand' in line:
            nr = m.group(1)
            text = m.group(2).strip()
            cleaned = strip_watermark(text)
            if not cleaned:
                # Pure watermark node — delete it entirely
                continue
            out.append(f'| {nr} | {cleaned} |')
            continue

        # ── Everything else unchanged ──────────────────────────────────────
        out.append(line)

    return '\n'.join(out)


def main() -> None:
    default_input = Path(__file__).parent / "BbgBO_node_inventory_fine.md"

    parser = argparse.ArgumentParser(
        description="Remove Bearbeitungsstand watermarks from a fine node inventory."
    )
    parser.add_argument(
        "--input",
        type=str,
        default=str(default_input),
        help="Path to the input fine inventory markdown.",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="",
        help="Path to write the cleaned inventory. Defaults to --input (in-place).",
    )
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output) if args.output else input_path

    if not input_path.exists():
        raise SystemExit(f"Input file not found: {input_path}")

    content = input_path.read_text(encoding='utf-8')
    original_rows = sum(1 for line in content.split('\n') if _ROW.match(line.strip()))
    original_wm   = content.count('Bearbeitungsstand')

    cleaned = process(content)

    cleaned_rows = sum(1 for line in cleaned.split('\n') if _ROW.match(line.strip()))
    remaining_wm = cleaned.count('Bearbeitungsstand')

    output_path.write_text(cleaned, encoding='utf-8')

    print(f"Cleaned: {input_path.name}")
    if output_path != input_path:
        print(f"  Output  : {output_path}")
    print(f"  Data rows before : {original_rows}")
    print(f"  Data rows after  : {cleaned_rows}")
    print(f"  Rows deleted     : {original_rows - cleaned_rows}")
    print(f"  Watermarks before: {original_wm}")
    print(f"  Watermarks after : {remaining_wm}")


if __name__ == '__main__':
    main()
