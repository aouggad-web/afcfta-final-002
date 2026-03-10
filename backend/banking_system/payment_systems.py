"""
Regional and international payment systems covering Africa.
"""

from typing import List, Optional
from .models import PaymentSystem

# ---------------------------------------------------------------------------
# PAYMENT SYSTEMS CATALOGUE
# ---------------------------------------------------------------------------

PAYMENT_SYSTEMS: List[PaymentSystem] = [

    # ── INTERNATIONAL ────────────────────────────────────────────────────────
    PaymentSystem(
        code="SWIFT",
        name="SWIFT – Society for Worldwide Interbank Financial Telecommunication",
        type="swift",
        region="Global",
        member_countries=["ALL"],
        currency=None,
        operator="SWIFT (Belgium)",
        notes=(
            "Réseau international de messagerie interbancaire. "
            "Standard universel pour les virements internationaux. "
            "Tous les pays africains membres SWIFT."
        ),
    ),

    # ── WEST AFRICA ──────────────────────────────────────────────────────────
    PaymentSystem(
        code="WAMZ_RTGS",
        name="West African Monetary Zone – Real Time Gross Settlement",
        type="regional",
        region="West Africa (non-UEMOA)",
        member_countries=["GH", "GM", "GN", "LR", "NG", "SL"],
        currency="Multiple",
        operator="West African Monetary Institute (WAMI)",
        notes=(
            "Système de règlement brut en temps réel pour les pays WAMZ. "
            "Objectif : convergence monétaire et création d'une monnaie commune (Eco)."
        ),
    ),
    PaymentSystem(
        code="BCEAO_SICA",
        name="BCEAO – Système Interbancaire de Compensation Automatisée",
        type="regional",
        region="West Africa (UEMOA)",
        member_countries=["BJ", "BF", "CI", "GW", "ML", "NE", "SN", "TG"],
        currency="XOF",
        operator="BCEAO",
        notes=(
            "Compensation automatisée des virements et chèques en XOF "
            "au sein de l'espace UEMOA. Délai de règlement T+1."
        ),
    ),
    PaymentSystem(
        code="BCEAO_STAR",
        name="BCEAO – Système de Transfert Automatisé et de Règlement (STAR-UEMOA)",
        type="regional",
        region="West Africa (UEMOA)",
        member_countries=["BJ", "BF", "CI", "GW", "ML", "NE", "SN", "TG"],
        currency="XOF",
        operator="BCEAO",
        notes="RTGS de la zone UEMOA pour les règlements de gros montants. Règlement immédiat.",
    ),

    # ── CENTRAL AFRICA ───────────────────────────────────────────────────────
    PaymentSystem(
        code="GIMAC",
        name="Groupement Interbancaire Monétique de l'Afrique Centrale",
        type="regional",
        region="Central Africa (CEMAC)",
        member_countries=["CM", "CF", "TD", "CG", "GA", "GQ"],
        currency="XAF",
        operator="GIMAC",
        notes=(
            "Opérateur monétique central de la CEMAC. "
            "Gère les paiements par carte, mobile et les transferts interbancaires "
            "en zone CFA BEAC."
        ),
    ),
    PaymentSystem(
        code="BEAC_SYGMA",
        name="BEAC – Système de Gros Montants Automatisé (SYGMA)",
        type="regional",
        region="Central Africa (CEMAC)",
        member_countries=["CM", "CF", "TD", "CG", "GA", "GQ"],
        currency="XAF",
        operator="BEAC",
        notes="RTGS de la zone CEMAC pour les paiements de gros montants.",
    ),

    # ── EAST AFRICA ──────────────────────────────────────────────────────────
    PaymentSystem(
        code="EAPS",
        name="East African Payment System",
        type="regional",
        region="East Africa (EAC)",
        member_countries=["KE", "TZ", "UG", "RW", "BI", "SS"],
        currency="Multiple",
        operator="East African Community (EAC)",
        notes=(
            "Système de paiement en cours de déploiement pour la zone EAC. "
            "Objectif : éliminer les conversions SWIFT entre pays EAC."
        ),
    ),
    PaymentSystem(
        code="KEPSS",
        name="Kenya Electronic Payment and Settlement System",
        type="regional",
        region="East Africa",
        member_countries=["KE"],
        currency="KES",
        operator="Central Bank of Kenya",
        notes="RTGS du Kenya. Hub régional pour les transferts EAC.",
    ),
    PaymentSystem(
        code="TISS",
        name="Tanzania Interbank Settlement System",
        type="regional",
        region="East Africa",
        member_countries=["TZ"],
        currency="TZS",
        operator="Bank of Tanzania",
        notes="RTGS de la Tanzanie.",
    ),

    # ── SOUTHERN AFRICA ──────────────────────────────────────────────────────
    PaymentSystem(
        code="SADC_RTGS",
        name="SADC – Integrated Regional Electronic Settlement System (SIRESS)",
        type="regional",
        region="Southern Africa (SADC)",
        member_countries=[
            "ZA", "BW", "LS", "NA", "SZ", "MZ", "ZM", "ZW",
            "MG", "MU", "TZ", "MW",
        ],
        currency="ZAR",
        operator="South African Reserve Bank (SARB) – settlement in ZAR",
        notes=(
            "RTGS régional SADC pour les règlements en ZAR. "
            "Permet aux banques SADC de régler en rands sans passer par SWIFT. "
            "Opérationnel depuis 2013."
        ),
    ),
    PaymentSystem(
        code="SAMOS",
        name="South African Multiple Option Settlement",
        type="regional",
        region="Southern Africa",
        member_countries=["ZA"],
        currency="ZAR",
        operator="South African Reserve Bank",
        notes="RTGS de l'Afrique du Sud. Principal hub de la zone SADC.",
    ),

    # ── NORTH AFRICA ─────────────────────────────────────────────────────────
    PaymentSystem(
        code="MAGHREB_PAYMENT",
        name="Système de Paiement Maghrébin (en cours)",
        type="regional",
        region="North Africa (UMA)",
        member_countries=["MA", "DZ", "TN", "LY", "MR"],
        currency="Multiple",
        operator="Union du Maghreb Arabe (UMA)",
        notes=(
            "Projet de système de paiement régional pour le Maghreb. "
            "En cours de développement – les échanges restent via SWIFT."
        ),
    ),

    # ── PAN-AFRICAN ───────────────────────────────────────────────────────────
    PaymentSystem(
        code="PAPSS",
        name="Pan-African Payment and Settlement System",
        type="regional",
        region="Pan-African (AfCFTA)",
        member_countries=list({"MA", "DZ", "TN", "EG", "NG", "GH", "CI", "SN",
                               "KE", "ET", "TZ", "ZA", "AO", "ZM"}),
        currency="Multiple",
        operator="Afreximbank / African Union",
        notes=(
            "Système de paiement pan-africain lancé en 2022 dans le cadre de la ZLECAf. "
            "Permet les paiements en devises locales entre pays africains "
            "sans passer par des devises tierces (USD/EUR). "
            "Objectif : réduire les coûts de transaction de 80%."
        ),
    ),

    # ── MOBILE MONEY ─────────────────────────────────────────────────────────
    PaymentSystem(
        code="MPESA",
        name="M-Pesa",
        type="mobile_money",
        region="East Africa",
        member_countries=["KE", "TZ", "UG", "RW", "ET", "MZ", "GH", "EG", "ZA"],
        currency="Multiple",
        operator="Safaricom / Vodacom",
        notes=(
            "Principale plateforme de mobile money en Afrique de l'Est. "
            "Transferts transfrontaliers disponibles KE-TZ-UG-RW. "
            "Paiements B2B limités – principalement B2C et C2C."
        ),
    ),
    PaymentSystem(
        code="MTN_MOMO",
        name="MTN Mobile Money (MoMo)",
        type="mobile_money",
        region="Pan-African",
        member_countries=["GH", "CI", "CM", "UG", "RW", "ZA", "NG", "BF", "BJ", "GN"],
        currency="Multiple",
        operator="MTN Group",
        notes=(
            "Réseau mobile money du groupe MTN présent dans 17 pays africains. "
            "Interopérabilité croissante avec d'autres opérateurs."
        ),
    ),
    PaymentSystem(
        code="ORANGE_MONEY",
        name="Orange Money",
        type="mobile_money",
        region="West & Central Africa",
        member_countries=["SN", "CI", "ML", "BF", "GN", "CM", "MG", "TN", "EG", "MA"],
        currency="Multiple",
        operator="Orange Group",
        notes="Mobile money du groupe Orange. Fort ancrage en Afrique francophone.",
    ),
    PaymentSystem(
        code="WAVE",
        name="Wave Mobile Money",
        type="mobile_money",
        region="West Africa",
        member_countries=["SN", "CI", "ML", "BF", "UG", "GN"],
        currency="XOF / UGX",
        operator="Wave (USA)",
        notes=(
            "Opérateur disruptif avec des frais très bas (1%). "
            "Fort développement en zone UEMOA depuis 2020."
        ),
    ),

    # ── DIGITAL PLATFORMS ────────────────────────────────────────────────────
    PaymentSystem(
        code="FLUTTERWAVE",
        name="Flutterwave",
        type="digital",
        region="Pan-African",
        member_countries=["NG", "GH", "KE", "ZA", "UG", "TZ", "CI", "MA", "EG", "SN"],
        currency="Multiple",
        operator="Flutterwave Inc. (Nigeria)",
        notes=(
            "Plateforme de paiement B2B et B2C panafricaine. "
            "Traite USD, EUR et devises locales. "
            "Intégration API pour le e-commerce et le commerce B2B."
        ),
    ),
    PaymentSystem(
        code="PAYSTACK",
        name="Paystack",
        type="digital",
        region="West Africa",
        member_countries=["NG", "GH", "ZA", "KE"],
        currency="Multiple",
        operator="Paystack (Nigeria) – filiale Stripe",
        notes="Plateforme de paiement en ligne. Acquisition par Stripe en 2020.",
    ),
]

# Indexed by code for quick lookup
_SYSTEMS_BY_CODE = {ps.code: ps for ps in PAYMENT_SYSTEMS}


# ---------------------------------------------------------------------------
# PUBLIC HELPERS
# ---------------------------------------------------------------------------

def get_payment_systems(country_code: Optional[str] = None) -> List[PaymentSystem]:
    """
    Return payment systems. If country_code is provided (ISO2),
    return only systems available in that country.
    """
    if country_code is None:
        return PAYMENT_SYSTEMS
    code = country_code.upper()
    return [
        ps for ps in PAYMENT_SYSTEMS
        if code in ps.member_countries or "ALL" in ps.member_countries
    ]


def get_regional_systems(region: Optional[str] = None) -> List[PaymentSystem]:
    """Return regional payment systems, optionally filtered by region name."""
    if region is None:
        return [ps for ps in PAYMENT_SYSTEMS if ps.type == "regional"]
    region_lower = region.lower()
    return [
        ps for ps in PAYMENT_SYSTEMS
        if ps.type == "regional" and region_lower in ps.region.lower()
    ]
