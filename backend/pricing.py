"""Single source of truth for subscription pricing across payment providers.

Every amount a customer can be charged is defined here **once** — Stripe in EUR,
Chargily in DZD, monthly and annual. ``stripe_setup.py``, ``chargily_service.py``
and the ``/api/billing/pricing`` endpoint all read from this module, so the price
grid can no longer drift between the four places it used to be duplicated in
(Chargily env vars, the Stripe setup script, ``.env`` and the pricing page).

Environment overrides: an ops-set env var still wins when present, so a single
price can be tuned without a redeploy. The constants below are the reviewed
defaults and the fail-safe when no override is set — unlike the previous design,
a missing override no longer breaks checkout, it falls back to the reviewed grid.

Pure module (no FastAPI, no DB) so it stays trivially testable, same pattern as
``entitlements.py``. Callers translate the exceptions raised here into HTTP
responses.
"""

from __future__ import annotations

import os
from typing import Dict, List

PLANS = ("starter", "pro", "business")
CYCLES = ("monthly", "annual")

# Minimum amount Chargily accepts, in DZD.
CHARGILY_MIN_DZD = 75

# Reviewed grid. EUR annual = 11 × monthly (~1 month free). DZD anchored at
# ~150 DZD per EUR, rounded to whole dinars. These are the ONLY hard-coded
# amounts in the codebase; everything else derives from them.
_GRID: Dict[str, Dict[str, int]] = {
    "starter": {"eur_monthly": 10, "eur_annual": 110, "dzd_monthly": 1500, "dzd_annual": 16500},
    "pro": {"eur_monthly": 25, "eur_annual": 275, "dzd_monthly": 3750, "dzd_annual": 41250},
    "business": {
        "eur_monthly": 125,
        "eur_annual": 1375,
        "dzd_monthly": 18750,
        "dzd_annual": 206250,
    },
}

# (plan, cycle) → env var that overrides the Chargily DZD amount, if set.
_CHARGILY_ENV = {
    ("starter", "monthly"): "CHARGILY_PRICE_STARTER_M",
    ("starter", "annual"): "CHARGILY_PRICE_STARTER_Y",
    ("pro", "monthly"): "CHARGILY_PRICE_PRO_M",
    ("pro", "annual"): "CHARGILY_PRICE_PRO_Y",
    ("business", "monthly"): "CHARGILY_PRICE_BUSINESS_M",
    ("business", "annual"): "CHARGILY_PRICE_BUSINESS_Y",
}


class UnknownPlanCycle(KeyError):
    """Raised when (plan, cycle) is not part of the published grid."""


class InvalidPrice(ValueError):
    """Raised when a resolved amount is misconfigured (bad override, below min)."""


# Produits hors formule (API, options, rapports, formation). Montant EUR revu ;
# le montant DZD suit la même règle que la grille ci-dessus (DZD_PER_EUR par
# euro), surchargeable par `CHARGILY_PRICE_<ID>` (ex. CHARGILY_PRICE_API_STARTER).
# "recurring" = facturé chaque mois (abonnement Stripe ; côté Chargily, un
# paiement ponctuel couvre 30 jours). "api_request_quota" = produit livré
# automatiquement sous forme de clé API avec ce quota mensuel de requêtes.
DZD_PER_EUR = 150

PRODUCTS: Dict[str, dict] = {
    "api_starter": {
        "label": "Starter API",
        "eur": 29,
        "recurring": True,
        "api_request_quota": 5000,
    },
    "api_business": {
        "label": "Business API",
        "eur": 99,
        "recurring": True,
        "api_request_quota": 50000,
    },
    "api_pack": {"label": "Pack requêtes API (+20 000 / mois)", "eur": 19, "recurring": True},
    "extra_seat": {"label": "Utilisateur supplémentaire", "eur": 5, "recurring": True},
    "priority_support": {"label": "Support prioritaire", "eur": 15, "recurring": True},
    "newsletter": {"label": "Newsletter — veille tarifaire", "eur": 9, "recurring": True},
    "team_training": {"label": "Formation équipe", "eur": 99, "recurring": False},
    "report_agri": {
        "label": "Rapport Agriculture & Agroalimentaire",
        "eur": 59,
        "recurring": False,
    },
    "report_textile": {"label": "Rapport Textile & Habillement", "eur": 59, "recurring": False},
    "report_pharma": {"label": "Rapport Pharmaceutique & Santé", "eur": 89, "recurring": False},
    "report_pack": {"label": "Pack 4 rapports sectoriels", "eur": 179, "recurring": False},
    "certification": {
        "label": "Certification Expert Commerce AfCFTA",
        "eur": 129,
        "recurring": False,
    },
}


class UnknownProduct(KeyError):
    """Raised when a product id is not part of the published catalogue."""


def product(product_id: str) -> dict:
    """Catalogue entry for a product id (read-only use)."""
    if product_id not in PRODUCTS:
        raise UnknownProduct(product_id)
    return PRODUCTS[product_id]


def product_dzd_amount(product_id: str) -> int:
    """Chargily DZD amount for a product: env override or EUR × DZD_PER_EUR."""
    entry = product(product_id)
    env_name = f"CHARGILY_PRICE_{product_id.upper()}"
    raw = os.environ.get(env_name)
    if raw is not None and raw.strip() != "":
        try:
            amount = int(raw)
        except ValueError as exc:
            raise InvalidPrice(f"{env_name}={raw!r} n'est pas un entier DZD.") from exc
    else:
        amount = entry["eur"] * DZD_PER_EUR
    if amount < CHARGILY_MIN_DZD:
        raise InvalidPrice(
            f"Montant DZD sous le minimum Chargily ({CHARGILY_MIN_DZD}) : {product_id}={amount}."
        )
    return amount


def products_grid() -> List[dict]:
    """The product catalogue as JSON-serialisable rows, for the pricing page."""
    return [
        {
            "product": product_id,
            "label": entry["label"],
            "recurring": entry["recurring"],
            "eur": entry["eur"],
            "dzd": product_dzd_amount(product_id),
        }
        for product_id, entry in PRODUCTS.items()
    ]


def _require_plan_cycle(plan: str, cycle: str) -> None:
    if plan not in _GRID or cycle not in CYCLES:
        raise UnknownPlanCycle(f"{plan}/{cycle}")


def eur_amount(plan: str, cycle: str) -> int:
    """Whole-euro Stripe price for (plan, cycle)."""
    _require_plan_cycle(plan, cycle)
    return _GRID[plan][f"eur_{cycle}"]


def stripe_cents(plan: str, cycle: str) -> int:
    """Stripe ``unit_amount`` (EUR cents) for (plan, cycle)."""
    return eur_amount(plan, cycle) * 100


def dzd_amount(plan: str, cycle: str) -> int:
    """Chargily DZD amount for (plan, cycle).

    An ``CHARGILY_PRICE_*`` env override wins when set; otherwise the reviewed
    grid default is used. Raises ``UnknownPlanCycle`` for an unknown couple and
    ``InvalidPrice`` for a non-integer override or an amount below the Chargily
    minimum.
    """
    _require_plan_cycle(plan, cycle)
    raw = os.environ.get(_CHARGILY_ENV[(plan, cycle)])
    if raw is not None and raw.strip() != "":
        try:
            amount = int(raw)
        except ValueError as exc:
            raise InvalidPrice(
                f"{_CHARGILY_ENV[(plan, cycle)]}={raw!r} n'est pas un entier DZD."
            ) from exc
    else:
        amount = _GRID[plan][f"dzd_{cycle}"]
    if amount < CHARGILY_MIN_DZD:
        raise InvalidPrice(
            f"Montant DZD sous le minimum Chargily ({CHARGILY_MIN_DZD}) : {plan}/{cycle}={amount}."
        )
    return amount


def grid() -> List[dict]:
    """The full grid as JSON-serialisable rows, for the pricing endpoint/UI."""
    rows: List[dict] = []
    for plan in PLANS:
        rows.append(
            {
                "plan": plan,
                "eur": {
                    "monthly": eur_amount(plan, "monthly"),
                    "annual": eur_amount(plan, "annual"),
                },
                "dzd": {
                    "monthly": dzd_amount(plan, "monthly"),
                    "annual": dzd_amount(plan, "annual"),
                },
            }
        )
    return rows
