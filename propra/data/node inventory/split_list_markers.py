#!/usr/bin/env python3
"""Inventory cleanup helper (Pattern A).

Pattern A:  "intro clause 1. list item content"  is one node.
Fix:        split into "intro clause" | "1. list item content"
            and renumber all subsequent nodes in the same paragraph.

A "1." is treated as a LIST MARKER only when it is NOT:
  - preceded by a legal reference word (Absatz, Satz, Nummer, Buchstabe, §)
  - followed by a German month name (date: "1. Januar")
  - at the very start of the text (already a list-item node)
"""

import argparse
import re
from pathlib import Path

# ── constants ──────────────────────────────────────────────────────────────────
ROW_RE = re.compile(r'^\| (\d+)\.(\d+) \| (.*?) \|$')

REF_WORDS = {'Absatz', 'Satz', 'Nummer', 'Buchstabe', 'Teil',
             'Abschnitt', 'Artikel', 'Ziffer'}

DE_MONTHS = {
    'Januar', 'Februar', 'März', 'April', 'Mai', 'Juni',
    'Juli', 'August', 'September', 'Oktober', 'November', 'Dezember',
}


# ── helpers ────────────────────────────────────────────────────────────────────
def find_list_1_split(text: str) -> int | None:
    """
    Return the position of the space before ' 1. ' that is a genuine list
    marker, or None if no such marker exists.
    """
    # Already a list-item node (starts with a number + period)
    if re.match(r'^\d+\.\s', text):
        return None

    for m in re.finditer(r' 1\. ', text):
        pos = m.start()            # position of the space before '1'
        end = m.end()              # position of the char after the trailing space

        # Word right before the space at pos
        prefix_words = text[:pos].split()
        last_word = prefix_words[-1].rstrip('.,;:()') if prefix_words else ''

        # Skip: legal reference word directly precedes
        if last_word in REF_WORDS:
            continue

        # Skip: '§' anywhere in the 6 chars before the match
        if '§' in text[max(0, pos - 6): pos]:
            continue

        # Skip: followed by a German month name (it's a date)
        rest = text[end:]
        first_rest = (rest.split()[0] if rest.split() else '').rstrip('.,;:')
        if first_rest in DE_MONTHS:
            continue

        return pos

    return None


# ── table-block processor ──────────────────────────────────────────────────────
def process_table_block(rows: list[tuple[int, int, str]]) -> list[tuple[int, int, str]]:
    """
    rows: [(para_num, item_num, text), ...]
    Returns a new list with Pattern-A splits applied and items renumbered.
    """
    # Group rows by paragraph number (first part of X.Y)
    from collections import defaultdict
    groups: dict[int, list[tuple[int, str]]] = defaultdict(list)
    para_order: list[int] = []

    for para, item, text in rows:
        if para not in groups:
            para_order.append(para)
        groups[para].append((item, text))

    # Process each paragraph group independently
    result_rows: list[tuple[int, int, str]] = []

    for para in para_order:
        items = groups[para]  # list of (item_num, text) in original order
        new_items: list[str] = []  # just the texts, in final order

        for _orig_item, text in items:
            split_pos = find_list_1_split(text)
            if split_pos is not None:
                intro   = text[:split_pos].rstrip()
                content = text[split_pos + 1:]     # starts with "1. ..."
                new_items.append(intro)
                new_items.append(content)
            else:
                new_items.append(text)

        # Re-number sequentially 1, 2, 3, ...
        for idx, text in enumerate(new_items, start=1):
            result_rows.append((para, idx, text))

    return result_rows


# ── main processing ────────────────────────────────────────────────────────────
def process(content: str) -> tuple[str, int]:
    """Return (cleaned_content, number_of_splits_performed)."""
    lines = content.split('\n')
    out: list[str] = []

    i = 0
    total_splits = 0

    while i < len(lines):
        line = lines[i]

        # Detect start of a table block (the header row "| Nr. | Regeltext ...")
        if re.match(r'^\|---\|---\|', line.strip()) or (
            re.match(r'^\| Nr\. \|', line.strip())
        ):
            # Emit this line unchanged
            out.append(line)
            i += 1

            # Collect all subsequent data rows
            table_rows: list[tuple[int, int, str, str]] = []  # (para, item, text, orig_line)
            while i < len(lines):
                row_line = lines[i]
                m = ROW_RE.match(row_line.strip())
                if m:
                    table_rows.append((int(m.group(1)), int(m.group(2)), m.group(3).strip(), row_line))
                    i += 1
                else:
                    break  # non-row line → end of table

            if not table_rows:
                continue

            # Count splits that will happen
            splits_here = sum(
                1 for _, _, text, _ in table_rows
                if find_list_1_split(text) is not None
            )
            total_splits += splits_here

            if splits_here == 0:
                # No changes — emit original lines
                for *_, orig_line in table_rows:
                    out.append(orig_line)
            else:
                # Process and renumber
                input_triples = [(p, it, txt) for p, it, txt, _ in table_rows]
                processed = process_table_block(input_triples)
                for para, item, text in processed:
                    out.append(f'| {para}.{item} | {text} |')

            # Don't advance i — the outer loop will handle lines[i]
            continue

        out.append(line)
        i += 1

    return '\n'.join(out), total_splits


def main() -> None:
    default_input = Path(__file__).parent / "BbgBO_node_inventory_fine.md"

    parser = argparse.ArgumentParser(
        description="Split over-merged inline list markers (' 1. ... 2. ...') in a fine inventory markdown table."
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

    cleaned, n_splits = process(content)

    cleaned_rows = sum(1 for line in cleaned.split('\n') if ROW_RE.match(line.strip()))

    output_path.write_text(cleaned, encoding='utf-8')

    print(f"Processed: {input_path.name}")
    if output_path != input_path:
        print(f"  Output  : {output_path}")
    print(f"  Pattern-A splits performed : {n_splits}")
    print(f"  Data rows before           : {original_rows}")
    print(f"  Data rows after            : {cleaned_rows}")
    print(f"  Net new rows added         : {cleaned_rows - original_rows}")


if __name__ == '__main__':
    main()
