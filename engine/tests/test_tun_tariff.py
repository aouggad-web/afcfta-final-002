"""
Tests — Profil tarifaire TUN (Tunisie / Douane — tarifweb)
==========================================================
Vérifie le profil fiscal tunisien (DD / DC / FODEC / TCL / TVA) :
  - séquence d'application et assiette TVA (CIF + DD + DC + FODEC + TCL)
  - tous les taux proviennent du crawl (aucun fixe inventé) → garde-fous OK
  - HS6 extrait des 11 digits NDP
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from adapters.raw_crawl_adapter import (
    convert_with_profile, _validate_profile, PROFILES,
)
from schemas.canonical_model import DutyBasis, MeasureType


def _crawl(positions):
    return {
        "country_code": "TUN", "country_name": "Tunisia",
        "source": "Douane Tunisienne — tarifweb (douane.gov.tn)",
        "source_url": "https://www.douane.gov.tn/tarifwebnew/getresultat.php",
        "crawled_at": "2026-06-15T12:00:00+00:00", "data_type": "raw_crawl",
        "positions": positions + [
            {"code": f"99{i:09d}", "description_en": f"x{i}",
             "dd_rate": [0.0, 10.0, 20.0, 36.0][i % 4], "dd_rate_raw": "x",
             "dc_rate": None, "fodec_rate": 1.0, "tcl_rate": None,
             "vat_rate": 19.0, "chapter": "99", "digits": 11}
            for i in range(600)
        ],
    }


def test_profile_passes_guardrails():
    _validate_profile(PROFILES["TUN"])


def test_customs_duty_from_crawl():
    dd = next(c for c in PROFILES["TUN"].components if c.is_customs_duty)
    assert dd.rate_field == "dd_rate"
    assert dd.fixed_rate is None


class TestTunStandard:
    def setup_method(self):
        recs = convert_with_profile(_crawl([
            {"code": "01012100000", "description_en": "Chevaux reproducteurs",
             "dd_rate": 0.0, "dd_rate_raw": "0 %", "dc_rate": None,
             "fodec_rate": 1.0, "tcl_rate": None, "vat_rate": 19.0,
             "chapter": "01", "digits": 11},
        ]), PROFILES["TUN"])
        self.r = recs[0]
        self.m = {x.code: x for x in self.r.measures}

    def test_measures_present(self):
        # DD (0% émis car always), FODEC (1%), TVA (19%) — pas de DC ni TCL
        assert set(self.m) == {"D.D", "FODEC", "T.V.A"}

    def test_dd_sequence_10(self):
        assert self.m["D.D"].sequence == 10
        assert self.m["D.D"].basis == DutyBasis.CIF

    def test_fodec_levy_sequence_30(self):
        assert self.m["FODEC"].measure_type == MeasureType.LEVY
        assert self.m["FODEC"].rate_pct == 1.0
        assert self.m["FODEC"].sequence == 30  # séquence fixe (DC=20 absent)

    def test_vat_sequence_50_includes_emitted(self):
        vat = self.m["T.V.A"]
        assert vat.sequence == 50
        assert vat.basis == DutyBasis.CIF_PLUS_INCLUDED
        assert vat.basis_includes == ["D.D", "FODEC"]  # DC/TCL absents filtrés

    def test_total(self):
        # 0 + 1 + 19 = 20
        assert self.r.total_npf_pct == 20.0

    def test_hs6_from_11_digits(self):
        assert self.r.commodity.hs6 == "010121"
        assert self.r.commodity.digits == 11


class TestTunWithExcise:
    def setup_method(self):
        recs = convert_with_profile(_crawl([
            {"code": "22030000000", "description_en": "Bière",
             "dd_rate": 36.0, "dd_rate_raw": "36 %", "dc_rate": 25.0,
             "fodec_rate": 1.0, "tcl_rate": None, "vat_rate": 19.0,
             "chapter": "22", "digits": 11},
        ]), PROFILES["TUN"])
        self.r = recs[0]
        self.m = {x.code: x for x in self.r.measures}

    def test_dc_excise_present(self):
        assert self.m["DC"].measure_type == MeasureType.EXCISE
        assert self.m["DC"].rate_pct == 25.0
        assert self.m["DC"].sequence == 20

    def test_vat_includes_dc(self):
        assert self.m["T.V.A"].basis_includes == ["D.D", "DC", "FODEC"]

    def test_total_beer(self):
        # 36 + 25 + 1 + 19 = 81
        assert self.r.total_npf_pct == 81.0


def test_reduced_vat_preserved():
    recs = convert_with_profile(_crawl([
        {"code": "30049000000", "description_en": "Médicaments", "dd_rate": 0.0,
         "dd_rate_raw": "0 %", "dc_rate": None, "fodec_rate": None,
         "tcl_rate": None, "vat_rate": 7.0, "chapter": "30", "digits": 11},
    ]), PROFILES["TUN"])
    vat = next(m for m in recs[0].measures if m.code == "T.V.A")
    assert vat.rate_pct == 7.0
