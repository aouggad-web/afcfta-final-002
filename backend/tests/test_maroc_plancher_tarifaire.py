"""Maroc — la rareté des zéros est un plancher tarifaire, pas une perte.

POURQUOI CE FICHIER EXISTE. Le diagnostic des zéros perdus
(`scripts/diagnostic_zeros_perdus.py`) a signalé le Maroc : 4 droits à 0 %
seulement sur 12 972 captés. La même signature, en Algérie, cachait 296 droits
supprimés par un miroir qui n'affiche pas les zéros.

L'examen a conclu l'inverse, et ces tests conservent ses deux preuves pour que
personne ne relance le travail, ni surtout ne « comble » ce qui n'est pas un
trou.

1. LE PLANCHER. Le Droit d'Importation marocain commence à 2,5 %, et la moitié
   du tarif porte ce taux. Un tarif dont le minimum est positif n'a pas de
   raison d'aligner des zéros : la rareté est une caractéristique.

2. LES QUATRE ZÉROS SONT COHÉRENTS. Ils portent tous sur le soufre (2503) —
   l'intrant des engrais phosphatés, cœur de l'industrie marocaine. Une
   franchise qui s'explique.

3. LES 142 POSITIONS MUETTES LE SONT À LA SOURCE. Elles ne portent aucune taxe
   dans le crawl — ni droit, ni TPI, ni TVA. Les 142 ont été interrogées une à
   une sur l'ADIL : le portail ne publie rien sur aucune. La collecte est
   fidèle ; l'indisponibilité est la seule réponse juste.

CE QUE CES TESTS NE PRÉTENDENT PAS. Ils n'établissent pas POURQUOI le portail
est muet sur ces 142 positions. Leur concentration dans les chapitres agricoles
suggère des régimes particuliers, mais cette lecture n'est pas sourcée et n'est
donc pas servie comme un fait.
"""

from __future__ import annotations

import json
import pathlib

import pytest

RACINE = pathlib.Path(__file__).resolve().parents[2]
CRAWL = RACINE / "backend" / "data" / "crawled" / "MAR_tariffs.json"
VERIFICATION = RACINE / "data" / "morocco" / "verification_positions_muettes.json"

DI = "Droit d'Importation (DI)"
PLANCHER_PUBLIE = "2.5 %"
SOUFRE = {"2503001000", "2503009010", "2503009020", "2503009090"}


@pytest.fixture(scope="module")
def lignes():
    if not CRAWL.exists():
        pytest.skip("crawl marocain absent")
    return json.loads(CRAWL.read_text(encoding="utf-8"))["sub_positions"]


def test_le_droit_d_importation_commence_a_deux_et_demi(lignes):
    """Le plancher, mesuré : aucun droit publié n'est inférieur à 2,5 %."""
    taux = []
    for ligne in lignes:
        brut = (ligne.get("taxes") or {}).get(DI)
        if brut is None:
            continue
        taux.append(float(str(brut).replace("%", "").replace(",", ".").strip()))
    assert taux, "aucun droit d'importation capté"
    positifs = [t for t in taux if t > 0]
    assert min(positifs) == 2.5
    # La moitié du tarif porte le plancher : c'est ce qui rend la rareté des
    # zéros intelligible sans supposer une perte.
    assert taux.count(2.5) / len(taux) > 0.5


def test_les_seuls_zeros_sont_le_soufre(lignes):
    """Quatre zéros, et ils s'expliquent : intrant des engrais phosphatés."""
    zeros = {
        ligne["code"]
        for ligne in lignes
        if str((ligne.get("taxes") or {}).get(DI, "")).strip() == "0 %"
    }
    assert zeros == SOUFRE


def test_les_positions_muettes_le_sont_a_la_source():
    """La preuve de l'examen, conservée : le portail ne publie rien sur les 142.

    Si ce test tombe parce que le nombre a changé, c'est que le tarif ou la
    collecte a bougé : il faut alors REFAIRE la vérification au portail, pas
    ajuster le chiffre.
    """
    if not VERIFICATION.exists() or not CRAWL.exists():
        pytest.skip("vérification ou crawl absent")
    verif = json.loads(VERIFICATION.read_text(encoding="utf-8"))
    muettes = {
        ligne["code"]
        for ligne in json.loads(CRAWL.read_text(encoding="utf-8"))["sub_positions"]
        if not (ligne.get("taxes") or {})
    }
    assert len(muettes) == 142
    assert set(verif["positions"]) == muettes
    assert set(verif["positions"].values()) == {"RIEN_PUBLIE"}


def test_l_examen_est_enregistre_dans_le_diagnostic():
    """Un cas réglé ne doit pas être re-signalé comme du travail à faire."""
    import sys

    sys.path.insert(0, str(RACINE / "scripts"))
    from diagnostic_zeros_perdus import EXAMENS_FAITS

    assert "MAR" in EXAMENS_FAITS
    assert "plancher tarifaire" in EXAMENS_FAITS["MAR"]
