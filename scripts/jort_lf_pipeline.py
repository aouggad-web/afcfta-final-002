#!/usr/bin/env python3
"""Pipeline JORT → corpus des lois de finances TUN (méthode DZA).
1. Recherche « المالية » (type=loi), pagination
2. Filtre les lois de finances (annuelles + complémentaires)
3. Pour chacune : texte intégral (A2) → référence JORT + articles tarifaires (« جمرك »)
4. PDF (A18) → SHA-256 → data/sources/TUN/jort/ (PDFs récents seulement)
Sortie : data/sources/TUN/jort/_manifest_jort.json
"""
import hashlib
import html as htmllib
import json
import re
import sys
import urllib.parse as up
import urllib.request as rq
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from jort_crawler import (  # noqa: E402
    BASE, OPENER, UA, open_advanced_search, search, parse_results,
    FORM_ACTION_RE, paginate,
)

ARCHIVE = Path("data/sources/TUN/jort")
ARCHIVE.mkdir(parents=True, exist_ok=True)
MANIFEST = ARCHIVE / "_manifest_jort.json"
PDF_SINCE = 2019  # PDFs archivés seulement pour les LF >= cette année


def detail_and_pdf(action_url, occ, pdf_out=None):
    """Texte intégral (A2) + PDF (A18) pour l'occurrence `occ` de la page résultats."""
    # texte intégral
    page = get_req(action_url, {"WD_BUTTON_CLICK_": "A2", "A1": str(occ)})
    t2 = re.sub(r"<script.*?</script>", "", page, flags=re.S | re.I)
    txt = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", t2))
    txt = htmllib.unescape(txt)
    # référence JORT : champs readonly du détail (A4=année, A5=numéro, A6=date)
    vals = dict(re.findall(r'NAME=(A[456])\s+VALUE="?([^"\s>]+)"?[^>]*READONLY', page))
    jort_ref = {
        "annee": vals.get("A4"),
        "numero": vals.get("A5"),
        "date": vals.get("A6"),
    }
    # articles à teneur fiscale/tarifaire : split sur les articles (الفصل N) puis filtre
    KW = ("جمرك", "تعريفة", "الرسوم", "معلوم ", "الاداء على القيمة")
    parts = re.split(r"الفصل\s*(?:عدد\s*)?(\d+)", txt)
    articles = []
    for i in range(1, len(parts) - 1, 2):
        num, body = parts[i], parts[i + 1]
        if any(k in body for k in KW) and len(body.strip()) > 30:
            articles.append(f"الفصل {num} — {body.strip()[:500]}")
    # PDF
    pdf_sha = pdf_size = None
    if pdf_out is not None:
        if pdf_out.exists() and pdf_out.stat().st_size > 10000:
            blob = pdf_out.read_bytes()
            pdf_sha, pdf_size = hashlib.sha256(blob).hexdigest(), len(blob)
        else:
            try:
                req = rq.Request(
                    action_url,
                    data=up.urlencode({"WD_BUTTON_CLICK_": "A18", "A1": str(occ)}).encode(),
                    headers={"User-Agent": UA, "Referer": BASE},
                )
                with OPENER.open(req, timeout=120) as r:
                    blob = r.read()
                if blob.startswith(b"%PDF"):
                    sha = hashlib.sha256(blob).hexdigest()
                    pdf_out.write_bytes(blob)
                    pdf_sha, pdf_size = sha, len(blob)
            except Exception as e:
                print(f"    PDF échec: {e}", file=sys.stderr)
    return {
        "jort_ref": jort_ref,
        "articles_douane": articles[:12],
        "pdf": {"file": pdf_out.name if pdf_out else None, "sha256": pdf_sha, "bytes": pdf_size},
        "text_len": len(txt),
    }


def get_req(url, extra):
    data = {"WD_ACTION_": "", **extra}
    req = rq.Request(
        url, data=up.urlencode(data).encode(),
        headers={"User-Agent": UA, "Referer": BASE},
    )
    with OPENER.open(req, timeout=90) as r:
        return r.read().decode("utf-8", errors="ignore")


def main():
    a3, f3 = open_advanced_search()
    res = search(a3, f3, "المالية", "2", None)
    lfs = {}
    docs = []
    for page in range(10):
        m = FORM_ACTION_RE.search(res)
        action = m.group(1)
        if action.startswith("/"):
            action = BASE + action
        rows = parse_results(res)
        for r in rows:
            t = r["title"]
            if "قانون المالية" in t or "قانون المال" in t:
                annee_m = re.search(r"المالية لسنة\s*(\d{4})", t)
                comp = "التكميلي" in t or "مكمل" in t
                if annee_m:
                    key = f"LF{annee_m.group(1)}{'C' if comp else ''}"
                    if key not in lfs:
                        lfs[key] = True
                        # détail + PDF immédiatement (état serveur = cette page)
                        pdf_path = (
                            ARCHIVE / f"{key}.pdf"
                            if int(annee_m.group(1)) >= PDF_SINCE
                            else None
                        )
                        print(f"{key}: {t[:60]}…", file=sys.stderr)
                        d = detail_and_pdf(action, r["occ"], pdf_path)
                        docs.append({
                            "file": pdf_path.name if pdf_path else None,
                            "title": f"Loi de finances {'complémentaire ' if comp else ''}pour {annee_m.group(1)} — {t}",
                            "type": "loi_finances",
                            "annee_budget": int(annee_m.group(1)),
                            "jort_ref": d["jort_ref"],
                            "articles_douane_extraits": len(d["articles_douane"]),
                            "articles_douane": d["articles_douane"],
                            "pdf_sha256": d["pdf"]["sha256"],
                            "pdf_bytes": d["pdf"]["bytes"],
                            "source_url": f"{BASE} (JORT, recherche multicritères — texte intégral)",
                        })
        print(f"page {page + 1}: total LF = {len(docs)}", file=sys.stderr)
        res = paginate(action, (page + 1) * 20)
        if not res or not parse_results(res):
            break

    print(f"== {len(docs)} lois de finances traitées ==", file=sys.stderr)
    docs.sort(key=lambda x: x["annee_budget"], reverse=True)

    manifest = {
        "country": "TUN",
        "description": "Lois de finances tunisiennes (textes modifiant droits/taxes) — JORT, Imprimerie Officielle. PDFs archivés SHA-256 pour les lois récentes ; texte intégral consultable en ligne.",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source": "http://www.iort.gov.tn (recherche multicritères, texte intégral depuis 2000)",
        "count": len(docs),
        "documents": docs,
    }
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"→ {MANIFEST} ({len(docs)} docs)", file=sys.stderr)


if __name__ == "__main__":
    main()
