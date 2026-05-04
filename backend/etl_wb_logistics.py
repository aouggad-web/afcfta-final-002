"""
ETL Module for World Bank Logistics Indicators
Collecte des indicateurs logistiques via World Bank WDI API (sans clé API)
"""
import requests
import json
from typing import Dict, List, Optional
from datetime import datetime

# Mapping des indicateurs logistiques World Bank
LOGISTICS_INDICATORS = {
    'lpi_overall': 'LP.LPI.OVRL.XQ',  # LPI Global Score
    'lpi_infrastructure': 'LP.LPI.INFR.XQ',  # Quality of trade and transport infrastructure
    'lpi_customs': 'LP.LPI.CUST.XQ',  # Efficiency of customs clearance
    'lpi_logistics_quality': 'LP.LPI.LOGS.XQ',  # Competence and quality of logistics services
    'lpi_tracking': 'LP.LPI.TRAC.XQ',  # Ability to track and trace consignments
    'lpi_timeliness': 'LP.LPI.TIME.XQ',  # Timeliness of shipments
    'container_port_traffic': 'IS.SHP.GOOD.TU',  # Container port traffic (TEU)
    'liner_connectivity': 'IS.SHP.LCON.XQ',  # Liner shipping connectivity index
}

# ISO3 codes des pays africains
AFRICAN_COUNTRIES_ISO3 = [
    'DZA', 'AGO', 'BEN', 'BWA', 'BFA', 'BDI', 'CMR', 'CPV', 'CAF', 'TCD',
    'COM', 'COG', 'COD', 'CIV', 'DJI', 'EGY', 'GNQ', 'ERI', 'SWZ', 'ETH',
    'GAB', 'GMB', 'GHA', 'GIN', 'GNB', 'KEN', 'LSO', 'LBR', 'LBY', 'MDG',
    'MWI', 'MLI', 'MRT', 'MUS', 'MAR', 'MOZ', 'NAM', 'NER', 'NGA', 'RWA',
    'STP', 'SEN', 'SYC', 'SLE', 'SOM', 'ZAF', 'SSD', 'SDN', 'TZA', 'TGO',
    'TUN', 'UGA', 'ZMB', 'ZWE'
]

class WorldBankLogisticsCollector:
    """Collecteur de données logistiques depuis World Bank API"""
    
    BASE_URL = "https://api.worldbank.org/v2"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'ZLECAf-Logistics-App/1.0'
        })
    
    def fetch_indicator(self, country_iso3: str, indicator_code: str, 
                        start_year: int = 2015, end_year: int = 2024) -> List[Dict]:
        """
        Récupère un indicateur pour un pays
        
        Args:
            country_iso3: Code ISO3 du pays (ex: DZA)
            indicator_code: Code de l'indicateur WDI (ex: LP.LPI.OVRL.XQ)
            start_year: Année de début
            end_year: Année de fin
            
        Returns:
            Liste des valeurs par année
        """
        url = f"{self.BASE_URL}/country/{country_iso3}/indicator/{indicator_code}"
        params = {
            'format': 'json',
            'per_page': 2000,
            'date': f'{start_year}:{end_year}'
        }
        
        try:
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            # World Bank API retourne [metadata, data]
            if isinstance(data, list) and len(data) > 1:
                return data[1] if data[1] else []
            
            return []
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Error fetching {indicator_code} for {country_iso3}: {e}")
            return []
    
    def fetch_all_logistics_indicators(self, country_iso3: str) -> Dict:
        """
        Récupère tous les indicateurs logistiques pour un pays
        
        Returns:
            Dict avec tous les indicateurs et leurs valeurs historiques
        """
        result = {
            'country_iso3': country_iso3,
            'indicators': {},
            'last_updated': datetime.now().isoformat()
        }
        
        for indicator_name, indicator_code in LOGISTICS_INDICATORS.items():
            print(f"  📊 Fetching {indicator_name} ({indicator_code}) for {country_iso3}...")
            
            data = self.fetch_indicator(country_iso3, indicator_code)
            
            # Transformer en format simplifié
            values = []
            for entry in data:
                if entry.get('value') is not None:
                    values.append({
                        'year': entry.get('date'),
                        'value': entry.get('value')
                    })
            
            result['indicators'][indicator_name] = {
                'code': indicator_code,
                'values': sorted(values, key=lambda x: x['year'], reverse=True)
            }
        
        return result
    
    def collect_all_africa(self, output_file: str = None) -> Dict:
        """
        Collecte tous les indicateurs logistiques pour tous les pays africains
        
        Args:
            output_file: Chemin du fichier JSON de sortie (optionnel)
            
        Returns:
            Dict complet de toutes les données collectées
        """
        print("🌍 Collecting World Bank Logistics Indicators for Africa...")
        print(f"📍 Countries: {len(AFRICAN_COUNTRIES_ISO3)}")
        print(f"📊 Indicators: {len(LOGISTICS_INDICATORS)}")
        print("=" * 70)
        
        all_data = {
            'metadata': {
                'source': 'World Bank WDI API',
                'collection_date': datetime.now().isoformat(),
                'countries_count': len(AFRICAN_COUNTRIES_ISO3),
                'indicators_count': len(LOGISTICS_INDICATORS)
            },
            'countries': {}
        }
        
        for i, country_iso3 in enumerate(AFRICAN_COUNTRIES_ISO3, 1):
            print(f"\n[{i}/{len(AFRICAN_COUNTRIES_ISO3)}] 🏴 {country_iso3}")
            
            country_data = self.fetch_all_logistics_indicators(country_iso3)
            all_data['countries'][country_iso3] = country_data
        
        print("\n" + "=" * 70)
        print("✅ Collection completed!")
        
        # Sauvegarder si demandé
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(all_data, f, indent=2, ensure_ascii=False)
            print(f"💾 Data saved to: {output_file}")
        
        return all_data


def main():
    """Script principal pour collecter les données"""
    collector = WorldBankLogisticsCollector()
    
    # Collecter toutes les données pour l'Afrique
    data = collector.collect_all_africa(
        output_file='/app/wb_logistics_africa.json'
    )
    
    # Afficher un résumé
    print("\n📈 Summary:")
    for country_iso3, country_data in data['countries'].items():
        lpi_data = country_data['indicators'].get('lpi_overall', {}).get('values', [])
        if lpi_data:
            latest = lpi_data[0]
            print(f"  {country_iso3}: LPI {latest['value']:.2f} ({latest['year']})")


if __name__ == "__main__":
    main()
