"""
Country risk assessment for AfCFTA commercial operations.

Risk ratings follow the Coface / OECD country risk classification conventions:
  A1 – Very low risk
  A2 – Low risk
  A3 – Satisfactory risk
  A4 – Acceptable risk
  B  – Uncertain risk
  C  – High risk
  D  – Very high risk

Forex risk, political risk and transfer risk use: low | moderate | high | very_high
"""

from typing import Dict, List, Optional
from .models import CountryRiskProfile

# ---------------------------------------------------------------------------
# RISK PROFILES
# ---------------------------------------------------------------------------

RISK_PROFILES: Dict[str, CountryRiskProfile] = {

    # ── NORTH AFRICA ──────────────────────────────────────────────────────────
    "MA": CountryRiskProfile(
        country_code="MA", country_name="Maroc",
        country_risk_rating="A4",
        forex_risk="moderate",
        political_risk="low",
        transfer_risk="moderate",
        recommended_instruments=["LC_IRREVOCABLE", "DOC_COLLECTION_DP", "BANK_GUARANTEE_PERFORMANCE"],
        credit_insurance_available=True,
        max_exposure_usd=5_000_000,
        notes=(
            "Risque modéré lié aux restrictions de change (dirham non convertible). "
            "Risque pays acceptable. Assurance-crédit disponible (Coface, SMAEX)."
        ),
    ),
    "DZ": CountryRiskProfile(
        country_code="DZ", country_name="Algérie",
        country_risk_rating="B",
        forex_risk="high",
        political_risk="moderate",
        transfer_risk="high",
        recommended_instruments=["LC_CONFIRMED", "BANK_GUARANTEE_ADVANCE"],
        credit_insurance_available=True,
        max_exposure_usd=2_000_000,
        notes=(
            "Risque de change élevé (dinar non convertible). "
            "Délais de paiement longs. Crédit documentaire confirmé recommandé."
        ),
    ),
    "TN": CountryRiskProfile(
        country_code="TN", country_name="Tunisie",
        country_risk_rating="B",
        forex_risk="moderate",
        political_risk="moderate",
        transfer_risk="moderate",
        recommended_instruments=["LC_IRREVOCABLE", "DOC_COLLECTION_DP", "EXPORT_FACTORING"],
        credit_insurance_available=True,
        max_exposure_usd=3_000_000,
        notes=(
            "Économie en transition post-2011. Risque modéré. "
            "Assurance-crédit COFACE et COTUNACE disponible."
        ),
    ),
    "EG": CountryRiskProfile(
        country_code="EG", country_name="Égypte",
        country_risk_rating="B",
        forex_risk="moderate",
        political_risk="moderate",
        transfer_risk="moderate",
        recommended_instruments=["LC_IRREVOCABLE", "DOC_COLLECTION_DP"],
        credit_insurance_available=True,
        max_exposure_usd=5_000_000,
        notes=(
            "Grande économie africaine avec risque modéré. "
            "Stabilité améliorée après réformes 2016-2017."
        ),
    ),
    "LY": CountryRiskProfile(
        country_code="LY", country_name="Libye",
        country_risk_rating="D",
        forex_risk="very_high",
        political_risk="very_high",
        transfer_risk="very_high",
        recommended_instruments=["LC_CONFIRMED", "STANDBY_LC"],
        credit_insurance_available=False,
        max_exposure_usd=500_000,
        notes="Situation politique instable. Risque très élevé. Éviter les transactions importantes.",
    ),

    # ── WEST AFRICA ──────────────────────────────────────────────────────────
    "NG": CountryRiskProfile(
        country_code="NG", country_name="Nigeria",
        country_risk_rating="C",
        forex_risk="high",
        political_risk="moderate",
        transfer_risk="high",
        recommended_instruments=["LC_CONFIRMED", "LC_IRREVOCABLE", "BANK_GUARANTEE_ADVANCE"],
        credit_insurance_available=True,
        max_exposure_usd=2_000_000,
        notes=(
            "Plus grande économie africaine mais risque de change élevé. "
            "Naira volatile. LC confirmé recommandé pour les exportateurs. "
            "Form M obligatoire côté importateur."
        ),
    ),
    "GH": CountryRiskProfile(
        country_code="GH", country_name="Ghana",
        country_risk_rating="B",
        forex_risk="moderate",
        political_risk="low",
        transfer_risk="moderate",
        recommended_instruments=["LC_IRREVOCABLE", "DOC_COLLECTION_DP", "SUPPLY_CHAIN_FINANCE"],
        credit_insurance_available=True,
        max_exposure_usd=3_000_000,
        notes=(
            "Démocratie stable. Crise dette 2022-2023 en cours de résolution. "
            "Risque modéré. Assurance-crédit disponible."
        ),
    ),
    "CI": CountryRiskProfile(
        country_code="CI", country_name="Côte d'Ivoire",
        country_risk_rating="B",
        forex_risk="low",
        political_risk="moderate",
        transfer_risk="low",
        recommended_instruments=["DOC_COLLECTION_DP", "LC_IRREVOCABLE", "SUPPLY_CHAIN_FINANCE"],
        credit_insurance_available=True,
        max_exposure_usd=5_000_000,
        notes=(
            "Franc CFA indexé EUR = risque de change très faible. "
            "Hub économique d'Afrique de l'Ouest. Assurance-crédit Coface."
        ),
    ),
    "SN": CountryRiskProfile(
        country_code="SN", country_name="Sénégal",
        country_risk_rating="B",
        forex_risk="low",
        political_risk="low",
        transfer_risk="low",
        recommended_instruments=["DOC_COLLECTION_DP", "LC_IRREVOCABLE"],
        credit_insurance_available=True,
        max_exposure_usd=3_000_000,
        notes=(
            "Pays stable avec franc CFA. Risque global faible. "
            "Économie portée par le pétrole (depuis 2024)."
        ),
    ),
    "ML": CountryRiskProfile(
        country_code="ML", country_name="Mali",
        country_risk_rating="C",
        forex_risk="low",
        political_risk="high",
        transfer_risk="moderate",
        recommended_instruments=["LC_CONFIRMED", "BANK_GUARANTEE_ADVANCE"],
        credit_insurance_available=False,
        max_exposure_usd=500_000,
        notes="Instabilité politique post-coup (2021). Risque élevé malgré franc CFA stable.",
    ),
    "BF": CountryRiskProfile(
        country_code="BF", country_name="Burkina Faso",
        country_risk_rating="C",
        forex_risk="low",
        political_risk="high",
        transfer_risk="moderate",
        recommended_instruments=["LC_CONFIRMED"],
        credit_insurance_available=False,
        max_exposure_usd=300_000,
        notes="Instabilité sécuritaire et politique. Risque pays élevé.",
    ),

    # ── EAST AFRICA ──────────────────────────────────────────────────────────
    "KE": CountryRiskProfile(
        country_code="KE", country_name="Kenya",
        country_risk_rating="A4",
        forex_risk="moderate",
        political_risk="low",
        transfer_risk="low",
        recommended_instruments=["DOC_COLLECTION_DP", "LC_IRREVOCABLE", "SUPPLY_CHAIN_FINANCE"],
        credit_insurance_available=True,
        max_exposure_usd=5_000_000,
        notes=(
            "Hub financier d'Afrique de l'Est. Risque global faible. "
            "Shilling librement convertible. Assurance-crédit disponible."
        ),
    ),
    "ET": CountryRiskProfile(
        country_code="ET", country_name="Éthiopie",
        country_risk_rating="C",
        forex_risk="very_high",
        political_risk="high",
        transfer_risk="very_high",
        recommended_instruments=["LC_CONFIRMED", "BANK_GUARANTEE_ADVANCE"],
        credit_insurance_available=False,
        max_exposure_usd=500_000,
        notes=(
            "Pénuries de devises chroniques. Conflit interne (Tigray). "
            "Risque de transfert très élevé. LC confirmé obligatoire."
        ),
    ),
    "TZ": CountryRiskProfile(
        country_code="TZ", country_name="Tanzanie",
        country_risk_rating="B",
        forex_risk="moderate",
        political_risk="low",
        transfer_risk="moderate",
        recommended_instruments=["LC_IRREVOCABLE", "DOC_COLLECTION_DP"],
        credit_insurance_available=True,
        max_exposure_usd=3_000_000,
        notes="Pays stable. Économie en croissance. Risque modéré.",
    ),

    # ── SOUTHERN AFRICA ──────────────────────────────────────────────────────
    "ZA": CountryRiskProfile(
        country_code="ZA", country_name="Afrique du Sud",
        country_risk_rating="A4",
        forex_risk="moderate",
        political_risk="moderate",
        transfer_risk="low",
        recommended_instruments=["DOC_COLLECTION_DP", "SUPPLY_CHAIN_FINANCE", "LC_IRREVOCABLE"],
        credit_insurance_available=True,
        max_exposure_usd=10_000_000,
        notes=(
            "Économie la plus développée d'Afrique subsaharienne. "
            "Risque modéré lié à l'instabilité politique interne (ANC). "
            "Rand volatile mais marchés financiers profonds."
        ),
    ),
    "AO": CountryRiskProfile(
        country_code="AO", country_name="Angola",
        country_risk_rating="C",
        forex_risk="very_high",
        political_risk="moderate",
        transfer_risk="high",
        recommended_instruments=["LC_CONFIRMED", "BANK_GUARANTEE_ADVANCE"],
        credit_insurance_available=True,
        max_exposure_usd=1_000_000,
        notes=(
            "Kwanza non convertible. Dépendance pétrolière. "
            "Risque de change très élevé. Réformes en cours."
        ),
    ),
    "ZM": CountryRiskProfile(
        country_code="ZM", country_name="Zambie",
        country_risk_rating="C",
        forex_risk="high",
        political_risk="moderate",
        transfer_risk="high",
        recommended_instruments=["LC_IRREVOCABLE", "BANK_GUARANTEE_ADVANCE"],
        credit_insurance_available=True,
        max_exposure_usd=1_000_000,
        notes=(
            "Restructuration de la dette en cours (2021-2023). "
            "Risque élevé. Kwacha volatile."
        ),
    ),
    "ZW": CountryRiskProfile(
        country_code="ZW", country_name="Zimbabwe",
        country_risk_rating="D",
        forex_risk="very_high",
        political_risk="high",
        transfer_risk="very_high",
        recommended_instruments=["LC_CONFIRMED", "CASH_IN_ADVANCE"],
        credit_insurance_available=False,
        max_exposure_usd=200_000,
        notes=(
            "Hyperinflation chronique. Dollar zimbabwéen instable. "
            "Risque très élevé. LC confirmé + paiement d'avance recommandés."
        ),
    ),
}

_DEFAULT_RISK = CountryRiskProfile(
    country_code="XX", country_name="Unknown",
    country_risk_rating="B",
    forex_risk="moderate",
    political_risk="moderate",
    transfer_risk="moderate",
    recommended_instruments=["LC_IRREVOCABLE"],
    credit_insurance_available=True,
    notes="Profil par défaut – données détaillées non disponibles.",
)


# ---------------------------------------------------------------------------
# PUBLIC HELPERS
# ---------------------------------------------------------------------------

def get_country_risk(country_code: str) -> CountryRiskProfile:
    """Return risk profile for a country (ISO2). Falls back to default."""
    profile = RISK_PROFILES.get(country_code.upper())
    if profile is not None:
        return profile
    return _DEFAULT_RISK.model_copy(update={"country_code": country_code.upper()})


def assess_transaction_risk(
    country_code: str,
    amount_usd: float,
    transaction_type: str = "export",
) -> dict:
    """
    Assess the risk of a specific transaction and provide actionable recommendations.

    Args:
        country_code: ISO2 code of the trade partner country.
        amount_usd: Transaction value in USD.
        transaction_type: "import" or "export".

    Returns:
        dict with risk assessment and recommendations.
    """
    profile = get_country_risk(country_code)
    risk_score = _compute_risk_score(profile, amount_usd)

    alert_level = "green"
    if risk_score >= 7:
        alert_level = "red"
    elif risk_score >= 5:
        alert_level = "orange"

    return {
        "country_code": country_code.upper(),
        "country_name": profile.country_name,
        "overall_risk_rating": profile.country_risk_rating,
        "forex_risk": profile.forex_risk,
        "political_risk": profile.political_risk,
        "transfer_risk": profile.transfer_risk,
        "risk_score": risk_score,
        "alert_level": alert_level,
        "transaction_type": transaction_type,
        "amount_usd": amount_usd,
        "recommended_instruments": profile.recommended_instruments,
        "credit_insurance_available": profile.credit_insurance_available,
        "max_recommended_exposure_usd": profile.max_exposure_usd,
        "exposure_warning": (
            amount_usd > (profile.max_exposure_usd or float("inf"))
        ),
        "notes": profile.notes,
    }


def _compute_risk_score(profile: CountryRiskProfile, amount_usd: float) -> int:
    """Compute a simple 0-10 risk score from the profile."""
    rating_score = {
        "A1": 1, "A2": 2, "A3": 3, "A4": 4, "B": 5, "C": 7, "D": 9,
    }
    level_score = {"low": 0, "moderate": 1, "high": 2, "very_high": 3}

    base = rating_score.get(profile.country_risk_rating, 5)
    base += level_score.get(profile.transfer_risk, 1)

    if profile.max_exposure_usd and amount_usd > profile.max_exposure_usd:
        base += 1

    return min(base, 10)
