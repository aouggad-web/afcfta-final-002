"""
Script ETL pour importer les codes HS6 depuis le fichier CSV officiel SH2022
et générer le fichier Python de la base de données complète.
"""

import csv
import re
from collections import defaultdict

# Catégories par chapitre HS
CHAPTER_CATEGORIES = {
    "01": "live_animals", "02": "meat", "03": "fish", "04": "dairy",
    "05": "animal_products", "06": "plants", "07": "vegetables", "08": "fruits",
    "09": "coffee_tea_spices", "10": "cereals", "11": "milling", "12": "oilseeds",
    "13": "lac_gums", "14": "vegetable_materials", "15": "fats_oils",
    "16": "meat_preparations", "17": "sugar", "18": "cocoa", "19": "cereal_preparations",
    "20": "vegetable_preparations", "21": "misc_food", "22": "beverages",
    "23": "food_residues", "24": "tobacco", "25": "salt_stone", "26": "ores",
    "27": "mineral_fuels", "28": "inorganic_chemicals", "29": "organic_chemicals",
    "30": "pharmaceuticals", "31": "fertilizers", "32": "tanning_dyes",
    "33": "essential_oils_cosmetics", "34": "soap_wax", "35": "proteins_glues",
    "36": "explosives", "37": "photography", "38": "chemicals_misc",
    "39": "plastics", "40": "rubber", "41": "raw_hides", "42": "leather_goods",
    "43": "furs", "44": "wood", "45": "cork", "46": "basketry",
    "47": "wood_pulp", "48": "paper", "49": "printed_matter",
    "50": "silk", "51": "wool", "52": "cotton", "53": "vegetable_fibers",
    "54": "man_made_filaments", "55": "man_made_staple", "56": "wadding_felt",
    "57": "carpets", "58": "special_fabrics", "59": "coated_fabrics",
    "60": "knitted_fabrics", "61": "knitted_apparel", "62": "woven_apparel",
    "63": "textile_articles", "64": "footwear", "65": "headgear",
    "66": "umbrellas", "67": "feathers", "68": "stone_articles",
    "69": "ceramics", "70": "glass", "71": "jewelry",
    "72": "iron_steel", "73": "iron_steel_articles", "74": "copper",
    "75": "nickel", "76": "aluminum", "78": "lead", "79": "zinc",
    "80": "tin", "81": "other_metals", "82": "tools", "83": "metal_misc",
    "84": "machinery", "85": "electrical", "86": "railway",
    "87": "vehicles", "88": "aircraft", "89": "ships",
    "90": "optical_medical", "91": "clocks", "92": "musical_instruments",
    "93": "arms", "94": "furniture", "95": "toys", "96": "misc_manufactured",
    "97": "art"
}

# Sensibilité par chapitre (approximatif selon ZLECAf)
SENSITIVE_CHAPTERS = {"01", "02", "04", "10", "11", "15", "17", "22", "24", "50", "51", "52", "61", "62", "64"}
EXCLUDED_CHAPTERS = {"36", "93"}

def clean_text(text):
    """Nettoie le texte des caractères spéciaux"""
    if not text:
        return ""
    text = text.strip().strip('"')
    text = re.sub(r'\s+', ' ', text)
    return text

def get_category(chapter):
    """Retourne la catégorie pour un chapitre"""
    return CHAPTER_CATEGORIES.get(chapter, "other")

def get_sensitivity(chapter):
    """Retourne la sensibilité pour un chapitre"""
    if chapter in EXCLUDED_CHAPTERS:
        return "excluded"
    if chapter in SENSITIVE_CHAPTERS:
        return "sensitive"
    return "normal"

def parse_csv_line(line):
    """Parse une ligne du CSV avec le séparateur ;"""
    # Le format est: "Chapitre;Desc FR;Desc EN;Code;Desc Produit FR;Desc Produit EN;Statut"
    parts = line.split(';')
    if len(parts) >= 6:
        return {
            'chapter': clean_text(parts[0]),
            'chapter_desc_fr': clean_text(parts[1]),
            'chapter_desc_en': clean_text(parts[2]),
            'code': clean_text(parts[3]),
            'desc_fr': clean_text(parts[4]),
            'desc_en': clean_text(parts[5]),
            'status': clean_text(parts[6]) if len(parts) > 6 else ''
        }
    return None

def import_csv(filepath):
    """Importe le CSV et retourne un dictionnaire de codes HS6"""
    hs6_data = {}
    
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    for i, line in enumerate(lines):
        if i == 0:  # Skip header
            continue
            
        # Nettoyer la ligne
        line = line.strip().strip('"')
        if not line:
            continue
            
        data = parse_csv_line(line)
        if not data:
            continue
            
        code = data['code']
        
        # Filtrer les codes invalides (chapitre 00 = codes spéciaux)
        if not code or len(code) != 6 or code.startswith('00'):
            continue
            
        # Filtrer les codes sans description
        if not data['desc_fr'] and not data['desc_en']:
            continue
            
        chapter = code[:2]
        
        # Créer l'entrée
        hs6_data[code] = {
            "chapter": chapter,
            "description_fr": data['desc_fr'] or data['desc_en'],
            "description_en": data['desc_en'] or data['desc_fr'],
            "category": get_category(chapter),
            "sensitivity": get_sensitivity(chapter),
            "has_sub_positions": True,
            "typical_sub_position_types": ["type"],
            "rule_of_origin": {
                "type": "substantial_transformation",
                "requirement_fr": "Transformation substantielle en Afrique",
                "requirement_en": "Substantial transformation in Africa",
                "regional_content": 40
            }
        }
    
    return hs6_data

def generate_python_file(hs6_data, output_path):
    """Génère le fichier Python avec la base de données complète"""
    
    # Trier par code
    sorted_codes = sorted(hs6_data.keys())
    
    # Compter par chapitre
    chapter_counts = defaultdict(int)
    for code in sorted_codes:
        chapter_counts[code[:2]] += 1
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('"""\n')
        f.write('BASE DE DONNÉES HS6 COMPLÈTE - Générée depuis SH2022 officiel\n')
        f.write(f'Total: {len(sorted_codes)} codes HS6\n')
        f.write(f'Chapitres couverts: {len(chapter_counts)}\n')
        f.write('"""\n\n')
        f.write('HS6_CSV_DATABASE = {\n')
        
        for code in sorted_codes:
            entry = hs6_data[code]
            f.write(f'    "{code}": {{\n')
            f.write(f'        "chapter": "{entry["chapter"]}",\n')
            
            # Escape quotes in descriptions
            desc_fr = entry["description_fr"].replace('"', '\\"')
            desc_en = entry["description_en"].replace('"', '\\"')
            
            f.write(f'        "description_fr": "{desc_fr}",\n')
            f.write(f'        "description_en": "{desc_en}",\n')
            f.write(f'        "category": "{entry["category"]}",\n')
            f.write(f'        "sensitivity": "{entry["sensitivity"]}",\n')
            f.write(f'        "has_sub_positions": {entry["has_sub_positions"]},\n')
            f.write(f'        "typical_sub_position_types": {entry["typical_sub_position_types"]},\n')
            f.write(f'        "rule_of_origin": {entry["rule_of_origin"]}\n')
            f.write('    },\n')
        
        f.write('}\n')
    
    return len(sorted_codes), dict(chapter_counts)

if __name__ == "__main__":
    import sys
    
    csv_path = "/app/backend/etl/codes_sh6_complet.csv"
    output_path = "/app/backend/etl/hs6_csv_database.py"
    
    print(f"Importation de {csv_path}...")
    hs6_data = import_csv(csv_path)
    
    print(f"Génération de {output_path}...")
    total, chapters = generate_python_file(hs6_data, output_path)
    
    print(f"\n=== RÉSULTAT ===")
    print(f"Total codes HS6: {total}")
    print(f"Chapitres couverts: {len(chapters)}")
    print("\nCodes par chapitre:")
    for ch in sorted(chapters.keys()):
        print(f"  Chapitre {ch}: {chapters[ch]} codes")
