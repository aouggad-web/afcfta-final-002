#!/usr/bin/env python3
"""Vérification d'énumération TUN : codes + libellés par chapitre depuis
douane.gov.tn/tarifwebnew/getresultat.php (l'app de détail est cassée côté source).
Sortie : backend/data/crawled/TUN_enumeration_2026-08.json"""
import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path

import httpx

from ._tunisia_parse import parse_enumeration, verify_tls_default

BASE = "https://www.douane.gov.tn/tarifwebnew/getresultat.php"
OUT = (
    Path(__file__).resolve().parent.parent.parent
    / "data"
    / "crawled"
    / "TUN_enumeration_2026-08.json"
)
HEADERS = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) Chrome/126.0"}


async def crawl_chapter(client, ch):
    try:
        r = await client.get(BASE, params={"rech": "1", "mcle": f"{ch:02d}"})
        if r.status_code != 200:
            return ch, None, f"HTTP {r.status_code}"
        pairs = list(parse_enumeration(r.text).items())
        return ch, pairs, None
    except Exception as e:
        return ch, None, str(e)[:100]


async def main():
    out = {}
    errors = []
    async with httpx.AsyncClient(
        headers=HEADERS, verify=verify_tls_default(), timeout=40, follow_redirects=True
    ) as client:
        for ch in range(1, 98):
            ch_id, pairs, err = await crawl_chapter(client, ch)
            if err:
                errors.append({"chapter": ch, "error": err})
                print(f"ch.{ch:02d}: ERREUR {err}", flush=True)
            else:
                # dédupliquer en gardant l'ordre
                seen = {}
                for code, label in pairs:
                    if code not in seen:
                        seen[code] = label
                out[f"{ch:02d}"] = seen
                print(f"ch.{ch:02d}: {len(seen)} codes", flush=True)
            await asyncio.sleep(1.2)
    doc = {
        "country": "TUN",
        "source": "douane.gov.tn/tarifwebnew/getresultat.php (énumération officielle)",
        "note": "Vérification d'énumération : codes et libellés officiels. Les taux du fichier "
        "TUN_tariffs.json proviennent du crawl tarifweb2025 (juin 2026) — l'hôte "
        "tarifweb2025.douane.finances.tn est hors ligne depuis et l'app de détail "
        "tarifwebnew ne publie plus les pages de taux côté serveur.",
        "extracted_at": datetime.now(timezone.utc).isoformat(),
        "chapters": out,
        "errors": errors,
    }
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=1), encoding="utf-8")
    total = sum(len(v) for v in out.values())
    print(f"TOTAL: {total} codes | erreurs: {len(errors)} -> {OUT.name}", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
