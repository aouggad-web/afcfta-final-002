"""
Para-Fiscal Levies — All 54 African Countries
==============================================
Comprehensive registry of taxes and levies beyond standard customs duties (D.D)
and VAT across all African countries.

These levies fall into four categories:

1. MANDATORY INSPECTION / CONFORMITY AGENCIES (analogous to DRC's OCC)
   Countries where a dedicated agency imposes a universal levy + certificate on
   all (or nearly all) imports, separate from the customs declaration:
   - NGA  Form M + CISS (Central Bank of Nigeria / Nigeria Customs)
   - EGY  GOEIC (General Organization for Export & Import Control)
   - CMR  ECTN via CNCC (maritime cargo only)
   - KEN  KEBS CoC (for regulated goods — already captured as STDCERT)

2. COMMUNITY / REGIONAL LEVIES
   Harmonised levies mandated by regional economic communities:
   ECOWAS: CEDEAO/PCC (0.5%), RS (1%), PCS (1%), PUA (0.2%)
   UEMOA:  additional RS + PCS on top of ECOWAS base
   AES:    PC-AES (0.5%) replacing PCC for MLI/BFA/NER since 2025
   CEMAC:  TCI (1%), RI (0.45%)
   EAC:    IDF (KEN 3.5%), RDL (KEN 2%), Infrastructure Levy (UGA 1.5%)

3. NATIONAL FISCAL LEVIES
   Country-specific surcharges levied alongside customs duty:
   - NGA  CISS (1% CIF) — Comprehensive Import Supervision Scheme
   - NGA  NAC  (varies) — Nigerian Automotive Council Levy (vehicles)
   - GHA  GETFUND (2.5%) — Ghana Education Trust Fund Levy
   - GHA  NHIL (2.5%)   — National Health Insurance Levy
   - ETH  SUR (10% of DD) — Complementary Tax (Taxe Complémentaire)
   - DZA  PRCT (2% CIF)  — Prélèvement Compensation Transport
   - DZA  TCS (3% food)  — Taxe de Contribution de Solidarité
   - DZA  DAPS (30–200%) — Droit Additionnel Provisoire de Sauvegarde
   - MAR  TPI (varies)   — Taxe Parafiscale sur les Importations
   - AGO  IE  (varies)   — Imposto Especial de Consumo
   - CMR  CAC (10% of DD) — Centimes Additionnels Communaux
   - MOZ  TRA (0.5%)     — Taxa de Regularização Aduaneira

4. PORT / INFRASTRUCTURE LEVIES
   - KEN  IDF (3.5% CIF) — Import Declaration Fee (Kenya Revenue Authority)
   - KEN  RDL (2.0% CIF) — Railway Development Levy (KRA / Kenya Railways)
   - UGA  INFRALVY (1.5% CIF) — Infrastructure Levy (URA)
   - TZA  PDL (1.0%)    — Port Development Levy (TPA)
   - GHA  CPL (1.0%)    — COVID-19 Levy (GRA, renewed annually)

Sources:
  NGA Form M: CBN Act 2007; CBN FOREX (Monitoring) Act 1995; NCS Circular 2019/01
  NGA CISS: Finance (Miscellaneous Provisions) Act 2003; Customs & Excise Tariff Act
  EGY GOEIC: Law 118/1975, Decree 991/2015, Decree 1267/2015, Ministerial Decree 43/2016
  KEN IDF/RDL: Finance Act 2022 (Kenya); EAC-CET 2022 (EAC)
  UGA Infrastructure Levy: Uganda Finance Act 2020
  GHA GETFUND: Ghana Education Trust Fund Act 581/1997
  GHA NHIL:   National Health Insurance Act 650/2003
  ETH SUR:    Ethiopian Customs Proclamation 859/2014
  CMR TCI/CAC: Règlement CEMAC n°17/99/CEMAC-20-CM-03
  ECOWAS RS/PCS: UEMOA Directive 02/98/CM/UEMOA; Règlement CEDEAO C/REG.2/6/00
  DZA PRCT/TCS: Loi de Finances 2024 (DZ); Décret exécutif 22-147
  MAR TPI: Circulaire Douanière 6050/2024 (ADII)

Last updated: 2025
"""

from typing import Dict, Optional, Tuple


# =============================================================================
# LEVY DESCRIPTION LOOKUP
# Maps short tax code → (name_fr, name_en)
# Used to fill empty `observation` fields in taxes_detail.
# =============================================================================

LEVY_DESCRIPTIONS: Dict[str, Tuple[str, str]] = {
    # ── ECOWAS / UEMOA / AES community levies ─────────────────────────────
    "CEDEAO":   ("Prélèvement Communautaire CEDEAO",
                 "ECOWAS Community Levy (0.5% CIF)"),
    "PCC":      ("Prélèvement Communautaire CEDEAO",
                 "ECOWAS Community Levy (0.5% CIF)"),
    "ETLS":     ("ECOWAS Trade Liberalization Scheme (CEDEAO)",
                 "ECOWAS Trade Liberalization Scheme (0.5% CIF)"),
    "RS":       ("Redevance Statistique UEMOA/CEDEAO (1% CIF)",
                 "Statistical Levy UEMOA/ECOWAS (1% of CIF)"),
    "PCS":      ("Prélèvement Communautaire de Solidarité UEMOA (1% CIF)",
                 "UEMOA Community Solidarity Levy (1% of CIF)"),
    "PUA":      ("Prélèvement Union Africaine (0.2% CIF)",
                 "African Union Levy (0.2% of CIF)"),
    "PC_AES":   ("Prélèvement Confédéral AES (0.5% CIF) — remplace PCC depuis 2025",
                 "AES Confederal Levy (0.5% CIF) — replaces ECOWAS levy since 2025"),
    "PC-AES":   ("Prélèvement Confédéral AES (0.5% CIF) — remplace PCC depuis 2025",
                 "AES Confederal Levy (0.5% CIF) — replaces ECOWAS levy since 2025"),

    # ── Nigeria-specific levies ────────────────────────────────────────────
    "CISS":     ("Prélèvement CISS Nigeria — Comprehensive Import Supervision Scheme (1% CIF)",
                 "Nigeria CISS — Comprehensive Import Supervision Scheme (1% of CIF value); "
                 "Finance (Misc. Provisions) Act 2003 — collected by NCS via authorized dealer banks"),
    "NAC":      ("Taxe Nigeria Automotive Council (véhicules)",
                 "Nigerian Automotive Council Levy (motor vehicles)"),

    # ── Ghana-specific levies ──────────────────────────────────────────────
    "GETFUND":  ("Ghana Education Trust Fund Levy — GETFund (2.5%)",
                 "Ghana Education Trust Fund Levy (2.5%); GETFund Act 581/1997 — GRA"),
    "NHIL":     ("National Health Insurance Levy Ghana (2.5%)",
                 "Ghana National Health Insurance Levy (2.5%); NHIA Act 650/2003 — GRA"),
    "CPL":      ("COVID-19 Levy Ghana (1%)",
                 "Ghana COVID-19 Health Recovery Levy (1%); COVID-19 Health Recovery Levy Act 2021"),
    "ECOWAS":   ("Prélèvement Communautaire CEDEAO",
                 "ECOWAS Community Levy (0.5% CIF)"),

    # ── EAC / Kenya / Uganda levies ───────────────────────────────────────
    "IDF":      ("Import Declaration Fee Kenya — IDF (3,5% CIF)",
                 "Kenya Import Declaration Fee (3.5% of CIF); Kenya Finance Act 2022 — KRA"),
    "RDL":      ("Railway Development Levy Kenya — RDL (2% CIF)",
                 "Kenya Railway Development Levy (2% of CIF); KRA / Kenya Railways Corporation"),
    "INFRALVY": ("Infrastructure Levy Uganda (1,5% CIF)",
                 "Uganda Infrastructure Levy (1.5% of CIF); Uganda Finance Act 2020 — URA"),

    # ── Ethiopia-specific levies ───────────────────────────────────────────
    "SUR":      ("Taxe Complémentaire Éthiopie / Surtaxe (10% du DD)",
                 "Ethiopia Complementary Tax / Surcharge (10% of customs duty value); "
                 "Ethiopian Customs Proclamation 859/2014 — Ethiopian Customs Commission"),
    "EXC":      ("Taxe d'Accise Éthiopie (taux variable)",
                 "Ethiopia Excise Tax (variable rates)"),

    # ── CEMAC / Cameroon levies ────────────────────────────────────────────
    "TCI":      ("Taxe Communautaire d'Intégration CEMAC (1% CIF)",
                 "CEMAC Community Integration Tax (1% of CIF); Règlement CEMAC n°17/99"),
    "RI":       ("Redevance Informatique CEMAC (0,45% CIF)",
                 "CEMAC IT User Fee (0.45% of CIF)"),
    "CAC":      ("Centimes Additionnels Communaux Cameroun (10% du DD)",
                 "Cameroon Municipal Additional Centimes (10% of customs duty); DGD-CM"),
    "CCI":      ("Contribution Communautaire d'Intégration CEEAC",
                 "ECCAS Community Integration Contribution"),

    # ── Algeria-specific levies ────────────────────────────────────────────
    "PRCT":     ("Prélèvement à la Compensation du Transport Algérie (2% CIF)",
                 "Algeria Transport Compensation Levy (2% of CIF); Loi de Finances Algeria"),
    "TCS":      ("Taxe de Contribution de Solidarité Algérie (1-3%)",
                 "Algeria Solidarity Contribution Tax (1–3%); DGD Algeria"),
    "DAPS":     ("Droit Additionnel Provisoire de Sauvegarde Algérie (30–200%)",
                 "Algeria Provisional Safeguard Additional Duty (30–200%); DGD Algeria"),
    "T.C.S":    ("Taxe de Contribution de Solidarité Algérie (1-3%)",
                 "Algeria Solidarity Contribution Tax (1–3%); DGD Algeria"),

    # ── Morocco-specific levies ────────────────────────────────────────────
    "TPI":      ("Taxe Parafiscale sur les Importations Maroc",
                 "Morocco Para-fiscal Import Tax (TPI); ADII — Circulaire 6050/2024"),

    # ── Angola-specific levies ─────────────────────────────────────────────
    "IE":       ("Imposto Especial de Consumo Angola (taux variable)",
                 "Angola Special Consumption Tax / Excise (variable rates); AGT Angola"),

    # ── Mozambique-specific levies ─────────────────────────────────────────
    "TRA":      ("Taxa de Regularização Aduaneira Mozambique (0,5% CIF)",
                 "Mozambique Customs Regularization Fee (0.5% of CIF); AT-MZ"),

    # ── SADC / other levies ────────────────────────────────────────────────
    "LEVY":     ("Prélèvement / Taxe additionnelle",
                 "Additional Import Levy"),
    "WHT":      ("Retenue à la Source sur Importations",
                 "Withholding Tax on Imports"),
    "DEV":      ("Taxe de Développement",
                 "Development Levy"),
}


# =============================================================================
# COUNTRY-SPECIFIC PARA-FISCAL FORMALITY INJECTIONS
# Countries where a mandatory inspection/authorization agency issues a
# document required for ALL (or a large category of) imports — analogous
# to DRC's OCC Certificat de Conformité.
# =============================================================================

COUNTRY_PARA_FISCAL_FORMALITIES: Dict[str, list] = {

    # ------------------------------------------------------------------
    # NIGERIA (NGA) — Form M (pre-import authorization)
    # The Central Bank of Nigeria (CBN) requires every commercial importer
    # to obtain a Form M (import licence) from an authorized dealer bank
    # BEFORE the goods leave the country of supply.
    # • Universal: applies to all commercial imports (goods for resale/use)
    # • Threshold: imports exceeding USD 10,000 (or any value for selected goods)
    # • Issued by: CBN-authorized dealer banks via Nigeria Trade Hub
    # • Legal basis: CBN Act Cap C4 LFN 2004; FOREX (Monitoring &
    #   Miscellaneous Provisions) Act Cap F34 LFN 2004; CBN Circular
    #   TED/FEM/PUB/FPC/01/010 (2019)
    # ------------------------------------------------------------------
    "NGA": [
        {
            "code": "FORMM",
            "document_fr": (
                "Formulaire M — Autorisation Préalable d'Importation (CBN/banques agréées) "
                "obligatoire pour toutes importations commerciales au Nigeria"
            ),
            "document_en": (
                "Form M — Pre-Import Authorization (Central Bank of Nigeria / Authorized Dealer Banks) "
                "mandatory for all commercial imports into Nigeria; CBN Act Cap C4 LFN 2004"
            ),
            "authority_fr": "Banque Centrale du Nigeria (CBN) — Banques Agréées (Authorized Dealer Banks)",
            "authority_en": "Central Bank of Nigeria (CBN) — Authorized Dealer Banks",
            "is_mandatory": True,
        },
    ],

    # ------------------------------------------------------------------
    # EGYPT (EGY) — GOEIC mandatory import inspection
    # The General Organization for Export & Import Control (GOEIC) under
    # the Ministry of Trade & Industry issues mandatory inspection
    # certificates for manufactured, industrial and food-grade goods.
    # • Scope: manufactured goods, food products, chemicals, textiles,
    #   electronics, vehicles (excludes raw agricultural goods, live animals)
    # • Importer must register at GOEIC and obtain product approval
    #   before shipment or at port of entry
    # • Legal basis: Law 118/1975; Decree 991/2015; Decree 1267/2015;
    #   Ministerial Decree 43/2016
    # ------------------------------------------------------------------
    "EGY": [
        {
            "code": "GOEIC",
            "document_fr": (
                "Certificat d'Inspection GOEIC — Contrôle Obligatoire des Importations "
                "(marchandises manufacturées, alimentaires, chimiques, textiles, véhicules) "
                "— Loi égyptienne 118/1975, Décret 991/2015"
            ),
            "document_en": (
                "GOEIC Import Inspection Certificate — General Organization for Export & Import Control; "
                "mandatory for manufactured goods, food, chemicals, textiles, vehicles, electronics; "
                "Law 118/1975, Decree 991/2015, Decree 1267/2015"
            ),
            "authority_fr": "Organisation Générale du Contrôle des Exportations et Importations (GOEIC) — Ministère du Commerce et de l'Industrie d'Égypte",
            "authority_en": "General Organization for Export & Import Control (GOEIC) — Ministry of Trade & Industry, Egypt",
            "is_mandatory": True,
        },
    ],

    # ------------------------------------------------------------------
    # KENYA (KEN) — IDF + RDL are collected at customs (no separate doc)
    # KEBS Certificate of Conformity (CoC) is already captured as STDCERT.
    # ------------------------------------------------------------------

    # ------------------------------------------------------------------
    # GHANA (GHA) — GETFUND + NHIL are collected by GRA at customs
    # GSA CoC is already captured as STDCERT.
    # ------------------------------------------------------------------

    # ------------------------------------------------------------------
    # ETHIOPIA (ETH) — Import Trade Permit
    # Ethiopia's Ministry of Trade & Industry requires Import Trade Permits
    # for a broad range of goods (consumer goods, manufactured products,
    # strategic goods). While not strictly universal, the permit covers
    # the majority of commercial imports.
    # • Legal basis: Commercial Code of Ethiopia; Proclamation 980/2016
    # ------------------------------------------------------------------
    "ETH": [
        {
            "code": "ETHPERMIT",
            "document_fr": (
                "Permis d'Importation Commerciale Éthiopie "
                "(Ministère du Commerce et de l'Intégration Régionale) "
                "— Proclamation 980/2016"
            ),
            "document_en": (
                "Ethiopia Import Trade Permit "
                "(Ministry of Trade & Regional Integration) "
                "— Commercial Code & Proclamation 980/2016; "
                "required for consumer, manufactured and strategic goods"
            ),
            "authority_fr": "Ministère du Commerce et de l'Intégration Régionale d'Éthiopie (MoTRI)",
            "authority_en": "Ethiopia Ministry of Trade & Regional Integration (MoTRI)",
            "is_mandatory": True,
        },
    ],

    # ------------------------------------------------------------------
    # CAMEROON / CEMAC — ECTN (Electronic Cargo Tracking Note)
    # The CNCC (Conseil National des Chargeurs du Cameroun) and similar
    # bodies in CEMAC countries require an ECTN (BSC — Bon de Suivi des
    # Cargaisons) for all maritime imports. It is a cargo tracking
    # certificate, not a conformity certificate, but it is universally
    # mandatory for all sea freight into CEMAC countries.
    # • Legal basis: Règlement CEMAC — Arrêté du MINFI (CMR)
    # ------------------------------------------------------------------
    "CMR": [
        {
            "code": "ECTN",
            "document_fr": (
                "ECTN/BSC — Bon de Suivi des Cargaisons / Electronic Cargo Tracking Note "
                "(fret maritime — obligatoire pour toutes importations par voie maritime) "
                "— CNCC Cameroun"
            ),
            "document_en": (
                "ECTN/BSC — Electronic Cargo Tracking Note / Bon de Suivi des Cargaisons; "
                "mandatory for all maritime freight imports into Cameroon; "
                "CNCC (Conseil National des Chargeurs du Cameroun)"
            ),
            "authority_fr": "Conseil National des Chargeurs du Cameroun (CNCC) / DGDDI-CM",
            "authority_en": "National Shippers Council of Cameroon (CNCC) / Customs DGD-CM",
            "is_mandatory": True,
        },
    ],
    "CAF": [
        {
            "code": "ECTN",
            "document_fr": (
                "ECTN/BSC — Bon de Suivi des Cargaisons (fret maritime) — Centrafrique"
            ),
            "document_en": (
                "ECTN/BSC — Electronic Cargo Tracking Note (maritime freight) — Central African Republic"
            ),
            "authority_fr": "Conseil Centrafricain des Chargeurs (CCC) / DGD-CF",
            "authority_en": "Central African Shippers Council (CCC) / Customs DGD-CF",
            "is_mandatory": True,
        },
    ],
    "COG": [
        {
            "code": "ECTN",
            "document_fr": "ECTN/BSC — Bon de Suivi des Cargaisons (fret maritime) — Congo-Brazzaville",
            "document_en": "ECTN/BSC — Electronic Cargo Tracking Note (maritime freight) — Republic of Congo",
            "authority_fr": "Conseil Congolais des Chargeurs (CCC) / DGD-CG",
            "authority_en": "Congo Shippers Council (CCC) / Customs DGD-CG",
            "is_mandatory": True,
        },
    ],
    "GAB": [
        {
            "code": "ECTN",
            "document_fr": "ECTN/BSC — Bon de Suivi des Cargaisons (fret maritime) — Gabon",
            "document_en": "ECTN/BSC — Electronic Cargo Tracking Note (maritime freight) — Gabon",
            "authority_fr": "Conseil Gabonais des Chargeurs (CGC) / DGD-GA",
            "authority_en": "Gabon Shippers Council (CGC) / Customs DGD-GA",
            "is_mandatory": True,
        },
    ],
    "GNQ": [
        {
            "code": "ECTN",
            "document_fr": "ECTN/BSC — Bon de Suivi des Cargaisons (fret maritime) — Guinée Équatoriale",
            "document_en": "ECTN/BSC — Electronic Cargo Tracking Note (maritime freight) — Equatorial Guinea",
            "authority_fr": "Consejo Nacional de Cargadores (CNC-GQ) / DGA-GQ",
            "authority_en": "Equatorial Guinea National Shippers Council (CNC-GQ) / DGA-GQ",
            "is_mandatory": True,
        },
    ],
    "TCD": [
        {
            "code": "ECTN",
            "document_fr": "ECTN/BSC — Bon de Suivi des Cargaisons (fret maritime transitant par Douala) — Tchad",
            "document_en": "ECTN/BSC — Electronic Cargo Tracking Note (maritime freight via Douala) — Chad",
            "authority_fr": "Conseil Tchadien des Chargeurs (CTC) / DGD-TD",
            "authority_en": "Chad Shippers Council (CTC) / Customs DGD-TD",
            "is_mandatory": True,
        },
    ],
}

# EGY GOEIC applies to manufactured/industrial goods only (not raw ag, live animals)
# Buckets to inject GOEIC into:
EGY_GOEIC_BUCKETS = {
    "general",
    "vehicles_machinery",
    "chemicals",
    "food_agriculture",   # processed food (ch16-24)
    "pharmaceuticals",
}
# Buckets where GOEIC does NOT apply (raw products mostly):
EGY_GOEIC_EXEMPT_CHAPTERS = {
    "01", "02", "03", "04", "05",  # live animals, fresh meat, fish, eggs
    "06", "07", "08", "09", "10",  # fresh plants, vegetables, fruits, cereals
    "27",                           # crude oil / gas (handled by EGPC/energy)
    "93",                           # arms (controlled separately)
}

# CEMAC ECTN countries
ECTN_COUNTRIES = {"CMR", "CAF", "COG", "GAB", "GNQ", "TCD"}


# =============================================================================
# PUBLIC API
# =============================================================================

def enrich_observation(tax_code: str) -> str:
    """
    Return a descriptive observation string for a known para-fiscal tax code.
    Returns the code itself if unknown (preserves existing non-empty observations).
    """
    entry = LEVY_DESCRIPTIONS.get(tax_code)
    if entry:
        return entry[1]  # English description with legal basis
    return tax_code


def get_para_fiscal_formalities(
    country_iso3: str,
    bucket: str,
    chapter: str,
) -> list:
    """
    Return country-specific para-fiscal formality entries to inject into
    the administrative_formalities list for a tariff line.

    Rules:
    - NGA: always injects FORMM (universal for all commercial imports)
    - EGY: injects GOEIC for manufactured/industrial/food goods (not raw ag/energy)
    - ETH: injects ETHPERMIT for non-animal, non-plant categories
    - CMR/CAF/COG/GAB/GNQ/TCD: injects ECTN (maritime cargo tracking note)

    Args:
        country_iso3: ISO3 code
        bucket:       formality bucket (general, food_agriculture, vehicles_machinery…)
        chapter:      2-digit HS chapter string

    Returns:
        List of formality dicts to append (may be empty).
    """
    extras = []
    ch = str(chapter).zfill(2)

    if country_iso3 == "NGA":
        extras.extend(COUNTRY_PARA_FISCAL_FORMALITIES["NGA"])

    elif country_iso3 == "EGY":
        if ch not in EGY_GOEIC_EXEMPT_CHAPTERS:
            extras.extend(COUNTRY_PARA_FISCAL_FORMALITIES["EGY"])

    elif country_iso3 == "ETH":
        # Import permit applies to manufactured and consumer goods.
        # Raw/primary agricultural products (ch01-15 live animals, fresh crops) are exempt.
        # Processed food (ch16+), all manufactured goods → require permit.
        # Filter only by chapter (not bucket) because ch16 is animal_products bucket
        # but IS a processed product requiring the import trade permit.
        _eth_raw_chapters = {
            "01", "02", "03", "04", "05",  # live animals / fresh animal products
            "06", "07", "08", "09", "10",  # live plants / fresh vegetables/fruits/cereals
            "11", "12", "13", "14",        # milling, oil seeds, lac/gums, vegetable materials
        }
        if ch not in _eth_raw_chapters:
            extras.extend(COUNTRY_PARA_FISCAL_FORMALITIES["ETH"])

    elif country_iso3 in ECTN_COUNTRIES:
        extras.extend(COUNTRY_PARA_FISCAL_FORMALITIES[country_iso3])

    return extras
