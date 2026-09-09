"""
Finance module – ZLECAf

Unified entry point for AfCFTA trade finance, composed of two sub-modules:

- ``finance.banking``: banks registry, forex regulations, trade finance
  instruments, payment systems, country risk assessment, intelligent
  recommendations, bank scoring, FX hedging, and financing matrix analysis.
- ``finance.insurance``: export credit / political risk insurance
  registry, insurer directory, and premium pricing.

Both sub-modules are thin, explicit re-exports over the underlying
``banking_system`` package — no logic is duplicated here, and existing
imports of ``banking_system`` continue to work unchanged.
"""

from . import banking, insurance

__all__ = ["banking", "insurance"]
