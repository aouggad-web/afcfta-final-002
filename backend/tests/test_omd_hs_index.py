"""
Tests de l'index alphabétique OMD (recherche « nom de marchandise -> code SH »).

Vérifie le service de recherche par tokens (insensible à l'ordre/accents/casse) et
la qualité de l'index généré par ``etl/omd_hs_index.py``.
"""

from services import omd_hs_index_service as omd


def _labels(res):
    return [r["label"] for r in res["results"]]


def test_index_loaded_and_non_trivial():
    data = omd._load()
    assert data["entries"], "l'index OMD doit être chargé"
    assert len(data["entries"]) > 3000, "l'index complet couvre des milliers d'entrées"


def test_word_order_independent_search():
    """L'OMD classe par premier mot (« PALME (HUILE DE) ») : la requête en langage
    naturel « huile de palme » doit malgré tout retrouver l'entrée."""
    res = omd.search("huile de palme", limit=10)
    top = res["results"][0]
    assert "PALME" in top["term"]
    assert "1511" in top["hs_codes"]


def test_accent_and_case_insensitive():
    res_lower = omd.search("thé vert")
    res_upper = omd.search("THE VERT")
    assert res_lower["results"] and res_upper["results"]
    assert res_lower["results"][0]["hs_codes"] == res_upper["results"][0]["hs_codes"]
    # Thé vert -> 0902.10 / 0902.20.
    assert any(c.startswith("0902") for c in res_lower["results"][0]["hs_codes"])


def test_no_mid_word_substring_false_positive():
    """
    Régression (revue Copilot) : le matching doit être ancré sur des limites de
    mot, pas une sous-chaîne arbitraire — le token « or » ne doit jamais matcher
    « coriandre » (qui ne contient « or » qu'en milieu de mot).
    """
    res = omd.search("or", limit=200)
    labels = [r["label"].lower() for r in res["results"]]
    assert not any("coriandre" in label for label in labels)


def test_singular_plural_prefix_still_matches():
    """Le matching par préfixe de mot doit continuer à couvrir les variations de
    singulier/pluriel usuelles (« voiture » -> libellés en « VOITURES »)."""
    res = omd.search("voiture", limit=10)
    assert res["results"]
    assert any("VOITURES" in r["label"] for r in res["results"])


def test_all_query_tokens_must_match():
    """Sémantique ET : un mot absent exclut l'entrée (pas de bruit)."""
    res = omd.search("machine à coudre")
    assert res["results"]
    for r in res["results"]:
        norm = omd._normalize(r["label"])
        assert "coudre" in norm


def test_cross_reference_preserved():
    """Les renvois « voir X » de l'OMD sont conservés (ex. ABRICOTS -> FRUITS)."""
    res = omd.search("abricots")
    assert res["results"]
    assert any(r["see_also"] for r in res["results"])


def test_empty_query_is_safe():
    res = omd.search("   ")
    assert res["count"] == 0
    assert res["results"] == []


def test_hs6_codes_are_digit_normalized():
    """Les codes retournés sont normalisés sans point (5305.21 -> 530521)."""
    res = omd.search("abaca")
    assert res["results"]
    codes = res["results"][0]["hs_codes"]
    assert "530521" in codes
    assert all(c.isdigit() for c in codes)
