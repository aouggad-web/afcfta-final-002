#!/usr/bin/env python3
"""
Runner unifié du pipeline de collecte tarifaire authentique (54 pays ZLECAf).

Principe : **authentique uniquement, avec source**. Aucune estimation produite.

Modes
-----
--dry-run   (par défaut) : aucun accès réseau. Cartographie la couverture
            effective des données existantes + l'état du manifeste, écrit
            data/crawled/coverage_report.json. Exécutable partout, y compris
            sans secrets ni réseau.

--run       Lance réellement la collecte. Pour chaque pays, dispatche vers le
            crawler authentique disponible, normalise au schéma canonique,
            VALIDE l'authenticité (rejette le vide/estimé) puis écrit
            data/crawled/{ISO3}_tariffs.json. Nécessite réseau + secrets.
            (Le branchement des scrapers réels par bloc est progressif ; un pays
            sans scraper implémenté est rapporté 'skipped: no_authentic_crawler'
            plutôt que rempli de données estimées.)

Exemples
--------
    python backend/scripts/crawl_all_countries.py            # dry-run, tous
    python backend/scripts/crawl_all_countries.py --country KEN
    python backend/scripts/crawl_all_countries.py --run --country MAR
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from tariff_crawl.canonical import validate_authenticity  # noqa: E402
from tariff_crawl.coverage import CRAWLED_DIR, build_coverage_report, format_report  # noqa: E402
from tariff_crawl.manifest import build_manifest  # noqa: E402


def cmd_dry_run(countries: list[str] | None) -> int:
    manifest = build_manifest()
    report = build_coverage_report()

    if countries:
        sel = {c.upper() for c in countries}
        report["countries"] = [c for c in report["countries"] if c["iso3"] in sel]

    print(format_report(report))
    print()

    # Lacunes : pays sans source authentique prête (à implémenter / sans données).
    to_implement = [
        iso
        for iso, d in manifest.items()
        if all(
            s.get("status") != "ready"
            for s in d["sources_chain"]
            if s["provenance"] == "national_crawl"
        )
    ]
    print(f"Pays avec crawl national encore à implémenter : {len(to_implement)}")

    out = CRAWLED_DIR / "coverage_report.json"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Rapport écrit : {out}")
    return 0


def cmd_run(countries: list[str] | None) -> int:
    """Collecte réelle. Sans scraper authentique branché, on SKIP (jamais d'estimé)."""
    manifest = build_manifest()
    targets = [c.upper() for c in countries] if countries else sorted(manifest.keys())

    # Registre des crawlers authentiques branchés (étendu au fil de l'eau).
    # iso3 -> callable() renvoyant (provenance, source, source_url, positions[])
    from tariff_crawl.crawlers import AUTHENTIC_CRAWLERS  # import tardif

    results = []
    total = len(targets)
    print(f"Démarrage du crawl pays par pays : {total} pays")
    for idx, iso3 in enumerate(targets, start=1):
        print(f"\n[{idx}/{total}] {iso3} — démarrage")
        crawler = AUTHENTIC_CRAWLERS.get(iso3)
        if crawler is None:
            results.append((iso3, "skipped", "no_authentic_crawler"))
            print(f"[{idx}/{total}] {iso3} — skipped: no_authentic_crawler")
            continue
        try:
            doc = crawler()
            ok, issues = validate_authenticity(doc)
            if not ok:
                detail = "; ".join(issues)
                results.append((iso3, "rejected", detail))
                print(f"[{idx}/{total}] {iso3} — rejected: {detail}")
                continue
            out = CRAWLED_DIR / f"{iso3}_tariffs.json"
            out.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")
            detail = f"{doc['stats']['sub_positions']} positions"
            results.append((iso3, "ok", detail))
            print(f"[{idx}/{total}] {iso3} — ok: {detail}")
        except Exception as e:  # un pays en échec n'arrête pas les autres
            results.append((iso3, "error", str(e)))
            print(f"[{idx}/{total}] {iso3} — error: {e}")

    print("\nRésumé final")
    print(f"{'ISO':<5}{'STATUT':<12}DÉTAIL")
    for iso3, status, detail in results:
        print(f"{iso3:<5}{status:<12}{detail}")
    ok_count = sum(1 for _, s, _ in results if s == "ok")
    print(f"\nSuccès: {ok_count}/{len(results)}")
    return 0 if ok_count or not targets else 1


def cmd_validate_file(iso3: str) -> int:
    """Valide l'authenticité d'un fichier data/crawled/{ISO3}_tariffs.json déjà produit."""
    iso3 = iso3.upper()
    path = CRAWLED_DIR / f"{iso3}_tariffs.json"
    if not path.exists():
        print(f"✗ Fichier introuvable : {path}")
        return 2

    doc = json.loads(path.read_text(encoding="utf-8"))
    positions = doc.get("sub_positions") or doc.get("positions") or doc.get("tariff_lines") or []
    from collections import Counter

    quals = Counter(p.get("source_quality") or p.get("quality") for p in positions)

    ok, issues = validate_authenticity(doc)
    print(f"Fichier   : {path}")
    print(f"Positions : {len(positions)}")
    print(f"Qualité   : {dict(quals)}")

    # Contrôle d'INGESTION : crawled_data_service indexe-t-il réellement ces
    # positions ? Détecte le bug « fichier plein mais lu vide » (schéma sans
    # normaliseur correspondant — cas EGY/GHA), invisible à la seule validation
    # d'authenticité.
    indexed = _indexed_count(iso3)
    print(f"Indexées  : {indexed} / {len(positions)} (via crawled_data_service)")
    ingestion_ok = True
    if positions and indexed == 0:
        ingestion_ok = False
        print(
            f"✗ INGESTION CASSÉE — 0 position indexée alors que le fichier en contient "
            f"{len(positions)}. Le schéma ne correspond à aucun normaliseur : ajouter un "
            f"_normalize_{iso3.lower()} dans services/crawled_data_service.py, ou émettre "
            f"le schéma canonique (code_raw/code_clean + taxes en liste)."
        )
    elif positions and indexed < len(positions) * 0.5:
        print(
            f"⚠ INGESTION PARTIELLE — seulement {indexed}/{len(positions)} positions indexées ; "
            f"vérifier le normaliseur."
        )

    if ok and ingestion_ok:
        print("✓ AUTHENTIQUE & INGESTIBLE — le fichier passe la validation et est servable.")
        return 0
    if not ok:
        print("✗ REJETÉ — problèmes d'authenticité :")
        for i in issues:
            print(f"   - {i}")
    return 1


def _indexed_count(iso3: str) -> int:
    """Nombre de positions effectivement indexées par crawled_data_service."""
    try:
        from services.crawled_data_service import CrawledDataService

        svc = CrawledDataService()
        svc.load(force=True)
        svc._ensure_country_loaded(iso3)
        return len(svc._code_index.get(iso3, {}))
    except Exception as e:  # ne bloque pas la validation d'authenticité
        print(f"  (contrôle d'ingestion indisponible : {e})")
        return -1


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="Pipeline de collecte tarifaire authentique (54 pays)."
    )
    ap.add_argument("--run", action="store_true", help="Collecte réelle (réseau + secrets requis).")
    ap.add_argument("--country", action="append", help="Limiter à un/des pays (ISO3). Répétable.")
    ap.add_argument(
        "--validate-file",
        metavar="ISO3",
        help="Valide l'authenticité de data/crawled/{ISO3}_tariffs.json déjà produit.",
    )
    args = ap.parse_args(argv)

    if args.validate_file:
        return cmd_validate_file(args.validate_file)
    if args.run:
        return cmd_run(args.country)
    return cmd_dry_run(args.country)


if __name__ == "__main__":
    raise SystemExit(main())
