import re
import pandas as pd

HS_RE = re.compile(r"\b(\d{6,10})\b")

def normalize(raw_csv: str, bloc: str, country: str, hs_version: str) -> pd.DataFrame:
    df = pd.read_csv(raw_csv, dtype=str).fillna("")

    def find_hs(row) -> str:
        for v in row.values:
            v = str(v).replace(".", "").strip()
            m = HS_RE.search(v)
            if m:
                return m.group(1)
        return ""

    out = pd.DataFrame()
    out["hs_code"] = df.apply(find_hs, axis=1)
    out = out[out["hs_code"] != ""].drop_duplicates(subset=["hs_code"])

    out["bloc"] = bloc
    out["country"] = country
    out["hs_version"] = hs_version
    return out
