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
    INSTRUMENT_ADOPTE,
    NIVEAUX,
    NON_SIGNATAIRE,
    OFFRE_TARIFAIRE,
    SIGNE_NON_RATIFIE,
    construire_reseau,
)
from services.zlecaf_schedule_zaf import DATES_ENTREE_ZAF

JOUR = date(2026, 10, 8)


def _par_iso(reseau):
    return {p["iso3"]: p for p in reseau["pays"]}


def _liens(reseau, importateur):
    return {lien["origine"] for lien in reseau["liaisons"] if lien["importateur"] == importateur}


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


def test_deploiement_reserve_aux_importateurs_en_vigueur():
    pays = _par_iso(construire_reseau(JOUR))
    attendus = {
        iso3
        for iso3, r in registry.RECORDS.items()
        if r.status == registry.APPLIED and registry.application_commencee(iso3, JOUR)
    } | {"ZAF"}
    deployes = {k for k, p in pays.items() if p["statut"] == DEPLOIEMENT}
    assert deployes == attendus


def test_etre_nomme_par_un_partenaire_ne_vaut_pas_deploiement():
    # Le Burundi est dans la General Note O sud-africaine, mais sa propre date
    # d'application n'est pas établie (fiche BDI_application_2026-09-27.json).
    pays = _par_iso(construire_reseau(JOUR))
    assert "BDI" in DATES_ENTREE_ZAF
    assert pays["BDI"]["statut"] != DEPLOIEMENT
    assert all(p["niveau"] != DEPLOIEMENT for p in pays["BDI"]["preuves"])
    # Le Ghana est nommé par l'Algérie et l'Afrique du Sud : liaisons, pas déploiement.
    assert pays["GHA"]["statut"] != DEPLOIEMENT


def test_liaisons_sud_africaines_suivent_la_date_de_chaque_notice():
    avant = construire_reseau(date(2025, 2, 20))
    apres = construire_reseau(date(2025, 2, 21))
    assert "BDI" not in _liens(avant, "ZAF")
    assert "BDI" in _liens(apres, "ZAF")
    assert _liens(construire_reseau(date(2024, 1, 30)), "ZAF") == set()


def test_application_pas_encore_commencee_nest_ni_liaison_ni_deploiement():
    # L'Ouganda n'applique qu'à partir du 13/02/2026 (attestation du gazettement).
    reseau = construire_reseau(date(2026, 1, 1))
    assert _liens(reseau, "UGA") == set()
    assert _par_iso(reseau)["UGA"]["statut"] != DEPLOIEMENT


def test_offre_et_instrument():
    pays = _par_iso(construire_reseau(JOUR))
    assert pays["SEN"]["statut"] == OFFRE_TARIFAIRE  # Annexe 1
    assert pays["ZWE"]["statut"] == OFFRE_TARIFAIRE  # barème archivé
    assert pays["CIV"]["statut"] == INSTRUMENT_ADOPTE


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


def test_liaisons_filtrent_doublons_boucles_et_non_ratifiants(monkeypatch):
    record = registry.RECORDS["DZA"]
    faux = record.__class__(
        **{**record.__dict__, "accepted_origins": record.accepted_origins | {"DZA", "BEN"}}
    )
    monkeypatch.setitem(registry.RECORDS, "DZA", faux)
    origines = _liens(construire_reseau(JOUR), "DZA")
    assert "DZA" not in origines  # boucle
    assert "BEN" not in origines  # non ratifiant
    assert origines == set(record.accepted_origins)


def test_liaisons_algerie_suivent_la_circulaire():
    from services.zlecaf_schedule_dza import ACTIVE_PARTNERS

    assert _liens(construire_reseau(JOUR), "DZA") == set(ACTIVE_PARTNERS)


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


def test_route_traduit_les_noms_et_nomme_la_rasd():
    from routes.zlecaf_network import get_zlecaf_network

    fr = _par_iso(asyncio.run(get_zlecaf_network(lang="fr")))
    en = _par_iso(asyncio.run(get_zlecaf_network(lang="en")))
    assert fr["DZA"]["nom"] == "Algérie"
    assert en["DZA"]["nom"] == "Algeria"
    assert fr["DZA"]["statut"] == en["DZA"]["statut"]
    # Sans traduction, le nom vient de constants, jamais le code ISO2.
    assert fr["ESH"]["nom"] not in ("EH", "ESH")
    assert "nom_constants" not in fr["ESH"]
