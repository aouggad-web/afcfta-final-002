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
import re
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


def _pct(raw: Optional[str]) -> Optional[float]:
    """'2.5 %' / '2,5%' / '15' -> 2.5 / 2.5 / 15.0 (float) ; None/'' -> None."""
    if raw is None:
        return None
    raw = raw.strip()
    if not raw:
        return None
    m = re.search(r"(\d+(?:[.,]\d+)?)", raw)
    return float(m.group(1).replace(",", ".")) if m else None


# Schéma pivot par pays : nom de colonne HS + colonnes de taux -> code, colonnes
# formalités/avantages. DZA reste le schéma historique (colonnes déjà en %
# numérique). Un pays sans entrée ici (ex. TUN : export en texte libre
# pipe-délimité, correspondance code<->libellé live NON confirmée) est
# simplement ignoré par check_pivots — jamais de correspondance devinée.
PIVOT_SCHEMAS: Dict[str, Dict] = {
    "DZA": {
        "hs_column": "Code_SH_10_chiffres",
        "tax_columns": PIVOT_TAX_COLUMNS,
        "parse_rate": lambda raw: float(raw.strip()) if raw and raw.strip() else None,
        "text_columns": {
            "Formalites_particulieres": "formalities",
            "Avantages_fiscaux": "advantages",
        },
    },
    "MAR": {
        "hs_column": "Code_Position_10_chiffres",
        "tax_columns": {
            "Droit_Importation_DI": "DI",
            "Taxe_Parafiscale_Importation_TPI": "TPI",
            "Taxe_Valeur_Ajoutee_TVA": "TVA",
            "Taxe_Interieure_Consommation_TIC": "TIC",
        },
        "parse_rate": _pct,
        "text_columns": {"Formalites_particulieres": "formalities"},
    },
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


def _candidate_chapters(candidate: Dict) -> set:
    return {
        (p.get("chapter") or (p.get("hs_code") or "")[:2])
        for p in candidate.get("sub_positions", [])
        if p.get("chapter") or p.get("hs_code")
    }


def compare_to_reference(candidate: Dict, reference: Dict, scope_to_candidate: bool = True) -> Dict:
    """Couverture, divergences de taxes, avantages/formalités perdus.

    ``scope_to_candidate`` (défaut) : restreint l'étalon aux CHAPITRES présents
    dans le candidat — indispensable pour valider un crawl PAR TRANCHES (ex.
    chapitre 01 seul) sans le comparer aux 17 061 positions complètes.
    """
    cand, ref_full = _index(candidate), _index(reference)
    chapters = _candidate_chapters(candidate) if scope_to_candidate else None
    if chapters:
        ref = {hs: p for hs, p in ref_full.items() if (p.get("chapter") or hs[:2]) in chapters}
    else:
        ref = ref_full
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
        "scoped_to_chapters": sorted(chapters) if chapters else "all",
        "reference_positions": len(ref),
        "reference_positions_full": len(ref_full),
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


def check_pivots(candidate: Dict, pivots_csv: Path, scope_to_candidate: bool = True) -> Dict:
    """Valeurs pivot vérifiées : taux exacts + concordance texte des
    formalités/avantages (repli : fragments contenus, sans accents/casse).

    ``scope_to_candidate`` : ne vérifie que les pivots dont le chapitre est
    présent dans le candidat (crawl par tranches → pas de faux « absent »).
    """
    country = (candidate.get("country") or "DZA").upper()
    schema = PIVOT_SCHEMAS.get(country)
    if not schema:
        return {
            "pivots_checked": 0,
            "pivots_skipped_out_of_scope": 0,
            "pivot_failures": [],
            # Aucun schéma pivot défini pour ce pays -> non-applicable (non-bloquant).
            "pivots_pass": True,
            "pivots_applicable": False,
        }
    hs_column = schema["hs_column"]
    tax_columns = schema["tax_columns"]
    parse_rate = schema["parse_rate"]
    text_columns = schema["text_columns"]

    cand = _index(candidate)
    chapters = _candidate_chapters(candidate) if scope_to_candidate else None
    rows = list(csv.DictReader(open(pivots_csv, encoding="utf-8-sig"), delimiter=";"))
    failures: List[Dict] = []
    checked = 0
    skipped_out_of_scope = 0
    for row in rows:
        hs = (row.get(hs_column) or "").strip()
        if not hs:
            continue
        if chapters is not None and hs[:2] not in chapters:
            skipped_out_of_scope += 1
            continue
        checked += 1
        pos = cand.get(hs)
        if not pos:
            failures.append({"hs_code": hs, "issue": "position absente"})
            continue
        # Taux
        for col, code in tax_columns.items():
            expected = parse_rate(row.get(col))
            if expected is None:
                continue
            got = _tax_rate(pos, code)
            if got is None or abs(expected - float(got)) > 1e-9:
                failures.append(
                    {"hs_code": hs, "issue": f"taux {code}", "expected": expected, "got": got}
                )
        # Concordance formalités / avantages (fragments séparés par '|')
        for col, field in text_columns.items():
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
        "pivots_skipped_out_of_scope": skipped_out_of_scope,
        "pivot_failures": failures,
        # Aucun pivot dans le périmètre crawlé -> non-bloquant (pas d'info).
        "pivots_pass": not failures and checked > 0,
        "pivots_applicable": checked > 0,
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


def check_national_layer(candidate: Dict) -> Dict:
    """Couche NATIONALE présente ? (docs/PLAN_SCRAPLING_CRAWLERS.md §7)

    Un tarif régional (TEC/CET) n'apporte que le DD. Un fichier pays doit aussi
    porter les taxes nationales (au-delà du DD), les formalités et/ou les
    régimes. On mesure la part de positions qui en portent — sert à refuser un
    fichier qui ne serait qu'un copier-coller du tarif régional."""
    positions = candidate.get("sub_positions", [])
    total = len(positions)
    beyond_dd = with_formalities = with_advantages = 0
    for pos in positions:
        taxes = set((pos.get("taxes") or {}).keys())
        if taxes - {"DD"}:
            beyond_dd += 1
        if pos.get("formalities"):
            with_formalities += 1
        if pos.get("advantages"):
            with_advantages += 1
    share_beyond_dd = beyond_dd / total if total else 0.0
    present = beyond_dd > 0 or with_formalities > 0 or with_advantages > 0
    return {
        "positions": total,
        "positions_with_tax_beyond_dd": beyond_dd,
        "share_tax_beyond_dd": round(share_beyond_dd, 4),
        "positions_with_formalities": with_formalities,
        "positions_with_advantages": with_advantages,
        # Présence = au moins une couche nationale observée (taxes hors DD,
        # formalités ou régimes). Un fichier « DD seul » -> present False.
        "national_layer_present": present,
    }


def run_gate(
    candidate_path: Path,
    reference_path: Optional[Path],
    pivots_path: Optional[Path],
    scope_to_candidate: bool = True,
    require_national_layer: bool = False,
):
    candidate = json.load(open(candidate_path, encoding="utf-8"))
    report: Dict = {
        "candidate": str(candidate_path),
        "scope_to_candidate": scope_to_candidate,
    }

    if reference_path and reference_path.exists():
        reference = json.load(open(reference_path, encoding="utf-8"))
        report["reference_check"] = compare_to_reference(candidate, reference, scope_to_candidate)
    if pivots_path and pivots_path.exists():
        report["pivots_check"] = check_pivots(candidate, pivots_path, scope_to_candidate)
    report["parsing_check"] = check_parsing_quality(candidate)
    report["national_layer_check"] = check_national_layer(candidate)
    report["stats_errors"] = (candidate.get("stats") or {}).get("errors")

    passes = [report["parsing_check"]["parsing_pass"], report.get("stats_errors", 0) == 0]
    ref = report.get("reference_check")
    if ref:
        passes += [ref["coverage_pass"], ref["tax_pass"], ref["no_loss_pass"]]
    piv = report.get("pivots_check")
    if piv and piv.get("pivots_applicable"):
        passes.append(piv["pivots_pass"])
    # Pays d'un bloc régional : refuser un fichier « DD régional seul » sans
    # couche nationale (taxes hors DD / formalités / régimes).
    if require_national_layer:
        passes.append(report["national_layer_check"]["national_layer_present"])

    report["verdict"] = "PASS" if all(passes) else "FAIL"
    return report


def main() -> int:
    ap = argparse.ArgumentParser(description="Gate qualité des tarifs crawlés")
    ap.add_argument("--candidate", required=True, type=Path)
    ap.add_argument("--reference", type=Path, default=None)
    ap.add_argument("--pivots", type=Path, default=None)
    ap.add_argument(
        "--no-scope",
        action="store_true",
        help="Comparer au dataset complet (pas seulement aux chapitres crawlés)",
    )
    ap.add_argument(
        "--require-national-layer",
        action="store_true",
        help="Échouer si le fichier n'a pas de couche nationale (taxes hors DD / "
        "formalités / régimes) — pour les pays d'un bloc régional (TEC/CET).",
    )
    args = ap.parse_args()
    report = run_gate(
        args.candidate,
        args.reference,
        args.pivots,
        scope_to_candidate=not args.no_scope,
        require_national_layer=args.require_national_layer,
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["verdict"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
