#!/usr/bin/env python3
"""
Récupération UNIDO IDSB + INDSTAT — niveau ISIC Rev.4 4 chiffres (classe)
=========================================================================
Interroge l'API officielle du portail statistique UNIDO (voir
https://stat.unido.org/unido-statistics-portal-api) pour un pays donné et
écrit un CSV compressé dans le schéma déjà utilisé par
``etl/isic4_idsb_data.py`` (``schema_version: unido_manufacturing_v1``), afin
que ces lignes soient servies par les mêmes routes ``/isic4/*`` que l'export
fourni manuellement ``unido_idsb_indstat_isic4_2018plus.csv.gz``.

POURQUOI CE SCRIPT
------------------
Le fichier manuel couvre 20 pays africains sur la fenêtre 2018-2024.
L'Algérie en est absente : son détail INDSTAT/IDSB au niveau classe s'arrête
en 2015 — l'ONS n'a pas transmis de ventilation ISIC 4 chiffres au-delà.
Plutôt que de laisser le pays en « payload estimé » (répartition à parts
égales des top_sectors), ce script verse les ANNÉES RÉELLEMENT PUBLIÉES
(2011-2015, édition INDSTAT/IDSB 2026, fournisseur Office national des
statistiques d'Alger) dans le même schéma.

CE QUE L'API DONNE PAR PAYS
---------------------------
  • INDSTAT (dataset ``INDSTAT/4``) — OFFICIAL_STATISTICS :
      01 Establishments (N), 04 Employees (N), 31 Female employees (N),
      05 Wages and salaries (M), 14 Output (M), 20 Value added (M),
      21 Gross fixed capital formation (M).
  • IDSB (dataset ``IDSB/4``) — UNIDO_DERIVED_ESTIMATE :
      100 Output, 101 Imports World, 104 Exports World, 107 Apparent
      Consumption.

Chaque montant INDSTAT arrive en deux monnaies : ``v`` (devise nationale) et
``u`` (USD courant). Les deux sont conservées, comme le prévoit le schéma
(``value_local_currency`` / ``value_usd_current``).

FILTRES — identiques au fichier manuel
--------------------------------------
  • ``isic_level = 4`` : seules les classes ISIC à 4 chiffres sont retenues,
    les sections/divisions/groupes sont écartés ;
  • un (classe, indicateur, année) sans valeur publiée est simplement omis :
    une valeur ``null`` ne donne pas de ligne (zéro fabrication).

USAGE
-----

    python3 scripts/fetch_unido_indstat.py                 # DZA par défaut
    python3 scripts/fetch_unido_indstat.py --iso3 MAR

NUANCES RÉSEAU
--------------
Le portail est derrière Cloudflare : des 403 sporadiques se contournent par
relance espacée avec en-têtes navigateur (la page d'API du portail documente
elle-même ce comportement). La vérification TLS, elle, n'est JAMAIS levée :
un échec de certificat — le signal qu'on ne parle peut-être pas à qui on
croit — fait échouer le script franchement ; si l'environnement manque de
magasin d'AC, pointer un bundle explicite avec ``--cafile``. Une donnée
collectée par un canal non authentifié ne se distinguerait plus d'une donnée
saine, et ce collecteur est destiné à être rejoué sur 53 pays.
"""

from __future__ import annotations

import csv
import gzip
import json
import ssl
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

SCRIPT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = SCRIPT_DIR.parent
OUT_DIR = BACKEND_DIR / "data" / "unido"

API_BASE = "https://stat.unido.org/portal"
SOURCE_URL = "https://stat.unido.org/unido-statistics-portal-api"
SCHEMA_VERSION = "unido_manufacturing_v1"

#: code pays UN M49 / ISO2 / nom EN — le portail indexe par code M49.
COUNTRIES = {
    "DZA": ("012", "DZ", "Algeria"),
}

#: dataset_code -> chemin API. L'id numérique est découvert dynamiquement :
#: la documentation du portail demande de ne PAS le coder en dur.
DATASETS = {
    "IDSB_R4": "IDSB/4",
    "INDSTAT_R4": "INDSTAT/4",
}

#: variables versées, avec le libellé publié et la nature (N = comptage,
#: M = montant). Les codes absents d'une base sont ignorés.
INDSTAT_VARIABLES = {
    "01": ("Establishments", "N"),
    "04": ("Employees", "N"),
    "31": ("Female employees", "N"),
    "05": ("Wages and salaries", "M"),
    "14": ("Output", "M"),
    "20": ("Value added", "M"),
    "21": ("Gross fixed capital formation", "M"),
}
IDSB_VARIABLES = {
    "100": ("Output", "M"),
    "101": ("Imports World", "M"),
    "104": ("Exports World", "M"),
    "107": ("Apparent Consumption", "M"),
}

_HEADERS = {
    "Accept": "application/json",
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}
_RETRIES = 5
_RETRY_BASE_DELAY_S = 3.0

CSV_COLUMNS = [
    "schema_version",
    "record_id",
    "dataset_code",
    "dataset_id",
    "dataset_name",
    "dataset_production_year",
    "country_iso3",
    "country_iso2",
    "country_un_m49",
    "country_name_en",
    "isic_revision",
    "isic_level",
    "isic_code",
    "isic_description_en",
    "year",
    "indicator_code",
    "indicator_name_en",
    "indicator_type",
    "value",
    "unit",
    "currency",
    "value_local_currency",
    "value_usd_current",
    "data_status",
    "data_nature",
    "source_url",
    "extracted_at_utc",
    "source_note",
    "data_supplier",
    "table_note",
    "observation_metadata_json",
]


def _ssl_context(cafile: Optional[str] = None) -> ssl.SSLContext:
    """TLS vérifié, TOUJOURS — un échec de certificat est une fin, pas un repli.

    Une première version de ce script retombait sur un contexte non vérifié
    quand la vérification échouait (« bundle CA local insuffisant »). C'était
    faux, et c'est précisément le cas où il ne faut pas continuer : un échec
    de certificat est le signal qu'on ne parle peut-être pas à qui on croit,
    et un versement industriel collecté par un canal non authentifié ne se
    distinguerait plus ensuite d'une donnée saine. Un pays non collecté est
    récupérable ; un canal non authentifié, non. Si l'environnement manque de
    magasin d'AC, pointer un bundle explicite : ``--cafile`` (certifi ou
    système). Sinon, le script échoue franchement.
    """
    return ssl.create_default_context(cafile=cafile)


def _request_json(
    url: str, ctx: ssl.SSLContext, body: Optional[dict] = None, retries: int = 5
) -> object:
    """Requête GET (ou POST si ``body``) avec relance devant 403/5xx sporadiques.

    Les 400/404 sont des erreurs métier : pas de relance, on échoue franchement.
    """
    delay = 3.0
    last: Exception = RuntimeError("unreachable")
    for attempt in range(1, retries + 1):
        try:
            data = json.dumps(body).encode() if body is not None else None
            req = urllib.request.Request(
                url,
                data=data,
                method="POST" if body is not None else "GET",
                headers={**_HEADERS, **({"Content-Type": "application/json"} if data else {})},
            )
            with urllib.request.urlopen(req, timeout=180, context=ctx) as resp:  # nosec B310
                return json.loads(resp.read())
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            # Un échec de certificat n'est pas une panne transitoire : c'est le
            # signal qu'on ne parle peut-être pas à qui on croit. Abandon franc,
            # avec le remède (pointer un bundle d'AC explicite).
            if isinstance(exc, urllib.error.URLError):
                reason = str(getattr(exc, "reason", exc))
                if "CERTIFICATE_VERIFY_FAILED" in reason:
                    raise SystemExit(
                        "TLS : vérification du certificat échouée — abandon, sans repli "
                        "non vérifié (une donnée collectée par un canal non authentifié "
                        "ne se distinguerait plus d'une donnée saine). Si l'environnement "
                        "manque de magasin d'AC, relancer avec "
                        "--cafile /chemin/vers/cacert.pem."
                    )
            last = exc
            code = getattr(exc, "code", None)
            if code in (400, 404):
                raise
            print(f"  relance {attempt}/{retries} ({code or type(exc).__name__}) …")
            time.sleep(delay)
            delay *= 2
    raise last


def _fmt(value) -> str:
    """Nombre en texte sans notation scientifique, sans zéro parasite."""
    if value is None:
        return ""
    num = float(value)
    if num == int(num):
        return str(int(num))
    return f"{num:.3f}".rstrip("0").rstrip(".")


def build_rows(
    dataset_code: str,
    meta: Dict,
    payloads: Dict[str, Dict],
    variables: Dict[str, Tuple[str, str]],
    iso3: str,
    iso2: str,
    m49: str,
    name_en: str,
    data_nature: str,
    provenance: Dict[str, str],
    extracted_at: str,
) -> List[Dict]:
    """Lignes CSV d'un dataset : une par (classe ISIC 4 chiffres, année, indicateur).

    Ne retient que les codes à 4 chiffres (isic_level 4, comme le fichier
    manuel) ; un couple (classe, année) sans valeur publiée est omis.
    """
    activities = {a["c"]: a["lang"]["en"] for a in meta.get("activities", [])}
    variables_meta = {v["c"]: v for v in meta.get("variables", [])}
    rows: List[Dict] = []
    for indicator_code, payload in payloads.items():
        label, nature = variables[indicator_code]
        var_meta = variables_meta.get(indicator_code)
        indicator_name = var_meta["lang"]["en"] if var_meta else label
        is_count = (var_meta.get("type") if var_meta else nature) == "N"
        unit = "count" if is_count else "current_USD"
        currency = "" if is_count else "USD"
        for rec in payload.get("data", []):
            isic = str(rec.get("a") or "")
            if not (isic.isdigit() and len(isic) == 4):
                continue
            year = str(rec.get("p") or "")
            # INDSTAT publie en devise nationale (``v``) ET en USD (``u``) ;
            # l'IDSB, non convertible (in_local_currency false), ne renvoie
            # qu'un montant, déjà en USD sous ``v``.
            has_local = bool(meta.get("in_local_currency"))
            value_local = rec.get("v")
            value_usd = rec.get("u")
            if not has_local:
                value_usd = value_usd if value_usd is not None else value_local
                value_local = None
            value = value_local if is_count else value_usd
            if value in (None, ""):
                continue
            rows.append(
                {
                    "schema_version": SCHEMA_VERSION,
                    "record_id": f"{dataset_code}:{iso3}:{isic}:{year}:{indicator_code}",
                    "dataset_code": dataset_code,
                    "dataset_id": str(meta["id"]),
                    "dataset_name": meta.get("name") or "",
                    "dataset_production_year": str(meta.get("production_year") or ""),
                    "country_iso3": iso3,
                    "country_iso2": iso2,
                    "country_un_m49": m49,
                    "country_name_en": name_en,
                    "isic_revision": "4",
                    "isic_level": "4",
                    "isic_code": isic,
                    "isic_description_en": activities.get(isic, ""),
                    "year": year,
                    "indicator_code": indicator_code,
                    "indicator_name_en": indicator_name,
                    "indicator_type": var_meta.get("type", nature) if var_meta else nature,
                    "value": _fmt(value),
                    "unit": unit,
                    "currency": currency,
                    # L'IDSB ne publie qu'en USD (in_local_currency false) : la
                    # colonne locale reste vide, comme dans le fichier manuel.
                    "value_local_currency": (
                        _fmt(value_local) if (not is_count and value_local is not None) else ""
                    ),
                    "value_usd_current": _fmt(value_usd) if not is_count else "",
                    "data_status": "DOCUMENTED",
                    "data_nature": data_nature,
                    "source_url": SOURCE_URL,
                    "extracted_at_utc": extracted_at,
                    "source_note": provenance.get(year, ""),
                    "data_supplier": "",
                    "table_note": "",
                    "observation_metadata_json": "",
                }
            )
    return rows


def _dataset_meta(path: str, ctx: ssl.SSLContext) -> Dict:
    return _request_json(f"{API_BASE}/dataset/getDataset/{path}", ctx)  # type: ignore[return-value]


def _year_provenance(payload: Dict) -> Dict[str, str]:
    keep = ("Data Supplier", "Related national publications")
    skip = ("Not reported.", "None reported.")
    out: Dict[str, str] = {}
    for y in payload.get("ym", []):
        notes = [
            m["note"]
            for m in y.get("metadataList", [])
            if m.get("noteClass") in keep and m.get("note") not in skip
        ]
        if notes:
            out[str(y.get("year"))] = "; ".join(notes)
    return out


def _country_data(dataset_id: int, m49: str, indicator_code: str, ctx: ssl.SSLContext) -> Dict:
    body = {"datasetId": dataset_id, "countryCode": m49, "variableCode": indicator_code}
    return _request_json(f"{API_BASE}/dataset/getData", ctx, body)  # type: ignore[return-value]


def fetch_country(iso3: str, ctx: ssl.SSLContext) -> List[Dict]:
    """Télécharge IDSB + INDSTAT pour un pays, retourne les lignes du schéma."""
    m49, iso2, name_en = COUNTRIES[iso3]
    extracted_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    all_rows: List[Dict] = []
    for dataset_code, dataset_path in DATASETS.items():
        print(f"• {dataset_code} ({dataset_path}) — métadonnées …")
        meta = _dataset_meta(dataset_path, ctx)
        variables = INDSTAT_VARIABLES if dataset_code == "INDSTAT_R4" else IDSB_VARIABLES
        data_nature = (
            "OFFICIAL_STATISTICS" if dataset_code == "INDSTAT_R4" else "UNIDO_DERIVED_ESTIMATE"
        )
        payloads: Dict[str, Dict] = {}
        provenance: Dict[str, str] = {}
        for indicator_code in sorted(variables):
            label = variables[indicator_code][0]
            print(f"    indicateur {indicator_code} ({label}) …")
            payload = _country_data(meta["id"], m49, indicator_code, ctx)
            payloads[indicator_code] = payload
            if not provenance:
                provenance = _year_provenance(payload)
        rows = build_rows(
            dataset_code, meta, payloads, variables,
            iso3, iso2, m49, name_en, data_nature, provenance, extracted_at,
        )
        print(f"    → {len(rows)} lignes")
        all_rows.extend(rows)
    return all_rows


def write_csv(rows: List[Dict], out_file: Path) -> None:
    """Écriture déterministe : tri (dataset, isic, année, indicateur) — diff stable."""
    rows.sort(
        key=lambda r: (
            r["dataset_code"], r["isic_code"], r["year"], r["indicator_code"]
        )
    )
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(out_file, "wt", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def _parse_args() -> tuple:
    """--iso3 (défaut DZA) et --cafile (bundle d'AC explicite, optionnel)."""
    iso3, cafile = "DZA", None
    args = sys.argv[1:]
    i = 0
    while i < len(args):
        if args[i] == "--iso3" and i + 1 < len(args):
            iso3 = args[i + 1].upper()
            i += 2
        elif args[i] == "--cafile" and i + 1 < len(args):
            cafile = args[i + 1]
            i += 2
        else:
            i += 1
    return iso3, cafile


def main() -> None:
    iso3, cafile = _parse_args()
    if iso3 not in COUNTRIES:
        sys.exit(f"Pays non configuré : {iso3}. Configuré : {', '.join(COUNTRIES)}")
    if cafile is not None and not Path(cafile).is_file():
        sys.exit(f"--cafile : fichier introuvable : {cafile}")

    ctx = _ssl_context(cafile)
    print(f"Récupération UNIDO IDSB + INDSTAT (ISIC Rev.4, classes) — {iso3} …")
    rows = fetch_country(iso3, ctx)
    if not rows:
        sys.exit(f"Aucune donnée publiée pour {iso3} — rien à écrire (zéro fabrication).")

    years = sorted({r["year"] for r in rows})
    out_file = OUT_DIR / (
        f"unido_idsb_indstat_isic4_{iso3.lower()}_{years[0]}_{years[-1]}.csv.gz"
    )
    write_csv(rows, out_file)

    n_classes = len({r["isic_code"] for r in rows})
    print(f"\n✅ Écrit : {out_file.relative_to(BACKEND_DIR.parent)}")
    print(f"   {len(rows)} lignes — {n_classes} classes ISIC 4 chiffres — "
          f"années {years[0]}→{years[-1]}")
    natures = {r["data_nature"] for r in rows}
    print(f"   nature : {natures}")
    suppliers = sorted({r["source_note"] for r in rows if r["source_note"]})
    for s in suppliers:
        print(f"   provenance : {s}")


if __name__ == "__main__":
    main()