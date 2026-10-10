"""
Échéance des calendriers ZLECAf publiés année par année.

Les Seychelles (S.I. 113 of 2022) publient une sous-colonne AfCFTA par année,
2022 à 2026 ; la Tunisie (Texte TA n°016/2023, Tarif Web) ses coefficients
pour 2026 seulement. Au 1er janvier suivant la dernière année, le moteur ne
sert plus aucune préférence pour ces destinations — à raison, faute de taux
publié, mais sans que rien ne le signale (audit du 2026-10-09, point 12).

Ce contrôle alerte dans les 90 jours qui précèdent l'échéance, sans faire
échouer la CI : un avertissement dans le résumé pytest, et une annotation
GitHub Actions sur le run. Il échoue une fois l'échéance passée, quand les
préférences ont effectivement disparu de l'écran.
"""

from __future__ import annotations

import datetime
import os
import sys
import warnings

import pytest

from services.zlecaf_schedule_syc import ANNEES_PUBLIEES
from services.zlecaf_schedule_tun import ANNEE_DES_COEFFICIENTS

#: Dernière année couverte, par destination, et le texte à collecter ensuite.
CALENDRIERS = {
    "SYC": (max(ANNEES_PUBLIEES), "la sous-colonne AfCFTA du S.I. tarifaire des Seychelles"),
    "TUN": (ANNEE_DES_COEFFICIENTS, "les coefficients ZLECAf du Tarif Web tunisien"),
}

PREAVIS = datetime.timedelta(days=90)

OK, ALERTE, EXPIRE = "OK", "ALERTE", "EXPIRE"


def echeance(derniere_annee: int, aujourd_hui: datetime.date) -> str:
    fin = datetime.date(derniere_annee + 1, 1, 1)
    if aujourd_hui >= fin:
        return EXPIRE
    if aujourd_hui >= fin - PREAVIS:
        return ALERTE
    return OK


def test_la_regle_d_echeance():
    assert echeance(2026, datetime.date(2026, 10, 2)) == OK
    assert echeance(2026, datetime.date(2026, 10, 3)) == ALERTE
    assert echeance(2026, datetime.date(2026, 12, 31)) == ALERTE
    assert echeance(2026, datetime.date(2027, 1, 1)) == EXPIRE


@pytest.mark.parametrize("pays", sorted(CALENDRIERS))
def test_le_calendrier_couvre_l_annee_en_cours(pays):
    derniere_annee, texte = CALENDRIERS[pays]
    etat = echeance(derniere_annee, datetime.date.today())
    message = (
        f"Calendrier ZLECAf {pays} publié jusqu'en {derniere_annee} : au 1er janvier "
        f"{derniere_annee + 1}, plus aucune préférence n'est servie. Collecter {texte} "
        f"pour {derniere_annee + 1}."
    )
    assert etat != EXPIRE, message
    if etat == ALERTE:
        warnings.warn(message, UserWarning)
        if os.environ.get("GITHUB_ACTIONS"):
            sys.__stdout__.write(f"::warning title=Échéance du calendrier ZLECAf {pays}::{message}\n")
