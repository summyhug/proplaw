"""Tests for the POST /assess endpoint — covers happy path and error path scenarios."""

from fastapi.testclient import TestClient


def test_assess_returns_503_until_implemented(client: TestClient, valid_situation: dict) -> None:
    """Valid situation against /assess returns 503 until retrieval/LLM are wired."""
    response = client.post("/api/assess", json=valid_situation)

    assert response.status_code == 503
    body = response.json()
    assert "detail" in body


def test_assess_missing_required_field(client: TestClient, valid_situation: dict) -> None:
    """Request missing a required field returns 422 before reaching the assess logic."""
    incomplete = {k: v for k, v in valid_situation.items() if k != "has_bplan"}

    response = client.post("/api/assess", json=incomplete)

    assert response.status_code == 422
    errors = response.json()["detail"]
    assert any(e["loc"][-1] == "has_bplan" for e in errors)


def test_assess_project_description_too_short(client: TestClient, valid_situation: dict) -> None:
    """project_description shorter than 10 characters returns 422."""
    payload = {**valid_situation, "project_description": "Kurz"}

    response = client.post("/api/assess", json=payload)

    assert response.status_code == 422
