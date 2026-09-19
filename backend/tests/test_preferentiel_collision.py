"""Deux colonnes ne peuvent pas se réclamer d'un même régime en silence.

`prefs` est un dictionnaire indexé par régime : une seconde colonne rangée sous
le même régime écrasait la première SANS RIEN DIRE, et le taux servi était celui
de la dernière colonne lue.

Le tarif malawien en donne le cas réel. Son Customs and Excise (Tariffs) Order
publie DEUX colonnes SADC, et sa propre loi les distingue :

    col. 8  « SADC rates of customs duty for imports from other Member States
              other than South Africa »
    col. 9  « SADC rates of customs duty for imports from South Africa only »

Les ranger toutes deux sous « SADC » ferait disparaître cette distinction, et le
taux servi serait juste pour une moitié des origines et faux pour l'autre.

Ce garde distingue les deux cas, parce qu'ils n'ont pas le même statut :
  — deux colonnes au MÊME taux sont un doublon sans effet : on garde ce qu'on a ;
  — deux colonnes QUI DIVERGENT sont une ambiguïté : aucune n'est retenue, le
    moteur ne sert alors AUCUNE préférence, et la collision est comptée.

C'est la règle appliquée partout ailleurs ici — refuser plutôt que retenir celle
qui arrange — étendue à un cas qui y échappait.
"""

import json
import pathlib
import sys
import tempfile

import pytest

RACINE = pathlib.Path(__file__).resolve().parents[2]
SCRIPTS = RACINE / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))


def _socle_avec_deux_colonnes(code_regime, taux_a, taux_b):
    import build_socle

    donnees = {
        "country": "TST",
        "source": "jeu d'essai du garde de collision",
        "calculation_rules": {"bases": {"DD": {"basis": "CIF", "type": "ad_valorem"}}},
        "sub_positions": [
            {
                "national_code": "01011000",
                "hs6": "010110",
                "chapter": "01",
                "designation": {"en": "essai", "fr": "", "verbatim": "essai"},
                "taxes": [
                    {"code": "DD", "rate_pct": 15.0, "base": "CIF", "source": "essai"},
                    {"code": code_regime, "name": "hors Afrique du Sud",
                     "rate_pct": taux_a, "source": "essai"},
                    {"code": code_regime, "name": "Afrique du Sud seulement",
                     "rate_pct": taux_b, "source": "essai"},
                ],
                "preferential_rates": [],
                "restrictions": [],
            }
        ],
    }
    dossier = pathlib.Path(tempfile.mkdtemp())
    fichier = dossier / "TST_tariffs.json"
    fichier.write_text(json.dumps(donnees, ensure_ascii=False), encoding="utf-8")
    socle, compteurs = build_socle.construire_pays("TST", str(fichier), "essai", {})
    return socle["positions"]["01011000"], compteurs


def test_un_doublon_au_meme_taux_passe_sans_bruit():
    """Deux colonnes identiques ne coûtent rien : la préférence est servie."""
    position, compteurs = _socle_avec_deux_colonnes("SADC", 0.0, 0.0)
    assert compteurs.get("preferentiels_collision", 0) == 0
    assert position["preferentiels"]["SADC"]["taux"] == 0.0


def test_deux_colonnes_divergentes_ne_servent_aucune_preference():
    """Le cas malawien : « hors Afrique du Sud » et « Afrique du Sud seulement »
    ne portent pas le même taux. Aucune n'est retenue."""
    position, compteurs = _socle_avec_deux_colonnes("SADC", 0.0, 7.5)
    assert compteurs["preferentiels_collision"] == 1
    prefs = position["preferentiels"]["SADC"]
    assert prefs["taux"] is None, "un taux tiré au sort est servi"
    assert prefs["motif"] == "DEUX_COLONNES_POUR_UN_MEME_REGIME"


def test_le_dernier_lu_ne_gagne_plus():
    """Contrôle de non-régression du défaut lui-même : avant ce garde, le taux
    servi était celui de la DERNIÈRE colonne lue — ici 7,5 %."""
    position, _ = _socle_avec_deux_colonnes("SADC", 0.0, 7.5)
    assert position["preferentiels"]["SADC"]["taux"] != 7.5


@pytest.mark.parametrize("regime", ["AFCFTA", "ZLECAF", "COMESA"])
def test_le_garde_vaut_pour_tous_les_regimes(regime):
    """Le défaut n'était pas propre à la SADC : il tenait à la structure."""
    position, compteurs = _socle_avec_deux_colonnes(regime, 0.0, 12.0)
    assert compteurs["preferentiels_collision"] == 1
    canon = "AFCFTA" if regime in ("AFCFTA", "ZLECAF") else regime
    assert position["preferentiels"][canon]["taux"] is None
