"""Frais indépendants de la valeur des pays déjà traités (Sénégal, Côte d'Ivoire,
Ghana, Burkina Faso) : affichés dans le bloc réglementaire, à part des droits et
taxes ; chiffrés quand le montant est publié, « montant à confirmer » sinon, et
écartés quand le mode d'acheminement déclaré ne les concerne pas."""

from services.regulatory_fee_service import build_regulatory_blocks, transport_declare


def _lignes(pays, mode=None):
    cout = build_regulatory_blocks(
        pays, None, fob_value=10_000, cif_value=10_000, transport=transport_declare(None, None, mode)
    )["regulatory_cost"]
    return {l["measure_name"]: l for l in cout["line_items"]}


def test_senegal_escorte_et_port_de_dakar_sans_montant():
    lignes = _lignes("SEN")
    for nom in ("Frais d'escorte douanière", "Frais portuaires (Port autonome de Dakar)"):
        assert lignes[nom]["fee_status"] == "FEE_EXISTS_AMOUNT_NOT_AVAILABLE"
    assert "Frais portuaires (Port autonome de Dakar)" not in _lignes("SEN", "ROUTE")


def test_cote_d_ivoire_port_ecarte_par_voie_aerienne():
    port = "Frais portuaires (Port autonome d'Abidjan)"
    assert port in _lignes("CIV") and port not in _lignes("CIV", "AIR")


def test_ghana_formulaire_chiffre_et_port_selon_la_taille_du_conteneur():
    lignes = _lignes("GHA")
    idf = lignes["Import Declaration Form (MOTI)"]
    assert (idf["calculated_amount"], idf["currency"]) == (5.0, "GHS")
    gpha = lignes["Port dues cargo (GPHA, conteneurs pleins)"]
    assert gpha["fee_status"] == "PARTIAL" and "70,07 USD" in gpha["conditions"]


def test_burkina_sylvie_sans_montant():
    sylvie = _lignes("BFA")["Prestations SYLVIE (Système de liaison virtuelle import-export, SOGESY)"]
    assert sylvie["fee_status"] == "FEE_EXISTS_AMOUNT_NOT_AVAILABLE"
