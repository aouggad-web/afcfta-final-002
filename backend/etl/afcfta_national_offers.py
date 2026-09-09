"""
afcfta_national_offers.py
Registre des offres tarifaires nationales ZLECAf (niveau 2), en précédence
sur le canevas générique SH2 (niveau 1, voir afcfta_schedule.py).

Le démantèlement ZLECAf est à deux niveaux :

  Niveau 1 — le canevas générique (SH2). Les modalités de l'Annexe 1 :
    répartition ~90/7/3 en catégories A/B/C, réduction linéaire annuelle,
    échéances 5/10 ans (non-PMA) et 10/13 ans (PMA). C'est un gabarit —
    normatif dans sa structure, indicatif dans son affectation ligne à
    ligne. Implémenté par ``classify_hs6()`` (afcfta_schedule.py).

  Niveau 2 — l'offre tarifaire nationale. Chaque État partie dépose son
    schéma de concessions, qui MODIFIE l'affectation ligne à ligne
    (SH6/SH8/SH10) tout en respectant le canevas (parts globales,
    échéances éligibles). Exemple opérationnel : l'Algérie (circulaire DGD
    n°482/DGD/SP/D.042/24 du 22/10/2024, voir services/zlecaf_schedule_dza.py).

Ce module route vers l'offre nationale quand elle couvre la ligne demandée,
à la précision où elle a été publiée — il n'invente jamais de
correspondance à une précision non couverte par la source (ex: une offre
publiée au SH10 n'est jamais appliquée à un code fourni au SH6 par
troncature/padding, ce qui produirait une classification fictive).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, Optional, Tuple

# Provenance de la classification renvoyée à l'appelant.
CLASSIFICATION_SOURCE_NATIONAL = "NATIONAL_OFFER_OFFICIAL"
CLASSIFICATION_SOURCE_CANVAS = "AFCFTA_CANVAS_HS2"

# Modalités officielles du canevas (Annexe 1, Article 4) — part indicative
# des lignes par catégorie, hors D (déjà à 0%, hors périmètre du calendrier).
CANVAS_MODALITY_PCT = {"A": 90.0, "B": 7.0, "C": 3.0}


@dataclass(frozen=True)
class NationalOfferAdapter:
    """Déclare une offre tarifaire nationale officielle ZLECAf."""

    iso3: str
    hs_precision: int  # précision (nb de chiffres) à laquelle l'offre est publiée
    classify: Callable[
        [str], Optional[str]
    ]  # code complet (>= hs_precision chiffres) -> "A"/"B"/"C"
    legal_reference: str
    source_id: str
    publication_url: Optional[str] = None
    canvas_version: str = "Annexe 1, Protocole sur le Commerce des Marchandises (UA, 2018)"
    # Dénombrement officiel des lignes explicitement listées (B, C) et du
    # total de lignes tarifaires du pays à la précision ``hs_precision``,
    # pour la vérification de conformité au canevas. None si non disponible.
    explicit_line_counts: Optional[Dict[str, int]] = None
    total_line_count: Optional[int] = None


def _dza_classify(hs_code_clean: str) -> Optional[str]:
    from services.zlecaf_schedule_dza import tariff_list

    return tariff_list(hs_code_clean)


def _dza_line_counts() -> Dict[str, int]:
    from services.zlecaf_schedule_dza import LIST_B_CODES, LIST_C_CODES

    return {"B": len(LIST_B_CODES), "C": len(LIST_C_CODES)}


# Registre des offres nationales officielles intégrées. L'Algérie est la
# seule juridiction disposant aujourd'hui d'une offre nationale ZLECAf
# vérifiée et exploitable ligne à ligne (circulaire DGD 482/2024). Voir
# ``docs/data-sources/DZA_SOURCE_REGISTER.md`` pour l'état de la
# traçabilité documentaire : le texte de la circulaire n'est, à ce jour,
# accessible sur aucun portail public interrogeable (douane.gov.dz et
# mfdgi.gov.dz injoignables au moment de la collecte) ; le contenu du
# calendrier est néanmoins repris fidèlement de la citation détaillée par
# article/partie déjà consignée dans ``services/zlecaf_schedule_dza.py``.
NATIONAL_OFFER_REGISTRY: Dict[str, NationalOfferAdapter] = {
    "DZA": NationalOfferAdapter(
        iso3="DZA",
        hs_precision=10,
        classify=_dza_classify,
        legal_reference="Circulaire DGD n°482/DGD/SP/D.042/24 du 22/10/2024, "
        "« Schéma général du traitement tarifaire à l'importation des "
        "produits dans le cadre de la ZLECAf »",
        source_id="DZA-DGD-482-2024-PENDING",
        publication_url=None,
        explicit_line_counts=_dza_line_counts(),
        total_line_count=17115,  # DZA_tariffs.json summary.total_sub_positions (SH10)
    ),
}


def resolve_classification(
    country_iso3: str, hs_code: str
) -> Tuple[Optional[str], str, Optional[NationalOfferAdapter]]:
    """Résout catégorie ZLECAf + provenance pour un code HS.

    Respecte la précision réellement publiée par l'offre nationale : un
    code fourni à une précision inférieure à celle de l'offre (ex: SH6
    alors que l'offre est publiée au SH10) n'est jamais forcé par
    troncature/padding — l'appelant retombe alors explicitement sur le
    canevas générique.

    Retourne ``(category_or_None, classification_source, adapter_or_None)``.
    ``category`` est None si l'offre nationale ne peut pas classer ce code
    (précision insuffisante ou code non listé côté adaptateur) ; dans ce
    cas l'appelant doit utiliser ``classify_hs6()`` (canevas SH2).
    """
    clean = "".join(ch for ch in hs_code if ch.isdigit())
    adapter = NATIONAL_OFFER_REGISTRY.get(country_iso3.upper())
    if adapter and len(clean) >= adapter.hs_precision:
        category = adapter.classify(clean)
        if category:
            return category, CLASSIFICATION_SOURCE_NATIONAL, adapter
    return None, CLASSIFICATION_SOURCE_CANVAS, None


def check_conformity(
    country_iso3: str,
    modality: Dict[str, float] = CANVAS_MODALITY_PCT,
    tolerance_pct: float = 5.0,
) -> dict:
    """Vérifie les parts A/B/C d'une offre nationale contre le canevas
    (~90/7/3 par défaut). Ne rejette et n'accepte jamais silencieusement :
    remonte les écarts au-delà de la tolérance comme constat à revoir,
    sans invalider l'offre (l'exactitude légale prime sur la conformité
    statistique — une offre officielle reste applicable même en cas
    d'écart, le constat sert la revue humaine)."""
    adapter = NATIONAL_OFFER_REGISTRY.get(country_iso3.upper())
    if not adapter:
        return {
            "country_iso3": country_iso3.upper(),
            "status": "NO_NATIONAL_OFFER_REGISTERED",
            "findings": [],
        }
    if not adapter.explicit_line_counts or not adapter.total_line_count:
        return {
            "country_iso3": country_iso3.upper(),
            "status": "NOT_COMPUTABLE",
            "findings": [
                "Dénombrement total des lignes tarifaires ou des listes "
                "explicites indisponible : la part A/B/C ne peut pas être "
                "calculée de façon fiable."
            ],
        }

    total = adapter.total_line_count
    counts_b = adapter.explicit_line_counts.get("B", 0)
    counts_c = adapter.explicit_line_counts.get("C", 0)
    counts_a = total - counts_b - counts_c
    shares = {
        "A": round(counts_a / total * 100, 2),
        "B": round(counts_b / total * 100, 2),
        "C": round(counts_c / total * 100, 2),
    }

    findings = []
    for category, expected_pct in modality.items():
        observed = shares.get(category, 0.0)
        deviation = round(observed - expected_pct, 2)
        if abs(deviation) > tolerance_pct:
            findings.append(
                f"Catégorie {category} : part observée {observed}% s'écarte de "
                f"{deviation:+.2f} points du canevas ({expected_pct}%, tolérance "
                f"±{tolerance_pct} points) — à revoir, l'offre reste applicable."
            )

    return {
        "country_iso3": country_iso3.upper(),
        "status": "REVIEW_FLAGGED" if findings else "WITHIN_TOLERANCE",
        "total_line_count": total,
        "hs_precision": adapter.hs_precision,
        "observed_shares_pct": shares,
        "canvas_modality_pct": modality,
        "tolerance_pct": tolerance_pct,
        "findings": findings,
        "legal_reference": adapter.legal_reference,
        "source_id": adapter.source_id,
    }
