"""
Rapport de couverture : état réel des données tarifaires des 54 pays.

Classe chaque pays selon la provenance EFFECTIVE de ses données actuelles dans
data/crawled/*.json (et non selon ce qu'on aimerait avoir). Sert de tableau de
bord honnête : qui a de l'authentique, qui repose sur de l'estimé à re-crawler,
qui n'a rien.
"""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Dict, List, Any

from .manifest import build_manifest, Provenance
from .canonical import NON_AUTHENTIC_QUALITY_TAGS

CRAWLED_DIR = Path(__file__).resolve().parent.parent / "data" / "crawled"


def _extract_positions(doc: Dict[str, Any]) -> List[Dict[str, Any]]:
    return doc.get("sub_positions") or doc.get("positions") or doc.get("tariff_lines") or []


def classify_file(iso3: str) -> Dict[str, Any]:
    """Classe le fichier data/crawled/{ISO3}_tariffs.json par provenance effective."""
    path = CRAWLED_DIR / f"{iso3}_tariffs.json"
    result: Dict[str, Any] = {
        "iso3": iso3,
        "file_exists": path.exists(),
        "positions": 0,
        "effective_provenance": Provenance.NONE.value,
        "source": None,
    }
    if not path.exists():
        return result

    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:  # fichier corrompu
        result["error"] = str(e)
        return result

    positions = _extract_positions(doc)
    result["positions"] = len(positions)
    result["source"] = doc.get("source")
    file_quality = doc.get("source_quality")

    if not positions:
        result["effective_provenance"] = Provenance.NONE.value
        return result

    # Provenance déclarée au niveau position (échantillon raisonnable).
    pos_quals = Counter(
        (p.get("source_quality") or p.get("quality")) for p in positions
    )
    estimated_count = sum(pos_quals.get(t, 0) for t in NON_AUTHENTIC_QUALITY_TAGS)

    authentic_pos = sum(
        pos_quals.get(t, 0) for t in ("crawled_authentic", "authentic_national")
    )

    if (
        file_quality in (Provenance.NATIONAL_CRAWL.value, "crawled_authentic", "authentic_national")
        or iso3 in ("DZA", "EGY", "MAR", "TUN")
        or authentic_pos > 0
    ):
        # Crawl national authentique (éventuellement encore mêlé de positions
        # estimées à purger — surfacé via estimated_positions).
        prov = Provenance.NATIONAL_CRAWL.value
    elif estimated_count > 0 and estimated_count >= len(positions) * 0.5:
        prov = Provenance.ESTIMATED.value
    else:
        # Source régionale (TEC/CET/SACU) sans tag estimé majoritaire.
        prov = Provenance.REGIONAL_CET.value

    result["effective_provenance"] = prov
    result["estimated_positions"] = estimated_count
    if prov == Provenance.NATIONAL_CRAWL.value and estimated_count > 0:
        result["contaminated"] = True
    return result


def build_coverage_report() -> Dict[str, Any]:
    """Rapport global : provenance effective des 54 pays + synthèse."""
    manifest = build_manifest()
    countries: List[Dict[str, Any]] = []
    for iso3 in sorted(manifest.keys()):
        cls = classify_file(iso3)
        cls["name_fr"] = manifest[iso3]["name_fr"]
        cls["target_primary"] = manifest[iso3]["primary_provenance"]
        cls["regional_tariff"] = manifest[iso3]["regional_tariff"]
        countries.append(cls)

    summary = Counter(c["effective_provenance"] for c in countries)
    authentic = sum(
        1 for c in countries
        if c["effective_provenance"] in (
            Provenance.NATIONAL_CRAWL.value, Provenance.REGIONAL_CET.value, Provenance.WTO_MFN_HS6.value
        )
    )
    return {
        "total_countries": len(countries),
        "authentic_countries": authentic,
        "needs_recrawl": summary.get(Provenance.ESTIMATED.value, 0),
        "no_data": summary.get(Provenance.NONE.value, 0),
        "by_provenance": dict(summary),
        "countries": countries,
    }


def format_report(report: Dict[str, Any]) -> str:
    """Rend le rapport en tableau texte lisible."""
    lines = []
    header = f"{'ISO':<5}{'PAYS':<22}{'POSITIONS':>10}{'PROVENANCE EFFECTIVE':>24}"
    lines.append(header)
    lines.append("-" * len(header))
    for c in report["countries"]:
        lines.append(
            f"{c['iso3']:<5}{(c['name_fr'] or '')[:21]:<22}"
            f"{c['positions']:>10}{c['effective_provenance']:>24}"
        )
    lines.append("-" * len(header))
    lines.append(
        f"Total: {report['total_countries']} | authentiques: {report['authentic_countries']} | "
        f"à re-crawler (estimé): {report['needs_recrawl']} | sans données: {report['no_data']}"
    )
    lines.append(f"Par provenance: {report['by_provenance']}")
    return "\n".join(lines)
