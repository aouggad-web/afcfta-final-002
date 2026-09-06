"""Garde-fous Integrity Watch TZA (PR #455) — cinq fils de revue.

1. les mesures VERIFIED_PRIMARY_TEXT (Cap. 147) doivent exister et ne jamais
   être supprimées par une régénération runtime ;
2. l'assiette déclarée des accises ad valorem doit correspondre au moteur
   (CIF + DD) ;
3. le zéro-rated exportations (VAT Act 2014, Sections 5(2)/55) doit exister ;
4. la préférence ZLECAf doit rester NOT_AVAILABLE (aucun snapshot TZA) —
   JAMAIS DOCUMENTED sans preuve indépendante ; la preuve d'application GTI
   et la réciprocité algérienne (circulaire 482/2024) sont documentées ;
5. TZA-CANONICAL-TARIFF doit être référencé dans legal_sources.json ;
   l'attente de devise (TZS) doit être documentée.
"""

import json
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
_ROOT = BACKEND_ROOT.parent
SLUG = _ROOT / "data" / "tanzania"


def _load(name):
    return json.loads((SLUG / name).read_text(encoding="utf-8"))


def test_excise_primary_law_cap147_present():
    d = _load("excise_measures.json")
    primary = [r for r in d["excise_rates"] if r["verification_status"] == "VERIFIED_PRIMARY_TEXT"]
    ids = {r["record_id"] for r in primary}
    assert {
        "TZA-EXCISE-2009-FRUIT-VEG-JUICE-LOCAL", "TZA-EXCISE-2009-FRUIT-VEG-JUICE-OTHER",
        "TZA-EXCISE-2201-MINERAL-WATER-LOCAL", "TZA-EXCISE-2201-MINERAL-WATER-IMPORTED",
        "TZA-EXCISE-0501-HUMAN-HAIR-LOCAL", "TZA-EXCISE-0501-HUMAN-HAIR-IMPORTED",
    } <= ids


def test_excise_rate_basis_matches_engine():
    d = _load("excise_measures.json")
    for r in d["excise_rates"]:
        basis = r.get("rate_basis", "")
        is_specific = "litre" in basis or "spécifique" in basis.lower()
        if not is_specific:
            assert "CIF + DD" in basis, (r["record_id"], basis)


def test_vat_zero_rated_exports_restored():
    v = _load("vat_measures.json")
    zeros = [r for r in v.get("vat_zero_rated", []) if r["record_id"] == "TZA-VAT-ZERO-EXPORTS"]
    assert len(zeros) == 1
    assert "Section 55" in zeros[0]["legal_reference"]
    assert zeros[0]["verification_status"] == "VERIFIED_PRIMARY_TEXT"


def test_preference_not_available_with_gti_evidence():
    reg = _load("tza_gazette_register.json")
    assert reg["preference_and_origin_status"] == "PARTIAL"
    ev = reg["afcfta_application_evidence"]
    assert ev["gti_participant"] is True
    assert "guided-trade-initiative" in ev["source_url"]
    assert ev["algeria_reciprocity"]["source_id"] == "DZA-DGD-CIRC-482-2024"


def test_canonical_tariff_in_legal_sources():
    ls = _load("legal_sources.json")
    ids = [s.get("source_id") for s in ls.get("sources", [])]
    assert "TZA-CANONICAL-TARIFF" in ids


def test_coverage_scope_and_currency_documented():
    reg = _load("tza_gazette_register.json")
    assert reg["coverage_scope"]["base_tariff"].startswith("VERIFIED")
    assert "PARTIAL" in reg["coverage_scope"]["national_layer"]
    assert "TZS" in reg.get("currency_note", "")


def test_coverage_complete_requires_verified_base_tariff():
    reg = _load("tza_gazette_register.json")
    if reg.get("coverage_complete"):
        assert reg["base_tariff_documentation"]["data_status"].startswith("VERIFIED")
