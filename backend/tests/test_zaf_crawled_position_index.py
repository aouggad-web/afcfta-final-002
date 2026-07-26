"""
Régression : `load_crawled_position_index()` (authentic_tariff_service.py)
ne comprenait que le schéma DZA (clé racine "sub_positions", code sous
"hs_code", taxes en dict {code: {rate,...}}). Pour l'Afrique du Sud, le
crawl authentique SARS (data/crawled/ZAF_tariffs.json) utilise un second
schéma réel dans ce dépôt (clé racine "positions", code sous
"code_clean"/"code_raw", taxes en LISTE de {code, rate_pct, ...}) — l'index
retournait donc systématiquement {} pour ZAF, et calculate_import_taxes()
retombait silencieusement sur le taux ETL au lieu du taux SARS crawlé.

Ce module verrouille : (1) l'index n'est plus vide pour ZAF, (2) le taux DD
utilisé provient bien du crawl SARS (pas de l'ETL), (3) DZA — seul pays
couvert avant ce correctif — garde un comportement strictement inchangé.
"""

from services import authentic_tariff_service as svc


def test_zaf_crawled_index_is_no_longer_empty():
    index = svc.load_crawled_position_index("ZAF")
    assert index, "load_crawled_position_index('ZAF') ne doit plus être vide"
    assert "020110" in index


def test_zaf_dd_rate_comes_from_the_sars_crawl_not_etl_fallback():
    """020110 (carcasses de mouton) a 40% chez SARS (colonne GENERAL) —
    doit être la valeur restituée, via la clé canonique DD."""
    entry = svc.load_crawled_position_index("ZAF")["020110"]
    assert "GENERAL" in entry["taxes"]
    assert entry["taxes"]["GENERAL"]["rate"] == 40.0

    result = svc.calculate_import_taxes(
        country_iso3="ZAF",
        hs_code="020110",
        cif_value=100_000.0,
        language="fr",
        origin_country="EGY",
    )
    assert "error" not in result
    assert result["rates"]["dd_rate_pct"] == 40.0


def test_zaf_afcfta_column_is_not_flattened_to_a_default():
    """La colonne AfCFTA de SARS varie réellement par produit (garde-fou
    contre un taux préférentiel générique appliqué par défaut)."""
    index = svc.load_crawled_position_index("ZAF")
    rates = {
        entry["taxes"]["AfCFTA"]["rate"] for entry in index.values() if "AfCFTA" in entry["taxes"]
    }
    assert len(rates) > 1, "la colonne AfCFTA ne doit pas être une valeur unique appliquée partout"


def test_dza_index_schema_is_unaffected():
    """Contrôle négatif : le schéma DZA (sub_positions/hs_code) doit
    continuer à s'indexer exactement comme avant ce correctif."""
    index = svc.load_crawled_position_index("DZA")
    assert index
    sample_code = next(iter(index))
    assert index[sample_code].get("hs_code") or index[sample_code].get("taxes")
