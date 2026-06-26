#!/usr/bin/env python3
"""
Build canonical EGY_tariffs.json from the official customs.gov.eg V2 crawl.

Input  : egy_raw_v2.json — 8,746 HS10 positions crawled from the Egyptian
         Customs Authority portal (Moslaha El Gamareg, customs.gov.eg/Services/Tarif).
         Each position carries REAL per-line Customs Duty (DD), VAT, schedule
         ("table") tax, and the official Arabic regulatory instructions — which
         include Egypt's AfCFTA/ZLECAf dismantling schedule:
             ر6790 — AfCFTA Group [A]: 100% DD reduction  (→ 0%)
             ر6791 — AfCFTA Group [B]:  60% DD reduction  (→ DD × 0.4)
             ر6792 / ر6793 — category-based AfCFTA rates

Output : backend/data/EGY_tariffs.json — canonical HS6 tariff_lines with HS10
         sub_positions, matching the schema consumed by tariff_data_service /
         authentic_tariff_service / the calculator.

The WCO HS French/English designations, product category and standard
administrative formalities are reused from the existing EGY_tariffs.json
(WCO HS 2022 nomenclature, already in the repo) keyed by HS6 — NOT fabricated.
Only the fiscal data (DD, VAT, table tax, AfCFTA treatment) is replaced with the
authentic per-position values from the official crawl.

Usage:
    python3 backend/scripts/build_egy_tariffs_v2.py --raw /path/to/egy_raw_v2.json
"""

import argparse
import collections
import json
import os
import re
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(HERE, "..", "data")
OLD_EGY = os.path.join(DATA_DIR, "EGY_tariffs.json")
OUT_FILE = os.path.join(DATA_DIR, "EGY_tariffs.json")

# ── AfCFTA instruction codes (official Egyptian tariff notes) ───────────────────
AFCFTA_A_100 = "ر6790"  # Group A — 100% DD reduction
AFCFTA_B_60 = "ر6791"  # Group B —  60% DD reduction
AFCFTA_A_CAT = "ر6792"  # Group A — category-based rate
AFCFTA_B_CAT = "ر6793"  # Group B — category-based rate


def _has(instructions, code):
    return any(i.startswith(code) for i in instructions)


def build_hs6_meta(old_path):
    """HS6 -> {description_fr, description_en, category, unit, administrative_formalities}
    sourced from the existing WCO-based nomenclature already in the repo."""
    meta = {}
    if not os.path.exists(old_path):
        return meta
    with open(old_path, encoding="utf-8") as f:
        old = json.load(f)
    for line in old.get("tariff_lines", []):
        hs6 = line.get("hs6")
        if not hs6:
            continue
        meta[hs6] = {
            "description_fr": line.get("description_fr", ""),
            "description_en": line.get("description_en", ""),
            "category": line.get("category", "general"),
            "unit": line.get("unit", "KG"),
            "administrative_formalities": line.get("administrative_formalities", []),
        }
    return meta


def afcfta_advantages(dd_rate, instructions):
    """Return (zlecaf_rate, zlecaf_source, fiscal_advantages[]) from official notes."""
    advantages = []
    a100 = _has(instructions, AFCFTA_A_100)
    b60 = _has(instructions, AFCFTA_B_60)
    acat = _has(instructions, AFCFTA_A_CAT)
    bcat = _has(instructions, AFCFTA_B_CAT)

    if a100:
        advantages.append(
            {
                "tax": "D.D",
                "rate": 0.0,
                "regime": "ZLECAf — Groupe A",
                "condition_fr": "Démantèlement tarifaire ZLECAf Groupe A : réduction 100% du Droit de Douane (Certificat d'Origine ZLECAf requis)",
                "condition_en": "AfCFTA Group A tariff dismantling: 100% Customs Duty reduction (AfCFTA Certificate of Origin required)",
                "legal_ref": "Tarif douanier égyptien — note ر6790 ; AfCFTA Protocol on Trade in Goods",
            }
        )
    if b60 and dd_rate is not None:
        advantages.append(
            {
                "tax": "D.D",
                "rate": round(dd_rate * 0.4, 3),
                "regime": "ZLECAf — Groupe B",
                "condition_fr": "Démantèlement tarifaire ZLECAf Groupe B : réduction 60% du Droit de Douane (Certificat d'Origine ZLECAf requis)",
                "condition_en": "AfCFTA Group B tariff dismantling: 60% Customs Duty reduction (AfCFTA Certificate of Origin required)",
                "legal_ref": "Tarif douanier égyptien — note ر6791 ; AfCFTA Protocol on Trade in Goods",
            }
        )
    if acat or bcat:
        advantages.append(
            {
                "tax": "D.D",
                "rate": dd_rate,
                "regime": "ZLECAf — taux par catégorie",
                "condition_fr": "Droit de Douane ZLECAf perçu selon les catégories indiquées en regard du bloc tarifaire",
                "condition_en": "AfCFTA Customs Duty levied according to the categories shown against the tariff line",
                "legal_ref": "Tarif douanier égyptien — notes ر6792 / ر6793",
            }
        )

    # Headline ZLECAf rate (best available preferential = AfCFTA end-state)
    if a100:
        return 0.0, "ZLECAf Groupe A — démantèlement 100% (note ر6790)", advantages
    if b60 and dd_rate is not None:
        return round(dd_rate * 0.4, 3), "ZLECAf Groupe B — réduction 60% (note ر6791)", advantages
    if (acat or bcat) and dd_rate is not None:
        return dd_rate, "ZLECAf — taux par catégorie (notes ر6792/ر6793)", advantages
    # No AfCFTA note → excluded / sensitive list, MFN rate maintained
    return dd_rate, "Hors démantèlement ZLECAf — taux NPF maintenu (liste d'exclusion)", advantages


def build_taxes_detail(dd_rate, vat_rate, table_tax_rate):
    detail = []
    if dd_rate is not None:
        detail.append(
            {"tax": "D.D", "rate": dd_rate, "observation": "Droit de Douane (ضريبة الوارد)"}
        )
    if vat_rate is not None:
        detail.append(
            {
                "tax": "T.V.A",
                "rate": vat_rate,
                "observation": "Taxe sur la Valeur Ajoutée (ضريبة القيمة المضافة)",
            }
        )
    if table_tax_rate:
        detail.append(
            {
                "tax": "T.J",
                "rate": table_tax_rate,
                "observation": "Taxe de Table / Droit de consommation (ضريبة الجدول)",
            }
        )
    return detail


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw", required=True, help="Path to egy_raw_v2.json")
    parser.add_argument("--out", default=OUT_FILE)
    args = parser.parse_args()

    with open(args.raw, encoding="utf-8") as f:
        raw = json.load(f)
    positions = raw["positions"]
    hs6_meta = build_hs6_meta(OLD_EGY)

    # Group HS10 positions by HS6
    by_hs6 = collections.OrderedDict()
    for p in positions:
        code = p["code"]
        hs6 = code[:6]
        by_hs6.setdefault(hs6, []).append(p)

    tariff_lines = []
    total_sub = 0
    dd_all = []
    afcfta_lines = 0

    for hs6, children in by_hs6.items():
        meta = hs6_meta.get(hs6, {})
        chapter = hs6[:2]

        # HS6 headline DD = most common child DD (most representative)
        child_dds = [c["dd_rate"] for c in children if c.get("dd_rate") is not None]
        if child_dds:
            dd_rate = collections.Counter(child_dds).most_common(1)[0][0]
        else:
            dd_rate = 0.0
        dd_all.append(dd_rate)

        # HS6 headline VAT = most common child VAT
        child_vats = [c["vat_rate"] for c in children if c.get("vat_rate") is not None]
        vat_rate = collections.Counter(child_vats).most_common(1)[0][0] if child_vats else 14.0

        # HS6 table tax = max among children (only present on some)
        child_tt = [c["table_tax_rate"] for c in children if c.get("table_tax_rate")]
        table_tax_rate = max(child_tt) if child_tt else 0.0

        # Aggregate instructions across children for headline AfCFTA treatment
        all_instr = set()
        for c in children:
            all_instr.update(c.get("instructions", []))
        zlecaf_rate, zlecaf_source, advantages = afcfta_advantages(dd_rate, all_instr)
        if advantages:
            afcfta_lines += 1

        # Arabic designation: take the shortest non-empty (HS6 parent-ish)
        ar_descs = [
            c.get("description_ar", "").strip() for c in children if c.get("description_ar")
        ]
        description_ar = min(ar_descs, key=len) if ar_descs else ""

        taxes_detail = build_taxes_detail(dd_rate, vat_rate, table_tax_rate)
        total_taxes_pct = round(dd_rate + vat_rate + table_tax_rate, 3)
        zlecaf_total = round(zlecaf_rate + vat_rate + table_tax_rate, 3)

        # Build sub_positions (HS10) with REAL per-line fiscal data
        sub_positions = []
        for c in sorted(children, key=lambda x: x["code"]):
            c_instr = c.get("instructions", [])
            c_dd = c.get("dd_rate")
            c_zlecaf, _, _ = afcfta_advantages(c_dd, c_instr)
            # Canonical sub_position is kept lean: the AfCFTA treatment is already
            # captured in zlecaf_rate / fiscal_advantages. The verbatim official
            # Arabic instructions (source evidence) are preserved once, in the
            # crawled evidence file (data/crawled/EGY_tariffs.json).
            sub_positions.append(
                {
                    "code": c["code"],
                    "digits": 10,
                    "dd": c_dd if c_dd is not None else dd_rate,
                    "zlecaf_rate": c_zlecaf,
                    "vat_rate": c.get("vat_rate"),
                    "table_tax_rate": c.get("table_tax_rate"),
                    "description_ar": c.get("description_ar", ""),
                    "dd_rate_raw": c.get("dd_rate_raw", ""),
                    "vat_rate_raw": c.get("vat_rate_raw", ""),
                    "source": "Egyptian Customs Authority (customs.gov.eg) — Tarif officiel",
                }
            )
        total_sub += len(sub_positions)

        sensitivity = "sensible" if (not advantages or zlecaf_rate > 0) else "normal"

        tariff_lines.append(
            {
                "hs6": hs6,
                "chapter": chapter,
                "description_fr": meta.get("description_fr", ""),
                "description_en": meta.get("description_en", ""),
                "description_ar": description_ar,
                "category": meta.get("category", "general"),
                "unit": meta.get("unit", "KG"),
                "sensitivity": sensitivity,
                "dd_rate": dd_rate,
                "dd_source": "Tarif douanier officiel EGY (customs.gov.eg)",
                "zlecaf_rate": zlecaf_rate,
                "zlecaf_source": zlecaf_source,
                "vat_rate": vat_rate,
                "other_taxes_rate": table_tax_rate,
                "taxes_detail": taxes_detail,
                "total_taxes_pct": total_taxes_pct,
                "fiscal_advantages": advantages,
                "administrative_formalities": meta.get("administrative_formalities", []),
                "total_import_taxes": total_taxes_pct,
                "zlecaf_total_taxes": zlecaf_total,
                "sub_positions": sub_positions,
                "has_sub_positions": len(sub_positions) > 0,
                "sub_position_count": len(sub_positions),
            }
        )

    dd_arr = [d for d in dd_all if d is not None]
    out = {
        "country_code": "EGY",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "data_format": "canonical_hs6_with_sub_positions",
        "source": "Egyptian Customs Authority — Moslaha El Gamareg (customs.gov.eg/Services/Tarif)",
        "source_url": "https://customs.gov.eg/Services/Tarif",
        "source_quality": "crawled_authentic",
        "legal_reference": "Tarif douanier égyptien (Décret présidentiel 419/2018 et mises à jour) ; notes AfCFTA ر6790/ر6791",
        "nomenclature": "HS 2022 (HS10 national)",
        "crawled_at": raw.get("crawled_at"),
        "summary": {
            "total_tariff_lines": len(tariff_lines),
            "total_sub_positions": total_sub,
            "total_positions": len(tariff_lines) + total_sub,
            "lines_with_afcfta_schedule": afcfta_lines,
            "vat_rate_standard_pct": 14.0,
            # Legacy keys consumed by tariff_data_service / calculator route
            "vat_rate_pct": 14.0,
            "other_taxes_pct": 0.0,
            "other_taxes_detail": {},
            "lines_with_sub_positions": sum(1 for l in tariff_lines if l["sub_positions"]),
            "vat_source": "ETA Égypte (ضريبة القيمة المضافة)",
            "dd_rate_range": {
                "min": min(dd_arr),
                "max": max(dd_arr),
                "avg": round(sum(dd_arr) / len(dd_arr), 2),
            },
            "chapters_covered": len({l["chapter"] for l in tariff_lines}),
            "has_detailed_taxes": True,
            "has_real_per_position_rates": True,
            "afcfta_dismantling": {
                "group_a": "100% DD reduction (note ر6790) → 0%",
                "group_b": "60% DD reduction (note ر6791) → DD × 0.4",
            },
        },
        "tariff_lines": tariff_lines,
    }

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, separators=(",", ":"))
    print(f"✓ Wrote {args.out}")

    # ── Mirror to data/tariffs/ (consumed by tariff_data_service) ──────────────
    tariffs_out = os.path.join(DATA_DIR, "tariffs", "EGY_tariffs.json")
    with open(tariffs_out, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, separators=(",", ":"))
    print(f"✓ Wrote {tariffs_out}")

    # ── Per-position crawled index (consumed as Priority-1 by authentic svc) ───
    # Built directly from raw positions so the verbatim official Arabic
    # instructions (source evidence) are preserved here, once.
    crawled_subs = []
    for p in sorted(positions, key=lambda x: x["code"]):
        code = p["code"]
        hs6 = code[:6]
        meta = hs6_meta.get(hs6, {})
        c_dd = p.get("dd_rate")
        c_instr = p.get("instructions", [])
        c_zlecaf, _, _ = afcfta_advantages(c_dd, c_instr)
        taxes = {
            "DD": {
                "name": "Droit de Douane",
                "rate": c_dd if c_dd is not None else 0.0,
                "raw": p.get("dd_rate_raw", ""),
                "source": "customs.gov.eg",
            }
        }
        if p.get("vat_rate") is not None:
            taxes["TVA"] = {
                "name": "TVA",
                "rate": p["vat_rate"],
                "raw": p.get("vat_rate_raw", ""),
                "source": "customs.gov.eg",
            }
        if p.get("table_tax_rate"):
            taxes["TJ"] = {
                "name": "Taxe de Table (ضريبة الجدول)",
                "rate": p["table_tax_rate"],
                "source": "customs.gov.eg",
            }
        crawled_subs.append(
            {
                "hs_code": code,
                "chapter": hs6[:2],
                "heading": hs6[:4],
                "name": meta.get("description_fr", ""),
                "description": meta.get("description_fr", ""),
                "name_ar": p.get("description_ar", ""),
                "taxes": taxes,
                "zlecaf_rate": c_zlecaf,
                "official_instructions": c_instr,
                "source": "customs.gov.eg",
            }
        )
    crawled_out = os.path.join(DATA_DIR, "crawled", "EGY_tariffs.json")
    crawled_doc = {
        "country": "EGY",
        "country_name": "Egypt",
        "source": "Egyptian Customs Authority (customs.gov.eg/Services/Tarif)",
        "source_url": "https://customs.gov.eg/Services/Tarif",
        "source_quality": "crawled_authentic",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "crawled_at": raw.get("crawled_at"),
        "stats": {"total_positions": len(crawled_subs), "hs_digits": 10},
        "sub_positions": crawled_subs,
    }
    with open(crawled_out, "w", encoding="utf-8") as f:
        json.dump(crawled_doc, f, ensure_ascii=False, separators=(",", ":"))
    print(f"✓ Wrote {crawled_out} ({len(crawled_subs)} per-position entries)")

    print(f"\n  HS6 tariff_lines : {len(tariff_lines)}")
    print(f"  HS10 sub_positions: {total_sub}")
    print(f"  Lines w/ AfCFTA schedule: {afcfta_lines}")
    print(f"  DD min/max/avg : {min(dd_arr)}/{max(dd_arr)}/{round(sum(dd_arr)/len(dd_arr),2)}")
    print(f"  Chapters       : {len({l['chapter'] for l in tariff_lines})}")


if __name__ == "__main__":
    main()
