"""Pydantic model for the assessment response — verdict, confidence, explanation, cited sources, and next action."""

from typing import Literal

from pydantic import BaseModel, Field, model_validator


class CitedSource(BaseModel):
    paragraph: str = Field(
        ...,
        description="Paragraph reference, e.g. '§ 6 Abs. 5'.",
        examples=["§ 6 Abs. 5"],
    )
    regulation_name: str = Field(
        ...,
        description="Full name of the regulation.",
        examples=["Brandenburgische Bauordnung (BbgBO)"],
    )
    jurisdiction: str = Field(
        ...,
        description="Jurisdiction this source applies to.",
        examples=["Brandenburg"],
    )
    excerpt: str | None = Field(
        default=None,
        description="One or two sentences quoted directly from the law text.",
    )


class AssessmentResponse(BaseModel):
    verdict: Literal["ALLOWED", "CONDITIONAL", "NOT_ALLOWED"] = Field(
        ...,
        description="Whether the project is permitted under the applicable regulations.",
    )
    confidence: Literal["LOW", "MEDIUM", "HIGH"] = Field(
        ...,
        description=(
            "Confidence level of the assessment. "
            "Cannot be HIGH when no B-Plan data is present."
        ),
    )
    explanation: str = Field(
        ...,
        description="Plain-German explanation of the regulatory situation.",
    )
    cited_sources: list[CitedSource] = Field(
        ...,
        description="Paragraphs and regulations the assessment is based on.",
    )
    next_action: str = Field(
        ...,
        description="Plain-German concrete next step for the user.",
    )
    has_bplan: bool = Field(
        ...,
        description="Whether a B-Plan was present — used to validate confidence ceiling.",
    )

    @model_validator(mode="after")
    def confidence_requires_bplan(self) -> "AssessmentResponse":
        if self.confidence == "HIGH" and not self.has_bplan:
            raise ValueError(
                "Confidence cannot be HIGH when no B-Plan data is present in the corpus."
            )
        return self

    model_config = {
        "json_schema_extra": {
            "example": {
                "verdict": "CONDITIONAL",
                "confidence": "MEDIUM",
                "explanation": (
                    "Eine Garage bis 50 m² ist in Brandenburg grundsätzlich zulässig, "
                    "sofern die Abstandsflächen nach § 6 BbgBO eingehalten werden."
                ),
                "cited_sources": [
                    {
                        "paragraph": "§ 6 Abs. 5",
                        "regulation_name": "Brandenburgische Bauordnung (BbgBO)",
                        "jurisdiction": "Brandenburg",
                    }
                ],
                "next_action": (
                    "Prüfen Sie den Abstand zur Grundstücksgrenze und beantragen Sie "
                    "ggf. eine Baugenehmigung bei Ihrer Gemeinde."
                ),
                "has_bplan": False,
            }
        }
    }
