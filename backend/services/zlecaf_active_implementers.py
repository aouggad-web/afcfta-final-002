"""
Pays ayant réellement mis en œuvre l'Accord ZLECAf à l'importation — au-delà
de la simple ratification continentale (zlecaf_membership_status.py).

Principe (celui déjà appliqué à l'Algérie via la circulaire DGD 482/2024,
généralisé ici) : une préférence tarifaire ZLECAf ne peut être réellement
accordée par un pays DESTINATION que si son administration douanière a
elle-même publié/appliqué un barème préférentiel opérationnel — la
ratification seule (acte juridique) ne suffit pas à garantir une réduction
de droit effective au poste-frontière.

DZA et ZAF ont leur propre module dédié (listes de partenaires bilatéraux
actifs : zlecaf_schedule_dza.py, zlecaf_schedule_zaf.py) — gérés en amont
dans _resolve_zlecaf_context, jamais via ce registre générique.

Deux niveaux de preuve, recherche documentée le 2026-07-06 :

1. INSTRUMENT DATÉ (circulaire/règlement/arrêté douanier nommé) :
   - ETH : Règlement du Conseil des Ministres n° 574/2025 (Federal Negarit
     Gazette, 14/07/2025) — Douanes éthiopiennes instruites d'appliquer les
     réductions ZLECAf avec 24 États membres.
   - ZMB : Statutory Instrument n° 92 du 30/12/2024 — barème provisoire de
     concessions tarifaires ZLECAf publié.
   - CIV : Ordonnance du Conseil des ministres du 23/04/2025 — démantèlement
     sur 5 516 lignes du TEC CEDEAO (HS2017), dégressif 10 %/an.
   - NGA : Barème provisoire de concessions tarifaires publié en 2025,
     unités douanières ZLECAf dédiées créées.

2. GUIDED TRADE INITIATIVE (GTI) — pilote opérationnel du Secrétariat
   ZLECAf, lancé 2022 : les pays participants échangent RÉELLEMENT sous
   préférence ZLECAf (c'est la définition même du programme), même sans
   circulaire nationale individuellement retrouvée. 8 pays fondateurs :
   CMR, EGY, GHA, KEN, MUS, RWA, TZA, TUN.

Non inclus malgré des indices partiels (preuve insuffisante ou
contradictoire) : MAR (tralac indique une ratification non déposée à ce
jour, en contradiction avec sa propre mention dans le règlement éthiopien
574/2025 et sur douane.gov.ma — litige de source non résolu, à vérifier).

Pas de fabrication : liste volontairement PARTIELLE. Un pays absent d'ici
n'est pas présumé non-implémenteur avec certitude — simplement, aucune
preuve suffisante n'a été trouvée à ce jour. _resolve_zlecaf_context traite
l'absence comme "application réelle non confirmée" (repli FTA conditionnelle
ou NPF), jamais comme une exclusion positive.
"""

from __future__ import annotations

# Instrument daté et nommé (le plus haut niveau de preuve).
DATED_INSTRUMENT: frozenset[str] = frozenset({"ETH", "ZMB", "CIV", "NGA"})

# Participants confirmés de la Guided Trade Initiative (échanges réels sous
# préférence ZLECAf, par construction du programme).
GTI_PARTICIPANTS: frozenset[str] = frozenset(
    {"CMR", "EGY", "GHA", "KEN", "MUS", "RWA", "TZA", "TUN"}
)

# DZA et ZAF gérés par leurs modules dédiés — inclus ici pour la cohérence de
# la documentation uniquement (jamais consultés via ce registre en pratique,
# _resolve_zlecaf_context les intercepte avant d'atteindre le cas générique).
DEDICATED_MODULE: frozenset[str] = frozenset({"DZA", "ZAF"})

ACTIVE_IMPLEMENTERS: frozenset[str] = DATED_INSTRUMENT | GTI_PARTICIPANTS | DEDICATED_MODULE


def is_active_implementer(iso3: str) -> bool:
    """True si le pays a une preuve (instrument daté ou GTI) d'application
    réelle du barème préférentiel ZLECAf à l'importation."""
    return (iso3 or "").upper() in ACTIVE_IMPLEMENTERS


def implementation_evidence(iso3: str) -> str:
    """Courte description de la preuve retenue, pour les notes utilisateur."""
    code = (iso3 or "").upper()
    if code in DEDICATED_MODULE:
        return "module bilatéral dédié"
    if code in DATED_INSTRUMENT:
        return "instrument douanier daté (voir docstring du module)"
    if code in GTI_PARTICIPANTS:
        return "participant Guided Trade Initiative (AfCFTA Secretariat)"
    return "aucune preuve d'application réelle trouvée"
