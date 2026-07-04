"""
Gate qualité (docs/PLAN_SCRAPLING_CRAWLERS.md §5) — verdict PASS/FAIL.

Étalon Algérie : un candidat DZA doit reproduire le dataset crawlé authentique
existant (couverture ≥ 99,5 %, 0 divergence de taxes, 0 avantage perdu) et les
12 pivots CSV (taux + concordance formalités/avantages). Le même gate sert
ensuite à chaque pays (pivots dédiés).

CLI :
    python -m crawlers.scrapling_engine.quality_gate \
        --candidate data/crawled/DZA_tariffs.json \
        --reference data/crawled/DZA_tariffs.json \
        --pivots frontend/public/DZA_tarif_douanier_echantillon.csv
Sortie : rapport JSON sur stdout ; code retour 0 = PASS, 1 = FAIL.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Dict, List, Optional

from crawlers.scrapling_engine.normalizer import _fold

COVERAGE_THRESHOLD = 0.995
PARSING_THRESHOLD = 0.90  # part des formalités/avantages structurés (le reste : raw)

PIVOT_TAX_COLUMNS = {
    "Droit_de_Douane_DD_pct": "DD",
    "TVA_pct": "TVA",
    "TCS_pct": "TCS",
    "PRCT_pct": "PRCT",
    "DAPS_pct": "DAPS",
}


def _index(dataset: Dict) -> Dict[str, Dict]:
    return {p["hs_code"]: p for p in dataset.get("sub_positions", []) if p.get("hs_code")}


def _tax_rate(position: Dict, code: str) -> Optional[float]:
    tax = (position.get("taxes") or {}).get(code)
    if not tax:
        return None
    return tax.get("rate")


def _raw_texts(items: List) -> List[str]:
    out = []
    for it in items or []:
        if isinstance(it, dict):
            out.append(it.get("raw") or it.get("condition_raw") or it.get("condition_fr") or "")
        else:
            out.append(str(it))
    return out


def compare_to_reference(candidate: Dict, reference: Dict) -> Dict:
    """Couverture, divergences de taxes, avantages/formalités perdus."""
    cand, ref = _index(candidate), _index(reference)
    common = set(cand) & set(ref)
    coverage = len(common) / len(ref) if ref else 0.0

    tax_divergences: List[Dict] = []
    lost_advantages = 0
    lost_formalities = 0
    for hs in common:
        c, r = cand[hs], ref[hs]
        for code in set((r.get("taxes") or {}).keys()):
            rc, cc = _tax_rate(r, code), _tax_rate(c, code)
            if rc is not None and cc != rc:
                tax_divergences.append({"hs_code": hs, "tax": code, "ref": rc, "candidate": cc})
        if (r.get("advantages") and not c.get("advantages")) or (
            len(c.get("advantages") or []) < len(r.get("advantages") or [])
        ):
            lost_advantages += 1
        if (r.get("formalities") and not c.get("formalities")) or (
            len(c.get("formalities") or []) < len(r.get("formalities") or [])
        ):
            lost_formalities += 1

    return {
        "reference_positions": len(ref),
        "candidate_positions": len(cand),
        "common_positions": len(common),
        "coverage": round(coverage, 5),
        "coverage_pass": coverage >= COVERAGE_THRESHOLD,
        "tax_divergences": tax_divergences[:50],
        "tax_divergences_count": len(tax_divergences),
        "tax_pass": len(tax_divergences) == 0,
        "lost_advantages": lost_advantages,
        "lost_formalities": lost_formalities,
        "no_loss_pass": lost_advantages == 0 and lost_formalities == 0,
    }


def check_pivots(candidate: Dict, pivots_csv: Path) -> Dict:
    """Valeurs pivot vérifiées : taux exacts + concordance texte des
    formalités/avantages (repli : fragments contenus, sans accents/casse)."""
    cand = _index(candidate)
    rows = list(csv.DictReader(open(pivots_csv, encoding="utf-8-sig"), delimiter=";"))
    failures: List[Dict] = []
    checked = 0
    for row in rows:
        hs = (row.get("Code_SH_10_chiffres") or "").strip()
        if not hs:
            continue
        checked += 1
        pos = cand.get(hs)
        if not pos:
            failures.append({"hs_code": hs, "issue": "position absente"})
            continue
        # Taux
        for col, code in PIVOT_TAX_COLUMNS.items():
            expected = (row.get(col) or "").strip()
            if expected == "":
                continue
            got = _tax_rate(pos, code)
            if got is None or abs(float(expected) - float(got)) > 1e-9:
                failures.append(
                    {"hs_code": hs, "issue": f"taux {code}", "expected": expected, "got": got}
                )
        # Concordance formalités / avantages (fragments séparés par '|')
        for col, field in [
            ("Formalites_particulieres", "formalities"),
            ("Avantages_fiscaux", "advantages"),
        ]:
            expected_raw = (row.get(col) or "").strip()
            if not expected_raw:
                continue
            haystack = _fold(" | ".join(_raw_texts(pos.get(field))))
            for fragment in expected_raw.split("|"):
                if _fold(fragment) and _fold(fragment) not in haystack:
                    failures.append(
                        {"hs_code": hs, "issue": f"{field} manquant", "fragment": fragment.strip()}
                    )
    return {
        "pivots_checked": checked,
        "pivot_failures": failures,
        "pivots_pass": not failures,
    }


def check_parsing_quality(candidate: Dict) -> Dict:
    """Part des formalités avec autorité identifiée et des avantages avec
    régime reconnu (≠ AUTRE) — informationnel + seuil doux (PARSING_THRESHOLD
    sur le fait d'être STRUCTURÉ, pas sur l'exactitude, le raw restant la vérité)."""
    total_f = parsed_f = total_a = parsed_a = 0
    for pos in candidate.get("sub_positions", []):
        for f in pos.get("formalities") or []:
            total_f += 1
            if isinstance(f, dict) and f.get("document"):
                parsed_f += 1
        for a in pos.get("advantages") or []:
            total_a += 1
            if isinstance(a, dict) and a.get("regime"):
                parsed_a += 1
    ratio_f = parsed_f / total_f if total_f else 1.0
    ratio_a = parsed_a / total_a if total_a else 1.0
    return {
        "formalities_structured_ratio": round(ratio_f, 4),
        "advantages_structured_ratio": round(ratio_a, 4),
        "parsing_pass": ratio_f >= PARSING_THRESHOLD and ratio_a >= PARSING_THRESHOLD,
    }


def run_gate(candidate_path: Path, reference_path: Optional[Path], pivots_path: Optional[Path]):
    candidate = json.load(open(candidate_path, encoding="utf-8"))
    report: Dict = {"candidate": str(candidate_path)}

    if reference_path and reference_path.exists():
        reference = json.load(open(reference_path, encoding="utf-8"))
        report["reference_check"] = compare_to_reference(candidate, reference)
    if pivots_path and pivots_path.exists():
        report["pivots_check"] = check_pivots(candidate, pivots_path)
    report["parsing_check"] = check_parsing_quality(candidate)
    report["stats_errors"] = (candidate.get("stats") or {}).get("errors")

    passes = [report["parsing_check"]["parsing_pass"], report.get("stats_errors", 0) == 0]
    ref = report.get("reference_check")
    if ref:
        passes += [ref["coverage_pass"], ref["tax_pass"], ref["no_loss_pass"]]
    piv = report.get("pivots_check")
    if piv:
        passes.append(piv["pivots_pass"])

    report["verdict"] = "PASS" if all(passes) else "FAIL"
    return report


def main() -> int:
    ap = argparse.ArgumentParser(description="Gate qualité des tarifs crawlés")
    ap.add_argument("--candidate", required=True, type=Path)
    ap.add_argument("--reference", type=Path, default=None)
    ap.add_argument("--pivots", type=Path, default=None)
    args = ap.parse_args()
    report = run_gate(args.candidate, args.reference, args.pivots)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["verdict"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
