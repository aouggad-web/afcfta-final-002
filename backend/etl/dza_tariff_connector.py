#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DZA Tariff Connector (Crawler + Parser + Normalizer + QA + Export)
Target: douane.gov.dz SPIP tariff pages (sous_position HS10)
Outputs:
 - raw cache (HTML)
 - parsed JSONL
 - curated CSV + curated JSON
 - QA report

Usage examples:
  python dza_tariff_connector.py crawl --out ./data --max-pages 2000
  python dza_tariff_connector.py parse --out ./data
  python dza_tariff_connector.py build --out ./data

Dependencies:
  pip install requests beautifulsoup4 lxml pandas

Notes:
 - This script is designed to be resilient: rate limiting, retries, caching, heuristic parsing.
 - If the site blocks automated requests, add --user-agent and consider running from a stable network.
"""

from __future__ import annotations

import argparse
import dataclasses
import datetime as dt
import hashlib
import json
import os
import random
import re
import sys
import time
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Tuple
from urllib.parse import urljoin, urlparse, parse_qs

import requests
import pandas as pd
from bs4 import BeautifulSoup


BASE_URL = "https://www.douane.gov.dz/"
ENTRY_URL = "https://www.douane.gov.dz/spip.php?page=tarif_douanier"

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/122.0 Safari/537.36",
    "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.7",
}

# --- Normalization dictionaries (extend as needed) ---
TAX_CODE_MAP = {
    "D.D": ("customs_duty", "DD"),
    "DD": ("customs_duty", "DD"),
    "T.V.A": ("vat", "TVA"),
    "TVA": ("vat", "TVA"),
    "PRCT": ("levy", "PRCT"),
    "T.C.S": ("surcharge", "TCS"),
    "TCS": ("surcharge", "TCS"),
    "D.C.A": ("excise", "DCA"),
    "DCA": ("excise", "DCA"),
    "TICBT": ("excise", "TICBT"),
    "TICPV": ("excise", "TICPV"),
    "TAPT": ("excise", "TAPT"),
}

UNIT_CANON = {
    "HL": "HL",
    "L": "L",
    "KG": "KG",
    "PA": "PA",
    "U": "U",
}

# Heuristics: section labels used in pages
H_TAX_ADV = "Taxes Ad-Valorem"
H_TAX_SPEC = "Taxes spécifiques annexes"
H_ADVANTAGES = "Avantages fiscaux"
H_FORMALITIES = "Formalités Administratives Particulières"


# ----------------------------- utilities -----------------------------

def now_iso() -> str:
    return dt.datetime.now(dt.timezone(dt.timedelta(hours=1))).isoformat(timespec="seconds")


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="ignore")).hexdigest()


def safe_mkdir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def stable_filename_from_url(url: str) -> str:
    h = hashlib.md5(url.encode("utf-8")).hexdigest()
    return f"{h}.html"


def clean_text(s: str) -> str:
    s = re.sub(r"\s+", " ", s or "").strip()
    return s


def parse_float_fr(x: str) -> Optional[float]:
    if x is None:
        return None
    t = clean_text(x)
    if t == "":
        return None
    # convert "5.00" or "5,00" -> 5.00
    t = t.replace("%", "").replace(" ", "")
    t = t.replace(",", ".")
    try:
        return float(t)
    except ValueError:
        return None


def sleep_jitter(base: float, jitter: float) -> None:
    time.sleep(base + random.random() * jitter)


# ----------------------------- data model -----------------------------

@dataclass
class Provenance:
    source_url: str
    retrieved_at: str
    source_hash: str
    http_status: int


@dataclass
class TaxComponent:
    type: str                    # customs_duty, vat, excise, levy, surcharge, other
    code: str                    # DD, TVA, PRCT, ...
    rate_kind: str               # ad_valorem, specific, mixed, exempt, formula
    rate_value: Optional[float] = None
    specific: Optional[Dict[str, Any]] = None   # {"amount": 60, "currency":"DZD", "per":"HL"}
    base: Optional[str] = None   # CIF, quantity, to_confirm_country_rules
    notes: Optional[str] = None


@dataclass
class Advantage:
    targets: List[str]           # e.g. ["DD"], ["DD","TVA"]
    override_kind: str           # rate_to_zero, rate_to_value
    override_value: Optional[float]
    condition: str               # human-readable condition
    documents: List[str]         # extracted keywords or placeholders
    legal_ref: Optional[str] = None


@dataclass
class Formality:
    code: str
    label: str


@dataclass
class TariffLine:
    identity: Dict[str, Any]
    descriptions: Dict[str, Any]
    taxes: List[TaxComponent]
    advantages: List[Advantage]
    formalities: List[Formality]
    provenance: Provenance
    quality: Dict[str, Any]


# ----------------------------- HTTP client -----------------------------

class HttpClient:
    def __init__(self, timeout: int = 30, max_retries: int = 4, backoff: float = 1.5,
                 headers: Optional[Dict[str, str]] = None):
        self.s = requests.Session()
        self.timeout = timeout
        self.max_retries = max_retries
        self.backoff = backoff
        self.headers = headers or DEFAULT_HEADERS

    def get(self, url: str) -> Tuple[int, str]:
        last_exc = None
        for attempt in range(1, self.max_retries + 1):
            try:
                r = self.s.get(url, headers=self.headers, timeout=self.timeout)
                return r.status_code, r.text
            except Exception as e:
                last_exc = e
                sleep_jitter(self.backoff ** attempt, 0.5)
        raise RuntimeError(f"GET failed after retries: {url} ({last_exc})")


# ----------------------------- crawler -----------------------------

def extract_links(html: str, base_url: str) -> List[str]:
    soup = BeautifulSoup(html, "lxml")
    links = []
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if not href:
            continue
        full = urljoin(base_url, href)
        if "douane.gov.dz" not in urlparse(full).netloc:
            continue
        # keep only SPIP pages
        if "spip.php" not in full:
            continue
        links.append(full)
    # de-dup preserving order
    seen = set()
    out = []
    for u in links:
        if u not in seen:
            seen.add(u)
            out.append(u)
    return out


def is_sous_position_url(url: str) -> bool:
    qs = parse_qs(urlparse(url).query)
    return qs.get("page", [""])[0] == "sous_position" and "sous_position" in qs


def crawl(out_dir: str, max_pages: int = 5000, rate: float = 0.6, jitter: float = 0.4,
          start_url: str = ENTRY_URL) -> None:
    safe_mkdir(out_dir)
    raw_dir = os.path.join(out_dir, "raw", "DZA", dt.date.today().isoformat())
    safe_mkdir(raw_dir)

    client = HttpClient()

    queue = [start_url]
    seen = set()
    discovered_sous = set()
    manifest_path = os.path.join(raw_dir, "manifest.jsonl")

    with open(manifest_path, "a", encoding="utf-8") as mf:
        while queue and len(seen) < max_pages:
            url = queue.pop(0)
            if url in seen:
                continue
            seen.add(url)

            sleep_jitter(rate, jitter)

            status, text = client.get(url)
            h = sha256_text(text) if text else ""
            fname = stable_filename_from_url(url)
            fpath = os.path.join(raw_dir, fname)

            with open(fpath, "w", encoding="utf-8", errors="ignore") as f:
                f.write(text or "")

            mf.write(json.dumps({
                "url": url,
                "file": fname,
                "retrieved_at": now_iso(),
                "status": status,
                "hash": h
            }, ensure_ascii=False) + "\n")
            mf.flush()

            # link discovery
            if status == 200 and text:
                links = extract_links(text, BASE_URL)
                for lk in links:
                    if lk not in seen and lk not in queue:
                        queue.append(lk)
                    if is_sous_position_url(lk):
                        discovered_sous.add(lk)

    # Save sous_position URL list for parsing convenience
    with open(os.path.join(raw_dir, "sous_position_urls.txt"), "w", encoding="utf-8") as f:
        for u in sorted(discovered_sous):
            f.write(u + "\n")

    print(f"[crawl] pages_fetched={len(seen)} sous_position_discovered={len(discovered_sous)}")
    print(f"[crawl] raw_dir={raw_dir}")


# ----------------------------- parser -----------------------------

def find_heading_node(soup: BeautifulSoup, heading_text: str):
    # headings might be h2/h3/strong/div. We'll search any tag containing that exact phrase.
    tag = soup.find(string=re.compile(re.escape(heading_text), re.IGNORECASE))
    return tag.parent if tag else None


def next_table_after(node) -> Optional[Any]:
    if node is None:
        return None
    # iterate next elements until a table is found
    for sib in node.next_elements:
        if getattr(sib, "name", None) == "table":
            return sib
    return None


def table_to_rows(table) -> List[List[str]]:
    rows = []
    for tr in table.find_all("tr"):
        cells = [clean_text(td.get_text(" ", strip=True)) for td in tr.find_all(["th", "td"])]
        if cells:
            rows.append(cells)
    return rows


def extract_identity(soup: BeautifulSoup) -> Dict[str, Any]:
    text = soup.get_text("\n", strip=True)

    # HS10 typically appears like "0101211900" near "Sous position tarifaire"
    hs10 = None
    m = re.search(r"Sous\s+position\s+tarifaire\s*:?\s*([0-9]{10})", text, flags=re.IGNORECASE)
    if m:
        hs10 = m.group(1)
    else:
        # fallback: first 10-digit block
        m2 = re.search(r"\b([0-9]{10})\b", text)
        hs10 = m2.group(1) if m2 else None

    key = None
    mk = re.search(r"Cl[ée]\s*([A-Z])", text, flags=re.IGNORECASE)
    if mk:
        key = mk.group(1).upper()

    unit = None
    mu = re.search(r"Unité\s*:\s*([A-Z]{1,3})\b", text, flags=re.IGNORECASE)
    if mu:
        unit = UNIT_CANON.get(mu.group(1).upper(), mu.group(1).upper())

    use_group = None
    mg = re.search(r"Groupe\s+d'utilisation\s*:\s*(.+)", text, flags=re.IGNORECASE)
    if mg:
        use_group = clean_text(mg.group(1))

    section = None
    chapter = None
    ms = re.search(r"Section\s*([0-9]{2})", text, flags=re.IGNORECASE)
    if ms:
        section = ms.group(1)
    mc = re.search(r"Chapitre\s*([0-9]{2})", text, flags=re.IGNORECASE)
    if mc:
        chapter = mc.group(1)

    identity = {
        "country_iso3": "DZA",
        "nomenclature_version": "HS2022",
        "effective_from": None,  # fill later if you want year-specific snapshots
        "effective_to": None,
        "section": section,
        "chapter": chapter,
        "hs6": hs10[:6] if hs10 else None,
        "national_code": hs10,
        "hs6_variant": None,  # computed in build step
        "key": key,
        "unit": unit,
        "use_group": use_group,
    }
    return identity


def extract_description_fr(soup: BeautifulSoup) -> str:
    # Try to capture "Désignation du Produit" block until next major heading
    text = soup.get_text("\n", strip=True)
    if "Désignation du Produit" not in text:
        return ""
    # crude but effective: take lines after "Désignation du Produit" until "Groupe d'utilisation" or "Unité"
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    try:
        idx = lines.index("Désignation du Produit :")
    except ValueError:
        # alt label
        idx = next((i for i, l in enumerate(lines) if "Désignation du Produit" in l), None)
        if idx is None:
            return ""
    chunk = []
    for l in lines[idx + 1:]:
        if re.search(r"Groupe\s+d'utilisation\s*:", l, flags=re.IGNORECASE):
            break
        if re.search(r"Unité\s*:", l, flags=re.IGNORECASE):
            break
        if re.search(r"Taxes\s+Ad-Valorem", l, flags=re.IGNORECASE):
            break
        chunk.append(l)
    # compress bullet list into one line
    return clean_text(" ".join(chunk))


def normalize_tax_code(raw: str) -> Tuple[str, str]:
    r = clean_text(raw).replace(" ", "")
    if r in TAX_CODE_MAP:
        return TAX_CODE_MAP[r]
    # remove dots
    r2 = r.replace(".", "")
    if r2 in TAX_CODE_MAP:
        return TAX_CODE_MAP[r2]
    # fallback: unknown -> other
    return ("other", r2 or raw)


def parse_ad_valorem_table(rows: List[List[str]]) -> List[TaxComponent]:
    # Expect headers like: Taxe | Taux (%) | Observation (sometimes 3-4 cols)
    out = []
    for r in rows[1:]:
        if len(r) < 2:
            continue
        code_raw = r[0]
        rate = parse_float_fr(r[1])
        obs = r[2] if len(r) >= 3 else None
        ttype, code = normalize_tax_code(code_raw)

        if rate is None:
            continue

        base = "CIF" if ttype in ("customs_duty", "levy", "surcharge") else ("to_confirm_country_rules" if ttype == "vat" else None)
        out.append(TaxComponent(
            type=ttype,
            code=code,
            rate_kind="ad_valorem",
            rate_value=rate,
            specific=None,
            base=base,
            notes=clean_text(obs) if obs else None
        ))
    return out


def parse_specific_table(rows: List[List[str]]) -> List[TaxComponent]:
    # Expect headers: Taxe | Quotité/Unité | Unité | Unité de mesure | Observation
    out = []
    for r in rows[1:]:
        if len(r) < 4:
            continue
        code_raw = r[0]
        amount = parse_float_fr(r[1])
        per_unit = clean_text(r[3])  # HL, KG, PA, ...
        obs = r[4] if len(r) >= 5 else None
        ttype, code = normalize_tax_code(code_raw)

        if amount is None:
            continue

        per_unit = UNIT_CANON.get(per_unit.upper(), per_unit.upper()) if per_unit else per_unit
        out.append(TaxComponent(
            type=ttype,
            code=code,
            rate_kind="specific",
            rate_value=None,
            specific={"amount": amount, "currency": "DZD", "per": per_unit},
            base="quantity",
            notes=clean_text(obs) if obs else None
        ))
    return out


def parse_advantages_block(soup: BeautifulSoup) -> List[Advantage]:
    # Often appears as a table (Taxe | Taux | JO | Document) + subsequent lines
    node = find_heading_node(soup, H_ADVANTAGES)
    tbl = next_table_after(node)
    if tbl is None:
        return []

    rows = table_to_rows(tbl)
    advs: List[Advantage] = []
    # rows may be like:
    # Taxe | Taux(%) | N° JO | Document
    # D.D | 0.00 | |   (and then next line(s) contain the doc text)
    i = 1
    while i < len(rows):
        r = rows[i]
        if len(r) >= 2 and re.search(r"\bD\.?D\b", r[0], flags=re.IGNORECASE) or re.search(r"\bT\.?V\.?A\b", r[0], flags=re.IGNORECASE):
            code_raw = r[0]
            rate = parse_float_fr(r[1])
            ttype, code = normalize_tax_code(code_raw)
            # Condition text might be in same row col3/4 or in following row(s)
            doc_txt = ""
            if len(r) >= 4 and r[3]:
                doc_txt = r[3]
            else:
                # Peek next row if it's a single-cell narrative
                if i + 1 < len(rows) and len(rows[i + 1]) == 1:
                    doc_txt = rows[i + 1][0]
                    i += 1
            condition = clean_text(doc_txt)
            targets = [code]  # override only the tax code referenced
            override_kind = "rate_to_zero" if (rate is not None and abs(rate) < 1e-9) else "rate_to_value"
            advs.append(Advantage(
                targets=targets,
                override_kind=override_kind,
                override_value=rate,
                condition=condition,
                documents=[slugify_doc_hint(condition)] if condition else [],
                legal_ref=None
            ))
        i += 1

    # Merge common case where same condition applies to DD and TVA (programme santé)
    merged: Dict[str, Advantage] = {}
    for a in advs:
        k = a.condition.lower().strip()
        if not k:
            continue
        if k not in merged:
            merged[k] = a
        else:
            # merge targets
            merged[k].targets = sorted(list(set(merged[k].targets + a.targets)))
            # if any sets to zero, keep as zero override if values are zero
            if merged[k].override_kind == "rate_to_zero" and a.override_kind == "rate_to_zero":
                merged[k].override_kind = "rate_to_zero"
                merged[k].override_value = 0.0
    # return merged + any empty-condition ones
    out = list(merged.values()) + [a for a in advs if not a.condition]
    return out


def slugify_doc_hint(text: str) -> str:
    t = text.lower()
    t = re.sub(r"[^a-z0-9]+", "_", t)
    t = t.strip("_")
    return t[:64] if t else ""


def parse_formalities(soup: BeautifulSoup) -> List[Formality]:
    node = find_heading_node(soup, H_FORMALITIES)
    tbl = next_table_after(node)
    if tbl is None:
        return []
    rows = table_to_rows(tbl)
    out = []
    for r in rows[1:]:
        if len(r) >= 2 and re.match(r"^\d{2,4}$", r[0]):
            out.append(Formality(code=r[0], label=r[1]))
        elif len(r) == 1:
            # sometimes concatenated strings; attempt split: "910  Declaration ..."
            m = re.match(r"^(\d{2,4})\s+(.*)$", r[0])
            if m:
                out.append(Formality(code=m.group(1), label=m.group(2)))
    return out


def parse_page(html: str, url: str, status: int, source_hash: str, retrieved_at: str) -> Optional[TariffLine]:
    if not html or status != 200:
        return None
    soup = BeautifulSoup(html, "lxml")

    identity = extract_identity(soup)
    desc_fr = extract_description_fr(soup)

    # Ad-valorem table
    adv_node = find_heading_node(soup, H_TAX_ADV)
    adv_tbl = next_table_after(adv_node)
    taxes: List[TaxComponent] = []
    if adv_tbl is not None:
        taxes.extend(parse_ad_valorem_table(table_to_rows(adv_tbl)))

    # Specific table
    spec_node = find_heading_node(soup, H_TAX_SPEC)
    spec_tbl = next_table_after(spec_node)
    if spec_tbl is not None:
        taxes.extend(parse_specific_table(table_to_rows(spec_tbl)))

    advantages = parse_advantages_block(soup)
    formalities = parse_formalities(soup)

    prov = Provenance(source_url=url, retrieved_at=retrieved_at, source_hash=source_hash, http_status=status)

    quality_flags = []
    # QA: code presence
    if not identity.get("national_code") or not re.match(r"^\d{10}$", identity["national_code"] or ""):
        quality_flags.append("bad_national_code")
    # QA: duty rate plausibility
    for t in taxes:
        if t.rate_kind == "ad_valorem" and t.rate_value is not None and (t.rate_value < 0 or t.rate_value > 300):
            quality_flags.append(f"rate_outlier:{t.code}")
    # QA: VAT missing
    if not any(t.code == "TVA" and t.type == "vat" for t in taxes):
        quality_flags.append("vat_missing")
    # QA: no DD
    if not any(t.code == "DD" and t.type == "customs_duty" for t in taxes):
        quality_flags.append("dd_missing")

    line = TariffLine(
        identity=identity,
        descriptions={"fr": desc_fr or None, "en": None},
        taxes=taxes,
        advantages=advantages,
        formalities=formalities,
        provenance=prov,
        quality={"flags": quality_flags, "confidence": 0.9 if not quality_flags else 0.75}
    )
    return line


def parse(out_dir: str) -> None:
    # Locate newest raw dir (by date folder)
    raw_root = os.path.join(out_dir, "raw", "DZA")
    if not os.path.isdir(raw_root):
        raise FileNotFoundError(f"No raw directory found: {raw_root}")

    date_dirs = sorted([d for d in os.listdir(raw_root) if os.path.isdir(os.path.join(raw_root, d))])
    if not date_dirs:
        raise FileNotFoundError("No dated raw folders found under raw/DZA")
    raw_dir = os.path.join(raw_root, date_dirs[-1])

    manifest_path = os.path.join(raw_dir, "manifest.jsonl")
    if not os.path.exists(manifest_path):
        raise FileNotFoundError(f"Missing manifest: {manifest_path}")

    parsed_dir = os.path.join(out_dir, "parsed", "DZA", date_dirs[-1])
    safe_mkdir(parsed_dir)
    parsed_path = os.path.join(parsed_dir, "tariff_lines.jsonl")

    n_in = 0
    n_ok = 0
    with open(manifest_path, "r", encoding="utf-8") as mf, open(parsed_path, "w", encoding="utf-8") as out:
        for line in mf:
            n_in += 1
            m = json.loads(line)
            url = m["url"]
            fname = m["file"]
            status = int(m.get("status", 0))
            source_hash = m.get("hash", "")
            retrieved_at = m.get("retrieved_at", now_iso())
            fpath = os.path.join(raw_dir, fname)
            if not os.path.exists(fpath):
                continue
            html = open(fpath, "r", encoding="utf-8", errors="ignore").read()
            tl = parse_page(html, url, status, source_hash, retrieved_at)
            if tl and tl.identity.get("national_code"):
                out.write(json.dumps(dataclasses.asdict(tl), ensure_ascii=False) + "\n")
                n_ok += 1

    print(f"[parse] manifest_rows={n_in} parsed_lines={n_ok}")
    print(f"[parse] parsed_path={parsed_path}")


# ----------------------------- build (curated + variants) -----------------------------

def compute_hs6_variants(df: pd.DataFrame) -> pd.DataFrame:
    # hs6_variant = hs6--NN by sorting national_code within each hs6
    df = df.copy()
    df["hs6"] = df["national_code"].astype(str).str.slice(0, 6)
    df["national_code_num"] = pd.to_numeric(df["national_code"], errors="coerce")
    df = df.sort_values(["country_iso3", "hs6", "national_code_num"], kind="mergesort")
    df["hs6_rank"] = df.groupby(["country_iso3", "hs6"]).cumcount() + 1
    df["hs6_variant"] = df["hs6"] + "--" + df["hs6_rank"].astype(int).astype(str).str.zfill(2)
    df = df.drop(columns=["national_code_num"])
    return df


def flatten_tax_components(taxes: List[Dict[str, Any]]) -> Tuple[str, str]:
    # split advalorem vs specific as JSON strings for CSV
    adv = []
    spec = []
    for t in taxes or []:
        rk = t.get("rate_kind")
        if rk == "ad_valorem":
            adv.append({"code": t.get("code"), "rate": t.get("rate_value"), "type": t.get("type"), "base": t.get("base"), "notes": t.get("notes")})
        elif rk == "specific":
            s = t.get("specific") or {}
            spec.append({"code": t.get("code"), "amount": s.get("amount"), "currency": s.get("currency"), "per": s.get("per"),
                         "type": t.get("type"), "notes": t.get("notes")})
        else:
            adv.append({"code": t.get("code"), "rate": t.get("rate_value"), "type": t.get("type"), "base": t.get("base"), "notes": t.get("notes")})
    return json.dumps(adv, ensure_ascii=False), json.dumps(spec, ensure_ascii=False)


def build(out_dir: str) -> None:
    parsed_root = os.path.join(out_dir, "parsed", "DZA")
    if not os.path.isdir(parsed_root):
        raise FileNotFoundError(f"No parsed directory found: {parsed_root}")
    date_dirs = sorted([d for d in os.listdir(parsed_root) if os.path.isdir(os.path.join(parsed_root, d))])
    if not date_dirs:
        raise FileNotFoundError("No dated parsed folders found under parsed/DZA")
    parsed_dir = os.path.join(parsed_root, date_dirs[-1])
    parsed_path = os.path.join(parsed_dir, "tariff_lines.jsonl")
    if not os.path.exists(parsed_path):
        raise FileNotFoundError(f"Missing parsed file: {parsed_path}")

    records = []
    with open(parsed_path, "r", encoding="utf-8") as f:
        for line in f:
            obj = json.loads(line)
            records.append(obj)

    if not records:
        raise RuntimeError("No records to build.")

    # Build a flat dataframe
    flat = []
    qa_counts = {}
    for obj in records:
        ident = obj.get("identity", {}) or {}
        desc = obj.get("descriptions", {}) or {}
        prov = obj.get("provenance", {}) or {}
        qual = obj.get("quality", {}) or {}
        taxes = obj.get("taxes", []) or []
        adv_json, spec_json = flatten_tax_components(taxes)

        advantages = obj.get("advantages", []) or []
        formalities = obj.get("formalities", []) or []

        flags = qual.get("flags", []) or []
        for fl in flags:
            qa_counts[fl] = qa_counts.get(fl, 0) + 1

        flat.append({
            "country_iso3": ident.get("country_iso3"),
            "nomenclature_version": ident.get("nomenclature_version"),
            "effective_from": ident.get("effective_from"),
            "section": ident.get("section"),
            "chapter": ident.get("chapter"),
            "hs6": ident.get("hs6"),
            "national_code": ident.get("national_code"),
            "hs6_variant": ident.get("hs6_variant"),  # filled after
            "key": ident.get("key"),
            "unit": ident.get("unit"),
            "use_group": ident.get("use_group"),
            "description_fr": desc.get("fr"),
            "advalorem_json": adv_json,
            "specific_json": spec_json,
            "advantages_json": json.dumps(advantages, ensure_ascii=False),
            "formalities_json": json.dumps(formalities, ensure_ascii=False),
            "source_url": prov.get("source_url"),
            "retrieved_at": prov.get("retrieved_at"),
            "source_hash": prov.get("source_hash"),
            "quality_flags": json.dumps(flags, ensure_ascii=False),
            "confidence": qual.get("confidence")
        })

    df = pd.DataFrame(flat)
    df = df[df["national_code"].astype(str).str.match(r"^\d{10}$", na=False)]
    df = compute_hs6_variants(df)

    pub_dir = os.path.join(out_dir, "published", "DZA", date_dirs[-1])
    safe_mkdir(pub_dir)

    csv_path = os.path.join(pub_dir, "DZA_tariff_curated.csv")
    json_path = os.path.join(pub_dir, "DZA_tariff_curated.json")
    qa_path = os.path.join(pub_dir, "DZA_QA_report.json")

    df.to_csv(csv_path, index=False, encoding="utf-8-sig")

    # Curated JSON: group by national_code for clean objects
    curated = []
    for _, r in df.iterrows():
        curated.append({
            "identity": {
                "country_iso3": r["country_iso3"],
                "nomenclature_version": r["nomenclature_version"],
                "effective_from": r["effective_from"],
                "section": r["section"],
                "chapter": r["chapter"],
                "hs6": r["hs6"],
                "national_code": r["national_code"],
                "hs6_variant": r["hs6_variant"],
                "key": r["key"],
                "unit": r["unit"],
                "use_group": r["use_group"],
            },
            "descriptions": {"fr": r["description_fr"], "en": None},
            "taxes_advalorem": json.loads(r["advalorem_json"]) if r["advalorem_json"] else [],
            "taxes_specific": json.loads(r["specific_json"]) if r["specific_json"] else [],
            "advantages": json.loads(r["advantages_json"]) if r["advantages_json"] else [],
            "formalities": json.loads(r["formalities_json"]) if r["formalities_json"] else [],
            "provenance": {
                "source_url": r["source_url"],
                "retrieved_at": r["retrieved_at"],
                "source_hash": r["source_hash"],
            },
            "quality": {
                "flags": json.loads(r["quality_flags"]) if r["quality_flags"] else [],
                "confidence": r["confidence"],
            }
        })

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(curated, f, ensure_ascii=False, indent=2)

    with open(qa_path, "w", encoding="utf-8") as f:
        json.dump({
            "generated_at": now_iso(),
            "total_lines": int(df.shape[0]),
            "unique_hs6": int(df["hs6"].nunique()),
            "flags": qa_counts
        }, f, ensure_ascii=False, indent=2)

    print(f"[build] csv={csv_path}")
    print(f"[build] json={json_path}")
    print(f"[build] qa={qa_path}")
    print(f"[build] total_lines={df.shape[0]} unique_hs6={df['hs6'].nunique()}")


# ----------------------------- CLI -----------------------------

def main():
    ap = argparse.ArgumentParser(description="DZA tariff connector (crawl/parse/build)")
    sub = ap.add_subparsers(dest="cmd", required=True)

    ap_c = sub.add_parser("crawl", help="crawl and cache raw HTML")
    ap_c.add_argument("--out", required=True, help="output base directory (e.g., ./data)")
    ap_c.add_argument("--max-pages", type=int, default=5000)
    ap_c.add_argument("--rate", type=float, default=0.6, help="base sleep between requests (seconds)")
    ap_c.add_argument("--jitter", type=float, default=0.4, help="random jitter (seconds)")
    ap_c.add_argument("--start-url", default=ENTRY_URL)

    ap_p = sub.add_parser("parse", help="parse cached HTML into parsed JSONL")
    ap_p.add_argument("--out", required=True)

    ap_b = sub.add_parser("build", help="build curated dataset + hs6 variants")
    ap_b.add_argument("--out", required=True)

    args = ap.parse_args()

    if args.cmd == "crawl":
        crawl(args.out, max_pages=args.max_pages, rate=args.rate, jitter=args.jitter, start_url=args.start_url)
    elif args.cmd == "parse":
        parse(args.out)
    elif args.cmd == "build":
        build(args.out)
    else:
        ap.print_help()
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
