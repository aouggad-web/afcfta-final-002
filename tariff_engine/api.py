import json
from pathlib import Path
from fastapi import FastAPI, HTTPException

DATA_PATH = Path("tariff_engine/normalized/EAC_MASTER_14_80_indexed.json")

app = FastAPI(title="Tariff API (EAC)")

_cache = None

def load_data():
    global _cache
    if _cache is None:
        if not DATA_PATH.exists():
            raise FileNotFoundError(f"Missing data file: {DATA_PATH}")
        _cache = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    return _cache

@app.get("/api/tariff/eac")
def get_eac(hs: str):
    data = load_data()
    key = hs.replace(".", "").strip()
    row = data.get(key)
    if not row:
        raise HTTPException(status_code=404, detail={"error": "not found", "hs": key})
    return row
