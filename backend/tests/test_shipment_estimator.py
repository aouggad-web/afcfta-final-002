"""Tests du dimensionnement conteneur à partir de la valeur FOB."""

import math

from services import shipment_estimator as se


def test_small_fob_single_teu():
    # Cacao (SH 1801, cours mondial ICE Cocoa ~5.88 USD/kg) :
    # 50 000 USD -> ~8.5 t -> 1 conteneur 20'.
    r = se.estimate_shipment(50000, "1801")
    assert r["available"] is True
    assert r["weight_source"] == "estimé"
    assert r["container_type"] == "teu"
    assert r["containers_needed"] == 1
    assert r["value_to_weight"]["classification_source"] == "cours_mondial"


def test_large_fob_multiple_feu():
    # 2 M USD de cacao -> plusieurs conteneurs 40'.
    r = se.estimate_shipment(2_000_000, "1801")
    assert r["container_type"] == "feu"
    assert r["containers_needed"] >= 2
    # Cohérence : nb = ceil(poids / capacité).
    assert r["containers_needed"] == math.ceil(r["weight_kg"] / r["container_capacity_kg"])


def test_heavy_cheap_commodity_more_containers_than_light_expensive():
    # Même valeur FOB : un minerai (lourd, bon marché) exige beaucoup plus de
    # conteneurs qu'un produit électronique (léger, cher).
    ore = se.estimate_shipment(500_000, "2601")  # minerai de fer, cours mondial
    electronics = se.estimate_shipment(500_000, "8517")  # chap. 85, estimation
    assert ore["weight_kg"] > electronics["weight_kg"]
    assert ore["containers_needed"] > electronics["containers_needed"]


def test_weight_override_ignores_value_ratio():
    r = se.estimate_shipment(999, "1801", weight_kg_override=60000)
    assert r["weight_source"] == "fourni"
    assert r["is_estimate"] is False
    assert r["value_to_weight"] is None
    # 60 t -> 40' (26,4 t) -> 3 conteneurs.
    assert r["container_type"] == "feu"
    assert r["containers_needed"] == 3


def test_no_value_no_weight_unavailable():
    r = se.estimate_shipment(None, "1801")
    assert r["available"] is False


def test_unknown_chapter_uses_default_ratio():
    r = se.usd_per_kg_for_hs("9999")
    assert r["usd_per_kg"] == se._DEFAULT_USD_PER_KG
    assert r["is_estimate"] is True
    assert r["classification_source"] == "estimation_chapitre"
    assert r["negotiation"]["usable_as_price_reference"] is False


def test_world_market_benchmark_matched_by_6_digit_hs_takes_priority():
    # Café Arabica (090111) doit matcher le cours ICE Coffee C 6 chiffres,
    # pas retomber sur l'estimation par chapitre 09.
    r = se.usd_per_kg_for_hs("090111")
    assert r["classification_source"] == "cours_mondial"
    assert r["hs_match"] == "090111"
    assert r["commodity"].startswith("Café Arabica")
    assert r["is_estimate"] is False
    assert r["negotiation"]["usable_as_price_reference"] is True
    assert r["negotiation"]["caveat"]


def test_world_market_benchmark_matched_by_4_digit_hs():
    r = se.usd_per_kg_for_hs("7403.10")  # cuivre affiné, avec un sous-code
    assert r["classification_source"] == "cours_mondial"
    assert r["hs_match"] == "7403"
    assert r["commodity"].startswith("Cuivre")
    assert r["usd_per_kg"] == 13.335


def test_robusta_coffee_not_covered_by_arabica_benchmark():
    # Le Robusta (090121) n'est pas dans _WORLD_MARKET_BENCHMARKS -> retombe
    # sur l'estimation par chapitre (09), pas sur le cours Arabica.
    r = se.usd_per_kg_for_hs("090121")
    assert r["classification_source"] == "estimation_chapitre"
    assert r["hs_chapter"] == "09"


def test_gold_benchmark_used_as_negotiation_reference_end_to_end():
    r = se.estimate_shipment(1_000_000, "7108")
    assert r["value_to_weight"]["classification_source"] == "cours_mondial"
    assert r["negotiation_reference"] is not None
    assert r["negotiation_reference"]["commodity"].startswith("Or")
    assert r["negotiation_reference"]["caveat"]


def test_chapter_estimate_has_no_negotiation_reference():
    r = se.estimate_shipment(500_000, "8517")  # électronique, estimation chapitre
    assert r["value_to_weight"]["classification_source"] == "estimation_chapitre"
    assert r["negotiation_reference"] is None


def test_apply_live_benchmarks_overrides_quote_but_keeps_business_note():
    static = {
        "090111": {
            "commodity": "Café Arabica",
            "benchmark": "ICE Coffee C",
            "raw_quote": "315.24 ¢/lb",
            "as_of": "2026-07-08",
            "usd_per_kg": 6.9499,
            "note": "Cours Arabica uniquement — Robusta non couvert.",
        }
    }
    live = {
        "090111": {
            "commodity": "Café Arabica (vert, non torréfié, non décaféiné)",
            "benchmark": "ICE Coffee C (contrat rapproché)",
            "raw_quote": "320.1 ¢/lb",
            "as_of": "2026-07-10",
            "usd_per_kg": 7.0571,
        }
    }
    merged = se._apply_live_benchmarks(static, live)
    assert merged["090111"]["usd_per_kg"] == 7.0571
    assert merged["090111"]["as_of"] == "2026-07-10"
    assert merged["090111"]["refresh"].startswith("auto")
    # La note métier statique (Robusta) survit au rafraîchissement.
    assert "Robusta" in merged["090111"]["note"]
    # L'original n'est pas muté.
    assert static["090111"]["usd_per_kg"] == 6.9499


def test_apply_live_benchmarks_rejects_invalid_quotes():
    static = {"1801": {"commodity": "Cacao", "usd_per_kg": 5.877}}
    live = {
        "1801": {"usd_per_kg": 0},  # nul -> ignoré
        "7403": {"usd_per_kg": "13.3"},  # non numérique -> ignoré
        "9999": {"commodity": "X"},  # sans cours -> ignoré
    }
    merged = se._apply_live_benchmarks(static, live)
    assert merged["1801"]["usd_per_kg"] == 5.877
    assert "7403" not in merged
    assert "9999" not in merged


def test_load_live_benchmarks_missing_or_corrupt_file_returns_empty(tmp_path):
    assert se._load_live_benchmarks(str(tmp_path / "absent.json")) == {}
    bad = tmp_path / "bad.json"
    bad.write_text("{pas du json", encoding="utf-8")
    assert se._load_live_benchmarks(str(bad)) == {}
    no_key = tmp_path / "nokey.json"
    no_key.write_text('{"autre": 1}', encoding="utf-8")
    assert se._load_live_benchmarks(str(no_key)) == {}


# ── Tier « valeur unitaire observée » (flux commercial réel OEC/BACI) ──────────
#
# Bug signalé : l'export de médicaments (SH 300490, chapitre 30) vers l'Algérie
# affichait un indice figé de 60 USD/kg — l'estimation par chapitre générique,
# alors qu'un flux réel (importations algériennes observées pour ce SH précis)
# était disponible et bien plus spécifique. Ces tests couvrent le nouveau palier
# intermédiaire de la cascade : cours mondial > valeur unitaire observée >
# estimation par chapitre.


def test_observed_unit_value_none_without_data():
    assert se.observed_unit_value("300490", None, None) is None
    assert se.observed_unit_value("300490", 0, 100) is None
    assert se.observed_unit_value("300490", 1000, 0) is None


def test_observed_unit_value_plausible_within_chapter_band():
    # Algérie importe (hypothèse) 50 M USD / 2 000 t de SH 300490 -> 25 USD/kg,
    # dans la bande plausible autour du repère de chapitre 30 (60 USD/kg).
    r = se.observed_unit_value(
        "300490", 50_000_000, 2000, basis="importations de DZA, toutes origines"
    )
    assert r is not None
    assert r["plausible"] is True
    assert r["usd_per_kg"] == 25.0
    assert r["note"] is None


def test_observed_unit_value_implausible_outside_band_flagged_not_used():
    # 50 M USD / 1 t -> 50 000 USD/kg, très au-delà de ×20 le repère de
    # chapitre (60 USD/kg) : quasi certainement une erreur de déclaration
    # (quantité omise/mal unitée) -> signalée, jamais utilisée aveuglément.
    r = se.observed_unit_value("300490", 50_000_000, 1)
    assert r is not None
    assert r["plausible"] is False
    assert r["note"] is not None
    assert "erreur de déclaration" in r["note"]


def test_usd_per_kg_for_hs_uses_observed_tier_when_plausible():
    # Sans flux observé : repli sur l'estimation générique par chapitre (bug
    # signalé -> 60 USD/kg plat pour tout le chapitre 30).
    baseline = se.usd_per_kg_for_hs("300490")
    assert baseline["classification_source"] == "estimation_chapitre"
    assert baseline["usd_per_kg"] == 60.0

    # Avec un flux réel observé et plausible : le ratio devient spécifique au
    # produit et au marché, plus fiable que le chapitre générique.
    enriched = se.usd_per_kg_for_hs(
        "300490",
        observed_value_usd=50_000_000,
        observed_quantity_tonnes=2000,
        observed_basis="importations de DZA, toutes origines, 2024",
        observed_year=2024,
    )
    assert enriched["classification_source"] == "valeur_unitaire_observee"
    assert enriched["usd_per_kg"] == 25.0
    assert enriched["basis"] == "importations de DZA, toutes origines, 2024"
    assert enriched["negotiation"]["usable_as_price_reference"] is True


def test_usd_per_kg_for_hs_falls_back_to_chapter_when_observed_implausible():
    r = se.usd_per_kg_for_hs("300490", observed_value_usd=50_000_000, observed_quantity_tonnes=1)
    assert r["classification_source"] == "estimation_chapitre"
    assert r["usd_per_kg"] == 60.0
    # Transparence : la valeur écartée reste tracée, jamais silencieuse.
    assert r.get("discarded_observed_value")


def test_usd_per_kg_for_hs_world_benchmark_still_wins_over_observed():
    # Le cours mondial coté (tier 1, curé/vérifié) reste prioritaire même si
    # un flux observé plausible est fourni.
    r = se.usd_per_kg_for_hs("1801", observed_value_usd=1_000_000, observed_quantity_tonnes=170)
    assert r["classification_source"] == "cours_mondial"


def test_estimate_shipment_forwards_observed_tier_end_to_end():
    r = se.estimate_shipment(
        2_000_000,
        "300490",
        observed_value_usd=50_000_000,
        observed_quantity_tonnes=2000,
        observed_basis="importations de DZA, toutes origines, 2024",
    )
    assert r["available"] is True
    assert r["value_to_weight"]["classification_source"] == "valeur_unitaire_observee"
    # 2 M USD / 25 USD/kg = 80 000 kg -> conteneurs 40'.
    assert r["weight_kg"] == 80000.0
    assert r["negotiation_reference"]["classification_source"] == "valeur_unitaire_observee"
    assert r["negotiation_reference"]["basis"] == "importations de DZA, toutes origines, 2024"
