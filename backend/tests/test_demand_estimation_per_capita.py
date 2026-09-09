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


def test_own_imports_fallback_exposes_usd_per_capita():
    # Repli sur imports propres (produit sans mapping production, besoin en USD) :
    # c'est le seul chemin intégré dont le besoin est en USD, donc la seule voie
    # qui exerce la branche USD du helper — le champ ne doit pas y être omis.
    history = [
        {"year": 2020, "import_value_usd": 1_000_000, "no_data": False},
        {"year": 2021, "import_value_usd": 2_000_000, "no_data": False},
    ]
    r = d.estimate_need_from_own_imports("901890", "DZA", history)
    assert r is not None
    ipc = r.get("implied_per_capita")
    assert ipc is not None
    assert ipc["unit"] == "USD/hab/an"


def test_suggested_supplier_suppressed_for_caveated_commodity():
    # Pour la banane (SH 080390), le classement de production est méthodologiquement
    # inapte à désigner un fournisseur EXPORT : la recommandation doit être
    # suspendue (pas de NGA recommandé) et le caveat remonté dans la réponse.
    r = d.estimate_national_need("080390", "DZA")
    assert r.get("available")
    assert r.get("suggested_supplier") is None
    assert r.get("suggested_supplier_suppressed_reason")
    assert r.get("commodity_caveat")
    assert "MÉTHODOLOGIE" in r.get("note", "")


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


# ── Garde-fou « seuil logique » (audit des besoins nationaux) ──────────────────


def test_diet_extrapolation_flagged_and_gdp_capped_cassava_north_africa():
    # Manioc pour l'Algérie : la sous-région (Afrique du Nord) n'en produit pas
    # (<2 producteurs) → référence continentale = régime subsaharien appliqué à un
    # pays qui ne consomme quasiment pas de manioc. DOIT être flaggé, l'ajustement
    # PIB à la hausse neutralisé, et aucun fournisseur suggéré.
    r = d.estimate_national_need("0714", "DZA")
    assert r.get("available")
    pl = r.get("plausibility")
    assert pl and "diet_extrapolation" in pl["flags"]
    assert r["inputs"]["gdp_adjustment_capped"] is True
    assert r.get("suggested_supplier") is None
    assert r.get("suggested_supplier_suppressed_reason")
    assert "SEUIL LOGIQUE" in r.get("note", "")


def test_legitimate_staple_not_flagged_cassava_nigeria():
    # Manioc pour le Nigéria : référence RÉGIONALE réelle (Afrique de l'Ouest,
    # 15 producteurs) — consommation staple élevée mais authentique. NE DOIT PAS
    # être flaggé, ni voir son facteur PIB plafonné, ni perdre le fournisseur.
    r = d.estimate_national_need("0714", "NGA")
    assert r.get("available")
    assert r.get("plausibility") is None
    assert r["inputs"]["gdp_adjustment_capped"] is False
    assert r.get("suggested_supplier") is not None


def test_banana_algeria_stays_plausible_unflagged():
    # Non-régression : le cas banane/DZA (≈13 kg/hab) reste dans les clous.
    r = d.estimate_national_need("080390", "DZA")
    assert r.get("available")
    assert r.get("plausibility") is None


def test_above_human_ceiling_flag_triggers():
    ipc = {"value": 1500.0, "unit": "kg/hab/an"}
    g = d._plausibility_guardrail("agri", ipc, False, "Afrique de l'Ouest", "Cassava")
    assert g and "above_human_ceiling" in g["flags"]


def test_plausibility_none_when_within_bounds():
    ipc = {"value": 50.0, "unit": "kg/hab/an"}
    assert d._plausibility_guardrail("agri", ipc, False, "Afrique de l'Ouest", "Maize") is None
