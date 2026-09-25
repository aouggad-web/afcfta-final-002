import json
import logging
import os
import re
from collections import OrderedDict
from math import isfinite
from typing import Dict, Optional

from services.designation import texte_designation
from services.tax_profile_data import (
    ASSIETTE_TVA_ETABLIE,
    ASSIETTE_TVA_NON_APPLICABLE,
    BASE_TVA_TOUTES_TAXES,
    COUNTRY_TAX_PROFILES,
)

logger = logging.getLogger(__name__)
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
CRAWLED_DIR = os.path.join(DATA_DIR, "crawled")
_tariff_cache = {}
_nomenclature_cache = {}
_CRAWLED_INDEX_CACHE_MAX_COUNTRIES = 4
_crawled_index_cache = OrderedDict()  # {ISO3: {national_hs_code: position_entry}}
_available_countries_cache = None
_postgres_provider_cache = None


def _clean_crawled_hs_code(entry: dict) -> str:
    """Return the first usable national/HS code exposed by a crawled row."""
    for key in (
        "hs_code",
        "code_clean",
        "code",
        "national_code",
        "raw_code",
        "code_raw",
        "hs6",
    ):
        raw_code = entry.get(key)
        if raw_code is None:
            continue
        code = re.sub(r"\D", "", str(raw_code))
        if len(code) >= 6:
            return code
    return ""


def _adapt_crawled_position(entry: dict, parent: Optional[dict] = None) -> Optional[dict]:
    """Expose one source position without changing its tariff columns."""
    code = _clean_crawled_hs_code(entry)
    if not code:
        return None

    parent = parent or {}
    description = (
        entry.get("name")
        or entry.get("description")
        or entry.get("designation")
        or entry.get("description_fr")
        or entry.get("description_en")
        or entry.get("name_fr_from_previous_crawl")
        or entry.get("desc_ar")
        or parent.get("description_fr")
        or parent.get("description_en")
        or parent.get("designation")
        or ""
    )
    source = entry.get("source") or parent.get("source") or "crawled"
    result = dict(entry)
    result.update(
        {
            "hs_code": code,
            "name": texte_designation(description),
            "description": texte_designation(description),
            "description_fr": texte_designation(entry.get("description_fr") or description, "fr"),
            "description_en": texte_designation(entry.get("description_en") or description, "en"),
            "source": source,
            "source_url": entry.get("source_url") or parent.get("source_url"),
            "source_quality": (
                entry.get("source_quality")
                or parent.get("source_quality")
                or entry.get("data_format")
                or parent.get("data_format")
                or "crawled_unclassified"
            ),
            "advantages": entry.get("advantages", entry.get("fiscal_advantages", [])),
        }
    )
    return result


def _iter_crawled_positions(data: dict):
    """Yield rows from every crawled schema currently present in the repo."""
    for key in ("sub_positions", "positions"):
        rows = data.get(key)
        if isinstance(rows, list):
            for row in rows:
                if isinstance(row, dict):
                    yield row, data

    tariff_lines = data.get("tariff_lines")
    if not isinstance(tariff_lines, list):
        return
    for line in tariff_lines:
        if not isinstance(line, dict):
            continue
        parent = dict(data)
        parent.update(line)
        sub_positions = line.get("sub_positions")
        if isinstance(sub_positions, list) and sub_positions:
            for row in sub_positions:
                if isinstance(row, dict):
                    yield row, parent


def load_crawled_position_index(country_iso3: str) -> dict:
    """
    Load a country crawled file and index every source position by HS code.

    Supported repository schemas:
    - ``sub_positions[]`` (DZA and WITS-normalised sources),
    - ``positions[]`` (national/regional crawlers),
    - ``tariff_lines[].sub_positions[]`` (canonical_v4).

    Returns ``{clean_hs_code: normalised_entry}`` for fast per-position lookup.
    Cached in memory after first load.
    """
    country_iso3 = _validate_iso3(country_iso3)
    if country_iso3 in _crawled_index_cache:
        _crawled_index_cache.move_to_end(country_iso3)
        return _crawled_index_cache[country_iso3]

    file_path = os.path.join(CRAWLED_DIR, f"{country_iso3}_tariffs.json")
    if not os.path.exists(file_path):
        _cache_crawled_position_index(country_iso3, {})
        return {}

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        index = {}
        for raw_position, parent in _iter_crawled_positions(data):
            position = _adapt_crawled_position(raw_position, parent)
            if position:
                index[position["hs_code"]] = position
        _cache_crawled_position_index(country_iso3, index)
        logger.info(f"Loaded crawled position index for {country_iso3}: {len(index)} entries")
        return index
    except Exception as e:
        logger.error(f"Error loading crawled index for {country_iso3}: {e}")
        _cache_crawled_position_index(country_iso3, {})
        return {}


def _cache_crawled_position_index(country_iso3: str, index: dict) -> None:
    """Keep only the most recently used country indexes in process memory."""
    _crawled_index_cache[country_iso3] = index
    _crawled_index_cache.move_to_end(country_iso3)
    while len(_crawled_index_cache) > _CRAWLED_INDEX_CACHE_MAX_COUNTRIES:
        _crawled_index_cache.popitem(last=False)


# Only allow well-formed ISO 2- or 3-letter country codes to prevent path traversal.
_ISO_CODE_RE = re.compile(r"^[A-Z]{2,3}$")


def _validate_iso3(country_iso3: str) -> str:
    """Normalise to uppercase and reject codes that could traverse the filesystem."""
    code = country_iso3.upper().strip()
    if not _ISO_CODE_RE.match(code):
        raise ValueError(f"Invalid country code: {country_iso3!r}")
    return code


def _get_postgres_provider():
    """Return PostgreSQL tariff provider when available, else None."""
    global _postgres_provider_cache
    if _postgres_provider_cache is False:
        return None
    if _postgres_provider_cache is not None:
        return _postgres_provider_cache
    try:
        from services.postgres_tariff_service import get_postgres_tariff_service

        _postgres_provider_cache = get_postgres_tariff_service()
        return _postgres_provider_cache
    except Exception as e:
        logger.info(f"PostgreSQL tariff provider unavailable, using ETL fallback: {e}")
        _postgres_provider_cache = False
        return None


def _log_etl_fallback(operation: str, country_iso3: str, hs_code: str = "", reason: str = ""):
    context = f"{operation} {country_iso3}"
    if hs_code:
        context += f"/{hs_code}"
    if reason:
        context += f" ({reason})"
    logger.warning(f"Tariff ETL fallback activated: {context}")


#: Les trois orthographes sous lesquelles la TVA apparaît dans les profils.
_ALIAS_TVA = ("TVA", "T.V.A", "VAT")

# Human-readable labels for each tax code
_TAX_LABELS = {
    "DD": "Droits de Douane",
    "DAPS": "Droit Additionnel Provisoire de Sauvegarde",
    "PRCT": "Précompte sur Impôt",
    "TCS": "Taxe de Contribution de Solidarité",
    "TVA": "Taxe sur la Valeur Ajoutée",
    "TPI": "Taxe Parafiscale à l'Importation",
    "CEDEAO": "Prélèvement Communautaire CEDEAO",
    "GETFUND": "Ghana Education Trust Fund Levy",
    "NHIL": "National Health Insurance Levy",
    "CISS": "Comprehensive Import Supervision Scheme",
    "IDF": "Import Declaration Fee",
    "RDL": "Railway Development Levy",
    "TCI": "Taxe Communautaire d'Intégration",
    "CAC": "Centimes Additionnels Communaux",
    "RS": "Redevance Statistique",
    "PCS": "Prélèvement Communautaire de Solidarité",
    "SUR": "Taxe Additionnelle / Accises",
    "TCL": "Taxe de Compensation des Licences",
    "D.D": "Droits de Douane",
    "T.V.A": "Taxe sur la Valeur Ajoutée",
}


def _normalize_tax_code(code: str) -> str:
    """Normalise 'D.D' → 'DD', 'T.V.A' → 'TVA', etc."""
    return code.replace(".", "").replace(" ", "").replace("/", "").replace("-", "").upper()


def _canonical_tax_code(code: str, label: str = "") -> str:
    """Map tax aliases found in generated country tariff files to calculator codes.

    The recent tariff files use source-native labels/codes (DI in Morocco, CET
    in EAC, VAT/IVA/TVA-APTAXE, GETFL in Ghana, etc.).  The cascade profiles
    are intentionally expressed with canonical calculator codes, so every tax
    coming from `taxes_detail` must be canonicalized before selecting bases.
    """
    norm = _normalize_tax_code(code)
    text = f"{norm} {label or ''}".lower()

    if norm in {"DD", "DI", "ID", "DROIT", "DDDROIT", "GENERAL", "CET", "DR"}:
        return "DD"
    if norm in {"TVA", "TVAI", "TVAAPTAXE", "TVAAP", "VAT", "IVA", "VALUEADDE", "VALUE_ADDE"}:
        return "TVA"
    if "value added" in text or "valeur ajoute" in text or "valeur ajout" in text:
        return "TVA"
    if "customs duty" in text or "import duty" in text or "droit d'importation" in text:
        return "DD"
    if norm in {"IMPORTDEC", "IMPORTDECL", "IMPORT_DEC", "IDF"} or "import declaration" in text:
        return "IDF"
    if norm in {"RAILWAYDE", "RAILWAY_DE", "RDL"} or "railway development" in text:
        return "RDL"
    if norm in {"GETFL", "GETFUND"} or "ghana education" in text:
        return "GETFUND"
    if norm in {"SR", "SUR"} or "surtax" in text:
        return "SUR"
    if norm in {"RPDIMPORREDEV", "RPDIMPOR", "TCL"}:
        return "TCL"
    return norm


# Codes TVA équivalents selon le pays (portugais IVA, anglais VAT, tunisien
# TVA/APTAXE) — un seul et même impôt fonctionnellement, jamais deux taxes
# distinctes. _find_vat_key() doit être utilisé PARTOUT où un code de taxe est
# comparé à "TVA" pour éviter (a) de rater le taux réel des pays non-DZA/MAR/
# COM/MDG/MRT (qui utilisent IVA/VAT), et (b) de la compter deux fois — une
# fois comme "TVA" au taux périmé de l'autre source, une fois comme sa propre
# entrée "IVA"/"VAT" dans le détail par taxe.
_VAT_EQUIVALENT_CODES = ("TVA", "IVA", "VAT", "TVAI")

# Preferential duty columns describe an alternative trade regime. They remain
# available verbatim on the crawled row but must never be added to the NPF tax
# cascade alongside the general customs duty.
# D2R is the Ethiopian source's COMESA preferential duty column.
_PREFERENTIAL_RATE_CODES = frozenset(
    {"AFCFTA", "ZLECAF", "SADC", "COMESA", "D2R", "EU_UK", "EUUK", "EFTA", "MERCOSUR"}
)


def _is_vat_code(code: str) -> bool:
    norm = _normalize_tax_code(code)
    return norm in _VAT_EQUIVALENT_CODES or norm.startswith("TVA/") or norm.startswith("TVA-")


def _find_vat_key(crawled_taxes: dict) -> Optional[str]:
    for k in crawled_taxes:
        if _is_vat_code(k):
            return k
    return None


def _parse_crawled_tax_rate(value) -> Optional[float]:
    """Read a rate without mutating the source-specific tax representation."""
    if isinstance(value, dict):
        value = value.get("rate", value.get("rate_pct"))
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return float(value) if isfinite(value) and value >= 0 else None
    if isinstance(value, str):
        if value.strip().lower() in {"free", "exempt", "exonere", "exonéré"}:
            return 0.0
        # A specific or compound expression is not an ad-valorem percentage.
        match = re.fullmatch(r"\s*(\d+(?:[.,]\d+)?)\s*%?\s*", value)
        if match:
            return float(match.group(1).replace(",", "."))
    return None


def _position_tax_payload(position):
    if "taxes_import" in position:
        return position["taxes_import"]
    return position.get("taxes")


def _normalise_crawled_tax_details(raw_taxes) -> dict:
    """Adapt dict, scalar-map and list tax schemas for runtime calculations.

    The returned mapping is derived and canonical. ``raw_taxes`` is retained
    unchanged on the crawled position so source columns (including
    preferential columns such as AfCFTA or SADC) remain available verbatim.
    """
    details = {}
    if isinstance(raw_taxes, dict):
        rows = []
        for code, value in raw_taxes.items():
            info = value if isinstance(value, dict) else {}
            rows.append(
                {
                    "code": code,
                    "name": info.get("name", info.get("label", info.get("label_published", code))),
                    "rate": value,
                    "source": info.get("source", "crawled"),
                }
            )
    elif isinstance(raw_taxes, list):
        rows = [row for row in raw_taxes if isinstance(row, dict)]
    else:
        return details

    for row in rows:
        code = row.get("code", row.get("tax", row.get("tax_code", "")))
        label = row.get("name", row.get("label", row.get("tax_name", row.get("observation", code))))
        value = row.get("rate", row.get("rate_pct", row.get("raw_value")))
        rate = _parse_crawled_tax_rate(value)
        if not code:
            continue
        canonical = _canonical_tax_code(code, label)
        if canonical in _PREFERENTIAL_RATE_CODES or row.get("is_preferential"):
            continue
        details[canonical] = {
            "label": label or _TAX_LABELS.get(canonical, canonical),
            "rate": rate,
            "source": row.get("source", "crawled"),
            "source_tax_code": code,
        }
    return details


def compute_tax_cascade(
    cif_value: float, taxes_rates: dict, country_iso3: str, fob_value: Optional[float] = None
) -> dict:
    """
    Compute import taxes using the official cascade method for each country.

    Args:
        cif_value:    CIF value of the goods
        taxes_rates:  {normalized_code: rate_pct}  e.g. {'DD': 30, 'DAPS': 60, 'TVA': 19}
        country_iso3: ISO-3 country code

    Returns a dict with:
        steps:          list of per-tax calculation steps (base, rate, amount)
        total_taxes:    total tax amount (excluding CIF)
        total_to_pay:   CIF + total_taxes
        effective_rate_pct:  (total_taxes / cif_value) × 100
        legal_source:   official legal reference used
    """
    profile = COUNTRY_TAX_PROFILES.get(country_iso3)
    profile_status = "country_specific" if profile else "default"

    # ── Default profile for unmapped countries ────────────────────────────────
    # All taxes on CIF; TVA on CIF+DD (most common pattern)
    if not profile:
        ordered_codes = list(taxes_rates.keys())
        bases = {c: ("CIF", []) for c in ordered_codes}
        # If TVA or T.V.A present, apply on CIF+DD
        for vat_alias in ("TVA", "T.V.A"):
            if vat_alias in bases:
                bases[vat_alias] = ("CIF", ["DD"] if "DD" in bases else [])
        profile = {
            "taxes_order": ordered_codes,
            "tax_bases": bases,
            "source": "Profil par défaut (TVA base = CIF+DD)",
        }

    # Work on request-local copies: profiles intentionally share regional base
    # dictionaries, and a source-specific extra tax must not leak into another
    # country or a later calculation.
    taxes_order = list(profile["taxes_order"])
    tax_bases = dict(profile["tax_bases"])
    legal_source = profile.get("source", "")

    # Build a normalized lookup: norm_code → rate
    norm_rates = {_canonical_tax_code(k): v for k, v in taxes_rates.items()}

    # Add any taxes present in the data but not in the profile (apply on CIF)
    for code in list(norm_rates.keys()):
        if code not in [_normalize_tax_code(c) for c in taxes_order]:
            taxes_order.append(code)
            tax_bases[code] = ("CIF", [])

    # ── Assiette de la TVA établie sur texte primaire ────────────────────────
    # Là où un texte a été lu et archivé, il prime sur le profil codé : les
    # quatre textes disposent que l'assiette est la valeur en douane augmentée
    # de TOUS les droits et taxes d'entrée, la TVA seule exclue. Le profil, lui,
    # applique « CIF + DD » et ampute donc l'assiette de tout le reste.
    regle_tva = ASSIETTE_TVA_ETABLIE.get(country_iso3)
    if regle_tva:
        alias_presents = [c for c in taxes_order if _normalize_tax_code(c) in _ALIAS_TVA]
        # Garde-fou : une taxe assise sur la TVA rendrait la cascade circulaire
        # dès lors que la TVA s'assied sur toutes les autres. Aucun des onze
        # pays concernés n'est dans ce cas aujourd'hui ; si cela changeait, le
        # profil codé doit continuer de s'appliquer plutôt qu'un calcul faux.
        circulaire = any(
            any(
                _normalize_tax_code(dep) in _ALIAS_TVA
                for dep in (tax_bases.get(c) or ("CIF", []))[1]
            )
            for c in taxes_order
        )
        if alias_presents and not circulaire:
            for code in alias_presents:
                tax_bases[code] = (BASE_TVA_TOUTES_TAXES, [])
            # La TVA doit être liquidée en dernier : son assiette contient les
            # montants de toutes les autres taxes, qui doivent donc être connus.
            for code in alias_presents:
                taxes_order.remove(code)
                taxes_order.append(code)
            legal_source = regle_tva["texte"]
            profile_status = "assiette_tva_texte_primaire"

    # Compute amounts in order, tracking each computed amount for cascade reuse
    computed_amounts: dict = {}  # norm_code → amount
    steps = []
    cumulative = cif_value

    for raw_code in taxes_order:
        norm_code = _normalize_tax_code(raw_code)
        rate = norm_rates.get(norm_code, 0.0)
        if rate == 0:
            continue

        base_formula, add_codes = tax_bases.get(raw_code, tax_bases.get(norm_code, ("CIF", [])))

        # Compute the base value
        if base_formula == "FOB":
            # Valeur en douane SACU : fret et assurance internationaux exclus
            # (Act 91/1964 s.65-67). Elle ne se déduit JAMAIS de la valeur CIF
            # — la part du fret et de l'assurance n'est pas connue ici. Sans
            # valeur FOB fournie, le droit ne se liquide pas : une base CIF
            # substituée produirait un montant crédible et faux (fail-closed).
            if fob_value is None:
                raise ValueError(
                    "valeur_fob requise : la valeur en douane SACU est la valeur FOB "
                    "(fret et assurance internationaux exclus) et ne peut être déduite "
                    "de la valeur CIF — voir Customs and Excise Act 91/1964 s.65-67"
                )
            if fob_value > cif_value:
                raise ValueError(
                    "valeur_fob ne peut excéder la valeur cif_value : le fret et "
                    "l'assurance ajoutés à la FOB composent la CIF"
                )
            base_value = fob_value
        elif base_formula == "DD_AMOUNT":
            # e.g. CAC = % of DD_amount
            base_value = computed_amounts.get("DD", 0.0)
        elif base_formula == BASE_TVA_TOUTES_TAXES:
            # Valeur en douane + tous les montants déjà liquidés, la taxe
            # elle-même exclue. Rien n'est énuméré : ce qui entre dans
            # l'assiette est ce que la source publie pour cette position.
            base_value = cif_value + sum(
                montant for code, montant in computed_amounts.items() if code != norm_code
            )
        else:
            # 'CIF' + optional already-computed amounts
            base_value = cif_value
            for dep_code in add_codes:
                base_value += computed_amounts.get(_normalize_tax_code(dep_code), 0.0)

        amount = round(base_value * rate / 100, 2)
        computed_amounts[norm_code] = amount
        cumulative = round(cumulative + amount, 2)

        label = _TAX_LABELS.get(norm_code, _TAX_LABELS.get(raw_code, raw_code))
        if base_formula == "DD_AMOUNT":
            base_desc = "DD_montant"
        elif base_formula == "FOB":
            base_desc = "FOB"
        elif base_formula == BASE_TVA_TOUTES_TAXES:
            autres = [c for c in computed_amounts if c != norm_code]
            base_desc = "CIF + " + " + ".join(autres) if autres else "CIF"
        elif add_codes:
            base_desc = "CIF + " + " + ".join(add_codes)
        else:
            base_desc = "CIF"

        steps.append(
            {
                "code": norm_code,
                "label": label,
                "rate_pct": rate,
                "base_formula": base_desc,
                "base_value": round(base_value, 2),
                "amount": amount,
                "cumulative": cumulative,
            }
        )

    total_taxes = round(sum(s["amount"] for s in steps), 2)
    total_to_pay = round(cif_value + total_taxes, 2)
    effective_rate_pct = round(total_taxes / cif_value * 100, 2) if cif_value > 0 else 0.0

    return {
        "steps": steps,
        "total_taxes": total_taxes,
        "total_to_pay": total_to_pay,
        "effective_rate_pct": effective_rate_pct,
        "legal_source": legal_source,
        "profile_status": profile_status,
    }


_COUNTRY_NAMES = {
    "DZA": "Algérie",
    "MAR": "Maroc",
    "TUN": "Tunisie",
    "EGY": "Égypte",
    "LBY": "Libye",
    "NGA": "Nigeria",
    "ZAF": "Afrique du Sud",
    "KEN": "Kenya",
    "ETH": "Éthiopie",
    "GHA": "Ghana",
    "CIV": "Côte d'Ivoire",
    "SEN": "Sénégal",
    "CMR": "Cameroun",
    "AGO": "Angola",
    "TZA": "Tanzanie",
    "UGA": "Ouganda",
    "BWA": "Botswana",
    "BEN": "Bénin",
    "BFA": "Burkina Faso",
    "BDI": "Burundi",
    "CPV": "Cap-Vert",
    "CAF": "Centrafrique",
    "COM": "Comores",
    "COG": "Congo",
    "COD": "RD Congo",
    "DJI": "Djibouti",
    "ERI": "Érythrée",
    "GAB": "Gabon",
    "GMB": "Gambie",
    "GIN": "Guinée",
    "GNB": "Guinée-Bissau",
    "GNQ": "Guinée Équatoriale",
    "LBR": "Libéria",
    "LSO": "Lesotho",
    "MDG": "Madagascar",
    "MWI": "Malawi",
    "MLI": "Mali",
    "MRT": "Mauritanie",
    "MUS": "Maurice",
    "MOZ": "Mozambique",
    "NAM": "Namibie",
    "NER": "Niger",
    "RWA": "Rwanda",
    "STP": "Sao Tomé-et-Príncipe",
    "SYC": "Seychelles",
    "SLE": "Sierra Leone",
    "SOM": "Somalie",
    "SDN": "Soudan",
    "SSD": "Soudan du Sud",
    "SWZ": "Eswatini",
    "TGO": "Togo",
    "ZMB": "Zambie",
    "ZWE": "Zimbabwe",
}


def load_country_tariffs(country_iso3):
    country_iso3 = _validate_iso3(country_iso3)
    if country_iso3 in _tariff_cache:
        return _tariff_cache[country_iso3]
    file_path = os.path.join(DATA_DIR, f"{country_iso3}_tariffs.json")
    if not os.path.exists(file_path):
        return None
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        logger.error(f"Error loading tariffs for {country_iso3}: {e}")
        return None

    # Doctrine tarifaire : refuser les fichiers non conformes (estimé/synthétique
    # sans source officielle vérifiable) et signaler explicitement le pays.
    from services.tariff_doctrine import evaluate_country_file

    servable, reason_code, detail = evaluate_country_file(data)
    if not servable:
        logger.warning(
            "Doctrine refusal for %s: %s (%s) — file not served",
            country_iso3,
            reason_code,
            detail,
        )
        _tariff_cache[country_iso3] = None
        return None

    _tariff_cache[country_iso3] = data
    return data


def load_nomenclature_map(country_iso3):
    """Load nomenclature map for countries with extended sub-positions (like DZA)."""
    country_iso3 = _validate_iso3(country_iso3)
    if country_iso3 in _nomenclature_cache:
        return _nomenclature_cache[country_iso3]

    file_path = os.path.join(DATA_DIR, f"{country_iso3}_nomenclature_map.json")
    if not os.path.exists(file_path):
        return None

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        _nomenclature_cache[country_iso3] = data
        logger.info(f"Loaded nomenclature map for {country_iso3}: {len(data)} entries")
        return data
    except Exception as e:
        logger.error(f"Error loading nomenclature map for {country_iso3}: {e}")
        return None


def get_tariff_line(country_iso3, hs_code):
    country_iso3 = _validate_iso3(country_iso3)
    hs_code_clean = hs_code.replace(".", "").replace(" ", "")
    hs6 = hs_code_clean[:6]

    provider = _get_postgres_provider()
    if provider:
        try:
            regulatory = provider.get_regulatory_details(country_iso3, hs_code_clean)
            country_info = provider.get_country_info(country_iso3) or {}
            if regulatory and regulatory.get("success"):
                measures = regulatory.get("measures", []) or []
                requirements = regulatory.get("requirements", []) or []
                taxes_detail = [
                    {
                        "tax": _normalize_tax_code(str(m.get("code") or m.get("type") or "")),
                        "rate": float(m["rate"]) if m.get("rate") is not None else None,
                        "observation": m.get("name", m.get("type", "")),
                        "source": "postgres",
                    }
                    for m in measures
                    if (m.get("code") or m.get("type"))
                ]
                other_taxes_rate = round(
                    sum(
                        t["rate"]
                        for t in taxes_detail
                        if t["tax"] not in ("DD", "TVA") and t["rate"] is not None
                    ),
                    4,
                )
                sub_positions = provider.get_sub_positions(country_iso3, hs6, "fr") or []
                normalized_sub_positions = [
                    {
                        "code": sp.get("code"),
                        "digits": sp.get("digits", len(sp.get("code", ""))),
                        "description_fr": sp.get("description_fr", sp.get("description_en", "")),
                        "description_en": sp.get("description_en", sp.get("description_fr", "")),
                        "dd": float(sp.get("dd", 0) or 0),
                        "source": "postgres",
                    }
                    for sp in sub_positions
                    if sp.get("code")
                ]
                fiscal_advantages = [
                    {
                        "tax_code": m.get("code"),
                        "condition_fr": f"ZLECAF applicable: {m.get('name', m.get('type', ''))}",
                        "condition_en": f"AfCFTA applicable: {m.get('name', m.get('type', ''))}",
                        "reduced_rate_pct": m.get("zlecaf_rate"),
                    }
                    for m in measures
                    if m.get("zlecaf_applicable") and m.get("zlecaf_rate") is not None
                ]
                dd_rate = regulatory.get("taxes", {}).get("dd_rate")
                vat_rate = regulatory.get("taxes", {}).get("vat_rate", country_info.get("vat_rate"))
                return {
                    "hs6": hs6,
                    "code": hs_code_clean,
                    "description_fr": regulatory.get("description", ""),
                    "description_en": regulatory.get("description", ""),
                    "dd_rate": float(dd_rate) if dd_rate is not None else None,
                    "zlecaf_rate": (
                        float(regulatory.get("taxes", {}).get("zlecaf_rate"))
                        if regulatory.get("taxes", {}).get("zlecaf_rate") is not None
                        else None
                    ),
                    "vat_rate": float(vat_rate) if vat_rate is not None else None,
                    "other_taxes_rate": other_taxes_rate,
                    "taxes_detail": taxes_detail,
                    "fiscal_advantages": fiscal_advantages,
                    "administrative_formalities": requirements,
                    "sub_positions": normalized_sub_positions,
                    "source": "postgres",
                    "data_source": "postgres",
                }
            _log_etl_fallback("get_tariff_line", country_iso3, hs6, "postgres-miss")
        except Exception as e:
            _log_etl_fallback("get_tariff_line", country_iso3, hs6, f"postgres-error: {e}")

    data = load_country_tariffs(country_iso3)
    if not data:
        return None
    for line in data.get("tariff_lines", []):
        if line.get("hs6") == hs6 or line.get("code") == hs_code_clean:
            return line
    position = load_crawled_position_index(country_iso3).get(hs_code_clean)
    if position and len(hs_code_clean) > 6:
        taxes = _normalise_crawled_tax_details(_position_tax_payload(position))
        return {
            "hs6": hs6,
            "code": hs_code_clean,
            "description_fr": position.get("description_fr", ""),
            "description_en": position.get("description_en", ""),
            "dd_rate": taxes.get("DD", {}).get("rate"),
            "vat_rate": taxes.get("TVA", {}).get("rate"),
            "taxes_detail": [
                {"tax": tax_code, "rate": tax["rate"], "observation": tax["label"]}
                for tax_code, tax in taxes.items()
            ],
            "sub_positions": [],
            "administrative_formalities": position.get(
                "formalities", position.get("administrative_formalities", [])
            ),
            "source": position.get("source"),
        }
    return None


def get_sub_positions(country_iso3, hs6, language="fr"):
    """
    Return all national sub-positions for a given HS6 code.

    Merges sub-positions from two sources so that every national position is
    returned even when tariff_lines only carries a subset:

    1. Sub-positions with explicit DD rates stored inside the parent
       tariff_line (``line['sub_positions']``).
    2. All entries in the optional ``{ISO3}_nomenclature_map.json`` file that
       begin with the requested HS6 prefix (e.g. DZA_nomenclature_map.json
       contains 7610909910 which is missing from tariff_lines).

    The parent DD rate is used as the fallback rate for positions that only
    appear in the nomenclature map.
    """
    country_iso3 = _validate_iso3(country_iso3)
    hs6_normalized = hs6.replace(".", "").replace(" ", "")[:6]

    merged: Dict[str, dict] = {}
    provider = _get_postgres_provider()
    if provider:
        try:
            postgres_positions = (
                provider.get_sub_positions(country_iso3, hs6_normalized, language) or []
            )
            if postgres_positions:
                for sp in postgres_positions:
                    code = sp.get("code")
                    if not code:
                        continue
                    merged[code] = {
                        "code": sp.get("code"),
                        "national_code": sp.get("code"),
                        "digits": sp.get("digits", len(sp.get("code", ""))),
                        "description_fr": sp.get("description_fr", sp.get("description_en", "")),
                        "description_en": sp.get("description_en", sp.get("description_fr", "")),
                        "dd_rate": float(sp.get("dd", 0) or 0),
                        "source": "postgres",
                    }
            else:
                _log_etl_fallback(
                    "get_sub_positions", country_iso3, hs6_normalized, "postgres-miss"
                )
        except Exception as e:
            _log_etl_fallback(
                "get_sub_positions", country_iso3, hs6_normalized, f"postgres-error: {e}"
            )

    line = get_tariff_line(country_iso3, hs6_normalized)
    parent_dd_rate_pct = line.get("dd_rate", 0) if line else 0

    # Build index from tariff_lines sub_positions (have explicit DD rates)
    if line:
        for sp in line.get("sub_positions", []):
            code = sp.get("code", "")
            if code and code not in merged:
                merged[code] = {
                    "code": code,
                    "national_code": code,
                    "digits": sp.get("digits", len(code)),
                    "description_fr": sp.get("description_fr", sp.get("description_en", "")),
                    "description_en": sp.get("description_en", sp.get("description_fr", "")),
                    "dd_rate": sp.get("dd", parent_dd_rate_pct),
                    "source": sp.get("source", f"Nomenclature nationale DGD {country_iso3}"),
                }

    # Exact collected rates override stale listing aggregates. PostgreSQL
    # remains authoritative where it provided the position.
    for code, position in load_crawled_position_index(country_iso3).items():
        if not (code.startswith(hs6_normalized) and len(code) > 6):
            continue
        if code in merged and merged[code].get("source") == "postgres":
            continue
        taxes = _position_tax_payload(position)
        dd_rate = _parse_crawled_tax_rate(position.get("dd"))
        if dd_rate is None:
            dd_rate = _parse_crawled_tax_rate(position.get("dd_rate"))
        normalised_taxes = _normalise_crawled_tax_details(taxes)
        if dd_rate is None:
            dd_rate = _parse_crawled_tax_rate(normalised_taxes.get("DD"))
        merged[code] = {
            "code": code,
            "national_code": code,
            "digits": len(code),
            "description_fr": position.get("description_fr") or position.get("name", ""),
            "description_en": position.get("description_en") or position.get("name", ""),
            "dd_rate": dd_rate,
            "duty_status": "PAYABLE" if dd_rate is not None else "UNAVAILABLE",
            "source": position.get("source", "crawled"),
            "source_url": position.get("source_url"),
            "source_quality": position.get("source_quality"),
        }

    # Merge with nomenclature_map – adds positions missing from tariff_lines
    # and enriches descriptions for existing ones
    nomenclature = load_nomenclature_map(country_iso3)
    if nomenclature:
        for code, description in nomenclature.items():
            if not (code.startswith(hs6_normalized) and len(code) > 6):
                continue
            if code not in merged:
                merged[code] = {
                    "code": code,
                    "national_code": code,
                    "digits": len(code),
                    "description_fr": description,
                    "description_en": description,
                    "dd_rate": parent_dd_rate_pct,
                    "source": f"Nomenclature DGD {country_iso3}",
                }
            else:
                # Enrich with official description when the tariff_lines entry
                # only has a generic placeholder (e.g. "Autres - Autre")
                if not merged[code].get("description_fr"):
                    merged[code]["description_fr"] = description
                if not merged[code].get("description_en"):
                    merged[code]["description_en"] = description

    result = sorted(merged.values(), key=lambda x: x["code"])
    result = _detacher_cle_de_controle(country_iso3, result)
    logger.debug(f"get_sub_positions({country_iso3}, {hs6_normalized}): {len(result)} positions")
    return result


def _longueur_position_declaree(country_iso3):
    """La longueur de la POSITION TARIFAIRE quand le pays déclare une clé.

    La déclaration vit dans le fichier de socle du pays — un seul endroit, et
    pays par pays. Rien n'est déduit d'une longueur observée.
    """
    try:
        from services import socle as _socle

        return (_socle.charger(country_iso3).get("nomenclature") or {}).get("longueur_position")
    except Exception:  # pragma: no cover - socle absent ou pays non servi
        return None


def _position_sans_cle(country_iso3, code):
    """Ramener un code SAISI à la position, qu'il porte ou non sa clé.

    Le chemin historique indexe les codes que `get_sub_positions` lui rend,
    désormais sans clé. Un opérateur qui recopie sa déclaration en douane tape
    pourtant les onze caractères : sans cette normalisation, il se verrait
    répondre « Position nationale introuvable » sur un code que le produit
    affichait lui-même hier.
    """
    longueur = _longueur_position_declaree(country_iso3)
    if longueur and len(code) == longueur + 1 and code.isdigit():
        return code[:longueur]
    return code


def _detacher_cle_de_controle(country_iso3, positions):
    """Rendre la POSITION TARIFAIRE, sans la clé de contrôle qui la suit.

    La Tunisie publie `01012100015`. Ce n'est pas un code à onze chiffres :
    c'est la sous-position `0101210001` suivie de la clé `5`, que le déclarant
    saisit avec elle sur la déclaration en douane. Les servir collés faisait
    afficher au sélecteur « HS11 digits » — le produit affirmait une
    nomenclature tunisienne à onze chiffres, qui n'existe pas — et faisait
    répondre « Position nationale introuvable » au code que l'opérateur tape.

    Le pays DÉCLARE sa nomenclature dans son propre fichier de socle ; rien
    n'est déduit d'une longueur. L'Éthiopie porte aussi des codes de onze
    caractères, mais son onzième est toujours « 0 » — un remplissage, pas une
    clé — et elle ne déclare rien : ses codes ressortent intacts.

    La clé n'est pas perdue pour autant : elle accompagne la position sous
    `cle_controle`, puisqu'elle sert à la saisie.
    """
    longueur = _longueur_position_declaree(country_iso3)
    if not longueur:
        return positions

    detachees = []
    for position in positions:
        code = str(position.get("code") or "")
        if len(code) != longueur + 1 or not code.isdigit():
            detachees.append(position)
            continue
        copie = dict(position)
        copie["code"] = code[:longueur]
        copie["national_code"] = code[:longueur]
        copie["cle_controle"] = code[longueur:]
        copie["digits"] = longueur
        # `code_raw` est délibérément RETIRÉ, pas renseigné avec le code
        # complet. `select_calculation_position` indexe par `code_raw` en
        # priorité : l'y laisser à onze caractères remettrait l'index à onze
        # pendant que la requête, elle, est à dix — index et requête doivent
        # s'accorder. Le code complet se reconstruit après la sélection, à
        # partir de `cle_controle`, là où le moteur en a besoin.
        copie.pop("code_raw", None)
        detachees.append(copie)
    return detachees


def get_taxes_detail(country_iso3, hs_code):
    line = get_tariff_line(country_iso3, hs_code)
    return line.get("taxes_detail", line.get("taxes", [])) if line else []


def get_fiscal_advantages(country_iso3, hs_code):
    line = get_tariff_line(country_iso3, hs_code)
    return line.get("fiscal_advantages", []) if line else []


def _normalize_crawled_formalities(raw_formalities):
    """Adapt a crawled position's own ``formalities`` (``text_verbatim``/
    ``source``) to the ``administrative_formalities`` shape the frontend
    renders (``document_fr``/``document_en``). Position-specific formalities
    take precedence over the generic HS6-level ones (see calculate_import_taxes):
    otherwise a generic chapter-level formality meant for another product
    (e.g. a CKD/SKD vehicle-assembly authorization) can be shown for an
    unrelated finished product sharing the same HS6.
    """
    if not raw_formalities:
        return []
    normalized = []
    for item in raw_formalities:
        if not isinstance(item, dict):
            continue
        text = item.get("text_verbatim") or item.get("document_fr") or item.get("document_en")
        if not text:
            continue
        normalized.append(
            {
                "code": item.get("code"),
                "document_fr": item.get("document_fr", text),
                "document_en": item.get("document_en", text),
                "fap_official_label": item.get("fap_official_label"),
            }
        )
    return normalized


#: États d'une demande de formalités. Les trois se confondaient en une liste
#: vide, et cette confusion est la plus coûteuse du produit : une absence
#: d'information n'est pas une absence d'obligation.
FORMALITES_DOCUMENTEES = "DOCUMENTEES"
FORMALITES_AUCUNE_PARTICULIERE = "AUCUNE_FORMALITE_PARTICULIERE"
FORMALITES_NON_ETABLIES = "NON_ETABLIES"
FORMALITES_POSITION_INTROUVABLE = "POSITION_INTROUVABLE"

#: PAYS DONT LA SOURCE PUBLIE SES FORMALITÉS DE FAÇON EXHAUSTIVE.
#:
#: Pour ces pays — et pour eux seuls — une liste vide n'est PAS une lacune :
#: c'est un constat de la source, qui publie le bloc quand une formalité
#: particulière existe et ne publie rien quand il n'y en a pas. Le produit dit
#: alors quelque chose de POSITIF au lieu d'une réserve.
#:
#: Ce que cet état n'affirme toujours PAS : que l'importation soit dispensée de
#: toute obligation. Il dit qu'aucune formalité PARTICULIÈRE ne frappe cette
#: marchandise. Les obligations générales du pays — déclaration en douane,
#: domiciliation bancaire — ne sont volontairement pas portées par le produit :
#: elles s'appliquent à toute importation sans distinction de position, et
#: l'opérateur qui consulte une position tarifaire les connaît. Décision du
#: propriétaire, prise le 21/09/2026 — déclarée ici pour qu'elle ne soit pas
#: reprise plus tard comme un oubli.
#:
#: CORRECTION D'UNE ERREUR DE MA PART, relevée par le propriétaire. J'avais
#: rangé la « déclaration d'importation du produit » algérienne parmi ces
#: obligations générales. C'est faux : ce n'est pas la déclaration en douane,
#: c'est une demande adressée aux services du contrôle de la qualité du
#: ministère du Commerce. Elle est donc PARTICULIÈRE, attachée à des
#: marchandises précises — et le produit la sert déjà, sur 6 816 positions
#: algériennes.
#:
#: 902 ET 910 SONT DES CODES DE DOCUMENTS, pas des noms de procédure : la DGD
#: codifie ainsi les pièces de sa liste FAP — 902 « Autorisation d'admission du
#: produit », 910 « Déclaration d'importation du produit », et de même 140,
#: 150, 160, 210, 215. Sur les 6 816 positions portant la déclaration
#: d'importation, 96 seulement en portent le code : les 6 720 autres ont le
#: même libellé sans code, faute de rapprochement à la liste. Écart constaté,
#: non corrigé ici — il n'ôte rien à l'exigence, il en retire l'identifiant.
#:
#: Chaque entrée exige sa preuve, relevée sur le portail. Ne jamais ajouter un
#: pays ici « par analogie » : c'est exactement la généralisation que le Maroc a
#: démentie sur les droits nuls.
SOURCES_EXHAUSTIVES_FORMALITES = {
    "DZA": (
        "conformepro.dz publie un bloc « Formalités » lorsqu'une formalité "
        "administrative particulière (FAP) existe, et aucun bloc sinon. Vérifié "
        "le 21/09/2026 sur un échantillon tiré au sort de 80 positions : les 60 "
        "positions sans formalité au crawl ne portent AUCUN bloc au portail, et "
        "19 des 20 positions avec formalité en portent un (la vingtième a échoué "
        "en réseau). Le crawl conserve d'ailleurs le code officiel de chaque "
        "formalité (`fap_code`, `match_status: MATCHED_DGD_FAP_LIST`)."
    ),
}


def get_administrative_formalities(country_iso3, hs_code):
    """Les formalités documentées pour cette position, éventuellement vides.

    Conservée telle quelle pour ses appelants existants. Qui a besoin de
    SAVOIR pourquoi la liste est vide appelle `formalites_et_statut()` :
    c'est cette distinction, et non la liste, qui empêche le produit
    d'affirmer qu'aucune obligation n'existe.
    """
    return formalites_et_statut(country_iso3, hs_code)[0]


def formalites_et_statut(country_iso3, hs_code):
    """(formalités, statut) — et le statut dit POURQUOI la liste est vide.

    LE DÉFAUT CORRIGÉ. `get_administrative_formalities()` rendait `[]` dans
    trois situations que rien ne distinguait ensuite :

      * la position porte des formalités              → on les sert ;
      * la position existe et n'en porte aucune       → rien n'est documenté ;
      * la position est INTROUVABLE                   → on n'a rien cherché.

    L'interface masquait alors purement et simplement la carte « Documents
    requis ». L'opérateur voyait un résultat complet — taxes, avantages, coût
    réglementaire — sans le moindre signe que les formalités n'avaient jamais
    été établies. Mesuré sur les crawls du 21/09/2026 : **315 185 positions sur
    350 022 (90 %) ne portent aucune formalité, et 46 pays sur 54 n'en portent
    aucune du tout**. Le silence était donc la règle, pas l'exception.

    Ce que ce statut n'affirme PAS : `NON_ETABLIES` ne veut pas dire
    « aucune obligation ». Le dépôt ne collecte nulle part une attestation
    d'absence d'obligation ; il collecte des formalités, ou rien. Tant qu'une
    telle attestation n'existe pas dans la source, `NON_ETABLIES` est le seul
    état honnête pour une liste vide, et l'interface doit le dire au lieu de
    se taire.
    """
    line = get_tariff_line(country_iso3, hs_code)
    if line is None:
        return [], FORMALITES_POSITION_INTROUVABLE
    formalites = line.get("administrative_formalities") or []
    if formalites:
        return formalites, FORMALITES_DOCUMENTEES
    # Une source exhaustive change la nature de la liste vide : elle cesse
    # d'être une lacune pour devenir un constat. Voir
    # SOURCES_EXHAUSTIVES_FORMALITES, dont chaque entrée porte sa preuve.
    if str(country_iso3 or "").upper() in SOURCES_EXHAUSTIVES_FORMALITES:
        return [], FORMALITES_AUCUNE_PARTICULIERE
    return [], FORMALITES_NON_ETABLIES


def _build_result_from_crawled_position(code, sp, etl_positions, country_iso3):
    """Format one crawled national position into a search result row.

    Shared by both the direct national-code match (step 1) and the HS6→code
    resolution when an ETL HS6-level query needs a specific national code
    (step 2) — same shape either way.
    """
    taxes = _normalise_crawled_tax_details(sp.get("taxes"))
    etl_position = etl_positions.get(code, {})
    dd = _parse_crawled_tax_rate(sp.get("dd"))
    if dd is None:
        dd = _parse_crawled_tax_rate(sp.get("dd_rate"))
    if dd is None:
        dd = _parse_crawled_tax_rate(taxes.get("DD"))
    if dd is None:
        dd = _parse_crawled_tax_rate(etl_position.get("dd_rate"))
    tva = _parse_crawled_tax_rate(taxes.get("TVA"))
    if tva is None:
        tva = _parse_crawled_tax_rate(etl_position.get("vat_rate"))
    if tva is None:
        tva = 0.0
    tcs = taxes.get("TCS", {}).get("rate", 0)
    prct = taxes.get("PRCT", {}).get("rate", 0)
    daps = taxes.get("DAPS", {}).get("rate", 0)
    # Effective rate = total_taxes / CIF×100 (cascade, not sum of rates).
    # Include every applicable source tax (PCC, TPI, etc.) while
    # excluding alternative preferential duty columns.
    cascade_rates = {
        tax_code: details["rate"]
        for tax_code, details in taxes.items()
        if tax_code not in _PREFERENTIAL_RATE_CODES and details["rate"] > 0
    }
    if dd is None:
        cascade_rates.pop("DD", None)
    elif dd > 0:
        cascade_rates["DD"] = dd
    if tva > 0:
        cascade_rates["TVA"] = tva
    # Métrique de référence par position : FOB = CIF ici (fret nul). Ce taux
    # affiché n'est pas une liquidation — celle-ci exige la valeur FOB réelle
    # de l'importation (voir compute_tax_cascade, fail-closed).
    ref_cascade = compute_tax_cascade(100.0, cascade_rates, country_iso3, fob_value=100.0)
    return {
        "hs6": code[:6],
        "national_code": code,
        "description_fr": sp.get("name") or sp.get("description") or "",
        "description_en": sp.get("name") or sp.get("description") or "",
        "designation": sp.get("designation") or sp.get("name") or "",
        "dd_rate": dd,
        "duty_status": "PAYABLE" if dd is not None else "UNAVAILABLE",
        "tva_rate": tva,
        "tcs_rate": tcs,
        "prct_rate": prct,
        "daps_rate": daps,
        "effective_rate": ref_cascade["effective_rate_pct"],
        "total_rate": ref_cascade["effective_rate_pct"],  # kept for compat
        "advantages": sp.get("advantages", []),
        "source": sp.get("source") or "crawled",
        "source_url": sp.get("source_url"),
        "source_quality": sp.get("source_quality", "crawled_unclassified"),
    }


def search_tariff_lines(country_iso3, query, language="fr", limit=20):
    """Search tariff lines by HS code prefix or description keyword.

    Priority order:
    1. PostgreSQL results when available
    2. Missing crawled authentic positions (national codes)
    3. ETL tariff_lines (HS6-level)
    4. Nomenclature map (extended national codes)
    """
    country_iso3 = _validate_iso3(country_iso3)
    q = query.lower().strip()
    results = []
    seen_codes = set()

    provider = _get_postgres_provider()
    if provider:
        try:
            pg_results = (
                provider.search_commodities(country_iso3, query, limit=limit, language=language)
                or []
            )
            if pg_results:
                for r in pg_results:
                    national_code = r.get("code", r.get("hs6", ""))
                    results.append(
                        {
                            "hs6": r.get("hs6", ""),
                            "national_code": national_code,
                            "description_fr": r.get("description", ""),
                            "description_en": r.get("description", ""),
                            "dd_rate": r.get("dd_rate", 0),
                            "zlecaf_rate": r.get("zlecaf_rate"),
                            "source": "postgres",
                        }
                    )
                    clean_code = re.sub(r"\D", "", str(national_code))
                    if clean_code:
                        seen_codes.add(clean_code)
                    if len(results) >= limit:
                        return results
            else:
                _log_etl_fallback("search_tariff_lines", country_iso3, reason="postgres-miss")
        except Exception as e:
            _log_etl_fallback("search_tariff_lines", country_iso3, reason=f"postgres-error: {e}")

    data = load_country_tariffs(country_iso3)
    etl_positions = {}
    etl_hs6_codes = set()
    if data:
        for line in data.get("tariff_lines", []):
            line_hs6 = _clean_crawled_hs_code(line)[:6]
            if line_hs6:
                etl_hs6_codes.add(line_hs6)
            for position in line.get("sub_positions", []):
                position_code = _clean_crawled_hs_code(position)
                if position_code:
                    etl_positions[position_code] = {
                        "dd_rate": position.get("dd"),
                        "vat_rate": line.get("vat_rate"),
                    }

    # ── 1. Crawled national/source positions (6-12 digits) ─────────────────
    crawled_index = load_crawled_position_index(country_iso3)
    if crawled_index:
        for code, sp in crawled_index.items():
            # This PR adds national positions only. Existing HS6 lines retain
            # the ETL search path's source, shape and priority unchanged.
            if len(code) == 6 and code in etl_hs6_codes:
                continue
            if code in seen_codes:
                continue
            name = (sp.get("name") or sp.get("description") or sp.get("designation") or "").lower()
            if code.startswith(q) or q in name:
                results.append(
                    _build_result_from_crawled_position(code, sp, etl_positions, country_iso3)
                )
                seen_codes.add(code)
                if len(results) >= limit:
                    return results

    # ── 2. ETL tariff_lines (HS6-level) ─────────────────────────────────────
    if len(results) < limit:
        if data:
            desc_key = "description_fr" if language == "fr" else "description_en"
            for line in data.get("tariff_lines", []):
                hs6 = line.get("hs6", "")
                desc = line.get(desc_key, line.get("description_fr", line.get("designation", "")))
                if hs6 in seen_codes or not (hs6.startswith(q) or q in desc.lower()):
                    continue
                # Un HS6 ETL est générique : le pays a souvent plusieurs codes
                # nationaux distincts sous ce préfixe, taxés différemment (ex.
                # riz à semer / riz de consommation en Égypte). Servir le HS6
                # nu forcerait un choix implicite entre positions différentes —
                # on résout donc vers le(s) code(s) national/nationaux, et on
                # n'expose le HS6 brut que si aucun code national n'existe.
                national_matches = (
                    [
                        (code, sp)
                        for code, sp in crawled_index.items()
                        if len(code) > 6 and code.startswith(hs6) and code not in seen_codes
                    ]
                    if crawled_index
                    else []
                )
                if national_matches:
                    for code, sp in national_matches:
                        results.append(
                            _build_result_from_crawled_position(
                                code, sp, etl_positions, country_iso3
                            )
                        )
                        seen_codes.add(code)
                        if len(results) >= limit:
                            return results
                else:
                    results.append(line)
                seen_codes.add(hs6)
                if len(results) >= limit:
                    return results

    # ── 3. Nomenclature map (extended national codes) ────────────────────────
    if len(results) < limit:
        nomenclature = load_nomenclature_map(country_iso3)
        if nomenclature:
            for code, description in nomenclature.items():
                if code not in seen_codes and (code.startswith(q) or q in description.lower()):
                    results.append(
                        {
                            "hs6": code[:6],
                            "national_code": code,
                            "description_fr": description,
                            "description_en": description,
                            "source": f"Nomenclature DGD {country_iso3}",
                        }
                    )
                    seen_codes.add(code)
                    if len(results) >= limit:
                        break

    return results


def get_country_summary(country_iso3):
    country_iso3 = _validate_iso3(country_iso3)
    provider = _get_postgres_provider()
    if provider:
        try:
            country = provider.get_country_info(country_iso3)
            if country:
                return {
                    "country_iso3": country_iso3,
                    "total_lines": int(country.get("total_positions", 0) or 0),
                    "total_sub_positions": int(country.get("total_positions", 0) or 0),
                    "total_national_positions": int(country.get("total_positions", 0) or 0),
                    "chapters_covered": country.get("chapters_covered", 0),
                    "vat_rate_pct": float(country.get("vat_rate", 0) or 0),
                    "dd_rate_range": {},
                    "generated_at": country.get("last_updated", ""),
                    "data_format": "postgres",
                }
            _log_etl_fallback("get_country_summary", country_iso3, reason="postgres-miss")
        except Exception as e:
            _log_etl_fallback("get_country_summary", country_iso3, reason=f"postgres-error: {e}")

    data = load_country_tariffs(country_iso3)
    if not data:
        return None
    summary = data.get("summary", {})
    tariff_lines = data.get("tariff_lines", [])
    nomenclature = load_nomenclature_map(country_iso3)
    return {
        "country_iso3": country_iso3,
        "total_lines": len(tariff_lines),
        "total_sub_positions": summary.get(
            "total_sub_positions",
            sum(len(line.get("sub_positions", [])) for line in tariff_lines),
        ),
        "total_national_positions": len(nomenclature) if nomenclature else 0,
        "chapters_covered": summary.get(
            "chapters_covered", len({line.get("chapter", "") for line in tariff_lines})
        ),
        "vat_rate_pct": summary.get("vat_rate_pct", 0),
        "dd_rate_range": summary.get("dd_rate_range", {}),
        "generated_at": data.get("generated_at", ""),
        "data_format": data.get("data_format", ""),
    }


def _resolve_zlecaf_context(
    dest_iso3, origin_iso3, hs_code_clean, dd_rate_pct, line_zlecaf_rate_pct
):
    """Détermine le régime commercial préférentiel applicable à la paire
    origine/destination et le taux DD effectif qui en découle.

    Préséance (du plus spécifique au plus général) :
      0. UNION DOUANIÈRE (SACU, EAC, CEMAC, UEMOA) : libre circulation, droit
         de douane intra-bloc 0 %. Définitionnelle (TEC + marché unique), donc
         PRIORITAIRE sur la ZLECAf et indépendante de la ratification ZLECAf.
      1. ZLECAf : ratification continentale (origine ET destination) + activation
         bilatérale (Algérie : partenaires actifs DGD 482/2024 ; Afrique du Sud :
         partenaires actifs hors SACU/SADC ; autres : instrument d'application,
         origine réciproque nommément acceptée et ligne officielle exacte).
      2. ZLE conditionnelle (CEDEAO/ECOWAS, SADC, COMESA) : signalée lorsqu'aucun
         régime ci-dessus ne s'applique mais que les deux pays partagent une zone
         de libre-échange — INFORMATIONNELLE, sans recalcul (règles d'origine).
      3. NPF par défaut.

    Source unique de vérité : réutilise exactement les mêmes modules que
    routes/calculator.py (zlecaf_membership_status, zlecaf_schedule_dza,
    zlecaf_schedule_zaf, zlecaf_implementation_registry) + regional_blocs.

    Retourne un dict :
      - preferential (bool)        : un régime réduit effectivement le droit de
                                     douane → déclenche la cascade préférentielle ;
      - preference_applied (bool)  : une préférence réduit les droits sur CE produit ;
      - dd_rate_pct (float)        : taux DD préférentiel effectif (en pourcentage) ;
      - daps_exempt (bool)         : DAPS exonéré (Algérie, listes A/B) ;
      - trade_regime (str)         : CUSTOMS_UNION | ZLECAF | FTA_CONDITIONAL | NPF ;
      - trade_regime_code (str|None): code du bloc (SACU, UEMOA, ECOWAS…) ou ZLECAF ;
      - trade_regime_note (str|None): explication du régime appliqué ;
      - zlecaf_eligible (bool)     : éligibilité STRICTE à la ZLECAf ;
      - zlecaf_note (str|None)     : note spécifique ZLECAf (rétro-compatibilité).
    """
    dest = (dest_iso3 or "").upper()
    origin = (origin_iso3 or "").strip().upper()

    def _result(
        *,
        preferential,
        preference_applied,
        dd,
        daps,
        regime,
        code,
        note,
        zlecaf_eligible,
        zlecaf_note,
        rate_expression=None,
        preferential_rate_source=None,
        preferential_rate_calculation_status=None,
        offer_rate_pct=None,
        offer_rate_expression=None,
        offer_rate_source=None,
    ):
        # ── Plancher NPF ──────────────────────────────────────────────────
        # Une préférence est une FACULTÉ, jamais une obligation : aucun
        # importateur n'invoque un régime plus cher que le droit commun, et
        # aucune douane ne le lui impose. Le règlement éthiopien 574/2025
        # l'écrit à son article 3(5) — « If the tariff under the Standard
        # Tariff Rules is lower than the tariff specified in the Free Trade
        # Area Tariff Schedule, goods originating from Member States may be
        # treated under the terms of the Standard Tariff Rules » — mais le
        # principe ne lui est pas propre.
        #
        # Les trois chemins préférentiels calculaient correctement
        # `preference_applied = taux < NPF`, puis servaient le taux
        # préférentiel QUAND MÊME. Le drapeau disait « pas d'avantage »
        # pendant que le montant facturait davantage. Mesuré avant
        # correction : 8 positions algériennes, 2 sud-africaines, 3
        # kényanes.
        #
        # Le garde-fou est posé ici, dans le constructeur que tous les
        # chemins traversent, plutôt que dans chacun d'eux : un chemin
        # ajouté demain en hérite sans qu'on ait à y penser.
        plancher_npf = None
        if dd is not None and dd_rate_pct is not None and dd > dd_rate_pct:
            plancher_npf = {
                "taux_preferentiel_ecarte_pct": dd,
                "taux_retenu_pct": dd_rate_pct,
                "motif": (
                    "Le taux préférentiel dépasse le droit NPF de la même "
                    "position : c'est le NPF qui est servi. Une préférence est "
                    "une faculté, pas une obligation."
                ),
            }
            dd = dd_rate_pct
            # Le drapeau n'est PAS touché : le plancher ne rabote que le droit
            # de douane, et une préférence ne se résume pas à lui. Sur les huit
            # positions algériennes concernées, `daps_exempt()` est vrai et la
            # cascade retire réellement un DAPS de 70 % — 70 000 DA d'économie
            # sur 100 000 de CIF. Éteindre le drapeau ici dirait « aucune
            # préférence » à un opérateur qui en tire une, et le dissuaderait
            # de présenter son certificat d'origine.
            #
            # Aucun chemin n'a besoin qu'on le corrige : les trois calculent le
            # drapeau avec un terme `taux préférentiel < NPF` qui est déjà faux
            # quand le plancher mord. Ce qui reste vrai — l'exonération du DAPS
            # — doit le rester.
            complement = (
                f" Taux préférentiel ({plancher_npf['taux_preferentiel_ecarte_pct']} %) "
                f"supérieur au NPF ({dd_rate_pct} %) : NPF servi."
            )
            note = (note or "") + complement
            zlecaf_note = (zlecaf_note or "") + complement

        return {
            "preferential": preferential,
            "preference_applied": preference_applied,
            "dd_rate_pct": dd,
            "plancher_npf": plancher_npf,
            "daps_exempt": daps,
            "trade_regime": regime,
            "trade_regime_code": code,
            "trade_regime_note": note,
            "zlecaf_eligible": zlecaf_eligible,
            "zlecaf_note": zlecaf_note,
            "zlecaf_rate_expression": rate_expression,
            "zlecaf_rate_source": preferential_rate_source,
            "zlecaf_rate_calculation_status": preferential_rate_calculation_status,
            # Taux publié sur le site officiel de la ZLECAf mais NON vérifié
            # comme applicable : strictement informatif. Jamais utilisé pour
            # calculer un droit, un total ou une économie — `dd_rate_pct`
            # reste le taux NPF. Affiché « à vérifier avec les douanes
            # locales » pour ne pas confondre une offre publiée avec une
            # absence pure de source.
            "zlecaf_offer_rate_pct": offer_rate_pct,
            "zlecaf_offer_rate_expression": offer_rate_expression,
            "zlecaf_offer_rate_source": offer_rate_source,
        }

    # Origine renseignée ? Toute préférence suppose un pays d'origine connu
    # (certificat d'origine). Validation ISO légère.
    if not re.fullmatch(r"[A-Z]{2,3}", origin):
        note = (
            "Origine non renseignée — aucun régime préférentiel applicable "
            "(certificat d'origine requis, taux NPF appliqué)"
        )
        return _result(
            preferential=False,
            preference_applied=False,
            dd=dd_rate_pct,
            daps=False,
            regime="NPF",
            code=None,
            note=note,
            zlecaf_eligible=False,
            zlecaf_note=note,
        )

    from services.regional_blocs import (
        CUSTOMS_UNION_NAMES,
        FTA_NAMES,
        same_customs_union,
        shared_free_trade_areas,
    )

    # 0. UNION DOUANIÈRE : libre circulation (0 %), prioritaire sur la ZLECAf.
    cu = same_customs_union(origin, dest)
    if cu:
        label = CUSTOMS_UNION_NAMES.get(cu, cu)
        note = (
            f"Échanges intra-{cu} : libre circulation sous le régime de "
            f"l'union douanière — {label}. Droit de douane 0 % (hors ZLECAf)."
        )
        return _result(
            preferential=True,
            preference_applied=(dd_rate_pct or 0) > 0,
            dd=0.0,
            daps=False,
            regime="CUSTOMS_UNION",
            code=cu,
            note=note,
            zlecaf_eligible=False,
            zlecaf_note=note,
        )

    from services.zlecaf_membership_status import (
        STATUS_NOT_SIGNED,
        STATUS_RATIFIED,
        ratification_status,
    )

    ftas = shared_free_trade_areas(origin, dest)

    def _no_preference(
        base_note,
        *,
        zlecaf_rate_status=None,
        offer_rate_pct=None,
        offer_rate_expression=None,
        offer_rate_source=None,
    ):
        """Aucun régime ZLECAf/union douanière : signaler une ZLE conditionnelle
        si les deux pays en partagent une, sinon NPF strict. Aucun recalcul.

        Un éventuel taux d'offre publié est transporté tel quel, à titre
        informatif : il ne touche jamais `dd`, qui reste le taux NPF."""
        if ftas:
            code = ftas[0]
            label = FTA_NAMES.get(code, code)
            fta_note = (
                f"Régime {code} potentiellement applicable — {label} : "
                f"franchise réservée aux produits originaires (règles "
                f"d'origine du bloc), non appliquée automatiquement ; "
                f"taux NPF affiché."
            )
            return _result(
                preferential=False,
                preference_applied=False,
                dd=dd_rate_pct,
                daps=False,
                regime="FTA_CONDITIONAL",
                code=code,
                note=fta_note,
                zlecaf_eligible=False,
                zlecaf_note=base_note,
                preferential_rate_calculation_status=zlecaf_rate_status,
                offer_rate_pct=offer_rate_pct,
                offer_rate_expression=offer_rate_expression,
                offer_rate_source=offer_rate_source,
            )
        return _result(
            preferential=False,
            preference_applied=False,
            dd=dd_rate_pct,
            daps=False,
            regime="NPF",
            code=None,
            note=base_note,
            zlecaf_eligible=False,
            zlecaf_note=base_note,
            preferential_rate_calculation_status=zlecaf_rate_status,
            offer_rate_pct=offer_rate_pct,
            offer_rate_expression=offer_rate_expression,
            offer_rate_source=offer_rate_source,
        )

    # 1. Ratification continentale ZLECAf (origine ET destination).
    o_status = ratification_status(origin)
    d_status = ratification_status(dest)
    if o_status != STATUS_RATIFIED or d_status != STATUS_RATIFIED:
        nonrat, st = (origin, o_status) if o_status != STATUS_RATIFIED else (dest, d_status)
        reason = "non signataire" if st == STATUS_NOT_SIGNED else "signataire, non encore ratifié"
        return _no_preference(f"ZLECAf non applicable : {nonrat} ({reason}) — taux NPF appliqué")

    # 2. Algérie : partenaires actifs (DGD 482/2024) + calendrier de démantèlement.
    if dest == "DZA":
        from services.zlecaf_schedule_dza import (
            ACTIVE_PARTNERS,
            compute_dza_zlecaf_rate,
            daps_exempt,
        )

        if origin not in ACTIVE_PARTNERS:
            return _no_preference(
                f"ZLECAf non encore activé pour {origin} à l'import en Algérie "
                f"(circulaire DGD 482/2024) — taux NPF appliqué"
            )
        # Pourcentages de bout en bout : le taux publié se transporte tel quel,
        # sans aller-retour vers une fraction. La conversion qui figurait ici
        # n'altérait aucun résultat, mais elle obligeait à convertir deux fois
        # et faisait d'un oubli une erreur d'un facteur 100.
        _r, _src = compute_dza_zlecaf_rate(hs_code_clean, origin, dd_rate_pct or 0)
        eff_dd = round(_r, 6) if _r is not None else dd_rate_pct
        _daps = daps_exempt(hs_code_clean, origin)
        applied = (eff_dd is not None and eff_dd < (dd_rate_pct or 0)) or _daps
        return _result(
            preferential=True,
            preference_applied=applied,
            dd=eff_dd,
            daps=_daps,
            regime="ZLECAF",
            code="ZLECAF",
            note=_src,
            zlecaf_eligible=True,
            zlecaf_note=_src,
        )

    # 2 bis. Égypte : circulaires n° 38 de 2024 et n° 44 de 2025 — liste A
    #    seulement, chapitres 50 à 63 et 87 reportés. L'e-Tariff Book contredit
    #    l'acte national : le taux est calculé depuis le NPF par le calendrier
    #    national, jamais servi depuis l'offre.
    if dest == "EGY":
        from services.zlecaf_schedule_egy import (
            compute_egy_zlecaf_rate,
            origine_admise,
        )

        if not origine_admise(origin):
            return _no_preference(
                f"ZLECAf non notifié par l'Égypte pour {origin} (circulaires "
                "n° 38 de 2024 et n° 44 de 2025) — taux NPF appliqué"
            )
        _r, _src = compute_egy_zlecaf_rate(hs_code_clean, origin, dd_rate_pct or 0)
        eff_dd = round(_r, 6) if _r is not None else dd_rate_pct
        applied = eff_dd is not None and eff_dd < (dd_rate_pct or 0)
        return _result(
            preferential=True,
            preference_applied=applied,
            dd=eff_dd,
            daps=False,
            regime="ZLECAF",
            code="ZLECAF",
            note=_src,
            zlecaf_eligible=True,
            zlecaf_note=_src,
        )

    # 3. Afrique du Sud : activation bilatérale (hors SACU/SADC, traités en 0)
    #    + colonne AfCFTA officielle de SARS Schedule 1 Part 1. Les droits
    #    spécifiques/composés sont documentés mais restent non calculables sans
    #    quantité : ils ne sont jamais aplatis en leur seule composante ad valorem.
    if dest == "ZAF":
        from services.official_preferential_rates import resolve_official_preferential_rate
        from services.zlecaf_schedule_zaf import zaf_partner_active

        if not zaf_partner_active(origin):
            return _no_preference(
                "ZLECAf ratifié mais échanges préférentiels pas encore activés "
                "avec l'Afrique du Sud (newsletter AfCFTA dtic/SARS, mars 2026) "
                "— taux NPF appliqué"
            )
        official_rate = resolve_official_preferential_rate(dest, hs_code_clean)
        eff_dd = official_rate.get("ad_valorem_rate_pct") if official_rate else None
        applied = eff_dd is not None and eff_dd < (dd_rate_pct or 0)
        source = None
        expression = None
        calculation_status = None
        note = None
        if official_rate:
            expression = official_rate["rate_expression"]
            calculation_status = official_rate["calculation_status"]
            source = {
                "title": official_rate["source_title"],
                "url": official_rate["source_url"],
                "pdf_url": official_rate["source_pdf_url"],
                "source_date": official_rate["source_date"],
                "pdf_sha256": official_rate["source_pdf_sha256"],
                "page": official_rate["page"],
                "column": official_rate["source_column"],
            }
            note = (
                f"SARS Schedule 1 Part 1, colonne AfCFTA, p. {official_rate['page']} "
                f"— taux officiel : {expression}."
            )
            if calculation_status != "CALCULABLE":
                note += " Quantité requise pour calculer ce droit spécifique/composé."
        return _result(
            preferential=True,
            preference_applied=applied,
            dd=eff_dd,
            daps=False,
            regime="ZLECAF",
            code="ZLECAF",
            note=note,
            zlecaf_eligible=True,
            zlecaf_note=note,
            rate_expression=expression,
            preferential_rate_source=source,
            preferential_rate_calculation_status=calculation_status,
        )

    # 4. Autres pays : une offre, une ratification ou la participation au GTI
    #    ne déclenchent jamais un calcul. Il faut une transposition en vigueur,
    #    une origine explicitement acceptée sur base réciproque et une ligne
    #    tarifaire officielle exacte.
    from services.official_preferential_rates import resolve_official_preferential_rate
    from services.zlecaf_implementation_registry import (
        OFFER_ONLY,
        PARTNER_NOTICE_REQUIRED,
        implementation_decision,
    )

    decision = implementation_decision(dest, origin)
    if not decision["applied"]:
        # OFFER_ONLY/PARTNER_NOTICE_REQUIRED restent distincts de NOT_AVAILABLE :
        # une offre publiée sur le site officiel de la ZLECAf n'est pas une
        # absence de source, mais un taux non vérifié comme applicable. On
        # remonte alors le taux publié à titre STRICTEMENT informatif, pour
        # l'afficher « à vérifier avec les douanes locales ». Il ne touche
        # jamais le droit exigible : `_no_preference` conserve le taux NPF.
        offer_pct = offer_expression = offer_source = None
        if decision["status"] in (OFFER_ONLY, PARTNER_NOTICE_REQUIRED):
            from services.official_preferential_rates import resolve_published_offer_rate

            published = resolve_published_offer_rate(dest, hs_code_clean, origin)
            if published:
                offer_pct = published.get("ad_valorem_rate_pct")
                offer_expression = published.get("rate_expression")
                offer_source = {
                    "title": published.get("source_title"),
                    "url": published.get("source_url"),
                    "api_url": published.get("source_api_url"),
                    "source_date": published.get("source_date"),
                    "column": published.get("source_column"),
                    "schedule": published.get("schedule"),
                    "schedule_year": published.get("schedule_year"),
                }
        return _no_preference(
            decision["note"],
            zlecaf_rate_status=decision["status"],
            offer_rate_pct=offer_pct,
            offer_rate_expression=offer_expression,
            offer_rate_source=offer_source,
        )

    official_rate = resolve_official_preferential_rate(dest, hs_code_clean, origin)
    if not official_rate or official_rate.get("ad_valorem_rate_pct") is None:
        return _result(
            preferential=True,
            preference_applied=False,
            dd=None,
            daps=False,
            regime="ZLECAF",
            code="ZLECAF",
            note=(
                f"{decision['note']} Aucune ligne préférentielle exacte et "
                "calculable n'a été vérifiée pour ce code."
            ),
            zlecaf_eligible=True,
            zlecaf_note=decision["note"],
            preferential_rate_calculation_status="NOT_AVAILABLE",
        )

    eff_dd = official_rate["ad_valorem_rate_pct"]
    applied = eff_dd < (dd_rate_pct or 0)
    record = decision["record"]
    source = {
        "title": official_rate["source_title"],
        "url": official_rate["source_url"],
        "api_url": official_rate.get("source_api_url"),
        "source_date": official_rate["source_date"],
        "column": official_rate["source_column"],
        "schedule": official_rate.get("schedule"),
        "implementation_instrument": record.instrument_id,
        "implementation_title": record.instrument_title,
        "implementation_url": record.instrument_url,
        "effective_from": record.effective_from,
    }
    note = (
        f"{record.instrument_id}, origine {origin}; ligne "
        f"{official_rate['hs_code']}, {official_rate['source_column']} : "
        f"{official_rate['rate_expression']}. Certificat d'origine ZLECAf requis."
    )
    contexte = _result(
        preferential=True,
        preference_applied=applied,
        dd=eff_dd,
        daps=False,
        regime="ZLECAF",
        code="ZLECAF",
        note=note,
        zlecaf_eligible=True,
        zlecaf_note=note,
        rate_expression=official_rate["rate_expression"],
        preferential_rate_source=source,
        preferential_rate_calculation_status=official_rate["calculation_status"],
    )
    if dest == "KEN" and applied:
        # Même réserve que le moteur du socle : rubrique sans règle d'origine
        # arrêtée à l'Appendice IV (décembre 2023), que le Kenya n'exclut pas.
        from services.zlecaf_schedule_ken import reserve_regle_d_origine

        contexte["zlecaf_reserve"] = reserve_regle_d_origine(hs_code_clean)
    return contexte


# Alias public : le moteur de rapports (benchmarking_service) doit appliquer
# EXACTEMENT le même régime préférentiel que le calculateur (activation
# bilatérale Algérie/Afrique du Sud, unions douanières, ratification) — jamais
# le taux ZLECAf générique de la ligne sans tenir compte de l'origine.
resolve_zlecaf_context = _resolve_zlecaf_context


_country_has_vat_cache: Dict[str, bool] = {}


def _tva_presente_dans_le_tarif(country_iso3: str, country_data) -> bool:
    """Vrai si le fichier du pays publie au moins une TVA (famille présente).

    Sépare un tarif qui collecte la TVA position par position (une position
    sans TVA est alors une exonération, ex. Algérie) d'un tarif qui n'en porte
    aucune (Somalie, SARS : la TVA/sales tax n'est pas dans ce fichier). Le
    verdict est constant pour un même chargement : il est mis en cache.
    """
    if country_iso3 in _country_has_vat_cache:
        return _country_has_vat_cache[country_iso3]
    presente = False
    if isinstance(country_data, dict):
        for line in country_data.get("tariff_lines", []) or []:
            if not isinstance(line, dict):
                continue
            if line.get("vat_rate") is not None or line.get("vat_rate_variants"):
                presente = True
                break
            for tax in line.get("taxes_detail", []) or []:
                if isinstance(tax, dict) and _is_vat_code(tax.get("tax") or ""):
                    presente = True
                    break
            if presente:
                break
            for sp in line.get("sub_positions", []) or []:
                if isinstance(sp, dict) and sp.get("vat_rate") is not None:
                    presente = True
                    break
            if presente:
                break
    _country_has_vat_cache[country_iso3] = presente
    return presente


# Pays dont une source établit que la position sans TVA est EXONÉRÉE, et non
# incomplète. Algérie : Code des taxes sur le chiffre d'affaires, art. 8/9/10/11
# (viandes, lait, médicaments, farines et semoules, or, navires) et art. 214
# LF2025 reconduit LF2026 (café vert). Toute autre entrée exige la même
# démonstration : sans elle, l'absence reste une absence.
EXONERATION_TVA_ETABLIE = {"DZA"}


def _sens_de_la_tva_absente(country_iso3: str, country_data) -> str:
    """Qualifie une TVA manquante : EXONEREE, HORS_TARIF ou INCONNUE.

    INCONNUE est le défaut : le taux reste nul et le calcul se déclare
    indisponible plutôt que de servir un zéro fabriqué.
    """
    if country_iso3 in EXONERATION_TVA_ETABLIE:
        return "EXONEREE"
    if not _tva_presente_dans_le_tarif(country_iso3, country_data):
        return "HORS_TARIF"
    return "INCONNUE"


def calculate_import_taxes(
    country_iso3,
    hs_code,
    cif_value,
    apply_zlecaf=False,
    language="fr",
    origin_country=None,
    fob_value=None,
):
    """Calculate import taxes for a country/HS code/CIF value combination.

    Supports both HS6 codes and extended national sub-position codes (8-12
    digits).  For Algeria (DZA) and any country that has a nomenclature map,
    sub-position-level descriptions are returned even for codes that only
    appear in the nomenclature file.

    Returns a dict compatible with the frontend CalculatorTab component.
    """
    from services.national_position_selection import (
        NationalPositionRequired,
        normalize_calculation_code,
        select_calculation_position,
    )

    try:
        hs_code_clean = _position_sans_cle(country_iso3, normalize_calculation_code(hs_code))
        selected = select_calculation_position(
            hs_code_clean, get_sub_positions(country_iso3, hs_code_clean[:6])
        )
        if selected:
            retenu = (
                selected.get("code_raw") or selected.get("code") or selected.get("national_code")
            )
            # Le moteur historique retrouve sa ligne dans le CRAWL, qui indexe
            # le code avec sa clé de contrôle. La sélection, elle, se fait sur
            # la position. On recolle donc la clé ici — sans quoi la recherche
            # échoue et le calcul se rabat sur le parent SH6 : sur 9003110000,
            # le droit passait ainsi de 10 % à 43 % sans que rien ne le
            # signale.
            if selected.get("cle_controle"):
                retenu = f"{retenu}{selected['cle_controle']}"
            hs_code_clean = normalize_calculation_code(retenu)
    except NationalPositionRequired as exc:
        return {"error": str(exc), "error_detail": exc.detail}
    hs6 = hs_code_clean[:6]

    country_data = load_country_tariffs(country_iso3)
    line = get_tariff_line(country_iso3, hs_code_clean)
    if not line:
        return {"error": f"Tariff line not found for {country_iso3}/{hs6}"}
    is_postgres_line = line.get("data_source") == "postgres" or line.get("source") == "postgres"

    if is_postgres_line:
        from math import isfinite

        rates = [line.get("dd_rate"), line.get("vat_rate")]
        rates.extend(t.get("rate") for t in line.get("taxes_detail", []))
        if any(
            not isinstance(rate, (int, float)) or not isfinite(rate) or rate < 0 for rate in rates
        ):
            detail = {
                "code": "CALCULATION_UNAVAILABLE",
                "message": "Mesures PostgreSQL incomplètes pour cette position nationale.",
                "hs_code": hs_code_clean,
            }
            return {"error": detail["message"], "error_detail": detail}

    # Keep missing values unresolved until all source-specific measures have
    # been selected. A published zero is distinct from a missing rate.
    dd_rate_pct = line.get("dd_rate")
    sub_position_info = None

    # --- Priority 1: crawled authentic JSON (per-position taxes) ---
    # Select the exact collected position; all tax schemas are reconciled below.
    crawled_sp_entry = None
    etl_sub_position_entry = None
    if not is_postgres_line:
        crawled_index = load_crawled_position_index(country_iso3)
        if crawled_index and hs_code_clean in crawled_index:
            crawled_sp_entry = crawled_index[hs_code_clean]

    if len(hs_code_clean) > 6:
        etl_sub_position_entry = next(
            (sp for sp in line.get("sub_positions", []) if sp.get("code") == hs_code_clean),
            None,
        )

    if len(hs_code_clean) > 6:
        if crawled_sp_entry:
            crawled_taxes = crawled_sp_entry.get("taxes", {})
            crawled_dd = crawled_taxes.get("DD") if isinstance(crawled_taxes, dict) else None
            if isinstance(crawled_dd, dict):
                parsed_dd = _parse_crawled_tax_rate(crawled_dd)
                if parsed_dd is not None:
                    dd_rate_pct = parsed_dd
            elif etl_sub_position_entry and not is_postgres_line:
                dd_rate_pct = etl_sub_position_entry.get("dd", dd_rate_pct)
        else:
            if etl_sub_position_entry and not is_postgres_line:
                dd_rate_pct = etl_sub_position_entry.get("dd", dd_rate_pct)

        # Resolve description: crawled name > nomenclature_map > sub_positions
        sp_desc = ""
        if crawled_sp_entry:
            sp_desc = crawled_sp_entry.get("name", "") or crawled_sp_entry.get("description", "")
        if not sp_desc:
            nomenclature = load_nomenclature_map(country_iso3)
            if nomenclature:
                sp_desc = nomenclature.get(hs_code_clean, "")
        if not sp_desc:
            if etl_sub_position_entry:
                sp_desc = etl_sub_position_entry.get(
                    "description_fr", etl_sub_position_entry.get("description_en", "")
                )

        sub_position_info = {
            "code": hs_code_clean,
            "description": sp_desc,
            "description_fr": sp_desc,
            "description_en": sp_desc,
        }

    # Missing VAT remains None; never turn it into a documented exemption.
    vat_rate_pct = line.get("vat_rate")
    other_taxes_pct = line.get("other_taxes_rate", 0) or 0
    # PAS de `or 0` ici : `zlecaf_rate` absent (aucune préférence tracée sur
    # cette ligne) doit rester `None`, pas devenir un taux préférentiel 0 %
    # fabriqué. `_resolve_zlecaf_context` gère déjà `None` explicitement
    # (`eff_dd is not None and eff_dd < dd_rate_pct`) — aucune régression sur
    # ce chemin, seulement la suppression du repli silencieux vers 0.
    zlecaf_rate_pct = line.get("zlecaf_rate")

    # Extract DAPS and other individual taxes:
    # If crawled entry has per-position taxes, use them as primary source;
    # otherwise fall back to taxes_detail from the ETL line.
    _raw_crawled_taxes = _position_tax_payload(crawled_sp_entry) if crawled_sp_entry else None
    _has_legacy_crawled_tax_details = isinstance(_raw_crawled_taxes, (dict, list))
    if not is_postgres_line and _has_legacy_crawled_tax_details:
        # Every collected schema is authoritative, including an empty payload.
        # Missing DD cannot be recovered from an obsolete HS6 parent.
        taxes_detail = _normalise_crawled_tax_details(_raw_crawled_taxes)
        dd_rate_pct = taxes_detail.get("DD", {}).get("rate")
        if "TVA" in taxes_detail:
            vat_rate_pct = taxes_detail["TVA"]["rate"]
        other_taxes_pct = sum(
            t["rate"]
            for code, t in taxes_detail.items()
            if code not in ("DD", "TVA") and t["rate"] is not None
        )
    else:
        if crawled_sp_entry and "dd" in crawled_sp_entry and not is_postgres_line:
            dd_rate_pct = _parse_crawled_tax_rate(crawled_sp_entry["dd"])
        taxes_detail = _normalise_crawled_tax_details(line.get("taxes_detail", {}))
        # An aggregate field may be absent while the same line explicitly
        # supplies the measure. Do not use a parent to fill an unknown child.
        if not crawled_sp_entry and not etl_sub_position_entry:
            if dd_rate_pct is None:
                dd_rate_pct = taxes_detail.get("DD", {}).get("rate")
            if vat_rate_pct is None:
                vat_rate_pct = taxes_detail.get("TVA", {}).get("rate")
        # The child's explicit DD wins over the aggregate repeated in details.
        if "DD" in taxes_detail:
            taxes_detail["DD"] = {**taxes_detail["DD"], "rate": dd_rate_pct}

    # TVA absente de la position : deux sens légitimes, jamais un zéro fabriqué
    # ni un blocage injustifié du calcul.
    #   (a) famille TVA entièrement absente du tarif (Somalie, SARS…) : la TVA
    #       n'est pas collectée par ce fichier. On sert les droits collectés et
    #       on signale la TVA absente (`tva_absente`) ; le total reste PARTIEL,
    #       il ne prétend pas inclure une taxe que la source n'a pas.
    #   (b) position publiée sans TVA (Algérie) : exonérée à 0 % par le Code des
    #       taxes sur le chiffre d'affaires (art. 8/9/10/11 — viandes, lait,
    #       médicaments, farines et semoules, or, navires ; café vert art. 214
    #       LF2025 reconduit LF2026), signalée `tva_exoneree`.
    # Une position sans droit de douane ET sans TVA (ex. DZA 1001110000) reste
    # réellement incomplète et garde le garde CALCULATION_UNAVAILABLE.
    tva_exoneree = False
    tva_absente = False
    sens = _sens_de_la_tva_absente(country_iso3, country_data)
    if vat_rate_pct is None and dd_rate_pct is not None:
        if sens == "EXONEREE":
            vat_rate_pct = 0.0
            tva_exoneree = True
        elif sens == "HORS_TARIF":
            vat_rate_pct = 0.0
            tva_absente = True
    # Le même arbitrage vaut pour une entrée TVA du détail laissée sans taux :
    # elle ne devient 0 % que lorsqu'une source établit l'exonération. Sinon
    # elle reste nulle et tombe dans `missing` → CALCULATION_UNAVAILABLE (#472).
    if sens == "EXONEREE":
        for code in list(taxes_detail.keys()):
            entree = taxes_detail[code]
            if _is_vat_code(code) and isinstance(entree, dict) and entree.get("rate") is None:
                taxes_detail[code] = {**entree, "rate": 0.0}
                tva_exoneree = True

    missing = [
        code
        for code, rate in (("DD", dd_rate_pct), ("TVA", vat_rate_pct))
        if _parse_crawled_tax_rate(rate) is None
    ]
    missing.extend(code for code, tax in taxes_detail.items() if tax["rate"] is None)
    if missing:
        detail = {
            "code": "CALCULATION_UNAVAILABLE",
            "message": "Taux absents ou droits spécifiques : calcul complet indisponible.",
            "hs_code": hs_code_clean,
            "missing_or_non_ad_valorem_taxes": sorted(set(missing)),
        }
        return {"error": detail["message"], "error_detail": detail}
    dd_rate_pct = float(dd_rate_pct)
    vat_rate_pct = float(vat_rate_pct)

    daps_rate_pct = 0.0
    prct_rate_pct = 0.0
    tcs_rate_pct = 0.0
    individual_taxes = []
    for tax_code, tax_info in taxes_detail.items():
        if not isinstance(tax_info, dict):
            continue
        label = tax_info.get(
            "label", tax_info.get("name", _TAX_LABELS.get(_normalize_tax_code(tax_code), tax_code))
        )
        norm = _canonical_tax_code(tax_code, label)
        rate = float(tax_info.get("rate", 0) or 0)
        if rate == 0:
            continue
        # PRCT/TCS : intitulés officiels fixes — on ignore les libellés
        # hérités des données crawled (ex. « Prélèvement à la Compensation
        # du Transport », « Taxe de Contrôle Sanitaire »), erronés. Réécrit
        # aussi dans tax_info (même dict que taxes_detail, copié plus haut)
        # pour que taxes_detail exposé en sortie soit corrigé de la même
        # façon que individual_taxes, pas seulement l'un des deux.
        if norm in ("PRCT", "TCS"):
            label = _TAX_LABELS[norm]
            tax_info["label"] = label
        individual_taxes.append({"code": norm, "label": label, "rate_pct": rate})
        if norm == "DAPS":
            daps_rate_pct = rate
        elif norm == "PRCT":
            prct_rate_pct = rate
        elif norm == "TCS":
            tcs_rate_pct = rate
        # Capture VAT from taxes_detail when not already set from crawled source
        elif _is_vat_code(norm) and vat_rate_pct == 0:
            vat_rate_pct = rate

    # Normaliser l'intitulé officiel du PRCT dans le dict taxes_detail renvoyé
    # (entrée recréée, jamais de mutation des objets de ligne mis en cache).
    for _k in list(taxes_detail.keys()):
        if _canonical_tax_code(
            _k,
            (
                taxes_detail.get(_k, {}).get("label", "")
                if isinstance(taxes_detail.get(_k), dict)
                else ""
            ),
        ) == "PRCT" and isinstance(taxes_detail.get(_k), dict):
            _entry = dict(taxes_detail[_k])
            for _lk in ("label", "name"):
                if _lk in _entry:
                    _entry[_lk] = _TAX_LABELS["PRCT"]
            taxes_detail[_k] = _entry

    # ── Resolve PRCT / TCS when not explicitly in taxes_detail ───────────────
    # Only add PRCT fallback if other_taxes_pct is not already covered by an
    # explicit individual tax (e.g. TPI for MAR already covers the 0.25%).
    # A selected national row has its own tax details. Its parent's aggregate
    # may describe different taxes and cannot manufacture a missing PRCT.
    _covered_other = sum(
        t["rate_pct"]
        for t in individual_taxes
        if t["code"] not in ("DD", "DAPS") and not _is_vat_code(t["code"])
    )
    if (
        prct_rate_pct == 0
        and not (crawled_sp_entry and _has_legacy_crawled_tax_details)
        and other_taxes_pct > 0
        and round(_covered_other, 4) < round(other_taxes_pct, 4)
    ):
        prct_rate_pct = other_taxes_pct
        if not any(t["code"] == "PRCT" for t in individual_taxes):
            individual_taxes.insert(
                0, {"code": "PRCT", "label": _TAX_LABELS["PRCT"], "rate_pct": other_taxes_pct}
            )

    # ── Build rates dict for cascade engine ──────────────────────────────────
    # Normalised code → rate_pct  (only non-zero taxes)
    taxes_for_cascade: dict = {}
    if daps_rate_pct > 0:
        taxes_for_cascade["DAPS"] = daps_rate_pct
    if dd_rate_pct > 0:
        taxes_for_cascade["DD"] = dd_rate_pct
    if prct_rate_pct > 0:
        taxes_for_cascade["PRCT"] = prct_rate_pct
    if tcs_rate_pct > 0:
        taxes_for_cascade["TCS"] = tcs_rate_pct
    if vat_rate_pct > 0:
        taxes_for_cascade["TVA"] = vat_rate_pct
    # Add any other taxes from individual_taxes not yet covered. Les codes TVA
    # équivalents (IVA/VAT/TVA-APTAXE) sont exclus : déjà représentés par
    # taxes_for_cascade["TVA"] via vat_rate_pct — les rajouter ici les
    # compterait deux fois (une fois comme "TVA", une fois sous leur propre
    # code).
    for t in individual_taxes:
        c = _canonical_tax_code(t["code"], t.get("label", ""))
        if c not in taxes_for_cascade and t.get("rate_pct", 0) > 0 and not _is_vat_code(c):
            taxes_for_cascade[c] = t["rate_pct"]

    # ── NPF cascade (régime normal / Most-Favoured-Nation) ───────────────────
    try:
        npf_cascade = compute_tax_cascade(
            cif_value, taxes_for_cascade, country_iso3, fob_value=fob_value
        )
    except ValueError as exc:
        # Fail-closed : une assiette exigée par le pays (FOB en SACU, p. ex.)
        # absente de la demande est une erreur du client, pas une panne —
        # la substituer par CIF produirait un montant crédible et faux.
        return {"error": str(exc), "error_detail": str(exc)}

    # ── ZLECAf : éligibilité bilatérale + taux préférentiel selon l'origine ──
    # L'avantage ZLECAf n'est accordé que si la paire origine/destination y est
    # éligible : ratification continentale (origine ET destination) + réciprocité
    # bilatérale (Algérie : 9 partenaires actifs ; Afrique du Sud : 14 partenaires
    # actifs, SACU exclue). Source unique de vérité : _resolve_zlecaf_context, qui
    # réutilise les mêmes modules que routes/calculator.py.
    # Le DAPS est un droit de douane, exonéré de façon BINAIRE pour les listes (A)
    # et (B) algériennes (circulaire 482/2024), indépendamment du facteur de
    # démantèlement du DD.
    _zctx = _resolve_zlecaf_context(
        country_iso3, origin_country, hs_code_clean, dd_rate_pct, zlecaf_rate_pct
    )
    _preferential = _zctx["preferential"]
    trade_regime = _zctx["trade_regime"]
    trade_regime_code = _zctx["trade_regime_code"]
    trade_regime_note = _zctx["trade_regime_note"]
    preferential_regime_applied = _zctx["preference_applied"]
    zlecaf_eligible = _zctx["zlecaf_eligible"]
    zlecaf_preference_applied = _zctx["preference_applied"] and trade_regime == "ZLECAF"
    zlecaf_note = _zctx["zlecaf_note"]
    zlecaf_rate_expression = _zctx["zlecaf_rate_expression"]
    zlecaf_rate_source = _zctx["zlecaf_rate_source"]
    zlecaf_rate_calculation_status = _zctx["zlecaf_rate_calculation_status"]
    # Offre publiée sur le site officiel de la ZLECAf, non vérifiée comme
    # applicable : informatif seulement, jamais injecté dans la cascade.
    zlecaf_offer_rate_pct = _zctx["zlecaf_offer_rate_pct"]
    zlecaf_offer_rate_expression = _zctx["zlecaf_offer_rate_expression"]
    zlecaf_offer_rate_source = _zctx["zlecaf_offer_rate_source"]

    zlecaf_taxes = dict(taxes_for_cascade)
    _eff_dd = None
    if _preferential:
        _eff_dd = _zctx["dd_rate_pct"]
        # DD : remplacé par le taux préférentiel ZLECAf (uniquement s'il réduit).
        if _eff_dd is not None and _eff_dd < dd_rate_pct:
            if _eff_dd == 0:
                zlecaf_taxes.pop("DD", None)
            else:
                zlecaf_taxes["DD"] = _eff_dd
        # DAPS (droit de douane) : exonération binaire selon les listes (A)/(B).
        if "DAPS" in zlecaf_taxes and daps_rate_pct > 0 and _zctx["daps_exempt"]:
            zlecaf_taxes.pop("DAPS", None)
    # Non éligible : zlecaf_taxes == NPF → aucune préférence, économies = 0.
    zlecaf_cascade = compute_tax_cascade(cif_value, zlecaf_taxes, country_iso3, fob_value=fob_value)

    # Traçabilité : un régime ZLECAf peut être éligible (`_preferential`) sans
    # qu'un taux préférentiel réel soit connu pour CETTE ligne (ex. Afrique du
    # Sud / autres implémenteurs actifs : `_eff_dd` vient directement de
    # `zlecaf_rate_pct`, absent de la source → None). Dans ce cas précis,
    # l'absence de donnée ne doit jamais s'afficher comme une économie de 0 %
    # (zéro vérifié) : elle est INCONNUE. Les autres régimes (union douanière,
    # calendrier DZA, NPF strict) retournent toujours un `dd_rate_pct`
    # numérique concret, jamais None — `zlecaf_status` reste `DOCUMENTED`.
    # OFFER_ONLY/PARTNER_NOTICE_REQUIRED : une offre publiée existe mais n'est
    # pas vérifiée comme applicable — aussi non traçable que NOT_AVAILABLE
    # pour le calcul (aucune économie affichée), mais un statut distinct pour
    # que le frontend l'affiche comme « à vérifier auprès des douanes
    # locales » plutôt que comme une absence pure et simple de source.
    zlecaf_rate_untraceable = zlecaf_rate_calculation_status in (
        "NOT_AVAILABLE",
        "OFFER_ONLY",
        "PARTNER_NOTICE_REQUIRED",
    ) or (_preferential and trade_regime == "ZLECAF" and _eff_dd is None)
    zlecaf_status = (
        zlecaf_rate_calculation_status
        if zlecaf_rate_calculation_status in ("OFFER_ONLY", "PARTNER_NOTICE_REQUIRED")
        else ("NOT_AVAILABLE" if zlecaf_rate_untraceable else "DOCUMENTED")
    )

    if zlecaf_rate_untraceable:
        savings_amount = None
        savings_pct = None
    else:
        savings_amount = round(npf_cascade["total_to_pay"] - zlecaf_cascade["total_to_pay"], 2)
        savings_pct = (
            round(savings_amount / npf_cascade["total_to_pay"] * 100, 2)
            if npf_cascade["total_to_pay"] > 0
            else 0
        )

    all_sub_positions = get_sub_positions(country_iso3, hs6)
    desc_key = "description_fr" if language == "fr" else "description_en"
    description = line.get(desc_key, line.get("description_fr", ""))

    # ── Build backward-compatible npf_calculation / zlecaf_calculation dicts ─
    def _steps_to_legacy(steps, cif):
        """Convert cascade steps to legacy {daps/dd/vat/other_taxes} dict."""
        out = {"total_to_pay": round(cif + sum(s["amount"] for s in steps), 2)}
        for s in steps:
            c = s["code"]
            entry = {"base": s["base_value"], "rate_pct": s["rate_pct"], "amount": s["amount"]}
            if c == "DD":
                out["dd"] = entry
            elif c == "DAPS":
                out["daps"] = entry
            elif c in ("TVA", "T.V.A"):
                out["vat"] = entry
            else:
                # Accumulate other taxes
                ot = out.get("other_taxes", {"base": cif, "rate_pct": 0, "amount": 0})
                ot["amount"] = round(ot["amount"] + s["amount"], 2)
                ot["rate_pct"] = round(ot["rate_pct"] + s["rate_pct"], 4)
                out["other_taxes"] = ot
        return out

    npf_legacy = _steps_to_legacy(npf_cascade["steps"], cif_value)
    zlecaf_legacy = _steps_to_legacy(zlecaf_cascade["steps"], cif_value)

    # ── Ventilation NPF vs ZLECAf, taxe par taxe (pour TaxBreakdownDual) ──────
    # Construite DIRECTEMENT à partir des étapes cascade déjà calculées afin de
    # garantir la cohérence parfaite avec le journal de calcul affiché.
    def _breakdown_category(code: str) -> str:
        # DAPS (Droit Additionnel Provisoire de Sauvegarde) est traité comme un
        # droit de douane (réduit sous ZLECAf au même titre que le DD).
        if code in ("DD", "DAPS"):
            return "droit_douane"
        if code in ("TVA", "TVAI", "T.V.A", "VAT"):
            return "tva"
        return "autre_taxe"

    _npf_by_code = {s["code"]: s for s in npf_cascade["steps"]}
    _zlc_by_code = {s["code"]: s for s in zlecaf_cascade["steps"]}
    _all_codes = list(
        dict.fromkeys(
            [s["code"] for s in npf_cascade["steps"]] + [s["code"] for s in zlecaf_cascade["steps"]]
        )
    )

    taxes_breakdown: list = []
    _tot = {
        "npf": {"droit_douane": 0.0, "tva": 0.0, "autre_taxe": 0.0},
        "zlecaf": {"droit_douane": 0.0, "tva": 0.0, "autre_taxe": 0.0},
    }
    for code in _all_codes:
        npf_s = _npf_by_code.get(code)
        zlc_s = _zlc_by_code.get(code)
        ref = npf_s or zlc_s
        cat = _breakdown_category(code)
        amount_npf = npf_s["amount"] if npf_s else 0.0
        amount_zlecaf = zlc_s["amount"] if zlc_s else 0.0
        rate_npf = npf_s["rate_pct"] if npf_s else 0.0
        rate_zlecaf = zlc_s["rate_pct"] if zlc_s else 0.0
        taxes_breakdown.append(
            {
                "code": code,
                "name": ref.get("label", code),
                "category": cat,
                "base_expr": ref.get("base_formula", "CIF"),
                "rate_npf_pct": round(rate_npf, 4),
                "rate_zlecaf_pct": round(rate_zlecaf, 4),
                "base_value_npf": (
                    npf_s["base_value"] if npf_s else (zlc_s["base_value"] if zlc_s else cif_value)
                ),
                "base_value_zlecaf": (
                    zlc_s["base_value"] if zlc_s else (npf_s["base_value"] if npf_s else cif_value)
                ),
                "amount_npf": amount_npf,
                "amount_zlecaf": amount_zlecaf,
                # Une taxe est « affectée » par la ZLECAf si son montant change
                # (DD préférentiel, ou TVA recalculée sur une base sans DD).
                "affected_by_zlecaf": round(amount_npf, 2) != round(amount_zlecaf, 2),
            }
        )
        _tot["npf"][cat] += amount_npf
        _tot["zlecaf"][cat] += amount_zlecaf

    def _breakdown_summary(regime: str) -> dict:
        t = _tot[regime]
        total = round(t["droit_douane"] + t["tva"] + t["autre_taxe"], 2)
        return {
            "droit_douane": round(t["droit_douane"], 2),
            "autres_taxes": round(t["autre_taxe"], 2),
            "tva": round(t["tva"], 2),
            "total_taxes_et_droits": total,
            "cout_total": round(cif_value + total, 2),
        }

    _npf_sum = _breakdown_summary("npf")
    _zlc_sum = _breakdown_summary("zlecaf")
    taxes_summary = {
        "npf": _npf_sum,
        "zlecaf": _zlc_sum,
        "economie_droits": round(_npf_sum["droit_douane"] - _zlc_sum["droit_douane"], 2),
        "economie_totale": round(_npf_sum["cout_total"] - _zlc_sum["cout_total"], 2),
    }

    # ── Bi-devise : montants en monnaie locale du pays de destination ────────
    # Dégradation propre si le taux de change est indisponible (USD uniquement).
    currency_block = None
    try:
        from currencies.service import get_by_country as _get_currency
        from exchange_rates import get_service as _get_fx_service
        from services.tax_computation import localize_breakdown

        _ccy = _get_currency(country_iso3)
        if _ccy:
            _rate_obj = None
            try:
                _rate_obj = _get_fx_service().get_rate("USD", _ccy.currency_code)
            except Exception as _fx_err:
                logger.warning(f"Taux de change indisponible ({_ccy.currency_code}): {_fx_err}")
            _fx_rate = _rate_obj.rate if (_rate_obj and _rate_obj.rate) else None
            if _fx_rate:
                _loc = localize_breakdown(
                    {"breakdown": taxes_breakdown, "summary": taxes_summary}, _fx_rate
                )
                taxes_breakdown = _loc["breakdown"]
                currency_block = {
                    "local_code": _ccy.currency_code,
                    "local_name": _ccy.currency_name_fr,
                    "local_symbol": _ccy.currency_symbol,
                    "usd_to_local_rate": round(_fx_rate, 6),
                    "rate_source": _rate_obj.source,
                    "rate_as_of": _rate_obj.timestamp.isoformat(),
                    "available": True,
                    "value_usd": round(cif_value, 2),
                    "value_local": round(cif_value * _fx_rate, 2),
                    "summary_local": _loc["summary_local"],
                }
            else:
                currency_block = {
                    "local_code": _ccy.currency_code,
                    "local_name": _ccy.currency_name_fr,
                    "local_symbol": _ccy.currency_symbol,
                    "usd_to_local_rate": None,
                    "available": False,
                    "note": "Taux de change indisponible — montants en USD uniquement.",
                    "value_usd": round(cif_value, 2),
                }
    except Exception as _ccy_err:
        logger.warning(f"Bloc devise indisponible pour {country_iso3}: {_ccy_err}")

    # Contrat API fail-closed : lorsque le taux ZLECAf exact n'est pas vérifié,
    # aucun consommateur ne doit pouvoir interpréter la copie NPF interne comme
    # un total ZLECAf ou une économie nulle. Les valeurs numériques internes ne
    # servent qu'à garder la cascade stable ; la sortie publique est neutralisée.
    if zlecaf_rate_untraceable:
        for tax_line in taxes_breakdown:
            tax_line.update(
                {
                    "rate_zlecaf_pct": None,
                    "amount_zlecaf": None,
                    "amount_zlecaf_local": None,
                    "base_value_zlecaf": None,
                    "affected_by_zlecaf": False,
                }
            )
        taxes_summary = {
            "npf": _npf_sum,
            "zlecaf": None,
            "economie_droits": None,
            "economie_totale": None,
        }
        zlecaf_legacy = None
        calculation_steps_zlecaf = []
        if currency_block and currency_block.get("summary_local"):
            currency_block["summary_local"].update(
                {
                    "zlecaf": None,
                    "economie_droits": None,
                    "economie_totale": None,
                }
            )
    else:
        calculation_steps_zlecaf = zlecaf_cascade["steps"]

    return {
        "hs_code": hs_code_clean,
        "hs6": hs6,
        "description": description,
        "description_fr": line.get("description_fr", ""),
        "description_en": line.get("description_en", ""),
        "country_iso3": country_iso3,
        "origin_country": (origin_country or "").strip().upper() or None,
        "trade_regime": trade_regime,
        "trade_regime_code": trade_regime_code,
        "trade_regime_note": trade_regime_note,
        "preferential_regime_applied": preferential_regime_applied,
        "zlecaf_eligible": zlecaf_eligible,
        "zlecaf_preference_applied": zlecaf_preference_applied,
        "zlecaf_note": zlecaf_note,
        # Réserve jointe à une préférence servie (Kenya : règle d'origine non
        # arrêtée). `None` quand il n'y en a pas.
        "zlecaf_reserve": _zctx.get("zlecaf_reserve"),
        # Renseigné UNIQUEMENT quand le taux préférentiel dépassait le NPF et a
        # donc été écarté : porte le taux écarté, le taux retenu et le motif.
        # Un montant corrigé sans être dit ne serait pas opposable, et la note
        # libre ne suffit pas — un client d'API ne peut pas la lire par
        # programme. `None` quand le plancher n'a pas mordu, soit le cas
        # général.
        "plancher_npf": _zctx.get("plancher_npf"),
        # Renseigné quand une position algérienne est lue sans TVA : l'absence
        # de TVA sur le tarif DGD est une exonération (0 %), pas un trou.
        "tva_exoneree": tva_exoneree,
        "tva_exoneree_source": (
            "CTCA art. 8, 9, 10 et 11 — fiche DZA_taux_TVA_2026-09-17.json"
            if tva_exoneree
            else None
        ),
        "tva_absente": tva_absente,
        "tva_absente_source": (
            "Famille TVA absente du tarif de ce pays — total sans TVA" if tva_absente else None
        ),
        # DOCUMENTED | NOT_AVAILABLE | OFFER_ONLY | PARTNER_NOTICE_REQUIRED
        "zlecaf_status": zlecaf_status,
        "zlecaf_rate_expression": zlecaf_rate_expression,
        "zlecaf_rate_source": zlecaf_rate_source,
        "zlecaf_rate_calculation_status": zlecaf_rate_calculation_status,
        # Taux d'offre publié au e-Tariff Book officiel de la ZLECAf mais NON
        # vérifié comme légalement applicable : affiché « à vérifier avec les
        # douanes locales ». Il n'entre dans AUCUN calcul — les totaux et
        # économies restent ceux du régime NPF.
        "zlecaf_offer_rate_pct": zlecaf_offer_rate_pct,
        "zlecaf_offer_rate_expression": zlecaf_offer_rate_expression,
        "zlecaf_offer_rate_source": zlecaf_offer_rate_source,
        "cif_value": cif_value,
        "generated_at": country_data.get("generated_at", "") if country_data else "",
        "rates": {
            "daps_rate_pct": daps_rate_pct,
            "dd_rate_pct": dd_rate_pct,
            "zlecaf_rate_pct": zlecaf_rate_pct,
            # Taux préférentiel effectivement résolu après les garde-fous
            # origine/destination (réciprocité, activation et calendrier).
            # Le taux brut de la ligne ci-dessus peut être absent ou différer
            # du taux applicable (notamment pour le calendrier DZA) : le
            # frontend ne doit donc jamais le convertir implicitement en 0 %.
            "effective_zlecaf_rate_pct": (
                round(min(float(_eff_dd), float(dd_rate_pct)), 6)
                if trade_regime == "ZLECAF" and _eff_dd is not None
                else None
            ),
            "vat_rate_pct": vat_rate_pct,
            "other_taxes_pct": other_taxes_pct,
            "prct_rate_pct": prct_rate_pct,
            "tcs_rate_pct": tcs_rate_pct,
            # effective_rate_pct = total_taxes / CIF × 100 (NOT a sum of rates)
            "effective_rate_pct": npf_cascade["effective_rate_pct"],
            # Kept for legacy compatibility but labelled clearly
            "sum_of_rates_pct": round(sum(taxes_for_cascade.values()), 2),
        },
        # Step-by-step cascade — ready for frontend display
        "calculation_steps": npf_cascade["steps"],
        "calculation_steps_zlecaf": calculation_steps_zlecaf,
        "cascade_legal_source": npf_cascade["legal_source"],
        "calculation_profile_status": npf_cascade["profile_status"],
        # Legacy keys kept for backward compatibility with existing frontend code
        "npf_calculation": npf_legacy,
        "zlecaf_calculation": zlecaf_legacy,
        "savings": {
            "amount": savings_amount,
            "percentage": savings_pct,
        },
        "taxes_detail": taxes_detail,
        "individual_taxes": individual_taxes,
        "fiscal_advantages": line.get("fiscal_advantages", []),
        # Une position nationale sélectionnée (crawled_sp_entry) a ses propres
        # formalités : les préférer au champ générique du line HS6, sinon une
        # formalité d'un autre produit du même chapitre (ex. CKD/SKD réservé
        # aux kits d'assemblage automobile) s'affiche pour un produit fini
        # sans rapport (ex. lave-vaisselle 8422119000, Algérie).
        "administrative_formalities": (
            _normalize_crawled_formalities(crawled_sp_entry.get("formalities"))
            if crawled_sp_entry and crawled_sp_entry.get("formalities")
            else line.get("administrative_formalities", [])
        ),
        "has_sub_positions": len(all_sub_positions) > 0,
        "sub_position_count": len(all_sub_positions),
        "sub_position": sub_position_info,
        "data_source": "authentic_tariff",
        "data_format": "enhanced_v2",
        # Ventilation bi-régime + bi-devise (consommée par TaxBreakdownDual)
        "taxes_breakdown": taxes_breakdown,
        "taxes_summary": taxes_summary,
        "currency": currency_block,
    }


def get_available_countries():
    """Return list of countries that have tariff data files available (cached)."""
    global _available_countries_cache
    if _available_countries_cache is not None:
        return _available_countries_cache
    countries = []
    provider = _get_postgres_provider()
    if provider:
        try:
            pg_countries = provider.get_countries() or []
            if pg_countries:
                countries = [
                    {
                        "iso3": c.get("iso3", ""),
                        "name": _COUNTRY_NAMES.get(
                            c.get("iso3", ""), c.get("name_fr", c.get("iso3", ""))
                        ),
                        "total_lines": int(c.get("total_positions", 0) or 0),
                        "total_positions": int(c.get("total_positions", 0) or 0),
                        "chapters_covered": c.get("chapters_covered", 0),
                        "has_nomenclature_map": False,
                    }
                    for c in pg_countries
                ]
                _available_countries_cache = countries
                return countries
            _log_etl_fallback("get_available_countries", "ALL", reason="postgres-miss")
        except Exception as e:
            _log_etl_fallback("get_available_countries", "ALL", reason=f"postgres-error: {e}")

    try:
        for fname in sorted(os.listdir(DATA_DIR)):
            if not fname.endswith("_tariffs.json") or fname.startswith("."):
                continue
            iso3 = fname.replace("_tariffs.json", "").upper()
            data = load_country_tariffs(iso3)
            if not data:
                continue
            summary = data.get("summary", {})
            countries.append(
                {
                    "iso3": iso3,
                    "name": _COUNTRY_NAMES.get(iso3, iso3),
                    "total_lines": len(data.get("tariff_lines", [])),
                    "total_positions": summary.get("total_positions", 0),
                    "chapters_covered": summary.get("chapters_covered", 0),
                    "has_nomenclature_map": os.path.exists(
                        os.path.join(DATA_DIR, f"{iso3}_nomenclature_map.json")
                    ),
                }
            )
    except Exception as e:
        logger.error(f"Error listing available countries: {e}")
    _available_countries_cache = countries
    return countries
