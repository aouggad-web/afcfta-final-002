"""
Export tariff engine — cascade de calcul à l'export, par pays.
================================================================

Chaque pays a son propre système tarifaire à l'import ET à l'export.
Le moteur import existe déjà (`authentic_tariff_service.compute_tax_cascade`,
profils par pays `COUNTRY_TAX_PROFILES`). Ce module apporte le pendant export :

- taxes et redevances d'export réelles par position nationale, lues dans les
  données officielles crawlées (ex. douane.gov.tn — Tarif Web) ;
- résolution des assiettes déclarées par la source (« SOMME D.T »,
  « VALEUR DOUANE DINARS », « PN (KG) », « QCS ») ;
- marquage des frais de prestataires délégataires de missions régaliennes
  (redevances de prestations douanières) avec leur payeur
  (État ou opérateurs économiques), via le registre
  `backend/data/customs_providers/providers_registry.json` ;
- refus explicite pour tout pays sans données export crawlées (doctrine :
  jamais de calcul sur des données estimées/synthétiques).
"""

import logging
import re
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

# ── Assiettes export telles que publiées par les sources officielles ─────────
# « SOMME D.T (G=0.1.2.3.4. »  → somme des droits et taxes déjà calculés
# « VALEUR DOUANE DINARS »     → valeur douane déclarée
# « PN (KG) » / « QCS »        → poids net / quantité (droits spécifiques)

_SPECIFIC_RATE_RE = re.compile(r"^\s*([\d.,]+)\s*dinars?\s*$", re.IGNORECASE)


def _parse_specific_dinars(raw_value: str) -> Optional[float]:
    """Extrait un tarif spécifique en dinars ('0.3 dinars') → 0.3 ; sinon None."""
    if not raw_value:
        return None
    m = _SPECIFIC_RATE_RE.match(str(raw_value))
    if not m:
        return None
    try:
        return float(m.group(1).replace(",", "."))
    except ValueError:
        return None


def _base_kind(assiette: str) -> str:
    """Classe l'assiette déclarée par la source officielle."""
    a = (assiette or "").upper()
    if "SOMME D.T" in a or "SOMME DROITS" in a:
        return "SUM_DUTIES_TAXES"
    if "VALEUR DOUANE" in a or "VAL.DOU" in a:
        return "CUSTOMS_VALUE"
    if "PN" in a and "KG" in a:
        return "NET_WEIGHT_KG"
    if a.startswith("QCS"):
        return "QUANTITY"
    return "CUSTOMS_VALUE" if not a else "UNKNOWN"


def get_export_profile(country_iso3: str) -> Dict:
    """
    Profil du système tarifaire export d'un pays, combinant :
    - les taxes export réelles de la position (données crawlées) ;
    - les prestataires délégataires et leurs payeurs (registre).
    Les pays sans données crawlées sont refusés explicitement (doctrine).
    """
    from services.crawled_data_service import crawled_service

    registry = load_providers_registry()
    country_entry = registry.get("countries", {}).get(country_iso3.upper(), {})
    return {
        "country_iso3": country_iso3.upper(),
        "verification_status": country_entry.get("verification_status", "A_DOCUMENTER"),
        "tariff_system": country_entry.get("tariff_system", {}),
        "providers": country_entry.get("providers", []),
    }


def compute_export_taxes(
    country_iso3: str,
    hs_code: str,
    customs_value: float = 0.0,
    quantity: float = 0.0,
    net_weight_kg: float = 0.0,
    currency: str = "TND",
) -> Dict:
    """
    Calcule la cascade de taxes/redevances à l'export pour une position
    nationale, selon les assiettes officielles déclarées dans la source crawlée.

    Args:
        country_iso3: pays exportateur (ISO3)
        hs_code: code SH national (6-12 chiffres)
        customs_value: valeur douane déclarée (devise locale du tarif)
        quantity: quantité en unités statistiques (droits spécifiques QCS)
        net_weight_kg: poids net kg (droits spécifiques au kg)

    Returns:
        Détail par taxe (montants, assiettes, sources), frais de prestataires
        marqués avec leur payeur, total — ou refus explicite si aucune donnée
        export officielle crawlée.
    """
    from services.crawled_data_service import crawled_service

    country_iso3 = country_iso3.upper()
    hs_code_clean = re.sub(r"[^0-9]", "", hs_code or "")

    export_data = None
    try:
        export_data = crawled_service.get_export_taxes(country_iso3, hs_code_clean)
    except ValueError as e:
        return {
            "error": f"Code pays invalide : {e}",
            "export_data_available": False,
        }

    if not export_data:
        return {
            "error": (
                f"Aucune taxe/redevance à l'export publiée par une source officielle "
                f"crawlée pour {country_iso3}/{hs_code_clean}. Conformément à la "
                "doctrine tarifaire, aucun calcul n'est effectué sur données estimées."
            ),
            "export_data_available": False,
            "country_iso3": country_iso3,
            "hs_code": hs_code_clean,
        }

    # Payeurs des frais de prestataires (registre par pays)
    registry = load_providers_registry()
    country_reg = registry.get("countries", {}).get(country_iso3, {})
    paid_by_map = {}
    for provider in country_reg.get("providers", []):
        for fee_code in provider.get("fee_codes", []):
            paid_by_map[fee_code] = {
                "paid_by": provider.get("paid_by", "INCONNU"),
                "paid_by_note": provider.get("paid_by_note", ""),
                "provider_mission": provider.get("delegated_missions", ""),
                "legal_basis": provider.get("legal_basis", ""),
            }

    steps: List[Dict] = []
    sum_duties_taxes = 0.0

    for tax in export_data.get("export_taxes", []):
        code = tax.get("code", "")
        name = tax.get("name", code)
        rate_pct = tax.get("rate_pct")
        raw_value = tax.get("raw_value", "")
        assiette = tax.get("assiette", "")
        base_kind = _base_kind(assiette)
        amount = None
        base_value = None
        method = None

        specific = _parse_specific_dinars(raw_value)
        if specific is not None:
            # Droit spécifique (ex. ferrailles : 0.3 dinars/kg)
            base_value = net_weight_kg if "PN" in assiette.upper() else quantity
            amount = round(specific * (base_value or 0.0), 4)
            method = (
                f"Spécifique : {raw_value} × {'PN (KG)' if 'PN' in assiette.upper() else 'QCS'}"
            )
        elif rate_pct is not None:
            if base_kind == "SUM_DUTIES_TAXES":
                base_value = sum_duties_taxes
                method = "Assiette officielle : SOMME D.T (droits et taxes)"
            else:
                base_value = customs_value
                method = f"Assiette officielle : {assiette or 'VALEUR DOUANE'}"
            amount = round(base_value * float(rate_pct) / 100.0, 4)

        if amount is None:
            continue

        sum_duties_taxes += amount

        step = {
            "code": code,
            "name": name,
            "rate_pct": rate_pct,
            "raw_value": raw_value,
            "base_formula": assiette,
            "base_kind": base_kind,
            "base_value": base_value,
            "calculation_method": method,
            "amount": amount,
            "source": tax.get("source", ""),
            "is_provider_fee": tax.get("is_provider_fee", False),
        }
        step.update(paid_by_map.get(code, {}))
        steps.append(step)

    provider_fees = [s for s in steps if s.get("is_provider_fee")]

    return {
        "success": True,
        "country_iso3": country_iso3,
        "hs_code": hs_code_clean,
        "position_code": export_data.get("code", ""),
        "designation": export_data.get("designation", ""),
        "export_cascade": steps,
        "total_export_taxes": round(sum(s["amount"] for s in steps), 4),
        "provider_fees": {
            "total": round(sum(s["amount"] for s in provider_fees), 4),
            "steps": provider_fees,
            "note": (
                "Frais de prestataires délégataires de missions régaliennes, "
                "payés par les opérateurs économiques déclarants (voir registre)."
                if provider_fees
                else "Aucun frais de prestataire sur cette position."
            ),
        },
        "tariff_system": country_reg.get("tariff_system", {}),
        "source": export_data.get("source", ""),
        "currency": currency,
        "informational_only": True,
        "legally_binding": False,
    }


# ── Registre des prestataires (cache mémoire) ────────────────────────────────

_providers_registry_cache: Optional[Dict] = None


def load_providers_registry(force: bool = False) -> Dict:
    """Charge le registre des prestataires délégataires (JSON sourcé)."""
    global _providers_registry_cache
    if _providers_registry_cache is not None and not force:
        return _providers_registry_cache
    import json
    import os

    path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "data",
        "customs_providers",
        "providers_registry.json",
    )
    try:
        with open(path, "r", encoding="utf-8") as f:
            _providers_registry_cache = json.load(f)
    except Exception as e:
        logger.error(f"Error loading providers registry: {e}")
        _providers_registry_cache = {"countries": {}}
    return _providers_registry_cache


def get_country_providers(country_iso3: str) -> List[Dict]:
    """Prestataires délégataires documentés pour un pays (peut être vide)."""
    entry = load_providers_registry().get("countries", {}).get(country_iso3.upper(), {})
    return [
        p
        for p in entry.get("providers", [])
        if entry.get("verification_status") == "VERIFIE_SOURCE_CRAWLEE"
    ]
