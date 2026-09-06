#!/usr/bin/env python3
"""Corrections Integrity Watch RWA (PR #454) — six fils de revue.

1. Accises : restauration des mesures de la loi primaire nº 011/2025
   (bière 40/65 %, cigarettes 36 % + FRW 230/pack, vin 70 % plafonné,
   essence FRW 183/l, gasoil FRW 150/l, véhicules <1500cc 5 %) ; les taux
   runtime de la colonne EAC (30 % bière, 36 % cigarettes) qui les
   contredisaient sont RETIRÉS — la colonne EAC 2017 n'a jamais été la loi
   rwandaise en vigueur. La ligne 2208 (spiritueux 40 %, non couverte par les
   7 mesures restaurées) est conservée avec sa provenance EAC explicite.
2. Assiette des accises alignée sur le moteur (ad valorem appliqué sur
   CIF + droits de douane) — l'assiette déclarée CIF seul était fausse.
3. Formalités : mapping_confidence 100 → 70 + legal_text_verified=false
   (dérivées du tarif EAC, sans texte rwandais établissant chaque document).
4. TVA : restauration des 3 traitements zéro-rated de la loi nº 049/2023.
5. Préférence ZLECAf : DOCUMENTED → OFFER_ONLY (le registre AfCFTA ne classe
   la preuve qu'OFFER_ONLY — jamais présentée comme préférence appliquée).
6. Devise : note explicite — customs_value attendu en RWF (conversion avant
   appel), les montants étant étiquetés RWF.

Usage : backend/.venv311/bin/python backend/scripts/fix_rwa_integrity_watch.py
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EXCISE = ROOT / "data" / "rwanda" / "excise_measures.json"
VAT = ROOT / "data" / "rwanda" / "vat_measures.json"
OVERRIDES = ROOT / "data" / "rwanda" / "legal_overrides.json"
REGISTER = ROOT / "data" / "rwanda" / "rwa_gazette_register.json"

LAW_011_2025 = "Law nº 011/2025 of 27/05/2025 establishing the excise duty"
LAW_049_2023 = "Law nº 049/2023 of 05/09/2023"

PRIMARY_EXCISE = [
    {
        "record_id": "RWA-EXCISE-BEER-OTHER",
        "rate": "65%",
        "rate_basis": "valeur en douane + droits de douane (CIF + DD) — ad valorem",
        "effective_from": "2025-07-01",
        "effective_to": None,
        "legal_status": "IN_FORCE_PRIMARY_TEXT",
        "supersedes_record_id": "RWA-EXCISE_EXCIS-30_0",
        "hs_codes_explicit": ["22030010", "22030090"],
        "legal_reference": (
            f"{LAW_011_2025}, Annexe — bière (autre que brassée localement à partir "
            "de matières premières locales) ; traitement préférentiel 40 % "
            "(BEER-LOCAL-RAWMAT) subordonné à la qualification du producteur, "
            "non dérivable du code SH"
        ),
        "source_id": "RWA-LAW-011-2025",
        "verification_status": "VERIFIED_PRIMARY_TEXT",
        "notes": (
            "La mesure BEER-LOCAL-RAWMAT (40 %) est conservée sans hs_codes_explicit : "
            "elle dépend d'une qualification producteur, pas du code tarifaire — le "
            "moteur applique le taux général 65 %."
        ),
    },
    {
        "record_id": "RWA-EXCISE-WINE-OTHER",
        "rate": "70% of value, capped at FRW 40,000 per litre",
        "rate_basis": (
            "valeur en douane + droits de douane (CIF + DD) — ad valorem plafonné "
            "par un montant spécifique par litre"
        ),
        "effective_from": "2025-07-01",
        "effective_to": None,
        "legal_status": "IN_FORCE_PRIMARY_TEXT",
        "supersedes_record_id": None,
        "hs_codes_explicit": [
            "2204.10.00", "2204.21.00", "2204.22.00", "2204.29.00",
            "2205.10.00", "2205.90.00",
        ],
        "legal_reference": f"{LAW_011_2025}, Annexe — vins et autres boissons fermentées",
        "source_id": "RWA-LAW-011-2025",
        "verification_status": "VERIFIED_PRIMARY_TEXT",
    },
    {
        "record_id": "RWA-EXCISE-CIGARETTES",
        "rate": "36% of the value of a pack of 20 cigarettes, plus FRW 230 per pack",
        "rate_basis": (
            "valeur en douane + droits de douane (CIF + DD) — ad valorem PLUS "
            "composante spécifique par paquet (exige la quantité)"
        ),
        "effective_from": "2025-07-01",
        "effective_to": None,
        "legal_status": "IN_FORCE_PRIMARY_TEXT",
        "supersedes_record_id": "RWA-EXCISE_EXCIS-36_0",
        "hs_codes_explicit": ["2402.20.10", "2402.20.90", "2402.90.00", "2402.10.00"],
        "legal_reference": f"{LAW_011_2025}, Annexe — cigarettes",
        "source_id": "RWA-LAW-011-2025",
        "verification_status": "VERIFIED_PRIMARY_TEXT",
    },
    {
        "record_id": "RWA-EXCISE-PETROL",
        "rate": "FRW 183 per litre",
        "rate_basis": "spécifique par litre (quantité exigée — non calculable sans quantité)",
        "effective_from": "2025-07-01",
        "effective_to": None,
        "legal_status": "IN_FORCE_PRIMARY_TEXT",
        "supersedes_record_id": None,
        "hs_codes_explicit": ["2710.12.20"],
        "legal_reference": f"{LAW_011_2025}, Annexe — essence",
        "source_id": "RWA-LAW-011-2025",
        "verification_status": "VERIFIED_PRIMARY_TEXT",
    },
    {
        "record_id": "RWA-EXCISE-GASOIL",
        "rate": "FRW 150 per litre",
        "rate_basis": "spécifique par litre (quantité exigée — non calculable sans quantité)",
        "effective_from": "2025-07-01",
        "effective_to": None,
        "legal_status": "IN_FORCE_PRIMARY_TEXT",
        "supersedes_record_id": None,
        "hs_codes_explicit": ["2710.19.31"],
        "legal_reference": f"{LAW_011_2025}, Annexe — gasoil",
        "source_id": "RWA-LAW-011-2025",
        "verification_status": "VERIFIED_PRIMARY_TEXT",
    },
    {
        "record_id": "RWA-EXCISE-VEHICLES-UNDER-1500CC",
        "rate": "5%",
        "rate_basis": "valeur en douane + droits de douane (CIF + DD) — ad valorem",
        "effective_from": "2025-07-01",
        "effective_to": None,
        "legal_status": "IN_FORCE_PRIMARY_TEXT",
        "supersedes_record_id": None,
        "hs_codes_explicit": ["8703.21.90"],
        "legal_reference": f"{LAW_011_2025}, Annexe — véhicules ≤ 1500 cc",
        "source_id": "RWA-LAW-011-2025",
        "verification_status": "VERIFIED_PRIMARY_TEXT",
    },
    {
        "record_id": "RWA-EXCISE-BEER-LOCAL-RAWMAT",
        "rate": "40%",
        "rate_basis": "valeur en douane + droits de douane (CIF + DD) — ad valorem",
        "effective_from": "2025-07-01",
        "effective_to": None,
        "legal_status": "CONDITIONAL_PRIMARY_TEXT",
        "supersedes_record_id": None,
        "hs_codes_explicit": [],
        "legal_reference": (
            f"{LAW_011_2025}, Annexe — bière brassée localement à partir de "
            "matières premières locales (qualification producteur exigée)"
        ),
        "source_id": "RWA-LAW-011-2025",
        "verification_status": "VERIFIED_PRIMARY_TEXT",
        "notes": "Documentation seule : jamais appliquée automatiquement (hs vide).",
    },
]

ZERO_RATED = [
    {
        "record_id": "RWA-VAT-ZERO-EXPORTS-GOODS",
        "legal_reference": f"{LAW_049_2023}, Article 4(a) and Article 7(1)(a)",
        "description": "Exportation de biens — taux zéro",
    },
    {
        "record_id": "RWA-VAT-ZERO-EXPORTS-SERVICES",
        "legal_reference": f"{LAW_049_2023}, Article 4(a) and Article 7(1)(b)",
        "description": "Exportation de services — taux zéro",
    },
    {
        "record_id": "RWA-VAT-ZERO-MINERALS-DOMESTIC",
        "legal_reference": f"{LAW_049_2023}, Article 7(1)(c)",
        "description": "Fourniture de minéraux extraits localement — taux zéro",
    },
]


def main() -> int:
    # ── 1+2. Accises ──
    d = json.loads(EXCISE.read_text(encoding="utf-8"))
    runtime = d.get("excise_rates") or []
    kept_runtime = [
        r for r in runtime
        if not r["record_id"].startswith(("RWA-EXCISE_EXCIS-30", "RWA-EXCISE_EXCIS-36"))
    ]
    for r in kept_runtime:
        r["rate_basis"] = (
            "valeur en douane + droits de douane (CIF + DD) — ad valorem "
            "(source : colonne accise du tarif EAC CET 2022)"
        )
    d["excise_rates"] = PRIMARY_EXCISE + kept_runtime
    d["primary_law_restored"] = {
        "law": LAW_011_2025,
        "records_restored": len(PRIMARY_EXCISE),
        "runtime_removed": ["RWA-EXCISE_EXCIS-30_0", "RWA-EXCISE_EXCIS-36_0"],
        "reason": (
            "les taux de la colonne EAC (bière 30 %, cigarettes 36 %) contredisaient "
            "la loi primaire nº 011/2025 (bière 40/65 %, cigarettes 36 % + FRW 230/pack) "
            "— la loi rwandaise fait foi, la colonne EAC 2017 n'est pas la loi en vigueur"
        ),
    }
    EXCISE.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")

    # ── 4. TVA zéro-rated ──
    v = json.loads(VAT.read_text(encoding="utf-8"))
    existing_ids = {r["record_id"] for r in v.get("vat_zero_rated", [])}
    for z in ZERO_RATED:
        if z["record_id"] not in existing_ids:
            v.setdefault("vat_zero_rated", []).append({
                "record_id": z["record_id"],
                "rate": "0%",
                "rate_basis": "non applicable à l'importation — régime des fournitures",
                "effective_from": "2023-10-01",
                "effective_to": None,
                "legal_status": "IN_FORCE_PRIMARY_TEXT",
                "supersedes_record_id": None,
                "hs_codes_explicit": [],
                "legal_reference": z["legal_reference"],
                "source_id": "RWA-LAW-049-2023",
                "verification_status": "VERIFIED_PRIMARY_TEXT",
                "notes": z["description"] + " — documentation seule (pas d'application HS automatique).",
            })
    VAT.write_text(json.dumps(v, ensure_ascii=False, indent=1), encoding="utf-8")

    # ── 3. Formalités ──
    o = json.loads(OVERRIDES.read_text(encoding="utf-8"))
    for m in o["measures"]:
        m["mapping_confidence"] = 70
        m["legal_text_verified"] = False
        m["provenance_quality"] = (
            "DERIVED_FROM_REGIONAL_TARIFF — autorités nationales réelles, mais les "
            "exigences documentaires dérivent du schéma IMPDEC/VETCERT/buckets et du "
            "tarif EAC, sans texte rwandais établissant chaque document"
        )
    o["provenance"]["integrity_watch"] = (
        "mapping_confidence dégradé à 70 et legal_text_verified=false — formalités "
        "dérivées du tarif régional, à confirmer par les textes rwandais"
    )
    OVERRIDES.write_text(json.dumps(o, ensure_ascii=False, indent=1), encoding="utf-8")

    # ── 5+6. Registre : préférence OFFER_ONLY + devise ──
    reg = json.loads(REGISTER.read_text(encoding="utf-8"))
    reg["preference_and_origin_status"] = "OFFER_ONLY"
    reg["preference_evidence"] = {
        "instrument": "ZLECAf — offre e-Tariff Book (au-afcfta.org), OFFER_ONLY",
        "note": (
            "aucun instrument d'implémentation rwandais ni liste officielle "
            "d'origines réciproques vérifié au 2026-09-06 — la préférence n'est "
            "JAMAIS appliquée par le calculateur (porte zlecaf_implementation_registry)"
        ),
        "status": "OFFER_ONLY",
    }
    reg["currency_note"] = (
        "customs_value attendu dans la devise de la juridiction (RWF) : toute valeur "
        "USD doit être convertie avant l'appel — les montants calculés sont étiquetés RWF"
    )
    reg["integrity_watch_fixes"] = {
        "as_of": "2026-09-06",
        "excise_primary_law_restored": True,
        "excise_rate_basis_aligned_with_engine": True,
        "formalities_confidence_downgraded": True,
        "vat_zero_rated_restored": 3,
        "preference_downgraded_to_offer_only": True,
        "currency_expectation_documented": True,
    }
    REGISTER.write_text(json.dumps(reg, ensure_ascii=False, indent=1), encoding="utf-8")

    print("RWA integrity watch : accises loi restaurées (7), runtime conflictuels retirés (2), "
          "zéro-rated restaurés (3), formalités dégradées (11), préférence OFFER_ONLY, devise documentée")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
