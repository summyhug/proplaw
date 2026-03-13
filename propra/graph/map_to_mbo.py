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


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _extract_titles(path: Path) -> dict[str, str]:
    """
    Parse section headings from an inventory markdown file.

    Returns dict of {§_number: title}, e.g. {'29': 'Erster und zweiter Rettungsweg'}.
    Only the first occurrence of each § number is kept (guards against duplicates).
    """
    titles: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^###\s+§§?\s*(\d+[a-z]?)\s*[—\-]\s*(.+)", line.strip(), re.IGNORECASE)
        if m:
            num = m.group(1).lower()
            title = m.group(2).strip()
            if num not in titles:
                titles[num] = title
    return titles


def _normalise(title: str) -> str:
    """Lowercase, strip umlauts, collapse punctuation/whitespace for comparison."""
    t = title.lower().translate(_UMLAUT)
    t = re.sub(r"[^a-z0-9\s]", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def _similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, _normalise(a), _normalise(b)).ratio()


def _best_mbo_match(title: str, mbo_titles: dict[str, str]) -> tuple[str, str, float]:
    """Return (mbo_num, mbo_title, score) for the closest MBO section title."""
    best_num, best_title, best_score = "", "", 0.0
    for num, t in mbo_titles.items():
        s = _similarity(title, t)
        if s > best_score:
            best_num, best_title, best_score = num, t, s
    return best_num, best_title, best_score


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
    state_dir = _DATA / _NODE_INVENTORY_DIR
    state_inventory = state_dir / f"{state}_node_inventory_v2.md"
    if not state_inventory.exists():
        state_inventory = state_dir / f"{state}_node_inventory.md"
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

    for state_num, state_title in sorted(state_titles.items(), key=lambda x: int(re.sub(r"[a-z]", "", x[0]))):
        mbo_num, mbo_title, score = _best_mbo_match(state_title, mbo_titles)

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
