"""POST /assess endpoint — triggers FAISS retrieval and LLM synthesis, returns regulatory assessment."""

import json
import os
import sys
from pathlib import Path

import anthropic
from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException, status

from propra.graph.kg_retriever import get_related_chunks
from propra.schemas.assessment import AssessmentResponse, ClassificationResult
from propra.schemas.situation import Situation

# ── path setup ────────────────────────────────────────────────────────────────
# rag.py lives in propra/retrieval/ and uses __file__-relative paths internally.
# Add its directory to sys.path so it resolves correctly as a standalone module.
_RETRIEVAL_DIR = Path(__file__).resolve().parent.parent / "retrieval"
if str(_RETRIEVAL_DIR) not in sys.path:
    sys.path.insert(0, str(_RETRIEVAL_DIR))

import rag  # noqa: E402
import kg_query  # noqa: E402

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

# ── prompts ───────────────────────────────────────────────────────────────────
_PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"
_PROMPT_PATH = _PROMPTS_DIR / "assess.txt"
_CLASSIFY_PROMPT_PATH = _PROMPTS_DIR / "classify_goal.txt"


def _load_system_prompt() -> str:
    """Load the assessment synthesis prompt from file."""
    try:
        return _PROMPT_PATH.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise RuntimeError(f"Prompt file not found: {_PROMPT_PATH}") from exc


def _load_classify_prompt() -> str:
    """Load the goal classification prompt from file."""
    try:
        return _CLASSIFY_PROMPT_PATH.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise RuntimeError(f"Prompt file not found: {_CLASSIFY_PROMPT_PATH}") from exc


_SYSTEM_PROMPT = _load_system_prompt()
_CLASSIFY_PROMPT = _load_classify_prompt()

# ── router ────────────────────────────────────────────────────────────────────
router = APIRouter()


def _classify_goal(project_description: str) -> ClassificationResult | None:
    """
    Call the LLM to classify the user's project into a goal category.

    Returns a ClassificationResult on success, or None if the LLM call fails
    or returns unparseable output. Failures are non-fatal — the assess pipeline
    continues without classification.
    """
    try:
        response = _get_llm().messages.create(
            model="claude-sonnet-4-6",
            max_tokens=200,
            system=_CLASSIFY_PROMPT,
            messages=[{"role": "user", "content": f"Vorhaben: {project_description}"}],
        )
        text = response.content[0].text.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
        data = json.loads(text)
        return ClassificationResult(**data)
    except Exception:
        return None


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
      2. LLM goal classification → category + node types (non-fatal if it fails).
      3. FAISS retrieval → top-5 document chunks (query augmented with node types).
      4. Anthropic API call with prompts/assess.txt → JSON AssessmentResponse.
      5. Validate response against AssessmentResponse schema.
    """
    # 1. Map jurisdiction label to ISO code (None = search all jurisdictions)
    iso_code = _LABEL_TO_CODE.get(situation.jurisdiction)

    # 2. Classify the goal (use frontend-provided category or call LLM classifier)
    if situation.goal_category:
        classification = ClassificationResult(
            goal_category=situation.goal_category,
            confidence=situation.goal_confidence or "LOW",
            parameters={},
        )
    else:
        classification = _classify_goal(situation.project_description)

    node_types = kg_query.query_by_category(classification.goal_category) if classification else []

    # 3. Retrieve relevant chunks (query augmented with node type hints)
    try:
        chunks = _retriever.retrieve(
            query=situation.project_description,
            k=5,
            jurisdiction=iso_code,
            node_types=node_types or None,
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
            goal_category=classification.goal_category if classification else None,
        )

    # 3b. KG enrichment (skipped when retrieval_mode == "rag")
    kg_chunks = get_related_chunks(chunks) if situation.retrieval_mode == "graphrag" else []
    all_chunks = chunks + kg_chunks

    # 4. Synthesise with Anthropic
    context = _build_context(all_chunks)
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

    # 5. Parse and validate JSON response
    try:
        text = raw_text.strip()
        # Strip markdown code fences if the model wrapped the JSON
        if text.startswith("```"):
            text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
        data = json.loads(text)
        # has_bplan and goal_category are sourced from the request, not the LLM
        data["has_bplan"] = situation.has_bplan
        data["goal_category"] = classification.goal_category if classification else None
        data["kg_nodes_used"] = [c["kg_node_id"] for c in kg_chunks]
        data["retrieval_mode"] = situation.retrieval_mode
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
