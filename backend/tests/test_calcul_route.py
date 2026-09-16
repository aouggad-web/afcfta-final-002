"""
Chaîne complète de calcul — chantier L3.

Socle → périmètre de la préférence → moteur → réponse. Ces tests vérifient ce
que la chaîne promet : un socle périmé n'est pas servi, une position absente
n'est pas remplacée par une voisine, une préférence non autorisée n'est jamais
appliquée, et chaque montant dit d'où il vient.
"""

import json
import os
import shutil
import sys

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from services import socle
from services.preference import taux_preferentiels

SOCLE_PRESENT = os.path.exists(socle.MANIFESTE)
besoin_socle = pytest.mark.skipif(
    not SOCLE_PRESENT, reason="socle absent : python3 scripts/build_socle.py"
)


@pytest.fixture(autouse=True)
def _cache_propre():
    socle.vider_cache()
    yield
    socle.vider_cache()


@pytest.fixture
def client():
    # La route est chargée par son chemin, sans passer par `routes/__init__.py`.
    # Elle n'a besoin ni de l'authentification ni des quotas — ceux-ci sont
    # posés au montage — et le test reste indépendant d'eux.
    import importlib.util

    chemin = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "routes", "calcul.py"
    )
    spec = importlib.util.spec_from_file_location("routes_calcul_test", chemin)
    module = importlib.util.module_from_spec(spec)
    sys.modules["routes_calcul_test"] = module  # pydantic résout ses annotations ici
    spec.loader.exec_module(module)

    app = FastAPI()
    app.include_router(module.router)
    return TestClient(app)


# ── Le chargeur refuse ce qu'il ne peut pas garantir ──────────────────────────
@besoin_socle
def test_un_socle_qui_ne_correspond_plus_a_son_empreinte_n_est_pas_servi(tmp_path):
    """Un socle périmé devient inerte au lieu de servir des montants qui ne
    correspondent plus à la donnée collectée."""
    fichier = os.path.join(socle.SOCLE_DIR, "CIV.json")
    sauvegarde = tmp_path / "CIV.json"
    shutil.copy(fichier, sauvegarde)
    try:
        with open(fichier, "r+", encoding="utf-8") as f:
            contenu = json.load(f)
            contenu["positions"]["7612900000"]["droits"][0]["taux"] = 99.0
            f.seek(0)
            json.dump(contenu, f, ensure_ascii=False, separators=(",", ":"))
            f.truncate()
        socle.vider_cache()
        with pytest.raises(socle.SocleIndisponible, match="ne correspond plus"):
            socle.charger("CIV")
    finally:
        shutil.copy(sauvegarde, fichier)
        socle.vider_cache()


@besoin_socle
def test_une_position_absente_leve_au_lieu_de_servir_une_voisine():
    with pytest.raises(KeyError):
        socle.position("DZA", "999999")


@besoin_socle
def test_le_niveau_reellement_servi_est_toujours_dit():
    # Le Ghana porte ses parents SH6 et ses enfants nationaux : les deux
    # niveaux sont adressables, et chacun se nomme.
    _, national = socle.position("GHA", "0101210000")
    assert national["niveau"] == "national"
    # Un code à six chiffres reste "hs6" même quand il correspond à une clé
    # du socle : ce n'est pas une sous-position nationale, le dire autrement
    # ferait annoncer une précision qui n'existe pas.
    _, parent = socle.position("GHA", "010121")
    assert parent["niveau"] == "hs6"
    # Un code national inconnu dont le parent SH6 existe est servi au parent —
    # mais la réponse le déclare, elle ne le laisse pas croire.
    _, remonte = socle.position("GHA", "0101219999")
    assert remonte["niveau"] == "hs6"


@besoin_socle
def test_la_devise_nationale_accompagne_la_provenance():
    _, provenance = socle.position("ZAF", "020830")
    assert provenance["devise_nationale"] == "ZAR"


def test_un_pays_hors_table_des_devises_ne_devine_pas_une_devise():
    assert socle.devise_nationale("XXX") is None


@besoin_socle
def test_aucune_remontee_au_chapitre_quand_le_parent_sh6_manque_lui_aussi():
    """La Côte d'Ivoire ne porte que des codes à dix chiffres : un code inconnu
    ne doit pas être servi par une position voisine du même chapitre."""
    with pytest.raises(KeyError):
        socle.position("CIV", "7612909999")


@pytest.mark.parametrize("code", ["", "12", "abc"])
def test_un_code_sh_trop_court_est_refuse(code):
    with pytest.raises(ValueError):
        socle.normaliser_code(code)


@pytest.mark.parametrize("pays", ["", "XX", "FRANCE", "12A"])
def test_un_code_pays_invalide_est_refuse(pays):
    with pytest.raises(ValueError):
        socle._iso3(pays)


# ── Le verrou juridique de la préférence ──────────────────────────────────────
@besoin_socle
def test_une_origine_hors_liste_admise_n_obtient_pas_la_preference():
    position, _ = socle.position("KEN", "01012100")
    decision = taux_preferentiels(position, "KEN", "FRA", "01012100")
    assert decision["applique"] is False
    assert decision["taux"] == {}
    assert "ne figure pas dans la liste" in decision["note"]


@besoin_socle
def test_un_couloir_non_autorise_reste_au_npf():
    """`OFFER_ONLY` et `PARTNER_NOTICE_REQUIRED` n'autorisent aucun calcul."""
    position, _ = socle.position("CIV", "7612900000")
    decision = taux_preferentiels(position, "CIV", "GHA", "7612900000")
    assert decision["applique"] is False
    assert decision["statut"] in {"OFFER_ONLY", "PARTNER_NOTICE_REQUIRED", "NOT_AVAILABLE"}


@besoin_socle
def test_un_couloir_autorise_sans_taux_trace_ne_derive_rien_du_npf():
    """Le Kenya admet le Ghana, mais sa source ne porte pas de colonne ZLECAf :
    aucun taux n'est fabriqué à partir du NPF."""
    position, _ = socle.position("KEN", "01012100")
    decision = taux_preferentiels(position, "KEN", "GHA", "01012100")
    assert decision["applique"] is False
    assert decision["statut"] == "PREFERENCE_NON_TRACEE"
    assert decision["taux"] == {}


@besoin_socle
def test_le_calendrier_algerien_rend_un_taux_trace_pas_un_echec_silencieux(monkeypatch):
    """Régression : les deux derniers arguments de `compute_dza_zlecaf_rate`
    étaient inversés (`npf` passé où `origine_iso3` était attendu), ce qui
    faisait lever `.upper()` sur un flottant — capté par un `except` large,
    et rendait `PREFERENCE_NON_TRACEE` sur tout calcul algérien passant par
    le calendrier plutôt que par la colonne préférentielle du socle.

    Aucun couloir algérien n'est aujourd'hui autorisé au registre
    (fail-closed, faute de preuve d'application bilatérale) : le verrou 1 est
    donc simulé ici pour exercer le verrou 2 — celui que le bug cassait —
    indépendamment de l'état, à ce jour transitoire, du registre.
    """
    from services import zlecaf_implementation_registry
    from services.zlecaf_schedule_dza import ACTIVE_PARTNERS, is_frozen, tariff_list

    monkeypatch.setattr(
        zlecaf_implementation_registry,
        "implementation_decision",
        lambda destination, origine: {
            "applied": True,
            "status": "APPLIED",
            "note": "simulé pour le test",
        },
    )

    origine = sorted(ACTIVE_PARTNERS)[0]
    code = next(
        (
            c
            for c in ("2201101100", "0101210000", "7612900000")
            if not is_frozen(c) and tariff_list(c) in ("A", "B")
        ),
        None,
    )
    if code is None:
        pytest.skip("aucune position de liste (A)/(B) sous la main")
    position, _ = socle.position("DZA", code)
    from services.preference import _colonne_de_la_position

    if _colonne_de_la_position(position) is not None:
        pytest.skip(
            "cette position porte déjà une colonne préférentielle : le calendrier n'est pas sollicité"
        )
    decision = taux_preferentiels(position, "DZA", origine, code)
    assert decision["statut"] != "PREFERENCE_NON_TRACEE"
    assert decision["applique"] is True
    assert decision["taux"]["DD"]["taux"] is not None


def test_le_perimetre_algerien_couvre_le_daps_avec_sa_reference():
    """Circulaire 482/2024 II-2, art. 2 de la LFC 2018. Le périmètre est
    national : il est déclaré, jamais déduit d'une règle générale."""
    from services.preference import PERIMETRES_NATIONAUX
    from services.zlecaf_schedule_dza import ACTIVE_PARTNERS, is_frozen, tariff_list

    etendue = PERIMETRES_NATIONAUX["DZA"]
    origine = sorted(ACTIVE_PARTNERS)[0]
    # Une position des listes (A)/(B), non gelée, importée d'un partenaire actif.
    code = next(
        (
            c
            for c in ("2201101100", "0101210000", "7612900000")
            if not is_frozen(c) and tariff_list(c) in ("A", "B")
        ),
        None,
    )
    if code is None:
        pytest.skip("aucune position de liste (A)/(B) sous la main")
    couvert = etendue(code, origine)
    assert "DAPS" in couvert
    assert "482/2024" in couvert["DAPS"]
    # Hors partenaire actif, l'exonération ne s'applique pas.
    assert etendue(code, "FRA") == {}


# ── La route ──────────────────────────────────────────────────────────────────
@besoin_socle
def test_la_reponse_dit_d_ou_vient_chaque_chiffre(client):
    reponse = client.post(
        "/calcul",
        json={"destination": "CIV", "code_sh": "7612900000", "valeur_cif": 1000},
    )
    assert reponse.status_code == 200
    corps = reponse.json()
    assert corps["npf"]["total_droits"] == 380.0
    provenance = corps["provenance"]
    assert provenance["niveau"] == "national"
    assert provenance["source"]["sha256"]
    assert provenance["source"]["fichier"].startswith("backend/data/")
    assert provenance["couverture"]["etat"] in {"COMPLET", "PARTIEL", "VIDE"}


@besoin_socle
def test_un_droit_specifique_sans_quantite_est_indisponible_pas_approche(client):
    sans = client.post(
        "/calcul", json={"destination": "ZAF", "code_sh": "020830", "valeur_cif": 1000}
    ).json()
    assert sans["npf"]["etat"] == "INDISPONIBLE"
    # La TVA sud-africaine n'est pas non plus tracée à la source (crawl SARS) :
    # le manque de quantité pour le DD et l'absence structurelle de TVA sont
    # deux causes distinctes, toutes deux nommées.
    assert sans["npf"]["manques"] == [
        {"code": "DD", "motif": "QUANTITE_REQUISE"},
        {"code": "TVA", "motif": "NON_TRACEE_A_LA_SOURCE"},
    ]

    avec = client.post(
        "/calcul",
        json={"destination": "ZAF", "code_sh": "020830", "valeur_cif": 1000, "quantite": 500},
    ).json()
    assert avec["npf"]["total_droits"] == 40.0  # 8c/kg × 500 kg, et non 8 %


@besoin_socle
def test_sans_origine_aucune_preference_n_est_supposee(client):
    corps = client.post(
        "/calcul",
        json={"destination": "DZA", "code_sh": "2201101100", "valeur_cif": 100000},
    ).json()
    assert corps["preference_zlecaf"]["statut"] == "ORIGINE_NON_FOURNIE"
    assert "preference" not in corps


@besoin_socle
@pytest.mark.parametrize(
    "charge,attendu",
    [
        ({"destination": "DZA", "code_sh": "999999", "valeur_cif": 1000}, 404),
        ({"destination": "XX", "code_sh": "010121", "valeur_cif": 1000}, 422),
        ({"destination": "DZA", "code_sh": "2201101100", "valeur_cif": -5}, 422),
        ({"destination": "DZA", "code_sh": "12", "valeur_cif": 1000}, 422),
    ],
)
def test_les_demandes_invalides_sont_refusees_explicitement(client, charge, attendu):
    assert client.post("/calcul", json=charge).status_code == attendu


@besoin_socle
def test_la_liste_des_pays_annonce_les_couvertures_partielles(client):
    corps = client.get("/calcul/pays").json()
    assert corps["totaux"]["pays"] == len(corps["pays"])
    # Les pays sans TVA à la source sont annoncés partiels, pas complétés.
    assert "ZAF" in corps["totaux"]["pays_partiels"]
    assert corps["pays"]["ZAF"]["etat"] == "PARTIEL"
    assert set(corps["totaux"]["pays_vides"]) == {"DJI", "ERI"}
