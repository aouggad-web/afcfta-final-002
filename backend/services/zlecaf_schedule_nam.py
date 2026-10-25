"""
Partenaires auxquels la Namibie accorde la colonne AfCFTA de son tarif, avec
la date à partir de laquelle chacun y a droit (règle SACU, validée le
25/10/2026 : General Note O, colonne AfCFTA et acte qui les met en vigueur).

Source authentique : General Note O du Schedule No. 1 (Customs and Excise
Act, 1998), Government Notice No. 390 of 2024 (Gazette No. 8542 du
20/12/2024), amendée par le Government Notice No. 229 of 2025 (Gazette
No. 8731 du 04/09/2025). Fiche : NAM_zlecaf_2026-10-25.json.

- Note O.1 : « Algeria, Cameroon, Egypt, Ghana, Kenya, Rwanda, Tunisia »,
  chacun daté du « 31 August 2023 » dans le texte.
- GN 229/2025 : « Gambia » et « the date 14 March 2024 » (l'Afrique du Sud
  porte le 14 March 2025, R.6233).
- Note O.6 : les États parties « qualify for the preferential rate contained
  in the AfCFTA column from the date these State Parties are listed in Note 1
  by Notice published in the Government Gazette ». La date retenue est donc
  celle de la publication de l'avis qui inscrit l'État, pas la date imprimée
  en regard de son nom.

Les taux sont ceux de la colonne AfCFTA namibienne (GN 391/2024, amendé par le
GN 174/2026), portés par le socle (scripts/build_socle.py, ZLECAF_NAM).
Les membres de la SADC échangent sous le Protocole SADC (Note O.6).
"""

from __future__ import annotations

from datetime import date

# ISO3 -> date de publication de l'avis qui a inscrit le partenaire.
DATES_ENTREE_NAM = {
    # GN 390/2024 (Gazette No. 8542, 20/12/2024).
    "DZA": "2024-12-20",
    "CMR": "2024-12-20",
    "EGY": "2024-12-20",
    "GHA": "2024-12-20",
    "KEN": "2024-12-20",
    "RWA": "2024-12-20",
    "TUN": "2024-12-20",
    # GN 229/2025 (Gazette No. 8731, 04/09/2025).
    "GMB": "2025-09-04",
}


def nam_partner_active(origin_iso3: str, jour: date | None = None) -> bool:
    """True si la colonne AfCFTA namibienne vaut pour ce partenaire à la date
    donnée (aujourd'hui par défaut)."""
    date_entree = DATES_ENTREE_NAM.get((origin_iso3 or "").upper())
    if date_entree is None:
        return False
    return (jour or date.today()) >= date.fromisoformat(date_entree)
