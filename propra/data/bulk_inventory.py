"""
bulk_inventory.py
=================
Generates node inventory .md files from clean LBO/MBO .txt files.

Uses a generic TYPE_MAP derived from MBO § structure. Applies to all
16 LBOs + MBO. Unknown §§ (state-specific additions) are flagged with
type UNKNOWN for manual review.

Usage:
    # Single file
    python bulk_inventory.py txt/BauO_BE.txt --out-dir node_inventory/

    # Entire folder
    python bulk_inventory.py txt/ --out-dir node_inventory/

Output:
    One .md file per .txt input, e.g. BauO_BE_node_inventory.md
    Summary table printed to stdout after each run.
"""

import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

# ---------------------------------------------------------------------------
# Generic TYPE_MAP — MBO § structure as baseline
# All 16 LBOs share this core. State-specific §§ fall through to UNKNOWN.
# ---------------------------------------------------------------------------
TYPE_MAP = {
    "1":   "anwendungsbereich",
    "2":   "begriffsbestimmung",
    "3":   "allgemeine_anforderung",
    "3a":   "allgemeine_anforderung",
    "4":   "grundstuecksbebauung",
    "5":   "verkehrssicherheit",
    "6":   "abstandsflaeche",
    "6a":   "abstandsflaeche_sonderfall",
    "7":   "grundstuecksteilung",
    "8":   "freiflaechengestaltung",
    "9":   "gestaltungsanforderung",
    "10":   "gestaltungsanforderung",
    "11":   "baustellenanforderung",
    "12":   "standsicherheit",
    "12a":   "allgemeine_anforderung",
    "12b":   "allgemeine_anforderung",
    "12c":   "allgemeine_anforderung",
    "13":   "schutzanforderung",
    "14":   "brandschutzanforderung",
    "15":   "schutzanforderung",
    "16":   "verkehrssicherheit",
    "16a":   "bauproduktzulassung",
    "16b":   "bauproduktzulassung",
    "16c":   "bauproduktzulassung",
    "17":   "bauproduktzulassung",
    "17a":   "bauproduktzulassung",
    "17b":   "bauproduktzulassung",
    "17c":   "bauproduktzulassung",
    "18":   "bauproduktzulassung",
    "18a":   "bauproduktzulassung",
    "18b":   "bauproduktzulassung",
    "19":   "bauproduktzulassung",
    "19a":   "bauproduktzulassung",
    "19b":   "bauproduktzulassung",
    "19c":   "bauproduktzulassung",
    "20":   "bauproduktzulassung",
    "20a":   "bauproduktzulassung",
    "20b":   "bauproduktzulassung",
    "20c":   "bauproduktzulassung",
    "21":   "bauproduktzulassung",
    "21a":   "abstandsflaeche",
    "22":   "bauproduktzulassung",
    "22a":   "bauproduktzulassung",
    "22b":   "bauproduktzulassung",
    "23":   "bauproduktzulassung",
    "23a":   "bauproduktzulassung",
    "24":   "bauproduktzulassung",
    "25":   "bauproduktzulassung",
    "26":   "brandklassifizierung",
    "27":   "tragende_wand",
    "28":   "aussenwand",
    "29":   "trennwand",
    "30":   "brandwand",
    "31":   "decke",
    "32":   "dach",
    "32a":   "allgemeine_anforderung",
    "33":   "bestandsaenderung",
    "34":   "treppe",
    "35":   "treppenraum",
    "36":   "notwendiger_flur",
    "37":   "fensteroffnung",
    "38":   "allgemeine_anforderung",
    "39":   "aufzugsanlage",
    "40":   "technische_anlage",
    "41":   "technische_anlage",
    "42":   "technische_anlage",
    "42a":   "technische_anlage",
    "43":   "sanitaerraum",
    "43a":   "technische_anlage",
    "44":   "technische_anlage",
    "45":   "technische_anlage",
    "46":   "technische_anlage",
    "46a":   "technische_anlage",
    "47":   "aufenthaltsraum",
    "48":   "wohnung",
    "49":   "stellplatzpflicht",
    "50":   "barrierefreiheit",
    "51":   "sonderbautyp",
    "52":   "beteiligtenpflicht",
    "53":   "beteiligtenpflicht",
    "54":   "beteiligtenpflicht",
    "55":   "verfahrensfreies_vorhaben",
    "56":   "beteiligtenpflicht",
    "56a":   "beteiligtenpflicht",
    "57":   "behoerdenstruktur",
    "58":   "behoerdenstruktur",
    "58a":   "bestandsschutz",
    "59":   "genehmigungspflicht",
    "60":   "genehmigungspflicht",
    "61":   "verfahrensfreies_vorhaben",
    "62":   "kenntnisgabeverfahren",
    "63":   "vereinfachtes_genehmigungsverfahren",
    "63a":   "vereinfachtes_genehmigungsverfahren",
    "64":   "genehmigungspflicht",
    "64a":   "besonderes_verfahren",
    "64b":   "beteiligtenpflicht",
    "64c":   "beteiligtenpflicht",
    "64d":   "beteiligtenpflicht",
    "64e":   "beteiligtenpflicht",
    "65":   "beteiligtenpflicht",
    "65a":   "beteiligtenpflicht",
    "65b":   "beteiligtenpflicht",
    "65c":   "beteiligtenpflicht",
    "65d":   "beteiligtenpflicht",
    "66":   "bauantrag",
    "67":   "abweichung",
    "68":   "bauantrag",
    "69":   "baugenehmigung",
    "70":   "nachbarbenachrichtigung",
    "70a":   "baugenehmigung",
    "71":   "baugenehmigung",
    "71a":   "typengenehmigung",
    "72":   "baugenehmigung",
    "72a":   "typengenehmigung",
    "73":   "baugenehmigung",
    "73a":   "typengenehmigung",
    "74":   "baugenehmigung",
    "74a":   "bestandsaenderung",
    "74b":   "bauproduktzulassung",
    "75":   "bauvorbescheid",
    "75a":   "typengenehmigung",
    "76":   "besonderes_verfahren",
    "76a":   "typengenehmigung",
    "77":   "besonderes_verfahren",
    "77a":   "typengenehmigung",
    "78":   "bauproduktzulassung",
    "79":   "bauueberwachung",
    "80":   "sanktion",
    "80a":   "bestandsschutz",
    "81":   "bauueberwachung",
    "81a":   "technische_baubestimmungen",
    "82":   "baubeginn",
    "83":   "sicherheitsleistung",
    "83a":   "bestandsaenderung",
    "83b":   "bestandsaenderung",
    "83c":   "bestandsaenderung",
    "84":   "sanktion",
    "84a":   "behoerdenstruktur",
    "84b":   "behoerdenstruktur",
    "84c":   "behoerdenstruktur",
    "85":   "ermaechtigungsgrundlage",
    "85a":   "technische_baubestimmungen",
    "85b":   "allgemeine_anforderung",
    "86":   "oertliche_bauvorschrift",
    "86a":   "ermaechtigungsgrundlage",
    "87":   "schlussvorschrift",
    "87a":   "technische_baubestimmungen",
    "88":   "schlussvorschrift",
    "88a":   "technische_baubestimmungen",
    "89":   "schlussvorschrift",
    "90":   "schlussvorschrift",
    "91":   "schlussvorschrift",
    "91a":   "behoerdenstruktur",
    "92":   "schlussvorschrift",
    "92a":   "behoerdenstruktur",
    "93":   "schlussvorschrift",
    "94":   "schlussvorschrift",
    "95":   "schlussvorschrift",
    "96":   "schlussvorschrift",
    "97":   "oertliche_bauvorschrift",
    "98":   "bestandsschutz",
    "99":   "ermaechtigungsgrundlage",
    "100":   "schlussvorschrift",
    "101":   "schlussvorschrift",
    "102":   "schlussvorschrift",
    "44a":   "allgemeine_anforderung",
    "61a":   "bauantrag",
    "61b":   "bauantrag",
    "62a":   "bauantrag",
    "62b":   "bauantrag",
    "66a":   "nachbarbenachrichtigung",
    "82a":   "abstandsflaeche",
    "82b":   "ermaechtigungsgrundlage",
    "82c":   "vereinfachtes_genehmigungsverfahren",
    "106":   "schlussvorschrift",
    "113":   "schlussvorschrift",
}

# ---------------------------------------------------------------------------
# Absatz detection
# ---------------------------------------------------------------------------
ABSATZ_RE = re.compile(r'^\((\d+)\)', re.MULTILINE)
PARA_RE   = re.compile(r'^§\s*(\d+[a-z]?)\s*[-—]?\s*(.*?)$', re.IGNORECASE | re.MULTILINE)


def split_paragraphs(text: str) -> list[tuple[str, str, str]]:
    """
    Split text into (par_num, title, body) tuples.
    Handles both § and Art. numbering (BayBO).
    Skips TOC entries — only keeps the substantive body occurrence.
    When a § appears multiple times, the last substantive occurrence wins.
    """
    # BayBO: "Art. N Title" appears inline mid-sentence — inject newlines first
    text = re.sub(r'(?<!\.)(Art\.\s*\d+[a-z]?\s+[A-ZÜÖÄ])', r'\n\1', text)

    para_re = re.compile(
        r'^(?:§|Art\.)\s*(\d+[a-z]?)\s*[-—]?\s*(.*?)$',
        re.IGNORECASE | re.MULTILINE
    )
    matches = list(para_re.finditer(text))
    candidates: dict = {}

    for i, m in enumerate(matches):
        par   = m.group(1).lower().strip()
        title = m.group(2).strip()
        start = m.end()
        end   = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body  = text[start:end].strip()

        has_absatz  = bool(re.search(r'^\(\d+\)', body, re.MULTILINE))
        substantial = len(body) > 100

        existing = candidates.get(par)
        existing_substantial = existing and (len(existing[2]) > 100)
        if has_absatz or substantial:
            # Prefer first substantive over TOC stub; skip if already substantive
            if not existing_substantial:
                candidates[par] = (par, title, body)
        elif par not in candidates:
            candidates[par] = (par, title, body)

    def sort_key(p):
        m2 = re.match(r'^(\d+)([a-z]?)$', p)
        return (int(m2.group(1)), m2.group(2)) if m2 else (9999, p)

    return [candidates[k] for k in sorted(candidates.keys(), key=sort_key)]


def make_rows(par: str, title: str, body: str) -> list[dict]:
    """
    Split a paragraph body into Absatz-level rows.
    Returns list of dicts with keys: row_id, absatz, text, node_type.
    """
    node_type = TYPE_MAP.get(par, "UNKNOWN")
    rows      = []

    # Split on Absatz markers
    absatz_matches = list(ABSATZ_RE.finditer(body))

    if not absatz_matches:
        # No Absatz markers — single row for whole paragraph
        rows.append({
            "row_id":    f"{par}.1",
            "absatz":    "—",
            "text":      body[:300].strip() if body else title,
            "node_type": node_type,
        })
        return rows

    for i, m in enumerate(absatz_matches):
        abs_num = m.group(1)
        start   = m.end()
        end     = absatz_matches[i + 1].start() if i + 1 < len(absatz_matches) else len(body)
        abs_text = body[start:end].strip()
        # Collapse internal newlines
        abs_text = re.sub(r'\s+', ' ', abs_text)

        rows.append({
            "row_id":    f"{par}.{abs_num}",
            "absatz":    f"Abs. {abs_num}",
            "text":      abs_text[:400],
            "node_type": node_type,
        })

    return rows


def generate_inventory(txt_path: str, out_path: str, jurisdiction: str) -> dict:
    """
    Parse a clean .txt file, generate node inventory .md.
    Returns stats dict.
    """
    text = Path(txt_path).read_text(encoding="utf-8", errors="replace")
    paragraphs = split_paragraphs(text)

    lines        = []
    total_rows   = 0
    unknown_pars = []
    seen_pars    = set()

    lines.append(f"# Node Inventory — {jurisdiction}")
    lines.append(f"> Generated from: {Path(txt_path).name}")
    lines.append(f"> Jurisdiction: {jurisdiction}")
    lines.append("")
    lines.append("| Row ID | § | Absatz | Node Type | Text (excerpt) |")
    lines.append("|--------|---|--------|-----------|----------------|")

    for par, title, body in paragraphs:
        # Skip TOC duplicates — keep first occurrence only
        if par in seen_pars:
            continue
        seen_pars.add(par)

        rows = make_rows(par, title, body)

        for row in rows:
            # Escape pipe chars in text
            text_escaped = row["text"].replace("|", "\\|")
            lines.append(
                f"| {row['row_id']} "
                f"| §{par} {title[:40]} "
                f"| {row['absatz']} "
                f"| {row['node_type']} "
                f"| {text_escaped[:120]} |"
            )
            total_rows += 1

        if TYPE_MAP.get(par) is None:
            unknown_pars.append(f"§{par} {title[:50]}")

    Path(out_path).write_text("\n".join(lines), encoding="utf-8")

    return {
        "jurisdiction": jurisdiction,
        "paragraphs":   len(seen_pars),
        "rows":         total_rows,
        "unknown":      len(unknown_pars),
        "unknown_list": unknown_pars,
        "out":          out_path,
    }


def jurisdiction_from_filename(name: str) -> str:
    """Derive a jurisdiction label from filename."""
    mapping = {
        "BauO_BE":    "DE-BE",
        "BauO_HE":    "DE-HE",
        "BauO_LSA":   "DE-ST",
        "BauO_MV":    "DE-MV",
        "BauO_NRW":   "DE-NW",
        "BayBO":      "DE-BY",
        "BbgBO":      "DE-BB",
        "HBauO":      "DE-HH",
        "LBauO_RLP":  "DE-RP",
        "LBO_HB":     "DE-HB",
        "LBO_SH":     "DE-SH",
        "LBO_SL":     "DE-SL",
        "MBO":        "DE-MBO",
        "NBauO":      "DE-NI",
        "SaechsBO":   "DE-SN",
        "ThuerBO":    "DE-TH",
        "BW_LBO":     "DE-BW",
    }
    stem = Path(name).stem
    return mapping.get(stem, stem.upper())


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate node inventory .md from clean LBO/MBO .txt files."
    )
    parser.add_argument(
        "input",
        help="Path to a single .txt file OR a directory containing .txt files.",
    )
    parser.add_argument(
        "--out-dir", "-o",
        default=None,
        help="Output directory for .md files (default: same folder as input).",
    )
    parser.add_argument(
        "--pattern", "-p",
        default="*.txt",
        help="Glob pattern when input is a directory (default: *.txt).",
    )
    args = parser.parse_args()

    input_path = Path(args.input)

    if input_path.is_dir():
        txts = sorted(input_path.glob(args.pattern))
        if not txts:
            print(f"No .txt files matched '{args.pattern}' in {input_path}")
            sys.exit(1)
    elif input_path.is_file():
        txts = [input_path]
    else:
        print(f"Input not found: {input_path}")
        sys.exit(1)

    if args.out_dir:
        out_dir = Path(args.out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
    else:
        out_dir = None

    print(f"Generating inventories for {len(txts)} file(s)...\n")
    print(f"{'File':<30} {'Juris':>8} {'§§':>5} {'Rows':>6} {'UNKNOWN':>8}  Status")
    print("-" * 72)

    all_unknowns = {}

    for txt in txts:
        stem         = txt.stem
        jurisdiction = jurisdiction_from_filename(stem)
        out_name     = f"{stem}_node_inventory.md"
        out_path     = (out_dir or txt.parent) / out_name

        try:
            r = generate_inventory(str(txt), str(out_path), jurisdiction)
            status = f"REVIEW: {r['unknown']} unknown §§" if r["unknown"] else "OK"
            print(
                f"{txt.name:<30} {r['jurisdiction']:>8} {r['paragraphs']:>5} "
                f"{r['rows']:>6} {r['unknown']:>8}  {status}"
            )
            if r["unknown_list"]:
                all_unknowns[txt.name] = r["unknown_list"]
        except Exception as exc:
            print(f"{txt.name:<30} {'':>8} {'':>5} {'':>6} {'':>8}  ERROR: {exc}")

    print()
    if all_unknowns:
        print("UNKNOWN §§ flagged for manual review:")
        for fname, pars in all_unknowns.items():
            print(f"\n  {fname}:")
            for p in pars:
                print(f"    {p}")
    else:
        print("All paragraphs mapped. No unknowns.")