"""
Statut d'adhésion à l'Accord ZLECAf (AfCFTA), niveau continental, par pays.

Source authentique : « Update on the AfCFTA » (the dtic / SARS, newsletter
mars 2026) :
  - « 54 of the 55 AU members have signed (except Eritrea) » ;
  - « 50 of these Members have ratified the Agreement... 4 countries,
    namely Benin, Libya, South Sudan and Sudan are yet to ratify the
    Agreement. » ;
  - « Tariff Offers Verified: 48 offers have been approved by the
    Secretariat. » (sur 50 ratifications, donc 2 pays ratifiés n'ont pas
    encore d'offre tarifaire vérifiée — non nommés par la source) ;
  - « Active Implementation: 25 countries have started preferential trade
    on 90% coverage of tariff books. » (sur les 48 offres vérifiées — liste
    nominative non fournie par la source au niveau continental ; seules des
    listes bilatérales spécifiques par pays importateur sont publiées, ex.
    circulaire DGD 482/2024 pour l'Algérie, ou la liste des partenaires
    d'application effective de l'Afrique du Sud — voir
    zlecaf_schedule_dza.py / zlecaf_schedule_zaf.py).

Pas de fabrication : seuls les statuts explicitement nommés par la source
sont distingués. Tout pays non cité dans NOT_SIGNED ou SIGNED_NOT_RATIFIED
est classé RATIFIED par défaut (50 pays sur 55), sans préjuger du dépôt
effectif d'une offre tarifaire (qui reste à vérifier au cas par cas via les
modules bilatéraux dédiés).
"""

from __future__ import annotations

NOT_SIGNED = frozenset({"ERI"})  # Érythrée : seul membre UA non signataire

SIGNED_NOT_RATIFIED = frozenset({"BEN", "LBY", "SSD", "SDN"})  # Bénin, Libye, Soudan du Sud, Soudan

STATUS_NOT_SIGNED = "NOT_SIGNED"
STATUS_SIGNED_NOT_RATIFIED = "SIGNED_NOT_RATIFIED"
STATUS_RATIFIED = "RATIFIED"


def ratification_status(iso3: str) -> str:
    """Statut de ratification de l'Accord ZLECAf pour un pays (ISO3).

    Ne dit rien sur le dépôt d'une offre tarifaire ni sur l'application
    effective bilatérale : un pays RATIFIED peut très bien ne pas (encore)
    échanger de préférences ZLECAf avec un partenaire donné (voir modules
    bilatéraux dédiés par pays importateur)."""
    code = (iso3 or "").upper()
    if code in NOT_SIGNED:
        return STATUS_NOT_SIGNED
    if code in SIGNED_NOT_RATIFIED:
        return STATUS_SIGNED_NOT_RATIFIED
    return STATUS_RATIFIED


def is_party_to_agreement(iso3: str) -> bool:
    """True si le pays a ratifié l'Accord ZLECAf (condition nécessaire mais
    pas suffisante pour bénéficier de préférences tarifaires effectives)."""
    return ratification_status(iso3) == STATUS_RATIFIED
