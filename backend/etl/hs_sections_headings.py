"""
Sections HS, Rangées HS4 et Groupes d'utilisation
Source: WCO Harmonized System 2022
"""
import json
import os

HS_SECTIONS = {
    "I":     {"fr": "Animaux vivants et produits du règne animal", "en": "Live animals and animal products", "chapters": ["01","02","03","04","05"]},
    "II":    {"fr": "Produits du règne végétal", "en": "Vegetable products", "chapters": ["06","07","08","09","10","11","12","13","14"]},
    "III":   {"fr": "Graisses et huiles animales ou végétales", "en": "Animal or vegetable fats and oils", "chapters": ["15"]},
    "IV":    {"fr": "Produits des industries alimentaires; boissons, liquides alcooliques et vinaigres; tabacs", "en": "Prepared foodstuffs; beverages, spirits, vinegar; tobacco", "chapters": ["16","17","18","19","20","21","22","23","24"]},
    "V":     {"fr": "Produits minéraux", "en": "Mineral products", "chapters": ["25","26","27"]},
    "VI":    {"fr": "Produits des industries chimiques ou des industries connexes", "en": "Products of the chemical or allied industries", "chapters": ["28","29","30","31","32","33","34","35","36","37","38"]},
    "VII":   {"fr": "Matières plastiques et ouvrages en ces matières; caoutchouc et ouvrages en caoutchouc", "en": "Plastics and articles thereof; rubber and articles thereof", "chapters": ["39","40"]},
    "VIII":  {"fr": "Peaux, cuirs, pelleteries et ouvrages en ces matières", "en": "Raw hides, skins, leather and articles thereof", "chapters": ["41","42","43"]},
    "IX":    {"fr": "Bois, charbon de bois et ouvrages en bois; liège et ouvrages en liège", "en": "Wood and articles of wood; cork and articles of cork", "chapters": ["44","45","46"]},
    "X":     {"fr": "Pâtes de bois; papier ou carton et ouvrages en ces matières", "en": "Pulp of wood; paper or paperboard and articles thereof", "chapters": ["47","48","49"]},
    "XI":    {"fr": "Matières textiles et ouvrages en ces matières", "en": "Textiles and textile articles", "chapters": ["50","51","52","53","54","55","56","57","58","59","60","61","62","63"]},
    "XII":   {"fr": "Chaussures, coiffures, parapluies; fleurs artificielles", "en": "Footwear, headgear, umbrellas; artificial flowers", "chapters": ["64","65","66","67"]},
    "XIII":  {"fr": "Ouvrages en pierres, plâtre, ciment; produits céramiques; verre et ouvrages en verre", "en": "Articles of stone, plaster, cement; ceramic products; glass and glassware", "chapters": ["68","69","70"]},
    "XIV":   {"fr": "Perles fines, pierres gemmes, métaux précieux et ouvrages en ces matières; bijouterie de fantaisie", "en": "Natural or cultured pearls, precious stones, precious metals and articles thereof", "chapters": ["71"]},
    "XV":    {"fr": "Métaux communs et ouvrages en ces métaux", "en": "Base metals and articles of base metal", "chapters": ["72","73","74","75","76","78","79","80","81","82","83"]},
    "XVI":   {"fr": "Machines et appareils, matériel électrique et leurs parties", "en": "Machinery and mechanical appliances; electrical equipment", "chapters": ["84","85"]},
    "XVII":  {"fr": "Matériel de transport", "en": "Vehicles, aircraft, vessels and associated transport equipment", "chapters": ["86","87","88","89"]},
    "XVIII": {"fr": "Instruments et appareils d'optique, de photographie, de mesure; horlogerie; instruments de musique", "en": "Optical, photographic, measuring, medical instruments; clocks; musical instruments", "chapters": ["90","91","92"]},
    "XIX":   {"fr": "Armes, munitions et leurs parties et accessoires", "en": "Arms and ammunition; parts and accessories thereof", "chapters": ["93"]},
    "XX":    {"fr": "Marchandises et produits divers", "en": "Miscellaneous manufactured articles", "chapters": ["94","95","96"]},
    "XXI":   {"fr": "Objets d'art, de collection ou d'antiquité", "en": "Works of art, collectors' pieces and antiques", "chapters": ["97","99"]},
}

_CHAPTER_TO_SECTION = {}
for sec_num, sec_data in HS_SECTIONS.items():
    for ch in sec_data["chapters"]:
        _CHAPTER_TO_SECTION[ch] = sec_num

UTILIZATION_GROUPS = {
    "01": "Élevage", "02": "Alimentation", "03": "Alimentation", "04": "Alimentation",
    "05": "Industrie", "06": "Agriculture", "07": "Alimentation", "08": "Alimentation",
    "09": "Alimentation", "10": "Alimentation", "11": "Alimentation", "12": "Agriculture",
    "13": "Industrie", "14": "Industrie", "15": "Alimentation", "16": "Alimentation",
    "17": "Alimentation", "18": "Alimentation", "19": "Alimentation", "20": "Alimentation",
    "21": "Alimentation", "22": "Alimentation", "23": "Alimentation animale", "24": "Tabac",
    "25": "Industrie", "26": "Industrie", "27": "Énergie", "28": "Industrie chimique",
    "29": "Industrie chimique", "30": "Santé", "31": "Agriculture", "32": "Industrie chimique",
    "33": "Cosmétique", "34": "Industrie chimique", "35": "Industrie chimique",
    "36": "Industrie", "37": "Industrie", "38": "Industrie chimique",
    "39": "Industrie", "40": "Industrie", "41": "Industrie", "42": "Industrie",
    "43": "Industrie", "44": "Industrie", "45": "Industrie", "46": "Industrie",
    "47": "Industrie", "48": "Industrie", "49": "Édition", "50": "Textile",
    "51": "Textile", "52": "Textile", "53": "Textile", "54": "Textile",
    "55": "Textile", "56": "Textile", "57": "Textile", "58": "Textile",
    "59": "Textile", "60": "Textile", "61": "Habillement", "62": "Habillement",
    "63": "Textile", "64": "Habillement", "65": "Habillement", "66": "Divers",
    "67": "Divers", "68": "Construction", "69": "Construction", "70": "Industrie",
    "71": "Bijouterie", "72": "Métallurgie", "73": "Métallurgie", "74": "Métallurgie",
    "75": "Métallurgie", "76": "Métallurgie", "78": "Métallurgie", "79": "Métallurgie",
    "80": "Métallurgie", "81": "Métallurgie", "82": "Outillage", "83": "Métallurgie",
    "84": "Équipement", "85": "Électronique", "86": "Transport", "87": "Transport",
    "88": "Transport", "89": "Transport", "90": "Équipement", "91": "Horlogerie",
    "92": "Divers", "93": "Armement", "94": "Ameublement", "95": "Divers",
    "96": "Divers", "97": "Art", "99": "Divers",
}

_hs4_headings_cache = None

def _load_hs4_headings():
    global _hs4_headings_cache
    if _hs4_headings_cache is not None:
        return _hs4_headings_cache
    data_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'hs4_headings_en.json')
    try:
        with open(data_path, 'r', encoding='utf-8') as f:
            _hs4_headings_cache = json.load(f)
    except FileNotFoundError:
        _hs4_headings_cache = {}
    return _hs4_headings_cache


def get_section_for_chapter(chapter_code: str) -> dict:
    ch = chapter_code.zfill(2)
    sec_num = _CHAPTER_TO_SECTION.get(ch)
    if not sec_num:
        return {"number": "", "fr": "", "en": ""}
    sec = HS_SECTIONS[sec_num]
    return {"number": sec_num, "fr": sec["fr"], "en": sec["en"]}


def get_hs4_heading(hs6_code: str) -> dict:
    hs4 = hs6_code[:4]
    headings = _load_hs4_headings()
    en = headings.get(hs4, "")
    return {"code": hs4, "en": en}


def get_utilization_group(chapter_code: str) -> str:
    return UTILIZATION_GROUPS.get(chapter_code.zfill(2), "Divers")


def get_rangee_number(hs4_code: str) -> str:
    return hs4_code[2:]
