"""
Service de Migration JSONL vers PostgreSQL
==========================================

Migre les données canoniques des fichiers JSONL vers PostgreSQL
pour une meilleure scalabilité et des requêtes SQL avancées.
"""

import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional
import logging

from sqlalchemy.orm import Session
from sqlalchemy import func

from .models import (
    Base, Country, Commodity, Measure, Requirement, FiscalAdvantage,
    MeasureType, RequirementType, get_engine, create_tables, get_session
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Mapping des pays avec leurs informations
COUNTRY_INFO = {
    "DZA": {"name_fr": "Algérie", "name_en": "Algeria", "currency": "DZD"},
    "MAR": {"name_fr": "Maroc", "name_en": "Morocco", "currency": "MAD"},
    "EGY": {"name_fr": "Égypte", "name_en": "Egypt", "currency": "EGP"},
    "NGA": {"name_fr": "Nigeria", "name_en": "Nigeria", "currency": "NGN"},
    "ZAF": {"name_fr": "Afrique du Sud", "name_en": "South Africa", "currency": "ZAR"},
    "KEN": {"name_fr": "Kenya", "name_en": "Kenya", "currency": "KES"},
    "CIV": {"name_fr": "Côte d'Ivoire", "name_en": "Ivory Coast", "currency": "XOF"},
    "GHA": {"name_fr": "Ghana", "name_en": "Ghana", "currency": "GHS"},
    "ETH": {"name_fr": "Éthiopie", "name_en": "Ethiopia", "currency": "ETB"},
    "TUN": {"name_fr": "Tunisie", "name_en": "Tunisia", "currency": "TND"},
    "SEN": {"name_fr": "Sénégal", "name_en": "Senegal", "currency": "XOF"},
    "CMR": {"name_fr": "Cameroun", "name_en": "Cameroon", "currency": "XAF"},
    "UGA": {"name_fr": "Ouganda", "name_en": "Uganda", "currency": "UGX"},
    "TZA": {"name_fr": "Tanzanie", "name_en": "Tanzania", "currency": "TZS"},
    "RWA": {"name_fr": "Rwanda", "name_en": "Rwanda", "currency": "RWF"},
    "MUS": {"name_fr": "Maurice", "name_en": "Mauritius", "currency": "MUR"},
}


class MigrationService:
    """Service de migration des données JSONL vers PostgreSQL"""
    
    def __init__(self, data_dir: str = "/app/engine/output", database_url: str = None):
        self.data_dir = Path(data_dir)
        self.engine = get_engine(database_url)
        self.stats = {
            "countries_migrated": 0,
            "commodities_inserted": 0,
            "measures_inserted": 0,
            "requirements_inserted": 0,
            "fiscal_advantages_inserted": 0
        }
    
    def init_database(self):
        """Initialise la base de données (crée les tables)"""
        logger.info("Création des tables PostgreSQL...")
        create_tables(self.engine)
        logger.info("Tables créées avec succès")
    
    def migrate_all(self, countries: List[str] = None, batch_size: int = 1000):
        """
        Migre toutes les données des pays spécifiés.
        
        Args:
            countries: Liste des codes ISO3 à migrer. Si None, migre tous les fichiers disponibles.
            batch_size: Taille des lots pour les insertions.
        """
        # Trouver tous les fichiers JSONL
        if countries is None:
            jsonl_files = list(self.data_dir.glob("*_canonical.jsonl"))
            countries = [f.stem.replace("_canonical", "") for f in jsonl_files]
        
        logger.info(f"Migration de {len(countries)} pays: {countries}")
        
        session = get_session(self.engine)
        
        try:
            for iso3 in countries:
                self._migrate_country(session, iso3, batch_size)
            
            session.commit()
            logger.info(f"Migration terminée: {self.stats}")
            
        except Exception as e:
            session.rollback()
            logger.error(f"Erreur de migration: {e}")
            raise
        finally:
            session.close()
        
        return self.stats
    
    def _migrate_country(self, session: Session, iso3: str, batch_size: int):
        """Migre les données d'un pays"""
        jsonl_path = self.data_dir / f"{iso3}_canonical.jsonl"
        summary_path = self.data_dir / f"{iso3}_summary.json"
        
        if not jsonl_path.exists():
            logger.warning(f"Fichier non trouvé: {jsonl_path}")
            return
        
        logger.info(f"Migration {iso3}...")
        
        # Charger le résumé
        summary = {}
        if summary_path.exists():
            with open(summary_path, 'r', encoding='utf-8') as f:
                summary = json.load(f)
        
        # Créer ou mettre à jour l'entrée pays
        country_info = COUNTRY_INFO.get(iso3, {"name_fr": iso3, "name_en": iso3, "currency": "USD"})
        
        country = session.query(Country).filter_by(iso3=iso3).first()
        if country:
            # Supprimer les anciennes données
            session.query(Commodity).filter_by(country_iso3=iso3).delete()
        else:
            country = Country(iso3=iso3)
        
        country.name_fr = country_info["name_fr"]
        country.name_en = country_info["name_en"]
        country.currency = country_info["currency"]
        country.vat_rate = summary.get("vat_rate", 0)
        country.total_positions = summary.get("total_positions", 0)
        country.chapters_covered = summary.get("chapters_covered", 0)
        country.data_format = summary.get("data_format", "enhanced_v2")
        country.last_updated = datetime.utcnow()
        
        session.add(country)
        session.flush()
        
        # Migrer les commodités par lots
        commodities_batch = []
        count = 0
        
        with open(jsonl_path, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    data = json.loads(line)
                    commodity = self._create_commodity(session, iso3, data)
                    commodities_batch.append(commodity)
                    count += 1
                    
                    if len(commodities_batch) >= batch_size:
                        session.add_all(commodities_batch)
                        session.flush()
                        commodities_batch = []
                        logger.info(f"  {iso3}: {count} enregistrements...")
                        
                except json.JSONDecodeError as e:
                    logger.warning(f"Erreur JSON ligne {count}: {e}")
                    continue
        
        # Insérer le reste
        if commodities_batch:
            session.add_all(commodities_batch)
            session.flush()
        
        # Mettre à jour le compteur du pays
        country.total_positions = count
        
        self.stats["countries_migrated"] += 1
        self.stats["commodities_inserted"] += count
        
        logger.info(f"  {iso3}: {count} enregistrements migrés")
    
    def _create_commodity(self, session: Session, iso3: str, data: Dict) -> Commodity:
        """Crée un objet Commodity à partir des données JSON"""
        commodity_data = data.get("commodity", {})
        
        commodity = Commodity(
            country_iso3=iso3,
            national_code=commodity_data.get("national_code", ""),
            hs6=commodity_data.get("hs6", ""),
            digits=commodity_data.get("digits", 6),
            description_fr=commodity_data.get("description_fr", ""),
            description_en=commodity_data.get("description_en"),
            chapter=commodity_data.get("chapter", ""),
            category=commodity_data.get("category"),
            unit=commodity_data.get("unit"),
            sensitivity=commodity_data.get("sensitivity", "normal"),
            total_npf_pct=data.get("total_npf_pct", 0),
            total_zlecaf_pct=data.get("total_zlecaf_pct", 0),
            savings_pct=data.get("savings_pct", 0),
            source_file=data.get("source_file"),
            last_updated=datetime.utcnow()
        )
        
        # Ajouter les mesures
        for m_data in data.get("measures", []):
            measure = Measure(
                measure_type=MeasureType[m_data.get("measure_type", "OTHER_TAX")],
                code=m_data.get("code", ""),
                name_fr=m_data.get("name_fr", ""),
                name_en=m_data.get("name_en"),
                rate_pct=m_data.get("rate_pct", 0),
                is_zlecaf_applicable=m_data.get("is_zlecaf_applicable", False),
                zlecaf_rate_pct=m_data.get("zlecaf_rate_pct"),
                observation=m_data.get("observation")
            )
            commodity.measures.append(measure)
            self.stats["measures_inserted"] += 1
        
        # Ajouter les formalités
        for r_data in data.get("requirements", []):
            requirement = Requirement(
                requirement_type=RequirementType[r_data.get("requirement_type", "CERTIFICATE")],
                code=r_data.get("code", ""),
                document_fr=r_data.get("document_fr", ""),
                document_en=r_data.get("document_en"),
                is_mandatory=r_data.get("is_mandatory", True),
                issuing_authority=r_data.get("issuing_authority")
            )
            commodity.requirements.append(requirement)
            self.stats["requirements_inserted"] += 1
        
        # Ajouter les avantages fiscaux
        for fa_data in data.get("fiscal_advantages", []):
            fiscal_advantage = FiscalAdvantage(
                tax_code=fa_data.get("tax_code", ""),
                reduced_rate_pct=fa_data.get("reduced_rate_pct", 0),
                condition_fr=fa_data.get("condition_fr", ""),
                condition_en=fa_data.get("condition_en")
            )
            commodity.fiscal_advantages.append(fiscal_advantage)
            self.stats["fiscal_advantages_inserted"] += 1
        
        return commodity


class PostgresQueryService:
    """Service de requêtes PostgreSQL pour le Moteur Réglementaire"""
    
    def __init__(self, database_url: str = None):
        self.engine = get_engine(database_url)
    
    def get_available_countries(self) -> List[Dict]:
        """Retourne la liste des pays disponibles"""
        session = get_session(self.engine)
        try:
            countries = session.query(Country).all()
            return [
                {
                    "iso3": c.iso3,
                    "name_fr": c.name_fr,
                    "name_en": c.name_en,
                    "total_positions": c.total_positions,
                    "vat_rate": c.vat_rate
                }
                for c in countries
            ]
        finally:
            session.close()
    
    def get_by_national_code(self, iso3: str, national_code: str) -> Optional[Dict]:
        """Recherche par code national exact"""
        session = get_session(self.engine)
        try:
            commodity = session.query(Commodity).filter_by(
                country_iso3=iso3.upper(),
                national_code=national_code
            ).first()
            
            if commodity:
                return self._commodity_to_dict(commodity)
            return None
        finally:
            session.close()
    
    def get_by_hs6(self, iso3: str, hs6: str) -> List[Dict]:
        """Recherche par code HS6"""
        session = get_session(self.engine)
        try:
            commodities = session.query(Commodity).filter_by(
                country_iso3=iso3.upper(),
                hs6=hs6
            ).all()
            
            return [self._commodity_to_dict(c) for c in commodities]
        finally:
            session.close()
    
    def search_description(self, iso3: str, query: str, limit: int = 50) -> List[Dict]:
        """Recherche dans les descriptions"""
        session = get_session(self.engine)
        try:
            commodities = session.query(Commodity).filter(
                Commodity.country_iso3 == iso3.upper(),
                Commodity.description_fr.ilike(f"%{query}%")
            ).limit(limit).all()
            
            return [
                {
                    "national_code": c.national_code,
                    "hs6": c.hs6,
                    "description_fr": c.description_fr,
                    "total_npf_pct": c.total_npf_pct
                }
                for c in commodities
            ]
        finally:
            session.close()
    
    def get_statistics(self, iso3: str) -> Dict:
        """Retourne les statistiques d'un pays"""
        session = get_session(self.engine)
        try:
            country = session.query(Country).filter_by(iso3=iso3.upper()).first()
            if not country:
                return {}
            
            # Statistiques agrégées
            stats = session.query(
                func.count(Commodity.id).label("total_commodities"),
                func.avg(Commodity.total_npf_pct).label("avg_npf"),
                func.avg(Commodity.savings_pct).label("avg_savings"),
                func.count(func.distinct(Commodity.chapter)).label("chapters")
            ).filter_by(country_iso3=iso3.upper()).first()
            
            return {
                "country": {
                    "iso3": country.iso3,
                    "name_fr": country.name_fr,
                    "vat_rate": country.vat_rate,
                    "currency": country.currency
                },
                "statistics": {
                    "total_commodities": stats.total_commodities,
                    "avg_npf_rate": round(stats.avg_npf or 0, 2),
                    "avg_savings_rate": round(stats.avg_savings or 0, 2),
                    "chapters_covered": stats.chapters
                }
            }
        finally:
            session.close()
    
    def _commodity_to_dict(self, commodity: Commodity) -> Dict:
        """Convertit une Commodity en dictionnaire"""
        return {
            "commodity": {
                "country_iso3": commodity.country_iso3,
                "national_code": commodity.national_code,
                "hs6": commodity.hs6,
                "digits": commodity.digits,
                "description_fr": commodity.description_fr,
                "description_en": commodity.description_en,
                "chapter": commodity.chapter,
                "category": commodity.category,
                "unit": commodity.unit,
                "sensitivity": commodity.sensitivity
            },
            "measures": [
                {
                    "measure_type": m.measure_type.value,
                    "code": m.code,
                    "name_fr": m.name_fr,
                    "rate_pct": m.rate_pct,
                    "is_zlecaf_applicable": m.is_zlecaf_applicable,
                    "zlecaf_rate_pct": m.zlecaf_rate_pct
                }
                for m in commodity.measures
            ],
            "requirements": [
                {
                    "requirement_type": r.requirement_type.value,
                    "code": r.code,
                    "document_fr": r.document_fr,
                    "is_mandatory": r.is_mandatory,
                    "issuing_authority": r.issuing_authority
                }
                for r in commodity.requirements
            ],
            "fiscal_advantages": [
                {
                    "tax_code": fa.tax_code,
                    "reduced_rate_pct": fa.reduced_rate_pct,
                    "condition_fr": fa.condition_fr
                }
                for fa in commodity.fiscal_advantages
            ],
            "total_npf_pct": commodity.total_npf_pct,
            "total_zlecaf_pct": commodity.total_zlecaf_pct,
            "savings_pct": commodity.savings_pct
        }


def main():
    """Point d'entrée pour la migration"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Migration JSONL vers PostgreSQL")
    parser.add_argument("--database-url", help="URL de connexion PostgreSQL")
    parser.add_argument("--countries", nargs="+", help="Codes ISO3 à migrer")
    parser.add_argument("--batch-size", type=int, default=1000, help="Taille des lots")
    parser.add_argument("--init-only", action="store_true", help="Créer les tables uniquement")
    
    args = parser.parse_args()
    
    service = MigrationService(database_url=args.database_url)
    
    if args.init_only:
        service.init_database()
    else:
        service.init_database()
        stats = service.migrate_all(countries=args.countries, batch_size=args.batch_size)
        print(f"Migration terminée: {stats}")


if __name__ == "__main__":
    main()
