"""
Adaptateur de base pour la transformation de données tarifaires
"""

from abc import ABC, abstractmethod
from typing import Generator, Dict, Any
import json
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from schemas.canonical_model import (
    CommodityCode, Measure, Requirement, FiscalAdvantage,
    CanonicalTariffLine, MeasureType, RequirementType
)


class BaseAdapter(ABC):
    """Classe de base pour tous les adaptateurs pays"""
    
    def __init__(self, country_iso3: str, source_path: str):
        self.country_iso3 = country_iso3.upper()
        self.source_path = Path(source_path)
        self._data = None
        
    def load_source_data(self) -> Dict[str, Any]:
        """Charge les données source du fichier JSON"""
        if self._data is None:
            with open(self.source_path, 'r', encoding='utf-8') as f:
                self._data = json.load(f)
        return self._data
    
    @abstractmethod
    def transform(self) -> Generator[CanonicalTariffLine, None, None]:
        """
        Transforme les données source au format canonique.
        Retourne un générateur de CanonicalTariffLine.
        """
        pass
    
    @abstractmethod
    def get_summary(self) -> Dict[str, Any]:
        """Retourne un résumé des données transformées"""
        pass
    
    def map_measure_type(self, tax_code: str) -> MeasureType:
        """Mappe un code de taxe au type de mesure canonique"""
        tax_code_upper = tax_code.upper().replace(".", "").replace(" ", "")
        
        mapping = {
            "DD": MeasureType.CUSTOMS_DUTY,
            "DROIT": MeasureType.CUSTOMS_DUTY,
            "TVA": MeasureType.VAT,
            "EXCISE": MeasureType.EXCISE,
            "PRCT": MeasureType.LEVY,
            "TCS": MeasureType.OTHER_TAX,
            "CEDEAO": MeasureType.LEVY,
            "CISS": MeasureType.LEVY,
            "TPI": MeasureType.LEVY,
            "AIR": MeasureType.OTHER_TAX,
        }
        
        for key, value in mapping.items():
            if key in tax_code_upper:
                return value
        
        return MeasureType.OTHER_TAX
    
    def map_requirement_type(self, code: str, document: str) -> RequirementType:
        """Mappe un code de formalité au type canonique"""
        doc_lower = document.lower()
        
        if "certificat" in doc_lower:
            return RequirementType.CERTIFICATE
        elif "licence" in doc_lower or "license" in doc_lower:
            return RequirementType.LICENSE
        elif "autorisation" in doc_lower or "authorization" in doc_lower:
            return RequirementType.AUTHORIZATION
        elif "inspection" in doc_lower:
            return RequirementType.INSPECTION
        elif "déclaration" in doc_lower or "declaration" in doc_lower:
            return RequirementType.IMPORT_DECLARATION
        elif "permis" in doc_lower or "permit" in doc_lower:
            return RequirementType.PERMIT
        
        return RequirementType.CERTIFICATE
    
    def calculate_totals(self, measures: list, fiscal_advantages: list) -> tuple:
        """Calcule les totaux NPF et ZLECAf"""
        total_npf = sum(m.rate_pct for m in measures)
        
        # Pour ZLECAf, appliquer les avantages fiscaux
        total_zlecaf = total_npf
        for advantage in fiscal_advantages:
            # Trouver la mesure correspondante et soustraire la différence
            for m in measures:
                if m.code.replace(".", "").replace(" ", "").upper() == \
                   advantage.tax_code.replace(".", "").replace(" ", "").upper():
                    total_zlecaf -= (m.rate_pct - advantage.reduced_rate_pct)
                    break
        
        savings = total_npf - total_zlecaf if total_npf > 0 else 0
        
        return total_npf, total_zlecaf, savings
