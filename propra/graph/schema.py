"""
Knotentypen, Kantentypen und Validierungslogik für den Propra-Wissensgraphen.

Jeder Knoten muss enthalten: type, jurisdiction, source_paragraph, text
Jede Kante muss enthalten: relation, sourced_from
"""

from dataclasses import dataclass, field
from typing import Optional


# ---------------------------------------------------------------------------
# Erlaubte Knotentypen
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
    "verfahrensfreiheit",
    "verfahrensfreies_vorhaben",  # einzelne Anhang-1-Einträge
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
    "zahlenwert",            # numerische Schwellenwerte als eigene Knoten
}

# ---------------------------------------------------------------------------
# Erlaubte Kantentypen
# ---------------------------------------------------------------------------

RELATION_TYPES = {
    # Regelstruktur
    "hat_bedingung",         # Knoten → Bedingungsknoten (z. B. Schwellenwert)
    "gilt_fuer",             # Regelknoten → Anwendungsbereich
    "ausnahme_von",          # Ausnahmeknoten → Grundregel
    "ergaenzt",              # Knoten ergänzt anderen Knoten
    "verweist_auf",          # Querverweis auf anderen Paragrafen
    "wird_ueberschrieben_von", # LBO-Standard → örtliche Bauvorschrift (§74)

    # Verfahren
    "ermoeglicht_verfahren", # Vorhaben → Verfahrenstyp
    "erfordert_nachweis",    # Anforderung → Nachweistyp

    # Klassifizierung
    "klassifiziert_als",     # Vorhaben → Knotentyp (z. B. Sonderbautyp)
    "gehoert_zu_gruppe",     # Anhang-1-Eintrag → Gruppe

    # Zuständigkeit
    "zustaendig",            # Behörde → Verfahren
    "gilt_in",               # Regel → Zuständigkeit/Gebietstyp
}

# ---------------------------------------------------------------------------
# Datenklassen
# ---------------------------------------------------------------------------

@dataclass
class Knoten:
    """
    Repräsentiert einen Knoten im Propra-Wissensgraphen.

    Pflichtfelder entsprechen CLAUDE.md:
        type, jurisdiction, source_paragraph, text
    """
    id: str                          # eindeutiger Bezeichner, z. B. "BW_LBO_§6_01"
    type: str                        # muss in NODE_TYPES enthalten sein
    jurisdiction: str                # z. B. "DE-BW"
    source_paragraph: str            # z. B. "§6 Abs. 1 Nr. 2 LBO BW"
    text: str                        # Wortlaut des Gesetzes oder Regelzusammenfassung
    zahlenwert: Optional[float] = None   # numerischer Schwellenwert, falls vorhanden
    einheit: Optional[str] = None        # z. B. "m", "m²", "m³", "Jahre"
    metadaten: dict = field(default_factory=dict)  # optionale Zusatzfelder

    def validieren(self) -> None:
        """Überprüft, ob alle Pflichtfelder korrekt befüllt sind."""
        if self.type not in NODE_TYPES:
            raise ValueError(
                f"Unbekannter Knotentyp '{self.type}'. "
                f"Erlaubte Typen: {sorted(NODE_TYPES)}"
            )
        for pflichtfeld in ("id", "jurisdiction", "source_paragraph", "text"):
            if not getattr(self, pflichtfeld):
                raise ValueError(f"Pflichtfeld '{pflichtfeld}' darf nicht leer sein.")


@dataclass
class Kante:
    """
    Repräsentiert eine gerichtete Kante im Propra-Wissensgraphen.

    Pflichtfelder entsprechen CLAUDE.md:
        relation, sourced_from
    """
    von: str            # ID des Quellknotens
    nach: str           # ID des Zielknotens
    relation: str       # muss in RELATION_TYPES enthalten sein
    sourced_from: str   # z. B. "§6 Abs. 1 Nr. 2 LBO BW"
    metadaten: dict = field(default_factory=dict)

    def validieren(self) -> None:
        """Überprüft, ob alle Pflichtfelder korrekt befüllt sind."""
        if self.relation not in RELATION_TYPES:
            raise ValueError(
                f"Unbekannter Kantentyp '{self.relation}'. "
                f"Erlaubte Typen: {sorted(RELATION_TYPES)}"
            )
        for pflichtfeld in ("von", "nach", "sourced_from"):
            if not getattr(self, pflichtfeld):
                raise ValueError(f"Pflichtfeld '{pflichtfeld}' darf nicht leer sein.")
