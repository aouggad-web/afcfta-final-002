"""
Tests — Adaptateur MUS (Mauritius Revenue Authority)
=====================================================
Vérifie la conversion raw_crawl → CanonicalTariffLine pour Maurice :
  - Séquence de taxes (DD / Excise / TVA ou DD / TVA ou DD seul)
  - Exonération VAT (vat_rate=0 → pas de mesure T.V.A émise)
  - Excise élevé tabac (230 %) → total_npf > 200
  - basis_includes TVA contient EXCISE si applicable
  - Provenance VERIFIED/A, version_date 2026-04-01
  - HS6 extrait des 8 digits
"""
import sys
from datetime import date
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from adapters.mus_tariff_adapter import convert
from schemas.canonical_model import (
    DataStatus, DutyBasis, MeasureType, RateType, ReliabilityGrade,
)

# ── Fixtures ──────────────────────────────────────────────────────────────────

def _raw(code: str, dd: float, excise: float = 0.0, vat: float = 15.0,
         desc: str = "Test product") -> dict:
    return {
        "country_code": "MUS",
        "country_name": "Mauritius",
        "source": "MRA Integrated Tariff Schedule HS2022",
        "source_url": "https://www.mra.mu/download/TariffInfo010426.pdf",
        "crawled_at": "2026-06-15T23:08:48.273498+00:00",
        "data_type": "raw_crawl",
        "notes": [],
        "positions": [{
            "code": code,
            "description_en": desc,
            "dd_rate_raw": str(int(dd)),
            "dd_rate": dd,
            "excise_rate_raw": str(int(excise)) if excise else "",
            "excise_rate": excise if excise else None,
            "vat_rate_raw": str(int(vat)),
            "vat_rate": vat,
            "chapter": code[:2],
            "digits": len(code),
        }],
    }


# ── Tests cas standard (DD + VAT, sans excise) ───────────────────────────────

class TestStandardDutyVAT:
    def setup_method(self):
        data = _raw("20011000", dd=15.0, vat=15.0)
        self.r = convert(data)[0]
        self.measures = {m.code: m for m in self.r.measures}

    def test_two_measures(self):
        """DD + VAT uniquement (pas d'excise)."""
        assert len(self.r.measures) == 2

    def test_dd_on_cif(self):
        m = self.measures["D.D"]
        assert m.basis == DutyBasis.CIF
        assert m.rate_pct == 15.0
        assert m.sequence == 10
        assert m.measure_type == MeasureType.CUSTOMS_DUTY

    def test_vat_on_cif_plus_dd(self):
        m = self.measures["T.V.A"]
        assert m.basis == DutyBasis.CIF_PLUS_INCLUDED
        assert "D.D" in m.basis_includes
        assert "EXCISE" not in m.basis_includes
        assert m.rate_pct == 15.0
        assert m.sequence == 30
        assert m.measure_type == MeasureType.VAT

    def test_total_npf(self):
        # DD=15 + VAT=15 = 30
        assert self.r.total_npf_pct == 30.0

    def test_zlecaf_only_dd(self):
        assert self.measures["D.D"].is_zlecaf_applicable is True
        assert self.measures["T.V.A"].is_zlecaf_applicable is False

    def test_provenance_verified_a(self):
        p = self.r.provenance
        assert p.data_status == DataStatus.VERIFIED
        assert p.reliability == ReliabilityGrade.A
        assert p.version_date == date(2026, 4, 1)

    def test_hs6_from_8digits(self):
        assert self.r.commodity.hs6 == "200110"
        assert self.r.commodity.digits == 8


# ── Tests position exonérée de VAT ──────────────────────────────────────────

class TestVATExempt:
    def setup_method(self):
        data = _raw("01022100", dd=0.0, vat=0.0, desc="Pure-bred breeding animals")
        self.r = convert(data)[0]
        self.codes = [m.code for m in self.r.measures]

    def test_no_vat_measure(self):
        """VAT=0 → aucune mesure T.V.A émise (exonéré)."""
        assert "T.V.A" not in self.codes

    def test_only_dd_measure(self):
        assert self.codes == ["D.D"]

    def test_total_npf_zero(self):
        assert self.r.total_npf_pct == 0.0

    def test_dd_exempt(self):
        m = self.r.measures[0]
        assert m.rate_type == RateType.EXEMPT
        assert m.rate_pct == 0.0


# ── Tests excise élevé (tabac) ───────────────────────────────────────────────

class TestHighExciseTobacco:
    def setup_method(self):
        data = _raw("24031100", dd=0.0, excise=230.0, vat=15.0,
                    desc="Water pipe tobacco")
        self.r = convert(data)[0]
        self.measures = {m.code: m for m in self.r.measures}

    def test_three_measures(self):
        """DD + EXCISE + VAT = 3 mesures."""
        assert len(self.r.measures) == 3

    def test_excise_basis_cif(self):
        m = self.measures["EXCISE"]
        assert m.basis == DutyBasis.CIF
        assert m.rate_pct == 230.0
        assert m.sequence == 20
        assert m.measure_type == MeasureType.EXCISE

    def test_vat_includes_excise(self):
        m = self.measures["T.V.A"]
        assert "EXCISE" in m.basis_includes
        assert "D.D"    in m.basis_includes

    def test_total_npf_tobacco(self):
        # DD=0 + Excise=230 + VAT=15 = 245
        assert self.r.total_npf_pct == 245.0

    def test_sensitivity_sensible(self):
        assert self.r.commodity.sensitivity == "sensible"


# ── Tests excise modéré (caviar / alcool moyen) ──────────────────────────────

def test_excise_moderate():
    data = _raw("16043100", dd=0.0, excise=30.0, vat=15.0, desc="Caviar")
    r = convert(data)[0]
    codes = {m.code for m in r.measures}
    assert "EXCISE" in codes
    excise_m = next(m for m in r.measures if m.code == "EXCISE")
    assert excise_m.rate_pct == 30.0
    # total: 0 + 30 + 15 = 45
    assert r.total_npf_pct == 45.0


# ── Test DD=100% (sucre) ─────────────────────────────────────────────────────

def test_dd_100_sugar():
    data = _raw("17011200", dd=100.0, excise=0.0, vat=0.0, desc="Beet sugar")
    r = convert(data)[0]
    dd_m = next(m for m in r.measures if m.code == "D.D")
    assert dd_m.rate_pct == 100.0
    # VAT=0 → exonéré → total = 100
    assert r.total_npf_pct == 100.0
    assert not any(m.code == "T.V.A" for m in r.measures)


# ── Test séquence strictement croissante ────────────────────────────────────

@pytest.mark.parametrize("dd,excise,vat", [
    (0.0, 0.0, 0.0),
    (15.0, 0.0, 15.0),
    (0.0, 230.0, 15.0),
    (30.0, 50.0, 15.0),
])
def test_sequence_strictly_ascending(dd, excise, vat):
    data = _raw("09010000", dd=dd, excise=excise, vat=vat)
    r = convert(data)[0]
    seqs = [m.sequence for m in r.measures]
    assert seqs == sorted(seqs)


# ── Test HS6 extraction ──────────────────────────────────────────────────────

@pytest.mark.parametrize("code8,expected_hs6", [
    ("09019000", "090190"),
    ("24031100", "240311"),
    ("17011200", "170112"),
    ("01022100", "010221"),
    ("98000000", "980000"),
])
def test_hs6_extraction(code8, expected_hs6):
    data = _raw(code8, dd=0.0, vat=15.0)
    r = convert(data)[0]
    assert r.commodity.hs6 == expected_hs6
    assert r.commodity.digits == 8


# ── Test batch ───────────────────────────────────────────────────────────────

def test_batch_multiple_positions():
    data = {
        "country_code": "MUS",
        "country_name": "Mauritius",
        "source": "MRA Integrated Tariff Schedule HS2022",
        "source_url": "https://www.mra.mu/download/TariffInfo010426.pdf",
        "crawled_at": "2026-06-15T23:00:00+00:00",
        "data_type": "raw_crawl",
        "notes": [],
        "positions": [
            {"code": "01022100", "description_en": "Cattle",
             "dd_rate": 0.0, "excise_rate": None, "excise_rate_raw": "",
             "vat_rate": 0.0, "vat_rate_raw": "0",
             "chapter": "01", "digits": 8},
            {"code": "24031100", "description_en": "Tobacco",
             "dd_rate": 0.0, "excise_rate": 230.0, "excise_rate_raw": "230",
             "vat_rate": 15.0, "vat_rate_raw": "15",
             "chapter": "24", "digits": 8},
            {"code": "20011000", "description_en": "Cucumbers",
             "dd_rate": 15.0, "excise_rate": None, "excise_rate_raw": "",
             "vat_rate": 15.0, "vat_rate_raw": "15",
             "chapter": "20", "digits": 8},
        ],
    }
    records = convert(data)
    assert len(records) == 3
    for r in records:
        assert r.commodity.country_iso3 == "MUS"
        assert r.provenance.data_status == DataStatus.VERIFIED
        assert r.provenance.version_date == date(2026, 4, 1)
