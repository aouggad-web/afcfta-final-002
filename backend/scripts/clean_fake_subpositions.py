"""
Remove hallucinated "Type 1", "Type 2", "Autre" placeholder sub-positions
from all country tariff JSON files, and replace DZA's with the authentic
17,115 sub-positions extracted from conformepro.dz (DGD Algeria) on
2026-05-05.

Run from /app/backend:
    python3 scripts/clean_fake_subpositions.py
"""

import json
import re
from collections import defaultdict
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parent.parent
TARIFFS_DIR = BACKEND_DIR / "data" / "tariffs"
DZA_FAST = BACKEND_DIR / "data" / "crawled" / "DZA_tariffs_fast.json"


GENERIC_PATTERNS = [
    re.compile(r"\bType\s*\d+\b", re.IGNORECASE),
    re.compile(r"\bAutres\s*-\s*Type\b", re.IGNORECASE),
    re.compile(r"\bAutres\s*-\s*Autre$", re.IGNORECASE),
]


def is_generic_description(desc: str) -> bool:
    if not desc:
        return True
    desc = desc.strip()
    if desc.lower() in {"autre", "autres", "—", "-", "", "n/a"}:
        return True
    return any(p.search(desc) for p in GENERIC_PATTERNS)


def load_dza_authentic() -> dict:
    """Return {hs6: [sub_position dicts]} from conformepro.dz fast crawl."""
    if not DZA_FAST.exists():
        return {}
    with open(DZA_FAST, "r", encoding="utf-8") as f:
        data = json.load(f)
    grouped = defaultdict(list)
    for sp in data.get("sub_positions", []):
        code = str(sp.get("hs_code") or "").replace(" ", "").replace(".", "")
        if not code or len(code) < 6:
            continue
        hs6 = code[:6]
        grouped[hs6].append({
            "hs_code": code,
            "code": code,
            "description_fr": sp.get("description") or sp.get("name") or "",
            "description": sp.get("description") or sp.get("name") or "",
            "name": sp.get("name") or "",
            "raw_code": sp.get("raw_code"),
            "source": sp.get("source", "conformepro.dz"),
            "source_url": sp.get("source_url"),
        })
    return dict(grouped)


def clean_country_file(path: Path, dza_authentic: dict) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    iso3 = (data.get("country_code") or path.stem.split("_")[0]).upper()
    is_dza = iso3 == "DZA"
    lines = data.get("tariff_lines") or []
    cleaned_total = 0
    replaced_total = 0
    sub_kept = 0

    for line in lines:
        hs6 = str(line.get("hs6") or "").strip()
        if not hs6:
            continue
        if is_dza and hs6 in dza_authentic:
            # Replace fully with authentic conformepro.dz data
            line["sub_positions"] = dza_authentic[hs6]
            replaced_total += len(dza_authentic[hs6])
        else:
            # Strip generic / hallucinated entries
            originals = line.get("sub_positions") or []
            filtered = [
                sp for sp in originals
                if not is_generic_description(
                    sp.get("description_fr") or sp.get("description") or ""
                )
            ]
            removed = len(originals) - len(filtered)
            cleaned_total += removed
            line["sub_positions"] = filtered
            sub_kept += len(filtered)

    backup = path.with_suffix(".json.bak")
    if not backup.exists():
        path.rename(backup)
    else:
        # backup already exists from a previous run — overwrite working file only
        pass
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    return {
        "iso3": iso3,
        "lines": len(lines),
        "fake_removed": cleaned_total,
        "authentic_replaced": replaced_total,
        "authentic_kept": sub_kept,
    }


def main():
    dza_authentic = load_dza_authentic()
    print(f"DZA authentic HS6 groups loaded: {len(dza_authentic)}")
    total_fake = 0
    total_real = 0
    for path in sorted(TARIFFS_DIR.glob("*_tariffs.json")):
        if path.suffix != ".json":
            continue
        res = clean_country_file(path, dza_authentic)
        total_fake += res["fake_removed"]
        total_real += res["authentic_replaced"]
        print(
            f"  {res['iso3']:>3}  lines={res['lines']:>5}  "
            f"fake_removed={res['fake_removed']:>6}  "
            f"authentic_replaced={res['authentic_replaced']:>6}  "
            f"kept={res['authentic_kept']:>6}"
        )
    print()
    print(f"Total fake sub-positions removed across all countries: {total_fake}")
    print(f"DZA authentic sub-positions injected: {total_real}")


if __name__ == "__main__":
    main()
