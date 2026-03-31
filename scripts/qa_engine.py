import pandas as pd
import json
import sys

def run_qa(csv_path: str):
    df = pd.read_csv(csv_path)
    total = len(df)

    def contains_tax(code: str):
        return df["advalorem_json"].fillna("").str.contains(f'"code":"{code}"', regex=False)

    qa = {
        "total_lines": int(total),
        "unique_hs6": int(df["hs6"].nunique()) if "hs6" in df.columns else None,
        "missing_dd_pct": float((~contains_tax("DD")).mean() * 100.0),
        "missing_tva_pct": float((~contains_tax("TVA")).mean() * 100.0),
        "empty_desc_pct": float(df["description_fr"].isna().mean() * 100.0) if "description_fr" in df.columns else None,
    }
    return qa

if __name__ == "__main__":
    print(json.dumps(run_qa(sys.argv[1]), ensure_ascii=False, indent=2))
