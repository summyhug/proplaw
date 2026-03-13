"""Tests for the POST /intake endpoint — covers happy path and error path scenarios."""

from fastapi.testclient import TestClient


def test_intake_happy_path(client: TestClient, valid_situation: dict) -> None:
    """Valid situation is accepted and echoed back with a German confirmation message."""
    response = client.post("/api/intake", json=valid_situation)

    assert response.status_code == 200
    body = response.json()
    assert body["situation"] == valid_situation
    assert "user_message" in body
    assert isinstance(body["user_message"], str)
    assert len(body["user_message"]) > 0


def test_intake_missing_required_field(client: TestClient, valid_situation: dict) -> None:
    """Request missing a required field returns 422 with validation detail."""
    incomplete = {k: v for k, v in valid_situation.items() if k != "jurisdiction"}

    response = client.post("/api/intake", json=incomplete)

    assert response.status_code == 422
    errors = response.json()["detail"]
    assert any(e["loc"][-1] == "jurisdiction" for e in errors)


def test_intake_project_description_too_short(client: TestClient, valid_situation: dict) -> None:
    """project_description shorter than 10 characters returns 422."""
    payload = {**valid_situation, "project_description": "Kurz"}

    response = client.post("/api/intake", json=payload)

    assert response.status_code == 422
