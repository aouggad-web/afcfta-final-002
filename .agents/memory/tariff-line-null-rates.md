---
name: Tariff line null rate fields
description: Real tariff data can carry explicit JSON null for rate fields; coerce to 0 or the calculator crashes and the VAT fallback silently breaks.
---

# Tariff line null rate fields

Real tariff-line data (e.g. authentic DZA lines) can contain an **explicit JSON
`null`** for numeric rate fields — `vat_rate`, `dd_rate`, `other_taxes_rate`,
`zlecaf_rate`. `dict.get(key, 0)` returns `None` (not the default) when the key
exists with a null value, so always coerce: `line.get('vat_rate', 0) or 0`.

**Why:** Two distinct failures occur if `None` propagates:
1. A `TypeError: '>' not supported between 'NoneType' and 'int'` crashes the
   cascade build (`if vat_rate_pct > 0`) → 500 on the calculator.
2. The VAT fallback that pulls TVA from `taxes_detail` is guarded by
   `vat_rate_pct == 0`. With `None`, `None == 0` is False, so VAT is *silently
   dropped* — under-calculating tax on the validation-reference product. The
   crash is loud; this second one is silent and worse for fiscal accuracy.

**How to apply:** Any new code reading a rate off a tariff line must `or 0` it at
the point of extraction. Unit-test real-data shapes with null rate fields plus a
matching `taxes_detail` entry, not just synthetic lines with clean numbers — the
monkeypatched test lines hid this for a long time.
