#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_dza_canonical_hs6_authentic.py

Régénère backend/data/DZA_tariffs.json (fichier canonique HS6, format canonical_v4)
EXCLUSIVEMENT depuis les sous-positions authentiques crawlées
(backend/data/crawled/DZA_tariffs.json, source_quality=crawled_authentic).

Règles (aucune extrapolation) :
  - dd_rate / vat_rate : valeur si univoque à l'HS6 ; None si hétérogène ou non
    publié (variants documentés dans dd_rate_variants / vat_rate_variants).
  - other_taxes_rate : somme PRCT+TCS+DAPS+TIC si univoque, sinon None.
  - total_taxes_pct : somme si toutes composantes univoques, sinon None.
  - zlecaf_rate : JAMAIS dérivé de cette source. conformepro.dz ne documente que
    l'exonération « -zale- » (Zone Arabe de Libre Échange), qui est un accord
    distinct de la ZLECAf. Assimiler les deux fabriquerait un taux ZLECAf
    (cf. PR #322/#324 qui ont retiré ces champs). L'avantage ZALE reste
    conservé verbatim dans fiscal_advantages.
  - fiscal_advantages / administrative_formalities : texte verbatim conservé ;
    rattachement au code F.A.P officiel quand la correspondance exacte existe.
"""
from __future__ import annotations

import json
import re
import shutil
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = BACKEND_DIR.parent
CRAWLED_PATH = BACKEND_DIR / "data" / "crawled" / "DZA_tariffs.json"
CANON_PATH = BACKEND_DIR / "data" / "DZA_tariffs.json"
FAP_JSON = REPO_ROOT / "data" / "sources" / "DZA" / "legislation" / "dgd_tax_codes_and_fap.json"
LF2026_JSON = (
    REPO_ROOT / "data" / "sources" / "DZA" / "legislation" / "lf2026_customs_articles.json"
)

DD_SOURCE = "Direction Générale des Douanes — Algérie (DGD) via conformepro.dz"
OTHER_TAX_CODES = ("PRCT", "TCS", "DAPS", "TIC")


def univoque(values: list) -> tuple:
    """(valeur, variants) : valeur si un seul taux distinct, sinon (None, variants)."""
    distinct = sorted({v for v in values if v is not None}, key=lambda x: (x is None, x))
    if not distinct:
        return None, []
    if len(distinct) == 1:
        return distinct[0], []
    return None, distinct


def main() -> int:
    now = datetime.now(timezone.utc).isoformat()

    crawled = json.loads(CRAWLED_PATH.read_text(encoding="utf-8"))
    fap_doc = json.loads(FAP_JSON.read_text(encoding="utf-8"))
    fap_list = fap_doc["formalites_administratives_particulieres"]
    lf2026 = json.loads(LF2026_JSON.read_text(encoding="utf-8"))
    lf_index = {}
    for art in lf2026.get("articles", []):
        for sp in art.get("sous_positions", []):
            code = sp.replace(".", "").replace(" ", "").lower()
            ex = code.startswith("ex")
            code = code[2:] if ex else code
            e = lf_index.setdefault(code, [])
            e.append(art["article"])

    subs = [
        p
        for p in crawled.get("sub_positions", [])
        if p.get("source_quality") == "crawled_authentic"
    ]
    by_hs6: dict[str, list] = defaultdict(list)
    for p in sorted(subs, key=lambda x: x.get("hs_code") or ""):
        by_hs6[p["hs_code"][:6]].append(p)

    tariff_lines = []
    for hs6, group in sorted(by_hs6.items()):
        first = group[0]
        dds = [(p.get("taxes") or {}).get("DD", {}).get("rate") for p in group]
        dd, dd_variants = univoque(dds)
        tvas = [(p.get("taxes") or {}).get("TVA", {}).get("rate") for p in group]
        vat, vat_variants = univoque(tvas)
        others, other_variants = {}, {}
        for code in OTHER_TAX_CODES:
            vals = [(p.get("taxes") or {}).get(code, {}).get("rate") for p in group]
            others[code], other_variants[code] = univoque(vals)
        others_sum = sum(v for v in others.values() if v is not None)
        others_complete = all(v is not None for v in others.values())

        # avantages : déduplication verbatim
        seen_adv = set()
        fiscal_advantages = []
        for p in group:
            for adv in p.get("advantages") or []:
                if adv in seen_adv:
                    continue
                seen_adv.add(adv)
                low = adv.lower()
                tax = "DD" if re.search(r"\bd\.?\s?d\b|droit", low) else None
                rate = 0.0 if "exo" in low else None
                # Aucun taux ZLECAf n'est dérivé ici : la source ne mentionne que
                # « -zale- » (Zone Arabe de Libre Échange), un accord distinct
                # de la ZLECAf per doctrine MISSION_TARIFS_AFRICAINS.md.
                # L'avantage reste conservé verbatim ci-dessous.
                fiscal_advantages.append(
                    {
                        "tax": tax,
                        "rate": rate,
                        "condition_fr": adv,
                        "condition_en": adv,
                    }
                )

        # formalités : déduplication verbatim + rattachement F.A.P exact
        seen_form = set()
        administrative_formalities = []
        for p in group:
            for f in p.get("formalities") or []:
                txt = f.get("text_verbatim") if isinstance(f, dict) else f
                if txt in seen_form:
                    continue
                seen_form.add(txt)
                administrative_formalities.append(
                    {
                        "code": f.get("fap_code") if isinstance(f, dict) else None,
                        "document_fr": txt,
                        "document_en": txt,
                        "fap_official_label": (
                            f.get("fap_official_label") if isinstance(f, dict) else None
                        ),
                    }
                )

        # taxes_detail (format canonical_v4)
        taxes_detail = []
        taxes_detail.append(
            {
                "tax": "DD",
                "rate": dd,
                "observation": (first.get("taxes") or {})
                .get("DD", {})
                .get("label_published", "DD"),
                "variants": dd_variants or None,
            }
        )
        taxes_detail.append(
            {
                "tax": "TVA",
                "rate": vat,
                "observation": (first.get("taxes") or {})
                .get("TVA", {})
                .get("label_published", "TVA"),
                "variants": vat_variants or None,
            }
        )
        for code in OTHER_TAX_CODES:
            if others.get(code) is None and not other_variants.get(code):
                continue
            taxes_detail.append(
                {
                    "tax": code,
                    "rate": others[code],
                    "observation": (first.get("taxes") or {})
                    .get(code, {})
                    .get("label_published", code),
                    "variants": other_variants.get(code) or None,
                }
            )

        total_taxes = None
        if dd is not None and vat is not None and others_complete:
            total_taxes = round(dd + vat + others_sum, 4)

        # provisions LF 2026 rattachées à l'HS6 (sous-positions exactes)
        lf_articles = sorted(
            {a for p in group if lf_index.get(p["hs_code"]) for a in lf_index[p["hs_code"]]}
        )

        line = {
            "hs6": hs6,
            "chapter": first.get("chapter", ""),
            "description_fr": first.get("designation_full")
            or first.get("description")
            or first.get("name")
            or "",
            "description_en": first.get("designation_full")
            or first.get("description")
            or first.get("name")
            or "",
            "category": None,
            "unit": None,
            "sensitivity": "normal",
            "dd_rate": dd,
            "dd_source": DD_SOURCE,
            "dd_rate_variants": dd_variants or None,
            "vat_rate": vat,
            "vat_rate_variants": vat_variants or None,
            "other_taxes_rate": others_sum if others_complete else None,
            "taxes_detail": taxes_detail,
            "total_taxes_pct": total_taxes,
            "lf2026_articles": lf_articles or None,
            "fiscal_advantages": fiscal_advantages,
            "administrative_formalities": administrative_formalities,
            "sub_positions": [
                {
                    "code": p["hs_code"],
                    "digits": 10,
                    "dd": (p.get("taxes") or {}).get("DD", {}).get("rate"),
                    "description_fr": p.get("designation_full")
                    or p.get("description")
                    or p.get("name")
                    or "",
                    "description_en": p.get("designation_full")
                    or p.get("description")
                    or p.get("name")
                    or "",
                    "source": DD_SOURCE,
                    "source_url": p.get("source_url"),
                    "lf2026_articles": (lf_index.get(p["hs_code"]) or None),
                }
                for p in group
            ],
        }
        tariff_lines.append(line)

    dd_known = [l["dd_rate"] for l in tariff_lines if l["dd_rate"] is not None]
    doc = {
        "country_code": "DZA",
        "generated_at": now,
        "data_format": "canonical_v4",
        "built_by": "backend/scripts/build_dza_canonical_hs6_authentic.py",
        "source": DD_SOURCE,
        "source_root_url": "https://conformepro.dz/resources/tarif-douanier",
        "source_quality": "crawled_authentic",
        "policy": (
            "Agrégation HS6 des sous-positions crawlées uniquement. Taux None = hétérogène "
            "entre sous-positions ou non publié par la source (variants listés). Aucun taux ETL. "
            "Aucun taux ZLECAf n'est dérivé : la source ne documente que l'exonération -zale- "
            "(Zone Arabe de Libre Échange), accord distinct de la ZLECAf (cf. PR #322/#324)."
        ),
        "summary": {
            "total_tariff_lines": len(tariff_lines),
            "total_sub_positions": len(subs),
            "chapters_covered": len({l["chapter"] for l in tariff_lines}),
            "lines_with_dd_rate": len(dd_known),
            "lines_dd_not_published": sum(1 for l in tariff_lines if l["dd_rate"] is None),
            "dd_rate_range": {
                "min": min(dd_known) if dd_known else None,
                "max": max(dd_known) if dd_known else None,
            },
            "has_detailed_taxes": True,
            "data_status": "CRAWLED_AUTHENTIC",
            "source_name": DD_SOURCE,
            "legal_refs": crawled.get("legal_refs", []),
        },
        "tariff_lines": tariff_lines,
    }

    backup_dir = REPO_ROOT / "data" / "archive" / "crawled_backup"
    backup_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup_path = backup_dir / f"DZA_canonical_hs6_{ts}.json"
    if CANON_PATH.exists():
        shutil.copy2(CANON_PATH, backup_path)

    tmp = CANON_PATH.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")
    import os

    os.replace(tmp, CANON_PATH)

    print(f"Backup ancien canonique : {backup_path}")
    print(json.dumps(doc["summary"], ensure_ascii=False, indent=1)[:900])
    return 0


if __name__ == "__main__":
    sys.exit(main())
