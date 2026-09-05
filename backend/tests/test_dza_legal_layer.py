"""
Tests de la couche de vérification juridique datée — juridiction DZA (Algérie).

La juridiction DZA est adossée au corpus national archivé SHA-256
(data/sources/DZA/legislation/_manifest.json : lois de finances 2020-2026,
Code des douanes 79-07, notes DGD 559/2023 et 4121/2024) et aux taxes
liées par position nationale dans backend/data/DZA_tariffs.json
(CRAWLED_AUTHENTIC — douane.gov.dz, 17 115 sous-positions 10 chiffres).

Doctrine vérifiée ici :
- Source : DOCUMENTED (tarif DGD archivé, SHA-256 présent) ;
- Temporalité : DOCUMENTED (couverture LF 2020 → 2026 déclarée) ;
- Fiscalité : DOCUMENTED (TVA/PRCT/TCS/DAPS par position nationale) ;
- Aucun message « gazette coverage » / « national-measure coverage » ;
- Aucun taux inventé : chaque composant cite sa position et sa source.
"""

import json
import sys
from datetime import date
from pathlib import Path

import pytest

BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from services.national_legal_calculation_service import (  # noqa: E402
    SUPPORTED_JURISDICTIONS,
    calculate_national_legal_layer,
)

_ROOT = BACKEND_ROOT.parent
_ON_DATE = date(2026, 9, 5)


def _calc(hs_code: str, value: float = 10000.0):
    return calculate_national_legal_layer(
        jurisdiction="DZA",
        hs_code=hs_code,
        on_date=_ON_DATE,
        customs_value=value,
        base_cet_rate=15.0,
    )


def test_dza_is_a_supported_jurisdiction():
    assert "DZA" in SUPPORTED_JURISDICTIONS
    cfg = SUPPORTED_JURISDICTIONS["DZA"]
    assert cfg.default_currency == "DZD"
    assert cfg.fiscal_data_dir.name == "dza"


def test_dza_quality_dimensions_all_documented():
    """Plus aucun « Non vérifié » / « Partiel » injustifié sur le calcul DZA."""
    r = _calc("0101211100")
    q = r["quality_dimensions"]
    assert q["source"] == "DOCUMENTED"
    assert q["temporal_validity"] == "DOCUMENTED"
    assert q["classification"] == "DOCUMENTED"
    assert q["taxes_and_levies"] == "DOCUMENTED"
    assert q["preference_and_origin"] == "DOCUMENTED"
    assert r["overall_status"] == "INFORMATIVE_COMPLETE"


def test_dza_no_missing_coverage_messages():
    """Les messages « gazette / national-measure coverage » ne doivent plus apparaître."""
    r = _calc("0101211100")
    gaps = " ".join(r.get("known_data_gaps", []) + r.get("missing_elements", []))
    assert "gazette coverage" not in gaps
    assert "national-measure coverage" not in gaps


def test_dza_components_by_national_position():
    """0101211100 : TVA réduite 9 % + TCS 3 % + PRCT 2 % — liés à la position."""
    r = _calc("0101211100")
    levies = r.get("other_levies") or {}
    assert (levies.get("prct") or {}).get("rate") == 2.0
    assert (levies.get("tcs") or {}).get("rate") == 3.0
    assert (levies.get("daps") or {}).get("rate") is None  # pas de DAPS sur les animaux vivants
    assert (r.get("vat") or {}).get("rate") == 9.0  # TVA réduite par position
    assert r.get("currency_code") == "DZD"


def test_dza_daps_applied_by_position():
    """D.A.P.S 60 % sur 721090 (acier) — taux codé DGD, lié par position."""
    r = _calc("7210900000")
    levies = r.get("other_levies") or {}
    assert (levies.get("daps") or {}).get("rate") == 60.0
    assert (levies.get("daps") or {}).get("legal_reference")


def test_dza_vat_standard_19_percent():
    """TVA standard 19 % hors liste réduite (ordinateurs, ch. 84)."""
    r = _calc("8471300000")
    assert (r.get("vat") or {}).get("rate") == 19.0


def test_dza_every_component_cites_a_source():
    """Aucun composant monétaire sans source_id (règle zéro-mock)."""
    r = _calc("0101211100")
    for c in r.get("monetary_components") or []:
        assert c.get("source_id"), c
    vat = r.get("vat") or {}
    if vat:
        assert vat.get("source_id")


def test_dza_gazette_register_integrity():
    """Le registre DZA cite des documents archivés avec SHA-256 vérifiables."""
    reg = json.loads(
        (_ROOT / "data" / "dza" / "dza_gazette_register.json").read_text(encoding="utf-8")
    )
    assert reg["coverage_complete"] is True
    assert reg["regional_cet_applicable"] is False  # UMA : pas de TEC régional
    assert reg["base_tariff_documentation"]["sha256"]
    assert reg["base_tariff_documentation"]["national_positions"] >= 17000
    # Chaque document du registre porte un SHA-256 (preuve d'archivage)
    assert all(d.get("sha256") for d in reg["documents"])
    # Le SHA-256 du tarif de base correspond au manifeste des sources
    manifest = json.loads(
        (_ROOT / "data" / "sources" / "DZA" / "legislation" / "_manifest.json").read_text(
            encoding="utf-8"
        )
    )
    by_file = {d["file"]: d["sha256"] for d in manifest["documents"]}
    assert (
        reg["base_tariff_documentation"]["sha256"]
        == by_file["tarif_d_usage_2020.pdf"]
    )


def test_kenya_layer_unaffected_by_dza_wiring():
    """Non-régression : la juridiction KEN garde son comportement (USD, registre EAC)."""
    assert SUPPORTED_JURISDICTIONS["KEN"].default_currency == "USD"
    cfg = SUPPORTED_JURISDICTIONS["DZA"]
    assert cfg.legal_overrides_path != SUPPORTED_JURISDICTIONS["KEN"].legal_overrides_path
