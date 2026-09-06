"""Garde-fous Integrity Watch RWA (PR #454) — six fils de revue.

Chaque test bloque une régression signalée :
1. la loi primaire nº 011/2025 (accises) ne peut plus être remplacée par les
   taux de la colonne EAC 2017 (bière 30 %, cigarettes sans composante FRW) ;
2. l'assiette déclarée des accises ad valorem doit correspondre à celle du
   moteur (CIF + DD) ;
3. les formalités dérivées du tarif régional doivent rester dégradées
   (confidence < 100, legal_text_verified false) ;
4. les 3 traitements TVA zéro-rated de la loi nº 049/2023 doivent exister ;
5. la préférence ZLECAf doit rester OFFER_ONLY (jamais DOCUMENTED sans
   instrument indépendant) ;
6. l'attente de devise (RWF) doit être documentée dans le registre.
"""

import json
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
_ROOT = BACKEND_ROOT.parent
SLUG = _ROOT / "data" / "rwanda"

LAW_011 = "Law nº 011/2025"
LAW_049 = "Law nº 049/2023"


def _load(name):
    return json.loads((SLUG / name).read_text(encoding="utf-8"))


def test_excise_primary_law_restored_and_conflicts_removed():
    d = _load("excise_measures.json")
    ids = {r["record_id"] for r in d["excise_rates"]}
    primary = [r for r in d["excise_rates"] if r["verification_status"] == "VERIFIED_PRIMARY_TEXT"]
    assert len(primary) >= 6
    assert {r["record_id"] for r in primary} >= {
        "RWA-EXCISE-BEER-OTHER", "RWA-EXCISE-CIGARETTES", "RWA-EXCISE-WINE-OTHER",
        "RWA-EXCISE-PETROL", "RWA-EXCISE-GASOIL", "RWA-EXCISE-VEHICLES-UNDER-1500CC",
    }
    # la bière 30 % (colonne EAC 2017) et le runtime cigarettes ont été retirés
    assert "RWA-EXCISE_EXCIS-30_0" not in ids and "RWA-EXCISE_EXCIS-36_0" not in ids
    # la composante spécifique FRW 230/pack est documentée
    cig = next(r for r in primary if r["record_id"] == "RWA-EXCISE-CIGARETTES")
    assert "230" in cig["rate"] and "36%" in cig["rate"]
    # bière : taux général 65 % lié aux codes SH réels
    beer = next(r for r in primary if r["record_id"] == "RWA-EXCISE-BEER-OTHER")
    assert beer["rate"] == "65%" and "22030010" in beer["hs_codes_explicit"]


def test_excise_rate_basis_matches_engine():
    d = _load("excise_measures.json")
    for r in d["excise_rates"]:
        basis = r.get("rate_basis", "")
        is_specific = "litre" in basis or "paquet" in basis or "spécifique" in basis.lower()
        if not is_specific:
            assert "CIF + DD" in basis, (r["record_id"], basis)


def test_formalities_downgraded():
    d = _load("legal_overrides.json")
    for m in d["measures"]:
        assert m["mapping_confidence"] < 100, m["measure_id"]
        assert m.get("legal_text_verified") is False


def test_vat_zero_rated_from_primary_law_present():
    d = _load("vat_measures.json")
    zeros = [r for r in d.get("vat_zero_rated", []) if LAW_049 in r.get("legal_reference", "")]
    assert len(zeros) == 3
    assert all(r["verification_status"] == "VERIFIED_PRIMARY_TEXT" for r in zeros)


def test_preference_status_is_offer_only():
    reg = _load("rwa_gazette_register.json")
    assert reg["preference_and_origin_status"] == "OFFER_ONLY"
    assert reg["preference_evidence"]["status"] == "OFFER_ONLY"


def test_afcfta_application_evidence_documented():
    reg = _load("rwa_gazette_register.json")
    ev = reg["afcfta_application_evidence"]
    assert ev["gti_participant"] is True
    assert "guided-trade-initiative" in ev["source_url"]
    assert ev["algeria_reciprocity"]["source_id"] == "DZA-DGD-CIRC-482-2024"
    assert ev["schedule_published"]


def test_coverage_complete_requires_verified_base_tariff():
    reg = _load("rwa_gazette_register.json")
    if reg.get("coverage_complete"):
        assert reg["base_tariff_documentation"]["data_status"].startswith("VERIFIED")


def test_currency_expectation_documented():
    reg = _load("rwa_gazette_register.json")
    assert "RWF" in reg.get("currency_note", "")
