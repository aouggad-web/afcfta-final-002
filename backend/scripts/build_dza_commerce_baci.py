#!/usr/bin/env python3
"""
Exportations algériennes et demande mondiale par produit SH6 (CEPII BACI via l'API OEC)
=======================================================================================
Construit data/json/dza_commerce_baci.json.

BACI (CEPII) réconcilie les déclarations des exportateurs et des importateurs : il
couvre 2018-2023, années où l'Algérie ne déclare pas à UN Comtrade.

  Offre   : exportations de l'Algérie par SH6 et par pays de destination (monde entier),
            2016-2024 (cube SH 2012 pour 2016-2017, SH 2017 pour 2018-2024).
  Demande : pour chaque produit exporté par l'Algérie (≥ 0,5 M USD une année au moins
            entre 2021 et 2024), importations de tous les pays en 2019 et 2021-2024.

Chaque requête est mise en cache (--cache), ce qui rend la reconstruction rejouable.
Contrôle : pour chaque produit et chaque année, la somme par continent et la somme par
pays égalent le total (à 0,5 % près).

Usage:
    python3 scripts/build_dza_commerce_baci.py [--cache DOSSIER] [--dry-run]
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
import tempfile
import time
import urllib.parse
import urllib.request
from collections import defaultdict
from datetime import date

RACINE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SORTIE = os.path.join(RACINE, "data", "json", "dza_commerce_baci.json")
BASE = "https://api.oec.world/tesseract/data.jsonrecords"
# L'OEC (Cloudflare) refuse l'agent par défaut de urllib : on s'identifie explicitement.
UA = "afcfta-saas-collecte/1.0 (curl-compatible; donnees publiques BACI)"
CUBE = {a: "trade_i_baci_a_17" for a in range(2018, 2025)}
CUBE.update({2016: "trade_i_baci_a_12", 2017: "trade_i_baci_a_12"})
SEUIL_USD = 0.5e6
ANNEES_DEMANDE = [2019, 2021, 2022, 2023, 2024]


def lire(params, cache, essais=6):
    url = BASE + "?" + urllib.parse.urlencode(params, safe=",+")
    chemin = os.path.join(cache, hashlib.md5(url.encode()).hexdigest() + ".json")
    if os.path.exists(chemin):
        with open(chemin) as f:
            return json.load(f)
    dernier = None
    for i in range(essais):
        try:
            req = urllib.request.Request(
                url, headers={"User-Agent": UA, "Accept": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=180) as r:
                d = json.load(r)
            if "data" in d:
                with open(chemin, "w") as f:
                    json.dump(d, f)
                time.sleep(1.5)
                return d
            dernier = d
        except Exception as e:  # noqa: BLE001 — réseau : on retente puis on signale
            dernier = e
        time.sleep(5 + 8 * i)
    raise RuntimeError(f"OEC injoignable pour {url} : {dernier}")


def hs6(oid):
    return str(oid)[-6:]


def iso3(oid):
    return str(oid or "")[2:].upper()


def main():
    cache = (
        sys.argv[sys.argv.index("--cache") + 1]
        if "--cache" in sys.argv
        else os.path.join(tempfile.gettempdir(), "oec_baci")
    )
    os.makedirs(cache, exist_ok=True)

    exp, lib = defaultdict(dict), {}
    afr = defaultdict(dict)
    dest = defaultdict(lambda: defaultdict(dict))
    cont_tot = defaultdict(lambda: defaultdict(float))
    for an, cube in sorted(CUBE.items()):
        base = {
            "cube": cube,
            "measures": "Trade Value,Quantity",
            "Exporter Country": "afdza",
            "Year": str(an),
        }
        for r in lire({**base, "drilldowns": "Year,HS6"}, cache)["data"]:
            h = hs6(r["HS6 ID"])
            exp[h][str(an)] = [
                round(r["Trade Value"]),
                round(r["Quantity"], 1) if r.get("Quantity") else None,
            ]
            lib[h] = (r["HS6"], r["HS6 ID"])
        for r in lire({**base, "drilldowns": "Year,HS6,Importer Continent"}, cache)["data"]:
            cont_tot[hs6(r["HS6 ID"])][str(an)] += r["Trade Value"]
            if r.get("Importer Continent ID") == "af":
                afr[hs6(r["HS6 ID"])][str(an)] = round(r["Trade Value"])
        for r in lire({**base, "drilldowns": "Year,HS6,Importer Country"}, cache)["data"]:
            dest[hs6(r["HS6 ID"])][str(an)][iso3(r.get("Importer Country ID"))] = (
                r["Importer Country"],
                round(r["Trade Value"]),
                round(r["Quantity"], 1) if r.get("Quantity") else None,
            )

    ecarts = 0
    for h, s in exp.items():
        for an, (v, _q) in s.items():
            for tot in (cont_tot[h].get(an, 0), sum(x[1] for x in dest[h].get(an, {}).values())):
                if tot and abs(tot / v - 1) > 0.005:
                    ecarts += 1
    if ecarts:
        sys.exit(f"{ecarts} écart(s) entre totaux et sommes par destination : données incohérentes")

    retenus = sorted(
        h
        for h, s in exp.items()
        if any(s.get(str(a), [0])[0] >= SEUIL_USD for a in range(2021, 2025))
    )
    ids = {h: lib[h][1] for h in retenus}
    demande = defaultdict(dict)  # h -> an -> {iso3: (pays, valeur)}
    lots = [retenus[i : i + 15] for i in range(0, len(retenus), 15)]
    for an in ANNEES_DEMANDE:
        for lot in lots:
            d = lire(
                {
                    "cube": CUBE[an],
                    "measures": "Trade Value",
                    "drilldowns": "Year,HS6,Importer Country",
                    "HS6": ",".join(str(ids[h]) for h in lot),
                    "Year": str(an),
                },
                cache,
            )
            for r in d["data"]:
                demande[hs6(r["HS6 ID"])].setdefault(str(an), {})[
                    iso3(r.get("Importer Country ID"))
                ] = (
                    r["Importer Country"],
                    r["Trade Value"],
                    str(r.get("Importer Country ID") or "").startswith("af"),
                )

    produits = {}
    for h in retenus:
        dem = demande.get(h, {})
        i24, i19 = dem.get("2024", {}), dem.get("2019", {})
        d24 = dest[h].get("2024", {})

        def ligne(k):
            pays, v, _a = i24[k]
            part = round(d24.get(k, (None, 0))[1] / v * 100, 1) if v else 0.0
            return [k, pays, round(v), round(i19.get(k, (None, 0, None))[1]), part]

        ordre = [k for k in sorted(i24, key=lambda k: -i24[k][1]) if k != "DZA"]
        produits[h] = {
            "libelle_en": lib[h][0],
            "exportations": dict(sorted(exp[h].items())),
            "exportations_afrique": dict(sorted(afr[h].items())),
            "destinations_2024": [
                [k, n, v, q] for k, (n, v, q) in sorted(d24.items(), key=lambda x: -x[1][1])[:15]
            ],
            "demande_monde": {
                an: round(sum(v for k, (_n, v, _a) in m.items() if k != "DZA"))
                for an, m in sorted(dem.items())
            },
            "demande_afrique": {
                an: round(sum(v for k, (_n, v, a) in m.items() if a and k != "DZA"))
                for an, m in sorted(dem.items())
            },
            "importateurs_2024": [ligne(k) for k in ordre[:20]],
            "importateurs_afrique_2024": [ligne(k) for k in ordre if i24[k][2]],
        }

    donnees = {
        "meta": {
            "titre": "Exportations de l'Algérie et demande mondiale par produit (SH6), 2016-2024",
            "source": "CEPII BACI via l'API OEC (api.oec.world/tesseract)",
            "genere_le": date.today().isoformat(),
            "script": "backend/scripts/build_dza_commerce_baci.py",
            "nature": "officiel",
            "cubes": {
                "2016-2017": "trade_i_baci_a_12 (SH 2012)",
                "2018-2024": "trade_i_baci_a_17 (SH 2017)",
            },
            "unites": {
                "valeurs": "USD courants (FOB réconciliés par BACI)",
                "quantites": "tonnes métriques",
            },
            "champ": "produits exportés par l'Algérie pour au moins 0,5 M USD une année entre 2021 et 2024",
            "demande": "importations des autres pays (l'Algérie elle-même exclue), monde et Afrique",
            "colonnes": {
                "exportations": "année -> [valeur USD, tonnes]",
                "destinations_2024": "[ISO3, pays, valeur USD, tonnes], 15 premières",
                "importateurs_2024": "[ISO3, pays, importations 2024 USD, importations 2019 USD, part de l'Algérie en %], 20 premiers",
                "importateurs_afrique_2024": "mêmes colonnes, tous les importateurs africains",
            },
            "limites": [
                "L'Algérie n'a pas déclaré à UN Comtrade de 2018 à 2023 : BACI reconstitue ces années à partir des déclarations des pays partenaires.",
                "Un flux que ni l'Algérie ni le partenaire ne déclare n'apparaît pas : c'est le cas de la Libye après 2019 ; les échanges avec la Libye sont donc sous-estimés.",
                "Les codes SH 2012 (2016-2017) et SH 2017 (2018-2024) diffèrent pour quelques produits.",
            ],
        },
        "produits": produits,
    }
    print(len(produits), "produits ; contrôles des sommes : 0 écart")
    if "--dry-run" not in sys.argv:
        with open(SORTIE, "w", encoding="utf-8") as f:
            json.dump(donnees, f, ensure_ascii=False, separators=(",", ":"))
        print(
            "écrit :",
            os.path.relpath(SORTIE, RACINE),
            round(os.path.getsize(SORTIE) / 1e6, 2),
            "Mo",
        )


if __name__ == "__main__":
    main()
