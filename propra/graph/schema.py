"""
Node types, edge types, and validation logic for the Propra knowledge graph.

Every node must contain: type, jurisdiction, source_paragraph, text
Every edge must contain: relation, sourced_from

Note: NODE_TYPES values are intentionally in German — they are German legal
taxonomy terms with no clean English equivalent. RELATION_TYPES values are in
English as they are structural graph primitives.
"""

from dataclasses import dataclass, field
from typing import Optional


# ---------------------------------------------------------------------------
# Allowed node types (German legal taxonomy — do not translate)
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Goal categories — maps user intent to relevant KG node types
# ---------------------------------------------------------------------------

GOAL_CATEGORIES: dict[str, list[str]] = {
    "zaun_einfriedung":        ["abstandsflaeche", "gestaltungsanforderung", "verfahrensfreies_vorhaben"],
    "garage_carport":          ["abstandsflaeche", "genehmigungspflicht", "verfahrensfreies_vorhaben", "stellplatzpflicht"],
    "terrasse_pergola":        ["verfahrensfreies_vorhaben", "abstandsflaeche", "freiflaechengestaltung"],
    "nebengebaeude_schuppen":  ["abstandsflaeche", "verfahrensfreies_vorhaben", "genehmigungspflicht"],
    "anbau_erweiterung":       ["abstandsflaeche", "genehmigungspflicht", "bauantrag", "standsicherheit", "brandschutzanforderung"],
    "fenster_tueren":          ["fensteroffnung", "bestandsaenderung", "brandschutzanforderung"],
    "dach_dachausbau":         ["dach", "brandschutzanforderung", "bestandsaenderung", "standsicherheit"],
    "solaranlage_pv":          ["verfahrensfreies_vorhaben", "technische_anlage", "dach"],
    "pool_teich":              ["verfahrensfreies_vorhaben", "abstandsflaeche", "grundstuecksbebauung"],
    "nutzungsaenderung":       ["genehmigungspflicht", "sonderbautyp", "bauantrag", "kenntnisgabeverfahren"],
    "barrierefreiheit":        ["barrierefreiheit", "aufzugsanlage", "sanitaerraum", "treppe"],
    "abriss":                  ["baugenehmigung", "bestandsschutz", "bestandsaenderung"],
}

# ---------------------------------------------------------------------------
# Allowed node types (German legal taxonomy — do not translate)
# ---------------------------------------------------------------------------

NODE_TYPES = {
    "anwendungsbereich",
    "begriffsbestimmung",
    "allgemeine_anforderung",
    "grundstuecksbebauung",
    "abstandsflaeche",
    "abstandsflaeche_sonderfall",
    "abstandsflaechenübertragung",
    "grundstuecksteilung",
    "freiflaechengestaltung",
    "gelaendehoehe",
    "gestaltungsanforderung",
    "baustellenanforderung",
    "standsicherheit",
    "schutzanforderung",
    "brandschutzanforderung",
    "verkehrssicherheit",
    "bauproduktzulassung",
    "brandklassifizierung",
    "tragende_wand",
    "aussenwand",
    "trennwand",
    "brandwand",
    "decke",
    "dach",
    "bestandsaenderung",
    "treppe",
    "treppenraum",
    "notwendiger_flur",
    "fensteroffnung",
    "aufzugsanlage",
    "technische_anlage",
    "aufenthaltsraum",
    "wohnung",
    "sanitaerraum",
    "stellplatzpflicht",
    "sonderbautyp",
    "barrierefreiheit",
    "gemeinschaftsanlage",
    "beteiligtenpflicht",
    "behoerdenstruktur",
    "genehmigungspflicht",
    "verfahrensfreiheit",         # permit-free status (general rule)
    "verfahrensfreies_vorhaben",  # individual Annex-1 entries
    "kenntnisgabeverfahren",
    "vereinfachtes_genehmigungsverfahren",
    "bauantrag",
    "verfahrensfrist",
    "nachbarbenachrichtigung",
    "abweichung",
    "bauvorbescheid",
    "baugenehmigung",
    "baubeginn",
    "sicherheitsleistung",
    "bauueberwachung",
    "typengenehmigung",
    "besonderes_verfahren",
    "ermaechtigungsgrundlage",
    "technische_baubestimmungen",
    "oertliche_bauvorschrift",
    "sanktion",
    "bestandsschutz",
    "schlussvorschrift",
    "zahlenwert",            # numeric threshold nodes
    "gesetz",                # root node representing a whole law (e.g. BbgBO, MBO)
}

# ---------------------------------------------------------------------------
# Allowed edge/relation types
# ---------------------------------------------------------------------------

RELATION_TYPES = {
    # Rule structure
    "has_condition",         # node → condition/threshold node
    "applies_to",            # rule node → its scope of application
    "exception_of",          # exception node → the base rule it overrides
    "supplements",           # node supplements another node
    "sub_item_of",           # list item node → parent rule (e.g. exclusion 2.2 → 2.1)
    "references",            # cross-reference to another paragraph
    "overridden_by",         # LBO standard → local bylaw (§74)

    # Procedure
    "enables_procedure",     # project type → permit procedure type
    "requires_proof",        # requirement → required proof/documentation

    # Classification
    "classified_as",         # project → category (e.g. Sonderbautyp)
    "belongs_to_group",      # Annex-1 entry → its group

    # Jurisdiction
    "responsible_for",       # authority → procedure
    "applies_in",            # rule → jurisdiction/zone type
    "state_version_of",      # BW-specific node → the MBO base node it deviates from
}

# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------

@dataclass
class Node:
    """
    Represents a node in the Propra knowledge graph.

    Required fields per CLAUDE.md: type, jurisdiction, source_paragraph, text
    """
    id: str                              # unique identifier, e.g. "BW_LBO_§6_01"
    type: str                            # must be in NODE_TYPES
    jurisdiction: str                    # e.g. "DE-BW"
    source_paragraph: str                # e.g. "§6 Abs. 1 Nr. 2 LBO BW"
    text: str                            # statutory wording or rule summary
    numeric_value: Optional[float] = None    # numeric threshold if applicable
    unit: Optional[str] = None               # e.g. "m", "m²", "m³", "Jahre"
    metadata: dict = field(default_factory=dict)

    def validate(self) -> None:
        """Checks that all required fields are correctly populated."""
        if self.type not in NODE_TYPES:
            raise ValueError(
                f"Unknown node type '{self.type}'. "
                f"Allowed types: {sorted(NODE_TYPES)}"
            )
        for required in ("id", "jurisdiction", "source_paragraph", "text"):
            if not getattr(self, required):
                raise ValueError(f"Required field '{required}' must not be empty.")


@dataclass
class Edge:
    """
    Represents a directed edge in the Propra knowledge graph.

    Required fields per CLAUDE.md: relation, sourced_from
    """
    source: str         # ID of the source node
    target: str         # ID of the target node
    relation: str       # must be in RELATION_TYPES
    sourced_from: str   # e.g. "§6 Abs. 1 Nr. 2 LBO BW"
    metadata: dict = field(default_factory=dict)

    def validate(self) -> None:
        """Checks that all required fields are correctly populated."""
        if self.relation not in RELATION_TYPES:
            raise ValueError(
                f"Unknown relation type '{self.relation}'. "
                f"Allowed types: {sorted(RELATION_TYPES)}"
            )
        for required in ("source", "target", "sourced_from"):
            if not getattr(self, required):
                raise ValueError(f"Required field '{required}' must not be empty.")
