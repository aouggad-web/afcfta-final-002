"""
API de Recherche Textuelle pour les Produits
=============================================
Permet de rechercher des produits par description dans la base PostgreSQL.
"""

from fastapi import APIRouter, Query, HTTPException
from typing import List, Optional
import os

router = APIRouter(prefix="/commodities")

# Configuration base de données
DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://afcfta:afcfta2026@localhost:5432/afcfta_regulatory"
)

# Flag pour savoir si PostgreSQL est disponible
POSTGRES_AVAILABLE = False
engine = None
SessionLocal = None

try:
    from sqlalchemy import create_engine, text
    from sqlalchemy.orm import sessionmaker
    
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)
    SessionLocal = sessionmaker(bind=engine)
    
    # Tester la connexion
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    POSTGRES_AVAILABLE = True
except Exception as e:
    print(f"PostgreSQL non disponible: {e}")


def get_db():
    """Crée une session de base de données"""
    if not POSTGRES_AVAILABLE:
        return None
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/search")
async def search_commodities(
    q: str = Query(..., min_length=2, description="Terme de recherche (minimum 2 caractères)"),
    country: Optional[str] = Query(None, description="Code ISO3 du pays (optionnel)"),
    lang: str = Query("fr", description="Langue de recherche: 'fr' (français) ou 'en' (anglais)"),
    limit: int = Query(50, ge=1, le=200, description="Nombre maximum de résultats"),
    offset: int = Query(0, ge=0, description="Décalage pour la pagination")
):
    """
    Recherche textuelle dans les descriptions de produits.
    
    Utilise la recherche full-text PostgreSQL avec support du français ET anglais.
    
    Exemples:
    - `/api/commodities/search?q=café` (français par défaut)
    - `/api/commodities/search?q=coffee&lang=en` (anglais)
    - `/api/commodities/search?q=véhicule&country=SEN`
    - `/api/commodities/search?q=vehicle&country=SEN&lang=en`
    """
    if not POSTGRES_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Base de données PostgreSQL non disponible. Migration en cours."
        )
    
    try:
        with engine.connect() as conn:
            # Déterminer la langue de recherche
            ts_config = 'french' if lang == 'fr' else 'english'
            
            # Construire la requête
            base_query = f"""
                SELECT 
                    c.id,
                    c.country_iso3,
                    co.name_fr as country_name,
                    c.national_code,
                    c.hs6,
                    c.description_fr,
                    c.chapter,
                    c.total_npf_pct,
                    c.total_zlecaf_pct,
                    c.savings_pct,
                    ts_rank(to_tsvector('{ts_config}', c.description_fr), plainto_tsquery('{ts_config}', :query)) as rank
                FROM commodities c
                JOIN countries co ON c.country_iso3 = co.iso3
                WHERE to_tsvector('{ts_config}', c.description_fr) @@ plainto_tsquery('{ts_config}', :query)
            """
            
            params = {"query": q, "limit": limit, "offset": offset}
            
            # Filtrer par pays si spécifié
            if country:
                base_query += " AND c.country_iso3 = :country"
                params["country"] = country.upper()
            
            # Ordonner par pertinence et limiter
            base_query += " ORDER BY rank DESC, c.hs6 LIMIT :limit OFFSET :offset"
            
            result = conn.execute(text(base_query), params)
            rows = result.fetchall()
            
            # Compter le total (pour la pagination)
            count_query = f"""
                SELECT COUNT(*) FROM commodities c
                WHERE to_tsvector('{ts_config}', c.description_fr) @@ plainto_tsquery('{ts_config}', :query)
            """
            if country:
                count_query += " AND c.country_iso3 = :country"
            
            total_result = conn.execute(text(count_query), params)
            total = total_result.scalar()
            
            # Formater les résultats
            results = []
            for row in rows:
                results.append({
                    "id": row.id,
                    "country_iso3": row.country_iso3,
                    "country_name": row.country_name,
                    "national_code": row.national_code,
                    "hs6": row.hs6,
                    "description": row.description_fr,
                    "chapter": row.chapter,
                    "tariffs": {
                        "npf_rate": row.total_npf_pct,
                        "zlecaf_rate": row.total_zlecaf_pct,
                        "savings_pct": row.savings_pct
                    },
                    "relevance_score": round(row.rank, 4) if row.rank else 0
                })
            
            return {
                "query": q,
                "country_filter": country,
                "total_results": total,
                "limit": limit,
                "offset": offset,
                "results": results
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur de recherche: {str(e)}")


@router.get("/search/simple")
async def simple_search(
    q: str = Query(..., min_length=2, description="Terme de recherche"),
    country: str = Query(..., description="Code ISO3 du pays"),
    limit: int = Query(30, ge=1, le=100)
):
    """
    Recherche simple par correspondance partielle (ILIKE).
    Plus rapide mais moins précise que la recherche full-text.
    """
    if not POSTGRES_AVAILABLE:
        raise HTTPException(status_code=503, detail="PostgreSQL non disponible")
    
    try:
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT 
                    national_code,
                    hs6,
                    description_fr,
                    chapter,
                    total_npf_pct,
                    total_zlecaf_pct,
                    savings_pct
                FROM commodities
                WHERE country_iso3 = :country
                AND description_fr ILIKE :pattern
                ORDER BY hs6
                LIMIT :limit
            """), {
                "country": country.upper(),
                "pattern": f"%{q}%",
                "limit": limit
            })
            
            rows = result.fetchall()
            
            return {
                "query": q,
                "country": country.upper(),
                "count": len(rows),
                "results": [
                    {
                        "national_code": row.national_code,
                        "hs6": row.hs6,
                        "description": row.description_fr,
                        "chapter": row.chapter,
                        "npf_rate": row.total_npf_pct,
                        "zlecaf_rate": row.total_zlecaf_pct,
                        "savings_pct": row.savings_pct
                    }
                    for row in rows
                ]
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/countries")
async def get_available_countries():
    """
    Retourne la liste des pays disponibles dans la base PostgreSQL.
    """
    if not POSTGRES_AVAILABLE:
        raise HTTPException(status_code=503, detail="PostgreSQL non disponible")
    
    try:
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT iso3, name_fr, currency, total_positions, last_updated
                FROM countries
                ORDER BY name_fr
            """))
            rows = result.fetchall()
            
            return {
                "total_countries": len(rows),
                "countries": [
                    {
                        "iso3": row.iso3,
                        "name": row.name_fr,
                        "currency": row.currency,
                        "total_products": row.total_positions,
                        "last_updated": row.last_updated.isoformat() if row.last_updated else None
                    }
                    for row in rows
                ]
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_database_stats():
    """
    Retourne les statistiques de la base de données.
    """
    if not POSTGRES_AVAILABLE:
        return {
            "status": "unavailable",
            "message": "PostgreSQL non disponible. Migration en cours."
        }
    
    try:
        with engine.connect() as conn:
            # Compter les pays
            countries_count = conn.execute(text("SELECT COUNT(*) FROM countries")).scalar()
            
            # Compter les commodités
            commodities_count = conn.execute(text("SELECT COUNT(*) FROM commodities")).scalar()
            
            # Stats par pays (top 5)
            top_countries = conn.execute(text("""
                SELECT co.iso3, co.name_fr, COUNT(c.id) as count
                FROM countries co
                LEFT JOIN commodities c ON co.iso3 = c.country_iso3
                GROUP BY co.iso3, co.name_fr
                ORDER BY count DESC
                LIMIT 5
            """)).fetchall()
            
            return {
                "status": "available",
                "statistics": {
                    "total_countries": countries_count,
                    "total_commodities": commodities_count,
                    "average_per_country": round(commodities_count / countries_count, 0) if countries_count > 0 else 0
                },
                "top_countries": [
                    {"iso3": row.iso3, "name": row.name_fr, "products": row.count}
                    for row in top_countries
                ]
            }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }
