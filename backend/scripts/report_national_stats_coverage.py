#!/usr/bin/env python3
"""
Couverture des statistiques nationales, par pays — rapport généré
==================================================================
Écrit ``docs/data-sources/COUVERTURE_STATISTIQUES_NATIONALES.md``.

Un tableau de couverture rédigé à la main vieillit mal et ment vite. Celui-ci
est dérivé de l'état réel du dépôt et des sources, à la date d'exécution.

TROIS VOIES VERS LA STATISTIQUE NATIONALE, ET ELLES NE SE VALENT PAS
---------------------------------------------------------------------
La statistique d'un office national peut nous parvenir de trois façons, dans
un ordre de coût croissant :

  1. **Republiée harmonisée.** ILOSTAT publie les enquêtes emploi des offices
     nationaux (« LFS - Labour Force Survey », « Enquête Nationale sur
     l'Emploi »…) sous une nomenclature commune. L'UNSD fait de même pour
     l'emploi manufacturier de la cible 9.2. Rien à négocier, rien à extraire.
  2. **Collectée directement.** Un bloc dans ``data/national_stats/``, adossé
     à une publication nommée et datée. C'est la seule voie pour ce que
     personne ne republie — au premier rang, la séparation exportations
     domestiques / réexportations, décisive pour l'origine ZLECAf.
  3. **Pas encore atteinte.** Ni republiée, ni collectée.

Le palier d'un pays dit donc où porter l'effort, pas la qualité de son office.

Usage :
    python3 scripts/report_national_stats_coverage.py            # écrit le rapport
    python3 scripts/report_national_stats_coverage.py --dry-run  # affiche seulement
    python3 scripts/report_national_stats_coverage.py --no-ilo   # sans appel réseau
"""

from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = SCRIPT_DIR.parent
REPO_ROOT = BACKEND_DIR.parent
sys.path.insert(0, str(BACKEND_DIR))
sys.path.insert(0, str(SCRIPT_DIR))

OUT_FILE = REPO_ROOT / "docs" / "data-sources" / "COUVERTURE_STATISTIQUES_NATIONALES.md"

TIER_DIRECT = "A — collecte directe"
TIER_REPUBLISHED = "B — republiée harmonisée"
TIER_NONE = "C — non atteinte"


def gather(use_ilo: bool = True) -> dict:
    import production_data as pd
    from etl.iso3_m49 import ISO3_TO_M49
    from etl.mining_extended import ISO3_FR_NAME
    from services import national_official_stats as nos

    direct = set(nos.list_covered_countries())

    # Emploi manufacturier UNSD — alimenté par les offices nationaux via la
    # cible 9.2, déjà ingéré par la phase 1.
    unsd = {r["country_iso3"] for r in pd.get_manufacturing_unsd(indicator_code="SL_TLF_MANF")}

    ilo: set[str] = set()
    ilo_error = None
    if use_ilo:
        try:
            from probe_ilostat_coverage import probe

            ilo = set(probe()["countries_covered"])
        except Exception as exc:  # pragma: no cover - dépend du réseau
            ilo_error = f"{type(exc).__name__}: {exc}"

    rows = []
    for iso3 in sorted(ISO3_TO_M49):
        has_direct = iso3 in direct
        has_ilo = iso3 in ilo
        has_unsd = iso3 in unsd
        if has_direct:
            tier = TIER_DIRECT
        elif has_ilo or has_unsd:
            tier = TIER_REPUBLISHED
        else:
            tier = TIER_NONE
        rows.append(
            {
                "iso3": iso3,
                "name": ISO3_FR_NAME.get(iso3, iso3),
                "tier": tier,
                "direct": has_direct,
                "ilo": has_ilo,
                "unsd": has_unsd,
            }
        )
    return {"rows": rows, "ilo_error": ilo_error, "ilo_probed": use_ilo}


def render(data: dict) -> str:
    rows = data["rows"]
    counts = {
        t: sum(1 for r in rows if r["tier"] == t)
        for t in (TIER_DIRECT, TIER_REPUBLISHED, TIER_NONE)
    }
    today = date.today().isoformat()

    def mark(flag: bool) -> str:
        return "oui" if flag else "—"

    body = "\n".join(
        f"| {r['iso3']} | {r['name']} | {r['tier'].split(' — ')[0]} | "
        f"{mark(r['direct'])} | {mark(r['ilo'])} | {mark(r['unsd'])} |"
        for r in rows
    )

    ilo_note = ""
    if data["ilo_error"]:
        ilo_note = (
            f"\n> ⚠ La sonde ILOSTAT a échoué à cette exécution "
            f"(`{data['ilo_error']}`) : la colonne correspondante est vide et "
            f"les paliers sont sous-estimés. Relancer avec le réseau ouvert.\n"
        )
    elif not data["ilo_probed"]:
        ilo_note = (
            "\n> ⚠ Exécution `--no-ilo` : la colonne ILOSTAT est vide par choix, "
            "les paliers sont sous-estimés.\n"
        )

    return f"""# Couverture des statistiques nationales, par pays

**Rapport GÉNÉRÉ** par `backend/scripts/report_national_stats_coverage.py`.
Ne pas éditer à la main — regénérer.

Dernière génération : {today}.
{ilo_note}
## Ce que le palier veut dire

La statistique d'un office national nous parvient de trois façons, de coût
croissant. Le palier dit **où porter l'effort**, jamais la qualité de l'office.

| Palier | Sens | Pays |
|---|---|---:|
| **A** | Collecte directe — un bloc adossé à une publication nommée et datée, dans `data/national_stats/` | {counts[TIER_DIRECT]} |
| **B** | Republiée harmonisée — l'enquête de l'office nous parvient via ILOSTAT ou l'UNSD, sans rien négocier | {counts[TIER_REPUBLISHED]} |
| **C** | Non atteinte — ni republiée, ni collectée | {counts[TIER_NONE]} |

## Pourquoi le palier B ne suffit pas

Les republications harmonisées portent l'emploi et l'activité. Elles ne
portent **pas** la séparation entre exportations domestiques et
réexportations — que seul l'office national publie, et qui commande les
règles d'origine ZLECAf : une marchandise réexportée depuis une zone franche
n'acquiert pas l'origine locale.

Un pays en palier B est donc couvert pour l'emploi, et découvert pour
l'origine. C'est vers cette distinction que la collecte directe doit aller en
priorité, et vers les pays à zones franches actives d'abord.

## Détail

| ISO3 | Pays | Palier | Collecte directe | ILOSTAT (enquêtes emploi) | UNSD 9.2 (emploi manuf.) |
|---|---|:---:|:---:|:---:|:---:|
{body}

## Regénérer

```bash
python3 backend/scripts/report_national_stats_coverage.py
```
"""


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dry-run", action="store_true", help="Affiche sans écrire")
    ap.add_argument("--no-ilo", action="store_true", help="Ne sonde pas ILOSTAT (hors ligne)")
    args = ap.parse_args()

    data = gather(use_ilo=not args.no_ilo)
    rows = data["rows"]
    for tier in (TIER_DIRECT, TIER_REPUBLISHED, TIER_NONE):
        n = sum(1 for r in rows if r["tier"] == tier)
        print(f"   {tier:28} {n:3} pays")
    if data["ilo_error"]:
        print(f"   ⚠ sonde ILOSTAT en échec : {data['ilo_error']}")

    if args.dry_run:
        print("\n(--dry-run) Rapport NON écrit.")
        return
    OUT_FILE.write_text(render(data), encoding="utf-8")
    print(f"\n✅ Écrit : {OUT_FILE.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
