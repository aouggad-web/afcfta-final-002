"""
Service de recherche « nom de marchandise -> code SH » (index alphabétique OMD).

Objectif produit : permettre à un utilisateur SANS connaissance douanière de
retrouver le code SH d'un produit en tapant son nom courant (« huile de palme »,
« machine à coudre », « thé vert »…), pour alimenter tous les modules du SaaS qui
attendent un code SH (flux stratégiques, tarifs, règles d'origine, statistiques).

Données : ``data/omd_hs_index.json``, produit par ``etl/omd_hs_index.py`` à partir
des index alphabétiques officiels de l'OMD (Système Harmonisé, 7e éd. 2022).

Recherche : par TOKENS, insensible à la casse et aux accents, indépendante de
l'ordre des mots — indispensable car l'OMD classe par premier mot significatif
(« PALME (HUILE DE) » et non « HUILE DE PALME »). Une requête matche une entrée
si TOUS ses mots figurent dans le libellé. Classement : correspondance exacte du
terme, puis préfixe, puis présence de tous les mots, les entrées codées avant les
simples renvois.
"""

from __future__ import annotations

import json
import re
import unicodedata
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Optional

_INDEX_PATH = Path(__file__).resolve().parent.parent / "data" / "omd_hs_index.json"


def _strip_accents(text: str) -> str:
    decomposed = unicodedata.normalize("NFD", text)
    return "".join(c for c in decomposed if unicodedata.category(c) != "Mn")


def _normalize(text: str) -> str:
    """Minuscule, sans accents, ponctuation réduite à des espaces."""
    text = _strip_accents((text or "").lower())
    return re.sub(r"[^a-z0-9]+", " ", text).strip()


@lru_cache(maxsize=1)
def _load() -> Dict:
    """Charge l'index une fois et pré-calcule la forme normalisée de chaque libellé."""
    try:
        payload = json.loads(_INDEX_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {"source": None, "entries": [], "norm": []}
    entries = payload.get("entries", [])
    norm = [_normalize(e.get("label", "")) for e in entries]
    return {"source": payload.get("source"), "entries": entries, "norm": norm}


def _score(query_norm: str, tokens: List[str], label_norm: str, entry: Dict) -> Optional[int]:
    """
    Score de pertinence (plus haut = mieux) ou None si l'entrée ne matche pas.
    Tous les tokens de la requête doivent figurer dans le libellé (sémantique ET).
    """
    if not all(tok in label_norm for tok in tokens):
        return None
    score = 0
    if label_norm == query_norm:
        score += 1000  # libellé identique
    term_norm = _normalize(entry.get("term", ""))
    if term_norm == query_norm:
        score += 500  # le terme principal EST la requête
    if label_norm.startswith(query_norm):
        score += 200  # préfixe
    if entry.get("hs_codes"):
        score += 50  # une entrée codée prime sur un simple renvoi « voir »
    # Bonus de concision : plus le libellé est court à tokens égaux, plus il est
    # spécifique et pertinent (« THE vert » avant « … machines pour le thé … »).
    score += max(0, 40 - len(label_norm.split()))
    return score


def search(query: str, limit: int = 20) -> Dict:
    """
    Recherche un produit et retourne les codes SH correspondants.

    Retour ::

        {
          "query": "...",
          "count": N,
          "results": [
            {"label", "term", "qualifier", "hs_codes": [...],
             "codes_display", "is_range", "see_also"},
            ...
          ],
          "source": "OMD — Index alphabétique du Système Harmonisé (7e éd. 2022)"
        }
    """
    data = _load()
    query_norm = _normalize(query)
    tokens = query_norm.split()
    if not tokens:
        return {"query": query, "count": 0, "results": [], "source": data.get("source")}

    scored: List[tuple] = []
    for entry, label_norm in zip(data["entries"], data["norm"]):
        s = _score(query_norm, tokens, label_norm, entry)
        if s is not None:
            scored.append((s, entry))

    scored.sort(key=lambda x: (-x[0], len(x[1]["label"])))
    results = [
        {
            "label": e["label"],
            "term": e["term"],
            "qualifier": e.get("qualifier"),
            "hs_codes": e.get("hs_codes", []),
            "codes_display": e.get("codes_display"),
            "is_range": e.get("is_range", False),
            "see_also": e.get("see_also"),
        }
        for _, e in scored[: max(1, limit)]
    ]
    return {
        "query": query,
        "count": len(scored),
        "results": results,
        "source": data.get("source"),
    }
