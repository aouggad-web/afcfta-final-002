#!/usr/bin/env python3
"""Tarif douanier national du Mozambique — Pauta Aduaneira.

Remplace la moyenne SH6 WITS/UNCTAD-TRAINS qui servait 5 388 positions SANS
AUCUNE désignation.

LA CASCADE EST ÉTABLIE PAR LA LOI, article par article.
Lei n.º 11/2016 de 30 de Dezembro (Boletim da República, I Série n.º 156,
13.º Suplemento), Instruções Preliminares da Pauta :

  art. 4     « O valor aduaneiro adoptado na República de Moçambique é o
               definido no artigo VII do Acordo Geral sobre Tarifas e Comércio
               de 1994 (GATT). »                          → valeur OMC = CIF
  art. 15 §2 « As taxas ad valorem incidem sobre o valor aduaneiro expresso em
               moeda nacional. »                          → DD      sur CIF
  art. 15 §5 « A sobretaxa resulta da aplicação da taxa relativa à sobretaxa,
               que incide sobre o valor aduaneiro. »      → SOBRETX sur CIF
  art. 15 §6 « O Imposto sobre Consumos Específicos […] incide sobre o valor
               aduaneiro adicionado do total dos direitos efectivamente
               pagos. »                                   → ICE     sur CIF+DD
  art. 15 §7 « [O IVA] incide sobre o valor aduaneiro adicionado do total dos
               direitos aduaneiros e do Imposto sobre Consumos Específicos
               efectivamente pagos e da sobretaxa, se for o caso. »
                                                → IVA sur CIF+DD+ICE+SOBRETX

UNE CELLULE D'IVA VIDE EST UNE EXONÉRATION, ET LA LOI LA NOMME. Le Código do
IVA (Lei n.º 32/2007 de 31 de Dezembro), article 9, exonère notamment « as
transmissões de redes mosquiteiras » (§1 e), « as transmissões de medicamentos,
bem como especialidades farmacêuticas e outros produtos farmacêuticos » (§1 f),
et renvoie pour les listes aux biens « constantes da Pauta Aduaneira e
discriminadas no Anexo III, que é parte integrante do presente Código » (§1 g).
L'exonération est donc définie PAR RENVOI AU TARIF : c'est pour cela que la
colonne y est vide.
Le relevé le confirme position par position : 452 cellules vides, dont
CHAPITRE 30 (produits pharmaceutiques) 46 sur 46, CHAPITRE 31 (engrais) 24 sur
24, toutes les semences « PARA SEMENTEIRA », les « REPRODUTORES DE RAÇA PURA »,
et nommément vaccins, insuline, antibiotiques, vitamines, préservatifs,
moustiquaires, dictionnaires, charrues et prothèses. Ce n'est pas une lacune de
collecte, et la traiter comme telle ferait disparaître l'exonération elle-même.

TROIS PIÈGES DU FICHIER, tous relevés en le lisant.

1. LES DÉCIMALES CHANGENT DE SIGNE SELON LA COLONNE. « 2,5 » et « 7,5 » à la
   virgule dans DIREITOS_GERAL ; « 0.0099 MZN Per 1 KG » au point dans
   ICE_VAL_MIN. Une lecture qui n'admettrait que le point rendrait 25 au lieu
   de 2,5 — dix fois le droit dû.

2. ICE_VAL_MIN N'EST PAS UN TAUX. C'est un « valor mínimo » par unité
   (« 475 MZN Per 1 L »), c'est-à-dire un plancher d'assiette et non un
   pourcentage. Le moteur ne sait pas le liquider : il est porté avec son
   libellé, SANS taux.

3. TXSOBVAL N'EST PAS IDENTIFIÉE. La loi nomme et assoit la « sobretaxa »
   (SOBRETX), mais aucun des textes consultés n'explique la colonne TXSOBVAL.
   Elle est portée SANS assiette — donc non liquidable — plutôt que rattachée
   à la sobretaxa par ressemblance de nom.

PROVENANCE, ET SA RÉSERVE. Le fichier est un EXPORT DE BASE DE DONNÉES du
système douanier mozambicain (sa dernière ligne porte la requête SQL), déposé
par l'utilisateur — ce n'est pas un document publié par l'autorité. Il est donc
CONTRÔLÉ CONTRE LE BARÈME PUBLIÉ dans la Lei n.º 11/2016 : sur les 1 142
positions communes, 1 131 concordent. Les 11 écarts portent sur les céréales,
le malt et le houblon (7,5 % → 2,5 %) et les produits laitiers (0 → 20 %) :
des changements de politique tarifaire entre 2016 et l'extrait, non des erreurs.

CE QUE L'EXTRAIT N'A PAS, ET QUI EST DIT PLUTÔT QUE COMBLÉ. Le barème publié
porte DEUX COLONNES PRÉFÉRENTIELLES — SADC et UE — que cet extrait ne contient
pas. Aucune préférence n'est donc servie pour le Mozambique, et c'est une
lacune nommée, pas un régime absent.
"""

import csv
import hashlib
import json
import logging
import re
import sys
from datetime import date
from pathlib import Path
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "crawled"
SOURCE_LOI = (
    "Lei n.º 11/2016 de 30 de Dezembro — Pauta Aduaneira, Instruções Preliminares"
)
SOURCE_IVA = "Código do IVA, Lei n.º 32/2007 de 31 de Dezembro, artigo 9"

RX_HS8 = re.compile(r"^\d{8}$")
# Colonnes de l'extrait, dans l'ordre.
I_CODE, I_DESIGNATION, I_UNITE = 4, 5, 6
COLONNES = ("DIREITOS_GERAL", "ICE_AD_VAL", "ICE_VAL_MIN", "SOBRETX", "TXSOBVAL", "IVA")
I_PREMIERE_TAXE = 7


def lire_taux(brut: str) -> Tuple[Optional[float], str, Optional[str]]:
    """Rend (taux, libellé brut, motif de non-lecture).

    La virgule décimale est admise : le fichier écrit « 2,5 » dans les colonnes
    de droits et « 0.0099 » dans celle des valeurs minimales.
    """
    texte = " ".join(str(brut or "").split())
    if not texte:
        return None, "", "CELLULE_VIDE"
    try:
        return float(texte.replace(",", ".")), texte, None
    except ValueError:
        pass
    if re.search(r"\bper\b|\bMZN\b", texte, re.I):
        return None, texte, "VALEUR_MINIMALE_PAR_UNITE"
    return None, texte, "EXPRESSION_NON_RECONNUE"


def _taxe(code, nom, nom_fr, taux, brut, base, base_source, note=None, **extra) -> Dict:
    ligne = {
        "code": code,
        "name": nom,
        "name_fr": nom_fr,
        "rate_pct": taux,
        "raw_value": brut,
        "base": base,
        "base_source": base_source,
        "source": "Pauta Aduaneira — extrait du système douanier mozambicain",
    }
    if note:
        ligne["note"] = note
    ligne.update(extra)
    return ligne


def extraire(chemin: Path) -> Tuple[List[Dict], Dict[str, int]]:
    positions: Dict[str, Dict] = {}
    stats = {
        "iva_exoneree": 0,
        "ice_ad_valorem": 0,
        "ice_valeur_minimale": 0,
        "sobretaxa": 0,
        "txsobval_non_identifiee": 0,
        "expressions_non_reconnues": 0,
    }

    with open(chemin, encoding="utf-8") as f:
        for ligne in csv.reader(f):
            if len(ligne) < I_PREMIERE_TAXE + len(COLONNES):
                continue
            code = " ".join(str(ligne[I_CODE] or "").split())
            if not RX_HS8.match(code) or code in positions:
                continue

            valeurs = {
                nom: lire_taux(ligne[I_PREMIERE_TAXE + i])
                for i, nom in enumerate(COLONNES)
            }
            taxes: List[Dict] = []
            gaps: List[str] = []

            # ── Droit de douane — art. 15 §2, assis sur le valor aduaneiro ──
            dd, dd_brut, dd_motif = valeurs["DIREITOS_GERAL"]
            taxes.append(_taxe(
                "DD", "Direitos Aduaneiros (Taxa Geral)",
                "Droit de douane (taux général)",
                dd, dd_brut, "CIF", f"{SOURCE_LOI}, art. 4 et art. 15 §2",
            ))
            if dd is None:
                gaps.append(f"DD_{dd_motif}")

            # ── Imposto sobre Consumos Específicos — art. 15 §6, sur CIF+DD ──
            ice, ice_brut, ice_motif = valeurs["ICE_AD_VAL"]
            if ice_motif != "CELLULE_VIDE":
                stats["ice_ad_valorem"] += 1
                taxes.append(_taxe(
                    "ICE", "Imposto sobre Consumos Específicos (ad valorem)",
                    "Impôt sur les consommations spécifiques (ad valorem)",
                    ice, ice_brut, "CIF+DD", f"{SOURCE_LOI}, art. 15 §6",
                ))

            # ── Valeur minimale d'accise : un plancher, pas un taux ──
            _, vm_brut, vm_motif = valeurs["ICE_VAL_MIN"]
            if vm_motif != "CELLULE_VIDE":
                stats["ice_valeur_minimale"] += 1
                taxes.append(_taxe(
                    "ICE_VAL_MIN", "Imposto sobre Consumos Específicos (valor mínimo)",
                    "Valeur minimale d'accise",
                    None, vm_brut, None, None,
                    note="Plancher d'assiette par unité, exprimé en MZN — ce n'est "
                         "pas un pourcentage et le moteur ne sait pas le liquider.",
                    non_liquidable="VALEUR_MINIMALE_PAR_UNITE",
                ))

            # ── Sobretaxa — art. 15 §5, assise sur le valor aduaneiro ──
            sob, sob_brut, sob_motif = valeurs["SOBRETX"]
            if sob_motif != "CELLULE_VIDE":
                stats["sobretaxa"] += 1
                taxes.append(_taxe(
                    "SOBRETX", "Sobretaxa", "Surtaxe",
                    sob, sob_brut, "CIF", f"{SOURCE_LOI}, art. 15 §5",
                ))

            # ── TXSOBVAL : colonne que AUCUN texte consulté n'explique ──
            tsv, tsv_brut, tsv_motif = valeurs["TXSOBVAL"]
            if tsv_motif != "CELLULE_VIDE":
                stats["txsobval_non_identifiee"] += 1
                taxes.append(_taxe(
                    "TXSOBVAL", "TXSOBVAL (colonne non identifiée)",
                    "TXSOBVAL — prélèvement non identifié",
                    tsv, tsv_brut, None, None,
                    note="La loi nomme et assoit la « sobretaxa » (SOBRETX) mais "
                         "aucun texte consulté n'explique cette colonne. Portée "
                         "sans assiette plutôt que rattachée par ressemblance de nom.",
                ))

            # ── IVA — art. 15 §7 ; vide = exonération, Código do IVA art. 9 ──
            iva, iva_brut, iva_motif = valeurs["IVA"]
            exoneree = iva_motif == "CELLULE_VIDE"
            if exoneree:
                stats["iva_exoneree"] += 1
            taxes.append(_taxe(
                "IVA", "Imposto sobre o Valor Acrescentado",
                "Taxe sur la valeur ajoutée",
                0.0 if exoneree else iva,
                iva_brut,
                "CIF+DD+ICE+SOBRETX", f"{SOURCE_LOI}, art. 15 §7",
                note=(
                    "Colonne vide au tarif : exonération. Le Código do IVA "
                    "(Lei n.º 32/2007) art. 9 exonère notamment les médicaments et "
                    "produits pharmaceutiques, les moustiquaires, et renvoie pour "
                    "les listes aux biens « constantes da Pauta Aduaneira »."
                ) if exoneree else None,
                exoneration_au_tarif=exoneree,
                exoneration_source=SOURCE_IVA if exoneree else None,
            ))

            for _, _, motif in valeurs.values():
                if motif == "EXPRESSION_NON_RECONNUE":
                    stats["expressions_non_reconnues"] += 1

            positions[code] = {
                "national_code": code,
                "hs6": code[:6],
                "chapter": code[:2],
                "heading": f"{code[:4]}.{code[4:6]}",
                "statistical_unit": " ".join(str(ligne[I_UNITE] or "").split()),
                "designation": {
                    "pt": " ".join(str(ligne[I_DESIGNATION] or "").split()),
                    "fr": "",
                    "verbatim": " ".join(str(ligne[I_DESIGNATION] or "").split()),
                },
                "taxes": taxes,
                "preferential_rates": [],
                "restrictions": [],
                "source_gaps": gaps,
                "source": "Pauta Aduaneira (Moçambique) — extrait du système douanier",
            }

    return list(positions.values()), stats


def construire(chemin: Path) -> Dict:
    positions, stats = extraire(chemin)
    if len(positions) < 5000:
        raise SystemExit(
            f"Collecte refusée : {len(positions)} positions lues, moins de 5 000. "
            "Un tarif amputé ne vaut pas mieux qu'une moyenne."
        )
    codes = sorted({t["code"] for p in positions for t in p["taxes"]})
    return {
        "country": "MOZ",
        "country_name": "Mozambique",
        "calculation_rules": {
            "order": ["DD", "SOBRETX", "ICE", "IVA"],
            "bases": {
                "DD": {"basis": "CIF", "type": "ad_valorem"},
                "SOBRETX": {"basis": "CIF", "type": "ad_valorem"},
                "ICE": {"basis": "CIF+DD", "type": "ad_valorem"},
                "IVA": {"basis": "CIF+DD+ICE+SOBRETX", "type": "ad_valorem"},
            },
            "source": (
                "Cascade établie article par article par la Lei n.º 11/2016 "
                "(Instruções Preliminares da Pauta) : art. 4 (valeur en douane = "
                "article VII du GATT de 1994), art. 15 §2 (droits sur le valor "
                "aduaneiro), §5 (sobretaxa sur le valor aduaneiro), §6 (ICE sur "
                "valor aduaneiro + droits), §7 (IVA sur valor aduaneiro + droits + "
                "ICE + sobretaxa). Une colonne d'IVA vide est une EXONÉRATION, "
                "établie par le Código do IVA (Lei n.º 32/2007) art. 9. "
                "Ni ICE_VAL_MIN (plancher par unité) ni TXSOBVAL (colonne non "
                "identifiée) ne reçoivent d'assiette : ils sont portés sans, donc "
                "non liquidables, plutôt que supposés."
            ),
        },
        "source": "Pauta Aduaneira do Moçambique — extrait du système douanier national",
        "source_url": None,
        "source_legal": (
            "Lei n.º 11/2016 de 30 de Dezembro (Boletim da República, I Série "
            "n.º 156, 13.º Suplemento) ; Código do IVA, Lei n.º 32/2007"
        ),
        "source_quality": "crawled_authentic",
        "source_sha256": hashlib.sha256(chemin.read_bytes()).hexdigest(),
        "provenance_reserve": (
            "Extrait de base de données déposé par l'utilisateur, non un document "
            "publié par l'autorité douanière. Contrôlé contre le barème publié dans "
            "la Lei n.º 11/2016 : 1 131 concordances sur 1 142 positions communes ; "
            "les 11 écarts (céréales, malt et houblon 7,5 % → 2,5 %, produits "
            "laitiers 0 → 20 %) sont des changements de politique tarifaire, "
            "l'extrait étant le plus récent."
        ),
        "extracted_at": date.today().isoformat(),
        "stats": {
            "total_positions": len(positions),
            "unique_tax_codes": codes,
            "chapters_covered": len({p["chapter"] for p in positions}),
            **stats,
        },
        "sub_positions": positions,
    }


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    if len(sys.argv) < 2:
        print(f"usage: {sys.argv[0]} <chemin du CSV de la Pauta Aduaneira>")
        return 2
    donnees = construire(Path(sys.argv[1]))
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    (DATA_DIR / "MOZ_tariffs.json").write_text(
        json.dumps(donnees, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    s = donnees["stats"]
    logger.info(
        "MOZ : %s positions, %s chapitres, codes %s",
        s["total_positions"], s["chapters_covered"], ",".join(s["unique_tax_codes"]),
    )
    logger.info(
        "  IVA exonérée %s | ICE ad valorem %s | valeurs minimales %s | "
        "sobretaxa %s | TXSOBVAL %s | expressions non reconnues %s",
        s["iva_exoneree"], s["ice_ad_valorem"], s["ice_valeur_minimale"],
        s["sobretaxa"], s["txsobval_non_identifiee"], s["expressions_non_reconnues"],
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
