"""
National Tax Documents Scraper — complétion tarifaire au-delà du TEC
=====================================================================

Collecte les documents officiels nationaux (douanes, administrations fiscales,
lois de finances) qui énoncent les droits et taxes d'effet équivalent (DTE),
la TVA, les accises et les redevances nationales — NON publiés par les TEC
régionaux (CEDEAO, CEMAC, EAC, SACU).

Doctrine (MISSION_TARIFS_AFRICAINS.md — « pas de mock, pas d'hallucination,
pas d'extrapolation ») :

- ce scraper N'EXTRAIT AUCUN taux : il vérifie la joignabilité des portails
  (mode ``verify``) et archive les documents bruts + SHA-256 (mode ``collect``) ;
- aucun taux ne peut être enregistré sans un document archivé ET une référence
  légale — l'extraction par instrument est confiée à des adaptateurs dédiés
  (à écrire document par document) validés par ``crawlers.validators`` ;
- un pays sans document archivé reste PENDING_OFFICIAL_COLLECTION (jamais
  complété par défaut, estimation ou copie d'un autre pays).

Usage :
    scraper = NationalTaxScraper("KEN", mode="verify")
    result = await scraper.run()
"""

import hashlib
import json
import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from ..all_countries_registry import get_country_config, get_national_tax_source
from ..base_scraper import BaseScraper, ScraperConfig

logger = logging.getLogger(__name__)

DATA_ROOT = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "data",
)
NATIONAL_TAX_DIR = os.path.join(DATA_ROOT, "national_taxes")
RAW_DOCS_DIR = os.path.join(NATIONAL_TAX_DIR, "raw")
STATUS_PATH = os.path.join(NATIONAL_TAX_DIR, "collection_status.json")


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class NationalTaxScraper(BaseScraper):
    """
    Scraper de complétion fiscale nationale.

    Modes :
      - "verify"  : vérifie la joignabilité de chaque URL source du pays et
                    journalise le statut HTTP (aucune donnée enregistrée).
      - "collect" : télécharge et archive les documents bruts + SHA-256 ;
                    N'ENREGISTRE AUCUN TAUX (fail-closed par construction).
    """

    def __init__(
        self,
        country_code: str,
        db_client: Optional[Any] = None,
        config: Optional[ScraperConfig] = None,
        mode: str = "verify",
    ):
        super().__init__(country_code, db_client=db_client, config=config)
        self.mode = mode
        self.source_cfg = get_national_tax_source(country_code)
        if self.source_cfg is None:
            raise ValueError(
                f"Aucune configuration de complétion fiscale nationale pour "
                f"{country_code} (pays déjà complété au niveau national ou inconnu)."
            )

    # ------------------------------------------------------------------
    # Mode verify : statut HTTP des portails officiels du pays
    # ------------------------------------------------------------------
    async def _verify_sources(self) -> Dict[str, Any]:
        urls: List[Dict[str, Optional[str]]] = []

        customs_url = (self._country_config or {}).get("customs_url")
        if customs_url:
            urls.append({"role": "customs_administration", "url": customs_url})

        tax = self.source_cfg.get("tax_authority") or {}
        if tax.get("url"):
            urls.append({"role": "tax_authority", "url": tax["url"]})

        checked = []
        for entry in urls:
            status_code, final_url = await self._probe(entry["url"])
            checked.append(
                {
                    "role": entry["role"],
                    "url": entry["url"],
                    "final_url": final_url,
                    "http_status": status_code,
                    "reachable": 200 <= (status_code or 0) < 400,
                    "checked_at": _now_iso(),
                }
            )

        return {
            "mode": "verify",
            "country_code": self.country_code,
            "collection_status": self.source_cfg["collection_status"],
            "checked": checked,
            "checked_at": _now_iso(),
        }

    async def _probe(self, url: str):
        """Probe HTTP léger — retourne (status_code, final_url)."""
        try:
            response = await self.http_client.get(url, timeout=self._config.timeout)
            self._stats["requests_made"] += 1
            return response.status_code, str(response.url)
        except Exception as e:
            self._stats["requests_failed"] += 1
            logger.warning(f"Probe failed for {url}: {e}")
            return None, url

    # ------------------------------------------------------------------
    # Mode collect : archivage brut + SHA-256, AUCUNE extraction de taux
    # ------------------------------------------------------------------
    async def _collect_documents(self) -> Dict[str, Any]:
        documents: List[Dict[str, Any]] = []
        for doc in self.source_cfg.get("documents_to_collect", []):
            url = doc.get("url")
            if not url:
                documents.append(
                    {
                        "instrument": doc.get("instrument"),
                        "status": "NOT_COLLECTED",
                        "reason": "URL_SOURCE_ABSENT",
                    }
                )
                continue
            status_code, _ = await self._probe(url)
            if not (status_code and 200 <= status_code < 400):
                documents.append(
                    {
                        "instrument": doc.get("instrument"),
                        "url": url,
                        "status": "NOT_COLLECTED",
                        "reason": f"HTTP_{status_code or 'ERROR'}",
                    }
                )
                continue
            try:
                response = await self.http_client.get(url, timeout=self._config.timeout)
                self._stats["requests_made"] += 1
                payload = response.content
                sha = _sha256_bytes(payload)
                country_dir = os.path.join(RAW_DOCS_DIR, self.country_code)
                os.makedirs(country_dir, exist_ok=True)
                fname = (
                    f"{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}_"
                    f"{_sha256_bytes(url.encode('utf-8'))[:10]}.bin"
                )
                fpath = os.path.join(country_dir, fname)
                with open(fpath, "wb") as fh:
                    fh.write(payload)
                documents.append(
                    {
                        "instrument": doc.get("instrument"),
                        "url": url,
                        "status": "RAW_ARCHIVED",
                        "http_status": status_code,
                        "sha256": sha,
                        "size_bytes": len(payload),
                        "archived_path": os.path.relpath(fpath, DATA_ROOT),
                        "archived_at": _now_iso(),
                        "rate_extraction": "FORBIDDEN_WITHOUT_DEDICATED_ADAPTER",
                    }
                )
            except Exception as e:
                self._stats["requests_failed"] += 1
                logger.warning(f"Collect failed for {url}: {e}")
                documents.append(
                    {
                        "instrument": doc.get("instrument"),
                        "url": url,
                        "status": "NOT_COLLECTED",
                        "reason": str(e)[:200],
                    }
                )

        result = {
            "mode": "collect",
            "country_code": self.country_code,
            "documents": documents,
            "collected_at": _now_iso(),
        }
        # Persistance fichier systématique (le statut de collecte ne dépend
        # pas de la présence d'un client Mongo).
        self._persist_status(result)
        return result

    def _persist_status(self, result: Dict[str, Any]) -> None:
        os.makedirs(NATIONAL_TAX_DIR, exist_ok=True)
        statuses: Dict[str, Any] = {}
        if os.path.exists(STATUS_PATH):
            try:
                with open(STATUS_PATH, "r", encoding="utf-8") as fh:
                    statuses = json.load(fh)
            except Exception:
                statuses = {}
        statuses[self.country_code] = result
        with open(STATUS_PATH, "w", encoding="utf-8") as fh:
            json.dump(statuses, fh, ensure_ascii=False, indent=2)

    # ------------------------------------------------------------------
    # Interface BaseScraper
    # ------------------------------------------------------------------
    async def scrape(self) -> Dict[str, Any]:
        if self.mode == "verify":
            return await self._verify_sources()
        return await self._collect_documents()

    async def validate(self, data: Dict[str, Any]) -> bool:
        """Valide la structure du résultat (aucun champ de taux en clair accepté ici)."""
        if not isinstance(data, dict) or not data.get("country_code"):
            return False
        if data.get("mode") == "collect":
            for doc in data.get("documents", []):
                if doc.get("status") == "RAW_ARCHIVED":
                    if not doc.get("sha256") or not doc.get("archived_path"):
                        return False
                # Aucune clé portant un taux (sauf le marqueur d'interdiction)
                for key in doc:
                    k = str(key).lower()
                    if "rate" in k and k != "rate_extraction":
                        return False
        return True

    async def save_to_db(self, data: Dict[str, Any]) -> int:
        """Persiste le statut de collecte dans Mongo si disponible."""
        if not self.database:
            return 0
        collection = self.database.national_tax_collection
        doc = dict(data)
        doc["updated_at"] = _now_iso()
        await collection.replace_one({"country_code": self.country_code}, doc, upsert=True)
        return 1
