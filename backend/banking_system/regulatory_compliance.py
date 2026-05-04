"""
Regulatory compliance module – country-specific banking and trade finance regulations.

Provides structured compliance information for cross-border commercial operations,
covering AML/KYC requirements, sanctions screening, and sector-specific restrictions.
"""

from typing import Dict, List, Optional, Any


# ---------------------------------------------------------------------------
# COMPLIANCE DATA BY COUNTRY
# ---------------------------------------------------------------------------

COUNTRY_COMPLIANCE: Dict[str, Dict[str, Any]] = {
    "MA": {
        "country_name": "Maroc",
        "aml_framework": "FATF member (MENAFATF)",
        "kyc_requirements": [
            "identity_documents",
            "proof_of_address",
            "business_registration",
            "tax_number",
            "beneficial_owner_declaration",
        ],
        "sanctions_screening": "Office des Changes + UN + EU + US OFAC",
        "restricted_sectors": ["armement", "drogues", "jeux_en_ligne"],
        "trade_restrictions": [
            "contrôle_importation_medicaments",
            "autorisation_import_produits_strategiques",
        ],
        "reporting_requirements": {
            "suspicious_transaction_report": "UTRF (Unité de Traitement du Renseignement Financier)",
            "cash_threshold_mad": 100_000,
            "cross_border_declaration_usd": 10_000,
        },
        "compliance_contacts": {
            "regulator": "Bank Al-Maghrib",
            "fiu": "UTRF",
            "website": "https://www.utrf.ma",
        },
    },
    "DZ": {
        "country_name": "Algérie",
        "aml_framework": "FATF member (MENAFATF)",
        "kyc_requirements": [
            "identity_documents",
            "registre_commerce",
            "numéro_identification_fiscale",
            "attestation_domiciliation",
        ],
        "sanctions_screening": "Banque d'Algérie + UN + EU",
        "restricted_sectors": ["armement", "alcool_detail", "tabac_gros"],
        "trade_restrictions": [
            "crédit_documentaire_obligatoire",
            "interdiction_paiement_especes_import",
            "liste_produits_interdits_import",
        ],
        "reporting_requirements": {
            "suspicious_transaction_report": "CTRF (Cellule de Traitement du Renseignement Financier)",
            "cash_threshold_dzd": 1_000_000,
            "cross_border_declaration_usd": 1_000,
        },
        "compliance_contacts": {
            "regulator": "Banque d'Algérie",
            "fiu": "CTRF",
            "website": "https://www.bank-of-algeria.dz",
        },
    },
    "TN": {
        "country_name": "Tunisie",
        "aml_framework": "FATF member (MENAFATF)",
        "kyc_requirements": [
            "identity_documents",
            "registre_commerce",
            "matricule_fiscal",
            "attestation_entreprise",
        ],
        "sanctions_screening": "BCT + UN + EU",
        "restricted_sectors": ["armement", "jeux_hasard"],
        "trade_restrictions": [
            "domiciliation_obligatoire_import",
            "autorisation_préalable_produits_sensibles",
        ],
        "reporting_requirements": {
            "suspicious_transaction_report": "CTAF (Commission Tunisienne des Analyses Financières)",
            "cash_threshold_tnd": 5_000,
            "cross_border_declaration_usd": 2_000,
        },
        "compliance_contacts": {
            "regulator": "Banque Centrale de Tunisie",
            "fiu": "CTAF",
            "website": "https://www.ctaf.gov.tn",
        },
    },
    "EG": {
        "country_name": "Égypte",
        "aml_framework": "FATF member (MENAFATF)",
        "kyc_requirements": [
            "national_id",
            "commercial_register",
            "tax_card",
            "importers_register",
        ],
        "sanctions_screening": "CBE + UN + EU + US OFAC",
        "restricted_sectors": ["armement", "substances_controlees"],
        "trade_restrictions": [
            "importers_register_mandatory",
            "GOEIC_inspection_required",
            "NAFEZA_advance_cargo_declaration",
        ],
        "reporting_requirements": {
            "suspicious_transaction_report": "EMLCU (Egyptian Money Laundering Combating Unit)",
            "cash_threshold_egp": 100_000,
            "cross_border_declaration_usd": 5_000,
        },
        "compliance_contacts": {
            "regulator": "Central Bank of Egypt",
            "fiu": "EMLCU",
            "website": "https://www.emlcu.gov.eg",
        },
    },
    "NG": {
        "country_name": "Nigeria",
        "aml_framework": "FATF member (GIABA)",
        "kyc_requirements": [
            "BVN_Bank_Verification_Number",
            "CAC_registration",
            "TIN_Tax_Identification",
            "SCUML_registration_for_DNFBPs",
        ],
        "sanctions_screening": "CBN + ONSA + UN + EU + US OFAC",
        "restricted_sectors": [
            "armement_sans_licence",
            "41_items_restricted_import",
        ],
        "trade_restrictions": [
            "Form_M_mandatory",
            "LC_mandatory_industrial_goods",
            "pre_import_assessment_NAFDAC",
            "SON_standards_certification",
        ],
        "reporting_requirements": {
            "suspicious_transaction_report": "NFIU (Nigerian Financial Intelligence Unit)",
            "cash_threshold_ngn": 5_000_000,
            "cross_border_declaration_usd": 10_000,
        },
        "compliance_contacts": {
            "regulator": "Central Bank of Nigeria",
            "fiu": "NFIU",
            "website": "https://www.nfiu.gov.ng",
        },
    },
    "KE": {
        "country_name": "Kenya",
        "aml_framework": "FATF member (ESAAMLG)",
        "kyc_requirements": [
            "national_id_or_passport",
            "KRA_PIN",
            "business_registration_certificate",
            "beneficial_owner_declaration",
        ],
        "sanctions_screening": "CBK + ARC + UN + EU + US OFAC",
        "restricted_sectors": ["armement", "drogues"],
        "trade_restrictions": [
            "KEBS_standards_certification",
            "KEPHIS_phytosanitary",
        ],
        "reporting_requirements": {
            "suspicious_transaction_report": "FRC (Financial Reporting Centre)",
            "cash_threshold_kes": 1_000_000,
            "cross_border_declaration_usd": 10_000,
        },
        "compliance_contacts": {
            "regulator": "Central Bank of Kenya",
            "fiu": "FRC",
            "website": "https://www.frc.or.ke",
        },
    },
    "ZA": {
        "country_name": "Afrique du Sud",
        "aml_framework": "FATF member",
        "kyc_requirements": [
            "SA_ID_or_passport",
            "CIPC_company_registration",
            "SARS_tax_reference",
            "beneficial_owner_declaration_FICA",
        ],
        "sanctions_screening": "SARB + FIC + UN + EU + US OFAC",
        "restricted_sectors": ["armement_licence_NCACC", "substances_controlees"],
        "trade_restrictions": [
            "SABS_standards_required",
            "ITAC_import_permits_certain_goods",
            "BEE_compliance_preferred",
        ],
        "reporting_requirements": {
            "suspicious_transaction_report": "FIC (Financial Intelligence Centre)",
            "cash_threshold_zar": 24_999,
            "cross_border_declaration_usd": 10_000,
        },
        "compliance_contacts": {
            "regulator": "South African Reserve Bank",
            "fiu": "FIC",
            "website": "https://www.fic.gov.za",
        },
    },
}

_DEFAULT_COMPLIANCE: Dict[str, Any] = {
    "aml_framework": "FATF affiliated",
    "kyc_requirements": ["identity_documents", "business_registration", "tax_number"],
    "sanctions_screening": "UN sanctions list",
    "restricted_sectors": ["armement", "drogues"],
    "trade_restrictions": [],
    "reporting_requirements": {
        "suspicious_transaction_report": "National FIU",
        "cash_threshold_usd": 10_000,
        "cross_border_declaration_usd": 10_000,
    },
    "compliance_contacts": {
        "regulator": "Central Bank",
        "fiu": "National FIU",
    },
}


# ---------------------------------------------------------------------------
# PUBLIC HELPERS
# ---------------------------------------------------------------------------

def get_country_compliance(country_code: str) -> Dict[str, Any]:
    """Return compliance data for a country (ISO2)."""
    code = country_code.upper()
    data = COUNTRY_COMPLIANCE.get(code, _DEFAULT_COMPLIANCE.copy())
    data["country_code"] = code
    return data


def check_compliance(
    country_code: str,
    transaction_value_usd: float,
    sector: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Perform a basic compliance check for a transaction.

    Returns:
        dict with keys:
          - compliant (bool): whether the transaction is likely compliant
          - warnings (list[str]): compliance warnings
          - required_actions (list[str]): actions required before processing
    """
    code = country_code.upper()
    compliance = get_country_compliance(code)

    warnings: List[str] = []
    required_actions: List[str] = []

    # Check declaration threshold
    threshold = compliance.get("reporting_requirements", {}).get(
        "cross_border_declaration_usd", 10_000
    )
    if transaction_value_usd >= threshold:
        warnings.append(
            f"Déclaration obligatoire : montant ({transaction_value_usd:,.0f} USD) "
            f"dépasse le seuil de {threshold:,.0f} USD."
        )
        required_actions.append("cross_border_declaration")

    # Check restricted sector
    if sector:
        restricted = compliance.get("restricted_sectors", [])
        if any(sector.lower() in r.lower() for r in restricted):
            warnings.append(
                f"Secteur '{sector}' potentiellement restreint dans ce pays."
            )
            required_actions.append("sector_authorization_required")

    # KYC reminder
    required_actions.extend(compliance.get("kyc_requirements", []))

    return {
        "country_code": code,
        "transaction_value_usd": transaction_value_usd,
        "compliant": len(warnings) == 0,
        "warnings": warnings,
        "required_actions": list(dict.fromkeys(required_actions)),  # deduplicate
        "sanctions_screening": compliance.get("sanctions_screening", "N/A"),
        "fiu": compliance.get("compliance_contacts", {}).get("fiu", "N/A"),
    }
