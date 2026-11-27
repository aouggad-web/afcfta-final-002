"""
Intervenants locaux relevés sur des sources publiques
(backend/data/intervenants_sources_publiques.json).

Chaque fiche ou bureau ajouté doit dire d'où viennent ses coordonnées :
URL de la page lue, type de source, niveau de vérification et origine
(« source_publique » ou, plus tard, « partenaire »). Les anciens contacts
d'armateurs non sourcés, remplacés après vérification, ne doivent pas revenir.
"""

import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from logistics_operators_data import (  # noqa: E402
    _FICHIER_SOURCES,
    LOGISTICS_OPERATORS,
    get_operators_by_country,
)

DOC = json.loads(_FICHIER_SOURCES.read_text(encoding="utf-8"))
ENTREES = DOC["agences_armateurs"] + DOC["operateurs"]


def test_chaque_entree_porte_sa_provenance():
    for e in ENTREES:
        assert e["source_url"].startswith(("http://", "https://")), e
        assert e["origine"] in DOC["origine"], e
        assert e["verification"] in DOC["verification"], e
        assert e["source_type"] in ("officielle", "annuaire"), e


def test_chaque_entree_a_au_moins_une_coordonnee():
    for e in ENTREES:
        assert any(e.get(k) for k in ("phone", "email", "website", "address")), e


def test_les_agences_locales_completent_les_fiches_armateurs():
    msc = next(o for o in LOGISTICS_OPERATORS["armateurs"] if o["id"] == "msc")
    bureau = msc["contacts"]["Algérie — Oran"]
    assert bureau["origine"] == "source_publique" and bureau["source"].startswith("https://")
    assert "DZA" in msc["africa_presence"]


def test_nouvelles_categories_par_pays():
    categories = {o["category"] for o in get_operators_by_country("MAR")}
    assert {"armateurs", "consignataires", "chargeurs"} <= categories
    for cat in (
        "consignataires",
        "chargeurs",
        "affreteurs",
        "organisations_routieres",
        "assistance_fret_aerien",
        "agents_fret_aerien",
    ):
        assert LOGISTICS_OPERATORS[cat], cat
        assert all(o.get("provenance", {}).get("source") for o in LOGISTICS_OPERATORS[cat])


def test_les_contacts_armateurs_non_sources_remplaces_ne_reviennent_pas():
    # Valeurs d'avant la vérification de novembre 2026, démenties ou introuvables.
    texte = json.dumps(LOGISTICS_OPERATORS["armateurs"], ensure_ascii=False)
    for ancien in ("algiers@msc.com", "durban@msc.com", "maesen@maersk.com", "18 Rue Didouche Mourad"):
        assert ancien not in texte


def _valeurs(obj):
    if isinstance(obj, dict):
        for v in obj.values():
            yield from _valeurs(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from _valeurs(v)
    elif isinstance(obj, str):
        yield obj


def test_les_contacts_routiers_et_aeriens_dementis_ne_reviennent_pas():
    valeurs = set(_valeurs(LOGISTICS_OPERATORS))
    for ancien in (
        "cargo.los@ethiopianairlines.com",
        "ramcargo@royalairmaroc.com",
        "cargo@airalgerie.dz",
        "+234 803 726 8535",
        "+225 27 20 21 5000",
    ):
        assert ancien not in valeurs


def test_les_intervenants_routiers_et_aeriens_par_pays():
    categories = {o["category"] for o in get_operators_by_country("DZA")}
    assert {"air_cargo", "assistance_fret_aerien", "trucking_companies"} <= categories


def test_lot_2_pays_enclaves_et_portuaires():
    # Novembre 2026 : 23 pays de plus (13 portuaires, 10 enclavés).
    for iso in ("TGO", "BEN", "DJI", "TZA", "MLI", "BFA", "NER", "TCD", "ETH", "ZMB"):
        assert get_operators_by_country(iso), iso
    chargeurs = {o["country_iso"] for o in LOGISTICS_OPERATORS["chargeurs"]}
    assert {"BFA", "NER"} <= chargeurs


def test_lot_2_contacts_dementis_retires():
    valeurs = set(_valeurs(LOGISTICS_OPERATORS))
    for ancien in (
        "berbera@dpworld.com",
        "port-louis@pilship.com",
        "dar@ictsi.com",
        "maeeth@maersk.com",
        "djibouti@cmacgm.com",
        "info.djibouti@aglgroup.com",
    ):
        assert ancien not in valeurs


def test_un_seul_courriel_par_champ():
    for e in ENTREES:
        if e.get("email"):
            assert e["email"].count("@") == 1, e
