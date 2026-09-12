"""Le récupérateur d'artefacts doit vérifier avant de publier, et tout vérifier.

Deux défauts trouvés en audit sont couverts ici, parce qu'une régression sur
l'un ou l'autre serait silencieuse : dans les deux cas le script continue
d'afficher un rapport rassurant.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import pathlib

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
SCRIPT = REPO_ROOT / "scripts" / "fetch_tariff_artifacts.py"
MANIFEST = REPO_ROOT / "backend" / "data" / "source_registry_v2.json"


@pytest.fixture(scope="module")
def fta():
    spec = importlib.util.spec_from_file_location("fetch_tariff_artifacts", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def countries():
    return json.loads(MANIFEST.read_text(encoding="utf-8"))["countries"]


def test_chaque_pays_declare_son_artefact_et_son_empreinte(countries):
    """Y compris les pays hérités : _shared désigne un barème, pas une dispense.

    Les membres d'une union douanière partagent le tarif extérieur commun, pas
    leur fiscalité nationale. Une entrée sans artifact_path ou sans sha256 ne
    peut pas être vérifiée, donc pas être servie de façon établie.
    """
    sans_artefact = sorted(k for k, v in countries.items() if not v.get("artifact_path"))
    sans_empreinte = sorted(
        k for k, v in countries.items() if not v.get("sha256") or v["sha256"] == "pending"
    )
    assert not sans_artefact, f"pays sans artifact_path : {sans_artefact}"
    assert not sans_empreinte, f"pays sans sha256 : {sans_empreinte}"


def test_un_pays_herite_est_reellement_verifie(fta, countries):
    """Un fichier altéré doit être rejeté, et non déclaré conforme sans lecture.

    C'est par ce trou que deux taux de TVA faux sont restés servis sous un
    rapport « 54/54 conformes » : les 27 pays hérités n'étaient jamais ouverts.
    """
    herites = [k for k, v in countries.items() if v.get("_shared")]
    assert herites, "le manifeste ne contient plus d'entrée héritée : test à revoir"
    iso = herites[0]

    faussé = dict(countries, **{iso: dict(countries[iso], sha256="0" * 64)})
    anomalie = fta.process(iso, faussé, verify_only=True)
    assert anomalie is not None, f"{iso} déclaré conforme sans vérification réelle"
    assert "empreinte non conforme" in anomalie


def test_telechargement_divergent_ne_detruit_pas_la_donnee_en_place(
    fta, countries, monkeypatch
):
    """Le refus doit précéder le remplacement, sinon il arrive trop tard.

    Une version antérieure publiait le téléchargement puis vérifiait : le
    fichier valide était déjà détruit quand l'écart était signalé.
    """
    iso = next(k for k, v in countries.items() if v.get("artifact_path"))
    dest = REPO_ROOT / countries[iso]["artifact_path"]
    if not dest.exists():
        pytest.skip(f"artefact {iso} absent de ce checkout")

    class ReponseCorrompue:
        _lu = False

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

        def read(self, taille=-1):
            if self._lu:
                return b""
            self._lu = True
            return b"CONTENU QUI NE CORRESPOND PAS A L EMPREINTE"

    monkeypatch.setattr(
        fta.urllib.request, "urlopen", lambda url, timeout=0: ReponseCorrompue()
    )

    avant = hashlib.sha256(dest.read_bytes()).hexdigest()
    cible = dict(
        countries,
        **{iso: dict(countries[iso], artifact_url="https://exemple.invalide/x.json")},
    )

    anomalie = fta.process(iso, cible, verify_only=False)

    assert anomalie is not None, "un téléchargement divergent doit être refusé"
    assert hashlib.sha256(dest.read_bytes()).hexdigest() == avant, (
        "le fichier valide a été écrasé par un téléchargement non conforme"
    )
    assert not list(dest.parent.glob(f"{dest.name}.part")), "fichier .part résiduel"
