"""
Benchmarking service for premium Opportunités reports.

Compares origin country's performance vs top African producers, top importers,
infrastructure quality, tariff advantage. All data real, sourced, never
fabricated.

Outputs: Ranking, competitive position, gap analysis, infrastructure score,
tariff benefit.
"""

import logging
from typing import Dict, List, Optional

_log = logging.getLogger(__name__)


def get_top_producers(hs_code: str, n: int = 5) -> Dict:
    """
    Top N continental producers of a product by continental share.

    Returns sorted by production volume desc. Data sourced from
    production_capacity_service (FAO/USGS/UNIDO).

    Returns: {
        available: bool,
        producers: [{country_iso3, country_name, continental_share_pct,
                     production_volume, unit, year, rank, source}],
        source: str,
        note: str
    }
    """
    try:
        from services.production_capacity_service import get_continental_producers

        result = get_continental_producers(hs_code)
    except Exception as exc:
        _log.warning("continental producers unavailable: %s", exc)
        return {"available": False, "producers": [], "note": str(exc)}

    if not result.get("available"):
        return {
            "available": False,
            "producers": [],
            "note": result.get("reason", "No production data for this product"),
        }

    top_prods = result.get("top_producers", [])
    producers = [
        {
            "rank": i + 1,
            "country_iso3": p.get("country_iso3"),
            "country_name": p.get("country_name"),
            # production_capacity_service returns share_pct / value; keep fallbacks
            # for the mocked/alternate key names.
            "continental_share_pct": p.get("share_pct", p.get("country_share_pct")),
            "production_volume": p.get("value", p.get("production_value")),
            "unit": result.get("unit"),
            "year": result.get("year"),
            "source": result.get("source"),
        }
        for i, p in enumerate(top_prods[:n])
    ]

    return {
        "available": True,
        "producers": producers,
        "total": len(top_prods),
        "source": result.get("source", "production_capacity_service"),
        "year": result.get("year"),
    }


def benchmark_cost(
    origin_iso3: str,
    hs_code: str,
    destination_iso3: str,
    landed_cost_usd: Optional[float],
) -> Dict:
    """
    Compares landed cost vs top African producers to same destination.

    Uses historical pricing (implicit in production capacity data) + estimated
    freight to destination. Provides position (best/competitive/higher_cost) and gap %.

    Returns: {
        available: bool,
        reference_producer: {iso3, cost_estimate_usd, rank, share_pct},
        position: "best" | "competitive" | "higher_cost",
        gap_pct: float,
        narrative: str,
        note: str
    }
    """
    if not landed_cost_usd:
        return {
            "available": False,
            "note": "Landed cost not provided; cost benchmark unavailable",
        }

    # Fetch top producers
    top = get_top_producers(hs_code, n=5)
    if not top.get("available") or not top.get("producers"):
        return {
            "available": False,
            "note": "Cannot benchmark cost without top producers reference",
        }

    # Cost comparison: if origin is the top producer, position is "best" (real data).
    # Otherwise, we estimate the gap via heuristic (~8% cheaper for leader) — mark as estimation.
    best_producer = top["producers"][0]
    origin_is_leader = origin_iso3.upper() == best_producer.get("country_iso3", "").upper()

    if origin_is_leader:
        position = "best"
        narrative = f"{origin_iso3.upper()} est le producteur le moins cher (position de leader)"
        return {
            "available": True,
            "reference_producer": {
                "iso3": best_producer.get("country_iso3"),
                "country_name": best_producer.get("country_name"),
                "continental_share_pct": best_producer.get("continental_share_pct"),
                "rank": best_producer.get("rank"),
            },
            "position": position,
            "gap_pct": 0.0,
            "origin_cost_est": landed_cost_usd,
            "reference_cost_est": landed_cost_usd,
            "narrative": narrative,
            "source": top.get("source"),
            "year": top.get("year"),
        }

    # Non-leader: we do NOT hold real per-producer cost data, so a numeric gap
    # would be fabricated. Report the qualitative position only (origin is not the
    # top producer) and mark the numeric comparison unavailable — no invented cost.
    return {
        "available": False,
        "position": "not_leader",
        "reference_producer": {
            "iso3": best_producer.get("country_iso3"),
            "country_name": best_producer.get("country_name"),
            "continental_share_pct": best_producer.get("continental_share_pct"),
            "rank": best_producer.get("rank"),
        },
        "gap_pct": None,
        "narrative": (
            f"{origin_iso3.upper()} n'est pas le 1er producteur continental "
            f"({best_producer.get('country_name')} l'est). Comparaison de coût "
            "chiffrée indisponible : la plateforme ne dispose pas des coûts réels "
            "par producteur."
        ),
        "source": top.get("source"),
        "year": top.get("year"),
        "note": "Comparaison de coût chiffrée non disponible (pas de données de coût par producteur).",
    }


def benchmark_infrastructure(destination_iso3: str, lang: str = "fr") -> Dict:
    """
    Compares destination's logistics/banking infrastructure vs regional peers.

    Proxies: port count, free zones, PAPSS coverage, country risk score.

    Returns: {
        available: bool,
        destination_iso3: str,
        regional_peers: [str],
        infrastructure_score: float (0–1),
        papss_coverage: bool,
        free_zones_count: int,
        narrative: str
    }
    """
    # Fetch benchmarks for this destination
    try:
        from services.logistics_opportunity_adapter import get_free_zones
        from services.macro_indicators_service import get_gai

        free_zones = get_free_zones(destination_iso3)
        zones_count = free_zones.get("count", 0)

        # PAPSS coverage: check if destination is in PAPSS network
        # (via banking_system get_payment_systems, not pair-matching which would miss unilateral members)
        try:
            from banking_system import get_payment_systems

            systems = get_payment_systems() or []
            papss = any(
                (s.get("code") or "").upper() == "PAPSS"
                and destination_iso3.upper()
                in [m.upper() for m in (s.get("member_countries") or [])]
                for s in systems
            )
        except Exception:
            papss = False  # Fallback: unavailable

        gai = get_gai(destination_iso3)
        gai_score = gai.get("score") if gai else None
    except Exception as exc:
        _log.warning("infrastructure benchmarking failed: %s", exc)
        return {"available": False, "note": str(exc)}

    # Simple infrastructure score: zones + PAPSS + GAI proxy
    score = 0.0
    if zones_count >= 3:
        score += 0.35
    elif zones_count >= 1:
        score += 0.2
    if papss:
        score += 0.35
    if gai_score and gai_score >= 60:
        score += 0.3

    narrative = f"{destination_iso3.upper()}: "
    components = []
    if zones_count > 0:
        components.append(f"{zones_count} zones franches")
    if papss:
        components.append("PAPSS connecté")
    if gai_score:
        components.append(f"GAI {gai_score:.0f}/100")

    narrative += (
        ", ".join(components) + "." if components else "Infrastructure partiellement documentée."
    )

    return {
        "available": True,
        "destination_iso3": destination_iso3.upper(),
        "infrastructure_score": round(min(score, 1.0), 2),
        "free_zones_count": zones_count,
        "papss_covered": papss,
        "gai_score": round(gai_score, 1) if gai_score else None,
        "narrative": narrative,
        "source": "logistics_data + banking_system + macro_indicators",
    }


def _resolve_hs6(destination_iso3: str, code: str):
    """
    Resolve a product code to an HS6 sub-heading in the destination's schedule.

    Returns ``(hs6, resolved)`` — ``resolved`` is True when a shorter (HS4/HS5)
    input was widened to a real HS6 line found under its prefix, or padded as a
    last resort. Returns ``(None, False)`` for an empty code.
    """
    clean = "".join(ch for ch in (code or "") if ch.isdigit())
    if not clean:
        return None, False
    if len(clean) >= 6:
        return clean[:6], False
    # Find a real HS6 line whose code starts with the given HS4/HS5 prefix.
    try:
        from services.authentic_tariff_service import load_country_tariffs

        data = load_country_tariffs(destination_iso3) or {}
        hs6s = sorted(
            {
                (ln.get("hs6") or "")
                for ln in data.get("tariff_lines", [])
                if (ln.get("hs6") or "").startswith(clean)
            }
            - {""}
        )
        if hs6s:
            return hs6s[0], True
    except Exception:  # pragma: no cover - defensive
        pass
    # Last resort: pad with zeros (may not exist -> caller degrades gracefully).
    return clean.ljust(6, "0"), True


def tariff_benefit_analysis(
    origin_iso3: str,
    destination_iso3: str,
    hs_code: str,
) -> Dict:
    """
    Computes the REAL tariff advantage of the preferential regime applicable to
    the ORIGIN/DESTINATION pair vs the national (MFN) rate.

    The tariff applied is the *destination* (importer) country's duty. The
    national duty rate (``dd_rate``) comes straight from the platform's
    authentic tariff dataset, and the preferential rate goes through the SAME
    regime resolution as the calculator (``resolve_zlecaf_context``): customs
    unions, continental ratification, bilateral activation (Algeria grants
    ZLECAf rates to its active partners only — DGD circular 482/2024 — and
    South Africa to its activated partners). An origin outside those lists
    gets the MFN rate, hence a ZERO advantage — never the generic line rate.

    No fabrication: if the destination has no tariff line for the product, the
    block is returned ``available: False`` — never an invented rate.

    Returns: {
        available, zlecaf_rate_pct (= applied preferential rate),
        national_rate_pct, tariff_advantage_pct, savings_per_1000usd,
        tariff_advantage_index (0-1), trade_regime, trade_regime_note,
        narrative, source
    }
    """
    # Tariff schedules are keyed at HS6. Resolve a shorter (HS4/HS5) code to a real
    # HS6 sub-heading under that prefix (or pad as a last resort) so the lookup
    # succeeds. hs6_resolved flags that the input was widened, for transparency.
    hs6, hs6_resolved = _resolve_hs6(destination_iso3, hs_code)
    if not hs6:
        return {
            "available": False,
            "note": "Code produit invalide pour la recherche tarifaire.",
            "source": "authentic_tariff_service",
        }
    try:
        from services.authentic_tariff_service import get_tariff_line

        line = get_tariff_line(destination_iso3, hs6)
    except Exception as exc:
        _log.warning("tariff benefit analysis unavailable: %s", exc)
        return {"available": False, "note": str(exc)}

    if not line:
        return {
            "available": False,
            "note": (
                f"Aucune ligne tarifaire pour {destination_iso3.upper()}/{hs6} "
                "dans le barème national ; avantage tarifaire non calculable."
            ),
            "source": "authentic_tariff_service",
        }

    national = line.get("dd_rate")
    zlecaf = line.get("zlecaf_rate")
    if national is None:
        return {
            "available": False,
            "note": "Taux de droit de douane national indisponible pour ce produit.",
            "source": "authentic_tariff_service",
        }
    national = float(national)

    # Résolution du régime préférentiel réellement applicable à la paire
    # origine/destination — même source de vérité que le calculateur
    # (activation bilatérale DZA/ZAF, unions douanières, ratification).
    try:
        from services.authentic_tariff_service import resolve_zlecaf_context

        ctx = resolve_zlecaf_context(
            destination_iso3,
            origin_iso3,
            hs6,
            national,
            float(zlecaf) if zlecaf is not None else None,
        )
    except Exception as exc:
        _log.warning("preferential regime resolution failed: %s", exc)
        return {
            "available": False,
            "note": f"Régime préférentiel non résolu ({exc}) ; avantage non calculable.",
            "source": "authentic_tariff_service",
        }

    regime = ctx["trade_regime"]
    applied = ctx["dd_rate_pct"]
    rate_status = ctx.get("zlecaf_rate_calculation_status")
    # OFFER_ONLY/PARTNER_NOTICE_REQUIRED : offre publiée ou domestication sans
    # liste de partenaires vérifiée — jamais assez pour modéliser un avantage
    # tarifaire chiffré, au même titre qu'une absence totale de source.
    if rate_status in ("NOT_AVAILABLE", "OFFER_ONLY", "PARTNER_NOTICE_REQUIRED") or applied is None:
        return {
            "available": False,
            "hs6_used": hs6,
            "hs6_resolved": hs6_resolved,
            "national_rate_pct": national,
            "zlecaf_rate_pct": None,
            "tariff_advantage_pct": None,
            "savings_per_1000usd": None,
            "tariff_advantage_index": None,
            "trade_regime": regime,
            "trade_regime_code": ctx.get("trade_regime_code"),
            "trade_regime_note": ctx.get("trade_regime_note"),
            "note": (
                ctx.get("zlecaf_note")
                or "Taux ZLECAf exact non vérifié pour cette ligne — avantage non calculable."
            ),
            "source": "authentic_tariff_service",
        }
    applied = float(applied)

    advantage = max(national - applied, 0.0)
    savings = (advantage / 100.0) * 1000  # USD saved per 1000 USD CIF
    # Normalised contribution to composite reward (a 20% duty saving -> 1.0).
    advantage_index = round(min(advantage / 20.0, 1.0), 3)

    regime_note = ctx.get("trade_regime_note")
    if regime in ("ZLECAF", "CUSTOMS_UNION"):
        regime_label = "ZLECAf" if regime == "ZLECAF" else "union douanière"
        narrative = (
            f"Avantage tarifaire {regime_label} pour "
            f"{origin_iso3.upper()} → {destination_iso3.upper()} : "
            f"{advantage:.1f} % (droit national {national:.1f} % → {applied:.1f} %), "
            f"soit {savings:.0f} $ économisés par 1 000 $ CIF"
        )
    else:
        narrative = (
            f"Aucun avantage tarifaire pour {origin_iso3.upper()} → "
            f"{destination_iso3.upper()} : "
            + (regime_note or f"taux NPF {national:.1f} % appliqué")
        )

    note = "Tarif indicatif au niveau HS6 ; vérifier la sous-position nationale exacte."
    if hs6_resolved:
        note = f"Code élargi en sous-position HS6 {hs6} pour la recherche tarifaire. " + note

    return {
        "available": True,
        "hs6_used": hs6,
        "hs6_resolved": hs6_resolved,
        "national_rate_pct": national,
        "zlecaf_rate_pct": applied,
        "tariff_advantage_pct": round(advantage, 2),
        "savings_per_1000usd": round(savings, 2),
        "tariff_advantage_index": advantage_index,
        "trade_regime": regime,
        "trade_regime_code": ctx.get("trade_regime_code"),
        "trade_regime_note": regime_note,
        "narrative": narrative,
        "source": line.get("dd_source") or "authentic_tariff_service (barème national + ZLECAf)",
        "note": note,
    }
