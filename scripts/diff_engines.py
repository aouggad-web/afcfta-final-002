#!/usr/bin/env python3
"""
Harnais différentiel des deux chemins de calcul du calculateur (phase 0.1).

L'audit du 13 septembre 2026 a montré que l'interface interroge deux circuits
concurrents — GET `/authentic-tariffs/calculate/...` servi par
`services.authentic_tariff_service.calculate_import_taxes`, puis en repli POST
`/calculate-tariff` servi par `routes.calculator` — et que les deux ne donnent
pas les mêmes droits pour la même position. Exemple reproduit : EGY
`0207110000` rend 195 sur le chemin prioritaire et 300 sur le POST, pour un
CIF de 1 000.

Ce script chiffre l'écart au lieu de l'illustrer. Il interroge les deux chemins
dans le même processus, sur les mêmes codes, avec le même CIF, et classe chaque
position. Le rapport JSON produit sert de référence avant correction, de mesure
de progression pendant, et de garde anti-régression en intégration continue
(`--fail-on-divergence`).

Il ne corrige rien et n'écrit aucune donnée tarifaire.

Conditions de comparabilité
---------------------------
Les deux chemins ne sont comparables que sur des sources identiques. Le script
impose donc, et consigne dans le rapport :

* **PostgreSQL neutralisé.** Le chemin prioritaire préfère PostgreSQL quand il
  est joignable, le POST ne le consulte pas. Comparer dans ces conditions
  mesurerait l'écart entre deux bases, pas entre deux moteurs. Si PostgreSQL
  répond, le script s'arrête — sauf `--allow-postgres`, qui l'inscrit alors en
  avertissement dans le rapport.
* **Conversion monétaire neutralisée**, pour que les montants restent dans la
  devise de la source.
* **Appels statistiques externes neutralisés** (OEC, Banque mondiale) : ils
  n'entrent pas dans le calcul des droits et rendraient la course dépendante du
  réseau.
* **Couche normalisée inventoriée.** `backend/data/crawled_normalized/` n'est
  pas versionnée (~2 Go) : un clone neuf en est dépourvu. Sans elle, le POST
  retombe sur des dictionnaires ETL de chapitre. Un pays dont le fichier
  normalisé manque est classé `NORMALISE_ABSENT` et **jamais** compté comme
  divergence : c'est un état d'environnement, pas un défaut du dépôt.

Usage
-----
    python3 scripts/diff_engines.py                       # pays du corpus
    python3 scripts/diff_engines.py --all --per-country 50
    python3 scripts/diff_engines.py --countries EGY,TUN --per-country 200
    python3 scripts/diff_engines.py --cases backend/tests/fixtures/calculator_golden.json
    python3 scripts/diff_engines.py --fail-on-divergence   # usage CI
"""

from __future__ import annotations

import argparse
import json
import os
import random
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

REPO_ROOT = Path(__file__).resolve().parent.parent
BACKEND = REPO_ROOT / "backend"
for _path in (REPO_ROOT, BACKEND):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

DATA_DIR = BACKEND / "data"
CRAWLED_DIR = DATA_DIR / "crawled"
NORMALIZED_DIR = DATA_DIR / "crawled_normalized"

# Pays des dix cas de l'audit (voir backend/tests/fixtures/calculator_golden.json).
CORPUS_COUNTRIES = ["DZA", "EGY", "ETH", "GHA", "MUS", "SOM", "TUN", "ZAF"]

# Graine fixe : deux exécutions sur le même commit tirent les mêmes codes, sinon
# le rapport n'est pas comparable d'une exécution à l'autre.
SAMPLE_SEED = 20260913

RATE_TOLERANCE = 1e-6
AMOUNT_TOLERANCE = 0.01

# Verdicts. `NORMALISE_ABSENT` et `HORS_PERIMETRE_ZLECAF` ne sont pas des
# divergences : le premier décrit l'environnement, le second une règle d'accès
# volontaire du POST.
V_IDENTIQUE = "IDENTIQUE"
V_ECART_TAUX = "ECART_TAUX"
V_ECART_MONTANT = "ECART_MONTANT"
V_ABSENT_PRIORITAIRE = "ABSENT_PRIORITAIRE"
V_ABSENT_POST = "ABSENT_POST"
V_ABSENT_DES_DEUX = "ABSENT_DES_DEUX"
V_EXCEPTION_PRIORITAIRE = "EXCEPTION_PRIORITAIRE"
V_EXCEPTION_POST = "EXCEPTION_POST"
V_ECART_QUALIFICATION = "ECART_QUALIFICATION"
V_NORMALISE_ABSENT = "NORMALISE_ABSENT"
V_HORS_PERIMETRE = "HORS_PERIMETRE_ZLECAF"

DIVERGENCE_VERDICTS = {
    V_ECART_TAUX,
    V_ECART_MONTANT,
    V_ABSENT_PRIORITAIRE,
    V_ABSENT_POST,
    V_EXCEPTION_PRIORITAIRE,
    V_EXCEPTION_POST,
    V_ECART_QUALIFICATION,
}


# --------------------------------------------------------------------------- #
# Neutralisations
# --------------------------------------------------------------------------- #


def _postgres_reachable() -> Tuple[bool, str]:
    """Dire si PostgreSQL répondrait au chemin prioritaire."""
    try:
        from services.postgres_tariff_service import get_postgres_tariff_service
    except Exception as exc:  # dépendance absente = base hors jeu
        return False, f"service indisponible: {exc}"
    try:
        service = get_postgres_tariff_service()
    except Exception as exc:
        return False, f"connexion refusée: {exc}"
    return (service is not None), ("service instancié" if service else "service nul")


def _neutralize_currency() -> None:
    """Garder les montants dans la devise de la source."""
    import currencies.service as currency_service

    currency_service.get_by_country = lambda code: None


def _neutralize_external_stats(calc_module) -> None:
    """Retirer OEC et Banque mondiale : hors calcul des droits, et réseau."""

    async def _no_producers(*_a, **_k):
        return []

    async def _no_country_data(*_a, **_k):
        return {}

    calc_module.oec_client.get_top_producers = _no_producers
    calc_module.wb_client.get_country_data = _no_country_data


# --------------------------------------------------------------------------- #
# Inventaire des sources
# --------------------------------------------------------------------------- #


def normalized_inventory() -> Dict[str, Dict[str, Any]]:
    """Empreinte de présence de la couche normalisée, pays par pays."""
    inventory: Dict[str, Dict[str, Any]] = {}
    if not NORMALIZED_DIR.is_dir():
        return inventory
    for path in sorted(NORMALIZED_DIR.glob("*_tariffs.json")):
        iso3 = path.name.split("_")[0].upper()
        stat = path.stat()
        inventory[iso3] = {"file": path.name, "size_bytes": stat.st_size}
    return inventory


def sample_codes(iso3: str, count: int) -> Tuple[List[str], str]:
    """
    Tirer `count` codes d'un pays, de façon reproductible.

    Priorité au crawl, qui porte les positions nationales ; à défaut au
    canonique. Le tirage est trié puis mélangé avec une graine dérivée de
    l'ISO3 : même commit, même échantillon.
    """
    codes: List[str] = []
    origin = "aucune"

    try:
        from services.authentic_tariff_service import load_crawled_position_index

        index = load_crawled_position_index(iso3) or {}
        if index:
            codes = sorted(index.keys())
            origin = "crawled"
    except Exception:
        codes = []

    if not codes:
        canonical = DATA_DIR / f"{iso3}_tariffs.json"
        if canonical.is_file():
            try:
                with canonical.open(encoding="utf-8") as handle:
                    payload = json.load(handle)
            except Exception:
                payload = {}
            seen = []
            for line in payload.get("tariff_lines", []) or []:
                for sub in line.get("sub_positions", []) or []:
                    code = str(sub.get("code") or "").strip()
                    if code:
                        seen.append(code)
                hs6 = str(line.get("hs6") or "").strip()
                if hs6:
                    seen.append(hs6)
            if seen:
                codes = sorted(set(seen))
                origin = "canonical"

    if not codes:
        return [], origin

    rng = random.Random(f"{SAMPLE_SEED}:{iso3}")
    rng.shuffle(codes)
    return codes[:count], origin


# --------------------------------------------------------------------------- #
# Appel des deux chemins
# --------------------------------------------------------------------------- #


# Qualification du droit servi. Un même montant peut être une mesure nationale
# publiée ou une moyenne NPF indicative : présenter la seconde comme la première
# est un défaut même quand les deux chemins tombent sur le même chiffre (cas MUS
# `010129`, où le prioritaire annonce `authentic_tariff` pendant que le POST
# annonce `duty_status=INDICATIVE_MFN`).
_INDICATIVE_MARKERS = {
    "INDICATIVE_MFN",
    "INFORMATIVE_PARTIAL",
    "estimation_ia",
    "crawled_partial_mfn_average",
}
_FALLBACK_MARKERS = {"etl_fallback", "chapter_fallback"}
_UNAVAILABLE_MARKERS = {"UNAVAILABLE", "CALCULATION_UNAVAILABLE"}


def _qualification(*values: Any) -> str:
    """
    Ramener les libellés de provenance à cinq classes comparables.

    On ne lit que des champs qui qualifient le **droit** (`duty_status`,
    `data_source`). `overall_status` décrit la complétude de la réponse entière,
    formalités comprises : l'inclure classerait toute réponse « indicatif » et
    noierait le signal.
    """
    seen = {str(value) for value in values if value}
    if seen & _FALLBACK_MARKERS:
        return "repli"
    if seen & _INDICATIVE_MARKERS:
        return "indicatif"
    if seen & _UNAVAILABLE_MARKERS:
        return "indisponible"
    if not seen:
        return "inconnu"
    return "authentique"


def _summary_block(payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Extraire la ventilation NPF commune aux deux chemins."""
    summary = payload.get("taxes_summary") or {}
    npf = summary.get("npf") or {}
    if not npf:
        return None
    return {
        "droit_douane": npf.get("droit_douane"),
        "autres_taxes": npf.get("autres_taxes"),
        "tva": npf.get("tva"),
        "total_taxes_et_droits": npf.get("total_taxes_et_droits"),
    }


def call_priority(iso3: str, code: str, cif: float, origin: str) -> Dict[str, Any]:
    """Chemin prioritaire : le service que sert le GET `/authentic-tariffs/...`."""
    from services import authentic_tariff_service as svc

    try:
        result = svc.calculate_import_taxes(iso3, code, cif, language="fr", origin_country=origin)
    except Exception as exc:  # une exception est un constat, pas un arrêt
        return {"status": "exception", "error": f"{type(exc).__name__}: {exc}"}

    if not isinstance(result, dict):
        return {"status": "exception", "error": f"réponse non exploitable: {type(result).__name__}"}
    if result.get("error"):
        return {"status": "absent", "error": str(result.get("error"))}

    return {
        "status": "ok",
        "dd_rate_pct": (result.get("rates") or {}).get("dd_rate_pct"),
        "summary": _summary_block(result),
        "data_source": result.get("data_source"),
        "data_format": result.get("data_format"),
        "duty_status": result.get("duty_status"),
        "qualification": _qualification(result.get("data_source"), result.get("duty_status")),
    }


def call_post(client, iso3: str, code: str, cif: float, origin: str) -> Dict[str, Any]:
    """Chemin de repli : POST `/calculate-tariff`."""
    try:
        response = client.post(
            "/api/calculate-tariff",
            json={
                "origin_country": origin,
                "destination_country": iso3,
                "hs_code": code,
                "value": cif,
            },
        )
    except Exception as exc:
        return {"status": "exception", "error": f"{type(exc).__name__}: {exc}"}

    if response.status_code == 422:
        return {"status": "absent", "error": f"422 {response.text[:200]}"}
    if response.status_code >= 500:
        return {"status": "exception", "error": f"{response.status_code} {response.text[:200]}"}
    if response.status_code != 200:
        return {"status": "absent", "error": f"{response.status_code} {response.text[:200]}"}

    payload = response.json()
    detail = json.dumps(payload)[:200] if not isinstance(payload, dict) else ""
    if not isinstance(payload, dict):
        return {"status": "exception", "error": f"réponse non exploitable: {detail}"}

    summary = _summary_block(payload)
    if summary is None:
        return {"status": "absent", "error": "aucune ventilation NPF dans la réponse"}

    # Les deux chemins n'expriment pas le taux dans la même unité : le service
    # prioritaire publie un pourcentage (`rates.dd_rate_pct` = 19.5), le POST
    # une fraction (`normal_tariff_rate` = 0.195, cf. calculator.py:332
    # `normal_rate = dd_tax["rate_pct"] / 100.0`). On ramène ici le POST au
    # pourcentage, sans quoi chaque position serait comptée en écart de taux.
    # L'incohérence d'unité entre les deux contrats d'API est elle-même un
    # défaut à corriger en phase 3 ; elle est signalée dans le rapport.
    raw_rate = payload.get("normal_tariff_rate")
    dd_rate_pct = None
    if isinstance(raw_rate, (int, float)):
        dd_rate_pct = float(raw_rate) * 100.0

    return {
        "status": "ok",
        "dd_rate_pct": dd_rate_pct,
        "dd_rate_raw_fraction": raw_rate,
        "summary": summary,
        "data_source": payload.get("data_source"),
        "data_format": None,
        "duty_status": payload.get("duty_status"),
        "qualification": _qualification(payload.get("data_source"), payload.get("duty_status")),
    }


# --------------------------------------------------------------------------- #
# Comparaison
# --------------------------------------------------------------------------- #


def _close(left: Any, right: Any, tolerance: float) -> bool:
    """Égalité tolérante qui ne confond pas `None` avec 0."""
    if left is None and right is None:
        return True
    if left is None or right is None:
        return False
    try:
        return abs(float(left) - float(right)) <= tolerance
    except (TypeError, ValueError):
        return left == right


def classify(
    priority: Dict[str, Any], post: Dict[str, Any], normalized_present: bool
) -> Tuple[str, List[str]]:
    """Rendre un verdict et la liste des champs en cause."""
    if priority["status"] == "exception":
        return V_EXCEPTION_PRIORITAIRE, ["exception"]
    if post["status"] == "exception":
        return V_EXCEPTION_POST, ["exception"]

    post_absent = post["status"] == "absent"
    priority_absent = priority["status"] == "absent"

    # Hors périmètre ZLECAf : refus volontaire du POST, pas un défaut de donnée.
    if post_absent and "ZLECAf" in (post.get("error") or ""):
        return V_HORS_PERIMETRE, []

    # Couche normalisée absente : le POST n'a rien à lire, l'écart n'a pas de sens.
    if post_absent and not normalized_present:
        return V_NORMALISE_ABSENT, []

    if priority_absent and post_absent:
        return V_ABSENT_DES_DEUX, []
    if priority_absent:
        return V_ABSENT_PRIORITAIRE, []
    if post_absent:
        return V_ABSENT_POST, []

    if not _close(priority.get("dd_rate_pct"), post.get("dd_rate_pct"), RATE_TOLERANCE):
        return V_ECART_TAUX, ["dd_rate_pct"]

    differing = [
        field
        for field in ("droit_douane", "autres_taxes", "tva", "total_taxes_et_droits")
        if not _close(
            (priority.get("summary") or {}).get(field),
            (post.get("summary") or {}).get(field),
            AMOUNT_TOLERANCE,
        )
    ]
    if differing:
        return V_ECART_MONTANT, differing

    # Montants identiques mais qualification opposée : l'un présente comme
    # authentique ce que l'autre donne pour indicatif ou pour un repli.
    if priority.get("qualification") != post.get("qualification"):
        return V_ECART_QUALIFICATION, ["qualification"]

    return V_IDENTIQUE, []


# --------------------------------------------------------------------------- #
# Exécution
# --------------------------------------------------------------------------- #


def build_post_client():
    """Application FastAPI minimale portant le seul routeur du calculateur."""
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from routes import calculator as calc
    from services.crawled_data_service import crawled_service

    # `crawled_service.load()` n'est déclenché que par l'événement de démarrage
    # de server.py. Sans cet appel, toutes les positions retomberaient sur le
    # repli ETL de chapitre et la comparaison serait vide de sens.
    crawled_service.load()
    _neutralize_external_stats(calc)

    app = FastAPI()
    app.include_router(calc.router, prefix="/api")
    return TestClient(app, raise_server_exceptions=False), crawled_service.is_loaded()


def load_cases(path: Path) -> List[Dict[str, str]]:
    """Lire les cas d'un corpus figé (`calculator_golden.json`)."""
    with path.open(encoding="utf-8") as handle:
        payload = json.load(handle)
    cases = []
    for case in payload.get("cases", []):
        cases.append(
            {
                "country": str(case["country"]).upper(),
                "code": str(case["hs_code"]),
                "case_id": case.get("id", ""),
            }
        )
    return cases


def git_commit() -> str:
    try:
        return subprocess.run(
            ["git", "-C", str(REPO_ROOT), "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
    except Exception:
        return "inconnu"


def run(args: argparse.Namespace) -> Dict[str, Any]:
    reachable, postgres_note = _postgres_reachable()
    if reachable and not args.allow_postgres:
        raise SystemExit(
            "PostgreSQL est joignable : le chemin prioritaire le préférerait et la "
            "comparaison mesurerait deux bases, pas deux moteurs. Neutralisez-le, "
            "ou relancez avec --allow-postgres pour l'assumer explicitement."
        )

    _neutralize_currency()
    client, crawled_loaded = build_post_client()
    inventory = normalized_inventory()

    if args.cases:
        cases = load_cases(Path(args.cases))
        countries = sorted({case["country"] for case in cases})
        sampling = {"mode": "corpus", "file": args.cases}
    else:
        countries = _resolve_countries(args)
        cases = []
        sampling = {"mode": "echantillon", "per_country": args.per_country, "seed": SAMPLE_SEED}
        for iso3 in countries:
            codes, origin = sample_codes(iso3, args.per_country)
            sampling.setdefault("origins", {})[iso3] = origin
            cases.extend({"country": iso3, "code": code, "case_id": ""} for code in codes)

    results: List[Dict[str, Any]] = []
    counters: Dict[str, int] = {}

    for case in cases:
        iso3, code = case["country"], case["code"]
        normalized_present = iso3 in inventory
        priority = call_priority(iso3, code, args.cif, args.origin)
        post = call_post(client, iso3, code, args.cif, args.origin)
        verdict, fields = classify(priority, post, normalized_present)
        counters[verdict] = counters.get(verdict, 0) + 1
        results.append(
            {
                "case_id": case["case_id"],
                "country": iso3,
                "hs_code": code,
                "verdict": verdict,
                "differing_fields": fields,
                "normalized_layer_present": normalized_present,
                "priority": priority,
                "post": post,
            }
        )
        if args.verbose:
            print(f"{iso3:>4} {code:<14} {verdict}", file=sys.stderr)

    divergences = sum(counters.get(verdict, 0) for verdict in DIVERGENCE_VERDICTS)

    return {
        "metadata": {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "commit": git_commit(),
            "cif_value": args.cif,
            "origin_country": args.origin,
            "countries": countries,
            "sampling": sampling,
            "conditions": {
                "postgres_reachable": reachable,
                "postgres_note": postgres_note,
                "postgres_allowed_explicitly": bool(args.allow_postgres),
                "currency_conversion": "neutralisée",
                "external_stats": "neutralisés (OEC, Banque mondiale)",
                "crawled_service_loaded": crawled_loaded,
                "rate_unit_note": (
                    "Le POST publie le droit en fraction (normal_tariff_rate), le service "
                    "prioritaire en pourcentage (rates.dd_rate_pct). Le harnais convertit "
                    "pour comparer ; l'incohérence d'unité reste un défaut à corriger."
                ),
                "normalized_countries": sorted(inventory),
                "normalized_missing_for_run": sorted(set(countries) - set(inventory)),
            },
        },
        "totals": {
            "cases": len(results),
            "divergences": divergences,
            "by_verdict": dict(sorted(counters.items())),
        },
        "cases": results,
    }


def _resolve_countries(args: argparse.Namespace) -> List[str]:
    if args.countries:
        return [iso.strip().upper() for iso in args.countries.split(",") if iso.strip()]
    if args.all:
        crawled = {
            path.name.split("_")[0].upper()
            for path in CRAWLED_DIR.glob("*_tariffs.json")
            if len(path.name.split("_")[0]) == 3
        }
        canonical = {
            path.name.split("_")[0].upper()
            for path in DATA_DIR.glob("*_tariffs.json")
            if len(path.name.split("_")[0]) == 3
        }
        return sorted(crawled | canonical)
    return list(CORPUS_COUNTRIES)


def main(argv: Optional[Iterable[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("--countries", help="Liste ISO3 séparée par des virgules")
    parser.add_argument("--all", action="store_true", help="Tous les pays porteurs de données")
    parser.add_argument("--per-country", type=int, default=25, help="Codes tirés par pays")
    parser.add_argument("--cases", help="Corpus figé de cas au lieu d'un échantillon")
    parser.add_argument("--cif", type=float, default=1000.0, help="Valeur CIF de test")
    parser.add_argument("--origin", default="SEN", help="Pays d'origine (ISO3)")
    parser.add_argument("--out", help="Écrire le rapport JSON dans ce fichier")
    parser.add_argument(
        "--allow-postgres",
        action="store_true",
        help="Assumer une base PostgreSQL joignable (comparaison alors non probante)",
    )
    parser.add_argument(
        "--fail-on-divergence",
        action="store_true",
        help="Sortir en code 1 si une divergence est relevée (usage CI)",
    )
    parser.add_argument("--verbose", action="store_true", help="Tracer chaque cas sur stderr")
    args = parser.parse_args(list(argv) if argv is not None else None)

    report = run(args)

    payload = json.dumps(report, ensure_ascii=False, indent=2)
    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(payload + "\n", encoding="utf-8")
    else:
        print(payload)

    totals = report["totals"]
    missing = report["metadata"]["conditions"]["normalized_missing_for_run"]
    print(
        f"\n{totals['cases']} cas — {totals['divergences']} divergence(s) : "
        + ", ".join(f"{k}={v}" for k, v in totals["by_verdict"].items()),
        file=sys.stderr,
    )
    if missing:
        print(
            "Couche normalisée absente pour : "
            + ", ".join(missing)
            + " — ces pays ne sont pas comparables (python3 scripts/normalize_crawled.py "
            "--country ISO3).",
            file=sys.stderr,
        )

    if args.fail_on_divergence and totals["divergences"]:
        return 1
    return 0


if __name__ == "__main__":
    os.environ.setdefault("PYTHONHASHSEED", "0")
    sys.exit(main())
