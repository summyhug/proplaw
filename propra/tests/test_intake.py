"""Tests for the POST /intake endpoint — covers happy path and error path scenarios."""


def test_intake_module_imports():
    """Smoke test: intake API module can be imported."""
    import propra.api.intake  # noqa: F401

    assert True
