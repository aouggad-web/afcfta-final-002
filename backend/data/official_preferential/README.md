# Official preferential schedules: legal-use policy

This directory separates tariff content from legal applicability.

## Executable schedule

- ZAF_afcfta_2026-08-06.json.gz: current SARS Schedule 1 Part 1, AfCFTA
  column. Bilateral activation remains controlled by
  zlecaf_schedule_zaf.py.

## Offer snapshots (never executable by themselves)

The following gzip-compressed production e-Tariff Book snapshots are tagged
legal_effect_status=OFFER_ONLY and execution_authorized=false:

| Snapshot | Requested destinations covered |
|---|---|
| EAC | Kenya, Rwanda |
| ECOWAS | Ghana, Côte d'Ivoire, Nigeria |
| CEMAC | Cameroon |
| EGY | Egypt |
| TUN | Tunisia |
| ETH | Ethiopia |
| ZMB | Zambia |

zlecaf_implementation_registry.py is the independent legal gate. A rate is
returned only when it confirms:

1. a domestic or regional implementation instrument in force;
2. the exact exporting country in an official reciprocal partner list;
3. an exact national tariff line and applicable annual column; and
4. the requirement for valid AfCFTA origin proof.

As reviewed on 2026-08-17, Kenya is the only newly prioritised destination
meeting all machine-verifiable gates: Legal Notice EAC/321/2022 plus KRA's
explicit list of 21 accepted origins. Ethiopia, Zambia, Côte d'Ivoire and
Nigeria have domestication evidence but no official exhaustive partner list
was found. Cameroon, Egypt, Ghana, Rwanda and Tunisia therefore remain
offer-only in the calculator as well. Missing evidence is NOT_AVAILABLE,
never zero.

## Reproduction

- SARS: python backend/scripts/extract_sars_afcfta_schedule.py
- e-Tariff Book:
  python backend/scripts/collect_afcfta_etariff_book.py backend/data/official_preferential
