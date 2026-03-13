"""Pydantic model for the situation object — captures the user's jurisdiction, property type, and project details."""

from pydantic import BaseModel, Field

GERMAN_STATES = [
    "Baden-Württemberg",
    "Bayern",
    "Berlin",
    "Brandenburg",
    "Bremen",
    "Hamburg",
    "Hessen",
    "Mecklenburg-Vorpommern",
    "Niedersachsen",
    "Nordrhein-Westfalen",
    "Rheinland-Pfalz",
    "Saarland",
    "Sachsen",
    "Sachsen-Anhalt",
    "Schleswig-Holstein",
    "Thüringen",
]


class Situation(BaseModel):
    jurisdiction: str = Field(
        ...,
        description="German federal state where the property is located.",
        examples=["Bayern", "Brandenburg"],
    )
    property_type: str = Field(
        ...,
        description="Type of property, e.g. Einfamilienhaus, Mehrfamilienhaus.",
        examples=["Einfamilienhaus"],
    )
    project_description: str = Field(
        ...,
        min_length=10,
        max_length=2000,
        description="Free-text description of the planned construction or modification.",
        examples=["Ich möchte eine Garage mit 6 m × 4 m im Hintergarten bauen."],
    )
    has_bplan: bool = Field(
        ...,
        description=(
            "Whether a Bebauungsplan (B-Plan) is in place for the property. "
            "Required to determine maximum confidence level of the assessment."
        ),
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "jurisdiction": "Brandenburg",
                "property_type": "Einfamilienhaus",
                "project_description": "Ich möchte eine Garage mit 6 m × 4 m im Hintergarten bauen.",
                "has_bplan": False,
            }
        }
    }
