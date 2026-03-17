"""FastAPI application package for the Propra API."""
import sys
from pathlib import Path

# Re-export `app` from main.py so that both `uvicorn api:app` and
# `import api; api.app` resolve correctly despite this package shadowing
# the old api.py file.
_propra_dir = str(Path(__file__).resolve().parent.parent)
if _propra_dir not in sys.path:
    sys.path.insert(0, _propra_dir)

from main import app as app  # noqa: E402
