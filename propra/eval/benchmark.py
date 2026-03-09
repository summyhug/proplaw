"""Benchmark evaluation script — defines 10 canonical queries for comparing KG vs RAG retrieval quality."""

BENCHMARK_QUESTIONS = [
    # 1. Fence height — Bavaria
    {
        "id": "BQ-01",
        "question": "Wie hoch darf ein Gartenzaun in Bayern maximal sein?",
        "jurisdiction": "Bayern",
        "category": "fence",
        "expected_verdict": "CONDITIONAL",
    },
    # 2. Fence height — Berlin
    {
        "id": "BQ-02",
        "question": "Welche Zaunhöhe ist in Berlin ohne Baugenehmigung erlaubt?",
        "jurisdiction": "Berlin",
        "category": "fence",
        "expected_verdict": "CONDITIONAL",
    },
    # 3. Window in side wall — NRW
    {
        "id": "BQ-03",
        "question": "Darf ich an der Seitenwand meines Hauses in NRW ein neues Fenster einbauen?",
        "jurisdiction": "Nordrhein-Westfalen",
        "category": "window",
        "expected_verdict": "CONDITIONAL",
    },
    # 4. Garden shed — Baden-Württemberg
    {
        "id": "BQ-04",
        "question": "Brauche ich in Baden-Württemberg eine Baugenehmigung für ein Gartenhaus?",
        "jurisdiction": "Baden-Württemberg",
        "category": "garden_structure",
        "expected_verdict": "CONDITIONAL",
    },
    # 5. Hedge height — Hamburg
    {
        "id": "BQ-05",
        "question": "Wie hoch darf eine Hecke zur Nachbargrenze in Hamburg sein?",
        "jurisdiction": "Hamburg",
        "category": "fence",
        "expected_verdict": "CONDITIONAL",
    },
    # 6. Terrace — Saxony
    {
        "id": "BQ-06",
        "question": "Ist eine überdachte Terrasse in Sachsen genehmigungspflichtig?",
        "jurisdiction": "Sachsen",
        "category": "garden_structure",
        "expected_verdict": "CONDITIONAL",
    },
    # 7. Skylight — Bavaria
    {
        "id": "BQ-07",
        "question": "Darf ich in Bayern ein Dachfenster ohne Genehmigung einbauen?",
        "jurisdiction": "Bayern",
        "category": "window",
        "expected_verdict": "CONDITIONAL",
    },
    # 8. Carport — Brandenburg
    {
        "id": "BQ-08",
        "question": "Brauche ich in Brandenburg eine Baugenehmigung für einen Carport?",
        "jurisdiction": "Brandenburg",
        "category": "garden_structure",
        "expected_verdict": "CONDITIONAL",
    },
    # 9. Pool — Hesse
    {
        "id": "BQ-09",
        "question": "Ist ein Swimmingpool im Garten in Hessen genehmigungsfrei?",
        "jurisdiction": "Hessen",
        "category": "garden_structure",
        "expected_verdict": "CONDITIONAL",
    },
    # 10. Boundary wall — Rhineland-Palatinate
    {
        "id": "BQ-10",
        "question": "Wie hoch darf eine Mauer zur Grundstücksgrenze in Rheinland-Pfalz sein?",
        "jurisdiction": "Rheinland-Pfalz",
        "category": "fence",
        "expected_verdict": "CONDITIONAL",
    },
]
