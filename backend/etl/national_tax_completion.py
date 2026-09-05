"""
National Tax Completion — état de complétion fiscale nationale par pays
========================================================================

Contexte : les TEC régionaux (CEDEAO, CEMAC, EAC, SACU) ne publient que les
droits de douane (DD). Les droits et taxes d'effet équivalent (DTE), la TVA,
les accises et les redevances nationales relèvent des administrations
nationales (douanes, impôts, lois de finances) et doivent être collectées
pays par pays.

Sources de vérité — TOUTES préexistantes sur le disque (aucune invention) :
- ``data/{pays}/vat_measures.json``  — taux TVA nationaux (31 pays, statuts
  VERIFIED_PRIMARY_TEXT / VERIFIED_CONSOLIDATED_HTML, références légales +
  PDF officiels archivés sous ``data/sources/{pays}/official/``) ;
- ``data/{pays}/excise_measures.json`` — accises nationales (7 pays) ;
- ``data/{pays}/legal_sources.json`` — registre des sources par pays
  (invariant testé : tout source_id cité y est enregistré) ;
- ``backend/etl/para_fiscal_levies.py`` — prélèvements communautaires/nationaux
  documentés avec références légales ;
- ``crawlers.all_countries_registry.NATIONAL_TAX_SOURCES`` — déclaration des
  sources officielles RESTANT à collecter (trous réels : BDI, BWA, COM, DJI,
  ERI, GNQ, LBY, LSO, MDG, MOZ, MWI, NAM, SDN, SOM, SSD, STP, SWZ, SYC, ZMB,
  ZWE + complétion VAT TUN/UGA) ;
- ``backend/data/{CC}_tariffs.json`` (canonical_v4) — DD TEC + taxes_detail.

Doctrine (MISSION_TARIFS_AFRICAINS.md) : ce module N'INVENTE AUCUN taux et
N'APPLIQUE AUCUN défaut. Statuts uniquement — les taux vivent dans les
datasets sourcés ci-dessus.
"""

import json
import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

try:  # exécution depuis backend/ (app) ou depuis la racine (tests)
    from crawlers.all_countries_registry import (
        NATIONAL_TAX_COMPLETED,
        NATIONAL_TAX_SOURCES,
        get_country_config,
    )
    from etl.para_fiscal_levies import LEVY_DESCRIPTIONS
except ImportError:  # pragma: no cover
    import sys

    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from crawlers.all_countries_registry import (
        NATIONAL_TAX_COMPLETED,
        NATIONAL_TAX_SOURCES,
        get_country_config,
    )
    from etl.para_fiscal_levies import LEVY_DESCRIPTIONS

BACKEND_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKEND_DATA_DIR = os.path.join(BACKEND_ROOT, "data")
ROOT_DATA_DIR = os.path.join(os.path.dirname(BACKEND_ROOT), "data")
NATIONAL_TAX_STATUS_PATH = os.path.join(
    BACKEND_DATA_DIR, "national_taxes", "collection_status.json"
)
ARBITRATION_PATH = os.path.join(ROOT_DATA_DIR, "coverage", "national_tax_arbitration.json")

# Familles de taxes au-delà du DD du TEC régional.
TAX_FAMILIES = ("VAT", "EXCISE", "DTE", "PARAFISCAL_NATIONAL")

# Datasets existants par famille (convention « complétion de l'existant »).
MEASURE_FILES = {
    "VAT": "vat_measures.json",
    "EXCISE": "excise_measures.json",
}

# Statuts possibles (alignés sur la doctrine — aucun taux ne circule ici).
STATUS_DOCUMENTED_NATIONAL = "DOCUMENTED_NATIONAL"
STATUS_DOCUMENTED = "DOCUMENTED_PRIMARY_SOURCE"
STATUS_PARTIAL_DOCUMENTED = "PARTIAL_DOCUMENTED"
STATUS_PENDING_OFFICIAL = "PENDING_OFFICIAL_COLLECTION"
STATUS_NOT_AVAILABLE = "NOT_AVAILABLE"
STATUS_DOCUMENTED_COMMUNITY = "DOCUMENTED_COMMUNITY"

# Correspondance répertoires ``data/{slug}/`` (existants) -> ISO3.
COUNTRY_SLUG_TO_ISO3 = {
    "algeria": "DZA",
    "angola": "AGO",
    "benin": "BEN",
    "burkina-faso": "BFA",
    "cameroon": "CMR",
    "cape-verde": "CPV",
    "chad": "TCD",
    "congo-brazzaville": "COG",
    "cote-d-ivoire": "CIV",
    "drc": "COD",
    "egypt": "EGY",
    "gabon": "GAB",
    "gambia": "GMB",
    "ghana": "GHA",
    "guinea": "GIN",
    "guinea-bissau": "GNB",
    "kenya": "KEN",
    "liberia": "LBR",
    "mali": "MLI",
    "mauritania": "MRT",
    "mauritius": "MUS",
    "morocco": "MAR",
    "niger": "NER",
    "nigeria": "NGA",
    "rwanda": "RWA",
    "senegal": "SEN",
    "sierra-leone": "SLE",
    "south_africa": "ZAF",
    "tanzania": "TZA",
    "togo": "TGO",
    "tunisia": "TUN",
    "uganda": "UGA",
}

# Registres d'enrichissement tarifaire (existants, consommés par
# services/tariff_enrichment_service.py) — vue « service » par pays :
# vat_status, other_taxes_status, national_extension_status.
ENRICHMENT_REGISTRY_PATHS = (
    "data/regional-18/tariff_enrichment_registry.json",
    "data/west-africa-15/tariff_enrichment_registry.json",
    "data/algeria-active-3/tariff_enrichment_registry.json",
    "data/morocco-angola-2/tariff_enrichment_registry.json",
)

# Clés du registre d'enrichissement alignées sur nos familles.
_ENRICHMENT_KEY_BY_FAMILY = {
    "VAT": "vat_status",
    "PARAFISCAL_NATIONAL": "other_taxes_status",
}


def load_enrichment_registry_statuses() -> Dict[str, Dict[str, Any]]:
    """
    Fusionne les registres d'enrichissement existants (vue « service ») :
    {iso3: {vat_status, other_taxes_status, national_extension_status,
            registry_path, as_of}}.
    """
    merged: Dict[str, Dict[str, Any]] = {}
    for rel in ENRICHMENT_REGISTRY_PATHS:
        path = os.path.join(os.path.dirname(BACKEND_ROOT), rel)
        data = _read_json(path)
        if not data:
            continue
        for iso3, cfg in (data.get("countries") or {}).items():
            merged[iso3] = {
                "vat_status": cfg.get("vat_status"),
                "other_taxes_status": cfg.get("other_taxes_status"),
                "national_extension_status": cfg.get("national_extension_status"),
                "registry_path": rel,
                "as_of": data.get("as_of"),
            }
    return merged


def _read_json(path: str) -> Optional[dict]:
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except Exception as e:
        logger.warning(f"Lecture impossible {path}: {e}")
        return None


def load_arbitration_decisions() -> Dict[str, Dict[str, dict]]:
    """
    Décisions d'arbitrage dataset ↔ registre (data/coverage/national_tax_arbitration.json),
    tranchées par l'examen des preuves sur disque — jamais par estimation.
    Retourne {iso3: {"VAT": decision_dict}}.
    """
    data = _read_json(ARBITRATION_PATH) or {}
    decisions: Dict[str, Dict[str, dict]] = {}
    for d in data.get("decisions") or []:
        iso3 = str(d.get("country") or "").upper()
        family = str(d.get("family") or "").upper()
        if iso3 and family:
            decisions.setdefault(iso3, {})[family] = d
    return decisions


def _measure_records(dataset: dict, family: str) -> List[dict]:
    key = {"VAT": "vat_rates", "EXCISE": "excise_rates"}.get(family)
    records = dataset.get(key) if key else None
    return records if isinstance(records, list) else []


def discover_measure_datasets() -> Dict[str, Dict[str, Dict[str, Any]]]:
    """
    Découvre les datasets de mesures nationales existants sur le disque
    (``data/{slug}/{vat,excise}_measures.json``) et retourne, par ISO3 puis
    famille, leur état réel : nombre d'enregistrements, statuts de vérification.
    Aucun taux n'est retourné — uniquement des métriques de provenance.
    """
    discovered: Dict[str, Dict[str, Dict[str, Any]]] = {}
    if not os.path.isdir(ROOT_DATA_DIR):
        return discovered
    for entry in sorted(os.listdir(ROOT_DATA_DIR)):
        iso3 = COUNTRY_SLUG_TO_ISO3.get(entry)
        if not iso3:
            continue
        for family, fname in MEASURE_FILES.items():
            path = os.path.join(ROOT_DATA_DIR, entry, fname)
            if not os.path.exists(path):
                continue
            dataset = _read_json(path) or {}
            records = _measure_records(dataset, family)
            verified = [
                r
                for r in records
                if str(r.get("verification_status") or "").startswith("VERIFIED")
            ]
            discovered.setdefault(iso3, {})[family] = {
                "dataset_path": os.path.relpath(path, os.path.dirname(ROOT_DATA_DIR)),
                "records": len(records),
                "verified_records": len(verified),
                "verification_statuses": sorted(
                    {str(r.get("verification_status")) for r in records if r.get("verification_status")}
                ),
            }
    return discovered


def _canonical_line_count(iso3: str) -> int:
    path = os.path.join(BACKEND_DATA_DIR, f"{iso3.upper()}_tariffs.json")
    if not os.path.exists(path):
        return 0
    data = _read_json(path) or {}
    return len(data.get("tariff_lines") or [])


def _community_levies(iso3: str) -> List[str]:
    cfg = NATIONAL_TAX_SOURCES.get(iso3.upper()) or {}
    return list(cfg.get("documented_levies") or [])


def _family_status(
    iso3: str,
    family: str,
    discovered: Dict[str, Dict[str, Dict[str, Any]]],
    registries: Dict[str, Dict[str, Any]],
    arbitrations: Dict[str, Dict[str, dict]],
) -> Dict[str, Any]:
    """
    Statut par famille, croisant deux vues existantes (datasets et registres
    d'enrichissement). Les divergences sont tranchées UNIQUEMENT par les
    décisions d'arbitrage documentées (data/coverage/national_tax_arbitration.json),
    chacune fondée sur des preuves citées — jamais par estimation.
    """
    registry_key = _ENRICHMENT_KEY_BY_FAMILY.get(family)
    registry_status = (registries.get(iso3) or {}).get(registry_key)

    if family in MEASURE_FILES:
        ds = (discovered.get(iso3) or {}).get(family)
        if ds:
            if ds["verified_records"] > 0:
                status = STATUS_DOCUMENTED
            else:
                status = STATUS_PARTIAL_DOCUMENTED
        else:
            status = STATUS_PENDING_OFFICIAL
            ds = {
                "dataset_path": None,
                "records": 0,
                "verified_records": 0,
            }
        result = {"status": status, **ds}

        # Divergence dataset ↔ registre (conservée, non arbitrée par défaut)
        divergence = None
        if registry_status:
            dataset_ok = status == STATUS_DOCUMENTED
            registry_ok = str(registry_status).upper() == "DOCUMENTED"
            if dataset_ok != registry_ok:
                divergence = {
                    "registry_status": registry_status,
                    "registry_path": (registries.get(iso3) or {}).get("registry_path"),
                    "note": (
                        "Vue registre d'enrichissement ≠ vue dataset — arbitrage "
                        "requiert une décision documentée."
                    ),
                }
        if registry_status:
            result["registry_status"] = registry_status

        # Application de la décision d'arbitrage documentée (si existante)
        decision = (arbitrations.get(iso3) or {}).get(family)
        if decision:
            code = decision.get("decision_code")
            result["arbitration"] = {
                "decision_code": code,
                "resolution": decision.get("resolution"),
                "evidence": decision.get("evidence"),
            }
            if code == "DATASET_EVIDENCE_RETAINED":
                # Preuve dataset (texte primaire gouvernemental) confirmée
                if divergence:
                    divergence["resolved_by_arbitration"] = True
            elif code == "OFFICIAL_CURRENT_PAGE_RETAINED":
                # Consolidation sur page officielle de l'administration (archivée)
                # — même effet que DATASET_EVIDENCE_RETAINED (précédent LSO).
                if divergence:
                    divergence["resolved_by_arbitration"] = True
            elif code == "OFFICIAL_PRIMARY_TEXT_EXTRACTED":
                # Taux extrait et cité depuis un texte officiel archivé :
                # le claim du registre devient substantié.
                result["status"] = STATUS_DOCUMENTED
                result["consolidation_note"] = (decision.get("evidence") or {}).get(
                    "extraction_method"
                )
                divergence = None
            elif code == "ENRICHMENT_PARTIAL_SUBSTANTIATED":
                # PARTIAL substantié par national_enrichment.json (taux +
                # sources vérifiées) : progrès depuis PENDING, sans promotion.
                result["status"] = STATUS_PARTIAL_DOCUMENTED
                evidence = decision.get("evidence") or {}
                result["dataset_path"] = evidence.get("enrichment_file")
                scope = decision.get("scope_limitation")
                if scope:
                    result["scope_limitation"] = scope
                divergence = None
            elif code == "REGISTRY_PRUDENCE_RETAINED":
                # Copie non gouvernementale : la prudence du registre l'emporte
                result["status"] = STATUS_PARTIAL_DOCUMENTED
                if divergence:
                    divergence["resolved_by_arbitration"] = True
            elif code == "REGISTRY_SUBSTANTIATED_BY_ENRICHMENT":
                # Registre substantié par national_enrichment.json (textes vérifiés)
                result["status"] = STATUS_DOCUMENTED
                evidence = decision.get("evidence") or {}
                result["dataset_path"] = evidence.get("enrichment_file")
                scope = decision.get("scope_limitation")
                if scope:
                    result["scope_limitation"] = scope
                divergence = None  # divergence résolue en faveur du registre
            elif code == "REGISTRY_CLAIM_UNSUBSTANTIATED":
                # Claim du registre sans preuve sur disque : dégradation honnête
                result["status"] = STATUS_PARTIAL_DOCUMENTED
                if divergence:
                    divergence["resolved_by_arbitration"] = True

        if divergence:
            result["registry_divergence"] = divergence
        return result

    if family == "DTE":
        return {
            "status": STATUS_PENDING_OFFICIAL,
            "dataset_path": None,
            "registry_status": registry_status,
            "note": (
                "Aucun dataset DTE national existant — à collecter auprès des "
                "douanes nationales (registre NATIONAL_TAX_SOURCES)."
            ),
        }

    # PARAFISCAL_NATIONAL
    levies = _community_levies(iso3)
    return {
        "status": STATUS_DOCUMENTED_COMMUNITY if levies else STATUS_NOT_AVAILABLE,
        "documented_levies": levies,
        "registry_status": registry_status,
        "reference": "etl/para_fiscal_levies.py (références légales citées)",
    }


def get_completion_status(country_iso3: str) -> Dict[str, Any]:
    """
    État de complétion fiscale nationale d'un pays, par famille de taxes.
    Aucun taux n'est retourné — uniquement des statuts, des chemins de
    datasets sourcés et des métriques de provenance.
    """
    iso3 = (country_iso3 or "").upper().strip()
    if not iso3:
        return {"country_iso3": None, "status": STATUS_NOT_AVAILABLE}

    discovered = discover_measure_datasets()
    registries = load_enrichment_registry_statuses()
    arbitrations = load_arbitration_decisions()
    canonical_lines = _canonical_line_count(iso3)
    completed_national = iso3 in NATIONAL_TAX_COMPLETED

    families = {
        family: _family_status(iso3, family, discovered, registries, arbitrations)
        for family in TAX_FAMILIES
    }

    if completed_national:
        overall = STATUS_DOCUMENTED_NATIONAL
    elif any(
        families[f]["status"] in (STATUS_DOCUMENTED, STATUS_PARTIAL_DOCUMENTED)
        for f in ("VAT", "EXCISE")
    ):
        # Au moins une famille nationale (TVA/accises) a une substantiation
        # vérifiée ou partiellement vérifiée — sans être un tarif national complet.
        overall = STATUS_PARTIAL_DOCUMENTED
    else:
        overall = STATUS_PENDING_OFFICIAL

    return {
        "country_iso3": iso3,
        "tariff_lines_canonical": canonical_lines,
        "overall_status": overall,
        "dd_regional": (
            {
                "status": "DOCUMENTED_REGIONAL",
                "detail": "TEC régional officiel (canonical_v4)",
            }
            if canonical_lines > 0
            else {"status": STATUS_NOT_AVAILABLE, "detail": "aucun fichier canonique"}
        ),
        "tax_families": families,
        "enrichment_registry": registries.get(iso3),
        "national_taxes": {
            "status": overall,
            "official_document_archived": _has_archived_national_document(iso3),
        },
        "collection": NATIONAL_TAX_SOURCES.get(iso3),
    }


def _has_archived_national_document(iso3: str) -> bool:
    """True si au moins un document national officiel archivé (collecte scraper)."""
    if not os.path.exists(NATIONAL_TAX_STATUS_PATH):
        return False
    statuses = _read_json(NATIONAL_TAX_STATUS_PATH) or {}
    docs = (statuses.get(iso3.upper()) or {}).get("documents") or []
    return any(d.get("status") == "RAW_ARCHIVED" for d in docs)


def national_completion_report() -> Dict[str, Any]:
    """Rapport agrégé de complétion (CI / rapports / API interne)."""
    discovered = discover_measure_datasets()
    all_codes = sorted(
        set(COUNTRY_SLUG_TO_ISO3.values())
        | set(NATIONAL_TAX_SOURCES.keys())
        | set(NATIONAL_TAX_COMPLETED)
    )
    per_country = {code: get_completion_status(code) for code in all_codes}

    counts: Dict[str, int] = {}
    for st in per_country.values():
        key = st["overall_status"]
        counts[key] = counts.get(key, 0) + 1

    vat_documented = sorted(
        code
        for code, st in per_country.items()
        if st["tax_families"]["VAT"]["status"] == STATUS_DOCUMENTED
    )
    excise_documented = sorted(
        code
        for code, st in per_country.items()
        if st["tax_families"]["EXCISE"]["status"] == STATUS_DOCUMENTED
    )
    verified_portals = [
        code
        for code, cfg in NATIONAL_TAX_SOURCES.items()
        if (cfg.get("tax_authority") or {}).get("url_status") == "VERIFIED_200"
    ]
    # Divergences dataset ↔ registre — seules les divergences NON résolues
    # par une décision d'arbitrage documentée restent listées.
    divergences = []
    arbitration_summary: Dict[str, int] = {}
    for code, st in per_country.items():
        for family, f in st["tax_families"].items():
            arb = f.get("arbitration")
            if arb:
                code_arb = arb.get("decision_code")
                arbitration_summary[code_arb] = arbitration_summary.get(code_arb, 0) + 1
            if f.get("registry_divergence") and not f["registry_divergence"].get(
                "resolved_by_arbitration"
            ):
                divergences.append(
                    {
                        "country": code,
                        "family": family,
                        "dataset_status": f["status"],
                        **f["registry_divergence"],
                    }
                )
    return {
        "as_of": datetime.now(timezone.utc).isoformat(),
        "countries_total": len(all_codes),
        "overall_status_counts": counts,
        "vat_documented_countries": vat_documented,
        "excise_documented_countries": excise_documented,
        "enrichment_registry_countries": sorted(load_enrichment_registry_statuses()),
        "dataset_registry_divergences": divergences,
        "arbitration": {
            "file": "data/coverage/national_tax_arbitration.json",
            "decisions_applied": sum(arbitration_summary.values()),
            "by_decision_code": arbitration_summary,
        },
        "portals_verified_200": sorted(verified_portals),
        "doctrine": (
            "Aucun taux inventé. Les taxes nationales (TVA, accises, DTE, "
            "redevances) proviennent exclusivement des datasets sourcés "
            "(data/{pays}/*_measures.json, vérification VERIFIED_*, PDF officiels "
            "archivés) ou restent PENDING_OFFICIAL_COLLECTION."
        ),
        "per_country": per_country,
    }


def write_completion_report_md(out_path: str) -> str:
    """Écrit le rapport de complétion en Markdown (rapports d'exécution)."""
    report = national_completion_report()
    counts = report["overall_status_counts"]
    lines: List[str] = [
        "# Complétion fiscale nationale au-delà des TEC — état de collecte",
        "",
        f"_Généré le {report['as_of']} — doctrine : aucun mock, aucune hallucination, "
        "aucune extrapolation._",
        "",
        f"- Pays suivis : **{report['countries_total']}**",
        f"- Tarif national complet (8–11 chiffres) : "
        f"**{counts.get(STATUS_DOCUMENTED_NATIONAL, 0)}**",
        f"- Taxes nationales partiellement documentées : "
        f"**{counts.get(STATUS_PARTIAL_DOCUMENTED, 0)}**",
        f"- En attente de collecte officielle : "
        f"**{counts.get(STATUS_PENDING_OFFICIAL, 0)}**",
        f"- TVA documentée (dataset sourcé) : **{len(report['vat_documented_countries'])}** "
        f"pays — {', '.join(report['vat_documented_countries'])}",
        f"- Accises documentées (dataset sourcé) : "
        f"**{len(report['excise_documented_countries'])}** pays — "
        f"{', '.join(report['excise_documented_countries'])}",
        f"- Portails officiels vérifiés joignables (HTTP 200) : "
        f"**{len(report['portals_verified_200'])}**",
        f"- Pays couverts par les registres d'enrichissement (vue service) : "
        f"**{len(report['enrichment_registry_countries'])}**",
        f"- Divergences dataset ↔ registre NON résolues : "
        f"**{len(report['dataset_registry_divergences'])}**",
        f"- Décisions d'arbitrage appliquées (preuves citées) : "
        f"**{report['arbitration']['decisions_applied']}** — "
        + ", ".join(
            f"{k}: {v}" for k, v in report["arbitration"]["by_decision_code"].items()
        ),
        "",
        "| Pays | Statut global | VAT | EXCISE | DTE | Para-fiscal national |",
        "|---|---|---|---|---|---|",
    ]
    for code, st in report["per_country"].items():
        fams = st["tax_families"]
        cells = []
        for family in ("VAT", "EXCISE", "DTE"):
            f = fams[family]
            cell = f["status"]
            if f.get("verified_records"):
                cell += f" ({f['verified_records']} vérifiés)"
            cells.append(cell)
        pf = fams["PARAFISCAL_NATIONAL"]
        cells.append(
            f"{pf['status']} ({', '.join(pf.get('documented_levies') or []) or '—'})"
        )
        lines.append(f"| {code} | {st['overall_status']} | " + " | ".join(cells) + " |")

    lines += [
        "",
        "## Règle d'or",
        "",
        report["doctrine"],
        "",
    ]
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))
    return out_path


def coverage_update_entries() -> Dict[str, str]:
    """
    Valeurs du champ ``national_taxes`` pour
    ``data/coverage/africa_country_coverage.json`` (remplace « SOURCE_PENDING »
    par des statuts précis — jamais par une donnée).
    """
    entries: Dict[str, str] = {}
    all_codes = sorted(
        set(COUNTRY_SLUG_TO_ISO3.values())
        | set(NATIONAL_TAX_SOURCES.keys())
        | set(NATIONAL_TAX_COMPLETED)
    )
    for code in all_codes:
        st = get_completion_status(code)
        entries[code] = st["overall_status"]
    return entries
