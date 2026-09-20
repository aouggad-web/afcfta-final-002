"""Algérie — 296 droits de douane à 0 %, repris à la source primaire.

CE QUI ÉTAIT FAUX. La collecte algérienne ne lit pas la DGD : elle lit
`conformepro.dz`, qui republie ses données. Ce miroir **supprime le bloc
« Droit de douane » quand le droit vaut zéro**. Vérifié page par page :

    01.01.2111.00  cheval de pur-sang, droit 5 %   → bloc présent
    10.01.1100.00  blé dur de semence,  droit 0 %  → AUCUN bloc
    27.10.1224.00  pétrole lampant,     droit 0 %  → AUCUN bloc

Le socle en tirait 299 droits « indisponibles ». Sur `2710122400`, il refusait
donc de liquider une position que le tarif laisse en franchise — alors que la
fiche officielle publie `D.D 0.00 | PRCT 2.00 | T.C.S 3.00 | T.V.A 19.00`.

CE QUE CES TESTS TIENNENT.

1. LE ZÉRO EST UNE DONNÉE, PAS UNE ABSENCE. 296 droits à 0 % là où il n'y en
   avait aucun sur 17 226. Un tarif national sans une seule ligne en franchise
   n'existe pas : ce compte est le garde-fou de tout le lot.

2. LA LACUNE QUI SUBSISTE RESTE UNE LACUNE. Trois positions du chapitre 98 —
   régimes particuliers, marchandises d'exposition et de démonstration — ne
   portent aucun droit **même à la DGD**. Elles ne sont pas comblées. Sans ce
   test, la tentation de « finir le travail » en posant 0 sur ces trois-là
   serait la prochaine régression.

3. LE RELEVÉ FAIT FOI. Chaque droit versé est adossé à sa fiche officielle,
   archivée dans `data/dza/releve_dd_dgd.json` avec son URL. Le crawl et
   l'archive doivent dire la même chose : une divergence signalerait une
   écriture faite ailleurs que par le relevé.
"""

from __future__ import annotations

import json
import pathlib

import pytest

RACINE = pathlib.Path(__file__).resolve().parents[2]
SOCLE = RACINE / "backend" / "socle" / "DZA.json"
CRAWL = RACINE / "backend" / "data" / "crawled" / "DZA_tariffs.json"
RELEVE = RACINE / "data" / "dza" / "releve_dd_dgd.json"

# Chapitre 98 : régimes douaniers particuliers. La DGD n'y publie pas de droit.
SANS_DROIT_A_LA_SOURCE = {"9800000000", "9810100000", "9810200000"}


@pytest.fixture(scope="module")
def positions():
    if not SOCLE.exists():
        pytest.skip("socle non construit : python3 scripts/build_socle.py")
    return json.loads(SOCLE.read_text(encoding="utf-8"))["positions"]


def _droit(position, code="DD"):
    for d in position.get("droits") or []:
        if d.get("code") == code:
            return d
    return None


def test_le_tarif_algerien_porte_des_droits_a_zero(positions):
    """Le compte qui tient tout le lot : il valait ZÉRO avant.

    Verrouillé sur 296 — le nombre de fiches où la DGD publie effectivement un
    droit — et non sur « au moins un » : une reprise partielle doit tomber.
    """
    a_zero = sum(
        1
        for p in positions.values()
        if isinstance(p, dict) and (_droit(p) or {}).get("taux") == 0.0
    )
    assert a_zero == 296


def test_le_kerosene_se_liquide_au_lieu_d_etre_refuse(positions):
    """La position par laquelle le défaut a été découvert.

    Fiche DGD : D.D 0.00 | PRCT 2.00 | T.C.S 3.00 | T.V.A 19.00.
    """
    from services.calcul import calculer

    p = positions["2710122400"]
    assert {d["code"]: d["taux"] for d in p["droits"]} == {
        "DD": 0.0,
        "TCS": 3.0,
        "TVA": 19.0,
        "PRCT": 2.0,
    }
    npf = calculer(p, valeur_cif=10000.0)["npf"]
    assert npf["etat"] == "COMPLET"
    assert npf["manques"] == []
    assert {l["code"]: l["montant"] for l in npf["lignes"]} == {
        "DD": 0.0,
        "TCS": 300.0,
        "TVA": 1900.0,
        "PRCT": 244.0,
    }


def test_les_positions_sans_droit_a_la_source_le_restent(positions):
    """Contrôle négatif : ce qui n'est pas publié n'est pas inventé."""
    for code in SANS_DROIT_A_LA_SOURCE:
        p = positions.get(code)
        if p is None:
            continue
        droit = _droit(p)
        assert droit is not None, f"{code} : la ligne DD doit exister, déclarée indisponible"
        assert droit["taux"] is None, f"{code} : un droit non publié ne se pose pas à 0"


def test_chaque_droit_verse_est_adosse_a_sa_fiche_officielle():
    """Le crawl et l'archive du relevé disent la même chose, code par code."""
    if not CRAWL.exists() or not RELEVE.exists():
        pytest.skip("crawl ou relevé absent")
    crawl = json.loads(CRAWL.read_text(encoding="utf-8"))
    releve = json.loads(RELEVE.read_text(encoding="utf-8"))["droits"]
    par_code = {x["hs_code"]: x for x in crawl["sub_positions"]}

    assert len(releve) == 296
    for code, fiche in releve.items():
        dd = (par_code[code].get("taxes") or {}).get("DD")
        assert dd is not None, f"{code} : droit relevé mais absent du crawl"
        assert dd["rate"] == fiche["rate"]
        assert dd["label_verification"] == "PUBLISHED_BY_DGD"
        assert fiche["source_url"], f"{code} : un taux sans son URL de fiche"
