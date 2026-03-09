"""
Service API pour le Moteur Réglementaire AfCFTA v3
==================================================

Expose les données canoniques via une API haute performance.
"""

import json
import time
from pathlib import Path
from typing import Dict, Any, Optional, List
from functools import lru_cache

import sys

# Use append (not insert) to avoid shadowing the backend 'api' package
# which takes higher priority when placed earlier in sys.path.
_engine_root = str(Path(__file__).parent.parent)
if _engine_root not in sys.path:
    sys.path.append(_engine_root)

from schemas.canonical_model import (
    CanonicalTariffLine, RegulatoryEngineResponse, CommodityCode,
    Measure, Requirement, FiscalAdvantage
)


class RegulatoryEngineService:
    """
    Service pour interroger les données canoniques du Moteur Réglementaire.
    Utilise les index pré-construits pour des recherches O(1).
    """
    
    def __init__(self, data_dir: str = "/app/engine/output"):
        self.data_dir = Path(data_dir)
        self._indexes = {}
        self._country_files = {}
        self._load_indexes()
    
    def _load_indexes(self):
        """Charge tous les index disponibles en mémoire"""
        index_dir = self.data_dir / "indexes"
        if not index_dir.exists():
            return
        
        # Charger l'index des pays
        countries_path = index_dir / "countries_index.json"
        if countries_path.exists():
            with open(countries_path, 'r', encoding='utf-8') as f:
                self._indexes["countries"] = json.load(f)
        
        # Charger les index par pays
        for iso3 in self._indexes.get("countries", {}).get("available_countries", []):
            nat_index_path = index_dir / f"{iso3}_index_national.json"
            hs6_index_path = index_dir / f"{iso3}_index_hs6.json"
            
            if nat_index_path.exists():
                with open(nat_index_path, 'r', encoding='utf-8') as f:
                    self._indexes[f"{iso3}_national"] = json.load(f)
            
            if hs6_index_path.exists():
                with open(hs6_index_path, 'r', encoding='utf-8') as f:
                    self._indexes[f"{iso3}_hs6"] = json.load(f)
            
            # Stocker le chemin du fichier JSONL
            jsonl_path = self.data_dir / f"{iso3}_canonical.jsonl"
            if jsonl_path.exists():
                self._country_files[iso3] = jsonl_path
    
    def get_available_countries(self) -> List[str]:
        """Retourne la liste des pays disponibles"""
        return self._indexes.get("countries", {}).get("available_countries", [])
    
    def get_by_national_code(
        self,
        country_iso3: str,
        national_code: str
    ) -> RegulatoryEngineResponse:
        """
        Recherche par code national exact.
        Performance: O(1) grâce à l'index.
        """
        start_time = time.time()
        country_iso3 = country_iso3.upper()
        
        # Vérifier si le pays est disponible
        if country_iso3 not in self._country_files:
            return RegulatoryEngineResponse(
                success=False,
                country_iso3=country_iso3,
                national_code=national_code,
                hs6=national_code[:6] if len(national_code) >= 6 else national_code,
                error=f"Pays {country_iso3} non disponible"
            )
        
        # Chercher dans l'index national
        index_key = f"{country_iso3}_national"
        if index_key not in self._indexes:
            return RegulatoryEngineResponse(
                success=False,
                country_iso3=country_iso3,
                national_code=national_code,
                hs6=national_code[:6] if len(national_code) >= 6 else national_code,
                error="Index national non disponible"
            )
        
        national_index = self._indexes[index_key]
        if national_code not in national_index:
            return RegulatoryEngineResponse(
                success=False,
                country_iso3=country_iso3,
                national_code=national_code,
                hs6=national_code[:6] if len(national_code) >= 6 else national_code,
                error=f"Code {national_code} non trouvé"
            )
        
        # Récupérer le numéro de ligne
        line_info = national_index[national_code]
        line_num = line_info["line"]
        
        # Lire la ligne spécifique du fichier JSONL
        record = self._read_line(country_iso3, line_num)
        
        if record is None:
            return RegulatoryEngineResponse(
                success=False,
                country_iso3=country_iso3,
                national_code=national_code,
                hs6=line_info.get("hs6", national_code[:6]),
                error="Erreur de lecture des données"
            )
        
        processing_time = (time.time() - start_time) * 1000
        
        return RegulatoryEngineResponse(
            success=True,
            country_iso3=country_iso3,
            national_code=national_code,
            hs6=record.commodity.hs6,
            data=record,
            processing_time_ms=round(processing_time, 2)
        )
    
    def get_by_hs6(
        self,
        country_iso3: str,
        hs6: str
    ) -> List[RegulatoryEngineResponse]:
        """
        Recherche par code HS6.
        Retourne toutes les sous-positions nationales correspondantes.
        """
        start_time = time.time()
        country_iso3 = country_iso3.upper()
        
        # Vérifier si le pays est disponible
        if country_iso3 not in self._country_files:
            return [RegulatoryEngineResponse(
                success=False,
                country_iso3=country_iso3,
                national_code=hs6,
                hs6=hs6,
                error=f"Pays {country_iso3} non disponible"
            )]
        
        # Chercher dans l'index HS6
        index_key = f"{country_iso3}_hs6"
        if index_key not in self._indexes:
            return [RegulatoryEngineResponse(
                success=False,
                country_iso3=country_iso3,
                national_code=hs6,
                hs6=hs6,
                error="Index HS6 non disponible"
            )]
        
        hs6_index = self._indexes[index_key]
        if hs6 not in hs6_index:
            return [RegulatoryEngineResponse(
                success=False,
                country_iso3=country_iso3,
                national_code=hs6,
                hs6=hs6,
                error=f"HS6 {hs6} non trouvé"
            )]
        
        results = []
        for line_num in hs6_index[hs6]:
            # Support pour l'ancien et le nouveau format d'index
            if isinstance(line_num, dict):
                actual_line = line_num.get("line", line_num)
                national_code = line_num.get("national_code", "")
            else:
                actual_line = line_num
                national_code = ""
            
            record = self._read_line(country_iso3, actual_line)
            if record:
                processing_time = (time.time() - start_time) * 1000
                # Extraire le code national du record si pas dans l'index
                if not national_code and record.commodity:
                    national_code = record.commodity.national_code
                results.append(RegulatoryEngineResponse(
                    success=True,
                    country_iso3=country_iso3,
                    national_code=national_code,
                    hs6=hs6,
                    data=record,
                    processing_time_ms=round(processing_time, 2)
                ))
        
        return results
    
    def _read_line(self, country_iso3: str, line_num: int) -> Optional[CanonicalTariffLine]:
        """Lit une ligne spécifique du fichier JSONL"""
        jsonl_path = self._country_files.get(country_iso3)
        if not jsonl_path:
            return None
        
        try:
            with open(jsonl_path, 'r', encoding='utf-8') as f:
                for i, line in enumerate(f):
                    if i == line_num:
                        data = json.loads(line)
                        return self._parse_record(data)
            return None
        except Exception as e:
            print(f"Erreur lecture ligne {line_num}: {e}")
            return None
    
    def _parse_record(self, data: Dict) -> CanonicalTariffLine:
        """Parse un enregistrement JSON en CanonicalTariffLine"""
        commodity_data = data.get("commodity", {})
        commodity = CommodityCode(**commodity_data)
        
        measures = [Measure(**m) for m in data.get("measures", [])]
        requirements = [Requirement(**r) for r in data.get("requirements", [])]
        fiscal_advantages = [FiscalAdvantage(**fa) for fa in data.get("fiscal_advantages", [])]
        
        return CanonicalTariffLine(
            commodity=commodity,
            measures=measures,
            requirements=requirements,
            fiscal_advantages=fiscal_advantages,
            total_npf_pct=data.get("total_npf_pct", 0),
            total_zlecaf_pct=data.get("total_zlecaf_pct", 0),
            savings_pct=data.get("savings_pct", 0),
            source_file=data.get("source_file"),
            last_updated=data.get("last_updated")
        )
    
    def get_country_summary(self, country_iso3: str) -> Optional[Dict[str, Any]]:
        """Retourne le résumé d'un pays"""
        summary_path = self.data_dir / f"{country_iso3.upper()}_summary.json"
        if summary_path.exists():
            with open(summary_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return None


# Instance singleton
_service_instance = None

def get_service() -> RegulatoryEngineService:
    """Retourne l'instance singleton du service"""
    global _service_instance
    if _service_instance is None:
        _service_instance = RegulatoryEngineService()
    return _service_instance
