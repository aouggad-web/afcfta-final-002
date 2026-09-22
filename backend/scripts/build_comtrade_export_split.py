#!/usr/bin/env python3
"""
Exportations domestiques / réexportations — dérivées d'UN Comtrade
===================================================================
Écrit ``backend/etl/comtrade_export_split.py`` à partir de l'endpoint PUBLIC
``comtradeapi.un.org/public/v1/preview`` — sans clé d'API.

POURQUOI CE MODULE EXISTE
--------------------------
La couche ``national_official_stats`` a été bâtie sur une affirmation :
« aucune source internationale ne publie la séparation entre exportations
domestiques et réexportations ». Cette affirmation est FAUSSE. UN Comtrade
porte les flux ``DX`` (domestic export) et ``RX`` (re-export) pour les
déclarants qui les soumettent, et les publie sans clé.

La distinction commande les règles d'origine ZLECAf : une marchandise
réexportée n'acquiert pas l'origine locale. La chercher office par office
donnait un pays sur cinq ; la source internationale en donne huit d'un coup.

LA PRÉSENCE D'UNE VENTILATION NE SUFFIT PAS — ELLE DOIT RÉCONCILIER
--------------------------------------------------------------------
C'est la règle d'admission, et elle n'est pas négociable. Un pays n'entre que
si ``DX + RX`` retombe sur ``X`` à la tolérance d'arrondi près. Sans ce
contrôle, on servirait des ventilations incohérentes avec le total qu'elles
sont censées décomposer :

    Angola  2023 : X = 225 472 394, DX + RX = 2 173 934 238  (8,6 × le total)
    Afrique du Sud : écart de 99,6 % de X

Neuf pays sont dans ce cas et sont ÉCARTÉS. C'est la même règle qui a fait
rejeter le Tableau 83 du bulletin togolais : une décomposition qui ne
retombe pas sur son total n'est pas une décomposition.

CE QUE CE SCRIPT REFUSE DE FAIRE
----------------------------------
- **Compléter un flux manquant.** Un pays qui ne publie que ``X`` reste hors
  du module ; on n'en déduit pas ``DX = X`` au motif que les réexportations
  seraient « probablement faibles ».
- **Convertir.** Les valeurs sont en USD telles que publiées par l'ONU.
- **Remplacer la collecte nationale.** Maurice publie la ventilation jusqu'au
  produit et au marché, là où Comtrade ne réconcilie pas pour elle. Les deux
  couches sont complémentaires : celle-ci couvre plus de pays, celle-là va
  plus loin en détail.

Usage :
    python3 backend/scripts/build_comtrade_export_split.py
    python3 backend/scripts/build_comtrade_export_split.py --dry-run
"""

from __future__ import annotations

import argparse
import json
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
OUT_MODULE = BACKEND_DIR / "etl" / "comtrade_export_split.py"

BASE = "https://comtradeapi.un.org/public/v1/preview/C/A/HS"
REPORTERS_REF = "https://comtradeapi.un.org/files/v1/app/reference/Reporters.json"

#: L'endpoint public n'accepte qu'UNE période par appel et limite le débit.
#: On essaie les années de la plus récente à la plus ancienne et on retient la
#: première effectivement reportée — sans jamais mélanger deux années.
YEARS = (2024, 2023, 2022, 2021, 2020, 2019, 2018)

#: Tolérance de réconciliation : un millionième du total, plancher 1 USD.
#: Les écarts observés chez les pays rejetés se comptent en millions ou en
#: ordres de grandeur ; aucun cas limite n'approche ce seuil.
def _tolerance(total: float) -> float:
    return max(abs(total) * 1e-6, 1.0)


AFRICA_ISO3 = (
    "DZA AGO BEN BWA BFA BDI CPV CMR CAF TCD COM COG COD CIV DJI EGY GNQ ERI SWZ ETH "
    "GAB GMB GHA GIN GNB KEN LSO LBR LBY MDG MWI MLI MRT MUS MAR MOZ NAM NER NGA RWA "
    "STP SEN SYC SLE SOM ZAF SSD SDN TZA TGO TUN UGA ZMB ZWE"
).split()


def _get(url: str, attempts: int = 6):
    for attempt in range(attempts):
        try:
            with urllib.request.urlopen(url, timeout=60) as resp:
                payload = json.loads(resp.read())
        except Exception:
            time.sleep(3 + attempt * 2)
            continue
        if payload.get("statusCode") == 429:
            time.sleep(3 + attempt * 2)
            continue
        return payload
    return None


def _world_total(reporter_code: int, flow: str, year: int):
    """Valeur monde / tous produits pour un flux et une année, ou None."""
    payload = _get(
        f"{BASE}?reporterCode={reporter_code}&period={year}"
        f"&flowCode={flow}&cmdCode=TOTAL&partnerCode=0"
    )
    if payload is None or payload.get("error"):
        return None
    rows = [
        r
        for r in (payload.get("data") or [])
        if r.get("cmdCode") == "TOTAL" and r.get("partnerCode") == 0
    ]
    return rows[0].get("primaryValue") if rows else None


def _iso3_to_m49() -> dict:
    payload = _get(REPORTERS_REF)
    if not payload:
        raise SystemExit("référentiel des déclarants Comtrade injoignable")
    return {
        r["reporterCodeIsoAlpha3"]: r["reporterCode"]
        for r in payload["results"]
        if r.get("reporterCodeIsoAlpha3")
    }


def build() -> tuple[list[dict], dict]:
    m49 = _iso3_to_m49()
    admitted, rejected, totals_only, silent = [], [], [], []

    for iso3 in AFRICA_ISO3:
        code = m49.get(iso3)
        if code is None:
            silent.append(iso3)
            continue
        # On retient l'année la plus récente dont la ventilation RÉCONCILIE,
        # et non simplement la plus récente reportée. Une année incohérente
        # n'invalide pas les précédentes : la Tanzanie réconcilie en 2023 et
        # pas en 2024 — s'arrêter à 2024 la ferait disparaître alors qu'une
        # mesure cohérente existe. On sert une donnée plus ancienne plutôt
        # qu'une donnée récente qui ne se recompose pas, et on le dit.
        reported, worst = False, None
        for year in YEARS:
            x = _world_total(code, "X", year)
            time.sleep(1.5)
            if not x:
                continue
            reported = True
            dx = _world_total(code, "DX", year)
            time.sleep(1.5)
            rx = _world_total(code, "RX", year)
            time.sleep(1.5)
            if not dx or not rx:
                continue
            gap = x - (dx + rx)
            if abs(gap) > _tolerance(x):
                if worst is None:  # on garde le rejet le plus RÉCENT, pour le dire
                    worst = {"iso3": iso3, "year": year, "gap": gap, "x": x}
                continue
            admitted.append(
                {
                    "country_iso3": iso3,
                    "year": year,
                    "total_exports_usd": x,
                    "domestic_exports_usd": dx,
                    "reexports_usd": rx,
                    "reexport_share_pct": round(rx / x * 100.0, 1),
                }
            )
            break
        else:
            # Aucune année n'a fourni de ventilation réconciliante.
            if worst is not None:
                rejected.append(worst)
            elif reported:
                totals_only.append(iso3)
            else:
                silent.append(iso3)

    report = {
        "admitted": len(admitted),
        "rejected": rejected,
        "totals_only": totals_only,
        "silent": silent,
    }
    return sorted(admitted, key=lambda r: r["country_iso3"]), report


def render(rows: list[dict], report: dict) -> str:
    generated_at = datetime.now(timezone.utc).isoformat()
    body = "\n".join(
        "    {\n"
        + "".join(f"        {k!r}: {v!r},\n" for k, v in r.items())
        + "    },"
        for r in rows
    )
    rejected = "\n".join(
        f"#   {r['iso3']} {r['year']} — écart de {r['gap']:,.0f} USD "
        f"({abs(r['gap']) / max(abs(r['x']), 1) * 100:,.1f} % du total)"
        for r in report["rejected"]
    )
    return f'''"""
Exportations domestiques / réexportations, dérivées d'UN Comtrade.

GÉNÉRÉ AUTOMATIQUEMENT par ``scripts/build_comtrade_export_split.py`` — NE PAS
ÉDITER À LA MAIN. Régénérer plutôt que corriger.

Source : endpoint PUBLIC ``comtradeapi.un.org/public/v1/preview`` (sans clé),
flux ``X`` (exportations totales), ``DX`` (domestiques), ``RX``
(réexportations), partenaire Monde, tous produits.

Généré le {generated_at}.

RÈGLE D'ADMISSION
------------------
Un pays ne figure ici que si ``DX + RX`` réconcilie avec ``X``. La présence
des trois flux ne suffit pas : neuf pays africains les publient sans qu'ils
se recomposent, et les servir ferait passer une incohérence pour une mesure.

Écartés faute de réconciliation :
{rejected}

Publient un total sans ventilation : {", ".join(report["totals_only"]) or "aucun"}

Ne reportent aucune année {YEARS[-1]}-{YEARS[0]} : {", ".join(report["silent"]) or "aucun"}

CE QUE CES CHIFFRES NE DISENT PAS
-----------------------------------
Ils portent sur le TOTAL des marchandises, partenaire Monde. Ils ne
ventilent ni par produit ni par client — pour cela il faut la statistique de
l'office national (voir ``services/national_official_stats.py``), qui couvre
moins de pays mais descend plus bas.

Une part de réexportation élevée ne dit pas qu'un pays produit peu : elle dit
que ses exportations ENREGISTRÉES incluent des marchandises d'origine
étrangère, qui n'acquièrent pas l'origine locale au sens de la ZLECAf.
"""

from typing import Dict, List

#: Valeurs en USD, telles que publiées par l'ONU. Aucune conversion.
COMTRADE_EXPORT_SPLIT: List[Dict] = [
{body}
]

#: Pays dont la ventilation a été REFUSÉE faute de réconciliation. Exposé pour
#: qu'un appelant puisse dire « la source publie une ventilation, nous la
#: jugeons incohérente » plutôt que « nous n'avons rien ».
COMTRADE_SPLIT_REJECTED: List[str] = {sorted(r["iso3"] for r in report["rejected"])!r}
'''


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    print("Ventilation exportations domestiques / réexportations — UN Comtrade")
    print("=" * 68)
    rows, report = build()
    print(f"   {'admis (réconcilient)':40} {report['admitted']}")
    print(f"   {'écartés (ne réconcilient pas)':40} {len(report['rejected'])}")
    print(f"   {'total seul':40} {len(report['totals_only'])}")
    print(f"   {'aucune année reportée':40} {len(report['silent'])}")
    for r in rows:
        print(
            f"     {r['country_iso3']} {r['year']}  "
            f"réexportations {r['reexport_share_pct']:>5.1f} %"
        )

    if args.dry_run:
        print("\n(--dry-run) Module NON écrit.")
        return
    OUT_MODULE.write_text(render(rows, report), encoding="utf-8")
    print(f"\n✅ Écrit : {OUT_MODULE.relative_to(BACKEND_DIR)}")


if __name__ == "__main__":
    main()
