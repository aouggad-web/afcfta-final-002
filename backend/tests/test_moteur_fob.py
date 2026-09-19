"""
Assiette « FOB » — la valeur en douane SACU.

La valeur en douane des pays SACU est la valeur de transaction sur base FOB :
fret et assurance internationaux exclus (Customs and Excise Act 91/1964, s.65-67,
corroboré par la politique SARS SC-CR-A-03 — fiche SACU_assiette_DD_2026-09-17).
Ces tests protègent une seule promesse : la base FOB est fournie par l'appelant
ou le droit reste indisponible — elle ne se déduit JAMAIS de la valeur CIF, dont
l'emploi surestimerait le droit du fret et de l'assurance internationaux.
"""

import pytest

from services.calcul import (
    COMPLET,
    INDISPONIBLE,
    calculer,
)
from services.calcul import MANQUE_FOB as VALEUR_FOB_REQUISE


def position(*droits, **extra):
    base = {"designation": "essai", "droits": list(droits)}
    base.update(extra)
    return base


def droit(code, taux=None, assiette="CIF", famille="autre", **extra):
    d = {"code": code, "libelle": code, "famille": famille, "assiette": assiette}
    if taux is not None:
        d["taux"] = taux
    d.update(extra)
    return d


def lignes(resultat, regime="npf"):
    return {ligne["code"]: ligne for ligne in resultat[regime]["lignes"]}


# ── Le moteur socle ───────────────────────────────────────────────────────────


def test_fob_liquide_sur_la_valeur_fob_pas_sur_le_cif():
    r = calculer(
        position(droit("DD", 20, "FOB", "droit_de_douane")),
        1000,
        valeur_fob=800,
    )
    ligne = lignes(r)["DD"]
    assert ligne["statut"] == "CALCULE"
    assert ligne["assiette"] == "FOB"
    assert ligne["montant"] == 160.0  # 20 % de 800, pas de 1000
    assert r["npf"]["total_droits"] == 160.0
    assert r["npf"]["etat"] == COMPLET


def test_fob_absente_le_droit_est_indisponible_jamais_liquide_sur_cif():
    r = calculer(position(droit("DD", 20, "FOB", "droit_de_douane")), 1000)
    ligne = lignes(r)["DD"]
    assert ligne["statut"] == VALEUR_FOB_REQUISE
    assert ligne["montant"] is None
    # Rien n'a été liquidé : l'état est INDISPONIBLE, pas un total à zéro.
    assert r["npf"]["etat"] == INDISPONIBLE


def test_fob_plus_codes_ajoute_les_droits_nomes_a_la_valeur_fob():
    r = calculer(
        position(
            droit("DD", 20, "FOB", "droit_de_douane"),
            droit("EXC", 10, "FOB+DD", "autre"),
        ),
        1000,
        valeur_fob=800,
    )
    l = lignes(r)
    assert l["DD"]["montant"] == 160.0
    assert l["EXC"]["montant"] == 96.0  # 10 % de (800 + 160)
    assert r["npf"]["total_droits"] == 256.0


def test_la_tva_sur_cif_plus_dd_reste_sur_le_cif_meme_fob_fournie():
    """La TVA sud-africaine s'assoit sur CIF+DD (VAT Act s.13(2)) : fournir la
    valeur FOB change l'assiette du droit, pas celle de la TVA."""
    r = calculer(
        position(
            droit("DD", 20, "FOB", "droit_de_douane"),
            droit("TVA", 15, "CIF+DD", "tva"),
        ),
        1000,
        valeur_fob=800,
    )
    l = lignes(r)
    assert l["DD"]["montant"] == 160.0
    assert l["TVA"]["montant"] == 174.0  # 15 % de (1000 + 160)
    assert r["npf"]["etat"] == COMPLET


def test_une_franchise_a_zero_pour_cent_liquide_sans_valeur_fob():
    """Zéro pour cent vaut zéro sur n'importe quelle assiette : une franchise
    intra-SACU (libre circulation) ne peut pas exiger la valeur FOB — rien
    n'est dû, la base n'influe sur aucun montant."""
    r = calculer(
        position(
            droit("DD", 0, "FOB", "droit_de_douane"),
            droit("TVA", 15, "CIF+DD", "tva"),
        ),
        10000,
    )
    l = lignes(r)
    assert l["DD"]["statut"] == "CALCULE"
    assert l["DD"]["montant"] == 0.0
    assert l["TVA"]["montant"] == 1500.0  # 15 % de (10 000 + 0)
    assert r["npf"]["etat"] == COMPLET


def test_fob_superieure_au_cif_est_refusee():
    with pytest.raises(ValueError):
        calculer(position(droit("DD", 20, "FOB", "droit_de_douane")), 1000, valeur_fob=1100)


def test_le_total_indisponible_n_calcule_pas_une_economie():
    """Sans valeur FOB, une remise NON nulle laisse NPF et préférence
    indisponibles : l'économie n'est pas chiffrée plutôt que soustraite de
    bases inconnues. (Une remise à 0 %, elle, se liquide sans valeur FOB —
    voir test_une_franchise_a_zero_pour_cent_liquide_sans_valeur_fob.)"""
    r = calculer(
        position(droit("DD", 20, "FOB", "droit_de_douane")),
        1000,
        taux_preferentiels={"DD": 5.0},
    )
    assert r["npf"]["etat"] == INDISPONIBLE
    assert r["preference"]["etat"] == INDISPONIBLE
    assert r["economie"] is None


# ── Le moteur historique (cascade codée) ─────────────────────────────────────


def test_zaf_cascade_liquide_le_dd_sur_la_valeur_fob():
    from services.authentic_tariff_service import compute_tax_cascade

    r = compute_tax_cascade(1000.0, {"DD": 20, "TVA": 15}, "ZAF", fob_value=800.0)
    dd = next(s for s in r["steps"] if s["code"] == "DD")
    tva = next(s for s in r["steps"] if s["code"] == "TVA")
    assert dd["base_formula"] == "FOB"
    assert dd["amount"] == 160.0
    assert tva["base_value"] == 1160.0  # CIF + DD, la TVA reste sur CIF+DD


def test_zaf_cascade_refuse_de_liquider_sans_valeur_fob():
    from services.authentic_tariff_service import compute_tax_cascade

    with pytest.raises(ValueError, match="valeur_fob"):
        compute_tax_cascade(1000.0, {"DD": 20, "TVA": 15}, "ZAF")


# ── La table d'assiettes du socle ────────────────────────────────────────────


def test_la_table_d_assiettes_pose_le_dd_sud_africain_sur_fob():
    import json
    import os

    chemin = os.path.join(
        os.path.dirname(__file__), "..", "socle", "assiettes_pays.json"
    )
    with open(chemin, encoding="utf-8") as f:
        table = json.load(f)
    zaf = table["pays"]["ZAF"]["taxes"]["DD"]
    assert zaf["assiette"] == "FOB"
    assert zaf["origine_assiette"] == "texte_primaire"
    assert "FOB" in table["_grammaire"]
