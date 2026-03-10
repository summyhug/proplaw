"""
Domain edges for fence and boundary regulations in Baden-Württemberg.

Encodes the legal relationships between:
  - BW §5  — Abstandsflächen (base setback rules)
  - BW §6  — Abstandsflächen in Sonderfällen (small structures at boundary)
  - BW §11 — Gestaltung (design requirements)
  - BW §74 — Örtliche Bauvorschriften (local bylaw overrides)
  - BW §50 — Verfahrensfreie Vorhaben (procedure-free framework)
  - Anhang 1 Gruppe 7 — Einfriedungen + Stützmauern (permit-free fences)

Where BW deviates from MBO, a `state_version_of` edge points to the MBO base node.
This module only exports edges — graph I/O is handled by build_graph.py.
"""

from propra.graph.schema import Edge


def edges() -> list[Edge]:
    """
    Returns all BW-level fence/boundary domain edges.

    Grouped by legal theme for readability and traceability.
    """
    return [

        # ---------------------------------------------------------------
        # BW §6 Abs. 1 special cases — exception_of BW §5 Abs. 1
        # These structures may be built at the boundary without setback.
        # ---------------------------------------------------------------
        Edge("BW_LBO_§6-01", "BW_LBO_§5_5.1", "exception_of",
             "§6 Abs. 1 Nr. 1 LBO BW",
             metadata={"reasoning": "Structures ≤1m wall height are exempt from the §5 setback requirement."}),

        Edge("BW_LBO_§6-02", "BW_LBO_§5_5.1", "exception_of",
             "§6 Abs. 1 Nr. 2 LBO BW",
             metadata={"reasoning": "Garages/greenhouses ≤3m wall height and ≤25m² wall area need no setback."}),

        Edge("BW_LBO_§6-03", "BW_LBO_§5_5.1", "exception_of",
             "§6 Abs. 1 Nr. 3 LBO BW",
             metadata={"reasoning": "Non-building structures ≤2.5m high or ≤25m² wall area need no setback."}),

        Edge("BW_LBO_§6-04", "BW_LBO_§5_5.1", "exception_of",
             "§6 Abs. 1 Nr. 4 LBO BW",
             metadata={"reasoning": "Agricultural greenhouses maintaining ≥1m distance need no setback."}),

        # ---------------------------------------------------------------
        # BW §5 deviates from MBO §6: minimum setback is 2.5m, not 3m.
        # ---------------------------------------------------------------
        Edge("BW_LBO_§5_5.25", "MBO_§6_6.11", "state_version_of",
             "§5 Abs. 7 LBO BW vs §6 Abs. 5 MBO",
             metadata={"reasoning": "BW sets minimum setback at 2.5m (walls ≤5m: 2m); MBO requires 3m minimum."}),

        # ---------------------------------------------------------------
        # BW §6 numeric thresholds — has_condition
        # ---------------------------------------------------------------
        Edge("BW_LBO_§6-02", "BW_LBO_§6_ZW_max_wandhoehe_nr_2", "has_condition",
             "§6 Abs. 1 Nr. 2 LBO BW",
             metadata={"reasoning": "§6-02 exemption applies only if wall height ≤ 3m."}),

        Edge("BW_LBO_§6-02", "BW_LBO_§6_ZW_max_wandflaeche_nr_2", "has_condition",
             "§6 Abs. 1 Nr. 2 LBO BW",
             metadata={"reasoning": "§6-02 exemption applies only if wall area ≤ 25m²."}),

        Edge("BW_LBO_§6_6.6", "BW_LBO_§6_ZW_max_grenzbebauung_je_nachbar", "has_condition",
             "§6 Abs. 1 LBO BW",
             metadata={"reasoning": "Boundary construction under §6-02 must not exceed 9m per neighbour boundary."}),

        Edge("BW_LBO_§6_6.6", "BW_LBO_§6_ZW_max_grenzbebauung_gesamt", "has_condition",
             "§6 Abs. 1 LBO BW",
             metadata={"reasoning": "Total boundary construction under §6-02 must not exceed 15m across all boundaries."}),

        Edge("BW_LBO_§6_6.8", "BW_LBO_§6_ZW_min_abstand_freiwillig", "has_condition",
             "§6 Abs. 2 LBO BW",
             metadata={"reasoning": "If §6 structures voluntarily maintain a setback, it must be at least 0.5m."}),

        # ---------------------------------------------------------------
        # BW §6 supplementary rules — supplements
        # ---------------------------------------------------------------
        Edge("BW_LBO_§6_6.5", "BW_LBO_§6-02", "supplements",
             "§6 Abs. 1 Nr. 2 LBO BW",
             metadata={"reasoning": "Specifies that the highest ground level is used for wall height calculation under Nr. 2."}),

        Edge("BW_LBO_§6_6.6", "BW_LBO_§6-02", "supplements",
             "§6 Abs. 1 LBO BW",
             metadata={"reasoning": "Adds boundary length limits (9m per neighbour, 15m total) for Nr. 2 structures."}),

        Edge("BW_LBO_§6_6.7", "BW_LBO_§6-02", "supplements",
             "§6 Abs. 1 Nr. 2 LBO BW",
             metadata={"reasoning": "Roof use for other purposes does not disqualify a structure from the Nr. 2 exemption."}),

        Edge("BW_LBO_§6_6.8", "BW_LBO_§6-01", "supplements",
             "§6 Abs. 2 LBO BW",
             metadata={"reasoning": "Voluntary setback rule applies to all §6 Abs. 1 structures, including Nr. 1."}),

        Edge("BW_LBO_§6_6.8", "BW_LBO_§6-02", "supplements",
             "§6 Abs. 2 LBO BW",
             metadata={"reasoning": "Voluntary setback minimum of 0.5m also applies to Nr. 2 structures."}),

        Edge("BW_LBO_§6_6.9", "BW_LBO_§6-01", "supplements",
             "§6 Abs. 3 LBO BW",
             metadata={"reasoning": "Reduced setbacks below §5 minimums are permissible under the conditions of §6 Abs. 3."}),

        Edge("BW_LBO_§6_6.10", "BW_LBO_§6_6.9", "supplements",
             "§6 Abs. 3 LBO BW",
             metadata={"reasoning": "Adds the condition that daylight, ventilation, fire protection, and neighbour interests must be met."}),

        # ---------------------------------------------------------------
        # Annex 1 Group 7 — permit-free fences and retaining walls
        # ---------------------------------------------------------------
        Edge("BW_LBO_A1-07a", "BW_LBO_§50_50.1", "enables_procedure",
             "Anhang 1 Nr. 7a zu §50 Abs. 1 LBO BW",
             metadata={"reasoning": "Einfriedungen im Innenbereich are permit-free under §50 Abs. 1."}),

        Edge("BW_LBO_A1-07b", "BW_LBO_§50_50.1", "enables_procedure",
             "Anhang 1 Nr. 7b zu §50 Abs. 1 LBO BW",
             metadata={"reasoning": "Open fences without foundation in Außenbereich for agriculture are permit-free."}),

        Edge("BW_LBO_A1-07c", "BW_LBO_§50_50.1", "enables_procedure",
             "Anhang 1 Nr. 7c zu §50 Abs. 1 LBO BW",
             metadata={"reasoning": "Retaining walls up to 2m are permit-free under §50 Abs. 1."}),

        # Permit-free does NOT mean material law is waived
        Edge("BW_LBO_§50_50.2", "BW_LBO_§50_50.1", "supplements",
             "§50 Abs. 2 LBO BW",
             metadata={"reasoning": "Permit-free status does not exempt from material requirements (setback, fire safety etc.)."}),

        Edge("BW_LBO_§50_50.3", "BW_LBO_§50_50.1", "supplements",
             "§50 Abs. 1 LBO BW",
             metadata={"reasoning": "§5 setback rules and all other material LBO requirements still apply to permit-free structures."}),

        # Fences as non-building structures subject to §6 Abs. 1 Nr. 3
        Edge("BW_LBO_A1-07a", "BW_LBO_§6-03", "references",
             "§6 Abs. 1 Nr. 3 LBO BW",
             metadata={"reasoning": "Fences (Einfriedungen) are non-building structures; §6-03 governs their setback exemption."}),

        # BW Annex 1 vs MBO §61 — same permit-free result, different structure
        Edge("BW_LBO_A1-07a", "MBO_§61-01", "state_version_of",
             "Anhang 1 Nr. 7a LBO BW vs §61 Abs. 1 Nr. 7a MBO",
             metadata={"reasoning": "BW encodes permit-free fences in Annex 1; MBO uses §61 directly. Same legal outcome."}),

        # ---------------------------------------------------------------
        # §74 local bylaw overrides — BW-specific, no MBO equivalent
        # ---------------------------------------------------------------
        Edge("BW_LBO_§5_5.1", "BW_LBO_§74_74.1", "overridden_by",
             "§74 Abs. 1 LBO BW",
             metadata={"reasoning": "Local bylaws under §74 can set stricter or different setback rules than §5."}),

        Edge("BW_LBO_§6-01", "BW_LBO_§74_74.1", "overridden_by",
             "§74 Abs. 1 LBO BW",
             metadata={"reasoning": "Local bylaws can regulate boundary structures and override §6 special cases."}),

        Edge("BW_LBO_A1-07a", "BW_LBO_§74_74.1", "overridden_by",
             "§74 Abs. 1 LBO BW",
             metadata={"reasoning": "§74 explicitly names Einfriedungen as subject to local bylaw regulation."}),

        Edge("BW_LBO_§74_74.2", "BW_LBO_§74_74.1", "supplements",
             "§74 LBO BW",
             metadata={"reasoning": "§74 Abs. 2 clarifies that local bylaws may deviate from LBO standards."}),

        # ---------------------------------------------------------------
        # §11 design requirements apply to fences
        # ---------------------------------------------------------------
        Edge("BW_LBO_§11_11.1", "BW_LBO_A1-07a", "applies_to",
             "§11 Abs. 1 LBO BW",
             metadata={"reasoning": "General design requirement (harmony with surroundings) applies to fences."}),

        Edge("BW_LBO_§11_11.1", "BW_LBO_A1-07c", "applies_to",
             "§11 Abs. 1 LBO BW",
             metadata={"reasoning": "General design requirement applies to retaining walls as structural elements."}),

        Edge("BW_LBO_§11_11.2", "BW_LBO_§11_11.1", "supplements",
             "§11 Abs. 2 LBO BW",
             metadata={"reasoning": "§11 Abs. 2 specifies criteria: form, scale, material, colour must suit surroundings."}),

        # ---------------------------------------------------------------
        # §5 internal structure — base setback rule and its clarifications
        # ---------------------------------------------------------------
        Edge("BW_LBO_§5_5.2", "BW_LBO_§5_5.1", "supplements",
             "§5 Abs. 1 LBO BW",
             metadata={"reasoning": "Exception: no setback required if planning law requires building at the boundary."}),

        Edge("BW_LBO_§5_5.3", "BW_LBO_§5_5.1", "supplements",
             "§5 Abs. 1 LBO BW",
             metadata={"reasoning": "Exception: no setback if permitted to build at boundary and neighbour land secured."}),

        Edge("BW_LBO_§5_5.4", "BW_LBO_§5_5.3", "supplements",
             "§5 Abs. 1 LBO BW",
             metadata={"reasoning": "Clarifies when public-law security (Baulast) is not required for the §5 Abs. 1 Nr. 2 exception."}),

        Edge("BW_LBO_§5_5.5", "BW_LBO_§5_5.1", "supplements",
             "§5 Abs. 2 LBO BW",
             metadata={"reasoning": "Setback areas must lie on the owner's own land."}),

        Edge("BW_LBO_§5_5.6", "BW_LBO_§5_5.5", "supplements",
             "§5 Abs. 2 LBO BW",
             metadata={"reasoning": "Exception: setback may extend onto public roads, green spaces, or water areas."}),

        Edge("BW_LBO_§5_5.7", "BW_LBO_§5_5.1", "supplements",
             "§5 Abs. 2 LBO BW",
             metadata={"reasoning": "Setback areas of different buildings may not overlap (except walls >75° apart)."}),

        Edge("BW_LBO_§5_5.8", "BW_LBO_§5_5.1", "supplements",
             "§5 Abs. 4 LBO BW",
             metadata={"reasoning": "Defines wall height as the measure from ground level to roof skin or top of wall."}),

        Edge("BW_LBO_§5_5.9", "BW_LBO_§5_5.8", "supplements",
             "§5 Abs. 4 LBO BW",
             metadata={"reasoning": "For sloped terrain, the averaged wall height across building corners is used."}),

        Edge("BW_LBO_§5_5.10", "BW_LBO_§5_5.8", "supplements",
             "§5 Abs. 4 LBO BW",
             metadata={"reasoning": "Actual post-construction ground level is the reference, unless manipulated to reduce setback."}),

        Edge("BW_LBO_§5_5.11", "BW_LBO_§5_5.8", "supplements",
             "§5 Abs. 4 LBO BW",
             metadata={"reasoning": "Roofs or dormers with inclination >70° are fully counted in wall height."}),

        Edge("BW_LBO_§5_5.12", "BW_LBO_§5_5.8", "supplements",
             "§5 Abs. 4 LBO BW",
             metadata={"reasoning": "Roofs or dormers with inclination >45° are counted at one quarter."}),

        Edge("BW_LBO_§5_5.13", "BW_LBO_§5_5.8", "supplements",
             "§5 Abs. 4 LBO BW",
             metadata={"reasoning": "Gable wall area is counted at one quarter from the eaves line upward."}),

        Edge("BW_LBO_§5_5.15", "BW_LBO_§5_5.8", "supplements",
             "§5 Abs. 4 LBO BW",
             metadata={"reasoning": "Additions of up to 2 storeys for housing on existing buildings are not added to wall height."}),

        Edge("BW_LBO_§5_5.16", "BW_LBO_§5_5.8", "supplements",
             "§5 Abs. 4 LBO BW",
             metadata={"reasoning": "Solar panels up to 1.5m height on roofs are not counted in wall height."}),

        Edge("BW_LBO_§5_5.17", "BW_LBO_§5_5.8", "supplements",
             "§5 Abs. 4 LBO BW",
             metadata={"reasoning": "Roof insulation up to 0.3m thickness is not counted in wall height."}),

        Edge("BW_LBO_§5_5.18", "BW_LBO_§5_5.1", "supplements",
             "§5 Abs. 6 LBO BW",
             metadata={"reasoning": "Minor projections (cornices, canopies) projecting ≤1.5m are ignored in setback calculation."}),

        Edge("BW_LBO_§5_5.19", "BW_LBO_§5_5.1", "supplements",
             "§5 Abs. 6 LBO BW",
             metadata={"reasoning": "Bay windows, balconies etc ≤5m wide and ≤1.5m projection and ≥2m from boundary are ignored."}),

        Edge("BW_LBO_§5_5.20", "BW_LBO_§5_5.19", "supplements",
             "§5 Abs. 6 LBO BW",
             metadata={"reasoning": "Retrofitted thermal insulation ≤0.3m projection is ignored, same as bay windows."}),

        Edge("BW_LBO_§5_5.21", "BW_LBO_§5_5.19", "supplements",
             "§5 Abs. 6 LBO BW",
             metadata={"reasoning": "Retrofitted solar installations follow same exception as thermal insulation."}),

        Edge("BW_LBO_§5_5.22", "BW_LBO_§5_5.1", "supplements",
             "§5 Abs. 7 LBO BW",
             metadata={"reasoning": "Standard setback depth: 0.4 × wall height (applies generally)."}),

        Edge("BW_LBO_§5_5.23", "BW_LBO_§5_5.22", "supplements",
             "§5 Abs. 7 LBO BW",
             metadata={"reasoning": "Reduced depth of 0.2 × wall height in core areas, village zones, and urban zones."}),

        Edge("BW_LBO_§5_5.24", "BW_LBO_§5_5.22", "supplements",
             "§5 Abs. 7 LBO BW",
             metadata={"reasoning": "Reduced depth of 0.125 × wall height in industrial and commercial zones."}),

        Edge("BW_LBO_§5_5.25", "BW_LBO_§5_5.22", "supplements",
             "§5 Abs. 7 LBO BW",
             metadata={"reasoning": "Minimum setback depth is 2.5m (or 2m for walls ≤5m wide)."}),
    ]
