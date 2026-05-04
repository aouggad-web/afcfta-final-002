"""
Modèles canoniques pour le Moteur Réglementaire AfCFTA v3
=========================================================

Ces modèles définissent le format standardisé pour toutes les données
tarifaires et réglementaires des 54+ pays africains.
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from enum import Enum


class MeasureType(str, Enum):
    """Types de mesures tarifaires"""
    CUSTOMS_DUTY = "CUSTOMS_DUTY"
    VAT = "VAT"
    EXCISE = "EXCISE"
    LEVY = "LEVY"
    OTHER_TAX = "OTHER_TAX"


class RequirementType(str, Enum):
    """Types de formalités administratives"""
    IMPORT_DECLARATION = "IMPORT_DECLARATION"
    CERTIFICATE = "CERTIFICATE"
    LICENSE = "LICENSE"
    PERMIT = "PERMIT"
    INSPECTION = "INSPECTION"
    AUTHORIZATION = "AUTHORIZATION"


class CommodityCode(BaseModel):
    """Code marchandise canonique (ligne tarifaire)"""
    country_iso3: str = Field(..., description="Code ISO3 du pays (ex: DZA)")
    national_code: str = Field(..., description="Code tarifaire national complet")
    hs6: str = Field(..., description="Code HS6 de base")
    digits: int = Field(..., description="Nombre de digits du code national")
    description_fr: str = Field(..., description="Description en français")
    description_en: Optional[str] = Field(None, description="Description en anglais")
    chapter: str = Field(..., description="Chapitre HS (2 digits)")
    category: Optional[str] = Field(None, description="Catégorie du produit")
    unit: Optional[str] = Field(None, description="Unité de mesure")
    sensitivity: str = Field("normal", description="Niveau de sensibilité ZLECAf")


class Measure(BaseModel):
    """Mesure tarifaire (droit, taxe)"""
    country_iso3: str = Field(..., description="Code ISO3 du pays")
    national_code: str = Field(..., description="Code tarifaire national")
    measure_type: MeasureType = Field(..., description="Type de mesure")
    code: str = Field(..., description="Code de la taxe (ex: D.D, T.V.A)")
    name_fr: str = Field(..., description="Nom complet en français")
    name_en: Optional[str] = Field(None, description="Nom complet en anglais")
    rate_pct: float = Field(..., description="Taux en pourcentage")
    is_zlecaf_applicable: bool = Field(False, description="Applicable sous ZLECAf")
    zlecaf_rate_pct: Optional[float] = Field(None, description="Taux ZLECAf si différent")
    observation: Optional[str] = Field(None, description="Notes/observations")


class Requirement(BaseModel):
    """Formalité administrative requise"""
    country_iso3: str = Field(..., description="Code ISO3 du pays")
    national_code: str = Field(..., description="Code tarifaire national")
    requirement_type: RequirementType = Field(..., description="Type de formalité")
    code: str = Field(..., description="Code de la formalité")
    document_fr: str = Field(..., description="Nom du document en français")
    document_en: Optional[str] = Field(None, description="Nom du document en anglais")
    is_mandatory: bool = Field(True, description="Obligatoire ou optionnel")
    issuing_authority: Optional[str] = Field(None, description="Autorité émettrice")


class FiscalAdvantage(BaseModel):
    """Avantage fiscal ZLECAf"""
    country_iso3: str = Field(..., description="Code ISO3 du pays")
    national_code: str = Field(..., description="Code tarifaire national")
    tax_code: str = Field(..., description="Code de la taxe concernée")
    reduced_rate_pct: float = Field(..., description="Taux réduit")
    condition_fr: str = Field(..., description="Condition d'application en français")
    condition_en: Optional[str] = Field(None, description="Condition d'application en anglais")


class CanonicalTariffLine(BaseModel):
    """Ligne tarifaire complète canonique - agrégation pour l'API"""
    commodity: CommodityCode
    measures: List[Measure] = Field(default_factory=list)
    requirements: List[Requirement] = Field(default_factory=list)
    fiscal_advantages: List[FiscalAdvantage] = Field(default_factory=list)
    
    # Champs calculés
    total_npf_pct: float = Field(0.0, description="Total taxes NPF")
    total_zlecaf_pct: float = Field(0.0, description="Total taxes ZLECAf")
    savings_pct: float = Field(0.0, description="Économie ZLECAf en %")
    
    # Métadonnées
    source_file: Optional[str] = Field(None)
    last_updated: Optional[datetime] = Field(None)


class RegulatoryEngineResponse(BaseModel):
    """Réponse de l'API Moteur Réglementaire"""
    success: bool
    country_iso3: str
    national_code: str
    hs6: str
    data: Optional[CanonicalTariffLine] = None
    error: Optional[str] = None
    processing_time_ms: Optional[float] = None


class IndexEntry(BaseModel):
    """Entrée d'index pour recherche rapide"""
    national_code: str
    hs6: str
    chapter: str
    file_offset: int = Field(..., description="Position dans le fichier JSONL")
    line_number: int = Field(..., description="Numéro de ligne")
