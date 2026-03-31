def simulate(payload, tariff, country_rules, preference):
    cif = float(payload["cif_value"])
    qty = float(payload["quantity"])

    dd = float(tariff.get("DD", 0))
    if payload.get("origin_certificate") and preference.get("DD") is not None:
        dd = float(preference["DD"])

    duty = cif * dd / 100.0
    prct = cif * float(tariff.get("PRCT", 0)) / 100.0
    tcs  = cif * float(tariff.get("TCS", 0)) / 100.0

    specific_sum = 0.0
    for st in tariff.get("SPECIFIC", []):
        specific_sum += float(st["amount"]) * qty

    vat_rate = float(country_rules["vat_rate"])
    vat_on_duty = bool(country_rules.get("vat_on_duty", True))
    base = cif + (duty + specific_sum if vat_on_duty else 0.0)
    vat = base * vat_rate / 100.0

    total_taxes = duty + prct + tcs + specific_sum + vat
    return {
        "cif": cif,
        "duty": duty,
        "prct": prct,
        "tcs": tcs,
        "specific_sum": specific_sum,
        "vat": vat,
        "total_taxes": total_taxes,
        "total_landed_cost": cif + total_taxes
    }
