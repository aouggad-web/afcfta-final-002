"""Bridge the public calculator to the dated national legal-override engine.

Généralise le pont Kenya (PR #307) à un registre de juridictions EAC.
Chaque juridiction déclare son répertoire de données fiscales nationales
(``data/<pays>/``) et partage, tant qu'aucun corpus juridique propre à la
juridiction n'existe, le corpus de mesures EAC commun
(``data/eac/legal_overrides.json``).

Ajouter une juridiction : déposer ses fichiers ``vat_measures.json``,
``excise_measures.json`` et ``import_levies.json`` (schéma identique à
``data/kenya/``, voir ``docs/data-sources/KEN_SOURCE_REGISTER.md`` pour la
discipline de sourçage), puis l'enregistrer dans
``SUPPORTED_JURISDICTIONS``.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date
from functools import lru_cache
from pathlib import Path
from typing import Dict, Iterable, Optional

from engine.legal_override_engine import load_legal_measures
from engine.national_customs_calculation import NationalFiscalStore, calculate_national_customs
from engine.schemas.legal_override import OverrideContext, RemissionEligibility

_ROOT = Path(__file__).resolve().parents[2]
_EAC_DATA = _ROOT / "data" / "eac"
_EAC_LEGAL_OVERRIDES = _EAC_DATA / "legal_overrides.json"
_EAC_GAZETTE_REGISTER = _EAC_DATA / "eac_gazette_register.json"


@dataclass(frozen=True)
class JurisdictionConfig:
    """Déclaration d'une juridiction desservie par la couche de vérification."""

    iso3: str
    fiscal_data_dir: Path
    legal_overrides_path: Path = _EAC_LEGAL_OVERRIDES
    gazette_register_path: Path = _EAC_GAZETTE_REGISTER
    default_currency: str = "USD"


# Juridictions couvertes par la couche de vérification juridique datée.
# Kenya (PR #307) reste la seule juridiction opérationnelle tant que les
# corpus fiscaux Tanzanie/Ouganda/Rwanda ne sont pas collectés depuis leurs
# sources officielles (TanzLII, ULII, RwandaLII) — voir le plan
# d'enrichissement EAC.
SUPPORTED_JURISDICTIONS: Dict[str, JurisdictionConfig] = {
    "KEN": JurisdictionConfig(iso3="KEN", fiscal_data_dir=_ROOT / "data" / "kenya"),
}


@lru_cache(maxsize=None)
def _resources(iso3: str):
    config = SUPPORTED_JURISDICTIONS[iso3]
    measures = load_legal_measures(config.legal_overrides_path)
    register = json.loads(config.gazette_register_path.read_text(encoding="utf-8"))
    store = NationalFiscalStore(config.fiscal_data_dir)
    return measures, store, bool(register.get("coverage_complete", False))


def calculate_national_legal_layer(
    *,
    jurisdiction: str,
    hs_code: str,
    on_date: date,
    customs_value: float,
    base_cet_rate: float,
    origin: Optional[str] = None,
    remission_eligibility: RemissionEligibility = RemissionEligibility.ELIGIBILITY_UNKNOWN,
    authorization_reference: Optional[str] = None,
    authorization_effective_from: Optional[date] = None,
    authorization_effective_to: Optional[date] = None,
    authorization_hs_codes: Optional[Iterable[str]] = None,
    authorization_goods: Optional[Iterable[str]] = None,
    beneficiary: Optional[str] = None,
    import_purpose: Optional[str] = None,
    quantity: Optional[float] = None,
    currency_code: Optional[str] = None,
) -> dict:
    if jurisdiction not in SUPPORTED_JURISDICTIONS:
        raise KeyError(f"Unsupported jurisdiction: {jurisdiction!r}")
    measures, fiscal_store, coverage_complete = _resources(jurisdiction)
    config = SUPPORTED_JURISDICTIONS[jurisdiction]
    context = OverrideContext(
        jurisdiction=jurisdiction,
        origin=origin,
        beneficiary=beneficiary,
        import_purpose=import_purpose,
        quantity=quantity,
        remission_eligibility=remission_eligibility,
        authorization_reference=authorization_reference,
        authorization_effective_from=authorization_effective_from,
        authorization_effective_to=authorization_effective_to,
        authorization_hs_codes=list(authorization_hs_codes or []),
        authorization_goods=list(authorization_goods or []),
    )
    return calculate_national_customs(
        jurisdiction=jurisdiction,
        hs_code=hs_code,
        on_date=on_date,
        customs_value=customs_value,
        base_cet_rate=base_cet_rate,
        measures=measures,
        fiscal_store=fiscal_store,
        context=context,
        coverage_complete=coverage_complete,
        currency_code=currency_code or config.default_currency,
    )


def calculate_kenya_legal_layer(*, currency_code: str = "USD", **kwargs) -> dict:
    """Alias rétrocompatible : calcul Kenya via le registre générique."""
    return calculate_national_legal_layer(jurisdiction="KEN", currency_code=currency_code, **kwargs)
