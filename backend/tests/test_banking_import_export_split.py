"""
Tests de la division import / export des formalités de change du module
banque (`backend/banking_system`).

La division est dérivée automatiquement de `DomiciliationRule` /
`ForexRegulation` (mêmes données sources, restructurées par sens de flux) :
aucune nouvelle donnée chiffrée n'est introduite. Seul le délai de
rapatriement (`repatriation_deadline_days`) est attribué à l'exportation ;
`transfer_deadline_days` (importation) reste `None` faute de source.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from banking_system import (
    get_export_formalities,
    get_forex_profile,
    get_import_formalities,
)
from banking_system.models import ExportFormalities, ImportFormalities


def test_profile_exposes_import_and_export_formalities():
    profile = get_forex_profile("MA")
    assert isinstance(profile.import_formalities, ImportFormalities)
    assert isinstance(profile.export_formalities, ExportFormalities)


def test_import_formalities_has_no_fabricated_transfer_deadline():
    # Aucune source ne fournit de délai de transfert distinct à l'importation.
    for code in (
        "MA",
        "DZ",
        "TN",
        "EG",
        "NG",
        "GH",
        "CI",
        "SN",
        "KE",
        "ET",
        "TZ",
        "ZA",
        "AO",
        "ZM",
    ):
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
    # Règlement BA n° 26-02, art. 2 : 120 jours en règle générale ; 180 jours
    # uniquement avec une assurance-crédit export nationale préalable.
    assert profile.export_formalities.repatriation_deadline_days == 120
    assert profile.export_formalities.conditional_repatriation_deadline_days == 180
    assert "assurance-crédit" in (profile.export_formalities.conditional_repatriation_condition)
    # Côté importation : domiciliation systématique dès le premier dinar.
    assert profile.import_formalities.domiciliation_threshold_usd == 0


def test_algeria_export_formalities_are_explicit_authentic():
    """L'Algérie fournit des formalités EXPORT explicites (régimes de
    domiciliation distincts par produit), non dérivées du bloc importation."""
    export = get_export_formalities("DZ")
    assert export.domiciliation_required is True
    assert export.domiciliation_conditional is True
    # Pas de seuil USD : le seuil officiel (100 000 DZD) est décrit en clair.
    assert export.domiciliation_threshold_usd is None
    assert "100 000 DZD" in export.repatriation_formalities
    assert "07-2021" in export.legal_reference
    assert "2016-04" in export.legal_reference
    assert "26-02" in export.legal_reference
    assert "120 jours" in export.repatriation_formalities
    assert "180 jours uniquement" in export.repatriation_formalities
    # Documents propres à l'exportation (et non au titre d'importation).
    assert "declaration_exportation" in export.mandatory_documents
    assert "titre_importation" not in export.mandatory_documents


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
