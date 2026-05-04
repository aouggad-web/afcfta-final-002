"""
Adaptateur Générique pour le Moteur Réglementaire AfCFTA v3
===========================================================

Adaptateur universel pour tous les pays utilisant le format enhanced_v2.
Fonctionne pour : MAR, EGY, NGA, ZAF, KEN, CIV, GHA et tout autre pays.
"""

from typing import Generator, Dict, Any, Optional
from datetime import datetime
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from schemas.canonical_model import (
    CommodityCode, Measure, Requirement, FiscalAdvantage,
    CanonicalTariffLine, MeasureType, RequirementType
)
from adapters.base_adapter import BaseAdapter


# Configuration spécifique par pays
COUNTRY_CONFIG = {
    "MAR": {
        "name_fr": "Maroc",
        "currency": "MAD",
        "tax_authority": "ADII",  # Administration des Douanes et Impôts Indirects
        "vat_authority": "DGI Maroc",
        "issuing_authorities": {
            "910": "ADII - Douanes du Maroc",
            "C004": "ONSSA - Office National de Sécurité Sanitaire",
            "C017": "Ministère du Commerce et de l'Industrie",
            "Y929": "ONSSA - Office National de Sécurité Sanitaire",
            "L001": "Ministère de l'Agriculture",
            "N002": "Ministère du Commerce",
        }
    },
    "EGY": {
        "name_fr": "Égypte",
        "currency": "EGP",
        "tax_authority": "ECA",  # Egyptian Customs Authority
        "vat_authority": "ETA Égypte",
        "issuing_authorities": {
            "910": "ECA - Autorité Douanière Égyptienne",
            "C004": "GOEIC - Org. Contrôle Import/Export",
            "C017": "Ministère du Commerce Égyptien",
            "Y929": "NFSA - Autorité Sécurité Alimentaire",
            "L001": "Ministère de l'Agriculture",
        }
    },
    "NGA": {
        "name_fr": "Nigeria",
        "currency": "NGN",
        "tax_authority": "NCS",  # Nigeria Customs Service
        "vat_authority": "FIRS Nigeria",
        "issuing_authorities": {
            "910": "NCS - Nigeria Customs Service",
            "C004": "NAFDAC - Agence Alimentaire et Médicaments",
            "C017": "SON - Standards Organization of Nigeria",
            "Y929": "NAFDAC - Agence Alimentaire et Médicaments",
            "L001": "Federal Ministry of Agriculture",
            "N002": "Federal Ministry of Trade",
        }
    },
    "ZAF": {
        "name_fr": "Afrique du Sud",
        "currency": "ZAR",
        "tax_authority": "SARS",  # South African Revenue Service
        "vat_authority": "SARS Afrique du Sud",
        "issuing_authorities": {
            "910": "SARS - South African Revenue Service",
            "C004": "DALRRD - Dept. Agriculture",
            "C017": "ITAC - International Trade Administration",
            "Y929": "DOH - Department of Health",
            "L001": "DALRRD - Dept. Agriculture",
            "N002": "dtic - Dept. Commerce et Industrie",
        }
    },
    "KEN": {
        "name_fr": "Kenya",
        "currency": "KES",
        "tax_authority": "KRA",  # Kenya Revenue Authority
        "vat_authority": "KRA Kenya",
        "issuing_authorities": {
            "910": "KRA - Kenya Revenue Authority",
            "C004": "KEPHIS - Service Phytosanitaire",
            "C017": "KEBS - Bureau des Standards",
            "Y929": "KEBS - Bureau des Standards",
            "L001": "Ministry of Agriculture",
            "N002": "Ministry of Trade",
        }
    },
    "CIV": {
        "name_fr": "Côte d'Ivoire",
        "currency": "XOF",
        "tax_authority": "DGD",  # Direction Générale des Douanes
        "vat_authority": "DGI Côte d'Ivoire",
        "issuing_authorities": {
            "910": "DGD - Direction Générale des Douanes",
            "C004": "LANADA - Laboratoire National",
            "C017": "Ministère du Commerce",
            "Y929": "Ministère de la Santé",
            "L001": "Ministère de l'Agriculture",
            "N002": "Guichet Unique du Commerce",
            "PL": "CEDEAO - Prélèvement Communautaire",
        }
    },
    "GHA": {
        "name_fr": "Ghana",
        "currency": "GHS",
        "tax_authority": "GRA",  # Ghana Revenue Authority
        "vat_authority": "GRA Ghana",
        "issuing_authorities": {
            "910": "GRA - Ghana Revenue Authority",
            "C004": "FDA - Food and Drugs Authority",
            "C017": "GSA - Ghana Standards Authority",
            "Y929": "FDA - Food and Drugs Authority",
            "L001": "Ministry of Food and Agriculture",
            "N002": "GFZA - Free Zones Authority",
        }
    }
}


class GenericAdapter(BaseAdapter):
    """Adaptateur générique pour tous les pays format enhanced_v2"""
    
    def __init__(self, country_iso3: str, source_path: str = None):
        if source_path is None:
            source_path = f"/app/backend/data/tariffs/{country_iso3}_tariffs.json"
        
        super().__init__(country_iso3, source_path)
        self.config = COUNTRY_CONFIG.get(country_iso3, {})
        self._processed_count = 0
        self._sub_position_count = 0
    
    def transform(self) -> Generator[CanonicalTariffLine, None, None]:
        """Transforme chaque ligne tarifaire au format canonique"""
        data = self.load_source_data()
        tariff_lines = data.get("tariff_lines", [])
        
        for line in tariff_lines:
            sub_positions = line.get("sub_positions", [])
            
            if sub_positions:
                for sub in sub_positions:
                    yield self._transform_sub_position(line, sub)
                    self._sub_position_count += 1
            else:
                yield self._transform_hs6_line(line)
            
            self._processed_count += 1
    
    def _transform_sub_position(self, parent: Dict, sub: Dict) -> CanonicalTariffLine:
        """Transforme une sous-position nationale"""
        national_code = sub.get("code", "")
        hs6 = parent.get("hs6", national_code[:6])
        
        commodity = CommodityCode(
            country_iso3=self.country_iso3,
            national_code=national_code,
            hs6=hs6,
            digits=sub.get("digits", len(national_code)),
            description_fr=sub.get("description_fr", parent.get("description_fr", "")),
            description_en=sub.get("description_en", parent.get("description_en")),
            chapter=hs6[:2],
            category=parent.get("category"),
            unit=parent.get("unit"),
            sensitivity=parent.get("sensitivity", "normal")
        )
        
        measures = self._extract_measures(parent, sub)
        requirements = self._extract_requirements(parent, national_code)
        fiscal_advantages = self._extract_fiscal_advantages(parent, national_code)
        
        total_npf, total_zlecaf, savings = self.calculate_totals(measures, fiscal_advantages)
        
        return CanonicalTariffLine(
            commodity=commodity,
            measures=measures,
            requirements=requirements,
            fiscal_advantages=fiscal_advantages,
            total_npf_pct=total_npf,
            total_zlecaf_pct=total_zlecaf,
            savings_pct=savings,
            source_file=str(self.source_path),
            last_updated=datetime.now()
        )
    
    def _transform_hs6_line(self, line: Dict) -> CanonicalTariffLine:
        """Transforme une ligne HS6 sans sous-position"""
        hs6 = line.get("hs6", "")
        
        commodity = CommodityCode(
            country_iso3=self.country_iso3,
            national_code=hs6,
            hs6=hs6,
            digits=6,
            description_fr=line.get("description_fr", ""),
            description_en=line.get("description_en"),
            chapter=hs6[:2],
            category=line.get("category"),
            unit=line.get("unit"),
            sensitivity=line.get("sensitivity", "normal")
        )
        
        measures = self._extract_measures(line, None)
        requirements = self._extract_requirements(line, hs6)
        fiscal_advantages = self._extract_fiscal_advantages(line, hs6)
        
        total_npf, total_zlecaf, savings = self.calculate_totals(measures, fiscal_advantages)
        
        return CanonicalTariffLine(
            commodity=commodity,
            measures=measures,
            requirements=requirements,
            fiscal_advantages=fiscal_advantages,
            total_npf_pct=total_npf,
            total_zlecaf_pct=total_zlecaf,
            savings_pct=savings,
            source_file=str(self.source_path),
            last_updated=datetime.now()
        )
    
    def _extract_measures(self, parent: Dict, sub: Dict = None) -> list:
        """Extrait les mesures tarifaires"""
        measures = []
        national_code = sub.get("code", parent.get("hs6", "")) if sub else parent.get("hs6", "")
        
        # DD (Droit de Douane)
        dd_rate = sub.get("dd", parent.get("dd_rate", 0)) if sub else parent.get("dd_rate", 0)
        measures.append(Measure(
            country_iso3=self.country_iso3,
            national_code=national_code,
            measure_type=MeasureType.CUSTOMS_DUTY,
            code="D.D",
            name_fr="Droit de Douane",
            name_en="Customs Duty",
            rate_pct=dd_rate,
            is_zlecaf_applicable=True,
            zlecaf_rate_pct=0.0,  # Exonération DD sous ZLECAf
            observation=f"Tarif national {self.country_iso3}"
        ))
        
        # Taxes détaillées si disponibles
        taxes_detail = parent.get("taxes_detail", [])
        for tax in taxes_detail:
            tax_code = tax.get("tax", "")
            if tax_code.upper().replace(".", "").replace(" ", "") in ["DD", "DROIT"]:
                continue  # Déjà ajouté
            
            # TVA
            if "TVA" in tax_code.upper():
                measures.append(Measure(
                    country_iso3=self.country_iso3,
                    national_code=national_code,
                    measure_type=MeasureType.VAT,
                    code=tax_code,
                    name_fr="Taxe sur la Valeur Ajoutée",
                    name_en="Value Added Tax",
                    rate_pct=tax.get("rate", parent.get("vat_rate", 0)),
                    is_zlecaf_applicable=False,
                    observation=tax.get("observation", "")
                ))
            else:
                # Autres taxes
                measure_type = self.map_measure_type(tax_code)
                measures.append(Measure(
                    country_iso3=self.country_iso3,
                    national_code=national_code,
                    measure_type=measure_type,
                    code=tax_code,
                    name_fr=tax.get("observation", tax_code),
                    name_en=tax.get("observation_en"),
                    rate_pct=tax.get("rate", 0),
                    is_zlecaf_applicable=False,
                    observation=tax.get("observation", "")
                ))
        
        # Si pas de taxes détaillées, ajouter TVA depuis les champs principaux
        if not taxes_detail and parent.get("vat_rate", 0) > 0:
            measures.append(Measure(
                country_iso3=self.country_iso3,
                national_code=national_code,
                measure_type=MeasureType.VAT,
                code="T.V.A",
                name_fr="Taxe sur la Valeur Ajoutée",
                name_en="Value Added Tax",
                rate_pct=parent.get("vat_rate", 0),
                is_zlecaf_applicable=False,
                observation=self.config.get("vat_authority", "")
            ))
        
        # Autres taxes agrégées si présentes
        other_taxes_rate = parent.get("other_taxes_rate", 0)
        if other_taxes_rate > 0 and not any(t.get("tax") not in ["D.D", "T.V.A"] for t in taxes_detail):
            measures.append(Measure(
                country_iso3=self.country_iso3,
                national_code=national_code,
                measure_type=MeasureType.OTHER_TAX,
                code="AUTRES",
                name_fr="Autres taxes et prélèvements",
                name_en="Other taxes and levies",
                rate_pct=other_taxes_rate,
                is_zlecaf_applicable=False,
                observation=""
            ))
        
        return measures
    
    def _extract_requirements(self, parent: Dict, national_code: str) -> list:
        """Extrait les formalités administratives"""
        requirements = []
        formalities = parent.get("administrative_formalities", [])
        
        # Autorités par défaut
        default_authorities = self.config.get("issuing_authorities", {})
        
        for form in formalities:
            code = form.get("code", "")
            doc_fr = form.get("document_fr", "")
            doc_en = form.get("document_en", "")
            
            # Déterminer l'autorité émettrice
            authority = default_authorities.get(code, self.config.get("tax_authority", f"Autorité {self.country_iso3}"))
            
            req_type = self.map_requirement_type(code, doc_fr)
            
            requirements.append(Requirement(
                country_iso3=self.country_iso3,
                national_code=national_code,
                requirement_type=req_type,
                code=code,
                document_fr=doc_fr,
                document_en=doc_en,
                is_mandatory=True,
                issuing_authority=authority
            ))
        
        return requirements
    
    def _extract_fiscal_advantages(self, parent: Dict, national_code: str) -> list:
        """Extrait les avantages fiscaux ZLECAf"""
        advantages = []
        fiscal_adv = parent.get("fiscal_advantages", [])
        
        for adv in fiscal_adv:
            advantages.append(FiscalAdvantage(
                country_iso3=self.country_iso3,
                national_code=national_code,
                tax_code=adv.get("tax", "D.D"),
                reduced_rate_pct=adv.get("rate", 0),
                condition_fr=adv.get("condition_fr", "Exonération ZLECAf"),
                condition_en=adv.get("condition_en", "AfCFTA Exemption")
            ))
        
        # Ajouter l'avantage DD si pas déjà présent
        if not any(a.tax_code.upper().replace(".", "") == "DD" for a in advantages):
            advantages.append(FiscalAdvantage(
                country_iso3=self.country_iso3,
                national_code=national_code,
                tax_code="D.D",
                reduced_rate_pct=0,
                condition_fr="Certificat d'Origine ZLECAf - Exonération Droits de Douane",
                condition_en="AfCFTA Certificate of Origin - Customs Duty Exemption"
            ))
        
        return advantages
    
    def get_summary(self) -> Dict[str, Any]:
        """Retourne un résumé des données transformées"""
        data = self.load_source_data()
        summary = data.get("summary", {})
        
        return {
            "country_iso3": self.country_iso3,
            "country_name": self.config.get("name_fr", self.country_iso3),
            "processed_lines": self._processed_count,
            "sub_positions": self._sub_position_count,
            "total_positions": summary.get("total_positions", 0),
            "chapters_covered": summary.get("chapters_covered", 0),
            "vat_rate": summary.get("vat_rate_pct", 0),
            "dd_range": summary.get("dd_rate_range", {}),
            "data_format": data.get("data_format", "enhanced_v2")
        }


# Factory pour créer des adaptateurs par pays
def create_adapter(country_iso3: str, source_path: str = None) -> GenericAdapter:
    """Crée un adaptateur pour le pays spécifié"""
    return GenericAdapter(country_iso3, source_path)
