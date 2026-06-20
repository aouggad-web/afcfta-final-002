"""
Régimes commerciaux régionaux africains : unions douanières et zones de
libre-échange.

Principe (confirmé par la newsletter « Update on the AfCFTA », dtic/SARS,
mars 2026, FAQ Q1 : « South Africa will […] not trade preferentially with
SACU and SADC Member States under the AfCFTA ») : deux pays d'une même UNION
DOUANIÈRE échangent en LIBRE CIRCULATION sous le régime de l'union (tarif
extérieur commun + droit de douane intra-bloc nul), et NON sous la ZLECAf.

Deux niveaux d'intégration sont distingués :

1. UNION DOUANIÈRE (SACU, EAC, CEMAC, UEMOA) — la franchise intra-bloc (0 %)
   est *définitionnelle* (marché unique / TEC + libre circulation), donc
   indépendante de la nomenclature produit et de la ratification ZLECAf.
   → le moteur applique 0 % de droit de douane sur les échanges intra-union.

2. ZONE DE LIBRE-ÉCHANGE (CEDEAO/ECOWAS, SADC, COMESA) — la franchise est
   réservée aux produits ORIGINAIRES remplissant les règles d'origine du bloc
   et hors listes sensibles/exclusions. Faute de calendrier produit + règles
   d'origine fiables dans ce moteur, ces régimes sont signalés comme
   CONDITIONNELS (information) SANS recalcul automatique des droits.

Rosters réutilisés du dépôt (aucune liste fabriquée) :
  - SACU  : backend/crawlers/countries/sacu_customs_union.py
  - CEMAC : backend/config/regional_config.py (CEMAC_COUNTRIES)
  - EAC, ECOWAS, SADC, COMESA :
            backend/intelligence/analytics/regional_analytics.py
  - UEMOA : les 8 membres de l'Union économique et monétaire ouest-africaine
            (sous-ensemble douanier francophone + GNB de la CEDEAO).
"""
from __future__ import annotations

# ── Unions douanières : libre circulation, droit de douane intra-bloc = 0 % ──
SACU = frozenset({"ZAF", "BWA", "NAM", "LSO", "SWZ"})
EAC = frozenset({"BDI", "COD", "KEN", "RWA", "SSD", "TZA", "UGA"})
CEMAC = frozenset({"CMR", "CAF", "TCD", "COG", "GNQ", "GAB"})
UEMOA = frozenset({"BEN", "BFA", "CIV", "GNB", "MLI", "NER", "SEN", "TGO"})

CUSTOMS_UNIONS = {
    "SACU": SACU,
    "EAC": EAC,
    "CEMAC": CEMAC,
    "UEMOA": UEMOA,
}

CUSTOMS_UNION_NAMES = {
    "SACU": "Union douanière d'Afrique australe (SACU)",
    "EAC": "Communauté d'Afrique de l'Est (EAC)",
    "CEMAC": "Communauté économique et monétaire de l'Afrique centrale (CEMAC)",
    "UEMOA": "Union économique et monétaire ouest-africaine (UEMOA)",
}

# ── Zones de libre-échange : franchise CONDITIONNELLE (règles d'origine) ─────
ECOWAS = frozenset({"BEN", "BFA", "CPV", "CIV", "GMB", "GHA", "GIN", "GNB",
                    "LBR", "MLI", "NER", "NGA", "SEN", "SLE", "TGO"})
SADC = frozenset({"AGO", "BWA", "COM", "COD", "LSO", "MDG", "MWI", "MUS",
                  "MOZ", "NAM", "SYC", "ZAF", "SWZ", "TZA", "ZMB", "ZWE"})
COMESA = frozenset({"BDI", "COM", "COD", "DJI", "EGY", "ERI", "ETH", "KEN",
                    "LBY", "MDG", "MWI", "MUS", "RWA", "SOM", "SDN", "SWZ",
                    "TUN", "UGA", "ZMB", "ZWE"})

FREE_TRADE_AREAS = {
    "ECOWAS": ECOWAS,
    "SADC": SADC,
    "COMESA": COMESA,
}

FTA_NAMES = {
    "ECOWAS": "Communauté économique des États de l'Afrique de l'Ouest (CEDEAO)",
    "SADC": "Communauté de développement d'Afrique australe (SADC)",
    "COMESA": "Marché commun de l'Afrique orientale et australe (COMESA)",
}


def _norm(iso3) -> str:
    return (iso3 or "").strip().upper()


def same_customs_union(origin_iso3, dest_iso3):
    """Code de l'union douanière commune aux deux pays, sinon ``None``.

    Retourne ``None`` si origine == destination ou si les deux pays ne
    partagent aucune union douanière. L'appartenance à une union douanière
    implique la libre circulation des marchandises (droit de douane
    intra-bloc nul), indépendamment de la ZLECAf."""
    o, d = _norm(origin_iso3), _norm(dest_iso3)
    if not o or not d or o == d:
        return None
    for code, members in CUSTOMS_UNIONS.items():
        if o in members and d in members:
            return code
    return None


def shared_free_trade_areas(origin_iso3, dest_iso3):
    """Codes des zones de libre-échange communes aux deux pays (liste, peut
    être vide).

    Régime conditionné aux règles d'origine du bloc : usage purement
    informatif (aucun recalcul automatique des droits)."""
    o, d = _norm(origin_iso3), _norm(dest_iso3)
    if not o or not d or o == d:
        return []
    return [code for code, members in FREE_TRADE_AREAS.items()
            if o in members and d in members]
