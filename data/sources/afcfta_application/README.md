# AfCFTA tariff application evidence — review 2026-08-17

The calculator distinguishes four facts that are often conflated:

1. ratification;
2. a tariff offer/PSTC;
3. domestic legal implementation; and
4. reciprocal acceptance of the exact exporting country.

Only the last two, combined with an exact tariff line and origin proof, can
authorise a preferential calculation.

| Destination | Reviewed evidence | Calculator status |
|---|---|---|
| South Africa | Current SARS Schedule 1 Part 1 plus the reviewed active-partner list | Applied for confirmed partners |
| Kenya | EAC/321/2022 and KRA's explicit 21-country import list | Applied only for the 21 named origins |
| Ethiopia | Regulation 574/2025; article 3(2) requires a separate notified partner list | Partner notice required |
| Zambia | SI 92/2024 domestication confirmed by Parliament; no exhaustive reciprocal-origin list found | Partner notice required |
| Côte d'Ivoire | Ordinance of 23 April 2025; application expressly reciprocal; no accepted-origin list found | Partner notice required |
| Nigeria | PSTC gazetting confirmed; no accepted-origin list found | Partner notice required |
| Cameroon | CEMAC PSTC in e-Tariff Book; no complete domestic/corridor proof reviewed | Offer only |
| Egypt | National PSTCs in e-Tariff Book; no complete domestic/corridor proof reviewed | Offer only |
| Ghana | ECOWAS PSTC in e-Tariff Book; GTI participation alone rejected as a legal switch | Offer only |
| Rwanda | EAC PSTC in e-Tariff Book; Kenya's national operational notice is not imputed to Rwanda | Offer only |
| Tunisia | National PSTCs in e-Tariff Book; no complete domestic/corridor proof reviewed | Offer only |

Primary sources are recorded in inventory.csv and in
backend/services/zlecaf_implementation_registry.py. Absence of a verified
partner notice yields NOT_AVAILABLE, never a zero rate.
