import camelot
import pandas as pd

def parse(pdf_path: str, out_csv: str) -> str:
    tables = camelot.read_pdf(pdf_path, pages="1-end", flavor="stream")
    frames = []
    for t in tables:
        df = t.df
        if df is None or df.empty:
            continue
        frames.append(df)

    if not frames:
        raise RuntimeError("Aucune table extraite. PDF peut être scanné ou structure incompatible.")

    data = pd.concat(frames, ignore_index=True)
    data.to_csv(out_csv, index=False)
    return out_csv
