"""
Tests du garde-fou d'intégrité de l'ETL World Bank (update_data_automated.py).

Contexte : la run automatique #131 a supprimé l'indicateur GDP_per_capita pour
52 pays à cause d'un 400 transitoire de l'API Banque Mondiale — l'ETL
reconstruisait le fichier avec les seuls indicateurs récupérés puis l'écrasait.
Un indicateur dont le fetch échoue ne doit JAMAIS effacer ses valeurs réelles
précédentes : on les préserve par fusion (jamais d'écrasement destructif).

Ces tests exercent la fonction pure de préservation, sans requête réseau.
"""

import json
import os
import sys

_backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

from update_data_automated import DataUpdater  # noqa: E402


def _write_existing(path):
    """Fichier World Bank « précédent » avec GDP + GDP_per_capita pour 2 pays."""
    payload = {
        "metadata": {"source": "World Bank API", "indicators": ["GDP", "GDP_per_capita"]},
        "data": {
            "DZA": {
                "name": "Algeria",
                "latest_update": "2026-02-06T00:00:00",
                "indicators": {
                    "GDP": {"2024": 260_000_000_000.0},
                    "GDP_per_capita": {"2024": 5722.0, "2023": 5410.0},
                },
            },
            "AGO": {
                "name": "Angola",
                "latest_update": "2026-02-06T00:00:00",
                "indicators": {
                    "GDP": {"2024": 100_000_000_000.0},
                    "GDP_per_capita": {"2024": 2665.87},
                },
            },
        },
    }
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_failed_indicator_values_are_preserved(tmp_path):
    out = tmp_path / "worldbank_data_latest.json"
    _write_existing(out)

    updater = DataUpdater(verbose=False)
    # Simule une run où GDP a été re-récupéré mais PAS GDP_per_capita (fetch 400).
    country_data = {
        "DZA": {
            "name": "Algeria",
            "latest_update": "2026-07-11T00:00:00",
            "indicators": {"GDP": {"2024": 261_000_000_000.0}},
        },
        "AGO": {
            "name": "Angola",
            "latest_update": "2026-07-11T00:00:00",
            "indicators": {"GDP": {"2024": 103_000_000_000.0}},
        },
    }
    touched = updater._preserve_unfetched_indicators(out, country_data, fetched_indicators={"GDP"})

    assert touched == 2
    # GDP_per_capita réel restauré à l'identique pour les deux pays
    assert country_data["DZA"]["indicators"]["GDP_per_capita"] == {"2024": 5722.0, "2023": 5410.0}
    assert country_data["AGO"]["indicators"]["GDP_per_capita"] == {"2024": 2665.87}
    # GDP fraîchement récupéré NON écrasé par l'ancienne valeur
    assert country_data["DZA"]["indicators"]["GDP"]["2024"] == 261_000_000_000.0


def test_fetched_indicator_is_never_overwritten(tmp_path):
    out = tmp_path / "worldbank_data_latest.json"
    _write_existing(out)

    updater = DataUpdater(verbose=False)
    country_data = {
        "DZA": {
            "name": "Algeria",
            "latest_update": "2026-07-11T00:00:00",
            "indicators": {"GDP_per_capita": {"2024": 9999.0}},  # nouvelle valeur
        }
    }
    # GDP_per_capita a bien été récupéré cette run -> l'ancienne valeur ne doit
    # pas revenir écraser la nouvelle.
    updater._preserve_unfetched_indicators(
        out, country_data, fetched_indicators={"GDP", "GDP_per_capita"}
    )
    assert country_data["DZA"]["indicators"]["GDP_per_capita"] == {"2024": 9999.0}


def test_country_absent_this_run_is_restored(tmp_path):
    out = tmp_path / "worldbank_data_latest.json"
    _write_existing(out)

    updater = DataUpdater(verbose=False)
    # AGO totalement absent de la run courante -> ses indicateurs non récupérés
    # doivent être réintroduits (aucune perte de pays).
    country_data = {
        "DZA": {"name": "Algeria", "latest_update": "x", "indicators": {"GDP": {"2024": 1.0}}}
    }
    updater._preserve_unfetched_indicators(out, country_data, fetched_indicators={"GDP"})
    assert "AGO" in country_data
    assert country_data["AGO"]["indicators"]["GDP_per_capita"] == {"2024": 2665.87}


def test_missing_existing_file_is_safe(tmp_path):
    out = tmp_path / "does_not_exist.json"
    updater = DataUpdater(verbose=False)
    country_data = {"DZA": {"name": "Algeria", "indicators": {"GDP": {"2024": 1.0}}}}
    touched = updater._preserve_unfetched_indicators(out, country_data, fetched_indicators={"GDP"})
    assert touched == 0
    assert country_data["DZA"]["indicators"] == {"GDP": {"2024": 1.0}}


def test_corrupt_existing_file_is_safe(tmp_path):
    out = tmp_path / "worldbank_data_latest.json"
    out.write_text("{ this is not valid json", encoding="utf-8")
    updater = DataUpdater(verbose=False)
    country_data = {"DZA": {"name": "Algeria", "indicators": {"GDP": {"2024": 1.0}}}}
    # Ne doit pas lever : un fichier corrompu = repli sur {} (aucune restauration).
    touched = updater._preserve_unfetched_indicators(out, country_data, fetched_indicators={"GDP"})
    assert touched == 0
