"""
Manifeste des sources authentiques par pays.

Pour chacun des 54 pays ZLECAf, déclare LA source de données tarifaires
authentique à utiliser, sa nature (provenance) et la chaîne de repli. Aucune
donnée n'est inventée : si aucune source authentique n'existe, le pays est
marqué NONE et le pipeline le signale honnêtement.

Le registre des 54 pays (`crawlers/all_countries_registry.py`) est chargé via
importlib pour éviter de déclencher `crawlers/__init__.py`, qui importe `motor`
(MongoDB) et casse l'exécution sur une machine de crawl ordinaire.
"""

from __future__ import annotations

import importlib.util
import sys
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

BACKEND_DIR = Path(__file__).resolve().parent.parent


class Provenance(str, Enum):
    """Niveau de provenance — tous authentiques, du plus précis au moins précis.

    NONE n'est PAS authentique : c'est l'absence de source. ESTIMATED non plus :
    il est listé uniquement pour pouvoir DÉTECTER et REJETER les données
    estimées héritées (etl_computed / taux de chapitre répliqué).
    """

    NATIONAL_CRAWL = "national_crawl"  # lignes nationales scrappées sur le portail douanier
    REGIONAL_CET = (
        "regional_cet_official"  # tarif extérieur commun officiel du bloc (TEC/CET/TDC/SACU)
    )
    WTO_MFN_HS6 = "wto_mfn_hs6"  # taux MFN appliqué OMC/WITS-TRAINS au niveau HS6
    ESTIMATED = "estimated"  # NON authentique — à rejeter / purger
    NONE = "none"  # aucune source authentique disponible


# Rang d'authenticité (plus élevé = meilleure provenance). Sert au classement
# et à la sélection de la meilleure source disponible.
PROVENANCE_RANK: Dict[str, int] = {
    Provenance.NATIONAL_CRAWL.value: 4,
    Provenance.REGIONAL_CET.value: 3,
    Provenance.WTO_MFN_HS6.value: 2,
    Provenance.ESTIMATED.value: 1,
    Provenance.NONE.value: 0,
}

# Provenances considérées comme authentiques (servables à l'utilisateur).
AUTHENTIC_PROVENANCES = frozenset(
    {
        Provenance.NATIONAL_CRAWL.value,
        Provenance.REGIONAL_CET.value,
        Provenance.WTO_MFN_HS6.value,
    }
)


# Sources régionales officielles (tarif extérieur commun du bloc).
REGIONAL_CET_SOURCES: Dict[str, Dict[str, str]] = {
    "TEC CEDEAO": {
        "source": "TEC CEDEAO (Tarif Extérieur Commun)",
        "source_url": "https://www.ecowas.int",
        "note": "Tarif extérieur commun appliqué par les États membres CEDEAO/UEMOA.",
    },
    "CET EAC": {
        "source": "EAC Common External Tariff",
        "source_url": "https://www.eac.int",
        "note": "Common External Tariff appliqué par les États partenaires de l'EAC.",
    },
    "TDC CEMAC": {
        "source": "Tarif Douanier Commun CEMAC",
        "source_url": "https://www.cemac.int",
        "note": "Tarif douanier commun appliqué par les États membres de la CEMAC.",
    },
    "SACU Common Tariff": {
        "source": "SACU Common External Tariff (SARS schedule)",
        "source_url": "https://www.sars.gov.za",
        "note": "Territoire douanier unique SACU : le tarif sud-africain s'applique à l'union.",
    },
}

# Pays disposant déjà d'un crawl national authentique abouti (ligne par ligne).
# Source de vérité = fichiers data/crawled/*.json validés.
NATIONAL_CRAWL_READY: Dict[str, Dict[str, str]] = {
    "DZA": {
        "source": "conformepro.dz (données douane.gov.dz)",
        "source_url": "https://www.douane.gov.dz",
    },
    "EGY": {
        "source": "Egyptian Customs Authority (customs.gov.eg)",
        "source_url": "https://www.customs.gov.eg",
    },
    "MAR": {"source": "douane.gov.ma/adil", "source_url": "https://www.douane.gov.ma"},
    "TUN": {"source": "douane.gov.tn/tarifweb2025", "source_url": "https://www.douane.gov.tn"},
}


def _load_registry():
    """Charge le registre des 54 pays sans déclencher crawlers/__init__ (→ motor)."""
    path = BACKEND_DIR / "crawlers" / "all_countries_registry.py"
    if not path.exists():
        raise FileNotFoundError(f"Registre introuvable : {path}")
    if "acr_registry" in sys.modules:
        return sys.modules["acr_registry"]
    spec = importlib.util.spec_from_file_location("acr_registry", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["acr_registry"] = mod
    spec.loader.exec_module(mod)
    return mod


def _regional_tariff_for(blocks: List[Any], B) -> Optional[str]:
    """Détermine le tarif régional applicable, dans l'ordre de priorité."""
    if B.ECOWAS in blocks or B.UEMOA in blocks:
        return "TEC CEDEAO"
    if B.EAC in blocks:
        return "CET EAC"
    if B.CEMAC in blocks:
        return "TDC CEMAC"
    if B.SACU in blocks:
        return "SACU Common Tariff"
    return None


def build_manifest() -> Dict[str, Dict[str, Any]]:
    """Construit le manifeste {ISO3: descripteur de source authentique}.

    Chaque descripteur indique la source PRIMAIRE recommandée (provenance la
    plus élevée disponible) et la chaîne de repli authentique.
    """
    reg = _load_registry()
    R = reg.AFRICAN_COUNTRIES_REGISTRY
    B = reg.RegionalBlock

    manifest: Dict[str, Dict[str, Any]] = {}
    for iso3, cfg in R.items():
        blocks = cfg.get("blocks", [])
        regional_key = _regional_tariff_for(blocks, B)
        customs_url = cfg.get("customs_url")

        # Construit la chaîne de sources authentiques par ordre de préférence.
        chain: List[Dict[str, str]] = []

        if iso3 in NATIONAL_CRAWL_READY:
            nat = NATIONAL_CRAWL_READY[iso3]
            chain.append(
                {
                    "provenance": Provenance.NATIONAL_CRAWL.value,
                    "source": nat["source"],
                    "source_url": nat["source_url"],
                    "status": "ready",
                }
            )
        elif customs_url:
            # Portail national identifié mais crawl pas encore implémenté/validé.
            chain.append(
                {
                    "provenance": Provenance.NATIONAL_CRAWL.value,
                    "source": f"Portail douanier national ({customs_url})",
                    "source_url": customs_url,
                    "status": "to_implement",
                }
            )

        if regional_key:
            r = REGIONAL_CET_SOURCES[regional_key]
            chain.append(
                {
                    "provenance": Provenance.REGIONAL_CET.value,
                    "source": r["source"],
                    "source_url": r["source_url"],
                    "note": r["note"],
                    "status": "available",
                }
            )

        # Repli international authentique : OMC/WITS-TRAINS MFN HS6.
        chain.append(
            {
                "provenance": Provenance.WTO_MFN_HS6.value,
                "source": "WTO/WITS-TRAINS — taux MFN appliqué (HS6)",
                "source_url": "https://wits.worldbank.org",
                "status": "available_with_key",
            }
        )

        primary = chain[0] if chain else {"provenance": Provenance.NONE.value}
        manifest[iso3] = {
            "iso3": iso3,
            "iso2": cfg.get("iso2"),
            "name_en": cfg.get("name_en"),
            "name_fr": cfg.get("name_fr"),
            "region": getattr(cfg.get("region"), "value", cfg.get("region")),
            "blocks": [getattr(b, "value", b) for b in blocks],
            "regional_tariff": regional_key,
            "customs_url": customs_url,
            "priority": getattr(cfg.get("priority"), "value", cfg.get("priority")),
            "primary_provenance": primary.get("provenance"),
            "sources_chain": chain,
        }

    return manifest


def get_source_descriptor(iso3: str) -> Optional[Dict[str, Any]]:
    """Descripteur de source pour un pays donné."""
    return build_manifest().get(iso3.upper())


def country_codes() -> List[str]:
    """Liste triée des 54 codes ISO3."""
    return sorted(build_manifest().keys())
