"""
Tests — Adaptateur ETH (Ethiopian Customs Commission)
=====================================================
Vérifie la conversion raw_crawl → CanonicalTariffLine pour l'Éthiopie :
  - Séquence de taxes (DD / Excise / SR / TVA / WHR)
  - Assiettes correctes (CIF / CIF_PLUS_INCLUDED)
  - basis_includes cohérents avec et sans excise
  - Provenance VERIFIED/A
  - HS6 extrait des 11 digits
  - total_npf_pct correct
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from adapters.eth_tariff_adapter import convert
from schemas.canonical_model import (
    DataStatus, DutyBasis, MeasureType, RateType, ReliabilityGrade,
)

# ── Fixtures ─────────────────────────────────────────────────────────────────

def _raw(code: str, dd: float, excise: float = 0.0,
         chapter: str | None = None) -> dict:
    """Construit une position raw_crawl minimale."""
    return {
        "country_code": "ETH",
        "country_name": "Ethiopia",
        "source": "Ethiopian Customs Commission (ECC)",
        "source_url": "https://customs.erca.gov.et/trade/customs-division/tariff",
        "crawled_at": "2026-06-15T19:05:08.873538+00:00",
        "data_type": "raw_crawl",
        "notes": [],
        "positions": [{
            "code": code,
            "description_en": f"Test product {code}",
            "unit": "KG",
            "dd_rate_raw": str(int(dd)),
            "dd_rate": dd,
            "excise_rate": excise,
            "vat_rate": 15.0,
            "withholding_rate": 3.0,
            "surtax_rate": None,
            "chapter": chapter or code[:2],
            "digits": len(code),
        }],
    }


# ── Tests séquence taxes sans excise ────────────────────────────────────────

class TestNoExcise:
    def setup_method(self):
        data = _raw("01012100000", dd=0.0)
        self.records = convert(data)
        self.r = self.records[0]
        self.measures = {m.code: m for m in self.r.measures}

    def test_four_measures(self):
        """Sans excise : D.D + SR + T.V.A + WHR = 4 mesures."""
        assert len(self.r.measures) == 4

    def test_no_excise_measure(self):
        assert "ER" not in self.measures

    def test_dd_basis_cif(self):
        m = self.measures["D.D"]
        assert m.basis == DutyBasis.CIF
        assert m.sequence == 10
        assert m.rate_pct == 0.0
        assert m.rate_type == RateType.EXEMPT
        assert m.measure_type == MeasureType.CUSTOMS_DUTY

    def test_sr_basis_cif_plus(self):
        m = self.measures["SR"]
        assert m.basis == DutyBasis.CIF_PLUS_INCLUDED
        assert m.basis_includes == ["D.D"]
        assert m.rate_pct == 10.0
        assert m.sequence == 30

    def test_vat_includes_dd_and_sr(self):
        m = self.measures["T.V.A"]
        assert m.basis == DutyBasis.CIF_PLUS_INCLUDED
        assert "D.D" in m.basis_includes
        assert "SR"  in m.basis_includes
        assert "ER"  not in m.basis_includes
        assert m.rate_pct == 15.0
        assert m.sequence == 40

    def test_whr_basis_cif(self):
        m = self.measures["WHR"]
        assert m.basis == DutyBasis.CIF
        assert m.rate_pct == 3.0
        assert m.sequence == 50

    def test_total_npf(self):
        # DD=0 + Excise=0 + SR=10 + VAT=15 + WHR=3 = 28
        assert self.r.total_npf_pct == 28.0

    def test_zlecaf_applicable_only_on_dd(self):
        dd = self.measures["D.D"]
        assert dd.is_zlecaf_applicable is True
        for code, m in self.measures.items():
            if code != "D.D":
                assert m.is_zlecaf_applicable is False

    def test_hs6_extracted(self):
        assert self.r.commodity.hs6 == "010121"
        assert self.r.commodity.digits == 11

    def test_provenance_verified_a(self):
        p = self.r.provenance
        assert p.data_status == DataStatus.VERIFIED
        assert p.reliability == ReliabilityGrade.A
        assert "ECC" in (p.source_name or "")


# ── Tests séquence taxes AVEC excise ────────────────────────────────────────

class TestWithExcise:
    def setup_method(self):
        data = _raw("22030000000", dd=35.0, excise=40.0, chapter="22")
        self.records = convert(data)
        self.r = self.records[0]
        self.measures = {m.code: m for m in self.r.measures}

    def test_five_measures(self):
        """Avec excise : D.D + ER + SR + T.V.A + WHR = 5 mesures."""
        assert len(self.r.measures) == 5

    def test_excise_basis_cif(self):
        m = self.measures["ER"]
        assert m.basis == DutyBasis.CIF
        assert m.sequence == 20
        assert m.rate_pct == 40.0
        assert m.measure_type == MeasureType.EXCISE

    def test_sr_includes_er(self):
        m = self.measures["SR"]
        assert "ER" in m.basis_includes
        assert "D.D" in m.basis_includes

    def test_vat_includes_dd_er_sr(self):
        m = self.measures["T.V.A"]
        assert set(m.basis_includes) == {"D.D", "ER", "SR"}

    def test_total_npf_biere(self):
        # DD=35 + Excise=40 + SR=10 + VAT=15 + WHR=3 = 103
        assert self.r.total_npf_pct == 103.0

    def test_sensitivity_high_dd(self):
        assert self.r.commodity.sensitivity in ("sensible", "élevé")


# ── Test DD=5 (taux intermédiaire) ──────────────────────────────────────────

def test_dd5_no_excise_total():
    data = _raw("52010000000", dd=5.0, chapter="52")
    r = convert(data)[0]
    # 5 + 0 + 10 + 15 + 3 = 33
    assert r.total_npf_pct == 33.0
    # Pas d'excise
    assert not any(m.code == "ER" for m in r.measures)


def test_dd25_total():
    data = _raw("87032400000", dd=25.0, chapter="87")
    r = convert(data)[0]
    assert r.total_npf_pct == 53.0


# ── Test séquence strictement croissante ─────────────────────────────────────

def test_sequence_order_without_excise():
    data = _raw("01012100000", dd=0.0)
    r = convert(data)[0]
    seqs = [m.sequence for m in r.measures]
    assert seqs == sorted(seqs)


def test_sequence_order_with_excise():
    data = _raw("22030000000", dd=35.0, excise=40.0, chapter="22")
    r = convert(data)[0]
    seqs = [m.sequence for m in r.measures]
    assert seqs == sorted(seqs)


# ── Test HS6 extrait des 11 digits ──────────────────────────────────────────

@pytest.mark.parametrize("code,expected_hs6", [
    ("09011100000", "090111"),
    ("18010000000", "180100"),
    ("27090000000", "270900"),
    ("71081200000", "710812"),
])
def test_hs6_extraction(code, expected_hs6):
    data = _raw(code, dd=5.0)
    r = convert(data)[0]
    assert r.commodity.hs6 == expected_hs6
    assert r.commodity.national_code == code


# ── Test batch — toutes les positions traitées ──────────────────────────────

def test_batch_convert_multiple_positions():
    data = {
        "country_code": "ETH",
        "country_name": "Ethiopia",
        "source": "ECC",
        "source_url": "https://customs.erca.gov.et/",
        "crawled_at": "2026-06-15T19:00:00+00:00",
        "data_type": "raw_crawl",
        "notes": [],
        "positions": [
            {"code": "01012100000", "description_en": "Horses",
             "dd_rate": 0.0, "excise_rate": 0.0, "vat_rate": 15.0,
             "withholding_rate": 3.0, "surtax_rate": None, "chapter": "01", "digits": 11},
            {"code": "22030000000", "description_en": "Beer",
             "dd_rate": 35.0, "excise_rate": 40.0, "vat_rate": 15.0,
             "withholding_rate": 3.0, "surtax_rate": None, "chapter": "22", "digits": 11},
            {"code": "09011100000", "description_en": "Coffee",
             "dd_rate": 0.0, "excise_rate": 0.0, "vat_rate": 15.0,
             "withholding_rate": 3.0, "surtax_rate": None, "chapter": "09", "digits": 11},
        ],
    }
    records = convert(data)
    assert len(records) == 3
    for r in records:
        assert r.commodity.country_iso3 == "ETH"
        assert r.provenance.data_status == DataStatus.VERIFIED
        # WHR toujours présent
        assert any(m.code == "WHR" for m in r.measures)
