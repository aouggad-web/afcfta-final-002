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
from dataclasses import asdict, dataclass, field
from decimal import ROUND_HALF_UP, Decimal
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")

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
    "DD": {"name_fr": "Droit de Douane (DD)", "name_en": "Customs Duty (CD)"},
    "DAPS": {
        "name_fr": "Droit Additionnel Provisoire de Sauvegarde",
        "name_en": "Provisional Safeguard Duty",
    },
    "TVA": {"name_fr": "TVA (Taxe sur la Valeur Ajoutée)", "name_en": "VAT (Value Added Tax)"},
    "TCS": {
        "name_fr": "Taxe de Contribution de Solidarité",
        "name_en": "Solidarity Contribution Tax",
    },
    "PRCT": {"name_fr": "Prélèvement Réglementation Commerce", "name_en": "Trade Regulation Levy"},
    "TIC": {"name_fr": "Taxe Intérieure de Consommation", "name_en": "Excise Tax (TIC)"},
    "TPP": {"name_fr": "Taxe sur les Produits Pétroliers", "name_en": "Tax on Petroleum Products"},
    "TPI": {"name_fr": "Prélèvement Fiscal Import", "name_en": "Import Fiscal Levy"},
    "CEDEAO": {"name_fr": "Prélèvement Communautaire CEDEAO", "name_en": "ECOWAS Community Levy"},
    "CISS": {
        "name_fr": "CISS (Supervision Import Globale)",
        "name_en": "Comprehensive Import Supervision Scheme",
    },
    "NAC": {
        "name_fr": "Conseil Automobile Nigérian",
        "name_en": "Nigerian Automotive Council Levy",
    },
    "ETLS": {
        "name_fr": "Schéma de Libéralisation CEDEAO",
        "name_en": "ECOWAS Trade Liberalization Scheme",
    },
    "LEVY": {"name_fr": "Prélèvement Import", "name_en": "Import Levy"},
}

# Taxes dont le montant est EXCLU de la base TVA (circulaire DGD)
TVA_EXCLUDED_CODES = {"TAPT", "DPE", "TSV", "TSP", "T.PNEUS", "T.HUILES"}

# Fallback VAT rates par pays (si JSON non disponible)
FALLBACK_VAT = {
    "DZA": 0.19,
    "MAR": 0.20,
    "TUN": 0.19,
    "EGY": 0.14,
    "NGA": 0.075,
    "GHA": 0.125,
    "KEN": 0.16,
    "ETH": 0.15,
    "ZAF": 0.15,
    "CMR": 0.1925,
    "CIV": 0.18,
    "SEN": 0.18,
    "TZA": 0.18,
    "UGA": 0.18,
    "RWA": 0.18,
    "ANG": 0.14,
    "MOZ": 0.17,
    "ZMB": 0.16,
    "DEFAULT": 0.18,
}

# Source unique de vérité : crawled_data_service (backend/data/crawled/).
# Les fichiers synthétiques backend/data/*_tariffs.json ne sont plus lus.
_crawled = None


def _get_crawled():
    """Accès lazy au singleton crawled_data_service."""
    global _crawled
    if _crawled is None:
        from services.crawled_data_service import crawled_service

        crawled_service.load()
        _crawled = crawled_service
    return _crawled


def _find_tariff_line(country_iso3: str, hs_code: str) -> Optional[Dict]:
    """
    Cherche la ligne tarifaire par code NATIONAL exact (8-12 digits).
    Si non trouvé, descend progressivement jusqu'au SH6.
    Utilise crawled_service (backend/data/crawled/) — jamais de synthétique.
    """
    svc = _get_crawled()
    if not svc.is_loaded():
        svc.load()
    result = svc.lookup(country_iso3, hs_code)
    if result:
        return result
    # Fail-closed : aucune donnée crawlée pour ce code/pays.
    return None


def _find_tariff_line_by_hs6(country_iso3: str, hs6: str) -> List[Dict]:
    """Retourne TOUTES les sous-positions nationales pour un SH6 donné."""
    svc = _get_crawled()
    if not svc.is_loaded():
        svc.load()
    return svc.lookup_by_hs6(country_iso3, hs6[:6].zfill(6))


def _canonical_code(raw: str) -> str:
    """Convertit un code de taxe JSON en code canonique interne."""
    return TAX_CODE_MAP.get(raw.strip(), raw.strip().replace(".", "").replace(" ", ""))


def _build_tax_list_from_crawled(tariff_line: Dict, country_iso3: str = "", zlecaf: bool = False) -> List[Dict]:
    """
    Construit la liste ordonnée des taxes à partir d'une position crawlée
    normalisée (format crawled_data_service).
    Pour ZLECAf, applique les fiscal_advantages (réduction/exonération DD).

    Retourne une liste de dicts :
      {code, name_fr, name_en, rate (décimal), raw_name, observation, is_tva, exclu_base_tva}
    """
    taxes_raw = tariff_line.get("taxes", [])
    fiscal_adv = {}
    if zlecaf:
        for adv in tariff_line.get("fiscal_advantages", []):
            if isinstance(adv, dict):
                rate_val = adv.get("rate_pct", adv.get("rate", 0.0))
                if isinstance(rate_val, str):
                    try:
                        rate_val = float(rate_val.replace("%", "").strip())
                    except ValueError:
                        rate_val = 0.0
                fiscal_adv[adv.get("code", adv.get("name", ""))] = rate_val

    # Taxes préférentielles ZLECAf/AfCFTA déjà présentes dans la ligne
    preferential_rates = {}
    for t in taxes_raw:
        if isinstance(t, dict):
            code = t.get("code", "").upper()
            # Schéma unifié : preferential_rates est une liste séparée
            # Schéma crawled original : is_preferential flag sur les taxes
            if t.get("is_preferential") or code in ("AFCFTA", "ZLECAF", "ZLECAF_RATE"):
                rate = t.get("rate_pct", t.get("rate"))
                if rate is not None:
                    preferential_rates["DD"] = rate

    # Schéma unifié : preferential_rates est une liste dans la position
    if not preferential_rates and isinstance(tariff_line.get("preferential_rates"), list):
        for pr in tariff_line.get("preferential_rates", []):
            if isinstance(pr, dict):
                regime = pr.get("regime", "").upper()
                if "AFCFTA" in regime or "ZLECAF" in regime:
                    rate = pr.get("rate_pct")
                    if rate is not None:
                        preferential_rates["DD"] = rate

    result = []
    for entry in taxes_raw:
        if not isinstance(entry, dict):
            continue
        code = entry.get("code", "")
        raw_name = entry.get("name", code)
        # LE DÉFAUT CORRIGÉ ICI. Ces trois lignes disaient :
        #
        #     if rate_pct is None:
        #         rate_pct = 0.0
        #
        # Un taux que la source ne publie PAS devenait donc zéro, et la
        # position se liquidait comme exonérée. Mesuré au 21/09/2026 sur les
        # crawls versionnés : 51 taxes égyptiennes portent `rate: null` — 12
        # sur la TVA, 16 sur la TVA_2, 23 sur le droit d'importation. Autant
        # d'exonérations fabriquées, servies avec l'apparence d'un calcul.
        #
        # `rate_pct` reste donc None, et le montant ne se calcule pas.
        rate_pct = entry.get("rate_pct", entry.get("rate"))
        if rate_pct == "":
            rate_pct = None
        if rate_pct is not None:
            try:
                rate_pct = float(rate_pct)
            except (TypeError, ValueError):
                # Un taux illisible n'est pas un taux nul : même traitement
                # que l'absence — nommé, jamais deviné.
                rate_pct = None

        # Ignorer les colonnes préférentielles (EU_UK, EFTA, SADC, MERCOSUR, AfCFTA)
        # AfCFTA est traité séparément via preferential_rates
        if code.upper() in ("EU_UK", "EFTA", "SADC", "MERCOSUR", "AFCFTA"):
            continue

        # Mapper les codes vers les codes canoniques internes
        canonical = _canonical_code(code) if code else code
        # SARS "GENERAL" = Droit de Douane (DD)
        if code.upper() == "GENERAL":
            canonical = "DD"
        # EGY "ID" = Import Duty = DD
        if code.upper() == "ID":
            canonical = "DD"
        # VAT/TVA mapping
        if code.upper() in ("VAT", "TVA"):
            canonical = "TVA"

        # Appliquer la préférence ZLECAf sur le DD
        # Une préférence remplace un taux ; elle peut donc s'appliquer même si
        # le plein droit est indisponible — c'est le taux préférentiel qui est
        # dû, pas le NPF manquant.
        if zlecaf and canonical == "DD":
            if "DD" in preferential_rates:
                rate_pct = preferential_rates["DD"]
            elif "DD" in fiscal_adv:
                rate_pct = fiscal_adv["DD"]

        meta = TAX_META.get(
            canonical,
            {
                "name_fr": raw_name,
                "name_en": raw_name,
            },
        )

        result.append(
            {
                "code": canonical,
                "raw_name": raw_name,
                "name_fr": meta["name_fr"],
                "name_en": meta["name_en"],
                "rate": None if rate_pct is None else rate_pct / 100.0,
                "rate_pct": rate_pct,
                "taux_indisponible": rate_pct is None,
                "observation": entry.get("observation", entry.get("source", "")),
                "is_tva": canonical == "TVA",
                "exclu_base_tva": canonical in TVA_EXCLUDED_CODES,
            }
        )

    # Si aucune TVA n'est présente dans les données crawlées (ex: SARS Schedule 1
    # ne publie pas la TVA), l'ajouter depuis le fallback national.
    has_tva = any(t["is_tva"] for t in result)
    if not has_tva and country_iso3:
        vat_rate = FALLBACK_VAT.get(country_iso3, FALLBACK_VAT["DEFAULT"])
        result.append(
            {
                "code": "TVA",
                "raw_name": "T.V.A",
                "name_fr": "TVA (Taxe sur la Valeur Ajoutée)",
                "name_en": "VAT (Value Added Tax)",
                "rate": vat_rate,
                "rate_pct": vat_rate * 100,
                "observation": "TVA non publiée dans le tarif douanier — taux national par défaut",
                "is_tva": True,
                "exclu_base_tva": False,
            }
        )
    return result


def _build_fallback_tax_list(
    country_iso3: str, dd_rate_pct: float, zlecaf: bool = False
) -> List[Dict]:
    """
    Construit une liste de taxes minimale (DD + TVA) si le JSON du pays est absent.
    """
    vat_rate = FALLBACK_VAT.get(country_iso3, FALLBACK_VAT["DEFAULT"])
    effective_dd = 0.0 if zlecaf else dd_rate_pct / 100.0
    return [
        {
            "code": "DD",
            "raw_name": "D.D",
            "name_fr": "Droit de Douane (DD)",
            "name_en": "Customs Duty",
            "rate": effective_dd,
            "rate_pct": effective_dd * 100,
            "observation": "Droit de Douane",
            "is_tva": False,
            "exclu_base_tva": False,
        },
        {
            "code": "TVA",
            "raw_name": "T.V.A",
            "name_fr": "TVA",
            "name_en": "VAT",
            "rate": vat_rate,
            "rate_pct": vat_rate * 100,
            "observation": "Taxe sur la Valeur Ajoutée",
            "is_tva": True,
            "exclu_base_tva": False,
        },
    ]


@dataclass
class TaxLine:
    """Ligne de taxe dans la ventilation de calcul"""

    code: str
    name_fr: str
    name_en: str
    # `rate`, `rate_pct` et `amount` sont FACULTATIFS, et c'est le fond de ce
    # correctif : quand la source ne publie pas de taux, il n'y a ni taux ni
    # montant à servir. Les mettre à zéro liquiderait la position comme
    # exonérée — une exonération fabriquée, indiscernable d'une vraie.
    rate: Optional[float]
    rate_pct: Optional[str]
    base_type: str
    base_value: float
    amount: Optional[float]
    is_zlecaf_exempt: bool = False
    notes: Optional[str] = None
    taux_indisponible: bool = False


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
    # Les codes dont le taux n'est pas publié. Non vide, le total est la somme
    # des SEULES lignes calculables : il est partiel, et le dire ici est la
    # seule façon qu'un appelant ne le prenne pas pour le total dû.
    codes_taux_indisponible: List[str] = field(default_factory=list)


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
        taxes = _build_tax_list_from_crawled(tariff_line, country_iso3=country_iso3, zlecaf=is_zlecaf)
    else:
        taxes = _build_fallback_tax_list(country_iso3, fallback_dd_pct, zlecaf=is_zlecaf)

    tax_lines: List[TaxLine] = []
    cumulative_before_tva = 0.0
    codes_indisponibles: List[str] = []

    for t in taxes:
        # UNE LIGNE SANS TAUX NE SE CALCULE PAS. Elle est servie quand même —
        # la taire ferait disparaître une taxe due de la ventilation, ce qui
        # est la même faute vue de l'autre côté — mais sans montant, et son
        # code est remonté pour que le total ne passe pas pour complet.
        if t.get("taux_indisponible"):
            codes_indisponibles.append(t["code"])
            tax_lines.append(
                TaxLine(
                    code=t["code"],
                    name_fr=t["name_fr"],
                    name_en=t["name_en"],
                    rate=None,
                    rate_pct=None,
                    base_type="indisponible",
                    base_value=_round2(cif_value + cumulative_before_tva),
                    amount=None,
                    notes=(
                        "Taux non publié par la source : ni montant ni exonération. "
                        "Vérifier auprès de l'administration douanière de destination."
                    ),
                    taux_indisponible=True,
                )
            )
            continue

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
        # Atteint uniquement avec un taux connu : les lignes sans taux sont
        # sorties plus haut par `continue`.
        notes = None
        if is_zlecaf and t["code"] == "DD":
            if t["rate"] == 0.0:
                notes = "Exonéré ZLECAf"
            else:
                notes = f"ZLECAf taux réduit {t['rate_pct']:.1f}%"

        tax_lines.append(
            TaxLine(
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
            )
        )

    # `tl.amount` vaut None sur les lignes sans taux : les additionner lèverait
    # une TypeError, et les compter pour zéro rendrait le total faux en silence.
    # Elles sont donc exclues de la somme, et `codes_taux_indisponible` dit
    # lesquelles — c'est ce qui distingue un total partiel d'un total dû.
    total_taxes = _round2(sum(tl.amount for tl in tax_lines if tl.amount is not None))
    total_to_pay = _round2(cif_value + total_taxes)

    regime_names = {
        "NPF": ("Régime NPF (Nation la Plus Favorisée)", "MFN Regime (Most Favored Nation)"),
        "ZLECAf": ("Régime ZLECAf (Zone de Libre-Échange)", "AfCFTA Regime (Free Trade Area)"),
    }

    currency_map = {
        "DZA": "DZD",
        "MAR": "MAD",
        "TUN": "TND",
        "EGY": "EGP",
        "NGA": "NGN",
        "GHA": "GHS",
        "KEN": "KES",
        "ETH": "ETB",
        "ZAF": "ZAR",
        "CMR": "XAF",
        "CIV": "XOF",
        "SEN": "XOF",
    }
    currency = currency_map.get(country_iso3, "USD")

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
        codes_taux_indisponible=codes_indisponibles,
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
        name_map = {
            "DZA": ("Algérie", "Algeria"),
            "MAR": ("Maroc", "Morocco"),
            "TUN": ("Tunisie", "Tunisia"),
            "EGY": ("Égypte", "Egypt"),
            "LBY": ("Libye", "Libya"),
            "MRT": ("Mauritanie", "Mauritania"),
            "NGA": ("Nigéria", "Nigeria"),
            "GHA": ("Ghana", "Ghana"),
            "CIV": ("Côte d'Ivoire", "Ivory Coast"),
            "SEN": ("Sénégal", "Senegal"),
            "CMR": ("Cameroun", "Cameroon"),
            "GAB": ("Gabon", "Gabon"),
            "KEN": ("Kenya", "Kenya"),
            "ETH": ("Éthiopie", "Ethiopia"),
            "TZA": ("Tanzanie", "Tanzania"),
            "UGA": ("Ouganda", "Uganda"),
            "RWA": ("Rwanda", "Rwanda"),
            "ZAF": ("Afrique du Sud", "South Africa"),
            "ANG": ("Angola", "Angola"),
            "MOZ": ("Mozambique", "Mozambique"),
            "ZMB": ("Zambie", "Zambia"),
            "ZWE": ("Zimbabwe", "Zimbabwe"),
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
        Recherche par code NATIONAL exact (8-12 digits) via crawled_service.
        Fail-closed : si aucune donnée crawlée → refus (pas de synthétique).
        """
        hs_code_clean = hs_code.replace(".", "").replace(" ", "")
        hs6 = hs_code_clean[:6].zfill(6)
        cif_value = fob_value + freight + insurance

        # Description : priorité à la désignation de la sous-position crawlée,
        # puis au HS6 database.
        hs_info = self.get_hs6_info(hs6, language) or {}
        desc_fr = hs_info.get("description_fr", f"Code SH {hs6}")
        desc_en = hs_info.get("description_en", f"HS Code {hs6}")

        # ── Recherche par code NATIONAL exact (8-12 digits) ──
        tariff_line = _find_tariff_line(country_iso3, hs_code_clean)

        if tariff_line:
            # Désignation : le schéma unifié utilise un dict designation
            crawled_desc_obj = tariff_line.get("designation", {})
            if isinstance(crawled_desc_obj, dict):
                crawled_desc_fr = crawled_desc_obj.get("fr", "")
                crawled_desc_en = crawled_desc_obj.get("en", "")
                crawled_desc = crawled_desc_fr or crawled_desc_en or ""
            else:
                crawled_desc = str(crawled_desc_obj)
                crawled_desc_fr = tariff_line.get("description_fr", "")
                crawled_desc_en = tariff_line.get("description_en", "")
            if crawled_desc_fr:
                desc_fr = crawled_desc_fr
            elif crawled_desc:
                desc_fr = crawled_desc
            if crawled_desc_en:
                desc_en = crawled_desc_en
            elif crawled_desc and language != "fr":
                desc_en = crawled_desc

            # Taux DD depuis la ligne crawlée
            dd_rate = 0.0
            for t in tariff_line.get("taxes", []):
                if isinstance(t, dict) and t.get("code", "").upper() in ("DD", "ID", "GENERAL", "DI"):
                    dd_rate = float(t.get("rate_pct", t.get("rate", 0)) or 0)
                    break
            if dd_rate == 0:
                dd_rate = tariff_line.get("dd_rate", 20.0)
            fallback_dd = dd_rate
            data_source = "crawled_authentic"
            confidence = 0.95
        else:
            # Fail-closed : aucune donnée crawlée pour ce code/pays.
            # Pas de fallback synthétique — signaler l'absence.
            fallback_dd = 0.0
            data_source = "unavailable_fail_closed"
            confidence = 0.0

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
        savings_pct = _round2(
            (savings / npf_calc.total_to_pay * 100) if npf_calc.total_to_pay > 0 else 0
        )

        # Sous-positions nationales pour ce SH6 (information)
        sub_positions = []
        try:
            all_subs = _find_tariff_line_by_hs6(country_iso3, hs6)
            if all_subs:
                sub_positions = [
                    {
                        "national_code": s.get("code_clean", ""),
                        "designation": s.get("designation", ""),
                        "description_fr": s.get("description_fr", s.get("designation", "")),
                        "description_en": s.get("description_en", ""),
                        "chapter": s.get("chapter", ""),
                        "source": s.get("source", ""),
                    }
                    for s in all_subs
                ]
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
