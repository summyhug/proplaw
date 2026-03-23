"""POST /assess endpoint — triggers FAISS retrieval and LLM synthesis, returns regulatory assessment."""

import json
import os
import sys
from pathlib import Path

import anthropic
from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException, status

from propra.schemas.assessment import AssessmentResponse, CitedSource
from propra.schemas.situation import Situation

# ── path setup ────────────────────────────────────────────────────────────────
# rag.py lives in propra/retrieval/ and uses __file__-relative paths internally.
# Add its directory to sys.path so it resolves correctly as a standalone module.
_RETRIEVAL_DIR = Path(__file__).resolve().parent.parent / "retrieval"
if str(_RETRIEVAL_DIR) not in sys.path:
    sys.path.insert(0, str(_RETRIEVAL_DIR))

import rag  # noqa: E402

# ── env ───────────────────────────────────────────────────────────────────────
load_dotenv()

# ── singletons ────────────────────────────────────────────────────────────────
_retriever = rag.Retriever()
_llm: anthropic.Anthropic | None = None


def _get_llm() -> anthropic.Anthropic:
    """Return the Anthropic client, initialising it on first call."""
    global _llm
    if _llm is None:
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise RuntimeError("ANTHROPIC_API_KEY not set in .env")
        _llm = anthropic.Anthropic(api_key=api_key)
    return _llm

# ── jurisdiction label → ISO 3166-2 code reverse map ─────────────────────────
_LABEL_TO_CODE: dict[str, str] = {
    v["label"]: v["code"] for v in rag.JURISDICTION_MAP.values()
}

# ── prompt ────────────────────────────────────────────────────────────────────
_PROMPT_PATH = Path(__file__).resolve().parent.parent / "prompts" / "assess.txt"


def _load_system_prompt() -> str:
    """Load the assessment synthesis prompt from file."""
    try:
        return _PROMPT_PATH.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise RuntimeError(f"Prompt file not found: {_PROMPT_PATH}") from exc


_SYSTEM_PROMPT = _load_system_prompt()

# ── router ────────────────────────────────────────────────────────────────────
router = APIRouter()


def _build_context(chunks: list[dict]) -> str:
    """Format retrieved chunks into a numbered context block for the LLM."""
    parts = []
    for i, c in enumerate(chunks, 1):
        parts.append(
            f"[{i}] {c['jurisdiction_label']} ({c['jurisdiction']}) · {c['source_paragraph']}\n{c['text']}"
        )
    return "\n\n".join(parts)


@router.post("/assess", response_model=AssessmentResponse)
def assess(situation: Situation) -> AssessmentResponse:
    """Run a regulatory assessment for the user's situation.

    Pipeline:
      1. Map jurisdiction label → ISO 3166-2 code for FAISS filter.
      2. FAISS retrieval → top-5 document chunks.
      3. Anthropic API call with prompts/assess.txt → JSON AssessmentResponse.
      4. Validate response against AssessmentResponse schema.
    """
    # 1. Map jurisdiction label to ISO code (None = search all jurisdictions)
    iso_code = _LABEL_TO_CODE.get(situation.jurisdiction)

    # 2. Retrieve relevant chunks
    try:
        chunks = _retriever.retrieve(
            query=situation.project_description,
            k=5,
            jurisdiction=iso_code,
        )
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "message": str(exc),
                "user_message": (
                    "Der Rechtsindex ist noch nicht verfügbar. "
                    "Bitte versuchen Sie es später erneut."
                ),
            },
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "message": f"Retrieval error: {exc}",
                "user_message": "Bei der Suche ist ein Fehler aufgetreten.",
            },
        ) from exc

    if not chunks:
        return AssessmentResponse(
            verdict="NOT_ALLOWED",
            confidence="LOW",
            explanation=(
                "Für Ihr Vorhaben konnten keine relevanten Gesetzesauszüge gefunden werden. "
                "Bitte beschreiben Sie das Vorhaben genauer."
            ),
            cited_sources=[],
            next_action=(
                "Wenden Sie sich an die Bauaufsichtsbehörde Ihrer Gemeinde für eine "
                "persönliche Beratung."
            ),
            has_bplan=situation.has_bplan,
        )

    # 3. Synthesise with Anthropic
    context = _build_context(chunks)
    user_message = (
        f"Situation:\n"
        f"- Bundesland: {situation.jurisdiction}\n"
        f"- Grundstückstyp: {situation.property_type}\n"
        f"- Vorhaben: {situation.project_description}\n"
        f"- Bebauungsplan vorhanden: {'Ja' if situation.has_bplan else 'Nein'}\n\n"
        f"Gesetzesauszüge:\n{context}"
    )

    try:
        response = _get_llm().messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1500,
            system=_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_message}],
        )
        raw_text = response.content[0].text
    except anthropic.APIError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={
                "message": f"LLM error: {exc}",
                "user_message": "Die KI-Analyse ist momentan nicht verfügbar.",
            },
        ) from exc

    # 4. Parse and validate JSON response
    try:
        text = raw_text.strip()
        # Strip markdown code fences if the model wrapped the JSON
        if text.startswith("```"):
            text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
        data = json.loads(text)
        # has_bplan is sourced from the request, not the LLM
        data["has_bplan"] = situation.has_bplan
        # Belt-and-suspenders: downgrade HIGH → MEDIUM when no B-Plan
        if data.get("confidence") == "HIGH" and not situation.has_bplan:
            data["confidence"] = "MEDIUM"
        result = AssessmentResponse(**data)
    except (json.JSONDecodeError, ValueError, KeyError) as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={
                "message": f"LLM response parse error: {exc}",
                "user_message": "Die Antwort der KI konnte nicht verarbeitet werden.",
            },
        ) from exc

    return result
