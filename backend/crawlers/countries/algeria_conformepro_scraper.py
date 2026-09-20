"""
Crawler pour extraire les positions tarifaires nationales algériennes
Source: conformepro.dz (données issues de douane.gov.dz)
Structure: Section → Chapitre → Rangée (HS4) → Sous-position (HS8/HS10)
Données extraites: code SH, désignation exacte, DD, TVA, TCS, PRCT, DAPS, formalités
"""

import asyncio
import json
import logging
import os
import re
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Set

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

BASE_URL = "https://conformepro.dz/resources/tarif-douanier"
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data", "crawled")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.5",
}

RATE_LIMIT_DELAY = 1.5


class AlgeriaConformeproScraper:
    def __init__(self):
        self.client = None
        self.sections = []
        self.chapters = []
        self.chapters_filter: Optional[Set[str]] = None
        self.headings = []
        self.sub_positions = []
        self.errors = []
        self.stats = {
            "sections": 0,
            "chapters": 0,
            "headings": 0,
            "sub_positions": 0,
            "errors": 0,
            "started_at": None,
            "finished_at": None,
        }

    async def _init_client(self):
        if not self.client:
            self.client = httpx.AsyncClient(
                headers=HEADERS,
                timeout=30.0,
                follow_redirects=True,
                # La vérification TLS est rétablie : `https://conformepro.dz/resources/
                # tarif-douanier` répond 200 avec la chaîne vérifiée (relevé le
                # 20/09/2026). Un collecteur qui accepte n'importe quel certificat
                # laisse un tiers sur le chemin dicter les taux qu'il liquide.
            )

    async def _close_client(self):
        if self.client:
            await self.client.aclose()
            self.client = None

    async def _fetch_page(self, url: str, retries: int = 3) -> Optional[str]:
        await self._init_client()
        for attempt in range(retries):
            try:
                await asyncio.sleep(RATE_LIMIT_DELAY)
                resp = await self.client.get(url)
                if resp.status_code == 200:
                    return resp.text
                logger.warning(f"HTTP {resp.status_code} for {url}")
                if resp.status_code == 429:
                    await asyncio.sleep(10)
            except Exception as e:
                logger.error(f"Fetch error (attempt {attempt+1}) for {url}: {e}")
                await asyncio.sleep(3)
        self.errors.append({"url": url, "error": "Max retries exceeded"})
        self.stats["errors"] += 1
        return None

    def _extract_links(self, html: str, pattern: str) -> List[Dict[str, str]]:
        soup = BeautifulSoup(html, "html.parser")
        links = []
        seen = set()
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if pattern not in href or href in seen:
                continue
            seen.add(href)
            text = a.get_text(" ", strip=True)
            if text:
                links.append({"url": href, "text": text})
        return links

    def _parse_rangee_cards(self, html: str, heading: Dict) -> List[Dict]:
        """
        Parse sous-position cards from a rangee listing page.

        Real card DOM (confirmed from conformepro.dz):
          <a href=".../sous-position/01.01.211100/slug">
            <small class="datagrid-title">Sous-position 2111.00</small>
            <h3 class="fw-bold mb-1 text-primary">Short title</h3>
            <p class="text-muted m-0 fs-4">Extended description</p>
          </a>
        """
        soup = BeautifulSoup(html, "html.parser")
        subs = []
        seen = set()

        for card in soup.find_all("a", href=lambda h: h and "/sous-position/" in h):
            href = card.get("href", "")
            if href in seen:
                continue
            seen.add(href)

            url = href if href.startswith("http") else f"https://conformepro.dz{href}"
            m = re.search(r"/sous-position/([\d.]+)/", url)
            if not m:
                continue
            raw_code = m.group(1)

            small = card.find("small", class_="datagrid-title")
            h3 = card.find("h3")
            p = card.find("p")

            display_code = small.get_text(strip=True) if small else ""
            title = h3.get_text(strip=True) if h3 else ""
            description = p.get_text(strip=True) if p else title

            subs.append(
                {
                    "raw_code": raw_code,
                    "display_code": display_code,
                    "name": title,
                    "description": description,
                    "url": url,
                    "heading": heading["code"],
                    "chapter": heading["chapter"],
                    "section": heading["section"],
                }
            )

        return subs

    async def scrape_sections(self) -> List[Dict]:
        logger.info("Scraping sections...")
        html = await self._fetch_page(BASE_URL)
        if not html:
            return []

        sections = []
        links = self._extract_links(html, "/resources/tarif-douanier/section/")
        for link in links:
            url = link["url"]
            if not url.startswith("http"):
                url = f"https://conformepro.dz{url}"
            m = re.search(r"/section/(\d+)/", url)
            if m:
                sections.append(
                    {
                        "code": m.group(1),
                        "name": link["text"],
                        "url": url,
                    }
                )

        seen = set()
        unique = []
        for s in sections:
            if s["code"] not in seen:
                seen.add(s["code"])
                unique.append(s)
        self.sections = unique
        self.stats["sections"] = len(unique)
        logger.info(f"Found {len(unique)} sections")
        return unique

    async def scrape_chapters(self) -> List[Dict]:
        logger.info("Scraping chapters from all sections...")
        chapters = []

        for section in self.sections:
            html = await self._fetch_page(section["url"])
            if not html:
                continue

            links = self._extract_links(html, "/resources/tarif-douanier/chapitre/")
            for link in links:
                url = link["url"]
                if not url.startswith("http"):
                    url = f"https://conformepro.dz{url}"
                m = re.search(r"/chapitre/(\d+)/", url)
                if m:
                    chapters.append(
                        {
                            "code": m.group(1),
                            "name": link["text"],
                            "url": url,
                            "section": section["code"],
                        }
                    )

        seen = set()
        unique = []
        for c in chapters:
            if c["code"] not in seen:
                seen.add(c["code"])
                unique.append(c)
        self.chapters = unique
        self.stats["chapters"] = len(unique)
        logger.info(f"Found {len(unique)} chapters")
        return unique

    async def scrape_headings(self) -> List[Dict]:
        logger.info("Scraping headings (rangées) from all chapters...")
        headings = []

        for i, chapter in enumerate(self.chapters):
            logger.info(f"  Chapter {chapter['code']} ({i+1}/{len(self.chapters)})")
            html = await self._fetch_page(chapter["url"])
            if not html:
                continue

            links = self._extract_links(html, "/resources/tarif-douanier/rangee/")
            for link in links:
                url = link["url"]
                if not url.startswith("http"):
                    url = f"https://conformepro.dz{url}"
                m = re.search(r"/rangee/([\d.]+)/", url)
                if m:
                    headings.append(
                        {
                            "code": m.group(1),
                            "name": link["text"],
                            "url": url,
                            "chapter": chapter["code"],
                            "section": chapter["section"],
                        }
                    )

        seen = set()
        unique = []
        for h in headings:
            if h["code"] not in seen:
                seen.add(h["code"])
                unique.append(h)
        self.headings = unique
        self.stats["headings"] = len(unique)
        logger.info(f"Found {len(unique)} headings")
        return unique

    async def scrape_sub_positions_for_heading(self, heading: Dict) -> List[Dict]:
        html = await self._fetch_page(heading["url"])
        if not html:
            return []
        return self._parse_rangee_cards(html, heading)

    def _parse_vstack(self, soup: BeautifulSoup, label: str) -> str:
        """
        Extract the value from a div.vstack block whose h2 text matches `label`.

        Real detail page DOM (confirmed from conformepro.dz):
          <div class="vstack ...">
            <h2>Droit de douane</h2>
            <p class="fw-bold display-5 m-0">5%</p>
          </div>
          <div class="vstack ...">
            <h2>Désignation complète</h2>
            <div class="fs-3">Animaux vivants > ...</div>
          </div>
          <div class="vstack ...">
            <h2>Avantages</h2>
            <div class="fs-3"><ul><li>...</li></ul></div>
          </div>
        """
        for div in soup.find_all("div", class_="vstack"):
            h2 = div.find("h2")
            if not h2 or h2.get_text(strip=True) != label:
                continue
            p = div.find("p", class_=lambda c: c and "fw-bold" in c)
            if p:
                return p.get_text(strip=True)
            div_fs = div.find("div", class_="fs-3")
            if div_fs:
                items = div_fs.find_all("li")
                if items:
                    return "; ".join(
                        li.get_text(strip=True) for li in items if li.get_text(strip=True)
                    )
                return div_fs.get_text(strip=True)
        return ""

    # Mapping des libellés publiés par conformepro.dz vers codes canoniques DGD.
    # Étendu pour couvrir TOUTES les taxes et redevances de la circulaire DGD.
    TAX_LABEL_MAP = {
        "Droit de douane": "DD",
        "TVA": "TVA",
        "TCS": "TCS",
        "PRCT": "PRCT",
        "DAPS": "DAPS",
        "TIC": "TIC",
        "TAPT": "TAPT",
        "Taxe sur les Autres Produits du Tabac": "TAPT",
        "DPE": "DPE",
        "Droit sur les Produits Énergétiques": "DPE",
        "TSV": "TSV",
        "Taxe sur les Services Vétérinaires": "TSV",
        "TSP": "TSP",
        "Taxe Sanitaire Phytosanitaire": "TSP",
        "T.PNEUS": "T.PNEUS",
        "Taxe sur les Pneus": "T.PNEUS",
        "T.HUILES": "T.HUILES",
        "Taxe sur les Huiles": "T.HUILES",
        "TPP": "TPP",
        "Taxe sur les Produits Pétroliers": "TPP",
        "TPI": "TPI",
        "Taxe Parafiscale à l'Importation": "TPI",
        "Redevance pour copie privée": "ONDA",
        "Droit de garantie": "DROIT_GARANTIE",
        "Taxe poisson": "TAXE_POISSON",
        "Acquit service alcools": "ACQUIT_ALCOOLS",
    }

    # Libellés connus qui ne sont PAS des taxes (ignorer dans l'extraction dynamique)
    NON_TAX_LABELS = {
        "Désignation complète", "Avantages", "Formalités",
        "Désignation", "Code", "Chapitre", "Section",
        "Unité", "Unité statistique", "Statistiques",
    }

    async def scrape_sub_position_detail(self, sub: Dict) -> Dict:
        html = await self._fetch_page(sub["url"])
        if not html:
            return sub

        soup = BeautifulSoup(html, "html.parser")

        result = {
            "raw_code": sub["raw_code"],
            "hs_code": sub["raw_code"].replace(".", ""),
            "display_code": sub.get("display_code", ""),
            "heading": sub["heading"],
            "chapter": sub["chapter"],
            "section": sub["section"],
            "name": sub.get("name", ""),
            "description": sub.get("description", sub.get("name", "")),
            "taxes": {},
            "advantages": [],
            "formalities": [],
            "source": "conformepro.dz",
            "source_url": sub["url"],
            "source_root_url": BASE_URL,
            "source_quality": "crawled_authentic",
            "data_status": "crawled_authentic",
            "crawled_at": datetime.utcnow().isoformat(),
            "date_consulted": datetime.utcnow().strftime("%Y-%m-%d"),
        }

        # "Désignation complète" is the authoritative full description
        designation_full = self._parse_vstack(soup, "Désignation complète")
        if designation_full:
            result["designation_full"] = designation_full

        # ── EXTRACTION DYNAMIQUE DES TAXES ──
        # Parcourir TOUS les div.vstack de la page et extraire ceux qui
        # contiennent un taux (%, DA, dinars) — pas seulement les 6
        # libellés hardcodés. Capture TAPT, DPE, TSV, TSP, T.PNEUS,
        # T.HUILES, TPP, TPI et toute autre taxe publiée.
        taxes = {}
        source_gaps = []
        for div in soup.find_all("div", class_="vstack"):
            h2 = div.find("h2")
            if not h2:
                continue
            label = h2.get_text(strip=True)

            # Ignorer les blocs non-fiscaux
            if label in self.NON_TAX_LABELS:
                continue

            # Extraire la valeur (p.fw-bold ou div.fs-3)
            p = div.find("p", class_=lambda c: c and "fw-bold" in c)
            raw_value = ""
            if p:
                raw_value = p.get_text(strip=True)
            else:
                div_fs = div.find("div", class_="fs-3")
                if div_fs:
                    raw_value = div_fs.get_text(strip=True)

            if not raw_value:
                continue

            # Déterminer le code canonique
            code = self.TAX_LABEL_MAP.get(label, "")
            if not code:
                # Extraction dynamique : si le libellé contient un taux,
                # c'est une taxe — utiliser le libellé comme code.
                if re.search(r"\d+(?:[.,]\d+)?\s*%", raw_value) or \
                   re.search(r"\d+(?:[.,]\d+)?\s*(?:da|DA|dinars?)", raw_value, re.IGNORECASE):
                    code = label.upper().replace(" ", "_").replace(".", "")[:20]
                else:
                    continue

            # Parser le taux
            rate = None
            rate_match = re.search(r"(\d+(?:[.,]\d+)?)\s*%?", raw_value)
            if rate_match:
                rate = float(rate_match.group(1).replace(",", "."))

            # Valeur spécifique (DA/kg, DA/hg, etc.)
            specific_match = re.search(
                r"(\d+(?:[.,]\d+)?)\s*(?:da|DA|dinars?)\s*(?:/|par)?\s*(kg|hg|hectogramme|litre|l|unité|u)?",
                raw_value, re.IGNORECASE
            )
            specific_value = specific_match.group(0) if specific_match else None

            taxes[code] = {
                "code": code,
                "label_published": label,
                "rate": rate if rate is not None else 0.0,
                "raw": raw_value,
                "specific_value": specific_value,
                "source": "conformepro.dz (données douane.gov.dz)",
                "source_root_url": BASE_URL,
                "official_dgd_code": code,
                "official_dgd_label": label,
                "label_verification": "DYNAMIC_EXTRACT",
            }

            # Si le taux n'a pas pu être extrait → source_gap
            if rate is None and not specific_value:
                source_gaps.append(code)

        result["taxes"] = taxes
        result["source_gaps"] = source_gaps

        # ── AVANTAGES FISCAUX ──
        advantages_raw = self._parse_vstack(soup, "Avantages")
        if advantages_raw:
            result["advantages"] = [s.strip() for s in advantages_raw.split(";") if s.strip()]

        # ── FORMALITÉS (avec extraction des taxes implicites) ──
        formalities_raw = self._parse_vstack(soup, "Formalités")
        if formalities_raw:
            formalities = []
            for f in formalities_raw.split(";"):
                f = f.strip()
                if not f:
                    continue

                # Détecter les taxes/redevances implicites dans les formalités
                # (ex: "Quit. paiement taxe poisson imp. 30da/kg",
                #       "Droit de garantie 16000da/hg or",
                #       "Redevance copie privée ONDA")
                fap_code = ""
                official_label = f
                match_status = "UNMATCHED_VERBATIM"

                # Mapper les formalités connues vers des codes FAP
                fap_mappings = {
                    "derogation sanitaire": ("D.S.V", "Dérogation sanitaire vétérinaire", "MATCHED_DGD_FAP_LIST"),
                    "visa de controle sanitaire": ("V.C.S.V", "Visa de Contrôle Sanitaire Vétérinaire", "MATCHED_DGD_FAP_LIST"),
                    "certificat phytosanitaire": ("C.P", "Certificat Phytosanitaire", "MATCHED_DGD_FAP_LIST"),
                    "autorisation": ("AUT", "Autorisation", "MATCHED_DGD_FAP_LIST"),
                    "licence": ("LIC", "Licence", "MATCHED_DGD_FAP_LIST"),
                    "agrement": ("AGR", "Agrément", "MATCHED_DGD_FAP_LIST"),
                    "homologation": ("HOM", "Homologation", "MATCHED_DGD_FAP_LIST"),
                    "visa technique": ("VT", "Visa Technique", "MATCHED_DGD_FAP_LIST"),
                    "inspection": ("INS", "Inspection", "MATCHED_DGD_FAP_LIST"),
                    "attestation": ("ATT", "Attestation", "MATCHED_DGD_FAP_LIST"),
                    "declaration": ("DEC", "Déclaration", "MATCHED_DGD_FAP_LIST"),
                    "acquit": ("ACQ", "Acquit", "MATCHED_DGD_FAP_LIST"),
                    "quit": ("QUIT", "Quittance", "MATCHED_DGD_FAP_LIST"),
                    "cahier des charges": ("CDC", "Cahier des Charges", "MATCHED_DGD_FAP_LIST"),
                    "monopole": ("MON", "Monopole", "MATCHED_DGD_FAP_LIST"),
                    "fiche": ("FIC", "Fiche", "MATCHED_DGD_FAP_LIST"),
                }

                f_lower = f.lower()
                for pattern, (code, label, status) in fap_mappings.items():
                    if pattern in f_lower:
                        fap_code = code
                        official_label = label
                        match_status = status
                        break

                formalities.append({
                    "text_verbatim": f,
                    "source": "conformepro.dz (données douane.gov.dz)",
                    "fap_code": fap_code,
                    "fap_official_label": official_label if fap_code else f,
                    "match_status": match_status,
                })

                # Si la formalité contient un montant (DA/kg, DA/hg),
                # l'enregistrer aussi comme taxe implicite
                da_match = re.search(
                    r"(\d+(?:[.,]\d+)?)\s*(?:da|DA|dinars?)\s*(?:/|par)?\s*(kg|hg|hectogramme|litre|l)?",
                    f, re.IGNORECASE
                )
                if da_match:
                    implicit_code = "IMPLICIT_" + f[:20].upper().replace(" ", "_").replace(".", "")
                    # Essayer de nommer la taxe
                    if "poisson" in f_lower:
                        implicit_code = "TAXE_POISSON"
                    elif "garantie" in f_lower or "or" in f_lower:
                        implicit_code = "DROIT_GARANTIE"
                    elif "onda" in f_lower or "copie privee" in f_lower:
                        implicit_code = "ONDA"
                    elif "alcool" in f_lower or "regie" in f_lower:
                        implicit_code = "ACQUIT_ALCOOLS"

                    if implicit_code not in taxes:
                        taxes[implicit_code] = {
                            "code": implicit_code,
                            "label_published": f,
                            "rate": None,
                            "raw": f,
                            "specific_value": da_match.group(0),
                            "source": "conformepro.dz — extrait des formalités",
                            "source_root_url": BASE_URL,
                            "official_dgd_code": implicit_code,
                            "official_dgd_label": f,
                            "label_verification": "IMPLICIT_FROM_FORMALITY",
                        }

            result["formalities"] = formalities

        # ── RÉFÉRENCES JURIDIQUES ──
        # conformepro.dz ne publie pas toujours les références juridiques
        # par sous-position, mais on les extrait quand elles sont présentes.
        legal_refs = []
        legal_raw = self._parse_vstack(soup, "Références juridiques")
        if legal_raw:
            for ref in legal_raw.split(";"):
                ref = ref.strip()
                if ref:
                    legal_refs.append({"ref": ref, "doc": None})
        if legal_refs:
            result["legal_refs"] = legal_refs
        else:
            # Références juridiques par défaut (Code des Douanes + Tarif D'Usage)
            result["legal_refs"] = [
                {
                    "ref": "Loi n° 79-07 du 21 juillet 1979 portant code des douanes, modifiée et complétée",
                    "doc": "data/sources/DZA/legislation/code_douanes_79-07.pdf",
                },
                {
                    "ref": "Tarif Douanier d'usage — DGD, Direction de la Fiscalité et des Bases de Taxation (édition LF 2020)",
                    "doc": "data/sources/DZA/legislation/tarif_d_usage_2020.pdf",
                },
            ]

        return result

    def _load_last_progress(self):
        import glob as globmod

        progress_files = sorted(
            globmod.glob(os.path.join(DATA_DIR, "DZA_progress_*.json")),
            key=lambda p: int(
                os.path.basename(p).replace("DZA_progress_", "").replace(".json", "")
            ),
        )
        if progress_files:
            last_file = progress_files[-1]
            try:
                with open(last_file, "r", encoding="utf-8") as f:
                    prev = json.load(f)
                data = prev.get("data", [])
                heading_idx = int(
                    os.path.basename(last_file).replace("DZA_progress_", "").replace(".json", "")
                )
                logger.info(
                    f"Resume: loaded {len(data)} sub-positions from {os.path.basename(last_file)}, resuming from heading {heading_idx}"
                )
                return data, heading_idx
            except Exception as e:
                logger.warning(f"Could not load progress: {e}")
        return [], 0

    async def scrape_all_sub_positions(
        self,
        start_heading_idx: int = 0,
        max_headings: int = None,
        resume: bool = True,
        concurrency: int = 1,
    ):
        if not isinstance(concurrency, int) or concurrency < 1:
            raise ValueError(f"concurrency must be an integer >= 1, got {concurrency!r}")
        logger.info(f"Scraping sub-positions from {len(self.headings)} headings...")
        all_subs = []
        actual_start = start_heading_idx

        if resume and start_heading_idx == 0:
            prev_data, prev_idx = self._load_last_progress()
            if prev_data:
                all_subs = prev_data
                actual_start = prev_idx
                logger.info(
                    f"Resuming from heading {actual_start} with {len(all_subs)} sub-positions already collected"
                )

        end_idx = (
            len(self.headings)
            if max_headings is None
            else min(actual_start + max_headings, len(self.headings))
        )

        for i in range(actual_start, end_idx):
            heading = self.headings[i]
            logger.info(f"  Heading {heading['code']} ({i+1}/{len(self.headings)})")

            subs = await self.scrape_sub_positions_for_heading(heading)
            logger.info(f"    Found {len(subs)} sub-positions, fetching details...")

            if concurrency > 1:
                sem = asyncio.Semaphore(concurrency)

                async def _fetch_one(s):
                    async with sem:
                        return await self.scrape_sub_position_detail(s)

                # Traité par lots bornés : le sémaphore borne déjà les
                # requêtes réseau simultanées, mais créer une tâche par
                # sous-position d'un coup peut être coûteux en mémoire pour
                # les grandes rubriques. On limite aussi le nombre de tâches
                # en vol en même temps.
                details = []
                batch_size = concurrency * 4
                for j in range(0, len(subs), batch_size):
                    batch = subs[j : j + batch_size]
                    details.extend(await asyncio.gather(*(_fetch_one(s) for s in batch)))
            else:
                details = [await self.scrape_sub_position_detail(s) for s in subs]

            for detail in details:
                all_subs.append(detail)

            if (i + 1) % 5 == 0:
                self._save_progress(all_subs, f"DZA_progress_{i+1}")
                logger.info(f"  Progress saved: {len(all_subs)} sub-positions so far")

        self.sub_positions.extend(all_subs)
        self.stats["sub_positions"] = len(self.sub_positions)
        return all_subs

    def _save_progress(self, data: List[Dict], filename: str):
        os.makedirs(DATA_DIR, exist_ok=True)
        filepath = os.path.join(DATA_DIR, f"{filename}.json")
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "country": "DZA",
                    "source": "conformepro.dz",
                    "extracted_at": datetime.utcnow().isoformat(),
                    "count": len(data),
                    "data": data,
                },
                f,
                ensure_ascii=False,
                indent=2,
            )
        logger.info(f"Saved {len(data)} records to {filepath}")

    def save_final(self):
        os.makedirs(DATA_DIR, exist_ok=True)
        self.stats["finished_at"] = datetime.utcnow().isoformat()

        structure = {
            "country": "DZA",
            "country_name": "Algérie",
            "source": "conformepro.dz (données douane.gov.dz)",
            "extracted_at": datetime.utcnow().isoformat(),
            "stats": self.stats,
            "sections": self.sections,
            "chapters": self.chapters,
        }
        with open(os.path.join(DATA_DIR, "DZA_structure.json"), "w", encoding="utf-8") as f:
            json.dump(structure, f, ensure_ascii=False, indent=2)

        # Fusionne avec un DZA_tariffs.json existant (ex. re-crawl ciblé d'un
        # sous-ensemble de chapitres) : les positions nouvellement re-crawlées
        # remplacent les anciennes par hs_code, le reste est conservé tel quel.
        existing_path = os.path.join(DATA_DIR, "DZA_tariffs.json")
        prev: Dict[str, Any] = {}
        merged_by_code: dict[str, dict] = {}
        if os.path.exists(existing_path):
            try:
                with open(existing_path, "r", encoding="utf-8") as f:
                    prev = json.load(f)
                for p in prev.get("sub_positions", []):
                    merged_by_code[p.get("hs_code") or p.get("raw_code")] = p
                logger.info(f"Fusion : {len(merged_by_code)} positions existantes chargées")
            except Exception as e:
                logger.warning(f"Impossible de charger {existing_path} pour fusion : {e}")

        for p in self.sub_positions:
            merged_by_code[p.get("hs_code") or p.get("raw_code")] = p

        all_positions = list(merged_by_code.values())
        now = datetime.utcnow().isoformat()

        # L'en-tête existant est REPRIS, jamais reconstruit : il porte la
        # provenance du jeu de données (source_root_url, source_quality,
        # source_provenance, built_by, policy, legal_refs) que ce crawler ne
        # produit pas et ne saurait donc pas réécrire. La reconstruire à
        # l'identique de zéro effacerait silencieusement cette traçabilité —
        # les positions, elles, survivaient à la fusion, ce qui rendait la
        # perte invisible dans le comportement du produit.
        tariff_data = {
            k: v for k, v in prev.items() if k not in ("sub_positions", "_integrity_seal")
        }
        tariff_data.setdefault("country", "DZA")
        tariff_data.setdefault("country_name", "Algérie")
        tariff_data.setdefault("source", "conformepro.dz (données douane.gov.dz)")

        if self.chapters_filter:
            # Re-crawl partiel : la date d'extraction d'origine reste vraie pour
            # l'immense majorité des positions, on ne la remplace pas par celle
            # d'un passage sur quelques chapitres.
            tariff_data.setdefault("extracted_at", now)
            tariff_data["last_partial_recrawl"] = {
                "chapters": sorted(self.chapters_filter),
                "at": now,
                "positions_recrawled": len(self.sub_positions),
            }
        else:
            tariff_data["extracted_at"] = now
            tariff_data.pop("last_partial_recrawl", None)

        tariff_data["stats"] = self.stats
        tariff_data["sub_positions"] = all_positions

        # Le sceau précédent ne vaut plus pour ce contenu : il est retiré plutôt
        # que laissé tel quel. `python backend/crawlers/integrity.py seal` le
        # régénère, et le manifeste doit être réaligné dans la foulée.
        with open(existing_path, "w", encoding="utf-8") as f:
            json.dump(tariff_data, f, ensure_ascii=False, indent=2)

        logger.info(
            f"Final data saved: {len(self.sub_positions)} positions re-crawlées, "
            f"{len(all_positions)} positions au total dans {existing_path}"
        )
        logger.info(f"Stats: {json.dumps(self.stats, indent=2)}")

    async def run(
        self,
        max_headings: int = None,
        chapters: Optional[Set[str]] = None,
        concurrency: int = 1,
    ):
        """
        chapters: si fourni, ne scrape que les chapitres SH listés (ex. {"29", "30", ...}).
        Permet de cibler un re-crawl correctif sans refaire les chapitres déjà
        authentiquement crawlés.
        """
        self.stats["started_at"] = datetime.utcnow().isoformat()
        logger.info("=== Algeria Tariff Scraper (conformepro.dz) ===")
        # save_final doit savoir si le passage est partiel : sinon il écrase la
        # date d'extraction du fichier entier avec celle d'un crawl de quelques
        # chapitres.
        self.chapters_filter = set(chapters) if chapters else None

        try:
            await self.scrape_sections()
            await self.scrape_chapters()
            if chapters:
                before = len(self.chapters)
                self.chapters = [c for c in self.chapters if c["code"] in chapters]
                logger.info(
                    f"Filtre chapitres : {before} -> {len(self.chapters)} "
                    f"({sorted(c['code'] for c in self.chapters)})"
                )
            await self.scrape_headings()
            await self.scrape_all_sub_positions(max_headings=max_headings, concurrency=concurrency)
            self.save_final()
        finally:
            await self._close_client()

        return {
            "success": True,
            "stats": self.stats,
            "sub_positions_count": len(self.sub_positions),
        }


async def run_algeria_scraper(
    max_headings: int = None, chapters: Optional[Set[str]] = None, concurrency: int = 1
):
    scraper = AlgeriaConformeproScraper()
    return await scraper.run(max_headings=max_headings, chapters=chapters, concurrency=concurrency)


async def run_algeria_scraper_fast():
    """
    Fast mode: collect only national tariff positions with card-level descriptions.
    Skips detail page requests (no taxes/formalities). ~15x faster than full mode.
    Output: DZA_tariffs_fast.json
    """
    scraper = AlgeriaConformeproScraper()
    scraper.stats["started_at"] = datetime.utcnow().isoformat()
    logger.info("=== Algeria Tariff Scraper — FAST MODE (positions + descriptions only) ===")

    try:
        await scraper.scrape_sections()
        await scraper.scrape_chapters()
        await scraper.scrape_headings()

        all_subs = []
        for i, heading in enumerate(scraper.headings):
            logger.info(f"  Heading {heading['code']} ({i+1}/{len(scraper.headings)})")
            subs = await scraper.scrape_sub_positions_for_heading(heading)
            for sub in subs:
                all_subs.append(
                    {
                        "raw_code": sub["raw_code"],
                        "hs_code": sub["raw_code"].replace(".", ""),
                        "display_code": sub.get("display_code", ""),
                        "heading": sub["heading"],
                        "chapter": sub["chapter"],
                        "section": sub["section"],
                        "name": sub.get("name", ""),
                        "description": sub.get("description", ""),
                        "source": "conformepro.dz",
                        "source_url": sub["url"],
                    }
                )
            logger.info(f"    {len(subs)} positions collected (total: {len(all_subs)})")

        scraper.stats["finished_at"] = datetime.utcnow().isoformat()
        scraper.stats["sub_positions"] = len(all_subs)

        output = {
            "country": "DZA",
            "country_name": "Algérie",
            "source": "conformepro.dz (données douane.gov.dz)",
            "mode": "fast — positions and descriptions only",
            "extracted_at": datetime.utcnow().isoformat(),
            "stats": scraper.stats,
            "sub_positions": all_subs,
        }
        os.makedirs(DATA_DIR, exist_ok=True)
        out_path = os.path.join(DATA_DIR, "DZA_tariffs_fast.json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
        logger.info(f"Saved {len(all_subs)} positions to {out_path}")

    finally:
        await scraper._close_client()

    return {"success": True, "count": len(all_subs)}


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--fast",
        action="store_true",
        help="Fast mode: positions and descriptions only, no detail pages",
    )
    parser.add_argument("--max-headings", type=int, default=None)
    parser.add_argument(
        "--chapters",
        type=str,
        default=None,
        help="Liste de chapitres SH à recrawler, séparés par des virgules "
        "ou plages (ex. '29-76,78-98'). Sans cet argument, scrape tous les chapitres.",
    )
    parser.add_argument(
        "--concurrency",
        type=int,
        default=1,
        help="Nombre de requêtes détail simultanées (1 = séquentiel).",
    )
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)

    chapters_filter = None
    if args.chapters:
        chapters_filter = set()
        for part in args.chapters.split(","):
            part = part.strip()
            if "-" in part:
                lo, hi = part.split("-")
                chapters_filter.update(f"{i:02d}" for i in range(int(lo), int(hi) + 1))
            elif part:
                chapters_filter.add(f"{int(part):02d}")

    if args.fast:
        result = asyncio.run(run_algeria_scraper_fast())
    else:
        result = asyncio.run(
            run_algeria_scraper(
                max_headings=args.max_headings,
                chapters=chapters_filter,
                concurrency=args.concurrency,
            )
        )
    print(json.dumps(result, indent=2, ensure_ascii=False))
