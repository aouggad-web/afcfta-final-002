#!/usr/bin/env python3
"""Crawler JORT (Imprimerie Officielle, iort.gov.tn) — appli WebDev sessionnelle.
Recherche multicritères dans le texte intégral (depuis 2000) + index.
Filtres : type de texte (2=loi, 3=décret, 4=arrêté, 5=décision, 6=avis), année.
Sortie : JSON avec type, titre, langue + pagination.
Usage: python3 jort_crawler.py "<mot-clé arabe>" [type] [--year 2026] [--pages 3] [--json out.json]
"""
import html as htmllib
import json
import re
import ssl
import sys
import urllib.parse as up
import urllib.request as rq
from http.cookiejar import CookieJar
from pathlib import Path

BASE = "http://www.iort.gov.tn"
CONNECT = f"{BASE}/WD120AWP/WD120Awp.exe/CONNECT/SITEIORT"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/126.0"
CTXSSL = ssl.create_default_context()
CTXSSL.check_hostname = False
CTXSSL.verify_mode = ssl.CERT_NONE
JAR = CookieJar()
OPENER = rq.build_opener(rq.HTTPSHandler(context=CTXSSL), rq.HTTPCookieProcessor(JAR))

FORM_ACTION_RE = re.compile(r'<FORM[^>]*ACTION="([^"]+)"', re.I)
HIDDEN_VAL_RE = re.compile(r'VALUE\s*=\s*"?([^">\s]*)', re.I)
OPT_RE = re.compile(r'<option[^>]*VALUE="?([\w-]+)"?[^>]*>', re.I)
ROW_TYPE_RE = re.compile(r'<div id="_(\d+)_A10">\s*([^<]+?)\s*</div>')
ROW_TITLE_RE = re.compile(
    r'<a name=A2[^>]*_PAGE_\.A1\.value=(\d+);[^>]*TITLE="[^"]*"[^>]*>(.*?)</a>', re.S
)
ROW_PDF_RE = re.compile(r'_PAGE_\.A1\.value=(\d+);javascript:\{_JSL\(_PAGE_,\'A18\'')
PAGI_RE = re.compile(r'href="([^"]*WD_ACTION_=SCROLLTABLE[^"]*)"', re.I)


def get(url, data=None):
    req = rq.Request(url, data=data, headers={"User-Agent": UA, "Referer": BASE})
    with OPENER.open(req, timeout=45) as r:
        return r.read().decode("utf-8", errors="ignore")


def parse_form(html):
    m = FORM_ACTION_RE.search(html)
    action = m.group(1) if m else None
    if action and action.startswith("/"):
        action = BASE + action
    fields = {}
    for tag in re.finditer(r"<(?:INPUT|SELECT|TEXTAREA)[^>]*>", html, re.I):
        t = tag.group(0)
        nm = re.search(r'NAME\s*=\s*"?(\w+)', t, re.I)
        if not nm or nm.group(1) in ("WD_BUTTON_CLICK_", "WD_ACTION_"):
            continue
        name = nm.group(1)
        if "<SELECT" in t.upper():
            om = OPT_RE.search(html[tag.end(): tag.end() + 800])
            fields[name] = om.group(1) if om else ""
        else:
            vm = HIDDEN_VAL_RE.search(t)
            fields[name] = vm.group(1) if vm else ""
    return action, fields


def submit(action_url, fields, button):
    data = dict(fields)
    data["WD_ACTION_"] = ""
    data["WD_BUTTON_CLICK_"] = button
    return get(action_url, data=up.urlencode(data).encode())


def clean(s):
    return htmllib.unescape(re.sub(r"\s+", " ", s)).strip()


def parse_results(html):
    """(type, titre, occ) par ligne de résultat."""
    types = {occ: clean(t) for occ, t in ROW_TYPE_RE.findall(html)}
    rows = []
    for occ, title in ROW_TITLE_RE.findall(html):
        rows.append({"occ": int(occ), "type": types.get(occ, ""), "title": clean(title)})
    return rows


def open_advanced_search():
    home = get(CONNECT)
    a, _ = parse_form(home)
    r8 = get(a + "?A8")  # page « البحث عن الرائد الرسمي »
    a8, f8 = parse_form(r8)
    adv = submit(a8, f8, "A31")  # → recherche multicritères
    a3, f3 = parse_form(adv)
    return a3, f3


def search(a3, f3, keyword, type_code="", year=None):
    f3["A22"] = keyword
    f3["A23"] = "1"  # contient
    f3["A25"] = "2"  # texte intégral depuis 2000
    f3["A9"] = type_code or "1"
    if year:
        f3["A8"] = str(2028 - int(year))  # index : 1='', 2=2026, 3=2025…
    return submit(a3, f3, "A40")  # bouton « بحث »


def paginate(action_url, offset):
    """GET SCROLLTABLE avec offset (20/page)."""
    sep = "&" if "?" in action_url else "?"
    return get(f"{action_url}{sep}WD_ACTION_=SCROLLTABLE&ZR_RechercheArijMulti={offset}")


def fetch_detail(action_url, occ):
    """Texte intégral d'un résultat (bouton A2) + lien PDF (A7) si présent."""
    data = {"WD_ACTION_": "", "WD_BUTTON_CLICK_": "A2", "A1": str(occ)}
    page = get(action_url, data=up.urlencode(data).encode())
    t2 = re.sub(r"<script.*?</script>", "", page, flags=re.S | re.I)
    # PDF : ancres internes / fileadmin / .pdf
    pdfs = sorted(set(re.findall(r'href="([^"]*(?:\.pdf|AFFICHEPDF|fileadmin)[^"]*)"', t2, re.I)))
    # texte visible
    txt = htmllib.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", t2)))
    # contexte de la page (form action)
    m = FORM_ACTION_RE.search(page)
    return {
        "page_url": BASE + m.group(1) if m else None,
        "pdfs": pdfs,
        "text_excerpt": txt[txt.find("خارطة الموقع") + 14:][:4000] if "خارطة الموقع" in txt else txt[:4000],
        "raw_len": len(page),
    }


def main():
    keyword = sys.argv[1] if len(sys.argv) > 1 else "الجمركي"
    type_code = sys.argv[2] if len(sys.argv) > 2 and sys.argv[2].strip() else ""
    year, pages, out = None, 1, None
    args = sys.argv[3:]
    if "--year" in args:
        year = args[args.index("--year") + 1]
    if "--pages" in args:
        pages = int(args[args.index("--pages") + 1])
    if "--json" in args:
        out = args[args.index("--json") + 1]

    a3, f3 = open_advanced_search()
    print(f"recherche: kw={keyword!r} type={type_code or 'tous'} année={year or '-'}", file=sys.stderr)
    res = search(a3, f3, keyword, type_code, year)

    all_rows = []
    cur_action = None
    for page in range(pages):
        rows = parse_results(res)
        all_rows.extend(rows)
        m = FORM_ACTION_RE.search(res)
        cur_action = BASE + m.group(1) if m and m.group(1).startswith("/") else m.group(1) if m else cur_action
        print(f"page {page + 1}: +{len(rows)} (total {len(all_rows)})", file=sys.stderr)
        pagi = PAGI_RE.search(res)
        if not pagi or not rows:
            break
        res = paginate(cur_action, (page + 1) * 20)

    for r in all_rows:
        print(f"[{r['type']:8}] {r['title'][:130]}")
    if out:
        Path(out).write_text(
            json.dumps(
                {
                    "source": "iort.gov.tn (JORT, Imprimerie Officielle)",
                    "query": {"keyword": keyword, "type": type_code, "year": year},
                    "extracted_at": "2026-08-30",
                    "count": len(all_rows),
                    "results": all_rows,
                },
                ensure_ascii=False,
                indent=1,
            ),
            encoding="utf-8",
        )
        print(f"→ {out}", file=sys.stderr)


if __name__ == "__main__":
    main()
