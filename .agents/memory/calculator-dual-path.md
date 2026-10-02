---
name: Calculator dual computation path
description: The frontend has two calc paths (authentic path, then POST /api/calcul); POST /api/calculate-tariff, once the fallback, was retired in lot O2-0.
---

# Calculator has two computation paths, and the primary one bypasses the rich backend route

`frontend/src/components/calculator/CalculatorTab.jsx` `calculateTariff()` tries, in order:
1. **PRIORITY 1 — authentic path:** `GET /api/authentic-tariffs/calculate/{destISO3}/{hs}` then builds a hand-rolled `transformedResult`. This object does **NOT** carry `taxes_breakdown` or `currency`.
2. **FALLBACK — `POST /api/calcul`** (adapter `unifiedCalculator.js`), on a 404 or 422 `CALCULATION_UNAVAILABLE` from the authentic path; TUN and MUS go to `/calcul` first. `POST /api/calculate-tariff` and `backend/routes/calculator.py` were retired in lot O2-0.

`TaxBreakdownDual.jsx` (the component with the USD ⇄ local-currency toggle) only renders when `result.taxes_breakdown?.length > 0`, and the toggle only shows when `currency.available && currency.usd_to_local_rate`.

**Consequence (two real bugs that look unrelated but share this root cause):**
- For any destination **with** authentic data (notably **DZA**, the reference market), the UI uses the authentic path → no `currency`/`taxes_breakdown` → **local currency never displays** and the full NPF-vs-ZLECAf tax detail card is absent.
- (Historical, before lot O2-0) Fiscal logic that lived **only** in `routes/calculator.py` (e.g. the ZLECAf base-rate-2019 list-B override, the continental ratification gate, the ZAF active-partner gate) is **invisible in the UI for those same destinations**, because the frontend never calls that route for them.

**Why (historical):** the authentic endpoint and `/api/calculate-tariff` were independent implementations; only the latter was enriched with the currency block and the ZLECAf schedule/ratification gates.

**How to apply:** `/api/calculate-tariff` no longer exists (retired in lot O2-0). When a calculator change must show up in the UI for DZA (or any authentic-data country), make `/api/authentic-tariffs/calculate` reuse the same `compute_dza_zlecaf_rate` / ratification / ZAF gates AND emit `currency` + `taxes_breakdown`. Verifying a change only via a `curl` to `/api/calculate-tariff` is NOT proof the UI shows it.

**Update — partial fix done:** the authentic endpoint NOW emits `currency` + `taxes_breakdown` + `taxes_summary` (built directly from its own cascade steps for consistency, localized via `localize_breakdown`), so the local-currency toggle + per-tax NPF-vs-ZLECAf card render for DZA. **Still divergent:** the authentic path takes its ZLECAf DD rate from `line['zlecaf_rate']` (DZA list-B → 0% full exemption), NOT from `compute_dza_zlecaf_rate` (PR base-2019 × dismantling → 24% in 2026). So the two endpoints disagreed on the DZA ZLECAf DD rate (historical: `/api/calculate-tariff` was retired in lot O2-0).

**DZA fiscal stack (validated, authentic path):** DAPS is a **customs duty** (`category='droit_douane'`), summed with DD in `droit_douane`, and reduced under ZLECAf by the **same dismantling factor as DD** (factor = `zlecaf_rate/dd_rate`, or full exemption when `dd_rate==0` and the ZLECAf rate is 0). Cascade order = DAPS, DD, TCS, TVA, PRCT. TVA base = CIF+DAPS+DD. PRCT (« Précompte (PRCT) », official label, forced over stale crawled names like "Prélèvement à la Compensation du Transport") is computed **after** TVA on global VAT-incl value **excl DAPS** (CIF+DD+TCS+TVA). TCS stays 3% on CIF, **unaffected** by ZLECAf (user's explicit choice). The legacy "Détail des Taxes" card in CalculatorTab.jsx expects an **array** but the authentic path returns `taxes_detail` as a **dict** → that card never renders; the authoritative UI is `TaxBreakdownDual` (`taxes_breakdown[]`). `individual_taxes` is not consumed by the frontend.
