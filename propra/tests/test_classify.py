"""Tests for the goal classification step within the POST /assess endpoint."""

from unittest.mock import MagicMock, patch

import anthropic
from fastapi.testclient import TestClient


# ── helpers ───────────────────────────────────────────────────────────────────

_SAMPLE_CHUNKS = [
    {
        "chunk_id": "DE-BB_§_6_0",
        "jurisdiction": "DE-BB",
        "jurisdiction_label": "Brandenburg",
        "source_file": "BbgBO",
        "source_paragraph": "§ 6",
        "text": "Einfriedungen bis 1,80 m Höhe sind in Brandenburg verfahrensfrei.",
        "score": 0.85,
    }
]

_CLASSIFY_JSON = '{"goal_category": "zaun_einfriedung", "confidence": "HIGH", "parameters": {"height_m": 1.8}}'

_ASSESS_JSON = (
    '{"verdict": "ALLOWED", "confidence": "MEDIUM",'
    ' "explanation": "Ein Zaun bis 1,80 m ist in Brandenburg verfahrensfrei zulässig.",'
    ' "cited_sources": [{"paragraph": "§ 6", "regulation_name": "BbgBO", "jurisdiction": "Brandenburg",'
    ' "excerpt": "Einfriedungen bis 1,80 m Höhe sind verfahrensfrei."}],'
    ' "next_action": "Kein Bauantrag nötig — prüfen Sie die genaue Höhe."}'
)


def _make_llm_response(text: str) -> MagicMock:
    msg = MagicMock()
    msg.content = [MagicMock(text=text)]
    return msg


def _mock_llm_sequence(*texts: str) -> MagicMock:
    """Return a mock LLM client whose successive messages.create calls return each text in order."""
    mock_llm = MagicMock(spec=anthropic.Anthropic)
    mock_llm.messages.create.side_effect = [_make_llm_response(t) for t in texts]
    return mock_llm


# ── happy path — backend classification ───────────────────────────────────────


def test_classify_sets_goal_category_in_response(client: TestClient, valid_situation: dict) -> None:
    """When classification succeeds, goal_category is returned in the AssessmentResponse."""
    mock_llm = _mock_llm_sequence(_CLASSIFY_JSON, _ASSESS_JSON)

    with (
        patch("propra.api.assess._retriever") as mock_retriever,
        patch("propra.api.assess._llm", mock_llm),
    ):
        mock_retriever.retrieve.return_value = _SAMPLE_CHUNKS
        payload = {**valid_situation, "project_description": "Ich möchte einen Zaun bauen."}
        response = client.post("/api/assess", json=payload)

    assert response.status_code == 200
    assert response.json()["goal_category"] == "zaun_einfriedung"


def test_classify_node_types_passed_to_retriever(client: TestClient, valid_situation: dict) -> None:
    """node_types from the fence category are forwarded to the retriever."""
    mock_llm = _mock_llm_sequence(_CLASSIFY_JSON, _ASSESS_JSON)

    with (
        patch("propra.api.assess._retriever") as mock_retriever,
        patch("propra.api.assess._llm", mock_llm),
    ):
        mock_retriever.retrieve.return_value = _SAMPLE_CHUNKS
        payload = {**valid_situation, "project_description": "Ich möchte einen Zaun bauen."}
        client.post("/api/assess", json=payload)

    call_kwargs = mock_retriever.retrieve.call_args.kwargs
    assert call_kwargs.get("node_types") is not None
    assert "abstandsflaeche" in call_kwargs["node_types"]


def test_classify_uses_frontend_category_when_provided(client: TestClient, valid_situation: dict) -> None:
    """When goal_category is sent by the frontend, the backend skips the classification LLM call."""
    mock_llm = MagicMock(spec=anthropic.Anthropic)
    mock_llm.messages.create.return_value = _make_llm_response(_ASSESS_JSON)

    with (
        patch("propra.api.assess._retriever") as mock_retriever,
        patch("propra.api.assess._llm", mock_llm),
    ):
        mock_retriever.retrieve.return_value = _SAMPLE_CHUNKS
        payload = {
            **valid_situation,
            "project_description": "Ich möchte einen Zaun bauen.",
            "goal_category": "zaun_einfriedung",
            "goal_confidence": "HIGH",
        }
        response = client.post("/api/assess", json=payload)

    # Only one LLM call (assessment), not two (classify + assessment)
    assert mock_llm.messages.create.call_count == 1
    assert response.status_code == 200
    assert response.json()["goal_category"] == "zaun_einfriedung"


# ── error paths ───────────────────────────────────────────────────────────────


def test_classify_failure_does_not_abort_assess(client: TestClient, valid_situation: dict) -> None:
    """If the classification LLM call fails, the assess pipeline continues without a category."""
    mock_llm = MagicMock(spec=anthropic.Anthropic)
    # First call (classify) raises; second call (assess) succeeds
    mock_llm.messages.create.side_effect = [
        anthropic.APIConnectionError(request=MagicMock()),
        _make_llm_response(_ASSESS_JSON),
    ]

    with (
        patch("propra.api.assess._retriever") as mock_retriever,
        patch("propra.api.assess._llm", mock_llm),
    ):
        mock_retriever.retrieve.return_value = _SAMPLE_CHUNKS
        response = client.post("/api/assess", json=valid_situation)

    assert response.status_code == 200
    assert response.json()["goal_category"] is None


def test_classify_bad_json_does_not_abort_assess(client: TestClient, valid_situation: dict) -> None:
    """If the classification LLM returns malformed JSON, the assess pipeline continues gracefully."""
    mock_llm = _mock_llm_sequence("not valid json", _ASSESS_JSON)

    with (
        patch("propra.api.assess._retriever") as mock_retriever,
        patch("propra.api.assess._llm", mock_llm),
    ):
        mock_retriever.retrieve.return_value = _SAMPLE_CHUNKS
        response = client.post("/api/assess", json=valid_situation)

    assert response.status_code == 200
    assert response.json()["goal_category"] is None
