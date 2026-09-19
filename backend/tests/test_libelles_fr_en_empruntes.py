"""Un libellé traduit est EMPRUNTÉ à un tarif officiel, jamais produit ici.

Plusieurs tarifs ne publient leur désignation que dans une langue — le portugais
au Mozambique, l'arabe en Égypte — et l'Égypte comme l'Angola servaient leurs
positions SANS AUCUN libellé. L'opérateur doit pouvoir reconnaître la
marchandise ; mais traduire nous-mêmes un libellé tarifaire produirait un texte
qui a l'air officiel sans l'être.

Le socle emprunte donc les libellés que d'AUTRES tarifs nationaux publient dans
ces langues — le tarif extérieur commun de l'EAC pour l'anglais, celui de la
CEDEAO pour le français — et chaque libellé porte le pays dont il vient.

Ces tests tiennent les trois limites de ce procédé : l'original n'est jamais
remplacé, l'emprunt se déclare comme tel, et il ne descend pas sous le SH6.
"""

import json
import pathlib
import sys

import pytest

RACINE = pathlib.Path(__file__).resolve().parents[1]
if str(RACINE) not in sys.path:
    sys.path.insert(0, str(RACINE))

TABLE = RACINE / "data" / "hs6_designations_fr_en.json"
SOCLE = RACINE / "socle"
#: Les pays que l'utilisateur a nommés, un par un.
PAYS = ("MOZ", "EGY", "AGO")

pytestmark = pytest.mark.skipif(
    not TABLE.exists() or not (SOCLE / "MOZ.json").exists(),
    reason="socle non construit dans cet environnement",
)


@pytest.fixture(scope="module")
def table():
    return json.loads(TABLE.read_text(encoding="utf-8"))


def _designation(position):
    x = position.get("designation")
    return x if isinstance(x, dict) else {}


@pytest.fixture(scope="module")
def socles():
    return {
        iso: json.loads((SOCLE / f"{iso}.json").read_text(encoding="utf-8"))
        for iso in PAYS
        if (SOCLE / f"{iso}.json").exists()
    }


def test_chaque_libelle_emprunte_nomme_le_tarif_dont_il_vient(table):
    """Sans provenance, un libellé n'est qu'une affirmation."""
    libelles = table["libelles"]
    assert len(libelles) > 5000
    for code, entree in libelles.items():
        for langue in ("fr", "en"):
            if entree.get(langue):
                source = entree.get(f"{langue}_source")
                assert source, f"{code} : libellé {langue} sans provenance"
                assert " — " in source, f"{code} : provenance {source!r} sans tarif nommé"


def test_la_table_ecarte_explicitement_la_source_incoherente(table):
    """hs6_database.json donne « Autres » en français et « Horses » en anglais
    sur la même sous-position : deux libellés contradictoires."""
    assert "hs6_database.json" in table["table_ecartee"]


def test_le_niveau_de_l_emprunt_est_declare(table):
    """Un libellé SH6 décrit le PARENT, pas la subdivision nationale."""
    assert table["niveau"] == "SH6"
    assert "nationale" in table["avertissement"]


@pytest.mark.parametrize("iso", PAYS)
def test_le_libelle_original_n_est_jamais_remplace(socles, iso):
    """C'est la garantie que l'utilisateur a demandée : garder l'original."""
    socle = socles.get(iso)
    if socle is None:
        pytest.skip(f"{iso} absent du socle")
    for code, position in socle["positions"].items():
        d = _designation(position)
        if not d:
            continue
        assert "verbatim" in d, f"{iso}/{code} : le verbatim a disparu"
        empruntees = d.get("langues_empruntees") or []
        for langue in empruntees:
            # Une langue empruntée ne peut l'être que si le tarif ne la
            # publiait pas : sinon c'est un écrasement.
            assert langue not in ("pt", "ar"), (
                f"{iso}/{code} : {langue} ne doit jamais être emprunté"
            )


@pytest.mark.parametrize("iso", PAYS)
def test_les_positions_portent_un_libelle_francais_et_anglais(socles, iso):
    socle = socles.get(iso)
    if socle is None:
        pytest.skip(f"{iso} absent du socle")
    positions = socle["positions"]
    avec = [
        code for code, p in positions.items()
        if _designation(p).get("fr") and _designation(p).get("en")
    ]
    part = len(avec) / len(positions)
    assert part > 0.95, f"{iso} : seulement {100*part:.1f} % avec libellé FR et EN"


@pytest.mark.parametrize("iso", PAYS)
def test_un_emprunt_se_declare_comme_tel(socles, iso):
    """Personne ne doit prendre un libellé SH6 pour celui de la ligne servie."""
    socle = socles.get(iso)
    if socle is None:
        pytest.skip(f"{iso} absent du socle")
    for code, p in socle["positions"].items():
        d = _designation(p)
        if d.get("langues_empruntees"):
            assert d.get("niveau_libelle_emprunte") == "SH6", (
                f"{iso}/{code} : emprunt non déclaré au niveau SH6"
            )
            for langue in d["langues_empruntees"]:
                assert d.get(f"{langue}_source"), (
                    f"{iso}/{code} : {langue} emprunté sans provenance"
                )


def test_le_socle_ne_traduit_que_les_pays_nommes():
    """« travaille pays par pays, ne cherche pas à généraliser » : rien n'est
    enrichi sans figurer dans la liste."""
    source = (RACINE.parent / "scripts" / "build_socle.py").read_text(encoding="utf-8")
    assert "PAYS_LIBELLES_TRADUITS" in source
    debut = source.index("PAYS_LIBELLES_TRADUITS = {")
    bloc = source[debut:source.index("}", debut)]
    for iso in PAYS:
        assert f'"{iso}"' in bloc, f"{iso} absent de la liste nommée"
    # Un pays dont le tarif publie déjà ses libellés n'y figure pas.
    for iso in ("KEN", "MUS", "SEN", "LBY"):
        assert f'"{iso}"' not in bloc, f"{iso} ne doit pas être enrichi"


def test_le_libelle_emprunte_correspond_bien_au_sh6(socles, table):
    """Contrôle sur une position connue, dans les deux langues."""
    moz = socles.get("MOZ")
    if moz is None:
        pytest.skip("MOZ absent")
    d = _designation(moz["positions"]["01012100"])
    assert d["pt"] == "-- REPRODUTORES DE RAÇA PURA"
    assert d["fr"] == table["libelles"]["010121"]["fr"]
    assert d["en"] == table["libelles"]["010121"]["en"]
    assert "reproducteurs de race pure" in d["fr"]
    assert "breeding animals" in d["en"]
