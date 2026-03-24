"""NetworkX knowledge graph query functions — traverses nodes and edges to retrieve regulatory rules."""

import sys
from pathlib import Path

# Allow importing graph.schema when this module is run directly or via the API
_PROPRA_ROOT = Path(__file__).resolve().parent.parent
if str(_PROPRA_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROPRA_ROOT))

from graph.schema import GOAL_CATEGORIES  # noqa: E402


def query_by_category(category: str) -> list[str]:
    """
    Return the list of KG node types associated with a goal category.

    Args:
        category: One of the 12 keys defined in GOAL_CATEGORIES
                  (e.g. 'fence', 'garage', 'extension').

    Returns:
        List of node type strings to use as retrieval filters.
        Returns an empty list for unknown categories or 'other'.
    """
    return list(GOAL_CATEGORIES.get(category, []))
