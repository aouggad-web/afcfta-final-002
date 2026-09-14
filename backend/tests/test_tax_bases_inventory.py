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


def test_les_desaccords_connus_restent_signales(rapport):
    """Ces cas sont ouverts, non résolus.

    Les faire disparaître en préférant silencieusement la table codée serait la
    régression que ce rapport existe pour empêcher. Leur résolution devra passer
    par une correction assumée, pays par pays.
    """
    couples = {(e["pays"], e["taxe"]) for e in rapport["desaccords"]}
    for pays in ("BEN", "SEN", "MLI", "NER", "TGO"):
        assert (pays, "TVA") in couples, (
            f"{pays} : la source publie une assiette TVA incluant RS et PCS que "
            "la table codée omet. Ce désaccord doit rester visible tant qu'il "
            "n'est pas tranché."
        )


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
