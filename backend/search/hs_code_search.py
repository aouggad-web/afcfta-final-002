"""
Optimized Tariff Search Engine for AfCFTA.
Dynamically loads data from the tariff engine and provides high-performance search.
"""

import os
import json
import pandas as pd
import re
from pathlib import Path
from typing import List, Dict, Any, Optional
from difflib import SequenceMatcher

class TariffSearchEngine:
    def __init__(self, data_dir: str = "tariff_engine/normalized"):
        self.data_dir = data_dir
        self.df = pd.DataFrame()
        self.load_data()

    def load_data(self):
        """
        Loads all normalized tariff CSV files into a central searchable DataFrame.
        Falls back to /app/backend/data/hs6_database.json + per-country tariffs
        when the normalized CSV directory is missing/empty.
        """
        all_data = []
        if os.path.exists(self.data_dir):
            for file in os.listdir(self.data_dir):
                if file.endswith(".csv"):
                    try:
                        temp_df = pd.read_csv(os.path.join(self.data_dir, file))
                        all_data.append(temp_df)
                    except Exception as e:
                        print(f"Error loading {file}: {e}")

        if all_data:
            self.df = pd.concat(all_data, ignore_index=True)
            self.df["description"] = self.df["description"].fillna("").astype(str)
            print(f"TariffSearchEngine: Loaded {len(self.df)} tariff positions from CSVs.")
            return

        # Fallback: load from JSON sources shipped with the backend.
        rows = self._load_from_backend_json()
        if rows:
            self.df = pd.DataFrame(rows)
            self.df["description"] = self.df["description"].fillna("").astype(str)
            print(f"TariffSearchEngine: Loaded {len(self.df)} HS6 entries from backend JSON fallback.")
        else:
            self.df = pd.DataFrame(columns=["hs_code", "description", "duty_rate_pct", "country", "bloc"])
            print("TariffSearchEngine: No data loaded.")

    def _load_from_backend_json(self) -> List[Dict[str, Any]]:
        """Build a search index from /app/backend/data/hs6_database.json
        and per-country *_tariffs.json files (FR descriptions preferred).
        """
        backend_data_dir = Path(__file__).resolve().parent.parent / "data"
        rows: List[Dict[str, Any]] = []

        # 1) Generic HS6 database (no country, no duty rate)
        hs6_db_path = backend_data_dir / "hs6_database.json"
        if hs6_db_path.exists():
            try:
                with open(hs6_db_path, "r", encoding="utf-8") as fh:
                    hs6_db = json.load(fh)
                for code, entry in hs6_db.items():
                    desc = entry.get("description_fr") or entry.get("description_en") or ""
                    rows.append({
                        "hs_code": str(code),
                        "description": desc,
                        "duty_rate_pct": None,
                        "country": "",
                        "bloc": "",
                    })
            except Exception as e:
                print(f"TariffSearchEngine: failed loading hs6_database.json: {e}")

        # 2) Per-country tariff files (used when query targets a specific country)
        tariffs_dirs = [backend_data_dir / "tariffs", backend_data_dir / "crawled", backend_data_dir]
        seen = set()
        for td in tariffs_dirs:
            if not td.exists():
                continue
            for fp in td.glob("*_tariffs.json"):
                key = fp.name
                if key in seen:
                    continue
                seen.add(key)
                country = fp.stem.replace("_tariffs", "").upper()
                try:
                    with open(fp, "r", encoding="utf-8") as fh:
                        data = json.load(fh)
                    for line in data.get("tariff_lines", []) or []:
                        hs6 = str(line.get("hs6") or line.get("hs_code") or "")
                        if not hs6:
                            continue
                        desc = line.get("description_fr") or line.get("description_en") or line.get("description") or ""
                        rows.append({
                            "hs_code": hs6,
                            "description": desc,
                            "duty_rate_pct": line.get("dd_rate"),
                            "country": country,
                            "bloc": "",
                        })
                except Exception as e:
                    print(f"TariffSearchEngine: failed loading {fp}: {e}")
        return rows

    def search(self, query: str, country: Optional[str] = None, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Hybrid search: Handles exact HS codes, partial codes, and fuzzy descriptions.
        """
        if self.df.empty:
            return []

        query = query.strip().lower()
        results = pd.DataFrame()

        # 1. Exact or Partial HS Code Match (Highest Priority)
        hs_query = re.sub(r"[^0-9]", "", query)
        if hs_query:
            hs_matches = self.df[self.df["hs_code"].astype(str).str.contains(hs_query)]
            hs_matches = hs_matches.copy()
            hs_matches["score"] = 1.0
            results = pd.concat([results, hs_matches])

        # 2. Keyword/Full-Text Match in Description
        keywords = query.split()
        if keywords:
            # Simple boolean 'and' match for keywords
            mask = self.df["description"].str.lower().apply(lambda x: all(k in x for k in keywords))
            keyword_matches = self.df[mask].copy()
            keyword_matches["score"] = 0.8
            results = pd.concat([results, keyword_matches])

        if results.empty:
            # 3. Fuzzy Fallback (Only if no keyword matches found)
            # We use a vectorized approach for performance
            self.df["temp_ratio"] = self.df["description"].str.lower().apply(
                lambda x: SequenceMatcher(None, query, x).ratio()
            )
            fuzzy_matches = self.df[self.df["temp_ratio"] > 0.4].copy()
            fuzzy_matches["score"] = fuzzy_matches["temp_ratio"]
            results = pd.concat([results, fuzzy_matches])

        if results.empty:
            return []

        # Filter by country if specified
        if country:
            results = results[results["country"].str.upper() == country.upper()]

        # Deduplicate and sort by score
        results = results.sort_values(by="score", ascending=False).drop_duplicates(subset=["hs_code", "country"])

        # Replace NaN/inf with None so the result is JSON-serialisable.
        import numpy as _np
        results = results.replace({_np.nan: None, _np.inf: None, -_np.inf: None})

        return results.head(limit).to_dict(orient="records")

# Singleton for backend use
_engine = None

def get_search_engine() -> TariffSearchEngine:
    global _engine
    if _engine is None:
        # Determine path relative to backend root
        base_path = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        data_path = os.path.join(base_path, "tariff_engine", "normalized")
        _engine = TariffSearchEngine(data_path)
    return _engine
