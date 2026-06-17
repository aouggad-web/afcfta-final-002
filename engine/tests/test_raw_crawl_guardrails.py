"""
Tests — Garde-fous anti-données-génériques du moteur raw_crawl
==============================================================
Ces tests PROUVENT qu'il est impossible de produire de la donnée VERIFIED/A
à partir d'une origine inventée, générée ou non traçable.

C'est la protection contre la rechute dans l'erreur production_africaine.json
(données synthétiques estampillées comme officielles).
"""
import sys
from dataclasses import replace
from datetime import date
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from adapters.raw_crawl_adapter import (
    convert_with_profile, _validate_profile, _validate_crawl,
    TaxProfile, TaxComponent, PROFILES,
    ProfileValidationError, CrawlValidationError,
)
from schemas.canonical_model import (
    MeasureType, DutyBasis, DataStatus, ReliabilityGrade,
)


# ── Fixtures : un crawl réaliste minimal ─────────────────────────────────────

def _valid_crawl(n_bands: int = 3) -> dict:
    bands = [0.0, 5.0, 15.0, 25.0, 35.0][:max(n_bands, 1)]
    positions = []
    for i in range(600):
        positions.append({
            "code": f"{1000 + i:08d}",
            "description_en": f"Product {i}",
            "dd_rate": bands[i % len(bands)],
            "excise_rate": 0.0,
            "vat_rate": 15.0,
            "chapter": f"{(i % 97) + 1:02d}",
            "digits": 8,
        })
    return {
        "country_code": "XXX",
        "country_name": "Testland",
        "source": "Testland Customs Authority",
        "source_url": "https://customs.testland.gov/tariff",
        "crawled_at": "2026-06-15T12:00:00+00:00",
        "data_type": "raw_crawl",
        "positions": positions,
    }


def _test_profile() -> TaxProfile:
    return TaxProfile(
        country_iso3="XXX",
        source_name="Testland Customs",
        source_url="https://customs.testland.gov/tariff",
        source_document="Testland Tariff Schedule 2026",
        components=[
            TaxComponent("D.D", "Droit", "Duty", MeasureType.CUSTOMS_DUTY,
                         DutyBasis.CIF, rate_field="dd_rate", is_customs_duty=True),
            TaxComponent("T.V.A", "TVA", "VAT", MeasureType.VAT,
                         DutyBasis.CIF_PLUS_INCLUDED, rate_field="vat_rate",
                         includes_codes=["D.D"], emit_when="positive",
                         legal_reference="VAT Act"),
        ],
    )


# ════════════════════════════════════════════════════════════════════════════
# VERROU 1 — Profil : interdiction des taux de douane inventés
# ════════════════════════════════════════════════════════════════════════════

class TestProfileGuardrails:
    def test_customs_duty_cannot_be_fixed(self):
        """Un droit de douane à taux fixe codé en dur = donnée inventée → refus."""
        bad = TaxProfile(
            country_iso3="XXX", source_name="x", source_url="x", source_document="x",
            components=[
                TaxComponent("D.D", "Droit", "Duty", MeasureType.CUSTOMS_DUTY,
                             DutyBasis.CIF, fixed_rate=10.0, is_customs_duty=True),
            ],
        )
        with pytest.raises(ProfileValidationError, match="jamais via fixed_rate"):
            _validate_profile(bad)

    def test_must_have_exactly_one_customs_duty(self):
        bad = TaxProfile(
            country_iso3="XXX", source_name="x", source_url="x", source_document="x",
            components=[
                TaxComponent("T.V.A", "TVA", "VAT", MeasureType.VAT, DutyBasis.CIF,
                             rate_field="vat_rate"),
            ],
        )
        with pytest.raises(ProfileValidationError, match="exactement 1 composante"):
            _validate_profile(bad)

    def test_fixed_rate_requires_legal_reference(self):
        """Une taxe statutaire fixe SANS référence légale est refusée."""
        bad = TaxProfile(
            country_iso3="XXX", source_name="x", source_url="x", source_document="x",
            components=[
                TaxComponent("D.D", "Droit", "Duty", MeasureType.CUSTOMS_DUTY,
                             DutyBasis.CIF, rate_field="dd_rate", is_customs_duty=True),
                TaxComponent("SR", "Surtaxe", "Surtax", MeasureType.LEVY,
                             DutyBasis.CIF, fixed_rate=10.0),  # pas de legal_reference
            ],
        )
        with pytest.raises(ProfileValidationError, match="SANS référence légale"):
            _validate_profile(bad)

    def test_component_without_rate_source_rejected(self):
        bad = TaxProfile(
            country_iso3="XXX", source_name="x", source_url="x", source_document="x",
            components=[
                TaxComponent("D.D", "Droit", "Duty", MeasureType.CUSTOMS_DUTY,
                             DutyBasis.CIF, rate_field="dd_rate", is_customs_duty=True),
                TaxComponent("X", "X", "X", MeasureType.OTHER_TAX, DutyBasis.CIF),
            ],
        )
        with pytest.raises(ProfileValidationError, match="sans source de taux"):
            _validate_profile(bad)

    def test_valid_profile_passes(self):
        _validate_profile(_test_profile())  # ne lève pas


# ════════════════════════════════════════════════════════════════════════════
# VERROU 2 — Crawl : refus des origines non réelles / non traçables
# ════════════════════════════════════════════════════════════════════════════

class TestCrawlGuardrails:
    def test_missing_source_rejected(self):
        crawl = _valid_crawl()
        del crawl["source"]
        with pytest.raises(CrawlValidationError, match="'source' manquant"):
            convert_with_profile(crawl, _test_profile())

    def test_missing_source_url_rejected(self):
        crawl = _valid_crawl()
        crawl["source_url"] = ""
        with pytest.raises(CrawlValidationError, match="'source_url' manquant"):
            convert_with_profile(crawl, _test_profile())

    @pytest.mark.parametrize("dtype", [
        "synthetic", "generated", "template_v2", "random_fill", "mock_data",
    ])
    def test_synthetic_data_type_rejected(self, dtype):
        crawl = _valid_crawl()
        crawl["data_type"] = dtype
        with pytest.raises(CrawlValidationError, match="synthétique/généré"):
            convert_with_profile(crawl, _test_profile())

    def test_empty_positions_rejected(self):
        crawl = _valid_crawl()
        crawl["positions"] = []
        with pytest.raises(CrawlValidationError, match="Aucune position"):
            convert_with_profile(crawl, _test_profile())

    def test_missing_duty_field_rejected(self):
        """Champ droit absent → interdit de combler par 0 (ce serait inventer)."""
        crawl = _valid_crawl()
        for p in crawl["positions"][:10]:
            del p["dd_rate"]
        with pytest.raises(CrawlValidationError, match="absent de"):
            convert_with_profile(crawl, _test_profile())

    def test_single_band_rejected(self):
        """Une seule bande tarifaire = signature de template → refus."""
        crawl = _valid_crawl(n_bands=1)  # tous à 0
        with pytest.raises(CrawlValidationError):
            convert_with_profile(crawl, _test_profile())

    def test_all_zero_duties_rejected(self):
        crawl = _valid_crawl()
        for p in crawl["positions"]:
            p["dd_rate"] = 0.0
        with pytest.raises(CrawlValidationError, match="à 0 %"):
            convert_with_profile(crawl, _test_profile())

    def test_valid_crawl_passes(self):
        records = convert_with_profile(_valid_crawl(), _test_profile())
        assert len(records) == 600
        for r in records:
            assert r.provenance.data_status == DataStatus.VERIFIED

    def test_few_positions_warns_but_passes(self, capsys):
        """< 500 positions : avertissement mais pas de refus."""
        crawl = _valid_crawl()
        crawl["positions"] = crawl["positions"][:100]
        records = convert_with_profile(crawl, _test_profile())
        assert len(records) == 100
        assert "Vérifier l'exhaustivité" in capsys.readouterr().out


# ════════════════════════════════════════════════════════════════════════════
# Les profils RÉELS embarqués (ETH, MUS) passent les garde-fous
# ════════════════════════════════════════════════════════════════════════════

class TestRealProfilesAreValid:
    def test_eth_profile_valid(self):
        _validate_profile(PROFILES["ETH"])

    def test_mus_profile_valid(self):
        _validate_profile(PROFILES["MUS"])

    def test_eth_real_crawl_passes(self):
        path = ("/root/.claude/uploads/d6b855c0-55bf-5ef4-a9c2-f54aa37badf6/"
                "1c30ccb9-eth_raw.json")
        if not Path(path).exists():
            pytest.skip("crawl ETH non disponible dans cet environnement")
        import json
        records = convert_with_profile(json.load(open(path)), PROFILES["ETH"])
        assert len(records) == 2063

    def test_mus_real_crawl_passes(self):
        path = ("/root/.claude/uploads/d6b855c0-55bf-5ef4-a9c2-f54aa37badf6/"
                "b64c1c79-mus_raw.json")
        if not Path(path).exists():
            pytest.skip("crawl MUS non disponible dans cet environnement")
        import json
        records = convert_with_profile(json.load(open(path)), PROFILES["MUS"])
        assert len(records) == 6073


# ════════════════════════════════════════════════════════════════════════════
# Parité moteur générique ↔ adaptateurs dédiés (champs significatifs)
# ════════════════════════════════════════════════════════════════════════════

def test_parity_with_dedicated_eth():
    path = ("/root/.claude/uploads/d6b855c0-55bf-5ef4-a9c2-f54aa37badf6/"
            "1c30ccb9-eth_raw.json")
    if not Path(path).exists():
        pytest.skip("crawl ETH non disponible")
    import json
    from adapters.eth_tariff_adapter import convert_file
    dedicated = convert_file(path)
    generic = convert_with_profile(json.load(open(path)), PROFILES["ETH"])
    assert len(dedicated) == len(generic)
    for a, b in zip(dedicated, generic):
        # Comparer les champs significatifs (hors observation/last_updated/provenance)
        assert a.total_npf_pct == b.total_npf_pct
        assert a.commodity.hs6 == b.commodity.hs6
        assert a.commodity.sensitivity == b.commodity.sensitivity
        assert len(a.measures) == len(b.measures)
        for ma, mb in zip(a.measures, b.measures):
            assert ma.code == mb.code
            assert ma.rate_pct == mb.rate_pct
            assert ma.basis == mb.basis
            assert ma.basis_includes == mb.basis_includes
            assert ma.sequence == mb.sequence
            assert ma.rate_type == mb.rate_type
