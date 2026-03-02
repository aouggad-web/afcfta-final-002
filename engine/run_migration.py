#!/usr/bin/env python3
"""
Script de migration rapide vers PostgreSQL
==========================================
Migre les 54 pays africains depuis les fichiers JSONL vers PostgreSQL.
"""

import os
import sys
import json
import time
from pathlib import Path
from datetime import datetime

# Ajouter le répertoire parent au path
sys.path.insert(0, '/app/engine')

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Configuration
DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://afcfta:afcfta2026@localhost:5432/afcfta_regulatory"
)
DATA_DIR = Path("/app/engine/output")

# Tous les pays africains avec leurs infos
AFRICAN_COUNTRIES = {
    "DZA": {"name_fr": "Algérie", "currency": "DZD"},
    "AGO": {"name_fr": "Angola", "currency": "AOA"},
    "BEN": {"name_fr": "Bénin", "currency": "XOF"},
    "BWA": {"name_fr": "Botswana", "currency": "BWP"},
    "BFA": {"name_fr": "Burkina Faso", "currency": "XOF"},
    "BDI": {"name_fr": "Burundi", "currency": "BIF"},
    "CMR": {"name_fr": "Cameroun", "currency": "XAF"},
    "CPV": {"name_fr": "Cap-Vert", "currency": "CVE"},
    "CAF": {"name_fr": "République centrafricaine", "currency": "XAF"},
    "TCD": {"name_fr": "Tchad", "currency": "XAF"},
    "COM": {"name_fr": "Comores", "currency": "KMF"},
    "COG": {"name_fr": "Congo", "currency": "XAF"},
    "COD": {"name_fr": "RD Congo", "currency": "CDF"},
    "CIV": {"name_fr": "Côte d'Ivoire", "currency": "XOF"},
    "DJI": {"name_fr": "Djibouti", "currency": "DJF"},
    "EGY": {"name_fr": "Égypte", "currency": "EGP"},
    "GNQ": {"name_fr": "Guinée équatoriale", "currency": "XAF"},
    "ERI": {"name_fr": "Érythrée", "currency": "ERN"},
    "SWZ": {"name_fr": "Eswatini", "currency": "SZL"},
    "ETH": {"name_fr": "Éthiopie", "currency": "ETB"},
    "GAB": {"name_fr": "Gabon", "currency": "XAF"},
    "GMB": {"name_fr": "Gambie", "currency": "GMD"},
    "GHA": {"name_fr": "Ghana", "currency": "GHS"},
    "GIN": {"name_fr": "Guinée", "currency": "GNF"},
    "GNB": {"name_fr": "Guinée-Bissau", "currency": "XOF"},
    "KEN": {"name_fr": "Kenya", "currency": "KES"},
    "LSO": {"name_fr": "Lesotho", "currency": "LSL"},
    "LBR": {"name_fr": "Liberia", "currency": "LRD"},
    "LBY": {"name_fr": "Libye", "currency": "LYD"},
    "MDG": {"name_fr": "Madagascar", "currency": "MGA"},
    "MWI": {"name_fr": "Malawi", "currency": "MWK"},
    "MLI": {"name_fr": "Mali", "currency": "XOF"},
    "MRT": {"name_fr": "Mauritanie", "currency": "MRU"},
    "MUS": {"name_fr": "Maurice", "currency": "MUR"},
    "MAR": {"name_fr": "Maroc", "currency": "MAD"},
    "MOZ": {"name_fr": "Mozambique", "currency": "MZN"},
    "NAM": {"name_fr": "Namibie", "currency": "NAD"},
    "NER": {"name_fr": "Niger", "currency": "XOF"},
    "NGA": {"name_fr": "Nigeria", "currency": "NGN"},
    "RWA": {"name_fr": "Rwanda", "currency": "RWF"},
    "STP": {"name_fr": "São Tomé-et-Príncipe", "currency": "STN"},
    "SEN": {"name_fr": "Sénégal", "currency": "XOF"},
    "SYC": {"name_fr": "Seychelles", "currency": "SCR"},
    "SLE": {"name_fr": "Sierra Leone", "currency": "SLE"},
    "SOM": {"name_fr": "Somalie", "currency": "SOS"},
    "ZAF": {"name_fr": "Afrique du Sud", "currency": "ZAR"},
    "SSD": {"name_fr": "Soudan du Sud", "currency": "SSP"},
    "SDN": {"name_fr": "Soudan", "currency": "SDG"},
    "TZA": {"name_fr": "Tanzanie", "currency": "TZS"},
    "TGO": {"name_fr": "Togo", "currency": "XOF"},
    "TUN": {"name_fr": "Tunisie", "currency": "TND"},
    "UGA": {"name_fr": "Ouganda", "currency": "UGX"},
    "ZMB": {"name_fr": "Zambie", "currency": "ZMW"},
    "ZWE": {"name_fr": "Zimbabwe", "currency": "ZWL"},
}


def init_database(engine):
    """Crée les tables si nécessaires"""
    with engine.connect() as conn:
        # Créer les tables
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS countries (
                iso3 VARCHAR(3) PRIMARY KEY,
                name_fr VARCHAR(100) NOT NULL,
                currency VARCHAR(3),
                vat_rate FLOAT DEFAULT 0,
                total_positions INTEGER DEFAULT 0,
                last_updated TIMESTAMP DEFAULT NOW()
            );
            
            CREATE TABLE IF NOT EXISTS commodities (
                id SERIAL PRIMARY KEY,
                country_iso3 VARCHAR(3) REFERENCES countries(iso3) ON DELETE CASCADE,
                national_code VARCHAR(15) NOT NULL,
                hs6 VARCHAR(6) NOT NULL,
                description_fr TEXT NOT NULL,
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
            CREATE INDEX IF NOT EXISTS idx_comm_description ON commodities USING gin(to_tsvector('french', description_fr));
        """))
        conn.commit()
    print("✓ Tables créées")


def migrate_country(engine, iso3: str):
    """Migre un pays vers PostgreSQL"""
    jsonl_path = DATA_DIR / f"{iso3}_canonical.jsonl"
    
    if not jsonl_path.exists():
        print(f"  ⚠ {iso3}: Fichier non trouvé")
        return 0
    
    country_info = AFRICAN_COUNTRIES.get(iso3, {"name_fr": iso3, "currency": "USD"})
    
    with engine.connect() as conn:
        # Supprimer les anciennes données
        conn.execute(text("DELETE FROM commodities WHERE country_iso3 = :iso3"), {"iso3": iso3})
        
        # Insérer/mettre à jour le pays
        conn.execute(text("""
            INSERT INTO countries (iso3, name_fr, currency, last_updated)
            VALUES (:iso3, :name_fr, :currency, NOW())
            ON CONFLICT (iso3) DO UPDATE SET
                name_fr = EXCLUDED.name_fr,
                currency = EXCLUDED.currency,
                last_updated = NOW()
        """), {"iso3": iso3, "name_fr": country_info["name_fr"], "currency": country_info["currency"]})
        
        # Préparer les données en lot
        batch = []
        batch_size = 500
        count = 0
        
        with open(jsonl_path, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    data = json.loads(line)
                    commodity = data.get("commodity", {})
                    
                    batch.append({
                        "country_iso3": iso3,
                        "national_code": commodity.get("national_code", ""),
                        "hs6": commodity.get("hs6", ""),
                        "description_fr": commodity.get("description_fr", ""),
                        "chapter": commodity.get("chapter", ""),
                        "total_npf_pct": data.get("total_npf_pct", 0),
                        "total_zlecaf_pct": data.get("total_zlecaf_pct", 0),
                        "savings_pct": data.get("savings_pct", 0),
                        "measures": json.dumps(data.get("measures", [])),
                        "requirements": json.dumps(data.get("requirements", [])),
                        "fiscal_advantages": json.dumps(data.get("fiscal_advantages", []))
                    })
                    count += 1
                    
                    if len(batch) >= batch_size:
                        conn.execute(text("""
                            INSERT INTO commodities 
                            (country_iso3, national_code, hs6, description_fr, chapter,
                             total_npf_pct, total_zlecaf_pct, savings_pct, measures, requirements, fiscal_advantages)
                            VALUES 
                            (:country_iso3, :national_code, :hs6, :description_fr, :chapter,
                             :total_npf_pct, :total_zlecaf_pct, :savings_pct, :measures::jsonb, :requirements::jsonb, :fiscal_advantages::jsonb)
                        """), batch)
                        batch = []
                        
                except Exception as e:
                    continue
        
        # Insérer le reste
        if batch:
            conn.execute(text("""
                INSERT INTO commodities 
                (country_iso3, national_code, hs6, description_fr, chapter,
                 total_npf_pct, total_zlecaf_pct, savings_pct, measures, requirements, fiscal_advantages)
                VALUES 
                (:country_iso3, :national_code, :hs6, :description_fr, :chapter,
                 :total_npf_pct, :total_zlecaf_pct, :savings_pct, :measures::jsonb, :requirements::jsonb, :fiscal_advantages::jsonb)
            """), batch)
        
        # Mettre à jour le compteur
        conn.execute(text("""
            UPDATE countries SET total_positions = :count WHERE iso3 = :iso3
        """), {"iso3": iso3, "count": count})
        
        conn.commit()
    
    return count


def main():
    """Point d'entrée principal"""
    print("=" * 60)
    print("MIGRATION POSTGRESQL - ZLECAf Regulatory Engine")
    print("=" * 60)
    
    start_time = time.time()
    
    # Connexion
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)
    
    # Initialiser les tables
    init_database(engine)
    
    # Trouver les fichiers disponibles
    jsonl_files = list(DATA_DIR.glob("*_canonical.jsonl"))
    countries_to_migrate = [f.stem.replace("_canonical", "") for f in jsonl_files]
    
    print(f"\n📦 {len(countries_to_migrate)} pays à migrer")
    print("-" * 60)
    
    total_records = 0
    migrated_countries = 0
    
    for i, iso3 in enumerate(sorted(countries_to_migrate), 1):
        try:
            count = migrate_country(engine, iso3)
            if count > 0:
                country_name = AFRICAN_COUNTRIES.get(iso3, {}).get("name_fr", iso3)
                print(f"  [{i:02d}/{len(countries_to_migrate)}] ✓ {iso3} ({country_name}): {count:,} enregistrements")
                total_records += count
                migrated_countries += 1
        except Exception as e:
            print(f"  [{i:02d}/{len(countries_to_migrate)}] ✗ {iso3}: Erreur - {str(e)[:50]}")
    
    elapsed = time.time() - start_time
    
    print("-" * 60)
    print(f"\n✅ MIGRATION TERMINÉE")
    print(f"   • Pays migrés: {migrated_countries}")
    print(f"   • Enregistrements: {total_records:,}")
    print(f"   • Durée: {elapsed:.1f}s")
    print("=" * 60)


if __name__ == "__main__":
    main()
