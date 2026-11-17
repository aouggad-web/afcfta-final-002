"""Registre des assureurs du module Finance (remarque de l'exploitant du
16/11/2026, vérification du 17/11/2026).

Le module présente des assureurs qu'un exportateur ou un importateur peut
contacter, jamais des réassureurs. Chaque entrée porte son rôle, qui peut
souscrire, ses contacts officiels et la page d'où ils viennent ; aucune
notation ni capacité sans source.
"""

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from banking_system.insurance_registry import (  # noqa: E402
    MAJOR_INSURERS,
    get_country_insurance_profile,
)

ROLES = {"eca", "assureur_credit", "multilateral", "assureur_general"}


def test_aucun_reassureur_ni_entree_retiree():
    assert set(MAJOR_INSURERS) == {
        "CAGEX", "SMAEX", "COTUNACE", "ATIDI", "ICIEC", "COFACE", "ATRADIUS"
    }
    for ins in MAJOR_INSURERS.values():
        assert not any("réassur" in t.lower() or "reinsur" in t.lower() for t in ins.insurance_type)
        assert "SARA" not in ins.name and "UK Export" not in ins.name


def test_chaque_assureur_a_role_souscription_source_et_site_https():
    for cle, ins in MAJOR_INSURERS.items():
        assert ins.role in ROLES, cle
        assert ins.souscription in {"pays", "etats_membres", "ouvert"}, cle
        if ins.souscription == "pays":
            assert ins.souscripteurs, cle
        assert ins.source and ins.source.startswith("https://"), cle
        assert ins.website and ins.website.startswith("https://"), cle


def test_aucune_valeur_sans_source():
    for cle, ins in MAJOR_INSURERS.items():
        assert ins.credit_rating is None, cle
        assert ins.total_capacity_usd_bn is None, cle


def test_contacts_bien_formes():
    for cle, ins in MAJOR_INSURERS.items():
        if ins.email:
            assert re.fullmatch(r"[^@\s]+@[^@\s]+\.[a-z]{2,}", ins.email), cle
        if ins.phone:
            assert re.fullmatch(r"\+\d[\d ]+", ins.phone), cle


def test_les_agences_nationales_sont_reservees_a_leur_pays():
    attendu = {"CAGEX": ["DZ"], "SMAEX": ["MA"], "COTUNACE": ["TN"]}
    for cle, pays in attendu.items():
        ins = MAJOR_INSURERS[cle]
        assert (ins.role, ins.souscription, ins.souscripteurs) == ("eca", "pays", pays)


def test_le_profil_d_un_pays_acheteur_liste_les_assureurs_a_contacter():
    profil = get_country_insurance_profile("SN")

    noms = {ins.abbreviation for ins in profil.available_insurers}
    assert {"CAGEX", "ATIDI", "ICIEC", "COFACE"} <= noms


def test_les_recommandations_proposent_d_abord_les_assureurs_ouverts_a_tous():
    """Revue Codex du 17/11/2026 : les recommandations prenaient les trois
    premiers du registre, toujours CAGEX, SMAEX et COTUNACE, réservées aux
    entreprises algériennes, marocaines et tunisiennes, sans le dire."""
    from banking_system.banking_recommendations import get_trade_recommendations

    for pays in ("SN", "KE", "DZ"):
        assureurs = get_trade_recommendations(pays, 200_000)["recommended_insurance"][
            "recommended_insurers"
        ]

        sigles = [a["abbreviation"] for a in assureurs]
        assert sigles[:2] == ["COFACE", "ATRADIUS"], pays
        assert sigles[2:4] == ["ATIDI", "ICIEC"], pays
        assert set(sigles[4:]) == {"CAGEX", "SMAEX", "COTUNACE"}, pays
        for a in assureurs:
            assert a["souscription"] in {"ouvert", "etats_membres", "pays"}
            assert a["website"].startswith("https://")
            assert "rating" not in a and "capacity_usd_bn" not in a
        cagex = next(a for a in assureurs if a["abbreviation"] == "CAGEX")
        assert cagex["souscripteurs"] == ["DZ"]
