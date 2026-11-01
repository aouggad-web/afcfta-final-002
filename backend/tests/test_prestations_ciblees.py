"""Formalités, prestataires et frais ciblés : seuls ceux qui visent la position
calculée et le sens de l'échange sont rendus. Le certificat d'un véhicule
d'occasion ne s'affiche pas pour du blé ; une mesure d'importation du Kenya ne
s'affiche pas sur une exportation depuis le Kenya."""

import pytest

from services.regulatory_fee_service import build_regulatory_blocks, dans_perimetre_sh, vise_le_sens

BLE = "10019910"
VOITURE = "87032310"


def _noms(blocs):
    items = (blocs["regulatory_cost"] or {}).get("line_items") or []
    return {(i["side"], i["measure_name"], i.get("actor_name")) for i in items}


def _mesures(blocs):
    return {m["record_id"] for m in (blocs["regulatory_compliance"] or {}).get("measures") or []}


@pytest.mark.parametrize(
    "perimetre, code, attendu",
    [
        (None, BLE, True),
        ({"include": ["8703"]}, BLE, False),
        ({"include": ["8703"]}, VOITURE, True),
        ({"exclude": ["10"]}, BLE, False),
        ({"exclude": ["10"]}, VOITURE, True),
        ({"include": ["8703"]}, None, True),  # position inconnue : rien n'est masqué
        ({"include": ["8703"]}, "8703.23.10", True),
    ],
)
def test_perimetre_sh(perimetre, code, attendu):
    assert dans_perimetre_sh({"hs_scope": perimetre} if perimetre else {}, code) is attendu


def test_sens_par_defaut_importation():
    assert vise_le_sens({}, "import") and not vise_le_sens({}, "export")
    assert vise_le_sens({"sides": ["import", "export"]}, "export")


def test_kenya_le_prestataire_des_vehicules_ne_vise_pas_le_ble():
    acteur = (
        "import",
        "Pre-Export Verification of Conformity (PVoC)",
        "Quality Inspection Services Inc. (QISJ)",
    )
    assert acteur not in _noms(build_regulatory_blocks("KEN", None, cif_value=1000, code=BLE))
    assert acteur in _noms(build_regulatory_blocks("KEN", None, cif_value=1000, code=VOITURE))
    # La formalité, elle, reste due pour le blé, sans prestataire confirmé (revue Codex de #748).
    items = build_regulatory_blocks("KEN", None, cif_value=1000, code=BLE)["regulatory_cost"]["line_items"]
    formalite = next(
        i for i in items if i["measure_name"] == "Pre-Export Verification of Conformity (PVoC)" and i["scope"] == "formality"
    )
    assert formalite["provider_status"] == "UNCONFIRMED"
    pvoc = next(
        m
        for m in build_regulatory_blocks("KEN", None, cif_value=1000, code=BLE)["regulatory_compliance"]["measures"]
        if m["record_id"] == "KEN-KEBS-PVOC"
    )
    assert pvoc["mandated_actors"] == []


def test_cameroun_civic_pour_les_seuls_vehicules():
    assert "CMR-CIVIC-VEHICLES" not in _mesures(build_regulatory_blocks("CMR", None, cif_value=1000, code="10019000"))
    assert "CMR-CIVIC-VEHICLES" in _mesures(build_regulatory_blocks("CMR", None, cif_value=1000, code=VOITURE))


def test_nigeria_soncap_hors_aliments_nafdac_pour_les_aliments():
    ble = build_regulatory_blocks("NGA", None, cif_value=1000, code=BLE)
    voiture = build_regulatory_blocks("NGA", None, cif_value=1000, code=VOITURE)
    assert _mesures(ble) == {"NGA-NAFDAC-CRIA"}
    assert _mesures(voiture) == {"NGA-SON-SONCAP"}
    assert not any("SONCAP" in nom for _, nom, _ in _noms(ble))


def test_ghana_easypass_et_maroc_voc_hors_agroalimentaire():
    assert "GHA-GSA-EASYPASS" not in _mesures(build_regulatory_blocks("GHA", None, cif_value=1000, code=BLE))
    assert "GHA-GSA-EASYPASS" in _mesures(build_regulatory_blocks("GHA", None, cif_value=1000, code=VOITURE))
    assert not _noms(build_regulatory_blocks("MAR", None, cif_value=1000, code=BLE))
    assert _noms(build_regulatory_blocks("MAR", None, cif_value=1000, code=VOITURE))


def test_une_mesure_d_importation_du_pays_d_origine_n_est_pas_une_formalite_d_exportation():
    """Exportation du Kenya vers l'Afrique du Sud : le PVoC kenyan (importation) n'apparaît pas."""
    blocs = build_regulatory_blocks("ZAF", "KEN", cif_value=1000, code=VOITURE)
    assert not any(side == "export" and "PVoC" in nom for side, nom, _ in _noms(blocs))


def test_un_guichet_unique_vaut_aussi_a_l_exportation():
    blocs = build_regulatory_blocks("ZAF", "COD", cif_value=1000, code=BLE)
    assert any(side == "export" for side, _, _ in _noms(blocs))


def test_sans_position_rien_n_est_masque():
    assert "CMR-CIVIC-VEHICLES" in _mesures(build_regulatory_blocks("CMR", None, cif_value=1000))


def test_indications_secondaires_selon_le_sens():
    """Le suivi du fret en transit au Kenya (importation) ne s'affiche pas sur une
    exportation depuis le Kenya ; le guichet unique ivoirien, si."""
    kenya = build_regulatory_blocks("ZAF", "KEN", cif_value=1000, code=BLE)["regulatory_reported"]
    assert not any(i["side"] == "export" for i in (kenya or {}).get("items") or [])
    civ = build_regulatory_blocks("ZAF", "CIV", cif_value=1000, code=BLE)["regulatory_reported"]
    assert [i["program"] for i in civ["items"] if i["side"] == "export"] == ["GUCE (Guichet Unique du Commerce Extérieur)"]
