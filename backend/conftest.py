"""
pytest configuration for the backend test suite.

This conftest.py sits at the backend/ root so pytest discovers it before any
test module is imported.  It handles two concerns:

1. sys.path — ensures `backend/` is on the Python path so that bare imports
   like `from etl.africa_formalities import ...` work regardless of how pytest
   is invoked (from the repo root, from backend/, or from backend/tests/).

2. Runtime dependencies — `httpx`, `motor`, `pydantic` etc. are listed in
   backend/requirements.txt and are available in CI (installed via
   `pip install -r backend/requirements.txt`).  In developer environments or
   the agent sandbox where a full `pip install -r requirements.txt` has not
   been run, pytest would otherwise crash at collection time.  This file
   installs any listed package that is currently missing before the first test
   is collected, avoiding confusing ModuleNotFoundError failures.
"""

import os
import subprocess
import sys

# ── 1. sys.path ───────────────────────────────────────────────────────────────
_backend_dir = os.path.dirname(os.path.abspath(__file__))
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

# ── 2. Auto-install missing runtime dependencies ──────────────────────────────
_REQUIREMENTS_FILE = os.path.join(_backend_dir, "requirements.txt")

# Packages whose absence causes test-collection failures (top-level imports
# inside production modules that tests import).  We check these explicitly
# rather than installing the entire requirements.txt to keep the install fast.
_REQUIRED_PACKAGES: list[tuple[str, str]] = [
    # (importable_name, pip_install_spec)
    ("httpx",           "httpx==0.28.1"),
    ("motor",           "motor==3.3.1"),
    ("pydantic",        "pydantic==2.12.0"),
    ("pytest_asyncio",  "pytest-asyncio==1.3.0"),
    ("fastapi",         "fastapi[standard]==0.115.12"),
    ("pandas",          "pandas>=2.0"),
    ("openpyxl",        "openpyxl>=3.1"),
]


def _package_available(import_name: str) -> bool:
    """Return True if `import import_name` would succeed."""
    import importlib.util
    return importlib.util.find_spec(import_name) is not None


def _ensure_packages() -> None:
    """Install any missing packages from _REQUIRED_PACKAGES."""
    missing = [
        spec for name, spec in _REQUIRED_PACKAGES
        if not _package_available(name)
    ]
    if not missing:
        return
    print(
        f"\n[conftest] Installing missing test dependencies: {missing}",
        file=sys.stderr,
    )
    subprocess.check_call(
        [sys.executable, "-m", "pip", "install", "--quiet"] + missing
    )
    print("[conftest] Done.", file=sys.stderr)


_ensure_packages()
