"""
Tests du pipeline tariff_crawl (authentique uniquement).

Tournent sans réseau ni MongoDB. Vérifient le manifeste (54 pays), le
validateur d'authenticité (rejet du vide/estimé), la normalisation canonique,
et la classification de couverture.
"""

import pytest
from tariff_crawl.canonical import (
    build_file,
    normalize_position,
    validate_authenticity,
)
from tariff_crawl.crawlers import AUTHENTIC_CRAWLERS, register
from tariff_crawl.manifest import AUTHENTIC_PROVENANCES, Provenance, build_manifest

# ----------------------------- manifest ------------------------------------


def test_manifest_covers_54_countries():
    m = build_manifest()
    assert len(m) == 54


def test_every_country_has_authentic_source_chain():
    m = build_manifest()
    for iso3, d in m.items():
        assert d["sources_chain"], f"{iso3} sans chaîne de source"
        # La chaîne se termine toujours par un repli authentique (OMC/WITS).
        provs = [s["provenance"] for s in d["sources_chain"]]
        assert Provenance.WTO_MFN_HS6.value in provs, iso3
        # Toutes les provenances de la chaîne sont authentiques.
        for p in provs:
            assert p in AUTHENTIC_PROVENANCES, f"{iso3}: provenance non authentique {p}"


def test_regional_blocs_assigned():
    m = build_manifest()
    assert m["KEN"]["regional_tariff"] == "CET EAC"
    assert m["NGA"]["regional_tariff"] == "TEC CEDEAO"
    assert m["CMR"]["regional_tariff"] == "TDC CEMAC"
    assert m["ZAF"]["regional_tariff"] == "SACU Common Tariff"


# --------------------------- normalisation ---------------------------------


def test_normalize_dict_taxes_label_form():
    raw = {
        "code": "0101210000",
        "designation": "Chevaux reproducteurs",
        "taxes": {"Droit d'Importation (DI)": "2.5 %", "TVA": "20 %"},
        "formalities": ["LICENCE D'IMPORTATION"],
    }
    n = normalize_position(raw, source="douane.gov.ma/adil")
    assert n["code_clean"] == "0101210000"
    di = next(t for t in n["taxes"] if "DI" in t["code"] or "Importation" in t["name"])
    assert di["rate_pct"] == 2.5
    assert n["formalities"] == ["LICENCE D'IMPORTATION"]


def test_normalize_dict_taxes_nested_form():
    raw = {
        "hs_code": "0102290000",
        "name": "Autres",
        "taxes": {"DD": {"name": "Droit de Douane", "rate": 0.0, "raw": "0%"}},
    }
    n = normalize_position(raw, source="customs.gov.eg")
    assert n["code_clean"] == "0102290000"
    assert n["taxes"][0]["code"] == "DD"
    assert n["taxes"][0]["rate_pct"] == 0.0


# ------------------------- validateur authenticité -------------------------


def _good_doc():
    return build_file(
        "MAR",
        "Maroc",
        provenance=Provenance.NATIONAL_CRAWL.value,
        source="douane.gov.ma/adil",
        source_url="https://www.douane.gov.ma",
        positions=[
            {
                "code": "0101210000",
                "designation": "x",
                "taxes": {"Droit d'Importation (DI)": "2.5 %"},
            }
        ],
    )


def test_validator_accepts_authentic_doc():
    ok, issues = validate_authenticity(_good_doc())
    assert ok, issues


def test_validator_rejects_empty():
    doc = _good_doc()
    doc["sub_positions"] = []
    ok, issues = validate_authenticity(doc)
    assert not ok
    assert any("vide" in i for i in issues)


def test_validator_rejects_missing_source():
    doc = _good_doc()
    doc["source"] = ""
    ok, issues = validate_authenticity(doc)
    assert not ok
    assert any("source" in i for i in issues)


def test_validator_rejects_missing_source_url():
    doc = _good_doc()
    doc.pop("source_url", None)
    ok, issues = validate_authenticity(doc)
    assert not ok
    assert any("source_url" in i for i in issues)


def test_validator_infers_provenance_from_position_tags():
    """Un crawl réel taggué seulement au niveau position (ex. DZA
    'crawled_authentic') doit être reconnu comme national_crawl."""
    doc = _good_doc()
    doc["source_quality"] = None
    doc["sub_positions"][0]["source_quality"] = "crawled_authentic"
    ok, issues = validate_authenticity(doc)
    assert ok, issues


def test_validator_rejects_estimated_positions():
    doc = _good_doc()
    doc["sub_positions"][0]["source_quality"] = "etl_computed"
    ok, issues = validate_authenticity(doc)
    assert not ok
    assert any("estimée" in i or "synth" in i for i in issues)


def test_validator_rejects_non_authentic_provenance():
    doc = _good_doc()
    doc["source_quality"] = "estimated"
    ok, issues = validate_authenticity(doc)
    assert not ok


# ----------------------------- registre ------------------------------------


def test_register_decorator():
    @register("ZZZ")
    def _fake():
        return _good_doc()

    assert "ZZZ" in AUTHENTIC_CRAWLERS
    assert AUTHENTIC_CRAWLERS["ZZZ"]()["country_code"] == "MAR"
    del AUTHENTIC_CRAWLERS["ZZZ"]


# ----------------------------- couverture ----------------------------------


def test_coverage_report_structure():
    from tariff_crawl.coverage import build_coverage_report

    r = build_coverage_report()
    assert r["total_countries"] == 54
    assert "by_provenance" in r
    # Les 4 pays à crawl national connu sont classés national_crawl.
    by_iso = {c["iso3"]: c for c in r["countries"]}
    for iso in ("DZA", "EGY", "MAR", "TUN"):
        assert by_iso[iso]["effective_provenance"] == Provenance.NATIONAL_CRAWL.value
