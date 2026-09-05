"""
Optimized Tariff Search Engine for AfCFTA.
Dynamically loads data from the tariff engine and provides high-performance search.
"""

import os
import re
from difflib import SequenceMatcher
from typing import Any, Dict, List, Optional

import pandas as pd


class TariffSearchEngine:
    def __init__(self, data_dir: str = "tariff_engine/normalized"):
        self.data_dir = data_dir
        self.df = pd.DataFrame()
        self.load_data()

    def load_data(self):
        """
        Loads all normalized tariff CSV files into a central searchable DataFrame.
        """
        all_data = []
        if not os.path.exists(self.data_dir):
            # Fallback to a sample if directory is empty (initial setup)
            self.df = pd.DataFrame(
                columns=["hs_code", "description", "duty_rate_pct", "country", "bloc"]
            )
            return

        for file in os.listdir(self.data_dir):
            if file.endswith(".csv"):
                try:
                    temp_df = pd.read_csv(os.path.join(self.data_dir, file))
                    all_data.append(temp_df)
                except Exception as e:
                    print(f"Error loading {file}: {e}")

        if all_data:
            self.df = pd.concat(all_data, ignore_index=True)
            # Ensure descriptions are strings for searching
            self.df["description"] = self.df["description"].fillna("").astype(str)
            print(f"TariffSearchEngine: Loaded {len(self.df)} tariff positions.")

    def search(
        self, query: str, country: Optional[str] = None, limit: int = 20
    ) -> List[Dict[str, Any]]:
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
            self.df["temp_ratio"] = (
                self.df["description"]
                .str.lower()
                .apply(lambda x: SequenceMatcher(None, query, x).ratio())
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
        results = results.sort_values(by="score", ascending=False).drop_duplicates(
            subset=["hs_code", "country"]
        )

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
