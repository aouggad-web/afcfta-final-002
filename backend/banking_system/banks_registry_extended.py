"""
Extended commercial-banks registry – broad coverage of major trade-finance
banks across all 54 African Union member states.

This module supplements ``banks_registry.COMMERCIAL_BANKS`` with additional
well-established commercial banks per country. The goal is breadth: for every
country we list the leading universal / trade-finance banks (public,
private and pan-African subsidiaries) that businesses actually use for
letters of credit, documentary collections, guarantees and FX.

Data-quality policy
-------------------
* ``name`` / ``abbreviation`` / ``website`` / ``address`` (head-office city)
  are stable, publicly verifiable identifiers.
* ``swift_code`` (BIC) is filled only where it is well documented; otherwise
  it is left ``None`` rather than guessed.
* ``phone`` / ``email`` are intentionally left ``None`` here – branch contact
  numbers change frequently and should be confirmed with the bank directly.
  The head-office ``website`` is the authoritative contact channel.

The entries are merged into ``COMMERCIAL_BANKS`` at import time by
``banks_registry`` via :func:`merge_into`, de-duplicating on the bank
abbreviation (falling back to the bank name) so existing curated entries are
never overwritten.
"""

from typing import Dict, List

from .models import BankContact, CommercialBank

# Default trade-finance service bundle for a universal commercial bank.
_DEFAULT_SERVICES: List[str] = [
    "LC",
    "documentary_collection",
    "bank_guarantee",
    "forex",
]

# ---------------------------------------------------------------------------
# Raw data: ISO2 country code → list of bank definitions (kwargs).
# ``country_code`` is injected automatically from the dict key.
# ---------------------------------------------------------------------------

_EXTRA: Dict[str, List[dict]] = {
    # ═══════════════════════════ NORTH AFRICA ═══════════════════════════════
    "MA": [
        dict(
            name="CIH Bank",
            abbreviation="CIH",
            swift_code="CIHMMAMC",
            website="https://www.cihbank.ma",
            address="187, Avenue Hassan II, Casablanca 20000, Maroc",
            license_type="Banque universelle",
        ),
        dict(
            name="Crédit du Maroc",
            abbreviation="CDM",
            swift_code="CDMAMAMC",
            website="https://www.creditdumaroc.ma",
            address="48-58, Bd Mohammed V, Casablanca, Maroc",
            correspondent_banks=["HOLMARCOM"],
            license_type="Banque universelle",
        ),
        dict(
            name="Crédit Agricole du Maroc",
            abbreviation="CAM",
            swift_code="CNCAMAMR",
            website="https://www.creditagricole.ma",
            address="28, Rue Abou Faris Al Marini, Rabat, Maroc",
            license_type="Banque publique spécialisée",
        ),
        dict(
            name="BMCI (BNP Paribas)",
            abbreviation="BMCI",
            swift_code="BMCIMAMC",
            website="https://www.bmci.ma",
            address="26, Place des Nations Unies, Casablanca, Maroc",
            correspondent_banks=["BNP_PARIBAS"],
            license_type="Filiale internationale",
        ),
        dict(
            name="Al Barid Bank",
            abbreviation="ABB",
            swift_code="BdlPMAMC",
            website="https://www.albaridbank.ma",
            address="798, Bd Ghandi, Casablanca, Maroc",
            license_type="Banque postale",
        ),
        dict(
            name="Bank Assafa (finance participative)",
            abbreviation="ASSAFA",
            website="https://www.bankassafa.com",
            address="Casablanca, Maroc",
            services=["murabaha", "bank_guarantee", "trade_finance_islamique"],
            license_type="Banque participative",
        ),
    ],
    "DZ": [
        dict(
            name="Banque de l'Agriculture et du Développement Rural",
            abbreviation="BADR",
            swift_code="BADRDZAL",
            website="https://www.badr-bank.dz",
            address="17, Bd Colonel Amirouche, Alger 16000, Algérie",
            license_type="Banque publique",
        ),
        dict(
            name="Banque de Développement Local",
            abbreviation="BDL",
            website="https://www.bdl.dz",
            address="5, Rue Gaci Amar, Staouéli, Alger, Algérie",
            license_type="Banque publique",
        ),
        dict(
            name="CNEP-Banque",
            abbreviation="CNEP",
            website="https://www.cnepbanque.dz",
            address="Garidi, Kouba, Alger, Algérie",
            license_type="Banque publique (épargne et logement)",
        ),
        dict(
            name="Société Générale Algérie",
            abbreviation="SGA",
            swift_code="SOGEDZAL",
            website="https://www.societegenerale.dz",
            address="Zone d'activité Bab Ezzouar, Alger, Algérie",
            correspondent_banks=["SOCIETE_GENERALE"],
            license_type="Filiale internationale",
        ),
        dict(
            name="BNP Paribas El Djazaïr",
            abbreviation="BNPP-DZ",
            website="https://www.bnpparibas.dz",
            address="Rue Ahmed Ouaked, Dély Ibrahim, Alger, Algérie",
            correspondent_banks=["BNP_PARIBAS"],
            license_type="Filiale internationale",
        ),
        dict(
            name="Gulf Bank Algeria",
            abbreviation="AGB",
            website="https://www.agb.dz",
            address="Rue des Frères Bouadou, Bir Mourad Raïs, Alger, Algérie",
            license_type="Banque privée",
        ),
        dict(
            name="Al Salam Bank Algeria",
            abbreviation="ASBA",
            website="https://www.alsalamalgeria.com",
            address="Lot Mackley, Ben Aknoun, Alger, Algérie",
            services=["murabaha", "bank_guarantee", "trade_finance_islamique", "forex"],
            license_type="Banque participative",
        ),
        dict(
            name="Housing Bank for Trade and Finance Algeria",
            abbreviation="HBTF-DZ",
            website="https://www.housingbank.dz",
            address="Alger, Algérie",
            license_type="Banque privée",
        ),
    ],
    "TN": [
        dict(
            name="Banque Nationale Agricole",
            abbreviation="BNA-TN",
            swift_code="BNAGTNTT",
            website="https://www.bna.tn",
            address="Rue Hédi Nouira, Tunis 1001, Tunisie",
            license_type="Banque publique",
        ),
        dict(
            name="Attijari Bank Tunisie",
            abbreviation="ATB-TN",
            swift_code="BSTUTNTT",
            website="https://www.attijaribank.com.tn",
            address="95, Avenue de la Liberté, Tunis, Tunisie",
            correspondent_banks=["ATTIJARIWAFA_BANK"],
            license_type="Banque universelle",
        ),
        dict(
            name="Amen Bank",
            abbreviation="AMEN",
            swift_code="CFCTTNTT",
            website="https://www.amenbank.com.tn",
            address="Avenue Mohamed V, Tunis, Tunisie",
            license_type="Banque universelle",
        ),
        dict(
            name="Banque de Tunisie",
            abbreviation="BT",
            swift_code="BDTNTNTT",
            website="https://www.bt.com.tn",
            address="2, Rue de Turquie, Tunis 1000, Tunisie",
            license_type="Banque universelle",
        ),
        dict(
            name="Union Internationale de Banques (Société Générale)",
            abbreviation="UIB",
            swift_code="UIBKTNTT",
            website="https://www.uib.com.tn",
            address="65, Avenue Habib Bourguiba, Tunis, Tunisie",
            correspondent_banks=["SOCIETE_GENERALE"],
            license_type="Filiale internationale",
        ),
        dict(
            name="Arab Tunisian Bank",
            abbreviation="ATB",
            swift_code="ATBKTNTT",
            website="https://www.atb.tn",
            address="9, Rue Hedi Nouira, Tunis, Tunisie",
            license_type="Banque universelle",
        ),
        dict(
            name="Banque de l'Habitat",
            abbreviation="BH",
            swift_code="BHBKTNTT",
            website="https://www.bhbank.tn",
            address="21, Avenue Kheireddine Pacha, Tunis, Tunisie",
            license_type="Banque publique",
        ),
    ],
    "EG": [
        dict(
            name="Banque Misr",
            abbreviation="BANQUE-MISR",
            swift_code="BMISEGCX",
            website="https://www.banquemisr.com",
            address="151, Mohamed Farid Street, Cairo, Egypt",
            license_type="Banque publique",
        ),
        dict(
            name="Banque du Caire",
            abbreviation="BDC-EG",
            swift_code="BCAIEGCX",
            website="https://www.banquemisr.com",
            address="6 Dr Mostafa Abou Zahra, Nasr City, Cairo, Egypt",
            license_type="Banque publique",
        ),
        dict(
            name="QNB Alahli",
            abbreviation="QNB-EG",
            swift_code="QNBAEGCX",
            website="https://www.qnbalahli.com",
            address="5 Champollion Street, Cairo, Egypt",
            license_type="Filiale internationale",
        ),
        dict(
            name="Arab African International Bank",
            abbreviation="AAIB",
            swift_code="ARAIEGCX",
            website="https://www.aaib.com",
            address="5 Midan Al Saray Al Koubra, Garden City, Cairo, Egypt",
            license_type="Banque universelle",
        ),
        dict(
            name="Bank of Alexandria (Intesa Sanpaolo)",
            abbreviation="ALEXBANK",
            swift_code="ALEXEGCX",
            website="https://www.alexbank.com",
            address="49 Kasr El Nil Street, Cairo, Egypt",
            license_type="Filiale internationale",
        ),
        dict(
            name="HSBC Egypt",
            abbreviation="HSBC-EG",
            swift_code="EBBKEGCX",
            website="https://www.hsbc.com.eg",
            address="306 Corniche El Nil, Maadi, Cairo, Egypt",
            correspondent_banks=["HSBC"],
            license_type="Filiale internationale",
        ),
    ],
    "LY": [
        dict(
            name="Jumhouria Bank",
            abbreviation="JUMHOURIA",
            swift_code="UMMABLTX",
            website="https://www.jbank.ly",
            address="Omar Al-Mukhtar Street, Tripoli, Libya",
            license_type="Banque publique",
        ),
        dict(
            name="National Commercial Bank",
            abbreviation="NCB-LY",
            website="https://www.ncb.ly",
            address="Al Bayda / Tripoli, Libya",
            license_type="Banque publique",
        ),
        dict(
            name="Bank of Commerce & Development",
            abbreviation="BCD-LY",
            swift_code="BCADLYLX",
            website="https://www.bcd.ly",
            address="Benghazi, Libya",
            license_type="Banque privée",
        ),
    ],
    "SD": [
        dict(
            name="Bank of Khartoum",
            abbreviation="BOK",
            swift_code="BKHESDKH",
            website="https://www.bankofkhartoum.com",
            address="Gamhouria Street, Khartoum, Sudan",
            services=["murabaha", "bank_guarantee", "trade_finance_islamique", "forex"],
            license_type="Banque islamique",
        ),
        dict(
            name="Faisal Islamic Bank (Sudan)",
            abbreviation="FIB-SD",
            swift_code="FIBSSDKH",
            website="https://www.fibsudan.com",
            address="Khartoum, Sudan",
            services=["murabaha", "bank_guarantee", "trade_finance_islamique"],
            license_type="Banque islamique",
        ),
    ],
    # ═══════════════════════════ WEST AFRICA ════════════════════════════════
    "NG": [
        dict(
            name="Access Bank",
            abbreviation="ACCESS",
            swift_code="ABNGNGLA",
            website="https://www.accessbankplc.com",
            address="Danmole Street, Victoria Island, Lagos, Nigeria",
            license_type="Banque universelle",
        ),
        dict(
            name="First City Monument Bank",
            abbreviation="FCMB",
            swift_code="FCMBNGLA",
            website="https://www.fcmb.com",
            address="Primrose Tower, Tinubu Square, Lagos, Nigeria",
            license_type="Banque universelle",
        ),
        dict(
            name="Fidelity Bank",
            abbreviation="FIDELITY",
            swift_code="FIDTNGLA",
            website="https://www.fidelitybank.ng",
            address="Kofo Abayomi Street, Victoria Island, Lagos, Nigeria",
            license_type="Banque universelle",
        ),
        dict(
            name="Stanbic IBTC Bank",
            abbreviation="STANBIC-NG",
            swift_code="SBICNGLX",
            website="https://www.stanbicibtcbank.com",
            address="Walter Carrington Crescent, Victoria Island, Lagos, Nigeria",
            correspondent_banks=["STANDARD_BANK"],
            license_type="Filiale internationale",
        ),
        dict(
            name="Union Bank of Nigeria",
            abbreviation="UNION-NG",
            swift_code="UBNINGLA",
            website="https://www.unionbankng.com",
            address="Stallion Plaza, Marina, Lagos, Nigeria",
            license_type="Banque universelle",
        ),
        dict(
            name="Sterling Bank",
            abbreviation="STERLING",
            swift_code="NAMENGLA",
            website="https://www.sterling.ng",
            address="Sterling Towers, Marina, Lagos, Nigeria",
            license_type="Banque universelle",
        ),
        dict(
            name="Ecobank Nigeria",
            abbreviation="ECOBANK-NG",
            swift_code="ECOCNGLA",
            website="https://ecobank.com/ng",
            address="Ahmadu Bello Way, Victoria Island, Lagos, Nigeria",
            correspondent_banks=["ECOBANK_TRANSNATIONAL"],
            license_type="Filiale panafricaine",
        ),
    ],
    "GH": [
        dict(
            name="Absa Bank Ghana",
            abbreviation="ABSA-GH",
            swift_code="BARCGHAC",
            website="https://www.absa.com.gh",
            address="Barclays House, High Street, Accra, Ghana",
            correspondent_banks=["ABSA"],
            license_type="Filiale internationale",
        ),
        dict(
            name="Standard Chartered Bank Ghana",
            abbreviation="SCB-GH",
            swift_code="SCBLGHAC",
            website="https://www.sc.com/gh",
            address="High Street, Accra, Ghana",
            correspondent_banks=["STANDARD_CHARTERED"],
            license_type="Filiale internationale",
        ),
        dict(
            name="Stanbic Bank Ghana",
            abbreviation="STANBIC-GH",
            swift_code="SBICGHAC",
            website="https://www.stanbicbank.com.gh",
            address="Stanbic Heights, Airport City, Accra, Ghana",
            correspondent_banks=["STANDARD_BANK"],
            license_type="Filiale internationale",
        ),
        dict(
            name="CalBank",
            abbreviation="CALBANK",
            swift_code="ACCCGHAC",
            website="https://www.calbank.net",
            address="23 Independence Avenue, Accra, Ghana",
            license_type="Banque universelle",
        ),
        dict(
            name="Fidelity Bank Ghana",
            abbreviation="FIDELITY-GH",
            swift_code="FBLIGHAC",
            website="https://www.fidelitybank.com.gh",
            address="Ridge Towers, Accra, Ghana",
            license_type="Banque universelle",
        ),
        dict(
            name="Zenith Bank Ghana",
            abbreviation="ZENITH-GH",
            swift_code="ZEBLGHAC",
            website="https://www.zenithbank.com.gh",
            address="Independence Avenue, Accra, Ghana",
            license_type="Filiale internationale",
        ),
    ],
    "CI": [
        dict(
            name="NSIA Banque Côte d'Ivoire",
            abbreviation="NSIA-CI",
            swift_code="BIAOCIAB",
            website="https://www.nsiabanque.ci",
            address="8-10 Avenue Joseph Anoma, Abidjan, Côte d'Ivoire",
            license_type="Banque universelle",
        ),
        dict(
            name="Banque Atlantique Côte d'Ivoire",
            abbreviation="BACI",
            swift_code="ATCICIAB",
            website="https://www.banqueatlantique.net",
            address="Rue du Commerce, Plateau, Abidjan, Côte d'Ivoire",
            license_type="Banque universelle",
        ),
        dict(
            name="Bank of Africa Côte d'Ivoire",
            abbreviation="BOA-CI",
            swift_code="AFRICIAB",
            website="https://www.boacotedivoire.com",
            address="Angle Avenue Terrasson de Fougères, Abidjan, Côte d'Ivoire",
            correspondent_banks=["BMCE_BANK_OF_AFRICA"],
            license_type="Filiale panafricaine",
        ),
        dict(
            name="Banque Internationale pour le Commerce et l'Industrie CI",
            abbreviation="BICICI",
            swift_code="BICICIAB",
            website="https://www.bicici.com",
            address="Avenue Franchet d'Esperey, Abidjan, Côte d'Ivoire",
            correspondent_banks=["BNP_PARIBAS"],
            license_type="Filiale internationale",
        ),
        dict(
            name="Standard Chartered Bank Côte d'Ivoire",
            abbreviation="SCB-CI",
            swift_code="SCBLCIAB",
            website="https://www.sc.com/ci",
            address="Boulevard de la République, Abidjan, Côte d'Ivoire",
            correspondent_banks=["STANDARD_CHARTERED"],
            license_type="Filiale internationale",
        ),
        dict(
            name="Coris Bank International CI",
            abbreviation="CORIS-CI",
            website="https://www.coris-bank.com",
            address="Plateau, Abidjan, Côte d'Ivoire",
            license_type="Banque universelle",
        ),
    ],
    "SN": [
        dict(
            name="Banque de Dakar",
            abbreviation="BDK",
            website="https://www.bdk.sn",
            address="Avenue Léopold Sédar Senghor, Dakar, Sénégal",
            license_type="Banque universelle",
        ),
        dict(
            name="Compagnie Bancaire de l'Afrique de l'Ouest",
            abbreviation="CBAO",
            swift_code="CBAOSNDA",
            website="https://www.cbao.sn",
            address="1 Place de l'Indépendance, Dakar, Sénégal",
            correspondent_banks=["ATTIJARIWAFA_BANK"],
            license_type="Banque universelle",
        ),
        dict(
            name="Banque of Africa Sénégal",
            abbreviation="BOA-SN",
            swift_code="AFRISNDA",
            website="https://www.boasenegal.com",
            address="Place de l'Indépendance, Dakar, Sénégal",
            correspondent_banks=["BMCE_BANK_OF_AFRICA"],
            license_type="Filiale panafricaine",
        ),
        dict(
            name="Banque Islamique du Sénégal",
            abbreviation="BIS-SN",
            swift_code="BISESNDA",
            website="https://www.bis-bank.com",
            address="Rue Huart, Dakar, Sénégal",
            services=["murabaha", "bank_guarantee", "trade_finance_islamique", "forex"],
            license_type="Banque islamique",
        ),
        dict(
            name="Banque Nationale pour le Développement Économique",
            abbreviation="BNDE-SN",
            website="https://www.bnde.sn",
            address="Boulevard Djily Mbaye, Dakar, Sénégal",
            license_type="Banque publique",
        ),
    ],
    "ML": [
        dict(
            name="Bank of Africa Mali",
            abbreviation="BOA-ML",
            swift_code="AFRIMLBA",
            website="https://www.boamali.com",
            address="Avenue Modibo Keïta, Bamako, Mali",
            correspondent_banks=["BMCE_BANK_OF_AFRICA"],
            license_type="Filiale panafricaine",
        ),
        dict(
            name="Banque Malienne de Solidarité",
            abbreviation="BMS-ML",
            website="https://www.bms-sa.ml",
            address="ACI 2000, Bamako, Mali",
            license_type="Banque universelle",
        ),
        dict(
            name="Banque Commerciale du Sahel",
            abbreviation="BCS-ML",
            website="https://www.bcs-sa.ml",
            address="Bamako, Mali",
            license_type="Banque universelle",
        ),
    ],
    "BF": [
        dict(
            name="Bank of Africa Burkina Faso",
            abbreviation="BOA-BF",
            swift_code="AFRIBFBF",
            website="https://www.boaburkinafaso.com",
            address="770 Avenue du Président Aboubacar Sangoulé Lamizana, Ouagadougou, Burkina Faso",
            correspondent_banks=["BMCE_BANK_OF_AFRICA"],
            license_type="Filiale panafricaine",
        ),
        dict(
            name="Banque Atlantique Burkina Faso",
            abbreviation="BABF",
            website="https://www.banqueatlantique.net",
            address="Ouagadougou, Burkina Faso",
            license_type="Banque universelle",
        ),
        dict(
            name="United Bank for Africa Burkina",
            abbreviation="UBA-BF",
            swift_code="UNAFBFBF",
            website="https://www.ubagroup.com",
            address="Ouagadougou, Burkina Faso",
            correspondent_banks=["UBA_GROUP"],
            license_type="Filiale panafricaine",
        ),
    ],
    "BJ": [
        dict(
            name="Bank of Africa Bénin",
            abbreviation="BOA-BJ",
            swift_code="AFRIBJBJ",
            website="https://www.boabenin.com",
            address="Avenue Jean-Paul II, Cotonou, Bénin",
            correspondent_banks=["BMCE_BANK_OF_AFRICA"],
            license_type="Filiale panafricaine",
        ),
        dict(
            name="Banque Atlantique Bénin",
            abbreviation="BABJ",
            website="https://www.banqueatlantique.net",
            address="Cotonou, Bénin",
            license_type="Banque universelle",
        ),
        dict(
            name="United Bank for Africa Bénin",
            abbreviation="UBA-BJ",
            swift_code="UNAFBJBJ",
            website="https://www.ubagroup.com",
            address="Cotonou, Bénin",
            correspondent_banks=["UBA_GROUP"],
            license_type="Filiale panafricaine",
        ),
    ],
    "TG": [
        dict(
            name="Orabank Togo",
            abbreviation="ORABANK-TG",
            website="https://www.orabank.net",
            address="Boulevard du 13 Janvier, Lomé, Togo",
            license_type="Banque universelle",
        ),
        dict(
            name="Banque Atlantique Togo",
            abbreviation="BATG",
            website="https://www.banqueatlantique.net",
            address="Lomé, Togo",
            license_type="Banque universelle",
        ),
        dict(
            name="Coris Bank International Togo",
            abbreviation="CORIS-TG",
            website="https://www.coris-bank.com",
            address="Lomé, Togo",
            license_type="Banque universelle",
        ),
    ],
    "NE": [
        dict(
            name="Bank of Africa Niger",
            abbreviation="BOA-NE",
            swift_code="AFRINENI",
            website="https://www.boaniger.com",
            address="Rue du Gaweye, Niamey, Niger",
            correspondent_banks=["BMCE_BANK_OF_AFRICA"],
            license_type="Filiale panafricaine",
        ),
        dict(
            name="Banque Atlantique Niger",
            abbreviation="BANE",
            website="https://www.banqueatlantique.net",
            address="Niamey, Niger",
            license_type="Banque universelle",
        ),
        dict(
            name="Banque Islamique du Niger",
            abbreviation="BIA-NE",
            website="https://www.bia-niger.com",
            address="Niamey, Niger",
            services=["murabaha", "bank_guarantee", "trade_finance_islamique"],
            license_type="Banque islamique",
        ),
    ],
    "GN": [
        dict(
            name="Banque Islamique de Guinée",
            abbreviation="BIG-GN",
            website="https://www.big-guinee.com",
            address="Conakry, Guinée",
            services=["murabaha", "bank_guarantee", "trade_finance_islamique"],
            license_type="Banque islamique",
        ),
        dict(
            name="United Bank for Africa Guinée",
            abbreviation="UBA-GN",
            swift_code="UNAFGNCO",
            website="https://www.ubagroup.com",
            address="Conakry, Guinée",
            correspondent_banks=["UBA_GROUP"],
            license_type="Filiale panafricaine",
        ),
        dict(
            name="Banque Populaire Maroco-Guinéenne",
            abbreviation="BPMG",
            website="https://www.bpmg.com.gn",
            address="Conakry, Guinée",
            license_type="Banque universelle",
        ),
    ],
    "GW": [
        dict(
            name="Banque de l'Afrique de l'Ouest (Bissau)",
            abbreviation="BAO-GW",
            website="https://www.orabank.net",
            address="Bissau, Guinée-Bissau",
            license_type="Banque universelle",
        ),
        dict(
            name="Banco da União",
            abbreviation="BDU-GW",
            address="Bissau, Guinée-Bissau",
            license_type="Banque universelle",
        ),
    ],
    "CV": [
        dict(
            name="Banco Interatlântico",
            abbreviation="BI-CV",
            swift_code="BICVCVCV",
            website="https://www.bi.cv",
            address="Avenida Cidade de Lisboa, Praia, Cabo Verde",
            correspondent_banks=["CAIXA_GERAL_DE_DEPOSITOS"],
            license_type="Banque universelle",
        ),
        dict(
            name="Banco Comercial do Atlântico",
            abbreviation="BCA-CV",
            swift_code="BCATCVCV",
            website="https://www.bca.cv",
            address="Avenida Amílcar Cabral, Praia, Cabo Verde",
            license_type="Banque universelle",
        ),
    ],
    "GM": [
        dict(
            name="Trust Bank Gambia",
            abbreviation="TBL-GM",
            swift_code="TBLGGMGM",
            website="https://www.tbl.gm",
            address="3-4 Ecowas Avenue, Banjul, The Gambia",
            license_type="Banque universelle",
        ),
        dict(
            name="Access Bank Gambia",
            abbreviation="ACCESS-GM",
            website="https://www.gambia.accessbankplc.com",
            address="47 Kairaba Avenue, Banjul, The Gambia",
            correspondent_banks=["ACCESS_BANK"],
            license_type="Filiale panafricaine",
        ),
    ],
    "SL": [
        dict(
            name="Rokel Commercial Bank",
            abbreviation="RCB-SL",
            swift_code="ROKISLFR",
            website="https://www.rokelbank.sl",
            address="25-27 Siaka Stevens Street, Freetown, Sierra Leone",
            license_type="Banque universelle",
        ),
        dict(
            name="Guaranty Trust Bank Sierra Leone",
            abbreviation="GTB-SL",
            swift_code="GTBISLFR",
            website="https://www.gtbank.sl",
            address="12 Charlotte Street, Freetown, Sierra Leone",
            correspondent_banks=["GTBANK"],
            license_type="Filiale panafricaine",
        ),
    ],
    "LR": [
        dict(
            name="International Bank Liberia",
            abbreviation="IB-LR",
            website="https://www.ibliberia.com",
            address="Broad Street, Monrovia, Liberia",
            license_type="Banque universelle",
        ),
        dict(
            name="United Bank for Africa Liberia",
            abbreviation="UBA-LR",
            swift_code="UNAFLRLM",
            website="https://www.ubagroup.com",
            address="Broad Street, Monrovia, Liberia",
            correspondent_banks=["UBA_GROUP"],
            license_type="Filiale panafricaine",
        ),
    ],
    # ═══════════════════════════ CENTRAL AFRICA ═════════════════════════════
    "CM": [
        dict(
            name="Afriland First Bank",
            abbreviation="AFRILAND",
            swift_code="CCEICMCX",
            website="https://www.afrilandfirstbank.com",
            address="Place de l'Indépendance, Yaoundé, Cameroun",
            license_type="Banque universelle",
        ),
        dict(
            name="Banque Internationale du Cameroun pour l'Épargne et le Crédit",
            abbreviation="BICEC",
            swift_code="BICECMCX",
            website="https://www.bicec.com",
            address="Avenue du Général de Gaulle, Douala, Cameroun",
            license_type="Banque universelle",
        ),
        dict(
            name="Ecobank Cameroun",
            abbreviation="ECOBANK-CM",
            swift_code="ECOCCMCX",
            website="https://ecobank.com/cm",
            address="Boulevard de la Liberté, Douala, Cameroun",
            correspondent_banks=["ECOBANK_TRANSNATIONAL"],
            license_type="Filiale panafricaine",
        ),
        dict(
            name="United Bank for Africa Cameroun",
            abbreviation="UBA-CM",
            swift_code="UNAFCMCX",
            website="https://www.ubagroup.com",
            address="Douala, Cameroun",
            correspondent_banks=["UBA_GROUP"],
            license_type="Filiale panafricaine",
        ),
        dict(
            name="Commercial Bank of Cameroon",
            abbreviation="CBC-CM",
            website="https://www.commercialbank.cm",
            address="Douala, Cameroun",
            license_type="Banque universelle",
        ),
    ],
    "GA": [
        dict(
            name="Ecobank Gabon",
            abbreviation="ECOBANK-GA",
            swift_code="ECOCGALI",
            website="https://ecobank.com/ga",
            address="Boulevard de l'Indépendance, Libreville, Gabon",
            correspondent_banks=["ECOBANK_TRANSNATIONAL"],
            license_type="Filiale panafricaine",
        ),
        dict(
            name="United Bank for Africa Gabon",
            abbreviation="UBA-GA",
            swift_code="UNAFGALI",
            website="https://www.ubagroup.com",
            address="Libreville, Gabon",
            correspondent_banks=["UBA_GROUP"],
            license_type="Filiale panafricaine",
        ),
        dict(
            name="Orabank Gabon",
            abbreviation="ORABANK-GA",
            website="https://www.orabank.net",
            address="Libreville, Gabon",
            license_type="Banque universelle",
        ),
    ],
    "CG": [
        dict(
            name="BGFIBank Congo",
            abbreviation="BGFI-CG",
            website="https://www.bgfi.com",
            address="Boulevard Denis Sassou Nguesso, Brazzaville, Congo",
            license_type="Banque universelle",
        ),
        dict(
            name="United Bank for Africa Congo",
            abbreviation="UBA-CG",
            swift_code="UNAFCGCG",
            website="https://www.ubagroup.com",
            address="Brazzaville, Congo",
            correspondent_banks=["UBA_GROUP"],
            license_type="Filiale panafricaine",
        ),
        dict(
            name="Banque Commerciale Internationale",
            abbreviation="BCI-CG",
            website="https://www.bci.cg",
            address="Pointe-Noire, Congo",
            license_type="Banque universelle",
        ),
    ],
    "TD": [
        dict(
            name="Commercial Bank Tchad",
            abbreviation="CBT",
            website="https://www.commercialbank-tchad.com",
            address="Avenue Charles de Gaulle, N'Djamena, Tchad",
            license_type="Banque universelle",
        ),
        dict(
            name="United Bank for Africa Tchad",
            abbreviation="UBA-TD",
            swift_code="UNAFTDND",
            website="https://www.ubagroup.com",
            address="N'Djamena, Tchad",
            correspondent_banks=["UBA_GROUP"],
            license_type="Filiale panafricaine",
        ),
    ],
    "CF": [
        dict(
            name="Banque Populaire Maroco-Centrafricaine",
            abbreviation="BPMC-CF",
            website="https://www.bpmc.cf",
            address="Bangui, République centrafricaine",
            license_type="Banque universelle",
        ),
        dict(
            name="Ecobank Centrafrique",
            abbreviation="ECOBANK-CF",
            swift_code="ECOCCFCF",
            website="https://ecobank.com",
            address="Bangui, République centrafricaine",
            correspondent_banks=["ECOBANK_TRANSNATIONAL"],
            license_type="Filiale panafricaine",
        ),
    ],
    "GQ": [
        dict(
            name="BGFIBank Guinée Équatoriale",
            abbreviation="BGFI-GQ",
            website="https://www.bgfi.com",
            address="Malabo, Guinée équatoriale",
            license_type="Banque universelle",
        ),
        dict(
            name="Ecobank Guinée Équatoriale",
            abbreviation="ECOBANK-GQ",
            website="https://ecobank.com",
            address="Malabo, Guinée équatoriale",
            correspondent_banks=["ECOBANK_TRANSNATIONAL"],
            license_type="Filiale panafricaine",
        ),
    ],
    "CD": [
        dict(
            name="Trust Merchant Bank",
            abbreviation="TMB-CD",
            swift_code="TRMSCDLI",
            website="https://www.tmb.cd",
            address="Boulevard du 30 Juin, Lubumbashi / Kinshasa, RD Congo",
            license_type="Banque universelle",
        ),
        dict(
            name="First Bank of Nigeria RDC",
            abbreviation="FBN-CD",
            website="https://www.firstbankcdrc.com",
            address="Kinshasa, RD Congo",
            license_type="Filiale internationale",
        ),
        dict(
            name="Standard Bank RDC",
            abbreviation="STANBIC-CD",
            swift_code="SBICCDKI",
            website="https://www.standardbank.cd",
            address="Kinshasa, RD Congo",
            correspondent_banks=["STANDARD_BANK"],
            license_type="Filiale internationale",
        ),
    ],
    "ST": [
        dict(
            name="Ecobank São Tomé",
            abbreviation="ECOBANK-ST",
            website="https://ecobank.com",
            address="São Tomé, São Tomé-et-Príncipe",
            correspondent_banks=["ECOBANK_TRANSNATIONAL"],
            license_type="Filiale panafricaine",
        ),
    ],
    # ═══════════════════════════ EAST AFRICA ════════════════════════════════
    "KE": [
        dict(
            name="Co-operative Bank of Kenya",
            abbreviation="COOP-KE",
            swift_code="KCOOKENA",
            website="https://www.co-opbank.co.ke",
            address="Co-operative House, Haile Selassie Avenue, Nairobi, Kenya",
            license_type="Banque universelle",
        ),
        dict(
            name="Absa Bank Kenya",
            abbreviation="ABSA-KE",
            swift_code="BARCKENX",
            website="https://www.absabank.co.ke",
            address="Absa Towers, Loita Street, Nairobi, Kenya",
            correspondent_banks=["ABSA"],
            license_type="Filiale internationale",
        ),
        dict(
            name="NCBA Bank Kenya",
            abbreviation="NCBA",
            swift_code="CBAFKENX",
            website="https://www.ncbagroup.com",
            address="NCBA Centre, Mara & Ragati Roads, Nairobi, Kenya",
            license_type="Banque universelle",
        ),
        dict(
            name="Diamond Trust Bank",
            abbreviation="DTB-KE",
            swift_code="DTKEKENA",
            website="https://www.dtbafrica.com",
            address="DTB Centre, Mombasa Road, Nairobi, Kenya",
            license_type="Banque universelle",
        ),
        dict(
            name="Stanbic Bank Kenya",
            abbreviation="STANBIC-KE",
            swift_code="SBICKENX",
            website="https://www.stanbicbank.co.ke",
            address="Stanbic Centre, Westlands, Nairobi, Kenya",
            correspondent_banks=["STANDARD_BANK"],
            license_type="Filiale internationale",
        ),
        dict(
            name="I&M Bank Kenya",
            abbreviation="IM-KE",
            swift_code="IMBLKENA",
            website="https://www.imbank.com",
            address="1 Park Avenue, 1st Parklands Avenue, Nairobi, Kenya",
            license_type="Banque universelle",
        ),
    ],
    "TZ": [
        dict(
            name="National Bank of Commerce",
            abbreviation="NBC-TZ",
            swift_code="NLCBTZTX",
            website="https://www.nbc.co.tz",
            address="Sokoine Drive / Azikiwe Street, Dar es Salaam, Tanzania",
            correspondent_banks=["ABSA"],
            license_type="Banque universelle",
        ),
        dict(
            name="Stanbic Bank Tanzania",
            abbreviation="STANBIC-TZ",
            swift_code="SBICTZTX",
            website="https://www.stanbicbank.co.tz",
            address="Kinondoni Road, Dar es Salaam, Tanzania",
            correspondent_banks=["STANDARD_BANK"],
            license_type="Filiale internationale",
        ),
        dict(
            name="Exim Bank Tanzania",
            abbreviation="EXIM-TZ",
            swift_code="EXTNTZTZ",
            website="https://www.eximbank.co.tz",
            address="Ghana Avenue, Dar es Salaam, Tanzania",
            license_type="Banque universelle",
        ),
        dict(
            name="Standard Chartered Bank Tanzania",
            abbreviation="SCB-TZ",
            swift_code="SCBLTZTX",
            website="https://www.sc.com/tz",
            address="International House, Garden Avenue, Dar es Salaam, Tanzania",
            correspondent_banks=["STANDARD_CHARTERED"],
            license_type="Filiale internationale",
        ),
    ],
    "UG": [
        dict(
            name="Stanbic Bank Uganda",
            abbreviation="STANBIC-UG",
            swift_code="SBICUGKX",
            website="https://www.stanbicbank.co.ug",
            address="Crested Towers, Hannington Road, Kampala, Uganda",
            correspondent_banks=["STANDARD_BANK"],
            license_type="Filiale internationale",
        ),
        dict(
            name="Standard Chartered Bank Uganda",
            abbreviation="SCB-UG",
            swift_code="SCBLUGKA",
            website="https://www.sc.com/ug",
            address="5 Speke Road, Kampala, Uganda",
            correspondent_banks=["STANDARD_CHARTERED"],
            license_type="Filiale internationale",
        ),
        dict(
            name="dfcu Bank",
            abbreviation="DFCU",
            swift_code="DFCUUGKA",
            website="https://www.dfcugroup.com",
            address="26 Kyadondo Road, Nakasero, Kampala, Uganda",
            license_type="Banque universelle",
        ),
        dict(
            name="Diamond Trust Bank Uganda",
            abbreviation="DTB-UG",
            swift_code="DTKEUGKA",
            website="https://www.dtbafrica.com",
            address="17-19 Kampala Road, Kampala, Uganda",
            license_type="Banque universelle",
        ),
    ],
    "RW": [
        dict(
            name="I&M Bank Rwanda",
            abbreviation="IM-RW",
            swift_code="BKORRWRW",
            website="https://www.imbank.com/rwanda",
            address="KN 3 Avenue, Kigali, Rwanda",
            license_type="Banque universelle",
        ),
        dict(
            name="Banque Populaire du Rwanda (Atlas Mara)",
            abbreviation="BPR-RW",
            swift_code="BPRWRWRW",
            website="https://www.bpr.rw",
            address="KN 67 Street, Kigali, Rwanda",
            license_type="Banque universelle",
        ),
        dict(
            name="Cogebanque",
            abbreviation="COGEBANK",
            swift_code="CGBKRWRW",
            website="https://www.cogebanque.co.rw",
            address="Centenary House, Kigali, Rwanda",
            license_type="Banque universelle",
        ),
    ],
    "ET": [
        dict(
            name="Awash Bank",
            abbreviation="AWASH",
            swift_code="AWINETAA",
            website="https://www.awashbank.com",
            address="Ras Abebe Aregay Street, Addis Ababa, Ethiopia",
            license_type="Banque privée",
        ),
        dict(
            name="Bank of Abyssinia",
            abbreviation="ABYSSINIA",
            swift_code="ABYSETAA",
            website="https://www.bankofabyssinia.com",
            address="Beklo Bet, Addis Ababa, Ethiopia",
            license_type="Banque privée",
        ),
        dict(
            name="Cooperative Bank of Oromia",
            abbreviation="COOP-ET",
            swift_code="CBORETAA",
            website="https://www.coopbankoromia.com.et",
            address="Bole Road, Addis Ababa, Ethiopia",
            license_type="Banque privée",
        ),
        dict(
            name="Wegagen Bank",
            abbreviation="WEGAGEN",
            swift_code="WEGAETAA",
            website="https://www.wegagenbanksc.com",
            address="Wegagen Building, Addis Ababa, Ethiopia",
            license_type="Banque privée",
        ),
    ],
    "SS": [
        dict(
            name="Ivory Bank",
            abbreviation="IVORY-SS",
            address="Juba, South Sudan",
            license_type="Banque universelle",
        ),
        dict(
            name="Cooperative Bank of South Sudan",
            abbreviation="COOP-SS",
            website="https://www.co-opbank.co.ke",
            address="Juba, South Sudan",
            license_type="Banque universelle",
        ),
    ],
    "ER": [
        dict(
            name="Commercial Bank of Eritrea",
            abbreviation="CBER",
            swift_code="CBERERAA",
            address="Asmara, Eritrea",
            license_type="Banque publique",
        ),
    ],
    "DJ": [
        dict(
            name="Bank of Africa Mer Rouge",
            abbreviation="BOA-DJ",
            swift_code="BAMRDJJD",
            website="https://www.boadjibouti.com",
            address="Place Lagarde, Djibouti",
            license_type="Banque universelle",
        ),
        dict(
            name="CAC International Bank",
            abbreviation="CAC-DJ",
            website="https://www.cacbank.dj",
            address="Djibouti",
            license_type="Banque universelle",
        ),
    ],
    "SO": [
        dict(
            name="Dahabshiil Bank International",
            abbreviation="DAHABSHIIL",
            website="https://www.dahabshiilbank.com",
            address="Maka Al Mukarama Road, Mogadishu, Somalia",
            services=["murabaha", "bank_guarantee", "trade_finance_islamique", "forex"],
            license_type="Banque islamique",
        ),
        dict(
            name="Salaam Somali Bank",
            abbreviation="SALAAM-SO",
            website="https://www.salaambank.so",
            address="Mogadishu, Somalia",
            services=["murabaha", "bank_guarantee", "trade_finance_islamique"],
            license_type="Banque islamique",
        ),
    ],
    # ═══════════════════════════ SOUTHERN AFRICA ════════════════════════════
    "ZA": [
        dict(
            name="Investec Bank",
            abbreviation="INVESTEC",
            swift_code="IVESZAJJ",
            website="https://www.investec.com",
            address="100 Grayston Drive, Sandton, Johannesburg, South Africa",
            license_type="Banque d'investissement",
        ),
        dict(
            name="Capitec Bank",
            abbreviation="CAPITEC",
            swift_code="CABLZAJJ",
            website="https://www.capitecbank.co.za",
            address="1 Quantum Street, Techno Park, Stellenbosch, South Africa",
            license_type="Banque de détail",
        ),
        dict(
            name="African Bank",
            abbreviation="AFRICAN-BANK",
            swift_code="AFRCZAJJ",
            website="https://www.africanbank.co.za",
            address="59 16th Road, Midrand, South Africa",
            license_type="Banque de détail",
        ),
        dict(
            name="Bidvest Bank",
            abbreviation="BIDVEST",
            swift_code="BIDBZAJJ",
            website="https://www.bidvestbank.co.za",
            address="Bidvest Bank House, Sandton, Johannesburg, South Africa",
            license_type="Banque de niche (forex/trade)",
        ),
    ],
    "AO": [
        dict(
            name="Banco de Fomento Angola",
            abbreviation="BFA",
            swift_code="BFMXAOLU",
            website="https://www.bfa.ao",
            address="Rua Amílcar Cabral, Luanda, Angola",
            license_type="Banque universelle",
        ),
        dict(
            name="Banco Angolano de Investimentos",
            abbreviation="BAI-AO",
            swift_code="BAIPAOLU",
            website="https://www.bancobai.ao",
            address="Rua Major Kanhangulo, Luanda, Angola",
            license_type="Banque universelle",
        ),
        dict(
            name="Banco BIC Angola",
            abbreviation="BIC-AO",
            swift_code="BAECAOLU",
            website="https://www.bancobic.ao",
            address="Talatona, Luanda, Angola",
            license_type="Banque universelle",
        ),
        dict(
            name="Standard Bank Angola",
            abbreviation="STANBIC-AO",
            swift_code="SBICAOLU",
            website="https://www.standardbank.co.ao",
            address="Rua da Missão, Luanda, Angola",
            correspondent_banks=["STANDARD_BANK"],
            license_type="Filiale internationale",
        ),
    ],
    "MZ": [
        dict(
            name="Millennium bim",
            abbreviation="BIM-MZ",
            swift_code="BIMOMZMX",
            website="https://www.millenniumbim.co.mz",
            address="Avenida 25 de Setembro, Maputo, Mozambique",
            correspondent_banks=["MILLENNIUM_BCP"],
            license_type="Banque universelle",
        ),
        dict(
            name="Banco Comercial e de Investimentos",
            abbreviation="BCI-MZ",
            swift_code="CGDIMZMA",
            website="https://www.bci.co.mz",
            address="Avenida 25 de Setembro, Maputo, Mozambique",
            license_type="Banque universelle",
        ),
        dict(
            name="Standard Bank Moçambique",
            abbreviation="STANBIC-MZ",
            swift_code="SBICMZMX",
            website="https://www.standardbank.co.mz",
            address="Praça 25 de Junho, Maputo, Mozambique",
            correspondent_banks=["STANDARD_BANK"],
            license_type="Filiale internationale",
        ),
    ],
    "ZM": [
        dict(
            name="First National Bank Zambia",
            abbreviation="FNB-ZM",
            swift_code="FIRNZMLX",
            website="https://www.fnbzambia.co.zm",
            address="Acacia Park, Great East Road, Lusaka, Zambia",
            correspondent_banks=["FIRSTRAND"],
            license_type="Filiale internationale",
        ),
        dict(
            name="Absa Bank Zambia",
            abbreviation="ABSA-ZM",
            swift_code="BARCZMLX",
            website="https://www.absa.co.zm",
            address="Elunda Park, Addis Ababa Drive, Lusaka, Zambia",
            correspondent_banks=["ABSA"],
            license_type="Filiale internationale",
        ),
        dict(
            name="Stanbic Bank Zambia",
            abbreviation="STANBIC-ZM",
            swift_code="SBICZMLX",
            website="https://www.stanbicbank.co.zm",
            address="Addis Ababa Drive, Lusaka, Zambia",
            correspondent_banks=["STANDARD_BANK"],
            license_type="Filiale internationale",
        ),
    ],
    "ZW": [
        dict(
            name="CBZ Bank",
            abbreviation="CBZ",
            swift_code="COBZZWHA",
            website="https://www.cbz.co.zw",
            address="Union House, First Street, Harare, Zimbabwe",
            license_type="Banque universelle",
        ),
        dict(
            name="Standard Chartered Bank Zimbabwe",
            abbreviation="SCB-ZW",
            swift_code="SCBLZWHX",
            website="https://www.sc.com/zw",
            address="Africa Unity Square, Harare, Zimbabwe",
            correspondent_banks=["STANDARD_CHARTERED"],
            license_type="Filiale internationale",
        ),
        dict(
            name="First Capital Bank Zimbabwe",
            abbreviation="FCB-ZW",
            swift_code="BARCZWHX",
            website="https://www.firstcapitalbank.co.zw",
            address="Josiah Chinamano Avenue, Harare, Zimbabwe",
            license_type="Banque universelle",
        ),
    ],
    "BW": [
        dict(
            name="First National Bank Botswana",
            abbreviation="FNBB",
            swift_code="FIRNBWGX",
            website="https://www.fnbbotswana.co.bw",
            address="Plot 54362, First Place, CBD, Gaborone, Botswana",
            correspondent_banks=["FIRSTRAND"],
            license_type="Filiale internationale",
        ),
        dict(
            name="Standard Chartered Bank Botswana",
            abbreviation="SCB-BW",
            swift_code="SCHBBWGX",
            website="https://www.sc.com/bw",
            address="5th Floor, Standard Chartered House, Gaborone, Botswana",
            correspondent_banks=["STANDARD_CHARTERED"],
            license_type="Filiale internationale",
        ),
        dict(
            name="Bank Gaborone",
            abbreviation="BANK-GABORONE",
            website="https://www.bankgaborone.co.bw",
            address="Plot 54368, CBD, Gaborone, Botswana",
            license_type="Banque universelle",
        ),
    ],
    "NA": [
        dict(
            name="Bank Windhoek",
            abbreviation="BANK-WINDHOEK",
            swift_code="BWLINANX",
            website="https://www.bankwindhoek.com.na",
            address="262 Independence Avenue, Windhoek, Namibia",
            license_type="Banque universelle",
        ),
        dict(
            name="Nedbank Namibia",
            abbreviation="NEDBANK-NA",
            swift_code="NEDSNANX",
            website="https://www.nedbank.com.na",
            address="12-20 Dr Frans Indongo Street, Windhoek, Namibia",
            correspondent_banks=["NEDBANK"],
            license_type="Filiale internationale",
        ),
    ],
    "MW": [
        dict(
            name="Standard Bank Malawi",
            abbreviation="STANBIC-MW",
            swift_code="SBICMWMX",
            website="https://www.standardbank.co.mw",
            address="Kaomba Centre, Blantyre, Malawi",
            correspondent_banks=["STANDARD_BANK"],
            license_type="Filiale internationale",
        ),
        dict(
            name="First Capital Bank Malawi",
            abbreviation="FCB-MW",
            swift_code="FMBLMWMW",
            website="https://www.firstcapitalbank.co.mw",
            address="Livingstone Towers, Blantyre, Malawi",
            license_type="Banque universelle",
        ),
    ],
    "LS": [
        dict(
            name="First National Bank Lesotho",
            abbreviation="FNB-LS",
            swift_code="FIRNLSMX",
            website="https://www.fnb.co.ls",
            address="Kingsway Road, Maseru, Lesotho",
            correspondent_banks=["FIRSTRAND"],
            license_type="Filiale internationale",
        ),
    ],
    "SZ": [
        dict(
            name="Nedbank Eswatini",
            abbreviation="NEDBANK-SZ",
            swift_code="NEDSSZMX",
            website="https://www.nedbank.co.sz",
            address="Corner Dr Sishayi & Sozisa Roads, Mbabane, Eswatini",
            correspondent_banks=["NEDBANK"],
            license_type="Filiale internationale",
        ),
        dict(
            name="Standard Bank Eswatini",
            abbreviation="STANBIC-SZ2",
            swift_code="SBICSZMX",
            website="https://www.standardbank.co.sz",
            address="Mbabane, Eswatini",
            correspondent_banks=["STANDARD_BANK"],
            license_type="Filiale internationale",
        ),
    ],
    # ═══════════════════════════ ISLAND STATES ══════════════════════════════
    "MU": [
        dict(
            name="Absa Bank Mauritius",
            abbreviation="ABSA-MU",
            swift_code="BARCMUMU",
            website="https://www.absamauritius.com",
            address="Absa House, 68 Wall Street, Ebène, Mauritius",
            correspondent_banks=["ABSA"],
            license_type="Filiale internationale",
        ),
        dict(
            name="AfrAsia Bank",
            abbreviation="AFRASIA",
            swift_code="AFBLMUMU",
            website="https://www.afrasiabank.com",
            address="Bowen Square, Ebène, Mauritius",
            license_type="Banque universelle",
        ),
        dict(
            name="Standard Bank Mauritius",
            abbreviation="STANBIC-MU",
            swift_code="SBICMUMU",
            website="https://www.standardbank.mu",
            address="Ebène, Mauritius",
            correspondent_banks=["STANDARD_BANK"],
            license_type="Filiale internationale",
        ),
    ],
    "SC": [
        dict(
            name="Nouvobanq",
            abbreviation="NOUVOBANQ",
            swift_code="SIMBSCSC",
            website="https://www.nouvobanq.sc",
            address="Victoria House, Victoria, Mahé, Seychelles",
            license_type="Banque universelle",
        ),
        dict(
            name="Seychelles Commercial Bank",
            abbreviation="SCB-SC",
            website="https://www.scb.sc",
            address="Kingsgate House, Victoria, Mahé, Seychelles",
            license_type="Banque universelle",
        ),
    ],
    "MG": [
        dict(
            name="Bank of Africa Madagascar",
            abbreviation="BOA-MG2",
            swift_code="AFRIMGMG",
            website="https://www.boa.mg",
            address="2 Place de l'Indépendance, Antananarivo, Madagascar",
            correspondent_banks=["BMCE_BANK_OF_AFRICA"],
            license_type="Filiale panafricaine",
        ),
        dict(
            name="BFV-Société Générale",
            abbreviation="BFV-SG",
            swift_code="BFAVMGMG",
            website="https://www.bfv.mg",
            address="14 Lalana Jeneraly Rabehevitra, Antananarivo, Madagascar",
            correspondent_banks=["SOCIETE_GENERALE"],
            license_type="Filiale internationale",
        ),
    ],
    "KM": [
        dict(
            name="Banque pour l'Industrie et le Commerce - Comores",
            abbreviation="BIC-KM",
            website="https://www.bic-comores.com",
            address="Moroni, Comores",
            license_type="Banque universelle",
        ),
    ],
    "CV2": [],  # placeholder guard (unused)
    # ═══════════════════════════ OTHER ══════════════════════════════════════
    "MR": [
        dict(
            name="Banque Mauritanienne pour le Commerce International",
            abbreviation="BMCI-MR",
            website="https://www.bmci.mr",
            address="Avenue Gamal Abdel Nasser, Nouakchott, Mauritanie",
            license_type="Banque universelle",
        ),
        dict(
            name="Générale de Banque de Mauritanie",
            abbreviation="GBM-MR",
            website="https://www.gbm.mr",
            address="Nouakchott, Mauritanie",
            license_type="Banque universelle",
        ),
        dict(
            name="Banque Al Wava Mauritanienne Islamique",
            abbreviation="BAMIS",
            website="https://www.bamis.mr",
            address="Nouakchott, Mauritanie",
            services=["murabaha", "bank_guarantee", "trade_finance_islamique"],
            license_type="Banque islamique",
        ),
    ],
    "BI": [
        dict(
            name="Interbank Burundi",
            abbreviation="IBB",
            swift_code="IBBUBIBI",
            website="https://www.ibb.bi",
            address="Boulevard de la Liberté, Bujumbura, Burundi",
            license_type="Banque universelle",
        ),
        dict(
            name="Banque de Crédit de Bujumbura",
            abbreviation="BCB-BI",
            swift_code="BCRBBIBI",
            website="https://www.bcb.bi",
            address="Chaussée Prince Louis Rwagasore, Bujumbura, Burundi",
            license_type="Banque universelle",
        ),
    ],
}


# ---------------------------------------------------------------------------
# Build CommercialBank objects
# ---------------------------------------------------------------------------


def _build() -> Dict[str, List[CommercialBank]]:
    out: Dict[str, List[CommercialBank]] = {}
    for code, rows in _EXTRA.items():
        if not rows or code == "CV2":
            continue
        banks: List[CommercialBank] = []
        for raw in rows:
            data = dict(raw)
            data["country_code"] = code
            data.setdefault("trade_finance", True)
            data.setdefault("services", list(_DEFAULT_SERVICES))
            data.setdefault("correspondent_banks", [])
            if "contact" not in data:
                data["contact"] = BankContact(
                    address=data.get("address"),
                    website=data.get("website"),
                    department="Trade Finance & Entreprises",
                )
            banks.append(CommercialBank(**data))
        out[code] = banks
    return out


#: ISO2 → list of additional commercial banks (merged into COMMERCIAL_BANKS).
COMMERCIAL_BANKS_EXTENDED: Dict[str, List[CommercialBank]] = _build()


def merge_into(registry: Dict[str, List[CommercialBank]]) -> Dict[str, List[CommercialBank]]:
    """Merge the extended banks into ``registry`` in place.

    De-duplicates on abbreviation (case-insensitive), falling back to the
    lower-cased bank name, so curated entries already present in ``registry``
    are never overwritten or duplicated.
    """
    for code, extra_banks in COMMERCIAL_BANKS_EXTENDED.items():
        current = registry.setdefault(code, [])
        seen = {(b.abbreviation or b.name or "").strip().lower() for b in current}
        for bank in extra_banks:
            key = (bank.abbreviation or bank.name or "").strip().lower()
            if key and key in seen:
                continue
            current.append(bank)
            seen.add(key)
    return registry
