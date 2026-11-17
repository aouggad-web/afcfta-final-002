"""Inventaire des routes de l'API (audit D1, 16/11/2026).

Décision de l'exploitant du 09/11/2026 : sans compte, seul le tableau de bord
d'accueil est consultable. Le 16/11, l'audit a trouvé 55 routes de modules
réservés servies sans compte : la règle avait été posée module par module, et
rien n'empêchait une route d'y échapper.

Ce test classe chaque route de l'application réelle :

- gardée : elle porte une garde d'accès (connexion, module, formule payante,
  quota, admin, rédacteur, export) ;
- publique : déclarée ici, avec sa raison.

Les 85 routes sans appelant, longtemps tenues à part, ont été supprimées le
17/11/2026 (décision de l'exploitant : une route qu'aucun écran n'appelle est
inutilisée). Une route nouvelle ni gardée ni publique fait échouer la CI.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.tests.routes_effectives import routes_api  # noqa: E402

# Noms (qualname) des dépendances qui contrôlent l'accès.
GARDES = (
    "require_module_consultation.",
    # Connexion exigée, rien de décompté : routes que le calculateur partage
    # (PR #806).
    "require_login.",
    "require_module_enabled.",
    "require_module.",
    "require_paid_module.",
    "require_calculations_quota.",
    "require_api_access.",
    "require_admin",
    "require_redacteur",
    "require_export_format.",
    "_format_d_export",
    "check_ai_quota",
)

# Routes publiques assumées, avec leur raison.
PUBLIQUES = {
    "/api/": "racine de l'API",
    "/api/health": "sonde de disponibilité",
    "/api/health/status": "sonde de disponibilité",
    "/api/contact": "formulaire de contact, public par décision du 09/11/2026",
    "/api/countries": "liste des pays, menus de l'application dont l'accueil",
    "/api/marches/apercu": "tableau de bord d'accueil (cours, bourses)",
    "/api/news": "tableau de bord d'accueil (dépêches)",
    "/api/news/by-category": "tableau de bord d'accueil",
    "/api/news/by-region": "tableau de bord d'accueil",
    "/api/news/country-of-the-week": "tableau de bord d'accueil",
    "/api/news/images/{article_id}": "vignettes des dépêches de l'accueil",
    "/api/auth/login": "authentification",
    "/api/auth/logout": "authentification",
    "/api/auth/register": "authentification",
    "/api/auth/session": "authentification",
    "/api/auth/me": "session courante, contrôlée par la route",
    "/api/auth/account": "suppression du compte, contrôlée par la route",
    "/api/auth/account/export": "export RGPD du compte, contrôlé par la route",
    "/api/billing/entitlements": "grille des formules, page Tarifs",
    "/api/billing/pricing": "prix, page Tarifs",
    "/api/billing/payment-context": "moyen de paiement selon le pays, page Tarifs",
    "/api/billing/geo-diagnostic": "diagnostic de l'adresse vue par le serveur (E5)",
    "/api/billing/subscription": "abonnement courant, contrôlé par la route",
    "/api/billing/checkout": "paiement, session contrôlée par la route",
    "/api/billing/product-checkout": "paiement, session contrôlée par la route",
    "/api/billing/portal": "portail de facturation, session contrôlée par la route",
    "/api/billing/webhook": "webhook Stripe, signature vérifiée",
    "/api/billing/chargily/webhook": "webhook Chargily, HMAC vérifié",
    "/api/admin/keys/verify": "vérification d'une clé API par son porteur",
    "/api/reports/health": "diagnostic public du module Opportunités",
    "/api/reports/oec-health": "diagnostic public du module Opportunités",
    "/api/calcul/export/pays": "pays couverts à l'export (métadonnées)",
    "/api/hs-codes/all": "nomenclature du Système harmonisé, publique",
    "/api/hs-codes/chapters": "nomenclature du Système harmonisé, publique",
    "/api/hs-codes/chapter/{chapter}": "nomenclature du Système harmonisé, publique",
    "/api/hs-codes/code/{hs_code}": "nomenclature du Système harmonisé, publique",
    "/api/hs-codes/label/{hs_code}": "nomenclature du Système harmonisé, publique",
    "/api/hs-codes/product-index": "nomenclature du Système harmonisé, publique",
    "/api/hs-codes/search": "nomenclature du Système harmonisé, publique",
    "/api/hs-codes/statistics": "nomenclature du Système harmonisé, publique",
    "/{full_path:path}": "interface React (repli de l'application monopage)",
}

def _gardee(route):
    pile = list(route.dependant.dependencies)
    while pile:
        dependance = pile.pop()
        if getattr(dependance.call, "__qualname__", "").startswith(GARDES):
            return True
        pile.extend(dependance.dependencies)
    return False


def _non_classees(app):
    non_classees = []
    for route in routes_api(app):
        if _gardee(route) or route.path in PUBLIQUES:
            continue
        methodes = ",".join(sorted(route.original_route.methods - {"HEAD", "OPTIONS"}))
        non_classees.append(f"{methodes} {route.path}")
    return non_classees


def test_chaque_route_est_gardee_ou_publique():
    from server import app

    assert _non_classees(app) == [], (
        "Route ni gardée ni publique : poser une garde (routes/__init__.py) ou la "
        "déclarer publique ici avec sa raison."
    )


def test_les_routes_sans_appelant_ne_sont_plus_servies():
    """Préfixes des routeurs supprimés le 17/11/2026 (audit D8, D3)."""
    from server import app

    supprimes = (
        "/api/ai/", "/api/ai-intelligence/", "/api/analysis/", "/api/countries/sadc/",
        "/api/currencies/", "/api/enhanced-search/", "/api/hs6-tariffs/", "/api/investment/",
        "/api/mining/", "/api/mobile/", "/api/news/algeria/", "/api/regional/",
        "/api/regions/", "/api/regulatory-compliance/", "/api/regulatory-master-registry/",
        "/api/regulatory-qa/", "/api/tariffs/", "/api/trade-corridors/", "/api/trade-data/",
    )
    restantes = [r.path for r in routes_api(app) if r.path.startswith(supprimes)]
    # Gardées et conservées : export de l'analytique régionale, rafraîchissement
    # admin des taux de change.
    analytique = {r.path for r in routes_api(app) if r.path.startswith("/api/regional-analytics/")}
    change = {r.path for r in routes_api(app) if r.path.startswith("/api/exchange-rates/")}

    assert restantes == []
    assert analytique == {"/api/regional-analytics/export"}
    assert change == {"/api/exchange-rates/refresh"}


def test_les_routes_des_modules_reserves_portent_une_garde():
    """Les routeurs trouvés ouverts par l'audit du 16/11/2026 (D1)."""
    from server import app

    prefixes = (
        "/api/banking/", "/api/insurance/", "/api/consultation/", "/api/regulatory-engine/",
        "/api/dismantlement/", "/api/oec/", "/api/faostat/",
        "/api/countries/economic-indicators", "/api/countries/official-stats/",
    )
    routes = [r for r in routes_api(app) if r.path.startswith(prefixes)]

    assert {p for p in prefixes if any(r.path.startswith(p) for r in routes)} == set(prefixes)
    assert [r.path for r in routes if not _gardee(r)] == []
