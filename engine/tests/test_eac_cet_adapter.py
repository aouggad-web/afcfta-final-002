"""
Tests du convertisseur et de l'adaptateur EAC CET 2022 (vague 1 — 8 pays).
"""

import json
import sys
from datetime import date
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.eac_cet_md_to_csv import parse, parse_rate, run as md_to_csv
from adapters.eac_cet_adapter import (
    EacCetAdapter, COUNTRIES, VAT_BY_COUNTRY, run,
)
from schemas.canonical_model import (
    DataStatus, ReliabilityGrade, DutyBasis, RateType, MeasureType,
)

FIXTURE_MD = Path(__file__).parent / "fixtures" / "eac_cet_sample.md"


@pytest.fixture
def csv_path(tmp_path):
    out = tmp_path / "eac_cet.csv"
    md_to_csv(str(FIXTURE_MD), str(out))
    return str(out)


@pytest.fixture
def adapter(csv_path):
    return EacCetAdapter(csv_path)


# ----------------------------------------------------------------------
# Convertisseur Markdown → CSV
# ----------------------------------------------------------------------

def test_parse_rate_formats():
    assert parse_rate("25%")["pct"] == "25"
    assert parse_rate("kg 25%")["pct"] == "25"          # cellule fusionnée
    assert parse_rate("25%25%")["pct"] == "25"          # artefact PDF
    mixed = parse_rate("75% or $345/MT whichever is higher")
    assert mixed == {"pct": "75", "specific": "345",
                     "specific_unit": "USD/MT",
                     "raw": "75% or $345/MT whichever is higher"}
    usd = parse_rate("35% or USD 0.40/kg whichever is higher")
    assert usd["specific"] == "0.40" and usd["specific_unit"] == "USD/kg"


def test_converter_counts(csv_path):
    rows, stats = parse(FIXTURE_MD)
    # 5 lignes normales + 2 SI résolues par le Schedule 2 ; la ligne
    # 9999.99.00 sans taux est exclue
    assert len(rows) == 7
    assert stats["schedule2_overrides"] == 2
    assert stats["si_unresolved"] == 0
    codes = {r["Code_SH"] for r in rows}
    assert "99999900" not in codes


def test_schedule2_overrides_si(csv_path):
    rows, _ = parse(FIXTURE_MD)
    by_code = {r["Code_SH"]: r for r in rows}
    assert by_code["04021000"]["DD"] == "60"
    assert by_code["04021000"]["Sensible"] == "1"
    rice = by_code["10061000"]
    assert rice["DD"] == "75"
    assert rice["DD_specifique"] == "345"
    assert rice["DD_unite_specifique"] == "USD/MT"


def test_merged_unit_rate_cell(csv_path):
    rows, _ = parse(FIXTURE_MD)
    onion = next(r for r in rows if r["Code_SH"] == "07031000")
    assert onion["DD"] == "25"
    assert onion["Unite"] == "kg"


# ----------------------------------------------------------------------
# Adaptateur CSV → canonique
# ----------------------------------------------------------------------

def test_parse_source_counts(adapter):
    rows = adapter.parse_source()
    assert len(rows) == 7
    assert adapter.stats["skipped"] == 0


def test_provenance_partial_b(adapter):
    line = next(adapter.transform("KEN"))
    assert line.provenance.data_status == DataStatus.PARTIAL
    assert line.provenance.reliability == ReliabilityGrade.B
    assert line.provenance.version_date == date(2022, 7, 1)
    assert line.schema_version == "4.0"


def test_dd_bands(adapter):
    rates = {l.commodity.national_code:
             next(m for m in l.measures if m.code == "D.D").rate_pct
             for l in adapter.transform("TZA")}
    assert rates["01012100"] == 0.0
    assert rates["01012900"] == 25.0
    assert rates["25232100"] == 10.0
    assert rates["63090000"] == 35.0


def test_sensitive_item_mixed_rate(adapter):
    lines = {l.commodity.national_code: l for l in adapter.transform("KEN")}
    rice = lines["10061000"]
    dd = next(m for m in rice.measures if m.code == "D.D")
    assert dd.rate_type == RateType.MIXED
    assert dd.rate_pct == 75.0
    assert dd.specific_amount == 345.0
    assert dd.specific_unit == "USD/MT"
    assert rice.commodity.sensitivity == "sensible"


def test_ken_national_levies(adapter):
    line = next(adapter.transform("KEN"))
    codes = {m.code for m in line.measures}
    assert {"D.D", "IDF", "RDL", "VAT"} <= codes
    vat = next(m for m in line.measures if m.sequence == 90)
    assert vat.rate_pct == 16.0
    assert vat.basis == DutyBasis.CIF_PLUS_INCLUDED
    assert "D.D" in vat.basis_includes
    assert "IDF" in vat.basis_includes


def test_ssd_no_undocumented_vat(adapter):
    """SSD : pas de TVA documentée → aucune mesure TVA (pas d'extrapolation)."""
    line = next(adapter.transform("SSD"))
    assert not any(m.measure_type == MeasureType.VAT for m in line.measures)
    codes = {m.code for m in line.measures}
    assert codes == {"D.D"}


def test_transition_note_for_cod(adapter):
    line = next(adapter.transform("COD"))
    assert "transitoire" in line.provenance.notes


def test_eac_and_zlecaf_advantages(adapter):
    line = next(adapter.transform("UGA"))
    agreements = {a.agreement for a in line.fiscal_advantages}
    assert {"EAC", "ZLECAf"} <= agreements
    dd = next(m for m in line.measures if m.code == "D.D")
    assert dd.is_zlecaf_applicable is True


def test_rejects_non_member(adapter):
    with pytest.raises(ValueError, match="membre de l'EAC"):
        next(adapter.transform("DZA"))


# ----------------------------------------------------------------------
# Émission par pays (run)
# ----------------------------------------------------------------------

def test_run_emits_all_countries(csv_path, tmp_path):
    out = tmp_path / "out"
    stats = run(csv_path, str(out))
    assert set(stats["countries"]) == set(COUNTRIES)
    assert all(n == 7 for n in stats["countries"].values())
    sample = json.loads(
        (out / "RWA_canonical.jsonl").read_text().splitlines()[0])
    assert sample["provenance"]["data_status"] == "PARTIAL"
    assert sample["commodity"]["country_iso3"] == "RWA"


def test_run_country_filter(csv_path, tmp_path):
    out = tmp_path / "out"
    stats = run(csv_path, str(out), countries=["ken", "RWA"])
    assert set(stats["countries"]) == {"KEN", "RWA"}
    assert not (out / "TZA_canonical.jsonl").exists()


def test_referentials_consistency():
    assert len(COUNTRIES) == 8
    assert set(VAT_BY_COUNTRY) <= set(COUNTRIES)
    # SSD et SOM volontairement absents de VAT_BY_COUNTRY (non documenté)
    assert "SSD" not in VAT_BY_COUNTRY
    assert "SOM" not in VAT_BY_COUNTRY
