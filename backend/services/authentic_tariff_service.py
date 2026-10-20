import json
import logging
import os
import re
import unicodedata
from collections import OrderedDict
from math import isfinite
from typing import Dict, Optional

from services.designation import texte_designation
from services.tax_profile_data import (
    ASSIETTE_TVA_ETABLIE,
    ASSIETTE_TVA_NON_APPLICABLE,
    BASE_FOB_TOUTES_TAXES,
    BASE_TVA_TOUTES_TAXES,
    COUNTRY_TAX_PROFILES,
    PRELEVEMENTS_CEDEAO_HORS_UEMOA,
    TAUX_TVA_LEGAUX,
    TVA_CEDEAO_HORS_UEMOA,
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
                if country_iso3 in TVA_CEDEAO_HORS_UEMOA:
                    _regle_cedeao_hors_uemoa(country_iso3, position)
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


def _regle_cedeao_hors_uemoa(country_iso3, position):
    """Gambie, Liberia, Sierra Leone, comme le socle : leurs fichiers collectés
    recopient le tarif du Bénin (redevance statistique de 1 %, TVA libérienne à
    10 %), qu'aucun texte de ces pays n'établit. La redevance est retirée, la
    TVA/GST prend le taux de la loi et les prélèvements nationaux sont ajoutés
    (TVA_CEDEAO_HORS_UEMOA, PRELEVEMENTS_CEDEAO_HORS_UEMOA ; fiche
    CEDEAO_hors_UEMOA_prelevements_2026-10-12.json). L'assiette de la TVA vient
    d'ASSIETTE_TVA_ETABLIE."""
    cle = "taxes_import" if "taxes_import" in position else "taxes"
    taxes = position.get(cle)
    if not isinstance(taxes, dict):
        return
    taux_tva = TVA_CEDEAO_HORS_UEMOA[country_iso3][0]
    corrigees = {
        code: (taux_tva if _is_vat_code(code) else valeur)
        for code, valeur in taxes.items()
        if _normalize_tax_code(code) != "RS"
    }
    for code, libelle, taux, _note in PRELEVEMENTS_CEDEAO_HORS_UEMOA.get(country_iso3, []):
        corrigees[code] = {"rate": taux, "name": libelle}
    position[cle] = corrigees


def _regle_cedeao_hors_uemoa_ligne(country_iso3, ligne):
    """La même règle sur une ligne tarifaire (fichier ETL ou PostgreSQL), dont
    les taxes sont une liste {tax, rate, observation} : redevance statistique
    retirée, TVA/GST au taux de la loi (GST libérienne publiée à 10 %),
    prélèvements nationaux ajoutés. Appliquée là où _retirer_tva_hors_la_loi
    l'est."""
    if not ligne or country_iso3 not in TVA_CEDEAO_HORS_UEMOA:
        return ligne
    taux_tva = TVA_CEDEAO_HORS_UEMOA[country_iso3][0]
    if ligne.get("vat_rate") is not None:
        ligne["vat_rate"] = taux_tva
    details = [
        d for d in ligne.get("taxes_detail") or []
        if _normalize_tax_code(str(d.get("tax") or "")) != "RS"
    ]
    for d in details:
        if _is_vat_code(str(d.get("tax") or "")):
            d["rate"] = taux_tva
    presents = {d.get("tax") for d in details}
    for code, libelle, taux, _note in PRELEVEMENTS_CEDEAO_HORS_UEMOA.get(country_iso3, []):
        if code not in presents:
            details.append({"tax": code, "rate": taux, "observation": libelle})
    ligne["taxes_detail"] = details
    taux = [d.get("rate") for d in details]
    if "other_taxes_rate" in ligne:
        ligne["other_taxes_rate"] = round(
            sum(
                d["rate"] for d in details
                if d.get("rate") is not None
                and d.get("tax") != "DD" and not _is_vat_code(str(d.get("tax") or ""))
            ),
            4,
        )
    if ligne.get("total_taxes_pct") is not None:
        ligne["total_taxes_pct"] = (
            round(sum(taux), 4) if all(t is not None for t in taux) else None
        )
    return ligne


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
    "CUF": "Customs User Fee",
    "FT": "Processing Fee",
    "PUA": "Prélèvement de l'Union africaine",
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
    if norm in {"TPI", "TAXEPARAFISCALE"} or "parafiscale" in text:
        # Maroc : la « Taxe Parafiscale à l'Importation (TPI) » arrive du crawl
        # sous son libellé entier. Sans ce mapping, elle était calculée sous un
        # code inconnu du profil MAR : la TVA, assise sur CIF+DD+TPI (CGI
        # art. 96), était sous-évaluée de TPI × TVA.
        return "TPI"
    if norm in {"TVA", "TVAI", "TVAAPTAXE", "TVAAP", "VAT", "IVA", "GST", "VALUEADDE", "VALUE_ADDE"}:
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


# Codes TVA équivalents selon le pays (portugais IVA, anglais VAT, GST de la
# Gambie, du Liberia et de la Sierra Leone, tunisien
# TVA/APTAXE) — un seul et même impôt fonctionnellement, jamais deux taxes
# distinctes. _find_vat_key() doit être utilisé PARTOUT où un code de taxe est
# comparé à "TVA" pour éviter (a) de rater le taux réel des pays non-DZA/MAR/
# COM/MDG/MRT (qui utilisent IVA/VAT), et (b) de la compter deux fois — une
# fois comme "TVA" au taux périmé de l'autre source, une fois comme sa propre
# entrée "IVA"/"VAT" dans le détail par taxe.
_VAT_EQUIVALENT_CODES = ("TVA", "IVA", "VAT", "TVAI", "GST")

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


def _tva_hors_la_loi(country_iso3, taux) -> bool:
    """Un taux de TVA collecté que la loi du pays ne connaît pas
    (TAUX_TVA_LEGAUX : 1 % ou 17,5 % au Nigéria) : il n'est servi ni au calcul
    ni à la recherche, comme dans le socle."""
    regle = TAUX_TVA_LEGAUX.get(country_iso3)
    taux = _parse_crawled_tax_rate(taux)
    return bool(regle) and taux is not None and taux not in regle["taux"]


def _retirer_tva_hors_la_loi(country_iso3, ligne):
    """Retirer d'une ligne tarifaire un taux de TVA que la loi ne connaît pas :
    le taux, son détail et le total qui l'inclut. Appliqué au chargement du
    fichier ETL et aux lignes PostgreSQL ou collectées que sert get_tariff_line."""
    if not ligne:
        return ligne
    retire = _tva_hors_la_loi(country_iso3, ligne.get("vat_rate"))
    if retire:
        ligne["vat_rate"] = None
    for detail in ligne.get("taxes_detail") or []:
        if _is_vat_code(str(detail.get("tax") or "")) and _tva_hors_la_loi(country_iso3, detail.get("rate")):
            detail["rate"] = None
            retire = True
    if retire and "total_taxes_pct" in ligne:
        ligne["total_taxes_pct"] = None
    return ligne


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
    cif_value: float,
    taxes_rates: dict,
    country_iso3: str,
    fob_value: Optional[float] = None,
    origin_iso3: Optional[str] = None,
    pays_expedition: Optional[str] = None,
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

    # ── TVA sud-africaine : exception selon l'origine ET l'expédition ────────
    # VAT Act 89/1991 s.13(2)(b) : pas de majoration de 10 % pour une origine
    # BWA, LSO, SWZ ou NAM importée de l'un de ces pays. Expédition inconnue
    # pour une telle origine : refus explicite plutôt qu'une assiette devinée.
    exception_sacu = profile.get("assiette_tva_origine_sacu")
    if exception_sacu and (origin_iso3 or "").upper() in exception_sacu["origines"]:
        if not pays_expedition:
            raise ValueError(
                "pays_expedition requis : pour une origine BWA, LSO, SWZ ou NAM, "
                "l'assiette de la TVA sud-africaine dépend du pays d'expédition "
                "(VAT Act 89/1991 s.13(2)(b))"
            )
        if pays_expedition.upper() in exception_sacu["origines"]:
            for code in taxes_order:
                if _normalize_tax_code(code) in _ALIAS_TVA:
                    tax_bases[code] = exception_sacu["base"]

    # Une TVA assise sur tous les autres droits se liquide en dernier.
    for code in [c for c in taxes_order if tax_bases.get(c, ("CIF", []))[0] == BASE_FOB_TOUTES_TAXES]:
        taxes_order.remove(code)
        taxes_order.append(code)

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
        if base_formula in ("FOB", BASE_FOB_TOUTES_TAXES) or base_formula.startswith("FOBx"):
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
            if base_formula == BASE_FOB_TOUTES_TAXES:
                base_value = fob_value + sum(
                    montant for code, montant in computed_amounts.items() if code != norm_code
                )
            else:
                # « FOBx1.10 » : forfait légal (VAT Act ZAF s.13(2)(a), NAM s.12(2)(a)).
                facteur = float(base_formula[len("FOBx") :]) if base_formula != "FOB" else 1.0
                base_value = fob_value * facteur
                for dep_code in add_codes:
                    base_value += computed_amounts.get(_normalize_tax_code(dep_code), 0.0)
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
        elif base_formula == BASE_FOB_TOUTES_TAXES:
            autres = [c for c in computed_amounts if c != norm_code]
            base_desc = "FOB + " + " + ".join(autres) if autres else "FOB"
        elif base_formula == "FOB" or base_formula.startswith("FOBx"):
            base_desc = base_formula.replace("FOBx", "FOB × ")
            if add_codes:
                base_desc += " + " + " + ".join(add_codes)
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

    if country_iso3 == "TUN":
        _completer_zero_de_tete_tun(data)
    if country_iso3 in TAUX_TVA_LEGAUX:
        for ligne in data.get("tariff_lines") or []:
            _retirer_tva_hors_la_loi(country_iso3, ligne)
    if country_iso3 in TVA_CEDEAO_HORS_UEMOA:
        for ligne in data.get("tariff_lines") or []:
            _regle_cedeao_hors_uemoa_ligne(country_iso3, ligne)
    _tariff_cache[country_iso3] = data
    return data


def _completer_zero_de_tete_tun(data):
    """Rendre son zéro de tête à une position tunisienne qui l'a perdu.

    Les positions publiées comptent 11 chiffres (10 + clé de contrôle). Une
    ligne collectée en compte 10 : « 4039011010 » pour 0403.90.11.01.0. Elle
    était rangée sous un SH6 « 403901 » qui n'existe pas, et la position
    correcte restait introuvable. Elle rejoint ici la ligne de son vrai SH6.
    """
    lignes = data.get("tariff_lines") or []
    par_sh6 = {ligne.get("hs6"): ligne for ligne in lignes}
    for ligne in list(lignes):
        sous_positions = ligne.get("sub_positions") or []
        if not sous_positions or not all(len(sp.get("code", "")) == 10 for sp in sous_positions):
            continue
        for sp in sous_positions:
            sp["code"] = sp["code"].zfill(11)
            sp["digits"] = 11
        sh6 = sous_positions[0]["code"][:6]
        cible = par_sh6.get(sh6)
        if cible is not None and cible is not ligne:
            cible.setdefault("sub_positions", []).extend(sous_positions)
            lignes.remove(ligne)
        else:
            ligne["hs6"] = sh6


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
                ligne = _retirer_tva_hors_la_loi(country_iso3, {
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
                })
                return _regle_cedeao_hors_uemoa_ligne(country_iso3, ligne)
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
        return _retirer_tva_hors_la_loi(country_iso3, {
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
        })
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
    take precedence over the generic HS6-level ones:
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
#: La « déclaration d'importation du produit » algérienne (code 910) n'est pas
#: l'une de ces obligations générales : c'est une demande adressée au contrôle
#: de la qualité du ministère du Commerce, attachée à des marchandises
#: précises — une formalité PARTICULIÈRE, servie avec son code comme les autres.
#:
#: Pour ces pays, formalites_et_statut lit la fiche de la position, jamais
#: l'agrégat SH6 : la formalité d'une position ne vaut pas pour ses voisines
#: du même SH6.
#:
#: Chaque entrée exige sa preuve, relevée sur le portail. Ne jamais ajouter un
#: pays ici « par analogie » : c'est exactement la généralisation que le Maroc a
#: démentie sur les droits nuls.
SOURCES_EXHAUSTIVES_FORMALITES = {
    "DZA": (
        "La fiche « sous-position » de l'e-service DGD publie le tableau "
        "« Formalités Administratives Particulières » (code, document) quand "
        "une formalité particulière frappe la position, et aucun tableau sinon. "
        "Vérifié sur la fiche même de chaque position : relevé des 03 et 04/10/2026, "
        "17 345 fiches sur 17 345 codes officiels, 8 671 avec tableau, 8 674 "
        "sans (data/dza/releve_dgd.json)."
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
    # Une source exhaustive change la nature de la liste vide : elle cesse
    # d'être une lacune pour devenir un constat — celui de la fiche de la
    # position, que seule une position relevée porte. Voir
    # SOURCES_EXHAUSTIVES_FORMALITES, dont chaque entrée porte sa preuve.
    # Tout se lit alors sur le crawl : le SH6 est connu quand une position du
    # tarif le porte.
    if str(country_iso3 or "").upper() in SOURCES_EXHAUSTIVES_FORMALITES:
        code = hs_code.replace(".", "").replace(" ", "")
        index = load_crawled_position_index(country_iso3)
        position = index.get(code)
        if position is None:
            if any(c.startswith(code[:6]) for c in index):
                return [], FORMALITES_NON_ETABLIES
            return [], FORMALITES_POSITION_INTROUVABLE
        formalites = _normalize_crawled_formalities(position.get("formalities"))
        return formalites, FORMALITES_DOCUMENTEES if formalites else FORMALITES_AUCUNE_PARTICULIERE
    line = get_tariff_line(country_iso3, hs_code)
    if line is None:
        # Pays sans ligne ETL : la position nationale du crawl, si elle existe.
        position = load_crawled_position_index(country_iso3).get(
            hs_code.replace(".", "").replace(" ", "")
        )
        if position is None:
            return [], FORMALITES_POSITION_INTROUVABLE
        line = {"administrative_formalities": _normalize_crawled_formalities(position.get("formalities"))}
    formalites = line.get("administrative_formalities") or []
    if formalites:
        return formalites, FORMALITES_DOCUMENTEES
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
    tva_hors_la_loi = _tva_hors_la_loi(country_iso3, tva)
    if tva_hors_la_loi:
        tva = None
    elif tva is None:
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
        if tax_code not in _PREFERENTIAL_RATE_CODES and details["rate"] is not None and details["rate"] > 0
    }
    if dd is None:
        cascade_rates.pop("DD", None)
    elif dd > 0:
        cascade_rates["DD"] = dd
    if tva_hors_la_loi:
        cascade_rates.pop("TVA", None)
    elif tva > 0:
        cascade_rates["TVA"] = tva
    # Métrique de référence par position : FOB = CIF ici (fret nul). Ce taux
    # affiché n'est pas une liquidation — celle-ci exige la valeur FOB réelle
    # de l'importation (voir compute_tax_cascade, fail-closed). Sans taux de
    # TVA servable, aucun total n'est affiché.
    ref_cascade = compute_tax_cascade(100.0, cascade_rates, country_iso3, fob_value=100.0)
    if tva_hors_la_loi:
        ref_cascade = {**ref_cascade, "effective_rate_pct": None}
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


def _plier(texte):
    """Minuscules sans accents : les tarifs publient « Cafe », l'opérateur tape « café »."""
    decompose = unicodedata.normalize("NFKD", texte.lower())
    return "".join(c for c in decompose if not unicodedata.combining(c))


def _correspond(requete, texte):
    """Chaque mot de la requête figure dans le texte, accents ignorés."""
    texte = _plier(texte)
    return all(mot in texte for mot in _plier(requete).split())


def _pertinence(requete, texte, intitule):
    """Clé de tri d'une position trouvée (la plus petite d'abord).

    Les mots de la requête présents comme mots entiers, pluriel admis :
    « lait » range le lait avant les laitances. Puis la place du premier
    d'entre eux dans l'intitulé de la rangée : « sucre » range les sucres
    (« Sucres de canne… ») avant le lait « additionné de sucre ».
    """
    texte, intitule = _plier(texte), _plier(intitule or texte)
    motifs = [rf"\b{re.escape(mot)}[sx]?\b" for mot in _plier(requete).split()]
    entiers = sum(1 for motif in motifs if re.search(motif, texte))
    places = [m.start() for m in (re.search(motif, intitule) for motif in motifs) if m]
    return (-entiers, min(places, default=len(intitule)))


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
        trouves = []
        for code, sp in crawled_index.items():
            # This PR adds national positions only. Existing HS6 lines retain
            # the ETL search path's source, shape and priority unchanged.
            if len(code) == 6 and code in etl_hs6_codes:
                continue
            if code in seen_codes:
                continue
            # La désignation de la position, et les libellés publiés de sa
            # rangée et de son chapitre quand la source les donne.
            name = " ".join(
                x
                for x in (
                    sp.get("name") or sp.get("description") or sp.get("designation"),
                    sp.get("heading_label"),
                    sp.get("chapter_label"),
                )
                if x
            )
            if code.startswith(q):
                trouves.append((0, (0, 0), code, sp))
            elif _correspond(q, name):
                trouves.append((1, _pertinence(q, name, sp.get("heading_label")), code, sp))
        # Le code d'abord, puis la pertinence, puis l'ordre du tarif.
        for _, _, code, sp in sorted(trouves, key=lambda t: t[:3]):
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
                if hs6 in seen_codes or not (hs6.startswith(q) or _correspond(q, desc)):
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
                if code not in seen_codes and (code.startswith(q) or _correspond(q, description)):
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

    Source unique de vérité : zlecaf_membership_status, zlecaf_schedule_dza,
    zlecaf_schedule_zaf, zlecaf_implementation_registry + regional_blocs.

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

    # 2 ter. Tunisie : texte TA n°016/2023 — coefficient 2026 du Tarif Web ×
    #    droit de base 2019 (e-Tariff), plafonné au NPF. Le calendrier par pays
    #    de l'e-Tariff est faux pour la Tunisie : il n'est jamais servi.
    if dest == "TUN":
        from services.zlecaf_implementation_registry import implementation_decision
        from services.zlecaf_schedule_tun import compute_tun_zlecaf_rate, note_zale

        decision = implementation_decision(dest, origin)
        if not decision["applied"]:
            zale = note_zale(hs_code_clean, origin)
            contexte = _no_preference(
                " ".join(filter(None, (decision["note"], zale))), zlecaf_rate_status=decision["status"]
            )
            if zale and zale not in (contexte["trade_regime_note"] or ""):
                # Égypte : la note COMESA occupe le bandeau ; la franchise ZALE
                # publiée y est ajoutée, toujours sans être calculée.
                contexte["trade_regime_note"] = f"{contexte['trade_regime_note']} {zale}"
            return contexte
        _r, _src = compute_tun_zlecaf_rate(hs_code_clean, origin, dd_rate_pct)
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
        from services.zlecaf_schedule_zaf import (
            zaf_partner_active,
            zaf_suspension_active,
        )

        if zaf_suspension_active(origin, hs_code_clean):
            return _no_preference(
                "Préférence ZLECAf suspendue par l'Afrique du Sud pour cette "
                "ligne (Notice R.6594, GG 53334 du 12/09/2025) — taux NPF "
                "appliqué"
            )
        if not zaf_partner_active(origin):
            return _no_preference(
                "ZLECAf ratifié mais échanges préférentiels pas encore activés "
                "avec l'Afrique du Sud pour cette origine (General Note O du "
                "Schedule No. 1) — taux NPF appliqué"
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
    from services.zlecaf_implementation_registry import DESTINATIONS_REGLE_B_EAC

    if dest in DESTINATIONS_REGLE_B_EAC and applied:
        # Même réserve que le moteur du socle : rubrique sans règle d'origine
        # arrêtée à l'Appendice IV (décembre 2023), que l'État n'exclut pas.
        # Le barème n'est chargé que pour ces destinations.
        from services.zlecaf_schedule_ken import reserve_regle_d_origine

        contexte["zlecaf_reserve"] = reserve_regle_d_origine(hs_code_clean)
    return contexte


# Alias public : le moteur de rapports (benchmarking_service) doit appliquer
# EXACTEMENT le même régime préférentiel que le calculateur (activation
# bilatérale Algérie/Afrique du Sud, unions douanières, ratification) — jamais
# le taux ZLECAf générique de la ligne sans tenir compte de l'origine.
resolve_zlecaf_context = _resolve_zlecaf_context


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
