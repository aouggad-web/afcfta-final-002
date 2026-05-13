"""
Optimized Tariff Search Engine for AfCFTA.
Dynamically loads data from the tariff engine and provides high-performance search.
Fallback loader added: reads the per-country `data/tariffs/*_tariffs.json` files
when the `tariff_engine/normalized/` directory is not populated, so autocompletion
works out of the box.
"""

import json
import os
import re
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from difflib import SequenceMatcher

import pandas as pd

logger = logging.getLogger(__name__)


class TariffSearchEngine:
    def __init__(self, data_dir: str = "tariff_engine/normalized"):
        self.data_dir = data_dir
        self.df = pd.DataFrame()
        self.load_data()

    def load_data(self):
        """
        Loads tariff positions into a central searchable DataFrame.
        Order:
          1. Normalized CSVs in `tariff_engine/normalized/` (legacy engine output)
          2. Fallback: flatten per-country `data/tariffs/*_tariffs.json` files
        """
        all_data = []
        if os.path.exists(self.data_dir):
            for file in os.listdir(self.data_dir):
                if file.endswith(".csv"):
                    try:
                        temp_df = pd.read_csv(os.path.join(self.data_dir, file))
                        all_data.append(temp_df)
                    except Exception as e:
                        logger.warning("Error loading %s: %s", file, e)

        if all_data:
            self.df = pd.concat(all_data, ignore_index=True)
            self.df["description"] = self.df["description"].fillna("").astype(str)
            logger.info("TariffSearchEngine: Loaded %s tariff positions from normalized CSVs.", len(self.df))
            return

        # ── Fallback: load from per-country tariff JSON files ────────────────
        backend_dir = Path(__file__).resolve().parent.parent
        candidates = [
            backend_dir / "data" / "tariffs",
            backend_dir.parent / "data" / "tariffs",
            backend_dir.parent / "backend" / "data" / "tariffs",
        ]
        tariffs_dir = next((c for c in candidates if c.exists()), None)
        if not tariffs_dir:
            self.df = pd.DataFrame(columns=["hs_code", "description", "duty_rate_pct", "country", "bloc"])
            return

        rows = []
        for json_path in sorted(tariffs_dir.glob("*_tariffs.json")):
            try:
                with open(json_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception as e:
                logger.warning("Error reading %s: %s", json_path.name, e)
                continue
            country_code = data.get("country_code") or json_path.stem.split("_")[0]
            lines = data.get("tariff_lines") or []
            for line in lines:
                hs_code = str(line.get("hs6") or line.get("hs_code") or line.get("code") or "").strip()
                hs_code = hs_code.replace(" ", "").replace(".", "")
                if not hs_code:
                    continue
                description = (
                    line.get("description_fr")
                    or line.get("description_en")
                    or line.get("description")
                    or ""
                )
                duty = line.get("dd_rate") or line.get("dd") or line.get("duty_rate_pct")
                rows.append({
                    "hs_code": hs_code,
                    "description": description or "",
                    "duty_rate_pct": duty,
                    "country": country_code,
                    "bloc": "AfCFTA",
                })
                # Also index the country-specific sub-positions (full national HS codes)
                for sp in line.get("sub_positions") or []:
                    sp_code = str(sp.get("hs_code") or sp.get("code") or "").strip().replace(" ", "").replace(".", "")
                    if not sp_code or sp_code == hs_code:
                        continue
                    sp_desc = (
                        sp.get("description_fr")
                        or sp.get("description_en")
                        or sp.get("description")
                        or description
                        or ""
                    )
                    sp_duty = sp.get("dd") or sp.get("dd_rate") or duty
                    rows.append({
                        "hs_code": sp_code,
                        "description": sp_desc,
                        "duty_rate_pct": sp_duty,
                        "country": country_code,
                        "bloc": "AfCFTA",
                    })

        if rows:
            self.df = pd.DataFrame(rows)
            self.df["description"] = self.df["description"].fillna("").astype(str)
            logger.info("TariffSearchEngine: Loaded %s positions from %s (fallback).", len(self.df), tariffs_dir)
        else:
            self.df = pd.DataFrame(columns=["hs_code", "description", "duty_rate_pct", "country", "bloc"])

    def search(self, query: str, country: Optional[str] = None, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Hybrid search: Handles exact HS codes, partial codes, and fuzzy descriptions.
        """
        if self.df.empty:
            return []

        query = query.strip().lower()
        results = pd.DataFrame()

        # 1. HS Code match (prefix > contains)
        hs_query = re.sub(r"[^0-9]", "", query)
        if hs_query:
            code_str = self.df["hs_code"].astype(str)
            starts_mask = code_str.str.startswith(hs_query)
            prefix_matches = self.df[starts_mask].copy()
            prefix_matches["score"] = 2.0  # strongest
            # prefer shorter codes (HS6 > HS8 > HS10) to surface the broad heading first
            prefix_matches["score"] = prefix_matches["score"] - (
                prefix_matches["hs_code"].astype(str).str.len() * 0.001
            )
            results = pd.concat([results, prefix_matches])

            # Contains (but not starts-with) — weaker
            contains_mask = code_str.str.contains(hs_query) & ~starts_mask
            contains_matches = self.df[contains_mask].copy()
            if not contains_matches.empty:
                contains_matches["score"] = 0.5
                results = pd.concat([results, contains_matches])

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
            results = results[results["country"].fillna("").astype(str).str.upper() == country.upper()]

        # Deduplicate and sort by score
        results = results.sort_values(by="score", ascending=False).drop_duplicates(subset=["hs_code", "country"])
        
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
