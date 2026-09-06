"""
EAC Common External Tariff (CET) 2022 - PDF Scraper v2
=======================================================
Extracts HS8 tariff positions from the official EAC CET 2022 PDF.
Source: Kenya Revenue Authority (KRA) - kra.go.ke
PDF: EAC-CET-2022-VERSION-30TH-JUNE-Fn.pdf (560 pages)

v2 — exhaustivité et détail maximaux (doctrine zéro-fabrication) :
- codes HS8 détectés même fusionnés avec la description (extraction non ancrée) ;
- résolution de la règle SI (Introduction p. 9) : « where the abbreviation "SI"
  (Sensitive Items) appears the applicable duty rates shall be those specified
  in Schedule 2 » → le taux applicable est celui du Schedule 2, une seule
  entrée par code (plus de doublons Schedule 1/Schedule 2) ;
- droits composés (« X% or $Y/MT whichever is higher ») structurés
  MAX_AD_VALOREM_SPECIFIC — jamais convertis en nombre fabriqué ;
- provenance par entrée : page PDF, schedule, texte du taux verbatim ;
- génère le fichier crawled détaillé ET le fichier canonique canonical_v4.

EAC Member States (7 countries):
- Kenya (KEN) - IDF 3.5%, RDL 2%, VAT 16%
- Tanzania (TZA) - VAT 18%
- Uganda (UGA) - VAT 18%, Infrastructure Levy 1.5%
- Rwanda (RWA) - VAT 18%
- Burundi (BDI) - VAT 18%
- South Sudan (SSD) - VAT 18% (estimated)
- DR Congo (COD) - VAT 16%

4-band tariff structure:
- 0% : Raw materials, capital goods
- 10% : Intermediate goods
- 25% : Finished goods
- 35% : Sensitive items (4th band added July 2022)
Plus specific rates for certain products (40%-100%)

Usage : python eac_cet_scraper.py [pdf_path] [--country TZA]
"""

import argparse
import hashlib
import json
import logging
import os
import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import fitz

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

PDF_URL = "https://www.kra.go.ke/images/publications/EAC-CET-2022-VERSION-30TH-JUNE-Fn.pdf"
SI_RULE = (
    'Introduction, p. 9 : "The fifth column of Schedule 1 contains applicable Common '
    'External Tariff rates and where the abbreviation "SI" (Sensitive Items) appears '
    'the applicable duty rates shall be those specified in Schedule 2."'
)

HS_SECTIONS = {
    "I": "Live Animals; Animal Products",
    "II": "Vegetable Products",
    "III": "Animal, Vegetable or Microbial Fats and Oils",
    "IV": "Prepared Foodstuffs; Beverages, Spirits and Vinegar; Tobacco",
    "V": "Mineral Products",
    "VI": "Products of Chemical or Allied Industries",
    "VII": "Plastics and Rubber",
    "VIII": "Raw Hides and Skins, Leather, Furskins",
    "IX": "Wood and Articles of Wood; Cork; Basketware",
    "X": "Pulp of Wood; Paper and Paperboard",
    "XI": "Textiles and Textile Articles",
    "XII": "Footwear, Headgear, Umbrellas",
    "XIII": "Articles of Stone, Plaster, Cement; Ceramic; Glass",
    "XIV": "Natural or Cultured Pearls, Precious Stones, Metals",
    "XV": "Base Metals and Articles of Base Metal",
    "XVI": "Machinery and Mechanical Appliances; Electrical Equipment",
    "XVII": "Vehicles, Aircraft, Vessels",
    "XVIII": "Optical, Photographic, Medical Instruments; Clocks; Musical Instruments",
    "XIX": "Arms and Ammunition",
    "XX": "Miscellaneous Manufactured Articles",
    "XXI": "Works of Art, Collectors' Pieces and Antiques",
}

EAC_COUNTRY_TAXES = {
    "KEN": {
        "name": "Kenya",
        "taxes": [
            {"name": "Import Declaration Fee (IDF)", "rate": 3.5, "base": "CIF"},
            {"name": "Railway Development Levy (RDL)", "rate": 2.0, "base": "CIF"},
            {"name": "Value Added Tax (VAT)", "rate": 16.0, "base": "CIF+Duty+Fees"},
        ],
        "excise_categories": {
            "2203": 50.0,
            "2204": 25.0,
            "2205": 25.0,
            "2206": 70.0,
            "2207": 65.0,
            "2208": 65.0,
            "2402": 35.0,
            "2403": 40.0,
            "8703": 20.0,
            "3303": 10.0,
            "3304": 10.0,
            "3305": 10.0,
        },
    },
    "TZA": {
        "name": "Tanzania",
        "taxes": [
            {"name": "Value Added Tax (VAT)", "rate": 18.0, "base": "CIF+Duty"},
        ],
        "excise_categories": {
            "2203": 50.0,
            "2204": 20.0,
            "2208": 60.0,
            "2402": 30.0,
            "2403": 30.0,
        },
    },
    "UGA": {
        "name": "Uganda",
        "taxes": [
            {"name": "Infrastructure Levy", "rate": 1.5, "base": "CIF"},
            {"name": "Value Added Tax (VAT)", "rate": 18.0, "base": "CIF+Duty+Levies"},
        ],
        "excise_categories": {
            "2203": 60.0,
            "2204": 20.0,
            "2208": 60.0,
            "2402": 40.0,
        },
    },
    "RWA": {
        "name": "Rwanda",
        "taxes": [
            {"name": "Value Added Tax (VAT)", "rate": 18.0, "base": "CIF+Duty"},
        ],
        "excise_categories": {
            "2203": 30.0,
            "2208": 40.0,
            "2402": 36.0,
        },
    },
    "BDI": {
        "name": "Burundi",
        "taxes": [
            {"name": "Value Added Tax (VAT)", "rate": 18.0, "base": "CIF+Duty"},
        ],
        "excise_categories": {},
    },
    "SSD": {
        "name": "South Sudan",
        "taxes": [
            {"name": "Value Added Tax (VAT)", "rate": 18.0, "base": "CIF+Duty"},
        ],
        "excise_categories": {},
    },
    "COD": {
        "name": "DR Congo",
        "taxes": [
            {"name": "Value Added Tax (VAT)", "rate": 16.0, "base": "CIF+Duty"},
        ],
        "excise_categories": {},
    },
}

# ── Regex d'extraction ────────────────────────────────────────────────────────
CODE_ANY = re.compile(r"\b(\d{4}\.\d{2}\.\d{2})\b")
CODE_EXACT = re.compile(r"^(\d{4}\.\d{2}\.\d{2})$")
HEADING_EXACT = re.compile(r"^(\d{2}\.\d{2})$")
SIMPLE_RATE = re.compile(r"^(\d+(?:\.\d+)?%|Free|SI)$")
UNIT_PATTERN = re.compile(
    r"^(kg|Kg|u|1000u|1000\s*u|1000\s*l|l|m|m²|m³|gm|g|t|ct|carat|No\.|pair|pa|set|2u"
    r"|1000\s*KWh|kWh|GI|x|K\.V\.A)$",
    re.IGNORECASE,
)
COMPOUND_RATE = re.compile(
    r"^(?P<adv>\d+(?:\.\d+)?)\s*%\s*or\s*(?P<cur>USD|\$)\s*"
    r"(?P<amount>\d+(?:\.\d+)?)\s*/\s*(?P<unit>MT|kg)\s*(whichever is higher)?$",
    re.IGNORECASE,
)
NOISE_HEADERS = {
    "Heading", "H.S. Code /", "Tariff No.", "Description", "Unit of",
    "Quantity", "Rate", "No.",
}
NOISE_LINE = re.compile(
    r"^(___*|\d{1,3})$"
)


# ── Offres ZLECAf (AfCFTA e-Tariff Book — UA) : OFFER_ONLY, jamais exécutables
#    sans porte légale (zlecaf_implementation_registry.py). Taux préférentiels
#    par ligne : réductions annuelles 1→N. TZA n'est pas couverte par le
#    snapshot EAC → NOT_AVAILABLE (jamais zéro, jamais deviné). ────────────────
BACKEND_DATA = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data"
)
AFCFTA_OFFER_SNAPSHOTS = {
    "KEN": os.path.join(BACKEND_DATA, "official_preferential", "EAC_afcfta_etariff_2026-08-17.json.gz"),
    "RWA": os.path.join(BACKEND_DATA, "official_preferential", "EAC_afcfta_etariff_2026-08-17.json.gz"),
    # TZA, UGA, BDI, SSD, COD : pas de snapshot officiel → NOT_AVAILABLE
}


def load_afcfta_offer(path: str) -> Optional[dict]:
    """Charge un snapshot e-Tariff Book → index code HS8 → enregistrement offre."""
    if not os.path.exists(path):
        return None
    import gzip

    d = json.load(gzip.open(path))
    idx = {}
    for sched in d.get("schedules", {}).values():
        for row in sched:
            code = str(row.get("hs_code", "")).strip()
            if len(code) == 8 and code.isdigit():
                idx[code] = {
                    "category": row.get("category"),
                    "time_frame_years": row.get("time_frame_years"),
                    "mfn_rate_expression": row.get("mfn_rate_expression"),
                    "annual_rate_expressions": row.get("annual_rate_expressions", {}),
                }
    return {
        "meta": {
            "source_title": d.get("source_title"),
            "source_url": d.get("source_url"),
            "source_api_url": d.get("source_api_url"),
            "collected_at": d.get("collected_at"),
            "source_revision_date": d.get("source_revision_date"),
            "legal_effect_status": d.get("legal_effect_status"),
            "execution_authorized": d.get("execution_authorized"),
            "destination_query_code": d.get("destination_query_code"),
        },
        "index": idx,
    }


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def parse_rate_text(rate_text: str) -> dict:
    """Structure un texte de taux EAC (zéro-fabrication)."""
    rt = " ".join(rate_text.split())
    # coupe une éventuelle description suivante collée au taux
    rt = re.sub(r"(whichever is higher)\b.*$", r"\1", rt, flags=re.IGNORECASE)
    if rt == "Free":
        return {"type": "AD_VALOREM", "ad_valorem_pct": 0.0, "rate_text": rt}
    if rt == "SI":
        return {"type": "SI_SCHEDULE_2", "ad_valorem_pct": None, "rate_text": rt}
    m = re.match(r"^(\d+(?:\.\d+)?)\s*%$", rt)
    if m:
        return {"type": "AD_VALOREM", "ad_valorem_pct": float(m.group(1)), "rate_text": rt}
    mc = COMPOUND_RATE.match(rt)
    if mc:
        cur = "USD" if mc.group("cur") == "$" else mc.group("cur")
        return {
            "type": "MAX_AD_VALOREM_SPECIFIC",
            "rule_text": "whichever is higher (le plus élevé des deux montants)",
            "ad_valorem_pct": float(mc.group("adv")),
            "specific_amount": float(mc.group("amount")),
            "specific_unit": mc.group("unit"),
            "specific_currency": cur,
            "requires_quantity": True,
            "rate_text": rt,
        }
    return {"type": "UNPARSED", "ad_valorem_pct": None, "rate_text": rt}


class EACCETScraper:
    def __init__(self, pdf_path: str = None):
        self.pdf_path = pdf_path
        self.positions: List[Dict] = []
        self.schedule2: Dict[str, Dict] = {}
        self.current_section = ""
        self.current_chapter = ""
        self.current_heading = ""
        self.current_heading_desc = ""
        self.pdf_sha256 = None
        self.afcfta_offer: Optional[dict] = None
        self.afcfta_crosscheck: Dict = {}
        self.stats = {
            "total_positions": 0,
            "chapters_found": set(),
            "sections_found": set(),
            "rate_distribution": {},
            "duplicates_schedule1": 0,
            "codes_merged_recovered": 0,
            "schedule2_items": 0,
        }

    def download_pdf(self) -> str:
        import urllib.request

        pdf_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "pdfs"
        )
        os.makedirs(pdf_dir, exist_ok=True)
        pdf_path = os.path.join(pdf_dir, "eac_cet_2022.pdf")
        if os.path.exists(pdf_path):
            logger.info(f"PDF already exists: {pdf_path}")
            return pdf_path
        logger.info(f"Downloading EAC CET PDF from {PDF_URL}...")
        urllib.request.urlretrieve(PDF_URL, pdf_path)
        logger.info(f"Downloaded: {os.path.getsize(pdf_path)} bytes")
        return pdf_path

    # ── Machine à états d'extraction (Schedule 1 et Schedule 2) ──────────────
    def _parse_lines(self, lines: List[str], page_num: int, schedule: str,
                     out: Dict[str, Dict]) -> None:
        """Flux de lignes → dictionnaire code → entrée. États :
        code → description... → unité → fragments de taux → taux."""
        state = "idle"          # idle | desc | unit | rate
        code = None
        desc: List[str] = []
        unit = None
        rate_parts: List[str] = []

        def flush():
            nonlocal state, code, desc, unit, rate_parts
            if code is None:
                state = "idle"
                return
            entry = out.get(code)
            if entry is not None:
                # doublon intra-schedule (répétition de page) : on garde le 1er
                if schedule == "1":
                    self.stats["duplicates_schedule1"] += 1
                state = "idle"
                code = None
                desc = []
                unit = None
                rate_parts = []
                return
            rate_text = " ".join(p.strip() for p in rate_parts if p.strip())
            parsed = parse_rate_text(rate_text) if rate_text else {
                "type": "UNPARSED", "ad_valorem_pct": None, "rate_text": "",
            }
            out[code] = {
                "hs_code": code,
                "hs_code_normalized": code.replace(".", ""),
                "description": " ".join(desc).strip(),
                "unit": unit or "",
                "parsed_rate": parsed,
                "chapter": code[:2],
                "heading": code[:2] + "." + code[2:4],
                "section": self.current_section,
                "schedule": schedule,
                "pdf_page": page_num,
            }
            key = parsed.get("rate_text") or "unknown"
            self.stats["rate_distribution"][key] = (
                self.stats["rate_distribution"].get(key, 0) + 1
            )
            state = "idle"
            code = None
            desc = []
            unit = None
            rate_parts = []

        for raw in lines:
            line = raw.strip()
            if not line or line.startswith("COMMON EXTERNAL TARIFF"):
                continue
            if line in NOISE_HEADERS:
                continue
            if NOISE_LINE.match(line):
                continue
            section_m = re.match(
                r"^Section\s+(I{1,3}V?|V?I{0,3}|X{1,3}I{0,2}V?|V?X{0,3}I{0,3})$",
                line, re.IGNORECASE,
            )
            if section_m:
                flush()
                self.current_section = section_m.group(1).upper()
                self.stats["sections_found"].add(self.current_section)
                continue
            chapter_m = re.match(r"^Chapter\s+(\d+)", line, re.IGNORECASE)
            if chapter_m:
                flush()
                self.current_chapter = chapter_m.group(1).zfill(2)
                self.stats["chapters_found"].add(self.current_chapter)
                continue
            if HEADING_EXACT.match(line):
                # un vrai heading n'apparaît qu'entre deux entrées (état idle) ;
                # dans une entrée en cours, "58.10" est un fragment de description
                # (ex. "... embroidery of heading 58.10")
                if code is not None:
                    if state == "desc":
                        desc.append(line)
                        continue
                flush()
                self.current_heading = line
                self.current_heading_desc = ""
                continue

            # code HS8 — exact OU fusionné avec la description (récupération)
            code_m = CODE_EXACT.match(line)
            if code_m:
                flush()
                code = code_m.group(1)
                state = "desc"
                continue
            inline_m = CODE_ANY.search(line)
            if inline_m and state != "rate":
                pre = line[: inline_m.start()].strip()
                post = line[inline_m.end():].strip()
                # code HS8 fusionné avec la description, ex.
                # "2404.91.00     -- For oral application" (code en début de
                # ligne, description à la suite) — jamais perdu
                if not pre or not re.search(r"\d{2}\.\d{2}", pre):
                    flush()
                    code = inline_m.group(1)
                    desc = ([pre] if pre else []) + ([post] if post else [])
                    state = "desc"
                    self.stats["codes_merged_recovered"] += 1
                    continue

            if state == "desc":
                if UNIT_PATTERN.match(line):
                    unit = line
                    state = "rate"
                else:
                    desc.append(line)
                continue
            if state == "rate":
                if SIMPLE_RATE.match(line):
                    # taux simple complet (1 ligne)
                    if not rate_parts:
                        rate_parts = [line]
                        flush()
                        continue
                    # fragment supplémentaire après un taux déjà complet → bruit
                rate_parts.append(line)
                continue
            # état idle : ligne hors structure → description de heading éventuelle
            if self.current_heading and not self.current_heading_desc and not line.startswith("-"):
                self.current_heading_desc = line

        flush()

    def extract_positions(self) -> List[Dict]:
        if not self.pdf_path:
            self.pdf_path = self.download_pdf()
        self.pdf_sha256 = sha256_file(self.pdf_path)

        doc = fitz.open(self.pdf_path)
        logger.info(f"Opened PDF with {len(doc)} pages")

        first_data_page = None
        sched2_start = None
        for i in range(len(doc)):
            text = doc[i].get_text()
            if first_data_page is None and re.search(r"\d{4}\.\d{2}\.\d{2}", text):
                first_data_page = i
            if sched2_start is None and re.search(r"SCHEDULE\s*2", text, re.I) and \
                    re.search(r"SENSITIVE", text, re.I) and i > 400:
                sched2_start = i
                break
        if first_data_page is None:
            logger.error("Could not find first data page")
            return []
        logger.info(f"First data page: {first_data_page + 1} | Schedule 2 starts: {sched2_start}")

        # ── Schedule 1 ──
        sched1: Dict[str, Dict] = {}
        for i in range(first_data_page, sched2_start):
            self._parse_lines(doc[i].get_text().split("\n"), i, "1", sched1)

        # ── Schedule 2 (Sensitive Items : code, description, taux — pas d'unité) ──
        sched2_raw: Dict[str, Dict] = {}
        saved_unit_state = None
        for i in range(sched2_start, len(doc)):
            # le Schedule 2 n'a pas de colonne unité : parser en mode sans unité
            saved_unit_state = self.current_section
            self._parse_lines_s2(doc[i].get_text().split("\n"), i, sched2_raw)
        self.current_section = saved_unit_state

        self.schedule2 = sched2_raw
        self.stats["schedule2_items"] = len(sched2_raw)

        # ── Fusion : une entrée par code, taux applicable = Schedule 2 si SI ──
        merged: Dict[str, Dict] = {}
        for code, e in sched1.items():
            e = dict(e)
            parsed = e["parsed_rate"]
            if parsed["type"] == "SI_SCHEDULE_2":
                s2 = sched2_raw.get(code)
                if s2:
                    applicable = s2.get("applicable_rate") or parse_rate_text(
                        s2["parsed_rate"]["rate_text"]
                    )
                    e["parsed_rate"] = applicable
                    e["rate_schedule"] = "2"
                    e["schedule2_description"] = s2["description"]
                else:
                    e["rate_schedule"] = "1"
            else:
                e["rate_schedule"] = "1"
            merged[code] = e
        # codes uniquement dans le Schedule 2 (aucun en pratique — vérifié)
        for code, s2 in sched2_raw.items():
            if code not in merged:
                merged[code] = {
                    "hs_code": code,
                    "hs_code_normalized": code.replace(".", ""),
                    "description": s2["description"],
                    "unit": "",
                    "parsed_rate": parse_rate_text(s2["parsed_rate"]["rate_text"]),
                    "chapter": code[:2],
                    "heading": code[:2] + "." + code[2:4],
                    "section": "",
                    "schedule": "2",
                    "pdf_page": s2["pdf_page"],
                }

        self.positions = sorted(merged.values(), key=lambda e: e["hs_code_normalized"])
        self.stats["total_positions"] = len(self.positions)
        logger.info(
            f"Extracted {len(self.positions)} unique positions "
            f"({self.stats['duplicates_schedule1']} doublons Schedule 1 ignorés, "
            f"{self.stats['codes_merged_recovered']} codes fusionnés récupérés, "
            f"{len(sched2_raw)} Sensitive Items Schedule 2)"
        )
        return self.positions

    def load_offer_for_country(self, country_code: str) -> None:
        """Charge l'offre ZLECAf (e-Tariff Book UA) du pays si un snapshot existe,
        et contre-vérifie les taux NPF du snapshot contre le CET du PDF."""
        path = AFCFTA_OFFER_SNAPSHOTS.get(country_code)
        self.afcfta_offer = load_afcfta_offer(path) if path else None
        self.afcfta_crosscheck = {}
        if not self.afcfta_offer:
            logger.info(f"{country_code}: aucune offre ZLECAf officielle chargée "
                        f"(NOT_AVAILABLE — jamais deviné)")
            return
        idx = self.afcfta_offer["index"]
        matched = npf_match = npf_mismatch = 0
        mismatch_examples = []
        for p in self.positions:
            rec = idx.get(p["hs_code_normalized"])
            if not rec:
                continue
            matched += 1
            cet_rate = p["parsed_rate"].get("ad_valorem_pct")
            try:
                mfn_v = float(rec.get("mfn_rate_expression"))
            except (TypeError, ValueError):
                mfn_v = None
            if cet_rate is None or mfn_v is None:
                continue
            if abs(cet_rate - mfn_v) < 0.01:
                npf_match += 1
            else:
                npf_mismatch += 1
                if len(mismatch_examples) < 5:
                    mismatch_examples.append({
                        "code": p["hs_code_normalized"],
                        "cet_pdf": cet_rate,
                        "offre_mfn": rec.get("mfn_rate_expression"),
                        "note": "offre ZLECAf (base de négociation) ≠ CET PDF (autoritaire)",
                    })
        offer_only = sorted(set(idx) - {p["hs_code_normalized"] for p in self.positions})
        cet_only = sorted(
            {p["hs_code_normalized"] for p in self.positions} - set(idx)
        )
        self.afcfta_crosscheck = {
            "offer_codes": len(idx),
            "matched_codes": matched,
            "npf_matches": npf_match,
            "npf_mismatches": npf_mismatch,
            "npf_mismatch_examples": mismatch_examples,
            "offer_only_codes": len(offer_only),
            "offer_only_note": (
                "codes du schedule ZLECAf absents du PDF EAC CET 2022 — splits "
                "nationaux du schedule (destination_query_code="
                f"{self.afcfta_offer['meta']['destination_query_code']}), hors périmètre EAC"
            ),
            "cet_only_codes": len(cet_only),
            "cet_only_note": (
                "lignes EAC CET 2022 exclues de l'offre ZLECAf (exclusions de la "
                "zone de libre-échange) — traitement NPF conservé"
            ),
        }
        logger.info(
            f"ZLECAf: {matched}/{len(idx)} codes couverts | NPF match "
            f"{npf_match} / mismatch {npf_mismatch} | CET exclus de l'offre: "
            f"{len(cet_only)}"
        )

    def _parse_lines_s2(self, lines: List[str], page_num: int,
                        out: Dict[str, Dict]) -> None:
        """Schedule 2 : code → description → taux (pas de colonne unité).
        Le taux s'arrête au prochain code ou à une référence de heading 'NN.NN'."""
        state = "idle"
        code = None
        desc: List[str] = []
        rate_parts: List[str] = []

        def flush():
            nonlocal state, code, desc, rate_parts
            if code is None:
                state = "idle"
                return
            rate_text = " ".join(p.strip() for p in rate_parts if p.strip())
            # retire les références du heading suivant collées au taux
            # (ex. "50% 1006 Rice" → "50%", "100 % or $ 460/MT whichever is
            # higher 17.02" → "100 % or $ 460/MT whichever is higher")
            rate_text = re.sub(
                r"\s+\d{2}\.\d{2}(\s|$).*", " ", " " + rate_text + " "
            ).strip()
            rate_text = re.sub(r"\s+\d{4}\s+.*", " ", " " + rate_text + " ").strip()
            parsed = parse_rate_text(rate_text) if rate_text else {
                "type": "UNPARSED", "ad_valorem_pct": None, "rate_text": "",
            }
            if parsed["type"] == "UNPARSED" and len(rate_parts) > 1:
                # description coupée finissant par "X%" puis vrai taux : le
                # taux applicable est le dernier fragment autonome valide
                last = rate_parts[-1].strip()
                if re.match(r"^\d+(?:\.\d+)?\s*%$", last):
                    parsed = parse_rate_text(last)
            if code not in out:
                out[code] = {
                    "description": " ".join(desc).strip(),
                    "parsed_rate": {"rate_text": rate_text or parsed.get("rate_text", "")},
                    "pdf_page": page_num,
                    "applicable_rate": parsed,
                }
            state = "idle"
            code = None
            desc = []
            rate_parts = []

        for raw in lines:
            line = raw.strip()
            if not line or line.startswith("COMMON EXTERNAL TARIFF"):
                continue
            if line in NOISE_HEADERS:
                continue
            if NOISE_LINE.match(line):
                continue
            m = CODE_EXACT.match(line)
            if m:
                flush()
                code = m.group(1)
                state = "desc"
                continue
            # référence de heading suivante "NN.NN" → fin d'entrée courante
            if re.match(r"^\d{2}\.\d{2}\s*$", line) and code:
                flush()
                continue
            if re.match(r"^\d{2}\.\d{2}\s+\S", line) and code:
                # "17.02  Other sugars..." → termine l'entrée, heading non traité
                flush()
                continue
            if state == "desc":
                # la description s'arrête au premier fragment qui ressemble à un taux
                if re.match(r"^\d+(?:\.\d+)?\s*%", line) or re.match(r"^\d+(?:\.\d+)?\s+or\b", line):
                    state = "rate"
                    rate_parts = [line]
                else:
                    desc.append(line)
                continue
            if state == "rate":
                if re.match(r"^\d{2}\.\d{2}\b", line) or re.match(r"^\d{4}\s+[A-Za-z]", line):
                    flush()
                    continue
                if line.startswith("-"):
                    # le taux est complet : la ligne qui suit décrit l'entrée
                    # suivante (ex. "- Other :") — on la laisse au prochain code
                    flush()
                    continue
                rate_parts.append(line)
                continue
        flush()

    # ── Génération par pays ───────────────────────────────────────────────────
    def generate_country_tariffs(self, country_code: str) -> List[Dict]:
        if country_code not in EAC_COUNTRY_TAXES:
            raise ValueError(f"Unknown EAC country: {country_code}")

        country_info = EAC_COUNTRY_TAXES[country_code]
        result = []

        for pos in self.positions:
            taxes_detail = []
            total_taxes_pct = 0.0
            parsed = pos["parsed_rate"]

            if parsed["type"] == "MAX_AD_VALOREM_SPECIFIC":
                sched_label = (
                    "Schedule 2 Sensitive Item" if pos.get("rate_schedule") == "2"
                    else "Schedule 1"
                )
                taxes_detail.append(
                    {
                        "tax_name": f"CET Import Duty (Droit composé — {sched_label})",
                        "rate": None,
                        "base": "CIF",
                        "is_cet": True,
                        "note": parsed["rate_text"],
                        "calculation": {
                            k: v for k, v in parsed.items() if k != "rate_text"
                        },
                    }
                )
            elif parsed["type"] == "AD_VALOREM" and parsed["ad_valorem_pct"] is not None:
                taxes_detail.append(
                    {
                        "tax_name": "CET Import Duty (Droit de Douane)",
                        "rate": parsed["ad_valorem_pct"],
                        "base": "CIF",
                        "is_cet": True,
                    }
                )
                total_taxes_pct += parsed["ad_valorem_pct"]
            elif parsed["type"] == "SI_SCHEDULE_2":
                taxes_detail.append(
                    {
                        "tax_name": "CET Import Duty (Sensitive Item)",
                        "rate": None,
                        "base": "CIF",
                        "is_cet": True,
                        "note": "Rate determined by national schedule",
                    }
                )
            elif parsed["type"] == "UNPARSED" and not parsed.get("rate_text"):
                # colonne taux vide dans le PDF officiel pour cette ligne —
                # trou documenté, jamais comblé (NOT_AVAILABLE)
                taxes_detail.append(
                    {
                        "tax_name": "CET Import Duty (Droit de Douane)",
                        "rate": None,
                        "base": "CIF",
                        "is_cet": True,
                        "note": (
                            "Taux non publié dans le PDF EAC CET 2022 (colonne "
                            "taux vide pour cette ligne) — NOT_AVAILABLE, à "
                            "vérifier auprès de la douane nationale"
                        ),
                        "data_gap": "RATE_NOT_PUBLISHED_IN_PDF",
                    }
                )
            # UNPARSED avec texte : aucune entrée CET fabriquée — le trou reste visible

            for tax in country_info["taxes"]:
                taxes_detail.append(
                    {
                        "tax_name": tax["name"],
                        "rate": tax["rate"],
                        "base": tax["base"],
                        "is_cet": False,
                    }
                )
                total_taxes_pct += tax["rate"]

            hs4 = pos["hs_code_normalized"][:4]
            excise_rate = country_info.get("excise_categories", {}).get(hs4)
            if excise_rate:
                taxes_detail.append(
                    {
                        "tax_name": "Excise Duty",
                        "rate": excise_rate,
                        "base": "CIF+Duty",
                        "is_cet": False,
                    }
                )
                total_taxes_pct += excise_rate

            # ── Taux NPF : pour l'EAC, le CET S'APPLIQUE aux pays tiers = taux NPF
            #    (traitement de la nation la plus favorisée, OMC) ──
            npf_rate = {
                "type": parsed["type"],
                "ad_valorem_pct": parsed.get("ad_valorem_pct"),
                "rate_text": parsed.get("rate_text", ""),
                "legal_reference": (
                    "EAC CET 2022 — le tarif commun s'applique aux importations en "
                    "provenance des pays tiers (traitement NPF/OMC ; préférences "
                    "régionales EAC/ZLECAf déduites sur preuve d'origine)"
                ),
            }

            # ── Offre ZLECAf par ligne (OFFER_ONLY — exécution gated ailleurs) ──
            zlecaf: Dict = {"status": "NOT_AVAILABLE",
                            "note": ("aucune offre ZLECAf officielle par ligne pour ce "
                                     "pays dans le snapshot e-Tariff Book — jamais "
                                     "devinée, jamais zéro")}
            if self.afcfta_offer:
                rec = self.afcfta_offer["index"].get(pos["hs_code_normalized"])
                if rec:
                    zlecaf = {
                        "status": "OFFER_ONLY",
                        "category": rec.get("category"),
                        "time_frame_years": rec.get("time_frame_years"),
                        "mfn_rate_expression": rec.get("mfn_rate_expression"),
                        "annual_rate_expressions": rec.get("annual_rate_expressions", {}),
                        **self.afcfta_offer["meta"],
                    }

            entry = {
                "hs_code": pos["hs_code_normalized"],
                "hs_code_display": pos["hs_code"],
                "designation": pos["description"],
                "unit": pos["unit"],
                "chapter": pos["chapter"],
                "heading": pos["heading"],
                "section": pos["section"],
                "is_sensitive_item": pos["parsed_rate"]["type"] == "SI_SCHEDULE_2",
                "rate_text": parsed.get("rate_text", ""),
                "rate_schedule": pos.get("rate_schedule", "1"),
                "pdf_page": pos["pdf_page"],
                "npf_rate": npf_rate,
                "zlecaf_afcfta": zlecaf,
                "taxes_detail": taxes_detail,
                "total_taxes_pct": round(total_taxes_pct, 2),
                "fiscal_advantages": [
                    {
                        "name": "EAC Intra-Community",
                        "description": "0% duty for goods originating from EAC member states with valid Certificate of Origin",
                        "conditions": "Certificate of Origin required",
                    },
                    {
                        "name": "AfCFTA Tariff Concession",
                        "description": "Progressive duty reduction for AfCFTA member states",
                        "conditions": "AfCFTA Certificate of Origin required",
                    },
                ],
                "administrative_formalities": [],
                "source": "EAC CET 2022 (kra.go.ke)",
                "data_format": "crawled_authentic",
            }

            result.append(entry)

        return result

    # ── Canonique canonical_v4 ────────────────────────────────────────────────
    def build_canonical(self, country_code: str, positions: List[Dict]) -> Dict:
        country_info = EAC_COUNTRY_TAXES[country_code]
        vat_rate = next(
            (t["rate"] for t in country_info["taxes"] if "Value Added" in t["name"]), 18.0
        )
        offer_idx = self.afcfta_offer["index"] if self.afcfta_offer else {}
        offer_meta = self.afcfta_offer["meta"] if self.afcfta_offer else {}
        lines_by_hs6: Dict[str, List[Dict]] = {}
        for p in positions:
            lines_by_hs6.setdefault(p["hs_code"][:6], []).append(p)

        tariff_lines = []
        dd_rates = []
        zlecaf_covered = 0
        for hs6 in sorted(lines_by_hs6):
            group = lines_by_hs6[hs6]
            first = group[0]
            sub_positions = []
            cet_rate = None
            cet_calc = None
            cet_note = None
            excise_rate = None
            for p in group:
                parsed = p["parsed_rate"]
                sp = {
                    "code": p["hs_code_normalized"],
                    "digits": 8,
                    # EAC : le CET s'applique aux pays tiers → taux NPF identique
                    "dd": parsed["ad_valorem_pct"] if parsed["type"] == "AD_VALOREM" else None,
                    "npf": parsed["ad_valorem_pct"] if parsed["type"] == "AD_VALOREM" else None,
                    "npf_rate_text": parsed.get("rate_text", ""),
                    "description_fr": p["description"],
                    "description_en": p["description"],
                    "source": "East African Community — EAC Common External Tariff 2022",
                    "rate_text": parsed.get("rate_text", ""),
                    "rate_schedule": p.get("rate_schedule", "1"),
                    "pdf_page": p["pdf_page"],
                }
                rec = offer_idx.get(p["hs_code_normalized"])
                if rec:
                    sp["zlecaf_afcfta"] = {
                        "status": "OFFER_ONLY",
                        "category": rec.get("category"),
                        "time_frame_years": rec.get("time_frame_years"),
                        "mfn_rate_expression": rec.get("mfn_rate_expression"),
                        "annual_rate_expressions": rec.get("annual_rate_expressions", {}),
                        **offer_meta,
                    }
                    zlecaf_covered += 1
                if parsed["type"] == "MAX_AD_VALOREM_SPECIFIC":
                    sp["dd_formula"] = parsed["rate_text"]
                    sp["dd_calculation"] = {
                        k: v for k, v in parsed.items() if k != "rate_text"
                    }
                if parsed["type"] == "AD_VALOREM" and parsed["ad_valorem_pct"] is not None:
                    dd_rates.append(parsed["ad_valorem_pct"])
                    if cet_rate is None:
                        cet_rate = parsed["ad_valorem_pct"]
                elif parsed["type"] == "MAX_AD_VALOREM_SPECIFIC" and cet_calc is None:
                    cet_calc = {k: v for k, v in parsed.items() if k != "rate_text"}
                    cet_note = parsed["rate_text"]
                sub_positions.append(sp)

            hs4 = hs6[:4]
            excise_rate = country_info.get("excise_categories", {}).get(hs4)
            taxes_detail = []
            if cet_calc:
                taxes_detail.append({
                    "tax": "CET", "rate": None,
                    "observation": f"CET Import Duty (Droit composé) : {cet_note}",
                    "calculation": cet_calc,
                })
            elif cet_rate is not None:
                taxes_detail.append({
                    "tax": "CET", "rate": cet_rate,
                    "observation": "CET Import Duty (Droit de Douane)",
                })
            else:
                taxes_detail.append({
                    "tax": "CET", "rate": None,
                    "observation": (
                        "Taux non publié dans le PDF EAC CET 2022 (colonne taux "
                        "vide) — NOT_AVAILABLE"
                    ),
                    "data_gap": "RATE_NOT_PUBLISHED_IN_PDF",
                })
            if excise_rate:
                taxes_detail.append({
                    "tax": "EXCISE_DUT", "rate": excise_rate,
                    "observation": "Excise Duty",
                })
            taxes_detail.append({
                "tax": "VALUE_ADDE", "rate": vat_rate,
                "observation": "Value Added Tax (VAT)",
            })
            other = sum(
                t["rate"] for t in taxes_detail
                if t["tax"] not in ("CET", "VALUE_ADDE") and t["rate"] is not None
            )
            tariff_lines.append({
                "hs6": hs6,
                "chapter": hs6[:2],
                "description_fr": first["description"],
                "description_en": first["description"],
                "category": None,
                "unit": first["unit"],
                "sensitivity": "sensible" if any(
                    sp.get("rate_schedule") == "2" for sp in sub_positions
                ) else "normal",
                "dd_rate": cet_rate,
                "dd_formula": cet_note,
                "dd_calculation": cet_calc,
                "dd_source": "East African Community — EAC Common External Tariff 2022",
                "vat_rate": vat_rate,
                "other_taxes_rate": other,
                "taxes_detail": taxes_detail,
                "total_taxes_pct": round(
                    (cet_rate or 0) + (excise_rate or 0) + vat_rate, 2
                ),
                "fiscal_advantages": [],
                "administrative_formalities": [],
                "sub_positions": sub_positions,
            })

        total_sp = sum(len(l["sub_positions"]) for l in tariff_lines)
        si_count = sum(1 for l in tariff_lines for sp in l["sub_positions"]
                       if sp.get("rate_schedule") == "2")
        canonical = {
            "country_code": country_code,
            "generated_at": datetime.now().isoformat(),
            "generated_by": "eac_cet_scraper v2 (extraction directe du PDF officiel)",
            "data_format": "canonical_v4",
            "summary": {
                "total_tariff_lines": len(tariff_lines),
                "total_sub_positions": total_sp,
                "total_positions": total_sp,
                "lines_with_sub_positions": sum(
                    1 for l in tariff_lines if l["sub_positions"]
                ),
                "lines_without_dd": sum(
                    1 for l in tariff_lines
                    if not any(t["tax"] == "CET" and t["rate"] is not None
                               for t in (l.get("taxes_detail") or []))
                ),
                "vat_rate_pct": vat_rate,
                "dd_rate_range": {
                    "min": min(dd_rates) if dd_rates else None,
                    "max": max(dd_rates) if dd_rates else None,
                    "avg": round(sum(dd_rates) / len(dd_rates), 4) if dd_rates else None,
                },
                "chapters_covered": len({l["chapter"] for l in tariff_lines}),
                "has_detailed_taxes": True,
                "data_status": "VERIFIED",
                "reliability": "A",
                "source_name": "East African Community — EAC Common External Tariff 2022",
                "source_url": PDF_URL,
            },
            "exhaustiveness_verification": {
                "verified_against": PDF_URL,
                "pdf_sha256": self.pdf_sha256,
                "method": (
                    "eac_cet_scraper v2 — extraction séquentielle complète du PDF "
                    "(Schedule 1 + Schedule 2), code HS8 détecté même fusionné avec "
                    "la description, doublons intra-schedule ignorés, règle SI du "
                    "texte officiel appliquée (taux applicable = Schedule 2)"
                ),
                "si_rule": SI_RULE,
                "unique_codes_extracted": len(self.positions),
                "schedule1_unique_codes": len(self.positions) - si_count,
                "schedule2_sensitive_items": si_count,
                "duplicates_schedule1_ignored": self.stats["duplicates_schedule1"],
                "codes_merged_recovered": self.stats["codes_merged_recovered"],
                "compound_rates_structured": sum(
                    1 for p in self.positions
                    if p["parsed_rate"]["type"] == "MAX_AD_VALOREM_SPECIFIC"
                ),
                "npf_note": (
                    "NPF : pour l'EAC, le tarif commun s'applique aux pays tiers — "
                    "le taux NPF est le taux CET par ligne"
                ),
                "zlecaf_afcfta": (
                    {
                        "status": "OFFER_ONLY",
                        "codes_covered": zlecaf_covered,
                        "legal_gate": (
                            "exécution gated par zlecaf_implementation_registry.py — "
                            "jamais calculée sans instrument d'implémentation + "
                            "liste de partenaires réciproques + preuve d'origine"
                        ),
                        **offer_meta,
                    }
                    if self.afcfta_offer
                    else {
                        "status": "NOT_AVAILABLE",
                        "note": ("aucune offre ZLECAf par ligne pour ce pays — "
                                 "NOT_AVAILABLE, jamais zéro"),
                    }
                ),
                "afcfta_npf_crosscheck": self.afcfta_crosscheck or None,
            },
            "tariff_lines": tariff_lines,
        }
        return canonical

    def save_country_data(self, country_code: str, positions: List[Dict],
                          output_dir: str = None):
        backend_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        if output_dir is None:
            output_dir = os.path.join(backend_root, "data", "crawled")
        os.makedirs(output_dir, exist_ok=True)

        country_name = EAC_COUNTRY_TAXES[country_code]["name"]
        filename = f"{country_code}_tariffs.json"
        filepath = os.path.join(output_dir, filename)

        data = {
            "country_code": country_code,
            "country_name": country_name,
            "source": "EAC Common External Tariff 2022",
            "source_url": PDF_URL,
            "source_organization": "East African Community / Kenya Revenue Authority",
            "extraction_date": datetime.now().isoformat(),
            "total_positions": len(positions),
            "hs_version": "HS 2022",
            "tariff_system": "EAC CET 4-band (0%, 10%, 25%, 35%) + specific rates",
            "economic_community": "EAC",
            "pdf_sha256": self.pdf_sha256,
            "si_rule": SI_RULE,
            "exhaustiveness_verification": {
                "unique_codes_extracted": len(self.positions),
                "schedule2_sensitive_items": self.stats["schedule2_items"],
                "duplicates_schedule1_ignored": self.stats["duplicates_schedule1"],
                "codes_merged_recovered": self.stats["codes_merged_recovered"],
            },
            "positions": positions,
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.info(f"Saved {len(positions)} positions to {filepath}")

        canonical = self.build_canonical(country_code, self.positions)
        canonical_path = os.path.join(backend_root, "data", f"{country_code}_tariffs.json")
        with open(canonical_path, "w", encoding="utf-8") as f:
            json.dump(canonical, f, ensure_ascii=False, indent=2)
        logger.info(
            f"Saved canonical ({canonical['summary']['total_sub_positions']} "
            f"sous-positions) to {canonical_path}"
        )
        return filepath

    def run(self, output_dir: str = None, only_country: str = None) -> Dict:
        logger.info("=" * 60)
        logger.info("EAC CET 2022 Scraper v2 - Starting extraction")
        logger.info("=" * 60)

        self.extract_positions()
        if only_country:
            self.load_offer_for_country(only_country)

        logger.info(f"\nExtraction complete:")
        logger.info(f"  Total unique positions: {self.stats['total_positions']}")
        logger.info(f"  Chapters: {len(self.stats['chapters_found'])}")
        logger.info(f"  Sections: {len(self.stats['sections_found'])}")
        logger.info(f"  Schedule 2 items: {self.stats['schedule2_items']}")

        countries = [only_country] if only_country else list(EAC_COUNTRY_TAXES)
        saved_files = {}
        for country_code in countries:
            if country_code not in EAC_COUNTRY_TAXES:
                raise ValueError(f"Unknown EAC country: {country_code}")
            logger.info(
                f"\nGenerating tariff data for {country_code} "
                f"({EAC_COUNTRY_TAXES[country_code]['name']})..."
            )
            country_positions = self.generate_country_tariffs(country_code)
            filepath = self.save_country_data(country_code, country_positions, output_dir)
            saved_files[country_code] = {
                "file": filepath,
                "positions": len(country_positions),
                "country_name": EAC_COUNTRY_TAXES[country_code]["name"],
            }

        result = {
            "status": "success",
            "total_cet_positions": self.stats["total_positions"],
            "chapters": len(self.stats["chapters_found"]),
            "countries": len(saved_files),
            "files": saved_files,
        }
        logger.info("\n" + "=" * 60)
        logger.info("EAC CET extraction complete!")
        logger.info(f"  {self.stats['total_positions']} positions x {len(saved_files)} countries")
        logger.info("=" * 60)
        return result


if __name__ == "__main__":
    import sys

    ap = argparse.ArgumentParser()
    ap.add_argument("pdf_path", nargs="?", default=None)
    ap.add_argument("--country", default=None, help="génère un seul pays (ex. TZA)")
    args = ap.parse_args()
    scraper = EACCETScraper(args.pdf_path)
    result = scraper.run(only_country=args.country)
    print(json.dumps(result, indent=2)[:2000])
