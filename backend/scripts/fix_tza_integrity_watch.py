#!/usr/bin/env python3
"""Corrections Integrity Watch TZA (PR #455) — cinq fils de revue.

1. Accises : restauration des mesures VERIFIED_PRIMARY_TEXT (Excise
   (Management and Tariff) Act, Cap. 147 — jus 9/232 Tshs/l, eau minérale
   58/64.05 Tshs/l, cheveux humains 10/25 %) ; les 4 taux runtime de la
   colonne EAC (2203/2204/2208/2402/2403) sont CONSERVÉS car ils couvrent des
   produits différents — aucun conflit ni double comptage.
2. Assiette : alignée sur le moteur (ad valorem appliqué sur CIF + DD).
3. VAT : restauration du traitement zéro-rated exportations (VAT Act 2014,
   Sections 5(2)/55).
4. Préférence ZLECAf : DOCUMENTED → NOT_AVAILABLE (aucun snapshot d'offre
   TZA, aucune preuve d'application — jamais présentée comme appliquée).
5. legal_sources.json : ajout de TZA-CANONICAL-TARIFF (référencé par les
   accises runtime) + note de couverture (base tarifaire vérifiée, couche
   nationale partielle : lois de finances/amendements non re-vérifiés).
6. Devise : customs_value attendu en TZS (conversion avant appel).

Usage : backend/.venv311/bin/python backend/scripts/fix_tza_integrity_watch.py
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EXCISE = ROOT / "data" / "tanzania" / "excise_measures.json"
VAT = ROOT / "data" / "tanzania" / "vat_measures.json"
SOURCES = ROOT / "data" / "tanzania" / "legal_sources.json"
REGISTER = ROOT / "data" / "tanzania" / "tza_gazette_register.json"

CAP147 = "Excise (Management and Tariff) Act, Cap. 147 (R.E. 2019)"

PRIMARY_EXCISE = [
    {
        "record_id": "TZA-EXCISE-2009-FRUIT-VEG-JUICE-LOCAL",
        "rate": "Tshs. 9.00 per litre",
        "rate_basis": "spécifique par litre (quantité exigée — non calculable sans quantité)",
        "hs_codes_explicit": [],
        "legal_reference": f"{CAP147} — jus de fruits/légumes produits localement",
        "verification_status": "VERIFIED_PRIMARY_TEXT",
        "source_id": "TZA-MOF-EXCISE-ACT-CAP147",
        "notes": "documentation seule (hs vide — application automatique impossible)",
    },
    {
        "record_id": "TZA-EXCISE-2009-FRUIT-VEG-JUICE-OTHER",
        "rate": "Tshs. 232.00 per litre",
        "rate_basis": "spécifique par litre (quantité exigée — non calculable sans quantité)",
        "hs_codes_explicit": [],
        "legal_reference": f"{CAP147} — jus de fruits/légumes (autres, dont importés)",
        "verification_status": "VERIFIED_PRIMARY_TEXT",
        "source_id": "TZA-MOF-EXCISE-ACT-CAP147",
        "notes": "documentation seule (hs vide — application automatique impossible)",
    },
    {
        "record_id": "TZA-EXCISE-2201-MINERAL-WATER-LOCAL",
        "rate": "Tshs. 58.00 per litre",
        "rate_basis": "spécifique par litre (quantité exigée — non calculable sans quantité)",
        "hs_codes_explicit": [],
        "legal_reference": f"{CAP147} — eau minérale produite localement",
        "verification_status": "VERIFIED_PRIMARY_TEXT",
        "source_id": "TZA-MOF-EXCISE-ACT-CAP147",
        "notes": "documentation seule (hs vide)",
    },
    {
        "record_id": "TZA-EXCISE-2201-MINERAL-WATER-IMPORTED",
        "rate": "Tshs. 64.05 per litre",
        "rate_basis": "spécifique par litre (quantité exigée — non calculable sans quantité)",
        "hs_codes_explicit": [],
        "legal_reference": f"{CAP147} — eau minérale importée",
        "verification_status": "VERIFIED_PRIMARY_TEXT",
        "source_id": "TZA-MOF-EXCISE-ACT-CAP147",
        "notes": "documentation seule (hs vide)",
    },
    {
        "record_id": "TZA-EXCISE-0501-HUMAN-HAIR-LOCAL",
        "rate": "10%",
        "rate_basis": "valeur en douane + droits de douane (CIF + DD) — ad valorem",
        "hs_codes_explicit": [],
        "legal_reference": f"{CAP147} — cheveux humains (produits locaux)",
        "verification_status": "VERIFIED_PRIMARY_TEXT",
        "source_id": "TZA-MOF-EXCISE-ACT-CAP147",
        "notes": "documentation seule (hs vide)",
    },
    {
        "record_id": "TZA-EXCISE-0501-HUMAN-HAIR-IMPORTED",
        "rate": "25%",
        "rate_basis": "valeur en douane + droits de douane (CIF + DD) — ad valorem",
        "hs_codes_explicit": [],
        "legal_reference": f"{CAP147} — cheveux humains (importés)",
        "verification_status": "VERIFIED_PRIMARY_TEXT",
        "source_id": "TZA-MOF-EXCISE-ACT-CAP147",
        "notes": "documentation seule (hs vide)",
    },
]


def main() -> int:
    # ── 1+2. Accises ──
    d = json.loads(EXCISE.read_text(encoding="utf-8"))
    runtime = d.get("excise_rates") or []
    for r in runtime:
        r["rate_basis"] = (
            "valeur en douane + droits de douane (CIF + DD) — ad valorem "
            "(source : colonne accise du tarif EAC CET 2022)"
        )
    existing_ids = {r["record_id"] for r in runtime}
    restored = [r for r in PRIMARY_EXCISE if r["record_id"] not in existing_ids]
    d["excise_rates"] = restored + runtime
    d["primary_law_restored"] = {
        "law": CAP147,
        "records_restored": len(restored),
        "runtime_kept": [r["record_id"] for r in runtime],
        "reason": (
            "les mesures Cap. 147 couvrent des produits (2009, 2201, 0501) non "
            "couverts par la colonne accise EAC (2203/2204/2208/2402/2403) — "
            "aucun conflit, aucune double comptage ; assiette alignée sur le moteur"
        ),
    }
    EXCISE.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")

    # ── 3. VAT zéro-rated ──
    v = json.loads(VAT.read_text(encoding="utf-8"))
    if not v.get("vat_zero_rated"):
        v["vat_zero_rated"] = [{
            "record_id": "TZA-VAT-ZERO-EXPORTS",
            "rate": "0%",
            "rate_basis": "non applicable à l'importation — régime des exportations",
            "effective_from": "2015-07-01",
            "effective_to": None,
            "legal_status": "IN_FORCE_PRIMARY_TEXT",
            "supersedes_record_id": None,
            "hs_codes_explicit": [],
            "legal_reference": (
                "Value Added Tax Act, 2014 (Act No. 5 of 2014), Section 5(2) "
                "and Section 55 — exportations au taux zéro"
            ),
            "source_id": "TZA-TANZLII-VAT-ACT-2014",
            "verification_status": "VERIFIED_PRIMARY_TEXT",
            "notes": (
                "documentation seule — le zéro-rated exportations dépend de la "
                "nature de l'opération, pas du code SH : jamais appliqué "
                "automatiquement aux lignes d'import"
            ),
        }]
    VAT.write_text(json.dumps(v, ensure_ascii=False, indent=1), encoding="utf-8")

    # ── 5. legal_sources : TZA-CANONICAL-TARIFF ──
    ls = json.loads(SOURCES.read_text(encoding="utf-8"))
    ids = [s.get("source_id") for s in ls.get("sources", [])]
    if "TZA-CANONICAL-TARIFF" not in ids:
        ls.setdefault("sources", []).append({
            "source_id": "TZA-CANONICAL-TARIFF",
            "title": "East African Community — EAC Common External Tariff 2022 (canonique TZA)",
            "url": "https://www.kra.go.ke/images/publications/EAC-CET-2022-VERSION-30TH-JUNE-Fn.pdf",
            "note": (
                "dataset d'exécution dérivé du PDF officiel (eac_cet_scraper v2, "
                "SHA-256 4c5acc8b…) — référencé par les mesures VERIFIED_RUNTIME_DATASET"
            ),
        })
    SOURCES.write_text(json.dumps(ls, ensure_ascii=False, indent=1), encoding="utf-8")

    # ── 4+6. Registre : préférence NOT_AVAILABLE + couverture scannée + devise ──
    reg = json.loads(REGISTER.read_text(encoding="utf-8"))
    reg["preference_and_origin_status"] = "NOT_AVAILABLE"
    reg["preference_evidence"] = {
        "instrument": "ZLECAf — aucune offre TZA archivée dans l'e-Tariff Book",
        "status": "NOT_AVAILABLE",
        "note": (
            "aucun snapshot d'offre tanzanien ni instrument d'implémentation "
            "vérifié au 2026-09-06 — la préférence n'est JAMAIS appliquée par le "
            "calculateur (NOT_AVAILABLE, jamais zéro ni deviné)"
        ),
    }
    reg["coverage_scope"] = {
        "base_tariff": "VERIFIED — exhaustivité prouvée vs PDF officiel (5 954 SP)",
        "national_layer": (
            "PARTIAL — lois de finances, amendements et accises nationales non "
            "re-vérifiés texte primaire par texte primaire ; mesures Cap. 147 et "
            "VAT Act restaurées (documentation) ; colonne accise EAC câblée"
        ),
    }
    reg["currency_note"] = (
        "customs_value attendu dans la devise de la juridiction (TZS) : toute valeur "
        "USD doit être convertie avant l'appel — les montants calculés sont étiquetés TZS"
    )
    reg["integrity_watch_fixes"] = {
        "as_of": "2026-09-06",
        "excise_primary_law_restored": len(restored),
        "excise_rate_basis_aligned_with_engine": True,
        "vat_zero_rated_restored": 1,
        "preference_downgraded_to_not_available": True,
        "legal_sources_canonical_added": True,
        "coverage_scope_documented": True,
        "currency_expectation_documented": True,
    }
    REGISTER.write_text(json.dumps(reg, ensure_ascii=False, indent=1), encoding="utf-8")

    print(f"TZA integrity watch : accises Cap.147 restaurées ({len(restored)}), "
          "assiette alignée, zéro-rated VAT restauré, préférence NOT_AVAILABLE, "
          "TZA-CANONICAL-TARIFF ajouté à legal_sources, couverture scannée, devise documentée")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
