"""Stable adapter over the single OMD/WCO alphabetical-index service.

The adapter deliberately does not read or copy the JSON corpus.  All searches
go through :mod:`omd_hs_index_service`, which remains the single loader and
search implementation.  Metadata is kept separately so the imported corpus
bytes and their recorded SHA-256 remain unchanged.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Dict, Optional

from . import omd_hs_index_service

_METADATA_PATH = Path(__file__).resolve().parent.parent / "data" / "omd_hs_index.metadata.json"


@lru_cache(maxsize=1)
def get_wco_index_metadata() -> Dict:
    return json.loads(_METADATA_PATH.read_text(encoding="utf-8"))


def search_wco_index(
    query: str,
    hs_version: str = "HS2022",
    language: Optional[str] = None,
    limit: int = 20,
) -> Dict:
    """Return WCO index candidates without inferring or expanding HS codes."""
    metadata = get_wco_index_metadata()
    if hs_version != metadata["hs_version"]:
        raise ValueError(
            f"Unsupported HS version {hs_version!r}; the installed WCO index is "
            f"{metadata['hs_version']}."
        )
    found = omd_hs_index_service.search(query, limit=limit)
    matches = []
    for row in found["results"]:
        positions = [
            {
                "code": code,
                "level": {2: "HS2", 4: "HS4", 6: "HS6"}.get(len(code), "HS_OTHER"),
            }
            for code in row.get("hs_codes", [])
        ]
        matches.append(
            {
                "query": query,
                "indexed_term": row.get("term"),
                "label": row.get("label"),
                "qualifier": row.get("qualifier"),
                "references": [row["see_also"]] if row.get("see_also") else [],
                "candidate_positions": positions,
                "codes_display": row.get("codes_display"),
                "is_range": row.get("is_range", False),
                "source": found.get("source"),
                "hs_version": metadata["hs_version"],
                "text_score": row.get("text_score"),
            }
        )
    return {
        "query": query,
        "language": language,
        "count": found["count"],
        "matches": matches,
        "source": found.get("source"),
        "metadata": metadata,
    }
