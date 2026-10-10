"""
Construit la géographie de la carte « Réseau ZLECAf » :
``frontend/src/data/zlecafNetworkGeo.json``.

Deux sources, toutes deux Natural Earth (domaine public), figées par leur
SHA-256 — un octet modifié dans une source fait échouer la construction :

* contour des terres : ``world-atlas@2.0.2/countries-50m.json`` (Natural Earth
  1:50m, TopoJSON) ;
* capitales : ``ne_10m_populated_places_simple.geojson`` (Natural Earth v5.1.2),
  entités ``Admin-0 capital`` / ``Admin-0 capital alt``.

Seul le CONTOUR des terres est tracé : aucune frontière intérieure n'est
dessinée, la carte ne prend donc parti sur aucun tracé disputé. Le Sahara
occidental (732) et le Somaliland (sans code) entrent dans le contour pour que
la côte soit continue, sans recevoir de point ni de statut.

Usage :
    python scripts/build_zlecaf_network_geo.py [--world FICHIER] [--places FICHIER]

Sans argument, les deux sources sont téléchargées depuis jsDelivr.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))

from constants import AFRICAN_COUNTRIES  # noqa: E402

OUTPUT = ROOT / "frontend" / "src" / "data" / "zlecafNetworkGeo.json"

WORLD = {
    "url": "https://cdn.jsdelivr.net/npm/world-atlas@2.0.2/countries-50m.json",
    "sha256": "04342cdc1e3016bcd7db1630de95684d67b79fe3c8c460321e87aef469502394",
    "label": "Natural Earth 1:50m (world-atlas 2.0.2), domaine public",
}
PLACES = {
    "url": (
        "https://cdn.jsdelivr.net/gh/nvkelso/natural-earth-vector@v5.1.2/"
        "geojson/ne_10m_populated_places_simple.geojson"
    ),
    "sha256": "fd3fa867a320cbd5c5b6bb5bc550afeec2939fb2cef688e508007282a55ac42f",
    "label": "Natural Earth v5.1.2, populated places (Admin-0 capital), domaine public",
}

# Codes ISO 3166-1 numériques des 54 États de la ZLECAf présents dans
# AFRICAN_COUNTRIES, plus le Sahara occidental (732) — contour seulement.
NUMERIC_TO_ISO3 = {
    "012": "DZA",
    "024": "AGO",
    "204": "BEN",
    "072": "BWA",
    "854": "BFA",
    "108": "BDI",
    "132": "CPV",
    "120": "CMR",
    "140": "CAF",
    "148": "TCD",
    "174": "COM",
    "178": "COG",
    "180": "COD",
    "262": "DJI",
    "818": "EGY",
    "226": "GNQ",
    "232": "ERI",
    "748": "SWZ",
    "231": "ETH",
    "266": "GAB",
    "270": "GMB",
    "288": "GHA",
    "324": "GIN",
    "624": "GNB",
    "384": "CIV",
    "404": "KEN",
    "426": "LSO",
    "430": "LBR",
    "434": "LBY",
    "450": "MDG",
    "454": "MWI",
    "466": "MLI",
    "478": "MRT",
    "480": "MUS",
    "504": "MAR",
    "508": "MOZ",
    "516": "NAM",
    "562": "NER",
    "566": "NGA",
    "646": "RWA",
    "678": "STP",
    "686": "SEN",
    "690": "SYC",
    "694": "SLE",
    "706": "SOM",
    "710": "ZAF",
    "728": "SSD",
    "729": "SDN",
    "834": "TZA",
    "768": "TGO",
    "788": "TUN",
    "800": "UGA",
    "894": "ZMB",
    "716": "ZWE",
}
LAND_ONLY = {"732"}  # Sahara occidental : contour, pas de point.
LAND_ONLY_NAMES = {"Somaliland"}  # entité sans code numérique dans world-atlas

# Membres de AFRICAN_COUNTRIES sans « Admin-0 capital » sous leur code ISO3
# dans Natural Earth : ils restent dans les données (statut, tableau), sans
# point sur la carte. Toute autre absence fait échouer la construction.
# ESH : Natural Earth range le Sahara occidental sous le code SAH et ne lui
# donne qu'une « Admin-0 capital alt » (Bir Lehlou), siège disputé — la carte
# ne place donc aucun point plutôt que de trancher.
SANS_CAPITALE_NE = {"ESH"}

# Capitale retenue quand Natural Earth en liste plusieurs pour un même pays
# (capitale constitutionnelle ou siège officiel des institutions). Burundi :
# Natural Earth v5.1.2 classe Bujumbura en « Admin-0 capital » et Gitega,
# capitale politique depuis 2019, en simple « Admin-1 capital » ; la carte suit
# le classement de la source (Bujumbura).
CAPITALE_RETENUE = {
    "BEN": "Porto-Novo",
    "CIV": "Yamoussoukro",
    "MAR": "Rabat",
    "NGA": "Abuja",
    "SWZ": "Mbabane",
    "TZA": "Dodoma",
    "ZAF": "Pretoria",
}

# Exonymes français des capitales dont le nom Natural Earth diffère de l'usage
# français. Traduction de libellé uniquement : les coordonnées restent celles
# de Natural Earth.
NOM_FR = {
    "Algiers": "Alger",
    "Cairo": "Le Caire",
    "Addis Ababa": "Addis-Abeba",
    "Mogadishu": "Mogadiscio",
    "Port Louis": "Port-Louis",
    "Juba": "Djouba",
    "Sao Tome": "São Tomé",
    "Lome": "Lomé",
}

# Projection équirectangulaire centrée sur l'équateur (l'Afrique est à cheval
# sur lui) : x = longitude, y = −latitude, à l'échelle ci-dessous.
SCALE = 1.0
PAD = 1.5
SIMPLIFY_DEG = 0.06  # tolérance Douglas-Peucker, en degrés
# Terres entièrement au sud de cette latitude (îles du Prince-Édouard, à
# l'Afrique du Sud) : hors cadre, elles doubleraient la hauteur de la carte.
LAT_MIN_CADRE = -40.0


def _load(path_arg: str | None, src: dict) -> bytes:
    if path_arg:
        raw = Path(path_arg).read_bytes()
    else:
        with urllib.request.urlopen(src["url"], timeout=120) as resp:
            raw = resp.read()
    digest = hashlib.sha256(raw).hexdigest()
    if digest != src["sha256"]:
        raise SystemExit(
            f"SHA-256 inattendu pour {src['url']} : {digest} (attendu {src['sha256']})"
        )
    return raw


def _decode_arcs(topo: dict) -> list[list[tuple[float, float]]]:
    sx, sy = topo["transform"]["scale"]
    tx, ty = topo["transform"]["translate"]
    arcs = []
    for arc in topo["arcs"]:
        x = y = 0
        pts = []
        for dx, dy in arc:
            x += dx
            y += dy
            pts.append((x * sx + tx, y * sy + ty))
        arcs.append(pts)
    return arcs


def _rdp(pts: list[tuple[float, float]], eps: float) -> list[tuple[float, float]]:
    """Douglas-Peucker ; conserve les extrémités pour que les arcs se raccordent."""
    if len(pts) < 3:
        return pts
    (x1, y1), (x2, y2) = pts[0], pts[-1]
    dx, dy = x2 - x1, y2 - y1
    norm = math.hypot(dx, dy)
    best, idx = -1.0, 0
    for i in range(1, len(pts) - 1):
        px, py = pts[i]
        if norm == 0:
            d = math.hypot(px - x1, py - y1)
        else:
            d = abs(dy * px - dx * py + x2 * y1 - y2 * x1) / norm
        if d > best:
            best, idx = d, i
    if best <= eps:
        return [pts[0], pts[-1]]
    return _rdp(pts[: idx + 1], eps)[:-1] + _rdp(pts[idx:], eps)


def _african_geometries(topo: dict) -> list[dict]:
    out = []
    for g in topo["objects"]["countries"]["geometries"]:
        gid = g.get("id")
        name = (g.get("properties") or {}).get("name", "")
        if gid in NUMERIC_TO_ISO3 or gid in LAND_ONLY or name in LAND_ONLY_NAMES:
            out.append(g)
    return out


def _rings(geom: dict) -> list[list[int]]:
    if geom["type"] == "Polygon":
        return list(geom["arcs"])
    if geom["type"] == "MultiPolygon":
        return [ring for poly in geom["arcs"] for ring in poly]
    return []


def _ring_points(ring: list[int], arcs: list) -> list[tuple[float, float]]:
    pts: list[tuple[float, float]] = []
    for i in ring:
        seg = arcs[i] if i >= 0 else arcs[~i][::-1]
        pts.extend(seg if not pts else seg[1:])
    return pts


def _fmt(v: float) -> str:
    s = f"{v:.2f}".rstrip("0").rstrip(".")
    return "0" if s == "-0" else s


def build(world_raw: bytes, places_raw: bytes) -> dict:
    topo = json.loads(world_raw)
    arcs = [_rdp(a, SIMPLIFY_DEG) for a in _decode_arcs(topo)]
    geoms = _african_geometries(topo)

    # Arcs « extérieurs » : utilisés une seule fois par l'ensemble africain —
    # les côtes et la frontière avec l'Asie (Sinaï). Les arcs partagés par deux
    # pays africains (frontières intérieures) ne sont jamais tracés.
    usage: dict[int, int] = {}
    for g in geoms:
        for ring in _rings(g):
            for i in ring:
                k = i if i >= 0 else ~i
                usage[k] = usage.get(k, 0) + 1

    def proj(lon: float, lat: float) -> tuple[float, float]:
        return lon * SCALE, -lat * SCALE

    land_rings = []
    for g in geoms:
        for ring in _rings(g):
            pts = _ring_points(ring, arcs)
            if len(pts) >= 4 and max(lat for _, lat in pts) >= LAT_MIN_CADRE:
                land_rings.append([proj(*p) for p in pts])
    coast = [
        [proj(*p) for p in arcs[k]]
        for k, n in sorted(usage.items())
        if n == 1 and max(lat for _, lat in arcs[k]) >= LAT_MIN_CADRE
    ]

    places = json.loads(places_raw)["features"]
    iso3_set = {c["iso3"] for c in AFRICAN_COUNTRIES}
    candidats: dict[str, list[dict]] = {}
    for f in places:
        p = f["properties"]
        if not str(p.get("featurecla", "")).startswith("Admin-0 capital"):
            continue
        if p.get("adm0_a3") in iso3_set:
            candidats.setdefault(p["adm0_a3"], []).append(p)

    capitals = {}
    for iso3 in sorted(iso3_set):
        options = candidats.get(iso3) or []
        if not options:
            if iso3 in SANS_CAPITALE_NE:
                continue
            raise SystemExit(f"Aucune capitale Natural Earth pour {iso3}")
        voulu = CAPITALE_RETENUE.get(iso3)
        if voulu:
            choix = [p for p in options if p["name"] == voulu]
            if not choix:
                raise SystemExit(f"{voulu} absente de Natural Earth pour {iso3}")
            p = choix[0]
        elif len(options) == 1:
            p = options[0]
        else:
            raise SystemExit(
                f"{iso3} : plusieurs capitales Natural Earth "
                f"({', '.join(o['name'] for o in options)}) — choisir dans CAPITALE_RETENUE"
            )
        x, y = proj(p["longitude"], p["latitude"])
        capitals[iso3] = {
            "name": p["name"],
            "name_fr": NOM_FR.get(p["name"], p["name"]),
            "lat": round(p["latitude"], 4),
            "lon": round(p["longitude"], 4),
            "x": round(x, 3),
            "y": round(y, 3),
            "ne_id": p.get("ne_id"),
        }

    xs = [x for r in land_rings for x, _ in r] + [c["x"] for c in capitals.values()]
    ys = [y for r in land_rings for _, y in r] + [c["y"] for c in capitals.values()]
    minx, maxx, miny, maxy = min(xs) - PAD, max(xs) + PAD, min(ys) - PAD, max(ys) + PAD

    def d_of(rings: list, close: bool) -> str:
        parts = []
        for r in rings:
            coords = " ".join(f"{_fmt(x)} {_fmt(y)}" for x, y in r)
            parts.append(f"M{coords}{'Z' if close else ''}")
        return "".join(parts)

    return {
        "viewBox": [_fmt(minx), _fmt(miny), _fmt(maxx - minx), _fmt(maxy - miny)],
        "projection": "équirectangulaire : x = longitude, y = −latitude (degrés)",
        "land": d_of(land_rings, True),
        "coast": d_of(coast, False),
        "capitals": capitals,
        "sources": [
            {"label": WORLD["label"], "url": WORLD["url"], "sha256": WORLD["sha256"]},
            {"label": PLACES["label"], "url": PLACES["url"], "sha256": PLACES["sha256"]},
        ],
        "without_capital": sorted(SANS_CAPITALE_NE),
        "notes": [
            "Seul le contour des terres est tracé : aucune frontière intérieure.",
            "Terres au sud de 40° S (îles du Prince-Édouard) hors cadre.",
            "Sahara occidental (ESH) : Natural Earth v5.1.2 ne lui donne, sous le "
            "code SAH, qu'une capitale « alt » disputée (Bir Lehlou) ; pas de point.",
            "Burundi : Natural Earth v5.1.2 classe Bujumbura en capitale ; Gitega, "
            "capitale politique depuis 2019, n'y est que capitale de province.",
        ],
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    ap.add_argument("--world", help="countries-50m.json local (sinon téléchargé)")
    ap.add_argument("--places", help="ne_10m_populated_places_simple.geojson local")
    args = ap.parse_args()
    data = build(_load(args.world, WORLD), _load(args.places, PLACES))
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")) + "\n")
    print(
        f"{OUTPUT.relative_to(ROOT)} : {len(data['capitals'])} capitales, "
        f"{OUTPUT.stat().st_size // 1024} Ko"
    )


if __name__ == "__main__":
    main()
