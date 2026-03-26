"""
Match state LBO sections to their MBO equivalents by title similarity.

Reads section headings from a state inventory and the MBO inventory,
matches them by normalised title, and writes a JSON mapping file to
propra/data/{STATE}_mbo_mapping.json.

The output has three buckets:
  mapping  — high-confidence matches (score >= threshold); used directly
             to build state_version_of edges in the graph.
  review   — low-confidence matches that need a human decision.
  unmatched — state sections with no plausible MBO equivalent (new provisions).

Usage:
    python -m propra.graph.map_to_mbo --state BbgBO
    python -m propra.graph.map_to_mbo --state BbgBO --threshold 0.80
"""

import argparse
import json
import re
import sys
from datetime import date
from difflib import SequenceMatcher
from pathlib import Path

_DATA = Path(__file__).parent.parent / "data"
_NODE_INVENTORY_DIR = "node inventory"
_MBO_INVENTORY = _DATA / _NODE_INVENTORY_DIR / "MBO_node_inventory.md"

# Auto-confirmed if score >= HIGH_THRESHOLD; sent to review if >= LOW_THRESHOLD
_HIGH_THRESHOLD = 0.85
_LOW_THRESHOLD = 0.50

_UMLAUT = str.maketrans({
    "ä": "ae", "ö": "oe", "ü": "ue", "ß": "ss",
    "Ä": "ae", "Ö": "oe", "Ü": "ue",
})

_TITLE_CUTOFF_PATTERNS = [
    re.compile(r"^\s*Seite\s+\d+\s+von\s+\d+\s+", re.IGNORECASE),
    re.compile(r"\b2130-\d+\s+\d+\b"),
    re.compile(
        r"\b(?:Erster|Erste|Zweiter|Dritter|Vierter|F(?:uenf|ünf)ter|Sechster|Siebenter|Achter|Neunter|Zehnter)\s+"
        r"(?:Teil|Abschnitt)\b.*$",
        re.IGNORECASE,
    ),
    re.compile(r"\bTeil\s+\d+\b.*$", re.IGNORECASE),
    re.compile(r"\bAbschnitt\s+(?:[IVXLC]+|\d+)\b.*$", re.IGNORECASE),
    re.compile(r"\bFassung\s+vom\b.*$", re.IGNORECASE),
    re.compile(r"\b(?:©\s*20\d{2}\s+)?(?:Wolters|Kluwer)\b.*$", re.IGNORECASE),
    re.compile(r"\bgespeichert:\s*\d{2}\.\d{2}\.\d{4},\s*\d{2}:\d{2}\s*Uhr.*$", re.IGNORECASE),
    re.compile(r"©\s*20\d{2}.*$", re.IGNORECASE),
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _extract_titles(path: Path) -> dict[str, str]:
    """
    Parse section headings from an inventory markdown file.

    Returns dict of {§_number: title}, e.g. {'29': 'Erster und zweiter Rettungsweg'}.
    Supports (1) ### § N — Title headings and (2) flat table with | row_id | §N Title | ...
    (e.g. MBO_node_inventory.md). Only the first occurrence of each § number is kept.
    """
    titles: dict[str, str] = {}
    lines = path.read_text(encoding="utf-8").splitlines()

    for line in lines:
        m = re.match(r"^###\s+§§?\s*(\d+[a-z]?)\s*[—\-]\s*(.+)", line.strip(), re.IGNORECASE)
        if m:
            num = m.group(1).lower()
            title = _clean_title(m.group(2).strip())
            if num not in titles:
                titles[num] = title

    if titles:
        return titles

    # Fallback: MBO-style flat table (| Row ID | § | Absatz | ... or | 1.1 | §1 Anwendungsbereich | ...)
    for line in lines:
        stripped = line.strip()
        if not stripped.startswith("|") or "|" not in stripped[1:]:
            continue
        cells = [c.strip() for c in stripped.strip("|").split("|")]
        if len(cells) < 2:
            continue
        # Second column often "§1 Anwendungsbereich" or "§1 Anwendungsbereich"
        cell = cells[1]
        m = re.match(r"§\s*(\d+[a-z]?)\s+(.+)", cell, re.IGNORECASE)
        if m:
            num = m.group(1).lower()
            title = _clean_title(m.group(2).strip())
            if num not in titles:
                titles[num] = title
    return titles


def _clean_title(title: str) -> str:
    """Trim obvious extraction bleed so matching uses the actual section heading."""
    cleaned = " ".join(title.split())
    for pattern in _TITLE_CUTOFF_PATTERNS:
        cleaned = pattern.sub("", cleaned).strip()
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned.rstrip(" .;,:-")


def _normalise(title: str) -> str:
    """Lowercase, strip umlauts, collapse punctuation/whitespace for comparison."""
    t = title.lower().translate(_UMLAUT)
    t = t.replace("geltungsbereich", "anwendungsbereich")
    t = re.sub(r"[^a-z0-9\s]", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def _similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, _normalise(a), _normalise(b)).ratio()


def _section_key(num: str) -> tuple[int, str]:
    m = re.match(r"^(\d+)([a-z]?)$", num)
    if not m:
        return (0, num)
    return (int(m.group(1)), m.group(2))


def _score_match(state_num: str, state_title: str, mbo_num: str, mbo_title: str) -> float:
    """
    Score one state-title ↔ MBO-title pair.

    Exact or near-exact title matches should win. If the section number also lines up,
    give a small bonus, but only when the lexical match is already fairly plausible.
    """
    base = _similarity(state_title, mbo_title)
    state_key = _section_key(state_num)
    mbo_key = _section_key(mbo_num)

    if state_key == mbo_key and base >= 0.70:
        base += 0.15
    elif state_key[0] == mbo_key[0] and base >= 0.60:
        base += 0.10
    elif abs(state_key[0] - mbo_key[0]) <= 1 and base >= 0.85:
        base += 0.05

    return min(base, 1.0)


def _best_mbo_match(state_num: str, title: str, mbo_titles: dict[str, str]) -> tuple[str, str, float]:
    """Return (mbo_num, mbo_title, score) for the closest MBO section title."""
    best_num, best_title, best_score = "", "", 0.0
    for num, t in mbo_titles.items():
        s = _score_match(state_num, title, num, t)
        if s > best_score:
            best_num, best_title, best_score = num, t, s
    return best_num, best_title, best_score


def _find_state_inventory(state: str) -> Path:
    """Prefer the fine inventory, then v2, then the paragraph-level fallback."""
    state_dir = _DATA / _NODE_INVENTORY_DIR
    candidates = [
        state_dir / f"{state}_node_inventory_fine.md",
        state_dir / f"{state}_node_inventory_v2.md",
        state_dir / f"{state}_node_inventory.md",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[-1]


# ---------------------------------------------------------------------------
# Core
# ---------------------------------------------------------------------------

def build_mapping(
    state: str,
    high_threshold: float = _HIGH_THRESHOLD,
    low_threshold: float = _LOW_THRESHOLD,
) -> dict:
    """
    Match all sections from a state inventory to MBO sections.

    Returns a dict with keys: state, generated, mapping, review, unmatched.
    """
    state_inventory = _find_state_inventory(state)
    if not state_inventory.exists():
        print(f"[ERROR] Inventory not found: {state_inventory}", file=sys.stderr)
        sys.exit(1)

    mbo_titles = _extract_titles(_MBO_INVENTORY)
    state_titles = _extract_titles(state_inventory)

    print(f"MBO sections   : {len(mbo_titles)}")
    print(f"{state} sections: {len(state_titles)}")
    print(f"Thresholds     : auto={high_threshold:.2f}  review={low_threshold:.2f}\n")

    mapping: dict[str, str] = {}          # state_§ -> mbo_§  (high confidence)
    review: list[dict] = []               # needs human decision
    unmatched: list[str] = []             # no match above low_threshold

    # Track which MBO sections are already claimed (warn on duplicates)
    claimed: dict[str, str] = {}          # mbo_§ -> state_§ that claimed it

    for state_num, state_title in sorted(state_titles.items(), key=lambda x: _section_key(x[0])):
        mbo_num, mbo_title, score = _best_mbo_match(state_num, state_title, mbo_titles)

        if score >= high_threshold:
            if mbo_num in claimed:
                # Duplicate — lower score goes to review
                print(f"  [DUPE] §{state_num} '{state_title}' → MBO §{mbo_num} already claimed by §{claimed[mbo_num]}")
                review.append({
                    "state_para": state_num,
                    "state_title": state_title,
                    "mbo_para": mbo_num,
                    "mbo_title": mbo_title,
                    "score": round(score, 3),
                    "flag": "duplicate_mbo_target",
                })
            else:
                mapping[state_num] = mbo_num
                claimed[mbo_num] = state_num
        elif score >= low_threshold:
            review.append({
                "state_para": state_num,
                "state_title": state_title,
                "mbo_para": mbo_num,
                "mbo_title": mbo_title,
                "score": round(score, 3),
                "flag": "low_confidence",
            })
        else:
            unmatched.append({
                "state_para": state_num,
                "state_title": state_title,
                "best_mbo_para": mbo_num,
                "best_mbo_title": mbo_title,
                "best_score": round(score, 3),
            })

    return {
        "state": state,
        "generated": str(date.today()),
        "thresholds": {"auto": high_threshold, "review": low_threshold},
        "mapping": mapping,
        "review": review,
        "unmatched": unmatched,
    }


def print_summary(result: dict) -> None:
    """Print a human-readable summary of the mapping result."""
    state = result["state"]
    print(f"{'─' * 50}")
    print(f"Auto-matched  : {len(result['mapping'])} sections")
    print(f"Needs review  : {len(result['review'])} sections")
    print(f"Unmatched     : {len(result['unmatched'])} sections")
    print()

    if result["review"]:
        print("── Review needed (check and move to mapping or unmatched) ──")
        for r in result["review"]:
            print(f"  {state} §{r['state_para']:>4}  '{r['state_title']}'")
            print(f"         → MBO §{r['mbo_para']:>4}  '{r['mbo_title']}'  score={r['score']}  [{r['flag']}]")
        print()

    if result["unmatched"]:
        print("── Unmatched (likely {state}-specific provisions) ──")
        for u in result["unmatched"]:
            print(f"  {state} §{u['state_para']:>4}  '{u['state_title']}'  (best={u['best_score']})")


def save_mapping(result: dict) -> Path:
    """Write the mapping result to propra/data/{STATE}_mbo_mapping.json."""
    out = _DATA / f"{result['state']}_mbo_mapping.json"
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return out


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Match state LBO sections to MBO by title similarity.")
    parser.add_argument("--state", required=True, help="State inventory name, e.g. BbgBO")
    parser.add_argument("--threshold", type=float, default=_HIGH_THRESHOLD,
                        help=f"Auto-match threshold (default {_HIGH_THRESHOLD})")
    parser.add_argument("--review-threshold", type=float, default=_LOW_THRESHOLD,
                        help=f"Review threshold (default {_LOW_THRESHOLD})")
    args = parser.parse_args()

    result = build_mapping(args.state, args.threshold, args.review_threshold)
    print_summary(result)
    out = save_mapping(result)
    print(f"\nSaved: {out}")
