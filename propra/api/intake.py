"""POST /intake endpoint — receives and validates the user's situation form submission."""

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from propra.schemas.situation import Situation

router = APIRouter()


@router.post("/intake")
def intake(situation: Situation) -> JSONResponse:
    """Validate and acknowledge the user's situation.

    Returns the validated situation so the frontend can pass it directly to /assess.
    No persistence yet — this will be extended once a database layer is added.
    """
    return JSONResponse(
        status_code=200,
        content={
            "situation": situation.model_dump(),
            "user_message": (
                "Ihre Angaben wurden erfasst. "
                "Sie können jetzt die Prüfung starten."
            ),
        },
    )
