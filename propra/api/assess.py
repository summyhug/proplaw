"""POST /assess endpoint — triggers retrieval and LLM synthesis, returns regulatory assessment."""

from fastapi import APIRouter, HTTPException, status

from propra.schemas.assessment import AssessmentResponse
from propra.schemas.situation import Situation

router = APIRouter()


@router.post("/assess", response_model=AssessmentResponse)
def assess(situation: Situation) -> AssessmentResponse:
    """Run a regulatory assessment for the user's situation.

    Pipeline (once wired):
      1. propra.retrieval.kg_query.retrieve(situation)  → relevant KG nodes/edges
      2. propra.retrieval.rag.retrieve(situation)       → relevant document chunks
      3. Anthropic API call with prompts/assess.txt     → AssessmentResponse JSON
      4. Validate response against AssessmentResponse schema (incl. confidence guard)

    Currently raises 503 until the retrieval and LLM layers are implemented.
    The request schema is fully validated so the frontend can integrate against this
    endpoint immediately.
    """
    # TODO: replace with propra.retrieval.kg_query.retrieve(situation)
    _kg_results: list = []

    # TODO: replace with propra.retrieval.rag.retrieve(situation)
    _rag_chunks: list = []

    # TODO: call Anthropic API with prompts/assess.txt once retrieval is wired
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="Retrieval and LLM integration not yet implemented.",
        headers={"X-User-Message": (
            "Die Prüfung steht noch nicht zur Verfügung. "
            "Bitte versuchen Sie es später erneut."
        )},
    )
