#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_dza_tariffs_authentic_v2.py

Reconstruit backend/data/crawled/DZA_tariffs.json à partir des données de crawl
conformepro.dz UNIQUEMENT (DZA_progress_*.json). Aucun taux ETL, aucune
estimation, aucune extrapolation.

Différences avec build_dza_tariffs_complete.py (ancien pipeline) :
  - L'ancien pipeline appliquait un ETL (etl.country_taxes_algeria) pour les
    chapitres non crawlés : taux génériques DD 15% / TVA 19% non vérifiés.
    CE script refuse toute donnée non crawlée : les positions absentes de la
    source sont conservées depuis l'ancien fichier MAIS marquées
    source_quality = "etl_legacy_unverified" + data_status = "REVIEW_REQUIRED".
  - Chaque ligne porte sa provenance complète : source_url, crawled_at,
    date_consulted.
  - Les formalités sont rapprochées de la liste officielle des F.A.P (Tarif
    d'usage DGD) — rapprochement documenté, texte conservé verbatim.
  - Les dispositions LF 2026 (JO n°88 du 31/12/2025) touchant des
    sous-positions précises sont attachées sous "lf2026_provisions" (verbatim,
    aucune modification de taux).
"""
from __future__ import annotations

import glob
import hashlib
import json
import os
import shutil
import sys
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = BACKEND_DIR.parent
CRAWLED_DIR = BACKEND_DIR / "data" / "crawled"
SOURCES_DIR = REPO_ROOT / "data" / "sources" / "DZA" / "legislation"
REPORTS_DIR = REPO_ROOT / "reports"

SOURCE_NAME = "conformepro.dz (données douane.gov.dz)"
SOURCE_ROOT_URL = "https://conformepro.dz/resources/tarif-douanier"
LEGAL_REFS_BASE = [
    {
        "ref": "Loi n° 79-07 du 21 juillet 1979 portant code des douanes, modifiée et complétée",
        "doc": "data/sources/DZA/legislation/code_douanes_79-07.pdf",
    },
    {
        "ref": "Tarif Douanier d'usage — DGD, Direction de la Fiscalité et des Bases de Taxation (édition LF 2020)",
        "doc": "data/sources/DZA/legislation/tarif_d_usage_2020.pdf",
    },
]

# Rapprochement code court données crawlées ↔ nomenclature officielle DGD
# (Tarif d'usage 2020, page 2). Uniquement quand le libellé officiel existe.
TAX_CODE_OFFICIAL_MATCH = {
    "DD": {
        "official_code": "D.D",
        "official_label": "Droits de Douane",
        "status": "MATCHED_DGD_LIST",
    },
    "TVA": {
        "official_code": "T.V.A",
        "official_label": "Taxe sur la Valeur Ajoutée",
        "status": "MATCHED_DGD_LIST",
    },
    "DAPS": {
        "official_code": "D.A.P.S",
        "official_label": "Droit Additionnel Provisoire de Sauvegarde",
        "status": "MATCHED_DGD_LIST",
    },
    "TIC": {
        "official_code": "T.I.C",
        "official_label": "Taxe Intérieure de Consommation",
        "status": "MATCHED_DGD_LIST",
    },
    "PRCT": {"official_code": None, "official_label": None, "status": "UNVERIFIED_LABEL"},
    "TCS": {"official_code": None, "official_label": None, "status": "UNVERIFIED_LABEL"},
}


def _norm(s: str) -> str:
    s = unicodedata.normalize("NFD", (s or "").lower())
    return "".join(c for c in s if unicodedata.category(c) != "Mn").strip()


def load_progress_positions() -> tuple[dict, dict]:
    """Charge tous les DZA_progress_*.json; déduplique par hs_code (dernier crawl gagne)."""
    pattern = str(CRAWLED_DIR / "DZA_progress_*.json")
    files = sorted(glob.glob(pattern), key=lambda p: int(p.rsplit("_", 1)[-1].split(".")[0]))
    index: dict[str, dict] = {}
    dup_count = 0
    for path in files:
        with open(path, encoding="utf-8") as f:
            d = json.load(f)
        for item in d.get("data", []):
            code = (item.get("hs_code") or item.get("raw_code") or "").replace(".", "").strip()
            if not code:
                continue
            if code in index:
                dup_count += 1
            item = dict(item)
            item["_progress_file"] = os.path.basename(path)
            item["_crawled_at"] = d.get("extracted_at")
            index[code] = item
    return index, {
        "progress_files": len(files),
        "unique_positions": len(index),
        "duplicates_overwritten": dup_count,
    }


def load_official_ref_files() -> tuple[dict, dict, dict]:
    fap_doc = json.loads((SOURCES_DIR / "dgd_tax_codes_and_fap.json").read_text(encoding="utf-8"))
    lf2026 = (
        json.loads((SOURCES_DIR / "legislation_lf2026.json").read_text(encoding="utf-8"))
        if (SOURCES_DIR / "legislation_lf2026.json").exists()
        else json.loads((SOURCES_DIR / "lf2026_customs_articles.json").read_text(encoding="utf-8"))
    )
    # index LF2026 par code numérique
    lf_index: dict[str, dict] = {}
    for art in lf2026.get("articles", []):
        for sp in art.get("sous_positions", []):
            code = sp.replace(".", "").replace(" ", "").lower()
            ex = code.startswith("ex")
            code = code[2:] if ex else code
            entry = lf_index.setdefault(code, {"articles": [], "partial": False})
            entry["articles"].append(art["article"])
            entry["partial"] = entry["partial"] or ex
    return fap_doc, lf2026, lf_index


def map_formalities(formalities: list[str], fap_list: dict) -> list:
    """Rapproche chaque formalité crawlée (verbatim) de la liste officielle F.A.P."""
    out = []
    fap_norm = {_norm(v.split("(")[0]): k for k, v in fap_list.items()}
    fap_norm2 = {_norm(k): k for k in fap_list}
    for raw in formalities:
        entry: dict = {"text_verbatim": raw, "source": SOURCE_NAME}
        base = raw.split("(")[0].strip()
        key = fap_norm.get(_norm(base)) or fap_norm2.get(_norm(raw))
        if key:
            entry.update(
                {
                    "fap_code": key,
                    "fap_official_label": fap_list[key],
                    "match_status": "MATCHED_DGD_FAP_LIST",
                }
            )
        else:
            entry["match_status"] = "UNMATCHED_VERBATIM"
        out.append(entry)
    return out


def build_tax_entry(code: str, info: dict) -> dict:
    entry = {
        "code": code,
        "label_published": info.get("name", code),
        "rate": info.get("rate"),
        "raw": info.get("raw"),
        "source": SOURCE_NAME,
        "source_root_url": SOURCE_ROOT_URL,
    }
    m = TAX_CODE_OFFICIAL_MATCH.get(code)
    if m:
        entry["official_dgd_code"] = m["official_code"]
        entry["official_dgd_label"] = m["official_label"]
        entry["label_verification"] = m["status"]
    else:
        entry["label_verification"] = "UNVERIFIED_LABEL"
    return entry


def main() -> int:
    now = datetime.now(timezone.utc).isoformat()

    old_path = CRAWLED_DIR / "DZA_tariffs.json"
    if not old_path.exists():
        print("Fichier existant introuvable:", old_path)
        return 2
    old = json.loads(old_path.read_text(encoding="utf-8"))
    old_by_code = {}
    for p in old.get("sub_positions", []):
        old_by_code[(p.get("hs_code") or p.get("raw_code") or "").replace(".", "")] = p

    progress_index, progress_stats = load_progress_positions()
    fap_doc, lf2026, lf_index = load_official_ref_files()
    fap_list = fap_doc["formalites_administratives_particulieres"]

    sub_positions = []
    stats = {
        "total": 0,
        "crawled_authentic": 0,
        "legacy_unverified": 0,
        "formalities_present": 0,
        "advantages_present": 0,
        "lf2026_linked": 0,
        "rate_changes_vs_previous": 0,
        "missing_dd_crawled": 0,
    }
    rate_changes = []

    # 1) positions crawlées (authentiques)
    for code, item in progress_index.items():
        taxes = {}
        for tcode, tinfo in (item.get("taxes") or {}).items():
            if isinstance(tinfo, dict):
                taxes[tcode] = build_tax_entry(tcode, tinfo)
        if "DD" not in taxes and "DAPS" not in taxes:
            stats["missing_dd_crawled"] += 1

        # blocs de taxes non publiés par la source (constat factuel, ex. blé de
        # semence, vaccins : la page conformepro n'affiche aucun bloc DD/TVA)
        source_gaps = [t for t in ("DD", "TVA") if t not in taxes]

        old_line = old_by_code.get(code)
        advantages = item.get("advantages") or []
        formalities = item.get("formalities") or []

        lf_link = lf_index.get(code)
        lf_provisions = None
        if lf_link:
            stats["lf2026_linked"] += 1
            arts = [a for a in lf2026["articles"] if a["article"] in lf_link["articles"]]
            lf_provisions = {
                "articles": lf_link["articles"],
                "partial_coverage": lf_link["partial"],
                "document": lf2026["source_document"],
                "details": arts,
            }

        if old_line:
            old_tax = {
                k: v.get("rate")
                for k, v in (old_line.get("taxes") or {}).items()
                if isinstance(v, dict)
            }
            new_tax = {k: v.get("rate") for k, v in taxes.items()}
            if old_tax != new_tax:
                stats["rate_changes_vs_previous"] += 1
                if len(rate_changes) < 50:
                    rate_changes.append(
                        {
                            "hs_code": code,
                            "old": old_tax,
                            "new": new_tax,
                            "source_url": item.get("source_url"),
                        }
                    )

        line = {
            "raw_code": item.get("raw_code"),
            "hs_code": code,
            "display_code": item.get("display_code", ""),
            "heading": item.get("heading", ""),
            "chapter": item.get("chapter", ""),
            "section": item.get("section", ""),
            "name": item.get("name", ""),
            "description": item.get("description", ""),
            "designation_full": item.get("designation_full", item.get("description", "")),
            "taxes": taxes,
            "source_gaps": source_gaps,
            "advantages": advantages,
            "formalities": map_formalities(formalities, fap_list),
            "lf2026_provisions": lf_provisions,
            "legal_refs": LEGAL_REFS_BASE
            + (
                [
                    {
                        "ref": "Loi de finances pour 2026 — JO n° 88 du 31/12/2025, "
                        + ", ".join(lf_link["articles"]),
                        "doc": "data/sources/DZA/legislation/JO_2026-88_loi_finances_2026.pdf",
                    }
                ]
                if lf_provisions
                else []
            ),
            "source": SOURCE_NAME,
            "source_root_url": SOURCE_ROOT_URL,
            "source_url": item.get("source_url"),
            "crawled_at": item.get("_crawled_at"),
            "date_consulted": (item.get("_crawled_at") or "")[:10] or None,
            "source_quality": "crawled_authentic",
            "data_status": "OK",
        }
        if formalities:
            stats["formalities_present"] += 1
        if advantages:
            stats["advantages_present"] += 1
        stats["crawled_authentic"] += 1
        stats["total"] += 1
        sub_positions.append(line)

    # 2) positions de l'ancien fichier absentes du crawl (aucune invention)
    for code, old_line in old_by_code.items():
        if code in progress_index:
            continue
        line = dict(old_line)
        line["source_quality"] = "etl_legacy_unverified"
        line["data_status"] = "REVIEW_REQUIRED"
        line["review_reason"] = (
            "Ligne héritée de l'ancien pipeline (taux ETL génériques) : sous-position "
            "non retrouvée dans le crawl conformepro.dz de cette session. Aucun taux "
            "authentique disponible — ne pas présenter comme authentique."
        )
        sub_positions.append(line)
        stats["legacy_unverified"] += 1
        stats["total"] += 1

    sub_positions.sort(key=lambda p: p.get("hs_code") or "")

    doc = {
        "country": "DZA",
        "country_name": "Algérie",
        "source": SOURCE_NAME,
        "source_root_url": SOURCE_ROOT_URL,
        "source_quality": "crawled_authentic",
        "source_provenance": "national_crawl",
        "extracted_at": now,
        "built_by": "backend/scripts/build_dza_tariffs_authentic_v2.py",
        "policy": (
            "Données crawlées uniquement. Aucun taux estimé/ETL. Les libellés PRCT/TCS "
            "restent tels que publiés par la source (mapping non vérifié dans les textes "
            "officiels à ce stade). Les lignes non retrouvées dans le crawl sont marquées "
            "etl_legacy_unverified / REVIEW_REQUIRED."
        ),
        "legal_refs": LEGAL_REFS_BASE
        + [
            {
                "ref": "Loi de finances pour l'année 2026 — JO n° 88 du 31 décembre 2025",
                "doc": "data/sources/DZA/legislation/JO_2026-88_loi_finances_2026.pdf",
            },
            {
                "ref": "Nomenclature F.A.P — Tarif d'usage DGD (pages 1-2)",
                "doc": "data/sources/DZA/legislation/dgd_tax_codes_and_fap.json",
            },
        ],
        "stats": stats,
        "progress_stats": progress_stats,
        "sub_positions": sub_positions,
    }

    # backup de l'ancien fichier
    backup_dir = REPO_ROOT / "data" / "archive" / "crawled_backup"
    backup_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup_path = backup_dir / f"DZA_tariffs_{ts}.json"
    shutil.copy2(old_path, backup_path)

    out = old_path
    tmp = old_path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, out)

    old_sha = hashlib.sha256(backup_path.read_bytes()).hexdigest()
    new_sha = hashlib.sha256(out.read_bytes()).hexdigest()

    print(f"Backup ancien fichier : {backup_path} (sha256 {old_sha[:16]}...)")
    print(f"Nouveau fichier       : {out} (sha256 {new_sha[:16]}...)")
    print(json.dumps(stats, ensure_ascii=False, indent=2))
    print(f"Positions crawlées    : {stats['crawled_authentic']}")
    print(f"Positions legacy      : {stats['legacy_unverified']}")

    # rapport de réconciliation
    report = {
        "date": now,
        "backup_file": str(backup_path.relative_to(REPO_ROOT)),
        "backup_sha256": old_sha,
        "new_file": str(out.relative_to(REPO_ROOT)),
        "new_sha256": new_sha,
        "stats": stats,
        "progress_stats": progress_stats,
        "rate_changes_sample": rate_changes,
    }
    REPORTS_DIR.mkdir(exist_ok=True)
    (REPORTS_DIR / "DZA_REBUILD_RECONCILIATION.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"Rapport : {REPORTS_DIR / 'DZA_REBUILD_RECONCILIATION.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
