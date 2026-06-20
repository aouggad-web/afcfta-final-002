"""Régression : l'endpoint authentique (calculate_import_taxes) doit renvoyer
`taxes_breakdown`, `taxes_summary` et `currency` (bi-devise) pour alimenter le
composant TaxBreakdownDual du frontend.
"""
import os
import sys
from datetime import datetime, timezone

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import currencies.service as currency_service
import exchange_rates as exchange_rates_module
from services import authentic_tariff_service as svc


class _FakeCurrency:
    currency_code = "KES"
    currency_name_fr = "Shilling kényan"
    currency_symbol = "KSh"


class _FakeRate:
    def __init__(self, rate):
        self.rate = rate
        self.source = "test_provider"
        self.timestamp = datetime(2026, 1, 1, tzinfo=timezone.utc)


class _FakeFxService:
    def __init__(self, rate=None, raise_exc=False):
        self._rate = rate
        self._raise = raise_exc

    def get_rate(self, base, quote):
        if self._raise:
            raise RuntimeError("FX provider indisponible")
        return _FakeRate(self._rate)


_SYNTHETIC_LINE = {
    "dd_rate": 20.0,
    "vat_rate": 15.0,
    "zlecaf_rate": 0.0,
    "other_taxes_rate": 0.0,
    "taxes_detail": {},
    "description_fr": "Produit test",
    "description_en": "Test product",
    "fiscal_advantages": [],
    "administrative_formalities": [],
}


@pytest.fixture
def synthetic_calc(monkeypatch):
    """calculate_import_taxes sur une ligne déterministe (profil par défaut :
    DD sur CIF, TVA sur CIF+DD). CIF=1000, DD=20%, TVA=15%, ZLECAf DD=0%."""
    monkeypatch.setattr(svc, "_get_postgres_provider", lambda: None)
    monkeypatch.setattr(svc, "load_country_tariffs", lambda iso3: {"generated_at": "2025-01-01"})
    monkeypatch.setattr(svc, "get_tariff_line", lambda iso3, hs6: dict(_SYNTHETIC_LINE))
    monkeypatch.setattr(svc, "load_crawled_position_index", lambda iso3: None)
    monkeypatch.setattr(svc, "get_sub_positions", lambda *a, **k: [])
    monkeypatch.setattr(currency_service, "get_by_country", lambda code: _FakeCurrency())
    return monkeypatch


def test_breakdown_and_currency_present_when_fx_available(synthetic_calc):
    synthetic_calc.setattr(exchange_rates_module, "get_service", lambda: _FakeFxService(rate=100.0))

    result = svc.calculate_import_taxes("KEN", "100190", 1000.0)

    assert "error" not in result
    assert {"taxes_breakdown", "taxes_summary", "currency"} <= set(result)

    breakdown = result["taxes_breakdown"]
    by_code = {b["code"]: b for b in breakdown}
    assert by_code["DD"]["category"] == "droit_douane"
    assert by_code["DD"]["amount_npf"] == 200.0
    assert by_code["DD"]["amount_zlecaf"] == 0.0
    assert by_code["DD"]["affected_by_zlecaf"] is True
    # TVA recalculée sur une base réduite (DD retiré) → montant change aussi.
    assert by_code["TVA"]["category"] == "tva"
    assert by_code["TVA"]["amount_npf"] == 180.0      # 15% de (1000+200)
    assert by_code["TVA"]["amount_zlecaf"] == 150.0   # 15% de 1000
    assert by_code["TVA"]["affected_by_zlecaf"] is True

    # Bi-devise : taux appliqué (1 USD = 100 KES) sur chaque montant.
    assert by_code["DD"]["amount_npf_local"] == 20000.0

    currency = result["currency"]
    assert currency["available"] is True
    assert currency["local_code"] == "KES"
    assert currency["usd_to_local_rate"] == 100.0
    assert currency["value_local"] == 100000.0
    assert "summary_local" in currency
    assert currency["summary_local"]["npf"]["cout_total"] == 138000.0  # 1380 × 100


def test_currency_degrades_to_usd_when_fx_unavailable(synthetic_calc):
    synthetic_calc.setattr(exchange_rates_module, "get_service", lambda: _FakeFxService(raise_exc=True))

    result = svc.calculate_import_taxes("KEN", "100190", 1000.0)

    # Le détail reste présent (USD uniquement) ; pas de plantage.
    assert result["taxes_breakdown"]
    assert result["taxes_summary"]
    currency = result["currency"]
    assert currency["available"] is False
    assert currency["usd_to_local_rate"] is None
    # Aucun montant local n'est ajouté lorsque le taux est indisponible.
    assert "amount_npf_local" not in result["taxes_breakdown"][0]


_DZA_LINE = {
    "dd_rate": 30.0,
    "vat_rate": 19.0,
    "zlecaf_rate": 0.0,
    "other_taxes_rate": 0.0,
    "taxes_detail": {
        "DAPS": {"rate": 30.0, "label": "Droit Additionnel Provisoire de Sauvegarde"},
        "TCS":  {"rate": 3.0,  "label": "Taxe Complémentaire de Sauvegarde"},
        "PRCT": {"rate": 2.0,  "label": "Précompte (PRCT)"},
    },
    "description_fr": "Viande bovine",
    "description_en": "Bovine meat",
    "fiscal_advantages": [],
    "administrative_formalities": [],
}


@pytest.fixture
def dza_calc(monkeypatch):
    """calculate_import_taxes sur une ligne DZA déterministe.
    CIF=10000 ; DAPS=30%, DD=30%, TCS=3%, TVA=19%, PRCT=2% ; ZLECAf DD=0%."""
    monkeypatch.setattr(svc, "_get_postgres_provider", lambda: None)
    monkeypatch.setattr(svc, "load_country_tariffs", lambda iso3: {"generated_at": "2025-01-01"})
    monkeypatch.setattr(svc, "get_tariff_line", lambda iso3, hs6: dict(_DZA_LINE))
    monkeypatch.setattr(svc, "load_crawled_position_index", lambda iso3: None)
    monkeypatch.setattr(svc, "get_sub_positions", lambda *a, **k: [])
    monkeypatch.setattr(currency_service, "get_by_country", lambda code: None)
    return monkeypatch


def test_dza_daps_treated_as_customs_duty_and_reduced_under_zlecaf(dza_calc):
    """DAPS = droit de douane, réduit sous ZLECAf comme le DD (mêmes 0% ici)."""
    result = svc.calculate_import_taxes("DZA", "020110", 10000.0)
    by_code = {b["code"]: b for b in result["taxes_breakdown"]}

    assert by_code["DAPS"]["category"] == "droit_douane"
    assert by_code["DAPS"]["amount_npf"] == 3000.0
    assert by_code["DAPS"]["amount_zlecaf"] == 0.0
    assert by_code["DAPS"]["affected_by_zlecaf"] is True

    assert by_code["DD"]["category"] == "droit_douane"
    assert by_code["DD"]["amount_zlecaf"] == 0.0

    # Les deux droits cumulés alimentent la catégorie droit_douane.
    assert result["taxes_summary"]["npf"]["droit_douane"] == 6000.0
    assert result["taxes_summary"]["zlecaf"]["droit_douane"] == 0.0
    assert result["taxes_summary"]["economie_droits"] == 6000.0


def test_dza_precompte_label_base_and_order(dza_calc):
    """PRCT = « Précompte (PRCT) », 2%, calculé après la TVA sur la valeur
    globale TVA incluse mais HORS DAPS = CIF + DD + TCS + TVA."""
    result = svc.calculate_import_taxes("DZA", "020110", 10000.0)
    by_code = {b["code"]: b for b in result["taxes_breakdown"]}

    prct = by_code["PRCT"]
    assert prct["name"] == "Précompte (PRCT)"
    assert prct["category"] == "autre_taxe"
    assert prct["base_expr"] == "CIF + DD + TCS + TVA"
    # NPF : 2% de (10000 + 3000 + 300 + 3040) = 326.80
    assert prct["amount_npf"] == 326.8
    # ZLECAf : DD/DAPS exonérés → 2% de (10000 + 0 + 300 + 1900) = 244.0
    assert prct["amount_zlecaf"] == 244.0

    # Le PRCT est calculé APRÈS la TVA dans la cascade.
    codes_in_order = [b["code"] for b in result["taxes_breakdown"]]
    assert codes_in_order.index("PRCT") > codes_in_order.index("TVA")


def test_dza_tcs_kept_at_3_percent_unaffected_by_zlecaf(dza_calc):
    """TCS conservée à 3% (base CIF), non affectée par la ZLECAf."""
    result = svc.calculate_import_taxes("DZA", "020110", 10000.0)
    by_code = {b["code"]: b for b in result["taxes_breakdown"]}

    tcs = by_code["TCS"]
    assert tcs["category"] == "autre_taxe"
    assert tcs["rate_npf_pct"] == 3.0
    assert tcs["amount_npf"] == 300.0
    assert tcs["amount_zlecaf"] == 300.0
    assert tcs["affected_by_zlecaf"] is False


def test_dza_daps_exempt_under_zlecaf_even_when_dd_is_zero(monkeypatch):
    """Edge case : un produit DZA sans DD (DD=0) mais avec DAPS doit voir le
    DAPS exonéré sous ZLECAf (le DAPS est un droit de douane)."""
    line = dict(_DZA_LINE)
    line["dd_rate"] = 0.0
    line["zlecaf_rate"] = 0.0
    line["taxes_detail"] = {
        "DAPS": {"rate": 30.0, "label": "Droit Additionnel Provisoire de Sauvegarde"},
        "TCS":  {"rate": 3.0,  "label": "Taxe Complémentaire de Sauvegarde"},
        "TVA":  {"rate": 19.0, "label": "Taxe sur la Valeur Ajoutée"},
    }
    monkeypatch.setattr(svc, "_get_postgres_provider", lambda: None)
    monkeypatch.setattr(svc, "load_country_tariffs", lambda iso3: {"generated_at": "2025-01-01"})
    monkeypatch.setattr(svc, "get_tariff_line", lambda iso3, hs6: dict(line))
    monkeypatch.setattr(svc, "load_crawled_position_index", lambda iso3: None)
    monkeypatch.setattr(svc, "get_sub_positions", lambda *a, **k: [])
    monkeypatch.setattr(currency_service, "get_by_country", lambda code: None)

    result = svc.calculate_import_taxes("DZA", "020110", 10000.0)
    by_code = {b["code"]: b for b in result["taxes_breakdown"]}

    assert by_code["DAPS"]["amount_npf"] == 3000.0
    assert by_code["DAPS"]["amount_zlecaf"] == 0.0
    assert by_code["DAPS"]["affected_by_zlecaf"] is True


def test_etl_list_format_taxes_detail_does_not_crash(monkeypatch):
    """Régression : une ligne ETL fournissant `taxes_detail` au format LISTE
    doit être normalisée sans planter (la copie défensive ne s'applique qu'aux
    dicts)."""
    line = {
        "dd_rate": 20.0,
        "vat_rate": 15.0,
        "zlecaf_rate": 0.0,
        "other_taxes_rate": 0.0,
        "taxes_detail": [
            {"tax": "D.D", "rate": 20.0, "observation": "Droit de douane"},
            {"tax": "TVA", "rate": 15.0, "observation": "TVA"},
        ],
        "description_fr": "Produit ETL",
        "description_en": "ETL product",
        "fiscal_advantages": [],
        "administrative_formalities": [],
    }
    monkeypatch.setattr(svc, "_get_postgres_provider", lambda: None)
    monkeypatch.setattr(svc, "load_country_tariffs", lambda iso3: {"generated_at": "2025-01-01"})
    monkeypatch.setattr(svc, "get_tariff_line", lambda iso3, hs6: dict(line))
    monkeypatch.setattr(svc, "load_crawled_position_index", lambda iso3: None)
    monkeypatch.setattr(svc, "get_sub_positions", lambda *a, **k: [])
    monkeypatch.setattr(currency_service, "get_by_country", lambda code: None)

    result = svc.calculate_import_taxes("KEN", "100190", 1000.0)

    assert "error" not in result
    by_code = {b["code"]: b for b in result["taxes_breakdown"]}
    assert by_code["DD"]["amount_npf"] == 200.0
    assert by_code["DD"]["amount_zlecaf"] == 0.0


def test_dza_precompte_label_normalized_in_legacy_fields(dza_calc):
    """Le PRCT renvoyé (taxes_detail + individual_taxes) doit porter l'intitulé
    officiel, même si la donnée crawled utilisait un ancien libellé."""
    line = dict(_DZA_LINE)
    line["taxes_detail"] = dict(_DZA_LINE["taxes_detail"])
    line["taxes_detail"]["PRCT"] = {"rate": 2.0, "label": "Prélèvement à la Compensation du Transport"}
    dza_calc.setattr(svc, "get_tariff_line", lambda iso3, hs6: dict(line))

    result = svc.calculate_import_taxes("DZA", "020110", 10000.0)

    assert result["taxes_detail"]["PRCT"]["label"] == "Précompte (PRCT)"
    prct_ind = next(t for t in result["individual_taxes"] if t["code"] == "PRCT")
    assert prct_ind["label"] == "Précompte (PRCT)"


def test_summary_totals_match_breakdown_rows(synthetic_calc):
    synthetic_calc.setattr(exchange_rates_module, "get_service", lambda: _FakeFxService(rate=100.0))

    result = svc.calculate_import_taxes("KEN", "100190", 1000.0)
    breakdown = result["taxes_breakdown"]
    summary = result["taxes_summary"]

    cat_map = {"droit_douane": "droit_douane", "tva": "tva", "autre_taxe": "autres_taxes"}
    for regime in ("npf", "zlecaf"):
        for cat, summ_key in cat_map.items():
            expected = round(sum(
                b[f"amount_{regime}"] for b in breakdown if b["category"] == cat
            ), 2)
            assert summary[regime][summ_key] == expected

    # Cohérence des agrégats dérivés.
    assert summary["economie_droits"] == round(
        summary["npf"]["droit_douane"] - summary["zlecaf"]["droit_douane"], 2
    )
    assert summary["economie_totale"] == round(
        summary["npf"]["cout_total"] - summary["zlecaf"]["cout_total"], 2
    )
