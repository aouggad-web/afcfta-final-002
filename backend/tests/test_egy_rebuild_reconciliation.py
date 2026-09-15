# -*- coding: utf-8 -*-
"""Le rapport de réconciliation égyptien doit nommer sa base et mesurer vraiment.

Le rapport a publié 8 793 « différences de taux » là où il n'y en avait aucune.
La cause n'était pas une erreur de données mais une comparaison sur des clés
mortes : le schéma a porté « DD »/« TVA » avant « ID »/« VAT », et la base était
interrogée sur les premières alors qu'elle ne portait plus que les secondes.
Toute position ayant un taux ressortait donc comme modifiée.

Un compteur qui ne dit pas à quoi il compare ne peut pas être contredit.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "backend" / "scripts"))

from build_egy_tariffs_official import (  # noqa: E402
    rates_by_canonical_code,
    reconcile,
)

REPORT = REPO_ROOT / "reports" / "EGY_REBUILD_RECONCILIATION.json"


@pytest.fixture(scope="module")
def rapport() -> dict:
    # Le rapport est un livrable versionné, pas une commodité. Sauter quand il
    # manque ferait d'une suppression accidentelle une CI plus verte : la
    # régression deviendrait un succès.
    assert REPORT.exists(), (
        f"{REPORT.relative_to(REPO_ROOT)} est un livrable versionné et doit "
        "exister. Le régénérer avec build_egy_tariffs_official.py "
        "--reconcile-only --base <version antérieure>."
    )
    return json.loads(REPORT.read_text(encoding="utf-8"))


def test_les_deux_generations_de_cles_donnent_le_meme_code_canonique():
    ancien = {"taxes": {"DD": {"rate": 5.0}, "TVA": {"rate": 14.0}}}
    courant = {"taxes": {"ID": {"rate": 5.0}, "VAT": {"rate": 14.0}}}
    assert rates_by_canonical_code(ancien) == rates_by_canonical_code(courant)


def test_un_changement_de_vocabulaire_n_est_pas_un_changement_de_taux():
    """Le défaut exact qui produisait 8 793 fausses différences."""
    base = {"sub_positions": [{"hs_code": "0101210000", "taxes": {"DD": {"rate": 5.0}}}]}
    construit = {"sub_positions": [{"hs_code": "0101210000", "taxes": {"ID": {"rate": 5.0}}}]}
    assert reconcile(base, construit)["rates"]["positions_changed"] == 0


def test_un_vrai_changement_de_taux_est_bien_detecte():
    base = {"sub_positions": [{"hs_code": "0101210000", "taxes": {"DD": {"rate": 5.0}}}]}
    construit = {"sub_positions": [{"hs_code": "0101210000", "taxes": {"ID": {"rate": 10.0}}}]}
    resultat = reconcile(base, construit)["rates"]
    assert resultat["positions_changed"] == 1
    assert resultat["sample"][0] == {
        "code": "0101210000",
        "tax": "ID",
        "before": 5.0,
        "after": 10.0,
    }


def test_le_rapport_nomme_et_empreinte_sa_base(rapport):
    base = rapport["comparison_base"]
    assert base.get("origin"), "la base de comparaison doit être qualifiée"
    assert len(base.get("sha256", "")) == 64
    assert base.get("positions")


def test_la_base_est_designee_de_facon_rejouable(rapport):
    """Un chemin temporaire ne prouve rien : personne d'autre ne peut l'ouvrir."""
    ref = rapport["comparison_base"]["ref"]
    assert not ref.startswith("/tmp"), ref
    assert ref.startswith("git:") or (REPO_ROOT / ref).exists(), ref


def test_le_rapport_porte_un_bilan_avant_apres(rapport):
    bilan = rapport["before_after"]
    for bloc in ("positions", "rates", "families", "instruction_texts", "references"):
        assert bloc in bilan, f"bilan incomplet : {bloc} manquant"
    assert bilan["positions"]["before"] == base_count(rapport)


def test_les_invariants_annonces_par_la_reconstruction_sont_vrais(rapport):
    """Vérifier que les blocs existent ne vérifie rien.

    Ce sont leurs VALEURS qui portent la promesse de cette reconstruction :
    aucune position ajoutée ou supprimée, aucun taux modifié, aucun texte
    perdu, aucune référence touchée, la méthode de calcul conservée. Un jeu
    régénéré fautif passait tant que la suite se contentait de la présence
    des sections.
    """
    bilan = rapport["before_after"]

    positions = bilan["positions"]
    assert positions["added"] == [], positions["added"][:10]
    assert positions["removed"] == [], positions["removed"][:10]
    assert positions["before"] == positions["after"]

    rates = bilan["rates"]
    assert rates["positions_changed"] == 0, rates["sample"][:5]
    assert (
        rates["positions_without_any_rate_before"] == rates["positions_without_any_rate_after"]
    ), "le nombre de positions sans aucun taux a changé"

    textes = bilan["instruction_texts"]
    assert textes["raw_instructions"]["lost"] == 0, textes["raw_instructions"]["lost_sample"][:5]
    for famille, mesure in textes["par_famille"].items():
        perdus = mesure["sortis_de_ce_bloc"] - mesure["retrouves_dans_une_autre_famille"]
        assert perdus == 0, (
            f"{famille} : {perdus} textes sortis du bloc et retrouvés dans "
            f"aucun autre — {mesure['sortis_sample'][:3]}"
        )

    assert bilan["references"]["positions_changed"] == 0, bilan["references"]["sample"]
    assert bilan["calculation_method_preserved"] is True

    provenance = bilan["provenance"]
    assert (
        provenance["extracted_at"]["before"] == provenance["extracted_at"]["after"]
    ), "la date de collecte a changé : une reconstruction ne recollecte pas"


def base_count(rapport: dict) -> int:
    return rapport["comparison_base"]["positions"]


def test_le_compteur_trompeur_n_est_plus_publie(rapport):
    assert "rate_diff_vs_previous" not in json.dumps(
        rapport
    ), "ce compteur comparait sur des clés que le document ne porte plus"
