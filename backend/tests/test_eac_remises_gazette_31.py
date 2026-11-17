"""Remises de droits du Kenya de la Gazette EAC Vol. AT 1 No. 31 (12/11/2026),
Legal Notices EAC/388 à EAC/413/2026.

Ces remises sont accordées à des sociétés NOMMÉES, pour des quantités et des produits
finis fixés. Elles ne sont donc jamais une préférence générale : sans autorisation datée qui
nomme la ligne, le droit du TEC et la préférence ZLECAf du couloir restent ceux du tarif.

Les mesures sont lues dans le PDF archivé par scripts/extraire_remises_eac_388_413_2026.py ;
ces tests vérifient les données contre ce PDF, jamais contre un taux figé."""

import importlib.util
import json
import os
from datetime import date

import pytest

from engine.schemas.legal_override import RemissionEligibility
from services import mesures_eac, socle

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
GAZETTE = "Vol. AT 1 No. 31"
DATE_GAZETTE = date(2026, 11, 12)
LE = date(2026, 11, 17)

besoin_socle = pytest.mark.skipif(
    not os.path.exists(socle.MANIFESTE), reason="socle absent : python3 scripts/build_socle.py"
)


def _mesures_gazette():
    with open(mesures_eac.MESURES, encoding="utf-8") as f:
        return [m for m in json.load(f)["measures"] if GAZETTE in (m.get("gazette_number") or "")]


def _script():
    spec = importlib.util.spec_from_file_location(
        "extraire_remises_eac_388_413_2026", os.path.join(REPO, "scripts", "extraire_remises_eac_388_413_2026.py")
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _position(code, taux=25.0):
    return {
        "designation": "test",
        "droits": [
            {"code": "DD", "libelle": "Droit de douane", "famille": "droit", "assiette": "CIF", "taux": taux},
            {"code": "TVA", "famille": "tva", "taux": 16.0, "assiette": "CIF+DD"},
        ],
    }


def _dd(position):
    return next(d for d in position["droits"] if d["code"] == "DD")


def _mesure_de(notice):
    return next(m for m in _mesures_gazette() if m["legal_reference"] == f"Legal Notice EAC/{notice}/2026")


# ── Les données sont celles du PDF ───────────────────────────────────────────


def test_les_mesures_de_la_gazette_ont_la_forme_attendue():
    mesures = _mesures_gazette()

    assert len(mesures) > 200
    assert len({m["measure_id"] for m in mesures}) == len(mesures)
    notices = {int(m["legal_reference"].split("/")[1]) for m in mesures}
    assert notices <= set(range(388, 414)) and len(notices) >= 20
    for m in mesures:
        assert (m["jurisdiction"], m["measure_type"], m["rate_unit"]) == ("KEN", "DUTY_REMISSION", "%")
        assert m["override_rate"] in (0.0, 10.0)
        assert len(m["hs_code_from"]) == 8 and m["hs_code_from"] == m["hs_code_to"]
        assert m["effective_from"] == DATE_GAZETTE.isoformat()
        assert m["effective_to"] in ("2027-06-30", "2027-11-11")
        assert m["named_beneficiary"] and m["finished_product"]
        assert m["allocated_quantity"] is None or m["allocated_quantity"] > 0
        # Une remise nommée n'est jamais une préférence générale : elle exige une autorisation.
        assert m["beneficiary"] in ("MANUFACTURER", "MILLER", "ASSEMBLER")
        assert m["verification_status"] == "VERIFIED_OFFICIAL_EXTRACT" and m["requires_human_review"] is False


@besoin_socle
def test_les_mesures_committees_sont_celles_que_donne_le_pdf_archive():
    """Les données ne dérivent pas du PDF : relire le PDF redonne exactement les mesures du dépôt."""
    pytest.importorskip("pymupdf")
    script = _script()
    notices, lignes, n, resultat, ecartees = script.calculer()

    assert n == 228 and len(lignes) == 228 and len(notices) == 26
    assert len(resultat) + len(ecartees) == 228
    assert resultat == _mesures_gazette()


@besoin_socle
def test_aucune_remise_ne_releve_le_droit_du_tec():
    positions = socle.charger("KEN")["positions"]
    for m in _mesures_gazette():
        dd = next(d for d in positions[m["hs_code_from"]]["droits"] if d["code"] == "DD")
        assert dd["taux"] is not None and m["override_rate"] < dd["taux"], m["measure_id"]


def test_le_pdf_archive_est_celui_que_le_registre_decrit():
    import hashlib

    with open(os.path.join(REPO, "data", "eac", "eac_gazette_register.json"), encoding="utf-8") as f:
        entree = next(g for g in json.load(f)["gazettes"] if g["reference"] == "EAC Gazette Vol. AT 1 No. 31")
    with open(os.path.join(REPO, entree["archive_path"]), "rb") as f:
        assert hashlib.sha256(f.read()).hexdigest() == entree["sha256"]
    assert {m["source_hash"] for m in _mesures_gazette()} == {entree["sha256"]}


# ── Le moteur : conditionnelle, jamais une préférence générale ───────────────


def test_sans_autorisation_le_droit_du_tec_reste_du_et_la_note_nomme_les_societes():
    mesure = _mesure_de(388)
    code = mesure["hs_code_from"]
    position, bloc = mesures_eac.appliquer(_position(code), "KEN", code, le=LE)

    assert _dd(position)["taux"] == 25.0
    note = _dd(position)["note"]
    assert "Legal Notice EAC/388/2026 : 0 %" in note and "Taux du TEC appliqué" in note
    assert mesure["named_beneficiary"] in note and "quantité allouée" in note
    assert bloc["autorisation_requise"] is True and bloc["taux_applique"] == 25.0


def test_une_autorisation_datee_qui_nomme_la_ligne_applique_la_remise():
    mesure = _mesure_de(388)
    code = mesure["hs_code_from"]
    autorisation = dict(
        eligibilite=RemissionEligibility.ELIGIBLE_VERIFIED, reference="KRA/REM/2026/388",
        debut=DATE_GAZETTE, fin=date(2027, 11, 11), lignes=[code],
    )
    position, bloc = mesures_eac.appliquer(_position(code), "KEN", code, le=LE, **autorisation)

    assert _dd(position)["taux"] == mesure["override_rate"] == 0.0
    assert bloc["taux_tec"] == 25.0 and bloc["taux_applique"] == 0.0

    autre = dict(autorisation, lignes=["72283099"])
    position, _ = mesures_eac.appliquer(_position(code), "KEN", code, le=LE, **autre)
    assert _dd(position)["taux"] == 25.0


def test_la_remise_n_est_pas_en_vigueur_avant_la_gazette_ni_apres_son_echeance():
    mesure = _mesure_de(388)
    code = mesure["hs_code_from"]
    veille, bloc = mesures_eac.appliquer(_position(code), "KEN", code, le=date(2026, 11, 11))
    assert bloc is None and "EAC/388/2026" not in (_dd(veille).get("note") or "")
    apres, bloc = mesures_eac.appliquer(_position(code), "KEN", code, le=date(2027, 11, 12))
    assert bloc is None and _dd(apres)["taux"] == 25.0


def test_une_remise_jusqu_au_30_juin_2027_s_arrete_a_cette_date():
    mesure = next(m for m in _mesures_gazette() if m["effective_to"] == "2027-06-30")
    code = mesure["hs_code_from"]
    _, bloc = mesures_eac.appliquer(_position(code), "KEN", code, le=date(2027, 6, 30))
    assert bloc is not None
    _, bloc = mesures_eac.appliquer(_position(code), "KEN", code, le=date(2027, 7, 1))
    # Une autre mesure du fichier peut couvrir la même ligne : aucune ne vient de la gazette 31.
    assert bloc is None or not any("EAC-4" in e["measure_id"] and "-2026-REMISSION" in e["measure_id"] and
                                   int(e["measure_id"].split("-")[1]) >= 388 for e in bloc["mesures"])


def test_les_remises_du_kenya_ne_valent_pas_pour_un_autre_etat_partenaire():
    mesure = _mesure_de(388)
    code = mesure["hs_code_from"]
    for etat in ("TZA", "UGA", "RWA", "BDI"):
        _, bloc = mesures_eac.appliquer(_position(code), etat, code, le=LE)
        assert bloc is None or not any(e["measure_id"].startswith("EAC-388-2026") for e in bloc["mesures"]), etat


def test_une_ligne_portee_par_plusieurs_societes_n_a_qu_une_note_par_avis():
    """EAC/393 : 4819.10.00 est alloué à une quinzaine de sociétés ; la note ne se répète pas."""
    code = "48191000"
    nommees = [m for m in _mesures_gazette() if m["hs_code_from"] == code and m["legal_reference"].endswith("/393/2026")]
    assert len(nommees) > mesures_eac.SOCIETES_AFFICHEES
    position, _ = mesures_eac.appliquer(_position(code, taux=35.0), "KEN", code, le=LE)
    note = _dd(position)["note"]

    assert note.count("Legal Notice EAC/393/2026 : 0 %") == 1
    assert note.count("remise réservée aux sociétés nommées") == 1
    noms = list(dict.fromkeys(m["named_beneficiary"] for m in nommees))
    reste = len(noms) - mesures_eac.SOCIETES_AFFICHEES
    assert f"et {reste} autre" in note
    # Les cinq premières sont nommées, les suivantes seulement comptées.
    assert all(nom in note for nom in noms[: mesures_eac.SOCIETES_AFFICHEES])
    assert not any(nom in note for nom in noms[mesures_eac.SOCIETES_AFFICHEES:])
    assert len(note) < 1500


# ── Aucun effet sur le calcul sans autorisation ──────────────────────────────


@besoin_socle
@pytest.mark.parametrize("origine", ["EGY", "BRA"])
def test_sans_autorisation_le_calcul_est_inchange(tmp_path, monkeypatch, origine):
    """Le tarif de base et la préférence ZLECAf du couloir ne bougent pas : le calcul d'une
    ligne de la gazette est le même avec et sans ces mesures dans le fichier."""
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    from routes import calcul as route

    app = FastAPI()
    app.include_router(route.router)
    client = TestClient(app)
    code = next(m["hs_code_from"] for m in _mesures_gazette() if m["named_beneficiary"])
    corps = {"destination": "KEN", "origine": origine, "code_sh": code, "valeur_cif": 10000, "quantites": {"kg": 100}}

    avec = client.post("/calcul", json=corps).json()
    assert avec["npf"]["lignes"]

    with open(mesures_eac.MESURES, encoding="utf-8") as f:
        donnees = json.load(f)
    donnees["measures"] = [m for m in donnees["measures"] if GAZETTE not in (m.get("gazette_number") or "")]
    fichier = tmp_path / "sans_gazette_31.json"
    fichier.write_text(json.dumps(donnees), encoding="utf-8")
    monkeypatch.setattr(mesures_eac, "MESURES", fichier)
    mesures_eac._mesures.cache_clear()
    try:
        sans = client.post("/calcul", json=corps).json()
    finally:
        monkeypatch.undo()
        mesures_eac._mesures.cache_clear()

    def lignes(corps_):
        return {
            bloc: [(ligne["code"], ligne.get("taux_pct"), ligne.get("montant")) for ligne in corps_[bloc]["lignes"]]
            for bloc in ("npf", "preference") if corps_.get(bloc)
        }

    assert lignes(avec) == lignes(sans)
    # Seule la note change : elle dit que le taux du TEC reste dû faute d'autorisation.
    notes_avec = " ".join(ligne.get("note") or "" for ligne in avec["npf"]["lignes"])
    notes_sans = " ".join(ligne.get("note") or "" for ligne in sans["npf"]["lignes"])
    assert "Taux du TEC appliqué" in notes_avec and "Gazette" not in notes_sans
