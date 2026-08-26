"""
National-need (demand) estimation service for the Opportunités decision tools.

Answers "how much of product X does country C need?" even when no direct
consumption statistic exists — through a TRANSPARENT cascade, from measured to
modelled. An estimated value is never presented as measured: every result
carries ``is_estimation``, ``estimation_level``, the formula, its inputs and its
sources, so a decision-maker can see exactly how the number was produced and
challenge it.

Cascade (best available wins):
  L1 — Measured apparent consumption = Production + Imports − Exports
       (real, when production + bilateral trade are both available).
  L2 — Population proxy: need ≈ population × per-capita continental availability,
       where per-capita availability = continental production ÷ continental
       population. Uses real FAO/USGS/UNIDO production + curated populations.
  L3 — Standard-of-living adjustment: L2 × (GDP/capita_country ÷ GDP/capita_avg)^ε.
       GDP/capita_avg is the POPULATION-WEIGHTED continental average (consistent
       with the continental per-capita reference of L2); ε is resolved per
       product class (HS chapter — staples ~0.3, pharma ~0.9, durables ~1.2),
       overridable, always exposed in the payload.

Garde-fous (chacun exposé dans le payload, jamais silencieux):
  - reference_scope: correspondance production au chapitre SH2 ⇒ le besoin
    estimé porte sur tout le SECTEUR, pas le seul produit — dit explicitement.
  - reference_coverage_caveat: référence de production à couverture partielle
    (ex. UNIDO ingéré pour 1-2 pays) ⇒ propagé dans la note.
  - calibration: les importations observées du pays (flux réel OEC) servent de
    PLANCHER mesuré — un proxy en dessous d'un flux réel est démenti par lui.
  - value arrondie à 3 chiffres significatifs (précision honnête d'une
    estimation).

No fabrication: if neither production nor population is available, the estimate
is returned ``available: False`` with a note.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Optional

_log = logging.getLogger(__name__)

_GDP_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "json" / "wb_gdp_pc.json"

# Default income elasticity of demand (modelling assumption, exposed to caller).
# ~0.4 is a common order of magnitude for food staples; discretionary goods higher.
DEFAULT_INCOME_ELASTICITY = 0.4

# Élasticité-revenu par classe de produit (chapitre SH) — ordres de grandeur de
# la littérature empirique (loi d'Engel, estimations transnationales type USDA
# ERS / Banque Mondiale ICP) : la demande d'aliments de base croît moins vite
# que le revenu (<0,5), celle des biens discrétionnaires (électronique,
# véhicules) plus vite (≥1). Une élasticité UNIQUE de 0,4 pour tout — des
# céréales aux téléviseurs — sous-estimait systématiquement l'effet revenu sur
# les biens manufacturés et l'exagérait sur les produits de base. Hypothèse de
# modélisation : exposée dans le payload et surchargeable par l'appelant.
_STAPLE_FOOD_CHAPTERS = {"07", "10", "11", "19"}  # légumes, céréales, minoterie, prép. céréales
_INCOME_ELASTICITY_BY_CLASS = [
    # (ensemble de chapitres SH2, élasticité, libellé de la classe)
    (_STAPLE_FOOD_CHAPTERS, 0.3, "aliments de base"),
    ({f"{c:02d}" for c in range(1, 25)} - _STAPLE_FOOD_CHAPTERS, 0.5, "autres agroalimentaires"),
    ({"30"}, 0.9, "produits pharmaceutiques"),
    ({f"{c:02d}" for c in range(50, 64)}, 0.8, "textiles et habillement"),
    ({"84", "85", "87"}, 1.2, "biens durables (machines, électronique, véhicules)"),
]


def income_elasticity_for_hs(hs_code: str) -> Dict:
    """Élasticité-revenu résolue par classe de produit (chapitre SH2)."""
    chapter = ("".join(ch for ch in str(hs_code or "") if ch.isdigit()))[:2]
    for chapters, elasticity, label in _INCOME_ELASTICITY_BY_CLASS:
        if chapter in chapters:
            return {"value": elasticity, "product_class": label}
    return {"value": DEFAULT_INCOME_ELASTICITY, "product_class": "défaut (classe non mappée)"}


# Chapitres SH2 de biens durables / à longue durée de conservation : équipements,
# instruments, pièces détachées — l'achat est cyclique et ponctuel (une commande
# groupée peut couvrir plusieurs années), pas un flux régulier comme la nourriture.
# Une seule année d'import y est un signal bruité (année creuse après un gros lot,
# ou pic ponctuel) : moyenner sur plusieurs années restitue le besoin ANNUEL
# TYPIQUE. Exemple type : aiguilles/instruments médicaux (SH90).
# Exclus délibérément : pharma (30, péremption réelle), textile/habillement/
# chaussures (50-67, cycles de mode courts), agroalimentaire/vivant (01-24).
_LONG_SHELF_LIFE_CHAPTERS = (
    {f"{c:02d}" for c in range(25, 27)}  # minéraux (25-26)
    | {f"{c:02d}" for c in range(28, 30)}  # chimie de base (hors 30 pharma)
    | {"31", "32", "34", "38", "39", "40"}  # engrais, teintures, plastiques, caoutchouc
    | {f"{c:02d}" for c in range(68, 84)}  # verre/céramique/métaux et ouvrages (68-83)
    | {"84", "85", "86", "87", "88", "89"}  # machines, électrique, véhicules, aéro/naval
    | {"90", "91", "92"}  # instruments médicaux/optiques/précision, horlogerie
    | {"94", "95", "96"}  # mobilier, jouets/équipements sportifs, articles divers
)


def is_long_shelf_life_product(hs_code: str) -> bool:
    """Vrai si le chapitre SH2 correspond à un bien durable / longue conservation
    (équipement, instrument, pièce) pour lequel un besoin annuel doit être estimé
    par une MOYENNE pluriannuelle des imports plutôt que la seule dernière année."""
    chapter = ("".join(ch for ch in str(hs_code or "") if ch.isdigit()))[:2]
    return chapter in _LONG_SHELF_LIFE_CHAPTERS


def estimate_need_from_own_imports(
    hs_code: str, country_iso3: str, imports_history: Optional[list]
) -> Optional[Dict]:
    """
    Repli quand la production continentale est INDISPONIBLE (aucun mapping
    HS -> commodité FAO/USGS/UNIDO, ex. instruments médicaux SH90) : plutôt que
    de renvoyer ``available: False``, utilise les IMPORTS RÉELS du pays lui-même
    pour ce SH (canal OEC partagé avec le module Statistiques) comme signal
    direct et mesuré du besoin national.

    ``imports_history`` : liste ``[{"year": .., "import_value_usd": .., "no_data": bool}]``
    sur plusieurs années (typiquement 5), la plus récente en dernier ou dans le
    désordre — triée ici.

    Deux régimes, selon la nature du produit :
    - Bien durable / longue conservation (SH classé via
      :func:`is_long_shelf_life_product`, ex. équipement, instrument, pièce) :
      MOYENNE des années effectivement observées. Ces achats sont ponctuels/
      cycliques (un lot de plusieurs années peut être importé en une seule
      année puis rien pendant 2-3 ans) — une seule année serait un signal bruité,
      la moyenne restitue le besoin ANNUEL TYPIQUE.
    - Autres produits (péremption, cycles de mode, etc.) : dernière année
      disponible avec un import > 0 seulement — moyenner lisserait à tort une
      vraie tendance récente (ex. une filière en déclin ou en forte croissance).

    Retourne None si aucune donnée exploitable n'existe (l'appelant garde alors
    le message "estimation impossible").
    """
    rows = sorted(
        (r for r in (imports_history or []) if not r.get("no_data")),
        key=lambda r: r.get("year") or 0,
    )
    if not rows:
        return None

    long_shelf = is_long_shelf_life_product(hs_code)

    if long_shelf:
        values = [float(r.get("import_value_usd") or 0.0) for r in rows]
        if not any(v > 0 for v in values):
            return None
        avg_value = sum(values) / len(values)
        years_used = [r.get("year") for r in rows]
        method = (
            f"Moyenne des importations réelles du pays sur {len(rows)} années "
            f"({years_used[0]}-{years_used[-1]}) pour ce code SH — bien durable/"
            "longue conservation : une seule année serait un signal bruité "
            "(achat ponctuel/cyclique), la moyenne restitue le besoin annuel typique."
        )
        note_detail = (
            f"Moyenne pluriannuelle ({len(rows)} années : "
            f"{', '.join(str(y) for y in years_used)}) car ce produit relève d'une "
            "catégorie à longue durée de conservation/vie utile (équipement, "
            "instrument, pièce détachée...) — l'achat y est cyclique, pas régulier."
        )
        basis = "own_imports_multi_year_average"
    else:
        latest = next((r for r in reversed(rows) if (r.get("import_value_usd") or 0) > 0), None)
        if not latest:
            return None
        avg_value = float(latest["import_value_usd"])
        years_used = [latest.get("year")]
        method = (
            f"Dernière année d'importations réelles du pays disponible "
            f"({years_used[0]}) pour ce code SH."
        )
        note_detail = (
            "Basé sur la dernière année d'imports observés (pas de moyenne : produit "
            "hors catégorie longue conservation, une année récente est plus "
            "représentative qu'une moyenne pluriannuelle)."
        )
        basis = "own_imports_latest_year"

    return {
        "available": True,
        "is_estimation": True,
        "estimation_level": 2,
        "level_label": "Proxy import national (estimé, sans production continentale)",
        "value": _round_sig(avg_value, 3),
        "unit": "USD",
        "reference_basis": basis,
        "is_long_shelf_life": long_shelf,
        "method": method,
        "inputs": {
            "years_used": years_used,
            "n_years_averaged": len(rows) if long_shelf else 1,
            "per_year_import_value_usd": (
                {r.get("year"): r.get("import_value_usd") for r in rows} if long_shelf else None
            ),
        },
        "sources": ["OEC / UN Comtrade (BACI) — importations observées du pays"],
        "observed_imports": None,
        "note": (
            "Estimation transparente : aucune production continentale de référence "
            f"pour ce code SH (SH{hs_code}) — repli sur les importations réelles du "
            f"pays lui-même comme signal direct de besoin. {note_detail} Cette valeur "
            "est en USD (pas d'unité physique de référence disponible pour ce produit)."
        ),
    }


def _implied_per_capita(need: Optional[float], unit: Optional[str], population: Optional[int]) -> Optional[Dict]:
    """
    Besoin estimé RAMENÉ PAR HABITANT — le contrôle de vraisemblance le plus
    direct d'une estimation de besoin national. Un total brut (« 581 000 t »)
    ne dit rien sans dénominateur ; ramené à l'habitant il devient immédiatement
    challengeable : ~13 kg/hab/an de bananes = plausible, alors que 8 t/hab/an
    sauterait aux yeux comme absurde. Exprimé en kg/hab/an quand l'unité de
    référence est la tonne (lisible à l'échelle humaine), sinon dans l'unité
    native par habitant.
    """
    if not need or not population or population <= 0:
        return None
    u = (unit or "").lower()
    if "tonne" in u:
        return {
            "value": round(need / population * 1000.0, 2),
            "unit": "kg/hab/an",
        }
    if u == "usd":
        return {
            "value": _round_sig(need / population, 3),
            "unit": "USD/hab/an",
        }
    return {
        "value": _round_sig(need / population, 3),
        "unit": f"{unit}/hab/an" if unit else "par hab/an",
    }


def _round_sig(x: float, sig: int = 3) -> float:
    """Arrondi à ``sig`` chiffres significatifs — une estimation affichée au
    centime près (« 3 694 915 962,13 USD ») revendique une précision qu'elle
    n'a pas ; trois chiffres significatifs disent honnêtement « ≈ 3,69 Md »."""
    if not x:
        return 0.0
    from math import floor, log10

    return round(x, -int(floor(log10(abs(x)))) + (sig - 1))


_POP_SOURCE = "constants.AFRICAN_COUNTRIES (populations curées, ~WB SP.POP.TOTL)"


def _country_index() -> Dict[str, Dict]:
    """ISO3 -> country record (population, region, name) from curated constants."""
    try:
        from constants import AFRICAN_COUNTRIES

        return {c["iso3"]: c for c in AFRICAN_COUNTRIES if c.get("iso3")}
    except Exception as exc:  # pragma: no cover - defensive
        _log.warning("country index unavailable: %s", exc)
        return {}


def get_population(country_iso3: str) -> Dict:
    """Curated population + region for an African country."""
    idx = _country_index()
    rec = idx.get((country_iso3 or "").upper())
    if rec and rec.get("population"):
        return {
            "available": True,
            "value": rec["population"],
            "region": rec.get("region"),
            "country_name": rec.get("name"),
            "source": _POP_SOURCE,
        }
    return {"available": False, "value": None, "note": "Population indisponible pour ce pays."}


def _continental_population(idx: Dict[str, Dict]) -> int:
    return sum(int(c.get("population") or 0) for c in idx.values())


def _load_gdp() -> Dict:
    """Load WB GDP-per-capita dataset (produced by etl/fetch_wb_gdp). Graceful."""
    try:
        if _GDP_PATH.exists():
            with open(_GDP_PATH, encoding="utf-8") as fh:
                return json.load(fh) or {}
    except Exception as exc:  # pragma: no cover - defensive
        _log.warning("GDP dataset unreadable: %s", exc)
    return {}


def _gdp_from_country_profiles(country_iso3: str) -> Optional[Dict]:
    """PIB/habitant depuis le module Profils Pays (``country_data.REAL_COUNTRY_DATA``,
    Banque Mondiale WDI 2024) — déjà embarqué dans le dépôt pour les 54 pays.
    Sert de source par défaut : plus besoin d'ETL réseau pour l'ajustement L3."""
    try:
        from country_data import REAL_COUNTRY_DATA

        rec = REAL_COUNTRY_DATA.get((country_iso3 or "").upper()) or {}
        value = rec.get("gdp_per_capita_2024")
        if value is not None:
            return {
                "available": True,
                "value_usd": float(value),
                "year": 2024,
                "source": "Banque Mondiale WDI 2024 (module Profils Pays)",
            }
    except Exception as exc:  # pragma: no cover - defensive
        _log.warning("country-profiles GDP unavailable: %s", exc)
    return None


def _gdp_values_map() -> Dict[str, float]:
    """Carte {iso3: PIB/hab} depuis la meilleure source disponible : dataset ETL
    s'il est présent, sinon module Profils Pays (54 pays, embarqué). Utilisée pour
    la moyenne continentale de l'ajustement L3 — sans dépendance réseau."""
    data = _load_gdp()
    if data:
        return {k: r["value"] for k, r in data.items() if r.get("value") is not None}
    try:
        from country_data import REAL_COUNTRY_DATA

        return {
            k: float(v["gdp_per_capita_2024"])
            for k, v in REAL_COUNTRY_DATA.items()
            if v.get("gdp_per_capita_2024") is not None
        }
    except Exception as exc:  # pragma: no cover - defensive
        _log.warning("country-profiles GDP map unavailable: %s", exc)
        return {}


def get_gdp_per_capita(country_iso3: str) -> Dict:
    """GDP per capita (USD). Source primaire : le module Profils Pays (déjà
    embarqué, 54 pays, WDI 2024) ; le dataset ETL ``wb_gdp_pc.json`` prend le
    dessus s'il est présent (données potentiellement plus récentes). Gracieux."""
    # Dataset ETL prioritaire s'il a été produit (potentiellement plus récent).
    data = _load_gdp()
    rec = data.get((country_iso3 or "").upper())
    if rec and rec.get("value") is not None:
        return {
            "available": True,
            "value_usd": rec["value"],
            "year": rec.get("year"),
            "source": "World Bank WDI NY.GDP.PCAP.CD",
        }
    # Repli (défaut) : module Profils Pays — aucune dépendance réseau.
    from_profiles = _gdp_from_country_profiles(country_iso3)
    if from_profiles:
        return from_profiles
    return {
        "available": False,
        "value_usd": None,
        "note": "PIB/habitant indisponible pour ce pays.",
    }


def _apparent_consumption(apparent: Optional[Dict]) -> Optional[float]:
    """Production + Imports − Exports, only if all three legs are present."""
    if not apparent:
        return None
    p, m, x = apparent.get("production"), apparent.get("imports"), apparent.get("exports")
    if p is None or m is None or x is None:
        return None
    return float(p) + float(m) - float(x)


def _weighted_regional_gdp_avg(
    gdp_map: Dict[str, float], idx: Dict[str, Dict], region: str
) -> Optional[float]:
    """PIB/habitant moyen pondéré par la population, restreint à une SOUS-RÉGION
    (cohérent avec une référence per-capita L2 elle-même régionale)."""
    total_gdp, total_pop = 0.0, 0
    for iso3, gdp_pc in gdp_map.items():
        rec = idx.get(iso3) or {}
        if rec.get("region") != region:
            continue
        pop = rec.get("population")
        if gdp_pc and pop:
            total_gdp += float(gdp_pc) * int(pop)
            total_pop += int(pop)
    return (total_gdp / total_pop) if total_pop else None


def _weighted_continental_gdp_avg(
    gdp_map: Dict[str, float], idx: Dict[str, Dict]
) -> Optional[float]:
    """
    PIB/habitant continental moyen PONDÉRÉ PAR LA POPULATION.

    La référence par habitant du proxy L2 est un agrégat continental
    (production ÷ population totale) ; pour que la somme des besoins estimés
    par pays reste cohérente avec la disponibilité continentale, le facteur L3
    doit être normalisé par la même grandeur : PIB continental ÷ population
    continentale. La moyenne SIMPLE des PIB/hab nationaux (ancien calcul) est
    tirée vers le haut par les petits pays riches (Seychelles, Maurice,
    Gabon...) et écrase donc systématiquement le facteur des grands pays
    peuplés à faible revenu (Éthiopie, RDC...).
    """
    total_gdp, total_pop = 0.0, 0
    for iso3, gdp_pc in gdp_map.items():
        pop = (idx.get(iso3) or {}).get("population")
        if gdp_pc and pop:
            total_gdp += float(gdp_pc) * int(pop)
            total_pop += int(pop)
    return (total_gdp / total_pop) if total_pop else None


def _observed_imports_floor(
    modelled: float, unit: Optional[str], hs_code: str, observed_imports: Optional[Dict]
) -> Optional[Dict]:
    """
    Recalage sur les importations observées (flux réel, USD/an) : le besoin
    national d'un produit est AU MOINS ce que le pays en importe déjà — un
    proxy population qui tombe en dessous est démenti par un flux mesuré.
    Plancher uniquement (jamais de plafond : la production locale s'ajoute aux
    importations). Conversion USD → unité physique via l'indice valeur/poids
    quand nécessaire, signalée comme estimation.
    """
    annual_usd = (observed_imports or {}).get("import_value_usd")
    if not annual_usd or annual_usd <= 0:
        return None
    if (unit or "").upper() == "USD":
        floor_value, conversion = float(annual_usd), None
    else:
        try:
            from services.shipment_estimator import usd_per_kg_for_hs

            ratio = usd_per_kg_for_hs(hs_code)
            usd_per_kg = ratio.get("usd_per_kg") or 0
            if usd_per_kg <= 0 or "tonne" not in (unit or "").lower():
                return None
            floor_value = float(annual_usd) / usd_per_kg / 1000.0  # tonnes
            conversion = {
                "usd_per_kg": usd_per_kg,
                "is_estimate": ratio.get("is_estimate", True),
                "source": ratio.get("source"),
            }
        except Exception as exc:  # pragma: no cover - defensive
            _log.warning("observed-imports conversion unavailable: %s", exc)
            return None
    if floor_value <= modelled:
        return None
    return {
        "applied": True,
        "floor_value": floor_value,
        "modelled_value_before_floor": modelled,
        "conversion": conversion,
        "note": (
            "Proxy population recalé au plancher des importations observées "
            f"({observed_imports.get('source', 'OEC')}, {observed_imports.get('year', '—')}) : "
            "le pays importe déjà davantage que l'estimation modélisée."
        ),
    }


def estimate_national_need(
    hs_code: str,
    country_iso3: str,
    apparent: Optional[Dict] = None,
    income_elasticity: Optional[float] = None,
    observed_imports: Optional[Dict] = None,
    continental_imports_tonnes: Optional[float] = None,
    own_imports_history: Optional[list] = None,
) -> Dict:
    """
    Estimate a country's national need for a product via the transparent cascade.

    ``apparent`` (optional): {"production": .., "imports": .., "exports": ..} in
    the product's native unit — enables the measured L1 apparent-consumption path
    (need = production + imports − exports).

    ``observed_imports`` (optional): {"import_value_usd": .., "source": ..} — the
    country's own imports of the product (USD, from OEC). A direct monetary signal
    of need, attached to the result as complementary evidence (kept separate from
    the physical estimate because units differ).

    ``continental_imports_tonnes`` (optional): continental imports in the product's
    physical unit. When provided, the L2 per-capita reference is based on apparent
    continental availability (production + imports) instead of production alone.

    ``own_imports_history`` (optional): ``[{"year": .., "import_value_usd": ..,
    "no_data": bool}, ...]`` — the COUNTRY's own multi-year import history for this
    SH code (OEC/BACI). Used ONLY when continental production has no reference at
    all (no FAO/USGS/UNIDO mapping for this SH, e.g. medical instruments SH90) —
    the cascade then falls back to the country's own real imports instead of
    returning ``available: False``. See :func:`estimate_need_from_own_imports`
    for the durable-goods multi-year averaging rule.

    Returns a fully self-describing block (value, unit, level, method, inputs,
    sources, is_estimation, observed_imports, reference_basis).
    """
    country_iso3 = (country_iso3 or "").upper()

    # Élasticité-revenu : résolue par classe de produit (chapitre SH) sauf
    # surcharge explicite de l'appelant — 0,4 pour tout (des céréales aux
    # téléviseurs) était une simplification excessive.
    if income_elasticity is None:
        elasticity_info = income_elasticity_for_hs(hs_code)
        income_elasticity = elasticity_info["value"]
        elasticity_class = elasticity_info["product_class"]
    else:
        elasticity_class = "surcharge appelant"

    # ── L1: measured apparent consumption (Production + Imports − Exports) ────
    app = _apparent_consumption(apparent)
    if app is not None:
        return {
            "available": True,
            "is_estimation": False,
            "estimation_level": 1,
            "level_label": "Consommation apparente (mesurée)",
            "value": round(app, 2),
            "unit": (apparent or {}).get("unit"),
            "implied_per_capita": _implied_per_capita(
                app, (apparent or {}).get("unit"), get_population(country_iso3).get("value")
            ),
            "method": "Production + Importations − Exportations",
            "inputs": {
                "production": apparent.get("production"),
                "imports": apparent.get("imports"),
                "exports": apparent.get("exports"),
            },
            "sources": [(apparent or {}).get("source", "production + trade")],
            "observed_imports": observed_imports if observed_imports else None,
        }

    # Need production (for the per-capita reference) and population.
    try:
        from services.production_capacity_service import get_continental_producers

        prod = get_continental_producers(hs_code)
    except Exception as exc:
        _log.warning("continental producers unavailable: %s", exc)
        prod = {"available": False}

    pop = get_population(country_iso3)
    idx = _country_index()

    cont_total = prod.get("continental_total") if prod.get("available") else None

    # Aucune référence de production continentale (pas de mapping HS -> commodité
    # FAO/USGS/UNIDO, ex. instruments médicaux SH90) : plutôt que d'abandonner,
    # replier sur les importations réelles du pays lui-même pour ce SH — un
    # signal mesuré, pas un proxy inventé. Moyenné sur plusieurs années pour les
    # biens durables/longue conservation (voir estimate_need_from_own_imports).
    if not cont_total and own_imports_history:
        own_imports_estimate = estimate_need_from_own_imports(
            hs_code, country_iso3, own_imports_history
        )
        if own_imports_estimate:
            return own_imports_estimate

    if not cont_total or not pop.get("available") or not idx:
        return {
            "available": False,
            "is_estimation": True,
            "value": None,
            "reason": (
                "no_continental_production_reference"
                if not cont_total
                else "population_unavailable"
            ),
            "note": (
                "Estimation impossible : "
                + (
                    "production continentale indisponible."
                    if not cont_total
                    else "population indisponible."
                )
            ),
        }

    cont_pop = _continental_population(idx)

    # ── Référence RÉGIONALE (priorité) ──────────────────────────────────────
    # Une moyenne per-capita CONTINENTALE mélange des régimes alimentaires très
    # différents (blé/thé dominants en Afrique du Nord, riz/manioc en Afrique
    # de l'Ouest...) — vérifié empiriquement : le proxy continental sous-estime
    # le besoin en blé de 5-6x pour l'Algérie/l'Égypte et surestime le thé
    # marocain de 2x, alors qu'une référence par sous-région (même échantillon
    # de pays partageant un profil de consommation proche) réduit ces écarts.
    # Repli sur le continental si la région manque de couverture (< 2 pays
    # producteurs de données) pour éviter qu'une "référence régionale" ne soit
    # en réalité l'auto-production du seul pays évalué divisée par la
    # population régionale — un artefact, pas une estimation.
    region = pop.get("region")
    region_availability = None
    region_pop = None
    region_coverage = None
    reg = {"available": False}
    if region:
        region_iso3_set = {iso for iso, rec in idx.items() if rec.get("region") == region}
        try:
            from services.production_capacity_service import get_regional_producers

            reg = get_regional_producers(hs_code, region_iso3_set)
        except Exception as exc:
            _log.warning("regional producers unavailable: %s", exc)
            reg = {"available": False}
        region_pop = sum(
            int((idx.get(iso) or {}).get("population") or 0) for iso in region_iso3_set
        )
        producer_count = reg.get("producer_count") or 0
        region_coverage = {
            "region": region,
            "countries_in_region": len(region_iso3_set),
            "producers_with_data": producer_count,
        }
        if reg.get("available") and reg.get("region_total") and region_pop and producer_count >= 2:
            region_availability = reg["region_total"]

    regional_available = region_availability is not None

    # Reference availability per capita: production, enriched with continental
    # imports when a same-unit (physical) figure is provided — so import-dependent
    # products (low local production) are not under-estimated. Un signal explicite
    # de l'appelant (imports continentaux réels) prime sur l'heuristique régionale
    # automatique — c'est un raffinement délibéré, pas une approximation.
    if continental_imports_tonnes and continental_imports_tonnes > 0:
        cont_availability = cont_total + continental_imports_tonnes
        ref_pop = cont_pop
        reference_basis = "production_plus_imports"
    elif regional_available:
        cont_availability = region_availability
        ref_pop = region_pop
        reference_basis = "regional_production_only"
    else:
        cont_availability = cont_total
        ref_pop = cont_pop
        reference_basis = "production_only"

    # ``regional_used`` reflète la décision EFFECTIVE (après arbitrage avec un
    # éventuel signal explicite de l'appelant), pas seulement la disponibilité
    # régionale — sinon un appel avec ``continental_imports_tonnes`` explicite
    # se retrouverait étiqueté "géographie régionale" à tort.
    regional_used = reference_basis == "regional_production_only"

    per_capita_ref = cont_availability / ref_pop if ref_pop else None
    if not per_capita_ref:
        return {
            "available": False,
            "is_estimation": True,
            "value": None,
            "reason": "continental_population_unavailable",
            "note": "Population continentale indisponible.",
        }

    # ── L2: population proxy ─────────────────────────────────────────────────
    need_l2 = pop["value"] * per_capita_ref
    level = 2
    level_label = "Proxy population (estimé)"
    if reference_basis == "regional_production_only":
        method = (
            f"Population × (production régionale [{region}] ÷ population régionale) "
            "[disponibilité apparente par habitant — référence régionale, hors importations]"
        )
    elif reference_basis == "production_plus_imports":
        method = (
            "Population × ((production + importations continentales) "
            "÷ population continentale) [disponibilité apparente par habitant]"
        )
    else:
        method = (
            "Population × (production continentale ÷ population continentale) "
            "[disponibilité apparente par habitant — hors importations, borne basse]"
        )
    gdp_factor = None

    # ── L3: standard-of-living adjustment ────────────────────────────────────
    # PIB/hab du pays ET moyenne de référence depuis la meilleure source (dataset
    # ETL prioritaire, sinon module Profils Pays) — L3 s'active sans réseau.
    # Moyenne PONDÉRÉE PAR LA POPULATION, restreinte à la RÉGION quand la
    # référence L2 est elle-même régionale (cohérence : on compare la richesse
    # du pays à ses pairs régionaux, pas à l'ensemble du continent — sinon
    # l'ajustement niveau de vie recolle artificiellement l'écart régional que
    # la régionalisation du L2 visait justement à corriger). Repli continental
    # si la moyenne régionale est indisponible (région trop petite/pauvre en
    # données PIB).
    gdp = get_gdp_per_capita(country_iso3)
    gdp_map = _gdp_values_map()
    if gdp.get("available") and gdp_map:
        gdp_avg = _weighted_regional_gdp_avg(gdp_map, idx, region) if regional_used else None
        gdp_avg_is_regional = gdp_avg is not None
        if gdp_avg is None:
            gdp_avg = _weighted_continental_gdp_avg(gdp_map, idx)
        if gdp_avg:
            gdp_factor = (gdp["value_usd"] / gdp_avg) ** income_elasticity
            need = need_l2 * gdp_factor
            level = 3
            level_label = "Proxy population + ajustement niveau de vie (estimé)"
            method += (
                f" × (PIB/hab_pays ÷ PIB/hab_moyen_{'régional' if gdp_avg_is_regional else 'continental'})"
                f"^{income_elasticity}"
            )
        else:
            need = need_l2
    else:
        need = need_l2

    sources = [
        prod.get("source", "production_capacity_service (FAO/USGS/UNIDO)"),
        _POP_SOURCE,
    ]
    if reference_basis == "production_plus_imports":
        sources.append("OEC / UN Comtrade (BACI) — importations continentales")
    if level == 3:
        sources.append(gdp.get("source", "World Bank WDI NY.GDP.PCAP.CD"))

    if reference_basis == "regional_production_only":
        basis_note = (
            f"Référence basée sur la production de la sous-région « {region} » "
            f"({region_coverage['producers_with_data']}/{region_coverage['countries_in_region']} "
            "pays avec données de production), rapportée à la population régionale — "
            "capte le profil de consommation régional (ex. blé/thé en Afrique du Nord, "
            "riz/manioc en Afrique de l'Ouest) mieux qu'une moyenne panafricaine unique. "
            "Hors importations : reste une borne basse pour les produits fortement importés."
        )
    elif reference_basis == "production_only":
        basis_note = (
            "Référence basée sur la production continentale seule (hors importations) : "
            "borne basse pour les produits fortement importés. Fournir les importations "
            "continentales (tonnes) affine l'estimation."
        )
    else:
        basis_note = "Référence basée sur la disponibilité apparente (production + importations)."

    # Portée de la référence : une correspondance au chapitre SH2 signifie que
    # la production de référence couvre tout un SECTEUR (ex. « Manufacture of
    # chemicals » pour le savon SH 340111) — le besoin estimé porte alors sur ce
    # secteur, pas sur le seul produit demandé. Sans cette mention, un besoin
    # sectoriel de plusieurs Md$ passe pour le besoin du produit SH6.
    match_level = prod.get("match_level") or ""
    scope_is_sector = match_level.startswith("HS2")
    scope_note = None
    if scope_is_sector:
        scope_note = (
            f"ATTENTION PORTÉE : correspondance production au chapitre SH2 — la valeur "
            f"estime le besoin de l'ensemble du secteur « {prod.get('commodity')} », "
            f"pas du seul produit SH {hs_code}. À lire comme un plafond sectoriel."
        )

    # Caveat de couverture de la donnée de référence (ex. UNIDO ingéré pour
    # 1-2 pays africains seulement) : la disponibilité continentale est alors
    # sous-estimée et l'estimation peu fiable — propagé, plus jamais silencieux.
    coverage_caveat = prod.get("coverage_caveat")

    # Recalage sur flux réel : les importations observées du pays sont un
    # plancher mesuré du besoin.
    calibration = _observed_imports_floor(need, prod.get("unit"), hs_code, observed_imports)
    if calibration:
        need = calibration["floor_value"]
        method += " ; recalé au plancher des importations observées (flux réel OEC)"
        sources.append(
            (observed_imports or {}).get("source", "OEC / UN Comtrade (BACI)")
            + " — importations observées du pays"
        )

    # Suggested supplier: the #1 African producer that isn't the market itself —
    # a natural "who could serve this need" hand-off to the bilateral report.
    suggested_supplier = None
    for p in prod.get("top_producers", []):
        iso = (p.get("country_iso3") or "").upper()
        if iso and iso != country_iso3:
            suggested_supplier = {"iso3": iso, "country_name": p.get("country_name")}
            break

    note = (
        "Estimation transparente : valeur modélisée, non mesurée. "
        + basis_note
        + " Affiner via consommation apparente réelle (production + import − export) "
        "dès que les flux commerciaux du pays sont disponibles."
    )
    if scope_note:
        note = scope_note + " " + note
    if coverage_caveat:
        note += " COUVERTURE PARTIELLE de la référence : " + coverage_caveat
    if calibration:
        note += " " + calibration["note"]

    return {
        "available": True,
        "is_estimation": True,
        "estimation_level": level,
        "level_label": level_label,
        # Arrondi à 3 chiffres significatifs : une estimation au centime près
        # revendiquerait une précision qu'elle n'a pas.
        "value": _round_sig(need, 3),
        "unit": prod.get("unit"),
        # Besoin ramené par habitant — contrôle de vraisemblance immédiat d'un
        # total brut qui, sans dénominateur, peut paraître aberrant (ex.
        # « 581 000 t » de bananes pour l'Algérie = ≈13 kg/hab/an, plausible).
        "implied_per_capita": _implied_per_capita(need, prod.get("unit"), pop.get("value")),
        "commodity": prod.get("commodity"),
        "reference_year": prod.get("year"),
        "reference_basis": reference_basis,
        "reference_geography": "régionale" if regional_used else "continentale",
        "region_coverage": region_coverage,
        "reference_scope": "secteur (chapitre SH2)" if scope_is_sector else "produit",
        "reference_coverage_caveat": coverage_caveat,
        "calibration": calibration,
        "suggested_supplier": suggested_supplier,
        "method": method,
        "inputs": {
            "population": pop["value"],
            "region": pop.get("region"),
            "continental_production": cont_total,
            "continental_imports_tonnes": continental_imports_tonnes,
            "continental_population": cont_pop,
            "regional_production": region_availability if regional_used else None,
            "regional_population": region_pop if regional_used else None,
            "per_capita_reference": round(per_capita_ref, 6),
            "gdp_adjustment_factor": round(gdp_factor, 3) if gdp_factor else None,
            "income_elasticity": income_elasticity if level == 3 else None,
            "income_elasticity_class": elasticity_class if level == 3 else None,
        },
        "sources": sources,
        # The country's own observed imports (USD) — a direct demand signal that
        # complements the physical estimate (different unit, shown separately).
        "observed_imports": observed_imports if observed_imports else None,
        "note": note,
    }
