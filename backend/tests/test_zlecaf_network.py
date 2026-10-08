"""
Tests de la carte « Réseau ZLECAf » (services/zlecaf_network.py) : chaque
statut doit être fondé sur une preuve nommée, et rien n'est inventé là où la
source se tait.
"""

import asyncio
import json
from datetime import date

from constants import AFRICAN_COUNTRIES
from services import zlecaf_implementation_registry as registry
from services import zlecaf_network as reseau_mod
from services.zlecaf_membership_status import NOT_SIGNED, SIGNED_NOT_RATIFIED
from services.zlecaf_network import (
    DEPLOIEMENT,
    NIVEAUX,
    NON_SIGNATAIRE,
    OFFRE_ACCEPTEE,
    SIGNE_NON_RATIFIE,
    construire_reseau,
)

JOUR = date(2026, 10, 8)


def _par_iso(reseau):
    return {p["iso3"]: p for p in reseau["pays"]}


def test_chaque_etat_present_une_seule_fois():
    reseau = construire_reseau(JOUR)
    iso3s = [p["iso3"] for p in reseau["pays"]]
    assert sorted(iso3s) == sorted(c["iso3"] for c in AFRICAN_COUNTRIES)
    assert len(iso3s) == len(set(iso3s))


def test_statut_porte_par_une_preuve_de_meme_niveau():
    for pays in construire_reseau(JOUR)["pays"]:
        assert pays["statut"] in NIVEAUX
        niveaux = {p["niveau"] for p in pays["preuves"]}
        assert pays["statut"] in niveaux, pays["iso3"]
        assert all(p["source"] for p in pays["preuves"])


def test_non_signataire_et_non_ratifiants_priment_sur_toute_autre_mention():
    pays = _par_iso(construire_reseau(JOUR))
    for iso3 in NOT_SIGNED:
        assert pays[iso3]["statut"] == NON_SIGNATAIRE
    for iso3 in SIGNED_NOT_RATIFIED:
        assert pays[iso3]["statut"] == SIGNE_NON_RATIFIE
    # Le Bénin figure à l'Annexe 1 (astérisqué) mais n'a pas ratifié.
    assert "BEN" in registry.ANNEXE1_PARTIES_2021
    assert pays["BEN"]["statut"] == SIGNE_NON_RATIFIE


def test_importateurs_en_vigueur_sont_en_deploiement():
    pays = _par_iso(construire_reseau(JOUR))
    for iso3, record in registry.RECORDS.items():
        if record.status == registry.APPLIED and registry.application_commencee(iso3, JOUR):
            assert pays[iso3]["statut"] == DEPLOIEMENT, iso3


def test_application_pas_encore_commencee_nest_pas_un_deploiement():
    # L'Ouganda n'applique qu'à partir du 13/02/2026 (attestation du gazettement).
    avant = _par_iso(construire_reseau(date(2026, 1, 1)))
    liens_uga = [
        lien
        for lien in construire_reseau(date(2026, 1, 1))["liaisons"]
        if lien["importateur"] == "UGA"
    ]
    assert liens_uga == []
    # Il reste en déploiement par la liste dtic de l'Afrique du Sud, qui le nomme.
    assert avant["UGA"]["statut"] == DEPLOIEMENT
    assert all(
        p["source"] != registry.RECORDS["UGA"].instrument_title for p in avant["UGA"]["preuves"]
    )


def test_annexe1_non_deployee_est_offre_acceptee():
    pays = _par_iso(construire_reseau(JOUR))
    assert pays["SEN"]["statut"] == OFFRE_ACCEPTEE


def test_liaisons_entre_ratifiants_sans_doublon_ni_boucle():
    reseau = construire_reseau(JOUR)
    pays = _par_iso(reseau)
    vues = set()
    for lien in reseau["liaisons"]:
        cle = (lien["importateur"], lien["origine"])
        assert cle not in vues
        vues.add(cle)
        assert lien["importateur"] != lien["origine"]
        assert lien["source"]
        for iso3 in cle:
            assert pays[iso3]["statut"] not in (NON_SIGNATAIRE, SIGNE_NON_RATIFIE)
        assert pays[lien["importateur"]]["statut"] == DEPLOIEMENT


def test_liaisons_algerie_suivent_la_circulaire():
    from services.zlecaf_schedule_dza import ACTIVE_PARTNERS

    origines = {
        lien["origine"]
        for lien in construire_reseau(JOUR)["liaisons"]
        if lien["importateur"] == "DZA"
    }
    assert origines == set(ACTIVE_PARTNERS)


def test_pib_une_seule_annee_sinon_none(tmp_path):
    fichier = tmp_path / "wb.json"
    fichier.write_text(
        json.dumps(
            {
                "data": {
                    "DZA": {"indicators": {"GDP": {"2024": 2.5e11, "2023": 2.4e11}}},
                    "ERI": {"indicators": {"GDP": {"2011": 2.0e9}}},
                }
            }
        )
    )
    pib = reseau_mod._pib(fichier)
    assert pib["DZA"] == 2.5e11
    assert pib["ERI"] is None  # pas de 2024 : jamais la valeur de 2011


def test_route_traduit_les_noms():
    from routes.zlecaf_network import get_zlecaf_network

    fr = _par_iso(asyncio.run(get_zlecaf_network(lang="fr")))
    en = _par_iso(asyncio.run(get_zlecaf_network(lang="en")))
    assert fr["DZA"]["nom"] and en["DZA"]["nom"]
    assert fr["DZA"]["statut"] == en["DZA"]["statut"]
