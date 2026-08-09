#!/usr/bin/env python3
"""
Création des Products / Prices Stripe pour les abonnements ZLECAf
=================================================================

Crée (ou retrouve) un Product par plan — Starter / Pro / Business — et deux
Prices récurrents par plan (mensuel + annuel), puis imprime le bloc de
variables d'environnement `STRIPE_PRICE_*` à coller dans votre `.env`.

Le script est **idempotent** :
  - les Products sont recherchés par `metadata.plan` avant création ;
  - les Prices sont retrouvés par `lookup_key` (unique) avant création.
Le relancer ne crée donc pas de doublons.

Grille (validée) — montants en USD :
  Starter : 9 $/mois   ·  annuel 7 $/mois  (84 $/an)
  Pro     : 19 $/mois  ·  annuel 15 $/mois (180 $/an)
  Business: 59 $/mois  ·  annuel 49 $/mois (588 $/an)

Usage :
  export STRIPE_SECRET_KEY=sk_test_xxx        # clé TEST tant que le compte est en vérification
  python scripts/stripe_setup.py              # crée/retrouve et affiche les price_id
  python scripts/stripe_setup.py --dry-run    # n'écrit rien, montre ce qui serait fait

Prérequis :
  pip install stripe
"""

from __future__ import annotations

import argparse
import os
import sys

try:
    import stripe
except ImportError:
    sys.exit("Le SDK Stripe est requis : pip install stripe")


# ── Grille tarifaire (source de vérité alignée sur pricing.html) ────────────
# unit_amount en cents USD. L'annuel est un prix `interval=year` dont le montant
# est le total annuel (mensuel remisé × 12).
PLANS = [
    {
        "slug": "starter",
        "name": "ZLECAf Starter",
        "description": "Calculs illimités, 54 pays, export CSV — indépendants et petits importateurs/exportateurs.",
        "monthly_cents": 900,     # 9 $/mois
        "annual_cents": 8400,     # 7 $/mois × 12 = 84 $/an
    },
    {
        "slug": "pro",
        "name": "ZLECAf Pro",
        "description": "Export CSV+Excel+PDF, profils complets, alertes tarifaires — exportateurs, traders, consultants.",
        "monthly_cents": 1900,    # 19 $/mois
        "annual_cents": 18000,    # 15 $/mois × 12 = 180 $/an
    },
    {
        "slug": "business",
        "name": "ZLECAf Business",
        "description": "Tout Pro + API REST, rapports automatisés, 5 utilisateurs — entreprises et plateformes.",
        "monthly_cents": 5900,    # 59 $/mois
        "annual_cents": 58800,    # 49 $/mois × 12 = 588 $/an
    },
]

CURRENCY = "usd"
APP_TAG = "zlecaf"


def find_product(slug: str):
    """Retrouve un Product par metadata.plan (search API), sinon None."""
    res = stripe.Product.search(query=f"metadata['plan']:'{slug}' AND metadata['app']:'{APP_TAG}'")
    return res.data[0] if res.data else None


def ensure_product(plan: dict, dry_run: bool):
    existing = find_product(plan["slug"])
    if existing:
        print(f"  Product   ✓ existant  {existing.id}  ({plan['name']})")
        return existing
    if dry_run:
        print(f"  Product   + à créer    (dry-run)  {plan['name']}")
        return None
    prod = stripe.Product.create(
        name=plan["name"],
        description=plan["description"],
        metadata={"app": APP_TAG, "plan": plan["slug"]},
    )
    print(f"  Product   + créé       {prod.id}  ({plan['name']})")
    return prod


def find_price_by_lookup(lookup_key: str):
    res = stripe.Price.list(lookup_keys=[lookup_key], limit=1)
    return res.data[0] if res.data else None


def ensure_price(product, plan: dict, cycle: str, dry_run: bool):
    """cycle ∈ {'monthly','annual'}. Retourne le price id (ou None en dry-run)."""
    interval = "month" if cycle == "monthly" else "year"
    amount = plan["monthly_cents"] if cycle == "monthly" else plan["annual_cents"]
    lookup_key = f"{APP_TAG}_{plan['slug']}_{cycle}"

    existing = find_price_by_lookup(lookup_key)
    if existing:
        print(f"  Price     ✓ existant  {existing.id}  [{lookup_key}]  {amount/100:.0f} {CURRENCY.upper()}/{interval}")
        return existing.id
    if dry_run:
        print(f"  Price     + à créer    (dry-run)  [{lookup_key}]  {amount/100:.0f} {CURRENCY.upper()}/{interval}")
        return None
    if product is None:
        print(f"  Price     ! ignoré (product non créé)  [{lookup_key}]")
        return None
    price = stripe.Price.create(
        product=product.id,
        currency=CURRENCY,
        unit_amount=amount,
        recurring={"interval": interval},
        lookup_key=lookup_key,
        transfer_lookup_key=True,  # réassigne la lookup_key si un ancien prix la portait
        metadata={"app": APP_TAG, "plan": plan["slug"], "cycle": cycle},
    )
    print(f"  Price     + créé       {price.id}  [{lookup_key}]  {amount/100:.0f} {CURRENCY.upper()}/{interval}")
    return price.id


def main() -> int:
    parser = argparse.ArgumentParser(description="Crée les Products/Prices Stripe ZLECAf.")
    parser.add_argument("--dry-run", action="store_true", help="N'écrit rien côté Stripe, montre le plan d'action.")
    args = parser.parse_args()

    key = os.environ.get("STRIPE_SECRET_KEY")
    if not key:
        return _fail("STRIPE_SECRET_KEY manquante. export STRIPE_SECRET_KEY=sk_test_...")
    stripe.api_key = key

    mode = "TEST" if key.startswith("sk_test_") else "LIVE"
    if mode == "LIVE":
        print("⚠️  Clé LIVE détectée. Ce script est prévu pour le mode TEST pendant la vérification.")
        if not args.dry_run and os.environ.get("STRIPE_ALLOW_LIVE") != "true":
            return _fail("Refus par sécurité. Pour forcer le live : export STRIPE_ALLOW_LIVE=true")

    print(f"\nMode Stripe : {mode}{'  (dry-run)' if args.dry_run else ''}\n")

    env_lines: list[str] = []
    for plan in PLANS:
        print(f"Plan {plan['slug'].upper()}")
        product = ensure_product(plan, args.dry_run)
        pid_m = ensure_price(product, plan, "monthly", args.dry_run)
        pid_y = ensure_price(product, plan, "annual", args.dry_run)
        up = plan["slug"].upper()
        env_lines.append(f"STRIPE_PRICE_{up}_M={pid_m or '<à générer — relancer sans --dry-run>'}")
        env_lines.append(f"STRIPE_PRICE_{up}_Y={pid_y or '<à générer — relancer sans --dry-run>'}")
        print()

    print("─" * 64)
    print("Collez ces lignes dans votre .env :\n")
    print("\n".join(env_lines))
    print("─" * 64)
    return 0


def _fail(msg: str) -> int:
    print(f"Erreur : {msg}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
