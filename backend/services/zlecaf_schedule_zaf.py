"""
Partenaires ayant effectivement déclenché l'échange de préférences ZLECAf
à l'IMPORTATION en Afrique du Sud (et non via un autre régime, ex. SACU),
avec la DATE D'ENTRÉE EN VIGUEUR de l'avis qui a ajouté chacun.

Source authentique : General Note O du Schedule No. 1 (Customs and Excise
Act, 1964), telle qu'amendée par les Notices R. du Government Gazette :

- R.4287 (GG 50045, 26/01/2024, effet 31/01/2024) : substitution de la
  General Note O — liste initiale des États non-SADC ayant mis en œuvre
  leurs PSTC (« Algeria, Cameroon, Egypt, Ghana, Kenya, Rwanda, Tunisia »),
  chacun daté du 31 August 2023 dans le texte ; la préférence sud-africaine
  court à partir du gazettement, le 31/01/2024.
- R.5879 (GG 52150, 21/02/2025) : « Country Burundi Morocco Uganda,
  Date 21 February 2025 ».
- R.6233 (GG 52750, 30/05/2025) : « The Gambia 14 March 2025 » — effet
  rétroactif au 14/03/2025.
- R.6595 (GG 53334, 12/09/2025) : « Nigeria 30 May 2025 » — effet rétroactif
  au 30/05/2025.
- R.6756 (GG 53572, 24/10/2025) : « Ethiopia 14 August 2025 » — effet
  rétroactif au 14/08/2025.

Écart signalé (27/09/2026) : la newsletter dtic (mars 2026) cite aussi la
Sierra Leone parmi les pays « implementing », mais AUCUNE Notice R. des
listes 2024-2026 ne l'ajoute à la General Note O — elle n'est PAS dans
cette liste, qui est la seule source authentique. La Tanzanie n'y figure
pas non plus (noté dans la fiche).

Point clé explicitement confirmé par la FAQ du newsletter dtic (Q1) :
« South Africa will, therefore, not trade preferentially with SACU and SADC
Member States under the AfCFTA. » — les membres de la SACU (Botswana,
Lesotho, Namibie, Eswatini) échangent avec l'Afrique du Sud sous le régime
SACU, pas sous la ZLECAf ; ils sont volontairement exclus de cette liste.
"""

from __future__ import annotations

from datetime import date

# ISO3 -> date d'entrée en vigueur de l'avis qui a ajouté le partenaire.
DATES_ENTREE_ZAF = {
    # R.4287 (GG 50045, effet 31/01/2024) : liste initiale, sept partenaires.
    "DZA": "2024-01-31",
    "CMR": "2024-01-31",
    "EGY": "2024-01-31",
    "GHA": "2024-01-31",
    "KEN": "2024-01-31",
    "RWA": "2024-01-31",
    "TUN": "2024-01-31",
    # R.5879 (GG 52150, 21/02/2025).
    "MAR": "2025-02-21",
    "BDI": "2025-02-21",
    "UGA": "2025-02-21",
    # R.6233 (GG 52750, 30/05/2025) : effet rétroactif au 14/03/2025.
    "GMB": "2025-03-14",
    # R.6595 (GG 53334, 12/09/2025) : effet rétroactif au 30/05/2025.
    "NGA": "2025-05-30",
    # R.6756 (GG 53572, 24/10/2025) : effet rétroactif au 14/08/2025.
    "ETH": "2025-08-14",
}

#: Compatibilité : les partenaires actifs (les clés de DATES_ENTREE_ZAF).
ACTIVE_PARTNERS_ZAF = frozenset(DATES_ENTREE_ZAF)


def zaf_partner_active(origin_iso3: str, jour: date | None = None) -> bool:
    """True si la préférence ZLECAf sud-africaine vaut pour ce partenaire à
    la date donnée (aujourd'hui par défaut) : le partenaire doit figurer à
    la General Note O ET la date d'entrée en vigueur de son avis de
    ceint être passée."""
    date_entree = DATES_ENTREE_ZAF.get((origin_iso3 or "").upper())
    if date_entree is None:
        return False
    if jour is None:
        jour = date.today()
    annee, mois, jour_eff = (int(x) for x in date_entree.split("-"))
    return jour >= date(annee, mois, jour_eff)
