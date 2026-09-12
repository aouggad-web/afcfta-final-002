"""Le besoin national doit tenir compte de ce que le pays produit et consomme.

Deux travers d'un même mécanisme, relevés sur des cas réels :

* la cascade estime une CONSOMMATION et l'appelle « besoin ». Un exportateur ne
  peut servir que ce que le pays ne produit pas : le Cameroun consomme des
  bananes mais en produit 4,7 Mt, son besoin d'importation est nul ;
* le proxy L2 applique au pays une disponibilité continentale par habitant.
  Pour le manioc, cette disponibilité est tirée par le Nigeria — d'où 7,35 Mt
  de « besoin » algérien pour un produit que l'Algérie ne consomme pas.

La règle de consommation révélée qui corrige le second travers ne doit JAMAIS
écarter un marché réel. La banane dessert vers l'Algérie et le manioc vers
l'Algérie sont indiscernables sur les seuls signaux locaux — ni production
nationale, ni production régionale. Seul le flux observé les sépare, et c'est
pourquoi « non attesté » exige une preuve positive d'absence.
"""

from __future__ import annotations

import importlib.util
import pathlib
import sys

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
BACKEND = REPO_ROOT / "backend"


@pytest.fixture(scope="module")
def des():
    for path in (str(BACKEND), str(REPO_ROOT)):
        if path not in sys.path:
            sys.path.insert(0, path)
    spec = importlib.util.spec_from_file_location(
        "demand_estimation_under_test", BACKEND / "services" / "demand_estimation_service.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _flux(usd):
    return {"import_value_usd": usd, "source": "OEC", "year": 2023}


# ── Auto-approvisionnement ───────────────────────────────────────────────────

def test_un_pays_autosuffisant_n_a_pas_de_besoin_importable(des):
    """Cameroun / bananes : 4,7 Mt produits pour 1,65 Mt de besoin estimé."""
    r = des.estimate_national_need("0803", "CMR")
    assert r["available"]
    assert r["self_sufficiency"]["covers_need"] is True
    assert r["self_sufficiency"]["ratio"] > 1
    assert r["importable_need"] == 0.0
    # Le besoin de consommation, lui, reste inchangé : on n'a pas réécrit sa
    # sémantique, on a ajouté celle qui manquait.
    assert r["value"] > 0


def test_le_besoin_de_consommation_n_est_pas_altere(des):
    """Nigeria / manioc : premier producteur mondial, besoin importable nul."""
    r = des.estimate_national_need("0714", "NGA")
    assert r["value"] > 1_000_000
    assert r["importable_need"] == 0.0
    assert r["consumption_basket"]["status"] == "attested"


def test_un_pays_sans_production_doit_importer_la_totalite(des):
    """Ne pas trouver de production nationale ne doit pas annuler le besoin."""
    r = des.estimate_national_need("0803", "DZA", observed_imports=_flux(250_000_000))
    assert r["consumption_basket"]["status"] == "attested"
    assert r["importable_need"] == pytest.approx(r["value"], rel=0.01)


def test_un_agregat_sh_est_signale_et_non_conclu(des):
    """SH 0803 mêle banane dessert et banane à cuire : ne pas trancher en silence."""
    r = des.estimate_national_need("0803", "CMR")
    assert r["self_sufficiency"].get("aggregate_caveat")
    assert "agrège" in r["self_sufficiency"]["aggregate_caveat"]


# ── Consommation révélée ─────────────────────────────────────────────────────

def test_un_produit_hors_panier_est_ecarte_sur_preuve(des):
    """Manioc / Algérie : 7,35 Mt de besoin fictif, importations nulles."""
    r = des.estimate_national_need("0714", "DZA", observed_imports=_flux(0))
    assert r["consumption_basket"]["status"] == "not_attested"
    assert r["importable_need"] is None
    assert "habitudes de consommation" in r["consumption_basket"]["caveat"]


def test_huile_de_palme_vers_l_afrique_du_nord_est_ecartee(des):
    """Ni produite ni consommée directement : importations anecdotiques."""
    r = des.estimate_national_need("1511", "DZA", observed_imports=_flux(5_000))
    assert r["consumption_basket"]["status"] == "not_attested"
    assert r["importable_need"] is None


def test_un_marche_reel_n_est_jamais_ecarte(des):
    """Le garde-fou le plus important : ne pas tuer un marché qui existe.

    Huile de palme vers l'Égypte et banane dessert vers l'Algérie sont
    structurellement identiques aux cas écartés ci-dessus — aucune production
    nationale ni régionale. Seul le flux les distingue.
    """
    for hs, iso, usd in (("1511", "EGY", 700_000_000), ("0803", "DZA", 250_000_000)):
        r = des.estimate_national_need(hs, iso, observed_imports=_flux(usd))
        assert r["consumption_basket"]["status"] == "attested", f"{hs}/{iso} écarté à tort"
        assert r["importable_need"] and r["importable_need"] > 0


def test_sans_flux_connu_on_ne_conclut_pas(des):
    """Absence de preuve n'est pas preuve d'absence : le marché est conservé."""
    r = des.estimate_national_need("0714", "DZA")
    assert r["consumption_basket"]["status"] == "unverifiable"
    assert r["consumption_basket"]["confidence"] == "low"
    assert r["consumption_basket"]["imports_known"] is False
    # Le besoin reste chiffré — mais explicitement signalé comme non vérifié.
    assert r["importable_need"] is not None
    assert "ni attestée ni écartée" in r["consumption_basket"]["caveat"]


def test_le_seuil_de_negligeabilite_suit_la_taille_du_pays(des):
    """Un plancher absolu qualifierait mal les petits et les grands marchés."""
    petit = des.estimate_national_need("0714", "SYC", observed_imports=_flux(0))
    grand = des.estimate_national_need("0714", "DZA", observed_imports=_flux(0))
    # Assertion inconditionnelle : un « if » laissait le test passer en silence
    # si l'un des deux jeux devenait indisponible — il n'aurait alors plus rien
    # vérifié, sans le dire.
    assert petit.get("available") and grand.get("available"), (
        "les deux pays témoins doivent être disponibles pour comparer les seuils"
    )
    seuils = [c["consumption_basket"]["negligible_threshold_usd"] for c in (petit, grand)]
    assert all(seuils), "les deux seuils doivent être calculés"
    assert seuils[0] < seuils[1], "le seuil doit croître avec la population"


def test_la_methode_du_seuil_est_exposee(des):
    """Une hypothèse de modélisation doit être lisible par qui la conteste."""
    r = des.estimate_national_need("0714", "DZA", observed_imports=_flux(0))
    basket = r["consumption_basket"]
    assert basket["threshold_basis"]
    assert basket["imports_usd"] == 0
    assert basket["negligible_threshold_usd"] > 0


# ── Le classement des marchés ────────────────────────────────────────────────

def _besoin(value, importable, statut="attested"):
    return {
        "available": True,
        "value": value,
        "importable_need": importable,
        "consumption_basket": {"status": statut},
    }


@pytest.fixture(scope="module")
def moteur():
    import importlib.util

    for path in (str(BACKEND), str(REPO_ROOT)):
        if path not in sys.path:
            sys.path.insert(0, path)
    spec = importlib.util.spec_from_file_location(
        "report_engine_under_test", BACKEND / "services" / "report_engine.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_un_marche_autosuffisant_est_ecarte_du_classement(moteur):
    """Besoin importable nul : le pays produit ce qu'il consomme."""
    assert moteur._market_is_addressable(_besoin(1_650_000, 0.0)) is False


def test_un_marche_non_atteste_est_ecarte_du_classement(moteur):
    assert moteur._market_is_addressable(_besoin(7_350_000, None, "not_attested")) is False


def test_un_marche_reel_reste_dans_le_classement(moteur):
    assert moteur._market_is_addressable(_besoin(1_010_000, 1_010_000)) is True


def test_le_classement_suit_le_besoin_importable_et_non_la_consommation(moteur):
    """Régression : trier sur « value » remettait l'auto-suffisant en tête."""
    marches = [
        {"destination_iso3": "CMR", "market_need": _besoin(1_650_000, 0.0)},
        {"destination_iso3": "DZA", "market_need": _besoin(1_010_000, 1_010_000)},
        {"destination_iso3": "TUN", "market_need": _besoin(900_000, 400_000)},
    ]
    retenus = [m for m in marches if moteur._market_is_addressable(m["market_need"])]
    retenus.sort(key=lambda m: (moteur._addressable_need(m["market_need"]) or 0), reverse=True)
    assert [m["destination_iso3"] for m in retenus] == ["DZA", "TUN"], (
        "le Cameroun auto-suffisant doit sortir, et l'ordre suivre l'importable"
    )


def test_un_importable_inconnu_se_rabat_sur_la_consommation(moteur):
    """Le repli documenté doit être atteignable.

    Le payload porte toujours la clé « importable_need », éventuellement à None :
    un test de présence de clé rendait ce repli impossible, et ces marchés
    étaient classés avec une demande nulle.
    """
    assert moteur._addressable_need(_besoin(500_000, None, "unverifiable")) == 500_000
