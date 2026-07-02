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
  L3 — Standard-of-living adjustment: L2 × (GDP/capita_country ÷ GDP/capita_avg)^ε
       with ε an income-elasticity assumption (exposed in the payload). Applied
       only when GDP-per-capita data is available (World Bank ETL); otherwise the
       result stays at L2.

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


def get_gdp_per_capita(country_iso3: str) -> Dict:
    """GDP per capita (USD) for a country, from the World Bank ETL. Graceful."""
    data = _load_gdp()
    rec = data.get((country_iso3 or "").upper())
    if rec and rec.get("value") is not None:
        return {
            "available": True,
            "value_usd": rec["value"],
            "year": rec.get("year"),
            "source": "World Bank WDI NY.GDP.PCAP.CD",
        }
    return {
        "available": False,
        "value_usd": None,
        "note": (
            "PIB/habitant indisponible (dataset wb_gdp_pc.json absent — "
            "à produire via etl/fetch_wb_gdp sur un environnement réseau)."
        ),
    }


def _apparent_consumption(apparent: Optional[Dict]) -> Optional[float]:
    """Production + Imports − Exports, only if all three legs are present."""
    if not apparent:
        return None
    p, m, x = apparent.get("production"), apparent.get("imports"), apparent.get("exports")
    if p is None or m is None or x is None:
        return None
    return float(p) + float(m) - float(x)


def estimate_national_need(
    hs_code: str,
    country_iso3: str,
    apparent: Optional[Dict] = None,
    income_elasticity: float = DEFAULT_INCOME_ELASTICITY,
    observed_imports: Optional[Dict] = None,
    continental_imports_tonnes: Optional[float] = None,
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

    Returns a fully self-describing block (value, unit, level, method, inputs,
    sources, is_estimation, observed_imports, reference_basis).
    """
    country_iso3 = (country_iso3 or "").upper()

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
    if not cont_total or not pop.get("available") or not idx:
        return {
            "available": False,
            "is_estimation": True,
            "value": None,
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

    # Reference availability per capita: production, enriched with continental
    # imports when a same-unit (physical) figure is provided — so import-dependent
    # products (low local production) are not under-estimated.
    if continental_imports_tonnes and continental_imports_tonnes > 0:
        cont_availability = cont_total + continental_imports_tonnes
        reference_basis = "production_plus_imports"
    else:
        cont_availability = cont_total
        reference_basis = "production_only"

    per_capita_ref = cont_availability / cont_pop if cont_pop else None
    if not per_capita_ref:
        return {
            "available": False,
            "is_estimation": True,
            "value": None,
            "note": "Population continentale indisponible.",
        }

    # ── L2: population proxy ─────────────────────────────────────────────────
    need_l2 = pop["value"] * per_capita_ref
    level = 2
    level_label = "Proxy population (estimé)"
    if reference_basis == "production_plus_imports":
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
    gdp = get_gdp_per_capita(country_iso3)
    gdp_data = _load_gdp()
    if gdp.get("available") and gdp_data:
        vals = [r.get("value") for r in gdp_data.values() if r.get("value")]
        gdp_avg = sum(vals) / len(vals) if vals else None
        if gdp_avg:
            gdp_factor = (gdp["value_usd"] / gdp_avg) ** income_elasticity
            need = need_l2 * gdp_factor
            level = 3
            level_label = "Proxy population + ajustement niveau de vie (estimé)"
            method += f" × (PIB/hab_pays ÷ PIB/hab_moyen)^{income_elasticity}"
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
        sources.append("World Bank WDI NY.GDP.PCAP.CD")

    if reference_basis == "production_only":
        basis_note = (
            "Référence basée sur la production continentale seule (hors importations) : "
            "borne basse pour les produits fortement importés. Fournir les importations "
            "continentales (tonnes) affine l'estimation."
        )
    else:
        basis_note = "Référence basée sur la disponibilité apparente (production + importations)."

    # Suggested supplier: the #1 African producer that isn't the market itself —
    # a natural "who could serve this need" hand-off to the bilateral report.
    suggested_supplier = None
    for p in prod.get("top_producers", []):
        iso = (p.get("country_iso3") or "").upper()
        if iso and iso != country_iso3:
            suggested_supplier = {"iso3": iso, "country_name": p.get("country_name")}
            break

    return {
        "available": True,
        "is_estimation": True,
        "estimation_level": level,
        "level_label": level_label,
        "value": round(need, 2),
        "unit": prod.get("unit"),
        "commodity": prod.get("commodity"),
        "reference_year": prod.get("year"),
        "reference_basis": reference_basis,
        "suggested_supplier": suggested_supplier,
        "method": method,
        "inputs": {
            "population": pop["value"],
            "region": pop.get("region"),
            "continental_production": cont_total,
            "continental_imports_tonnes": continental_imports_tonnes,
            "continental_population": cont_pop,
            "per_capita_reference": round(per_capita_ref, 6),
            "gdp_adjustment_factor": round(gdp_factor, 3) if gdp_factor else None,
            "income_elasticity": income_elasticity if level == 3 else None,
        },
        "sources": sources,
        # The country's own observed imports (USD) — a direct demand signal that
        # complements the physical estimate (different unit, shown separately).
        "observed_imports": observed_imports if observed_imports else None,
        "note": (
            "Estimation transparente : valeur modélisée, non mesurée. "
            + basis_note
            + " Affiner via consommation apparente réelle (production + import − export) "
            "dès que les flux commerciaux du pays sont disponibles."
        ),
    }
