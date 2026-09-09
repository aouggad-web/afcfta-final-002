#!/usr/bin/env python3
"""Re-complète l'énumération TUN pour les chapitres vides : requête chapitre
re-tentée, puis repli par rangée (préfixe 4 chiffres)."""
import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path

import httpx

try:
    from ._tunisia_parse import parse_enumeration, verify_tls_default
except ImportError:
    # Exécution directe (`python tunisia_enum_complete.py`) : pas de paquet
    # parent connu pour un import relatif. Repli sur sys.path.
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from _tunisia_parse import parse_enumeration, verify_tls_default

BASE = "https://www.douane.gov.tn/tarifwebnew/getresultat.php"
HEADERS = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) Chrome/126.0"}
OUT = (
    Path(__file__).resolve().parent.parent.parent
    / "data"
    / "crawled"
    / "TUN_enumeration_2026-08.json"
)


async def main():
    enum = json.loads(OUT.read_text(encoding="utf-8"))
    chapters = enum["chapters"]
    empty = [ch for ch, codes in chapters.items() if not codes]
    print("chapitres vides:", empty, flush=True)

    async with httpx.AsyncClient(
        headers=HEADERS, verify=verify_tls_default(), timeout=50, follow_redirects=True
    ) as client:
        for ch in empty:
            got = {}
            for attempt in range(3):
                try:
                    r = await client.get(BASE, params={"rech": "1", "mcle": ch})
                    got = parse_enumeration(r.text)
                    if got:
                        break
                    if attempt < 2:
                        print(
                            f"ch.{ch}: tentative {attempt+1} réponse vide/non parsable, retry",
                            flush=True,
                        )
                        await asyncio.sleep(5)
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
                    got2 = {}
                    for attempt in range(3):
                        try:
                            r2 = await client.get(BASE, params={"rech": "1", "mcle": hh})
                            got2 = parse_enumeration(r2.text)
                            if got2:
                                break
                            if attempt == 2:
                                print(
                                    f"  ch.{ch} heading {hh}: réponse vide après 3 essais",
                                    flush=True,
                                )
                            else:
                                await asyncio.sleep(5)
                        except Exception:
                            if attempt == 2:
                                print(f"  ch.{ch} heading {hh}: abandon après 3 essais", flush=True)
                            await asyncio.sleep(5)
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
