"""Côte d'Ivoire : tarif officiel de la DGD (27/03/2026) ; RS, PCS, PCC et PUA
(circulaire DGD n° 2258), TVA sur la valeur en douane majorée des droits et
taxes d'entrée (directive UEMOA n° 02/98, art. 27). Fiche : CIV_prelevements_TVA_2026-10-10.json."""

import json
import os

import pytest

from services.calcul import calculer

SOCLE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "socle", "CIV.json")

pytestmark = pytest.mark.skipif(not os.path.exists(SOCLE), reason="socle absent (gitignoré)")


@pytest.fixture(scope="module")
def positions():
    with open(SOCLE, encoding="utf-8") as f:
        return json.load(f)["positions"]


def _calcul(position):
    r = calculer(position, 1000, devise_cif="XOF")["npf"]
    return r["etat"], {l["code"]: l for l in r["lignes"]}


def test_tissu_porte_les_prelevements_et_la_tva_sur_les_droits_d_entree(positions):
    """DD 10 % : 100 ; RS 10 ; PCS 8 ; PCC 5 ; PUA 2 ; TVA 18 % sur 1 125."""
    etat, lignes = _calcul(positions["5208110000"])
    assert [lignes[c]["montant"] for c in ("DD", "RS", "PCS", "PCC", "PUA")] == [100.0, 10.0, 8.0, 5.0, 2.0]
    assert lignes["TVA"]["base"] == 1125.0 and etat == "COMPLET"


def test_spiritueux_taxe_speciale_sur_valeur_et_droits_d_entree(positions):
    """CGI art. 418 : taxe sur valeur + droits hors TVA ; TVA sur le tout."""
    etat, lignes = _calcul(positions["2208201000"])
    assert lignes["TSBPT"]["base"] == 1225.0
    assert lignes["TVA"]["base"] == 1225.0 + lignes["TSBPT"]["montant"] and etat == "COMPLET"


def test_toutes_les_positions_portent_les_quatre_prelevements(positions):
    for p in positions.values():
        codes = {d["code"] for d in p["droits"]}
        if codes:
            assert {"RS", "PCS", "PCC", "PUA"} <= codes


def test_taxes_speciales_art_418_selon_le_tarif_officiel(positions):
    """Tarif DGD du 27/03/2026 : cosmétique 3304.99 à 15 % (TCB), cigares à
    57 % (TAB), sur valeur + droits d'entrée ; TVA sur le tout."""
    etat, lignes = _calcul(positions["3304990000"])
    assert (lignes["TCB"]["base"], lignes["TCB"]["montant"]) == (1225.0, 183.75)
    assert lignes["TVA"]["base"] == 1408.75 and etat == "COMPLET"
    assert _calcul(positions["2402100000"])[1]["TAB"]["taux_pct"] == 57.0


def test_codes_sans_legende_rendent_le_calcul_partiel(positions):
    """TFS et TSS (cigarettes) : codes du tarif sans légende, assiette inconnue."""
    etat, lignes = _calcul(positions["2402200000"])
    assert lignes["TFS"]["montant"] is None and etat != "COMPLET"


def test_droit_de_sortie_absent_du_calcul_d_import(positions):
    assert not any(d["code"] == "DUS" for p in positions.values() for d in p["droits"])


def test_viande_au_taux_du_tarif_officiel(positions):
    """0201.10 : DD 20 % et TVA 9 % au tarif de 2026 (35 % et sans TVA au portail de février)."""
    etat, lignes = _calcul(positions["0201100000"])
    assert lignes["DD"]["taux_pct"] == 20.0 and lignes["TVA"]["taux_pct"] == 9.0


def test_taxe_d_ajustement_dans_les_droits_d_entree(positions):
    """OMC WT/TPR/S/362 § 3.24 : TAI 10 % sur la valeur, comprise dans la base de la TVA.
    6402.19.10 : 1 000 + DD 100 + RS 10 + PCS 8 + PCC 5 + PUA 2 + TAI 100."""
    lignes = _calcul(positions["6402191000"])[1]
    assert lignes["TAI"]["montant"] == 100.0
    assert lignes["TVA"]["base"] == 1225.0


def test_tci_sans_assiette_rend_la_tva_indisponible(positions):
    """5310.10 : la TCI, droit d'entrée, n'a pas d'assiette établie ; la TVA ne se
    calcule pas comme si elle valait zéro."""
    etat, lignes = _calcul(positions["5310100000"])
    assert lignes["TAI"]["montant"] == 100.0
    assert lignes["TCI"]["montant"] is None
    assert lignes["TVA"]["montant"] is None and etat != "COMPLET"


def test_sucre_sans_base_tant_que_le_prix_de_declenchement_est_inconnu(positions):
    """OMC § 3.26 : le prix de déclenchement de la TCI forme la base des autres droits."""
    etat, lignes = _calcul(positions["1701120000"])
    assert all(l["montant"] is None for l in lignes.values()) and etat != "COMPLET"


def test_compteurs_d_assiette_du_manifeste(positions):
    with open(os.path.join(os.path.dirname(SOCLE), "MANIFESTE.json"), encoding="utf-8") as f:
        compteurs = json.load(f)["pays"]["CIV"]["compteurs"]
    origines = [d.get("assiette_origine") if d.get("assiette") else None for p in positions.values() for d in p["droits"]]
    assert compteurs["assiettes_source"] == origines.count("source")
    assert compteurs["assiettes_table"] == origines.count("regle_de_pays")
    assert compteurs["assiettes_indisponibles"] == origines.count(None)
