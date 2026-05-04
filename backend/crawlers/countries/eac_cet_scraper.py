"""
EAC Common External Tariff (CET) 2022 - PDF Scraper
=====================================================
Extracts HS8 tariff positions from the official EAC CET 2022 PDF.
Source: Kenya Revenue Authority (KRA) - kra.go.ke
PDF: EAC-CET-2022-VERSION-30TH-JUNE-Fn.pdf (560 pages)

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

Output: HS8 positions with CET duty rate + country-specific taxes
"""

import fitz
import re
import json
import os
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

PDF_URL = "https://www.kra.go.ke/images/publications/EAC-CET-2022-VERSION-30TH-JUNE-Fn.pdf"

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
            "2203": 50.0, "2204": 25.0, "2205": 25.0, "2206": 70.0, "2207": 65.0, "2208": 65.0,
            "2402": 35.0, "2403": 40.0,
            "8703": 20.0,
            "3303": 10.0, "3304": 10.0, "3305": 10.0,
        }
    },
    "TZA": {
        "name": "Tanzania",
        "taxes": [
            {"name": "Value Added Tax (VAT)", "rate": 18.0, "base": "CIF+Duty"},
        ],
        "excise_categories": {
            "2203": 50.0, "2204": 20.0, "2208": 60.0,
            "2402": 30.0, "2403": 30.0,
        }
    },
    "UGA": {
        "name": "Uganda",
        "taxes": [
            {"name": "Infrastructure Levy", "rate": 1.5, "base": "CIF"},
            {"name": "Value Added Tax (VAT)", "rate": 18.0, "base": "CIF+Duty+Levies"},
        ],
        "excise_categories": {
            "2203": 60.0, "2204": 20.0, "2208": 60.0,
            "2402": 40.0,
        }
    },
    "RWA": {
        "name": "Rwanda",
        "taxes": [
            {"name": "Value Added Tax (VAT)", "rate": 18.0, "base": "CIF+Duty"},
        ],
        "excise_categories": {
            "2203": 30.0, "2208": 40.0,
            "2402": 36.0,
        }
    },
    "BDI": {
        "name": "Burundi",
        "taxes": [
            {"name": "Value Added Tax (VAT)", "rate": 18.0, "base": "CIF+Duty"},
        ],
        "excise_categories": {}
    },
    "SSD": {
        "name": "South Sudan",
        "taxes": [
            {"name": "Value Added Tax (VAT)", "rate": 18.0, "base": "CIF+Duty"},
        ],
        "excise_categories": {}
    },
    "COD": {
        "name": "DR Congo",
        "taxes": [
            {"name": "Value Added Tax (VAT)", "rate": 16.0, "base": "CIF+Duty"},
        ],
        "excise_categories": {}
    },
}


class EACCETScraper:
    def __init__(self, pdf_path: str = None):
        self.pdf_path = pdf_path
        self.positions = []
        self.current_section = ""
        self.current_chapter = ""
        self.current_heading = ""
        self.current_heading_desc = ""
        self.stats = {
            "total_positions": 0,
            "chapters_found": set(),
            "sections_found": set(),
            "rate_distribution": {},
        }

    def download_pdf(self) -> str:
        import urllib.request
        pdf_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "pdfs")
        os.makedirs(pdf_dir, exist_ok=True)
        pdf_path = os.path.join(pdf_dir, "eac_cet_2022.pdf")
        if os.path.exists(pdf_path):
            logger.info(f"PDF already exists: {pdf_path}")
            return pdf_path
        logger.info(f"Downloading EAC CET PDF from {PDF_URL}...")
        urllib.request.urlretrieve(PDF_URL, pdf_path)
        logger.info(f"Downloaded: {os.path.getsize(pdf_path)} bytes")
        return pdf_path

    def parse_rate(self, rate_str: str) -> Optional[float]:
        rate_str = rate_str.strip()
        if rate_str == "Free" or rate_str == "0%":
            return 0.0
        if rate_str == "SI":
            return None
        match = re.match(r'^(\d+(?:\.\d+)?)%$', rate_str)
        if match:
            return float(match.group(1))
        return None

    def extract_positions(self) -> List[Dict]:
        if not self.pdf_path:
            self.pdf_path = self.download_pdf()

        doc = fitz.open(self.pdf_path)
        logger.info(f"Opened PDF with {len(doc)} pages")

        first_data_page = None
        for i in range(len(doc)):
            text = doc[i].get_text()
            if re.search(r'\d{4}\.\d{2}\.\d{2}', text):
                first_data_page = i
                break

        if first_data_page is None:
            logger.error("Could not find first data page")
            return []

        logger.info(f"First data page: {first_data_page + 1}")

        section_pattern = re.compile(r'^Section\s+(I{1,3}V?|V?I{0,3}|X{1,3}I{0,2}V?|V?X{0,3}I{0,3})$', re.IGNORECASE)
        chapter_pattern = re.compile(r'^Chapter\s+(\d+)', re.IGNORECASE)
        heading_pattern = re.compile(r'^(\d{2}\.\d{2})$')
        hs8_pattern = re.compile(r'^(\d{4}\.\d{2}\.\d{2})$')
        rate_pattern = re.compile(r'^(\d+(?:\.\d+)?%|Free|SI)$')
        unit_pattern = re.compile(r'^(kg|u|l|m|m2|m3|1000\s*u|1000\s*l|GI|ct|No\.|pair|pa|g|set|m/s|t|kWh|1000\s*kWh|2u)$', re.IGNORECASE)

        pending_hs = None
        pending_desc_lines = []
        pending_unit = None

        for page_num in range(first_data_page, len(doc)):
            page = doc[page_num]
            text = page.get_text()
            lines = text.split('\n')

            for line in lines:
                line_stripped = line.strip()
                if not line_stripped:
                    continue
                if line_stripped.startswith("COMMON EXTERNAL TARIFF"):
                    continue
                if line_stripped in ("Heading", "H.S. Code /", "Tariff No.", "Description", "Unit of", "Quantity", "Rate"):
                    continue
                if re.match(r'^\d+$', line_stripped) and len(line_stripped) <= 3:
                    continue

                section_m = section_pattern.match(line_stripped)
                if section_m:
                    self.current_section = section_m.group(1).upper()
                    self.stats["sections_found"].add(self.current_section)
                    continue

                chapter_m = chapter_pattern.match(line_stripped)
                if chapter_m:
                    self.current_chapter = chapter_m.group(1).zfill(2)
                    self.stats["chapters_found"].add(self.current_chapter)
                    continue

                heading_m = heading_pattern.match(line_stripped)
                if heading_m:
                    if pending_hs:
                        self._flush_pending(pending_hs, pending_desc_lines, pending_unit, None)
                        pending_hs = None
                        pending_desc_lines = []
                        pending_unit = None
                    self.current_heading = heading_m.group(1)
                    self.current_heading_desc = ""
                    continue

                hs8_m = hs8_pattern.match(line_stripped)
                if hs8_m:
                    if pending_hs:
                        self._flush_pending(pending_hs, pending_desc_lines, pending_unit, None)
                    pending_hs = hs8_m.group(1)
                    pending_desc_lines = []
                    pending_unit = None
                    chapter = pending_hs[:2]
                    if chapter != self.current_chapter:
                        self.current_chapter = chapter
                        self.stats["chapters_found"].add(chapter)
                    continue

                if pending_hs is not None:
                    if rate_pattern.match(line_stripped):
                        rate_str = line_stripped
                        self._flush_pending(pending_hs, pending_desc_lines, pending_unit, rate_str)
                        pending_hs = None
                        pending_desc_lines = []
                        pending_unit = None
                        continue

                    if unit_pattern.match(line_stripped):
                        pending_unit = line_stripped
                        continue

                    pending_desc_lines.append(line_stripped)
                else:
                    if line_stripped.startswith("-") or line_stripped.startswith("--") or line_stripped.startswith("---"):
                        pass
                    elif not self.current_heading_desc and self.current_heading:
                        self.current_heading_desc = line_stripped

        if pending_hs:
            self._flush_pending(pending_hs, pending_desc_lines, pending_unit, None)

        doc.close()
        logger.info(f"Extracted {len(self.positions)} positions from {len(self.stats['chapters_found'])} chapters")
        return self.positions

    def _flush_pending(self, hs_code: str, desc_lines: List[str], unit: Optional[str], rate_str: Optional[str]):
        description = " ".join(desc_lines).strip()
        description = re.sub(r'\s+', ' ', description)

        rate_value = None
        rate_display = rate_str or ""
        is_sensitive = False

        if rate_str:
            if rate_str == "SI":
                is_sensitive = True
                rate_display = "SI (Sensitive Item)"
            else:
                rate_value = self.parse_rate(rate_str)
                if rate_value is not None:
                    rate_display = f"{rate_value}%"

        rate_key = rate_display if rate_display else "unknown"
        self.stats["rate_distribution"][rate_key] = self.stats["rate_distribution"].get(rate_key, 0) + 1

        position = {
            "hs_code": hs_code,
            "hs_code_normalized": hs_code.replace(".", ""),
            "description": description,
            "unit": unit or "",
            "cet_rate": rate_value,
            "cet_rate_display": rate_display,
            "is_sensitive_item": is_sensitive,
            "chapter": self.current_chapter,
            "heading": self.current_heading,
            "section": self.current_section,
        }

        self.positions.append(position)
        self.stats["total_positions"] += 1

    def generate_country_tariffs(self, country_code: str) -> List[Dict]:
        if country_code not in EAC_COUNTRY_TAXES:
            raise ValueError(f"Unknown EAC country: {country_code}")

        country_info = EAC_COUNTRY_TAXES[country_code]
        result = []

        for pos in self.positions:
            taxes_detail = []
            total_taxes_pct = 0.0

            if pos["cet_rate"] is not None:
                taxes_detail.append({
                    "tax_name": "CET Import Duty (Droit de Douane)",
                    "rate": pos["cet_rate"],
                    "base": "CIF",
                    "is_cet": True
                })
                total_taxes_pct += pos["cet_rate"]
            elif pos["is_sensitive_item"]:
                taxes_detail.append({
                    "tax_name": "CET Import Duty (Sensitive Item)",
                    "rate": None,
                    "base": "CIF",
                    "is_cet": True,
                    "note": "Rate determined by national schedule"
                })

            for tax in country_info["taxes"]:
                taxes_detail.append({
                    "tax_name": tax["name"],
                    "rate": tax["rate"],
                    "base": tax["base"],
                    "is_cet": False
                })
                total_taxes_pct += tax["rate"]

            hs4 = pos["hs_code_normalized"][:4]
            excise_rate = country_info.get("excise_categories", {}).get(hs4)
            if excise_rate:
                taxes_detail.append({
                    "tax_name": "Excise Duty",
                    "rate": excise_rate,
                    "base": "CIF+Duty",
                    "is_cet": False
                })
                total_taxes_pct += excise_rate

            entry = {
                "hs_code": pos["hs_code_normalized"],
                "hs_code_display": pos["hs_code"],
                "designation": pos["description"],
                "unit": pos["unit"],
                "chapter": pos["chapter"],
                "heading": pos["heading"],
                "section": pos["section"],
                "is_sensitive_item": pos["is_sensitive_item"],
                "taxes_detail": taxes_detail,
                "total_taxes_pct": round(total_taxes_pct, 2),
                "fiscal_advantages": [
                    {
                        "name": "EAC Intra-Community",
                        "description": "0% duty for goods originating from EAC member states with valid Certificate of Origin",
                        "conditions": "Certificate of Origin required"
                    },
                    {
                        "name": "AfCFTA Tariff Concession",
                        "description": "Progressive duty reduction for AfCFTA member states",
                        "conditions": "AfCFTA Certificate of Origin required"
                    }
                ],
                "administrative_formalities": [],
                "source": "EAC CET 2022 (kra.go.ke)",
                "data_format": "crawled_authentic"
            }

            result.append(entry)

        return result

    def save_country_data(self, country_code: str, positions: List[Dict], output_dir: str = None):
        if output_dir is None:
            output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "crawled")
        os.makedirs(output_dir, exist_ok=True)

        country_name = EAC_COUNTRY_TAXES[country_code]["name"]
        filename = f"{country_code.lower()}_tariffs.json"
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
            "positions": positions
        }

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        logger.info(f"Saved {len(positions)} positions to {filepath}")
        return filepath

    def run(self, output_dir: str = None) -> Dict:
        logger.info("=" * 60)
        logger.info("EAC CET 2022 Scraper - Starting extraction")
        logger.info("=" * 60)

        self.extract_positions()

        logger.info(f"\nExtraction complete:")
        logger.info(f"  Total positions: {self.stats['total_positions']}")
        logger.info(f"  Chapters: {len(self.stats['chapters_found'])}")
        logger.info(f"  Sections: {len(self.stats['sections_found'])}")
        logger.info(f"  Rate distribution:")
        for rate, count in sorted(self.stats["rate_distribution"].items(), key=lambda x: -x[1])[:15]:
            logger.info(f"    {rate}: {count}")

        saved_files = {}
        for country_code in EAC_COUNTRY_TAXES:
            logger.info(f"\nGenerating tariff data for {country_code} ({EAC_COUNTRY_TAXES[country_code]['name']})...")
            country_positions = self.generate_country_tariffs(country_code)
            filepath = self.save_country_data(country_code, country_positions, output_dir)
            saved_files[country_code] = {
                "file": filepath,
                "positions": len(country_positions),
                "country_name": EAC_COUNTRY_TAXES[country_code]["name"]
            }

        result = {
            "status": "success",
            "total_cet_positions": self.stats["total_positions"],
            "chapters": len(self.stats["chapters_found"]),
            "countries": len(saved_files),
            "files": saved_files,
            "rate_distribution": dict(sorted(
                self.stats["rate_distribution"].items(), key=lambda x: -x[1]
            ))
        }

        logger.info("\n" + "=" * 60)
        logger.info("EAC CET extraction complete!")
        logger.info(f"  {self.stats['total_positions']} positions x {len(saved_files)} countries")
        logger.info("=" * 60)

        return result


if __name__ == "__main__":
    import sys
    pdf_path = sys.argv[1] if len(sys.argv) > 1 else None
    scraper = EACCETScraper(pdf_path)
    result = scraper.run()
    print(json.dumps(result, indent=2, default=str))
