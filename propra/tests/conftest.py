"""Shared fixtures for the Propra API test suite."""

import pytest
from fastapi.testclient import TestClient

from propra.main import app


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def valid_situation() -> dict:
    return {
        "jurisdiction": "Brandenburg",
        "property_type": "Einfamilienhaus",
        "project_description": "Ich möchte eine Garage mit 6 m × 4 m im Hintergarten bauen.",
        "has_bplan": False,
    }
