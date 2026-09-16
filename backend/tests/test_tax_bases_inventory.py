# -*- coding: utf-8 -*-
"""L'inventaire des assiettes doit détecter les désaccords, pas les lisser.

Le moteur de cascade ne lit que `COUNTRY_TAX_PROFILES`, une table écrite à la
main. Les fichiers collectés portent leur propre assiette. Les deux divergent
sur quinze couples pays/taxe, et le montant servi y est faux dans les deux sens.

Ces tests ne valident pas que les assiettes sont bonnes — la question est
ouverte et se tranche pays par pays. Ils garantissent que l'outil qui la pose
ne peut pas devenir aveugle : un désaccord doit rester visible, une assiette
quantitative ne doit pas passer pour valorielle, et le rapport doit exister.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from inventory_tax_bases import (  # noqa: E402
    QUANTITATIVE,
    VALORIELLE,
    VALORIELLE_PLAFONNEE,
    base_dependencies,
    base_kind,
)

RAPPORT = REPO_ROOT / "reports" / "ASSIETTES_ET_METHODES.json"


@pytest.fixture(scope="module")
def rapport() -> dict:
    assert RAPPORT.exists(), (
        f"{RAPPORT.relative_to(REPO_ROOT)} est un livrable versionné. "
        "Le régénérer avec scripts/inventory_tax_bases.py."
    )
    return json.loads(RAPPORT.read_text(encoding="utf-8"))


def test_duty_et_dd_designent_la_meme_taxe():
    """« CIF+Duty » et « CIF + DD » sont la même assiette écrite en deux langues."""
    assert base_dependencies("CIF+Duty") == base_dependencies("CIF + DD") == ["DD"]


def test_la_cascade_cedeao_est_lue_entierement():
    """Omettre RS et PCS sous-évalue la TVA de onze pays."""
    assert base_dependencies("CIF + DD + RS + PCS") == ["DD", "PCS", "RS"]


def test_une_assiette_quantitative_n_est_pas_valorielle():
    """« PN (KG) » est un poids : l'appliquer à une valeur produirait un montant faux."""
    assert base_kind("PN (KG)") == QUANTITATIVE
    assert base_kind("CIF") == VALORIELLE
    assert base_kind("CIF (plafond 15 000 XAF)") == VALORIELLE_PLAFONNEE


def test_le_rapport_nomme_ses_deux_sources(rapport):
    methode = rapport["methode"]
    assert "crawled" in methode["source_assiettes"]
    assert "COUNTRY_TAX_PROFILES" in methode["source_table_codee"]
    assert methode["limite"], "une assiette absente n'est pas une assiette inexistante"


def test_chaque_desaccord_porte_ses_deux_cotes(rapport):
    """Un désaccord sans ses deux termes ne serait pas arbitrable."""
    for ecart in rapport["desaccords"]:
        assert ecart["dependances_source"] is not None, ecart
        assert ecart["dependances_table_codee"] is not None, ecart
        assert set(ecart["dependances_source"]) != set(ecart["dependances_table_codee"]), ecart


def test_le_decompte_des_desaccords_est_coherent(rapport):
    assert rapport["synthese"]["desaccords"] == len(rapport["desaccords"])


def test_les_desaccords_non_tranches_restent_signales(rapport):
    """Ces cas sont ouverts ; les faire disparaître serait la régression à éviter.

    Quatre pays dérivés du Bénin — CPV, GMB, LBR, SLE — publient une assiette
    TVA incluant RS et PCS que la table codée omet, et leur propre loi de TVA
    n'a pas été établie. La Tunisie est dans le même état, pour d'autres
    raisons, consignées dans sa fiche.

    Préférer silencieusement la table codée, ou l'assiette publiée, les
    effacerait du rapport. Leur résolution passe par une détermination
    juridique assumée, pays par pays.
    """
    couples = {(e["pays"], e["taxe"]) for e in rapport["desaccords"]}
    for pays in ("CPV", "GMB", "LBR", "SLE", "TUN"):
        assert (pays, "TVA") in couples, (
            f"{pays} : le désaccord d'assiette TVA doit rester visible tant "
            "qu'aucun texte primaire ne l'a tranché."
        )


def test_les_desaccords_tranches_le_sont_par_un_texte_et_non_par_silence(rapport):
    """La bonne façon de faire disparaître un désaccord, et la seule.

    BEN, SEN, MLI, NER et TGO figuraient parmi les désaccords jusqu'à ce que
    la directive UEMOA établisse l'assiette de leur TVA. Ils n'y figurent plus
    — mais cela ne vaut que si le rapport dit ce que le moteur applique et au
    nom de quel texte. Un désaccord qui s'évanouit sans fondement cité serait
    indiscernable d'une régression.

    On vérifie aussi que l'assiette codée, plus étroite, reste consignée : la
    remplacer ne doit pas effacer la trace de ce qu'elle disait.
    """
    couples = {(e["pays"], e["taxe"]) for e in rapport["desaccords"]}
    for pays in ("BEN", "SEN", "MLI", "NER", "TGO", "KEN"):
        entree = rapport["par_pays"][pays]["taxes"]["TVA"]
        assert (pays, "TVA") not in couples, pays
        assert entree["assiette_appliquee_par_le_moteur"] == "TOUTES_LES_AUTRES_TAXES", pays
        assert entree["fondement_de_l_assiette_appliquee"], (
            f"{pays} : le rapport annonce une assiette élargie sans citer le "
            "texte qui l'établit"
        )
        assert entree["dependances_table_codee"] is not None, (
            f"{pays} : l'assiette codée, plus étroite, doit rester consignée"
        )


def test_une_taxe_lue_dans_la_source_ne_peut_pas_manquer_partout_d_assiette(rapport):
    """Deux affirmations qui ne peuvent pas être vraies ensemble.

    Le rapport annonçait « lue dans la source » pour les six taxes béninoises
    tout en comptant 6 129 positions sans assiette publiée sur 6 129 lignes.
    La cause : chaque ligne décrit ses taxes deux fois, dans un bloc compact
    sans assiette et dans un bloc détaillé qui en porte une, et les deux
    étaient comptés. Un rapport qui se contredit ne peut servir à décider.
    """
    incoherents = [
        (iso, taxe)
        for iso, bloc in rapport["par_pays"].items()
        for taxe, detail in bloc["taxes"].items()
        if detail["statut"] == "lue_dans_la_source"
        and detail["positions_sans_assiette_publiee"] >= bloc["lignes"]
    ]
    assert not incoherents, (
        "ces couples déclarent une assiette lue dans la source et, en même "
        f"temps, aucune position qui la porte : {incoherents}"
    )


def test_les_assiettes_declarees_au_niveau_du_jeu_sont_lues(rapport):
    """Une assiette déclarée une fois vaut pour toutes les lignes du fichier.

    MUS_tariffs.json porte calculation_rules.bases.DD.basis = « CIF » sans le
    répéter ligne par ligne. Ne lire que la position faisait compter Maurice
    comme dépourvue d'assiette sur ses 5 619 lignes — un coût d'indisponibilité
    entièrement imaginaire.
    """
    mus = rapport["par_pays"]["MUS"]["taxes"]["DD"]
    assert mus["statut"] == "lue_dans_la_source"
    assert mus["positions_sans_assiette_publiee"] == 0
    assert mus["assiette_publiee"]


def test_les_assiettes_non_valorielles_sont_identifiees(rapport):
    """Fondre un poids dans la cascade valorielle produirait des montants faux."""
    quantitatives = [
        (iso, taxe)
        for iso, bloc in rapport["par_pays"].items()
        for taxe, entree in bloc["taxes"].items()
        if entree["nature"] == QUANTITATIVE
    ]
    assert quantitatives, "le dépôt porte des assiettes au poids : elles doivent ressortir"
    assert all(iso == "TUN" for iso, _ in quantitatives), sorted(quantitatives)
