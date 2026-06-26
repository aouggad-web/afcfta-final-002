"""
Calendrier de démantèlement tarifaire ZLECAf applicable à l'IMPORTATION en
Algérie (taux DD, droit de douane uniquement).

Source authentique : Circulaire DGD n°482/DGD/SP/D.042/24 du 22/10/2024
« Mise en œuvre de l'Accord portant création de la ZLECAf », et son
« Schéma général du traitement tarifaire à l'importation des produits dans
le cadre de la ZLECAf » + listes des concessions tarifaires algériennes
(A), (B), (C).

Points clés (sinon le taux ZLECAf générique du moteur serait faux pour
l'Algérie) :
  - Seuls 9 pays partenaires ont déclenché l'application effective et
    réciproque de l'accord avec l'Algérie à ce jour (liste mise à jour
    périodiquement par le ministère du Commerce) : les autres membres de
    la ZLECAf restent au droit commun à l'import en Algérie.
  - Le calendrier dépend de la liste du produit (A/B/C) ET du régime
    appliqué au pays partenaire (standard ou "principe de réciprocité"
    pour les pays non-PMA appliquant eux-mêmes le calendrier PMA).
  - Liste (C) : exclue du démantèlement, toujours au droit commun.
  - Certaines positions (textiles, véhicules) sont gelées tant que leurs
    règles d'origine détaillées ne sont pas arrêtées : droit commun.
"""

from __future__ import annotations

import datetime
import json
from pathlib import Path
from typing import Optional, Tuple

DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "zlecaf_dza"

with open(DATA_DIR / "list_b_codes.json", encoding="utf-8") as f:
    LIST_B_CODES = frozenset(json.load(f))
with open(DATA_DIR / "list_c_codes.json", encoding="utf-8") as f:
    LIST_C_CODES = frozenset(json.load(f))

# Taux DD de base 2019 (figé à l'entrée en vigueur de l'Accord, art. 23),
# par code SH10 de la liste (B) — source : tableau détaillé « Liste (B) :
# produits concernés par le démantèlement tarifaire pendant 13 ans dans le
# cadre de l'application du principe de réciprocité ». Ce taux de base est
# une propriété du produit (indépendante du calendrier standard/réciprocité
# appliqué au partenaire) et peut différer du taux DD courant figurant dans
# la nomenclature tarifaire générale (ex. : 0201101100 — viande de veau —
# taux de base ZLECAf 30%, taux DD courant 5% suite à une réduction
# postérieure à 2019) : il prévaut donc sur tout taux normal transmis par
# l'appelant pour les positions qu'il couvre.
with open(DATA_DIR / "list_b_base_rates.json", encoding="utf-8") as f:
    LIST_B_BASE_RATES_2019 = {k: v / 100.0 for k, v in json.load(f).items()}

# Pays ayant déclenché l'application effective et réciproque de la ZLECAf
# avec l'Algérie (circulaire 482/2024, partie I).
ACTIVE_PARTNERS = frozenset({"ZAF", "CMR", "EGY", "GHA", "KEN", "MUS", "RWA", "TZA", "TUN"})

# Pays en développement (non-PMA) membres de CER appliquant le calendrier
# PMA : l'Algérie leur applique le "principe de réciprocité" (calendrier
# plus long, partie II-3 de la circulaire).
RECIPROCITY_PARTNERS = frozenset(
    {
        "ZAF",
        "BWA",
        "CMR",
        "CPV",
        "COG",
        "CIV",
        "SWZ",
        "GAB",
        "GHA",
        "GNQ",
        "KEN",
        "NGA",
        "NAM",
    }
)

# Positions dont les règles d'origine détaillées ne sont pas encore
# arrêtées : admises au droit commun (circulaire, partie III-1).
FROZEN_HEADINGS = (
    ("5111", "5113"),
    ("5204", "5212"),
    ("5309", "5309"),
    ("5407", "5408"),
    ("5512", "5516"),
    ("5801", "5804"),
    ("5806", "5806"),
    ("5810", "5810"),
    ("6001", "6017"),  # chapitre 60 (bonneterie) entier
    ("6301", "6306"),
    ("8701", "8701"),
    ("8703", "8708"),
    ("8710", "8712"),
)

# Facteur = part du droit de base encore appliquée (0.0 = exonération totale).
_STANDARD_A = {2021: 0.8, 2022: 0.6, 2023: 0.4, 2024: 0.2}  # >=2025 -> 0.0
_STANDARD_B = {2026: 0.8, 2027: 0.6, 2028: 0.4, 2029: 0.2}  # 2021-25 -> 1.0 ; >=2030 -> 0.0
_RECIP_A = {
    2021: 0.9,
    2022: 0.8,
    2023: 0.7,
    2024: 0.6,
    2025: 0.5,
    2026: 0.4,
    2027: 0.3,
    2028: 0.2,
    2029: 0.1,
}  # >=2030 -> 0.0
_RECIP_B = {
    2026: 0.875,
    2027: 0.75,
    2028: 0.625,
    2029: 0.5,
    2030: 0.375,
    2031: 0.25,
    2032: 0.125,
}  # 2021-25 -> 1.0 ; >=2033 -> 0.0


def _heading(hs_code_clean: str) -> str:
    return hs_code_clean[:4]


def is_frozen(hs_code_clean: str) -> bool:
    h = _heading(hs_code_clean)
    return any(lo <= h <= hi for lo, hi in FROZEN_HEADINGS)


def tariff_list(hs_code_clean: str) -> str:
    """Liste (A), (B) ou (C) d'une position. (A) est la liste par défaut
    (90% des lignes), elle n'est pas énumérée explicitement par la source."""
    code10 = hs_code_clean.ljust(10, "0")[:10]
    if code10 in LIST_C_CODES:
        return "C"
    if code10 in LIST_B_CODES:
        return "B"
    return "A"


def _factor_standard(lst: str, year: int) -> float:
    if lst == "C":
        return 1.0
    if lst == "A":
        if year < 2021:
            return 1.0
        if year >= 2025:
            return 0.0
        return _STANDARD_A[year]
    if lst == "B":
        if year < 2026:
            return 1.0
        if year >= 2030:
            return 0.0
        return _STANDARD_B[year]
    raise ValueError(lst)


def _factor_reciprocity(lst: str, year: int) -> float:
    if lst == "C":
        return 1.0
    if lst == "A":
        if year < 2021:
            return 1.0
        if year >= 2030:
            return 0.0
        return _RECIP_A[year]
    if lst == "B":
        if year < 2026:
            return 1.0
        if year >= 2033:
            return 0.0
        return _RECIP_B[year]
    raise ValueError(lst)


def compute_dza_zlecaf_rate(
    hs_code: str,
    origin_iso3: str,
    normal_rate: float,
    as_of: Optional[datetime.date] = None,
) -> Tuple[Optional[float], Optional[str]]:
    """Taux DD ZLECAf à l'importation en Algérie pour un HS code / partenaire.

    Retourne (taux, libellé source), ou (None, None) si les paramètres sont
    insuffisants (laisser l'appelant garder son propre calcul générique).
    """
    if not origin_iso3 or normal_rate is None:
        return None, None
    origin = origin_iso3.upper()
    hs_clean = (hs_code or "").replace(".", "").replace(" ", "")
    if not hs_clean:
        return None, None

    if origin not in ACTIVE_PARTNERS:
        return normal_rate, (
            f"ZLECAf non encore activé pour {origin} à l'import en Algérie "
            f"(circulaire DGD 482/2024) — taux NPF appliqué"
        )

    year = (as_of or datetime.date.today()).year
    lst = tariff_list(hs_clean)

    if is_frozen(hs_clean):
        return normal_rate, f"Liste ({lst}) gelée — règles d'origine non finalisées (droit commun)"

    code10 = hs_clean.ljust(10, "0")[:10]
    base_rate = LIST_B_BASE_RATES_2019.get(code10, normal_rate) if lst == "B" else normal_rate
    base_label = " (taux de base 2019)" if lst == "B" and code10 in LIST_B_BASE_RATES_2019 else ""

    reciprocity = origin in RECIPROCITY_PARTNERS
    factor = _factor_reciprocity(lst, year) if reciprocity else _factor_standard(lst, year)
    rate = round(base_rate * factor, 6)
    schedule_label = "réciprocité" if reciprocity else "standard"
    return rate, f"ZLECAf DZA — liste ({lst}){base_label}, calendrier {schedule_label}, {year}"


def daps_exempt(hs_code: str, origin_iso3: str) -> bool:
    """DAPS (Droit Additionnel Provisoire de Sauvegarde) exonéré pour les
    produits des listes (A) et (B) importés dans le cadre de la ZLECAf
    (circulaire 482/2024, partie II-2 : « Les produits objet de ces deux
    listes (A) et (B), importés dans le cadre de la ZLECAf, sont exonérés
    du [DAPS], conformément à l'article 2 de la loi de finances
    complémentaire pour 2018 »). Cette exonération est distincte du
    calendrier de démantèlement du DD (qui ne couvre que le taux DD) :
    elle ne s'applique qu'aux produits effectivement admis sous régime
    ZLECAf, donc à un partenaire actif et à une position non gelée."""
    if not origin_iso3 or origin_iso3.upper() not in ACTIVE_PARTNERS:
        return False
    hs_clean = (hs_code or "").replace(".", "").replace(" ", "")
    if not hs_clean or is_frozen(hs_clean):
        return False
    return tariff_list(hs_clean) in ("A", "B")
