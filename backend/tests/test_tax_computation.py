"""
Tests du moteur de calcul des droits et taxes (ventilation NPF vs ZLECAf).

Vérifie le point critique : chaque taxe est calculée sur SA base déclarée
(assiette propre au pays), et non via une cascade uniforme. Couvre les méthodes
CEDEAO, CEMAC, EAC et la méthode nationale par défaut (base absente).
"""

import pytest
from services.tax_computation import (
    build_journal,
    classify,
    compute_dual_breakdown,
    localize_breakdown,
    parse_cap,
)


def test_parse_cap():
    assert parse_cap("CIF (plafond 15 000 XAF)") == {"amount": 15000.0, "currency": "XAF"}
    assert parse_cap("CIF") is None
    assert parse_cap(None) is None


def test_specific_cap_applied():
    """RI CEMAC 0,45% plafonné à 15 000 XAF : écrêté quand l'ad valorem dépasse."""
    lines = [
        {"code": "DD", "name": "Droit de Douane", "rate_pct": 30.0, "base": "CIF"},
        {
            "code": "RI",
            "name": "Redevance Informatique",
            "rate_pct": 0.45,
            "base": "CIF (plafond 15 000 XAF)",
        },
    ]
    # 1 USD = 600 XAF -> plafond = 25 USD ; ad valorem = 0.45% de 100000 = 450
    capped = compute_dual_breakdown(100_000, lines, 30.0, 0.0, caps={"RI": 25.0})
    ri = next(b for b in capped["breakdown"] if b["code"] == "RI")
    assert ri["amount_npf"] == 25.0
    assert ri["cap"] == {"amount": 15000.0, "currency": "XAF"}
    assert ri["capped_npf"] is True
    # sans plafond fourni (taux indisponible) -> ad valorem complet
    uncapped = compute_dual_breakdown(100_000, lines, 30.0, 0.0)
    ri2 = next(b for b in uncapped["breakdown"] if b["code"] == "RI")
    assert ri2["amount_npf"] == 450.0


def test_cap_not_applied_when_below_ceiling():
    """Petite valeur : l'ad valorem reste sous le plafond, pas d'écrêtage."""
    lines = [{"code": "RI", "name": "RI", "rate_pct": 0.45, "base": "CIF (plafond 15 000 XAF)"}]
    r = compute_dual_breakdown(1_000, lines, 0.0, 0.0, caps={"RI": 25.0})
    ri = next(b for b in r["breakdown"] if b["code"] == "RI")
    assert ri["amount_npf"] == 4.5  # 0.45% de 1000, sous le plafond
    assert ri["capped_npf"] is False


_LEGAL = {
    "cif": {"ref": "CIF", "url": None},
    "zlecaf": {"ref": "ZLECAf", "url": None},
    "vat": {"ref": "CGI", "url": None},
    "rs": {"ref": "RS", "url": None},
    "pcs": {"ref": "PCS", "url": None},
    "cedeao": {"ref": "CEDEAO", "url": None},
    "dd": {"ref": "DD", "url": None},
    "tci": {"ref": "TCI", "url": None},
}


def test_classify():
    assert classify({"code": "DD", "name": "Droit de Douane"}) == "dd"
    assert classify({"code": "DI", "name": "Droit d'Importation"}) == "dd"
    assert classify({"code": "GENERAL", "name": "General Customs Duty"}) == "dd"
    assert classify({"code": "TVA", "name": "Taxe Valeur Ajoutée"}) == "tva"
    assert classify({"code": "VAT", "name": "Value Added Tax"}) == "tva"
    assert classify({"code": "PCS", "name": "Prélèvement Communautaire"}) == "autre"


# --- CEDEAO : TVA sur CIF+DD+RS+PCS (PCC et PUA EXCLUS de la base TVA) ---


def _ben_lines():
    return [
        {"code": "DD", "name": "Droit de Douane (TEC CEDEAO)", "rate_pct": 10.0, "base": "CIF"},
        {"code": "RS", "name": "Redevance Statistique", "rate_pct": 1.0, "base": "CIF"},
        {"code": "PCS", "name": "PCS UEMOA", "rate_pct": 1.0, "base": "CIF"},
        {"code": "PCC", "name": "Prélèvement CEDEAO", "rate_pct": 0.5, "base": "CIF"},
        {"code": "PUA", "name": "Prélèvement UA", "rate_pct": 0.2, "base": "CIF"},
        {"code": "TVA", "name": "TVA", "rate_pct": 18.0, "base": "CIF + DD + RS + PCS"},
    ]


def test_cedeao_vat_base_excludes_pcc_pua():
    r = compute_dual_breakdown(100_000, _ben_lines(), 10.0, 0.0)
    tva = next(b for b in r["breakdown"] if b["code"] == "TVA")
    # base = CIF(100000) + DD(10000) + RS(1000) + PCS(1000) = 112000, PAS 112700
    assert tva["base_value_npf"] == 112_000.0
    assert tva["amount_npf"] == pytest.approx(112_000 * 0.18, abs=0.01)


def test_dd_reduced_under_zlecaf_and_vat_base_follows():
    r = compute_dual_breakdown(100_000, _ben_lines(), 10.0, 0.0)
    dd = next(b for b in r["breakdown"] if b["code"] == "DD")
    tva = next(b for b in r["breakdown"] if b["code"] == "TVA")
    # DD : taux réduit, montant -> 0 sous ZLECAf
    assert dd["rate_npf_pct"] == 10.0 and dd["rate_zlecaf_pct"] == 0.0
    assert dd["amount_npf"] == 10_000.0 and dd["amount_zlecaf"] == 0.0
    assert dd["affected_by_zlecaf"] is True
    # base TVA suit la baisse du DD : 112000 -> 102000
    assert tva["base_value_zlecaf"] == 102_000.0


def test_internal_taxes_rate_unchanged_not_zeroed():
    r = compute_dual_breakdown(100_000, _ben_lines(), 10.0, 0.0)
    for code in ("RS", "PCS", "PCC", "PUA"):
        line = next(b for b in r["breakdown"] if b["code"] == code)
        assert line["rate_npf_pct"] == line["rate_zlecaf_pct"]  # taux inchangé
        assert line["amount_zlecaf"] > 0  # pas mis à zéro
        assert line["affected_by_zlecaf"] is False


def test_tva_rate_identical_both_regimes():
    r = compute_dual_breakdown(100_000, _ben_lines(), 10.0, 0.0)
    tva = next(b for b in r["breakdown"] if b["code"] == "TVA")
    assert tva["rate_npf_pct"] == tva["rate_zlecaf_pct"] == 18.0


def test_all_taxes_integrated():
    lines = _ben_lines()
    r = compute_dual_breakdown(100_000, lines, 10.0, 0.0)
    assert len(r["breakdown"]) == len(lines)  # aucune taxe omise


# --- CEMAC : TVA sur CIF+DD+TCI (RI exclu) ---


def test_cemac_vat_base_excludes_ri():
    lines = [
        {"code": "DD", "name": "Droit de Douane (TEC CEMAC)", "rate_pct": 30.0, "base": "CIF"},
        {"code": "TCI", "name": "Taxe Communautaire", "rate_pct": 1.0, "base": "CIF"},
        {
            "code": "RI",
            "name": "Redevance Informatique",
            "rate_pct": 0.45,
            "base": "CIF (plafond 15 000 XAF)",
        },
        {"code": "TVA", "name": "TVA", "rate_pct": 19.25, "base": "CIF + DD + TCI"},
    ]
    r = compute_dual_breakdown(100_000, lines, 30.0, 0.0)
    tva = next(b for b in r["breakdown"] if b["code"] == "TVA")
    assert tva["base_value_npf"] == 131_000.0  # 100000+30000+1000 (RI exclu)
    assert tva["base_value_zlecaf"] == 101_000.0


# --- Méthode nationale par défaut quand la base est absente (DZA/MAR/EGY) ---


def test_default_method_vat_on_cif_plus_dd():
    lines = [
        {"code": "DD", "name": "Droit de Douane", "rate_pct": 5.0},
        {"code": "TVA", "name": "TVA", "rate_pct": 14.0},
    ]
    r = compute_dual_breakdown(100_000, lines, 5.0, 0.0)
    tva = next(b for b in r["breakdown"] if b["code"] == "TVA")
    assert tva["base_value_npf"] == 105_000.0  # CIF + DD
    assert tva["base_value_zlecaf"] == 100_000.0  # DD=0 sous ZLECAf


def test_journal_reconciles_with_totals():
    """Le cumul final du journal doit égaler le coût total de chaque régime
    (cohérence montants agrégés <-> détail <-> journal)."""
    r = compute_dual_breakdown(100_000, _ben_lines(), 10.0, 0.0)
    for regime in ("npf", "zlecaf"):
        journal = build_journal(100_000, r["breakdown"], regime, _LEGAL)
        assert journal[0]["component"] == "Valeur CIF"
        assert journal[-1]["cumulative"] == pytest.approx(
            r["summary"][regime]["cout_total"], abs=0.01
        )
        # total taxes = somme des montants des étapes (hors CIF)
        somme = sum(s["amount"] for s in journal[1:])
        assert somme == pytest.approx(r["summary"][regime]["total_taxes_et_droits"], abs=0.01)


def test_journal_uses_real_declared_base_for_vat():
    """La base TVA du journal reflète l'assiette déclarée (CIF+DD+RS+PCS), pas
    le cumul de toutes les taxes précédentes."""
    r = compute_dual_breakdown(100_000, _ben_lines(), 10.0, 0.0)
    journal = build_journal(100_000, r["breakdown"], "npf", _LEGAL)
    tva_step = next(s for s in journal if s["component"].upper().startswith("TVA"))
    assert tva_step["base"] == 112_000.0  # CIF+DD+RS+PCS (PCC/PUA exclus)


def test_localize_breakdown_dual_currency():
    """Les montants sont convertis en monnaie locale (1 USD = rate) ; les taux
    en % restent inchangés."""
    d = compute_dual_breakdown(1_000, _ben_lines(), 10.0, 0.0)
    loc = localize_breakdown(d, 600.0)  # 1 USD = 600 XOF
    dd = next(b for b in loc["breakdown"] if b["code"] == "DD")
    assert dd["amount_npf_local"] == round(dd["amount_npf"] * 600, 2)
    assert dd["rate_npf_pct"] == 10.0  # taux inchangé
    assert loc["summary_local"]["npf"]["cout_total"] == round(
        d["summary"]["npf"]["cout_total"] * 600, 2
    )
    assert loc["summary_local"]["economie_totale"] == round(
        d["summary"]["economie_totale"] * 600, 2
    )


def test_currency_mapping_and_offline_rate():
    """Le mapping pays->devise marche hors-ligne ; le taux est None sans réseau
    (le calculateur dégrade alors proprement en USD)."""
    from currencies.service import get_by_country
    from exchange_rates import get_service

    assert get_by_country("CI").currency_code == "XOF"
    assert get_by_country("CM").currency_code == "XAF"
    # Hors réseau, get_rate renvoie None (pas d'exception) -> dégradation USD.
    assert get_service().get_rate("USD", "XOF") is None


def test_summary_savings():
    r = compute_dual_breakdown(100_000, _ben_lines(), 10.0, 0.0)
    s = r["summary"]
    assert s["economie_droits"] == 10_000.0
    # économie totale = baisse DD + baisse TVA (base moindre)
    assert s["economie_totale"] == pytest.approx(11_800.0, abs=0.01)
    assert s["npf"]["cout_total"] > s["zlecaf"]["cout_total"]
