"""Compatibilité rétroactive — alias Kenya du service national générique.

Le pont Kenya a été généralisé dans
``services.national_legal_calculation_service`` afin de desservir un
registre de juridictions EAC. Ce module ne fait plus que ré-exporter
``calculate_kenya_legal_layer`` pour ne pas casser les appelants existants
(notamment ``routes.authentic_tariffs`` et ses tests, qui monkeypatchent ce
nom).
"""

from __future__ import annotations

from services.national_legal_calculation_service import calculate_kenya_legal_layer

__all__ = ["calculate_kenya_legal_layer"]
