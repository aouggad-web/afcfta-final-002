from concurrent.futures import ProcessPoolExecutor

import pandas as pd

from tariff_engine.normalizer.normalize_eac import normalize
from tariff_engine.parsers.eac_parser_v1_2 import run_to_csv as parse_eac


def process_country(row):
    """
    Worker function to process a single country's tariff data.
    """
    bloc, country, pdf_path = row["bloc"], row["country"], row["local_path"]
    raw_out = f"tariff_engine/raw_tables/{bloc}_raw.csv"
    norm_out = f"tariff_engine/normalized/{bloc}_norm.csv"

    try:
        print(f"Processing {country}...")
        # 1. Parse PDF to Raw CSV (Targeting pages 14-80 for EAC)
        parse_eac(pdf_path, raw_out, pages=list(range(14, 81)))

        # 2. Normalize and preserve data
        norm = normalize(raw_out, bloc, country, row["hs_version"])
        norm.to_csv(norm_out, index=False)
        return f"[OK] {country} processed: {len(norm)} lines found."
    except Exception as e:
        return f"[ERROR] {country}: {str(e)}"


def run():
    """
    Main entry point for the parallel processing pipeline.
    """
    try:
        reg = pd.read_csv("tariff_engine/registry.csv")
    except FileNotFoundError:
        print("Error: registry.csv not found in tariff_engine directory.")
        return

    print(f"Starting parallel processing for {len(reg)} countries...")

    with ProcessPoolExecutor() as executor:
        # Map processing to multiple cores
        results = list(executor.map(process_country, [r.to_dict() for _, r in reg.iterrows()]))

        # Print summary results
        for res in results:
            print(res)


if __name__ == "__main__":
    run()
