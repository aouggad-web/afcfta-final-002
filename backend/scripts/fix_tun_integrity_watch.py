#!/usr/bin/env python3
"""Corrections Integrity Watch TUN (PR #456) + réconciliation CI #1636.

Fils traités :
1. préférence ZLECAf : DOCUMENTED → PARTIAL (offre OFFER_ONLY ligne à ligne,
   application effective démontrée par le GTI du Secrétariat ZLECAf, réciprocité
   algérienne circulaire 482/2024) — jamais appliquée sans porte légale ;
2. TVA : effective_from rétroactif 2017-07-01 → date du re-crawl (2026-08-30),
   validité rétroactive non documentée par la source ;
3. assiette RPD : retirée des tables câblées du moteur (assiette source =
   « SOMME D.T » — somme des droits et taxes, PAS la valeur en douane) ;
   documentée verbatim, application moteur dédiée à venir ;
4. 83 codes retirés : valid_to = 2026-08-30 + statut RETIRED_FROM_SOURCE
   (fait par build_tun_canonical.py) ;
5. restrictions d'importation : réglementations d'import portées par sous-position
   (7 790 SP, 26 codes officiels : certificats sanitaires, contrôle technique,
   dérogation monopole d'État…) ; le décompte « ~1 545 interdictions » de la
   revue n'est pas vérifiable dans les données archivées → UNVERIFIED ;
6. couverture scannée : base tarifaire VERIFIED / couche nationale PARTIAL,
   trous documentés (droits spécifiques quantité non modélisés) ;
7. CI #1636 : réconciliation du registre d'enrichissement TUN à la source
   (vat_status NOT_AVAILABLE → DOCUMENTED, provenance re-crawl Tarif Web 2026)
   + mise à jour du compteur du test (27 → 28) avec justification.
+ devise TND documentée (conversion avant appel).

Usage : backend/.venv311/bin/python backend/scripts/fix_tun_integrity_watch.py
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VAT = ROOT / "data" / "tunisia" / "vat_measures.json"
LEVIES = ROOT / "data" / "tunisia" / "import_levies.json"
CONFIG = ROOT / "data" / "tunisia" / "jurisdiction_config.json"
REGISTER = ROOT / "data" / "tunisia" / "tun_gazette_register.json"
REGISTRY = ROOT / "data" / "algeria-active-3" / "tariff_enrichment_registry.json"

GTI_EVIDENCE = {
    "gti_participant": True,
    "gti_launch": "2022-10-07",
    "source_url": "https://au-afcfta.org/guided-trade-initiative/",
    "source_title": "AfCFTA Secretariat — Guided Trade Initiative (GTI)",
    "note": (
        "l'application effective des préférences ZLECAf par la douane tunisienne "
        "est démontrée par le Secrétariat (GTI) ; l'offre TUN est publiée dans "
        "l'e-Tariff Book (9 chiffres, OFFER_ONLY) — la portée ligne à ligne reste "
        "contrôlée par zlecaf_implementation_registry.py"
    ),
}
ALGERIA_RECIPROCITY = {
    "instrument": "Circulaire n° 482/DGD/SP/D.042/24 du 22 octobre 2024 (DGD Algérie)",
    "source_id": "DZA-DGD-CIRC-482-2024",
    "sha256": "483e8d2cf6f8769eb7d3bbfc9dda1a3df2132b6fe504bbd554f7bab1c80bdc99",
    "note": (
        "l'Algérie applique la ZLECAf à l'importation (17 322 lignes classées "
        "A/B/C, calendriers standard et réciprocité) — l'acceptation algérienne "
        "des partenaires ZLECAf prouve la réciprocité de l'accord"
    ),
}


def main() -> int:
    # ── 2. TVA : fin de la rétroactivité non documentée ──
    v = json.loads(VAT.read_text(encoding="utf-8"))
    for r in v.get("vat_rates", []):
        if r.get("effective_from") == "2017-07-01":
            r["effective_from"] = "2026-08-30"
            r["legal_status"] = "CURRENT_OFFICIAL_GUIDE"
            r["notes"] = (
                "taux publiés par le re-crawl Tarif Web 2026 du 2026-08-30 — la "
                "source ne documente PAS de validité rétroactive ; aucune série "
                "historique n'est affirmée"
            )
    VAT.write_text(json.dumps(v, ensure_ascii=False, indent=1), encoding="utf-8")

    # ── 3. RPD : hors câblage moteur (assiette = Σ D.T, pas CIF) ──
    lev = json.loads(LEVIES.read_text(encoding="utf-8"))
    rpd_tables = [k for k in lev if k.startswith("RPD")]
    for t in rpd_tables:
        for r in lev[t]:
            r["engine_wired"] = False
            r["rate_basis"] = (
                "assiette source verbatim : « SOMME D.T (G=0.1.2.3.4. » — somme des "
                "droits et taxes (PAS la valeur en douane) ; application moteur "
                "dédiée à venir, jamais calculée sur CIF"
            )
    lev["assiette_gaps"] = {
        "RPD": (
            "assiette = somme des droits et taxes (verbatim source) — non câblée : "
            "le moteur n'applique PAS cette redevance tant que son câblage n'est "
            "pas testé"
        )
    }
    LEVIES.write_text(json.dumps(lev, ensure_ascii=False, indent=1), encoding="utf-8")

    cfg = json.loads(CONFIG.read_text(encoding="utf-8"))
    cfg["levy_tables"] = [t for t in cfg.get("levy_tables", []) if not t.startswith("RPD")]
    cfg["levy_tables_not_wired"] = rpd_tables
    cfg["note"] = (
        "les tables RPD sont documentées mais NON câblées (assiette = somme des "
        "droits et taxes, verbatim source) — jamais calculées sur CIF"
    )
    CONFIG.write_text(json.dumps(cfg, ensure_ascii=False, indent=1), encoding="utf-8")

    # ── 1+5+6+7(devise). Registre ──
    reg = json.loads(REGISTER.read_text(encoding="utf-8"))
    reg["preference_and_origin_status"] = "PARTIAL"
    reg["preference_evidence"] = {
        "instrument": (
            "ZLECAf — offre TUN publiée dans l'e-Tariff Book (9 chiffres, "
            "OFFER_ONLY, 2 périodes 5/10 ans)"
        ),
        "status": "PARTIAL",
        "note": (
            "application effective démontrée (GTI) mais l'offre ligne à ligne "
            "n'est PAS exécutable sans instrument d'implémentation + origine "
            "vérifiée (porte zlecaf_implementation_registry)"
        ),
    }
    reg["afcfta_application_evidence"] = {
        **GTI_EVIDENCE,
        "algeria_reciprocity": ALGERIA_RECIPROCITY,
        "schedule_published": "e-Tariff Book (snapshot TUN — 9 373 lignes à 9 chiffres, 2 périodes)",
    }
    reg["coverage_scope"] = {
        "base_tariff": "VERIFIED — exhaustivité prouvée vs énumération officielle (17 542 = 17 542)",
        "national_layer": (
            "PARTIAL — taxes par ligne re-crawlées (assiettes verbatim) ; droits "
            "spécifiques fondés sur quantité documentés mais NON modélisés dans le "
            "moteur ; réglementations d'import portées par sous-position"
        ),
    }
    reg["data_gaps"] = [
        "droits spécifiques fondés sur quantité (P/*, TM/*, T/MOTEURS…) documentés avec assiettes verbatim mais non modélisés dans le moteur",
        "le décompte exact des positions interdites (~1 545 selon la revue) n'est pas vérifiable dans les données archivées — UNVERIFIED ; les réglementations d'import (26 codes officiels, dont 243 dérogations monopole d'État) sont portées par sous-position",
        "83 codes retirés de la source conservés avec valid_to=2026-08-30 et statut RETIRED_FROM_SOURCE",
        "assiette RPD (somme des droits et taxes) non câblée",
    ]
    reg["currency_note"] = (
        "customs_value attendu dans la devise de la juridiction (TND) : toute valeur "
        "USD doit être convertie avant l'appel — les montants calculés sont étiquetés TND"
    )
    reg["integrity_watch_fixes"] = {
        "as_of": "2026-09-06",
        "preference_downgraded_to_partial": True,
        "vat_retroactivity_removed": True,
        "rpd_assiette_not_wired": True,
        "retired_codes_validity_set": 83,
        "import_regulations_carried": 7790,
        "prohibitions_count_unverified": True,
        "coverage_scope_documented": True,
        "currency_expectation_documented": True,
    }
    REGISTER.write_text(json.dumps(reg, ensure_ascii=False, indent=1), encoding="utf-8")

    # ── 7. Registre d'enrichissement : réconciliation TUN à la source ──
    d = json.loads(REGISTRY.read_text(encoding="utf-8"))
    for key, entry in d["countries"].items():
        if key.startswith("TUN"):
            entry["vat_status"] = "DOCUMENTED"
            entry["line_count_per_country"] = 17625
            entry["source_paths"] = [
                "data/tunisia/legal_sources.json",
                "data/tunisia/vat_measures.json",
                "data/tunisia/calculation_method.json",
            ]
            entry["anomalies"] = [
                "RÉSOLU 2026-09-06 : re-crawl complet Tarif Web 2026 du 2026-08-30 "
                "(17 542 codes = énumération officielle, tous avec taux publiés) — "
                "TVA documentée par position avec assiettes verbatim",
                "droits spécifiques fondés sur quantité documentés mais non modélisés",
                "décompte des positions interdites UNVERIFIED (réglementations d'import portées par sous-position)",
            ]
            entry["vat_measure_path"] = "data/tunisia/vat_measures.json"
            entry["afcfta_status"] = "OFFER_ONLY"
            entry["regulatory_status"] = "PARTIAL"
            entry["required_documents_status"] = "PARTIAL"
    d["as_of"] = "2026-09-06"
    REGISTRY.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")

    print("TUN integrity watch : préférence PARTIAL (GTI+offre OFFER_ONLY), TVA non rétroactive, "
          "RPD non câblée, 83 codes valid_to, réglementations portées, registre d'enrichissement réconcilié")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
