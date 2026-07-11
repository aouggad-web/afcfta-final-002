"""
Tests du garde-fou d'intégrité de l'ETL World Bank (update_data_automated.py).

Contexte : la run automatique #131 a supprimé l'indicateur GDP_per_capita pour
52 pays à cause d'un 400 transitoire de l'API Banque Mondiale — l'ETL
reconstruisait le fichier avec les seuls indicateurs récupérés puis l'écrasait.
Toute valeur (pays × indicateur × année) non collectée cette run doit être
restaurée depuis le fichier précédent ; les valeurs fraîches l'emportent
toujours (on ne comble que les trous, jamais d'écrasement).

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
                    "GDP": {"2024": 260_000_000_000.0, "2023": 240_000_000_000.0},
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
    # Run où GDP a été re-récupéré mais PAS GDP_per_capita (fetch 400).
    country_data = {
        "DZA": {
            "name": "Algeria",
            "latest_update": "2026-07-11T00:00:00",
            "indicators": {"GDP": {"2024": 261_000_000_000.0, "2023": 240_000_000_000.0}},
        },
        "AGO": {
            "name": "Angola",
            "latest_update": "2026-07-11T00:00:00",
            "indicators": {"GDP": {"2024": 103_000_000_000.0}},
        },
    }
    countries, series = updater._preserve_previous_values(out, country_data)

    assert countries == 2
    assert series == 2  # GDP_per_capita restauré pour DZA et AGO
    assert country_data["DZA"]["indicators"]["GDP_per_capita"] == {"2024": 5722.0, "2023": 5410.0}
    assert country_data["AGO"]["indicators"]["GDP_per_capita"] == {"2024": 2665.87}
    # GDP fraîchement récupéré NON écrasé
    assert country_data["DZA"]["indicators"]["GDP"]["2024"] == 261_000_000_000.0


def test_fresh_value_is_never_overwritten(tmp_path):
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
    updater._preserve_previous_values(out, country_data)
    # La valeur fraîche 2024 gagne ; seule l'année manquante 2023 est comblée.
    assert country_data["DZA"]["indicators"]["GDP_per_capita"]["2024"] == 9999.0
    assert country_data["DZA"]["indicators"]["GDP_per_capita"]["2023"] == 5410.0


def test_null_only_page_is_treated_as_missing(tmp_path):
    # Cas Codex #1 : l'API renvoie une page non vide mais 100 % null -> la boucle
    # d'ingestion n'écrit rien -> l'indicateur est ABSENT de country_data ->
    # il doit être restauré (aucune dépendance à un drapeau « récupéré »).
    out = tmp_path / "worldbank_data_latest.json"
    _write_existing(out)

    updater = DataUpdater(verbose=False)
    country_data = {
        "DZA": {
            "name": "Algeria",
            "latest_update": "2026-07-11T00:00:00",
            # GDP_per_capita n'a produit aucune valeur (page tout-null)
            "indicators": {"GDP": {"2024": 261_000_000_000.0, "2023": 240_000_000_000.0}},
        }
    }
    _, series = updater._preserve_previous_values(out, country_data)
    assert series >= 1
    assert country_data["DZA"]["indicators"]["GDP_per_capita"] == {"2024": 5722.0, "2023": 5410.0}


def test_country_omitted_from_fetched_indicator_keeps_all_series(tmp_path):
    # Cas Codex #2 : GDP récupéré pour DZA mais AGO omis cette run. AGO doit être
    # réintroduit avec TOUTES ses séries précédentes (GDP inclus), pas seulement
    # les indicateurs ayant échoué.
    out = tmp_path / "worldbank_data_latest.json"
    _write_existing(out)

    updater = DataUpdater(verbose=False)
    country_data = {
        "DZA": {
            "name": "Algeria",
            "latest_update": "2026-07-11T00:00:00",
            "indicators": {"GDP": {"2024": 261_000_000_000.0}},
        }
        # AGO totalement absent de la run
    }
    updater._preserve_previous_values(out, country_data)
    assert "AGO" in country_data
    assert country_data["AGO"]["indicators"]["GDP"] == {"2024": 100_000_000_000.0}
    assert country_data["AGO"]["indicators"]["GDP_per_capita"] == {"2024": 2665.87}


def test_missing_years_are_backfilled(tmp_path):
    # Un indicateur présent mais amputé d'années antérieures : les années
    # manquantes sont comblées depuis le fichier précédent (série pluriannuelle
    # préservée), l'année fraîche restant intacte.
    out = tmp_path / "worldbank_data_latest.json"
    _write_existing(out)

    updater = DataUpdater(verbose=False)
    country_data = {
        "DZA": {
            "name": "Algeria",
            "latest_update": "2026-07-11T00:00:00",
            "indicators": {"GDP": {"2024": 261_000_000_000.0}},  # 2023 manquant
        }
    }
    updater._preserve_previous_values(out, country_data)
    assert country_data["DZA"]["indicators"]["GDP"]["2024"] == 261_000_000_000.0  # frais
    assert country_data["DZA"]["indicators"]["GDP"]["2023"] == 240_000_000_000.0  # comblé


def test_clean_full_run_is_noop(tmp_path):
    # Run complète : toutes les valeurs sont fraîches -> rien à restaurer.
    out = tmp_path / "worldbank_data_latest.json"
    _write_existing(out)

    updater = DataUpdater(verbose=False)
    country_data = {
        "DZA": {
            "name": "Algeria",
            "latest_update": "x",
            "indicators": {
                "GDP": {"2024": 1.0, "2023": 2.0},
                "GDP_per_capita": {"2024": 3.0, "2023": 4.0},
            },
        },
        "AGO": {
            "name": "Angola",
            "latest_update": "x",
            "indicators": {"GDP": {"2024": 5.0}, "GDP_per_capita": {"2024": 6.0}},
        },
    }
    countries, series = updater._preserve_previous_values(out, country_data)
    assert (countries, series) == (0, 0)


def test_missing_existing_file_is_safe(tmp_path):
    out = tmp_path / "does_not_exist.json"
    updater = DataUpdater(verbose=False)
    country_data = {"DZA": {"name": "Algeria", "indicators": {"GDP": {"2024": 1.0}}}}
    countries, series = updater._preserve_previous_values(out, country_data)
    assert (countries, series) == (0, 0)
    assert country_data["DZA"]["indicators"] == {"GDP": {"2024": 1.0}}


def test_corrupt_existing_file_is_safe(tmp_path):
    out = tmp_path / "worldbank_data_latest.json"
    out.write_text("{ this is not valid json", encoding="utf-8")
    updater = DataUpdater(verbose=False)
    country_data = {"DZA": {"name": "Algeria", "indicators": {"GDP": {"2024": 1.0}}}}
    countries, series = updater._preserve_previous_values(out, country_data)
    assert (countries, series) == (0, 0)
