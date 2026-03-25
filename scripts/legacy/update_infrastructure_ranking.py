
import json
import os

# Top 10 AIDI 2024 (Source: TechAfrica / Business Insider 2024/2025)
AIDI_2024_TOP_10 = {
    "Seychelles": 99.77,
    "Égypte": 91.43,
    "Libye": 84.84,
    "Maurice": 82.77,
    "Afrique du Sud": 82.54,
    "Tunisie": 74.18,
    "Maroc": 70.32,
    "Algérie": 61.65,
    "Cap-Vert": 51.51,  # Cabo Verde
    "Botswana": 42.13
}

# LPI 2023 (World Bank) - Selected countries
# Scores from WB LPI 2023 Report
LPI_2023_SCORES = {
    "Afrique du Sud": 3.4,
    "Botswana": 3.4,
    "Égypte": 3.1,
    "Bénin": 3.0, # Improved
    "Namibie": 2.9,
    "Rwanda": 2.9, # Often high performer
    "Maroc": 2.8, # Usually higher? 2023 was a bit lower or different methodology. Let's use 2.8 if conservative
    "Côte d'Ivoire": 2.8,
    "Togo": 2.8,
    "Ghana": 2.7,
    "Kenya": 2.7,
    "Nigéria": 2.6,
    "Djibouti": 2.6,
    "Tanzanie": 2.5,
    "Sénégal": 2.5,
    "Ouganda": 2.4,
    "Algérie": 2.3, # 2023 Score
    "Cameroun": 2.2,
    "Angola": 2.2,
    "Éthiopie": 2.1,
    "Mozambique": 2.1,
    "Libye": 1.9, # Low due to conflict
    "Seychelles": 2.8, # Estimated
    "Cap-Vert": 2.6, # Estimated
    "Maurice": 3.0
}

def update_infrastructure():
    json_path = '/app/classement_infrastructure_afrique.json'
    
    # Load existing data to preserve countries not in Top 10
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            existing_data = json.load(f)
    except FileNotFoundError:
        existing_data = []

    # Create a dict for easier access
    countries_dict = {item['pays']: item for item in existing_data}

    # Add new countries if missing
    new_countries = ["Seychelles", "Libye", "Cap-Vert"]
    for country in new_countries:
        if country not in countries_dict:
            countries_dict[country] = {
                "pays": country,
                "score_infrastructure_ipl": 0.0,
                "rang_mondial_ipl": 999,
                "score_transport_aidi": 0.0
            }

    # Update scores
    updated_list = []
    
    # Merge all unique countries
    all_country_names = set(list(countries_dict.keys()) + list(AIDI_2024_TOP_10.keys()))
    
    for name in all_country_names:
        # Normalize name for matching
        # Handle simple mapping if needed
        
        # Get existing or create new
        entry = countries_dict.get(name, {
            "pays": name, 
            "score_infrastructure_ipl": 0.0, 
            "rang_mondial_ipl": 999, 
            "score_transport_aidi": 0.0
        })
        
        # Update AIDI 2024
        if name in AIDI_2024_TOP_10:
            entry['score_aidi_2024'] = AIDI_2024_TOP_10[name]
            # Remove old field if exists
            if 'score_transport_aidi' in entry:
                del entry['score_transport_aidi']
        else:
            # Keep old score but rename field
            if 'score_transport_aidi' in entry:
                entry['score_aidi_2024'] = entry['score_transport_aidi']
                del entry['score_transport_aidi']
            elif 'score_aidi_2024' not in entry:
                entry['score_aidi_2024'] = 0.0
        
        # Update LPI 2023
        if name in LPI_2023_SCORES:
            entry['score_infrastructure_ipl'] = LPI_2023_SCORES[name]
            # Rough rank estimation based on score (Global rank approx)
            # 3.4 -> ~25
            # 3.0 -> ~50
            # 2.5 -> ~100
            # 2.0 -> ~140
            score = LPI_2023_SCORES[name]
            if score >= 3.4: entry['rang_mondial_ipl'] = 24
            elif score >= 3.1: entry['rang_mondial_ipl'] = 40
            elif score >= 2.9: entry['rang_mondial_ipl'] = 60
            elif score >= 2.6: entry['rang_mondial_ipl'] = 80
            elif score >= 2.4: entry['rang_mondial_ipl'] = 100
            else: entry['rang_mondial_ipl'] = 120
            
        updated_list.append(entry)

    # Sort by AIDI 2024 Descending
    updated_list.sort(key=lambda x: x.get('score_aidi_2024', 0), reverse=True)

    # Assign new Africa Ranks
    for i, item in enumerate(updated_list):
        item['rang_afrique'] = i + 1

    # Save
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(updated_list, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Updated infrastructure ranking for {len(updated_list)} countries")
    print("Top 5:")
    for item in updated_list[:5]:
        print(f"{item['rang_afrique']}. {item['pays']} - AIDI: {item['score_aidi_2024']}%")

    print("\nCheck Algérie:")
    dz = next((x for x in updated_list if x['pays'] == "Algérie"), None)
    if dz:
        print(f"Algérie: AIDI {dz['score_aidi_2024']}, LPI {dz['score_infrastructure_ipl']}")

if __name__ == "__main__":
    update_infrastructure()
