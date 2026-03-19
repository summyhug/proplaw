#!/usr/bin/env python3
"""Inventory cleanup helper (Pattern C).

Pattern C: a sentence is split across consecutive nodes because the PDF
           page-break occurred mid-sentence inside a legal cross-reference.
           The split point is always a dangling abbreviation at the END of
           a node's text:

               Abs.  →  needs the following paragraph/item number
               Nr.   →  needs the following item number

Example BEFORE:
  | 6.1 | …, soweit nicht gemäß § 9 Abs. |
  | 6.2 | 2 des Baugesetzbuchs oder … |

Example AFTER (merged, 6.2 deleted, paragraph renumbered if needed):
  | 6.1 | …, soweit nicht gemäß § 9 Abs. 2 des Baugesetzbuchs oder … |

Chains of three or more are handled iteratively until the combined text
no longer ends with a continuation marker.

Only nodes within the SAME paragraph (same first part of X.Y) are merged.
"""

import argparse
import re
from collections import defaultdict
from pathlib import Path

ROW_RE = re.compile(r'^\| (\d+)\.(\d+) \| (.*?) \|$')

# A node whose text ends with one of these abbreviations is an
# incomplete sentence that must be joined to the next node.
CONT_END_RE = re.compile(r'\bAbs\.\s*$|\bNr\.\s*$')


def process_table_block(
    rows: list[tuple[int, int, str]],
) -> tuple[list[tuple[int, int, str]], int]:
    """Merge Pattern-C sentence-continuation nodes within each paragraph.

    rows: list of (para_num, item_num, text) — all data rows from one table.
    Returns (new_rows, n_merges_performed).
    """
    # Group by paragraph
    groups: dict[int, list[str]] = defaultdict(list)
    para_order: list[int] = []
    for para, _item, text in rows:
        if para not in groups:
            para_order.append(para)
        groups[para].append(text)

    result_rows: list[tuple[int, int, str]] = []
    total_merges = 0

    for para in para_order:
        texts = groups[para]
        merged: list[str] = []

        i = 0
        while i < len(texts):
            current = texts[i]
            # Absorb following fragments as long as current ends with Abs./Nr.
            while CONT_END_RE.search(current) and i + 1 < len(texts):
                i += 1
                current = current + ' ' + texts[i]
                total_merges += 1
            merged.append(current)
            i += 1

        for idx, text in enumerate(merged, start=1):
            result_rows.append((para, idx, text))

    return result_rows, total_merges


def process(content: str) -> tuple[str, int]:
    """Return (cleaned_content, total_merges_performed)."""
    lines = content.split('\n')
    out: list[str] = []
    total_merges = 0

    i = 0
    while i < len(lines):
        line = lines[i]

        # Detect a table header or separator that opens a data block
        if re.match(r'^\|---\|---\|', line.strip()) or re.match(
            r'^\| Nr\. \|', line.strip()
        ):
            out.append(line)
            i += 1

            # Collect all immediately following data rows
            table_rows: list[tuple[int, int, str, str]] = []
            while i < len(lines):
                row_line = lines[i]
                m = ROW_RE.match(row_line.strip())
                if m:
                    table_rows.append(
                        (int(m.group(1)), int(m.group(2)), m.group(3).strip(), row_line)
                    )
                    i += 1
                else:
                    break

            if not table_rows:
                continue

            # Check whether any merges are needed
            pre_check = sum(
                1
                for _, _, txt, _ in table_rows
                if CONT_END_RE.search(txt)
            )

            if pre_check == 0:
                # Nothing to merge — emit original lines
                for *_, orig_line in table_rows:
                    out.append(orig_line)
            else:
                # Apply merges and renumber
                triples = [(p, it, txt) for p, it, txt, _ in table_rows]
                processed, n = process_table_block(triples)
                total_merges += n
                for para, item, text in processed:
                    out.append(f'| {para}.{item} | {text} |')

            continue  # don't advance i; outer loop handles lines[i]

        out.append(line)
        i += 1

    return '\n'.join(out), total_merges


def main() -> None:
    default_input = Path(__file__).parent / "BbgBO_node_inventory_fine.md"

    parser = argparse.ArgumentParser(
        description="Merge Pattern-C sentence-continuation nodes in a fine inventory markdown table."
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

    original_rows = sum(1 for line in content.split('\n') if ROW_RE.match(line.strip()))
    cleaned, n_merges = process(content)
    cleaned_rows = sum(1 for line in cleaned.split('\n') if ROW_RE.match(line.strip()))

    output_path.write_text(cleaned, encoding='utf-8')

    print(f"Processed: {input_path.name}")
    if output_path != input_path:
        print(f"  Output  : {output_path}")
    print(f'  Pattern-C merges performed : {n_merges}')
    print(f'  Data rows before           : {original_rows}')
    print(f'  Data rows after            : {cleaned_rows}')
    print(f'  Net rows removed           : {original_rows - cleaned_rows}')


if __name__ == '__main__':
    main()
