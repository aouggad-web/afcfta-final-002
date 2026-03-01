"""
Modèles SQLAlchemy pour le Moteur Réglementaire AfCFTA v3
=========================================================

Tables PostgreSQL pour stocker les données tarifaires canoniques.
Migration depuis les fichiers JSONL vers une base relationnelle
pour une meilleure scalabilité et des requêtes plus performantes.
"""

from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, Text,
    ForeignKey, Index, Enum as SQLEnum, JSON, create_engine
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from datetime import datetime
import enum

Base = declarative_base()


class MeasureType(enum.Enum):
    """Types de mesures tarifaires"""
    CUSTOMS_DUTY = "CUSTOMS_DUTY"
    VAT = "VAT"
    EXCISE = "EXCISE"
    LEVY = "LEVY"
    OTHER_TAX = "OTHER_TAX"


class RequirementType(enum.Enum):
    """Types de formalités administratives"""
    IMPORT_DECLARATION = "IMPORT_DECLARATION"
    CERTIFICATE = "CERTIFICATE"
    LICENSE = "LICENSE"
    PERMIT = "PERMIT"
    INSPECTION = "INSPECTION"
    AUTHORIZATION = "AUTHORIZATION"


class Country(Base):
    """Table des pays disponibles"""
    __tablename__ = "countries"
    
    iso3 = Column(String(3), primary_key=True, comment="Code ISO 3166-1 alpha-3")
    name_fr = Column(String(100), nullable=False, comment="Nom en français")
    name_en = Column(String(100), comment="Nom en anglais")
    currency = Column(String(3), comment="Code devise ISO 4217")
    vat_rate = Column(Float, default=0, comment="Taux TVA standard (%)")
    tax_authority = Column(String(100), comment="Autorité fiscale")
    total_positions = Column(Integer, default=0, comment="Nombre de positions tarifaires")
    chapters_covered = Column(Integer, default=0, comment="Chapitres SH couverts")
    data_format = Column(String(20), default="enhanced_v2")
    last_updated = Column(DateTime, default=datetime.utcnow)
    
    # Relations
    commodities = relationship("Commodity", back_populates="country", cascade="all, delete-orphan")


class Commodity(Base):
    """Table des marchandises (codes tarifaires)"""
    __tablename__ = "commodities"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    country_iso3 = Column(String(3), ForeignKey("countries.iso3", ondelete="CASCADE"), nullable=False)
    national_code = Column(String(15), nullable=False, comment="Code tarifaire national complet")
    hs6 = Column(String(6), nullable=False, index=True, comment="Code HS6")
    digits = Column(Integer, default=6, comment="Nombre de digits")
    description_fr = Column(Text, nullable=False, comment="Description français")
    description_en = Column(Text, comment="Description anglais")
    chapter = Column(String(2), nullable=False, index=True, comment="Chapitre HS")
    category = Column(String(50), comment="Catégorie de produit")
    unit = Column(String(20), comment="Unité de mesure")
    sensitivity = Column(String(20), default="normal", comment="Sensibilité ZLECAf")
    
    # Totaux précalculés
    total_npf_pct = Column(Float, default=0, comment="Total taxes NPF (%)")
    total_zlecaf_pct = Column(Float, default=0, comment="Total taxes ZLECAf (%)")
    savings_pct = Column(Float, default=0, comment="Économie ZLECAf (%)")
    
    # Métadonnées
    source_file = Column(String(255))
    last_updated = Column(DateTime, default=datetime.utcnow)
    
    # Relations
    country = relationship("Country", back_populates="commodities")
    measures = relationship("Measure", back_populates="commodity", cascade="all, delete-orphan")
    requirements = relationship("Requirement", back_populates="commodity", cascade="all, delete-orphan")
    fiscal_advantages = relationship("FiscalAdvantage", back_populates="commodity", cascade="all, delete-orphan")
    
    # Index composites
    __table_args__ = (
        Index("idx_commodity_country_hs6", "country_iso3", "hs6"),
        Index("idx_commodity_country_national", "country_iso3", "national_code"),
        Index("idx_commodity_country_chapter", "country_iso3", "chapter"),
    )


class Measure(Base):
    """Table des mesures tarifaires (taxes, droits)"""
    __tablename__ = "measures"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    commodity_id = Column(Integer, ForeignKey("commodities.id", ondelete="CASCADE"), nullable=False)
    measure_type = Column(SQLEnum(MeasureType), nullable=False)
    code = Column(String(20), nullable=False, comment="Code de la taxe (D.D, TVA)")
    name_fr = Column(String(200), nullable=False)
    name_en = Column(String(200))
    rate_pct = Column(Float, nullable=False, comment="Taux NPF (%)")
    is_zlecaf_applicable = Column(Boolean, default=False)
    zlecaf_rate_pct = Column(Float, comment="Taux ZLECAf si différent")
    observation = Column(Text)
    
    # Relations
    commodity = relationship("Commodity", back_populates="measures")
    
    __table_args__ = (
        Index("idx_measure_commodity", "commodity_id"),
        Index("idx_measure_type", "measure_type"),
    )


class Requirement(Base):
    """Table des formalités administratives"""
    __tablename__ = "requirements"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    commodity_id = Column(Integer, ForeignKey("commodities.id", ondelete="CASCADE"), nullable=False)
    requirement_type = Column(SQLEnum(RequirementType), nullable=False)
    code = Column(String(20), nullable=False)
    document_fr = Column(String(300), nullable=False)
    document_en = Column(String(300))
    is_mandatory = Column(Boolean, default=True)
    issuing_authority = Column(String(200))
    
    # Relations
    commodity = relationship("Commodity", back_populates="requirements")
    
    __table_args__ = (
        Index("idx_requirement_commodity", "commodity_id"),
    )


class FiscalAdvantage(Base):
    """Table des avantages fiscaux ZLECAf"""
    __tablename__ = "fiscal_advantages"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    commodity_id = Column(Integer, ForeignKey("commodities.id", ondelete="CASCADE"), nullable=False)
    tax_code = Column(String(20), nullable=False, comment="Code de la taxe concernée")
    reduced_rate_pct = Column(Float, nullable=False, comment="Taux réduit")
    condition_fr = Column(Text, nullable=False)
    condition_en = Column(Text)
    
    # Relations
    commodity = relationship("Commodity", back_populates="fiscal_advantages")
    
    __table_args__ = (
        Index("idx_fiscal_advantage_commodity", "commodity_id"),
    )


# Configuration de la base de données
def get_engine(database_url: str = None):
    """Crée et retourne le moteur SQLAlchemy"""
    if database_url is None:
        import os
        database_url = os.environ.get(
            "DATABASE_URL",
            "postgresql://postgres:postgres@localhost:5432/afcfta_regulatory"
        )
    return create_engine(database_url, echo=False, pool_pre_ping=True)


def create_tables(engine):
    """Crée toutes les tables"""
    Base.metadata.create_all(engine)


def get_session(engine):
    """Crée une session de base de données"""
    Session = sessionmaker(bind=engine)
    return Session()
