
import csv
from backend.server import AFRICAN_COUNTRIES

def check_missing_countries():
    # Get all 54 ISO codes
    all_isos = set(c['iso3'] for c in AFRICAN_COUNTRIES)
    
    # Get ISOs in CSV
    csv_isos = set()
    try:
        with open('/app/ZLECAf_ENRICHI_2024_COMMERCE.csv', 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                csv_isos.add(row['Code_ISO'])
    except Exception as e:
        print(f"Error reading CSV: {e}")
        return

    missing = all_isos - csv_isos
    print(f"Total defined countries: {len(all_isos)}")
    print(f"Countries in CSV: {len(csv_isos)}")
    print(f"Missing countries ({len(missing)}): {missing}")

if __name__ == "__main__":
    check_missing_countries()
