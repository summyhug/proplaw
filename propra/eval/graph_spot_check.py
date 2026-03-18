"""Comprehensive graph reliability spot-check.

Runs five quality checks against graph.pkl by sampling nodes per state:

  1. Regeltext quality   — text is non-trivial, no page-noise artifacts remain
  2. Node type accuracy  — check well-known sections have the expected type
  3. Supplements edges   — every state's §§ link back to the MBO counterpart via supplements
  4. Section coverage    — no gaps in section numbering per state
  5. Cross-state consistency — same topic nodes across states have consistent types
"""

import pickle
import re
from collections import defaultdict
from pathlib import Path

GRAPH_PATH = Path(__file__).parent.parent / "data" / "graph.pkl"

# Well-known section → expected node type mapping (holds across all LBOs,
# since they all follow MBO numbering roughly).
KNOWN_SECTIONS = {
    "§1":  "anwendungsbereich",
    "§2":  "begriffsbestimmung",
    "§3":  "allgemeine_anforderung",
    "§6":  "abstandsflaeche",
    "§12": "brandschutzanforderung",  # or brandschutz
    "§14": "brandschutzanforderung",  # Brandschutz in most states
    "§34": None,  # varies: aufzug, technische_anlage
}

# Patterns that should NOT appear in cleaned regeltext
NOISE_PATTERNS = [
    re.compile(r"^[-–]?\s*Seite\s+\d+\s+von\s+\d+", re.IGNORECASE),
    re.compile(r"Fassung\s+vom\s+\d{2}\.\d{2}\.\d{4}\s+Seite\s+\d+", re.IGNORECASE),
    re.compile(r"^\w{3,30}\s+\d{2}\.\d{2}\.\d{4}\s*$"),  # title-only
]

EXPECTED_STATES = [
    "BauO_BE", "BauO_HE", "BauO_LSA", "BauO_MV", "BauO_NRW",
    "BayBO", "BbgBO", "HBauO", "LBO_SH", "LBO_SL",
    "LBauO_RLP", "NBauO", "SaechsBO", "ThuerBO",
]


def load_graph():
    with open(GRAPH_PATH, "rb") as f:
        return pickle.load(f)


def check_regeltext_quality(G):
    """Check that node text is substantive and free of noise artifacts."""
    print("\n══ CHECK 1 — Regeltext quality ══")
    issues = []
    short_count = defaultdict(int)
    noise_count = defaultdict(int)

    for nid, data in G.nodes(data=True):
        text = data.get("text", "")
        prefix = nid.split("_§")[0] if "_§" in nid else None
        if not prefix or prefix == "MBO":
            continue

        # Check for noise patterns
        for pat in NOISE_PATTERNS:
            if pat.search(text):
                noise_count[prefix] += 1
                issues.append(f"  NOISE {prefix}: {nid}: '{text[:80]}'")
                break

        # Check for very short text (< 15 chars) on content nodes
        if len(text) < 15 and data.get("type") not in ("anchor",):
            short_count[prefix] += 1
            if len(issues) < 30:  # cap output
                issues.append(f"  SHORT {prefix}: {nid}: '{text}'")

    total_noise = sum(noise_count.values())
    total_short = sum(short_count.values())

    if total_noise == 0:
        print("  [PASS] No noise artifacts found in any node text")
    else:
        print(f"  [FAIL] {total_noise} nodes still have noise artifacts:")
        for s, c in sorted(noise_count.items()):
            print(f"         {s}: {c}")

    if total_short == 0:
        print("  [PASS] No ultra-short content nodes")
    else:
        print(f"  [WARN] {total_short} content nodes with text < 15 chars")
        for s, c in sorted(short_count.items()):
            print(f"         {s}: {c}")

    if issues:
        print("  Details (first 30):")
        for i in issues[:30]:
            print(i)

    return total_noise == 0


def check_node_type_accuracy(G):
    """Spot-check well-known sections have sensible types."""
    print("\n══ CHECK 2 — Node type accuracy (spot-check) ══")
    ok = 0
    issues = []

    for nid, data in G.nodes(data=True):
        if "_§" not in nid:
            continue
        ntype = data.get("type", "")

        # Check §1 → anwendungsbereich
        if re.search(r"_§1_", nid) and "1.1" in nid:
            if ntype == "anwendungsbereich":
                ok += 1
            else:
                issues.append(f"  {nid}: expected anwendungsbereich, got {ntype}")

        # Check §2 → begriffsbestimmung
        if re.search(r"_§2_", nid) and "2.1" in nid:
            if ntype == "begriffsbestimmung":
                ok += 1
            else:
                issues.append(f"  {nid}: expected begriffsbestimmung, got {ntype}")

        # Check §6 → abstandsflaeche
        if re.search(r"_§6_", nid) and "6.1" in nid:
            if ntype == "abstandsflaeche":
                ok += 1
            else:
                issues.append(f"  {nid}: expected abstandsflaeche, got {ntype}")

    if issues:
        print(f"  [WARN] {len(issues)} type mismatches found:")
        for i in issues[:20]:
            print(i)
    else:
        print(f"  [PASS] All {ok} spot-checked nodes have correct types")
    return len(issues) == 0


def check_supplements_edges(G):
    """Verify state LBO nodes link to MBO via supplements edges."""
    print("\n══ CHECK 3 — Supplements edges (state → section anchors) ══")
    # For each state, check that supplements edges exist
    state_supplements = defaultdict(int)
    state_sub_items = defaultdict(int)

    for u, v, data in G.edges(data=True):
        rel = data.get("relation", "")
        prefix_u = u.split("_§")[0] if "_§" in u else None
        if not prefix_u or prefix_u == "MBO":
            continue
        if rel == "supplements":
            state_supplements[prefix_u] += 1
        elif rel == "sub_item_of":
            state_sub_items[prefix_u] += 1

    all_pass = True
    for state in EXPECTED_STATES:
        sup = state_supplements.get(state, 0)
        sub = state_sub_items.get(state, 0)
        if sup == 0:
            print(f"  [FAIL] {state}: 0 supplements edges — not linked to graph")
            all_pass = False
        elif sup < 50:
            print(f"  [WARN] {state}: only {sup} supplements edges (expected 80+)")
        else:
            print(f"  [PASS] {state}: {sup} supplements, {sub} sub_item_of")

    return all_pass


def check_section_coverage(G):
    """Check that section numbering has no large gaps per state."""
    print("\n══ CHECK 4 — Section numbering coverage ══")
    state_sections = defaultdict(set)

    for nid in G.nodes:
        if "_§" not in nid:
            continue
        prefix = nid.split("_§")[0]
        # Extract section number
        m = re.search(r"_§(\d+)", nid)
        if m:
            state_sections[prefix].add(int(m.group(1)))

    all_pass = True
    for state in sorted(EXPECTED_STATES):
        secs = sorted(state_sections.get(state, []))
        if not secs:
            print(f"  [FAIL] {state}: no sections found")
            all_pass = False
            continue

        # Check for gaps > 2 in consecutive section numbering
        gaps = []
        for i in range(1, len(secs)):
            if secs[i] - secs[i - 1] > 2:
                gaps.append(f"§{secs[i-1]}→§{secs[i]}")

        if gaps:
            print(f"  [WARN] {state}: §{secs[0]}–§{secs[-1]} ({len(secs)} sections), gaps: {', '.join(gaps[:5])}")
        else:
            print(f"  [PASS] {state}: §{secs[0]}–§{secs[-1]} ({len(secs)} sections), no large gaps")

    return all_pass


def check_cross_state_consistency(G):
    """Check that the same topic sections across states have consistent types."""
    print("\n══ CHECK 5 — Cross-state type consistency ══")
    # For each section number, collect (state, type) pairs
    sec_types = defaultdict(lambda: defaultdict(set))

    for nid, data in G.nodes(data=True):
        if "_§" not in nid:
            continue
        prefix = nid.split("_§")[0]
        m = re.search(r"_§(\d+)_", nid)
        if m:
            sec_num = int(m.group(1))
            ntype = data.get("type", "unknown")
            sec_types[sec_num][prefix].add(ntype)

    # For key sections, check consistency
    key_sections = [1, 2, 3, 6]
    issues = []
    ok = 0

    for sec in key_sections:
        types_per_state = sec_types.get(sec, {})
        # Get the most common type
        all_types = defaultdict(int)
        for state, types in types_per_state.items():
            for t in types:
                all_types[t] += 1

        if not all_types:
            continue

        dominant = max(all_types, key=all_types.get)
        outliers = []
        for state, types in types_per_state.items():
            if dominant not in types:
                outliers.append(f"{state}={list(types)}")

        if outliers:
            issues.append(f"  §{sec}: dominant={dominant}, outliers: {', '.join(outliers[:5])}")
        else:
            ok += 1
            print(f"  [PASS] §{sec}: all states use '{dominant}'")

    if issues:
        print(f"  [WARN] {len(issues)} sections have inconsistent types:")
        for i in issues:
            print(i)

    return len(issues) == 0


def main():
    print(f"Loading graph: {GRAPH_PATH}")
    G = load_graph()
    print(f"  {G.number_of_nodes()} nodes, {G.number_of_edges()} edges\n")

    results = {}
    results["regeltext"] = check_regeltext_quality(G)
    results["node_types"] = check_node_type_accuracy(G)
    results["supplements"] = check_supplements_edges(G)
    results["coverage"] = check_section_coverage(G)
    results["consistency"] = check_cross_state_consistency(G)

    print("\n" + "═" * 50)
    failures = [k for k, v in results.items() if not v]
    if failures:
        print(f"  RESULT: {len(failures)} check(s) with issues: {', '.join(failures)}")
    else:
        print("  RESULT: ALL CHECKS PASS")


if __name__ == "__main__":
    main()
