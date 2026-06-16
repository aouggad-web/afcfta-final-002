"""
Exécution de tous les convertisseurs pays-spécifiques.

Usage :
  python engine/converters/run_all.py            # tous les pays
  python engine/converters/run_all.py DZA TUN    # pays sélectionnés
  python engine/converters/run_all.py --list     # afficher les pays disponibles
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from converters import (
    cemac_converter, dza_converter, eac_converter,
    ecowas_converter, egy_converter, mar_converter,
    nga_converter, sacu_converter, tun_converter,
)

# Registre : iso3 → fonction convert()
_REGISTRY: dict[str, tuple] = {
    # Maghreb
    "DZA": (dza_converter.convert,      "Algérie — conformepro.dz",     "17 115 pos."),
    "TUN": (tun_converter.convert,      "Tunisie — douane.gov.tn",      "17 512 pos."),
    "MAR": (mar_converter.convert,      "Maroc — douane.gov.ma",        "13 114 pos."),
    "EGY": (egy_converter.convert,      "Égypte — customs.gov.eg",       "8 746 pos."),
    # SACU
    "ZAF": (lambda: sacu_converter.convert_country("ZAF"), "Afr. du Sud — sars.gov.za", "8 589 pos."),
    "BWA": (lambda: sacu_converter.convert_country("BWA"), "Botswana — sars.gov.za",    "8 589 pos."),
    "LSO": (lambda: sacu_converter.convert_country("LSO"), "Lesotho — sars.gov.za",     "8 589 pos."),
    "NAM": (lambda: sacu_converter.convert_country("NAM"), "Namibie — sars.gov.za",     "8 589 pos."),
    "SWZ": (lambda: sacu_converter.convert_country("SWZ"), "Eswatini — sars.gov.za",   "8 589 pos."),
    # EAC
    "KEN": (lambda: eac_converter.convert_country("KEN"), "Kenya — kra.go.ke",      "5 984 pos."),
    "BDI": (lambda: eac_converter.convert_country("BDI"), "Burundi — kra.go.ke",    "5 984 pos."),
    "COD": (lambda: eac_converter.convert_country("COD"), "RD Congo — kra.go.ke",   "5 984 pos."),
    "RWA": (lambda: eac_converter.convert_country("RWA"), "Rwanda — kra.go.ke",     "5 984 pos."),
    "SSD": (lambda: eac_converter.convert_country("SSD"), "Sud-Soudan — kra.go.ke", "5 984 pos."),
    "TZA": (lambda: eac_converter.convert_country("TZA"), "Tanzanie — kra.go.ke",   "5 984 pos."),
    "UGA": (lambda: eac_converter.convert_country("UGA"), "Ouganda — kra.go.ke",    "5 984 pos."),
    # CEDEAO
    "BEN": (lambda: ecowas_converter.convert_country("BEN"), "Bénin — douanes.gouv.bj",   "6 129 pos."),
    "BFA": (lambda: ecowas_converter.convert_country("BFA"), "Burkina — dgi.bf",          "6 129 pos."),
    "CIV": (lambda: ecowas_converter.convert_country("CIV"), "Côte d'Ivoire — guce.gouv.ci", "6 129 pos."),
    "GIN": (lambda: ecowas_converter.convert_country("GIN"), "Guinée — dgd.gov.gn",       "6 129 pos."),
    "MLI": (lambda: ecowas_converter.convert_country("MLI"), "Mali — douanes.gouv.ml",    "6 129 pos."),
    "NER": (lambda: ecowas_converter.convert_country("NER"), "Niger — impots.gouv.ne",    "6 129 pos."),
    "SEN": (lambda: ecowas_converter.convert_country("SEN"), "Sénégal — douanes.sn",      "6 129 pos."),
    "TGO": (lambda: ecowas_converter.convert_country("TGO"), "Togo — otr.tg",             "6 129 pos."),
    # CEDEAO — dérivés (TEC CEDEAO commun, taxes nationales documentées)
    "CPV": (lambda: ecowas_converter.convert_country("CPV"), "Cabo Verde — dérivé TEC CEDEAO", "6 129 pos."),
    "GHA": (lambda: ecowas_converter.convert_country("GHA"), "Ghana — dérivé TEC CEDEAO",       "6 129 pos."),
    "GMB": (lambda: ecowas_converter.convert_country("GMB"), "Gambie — dérivé TEC CEDEAO",      "6 129 pos."),
    "GNB": (lambda: ecowas_converter.convert_country("GNB"), "Guinée-Bissau — dérivé TEC CEDEAO", "6 129 pos."),
    "LBR": (lambda: ecowas_converter.convert_country("LBR"), "Liberia — dérivé TEC CEDEAO",     "6 129 pos."),
    "SLE": (lambda: ecowas_converter.convert_country("SLE"), "Sierra Leone — dérivé TEC CEDEAO", "6 129 pos."),
    # CEMAC
    "CMR": (lambda: cemac_converter.convert_country("CMR"), "Cameroun — DGD",    "5 239 pos."),
    "CAF": (lambda: cemac_converter.convert_country("CAF"), "Centrafrique — CEMAC", "5 239 pos."),
    "COG": (lambda: cemac_converter.convert_country("COG"), "Congo — CEMAC",     "5 239 pos."),
    "GAB": (lambda: cemac_converter.convert_country("GAB"), "Gabon — CEMAC",     "5 239 pos."),
    "TCD": (lambda: cemac_converter.convert_country("TCD"), "Tchad — CEMAC",     "5 239 pos."),
    # CEMAC — dérivé (TEC CEMAC commun via CMR)
    "GNQ": (lambda: cemac_converter.convert_country("GNQ"), "Guinée Équatoriale — dérivé TEC CEMAC", "5 239 pos."),
    # Afrique de l'Ouest
    "NGA": (nga_converter.convert, "Nigeria — customs.gov.ng", "6 363 pos."),
}


def list_countries() -> None:
    print("\nPays disponibles :\n")
    for iso3, (_, desc, size) in sorted(_REGISTRY.items()):
        print(f"  {iso3}  {desc:<40} {size}")
    print(f"\n  Total : {len(_REGISTRY)} pays\n")


def run(targets: list[str]) -> None:
    print(f"\n{'='*60}")
    print(f"  Convertisseurs AfCFTA — {len(targets)} pays")
    print(f"{'='*60}\n")

    results: list[tuple[str, int, float, str]] = []

    for iso3 in targets:
        iso3 = iso3.upper()
        if iso3 not in _REGISTRY:
            print(f"  [SKIP] {iso3} — non enregistré")
            continue
        fn, desc, _ = _REGISTRY[iso3]
        t0 = time.time()
        try:
            count = fn()
            elapsed = time.time() - t0
            results.append((iso3, count or 0, elapsed, "OK"))
        except FileNotFoundError as e:
            results.append((iso3, 0, 0.0, f"FICHIER ABSENT: {e}"))
        except Exception as e:
            results.append((iso3, 0, 0.0, f"ERREUR: {e}"))

    print(f"\n{'='*60}")
    print(f"  RÉSUMÉ\n{'='*60}")
    total_lines = 0
    ok_count    = 0
    for iso3, count, elapsed, status in results:
        flag = "✓" if status == "OK" else "✗"
        print(f"  {flag} {iso3:<5} {count:>6} lignes  {elapsed:>5.1f}s  {status}")
        if status == "OK":
            total_lines += count
            ok_count += 1

    print(f"\n  {ok_count}/{len(results)} pays convertis — {total_lines:,} lignes canoniques")
    print(f"  Sortie : engine/output/\n")


if __name__ == "__main__":
    args = sys.argv[1:]

    if not args or "--list" in args:
        list_countries()
        if not args:
            print("Lancer avec 'ALL' pour convertir tous les pays\n")
        sys.exit(0)

    if args[0].upper() == "ALL":
        targets = list(_REGISTRY.keys())
    else:
        targets = [a.upper() for a in args]

    run(targets)
