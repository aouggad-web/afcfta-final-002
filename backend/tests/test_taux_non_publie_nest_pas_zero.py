"""Un taux que la source ne chiffre pas n'est pas un taux nul.

`_build_tax_list_from_crawled()` ramenait tout `rate: null` à `0.0`, si bien
qu'une taxe dont le tarif publie un montant que le collecteur n'a pas su
convertir se liquidait comme une EXONÉRATION. Mesuré au 21/09/2026 sur les
crawls versionnés : 58 taxes égyptiennes sont dans ce cas, et aucune n'est
inconnue — ce sont des droits spécifiques, dont la mention est conservée
dans `raw` :

    ID     9 جنية لكل كيلو جرام صافى        9 £E / kg net      tabacs (2401)
    VAT    0.48 جنية لكل لتر                0,48 £E / litre    pétrole (2707)
    VAT_2  بحد ادنى 60 جنية لكل كيلو جرام   min. 60 £E / kg
    ...    15 جنية لكل لتر سائل             15 £E / litre      alcool (2207)

Le produit annonçait donc « 0,00 % » sur les tabacs et les alcools égyptiens.

Ce lot ne convertit PAS ces mentions en taux : le faire supposerait une
quantité et une devise, et la conversion est un travail de collecte, pays par
pays, sur le texte officiel. Il fait cesser le zéro fabriqué, et nomme la
lacune à sa place.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.enhanced_calculator_service import (  # noqa: E402
    _build_tax_list_from_crawled,
    _compute_regime,
)

CIF = 10_000.0


def _ligne(taxes):
    return {"hs_code": "2401100010", "taxes": taxes}


def _regime(taxes, pays="EGY", regime="NPF"):
    return _compute_regime(regime, _ligne(taxes), pays, CIF, CIF, 0.0, 0.0)


def test_un_taux_absent_ne_devient_pas_zero():
    """Le cœur du correctif : `rate: None` ne se lit plus « 0 % »."""
    taxes = _build_tax_list_from_crawled(
        _ligne(
            [
                {"code": "DD", "name": "Droit de douane", "rate": 10.0},
                {"code": "VAT", "name": "TVA", "rate": None},
            ]
        )
    )
    par_code = {t["code"]: t for t in taxes}
    assert par_code["TVA"]["rate"] is None
    assert par_code["TVA"]["rate_pct"] is None
    assert par_code["TVA"]["taux_indisponible"] is True
    # Le taux connu, lui, n'est pas touché.
    assert par_code["DD"]["rate"] == 0.1
    assert par_code["DD"]["taux_indisponible"] is False


def test_la_ligne_sans_taux_est_servie_sans_montant():
    """Elle n'est ni chiffrée ni escamotée.

    La supprimer ferait disparaître une taxe DUE de la ventilation — la même
    faute vue de l'autre côté : l'opérateur lirait un total sans savoir qu'une
    ligne manque.
    """
    bloc = _regime(
        [
            {"code": "DD", "name": "Droit de douane", "rate": 10.0},
            {"code": "VAT", "name": "TVA", "rate": None},
        ]
    )
    par_code = {tl.code: tl for tl in bloc.tax_lines}
    assert "TVA" in par_code, "la ligne sans taux doit rester visible"
    assert par_code["TVA"].amount is None
    assert par_code["TVA"].rate is None
    assert par_code["TVA"].taux_indisponible is True
    assert par_code["TVA"].notes and "non publié" in par_code["TVA"].notes


def test_le_total_dit_qu_il_est_partiel():
    """Un total amputé d'une ligne doit le dire, sinon il passe pour le dû."""
    bloc = _regime(
        [
            {"code": "DD", "name": "Droit de douane", "rate": 10.0},
            {"code": "VAT", "name": "TVA", "rate": None},
        ]
    )
    assert bloc.codes_taux_indisponible == ["TVA"]
    # 10 % de 10 000, et rien pour la TVA — pas 0 compté comme un montant.
    assert bloc.total_taxes == 1_000.0


def test_un_taux_illisible_est_traite_comme_une_absence():
    """Une chaîne non numérique n'est pas zéro non plus : elle est nommée."""
    bloc = _regime([{"code": "DD", "name": "Droit de douane", "rate": "n/a"}])
    assert bloc.codes_taux_indisponible == ["DD"]
    assert bloc.tax_lines[0].amount is None


# ─────────────────────────────────────────────────────────────────────────────
# LES CONTRÔLES NÉGATIFS — ils comptent plus que la correction elle-même.
#
# Le risque de ce lot est de sur-corriger : transformer les VRAIS zéros en
# indisponibilités. Un zéro publié est une exonération, c'est une DONNÉE du
# dépôt, et `test_taux_zero_est_une_donnee.py` l'impose déjà aux 76
# collecteurs. Le calculateur doit respecter la même règle.
# ─────────────────────────────────────────────────────────────────────────────


def test_un_zero_publie_reste_une_exoneration_chiffree():
    """0 n'est pas None : il se sert, nommé, avec son montant à 0."""
    bloc = _regime(
        [
            {"code": "DD", "name": "Droit de douane", "rate": 0.0},
            {"code": "VAT", "name": "TVA", "rate": 14.0},
        ]
    )
    par_code = {tl.code: tl for tl in bloc.tax_lines}
    assert par_code["DD"].rate == 0.0
    assert par_code["DD"].amount == 0.0
    assert par_code["DD"].taux_indisponible is False
    assert bloc.codes_taux_indisponible == [], "un zéro publié n'est pas une lacune"


def test_un_taux_connu_produit_le_meme_montant_qu_avant():
    """Le chemin nominal ne bouge pas : contrôle de non-régression."""
    bloc = _regime(
        [
            {"code": "DD", "name": "Droit de douane", "rate": 10.0},
            {"code": "VAT", "name": "TVA", "rate": 14.0},
        ]
    )
    par_code = {tl.code: tl for tl in bloc.tax_lines}
    assert par_code["DD"].amount == 1_000.0
    # Assiette cumulative : la TVA porte sur CIF + DD. Le code « VAT » du crawl
    # est canonisé en « TVA » — c'est sous ce nom qu'il ressort.
    assert par_code["TVA"].base_value == 11_000.0
    assert par_code["TVA"].amount == 1_540.0
    assert bloc.total_taxes == 2_540.0
    assert bloc.codes_taux_indisponible == []


def test_une_preference_zlecaf_s_applique_malgre_un_plein_droit_absent():
    """Un taux préférentiel REMPLACE le NPF : il est dû même si le NPF manque.

    Refuser de le servir au motif que le plein droit est indisponible ferait
    perdre une préférence acquise — le produit cacherait du vrai.
    """
    ligne = {
        "hs_code": "2401100010",
        "taxes": [{"code": "DD", "name": "Droit de douane", "rate": None}],
        "preferential_rates": [{"regime": "AFCFTA", "rate_pct": 0.0}],
    }
    bloc = _compute_regime("ZLECAf", ligne, "EGY", CIF, CIF, 0.0, 0.0)
    par_code = {tl.code: tl for tl in bloc.tax_lines}
    assert par_code["DD"].rate == 0.0, "la préférence ZLECAf doit s'appliquer"
    assert par_code["DD"].amount == 0.0
    assert bloc.codes_taux_indisponible == []


def test_les_droits_specifiques_egyptiens_ne_sont_plus_servis_a_zero():
    """Le cas réel qui a motivé le lot, avec ses mentions d'origine.

    Ces cinq taxes sont celles du crawl égyptien versionné : des droits
    spécifiques (£E par kg, par litre, par vingt cigarettes) que le collecteur
    n'a pas convertis. Aucune ne doit être liquidée comme une exonération.
    """
    taxes = [
        {"code": "ID", "name": "Import duty", "rate": None, "raw": "9 جنية لكل كيلو جرام صافى"},
        {"code": "VAT", "name": "VAT", "rate": None, "raw": "0.48 جنية لكل لتر"},
    ]
    bloc = _regime(taxes)
    assert set(bloc.codes_taux_indisponible) == {"DD", "TVA"}, (
        "ID est canonisé en DD et VAT en TVA ; les deux doivent remonter "
        "comme indisponibles, non comme exonérés"
    )
    for tl in bloc.tax_lines:
        assert tl.amount is None
        assert tl.rate is None
    assert bloc.total_taxes == 0.0
    # Et le total ne peut pas se lire comme « rien à payer » : la liste des
    # codes indisponibles est non vide, c'est ce qui l'en empêche.
    assert bloc.codes_taux_indisponible


def test_aucune_valeur_de_repli_ne_comble_un_taux_absent():
    """Le contrôle négatif le plus important.

    Le dépôt porte une table `FALLBACK_VAT` de taux nationaux par défaut, et il
    serait tentant de s'en servir ici. Ce serait remplacer une lacune par une
    valeur plausible — la faute que toute la doctrine interdit. La TVA publiée
    mais non chiffrée reste indisponible ; le repli ne sert QUE lorsque le
    tarif ne porte aucune ligne de TVA du tout.
    """
    bloc = _regime([{"code": "VAT", "name": "TVA", "rate": None}], pays="EGY")
    tva = [tl for tl in bloc.tax_lines if tl.code == "TVA"]
    assert len(tva) == 1, "pas de seconde ligne de TVA ajoutée par repli"
    assert tva[0].amount is None
    assert tva[0].rate is None
