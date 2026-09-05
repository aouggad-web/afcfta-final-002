---
name: Trade regime precedence (customs unions vs ZLECAf vs FTAs)
description: How the tariff calculator decides which preferential regime applies between an origin and destination African country.
---

# Trade regime precedence

When resolving the preferential regime for an origin→destination pair, the order is:

1. **Customs unions** (SACU, EAC, CEMAC, UEMOA) → free circulation, intra-bloc
   customs duty recalculated to **0 %**. This check comes **first**, *before* the
   ZLECAf ratification gate.
2. **ZLECAf** ratification + bilateral activation (Algeria active-partner schedule,
   South Africa active partners, else generic line rate).
3. **Free-trade areas** (ECOWAS, SADC, COMESA) → **conditional metadata only**,
   surfaced as `FTA_CONDITIONAL`. **No automatic recalculation** of duties.
4. **NPF** (most-favoured-nation) default.

**Why:** Two members of the same customs union trade in free circulation under the
union (common external tariff + zero intra-bloc duty), *not* under ZLECAf —
confirmed by the dtic/SARS "Update on the AfCFTA" newsletter (March 2026):
"South Africa will not trade preferentially with SACU and SADC Member States
under the AfCFTA." FTAs (unlike customs unions) only grant duty-free access to
goods that satisfy the bloc's rules of origin and are off the sensitive/exclusion
lists — and those product schedules + origin rules are not reliably modelled here,
so applying 0 % automatically would be wrong (e.g. ERI↔EGY via COMESA must NOT
auto-zero-rate).

**How to apply:**
- Membership rosters live in `backend/services/regional_blocs.py`
  (`same_customs_union`, `shared_free_trade_areas`); reuse them, never re-list members.
- A country can belong to a customs union AND an overlapping FTA (e.g. ZAF/BWA are
  SACU + SADC) — the customs-union result wins; the FTA is informational.
- Algeria is in no sub-Saharan customs union, so its authentic ZLECAf schedule is
  untouched by bloc logic.
- API distinguishes `preferential_regime_applied` (a preference actually reduced
  the duty on *this* product) from `zlecaf_eligible` (strict ZLECAf eligibility);
  legacy `zlecaf_*` fields are kept alongside the generic `trade_regime*` fields.
- Bloc rosters are hardcoded — treat membership edge cases (e.g. EAC/Somalia,
  transitional accessions) as needing source verification before relying on them
  for regulatory output.
- **User rule (decision):** a country gets customs-union 0 % treatment ONLY when
  its membership is *officially confirmed AND ratified*. For any pending /
  unratified / transitional accession, leave the roster as-is (do NOT add it to a
  customs union) and let it fall through to ZLECAf-if-eligible. Roster details to
  be verified later — stay conservative until then. This is already how the
  precedence chain behaves: non-customs-union members flow to the ZLECAf path.
