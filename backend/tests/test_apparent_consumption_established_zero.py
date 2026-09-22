"""
Une production nulle ÉTABLIE rend la consommation apparente mesurable.

LE CAS
-------
Le café en Afrique du Nord. L'Algérie n'en produit pas — et ce n'est pas une
lacune documentaire : FAOSTAT (bulk QCL Afrique) couvre TOUS les pays
africains, donc son silence sur le couple Algérie/café prouve une production
nulle. ``domestic_supply()`` le sait déjà et le dit par
``absence_established``.

``_apparent_consumption`` l'ignorait pourtant : elle exigeait les trois jambes
non nulles et rendait ``None`` dès que la production manquait. Le besoin
retombait donc sur le proxy démographique L2 alors qu'un chiffre MESURÉ
existait — pour le café algérien 2024, 86 630 tonnes (importations 86 642 t,
exportations 12 t, relevées sur UN Comtrade).

CE QUE CES TESTS INTERDISENT
-----------------------------
Le glissement inverse, qui serait pire : traiter une production INCONNUE
comme un zéro. Ne pas savoir n'est pas savoir que c'est zéro. Confondre les
deux attribuerait la totalité du besoin à l'importation pour un pays qui
produit peut-être tout ce qu'il consomme.
"""

import os
import sys

_backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

from services import demand_estimation_service as des  # noqa: E402


def test_established_zero_production_yields_a_measured_consumption():
    # Le cas algérien, avec les valeurs relevées sur Comtrade (tonnes).
    apparent = {
        "production": None,
        "production_absence_established": True,
        "imports": 86_642.25,
        "exports": 11.98,
        "unit": "tonnes",
    }
    assert des._apparent_consumption(apparent) == 86_630.27


def test_unknown_production_still_refuses_to_conclude():
    # MÊME forme, sans l'établissement de l'absence. La fonction doit rendre
    # None : c'est le garde-fou qui empêche de compter une ignorance pour zéro.
    apparent = {
        "production": None,
        "imports": 86_642.25,
        "exports": 11.98,
        "unit": "tonnes",
    }
    assert des._apparent_consumption(apparent) is None
    # Et explicitement à False, pas seulement absent.
    apparent["production_absence_established"] = False
    assert des._apparent_consumption(apparent) is None


def test_a_measured_production_is_never_overridden():
    # L'établissement d'une absence ne doit pas écraser une production connue.
    apparent = {
        "production": 1_000.0,
        "production_absence_established": True,
        "imports": 500.0,
        "exports": 100.0,
    }
    assert des._apparent_consumption(apparent) == 1_400.0


def test_the_payload_says_which_zero_it_carries():
    """Un zéro établi et un zéro mesuré ne se lisent pas pareil.

    Sans ce champ, un lecteur du payload ne peut pas distinguer « le pays ne
    produit pas » de « la production vaut zéro d'après la source ».
    """
    need = des.estimate_national_need(
        "0901",
        "DZA",
        apparent={
            "production": None,
            "production_absence_established": True,
            "imports": 86_642.25,
            "exports": 11.98,
            "unit": "tonnes",
            "source": "FAOSTAT (absence établie) + UN Comtrade 2024",
        },
    )
    assert need["available"] is True
    assert need["is_estimation"] is False
    assert need["estimation_level"] == 1
    assert need["value"] == 86_630.27
    assert need["inputs"]["production_absence_established"] is True
    assert need["inputs"]["production"] is None


def test_importable_need_counts_an_established_zero_as_zero_production():
    # Besoin importable = importations − exportations. Avec une production
    # nulle établie, l'auto-approvisionnement vaut 0 et doit être servi comme
    # une mesure, pas laissé vide.
    bloc = des._l1_importable(
        {
            "production": None,
            "production_absence_established": True,
            "imports": 86_642.25,
            "exports": 11.98,
        },
        86_630.27,
    )
    assert bloc["importable_need"] == 86_630.27
    assert bloc["self_sufficiency"]["domestic_production"] == 0.0
    assert bloc["self_sufficiency"]["ratio"] == 0.0
    assert bloc["self_sufficiency"]["covers_need"] is False


def test_faostat_absence_is_established_only_for_agriculture():
    """Le contrôle qui rend tout le reste légitime.

    L'absence n'est établie que si la source qui se tait COUVRE le pays.
    FAOSTAT couvre les 54 ; USGS et UNIDO non. Si ce test tombait, le zéro
    établi deviendrait une déduction, et la correction ci-dessus se
    retournerait en surestimation systématique.
    """
    import inspect

    src = inspect.getsource(des.domestic_supply)
    assert 'dimension == "agri"' in src
