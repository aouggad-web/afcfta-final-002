#!/usr/bin/env python3
"""Re-complète l'énumération TUN pour les préfixes (4 chiffres) où des codes
présents dans le crawl national de juin manquent à l'énumération du 2026-08-29
(due à des requêtes transitoirement échouées pendant le repli par rangée).
Méthode DZA : source authentique uniquement, sauvegarde incrémentale, aucun taux inventé."""
import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path

import httpx

from ._tunisia_parse import parse_enumeration as parse
from ._tunisia_parse import verify_tls_default

BASE = "https://www.douane.gov.tn/tarifwebnew/getresultat.php"
HEADERS = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) Chrome/126.0"}
OUT = Path("backend/data/crawled/TUN_enumeration_2026-08.json")
CRAWL = Path("backend/data/crawled/TUN_tariffs.json")


async def fetch_prefix(client, hh):
    for attempt in range(5):
        try:
            r = await client.get(BASE, params={"rech": "1", "mcle": hh})
            got = parse(r.text)
            if got:
                return got, None
            if r.status_code == 200:
                # 200 mais aucune paire (code, libellé) : page vide / parse échoué.
                return {}, "empty or unparseable response"
            return {}, f"HTTP {r.status_code}"
        except Exception as e:
            if attempt == 4:
                return {}, f"{type(e).__name__}: {e}"
            await asyncio.sleep(4 + attempt * 3)
    return {}, "unreachable"


async def main():
    enum = json.loads(OUT.read_text(encoding="utf-8"))
    chapters = enum["chapters"]
    enum_codes = set()
    for ch, codes in chapters.items():
        enum_codes.update(codes.keys())
    crawl = json.loads(CRAWL.read_text(encoding="utf-8"))
    crawl_codes = [s["hs_code"] for s in crawl["sub_positions"]]
    missing = [c for c in crawl_codes if c not in enum_codes]
    prefixes = sorted(set(c[:4] for c in missing))
    print(f"codes absents: {len(missing)} | préfixes à re-requêter: {len(prefixes)}", flush=True)

    failed = []
    async with httpx.AsyncClient(
        headers=HEADERS, verify=verify_tls_default(), timeout=60, follow_redirects=True
    ) as client:
        for i, pf in enumerate(prefixes, 1):
            got, err = await fetch_prefix(client, pf)
            if got:
                ch = pf[:2]
                merged = chapters.setdefault(ch, {})
                new = 0
                for k, v in got.items():
                    if k not in merged:
                        merged[k] = v
                        new += 1
                print(f"[{i}/{len(prefixes)}] {pf}: {len(got)} codes (+{new} nouveaux)", flush=True)
            else:
                failed.append({"prefix": pf, "error": err})
                print(f"[{i}/{len(prefixes)}] {pf}: ÉCHEC {err}", flush=True)
            await asyncio.sleep(1.2)
            if i % 10 == 0:
                enum["extracted_at"] = datetime.now(timezone.utc).isoformat()
                OUT.write_text(json.dumps(enum, ensure_ascii=False, indent=1), encoding="utf-8")

    enum["extracted_at"] = datetime.now(timezone.utc).isoformat()
    if failed:
        enum["recompletion_failures"] = failed
    else:
        enum.pop("recompletion_failures", None)
    enum["note"] += " Re-complétion ciblée des préfixes manquants le 2026-08-29 (retries x5)."
    OUT.write_text(json.dumps(enum, ensure_ascii=False, indent=1), encoding="utf-8")

    total = sum(len(v) for v in chapters.values())
    ec = set()
    for codes in chapters.values():
        ec.update(codes)
    still = len(set(crawl_codes) - ec)
    print(
        f"TOTAL: {total} codes | échecs: {len(failed)} | codes du crawl toujours absents: {still}",
        flush=True,
    )


if __name__ == "__main__":
    asyncio.run(main())
