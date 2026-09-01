#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_egy_tariffs_official.py

Fusionne les EGY_official_progress_*.json (crawl officiel customs.gov.eg
/Services/TrfDetails) en un fichier canonique + rapport de réconciliation
avec l'ancien fichier EGY_tariffs.json.

Règles (aucune extrapolation) :
  - taxes : verbatim arabe + taux numériques lus littéralement dans la chaîne
    publiée (ex. "ضريبة الوارد : 5%" -> 5.0 ; "صفر" -> 0.0). Rien d'autre.
  - instructions : verbatim, avec codes officiels (ر = préférences FTA /
    exonérations, غ = formalités administratives, ق = restrictions).
  - name_fr : uniquement si l'ancien crawl (juin 2026, même source officielle)
    contient le code — champ séparé "name_fr_from_previous_crawl".
"""
from __future__ import annotations

import glob
import hashlib
import json
import os
import re
import shutil
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = BACKEND_DIR.parent
CRAWLED_DIR = BACKEND_DIR / "data" / "crawled"
REPORTS_DIR = REPO_ROOT / "reports"

RATE_RE = re.compile(r"(\d+(?:[.,]\d+)?)\s*%")

TAX_CODE_MAPPING = {
    "ضريبة الوارد": "ID",
    "ضريبة قيمه مضافه": "VAT",
    "ضريبة الدمغة": "STAMP",
    "رسم دعم": "SUPPORT",
}


def norm_code(code: str) -> str:
    return code.replace("/", "").strip()


def parse_taxes_lines(taxes_verbatim: list[str]) -> list[dict]:
    """Parse ordonné des lignes de taxes publiées par la source.

    Structure de la source : une ligne sans ':' est un en-tête de régime
    (accord commercial, ex. « اتفاقيه الشراكه المصريه الاوربيه ») ; les lignes
    « LABEL : valeur » qui suivent s'appliquent sous CE régime. Les lignes qui
    précèdent tout en-tête sont les taux génériques. Rien n'est interprété :
    le texte arabe reste verbatim."""
    out: list[dict] = []
    regime = None
    for raw in taxes_verbatim or []:
        raw = raw.strip()
        if not raw:
            continue
        if ":" not in raw:
            regime = raw
            out.append(
                {
                    "label_ar": raw,
                    "code": None,
                    "raw": "",
                    "rate": None,
                    "rate_parsed": False,
                    "regime_ar": regime,
                    "kind": "regime_header",
                }
            )
            continue
        label = raw.split(":")[0].strip()
        value = raw.split(":", 1)[1].strip()
        code = None
        for ar, cd in TAX_CODE_MAPPING.items():
            if ar in label:
                code = cd
                break
        num = None
        m = RATE_RE.search(value)
        if m:
            num = float(m.group(1).replace(",", "."))
        elif "صفر" in value:
            num = 0.0
        out.append(
            {
                "label_ar": label,
                "code": code,
                "raw": value,
                "rate": num,
                "rate_parsed": num is not None,
                "regime_ar": regime,
                "kind": "tax",
            }
        )
    return out


def build_taxes_dict(taxes_parsed: list[dict]) -> dict:
    """Dict des taux GÉNÉRIQUES uniquement (aucun régime). En cas de libellé
    dupliqué générique (ex. TVA ad valorem + TVA minimum), la 2e/3e occurrence
    est conservée sous un suffixe _2/_3 — aucune donnée n'est écrasée."""
    out: dict = {}
    seen: dict[str, int] = {}
    for e in taxes_parsed:
        if e.get("kind") != "tax" or e.get("regime_ar"):
            continue
        key = e.get("code") or e["label_ar"]
        seen[key] = seen.get(key, 0) + 1
        if seen[key] > 1:
            key = f"{key}_{seen[key]}"
        out[key] = {
            "code": e.get("code"),
            "label_ar": e["label_ar"],
            "raw": e["raw"],
            "rate": e["rate"],
            "rate_parsed": e["rate_parsed"],
        }
    return out


def build_regime_rates(taxes_parsed: list[dict]) -> list[dict]:
    """Taux publiés SOUS un régime (accord) — conservés séparément du taux
    générique (l'ancien parseur les écrasait dans le dict)."""
    return [
        {
            "regime_ar": e["regime_ar"],
            "code": e.get("code"),
            "label_ar": e["label_ar"],
            "raw": e["raw"],
            "rate": e["rate"],
            "rate_parsed": e["rate_parsed"],
        }
        for e in taxes_parsed
        if e.get("kind") == "tax" and e.get("regime_ar")
    ]


def main() -> int:
    now = datetime.now(timezone.utc).isoformat()

    files = sorted(glob.glob(str(CRAWLED_DIR / "EGY_official_progress_*.json")))
    if not files:
        print("aucun fichier de progression EGY officiel")
        return 2
    positions = {}
    chapters_covered = set()
    for f in files:
        d = json.loads(Path(f).read_text(encoding="utf-8"))
        chapters_covered.add(d.get("chapter"))
        for row in d.get("data", []):
            code = norm_code(row.get("code", ""))
            if code:
                positions[code] = row
    print(f"{len(files)} chapitres, {len(positions)} positions officielles")

    old_path = CRAWLED_DIR / "EGY_tariffs.json"
    old = json.loads(old_path.read_text(encoding="utf-8"))
    old_by_code = {
        (p.get("hs_code") or "").replace("/", ""): p for p in old.get("sub_positions", [])
    }

    sub_positions = []
    stats = Counter()
    rate_diffs = []
    for code in sorted(positions):
        row = positions[code]
        taxes_verbatim = row.get("taxes_verbatim") or []
        # re-parse depuis le verbatim (source ordonnée faisant foi) ; le dict
        # `taxes` du crawl est un repli si le verbatim est absent
        if taxes_verbatim:
            taxes_parsed = parse_taxes_lines(taxes_verbatim)
            taxes = build_taxes_dict(taxes_parsed)
            regime_rates = build_regime_rates(taxes_parsed)
        else:
            taxes = row.get("taxes") or {}
            regime_rates = []
        if regime_rates:
            stats["with_regime_rates"] += 1
        old_line = old_by_code.get(code)

        dd = taxes.get("ID") or {}
        vat = taxes.get("VAT") or {}
        new_dd = dd.get("rate")
        new_vat = vat.get("rate")
        old_dd = (old_line.get("taxes") or {}).get("DD", {}).get("rate") if old_line else None
        old_vat = (old_line.get("taxes") or {}).get("TVA", {}).get("rate") if old_line else None
        if old_line and (new_dd != old_dd or new_vat != old_vat):
            stats["rate_diff_vs_previous"] += 1
            if len(rate_diffs) < 60:
                rate_diffs.append(
                    {
                        "code": code,
                        "old": {"dd": old_dd, "tva": old_vat},
                        "new": {"dd": new_dd, "tva": new_vat},
                        "taxes_verbatim": row.get("taxes_verbatim"),
                    }
                )

        instructions = row.get("instructions") or []
        codes_instr = row.get("instruction_codes") or []
        formalities = (
            [
                {
                    "code_verbatim": c,
                    "text_verbatim": t,
                    "kind": "administrative_instruction(غ)" if c.startswith("غ") else None,
                    "source": row.get("source"),
                }
                for c, t in zip(codes_instr, instructions)
                if c.startswith("غ")
            ]
            if len(codes_instr) == len(instructions)
            else []
        )
        fta_preferences = (
            [
                {
                    "code_verbatim": c,
                    "text_verbatim": t,
                    "kind": "customs_instruction(ر)",
                    "zlecaf": ("افريقية القارية" in t),
                }
                for c, t in zip(codes_instr, instructions)
                if c.startswith("ر")
            ]
            if len(codes_instr) == len(instructions)
            else []
        )

        line = {
            "hs_code": code,
            "code_official": row.get("number") or row.get("code"),
            "chapter": code[:2],
            "heading": code[:4],
            "desc_ar": row.get("short_desc_ar") or row.get("desc_ar"),
            "name_fr_from_previous_crawl": (old_line or {}).get("name"),
            "name_ar_from_previous_crawl": (old_line or {}).get("name_ar"),
            "taxes": taxes,
            "taxes_regimes": regime_rates,
            "taxes_verbatim_ar": row.get("taxes_verbatim"),
            "official_instructions": instructions,
            "official_instruction_codes": codes_instr,
            "formalities": formalities,
            "fta_preferences": fta_preferences,
            "zlecaf_instruction": next((t for t in fta_preferences if t["zlecaf"]), None),
            "data_status": row.get("data_status", "OK"),
            "source": "customs.gov.eg — Autorité Égyptienne des Douanes (Services/Tarif + TrfDetails)",
            "source_url": row.get("source_url"),
            "detail_endpoint": row.get("detail_endpoint"),
            "source_quality": "crawled_authentic" if row.get("data_status") == "OK" else "PARTIAL",
            "date_consulted": (row.get("extracted_at") or now)[:10],
        }
        if instructions:
            stats["with_instructions"] += 1
        if fta_preferences:
            stats["with_fta_preferences"] += 1
        if formalities:
            stats["with_formalities"] += 1
        if any(f["zlecaf"] for f in fta_preferences):
            stats["with_zlecaf_instruction"] += 1
        if not dd and not vat:
            stats["missing_taxes"] += 1
        stats["total"] += 1
        sub_positions.append(line)

    # positions de l'ancien fichier absentes du crawl officiel
    legacy = []
    for code, old_line in old_by_code.items():
        if code not in positions:
            l = dict(old_line)
            l["source_quality"] = "previous_crawl_unverified_today"
            l["data_status"] = "REVIEW_REQUIRED"
            legacy.append(l)
            stats["legacy_not_in_official_crawl"] += 1

    doc = {
        "country": "EGY",
        "country_name": "Égypte",
        "source": "customs.gov.eg — Autorité Égyptienne des Douanes",
        "source_url": "https://www.customs.gov.eg/Services/Tarif",
        "detail_endpoint": "POST https://www.customs.gov.eg/Services/TrfDetails?trfNumber={code}&trfType=1",
        "source_quality": "crawled_authentic",
        "extracted_at": now,
        "built_by": "backend/scripts/build_egy_tariffs_official.py",
        "policy": (
            "Crawl officiel : taxes et instructions verbatim (arabe), taux lus littéralement "
            "dans les chaînes publiées. Les codes ر = instructions tarifaires/préférences "
            "(ZLECAf groupes أ/ب inclus), غ = formalités administratives, ق = restrictions. "
            "Les libellés français proviennent du crawl précédent (même autorité) et sont "
            "identifiés comme tels."
        ),
        "stats": dict(stats),
        "chapters_covered": sorted(chapters_covered),
        "sub_positions": sub_positions + legacy,
    }

    backup_dir = REPO_ROOT / "data" / "archive" / "crawled_backup"
    backup_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup_path = backup_dir / f"EGY_tariffs_{ts}.json"
    shutil.copy2(old_path, backup_path)

    tmp = old_path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, old_path)

    report = {
        "date": now,
        "stats": dict(stats),
        "rate_diffs_sample": rate_diffs,
        "backup": str(backup_path.relative_to(REPO_ROOT)),
        "chapters_covered": sorted(chapters_covered),
    }
    REPORTS_DIR.mkdir(exist_ok=True)
    (REPORTS_DIR / "EGY_REBUILD_RECONCILIATION.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(dict(stats), ensure_ascii=False, indent=1))
    print(f"backup: {backup_path.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
