"""
African banks registry – central banks, commercial banks and regional development banks.

Coverage:
- All 54 African Union member states (central banks)
- Priority commercial banks for the 14 phase-1 countries
- Major pan-African and regional development banks
"""

from typing import Dict, List, Optional
from .models import CentralBank, CommercialBank, RegionalBank, BankingSystemInfo

# ---------------------------------------------------------------------------
# CENTRAL BANKS – 54 African countries
# ---------------------------------------------------------------------------

CENTRAL_BANKS: Dict[str, CentralBank] = {
    # ── NORTH AFRICA ────────────────────────────────────────────────────────
    "MA": CentralBank(
        country_code="MA", country_name="Maroc",
        name="Bank Al-Maghrib", abbreviation="BAM",
        website="https://www.bkam.ma", swift_code="BKAMMAMR",
        forex_regulation="strict", currency_code="MAD", currency_name="Dirham marocain",
    ),
    "DZ": CentralBank(
        country_code="DZ", country_name="Algérie",
        name="Banque d'Algérie", abbreviation="BA",
        website="https://www.bank-of-algeria.dz", swift_code="BADALYDZ",
        forex_regulation="strict", currency_code="DZD", currency_name="Dinar algérien",
    ),
    "TN": CentralBank(
        country_code="TN", country_name="Tunisie",
        name="Banque Centrale de Tunisie", abbreviation="BCT",
        website="https://www.bct.gov.tn", swift_code="BCTUTNTT",
        forex_regulation="moderate", currency_code="TND", currency_name="Dinar tunisien",
    ),
    "EG": CentralBank(
        country_code="EG", country_name="Égypte",
        name="Central Bank of Egypt", abbreviation="CBE",
        website="https://www.cbe.org.eg", swift_code="CBEGEGCX",
        forex_regulation="moderate", currency_code="EGP", currency_name="Livre égyptienne",
    ),
    "LY": CentralBank(
        country_code="LY", country_name="Libye",
        name="Central Bank of Libya", abbreviation="CBL",
        website="https://cbl.gov.ly", swift_code=None,
        forex_regulation="strict", currency_code="LYD", currency_name="Dinar libyen",
    ),
    "SD": CentralBank(
        country_code="SD", country_name="Soudan",
        name="Central Bank of Sudan", abbreviation="CBS",
        website="https://www.cbos.gov.sd", swift_code=None,
        forex_regulation="strict", currency_code="SDG", currency_name="Livre soudanaise",
    ),

    # ── WEST AFRICA ─────────────────────────────────────────────────────────
    "NG": CentralBank(
        country_code="NG", country_name="Nigeria",
        name="Central Bank of Nigeria", abbreviation="CBN",
        website="https://www.cbn.gov.ng", swift_code="CENBNGLX",
        forex_regulation="strict", currency_code="NGN", currency_name="Naira nigérian",
    ),
    "GH": CentralBank(
        country_code="GH", country_name="Ghana",
        name="Bank of Ghana", abbreviation="BoG",
        website="https://www.bog.gov.gh", swift_code="BGHAGHAL",
        forex_regulation="moderate", currency_code="GHS", currency_name="Cedi ghanéen",
    ),
    "CI": CentralBank(
        country_code="CI", country_name="Côte d'Ivoire",
        name="Banque Centrale des États de l'Afrique de l'Ouest", abbreviation="BCEAO",
        website="https://www.bceao.int", swift_code="BCEACIAB",
        forex_regulation="moderate", currency_code="XOF", currency_name="Franc CFA BCEAO",
    ),
    "SN": CentralBank(
        country_code="SN", country_name="Sénégal",
        name="Banque Centrale des États de l'Afrique de l'Ouest", abbreviation="BCEAO",
        website="https://www.bceao.int", swift_code="BCEASNDA",
        forex_regulation="moderate", currency_code="XOF", currency_name="Franc CFA BCEAO",
    ),
    "ML": CentralBank(
        country_code="ML", country_name="Mali",
        name="Banque Centrale des États de l'Afrique de l'Ouest", abbreviation="BCEAO",
        website="https://www.bceao.int", swift_code=None,
        forex_regulation="moderate", currency_code="XOF", currency_name="Franc CFA BCEAO",
    ),
    "BF": CentralBank(
        country_code="BF", country_name="Burkina Faso",
        name="Banque Centrale des États de l'Afrique de l'Ouest", abbreviation="BCEAO",
        website="https://www.bceao.int", swift_code=None,
        forex_regulation="moderate", currency_code="XOF", currency_name="Franc CFA BCEAO",
    ),
    "GN": CentralBank(
        country_code="GN", country_name="Guinée",
        name="Banque Centrale de la République de Guinée", abbreviation="BCRG",
        website="https://www.bcrg-guinee.org", swift_code=None,
        forex_regulation="moderate", currency_code="GNF", currency_name="Franc guinéen",
    ),
    "NE": CentralBank(
        country_code="NE", country_name="Niger",
        name="Banque Centrale des États de l'Afrique de l'Ouest", abbreviation="BCEAO",
        website="https://www.bceao.int", swift_code=None,
        forex_regulation="moderate", currency_code="XOF", currency_name="Franc CFA BCEAO",
    ),
    "BJ": CentralBank(
        country_code="BJ", country_name="Bénin",
        name="Banque Centrale des États de l'Afrique de l'Ouest", abbreviation="BCEAO",
        website="https://www.bceao.int", swift_code=None,
        forex_regulation="moderate", currency_code="XOF", currency_name="Franc CFA BCEAO",
    ),
    "TG": CentralBank(
        country_code="TG", country_name="Togo",
        name="Banque Centrale des États de l'Afrique de l'Ouest", abbreviation="BCEAO",
        website="https://www.bceao.int", swift_code=None,
        forex_regulation="moderate", currency_code="XOF", currency_name="Franc CFA BCEAO",
    ),
    "MR": CentralBank(
        country_code="MR", country_name="Mauritanie",
        name="Banque Centrale de Mauritanie", abbreviation="BCM",
        website="https://www.bcm.mr", swift_code=None,
        forex_regulation="moderate", currency_code="MRU", currency_name="Ouguiya mauritanien",
    ),
    "GM": CentralBank(
        country_code="GM", country_name="Gambie",
        name="Central Bank of The Gambia", abbreviation="CBG",
        website="https://www.cbg.gm", swift_code=None,
        forex_regulation="liberal", currency_code="GMD", currency_name="Dalasi gambien",
    ),
    "SL": CentralBank(
        country_code="SL", country_name="Sierra Leone",
        name="Bank of Sierra Leone", abbreviation="BSL",
        website="https://www.bsl.gov.sl", swift_code=None,
        forex_regulation="moderate", currency_code="SLL", currency_name="Leone sierra-léonais",
    ),
    "LR": CentralBank(
        country_code="LR", country_name="Liberia",
        name="Central Bank of Liberia", abbreviation="CBL",
        website="https://www.cbl.org.lr", swift_code=None,
        forex_regulation="liberal", currency_code="LRD", currency_name="Dollar libérien",
    ),
    "GW": CentralBank(
        country_code="GW", country_name="Guinée-Bissau",
        name="Banque Centrale des États de l'Afrique de l'Ouest", abbreviation="BCEAO",
        website="https://www.bceao.int", swift_code=None,
        forex_regulation="moderate", currency_code="XOF", currency_name="Franc CFA BCEAO",
    ),
    "CV": CentralBank(
        country_code="CV", country_name="Cap-Vert",
        name="Banco de Cabo Verde", abbreviation="BCV",
        website="https://www.bcv.cv", swift_code=None,
        forex_regulation="moderate", currency_code="CVE", currency_name="Escudo cap-verdien",
    ),

    # ── CENTRAL AFRICA ───────────────────────────────────────────────────────
    "CM": CentralBank(
        country_code="CM", country_name="Cameroun",
        name="Banque des États de l'Afrique Centrale", abbreviation="BEAC",
        website="https://www.beac.int", swift_code="BEACCMYA",
        forex_regulation="moderate", currency_code="XAF", currency_name="Franc CFA BEAC",
    ),
    "CD": CentralBank(
        country_code="CD", country_name="RD Congo",
        name="Banque Centrale du Congo", abbreviation="BCC",
        website="https://www.bcc.cd", swift_code=None,
        forex_regulation="strict", currency_code="CDF", currency_name="Franc congolais",
    ),
    "CG": CentralBank(
        country_code="CG", country_name="Congo",
        name="Banque des États de l'Afrique Centrale", abbreviation="BEAC",
        website="https://www.beac.int", swift_code=None,
        forex_regulation="moderate", currency_code="XAF", currency_name="Franc CFA BEAC",
    ),
    "GA": CentralBank(
        country_code="GA", country_name="Gabon",
        name="Banque des États de l'Afrique Centrale", abbreviation="BEAC",
        website="https://www.beac.int", swift_code=None,
        forex_regulation="moderate", currency_code="XAF", currency_name="Franc CFA BEAC",
    ),
    "CF": CentralBank(
        country_code="CF", country_name="République centrafricaine",
        name="Banque des États de l'Afrique Centrale", abbreviation="BEAC",
        website="https://www.beac.int", swift_code=None,
        forex_regulation="moderate", currency_code="XAF", currency_name="Franc CFA BEAC",
    ),
    "TD": CentralBank(
        country_code="TD", country_name="Tchad",
        name="Banque des États de l'Afrique Centrale", abbreviation="BEAC",
        website="https://www.beac.int", swift_code=None,
        forex_regulation="moderate", currency_code="XAF", currency_name="Franc CFA BEAC",
    ),
    "GQ": CentralBank(
        country_code="GQ", country_name="Guinée équatoriale",
        name="Banque des États de l'Afrique Centrale", abbreviation="BEAC",
        website="https://www.beac.int", swift_code=None,
        forex_regulation="moderate", currency_code="XAF", currency_name="Franc CFA BEAC",
    ),
    "ST": CentralBank(
        country_code="ST", country_name="Sao Tomé-et-Príncipe",
        name="Banco Central de São Tomé e Príncipe", abbreviation="BCSTP",
        website="https://www.bcstp.st", swift_code=None,
        forex_regulation="moderate", currency_code="STN", currency_name="Dobra de Sao Tomé",
    ),

    # ── EAST AFRICA ──────────────────────────────────────────────────────────
    "KE": CentralBank(
        country_code="KE", country_name="Kenya",
        name="Central Bank of Kenya", abbreviation="CBK",
        website="https://www.centralbank.go.ke", swift_code="CBKEKENA",
        forex_regulation="liberal", currency_code="KES", currency_name="Shilling kényan",
    ),
    "ET": CentralBank(
        country_code="ET", country_name="Éthiopie",
        name="National Bank of Ethiopia", abbreviation="NBE",
        website="https://www.nbe.gov.et", swift_code=None,
        forex_regulation="strict", currency_code="ETB", currency_name="Birr éthiopien",
    ),
    "TZ": CentralBank(
        country_code="TZ", country_name="Tanzanie",
        name="Bank of Tanzania", abbreviation="BoT",
        website="https://www.bot.go.tz", swift_code="BOTATZTZ",
        forex_regulation="moderate", currency_code="TZS", currency_name="Shilling tanzanien",
    ),
    "UG": CentralBank(
        country_code="UG", country_name="Ouganda",
        name="Bank of Uganda", abbreviation="BoU",
        website="https://www.bou.or.ug", swift_code=None,
        forex_regulation="liberal", currency_code="UGX", currency_name="Shilling ougandais",
    ),
    "RW": CentralBank(
        country_code="RW", country_name="Rwanda",
        name="National Bank of Rwanda", abbreviation="BNR",
        website="https://www.bnr.rw", swift_code=None,
        forex_regulation="liberal", currency_code="RWF", currency_name="Franc rwandais",
    ),
    "BI": CentralBank(
        country_code="BI", country_name="Burundi",
        name="Banque de la République du Burundi", abbreviation="BRB",
        website="https://www.brb.bi", swift_code=None,
        forex_regulation="moderate", currency_code="BIF", currency_name="Franc burundais",
    ),
    "SO": CentralBank(
        country_code="SO", country_name="Somalie",
        name="Central Bank of Somalia", abbreviation="CBS",
        website="https://www.centralbank.gov.so", swift_code=None,
        forex_regulation="liberal", currency_code="SOS", currency_name="Shilling somalien",
    ),
    "DJ": CentralBank(
        country_code="DJ", country_name="Djibouti",
        name="Banque Centrale de Djibouti", abbreviation="BCD",
        website="https://www.banque-centrale.dj", swift_code=None,
        forex_regulation="liberal", currency_code="DJF", currency_name="Franc djiboutien",
    ),
    "ER": CentralBank(
        country_code="ER", country_name="Érythrée",
        name="Bank of Eritrea", abbreviation="BoE",
        website=None, swift_code=None,
        forex_regulation="strict", currency_code="ERN", currency_name="Nakfa érythréen",
    ),
    "SS": CentralBank(
        country_code="SS", country_name="Soudan du Sud",
        name="Bank of South Sudan", abbreviation="BSS",
        website="https://www.bankofsouthsudan.org", swift_code=None,
        forex_regulation="strict", currency_code="SSP", currency_name="Livre sud-soudanaise",
    ),

    # ── SOUTHERN AFRICA ──────────────────────────────────────────────────────
    "ZA": CentralBank(
        country_code="ZA", country_name="Afrique du Sud",
        name="South African Reserve Bank", abbreviation="SARB",
        website="https://www.resbank.co.za", swift_code="RESOZAJJ",
        forex_regulation="moderate", currency_code="ZAR", currency_name="Rand sud-africain",
    ),
    "AO": CentralBank(
        country_code="AO", country_name="Angola",
        name="Banco Nacional de Angola", abbreviation="BNA",
        website="https://www.bna.ao", swift_code=None,
        forex_regulation="strict", currency_code="AOA", currency_name="Kwanza angolais",
    ),
    "ZM": CentralBank(
        country_code="ZM", country_name="Zambie",
        name="Bank of Zambia", abbreviation="BoZ",
        website="https://www.boz.zm", swift_code=None,
        forex_regulation="moderate", currency_code="ZMW", currency_name="Kwacha zambien",
    ),
    "ZW": CentralBank(
        country_code="ZW", country_name="Zimbabwe",
        name="Reserve Bank of Zimbabwe", abbreviation="RBZ",
        website="https://www.rbz.co.zw", swift_code=None,
        forex_regulation="strict", currency_code="ZWL", currency_name="Dollar zimbabwéen",
    ),
    "MZ": CentralBank(
        country_code="MZ", country_name="Mozambique",
        name="Banco de Moçambique", abbreviation="BM",
        website="https://www.bancomoc.mz", swift_code=None,
        forex_regulation="moderate", currency_code="MZN", currency_name="Metical mozambicain",
    ),
    "MW": CentralBank(
        country_code="MW", country_name="Malawi",
        name="Reserve Bank of Malawi", abbreviation="RBM",
        website="https://www.rbm.mw", swift_code=None,
        forex_regulation="moderate", currency_code="MWK", currency_name="Kwacha malawien",
    ),
    "BW": CentralBank(
        country_code="BW", country_name="Botswana",
        name="Bank of Botswana", abbreviation="BoB",
        website="https://www.bankofbotswana.bw", swift_code=None,
        forex_regulation="liberal", currency_code="BWP", currency_name="Pula botswanien",
    ),
    "NA": CentralBank(
        country_code="NA", country_name="Namibie",
        name="Bank of Namibia", abbreviation="BoN",
        website="https://www.bon.com.na", swift_code=None,
        forex_regulation="moderate", currency_code="NAD", currency_name="Dollar namibien",
    ),
    "LS": CentralBank(
        country_code="LS", country_name="Lesotho",
        name="Central Bank of Lesotho", abbreviation="CBL",
        website="https://www.centralbank.org.ls", swift_code=None,
        forex_regulation="moderate", currency_code="LSL", currency_name="Loti lésothien",
    ),
    "SZ": CentralBank(
        country_code="SZ", country_name="Eswatini",
        name="Central Bank of Eswatini", abbreviation="CBE",
        website="https://www.centralbank.org.sz", swift_code=None,
        forex_regulation="moderate", currency_code="SZL", currency_name="Lilangeni swazi",
    ),
    "MG": CentralBank(
        country_code="MG", country_name="Madagascar",
        name="Banque Centrale de Madagascar", abbreviation="BCM",
        website="https://www.banky-foiben-i-madagasikara.mg", swift_code=None,
        forex_regulation="moderate", currency_code="MGA", currency_name="Ariary malgache",
    ),
    "MU": CentralBank(
        country_code="MU", country_name="Maurice",
        name="Bank of Mauritius", abbreviation="BoM",
        website="https://www.bom.mu", swift_code=None,
        forex_regulation="liberal", currency_code="MUR", currency_name="Roupie mauricienne",
    ),
    "SC": CentralBank(
        country_code="SC", country_name="Seychelles",
        name="Central Bank of Seychelles", abbreviation="CBS",
        website="https://www.cbs.sc", swift_code=None,
        forex_regulation="liberal", currency_code="SCR", currency_name="Roupie seychelloise",
    ),
    "KM": CentralBank(
        country_code="KM", country_name="Comores",
        name="Banque Centrale des Comores", abbreviation="BCC",
        website="https://www.banque-comores.km", swift_code=None,
        forex_regulation="moderate", currency_code="KMF", currency_name="Franc comorien",
    ),
}

# ---------------------------------------------------------------------------
# COMMERCIAL BANKS – Phase-1 priority countries
# ---------------------------------------------------------------------------

COMMERCIAL_BANKS: Dict[str, List[CommercialBank]] = {
    "MA": [
        CommercialBank(
            name="Attijariwafa Bank", abbreviation="AWB", country_code="MA",
            swift_code="BCMAMAMC", trade_finance=True,
            correspondent_banks=["BNP_PARIBAS", "SOCIETE_GENERALE", "CREDIT_AGRICOLE"],
            services=["LC", "documentary_collection", "bank_guarantee", "forex", "trade_loans"],
        ),
        CommercialBank(
            name="Banque Centrale Populaire", abbreviation="BCP", country_code="MA",
            swift_code="BCPPMAMR", trade_finance=True,
            correspondent_banks=["CREDIT_MUTUEL", "NATIXIS"],
            services=["LC", "documentary_collection", "bank_guarantee", "forex"],
        ),
        CommercialBank(
            name="BMCE Bank of Africa", abbreviation="BMCE", country_code="MA",
            swift_code="BCMOMAMR", trade_finance=True,
            correspondent_banks=["COMMERZBANK", "STANDARD_CHARTERED"],
            services=["LC", "bank_guarantee", "forex", "trade_loans", "supply_chain_finance"],
        ),
        CommercialBank(
            name="Société Générale Maroc", abbreviation="SGM", country_code="MA",
            swift_code="SGMBMAMC", trade_finance=True,
            correspondent_banks=["SOCIETE_GENERALE"],
            services=["LC", "documentary_collection", "bank_guarantee", "forex"],
        ),
    ],
    "DZ": [
        CommercialBank(
            name="Banque Extérieure d'Algérie", abbreviation="BEA", country_code="DZ",
            swift_code="BEAADZAL", trade_finance=True,
            correspondent_banks=["BNP_PARIBAS", "SOCIETE_GENERALE"],
            services=["LC", "bank_guarantee", "forex", "trade_loans"],
        ),
        CommercialBank(
            name="Banque Nationale d'Algérie", abbreviation="BNA", country_code="DZ",
            swift_code="BNAADZAL", trade_finance=True,
            correspondent_banks=["CREDIT_AGRICOLE"],
            services=["LC", "documentary_collection", "bank_guarantee"],
        ),
        CommercialBank(
            name="Crédit Populaire d'Algérie", abbreviation="CPA", country_code="DZ",
            swift_code=None, trade_finance=True,
            correspondent_banks=["NATIXIS"],
            services=["LC", "bank_guarantee", "forex"],
        ),
    ],
    "TN": [
        CommercialBank(
            name="Banque Internationale Arabe de Tunisie", abbreviation="BIAT",
            country_code="TN", swift_code="BIATTNTT", trade_finance=True,
            correspondent_banks=["SOCIETE_GENERALE", "BNP_PARIBAS"],
            services=["LC", "documentary_collection", "bank_guarantee", "forex"],
        ),
        CommercialBank(
            name="Société Tunisienne de Banque", abbreviation="STB",
            country_code="TN", swift_code="STBKTNTT", trade_finance=True,
            correspondent_banks=["BNP_PARIBAS"],
            services=["LC", "documentary_collection", "bank_guarantee"],
        ),
        CommercialBank(
            name="Banque de l'Habitat", abbreviation="BH",
            country_code="TN", swift_code=None, trade_finance=False,
            correspondent_banks=[],
            services=["real_estate", "consumer_credit"],
        ),
    ],
    "EG": [
        CommercialBank(
            name="National Bank of Egypt", abbreviation="NBE", country_code="EG",
            swift_code="NBEGEGCX", trade_finance=True,
            correspondent_banks=["CITIBANK", "JP_MORGAN", "COMMERZBANK"],
            services=["LC", "documentary_collection", "bank_guarantee", "forex", "export_finance"],
        ),
        CommercialBank(
            name="Banque Misr", abbreviation="BM", country_code="EG",
            swift_code="BMISEGCX", trade_finance=True,
            correspondent_banks=["BNP_PARIBAS", "SOCIETE_GENERALE"],
            services=["LC", "documentary_collection", "bank_guarantee", "forex"],
        ),
        CommercialBank(
            name="Commercial International Bank", abbreviation="CIB", country_code="EG",
            swift_code="CIBEEGCX", trade_finance=True,
            correspondent_banks=["STANDARD_CHARTERED", "CITIBANK"],
            services=["LC", "documentary_collection", "bank_guarantee", "forex", "trade_loans"],
        ),
    ],
    "NG": [
        CommercialBank(
            name="Zenith Bank", abbreviation="ZENITH", country_code="NG",
            swift_code="ZEIBNGLA", trade_finance=True,
            correspondent_banks=["CITIBANK", "STANDARD_CHARTERED", "JP_MORGAN"],
            services=["LC", "documentary_collection", "bank_guarantee", "forex", "export_finance"],
        ),
        CommercialBank(
            name="United Bank for Africa", abbreviation="UBA", country_code="NG",
            swift_code="UNAFNGLA", trade_finance=True,
            correspondent_banks=["CITIBANK", "BNP_PARIBAS"],
            services=["LC", "bank_guarantee", "forex", "trade_loans"],
        ),
        CommercialBank(
            name="Guaranty Trust Bank", abbreviation="GTBank", country_code="NG",
            swift_code="GTBINGLA", trade_finance=True,
            correspondent_banks=["STANDARD_CHARTERED", "COMMERZBANK"],
            services=["LC", "documentary_collection", "bank_guarantee", "forex"],
        ),
        CommercialBank(
            name="First Bank of Nigeria", abbreviation="FBN", country_code="NG",
            swift_code="FBNINGLA", trade_finance=True,
            correspondent_banks=["CITIBANK", "BARCLAYS"],
            services=["LC", "documentary_collection", "bank_guarantee", "forex", "export_finance"],
        ),
    ],
    "GH": [
        CommercialBank(
            name="Ghana Commercial Bank", abbreviation="GCB", country_code="GH",
            swift_code="GHCBGHAC", trade_finance=True,
            correspondent_banks=["CITIBANK", "STANDARD_CHARTERED"],
            services=["LC", "documentary_collection", "bank_guarantee", "forex"],
        ),
        CommercialBank(
            name="Ecobank Ghana", abbreviation="ECOBANK-GH", country_code="GH",
            swift_code="ECOCGHAC", trade_finance=True,
            correspondent_banks=["CITIBANK", "SOCIETE_GENERALE"],
            services=["LC", "bank_guarantee", "forex", "trade_loans"],
        ),
    ],
    "CI": [
        CommercialBank(
            name="Société Générale Côte d'Ivoire", abbreviation="SGCI", country_code="CI",
            swift_code="SGBFCIAB", trade_finance=True,
            correspondent_banks=["SOCIETE_GENERALE"],
            services=["LC", "documentary_collection", "bank_guarantee", "forex"],
        ),
        CommercialBank(
            name="Ecobank Côte d'Ivoire", abbreviation="ECOBANK-CI", country_code="CI",
            swift_code="ECOCCIAB", trade_finance=True,
            correspondent_banks=["CITIBANK"],
            services=["LC", "bank_guarantee", "forex"],
        ),
    ],
    "SN": [
        CommercialBank(
            name="Banque de l'Habitat du Sénégal", abbreviation="BHS", country_code="SN",
            swift_code=None, trade_finance=False,
            services=["real_estate"],
        ),
        CommercialBank(
            name="Ecobank Sénégal", abbreviation="ECOBANK-SN", country_code="SN",
            swift_code="ECOCSNDA", trade_finance=True,
            correspondent_banks=["CITIBANK"],
            services=["LC", "bank_guarantee", "forex"],
        ),
        CommercialBank(
            name="Société Générale Sénégal", abbreviation="SGS", country_code="SN",
            swift_code="SGSNSNDA", trade_finance=True,
            correspondent_banks=["SOCIETE_GENERALE"],
            services=["LC", "documentary_collection", "bank_guarantee", "forex"],
        ),
    ],
    "KE": [
        CommercialBank(
            name="Kenya Commercial Bank", abbreviation="KCB", country_code="KE",
            swift_code="KCBLKENA", trade_finance=True,
            correspondent_banks=["CITIBANK", "STANDARD_CHARTERED"],
            services=["LC", "documentary_collection", "bank_guarantee", "forex", "trade_loans"],
        ),
        CommercialBank(
            name="Equity Bank Kenya", abbreviation="EQUITY", country_code="KE",
            swift_code="EQBLKENA", trade_finance=True,
            correspondent_banks=["CITIBANK"],
            services=["LC", "bank_guarantee", "forex", "mobile_banking"],
        ),
        CommercialBank(
            name="Standard Chartered Kenya", abbreviation="SCB-KE", country_code="KE",
            swift_code="SCBLKENA", trade_finance=True,
            correspondent_banks=["STANDARD_CHARTERED"],
            services=["LC", "documentary_collection", "bank_guarantee", "forex", "export_finance"],
        ),
    ],
    "ET": [
        CommercialBank(
            name="Commercial Bank of Ethiopia", abbreviation="CBE", country_code="ET",
            swift_code="CBETETAA", trade_finance=True,
            correspondent_banks=["CITIBANK", "COMMERZBANK"],
            services=["LC", "documentary_collection", "bank_guarantee", "forex"],
        ),
        CommercialBank(
            name="Dashen Bank", abbreviation="DASHEN", country_code="ET",
            swift_code=None, trade_finance=True,
            correspondent_banks=["COMMERZBANK"],
            services=["LC", "bank_guarantee", "forex"],
        ),
    ],
    "TZ": [
        CommercialBank(
            name="CRDB Bank", abbreviation="CRDB", country_code="TZ",
            swift_code="CORUTZTZ", trade_finance=True,
            correspondent_banks=["STANDARD_CHARTERED", "COMMERZBANK"],
            services=["LC", "documentary_collection", "bank_guarantee", "forex"],
        ),
        CommercialBank(
            name="NMB Bank Tanzania", abbreviation="NMB", country_code="TZ",
            swift_code="NMBCTZTZ", trade_finance=True,
            correspondent_banks=["CITIBANK"],
            services=["LC", "bank_guarantee", "forex"],
        ),
    ],
    "ZA": [
        CommercialBank(
            name="Standard Bank South Africa", abbreviation="SBSA", country_code="ZA",
            swift_code="SBZAZAJJ", trade_finance=True,
            correspondent_banks=["CITIBANK", "JP_MORGAN", "COMMERZBANK"],
            services=["LC", "documentary_collection", "bank_guarantee", "forex", "export_finance", "supply_chain_finance"],
        ),
        CommercialBank(
            name="FirstRand Bank (FNB)", abbreviation="FNB", country_code="ZA",
            swift_code="FIRNZAJJ", trade_finance=True,
            correspondent_banks=["BARCLAYS", "CITIBANK"],
            services=["LC", "documentary_collection", "bank_guarantee", "forex"],
        ),
        CommercialBank(
            name="Absa Bank South Africa", abbreviation="ABSA", country_code="ZA",
            swift_code="ABSAZAJJ", trade_finance=True,
            correspondent_banks=["BARCLAYS", "STANDARD_CHARTERED"],
            services=["LC", "documentary_collection", "bank_guarantee", "forex", "export_finance"],
        ),
        CommercialBank(
            name="Nedbank", abbreviation="NEDBANK", country_code="ZA",
            swift_code="NEDSZAJJ", trade_finance=True,
            correspondent_banks=["CITIBANK"],
            services=["LC", "bank_guarantee", "forex"],
        ),
    ],
    "AO": [
        CommercialBank(
            name="Banco Angolano de Investimentos", abbreviation="BAI", country_code="AO",
            swift_code="BAIEAOLU", trade_finance=True,
            correspondent_banks=["CITIBANK", "COMMERZBANK"],
            services=["LC", "bank_guarantee", "forex"],
        ),
        CommercialBank(
            name="Banco BIC Angola", abbreviation="BIC", country_code="AO",
            swift_code=None, trade_finance=True,
            correspondent_banks=[],
            services=["LC", "forex"],
        ),
    ],
    "ZM": [
        CommercialBank(
            name="Zambia National Commercial Bank", abbreviation="ZANACO", country_code="ZM",
            swift_code="ZANZZMLU", trade_finance=True,
            correspondent_banks=["STANDARD_CHARTERED"],
            services=["LC", "documentary_collection", "bank_guarantee", "forex"],
        ),
        CommercialBank(
            name="Standard Chartered Zambia", abbreviation="SCB-ZM", country_code="ZM",
            swift_code="SCBLZMLU", trade_finance=True,
            correspondent_banks=["STANDARD_CHARTERED"],
            services=["LC", "documentary_collection", "bank_guarantee", "forex", "trade_loans"],
        ),
    ],
}

# ---------------------------------------------------------------------------
# REGIONAL / DEVELOPMENT BANKS
# ---------------------------------------------------------------------------

REGIONAL_BANKS: List[RegionalBank] = [
    RegionalBank(
        name="African Development Bank", abbreviation="AfDB",
        region="Pan-African", headquarters="Abidjan, Côte d'Ivoire",
        website="https://www.afdb.org",
        member_countries=list(CENTRAL_BANKS.keys()),
        focus_areas=["infrastructure", "agriculture", "industry", "trade_finance"],
    ),
    RegionalBank(
        name="Afreximbank – African Export-Import Bank", abbreviation="Afreximbank",
        region="Pan-African", headquarters="Le Caire, Égypte",
        website="https://www.afreximbank.com",
        member_countries=list(CENTRAL_BANKS.keys()),
        focus_areas=["export_finance", "trade_finance", "project_finance", "LC_confirmation"],
    ),
    RegionalBank(
        name="Banque Ouest Africaine de Développement", abbreviation="BOAD",
        region="West Africa (UEMOA)", headquarters="Lomé, Togo",
        website="https://www.boad.org",
        member_countries=["BJ", "BF", "CI", "GW", "ML", "NE", "SN", "TG"],
        focus_areas=["infrastructure", "agriculture", "SME_finance"],
    ),
    RegionalBank(
        name="East African Development Bank", abbreviation="EADB",
        region="East Africa (EAC)", headquarters="Kampala, Ouganda",
        website="https://www.eadb.org",
        member_countries=["KE", "TZ", "UG", "RW", "SS"],
        focus_areas=["infrastructure", "industry", "SME_finance"],
    ),
    RegionalBank(
        name="Development Bank of Southern Africa", abbreviation="DBSA",
        region="Southern Africa (SADC)", headquarters="Midrand, Afrique du Sud",
        website="https://www.dbsa.org",
        member_countries=["ZA", "BW", "LS", "NA", "SZ", "MZ", "ZM", "ZW", "MG", "MU"],
        focus_areas=["infrastructure", "energy", "water", "transport"],
    ),
    RegionalBank(
        name="Banque de Développement des États de l'Afrique Centrale", abbreviation="BDEAC",
        region="Central Africa (CEMAC)", headquarters="Brazzaville, Congo",
        website="https://www.bdeac.org",
        member_countries=["CM", "CF", "TD", "CG", "GA", "GQ"],
        focus_areas=["infrastructure", "SME_finance", "agriculture"],
    ),
    RegionalBank(
        name="Trade and Development Bank", abbreviation="TDB",
        region="Eastern & Southern Africa (COMESA)", headquarters="Nairobi, Kenya",
        website="https://www.tdbgroup.org",
        member_countries=["KE", "ET", "TZ", "UG", "ZM", "ZW", "MU", "EG", "SD"],
        focus_areas=["trade_finance", "project_finance", "LC_confirmation"],
    ),
]


# ---------------------------------------------------------------------------
# PUBLIC HELPERS
# ---------------------------------------------------------------------------

def get_central_bank(country_code: str) -> Optional[CentralBank]:
    """Return central bank data for a given ISO2 country code (case-insensitive)."""
    return CENTRAL_BANKS.get(country_code.upper())


def get_country_banks(country_code: str) -> BankingSystemInfo:
    """Return complete banking information for a country."""
    code = country_code.upper()
    cb = CENTRAL_BANKS.get(code)
    if cb is None:
        return BankingSystemInfo(
            country_code=code,
            country_name="Unknown",
            central_bank=CentralBank(
                country_code=code, country_name="Unknown",
                name="Unknown", abbreviation="N/A",
                forex_regulation="unknown",
                currency_code="N/A", currency_name="Unknown",
            ),
        )
    return BankingSystemInfo(
        country_code=code,
        country_name=cb.country_name,
        central_bank=cb,
        commercial_banks=COMMERCIAL_BANKS.get(code, []),
        regional_banks=[rb for rb in REGIONAL_BANKS if code in rb.member_countries],
    )


def get_regional_banks(region: Optional[str] = None) -> List[RegionalBank]:
    """Return regional/development banks, optionally filtered by region."""
    if region is None:
        return REGIONAL_BANKS
    region_lower = region.lower()
    return [
        rb for rb in REGIONAL_BANKS
        if region_lower in rb.region.lower()
    ]
