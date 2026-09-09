"""Reviewable product-to-HS mapping for descriptions found in legal gazettes.

The mapper receives the SaaS tariff search function as a dependency.  It does
not build or persist a competing nomenclature index, and an index hit alone is
never treated as the legal basis for classification.
"""

import re
import unicodedata
from enum import Enum
from typing import Callable, Dict, Iterable, List, Optional

from pydantic import BaseModel, Field


class ClassificationStatus(str, Enum):
    EXACT_INDEX_MATCH = "EXACT_INDEX_MATCH"
    VALIDATED_HS6 = "VALIDATED_HS6"
    MULTIPLE_HS_CANDIDATES = "MULTIPLE_HS_CANDIDATES"
    CONTEXT_DEPENDENT = "CONTEXT_DEPENDENT"
    END_USE_MEASURE = "END_USE_MEASURE"
    HUMAN_REVIEW_REQUIRED = "HUMAN_REVIEW_REQUIRED"
    UNMAPPED = "UNMAPPED"


class GazetteProductMapping(BaseModel):
    mapping_id: str
    measure_id: str
    gazette_product_text: str
    normalized_product_name: str
    material: Optional[str] = None
    function: Optional[str] = None
    use: Optional[str] = None
    presentation: Optional[str] = None
    sector: Optional[str] = None
    beneficiary: Optional[str] = None
    special_destination: Optional[str] = None
    technical_condition: Optional[str] = None
    exclusions: List[str] = Field(default_factory=list)
    unit: Optional[str] = None
    gazette_reference: str
    index_terms_used: List[str] = Field(default_factory=list)
    wco_index_matches: List[Dict] = Field(default_factory=list)
    hs_version: str = "HS2022"
    hs4_candidates: List[str] = Field(default_factory=list)
    hs6_candidates: List[str] = Field(default_factory=list)
    selected_hs6: Optional[str] = None
    classification_status: ClassificationStatus
    confidence_score: int = Field(ge=0, le=100)
    classification_reasoning: str
    section_notes_checked: List[str] = Field(default_factory=list)
    chapter_notes_checked: List[str] = Field(default_factory=list)
    legal_conditions: List[str] = Field(default_factory=list)
    requires_human_review: bool = True
    reviewer: Optional[str] = None
    reviewed_at: Optional[str] = None
    source_id: str
    effective_from: str
    effective_to: Optional[str] = None

    def is_automatic(self, target_hs_version: str) -> bool:
        return (
            self.confidence_score >= 90
            and self.selected_hs6 is not None
            and len(self.hs6_candidates) == 1
            and self.classification_status
            in {ClassificationStatus.EXACT_INDEX_MATCH, ClassificationStatus.VALIDATED_HS6}
            and not self.requires_human_review
            and self.hs_version == target_hs_version
            and bool(self.section_notes_checked or self.chapter_notes_checked)
        )


def normalize_term(value: str) -> str:
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()
    value = re.sub(r"[^a-zA-Z0-9]+", " ", value.lower())
    words = [word[:-1] if len(word) > 4 and word.endswith("s") else word for word in value.split()]
    return " ".join(words)


class ExistingTariffIndexMapper:
    """Adapter around the existing SaaS search service."""

    def __init__(self, search: Callable[..., Iterable[Dict]], country: str = "KEN"):
        self.search = search
        self.country = country

    def candidates(self, terms: Iterable[str], limit: int = 20) -> List[Dict]:
        found = {}
        for term in dict.fromkeys(t for t in terms if t):
            for row in self.search(self.country, term, language="en", limit=limit) or []:
                hs6 = re.sub(r"\D", "", str(row.get("hs6", "")))[:6]
                if len(hs6) == 6:
                    found.setdefault(hs6, row)
        return list(found.values())


class WCOIndexCandidateMapper:
    """Inject the canonical WCO adapter without importing backend from engine.

    An END_USE measure is searched only when the caller supplies detailed goods
    from an official authorization or annex.  The broad industrial-use wording
    is never used as a classification shortcut.
    """

    def __init__(self, search_wco_index: Callable[..., Dict]):
        self.search_wco_index = search_wco_index

    def enrich(
        self,
        mapping: GazetteProductMapping,
        *,
        detailed_goods: Optional[Iterable[str]] = None,
        language: Optional[str] = None,
        limit: int = 20,
    ) -> GazetteProductMapping:
        terms = list(dict.fromkeys(t.strip() for t in (detailed_goods or []) if t.strip()))
        if mapping.classification_status != ClassificationStatus.END_USE_MEASURE and not terms:
            terms = [mapping.normalized_product_name]
        if not terms:
            return mapping.model_copy(
                update={
                    "classification_reasoning": (
                        mapping.classification_reasoning
                        + " No WCO search was run: detailed authorized goods are required "
                        "for an END_USE measure."
                    ),
                    "requires_human_review": True,
                    "selected_hs6": None,
                }
            )

        matches: List[Dict] = []
        hs4 = set(mapping.hs4_candidates)
        hs6 = set(mapping.hs6_candidates)
        for term in terms:
            result = self.search_wco_index(
                term,
                hs_version=mapping.hs_version,
                language=language,
                limit=limit,
            )
            for match in result.get("matches", []):
                matches.append(match)
                for candidate in match.get("candidate_positions", []):
                    code = re.sub(r"\D", "", str(candidate.get("code", "")))
                    if len(code) == 4:
                        hs4.add(code)
                    elif len(code) == 6:
                        hs6.add(code)

        candidate_count = len(hs4) + len(hs6)
        confidence = 0 if not matches else (70 if candidate_count == 1 else 45)
        status = mapping.classification_status
        if status != ClassificationStatus.END_USE_MEASURE:
            status = (
                ClassificationStatus.MULTIPLE_HS_CANDIDATES
                if candidate_count > 1
                else ClassificationStatus.HUMAN_REVIEW_REQUIRED
            )
        return mapping.model_copy(
            update={
                "index_terms_used": terms,
                "wco_index_matches": matches,
                "hs4_candidates": sorted(hs4),
                "hs6_candidates": sorted(hs6),
                "selected_hs6": None,
                "classification_status": status,
                "confidence_score": confidence,
                "requires_human_review": True,
                "classification_reasoning": (
                    mapping.classification_reasoning
                    + " WCO alphabetical-index hits are candidates only; legal notes and "
                    "the detailed authorization remain to be reviewed."
                ),
            }
        )


def automatic_overlay_hs6(mapping: GazetteProductMapping, target_hs_version="HS2022"):
    """Return a usable HS6 only when every automatic-classification gate passes."""
    return mapping.selected_hs6 if mapping.is_automatic(target_hs_version) else None
