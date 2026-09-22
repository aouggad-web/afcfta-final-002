"""
Le passage ETL doit committer la SOURCE avec son PRODUIT.

``production_etl.yml`` régénère ``backend/etl/macro_wdi_data.py`` et
``backend/etl/unsd_manufacturing_data.py`` depuis les API World Bank et UNSD,
puis fabrique ``data/json/production_africaine.json`` en LISANT ces modules.

Il ne committait que le JSON. Les modules restaient donc périmés dans le
dépôt, et un ``enrich_production_data.py`` relancé ensuite hors ligne
réinjectait leurs anciennes valeurs — le rafraîchissement était défait sans
que rien ne le signale. Un produit committé sans sa source finit toujours par
diverger d'elle.

Ce test verrouille l'appariement plutôt que la formulation : il lit le YAML
et vérifie que l'étape qui committe le JSON committe aussi les deux modules
qu'elle vient de régénérer.
"""

import os

import pytest  # noqa: F401
import yaml

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_WORKFLOW = os.path.join(_ROOT, ".github", "workflows", "production_etl.yml")

#: Les modules que le workflow régénère et dont l'enrichissement dépend.
_REGENERATED_MODULES = (
    "backend/etl/macro_wdi_data.py",
    "backend/etl/unsd_manufacturing_data.py",
)
_DATASET = "data/json/production_africaine.json"


def _steps():
    with open(_WORKFLOW, encoding="utf-8") as fh:
        doc = yaml.safe_load(fh)
    job = doc["jobs"][next(iter(doc["jobs"]))]
    return job["steps"]


def test_the_workflow_regenerates_those_modules_in_the_first_place():
    # Sans cette prémisse, le test suivant vérifierait une règle sans objet.
    scripts = "\n".join(s.get("run", "") for s in _steps())
    assert "fetch_wdi_macro.py" in scripts
    assert "fetch_unsd_manufacturing.py" in scripts


def test_the_commit_step_stages_the_sources_with_the_dataset():
    commit_steps = [s for s in _steps() if _DATASET in s.get("run", "") and "git add" in s.get("run", "")]
    assert len(commit_steps) == 1, "une seule étape doit committer le dataset"
    run = commit_steps[0]["run"]
    for module in _REGENERATED_MODULES:
        assert module in run, (
            f"{module} est régénéré par ce workflow mais jamais committé : "
            "le dépôt garderait l'ancienne version, et un enrichissement "
            "hors ligne réinjecterait ses valeurs périmées"
        )


def test_nothing_is_committed_when_the_run_did_not_ask_for_it():
    # Contrôle miroir : élargir ce qui est committé ne doit pas transformer un
    # passage de vérification en écriture sur la branche.
    commit_steps = [s for s in _steps() if "git push" in s.get("run", "")]
    assert commit_steps, "aucune étape de push trouvée"
    for step in commit_steps:
        assert "inputs.commit_data" in str(step.get("if", "")), step.get("name")
