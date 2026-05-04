"""Environment validation script for AfCFTA backend dependencies."""

import importlib
import sys


REQUIRED_PACKAGES = [
    "fastapi",
    "uvicorn",
    "pydantic",
    "pymongo",
    "motor",
    "pandas",
    "numpy",
    "requests",
    "httpx",
    "faostat",
    "dotenv",
    "passlib",
    "jose",
    "multipart",
]


def validate_environment() -> bool:
    """Check that all required packages can be imported. Returns True on success."""
    errors = []
    for package in REQUIRED_PACKAGES:
        try:
            importlib.import_module(package)
        except ImportError as exc:
            errors.append(f"  MISSING: {package} ({exc})")

    if errors:
        print("Environment validation FAILED. Missing packages:")
        for err in errors:
            print(err)
        return False

    print(f"Environment validation PASSED. Python {sys.version}")
    print(f"All {len(REQUIRED_PACKAGES)} required packages are available.")
    return True


if __name__ == "__main__":
    success = validate_environment()
    sys.exit(0 if success else 1)
