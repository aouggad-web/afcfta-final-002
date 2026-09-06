#!/usr/bin/env python3
"""Corrections Integrity Watch / Codex CMR (PR #451).

1. préférence ZLECAf : DOCUMENTED → PARTIAL (membre GTI + offre CEMAC
   archivée dans l'e-Tariff Book — 5 284 codes 8 chiffres, OFFER_ONLY) ;
2. contre-vérification NPF documentée : 4 379 codes communs, 4 336 MFN
   identiques, 43 divergences non arbitrées (version de tarif différente) ;
3. énumération : 860 codes nationaux hors snapshot + 905 snapshot hors
   national — écarts de version documentés, non arbitrés ;
4. formalités : legal_text_verified=false + confidence ≤70 ;
5. cascade CEMAC documentée (DD → RI 0,45% → TCI 1% → TVA 17,5/19,25% → DA) ;
6. devise XAF + principe SH6 (CEMAC 8 chiffres — vérifié contre le snapshot
   e-Tariff CEMAC : 5 284 codes, tous à 8 chiffres, pas de lignes nationales
   10 chiffres dans la source en vigueur).

Usage : backend/.venv311/bin/python backend/scripts/fix_cmr_integrity_watch.py
"""
from __future__ import annotations

import gzip
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REGISTER = ROOT / "data" / "cameroon" / "cmr_gazette_register.json"
OVERRIDES = ROOT / "data" / "cameroon" / "legal_overrides.json"
CONFIG = ROOT / "data" / "cameroon" / "jurisdiction_config.json"
CANON = ROOT / "backend" / "data" / "CMR_tariffs.json"
OFFER = ROOT / "backend" / "data" / "official_preferential" / "CEMAC_afcfta_etariff_2026-08-17.json.gz"


def main() -> int:
    # ── contre-vérification NPF (documentée dans le registre) ──
    can = json.loads(CANON.read_text(encoding="utf-8"))
    sps = {sp["code"]: sp for l in can["tariff_lines"] for sp in (l.get("sub_positions") or [])}
    d = json.load(gzip.open(OFFER))
    snap = {str(r["hs_code"]): r for r in d["schedules"]["1"]}
    inter = set(sps) & set(snap)
    match = mismatch = 0
    examples = []
    for c in sorted(inter):
        dd = sps[c].get("dd")
        mfn = snap[c].get("mfn_rate_expression")
        try:
            mfn_v = float(mfn)
        except (TypeError, ValueError):
            mfn_v = None
        if dd is None or mfn_v is None:
            continue
        if abs(dd - mfn_v) < 0.01:
            match += 1
        else:
            mismatch += 1
            if len(examples) < 6:
                examples.append({"code": c, "national_dd": dd, "snapshot_mfn": mfn})

    # ── registre ──
    reg = json.loads(REGISTER.read_text(encoding="utf-8"))
    reg["preference_and_origin_status"] = "PARTIAL"
    reg["preference_evidence"] = {
        "instrument": (
            "ZLECAf — offre CEMAC publiée dans l'e-Tariff Book du Secrétariat "
            "(5 284 codes 8 chiffres, OFFER_ONLY, 2 périodes)"
        ),
        "status": "PARTIAL",
        "note": (
            "membre du Guided Trade Initiative (application effective démontrée "
            "par le Secrétariat depuis le 07/10/2022) — l'offre ligne à ligne "
            "n'est PAS exécutable sans instrument d'implémentation + origine "
            "vérifiée (porte zlecaf_implementation_registry)"
        ),
    }
    reg["afcfta_application_evidence"] = {
        "gti_participant": True,
        "gti_launch": "2022-10-07",
        "source_url": "https://au-afcfta.org/guided-trade-initiative/",
        "offer_published": "e-Tariff Book CEMAC (snapshot archivé 2026-08-17)",
        "npf_crosscheck": {
            "codes_comparés": len(inter),
            "npf_matches": match,
            "npf_mismatches": mismatch,
            "mismatch_examples": examples,
            "note": (
                "divergences non arbitrées — version du tarif CEMAC différente "
                "entre le snapshot e-Tariff (soumission) et le tarif DGD en "
                "vigueur (national) ; à arbitrer sur textes officiels"
            ),
        },
        "enumeration_gaps": {
            "national_hors_snapshot": len(set(sps) - set(snap)),
            "snapshot_hors_national": len(set(snap) - set(sps)),
            "note": "écarts de version documentés, non arbitrés",
        },
        "algeria_reciprocity": {
            "instrument": "Circulaire n° 482/DGD/SP/D.042/24 du 22 octobre 2024 (DGD Algérie)",
            "source_id": "DZA-DGD-CIRC-482-2024",
            "sha256": "483e8d2cf6f8769eb7d3bbfc9dda1a3df2132b6fe504bbd554f7bab1c80bdc99",
            "note": (
                "l'Algérie applique la ZLECAf à l'importation (17 322 lignes "
                "classées A/B/C, calendriers standard et réciprocité)"
            ),
        },
    }
    reg["coverage_scope"] = {
        "base_tariff": (
            "VERIFIED vs source DGD — 5 239 SPs nationales 8 chiffres (CEMAC) ; "
            "écarts d'énumération avec le snapshot e-Tariff documentés"
        ),
        "national_layer": (
            "PARTIAL — RI/TCI câblés, TVA 17,5% (CGI art. 142, primaire) vs "
            "19,25% runtime à arbitrer ; DA (accises CEMAC) par ligne à documenter"
        ),
    }
    reg["currency_note"] = (
        "customs_value attendu dans la devise de la juridiction (XAF) : toute "
        "valeur USD doit être convertie avant l'appel — les montants calculés "
        "sont étiquetés XAF"
    )
    reg["integrity_watch_fixes"] = {
        "as_of": "2026-09-06",
        "preference_downgraded_to_partial": True,
        "npf_crosscheck_documented": True,
        "enumeration_gaps_documented": True,
        "formalities_downgraded": True,
        "currency_expectation_documented": True,
    }
    REGISTER.write_text(json.dumps(reg, ensure_ascii=False, indent=1), encoding="utf-8")

    # ── formalités : dégradation ──
    if OVERRIDES.is_file():
        ov = json.loads(OVERRIDES.read_text(encoding="utf-8"))
        for m in ov.get("measures", []):
            m["mapping_confidence"] = min(m.get("mapping_confidence", 100), 70)
            m["legal_text_verified"] = False
            m["provenance_quality"] = (
                "DERIVED_FROM_REGIONAL_SCHEME — à confirmer par les textes "
                "camerounais (PECAE, instructions douanières)"
            )
        ov["provenance"]["integrity_watch"] = (
            "formalités dégradées (legal_text_verified=false) — à confirmer par "
            "les textes camerounais"
        )
        OVERRIDES.write_text(json.dumps(ov, ensure_ascii=False, indent=1), encoding="utf-8")

    # ── config : principe SH6 ──
    cfg = json.loads(CONFIG.read_text(encoding="utf-8"))
    cfg["sh6_principle"] = (
        "les 6 premiers chiffres (SH) sont internationaux ; le tarif CEMAC "
        "commun se développe sur 8 chiffres (SH6+2) — vérifié contre le "
        "snapshot e-Tariff CEMAC (5 284 codes, tous à 8 chiffres) ; le tarif "
        "national authentique (DGD Cameroun) est la source unique"
    )
    CONFIG.write_text(json.dumps(cfg, ensure_ascii=False, indent=1), encoding="utf-8")

    print(f"CMR integrity watch : préférence PARTIAL (GTI + offre CEMAC), NPF "
          f"{match}/{match + mismatch} documenté, écarts d'énumération documentés, "
          "formalités dégradées, devise XAF, principe SH6")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
