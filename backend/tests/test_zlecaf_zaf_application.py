"""L'Afrique du Sud applique le barème ZLECAf (hors SACU/SADC) — liste datée.

General Note O du Schedule No. 1 (Customs and Excise Act, 1964), telle
qu'amendée par les Notices R. gazettées : liste initiale (R.4287, GG 50045,
effet 31/01/2024), puis R.5879 (21/02/2025 : Maroc, Burundi, Ouganda),
R.6233 (Gambie, effet rétroactif 14/03/2025), R.6595 (Nigeria, effet
rétroactif 30/05/2025), R.6756 (Éthiopie, effet rétroactif 14/08/2025).

Ces tests verrouillent :
(a) les dates d'entrée en vigueur, notice par notice (dates réelles du texte
    primaire — PAS les dates de publication : les avis Gambie/Nigeria/Éthiopie
    portent une clause rétroactive) ;
(b) l'écart signalé : la Sierra Leone est dans la liste dtic mais absente de
    la General Note O — elle ne reçoit pas de préférence ;
(c) SACU : union douanière, jamais la ZLECAf ;
(d) la Tanzanie, absente de la General Note O : NPF ;
(e) le même taux dans les deux chemins pour une origine admise ;
(f) le chemin socle avec la date du jour simulée avant/après l'entrée du
    Nigeria.
"""

import datetime
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services import socle  # noqa: E402
from services.authentic_tariff_service import calculate_import_taxes  # noqa: E402
from services.preference import taux_preferentiels  # noqa: E402
from services.zlecaf_schedule_zaf import DATES_ENTREE_ZAF, zaf_partner_active  # noqa: E402

SOCLE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "socle")

besoin_socle = pytest.mark.skipif(
    not os.path.exists(os.path.join(SOCLE, "ZAF.json")),
    reason="socle absent (gitignoré) : reconstruire avec scripts/build_socle.py",
)

CODE = "72191490"  # la position SARS de référence (NPF 10 %, AfCFTA 2 %)


def test_a_les_dates_des_notices_sont_celles_du_texte_primaire():
    """Les avis Gambie/Nigeria/Éthiopie portent une clause rétroactive : la
    date d'entrée est celle du TEXTE, pas celle de la publication."""
    # R.6233 (Gambie) : effet rétroactif au 14/03/2025 (publiée le 30/05).
    assert zaf_partner_active("GMB", datetime.date(2025, 3, 13)) is False
    assert zaf_partner_active("GMB", datetime.date(2025, 3, 14)) is True
    # R.6595 (Nigeria) : effet rétroactif au 30/05/2025 (publiée le 12/09).
    assert zaf_partner_active("NGA", datetime.date(2025, 5, 29)) is False
    assert zaf_partner_active("NGA", datetime.date(2025, 5, 30)) is True
    # R.6756 (Éthiopie) : effet rétroactif au 14/08/2025 (publiée le 24/10).
    assert zaf_partner_active("ETH", datetime.date(2025, 8, 13)) is False
    assert zaf_partner_active("ETH", datetime.date(2025, 8, 14)) is True
    # R.5879 (Maroc, Burundi, Ouganda) : 21/02/2025.
    assert zaf_partner_active("BDI", datetime.date(2025, 2, 20)) is False
    assert zaf_partner_active("BDI", datetime.date(2025, 2, 21)) is True
    assert zaf_partner_active("MAR", datetime.date(2025, 2, 21)) is True
    # Liste initiale (R.4287) : effet 31/01/2024.
    for iso in ("DZA", "CMR", "EGY", "GHA", "KEN", "RWA", "TUN"):
        assert zaf_partner_active(iso, datetime.date(2024, 1, 31)) is True
        assert zaf_partner_active(iso, datetime.date(2024, 1, 30)) is False


def test_b_la_sierra_leone_est_hors_general_note_o():
    """Écart signalé au rapport : la newsletter dtic (mars 2026) cite la
    Sierra Leone, mais AUCUNE Notice R. ne l'ajoute à la General Note O —
    elle ne reçoit donc pas de préférence."""
    assert "SLE" not in DATES_ENTREE_ZAF
    assert zaf_partner_active("SLE") is False
    assert zaf_partner_active("SLE", datetime.date(2026, 9, 27)) is False


@besoin_socle
def test_c_sacu_est_une_union_douaniere_jamais_la_zlecaf():
    """Namibie et Botswana : libre circulation SACU (0 %), jamais la
    préférence continentale."""
    for iso in ("NAM", "BWA"):
        position, _ = socle.position("ZAF", CODE)
        decision = taux_preferentiels(position, "ZAF", iso, CODE)
        assert decision["regime"] == "UNION_DOUANIERE", iso
        assert decision["taux"]["DD"]["taux"] == 0.0, iso
        assert decision["statut"] != "ZLECAF"


@besoin_socle
def test_d_la_tanzanie_absente_de_la_general_note_o_est_au_npf():
    """La Tanzanie a gazetté son propre PSTC (règle B EAC) mais ne figure
    PAS dans la General Note O sud-africaine : NPF — noté comme tel dans la
    fiche."""
    assert zaf_partner_active("TZA") is False
    position, _ = socle.position("ZAF", CODE)
    decision = taux_preferentiels(position, "ZAF", "TZA", CODE)
    assert decision["applique"] is False
    assert decision["taux"] == {}


@besoin_socle
def test_e_meme_taux_dans_les_deux_chemins_pour_une_origine_admie():
    """Égypte (liste initiale) : le socle et le chemin historique servent le
    même taux de la colonne AfCFTA (2 % contre un NPF de 10 %)."""
    position, _ = socle.position("ZAF", CODE)
    soc = taux_preferentiels(position, "ZAF", "EGY", CODE)
    assert soc["applique"] is True
    assert soc["taux"]["DD"]["taux"] == 2.0

    hist = calculate_import_taxes(
        "ZAF", CODE, 10000, apply_zlecaf=True, origin_country="EGY", fob_value=10000
    )
    assert hist["zlecaf_preference_applied"] is True
    assert hist["rates"]["effective_zlecaf_rate_pct"] == 2.0


@besoin_socle
@pytest.mark.parametrize("jour_str,attendu", [("2025-05-29", False), ("2025-05-30", True)])
def test_f_le_socle_donne_ne_servit_pas_le_nigeria_avant_son_entree(monkeypatch, jour_str, attendu):
    """Date du jour simulée : le socle ne sert le Nigeria qu'à partir du
    30/05/2025 (effet rétroactif de la Notice R.6595)."""
    import services.zlecaf_schedule_zaf as zaf

    annee, mois, jour = (int(x) for x in jour_str.split("-"))

    class JourFixe(datetime.date):
        @classmethod
        def today(cls):
            return cls(annee, mois, jour)

    monkeypatch.setattr(zaf, "date", JourFixe)

    position, _ = socle.position("ZAF", CODE)
    decision = taux_preferentiels(position, "ZAF", "NGA", CODE)
    assert decision["applique"] is attendu
    if attendu:
        assert decision["taux"]["DD"]["taux"] == 2.0
    else:
        assert decision["taux"] == {}


def test_g_la_suspension_r6594_suit_sa_date_et_son_origine():
    """Suspension unilatérale (R.6594, GG 53334, 12/09/2025) : thé 0902.40 du
    Kenya suspendu à partir du 12/09/2025 ; pas avant ; pas pour une autre
    origine ; pas pour une autre ligne."""
    from services.zlecaf_schedule_zaf import zaf_suspension_active

    assert zaf_suspension_active("KEN", "0902.40", datetime.date(2025, 9, 11)) is False
    assert zaf_suspension_active("KEN", "0902.40", datetime.date(2025, 9, 12)) is True
    assert zaf_suspension_active("KEN", "09024000", datetime.date(2026, 9, 27)) is True
    # Le café (0901) n'est pas suspendu.
    assert zaf_suspension_active("KEN", "0901", datetime.date(2026, 9, 27)) is False
    # La suspension ne vise que le Kenya.
    assert zaf_suspension_active("EGY", "0902.40", datetime.date(2026, 9, 27)) is False


@besoin_socle
def test_h_le_the_kenyan_suspends_vers_le_npf_avec_la_notice():
    """Socle : thé 0902.40 du Kenya = NPF avec la note citant R.6594."""
    position, _ = socle.position("ZAF", "09024000")
    decision = taux_preferentiels(position, "ZAF", "KEN", "09024000")
    assert decision["applique"] is False
    assert decision["taux"] == {}
    assert "R.6594" in decision["note"]


def test_h_bis_le_chemin_historique_porte_la_meme_notice_de_suspension():
    """Historique (résolveur de contexte) : même note R.6594, préférence non
    appliquée."""
    from services.authentic_tariff_service import resolve_zlecaf_context

    ctx = resolve_zlecaf_context("ZAF", "KEN", "090240", 10.0, None)
    assert ctx["preference_applied"] is False
    assert "R.6594" in ctx["trade_regime_note"]


@besoin_socle
def test_i_une_ligne_kenyane_non_suspendue_sert_le_taux_afcfta():
    """Contraste : sur une ligne ad valorem non suspendue (72191490), le
    Kenya reçoit bien le taux AfCFTA (2 % contre un NPF de 10 %) — le même
    dans les deux chemins."""
    position, _ = socle.position("ZAF", CODE)
    soc = taux_preferentiels(position, "ZAF", "KEN", CODE)
    assert soc["applique"] is True and soc["taux"]["DD"]["taux"] == 2.0
    hist = calculate_import_taxes(
        "ZAF", CODE, 10000, apply_zlecaf=True, origin_country="KEN", fob_value=10000
    )
    assert hist["rates"]["effective_zlecaf_rate_pct"] == 2.0


@besoin_socle
def test_j_le_cafe_kenyan_sert_son_droit_specifique_afcfta():
    """Le café 0901 porte un droit SPÉCIFIQUE dans la colonne AfCFTA de SARS
    (2,4 c/kg) : servi tel quel (jamais aplati en ad valorem), sans
    suspension."""
    position, _ = socle.position("ZAF", "09012100")
    decision = taux_preferentiels(position, "ZAF", "KEN", "09012100")
    assert decision["applique"] is True
    assert decision["statut"] == "APPLIED"
    dd = decision["taux"]["DD"]
    assert dd["taux"] is None
    assert dd["specifique"]["brut"] == "2,4c/kg"
    assert "R.6594" not in decision["note"]  # pas une suspension : un droit spécifique
