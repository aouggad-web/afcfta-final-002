#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
egypt_customs_official_scraper.py

Crawler du tarif douanier OFFICIEL de l'Autorité Égyptienne des Douanes
(customs.gov.eg/Services/Tarif) :

  1. listing paginé : /Services/Tarif?page=N&type=1&chapterId=C  (codes + désignations AR)
  2. détail par sous-position : POST /Services/TrfDetails?trfNumber=...&trfType=1
     → JSON officiel : Taxes (verbatim AR), Instructions (codes ر/غ/ق = préférences
       FTA — dont ZLECAf groupes A/B —, exemptions, formalités), InstructionCodes

Aucune estimation : les textes arabes sont conservés verbatim avec leur code
officiel d'instruction et l'URL source.

Sortie : backend/data/crawled/EGY_official_progress_{chapter}.json puis fusion.
"""
from __future__ import annotations

import asyncio
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import httpx

BASE = "https://www.customs.gov.eg"
LIST_URL = f"{BASE}/Services/Tarif"
DETAIL_URL = f"{BASE}/Services/TrfDetails"
OUT_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "crawled"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36",
    "Accept-Language": "ar,en;q=0.8,fr;q=0.5",
    "X-Requested-With": "XMLHttpRequest",
    "Referer": LIST_URL,
}
DELAY = 1.2
CONCURRENCY = 3

CODE_RE = re.compile(r"(\d{2}/\d{2}/\d{2}/\d{2}/\d{2})")


class EgyptOfficialScraper:
    def __init__(self):
        self.client = None
        self.sem = None
        self.errors: list[dict] = []

    async def _init(self):
        if not self.client:
            self.client = httpx.AsyncClient(
                headers=HEADERS, timeout=40.0, follow_redirects=True, verify=False
            )
            self.sem = asyncio.Semaphore(CONCURRENCY)

    async def _get(self, url, params=None, retries=3):
        for attempt in range(retries):
            try:
                await asyncio.sleep(DELAY)
                async with self.sem:
                    r = await self.client.get(url, params=params)
                if r.status_code == 200:
                    return r.text
                self.errors.append({"url": url, "status": r.status_code})
                await asyncio.sleep(3 * (attempt + 1))
            except Exception as e:
                self.errors.append({"url": url, "error": str(e)[:120]})
                await asyncio.sleep(3 * (attempt + 1))
        return None

    async def _post(self, url, params=None, retries=3):
        for attempt in range(retries):
            try:
                await asyncio.sleep(DELAY)
                async with self.sem:
                    r = await self.client.post(url, params=params)
                if r.status_code == 200:
                    try:
                        return r.json()
                    except Exception:
                        return None
                self.errors.append({"url": url, "status": r.status_code})
                await asyncio.sleep(3 * (attempt + 1))
            except Exception as e:
                self.errors.append({"url": url, "error": str(e)[:120]})
                await asyncio.sleep(3 * (attempt + 1))
        return None

    async def list_chapter(self, chapter_id: int, trf_type: int = 1) -> list[dict]:
        """Toutes les sous-positions d'un chapitre (toutes les pages)."""
        rows: dict[str, dict] = {}
        page = 1
        while True:
            html = await self._get(LIST_URL, params={"page": page, "type": trf_type, "chapterId": chapter_id})
            if not html:
                break
            found = CODE_RE.findall(html)
            if not found:
                break
            new_codes = [c for c in found if c not in rows]
            for code in new_codes:
                rows[code] = {"code": code, "chapter": chapter_id}
            # pagination : s'arrêter quand plus de nouvelles pages
            pages_in_html = sorted({int(p) for p in re.findall(r"page=(\d+)", html)})
            max_page = max(pages_in_html) if pages_in_html else page
            if page >= max_page or not new_codes:
                break
            page += 1
        return list(rows.values())

    async def detail(self, code: str, trf_type: int = 1) -> dict | None:
        return await self._post(DETAIL_URL, params={"trfNumber": code, "trfType": trf_type})

    def _parse_taxes(self, taxes: list[str]) -> dict:
        """Taxes verbatim + tentative de lecture purement littérale du taux publié."""
        out = {}
        mapping = {"ضريبة الوارد": "ID", "ضريبة قيمه مضافه": "VAT",
                   "ضريبة الدمغة": "STAMP", "رسم دعم": "SUPPORT"}
        for raw in taxes or []:
            label = raw.split(":")[0].strip()
            value = raw.split(":", 1)[1].strip() if ":" in raw else ""
            code = None
            for ar, cd in mapping.items():
                if ar in label:
                    code = cd
                    break
            num = None
            m = re.search(r"(\d+(?:\.\d+)?)\s*%", value)
            if m:
                num = float(m.group(1))
            elif "صفر" in value:
                num = 0.0
            key = code or label
            out[key] = {
                "code": code,
                "label_ar": label,
                "raw": value,
                "rate": num,
                "rate_parsed": num is not None,
            }
        return out

    async def crawl_chapter(self, chapter_id: int, trf_type: int = 1) -> list[dict]:
        rows = await self.list_chapter(chapter_id, trf_type)
        if not rows:
            return []

        async def one(row):
            det = await self.detail(row["code"], trf_type)
            if not det:
                row["data_status"] = "DETAIL_UNAVAILABLE"
                return row
            row.update({
                "number": det.get("Number"),
                "short_desc_ar": det.get("ShortDesc"),
                "desc_ar": det.get("Desc"),
                "taxes": self._parse_taxes(det.get("Taxes")),
                "taxes_verbatim": det.get("Taxes"),
                "instructions": det.get("Instructions"),
                "instruction_codes": det.get("InstructionCodes"),
                "data_status": "OK",
                "source": "customs.gov.eg (Autorité Égyptienne des Douanes)",
                "source_url": f"{LIST_URL}?type={trf_type}&chapterId={chapter_id}",
                "detail_endpoint": f"POST {DETAIL_URL}?trfNumber={det.get('Number')}&trfType={trf_type}",
            })
            return row

        tasks = [one(r) for r in rows]
        results = await asyncio.gather(*tasks)
        return [r for r in results if r]

    def save(self, chapter_id: int, rows: list[dict]):
        doc = {
            "chapter": chapter_id,
            "trf_type": 1,
            "count": len(rows),
            "extracted_at": datetime.now(timezone.utc).isoformat(),
            "data": rows,
        }
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        p = OUT_DIR / f"EGY_official_progress_{chapter_id:02d}.json"
        p.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"ch.{chapter_id:02d}: {len(rows)} positions -> {p.name}", flush=True)


async def main(chapters: list[int] | None = None):
    scraper = EgyptOfficialScraper()
    await scraper._init()
    try:
        chapters = chapters or list(range(1, 98))
        for ch in chapters:
            out = OUT_DIR / f"EGY_official_progress_{ch:02d}.json"
            if out.exists():
                print(f"ch.{ch:02d}: déjà crawlé, skip", flush=True)
                continue
            rows = await scraper.crawl_chapter(ch)
            scraper.save(ch, rows)
    finally:
        await scraper._close() if hasattr(scraper, "_close") else None
        if scraper.client:
            await scraper.client.aclose()
    err = OUT_DIR / "EGY_official_errors.json"
    err.write_text(json.dumps(scraper.errors, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"erreurs: {len(scraper.errors)} -> {err.name}", flush=True)


if __name__ == "__main__":
    args = sys.argv[1:]
    chs = [int(a) for a in args] if args else None
    asyncio.run(main(chs))
