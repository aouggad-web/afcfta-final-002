#!/usr/bin/env python3
"""
Générateur de positions nationales EAC CET 2022 — HS8 réelles
==============================================================
Source: Kenya Revenue Authority (KRA)
        https://www.kra.go.ke/images/publications/EAC-CET-2022-VERSION-30TH-JUNE-Fn.pdf
        → backend/data/pdfs/eac_cet_2022.pdf

Extrait les ~5 872 positions HS8 du PDF officiel EAC CET 2022
et génère les fichiers tarifaires pour les 7 États membres EAC.

Usage:
    python scripts/generate_eac_national_positions.py
    python scripts/generate_eac_national_positions.py KEN TZA UGA
"""

import json
import logging
import os
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from typing import Dict, List, Optional

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

PDF_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "pdfs", "eac_cet_2022.pdf")
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "crawled")

# ──────────────────────────────────────────────────────────────────────────────
# Configurations pays EAC + taxes nationales
# Sources: portails officiels customs + textes légaux
# ──────────────────────────────────────────────────────────────────────────────
EAC_COUNTRIES = {
    "KEN": {
        "name": "Kenya", "currency": "KES",
        "tva_rate": 16.0, "tva_name": "Value Added Tax (VAT)",
        "tva_base": "CIF + DD + IDF + RDL",
        "source": "Kenya Revenue Authority (KRA) + EAC CET 2022",
        "source_url": "https://www.kra.go.ke/",
        "national_taxes": [
            {"code": "IDF",  "name": "Import Declaration Fee",     "rate": 3.5, "base": "CIF",
             "authority": "KRA — Finance Act 2023; payable via KRA iTax"},
            {"code": "RDL",  "name": "Railway Development Levy",   "rate": 2.0, "base": "CIF",
             "authority": "Kenya Railways — Finance Act 2013 (Cap 397)"},
        ],
        "excise_by_chapter": {
            "22": 50.0, "24": 45.0, "87": 20.0,
        },
        "notes": ["EAC CET 2022 (4 bandes: 0%, 10%, 25%, 35%) + IDF 3.5% + RDL 2% + VAT 16%",
                  "Source: kra.go.ke / EAC-CET-2022-VERSION-30TH-JUNE-Fn.pdf"]
    },
    "TZA": {
        "name": "Tanzanie", "currency": "TZS",
        "tva_rate": 18.0, "tva_name": "Value Added Tax (VAT)",
        "tva_base": "CIF + DD",
        "source": "Tanzania Revenue Authority (TRA) + EAC CET 2022",
        "source_url": "https://www.tra.go.tz/",
        "national_taxes": [
            {"code": "SDL",  "name": "Skills and Development Levy", "rate": 6.0, "base": "CIF+DD",
             "authority": "TRA — Skills Development Levy Act Cap 388"},
        ],
        "excise_by_chapter": {
            "22": 30.0, "24": 35.0,
        },
        "notes": ["EAC CET 2022 + SDL 6% + VAT 18% — TRA"]
    },
    "UGA": {
        "name": "Ouganda", "currency": "UGX",
        "tva_rate": 18.0, "tva_name": "Value Added Tax (VAT)",
        "tva_base": "CIF + DD + Infrastructure Levy",
        "source": "Uganda Revenue Authority (URA) + EAC CET 2022",
        "source_url": "https://www.ura.go.ug/",
        "national_taxes": [
            {"code": "INFRA","name": "Infrastructure Development Levy","rate": 1.5, "base": "CIF",
             "authority": "URA — Finance Act 2018"},
        ],
        "excise_by_chapter": {
            "22": 60.0, "24": 40.0,
        },
        "notes": ["EAC CET 2022 + Infrastructure Levy 1.5% + VAT 18% — URA"]
    },
    "RWA": {
        "name": "Rwanda", "currency": "RWF",
        "tva_rate": 18.0, "tva_name": "Value Added Tax (VAT)",
        "tva_base": "CIF + DD + IDL",
        "source": "Rwanda Revenue Authority (RRA) + EAC CET 2022",
        "source_url": "https://www.rra.gov.rw/",
        "national_taxes": [
            {"code": "IDL",  "name": "Infrastructure Development Levy", "rate": 1.5, "base": "CIF",
             "authority": "RRA — Loi de finances 2021 — applicable à toutes importations"},
            {"code": "AU",   "name": "Prélèvement Union Africaine",     "rate": 0.2, "base": "CIF",
             "authority": "Union Africaine — Décision Assembly/AU/Dec.578(XXV)"},
        ],
        "excise_by_chapter": {
            "22": 30.0, "24": 36.0,
        },
        "notes": [
            "EAC CET 2022 + IDL 1.5% (CIF) + AU 0.2% (CIF) + VAT 18% — RRA",
            "TVA: exonérations légales sur denrées de base, intrants agricoles, médicaments — non modélisées",
        ]
    },
    "BDI": {
        "name": "Burundi", "currency": "BIF",
        "tva_rate": 18.0, "tva_name": "Taxe sur la Valeur Ajoutée (TVA)",
        "tva_base": "CIF + DD",
        "source": "Office Burundais des Recettes (OBR) + EAC CET 2022",
        "source_url": "https://www.obr.gov.bi/",
        "national_taxes": [
            {"code": "AU",   "name": "Prélèvement Union Africaine",     "rate": 0.2, "base": "CIF",
             "authority": "Union Africaine — Décision Assembly/AU/Dec.578(XXV)"},
        ],
        "excise_by_chapter": {"22": 30.0, "24": 30.0},
        "notes": ["EAC CET 2022 + AU 0.2% + TVA 18% — OBR"]
    },
    "SSD": {
        "name": "Soudan du Sud", "currency": "SSP",
        "tva_rate": 18.0, "tva_name": "Value Added Tax (VAT)",
        "tva_base": "CIF + DD",
        "source": "South Sudan Customs + EAC CET 2022",
        "source_url": "https://mof.gov.ss/",
        "national_taxes": [
            {"code": "AU",   "name": "African Union Levy",              "rate": 0.2, "base": "CIF",
             "authority": "African Union — Assembly/AU/Dec.578(XXV)"},
        ],
        "excise_by_chapter": {},
        "notes": ["EAC CET 2022 + AU 0.2% + VAT 18% (estimation — données officielles SSD limitées)"]
    },
    "COD": {
        "name": "RD Congo", "currency": "CDF",
        "tva_rate": 16.0, "tva_name": "Taxe sur la Valeur Ajoutée (TVA)",
        "tva_base": "CIF + DD + OCC",
        "source": "DGDA Congo + EAC CET 2022",
        "source_url": "https://www.dgda.gouv.cd/",
        "national_taxes": [
            {"code": "OCC", "name": "Redevance OCC (Office Congolais de Contrôle)", "rate": 1.5, "base": "CIF",
             "authority": "OCC — Décret 090-0012/1990 — applicable à TOUTES importations"},
        ],
        "excise_by_chapter": {},
        "notes": ["EAC CET 2022 + OCC 1.5% (toutes importations) + TVA 16% — DGDA"]
    },
}

# ──────────────────────────────────────────────────────────────────────────────
# Bandes tarifaires EAC CET 2022
# ──────────────────────────────────────────────────────────────────────────────
EAC_BAND_LABELS = {
    0.0:  "EAC CET Bande 0% — Matières premières / biens d'équipement",
    6.0:  "EAC CET Bande 6% — Taux spécial",
    10.0: "EAC CET Bande 10% — Intrants intermédiaires",
    25.0: "EAC CET Bande 25% — Biens de consommation finale",
    35.0: "EAC CET Bande 35% — Produits sensibles / protection industrie locale",
    50.0: "EAC CET Bande 50% — Liste sensible EAC (riz, céréales)",
    60.0: "EAC CET Bande 60% — Taux spécial élevé",
    75.0: "EAC CET Bande 75% — Liste sensible EAC (riz, taux max)",
    100.0:"EAC CET Bande 100% — Liste sensible EAC (sucre raffiné)",
}

# ──────────────────────────────────────────────────────────────────────────────
# Corrections liste sensible EAC — produits mal extraits du PDF
# Sources: EAC CET 2022 Gazette officielle + Kenya Legal Notice No.60/2023
# Ces taux surchargent le DD extrait du PDF quand celui-ci est erroné.
# ──────────────────────────────────────────────────────────────────────────────
SENSITIVE_LIST_DD_CORRECTIONS = {
    # Sucre raffiné — liste sensible EAC : 100% (pas 50%)
    "170111": 100.0, "170112": 100.0, "170191": 100.0, "170199": 100.0,
    # Vêtements usagés / friperie — 35% (pas 25%)
    "630900": 35.0,
    # Farine de blé — 60% liste sensible EAC
    "110100": 60.0,
    # Maïs — 50% liste sensible
    "100590": 50.0, "100510": 50.0,
    # Lait en poudre — 60% liste sensible
    "040210": 60.0, "040221": 60.0, "040229": 60.0,
    # Huile de cuisson / palme raffinée — 35%
    "151110": 35.0, "151190": 35.0, "151211": 35.0, "151219": 35.0,
    # Voitures particulières — 25% (le PDF peut extraire 0% pour certains SH8)
    "870321": 25.0, "870322": 25.0, "870323": 25.0, "870324": 25.0,
    "870331": 25.0, "870332": 25.0, "870333": 25.0,
}

UNIT_WORDS = {
    "u", "kg", "l", "m", "m2", "m3", "No.", "pair", "g", "set", "m/s",
    "t", "kWh", "GI", "ct", "1000", "2u", "pa", "T", "Kg", "KG", "L",
    "1000 u", "1000 l", "1000 kWh",
}


def parse_eac_pdf(pdf_path: str) -> List[Dict]:
    """
    Parse the full EAC CET 2022 PDF (560 pages).
    Returns list of {code, desc, rate, chapter, heading}.
    """
    try:
        import fitz
    except ImportError:
        logger.error("PyMuPDF (fitz) non disponible. Installer: pip install pymupdf")
        sys.exit(1)

    doc = fitz.open(pdf_path)
    logger.info(f"PDF EAC CET: {len(doc)} pages")

    hs8_pattern   = re.compile(r"^(\d{4}\.\d{2}\.\d{2})$")
    rate_pattern  = re.compile(r"^(\d+(?:\.\d+)?%|Free|SI)$")
    heading_pat   = re.compile(r"^(\d{2}\.\d{2})$")
    chapter_pat   = re.compile(r"^(\d{2})\s*$")

    positions = []
    current_heading = ""
    current_chapter = ""
    pages_with_data = 0

    for page_num in range(len(doc)):
        text  = doc[page_num].get_text()
        lines = [l.strip() for l in text.split("\n") if l.strip()]

        found_any = False
        i = 0
        while i < len(lines):
            line = lines[i]

            # Track heading and chapter context
            if heading_pat.fullmatch(line):
                current_heading = line.replace(".", "")

            # HS8 code detection
            hs8_m = hs8_pattern.fullmatch(line)
            if hs8_m:
                code = hs8_m.group(1).replace(".", "")
                current_chapter = code[:2]
                desc = ""
                rate = None

                for j in range(i + 1, min(i + 10, len(lines))):
                    l2 = lines[j]
                    rate_m = rate_pattern.fullmatch(l2)
                    if rate_m:
                        rs = l2.strip()
                        if rs in ("Free", "0%"):
                            rate = 0.0
                        elif rs == "SI":
                            rate = None  # Specific / suspended
                        else:
                            rate = float(rs.rstrip("%"))
                        break
                    elif (not hs8_pattern.fullmatch(l2)
                          and l2 not in UNIT_WORDS
                          and not l2.isdigit()
                          and len(l2) > 3):
                        if not desc:
                            desc = l2

                if rate is not None:
                    positions.append({
                        "code":    code,
                        "digits":  8,
                        "desc":    desc,
                        "rate":    rate,
                        "chapter": current_chapter,
                        "heading": current_heading or code[:4],
                    })
                    found_any = True

            i += 1

        if found_any:
            pages_with_data += 1

    # Rate distribution
    dist = Counter(p["rate"] for p in positions)
    logger.info(
        f"EAC CET: {len(positions)} positions HS8 extraites "
        f"({pages_with_data} pages) | Répartition: {dict(sorted(dist.items()))}"
    )
    return positions


def group_by_hs6(positions: List[Dict]) -> Dict[str, List[Dict]]:
    """Group HS8 positions by their HS6 parent (first 6 chars)."""
    groups: Dict[str, List[Dict]] = defaultdict(list)
    for p in positions:
        hs6 = p["code"][:6].zfill(6)
        groups[hs6].append(p)
    return dict(groups)


def build_taxes_detail(country_cfg: Dict, dd_rate: float, chapter: str) -> List[Dict]:
    """Build taxes_detail for a position."""
    items = [
        {
            "tax":         "D.D",
            "rate":        dd_rate,
            "base":        "CIF",
            "methode":     f"CIF × {dd_rate}%",
            "observation": EAC_BAND_LABELS.get(dd_rate, f"EAC CET {dd_rate}%"),
        }
    ]
    for t in country_cfg["national_taxes"]:
        items.append({
            "tax":         t["code"],
            "rate":        t["rate"],
            "base":        t["base"],
            "methode":     f"{t['base']} × {t['rate']}%",
            "observation": t["authority"],
        })
    # Excise for specific chapters
    excise_rate = country_cfg.get("excise_by_chapter", {}).get(chapter.lstrip("0") or "0")
    if excise_rate:
        items.append({
            "tax":         "EXCISE",
            "rate":        excise_rate,
            "base":        "CIF + DD",
            "methode":     f"(CIF + DD) × {excise_rate}%",
            "observation": f"Accise — chapitre {chapter}",
        })
    items.append({
        "tax":         "T.V.A",
        "rate":        country_cfg["tva_rate"],
        "base":        country_cfg["tva_base"],
        "methode":     f"({country_cfg['tva_base']}) × {country_cfg['tva_rate']}%",
        "observation": country_cfg["tva_name"],
    })
    return items


def build_formalities(iso3: str, chapter: str, hs6: str) -> List[Dict]:
    try:
        from etl.africa_formalities import get_formalities_for_line
        ch_int = int(chapter) if chapter.isdigit() else 0
        cat = _infer_category(ch_int)
        result = get_formalities_for_line({"hs6": hs6, "chapter": chapter}, cat, chapter)
        if result:
            return result
    except Exception:
        pass
    return [
        {
            "code": "IMPDEC",
            "document_fr": "Déclaration d'Importation",
            "document_en": "Import Declaration",
            "authority_fr": f"Customs {EAC_COUNTRIES.get(iso3, {}).get('name', iso3)}",
            "authority_en": f"Customs {iso3}",
            "is_mandatory": True,
        }
    ]


def _infer_category(ch: int) -> str:
    if ch <= 5:  return "livestock"
    if ch <= 15: return "agricultural"
    if ch <= 24: return "food"
    if ch <= 27: return "energy"
    if ch <= 40: return "chemicals"
    if ch <= 63: return "textiles"
    if ch <= 70: return "glass"
    if ch <= 83: return "metals"
    if ch <= 85: return "machinery"
    if ch <= 92: return "vehicles"
    return "general"


def generate_country_file(iso3: str, country_cfg: Dict,
                          hs6_groups: Dict[str, List[Dict]],
                          all_hs6: List[str]) -> None:
    """Generate the tariff file for one EAC country."""

    # Load existing to preserve HS6 list and descriptions
    existing_path = os.path.join(OUTPUT_DIR, f"{iso3}_tariffs.json")
    existing_lines = {}
    if os.path.exists(existing_path):
        with open(existing_path) as f:
            existing = json.load(f)
        for line in existing.get("tariff_lines", []):
            existing_lines[line["hs6"]] = line

    tariff_lines = []
    total_positions = 0
    hs6_without = 0

    union_hs6 = sorted(set(existing_lines.keys()) | set(hs6_groups.keys()) | set(all_hs6))

    for hs6 in union_hs6:
        existing = existing_lines.get(hs6, {})
        nat_positions = hs6_groups.get(hs6, [])
        chapter = (nat_positions[0]["chapter"] if nat_positions
                   else existing.get("chapter", hs6[:2]))
        ch_int = int(chapter) if chapter.isdigit() else 0

        # HS6-level dd_rate = most common among sub-positions
        if nat_positions:
            rate_counts = Counter(p["rate"] for p in nat_positions)
            dd_rate = rate_counts.most_common(1)[0][0]
        else:
            dd_rate = existing.get("dd_rate", 25.0)
            hs6_without += 1

        # Apply sensitive list corrections (override PDF extraction errors)
        if hs6 in SENSITIVE_LIST_DD_CORRECTIONS:
            dd_rate = SENSITIVE_LIST_DD_CORRECTIONS[hs6]

        nat_taxes_sum = sum(t["rate"] for t in country_cfg["national_taxes"])
        excise_rate = country_cfg.get("excise_by_chapter", {}).get(chapter.lstrip("0") or "0", 0)
        # TVA cascade: assiette = CIF + DD + taxes nat + accise (pas seulement CIF+DD)
        total_before_tva = dd_rate + nat_taxes_sum + excise_rate
        tva_base_multiplier = 1.0 + (dd_rate + nat_taxes_sum + excise_rate) / 100
        tva_amount = round(100 * tva_base_multiplier * country_cfg["tva_rate"] / 100, 4)
        full_total = round(total_before_tva + tva_amount, 2)

        taxes = build_taxes_detail(country_cfg, dd_rate, chapter)

        # Build sub-positions (real HS8 from EAC CET)
        sub_positions_out = []
        for p in nat_positions:
            # Apply sensitive list corrections at sub-position level too
            p_dd = SENSITIVE_LIST_DD_CORRECTIONS.get(hs6, p["rate"])
            p_taxes = build_taxes_detail(country_cfg, p_dd, chapter)
            p_excise = country_cfg.get("excise_by_chapter", {}).get(chapter.lstrip("0") or "0", 0)
            p_other = nat_taxes_sum + p_excise
            # Correct cascade: TVA assiette = CIF*(1 + DD + levies + excise)/100 * TVA%
            p_tva_base_mult = 1.0 + (p_dd + p_other) / 100
            p_tva = round(100 * p_tva_base_mult * country_cfg["tva_rate"] / 100, 4)
            sub_positions_out.append({
                "code":           p["code"],
                "national_code":  p["code"],
                "digits":         8,
                "description_fr": p["desc"],
                "description_en": p["desc"],
                "dd_rate":        p_dd,
                "dd_source":      EAC_BAND_LABELS.get(p_dd, f"EAC CET {p_dd}%"),
                "taxes_detail":   p_taxes,
                "total_taxes":    round(p_dd + p_other + p_tva, 2),
                "source":         f"EAC CET 2022 — KRA — {country_cfg['source']}",
            })
            total_positions += 1

        formalities = existing.get("administrative_formalities") or build_formalities(iso3, chapter, hs6)

        line = {
            "hs6":                    hs6,
            "chapter":                chapter,
            "description_fr":         existing.get("description_fr", ""),
            "description_en":         existing.get("description_en", ""),
            "category":               existing.get("category") or _infer_category(ch_int),
            "unit":                   existing.get("unit", "KG"),
            "sensitivity":            "sensitive" if dd_rate >= 50 else ("elevated" if dd_rate >= 25 else "normal"),
            "dd_rate":                dd_rate,
            "dd_source":              f"EAC CET 2022 — {country_cfg['source']}",
            # zlecaf_rate: non disponible — le calendrier de démantèlement ZLECAf officiel
            # (catégories A/B/C, PMA) n'est pas encore publié par pays.
            # Ne pas utiliser cette valeur comme taux réel.
            "zlecaf_rate":            None,
            "zlecaf_rate_note":       "Non disponible — calendrier ZLECAf officiel requis (cat. A/B/C PMA)",
            "vat_rate":               country_cfg["tva_rate"],
            "vat_note":               "Taux standard. Exonérations légales (denrées de base, médicaments, intrants agricoles) non modélisées.",
            "other_taxes_rate":       nat_taxes_sum,
            "taxes_detail":           taxes,
            "total_taxes_pct":        full_total,
            "fiscal_advantages":      existing.get("fiscal_advantages", [
                {
                    "tax": "D.D",
                    "rate": 0.0,
                    "condition_fr": "Certificat d'Origine ZLECAf — Exonération DD (taux réel selon calendrier officiel)",
                    "condition_en": "AfCFTA Certificate of Origin — DD Exemption (actual rate per official schedule)",
                }
            ]),
            "administrative_formalities": formalities,
            "total_import_taxes":     full_total,
            "sub_positions":          sub_positions_out,
            "has_sub_positions":      len(sub_positions_out) > 0,
            "sub_position_count":     len(sub_positions_out),
            "data_source":            "eac_cet_2022_authentic",
            # partial: DD authentique (CET EAC 2022), taxes nat. documentées;
            # TVA uniforme (exonérations non modélisées), zlecaf non disponible.
            "data_quality":           "partial",
        }
        tariff_lines.append(line)

    dd_rates = [l["dd_rate"] for l in tariff_lines]
    output = {
        "country_code": iso3,
        "country_name": country_cfg["name"],
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "data_format":  "national_positions_eac_cet_2022",
        "data_source":  "eac_cet_2022_authentic",
        "source_url":   country_cfg["source_url"],
        "notes":        country_cfg.get("notes", []),
        "summary": {
            "total_tariff_lines":       len(tariff_lines),
            "total_national_positions": total_positions,
            "hs6_with_hs8_positions":   len(tariff_lines) - hs6_without,
            "hs6_without_positions":    hs6_without,
            "vat_rate_pct":             country_cfg["tva_rate"],
            "eac_band_distribution": {
                "0%":  sum(1 for l in tariff_lines if l["dd_rate"] == 0),
                "10%": sum(1 for l in tariff_lines if l["dd_rate"] == 10),
                "25%": sum(1 for l in tariff_lines if l["dd_rate"] == 25),
                "35%": sum(1 for l in tariff_lines if l["dd_rate"] == 35),
                "50%+": sum(1 for l in tariff_lines if l["dd_rate"] >= 50),
            },
            "dd_rate_range": {
                "min": min(dd_rates),
                "max": max(dd_rates),
                "avg": round(sum(dd_rates) / len(dd_rates), 2),
            },
        },
        "tariff_lines": tariff_lines,
    }

    out_path = os.path.join(OUTPUT_DIR, f"{iso3}_tariffs.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, separators=(",", ":"))

    sz = os.path.getsize(out_path) / 1024 / 1024
    logger.info(
        f"{iso3}: {len(tariff_lines)} HS6 | {total_positions} positions HS8 réelles "
        f"| {hs6_without} sans position | {sz:.1f} MB → {out_path}"
    )


def main(countries: Optional[List[str]] = None) -> None:
    logger.info("=== Générateur positions nationales EAC CET 2022 ===")

    if not os.path.exists(PDF_PATH):
        logger.error(f"PDF EAC CET introuvable: {PDF_PATH}")
        sys.exit(1)

    logger.info("Parsing PDF EAC CET 2022 (560 pages)...")
    eac_positions = parse_eac_pdf(PDF_PATH)

    # Save parsed positions for reuse
    cache = "/tmp/eac_cet_positions.json"
    with open(cache, "w") as f:
        json.dump(eac_positions, f)
    logger.info(f"Cache sauvegardé: {cache}")

    hs6_groups = group_by_hs6(eac_positions)
    all_hs6_from_pdf = list(hs6_groups.keys())
    logger.info(f"HS6 couverts par le PDF: {len(all_hs6_from_pdf)}")

    target = countries or list(EAC_COUNTRIES.keys())
    logger.info(f"Pays cibles: {target}")

    for iso3 in target:
        if iso3 not in EAC_COUNTRIES:
            logger.warning(f"Pays non configuré: {iso3}")
            continue
        logger.info(f"Génération {iso3}...")
        generate_country_file(iso3, EAC_COUNTRIES[iso3], hs6_groups, all_hs6_from_pdf)

    logger.info("=== Terminé ===")


if __name__ == "__main__":
    args = sys.argv[1:] or None
    main(args)
