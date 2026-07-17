"""
Real Trade Data Service
Integrates multiple free data sources:
- OEC (Observatory of Economic Complexity) - Already integrated
- WITS (World Bank) - Free, no registration
- UN Comtrade Preview API - Limited free access

Provides real trade data for African countries
"""

import asyncio
import logging
import os
from collections import defaultdict
from datetime import datetime
from typing import Dict, List

import httpx

logger = logging.getLogger(__name__)

# WITS API Configuration (World Bank - FREE)
WITS_BASE_URL = "https://wits.worldbank.org/API/V1/SDMX/V21/rest"
WITS_DATA_URL = "https://wits.worldbank.org/API/V1"

# OEC API (Already integrated in oec_trade_service.py)
# Base URL is overridable via env in case a paid plan uses a distinct host.
OEC_BASE_URL = os.getenv("OEC_BASE_URL", "https://api-v2.oec.world/tesseract/data.jsonrecords")

# Paid-plan API token. Read from the environment / secret store ONLY — never
# hardcode a token here or commit one. Accepts either OEC_API_TOKEN or the
# OEC_API_KEY name already reserved in .env.example. When absent, requests go
# out unauthenticated (public tier, subject to rate limits and blocking).
OEC_API_TOKEN = os.getenv("OEC_API_TOKEN") or os.getenv("OEC_API_KEY")


def _oec_params(params: Dict) -> Dict:
    """Inject the OEC token into request params when configured."""
    if OEC_API_TOKEN:
        enriched = dict(params)
        enriched["token"] = OEC_API_TOKEN
        return enriched
    return params


# African Countries (55 pays incluant la RASD - Membre UA depuis 1984)
# Note: La RASD n'a pas de statistiques commerciales (territoire occupé)
AFRICAN_COUNTRIES = {
    "DZA": {
        "name_fr": "Algérie",
        "name_en": "Algeria",
        "wits": "DZA",
        "oec": "afdza",
        "has_trade_data": True,
    },
    "AGO": {
        "name_fr": "Angola",
        "name_en": "Angola",
        "wits": "AGO",
        "oec": "afago",
        "has_trade_data": True,
    },
    "BEN": {
        "name_fr": "Bénin",
        "name_en": "Benin",
        "wits": "BEN",
        "oec": "afben",
        "has_trade_data": True,
    },
    "BWA": {
        "name_fr": "Botswana",
        "name_en": "Botswana",
        "wits": "BWA",
        "oec": "afbwa",
        "has_trade_data": True,
    },
    "BFA": {
        "name_fr": "Burkina Faso",
        "name_en": "Burkina Faso",
        "wits": "BFA",
        "oec": "afbfa",
        "has_trade_data": True,
    },
    "BDI": {
        "name_fr": "Burundi",
        "name_en": "Burundi",
        "wits": "BDI",
        "oec": "afbdi",
        "has_trade_data": True,
    },
    "CMR": {
        "name_fr": "Cameroun",
        "name_en": "Cameroon",
        "wits": "CMR",
        "oec": "afcmr",
        "has_trade_data": True,
    },
    "CPV": {
        "name_fr": "Cap-Vert",
        "name_en": "Cape Verde",
        "wits": "CPV",
        "oec": "afcpv",
        "has_trade_data": True,
    },
    "CAF": {
        "name_fr": "Centrafrique",
        "name_en": "Central African Republic",
        "wits": "CAF",
        "oec": "afcaf",
        "has_trade_data": True,
    },
    "TCD": {
        "name_fr": "Tchad",
        "name_en": "Chad",
        "wits": "TCD",
        "oec": "aftcd",
        "has_trade_data": True,
    },
    "COM": {
        "name_fr": "Comores",
        "name_en": "Comoros",
        "wits": "COM",
        "oec": "afcom",
        "has_trade_data": True,
    },
    "COG": {
        "name_fr": "Congo",
        "name_en": "Republic of the Congo",
        "wits": "COG",
        "oec": "afcog",
        "has_trade_data": True,
    },
    "COD": {
        "name_fr": "RD Congo",
        "name_en": "DR Congo",
        "wits": "COD",
        "oec": "afcod",
        "has_trade_data": True,
    },
    "CIV": {
        "name_fr": "Côte d'Ivoire",
        "name_en": "Ivory Coast",
        "wits": "CIV",
        "oec": "afciv",
        "has_trade_data": True,
    },
    "DJI": {
        "name_fr": "Djibouti",
        "name_en": "Djibouti",
        "wits": "DJI",
        "oec": "afdji",
        "has_trade_data": True,
    },
    "EGY": {
        "name_fr": "Égypte",
        "name_en": "Egypt",
        "wits": "EGY",
        "oec": "afegy",
        "has_trade_data": True,
    },
    "GNQ": {
        "name_fr": "Guinée Équatoriale",
        "name_en": "Equatorial Guinea",
        "wits": "GNQ",
        "oec": "afgnq",
        "has_trade_data": True,
    },
    "ERI": {
        "name_fr": "Érythrée",
        "name_en": "Eritrea",
        "wits": "ERI",
        "oec": "aferi",
        "has_trade_data": True,
    },
    # RASD - République Arabe Sahraouie Démocratique (Sahara Occidental)
    # Membre fondateur de l'Union Africaine (UA) depuis 1984
    # ATTENTION: Territoire occupé - PAS DE STATISTIQUES COMMERCIALES DISPONIBLES
    "ESH": {
        "name_fr": "RASD (Sahara Occidental)",
        "name_en": "Sahrawi Arab Democratic Republic",
        "wits": None,
        "oec": None,
        "has_trade_data": False,
        "note": "Territoire occupé - pas de données commerciales",
    },
    "SWZ": {
        "name_fr": "Eswatini",
        "name_en": "Eswatini",
        "wits": "SWZ",
        "oec": "afswz",
        "has_trade_data": True,
    },
    "ETH": {
        "name_fr": "Éthiopie",
        "name_en": "Ethiopia",
        "wits": "ETH",
        "oec": "afeth",
        "has_trade_data": True,
    },
    "GAB": {
        "name_fr": "Gabon",
        "name_en": "Gabon",
        "wits": "GAB",
        "oec": "afgab",
        "has_trade_data": True,
    },
    "GMB": {
        "name_fr": "Gambie",
        "name_en": "Gambia",
        "wits": "GMB",
        "oec": "afgmb",
        "has_trade_data": True,
    },
    "GHA": {
        "name_fr": "Ghana",
        "name_en": "Ghana",
        "wits": "GHA",
        "oec": "afgha",
        "has_trade_data": True,
    },
    "GIN": {
        "name_fr": "Guinée",
        "name_en": "Guinea",
        "wits": "GIN",
        "oec": "afgin",
        "has_trade_data": True,
    },
    "GNB": {
        "name_fr": "Guinée-Bissau",
        "name_en": "Guinea-Bissau",
        "wits": "GNB",
        "oec": "afgnb",
        "has_trade_data": True,
    },
    "KEN": {
        "name_fr": "Kenya",
        "name_en": "Kenya",
        "wits": "KEN",
        "oec": "afken",
        "has_trade_data": True,
    },
    "LSO": {
        "name_fr": "Lesotho",
        "name_en": "Lesotho",
        "wits": "LSO",
        "oec": "aflso",
        "has_trade_data": True,
    },
    "LBR": {
        "name_fr": "Libéria",
        "name_en": "Liberia",
        "wits": "LBR",
        "oec": "aflbr",
        "has_trade_data": True,
    },
    "LBY": {
        "name_fr": "Libye",
        "name_en": "Libya",
        "wits": "LBY",
        "oec": "aflby",
        "has_trade_data": True,
    },
    "MDG": {
        "name_fr": "Madagascar",
        "name_en": "Madagascar",
        "wits": "MDG",
        "oec": "afmdg",
        "has_trade_data": True,
    },
    "MWI": {
        "name_fr": "Malawi",
        "name_en": "Malawi",
        "wits": "MWI",
        "oec": "afmwi",
        "has_trade_data": True,
    },
    "MLI": {
        "name_fr": "Mali",
        "name_en": "Mali",
        "wits": "MLI",
        "oec": "afmli",
        "has_trade_data": True,
    },
    "MRT": {
        "name_fr": "Mauritanie",
        "name_en": "Mauritania",
        "wits": "MRT",
        "oec": "afmrt",
        "has_trade_data": True,
    },
    "MUS": {
        "name_fr": "Maurice",
        "name_en": "Mauritius",
        "wits": "MUS",
        "oec": "afmus",
        "has_trade_data": True,
    },
    "MAR": {
        "name_fr": "Maroc",
        "name_en": "Morocco",
        "wits": "MAR",
        "oec": "afmar",
        "has_trade_data": True,
    },
    "MOZ": {
        "name_fr": "Mozambique",
        "name_en": "Mozambique",
        "wits": "MOZ",
        "oec": "afmoz",
        "has_trade_data": True,
    },
    "NAM": {
        "name_fr": "Namibie",
        "name_en": "Namibia",
        "wits": "NAM",
        "oec": "afnam",
        "has_trade_data": True,
    },
    "NER": {
        "name_fr": "Niger",
        "name_en": "Niger",
        "wits": "NER",
        "oec": "afner",
        "has_trade_data": True,
    },
    "NGA": {
        "name_fr": "Nigeria",
        "name_en": "Nigeria",
        "wits": "NGA",
        "oec": "afnga",
        "has_trade_data": True,
    },
    "RWA": {
        "name_fr": "Rwanda",
        "name_en": "Rwanda",
        "wits": "RWA",
        "oec": "afrwa",
        "has_trade_data": True,
    },
    "STP": {
        "name_fr": "São Tomé-et-Príncipe",
        "name_en": "São Tomé and Príncipe",
        "wits": "STP",
        "oec": "afstp",
        "has_trade_data": True,
    },
    "SEN": {
        "name_fr": "Sénégal",
        "name_en": "Senegal",
        "wits": "SEN",
        "oec": "afsen",
        "has_trade_data": True,
    },
    "SYC": {
        "name_fr": "Seychelles",
        "name_en": "Seychelles",
        "wits": "SYC",
        "oec": "afsyc",
        "has_trade_data": True,
    },
    "SLE": {
        "name_fr": "Sierra Leone",
        "name_en": "Sierra Leone",
        "wits": "SLE",
        "oec": "afsle",
        "has_trade_data": True,
    },
    "SOM": {
        "name_fr": "Somalie",
        "name_en": "Somalia",
        "wits": "SOM",
        "oec": "afsom",
        "has_trade_data": True,
    },
    "ZAF": {
        "name_fr": "Afrique du Sud",
        "name_en": "South Africa",
        "wits": "ZAF",
        "oec": "afzaf",
        "has_trade_data": True,
    },
    "SSD": {
        "name_fr": "Soudan du Sud",
        "name_en": "South Sudan",
        "wits": "SSD",
        "oec": "afssd",
        "has_trade_data": True,
    },
    "SDN": {
        "name_fr": "Soudan",
        "name_en": "Sudan",
        "wits": "SDN",
        "oec": "afsdn",
        "has_trade_data": True,
    },
    "TZA": {
        "name_fr": "Tanzanie",
        "name_en": "Tanzania",
        "wits": "TZA",
        "oec": "aftza",
        "has_trade_data": True,
    },
    "TGO": {
        "name_fr": "Togo",
        "name_en": "Togo",
        "wits": "TGO",
        "oec": "aftgo",
        "has_trade_data": True,
    },
    "TUN": {
        "name_fr": "Tunisie",
        "name_en": "Tunisia",
        "wits": "TUN",
        "oec": "aftun",
        "has_trade_data": True,
    },
    "UGA": {
        "name_fr": "Ouganda",
        "name_en": "Uganda",
        "wits": "UGA",
        "oec": "afuga",
        "has_trade_data": True,
    },
    "ZMB": {
        "name_fr": "Zambie",
        "name_en": "Zambia",
        "wits": "ZMB",
        "oec": "afzmb",
        "has_trade_data": True,
    },
    "ZWE": {
        "name_fr": "Zimbabwe",
        "name_en": "Zimbabwe",
        "wits": "ZWE",
        "oec": "afzwe",
        "has_trade_data": True,
    },
}


def has_trade_data(iso3: str) -> bool:
    """Check if a country has trade data available"""
    country = AFRICAN_COUNTRIES.get(iso3.upper())
    if not country:
        return False
    return country.get("has_trade_data", True)


# HS Product Names (French/English) - EXPANDED
HS_PRODUCT_NAMES = {
    # Chapters
    "01": {"fr": "Animaux vivants", "en": "Live animals"},
    "02": {"fr": "Viandes", "en": "Meat"},
    "03": {"fr": "Poissons, crustacés", "en": "Fish, crustaceans"},
    "04": {"fr": "Produits laitiers, œufs", "en": "Dairy, eggs"},
    "05": {"fr": "Produits d'origine animale", "en": "Animal products"},
    "06": {"fr": "Plantes vivantes, fleurs", "en": "Live plants, flowers"},
    "07": {"fr": "Légumes", "en": "Vegetables"},
    "08": {"fr": "Fruits comestibles", "en": "Edible fruits"},
    "09": {"fr": "Café, thé, épices", "en": "Coffee, tea, spices"},
    "10": {"fr": "Céréales", "en": "Cereals"},
    "11": {"fr": "Produits de la minoterie", "en": "Milling products"},
    "12": {"fr": "Graines, fruits oléagineux", "en": "Oil seeds"},
    "13": {"fr": "Gommes, résines", "en": "Gums, resins"},
    "14": {"fr": "Matières à tresser", "en": "Vegetable plaiting materials"},
    "15": {"fr": "Graisses et huiles", "en": "Fats and oils"},
    "16": {"fr": "Préparations de viandes", "en": "Meat preparations"},
    "17": {"fr": "Sucres et sucreries", "en": "Sugars and confectionery"},
    "18": {"fr": "Cacao et préparations", "en": "Cocoa and preparations"},
    "19": {"fr": "Préparations de céréales", "en": "Cereal preparations"},
    "20": {"fr": "Préparations de légumes/fruits", "en": "Vegetable/fruit preparations"},
    "21": {"fr": "Préparations alimentaires", "en": "Food preparations"},
    "22": {"fr": "Boissons, vinaigres", "en": "Beverages, vinegar"},
    "23": {"fr": "Résidus industries alimentaires", "en": "Food industry residues"},
    "24": {"fr": "Tabacs", "en": "Tobacco"},
    "25": {"fr": "Sel, soufre, pierres", "en": "Salt, sulfur, stones"},
    "26": {"fr": "Minerais, scories", "en": "Ores, slag"},
    "27": {"fr": "Combustibles minéraux, huiles", "en": "Mineral fuels, oils"},
    "28": {"fr": "Produits chimiques inorganiques", "en": "Inorganic chemicals"},
    "29": {"fr": "Produits chimiques organiques", "en": "Organic chemicals"},
    "30": {"fr": "Produits pharmaceutiques", "en": "Pharmaceutical products"},
    "31": {"fr": "Engrais", "en": "Fertilizers"},
    "32": {"fr": "Extraits tannants, colorants", "en": "Tanning, dyeing extracts"},
    "33": {"fr": "Huiles essentielles, parfums", "en": "Essential oils, perfumes"},
    "34": {"fr": "Savons, préparations", "en": "Soaps, preparations"},
    "35": {"fr": "Matières albuminoïdes", "en": "Albuminoidal substances"},
    "36": {"fr": "Explosifs", "en": "Explosives"},
    "37": {"fr": "Produits photographiques", "en": "Photographic goods"},
    "38": {"fr": "Produits chimiques divers", "en": "Miscellaneous chemicals"},
    "39": {"fr": "Matières plastiques", "en": "Plastics"},
    "40": {"fr": "Caoutchouc", "en": "Rubber"},
    "41": {"fr": "Peaux et cuirs", "en": "Raw hides and skins"},
    "42": {"fr": "Ouvrages en cuir", "en": "Leather articles"},
    "43": {"fr": "Pelleteries", "en": "Furskins"},
    "44": {"fr": "Bois et ouvrages", "en": "Wood and articles"},
    "45": {"fr": "Liège", "en": "Cork"},
    "46": {"fr": "Ouvrages de sparterie", "en": "Straw articles"},
    "47": {"fr": "Pâtes de bois", "en": "Wood pulp"},
    "48": {"fr": "Papiers et cartons", "en": "Paper and paperboard"},
    "49": {"fr": "Livres, journaux", "en": "Books, newspapers"},
    "50": {"fr": "Soie", "en": "Silk"},
    "51": {"fr": "Laine", "en": "Wool"},
    "52": {"fr": "Coton", "en": "Cotton"},
    "53": {"fr": "Autres fibres textiles", "en": "Other vegetable textile fibers"},
    "54": {"fr": "Filaments synthétiques", "en": "Man-made filaments"},
    "55": {"fr": "Fibres synthétiques discontinues", "en": "Man-made staple fibers"},
    "56": {"fr": "Ouates, feutres", "en": "Wadding, felt"},
    "57": {"fr": "Tapis", "en": "Carpets"},
    "58": {"fr": "Tissus spéciaux", "en": "Special woven fabrics"},
    "59": {"fr": "Tissus imprégnés", "en": "Impregnated textiles"},
    "60": {"fr": "Étoffes de bonneterie", "en": "Knitted fabrics"},
    "61": {"fr": "Vêtements en bonneterie", "en": "Knitted apparel"},
    "62": {"fr": "Vêtements non en bonneterie", "en": "Woven apparel"},
    "63": {"fr": "Autres articles textiles", "en": "Other textile articles"},
    "64": {"fr": "Chaussures", "en": "Footwear"},
    "65": {"fr": "Coiffures", "en": "Headgear"},
    "66": {"fr": "Parapluies", "en": "Umbrellas"},
    "67": {"fr": "Plumes apprêtées", "en": "Prepared feathers"},
    "68": {"fr": "Ouvrages en pierres", "en": "Stone articles"},
    "69": {"fr": "Produits céramiques", "en": "Ceramic products"},
    "70": {"fr": "Verre et ouvrages", "en": "Glass and glassware"},
    "71": {"fr": "Perles, pierres précieuses", "en": "Pearls, precious stones"},
    "72": {"fr": "Fonte, fer et acier", "en": "Iron and steel"},
    "73": {"fr": "Ouvrages en fer/acier", "en": "Iron/steel articles"},
    "74": {"fr": "Cuivre et ouvrages", "en": "Copper and articles"},
    "75": {"fr": "Nickel et ouvrages", "en": "Nickel and articles"},
    "76": {"fr": "Aluminium et ouvrages", "en": "Aluminum and articles"},
    "78": {"fr": "Plomb et ouvrages", "en": "Lead and articles"},
    "79": {"fr": "Zinc et ouvrages", "en": "Zinc and articles"},
    "80": {"fr": "Étain et ouvrages", "en": "Tin and articles"},
    "81": {"fr": "Autres métaux communs", "en": "Other base metals"},
    "82": {"fr": "Outils en métaux communs", "en": "Tools of base metal"},
    "83": {"fr": "Ouvrages divers en métaux", "en": "Miscellaneous metal articles"},
    "84": {"fr": "Machines, appareils mécaniques", "en": "Machinery"},
    "85": {"fr": "Machines et appareils électriques", "en": "Electrical machinery"},
    "86": {"fr": "Véhicules ferroviaires", "en": "Railway vehicles"},
    "87": {"fr": "Véhicules automobiles", "en": "Vehicles"},
    "88": {"fr": "Aéronefs, engins spatiaux", "en": "Aircraft, spacecraft"},
    "89": {"fr": "Navires, bateaux", "en": "Ships, boats"},
    "90": {"fr": "Instruments optiques, médicaux", "en": "Optical, medical instruments"},
    "91": {"fr": "Horlogerie", "en": "Clocks and watches"},
    "92": {"fr": "Instruments de musique", "en": "Musical instruments"},
    "93": {"fr": "Armes et munitions", "en": "Arms and ammunition"},
    "94": {"fr": "Meubles, literie", "en": "Furniture, bedding"},
    "95": {"fr": "Jouets, jeux", "en": "Toys, games"},
    "96": {"fr": "Ouvrages divers", "en": "Miscellaneous articles"},
    "97": {"fr": "Objets d'art", "en": "Works of art"},
    # Specific HS4 codes
    "0603": {"fr": "Fleurs coupées", "en": "Cut flowers"},
    "0713": {"fr": "Légumes secs", "en": "Dried legumes"},
    "0805": {"fr": "Agrumes", "en": "Citrus fruits"},
    "0901": {"fr": "Café", "en": "Coffee"},
    "0902": {"fr": "Thé", "en": "Tea"},
    "1001": {"fr": "Blé et méteil", "en": "Wheat and meslin"},
    "1005": {"fr": "Maïs", "en": "Maize/corn"},
    "1006": {"fr": "Riz", "en": "Rice"},
    "1201": {"fr": "Fèves de soja", "en": "Soybeans"},
    "1207": {"fr": "Graines de sésame", "en": "Sesame seeds"},
    "1509": {"fr": "Huile d'olive", "en": "Olive oil"},
    "1511": {"fr": "Huile de palme", "en": "Palm oil"},
    "1512": {"fr": "Huile de tournesol", "en": "Sunflower oil"},
    "1701": {"fr": "Sucres de canne/betterave", "en": "Cane/beet sugar"},
    "1801": {"fr": "Cacao en fèves", "en": "Cocoa beans"},
    "2202": {"fr": "Boissons non alcoolisées", "en": "Non-alcoholic beverages"},
    "2523": {"fr": "Ciment", "en": "Cement"},
    "2709": {"fr": "Huiles brutes de pétrole", "en": "Crude petroleum oils"},
    "2710": {"fr": "Huiles de pétrole raffinées", "en": "Refined petroleum oils"},
    "2711": {"fr": "Gaz de pétrole", "en": "Petroleum gases"},
    "3004": {"fr": "Médicaments", "en": "Medicaments"},
    "3102": {"fr": "Engrais azotés", "en": "Nitrogen fertilizers"},
    "3105": {"fr": "Engrais NPK", "en": "NPK fertilizers"},
    "3901": {"fr": "Polymères d'éthylène", "en": "Ethylene polymers"},
    "3902": {"fr": "Polymères de propylène", "en": "Propylene polymers"},
    "4011": {"fr": "Pneumatiques neufs", "en": "New pneumatic tires"},
    "5201": {"fr": "Coton non cardé", "en": "Cotton, not carded"},
    "7108": {"fr": "Or", "en": "Gold"},
    "7208": {"fr": "Produits laminés plats en fer", "en": "Flat-rolled iron products"},
    "7403": {"fr": "Cuivre affiné", "en": "Refined copper"},
    "8517": {"fr": "Téléphones", "en": "Telephones"},
    "8544": {"fr": "Fils et câbles électriques", "en": "Insulated wire, cable"},
    "8703": {"fr": "Voitures de tourisme", "en": "Motor cars"},
    "8704": {"fr": "Véhicules pour transport de marchandises", "en": "Goods transport vehicles"},
}


class RealTradeDataService:
    """
    Service to fetch real trade data from free APIs
    """

    def __init__(self):
        self.timeout = 30.0
        self._cache = {}
        self._cache_ttl = 3600  # 1 hour

    async def get_oec_imports(
        self, country_iso3: str, year: int = 2022, limit: int = 100
    ) -> List[Dict]:
        """
        Get imports for a country from OEC API
        """
        country_info = AFRICAN_COUNTRIES.get(country_iso3.upper())
        if not country_info:
            return []

        oec_id = country_info["oec"]

        try:
            params = {
                "cube": "trade_i_baci_a_17",
                "drilldowns": "Year,Importer Country,HS4",
                "measures": "Trade Value,Quantity",
                "Year": str(year),
                "Importer Country": oec_id,
                "limit": str(limit * 5),  # Get more to filter
            }

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(OEC_BASE_URL, params=_oec_params(params))

                if response.status_code == 200:
                    data = response.json()
                    records = data.get("data", [])

                    # Sort by trade value and take top items
                    records.sort(key=lambda x: x.get("Trade Value", 0), reverse=True)

                    # Format results
                    results = []
                    for record in records[:limit]:
                        hs4_id = str(record.get("HS4 ID", ""))
                        hs4_code = hs4_id[-4:].zfill(4) if hs4_id else ""

                        results.append(
                            {
                                "hs_code": hs4_code,
                                "product_name": record.get("HS4", ""),
                                "trade_value": record.get("Trade Value", 0),
                                "quantity": record.get("Quantity", 0),
                                "year": year,
                            }
                        )

                    return results

        except Exception as e:
            logger.error(f"OEC API error: {str(e)}")

        return []

    async def get_oec_exports(
        self, country_iso3: str, year: int = 2022, limit: int = 100
    ) -> List[Dict]:
        """
        Get exports for a country from OEC API
        """
        country_info = AFRICAN_COUNTRIES.get(country_iso3.upper())
        if not country_info:
            return []

        oec_id = country_info["oec"]

        try:
            params = {
                "cube": "trade_i_baci_a_17",
                "drilldowns": "Year,Exporter Country,HS4",
                "measures": "Trade Value,Quantity",
                "Year": str(year),
                "Exporter Country": oec_id,
                "limit": str(limit * 5),
            }

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(OEC_BASE_URL, params=_oec_params(params))

                if response.status_code == 200:
                    data = response.json()
                    records = data.get("data", [])

                    records.sort(key=lambda x: x.get("Trade Value", 0), reverse=True)

                    results = []
                    for record in records[:limit]:
                        hs4_id = str(record.get("HS4 ID", ""))
                        hs4_code = hs4_id[-4:].zfill(4) if hs4_id else ""

                        results.append(
                            {
                                "hs_code": hs4_code,
                                "product_name": record.get("HS4", ""),
                                "trade_value": record.get("Trade Value", 0),
                                "quantity": record.get("Quantity", 0),
                                "year": year,
                            }
                        )

                    return results

        except Exception as e:
            logger.error(f"OEC API error: {str(e)}")

        return []

    async def get_oec_bilateral_from_world(
        self, importer_iso3: str, year: int = 2022, limit: int = 50
    ) -> Dict:
        """
        Get imports by partner country to identify non-African sources
        """
        country_info = AFRICAN_COUNTRIES.get(importer_iso3.upper())
        if not country_info:
            return {"total": 0, "from_africa": 0, "from_outside": 0, "products_from_outside": []}

        oec_id = country_info["oec"]
        african_oec_ids = [c["oec"] for c in AFRICAN_COUNTRIES.values()]

        try:
            # Get imports by exporter country
            params = {
                "cube": "trade_i_baci_a_17",
                "drilldowns": "Year,Importer Country,Exporter Country,HS4",
                "measures": "Trade Value",
                "Year": str(year),
                "Importer Country": oec_id,
                "limit": "500",
            }

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(OEC_BASE_URL, params=_oec_params(params))

                if response.status_code == 200:
                    data = response.json()
                    records = data.get("data", [])

                    total_value = 0
                    from_africa = 0
                    from_outside = 0
                    products_from_outside = defaultdict(lambda: {"value": 0, "sources": set()})

                    for record in records:
                        value = record.get("Trade Value", 0)
                        exporter_id = record.get("Exporter Country ID", "")
                        hs4_id = str(record.get("HS4 ID", ""))
                        hs4_code = hs4_id[-4:].zfill(4) if hs4_id else ""
                        product_name = record.get("HS4", "")
                        exporter_name = record.get("Exporter Country", "")

                        total_value += value

                        # Check if from Africa
                        is_african = any(
                            exporter_id.startswith(af_id.replace("af", ""))
                            for af_id in african_oec_ids
                        )

                        if is_african:
                            from_africa += value
                        else:
                            from_outside += value
                            if hs4_code and value > 1000000:  # Only significant imports
                                products_from_outside[hs4_code]["value"] += value
                                products_from_outside[hs4_code]["name"] = product_name
                                products_from_outside[hs4_code]["sources"].add(exporter_name)

                    # Format products from outside
                    products_list = []
                    for hs_code, data in products_from_outside.items():
                        products_list.append(
                            {
                                "hs_code": hs_code,
                                "product_name": data["name"],
                                "import_value": data["value"],
                                "source_regions": list(data["sources"])[:3],
                            }
                        )

                    products_list.sort(key=lambda x: x["import_value"], reverse=True)

                    return {
                        "total": total_value,
                        "from_africa": from_africa,
                        "from_outside": from_outside,
                        "africa_share": (from_africa / total_value * 100) if total_value > 0 else 0,
                        "products_from_outside": products_list[:limit],
                    }

        except Exception as e:
            logger.error(f"OEC bilateral API error: {str(e)}")

        return {"total": 0, "from_africa": 0, "from_outside": 0, "products_from_outside": []}

    async def ping_oec(self, year: int = 2022) -> Dict:
        """
        Lightweight connectivity check against the OEC API.

        Performs a minimal real request and reports whether OEC is reachable,
        the HTTP status, latency and how many records came back. Used by the
        /ai/oec-health diagnostic so operators can confirm that outbound access
        to api-v2.oec.world is allowed by the deployment's network policy.
        """
        params = {
            "cube": "trade_i_baci_a_17",
            "drilldowns": "Year,Exporter Country,HS4",
            "measures": "Trade Value",
            "Year": str(year),
            "Exporter Country": "afzaf",
            "limit": "1",
        }
        start = datetime.utcnow()
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(OEC_BASE_URL, params=_oec_params(params))
            latency_ms = int((datetime.utcnow() - start).total_seconds() * 1000)
            records = []
            if response.status_code == 200:
                records = response.json().get("data", [])
            return {
                "reachable": response.status_code == 200 and bool(records),
                "status_code": response.status_code,
                "latency_ms": latency_ms,
                "records": len(records),
                "endpoint": OEC_BASE_URL,
                "token_configured": bool(OEC_API_TOKEN),
                "error": None if response.status_code == 200 else f"HTTP {response.status_code}",
            }
        except Exception as e:
            latency_ms = int((datetime.utcnow() - start).total_seconds() * 1000)
            return {
                "reachable": False,
                "status_code": None,
                "latency_ms": latency_ms,
                "records": 0,
                "endpoint": OEC_BASE_URL,
                "token_configured": bool(OEC_API_TOKEN),
                "error": str(e),
            }

    async def get_bilateral_trade(
        self, exporter_iso3: str, importer_iso3: str, year: int = 2022, limit: int = 10
    ) -> Dict:
        """
        Real directional trade flow exporter -> importer from the OEC API.

        Returns the total exported value plus the top HS4 products. Used by the
        country-comparison view to show real bilateral trade (not estimates).
        """
        exp_info = AFRICAN_COUNTRIES.get(exporter_iso3.upper())
        imp_info = AFRICAN_COUNTRIES.get(importer_iso3.upper())
        if not exp_info or not imp_info or not exp_info.get("oec") or not imp_info.get("oec"):
            return {"total_value": 0, "top_products": [], "year": year}

        try:
            params = {
                "cube": "trade_i_baci_a_17",
                "drilldowns": "Year,Exporter Country,Importer Country,HS4",
                "measures": "Trade Value",
                "Year": str(year),
                "Exporter Country": exp_info["oec"],
                "Importer Country": imp_info["oec"],
                "limit": "300",
            }

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(OEC_BASE_URL, params=_oec_params(params))

                if response.status_code == 200:
                    records = response.json().get("data", [])
                    total_value = 0
                    products = []
                    for record in records:
                        value = record.get("Trade Value", 0)
                        total_value += value
                        hs4_id = str(record.get("HS4 ID", ""))
                        hs4_code = hs4_id[-4:].zfill(4) if hs4_id else ""
                        products.append(
                            {
                                "hs_code": hs4_code,
                                "product_name": record.get("HS4", ""),
                                "value": value,
                            }
                        )

                    products.sort(key=lambda p: p["value"], reverse=True)
                    return {
                        "total_value": total_value,
                        "top_products": products[:limit],
                        "year": year,
                    }

        except Exception as e:
            logger.error(f"OEC bilateral trade API error: {str(e)}")

        return {"total_value": 0, "top_products": [], "year": year}

    async def get_african_exporters_for_product(self, hs_code: str, year: int = 2022) -> List[Dict]:
        """
        Find African countries that export a specific product
        Queries OEC API for all African exporters
        """
        try:
            # Search for HS4 (first 4 digits)
            hs4 = hs_code[:4] if len(hs_code) >= 4 else hs_code.zfill(4)

            # Build list of African OEC IDs
            african_exporters_found = []

            # Query OEC for each major African exporter
            major_exporters = [
                "NGA",
                "ZAF",
                "EGY",
                "DZA",
                "AGO",
                "MAR",
                "KEN",
                "ETH",
                "GHA",
                "CIV",
                "TZA",
                "TUN",
                "SEN",
                "CMR",
                "COD",
                "ZMB",
            ]

            for iso3 in major_exporters:
                country_info = AFRICAN_COUNTRIES.get(iso3)
                if not country_info:
                    continue

                oec_id = country_info["oec"]

                params = {
                    "cube": "trade_i_baci_a_17",
                    "drilldowns": "Year,Exporter Country,HS4",
                    "measures": "Trade Value,Quantity",
                    "Year": str(year),
                    "Exporter Country": oec_id,
                    "limit": "100",
                }

                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.get(OEC_BASE_URL, params=_oec_params(params))

                    if response.status_code == 200:
                        data = response.json()
                        records = data.get("data", [])

                        for record in records:
                            hs4_id = str(record.get("HS4 ID", ""))
                            record_hs4 = hs4_id[-4:].zfill(4) if hs4_id else ""

                            # Match HS code (at least first 2 digits)
                            if record_hs4[:2] == hs4[:2]:
                                export_value = record.get("Trade Value", 0)
                                if export_value > 0:
                                    african_exporters_found.append(
                                        {
                                            "country_iso3": iso3,
                                            "country_name": country_info["name_fr"],
                                            "hs_code": record_hs4,
                                            "product_name": record.get("HS4", ""),
                                            "export_value": export_value,
                                            "quantity": record.get("Quantity", 0),
                                        }
                                    )

            # Remove duplicates and aggregate by country
            country_exports = {}
            for exp in african_exporters_found:
                iso3 = exp["country_iso3"]
                if iso3 not in country_exports:
                    country_exports[iso3] = {
                        "country_iso3": iso3,
                        "country_name": exp["country_name"],
                        "export_value": 0,
                        "products": [],
                    }
                country_exports[iso3]["export_value"] += exp["export_value"]
                country_exports[iso3]["products"].append(exp["product_name"])

            # Convert to list and sort
            result = list(country_exports.values())
            result.sort(key=lambda x: x["export_value"], reverse=True)

            return result

        except Exception as e:
            logger.error(f"OEC product exporters API error: {str(e)}")

        return []

    async def get_african_importers_for_product(self, hs_code: str, year: int = 2022) -> List[Dict]:
        """
        African countries that import a specific product, at the EXACT HS4/HS6
        level, across ALL 54 African countries (not a 10-country chapter-level
        sample).

        - 6+ digit code -> HS6 drilldown, exact 6-digit match.
        - 4-5 digit code -> HS4 drilldown, exact 4-digit match.

        Primary channel: the statistics module's FREE OEC client
        (``oec_trade_service.get_top_african_importers``) — ONE cached request
        for all importers, no token needed. Fallback: the legacy per-country
        fan-out (one request per country, small semaphore).
        """
        clean_hs = "".join(ch for ch in (hs_code or "") if ch.isdigit())
        try:
            from services.oec_trade_service import oec_service

            res = await oec_service.get_top_african_importers(clean_hs, year)
            rows = (res or {}).get("data") or []
            if rows:
                return rows
        except Exception as e:
            logger.warning(f"OEC importers via free stats channel {hs_code}: {e}")

        clean = clean_hs
        if len(clean) >= 6:
            level, code, id_len, limit = "HS6", clean[:6], 6, "6000"
        else:
            level, code, id_len, limit = "HS4", clean[:4].zfill(4), 4, "2000"

        importers = [
            (iso3, info)
            for iso3, info in AFRICAN_COUNTRIES.items()
            if info.get("has_trade_data") and info.get("oec")
        ]

        sem = asyncio.Semaphore(6)

        async def _one(client: httpx.AsyncClient, iso3: str, info: Dict):
            params = {
                "cube": "trade_i_baci_a_17",
                "drilldowns": f"Year,Importer Country,{level}",
                "measures": "Trade Value",
                "Year": str(year),
                "Importer Country": info["oec"],
                "limit": limit,
            }
            async with sem:
                try:
                    response = await client.get(OEC_BASE_URL, params=_oec_params(params))
                    if response.status_code != 200:
                        return None
                    records = response.json().get("data", [])
                except Exception as e:
                    logger.warning(f"OEC importers {iso3}: {e}")
                    return None

                total = 0.0
                for record in records:
                    rid = str(record.get(f"{level} ID", ""))
                    rcode = rid[-id_len:].zfill(id_len) if rid else ""
                    if rcode == code:
                        value = record.get("Trade Value") or 0
                        if value > 0:
                            total += value
                if total <= 0:
                    return None
                return {
                    "country_iso3": iso3,
                    "country_name": info["name_fr"],
                    "hs_code": code,
                    "import_value": total,
                }

        try:
            # Single pooled client shared across all country tasks (connection
            # reuse; the semaphore still bounds concurrency).
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                gathered = await asyncio.gather(*[_one(client, i, inf) for i, inf in importers])
        except Exception as e:
            logger.error(f"OEC product importers API error: {str(e)}")
            return []

        result = [r for r in gathered if r]
        result.sort(key=lambda x: x["import_value"], reverse=True)
        return result

    async def get_country_product_imports(
        self, importer_iso3: str, hs_code: str, year: int = 2022
    ) -> Dict:
        """
        Total imports (USD) of a product by ONE country. Used to feed the
        bilateral report's market-potential component and the S3 observed-imports
        signal from real demand.

        Primary channel: the SAME OEC client as the statistics module's
        SH2/SH4/SH6 search (``oec_trade_service``) — persistent cache with
        stale-on-error, and one cached OEC response per (country, period)
        serves EVERY HS code (the HS filter is client-side). So a country
        already browsed in the statistics tab keeps feeding the opportunities
        module even when OEC is momentarily unreachable.

        Fallback: the legacy direct OEC request (kept for environments where
        the shared client is unavailable).

        Returns {available, import_value_usd, hs_code, year, source} or
        {available: False} — never fabricated.
        """
        clean_hs = "".join(ch for ch in (hs_code or "") if ch.isdigit())
        try:
            from services.oec_trade_service import DEFAULT_YEAR, oec_service

            level = "hs6" if len(clean_hs) >= 6 else ("hs4" if len(clean_hs) >= 4 else "hs2")
            hist = await oec_service.get_country_hs6_history(
                country_iso3=importer_iso3,
                hs_code=clean_hs,
                n_years=3,
                end_year=max(int(year or 0), DEFAULT_YEAR),
                level=level,
            )
            rows = (hist or {}).get("chart_rows") or []
            # Most recent year with observed imports (> 0).
            for row in sorted(rows, key=lambda r: -(r.get("year") or 0)):
                if (row.get("imports") or 0) > 0:
                    return {
                        "available": True,
                        "import_value_usd": float(row["imports"]),
                        "hs_code": clean_hs[:6] if len(clean_hs) >= 6 else clean_hs,
                        "year": row.get("year"),
                        "source": hist.get("source") or "OEC / BACI",
                        "channel": "oec_trade_service (cache partagé avec le module Statistiques)",
                    }
        except Exception as e:
            logger.warning(f"OEC shared-channel imports {importer_iso3}/{hs_code}: {e}")

        info = AFRICAN_COUNTRIES.get((importer_iso3 or "").upper())
        if not info or not info.get("oec"):
            return {"available": False, "note": "Pays importateur inconnu de l'OEC."}

        clean = "".join(ch for ch in (hs_code or "") if ch.isdigit())
        if len(clean) >= 6:
            level, code, id_len, limit = "HS6", clean[:6], 6, "6000"
        else:
            level, code, id_len, limit = "HS4", clean[:4].zfill(4), 4, "2000"

        params = {
            "cube": "trade_i_baci_a_17",
            "drilldowns": f"Year,Importer Country,{level}",
            "measures": "Trade Value",
            "Year": str(year),
            "Importer Country": info["oec"],
            "limit": limit,
        }
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(OEC_BASE_URL, params=_oec_params(params))
            if response.status_code != 200:
                return {"available": False, "note": f"HTTP {response.status_code}"}
            records = response.json().get("data", [])
        except Exception as e:
            logger.warning(f"OEC country-product imports {importer_iso3}: {e}")
            return {"available": False, "note": str(e)}

        total = 0.0
        for record in records:
            rid = str(record.get(f"{level} ID", ""))
            rcode = rid[-id_len:].zfill(id_len) if rid else ""
            if rcode == code:
                value = record.get("Trade Value") or 0
                if value > 0:
                    total += value
        if total <= 0:
            return {"available": False, "note": "Aucune importation observée."}
        return {
            "available": True,
            "import_value_usd": total,
            "hs_code": code,
            "year": year,
            "source": "OEC / UN Comtrade (BACI)",
        }

    async def get_country_product_import_history(
        self, importer_iso3: str, hs_code: str, n_years: int = 5, end_year: int = 2022
    ) -> Dict:
        """
        Historique pluriannuel des imports (USD) d'UN pays pour un SH — utilisé
        par le repli "production continentale indisponible" du module Demande
        (``demand_estimation_service.estimate_need_from_own_imports``) : quand
        aucune donnée de production (FAO/USGS/UNIDO) n'existe pour ce SH (ex.
        instruments médicaux SH90), l'estimation du besoin national se rabat sur
        les imports RÉELS du pays lui-même, moyennés sur plusieurs années pour
        les biens durables/longue conservation (achat ponctuel/cyclique).

        Même canal OEC partagé (cache persistant, stale-on-error) que
        ``get_country_product_imports`` — une réponse par (pays, période) sert
        tous les codes SH déjà interrogés pour ce pays.

        Retourne {available, imports: [{year, import_value_usd, no_data}], source}
        ou {available: False} — jamais fabriqué.
        """
        clean_hs = "".join(ch for ch in (hs_code or "") if ch.isdigit())
        try:
            from services.oec_trade_service import DEFAULT_YEAR, oec_service

            level = "hs6" if len(clean_hs) >= 6 else ("hs4" if len(clean_hs) >= 4 else "hs2")
            hist = await oec_service.get_country_hs6_history(
                country_iso3=importer_iso3,
                hs_code=clean_hs,
                n_years=n_years,
                end_year=min(int(end_year or DEFAULT_YEAR), DEFAULT_YEAR),
                level=level,
            )
            rows = (hist or {}).get("imports") or []
            if not rows:
                return {"available": False, "note": "Historique d'imports indisponible."}
            imports = [
                {
                    "year": r.get("year"),
                    "import_value_usd": r.get("trade_value"),
                    "no_data": bool(r.get("no_data")),
                }
                for r in rows
            ]
            return {
                "available": True,
                "imports": imports,
                "source": hist.get("source") or "OEC / BACI",
            }
        except Exception as e:
            logger.warning(f"OEC import history {importer_iso3}/{hs_code}: {e}")
            return {"available": False, "note": str(e)}


def get_product_name(hs_code: str, lang: str = "fr", oec_name: str = None) -> str:
    """
    Intitulé officiel d'un code SH, du plus spécifique au plus général :
    sous-position SH6 exacte (base OMD 5 800+ codes) -> position SH4 ->
    chapitre SH2 -> nom OEC fourni -> générique.

    Bug corrigé : l'ancien code tronquait un SH6 à ses 4 DERNIERS chiffres
    (« 180400 » -> « 0400 »), rattachant chaque sous-position au chapitre de
    ses chiffres 3-4 — « Beurre de cacao » était étiqueté « Produits
    laitiers, œufs » (chapitre 04), et tout SH6 dont les chiffres 3-4
    valaient « 01 » devenait « Animaux vivants ».
    """
    if not hs_code:
        return oec_name or "Produit inconnu"

    clean_code = "".join(ch for ch in str(hs_code) if ch.isdigit())
    if not clean_code:
        return oec_name or f"HS {hs_code}"

    # Sous-position SH6 exacte — libellés officiels FR/EN de la base OMD.
    if len(clean_code) >= 6:
        try:
            from etl.hs6_database import HS6_DATABASE

            entry = HS6_DATABASE.get(clean_code[:6])
            if entry:
                label = entry.get(f"description_{lang}") or entry.get("description_en")
                if label:
                    return label
        except ImportError:  # base indisponible — replis ci-dessous
            pass

    # Position SH4 puis chapitre SH2, dans la table locale.
    for prefix_len in (4, 2):
        prefix = clean_code[:prefix_len]
        if len(prefix) == prefix_len and prefix in HS_PRODUCT_NAMES:
            return HS_PRODUCT_NAMES[prefix].get(
                lang, HS_PRODUCT_NAMES[prefix].get("en", f"HS {prefix}")
            )

    if oec_name:
        return oec_name

    return f"HS {hs_code}"


def get_country_name(iso3: str, lang: str = "fr") -> str:
    """Get country name"""
    country = AFRICAN_COUNTRIES.get(iso3.upper(), {})
    return country.get(f"name_{lang}", country.get("name_en", iso3))


# Singleton instance
real_trade_service = RealTradeDataService()
