"""Namibie : barème de Namport 2026/2027 (manutention des conteneurs et Base Tariff),
frais vérifiés hors du coût douanier. Source : data/sources/NAM/ports/NAM_Namport_Tariffs_2026-27.extrait-ocr.txt."""

from services.regulatory_fee_service import build_verified_provider_costs, transport_declare


def _par_nom(lignes):
    return {ligne["measure_name"]: ligne for ligne in lignes}


CONTENEURS = "Manutention des conteneurs au terminal (Namport, Base Tariff compris)"
BASE = "Base Tariff sur la marchandise conventionnelle (Namport)"


def test_importation_par_mer_porte_les_deux_frais_partiels():
    lignes = _par_nom(build_verified_provider_costs("NAM", cif_value=1000, side="import"))
    assert {CONTENEURS, BASE} <= set(lignes)
    conteneurs, base = lignes[CONTENEURS], lignes[BASE]
    assert conteneurs["fee_status"] == base["fee_status"] == "PARTIAL"
    assert conteneurs["calculated_amount"] is None and base["calculated_amount"] is None
    assert conteneurs["currency"] == "NAD" and "7 526 NAD (20 pieds)" in conteneurs["conditions"]
    assert "564 NAD" in base["conditions"] and conteneurs["payer"] == "IMPORTER"


def test_un_conteneur_declare_reste_a_chiffrer_faute_de_taille():
    lignes = _par_nom(build_verified_provider_costs(
        "NAM", cif_value=1000, side="import", transport=transport_declare("conteneur", 2, "MER")
    ))
    assert lignes[CONTENEURS]["calculated_amount"] is None


def test_le_poids_ne_chiffre_pas_le_base_tariff_qui_depend_de_la_categorie():
    lignes = _par_nom(build_verified_provider_costs("NAM", cif_value=1000, side="import", poids_brut_kg=2500))
    assert lignes[BASE]["calculated_amount"] is None


def test_importation_par_route_sans_frais_portuaire():
    lignes = _par_nom(build_verified_provider_costs(
        "NAM", cif_value=1000, side="import", transport=transport_declare(None, None, "ROUTE")
    ))
    assert CONTENEURS not in lignes and BASE not in lignes


def test_exportation_depuis_la_namibie():
    lignes = _par_nom(build_verified_provider_costs("NAM", cif_value=1000, side="export"))
    assert lignes[CONTENEURS]["payer"] == "EXPORTER"
    assert "poisson importé" not in lignes[BASE]["conditions"]
