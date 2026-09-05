"""Couche « indications secondaires » — prestataires et frais REPORTÉS, non vérifiés.

Distincte et jamais mélangée au registre conforme (regulatory_compliance_service),
qui, lui, est fail-closed et sourcé en primaire. Cette couche expose des données
issues d'une synthèse secondaire (backlog de collecte, data/research/…) à titre
purement INFORMATIF, avec un étiquetage explicite « à confirmer ». Elle n'alimente
jamais un total, n'émet jamais de fee CALCULABLE, et ne prétend jamais à une
source officielle.
"""

import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional

REPO_ROOT = Path(__file__).resolve().parents[2]
_DATASET_PATH = REPO_ROOT / "data/research/private_customs_missions_africa_2016_2026.json"

# Statuts de mandat reportés considérés comme « actif » côté indications
# secondaires (le vocabulaire du dossier diffère du registre conforme).
_REPORTED_ACTIVE = {"ACTIVE", "ACTIVE_TRANSFERRED_TO_STATE", "ACTIVE_TRANSITION"}


@lru_cache(maxsize=1)
def _load_dataset() -> Dict[str, Any]:
    with open(_DATASET_PATH, "r", encoding="utf-8") as fh:
        return json.load(fh)


def get_reported_provenance() -> Dict[str, Any]:
    data = _load_dataset()
    return data.get("source_provenance", {})


def get_reported_missions(country_iso3: Optional[str]) -> List[Dict[str, Any]]:
    """Retourne les enregistrements reportés pour un pays (liste, jamais None).

    Un enregistrement peut regrouper plusieurs pays dans country_iso3 (donnée
    source brute) ; on filtre sur l'ISO3 exact en tête de champ pour rester
    prudent, sans sur-attribuer une donnée mal désagrégée.
    """
    if not country_iso3:
        return []
    iso = country_iso3.upper()
    out: List[Dict[str, Any]] = []
    for rec in _load_dataset().get("records", []):
        if rec.get("country_iso3", "").upper() == iso:
            out.append(rec)
    return out


def build_reported_layer(
    dest_iso3: Optional[str], origin_iso3: Optional[str]
) -> Optional[Dict[str, Any]]:
    """Compose la couche d'indications secondaires pour import + export.

    Renvoie None si aucun enregistrement reporté n'existe pour l'un ou l'autre
    pays (pas de rubrique vide).
    """
    items: List[Dict[str, Any]] = []
    for side, iso in (("import", dest_iso3), ("export", origin_iso3)):
        for rec in get_reported_missions(iso):
            fee = rec.get("reported_fee_structure") or {}
            items.append(
                {
                    "side": side,
                    "country_iso3": rec.get("country_iso3"),
                    "country_name": rec.get("country_name"),
                    "program": rec.get("program"),
                    "formality_type": rec.get("formality_type"),
                    "providers": rec.get("providers", []),
                    "mission": rec.get("mission"),
                    "payer": rec.get("payer"),
                    "period": rec.get("period"),
                    "mandate_status_reported": rec.get("mandate_status_reported"),
                    "is_reported_active": rec.get("mandate_status_reported") in _REPORTED_ACTIVE,
                    "reported_fee_method": fee.get("method"),
                    "reported_fee_range": fee.get("reported_range"),
                    "reported_fee_min": fee.get("reported_min"),
                    "reported_fee_max": fee.get("reported_max"),
                    "reported_fee_rate": fee.get("reported_rate"),
                    "reported_fee_currency": fee.get("currency"),
                    "traceability": rec.get("traceability"),
                    "verification_status": rec.get("verification_status", "UNVERIFIED"),
                    # Jamais un montant exploitable : la couche reportée n'émet
                    # aucun fee calculable.
                    "fee_status": "FEE_EXISTS_AMOUNT_NOT_AVAILABLE",
                }
            )

    if not items:
        return None

    return {
        "reliability": "UNVERIFIED_SECONDARY",
        "provenance": get_reported_provenance(),
        "disclaimer": (
            "Indications issues d'une synthèse secondaire non vérifiée (backlog de "
            "collecte). Montants approximatifs et non opposables — à confirmer auprès "
            "du prestataire ou de l'autorité compétente. N'entrent dans aucun total."
        ),
        "items": items,
    }
