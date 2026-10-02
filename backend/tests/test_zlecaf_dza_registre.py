"""Algérie : la circulaire 482/2024 est inscrite au registre d'application.

Le chemin historique servait déjà le calendrier algérien ; le moteur du socle,
faute d'entrée au registre, s'arrêtait avant. Ce fichier verrouille : les neuf
origines admises, l'exonération du DAPS, le refus d'une origine non admise et
le même droit de douane dans les deux chemins.
"""

from __future__ import annotations

from services.authentic_tariff_service import calculate_import_taxes
from services.preference import taux_preferentiels
from services.zlecaf_implementation_registry import APPLIED, RECORDS
from services.zlecaf_schedule_dza import ACTIVE_PARTNERS

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


def test_le_registre_porte_les_neuf_origines_de_la_circulaire():
    record = RECORDS["DZA"]
    assert record.status == APPLIED
    assert record.accepted_origins == ACTIVE_PARTNERS
    assert len(record.accepted_origins) == 9
    assert record.effective_from == "2024-11-01"


def test_le_socle_sert_la_liste_a_et_exonere_le_daps():
    resultat = taux_preferentiels(_position(), "DZA", "TUN", CODE)
    assert resultat["applique"] is True
    assert resultat["taux"]["DD"]["taux"] == 0.0
    assert resultat["taux"]["DAPS"]["taux"] == 0.0


def test_une_origine_non_admise_reste_au_npf():
    # Le Maroc a ratifié mais n'est pas parmi les neuf origines admises.
    resultat = taux_preferentiels(_position(), "DZA", "MAR", CODE)
    assert resultat["applique"] is False
    assert resultat["taux"] == {}


def test_les_deux_chemins_servent_le_meme_droit_de_douane():
    socle = taux_preferentiels(_position(), "DZA", "TUN", CODE)["taux"]["DD"]["taux"]
    historique = calculate_import_taxes("DZA", CODE, 1000.0, origin_country="TUN")
    assert historique["rates"]["effective_zlecaf_rate_pct"] == socle
