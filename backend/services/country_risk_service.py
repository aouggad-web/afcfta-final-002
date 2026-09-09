"""
Ratio de risque pays composite pour le module Opportunités.
============================================================

Croise deux familles de sources complémentaires :

1. NOTATIONS SOUVERAINES (Standard & Poor's, Moody's, Fitch Ratings, Scope) —
   déjà curées dans le dépôt (``country_data.REAL_COUNTRY_DATA.risk_ratings``,
   54 pays). Elles mesurent la probabilité de défaut de l'ÉTAT sur sa dette à
   long terme : c'est le plafond macro-financier du pays (accès aux devises,
   soutenabilité budgétaire), mais PAS le risque d'une transaction commerciale.

2. ÉVALUATION OPÉRATIONNELLE type ASSURANCE-CRÉDIT (convention d'échelle
   Coface/OCDE : A1 → D) — profils curés de la plateforme
   (``banking_system/risk_assessment.py``, 18 pays détaillés), du même type
   que les évaluations publiées par la Coface ou Allianz Trade : risque
   d'impayé COMMERCIAL à court terme, risque de change, risque politique,
   risque de transfert, disponibilité de l'assurance-crédit et instruments
   recommandés. C'est la vue la plus proche d'une opportunité d'exportation.

Formule (transparente, exposée dans chaque réponse) :

    risk_ratio = w_op × score_opérationnel + w_sov × score_souverain
    (w_op = 0.6, w_sov = 0.4 quand les deux composantes existent)

Pourquoi 60/40 : une opportunité du module est une TRANSACTION commerciale
(paiement à 30-180 jours, rapatriement des fonds), pas un investissement en
dette souveraine — le risque opérationnel court terme (celui que couvrent les
assureurs-crédit) pèse donc plus lourd que la note souveraine, qui sert
d'ancrage macro. Quand une composante manque, l'autre porte 100 % du ratio et
la réponse le dit explicitement (confidence dégradée).

Garde-fous « zéro fabrication » :
- Le profil opérationnel PAR DÉFAUT de banking_system (pays non curé) n'entre
  JAMAIS dans le ratio — un grade générique appliqué à un pays inconnu serait
  une donnée fabriquée. La composante est alors marquée indisponible.
- Les notations "NR"/"Non évalué" sont exclues du calcul, jamais converties.
- Chaque réponse embarque la formule, les intrants, les poids effectifs, la
  méthodologie détaillée et les mises en garde (une note n'est pas une
  garantie ; évaluer chaque transaction ; dates des données).
"""

import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

# ── Échelle des notations souveraines (crans standard S&P/Fitch + Moody's) ────
# Cran 1 = AAA/Aaa (meilleur) ... 21 = C, 22 = défaut (SD/D/RD).
_NOTCHES: Dict[str, int] = {}
for i, (sf, moody) in enumerate(
    [
        ("AAA", "Aaa"),
        ("AA+", "Aa1"),
        ("AA", "Aa2"),
        ("AA-", "Aa3"),
        ("A+", "A1"),
        ("A", "A2"),
        ("A-", "A3"),
        ("BBB+", "Baa1"),
        ("BBB", "Baa2"),
        ("BBB-", "Baa3"),
        ("BB+", "Ba1"),
        ("BB", "Ba2"),
        ("BB-", "Ba3"),
        ("B+", "B1"),
        ("B", "B2"),
        ("B-", "B3"),
        ("CCC+", "Caa1"),
        ("CCC", "Caa2"),
        ("CCC-", "Caa3"),
        ("CC", "Ca"),
        ("C", "C"),
    ],
    start=1,
):
    _NOTCHES[sf] = i
    _NOTCHES[moody] = i
for default_grade in ("SD", "D", "RD"):
    _NOTCHES[default_grade] = 22

_MAX_NOTCH = 22
_UNRATED = {None, "", "NR", "WR", "NON ÉVALUÉ", "NON EVALUE", "N/A"}

# ── Échelle opérationnelle (convention Coface/OCDE, cf. banking_system) ───────
# A1 très faible ... D très élevé. Scores 0-100 (100 = risque minimal),
# centres de classe réguliers sur l'échelle publiée à 7 niveaux.
_OPERATIONAL_GRADE_SCORES = {
    "A1": 93,
    "A2": 82,
    "A3": 71,
    "A4": 61,
    "B": 46,
    "C": 32,
    "D": 18,
}

_GRADE_LABELS = {
    "A1": "risque très faible",
    "A2": "risque faible",
    "A3": "risque satisfaisant",
    "A4": "risque acceptable",
    "B": "risque incertain",
    "C": "risque élevé",
    "D": "risque très élevé",
}

# Poids nominaux quand les DEUX composantes sont disponibles.
_W_OPERATIONAL = 0.6
_W_SOVEREIGN = 0.4


def _iso2(iso3: str) -> Optional[str]:
    try:
        from constants import AFRICAN_COUNTRIES

        for c in AFRICAN_COUNTRIES:
            if c.get("iso3") == (iso3 or "").upper():
                return c.get("code")
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning("iso2 lookup failed: %s", exc)
    return None


def _notch_of(rating: Optional[str]) -> Optional[int]:
    token = (rating or "").strip().upper()
    if token in {u for u in _UNRATED if u} or not token:
        return None
    # Tolère les suffixes de perspective ("B+ (stable)") et le "u" non sollicité.
    token = token.split("(")[0].split()[0].rstrip("U").strip()
    return _NOTCHES.get(token) or _NOTCHES.get(token.capitalize())


def _notch_to_score(notch: float) -> float:
    """Cran 1 → 100 ; cran 22 (défaut) → 0. Interpolation linéaire."""
    return max(0.0, min(100.0, 100.0 * (_MAX_NOTCH - notch) / (_MAX_NOTCH - 1)))


def _sovereign_component(iso3: str) -> Dict:
    """Score souverain 0-100 depuis les notations d'agences curées (54 pays)."""
    try:
        from country_data import REAL_COUNTRY_DATA

        ratings = (REAL_COUNTRY_DATA.get(iso3) or {}).get("risk_ratings") or {}
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning("agency ratings unavailable: %s", exc)
        ratings = {}

    used, ignored = {}, {}
    agencies = {
        "sp": "Standard & Poor's",
        "moodys": "Moody's",
        "fitch": "Fitch Ratings",
        "scope": "Scope Ratings",
    }
    notches = []
    for key, label in agencies.items():
        raw = ratings.get(key)
        notch = _notch_of(raw)
        if notch is None:
            ignored[label] = raw or "NR"
        else:
            used[label] = raw
            notches.append(notch)

    if not notches:
        return {
            "available": False,
            "score": None,
            "ratings_used": {},
            "ratings_ignored": ignored,
            "explanation": (
                "Aucune notation souveraine exploitable : le pays n'est noté par "
                "aucune des agences suivies (S&P, Moody's, Fitch, Scope) — les "
                "mentions NR (« not rated ») ne sont jamais converties en score."
            ),
        }

    avg_notch = sum(notches) / len(notches)
    score = round(_notch_to_score(avg_notch), 1)
    return {
        "available": True,
        "score": score,
        "average_notch": round(avg_notch, 2),
        "scale": "cran 1 = AAA/Aaa (score 100) … cran 22 = défaut SD/D (score 0)",
        "ratings_used": used,
        "ratings_ignored": ignored,
        "explanation": (
            f"Score souverain {score}/100, moyenne de {len(notches)} notation(s) "
            f"d'agence convertie(s) en crans standard (cran moyen "
            f"{round(avg_notch, 2)}). Une notation souveraine mesure la capacité "
            "de l'ÉTAT à honorer sa dette à long terme : elle fixe le plafond "
            "macro-financier (accès aux devises, stabilité budgétaire) mais ne "
            "mesure PAS le risque d'impayé d'un acheteur privé sur une "
            "transaction commerciale."
        ),
    }


def _operational_component(iso3: str) -> Dict:
    """
    Grade opérationnel type assurance-crédit (convention Coface/OCDE A1→D)
    depuis les profils curés de banking_system — 18 pays détaillés. Le profil
    PAR DÉFAUT (pays non curé) est refusé : un grade générique serait fabriqué.
    """
    iso2 = _iso2(iso3)
    try:
        from banking_system.risk_assessment import RISK_PROFILES
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning("risk profiles unavailable: %s", exc)
        return {"available": False, "score": None, "explanation": str(exc)}

    profile = RISK_PROFILES.get(iso2) if iso2 else None
    if profile is None:
        return {
            "available": False,
            "score": None,
            "explanation": (
                "Pas de profil opérationnel curé pour ce pays dans la base "
                "plateforme (18 pays couverts en détail). Le profil générique "
                "par défaut est volontairement exclu du ratio : appliquer un "
                "grade standard à un pays non évalué reviendrait à fabriquer "
                "une donnée. Le ratio repose alors sur la seule composante "
                "souveraine, avec confiance dégradée."
            ),
        }

    grade = profile.country_risk_rating
    score = _OPERATIONAL_GRADE_SCORES.get(grade)
    return {
        "available": score is not None,
        "score": score,
        "grade": grade,
        "grade_label": _GRADE_LABELS.get(grade, grade),
        "scale": "convention Coface/OCDE : A1 (très faible) → D (très élevé)",
        "forex_risk": profile.forex_risk,
        "political_risk": profile.political_risk,
        "transfer_risk": profile.transfer_risk,
        "credit_insurance_available": profile.credit_insurance_available,
        "recommended_instruments": profile.recommended_instruments,
        "max_recommended_exposure_usd": profile.max_exposure_usd,
        "notes": profile.notes,
        "explanation": (
            f"Grade opérationnel {grade} ({_GRADE_LABELS.get(grade, '—')}), "
            f"score {score}/100 — évaluation curée par la plateforme suivant la "
            "convention d'échelle des assureurs-crédit (Coface/OCDE ; Allianz "
            "Trade publie des évaluations du même type). Elle reflète le risque "
            "d'impayé COMMERCIAL à court terme sur ce marché : risque de change "
            f"({profile.forex_risk}), risque politique ({profile.political_risk}), "
            f"risque de transfert ({profile.transfer_risk}), et la disponibilité "
            "d'une assurance-crédit"
            + (" (disponible)" if profile.credit_insurance_available else " (indisponible)")
            + ". C'est la composante la plus proche du risque réel d'une "
            "opportunité d'exportation."
        ),
    }


def _risk_class(ratio: float) -> str:
    if ratio >= 75:
        return "faible"
    if ratio >= 55:
        return "modéré"
    if ratio >= 35:
        return "élevé"
    return "très élevé"


def get_risk_ratio(country_iso3: str) -> Dict:
    """
    Ratio de risque composite 0-100 (100 = risque minimal) pour un pays
    partenaire, avec le détail complet de chaque composante, la formule,
    les poids effectifs, la méthodologie et les mises en garde.
    """
    iso3 = (country_iso3 or "").strip().upper()
    sovereign = _sovereign_component(iso3)
    operational = _operational_component(iso3)

    weights: Dict[str, float] = {}
    if sovereign["available"] and operational["available"]:
        weights = {"operational": _W_OPERATIONAL, "sovereign": _W_SOVEREIGN}
        ratio = _W_OPERATIONAL * operational["score"] + _W_SOVEREIGN * sovereign["score"]
        confidence = "normale"
    elif operational["available"]:
        weights = {"operational": 1.0, "sovereign": 0.0}
        ratio = float(operational["score"])
        confidence = "dégradée (composante souveraine indisponible)"
    elif sovereign["available"]:
        weights = {"operational": 0.0, "sovereign": 1.0}
        ratio = float(sovereign["score"])
        confidence = "dégradée (composante opérationnelle non curée pour ce pays)"
    else:
        return {
            "available": False,
            "country_iso3": iso3,
            "risk_ratio": None,
            "components": {"sovereign": sovereign, "operational": operational},
            "note": (
                "Aucune composante disponible : pays sans notation d'agence "
                "exploitable ni profil opérationnel curé — aucun ratio n'est "
                "calculé plutôt que d'inventer un score."
            ),
        }

    ratio = round(ratio, 1)
    methodology: List[str] = [
        "risk_ratio = w_op × score_opérationnel + w_sov × score_souverain "
        f"(poids effectifs : opérationnel {weights['operational']}, "
        f"souverain {weights['sovereign']}).",
        "Composante souveraine : moyenne des notations S&P / Moody's / Fitch / "
        "Scope converties en crans standard (AAA/Aaa = cran 1 = 100 ; défaut "
        "SD/D = cran 22 = 0). Mesure le risque de défaut de l'État à long "
        "terme — plafond macro-financier du pays.",
        "Composante opérationnelle : grade A1→D (convention d'échelle "
        "Coface/OCDE, du même type que les évaluations pays publiées par la "
        "Coface ou Allianz Trade) issu des profils curés de la plateforme : "
        "risque d'impayé commercial court terme, change, politique, transfert, "
        "assurance-crédit.",
        "Pondération nominale 60 % opérationnel / 40 % souverain : une "
        "opportunité du module est une transaction commerciale (paiement 30-180 "
        "jours, rapatriement des fonds), pas un investissement en dette "
        "souveraine — le risque court terme couvert par les assureurs-crédit "
        "prime, la note souveraine sert d'ancrage macro.",
        "Quand une composante manque (pays non noté, ou profil opérationnel non "
        "curé), l'autre porte 100 % du ratio et la confiance est marquée "
        "« dégradée » — aucun score n'est jamais inventé pour combler.",
    ]
    caveats = [
        "Un ratio de risque n'est PAS une garantie : il synthétise des "
        "évaluations publiques datées, pas la solvabilité d'un acheteur précis.",
        "Chaque transaction doit être évaluée individuellement (montant, "
        "acheteur, instrument de paiement) — voir recommended_instruments et "
        "max_recommended_exposure_usd de la composante opérationnelle.",
        "Les notations et grades évoluent : vérifier la date des sources avant "
        "toute décision d'exposition significative.",
        "Le grade opérationnel suit la CONVENTION d'échelle Coface/OCDE — c'est "
        "l'évaluation curée de la plateforme, pas un flux temps réel Coface ou "
        "Allianz Trade ; pour une couverture ferme, interroger l'assureur.",
    ]

    return {
        "available": True,
        "country_iso3": iso3,
        "risk_ratio": ratio,
        "risk_class": _risk_class(ratio),
        "scale": "0-100 — 100 = risque minimal, 0 = risque maximal",
        "confidence": confidence,
        "weights": weights,
        "components": {"sovereign": sovereign, "operational": operational},
        "methodology": methodology,
        "caveats": caveats,
        "sources": [
            "Standard & Poor's / Moody's / Fitch Ratings / Scope Ratings — "
            "notations souveraines (dataset Profils Pays, WDI 2024)",
            "Profils de risque opérationnel plateforme (banking_system, "
            "convention Coface/OCDE — cf. évaluations type Coface / Allianz Trade)",
        ],
    }


def compact_risk_for_opportunity(country_iso3: str) -> Optional[Dict]:
    """
    Version compacte pour l'enrichissement des opportunités IA (15 opportunités
    par analyse : le détail complet reste sur l'endpoint dédié).
    """
    full = get_risk_ratio(country_iso3)
    if not full.get("available"):
        return None
    op = full["components"]["operational"]
    sov = full["components"]["sovereign"]
    return {
        "risk_ratio": full["risk_ratio"],
        "risk_class": full["risk_class"],
        "confidence": full["confidence"],
        "sovereign_score": sov.get("score"),
        "operational_grade": op.get("grade"),
        "credit_insurance_available": op.get("credit_insurance_available"),
        "note": (
            f"Risque {full['risk_class']} ({full['risk_ratio']}/100, 100 = risque "
            "minimal) — composite notations souveraines × évaluation opérationnelle "
            "type assurance-crédit. Détail : GET /api/reports/risk-ratio/"
            f"{full['country_iso3']}"
        ),
    }
