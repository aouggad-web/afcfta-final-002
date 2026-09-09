"""
Tests de l'adaptateur TEC CEDEAO (vague 1 — 15 pays).
"""

import json
import sys
from datetime import date
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from adapters.cedeao_tec_adapter import (
    CET_BANDS,
    COUNTRIES,
    UEMOA,
    CedeaoTecAdapter,
    run,
)
from schemas.canonical_model import DataStatus, DutyBasis, ReliabilityGrade

FIXTURE = Path(__file__).parent / "fixtures" / "cedeao_tec_sample.csv"


@pytest.fixture
def adapter():
    return CedeaoTecAdapter(str(FIXTURE), version_date=date(2022, 1, 1))


# ----------------------------------------------------------------------
# Parsing source
# ----------------------------------------------------------------------


def test_parse_source_counts(adapter):
    rows = adapter.parse_source()
    # 6 lignes valides (dont une avec points dans le code), 1 parasite ignorée
    assert len(rows) == 6
    assert adapter.stats["skipped"] == 1


def test_band_to_rate_mapping(adapter):
    rates = {r["code"]: r["rate"] for r in adapter.parse_source()}
    assert rates["0101210000"] == 0.0  # catégorie 0
    assert rates["0201100000"] == 5.0  # catégorie 1
    assert rates["2523210000"] == 10.0  # catégorie 2
    assert rates["6309000000"] == 20.0  # catégorie 3
    assert rates["2402202000"] == 35.0  # catégorie 4


def test_code_normalisation(adapter):
    codes = [r["code"] for r in adapter.parse_source()]
    # '0102.29.0000' nettoyé en 10 chiffres
    assert "0102290000" in codes


def test_rate_column_takes_precedence(tmp_path):
    src = tmp_path / "tec.csv"
    src.write_text(
        "HS Code,Description,Category,Duty Rate\n"
        "0101210000,Pure-bred breeding horses,1,5\n"
        "9999999999,Special line,3,35\n",
        encoding="utf-8",
    )
    adapter = CedeaoTecAdapter(str(src))
    rows = adapter.parse_source()
    assert rows[0]["rate"] == 5.0
    # taux 35 incohérent avec la bande 3 (20 %) → compté, taux conservé
    assert rows[1]["rate"] == 35.0
    assert adapter.stats["band_mismatch"] == 1


def test_missing_columns_raise(tmp_path):
    src = tmp_path / "bad.csv"
    src.write_text("Foo;Bar\n1;2\n", encoding="utf-8")
    with pytest.raises(ValueError, match="Colonnes introuvables"):
        CedeaoTecAdapter(str(src)).parse_source()


# ----------------------------------------------------------------------
# Transformation canonique
# ----------------------------------------------------------------------


def test_provenance_partial_b(adapter):
    line = next(adapter.transform("SEN"))
    assert line.provenance.data_status == DataStatus.PARTIAL
    assert line.provenance.reliability == ReliabilityGrade.B
    assert line.schema_version == "4.0"
    assert line.provenance.version_date == date(2022, 1, 1)


def test_uemoa_member_has_community_levies(adapter):
    line = next(adapter.transform("SEN"))  # SEN ∈ UEMOA
    codes = {m.code for m in line.measures}
    assert {"D.D", "R.S", "PC-CEDEAO", "PCS-UEMOA", "PUA", "T.V.A"} <= codes


def test_non_uemoa_member_has_no_uemoa_levies(adapter):
    line = next(adapter.transform("GHA"))  # GHA ∉ UEMOA
    codes = {m.code for m in line.measures}
    assert "PC-CEDEAO" in codes
    assert "PUA" in codes  # AU levy s'applique à tous les membres
    assert "R.S" not in codes
    assert "PCS-UEMOA" not in codes
    # taxes nationales ghanéennes documentées
    assert {"NHIL", "GETFund"} <= codes


def test_vat_basis_includes_upstream(adapter):
    line = next(adapter.transform("CIV"))
    vat = next(m for m in line.measures if m.sequence == 90)
    assert vat.basis == DutyBasis.CIF_PLUS_INCLUDED
    assert "D.D" in vat.basis_includes
    assert vat.code not in vat.basis_includes  # jamais auto-référente


def test_vat_rate_per_country(adapter):
    nga = next(adapter.transform("NGA"))
    vat = next(m for m in nga.measures if m.sequence == 90)
    assert vat.code == "VAT" and vat.rate_pct == 7.5


def test_zlecaf_and_etls_advantages(adapter):
    line = next(adapter.transform("BEN"))
    agreements = {a.agreement for a in line.fiscal_advantages}
    assert {"CEDEAO/SLEC", "ZLECAf"} <= agreements
    dd = next(m for m in line.measures if m.code == "D.D")
    assert dd.is_zlecaf_applicable is True


def test_duty_free_line_is_exempt(adapter):
    line = next(adapter.transform("MLI"))  # cat 0 → DD 0 %
    dd = next(m for m in line.measures if m.code == "D.D")
    assert dd.rate_pct == 0.0
    assert dd.rate_type.value == "EXEMPT"


def test_rejects_non_member():
    with pytest.raises(ValueError, match="membre de la CEDEAO"):
        next(CedeaoTecAdapter(str(FIXTURE)).transform("DZA"))


# ----------------------------------------------------------------------
# Émission par pays (run)
# ----------------------------------------------------------------------


def test_run_emits_all_15_countries(tmp_path):
    stats = run(str(FIXTURE), str(tmp_path))
    assert set(stats["countries"]) == set(COUNTRIES)
    assert all(n == 6 for n in stats["countries"].values())
    sample = json.loads((tmp_path / "NGA_canonical.jsonl").read_text().splitlines()[0])
    assert sample["provenance"]["data_status"] == "PARTIAL"
    assert sample["commodity"]["country_iso3"] == "NGA"


def test_run_country_filter(tmp_path):
    stats = run(str(FIXTURE), str(tmp_path), countries=["sen", "GHA"])
    assert set(stats["countries"]) == {"SEN", "GHA"}
    assert not (tmp_path / "NGA_canonical.jsonl").exists()


def test_referentials_consistency():
    assert len(COUNTRIES) == 15
    assert UEMOA <= set(COUNTRIES)
    assert len(UEMOA) == 8
    assert CET_BANDS == {0: 0.0, 1: 5.0, 2: 10.0, 3: 20.0, 4: 35.0}


# ----------------------------------------------------------------------
# CSV enrichi — colonnes TVA, TSB, PUA universelle
# ----------------------------------------------------------------------


def test_pua_applies_to_all_members(adapter):
    for iso3 in ["SEN", "GHA", "NGA", "LBR"]:  # UEMOA, non-UEMOA, Anglophone
        line = next(adapter.transform(iso3))
        codes = {m.code for m in line.measures}
        assert "PUA" in codes, f"PUA absent pour {iso3}"


def test_tva_override_from_enriched_csv(tmp_path):
    src = tmp_path / "tec_enrichi.csv"
    src.write_text(
        "Code_SH;Designation;DD;TVA\n"
        "0201100000;Viande bovine fraîche;20;9\n"
        "0101210000;Chevaux reproducteurs;5;0\n",
        encoding="utf-8",
    )
    adapter = CedeaoTecAdapter(str(src))
    lines = {l.commodity.national_code: l for l in adapter.transform("CIV")}
    vat_beef = next(m for m in lines["0201100000"].measures if m.sequence == 90)
    vat_horse = next(m for m in lines["0101210000"].measures if m.sequence == 90)
    assert vat_beef.rate_pct == 9.0
    assert vat_horse.rate_pct == 0.0
    assert vat_horse.rate_type.value == "EXEMPT"


def test_tsb_specific_duty_from_enriched_csv(tmp_path):
    src = tmp_path / "tec_tsb.csv"
    src.write_text(
        "Code_SH;Designation;DD;TVA;TSB\n"
        "2203001000;Bières de malt en récipient ≤10 L;20;18;17\n",
        encoding="utf-8",
    )
    adapter = CedeaoTecAdapter(str(src))
    line = next(adapter.transform("CIV"))
    tsb = next((m for m in line.measures if m.code == "TSB"), None)
    assert tsb is not None
    assert tsb.rate_type.value == "SPECIFIC"
    assert tsb.specific_amount == 17.0
