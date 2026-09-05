"""
Partenaires ayant effectivement déclenché l'échange de préférences ZLECAf
à l'IMPORTATION en Afrique du Sud (et non via un autre régime, ex. SACU).

Source authentique : « Update on the AfCFTA » (the dtic / SARS, newsletter
mars 2026), section « What Exporters should know… » :
« Beyond SADC, new market access opportunities are in the following
implementing countries: Ghana, Nigeria, Sierra Leone, The Gambia, Ethiopia,
Cameroon, Tunisia, Algeria, Egypt, Morocco, Kenya, Rwanda, Uganda,
Burundi. »

Point clé explicitement confirmé par la FAQ du même document (Q1) :
« No. […] South Africa will, therefore, not trade preferentially with
SACU and SADC Member States under the AfCFTA. » — les membres de la SACU
(Botswana, Lesotho, Namibie, Eswatini) échangent avec l'Afrique du Sud sous
le régime SACU, pas sous la ZLECAf ; ils sont donc volontairement exclus de
cette liste.

Cette liste est analogue, dans son principe, à `ACTIVE_PARTNERS` de
`zlecaf_schedule_dza.py` : l'activation de la ZLECAf est bilatérale
(notification/gazette réciproque), pas un statut continental unique. Aucun
calendrier tarifaire détaillé par produit (listes A/B/C sud-africaines)
n'est disponible dans cette source : ce module ne fournit qu'un statut
d'éligibilité, pas un taux.
"""

from __future__ import annotations

ACTIVE_PARTNERS_ZAF = frozenset(
    {
        "GHA",
        "NGA",
        "SLE",
        "GMB",
        "ETH",
        "CMR",
        "TUN",
        "DZA",
        "EGY",
        "MAR",
        "KEN",
        "RWA",
        "UGA",
        "BDI",
    }
)


def zaf_partner_active(origin_iso3: str) -> bool:
    """True si l'Afrique du Sud échange déjà des préférences ZLECAf
    (hors SACU) avec ce pays partenaire à l'importation."""
    return (origin_iso3 or "").upper() in ACTIVE_PARTNERS_ZAF
