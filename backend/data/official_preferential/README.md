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
| TUN | Tunisia (recollected 2026-10-03: the August snapshot lacked chapters 29, 84 and 85) |
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

Update 2026-10-03 — Tunisia: only the e-Tariff *base rate* is used, as the
2019 base duty of text TA n°016/2023, multiplied by the 2026 coefficient the
customs publish in Tarif Web 2026 (services/zlecaf_schedule_tun.py, fiche
TUN_droit_de_base_2019_2026-10-03.json). The e-Tariff country calendar is
never served for Tunisia.

Known collection gap (2026-10-03): the API returns an empty list for some
whole-chapter searches while serving their headings one by one. Every
snapshot dated before 2026-10-03 lacks chapter 84; MAR also lacks 29, 39 and
85, ZMB lacks 29. The collector now re-reads an empty chapter heading by
heading. Recollected on 2026-10-03: TUN, MAR (also checked against the
Liste A of amendment 6627/223, services/zlecaf_schedule_mar.py), ECOWAS,
CEMAC, EGY, ETH, ZMB and ZWE. EAC is not recollected: the EAC destinations
are served from the gazetted Legal Notice EAC/321/2022, never from this
snapshot.

## Reproduction

- SARS: python backend/scripts/extract_sars_afcfta_schedule.py
- e-Tariff Book:
  python backend/scripts/collect_afcfta_etariff_book.py backend/data/official_preferential
