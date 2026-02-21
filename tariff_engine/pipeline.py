import pandas as pd
from tariff_engine.parsers.eac_parser import parse as parse_eac
from tariff_engine.normalizer.normalize_eac import normalize

def run():
    reg = pd.read_csv("tariff_engine/registry.csv")

    for _, r in reg.iterrows():
        bloc = r["bloc"]
        country = r["country"]
        hs_version = r["hs_version"]
        pdf_path = r["local_path"]
        parser = r["parser"]

        raw_out = f"tariff_engine/raw_tables/{bloc}_raw.csv"
        norm_out = f"tariff_engine/normalized/{bloc}_norm.csv"

        if parser == "eac_parser":
            parse_eac(pdf_path, raw_out)
        else:
            raise ValueError(f"Parser inconnu: {parser}")

        norm = normalize(raw_out, bloc, country, hs_version)
        norm.to_csv(norm_out, index=False)

        print(f"[OK] {bloc}: raw={raw_out} | norm={norm_out} | hs_count={len(norm)}")

if __name__ == "__main__":
    run()
