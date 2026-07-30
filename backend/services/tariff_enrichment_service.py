"""Traceable tariff, fiscal and regulatory coverage across enrichment waves."""

import copy
import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional

REPO_ROOT = Path(__file__).resolve().parents[2]
RESOLVED_REPO_ROOT = REPO_ROOT.resolve()
REGISTRY_PATHS = (
    REPO_ROOT / "data" / "regional-18" / "tariff_enrichment_registry.json",
    REPO_ROOT / "data" / "west-africa-15" / "tariff_enrichment_registry.json",
    REPO_ROOT / "data" / "algeria-active-3" / "tariff_enrichment_registry.json",
)


@lru_cache(maxsize=1)
def _load_registry() -> Dict[str, Any]:
    registries = [
        json.loads(path.read_text(encoding="utf-8")) for path in REGISTRY_PATHS if path.is_file()
    ]
    if not registries:
        raise FileNotFoundError("No tariff enrichment registry file was found")

    merged: Dict[str, Any] = {
        "as_of": max(item["as_of"] for item in registries),
        "regions": {},
        "countries": {},
        "country_disclaimers": {},
    }
    for registry in registries:
        overlap = set(merged["countries"]) & set(registry["countries"])
        if overlap:
            raise ValueError(
                "Duplicate enrichment countries across registries: " + ", ".join(sorted(overlap))
            )
        merged["regions"].update(copy.deepcopy(registry["regions"]))
        merged["countries"].update(copy.deepcopy(registry["countries"]))
        merged["country_disclaimers"].update(
            {country: registry["disclaimer"] for country in registry["countries"]}
        )
    return merged


@lru_cache(maxsize=None)
def _read_json(relative_path: str) -> Dict[str, Any]:
    source_path = (RESOLVED_REPO_ROOT / relative_path).resolve()
    try:
        source_path.relative_to(RESOLVED_REPO_ROOT)
    except ValueError as exc:
        raise ValueError(
            f"Enrichment source path resolves outside repository: {relative_path}"
        ) from exc
    return json.loads(source_path.read_text(encoding="utf-8"))


def _compact_legal_sources(source_paths: List[str]) -> List[Dict[str, Any]]:
    compact: List[Dict[str, Any]] = []
    for relative_path in source_paths:
        if not relative_path.endswith("legal_sources.json"):
            continue
        for source in _read_json(relative_path).get("sources", []):
            compact.append(
                {
                    "source_id": source.get("source_id"),
                    "title": source.get("official_title") or source.get("title"),
                    "institution": source.get("institution"),
                    "legal_date": (
                        source.get("legal_date")
                        or source.get("publication_date")
                        or source.get("consolidation_date")
                    ),
                    "url": source.get("html_url") or source.get("url") or source.get("pdf_url"),
                    "sha256": source.get("sha256"),
                    "verification_status": (
                        source.get("verification_status")
                        or source.get("source_status")
                        or source.get("status")
                    ),
                    "registry_path": relative_path,
                }
            )
    return compact


def _measure_source_ids(measures: Dict[str, Any]) -> List[str]:
    """Return the stable source identifiers used by published tax records."""

    return sorted(
        {
            source_id
            for collection in ("vat_rates", "vat_exemptions", "vat_zero_rated")
            for record in measures.get(collection, [])
            if (source_id := record.get("source_id"))
        }
    )


def _kenya_required_documents(record_ids: List[str]) -> List[Dict[str, Any]]:
    data = _read_json("data/kenya/administrative_formalities.json")
    records = {
        item.get("record_id"): item
        for item in data.get("administrative_formalities", [])
        if item.get("record_id") in record_ids
    }
    metadata = {
        "FORM-TPA-44A": {
            "title": "Certificate of Origin",
            "issuer": None,
            "responsible_authority": "Kenya Revenue Authority — Commissioner or authorised officer",
            "platform": None,
            "stage": "Before processing and clearance of the import entry",
            "validity": "Valid when the statutory information listed in section 44A is disclosed",
            "transport": "All modes",
            "scope": "All goods imported into Kenya",
        },
        "FORM-KRA-CLEARANCE-DOCS": {
            "title": "Import clearance supporting-document set",
            "issuer": None,
            "responsible_authority": "Kenya Revenue Authority",
            "platform": None,
            "stage": "Import clearance",
            "validity": None,
            "transport": "All modes; transport document varies by mode",
            "scope": "General import-clearance package; conditional documents apply only where relevant",
        },
    }
    missing_records = sorted(set(record_ids) - set(records))
    if missing_records:
        raise ValueError(
            "Kenya required-document records missing from "
            f"administrative_formalities.json: {', '.join(missing_records)}"
        )
    missing_metadata = sorted(set(record_ids) - set(metadata))
    if missing_metadata:
        raise ValueError(
            "Kenya required-document metadata missing for: " f"{', '.join(missing_metadata)}"
        )

    documents: List[Dict[str, Any]] = []
    for record_id in record_ids:
        record = records[record_id]
        document = dict(metadata[record_id])
        document.update(
            {
                "document_id": record_id,
                "conditions": record.get("legal_product_description"),
                "exemptions": None,
                "hs_codes_explicit": record.get("hs_codes_explicit", []),
                "hs_level_requirement": bool(record.get("hs_codes_explicit")),
                "source_id": record.get("source_id"),
                "legal_reference": record.get("legal_reference"),
                "effective_from": record.get("effective_from"),
                "verification_status": record.get("verification_status"),
                "source_record_path": "data/kenya/administrative_formalities.json",
            }
        )
        documents.append(document)
    return documents


def _cod_required_documents(record_ids: List[str]) -> List[Dict[str, Any]]:
    data = _read_json("data/drc/regulatory_measures.json")
    stage_by_category = {
        "single_window": "Electronic trade-formality submission",
        "conformity_assessment": "Pre-shipment inspection and import clearance",
        "cargo_tracking_note": "Before shipment and before cargo arrival",
    }
    documents: List[Dict[str, Any]] = []
    found_record_ids = set()
    for measure in data.get("regulatory_measures", []):
        record_id = measure.get("record_id")
        if record_id not in record_ids:
            continue
        found_record_ids.add(record_id)
        for index, title in enumerate(measure.get("documents", []), start=1):
            documents.append(
                {
                    "document_id": f"{record_id}-DOC-{index}",
                    "title": title,
                    "issuer": None,
                    "receiving_authority": measure.get("authority"),
                    "responsible_authority": measure.get("authority"),
                    "platform": measure.get("platform"),
                    "stage": stage_by_category.get(measure.get("measure_category")),
                    "validity": None,
                    "conditions": measure.get("conditions"),
                    "exemptions": (
                        None
                        if measure.get("exemptions") == "NOT_AVAILABLE"
                        else measure.get("exemptions")
                    ),
                    "transport": measure.get("transport"),
                    "scope": measure.get("products"),
                    "hs_codes_explicit": measure.get("hs_codes_explicit", []),
                    "hs_level_requirement": bool(measure.get("hs_codes_explicit")),
                    "source_id": measure.get("source_id"),
                    "legal_reference": measure.get("legal_reference"),
                    "verification_status": measure.get("verification_status"),
                    "pending_primary_archive": measure.get("pending_primary_archive", False),
                    "source_record_path": "data/drc/regulatory_measures.json",
                }
            )
    missing_records = sorted(set(record_ids) - found_record_ids)
    if missing_records:
        raise ValueError(
            "DRC required-document measures missing from regulatory_measures.json: "
            f"{', '.join(missing_records)}"
        )
    return documents


def get_supported_enrichment_countries() -> List[str]:
    """Return the exact ISO3 coverage of all published enrichment waves."""

    return sorted(_load_registry()["countries"])


def get_country_enrichment(country_iso3: str) -> Optional[Dict[str, Any]]:
    """Return source-bound enrichment without synthesising missing values."""

    country = country_iso3.upper()
    registry = _load_registry()
    configured = registry["countries"].get(country)
    if configured is None:
        return None

    result = copy.deepcopy(configured)
    result["country_iso3"] = country
    result["as_of"] = registry["as_of"]
    result["tariff"] = copy.deepcopy(registry["regions"][configured["region"]]["tariff"])
    result["traceability_sources"] = _compact_legal_sources(configured["source_paths"])

    vat_measure_path = configured.get("vat_measure_path")
    if vat_measure_path:
        vat_data = _read_json(vat_measure_path)
        vat_is_available = configured["vat_status"] != "NOT_AVAILABLE"
        result["consumption_tax"] = {
            "tax_type": "VAT_OR_GST",
            "status": configured["vat_status"],
            "rates": copy.deepcopy(vat_data.get("vat_rates", [])) if vat_is_available else [],
            "exemptions": (
                copy.deepcopy(vat_data.get("vat_exemptions", [])) if vat_is_available else []
            ),
            "zero_rated": (
                copy.deepcopy(vat_data.get("vat_zero_rated", [])) if vat_is_available else []
            ),
            "source_ids": _measure_source_ids(vat_data) if vat_is_available else [],
            "source_record_path": vat_measure_path,
        }

    national_measure_path = configured.get("national_measure_path")
    national_data = None
    if national_measure_path:
        national_data = _read_json(national_measure_path)["countries"].get(country)
        if national_data is None:
            raise ValueError(
                f"National enrichment record missing for {country}: {national_measure_path}"
            )
        for field in (
            "consumption_tax",
            "other_import_taxes",
            "national_tariff_extension",
            "inspection_before_shipment",
        ):
            result[field] = copy.deepcopy(national_data.get(field))
        result["traceability_sources"].extend(copy.deepcopy(national_data.get("sources", [])))

    if country == "KEN":
        required_documents = _kenya_required_documents(configured["required_document_records"])
    elif country == "COD":
        required_documents = _cod_required_documents(configured["required_document_records"])
    elif national_data is not None:
        required_documents = copy.deepcopy(national_data.get("required_documents", []))
    else:
        required_documents = []

    result["required_documents"] = required_documents
    result["required_documents_are_hs_specific"] = any(
        bool(item.get("hs_level_requirement") or item.get("hs_codes_explicit"))
        for item in required_documents
    )
    result["disclaimer"] = registry["country_disclaimers"][country]
    return result
