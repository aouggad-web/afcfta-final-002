"""
Calendrier de démantèlement tarifaire ZLECAf applicable à l'IMPORTATION en
Égypte — droit de douane uniquement.

Sources authentiques (archivées sous backend/data/legal_refs/zlecaf_application/) :

* منشور اتفاقيات رقم 38 لسنة 2024, « إجراءات تفعيل اتفاق منطقة التجارة الحرة
  القارية الأفريقية AfCFTA » : la réduction ne porte que sur la liste A ; le
  groupe à 10 ans (réciprocité, par annuités égales) est à 50 % au 1/1/2025 ;
  le groupe à 5 ans est à 100 % au 1/1/2025 ; les listes B et C ne sont pas
  entrées en vigueur.
* منشور اتفاقيات رقم 44 لسنة 2025 du 28/12/2025 : actualise le groupe à
  10 ans (huit origines : GHA KEN CMR ZAF NAM NGA SWZ BWA), fixe la réduction
  à 60 % au 1/1/2026, et reporte les réductions des chapitres 50 à 63 et 87.

Ce que ce module oppose à l'e-Tariff Book, et pourquoi : la carte d'origines du
e-Tariff Book de l'UA contredit les circulaires pour 15 origines sur 19, et ses
barèmes publient des réductions sur les chapitres que la n° 44 reporte. Aucun
barème de l'UA, tel qu'alloué, ne reproduit l'acte national — constat du
rapprochement (EGY_rapprochement_baremes_2026-09-24.json). Le taux est donc
calculé depuis le NPF et le calendrier de la circulaire, comme pour l'Algérie,
et jamais servi depuis l'offre.

UNITÉ : pourcentages de bout en bout. Un taux publié à 5 vaut 5 % et ressort
dans la même unité.
"""

from __future__ import annotations

import datetime
import json
from pathlib import Path
from typing import Optional, Tuple

from services.official_preferential_rates import published_offer_category

_FICHES = Path(__file__).resolve().parents[1] / "data" / "legal_refs" / "zlecaf_application"
FICHE = _FICHES / "EGY_application_2026-09-14.json"

#: Chapitres dont la réduction est reportée (circulaire n° 44) : textiles et
#: habillement (50 à 63) et véhicules (87). Ils restent au NPF même pour une
#: origine admise et une ligne de liste A.
CHAPITRES_REPORTES = frozenset(str(n) for n in range(50, 64)) | {"87"}

#: Première annuité du démantèlement : 1er janvier 2021.
DEBUT_ANNEES = 2021


def _charger_groupes() -> dict:
    """Origine -> durée de démantèlement (5 ou 10 ans), lue dans la fiche.

    La fiche de détermination est la source unique : recopier les listes ici
    les laisserait diverger du texte archivé qui les établit. Fiche absente ou
    illisible : table vide, et rien n'est servi (fail-closed).
    """
    try:
        fiche = json.loads(FICHE.read_text(encoding="utf-8"))
        return {
            iso: int(groupe["dismantling_years"])
            for cle, groupe in fiche["accepted_origins"].items()
            if cle.startswith("groupe_")
            for iso in groupe["iso3"]
        }
    except (OSError, ValueError, KeyError, TypeError):
        return {}


#: Les 19 origines admises par les circulaires n° 38 et n° 44 : 8 à 10 ans,
#: 11 à 5 ans. Lue depuis la fiche, jamais recopiée.
ORIGINES_PAR_GROUPE: dict = _charger_groupes()


def origine_admise(origin_iso3: str) -> bool:
    """L'Égypte a-t-elle notifié cette origine ?"""
    return (origin_iso3 or "").upper() in ORIGINES_PAR_GROUPE


def categorie_produit(hs_code: str) -> Optional[str]:
    """Catégorie A/B/C publiée par l'e-Tariff Book, ou None si absente.

    Sert à classer, jamais à taxer : seule la liste A est réduite par la
    circulaire n° 38. La résolution se fait à la maille publiée (8 puis
    6 chiffres) ; une ligne absente rend None, et l'appelant reste au NPF.
    """
    return published_offer_category("EGY", hs_code)


def _part_restante(groupe_ans: int, annee: int) -> float:
    """Part du droit encore appliquée pour ce groupe, à cette année.

    Annuités égales : pour un démantèlement sur N ans à partir du 1/1/2021,
    la n-ième annuité retire n/N du droit. Le groupe à 5 ans atteint donc
    0,00 au 1/1/2025 (100 % de réduction, circulaire 38) et le groupe à
    10 ans 0,50 au 1/1/2025 puis 0,40 au 1/1/2026 (50 % puis 60 %,
    circulaires 38 et 44).
    """
    if annee < DEBUT_ANNEES:
        return 1.0
    part = 1.0 - (annee - (DEBUT_ANNEES - 1)) / groupe_ans
    return max(0.0, min(1.0, part))


def compute_egy_zlecaf_rate(
    hs_code: str,
    origin_iso3: str,
    normal_rate_pct: float,
    as_of: Optional[datetime.date] = None,
) -> Tuple[Optional[float], Optional[str]]:
    """Taux DD ZLECAf à l'importation en Égypte pour un HS code / une origine.

    Retourne (taux, libellé source). Le taux rendu est au plus égal au NPF :
    le calendrier applique une part restante, jamais un supplément. Hors
    origine admise, hors liste A ou chapitre reporté, c'est le NPF qui est
    rendu, avec le motif. (None, None) si les paramètres sont insuffisants —
    l'appelant garde alors son propre calcul.
    """
    if not origin_iso3 or normal_rate_pct is None:
        return None, None
    origin = origin_iso3.upper()
    hs_clean = (hs_code or "").replace(".", "").replace(" ", "")
    if not hs_clean:
        return None, None
    annee = (as_of or datetime.date.today()).year

    if origin not in ORIGINES_PAR_GROUPE:
        return normal_rate_pct, (
            f"ZLECAf non notifié pour {origin} à l'import en Égypte "
            f"(circulaires 38/2024 et 44/2025) — taux NPF appliqué"
        )

    if hs_clean[:2] in CHAPITRES_REPORTES:
        return normal_rate_pct, (
            f"Chapitre {hs_clean[:2]} — réduction reportée par la circulaire "
            f"44/2025 (textiles, habillement, véhicules) : taux NPF appliqué"
        )

    categorie = categorie_produit(hs_clean)
    if categorie != "A":
        motif = categorie or "absente de l'offre publiée"
        return normal_rate_pct, (
            f"Ligne hors liste A ({motif}) — la circulaire 38/2024 ne réduit "
            f"que la liste A : taux NPF appliqué"
        )

    groupe = ORIGINES_PAR_GROUPE[origin]
    part = _part_restante(groupe, annee)
    rate = round(normal_rate_pct * part, 6)
    return rate, (
        f"ZLECAf Égypte — liste A, groupe {groupe} ans, calendrier national "
        f"{annee} : {round((1 - part) * 100, 2)} % de réduction "
        f"(circulaires 38/2024 et 44/2025)"
    )
