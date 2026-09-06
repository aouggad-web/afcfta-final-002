#!/usr/bin/env python3
"""Corrections Integrity Watch / Codex MUS (PR #453) — huit fils de revue.

1. excise : assiette alignée sur le moteur (ad valorem appliqué sur CIF + DD) ;
2. excise : NE PAS antidater — la source est explicitement le tarif MRA
   (schedule avril 2026) → effective_from = 2026-04-01 (plus 2017-07-01) ;
3. préférence ZLECAf : DOCUMENTED → PARTIAL (membre GTI — application
   effective démontrée par le Secrétariat ; aucune offre ligne à ligne
   archivée pour MUS) + réciprocité algérienne (circulaire 482/2024) ;
4. couverture scannée : base tarifaire VERIFIED / couche nationale PARTIAL
   (prélèvements omis non modélisés) ;
5. formalités synthétiques : legal_text_verified=false + confidence <100
   (aucune mesure ici — no-op si vide) ;
6. devise : customs_value attendu en MUR (conversion avant appel) ;
7. vat_exemptions : préservées si présentes (builder non destructif) ;
8. principe SH6 documenté dans la config.

Usage : backend/.venv311/bin/python backend/scripts/fix_mus_integrity_watch.py
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EXCISE = ROOT / "data" / "mauritius" / "excise_measures.json"
REGISTER = ROOT / "data" / "mauritius" / "mus_gazette_register.json"
OVERRIDES = ROOT / "data" / "mauritius" / "legal_overrides.json"
CONFIG = ROOT / "data" / "mauritius" / "jurisdiction_config.json"

GTI_EVIDENCE = {
    "gti_participant": True,
    "gti_launch": "2022-10-07",
    "source_url": "https://au-afcfta.org/guided-trade-initiative/",
    "source_title": "AfCFTA Secretariat — Guided Trade Initiative (GTI)",
    "note": (
        "l'application effective des préférences ZLECAf par les douanes "
        "mauriciennes est démontrée par le Secrétariat (GTI) — la portée "
        "ligne à ligne reste contrôlée par zlecaf_implementation_registry.py"
    ),
    "algeria_reciprocity": {
        "instrument": "Circulaire n° 482/DGD/SP/D.042/24 du 22 octobre 2024 (DGD Algérie)",
        "source_id": "DZA-DGD-CIRC-482-2024",
        "sha256": "483e8d2cf6f8769eb7d3bbfc9dda1a3df2132b6fe504bbd554f7bab1c80bdc99",
        "note": (
            "l'Algérie applique la ZLECAf à l'importation (17 322 lignes "
            "classées A/B/C, calendriers standard et réciprocité)"
        ),
    },
    "schedule_published": "aucune offre MUS ligne à ligne archivée (NOT_AVAILABLE)",
}


def main() -> int:
    # ── 1+2. Accises : assiette moteur + fin d'antidatage ──
    d = json.loads(EXCISE.read_text(encoding="utf-8"))
    for r in d.get("excise_rates", []):
        rate = r.get("rate")
        ad_valorem = isinstance(rate, str) and rate.strip().endswith("%")
        if ad_valorem:
            r["rate_basis"] = (
                "valeur en douane + droits de douane (CIF + DD) — ad valorem "
                "(assiette alignée sur le moteur)"
            )
        else:
            r["rate_basis"] = (
                "spécifique (quantité exigée — non calculable sans quantité)"
            )
        if r.get("effective_from") == "2017-07-01":
            r["effective_from"] = "2026-04-01"
            r["notes"] = (
                "source explicite : MRA Integrated Tariff Schedule HS2022 "
                "(schedule avril 2026) — la source ne documente PAS de validité "
                "rétroactive depuis 2017 ; aucune série historique affirmée"
            )
    d["assiette_note"] = (
        "assiette ad valorem = CIF + droits de douane (alignée sur le moteur) ; "
        "les composantes spécifiques exigent la quantité (non calculables sans elle)"
    )
    EXCISE.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")

    # ── 5. Formalités synthétiques (si présentes) ──
    ov_path = OVERRIDES
    if ov_path.is_file():
        ov = json.loads(ov_path.read_text(encoding="utf-8"))
        for m in ov.get("measures", []):
            m["mapping_confidence"] = min(m.get("mapping_confidence", 100), 70)
            m["legal_text_verified"] = False
            m["provenance_quality"] = (
                "DERIVED_FROM_REGIONAL_SCHEME — autorités réelles, exigences "
                "dérivées du schéma générique, à confirmer par les textes mauriciens"
            )
        ov_path.write_text(json.dumps(ov, ensure_ascii=False, indent=1), encoding="utf-8")

    # ── 3+4+6. Registre ──
    reg = json.loads(REGISTER.read_text(encoding="utf-8"))
    reg["preference_and_origin_status"] = "PARTIAL"
    reg["preference_evidence"] = {
        "instrument": "ZLECAf — aucune offre MUS ligne à ligne archivée",
        "status": "PARTIAL",
        "note": (
            "application effective démontrée (GTI) mais pas de schedule MUS "
            "ligne à ligne — la préférence n'est JAMAIS appliquée par le calculateur"
        ),
    }
    reg["afcfta_application_evidence"] = GTI_EVIDENCE
    reg["coverage_scope"] = {
        "base_tariff": "VERIFIED — 6 073 sous-positions MRA HS2022 (colonne TVA incluse)",
        "national_layer": (
            "PARTIAL — prélèvements nationaux omis non modélisés ; accises "
            "documentées (assiette alignée moteur) ; TVA avec exemptions par position"
        ),
    }
    reg["currency_note"] = (
        "customs_value attendu dans la devise de la juridiction (MUR) : toute "
        "valeur USD doit être convertie avant l'appel — les montants calculés "
        "sont étiquetés MUR"
    )
    reg["integrity_watch_fixes"] = {
        "as_of": "2026-09-06",
        "excise_rate_basis_aligned_with_engine": True,
        "excise_backdating_removed": True,
        "preference_downgraded_to_partial": True,
        "coverage_scope_documented": True,
        "currency_expectation_documented": True,
        "sh6_principle_documented": True,
    }
    REGISTER.write_text(json.dumps(reg, ensure_ascii=False, indent=1), encoding="utf-8")

    # ── 8. Config : principe SH6 ──
    cfg = json.loads(CONFIG.read_text(encoding="utf-8"))
    cfg["sh6_principle"] = (
        "les 6 premiers chiffres (SH) sont internationaux ; le tarif national "
        "se développe au-delà du 6e chiffre (MUS : 8 chiffres = SH6+2) — le "
        "tarif national authentique est la source unique"
    )
    CONFIG.write_text(json.dumps(cfg, ensure_ascii=False, indent=1), encoding="utf-8")

    print("MUS integrity watch : assiette accises alignée, anti-datage retiré (2026-04-01), "
          "préférence PARTIAL (GTI), couverture scannée, devise MUR, principe SH6")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
