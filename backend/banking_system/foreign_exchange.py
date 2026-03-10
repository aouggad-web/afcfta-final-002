"""
Foreign-exchange control and domiciliation rules by country.

Covers the 14 phase-1 priority countries with full detail, and provides
a default liberal profile for the remaining African countries.
"""

from typing import Dict, Optional
from .models import DomiciliationRule, ForexRegulation, CountryForexProfile

# ---------------------------------------------------------------------------
# FOREX PROFILES – Phase-1 priority countries (detailed)
# ---------------------------------------------------------------------------

FOREX_PROFILES: Dict[str, CountryForexProfile] = {

    # ── MAROC ────────────────────────────────────────────────────────────────
    "MA": CountryForexProfile(
        country_code="MA", country_name="Maroc",
        central_bank_name="Bank Al-Maghrib",
        domiciliation=DomiciliationRule(
            required=True, conditional=False,
            threshold_usd=10_000,
            mandatory_documents=[
                "facture_commerciale",
                "contrat_commercial",
                "autorisation_office_changes",
                "titre_import_export",
            ],
            timeline_days=150,
            notes=(
                "La domiciliation est obligatoire pour tout règlement dépassant "
                "10 000 USD. L'Office des Changes délivre les autorisations "
                "préalables pour les transactions sensibles."
            ),
        ),
        forex_regulation=ForexRegulation(
            regulation_level="strict",
            prior_authorization_required=True,
            authorization_threshold_usd=10_000,
            declaration_threshold_usd=10_000,
            repatriation_deadline_days=150,
            penalties=(
                "Amendes jusqu'à 5× le montant non rapatrié + suspension "
                "des autorisations d'opérations de change."
            ),
            notes=(
                "Office des Changes (OC) contrôle toutes les opérations en devises. "
                "Le dirham n'est pas convertible hors frontières."
            ),
        ),
        authorized_currencies=["USD", "EUR", "GBP", "CHF", "JPY", "CAD"],
        restricted_operations=["capital_account_transfers", "speculative_forex"],
        special_regimes=["CFC_Casablanca_Finance_City", "zones_franches"],
    ),

    # ── ALGÉRIE ──────────────────────────────────────────────────────────────
    "DZ": CountryForexProfile(
        country_code="DZ", country_name="Algérie",
        central_bank_name="Banque d'Algérie",
        domiciliation=DomiciliationRule(
            required=True, conditional=False,
            threshold_usd=0,
            mandatory_documents=[
                "facture_pro_forma",
                "contrat_commercial",
                "titre_importation",
                "domiciliation_bancaire",
            ],
            timeline_days=180,
            notes=(
                "Toute importation doit être domiciliée auprès d'une banque "
                "primaire agréée. Pas de seuil minimal : la domiciliation est "
                "systématique dès le premier dinar."
            ),
        ),
        forex_regulation=ForexRegulation(
            regulation_level="strict",
            prior_authorization_required=True,
            authorization_threshold_usd=0,
            declaration_threshold_usd=1_000,
            repatriation_deadline_days=180,
            penalties=(
                "Infractions au code pénal : amende + emprisonnement possible. "
                "Gel des avoirs et suspension des autorisations bancaires."
            ),
            notes=(
                "Le dinar algérien est non convertible. Le règlement des "
                "importations se fait exclusivement par crédit documentaire "
                "ou remise documentaire via une banque agréée."
            ),
        ),
        authorized_currencies=["USD", "EUR", "GBP"],
        restricted_operations=[
            "cash_payments_import", "capital_account_transfers",
            "crypto_transactions",
        ],
        special_regimes=["zones_franches_exportation"],
    ),

    # ── TUNISIE ───────────────────────────────────────────────────────────────
    "TN": CountryForexProfile(
        country_code="TN", country_name="Tunisie",
        central_bank_name="Banque Centrale de Tunisie",
        domiciliation=DomiciliationRule(
            required=True, conditional=False,
            threshold_usd=2_000,
            mandatory_documents=[
                "facture_commerciale",
                "declaration_importation",
                "attestation_banque_domiciliataire",
            ],
            timeline_days=90,
            notes=(
                "Domiciliation obligatoire au-delà de 2 000 USD. "
                "Les entreprises totalement exportatrices bénéficient d'un "
                "régime simplifié."
            ),
        ),
        forex_regulation=ForexRegulation(
            regulation_level="moderate",
            prior_authorization_required=False,
            declaration_threshold_usd=2_000,
            repatriation_deadline_days=90,
            penalties="Amende administrative + pénalités de retard (1% par mois).",
            notes=(
                "Libéralisation progressive depuis 2018. Le dinar tunisien "
                "reste non convertible mais des dérogations existent pour "
                "les entreprises offshore."
            ),
        ),
        authorized_currencies=["USD", "EUR", "GBP", "CHF", "JPY"],
        restricted_operations=["capital_account_transfers"],
        special_regimes=["entreprises_totalement_exportatrices", "zones_franches"],
    ),

    # ── ÉGYPTE ───────────────────────────────────────────────────────────────
    "EG": CountryForexProfile(
        country_code="EG", country_name="Égypte",
        central_bank_name="Central Bank of Egypt",
        domiciliation=DomiciliationRule(
            required=True, conditional=False,
            threshold_usd=5_000,
            mandatory_documents=[
                "commercial_invoice",
                "import_registration_certificate",
                "LC_or_documentary_collection",
            ],
            timeline_days=90,
            notes=(
                "Depuis 2017, les paiements d'importation doivent transiter "
                "par des banques agréées CBE. Les importateurs doivent être "
                "enregistrés au registre des importateurs."
            ),
        ),
        forex_regulation=ForexRegulation(
            regulation_level="moderate",
            prior_authorization_required=False,
            declaration_threshold_usd=5_000,
            repatriation_deadline_days=90,
            penalties="Amende 5 000 EGP + suspension du registre d'importateur.",
            notes=(
                "La livre égyptienne a été libéralisée en 2022. Le marché "
                "des changes est plus ouvert mais les banques restent "
                "obligatoires pour les paiements commerciaux."
            ),
        ),
        authorized_currencies=["USD", "EUR", "GBP", "CHF", "JPY", "AED", "SAR"],
        restricted_operations=["speculative_forex"],
        special_regimes=["zones_economiques_speciales", "Suez_Canal_Zone"],
    ),

    # ── NIGERIA ───────────────────────────────────────────────────────────────
    "NG": CountryForexProfile(
        country_code="NG", country_name="Nigeria",
        central_bank_name="Central Bank of Nigeria",
        domiciliation=DomiciliationRule(
            required=True, conditional=False,
            threshold_usd=10_000,
            mandatory_documents=[
                "Form_M",
                "proforma_invoice",
                "Combined_Expatriate_Resident_Permit",
                "LC_mandatory_for_industrial_goods",
            ],
            timeline_days=60,
            notes=(
                "Le Form M est obligatoire pour toute importation. "
                "Les biens industriels requièrent un crédit documentaire "
                "irrévocable. La CBN contrôle strictement les sorties de devises."
            ),
        ),
        forex_regulation=ForexRegulation(
            regulation_level="strict",
            prior_authorization_required=True,
            authorization_threshold_usd=10_000,
            declaration_threshold_usd=10_000,
            repatriation_deadline_days=60,
            penalties=(
                "Suspension de la licence bancaire, amende jusqu'à "
                "5× le montant + gel des avoirs."
            ),
            notes=(
                "La CBN maintient un système de change à guichets multiples. "
                "Le naira n'est pas librement convertible. "
                "Les paiements en espèces sont interdits pour les importations."
            ),
        ),
        authorized_currencies=["USD", "EUR", "GBP", "CNY"],
        restricted_operations=[
            "cash_import_payments", "41_restricted_items_import",
            "capital_account_outflows_above_limit",
        ],
        special_regimes=["Export_Proceeds_Domiciliary_Account", "NEPZ_free_zones"],
    ),

    # ── GHANA ─────────────────────────────────────────────────────────────────
    "GH": CountryForexProfile(
        country_code="GH", country_name="Ghana",
        central_bank_name="Bank of Ghana",
        domiciliation=DomiciliationRule(
            required=False, conditional=True,
            threshold_usd=50_000,
            mandatory_documents=[
                "commercial_invoice",
                "bill_of_lading",
                "customs_declaration",
            ],
            timeline_days=60,
            notes=(
                "Le Ghana dispose d'un régime de change relativement libéral. "
                "La domiciliation n'est pas systématique mais les banques "
                "restent obligatoires pour les transferts > 50 000 USD."
            ),
        ),
        forex_regulation=ForexRegulation(
            regulation_level="moderate",
            prior_authorization_required=False,
            declaration_threshold_usd=50_000,
            repatriation_deadline_days=60,
            penalties="Amende administrative.",
            notes=(
                "Depuis 2006, le Ghana a libéralisé son compte courant. "
                "Le cedi peut être échangé librement."
            ),
        ),
        authorized_currencies=["USD", "EUR", "GBP", "CHF"],
        restricted_operations=["speculative_forex"],
        special_regimes=["GIPC_investment_incentives"],
    ),

    # ── CÔTE D'IVOIRE ─────────────────────────────────────────────────────────
    "CI": CountryForexProfile(
        country_code="CI", country_name="Côte d'Ivoire",
        central_bank_name="BCEAO",
        domiciliation=DomiciliationRule(
            required=True, conditional=False,
            threshold_usd=5_000,
            mandatory_documents=[
                "declaration_importation",
                "facture_commerciale",
                "domiciliation_BCEAO",
            ],
            timeline_days=120,
            notes=(
                "Zone UEMOA : la domiciliation suit les règles BCEAO. "
                "Le franc CFA est indexé à l'euro (parité fixe)."
            ),
        ),
        forex_regulation=ForexRegulation(
            regulation_level="moderate",
            prior_authorization_required=False,
            declaration_threshold_usd=5_000,
            repatriation_deadline_days=120,
            penalties="Pénalités BCEAO + saisie des avoirs.",
            notes=(
                "La zone CFA BCEAO (UEMOA) offre une convertibilité "
                "garantie par la Banque de France. "
                "Les transferts intra-zone sont libres."
            ),
        ),
        authorized_currencies=["EUR", "USD", "GBP"],
        restricted_operations=["speculative_forex"],
        special_regimes=["zone_UEMOA_libre_circulation_capitaux"],
    ),

    # ── SÉNÉGAL ──────────────────────────────────────────────────────────────
    "SN": CountryForexProfile(
        country_code="SN", country_name="Sénégal",
        central_bank_name="BCEAO",
        domiciliation=DomiciliationRule(
            required=True, conditional=False,
            threshold_usd=5_000,
            mandatory_documents=[
                "declaration_importation",
                "facture_commerciale",
                "domiciliation_BCEAO",
            ],
            timeline_days=120,
            notes="Mêmes règles que la zone UEMOA (BCEAO).",
        ),
        forex_regulation=ForexRegulation(
            regulation_level="moderate",
            prior_authorization_required=False,
            declaration_threshold_usd=5_000,
            repatriation_deadline_days=120,
            penalties="Pénalités BCEAO.",
            notes="Zone CFA BCEAO – parité fixe EUR/XOF.",
        ),
        authorized_currencies=["EUR", "USD", "GBP"],
        restricted_operations=[],
        special_regimes=["zone_UEMOA"],
    ),

    # ── KENYA ─────────────────────────────────────────────────────────────────
    "KE": CountryForexProfile(
        country_code="KE", country_name="Kenya",
        central_bank_name="Central Bank of Kenya",
        domiciliation=DomiciliationRule(
            required=False, conditional=True,
            threshold_usd=100_000,
            mandatory_documents=[
                "commercial_invoice",
                "bill_of_lading",
            ],
            timeline_days=30,
            notes=(
                "Le Kenya dispose d'un système de change libéral. "
                "Les transferts sont généralement libres via les banques. "
                "M-Pesa est très utilisé pour le commerce de proximité."
            ),
        ),
        forex_regulation=ForexRegulation(
            regulation_level="liberal",
            prior_authorization_required=False,
            declaration_threshold_usd=100_000,
            repatriation_deadline_days=30,
            penalties="Amende administrative légère.",
            notes=(
                "Le shilling kenyan est librement convertible sur le marché "
                "interbancaire. Le Kenya est le hub financier de l'Afrique de l'Est."
            ),
        ),
        authorized_currencies=["USD", "EUR", "GBP", "CHF", "JPY", "AED"],
        restricted_operations=[],
        special_regimes=["Nairobi_International_Financial_Centre"],
    ),

    # ── ÉTHIOPIE ──────────────────────────────────────────────────────────────
    "ET": CountryForexProfile(
        country_code="ET", country_name="Éthiopie",
        central_bank_name="National Bank of Ethiopia",
        domiciliation=DomiciliationRule(
            required=True, conditional=False,
            threshold_usd=0,
            mandatory_documents=[
                "commercial_invoice",
                "LC_mandatory",
                "import_permit_NBE",
            ],
            timeline_days=60,
            notes=(
                "Toutes les importations nécessitent un crédit documentaire "
                "irrévocable. Le NBE contrôle les allocations de devises. "
                "Pénuries de devises fréquentes."
            ),
        ),
        forex_regulation=ForexRegulation(
            regulation_level="strict",
            prior_authorization_required=True,
            authorization_threshold_usd=0,
            declaration_threshold_usd=500,
            repatriation_deadline_days=60,
            penalties="Confiscation des devises + sanctions pénales.",
            notes=(
                "Le birr éthiopien est non convertible. "
                "La NBE alloue les devises selon ses priorités sectorielles. "
                "Réforme partielle en cours depuis 2019."
            ),
        ),
        authorized_currencies=["USD", "EUR"],
        restricted_operations=[
            "cash_forex", "capital_account_transfers", "speculative_forex",
        ],
        special_regimes=["Industrial_Parks_forex_facilities"],
    ),

    # ── TANZANIE ──────────────────────────────────────────────────────────────
    "TZ": CountryForexProfile(
        country_code="TZ", country_name="Tanzanie",
        central_bank_name="Bank of Tanzania",
        domiciliation=DomiciliationRule(
            required=False, conditional=True,
            threshold_usd=50_000,
            mandatory_documents=[
                "commercial_invoice",
                "bill_of_lading",
                "customs_declaration",
            ],
            timeline_days=90,
            notes=(
                "La Tanzanie a libéralisé son régime de change. "
                "Domiciliation recommandée mais non systématiquement obligatoire."
            ),
        ),
        forex_regulation=ForexRegulation(
            regulation_level="moderate",
            prior_authorization_required=False,
            declaration_threshold_usd=50_000,
            repatriation_deadline_days=90,
            penalties="Amende administrative.",
            notes="Shilling tanzanien librement échangeable sur le marché interbancaire.",
        ),
        authorized_currencies=["USD", "EUR", "GBP", "KES"],
        restricted_operations=[],
        special_regimes=["EPZ_Zanzibar_free_zone"],
    ),

    # ── AFRIQUE DU SUD ───────────────────────────────────────────────────────
    "ZA": CountryForexProfile(
        country_code="ZA", country_name="Afrique du Sud",
        central_bank_name="South African Reserve Bank",
        domiciliation=DomiciliationRule(
            required=True, conditional=False,
            threshold_usd=5_000,
            mandatory_documents=[
                "commercial_invoice",
                "SARS_customs_declaration",
                "authorised_dealer_confirmation",
            ],
            timeline_days=30,
            notes=(
                "Les Authorised Dealers (banques agréées SARB) traitent tous "
                "les paiements de commerce extérieur. "
                "Les entreprises doivent déclarer et rapatrier les recettes d'exportation."
            ),
        ),
        forex_regulation=ForexRegulation(
            regulation_level="moderate",
            prior_authorization_required=False,
            declaration_threshold_usd=5_000,
            repatriation_deadline_days=30,
            penalties=(
                "Amende jusqu'à 250 000 ZAR + emprisonnement possible "
                "selon Currency and Exchanges Act."
            ),
            notes=(
                "Le rand sud-africain est librement négociable. "
                "Le Currency and Exchanges Act régit toutes les transactions. "
                "La SARB publie des Exchange Control Rulings détaillées."
            ),
        ),
        authorized_currencies=["USD", "EUR", "GBP", "CHF", "JPY", "AUD", "CNY"],
        restricted_operations=["offshore_loans_above_limit", "speculative_forex"],
        special_regimes=["Authorised_Dealer_network", "loop_structure_exemptions"],
    ),

    # ── ANGOLA ────────────────────────────────────────────────────────────────
    "AO": CountryForexProfile(
        country_code="AO", country_name="Angola",
        central_bank_name="Banco Nacional de Angola",
        domiciliation=DomiciliationRule(
            required=True, conditional=False,
            threshold_usd=0,
            mandatory_documents=[
                "factura_proforma",
                "contrato_comercial",
                "licenca_importacao",
                "DU_declaracao_unica",
            ],
            timeline_days=90,
            notes=(
                "Toute importation doit être domiciliée auprès d'une banque "
                "agréée BNA. Le paiement en espèces est interdit. "
                "Pénurie chronique de dollars."
            ),
        ),
        forex_regulation=ForexRegulation(
            regulation_level="strict",
            prior_authorization_required=True,
            authorization_threshold_usd=0,
            declaration_threshold_usd=10_000,
            repatriation_deadline_days=90,
            penalties="Amende + suspension des licences d'import.",
            notes=(
                "Le kwanza est non convertible. "
                "La BNA alloue les dollars en priorité aux secteurs stratégiques. "
                "Réformes en cours depuis 2018 pour libéraliser progressivement."
            ),
        ),
        authorized_currencies=["USD", "EUR"],
        restricted_operations=[
            "cash_forex", "capital_account_transfers",
        ],
        special_regimes=["oil_sector_forex_facilities", "ZEE_zones"],
    ),

    # ── ZAMBIE ────────────────────────────────────────────────────────────────
    "ZM": CountryForexProfile(
        country_code="ZM", country_name="Zambie",
        central_bank_name="Bank of Zambia",
        domiciliation=DomiciliationRule(
            required=False, conditional=True,
            threshold_usd=50_000,
            mandatory_documents=[
                "commercial_invoice",
                "bill_of_lading",
                "customs_declaration",
            ],
            timeline_days=60,
            notes=(
                "La Zambie a libéralisé son compte courant. "
                "Domiciliation requise pour les grandes transactions."
            ),
        ),
        forex_regulation=ForexRegulation(
            regulation_level="moderate",
            prior_authorization_required=False,
            declaration_threshold_usd=50_000,
            repatriation_deadline_days=60,
            penalties="Amende administrative.",
            notes="Kwacha zambien relativement libre depuis 2012.",
        ),
        authorized_currencies=["USD", "EUR", "GBP", "ZAR"],
        restricted_operations=[],
        special_regimes=["mining_sector_forex_facilities"],
    ),
}

# ---------------------------------------------------------------------------
# DEFAULT PROFILE for countries not yet fully detailed
# ---------------------------------------------------------------------------

_DEFAULT_PROFILE = CountryForexProfile(
    country_code="XX", country_name="Unknown",
    central_bank_name="Unknown",
    domiciliation=DomiciliationRule(
        required=False, conditional=True,
        threshold_usd=10_000,
        mandatory_documents=["commercial_invoice", "customs_declaration"],
        timeline_days=90,
        notes="Profil par défaut – données détaillées non encore disponibles.",
    ),
    forex_regulation=ForexRegulation(
        regulation_level="moderate",
        prior_authorization_required=False,
        declaration_threshold_usd=10_000,
        repatriation_deadline_days=90,
        notes="Profil par défaut – consulter la banque centrale locale.",
    ),
    authorized_currencies=["USD", "EUR"],
)


# ---------------------------------------------------------------------------
# PUBLIC HELPERS
# ---------------------------------------------------------------------------

def get_forex_profile(country_code: str) -> CountryForexProfile:
    """Return forex profile for a country (ISO2). Falls back to default profile."""
    profile = FOREX_PROFILES.get(country_code.upper())
    if profile is not None:
        return profile
    # Return a copy of the default profile with the correct country code
    default = _DEFAULT_PROFILE.model_copy(
        update={"country_code": country_code.upper()}
    )
    return default


def get_domiciliation_rules(country_code: str) -> DomiciliationRule:
    """Return domiciliation rules for a country (ISO2)."""
    return get_forex_profile(country_code).domiciliation
