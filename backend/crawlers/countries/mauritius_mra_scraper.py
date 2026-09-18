#!/usr/bin/env python3
"""Tarif douanier national de Maurice — Customs Tariff Schedules (Integrated Tariff).

Source : https://www.mra.mu/download/TariffInf130826.pdf
        807 pages, HS 2022, « As at 13 August 2026 », publié par la MRA Customs.

Remplace la moyenne SH6 WITS/UNCTAD-TRAINS qui servait 5 619 positions SANS
AUCUNE désignation. Le tarif national porte les codes à huit chiffres, leur
libellé, leur unité statistique, et quinze colonnes de taux.

ASSIETTE DU DROIT DE DOUANE — ÉTABLIE, et par la même autorité que le tarif.
Customs Act 1988 (mra.mu/download/CustomsAct1988.pdf) :

  s.18(1) « Where duty is leviable on goods by reference to their value, the
           value of the goods shall be the transaction value of the goods as
           determined in accordance with section 18A. »
  s.18A   « The transaction value of the goods shall be the price actually paid
           or payable for the goods when sold for export to an importer in
           Mauritius […] and shall in addition include — (a) all costs, charges
           and expenses incidental to the sale contract and delivery of those
           goods; and (b) the loading charges, freight, insurance and other
           charges and expenses in respect of those goods as may be prescribed »

Prix payé + fret + assurance + mise à bord : c'est le CIF.

ASSIETTE DE LA TVA — ÉTABLIE elle aussi, et elle n'est PAS « CIF + droit ».
Value Added Tax Act 1998 (mra.mu/download/VATAct_Proclamation_38_2013.pdf), s.13
« Value of imported goods » :

  « The value shall, in respect of goods imported by any person, be the sum of –
    (a) the customs value of the goods; (b) the customs duty and excise duty
    payable on the goods; (c) the MID levy; (d) the CO2 levy; and (e) the levy
    on energy consumption. »

L'ACCISE ENTRE DONC DANS L'ASSIETTE DE LA TVA. Le profil générique du socle y
posait « CIF+DD », qui l'omet : sur les 717 positions soumises à accise, la TVA
aurait été sous-facturée. L'assiette retenue est « CIF+DD+EXC ».
Réserve portée : les trois prélèvements (c), (d) et (e) ne sont pas collectés.
Là où ils s'appliquent, l'assiette servie est donc minorée, et c'est dit plutôt
que comblé.

CE QUI N'EST PAS ÉTABLI, ET QUI EST DONC DÉCLARÉ. L'assiette de l'ACCISE
elle-même n'est énoncée ni par le tarif, ni par le Customs Act, ni par le VAT
Act. Elle est portée SANS assiette — donc non liquidable — plutôt que posée de
mémoire. Conséquence assumée : sur une position soumise à accise, la TVA repose
sur un composant que le socle ne sait pas chiffrer, et le moteur la déclare
incomplète au lieu de servir un montant minoré.

QUATRE PIÈGES DU DOCUMENT, tous relevés en le lisant.

1. LA CELLULE VIDE N'EST PAS UN ZÉRO. La colonne Excise est vide sur 5 599
   positions et porte un taux sur 520 — dont 173 à 0 %. Vide veut dire « non
   soumis à accise », zéro veut dire « soumis, au taux nul ». Les confondre
   ferait disparaître 173 taux publiés, ou en inventerait 5 599.

2. LA TVA PORTE UN MARQUEUR D'EXONÉRATION. 287 positions portent « EXM » (ou
   « EX M ») au lieu d'un nombre : le tarif les déclare exonérées. C'est une
   donnée, pas une lacune ; le libellé brut est conservé à côté du taux.

3. LA COLONNE « HEADING » N'EST PAS TOUJOURS LÀ, et un indice fixe se décale
   donc silencieusement. Page 41 la ligne s'ouvre sur une cellule vide et le
   code SH est en deuxième position ; page 234 — tout le chapitre 30, les
   produits pharmaceutiques — elle s'ouvre DIRECTEMENT sur le code. Deux mises
   en page différentes produisent la même largeur de ligne : lire par indice
   fixe faisait perdre les chapitres 30, 44, 68 et 97 en entier. Les colonnes
   sont donc repérées par rapport à LA POSITION RÉELLE DU CODE, et l'organisme
   est pris comme la dernière cellule non vide au-delà des taux.

4. UN TAUX SPÉCIFIQUE REPLIÉ SUR DEUX LIGNES FAIT SCINDER SA COLONNE, et tout
   ce qui suit se décale d'un cran : sur 2701.11.00 (anthracite) on lit
   « 0 | 0 | 30 cents per kg | 15 » là où l'on attend
   « General | Excise | VAT | COMESA I ». Appliquer le plan facturerait
   « 30 cents per kg » de TVA et 15 % de préférence COMESA.
   Ces lignes sont reconnues par une règle tirée de la source elle-même : la
   TVA mauricienne est ad valorem (page 12 : « % | percent ad valorem ») ou
   porte « EXM » — jamais un taux spécifique. Une cellule de TVA qui porte
   « 30 cents per kg » dénonce donc le décalage. Ces positions sont émises SANS
   TAUX et signalées, jamais devinées.

4. CERTAINS « TAUX » SONT DES CONTINGENTS. Les colonnes INDIA et UAE portent
   « 300 tons @ 0% duty », « 1,000 Kg at 5% duty » : un taux sous quota, que ce
   moteur ne sait pas liquider faute de connaître le volume déjà imputé. Émis
   avec leur libellé, sans taux.

LA COLONNE « AGENCY » EST UNE FORMALITÉ, PAS UN TAUX. 3 166 positions nomment
l'organisme qui délivre le document exigé — Food Import Unit, Dangerous Chemicals
Control Board, Pharmacy Board, National Plant Protection Office… Sa légende est
LUE À LA PAGE 11 du tarif, jamais recopiée de mémoire, et la collecte échoue si
elle n'y est plus. Distinction tenue : 537 positions portent « MIC for Export
under AGOA », qui est une formalité D'EXPORTATION ; la servir comme une exigence
à l'importation ferait réclamer un document que l'importateur n'a pas à produire.

Le plafond de pages du collecteur précédent (700 sur 807) est retiré : la
dernière position du tarif se trouve page 802.
"""

import hashlib
import json
import logging
import re
import sys
from datetime import date
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pymupdf

logger = logging.getLogger(__name__)

PDF_URL = "https://www.mra.mu/download/TariffInf130826.pdf"
ACTE_URL = "https://www.mra.mu/download/CustomsAct1988.pdf"
DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "crawled"

RX_HS8 = re.compile(r"^\d{4}\.\d{2}\.\d{2}$")
RX_EXONERE = re.compile(r"^ex\s*m$", re.I)

# Indices valables pour les largeurs 19, 20 et 22 — vérifiés cellule à cellule.
RX_EXPORT = re.compile(r"for\s+export", re.I)
# Décalages par rapport à la cellule qui porte le code SH.
D_DESC, D_UNIT, D_GENERAL, D_EXCISE, D_VAT = 1, 2, 3, 4, 5
D_PREF_DEBUT = 6          # douze colonnes préférentielles, puis l'organisme
NB_PREFERENTIELS = 12

# Dans l'ordre des colonnes du tarif, à partir de la TVA.
PREFERENTIELS: Tuple[Tuple[str, str], ...] = (
    ("COMESA_I", "COMESA Group I"),
    ("COMESA_II", "COMESA Group II"),
    ("SADC", "SADC"),
    ("IOC", "Indian Ocean Commission"),
    ("INDE", "India"),
    ("PAKISTAN", "Pakistan"),
    ("UE", "European Community"),
    ("TURKIYE", "TÜRKIYE"),
    ("UK", "United Kingdom"),
    ("CHINE", "China"),
    ("ZLECAF", "AfCFTA"),
    ("EAU", "United Arab Emirates"),
)


def lire_legende_agences(doc) -> Dict[str, str]:
    """Lit la table « ABBREVIATIONS AND SYMBOLS » des organismes, dans le tarif."""
    for index in range(min(20, doc.page_count)):
        texte = doc[index].get_text()
        if "ABBREVIATIONS AND SYMBOLS" not in texte:
            continue
        lignes = [x.strip() for x in texte.splitlines() if x.strip()]
        legende: Dict[str, str] = {}
        for i, ligne in enumerate(lignes):
            m = re.match(r"^([A-Z][A-Za-z]{1,5})\s{2,}(.+)$", ligne)
            if m:
                legende[m.group(1)] = m.group(2).strip()
                continue
            # Sigle seul, intitulé sur la ligne suivante.
            if re.match(r"^[A-Z][A-Za-z]{1,5}$", ligne) and i + 1 < len(lignes):
                suite = lignes[i + 1]
                if not re.match(r"^[A-Z][A-Za-z]{1,5}$", suite) and len(suite) > 6:
                    legende.setdefault(ligne, suite)
        if len(legende) >= 15:
            return legende
    raise SystemExit(
        "Collecte refusée : la légende des organismes est introuvable dans le "
        "tarif. Elle n'est pas recopiée de mémoire."
    )


def lire_agences(cellule: Any, legende: Dict[str, str]) -> List[Dict]:
    """Rend les organismes délivrant le document exigé, portée distinguée."""
    brut = re.sub(r"\s+", " ", str(cellule or "")).strip()
    if not brut or brut in ("0", "-"):
        return []
    # La portée se juge SEGMENT PAR SEGMENT. « DVS (MIC for Export under AGOA) »
    # porte deux choses : une exigence à l'importation (DVS) et une formalité
    # d'exportation (MIC). Marquer toute la cellule d'après la parenthèse ferait
    # disparaître l'exigence d'import qui la précède.
    segments = []
    reste = brut
    for parenthese in re.findall(r"\(([^)]*)\)", brut):
        if parenthese.strip():
            segments.append(parenthese.strip())
        reste = reste.replace(f"({parenthese})", " ")
    segments = [x.strip() for x in re.split(r"[+&]", reste) if x.strip()] + segments
    sigles = segments
    sorties: List[Dict] = []
    for morceau in sigles:
        # « DCC B » et « DCCB » sont le même organisme : le retour à la ligne du
        # tarif ne doit pas produire deux sigles.
        compact = re.sub(r"\s+", "", morceau)
        sigle = ""
        for candidat in sorted(legende, key=len, reverse=True):
            if compact.upper().startswith(candidat.upper()):
                sigle = candidat
                break
        if not sigle:
            cle = re.match(r"^([A-Za-z]{2,6})", compact)
            sigle = cle.group(1) if cle else ""
        sorties.append({
            "sigle": sigle,
            "organisme": legende.get(sigle),
            "portee": "EXPORTATION" if RX_EXPORT.search(morceau) else "IMPORTATION",
            "verbatim": morceau,
            "colonne_source": "Agency",
        })
    return sorties


def lire_taux(cellule: Any) -> Tuple[Optional[float], str, Optional[str]]:
    """Rend (taux, libellé brut, motif de non-lecture).

    Une cellule VIDE rend (None, "", "CELLULE_VIDE") — absence.
    Un zéro publié rend (0.0, "0", None) — donnée.
    """
    brut = re.sub(r"\s+", " ", str(cellule or "")).strip()
    if not brut:
        return None, "", "CELLULE_VIDE"
    if RX_EXONERE.match(brut):
        return 0.0, brut, None
    try:
        return float(brut), brut, None
    except ValueError:
        pass
    if re.search(r"\b(ton|tons|kg)\b.*\bduty\b", brut, re.I):
        return None, brut, "TAUX_SOUS_CONTINGENT"
    return None, brut, "TAUX_SPECIFIQUE_NON_AD_VALOREM"


def extraire(chemin: Path) -> Tuple[List[Dict], Dict[str, int]]:
    doc = pymupdf.open(chemin)
    legende = lire_legende_agences(doc)
    positions: Dict[str, Dict] = {}
    stats = {
        "pages": doc.page_count,
        "lignes_decalees_ecartees": 0,
        "accise_non_soumis": 0,
        "tva_exoneree": 0,
        "taux_sous_contingent": 0,
        "taux_specifiques": 0,
        "organismes_legende": len(legende),
        "positions_avec_formalite": 0,
        "formalites_d_exportation": 0,
    }

    for index in range(doc.page_count):
        try:
            tables = list(doc[index].find_tables())
        except Exception:  # une page sans grille lisible n'est pas une erreur
            continue

        for table in tables:
            try:
                lignes = table.extract()
            except Exception:
                continue

            for ligne in lignes:
                ancre = None
                for j, cellule in enumerate(ligne):
                    if RX_HS8.match(re.sub(r"\s+", "", str(cellule or ""))):
                        ancre = j
                        break
                if ancre is None:
                    continue
                national = re.sub(r"\s+", "", str(ligne[ancre])).replace(".", "")
                if national in positions:
                    continue

                def cel(decalage):
                    k = ancre + decalage
                    return ligne[k] if k < len(ligne) else None

                designation = re.sub(r"\s+", " ", str(cel(D_DESC) or "")).strip()
                unite = re.sub(r"\s+", " ", str(cel(D_UNIT) or "")).strip()

                _, tva_brut_test, tva_motif_test = lire_taux(cel(D_VAT))
                decalee = (
                    len(ligne) < ancre + D_PREF_DEBUT + NB_PREFERENTIELS
                    or tva_motif_test in (
                        "TAUX_SPECIFIQUE_NON_AD_VALOREM", "TAUX_SOUS_CONTINGENT"
                    )
                )
                if decalee:
                    # Colonnes décalées : on garde la position et son libellé,
                    # on refuse ses taux. Un manque nommé, jamais un taux faux.
                    stats["lignes_decalees_ecartees"] += 1
                    positions[national] = _position(
                        national, designation, unite, [], [],
                        gaps=["COLONNES_DECALEES_TAUX_NON_LUS"], page=index + 1,
                        agences=[],
                    )
                    continue

                taxes: List[Dict] = []
                gaps: List[str] = []

                dd, dd_brut, dd_motif = lire_taux(cel(D_GENERAL))
                taxes.append({
                    "code": "DD",
                    "name": "Customs duty (General rate)",
                    "name_fr": "Droit de douane (colonne « General »)",
                    "rate_pct": dd,
                    "raw_value": dd_brut,
                    "base": "CIF",
                    "base_source": "Customs Act 1988, s.18(1) et s.18A",
                    "source": "mra.mu — Customs Tariff Schedules (HS 2022)",
                })
                if dd is None:
                    gaps.append(f"DD_{dd_motif}")

                exc, exc_brut, exc_motif = lire_taux(cel(D_EXCISE))
                if exc_motif == "CELLULE_VIDE":
                    stats["accise_non_soumis"] += 1
                else:
                    if exc_motif:
                        stats["taux_specifiques"] += 1
                    taxes.append({
                        "code": "EXC",
                        "name": "Excise duty",
                        "name_fr": "Droit d'accise",
                        "rate_pct": exc,
                        "raw_value": exc_brut,
                        "base": None,
                        "base_source": None,
                        "note": "Assiette de l'accise non établie par le tarif, "
                                "le Customs Act 1988 ni le VAT Act 1998 — non "
                                "liquidable en l'état.",
                        "source": "mra.mu — Customs Tariff Schedules (HS 2022)",
                    })

                tva, tva_brut, tva_motif = lire_taux(cel(D_VAT))
                exoneree = bool(RX_EXONERE.match(tva_brut))
                if exoneree:
                    stats["tva_exoneree"] += 1
                if tva_motif != "CELLULE_VIDE":
                    taxes.append({
                        "code": "TVA",
                        "name": "Value Added Tax",
                        "name_fr": "Taxe sur la valeur ajoutée",
                        "rate_pct": tva,
                        "raw_value": tva_brut,
                        "exoneration_au_tarif": exoneree,
                        "base": "CIF+DD+EXC",
                        "base_source": "Value Added Tax Act 1998, s.13",
                        "note": "VAT Act 1998 s.13 : valeur en douane + droit de "
                                "douane + accise, plus les MID, CO2 et energy "
                                "levies — ces trois prélèvements ne sont pas "
                                "collectés, l'assiette servie est donc minorée "
                                "là où ils s'appliquent.",
                        "source": "mra.mu — Customs Tariff Schedules (HS 2022)",
                    })

                preferences: List[Dict] = []
                for rang, (regime, libelle) in enumerate(PREFERENTIELS):
                    taux, brut, motif = lire_taux(cel(D_PREF_DEBUT + rang))
                    if motif == "CELLULE_VIDE":
                        continue
                    if motif == "TAUX_SOUS_CONTINGENT":
                        stats["taux_sous_contingent"] += 1
                    preferences.append({
                        "regime": regime,
                        "regime_name_fr": libelle,
                        "rate_pct": taux,
                        "raw_value": brut,
                        "non_liquidable": motif,
                        "colonne_source": libelle,
                        "source": "mra.mu — Customs Tariff Schedules (HS 2022)",
                    })

                # L'organisme est la dernière cellule non vide après les taux.
                reste = [
                    str(c or "").strip()
                    for c in ligne[ancre + D_PREF_DEBUT + NB_PREFERENTIELS:]
                ]
                brut_agence = next((c for c in reversed(reste) if c), "")
                agences = lire_agences(brut_agence, legende)
                if agences:
                    stats["positions_avec_formalite"] += 1
                    if any(a["portee"] == "EXPORTATION" for a in agences):
                        stats["formalites_d_exportation"] += 1

                positions[national] = _position(
                    national, designation, unite, taxes, preferences,
                    gaps=gaps, page=index + 1, agences=agences,
                )

    return list(positions.values()), stats


def _position(national, designation, unite, taxes, preferences, gaps, page,
              agences) -> Dict:
    return {
        "national_code": national,
        "hs6": national[:6],
        "chapter": national[:2],
        "heading": f"{national[:4]}.{national[4:6]}",
        "statistical_unit": unite,
        "designation": {"en": designation, "fr": "", "verbatim": designation},
        "taxes": taxes,
        "preferential_rates": preferences,
        "formalities": agences,
        "restrictions": [],
        "source_gaps": gaps,
        "page_source": page,
        "source": "mra.mu — Customs Tariff Schedules (Integrated Tariff), HS 2022",
        "source_url": PDF_URL,
    }


def construire(chemin: Path) -> Dict:
    positions, stats = extraire(chemin)
    if len(positions) < 5000:
        raise SystemExit(
            f"Collecte refusée : {len(positions)} positions lues, moins de 5 000. "
            "Un tarif amputé ne vaut pas mieux qu'une moyenne."
        )
    empreinte = hashlib.sha256(chemin.read_bytes()).hexdigest()
    codes = sorted({t["code"] for p in positions for t in p["taxes"]})
    return {
        "country": "MUS",
        "country_name": "Maurice",
        "calculation_rules": {
            "order": ["DD", "EXC", "TVA"],
            "bases": {
                "DD": {"basis": "CIF", "type": "ad_valorem"},
                "TVA": {"basis": "CIF+DD+EXC", "type": "ad_valorem"},
            },
            "source": (
                "Customs Tariff Schedules (Integrated Tariff) HS 2022, MRA Customs, "
                "position par position — remplace la moyenne SH6 WITS/UNCTAD-TRAINS. "
                "Assiette du droit établie par le Customs Act 1988, s.18(1) et s.18A "
                "(valeur transactionnelle + fret + assurance + mise à bord = CIF). "
                "Assiette de la TVA établie par le VAT Act 1998, s.13 : valeur en "
                "douane + droit de douane + ACCISE (+ MID, CO2 et energy levies, non "
                "collectés et déclarés comme tels). L'assiette de l'accise n'est "
                "établie par aucun de ces textes : elle est portée sans assiette, donc "
                "non liquidable, plutôt que supposée."
            ),
        },
        "source": "mra.mu (Customs Tariff Schedules, HS 2022, as at 13 August 2026)",
        "source_url": PDF_URL,
        "source_legal": ACTE_URL,
        "source_quality": "crawled_authentic",
        "source_sha256": empreinte,
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
        print(f"usage: {sys.argv[0]} <chemin du PDF téléchargé depuis {PDF_URL}>")
        return 2
    donnees = construire(Path(sys.argv[1]))
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    sortie = DATA_DIR / "MUS_tariffs.json"
    sortie.write_text(
        json.dumps(donnees, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    s = donnees["stats"]
    logger.info(
        "MUS : %s positions, %s chapitres, codes %s",
        s["total_positions"], s["chapters_covered"], ",".join(s["unique_tax_codes"]),
    )
    logger.info(
        "  accise non soumise %s | TVA exonérée %s | contingents %s | "
        "spécifiques %s | lignes décalées écartées %s",
        s["accise_non_soumis"], s["tva_exoneree"], s["taux_sous_contingent"],
        s["taux_specifiques"], s["lignes_decalees_ecartees"],
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
