"""
AfCFTA Platform - Dashboard Visualization Engine
=================================================
Generates chart-ready datasets and heatmap data for the regional analytics
dashboard. All data is structured for direct consumption by Chart.js or
similar frontend visualization libraries.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class VisualizationEngine:
    """
    Transforms raw analytics data into chart-ready datasets.

    Supported visualizations:
    - Radar charts (country comparison)
    - Bar charts (regional metric comparison)
    - Heatmaps (investment score by country/bloc)
    - Sankey diagrams (trade flow corridors)
    - Line charts (trend analysis)
    """

    # Colour palette for regional blocs
    BLOC_COLORS: Dict[str, str] = {
        "ECOWAS": "#F59E0B",
        "CEMAC":  "#EF4444",
        "EAC":    "#10B981",
        "SADC":   "#3B82F6",
        "UMA":    "#8B5CF6",
        "COMESA": "#EC4899",
        "IGAD":   "#6366F1",
    }

    def radar_chart_data(
        self,
        countries: List[str],
        sector: str = "general",
    ) -> Dict[str, Any]:
        """
        Build Chart.js radar dataset for multi-country comparison.
        Dimensions: market_access, investment_climate, infrastructure,
                    incentives, market_potential, cost_competitiveness
        """
        from intelligence.ai_engine.investment_scoring import (
            get_intelligence_engine,
            SCORING_ALGORITHM,
        )
        engine = get_intelligence_engine()
        dimensions = list(SCORING_ALGORITHM.keys())
        labels = [d.replace("_", " ").title() for d in dimensions]

        datasets = []
        for country in countries:
            score = engine.calculate_investment_score(country, sector)
            values = [c.raw_score for c in score.component_scores]
            color = self._country_color(country)
            datasets.append({
                "label": country,
                "data": [round(v * 100, 1) for v in values],
                "backgroundColor": color + "33",
                "borderColor": color,
                "pointBackgroundColor": color,
                "borderWidth": 2,
            })

        return {
            "type": "radar",
            "data": {"labels": labels, "datasets": datasets},
            "options": {
                "scales": {
                    "r": {
                        "min": 0,
                        "max": 100,
                        "ticks": {"stepSize": 20},
                    }
                },
                "plugins": {
                    "title": {
                        "display": True,
                        "text": f"Country Comparison – {sector.title()} Sector",
                    }
                },
            },
        }

    def bar_chart_data(
        self,
        blocs: Optional[List[str]] = None,
        metric: str = "investment_score",
    ) -> Dict[str, Any]:
        """Build a Chart.js bar dataset for regional bloc comparison."""
        from intelligence.analytics.regional_analytics import (
            get_regional_analytics,
            REGIONAL_BENCHMARKS,
        )
        analytics = get_regional_analytics()
        if blocs is None:
            blocs = analytics.get_all_blocs()

        labels = []
        values = []
        colors = []

        for bloc in blocs:
            benchmarks = REGIONAL_BENCHMARKS.get(bloc, {})
            value = benchmarks.get(metric, 0)
            labels.append(bloc)
            values.append(round(value * 100 if metric == "investment_score" else value, 1))
            colors.append(self.BLOC_COLORS.get(bloc, "#94A3B8"))

        metric_label = metric.replace("_", " ").title()
        return {
            "type": "bar",
            "data": {
                "labels": labels,
                "datasets": [{
                    "label": metric_label,
                    "data": values,
                    "backgroundColor": colors,
                    "borderRadius": 6,
                }],
            },
            "options": {
                "plugins": {
                    "title": {"display": True, "text": f"Regional {metric_label}"}
                },
                "scales": {"y": {"beginAtZero": True}},
            },
        }

    def heatmap_data(self) -> Dict[str, Any]:
        """
        Generate investment opportunity heatmap data.
        Returns a structure suitable for choropleth / tile-based heatmaps.
        """
        from intelligence.ai_engine.investment_scoring import (
            get_intelligence_engine,
            COUNTRY_INDICATORS,
        )
        engine = get_intelligence_engine()
        heatmap = []
        for country in COUNTRY_INDICATORS:
            score = engine.calculate_investment_score(country)
            heatmap.append({
                "country": country,
                "score": score.overall_score,
                "grade": score.grade,
                "color": self._score_color(score.overall_score),
                "tooltip": (
                    f"{country}: {score.overall_score:.0%} ({score.grade}) — "
                    f"{score.recommendation_strength.replace('_', ' ')}"
                ),
            })
        heatmap.sort(key=lambda x: x["score"], reverse=True)
        return {
            "type": "heatmap",
            "entries": heatmap,
            "legend": [
                {"label": "Excellent (80%+)", "color": "#10B981"},
                {"label": "Good (64-80%)",    "color": "#3B82F6"},
                {"label": "Fair (50-64%)",    "color": "#F59E0B"},
                {"label": "Poor (<50%)",      "color": "#EF4444"},
            ],
        }

    def sankey_data(self) -> Dict[str, Any]:
        """
        Build a Sankey diagram dataset for trade corridor visualization.
        Compatible with Chart.js sankey plugin or D3.
        """
        from intelligence.analytics.regional_analytics import get_regional_analytics
        corridors = get_regional_analytics().get_trade_corridor_analysis()

        nodes: Dict[str, int] = {}
        links = []

        for corridor in corridors:
            for bloc in (corridor["origin"], corridor["destination"]):
                if bloc not in nodes:
                    nodes[bloc] = len(nodes)

            links.append({
                "source": nodes[corridor["origin"]],
                "target": nodes[corridor["destination"]],
                "value": corridor.get("trade_value_bn", 1),
                "label": ", ".join(corridor.get("key_products", [])[:2]),
            })

        return {
            "type": "sankey",
            "nodes": [{"id": idx, "label": bloc} for bloc, idx in nodes.items()],
            "links": links,
        }

    def line_chart_trend(
        self,
        country: str,
        metric: str = "investment_score",
        years: int = 5,
    ) -> Dict[str, Any]:
        """
        Generate a trend line chart (simulated historical data).
        In production this queries the time-series database.
        """
        from intelligence.ai_engine.investment_scoring import get_intelligence_engine
        engine = get_intelligence_engine()
        current_score = engine.calculate_investment_score(country).overall_score

        # Simulate historical data with slight variation
        import random
        random.seed(hash(country + metric))
        current_year = 2024
        history = []
        for i in range(years, 0, -1):
            year = current_year - i
            variation = random.uniform(-0.05, 0.05)
            history.append({
                "year": year,
                "value": round(max(0, min(1, current_score + variation - 0.01 * i)) * 100, 1),
            })
        history.append({"year": current_year, "value": round(current_score * 100, 1)})

        labels = [str(h["year"]) for h in history]
        values = [h["value"] for h in history]
        color = self._country_color(country)

        return {
            "type": "line",
            "data": {
                "labels": labels,
                "datasets": [{
                    "label": f"{country} – {metric.replace('_', ' ').title()}",
                    "data": values,
                    "borderColor": color,
                    "backgroundColor": color + "22",
                    "fill": True,
                    "tension": 0.4,
                }],
            },
            "options": {
                "scales": {"y": {"min": 0, "max": 100, "title": {"display": True, "text": "%"}}},
                "plugins": {"title": {"display": True, "text": f"{country} Trend Analysis"}},
            },
        }

    # ------------------------------------------------------------------
    # Internal colour helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _score_color(score: float) -> str:
        if score >= 0.80:
            return "#10B981"
        if score >= 0.64:
            return "#3B82F6"
        if score >= 0.50:
            return "#F59E0B"
        return "#EF4444"

    @staticmethod
    def _country_color(country: str) -> str:
        palette = [
            "#3B82F6", "#10B981", "#F59E0B", "#EF4444",
            "#8B5CF6", "#EC4899", "#6366F1", "#14B8A6",
        ]
        return palette[hash(country) % len(palette)]


# Singleton
_viz: Optional[VisualizationEngine] = None


def get_visualization_engine() -> VisualizationEngine:
    global _viz
    if _viz is None:
        _viz = VisualizationEngine()
    return _viz
