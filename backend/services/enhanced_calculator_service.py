"""
Enhanced Tariff Calculator Service
Provides detailed calculation breakdown for NPF vs ZLECAf tariffs

Méthode de calcul (assiette cumulative - circulaire DGD algérienne + méthodes africaines standards) :
- DD   = Valeur CIF × taux_DD / 100
- DAPS = (Valeur CIF + DD) × taux_DAPS / 100
- PRCT = (Valeur CIF + DD + DAPS) × taux_PRCT / 100
- BASE TVA = CIF + DD + DAPS + PRCT + TCS + TIC + autres taxes (hors TVA)
- TVA  = BASE_TVA × taux_TVA / 100
Chaque taxe a pour assiette la valeur CIF + toutes les taxes qui la précèdent.

Source des taux : fichiers JSON pays ({ISO3}_tariffs.json), champ taxes_detail par code SH6.
"""

import json
import logging
import os
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from decimal import Decimal, ROUND_HALF_UP

logger = logging.getLogger(__name__)

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')

# Mapping des codes de taxes JSON → codes canoniques internes
TAX_CODE_MAP = {
    "D.D": "DD",
    "D.A.P.S": "DAPS",
    "T.V.A": "TVA",
    "T.C.S": "TCS",
    "PRCT": "PRCT",
    "TIC": "TIC",
    "T.P.P": "TPP",
    "TPI": "TPI",
    "CEDEAO": "CEDEAO",
    "CISS": "CISS",
    "NAC": "NAC",
    "ETLS": "ETLS",
    "LEVY": "LEVY",
}

# Informations descriptives par code canonique
TAX_META = {
    "DD":     {"name_fr": "Droit de Douane (DD)",                          "name_en": "Customs Duty (CD)"},
    "DAPS":   {"name_fr": "Droit Additionnel Provisoire de Sauvegarde",     "name_en": "Provisional Safeguard Duty"},
    "TVA":    {"name_fr": "TVA (Taxe sur la Valeur Ajoutée)",               "name_en": "VAT (Value Added Tax)"},
    "TCS":    {"name_fr": "Taxe de Contribution de Solidarité",             "name_en": "Solidarity Contribution Tax"},
    "PRCT":   {"name_fr": "Prélèvement Réglementation Commerce",            "name_en": "Trade Regulation Levy"},
    "TIC":    {"name_fr": "Taxe Intérieure de Consommation",                "name_en": "Excise Tax (TIC)"},
    "TPP":    {"name_fr": "Taxe sur les Produits Pétroliers",               "name_en": "Tax on Petroleum Products"},
    "TPI":    {"name_fr": "Prélèvement Fiscal Import",                      "name_en": "Import Fiscal Levy"},
    "CEDEAO": {"name_fr": "Prélèvement Communautaire CEDEAO",               "name_en": "ECOWAS Community Levy"},
    "CISS":   {"name_fr": "CISS (Supervision Import Globale)",              "name_en": "Comprehensive Import Supervision Scheme"},
    "NAC":    {"name_fr": "Conseil Automobile Nigérian",                    "name_en": "Nigerian Automotive Council Levy"},
    "ETLS":   {"name_fr": "Schéma de Libéralisation CEDEAO",               "name_en": "ECOWAS Trade Liberalization Scheme"},
    "LEVY":   {"name_fr": "Prélèvement Import",                             "name_en": "Import Levy"},
}

# Taxes dont le montant est EXCLU de la base TVA (circulaire DGD)
TVA_EXCLUDED_CODES = {"TAPT", "DPE", "TSV", "TSP", "T.PNEUS", "T.HUILES"}

# Fallback VAT rates par pays (si JSON non disponible)
FALLBACK_VAT = {
    "DZA": 0.19, "MAR": 0.20, "TUN": 0.19, "EGY": 0.14,
    "NGA": 0.075, "GHA": 0.125, "KEN": 0.16, "ETH": 0.15,
    "ZAF": 0.15, "CMR": 0.1925, "CIV": 0.18, "SEN": 0.18,
    "TZA": 0.18, "UGA": 0.18, "RWA": 0.18, "ANG": 0.14,
    "MOZ": 0.17, "ZMB": 0.16, "DEFAULT": 0.18,
}

# Cache JSON chargé en mémoire par pays
_tariff_cache: Dict[str, Dict] = {}


def _load_country_json(country_iso3: str) -> Optional[Dict]:
    """Charge le fichier JSON du pays (avec cache mémoire)."""
    if country_iso3 in _tariff_cache:
        return _tariff_cache[country_iso3]
    path = os.path.join(DATA_DIR, f"{country_iso3}_tariffs.json")
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        _tariff_cache[country_iso3] = data
        return data
    except Exception as e:
        logger.error(f"Impossible de charger {path}: {e}")
        return None


def _find_tariff_line(country_iso3: str, hs6: str) -> Optional[Dict]:
    """Cherche la ligne tarifaire pour un code SH6 dans le JSON du pays."""
    data = _load_country_json(country_iso3)
    if not data:
        return None
    lines = data.get("tariff_lines", [])
    hs6_clean = hs6[:6]
    for line in lines:
        if line.get("hs6", "") == hs6_clean:
            return line
    return None


def _canonical_code(raw: str) -> str:
    """Convertit un code de taxe JSON en code canonique interne."""
    return TAX_CODE_MAP.get(raw.strip(), raw.strip().replace(".", "").replace(" ", ""))


def _build_tax_list_from_json(tariff_line: Dict, zlecaf: bool = False) -> List[Dict]:
    """
    Construit la liste ordonnée des taxes à partir du champ taxes_detail du JSON.
    Pour ZLECAf, applique les fiscal_advantages (réduction/exonération DD).

    Retourne une liste de dicts :
      {code, name_fr, name_en, rate (décimal), raw_name, observation, is_tva, exclu_base_tva}
    """
    taxes_detail = tariff_line.get("taxes_detail", [])
    fiscal_adv = {}
    if zlecaf:
        for adv in tariff_line.get("fiscal_advantages", []):
            raw = adv.get("tax", "")
            code = _canonical_code(raw)
            fiscal_adv[code] = adv.get("rate", 0.0)

    result = []
    for entry in taxes_detail:
        raw_name = entry.get("tax", "")
        code = _canonical_code(raw_name)
        rate_pct = entry.get("rate", 0.0)

        if zlecaf and code in fiscal_adv:
            rate_pct = fiscal_adv[code]

        meta = TAX_META.get(code, {"name_fr": entry.get("observation", raw_name), "name_en": entry.get("observation", raw_name)})

        result.append({
            "code": code,
            "raw_name": raw_name,
            "name_fr": meta["name_fr"],
            "name_en": meta["name_en"],
            "rate": rate_pct / 100.0,
            "rate_pct": rate_pct,
            "observation": entry.get("observation", ""),
            "is_tva": code == "TVA",
            "exclu_base_tva": code in TVA_EXCLUDED_CODES,
        })
    return result


def _build_fallback_tax_list(country_iso3: str, dd_rate_pct: float, zlecaf: bool = False) -> List[Dict]:
    """
    Construit une liste de taxes minimale (DD + TVA) si le JSON du pays est absent.
    """
    vat_rate = FALLBACK_VAT.get(country_iso3, FALLBACK_VAT["DEFAULT"])
    effective_dd = 0.0 if zlecaf else dd_rate_pct / 100.0
    return [
        {
            "code": "DD", "raw_name": "D.D",
            "name_fr": "Droit de Douane (DD)", "name_en": "Customs Duty",
            "rate": effective_dd, "rate_pct": effective_dd * 100,
            "observation": "Droit de Douane", "is_tva": False, "exclu_base_tva": False,
        },
        {
            "code": "TVA", "raw_name": "T.V.A",
            "name_fr": "TVA", "name_en": "VAT",
            "rate": vat_rate, "rate_pct": vat_rate * 100,
            "observation": "Taxe sur la Valeur Ajoutée", "is_tva": True, "exclu_base_tva": False,
        },
    ]


@dataclass
class TaxLine:
    """Ligne de taxe dans la ventilation de calcul"""
    code: str
    name_fr: str
    name_en: str
    rate: float
    rate_pct: str
    base_type: str
    base_value: float
    amount: float
    is_zlecaf_exempt: bool = False
    notes: Optional[str] = None


@dataclass
class CalculationBreakdown:
    """Ventilation complète du calcul (NPF ou ZLECAf)"""
    regime: str
    regime_name_fr: str
    regime_name_en: str
    fob_value: float
    freight: float
    insurance: float
    cif_value: float
    tax_lines: List[TaxLine]
    total_taxes: float
    total_to_pay: float
    currency: str


@dataclass
class ComparisonResult:
    """Comparaison NPF vs ZLECAf"""
    hs_code: str
    hs_code_description_fr: str
    hs_code_description_en: str
    country_iso3: str
    country_name_fr: str
    country_name_en: str
    npf_calculation: CalculationBreakdown
    zlecaf_calculation: CalculationBreakdown
    savings_amount: float
    savings_percent: float
    sub_positions: Optional[List[Dict]] = None
    data_source: str = "official_tariff_json"
    data_confidence: float = 0.95


def _round2(value: float) -> float:
    return float(Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def _compute_regime(
    regime: str,
    tariff_line: Optional[Dict],
    country_iso3: str,
    cif_value: float,
    fob_value: float,
    freight: float,
    insurance: float,
    fallback_dd_pct: float = 20.0,
) -> CalculationBreakdown:
    """
    Calcule la ventilation des taxes selon la méthode officielle (assiette cumulative) :
    - Chaque taxe (hors TVA) : base = CIF + somme de toutes les taxes précédentes
    - TVA : base = CIF + somme de TOUTES les taxes qui précèdent
              (sauf les taxes explicitement exclues de la base TVA)

    Paramètres
    ----------
    regime        : 'NPF' ou 'ZLECAf'
    tariff_line   : ligne du JSON (peut être None si pays sans JSON)
    country_iso3  : code pays
    cif_value     : valeur CIF en USD
    """
    is_zlecaf = regime == "ZLECAf"

    if tariff_line:
        taxes = _build_tax_list_from_json(tariff_line, zlecaf=is_zlecaf)
    else:
        taxes = _build_fallback_tax_list(country_iso3, fallback_dd_pct, zlecaf=is_zlecaf)

    tax_lines: List[TaxLine] = []
    cumulative_before_tva = 0.0

    for t in taxes:
        if t["is_tva"]:
            # BASE TVA = CIF + toutes les taxes précédentes (hors exclusions)
            base_value = _round2(cif_value + cumulative_before_tva)
            base_type = "cif_plus_all_taxes"
            amount = _round2(base_value * t["rate"])
        else:
            # Base = CIF + toutes les taxes précédentes (méthode assiette cumulative)
            base_value = _round2(cif_value + cumulative_before_tva)
            base_type = "cif_plus_previous_taxes" if cumulative_before_tva > 0 else "cif"
            amount = _round2(base_value * t["rate"])
            # Accumule dans la base TVA (sauf taxes exclues)
            if not t["exclu_base_tva"]:
                cumulative_before_tva += amount

        is_exempt = is_zlecaf and t["code"] == "DD" and t["rate"] == 0.0
        notes = None
        if is_zlecaf and t["code"] == "DD":
            if t["rate"] == 0.0:
                notes = "Exonéré ZLECAf"
            else:
                notes = f"ZLECAf taux réduit {t['rate_pct']:.1f}%"

        tax_lines.append(TaxLine(
            code=t["code"],
            name_fr=t["name_fr"],
            name_en=t["name_en"],
            rate=t["rate"],
            rate_pct=f"{t['rate_pct']:.2f}%",
            base_type=base_type,
            base_value=base_value,
            amount=amount,
            is_zlecaf_exempt=is_exempt,
            notes=notes,
        ))

    total_taxes = _round2(sum(tl.amount for tl in tax_lines))
    total_to_pay = _round2(cif_value + total_taxes)

    regime_names = {
        "NPF":    ("Régime NPF (Nation la Plus Favorisée)", "MFN Regime (Most Favored Nation)"),
        "ZLECAf": ("Régime ZLECAf (Zone de Libre-Échange)", "AfCFTA Regime (Free Trade Area)"),
    }

    # NOTE: input values are in USD (FOB/freight/insurance), so all computed
    # tax amounts are in USD too. The local currency code (DZD/MAD/...) is
    # informational only — kept for reference. The display layer should label
    # the values as USD.
    currency_map = {
        "DZA": "DZD", "MAR": "MAD", "TUN": "TND", "EGY": "EGP",
        "NGA": "NGN", "GHA": "GHS", "KEN": "KES", "ETH": "ETB",
        "ZAF": "ZAR", "CMR": "XAF", "CIV": "XOF", "SEN": "XOF",
    }
    currency = "USD"
    local_currency = currency_map.get(country_iso3, "USD")

    return CalculationBreakdown(
        regime=regime,
        regime_name_fr=regime_names[regime][0],
        regime_name_en=regime_names[regime][1],
        fob_value=_round2(fob_value),
        freight=_round2(freight),
        insurance=_round2(insurance),
        cif_value=_round2(cif_value),
        tax_lines=tax_lines,
        total_taxes=total_taxes,
        total_to_pay=total_to_pay,
        currency=currency,
    )


class EnhancedTariffCalculator:
    """
    Calculateur tarifaire avec ventilation détaillée NPF vs ZLECAf.
    Utilise les fichiers JSON par pays comme source de vérité pour les taux.
    """

    def __init__(self):
        try:
            from etl.hs6_database import get_hs6_info
            self.get_hs6_info = get_hs6_info
        except Exception:
            self.get_hs6_info = lambda hs6, lang="fr": {}

        try:
            from etl.country_hs6_detailed import get_all_sub_positions
            self.get_sub_positions = get_all_sub_positions
        except Exception:
            self.get_sub_positions = lambda *a, **kw: []

    def _get_country_names(self, country_iso3: str) -> tuple:
        data = _load_country_json(country_iso3)
        name_map = {
            "DZA": ("Algérie", "Algeria"),           "MAR": ("Maroc", "Morocco"),
            "TUN": ("Tunisie", "Tunisia"),            "EGY": ("Égypte", "Egypt"),
            "LBY": ("Libye", "Libya"),                "MRT": ("Mauritanie", "Mauritania"),
            "NGA": ("Nigéria", "Nigeria"),            "GHA": ("Ghana", "Ghana"),
            "CIV": ("Côte d'Ivoire", "Ivory Coast"), "SEN": ("Sénégal", "Senegal"),
            "CMR": ("Cameroun", "Cameroon"),          "GAB": ("Gabon", "Gabon"),
            "KEN": ("Kenya", "Kenya"),                "ETH": ("Éthiopie", "Ethiopia"),
            "TZA": ("Tanzanie", "Tanzania"),          "UGA": ("Ouganda", "Uganda"),
            "RWA": ("Rwanda", "Rwanda"),              "ZAF": ("Afrique du Sud", "South Africa"),
            "ANG": ("Angola", "Angola"),              "MOZ": ("Mozambique", "Mozambique"),
            "ZMB": ("Zambie", "Zambia"),              "ZWE": ("Zimbabwe", "Zimbabwe"),
        }
        fr, en = name_map.get(country_iso3, (country_iso3, country_iso3))
        return fr, en

    def calculate_comparison(
        self,
        country_iso3: str,
        hs_code: str,
        fob_value: float,
        freight: float = 0.0,
        insurance: float = 0.0,
        language: str = "fr",
    ) -> ComparisonResult:
        """
        Calcule la comparaison NPF vs ZLECAf avec ventilation complète des taxes.
        """
        hs6 = hs_code[:6]
        cif_value = fob_value + freight + insurance

        hs_info = self.get_hs6_info(hs6, language) or {}
        desc_fr = hs_info.get("description_fr", f"Code SH {hs6}")
        desc_en = hs_info.get("description_en", f"HS Code {hs6}")

        tariff_line = _find_tariff_line(country_iso3, hs6)
        if tariff_line:
            fallback_dd = tariff_line.get("dd_rate", 20.0)
            data_source = "official_tariff_json"
            confidence = 0.95
        else:
            fallback_dd = 20.0
            data_source = "estimated_fallback"
            confidence = 0.60

        npf_calc = _compute_regime(
            regime="NPF",
            tariff_line=tariff_line,
            country_iso3=country_iso3,
            cif_value=cif_value,
            fob_value=fob_value,
            freight=freight,
            insurance=insurance,
            fallback_dd_pct=fallback_dd,
        )

        zlecaf_calc = _compute_regime(
            regime="ZLECAf",
            tariff_line=tariff_line,
            country_iso3=country_iso3,
            cif_value=cif_value,
            fob_value=fob_value,
            freight=freight,
            insurance=insurance,
            fallback_dd_pct=fallback_dd,
        )

        savings = _round2(npf_calc.total_to_pay - zlecaf_calc.total_to_pay)
        savings_pct = _round2((savings / npf_calc.total_to_pay * 100) if npf_calc.total_to_pay > 0 else 0)

        sub_positions = []
        try:
            sub_positions = self.get_sub_positions(country_iso3, hs6) or []
        except Exception:
            pass

        country_fr, country_en = self._get_country_names(country_iso3)

        return ComparisonResult(
            hs_code=hs_code,
            hs_code_description_fr=desc_fr,
            hs_code_description_en=desc_en,
            country_iso3=country_iso3,
            country_name_fr=country_fr,
            country_name_en=country_en,
            npf_calculation=npf_calc,
            zlecaf_calculation=zlecaf_calc,
            savings_amount=savings,
            savings_percent=savings_pct,
            sub_positions=sub_positions,
            data_source=data_source,
            data_confidence=confidence,
        )

    def to_dict(self, result: ComparisonResult) -> Dict[str, Any]:
        def convert(obj):
            if hasattr(obj, "__dataclass_fields__"):
                return {k: convert(v) for k, v in asdict(obj).items()}
            elif isinstance(obj, list):
                return [convert(item) for item in obj]
            return obj
        return convert(result)


# Instance singleton
enhanced_calculator = EnhancedTariffCalculator()


def calculate_detailed_tariff(
    country_iso3: str,
    hs_code: str,
    fob_value: float,
    freight: float = 0.0,
    insurance: float = 0.0,
    language: str = "fr",
) -> Dict[str, Any]:
    """
    Point d'entrée principal pour le calcul tarifaire détaillé.
    Retourne un dict JSON-sérialisable avec la ventilation complète NPF vs ZLECAf.
    """
    result = enhanced_calculator.calculate_comparison(
        country_iso3=country_iso3,
        hs_code=hs_code,
        fob_value=fob_value,
        freight=freight,
        insurance=insurance,
        language=language,
    )
    return enhanced_calculator.to_dict(result)
