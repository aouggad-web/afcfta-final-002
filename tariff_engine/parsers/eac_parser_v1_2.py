import re
import warnings
import camelot
import pandas as pd

warnings.filterwarnings("ignore")

PCT_RE = re.compile(r"(\d+(?:\.\d+)?)\s*%")

# whitelist d'unités courantes (à enrichir)
UNIT_OK = {
    "kg","g","l","hl","m","m2","m3","no","nos","u","unit","pair","prs","pc","pcs","set","doz","ton","t"
}

def _clean(x: str) -> str:
    return str(x).replace("\n", " ").replace("\r", " ").strip()

def _to_hs(code: str) -> str:
    c = _clean(code).replace(".", "")
    return c if c.isdigit() else ""

def _find_rate_pct(cells) -> float:
    for v in cells:
        m = PCT_RE.search(_clean(v))
        if m:
            return float(m.group(1))
    return None

def _find_unit(cells) -> str:
    # on cherche une cellule courte alphnum, puis on normalise
    for v in cells:
        u = _clean(v).lower()
        u = u.replace(".", "")
        if not u:
            continue
        if len(u) <= 6 and re.fullmatch(r"[a-z0-9]+", u):
            if u in UNIT_OK:
                return u
    return ""

def parse_pages(pdf_path: str, pages, flavor: str = "stream") -> pd.DataFrame:
    out = []
    current_heading = None

    for p in pages:
        try:
            tables = camelot.read_pdf(pdf_path, pages=str(p), flavor=flavor)
        except Exception:
            continue

        for tb in tables:
            df = tb.df
            if df is None or df.empty:
                continue
            df = df.applymap(_clean)

            if df.shape[1] < 4 or df.shape[0] < 5:
                continue

            for _, r in df.iterrows():
                cells = r.values.tolist()
                c0 = cells[0] if len(cells) > 0 else ""
                c1 = cells[1] if len(cells) > 1 else ""
                c2 = cells[2] if len(cells) > 2 else ""
                c3 = cells[3] if len(cells) > 3 else ""

                # heading contexte (ex 15.17)
                if re.fullmatch(r"\d{1,2}\.\d{2}", _clean(c0)) and _clean(c1) == "":
                    current_heading = _clean(c0)

                hs = _to_hs(c1) or _to_hs(c0)
                if not hs or len(hs) < 6:
                    continue

                # description: concat des colonnes textuelles (on exclut les colonnes qui ressemblent à unit ou rate)
                desc = " ".join([_clean(c2), _clean(c3)]).strip()

                duty = _find_rate_pct(cells)

                # unité: cherche dans toutes les cellules, mais whitelistée
                unit = _find_unit(cells)

                out.append({
                    "hs_code": hs,
                    "heading_ctx": current_heading,
                    "description": desc,
                    "unit": unit,
                    "duty_rate_pct": duty,
                    "page": int(p),
                    "source_pdf": pdf_path
                })

    df_out = pd.DataFrame(out)
    if df_out.empty:
        return df_out

    # dédoublonnage HS: garder la ligne la plus "riche" (taux présent prioritaire)
    df_out["has_rate"] = df_out["duty_rate_pct"].notna().astype(int)
    df_out = df_out.sort_values(by=["hs_code","has_rate","page"]).drop_duplicates(subset=["hs_code"], keep="last")
    df_out = df_out.drop(columns=["has_rate"])
    return df_out

def run_to_csv(pdf_path: str, out_csv: str, pages, flavor: str = "stream") -> str:
    df = parse_pages(pdf_path, pages=pages, flavor=flavor)
    df.to_csv(out_csv, index=False)
    return out_csv
