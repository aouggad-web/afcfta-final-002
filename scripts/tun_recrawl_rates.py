#!/usr/bin/env python3
"""Re-crawl complet des taux TUN depuis le Tarif Web 2026 officiel (douane.gov.tn).
Méthode DZA : source authentique uniquement, sauvegarde incrémentale, aucun taux inventé.
Usage:
  python3 tun_recrawl_rates.py pilot [N]   # N premiers codes (défaut 8)
  python3 tun_recrawl_rates.py full        # crawl complet des codes d'énumération
  python3 tun_recrawl_rates.py missing     # reprend les codes sans taux / en échec
"""
import html as htmllib
import json
import re
import ssl
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import build_opener, HTTPSHandler
from urllib.parse import urlencode

BASE = "https://www.douane.gov.tn/tarifwebnew/getresultat.php"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/126.0 Safari/537.36",
    "Accept-Language": "fr-FR,fr;q=0.9",
}
ENUM = Path(__file__).resolve().parents[1] / "backend/data/crawled/TUN_enumeration_2026-08.json"
OUT = Path(__file__).resolve().parents[1] / "backend/data/crawled/TUN_rates_2026-08-30.json"
CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE
OPENER = build_opener(HTTPSHandler(context=CTX))

SEC_RE = re.compile(r'section-title">\s*([^<]+?)\s*</div')
TAXROW_RE = re.compile(
    r"<td>\s*([A-Za-z0-9./()]+)\s*<br>\s*<font class=\"lib_ass\">\s*(.*?)\s*</font>\s*</td>"
    r"\s*<td[^>]*>\s*(.*?)\s*</td>\s*<td>\s*(.*?)\s*</td>",
    re.S,
)
PREFROW_RE = re.compile(
    r"<td[^>]*>\s*(\d{1,4})\s*</td>\s*<td[^>]*>\s*([^<]+?)\s*</td>\s*<td[^>]*>\s*([^<]+?)\s*</td>",
    re.S,
)
META_RE = re.compile(
    r"<th>(QCS|GU|Mode de Paiement|NOMBRE|BIENS DE CONSOMMATION)[^<]*(?:<br>\s*<font class=\"lib_ass\">\s*(.*?)\s*</font>)?\s*</th>\s*<th>[^<]*?(?:<br>\s*<font class=\"lib_ass\">\s*(.*?)\s*</font>)?\s*</th>\s*<th>[^<]*?(?:<br>\s*<font class=\"lib_ass\">\s*(.*?)\s*</font>)?\s*</th>\s*</tr>\s*<tr>\s*<td>(.*?)</td>\s*<td>(.*?)</td>\s*<td>(.*?)</td>",
    re.S,
)
TH_RE = re.compile(r"<th>(.*?)</th>", re.S)
TD_RE = re.compile(r"<td>(.*?)</td>", re.S)
TAG_RE = re.compile(r"<[^>]+>")


def clean(s):
    return htmllib.unescape(TAG_RE.sub(" ", s)).replace("\xa0", " ").strip()


def num(v):
    """Normalise '36 %' -> 36.0, '0.1 dinars' -> 0.1, garde brut sinon."""
    m = re.match(r"^\s*(-?[\d\s.,]+)\s*(%|dinars?|dt|D)\s*$", v, re.I)
    if not m:
        return None
    n = m.group(1).replace(" ", "").replace("\xa0", "")
    n = n.replace(",", ".") if n.count(",") == 1 and "." not in n else n
    try:
        return float(n)
    except ValueError:
        return None


def fetch(code, tries=4):
    qs = urlencode({"choix": "", "chap": "", "sel": code})
    last = ""
    for attempt in range(tries):
        try:
            req = {
                "User-Agent": HEADERS["User-Agent"],
                "Accept-Language": HEADERS["Accept-Language"],
            }
            import urllib.request as _u

            r = _u.Request(f"{BASE}?{qs}", headers=req)
            with OPENER.open(r, timeout=30) as resp:
                data = resp.read().decode("utf-8", errors="ignore")
                if resp.status == 200 and "info-table" in data:
                    return data, None
                if resp.status == 200:
                    # page valide mais aucun résultat pour ce code (pas de retry)
                    return None, "no_result"
                last = f"HTTP {resp.status}"
        except Exception as e:
            last = f"{type(e).__name__}: {e}"
        time.sleep(3 + attempt * 4)
    return None, last


def parse_detail(text):
    out = {"import_taxes": [], "export_taxes": [], "preferential": [], "meta": {}}
    parts = SEC_RE.split(text)
    # parts: [pre, title1, body1, title2, body2, ...]
    for i in range(1, len(parts), 2):
        title = parts[i].strip().upper()
        body = parts[i + 1] if i + 1 < len(parts) else ""
        if "IMPORTATION" in title and "EXPORT" not in title:
            for m in TAXROW_RE.finditer(body):
                code, label, val, base = (
                    clean(m.group(1)),
                    clean(m.group(2)),
                    clean(m.group(3)),
                    clean(m.group(4)),
                )
                out["import_taxes"].append(
                    {
                        "code": code,
                        "label": label,
                        "value_raw": val,
                        "value_num": num(val),
                        "base": base,
                    }
                )
        elif "EXPORTATION" in title:
            for m in TAXROW_RE.finditer(body):
                code, label, val, base = (
                    clean(m.group(1)),
                    clean(m.group(2)),
                    clean(m.group(3)),
                    clean(m.group(4)),
                )
                out["export_taxes"].append(
                    {
                        "code": code,
                        "label": label,
                        "value_raw": val,
                        "value_num": num(val),
                        "base": base,
                    }
                )
        elif "PRÉFÉRENTIELS" in title or "PREFERENTIELS" in title:
            for m in PREFROW_RE.finditer(body):
                out["preferential"].append(
                    {
                        "country_code": clean(m.group(1)),
                        "country": clean(m.group(2)),
                        "rate_raw": clean(m.group(3)),
                    }
                )
        elif "INFORMATIONS GÉNÉRALES" in title or "INFORMATIONS GENERALES" in title:
            ths = [clean(x) for x in TH_RE.findall(body)]
            tds = [clean(x) for x in TD_RE.findall(body)]
            for k, v in zip(ths, tds):
                if k:
                    short = k.split("  ")[0].split("\n")[0].strip()
                    out["meta"][short or k[:30]] = v
        elif "CCEC" in title:
            ths = [clean(x).split("\n")[0].strip() for x in TH_RE.findall(body)]
            tds = [clean(x) for x in TD_RE.findall(body)]
            for k, v in zip(ths, tds):
                if k in ("IMPORT", "EXPORT"):
                    out["meta"][k.lower()] = v
    return out


def codes_from_enum():
    enum = json.loads(ENUM.read_text(encoding="utf-8"))
    lst = []
    for ch, codes in sorted(enum["chapters"].items()):
        for c in sorted(codes):
            lst.append((ch, c))
    return enum, lst


_lock = threading.Lock()
_stats = {"done": 0, "ok": 0, "failed": 0, "no_result": 0}


def save(results, enum, done, failed):
    doc = {
        "country": "TUN",
        "source": "douane.gov.tn/tarifwebnew/getresultat.php (Tarif Web 2026, portail officiel Douane)",
        "enumeration_source": "backend/data/crawled/TUN_enumeration_2026-08.json",
        "extracted_at": datetime.now(timezone.utc).isoformat(),
        "stats": {
            "attempted": done,
            "ok": _stats["ok"],
            "no_result": _stats["no_result"],
            "failed": _stats["failed"],
            "total_enum": _stats.get("total", 0),
        },
        "failures": failed,
        "rates": results,
    }
    tmp = OUT.with_suffix(".tmp")
    tmp.write_text(json.dumps(doc, ensure_ascii=False), encoding="utf-8")
    tmp.replace(OUT)


def worker(args):
    ch, code = args
    text, err = fetch(code)
    if text is None:
        return code, None, err, False
    if "DROITS" not in text and "TAXES" not in text:
        return code, None, "no_result", False
    rec = parse_detail(text)
    rec["chapter"] = ch
    rec["hs_code"] = code
    return code, rec, None, True


def run(targets, results, failed, workers=3, save_every=150):
    total = len(targets)
    _stats["total"] = total
    done = 0
    t0 = time.time()
    with ThreadPoolExecutor(max_workers=workers) as ex:
        for fut in as_completed([ex.submit(worker, t) for t in targets]):
            code, rec, err, ok = fut.result()
            with _lock:
                done += 1
                _stats["done"] = done
                if ok:
                    results[code] = rec
                    _stats["ok"] += 1
                elif err == "no_result":
                    results[code] = {"hs_code": code, "chapter": code[:2], "no_result": True}
                    _stats["no_result"] += 1
                else:
                    failed.append({"code": code, "error": err})
                    _stats["failed"] += 1
                if done % 25 == 0:
                    rate = done / max(time.time() - t0, 1)
                    eta = (total - done) / max(rate, 0.01) / 60
                    print(
                        f"[{done}/{total}] ok={_stats['ok']} nores={_stats['no_result']} fail={_stats['failed']} "
                        f"| {rate:.1f}/s ETA {eta:.0f} min",
                        flush=True,
                    )
                if done % save_every == 0 or done == total:
                    save(results, None, done, failed)


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "pilot"
    enum, all_codes = codes_from_enum()
    print(f"énumération: {len(all_codes)} codes", flush=True)

    if mode == "pilot":
        n = int(sys.argv[2]) if len(sys.argv) > 2 else 8
        # mix: quelques codes connus + un ch.87 (hybrides/électriques)
        picks = ["01012100015", "01012900011", "10063010911", "87038000113", "87034000114"]
        picks += [c for _, c in all_codes if c not in picks][:n]
        for code in picks:
            text, err = fetch(code)
            if text is None:
                print(f"{code}: ÉCHEC {err}", flush=True)
                continue
            rec = parse_detail(text)
            print(f"--- {code} ---", flush=True)
            print(json.dumps(rec, ensure_ascii=False, indent=1)[:1500], flush=True)
        return

    results, failed = {}, []
    if OUT.exists() and mode in ("full", "missing"):
        prev = json.loads(OUT.read_text(encoding="utf-8"))
        results = prev.get("rates", {})
        prev_fail = {f["code"] for f in prev.get("failures", [])}
        remaining = [c for _, c in all_codes if c not in results]
        if mode == "missing":
            # reprend uniquement : codes en échec + codes jamais traités
            targets = [(c[:2], c) for c in sorted(prev_fail)]
            targets += [(c[:2], c) for c in remaining]
        else:
            targets = [(c[:2], c) for c in remaining]
    else:
        targets = all_codes
    print(f"à traiter: {len(targets)}", flush=True)
    save(results, enum, len(results), failed)
    run(targets, results, failed, workers=3, save_every=150)
    save(results, enum, len(results), failed)
    print(
        f"FINI: ok={_stats['ok']} no_result={_stats['no_result']} failed={_stats['failed']}",
        flush=True,
    )


if __name__ == "__main__":
    main()
