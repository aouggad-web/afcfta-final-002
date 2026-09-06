#!/usr/bin/env python3
"""Documentation des exonérations TVA Maurice — 1 309 lignes sans TVA du tarif MRA.

Le tarif MRA Integrated Tariff Schedule HS2022 publie une colonne TVA par ligne :
3 470 lignes portent 15 %, **1 309 lignes n'en publient aucune** (poisson ch.03,
médicaments ch.29/30, machines ch.84, bus ch.87…) — l'absence de taux publiée par
la source est traitée comme exonération documentée, jamais comblée à 15 %.

Le script génère les enregistrements vat_exemptions (par chapitre, codes SP
explicites) consommés par engine/national_customs_calculation.vat_treatment
(treatment EXEMPT, rate 0), avec :
- référence légale : MRA Integrated Tariff Schedule HS2022 — colonne TVA vide
  (exonération à l'importation) ; cadre : Value Added Tax Act 1998, Schedule 1
  (corroboré par PwC Mauritius, revu 2026-06-15) ;
- source_id MUS-CANONICAL-TARIFF + SHA-256 du canonique.

Usage : backend/.venv311/bin/python backend/scripts/build_mus_vat_exemptions.py
"""
from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CANONICAL = ROOT / "backend" / "data" / "MUS_tariffs.json"
VAT_MEASURES = ROOT / "data" / "mauritius" / "vat_measures.json"

CHAPTER_LABELS = {
    "03": "Poissons et crustacés, mollusques et autres invertébrés aquatiques",
    "04": "Produits de la nature laitiers",
    "05": "Autres produits d'origine animale",
    "06": "Arbres, plantes vivantes ; bulbes, racines vivantes",
    "07": "Légumes, plantes, racines et tubercules alimentaires",
    "08": "Fruits comestibles ; écorces d'agrumes ou de melons",
    "09": "Café, thé, maté et épices",
    "10": "Céréales",
    "12": "Graines oléagineuses, graines, fruits à envelope dure",
    "15": "Graisses et huiles animales, végétales ou microbiennes",
    "16": "Préparations de viande, de poissons ou de crustacés",
    "18": "Cacao et préparations de cacao",
    "21": "Préparations alimentaires diverses",
    "22": "Boissons, liquides alcooliques et vinaigres",
    "23": "Résidus et déchets des industries alimentaires ; aliments pour animaux",
    "24": "Tabac et succédanés de tabac",
    "27": "Combustibles minéraux, huiles minérales",
    "28": "Produits chimiques inorganiques",
    "29": "Produits chimiques organiques (dont antibiotiques)",
    "30": "Produits pharmaceutiques",
    "31": "Engrais",
    "33": "Huiles essentielles, parfumerie, cosmétiques",
    "34": "Savons, agents de surface, cires",
    "35": "Matières albuminoïdes, colles, enzymes",
    "36": "Poudres pyrotechniques, allumettes",
    "37": "Produits photographiques et cinématographiques",
    "38": "Produits divers de l'industrie chimique",
    "39": "Matières plastiques",
    "40": "Caoutchouc",
    "41": "Peaux et cuirs bruts",
    "44": "Bois et articles en bois",
    "45": "Liège et articles en liège",
    "47": "Pâtes de bois ou de matières fibreuses cellulose",
    "48": "Papier et carton",
    "49": "Livres, journaux, imprimés",
    "51": "Laine, poils fins ou grossiers, filés",
    "52": "Coton",
    "53": "Autres fibres textiles végétales",
    "54": "Filaments synthétiques ou artificiels",
    "55": "Fibres synthétiques ou artificielles discontinues",
    "56": "Ouates, feutres, cordes, ficelles",
    "57": "Tapis et revêtements de sol en matières textiles",
    "58": "Textiles spécialisés",
    "59": "Textiles imprégnés, enduits ou recouverts",
    "60": "Étoffes tricotées ou crochetées",
    "61": "Vêtements en bonneterie",
    "62": "Vêtements autres qu'en bonneterie",
    "63": "Articles de textile à usage domestique",
    "64": "Chaussures",
    "65": "Coiffures",
    "68": "Ouvrages en pierre, plâtre, ciment",
    "69": "Produits céramiques",
    "70": "Verre",
    "71": "Pierres précieuses, métaux précieux",
    "72": "Fonte, fer et acier",
    "73": "Ouvrages en fonte, fer ou acier",
    "76": "Aluminium et ouvrages en aluminium",
    "78": "Plomb",
    "82": "Outils, couteaux et couverts",
    "83": "Ouvrages divers en métaux communs",
    "84": "Machines et appareils mécaniques (dont réacteurs nucléaires)",
    "85": "Machines et appareils électriques",
    "86": "Matériel ferroviaire",
    "87": "Véhicules automobiles (dont bus)",
    "90": "Instruments d'optique, de précision, de médecine",
    "91": "Horlogerie",
    "92": "Instruments de musique",
    "94": "Meubles, literie, luminaires",
    "95": "Jouets, jeux, articles de sport",
    "96": "Ouvrages divers",
}


def main() -> int:
    canon = json.loads(CANONICAL.read_text(encoding="utf-8"))
    vat_doc = json.loads(VAT_MEASURES.read_text(encoding="utf-8"))
    canon_sha = hashlib.sha256(CANONICAL.read_bytes()).hexdigest()

    by_chapter: dict[str, set] = defaultdict(set)
    exempt_lines = 0
    for l in canon["tariff_lines"]:
        taxes = l.get("taxes_detail") or []
        has_vat = any(
            str(t.get("tax", "")).replace(".", "").upper().startswith("TVA")
            or str(t.get("tax", "")).upper().startswith("VAT")
            for t in taxes
        )
        if has_vat:
            continue
        exempt_lines += 1
        chapter = l["hs6"][:2]
        for sp in (l.get("sub_positions") or []):
            if sp.get("code"):
                by_chapter[chapter].add(sp["code"])

    records = []
    for chapter in sorted(by_chapter):
        label = CHAPTER_LABELS.get(chapter, f"Chapitre {chapter}")
        records.append({
            "record_id": f"MUS-VAT-EXEMPT-CH{chapter}",
            "legal_product_description": (
                f"Chapitre {chapter} — {label} : aucune TVA publiée dans le tarif MRA "
                "pour ces sous-positions (exonération à l'importation)."
            ),
            "normalized_product_description": (
                f"chapter {chapter} goods exempt from import VAT per MRA tariff"
            ),
            "rate": "EXEMPT",
            "rate_basis": "aucune TVA publiée — non applicable",
            "effective_from": "2020-01-01",
            "effective_to": None,
            "legal_status": "CURRENT_OFFICIAL_GUIDE",
            "supersedes_record_id": None,
            "hs_codes_explicit": sorted(by_chapter[chapter]),
            "legal_reference": (
                "MRA Integrated Tariff Schedule HS2022 — colonne TVA vide "
                "(exonération) ; cadre : Value Added Tax Act 1998, Schedule 1 "
                "(corroboration PwC Mauritius, revu 2026-06-15)"
            ),
            "source_id": "MUS-CANONICAL-TARIFF",
            "verification_status": "VERIFIED_OFFICIAL_GUIDE",
            "positions_count": len(by_chapter[chapter]),
        })

    vat_doc["vat_exemptions"] = records
    vat_doc["vat_exemptions_summary"] = {
        "as_of": "2026-09-06",
        "lines_without_vat": exempt_lines,
        "sub_positions_covered": sum(len(v) for v in by_chapter.values()),
        "chapters": len(by_chapter),
        "doctrine": (
            "l'absence de taux TVA publiée par la source officielle est documentée "
            "comme exonération par position — jamais comblée au taux standard"
        ),
    }
    vat_doc["provenance"] = {
        "source": f"backend/data/MUS_tariffs.json ({canon['summary'].get('data_status')})",
        "canonical_sha256": canon_sha,
    }
    VAT_MEASURES.write_text(json.dumps(vat_doc, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"MUS vat_exemptions : {len(records)} enregistrements | "
          f"{exempt_lines} lignes | {sum(len(v) for v in by_chapter.values())} SP")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
