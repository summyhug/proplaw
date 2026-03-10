"""
LLM-assisted edge proposal for the Propra knowledge graph.

Sends a filtered set of nodes to Claude and asks it to propose typed edges.
All proposed edges are validated against RELATION_TYPES and node IDs before
being returned as Edge objects.

Usage:
    from propra.graph.edge_proposer import propose_edges

    edges = propose_edges(graph, node_ids=["BW_LBO_§6-01", ...])
    for edge in edges:
        add_edge(graph, edge)
"""

import json
import os
from pathlib import Path
from typing import Optional

import anthropic
import networkx as nx
from dotenv import load_dotenv

from propra.graph.schema import RELATION_TYPES, Edge

load_dotenv()

_PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "propose_edges.txt"
_MODEL = "claude-sonnet-4-6"

_RELATION_DESCRIPTIONS = {
    "has_condition":     "rule node → its numeric threshold or condition node",
    "applies_to":        "general rule → specific subject it governs",
    "exception_of":      "exception node → the base rule it overrides",
    "supplements":       "clarifying rule → the rule it adds context to",
    "references":        "cross-reference → the referenced paragraph node",
    "overridden_by":     "LBO standard rule → local bylaw (§74) that can override it",
    "enables_procedure": "project type → the permit procedure type it triggers",
    "requires_proof":    "requirement → the required proof or document type",
    "classified_as":     "project → its legal category node",
    "belongs_to_group":  "annex entry → its annex group node",
    "responsible_for":   "authority → the procedure it handles",
    "applies_in":        "rule → the zone or jurisdiction type it applies in",
}


def propose_edges(
    G: nx.DiGraph,
    node_ids: list[str],
    max_edges: int = 80,
    verbose: bool = True,
) -> list[Edge]:
    """
    Ask Claude to propose edges between the given nodes.

    Args:
        G:         The base graph (used to look up node attributes).
        node_ids:  List of node IDs to include in the proposal request.
        max_edges: Soft cap on edges returned (Claude may return fewer).
        verbose:   Print progress and validation summary.

    Returns:
        List of validated Edge objects ready to be added to the graph.
    """
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    # Build compact node list for the prompt
    nodes_for_prompt = []
    for nid in node_ids:
        if nid not in G:
            continue
        data = G.nodes[nid]
        nodes_for_prompt.append({
            "id":               nid,
            "type":             data.get("type", ""),
            "source_paragraph": data.get("source_paragraph", ""),
            "text":             data.get("text", "")[:200],  # truncate long texts
        })

    if not nodes_for_prompt:
        print("[WARN] No valid nodes found for edge proposal.")
        return []

    prompt_template = _PROMPT_PATH.read_text(encoding="utf-8")
    # Strip the comment block (lines starting with #) before sending to LLM
    prompt_body = "\n".join(
        line for line in prompt_template.splitlines()
        if not line.startswith("#")
    ).strip()

    prompt = prompt_body.replace(
        "{nodes_json}", json.dumps(nodes_for_prompt, ensure_ascii=False, indent=2)
    ).replace(
        "{relation_types}", json.dumps(_RELATION_DESCRIPTIONS, ensure_ascii=False, indent=2)
    )

    if verbose:
        print(f"  Sending {len(nodes_for_prompt)} nodes to {_MODEL} for edge proposals...")

    message = client.messages.create(
        model=_MODEL,
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}],
    )

    raw = message.content[0].text.strip()

    # Parse and validate
    try:
        proposals = json.loads(raw)
    except json.JSONDecodeError:
        # Try to extract JSON array from response if wrapped in markdown
        import re
        match = re.search(r"\[.*\]", raw, re.DOTALL)
        if match:
            proposals = json.loads(match.group(0))
        else:
            print(f"[ERROR] Could not parse Claude response as JSON.")
            print(raw[:500])
            return []

    valid_ids = set(node_ids)
    edges: list[Edge] = []
    skipped = 0

    for p in proposals[:max_edges]:
        source = p.get("source", "")
        target = p.get("target", "")
        relation = p.get("relation", "")
        sourced_from = p.get("sourced_from", "")

        issues = []
        if source not in valid_ids:
            issues.append(f"unknown source '{source}'")
        if target not in valid_ids:
            issues.append(f"unknown target '{target}'")
        if relation not in RELATION_TYPES:
            issues.append(f"unknown relation '{relation}'")
        if not sourced_from:
            issues.append("missing sourced_from")

        if issues:
            if verbose:
                print(f"  [SKIP] {source} →{relation}→ {target}: {'; '.join(issues)}")
            skipped += 1
            continue

        e = Edge(source=source, target=target, relation=relation, sourced_from=sourced_from,
                 metadata={"reasoning": p.get("reasoning", "")})
        try:
            e.validate()
            edges.append(e)
        except ValueError as err:
            if verbose:
                print(f"  [SKIP] Validation failed: {err}")
            skipped += 1

    if verbose:
        print(f"  Proposed: {len(proposals)}  Valid: {len(edges)}  Skipped: {skipped}")

    return edges
