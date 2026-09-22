"""
Tests du garde-fou MÉTHODOLOGIQUE par commodité (commodity_caveat).

Bug signalé : pour la banane dessert (SH 080390), le module Opportunités
affichait le Nigéria comme « producteur principal » avec plus de 22 % de part
continentale. Ce n'est pas une hallucination ni un trou de couverture : le
chiffre (≈6,9 M t) correspond fidèlement à l'item FAOSTAT 486 « Bananas ».

Le problème est méthodologique : FAOSTAT « Bananas » agrège les bananes
dessert (Cavendish, l'essentiel du commerce SH 080390) ET les bananes à
cuire / bananes de montagne d'Afrique de l'Est (matooke…), cultivées surtout
pour l'autoconsommation. Le classement de PRODUCTION alimentaire ne reflète
donc pas la capacité d'EXPORT de banane dessert — les leaders africains à
l'export (Côte d'Ivoire, Cameroun) se lisent sur les flux commerciaux. D'où
ce caveat, affiché EN PLUS du classement (jamais un motif de suppression,
contrairement au coverage_caveat).
"""

import os
import sys

_backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

from services import production_capacity_service as pcs  # noqa: E402


def test_commodity_caveat_present_for_bananas():
    note = pcs._commodity_caveat("Bananas")
    assert note is not None
    assert "080390" in note
    assert "Côte d'Ivoire" in note and "Cameroun" in note


def test_commodity_caveat_present_for_plantain():
    note = pcs._commodity_caveat("Plantain")
    assert note is not None
    assert "080310" in note


def test_commodity_caveat_absent_for_unaffected_commodity():
    assert pcs._commodity_caveat("Cocoa beans") is None
    assert pcs._commodity_caveat("Gold") is None


def test_continental_producers_banana_carries_methodology_caveat():
    # Reproduit exactement le cas signalé : SH 080390 -> classement mené par le
    # Nigéria, MAIS avec un caveat méthodologique explicite qui interdit de le
    # lire comme capacité d'export de banane dessert.
    res = pcs.get_continental_producers("080390")
    assert res.get("available")
    assert res.get("commodity") == "Bananas"
    caveat = res.get("commodity_caveat")
    assert caveat is not None
    assert "export" in caveat.lower()
    # Le classement lui-même reste fourni (le caveat ne le supprime PAS).
    assert res.get("top_producers")


def test_get_capacity_banana_continental_block_has_methodology_caveat():
    cap = pcs.get_capacity("NGA", "080390")
    assert cap.get("available")
    assert (cap.get("continental") or {}).get("commodity_caveat")


def test_country_profile_banana_entry_has_methodology_caveat():
    # get_capacity("NGA", "080390") établit que la fixture contient bien des
    # données banane pour le Nigéria — l'entrée DOIT donc exister dans le profil,
    # sans quoi la propagation get_country_profile ne serait pas réellement testée.
    #
    # ``top_n`` est explicite parce que le profil est TRONQUÉ par part africaine
    # décroissante. Tant que le pont ne portait que 92 commodités agricoles, la
    # banane tenait dans les 20 premières du Nigéria par accident de rareté ;
    # avec 151, vingt produits la devancent réellement. Le test porte sur la
    # PROPAGATION du caveat, pas sur le rang de la banane — figer ce rang
    # ferait échouer la suite à chaque fois que le référentiel s'enrichit.
    assert pcs.get_capacity("NGA", "080390").get("available")
    profile = pcs.get_country_profile("NGA", top_n=len(pcs.list_tracked_products()))
    bananas = [p for p in profile.get("products", []) if p.get("commodity") == "Bananas"]
    assert bananas, "attendu : une entrée « Bananas » dans le profil du Nigéria"
    assert bananas[0].get("commodity_caveat")


def test_country_profile_is_truncated_and_ranked_by_african_share():
    # Contrôle miroir du précédent : si la troncature disparaissait, le test
    # ci-dessus passerait sans rien prouver de la propagation sur un profil réel.
    profile = pcs.get_country_profile("NGA", top_n=5)
    shares = [p["share_pct"] or 0.0 for p in profile["products"]]
    assert len(profile["products"]) == 5
    assert shares == sorted(shares, reverse=True)
