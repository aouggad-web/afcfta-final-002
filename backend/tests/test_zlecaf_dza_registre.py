"""Algérie : la circulaire 482/2024 est inscrite au registre d'application.

Le chemin historique servait déjà le calendrier algérien ; le moteur du socle,
faute d'entrée au registre, s'arrêtait avant. Ce fichier verrouille : les origines
admises (neuf de la circulaire, douze de la liste de la Douane du 16/11/2026), l'exonération du DAPS, le refus d'une origine non admise et
le droit de douane servi par la réponse publique de `POST /calcul`.
"""

from __future__ import annotations

from routes.calcul import DemandeCalcul, calcul
from services.preference import taux_preferentiels
from services.zlecaf_implementation_registry import APPLIED, RECORDS
from services.zlecaf_schedule_dza import ACTIVE_PARTNERS, ORIGINES_CIRCULAIRE_482

#: Ligne réelle de la liste (A) : DD 30 %, DAPS 70 % (tarif algérien collecté).
CODE = "0204501100"


def _position() -> dict:
    return {
        "droits": [
            {"code": "DD", "taux": 30.0, "assiette": "CIF", "famille": "droit"},
            {"code": "DAPS", "taux": 70.0, "assiette": "CIF", "famille": "droit"},
        ],
        "preferentiels": {},
    }


def test_le_registre_porte_les_origines_de_la_circulaire_et_de_la_liste_de_la_douane():
    record = RECORDS["DZA"]
    assert record.status == APPLIED
    assert record.accepted_origins == ACTIVE_PARTNERS
    assert len(record.accepted_origins) == 21
    assert ORIGINES_CIRCULAIRE_482 <= record.accepted_origins
    assert "preuve secondaire" in record.note
    assert record.effective_from == "2024-11-01"


def test_le_socle_sert_la_liste_a_et_exonere_le_daps():
    resultat = taux_preferentiels(_position(), "DZA", "TUN", CODE)
    assert resultat["applique"] is True
    assert resultat["taux"]["DD"]["taux"] == 0.0
    assert resultat["taux"]["DAPS"]["taux"] == 0.0


def test_une_origine_non_admise_reste_au_npf():
    # Le Sénégal a ratifié mais ne figure ni dans la circulaire ni dans la liste de la
    # Douane.
    resultat = taux_preferentiels(_position(), "DZA", "SEN", CODE)
    assert resultat["applique"] is False
    assert resultat["taux"] == {}


def test_la_reponse_publique_sert_le_droit_du_registre():
    registre = taux_preferentiels(_position(), "DZA", "TUN", CODE)["taux"]["DD"]["taux"]
    reponse = calcul(
        DemandeCalcul(destination="DZA", origine="TUN", code_sh=CODE, valeur_cif=1000.0)
    )
    dd = next(l for l in reponse["preference"]["lignes"] if l["code"] == "DD")
    assert dd["taux_pct"] == registre
