"""
ETL Pipeline - Ports Africains
==============================
Expert Senior en Stratégie Maritime et Opérationnelle

Pipeline d'automatisation pour la mise à jour des données portuaires depuis:
- World Bank (LPI, CPPI)
- UNCTAD (Review of Maritime Transport)
- WCO (Time Release Studies)
- FAO/FAOSTAT (données agricoles export)
- Sources nationales (Autorités portuaires)

Auteur: Expert Maritime ZLECAf
Date: 2025
"""

import json
import os
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
import logging

# Configuration logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Chemins
ROOT_DIR = Path(__file__).parent.parent.parent
PORTS_FILE = ROOT_DIR / 'data' / 'json' / 'ports_africains.json'
ETL_LOG_FILE = ROOT_DIR / 'backend' / 'etl' / 'etl_log.json'

# Import des données TRS officielles
from .trs_official_data import TRS_OFFICIAL_DATA, LPI_2023_DATA, GLOBAL_BENCHMARKS


class PortsETL:
    """
    Pipeline ETL pour les données portuaires africaines.
    
    Principes:
    - AUCUNE estimation - uniquement données officielles
    - Traçabilité complète (source, date, année)
    - "NA" si donnée non disponible
    """
    
    def __init__(self):
        self.ports = self._load_ports()
        self.etl_log = []
        
    def _load_ports(self) -> List[Dict]:
        """Charge les données portuaires existantes."""
        try:
            with open(PORTS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error(f"Fichier ports non trouvé: {PORTS_FILE}")
            return []
    
    def _save_ports(self):
        """Sauvegarde les données portuaires."""
        with open(PORTS_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.ports, f, ensure_ascii=False, indent=2)
        logger.info(f"✅ Données sauvegardées: {PORTS_FILE}")
    
    def _log_update(self, port_id: str, field: str, old_value: Any, new_value: Any, source: str):
        """Enregistre une mise à jour dans le log ETL."""
        self.etl_log.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "port_id": port_id,
            "field": field,
            "old_value": old_value,
            "new_value": new_value,
            "source": source
        })
    
    def _save_etl_log(self):
        """Sauvegarde le log ETL."""
        ETL_LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        
        # Charger le log existant
        existing_log = []
        if ETL_LOG_FILE.exists():
            with open(ETL_LOG_FILE, 'r', encoding='utf-8') as f:
                existing_log = json.load(f)
        
        # Ajouter les nouvelles entrées
        existing_log.extend(self.etl_log)
        
        with open(ETL_LOG_FILE, 'w', encoding='utf-8') as f:
            json.dump(existing_log, f, ensure_ascii=False, indent=2)
        
        logger.info(f"📋 Log ETL mis à jour: {len(self.etl_log)} entrées")
    
    def update_trs_data(self):
        """
        Met à jour les données TRS (Time Release Study) avec les données officielles et fiables.
        
        RÈGLE: Données officielles prioritaires. Sources fiables avec avertissement si non-officielles.
        """
        logger.info("🚀 Mise à jour des données TRS...")
        updated_count = 0
        na_count = 0
        
        for port in self.ports:
            port_id = port.get('port_id')
            
            # Récupérer les données TRS
            trs_data = TRS_OFFICIAL_DATA.get(port_id)
            
            # Construire la nouvelle structure TRS
            new_trs = {
                "container_dwell_time_days": "NA",
                "source": "NA",
                "source_type": "NO_DATA",
                "source_reliability_level": 99,
                "data_year": "NA",
                "methodology": "NA",
                "publication_date": "NA",
                "notes": "Aucune étude TRS (Time Release Study) disponible pour ce port.",
                "vessel_turnaround_hours": "NA",
                "customs_clearance_hours": "NA",
                "warning": None,
                "last_updated": datetime.now(timezone.utc).strftime("%Y-%m-%d")
            }
            
            if trs_data:
                # Mettre à jour avec les données disponibles
                for key in trs_data.keys():
                    new_trs[key] = trs_data[key]
                
                # Ajouter les informations de fiabilité
                from .trs_official_data import get_source_reliability
                source_info = get_source_reliability(trs_data.get('source_type', 'NO_DATA'))
                new_trs['source_reliability_level'] = source_info['level']
                new_trs['source_reliability_label'] = source_info['label']
                
                # Avertissement de la source si non-officielle
                if source_info.get('warning') and not new_trs.get('warning'):
                    new_trs['warning'] = source_info['warning']
                
                if new_trs['container_dwell_time_days'] != "NA":
                    updated_count += 1
                else:
                    na_count += 1
            else:
                na_count += 1
            
            # Log de la mise à jour
            old_trs = port.get('trs_analysis', {})
            self._log_update(
                port_id, 
                'trs_analysis', 
                old_trs.get('container_dwell_time_days', 'N/A'),
                new_trs['container_dwell_time_days'],
                new_trs['source']
            )
            
            # Remplacer l'ancien TRS
            port['trs_analysis'] = new_trs
            
            # Supprimer l'ancien champ wco_trs_modeled si présent
            if 'wco_trs_modeled' in port:
                del port['wco_trs_modeled']
        
        logger.info(f"✅ TRS mis à jour: {updated_count} ports avec données")
        logger.info(f"⚠️ TRS = NA: {na_count} ports sans données")
        
        return updated_count, na_count
    
    def update_lpi_data(self):
        """
        Met à jour les données LPI (Logistics Performance Index) 2023.
        """
        logger.info("🚀 Mise à jour des données LPI...")
        updated_count = 0
        
        for port in self.ports:
            country_iso = port.get('country_iso')
            lpi_data = LPI_2023_DATA.get(country_iso)
            
            if lpi_data:
                port['lpi_2023'] = {
                    "overall_score": lpi_data.get('overall', 'NA'),
                    "customs_score": lpi_data.get('customs', 'NA'),
                    "timeliness_score": lpi_data.get('timeliness', 'NA'),
                    "world_rank": lpi_data.get('rank', 'NA'),
                    "source": "World Bank LPI 2023",
                    "year": 2023
                }
                updated_count += 1
        
        logger.info(f"✅ LPI 2023 mis à jour: {updated_count} ports")
        return updated_count
    
    def add_global_benchmarks(self):
        """
        Ajoute les benchmarks globaux UNCTAD pour comparaison.
        """
        for port in self.ports:
            port['global_benchmarks'] = {
                "africa_avg_dwell_days": GLOBAL_BENCHMARKS['container_dwell_time_days_africa_avg'],
                "africa_avg_source": GLOBAL_BENCHMARKS['container_dwell_time_days_africa_avg_source'],
                "africa_avg_note": GLOBAL_BENCHMARKS['container_dwell_time_days_afdb_note'],
                "global_median_dwell_days_h2_2023": GLOBAL_BENCHMARKS['container_dwell_time_days_global_median_h2_2023'],
                "source": GLOBAL_BENCHMARKS['source']
            }
    
    def run_full_etl(self):
        """
        Exécute le pipeline ETL complet.
        """
        logger.info("=" * 60)
        logger.info("🔄 DÉMARRAGE PIPELINE ETL - PORTS AFRICAINS")
        logger.info("=" * 60)
        
        start_time = datetime.now(timezone.utc)
        
        # 1. Mise à jour TRS
        trs_updated, trs_na = self.update_trs_data()
        
        # 2. Mise à jour LPI
        lpi_updated = self.update_lpi_data()
        
        # 3. Ajout benchmarks
        self.add_global_benchmarks()
        
        # 4. Sauvegarde
        self._save_ports()
        self._save_etl_log()
        
        end_time = datetime.now(timezone.utc)
        duration = (end_time - start_time).total_seconds()
        
        logger.info("=" * 60)
        logger.info("✅ PIPELINE ETL TERMINÉ")
        logger.info(f"   Durée: {duration:.2f} secondes")
        logger.info(f"   Ports TRS avec données: {trs_updated}")
        logger.info(f"   Ports TRS = NA: {trs_na}")
        logger.info(f"   Ports LPI mis à jour: {lpi_updated}")
        logger.info("=" * 60)
        
        return {
            "status": "success",
            "duration_seconds": duration,
            "trs_updated": trs_updated,
            "trs_na": trs_na,
            "lpi_updated": lpi_updated,
            "timestamp": end_time.isoformat()
        }


def run_etl():
    """Point d'entrée pour exécuter le pipeline ETL."""
    etl = PortsETL()
    return etl.run_full_etl()


if __name__ == "__main__":
    run_etl()
