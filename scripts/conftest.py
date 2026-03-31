"""
Root pytest configuration for the ZLECAf repository.

Provides:
- sys.path setup so backend modules are importable from both root-level tests
  and backend/tests/ without requiring an editable install.
- A ``live_server`` marker / skip mechanism: tests that require a running HTTP
  server are skipped automatically when REACT_APP_BACKEND_URL is not set.
"""

import os
import sys
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# sys.path setup
# ---------------------------------------------------------------------------
_ROOT = Path(__file__).parent
_BACKEND = _ROOT / "backend"

# Add backend to sys.path for backend module imports
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))


# ---------------------------------------------------------------------------
# Live-server skip helper
# ---------------------------------------------------------------------------

def pytest_collection_modifyitems(config, items):
    """
    Skip tests that require a live server when REACT_APP_BACKEND_URL is not set.

    Any test that performs HTTP requests via ``requests.get(BASE_URL + ...)``
    will fail with a MissingSchema error if BASE_URL is empty.  We detect this
    pattern by checking for ``BASE_URL`` usage in the test module and skip those
    tests gracefully instead of letting them hard-fail.
    """
    backend_url = os.environ.get("REACT_APP_BACKEND_URL", "").strip()
    if backend_url:
        # Server is available – run all tests normally
        return

    skip_live = pytest.mark.skip(
        reason=(
            "REACT_APP_BACKEND_URL is not set; "
            "live-server integration tests are skipped. "
            "Set the env var to run them against a running backend."
        )
    )

    for item in items:
        module = getattr(item, "module", None)
        if module is None:
            continue
        module_src = getattr(module, "__file__", "") or ""
        # Check if the module uses a BASE_URL pattern from env vars
        try:
            with open(module_src, "r", encoding="utf-8", errors="ignore") as fh:
                source = fh.read()
            if (
                "REACT_APP_BACKEND_URL" in source
                and ("requests.get" in source or "requests.post" in source)
            ):
                item.add_marker(skip_live)
        except (OSError, UnicodeDecodeError):
            pass
