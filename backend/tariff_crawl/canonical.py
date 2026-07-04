"""
Schéma canonique de sortie + validateur d'authenticité.

Tout crawl, quelle que soit sa source, est normalisé vers UN schéma canonique
unique, écrit dans data/crawled/{ISO3}_tariffs.json et lu par
`services/crawled_data_service.py`.

Le validateur applique le principe directeur : **authentique uniquement,
sourcé et traçable**. Il REJETTE les fichiers vides, sans source, sans URL
de source vérifiable, ou contenant des positions estimées (etl_computed /
synthétiques). Un fichier qui ne passe pas la validation ne doit pas être
servi à l'utilisateur.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple

from .manifest import AUTHENTIC_PROVENANCES, Provenance

# Marqueurs de données NON authentiques à rejeter explicitement.
NON_AUTHENTIC_QUALITY_TAGS = frozenset(
    {
        "etl_computed",
        "estimated",
        "synthetic",
        "generated",
        "chapter_replicated",
    }
)

# Synonymes employés par les crawlers réels → provenance canonique.
PROVENANCE_SYNONYMS = {
    "crawled_authentic": Provenance.NATIONAL_CRAWL.value,
    "authentic_national": Provenance.NATIONAL_CRAWL.value,
    "national": Provenance.NATIONAL_CRAWL.value,
    "regional_cet": Provenance.REGIONAL_CET.value,
    "cet": Provenance.REGIONAL_CET.value,
    "wto_mfn": Provenance.WTO_MFN_HS6.value,
}


def _canonical_provenance(value: str | None) -> str | None:
    """Ramène un tag de provenance (éventuel synonyme) à la valeur canonique."""
    if value in AUTHENTIC_PROVENANCES:
        return value
    return PROVENANCE_SYNONYMS.get(value)


SCHEMA_VERSION = "tariff_crawl/1.0"


def normalize_position(raw: Dict[str, Any], *, source: str) -> Dict[str, Any]:
    """Normalise une position brute vers le schéma de position canonique.

    Position canonique :
        code_raw, code_clean, designation, chapter,
        taxes: [{code, name, rate_pct, raw_value, source}],
        formalities: [str|dict], fiscal_advantages: [...],
        source
    """
    code_raw = str(raw.get("code_raw") or raw.get("code") or raw.get("hs_code") or "").strip()
    code_clean = (raw.get("code_clean") or code_raw).replace(".", "").replace(" ", "")

    taxes_in = raw.get("taxes", [])
    taxes: List[Dict[str, Any]] = []
    if isinstance(taxes_in, dict):
        # forme {label: "10 %"} ou {code: {name, rate, raw}}
        for key, val in taxes_in.items():
            if isinstance(val, dict):
                taxes.append(
                    {
                        "code": val.get("code", key),
                        "name": val.get("name", key),
                        "rate_pct": val.get("rate", val.get("rate_pct")),
                        "raw_value": val.get("raw", val.get("raw_value", "")),
                        "source": val.get("source", source),
                    }
                )
            else:
                taxes.append(
                    {
                        "code": key,
                        "name": key,
                        "rate_pct": _parse_pct(val),
                        "raw_value": str(val),
                        "source": source,
                    }
                )
    elif isinstance(taxes_in, list):
        for t in taxes_in:
            taxes.append(
                {
                    "code": t.get("code", ""),
                    "name": t.get("name", t.get("code", "")),
                    "rate_pct": t.get("rate_pct", t.get("rate")),
                    "raw_value": t.get("raw_value", ""),
                    "source": t.get("source", source),
                }
            )

    return {
        "code_raw": code_raw,
        "code_clean": code_clean,
        "designation": raw.get("designation") or raw.get("description") or raw.get("name", ""),
        "chapter": raw.get("chapter") or (code_clean[:2] if len(code_clean) >= 2 else ""),
        "taxes": taxes,
        "formalities": raw.get("formalities", raw.get("administrative_formalities", [])),
        "fiscal_advantages": raw.get("fiscal_advantages", []),
        "source": source,
    }


def _parse_pct(value: Any) -> Any:
    if value is None:
        return None
    s = str(value).replace("%", "").replace(",", ".").strip()
    try:
        return float(s)
    except ValueError:
        return None


def build_file(
    iso3: str,
    country_name: str,
    provenance: str,
    source: str,
    source_url: str,
    positions: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Assemble le document canonique pour un pays."""
    norm = [normalize_position(p, source=source) for p in positions]
    return {
        "schema_version": SCHEMA_VERSION,
        "country_code": iso3.upper(),
        "country_name": country_name,
        "source": source,
        "source_url": source_url,
        "source_quality": provenance,
        "crawled_at": datetime.now(timezone.utc).isoformat(),
        "stats": {"sub_positions": len(norm)},
        "sub_positions": norm,
    }


def validate_authenticity(doc: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """Vérifie qu'un document est authentique et servable.

    Retourne (ok, issues). ok=False si une règle d'authenticité est violée.
    """
    issues: List[str] = []

    positions = doc.get("sub_positions") or doc.get("positions") or doc.get("tariff_lines") or []

    # Provenance au niveau fichier, sinon inférée des positions (crawlers réels
    # qui ne taguent qu'au niveau position, ex. DZA: 'crawled_authentic').
    provenance = _canonical_provenance(doc.get("source_quality"))
    if provenance is None and positions:
        pos_tags = {p.get("source_quality") or p.get("quality") for p in positions}
        canon = {_canonical_provenance(t) for t in pos_tags} - {None}
        non_auth = pos_tags & NON_AUTHENTIC_QUALITY_TAGS
        if canon and not non_auth:
            provenance = sorted(canon)[0]
    if provenance not in AUTHENTIC_PROVENANCES:
        issues.append(
            f"provenance non authentique ou absente: {doc.get('source_quality')!r} "
            f"(attendu l'un de {sorted(AUTHENTIC_PROVENANCES)} ou synonyme reconnu)"
        )

    # L'attribution 'source' et une URL vérifiable sont obligatoires : la
    # priorité absolue est de pouvoir revenir à la base officielle plutôt que
    # de propager des approximations ou hallucinations héritées.
    if not doc.get("source"):
        issues.append("champ 'source' manquant")
    if not doc.get("source_url"):
        issues.append("champ 'source_url' manquant — source officielle vérifiable obligatoire")

    if not positions:
        issues.append("aucune position tarifaire (fichier vide)")

    # Rejet des positions estimées / synthétiques.
    estimated = 0
    no_code = 0
    no_tax = 0
    for p in positions:
        q = p.get("source_quality") or p.get("quality")
        if q in NON_AUTHENTIC_QUALITY_TAGS:
            estimated += 1
        if not (p.get("code_clean") or p.get("code") or p.get("hs_code")):
            no_code += 1
        # Les crawlers réels emploient des noms de champ variés pour les taxes
        # (taxes / taxes_detail / taxes_import). On considère qu'une position
        # porte une taxe dès que l'un d'eux est non vide.
        has_tax = any(
            bool(p.get(field)) and isinstance(p.get(field), (list, dict))
            for field in ("taxes", "taxes_detail", "taxes_import")
        )
        if not has_tax:
            no_tax += 1

    if estimated:
        issues.append(f"{estimated} position(s) marquée(s) estimée(s)/synthétique(s) — interdit")
    if positions and no_code == len(positions):
        issues.append("aucune position n'a de code HS exploitable")
    if positions and no_tax == len(positions):
        issues.append("aucune position ne porte de taxe — données vides")

    return (len(issues) == 0), issues
