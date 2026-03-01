"""
Adaptateurs de données pour le Moteur Réglementaire AfCFTA v3
=============================================================

Chaque pays a un adaptateur qui transforme ses données tarifaires
nationales au format canonique standardisé.
"""

from .base_adapter import BaseAdapter
from .dza_adapter import DZAAdapter

__all__ = ["BaseAdapter", "DZAAdapter"]
