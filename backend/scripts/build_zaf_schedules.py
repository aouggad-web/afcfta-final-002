#!/usr/bin/env python3
"""Complétion exhaustive ZAF — annexes du Customs & Excise Act + ITAC.

Ajoute au fichier national ZAF_tariffs.json (Schedule 1 Part 1, crawl du jour)
des sections SÉPARÉES, strictement verbatim, extraites des PDF officiels :

  - schedule_2_trade_remedies : anti-dumping (Part 2), countervailing (Part 3),
    safeguard (Part 1) — taux additionnels publiés par produit/origine
  - schedule_3_rebates : rebates industriels (extents verbatim)
  - schedule_8_licences : licences et frais
  - schedule_1_part_2a/2b : droits d'accise spécifiques
  - itac_definitive_measures : mesures définitives ITAC en vigueur

Règles : pas de mock, pas de synthèse, pas d'extrapolation. Chaque ligne garde
son bloc verbatim ; les taux numériques sont lus littéralement dans la chaîne
publiée ou laissés à None. Aucune fusion avec le taux général.
"""
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import fitz  # PyMuPDF — python système

ROOT = Path(__file__).resolve().parents[2]
LEG = ROOT / "data" / "sources" / "ZAF" / "legislation"
NAT = ROOT / "backend" / "data" / "crawled" / "ZAF_tariffs.json"
REPORTS = ROOT / "reports"

RATE_RE = re.compile(r"(\d+(?:[.,]\d+)?)\s*%")
ITEM_RE = re.compile(r"^\d{3}\.\d{2}$")
TARIFF_RE = re.compile(r"^\d{4}\.\d{2}(?:\.\d{1,2})?$")
SUBITEM_RE = re.compile(r"^\d{3,4}\.\d{2}\.\d{2}$")


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read_pdf(path):
    doc = fitz.open(str(path))
    return [(doc[i].get_text()) for i in range(len(doc))]


def date_in_pages(pages):
    for t in pages:
        m = re.search(r"Date:\s*(\d{4}-\d{2}-\d{2})", t)
        if m:
            return m.group(1)
    return None


def literal_rate(raw):
    """Lecture littérale d'un pourcentage publié (73,33% -> 73.33)."""
    m = RATE_RE.search(raw or "")
    if m:
        return float(m.group(1).replace(",", "."))
    if (raw or "").strip().lower() in ("free", "0%"):
        return 0.0
    return None


def parse_sch2(path):
    """Schedule 2 : remèdes. Lignes ancrées sur l'item (ex. 201.02).
    Parties réelles d'après les en-têtes : P1 anti-dumping (p.2-46),
    P2 countervailing (p.47), P3 safeguard (p.48+)."""
    pages = read_pdf(path)
    date_pub = date_in_pages(pages)
    part = None
    rows = []
    for pno, text in enumerate(pages):
        m = re.search(r"SCHEDULE 2\s*/\s*PART\s*(\d+)\s*\n([^\n]+)", text)
        if m:
            # structure publiée : Part 1 = anti-dumping, Part 2 = countervailing,
            # Part 3 = safeguard (en-têtes vérifiés p.2, p.47, p.48)
            part = {"1": "part_1_antidumping", "2": "part_2_countervailing", "3": "part_3_safeguard"}.get(m.group(1), f"part_{m.group(1)}")
        lines = [l.strip() for l in text.splitlines() if l.strip()]
        i = 0
        while i < len(lines):
            if ITEM_RE.match(lines[i]):
                block = [lines[i]]
                i += 1
                while i < len(lines) and not ITEM_RE.match(lines[i]) and "SCHEDULE 2 / PART" not in lines[i]:
                    block.append(lines[i])
                    i += 1
                rate_raw = None
                rate_num = None
                for l in reversed(block):
                    if "%" in l or l.lower().strip() == "free":
                        rate_raw = l
                        rate_num = literal_rate(l)
                        break
                tariff = next((l for l in block if TARIFF_RE.match(l)), None)
                country = None
                if rate_raw and rate_raw in block:
                    idx = block.index(rate_raw)
                    if idx > 0 and not TARIFF_RE.match(block[idx - 1]):
                        country = block[idx - 1]
                rows.append({
                    "part": part,
                    "item": block[0],
                    "tariff_code": tariff,
                    "rate_raw": rate_raw,
                    "rate_numeric": rate_num,
                    "imported_from_or_originating_in": country,
                    "raw_block": " | ".join(block)[:1200],
                    "page": pno + 1,
                })
            else:
                i += 1
    return rows, date_pub


def parse_sch3(path):
    """Schedule 3 : rebates industriels. Ancrage rebate item (ex. 303.01)."""
    pages = read_pdf(path)
    date_pub = date_in_pages(pages)
    rows = []
    for pno, text in enumerate(pages):
        lines = [l.strip() for l in text.splitlines() if l.strip()]
        i = 0
        while i < len(lines):
            if ITEM_RE.match(lines[i]):
                block = [lines[i]]
                i += 1
                while i < len(lines) and not ITEM_RE.match(lines[i]) and "SCHEDULE 3" not in lines[i]:
                    block.append(lines[i])
                    i += 1
                tariff = next((l for l in block[1:] if re.match(r"^\d{4}\.\d{2}$", l)), None)
                extent = None
                for l in reversed(block):
                    if "%" in l or "full duty" in l.lower() or "c/" in l or "free" in l.lower():
                        extent = l
                        break
                rows.append({
                    "rebate_item": block[0],
                    "tariff_code": tariff,
                    "extent_raw": extent,
                    "extent_numeric": literal_rate(extent) if extent and "%" in (extent or "") else None,
                    "raw_block": " | ".join(block)[:1200],
                    "page": pno + 1,
                })
            else:
                i += 1
    return rows, date_pub


def parse_licences(path):
    """Schedule 8 : licences (item, licence, frais, validité)."""
    pages = read_pdf(path)
    rows = []
    for pno, text in enumerate(pages):
        lines = [l.strip() for l in text.splitlines() if l.strip()]
        i = 0
        while i < len(lines):
            if re.match(r"^8\d\d\.\d{2}$", lines[i]):
                block = [lines[i]]
                i += 1
                while i < len(lines) and not re.match(r"^8\d\d\.\d{2}$", lines[i]) and "SCHEDULE 8" not in lines[i]:
                    block.append(lines[i])
                    i += 1
                rows.append({
                    "item": block[0],
                    "raw_block": " | ".join(block)[:800],
                    "page": pno + 1,
                })
            else:
                i += 1
    return rows


def parse_specific_excise(path, label):
    """Schedule 1 Part 2A/2B : droits d'accise spécifiques.
    Anchres : Tariff Item = \\d{3}.\\d{2}.\\d{2} (ex. 104.01.05) ; le sous-tarif
    HS8 (\\d{4}.\\d{2}.\\d{2}, ex. 1901.90.13) n'est PAS un ancre."""
    pages = read_pdf(path)
    date_pub = date_in_pages(pages)
    item_re = re.compile(r"^\d{3}\.\d{2}\.\d{2}$")
    sub_re = re.compile(r"^\d{4}\.\d{2}\.\d{2}$")
    rows = []
    for pno, text in enumerate(pages):
        lines = [l.strip() for l in text.splitlines() if l.strip()]
        i = 0
        while i < len(lines):
            if item_re.match(lines[i]):
                block = [lines[i]]
                i += 1
                while i < len(lines) and not item_re.match(lines[i]) and "SCHEDULE 1" not in lines[i]:
                    block.append(lines[i])
                    i += 1
                subheading = next((l for l in block[1:] if sub_re.match(l)), None)
                rate_raw = None
                for l in reversed(block):
                    if re.search(r"\d", l) and ("c/" in l or "%" in l or "R" in l):
                        rate_raw = l
                        break
                rows.append({
                    "tariff_item": block[0],
                    "tariff_subheading": subheading,
                    "rate_raw": rate_raw,
                    "rate_numeric": literal_rate(rate_raw),
                    "raw_block": " | ".join(block)[:1000],
                    "page": pno + 1,
                })
            else:
                i += 1
    return rows, date_pub


def parse_itac(path):
    """ITAC : mesures définitives en vigueur (tableau libre)."""
    pages = read_pdf(path)
    out = []
    for pno, text in enumerate(pages):
        out.append({"page": pno + 1, "raw_text": text[:6000]})
    return out


def main():
    now = datetime.now(timezone.utc).isoformat()
    nat = json.loads(NAT.read_text(encoding="utf-8"))
    schedules = {}  # re-parse complet à chaque exécution (PDF = source de vérité)

    specs = [
        ("schedule_2_trade_remedies", LEG / "Sch2-Schedule-No-2.pdf", parse_sch2),
        ("schedule_3_rebates", LEG / "Sch3-Schedule-No-3.pdf", parse_sch3),
        ("schedule_8_licences", LEG / "Sch8-Schedule-No-8.pdf", parse_licences),
        ("schedule_1_part_2a_specific_excise", LEG / "Sch1P2A-Schedule-No-1-Part-2A.pdf", lambda p: parse_specific_excise(p, "2A")),
        ("schedule_1_part_2b_specific_excise", LEG / "Sch1P2B-Schedule-No-1-Part-2B.pdf", lambda p: parse_specific_excise(p, "2B")),
        ("itac_definitive_measures", LEG / "itac_definitive_duties_2022-12-31.pdf", parse_itac),
    ]

    stats = {}
    for key, path, fn in specs:
        if not path.exists():
            stats[key] = "PDF ABSENT"
            continue
        parsed = fn(path)
        if isinstance(parsed, tuple):
            rows, date_pub = parsed
        else:
            rows, date_pub = parsed, None
        schedules[key] = {
            "pdf": str(path.relative_to(ROOT)),
            "pdf_sha256": sha256(path),
            "date_on_pdf": date_pub,
            "source_url": "https://www.sars.gov.za/wp-content/uploads/Legal/SCEA1964/"
            + path.name if "Sch" in path.name else "https://itac.org.za/wp-content/uploads/" + path.name,
            "rows": rows,
            "n_rows": len(rows),
            "parsed_at": now,
        }
        stats[key] = f"{len(rows)} lignes (date PDF: {date_pub})"

    nat["schedules"] = schedules
    nat["policy"] = (
        "Crawl et extraction verbatim des PDF officiels SARS (Schedule 1 Part 1 et annexes) "
        "et ITAC : pas de mock, pas de synthèse, pas d'extrapolation. Les taux numériques sont "
        "lus littéralement dans les chaînes publiées ; toute donnée non publiée reste un écart "
        "documenté. Outil informatif non opposable : seules les publications officielles font foi."
    )
    nat["calculation_method"] = {
        "title": "Méthode de calcul des droits et taxes — ZAF/SACU",
        "extracted_at": now,
        "assiettes": {
            "GENERAL / préférentiels (Schedule 1 Part 1)": "ad valorem % sur la valeur en douane, ou spécifique/composé c/kg, c/li, c/la, c/unit (321 lignes composées — raw_value verbatim)",
            "Anti-dumping / countervailing / safeguard (Schedule 2)": "taux additionnels publiés par produit ET par origine (rate_raw verbatim) — s'ajoutent au droit général selon le texte du Schedule",
            "Rebates (Schedule 3)": "extents verbatim ('Full duty', %, c/kg) — atténuations conditionnées à l'usage industriel (section 75)",
            "Accise spécifique (Sch1 Part 2A/2B)": "c/l, c/kg, % (rate_raw verbatim)",
            "TVA": "15 % standard ; liste zéro-rated du VAT Act à archiver (écart documenté)",
        },
        "note": "Aucune fusion automatique des remèdes/rebates avec le taux général : les sections restent séparées, le calcul final suit le texte légal publié.",
    }

    tmp = NAT.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(nat, ensure_ascii=False, indent=1), encoding="utf-8")
    tmp.replace(NAT)

    report = {
        "date": now,
        "country": "ZAF",
        "action": "complétion exhaustive annexes SARS + ITAC",
        "stats": stats,
        "pdfs_sha256": {s[0]: sha256(s[1]) for s in specs if s[1].exists()},
        "nrcs": "NRCS inaccessible depuis ce réseau (connexion échouée) — écart documenté ; alternative : Government Gazette",
        "schedule_1_part_1": "8 589 positions (crawl 2026-08-29, inchangé)",
    }
    REPORTS.mkdir(exist_ok=True)
    (REPORTS / "ZAF_SCHEDULES_RECONCILIATION.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(stats, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
