"""
Foreign-exchange control and domiciliation rules by country.

Covers the 14 phase-1 priority countries with full detail, and provides
a default liberal profile for the remaining African countries.

Sources légales :
  Maroc     – Office des Changes / Bank Al-Maghrib (Instruction OC 3/2023)
  Algérie   – Banque d'Algérie (Ordonnance n° 23-01 du 29 août 2023)
  Tunisie   – BCT (Loi n° 2016-48 ; Circulaire 2021-10)
  Égypte    – CBE (Banking Law No. 194 of 2020)
  Nigeria   – CBN (BOFIA 2020 ; Circulaire TED/FEM/FPC/GEN/01/012)
  Ghana     – BoG (Foreign Exchange Act 723 / 2006)
  Côte d'Ivoire – BCEAO / UEMOA (Règlement n° 09/2010/CM/UEMOA)
  Sénégal   – BCEAO / UEMOA (idem)
  Kenya     – CBK (CBK Act Cap. 491)
  Éthiopie  – NBE (Directive FXD/44/2018)
  Tanzanie  – BoT (Foreign Exchange Act 1992 Cap. 271)
  Afrique du Sud – SARB FinSurv (Currency and Exchanges Act No. 9/1933 ; Manual 2023)
  Angola    – BNA (Lei n.º 5/97 ; Instrutivo n.º 02/2019)
  Zambie    – BoZ (FEMA 2023)

Statuts FMI (Article VIII / XIV) :
  Source : https://www.imf.org/en/Publications/Annual-Report-on-Exchange-Arrangements
"""

from typing import Dict, Optional, Tuple

from .models import (
    CountryForexProfile,
    DomiciliationRule,
    ExportFormalities,
    ForexRegulation,
    ImportFormalities,
)

# ---------------------------------------------------------------------------
# FOREX PROFILES – Phase-1 priority countries (detailed)
# ---------------------------------------------------------------------------

FOREX_PROFILES: Dict[str, CountryForexProfile] = {
    # ── MAROC ────────────────────────────────────────────────────────────────
    "MA": CountryForexProfile(
        country_code="MA",
        country_name="Maroc",
        central_bank_name="Bank Al-Maghrib",
        currency_code="MAD",
        currency_name="Dirham marocain",
        domiciliation=DomiciliationRule(
            required=True,
            conditional=False,
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
                "préalables pour les transactions sensibles. "
                "Délai de rapatriement des recettes d'exportation : 150 jours "
                "(prorogeable sur demande à l'OC)."
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
                "des autorisations d'opérations de change "
                "(Art. 14 et suivants de la Loi n° 17-95)."
            ),
            notes=(
                "Office des Changes (OC) contrôle toutes les opérations en devises. "
                "Le dirham marocain (MAD) n'est pas convertible hors frontières ; "
                "seule la convertibilité pour les transactions courantes est garantie. "
                "La convertibilité du compte de capital reste soumise à autorisation préalable."
            ),
            legal_reference=(
                "Instruction de l'Office des Changes n° 3/2023 relative aux opérations "
                "d'importation et d'exportation de biens et services ; "
                "Circulaire Bank Al-Maghrib n° 9/G/2023 ; "
                "Décret n° 2-97-344 du 10 Rabia II 1418 (14 août 1997)"
            ),
            regulatory_body="Office des Changes (OC) – Ministère de l'Économie et des Finances",
            imf_article_status=(
                "Article VIII – Acceptation du 21 janvier 1993. "
                "Restrictions sur compte de capital maintenues."
            ),
        ),
        authorized_currencies=["USD", "EUR", "GBP", "CHF", "JPY", "CAD", "AED", "SAR"],
        restricted_operations=[
            "capital_account_transfers",
            "speculative_forex",
            "crypto_transactions",
        ],
        special_regimes=[
            "CFC_Casablanca_Finance_City",
            "zones_franches_exportation",
            "régime_exportateur_permanent",
        ],
    ),
    # ── ALGÉRIE ──────────────────────────────────────────────────────────────
    "DZ": CountryForexProfile(
        country_code="DZ",
        country_name="Algérie",
        central_bank_name="Banque d'Algérie",
        currency_code="DZD",
        currency_name="Dinar algérien",
        domiciliation=DomiciliationRule(
            required=True,
            conditional=False,
            threshold_usd=0,
            mandatory_documents=[
                "facture_pro_forma",
                "contrat_commercial",
                "titre_importation",
                "domiciliation_bancaire",
                "certificat_conformite_produits",
            ],
            timeline_days=180,
            notes=(
                "Toute importation doit être domiciliée auprès d'une banque "
                "primaire agréée. Pas de seuil minimal : la domiciliation est "
                "systématique dès le premier dinar. "
                "Le règlement par crédit documentaire irrévocable est obligatoire "
                "pour la quasi-totalité des importations."
            ),
        ),
        forex_regulation=ForexRegulation(
            regulation_level="strict",
            prior_authorization_required=True,
            authorization_threshold_usd=0,
            declaration_threshold_usd=1_000,
            repatriation_deadline_days=180,
            penalties=(
                "Infractions au code pénal algérien (Art. 429 à 442) : "
                "amende de 2 à 5 fois la valeur de l'infraction + emprisonnement "
                "de 2 à 10 ans. Gel des avoirs et suspension des autorisations bancaires."
            ),
            notes=(
                "Le dinar algérien (DZD) est non convertible. Le règlement des "
                "importations se fait exclusivement par crédit documentaire (LC) "
                "ou remise documentaire via une banque agréée. "
                "Les sorties de capitaux sont soumises à autorisation préalable "
                "de la Banque d'Algérie. "
                "Le marché officiel des changes est géré par la Banque d'Algérie."
            ),
            legal_reference=(
                "Ordonnance n° 23-01 du 29 août 2023 relative à la monnaie et au crédit ; "
                "Règlement BA n° 17-01 du 10 janvier 2017 relatif aux conditions "
                "d'ouverture et de fonctionnement des comptes devises ; "
                "Règlement n° 07-01 du 03 février 2007 relatif aux règles applicables "
                "aux transactions courantes avec l'étranger et aux comptes devises"
            ),
            regulatory_body=(
                "Banque d'Algérie – Direction Générale des Opérations Bancaires "
                "et des Changes (DGOBC)"
            ),
            imf_article_status=(
                "Article XIV – Régime transitoire. "
                "Restrictions sur transactions courantes et compte de capital maintenues."
            ),
        ),
        authorized_currencies=["USD", "EUR", "GBP"],
        restricted_operations=[
            "cash_payments_import",
            "capital_account_transfers",
            "crypto_transactions",
            "open_account_payment",
        ],
        special_regimes=["zones_franches_exportation", "offshore_banking_units"],
        # Formalités de change à l'EXPORTATION fournies explicitement (données
        # authentiques DGD/Banque d'Algérie) : régimes de domiciliation distincts
        # selon le type de produit et délai de rapatriement de 180 jours.
        export_formalities=ExportFormalities(
            domiciliation_required=True,
            domiciliation_conditional=True,
            domiciliation_threshold_usd=None,
            mandatory_documents=[
                "ouverture_dossier_domiciliation",
                "numero_domiciliation",
                "facture_commerciale",
                "declaration_exportation",
                "autorisations_FAP_si_applicable",
                "preuve_origine_si_avantages_fiscaux",
            ],
            repatriation_deadline_days=180,
            repatriation_formalities=(
                "Délai de rapatriement des recettes d'exportation hors "
                "hydrocarbures : 180 jours maximum à compter de la date "
                "d'expédition. Deux régimes de domiciliation selon le produit : "
                "(1) Produits frais, périssables et/ou dangereux — domiciliation "
                "a posteriori autorisée : la facture commerciale peut être "
                "domiciliée dans les 05 jours ouvrables suivant l'expédition "
                "(Instruction Banque d'Algérie n° 07-2021 du 29 juin 2021, "
                "règle générale 180 jours) ; "
                "(2) Biens de consommation courants — domiciliation a priori "
                "obligatoire avant expédition, sauf dérogation "
                "(Règlement Banque d'Algérie n° 2016-04 du 17 novembre 2016, "
                "180 jours maximum). "
                "Aucune domiciliation requise pour les exportations de "
                "marchandises ou d'échantillons d'une valeur inférieure ou "
                "égale à 100 000 DZD."
            ),
            legal_reference=(
                "Instruction de la Banque d'Algérie n° 07-2021 du 29 juin 2021 "
                "(produits frais et périssables – domiciliation a posteriori) ; "
                "Règlement de la Banque d'Algérie n° 2016-04 du 17 novembre 2016 "
                "(biens de consommation courants – domiciliation a priori) ; "
                "Guide de l'exportateur 2017 – Direction Générale des Douanes"
            ),
            regulatory_body=(
                "Banque d'Algérie – Direction Générale des Opérations Bancaires "
                "et des Changes (DGOBC) ; Direction Générale des Douanes (DGD)"
            ),
        ),
    ),
    # ── TUNISIE ───────────────────────────────────────────────────────────────
    "TN": CountryForexProfile(
        country_code="TN",
        country_name="Tunisie",
        central_bank_name="Banque Centrale de Tunisie",
        currency_code="TND",
        currency_name="Dinar tunisien",
        domiciliation=DomiciliationRule(
            required=True,
            conditional=False,
            threshold_usd=2_000,
            mandatory_documents=[
                "facture_commerciale",
                "declaration_importation",
                "attestation_banque_domiciliataire",
                "certificat_qualite_si_applicable",
            ],
            timeline_days=90,
            notes=(
                "Domiciliation obligatoire au-delà de 2 000 USD auprès d'une banque "
                "intermédiaire agréée (BIA). "
                "Les entreprises totalement exportatrices (ETE) bénéficient d'un "
                "régime simplifié avec comptes en devises et compte de "
                "rétrocession de 50% des recettes. "
                "Délai de rapatriement : 90 jours à compter de la date d'expédition."
            ),
        ),
        forex_regulation=ForexRegulation(
            regulation_level="moderate",
            prior_authorization_required=False,
            declaration_threshold_usd=2_000,
            repatriation_deadline_days=90,
            penalties=(
                "Amende administrative de 1 à 3 fois la valeur de l'infraction "
                "+ pénalités de retard de 1% par mois (Art. 45 de la Loi 76-18)."
            ),
            notes=(
                "Libéralisation progressive depuis 2018 (Loi n° 2018-54). "
                "Le dinar tunisien reste non convertible pour les opérations "
                "en capital, mais des dérogations existent pour les entreprises "
                "offshore. "
                "Les banques intermédiaires agréées (BIA) sont les seules "
                "habilitées à effectuer les opérations de change."
            ),
            legal_reference=(
                "Loi n° 2016-48 du 11 juillet 2016 relative aux banques et "
                "aux établissements financiers ; "
                "Loi n° 76-18 du 21 janvier 1976 portant refonte de la "
                "réglementation des changes (modifiée) ; "
                "Circulaire BCT n° 2021-10 relative aux opérations de change "
                "afférentes aux transactions commerciales"
            ),
            regulatory_body=(
                "Banque Centrale de Tunisie (BCT) – "
                "Direction des Opérations de Change et du Commerce Extérieur"
            ),
            imf_article_status=(
                "Article XIV – Régime transitoire. "
                "La Tunisie maintient des restrictions sur le compte de capital."
            ),
        ),
        authorized_currencies=["USD", "EUR", "GBP", "CHF", "JPY"],
        restricted_operations=["capital_account_transfers", "crypto_transactions"],
        special_regimes=[
            "entreprises_totalement_exportatrices",
            "zones_franches",
            "régime_offshore",
        ],
    ),
    # ── ÉGYPTE ───────────────────────────────────────────────────────────────
    "EG": CountryForexProfile(
        country_code="EG",
        country_name="Égypte",
        central_bank_name="Central Bank of Egypt",
        currency_code="EGP",
        currency_name="Livre égyptienne",
        domiciliation=DomiciliationRule(
            required=True,
            conditional=False,
            threshold_usd=5_000,
            mandatory_documents=[
                "commercial_invoice",
                "import_registration_certificate",
                "LC_or_documentary_collection",
                "customs_bill_of_entry",
            ],
            timeline_days=90,
            notes=(
                "Depuis 2017, les paiements d'importation doivent transiter "
                "par des banques agréées CBE. Les importateurs doivent être "
                "enregistrés au Registre des Importateurs du Ministère du Commerce. "
                "Les lettres de crédit (LC) irrévocables sont obligatoires pour "
                "la plupart des catégories de biens importés."
            ),
        ),
        forex_regulation=ForexRegulation(
            regulation_level="moderate",
            prior_authorization_required=False,
            declaration_threshold_usd=5_000,
            repatriation_deadline_days=90,
            penalties=(
                "Amende allant de 5 000 à 500 000 EGP + suspension "
                "du certificat d'importateur (Art. 126 Banking Law No. 194/2020)."
            ),
            notes=(
                "La livre égyptienne (EGP) a été libéralisée en novembre 2022 "
                "dans le cadre du programme FMI (accord de 3 milliards USD). "
                "Le marché des changes est désormais à taux flottant géré. "
                "Les banques restent obligatoires pour tous les paiements "
                "commerciaux d'importation/exportation."
            ),
            legal_reference=(
                "Banking Law No. 194 of 2020 (loi bancaire CBE) ; "
                "CBE Circular No. 1/2017 relative aux paiements d'importation ; "
                "Ministerial Decree No. 770/2022 re: import payment regulations"
            ),
            regulatory_body=(
                "Central Bank of Egypt (CBE) – " "Foreign Exchange & International Relations Sector"
            ),
            imf_article_status=(
                "Article VIII – Acceptation du 2 février 2005. "
                "Restrictions résiduelles sur certains paiements courants."
            ),
        ),
        authorized_currencies=["USD", "EUR", "GBP", "CHF", "JPY", "AED", "SAR", "KWD"],
        restricted_operations=["speculative_forex", "crypto_transactions"],
        special_regimes=[
            "zones_economiques_speciales",
            "Suez_Canal_Zone",
            "régime_investisseurs_étrangers",
        ],
    ),
    # ── NIGERIA ───────────────────────────────────────────────────────────────
    "NG": CountryForexProfile(
        country_code="NG",
        country_name="Nigeria",
        central_bank_name="Central Bank of Nigeria",
        currency_code="NGN",
        currency_name="Naira nigérian",
        domiciliation=DomiciliationRule(
            required=True,
            conditional=False,
            threshold_usd=10_000,
            mandatory_documents=[
                "Form_M",
                "proforma_invoice",
                "SON_NAFDAC_certification_if_applicable",
                "LC_mandatory_for_industrial_goods",
                "customs_HS_code_declaration",
            ],
            timeline_days=60,
            notes=(
                "Le Form M (formulaire CBN) est obligatoire pour toute importation "
                "avant l'ouverture d'une LC ou d'une remise documentaire. "
                "Les biens industriels et alimentaires requièrent un crédit "
                "documentaire irrévocable confirmé. "
                "La CBN contrôle strictement les sorties de devises. "
                "Liste des 41 articles dont l'importation via les banques est interdite "
                "(circulaire CBN du 25 juin 2015, actualisée 2023)."
            ),
        ),
        forex_regulation=ForexRegulation(
            regulation_level="strict",
            prior_authorization_required=True,
            authorization_threshold_usd=10_000,
            declaration_threshold_usd=10_000,
            repatriation_deadline_days=60,
            penalties=(
                "Révocation ou suspension de la licence bancaire, amende "
                "jusqu'à 5× le montant de l'infraction + gel des avoirs "
                "(Art. 30–35 BOFIA 2020)."
            ),
            notes=(
                "La CBN a unifié son marché des changes (NAFEM) en juin 2023, "
                "abandonnant le système de taux multiples. "
                "Le naira est désormais à taux flottant dirigé mais reste sous "
                "fort contrôle de la CBN. "
                "Les paiements en espèces pour les importations sont formellement interdits. "
                "Le Investors' and Exporters' (I&E) Window est le marché de référence."
            ),
            legal_reference=(
                "Banks and Other Financial Institutions Act 2020 (BOFIA 2020) ; "
                "CBN Circular TED/FEM/FPC/GEN/01/012 re: Form M ; "
                "CBN Foreign Exchange Manual (Revised Edition 2018) ; "
                "CBN Circular FEM/FPC/GEN/01/0010 du 14 juin 2023 re: unification"
            ),
            regulatory_body=(
                "Central Bank of Nigeria (CBN) – " "Trade and Exchange Department (TED)"
            ),
            imf_article_status=(
                "Article VIII – Acceptation du 2 août 1962. "
                "Restrictions sur certains paiements courants (I&E Window)."
            ),
        ),
        authorized_currencies=["USD", "EUR", "GBP", "CNY"],
        restricted_operations=[
            "cash_import_payments",
            "41_restricted_items_import",
            "capital_account_outflows_above_limit",
            "crypto_transactions_non_licensed",
        ],
        special_regimes=["Export_Proceeds_Domiciliary_Account", "NEPZ_free_zones", "NAFEM_window"],
    ),
    # ── GHANA ─────────────────────────────────────────────────────────────────
    "GH": CountryForexProfile(
        country_code="GH",
        country_name="Ghana",
        central_bank_name="Bank of Ghana",
        currency_code="GHS",
        currency_name="Cedi ghanéen",
        domiciliation=DomiciliationRule(
            required=False,
            conditional=True,
            threshold_usd=50_000,
            mandatory_documents=[
                "commercial_invoice",
                "bill_of_lading",
                "customs_declaration",
                "form_of_declaration_GhanaCustums",
            ],
            timeline_days=60,
            notes=(
                "Le Ghana dispose d'un régime de change relativement libéral. "
                "La domiciliation n'est pas systématique mais les banques "
                "agréées restent obligatoires pour les transferts > 50 000 USD. "
                "Depuis la Loi 723 (2006), les résidents peuvent détenir "
                "des comptes en devises dans des banques agréées au Ghana."
            ),
        ),
        forex_regulation=ForexRegulation(
            regulation_level="moderate",
            prior_authorization_required=False,
            declaration_threshold_usd=50_000,
            repatriation_deadline_days=60,
            penalties=(
                "Amende administrative jusqu'à GHS 12 000 + suspension "
                "des droits de change (Art. 17 et 18 du Foreign Exchange Act 723)."
            ),
            notes=(
                "Depuis le Foreign Exchange Act 2006 (Act 723), le Ghana a "
                "libéralisé son compte courant. Le cedi peut être échangé "
                "librement sur le marché interbancaire. "
                "En 2022, le Ghana a fait appel au FMI (programme de 3 milliards USD) "
                "suite à la dépréciation sévère du cedi."
            ),
            legal_reference=(
                "Foreign Exchange Act, 2006 (Act 723) ; "
                "Bank of Ghana Notice BG/GOV/SEC/2019/05 re: FX reporting ; "
                "Bank of Ghana Guidelines on Foreign Exchange Operations 2018"
            ),
            regulatory_body=(
                "Bank of Ghana (BoG) – "
                "Foreign Exchange Department & Banking Supervision Department"
            ),
            imf_article_status=(
                "Article VIII – Acceptation du 23 juin 1994. "
                "Compte courant libéré, restrictions sur compte de capital."
            ),
        ),
        authorized_currencies=["USD", "EUR", "GBP", "CHF", "CNY"],
        restricted_operations=["speculative_forex", "crypto_unlicensed"],
        special_regimes=["GIPC_investment_incentives", "Ghana_Free_Zones_Authority"],
    ),
    # ── CÔTE D'IVOIRE ─────────────────────────────────────────────────────────
    "CI": CountryForexProfile(
        country_code="CI",
        country_name="Côte d'Ivoire",
        central_bank_name="BCEAO",
        currency_code="XOF",
        currency_name="Franc CFA BCEAO",
        domiciliation=DomiciliationRule(
            required=True,
            conditional=False,
            threshold_usd=5_000,
            mandatory_documents=[
                "declaration_importation",
                "facture_commerciale",
                "domiciliation_BCEAO",
                "bordereau_de_suivi_des_cargaisons",
            ],
            timeline_days=120,
            notes=(
                "Zone UEMOA : la domiciliation suit les règles BCEAO. "
                "Le franc CFA (XOF) est indexé à l'euro avec une parité fixe "
                "(1 EUR = 655,957 XOF). "
                "Les transferts intra-zone UEMOA sont libres sans limitation."
            ),
        ),
        forex_regulation=ForexRegulation(
            regulation_level="moderate",
            prior_authorization_required=False,
            declaration_threshold_usd=5_000,
            repatriation_deadline_days=120,
            penalties=(
                "Pénalités BCEAO : amende de 25% à 200% du montant + "
                "saisie des avoirs en cas de fraude (Art. 34 du Règlement UEMOA)."
            ),
            notes=(
                "La zone CFA BCEAO (UEMOA) bénéficie d'une convertibilité "
                "garantie par le Trésor français (accord de coopération monétaire). "
                "Les transferts intra-UEMOA sont libres. "
                "Les transferts hors zone nécessitent une domiciliation bancaire."
            ),
            legal_reference=(
                "Règlement UEMOA n° 09/2010/CM/UEMOA du 1er octobre 2010 "
                "relatif aux relations financières extérieures ; "
                "Instruction BCEAO n° 04/2012/RB du 2 juillet 2012 ; "
                "Accord de coopération monétaire France-UEMOA du 14 novembre 1973"
            ),
            regulatory_body=(
                "BCEAO – Direction Nationale pour la Côte d'Ivoire ; "
                "Ministère de l'Économie et des Finances de Côte d'Ivoire"
            ),
            imf_article_status=(
                "Article VIII – Zone UEMOA. " "Acceptation collective du 1er juin 1996."
            ),
        ),
        authorized_currencies=["EUR", "USD", "GBP", "XAF"],
        restricted_operations=["speculative_forex", "crypto_non_agréé"],
        special_regimes=["zone_UEMOA_libre_circulation_capitaux", "Zone_Franche_de_Côte_dIvoire"],
    ),
    # ── SÉNÉGAL ──────────────────────────────────────────────────────────────
    "SN": CountryForexProfile(
        country_code="SN",
        country_name="Sénégal",
        central_bank_name="BCEAO",
        currency_code="XOF",
        currency_name="Franc CFA BCEAO",
        domiciliation=DomiciliationRule(
            required=True,
            conditional=False,
            threshold_usd=5_000,
            mandatory_documents=[
                "declaration_importation",
                "facture_commerciale",
                "domiciliation_BCEAO",
                "bordereau_fret",
            ],
            timeline_days=120,
            notes=(
                "Mêmes règles que la zone UEMOA (BCEAO). "
                "Parité fixe EUR/XOF : 1 EUR = 655,957 XOF. "
                "Les déclarations d'importation sont traitées via le "
                "Guichet Unique du Commerce Extérieur (GUCE)."
            ),
        ),
        forex_regulation=ForexRegulation(
            regulation_level="moderate",
            prior_authorization_required=False,
            declaration_threshold_usd=5_000,
            repatriation_deadline_days=120,
            penalties=(
                "Pénalités BCEAO conformément au Règlement UEMOA n° 09/2010. "
                "Amende de 25% à 200% du montant de l'infraction."
            ),
            notes=(
                "Zone CFA BCEAO – parité fixe EUR/XOF (655,957). "
                "La convertibilité est garantie par la France (compte d'opérations "
                "au Trésor français). "
                "Les transferts intra-UEMOA sont libres et non soumis à déclaration."
            ),
            legal_reference=(
                "Règlement UEMOA n° 09/2010/CM/UEMOA du 1er octobre 2010 ; "
                "Instruction BCEAO n° 04/2012/RB ; "
                "Loi n° 2002-07 du 15 juillet 2002 relative au contrôle des changes"
            ),
            regulatory_body=(
                "BCEAO – Direction Nationale du Sénégal ; "
                "Ministère des Finances et du Budget du Sénégal"
            ),
            imf_article_status=(
                "Article VIII – Zone UEMOA. " "Acceptation collective du 1er juin 1996."
            ),
        ),
        authorized_currencies=["EUR", "USD", "GBP"],
        restricted_operations=[],
        special_regimes=["zone_UEMOA", "Dakar_Financial_Centre"],
    ),
    # ── KENYA ─────────────────────────────────────────────────────────────────
    "KE": CountryForexProfile(
        country_code="KE",
        country_name="Kenya",
        central_bank_name="Central Bank of Kenya",
        currency_code="KES",
        currency_name="Shilling kenyan",
        domiciliation=DomiciliationRule(
            required=False,
            conditional=True,
            threshold_usd=100_000,
            mandatory_documents=[
                "commercial_invoice",
                "bill_of_lading",
                "customs_import_declaration",
            ],
            timeline_days=30,
            notes=(
                "Le Kenya dispose d'un système de change libéral (Article VIII FMI). "
                "Les transferts sont généralement libres via les banques agréées CBK. "
                "M-Pesa (Safaricom) est très utilisé pour le commerce de proximité "
                "et les envois transfrontaliers en EAC. "
                "La domiciliation devient obligatoire pour les transactions > 100 000 USD."
            ),
        ),
        forex_regulation=ForexRegulation(
            regulation_level="liberal",
            prior_authorization_required=False,
            declaration_threshold_usd=100_000,
            repatriation_deadline_days=30,
            penalties=(
                "Amende administrative de KES 500 000 à KES 5 000 000 "
                "(Art. 35 CBK Act Cap. 491) + suspension des droits de change."
            ),
            notes=(
                "Le shilling kenyan (KES) est librement convertible "
                "sur le marché interbancaire. "
                "Le Kenya est le hub financier de l'Afrique de l'Est. "
                "Le Nairobi International Financial Centre (NIFC) offre "
                "des incitations pour les services financiers régionaux. "
                "Le CBK a introduit le Kenya Fast Payment System (KFPS) en 2023."
            ),
            legal_reference=(
                "Central Bank of Kenya Act (Cap. 491, révisé 2023) ; "
                "Foreign Exchange (Controls) Regulations (L.N. 241/1967, révisées) ; "
                "CBK Prudential Guidelines on Foreign Exchange Exposure 2013"
            ),
            regulatory_body=("Central Bank of Kenya (CBK) – " "Financial Markets Department"),
            imf_article_status=(
                "Article VIII – Acceptation du 30 juin 1994. "
                "Compte courant et capital libéralisés."
            ),
        ),
        authorized_currencies=["USD", "EUR", "GBP", "CHF", "JPY", "AED", "ZAR", "TZS", "UGX"],
        restricted_operations=["crypto_unlicensed"],
        special_regimes=["Nairobi_International_Financial_Centre", "EPZ_Export_Processing_Zone"],
    ),
    # ── ÉTHIOPIE ──────────────────────────────────────────────────────────────
    "ET": CountryForexProfile(
        country_code="ET",
        country_name="Éthiopie",
        central_bank_name="National Bank of Ethiopia",
        currency_code="ETB",
        currency_name="Birr éthiopien",
        domiciliation=DomiciliationRule(
            required=True,
            conditional=False,
            threshold_usd=0,
            mandatory_documents=[
                "commercial_invoice",
                "LC_mandatory",
                "import_permit_NBE",
                "certificate_of_origin",
                "packing_list",
            ],
            timeline_days=60,
            notes=(
                "Toutes les importations nécessitent un crédit documentaire (LC) "
                "irrévocable confirmé par une banque agréée NBE. "
                "Le NBE contrôle les allocations de devises via un système "
                "de priorités sectorielles (médicaments, carburant, industrie). "
                "Pénuries chroniques de devises étrangères."
            ),
        ),
        forex_regulation=ForexRegulation(
            regulation_level="strict",
            prior_authorization_required=True,
            authorization_threshold_usd=0,
            declaration_threshold_usd=500,
            repatriation_deadline_days=60,
            penalties=(
                "Confiscation des devises non déclarées + sanctions pénales "
                "(Art. 13 de la Directive FXD/44/2018 ; emprisonnement possible)."
            ),
            notes=(
                "Le birr éthiopien (ETB) est non convertible. "
                "La NBE alloue les devises selon ses priorités sectorielles. "
                "Réforme partielle initiée depuis 2019 : le taux de change "
                "a été dévalué de 30% en juillet 2023 dans le cadre d'un "
                "programme FMI. Le taux flottant dirigé est progressivement "
                "introduit mais les restrictions restent très importantes."
            ),
            legal_reference=(
                "Proclamation No. 600/2008 (NBE Establishment Proclamation) ; "
                "National Bank of Ethiopia Directive FXD/44/2018 re: "
                "Foreign Exchange Directives for Banks ; "
                "NBE Directive No. SBB/73/2022 re: import payment procedures"
            ),
            regulatory_body=(
                "National Bank of Ethiopia (NBE) – " "Foreign Exchange Management Directorate"
            ),
            imf_article_status=(
                "Article XIV – Régime transitoire. "
                "Restrictions importantes sur transactions courantes et capital."
            ),
        ),
        authorized_currencies=["USD", "EUR"],
        restricted_operations=[
            "cash_forex",
            "capital_account_transfers",
            "speculative_forex",
            "open_account_payment",
        ],
        special_regimes=["Industrial_Parks_forex_facilities", "Dire_Dawa_Free_Zone"],
    ),
    # ── TANZANIE ──────────────────────────────────────────────────────────────
    "TZ": CountryForexProfile(
        country_code="TZ",
        country_name="Tanzanie",
        central_bank_name="Bank of Tanzania",
        currency_code="TZS",
        currency_name="Shilling tanzanien",
        domiciliation=DomiciliationRule(
            required=False,
            conditional=True,
            threshold_usd=50_000,
            mandatory_documents=[
                "commercial_invoice",
                "bill_of_lading",
                "customs_declaration",
                "TRA_clearance_if_applicable",
            ],
            timeline_days=90,
            notes=(
                "La Tanzanie a libéralisé son régime de change depuis 1995. "
                "Domiciliation recommandée mais non systématiquement obligatoire "
                "pour les transactions < 50 000 USD. "
                "Le Tanzania Revenue Authority (TRA) supervise les déclarations "
                "douanières liées aux opérations de change."
            ),
        ),
        forex_regulation=ForexRegulation(
            regulation_level="moderate",
            prior_authorization_required=False,
            declaration_threshold_usd=50_000,
            repatriation_deadline_days=90,
            penalties=(
                "Amende administrative de TZS 1 000 000 à TZS 10 000 000 "
                "(Art. 28 Foreign Exchange Act 1992)."
            ),
            notes=(
                "Le shilling tanzanien (TZS) est librement échangeable "
                "sur le marché interbancaire. "
                "La Tanzanie fait partie de la Communauté d'Afrique de l'Est (EAC). "
                "Les transferts intra-EAC sont facilités mais pas totalement libres."
            ),
            legal_reference=(
                "Bank of Tanzania Act 2006 (Chapter 197) ; "
                "Foreign Exchange Act 1992 (Cap. 271, révisé 2022) ; "
                "BoT Foreign Exchange Regulations, 2022"
            ),
            regulatory_body=("Bank of Tanzania (BoT) – " "Financial Markets Department"),
            imf_article_status=(
                "Article VIII – Acceptation du 15 juillet 1996. " "Compte courant libéré."
            ),
        ),
        authorized_currencies=["USD", "EUR", "GBP", "KES", "UGX", "ZAR"],
        restricted_operations=["crypto_unlicensed"],
        special_regimes=["EPZ_Zanzibar_free_zone", "Tanzania_SEZ"],
    ),
    # ── AFRIQUE DU SUD ───────────────────────────────────────────────────────
    "ZA": CountryForexProfile(
        country_code="ZA",
        country_name="Afrique du Sud",
        central_bank_name="South African Reserve Bank",
        currency_code="ZAR",
        currency_name="Rand sud-africain",
        domiciliation=DomiciliationRule(
            required=True,
            conditional=False,
            threshold_usd=5_000,
            mandatory_documents=[
                "commercial_invoice",
                "SARS_customs_declaration",
                "authorised_dealer_confirmation",
                "shipping_documents",
            ],
            timeline_days=30,
            notes=(
                "Les Authorised Dealers (banques agréées SARB) traitent tous "
                "les paiements de commerce extérieur. "
                "Les exportateurs doivent déclarer et rapatrier les recettes "
                "d'exportation dans les 30 jours. "
                "Le Financial Surveillance Department (FinSurv) de la SARB "
                "gère le manuel Exchange Control."
            ),
        ),
        forex_regulation=ForexRegulation(
            regulation_level="moderate",
            prior_authorization_required=False,
            declaration_threshold_usd=5_000,
            repatriation_deadline_days=30,
            penalties=(
                "Amende jusqu'à ZAR 250 000 + emprisonnement jusqu'à 5 ans "
                "selon Section 27A du Currency and Exchanges Act No. 9/1933."
            ),
            notes=(
                "Le rand sud-africain (ZAR) est librement négociable. "
                "Le Currency and Exchanges Act No. 9 de 1933 et les "
                "Exchange Control Regulations de 1961 régissent toutes les transactions. "
                "La SARB publie un Exchange Control Manual détaillé mis à jour "
                "régulièrement. Depuis 2021, les entreprises peuvent conserver "
                "à l'étranger jusqu'à ZAR 10 milliards sans autorisation préalable."
            ),
            legal_reference=(
                "Currency and Exchanges Act No. 9 of 1933 (GN R.1111 du 1er décembre 1961) ; "
                "Exchange Control Regulations, 1961 (R.1111) ; "
                "SARB Exchange Control Manual (Version 2023) ; "
                "Financial Intelligence Centre Act (FICA) No. 38 of 2001"
            ),
            regulatory_body=(
                "South African Reserve Bank (SARB) – " "Financial Surveillance Department (FinSurv)"
            ),
            imf_article_status=(
                "Article VIII – Acceptation du 15 septembre 1973. "
                "Libération progressive du compte de capital."
            ),
        ),
        authorized_currencies=[
            "USD",
            "EUR",
            "GBP",
            "CHF",
            "JPY",
            "AUD",
            "CNY",
            "BWP",
            "LSL",
            "NAD",
            "SZL",
        ],
        restricted_operations=["offshore_loans_above_limit", "speculative_forex", "round_tripping"],
        special_regimes=[
            "Authorised_Dealer_network",
            "loop_structure_exemptions",
            "SACU_free_movement_ZAR",
        ],
    ),
    # ── ANGOLA ────────────────────────────────────────────────────────────────
    "AO": CountryForexProfile(
        country_code="AO",
        country_name="Angola",
        central_bank_name="Banco Nacional de Angola",
        currency_code="AOA",
        currency_name="Kwanza angolais",
        domiciliation=DomiciliationRule(
            required=True,
            conditional=False,
            threshold_usd=0,
            mandatory_documents=[
                "factura_proforma",
                "contrato_comercial",
                "licenca_importacao",
                "DU_declaracao_unica",
                "certificado_conformidade",
            ],
            timeline_days=90,
            notes=(
                "Toute importation doit être domiciliée auprès d'une banque "
                "commerciale agréée BNA. Le paiement en espèces est interdit. "
                "Pénurie chronique de dollars liée à la dépendance pétrolière. "
                "La Declaração Única (DU) remplace les anciens formulaires d'importation."
            ),
        ),
        forex_regulation=ForexRegulation(
            regulation_level="strict",
            prior_authorization_required=True,
            authorization_threshold_usd=0,
            declaration_threshold_usd=10_000,
            repatriation_deadline_days=90,
            penalties=(
                "Amende de 20% à 50% de la valeur de l'infraction + "
                "suspension des licences d'import (Art. 52 de la Lei n.º 5/97)."
            ),
            notes=(
                "Le kwanza angolais (AOA) est non convertible. "
                "La BNA alloue les dollars en priorité aux secteurs stratégiques. "
                "Réformes engagées depuis 2018 : loi sur l'investissement privé, "
                "libéralisation partielle des comptes en devises. "
                "Le taux de change est désormais fixé par le marché interbancaire "
                "mais la BNA intervient activement."
            ),
            legal_reference=(
                "Lei Cambial n.º 5/97 de 27 de Junho de 1997 ; "
                "Instrutivo do BNA n.º 02/2019 sobre operações cambiais ; "
                "Lei n.º 10/18 de 26 de Junho de 2018 (Lei do Investimento Privado)"
            ),
            regulatory_body=(
                "Banco Nacional de Angola (BNA) – "
                "Departamento de Câmbios e Operações Financeiras"
            ),
            imf_article_status=(
                "Article XIV – Régime transitoire. "
                "Restrictions importantes sur transactions courantes et capital."
            ),
        ),
        authorized_currencies=["USD", "EUR"],
        restricted_operations=[
            "cash_forex",
            "capital_account_transfers",
            "crypto_transactions",
        ],
        special_regimes=["oil_sector_forex_facilities", "ZEE_zones_economiques_especiais"],
    ),
    # ── ZAMBIE ────────────────────────────────────────────────────────────────
    "ZM": CountryForexProfile(
        country_code="ZM",
        country_name="Zambie",
        central_bank_name="Bank of Zambia",
        currency_code="ZMW",
        currency_name="Kwacha zambien",
        domiciliation=DomiciliationRule(
            required=False,
            conditional=True,
            threshold_usd=50_000,
            mandatory_documents=[
                "commercial_invoice",
                "bill_of_lading",
                "customs_declaration",
                "ZRA_tax_clearance_if_applicable",
            ],
            timeline_days=60,
            notes=(
                "La Zambie a libéralisé son compte courant depuis 1995 (Article VIII FMI). "
                "Domiciliation requise pour les grandes transactions (> 50 000 USD). "
                "La Zambia Revenue Authority (ZRA) supervise les déclarations douanières."
            ),
        ),
        forex_regulation=ForexRegulation(
            regulation_level="moderate",
            prior_authorization_required=False,
            declaration_threshold_usd=50_000,
            repatriation_deadline_days=60,
            penalties=(
                "Amende administrative jusqu'à ZMW 1 000 000 "
                "(Art. 17 de la Foreign Exchange Management Act 2023)."
            ),
            notes=(
                "Le kwacha zambien (ZMW) est relativement libre depuis 2012. "
                "La BoZ maintient un taux flottant géré. "
                "La Zambie a restructuré sa dette souveraine en 2023 après "
                "le défaut de 2020, ce qui a stabilisé le kwacha."
            ),
            legal_reference=(
                "Bank of Zambia Act (Cap. 360, révisé 2022) ; "
                "Foreign Exchange Management Act (FEMA) 2023 ; "
                "BoZ Directive on Foreign Currency Accounts 2021"
            ),
            regulatory_body=("Bank of Zambia (BoZ) – " "Financial Markets Department"),
            imf_article_status=(
                "Article VIII – Acceptation du 19 juillet 1995. " "Compte courant libéré."
            ),
        ),
        authorized_currencies=["USD", "EUR", "GBP", "ZAR"],
        restricted_operations=["crypto_unlicensed"],
        special_regimes=["mining_sector_forex_facilities", "Zambia_Multifacility_Economic_Zone"],
    ),
}

# ---------------------------------------------------------------------------
# MONETARY-UNION PROFILES – generated from the shared, uniform exchange
# regime of each union (identical rules across member states, so member
# profiles are derived from one authenticated template rather than guessed).
#   • UEMOA / BCEAO  – Franc CFA XOF (parité fixe 1 EUR = 655,957 XOF)
#   • CEMAC / BEAC   – Franc CFA XAF (parité fixe 1 EUR = 655,957 XAF)
# Members that already carry an explicit, curated profile above
# (Côte d'Ivoire, Sénégal) are never overwritten.
# ---------------------------------------------------------------------------

#: UEMOA member states (ISO2) sharing the BCEAO exchange regime.
_UEMOA_MEMBERS: Dict[str, str] = {
    "BF": "Burkina Faso",
    "BJ": "Bénin",
    "GW": "Guinée-Bissau",
    "ML": "Mali",
    "NE": "Niger",
    "TG": "Togo",
}

#: CEMAC member states (ISO2) sharing the BEAC exchange regime.
_CEMAC_MEMBERS: Dict[str, str] = {
    "CM": "Cameroun",
    "CF": "République centrafricaine",
    "CG": "Congo",
    "GA": "Gabon",
    "GQ": "Guinée équatoriale",
    "TD": "Tchad",
}


def _build_uemoa_profile(code: str, name: str) -> CountryForexProfile:
    """Build a BCEAO/UEMOA forex profile (uniform regime, Règlement 09/2010)."""
    return CountryForexProfile(
        country_code=code,
        country_name=name,
        central_bank_name="BCEAO",
        currency_code="XOF",
        currency_name="Franc CFA BCEAO",
        domiciliation=DomiciliationRule(
            required=True,
            conditional=False,
            threshold_usd=5_000,
            mandatory_documents=[
                "declaration_importation",
                "facture_commerciale",
                "domiciliation_BCEAO",
                "bordereau_de_suivi_des_cargaisons",
            ],
            timeline_days=120,
            notes=(
                "Zone UEMOA : la domiciliation bancaire suit les règles uniformes "
                "de la BCEAO. Le franc CFA (XOF) est arrimé à l'euro à parité fixe "
                "(1 EUR = 655,957 XOF). Les transferts intra-UEMOA sont libres ; "
                "les transferts hors zone requièrent une domiciliation et sont "
                "adossés à un motif justifié (importation, service, etc.)."
            ),
        ),
        forex_regulation=ForexRegulation(
            regulation_level="moderate",
            prior_authorization_required=False,
            declaration_threshold_usd=5_000,
            repatriation_deadline_days=120,
            penalties=(
                "Pénalités BCEAO conformément au Règlement UEMOA n° 09/2010 : "
                "amende de 25% à 200% du montant de l'infraction, saisie possible "
                "des avoirs en cas de fraude."
            ),
            notes=(
                "Zone CFA BCEAO (UEMOA) – convertibilité garantie via la "
                "coopération monétaire avec la France (compte d'opérations au "
                "Trésor français). Parité fixe EUR/XOF (655,957). Les transferts "
                "intra-UEMOA sont libres et non soumis à déclaration ; les "
                "transferts hors zone au-delà des seuils requièrent une "
                "domiciliation bancaire et une déclaration."
            ),
            legal_reference=(
                "Règlement n° 09/2010/CM/UEMOA du 1er octobre 2010 relatif aux "
                "relations financières extérieures des États membres de l'UEMOA ; "
                "Instruction BCEAO n° 04/2012/RB du 2 juillet 2012 ; "
                "Accord de coopération monétaire France-UEMOA du 14 novembre 1973"
            ),
            regulatory_body=(
                f"BCEAO – Direction Nationale pour {name} ; "
                f"Ministère chargé des Finances ({name})"
            ),
            imf_article_status="Article VIII – Zone UEMOA (acceptation collective du 1er juin 1996)",
        ),
        authorized_currencies=["EUR", "USD", "GBP"],
        restricted_operations=["speculative_forex", "crypto_non_agréé"],
        special_regimes=[
            "zone_UEMOA_libre_circulation_capitaux",
            "parité_fixe_EUR_XOF",
        ],
    )


def _build_cemac_profile(code: str, name: str) -> CountryForexProfile:
    """Build a BEAC/CEMAC forex profile (Règlement des changes 02/18/CEMAC/UMAC/CM 2018)."""
    return CountryForexProfile(
        country_code=code,
        country_name=name,
        central_bank_name="BEAC",
        currency_code="XAF",
        currency_name="Franc CFA BEAC",
        domiciliation=DomiciliationRule(
            required=False,
            conditional=True,
            # Le seuil légal est exprimé en monnaie locale (5 000 000 XAF) ; le
            # champ threshold_usd (USD) est laissé None pour ne pas publier une
            # conversion approximative. Le seuil exact figure dans les notes.
            threshold_usd=None,
            mandatory_documents=[
                "declaration_importation_exportation",
                "facture_commerciale",
                "domiciliation_bancaire_BEAC",
                "engagement_de_change",
            ],
            timeline_days=150,
            notes=(
                "Zone CEMAC : depuis l'entrée en vigueur du nouveau Règlement des "
                "changes le 1er mars 2019, la domiciliation bancaire est "
                "obligatoire pour les opérations d'importation et d'exportation "
                "dont le montant est supérieur à 5 000 000 XAF (règle "
                "conditionnelle : en deçà de ce seuil, la domiciliation n'est pas "
                "exigée). Le franc CFA (XAF) est arrimé à l'euro à parité fixe "
                "(1 EUR = 655,957 XAF). Les recettes d'exportation doivent être "
                "rapatriées et cédées via le système bancaire dans un délai de "
                "150 jours."
            ),
        ),
        forex_regulation=ForexRegulation(
            regulation_level="strict",
            prior_authorization_required=True,
            authorization_threshold_usd=None,
            declaration_threshold_usd=None,
            repatriation_deadline_days=150,
            penalties=(
                "Sanctions prévues par le Règlement des changes CEMAC de 2018 et "
                "les textes nationaux : amendes proportionnelles au montant de "
                "l'infraction et sanctions pénales pour non-rapatriement des "
                "recettes d'exportation."
            ),
            notes=(
                "Zone CFA BEAC (CEMAC) – convertibilité garantie via la coopération "
                "monétaire avec la France. Parité fixe EUR/XAF (655,957). Le "
                "Règlement des changes de 2018, appliqué à partir de 2019, a "
                "renforcé le rapatriement obligatoire des devises, la "
                "domiciliation des opérations et le contrôle des transferts par "
                "la BEAC. Les transferts hors zone requièrent la présentation de "
                "pièces justificatives et, au-delà de certains seuils, un accord "
                "préalable de la BEAC."
            ),
            legal_reference=(
                "Règlement n° 02/18/CEMAC/UMAC/CM du 21 décembre 2018 portant "
                "réglementation des changes dans la CEMAC (en vigueur le 1er mars "
                "2019) ; Instructions d'application de la BEAC (2019-2020) ; "
                "Convention de coopération monétaire entre les États membres de "
                "la CEMAC et la France du 23 novembre 1972"
            ),
            regulatory_body=(
                f"BEAC – Direction Nationale pour {name} ; "
                f"Commission Bancaire de l'Afrique Centrale (COBAC) ; "
                f"Ministère chargé des Finances ({name})"
            ),
            imf_article_status="Article VIII – Zone CEMAC",
        ),
        authorized_currencies=["EUR", "USD", "GBP"],
        restricted_operations=[
            "speculative_forex",
            "crypto_non_agréé",
            "capital_account_transfers",
        ],
        special_regimes=[
            "zone_CEMAC",
            "parité_fixe_EUR_XAF",
            "réglementation_changes_BEAC_2018",
        ],
    )


def _register_union_profiles() -> None:
    """Register generated union profiles for members lacking an explicit one."""
    for _code, _name in _UEMOA_MEMBERS.items():
        FOREX_PROFILES.setdefault(_code, _build_uemoa_profile(_code, _name))
    for _code, _name in _CEMAC_MEMBERS.items():
        FOREX_PROFILES.setdefault(_code, _build_cemac_profile(_code, _name))
    # ── Comores : franc comorien (KMF) arrimé à l'euro (1 EUR = 491,96775 KMF)
    FOREX_PROFILES.setdefault(
        "KM",
        CountryForexProfile(
            country_code="KM",
            country_name="Comores",
            central_bank_name="Banque Centrale des Comores",
            currency_code="KMF",
            currency_name="Franc comorien",
            domiciliation=DomiciliationRule(
                required=True,
                conditional=True,
                threshold_usd=5_000,
                mandatory_documents=[
                    "facture_commerciale",
                    "declaration_douaniere",
                    "domiciliation_bancaire",
                ],
                timeline_days=90,
                notes=(
                    "Le franc comorien (KMF) est arrimé à l'euro à parité fixe "
                    "(1 EUR = 491,96775 KMF) dans le cadre de l'accord de "
                    "coopération monétaire avec la France. Les opérations "
                    "commerciales transitent par les banques agréées."
                ),
            ),
            forex_regulation=ForexRegulation(
                regulation_level="moderate",
                prior_authorization_required=False,
                declaration_threshold_usd=5_000,
                repatriation_deadline_days=90,
                notes=(
                    "Convertibilité du compte courant garantie via la coopération "
                    "monétaire avec la France (compte d'opérations au Trésor "
                    "français). Parité fixe EUR/KMF (491,96775)."
                ),
                legal_reference=(
                    "Accord de coopération monétaire entre la France et les "
                    "Comores du 23 novembre 1979 ; réglementation des changes de "
                    "la Banque Centrale des Comores"
                ),
                regulatory_body="Banque Centrale des Comores (BCC) – Direction des Changes",
                imf_article_status="Article VIII",
            ),
            authorized_currencies=["EUR", "USD"],
            restricted_operations=["speculative_forex"],
            special_regimes=["parité_fixe_EUR_KMF"],
        ),
    )


_register_union_profiles()

# ---------------------------------------------------------------------------
# DEFAULT PROFILE for countries not yet fully detailed
# ---------------------------------------------------------------------------

_DEFAULT_PROFILE = CountryForexProfile(
    country_code="XX",
    country_name="Unknown",
    central_bank_name="Unknown",
    domiciliation=DomiciliationRule(
        required=False,
        conditional=True,
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
        legal_reference="Non renseigné – consulter la banque centrale locale.",
        regulatory_body="Banque Centrale Nationale",
        imf_article_status="Non renseigné",
    ),
    authorized_currencies=["USD", "EUR"],
)


# ---------------------------------------------------------------------------
# CURRENCY METADATA – currency_code & currency_name for all CENTRAL_BANKS
# (used by enrich_profile_with_rate to resolve the local currency)
# ---------------------------------------------------------------------------

#: Mapping ISO2 → (currency_code, currency_name, convertibility)
_CURRENCY_META: Dict[str, Tuple[str, str, str]] = {
    "MA": ("MAD", "Dirham marocain", "partially_convertible"),
    "DZ": ("DZD", "Dinar algérien", "non_convertible"),
    "TN": ("TND", "Dinar tunisien", "partially_convertible"),
    "EG": ("EGP", "Livre égyptienne", "partially_convertible"),
    "LY": ("LYD", "Dinar libyen", "non_convertible"),
    "SD": ("SDG", "Livre soudanaise", "non_convertible"),
    "NG": ("NGN", "Naira nigérian", "partially_convertible"),
    "GH": ("GHS", "Cedi ghanéen", "partially_convertible"),
    "CI": ("XOF", "Franc CFA BCEAO", "freely_convertible"),
    "SN": ("XOF", "Franc CFA BCEAO", "freely_convertible"),
    "ML": ("XOF", "Franc CFA BCEAO", "freely_convertible"),
    "BF": ("XOF", "Franc CFA BCEAO", "freely_convertible"),
    "GN": ("GNF", "Franc guinéen", "partially_convertible"),
    "NE": ("XOF", "Franc CFA BCEAO", "freely_convertible"),
    "TG": ("XOF", "Franc CFA BCEAO", "freely_convertible"),
    "BJ": ("XOF", "Franc CFA BCEAO", "freely_convertible"),
    "GW": ("XOF", "Franc CFA BCEAO", "freely_convertible"),
    "KE": ("KES", "Shilling kenyan", "freely_convertible"),
    "ET": ("ETB", "Birr éthiopien", "non_convertible"),
    "TZ": ("TZS", "Shilling tanzanien", "freely_convertible"),
    "UG": ("UGX", "Shilling ougandais", "freely_convertible"),
    "RW": ("RWF", "Franc rwandais", "partially_convertible"),
    "ZA": ("ZAR", "Rand sud-africain", "freely_convertible"),
    "AO": ("AOA", "Kwanza angolais", "non_convertible"),
    "ZM": ("ZMW", "Kwacha zambien", "partially_convertible"),
    "ZW": ("ZWL", "Dollar zimbabwéen", "non_convertible"),
    "BW": ("BWP", "Pula botswanaise", "freely_convertible"),
    "MW": ("MWK", "Kwacha malawien", "partially_convertible"),
    "MZ": ("MZN", "Metical mozambicain", "partially_convertible"),
    "NA": ("NAD", "Dollar namibien", "freely_convertible"),
    "LS": ("LSL", "Loti lesothan", "freely_convertible"),
    "SZ": ("SZL", "Lilangeni swazi", "freely_convertible"),
    "CM": ("XAF", "Franc CFA BEAC", "freely_convertible"),
    "GA": ("XAF", "Franc CFA BEAC", "freely_convertible"),
    "CG": ("XAF", "Franc CFA BEAC", "freely_convertible"),
    "CD": ("CDF", "Franc congolais", "partially_convertible"),
    "TD": ("XAF", "Franc CFA BEAC", "freely_convertible"),
    "CF": ("XAF", "Franc CFA BEAC", "freely_convertible"),
    "GQ": ("XAF", "Franc CFA BEAC", "freely_convertible"),
    "MR": ("MRU", "Ouguiya mauritanien", "partially_convertible"),
    "DJ": ("DJF", "Franc djiboutien", "freely_convertible"),
    "SO": ("SOS", "Shilling somalien", "non_convertible"),
    "ER": ("ERN", "Nakfa érythréen", "non_convertible"),
    "SS": ("SSP", "Livre sud-soudanaise", "non_convertible"),
    "MG": ("MGA", "Ariary malgache", "partially_convertible"),
    "MU": ("MUR", "Roupie mauricienne", "freely_convertible"),
    "SC": ("SCR", "Roupie seychelloise", "freely_convertible"),
    "KM": ("KMF", "Franc comorien", "freely_convertible"),
    "CV": ("CVE", "Escudo cap-verdien", "freely_convertible"),
    "GM": ("GMD", "Dalasi gambien", "partially_convertible"),
    "SL": ("SLE", "Leone sierra-léonais", "partially_convertible"),
    "LR": ("LRD", "Dollar libérien", "partially_convertible"),
    "ST": ("STN", "Dobra santoméen", "partially_convertible"),
    "BI": ("BIF", "Franc burundais", "partially_convertible"),
}


# ---------------------------------------------------------------------------
# PUBLIC HELPERS
# ---------------------------------------------------------------------------


def _normalize_iso2(country_code: str) -> str:
    """Normalize an ISO2/ISO3 country code to ISO2 for forex lookups."""
    try:
        from currencies.service import to_iso2

        return to_iso2(country_code)
    except Exception:
        return (country_code or "").upper()


def get_forex_profile(country_code: str) -> CountryForexProfile:
    """Return forex profile for a country (ISO2 or ISO3). Falls back to default profile."""
    code = _normalize_iso2(country_code)
    profile = FOREX_PROFILES.get(code)
    if profile is not None:
        return profile
    # Return a copy of the default profile with the correct country code
    default = _DEFAULT_PROFILE.model_copy(update={"country_code": code})
    return default


def get_domiciliation_rules(country_code: str) -> DomiciliationRule:
    """Return domiciliation rules for a country (ISO2)."""
    return get_forex_profile(country_code).domiciliation


def get_import_formalities(country_code: str) -> ImportFormalities:
    """Return import-side forex formalities (paiement des factures, délai de transfert)."""
    return get_forex_profile(country_code).import_formalities


def get_export_formalities(country_code: str) -> ExportFormalities:
    """Return export-side forex formalities (rapatriement des devises)."""
    return get_forex_profile(country_code).export_formalities


def get_currency_meta(country_code: str) -> Tuple[str, str, str]:
    """
    Return (currency_code, currency_name, convertibility) for a country.

    Falls back to ('USD', 'Dollar américain', 'freely_convertible') if unknown.
    """
    return _CURRENCY_META.get(
        _normalize_iso2(country_code), ("USD", "Dollar américain", "freely_convertible")
    )


def get_all_currency_meta() -> Dict[str, Tuple[str, str, str]]:
    """Return the full currency metadata mapping (ISO2 → (currency_code, name, convertibility)).

    Returns the dictionary directly. Callers must not mutate the returned object.
    """
    return _CURRENCY_META
