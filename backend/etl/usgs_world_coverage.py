"""
Couverture USGS — quels pays africains figurent parmi les producteurs listés.

DÉRIVÉE d'une source publiée, pas saisie à la main : le jeu de données
« U.S. Geological Survey Mineral Commodity Summaries 2025 Data Release
(ver. 2.0, avril 2025) », membre ``MCS2025_World_Data.csv``, publie la
production 2023 et l'estimation 2024 par commodité et par pays.
https://www.sciencebase.gov/catalog/item/677eaf95d34e760b392c4970

À QUOI CETTE LISTE SERT — ET CE QU'ELLE NE DIT PAS
---------------------------------------------------
Elle sert à répondre honnêtement quand un pays n'a aucune donnée minière chez
nous : plutôt qu'un onglet vide, l'API peut dire *ce qui a été consulté* et
*ce que la source en dit*.

Figurer dans cette liste signifie : USGS recense au moins une production
minérale pour ce pays. En être absent signifie UNIQUEMENT que USGS ne le
recense pas parmi les producteurs des commodités qu'il suit. **Ce n'est pas
une affirmation d'absence d'extraction** : MCS ne suit ni la production
artisanale, ni les volumes sous son seuil de significativité, ni les
hydrocarbures (couverts chez nous par EIA/OPEC) ni l'uranium (WNA).

Régénérer : télécharger le membre ``World_Data_Release_MCS_*.zip`` de la
publication ScienceBase de l'édition courante et rejouer la dérivation
décrite ci-dessus.
"""

from __future__ import annotations

from typing import FrozenSet

USGS_MCS_EDITION = "Mineral Commodity Summaries 2025 Data Release (ver. 2.0, avril 2025)"
USGS_MCS_SOURCE_URL = "https://www.sciencebase.gov/catalog/item/677eaf95d34e760b392c4970"

#: Pays africains recensés comme producteurs par USGS MCS 2025 (32 sur 54).
USGS_LISTED_PRODUCERS_AFRICA: FrozenSet[str] = frozenset(
    {
        "AGO",  # Angola — 2 commodité(s)
        "BDI",  # Burundi — 1 commodité(s)
        "BFA",  # Burkina Faso — 1 commodité(s)
        "BWA",  # Botswana — 3 commodité(s)
        "CIV",  # Côte d'Ivoire — 1 commodité(s)
        "CMR",  # Cameroun — 1 commodité(s)
        "COD",  # RD Congo — 7 commodité(s)
        "DZA",  # Algérie — 5 commodité(s)
        "EGY",  # Égypte — 4 commodité(s)
        "ETH",  # Éthiopie — 3 commodité(s)
        "GAB",  # Gabon — 1 commodité(s)
        "GHA",  # Ghana — 3 commodité(s)
        "GIN",  # Guinée — 2 commodité(s)
        "KEN",  # Kenya — 3 commodité(s)
        "LSO",  # Lesotho — 1 commodité(s)
        "MAR",  # Maroc — 5 commodité(s)
        "MDG",  # Madagascar — 7 commodité(s)
        "MLI",  # Mali — 1 commodité(s)
        "MOZ",  # Mozambique — 6 commodité(s)
        "MRT",  # Mauritanie — 1 commodité(s)
        "NAM",  # Namibie — 2 commodité(s)
        "NGA",  # Nigéria — 4 commodité(s)
        "RWA",  # Rwanda — 5 commodité(s)
        "SEN",  # Sénégal — 4 commodité(s)
        "SLE",  # Sierra Leone — 3 commodité(s)
        "TGO",  # Togo — 1 commodité(s)
        "TUN",  # Tunisie — 1 commodité(s)
        "TZA",  # Tanzanie — 4 commodité(s)
        "UGA",  # Ouganda — 3 commodité(s)
        "ZAF",  # Afrique du Sud — 22 commodité(s)
        "ZMB",  # Zambie — 1 commodité(s)
        "ZWE",  # Zimbabwe — 6 commodité(s)
    }
)
