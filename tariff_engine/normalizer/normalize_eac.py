import re
import pandas as pd

HS_RE = re.compile(r"\b(\d{6,10})\b")

def normalize(raw_csv: str, bloc: str, country: str, hs_version: str) -> pd.DataFrame:
    """
    Normalizes raw tariff data, preserving key columns and standardizing the format.
    """
    df = pd.read_csv(raw_csv, dtype=str).fillna("")
    
    def find_hs(row):
        for v in row.values:
            v = str(v).replace(".", "").strip()
            m = HS_RE.search(v)
            if m: return m.group(1)
        return ""

    # Preserve all columns and only filter rows where HS code is found
    df["hs_code"] = df.apply(find_hs, axis=1)
    df = df[df["hs_code"] != ""].drop_duplicates(subset=["hs_code"])
    
    # Clean up the duty rates (converting to float for calculations)
    df["duty_rate_pct"] = pd.to_numeric(df["duty_rate_pct"], errors='coerce')
    
    df["bloc"] = bloc
    df["country"] = country
    df["hs_version"] = hs_version
    
    # Final cleanup of columns to keep it professional
    cols = ["hs_code", "description", "unit", "duty_rate_pct", "page", "bloc", "country", "hs_version"]
    return df[cols]
