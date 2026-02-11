import json
from pathlib import Path
from fastapi import FastAPI, HTTPException

DATA_DIR = Path("tariff_engine/normalized")

app = FastAPI(title="Tariff API (multi-blocs)")

_cache = {}

def load_bloc(bloc: str):
    bloc = bloc.upper().strip()

    # Convention de nommage
    candidates = [
        DATA_DIR / f"{bloc}_MASTER_indexed.json",
        DATA_DIR / f"{bloc}_MASTER_14_80_indexed.json",
        DATA_DIR / f"{bloc}_MASTER_indexed.json".lower(),
    ]

    for p in candidates:
        if p.exists():
            if bloc not in _cache:
                _cache[bloc] = json.loads(p.read_text(encoding="utf-8"))
            return _cache[bloc], str(p)

    raise FileNotFoundError(f"No indexed JSON found for bloc={bloc}. Expected one of: {', '.join(str(x) for x in candidates)}")

@app.get("/api/tariff/{bloc}")
def get_tariff(bloc: str, hs: str):
    try:
        data, src = load_bloc(bloc)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

    key = hs.replace(".", "").strip()
    row = data.get(key)
    if not row:
        raise HTTPException(status_code=404, detail={"error": "not found", "bloc": bloc.upper(), "hs": key, "source": src})

    # ajoute une trace utile côté client
    row["_bloc"] = bloc.upper()
    row["_dataset"] = src
    return row
