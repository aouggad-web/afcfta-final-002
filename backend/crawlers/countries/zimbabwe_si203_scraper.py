#!/usr/bin/env python3
"""Tarif douanier du Zimbabwe — Statutory Instrument 203 of 2022.

Source : Customs and Excise (Tariff) Notice, 2022, pris par le ministre des
Finances en vertu de la section 225 du Customs and Excise Act [Chapter 23:02].
C'est le TEXTE RÉGLEMENTAIRE lui-même, 1 162 pages, et non une compilation.
Il abroge et remplace le Statutory Instrument 53 of 2017.

Remplace la moyenne SH6 WITS/UNCTAD-TRAINS qui servait 5 388 positions sans
aucune désignation.

ASSIETTE — ÉTABLIE, et c'est le CIF.
Customs and Excise Act [Chapter 23:02] :
  s.106(1) « the value for duty purposes of any imported goods shall be the
            transaction value of the goods, that is to say, the price actually
            paid or payable for the goods when sold for export to Zimbabwe,
            adjusted in terms of section one hundred and thirteen »
  s.113(2)(c) ajoute « the cost of freight and insurance from the place where
            the goods were placed on board the means of transport by which they
            were removed to Zimbabwe to the place of importation in Zimbabwe »
Prix payé + fret + assurance jusqu'au lieu d'importation : c'est le CIF.

LA RÈGLE DU « or » EST ÉNONCÉE PAR LE TEXTE, et c'est ce qui change tout.
Page 13 du SI, dispositions préliminaires :
  « When a rate of duty in any column of Part II in respect of any goods
    consists of two parts separated by the word "or", each part shall be deemed
    to be a separate and complete rate of duty, and THE RATE OF DUTY YIELDING
    THE HIGHER AMOUNT OF DUTY SHALL BE APPLICABLE in respect of such goods. »
Un droit « 40% or US$1.50/kg » est donc LIQUIDABLE, selon la règle
LE_PLUS_ELEVE. C'est l'exact contraire du tarif sud-africain, dont la même
forme reste REFUSÉE parce qu'aucun texte n'y dit laquelle des deux composantes
s'applique. La différence n'est pas un choix : elle est dans les textes.
Le même passage énonce que « the duties expressed as percentage rates shall be
ad valorem duties ».

DEUX COLONNES, ET ELLES DISENT LA MÊME CHOSE.
Le SI réserve la colonne M.F.N. aux marchandises originaires des parties
contractantes du GATT et des partenaires liés par une clause de la nation la
plus favorisée ; la colonne General vaut pour tout le reste. MESURÉ : sur les
6 637 positions, les deux colonnes portent le MÊME taux — zéro divergence.
C'est M.F.N. qui est servi, parce que c'est le régime applicable aux membres de
l'OMC et aux États parties de la ZLECAf ; General est conservé en regard, avec
sa condition, et la concordance est vérifiée position par position à la
collecte : un écart futur serait signalé, non moyenné.

SIX PIÈGES DU DOCUMENT, tous relevés en le lisant.

1. AUCUN FILET DE TABLEAU. `find_tables()` ne rend rien sur ce PDF : les
   colonnes sont posées à la position, sans bordure. L'extraction se fait donc
   par coordonnées.

2. LES COLONNES NE SONT PAS AU MÊME ENDROIT D'UNE PAGE À L'AUTRE. L'en-tête
   « General » se trouve à x=387 sur 803 pages, mais à 382, 386, 384, 383 ou
   374 sur les autres ; « M.F.N. » à 452 ou 454. Des fenêtres figées se
   trompent de colonne — c'est ce qui faisait apparaître 119 fausses
   divergences entre les deux. CHAQUE PAGE EST DONC CALIBRÉE SUR SON PROPRE
   EN-TÊTE ; les 60 pages qui n'en portent pas retombent sur le calibrage
   dominant.

3. UN TAUX SE REPLIE SUR DEUX LIGNES. Sur 0206.10.00, la première porte
   « 40% or » et la suivante « US$1.50/kg ». Lu ligne par ligne, on servirait
   « 40 % » — c'est-à-dire la composante la plus faible, présentée comme le
   droit entier. Une position est donc prolongée par les bandes qui la suivent
   TANT QU'AUCUN nouveau code n'apparaît.

4. LE TEXTE DE LA DÉSIGNATION DÉBORDE DANS LES COLONNES DE TAUX. Un libellé
   long empiète au-delà de la frontière, et « CHILLED OR » se lisait comme
   l'opérateur « or ». Le taux est donc reconstruit par GRAMMAIRE — pourcentage,
   montant en US$ par unité, mot « Excise », reliés par « or » ou « + » — et
   tout le reste est écarté.

5. LE CODE EST CENTRÉ VERTICALEMENT DANS SA LIGNE. Quand la ligne tient sur
   deux lignes de texte, le code tombe sur la SECONDE. Ancrer la position sur
   le code la faisait donc commencer une ligne trop bas, et sa première ligne —
   désignation ET début du taux — allait grossir la position PRÉCÉDENTE. Relevé
   page 437 : 4011.20.10 se servait « 15% + US$5.00/Kg », c'est-à-dire le droit
   de sa voisine 4011.20.90, laquelle se servait sans aucun taux. Un droit faux,
   et silencieux. Un code sans taux SUR SA BANDE est reconnu pour ce qu'il est —
   un code centré — et sa ligne lui est rendue.

6. LA SOURCE ÉCRIT NEUF CODES DE TRAVERS : « 9608.9900 » sans un de ses points,
   « 5113. 00.00 » avec une espace. N'accepter que la forme canonique les
   faisait disparaître en silence, et une position absente se lit comme une
   position qu'on n'a pas.

CONTRÔLE INTERNE DU DOCUMENT. Le tarif énonce chaque taux DEUX FOIS, en General
et en M.F.N. Après calibrage et grammaire, les deux lectures coïncident sur
6 637 positions sur 6 637, et aucune position n'est servie sans désignation ni
sans taux lu.

« EXCISE » EST UNE INDISPONIBILITÉ, PAS UN ZÉRO. 116 positions portent le mot
« Excise » dans leur colonne de droits — seul (« Excise »), ou en cumul
(« 95% + Excise »). L'accise est due, mais son taux n'est PAS porté par cette
notice : il relève du tarif d'accise. La ligne est donc émise SANS TAUX, avec
son motif — la traiter comme un zéro exonérerait des alcools et des tabacs.

LES MONTANTS SONT EN DOLLARS DES ÉTATS-UNIS. Le SI le précise : un droit
libellé en US$ « shall be payable in Zimbabwe dollars at the prevailing customs
exchange rate ». La devise est donc portée telle quelle ; si la valeur en douane
est servie dans une autre monnaie, le moteur réclame le taux de change au lieu
de comparer deux monnaies.
"""

import collections
import hashlib
import json
import logging
import re
import sys
from datetime import date
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pymupdf

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "crawled"
SOURCE = "Statutory Instrument 203 of 2022 — Customs and Excise (Tariff) Notice"
SOURCE_ACTE = "Customs and Excise Act [Chapter 23:02], s.106(1) et s.113(2)(c)"

#: Le code d'une sous-position, tel que le tarif l'écrit — et tel qu'il lui
#: arrive de l'écrire de travers. Neuf positions sur 6 637 omettent un point
#: (« 9608.9900 » pour 9608.99.00) et une intercale une espace
#: (« 5113. 00.00 »). N'accepter que la forme canonique les faisait disparaître
#: en silence : une position absente n'est pas une position à zéro, mais elle
#: se lit pareil pour qui la cherche. Les deux formes sont donc reconnues, et
#: `_code_national` les ramène à leurs huit chiffres.
RX_CODE = re.compile(r"^\d{4}\.(?:\d{2}\.\d{2}|\d{4})$")
RX_CODE_TRONQUE = re.compile(r"^\d{4}\.$")


def _code_national(brut: str) -> str:
    return re.sub(r"\D", "", brut)
#: La grammaire d'un taux zimbabwéen, et rien d'autre.
_PCT = r"\d+(?:\.\d+)?\s*%"
_MONTANT = r"US\$\s*\d+(?:[.,]\d+)?\s*/\s*(?:\d+\s+)?[A-Za-z]+"
RX_TERME = re.compile(rf"(?:{_PCT}|{_MONTANT}|Excise)", re.I)
RX_OPERATEUR = re.compile(r"\b(or)\b|(\+)")
RX_MONTANT_SEUL = re.compile(
    r"US\$\s*(\d+(?:[.,]\d+)?)\s*/\s*((?:\d+\s+)?[A-Za-z]+)", re.I
)

#: Calibrage de repli, pour les 60 pages de barème sans en-tête.
X_GENERAL_DOMINANT, X_MFN_DOMINANT = 387.0, 452.0
MARGE = 15.0          # les valeurs débordent à gauche de leur en-tête
X_CODE = (100.0, 160.0)
X_DESIGNATION_DEBUT = 160.0


def expression_de_taux(brut: str) -> str:
    """Reconstituer l'expression du taux, en écartant ce qui n'en est pas.

    Le texte d'une désignation longue déborde dans la colonne : on ne retient
    que les TERMES du barème et les opérateurs qui les relient.
    """
    texte = " ".join(str(brut or "").split())
    morceaux: List[str] = []
    curseur = 0
    for m in RX_TERME.finditer(texte):
        operateur = RX_OPERATEUR.search(texte[curseur:m.start()])
        if morceaux and operateur:
            morceaux.append("or" if operateur.group(1) else "+")
        elif morceaux:
            break  # deux termes sans opérateur : le second n'appartient pas au taux
        terme = " ".join(m.group(0).split()).replace(" %", "%")
        morceaux.append(re.sub(r"\s*/\s*", "/", terme))
        curseur = m.end()
    return " ".join(morceaux)


def decomposer(expression: str) -> Dict[str, object]:
    """Rendre les composantes d'un taux : ad valorem, spécifique, accise, règle."""
    if not expression:
        return {"motif": "TAUX_NON_LU"}
    ad_valorem: Optional[float] = None
    specifiques: List[str] = []
    accise = False
    regle: Optional[str] = None

    if re.search(r"\bor\b", expression):
        regle = "higher"  # SI 203/2022, p. 13 : le plus élevé des deux s'applique
    for terme in re.split(r"\s+(?:or|\+)\s+", expression):
        t = terme.strip()
        if re.fullmatch(r"Excise", t, re.I):
            accise = True
            continue
        pct = re.fullmatch(_PCT, t, re.I)
        if pct:
            ad_valorem = float(t.replace("%", "").strip())
            continue
        mont = RX_MONTANT_SEUL.fullmatch(t)
        if mont:
            # `lire_specifique` du constructeur attend « montant monnaie/unité ».
            quantite = " ".join(mont.group(2).split()).replace(" ", "")
            specifiques.append(f"{mont.group(1).replace(',', '.')} USD/{quantite}")

    # Onze positions de spiritueux (chapitre 22) portent DEUX composantes
    # spécifiques dans DES UNITÉS DIFFÉRENTES — « US$5.00/L or US$10.00/LAA
    # + Excise » : par litre de produit, ou par litre d'alcool pur. Les
    # départager suppose le titre alcoométrique, que le tarif ne porte pas, et
    # une seule quantité déclarée ne permet pas de calculer les deux. N'en
    # retenir qu'une — la dernière lue — servirait un montant crédible et faux.
    # Le droit est donc porté sans valeur liquidable, avec son verbatim.
    if len(specifiques) > 1:
        return {"motif": "DEUX_COMPOSANTES_SPECIFIQUES_UNITES_DIFFERENTES"}

    return {
        "ad_valorem": ad_valorem,
        "specifique": specifiques[0] if specifiques else None,
        "accise": accise,
        "regle": regle,
        "motif": None,
    }


def _code_de_la_bande(bande):
    """Le code de la sous-position porté par la bande, ou None.

    Reconnaît aussi « 5113. » suivi de « 00.00 », que la source coupe en deux
    mots, et « 9608.9900 », où elle omet un point.
    """
    mots = [m for _, m in sorted(bande.get("code", []))]
    for i, mot in enumerate(mots):
        if RX_CODE.match(mot):
            return _code_national(mot)
        if RX_CODE_TRONQUE.match(mot):
            suite = mots[i + 1] if i + 1 < len(mots) else ""
            if re.fullmatch(r"\d{2}\.\d{2}", suite):
                return _code_national(mot + suite)
    # « 5113. 00.00 » : la fin du code tombe dans la colonne de désignation.
    for i, mot in enumerate(mots):
        if RX_CODE_TRONQUE.match(mot):
            for _, voisin in sorted(bande.get("designation", []))[:1]:
                if re.fullmatch(r"\d{2}\.\d{2}", voisin):
                    return _code_national(mot + voisin)
    return None


def _reprendre_la_ligne_du_dessus(empilees: List[Dict]) -> List[Dict]:
    """Rendre à la position qui suit les bandes qui lui appartiennent.

    `empilees` sont les bandes déjà versées à la position précédente, dans
    l'ordre. On rend la dernière suite de bandes porteuses de taux, avec ce qui
    la suit — et seulement si la position précédente conserve un taux à elle :
    sans cette garde, une position dont le taux tient sur une seule bande se
    ferait dépouiller du sien.
    """
    fin = len(empilees)
    while fin > 0 and not empilees[fin - 1]["general"]:
        fin -= 1
    if fin == 0:
        return []
    debut = fin
    while debut > 0 and empilees[debut - 1]["general"]:
        debut -= 1
    if not any(bloc["general"] for bloc in empilees[:debut]):
        return []
    reprises = empilees[debut:]
    del empilees[debut:]
    return reprises


def _frontieres(mots) -> Tuple[float, float]:
    """Les bornes des deux colonnes de droits, lues sur l'en-tête de LA page."""
    general = [w[0] for w in mots if w[4] == "General"]
    mfn = [w[0] for w in mots if w[4] in ("M.F.N.", "M.F.N")]
    if general and mfn:
        return general[0] - MARGE, mfn[0] - MARGE
    return X_GENERAL_DOMINANT - MARGE, X_MFN_DOMINANT - MARGE


def extraire(chemin: Path) -> Tuple[List[Dict], Dict[str, int]]:
    doc = pymupdf.open(chemin)
    brut: Dict[str, Dict] = {}
    stats = {
        "pages": doc.page_count,
        "pages_calibrees_sur_entete": 0,
        "pages_sans_entete": 0,
        "colonnes_divergentes": 0,
        "taux_non_lus": 0,
        "droits_composes": 0,
        "droits_cumulatifs": 0,
        "accises_sans_taux": 0,
        "specifiques_incomparables": 0,
    }

    for index in range(doc.page_count):
        mots = doc[index].get_text("words")
        if not mots:
            continue
        borne_g, borne_m = _frontieres(mots)
        porte_entete = any(w[4] == "General" for w in mots)
        bandes = collections.defaultdict(lambda: collections.defaultdict(list))
        for x0, y0, _x1, _y1, mot, *_ in mots:
            if X_CODE[0] <= x0 < X_CODE[1]:
                colonne = "code"
            elif X_DESIGNATION_DEBUT <= x0 < borne_g:
                colonne = "designation"
            elif borne_g <= x0 < borne_m:
                colonne = "general"
            elif x0 >= borne_m:
                colonne = "mfn"
            else:
                continue
            bandes[round(y0)][colonne].append((x0, mot))

        # Une position s'ancre sur la bande qui porte son code, et se prolonge
        # par les bandes SANS code qui la suivent : c'est ainsi qu'un taux
        # replié sur deux lignes se reconstitue.
        #
        # MAIS le code est CENTRÉ VERTICALEMENT dans sa ligne. Quand celle-ci
        # tient sur deux lignes de texte, il tombe sur la SECONDE, et la
        # première — désignation ET début du taux — se retrouve rattachée à la
        # position PRÉCÉDENTE. Relevé sur 4011.20.10, qui se servait
        # « 15% + US$5.00/Kg » : le droit de sa voisine 4011.20.90, laquelle se
        # servait sans aucun taux. Un droit faux, et silencieux.
        #
        # La réparation lit le même indice que l'œil : un code sans taux SUR SA
        # BANDE est un code centré, et sa ligne commence plus haut. On lui rend
        # alors la dernière suite de bandes porteuses de taux — et rien de plus,
        # la position précédente devant garder un taux à elle.
        vu_une_position = False
        courant = None
        empilees: List[Dict] = []
        for y in sorted(bandes):
            bande = bandes[y]
            contenu = {
                colonne: [m for _, m in sorted(bande.get(colonne, []))]
                for colonne in ("designation", "general", "mfn")
            }
            code = _code_de_la_bande(bande)
            if code:
                national = code
                if national in brut:
                    courant, empilees = None, []
                    continue
                reprises = []
                if not contenu["general"] and courant is not None:
                    reprises = _reprendre_la_ligne_du_dessus(empilees)
                nouveau = {
                    "designation": [], "general": [], "mfn": [], "page": index + 1,
                }
                for bloc in reprises:
                    for colonne in ("designation", "general", "mfn"):
                        nouveau[colonne] += bloc[colonne]
                brut[national] = nouveau
                courant, empilees = nouveau, list(reprises)
                vu_une_position = True
            if courant is None:
                continue
            for colonne in ("designation", "general", "mfn"):
                courant[colonne] += contenu[colonne]
            empilees.append(contenu)
        if vu_une_position:
            if porte_entete:
                stats["pages_calibrees_sur_entete"] += 1
            else:
                stats["pages_sans_entete"] += 1

    positions: List[Dict] = []
    for national, p in brut.items():
        expr_mfn = expression_de_taux(" ".join(p["mfn"]))
        expr_general = expression_de_taux(" ".join(p["general"]))
        gaps: List[str] = []
        if expr_general and expr_mfn and expr_general != expr_mfn:
            stats["colonnes_divergentes"] += 1
            gaps.append("COLONNES_GENERAL_ET_MFN_DIVERGENTES")

        parts = decomposer(expr_mfn)
        taxes: List[Dict] = []
        if parts.get("motif"):
            gaps.append(parts["motif"])
            if parts["motif"] == "DEUX_COMPOSANTES_SPECIFIQUES_UNITES_DIFFERENTES":
                stats["specifiques_incomparables"] += 1
                note = (
                    "Le droit oppose DEUX montants spécifiques dans des unités "
                    f"différentes (« {expr_mfn} ») : par litre de produit, ou par "
                    "litre d'alcool pur. La règle du plus élevé (SI 203/2022, p. 13) "
                    "suppose de les comparer, ce qui exige le titre alcoométrique — "
                    "que le tarif ne porte pas. Porté sans valeur liquidable : n'en "
                    "retenir qu'une servirait un montant crédible et faux."
                )
            else:
                stats["taux_non_lus"] += 1
                note = ("Taux présent au tarif mais non lu par la collecte — "
                        "déclaré indisponible plutôt que servi faux.")
            taxes.append({
                "code": "DD", "name": "Customs duty (M.F.N. rate)",
                "name_fr": "Droit de douane (colonne « M.F.N. »)",
                "rate_pct": None, "raw_value": "",
                "expression_colonne": expr_mfn,
                "base": "CIF", "base_source": SOURCE_ACTE, "source": SOURCE,
                "note": note,
            })
            if re.search(r"Excise", expr_mfn, re.I):
                # Le « + Excise » de ces lignes est dû, indépendamment du droit
                # de douane que la collecte ne sait pas liquider. Le taire
                # l'exonérerait.
                stats["accises_sans_taux"] += 1
                taxes.append({
                    "code": "EXC", "name": "Excise duty",
                    "name_fr": "Droit d'accise",
                    "rate_pct": None, "raw_value": "Excise",
                    "expression_colonne": expr_mfn,
                    "base": None, "base_source": None, "source": SOURCE,
                    "note": "Le tarif mentionne « Excise » sans en porter le taux "
                            f"(colonne M.F.N. : « {expr_mfn} ») : il relève du "
                            "tarif d'accise. Émise sans taux — la traiter comme "
                            "un zéro exonérerait alcools et tabacs.",
                })
        else:
            if parts["regle"]:
                stats["droits_composes"] += 1
            elif parts["specifique"] and parts["ad_valorem"] is not None:
                stats["droits_cumulatifs"] += 1
            droit = {
                "code": "DD", "name": "Customs duty (M.F.N. rate)",
                "name_fr": "Droit de douane (colonne « M.F.N. »)",
                "rate_pct": parts["ad_valorem"],
                "specific_value": parts["specifique"],
                "raw_value": expr_mfn,
                "compound": bool(parts["regle"]),
                "compound_rule": parts["regle"],
                "specific_currency": "USD" if parts["specifique"] else None,
                "base": "CIF", "base_source": SOURCE_ACTE, "source": SOURCE,
            }
            if parts["regle"]:
                droit["note"] = (
                    "Droit composé dont la RÈGLE EST ÉNONCÉE par le texte : "
                    "SI 203/2022, p. 13 — « the rate of duty yielding the higher "
                    "amount of duty shall be applicable »."
                )
            elif parts["specifique"] and parts["ad_valorem"] is not None:
                droit["note"] = (
                    "Droit cumulatif : les DEUX composantes sont dues "
                    "(« + » et non « or »)."
                )
            taxes.append(droit)

            if parts["accise"]:
                stats["accises_sans_taux"] += 1
                taxes.append({
                    "code": "EXC", "name": "Excise duty",
                    "name_fr": "Droit d'accise",
                    # `raw_value` porte « Excise » SEUL, et non l'expression
                    # entière de la colonne. Y laisser « 5% + Excise » faisait
                    # relire 5 % par le constructeur du socle — le taux du
                    # droit de douane servi comme taux d'accise : un montant
                    # crédible et faux. L'expression entière reste consultable
                    # dans la note.
                    "rate_pct": None, "raw_value": "Excise",
                    "expression_colonne": expr_mfn,
                    "base": None, "base_source": None, "source": SOURCE,
                    "note": "Le tarif mentionne « Excise » sans en porter le taux "
                            f"(colonne M.F.N. : « {expr_mfn} ») : il relève du "
                            "tarif d'accise. Émise sans taux — la traiter comme "
                            "un zéro exonérerait alcools et tabacs.",
                })

        designation = " ".join(" ".join(p["designation"]).split())
        positions.append({
            "national_code": national,
            "hs6": national[:6],
            "chapter": national[:2],
            "heading": f"{national[:4]}.{national[4:6]}",
            "statistical_unit": "",
            "designation": {"en": designation, "fr": "", "verbatim": designation},
            "taxes": taxes,
            "preferential_rates": [],
            "restrictions": [],
            "source_gaps": gaps,
            "colonne_general": expr_general,
            "page_source": p["page"],
            "source": SOURCE,
        })
    return positions, stats


def construire(chemin: Path) -> Dict:
    positions, stats = extraire(chemin)
    if len(positions) < 5000:
        raise SystemExit(
            f"Collecte refusée : {len(positions)} positions lues, moins de 5 000."
        )
    codes = sorted({t["code"] for p in positions for t in p["taxes"]})
    return {
        "country": "ZWE",
        "country_name": "Zimbabwe",
        "calculation_rules": {
            "order": ["DD", "EXC"],
            "bases": {"DD": {"basis": "CIF", "type": "ad_valorem"}},
            "source": (
                "Statutory Instrument 203 of 2022 (Customs and Excise (Tariff) "
                "Notice), colonne M.F.N., position par position — remplace la "
                "moyenne SH6 WITS/UNCTAD-TRAINS. Assiette établie par le Customs "
                "and Excise Act [Chapter 23:02], s.106(1) et s.113(2)(c) : valeur "
                "transactionnelle + fret + assurance jusqu'au lieu d'importation, "
                "soit le CIF. Un droit « X% or US$Y/unité » est liquidé selon la "
                "règle que le texte énonce lui-même (p. 13) : le plus élevé des "
                "deux. L'accise mentionnée sans taux reste sans taux."
            ),
        },
        "source": SOURCE,
        "source_url": None,
        "source_legal": SOURCE_ACTE,
        "source_quality": "crawled_authentic",
        "source_sha256": hashlib.sha256(chemin.read_bytes()).hexdigest(),
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
        print(f"usage: {sys.argv[0]} <chemin du PDF du SI 203 of 2022>")
        return 2
    donnees = construire(Path(sys.argv[1]))
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    (DATA_DIR / "ZWE_tariffs.json").write_text(
        json.dumps(donnees, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    s = donnees["stats"]
    logger.info(
        "ZWE : %s positions, %s chapitres, codes %s",
        s["total_positions"], s["chapters_covered"], ",".join(s["unique_tax_codes"]),
    )
    logger.info(
        "  pages calibrées sur en-tête %s | sans en-tête %s | colonnes divergentes %s",
        s["pages_calibrees_sur_entete"], s["pages_sans_entete"], s["colonnes_divergentes"],
    )
    logger.info(
        "  droits composés (règle énoncée) %s | cumulatifs %s | accises sans taux %s "
        "| spécifiques incomparables %s | taux non lus %s",
        s["droits_composes"], s["droits_cumulatifs"], s["accises_sans_taux"],
        s["specifiques_incomparables"], s["taux_non_lus"],
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
