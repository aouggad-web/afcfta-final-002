#!/usr/bin/env python3
"""Registre verbatim des codes de taxes/assiettes TUN publiés par la source +
manifeste SHA-256 des documents officiels archivés (méthode DZA)."""
import hashlib
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

CRAWLED = Path("backend/data/crawled/TUN_tariffs.json")
SRC = Path("data/sources/TUN")


def main():
    now = datetime.now(timezone.utc).isoformat()
    d = json.loads(CRAWLED.read_text(encoding="utf-8"))

    reg = {}
    for s in d["sub_positions"]:
        for side in ("taxes_import", "taxes_export"):
            for t in s.get(side) or []:
                r = reg.setdefault(t["code"], {
                    "codes_source": set(), "assiettes": set(), "n_lignes": 0,
                    "n_ad_valorem": 0, "n_specifique": 0, "cotes": set(),
                })
                r["codes_source"].add(t.get("name") or "")
                r["assiettes"].add((t.get("assiette") or "").strip())
                r["n_lignes"] += 1
                r["n_specifique" if t.get("specific_value") else "n_ad_valorem"] += 1
                r["cotes"].add("import" if side == "taxes_import" else "export")

    registry = {
        "country": "TUN",
        "title": "Registre verbatim des codes de taxes et de leurs assiettes (méthode de calcul publiée par la source)",
        "source": "douane.gov.tn/tarifweb2025 (données de juin 2026) — assiettes telles que publiées par la source, sans interprétation",
        "generated_at": now,
        "note": (
            "Chaque taxe de chaque sous-position du fichier national porte son assiette "
            "(base de calcul) dans le champ `assiette`. Les libellés d'assiette sont conservés "
            "tels que publiés (abréviations de la source, certains tronqués côté source). "
            "Les chapitres du Code des douanes archivés (CD_12 en particulier) fournissent la "
            "base légale des droits et taxes perçus par la douane."
        ),
        "taxes": [
            {
                "code": code,
                "libelles_source": sorted(r["codes_source"]),
                "assiettes_source": sorted(r["assiettes"]),
                "cotations": sorted(r["cotes"]),
                "n_lignes": r["n_lignes"],
                "n_ad_valorem": r["n_ad_valorem"],
                "n_specifique": r["n_specifique"],
            }
            for code in sorted(reg)
        ],
    }
    out = SRC / "tarifweb2026" / "tax_codes_and_assiettes.json"
    out.write_text(json.dumps(registry, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"registre: {len(reg)} codes de taxes -> {out}")

    # --- manifeste des documents archivés ---
    docs = []

    def add(path, title, source_url, referencing_page):
        p = Path(path)
        docs.append({
            "file": str(p.relative_to(SRC)),
            "title": title,
            "source_url": source_url,
            "referencing_page": referencing_page,
            "sha256": hashlib.sha256(p.read_bytes()).hexdigest(),
            "archived_at": now,
        })

    for i in range(1, 17):
        f = SRC / "code_douanes" / f"CD_{i}.pdf"
        if f.exists():
            add(f, f"Code des douanes tunisien (loi n°2008-34 du 2 juin 2008) — section {i}/16", 
                f"https://www.douane.gov.tn/fileadmin/lois_et_reglements/CD/FR/CD_{i}.pdf",
                "https://www.douane.gov.tn/code-des-douanes/")
    add(SRC / "textes_application" / "2009-02-25_Arrete_preuves_d_origine.pdf",
        "Arrêté du 25 février 2009 — preuves d'origine (texte d'application du Code des douanes)",
        "https://www.douane.gov.tn/fileadmin/lois_et_reglements/TA_2008/FR/2009-02-25_Arrete_preuves_d_origine.pdf",
        "https://www.douane.gov.tn/textes-dapplication-2/")
    add(SRC / "textes_application" / "2009-02-19_Arrete_justif_d_origine.pdf",
        "Arrêté du 19 février 2009 — justification d'origine (texte d'application du Code des douanes)",
        "https://www.douane.gov.tn/fileadmin/lois_et_reglements/TA_2008/FR/2009-02-19_Arrete_justif_d_origine.pdf",
        "https://www.douane.gov.tn/textes-dapplication-2/")
    for f in sorted((SRC / "tarifweb2026").glob("*.html")):
        add(f, f"Capture du portail officiel Tarif Web 2026 — {f.name}",
            "https://www.douane.gov.tn/tarifweb2026/ (+ tarifwebnew/getresultat.php)",
            "https://www.douane.gov.tn/tarifweb2026/")
    add(SRC / "tarifweb2026" / "tax_codes_and_assiettes.json",
        "Registre verbatim des codes de taxes et assiettes (extrait du fichier national)",
        "douane.gov.tn/tarifweb2025 (données de juin 2026)",
        "https://www.douane.gov.tn/tarifweb2026/")

    manifest = {
        "country": "TUN",
        "generated_at": now,
        "description": "Documents officiels tunisiens archivés avec empreintes SHA-256 (méthode DZA : archiver sans remplacer les fichiers de données).",
        "documents": docs,
    }
    (SRC / "_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"manifeste: {len(docs)} documents -> {SRC}/_manifest.json")


if __name__ == "__main__":
    main()
