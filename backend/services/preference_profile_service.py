"""
preference_profile_service.py
=============================
Profil de marge préférentielle ZLECAf d'un pays, calculé à partir de son
fichier tarifaire national ({ISO3}_tariffs.json).

Pour chaque ligne tarifaire (HS6) on dispose du droit NPF national (dd_rate)
et du taux ZLECAf (zlecaf_rate). La marge préférentielle = NPF − ZLECAf
représente l'économie tarifaire offerte par la ZLECAf sur cette ligne.

Ce module agrège ces marges au niveau pays (moyennes, part des lignes
bénéficiant d'une préférence, ventilation par sensibilité et par secteur).

Note: il s'agit d'une mesure du *potentiel* préférentiel (marges offertes),
calculée sur des données tarifaires réelles. Le taux d'utilisation effectif
des préférences nécessiterait des données douanières de demandes d'origine,
non disponibles ici.
"""

import json
import logging
import os
from typing import Dict, Optional

logger = logging.getLogger(__name__)

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")


def _load_tariff_lines(country_iso3: str) -> Optional[list]:
    path = os.path.join(DATA_DIR, f"{country_iso3.upper()}_tariffs.json")
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("tariff_lines", [])
    except (json.JSONDecodeError, OSError) as e:
        logger.error(f"Failed to load tariffs for {country_iso3}: {e}")
        return None


def _avg(values):
    return round(sum(values) / len(values), 2) if values else None


def get_preference_profile(country_iso3: str, top_sectors: int = 10) -> Dict:
    """Calcule le profil de marge préférentielle ZLECAf pour un pays."""
    country = country_iso3.strip().upper()
    lines = _load_tariff_lines(country)
    if lines is None:
        return {"error": f"No tariff data for country {country}"}

    rated = [
        ln for ln in lines if ln.get("dd_rate") is not None and ln.get("zlecaf_rate") is not None
    ]
    if not rated:
        return {"error": f"No rated tariff lines for country {country}"}

    npf_rates, zlecaf_rates, margins = [], [], []
    lines_with_preference = 0
    lines_zero_npf = 0

    # Agrégats par sensibilité et par secteur (category)
    by_sensitivity: Dict[str, Dict] = {}
    by_sector: Dict[str, Dict] = {}

    for ln in rated:
        npf = float(ln["dd_rate"])
        zl = float(ln["zlecaf_rate"])
        margin = max(npf - zl, 0.0)
        npf_rates.append(npf)
        zlecaf_rates.append(zl)
        margins.append(margin)
        if margin > 0:
            lines_with_preference += 1
        if npf == 0:
            lines_zero_npf += 1

        sens = ln.get("sensitivity") or "unknown"
        s = by_sensitivity.setdefault(sens, {"count": 0, "_margins": [], "_npf": []})
        s["count"] += 1
        s["_margins"].append(margin)
        s["_npf"].append(npf)

        sector = ln.get("category") or "other"
        sec = by_sector.setdefault(sector, {"count": 0, "_margins": []})
        sec["count"] += 1
        sec["_margins"].append(margin)

    total = len(rated)

    sensitivity_breakdown = {
        k: {
            "count": v["count"],
            "share_pct": round(v["count"] / total * 100, 1),
            "avg_npf_rate": _avg(v["_npf"]),
            "avg_preference_margin": _avg(v["_margins"]),
        }
        for k, v in sorted(by_sensitivity.items(), key=lambda x: -x[1]["count"])
    }

    top_sector_list = sorted(
        (
            {
                "sector": k,
                "count": v["count"],
                "avg_preference_margin": _avg(v["_margins"]),
            }
            for k, v in by_sector.items()
        ),
        key=lambda x: (x["avg_preference_margin"] or 0, x["count"]),
        reverse=True,
    )[:top_sectors]

    return {
        "country_iso3": country,
        "total_lines_analyzed": total,
        "avg_npf_rate": _avg(npf_rates),
        "avg_zlecaf_rate": _avg(zlecaf_rates),
        "avg_preference_margin": _avg(margins),
        "lines_with_preference": lines_with_preference,
        "lines_with_preference_pct": round(lines_with_preference / total * 100, 1),
        "lines_already_duty_free": lines_zero_npf,
        "lines_already_duty_free_pct": round(lines_zero_npf / total * 100, 1),
        "sensitivity_breakdown": sensitivity_breakdown,
        "top_sectors_by_margin": top_sector_list,
        "methodology": (
            "Marge préférentielle = NPF − ZLECAf par ligne SH6, agrégée par pays. "
            "Mesure le potentiel préférentiel offert (données tarifaires réelles), "
            "non le taux d'utilisation douanier effectif."
        ),
        "source": "Fichiers tarifaires nationaux ({ISO3}_tariffs.json)",
    }
