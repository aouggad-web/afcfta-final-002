"""
SACU Customs Union Framework
=============================
Provides the SACU (Southern African Customs Union) common framework data
and helper functions.  The SACU CET (Common External Tariff) is anchored to
South Africa's SARS Schedule 1 and applies identically across the five member
states: ZAF, BWA, NAM, LSO, SWZ.

Revenue sharing, institution overview, and helper utilities are included here
so that other services can import a single source of truth.
"""

import json
import logging
import os
from datetime import datetime
from typing import Dict, List, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data", "crawled")

# ---------------------------------------------------------------------------
# SACU framework constants
# ---------------------------------------------------------------------------

SACU_FRAMEWORK = {
    "name": "Southern African Customs Union",
    "abbreviation": "SACU",
    "founded": 1910,
    "current_agreement": 2002,
    "secretariat": "Windhoek, Namibia",
    "website": "https://www.sacu.int",
    "members": ["ZAF", "BWA", "NAM", "LSO", "SWZ"],
    "member_count": 5,
    "common_external_tariff": True,
    "free_internal_trade": True,
    "revenue_sharing": {
        "customs_component": "48% of total SACU customs revenue pool",
        "excise_component": "23% of total SACU excise revenue pool",
        "development_component": "15% of customs revenue for BLNS countries (BWA, LSO, NAM, SWZ)",
        "distribution_formula": "Based on intra-SACU trade flows, GDP shares, and development status",
        "note": (
            "BLNS countries receive a development component that compensates for the "
            "trade-diversion cost of the common external tariff and the dominance "
            "of South African producers in the SACU market."
        ),
    },
    "harmonised_policies": [
        "customs_procedures",
        "trade_facilitation",
        "rules_of_origin",
        "industrial_development",
        "agricultural_policy_coordination",
    ],
    "institutions": {
        "council_of_ministers": {
            "role": "Supreme policy body – ministers responsible for trade/finance",
            "decisions": "Consensus",
        },
        "customs_union_commission": {
            "role": "Technical coordination and implementation",
            "composition": "One senior official per member state",
        },
        "tariff_board": {
            "role": "Independent body – recommends tariff adjustments to Council",
            "note": "Replaced former South African Board of Tariffs and Trade",
        },
        "tribunal": {
            "role": "Dispute resolution among member states",
        },
        "secretariat": {
            "location": "Windhoek, Namibia",
            "role": "Administrative and support functions",
        },
    },
}

# ---------------------------------------------------------------------------
# Member-state revenue share estimates (illustrative)
# ---------------------------------------------------------------------------

SACU_REVENUE_SHARES = {
    "ZAF": {
        "customs_share_pct": 55.0,
        "excise_share_pct": 70.0,
        "development_share_pct": 0.0,
        "note": "South Africa as largest economy retains majority but funds development component",
    },
    "BWA": {
        "customs_share_pct": 19.0,
        "excise_share_pct": 10.5,
        "development_share_pct": 5.0,
        "note": "Diamond economy; SACU revenues historically >30% of government revenue",
    },
    "NAM": {
        "customs_share_pct": 13.0,
        "excise_share_pct": 8.0,
        "development_share_pct": 4.5,
        "note": "SACU revenues ~25% of government revenue",
    },
    "LSO": {
        "customs_share_pct": 7.0,
        "excise_share_pct": 6.0,
        "development_share_pct": 3.5,
        "note": "SACU revenues historically >50% of government revenue – high fiscal dependency",
    },
    "SWZ": {
        "customs_share_pct": 6.0,
        "excise_share_pct": 5.5,
        "development_share_pct": 2.0,
        "note": "SACU revenues >50% of government revenue",
    },
}

# ---------------------------------------------------------------------------
# Common External Tariff band mapping
# ---------------------------------------------------------------------------

SACU_CET_BANDS = {
    0.0: "raw_materials_capital_goods",
    5.0: "intermediate_goods",
    15.0: "final_consumer_goods",
    20.0: "agricultural_products",
    22.0: "textiles_and_clothing",
    25.0: "automotive",
    30.0: "luxury_goods",
}

# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------


def generate_sacu_summary() -> Dict:
    """Return a summary of the SACU framework suitable for API responses."""
    return {
        "framework": SACU_FRAMEWORK,
        "revenue_shares": SACU_REVENUE_SHARES,
        "cet_bands": {str(k): v for k, v in SACU_CET_BANDS.items()},
        "generated_at": datetime.utcnow().isoformat(),
    }


def run_scraper() -> Dict:
    """
    Save the SACU framework summary to disk.

    Returns the summary dict.
    """
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    summary = generate_sacu_summary()

    output_path = os.path.join(OUTPUT_DIR, "SACU_framework.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    logger.info(f"SACU framework data saved to {output_path}")
    return summary


if __name__ == "__main__":
    run_scraper()
