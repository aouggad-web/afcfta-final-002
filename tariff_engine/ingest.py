from pathlib import Path

import pandas as pd
import requests

BASE = Path("tariff_engine")
PDF_DIR = BASE / "pdf_sources"
NORM_DIR = BASE / "normalized"

PDF_DIR.mkdir(exist_ok=True, parents=True)
NORM_DIR.mkdir(exist_ok=True, parents=True)


def download(url: str, out: Path) -> None:
    if out.exists() and out.stat().st_size > 0:
        print("Already downloaded:", out)
        return

    print("Downloading:", url)

    # TLS toujours vérifié (audit INFO-7) : plus de nouvel essai sans
    # vérification, qui laissait un intermédiaire réseau substituer le PDF
    # tarifaire. Un serveur qui n'envoie pas son certificat intermédiaire se
    # traite en fournissant celui-ci (voir scripts/releve_dgd_dza.py).
    r = requests.get(url, timeout=90, headers={"User-Agent": "Mozilla/5.0 (TariffBot/1.0)"})
    r.raise_for_status()
    out.write_bytes(r.content)
    print("Saved:", out, f"({out.stat().st_size} bytes)")


def ingest_row(row: dict) -> None:
    bloc = row["bloc"]
    parser = row["parser"]
    pdf_url = row["pdf_url"]

    bloc_dir = PDF_DIR / bloc
    bloc_dir.mkdir(exist_ok=True, parents=True)

    pdf_path = bloc_dir / f"{bloc}.pdf"
    download(pdf_url, pdf_path)

    out_csv = NORM_DIR / f"{bloc}_MASTER.csv"

    if parser == "eac":
        # Ici tu peux pointer vers ton parser "production"
        # Pour l'instant, on réutilise celui qui marche déjà sur ton PDF EAC.
        from tariff_engine.parsers.eac_parser_v1_2 import run_to_csv

        # Extraction ciblée 14-80 (rapide)
        pages = list(range(14, 81))
        run_to_csv(str(pdf_path), str(out_csv), pages=pages)
        print("Parsed ->", out_csv)
    else:
        raise ValueError(f"Unknown parser: {parser}")


def main():
    reg = pd.read_csv("registry.csv").fillna("")
    for _, r in reg.iterrows():
        ingest_row(r.to_dict())


if __name__ == "__main__":
    main()
