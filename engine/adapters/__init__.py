"""
Adaptateurs de données pour le Moteur Réglementaire AfCFTA v3
=============================================================

Chaque pays a un adaptateur qui transforme ses données tarifaires
nationales au format canonique standardisé.

Pays majeurs supportés: DZA, MAR, EGY, NGA, ZAF, KEN, CIV, GHA
"""

from .base_adapter import BaseAdapter
from .dza_adapter import DZAAdapter
from .generic_adapter import GenericAdapter, create_adapter, COUNTRY_CONFIG

__all__ = [
    "BaseAdapter", 
    "DZAAdapter", 
    "GenericAdapter", 
    "create_adapter",
    "COUNTRY_CONFIG"
]
