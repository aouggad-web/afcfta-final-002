"""
Barème ZLECAf applicable à l'IMPORTATION aux Seychelles.

Source authentique : Customs Management (Tariff and Classification of Goods)
Regulations, 2022 — S.I. 113 of 2022, Supplement to Official Gazette du
28/10/2022, en vigueur le 01/11/2022 (fiche SYC_application_2026-09-28.json).

* Regulation 2(6) : « The list of African Continental Free Trade Area (AfCFTA)
  State Parties are specified in Schedule VI. » — la Schedule VI énumère 38
  États, transcrits ci-dessous dans l'ordre du texte.
* Le barème porte une sous-colonne AfCFTA par année civile, de 2022 à 2026.
  Aucune année au-delà n'est publiée : hors de cette plage, rien n'est servi.

Seul le droit de douane est réduit.
"""

from __future__ import annotations

from typing import Optional

#: Schedule VI du S.I. 113 of 2022, « List of African Continental Free Trade
#: Area (AfCFTA) Member States », 38 entrées (p. 1901-1902 de la gazette).
ORIGINES_SCHEDULE_VI = frozenset(
    {
        "EGY",  # 1. Arab Republic of Egypt
        "CAF",  # 2. Central African Republic
        "GNQ",  # 3. Equatorial Guinea
        "SWZ",  # 4. Kingdom of Eswatini
        "LSO",  # 5. Kingdom of Lesotho
        "AGO",  # 6. Republic of Angola
        "BFA",  # 7. Republic of Burkina Faso
        "BDI",  # 8. Republic of Burundi
        "CMR",  # 9. Republic of Cameroon
        "TCD",  # 10. Republic of Chad
        "COG",  # 11. Republic of the Congo
        "DJI",  # 12. Republic of Djibouti
        "ETH",  # 13. Republic of Ethiopia
        "GMB",  # 14. Republic of Gambia
        "GAB",  # 15. Republic of Gabon
        "GHA",  # 16. Republic of Ghana
        "GIN",  # 17. Republic of Guinea
        "CIV",  # 18. Republic of Ivory Coast
        "KEN",  # 19. Republic of Kenya
        "MWI",  # 20. Republic of Malawi
        "MLI",  # 21. Republic of Mali
        "MRT",  # 22. Republic of Mauritania
        "MUS",  # 23. Republic of Mauritius
        "NAM",  # 24. Republic of Namibia
        "NER",  # 25. Republic of Niger
        "NGA",  # 26. Republic of Nigeria
        "RWA",  # 27. Republic of Rwanda
        "STP",  # 28. Republic of Sao Tome and Principe
        "SEN",  # 29. Republic of Senegal
        "SLE",  # 30. Republic of Sierra Leone
        "ZAF",  # 31. Republic of South Africa
        "TGO",  # 32. Republic of Togo
        "TUN",  # 33. Republic of Tunisia
        "UGA",  # 34. Republic of Uganda
        "ZMB",  # 35. Republic of Zambia
        "ZWE",  # 36. Republic of Zimbabwe
        "ESH",  # 37. Sahrawi Arab Democratic Republic
        "DZA",  # 38. Socialist Republic of Algeria
    }
)

#: Années publiées par le barème : une sous-colonne AfCFTA par année.
ANNEES_PUBLIEES = range(2022, 2027)


def colonne_de_l_annee(annee: int) -> Optional[str]:
    """Code de la sous-colonne AfCFTA de l'année, None hors 2022-2026."""
    return f"AFCFTA_{annee}" if annee in ANNEES_PUBLIEES else None
