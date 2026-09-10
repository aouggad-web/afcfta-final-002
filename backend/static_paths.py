"""Resolve SPA asset paths without allowing sibling directories or symlink escapes."""

from pathlib import Path
from typing import Optional


def resolve_frontend_file(build_dir: Path, full_path: str) -> Optional[Path]:
    root = build_dir.resolve()
    try:
        candidate = (root / full_path).resolve()
        candidate.relative_to(root)
        return candidate if candidate.is_file() else None
    except (ValueError, OSError, RuntimeError):
        return None
