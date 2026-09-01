"""Régime TVA (exonération / taux zéro / standard) — engine.national_customs_calculation.

Corrige un bug constaté : les 307 exonérations et 53 lignes à taux zéro
TVA du Kenya, déjà collectées dans ``data/kenya/vat_measures.json``,
n'étaient consultées par aucun calcul — un bien légalement exonéré était
facturé au taux standard (16%). Ce module vérifie que les enregistrements
disposant d'un code SH explicite priment désormais correctement sur le
taux standard, et que les enregistrements à description seule (sans code
SH) ne s'appliquent jamais automatiquement.
"""

from datetime import date
from pathlib import Path

from engine.national_customs_calculation import NationalFiscalStore

_KENYA_DATA = Path(__file__).resolve().parents[2] / "data" / "kenya"


def _store() -> NationalFiscalStore:
    return NationalFiscalStore(_KENYA_DATA)


def test_explicit_exemption_overrides_standard_rate():
    """Sperme bovin 0511.10.00 — VAT Act, Annexe 1 partie I, para 1 :
    exonéré, jamais 16%."""
    store = _store()
    result = store.vat_treatment(date(2026, 7, 25), "0511100000")
    assert result is not None
    assert result["treatment"] == "EXEMPT"
    assert result["rate_pct"] == 0.0
    assert result["legal_reference"]
    assert result["source_id"]


def test_explicit_zero_rated_overrides_standard_rate():
    store = _store()
    zero_rated = _store().vat.get("vat_zero_rated", [])
    explicit = next(r for r in zero_rated if r.get("hs_codes_explicit"))
    code = explicit["hs_codes_explicit"][0].replace(".", "")
    result = store.vat_treatment(date(2026, 7, 25), code)
    assert result is not None
    assert result["treatment"] == "ZERO_RATED"
    assert result["rate_pct"] == 0.0


def test_ordinary_line_still_gets_standard_rate():
    store = _store()
    result = store.vat_treatment(date(2026, 7, 25), "8703229090")
    assert result is not None
    assert result["treatment"] == "STANDARD"
    assert result["rate_pct"] == 16.0


def test_description_only_exemption_never_auto_applies():
    """Une exonération sans code SH explicite (ex. biens destinés à une
    boutique hors taxes agréée) ne doit jamais correspondre à une ligne
    précise par accident : elle est absente du filtrage par ``hs_match``,
    donc ne peut pas faire baisser un taux à tort."""
    store = _store()
    description_only = [
        r for r in store.vat.get("vat_exemptions", []) if not r.get("hs_codes_explicit")
    ]
    assert description_only, "le corpus doit contenir des exonérations à description seule"
    # Une ligne quelconque, non listée nulle part, reste au taux standard —
    # aucune des 148 exonérations à description seule ne doit s'y substituer.
    result = store.vat_treatment(date(2026, 7, 25), "9999999999")
    assert result is not None
    assert result["treatment"] == "STANDARD"


def test_calculate_national_customs_applies_zero_vat_on_exempt_line():
    from engine.legal_override_engine import load_legal_measures
    from engine.national_customs_calculation import calculate_national_customs

    measures = load_legal_measures(
        Path(__file__).resolve().parents[2] / "data" / "eac" / "legal_overrides.json"
    )
    store = _store()
    result = calculate_national_customs(
        jurisdiction="KEN",
        hs_code="0511100000",
        on_date=date(2026, 7, 25),
        customs_value=10000,
        base_cet_rate=0,
        measures=measures,
        fiscal_store=store,
        coverage_complete=False,
        currency_code="USD",
    )
    assert result["vat"]["treatment"] == "EXEMPT"
    assert result["vat"]["amount"] == 0.0
