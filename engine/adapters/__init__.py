"""
Adaptateurs de données pour le Moteur Réglementaire AfCFTA v3
=============================================================

Chaque pays a un adaptateur qui transforme ses données tarifaires
nationales au format canonique standardisé.

Pays majeurs supportés: MAR, EGY, NGA, ZAF, KEN, CIV, GHA
"""

from .base_adapter import BaseAdapter
from .generic_adapter import COUNTRY_CONFIG, GenericAdapter, create_adapter

__all__ = ["BaseAdapter", "GenericAdapter", "create_adapter", "COUNTRY_CONFIG"]
