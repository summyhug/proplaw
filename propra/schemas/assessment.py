"""Pydantic model for the assessment response — verdict, confidence, explanation, cited sources, and next action."""

from typing import Literal

from pydantic import BaseModel, Field, model_validator


class ClassificationResult(BaseModel):
    """Result of the goal classification step — what type of project the user is describing."""

    goal_category: str = Field(
        ...,
        description="One of the 12 goal categories defined in GOAL_CATEGORIES (e.g. 'fence', 'garage').",
    )
    confidence: Literal["LOW", "MEDIUM", "HIGH"] = Field(
        ...,
        description="How confidently the classifier matched the description to this category.",
    )
    parameters: dict = Field(
        default_factory=dict,
        description="Extracted numeric parameters, e.g. {'height_m': 1.8, 'area_m2': 25}.",
    )


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
    goal_category: str | None = Field(
        default=None,
        description="Classified goal category for this request (e.g. 'fence'). None if classification failed.",
    )
    retrieval_mode: Literal["rag", "graphrag"] = Field(
        ...,
        description="Retrieval mode that was actually used for this assessment.",
    )
    kg_status: Literal[
        "not_requested",
        "graph_unavailable",
        "no_seed_match",
        "no_related_nodes",
        "used",
    ] = Field(
        ...,
        description=(
            "Debug status for the KG enrichment step. "
            "'used' means graph context was added; the other values explain why it was not."
        ),
    )
    kg_nodes_used: list[str] = Field(
        default_factory=list,
        description="Knowledge-graph node IDs added to the context for this assessment.",
    )
    kg_seed_paragraphs: list[str] = Field(
        default_factory=list,
        description="FAISS source paragraphs that successfully matched KG seed nodes.",
    )
    kg_message: str | None = Field(
        default=None,
        description="Human-readable debug note for the KG enrichment step.",
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
                "goal_category": "garage",
                "retrieval_mode": "graphrag",
                "kg_status": "used",
                "kg_nodes_used": ["BBGBO_6_9"],
                "kg_seed_paragraphs": ["§ 6"],
                "kg_message": "2 KG nodes were added from 1 FAISS seed paragraph.",
            }
        }
    }
