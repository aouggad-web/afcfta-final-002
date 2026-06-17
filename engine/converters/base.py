"""
Utilitaires partagés entre les convertisseurs.

Principes :
  - Zéro normalisation des intitulés : les libellés officiels sont copiés tels quels
    dans name_fr / document_fr.
  - La classification (MeasureType, RequirementType) est la seule opération
    d'interprétation — elle est basée sur des mots-clés exhaustifs.
  - La traçabilité (Provenance) est fixée par convertisseur, pas par ligne.
"""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Generator, Optional

sys.path.insert(0, str(Path(__file__).parent.parent))

from schemas.canonical_model import (
    CanonicalTariffLine, CommodityCode, DutyBasis, FiscalAdvantage,
    Measure, MeasureType, Provenance, RateType, Requirement,
    RequirementType, SCHEMA_VERSION,
)

# ------------------------------------------------------------------
# Constantes
# ------------------------------------------------------------------

CRAWLED_DIR = Path(__file__).parent.parent.parent / "backend" / "data" / "crawled"
OUTPUT_DIR  = Path(__file__).parent.parent / "output"


# ------------------------------------------------------------------
# Normalisation des codes HS
# ------------------------------------------------------------------

def clean_hs(code: str) -> str:
    """Supprime les points/tirets d'un code HS."""
    return re.sub(r"[.\-\s]", "", str(code))


def hs6_from_code(code: str) -> str:
    """Extrait le HS6 depuis n'importe quelle longueur de code."""
    c = clean_hs(code)
    return c[:6] if len(c) >= 6 else c.zfill(6)


def digits_from_code(code: str) -> int:
    return len(clean_hs(code))


# ------------------------------------------------------------------
# Classification des mesures tarifaires
# ------------------------------------------------------------------

_DUTY_KEYWORDS = re.compile(
    r"droit.*(douane|import|customs?)|customs?\s+duty|import\s+duty|"
    r"\bDD\b|\bD\.D\b|\bID\b|\bDI\b|\bDDROIT\b|droit.*(import|intégr)",
    re.IGNORECASE,
)
_VAT_KEYWORDS = re.compile(
    r"\bT\.?V\.?A\.?\b|\bVAT\b|\bIVA\b|\btaxe.*valeur\s+ajout|value.added",
    re.IGNORECASE,
)
_EXCISE_KEYWORDS = re.compile(
    r"excis|accis|taxe.*(alcool|tabac|boisson|pétrole|carburant)|"
    r"droit.*(accis|excis|\balcool\b|\btabac\b)",
    re.IGNORECASE,
)
_LEVY_KEYWORDS = re.compile(
    r"prélève|redevance|communautaire|statistique|solidarit|intégrat|"
    r"railway|IDF|infrastructure|development\s+levy|RDL|PCS|PCC|PUA|RS\b|TCI\b",
    re.IGNORECASE,
)
_SAFEGUARD_KEYWORDS = re.compile(
    r"sauvegarde|DAPS|safeguard|anti.?dump|compensat",
    re.IGNORECASE,
)


def classify_measure(code: str, name: str) -> MeasureType:
    """
    Déduit le MeasureType à partir du code et du libellé officiel.
    Ne modifie pas le libellé — classification uniquement.
    """
    text = f"{code} {name}"
    if _VAT_KEYWORDS.search(text):
        return MeasureType.VAT
    if _EXCISE_KEYWORDS.search(text):
        return MeasureType.EXCISE
    if _SAFEGUARD_KEYWORDS.search(text):
        return MeasureType.SAFEGUARD
    if _LEVY_KEYWORDS.search(text):
        return MeasureType.LEVY
    if _DUTY_KEYWORDS.search(text):
        return MeasureType.CUSTOMS_DUTY
    return MeasureType.OTHER_TAX


# ------------------------------------------------------------------
# Classification des formalités administratives
# ------------------------------------------------------------------

_CERT_KW  = re.compile(r"certificat|certificate|conformit|phyto|sanit|zoo", re.IGNORECASE)
_LIC_KW   = re.compile(r"licen[sc]e|autorisation\s+d'import|import\s+licen", re.IGNORECASE)
_PERMIT_KW = re.compile(r"\bpermis\b|permit\b|agrément\b", re.IGNORECASE)
_INSP_KW  = re.compile(r"inspect|contr.le|visite|analyse|test\b", re.IGNORECASE)
_AUTH_KW  = re.compile(r"autorisation|approbation|accord\s+préalable|موافقة", re.IGNORECASE)
_VISA_KW  = re.compile(r"\bvisa\b", re.IGNORECASE)
_DERO_KW  = re.compile(r"déroga|dérogat", re.IGNORECASE)
_DECL_KW  = re.compile(r"déclaration|declaration", re.IGNORECASE)


def classify_requirement(text: str) -> RequirementType:
    """Déduit le type de formalité depuis le libellé exact (sans modifier le texte)."""
    if _DERO_KW.search(text):
        return RequirementType.DEROGATION
    if _VISA_KW.search(text):
        return RequirementType.VISA
    if _CERT_KW.search(text):
        return RequirementType.CERTIFICATE
    if _LIC_KW.search(text):
        return RequirementType.LICENSE
    if _PERMIT_KW.search(text):
        return RequirementType.PERMIT
    if _INSP_KW.search(text):
        return RequirementType.INSPECTION
    if _AUTH_KW.search(text):
        return RequirementType.AUTHORIZATION
    if _DECL_KW.search(text):
        return RequirementType.IMPORT_DECLARATION
    return RequirementType.AUTHORIZATION


# ------------------------------------------------------------------
# Extraction d'autorités depuis les libellés
# ------------------------------------------------------------------

_AUTHORITY_MAP = [
    (re.compile(r"m\.\s*agric|min.*(agric|élev|plant|vétéri)", re.IGNORECASE),
     ("Ministère de l'Agriculture", "M_AGRI")),
    (re.compile(r"min.*(santé|hygièn|health)", re.IGNORECASE),
     ("Ministère de la Santé", "M_SANTE")),
    (re.compile(r"min.*(comm|trade|échange|industri)", re.IGNORECASE),
     ("Ministère du Commerce", "M_COMM")),
    (re.compile(r"min.*(environ|écolog)", re.IGNORECASE),
     ("Ministère de l'Environnement", "M_ENV")),
    (re.compile(r"\bONSSA\b", re.IGNORECASE), ("ONSSA", "ONSSA")),
    (re.compile(r"\bNAFDAC\b", re.IGNORECASE), ("NAFDAC Nigeria", "NAFDAC")),
    (re.compile(r"\bKEBS\b", re.IGNORECASE), ("Kenya Bureau of Standards", "KEBS")),
    (re.compile(r"\bSARS\b", re.IGNORECASE), ("South African Revenue Service", "SARS")),
    (re.compile(r"\bDGD\b", re.IGNORECASE), ("Direction Générale des Douanes", "DGD")),
    (re.compile(r"quarantaine\s*vétéri|وﺯاﺭة.*بيطر|حجر.*بيطر", re.IGNORECASE),
     ("Direction de la Quarantaine Vétérinaire", "QUARAT_VET")),
    (re.compile(r"cites|espèces?\s+menacées?", re.IGNORECASE),
     ("Autorité CITES nationale", "CITES")),
]


def extract_authority(text: str) -> tuple[Optional[str], Optional[str]]:
    """
    Retourne (nom complet autorité, code/sigle) depuis le libellé,
    ou (None, None) si non identifiable.
    """
    for pattern, (name, code) in _AUTHORITY_MAP:
        if pattern.search(text):
            return name, code
    return None, None


# ------------------------------------------------------------------
# Parsing des droits spécifiques / mixtes
# ------------------------------------------------------------------

_SPECIFIC_RE = re.compile(
    r"(?P<amount>[\d.,]+)\s*(?P<unit>[A-Z]{2,6}(?:/(?:kg|MT|t\b|litre|u\b|unité))?)(?:\s*/\s*(?P<per_unit>[^,;\n]+))?",
    re.IGNORECASE,
)
_PCT_RE = re.compile(r"([\d.,]+)\s*%")


def parse_duty_value(raw: str, rate_hint: Optional[float] = None) -> dict:
    """
    Analyse une valeur brute de droit et retourne un dict avec les champs
    Measure pertinents : rate_pct, rate_type, specific_amount, specific_unit.

    Exemples :
      "5.5%" → AD_VALOREM, rate_pct=5.5
      "free" / "0%" → EXEMPT, rate_pct=0.0
      "0.100 dinars" → SPECIFIC, specific_amount=0.1, specific_unit="TND"
      "10% + 5 EGP/kg" → MIXED, rate_pct=10.0, specific_amount=5.0
    """
    r = raw.strip().lower() if raw else ""
    if not r or r in ("free", "0", "0.0", "0%", "exonéré", "exempt"):
        return {"rate_pct": 0.0, "rate_type": RateType.EXEMPT,
                "specific_amount": None, "specific_unit": None}

    pct_matches = _PCT_RE.findall(raw)
    spec_match  = _SPECIFIC_RE.search(raw)

    rate_pct = float(pct_matches[0].replace(",", ".")) if pct_matches else rate_hint

    if spec_match and pct_matches:
        # MIXED : % + montant spécifique
        try:
            amount = float(spec_match.group("amount").replace(",", "."))
        except (ValueError, AttributeError):
            amount = None
        unit   = (spec_match.group("unit") or "").upper()
        if amount is not None:
            return {"rate_pct": rate_pct, "rate_type": RateType.MIXED,
                    "specific_amount": amount, "specific_unit": unit or None}

    if spec_match and not pct_matches:
        # SPECIFIC pur
        try:
            amount = float(spec_match.group("amount").replace(",", "."))
        except (ValueError, AttributeError):
            amount = None
        unit   = (spec_match.group("unit") or "").upper()
        if amount is not None:
            return {"rate_pct": None, "rate_type": RateType.SPECIFIC,
                    "specific_amount": amount, "specific_unit": unit or None}

    if rate_pct is not None:
        return {"rate_pct": rate_pct, "rate_type": RateType.AD_VALOREM,
                "specific_amount": None, "specific_unit": None}

    return {"rate_pct": None, "rate_type": RateType.AD_VALOREM,
            "specific_amount": None, "specific_unit": None}


# ------------------------------------------------------------------
# Écriture JSONL
# ------------------------------------------------------------------

def write_jsonl(lines: list[CanonicalTariffLine], path: Path) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        for line in lines:
            fh.write(line.model_dump_json(exclude_none=False) + "\n")
    return len(lines)


def load_crawled(country_iso3: str) -> dict:
    """Charge le fichier crawlé pour un pays (lève FileNotFoundError si absent)."""
    path = CRAWLED_DIR / f"{country_iso3}_tariffs.json"
    if not path.exists():
        raise FileNotFoundError(f"Fichier crawlé introuvable : {path}")
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)
