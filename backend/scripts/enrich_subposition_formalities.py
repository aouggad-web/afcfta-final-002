"""
enrich_subposition_formalities.py
Descend les formalités administratives du niveau HS6 vers chaque position
nationale (10 ou 11 chiffres) dans les 54 fichiers JSON pays.

Principe officiel:
  Les formalités sont établies par position tarifaire nationale (10/11 chiffres).
  Chaque sous-position hérite des formalités de sa position HS6 parente,
  avec possibilité de surcharge (overrides) pour les cas où la position nationale
  implique des exigences spécifiques différentes.

Usage:
  python scripts/enrich_subposition_formalities.py           # tous les pays
  python scripts/enrich_subposition_formalities.py DZA NGA   # pays spécifiques
"""

import json
import os
import sys
from copy import deepcopy
from pathlib import Path
from typing import Dict, List, Optional

DATA_DIR = Path(__file__).parent.parent / "data"

# ---------------------------------------------------------------------------
# Overrides par position nationale (10 chiffres)
# Basés sur les nomenclatures officielles publiées par les autorités douanières
# Format: { "CCNNNNNNNNNN": [liste de formalités] }
# où CC = ISO3 et NNNNNNNNNN = code national 10 chiffres
#
# Ces overrides remplacent COMPLÈTEMENT les formalités héritées du HS6 parent
# pour les positions qui ont des exigences spécifiques différentes.
# ---------------------------------------------------------------------------
POSITION_OVERRIDES: Dict[str, List[Dict]] = {

    # -----------------------------------------------------------------------
    # NIGERIA — NCS / NAFDAC / SON
    # Form M obligatoire pour toutes positions commerciales
    # Positions pharmaceutiques: autorisation NAFDAC spécifique
    # -----------------------------------------------------------------------
    "NGA3004901000": [   # Médicaments contenant pénicilline — usage hospitalier
        {"code": "IMPDEC", "document_fr": "Single Goods Declaration (SGD) — NICIS II",
         "document_en": "Single Goods Declaration (SGD) — NICIS II", "is_mandatory": True},
        {"code": "FORMM", "document_fr": "Form M — Autorisation d'Importation (CBN)",
         "document_en": "Form M — Pre-Import Authorization (CBN)", "is_mandatory": True},
        {"code": "PHARMAUTH", "document_fr": "Autorisation d'importation NAFDAC — Produits pharmaceutiques contrôlés",
         "document_en": "NAFDAC Import Authorization — Controlled pharmaceutical products", "is_mandatory": True},
    ],
    "NGA8703231000": [   # Véhicules 1500-3000cc usage particulier — taxe CISS
        {"code": "IMPDEC", "document_fr": "Single Goods Declaration (SGD) — NICIS II",
         "document_en": "Single Goods Declaration (SGD) — NICIS II", "is_mandatory": True},
        {"code": "FORMM", "document_fr": "Form M — Autorisation d'Importation (CBN)",
         "document_en": "Form M — Pre-Import Authorization (CBN)", "is_mandatory": True},
        {"code": "STDCERT", "document_fr": "Certificat de conformité SON (Standards Organisation of Nigeria)",
         "document_en": "SON Conformity Assessment Certificate", "is_mandatory": True},
        {"code": "CISS", "document_fr": "Redevance CISS — 1% CIF (Cotecna / Webb Fontaine)",
         "document_en": "CISS Levy — 1% CIF (Cotecna / Webb Fontaine)", "is_mandatory": True},
    ],

    # -----------------------------------------------------------------------
    # ÉGYPTE — GOEIC obligatoire pour produits manufacturés (Ch 25-96 sauf 50-63)
    # Positions agricoles/alimentaires: exemptées du GOEIC
    # Positions manufacturées: GOEIC obligatoire (Décret 991/2015)
    # -----------------------------------------------------------------------
    "EGY8471300000": [   # Ordinateurs portables
        {"code": "IMPDEC", "document_fr": "Déclaration en douane — Egyptian Customs Authority (ECA)",
         "document_en": "Customs Declaration — Egyptian Customs Authority (ECA)", "is_mandatory": True},
        {"code": "GOEIC", "document_fr": "Certificat d'inspection GOEIC — Produits industriels (Décret 991/2015)",
         "document_en": "GOEIC Inspection Certificate — Industrial goods (Decree 991/2015)", "is_mandatory": True},
    ],
    "EGY8517120000": [   # Téléphones portables
        {"code": "IMPDEC", "document_fr": "Déclaration en douane — Egyptian Customs Authority (ECA)",
         "document_en": "Customs Declaration — Egyptian Customs Authority (ECA)", "is_mandatory": True},
        {"code": "GOEIC", "document_fr": "Certificat d'inspection GOEIC — Appareils de télécommunication",
         "document_en": "GOEIC Inspection Certificate — Telecommunications equipment", "is_mandatory": True},
        {"code": "STDCERT", "document_fr": "Approbation de type NTRA — Équipements radiofréquence",
         "document_en": "NTRA Type Approval — Radio frequency equipment", "is_mandatory": True},
    ],

    # -----------------------------------------------------------------------
    # AFRIQUE DU SUD — SARS / ITAC / SAHPRA / NRCS
    # Positions textiles Ch 61-62: permis ITAC obligatoire
    # Positions pharmaceutiques: enregistrement SAHPRA
    # -----------------------------------------------------------------------
    "ZAF6109100010": [   # T-shirts coton — permis ITAC (quota textile)
        {"code": "IMPDEC", "document_fr": "Bill of Entry (DA 306) — SARS / SAPS",
         "document_en": "Bill of Entry (DA 306) — SARS / SAPS", "is_mandatory": True},
        {"code": "ITACPERM", "document_fr": "Permis d'importation ITAC — Textiles et vêtements (R3665/2011)",
         "document_en": "ITAC Import Permit — Textiles and clothing (R3665/2011)", "is_mandatory": True},
    ],
    "ZAF3004500010": [   # Médicaments — enregistrement SAHPRA
        {"code": "IMPDEC", "document_fr": "Bill of Entry (DA 306) — SARS",
         "document_en": "Bill of Entry (DA 306) — SARS", "is_mandatory": True},
        {"code": "PHARMAUTH", "document_fr": "Enregistrement SAHPRA — Medicine Control Council Act 101/1965",
         "document_en": "SAHPRA Registration — Medicine Control Council Act 101/1965", "is_mandatory": True},
    ],

    # -----------------------------------------------------------------------
    # MAROC — ADII / ONSSA / IMANOR
    # Positions agroalimentaires: contrôle ONSSA obligatoire (Loi 25-08)
    # -----------------------------------------------------------------------
    "MAR0207140000": [   # Morceaux de volaille congelés
        {"code": "910", "document_fr": "Déclaration Unique de Marchandises (DUM) — ADII",
         "document_en": "Single Goods Declaration (DUM) — ADII", "is_mandatory": True},
        {"code": "C01", "document_fr": "Certificat sanitaire vétérinaire — ONSSA (Loi 25-08)",
         "document_en": "Veterinary sanitary certificate — ONSSA (Law 25-08)", "is_mandatory": True},
        {"code": "C04", "document_fr": "Autorisation d'importation — ONSSA (quota abattoir agréé)",
         "document_en": "Import authorization — ONSSA (approved slaughterhouse quota)", "is_mandatory": True},
    ],
}


# ---------------------------------------------------------------------------
# Règles de surcharge conditionnelle par suffix de code national
# Appliquées quand aucun override exact n'existe
# ---------------------------------------------------------------------------
def _apply_conditional_rules(
    country: str,
    national_code: str,
    digits: int,
    hs6: str,
    description_fr: str,
    parent_formalities: List[Dict],
) -> Optional[List[Dict]]:
    """
    Retourne des formalités spécifiques si la position nationale remplit
    des conditions connues. Retourne None pour hériter du parent HS6.
    """
    desc_lower = (description_fr or "").lower()

    # EGY — GOEIC pour tous produits manufacturés (Ch 25-96 hors textile/habillement)
    chapter = hs6[:2]
    if country == "EGY":
        manufactured_chapters = set(str(c).zfill(2) for c in range(25, 97))
        textile_chapters = {str(c).zfill(2) for c in range(50, 64)}
        food_chapters = {str(c).zfill(2) for c in range(1, 25)}
        if chapter in manufactured_chapters and chapter not in textile_chapters | food_chapters:
            # Ajouter GOEIC si pas déjà présent
            codes_present = {f["code"] for f in parent_formalities}
            if "GOEIC" not in codes_present:
                result = deepcopy(parent_formalities)
                result.append({
                    "code": "GOEIC",
                    "document_fr": "Certificat d'inspection GOEIC — Produits industriels (Décret 991/2015, Loi 118/1975)",
                    "document_en": "GOEIC Inspection Certificate — Industrial goods (Decree 991/2015, Law 118/1975)",
                    "is_mandatory": True,
                    "authority_fr": "Organisme Général d'Exportation et d'Importation (GOEIC)",
                    "authority_en": "General Organization for Export and Import Control (GOEIC)",
                })
                return result

    # NGA — usage industriel vs usage personnel (certaines positions)
    if country == "NGA" and "usage industriel" in desc_lower:
        codes_present = {f["code"] for f in parent_formalities}
        if "STDCERT" not in codes_present:
            result = deepcopy(parent_formalities)
            result.append({
                "code": "STDCERT",
                "document_fr": "Certificat de conformité SON — Usage industriel",
                "document_en": "SON Conformity Certificate — Industrial use",
                "is_mandatory": True,
            })
            return result

    # ETH — permis d'importation pour produits de consommation
    if country == "ETH":
        consumer_chapters = set(str(c).zfill(2) for c in list(range(61, 64)) + list(range(84, 86)) + [87])
        if chapter in consumer_chapters:
            codes_present = {f["code"] for f in parent_formalities}
            if "ETHPERMIT" not in codes_present:
                result = deepcopy(parent_formalities)
                result.append({
                    "code": "ETHPERMIT",
                    "document_fr": "Permis d'importation — Ethiopian Trade Competition and Consumer Protection Authority (Proclamation 980/2016)",
                    "document_en": "Import Trade Permit — Ethiopian Trade Competition and Consumer Protection Authority (Proclamation 980/2016)",
                    "is_mandatory": True,
                })
                return result

    return None  # Hériter du parent


# ---------------------------------------------------------------------------
# Enrichissement d'un fichier pays
# ---------------------------------------------------------------------------
def enrich_country(country_iso3: str, dry_run: bool = False) -> Dict:
    path = DATA_DIR / f"{country_iso3}_tariffs.json"
    if not path.exists():
        return {"country": country_iso3, "status": "not_found"}

    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    lines = data.get("tariff_lines", [])
    enriched_lines = 0
    total_sub_positions = 0
    overridden = 0

    for line in lines:
        parent_formalities = line.get("administrative_formalities", [])
        hs6 = line.get("hs6", "")

        sub_positions = line.get("sub_positions", [])
        for sp in sub_positions:
            total_sub_positions += 1
            national_code = sp.get("code", "")
            digits = sp.get("digits", 10)
            desc_fr = sp.get("description_fr", "")

            # 1. Chercher un override exact pays+code
            override_key = f"{country_iso3}{national_code}"
            if override_key in POSITION_OVERRIDES:
                sp["administrative_formalities"] = deepcopy(POSITION_OVERRIDES[override_key])
                overridden += 1
                continue

            # 2. Appliquer règles conditionnelles
            conditional = _apply_conditional_rules(
                country_iso3, national_code, digits, hs6, desc_fr, parent_formalities
            )
            if conditional is not None:
                sp["administrative_formalities"] = conditional
                overridden += 1
                continue

            # 3. Héritage du parent HS6 (cas général)
            sp["administrative_formalities"] = deepcopy(parent_formalities)

        if sub_positions:
            enriched_lines += 1

    stats = {
        "country": country_iso3,
        "status": "ok" if not dry_run else "dry_run",
        "lines_with_sub_positions": enriched_lines,
        "total_sub_positions": total_sub_positions,
        "position_overrides_applied": overridden,
    }

    if not dry_run:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, separators=(",", ":"))

    return stats


# ---------------------------------------------------------------------------
# Point d'entrée
# ---------------------------------------------------------------------------
def main():
    args = sys.argv[1:]
    dry_run = "--dry-run" in args
    args = [a for a in args if not a.startswith("--")]

    if args:
        countries = [a.upper() for a in args]
    else:
        # Tous les pays disponibles
        countries = sorted(
            p.stem.replace("_tariffs", "")
            for p in DATA_DIR.glob("*_tariffs.json")
        )

    print(f"{'DRY RUN — ' if dry_run else ''}Enrichissement de {len(countries)} pays")
    print("-" * 60)

    total_sp = 0
    total_overrides = 0
    for cc in countries:
        result = enrich_country(cc, dry_run=dry_run)
        sp = result.get("total_sub_positions", 0)
        ov = result.get("position_overrides_applied", 0)
        total_sp += sp
        total_overrides += ov
        status = result.get("status", "?")
        print(f"  {cc:4s}  {status:10s}  {sp:6d} positions nationales  {ov} overrides")

    print("-" * 60)
    print(f"Total: {total_sp:,} positions nationales enrichies, {total_overrides} overrides appliqués")


if __name__ == "__main__":
    main()
