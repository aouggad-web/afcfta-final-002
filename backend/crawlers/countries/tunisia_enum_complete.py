#!/usr/bin/env python3
"""Re-complète l'énumération TUN pour les chapitres vides : requête chapitre
re-tentée, puis repli par rangée (préfixe 4 chiffres)."""
import asyncio
import json
import re
from datetime import datetime, timezone
from pathlib import Path

import httpx

BASE = "https://www.douane.gov.tn/tarifwebnew/getresultat.php"
HEADERS = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) Chrome/126.0"}
CODE_RE = re.compile(r"submit_frm_resultat\('', '', '(\d+)'\);")
LABEL_RE = re.compile(r"submit_frm_resultat\('', '', '\d+'\); return false;\">([^<]+)</td>")
OUT = Path("backend/data/crawled/TUN_enumeration_2026-08.json")


def parse(text):
    codes = CODE_RE.findall(text)
    labels = LABEL_RE.findall(text)
    if len(labels) == len(codes) and len(codes) % 2 == 0 and codes:
        return dict(zip(codes[::2], [l.strip() for l in labels[1::2]]))
    return {}


async def main():
    enum = json.loads(OUT.read_text(encoding="utf-8"))
    chapters = enum["chapters"]
    empty = [ch for ch, codes in chapters.items() if not codes]
    print("chapitres vides:", empty, flush=True)

    async with httpx.AsyncClient(headers=HEADERS, verify=False, timeout=50, follow_redirects=True) as client:
        for ch in empty:
            got = {}
            for attempt in range(3):
                try:
                    r = await client.get(BASE, params={"rech": "1", "mcle": ch})
                    got = parse(r.text)
                    break
                except Exception as e:
                    print(f"ch.{ch}: tentative {attempt+1} erreur {type(e).__name__}", flush=True)
                    await asyncio.sleep(5)
            if got:
                chapters[ch] = got
                print(f"ch.{ch}: retry OK -> {len(got)} codes", flush=True)
            else:
                # repli : requêtes par rangée
                merged = {}
                for h in range(1, 98):
                    hh = f"{ch}{h:02d}"
                    for attempt in range(3):
                        try:
                            r2 = await client.get(BASE, params={"rech": "1", "mcle": hh})
                            got2 = parse(r2.text)
                            break
                        except Exception as e:
                            if attempt == 2:
                                print(f"  ch.{ch} heading {hh}: abandon après 3 essais", flush=True)
                            await asyncio.sleep(5)
                    else:
                        got2 = {}
                    for k, v in got2.items():
                        merged.setdefault(k, v)
                    await asyncio.sleep(1.2)
                chapters[ch] = merged
                print(f"ch.{ch}: repli rangées -> {len(merged)} codes", flush=True)
            await asyncio.sleep(1.5)
            enum["chapters"] = chapters
            # sauvegarde incrémentale après CHAQUE chapitre
            OUT.write_text(json.dumps(enum, ensure_ascii=False, indent=1), encoding="utf-8")

    enum["extracted_at"] = datetime.now(timezone.utc).isoformat()
    enum["note"] += " Complétion des chapitres vides par requêtes au niveau rangée le même jour."
    OUT.write_text(json.dumps(enum, ensure_ascii=False, indent=1), encoding="utf-8")
    total = sum(len(v) for v in chapters.values())
    print(f"TOTAL FINAL: {total}", flush=True)



if __name__ == "__main__":
    asyncio.run(main())
