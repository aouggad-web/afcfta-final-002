import re
import warnings
import camelot
import pandas as pd

warnings.filterwarnings("ignore")

HS_RE = re.compile(r"\b(\d{4}\.\d{2}\.\d{2})\b|\b(\d{6,10})\b")
PCT_RE = re.compile(r"(\d+(?:\.\d+)?)\s*%")

def _clean(x: str) -> str:
    return str(x).replace("\n", " ").replace("\r", " ").strip()

def _to_hs(code: str) -> str:
    c = _clean(code).replace(".", "")
    return c if c.isdigit() else ""

def _rate_pct(rate_cell: str):
    s = _clean(rate_cell)
    m = PCT_RE.search(s)
    return float(m.group(1)) if m else None

def parse_range(pdf_path: str, page_from: int = 14, page_to: int = 80, flavor: str = "stream") -> pd.DataFrame:
    out = []
    current_heading = None  # ex: "15.17" for context if needed

    for p in range(page_from, page_to + 1):
        try:
            tables = camelot.read_pdf(pdf_path, pages=str(p), flavor=flavor)
        except Exception:
            continue

        for tb in tables:
            df = tb.df
            if df is None or df.empty:
                continue

            df = df.applymap(_clean)

            # Attendu: 7 colonnes (comme page 75). On tolère 5-8.
            if df.shape[1] < 5:
                continue

            # Normaliser colonnes: on travaille sur index 0..n-1
            for _, r in df.iterrows():
                c0 = r.iloc[0] if df.shape[1] > 0 else ""
                c1 = r.iloc[1] if df.shape[1] > 1 else ""
                c2 = r.iloc[2] if df.shape[1] > 2 else ""
                c3 = r.iloc[3] if df.shape[1] > 3 else ""
                c4 = r.iloc[4] if df.shape[1] > 4 else ""
                c5 = r.iloc[5] if df.shape[1] > 5 else ""
                c6 = r.iloc[6] if df.shape[1] > 6 else ""

                # détecter heading (ex "15.17") pour contexte
                if re.fullmatch(r"\d{1,2}\.\d{2}", c0) and c1 == "":
                    current_heading = c0

                # HS code est généralement dans c1 (Tariff No.) sinon parfois dans c0
                hs = _to_hs(c1) or _to_hs(c0)
                if not hs or len(hs) < 6:
                    continue

                # Description: c2 + c3 (souvent split)
                desc = " ".join([x for x in [c2, c3] if x]).strip()

                # Unité: peut être en c4 ou c5 (selon ligne)
                unit = ""
                # heuristique: cellule courte alphabétique
                for u in [c4, c5]:
                    uu = _clean(u)
                    if 0 < len(uu) <= 5 and re.fullmatch(r"[A-Za-z]+", uu):
                        unit = uu.lower()
                        break

                duty = _rate_pct(c6) or _rate_pct(c5)  # parfois le taux glisse

                out.append({
                    "hs_code": hs,
                    "heading_ctx": current_heading,
                    "description": desc,
                    "unit": unit,
                    "duty_rate_pct": duty,
                    "page": p,
                    "source_pdf": pdf_path
                })

    df_out = pd.DataFrame(out)
    if df_out.empty:
        return df_out

    # Nettoyage: garder la dernière occurrence par hs_code (souvent la plus complète)
    df_out = df_out.sort_values(by=["hs_code", "page"]).drop_duplicates(subset=["hs_code"], keep="last")
    return df_out

def run_to_csv(pdf_path: str, out_csv: str, page_from: int = 14, page_to: int = 80) -> str:
    df = parse_range(pdf_path, page_from, page_to, flavor="stream")
    df.to_csv(out_csv, index=False)
    return out_csv
