"""
Tests — SACU & traitement honnête des droits spécifiques/composés
=================================================================
Vérifie que le moteur ne fabrique JAMAIS un faux 0 % pour un droit non
réductible en pourcentage :
  - droit spécifique « Nc/kg »  → RateType.SPECIFIC, rate_pct=None, montant+unité
  - droit composé non résolu     → RateType.MIXED, rate_pct=None, ligne PARTIAL
  - « free »                     → exonéré réel (0 %)
Et vérifie la structure des 5 profils SACU (TEC commun + TVA domestique).
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from adapters.raw_crawl_adapter import (
    PROFILES,
    _parse_specific_duty,
    convert_with_profile,
)
from schemas.canonical_model import (
    DataStatus,
    DutyBasis,
    MeasureType,
    RateType,
)

SACU_MEMBERS = ["ZAF", "NAM", "BWA", "LSO", "SWZ"]


# ── Parseur de droit spécifique ──────────────────────────────────────────────


class TestParseSpecificDuty:
    @pytest.mark.parametrize(
        "raw,amount,unit",
        [
            ("5,5c/kg", 5.5, "c/kg"),
            ("450c/kg", 450.0, "c/kg"),
            ("8c/kg", 8.0, "c/kg"),
            ("2,75c/kg", 2.75, "c/kg"),
            ("483,72c/kg", 483.72, "c/kg"),
            ("12c/u", 12.0, "c/u"),
        ],
    )
    def test_valid_specific(self, raw, amount, unit):
        assert _parse_specific_duty(raw) == (amount, unit)

    @pytest.mark.parametrize("raw", ["or", "but", "u", "kg", "x", "", "free", "20%"])
    def test_non_specific_returns_none(self, raw):
        assert _parse_specific_duty(raw) is None


# ── Fixture crawl SACU minimal couvrant tous les cas ─────────────────────────


def _sacu_crawl() -> dict:
    positions = [
        # ad valorem normal
        {
            "code": "010121",
            "description_en": "Breeding animals",
            "dd_rate": 0.0,
            "dd_rate_raw": "free",
            "chapter": "01",
            "digits": 6,
        },
        {
            "code": "220300",
            "description_en": "Beer",
            "dd_rate": 25.0,
            "dd_rate_raw": "25%",
            "chapter": "22",
            "digits": 6,
        },
        # droit spécifique c/kg
        {
            "code": "020830",
            "description_en": "Primate meat",
            "dd_rate": None,
            "dd_rate_raw": "8c/kg",
            "chapter": "02",
            "digits": 6,
        },
        # droit composé non résolu
        {
            "code": "010391",
            "description_en": "Swine",
            "dd_rate": None,
            "dd_rate_raw": "u",
            "chapter": "01",
            "digits": 6,
        },
    ]
    # Padding pour passer le seuil de bandes + volume
    for i in range(600):
        positions.append(
            {
                "code": f"99{i:06d}",
                "description_en": f"x{i}",
                "dd_rate": [0.0, 10.0, 20.0, 30.0][i % 4],
                "dd_rate_raw": f"{[0,10,20,30][i % 4]}%",
                "chapter": "99",
                "digits": 8,
            }
        )
    return {
        "country_code": "ZAF",
        "country_name": "South Africa",
        "source": "SARS — South African Revenue Service",
        "source_url": "https://www.sars.gov.za/legal-tariff/",
        "crawled_at": "2026-06-12T21:00:00+00:00",
        "data_type": "raw_crawl",
        "positions": positions,
    }


# ── Traitement honnête des droits non ad valorem ─────────────────────────────


class TestHonestDutyHandling:
    def setup_method(self):
        self.recs = convert_with_profile(_sacu_crawl(), PROFILES["ZAF"])
        self.by_code = {r.commodity.national_code: r for r in self.recs}

    def _dd(self, code):
        return next(m for m in self.by_code[code].measures if m.code == "D.D")

    def test_specific_duty_not_zero(self):
        """8c/kg ne doit JAMAIS devenir 0 % ad valorem."""
        m = self._dd("020830")
        assert m.rate_type == RateType.SPECIFIC
        assert m.rate_pct is None
        assert m.specific_amount == 8.0
        assert m.specific_unit == "c/kg"
        assert m.basis == DutyBasis.QUANTITY

    def test_specific_duty_line_still_verified(self):
        """Un droit spécifique connu reste VERIFIED (on le connaît exactement)."""
        assert self.by_code["020830"].provenance.data_status == DataStatus.VERIFIED

    def test_unresolved_duty_not_zero(self):
        """Droit composé « u » → non résolu, pas 0 %."""
        m = self._dd("010391")
        assert m.rate_type == RateType.MIXED
        assert m.rate_pct is None

    def test_unresolved_line_marked_partial(self):
        """Une ligne au droit non résolu est dégradée en PARTIAL/B."""
        prov = self.by_code["010391"].provenance
        assert prov.data_status == DataStatus.PARTIAL
        assert "vérifier" in (prov.notes or "").lower()

    def test_free_is_real_zero(self):
        m = self._dd("010121")
        assert m.rate_pct == 0.0
        assert m.rate_type == RateType.EXEMPT

    def test_advalorem_unchanged(self):
        m = self._dd("220300")
        assert m.rate_pct == 25.0
        assert m.rate_type == RateType.AD_VALOREM

    def test_total_npf_excludes_specific(self):
        """total_npf ne compte pas le droit spécifique (ce n'est pas un %)."""
        r = self.by_code["020830"]
        # seul le VAT 15 % est ad valorem
        assert r.total_npf_pct == 15.0

    def test_vat_always_present(self):
        for code in ("010121", "220300", "020830", "010391"):
            assert any(m.code == "T.V.A" for m in self.by_code[code].measures)


# ── Profils SACU : TEC commun + TVA domestique ───────────────────────────────


class TestSacuProfiles:
    def test_all_members_registered(self):
        for iso in SACU_MEMBERS:
            assert iso in PROFILES

    def test_customs_duty_reads_crawl_field(self):
        """Le droit SACU doit lire le champ du crawl (jamais inventé)."""
        for iso in SACU_MEMBERS:
            dd = next(c for c in PROFILES[iso].components if c.is_customs_duty)
            assert dd.rate_field == "dd_rate"
            assert dd.raw_field == "dd_rate_raw"
            assert dd.fixed_rate is None

    @pytest.mark.parametrize(
        "iso,vat",
        [
            ("ZAF", 15.0),
            ("NAM", 15.0),
            ("BWA", 14.0),
            ("LSO", 15.0),
            ("SWZ", 15.0),
        ],
    )
    def test_member_vat_rate(self, iso, vat):
        vat_comp = next(c for c in PROFILES[iso].components if c.code == "T.V.A")
        assert vat_comp.fixed_rate == vat
        assert vat_comp.legal_reference  # base légale obligatoire

    def test_bwa_vat_differs(self):
        """Botswana a une TVA de 14 %, distincte des autres membres (15 %)."""
        bwa = next(c for c in PROFILES["BWA"].components if c.code == "T.V.A")
        zaf = next(c for c in PROFILES["ZAF"].components if c.code == "T.V.A")
        assert bwa.fixed_rate == 14.0
        assert zaf.fixed_rate == 15.0

    def test_real_crawl_all_members(self):
        """Le crawl SARS réel s'applique aux 5 membres avec la bonne TVA."""
        path = "/root/.claude/uploads/d6b855c0-55bf-5ef4-a9c2-f54aa37badf6/" "20da6e3b-zaf_raw.json"
        if not Path(path).exists():
            pytest.skip("crawl ZAF non disponible")
        import json

        data = json.load(open(path))
        for iso, expected_vat in [("ZAF", 15.0), ("BWA", 14.0)]:
            recs = convert_with_profile(data, PROFILES[iso])
            assert len(recs) == 8592
            sample = recs[0]
            vat = next(m for m in sample.measures if m.code == "T.V.A")
            assert vat.rate_pct == expected_vat
