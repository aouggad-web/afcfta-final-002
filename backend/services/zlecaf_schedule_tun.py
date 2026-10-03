"""
Droit ZLECAf à l'IMPORTATION en Tunisie : coefficient de l'année × droit de
base 2019.

Source de la règle : texte TA n°016/2023 du 06/04/2023 (النشرية الرسمية
للديوانة n° 973), section V-2 — la réduction « s'applique sur la base des
taux de base de 2019, pris comme taux de référence ». Fiches :
TUN_application_2026-09-13.json, TUN_rapprochement_baremes_2026-09-29.json,
TUN_droit_de_base_2019_2026-10-03.json.

DEUX SOURCES, UNE PAR FACTEUR :

* **Le coefficient** est celui que la douane publie au Tarif Web 2026, zone
  « ZLECAf », par position et par origine (data/zlecaf_tun/). Il ne vaut que
  pour 2026 : hors de cette année, rien n'est servi.
* **Le droit de base 2019** est le taux de base de l'e-Tariff Book, lu au
  niveau de la ligne à 9 chiffres. Le ministère déclare que l'offre utilise
  les tarifs nationaux 2019 ; la loi de finances 2019 le confirme sur les
  lignes qu'elle modifie (art. 60 et 81). Décision du propriétaire du
  03/10/2026.

Le droit servi ne dépasse jamais le NPF du socle : l'importateur peut
toujours dédouaner au droit commun. Une position sans coefficient publié pour
l'origine, ou sans ligne e-Tariff, rend None et le NPF s'applique.

Seul le droit de douane est réduit.
"""

from __future__ import annotations

import datetime
import gzip
import json
from pathlib import Path
from typing import Optional, Tuple

_DATA = Path(__file__).resolve().parent.parent / "data"

with open(_DATA / "zlecaf_tun" / "coefficients_tarifweb_2026.json", encoding="utf-8") as f:
    _COEFFICIENTS = json.load(f)

ANNEE_DES_COEFFICIENTS = _COEFFICIENTS["_annee"]
MOTIFS = _COEFFICIENTS["motifs"]
POSITIONS = _COEFFICIENTS["positions"]

#: Origines auxquelles la douane publie au moins un coefficient.
ORIGINES_TARIF_WEB = frozenset(iso for motif in MOTIFS for iso in motif)

with gzip.open(
    _DATA / "official_preferential" / "TUN_afcfta_etariff_2026-10-03.json.gz", "rt", encoding="utf-8"
) as f:
    _ETARIFF = json.load(f)

#: Droit de base 2019 par ligne e-Tariff à 9 chiffres, en pourcentage.
DROIT_DE_BASE_2019 = {
    ligne["hs_code"]: float(ligne["mfn_rate_expression"]) for ligne in _ETARIFF["schedules"]["1"]
}

LIBELLE = "Texte TA n°016/2023, section V-2 : coefficient {annee} du Tarif Web ({coef:g} %) × droit de base 2019 de l'e-Tariff ({base:g} %)"


def compute_tun_zlecaf_rate(
    hs_code: str,
    origin_iso3: str,
    normal_rate_pct: Optional[float],
    as_of: Optional[datetime.date] = None,
) -> Tuple[Optional[float], str]:
    """Rendre (taux en %, libellé), ou (None, motif) quand rien n'est servi."""
    annee = (as_of or datetime.date.today()).year
    if annee != ANNEE_DES_COEFFICIENTS:
        return None, f"Coefficients ZLECAf tunisiens publiés pour {ANNEE_DES_COEFFICIENTS} seulement"
    code = "".join(ch for ch in str(hs_code) if ch.isdigit())
    motif = POSITIONS.get(code[:10])
    coef = MOTIFS[motif].get((origin_iso3 or "").upper()) if motif is not None else None
    if coef is None:
        return None, "Aucun coefficient ZLECAf publié au Tarif Web pour cette position et cette origine"
    base = DROIT_DE_BASE_2019.get(code[:9])
    if base is None:
        return None, "Position absente de l'e-Tariff : droit de base 2019 non établi"
    taux = round(coef * base / 100, 6)
    libelle = LIBELLE.format(annee=annee, coef=coef, base=base)
    if normal_rate_pct is not None and taux > normal_rate_pct:
        taux = float(normal_rate_pct)
        libelle = f"{libelle} ; plafonné au NPF"
    return taux, libelle
