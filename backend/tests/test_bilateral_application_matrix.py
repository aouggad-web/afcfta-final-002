"""Le tableau bilatéral doit rester une lecture des sources, pas une opinion.

Ces tests ne vérifient pas que le rapport existe — un rapport peut exister et
mentir. Ils vérifient les propriétés dont dépend sa valeur : qu'aucune case
n'est remplie par défaut, que les listes ne sont pas recopiées, et qu'une
préférence n'est jamais accordée à une origine qui ne peut pas y prétendre.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parents[2]


def _charger_generateur():
    """Charge le script par chemin : scripts/ n'est pas un paquet importable."""
    chemin = RACINE / "scripts" / "build_bilateral_application_matrix.py"
    spec = importlib.util.spec_from_file_location("matrice_bilaterale", chemin)
    module = importlib.util.module_from_spec(spec)
    sys.modules["matrice_bilaterale"] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def rapport():
    return _charger_generateur().construire()


def test_aucune_origine_non_ratifiante_ne_recoit_de_preference(rapport):
    """La garde la plus simple, et celle qui coûterait le plus cher.

    Le Bénin, la Libye, le Soudan et le Soudan du Sud ont signé sans déposer
    leurs instruments ; l'Érythrée n'a pas signé. Aucune destination ne peut
    leur accorder le tarif ZLECAf. Une case ACCORDEE pour l'un d'eux ferait
    calculer un droit réduit sur un flux qui n'y a pas droit.
    """
    from services.zlecaf_membership_status import NOT_SIGNED, SIGNED_NOT_RATIFIED

    sans_droit = set(NOT_SIGNED) | set(SIGNED_NOT_RATIFIED)
    assert sans_droit, "la garde n'aurait rien à garder"

    fautes = [
        f"{dest}<-{org}"
        for dest, ligne in rapport["couples"].items()
        for org, case in ligne.items()
        if org in sans_droit and case["etat"] == "ACCORDEE"
    ]
    assert not fautes, f"préférence accordée à une origine sans droit : {fautes}"


def test_une_origine_non_ratifiante_nommee_par_un_acte_est_signalee():
    """La garde précédente est satisfaite par construction ; celle-ci mord.

    Le contrôle de ratification précède la lecture des listes : une origine
    non ratifiante ressort ORIGINE_NON_RATIFIANTE qu'un acte national la
    nomme ou non. C'est le bon comportement pour la case — mais il masquerait
    une contradiction entre deux sources primaires. On vérifie qu'elle est
    publiée au lieu d'être avalée.
    """
    module = _charger_generateur()
    vraies = module.listes_verifiees

    def avec_un_beninois_ajoute():
        listes = vraies()
        listes["MAR"] = {**listes["MAR"], "origines": {**listes["MAR"]["origines"], "BEN": "5 ans"}}
        return listes

    module.listes_verifiees = avec_un_beninois_ajoute
    try:
        truque = module.construire()
    finally:
        module.listes_verifiees = vraies

    case = truque["couples"]["MAR"]["BEN"]
    assert case["etat"] == "ORIGINE_NON_RATIFIANTE"
    assert "contradiction" in case, "la divergence serait passée sous silence"

    cas = truque["contradictions_ratification"]["cas"]
    assert {"destination": "MAR", "origine": "BEN"}.items() <= cas[0].items()

    # Et sur les listes réelles, aucune contradiction de ce type ne subsiste.
    assert vraies() is not None
    assert module.construire()["contradictions_ratification"]["cas"] == []


def test_une_destination_non_etablie_n_est_jamais_un_refus(rapport):
    """Ne pas savoir et refuser sont deux choses ; les confondre est le défaut
    que ce tableau existe pour éviter.

    Une destination sans liste vérifiée ne doit produire que des cases
    DESTINATION_NON_ETABLIE — jamais NON_ACCORDEE, qui affirmerait un refus
    que personne n'a constaté.
    """
    etablies = set(rapport["destinations_etablies"])
    assert rapport["destinations_non_etablies"], "toutes les destinations seraient établies"

    for dest in rapport["destinations_non_etablies"]:
        assert dest not in etablies
        etats = {c["etat"] for c in rapport["couples"][dest].values()}
        assert etats <= {"DESTINATION_NON_ETABLIE", "ORIGINE_NON_RATIFIANTE", "MEME_PAYS"}, (
            f"{dest} porte un état qu'aucune source ne soutient : {etats}"
        )


def test_les_listes_ne_sont_pas_recopiees_dans_le_generateur(rapport):
    """Chaque liste doit provenir de sa source d'autorité.

    On confronte les effectifs du rapport à ceux lus indépendamment dans les
    modules et fiches. Une liste recopiée dans le générateur passerait ce test
    le jour de sa recopie, et le trahirait dès la première divergence.
    """
    import json

    from services.zlecaf_implementation_registry import RECORDS
    from services.zlecaf_schedule_dza import ACTIVE_PARTNERS
    from services.zlecaf_schedule_zaf import ACTIVE_PARTNERS_ZAF

    fiches = RACINE / "backend" / "data" / "legal_refs" / "zlecaf_application"
    mar = json.loads((fiches / "MAR_application_2026-09-13.json").read_text(encoding="utf-8"))
    attendu = {
        "DZA": len(ACTIVE_PARTNERS),
        "ZAF": len(ACTIVE_PARTNERS_ZAF),
        "KEN": len(RECORDS["KEN"].accepted_origins),
        "MAR": mar["accepted_origins"]["count"],
    }
    for iso, compte in attendu.items():
        assert rapport["destinations_etablies"][iso]["origines_admises"] == compte, iso

    # Le compte marocain doit lui-même rester la somme de ses deux groupes :
    # la fiche publie un total ET son détail, et les deux peuvent diverger.
    p1 = len(mar["accepted_origins"]["P1"]["iso3"])
    p2 = len(mar["accepted_origins"]["P2"]["iso3"])
    assert p1 + p2 == mar["accepted_origins"]["count"]


def test_les_asymetries_sont_verifiables_case_par_case(rapport):
    """Une asymétrie annoncée doit se lire dans le tableau lui-même.

    C'est la conclusion la plus forte du rapport — « ce pays vous admet, vous
    ne l'admettez pas » — donc celle qui doit le moins reposer sur la parole
    du générateur.
    """
    asymetries = rapport["reciprocite"]["asymetries"]
    assert asymetries, "le croisement ne révélerait rien"

    for a in asymetries:
        donneur, receveur = a["accorde_par"], a["non_accorde_par"]
        assert rapport["couples"][donneur][receveur]["etat"] == "ACCORDEE"
        assert rapport["couples"][receveur][donneur]["etat"] == "NON_ACCORDEE"

    for paire in rapport["reciprocite"]["confirmees"]:
        a, b = paire.split("<->")
        assert rapport["couples"][a][b]["etat"] == "ACCORDEE"
        assert rapport["couples"][b][a]["etat"] == "ACCORDEE"


def test_toute_case_accordee_nomme_le_texte_qui_la_fonde(rapport):
    """Un montant sans source n'a pas de valeur ; une préférence non plus."""
    sans_fondement = [
        f"{dest}<-{org}"
        for dest, ligne in rapport["couples"].items()
        for org, case in ligne.items()
        if case["etat"] == "ACCORDEE" and not case.get("fondement")
    ]
    assert not sans_fondement, f"préférence sans texte cité : {sans_fondement}"


def test_la_couverture_annoncee_correspond_aux_cases_comptees(rapport):
    """Le chiffre mis en avant doit être celui que le tableau contient.

    Annoncer une couverture plus flatteuse que la réalité des cases serait
    exactement le travers que ce rapport dénonce.
    """
    compte = rapport["repartition_des_couples"]
    renseignes = compte.get("ACCORDEE", 0) + compte.get("NON_ACCORDEE", 0)
    attendu = round(100 * renseignes / rapport["couples_possibles"], 2)

    assert rapport["couverture_pct"] == attendu
    assert sum(compte.values()) == rapport["couples_possibles"]
