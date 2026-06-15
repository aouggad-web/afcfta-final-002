"""
Tests — Profil tarifaire MAR (Maroc / ADII — portail ADIL)
==========================================================
Vérifie le profil fiscal marocain (DD / TPI / TIC / TVA) du moteur générique :
  - séquence d'application et assiettes (TVA sur CIF+DD+TPI+TIC)
  - tous les taux proviennent du crawl (aucun fixe inventé) → garde-fous OK
  - HS6 extrait des 10 digits NTS
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from adapters.raw_crawl_adapter import (
    convert_with_profile, _validate_profile, PROFILES,
)
from schemas.canonical_model import DutyBasis, MeasureType, RateType


def _crawl(positions):
    return {
        "country_code": "MAR", "country_name": "Morocco",
        "source": "Douane Maroc (ADII) — portail ADIL",
        "source_url": "https://www.douane.gov.ma/adil/",
        "crawled_at": "2026-06-15T12:00:00+00:00", "data_type": "raw_crawl",
        "positions": positions + [
            {"code": f"99{i:08d}", "description_en": f"x{i}",
             "dd_rate": [2.5, 10.0, 25.0, 40.0][i % 4], "dd_rate_raw": "x",
             "tpi_rate": 0.25, "vat_rate": 20.0, "tic_rate": None,
             "chapter": "99", "digits": 10}
            for i in range(600)
        ],
    }


def test_profile_passes_guardrails():
    _validate_profile(PROFILES["MAR"])


def test_profile_customs_duty_from_crawl():
    """Le DD marocain doit lire le crawl (jamais un taux fixe inventé)."""
    dd = next(c for c in PROFILES["MAR"].components if c.is_customs_duty)
    assert dd.rate_field == "dd_rate"
    assert dd.fixed_rate is None


class TestMarStandard:
    def setup_method(self):
        recs = convert_with_profile(_crawl([
            {"code": "0101210000", "description_en": "Chevaux reproducteurs",
             "dd_rate": 2.5, "dd_rate_raw": "2.5 %", "tpi_rate": 0.25,
             "vat_rate": 20.0, "tic_rate": None, "chapter": "01", "digits": 10},
        ]), PROFILES["MAR"])
        self.r = recs[0]
        self.m = {x.code: x for x in self.r.measures}

    def test_three_measures(self):
        assert set(self.m) == {"D.D", "TPI", "T.V.A"}

    def test_dd_on_cif(self):
        assert self.m["D.D"].basis == DutyBasis.CIF
        assert self.m["D.D"].rate_pct == 2.5
        assert self.m["D.D"].sequence == 10

    def test_tpi_levy(self):
        assert self.m["TPI"].measure_type == MeasureType.LEVY
        assert self.m["TPI"].rate_pct == 0.25
        assert self.m["TPI"].sequence == 20

    def test_vat_includes_dd_tpi(self):
        vat = self.m["T.V.A"]
        assert vat.basis == DutyBasis.CIF_PLUS_INCLUDED
        assert vat.basis_includes == ["D.D", "TPI"]
        assert vat.sequence == 40  # séquence fixe : TVA toujours 40

    def test_total(self):
        # 2.5 + 0.25 + 20 = 22.75
        assert self.r.total_npf_pct == 22.75

    def test_hs6_from_10digits(self):
        assert self.r.commodity.hs6 == "010121"
        assert self.r.commodity.digits == 10


class TestMarWithTIC:
    def setup_method(self):
        recs = convert_with_profile(_crawl([
            {"code": "2208300000", "description_en": "Whiskies",
             "dd_rate": 17.5, "dd_rate_raw": "17.5 %", "tpi_rate": 0.25,
             "vat_rate": 20.0, "tic_rate": 15.0, "chapter": "22", "digits": 10},
        ]), PROFILES["MAR"])
        self.r = recs[0]
        self.m = {x.code: x for x in self.r.measures}

    def test_four_measures(self):
        assert set(self.m) == {"D.D", "TPI", "TIC", "T.V.A"}

    def test_tic_excise(self):
        assert self.m["TIC"].measure_type == MeasureType.EXCISE
        assert self.m["TIC"].rate_pct == 15.0
        assert self.m["TIC"].sequence == 30

    def test_vat_includes_tic(self):
        assert self.m["T.V.A"].basis_includes == ["D.D", "TPI", "TIC"]

    def test_total_whisky(self):
        # 17.5 + 0.25 + 15 + 20 = 52.75
        assert self.r.total_npf_pct == 52.75


def test_reduced_vat_rate_preserved():
    """TVA réduite (10 %) lue telle quelle depuis le crawl."""
    recs = convert_with_profile(_crawl([
        {"code": "1006300000", "description_en": "Riz", "dd_rate": 40.0,
         "dd_rate_raw": "40 %", "tpi_rate": 0.25, "vat_rate": 10.0,
         "tic_rate": None, "chapter": "10", "digits": 10},
    ]), PROFILES["MAR"])
    vat = next(m for m in recs[0].measures if m.code == "T.V.A")
    assert vat.rate_pct == 10.0
