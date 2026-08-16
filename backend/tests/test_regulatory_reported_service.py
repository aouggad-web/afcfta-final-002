"""Tests de la couche « indications secondaires » (non vérifiée).

Garantit que cette couche reste strictement informative : jamais de fee
calculable, toujours étiquetée non vérifiée, et distincte du registre conforme.
"""

from services.regulatory_reported_service import (
    build_reported_layer,
    get_reported_missions,
)


def test_new_country_has_reported_items():
    # Le Sénégal n'est pas dans le registre conforme mais figure dans la couche
    # reportée (scanners Cotecna + BESC).
    items = get_reported_missions("SEN")
    assert items, "SEN doit avoir des enregistrements reportés"


def test_reported_layer_is_never_calculable_and_flagged_unverified():
    layer = build_reported_layer("SEN", "DZA")
    assert layer is not None
    assert layer["reliability"] == "UNVERIFIED_SECONDARY"
    assert (
        "à confirmer" in layer["disclaimer"].lower() or "confirmer" in layer["disclaimer"].lower()
    )
    for item in layer["items"]:
        # Aucune indication reportée ne devient un montant exploitable.
        assert item["fee_status"] == "FEE_EXISTS_AMOUNT_NOT_AVAILABLE"
        assert "calculated_amount" not in item


def test_layer_covers_both_import_and_export_sides():
    # Import = destination (SEN), export = origine (GHA) : les deux côtés sont
    # peuplés indépendamment.
    layer = build_reported_layer("SEN", "GHA")
    sides = {i["side"] for i in layer["items"]}
    assert sides == {"import", "export"}


def test_uncovered_pair_returns_none_no_empty_section():
    assert build_reported_layer("XXX", "YYY") is None


def test_ghana_carries_verification_attempt_note():
    # La tentative de vérification primaire (assiette FOB/CIF non tranchée) est
    # tracée dans le dossier et ne promeut PAS le frais en calculable.
    items = get_reported_missions("GHA")
    ghana_icums = next(r for r in items if "ICUMS" in r.get("program", ""))
    attempts = ghana_icums.get("verification_attempts", [])
    assert attempts, "Ghana ICUMS doit porter une tentative de vérification"
    assert attempts[0]["outcome"] == "NOT_PROMOTED_TO_CALCULABLE"


def test_sahel_freight_tracking_reported_not_calculable():
    # Pays du Sahel (enclavés) : BSC/ECTN/PVI délégués à des privés, barèmes
    # officiels non publiés → indications secondaires, jamais calculables.
    for iso in ("MLI", "BFA", "TCD", "MRT", "NER"):
        items = get_reported_missions(iso)
        assert items, f"{iso} doit avoir une indication de suivi du fret"
        layer = build_reported_layer(iso, "DZA")
        assert layer is not None
        for it in layer["items"]:
            assert it["fee_status"] == "FEE_EXISTS_AMOUNT_NOT_AVAILABLE"


def test_central_african_republic_reported_but_not_calculable():
    # RCA (CAF) : conformité SGS + BESC Groupe Albatros, prestataires privés, mais
    # taux/montant non publiés → indications secondaires, jamais calculables.
    items = get_reported_missions("CAF")
    assert len(items) >= 2
    programs = " ".join(r.get("program", "") for r in items)
    assert "conformité" in programs.lower() and "BESC" in programs
    layer = build_reported_layer("CAF", "DZA")
    assert layer is not None
    for it in layer["items"]:
        assert it["fee_status"] == "FEE_EXISTS_AMOUNT_NOT_AVAILABLE"
