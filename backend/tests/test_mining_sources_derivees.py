"""
Mines et énergie : chaque chiffre vient d'un générateur, jamais d'une saisie.

Les tables minières étaient recopiées à la main et citaient l'USGS, l'EIA,
l'OPEP ou l'AIE sans correspondre à leurs publications : sur 327 valeurs
citées « MCS », 24 concordaient avec les fiches. Elles sont remplacées par
trois générateurs (fiches USGS MCS, fichier INTL de l'EIA, tableau de la WNA)
qui écrivent des fichiers de données marqués « générés ».

Ces tests verrouillent :
- la lecture des tableaux USGS, là où la mise en page piège un lecteur naïf
  (renvois de note, chiffres renvoyés sous un « e », colonnes multiples) ;
- les règles des lecteurs EIA et WNA (ni zéro, ni « NA », ni pays hors Afrique) ;
- que le JSON servi est exactement ce que les générateurs produisent : une
  valeur saisie à la main ne peut plus s'y glisser sans faire tomber ce test.
"""

import json
import os
import sys
from pathlib import Path

_backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for chemin in (_backend_dir, os.path.join(_backend_dir, "scripts")):
    if chemin not in sys.path:
        sys.path.insert(0, chemin)

from build_energy_from_eia import deriver as deriver_eia  # noqa: E402
from build_mining_from_usgs_pdfs import SPECS, combiner, extraire, lire_tableau  # noqa: E402
from build_uranium_from_wna import lire_tableau as lire_wna  # noqa: E402
from etl.mining_extended import build_all  # noqa: E402

JSON_PRODUCTION = Path(_backend_dir).parent / "data" / "json" / "production_africaine.json"


def _ligne(nom, valeurs, positions):
    """Ligne de tableau : nom à gauche, chaque valeur finissant à sa position."""
    out = nom
    for valeur, fin in zip(valeurs, positions):
        out = out.ljust(fin + 1 - len(valeur)) + valeur
    return out


# En-tête à deux années, comme les fiches MCS (« 2023    2024e »).
ENTETE = "World Mine Production and Reserves:\n" + " " * 60 + "2023      2024e"
POS = (63, 73)  # dernier caractère de « 2023 » et de « 2024 »


def test_usgs_les_chiffres_renvoyes_sous_un_e_font_foi():
    texte = "\n".join([
        ENTETE,
        _ligne("Algeria", ["e"], [61]),
        _ligne("", ["2,000", "2,000", "2,200,000"], [63, 73, 110]),
        "  World total (rounded)",
    ])
    _, pays = lire_tableau(texte)
    # La réserve (2 200 000) ne tombe sous aucune année : ignorée.
    assert pays["DZA"] == {0: 2000.0, 1: 2000.0}


def test_usgs_un_renvoi_de_note_ne_devient_pas_une_production():
    # MCS 2025, zirconium : « Kenya    12 », les chiffres à la ligne suivante.
    texte = "\n".join([
        ENTETE,
        _ligne("Kenya", ["12"], [62]),
        _ligne("", ["20", "20", "5"], [64, 73, 110]),
        _ligne("Madagascar11", ["300", "240", "30,000"], [63, 73, 110]),
        "  World total (rounded)",
    ])
    _, pays = lire_tableau(texte)
    assert pays["KEN"] == {0: 20.0, 1: 20.0}
    # Renvoi collé au nom (« Madagascar11 ») : le nom est reconnu, la note ignorée.
    assert pays["MDG"] == {0: 300.0, 1: 240.0}


def test_usgs_une_section_ne_lit_que_ses_lignes():
    # Fiche titane : le même pays figure sous « Ilmenite: » et sous « Rutile: ».
    texte = "\n".join([
        ENTETE,
        "Ilmenite:",
        _ligne("   South Africa11", ["1,260", "1,300"], POS),
        "Rutile:",
        _ligne("   South Africa11", ["100", "110"], POS),
        "  World total (rounded)",
    ])
    spec = SPECS["Titanium (ilmenite)"]
    assert extraire(texte, spec, (2023, 2024)) == {"ZAF": {2023: 1_260_000.0, 2024: 1_300_000.0}}


def test_usgs_la_mesure_choisit_ses_colonnes():
    # Fiche bauxite : alumine (2 colonnes), puis bauxite (2 colonnes).
    entete = "World Alumina Refinery and Bauxite Mine Production:\n" + " " * 50 + (
        "2023     2024e" + " " * 16 + "2023      2024e"
    )
    texte = "\n".join([
        entete,
        _ligne("Guinea", ["273", "300", "123,000", "130,000"], [53, 62, 82, 92]),
        "  World total (rounded)",
    ])
    assert extraire(texte, SPECS["Bauxite"], (2023, 2024)) == {
        "GIN": {2023: 123_000_000.0, 2024: 130_000_000.0}
    }


def test_usgs_une_phrase_qui_cite_des_annees_n_est_pas_un_en_tete():
    # MCS 2026, hélium : la prose du tableau cite « 2024 and 2025 » avant l'en-tête.
    texte = "\n".join([
        "World Production and Reserves:",
        "production of helium-3 was estimated to be 40,000 liters in 2024 and 2025 with most",
        " " * 60 + "2023      2024e",
        _ligne("Algeria", ["e"], [61]),
        _ligne("", ["11", "11"], POS),
        "  World total (rounded)",
    ])
    _, pays = lire_tableau(texte)
    assert pays["DZA"] == {0: 11.0, 1: 11.0}


def test_usgs_une_ligne_de_suite_peut_porter_du_texte_a_droite():
    # MCS 2026, béryllium : la colonne « réserves » est rédigée.
    texte = "\n".join([
        ENTETE,
        _ligne("Nigeria", ["e"], [61]),
        _ligne("", ["40", "40"], POS) + "        probable bertrandite reserves in Utah total about",
        _ligne("Uganda", ["e23", "20"], POS),
        "  World total (rounded)",
    ])
    _, pays = lire_tableau(texte)
    assert pays["NGA"] == {0: 40.0, 1: 40.0}
    # « e23 » : l'estimation collée au nombre.
    assert pays["UGA"] == {0: 23.0, 1: 20.0}


def test_usgs_chaque_valeur_vient_de_la_plus_recente_edition_qui_la_publie():
    lectures = {
        2024: {"BFA": {2022: 58.0, 2023: 60.0}},
        2025: {"BFA": {2023: 57.0, 2024: 60.0}, "GHA": {2023: 126.0, 2024: 130.0}},
        # MCS 2026 range le Burkina Faso dans « Other countries ».
        2026: {"GHA": {2024: 149.0, 2025: 150.0}},
    }
    assert combiner(lectures) == {
        # 2024 du Burkina : seule l'estimation de MCS 2025 le publie.
        "BFA": {2022: (58.0, 2024), 2023: (57.0, 2025), 2024: (60.0, 2025)},
        "GHA": {2023: (126.0, 2025), 2024: (149.0, 2026), 2025: (150.0, 2026)},
    }


def test_eia_ni_zero_ni_na_ni_pays_hors_afrique():
    lignes = [
        json.dumps({"series_id": "INTL.57-1-DZA-TBPD.A", "last_updated": "2026-03-27",
                    "data": [["2024", 1119.6174], ["2023", "NA"], ["2022", 1211.8630]]}),
        json.dumps({"series_id": "INTL.7-1-ZAF-MT.A", "last_updated": "2026-11-19",
                    "data": [["2024", 235966.335], ["2023", 0]]}),
        json.dumps({"series_id": "INTL.7-1-DZA-MT.A", "data": [["2024", 0]]}),
        json.dumps({"series_id": "INTL.57-1-USA-TBPD.A", "data": [["2024", 13200]]}),
    ]
    series, maj = deriver_eia(lignes)
    assert series["Crude oil"]["by_country"] == {"DZA": {2022: 1211.86, 2024: 1119.62}}
    # Charbon : milliers de tonnes -> tonnes.
    assert series["Coal"]["by_country"] == {"ZAF": {2024: 235966335.0}}
    assert maj == "2026-11-19"


def test_wna_lit_le_tableau_par_pays():
    page = """<table><tr><th>Method</th><th>%</th></tr></table>
    <table><tr><th>Country</th><th>2022</th><th>2023</th><th>2024</th></tr>
    <tr><td>Namibia</td><td>5611</td><td>6986</td><td>7,333</td></tr>
    <tr><td>Kazakhstan</td><td>21227</td><td>21112</td><td>23270</td></tr>
    <tr><td>Niger</td><td>2020</td><td>1130</td><td>962</td></tr></table>"""
    par_pays, _ = lire_wna(page)
    assert par_pays == {
        "NAM": {2022: 5611.0, 2023: 6986.0, 2024: 7333.0},
        "NER": {2022: 2020.0, 2023: 1130.0, 2024: 962.0},
    }


def test_le_json_servi_est_exactement_ce_que_produisent_les_generateurs():
    """Une valeur saisie à la main ne peut plus s'y glisser.

    Régénérer : ``python3 backend/scripts/enrich_production_data.py``.
    """
    servi = json.loads(JSON_PRODUCTION.read_text(encoding="utf-8"))["mining_usgs"]
    assert servi == build_all()


def test_chaque_chiffre_cite_une_source_derivee():
    sources = {r["source_institution"] for r in build_all()}
    assert sources == {"USGS", "EIA", "World Nuclear Association"}
    for r in build_all():
        assert "OPEC" not in r["source_dataset"] and "IEA" not in r["source_dataset"], r
        # La mesure de la source est portée jusqu'à l'écran.
        assert " — " in r["usgs_table_name"], r
