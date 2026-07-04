"""
Ingesteur WITS / UNCTAD-TRAINS (Banque mondiale) — couverture SH6 multi-pays.

Source quasi-officielle : taux de douane MFN appliqués (et estimés) au niveau
SH6, publiés par la Banque mondiale (WITS) à partir d'UNCTAD-TRAINS. Permet de
couvrir des dizaines de pays africains dont le portail national n'expose aucune
base tarifaire crawlable (cf. docs/PLAN_SCRAPLING_CRAWLERS.md §10).

NATURE DE LA DONNÉE (assumée, pas cachée) : SH6 (6 chiffres), droit de douane
seul (MFN appliqué), SANS couche nationale (TVA/accises/formalités/régimes).
Le champ `source`/`source_url` trace l'origine ; le gate signalera l'absence de
couche nationale (national_layer_present=false) — c'est voulu pour cette source.

API (confirmée par reconnaissance depuis le runner) :
  - catalogue pays :   /API/V1/wits/datasource/trn/country/ALL  (XML wits:*)
  - données tarif :    /API/V1/SDMX/V21/datasource/TRN/reporter/{code}/partner/000/
                       product/all/year/{year}/datatype/{reported|aveestimated}
                       (SDMX StructureSpecificData XML)

Zéro fabrication : on ne retourne que les observations réellement publiées.
"""

from __future__ import annotations

import sys
import xml.etree.ElementTree as ET
from typing import Dict, List, Optional

import httpx

BASE = "https://wits.worldbank.org/API/V1"
COUNTRY_LIST = f"{BASE}/wits/datasource/trn/country/ALL"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "application/xml,text/xml,*/*",
}
# Années tentées (la plus récente disponible par pays d'abord).
YEARS = [2022, 2021, 2020, 2019, 2018]
SOURCE = "WITS / UNCTAD-TRAINS (Banque mondiale) — MFN appliqué SH6"

# Noms FR des pays (attribution). Complété au besoin ; sinon on retombe sur le
# nom renvoyé par le catalogue WITS.
COUNTRY_NAMES: Dict[str, str] = {
    "AGO": "Angola",
    "COM": "Comores",
    "DJI": "Djibouti",
    "ERI": "Érythrée",
    "ETH": "Éthiopie",
    "GHA": "Ghana",
    "LBY": "Libye",
    "MDG": "Madagascar",
    "MOZ": "Mozambique",
    "MRT": "Mauritanie",
    "MUS": "Maurice",
    "MWI": "Malawi",
    "SDN": "Soudan",
    "SOM": "Somalie",
    "STP": "São Tomé-et-Príncipe",
    "SYC": "Seychelles",
    "ZMB": "Zambie",
    "ZWE": "Zimbabwe",
}


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1] if "}" in tag else tag


def _reporter_code(iso3: str) -> Optional[str]:
    """ISO3 -> code WITS du pays déclarant (isreporter=1)."""
    with httpx.Client(headers=HEADERS, timeout=60.0, follow_redirects=True, verify=False) as c:
        xml = c.get(COUNTRY_LIST).text
    root = ET.fromstring(xml.encode("utf-8"))
    for country in root.iter():
        if _local(country.tag) != "country":
            continue
        if country.attrib.get("isreporter") != "1":
            continue
        iso = None
        for ch in country:
            if _local(ch.tag) == "iso3Code":
                iso = (ch.text or "").strip().upper()
        if iso == iso3.upper():
            return country.attrib.get("countrycode")
    return None


def _pick_rate(obs_attrs: Dict[str, str]) -> Optional[float]:
    """Valeur numérique de l'observation (attribut OBS_VALUE ou équivalent)."""
    for key in ("OBS_VALUE", "OBSVALUE", "Value", "value"):
        if key in obs_attrs:
            try:
                return float(obs_attrs[key])
            except (ValueError, TypeError):
                return None
    return None


def _fetch_year(code: str, year: int, datatype: str) -> Optional[str]:
    url = (
        f"{BASE}/SDMX/V21/datasource/TRN/reporter/{code}/partner/000/"
        f"product/all/year/{year}/datatype/{datatype}"
    )
    with httpx.Client(headers=HEADERS, timeout=120.0, follow_redirects=True, verify=False) as c:
        resp = c.get(url)
    if resp.status_code == 200 and "<" in resp.text[:200]:
        return resp.text
    return None


def _parse(xml_text: str) -> List[Dict]:
    """SDMX StructureSpecificData -> [{hs6, rate, indicator, attrs}]. Les
    dimensions sont portées comme attributs sur Series/Obs ; on fusionne."""
    root = ET.fromstring(xml_text.encode("utf-8"))
    rows: List[Dict] = []
    indicators_seen = set()
    attr_keys_seen = set()

    def walk(el, inherited: Dict[str, str]):
        attrs = {**inherited, **el.attrib}
        tag = _local(el.tag)
        children = list(el)
        if tag == "Obs" or (tag == "Series" and not any(_local(c.tag) == "Obs" for c in children)):
            attr_keys_seen.update(attrs.keys())
            product = (
                attrs.get("PRODUCTCODE") or attrs.get("PRODUCT") or attrs.get("ProductCode") or ""
            )
            # TARIFFTYPE distingue MFN / préférentiel (confirmé par reco : le
            # flux partner/000 est MFN). On le garde comme discriminant.
            indicator = (
                attrs.get("TARIFFTYPE")
                or attrs.get("INDICATOR")
                or attrs.get("INDICATORCODE")
                or attrs.get("DATATYPE")
                or ""
            )
            indicators_seen.add(indicator)
            rate = _pick_rate(attrs)
            if product and rate is not None:
                rows.append(
                    {
                        "hs6": product,
                        "rate": rate,
                        "indicator": indicator,
                        "measure": attrs.get("OBS_VALUE_MEASURE", ""),
                        "nbr_mfn": attrs.get("NBR_MFN_LINES", ""),
                    }
                )
        for c in children:
            walk(c, attrs)

    walk(root, {})
    # Diagnostic (stderr) : aide à confirmer le bon indicateur/attributs.
    print(
        f"[wits] indicateurs={sorted(i for i in indicators_seen if i)[:12]} "
        f"attrs={sorted(attr_keys_seen)[:16]}",
        file=sys.stderr,
    )
    return rows


# Indicateurs TRAINS préférés : moyenne simple du MFN appliqué / effectivement
# appliqué. On retient le premier motif trouvé parmi les observations.
_PREFERRED = ("MFN", "AHS")


def crawl(iso3: str, max_positions: Optional[int] = None, year: Optional[int] = None) -> List[Dict]:
    code = _reporter_code(iso3)
    if not code:
        print(f"[wits] {iso3} n'est pas un pays déclarant TRAINS.", file=sys.stderr)
        return []

    years = [year] if year else YEARS
    rows: List[Dict] = []
    used_year = None
    for y in years:
        for datatype in ("reported", "aveestimated"):
            xml_text = _fetch_year(code, y, datatype)
            if not xml_text:
                continue
            parsed = _parse(xml_text)
            if parsed:
                rows = parsed
                used_year = y
                break
        if rows:
            break
    if not rows:
        return []

    # Dédup par SH6 : préférer un indicateur MFN/AHS ; sinon garder le 1er.
    by_hs: Dict[str, Dict] = {}
    for r in rows:
        hs = r["hs6"].zfill(6)[:6]
        cur = by_hs.get(hs)
        pref = any(p in (r["indicator"] or "").upper() for p in _PREFERRED)
        if cur is None:
            by_hs[hs] = {**r, "_pref": pref}
        elif pref and not cur.get("_pref"):
            by_hs[hs] = {**r, "_pref": pref}

    positions: List[Dict] = []
    for hs, r in sorted(by_hs.items()):
        if max_positions and len(positions) >= max_positions:
            break
        positions.append(
            {
                "hs_code": hs,
                "chapter": hs[:2],
                "name": "",  # WITS ne fournit pas la désignation dans ce flux
                "description": "",
                "taxes": {
                    "DD": {
                        "name": "Droit de douane (MFN appliqué, WITS/TRAINS)",
                        "rate": r["rate"],
                        "raw": (
                            f"{r['rate']} % ({r.get('indicator') or 'MFN'}"
                            f"{', ' + r['measure'] if r.get('measure') else ''}, {used_year})"
                        ),
                    }
                },
                "advantages": [],
                "formalities": [],
                "source": SOURCE,
                "source_url": (
                    f"{BASE}/SDMX/V21/datasource/TRN/reporter/{code}/partner/000/"
                    f"product/{hs}/year/{used_year}/datatype/reported"
                ),
            }
        )
    print(
        f"[wits] {iso3} ({code}) année {used_year} : {len(positions)} positions SH6",
        file=sys.stderr,
    )
    return positions
