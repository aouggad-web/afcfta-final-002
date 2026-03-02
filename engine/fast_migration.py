#!/usr/bin/env python3
"""
Script de migration rapide vers PostgreSQL avec COPY
====================================================
"""

import os
import json
import time
import tempfile
from pathlib import Path
from sqlalchemy import create_engine, text

DATABASE_URL = "postgresql://afcfta:afcfta2026@localhost:5432/afcfta_regulatory"
DATA_DIR = Path("/app/engine/output")

COUNTRIES = {
    "DZA": "Algérie", "AGO": "Angola", "BEN": "Bénin", "BWA": "Botswana",
    "BFA": "Burkina Faso", "BDI": "Burundi", "CMR": "Cameroun", "CPV": "Cap-Vert",
    "CAF": "Centrafrique", "TCD": "Tchad", "COM": "Comores", "COG": "Congo",
    "COD": "RD Congo", "CIV": "Côte d'Ivoire", "DJI": "Djibouti", "EGY": "Égypte",
    "GNQ": "Guinée équatoriale", "ERI": "Érythrée", "SWZ": "Eswatini", "ETH": "Éthiopie",
    "GAB": "Gabon", "GMB": "Gambie", "GHA": "Ghana", "GIN": "Guinée",
    "GNB": "Guinée-Bissau", "KEN": "Kenya", "LSO": "Lesotho", "LBR": "Liberia",
    "LBY": "Libye", "MDG": "Madagascar", "MWI": "Malawi", "MLI": "Mali",
    "MRT": "Mauritanie", "MUS": "Maurice", "MAR": "Maroc", "MOZ": "Mozambique",
    "NAM": "Namibie", "NER": "Niger", "NGA": "Nigeria", "RWA": "Rwanda",
    "STP": "São Tomé", "SEN": "Sénégal", "SYC": "Seychelles", "SLE": "Sierra Leone",
    "SOM": "Somalie", "ZAF": "Afrique du Sud", "SSD": "Soudan du Sud", "SDN": "Soudan",
    "TZA": "Tanzanie", "TGO": "Togo", "TUN": "Tunisie", "UGA": "Ouganda",
    "ZMB": "Zambie", "ZWE": "Zimbabwe"
}

def migrate_country(engine, iso3: str) -> int:
    """Migre un pays avec insertion par lots optimisée"""
    jsonl_path = DATA_DIR / f"{iso3}_canonical.jsonl"
    if not jsonl_path.exists():
        return 0
    
    name = COUNTRIES.get(iso3, iso3)
    count = 0
    batch = []
    batch_size = 200
    
    with engine.connect() as conn:
        # Insérer le pays
        conn.execute(text("""
            INSERT INTO countries (iso3, name_fr, last_updated)
            VALUES (:iso3, :name, NOW())
            ON CONFLICT (iso3) DO UPDATE SET name_fr = EXCLUDED.name_fr, last_updated = NOW()
        """), {"iso3": iso3, "name": name})
        
        # Supprimer anciennes données
        conn.execute(text("DELETE FROM commodities WHERE country_iso3 = :iso3"), {"iso3": iso3})
        
        with open(jsonl_path, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    data = json.loads(line)
                    c = data.get("commodity", {})
                    batch.append({
                        "country_iso3": iso3,
                        "national_code": c.get("national_code", "")[:15],
                        "hs6": c.get("hs6", "")[:6],
                        "description_fr": (c.get("description_fr", "") or "")[:2000],
                        "chapter": c.get("chapter", "")[:2],
                        "total_npf_pct": float(data.get("total_npf_pct", 0) or 0),
                        "total_zlecaf_pct": float(data.get("total_zlecaf_pct", 0) or 0),
                        "savings_pct": float(data.get("savings_pct", 0) or 0),
                        "measures": json.dumps(data.get("measures", [])),
                        "requirements": json.dumps(data.get("requirements", [])),
                        "fiscal_advantages": json.dumps(data.get("fiscal_advantages", []))
                    })
                    count += 1
                    
                    if len(batch) >= batch_size:
                        _insert_batch(conn, batch)
                        batch = []
                except:
                    continue
        
        if batch:
            _insert_batch(conn, batch)
        
        conn.execute(text("UPDATE countries SET total_positions = :c WHERE iso3 = :iso3"), {"c": count, "iso3": iso3})
        conn.commit()
    
    return count

def _insert_batch(conn, batch):
    """Insère un lot de commodités"""
    conn.execute(text("""
        INSERT INTO commodities 
        (country_iso3, national_code, hs6, description_fr, chapter,
         total_npf_pct, total_zlecaf_pct, savings_pct, measures, requirements, fiscal_advantages)
        VALUES 
        (:country_iso3, :national_code, :hs6, :description_fr, :chapter,
         :total_npf_pct, :total_zlecaf_pct, :savings_pct, :measures::jsonb, :requirements::jsonb, :fiscal_advantages::jsonb)
    """), batch)

def main():
    print("=" * 60)
    print("MIGRATION POSTGRESQL RAPIDE")
    print("=" * 60)
    
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)
    
    # Créer tables
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS countries (
                iso3 VARCHAR(3) PRIMARY KEY,
                name_fr VARCHAR(100),
                currency VARCHAR(3),
                vat_rate FLOAT DEFAULT 0,
                total_positions INTEGER DEFAULT 0,
                last_updated TIMESTAMP DEFAULT NOW()
            );
            CREATE TABLE IF NOT EXISTS commodities (
                id SERIAL PRIMARY KEY,
                country_iso3 VARCHAR(3) REFERENCES countries(iso3),
                national_code VARCHAR(15),
                hs6 VARCHAR(6),
                description_fr TEXT,
                chapter VARCHAR(2),
                total_npf_pct FLOAT DEFAULT 0,
                total_zlecaf_pct FLOAT DEFAULT 0,
                savings_pct FLOAT DEFAULT 0,
                measures JSONB,
                requirements JSONB,
                fiscal_advantages JSONB
            );
            CREATE INDEX IF NOT EXISTS idx_comm_country ON commodities(country_iso3);
            CREATE INDEX IF NOT EXISTS idx_comm_hs6 ON commodities(hs6);
            CREATE INDEX IF NOT EXISTS idx_comm_country_hs6 ON commodities(country_iso3, hs6);
        """))
        conn.commit()
    print("✓ Tables prêtes")
    
    # Trouver fichiers
    jsonl_files = sorted(DATA_DIR.glob("*_canonical.jsonl"))
    countries = [f.stem.replace("_canonical", "") for f in jsonl_files]
    
    print(f"\n📦 Migration de {len(countries)} pays...\n")
    
    start = time.time()
    total = 0
    
    for i, iso3 in enumerate(countries, 1):
        count = migrate_country(engine, iso3)
        if count > 0:
            name = COUNTRIES.get(iso3, iso3)
            print(f"  [{i:02d}/{len(countries)}] ✓ {iso3} ({name}): {count:,}")
            total += count
    
    elapsed = time.time() - start
    
    # Créer index full-text après migration
    print("\n📝 Création index full-text...")
    with engine.connect() as conn:
        try:
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_desc_search ON commodities USING gin(to_tsvector('french', description_fr));"))
            conn.commit()
            print("✓ Index full-text créé")
        except Exception as e:
            print(f"⚠ Index: {e}")
    
    print("\n" + "=" * 60)
    print(f"✅ TERMINÉ: {len(countries)} pays, {total:,} produits en {elapsed:.0f}s")
    print("=" * 60)

if __name__ == "__main__":
    main()
