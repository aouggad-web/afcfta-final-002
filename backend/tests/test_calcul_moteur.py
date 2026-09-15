"""
Moteur de liquidation — chantier L2.

Ces tests protègent trois promesses : les cinq primitives d'assiette liquident
ce que la douane liquide, un élément manquant ne devient jamais zéro, et la
préférence ne réduit que les prélèvements qu'un texte lui désigne — le droit de
douane le plus souvent, mais aussi le DAPS algérien, et le périmètre ne se
déduit jamais.
"""

import pytest

from services.calcul import (
    CALCULE,
    COMPLET,
    INDISPONIBLE,
    MANQUE_ASSIETTE,
    MANQUE_CHANGE,
    MANQUE_COMPOSANT,
    MANQUE_QUANTITE,
    MANQUE_TAUX,
    PARTIEL,
    calculer,
)


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


# ── Les cinq primitives ───────────────────────────────────────────────────────
def test_cif():
    r = calculer(position(droit("DD", 20, "CIF", "droit")), 1000)
    assert lignes(r)["DD"]["montant"] == 200.0
    assert r["npf"]["total_droits"] == 200.0
    assert r["npf"]["taux_effectif_pct"] == 20.0


def test_cif_plus_codes_nommes():
    """Algérie : TVA sur CIF + DAPS + DD (art. 21 CTCA)."""
    r = calculer(
        position(
            droit("DAPS", 70, "CIF", "droit"),
            droit("DD", 30, "CIF", "droit"),
            droit("TVA", 19, "CIF+DAPS+DD", "tva"),
        ),
        1000,
    )
    assert lignes(r)["TVA"]["base"] == 2000.0  # 1000 + 700 + 300
    assert lignes(r)["TVA"]["montant"] == 380.0


def test_cif_plus_tous_sauf_tva():
    """Règle d'assiette établie : la valeur augmentée de tous les prélèvements
    d'entrée, la TVA seule exclue. Une énumération se périmerait ; pas elle."""
    r = calculer(
        position(
            droit("DD", 0, "CIF", "droit"),
            droit("IDF", 3.5, "CIF", "redevance"),
            droit("RDL", 2, "CIF", "redevance"),
            droit("TVA", 16, "CIF+TOUS_SAUF_TVA", "tva"),
        ),
        1000,
    )
    assert lignes(r)["TVA"]["base"] == 1055.0
    assert lignes(r)["TVA"]["montant"] == 168.8


def test_un_prelevement_non_classe_entre_dans_l_assiette_de_la_tva():
    """« autre » est liquidé avant la TVA : l'exclure serait une omission
    silencieuse, donc un montant faux qui a l'air juste."""
    r = calculer(
        position(
            droit("DD", 10, "CIF", "droit"),
            droit("XYZ", 5, "CIF", "autre"),
            droit("TVA", 20, "CIF+TOUS_SAUF_TVA", "tva"),
        ),
        1000,
    )
    assert lignes(r)["TVA"]["base"] == 1150.0


def test_somme_sans_la_valeur():
    """Tunisie : la redevance de prestation douanière s'assied sur la somme des
    droits et taxes, pas sur la valeur."""
    r = calculer(
        position(
            droit("DD", 10, "CIF", "droit"),
            droit("RPD", 3, "SOMME(TOUS_SAUF_SOI)", "redevance"),
        ),
        1000,
    )
    assert lignes(r)["RPD"]["base"] == 100.0
    assert lignes(r)["RPD"]["montant"] == 3.0


def test_pourcentage_du_montant_du_droit():
    """CEMAC : les centimes additionnels communaux portent sur le montant du
    droit de douane, pas sur la valeur."""
    r = calculer(
        position(droit("DD", 20, "CIF", "droit"), droit("CAC", 25, "%DD", "communautaire")),
        1000,
    )
    assert lignes(r)["CAC"]["base"] == 200.0
    assert lignes(r)["CAC"]["montant"] == 50.0


def test_droit_specifique_a_la_quantite():
    d = droit(
        "DD",
        None,
        "xQTE",
        "droit",
        specifique={"montant": 0.08, "unite_quantite": "kg", "brut": "8c/kg"},
    )
    r = calculer(position(d), 1000, quantite=500)
    ligne = lignes(r)["DD"]
    assert ligne["montant"] == 40.0
    assert ligne["unite_quantite"] == "kg"


def test_un_droit_en_centimes_n_est_pas_lu_comme_une_unite():
    """« 8c/kg » vaut 0,08 par kg. Le lire « 8 » multiplierait par cent le
    droit de toute la SACU."""
    d = droit("DD", None, "CIF", "droit", specifique="8c/kg")  # forme héritée
    r = calculer(position(d), 1000, quantite=500)
    assert (
        lignes(r)["DD"]["statut"] == MANQUE_TAUX
    ), "un spécifique non décomposé par le socle est refusé, jamais deviné"


def test_un_droit_specifique_ne_se_liquide_jamais_sur_la_valeur():
    """Même si l'assiette héritée dit « CIF » : 8c/kg n'est pas 8 %."""
    d = droit("DD", None, "CIF", "droit", specifique={"montant": 0.08, "brut": "8c/kg"})
    r = calculer(position(d), 1000, quantite=500)
    assert lignes(r)["DD"]["assiette"] == "xQTE"
    assert lignes(r)["DD"]["montant"] == 40.0


def test_le_pourcentage_porte_sur_le_code_que_l_assiette_nomme():
    """« %DD » n'est pas une méthode figée : le code est dans l'assiette."""
    r = calculer(
        position(
            droit("DD", 20, "CIF", "droit"),
            droit("TCI", 10, "CIF", "communautaire"),
            droit("CAC", 50, "%TCI", "communautaire"),
        ),
        1000,
    )
    assert lignes(r)["CAC"]["base"] == 100.0  # le montant du TCI, pas celui du DD
    assert lignes(r)["CAC"]["montant"] == 50.0


def test_un_composant_non_liquide_ampute_l_assiette_au_lieu_de_valoir_zero():
    """Si la TVA s'assied sur CIF+DD+TCI et que le TCI n'a pas pu être liquidé,
    compter le TCI pour zéro rendrait un montant trop faible — et crédible."""
    r = calculer(
        position(
            droit("DD", 10, "CIF", "droit"),
            droit("TCI", None, "CIF", "communautaire"),  # taux indisponible
            droit("TVA", 20, "CIF+DD+TCI", "tva"),
        ),
        1000,
    )
    tva = lignes(r)["TVA"]
    assert tva["statut"] == MANQUE_COMPOSANT
    assert tva["montant"] is None
    assert tva["composants_absents"] == ["TCI"]
    assert r["npf"]["etat"] == PARTIEL


def test_un_composant_absent_de_la_position_est_sans_objet_et_signale():
    """Ghana : l'assiette nomme le prélèvement CEDEAO, que cette position ne
    porte pas. Il ne s'applique pas — mais le résultat le dit."""
    r = calculer(
        position(
            droit("DD", 10, "CIF", "droit"),
            droit("TVA", 15, "CIF+DD+CEDEAO", "tva"),
        ),
        1000,
    )
    tva = lignes(r)["TVA"]
    assert tva["statut"] == CALCULE
    assert tva["base"] == 1100.0
    assert tva["composants_sans_objet"] == ["CEDEAO"]


def test_une_assiette_globale_rejette_un_prelevement_non_liquide():
    """« CIF + tous les droits sauf la TVA » additionne ce qui a été liquidé.
    Si un droit applicable a échoué, l'assiette est amputée : la compter quand
    même rendrait une TVA sur le seul CIF, plus faible et crédible."""
    r = calculer(
        position(
            droit("DD", None, "CIF", "droit"),  # taux indisponible
            droit("TVA", 20, "CIF+TOUS_SAUF_TVA", "tva"),
        ),
        1000,
    )
    tva = lignes(r)["TVA"]
    assert tva["statut"] == MANQUE_COMPOSANT
    assert tva["composants_absents"] == ["DD"]
    assert tva["montant"] is None


def test_une_somme_globale_rejette_aussi_un_prelevement_non_liquide():
    """Tunisie : la redevance s'assied sur la somme des droits et taxes."""
    r = calculer(
        position(
            droit("DD", None, "CIF", "droit"),
            droit("RPD", 3, "SOMME(TOUS_SAUF_SOI)", "redevance"),
        ),
        1000,
    )
    assert lignes(r)["RPD"]["statut"] == MANQUE_COMPOSANT


def test_l_echec_d_une_tva_n_empeche_pas_une_assiette_qui_l_exclut():
    """L'invariant vise les composants de l'assiette, pas tous les échecs."""
    r = calculer(
        position(
            droit("DD", 10, "CIF", "droit"),
            droit("TVA", None, "CIF", "tva"),  # échoue
            droit("PRCT", 2, "CIF+TOUS_SAUF_TVA", "post_tva"),
        ),
        1000,
    )
    assert lignes(r)["PRCT"]["statut"] == CALCULE
    assert lignes(r)["PRCT"]["base"] == 1100.0


# ── Une préférence peut être spécifique ───────────────────────────────────────
def test_un_droit_preferentiel_specifique_est_liquide_a_la_quantite():
    """Afrique du Sud : 181 lignes opposent « 8c/kg » en NPF à « 3,2c/kg » sous
    ZLECAf. N'en garder que le taux perdrait le droit préférentiel."""
    npf = droit(
        "DD",
        None,
        "xQTE",
        "droit",
        specifique={"montant": 0.08, "unite_quantite": "kg", "brut": "8c/kg"},
    )
    r = calculer(
        position(npf),
        1000,
        quantite=500,
        taux_preferentiels={
            "DD": {
                "taux": None,
                "specifique": {"montant": 0.032, "unite_quantite": "kg", "brut": "3,2c/kg"},
            }
        },
    )
    assert lignes(r, "npf")["DD"]["montant"] == 40.0
    ligne = lignes(r, "preference")["DD"]
    assert ligne["montant"] == 16.0
    assert ligne["specifique"] == "3,2c/kg"
    assert ligne["specifique_npf"] == "8c/kg"
    assert r["economie"] == 24.0


def test_une_preference_ad_valorem_sur_un_npf_specifique_change_d_assiette():
    """La substitution précède la résolution de l'assiette : sinon le taux
    préférentiel serait liquidé sur l'assiette du NPF."""
    npf = droit(
        "DD",
        None,
        "xQTE",
        "droit",
        specifique={"montant": 0.08, "unite_quantite": "kg", "brut": "8c/kg"},
    )
    r = calculer(position(npf), 1000, quantite=500, taux_preferentiels={"DD": {"taux": 0.0}})
    assert lignes(r, "preference")["DD"]["montant"] == 0.0


def test_la_forme_simple_reste_acceptee():
    """`{"DD": 0}` doit continuer de valoir `{"DD": {"taux": 0}}`."""
    r = calculer(position(droit("DD", 20, "CIF", "droit")), 1000, taux_preferentiels={"DD": 0})
    assert lignes(r, "preference")["DD"]["montant"] == 0.0


# ── Le modificateur plafond ───────────────────────────────────────────────────
def test_plafond_borne_l_assiette():
    d = droit("TCI", 10, "CIF", "communautaire", plafond={"montant": 500.0, "devise": None})
    r = calculer(position(d), 1000)
    assert lignes(r)["TCI"]["base"] == 500.0
    assert lignes(r)["TCI"]["montant"] == 50.0


def test_un_plafond_en_devise_etrangere_exige_une_conversion():
    d = droit("TCI", 10, "CIF", "communautaire", plafond={"montant": 15000.0, "devise": "XAF"})
    r = calculer(position(d), 1000)
    assert lignes(r)["TCI"]["statut"] == MANQUE_CHANGE
    assert r["npf"]["etat"] == INDISPONIBLE

    r2 = calculer(position(d), 1000, taux_de_change=0.05)
    assert lignes(r2)["TCI"]["base"] == 750.0  # 15 000 XAF × 0,05


# ── Rien n'est fabriqué ───────────────────────────────────────────────────────
def test_un_taux_absent_ne_vaut_pas_zero():
    r = calculer(position(droit("DD", None, "CIF", "droit")), 1000)
    ligne = lignes(r)["DD"]
    assert ligne["statut"] == MANQUE_TAUX
    assert ligne["montant"] is None


def test_une_assiette_absente_ne_vaut_pas_cif():
    r = calculer(position(droit("DD", 20, None, "droit")), 1000)
    assert lignes(r)["DD"]["statut"] == MANQUE_ASSIETTE
    assert lignes(r)["DD"]["montant"] is None


def test_une_quantite_manquante_est_nommee():
    d = droit("DSV", None, "xQTE", "redevance", specifique={"montant": 0.1, "brut": "0.1 dinars"})
    r = calculer(position(d), 1000)
    assert lignes(r)["DSV"]["statut"] == MANQUE_QUANTITE
    assert r["npf"]["manques"] == [{"code": "DSV", "motif": MANQUE_QUANTITE}]


def test_un_total_incomplet_se_declare_partiel():
    r = calculer(
        position(
            droit("DD", 20, "CIF", "droit"),
            droit("EXC", None, "CIF", "accise"),
        ),
        1000,
    )
    assert r["npf"]["etat"] == PARTIEL
    assert r["npf"]["total_droits"] == 200.0
    assert [m["code"] for m in r["npf"]["manques"]] == ["EXC"]


def test_rien_de_calculable_donne_indisponible():
    r = calculer(position(droit("DD", None, None, "droit")), 1000)
    assert r["npf"]["etat"] == INDISPONIBLE
    assert r["npf"]["total_droits"] == 0


def test_tout_calcule_donne_complet():
    r = calculer(position(droit("DD", 20, "CIF", "droit")), 1000)
    assert r["npf"]["etat"] == COMPLET
    assert all(ligne["statut"] == CALCULE for ligne in r["npf"]["lignes"])


def test_une_valeur_negative_est_refusee():
    with pytest.raises(ValueError):
        calculer(position(droit("DD", 20)), -1)


# ── La préférence ne réduit que ce qu'on lui désigne ──────────────────────────
def test_la_preference_ne_touche_que_les_prelevements_designes():
    p = position(
        droit("DD", 20, "CIF", "droit"),
        droit("RS", 1, "CIF", "communautaire"),
        droit("TVA", 18, "CIF+TOUS_SAUF_TVA", "tva"),
    )
    r = calculer(p, 1000, taux_preferentiels={"DD": 0})

    npf, pref = lignes(r, "npf"), lignes(r, "preference")
    assert npf["DD"]["montant"] == 200.0 and pref["DD"]["montant"] == 0.0
    # Les autres prélèvements restent dus — c'est ce que liquide la douane.
    assert pref["RS"]["montant"] == 10.0
    # …et la TVA suit mécaniquement l'assiette réduite, sans être « remisée ».
    assert npf["TVA"]["base"] == 1210.0
    assert pref["TVA"]["base"] == 1010.0
    assert pref["TVA"]["taux_pct"] == 18


def test_le_perimetre_de_la_preference_n_est_jamais_deduit_par_le_moteur():
    """Algérie : sous ZLECAf, le DAPS est exonéré au même titre que le droit de
    douane pour les produits des listes (A) et (B) — circulaire 482/2024,
    partie II-2, citant l'art. 2 de la loi de finances complémentaire 2018.
    Réduire le seul DD surestimerait ici le droit liquidé de 700 sur 1 000."""
    dza = position(
        droit("DAPS", 70, "CIF", "droit"),
        droit("DD", 30, "CIF", "droit"),
        droit("TCS", 3, "CIF", "accise"),
        droit("TVA", 19, "CIF+DAPS+DD", "tva"),
    )
    partiel = calculer(dza, 1000, taux_preferentiels={"DD": 0})
    complet = calculer(dza, 1000, taux_preferentiels={"DD": 0, "DAPS": 0})

    assert lignes(partiel, "preference")["DAPS"]["montant"] == 700.0
    assert lignes(complet, "preference")["DAPS"]["montant"] == 0.0
    # L'exonération du DAPS allège aussi l'assiette de la TVA (CIF+DAPS+DD).
    assert lignes(complet, "preference")["TVA"]["base"] == 1000.0
    assert complet["preference"]["prelevements_remises"] == ["DAPS", "DD"]
    # La taxe de consommation spécifique, elle, reste due dans les deux cas.
    assert lignes(complet, "preference")["TCS"]["montant"] == 30.0


def test_la_preference_conserve_le_taux_npf_pour_comparaison():
    r = calculer(position(droit("DD", 20, "CIF", "droit")), 1000, taux_preferentiels={"DD": 5})
    ligne = lignes(r, "preference")["DD"]
    assert ligne["taux_npf_pct"] == 20
    assert ligne["taux_pct"] == 5
    assert ligne["regime_applique"] == "preference"
    assert r["economie"] == 150.0


def test_sans_preference_autorisee_aucun_regime_preferentiel_n_est_rendu():
    """Le moteur applique un taux ; il ne décide pas du droit à la préférence."""
    r = calculer(position(droit("DD", 20, "CIF", "droit")), 1000)
    assert "preference" not in r
    assert "economie" not in r


# ── La provenance suit le calcul ──────────────────────────────────────────────
def test_les_marqueurs_de_provenance_atteignent_le_resultat():
    d = droit(
        "TVA",
        14,
        "CIF",
        "tva",
        source="PwC Worldwide Tax Summaries",
        note="Taux national standard, non vérifié position par position",
        classification_source="estimation_ia",
    )
    ligne = lignes(calculer(position(d), 1000))["TVA"]
    assert ligne["source"] == "PwC Worldwide Tax Summaries"
    assert ligne["note"].startswith("Taux national standard")
    assert ligne["classification_source"] == "estimation_ia"
