# -*- coding: utf-8 -*-
"""Le moteur doit liquider la TVA sur l'assiette que le texte établit.

Quatre textes primaires ont été lus et archivés — directive UEMOA, loi kényane,
loi ougandaise, code tunisien. Tous disposent de la même règle : la valeur en
douane augmentée de TOUS les droits et taxes perçus à l'entrée, la TVA seule
exclue de sa propre assiette.

`COUNTRY_TAX_PROFILES` appliquait « CIF + DD » à ces onze pays, amputant
l'assiette de tout le reste — pour la Tunisie en citant en référence l'article
même qui les inclut.

Ces tests verrouillent trois choses : la valeur légale sur un cas calculable à
la main, l'absence de régression là où un profil documenté existe hors du
registre, et le fait que la règle reste une règle et non une énumération.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "backend"))

from services.authentic_tariff_service import (  # noqa: E402
    ASSIETTE_TVA_ETABLIE,
    BASE_TVA_TOUTES_TAXES,
    COUNTRY_TAX_PROFILES,
    compute_tax_cascade,
)

REFS = REPO_ROOT / "backend" / "data" / "legal_refs" / "zlecaf_application"

#: Bénin, cas calculable à la main et chiffré dans la fiche UEMOA.
BEN_TAXES = {"DD": 20.0, "RS": 1.0, "PCS": 1.0, "PCC": 0.5, "PUA": 0.2, "TVA": 18.0}


def _etape(resultat: dict, code: str) -> dict:
    return next(s for s in resultat["steps"] if s["code"] == code)


def test_l_assiette_beninoise_est_celle_de_la_directive():
    """CIF 10 000 : assiette 12 270,00 et TVA 2 208,60, et non 12 000 / 2 160."""
    tva = _etape(compute_tax_cascade(10000.0, BEN_TAXES, "BEN"), "TVA")
    assert tva["base_value"] == 12270.00
    assert tva["amount"] == 2208.60


def test_le_texte_applique_est_cite_dans_le_resultat():
    """Une assiette servie sans sa source ne serait pas opposable."""
    resultat = compute_tax_cascade(10000.0, BEN_TAXES, "BEN")
    assert "02/98/CM/UEMOA" in resultat["legal_source"]
    assert "article 27" in resultat["legal_source"]


def test_la_tva_est_liquidee_en_dernier():
    """Son assiette contient les autres montants : ils doivent être connus."""
    resultat = compute_tax_cascade(10000.0, BEN_TAXES, "BEN")
    assert resultat["steps"][-1]["code"] == "TVA"


def test_la_regle_n_est_pas_une_enumeration():
    """Une taxe qui apparaît entre dans l'assiette sans qu'on ait à l'inscrire.

    C'est ce qui distingue cette correction de la table qu'elle remplace : une
    liste se périme dès qu'un prélèvement nouveau est collecté.
    """
    avec_taxe_neuve = dict(BEN_TAXES, TAXE_INEDITE=2.0)
    base_avant = _etape(compute_tax_cascade(10000.0, BEN_TAXES, "BEN"), "TVA")["base_value"]
    base_apres = _etape(compute_tax_cascade(10000.0, avec_taxe_neuve, "BEN"), "TVA")["base_value"]
    assert base_apres == base_avant + 200.0


def test_la_tva_n_entre_pas_dans_sa_propre_assiette():
    resultat = compute_tax_cascade(10000.0, BEN_TAXES, "BEN")
    tva = _etape(resultat, "TVA")
    autres = sum(s["amount"] for s in resultat["steps"] if s["code"] != "TVA")
    assert tva["base_value"] == pytest.approx(10000.0 + autres)


def test_un_profil_documente_hors_registre_reste_intact():
    """L'Algérie n'est pas dans le registre : rien ne doit y changer.

    Son profil documente une TVA assise sur CIF + DAPS + DD au titre de
    l'article 21 du CTCA, et un précompte liquidé APRÈS la TVA. Appliquer la
    règle générale y détruirait une méthode établie.
    """
    taxes = {"DAPS": 60.0, "DD": 30.0, "TCS": 0.0, "TVA": 19.0, "PRCT": 2.0}
    resultat = compute_tax_cascade(10000.0, taxes, "DZA")
    assert _etape(resultat, "TVA")["base_formula"] == "CIF + DAPS + DD"
    assert _etape(resultat, "TVA")["amount"] == 3610.00
    assert _etape(resultat, "PRCT")["amount"] == 332.20


def test_une_taxe_assise_sur_la_tva_desactive_la_regle():
    """Garde-fou anti-circularité.

    Si une taxe s'asseyait sur la TVA pendant que la TVA s'assied sur toutes les
    autres, la cascade n'aurait pas de solution. Le profil codé doit alors
    continuer de s'appliquer plutôt qu'un calcul faux.
    """
    profil = COUNTRY_TAX_PROFILES["BEN"]
    sauvegarde = dict(profil["tax_bases"])
    # PCS, et non PCC : seules les taxes présentes dans taxes_order conservent
    # l'assiette du profil, les autres étant réécrites sur CIF en amont.
    profil["tax_bases"] = dict(sauvegarde, PCS=("CIF", ["TVA"]))
    try:
        tva = _etape(compute_tax_cascade(10000.0, BEN_TAXES, "BEN"), "TVA")
        assert tva["base_formula"] != BASE_TVA_TOUTES_TAXES
        assert tva["base_value"] == 12000.00
    finally:
        profil["tax_bases"] = sauvegarde


@pytest.mark.parametrize("iso3", sorted(ASSIETTE_TVA_ETABLIE))
def test_chaque_pays_du_registre_cite_une_fiche_archivee(iso3):
    """Un pays inscrit sans sa détermination archivée serait une règle sans source."""
    regle = ASSIETTE_TVA_ETABLIE[iso3]
    assert regle["texte"], iso3
    assert (REFS / regle["fiche"]).exists(), regle["fiche"]
