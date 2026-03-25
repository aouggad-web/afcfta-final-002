import pandas as pd
import json
import sys

FIELDS = ["advalorem_json", "specific_json", "advantages_json", "formalities_json"]

def compare(old_csv: str, new_csv: str):
    old = pd.read_csv(old_csv).set_index("national_code")
    new = pd.read_csv(new_csv).set_index("national_code")

    deltas = []

    for c in new.index.difference(old.index):
        deltas.append({"national_code": c, "change_type": "NEW"})

    for c in old.index.difference(new.index):
        deltas.append({"national_code": c, "change_type": "REMOVED"})

    common = old.index.intersection(new.index)
    for c in common:
        for f in FIELDS:
            ov = str(old.loc[c, f]) if f in old.columns else ""
            nv = str(new.loc[c, f]) if f in new.columns else ""
            if ov != nv:
                deltas.append({
                    "national_code": c,
                    "change_type": "MODIFIED",
                    "field_changed": f,
                    "old_value": ov,
                    "new_value": nv
                })

    return deltas

if __name__ == "__main__":
    old_csv, new_csv = sys.argv[1], sys.argv[2]
    print(json.dumps(compare(old_csv, new_csv), ensure_ascii=False, indent=2))
