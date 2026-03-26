"""Backward-compatible Brandenburg entrypoint for the generic state section-edge generator."""

from __future__ import annotations

from pathlib import Path

from propra.graph.generate_state_section_edges import generate_for_state

_OUTPUT_FILE = Path(__file__).parent / "bbgbo_section_edges.py"


def generate() -> str:
    """Return the generated Brandenburg section-edge module content."""
    return generate_for_state("BbgBO")


def main() -> None:
    content = generate()
    _OUTPUT_FILE.write_text(content, encoding="utf-8")
    print(f"Wrote {_OUTPUT_FILE} (generated from MBO mapping). Review and adapt.")


if __name__ == "__main__":
    main()
