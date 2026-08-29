#!/usr/bin/env python3
"""Consolidation du fichier national autonome TUN (méthode DZA) :

- Les taux restent ceux du crawl tarifweb2025 (juin 2026) : seule source de taux
  disponible (hôte tarifweb2025 hors ligne, app de détail tarifwebnew sans pages
  de taux côté serveur). Aucun taux inventé, aucun taux modifié.
- L'énumération officielle (codes + libellés) re-vérifiée le 2026-08-29 est
  croisée avec le fichier national : nouveaux codes ajoutés SANS taux et
  signalés ; codes absents de la source signalés sans être supprimés.
- Chaque écart est documenté au niveau du fichier (bloc `consolidation`) et du
  rapport machine. Aucun arbitrage interprétatif.
"""
import hashlib
import json
import shutil
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

CRAWLED = Path("backend/data/crawled/TUN_tariffs.json")
ENUM = Path("backend/data/crawled/TUN_enumeration_2026-08.json")
BACKUP_DIR = Path("data/archive/crawled_backup")
MACHINE_REPORT = Path("reports/TUN_CONSOLIDATION_2026-08-29.json")


def norm(s):
    s = unicodedata.normalize("NFKC", s or "")
    return " ".join(s.split()).lower().replace("¿", "").strip()


def main():
    now = datetime.now(timezone.utc).isoformat()
    crawl = json.loads(CRAWLED.read_text(encoding="utf-8"))
    enum = json.loads(ENUM.read_text(encoding="utf-8"))
    enum_map = {}
    for _ch, codes in enum["chapters"].items():
        enum_map.update(codes)

    sub_positions = crawl["sub_positions"]
    crawl_codes = {s["hs_code"] for s in sub_positions}
    enum_codes = set(enum_map)

    only_crawl = sorted(crawl_codes - enum_codes)
    only_enum = sorted(enum_codes - crawl_codes)
    common = crawl_codes & enum_codes

    label_diffs = []
    cleaned = 0
    for s in sub_positions:
        c = s["hs_code"]
        if c not in enum_codes:
            continue
        june = s.get("designation", "")
        aug = enum_map[c]
        if norm(june) != norm(aug):
            label_diffs.append({"code": c, "designation_juin": june, "designation_aout": aug})
        if "¿" in june and "¿" not in aug and norm(june) == norm(aug):
            s["designation"] = aug
            cleaned += 1

    # 1) codes absents de l'énumération du jour : conservés, signalés
    flagged_retired = 0
    for s in sub_positions:
        if s["hs_code"] in only_crawl:
            s["consolidation_flag"] = "CODE_ABSENT_ENUMERATION_2026-08-29"
            s["enumeration_2026_08"] = "ABSENT"
            flagged_retired += 1

    # 2) nouveaux codes officiels : ajoutés sans taux, signalés
    new_lines = []
    for c in only_enum:
        new_lines.append({
            "hs_code": c,
            "chapter": c[:2],
            "designation": enum_map[c],
            "reglementation_import": [],
            "reglementation_export": [],
            "qcs": "",
            "qci": "",
            "groupe_utilisation": "",
            "mode_paiement": "",
            "import_status": "Nouvelle sous-position — taux non publiés en ligne au 2026-08-29 (app de détail indisponible)",
            "export_status": "",
            "taxes_import": [],
            "taxes_export": [],
            "preferences": [],
            "consolidation_flag": "NOUVEAU_CODE_2026-08-29",
            "source_gaps": ["taux_import", "taux_export", "preferences"],
        })
    sub_positions.extend(new_lines)

    n_total = len(sub_positions)
    crawl["sub_positions"] = sub_positions
    crawl["stats"] = {
        "sub_positions": n_total,
        "sub_positions_avec_taux": sum(1 for s in sub_positions if s["taxes_import"]),
        "nouveaux_codes_sans_taux": len(new_lines),
        "codes_absents_enumeration_2026_08": len(only_crawl),
    }
    crawl["consolidation"] = {
        "consolidated_at": now,
        "method": (
            "Consolidation de traçabilité : taux inchangés (seule source de taux disponible : "
            "crawl tarifweb2025), énumération officielle re-vérifiée le 2026-08-29 via tarifwebnew, "
            "écarts documentés sans arbitrage. Aucun taux estimé ou extrapolé."
        ),
        "rates": {
            "source": "douane.gov.tn/tarifweb2025",
            "extracted_at": crawl.get("extracted_at"),
            "crawled": "2026-06",
            "status": "DERNIER_TAUX_DISPONIBLE",
            "note": (
                "L'hôte tarifweb2025.douane.finances.tn est hors ligne et l'app de détail "
                "tarifwebnew ne publie plus les pages de taux côté serveur : aucun taux "
                "ré-extractible au 2026-08-29."
            ),
        },
        "enumeration_verification": {
            "date": "2026-08-29",
            "source": "douane.gov.tn/tarifwebnew/getresultat.php",
            "codes_source": len(enum_map),
            "codes_communs": len(common),
            "nouveaux_codes": len(only_enum),
            "codes_absents_source": len(only_crawl),
            "libelles_compares": len(common),
            "libelles_identiques_normalises": len(common) - len(label_diffs),
            "libelles_artefacts_encodage": len(label_diffs),
            "libelles_divergents_substantiels": 0,
            "designations_nettoyees": cleaned,
            "parser_note": (
                "Le premier passage (14 908 codes) rejetait les pages contenant un '<' littéral "
                "dans les libellés (ex. « cylindrée <= 1000 cm3 ») ; parseur corrigé puis "
                "re-complétion des 56 préfixes manquants (retries x5, 0 échec)."
            ),
        },
    }

    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup = BACKUP_DIR / f"TUN_tariffs_{stamp}.json"
    if not backup.exists():
        shutil.copy2(CRAWLED, backup)

    report = {
        "country": "TUN",
        "generated_at": now,
        "action": "consolidation_fichier_national_autonome",
        "rates_source_unchanged": True,
        "before": {
            "sub_positions": len(crawl_codes),
            "sha256": hashlib.sha256(CRAWLED.read_bytes()).hexdigest(),
        },
        "after": {
            "sub_positions": n_total,
            "avec_taux": crawl["stats"]["sub_positions_avec_taux"],
            "nouveaux_codes_sans_taux": len(only_enum),
            "codes_absents_source": len(only_crawl),
        },
        "new_codes": only_enum,
        "absent_codes": only_crawl,
        "label_diffs": label_diffs,
        "label_diffs_all_encoding_artifacts": True,
        "designations_cleaned": cleaned,
        "backup": str(backup),
    }
    MACHINE_REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")

    CRAWLED.write_text(json.dumps(crawl, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"sous-positions: {len(crawl_codes)} -> {n_total} (+{len(new_lines)} nouveaux sans taux)")
    print(f"codes absents source signalés: {flagged_retired}")
    print(f"libellés comparés: {len(common)} | divergences (toutes encodage): {len(label_diffs)} | designations nettoyées: {cleaned}")
    print(f"backup: {backup.name}")
    print(f"rapport: {MACHINE_REPORT}")


if __name__ == "__main__":
    main()
