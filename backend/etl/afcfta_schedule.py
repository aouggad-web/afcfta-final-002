"""
afcfta_schedule.py
Schéma officiel de démantèlement tarifaire ZLECAf
Source: Annexe 1, Protocole sur le Commerce des Marchandises — Union Africaine (2018)
Entrée en vigueur: 1er janvier 2021 (Année 1)

Modalités officielles:
  Pays non-PMA:
    Catégorie A (90% des lignes): 0% en 5 ans — réductions linéaires annuelles
    Catégorie B (7% — sensibles):  0% en 10 ans — réductions linéaires annuelles
    Catégorie C (3% — exclus):    Pas de réduction
    Catégorie D (déjà à 0%):      Consolidé à 0% immédiatement

  Pays PMA (LDC):
    Catégorie A (90% des lignes): 0% en 10 ans — réductions linéaires annuelles
    Catégorie B (7% — sensibles):  0% en 13 ans — réductions linéaires annuelles
    Catégorie C (3% — exclus):    Pas de réduction
    Catégorie D (déjà à 0%):      Consolidé à 0% immédiatement
"""

from __future__ import annotations

from datetime import date
from typing import Dict, List, Optional

# ---------------------------------------------------------------------------
# Constantes officielles
# ---------------------------------------------------------------------------
AFCFTA_EIF_YEAR = 2021  # Année 1 du calendrier ZLECAf
CURRENT_YEAR = date.today().year
CURRENT_IMPLEMENTATION_YEAR = max(1, CURRENT_YEAR - AFCFTA_EIF_YEAR + 1)

# Catégories officielles (Annexe 1, Article 4)
CAT_A = "A"  # 90% des lignes — libéralisation normale
CAT_B = "B"  # 7% des lignes — produits sensibles
CAT_C = "C"  # 3% des lignes — produits exclus (pas de réduction)
CAT_D = "D"  # Lignes déjà à 0% — consolidées immédiatement

# Durées de réduction (en années) — Annexe 1, Article 6
REDUCTION_YEARS: Dict[str, Dict[str, int]] = {
    "non_ldc": {CAT_A: 5, CAT_B: 10, CAT_C: 0, CAT_D: 0},
    "ldc": {CAT_A: 10, CAT_B: 13, CAT_C: 0, CAT_D: 0},
}

# ---------------------------------------------------------------------------
# PMA africains (LDC) — liste officielle UA/CNUCED 2024
# ---------------------------------------------------------------------------
LDC_COUNTRIES: frozenset = frozenset(
    {
        "BEN",
        "BFA",
        "BDI",
        "CAF",
        "TCD",
        "COM",
        "COD",
        "DJI",
        "ERI",
        "ETH",
        "GMB",
        "GIN",
        "GNB",
        "LSO",
        "LBR",
        "MDG",
        "MWI",
        "MLI",
        "MRT",
        "MOZ",
        "NER",
        "RWA",
        "STP",
        "SEN",
        "SLE",
        "SOM",
        "SSD",
        "SDN",
        "TZA",
        "TGO",
        "UGA",
        "ZMB",
    }
)

# ---------------------------------------------------------------------------
# Classification des chapitres HS par catégorie ZLECAf
# Basée sur les listes d'offres soumises à la Secrétariat ZLECAf
# Catégorie B = produits sensibles communs à la majorité des États membres
# Catégorie C = produits exclus déclarés par au moins 60% des membres
# ---------------------------------------------------------------------------
# Catégorie B — Sensibles (réduction allongée)
_SENSITIVE_CHAPTERS = frozenset(
    {
        "01",
        "02",
        "03",
        "04",  # Animaux vivants, viandes, poissons, produits laitiers
        "10",
        "11",  # Céréales, farines
        "17",  # Sucres
        "22",
        "24",  # Boissons, tabac
        "27",  # Combustibles/pétrole (sensible pour pays producteurs)
        "50",
        "51",
        "52",
        "53",  # Textiles naturels
        "61",
        "62",  # Vêtements confectionnés
        "64",  # Chaussures
        "72",
        "73",  # Acier
        "87",  # Véhicules automobiles
    }
)

# Catégorie C — Exclus (aucune réduction)
_EXCLUDED_CHAPTERS = frozenset(
    {
        "93",  # Armes et munitions
        "30",  # Médicaments essentiels (souveraineté sanitaire, certains pays)
    }
)

# Catégorie D — Déjà à 0% NPF (consolidés)
_ZERO_RATE_CHAPTERS = frozenset(
    {
        "84",
        "85",  # Machines et équipements électriques (souvent 0% pour certains pays)
    }
)


def classify_hs6(country_iso3: str, hs6: str, npf_rate: float) -> str:
    """
    Classifie un code HS6 dans sa catégorie ZLECAf officielle.
    La classification réelle vient des listes d'offres nationales soumises
    au Secrétariat ZLECAf — cette fonction est la meilleure approximation
    disponible en l'absence de l'accès complet aux listes d'offres.
    """
    if npf_rate == 0.0:
        return CAT_D

    chapter = hs6[:2].zfill(2)

    if chapter in _EXCLUDED_CHAPTERS:
        return CAT_C

    if chapter in _SENSITIVE_CHAPTERS:
        return CAT_B

    return CAT_A


# ---------------------------------------------------------------------------
# Calcul du calendrier annuel officiel
# ---------------------------------------------------------------------------
def compute_annual_schedule(
    npf_rate: float,
    category: str,
    is_ldc: bool,
) -> List[Dict]:
    """
    Calcule le calendrier annuel de réduction tarifaire selon l'Annexe 1.

    Retourne une liste de dicts:
      [{year: 1, calendar_year: 2021, rate: X, reduction_pct: Y}, ...]

    Règle de réduction (Annexe 1, Article 6):
      Réductions linéaires égales annuelles jusqu'à 0%.
      Pour Catégorie A non-LDC (5 ans):
        Réduction annuelle = NPF / 5
        Année 1: NPF - (NPF/5) × 1
        ...
        Année 5: 0%
    """
    group = "ldc" if is_ldc else "non_ldc"
    years = REDUCTION_YEARS[group].get(category, 0)

    # Catégorie D ou NPF déjà nul: immédiatement à 0%
    if category == CAT_D or npf_rate == 0.0:
        return [
            {
                "year": 0,
                "calendar_year": AFCFTA_EIF_YEAR,
                "rate": 0.0,
                "reduction_pct": 100.0,
                "category": category,
            }
        ]

    # Catégorie C: aucune réduction
    if category == CAT_C or years == 0:
        schedule = []
        for y in range(0, 16):
            schedule.append(
                {
                    "year": y,
                    "calendar_year": AFCFTA_EIF_YEAR + y,
                    "rate": round(npf_rate, 2),
                    "reduction_pct": 0.0,
                    "category": category,
                }
            )
        return schedule

    # Catégories A et B: réductions linéaires annuelles
    annual_reduction = npf_rate / years
    schedule = []

    # Année 0 = taux NPF (avant ZLECAf ou année d'entrée en vigueur)
    schedule.append(
        {
            "year": 0,
            "calendar_year": AFCFTA_EIF_YEAR - 1,  # 2020 = avant EIV
            "rate": round(npf_rate, 2),
            "reduction_pct": 0.0,
            "category": category,
        }
    )

    for y in range(1, years + 1):
        rate = max(0.0, npf_rate - annual_reduction * y)
        schedule.append(
            {
                "year": y,
                "calendar_year": AFCFTA_EIF_YEAR + y - 1,
                "rate": round(rate, 2),
                "reduction_pct": (
                    round((npf_rate - rate) / npf_rate * 100, 1) if npf_rate > 0 else 100.0
                ),
                "category": category,
            }
        )

    # Années après la fin du calendrier: taux = 0%
    last_year = years
    for y in range(last_year + 1, 16):
        schedule.append(
            {
                "year": y,
                "calendar_year": AFCFTA_EIF_YEAR + y - 1,
                "rate": 0.0,
                "reduction_pct": 100.0,
                "category": category,
            }
        )

    return schedule


def get_current_zlecaf_rate(
    npf_rate: float,
    category: str,
    is_ldc: bool,
    implementation_year: Optional[int] = None,
) -> float:
    """Retourne le taux ZLECAf applicable aujourd'hui."""
    year = implementation_year or CURRENT_IMPLEMENTATION_YEAR
    schedule = compute_annual_schedule(npf_rate, category, is_ldc)
    for entry in schedule:
        if entry["year"] == year:
            return entry["rate"]
    # Si au-delà du calendrier → 0 (sauf Cat C)
    return npf_rate if category == CAT_C else 0.0


# ---------------------------------------------------------------------------
# API publique principale
# ---------------------------------------------------------------------------
def get_dismantlement_schedule(
    country_iso3: str,
    hs6: str,
    npf_rate: float,
    category: Optional[str] = None,
) -> Dict:
    """
    Retourne le schéma complet de démantèlement pour un couple pays/HS6.

    Args:
        country_iso3: Code ISO3 du pays de destination
        hs6:          Code HS6 (6 chiffres)
        npf_rate:     Taux NPF (droit de douane normal) en %
        category:     Catégorie ZLECAf (A/B/C/D). Si None, calculée automatiquement.

    Returns:
        {
          country_iso3, hs6, npf_rate, category, is_ldc,
          current_year, current_rate, target_year, target_rate,
          schedule: [{year, calendar_year, rate, reduction_pct, category}]
        }
    """
    is_ldc = country_iso3 in LDC_COUNTRIES
    cat = category or classify_hs6(country_iso3, hs6, npf_rate)

    schedule = compute_annual_schedule(npf_rate, cat, is_ldc)

    current_year = CURRENT_IMPLEMENTATION_YEAR
    current_entry = next((e for e in schedule if e["year"] == current_year), schedule[-1])

    group = "ldc" if is_ldc else "non_ldc"
    total_years = REDUCTION_YEARS[group].get(cat, 0)
    target_year = AFCFTA_EIF_YEAR + total_years - 1 if total_years > 0 else None

    return {
        "country_iso3": country_iso3,
        "hs6": hs6,
        "npf_rate": npf_rate,
        "category": cat,
        "category_label_fr": _category_label(cat, "fr"),
        "category_label_en": _category_label(cat, "en"),
        "is_ldc": is_ldc,
        "eif_year": AFCFTA_EIF_YEAR,
        "current_implementation_year": current_year,
        "current_calendar_year": CURRENT_YEAR,
        "current_zlecaf_rate": current_entry["rate"],
        "reduction_achieved_pct": current_entry["reduction_pct"],
        "target_rate": 0.0 if cat != CAT_C else npf_rate,
        "target_calendar_year": target_year,
        "fully_liberalized": current_entry["rate"] == 0.0 and cat != CAT_C,
        "schedule": schedule,
    }


def compute_impact_projection(
    npf_rate: float,
    category: str,
    is_ldc: bool,
    trade_value: float,
) -> List[Dict]:
    """
    Projette l'économie de droits de douane année par année pour un flux
    commercial récurrent de ``trade_value`` (USD) sur un produit donné.

    Pour chaque année du calendrier de démantèlement:
      droit NPF        = trade_value × npf_rate / 100   (constant)
      droit ZLECAf     = trade_value × rate(année) / 100
      économie         = droit NPF − droit ZLECAf
      économie cumulée = somme des économies annuelles

    Hypothèse: même valeur échangée chaque année (flux récurrent), ce qui rend
    le cumul interprétable comme l'économie totale sur la période de transition.
    """
    schedule = compute_annual_schedule(npf_rate, category, is_ldc)
    duty_npf = trade_value * npf_rate / 100.0
    cumulative = 0.0
    rows: List[Dict] = []
    for entry in schedule:
        duty_zlecaf = trade_value * entry["rate"] / 100.0
        saving = duty_npf - duty_zlecaf
        cumulative += saving
        rows.append(
            {
                "year": entry["year"],
                "calendar_year": entry["calendar_year"],
                "zlecaf_rate": entry["rate"],
                "duty_npf": round(duty_npf, 2),
                "duty_zlecaf": round(duty_zlecaf, 2),
                "annual_saving": round(saving, 2),
                "cumulative_saving": round(cumulative, 2),
            }
        )
    return rows


def _category_label(cat: str, lang: str) -> str:
    labels = {
        CAT_A: {
            "fr": "Catégorie A — Libéralisation normale (90% des lignes)",
            "en": "Category A — Standard liberalization (90% of lines)",
        },
        CAT_B: {
            "fr": "Catégorie B — Produits sensibles (7% des lignes)",
            "en": "Category B — Sensitive products (7% of lines)",
        },
        CAT_C: {
            "fr": "Catégorie C — Produits exclus (3% des lignes)",
            "en": "Category C — Excluded products (3% of lines)",
        },
        CAT_D: {
            "fr": "Catégorie D — Déjà en franchise (0% NPF)",
            "en": "Category D — Already duty-free (0% MFN)",
        },
    }
    return labels.get(cat, {}).get(lang, cat)
