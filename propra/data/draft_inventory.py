"""
propra/data/draft_inventory.py
────────────────────────────────────────────────────────────────────────────
Semi-automated node inventory drafter for LBO/BayBO source texts.

Parses a cleaned .txt file (output of extract_pdf.py), splits it into
provisions (§ or Art.), classifies each using an LLM (Anthropic or Gemini)
against the NODE_TYPES in schema.py, and outputs a draft node_inventory.md
in the same format as BW_LBO_node_inventory.md.

The output is a DRAFT — always review and correct before committing.

Usage:
    python propra/data/draft_inventory.py \
        --txt propra/data/txt/BayBO.txt \
        --bundesland Bayern \
        --lbo_code BayBO \
        --jurisdiction DE-BY \
        --version_date "23. Dezember 2025" \
        --source_url "https://www.gesetze-bayern.de/Content/Document/BayBO" \
        --output propra/data/node inventory/BayBO_node_inventory.md

    # Dry run — parse only, no API calls, no output file
    python propra/data/draft_inventory.py --txt propra/data/txt/BayBO.txt --dry_run
"""

import argparse
import os
import re
import sys
import time
from dataclasses import dataclass
from pathlib import Path

import anthropic
from dotenv import load_dotenv

try:
    import google.generativeai as genai
except ImportError:
    genai = None

# Import node types from schema
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from propra.graph.schema import NODE_TYPES

load_dotenv()
sys.stdout.reconfigure(encoding='utf-8')


# ─── Data structures ──────────────────────────────────────────────────────────

@dataclass
class Provision:
    """A single § or Art. provision parsed from the source text."""
    number: str          # e.g. "§ 6" or "Art. 6"
    title: str           # e.g. "Abstandsflächen" (may be empty)
    full_text: str       # complete raw text of the provision
    absaetze: list[str]  # individual Absätze (paragraphs within the provision)


# ─── Parsing ──────────────────────────────────────────────────────────────────

# Matches: § 6, §6, Art. 6, Art.6, Artikel 6
PROVISION_START = re.compile(
    r"^((?:§\s*|Art(?:ikel)?\.\s*)\d+[a-zA-Z]?)\s*(.*?)$",
    re.MULTILINE,
)

ABSATZ_START = re.compile(r"^\(\d+\)")

# Words that, when capitalised, signal the start of body text rather than a
# title continuation.  German prepositions / articles / copulas that open
# sentences only appear with an uppercase initial letter at sentence start.
_BODY_STARTERS = frozenset({
    "Die", "Das", "Der", "Den", "Dem", "Des",
    "Ein", "Eine", "Einer", "Einem", "Einen", "Eines",
    "Bei", "In", "An", "Von", "Mit", "Über", "Unter",
    "Nach", "Für", "Zu", "Durch", "Aus", "Auf", "Bis",
    "Zwischen", "Neben", "Hinter", "Vor", "Gegen", "Ohne",
    "Soweit", "Sofern", "Wenn", "Falls",
    "Sind", "Ist", "Wird", "Werden", "Hat", "Haben",
    "Abweichend", "Unbeschadet", "Vorbehaltlich",
})


def _split_title_body(rest: str) -> tuple[str, str]:
    """Split 'Title Body...' into (title, body_remainder).

    When extract_pdf.py joins a provision heading with its body text on one
    line (e.g. for provisions without Absätze), group 2 of PROVISION_START
    contains both the title noun-phrase and the opening body sentence.  We
    detect the boundary at the first word (position >= 1) that is a known
    German clause-opener (preposition, article, copula).
    """
    words = rest.split(" ")
    for i in range(1, len(words)):
        if words[i] in _BODY_STARTERS:
            return " ".join(words[:i]), " ".join(words[i:])
    return rest, ""


def parse_provisions(text: str) -> list[Provision]:
    """
    Split cleaned LBO text into individual provisions.
    Handles both § (most LBOs) and Art. (BayBO) numbering.
    """
    lines = text.splitlines()
    provisions = []
    current_number = None
    current_title = ""
    current_lines = []

    def flush():
        if current_number and current_lines:
            full = "\n".join(current_lines).strip()
            absaetze = _split_absaetze(full)
            provisions.append(Provision(
                number=current_number,
                title=current_title,
                full_text=full,
                absaetze=absaetze,
            ))

    for line in lines:
        m = PROVISION_START.match(line.strip())
        if m:
            flush()
            current_number = m.group(1).strip()
            current_title, _body_rem = _split_title_body(m.group(2).strip())
            current_lines = [line]
            if _body_rem:
                current_lines.append(_body_rem)
        elif current_number is not None:
            current_lines.append(line)

    flush()
    return provisions


def _split_absaetze(text: str) -> list[str]:
    """Split provision text into individual Absätze."""
    parts = re.split(r"(?=^\(\d+\))", text, flags=re.MULTILINE)
    return [p.strip() for p in parts if p.strip()]


# ─── Anthropic classification ─────────────────────────────────────────────────

CLASSIFICATION_PROMPT = """You are a German building law expert classifying provisions of a Landesbauordnung (LBO) into node types for a knowledge graph.

Given this provision from {lbo_code}:

PROVISION: {number} {title}
TEXT:
{text}

Classify it into EXACTLY ONE of these node types (German legal taxonomy):
{node_types}

Rules:
- Return ONLY the node type string, nothing else
- Choose the most specific type that fits
- If the provision contains multiple aspects, choose the dominant one
- "zahlenwert" is only for pure numeric threshold nodes, not full provisions
- "schlussvorschrift" for final/transitional provisions
- "ermaechtigungsgrundlage" for authorization/enabling provisions

Node type:"""


def _call_llm_anthropic(api_key: str, prompt: str) -> str:
    """Call Anthropic API; return raw response text."""
    client = anthropic.Anthropic(api_key=api_key)
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=50,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text.strip()


def _call_llm_gemini(api_key: str, prompt: str, model_id: str | None = None) -> str:
    """Call Gemini API; return raw response text."""
    if genai is None:
        raise RuntimeError("google-generativeai not installed. pip install google-generativeai")
    genai.configure(api_key=api_key)
    model_id = model_id or os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
    model = genai.GenerativeModel(model_id)
    response = model.generate_content(prompt)
    if not response.text:
        raise RuntimeError("Gemini returned empty response")
    return response.text.strip()


def classify_provision(
    provider: str,
    api_key: str,
    provision: Provision,
    lbo_code: str,
    gemini_model: str | None = None,
) -> str:
    """
    Use LLM (Anthropic or Gemini) to classify a provision into a NODE_TYPE.
    Returns the node type string.
    """
    node_types_list = "\n".join(f"- {t}" for t in sorted(NODE_TYPES))

    prompt = CLASSIFICATION_PROMPT.format(
        lbo_code=lbo_code,
        number=provision.number,
        title=provision.title,
        text=provision.full_text[:1500],  # cap to avoid token waste
        node_types=node_types_list,
    )

    if provider == "gemini":
        raw = _call_llm_gemini(api_key, prompt, model_id=gemini_model)
    else:
        raw = _call_llm_anthropic(api_key, prompt)

    result = raw.lower().replace(" ", "_")

    # Validate — fall back to allgemeine_anforderung if unknown
    if result not in NODE_TYPES:
        print(f"  WARN  Unknown type '{result}' for {provision.number} - defaulting to allgemeine_anforderung")
        return "allgemeine_anforderung"

    return result


# ─── Markdown generation ──────────────────────────────────────────────────────

def format_provision_md(
    provision: Provision,
    node_type: str,
    lbo_code: str,
    jurisdiction: str,
) -> str:
    """
    Format a single provision as a markdown section matching the BW inventory format.
    """
    lines = []

    # Section header
    lines.append(f"### {provision.number}" + (f" — {provision.title}" if provision.title else ""))
    lines.append(f"**type:** {node_type}")
    lines.append("")

    # Build table from Absätze
    lines.append("| Nr. | Regeltext (Wortlaut) |")
    lines.append("|---|---|")

    # Normalise number for row IDs: "Art. 6" → "6", "§ 6" → "6"
    num_clean = re.sub(r"[^\d]", "", provision.number)

    if provision.absaetze:
        for i, absatz in enumerate(provision.absaetze, 1):
            text = absatz.replace("\n", " ").replace("|", "\\|")
            lines.append(f"| {num_clean}.{i} | {text} |")
    else:
        text = provision.full_text.replace("\n", " ").replace("|", "\\|")
        lines.append(f"| {num_clean}.1 | {text} |")

    lines.append("")
    lines.append("---")
    lines.append("")

    return "\n".join(lines)


def build_inventory_md(
    provisions: list[Provision],
    node_types: list[str],
    bundesland: str,
    lbo_code: str,
    jurisdiction: str,
    version_date: str,
    source_url: str,
) -> str:
    """Assemble the full node inventory markdown document."""
    header = f"""# {lbo_code} — Knotenverzeichnis
## {_full_lbo_name(lbo_code)}
**source:** {lbo_code}.pdf — Fassung {version_date}
**jurisdiction:** {bundesland} ({jurisdiction})
**source_url:** {source_url}

---

> **purpose:** Strukturiertes Verzeichnis aller Paragrafen/Artikel der {lbo_code}. Vorbereitungsdokument für den Wissensgraphen — nur Knoten, keine Kanten. ⚠️ DRAFT — manuell prüfen und korrigieren vor Commit.

---

"""

    body_parts = []
    for provision, node_type in zip(provisions, node_types):
        body_parts.append(format_provision_md(provision, node_type, lbo_code, jurisdiction))

    return header + "\n".join(body_parts)


def _full_lbo_name(lbo_code: str) -> str:
    names = {
        "BayBO": "Bayerische Bauordnung (BayBO)",
        "LBO_BW": "Landesbauordnung Baden-Württemberg (LBO)",
        "BauO_Bln": "Bauordnung für Berlin (BauO Bln)",
        "BbgBO": "Brandenburgische Bauordnung (BbgBO)",
        "BremLBO": "Bremische Landesbauordnung (BremLBO)",
        "HBauO": "Hamburgische Bauordnung (HBauO)",
        "HBO": "Hessische Bauordnung (HBO)",
        "LBauO_MV": "Landesbauordnung Mecklenburg-Vorpommern (LBauO M-V)",
        "NBauO": "Niedersächsische Bauordnung (NBauO)",
        "BauO_NRW": "Bauordnung Nordrhein-Westfalen (BauO NRW)",
        "LBauO_RLP": "Landesbauordnung Rheinland-Pfalz (LBauO RLP)",
        "LBO_SL": "Landesbauordnung Saarland (LBO)",
        "SaechsBO": "Sächsische Bauordnung (SächsBO)",
        "BauO_LSA": "Bauordnung des Landes Sachsen-Anhalt (BauO LSA)",
        "LBO_SH": "Landesbauordnung Schleswig-Holstein (LBO)",
        "ThürBO": "Thüringer Bauordnung (ThürBO)",
        "MBO": "Musterbauordnung (MBO)",
    }
    return names.get(lbo_code, lbo_code)


# ─── Main pipeline ─────────────────────────────────────────────────────────────

def draft_inventory(
    txt_path: Path,
    bundesland: str,
    lbo_code: str,
    jurisdiction: str,
    version_date: str,
    source_url: str,
    output_path: Path,
    dry_run: bool = False,
    rate_limit_delay: float = 0.3,
    provider: str = "anthropic",
    gemini_model: str | None = None,
) -> None:
    """Full pipeline: parse → classify → write inventory."""

    print(f"\n{'='*60}")
    print(f"Drafting node inventory: {lbo_code}")
    print(f"Source: {txt_path}")
    print(f"{'='*60}\n")

    # 1. Parse
    text = txt_path.read_text(encoding="utf-8")
    provisions = parse_provisions(text)
    print(f"OK Parsed {len(provisions)} provisions\n")

    if not provisions:
        print("ERR No provisions found - check the .txt format")
        sys.exit(1)

    # Preview first 5
    print("First 5 provisions detected:")
    for p in provisions[:5]:
        print(f"  {p.number:12s} | {p.title[:50]}")
    print()

    if dry_run:
        print("[DRY RUN] — stopping here, no API calls, no output written")
        return

    # 2. Classify via LLM (Anthropic or Gemini)
    if provider == "gemini":
        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            print("ERR GEMINI_API_KEY or GOOGLE_API_KEY not set in .env")
            sys.exit(1)
    else:
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            print("ERR ANTHROPIC_API_KEY not set in .env")
            sys.exit(1)

    node_types = []

    print(f"Classifying {len(provisions)} provisions via {provider}...")
    print("(This takes ~1-2 minutes for a full LBO)\n")

    for i, provision in enumerate(provisions, 1):
        try:
            node_type = classify_provision(provider, api_key, provision, lbo_code, gemini_model=gemini_model)
            node_types.append(node_type)
            print(f"  [{i:3d}/{len(provisions)}] {provision.number:12s} → {node_type}")
            time.sleep(rate_limit_delay)  # be gentle with the API
        except Exception as e:
            print(f"  WARN  Error classifying {provision.number}: {e} - defaulting to allgemeine_anforderung")
            node_types.append("allgemeine_anforderung")

    print(f"\nOK Classified {len(node_types)} provisions")

    # 3. Build markdown
    md = build_inventory_md(
        provisions=provisions,
        node_types=node_types,
        bundesland=bundesland,
        lbo_code=lbo_code,
        jurisdiction=jurisdiction,
        version_date=version_date,
        source_url=source_url,
    )

    # 4. Write output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(md, encoding="utf-8")

    print(f"\nOK Draft inventory written to: {output_path}")
    print("\nWARN NEXT STEP: Review and correct the draft before committing.")
    print("   Pay attention to: node type classifications, truncated Absätze, numeric values.")
    print(f"   Compare against {txt_path} for any missed provisions.")


# ─── CLI ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Draft a node inventory .md from a cleaned LBO .txt file."
    )
    parser.add_argument("--txt",          required=True,  help="Path to cleaned .txt file")
    parser.add_argument("--bundesland",   default="Bayern", help="e.g. Bayern")
    parser.add_argument("--lbo_code",     default="BayBO",  help="e.g. BayBO")
    parser.add_argument("--jurisdiction", default="DE-BY",  help="e.g. DE-BY")
    parser.add_argument("--version_date", default="",       help="e.g. 23. Dezember 2025")
    parser.add_argument("--source_url",   default="",       help="Official source URL")
    parser.add_argument("--output",       default="",       help="Output .md path")
    parser.add_argument("--dry_run",      action="store_true", help="Parse only, no API calls")
    parser.add_argument("--delay",        type=float, default=0.3, help="Seconds between API calls")
    parser.add_argument("--provider",     default="anthropic", choices=("anthropic", "gemini"),
                        help="LLM provider for classification (default: anthropic)")
    parser.add_argument("--gemini-model", default="", dest="gemini_model",
                        help="Gemini model ID (default: gemini-2.0-flash, or set GEMINI_MODEL in .env)")

    args = parser.parse_args()

    txt_path = Path(args.txt)
    if not txt_path.exists():
        print(f"ERR File not found: {txt_path}")
        sys.exit(1)

    output_path = Path(args.output) if args.output else \
        txt_path.parent.parent / "node inventory" / f"{args.lbo_code}_node_inventory.md"

    draft_inventory(
        txt_path=txt_path,
        bundesland=args.bundesland,
        lbo_code=args.lbo_code,
        jurisdiction=args.jurisdiction,
        version_date=args.version_date,
        source_url=args.source_url,
        output_path=output_path,
        dry_run=args.dry_run,
        rate_limit_delay=args.delay,
        provider=args.provider,
        gemini_model=args.gemini_model or None,
    )


if __name__ == "__main__":
    main()