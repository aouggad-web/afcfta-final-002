"""
Calendrier de démantèlement ZLECAf applicable à l'IMPORTATION au Maroc.

Sources authentiques (archivées sous backend/data/legal_refs/zlecaf_application/) :

* Circulaire ADII n° 6530/223 du 22/01/2024, section III : « La Liste A du
  Maroc regroupe les produits soumis à un démantèlement tarifaire du droit
  d'importation (DI) et de la taxe parafiscale à l'importation (TPI), sur
  5 ans pour les pays de la Liste P1, et sur 10 ans pour les pays de la
  Liste P2. » Le démantèlement court à compter du 1er janvier 2021.
* Avenant n° 6627/223 du 09/01/2025 : actualise les codes de la Liste A pour
  la nomenclature de la loi de finances 2025 ; sa section « Liste A » répète
  la même règle (DI et TPI, 5 ans P1 / 10 ans P2) et ne modifie pas P1/P2.

Ce module ne sert que le prélèvement d'effet équivalent (la TPI) : le droit
d'importation préférentiel vient du barème publié de l'e-Tariff Book, que
services/official_preferential_rates.py sélectionne par les listes P1/P2 de la
fiche — la carte d'origines de l'UA divergeant sur 33 des 40 origines.

UNITÉ : pourcentages de bout en bout. Le taux rendu est un taux de TPI
préférentiel (part restante × TPI publiée), jamais une fraction.
"""

from __future__ import annotations

import datetime
import json
from pathlib import Path
from typing import Optional, Tuple

_FICHES = Path(__file__).resolve().parents[1] / "data" / "legal_refs" / "zlecaf_application"
FICHE = _FICHES / "MAR_application_2026-09-13.json"

#: Première annuité du démantèlement : 1er janvier 2021.
DEBUT_ANNEES = 2021

#: Référence portée par toute réduction de TPI.
REFERENCE_TPI = (
    "Circulaire ADII n° 6530/223 du 22/01/2024, section III : liste A — "
    "démantèlement du DI et de la TPI, 5 ans (P1) / 10 ans (P2) à compter du "
    "01/01/2021 (avenant n° 6627/223 du 09/01/2025, même règle)"
)


def _charger_groupes() -> dict:
    """Origine -> durée de démantèlement (5 ou 10 ans), lue dans la fiche.

    La fiche de détermination est la source unique : recopier P1/P2 ici les
    laisserait diverger du texte archivé qui les établit. Fiche absente ou
    illisible : table vide, et rien n'est servi (fail-closed).
    """
    try:
        fiche = json.loads(FICHE.read_text(encoding="utf-8"))
        return {
            iso: int(fiche["accepted_origins"][cle]["dismantling_years"])
            for cle in ("P1", "P2")
            for iso in fiche["accepted_origins"][cle]["iso3"]
        }
    except (OSError, ValueError, KeyError, TypeError):
        return {}


#: Les 40 origines admises par la circulaire : 27 en P1 (5 ans), 13 en P2
#: (10 ans). Lue depuis la fiche, jamais recopiée.
ORIGINES_PAR_GROUPE: dict = _charger_groupes()


def origine_admise(origin_iso3: str) -> bool:
    """Le Maroc a-t-il notifié cette origine ?"""
    return (origin_iso3 or "").upper() in ORIGINES_PAR_GROUPE


def part_restante(origin_iso3: str, as_of: Optional[datetime.date] = None) -> Optional[float]:
    """Part du droit (DI comme TPI) encore appliquée pour cette origine.

    Annuités égales : sur N années à compter du 1/1/2021, la n-ième annuité
    retire n/N. Le groupe P1 est donc éteint au 1/1/2025 et P2 à 40 % au
    1/1/2026. Rend None pour une origine non admise.
    """
    ans = ORIGINES_PAR_GROUPE.get((origin_iso3 or "").upper())
    if ans is None:
        return None
    annee = (as_of or datetime.date.today()).year
    if annee < DEBUT_ANNEES:
        return 1.0
    return max(0.0, min(1.0, 1.0 - (annee - (DEBUT_ANNEES - 1)) / ans))


def tpi_preferentielle(
    tpi_base_pct: Optional[float],
    origin_iso3: str,
    as_of: Optional[datetime.date] = None,
) -> Tuple[Optional[float], Optional[str]]:
    """TPI préférentielle : part restante appliquée à la TPI publiée.

    Retourne (taux, référence), ou (None, None) si l'origine n'est pas admise
    ou le taux de base absent. Jamais d'exonération immédiate : la circulaire
    soumet la TPI au même calendrier que le DI (contrairement au DAPS
    algérien, dont l'exonération est binaire dans la circulaire 482/2024).
    """
    if tpi_base_pct is None or not origine_admise(origin_iso3):
        return None, None
    part = part_restante(origin_iso3, as_of)
    if part is None:
        return None, None
    return round(float(tpi_base_pct) * part, 6), REFERENCE_TPI
