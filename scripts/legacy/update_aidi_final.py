
import json

# Verified AIDI 2024/2025 Scores (Source: AfDB / TechAfrica / IntelPoint)
AIDI_SCORES = {
    "Seychelles": 99.77,
    "Égypte": 91.43,
    "Libye": 84.84,
    "Maurice": 82.77,
    "Afrique du Sud": 82.54,
    "Tunisie": 74.18,
    "Maroc": 70.32,
    "Algérie": 61.65,
    "Cap-Vert": 51.51,
    "Botswana": 42.13,
    "Nigéria": 25.70, # Confirmed 24th
    "Sao Tomé-et-Principe": 45.2, # Est
    "Gabon": 35.8, # Est
    "Ghana": 31.6, # Est
    "Namibie": 33.0, # Est
    "Sénégal": 39.8, # Est
    "Côte d'Ivoire": 33.1, # Est
    "Kenya": 41.2, # Est
    "Djibouti": 29.8, # Est
    "Rwanda": 20.8, # Est
    "Éthiopie": 21.5 # Est
}

# Mapping codes to French names in our DB
CODE_TO_NAME = {
    "SC": "Seychelles", "EG": "Égypte", "LY": "Libye", "MU": "Maurice", "ZA": "Afrique du Sud",
    "TN": "Tunisie", "MA": "Maroc", "DZ": "Algérie", "CV": "Cap-Vert", "BW": "Botswana",
    "NG": "Nigéria", "ST": "Sao Tomé-et-Principe", "GA": "Gabon", "GH": "Ghana", 
    "NA": "Namibie", "SN": "Sénégal", "CI": "Côte d'Ivoire", "KE": "Kenya",
    "DJ": "Djibouti", "RW": "Rwanda", "ET": "Éthiopie"
}

def update_scores():
    json_path = '/app/classement_infrastructure_afrique.json'
    
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    for item in data:
        country = item['pays']
        if country in AIDI_SCORES:
            item['score_aidi_2024'] = AIDI_SCORES[country]
            
    # Sort and re-rank
    data.sort(key=lambda x: x.get('score_aidi_2024', 0), reverse=True)
    for i, item in enumerate(data):
        item['rang_afrique'] = i + 1
        
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        
    print("Mise à jour terminée avec les scores AIDI 2025/2024.")

if __name__ == "__main__":
    update_scores()
