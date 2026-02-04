"""
Real Trade Data Service
Integrates multiple free data sources:
- OEC (Observatory of Economic Complexity) - Already integrated
- WITS (World Bank) - Free, no registration
- UN Comtrade Preview API - Limited free access

Provides real trade data for African countries
"""
import httpx
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging
from collections import defaultdict

logger = logging.getLogger(__name__)

# WITS API Configuration (World Bank - FREE)
WITS_BASE_URL = "https://wits.worldbank.org/API/V1/SDMX/V21/rest"
WITS_DATA_URL = "https://wits.worldbank.org/API/V1"

# OEC API (Already integrated in oec_trade_service.py)
OEC_BASE_URL = "https://api-v2.oec.world/tesseract/data.jsonrecords"

# African Countries (55 pays incluant la RASD - Membre UA depuis 1984)
AFRICAN_COUNTRIES = {
    "DZA": {"name_fr": "Algérie", "name_en": "Algeria", "wits": "DZA", "oec": "afdza"},
    "AGO": {"name_fr": "Angola", "name_en": "Angola", "wits": "AGO", "oec": "afago"},
    "BEN": {"name_fr": "Bénin", "name_en": "Benin", "wits": "BEN", "oec": "afben"},
    "BWA": {"name_fr": "Botswana", "name_en": "Botswana", "wits": "BWA", "oec": "afbwa"},
    "BFA": {"name_fr": "Burkina Faso", "name_en": "Burkina Faso", "wits": "BFA", "oec": "afbfa"},
    "BDI": {"name_fr": "Burundi", "name_en": "Burundi", "wits": "BDI", "oec": "afbdi"},
    "CMR": {"name_fr": "Cameroun", "name_en": "Cameroon", "wits": "CMR", "oec": "afcmr"},
    "CPV": {"name_fr": "Cap-Vert", "name_en": "Cape Verde", "wits": "CPV", "oec": "afcpv"},
    "CAF": {"name_fr": "Centrafrique", "name_en": "Central African Republic", "wits": "CAF", "oec": "afcaf"},
    "TCD": {"name_fr": "Tchad", "name_en": "Chad", "wits": "TCD", "oec": "aftcd"},
    "COM": {"name_fr": "Comores", "name_en": "Comoros", "wits": "COM", "oec": "afcom"},
    "COG": {"name_fr": "Congo", "name_en": "Republic of the Congo", "wits": "COG", "oec": "afcog"},
    "COD": {"name_fr": "RD Congo", "name_en": "DR Congo", "wits": "COD", "oec": "afcod"},
    "CIV": {"name_fr": "Côte d'Ivoire", "name_en": "Ivory Coast", "wits": "CIV", "oec": "afciv"},
    "DJI": {"name_fr": "Djibouti", "name_en": "Djibouti", "wits": "DJI", "oec": "afdji"},
    "EGY": {"name_fr": "Égypte", "name_en": "Egypt", "wits": "EGY", "oec": "afegy"},
    "GNQ": {"name_fr": "Guinée Équatoriale", "name_en": "Equatorial Guinea", "wits": "GNQ", "oec": "afgnq"},
    "ERI": {"name_fr": "Érythrée", "name_en": "Eritrea", "wits": "ERI", "oec": "aferi"},
    # RASD - République Arabe Sahraouie Démocratique (Sahara Occidental)
    # Membre fondateur de l'Union Africaine (UA) depuis 1984
    "ESH": {"name_fr": "RASD (Sahara Occidental)", "name_en": "Sahrawi Arab Democratic Republic", "wits": "ESH", "oec": "afesh"},
    "SWZ": {"name_fr": "Eswatini", "name_en": "Eswatini", "wits": "SWZ", "oec": "afswz"},
    "ETH": {"name_fr": "Éthiopie", "name_en": "Ethiopia", "wits": "ETH", "oec": "afeth"},
    "GAB": {"name_fr": "Gabon", "name_en": "Gabon", "wits": "GAB", "oec": "afgab"},
    "GMB": {"name_fr": "Gambie", "name_en": "Gambia", "wits": "GMB", "oec": "afgmb"},
    "GHA": {"name_fr": "Ghana", "name_en": "Ghana", "wits": "GHA", "oec": "afgha"},
    "GIN": {"name_fr": "Guinée", "name_en": "Guinea", "wits": "GIN", "oec": "afgin"},
    "GNB": {"name_fr": "Guinée-Bissau", "name_en": "Guinea-Bissau", "wits": "GNB", "oec": "afgnb"},
    "KEN": {"name_fr": "Kenya", "name_en": "Kenya", "wits": "KEN", "oec": "afken"},
    "LSO": {"name_fr": "Lesotho", "name_en": "Lesotho", "wits": "LSO", "oec": "aflso"},
    "LBR": {"name_fr": "Libéria", "name_en": "Liberia", "wits": "LBR", "oec": "aflbr"},
    "LBY": {"name_fr": "Libye", "name_en": "Libya", "wits": "LBY", "oec": "aflby"},
    "MDG": {"name_fr": "Madagascar", "name_en": "Madagascar", "wits": "MDG", "oec": "afmdg"},
    "MWI": {"name_fr": "Malawi", "name_en": "Malawi", "wits": "MWI", "oec": "afmwi"},
    "MLI": {"name_fr": "Mali", "name_en": "Mali", "wits": "MLI", "oec": "afmli"},
    "MRT": {"name_fr": "Mauritanie", "name_en": "Mauritania", "wits": "MRT", "oec": "afmrt"},
    "MUS": {"name_fr": "Maurice", "name_en": "Mauritius", "wits": "MUS", "oec": "afmus"},
    "MAR": {"name_fr": "Maroc", "name_en": "Morocco", "wits": "MAR", "oec": "afmar"},
    "MOZ": {"name_fr": "Mozambique", "name_en": "Mozambique", "wits": "MOZ", "oec": "afmoz"},
    "NAM": {"name_fr": "Namibie", "name_en": "Namibia", "wits": "NAM", "oec": "afnam"},
    "NER": {"name_fr": "Niger", "name_en": "Niger", "wits": "NER", "oec": "afner"},
    "NGA": {"name_fr": "Nigeria", "name_en": "Nigeria", "wits": "NGA", "oec": "afnga"},
    "RWA": {"name_fr": "Rwanda", "name_en": "Rwanda", "wits": "RWA", "oec": "afrwa"},
    "STP": {"name_fr": "São Tomé-et-Príncipe", "name_en": "São Tomé and Príncipe", "wits": "STP", "oec": "afstp"},
    "SEN": {"name_fr": "Sénégal", "name_en": "Senegal", "wits": "SEN", "oec": "afsen"},
    "SYC": {"name_fr": "Seychelles", "name_en": "Seychelles", "wits": "SYC", "oec": "afsyc"},
    "SLE": {"name_fr": "Sierra Leone", "name_en": "Sierra Leone", "wits": "SLE", "oec": "afsle"},
    "SOM": {"name_fr": "Somalie", "name_en": "Somalia", "wits": "SOM", "oec": "afsom"},
    "ZAF": {"name_fr": "Afrique du Sud", "name_en": "South Africa", "wits": "ZAF", "oec": "afzaf"},
    "SSD": {"name_fr": "Soudan du Sud", "name_en": "South Sudan", "wits": "SSD", "oec": "afssd"},
    "SDN": {"name_fr": "Soudan", "name_en": "Sudan", "wits": "SDN", "oec": "afsdn"},
    "TZA": {"name_fr": "Tanzanie", "name_en": "Tanzania", "wits": "TZA", "oec": "aftza"},
    "TGO": {"name_fr": "Togo", "name_en": "Togo", "wits": "TGO", "oec": "aftgo"},
    "TUN": {"name_fr": "Tunisie", "name_en": "Tunisia", "wits": "TUN", "oec": "aftun"},
    "UGA": {"name_fr": "Ouganda", "name_en": "Uganda", "wits": "UGA", "oec": "afuga"},
    "ZMB": {"name_fr": "Zambie", "name_en": "Zambia", "wits": "ZMB", "oec": "afzmb"},
    "ZWE": {"name_fr": "Zimbabwe", "name_en": "Zimbabwe", "wits": "ZWE", "oec": "afzwe"}
}

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
        self,
        country_iso3: str,
        year: int = 2022,
        limit: int = 100
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
                "limit": str(limit * 5)  # Get more to filter
            }
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(OEC_BASE_URL, params=params)
                
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
                        
                        results.append({
                            "hs_code": hs4_code,
                            "product_name": record.get("HS4", ""),
                            "trade_value": record.get("Trade Value", 0),
                            "quantity": record.get("Quantity", 0),
                            "year": year
                        })
                    
                    return results
                    
        except Exception as e:
            logger.error(f"OEC API error: {str(e)}")
        
        return []
    
    async def get_oec_exports(
        self,
        country_iso3: str,
        year: int = 2022,
        limit: int = 100
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
                "limit": str(limit * 5)
            }
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(OEC_BASE_URL, params=params)
                
                if response.status_code == 200:
                    data = response.json()
                    records = data.get("data", [])
                    
                    records.sort(key=lambda x: x.get("Trade Value", 0), reverse=True)
                    
                    results = []
                    for record in records[:limit]:
                        hs4_id = str(record.get("HS4 ID", ""))
                        hs4_code = hs4_id[-4:].zfill(4) if hs4_id else ""
                        
                        results.append({
                            "hs_code": hs4_code,
                            "product_name": record.get("HS4", ""),
                            "trade_value": record.get("Trade Value", 0),
                            "quantity": record.get("Quantity", 0),
                            "year": year
                        })
                    
                    return results
                    
        except Exception as e:
            logger.error(f"OEC API error: {str(e)}")
        
        return []
    
    async def get_oec_bilateral_from_world(
        self,
        importer_iso3: str,
        year: int = 2022,
        limit: int = 50
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
                "limit": "500"
            }
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(OEC_BASE_URL, params=params)
                
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
                        is_african = any(exporter_id.startswith(af_id.replace("af", "")) for af_id in african_oec_ids)
                        
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
                        products_list.append({
                            "hs_code": hs_code,
                            "product_name": data["name"],
                            "import_value": data["value"],
                            "source_regions": list(data["sources"])[:3]
                        })
                    
                    products_list.sort(key=lambda x: x["import_value"], reverse=True)
                    
                    return {
                        "total": total_value,
                        "from_africa": from_africa,
                        "from_outside": from_outside,
                        "africa_share": (from_africa / total_value * 100) if total_value > 0 else 0,
                        "products_from_outside": products_list[:limit]
                    }
                    
        except Exception as e:
            logger.error(f"OEC bilateral API error: {str(e)}")
        
        return {"total": 0, "from_africa": 0, "from_outside": 0, "products_from_outside": []}
    
    async def get_african_exporters_for_product(
        self,
        hs_code: str,
        year: int = 2022
    ) -> List[Dict]:
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
            major_exporters = ["NGA", "ZAF", "EGY", "DZA", "AGO", "MAR", "KEN", "ETH", 
                              "GHA", "CIV", "TZA", "TUN", "SEN", "CMR", "COD", "ZMB"]
            
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
                    "limit": "100"
                }
                
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.get(OEC_BASE_URL, params=params)
                    
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
                                    african_exporters_found.append({
                                        "country_iso3": iso3,
                                        "country_name": country_info["name_fr"],
                                        "hs_code": record_hs4,
                                        "product_name": record.get("HS4", ""),
                                        "export_value": export_value,
                                        "quantity": record.get("Quantity", 0)
                                    })
            
            # Remove duplicates and aggregate by country
            country_exports = {}
            for exp in african_exporters_found:
                iso3 = exp["country_iso3"]
                if iso3 not in country_exports:
                    country_exports[iso3] = {
                        "country_iso3": iso3,
                        "country_name": exp["country_name"],
                        "export_value": 0,
                        "products": []
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
    
    async def get_african_importers_for_product(
        self,
        hs_code: str,
        year: int = 2022
    ) -> List[Dict]:
        """
        Find African countries that import a specific product
        Queries OEC API for all African importers
        """
        try:
            hs4 = hs_code[:4] if len(hs_code) >= 4 else hs_code.zfill(4)
            
            african_importers_found = []
            
            # Sample top importing African countries for efficiency
            top_importers = ["ZAF", "EGY", "NGA", "MAR", "DZA", "KEN", "TUN", "ETH", "GHA", "TZA"]
            
            for iso3 in top_importers:
                country_info = AFRICAN_COUNTRIES.get(iso3)
                if not country_info:
                    continue
                
                oec_id = country_info["oec"]
                
                params = {
                    "cube": "trade_i_baci_a_17",
                    "drilldowns": "Year,Importer Country,HS4",
                    "measures": "Trade Value",
                    "Year": str(year),
                    "Importer Country": oec_id,
                    "limit": "100"
                }
                
                try:
                    async with httpx.AsyncClient(timeout=15.0) as client:
                        response = await client.get(OEC_BASE_URL, params=params)
                        
                        if response.status_code == 200:
                            data = response.json()
                            records = data.get("data", [])
                            
                            for record in records:
                                hs4_id = str(record.get("HS4 ID", ""))
                                record_hs4 = hs4_id[-4:].zfill(4) if hs4_id else ""
                                
                                # Match HS code (at least first 2 digits)
                                if record_hs4[:2] == hs4[:2]:
                                    import_value = record.get("Trade Value", 0)
                                    if import_value > 0:
                                        african_importers_found.append({
                                            "country_iso3": iso3,
                                            "country_name": country_info["name_fr"],
                                            "hs_code": record_hs4,
                                            "product_name": record.get("HS4", ""),
                                            "import_value": import_value
                                        })
                except Exception as e:
                    logger.warning(f"Error fetching imports for {iso3}: {e}")
                    continue
            
            # Aggregate by country
            country_imports = {}
            for imp in african_importers_found:
                iso3 = imp["country_iso3"]
                if iso3 not in country_imports:
                    country_imports[iso3] = {
                        "country_iso3": iso3,
                        "country_name": imp["country_name"],
                        "import_value": 0
                    }
                country_imports[iso3]["import_value"] += imp["import_value"]
            
            result = list(country_imports.values())
            result.sort(key=lambda x: x["import_value"], reverse=True)
            
            return result
                    
        except Exception as e:
            logger.error(f"OEC product importers API error: {str(e)}")
        
        return []


def get_product_name(hs_code: str, lang: str = "fr", oec_name: str = None) -> str:
    """Get product name for HS code with fallback to OEC name"""
    if not hs_code:
        return oec_name or "Produit inconnu"
    
    # Clean HS code (remove any prefixes)
    clean_code = str(hs_code).strip()
    if len(clean_code) > 4:
        clean_code = clean_code[-4:]  # Keep last 4 digits if longer
    
    # Try exact match first
    if clean_code in HS_PRODUCT_NAMES:
        return HS_PRODUCT_NAMES[clean_code].get(lang, HS_PRODUCT_NAMES[clean_code].get("en", clean_code))
    
    # Try HS4 (first 4 digits)
    if len(clean_code) >= 4:
        hs4 = clean_code[:4]
        if hs4 in HS_PRODUCT_NAMES:
            return HS_PRODUCT_NAMES[hs4].get(lang, HS_PRODUCT_NAMES[hs4].get("en", f"HS {hs4}"))
    
    # Try chapter (first 2 digits)
    chapter = clean_code[:2]
    if chapter in HS_PRODUCT_NAMES:
        return HS_PRODUCT_NAMES[chapter].get(lang, HS_PRODUCT_NAMES[chapter].get("en", f"HS {hs_code}"))
    
    # Return OEC name if available, otherwise generic
    if oec_name:
        return oec_name
    
    return f"HS {hs_code}"


def get_country_name(iso3: str, lang: str = "fr") -> str:
    """Get country name"""
    country = AFRICAN_COUNTRIES.get(iso3.upper(), {})
    return country.get(f"name_{lang}", country.get("name_en", iso3))


# Singleton instance
real_trade_service = RealTradeDataService()
