"""Tarif douanier algérien — portail officiel de la Direction Générale des Douanes.

Complément du crawler ``algeria_conformepro_scraper``. conformepro.dz republie
les données de la DGD mais n'expose que 95 chapitres : sa section 04 s'intitule
« Produits des industries alimentaires, boissons, vinaigres » et saute les
chapitres 22 (boissons et liquides alcooliques) et 24 (tabacs), ainsi que la
position 96.14 (pipes). La DGD, elle, les publie — sa section 04 porte
l'intitulé complet du SH, tabacs compris.

Ce module va donc chercher ces positions à la source primaire, via l'e-service
``spip.php?page=tarif_douanier`` qui se parcourt en cinq niveaux :

    tarif_douanier → chapitre&section → range&chapitre → position&range
                   → sous_position

Le portail est servi derrière un pare-feu applicatif qui bloque l'accès direct
depuis un hébergeur ; les pages sont donc lues à travers un relais de lecture,
dont l'URL est paramétrable. Le relais ne transforme rien : ``x-return-format:
html`` rend les octets de la page.

Ce que le module ne fait pas, délibérément :

* il ne remplit pas ``fiscal_advantages``. Le portail publie un tableau
  « Avantages fiscaux » qui liste des taux d'exonération (D.D 0 %, T.V.A 0 %)
  rattachés à des régimes conditionnels, pas des taux applicables de plein
  droit. ``enhanced_calculator_service`` déduit ``fiscal_advantages`` du droit
  dû : l'y verser exonérerait tout le monde. Le tableau est conservé verbatim
  dans ``tax_advantages``, sans interprétation ;
* il ne convertit pas les taxes spécifiques en taux. Une quotité par hectolitre
  n'est pas un pourcentage ; elle est rendue telle quelle dans
  ``specific_taxes`` ;
* il ne corrige pas les caractères perdus. La base de la DGD stocke « mo?ts »
  pour « moûts » et « succ?dan?s » pour « succédanés » ; ces « ? » sont dans
  les octets servis. Les réécrire serait réécrire la source.

Usage :
    python -m crawlers.countries.algeria_dgd_official_scraper \
        --chapters 22,24 --out /tmp/DZA_dgd.json
    python -m crawlers.countries.algeria_dgd_official_scraper \
        --chapters 96 --headings 96.14 --out /tmp/DZA_9614.json
"""

from __future__ import annotations

import argparse
import json
import logging
import re
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from typing import Dict, Iterable, List, Optional

logger = logging.getLogger(__name__)

BASE_URL = "https://www.douane.gov.dz/spip.php"
SOURCE_NAME = "douane.gov.dz — Tarif douanier (e-service DGD)"
DEFAULT_RELAY = "https://r.jina.ai/"

# Codes publiés par la DGD → codes canoniques employés dans le jeu de données.
# La source étant la DGD elle-même, le libellé publié fait foi : pas de
# rapprochement à effectuer, contrairement au crawler conformepro.
DGD_TAX_CODES = {
    "D.D": ("DD", "Droits de Douane"),
    "T.V.A": ("TVA", "Taxe sur la Valeur Ajoutée"),
    "T.C.S": ("TCS", "Taxe de Formalité Douanière / Contribution de Solidarité"),
    "PRCT": ("PRCT", "Prélèvement au profit de la Chambre de Commerce"),
    "D.A.P.S": ("DAPS", "Droit Additionnel Provisoire de Sauvegarde"),
    "T.I.C": ("TIC", "Taxe Intérieure de Consommation"),
    "TIC": ("TIC", "Taxe Intérieure de Consommation"),
    # Accises reprises du référentiel de backend/etl/dza_tariff_connector.py.
    # Ce module en connaît le code canonique mais pas le libellé développé :
    # celui-ci reste nul plutôt que reconstitué à partir du sigle.
    "TICPV": ("TICPV", None),
    "TICBT": ("TICBT", None),
    "TAPT": ("TAPT", None),
    "D.C.A": ("DCA", None),
    "DCA": ("DCA", None),
}

_ROW = re.compile(
    r'<tr data-href="([^"]+)">\s*<td[^>]*>\s*(.*?)\s*</td>\s*<td[^>]*>(.*?)</td>',
    re.S,
)
_TABLE = re.compile(r"<table class=\"table\">(.*?)</table>", re.S)
_CELL = re.compile(r"<td[^>]*>(.*?)</td>", re.S)
_TR = re.compile(r"<tr[^>]*>(.*?)</tr>", re.S)
_TAG = re.compile(r"<[^>]+>")


def _text(fragment: str) -> str:
    """Texte visible d'un fragment HTML, espaces normalisés."""
    plain = _TAG.sub(" ", fragment)
    for entity, char in (("&amp;", "&"), ("&nbsp;", " "), ("&#39;", "'"), ("&quot;", '"')):
        plain = plain.replace(entity, char)
    return " ".join(plain.split())


def _rate(raw: str) -> Optional[float]:
    """Taux publié, ou None — jamais 0 par défaut.

    Une cellule vide signifie que la source ne publie pas de taux, ce qui n'est
    pas la même chose qu'un taux nul.
    """
    cleaned = raw.replace("%", "").replace(",", ".").strip()
    if not cleaned:
        return None
    try:
        return float(cleaned)
    except ValueError:
        return None


class DgdOfficialScraper:
    """Parcourt l'e-service tarifaire de la DGD et en extrait les feuilles."""

    def __init__(self, relay: str = DEFAULT_RELAY, delay: float = 0.5,
                 retries: int = 4, timeout: int = 120):
        self.relay = relay
        self.delay = delay
        self.retries = retries
        self.timeout = timeout
        self.requests = 0
        self.errors: List[str] = []

    # ----- transport ------------------------------------------------------

    def fetch(self, **params: str) -> str:
        target = f"{BASE_URL}?{urllib.parse.urlencode(params)}"
        url = self.relay + urllib.parse.quote(target, safe="") if self.relay else target
        request = urllib.request.Request(
            url,
            headers={
                "x-return-format": "html",
                "User-Agent": "afcfta-tariff-crawler/1.0 (+integrity audit)",
            },
        )
        for attempt in range(self.retries):
            try:
                with urllib.request.urlopen(request, timeout=self.timeout) as response:
                    self.requests += 1
                    time.sleep(self.delay)
                    return response.read().decode("utf-8", "replace")
            except Exception as exc:  # noqa: BLE001 — remonté tel quel dans errors
                if attempt == self.retries - 1:
                    self.errors.append(f"{target} : {exc}")
                    raise
                time.sleep(2 ** attempt)
        return ""

    # ----- navigation -----------------------------------------------------

    @staticmethod
    def _navigation_rows(html: str) -> List[Dict[str, str]]:
        """Lignes cliquables d'une table de navigation (code, libellé, href)."""
        return [
            {
                "href": href.replace("&amp;", "&"),
                "code": _text(code),
                "label": _text(label),
            }
            for href, code, label in _ROW.findall(html)
        ]

    def chapter_sections(self) -> Dict[str, str]:
        """Chapitre → section, découvert et non codé en dur."""
        mapping: Dict[str, str] = {}
        for section in self._navigation_rows(self.fetch(page="tarif_douanier")):
            code = section["code"]
            for chapter in self._navigation_rows(self.fetch(page="chapitre", section=code)):
                mapping[chapter["code"]] = code
        return mapping

    def leaves(self, section: str, chapter: str,
               headings: Optional[Iterable[str]] = None) -> List[Dict[str, str]]:
        """Sous-positions d'un chapitre, éventuellement restreintes à des positions."""
        wanted = {h.replace(".", "") for h in headings} if headings else None
        found: List[Dict[str, str]] = []
        chapter_label = ""

        for row in self._navigation_rows(
            self.fetch(page="chapitre", section=section)
        ):
            if row["code"] == chapter:
                chapter_label = row["label"]

        for rng in self._navigation_rows(
            self.fetch(page="range", section=section, chapitre=chapter)
        ):
            heading = f"{chapter}{rng['code']}"
            if wanted is not None and heading not in wanted:
                continue
            for pos in self._navigation_rows(
                self.fetch(page="position", section=section,
                           chapitre=chapter, range=rng["code"])
            ):
                query = urllib.parse.parse_qs(urllib.parse.urlparse(pos["href"]).query)
                sub_code = (query.get("sous_position") or [""])[0]
                if not sub_code:
                    self.errors.append(f"{pos['href']} : sous_position absente de l'URL")
                    continue
                found.append({
                    "sub_position": sub_code,
                    "position": (query.get("position") or [""])[0],
                    "section": section,
                    "chapter": chapter,
                    "range": rng["code"],
                    "chapter_label": chapter_label,
                    "heading_label": rng["label"],
                    "leaf_label": pos["label"],
                })
        return found

    # ----- feuille --------------------------------------------------------

    def _tables(self, html: str) -> Dict[str, List[List[str]]]:
        """Tables de la fiche, indexées par leur titre d'en-tête."""
        result: Dict[str, List[List[str]]] = {}
        for body in _TABLE.findall(html):
            rows = _TR.findall(body)
            if not rows:
                continue
            title = _text(rows[0])
            cells = [[_text(c) for c in _CELL.findall(r)] for r in rows]
            result[title] = [c for c in cells if c]
        return result

    def leaf_detail(self, leaf: Dict[str, str]) -> Dict:
        html = self.fetch(
            page="sous_position",
            section=leaf["section"],
            chapitre=leaf["chapter"],
            range=leaf["range"],
            position=leaf["position"],
            sous_position=leaf["sub_position"],
        )
        tables = self._tables(html)
        now = datetime.now(timezone.utc)
        code = leaf["sub_position"]
        source_url = (
            f"{BASE_URL}?page=sous_position&section={leaf['section']}"
            f"&chapitre={leaf['chapter']}&range={leaf['range']}"
            f"&position={leaf['position']}&sous_position={code}"
        )

        taxes: Dict[str, Dict] = {}
        gaps: List[str] = []
        for row in tables.get("Taxes Ad-Valorem", []):
            if len(row) < 2:
                continue
            published = row[0]
            canonical, official_label = DGD_TAX_CODES.get(published, (None, None))
            rate = _rate(row[1])
            if canonical is None and published not in DGD_TAX_CODES:
                # Taxe publiée mais inconnue du référentiel : conservée sous son
                # code publié et signalée, plutôt que silencieusement écartée.
                canonical = published.replace(".", "")
                gaps.append(f"taxe non répertoriée : {published}")
            if rate is None:
                gaps.append(f"taux non publié pour {published}")
                continue
            taxes[canonical] = {
                "code": canonical,
                "label_published": published,
                "rate": rate,
                "raw": f"{row[1]}%",
                "source": SOURCE_NAME,
                "source_root_url": f"{BASE_URL}?page=tarif_douanier",
                "official_dgd_code": published,
                "official_dgd_label": official_label,
                "label_verification": "PUBLISHED_BY_DGD",
                "observation": row[2] if len(row) > 2 and row[2] else None,
            }

        specific = [
            {
                "label_published": row[0],
                "quota_per_unit": _rate(row[1]) if len(row) > 1 else None,
                "unit_count": row[2] if len(row) > 2 else None,
                "unit": row[3] if len(row) > 3 else None,
                "observation": row[4] if len(row) > 4 and row[4] else None,
                "source": SOURCE_NAME,
            }
            for row in tables.get("Taxes spécifiques annexes", [])
            if row and row[0] not in ("Taxe",)
        ]

        advantages = [
            {
                "tax_published": row[0],
                "rate": _rate(row[1]) if len(row) > 1 else None,
                "official_journal": row[2] if len(row) > 2 and row[2] else None,
                "document": row[3] if len(row) > 3 and row[3] else None,
                "source": SOURCE_NAME,
            }
            for row in tables.get("Avantages fiscaux", [])
            if row and row[0] not in ("Taxe",)
        ]

        formalities = [
            {
                "text_verbatim": row[1],
                "fap_code": row[0],
                "source": SOURCE_NAME,
                "match_status": "PUBLISHED_BY_DGD",
            }
            for row in tables.get("Formalités Administratives Particulières", [])
            if len(row) > 1 and row[0] not in ("Code",)
        ]

        if not taxes:
            gaps.append("aucune taxe ad valorem publiée pour cette sous-position")

        heading = f"{leaf['chapter']}.{leaf['range']}"
        return {
            "raw_code": f"{leaf['chapter']}.{leaf['range']}.{leaf['position']}",
            "hs_code": code,
            # Forme publiée par la source de référence : « 3010.00 », soit les
            # deux derniers chiffres détachés.
            "display_code": (
                f"Sous-position {leaf['position'][:-2]}.{leaf['position'][-2:]}"
                if len(leaf["position"]) > 2 else f"Sous-position {leaf['position']}"
            ),
            "heading": heading,
            "chapter": leaf["chapter"],
            "section": leaf["section"],
            "name": leaf["leaf_label"],
            "description": leaf["leaf_label"],
            "designation_full": " > ".join(
                p for p in (leaf["chapter_label"], leaf["heading_label"],
                            leaf["leaf_label"]) if p
            ),
            "taxes": taxes,
            "specific_taxes": specific,
            "source_gaps": gaps,
            "advantages": [],
            "tax_advantages": advantages,
            "formalities": formalities,
            "lf2026_provisions": None,
            "legal_refs": [
                {
                    "ref": "Loi n° 79-07 du 21 juillet 1979 portant code des douanes, "
                           "modifiée et complétée",
                    "doc": "data/sources/DZA/legislation/code_douanes_79-07.pdf",
                },
            ],
            "source": SOURCE_NAME,
            "source_root_url": f"{BASE_URL}?page=tarif_douanier",
            "source_url": source_url,
            "crawled_at": now.isoformat(),
            "date_consulted": now.strftime("%Y-%m-%d"),
            "source_quality": "crawled_authentic_primary",
            "data_status": "OK" if taxes else "REVIEW_REQUIRED",
        }

    # ----- orchestration --------------------------------------------------

    def run(self, chapters: List[str],
            headings: Optional[List[str]] = None) -> List[Dict]:
        sections = self.chapter_sections()
        positions: List[Dict] = []
        for chapter in chapters:
            section = sections.get(chapter)
            if section is None:
                self.errors.append(f"chapitre {chapter} absent du portail DGD")
                logger.error("chapitre %s absent du portail DGD", chapter)
                continue
            leaves = self.leaves(section, chapter, headings)
            logger.info("chapitre %s (section %s) : %d sous-positions",
                        chapter, section, len(leaves))
            for index, leaf in enumerate(leaves, 1):
                positions.append(self.leaf_detail(leaf))
                if index % 20 == 0:
                    logger.info("  %d/%d", index, len(leaves))
        return positions


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--chapters", required=True,
                        help="chapitres SH séparés par des virgules (ex. 22,24)")
    parser.add_argument("--headings", default="",
                        help="restreindre à ces positions (ex. 96.14)")
    parser.add_argument("--out", required=True, help="fichier JSON de sortie")
    parser.add_argument("--relay", default=DEFAULT_RELAY,
                        help="relais de lecture ; vide pour un accès direct")
    parser.add_argument("--delay", type=float, default=0.5,
                        help="pause entre requêtes, en secondes")
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
    scraper = DgdOfficialScraper(relay=args.relay, delay=args.delay)
    chapters = [c.strip() for c in args.chapters.split(",") if c.strip()]
    headings = [h.strip() for h in args.headings.split(",") if h.strip()] or None

    started = datetime.now(timezone.utc)
    positions = scraper.run(chapters, headings)
    finished = datetime.now(timezone.utc)

    payload = {
        "country": "DZA",
        "country_name": "Algérie",
        "source": SOURCE_NAME,
        "source_root_url": f"{BASE_URL}?page=tarif_douanier",
        "source_quality": "crawled_authentic_primary",
        "source_provenance": (
            "Portail tarifaire de la Direction Générale des Douanes, lu à travers "
            "un relais de lecture : le pare-feu applicatif du site bloque l'accès "
            "direct depuis un hébergeur. Le relais ne transforme pas la page."
        ),
        "built_by": "backend/crawlers/countries/algeria_dgd_official_scraper.py",
        "policy": (
            "Données crawlées uniquement. Aucun taux estimé. Une cellule vide reste "
            "une absence, jamais un zéro. Les avantages fiscaux publiés par la DGD "
            "sont conservés verbatim dans tax_advantages et ne sont pas versés dans "
            "fiscal_advantages : ce sont des exonérations conditionnelles, pas des "
            "taux applicables de plein droit."
        ),
        "extracted_at": started.isoformat(),
        "stats": {
            "chapters": chapters,
            "headings": headings,
            "sub_positions": len(positions),
            "http_requests": scraper.requests,
            "errors": len(scraper.errors),
            "started_at": started.isoformat(),
            "finished_at": finished.isoformat(),
        },
        "errors": scraper.errors,
        "sub_positions": positions,
    }
    with open(args.out, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=1)

    logger.info("%d sous-positions écrites dans %s (%d requêtes, %d erreurs)",
                len(positions), args.out, scraper.requests, len(scraper.errors))
    return 1 if scraper.errors else 0


if __name__ == "__main__":
    sys.exit(main())
