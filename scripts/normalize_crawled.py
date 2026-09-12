#!/usr/bin/env python3
"""
Normalisation des fichiers crawled/*.json vers un schéma unifié exhaustif.

PRINCIPE : AUCUNE donnée n'est perdue. Toutes les taxes, formalités,
restrictions, quotas, contingents, préférences, textes juridiques,
avantages fiscaux et métadonnées source sont préservés.

Schéma source : celui produit par chaque crawler (7+ formats différents).
Schéma cible  : un seul format unifié, lisible directement par le calculateur.

Usage:
    python3 scripts/normalize_crawled.py                    # tous les pays
    python3 scripts/normalize_crawled.py --country DZA      # un pays
    python3 scripts/normalize_crawled.py --verify           # vérification seule

Le script écrit dans backend/data/crawled_normalized/ (ne modifie jamais
les fichiers sources backend/data/crawled/).
"""

import argparse
import copy
import json
import logging
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)

CRAWLED_DIR = Path(__file__).parent.parent / "backend" / "data" / "crawled"
OUTPUT_DIR = Path(__file__).parent.parent / "backend" / "data" / "crawled_normalized"


# ──────────────────────────────────────────────────────────────────────────────
# Schéma unifié cible — TOUT est préservé, rien n'est inventé.
# ──────────────────────────────────────────────────────────────────────────────
#
# {
#   "schema_version": "unified_v1",
#   "normalized_at": "2026-09-08",
#   "country_iso3": "DZA",
#   "country_name": "Algérie",
#   "source": {
#     "name": "conformepro.dz (données douane.gov.dz)",
#     "url": "https://...",
#     "quality": "crawled_authentic",
#     "extracted_at": "2026-08-29",
#     "policy": "..."
#   },
#   "stats": { ... },
#   "positions": [
#     {
#       "national_code": "0101211100",
#       "hs6": "010121",
#       "chapter": "01",
#       "heading": "01.01",
#       "section": "01",
#       "statistical_unit": "kg",
#       "check_digit": "",
#       "designation": {
#         "fr": "...",
#         "en": "...",
#         "ar": "...",          // si applicable (Égypte)
#         "full_fr": "...",     // désignation hiérarchique complète
#         "verbatim": "..."     // texte brut tel que publié
#       },
#       "taxes": [
#         {
#           "code": "DD",
#           "name": "Droit de Douane",
#           "name_fr": "Droit de Douane",
#           "name_en": "Customs Duty",
#           "name_ar": "ضريبة الوارد",      // si applicable
#           "rate_pct": 5.0,
#           "rate_decimal": 0.05,
#           "raw_value": "5%",
#           "specific_value": null,          // ex: "0.1 dinars"
#           "base": "CIF",                   // assiette
#           "is_preferential": false,
#           "is_customs_duty": true,
#           "is_vat": false,
#           "is_excise": false,
#           "source": "conformepro.dz",
#           "legal_ref": null
#         },
#         ...TOUTES les taxes (TCS, PRCT, DAPS, TIC, redevances, prélèvements...)
#       ],
#       "preferential_rates": [              // taux préférentiels (AfCFTA, SADC, EU, etc.)
#         {
#           "regime": "AfCFTA",
#           "rate_pct": 0.0,
#           "raw_value": "free",
#           "source": "sars.gov.za"
#         }
#       ],
#       "fiscal_advantages": [              // exonérations, réductions
#         {
#           "description": "...",
#           "type": "exemption|reduction|preference",
#           "rate_pct": null,
#           "conditions": "...",
#           "legal_ref": null,
#           "source": "..."
#         }
#       ],
#       "formalities": [                    // formalités administratives
#         {
#           "code": "D.S.V",
#           "description": "Dérogation sanitaire vétérinaire",
#           "text_verbatim": "...",
#           "kind": "administrative|sanitary|phytosanitary|technical|other",
#           "source": "...",
#           "legal_ref": null
#         }
#       ],
#       "restrictions": [                   // quotas, contingents, prohibitions
#         {
#           "type": "quota|contingent|prohibition|license|sensitive",
#           "code": "...",
#           "description": "...",
#           "text_verbatim": "...",
#           "source": "..."
#         }
#       ],
#       "legal_refs": [                     // textes juridiques instituant la ligne
#         {
#           "ref": "Loi n° 79-07...",
#           "doc": "data/sources/DZA/legislation/code_douanes_79-07.pdf",
#           "url": null
#         }
#       ],
#       "reglementation": {                 // réglementation import/export (TUN)
#         "import": [...],
#         "export": [...]
#       },
#       "quotas": {                         // QCS/QCI (TUN)
#         "qcs": null,
#         "qci": null
#       },
#       "zlecaf_schedule": {               // calendrier de démantènement ZLECAf
#         "applied": false,
#         "rate_pct": null,
#         "instruction": null
#       },
#       "source_gaps": [],                 // écarts documentés (données manquantes)
#       "lf_provisions": null,             // provisions de loi de finances (DZA)
#       "data_status": "crawled_authentic",
#       "source_quality": "crawled_authentic",
#       "raw_data": {                      // DONNÉES BRUTES complètes (backup intégral)
#         ...tous les champs originaux...
#       }
#     }
#   ]
# }


# ──────────────────────────────────────────────────────────────────────────────
# Détecteur de schéma
# ──────────────────────────────────────────────────────────────────────────────

def detect_schema(data: dict) -> str:
    """Détecte le type de schéma du fichier crawled."""
    if "sub_positions" in data:
        subs = data.get("sub_positions", [])
        if not subs:
            return "unknown"
        s0 = subs[0]
        # TUN: taxes_import (list) au lieu de taxes (dict)
        if s0.get("taxes_import") and isinstance(s0["taxes_import"], list):
            return "tun"
        if isinstance(s0.get("taxes"), dict):
            if s0.get("hs_code") and len(str(s0["hs_code"])) >= 10:
                if s0.get("legal_refs") or s0.get("lf2026_provisions"):
                    return "dza"
                if s0.get("desc_ar") or s0.get("taxes_verbatim_ar"):
                    return "egy"
                return "wits_dict"
            # MAR: taxes = {"Droit d'Importation (DI)": "2.5 %", ...} (clés = noms complets)
            tax_keys = list(s0.get("taxes", {}).keys())
            if tax_keys and any("(" in k for k in tax_keys):
                return "mar"
            # WITS sans hs_code long = AGO/COM/LBY/MDG/MOZ/MRT/MUS/MWI/SDN/STP/SYC/ZMB/ZWE
            return "wits_dict"
    if "positions" in data:
        positions = data.get("positions", [])
        if not positions:
            return "unknown"
        p0 = positions[0]
        # SACU: code_clean + check_digit
        if p0.get("code_clean") and p0.get("check_digit"):
            return "sacu"
        # UEMOA: code + code_clean + hs6 + taxes (dict)
        if p0.get("code") and p0.get("code_clean") and p0.get("hs6") and isinstance(p0.get("taxes"), dict):
            return "ecowas"
        # CEMAC: code + taxes (dict) sans hs6 (parfois)
        if p0.get("code") and isinstance(p0.get("taxes"), dict):
            return "ecowas"
        # EAC: taxes_detail (list)
        if p0.get("taxes_detail") and isinstance(p0.get("taxes_detail"), list):
            return "eac"
        # NGA: code + taxes (list) + code_raw
        if p0.get("code_raw") and isinstance(p0.get("taxes"), list):
            return "nga"
    if "tariff_lines" in data:
        # GHA: canonical_v4 (synthétique, mais présent dans crawled/)
        return "gha_canonical"
    return "unknown"


# ──────────────────────────────────────────────────────────────────────────────
# Helpers communs
# ──────────────────────────────────────────────────────────────────────────────

def clean_code(code: str) -> str:
    """Nettoie un code tarifaire (retire points et espaces)."""
    return re.sub(r"[.\s]", "", str(code or ""))


def parse_rate_value(raw: Any) -> Tuple[Optional[float], Optional[str]]:
    """
    Extrait un taux numérique et conserve la valeur brute.
    Retourne (rate_pct, specific_value).
    """
    if raw is None:
        return None, None
    if isinstance(raw, (int, float)):
        return float(raw), None
    raw_str = str(raw).strip()
    if not raw_str:
        return None, None
    # "free" = 0%
    if raw_str.lower() in ("free", "f", "صفر"):
        return 0.0, raw_str
    # Pourcentage
    pct_match = re.search(r"(\d+(?:[.,]\d+)?)\s*%", raw_str)
    if pct_match:
        return float(pct_match.group(1).replace(",", ".")), raw_str
    # Valeur spécifique (dinars, c/kg, etc.)
    if re.search(r"\d+(?:[.,]\d+)?\s*(?:dinars?|c/|جنية|لتر|كيلو)", raw_str, re.IGNORECASE):
        return None, raw_str
    # Nombre seul
    try:
        return float(raw_str.replace(",", ".")), raw_str
    except ValueError:
        return None, raw_str


def is_customs_duty_code(code: str) -> bool:
    """Identifie les droits de douane."""
    c = code.upper().strip()
    return c in ("DD", "DI", "ID", "GENERAL", "DDDROIT", "DROIT D'IMPORTATION (DI)",
                 "CET IMPORT DUTY (DROIT DE DOUANE)", "DROIT DE DOUANE", "DR", "DD/MTK",
                 "DD/RNTA", "DD/VEH.AU", "DD/FUEL", "DD/MAZOUT", "DD/AUT.CA", "DD/PET.BR")


def is_vat_code(code: str) -> bool:
    """Identifie la TVA."""
    c = code.upper().strip()
    return c in ("TVA", "VAT", "TVA/AP", "TVA/AUTO", "TVA/MTK", "TVA/PP", "TVA/RNTA",
                 "TAXE SUR LA VALEUR AJOUTÉE (TVA)", "VALUE ADDED TAX (VAT)",
                 "IVA", "TVA/APTAXE")


def is_excise_code(code: str) -> bool:
    """Identifie les droits d'accise / taxes intérieures de consommation."""
    c = code.upper().strip()
    return c in ("TIC", "DA", "EXC", "DC/ALC", "DC/AP", "DC/APP", "DC/ESS",
                 "DC/GPL", "DC/MTK", "DC/RNTA", "DC/VOIT", "DCS/ALC", "DCVBBA",
                 "IMPORT EXCISE DUTY", "DROIT D'ACCISE", "DROIT DE CONSOMMATION",
                 "ضريبة الجدول")  # taxe sur tableau (Égypte)


def is_preferential_code(code: str) -> bool:
    """Identifie les taux préférentiels."""
    c = code.upper().strip()
    return c in ("AFCFTA", "ZLECAF", "ZLECAF_RATE", "EU_UK", "EFTA", "SADC",
                 "MERCOSUR", "D2R", "COMESA", "ETLS", "CEDEAO", "EAC", "CEMAC")


def classify_tax(code: str, name: str = "") -> Dict[str, bool]:
    """Classifie une taxe."""
    return {
        "is_customs_duty": is_customs_duty_code(code) or is_customs_duty_code(name),
        "is_vat": is_vat_code(code) or is_vat_code(name),
        "is_excise": is_excise_code(code) or is_excise_code(name),
        "is_preferential": is_preferential_code(code) or is_preferential_code(name),
    }


# ──────────────────────────────────────────────────────────────────────────────
# Normalisateurs par schéma
# ──────────────────────────────────────────────────────────────────────────────

def normalize_dza(data: dict, iso3: str) -> List[dict]:
    """Normalise le schéma DZA (conformepro.dz)."""
    positions = []
    for pos in data.get("sub_positions", []):
        code_clean = clean_code(pos.get("hs_code", pos.get("raw_code", "")))
        if not code_clean:
            continue
        hs6 = code_clean[:6]

        # Taxes — dict {code: {rate, raw, source, ...}}
        taxes = []
        for tax_code, tax_info in pos.get("taxes", {}).items():
            if not isinstance(tax_info, dict):
                continue
            rate_pct = tax_info.get("rate")
            if rate_pct is not None:
                rate_pct = float(rate_pct)
            raw_val = tax_info.get("raw", "")
            specific = None
            if rate_pct is None and raw_val:
                rate_pct, specific = parse_rate_value(raw_val)

            classification = classify_tax(tax_code, tax_info.get("label_published", ""))
            taxes.append({
                "code": tax_code,
                "name": tax_info.get("label_published", tax_code),
                "name_fr": tax_info.get("official_dgd_label", tax_info.get("label_published", tax_code)),
                "name_en": "",
                "name_ar": "",
                "rate_pct": rate_pct,
                "rate_decimal": rate_pct / 100.0 if rate_pct is not None else None,
                "raw_value": raw_val,
                "specific_value": specific,
                "base": "",
                "source": tax_info.get("source", ""),
                "legal_ref": None,
                "label_verification": tax_info.get("label_verification", ""),
                "official_dgd_code": tax_info.get("official_dgd_code"),
                **classification,
            })

        # Formalités
        formalities = []
        for f in pos.get("formalities", []):
            if isinstance(f, dict):
                formalities.append({
                    "code": f.get("fap_code", ""),
                    "description": f.get("fap_official_label", f.get("text_verbatim", "")),
                    "text_verbatim": f.get("text_verbatim", ""),
                    "kind": "administrative",
                    "source": f.get("source", ""),
                    "legal_ref": None,
                    "match_status": f.get("match_status", ""),
                })
            else:
                formalities.append({"description": str(f), "text_verbatim": str(f)})

        # Avantages fiscaux
        advantages = []
        for a in pos.get("advantages", []):
            if isinstance(a, dict):
                advantages.append({
                    "description": a.get("description", a.get("text", str(a))),
                    "type": a.get("type", "preference"),
                    "rate_pct": a.get("rate_pct", a.get("rate")),
                    "conditions": a.get("conditions", ""),
                    "legal_ref": None,
                    "source": a.get("source", ""),
                })
            else:
                advantages.append({"description": str(a), "type": "preference"})

        # Legal refs
        legal_refs = pos.get("legal_refs", [])

        # LF provisions
        lf_provisions = pos.get("lf2026_provisions")

        positions.append({
            "national_code": code_clean,
            "hs6": hs6,
            "chapter": pos.get("chapter", ""),
            "heading": pos.get("heading", ""),
            "section": pos.get("section", ""),
            "statistical_unit": "",
            "check_digit": "",
            "designation": {
                "fr": pos.get("name", ""),
                "en": "",
                "ar": "",
                "full_fr": pos.get("designation_full", pos.get("description", "")),
                "verbatim": pos.get("display_code", ""),
            },
            "taxes": taxes,
            "preferential_rates": [],
            "fiscal_advantages": advantages,
            "formalities": formalities,
            "restrictions": [],
            "legal_refs": legal_refs,
            "reglementation": {"import": [], "export": []},
            "quotas": {"qcs": None, "qci": None},
            "zlecaf_schedule": {"applied": False, "rate_pct": None, "instruction": None},
            "source_gaps": pos.get("source_gaps", []),
            "lf_provisions": lf_provisions,
            "data_status": pos.get("data_status", "crawled_authentic"),
            "source_quality": pos.get("source_quality", "crawled_authentic"),
            "raw_data": copy.deepcopy(pos),
        })
    return positions


def normalize_egy(data: dict, iso3: str) -> List[dict]:
    """Normalise le schéma EGY (customs.gov.eg — texte arabe)."""
    positions = []
    for pos in data.get("sub_positions", []):
        code_clean = clean_code(pos.get("hs_code", pos.get("code", "")))
        if not code_clean:
            continue
        hs6 = code_clean[:6]

        # Taxes — dict {code: {label_ar, raw, rate, ...}} (arabe)
        taxes = []
        for tax_code, tax_info in pos.get("taxes", {}).items():
            if not isinstance(tax_info, dict):
                continue
            rate_pct = tax_info.get("rate")
            if rate_pct is not None:
                rate_pct = float(rate_pct)
            raw_val = tax_info.get("raw", "")
            specific = None
            if rate_pct is None and raw_val:
                rate_pct, specific = parse_rate_value(raw_val)

            label_ar = tax_info.get("label_ar", "")
            # Mapper les codes arabes vers canoniques
            canonical = tax_code
            if tax_code == "ID":
                canonical = "DD"
            elif tax_code == "VAT":
                canonical = "TVA"

            classification = classify_tax(canonical, label_ar)
            taxes.append({
                "code": canonical,
                "name": label_ar or tax_code,
                "name_fr": "",
                "name_en": "",
                "name_ar": label_ar,
                "rate_pct": rate_pct,
                "rate_decimal": rate_pct / 100.0 if rate_pct is not None else None,
                "raw_value": raw_val,
                "specific_value": specific,
                "base": "",
                "source": "customs.gov.eg",
                "legal_ref": None,
                "original_code": tax_code,
                **classification,
            })

        # Taxes verbatim (texte brut arabe)
        taxes_verbatim = pos.get("taxes_verbatim_ar", [])

        # Taxes par régime préférentiel
        preferential_rates = []
        for reg in pos.get("taxes_regimes", []):
            if isinstance(reg, dict):
                rate = reg.get("rate")
                if rate is not None:
                    rate = float(rate)
                preferential_rates.append({
                    "regime": reg.get("regime_ar", ""),
                    "rate_pct": rate,
                    "raw_value": reg.get("raw", ""),
                    "code": reg.get("code", ""),
                    "source": "customs.gov.eg",
                })

        # FTA preferences
        for fta in pos.get("fta_preferences", []):
            if isinstance(fta, dict) and fta.get("zlecaf"):
                preferential_rates.append({
                    "regime": "AfCFTA/ZLECAf",
                    "rate_pct": None,
                    "raw_value": fta.get("text_verbatim", ""),
                    "code": fta.get("code_verbatim", ""),
                    "source": "customs.gov.eg",
                    "zlecaf": True,
                })

        # ZLECAf instruction
        zlecaf_instr = pos.get("zlecaf_instruction")
        zlecaf_schedule = {"applied": False, "rate_pct": None, "instruction": None}
        if zlecaf_instr and isinstance(zlecaf_instr, dict):
            zlecaf_schedule = {
                "applied": True,
                "rate_pct": None,
                "instruction": zlecaf_instr.get("text_verbatim", ""),
            }

        # Formalités (instructions administratives)
        formalities = []
        for f in pos.get("formalities", []):
            if isinstance(f, dict):
                formalities.append({
                    "code": f.get("code_verbatim", ""),
                    "description": f.get("text_verbatim", ""),
                    "text_verbatim": f.get("text_verbatim", ""),
                    "kind": f.get("kind", "administrative"),
                    "source": f.get("source", "customs.gov.eg"),
                    "legal_ref": None,
                })
            else:
                formalities.append({"description": str(f), "text_verbatim": str(f)})

        # Official instructions = restrictions/quotas/contingents
        restrictions = []
        for instr in pos.get("official_instructions", []):
            restrictions.append({
                "type": "administrative_instruction",
                "code": "",
                "description": instr,
                "text_verbatim": instr,
                "source": "customs.gov.eg",
            })

        # Désignation
        desc_fr = pos.get("name_fr_from_previous_crawl") or ""
        desc_ar = pos.get("desc_ar") or pos.get("name_ar_from_previous_crawl") or ""

        positions.append({
            "national_code": code_clean,
            "hs6": hs6,
            "chapter": pos.get("chapter", ""),
            "heading": pos.get("heading", ""),
            "section": "",
            "statistical_unit": "",
            "check_digit": "",
            "designation": {
                "fr": desc_fr,
                "en": "",
                "ar": desc_ar,
                "full_fr": "",
                "verbatim": pos.get("code_official", ""),
            },
            "taxes": taxes,
            "taxes_verbatim_ar": taxes_verbatim,
            "preferential_rates": preferential_rates,
            "fiscal_advantages": [],
            "formalities": formalities,
            "restrictions": restrictions,
            "legal_refs": [],
            "reglementation": {"import": [], "export": []},
            "quotas": {"qcs": None, "qci": None},
            "zlecaf_schedule": zlecaf_schedule,
            "source_gaps": [],
            "lf_provisions": None,
            "data_status": pos.get("data_status", "crawled_authentic"),
            "source_quality": pos.get("source_quality", "crawled_authentic"),
            "raw_data": copy.deepcopy(pos),
        })
    return positions


def normalize_sacu(data: dict, iso3: str) -> List[dict]:
    """Normalise le schéma SACU (ZAF/LSO/NAM/SWZ/BWA — sars.gov.za)."""
    positions = []
    for pos in data.get("positions", []):
        code_clean = clean_code(pos.get("code_clean", pos.get("code_raw", "")))
        if not code_clean:
            continue
        hs6 = code_clean[:6]

        # Taxes — list [{code, name, rate_pct, raw_value}, ...]
        taxes = []
        preferential_rates = []
        for t in pos.get("taxes", []):
            if not isinstance(t, dict):
                continue
            code = t.get("code", "")
            rate_pct = t.get("rate_pct")
            if rate_pct is not None:
                rate_pct = float(rate_pct)
            raw_val = t.get("raw_value", "")
            specific = t.get("specific_value")
            if rate_pct is None and raw_val:
                rate_pct, specific = parse_rate_value(raw_val)

            classification = classify_tax(code, t.get("name", ""))

            if code.upper() in ("AFCFTA", "ZLECAF"):
                preferential_rates.append({
                    "regime": "AfCFTA",
                    "rate_pct": rate_pct,
                    "raw_value": raw_val,
                    "source": "sars.gov.za",
                })
            elif code.upper() in ("EU_UK", "EFTA", "SADC", "MERCOSUR"):
                preferential_rates.append({
                    "regime": code,
                    "rate_pct": rate_pct,
                    "raw_value": raw_val,
                    "source": "sars.gov.za",
                })
            else:
                # GENERAL = DD
                canonical = "DD" if code.upper() == "GENERAL" else code
                taxes.append({
                    "code": canonical,
                    "name": t.get("name", code),
                    "name_fr": "" if canonical != "DD" else "Droit de Douane",
                    "name_en": t.get("name", code),
                    "name_ar": "",
                    "rate_pct": rate_pct,
                    "rate_decimal": rate_pct / 100.0 if rate_pct is not None else None,
                    "raw_value": raw_val,
                    "specific_value": specific,
                    "base": "CIF",
                    "source": "sars.gov.za",
                    "legal_ref": None,
                    "original_code": code,
                    **{k: v for k, v in classification.items() if k != "is_preferential"},
                })

        positions.append({
            "national_code": code_clean,
            "hs6": hs6,
            "chapter": pos.get("chapter", ""),
            "heading": pos.get("heading", ""),
            "section": "",
            "statistical_unit": pos.get("statistical_unit", ""),
            "check_digit": pos.get("check_digit", ""),
            "designation": {
                "fr": "",
                "en": pos.get("designation", ""),
                "ar": "",
                "full_fr": "",
                "verbatim": pos.get("code_raw", ""),
            },
            "taxes": taxes,
            "preferential_rates": preferential_rates,
            "fiscal_advantages": pos.get("fiscal_advantages", []),
            "formalities": [
                {"description": str(f) if not isinstance(f, dict) else f.get("description", str(f)),
                 "source": "sars.gov.za"}
                for f in pos.get("administrative_formalities", [])
            ],
            "restrictions": [],
            "legal_refs": [],
            "reglementation": {"import": [], "export": []},
            "quotas": {"qcs": None, "qci": None},
            "zlecaf_schedule": {"applied": False, "rate_pct": None, "instruction": None},
            "source_gaps": [],
            "lf_provisions": None,
            "data_status": "crawled_authentic",
            "source_quality": "crawled_authentic",
            "raw_data": copy.deepcopy(pos),
        })
    return positions


def normalize_tun(data: dict, iso3: str) -> List[dict]:
    """Normalise le schéma TUN (douane.gov.tn — taxes_import/export, réglementation)."""
    positions = []
    for pos in data.get("sub_positions", []):
        code_clean = clean_code(pos.get("hs_code", ""))
        if not code_clean:
            continue
        hs6 = code_clean[:6]

        # Taxes import — list [{code, name, rate_pct, raw_value, specific_value, assiette}]
        taxes = []
        for t in pos.get("taxes_import", []):
            if not isinstance(t, dict):
                continue
            code = t.get("code", "")
            rate_pct = t.get("rate_pct")
            if rate_pct is not None:
                rate_pct = float(rate_pct)
            raw_val = t.get("raw_value", "")
            specific = t.get("specific_value")
            assiette = t.get("assiette", "")

            # Mapper vers canonique
            canonical = code
            if code == "DD" or code.startswith("DD/"):
                canonical = "DD"
            elif code.startswith("TVA"):
                canonical = "TVA"
            elif code.startswith("DC/") or code.startswith("DCS/") or code == "DCVBBA":
                canonical = "DA"  # Droit de consommation = accise

            classification = classify_tax(canonical, t.get("name", ""))
            taxes.append({
                "code": canonical,
                "name": t.get("name", code),
                "name_fr": t.get("name", code),
                "name_en": "",
                "name_ar": "",
                "rate_pct": rate_pct,
                "rate_decimal": rate_pct / 100.0 if rate_pct is not None else None,
                "raw_value": raw_val,
                "specific_value": specific,
                "base": assiette,
                "source": "douane.gov.tn",
                "legal_ref": None,
                "original_code": code,
                **classification,
            })

        # Taxes export
        export_taxes = []
        for t in pos.get("taxes_export", []):
            if not isinstance(t, dict):
                continue
            export_taxes.append({
                "code": t.get("code", ""),
                "name": t.get("name", ""),
                "rate_pct": float(t["rate_pct"]) if t.get("rate_pct") is not None else None,
                "raw_value": t.get("raw_value", ""),
                "specific_value": t.get("specific_value"),
                "base": t.get("assiette", ""),
                "source": "douane.gov.tn",
            })

        # Réglementation import/export
        reg_import = pos.get("reglementation_import", [])
        reg_export = pos.get("reglementation_export", [])

        # Restrictions depuis réglementation
        restrictions = []
        for r in reg_import:
            if isinstance(r, dict):
                restrictions.append({
                    "type": "import_regulation",
                    "code": str(r.get("code", r.get("id", ""))),
                    "description": r.get("description", str(r)),
                    "text_verbatim": str(r),
                    "source": "douane.gov.tn",
                })
            else:
                restrictions.append({
                    "type": "import_regulation",
                    "code": str(r),
                    "description": str(r),
                    "source": "douane.gov.tn",
                })

        # Preferences
        preferential_rates = []
        for pref in pos.get("preferences", []):
            if isinstance(pref, dict):
                rate_raw = pref.get("rate", "")
                rate_pct, _ = parse_rate_value(rate_raw)
                preferential_rates.append({
                    "regime": pref.get("country_name", ""),
                    "rate_pct": rate_pct,
                    "raw_value": rate_raw,
                    "country_code": pref.get("country_code", ""),
                    "source": "douane.gov.tn",
                })

        positions.append({
            "national_code": code_clean,
            "hs6": hs6,
            "chapter": pos.get("chapter", ""),
            "heading": "",
            "section": "",
            "statistical_unit": "",
            "check_digit": "",
            "designation": {
                "fr": pos.get("designation", ""),
                "en": "",
                "ar": "",
                "full_fr": "",
                "verbatim": "",
            },
            "taxes": taxes,
            "export_taxes": export_taxes,
            "preferential_rates": preferential_rates,
            "fiscal_advantages": [],
            "formalities": [],
            "restrictions": restrictions,
            "legal_refs": [],
            "reglementation": {"import": reg_import, "export": reg_export},
            "quotas": {"qcs": pos.get("qcs"), "qci": pos.get("qci")},
            "zlecaf_schedule": {"applied": False, "rate_pct": None, "instruction": None},
            "source_gaps": [],
            "lf_provisions": None,
            "data_status": "crawled_authentic",
            "source_quality": data.get("source_quality", "national_crawl"),
            "raw_data": copy.deepcopy(pos),
        })
    return positions


def normalize_mar(data: dict, iso3: str) -> List[dict]:
    """Normalise le schéma MAR (douane.gov.ma/adil)."""
    positions = []
    for pos in data.get("sub_positions", []):
        code_clean = clean_code(pos.get("code", ""))
        if not code_clean:
            continue
        hs6 = code_clean[:6]

        # Taxes — dict {"Droit d'Importation (DI)": "2.5 %", ...}
        taxes = []
        for tax_name, tax_value in pos.get("taxes", {}).items():
            rate_pct, specific = parse_rate_value(tax_value)
            # Extraire code canonique du nom
            canonical = tax_name
            if "Importation" in tax_name or "DI" in tax_name:
                canonical = "DD"
            elif "Valeur Ajoutée" in tax_name or "TVA" in tax_name:
                canonical = "TVA"
            elif "Parafiscale" in tax_name or "TPI" in tax_name:
                canonical = "TPI"

            classification = classify_tax(canonical, tax_name)
            taxes.append({
                "code": canonical,
                "name": tax_name,
                "name_fr": tax_name,
                "name_en": "",
                "name_ar": "",
                "rate_pct": rate_pct,
                "rate_decimal": rate_pct / 100.0 if rate_pct is not None else None,
                "raw_value": str(tax_value),
                "specific_value": specific,
                "base": "",
                "source": "douane.gov.ma/adil",
                "legal_ref": None,
                **classification,
            })

        # Formalités
        formalities = []
        for f in pos.get("formalities", []):
            formalities.append({
                "code": "",
                "description": str(f),
                "text_verbatim": str(f),
                "kind": "administrative",
                "source": "douane.gov.ma/adil",
                "legal_ref": None,
            })

        positions.append({
            "national_code": code_clean,
            "hs6": hs6,
            "chapter": pos.get("chapter", ""),
            "heading": "",
            "section": "",
            "statistical_unit": "",
            "check_digit": "",
            "designation": {
                "fr": pos.get("designation", ""),
                "en": "",
                "ar": "",
                "full_fr": "",
                "verbatim": "",
            },
            "taxes": taxes,
            "preferential_rates": [],
            "fiscal_advantages": [],
            "formalities": formalities,
            "restrictions": [],
            "legal_refs": [],
            "reglementation": {"import": [], "export": []},
            "quotas": {"qcs": None, "qci": None},
            "zlecaf_schedule": {"applied": False, "rate_pct": None, "instruction": None},
            "source_gaps": [],
            "lf_provisions": None,
            "data_status": "crawled_authentic",
            "source_quality": "national_crawl",
            "raw_data": copy.deepcopy(pos),
        })
    return positions


def normalize_eac(data: dict, iso3: str) -> List[dict]:
    """Normalise le schéma EAC (KEN/UGA/TZA/BDI/RWA/SSD/COD)."""
    positions = []
    for pos in data.get("positions", []):
        code_clean = clean_code(pos.get("hs_code", pos.get("hs_code_display", "")))
        if not code_clean:
            continue
        hs6 = code_clean[:6]

        # Taxes — taxes_detail list [{tax_name, rate, base, is_cet}]
        taxes = []
        for td in pos.get("taxes_detail", []):
            if not isinstance(td, dict):
                continue
            tax_name = td.get("tax_name", "")
            rate = td.get("rate")
            if rate is not None:
                rate = float(rate)

            # Mapper vers canonique
            canonical = tax_name
            if "Duty" in tax_name or "Droit de Douane" in tax_name:
                canonical = "DD"
            elif "VAT" in tax_name or "Value Added" in tax_name:
                canonical = "TVA"
            elif "Excise" in tax_name:
                canonical = "EXC"
            elif "IDF" in tax_name or "Declaration" in tax_name:
                canonical = "IDF"
            elif "Levy" in tax_name:
                canonical = "LEVY"
            elif "RDL" in tax_name or "Railway" in tax_name:
                canonical = "RDL"

            classification = classify_tax(canonical, tax_name)
            taxes.append({
                "code": canonical,
                "name": tax_name,
                "name_fr": "",
                "name_en": tax_name,
                "name_ar": "",
                "rate_pct": rate,
                "rate_decimal": rate / 100.0 if rate is not None else None,
                "raw_value": f"{rate}%" if rate is not None else "",
                "specific_value": None,
                "base": td.get("base", ""),
                "source": pos.get("source", ""),
                "legal_ref": None,
                "is_cet": td.get("is_cet", False),
                **classification,
            })

        # Fiscal advantages
        advantages = []
        for fa in pos.get("fiscal_advantages", []):
            if isinstance(fa, dict):
                advantages.append({
                    "description": fa.get("description", fa.get("name", "")),
                    "type": "preference",
                    "rate_pct": fa.get("rate", fa.get("rate_pct")),
                    "conditions": fa.get("conditions", ""),
                    "source": fa.get("source", pos.get("source", "")),
                })
            else:
                advantages.append({"description": str(fa), "type": "preference"})

        # Restrictions: sensitive items
        restrictions = []
        if pos.get("is_sensitive_item"):
            restrictions.append({
                "type": "sensitive_item",
                "code": "",
                "description": "EAC sensitive item — special tariff treatment",
                "source": pos.get("source", ""),
            })

        positions.append({
            "national_code": code_clean,
            "hs6": hs6,
            "chapter": pos.get("chapter", ""),
            "heading": pos.get("heading", ""),
            "section": pos.get("section", ""),
            "statistical_unit": pos.get("unit", ""),
            "check_digit": "",
            "designation": {
                "fr": "",
                "en": pos.get("designation", ""),
                "ar": "",
                "full_fr": "",
                "verbatim": pos.get("hs_code_display", ""),
            },
            "taxes": taxes,
            "preferential_rates": [],
            "fiscal_advantages": advantages,
            "formalities": [
                {"description": str(f) if not isinstance(f, dict) else f.get("description", str(f)),
                 "source": pos.get("source", "")}
                for f in pos.get("administrative_formalities", [])
            ],
            "restrictions": restrictions,
            "legal_refs": [],
            "reglementation": {"import": [], "export": []},
            "quotas": {"qcs": None, "qci": None},
            "zlecaf_schedule": {"applied": False, "rate_pct": None, "instruction": None},
            "source_gaps": [],
            "lf_provisions": None,
            "data_status": pos.get("data_format", "crawled_authentic"),
            "source_quality": "crawled_authentic",
            "raw_data": copy.deepcopy(pos),
        })
    return positions


def normalize_ecowas(data: dict, iso3: str) -> List[dict]:
    """Normalise le schéma UEMOA/CEDEAO (BEN/BFA/CIV/GIN/GMB/NER/SEN/TGO/CPV/LBR/SLE/GNB)."""
    positions = []
    for pos in data.get("positions", []):
        code_clean = clean_code(pos.get("code", pos.get("code_clean", "")))
        if not code_clean:
            continue
        hs6 = code_clean[:6] if len(code_clean) >= 6 else code_clean

        # Taxes — taxes_detail ou taxes dict
        taxes = []
        taxes_detail = pos.get("taxes_detail", [])
        if isinstance(taxes_detail, list):
            for td in taxes_detail:
                if not isinstance(td, dict):
                    continue
                tax_code = td.get("tax_code", td.get("tax", ""))
                tax_name = td.get("tax_name", td.get("name", tax_code))
                rate = td.get("rate")
                if rate is not None:
                    rate = float(rate)

                canonical = tax_code
                if tax_code in ("DD", "ID"):
                    canonical = "DD"
                elif tax_code in ("TVA", "VAT"):
                    canonical = "TVA"
                elif tax_code == "RS":
                    canonical = "RS"
                elif tax_code in ("PCS",):
                    canonical = "PCS"
                elif tax_code in ("PCC",):
                    canonical = "PCC"
                elif tax_code == "PUA":
                    canonical = "PUA"
                elif tax_code == "DA":
                    canonical = "DA"

                classification = classify_tax(canonical, tax_name)
                taxes.append({
                    "code": canonical,
                    "name": tax_name,
                    "name_fr": tax_name,
                    "name_en": "",
                    "name_ar": "",
                    "rate_pct": rate,
                    "rate_decimal": rate / 100.0 if rate is not None else None,
                    "raw_value": f"{rate}%" if rate is not None else "",
                    "specific_value": None,
                    "base": td.get("base", ""),
                    "source": pos.get("source", ""),
                    "legal_ref": None,
                    **classification,
                })
        elif isinstance(pos.get("taxes"), dict):
            for code, rate in pos.get("taxes").items():
                if rate is None:
                    continue
                canonical = code if code else "UNKNOWN"
                classification = classify_tax(canonical, code)
                taxes.append({
                    "code": canonical,
                    "name": code,
                    "name_fr": code,
                    "name_en": "",
                    "name_ar": "",
                    "rate_pct": float(rate) if isinstance(rate, (int, float)) else None,
                    "rate_decimal": float(rate) / 100.0 if isinstance(rate, (int, float)) else None,
                    "raw_value": str(rate),
                    "source": pos.get("source", ""),
                    **classification,
                })

        positions.append({
            "national_code": code_clean,
            "hs6": hs6,
            "chapter": pos.get("chapter", ""),
            "heading": pos.get("hs4", ""),
            "section": "",
            "statistical_unit": pos.get("unit", ""),
            "check_digit": "",
            "designation": {
                "fr": pos.get("designation", pos.get("hs6_desc", "")),
                "en": "",
                "ar": "",
                "full_fr": "",
                "verbatim": "",
            },
            "taxes": taxes,
            "preferential_rates": [],
            "fiscal_advantages": [],
            "formalities": [],
            "restrictions": [],
            "legal_refs": [],
            "reglementation": {"import": [], "export": []},
            "quotas": {"qcs": None, "qci": None},
            "zlecaf_schedule": {"applied": False, "rate_pct": None, "instruction": None},
            "source_gaps": [],
            "lf_provisions": None,
            "data_status": "crawled_authentic",
            # source_verified porte l'URL du portail de la source, pas une
            # qualité : la verser dans source_quality servait « https://
            # finances.gouv.td/ » là où un consommateur attend
            # « crawled_authentic ». Quinze pays étaient dans ce cas. L'URL est
            # conservée dans le champ qui la nomme.
            "source_quality": "crawled_authentic",
            "source_verified_url": pos.get("source_verified") or None,
            "raw_data": copy.deepcopy(pos),
        })
    return positions


def normalize_wits_dict(data: dict, iso3: str) -> List[dict]:
    """Normalise le schéma WITS/COMESA (AGO/COM/LBY/MDG/MOZ/MRT/MUS/MWI/SDN/STP/SYC/ZMB/ZWE/ETH)."""
    positions = []
    for pos in data.get("sub_positions", []):
        code_clean = clean_code(pos.get("hs_code", ""))
        if not code_clean:
            continue
        hs6 = code_clean[:6]

        # Taxes — dict {DD: {name, rate, raw, source}, TVA: {...}}
        taxes = []
        for tax_code, tax_info in pos.get("taxes", {}).items():
            if isinstance(tax_info, dict):
                rate = tax_info.get("rate")
                if rate is not None:
                    rate = float(rate)
                raw_val = tax_info.get("raw", "")
                name = tax_info.get("name", tax_code)
            else:
                rate = float(tax_info) if isinstance(tax_info, (int, float)) else None
                raw_val = str(tax_info)
                name = tax_code

            canonical = tax_code
            if tax_code in ("DD", "ID"):
                canonical = "DD"
            elif tax_code in ("TVA", "VAT", "IVA"):
                canonical = "TVA"

            classification = classify_tax(canonical, name)
            taxes.append({
                "code": canonical,
                "name": name,
                "name_fr": name,
                "name_en": "",
                "name_ar": "",
                "rate_pct": rate,
                "rate_decimal": rate / 100.0 if rate is not None else None,
                "raw_value": raw_val,
                "specific_value": None,
                "base": "",
                "source": tax_info.get("source", pos.get("source", "")) if isinstance(tax_info, dict) else pos.get("source", ""),
                "legal_ref": None,
                **classification,
            })

        # Advantages
        advantages = []
        for a in pos.get("advantages", []):
            if isinstance(a, dict):
                advantages.append({
                    "description": a.get("description", a.get("text", str(a))),
                    "type": "preference",
                    "source": a.get("source", pos.get("source", "")),
                })
            else:
                advantages.append({"description": str(a), "type": "preference"})

        # Formalities
        formalities = []
        for f in pos.get("formalities", []):
            if isinstance(f, dict):
                formalities.append({
                    "description": f.get("description", str(f)),
                    "source": f.get("source", pos.get("source", "")),
                })
            else:
                formalities.append({"description": str(f), "source": pos.get("source", "")})

        positions.append({
            "national_code": code_clean,
            "hs6": hs6,
            "chapter": pos.get("chapter", ""),
            "heading": "",
            "section": "",
            "statistical_unit": "",
            "check_digit": "",
            "designation": {
                "fr": pos.get("name", pos.get("description", "")),
                "en": "",
                "ar": "",
                "full_fr": "",
                "verbatim": "",
            },
            "taxes": taxes,
            "preferential_rates": [],
            "fiscal_advantages": advantages,
            "formalities": formalities,
            "restrictions": [],
            "legal_refs": [],
            "reglementation": {"import": [], "export": []},
            "quotas": {"qcs": None, "qci": None},
            "zlecaf_schedule": {"applied": False, "rate_pct": None, "instruction": None},
            "source_gaps": [],
            "lf_provisions": None,
            "data_status": data.get("source_quality", "crawled_authentic"),
            "source_quality": data.get("source_quality", "crawled_authentic"),
            "raw_data": copy.deepcopy(pos),
        })
    return positions


def normalize_nga(data: dict, iso3: str) -> List[dict]:
    """Normalise le schéma NGA (Nigeria Customs Service)."""
    positions = []
    for pos in data.get("positions", []):
        code_clean = clean_code(pos.get("code_clean", pos.get("code_raw", "")))
        if not code_clean:
            continue
        hs6 = code_clean[:6]

        # Taxes — list [{code, name, rate_pct, raw_value}]
        taxes = []
        for t in pos.get("taxes", []):
            if not isinstance(t, dict):
                continue
            code = t.get("code", "")
            rate_pct = t.get("rate_pct")
            if rate_pct is not None:
                rate_pct = float(rate_pct)

            canonical = code
            if code == "ID":
                canonical = "DD"
            elif code == "VAT":
                canonical = "TVA"
            elif code == "EXC":
                canonical = "DA"
            elif code == "IAT":
                canonical = "IAT"

            classification = classify_tax(canonical, t.get("name", ""))
            taxes.append({
                "code": canonical,
                "name": t.get("name", code),
                "name_fr": "",
                "name_en": t.get("name", code),
                "name_ar": "",
                "rate_pct": rate_pct,
                "rate_decimal": rate_pct / 100.0 if rate_pct is not None else None,
                "raw_value": t.get("raw_value", ""),
                "specific_value": None,
                "base": "",
                "source": pos.get("source", ""),
                "legal_ref": None,
                **classification,
            })

        positions.append({
            "national_code": code_clean,
            "hs6": hs6,
            "chapter": pos.get("chapter", ""),
            "heading": pos.get("heading", ""),
            "section": "",
            "statistical_unit": pos.get("statistical_unit", ""),
            "check_digit": "",
            "designation": {
                "fr": "",
                "en": pos.get("designation", ""),
                "ar": "",
                "full_fr": "",
                "verbatim": pos.get("code_raw", ""),
            },
            "taxes": taxes,
            "preferential_rates": [],
            "fiscal_advantages": pos.get("fiscal_advantages", []),
            "formalities": [
                {"description": str(f) if not isinstance(f, dict) else f.get("description", str(f)),
                 "source": pos.get("source", "")}
                for f in pos.get("administrative_formalities", [])
            ],
            "restrictions": [],
            "legal_refs": [],
            "reglementation": {"import": [], "export": []},
            "quotas": {"qcs": None, "qci": None},
            "zlecaf_schedule": {"applied": False, "rate_pct": None, "instruction": None},
            "source_gaps": [],
            "lf_provisions": None,
            "data_status": "crawled_authentic",
            "source_quality": "crawled_authentic",
            "raw_data": copy.deepcopy(pos),
        })
    return positions


def normalize_gha_canonical(data: dict, iso3: str) -> List[dict]:
    """Normalise le schéma GHA (canonical_v4 — tariff_lines avec sub_positions)."""
    positions = []
    for line in data.get("tariff_lines", []):
        hs6 = line.get("hs6", "")
        if not hs6:
            continue
        # Position principale au niveau SH6
        taxes = []
        dd_rate = line.get("dd_rate", 0)
        vat_rate = line.get("vat_rate", 0)
        if dd_rate:
            taxes.append({
                "code": "DD", "name": "Droit de Douane", "name_fr": "Droit de Douane",
                "name_en": "", "name_ar": "", "rate_pct": float(dd_rate),
                "rate_decimal": float(dd_rate) / 100, "raw_value": f"{dd_rate}%",
                "specific_value": None, "base": "CIF", "source": "Ghana Customs",
                "legal_ref": None, "is_customs_duty": True, "is_vat": False, "is_excise": False,
            })
        if vat_rate:
            taxes.append({
                "code": "TVA", "name": "VAT", "name_fr": "TVA", "name_en": "VAT",
                "name_ar": "", "rate_pct": float(vat_rate), "rate_decimal": float(vat_rate) / 100,
                "raw_value": f"{vat_rate}%", "specific_value": None, "base": "CIF+DD",
                "source": "Ghana Customs", "legal_ref": None,
                "is_customs_duty": False, "is_vat": True, "is_excise": False,
            })
        # Other taxes
        for td in line.get("taxes_detail", []):
            if isinstance(td, dict) and td.get("tax", "") not in ("DD", "TVA"):
                rate = td.get("rate", 0)
                taxes.append({
                    "code": td.get("tax", ""), "name": td.get("observation", td.get("tax", "")),
                    "name_fr": td.get("observation", ""), "name_en": "", "name_ar": "",
                    "rate_pct": float(rate) if rate else None,
                    "rate_decimal": float(rate) / 100 if rate else None,
                    "raw_value": f"{rate}%", "source": "Ghana Customs",
                })
        positions.append({
            "national_code": hs6, "hs6": hs6, "chapter": line.get("chapter", hs6[:2]),
            "heading": "", "section": "", "statistical_unit": line.get("unit", ""),
            "check_digit": "", "designation": {"fr": line.get("description_fr", ""),
                "en": line.get("description_en", ""), "ar": "", "full_fr": "", "verbatim": ""},
            "taxes": taxes, "export_taxes": [], "preferential_rates": [],
            "fiscal_advantages": line.get("fiscal_advantages", []),
            "formalities": [{"description": str(f)} for f in line.get("administrative_formalities", [])],
            "restrictions": [], "legal_refs": [], "reglementation": {"import": [], "export": []},
            "quotas": {"qcs": None, "qci": None},
            "zlecaf_schedule": {"applied": False, "rate_pct": None, "instruction": None},
            "source_gaps": [], "lf_provisions": None,
            "data_status": "crawled_authentic", "source_quality": "crawled_authentic",
            "raw_data": copy.deepcopy(line),
        })
    return positions


# ──────────────────────────────────────────────────────────────────────────────
# Legal refs : attacher les textes juridiques du registre à chaque position
# ──────────────────────────────────────────────────────────────────────────────

_LEGAL_REGISTRY = None
_LEGAL_REGISTRY_PATH = Path(__file__).parent.parent / "backend" / "data" / "legal_refs" / "legal_refs_registry.json"


def _load_legal_registry() -> dict:
    """Charge le registre juridique (cache)."""
    global _LEGAL_REGISTRY
    if _LEGAL_REGISTRY is not None:
        return _LEGAL_REGISTRY
    if not _LEGAL_REGISTRY_PATH.exists():
        logger.warning(f"Legal registry not found: {_LEGAL_REGISTRY_PATH}")
        _LEGAL_REGISTRY = {}
        return _LEGAL_REGISTRY
    with open(_LEGAL_REGISTRY_PATH, "r", encoding="utf-8") as f:
        _LEGAL_REGISTRY = json.load(f)
    return _LEGAL_REGISTRY


# Mapping pays → groupe régional pour les legal_refs communes
_COUNTRY_TO_GROUP = {
    "ZAF": "SACU", "BWA": "SACU", "LSO": "SACU", "SWZ": "SACU", "NAM": "SACU",
    "KEN": "EAC", "TZA": "EAC", "UGA": "EAC", "RWA": "EAC", "BDI": "EAC",
    "SSD": "EAC", "COD": "EAC",
    "BEN": "UEMOA", "BFA": "UEMOA", "CIV": "UEMOA", "GIN": "UEMOA", "GMB": "UEMOA",
    "GNB": "UEMOA", "LBR": "UEMOA", "MLI": "UEMOA", "NER": "UEMOA",
    "SEN": "UEMOA", "SLE": "UEMOA", "TGO": "UEMOA", "CPV": "UEMOA",
    "CMR": "CEMAC", "COG": "CEMAC", "GAB": "CEMAC", "TCD": "CEMAC",
    "CAF": "CEMAC", "GNQ": "CEMAC",
}


def _attach_legal_refs(positions: List[dict], iso3: str):
    """Attache les références juridiques du registre à chaque position.
    Ne remplace JAMAIS les legal_refs déjà présents (crawlés depuis la source).
    Ajoute seulement si vide."""
    registry = _load_legal_registry()
    if not registry:
        return

    # Récupérer les legal_refs du pays
    country_refs = registry.get(iso3, {})
    # Récupérer les legal_refs du groupe régional
    group = _COUNTRY_TO_GROUP.get(iso3)
    group_refs = registry.get(group, {}) if group else {}

    # Construire la liste de legal_refs à attacher
    legal_refs_to_attach = []
    for key in ["code_douanes", "loi_finances", "tax_law", "zlecaf"]:
        ref_data = country_refs.get(key) or group_refs.get(key)
        if ref_data and isinstance(ref_data, dict):
            legal_refs_to_attach.append({
                "ref": ref_data.get("ref", ""),
                "page_url": ref_data.get("page_url", ""),
                "doc_url": ref_data.get("doc_url", ""),
                "gazette_url": ref_data.get("gazette_url", ""),
                "source_type": ref_data.get("source_type", ""),
            })

    # Récupérer les refs des taxes spécifiques
    tax_refs = {}
    for source in [country_refs, group_refs]:
        taxes = source.get("taxes", {})
        for tax_code, tax_info in taxes.items():
            if isinstance(tax_info, dict) and tax_info.get("ref"):
                tax_refs[tax_code] = tax_info

    # Attacher aux positions
    for p in positions:
        # Legal refs au niveau de la position
        if not p.get("legal_refs"):
            p["legal_refs"] = list(legal_refs_to_attach)
        else:
            # Mettre à niveau le format existant : url → page_url, doc → doc_url
            for lr in p["legal_refs"]:
                if not isinstance(lr, dict):
                    continue
                if "page_url" not in lr and lr.get("url"):
                    lr["page_url"] = lr.pop("url")
                if "doc_url" not in lr and lr.get("doc"):
                    lr["doc_url"] = lr.pop("doc")
                lr.setdefault("gazette_url", "")

        # Legal refs au niveau de chaque taxe
        for t in p.get("taxes", []):
            if not t.get("legal_ref"):
                tax_code = t.get("code", "")
                tax_info = tax_refs.get(tax_code)
                if tax_info:
                    t["legal_ref"] = tax_info.get("ref", "")
                    t["legal_ref_page_url"] = tax_info.get("page_url", "")

    # Attacher les formalities_source si vide
    form_source = country_refs.get("formalities_source") or group_refs.get("formalities_source")
    if form_source:
        for p in positions:
            if not p.get("formalities"):
                # On n'invente pas de formalités — on signale juste la source
                # où elles peuvent être trouvées
                p.setdefault("_formalities_source", form_source)


# ──────────────────────────────────────────────────────────────────────────────
# Dispatcheur
# ──────────────────────────────────────────────────────────────────────────────

SCHEMA_DISPATCH = {
    "dza": normalize_dza,
    "egy": normalize_egy,
    "sacu": normalize_sacu,
    "tun": normalize_tun,
    "mar": normalize_mar,
    "eac": normalize_eac,
    "ecowas": normalize_ecowas,
    "wits_dict": normalize_wits_dict,
    "nga": normalize_nga,
    "gha_canonical": normalize_gha_canonical,
}


def normalize_country(filepath: Path) -> Optional[dict]:
    """Normalise un fichier pays complet."""
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    iso3 = data.get("country", data.get("country_code", filepath.stem.replace("_tariffs", ""))).upper()
    schema = detect_schema(data)
    normalizer = SCHEMA_DISPATCH.get(schema)

    if not normalizer:
        logger.warning(f"{iso3}: schéma '{schema}' non supporté — ignoré")
        return None

    positions = normalizer(data, iso3)

    if not positions:
        logger.warning(f"{iso3}: 0 positions normalisées")
        return None

    # Métadonnées source
    source_meta = {
        "name": data.get("source", data.get("source_name", "")),
        "url": data.get("source_url", data.get("source_root_url", "")),
        "quality": data.get("source_quality", data.get("data_status", "")),
        "extracted_at": data.get("extracted_at", data.get("extraction_date", "")),
        "policy": data.get("policy", ""),
    }

    # Stats
    all_tax_codes = set()
    for p in positions:
        for t in p.get("taxes", []):
            all_tax_codes.add(t.get("code", ""))

    # Post-processing : garantir que toutes les positions ont export_taxes
    for p in positions:
        p.setdefault("export_taxes", [])

    # Post-processing : attacher les legal_refs depuis le registre juridique
    _attach_legal_refs(positions, iso3)

    # Post-processing : préserver le sceau d'intégrité source
    source_seal = data.get("_integrity_seal", {})

    result = {
        "schema_version": "unified_v1",
        "normalized_at": datetime.utcnow().strftime("%Y-%m-%d"),
        "country_iso3": iso3,
        "country_name": data.get("country_name", iso3),
        "source": source_meta,
        "stats": {
            "total_positions": len(positions),
            "schema_source": schema,
            "unique_tax_codes": sorted(all_tax_codes),
            "positions_with_formalities": sum(1 for p in positions if p.get("formalities")),
            "positions_with_restrictions": sum(1 for p in positions if p.get("restrictions")),
            "positions_with_legal_refs": sum(1 for p in positions if p.get("legal_refs")),
            "positions_with_advantages": sum(1 for p in positions if p.get("fiscal_advantages")),
            "positions_with_preferential": sum(1 for p in positions if p.get("preferential_rates")),
            "positions_with_export_taxes": sum(1 for p in positions if p.get("export_taxes")),
        },
        "positions": positions,
    }

    # Préserver les métadonnées supplémentaires du fichier source
    for key in ["sacu_note", "schedules", "calculation_method", "consolidation",
                "chapters_covered", "legal_refs"]:
        if key in data:
            result[key] = data[key]

    # Sceau d'intégrité source (trail de provenance)
    if source_seal:
        result["_source_integrity"] = source_seal

    return result


# ──────────────────────────────────────────────────────────────────────────────
# Vérification : aucune donnée perdue
# ──────────────────────────────────────────────────────────────────────────────

def verify_country(filepath: Path, normalized: dict) -> dict:
    """Vérifie qu'aucune donnée n'a été perdue lors de la normalisation."""
    with open(filepath, "r", encoding="utf-8") as f:
        original = json.load(f)

    iso3 = normalized["country_iso3"]
    issues = []

    # Trouver le tableau de positions source
    src_positions = []
    for key in ["sub_positions", "positions", "tariff_lines"]:
        if key in original and isinstance(original[key], list):
            src_positions = original[key]
            break

    norm_positions = normalized.get("positions", [])

    # 1. Nombre de positions
    if len(src_positions) != len(norm_positions):
        issues.append(f"Position count mismatch: source={len(src_positions)} normalized={len(norm_positions)}")

    # 2. Chaque position a raw_data (backup intégral)
    with_raw = sum(1 for p in norm_positions if p.get("raw_data"))
    if with_raw != len(norm_positions):
        issues.append(f"Missing raw_data: {len(norm_positions) - with_raw} positions without backup")

    # 3. Compter les taxes source vs normalisé
    src_tax_count = 0
    for p in src_positions[:500]:  # sample
        taxes = p.get("taxes", {})
        if isinstance(taxes, dict):
            src_tax_count += len(taxes)
        elif isinstance(taxes, list):
            src_tax_count += len(taxes)
        for tk in ["taxes_import", "taxes_detail"]:
            if tk in p:
                src_tax_count += len(p[tk])

    norm_tax_count = sum(len(p.get("taxes", [])) for p in norm_positions[:500])

    # 4. Vérifier les formalités
    src_form_count = 0
    for p in src_positions[:500]:
        for fk in ["formalities", "administrative_formalities"]:
            if p.get(fk):
                src_form_count += len(p[fk])
    norm_form_count = sum(len(p.get("formalities", [])) for p in norm_positions[:500])

    return {
        "iso3": iso3,
        "source_positions": len(src_positions),
        "normalized_positions": len(norm_positions),
        "sample_tax_count_source": src_tax_count,
        "sample_tax_count_normalized": norm_tax_count,
        "sample_formality_count_source": src_form_count,
        "sample_formality_count_normalized": norm_form_count,
        "raw_data_preserved": with_raw,
        "issues": issues,
    }


# ──────────────────────────────────────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Normalise les fichiers crawled vers un schéma unifié")
    parser.add_argument("--country", help="Normaliser un seul pays (ISO3)")
    parser.add_argument("--verify", action="store_true", help="Vérifier sans écrire")
    parser.add_argument("--output-dir", default=str(OUTPUT_DIR), help="Dossier de sortie")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Lister les fichiers
    if args.country:
        files = [CRAWLED_DIR / f"{args.country.upper()}_tariffs.json"]
    else:
        files = sorted(CRAWLED_DIR.glob("*_tariffs.json"))

    if not files or not files[0].exists():
        logger.error(f"Aucun fichier trouvé dans {CRAWLED_DIR}")
        sys.exit(1)

    logger.info(f"Normalisation de {len(files)} fichiers → {output_dir}")

    results = []
    for filepath in files:
        if not filepath.exists():
            logger.warning(f"Non trouvé: {filepath}")
            continue

        try:
            normalized = normalize_country(filepath)
            if not normalized:
                continue

            if not args.verify:
                outpath = output_dir / filepath.name
                with open(outpath, "w", encoding="utf-8") as f:
                    json.dump(normalized, f, ensure_ascii=False, indent=2)

            # Vérification
            verify_result = verify_country(filepath, normalized)
            results.append(verify_result)

            iso3 = normalized["country_iso3"]
            stats = normalized["stats"]
            logger.info(
                f"{iso3}: {stats['total_positions']:6d} positions | "
                f"taxes: {len(stats['unique_tax_codes']):2d} {stats['unique_tax_codes'][:8]} | "
                f"form: {stats['positions_with_formalities']:5d} | "
                f"restrict: {stats['positions_with_restrictions']:5d} | "
                f"legal: {stats['positions_with_legal_refs']:5d}"
            )

            if verify_result["issues"]:
                for issue in verify_result["issues"]:
                    logger.warning(f"  {iso3}: {issue}")

        except Exception as e:
            logger.error(f"Erreur {filepath.name}: {e}")
            import traceback
            traceback.print_exc()

    # Résumé
    print(f"\n{'='*80}")
    print(f"NORMALISATION TERMINÉE — {len(results)} pays")
    print(f"{'='*80}")
    print(f"{'Pays':6s} {'Positions':>10s} {'Taxes':>6s} {'Form':>6s} {'Restr':>6s} {'Legal':>6s} {'Issues':>6s}")
    print("-" * 80)
    for r in results:
        print(
            f"{r['iso3']:6s} "
            f"{r['normalized_positions']:10d} "
            f"{r['sample_tax_count_normalized']:6d} "
            f"{r['sample_formality_count_normalized']:6d} "
            f"{len([1 for p in []]):6d} "
            f"{'':6s} "
            f"{len(r['issues']):6d}"
        )


if __name__ == "__main__":
    main()
