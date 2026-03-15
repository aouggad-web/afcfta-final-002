"""
Service PostgreSQL pour les données tarifaires
Remplace la lecture des fichiers JSONL par des requêtes PostgreSQL
"""

import os
import logging
from typing import Optional, List, Dict, Any
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from functools import lru_cache
from datetime import datetime

logger = logging.getLogger(__name__)

DATABASE_URL = os.environ.get(
    "POSTGRES_URL",
    "postgresql://afcfta:afcfta2026@localhost:5432/afcfta_regulatory"
)

# Global engine and session factory
_engine = None
_SessionFactory = None

def get_engine():
    """Get or create SQLAlchemy engine"""
    global _engine
    if _engine is None:
        _engine = create_engine(DATABASE_URL, echo=False, pool_pre_ping=True, pool_size=10)
    return _engine

def get_session():
    """Get a new database session"""
    global _SessionFactory
    if _SessionFactory is None:
        _SessionFactory = sessionmaker(bind=get_engine())
    return _SessionFactory()


class PostgresTariffService:
    """Service for tariff data queries using PostgreSQL"""
    
    def __init__(self):
        self._engine = get_engine()
    
    def _execute_query(self, query: str, params: dict = None) -> List[Dict]:
        """Execute a query and return results as list of dicts"""
        with get_session() as session:
            try:
                result = session.execute(text(query), params or {})
                columns = result.keys()
                return [dict(zip(columns, row)) for row in result.fetchall()]
            except Exception as e:
                logger.error(f"Query error: {e}")
                return []
    
    def get_countries(self) -> List[Dict]:
        """Get list of all countries with data"""
        return self._execute_query("""
            SELECT iso3, name_fr, name_en, currency, vat_rate, total_positions, last_updated
            FROM countries
            ORDER BY name_fr
        """)
    
    def get_country_info(self, iso3: str) -> Optional[Dict]:
        """Get country information"""
        results = self._execute_query("""
            SELECT iso3, name_fr, name_en, currency, vat_rate, total_positions, 
                   chapters_covered, last_updated
            FROM countries
            WHERE iso3 = :iso3
        """, {'iso3': iso3.upper()})
        return results[0] if results else None
    
    def get_sub_positions(self, country_iso3: str, hs6: str, language: str = 'fr') -> List[Dict]:
        """Get national sub-positions for a HS6 code"""
        query = """
            SELECT 
                c.national_code as code,
                c.digits,
                c.description_fr,
                c.description_en,
                c.total_npf_pct as dd_rate,
                c.total_zlecaf_pct as zlecaf_rate,
                c.savings_pct,
                c.unit
            FROM commodities c
            WHERE c.country_iso3 = :iso3 AND c.hs6 = :hs6
            ORDER BY c.national_code
        """
        results = self._execute_query(query, {'iso3': country_iso3.upper(), 'hs6': hs6})
        
        # Format for frontend
        formatted = []
        for r in results:
            desc = r['description_fr'] if language == 'fr' else (r['description_en'] or r['description_fr'])
            formatted.append({
                'code': r['code'],
                'digits': r['digits'],
                'description_fr': r['description_fr'],
                'description_en': r['description_en'] or r['description_fr'],
                'dd': r['dd_rate'],
                'zlecaf_rate': r['zlecaf_rate'],
                'savings': r['savings_pct'],
                'unit': r['unit']
            })
        
        return formatted
    
    def get_commodity_details(self, country_iso3: str, national_code: str) -> Optional[Dict]:
        """Get full commodity details including measures and requirements"""
        # Get commodity
        commodities = self._execute_query("""
            SELECT id, country_iso3, national_code, hs6, digits, description_fr, description_en,
                   chapter, category, unit, sensitivity, total_npf_pct, total_zlecaf_pct, savings_pct
            FROM commodities
            WHERE country_iso3 = :iso3 AND national_code = :code
        """, {'iso3': country_iso3.upper(), 'code': national_code})
        
        if not commodities:
            return None
        
        commodity = commodities[0]
        commodity_id = commodity['id']
        
        # Get measures
        measures = self._execute_query("""
            SELECT measure_type, code, name_fr, name_en, rate_pct, 
                   is_zlecaf_applicable, zlecaf_rate_pct, observation
            FROM measures
            WHERE commodity_id = :id
        """, {'id': commodity_id})
        
        # Get requirements
        requirements = self._execute_query("""
            SELECT requirement_type, code, document_fr, document_en, 
                   is_mandatory, issuing_authority
            FROM requirements
            WHERE commodity_id = :id
        """, {'id': commodity_id})
        
        # Get fiscal advantages
        fiscal = self._execute_query("""
            SELECT tax_code, reduced_rate_pct, condition_fr, condition_en
            FROM fiscal_advantages
            WHERE commodity_id = :id
        """, {'id': commodity_id})
        
        return {
            'commodity': {
                'country_iso3': commodity['country_iso3'],
                'national_code': commodity['national_code'],
                'hs6': commodity['hs6'],
                'digits': commodity['digits'],
                'description_fr': commodity['description_fr'],
                'description_en': commodity['description_en'],
                'chapter': commodity['chapter'],
                'category': commodity['category'],
                'unit': commodity['unit'],
                'sensitivity': commodity['sensitivity']
            },
            'taxes': {
                'total_npf': commodity['total_npf_pct'],
                'total_zlecaf': commodity['total_zlecaf_pct'],
                'savings': commodity['savings_pct']
            },
            'measures': [
                {
                    'type': m['measure_type'],
                    'code': m['code'],
                    'name_fr': m['name_fr'],
                    'name_en': m['name_en'],
                    'rate': m['rate_pct'],
                    'is_zlecaf': m['is_zlecaf_applicable'],
                    'zlecaf_rate': m['zlecaf_rate_pct']
                }
                for m in measures
            ],
            'requirements': [
                {
                    'type': r['requirement_type'],
                    'code': r['code'],
                    'document_fr': r['document_fr'],
                    'document_en': r['document_en'],
                    'mandatory': r['is_mandatory'],
                    'authority': r['issuing_authority']
                }
                for r in requirements
            ],
            'fiscal_advantages': [
                {
                    'tax_code': f['tax_code'],
                    'reduced_rate': f['reduced_rate_pct'],
                    'condition_fr': f['condition_fr'],
                    'condition_en': f['condition_en']
                }
                for f in fiscal
            ]
        }
    
    def search_commodities(self, country_iso3: str, query: str, limit: int = 50, language: str = 'fr') -> List[Dict]:
        """Full-text search for commodities"""
        search_query = """
            SELECT national_code, hs6, description_fr, description_en, 
                   total_npf_pct, total_zlecaf_pct, savings_pct,
                   ts_rank(to_tsvector('french', description_fr), plainto_tsquery('french', :query)) as rank
            FROM commodities
            WHERE country_iso3 = :iso3 
              AND to_tsvector('french', description_fr) @@ plainto_tsquery('french', :query)
            ORDER BY rank DESC
            LIMIT :limit
        """
        
        results = self._execute_query(search_query, {
            'iso3': country_iso3.upper(),
            'query': query,
            'limit': limit
        })
        
        return [
            {
                'code': r['national_code'],
                'hs6': r['hs6'],
                'description': r['description_fr'] if language == 'fr' else (r['description_en'] or r['description_fr']),
                'dd_rate': r['total_npf_pct'],
                'zlecaf_rate': r['total_zlecaf_pct'],
                'savings': r['savings_pct']
            }
            for r in results
        ]
    
    def calculate_tariffs(self, country_iso3: str, hs6: str, value: float = 1000) -> Dict:
        """Calculate tariffs for a HS6 code"""
        # Get all sub-positions
        sub_positions = self.get_sub_positions(country_iso3, hs6)
        
        if not sub_positions:
            return {
                'success': False,
                'error': f'No data found for {country_iso3}/{hs6}'
            }
        
        # Get country info
        country = self.get_country_info(country_iso3)
        
        # Calculate for each sub-position
        calculations = []
        for sp in sub_positions:
            dd_rate = sp.get('dd', 0) or 0
            zlecaf_rate = sp.get('zlecaf_rate', 0) or 0
            
            npf_duty = value * (dd_rate / 100)
            zlecaf_duty = value * (zlecaf_rate / 100)
            savings = npf_duty - zlecaf_duty
            
            calculations.append({
                'code': sp['code'],
                'description': sp['description_fr'],
                'dd_rate': dd_rate,
                'zlecaf_rate': zlecaf_rate,
                'npf_duty': round(npf_duty, 2),
                'zlecaf_duty': round(zlecaf_duty, 2),
                'savings': round(savings, 2),
                'savings_pct': round((savings / npf_duty * 100) if npf_duty > 0 else 0, 1)
            })
        
        # Calculate average
        avg_dd = sum(c['dd_rate'] for c in calculations) / len(calculations) if calculations else 0
        total_npf = sum(c['npf_duty'] for c in calculations) / len(calculations) if calculations else 0
        total_zlecaf = sum(c['zlecaf_duty'] for c in calculations) / len(calculations) if calculations else 0
        
        return {
            'success': True,
            'country': {
                'iso3': country_iso3,
                'name': country['name_fr'] if country else country_iso3,
                'currency': country['currency'] if country else 'USD',
                'vat_rate': country['vat_rate'] if country else 0
            },
            'hs6': hs6,
            'value': value,
            'sub_positions': calculations,
            'summary': {
                'avg_dd_rate': round(avg_dd, 2),
                'total_npf': round(total_npf, 2),
                'total_zlecaf': round(total_zlecaf, 2),
                'total_savings': round(total_npf - total_zlecaf, 2)
            }
        }
    
    def get_regulatory_details(self, country_iso3: str, hs6: str) -> Dict:
        """Get regulatory details for a HS6 code"""
        # Get main commodity info
        commodities = self._execute_query("""
            SELECT id, national_code, description_fr, description_en, 
                   total_npf_pct, total_zlecaf_pct
            FROM commodities
            WHERE country_iso3 = :iso3 AND hs6 = :hs6
            LIMIT 1
        """, {'iso3': country_iso3.upper(), 'hs6': hs6})
        
        if not commodities:
            return {'success': False, 'error': 'No data found'}
        
        commodity = commodities[0]
        commodity_id = commodity['id']
        
        # Get all measures
        measures = self._execute_query("""
            SELECT DISTINCT measure_type, code, name_fr, rate_pct, is_zlecaf_applicable, zlecaf_rate_pct
            FROM measures m
            JOIN commodities c ON m.commodity_id = c.id
            WHERE c.country_iso3 = :iso3 AND c.hs6 = :hs6
        """, {'iso3': country_iso3.upper(), 'hs6': hs6})
        
        # Get all requirements
        requirements = self._execute_query("""
            SELECT DISTINCT requirement_type, code, document_fr, is_mandatory, issuing_authority
            FROM requirements r
            JOIN commodities c ON r.commodity_id = c.id
            WHERE c.country_iso3 = :iso3 AND c.hs6 = :hs6
        """, {'iso3': country_iso3.upper(), 'hs6': hs6})
        
        return {
            'success': True,
            'country_iso3': country_iso3,
            'hs6': hs6,
            'description': commodity['description_fr'],
            'taxes': {
                'dd_rate': commodity['total_npf_pct'],
                'zlecaf_rate': commodity['total_zlecaf_pct']
            },
            'measures': [
                {
                    'type': m['measure_type'],
                    'code': m['code'],
                    'name': m['name_fr'],
                    'rate': m['rate_pct'],
                    'zlecaf_applicable': m['is_zlecaf_applicable'],
                    'zlecaf_rate': m['zlecaf_rate_pct']
                }
                for m in measures
            ],
            'requirements': [
                {
                    'type': r['requirement_type'],
                    'code': r['code'],
                    'document': r['document_fr'],
                    'mandatory': r['is_mandatory'],
                    'authority': r['issuing_authority']
                }
                for r in requirements
            ]
        }


# Singleton instance
_postgres_service = None

def get_postgres_tariff_service() -> PostgresTariffService:
    """Get singleton instance of PostgresTariffService"""
    global _postgres_service
    if _postgres_service is None:
        _postgres_service = PostgresTariffService()
    return _postgres_service
