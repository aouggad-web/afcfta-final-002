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
def test_un_crawl_source_modifie_sans_reconstruction_n_est_pas_servi(tmp_path):
    """Le socle peut correspondre à son propre manifeste tout en datant d'un
    crawl que la collecte a depuis remplacé sans reconstruction. Deux
    empreintes identiques (socle), une source différente : la seconde
    vérification doit, elle aussi, refuser de servir."""
    entree = socle.manifeste()["pays"]["CIV"]
    source = os.path.join(socle.RACINE, entree["source_fichier"])
    sauvegarde = tmp_path / "CIV_tariffs.json"
    shutil.copy(source, sauvegarde)
    try:
        with open(source, "r+", encoding="utf-8") as f:
            contenu = f.read()
            f.seek(0)
            f.write(contenu + " ")
            f.truncate()
        socle.vider_cache()
        with pytest.raises(socle.SocleIndisponible, match="crawl source a changé"):
            socle.charger("CIV")
    finally:
        shutil.copy(sauvegarde, source)
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


# ── Union douanière : libre circulation, prioritaire sur la ZLECAf ───────────
@besoin_socle
def test_deux_membres_d_une_meme_union_douaniere_echangent_a_droit_nul(client):
    """Botswana → Afrique du Sud : deux membres de la SACU. Le droit de douane
    est nul par définition du marché unique, quelle que soit la position et
    quel que soit l'état de la ZLECAf. Avant ce correctif, la route unifiée
    liquidait le droit NPF plein (8c/kg) sur un échange en libre circulation."""
    corps = client.post(
        "/calcul",
        json={
            "destination": "ZAF",
            "origine": "BWA",
            "code_sh": "020830",
            "valeur_cif": 10000,
            "quantite": 100,
        },
    ).json()
    npf = {ligne["code"]: ligne for ligne in corps["npf"]["lignes"]}
    pref = {ligne["code"]: ligne for ligne in corps["preference"]["lignes"]}
    assert npf["DD"]["montant"] == 8.0  # 8c/kg × 100 kg, régime NPF
    assert pref["DD"]["montant"] == 0.0  # libre circulation intra-SACU
    assert corps["regime_commercial"]["regime"] == "UNION_DOUANIERE"
    assert corps["regime_commercial"]["code_bloc"] == "SACU"


@besoin_socle
def test_une_union_douaniere_n_est_jamais_presentee_comme_une_preference_zlecaf(client):
    """La confusion de régimes est le défaut que cette PR refuse : afficher
    « préférence ZLECAf appliquée » là où la ZLECAf est précisément écartée
    serait la même faute qu'une colonne COMESA lue comme un taux ZLECAf."""
    corps = client.post(
        "/calcul",
        json={
            "destination": "ZAF",
            "origine": "BWA",
            "code_sh": "020830",
            "valeur_cif": 10000,
            "quantite": 100,
        },
    ).json()
    assert corps["preference_zlecaf"]["applique"] is False
    assert corps["preference_zlecaf"]["statut"] == "REGIME_UNION_DOUANIERE"
    assert "union douanière" in corps["preference_zlecaf"]["note"]


@besoin_socle
def test_la_franchise_intra_union_ne_touche_pas_la_fiscalite_interne(client):
    """Le périmètre est le seul droit de douane. Étendre la franchise à la TVA
    ou aux accises ferait disparaître des taxes réellement perçues."""
    corps = client.post(
        "/calcul",
        json={
            "destination": "CMR",
            "origine": "GAB",
            "code_sh": "01011010",
            "valeur_cif": 10000,
        },
    ).json()
    assert corps["regime_commercial"]["code_bloc"] == "CEMAC"
    pref = {ligne["code"]: ligne for ligne in corps["preference"]["lignes"]}
    assert pref["DD"]["taux_pct"] == 0.0
    # Tout prélèvement hors droit de douane garde son taux NPF.
    npf = {ligne["code"]: ligne for ligne in corps["npf"]["lignes"]}
    for code, ligne in npf.items():
        if code != "DD" and ligne["statut"] == "CALCULE":
            assert pref[code]["taux_pct"] == ligne["taux_pct"]


@besoin_socle
def test_une_zone_de_libre_echange_ne_donne_aucune_franchise_automatique(client):
    """CEDEAO : la franchise dépend des règles d'origine et des listes
    sensibles, que ce moteur n'a pas. La rendre à 0 % serait fabriquer une
    exonération — le couloir reste au régime que le registre décide."""
    corps = client.post(
        "/calcul",
        json={
            "destination": "CIV",
            "origine": "GHA",
            "code_sh": "7612900000",
            "valeur_cif": 10000,
        },
    ).json()
    assert corps["regime_commercial"]["regime"] == "ZLECAF"
    assert corps["regime_commercial"].get("code_bloc") is None


@besoin_socle
def test_la_fiscalite_interne_diverge_entre_membres_d_une_meme_union(client):
    """Une union douanière harmonise le tarif *extérieur* et supprime le droit
    *intérieur* — elle n'harmonise pas la fiscalité interne. Sur la même
    position 01011010, importée depuis le même partenaire CEMAC, le Cameroun
    liquide 19,25 % de TVA et le Gabon 18 %. Supposer un taux de bloc unique
    ferait payer au Gabon la TVA camerounaise."""
    taux = {}
    for destination, origine in (("CMR", "GAB"), ("GAB", "CMR")):
        corps = client.post(
            "/calcul",
            json={
                "destination": destination,
                "origine": origine,
                "code_sh": "01011010",
                "valeur_cif": 10000,
            },
        ).json()
        assert corps["regime_commercial"]["code_bloc"] == "CEMAC"
        lignes = {ligne["code"]: ligne for ligne in corps["preference"]["lignes"]}
        assert lignes["DD"]["taux_pct"] == 0.0  # franchise intra-union des deux côtés
        taux[destination] = lignes["TVA"]["taux_pct"]

    assert taux["CMR"] == 19.25
    assert taux["GAB"] == 18.0
    assert taux["CMR"] != taux["GAB"], "la TVA doit rester celle du pays de destination"


@besoin_socle
def test_une_tva_non_collectee_est_nommee_au_lieu_d_etre_comptee_zero(client):
    """Le revers de la règle précédente : quand la fiscalité interne du pays
    de destination n'est pas collectée, le total ne doit pas se présenter comme
    complet. Les cinq pays SACU sont `PENDING_OFFICIAL_COLLECTION` pour la TVA
    (registre des sources nationales) : un import intra-SACU a donc un droit de
    douane nul *et* une TVA inconnue. Sans ce garde-fou, le calcul afficherait
    « rien à payer » sur une importation qui supporte réellement la TVA."""
    corps = client.post(
        "/calcul",
        json={
            "destination": "ZAF",
            "origine": "BWA",
            "code_sh": "010121",
            "valeur_cif": 10000,
        },
    ).json()
    preference = corps["preference"]
    assert preference["etat"] != "COMPLET"
    assert {"code": "TVA", "motif": "NON_TRACEE_A_LA_SOURCE"} in preference["manques"]
    # Aucune économie n'est annoncée : comparer deux totaux incomplets
    # produirait un chiffre plausible construit sur une base inconnue.
    assert corps["economie"] is None


# ── Le bloc réglementaire — chantier L4 ───────────────────────────────────────
@besoin_socle
def test_la_route_sert_le_bloc_reglementaire_comme_le_chemin_historique(client):
    """`build_regulatory_blocks` est le point d'entrée unique de toutes les
    routes de calcul. Ne pas l'appeler ici faisait dire à la même importation
    deux choses différentes selon la route servie."""
    corps = client.post(
        "/calcul",
        json={
            "destination": "CIV",
            "origine": "GHA",
            "code_sh": "7612900000",
            "valeur_cif": 10000,
        },
    ).json()
    assert corps["regulatory_compliance"]["country_iso3"] == "CIV"
    assert "regulatory_cost_total" in corps["regulatory_cost"]
    assert "reliability" in corps["regulatory_reported"]


@besoin_socle
def test_les_frais_reglementaires_n_entrent_jamais_dans_le_cout_douanier(client):
    """L'invariant du bloc : il est informatif. Un frais de prestataire ajouté
    au total douanier ferait payer à l'importateur une somme que la douane ne
    perçoit pas — et la rendrait indiscernable d'un droit."""
    # Couloir Ghana → Nigeria : l'un des rares dont les frais réglementaires
    # soient réellement chiffrés. Ailleurs le service rend `None` — « non
    # chiffré » — et le test ne mordrait sur rien.
    charge = {
        "destination": "NGA",
        "origine": "GHA",
        "code_sh": "0101210000",
        "valeur_cif": 10000,
    }
    corps = client.post("/calcul", json=charge).json()
    frais = corps["regulatory_cost"]["regulatory_cost_total"]
    assert frais, "le couloir de référence doit porter un frais chiffré"
    # Le total douanier reste exactement la somme des droits liquidés.
    total_lignes = sum(
        ligne["montant"] for ligne in corps["npf"]["lignes"] if ligne["statut"] == "CALCULE"
    )
    assert corps["npf"]["total_droits"] == pytest.approx(total_lignes, abs=0.01)
    assert corps["npf"]["total_a_payer"] == pytest.approx(
        corps["valeur_cif"] + corps["npf"]["total_droits"], abs=0.01
    )


@besoin_socle
def test_un_bloc_reglementaire_en_panne_n_interrompt_pas_le_calcul(client, monkeypatch):
    """Fail-safe : l'indisponibilité du registre réglementaire rend trois
    `None` — « non consulté », jamais « zéro frais » — et laisse le calcul
    tarifaire intact."""
    import routes_calcul_test as module

    def _tombe(*_args, **_kwargs):
        raise RuntimeError("registre réglementaire indisponible")

    monkeypatch.setattr(module, "build_regulatory_blocks", _tombe)
    corps = client.post(
        "/calcul",
        json={"destination": "CIV", "code_sh": "7612900000", "valeur_cif": 1000},
    ).json()
    assert corps["npf"]["total_droits"] == 380.0
    assert corps["npf"]["etat"] in {"COMPLET", "PARTIEL"}
    for cle in ("regulatory_compliance", "regulatory_cost", "regulatory_reported"):
        assert corps[cle] is None
