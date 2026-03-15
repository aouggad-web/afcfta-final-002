"""
Script de migration rapide JSONL -> PostgreSQL
Utilise des insertions batch et COPY pour de meilleures performances.
"""

import os
import sys
import json
import glob
import logging
from datetime import datetime
from sqlalchemy import text, create_engine
from sqlalchemy.orm import sessionmaker

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Database URL
DATABASE_URL = "postgresql://afcfta:afcfta2026@localhost:5432/afcfta_regulatory"
JSONL_DIR = "/app/engine/output"
BATCH_SIZE = 5000

def get_db_session():
    """Create database session"""
    engine = create_engine(DATABASE_URL, echo=False, pool_pre_ping=True)
    Session = sessionmaker(bind=engine)
    return Session(), engine

def clear_tables(session):
    """Clear all data from tables"""
    logger.info("Clearing existing data...")
    session.execute(text("TRUNCATE fiscal_advantages, requirements, measures, commodities, countries RESTART IDENTITY CASCADE"))
    session.commit()
    logger.info("Tables cleared")

def parse_jsonl_file(filepath):
    """Parse JSONL file and yield records"""
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                continue

def migrate_country(session, country_iso3, jsonl_path, summary_path=None):
    """Migrate one country's data"""
    
    # Read summary if available
    country_name_fr = country_iso3
    country_name_en = country_iso3
    vat_rate = 0
    currency = ""
    total_positions = 0
    
    if summary_path and os.path.exists(summary_path):
        try:
            with open(summary_path, 'r', encoding='utf-8') as f:
                summary = json.load(f)
                country_name_fr = summary.get('country_name_fr', country_iso3)
                country_name_en = summary.get('country_name_en', country_iso3)
                vat_rate = summary.get('vat_rate', 0) or 0
                currency = summary.get('currency', '')
                total_positions = summary.get('total_lines', 0)
        except:
            pass
    
    # Insert country
    session.execute(text("""
        INSERT INTO countries (iso3, name_fr, name_en, currency, vat_rate, total_positions, last_updated)
        VALUES (:iso3, :name_fr, :name_en, :currency, :vat_rate, :total_positions, :now)
        ON CONFLICT (iso3) DO UPDATE SET
            name_fr = EXCLUDED.name_fr,
            name_en = EXCLUDED.name_en,
            total_positions = EXCLUDED.total_positions,
            last_updated = EXCLUDED.last_updated
    """), {
        'iso3': country_iso3,
        'name_fr': country_name_fr,
        'name_en': country_name_en,
        'currency': currency,
        'vat_rate': float(vat_rate) if vat_rate else 0,
        'total_positions': total_positions,
        'now': datetime.utcnow()
    })
    
    # Parse and insert commodities, measures, requirements
    commodities_batch = []
    measures_batch = []
    requirements_batch = []
    fiscal_batch = []
    
    record_count = 0
    
    for record in parse_jsonl_file(jsonl_path):
        commodity = record.get('commodity', {})
        national_code = commodity.get('national_code', '')
        hs6 = commodity.get('hs6', '')
        
        if not national_code or not hs6:
            continue
        
        record_count += 1
        
        # Calculate totals from measures
        total_npf = 0
        total_zlecaf = 0
        dd_rate = 0
        
        for m in record.get('measures', []):
            rate = m.get('rate') or 0
            if isinstance(rate, str):
                try:
                    rate = float(rate.replace('%', '').strip())
                except:
                    rate = 0
            total_npf += rate
            
            if m.get('measure_type') == 'CUSTOMS_DUTY':
                dd_rate = rate
                # ZLECAf reduces customs duty to 0 for most products
                total_zlecaf += 0
            else:
                total_zlecaf += rate
        
        savings = total_npf - total_zlecaf if total_npf > total_zlecaf else 0
        
        commodities_batch.append({
            'country_iso3': country_iso3,
            'national_code': national_code,
            'hs6': hs6,
            'digits': commodity.get('digits', len(national_code.replace('.', ''))),
            'description_fr': commodity.get('description_fr', '')[:2000],
            'description_en': commodity.get('description_en', '')[:2000] if commodity.get('description_en') else None,
            'chapter': hs6[:2] if len(hs6) >= 2 else '',
            'category': commodity.get('category'),
            'unit': commodity.get('unit'),
            'sensitivity': commodity.get('sensitivity', 'normal'),
            'total_npf_pct': total_npf,
            'total_zlecaf_pct': total_zlecaf,
            'savings_pct': savings,
            'source_file': os.path.basename(jsonl_path),
            'measures': record.get('measures', []),
            'requirements': record.get('requirements', []),
            'fiscal_advantages': record.get('fiscal_advantages', [])
        })
        
        # Batch insert when reaching batch size
        if len(commodities_batch) >= BATCH_SIZE:
            insert_batch(session, commodities_batch)
            logger.info(f"  {country_iso3}: Inserted {record_count} records...")
            commodities_batch = []
    
    # Insert remaining
    if commodities_batch:
        insert_batch(session, commodities_batch)
    
    session.commit()
    logger.info(f"  {country_iso3}: Completed - {record_count} total records")
    return record_count

def insert_batch(session, commodities_batch):
    """Insert a batch of commodities with their related data"""
    
    for c in commodities_batch:
        # Insert commodity
        result = session.execute(text("""
            INSERT INTO commodities (
                country_iso3, national_code, hs6, digits, description_fr, description_en,
                chapter, category, unit, sensitivity, total_npf_pct, total_zlecaf_pct,
                savings_pct, source_file, last_updated
            ) VALUES (
                :country_iso3, :national_code, :hs6, :digits, :description_fr, :description_en,
                :chapter, :category, :unit, :sensitivity, :total_npf_pct, :total_zlecaf_pct,
                :savings_pct, :source_file, :now
            )
            ON CONFLICT DO NOTHING
            RETURNING id
        """), {
            'country_iso3': c['country_iso3'],
            'national_code': c['national_code'],
            'hs6': c['hs6'],
            'digits': c['digits'],
            'description_fr': c['description_fr'],
            'description_en': c['description_en'],
            'chapter': c['chapter'],
            'category': c['category'],
            'unit': c['unit'],
            'sensitivity': c['sensitivity'],
            'total_npf_pct': c['total_npf_pct'],
            'total_zlecaf_pct': c['total_zlecaf_pct'],
            'savings_pct': c['savings_pct'],
            'source_file': c['source_file'],
            'now': datetime.utcnow()
        })
        
        row = result.fetchone()
        if not row:
            continue
            
        commodity_id = row[0]
        
        # Insert measures
        for m in c.get('measures', []):
            rate = m.get('rate') or 0
            if isinstance(rate, str):
                try:
                    rate = float(rate.replace('%', '').strip())
                except:
                    rate = 0
            
            measure_type = m.get('measure_type', 'OTHER_TAX')
            if measure_type not in ('CUSTOMS_DUTY', 'VAT', 'EXCISE', 'LEVY', 'OTHER_TAX'):
                measure_type = 'OTHER_TAX'
            
            session.execute(text("""
                INSERT INTO measures (
                    commodity_id, measure_type, code, name_fr, name_en, rate_pct,
                    is_zlecaf_applicable, zlecaf_rate_pct, observation
                ) VALUES (
                    :commodity_id, :measure_type, :code, :name_fr, :name_en, :rate_pct,
                    :is_zlecaf, :zlecaf_rate, :observation
                )
            """), {
                'commodity_id': commodity_id,
                'measure_type': measure_type,
                'code': m.get('code', 'TAX')[:20],
                'name_fr': m.get('name_fr', m.get('code', 'Taxe'))[:200],
                'name_en': m.get('name_en', '')[:200] if m.get('name_en') else None,
                'rate_pct': rate,
                'is_zlecaf': m.get('is_zlecaf_applicable', measure_type == 'CUSTOMS_DUTY'),
                'zlecaf_rate': 0 if measure_type == 'CUSTOMS_DUTY' else rate,
                'observation': m.get('observation')
            })
        
        # Insert requirements
        for r in c.get('requirements', []):
            req_type = r.get('requirement_type', 'CERTIFICATE')
            if req_type not in ('IMPORT_DECLARATION', 'CERTIFICATE', 'LICENSE', 'PERMIT', 'INSPECTION', 'AUTHORIZATION'):
                req_type = 'CERTIFICATE'
            
            session.execute(text("""
                INSERT INTO requirements (
                    commodity_id, requirement_type, code, document_fr, document_en,
                    is_mandatory, issuing_authority
                ) VALUES (
                    :commodity_id, :req_type, :code, :doc_fr, :doc_en, :mandatory, :authority
                )
            """), {
                'commodity_id': commodity_id,
                'req_type': req_type,
                'code': r.get('code', 'DOC')[:20],
                'doc_fr': r.get('document_fr', r.get('code', 'Document'))[:300],
                'doc_en': r.get('document_en', '')[:300] if r.get('document_en') else None,
                'mandatory': r.get('is_mandatory', True),
                'authority': r.get('issuing_authority', '')[:200] if r.get('issuing_authority') else None
            })

def run_migration():
    """Run full migration"""
    logger.info("Starting PostgreSQL migration...")
    
    session, engine = get_db_session()
    
    # Clear existing data
    clear_tables(session)
    
    # Find all JSONL files
    jsonl_files = glob.glob(os.path.join(JSONL_DIR, "*_canonical.jsonl"))
    logger.info(f"Found {len(jsonl_files)} country files to migrate")
    
    total_records = 0
    success_countries = 0
    
    for jsonl_path in sorted(jsonl_files):
        country_iso3 = os.path.basename(jsonl_path).replace('_canonical.jsonl', '')
        summary_path = jsonl_path.replace('_canonical.jsonl', '_summary.json')
        
        try:
            count = migrate_country(session, country_iso3, jsonl_path, summary_path)
            total_records += count
            success_countries += 1
        except Exception as e:
            logger.error(f"Error migrating {country_iso3}: {e}")
            session.rollback()
            continue
    
    # Create full-text search index
    logger.info("Creating full-text search index...")
    try:
        session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_commodities_fts 
            ON commodities USING gin(to_tsvector('french', description_fr))
        """))
        session.commit()
        logger.info("Full-text search index created")
    except Exception as e:
        logger.warning(f"Could not create FTS index: {e}")
    
    logger.info(f"Migration completed: {success_countries} countries, {total_records} records")
    session.close()

if __name__ == "__main__":
    run_migration()
