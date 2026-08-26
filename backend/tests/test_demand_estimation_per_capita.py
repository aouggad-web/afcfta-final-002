"""
Tests du contrôle de vraisemblance `implied_per_capita` de l'estimation de
besoin national.

Contexte : pour la banane fraîche (SH 080390), le besoin estimé de l'Algérie
ressort à ≈581 000 t/an — un total qui, sans dénominateur, peut paraître
aberrant. Ramené par habitant il vaut ≈13 kg/hab/an, soit une consommation de
banane parfaitement plausible (moyenne mondiale ~12-14 kg/hab/an). Le champ
`implied_per_capita` expose ce ratio pour rendre la vérification immédiate.
"""

import os
import sys

_backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

from services import demand_estimation_service as d  # noqa: E402


def test_implied_per_capita_tonnes_expressed_in_kg():
    r = d._implied_per_capita(581000.0, "tonnes", 44700000)
    assert r is not None
    assert r["unit"] == "kg/hab/an"
    # 581000 t / 44.7M hab = 0.013 t = ~13 kg/hab
    assert 12.0 < r["value"] < 14.0


def test_implied_per_capita_usd_kept_in_usd():
    r = d._implied_per_capita(4_470_000_000.0, "USD", 44700000)
    assert r is not None
    assert r["unit"] == "USD/hab/an"
    assert 90 < r["value"] < 110  # ~100 USD/hab


def test_implied_per_capita_guards_zero_population():
    assert d._implied_per_capita(500000.0, "tonnes", 0) is None
    assert d._implied_per_capita(500000.0, "tonnes", None) is None
    assert d._implied_per_capita(None, "tonnes", 1000) is None


def test_algeria_banana_need_is_realistic_per_capita():
    # Reproduit le cas signalé : le TOTAL paraît énorme (~5-6·10^5 t) mais le
    # ratio par habitant confirme que la logique est saine (≈13 kg/hab/an, pas
    # 8 t/hab/an comme le laissait craindre une division erronée).
    r = d.estimate_national_need("080390", "DZA")
    assert r.get("available")
    ipc = r.get("implied_per_capita")
    assert ipc is not None
    assert ipc["unit"] == "kg/hab/an"
    # Ordre de grandeur d'une consommation réelle de banane : jamais des tonnes/hab.
    assert 5.0 < ipc["value"] < 40.0


def test_measured_l1_path_also_exposes_per_capita():
    r = d.estimate_national_need(
        "080390",
        "DZA",
        apparent={
            "production": 100000,
            "imports": 400000,
            "exports": 1000,
            "unit": "tonnes",
            "source": "test",
        },
    )
    assert r.get("estimation_level") == 1
    assert r.get("implied_per_capita", {}).get("unit") == "kg/hab/an"
