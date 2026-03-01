"""
Adaptateur Algérie (DZA) pour le Moteur Réglementaire AfCFTA v3
===============================================================

Transforme les données tarifaires algériennes au format canonique.
Source: /app/backend/data/DZA_tariffs.json
"""

from typing import Generator, Dict, Any
from datetime import datetime

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from schemas.canonical_model import (
    CommodityCode, Measure, Requirement, FiscalAdvantage,
    CanonicalTariffLine, MeasureType, RequirementType
)
from adapters.base_adapter import BaseAdapter


class DZAAdapter(BaseAdapter):
    """Adaptateur spécifique pour l'Algérie"""
    
    def __init__(self, source_path: str = "/app/backend/data/DZA_tariffs.json"):
        super().__init__("DZA", source_path)
        self._processed_count = 0
        self._sub_position_count = 0
    
    def transform(self) -> Generator[CanonicalTariffLine, None, None]:
        """
        Transforme chaque ligne tarifaire DZA au format canonique.
        Génère une entrée pour chaque sous-position nationale.
        """
        data = self.load_source_data()
        tariff_lines = data.get("tariff_lines", [])
        
        for line in tariff_lines:
            # Traiter les sous-positions si présentes
            sub_positions = line.get("sub_positions", [])
            
            if sub_positions:
                for sub in sub_positions:
                    yield self._transform_sub_position(line, sub)
                    self._sub_position_count += 1
            else:
                # Pas de sous-position, utiliser le code HS6
                yield self._transform_hs6_line(line)
            
            self._processed_count += 1
    
    def _transform_sub_position(self, parent: Dict, sub: Dict) -> CanonicalTariffLine:
        """Transforme une sous-position nationale"""
        national_code = sub.get("code", "")
        hs6 = parent.get("hs6", national_code[:6])
        
        # Créer le CommodityCode
        commodity = CommodityCode(
            country_iso3="DZA",
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
        
        # Créer les mesures
        measures = self._extract_measures(parent, sub)
        
        # Créer les formalités
        requirements = self._extract_requirements(parent, national_code)
        
        # Créer les avantages fiscaux
        fiscal_advantages = self._extract_fiscal_advantages(parent, national_code)
        
        # Calculer les totaux
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
            country_iso3="DZA",
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
        """
        Extrait les mesures tarifaires selon la méthode de calcul algérienne
        (Circulaire 419/DGD/SP/D.420 du 22 mars 2008)
        
        Ordre de calcul :
        1. D.D (Droit de Douane) - sur valeur en douane
        2. Autres taxes (PRCT, T.C.S, D.A.P.S, etc.)
        3. T.V.A - sur (VD + DD + taxes incluses dans l'assiette TVA)
        
        Taxes INCLUSES dans l'assiette TVA : D.D, TIC, TPP, TCLS, DCA, T.Carburants
        Taxes EXCLUES de l'assiette TVA : TAPT, T.Pneus, T.Huiles, TSP, TSV, D.RTA, D.GARANTIE
        """
        measures = []
        national_code = sub.get("code", parent.get("hs6", "")) if sub else parent.get("hs6", "")
        
        # DD (Droit de Douane) - utiliser le taux de la sous-position si disponible
        dd_rate = sub.get("dd", parent.get("dd_rate", 0)) if sub else parent.get("dd_rate", 0)
        measures.append(Measure(
            country_iso3="DZA",
            national_code=national_code,
            measure_type=MeasureType.CUSTOMS_DUTY,
            code="D.D",
            name_fr="Droit de Douane",
            name_en="Customs Duty",
            rate_pct=float(dd_rate or 0),
            is_zlecaf_applicable=True,
            zlecaf_rate_pct=0.0,  # Exonération ZLECAf (AfCFTA Art. 8)
            observation="Base: Valeur en douane (Art. 16 Code des Douanes)"
        ))
        
        # Extraire les autres taxes depuis taxes_detail
        # en respectant les intitulés EXACTS du fichier source
        taxes_detail = parent.get("taxes_detail", [])
        for tax in taxes_detail:
            tax_code = tax.get("tax", "")
            if tax_code.upper().replace(".", "") == "DD":
                continue  # Déjà traité
            
            # Déterminer si la taxe est incluse dans l'assiette TVA
            # Selon Circulaire 419: TVA calculée sur VD + DD + taxes incluses
            taxes_incluses_tva = ["TIC", "TPP", "TCLS", "DCA", "PRCT", "TCS"]
            is_tva = tax_code.upper().replace(".", "") == "TVA"
            is_in_tva_base = any(t in tax_code.upper().replace(".", "") for t in taxes_incluses_tva)
            
            # Note d'observation selon le type de taxe
            if is_tva:
                obs_note = "Base: VD + DD + taxes incluses (Circ. 419)"
            elif is_in_tva_base:
                obs_note = "Inclus dans l'assiette TVA (Circ. 419)"
            else:
                obs_note = "Exclus de l'assiette TVA (Circ. 419)"
            
            measures.append(Measure(
                country_iso3="DZA",
                national_code=national_code,
                measure_type=self.map_measure_type(tax_code),
                code=tax_code,
                name_fr=tax.get("observation", tax_code),  # Intitulé EXACT du fichier source
                name_en=None,
                rate_pct=float(tax.get("rate", 0)),
                is_zlecaf_applicable=False,  # Seul le DD est exonéré sous ZLECAf
                observation=obs_note
            ))
        
        return measures
    
    def _extract_requirements(self, parent: Dict, national_code: str) -> list:
        """Extrait les formalités administratives"""
        requirements = []
        formalities = parent.get("administrative_formalities", [])
        
        for form in formalities:
            code = form.get("code", "")
            doc_fr = form.get("document_fr", "")
            doc_en = form.get("document_en")
            
            requirements.append(Requirement(
                country_iso3="DZA",
                national_code=national_code,
                requirement_type=self.map_requirement_type(code, doc_fr),
                code=code,
                document_fr=doc_fr,
                document_en=doc_en,
                is_mandatory=True,
                issuing_authority=self._get_issuing_authority(code)
            ))
        
        return requirements
    
    def _extract_fiscal_advantages(self, parent: Dict, national_code: str) -> list:
        """Extrait les avantages fiscaux ZLECAf"""
        advantages = []
        fiscal_advs = parent.get("fiscal_advantages", [])
        
        for adv in fiscal_advs:
            advantages.append(FiscalAdvantage(
                country_iso3="DZA",
                national_code=national_code,
                tax_code=adv.get("tax", "D.D"),
                reduced_rate_pct=float(adv.get("rate", 0)),
                condition_fr=adv.get("condition_fr", ""),
                condition_en=adv.get("condition_en")
            ))
        
        return advantages
    
    def _get_issuing_authority(self, code: str) -> str:
        """
        Détermine l'autorité émettrice selon le code de formalité
        Source : Nomenclature des documents douaniers algériens
        """
        authority_map = {
            # Autorisations spéciales (100-199)
            "100": "Direction Générale de la Sûreté Nationale (DGSN) / MDN",
            "101": "Bureau de dépôt",
            "105": "Ministère des Postes et Télécommunications",
            "110": "Administration des Douanes et/ou Administration Fiscale",
            "115": "Ministère de l'Agriculture (Médicaments Vétérinaires)",
            "120": "Ministère de la Santé (Stupéfiants)",
            "130": "Ministère de la Santé (Édulcorants Intenses)",
            "140": "Administration des Impôts Indirects",
            "150": "Service des Impôts Indirects (SNTA)",
            "160": "Ministère de l'Agriculture (Contrôle Sanitaire Vétérinaire)",
            "170": "Autorité du pays d'origine (Herdbook)",
            "180": "Ministère du Commerce (Dérogation Sanitaire)",
            "190": "Conseil Supérieur de l'Information & DGSN",
            "195": "Ministère de la Culture (Beaux Arts)",
            
            # Visas et contrôles (200-299)
            "200": "Présidence du Conseil - Secrétariat Général",
            "210": "Ministère de l'Agriculture (Contrôle Phytosanitaire)",
            "215": "Ministère de l'Agriculture (Certificat Phytosanitaire)",
            "216": "Direction des Services Vétérinaires",
            "220": "Ministère du Commerce - Métrologie Légale",
            "230": "Administration des Impôts Indirects (Garantie)",
            "240": "Ministère de l'Industrie et de l'Énergie",
            
            # Autorisations diverses (300-599)
            "300": "Ministère des Moudjahidines",
            "350": "Directeur de l'établissement",
            "351": "Service concerné du Ministère",
            "356": "Services concernés",
            "400": "Ministère de la Santé (Opium)",
            "500": "Ministère de la Santé (Prohibition)",
            "510": "Administration des Douanes (CKD)",
            
            # Documents commerciaux (600-699)
            "600": "Opérateur économique",
            "610": "Banque domiciliataire",
            "620": "Centre National du Registre du Commerce",
            "625": "Compagnie aérienne",
            "630": "Compagnie d'assurance",
            "635": "Consulat",
            "640": "Déclarant",
            "645": "Déclarant",
            "659": "Organisme de contrôle de conformité",
            "667": "Douane du pays d'origine (EUR.1)",
            "670": "Banque d'Algérie",
            
            # Licences invalides (700-899)
            "700": "Ministère des Moudjahidines",
            "705": "Service des pensions",
            "710": "Service des handicapés",
            "871": "Ministère de la Défense Nationale (MDN)",
            "872": "SONATRACH",
            
            # Documents douaniers spéciaux (900-999)
            "902": "Ministère du Commerce - Inspection du Contrôle aux Frontières",
            "910": "Ministère du Commerce",
            "980": "Service concerné du Ministère (SONATRACH)",
            "983": "Opérateur économique",
        }
        return authority_map.get(code, "Administration douanière DZA")
            "220": "Ministère de la Santé",
        }
        return authority_map.get(code, "Administration douanière DZA")
    
    def get_summary(self) -> Dict[str, Any]:
        """Retourne un résumé des données transformées"""
        data = self.load_source_data()
        summary = data.get("summary", {})
        
        return {
            "country_iso3": "DZA",
            "country_name_fr": "Algérie",
            "country_name_en": "Algeria",
            "adapter_version": "3.0",
            "source_format": data.get("data_format", "unknown"),
            "total_tariff_lines": summary.get("total_tariff_lines", 0),
            "total_sub_positions": summary.get("total_sub_positions", 0),
            "chapters_covered": summary.get("chapters_covered", 0),
            "vat_rate_pct": summary.get("vat_rate_pct", 19.0),
            "dd_rate_range": summary.get("dd_rate_range", {}),
            "has_detailed_taxes": summary.get("has_detailed_taxes", False),
            "processed_count": self._processed_count,
            "sub_position_count": self._sub_position_count
        }
