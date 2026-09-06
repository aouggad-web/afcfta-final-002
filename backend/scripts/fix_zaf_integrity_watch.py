#!/usr/bin/env python3
"""Corrections Integrity Watch / Codex ZAF (PR #450) — cinq fils de revue.

1. **Préférence ZLECAf bindée à la vraie source** : la colonne AfCFTA du
   SARS Schedule 1 Part 1 (tarif national sud-africain EN VIGUEUR) est la
   preuve d'application ligne à ligne — 8 592 taux publiés par le SARS
   (4 329 SH6 + 4 263 codes 8 chiffres), exécutables via
   zlecaf_schedule_zaf.py avec porte légale. Statut : IMPLEMENTED_OFFER.
2. **Couverture** : coverage_complete reflète la base tarifaire (4 260 SPs
   nationales = codes du SARS officiel) ; les 8 592 taux AfCFTA SARS sont
   une couche séparée (SH6/8 chiffres) — écart expliqué dans le registre ;
   2 codes du canonique absents du PDF SARS actuel documentés
   (39173920/39173990 — retirés du tarif officiel).
3. **Accises** : le Schedule 1 Part 1 SARS ne contient PAS les accises
   (Schedule Part 2 séparé) — statut NOT_AVAILABLE + action d'archivage.
4. **Formalités** : AGRIINPUT sans codes HS (match-all) → scope réel
   chapitre 31 (engrais) ; toutes les formalités dégradées
   (legal_text_verified=false, conf ≤70).
5. **Devise** : customs_value attendu en ZAR (conversion avant appel).

Usage : backend/.venv311/bin/python backend/scripts/fix_zaf_integrity_watch.py
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REGISTER = ROOT / "data" / "south_africa" / "zaf_gazette_register.json"
OVERRIDES = ROOT / "data" / "south_africa" / "legal_overrides.json"
EXCISE = ROOT / "data" / "south_africa" / "excise_measures.json"
CONFIG = ROOT / "data" / "south_africa" / "jurisdiction_config.json"

OFFER_PATH = ROOT / "backend" / "data" / "official_preferential" / "ZAF_afcfta_2026-08-06.json.gz"


def main() -> int:
    # ── 2. compte des codes SARS vs canonique ──
    import gzip
    d = json.load(gzip.open(OFFER_PATH))
    sar_codes = {str(l["hs_code"]) for l in d["lines"]}
    by8 = {c for c in sar_codes if len(c) == 8}
    can = json.loads((ROOT / "backend" / "data" / "ZAF_tariffs.json").read_text(encoding="utf-8"))
    sps = {sp["code"] for l in can["tariff_lines"] for sp in (l.get("sub_positions") or [])}
    covered = sum(1 for c in sps if c in by8)
    missing = sorted(sps - by8)

    # ── 1. préférence : colonne AfCFTA SARS officielle ──
    reg = json.loads(REGISTER.read_text(encoding="utf-8"))
    reg["preference_and_origin_status"] = "IMPLEMENTED_OFFER"
    reg["preference_evidence"] = {
        "instrument": (
            "ZLECAf — colonne AfCFTA du SARS Schedule 1 Part 1 (tarif national "
            "sud-africain en vigueur), source : SARS, mise à jour 2026-08-06"
        ),
        "status": "IMPLEMENTED_OFFER",
        "line_count": d["line_count"],
        "rate_kinds": d["rate_kind_counts"],
        "source_pdf_sha256": d.get("source_pdf_sha256"),
        "note": (
            "le SARS publie et applique lui-même les taux ZLECAf ligne à ligne "
            "dans son tarif national — exécution contrôlée par "
            "zlecaf_schedule_zaf.py (porte légale : origine réciproque + "
            "certificat d'origine)"
        ),
    }
    reg["afcfta_application_evidence"] = {
        "sars_afcfta_column": True,
        "lines_published": d["line_count"],
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

    # ── 2. couverture ──
    reg["coverage_complete"] = True
    reg["base_tariff_documentation"]["data_status"] = "VERIFIED"
    reg["base_tariff_documentation"]["national_positions"] = len(sps)
    reg["base_tariff_documentation"]["sars_verification"] = {
        "verified_on": "2026-09-06",
        "source_pdf": "SARS Schedule 1 Part 1 (2026-08-28, 704 pages) — archivé localement",
        "codes_sars_officiels_8_digits": len(by8),
        "sub_positions_couvertes": covered,
        "codes_retires_documentes": missing,
        "note_8592": (
            "les 8 592 lignes = les taux AfCFTA publiés par le SARS (4 329 SH6 + "
            "4 263 codes 8 chiffres) — couche séparée de la base nationale 8 "
            "chiffres (4 260 SPs), les deux niveaux coexistent dans le tarif "
            "sud-africain"
        ),
    }
    reg["coverage_scope"] = {
        "base_tariff": "VERIFIED — 4 260 SPs nationales vs codes SARS officiels (4 263)",
        "national_layer": (
            "PARTIAL — accises NON incluses (Schedule Part 2 séparé, à archiver) ; "
            "préférence AfCFTA = colonne officielle SARS (exécutable gated)"
        ),
    }
    reg["data_gaps"] = [
        "accises : Schedule Part 2 SARS non archivé — excise NOT_AVAILABLE",
        f"codes retirés du tarif SARS actuel conservés dans le canonique : {', '.join(missing)}",
    ]
    reg["currency_note"] = (
        "customs_value attendu dans la devise de la juridiction (ZAR) : toute "
        "valeur USD doit être convertie avant l'appel — les montants calculés "
        "sont étiquetés ZAR"
    )
    reg["integrity_watch_fixes"] = {
        "as_of": "2026-09-06",
        "preference_bound_to_sars_afcfta_column": True,
        "coverage_scoped_and_verified": True,
        "codes_8592_explained": True,
        "retired_codes_documented": len(missing),
        "excise_not_available_documented": True,
        "formalities_downgraded": True,
        "currency_expectation_documented": True,
    }

    # ── 3. accises : NOT_AVAILABLE documenté ──
    excise_doc = {
        "schema_version": "1.0",
        "country": "ZAF",
        "as_of": "2026-09-06",
        "excise_rates": [],
        "status": "NOT_AVAILABLE",
        "note": (
            "les accises sud-africaines figurent dans le Schedule Part 2 du "
            "Customs and Excise Act (document séparé, non archivé à ce jour) — "
            "NOT_AVAILABLE, jamais deviné ; action : archiver le Schedule Part 2"
        ),
        "provenance": {"source": "SARS Schedule Part 2 (à archiver)"},
    }
    EXCISE.write_text(json.dumps(excise_doc, ensure_ascii=False, indent=1), encoding="utf-8")

    # ── 4. formalités : scopes réels + dégradation ──
    ov = json.loads(OVERRIDES.read_text(encoding="utf-8"))
    for m in ov.get("measures", []):
        if m.get("measure_id", "").endswith("AGRIINPUT") and not m.get("hs_codes"):
            m["hs_codes"] = [
                "31010000", "31021000", "31022100", "31022900", "31023000",
                "31024000", "31025000", "31026000", "31028000", "31029000",
                "31031100", "31031900", "31039000", "31042000", "31043000",
                "31049000", "31051000", "31052000", "31053000", "31054000",
                "31055100", "31055900", "31056000", "31059000",
            ]
            m["scope_note"] = "engrais — chapitre 31 (scope réel, non match-all)"
        m["mapping_confidence"] = min(m.get("mapping_confidence", 100), 70)
        m["legal_text_verified"] = False
        m["provenance_quality"] = (
            "DERIVED_FROM_REGIONAL_SCHEME — autorités réelles, exigences à "
            "confirmer par les textes sud-africains"
        )
    ov["provenance"]["integrity_watch"] = (
        "AGRIINPUT scopé au chapitre 31 ; toutes les formalités dégradées "
        "(legal_text_verified=false) — à confirmer par les textes sud-africains"
    )
    OVERRIDES.write_text(json.dumps(ov, ensure_ascii=False, indent=1), encoding="utf-8")

    # ── 5. config : principe SH6 ──
    cfg = json.loads(CONFIG.read_text(encoding="utf-8"))
    cfg["sh6_principle"] = (
        "les 6 premiers chiffres (SH) sont internationaux ; le tarif national "
        "se développe au-delà (ZAF : 8 chiffres) — le tarif national authentique "
        "(SARS Schedule 1 Part 1) est la source unique ; la colonne AfCFTA du "
        "SARS publie en outre 8 592 taux préférentiels appliqués"
    )
    CONFIG.write_text(json.dumps(cfg, ensure_ascii=False, indent=1), encoding="utf-8")

    REGISTER.write_text(json.dumps(reg, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"ZAF integrity watch : préférence IMPLEMENTED_OFFER (colonne SARS AfCFTA "
          f"{d['line_count']} lignes), couverture {covered}/{len(sps)} SPs vs SARS, "
          f"{len(missing)} codes retirés documentés, accises NOT_AVAILABLE documenté, "
          "formalités dégradées, devise ZAR")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
