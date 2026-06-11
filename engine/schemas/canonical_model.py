"""
Modèles canoniques pour le Moteur Réglementaire AfCFTA — Schéma v4
==================================================================

v4 ajoute trois capacités au schéma v3 (rétrocompatible) :

1. PROVENANCE : chaque ligne porte son statut (VERIFIED / PARTIAL / SYNTHETIC),
   sa note de fiabilité (A/B/C/D), sa source et sa date de version.
   Les données générées par template DOIVENT être marquées SYNTHETIC.

2. ASSIETTE STRUCTURÉE : chaque mesure déclare formellement sa base de calcul
   (CIF, FOB, valeur en douane, assiette cumulée, quantité) au lieu d'une
   note en texte libre — le calcul devient déterministe et auditable.

3. SÉQUENCE D'APPLICATION : ordre d'application des droits et taxes
   (ex. Algérie : DD sur CAF -> TCS/PRCT sur CAF -> TVA sur CAF+DD+TCS+PRCT).

Tous les nouveaux champs sont optionnels avec valeurs par défaut :
les fichiers JSONL v3 restent lisibles sans migration de code.
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime, date
from enum import Enum

SCHEMA_VERSION = "4.0"


# ============================================================
# Énumérations
# ============================================================

class MeasureType(str, Enum):
    """Types de mesures tarifaires"""
    CUSTOMS_DUTY = "CUSTOMS_DUTY"
    VAT = "VAT"
    EXCISE = "EXCISE"
    LEVY = "LEVY"
    OTHER_TAX = "OTHER_TAX"
    SAFEGUARD = "SAFEGUARD"        # v4 : ex. DAPS (Algérie), mesures de sauvegarde
    ANTI_DUMPING = "ANTI_DUMPING"  # v4


class RequirementType(str, Enum):
    """Types de formalités administratives"""
    IMPORT_DECLARATION = "IMPORT_DECLARATION"
    CERTIFICATE = "CERTIFICATE"
    LICENSE = "LICENSE"
    PERMIT = "PERMIT"
    INSPECTION = "INSPECTION"
    AUTHORIZATION = "AUTHORIZATION"
    VISA = "VISA"                  # v4 : ex. visa de contrôle sanitaire vétérinaire
    DEROGATION = "DEROGATION"      # v4 : ex. dérogation sanitaire


class DataStatus(str, Enum):
    """Statut d'authenticité de la donnée — OBLIGATOIRE à afficher côté UI"""
    VERIFIED = "VERIFIED"    # Collectée depuis une source officielle et vérifiée
    PARTIAL = "PARTIAL"      # Partiellement vérifiée (ex. taux vérifiés, formalités non)
    SYNTHETIC = "SYNTHETIC"  # Générée par template/IA — NE JAMAIS présenter comme réelle


class ReliabilityGrade(str, Enum):
    """Note de fiabilité de la source (aligné sur le Business Atlas)"""
    A = "A"  # Source officielle primaire (douane nationale, journal officiel, TEC publié)
    B = "B"  # Source institutionnelle secondaire (OMC, ITC MacMap, CNUCED TRAINS)
    C = "C"  # Source tierce non institutionnelle, à recouper
    D = "D"  # Donnée générée, estimée ou non sourcée


class RateType(str, Enum):
    """Nature du taux"""
    AD_VALOREM = "AD_VALOREM"  # % de l'assiette
    SPECIFIC = "SPECIFIC"      # montant par unité (ex. 50 DZD/kg)
    MIXED = "MIXED"            # combinaison (ex. 10% + 5 EGP/unité)
    EXEMPT = "EXEMPT"          # exonéré


class DutyBasis(str, Enum):
    """Assiette de calcul de la mesure"""
    CIF = "CIF"                          # Valeur CAF (coût + assurance + fret)
    FOB = "FOB"                          # Valeur FOB
    CUSTOMS_VALUE = "CUSTOMS_VALUE"      # Valeur en douane (si distincte du CAF)
    CIF_PLUS_INCLUDED = "CIF_PLUS_INCLUDED"  # CAF + montants des mesures listées
                                             # dans basis_includes (ex. TVA Algérie)
    QUANTITY = "QUANTITY"                # Quantité physique (droits spécifiques)
    OTHER = "OTHER"                      # Préciser dans basis_note


# ============================================================
# Provenance (v4)
# ============================================================

class Provenance(BaseModel):
    """Traçabilité obligatoire de chaque ligne tarifaire"""
    data_status: DataStatus = Field(DataStatus.SYNTHETIC,
        description="VERIFIED / PARTIAL / SYNTHETIC")
    reliability: ReliabilityGrade = Field(ReliabilityGrade.D,
        description="Note de fiabilité A/B/C/D")
    source_name: Optional[str] = Field(None,
        description="Nom de la source (ex: 'DGD Algérie — Tarif intégré')")
    source_url: Optional[str] = Field(None,
        description="URL de la source officielle")
    source_document: Optional[str] = Field(None,
        description="Document précis (ex: 'LF 2026, art. 12' ou 'EAC CET 2022')")
    version_date: Optional[date] = Field(None,
        description="Date de version du tarif source (millésime)")
    retrieved_at: Optional[datetime] = Field(None,
        description="Date/heure de collecte")
    notes: Optional[str] = Field(None,
        description="Remarques (méthode de collecte, limites connues)")


# ============================================================
# Modèles principaux
# ============================================================

class CommodityCode(BaseModel):
    """Code marchandise canonique (ligne tarifaire)"""
    country_iso3: str = Field(..., description="Code ISO3 du pays (ex: DZA)")
    national_code: str = Field(..., description="Code tarifaire national complet")
    hs6: str = Field(..., description="Code HS6 de base")
    digits: int = Field(..., description="Nombre de digits du code national (8/10/12)")
    description_fr: str = Field(..., description="Description en français")
    description_en: Optional[str] = Field(None, description="Description en anglais")
    chapter: str = Field(..., description="Chapitre HS (2 digits)")
    category: Optional[str] = Field(None, description="Catégorie du produit")
    unit: Optional[str] = Field(None, description="Unité de mesure statistique")
    sensitivity: str = Field("normal", description="Niveau de sensibilité ZLECAf")
    hs_version: Optional[str] = Field(None,
        description="v4 — Version SH de la nomenclature (ex: 'HS2022')")
    description_official_fr: Optional[str] = Field(None,
        description="v4 — Libellé officiel exact du tarif national (non reformulé)")


class Measure(BaseModel):
    """Mesure tarifaire (droit, taxe, prélèvement)"""
    country_iso3: str = Field(..., description="Code ISO3 du pays")
    national_code: str = Field(..., description="Code tarifaire national")
    measure_type: MeasureType = Field(..., description="Type de mesure")
    code: str = Field(..., description="Code de la taxe (ex: D.D, T.V.A)")
    name_fr: str = Field(..., description="Intitulé officiel en français")
    name_en: Optional[str] = Field(None, description="Intitulé officiel en anglais")
    rate_pct: Optional[float] = Field(None,
        description="Taux ad valorem en % (None si purement spécifique)")
    is_zlecaf_applicable: bool = Field(False, description="Démantelée sous ZLECAf")
    zlecaf_rate_pct: Optional[float] = Field(None, description="Taux préférentiel ZLECAf")
    observation: Optional[str] = Field(None, description="Notes/observations")

    # ---- v4 : méthode de calcul structurée ----
    rate_type: RateType = Field(RateType.AD_VALOREM,
        description="AD_VALOREM / SPECIFIC / MIXED / EXEMPT")
    specific_amount: Optional[float] = Field(None,
        description="Montant du droit spécifique (si SPECIFIC ou MIXED)")
    specific_unit: Optional[str] = Field(None,
        description="Unité du droit spécifique (ex: 'DZD/kg', 'EGP/unité')")
    basis: DutyBasis = Field(DutyBasis.CIF,
        description="Assiette de calcul")
    basis_includes: List[str] = Field(default_factory=list,
        description="Si basis=CIF_PLUS_INCLUDED : codes des mesures dont le montant "
                    "s'ajoute à l'assiette (ex: ['D.D','T.C.S','PRCT'] pour la TVA DZA)")
    basis_note: Optional[str] = Field(None,
        description="Précision sur l'assiette si basis=OTHER")
    sequence: int = Field(100,
        description="Ordre d'application (10=DD, 20-80=taxes intermédiaires, 90=TVA)")
    legal_reference: Optional[str] = Field(None,
        description="Base légale (ex: 'Art. 16 Code des Douanes', 'Circ. 419 DGD')")


class Requirement(BaseModel):
    """Formalité administrative requise"""
    country_iso3: str = Field(..., description="Code ISO3 du pays")
    national_code: str = Field(..., description="Code tarifaire national")
    requirement_type: RequirementType = Field(..., description="Type de formalité")
    code: str = Field(..., description="Code de la formalité")
    document_fr: str = Field(..., description="Dénomination exacte du document (FR)")
    document_en: Optional[str] = Field(None, description="Dénomination exacte (EN)")
    is_mandatory: bool = Field(True, description="Obligatoire ou optionnel")
    issuing_authority: Optional[str] = Field(None,
        description="Autorité qui délivre le document (dénomination complète)")

    # ---- v4 ----
    issuing_authority_code: Optional[str] = Field(None,
        description="Sigle de l'autorité (ex: 'ONSSA', 'NAFDAC', 'DGD')")
    applies_to: str = Field("IMPORT", description="IMPORT / EXPORT / BOTH")
    legal_reference: Optional[str] = Field(None,
        description="Base légale de l'exigence")
    when_required: Optional[str] = Field(None,
        description="Condition de déclenchement si non systématique "
                    "(ex: 'si produit d'origine animale')")


class FiscalAdvantage(BaseModel):
    """Avantage fiscal (ZLECAf ou autre accord préférentiel)"""
    country_iso3: str = Field(..., description="Code ISO3 du pays")
    national_code: str = Field(..., description="Code tarifaire national")
    tax_code: str = Field(..., description="Code de la taxe concernée")
    reduced_rate_pct: float = Field(..., description="Taux réduit")
    condition_fr: str = Field(..., description="Condition d'application (FR)")
    condition_en: Optional[str] = Field(None, description="Condition d'application (EN)")
    agreement: Optional[str] = Field(None,
        description="v4 — Accord concerné (ex: 'ZLECAf', 'ZALE', 'UE-Maroc')")
    required_document: Optional[str] = Field(None,
        description="v4 — Document exigé (ex: 'Certificat d'origine ZLECAf')")


class CanonicalTariffLine(BaseModel):
    """Ligne tarifaire complète canonique — agrégation pour l'API"""
    commodity: CommodityCode
    measures: List[Measure] = Field(default_factory=list)
    requirements: List[Requirement] = Field(default_factory=list)
    fiscal_advantages: List[FiscalAdvantage] = Field(default_factory=list)

    # Champs calculés
    total_npf_pct: float = Field(0.0, description="Total taxes NPF (indicatif ad valorem)")
    total_zlecaf_pct: float = Field(0.0, description="Total taxes ZLECAf (indicatif)")
    savings_pct: float = Field(0.0, description="Économie ZLECAf en %")

    # Métadonnées
    source_file: Optional[str] = Field(None)
    last_updated: Optional[datetime] = Field(None)

    # ---- v4 ----
    schema_version: str = Field(SCHEMA_VERSION)
    provenance: Provenance = Field(default_factory=Provenance,
        description="Traçabilité — défaut SYNTHETIC/D tant que non vérifié")


class RegulatoryEngineResponse(BaseModel):
    """Réponse de l'API Moteur Réglementaire"""
    success: bool
    country_iso3: str
    national_code: str
    hs6: str
    data: Optional[CanonicalTariffLine] = None
    error: Optional[str] = None
    processing_time_ms: Optional[float] = None
    data_status: Optional[DataStatus] = Field(None,
        description="v4 — Statut remonté en tête de réponse pour l'UI")
    disclaimer: Optional[str] = Field(None,
        description="v4 — Mention légale obligatoire si SYNTHETIC/PARTIAL")


class IndexEntry(BaseModel):
    """Entrée d'index pour recherche rapide"""
    national_code: str
    hs6: str
    chapter: str
    file_offset: int = Field(..., description="Position dans le fichier JSONL")
    line_number: int = Field(..., description="Numéro de ligne")


# Mention légale standard (à servir avec toute donnée non VERIFIED)
LEGAL_DISCLAIMER_FR = (
    "Donnée indicative non vérifiée. Seuls les taux et formalités publiés dans la "
    "législation nationale du pays importateur et les Listes de concessions "
    "tarifaires ZLECAf officielles font foi."
)
