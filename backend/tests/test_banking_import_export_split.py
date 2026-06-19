"""
Tests de la division import / export des formalités de change du module
banque (`backend/banking_system`).

La division est dérivée automatiquement de `DomiciliationRule` /
`ForexRegulation` (mêmes données sources, restructurées par sens de flux) :
aucune nouvelle donnée chiffrée n'est introduite. Seul le délai de
rapatriement (`repatriation_deadline_days`) est attribué à l'exportation ;
`transfer_deadline_days` (importation) reste `None` faute de source.
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from banking_system import (
    get_forex_profile,
    get_import_formalities,
    get_export_formalities,
)
from banking_system.models import ImportFormalities, ExportFormalities


def test_profile_exposes_import_and_export_formalities():
    profile = get_forex_profile("MA")
    assert isinstance(profile.import_formalities, ImportFormalities)
    assert isinstance(profile.export_formalities, ExportFormalities)


def test_import_formalities_has_no_fabricated_transfer_deadline():
    # Aucune source ne fournit de délai de transfert distinct à l'importation.
    for code in ("MA", "DZ", "TN", "EG", "NG", "GH", "CI", "SN", "KE", "ET", "TZ", "ZA", "AO", "ZM"):
        formalities = get_import_formalities(code)
        assert formalities.transfer_deadline_days is None


def test_export_formalities_repatriation_deadline_matches_forex_regulation():
    profile = get_forex_profile("MA")
    assert profile.export_formalities.repatriation_deadline_days == 150
    assert (
        profile.export_formalities.repatriation_deadline_days
        == profile.forex_regulation.repatriation_deadline_days
    )


def test_algeria_export_repatriation_deadline():
    profile = get_forex_profile("DZ")
    assert profile.export_formalities.repatriation_deadline_days == 180
    assert profile.import_formalities.domiciliation_threshold_usd == 0


def test_import_export_share_domiciliation_trigger():
    profile = get_forex_profile("NG")
    assert (
        profile.import_formalities.domiciliation_required
        == profile.export_formalities.domiciliation_required
        == profile.domiciliation.required
    )
    assert (
        profile.import_formalities.domiciliation_threshold_usd
        == profile.export_formalities.domiciliation_threshold_usd
        == profile.domiciliation.threshold_usd
    )


def test_unknown_country_falls_back_to_default_profile_split():
    formalities = get_import_formalities("XX")
    assert formalities.transfer_deadline_days is None
    export = get_export_formalities("XX")
    assert export.repatriation_deadline_days == 90
