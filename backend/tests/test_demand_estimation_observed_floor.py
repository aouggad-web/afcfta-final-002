"""
Tests du plancher « importations observées » (`_observed_imports_floor`).

Contexte (revue Copilot, PR #430) : quand une quantité réelle est connue pour
le même flux BACI, elle était utilisée directement comme plancher de besoin
national — sans passer par le garde-fou de plausibilité introduit pour ce
même couple valeur/quantité dans `shipment_estimator.observed_unit_value`.
Une quantité douanière omise ou mal unitée pouvait donc gonfler le besoin
national de façon arbitraire, alors que son ratio USD/kg aurait été rejeté
par ce garde-fou. Ces tests vérifient que le couple est validé avant d'être
retenu, avec repli sur la conversion par chapitre si implausible.
"""

import os
import sys

_backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

from services import demand_estimation_service as d  # noqa: E402


def test_observed_quantity_used_directly_when_plausible():
    # SH 300490 (médicaments, chapitre 30) : 50 M USD / 2 000 t -> 25 USD/kg,
    # dans la bande plausible autour du repère de chapitre (60 USD/kg).
    observed = {
        "import_value_usd": 50_000_000,
        "import_quantity_tonnes": 2000,
        "source": "OEC / BACI",
    }
    r = d._observed_imports_floor(500.0, "tonnes", "300490", observed)
    assert r is not None
    assert r["floor_value"] == 2000.0
    assert r["conversion"]["is_estimate"] is False
    assert "Quantité réelle observée" in r["conversion"]["note"]


def test_observed_quantity_rejected_when_implausible_falls_back_to_chapter():
    # 50 M USD / 1 t -> 50 000 USD/kg, très au-delà de la bande plausible
    # (×0,05-×20 du repère de chapitre 60 USD/kg) : quasi certainement une
    # erreur de déclaration (quantité omise/mal unitée) -> jamais utilisée
    # comme plancher tel quel ; repli sur la conversion par chapitre.
    observed = {
        "import_value_usd": 50_000_000,
        "import_quantity_tonnes": 1,
        "source": "OEC / BACI",
    }
    r = d._observed_imports_floor(500.0, "tonnes", "300490", observed)
    assert r is not None
    # Repli sur le ratio de chapitre (60 USD/kg) : 50M / 60 / 1000 ≈ 833 t,
    # PAS la quantité brute (1 t) ni le plancher via quantité directe.
    assert r["floor_value"] != 1.0
    assert round(r["floor_value"], 1) == round(50_000_000 / 60.0 / 1000.0, 1)
    assert r["conversion"]["is_estimate"] is True


def test_observed_quantity_plausibility_check_failure_falls_back_gracefully(monkeypatch):
    # Si le contrôle de plausibilité lève une exception pour CE couple
    # valeur/quantité précis, ne jamais utiliser la quantité brute
    # aveuglément : repli sur la conversion par chapitre (le repère de
    # chapitre lui-même, sans quantité observée, doit continuer de
    # fonctionner normalement).
    import services.shipment_estimator as se

    real_observed_unit_value = se.observed_unit_value

    def _boom_only_for_this_pair(hs_code, value_usd, quantity_tonnes, *args, **kwargs):
        if quantity_tonnes == 2000:
            raise RuntimeError("boom")
        return real_observed_unit_value(hs_code, value_usd, quantity_tonnes, *args, **kwargs)

    monkeypatch.setattr(se, "observed_unit_value", _boom_only_for_this_pair)
    observed = {
        "import_value_usd": 50_000_000,
        "import_quantity_tonnes": 2000,
        "source": "OEC / BACI",
    }
    r = d._observed_imports_floor(500.0, "tonnes", "300490", observed)
    assert r is not None
    assert r["floor_value"] != 2000.0
    assert r["conversion"]["is_estimate"] is True
