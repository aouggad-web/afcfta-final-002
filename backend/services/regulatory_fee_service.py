"""Moteur de calcul — frais de formalités et de prestataires mandatés.

Ce service transforme un descriptif de frais STRUCTURÉ et sourcé en une ligne de
coût normalisée, en respectant une discipline fail-closed stricte :

- jamais de coût sans source officielle (règle 1) ;
- jamais de gratuité supposée quand le montant est absent (règle 2) ;
- jamais de pourcentage sans assiette explicitement définie (règle 3) ;
- pas de tarif national généralisé à tous les produits — le calcul ne porte que
  sur le descriptif attaché à la mesure/au prestataire fourni (règle 4) ;
- une prestation expirée n'est jamais transmise ici (le caller ne passe que des
  mandats actifs) (règle 5) ;
- l'état complet/partiel est toujours explicite (règle 6) ;
- les frais du prestataire restent séparés des droits et taxes publics (règle 7,
  garantie par ``build_regulatory_cost`` qui range formalité et prestataire dans
  des compartiments distincts).

Aucune valeur n'est fabriquée : en l'absence de descriptif chiffré, un frais dont
l'existence est confirmée renvoie ``FEE_EXISTS_AMOUNT_NOT_AVAILABLE`` (montant
None), jamais 0.
"""

import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional

_REPO_ROOT = Path(__file__).resolve().parents[2]
_VERIFIED_FEES_PATH = _REPO_ROOT / "data/regulatory-compliance/verified_provider_fees.json"

# Statuts canoniques d'un frais (spec lot « intégration calculateur »).
FEE_STATUSES = {
    "CALCULABLE",
    "DOCUMENTED_FIXED_AMOUNT",
    "DOCUMENTED_PERCENTAGE",
    "FEE_EXISTS_AMOUNT_NOT_AVAILABLE",
    "PARTIAL",
    "NOT_AVAILABLE",
    "NOT_APPLICABLE",
}

# Méthodes de calcul reconnues. L'assiette (base) est explicite dans le nom :
# FOB = valeur déclarée franco à bord ; CIF = valeur coût-assurance-fret.
CALCULATION_METHODS = {"FIXED_AMOUNT", "PERCENTAGE_OF_FOB", "PERCENTAGE_OF_CIF"}

# Statuts de mandat considérés comme confirmés et actuellement actifs (miroir de
# regulatory_compliance_service._ACTIVE_MANDATE_STATUSES).
_ACTIVE_MANDATE_STATUSES = {"CONFIRMED_TIME_LIMITED", "CONFIRMED_UNDATED_END"}


def _source_of(fee_detail: Dict[str, Any]) -> Optional[str]:
    return fee_detail.get("source") or fee_detail.get("source_id") or fee_detail.get("source_url")


def _unpriced(fee_exists: bool, reason: str) -> Dict[str, Any]:
    """Résultat sans montant : signalé si le frais existe, sinon indisponible."""
    return {
        "fee_status": "FEE_EXISTS_AMOUNT_NOT_AVAILABLE" if fee_exists else "NOT_AVAILABLE",
        "calculated_amount": None,
        "currency": None,
        "reason": reason,
    }


def compute_fee(
    fee_detail: Optional[Dict[str, Any]],
    *,
    fob_value: Optional[float] = None,
    cif_value: Optional[float] = None,
    fee_exists: bool = False,
) -> Dict[str, Any]:
    """Normalise un descriptif de frais en ligne de coût, fail-closed.

    ``fee_detail`` : descriptif STRUCTURÉ optionnel (calculation_method, rate,
    fixed_amount, minimum_amount, maximum_amount, currency, effective_date,
    source, conditions). Absent → aucun montant fabriqué.

    ``fee_exists`` : vrai lorsque l'existence d'un paiement est confirmée (ex.
    prestataire mandaté actif) sans descriptif chiffré — pour distinguer
    ``FEE_EXISTS_AMOUNT_NOT_AVAILABLE`` (à signaler) de ``NOT_AVAILABLE``.
    """
    if not fee_detail:
        return _unpriced(fee_exists, "no_structured_fee_detail")

    # Règle 1 — pas de coût sans source officielle.
    source = _source_of(fee_detail)
    if not source:
        return _unpriced(fee_exists, "no_source")

    method = fee_detail.get("calculation_method")
    currency = fee_detail.get("currency")
    effective_date = fee_detail.get("effective_date")
    conditions = fee_detail.get("conditions")
    base_result = {
        "calculation_method": method,
        "currency": currency,
        "effective_date": effective_date,
        "conditions": conditions,
        "minimum_amount": fee_detail.get("minimum_amount"),
        "maximum_amount": fee_detail.get("maximum_amount"),
        "source": source,
        "last_verified": fee_detail.get("last_verified"),
    }

    if method not in CALCULATION_METHODS:
        # Existence/source connues mais méthode non exploitable → partiel.
        return {
            **base_result,
            "fee_status": "PARTIAL",
            "calculated_amount": None,
            "reason": "unknown_or_missing_calculation_method",
        }

    if method == "FIXED_AMOUNT":
        amount = fee_detail.get("fixed_amount")
        if amount is None or currency is None:
            return {
                **base_result,
                "fee_status": "PARTIAL",
                "calculated_amount": None,
                "reason": "fixed_amount_or_currency_missing",
            }
        return {
            **base_result,
            "fee_status": "DOCUMENTED_FIXED_AMOUNT",
            "calculated_amount": round(float(amount), 2),
        }

    # Méthodes en pourcentage — assiette obligatoire (règle 3).
    # Le taux peut être unique (rate) ou une FOURCHETTE route-dépendante
    # (rate_min/rate_max) : dans ce dernier cas, on calcule des bornes min/max
    # plutôt qu'un montant unique fictif.
    rate = fee_detail.get("rate")
    rate_min = fee_detail.get("rate_min")
    rate_max = fee_detail.get("rate_max")
    base_value = fob_value if method == "PERCENTAGE_OF_FOB" else cif_value
    base_label = "FOB" if method == "PERCENTAGE_OF_FOB" else "CIF"

    has_single = rate is not None
    has_range = rate_min is not None and rate_max is not None
    # Pour une méthode en pourcentage, la devise du montant est celle de l'assiette
    # (ad valorem) : elle peut rester None (unité de la valeur saisie). On n'exige
    # donc PAS de devise ici, contrairement au montant fixe. L'assiette, elle,
    # reste obligatoire (règle 3).
    if (not has_single and not has_range) or base_value is None:
        return {
            **base_result,
            "fee_status": "PARTIAL",
            "calculated_amount": None,
            "rate": rate,
            "base_label": base_label,
            "reason": "rate_or_base_missing",
        }
    is_ad_valorem = currency is None

    minimum = fee_detail.get("minimum_amount")
    maximum = fee_detail.get("maximum_amount")

    def _bounded(r: float) -> float:
        amt = float(r) * float(base_value)
        if minimum is not None:
            amt = max(amt, float(minimum))
        if maximum is not None:
            amt = min(amt, float(maximum))
        return round(amt, 2)

    if has_range:
        # Fourchette : montant borné bas (rate_min) et haut (rate_max).
        return {
            **base_result,
            "fee_status": "CALCULABLE",
            "is_range": True,
            "ad_valorem": is_ad_valorem,
            "rate_min": rate_min,
            "rate_max": rate_max,
            "base_label": base_label,
            "base_value": round(float(base_value), 2),
            "calculated_amount": None,
            "calculated_amount_min": _bounded(rate_min),
            "calculated_amount_max": _bounded(rate_max),
        }

    return {
        **base_result,
        "fee_status": "CALCULABLE",
        "is_range": False,
        "ad_valorem": is_ad_valorem,
        "rate": rate,
        "base_label": base_label,
        "base_value": round(float(base_value), 2),
        "calculated_amount": _bounded(rate),
    }


def _fee_exists_for_measure(measure: Dict[str, Any]) -> bool:
    """L'existence d'un frais de formalité est-elle confirmée (≠ NOT_APPLICABLE) ?"""
    return measure.get("fees_status") not in (None, "NOT_APPLICABLE")


def build_regulatory_cost(
    compliance: Optional[Dict[str, Any]],
    *,
    fob_value: Optional[float] = None,
    cif_value: Optional[float] = None,
    side: str = "import",
) -> Optional[Dict[str, Any]]:
    """Compose la ventilation des frais réglementaires d'un pays.

    Ne traite QUE les mesures portant un prestataire mandaté ACTIF (règle 5) et
    range séparément « frais de formalité obligatoire » et « frais du prestataire
    mandaté » (règle 7). Renvoie None quand aucun prestataire actif n'est présent
    (pas de rubrique vide).
    """
    if not compliance:
        return None

    line_items: List[Dict[str, Any]] = []
    for measure in compliance.get("measures", []):
        active_actors = [
            a
            for a in (measure.get("mandated_actors") or [])
            if a.get("mandate_status") in _ACTIVE_MANDATE_STATUSES
        ]
        if not active_actors:
            continue

        # Frais de la formalité elle-même (perçu public éventuel).
        formality_fee = compute_fee(
            measure.get("fees_detail"),
            fob_value=fob_value,
            cif_value=cif_value,
            fee_exists=_fee_exists_for_measure(measure),
        )
        line_items.append(
            {
                "scope": "formality",
                "measure_name": measure.get("measure_name"),
                "measure_step": measure.get("procedure_step") or measure.get("scope_type"),
                "mandating_authority": measure.get("authority"),
                "actor_name": None,
                "products": measure.get("products"),
                "transport": measure.get("transport"),
                "legal_reference": measure.get("legal_reference"),
                "as_of": compliance.get("as_of"),
                "side": side,
                **formality_fee,
            }
        )

        # Frais de chaque prestataire mandaté actif (perçu privé).
        for actor in active_actors:
            provider_fee = compute_fee(
                actor.get("authorized_fees_detail"),
                fob_value=fob_value,
                cif_value=cif_value,
                fee_exists=True,  # prestataire actif → un frais est réputé exister
            )
            line_items.append(
                {
                    "scope": "provider",
                    "measure_name": measure.get("measure_name"),
                    "measure_step": measure.get("procedure_step") or measure.get("scope_type"),
                    "mandating_authority": actor.get("mandating_authority"),
                    "actor_name": actor.get("actor_name"),
                    "service": actor.get("mission"),
                    "contact": _actor_contact(actor, measure),
                    "mandate_status": actor.get("mandate_status"),
                    "as_of": compliance.get("as_of"),
                    "side": side,
                    **provider_fee,
                }
            )

    if not line_items:
        return None

    return _summarise(line_items)


@lru_cache(maxsize=1)
def _load_verified_fees() -> List[Dict[str, Any]]:
    """Charge le jeu de frais vérifiés (source primaire). Absent → liste vide."""
    if not _VERIFIED_FEES_PATH.exists():
        return []
    with open(_VERIFIED_FEES_PATH, "r", encoding="utf-8") as fh:
        return json.load(fh).get("fees", [])


def build_verified_provider_costs(
    country_iso3: Optional[str],
    *,
    fob_value: Optional[float] = None,
    cif_value: Optional[float] = None,
    side: str = "import",
) -> List[Dict[str, Any]]:
    """Lignes de coût CALCULABLES issues de frais VÉRIFIÉS sur source primaire.

    Ces frais sont autoritaires par construction (chaque entrée cite ses sources) :
    ils apparaissent indépendamment du registre conforme. Un frais dont le seuil de
    déclenchement (threshold_fob) n'est pas atteint est marqué NOT_APPLICABLE.
    """
    if not country_iso3:
        return []
    iso = country_iso3.upper()
    out: List[Dict[str, Any]] = []
    for entry in _load_verified_fees():
        if entry.get("country_iso3", "").upper() != iso:
            continue
        if entry.get("side", "import") != side:
            continue
        detail = dict(entry.get("fee_detail") or {})
        verification = entry.get("verification") or {}
        # Source obligatoire (règle 1) : la 1re URL de vérification.
        sources = verification.get("sources") or []
        if sources and not detail.get("source"):
            detail["source"] = sources[0].get("url")
        threshold = detail.get("threshold_fob_xof")
        # Seuil de déclenchement : sous le seuil, la VOC ne s'applique pas. On ne
        # convertit pas de devise ; le seuil est appliqué uniquement si l'assiette
        # est exprimée dans la même devise que le seuil (prudence anti-FX).
        computed = compute_fee(detail, fob_value=fob_value, cif_value=cif_value, fee_exists=True)
        line = {
            "scope": "provider",
            "measure_name": entry.get("program"),
            "mandating_authority": entry.get("mandating_authority"),
            "actor_name": ", ".join(entry.get("providers", [])) or None,
            "service": entry.get("scope"),
            "payer": entry.get("payer"),
            "contact": sources[0].get("url") if sources else None,
            "verification_status": verification.get("status"),
            "verification_sources": sources,
            "threshold_fob_xof": threshold,
            "conditions": detail.get("conditions"),
            "as_of": verification.get("date"),
            "side": side,
            "tier": "VERIFIED_PRIMARY",
            **computed,
        }
        out.append(line)
    return out


def _actor_contact(actor: Dict[str, Any], measure: Dict[str, Any]) -> Optional[str]:
    """Meilleur lien/contact disponible, sans rien fabriquer."""
    for ev in actor.get("mandate_evidence") or []:
        if ev.get("url"):
            return ev["url"]
    return measure.get("platform")


_INCOMPLETE_STATUSES = {"FEE_EXISTS_AMOUNT_NOT_AVAILABLE", "PARTIAL"}
_COMPUTED_STATUSES = {"CALCULABLE", "DOCUMENTED_FIXED_AMOUNT", "DOCUMENTED_PERCENTAGE"}


def _summarise(line_items: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Agrège les lignes en totaux séparés + drapeaux de complétude.

    Les montants ne sont sommés qu'entre lignes partageant la même devise ; en cas
    de devises mixtes, le total reste par devise et l'ensemble est marqué
    incomplet plutôt que d'additionner des unités hétérogènes.
    """
    # Totaux bornés par devise : chaque ligne calculée contribue par son montant
    # (point) ou, pour une fourchette, par ses bornes min/max.
    provider_min: Dict[str, float] = {}
    provider_max: Dict[str, float] = {}
    formality_min: Dict[str, float] = {}
    formality_max: Dict[str, float] = {}
    for item in line_items:
        if item.get("fee_status") not in _COMPUTED_STATUSES:
            continue
        ccy = item.get("currency")
        if not ccy:
            continue
        if item.get("is_range"):
            lo, hi = item.get("calculated_amount_min"), item.get("calculated_amount_max")
        else:
            lo = hi = item.get("calculated_amount")
        if lo is None or hi is None:
            continue
        bmin = provider_min if item["scope"] == "provider" else formality_min
        bmax = provider_max if item["scope"] == "provider" else formality_max
        bmin[ccy] = round(bmin.get(ccy, 0.0) + float(lo), 2)
        bmax[ccy] = round(bmax.get(ccy, 0.0) + float(hi), 2)

    has_unpriced = any(i.get("fee_status") == "FEE_EXISTS_AMOUNT_NOT_AVAILABLE" for i in line_items)
    is_incomplete = any(i.get("fee_status") in _INCOMPLETE_STATUSES for i in line_items)

    # Total réglementaire combiné, uniquement si une seule devise est en jeu.
    all_ccys = set(provider_min) | set(formality_min)
    regulatory_total = None
    regulatory_total_min = None
    regulatory_total_max = None
    regulatory_total_currency = None
    if len(all_ccys) == 1:
        ccy = next(iter(all_ccys))
        regulatory_total_currency = ccy
        regulatory_total_min = round(provider_min.get(ccy, 0.0) + formality_min.get(ccy, 0.0), 2)
        regulatory_total_max = round(provider_max.get(ccy, 0.0) + formality_max.get(ccy, 0.0), 2)
        # Point unique quand min == max (aucune fourchette en jeu).
        if regulatory_total_min == regulatory_total_max:
            regulatory_total = regulatory_total_min

    # Compat : provider_fees_total/formality_fees_total exposent la borne basse
    # (identique à la borne haute en l'absence de fourchette).
    return {
        "line_items": line_items,
        "provider_fees_total": provider_min or None,
        "formality_fees_total": formality_min or None,
        "regulatory_cost_total": regulatory_total,
        "regulatory_cost_total_min": regulatory_total_min,
        "regulatory_cost_total_max": regulatory_total_max,
        "regulatory_cost_is_range": (
            regulatory_total_min is not None and regulatory_total_min != regulatory_total_max
        ),
        "regulatory_cost_currency": regulatory_total_currency,
        "complete": not is_incomplete,
        "has_unpriced_fees": has_unpriced,
        "statuses_present": sorted(
            {i.get("fee_status") for i in line_items if i.get("fee_status")}
        ),
    }
