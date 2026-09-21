"""
Production Africaine - Gestion des données de production (Agriculture, Industrie, Mines)
Charge et expose les données de production pour 2021-2024
"""

import hashlib
import json
import os
from pathlib import Path
from typing import Dict, List, Optional

# Chemin du fichier JSON
DATA_FILE = os.path.join(
    os.path.dirname(__file__), "..", "data", "json", "production_africaine.json"
)

# Cache global
_production_data = None
# Version courte du dataset (stamp d'invalidation de cache)
_production_data_version = None


def _normalize_country_iso3(country_iso3: Optional[str]) -> Optional[str]:
    """Normalise le code ISO3 pays pour les filtres."""
    if country_iso3 is None:
        return None
    return country_iso3.strip().upper()


def _extract_years(records: List[Dict]) -> List[int]:
    """Retourne la liste triée des années distinctes présentes dans les records.

    Trié de façon croissante pour que ``years_covered[-1]`` corresponde à
    l'année la plus récente.
    """
    years = {r.get("year") for r in records if r.get("year") is not None}
    return sorted(years)


def load_production_data():
    """Charge les données de production depuis le fichier JSON"""
    global _production_data
    if _production_data is None:
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                _production_data = json.load(f)
            print(f"✅ Loaded production data from {DATA_FILE}")
            print(
                f"   - Value added macro: {len(_production_data.get('value_added_macro', []))} records"
            )
            print(
                f"   - Agriculture FAOSTAT: {len(_production_data.get('agri_faostat', []))} records"
            )
            print(
                f"   - Manufacturing UNIDO: {len(_production_data.get('manufacturing_unido', []))} records"
            )
            print(f"   - Mining USGS: {len(_production_data.get('mining_usgs', []))} records")
        except FileNotFoundError:
            print(f"❌ File not found: {DATA_FILE}")
            _production_data = {
                "value_added_macro": [],
                "agri_faostat": [],
                "manufacturing_unido": [],
                "mining_usgs": [],
            }
        except json.JSONDecodeError as e:
            print(f"❌ JSON decode error: {e}")
            _production_data = {
                "value_added_macro": [],
                "agri_faostat": [],
                "manufacturing_unido": [],
                "mining_usgs": [],
            }
    return _production_data


def get_production_data_version() -> str:
    """
    Retourne une version courte (8 hex) du dataset de production.

    Dérivée de metadata.last_updated + nombre d'enregistrements par section.
    Sert de stamp d'invalidation de cache : lorsqu'on reconstruit
    production_africaine.json (build_production_real.py /
    build_production_faostat_usgs.py), cette version change, ce qui rend les
    analyses Claude en cache inaccessibles (elles expirent ensuite par TTL).
    Ainsi les analyses servies après une mise à jour des données portent
    toujours les capacités de production à jour, sans purge manuelle.
    """
    global _production_data_version
    if _production_data_version is None:
        data = load_production_data()
        meta = data.get("metadata", {}) if isinstance(data, dict) else {}
        signature = "|".join(
            [
                str(meta.get("last_updated", "")),
                str(len(data.get("agri_faostat", []))),
                str(len(data.get("manufacturing_unido", []))),
                str(len(data.get("manufacturing_unsd", []))),
                str(len(data.get("mining_usgs", []))),
                str(len(data.get("value_added_macro", []))),
            ]
        )
        _production_data_version = hashlib.md5(signature.encode()).hexdigest()[:8]
    return _production_data_version


# ==========================================
# VALUE ADDED MACRO (WDI/WEO)
# ==========================================


def get_value_added(
    country_iso3: Optional[str] = None, year: Optional[int] = None, sector: Optional[str] = None
) -> List[Dict]:
    """
    Récupère les données de valeur ajoutée macro

    Args:
        country_iso3: Code ISO3 du pays (ex: 'ZAF')
        year: Année (2021-2024)
        sector: Section ISIC (A, B-F, C)
    """
    data = load_production_data()
    records = data.get("value_added_macro", [])

    country_iso3 = _normalize_country_iso3(country_iso3)

    if country_iso3:
        records = [r for r in records if r.get("country_iso3") == country_iso3]

    if year:
        records = [r for r in records if r.get("year") == year]

    if sector:
        records = [r for r in records if r.get("sector_isic_section") == sector]

    return records


def get_value_added_by_country(country_iso3: str) -> Dict:
    """Récupère toutes les séries de valeur ajoutée pour un pays.

    Les parts de PIB et les montants en USD partagent le même ``sector_detail``
    (« Manufacturing » désigne le secteur, pas la mesure). Les grouper sur ce
    seul libellé mettrait 7,4 (% du PIB) et 21 839 012 706 (USD) dans la même
    série. Les deux familles sont donc rendues séparément :

    * ``data_by_sector`` — les parts et la croissance, en pourcentage. C'est le
      contenu historique de ce champ : inchangé, y compris quand aucun montant
      n'est publié ;
    * ``data_by_sector_usd`` — les montants en USD courants.
    """
    country_iso3 = _normalize_country_iso3(country_iso3)
    records = get_value_added(country_iso3=country_iso3)

    # Organiser par secteur, en tenant les deux unités à l'écart.
    by_sector: Dict[str, List[Dict]] = {}
    by_sector_usd: Dict[str, List[Dict]] = {}
    for record in records:
        sector = record.get("sector_detail", "Unknown")
        target = by_sector_usd if record.get("unit") == "USD" else by_sector
        target.setdefault(sector, []).append(record)

    years_covered = _extract_years(records)

    return {
        "country_iso3": country_iso3,
        "country_name": records[0].get("country_name") if records else None,
        "data_by_sector": by_sector,
        "data_by_sector_usd": by_sector_usd,
        "total_records": len(records),
        "years_covered": years_covered,
        "latest_year": years_covered[-1] if years_covered else None,
    }


# ==========================================
# AGRICULTURE FAOSTAT
# ==========================================


def get_agriculture_production(
    country_iso3: Optional[str] = None, year: Optional[int] = None, commodity: Optional[str] = None
) -> List[Dict]:
    """
    Récupère les données de production agricole

    Args:
        country_iso3: Code ISO3 du pays
        year: Année (2021-2024)
        commodity: Nom ou code du produit (ex: 'Maize', '0015')
    """
    data = load_production_data()
    records = data.get("agri_faostat", [])

    country_iso3 = _normalize_country_iso3(country_iso3)

    if country_iso3:
        records = [r for r in records if r.get("country_iso3") == country_iso3]

    if year:
        records = [r for r in records if r.get("year") == year]

    if commodity:
        records = [
            r
            for r in records
            if commodity.lower() in r.get("commodity_label", "").lower()
            or commodity == r.get("commodity_code")
        ]

    return records


def get_agriculture_by_country(country_iso3: str) -> Dict:
    """Récupère toutes les productions agricoles pour un pays"""
    country_iso3 = _normalize_country_iso3(country_iso3)
    records = get_agriculture_production(country_iso3=country_iso3)

    # Organiser par produit
    by_commodity = {}
    for record in records:
        commodity = record.get("commodity_label", "Unknown")
        if commodity not in by_commodity:
            by_commodity[commodity] = []
        by_commodity[commodity].append(record)

    years_covered = _extract_years(records)

    return {
        "country_iso3": country_iso3,
        "country_name": records[0].get("country_name") if records else None,
        "data_by_commodity": by_commodity,
        "total_records": len(records),
        "years_covered": years_covered,
        "latest_year": years_covered[-1] if years_covered else None,
    }


def get_agriculture_projections(
    country_iso3: Optional[str] = None, year: Optional[int] = None, commodity: Optional[str] = None
) -> List[Dict]:
    """
    Récupère les PRÉVISIONS agricoles (OECD-FAO Agricultural Outlook).

    Stockées séparément des productions observées (``agri_projections``) car ce
    sont des projections (horizons 2025/2030), à ne pas confondre avec les
    productions réelles FAOSTAT.

    Args:
        country_iso3: Code ISO3 du pays
        year: Horizon de projection (2025, 2030)
        commodity: Nom de l'agrégat (ex: 'Cereals')
    """
    data = load_production_data()
    records = data.get("agri_projections", [])

    country_iso3 = _normalize_country_iso3(country_iso3)

    if country_iso3:
        records = [r for r in records if r.get("country_iso3") == country_iso3]
    if year:
        records = [r for r in records if r.get("year") == year]
    if commodity:
        records = [r for r in records if commodity.lower() in r.get("commodity_label", "").lower()]
    return records


# ==========================================
# MANUFACTURING UNIDO
# ==========================================


def get_manufacturing_production(
    country_iso3: Optional[str] = None, year: Optional[int] = None, isic_code: Optional[str] = None
) -> List[Dict]:
    """
    Récupère les données de production manufacturière

    Args:
        country_iso3: Code ISO3 du pays
        year: Année (2021-2024)
        isic_code: Code ISIC Rev.4 (ex: '10', '11', '13')
    """
    data = load_production_data()
    records = data.get("manufacturing_unido", [])

    country_iso3 = _normalize_country_iso3(country_iso3)

    if country_iso3:
        records = [r for r in records if r.get("country_iso3") == country_iso3]

    if year:
        records = [r for r in records if r.get("year") == year]

    if isic_code:
        records = [r for r in records if r.get("isic_code") == isic_code]

    return records


def get_manufacturing_by_country(country_iso3: str) -> Dict:
    """Récupère toutes les productions manufacturières pour un pays"""
    country_iso3 = _normalize_country_iso3(country_iso3)
    records = get_manufacturing_production(country_iso3=country_iso3)

    # Organiser par secteur ISIC
    by_isic = {}
    for record in records:
        isic = f"{record.get('isic_code')} - {record.get('isic_label', 'Unknown')}"
        if isic not in by_isic:
            by_isic[isic] = []
        by_isic[isic].append(record)

    years_covered = _extract_years(records)

    return {
        "country_iso3": country_iso3,
        "country_name": records[0].get("country_name") if records else None,
        "data_by_isic": by_isic,
        "key_products": get_manufacturing_key_products(country_iso3),
        "manufacturing_profile": get_manufacturing_profile(country_iso3),
        "total_records": len(records),
        "years_covered": years_covered,
        "latest_year": years_covered[-1] if years_covered else None,
    }


def _unido_industry_data() -> Dict:
    """
    Table UNIDO INDSTAT4 curée (``backend/etl/unido_data.py``), source des
    enregistrements manufacturiers du fichier de production.

    Import paresseux + dégradation silencieuse : le fichier de production reste
    la source d'autorité pour la valeur ajoutée par secteur ; on ne lit ici que
    les signaux additionnels curés (produits phares, part haute technologie,
    exports manufacturiers) qui ne sont pas matérialisés dans le JSON, afin que
    le module production expose le MAXIMUM d'information disponible sans dépendre
    d'une reconstruction du fichier.
    """
    try:
        from etl.unido_data import UNIDO_INDUSTRY_DATA

        return UNIDO_INDUSTRY_DATA
    except Exception:  # pragma: no cover - source absente
        return {}


def get_manufacturing_key_products(country_iso3: str) -> List[str]:
    """
    Produits manufacturés phares (exportables) curés pour un pays.

    Ces libellés (« Ciment », « Acier », « Véhicules automobiles »…) nomment
    concrètement ce qu'un pays produit déjà, au-delà de la seule valeur ajoutée
    par division ISIC. Ils ancrent la découverte d'opportunités d'export sur des
    produits réels. Retourne ``[]`` si le pays n'est pas curé.
    """
    iso3 = _normalize_country_iso3(country_iso3)
    entry = _unido_industry_data().get(iso3) or {}
    return list(entry.get("key_products", []))


def get_manufacturing_profile(country_iso3: str) -> Dict:
    """
    Profil manufacturier synthétique d'un pays (signaux UNIDO curés au-delà de
    la valeur ajoutée par secteur) : valeur ajoutée manufacturière totale, part
    moyenne/haute technologie, emploi industriel, exports manufacturiers, rang
    CIP. Champs absents -> ``None``. Retourne ``{}`` si le pays n'est pas curé.
    """
    iso3 = _normalize_country_iso3(country_iso3)
    entry = _unido_industry_data().get(iso3)
    if not entry:
        return {}
    return {
        "country_name": entry.get("country_name"),
        "region": entry.get("region"),
        "mva_mln_usd": entry.get("mva_2024_mln_usd", entry.get("mva_2023_mln_usd")),
        "mva_gdp_percent": entry.get("mva_gdp_percent"),
        "mva_per_capita_usd": entry.get("mva_per_capita_usd"),
        "mht_share_mva": entry.get("mht_share_mva"),
        "industry_employment": entry.get("industry_employment"),
        "exports_manuf_mln_usd": entry.get("exports_manuf_mln_usd"),
        "manuf_share_exports": entry.get("manuf_share_exports"),
        "cip_index_rank": entry.get("cip_index_rank"),
        "data_year": entry.get("data_year"),
        "source": entry.get("source"),
    }


# ==========================================
# MANUFACTURING MESURÉ — agrégats nationaux UNSD (source UNIDO)
# ==========================================


def get_manufacturing_unsd(
    country_iso3: Optional[str] = None,
    year: Optional[int] = None,
    indicator_code: Optional[str] = None,
) -> List[Dict]:
    """Agrégats manufacturiers mesurés publiés par l'UNSD (base ODD, cible 9.2).

    Dimension distincte de ``manufacturing_unido`` : celle-ci ventile par
    division ISIC et repose sur une structure estimée pour 32 pays, faute
    d'accès libre à INDSTAT ; celle-là mesure trois agrégats nationaux.
    Les confondre ferait passer du mesuré pour de l'estimé.

    Args:
        country_iso3: Code ISO3 du pays (ex: 'KEN')
        year: Année
        indicator_code: Série UNSD ('NV_IND_MANFPC', 'SL_TLF_MANF', 'NV_IND_TECH')
    """
    records = load_production_data().get("manufacturing_unsd", [])

    country_iso3 = _normalize_country_iso3(country_iso3)
    if country_iso3:
        records = [r for r in records if r.get("country_iso3") == country_iso3]
    if year:
        records = [r for r in records if r.get("year") == year]
    if indicator_code:
        records = [r for r in records if r.get("indicator_code") == indicator_code]

    return records


def get_manufacturing_unsd_by_country(country_iso3: str) -> Dict:
    """Séries manufacturières mesurées d'un pays, groupées par indicateur."""
    country_iso3 = _normalize_country_iso3(country_iso3)
    records = get_manufacturing_unsd(country_iso3=country_iso3)

    by_indicator: Dict[str, List[Dict]] = {}
    for record in records:
        by_indicator.setdefault(record.get("indicator_code", "Unknown"), []).append(record)
    for series in by_indicator.values():
        series.sort(key=lambda r: r.get("year") or 0)

    years_covered = _extract_years(records)

    return {
        "country_iso3": country_iso3,
        "country_name": records[0].get("country_name") if records else None,
        "data_by_indicator": by_indicator,
        "total_records": len(records),
        "years_covered": years_covered,
        "latest_year": years_covered[-1] if years_covered else None,
    }


# ==========================================
# MINING USGS
# ==========================================


def get_mining_production(
    country_iso3: Optional[str] = None, year: Optional[int] = None, commodity: Optional[str] = None
) -> List[Dict]:
    """
    Récupère les données de production minière

    Args:
        country_iso3: Code ISO3 du pays
        year: Année (2021-2024)
        commodity: Nom ou code du minerai (ex: 'Gold', 'AU')
    """
    data = load_production_data()
    records = data.get("mining_usgs", [])

    country_iso3 = _normalize_country_iso3(country_iso3)

    if country_iso3:
        records = [r for r in records if r.get("country_iso3") == country_iso3]

    if year:
        records = [r for r in records if r.get("year") == year]

    if commodity:
        records = [
            r
            for r in records
            if commodity.lower() in r.get("commodity_label", "").lower()
            or commodity.upper() == r.get("commodity_code")
        ]

    return records


#: Sources consultées pour la dimension minière, dans l'ordre où elles couvrent
#: le terrain. Nommées dans la réponse afin qu'une absence soit vérifiable.
_MINING_SOURCES = (
    "USGS Mineral Commodity Summaries 2025 (minéraux)",
    "EIA International Energy Statistics (pétrole, gaz)",
    "OPEC Annual Statistical Bulletin (pétrole)",
    "World Nuclear Association (uranium)",
)


def get_mining_coverage(country_iso3: str, has_records: bool) -> Dict:
    """Explique l'état de couverture minière d'un pays.

    Treize pays africains n'ont aucun enregistrement minier. Leur servir un
    onglet vide laisse le lecteur conclure ce qu'il veut — le plus souvent que
    la plateforme a perdu la donnée. Cette fonction dit ce qui a été consulté
    et ce que la source en rapporte.

    Distinction qui fait tout : l'absence chez USGS n'est PAS une absence
    d'extraction. MCS ne recense ni la production artisanale, ni les volumes
    sous son seuil de significativité, ni les hydrocarbures, ni l'uranium.
    Le statut renvoyé porte donc sur nos sources, jamais sur le pays.
    """
    from etl.usgs_world_coverage import (
        USGS_LISTED_PRODUCERS_AFRICA,
        USGS_MCS_EDITION,
        USGS_MCS_SOURCE_URL,
    )

    listed_by_usgs = country_iso3 in USGS_LISTED_PRODUCERS_AFRICA

    if has_records:
        status = "COVERED"
        note = "Production publiée par au moins une des sources consultées."
    elif listed_by_usgs:
        # Cas à traiter en priorité : USGS recense ce pays, mais nous n'avons
        # pas ingéré ses commodités. C'est un trou d'ingestion, pas un trait
        # du pays.
        status = "LISTED_BY_USGS_NOT_INGESTED"
        note = (
            "USGS recense une production minérale pour ce pays, mais aucune de ses "
            "commodités n'est encore ingérée ici. Lacune de collecte, à combler."
        )
    else:
        status = "NOT_LISTED_BY_SOURCES"
        note = (
            "Aucune production rapportée pour ce pays par les sources consultées. "
            "Cela ne signifie pas qu'il n'extrait rien : USGS ne recense ni la "
            "production artisanale, ni les volumes sous son seuil de "
            "significativité ; les hydrocarbures et l'uranium relèvent des autres "
            "sources listées, qui ne le mentionnent pas davantage."
        )

    return {
        "status": status,
        "listed_by_usgs": listed_by_usgs,
        "sources_consulted": list(_MINING_SOURCES),
        "usgs_edition": USGS_MCS_EDITION,
        "usgs_source_url": USGS_MCS_SOURCE_URL,
        "note": note,
    }


def get_mining_by_country(country_iso3: str) -> Dict:
    """Récupère toutes les productions minières pour un pays.

    Une absence de donnée est renseignée plutôt que muette : voir ``coverage``.
    """
    country_iso3 = _normalize_country_iso3(country_iso3)
    records = get_mining_production(country_iso3=country_iso3)

    # Organiser par minerai
    by_commodity = {}
    for record in records:
        commodity = record.get("commodity_label", "Unknown")
        if commodity not in by_commodity:
            by_commodity[commodity] = []
        by_commodity[commodity].append(record)

    years_covered = _extract_years(records)

    return {
        "country_iso3": country_iso3,
        "country_name": records[0].get("country_name") if records else None,
        "data_by_commodity": by_commodity,
        "total_records": len(records),
        "years_covered": years_covered,
        "latest_year": years_covered[-1] if years_covered else None,
        "coverage": get_mining_coverage(country_iso3, bool(records)),
    }


# ==========================================
# STATISTICS & OVERVIEW
# ==========================================


def get_production_statistics() -> Dict:
    """Calcule des statistiques globales sur les données de production"""
    data = load_production_data()

    # Compter les pays uniques dans chaque dimension
    countries_va = set(r.get("country_iso3") for r in data.get("value_added_macro", []))
    countries_agri = set(r.get("country_iso3") for r in data.get("agri_faostat", []))
    countries_manuf = set(r.get("country_iso3") for r in data.get("manufacturing_unido", []))
    countries_manuf_unsd = set(r.get("country_iso3") for r in data.get("manufacturing_unsd", []))
    countries_mining = set(r.get("country_iso3") for r in data.get("mining_usgs", []))

    all_countries = (
        countries_va | countries_agri | countries_manuf | countries_manuf_unsd | countries_mining
    )

    # Années couvertes
    years_va = set(r.get("year") for r in data.get("value_added_macro", []))
    years_agri = set(r.get("year") for r in data.get("agri_faostat", []))
    years_manuf = set(r.get("year") for r in data.get("manufacturing_unido", []))
    years_manuf_unsd = set(r.get("year") for r in data.get("manufacturing_unsd", []))
    years_mining = set(r.get("year") for r in data.get("mining_usgs", []))

    all_years = sorted(years_va | years_agri | years_manuf | years_manuf_unsd | years_mining)

    return {
        "total_countries": len(all_countries),
        "countries_list": sorted(list(all_countries)),
        "years_covered": all_years,
        "dimensions": {
            "value_added_macro": {
                "total_records": len(data.get("value_added_macro", [])),
                "countries": len(countries_va),
                "years": sorted(list(years_va)),
            },
            "agriculture_faostat": {
                "total_records": len(data.get("agri_faostat", [])),
                "countries": len(countries_agri),
                "years": sorted(list(years_agri)),
            },
            "manufacturing_unido": {
                "total_records": len(data.get("manufacturing_unido", [])),
                "countries": len(countries_manuf),
                "years": sorted(list(years_manuf)),
            },
            "manufacturing_unsd": {
                "total_records": len(data.get("manufacturing_unsd", [])),
                "countries": len(countries_manuf_unsd),
                "years": sorted(list(years_manuf_unsd)),
            },
            "mining_usgs": {
                "total_records": len(data.get("mining_usgs", [])),
                "countries": len(countries_mining),
                "years": sorted(list(years_mining)),
            },
            "agriculture_projections": {
                "total_records": len(data.get("agri_projections", [])),
                "countries": len(
                    set(r.get("country_iso3") for r in data.get("agri_projections", []))
                ),
                "years": sorted(
                    set(
                        r.get("year")
                        for r in data.get("agri_projections", [])
                        if r.get("year") is not None
                    )
                ),
            },
        },
    }


def get_country_production_overview(country_iso3: str) -> Dict:
    """Vue d'ensemble complète de la production pour un pays"""
    country_iso3 = _normalize_country_iso3(country_iso3)
    return {
        "country_iso3": country_iso3,
        "value_added": get_value_added_by_country(country_iso3),
        "agriculture": get_agriculture_by_country(country_iso3),
        "agriculture_projections": get_agriculture_projections(country_iso3),
        "manufacturing": get_manufacturing_by_country(country_iso3),
        "mining": get_mining_by_country(country_iso3),
    }


# Initialize data on module import
load_production_data()
