#!/usr/bin/env python3
"""Inventory cleanup helper (Pattern B).

Pattern B: a data row whose text ends with a dangling list marker " N."
where the actual list-item content was pushed into the next row.

Example BEFORE:
  | 2.1 | ...bebauten Grundstücke sind 1. |
  | 2.2 | wasseraufnahmefähig zu belassen oder herzustellen und 2. |
  | 2.3 | zu begrünen oder zu bepflanzen, ... |

Example AFTER:
  | 2.1 | ...bebauten Grundstücke sind |
  | 2.2 | 1. wasseraufnahmefähig zu belassen oder herzustellen und |
  | 2.3 | 2. zu begrünen oder zu bepflanzen, ... |

No node-ID renumbering is needed (we only move markers, not add/remove rows).

A trailing " N." is treated as a LIST MARKER only when it is NOT:
  - preceded by a legal reference word (Absatz, Satz, Nummer, Buchstabe, §)
  - followed by a German month name in the next row (it's a split date)
"""

import argparse
import re
from pathlib import Path

ROW_RE = re.compile(r'^\| (\d+\.\d+) \| (.*?) \|$')
END_MARKER_RE = re.compile(r' (\d+)\.$')

REF_WORDS = {'Absatz', 'Satz', 'Nummer', 'Buchstabe', 'Teil',
             'Abschnitt', 'Artikel', 'Ziffer'}
DE_MONTHS = {
    'Januar', 'Februar', 'März', 'April', 'Mai', 'Juni',
    'Juli', 'August', 'September', 'Oktober', 'November', 'Dezember',
}


def is_genuine_end_marker(text: str, next_text: str) -> re.Match | None:
    """
    If text ends with a genuine list marker ' N.', return the match object.
    Otherwise return None.
    """
    m = END_MARKER_RE.search(text)
    if not m:
        return None

    # Word immediately before ' N.'
    pre = text[:m.start()]
    last_word = (pre.split()[-1] if pre.split() else '').rstrip('.,;:()')

    # Skip: preceded by a reference word (e.g. "Absatz 3.", "Satz 2.")
    if last_word in REF_WORDS:
        return None

    # Skip: preceded by "§" nearby (e.g. "§ 1.", "gemäß § 3.")
    if '§' in text[max(0, m.start() - 6): m.start()]:
        return None

    # Skip: part of a numerical range "X und N." or "X bis N."
    # e.g. "Gebäudeklassen 1 und 2." or "Absätze 1 und 2." or "1 bis 3."
    pre_words = pre.split()
    if len(pre_words) >= 2:
        second_last = pre_words[-2].rstrip('.,;:()')
        if last_word in ('und', 'bis') and second_last.rstrip('.').isdigit():
            return None

    # Skip: next row starts with a German month name (split date: "1. Oktober")
    first_next = (next_text.split()[0] if next_text.split() else '').rstrip('.,;:')
    if first_next in DE_MONTHS:
        return None

    return m


def process(content: str) -> tuple[str, int]:
    """Return (cleaned_content, number_of_fixes_applied)."""
    lines = content.split('\n')
    n_fixes = 0

    # Build list of (line_index, node_id, text) for all data rows
    data_rows: list[tuple[int, str, str]] = []
    for idx, line in enumerate(lines):
        m = ROW_RE.match(line.strip())
        if m:
            data_rows.append((idx, m.group(1), m.group(2).strip()))

    # Process consecutive pairs
    pending_prefix: dict[int, str] = {}  # line_index → prefix to prepend

    for i in range(len(data_rows) - 1):
        li, nr, text = data_rows[i]
        # Apply any already-scheduled prefix (from a prior iteration)
        had_pending = li in pending_prefix
        if had_pending:
            text = pending_prefix[li] + text
            del pending_prefix[li]

        next_li, next_nr, next_text = data_rows[i + 1]
        # Apply pending prefix to next text (for lookahead month check)
        effective_next = pending_prefix.get(next_li, '') + next_text

        m = is_genuine_end_marker(text, effective_next)
        if m is None:
            # If we prepended a prefix but no further marker, write back now
            if had_pending:
                lines[li] = f'| {nr} | {text} |'
            continue

        marker_n = m.group(1)

        # Strip ' N.' from current text
        new_text = text[:m.start()].rstrip()

        # Prepend 'N. ' to next row
        prefix = f'{marker_n}. '

        # Schedule the update
        if next_li not in pending_prefix:
            pending_prefix[next_li] = prefix
        # (If already scheduled, the pending prefix was already prepended in
        #  `effective_next` above, so don't double-add.)

        # Write back current row
        lines[li] = f'| {nr} | {new_text} |'
        n_fixes += 1

    # Apply any remaining pending prefixes (last row in chain)
    for li_idx, prefix in pending_prefix.items():
        m_row = ROW_RE.match(lines[li_idx].strip())
        if m_row:
            new_t = prefix + m_row.group(2).strip()
            lines[li_idx] = f'| {m_row.group(1)} | {new_t} |'

    return '\n'.join(lines), n_fixes


def main() -> None:
    default_input = Path(__file__).parent / "BbgBO_node_inventory_fine.md"

    parser = argparse.ArgumentParser(
        description="Fix dangling list markers ('N.') in a fine node inventory markdown table."
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
    cleaned, n_fixes = process(content)
    output_path.write_text(cleaned, encoding='utf-8')

    print(f"Processed: {input_path.name}")
    if output_path != input_path:
        print(f"  Output  : {output_path}")
    print(f"  Pattern-B fixes applied: {n_fixes}")

if __name__ == '__main__':
    main()
