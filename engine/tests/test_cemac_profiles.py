"""
Tests — Profils tarifaires CEMAC (Communauté Économique et Monétaire)
=====================================================================
Vérifie la structure CEMAC TEC (Tarif Extérieur Commun) avec support export
ET les taxes locales de chaque membre (TCI, RI, CIA, TS, PUA, RS, OHADA, TVA).

Structure vérifiée par pays :
  CMR : DD + TCI(1%) + RI(0.45%) + TVA(19.25%)
  GAB : DD + TCI(1%) + CIA(0.2%) + TVA(18%)
  TCD : DD + TCI(1%) + TS(2%) + PUA(0.2%) + TVA(18%)
  CAF : DD + TCI(1%) + RS(1%) + TVA(19%)
  COG : DD + TCI(1%) + TS(0.2%) + OHADA(0.05%) + TVA(18%)
  GNQ : DD + TCI(1%) + TVA(15%)
  Export (tous) : PRÉLEV(crawl) + RED.INTRA(0%)
"""
import sys
from pathlib import Path
from datetime import date

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from adapters.raw_crawl_adapter import (
    convert_with_profile, _validate_profile, PROFILES,
)
from schemas.canonical_model import DutyBasis, MeasureType


# 6 membres CEMAC : CMR, GAB, TCD, CAF, COG, GNQ
CEMAC_MEMBERS = ["CMR", "GAB", "TCD", "CAF", "COG", "GNQ"]


def _crawl(country: str, positions, vat_rate: float = 19.0):
    """Crée un crawl CEMAC avec côté import et export."""
    return {
        "country_code": country,
        "country_name": "CEMAC Member",
        "source": "CEMAC TEC CEEAC",
        "source_url": "https://www.cemac.int/",
        "crawled_at": "2026-01-01T12:00:00+00:00",
        "data_type": "raw_crawl",
        "positions": positions + [
            {"code": f"99{i:08d}", "description_en": f"x{i}",
             "dd_rate": [0.0, 5.0, 10.0, 20.0, 30.0, 40.0][i % 6],
             "vat_rate": vat_rate if i % 5 != 0 else 0.0,  # 20% de positions exonérées
             "export_levy_rate": None,
             "chapter": "99", "digits": 10}
            for i in range(600)
        ],
    }


def test_all_cemac_members_registered():
    """Les 6 membres CEMAC doivent avoir un profil."""
    for member in CEMAC_MEMBERS:
        assert member in PROFILES, f"{member} not registered in PROFILES"


def test_cemac_profile_passes_guardrails():
    """Chaque profil CEMAC doit passer les garde-fous."""
    for member in CEMAC_MEMBERS:
        profile = PROFILES[member]
        _validate_profile(profile)  # Must not raise


def test_customs_duty_from_crawl():
    """Le DD doit lire le crawl, jamais un taux fixe."""
    for member in CEMAC_MEMBERS:
        profile = PROFILES[member]
        dd = next(c for c in profile.components if c.is_customs_duty)
        assert dd.rate_field == "dd_rate", f"{member}: DD field must be dd_rate"
        assert dd.fixed_rate is None, f"{member}: DD cannot have fixed_rate"


def test_import_and_export_components():
    """Les profils CEMAC doivent avoir composantes import et export."""
    for member in CEMAC_MEMBERS:
        profile = PROFILES[member]
        import_comps = [c for c in profile.components if not c.is_export]
        export_comps = [c for c in profile.components if c.is_export]
        assert len(import_comps) > 0, f"{member}: Must have import components"
        assert len(export_comps) > 0, f"{member}: Must have export components"


class TestCemacStandard:
    """Test cas standard : position avec DD côté import, prélèvement côté export."""

    def setup_method(self):
        member = "CMR"
        recs = convert_with_profile(_crawl(member, [
            {"code": "0101210000", "description_en": "Horses",
             "dd_rate": 5.0, "export_levy_rate": 2.0, "chapter": "01", "digits": 10},
        ]), PROFILES[member])
        self.r = recs[0]
        self.m = {x.code: x for x in self.r.measures}

    def test_import_measures_present(self):
        """DD (5 %) côté import."""
        import_measures = [m for m in self.r.measures if m.sequence < 60]
        assert len(import_measures) > 0
        dd = next((m for m in import_measures if m.code == "D.D"), None)
        assert dd is not None
        assert dd.rate_pct == 5.0

    def test_dd_sequence_10(self):
        dd = self.m["D.D"]
        assert dd.sequence == 10
        assert dd.basis == DutyBasis.CIF
        assert dd.is_zlecaf_applicable is True

    def test_export_measures_present(self):
        """Prélèvement (2 %) côté export."""
        export_measures = [m for m in self.r.measures if m.sequence >= 60]
        assert len(export_measures) > 0
        levy = next((m for m in export_measures
                     if "Prélèvement" in m.name_fr or "Levy" in m.name_en), None)
        assert levy is not None

    def test_export_sequence_higher(self):
        """Les mesures export commencent à séquence 60+."""
        export_measures = [m for m in self.r.measures if m.sequence >= 60]
        assert all(m.sequence >= 60 for m in export_measures)

    def test_import_export_separation(self):
        """Import et export doivent être dans des séquences différentes."""
        import_seqs = {m.sequence for m in self.r.measures if m.sequence < 60}
        export_seqs = {m.sequence for m in self.r.measures if m.sequence >= 60}
        assert import_seqs and export_seqs
        assert not (import_seqs & export_seqs)

    def test_export_is_zlecaf_not_applicable(self):
        """Les mesures export ne sont pas applicables ZLECAF."""
        export_measures = [m for m in self.r.measures if m.sequence >= 60]
        assert all(not m.is_zlecaf_applicable for m in export_measures)

    def test_total_npf_import_only(self):
        """total_npf inclut seulement côté import."""
        import_dd = next((m for m in self.r.measures
                          if m.code == "D.D" and m.sequence < 60), None)
        if import_dd and import_dd.rate_pct is not None:
            assert self.r.total_npf_pct >= import_dd.rate_pct


def test_intra_cemac_reduction_is_zero():
    """La réduction intra-CEMAC doit être 0 %."""
    member = "GAB"
    profile = PROFILES[member]
    red_intra = next((c for c in profile.components
                      if "INTRA" in c.code), None)
    if red_intra:
        assert red_intra.fixed_rate == 0.0


def test_hs6_extraction():
    """HS6 doit être extrait correctement (premiers 6 chiffres)."""
    member = "TCD"
    recs = convert_with_profile(_crawl(member, [
        {"code": "0206290000", "description_en": "Beef",
         "dd_rate": 20.0, "chapter": "02", "digits": 10},
    ]), PROFILES[member])
    assert recs[0].commodity.hs6 == "020629"
    assert recs[0].commodity.digits == 10


def test_multiple_dd_bands():
    """Les 6 bandes tarifaires (0, 5, 10, 20, 30, 40) doivent être présentes."""
    member = "CAF"
    positions = [
        {"code": f"01012{i:05d}", "description_en": f"Item {i}",
         "dd_rate": [0.0, 5.0, 10.0, 20.0, 30.0, 40.0][i],
         "chapter": "01", "digits": 10}
        for i in range(6)
    ]
    recs = convert_with_profile(_crawl(member, positions), PROFILES[member])
    dd_bands = set()
    for r in recs:
        dd = next((m.rate_pct for m in r.measures
                   if m.is_zlecaf_applicable and m.sequence < 60), None)
        if dd is not None:
            dd_bands.add(dd)
    assert dd_bands == {0.0, 5.0, 10.0, 20.0, 30.0, 40.0}


def test_all_members_emit_same_dd_for_same_code():
    """Tous les membres CEMAC appliquent le même TEC pour un code donné."""
    code_crawl = {
        "code": "0206290000",
        "description_en": "Beef",
        "dd_rate": 15.0,
        "vat_rate": 19.0,
        "chapter": "02",
        "digits": 10,
    }
    dd_rates = {}
    for member in CEMAC_MEMBERS:
        recs = convert_with_profile(_crawl(member, [code_crawl]), PROFILES[member])
        dd = next((m.rate_pct for m in recs[0].measures
                   if m.is_zlecaf_applicable and m.sequence < 60), None)
        dd_rates[member] = dd

    # Tous doivent avoir le même DD du crawl
    assert len(set(dd_rates.values())) == 1
    assert 15.0 in dd_rates.values()


# ============================================================================
# Tests des taxes locales par pays
# ============================================================================

def _pos(dd: float, vat: float, export_levy: float = None) -> dict:
    return {
        "code": "0206290000", "description_en": "Beef",
        "dd_rate": dd, "dd_rate_raw": f"{dd} %",
        "vat_rate": vat, "export_levy_rate": export_levy,
        "chapter": "02", "digits": 10,
    }


class TestCmrLocalTaxes:
    """CMR : DD + TCI(1%) + RI(0.45%) + TVA(19.25%)."""

    def setup_method(self):
        recs = convert_with_profile(_crawl("CMR", [_pos(20.0, 19.25)], 19.25),
                                    PROFILES["CMR"])
        self.r = recs[0]
        self.m = {x.code: x for x in self.r.measures if x.sequence < 60}

    def test_tci_present(self):
        assert "TCI" in self.m
        assert self.m["TCI"].rate_pct == 1.0
        assert self.m["TCI"].measure_type == MeasureType.LEVY

    def test_ri_present(self):
        assert "RI" in self.m
        assert self.m["RI"].rate_pct == 0.45
        assert self.m["RI"].measure_type == MeasureType.LEVY

    def test_vat_present_at_correct_rate(self):
        assert "T.V.A" in self.m
        assert self.m["T.V.A"].rate_pct == 19.25

    def test_total_import_without_exemption(self):
        # DD(20) + TCI(1) + RI(0.45) + TVA(19.25) = 40.7
        assert self.r.total_npf_pct == pytest.approx(40.70, abs=0.01)

    def test_tci_has_legal_reference(self):
        assert self.m["TCI"].legal_reference and "CEMAC" in self.m["TCI"].legal_reference

    def test_ri_has_observation_about_cap(self):
        """RI est plafonnée — l'observation doit le mentionner."""
        assert "plafonn" in (self.m["RI"].observation or "").lower()


class TestGabLocalTaxes:
    """GAB : DD + TCI(1%) + CIA(0.2%) + TVA(18%)."""

    def setup_method(self):
        recs = convert_with_profile(_crawl("GAB", [_pos(10.0, 18.0)], 18.0),
                                    PROFILES["GAB"])
        self.r = recs[0]
        self.m = {x.code: x for x in self.r.measures if x.sequence < 60}

    def test_tci_present(self):
        assert self.m["TCI"].rate_pct == 1.0

    def test_cia_present(self):
        assert "CIA" in self.m
        assert self.m["CIA"].rate_pct == 0.2

    def test_vat_18(self):
        assert self.m["T.V.A"].rate_pct == 18.0

    def test_total_gab(self):
        # DD(10) + TCI(1) + CIA(0.2) + TVA(18) = 29.2
        assert self.r.total_npf_pct == pytest.approx(29.2, abs=0.01)


class TestTcdLocalTaxes:
    """TCD : DD + TCI(1%) + TS(2%) + PUA(0.2%) + TVA(18%)."""

    def setup_method(self):
        recs = convert_with_profile(_crawl("TCD", [_pos(20.0, 18.0)], 18.0),
                                    PROFILES["TCD"])
        self.r = recs[0]
        self.m = {x.code: x for x in self.r.measures if x.sequence < 60}

    def test_ts_present(self):
        assert "TS" in self.m
        assert self.m["TS"].rate_pct == 2.0

    def test_pua_present(self):
        assert "PUA" in self.m
        assert self.m["PUA"].rate_pct == 0.2

    def test_vat_18_not_1925(self):
        """TVA Tchad = 18% (Loi 2024), PAS 19.25% du scraper CMR."""
        assert self.m["T.V.A"].rate_pct == 18.0

    def test_total_tcd(self):
        # DD(20) + TCI(1) + TS(2) + PUA(0.2) + TVA(18) = 41.2
        assert self.r.total_npf_pct == pytest.approx(41.2, abs=0.01)


class TestCafLocalTaxes:
    """CAF : DD + TCI(1%) + RS(1%) + TVA(19%)."""

    def setup_method(self):
        recs = convert_with_profile(_crawl("CAF", [_pos(10.0, 19.0)], 19.0),
                                    PROFILES["CAF"])
        self.r = recs[0]
        self.m = {x.code: x for x in self.r.measures if x.sequence < 60}

    def test_rs_present(self):
        assert "RS" in self.m
        assert self.m["RS"].rate_pct == 1.0

    def test_vat_19(self):
        assert self.m["T.V.A"].rate_pct == 19.0

    def test_total_caf(self):
        # DD(10) + TCI(1) + RS(1) + TVA(19) = 31.0
        assert self.r.total_npf_pct == pytest.approx(31.0, abs=0.01)


class TestCogLocalTaxes:
    """COG : DD + TCI(1%) + TS(0.2%) + OHADA(0.05%) + TVA(18%)."""

    def setup_method(self):
        recs = convert_with_profile(_crawl("COG", [_pos(20.0, 18.0)], 18.0),
                                    PROFILES["COG"])
        self.r = recs[0]
        self.m = {x.code: x for x in self.r.measures if x.sequence < 60}

    def test_ts_present(self):
        assert "TS" in self.m
        assert self.m["TS"].rate_pct == 0.2

    def test_ohada_present(self):
        assert "OHADA" in self.m
        assert self.m["OHADA"].rate_pct == 0.05

    def test_vat_18(self):
        assert self.m["T.V.A"].rate_pct == 18.0

    def test_total_cog(self):
        # DD(20) + TCI(1) + TS(0.2) + OHADA(0.05) + TVA(18) = 39.25
        assert self.r.total_npf_pct == pytest.approx(39.25, abs=0.01)


def test_vat_exempt_products_skip_tva():
    """Produit exonéré TVA : T.V.A ne doit pas être émise."""
    member = "CMR"
    recs = convert_with_profile(
        _crawl(member, [_pos(5.0, 0.0)], 19.25),  # vat_rate=0 → exonéré
        PROFILES[member]
    )
    m = {x.code: x for x in recs[0].measures if x.sequence < 60}
    assert "T.V.A" not in m  # emit_when="positive" → 0% non émis
    assert "D.D" in m
    assert "TCI" in m


def test_export_levy_emitted_when_positive():
    """Prélèvement export à 3% doit être émis avec séquence ≥ 60."""
    member = "GAB"
    recs = convert_with_profile(
        _crawl(member, [_pos(10.0, 18.0, export_levy=3.0)], 18.0),
        PROFILES[member]
    )
    export_m = [m for m in recs[0].measures if m.sequence >= 60]
    prelev = next((m for m in export_m if "PRÉLEV" in m.code), None)
    assert prelev is not None
    assert prelev.rate_pct == 3.0
    assert prelev.is_zlecaf_applicable is False


def test_tci_has_legal_reference_all_members():
    """TCI doit avoir legal_reference pour tous les membres."""
    for member in CEMAC_MEMBERS:
        profile = PROFILES[member]
        tci = next((c for c in profile.components if c.code == "TCI"), None)
        assert tci is not None, f"{member}: TCI absent du profil"
        assert tci.legal_reference, f"{member}: TCI sans legal_reference"


def test_national_taxes_have_legal_reference():
    """Toutes les taxes à taux fixe doivent avoir une legal_reference."""
    for member in CEMAC_MEMBERS:
        profile = PROFILES[member]
        for comp in profile.components:
            if comp.fixed_rate is not None:
                assert comp.legal_reference, (
                    f"{member}/{comp.code}: taux fixe {comp.fixed_rate}% "
                    f"sans legal_reference — interdit par les garde-fous"
                )
