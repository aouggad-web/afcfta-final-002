#!/usr/bin/env python3
"""Tarif douanier du Malawi — Customs and Excise (Tariffs) (No. 3) Order, 2022.

Source : Malawi Gazette Supplement du 29 juillet 2022, GOVERNMENT NOTICE NO. 30,
pris sous le Customs and Excise Act (Chapter 42:01), version SH 2022. Publie par
la Malawi Revenue Authority, 642 pages. C'est le TEXTE REGLEMENTAIRE lui-meme.

Remplace la moyenne SH6 WITS/UNCTAD-TRAINS qui servait 5 388 positions sans
aucune designation.

LE MALAWI PUBLIE UNE COLONNE ZLECAf, ET C'EST CE QUI DISTINGUE CE TARIF.
Aucun des tarifs integres avant lui — Zimbabwe, Zambie — ne publie de taux
preferentiel ZLECAf dans son instrument legal ; l'extrait mozambicain avait
perdu les colonnes SADC et UE que son bareme porte. Ici la colonne 7A est
introduite par le Govt Notice 31 du 28/05/2021 et definie par le decret.

LA CARTE DES COLONNES EST DANS LE DECRET, PAS DEDUITE DE LA MISE EN PAGE.
Paragraphe 4, page 22 :
  col. 1   numero de position        col. 7A  taux ZLECAf (AfCFTA)
  col. 2   sous-position             col. 8   SADC hors Afrique du Sud
  col. 3   designation               col. 9   SADC, Afrique du Sud seulement
  col. 4   unite de quantite         col. 10  accise
  col. 5   droit de douane           col. 11  TVA
  col. 6   droit de douane           col. 12  Advance Income Tax
  col. 7   taux COMESA

CE QUI SEPARE LES COLONNES 5 ET 6 — la question decisive, et elle est ecrite.
Le paragraphe 4 dit seulement que les deux portent « the rates of customs duty ».
MESURE : elles DIVERGENT sur 3 284 lignes sur 6 399, plus de la moitie du tarif
(15 % contre 10 % sur la viande bovine). Se tromper de colonne donnerait donc un
droit faux sur la majorite des positions.

Le paragraphe 5, page 23, pris en vertu de la section 89 de l'Act, tranche : ce
ne sont pas deux droits cote a cote, mais UN PLEIN DROIT ET SES REMISES.

  « rebates shall be allowed to an extent sufficient to reduce the rates of duty
    set out in COLUMN 5 of Part III to the rates respectively set out in COLUMN 6
    or 7, 7A, 8 or 9 of Part III in respect of goods grown, produced or
    manufactured in any country which is — »

  col. 5  PLEIN DROIT, la base dont les autres sont des remises.
  col. 6  remise pour un pays qui est (i) « Member State » ou « ACP State » au
          sens de la Convention de Lome, (ii) un pays independant du
          Commonwealth, ou (iii) « a Contracting Party of the General Agreement
          on Tariffs and Trade (GATT) ».
          => c'est EN FAIT le taux NPF, et c'est LUI qui est servi comme droit de
          douane : tout membre de l'OMC y a droit, donc tout partenaire commercial
          ordinaire du Malawi. La colonne 5 est conservee a cote, nommee, pour les
          origines qui n'entrent dans aucune de ces categories.

DEUX REGLES D'ORIGINE QUE LE TEXTE ENONCE, ET QUI NE SE DEVINENT PAS.
  — L'AFRIQUE DU SUD EST EXCLUE DE LA COLONNE ZLECAf : « goods imported into
    Malawi from a country that is a State Party to the AfCFTA OTHER THAN REPUBLIC
    OF SOUTH AFRICA ». Une expedition sud-africaine ne beneficie pas du 7A.
  — LE TAUX PREFERENTIEL EST CONDITIONNEL a un « specified country content of not
    less than thirty-five per cent ». Cette condition depend de la marchandise et
    de son certificat d'origine : le collecteur la PORTE sur la ligne, il ne la
    verifie pas. Promettre une preference sans elle serait inventer une
    exoneration.

L'ASSIETTE DU DROIT DE DOUANE — et elle n'est PAS celle de l'OMC.
Customs and Excise Act s.111(2) : « The value of imported goods shall be
determined in accordance with the provisions of SCHEDULE A ». La Schedule A
retient le PRIX NORMAL, la Definition de Bruxelles :
  « The value of any imported goods shall be taken to be the normal price, that
    is to say, the price which they would fetch [...] on a sale in the open
    market between a buyer and a seller independent of each other »,
determine sur les hypotheses que « the goods are delivered to the buyer at the
PORT OR PLACE OF INTRODUCTION INTO MALAWI » et que « the seller bears ALL COSTS,
CHARGES AND EXPENSES incidental to the sale and to the delivery of the goods at
the port or place of introduction, WHICH ARE HENCE INCLUDED in the normal price ».
Par son contenu economique, l'assiette comprend donc prix + fret + assurance
jusqu'au port malawien : c'est le CIF, et c'est ce que le socle sert. Mais la
FORME juridique est une valeur theorique de marche ouvert, non la valeur
transactionnelle : sur une vente entre parties liees, les deux ne donnent pas le
meme montant. Le meme amendement (Act 10 of 2014) a fait passer les EXPORTATIONS
a la valeur transactionnelle et laisse les importations sur le prix normal : ce
n'est donc pas un texte oublie, c'est le choix malawien.

RESERVE PORTEE SUR CHAQUE LIGNE DE DROIT : la consolidation lue s'arrete au
30 juin 2018 (malawilii.org refuse son PDF, 403). Une modification posterieure
n'est pas exclue.

DEUX DEFAUTS DU DOCUMENT, COMPTES ET NON CORRIGES. La couche texte du PDF rend
« Free » tronque en « Fre » quatre fois sur 642 pages, et ecrit une fois « 12,5% »
a la virgule la ou le reste du bareme met un point. Aucun des deux n'est devine :
la cellule reste non lue et la position le declare. Deduire « Free » d'un prefixe
serait servir une franchise que le collecteur n'a pas vue.

TROIS PRELEVEMENTS SONT PORTES SANS ASSIETTE, donc non liquidables : l'accise
(col. 10), la TVA (col. 11) et l'Advance Income Tax (col. 12). Le decret donne
leurs TAUX, pas leur assiette, et aucun texte malawien lu ici ne l'etablit. Les
poser sur CIF de memoire — parce que c'est l'usage ailleurs — fabriquerait un
montant credible et faux. Le moteur les declarera indisponibles, avec leur motif.
"""

import collections
import hashlib
import itertools
import json
import logging
import math
import re
import sys
from datetime import date
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pymupdf

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "crawled"
SOURCE = (
    "Customs and Excise (Tariffs) (No. 3) Order, 2022 (HS 2022 Version) — "
    "Malawi Gazette Supplement du 29 juillet 2022, Government Notice No. 30"
)
SOURCE_URL = (
    "https://www.mra.mw/admin/storage/downloads/"
    "MALAWI_CUSTOMS_AND_EXCISE_(TARIFFS)_ORDER_HS_2022_VERSION_2023-2024_(P).pdf"
)
ACTE_DD = (
    "Customs and Excise Act (Cap. 42:01), s.111(2) et Schedule A — prix normal, "
    "marchandises « delivered to the buyer at the port or place of introduction "
    "into Malawi », le vendeur supportant tous les frais jusque-la"
)
RESERVE_ACTE = (
    "Assiette lue sur la consolidation Laws.Africa arretee au 30 juin 2018 ; une "
    "modification posterieure n'est pas exclue (malawilii.org refuse son PDF, 403)."
)
CONDITION_ORIGINE = (
    "Taux SOUS CONDITION : le paragraphe 5 de l'Order exige un « specified country "
    "content of not less than thirty-five per cent ». Le calculateur ne verifie pas "
    "cette condition — elle depend de la marchandise et de son certificat d'origine."
)

#: Le code d'une sous-position malawienne, avec point final optionnel.
RX_CODE = re.compile(r"^\d{4}\.\d{2}\.\d{2}\.?$")
#: Une POSITION a quatre chiffres — « 02.03 » — ouvre un nouveau libelle sans
#: porter de taux. Rattachee a la sous-position precedente, sa designation venait
#: s'y coller : 0202.30.00 se lisait « Boneless 02.03 Meat of swine ».
RX_POSITION = re.compile(r"^\d{2}\.\d{2}$")
#: Une valeur de droit : pourcentage, ou « Free » qui vaut zero.
RX_PCT = re.compile(r"^(\d+(?:\.\d+)?)\s*%$")
RX_ZERO = re.compile(r"^(free)$", re.I)
#: La colonne TVA ne porte pas toujours un taux : le bareme y ecrit aussi « Zero »
#: (detaxe, VAT Act Second Schedule) et « Exempt » (exoneration, First Schedule).
#: Les deux sont des mentions PUBLIEES, et elles ne disent pas la meme chose :
#: une livraison detaxee est taxee a 0 %, une livraison exoneree n'est pas dans
#: le champ de la taxe. Aucune des deux n'est un taux, et aucune n'est un manque.
RX_MENTION_TVA = re.compile(r"^(zero|exempt)$", re.I)

#: Les neuf colonnes de taux, dans l'ordre ou le decret les enumere, avec le
#: code que le socle leur donne. Les abscisses sont le BORD GAUCHE moyen de la
#: valeur, mesure sur les 556 lignes du document qui portent les neuf valeurs a
#: la fois — donc les seules dont l'affectation soit forcee. L'ecart-type y est
#: de 2,4 unite sur la colonne 5 et de 5,3 sur la colonne 12, pour un pas de
#: 27 : la grille est donc une FORME, pas une position absolue.
COLONNES = [
    ("DD_PLEIN", 342.6, "col. 5 — plein droit"),
    ("DD", 370.3, "col. 6 — droit de douane NPF (parties contractantes du GATT)"),
    ("COMESA", 397.6, "col. 7 — taux COMESA"),
    ("AFCFTA", 422.8, "col. 7A — taux ZLECAf"),
    ("SADC", 450.2, "col. 8 — taux SADC hors Afrique du Sud"),
    ("SADC_ZAF", 477.3, "col. 9 — taux SADC, Afrique du Sud seulement"),
    ("EXC", 502.6, "col. 10 — accise"),
    ("TVA", 528.2, "col. 11 — TVA"),
    ("AIT", 558.7, "col. 12 — Advance Income Tax a l'importation"),
]
GRILLE = [x for _n, x, _l in COLONNES]
#: Rang de la colonne TVA dans la grille. « Zero » et « Exempt » ne se lisent
#: que la : ce sont les mentions des annexes du VAT Act, et aucune autre colonne
#: du bareme n'en porte. C'est ce qui permet de trancher une ligne ou le placement
#: des valeurs hesitait entre l'accise et la TVA.
RANG_TVA = [n for n, _x, _l in COLONNES].index("TVA")
#: Demi-largeur d'une colonne. Le pas mesure entre deux colonnes est d'environ
#: 27 unites : une demi-largeur de 12,5 les separe sans les faire se recouvrir.
DEMI = 12.5
TOLERANCE_Y = 4.0
X_PREMIERE_COLONNE = 325.0
#: La colonne 4 du bareme — l'unite de quantite — tient entre la designation et
#: la premiere colonne de taux. Les points de conduite de la designation la
#: precedent, si bien que l'unite est le dernier mot avant les taux. Le
#: vocabulaire est ferme : le reconnaitre evite de prendre pour une unite le
#: dernier mot d'une designation qui deborde, ou le « 4 » de l'en-tete de colonne.
X_UNITE = 300.0
#: Bord droit de la COLONNE DES CODES. Dans la Partie III, 7 364 codes tombent entre
#: x=60 et x=105 ; les 37 au-dela de 140 sont tous des codes CITES DANS UN TEXTE —
#: « ---Chassis [...] for special conversion into vehicles of subheadings 8704.21.90,
#: 8704.22.10 [...] », p. 457. Sans cette borne, ces citations devenaient des
#: positions, et neuf d'entre elles se servaient avec le droit de la ligne qui les
#: cite : 8704.23.00 rendait « Free » emprunte au chassis de 8706.00.10, et
#: 7321.11.00 rendait le 30 % de la ligne de pieces 7321.90.10.
X_COLONNE_DES_CODES = 140.0
RX_UNITE = re.compile(
    r"^(kg|U|l|m|g|t|tonne|ct|pr|doz|m2|m3"
    r"|[0-9]{1,4}U|kg/[A-Za-z0-9]{1,4}|[A-Za-z0-9]{1,4}/kg)$"
)
#: Seuils de l'affectation par ligne. Ils ont ete regles par un test en
#: LAISSANT-UN-DEHORS : sur chacune des 556 lignes du document qui portent les
#: neuf valeurs — les seules dont l'affectation soit forcee, donc connue — on
#: retire une valeur et on demande a l'affectation de retrouver les huit colonnes
#: restantes, soit 5 004 cas. A ces seuils elle en lit 3 762 et REFUSE les 1 242
#: autres, SANS SE TROMPER UNE SEULE FOIS. Les relacher — en ajoutant une prime
#: au decalage nul, qui porterait la lecture a 4 600 cas — introduisait 30 valeurs
#: fausses : le taux d'une colonne servi sous le nom d'une autre.
ECART_TYPE_MAX = 7.0
DECALAGE_MAX = 14.0
MARGE_DE_DEPARTAGE = 2.0


def lire_valeur(cellule: str) -> Tuple[Optional[float], Optional[str]]:
    """Rendre (taux, motif) pour une cellule de taux.

    « Free » est un ZERO PUBLIE — une franchise, pas une absence. Une cellule
    vide rend un motif : le decret ne dit alors rien de ce prelevement pour
    cette position, et rien n'est suppose.
    """
    brut = (cellule or "").strip()
    if not brut:
        return None, "CELLULE_VIDE"
    if RX_ZERO.match(brut):
        return 0.0, None
    if RX_MENTION_TVA.match(brut):
        # « Zero » est un taux nul publie ; « Exempt » est hors du champ de la
        # taxe, donc pas un taux du tout : le confondre avec 0 % effacerait la
        # difference que le VAT Act etablit entre ses deux annexes.
        return (0.0, None) if brut.lower() == "zero" else (None, "HORS_CHAMP_DE_LA_TVA")
    m = RX_PCT.match(brut)
    if m:
        return float(m.group(1)), None
    return None, "EXPRESSION_NON_LUE"


def _est_valeur(mot: str) -> bool:
    return bool(RX_PCT.match(mot) or RX_ZERO.match(mot) or RX_MENTION_TVA.match(mot))


def _bandes(mots, tolerance: float = TOLERANCE_Y):
    """Regrouper les tokens par ligne VISUELLE.

    Les cellules de taux ne tombent pas toujours sur la bande arrondie du code :
    2 749 lignes sur 7 426 s'en trouvaient separees. Le regroupement se fait donc
    a la tolerance, et la ligne se prolonge ensuite par les bandes sans code.
    """
    groupes: List[Tuple[float, List[Tuple[float, float, str]]]] = []
    for x0, y0, x1, _y1, mot, *_ in sorted(mots, key=lambda w: (w[1], w[0])):
        if groupes and abs(y0 - groupes[-1][0]) <= tolerance:
            groupes[-1][1].append((x0, x1, mot))
        else:
            groupes.append((y0, [(x0, x1, mot)]))
    return [(y, _recoller(sorted(toks))) for y, toks in groupes]


def _recoller(toks) -> List[Tuple[float, str]]:
    """Recoudre les valeurs que l'extraction a coupees en deux.

    « 30% » sort parfois en deux tokens colles, « 3 » puis « 0% ». Le second
    tombe alors dans la bande de sa colonne et s'y lit comme un droit de 0 % :
    la position 0302.49.00 se voyait ainsi servir une franchise au lieu de son
    plein droit de 30 %. On recoud donc deux tokens separes de moins de 4 unites — deux colonnes
    voisines ne le sont jamais de moins de 8 — quand leur
    concatenation, et elle seule, fait un pourcentage.
    """
    recolles: List[Tuple[float, str]] = []
    index = 0
    while index < len(toks):
        x0, x1, mot = toks[index]
        while index + 1 < len(toks):
            suivant_x0, suivant_x1, suivant = toks[index + 1]
            if suivant_x0 - x1 > 4.0 or not RX_PCT.match(mot + suivant):
                break
            mot, x1, index = mot + suivant, suivant_x1, index + 1
        recolles.append((x0, mot))
        index += 1
    return recolles


def _colonnes_de_la_ligne(valeurs: List[Tuple[float, str]]) -> Optional[List[int]]:
    """Rendre, pour chaque valeur de la ligne, l'indice de SA colonne.

    LA GRILLE N'EST PAS A LA MEME PLACE D'UNE LIGNE A L'AUTRE. Sur 529 lignes
    portant les neuf valeurs, 466 tombent a l'abscisse nominale, mais les pages
    452 a 454 — les vehicules automobiles — glissent jusqu'a 24 unites vers la
    gauche, presque une colonne entiere. Comparer une abscisse a la grille
    nominale y lisait donc le taux de la colonne voisine : c'est ainsi qu'un
    droit COMESA de 13 % se servait comme droit de douane.

    Ce qui, en revanche, NE bouge PAS, c'est l'ECART entre deux colonnes. On
    cherche donc la FORME et non la position : parmi les facons de placer les
    valeurs de la ligne dans les neuf colonnes en respectant leur ordre, on
    retient celle dont les ecarts a la grille sont les plus constants, le
    decalage commun etant lu et non suppose.

    Une valeur qui dit « Zero » ou « Exempt » est en revanche RATTACHEE d'office
    a la colonne TVA : ces deux mentions viennent des annexes du VAT Act, aucune
    autre colonne du bareme n'en porte. Sans cette attache, 220 lignes restaient
    refusees parce que le placement hesitait entre servir « Exempt » comme accise
    ou comme TVA.

    La ligne est REFUSEE quand deux placements s'ajustent presque aussi bien :
    un taux d'accise servi comme droit de douane est un chiffre faux, une
    colonne declaree illisible n'est qu'un manque nomme.
    """
    xs = [x for x, _m in valeurs]
    k = len(xs)
    if k == 0:
        return []
    if k > len(GRILLE):
        return None
    if k == len(GRILLE):
        # Les neuf colonnes sont la : l'ordre suffit, il n'y a rien a arbitrer.
        return list(range(k))
    # Une mention du VAT Act ne peut etre que dans la colonne TVA.
    impose = [i for i, (_x, m) in enumerate(valeurs) if RX_MENTION_TVA.match(m)]
    if len(impose) > 1:
        return None
    candidats = []
    for combinaison in itertools.combinations(range(len(GRILLE)), k):
        if impose and combinaison[impose[0]] != RANG_TVA:
            continue
        ecarts = [xs[i] - GRILLE[c] for i, c in enumerate(combinaison)]
        decalage = sum(ecarts) / k
        dispersion = math.sqrt(sum((e - decalage) ** 2 for e in ecarts) / k)
        candidats.append((dispersion, abs(decalage), combinaison))
    if not candidats:
        return None
    candidats.sort()
    dispersion, decalage, combinaison = candidats[0]
    if dispersion > ECART_TYPE_MAX or decalage > DECALAGE_MAX:
        return None
    if len(candidats) > 1 and candidats[1][0] < dispersion + MARGE_DE_DEPARTAGE:
        return None
    return list(combinaison)


def _unite(toks) -> str:
    """L'unite de quantite de la colonne 4, ou la chaine vide.

    Elle est PUBLIEE et elle compte : c'est elle qui dit en quoi une quantite se
    declare. Elle est lue sur 7 234 des 7 373 positions ; ailleurs le dernier mot
    de la zone n'appartient pas au vocabulaire des unites, et rien n'est suppose.
    """
    cands = [m for x, m in toks if X_UNITE < x < X_PREMIERE_COLONNE and m.strip(".")]
    if not cands:
        return ""
    mot = cands[-1].strip(".")
    return mot if RX_UNITE.match(mot) else ""


def _valeurs_de_la_ligne(toks) -> Tuple[Dict[str, str], Optional[str]]:
    """Rendre {nom de colonne: valeur brute}, ou un motif de refus de la ligne.

    Deux valeurs separees de moins d'une demi-colonne ne sont pas arbitrees :
    c'est le signe que deux lignes du bareme se sont fondues a la lecture, et
    rien ne dit laquelle des deux porte le droit.
    """
    valeurs = sorted((x, m) for x, m in toks if x > X_PREMIERE_COLONNE and _est_valeur(m))
    if not valeurs:
        return {}, "AUCUNE_VALEUR_SUR_LA_LIGNE"
    for (x, _m), (suivant, _s) in zip(valeurs, valeurs[1:]):
        if suivant - x < DEMI:
            return {}, "DEUX_VALEURS_DANS_LA_MEME_COLONNE"
    colonnes = _colonnes_de_la_ligne(valeurs)
    if colonnes is None:
        return {}, "COLONNES_NON_IDENTIFIEES"
    return {COLONNES[c][0]: valeurs[i][1] for i, c in enumerate(colonnes)}, None


def _taxe(
    code: str, taux: Optional[float], brut: Optional[str], libelle: str, preferentiel: bool
) -> Dict:
    """Une ligne de prelevement, avec son assiette quand elle est etablie."""
    commun = {
        "code": code,
        "name": libelle,
        "rate_pct": taux,
        "raw_value": brut or "",
        "specific_value": None,
        "source": SOURCE,
    }
    if code in ("DD", "DD_PLEIN"):
        return dict(
            commun,
            base="CIF",
            base_source=ACTE_DD,
            note=(
                "Droit de douane de la colonne 6 — le taux dont beneficie toute "
                "partie contractante du GATT, donc tout membre de l'OMC "
                "(Order, par. 5(a)(iii)). " + RESERVE_ACTE
                if code == "DD"
                else "PLEIN DROIT de la colonne 5. Ce n'est PAS le taux courant : les "
                "colonnes 6 a 9 en sont des remises par origine (Order, par. 5). "
                "Il s'applique aux origines qui n'entrent dans aucune de ces "
                "categories. " + RESERVE_ACTE
            ),
        )
    if preferentiel:
        exclusion = (
            " L'AFRIQUE DU SUD EN EST EXCLUE : « a State Party to the AfCFTA other "
            "than Republic of South Africa » (Order, par. 5(c))."
            if code == "AFCFTA"
            else ""
        )
        return dict(
            commun, base=None, base_source=None, note=libelle + ". " + CONDITION_ORIGINE + exclusion
        )
    # Accise, TVA, Advance Income Tax : le decret donne le TAUX, pas l'assiette.
    return dict(
        commun,
        base=None,
        base_source=None,
        note=(
            f"{libelle}. Le taux est publie par l'Order ; son ASSIETTE n'est "
            "etablie par aucun texte malawien lu ici. Portee sans assiette — la "
            "poser sur le CIF parce que c'est l'usage ailleurs fabriquerait un "
            "montant credible et faux."
        ),
    )


def bornes_de_part_iii(doc) -> Tuple[int, int]:
    """Les pages ou commence et finit la PARTIE III, le tarif de droit commun.

    Le decret ne contient pas QUE le tarif : apres la Partie III viennent la
    Deuxieme annexe (accises), la Quatrieme (droits d'exportation), la Cinquieme
    (surtaxe), la Sixieme (taxe carbone) et une Appendix A de REMISES par
    industrie. Toutes portent des positions SH et des taux, dans des grilles de
    colonnes DIFFERENTES.

    Sans cette borne, la collecte les avalait : 39 positions de l'Appendix A
    entraient au tarif, leurs trois colonnes (« Free Free 16.5% ») tombant sur
    SADC_ZAF, accise et TVA. Un droit faux, tire d'un bareme qui n'est pas celui
    des droits de douane. Les bornes sont donc LUES dans le document, et non
    fixees : une reedition qui decale ses pages reste correctement bornee.

    Le DEBUT n'est pas cherche sur le titre « PART III CUSTOMS DUTIES » : la
    table des matieres, page 16, le porte aussi, et la borne tombait dix pages
    trop haut. Il est cherche sur ce qui ne se trouve QUE dans le bareme — une
    page portant au moins trois positions tarifaires.
    """
    debut = fin = None
    for index in range(doc.page_count):
        mots = doc[index].get_text().split()
        if debut is None:
            if sum(1 for m in mots if RX_CODE.match(m)) >= 3:
                debut = index
            continue
        if re.search(r"SECOND\s+SCHEDULE", " ".join(mots), re.I):
            fin = index
            break
    if debut is None:
        raise SystemExit("Partie III introuvable : le document n'est pas celui attendu.")
    return debut, fin if fin is not None else doc.page_count


def extraire(chemin: Path) -> Tuple[List[Dict], Dict[str, int]]:
    doc = pymupdf.open(chemin)
    debut, fin = bornes_de_part_iii(doc)
    positions: List[Dict] = []
    vus = set()
    stats = {
        "pages": doc.page_count,
        "part_iii_pages": f"{debut + 1}-{fin}",
        "lignes_colonnes_non_identifiees": 0,
        "lignes_deux_valeurs_dans_une_colonne": 0,
        "lignes_sans_aucune_valeur": 0,
        "sans_droit_npf": 0,
        "avec_zlecaf": 0,
        "avec_comesa": 0,
        "avec_sadc": 0,
        "avec_accise": 0,
        "avec_tva": 0,
        "tva_exoneree": 0,
        "avec_ait": 0,
        "plein_droit_different_du_npf": 0,
        "preference_superieure_au_plein_droit": 0,
    }

    for index in range(debut, fin):
        mots = doc[index].get_text("words")
        if not mots:
            continue
        lignes: List[Dict] = []
        for _y, toks in _bandes(mots):
            code = next((m for x, m in toks if x < X_COLONNE_DES_CODES and RX_CODE.match(m)), None)
            mots = [m for x, m in toks if x < X_UNITE and not RX_CODE.match(m)]
            if code:
                lignes.append({"code": code, "toks": list(toks), "desc": mots, "desc_close": False})
            elif lignes:
                # Les taux d'une ligne tombent parfois sous la bande du code : la
                # bande suivante les y apporte, et il faut donc la joindre.
                lignes[-1]["toks"] += toks
                if any(RX_POSITION.match(m) for x, m in toks):
                    # Une POSITION a quatre chiffres ouvre un nouveau libelle : le
                    # precedent s'arrete la, sinon 0202.30.00 se lisait
                    # « Boneless 02.03 Meat of swine ».
                    lignes[-1]["desc_close"] = True
                elif not lignes[-1]["desc_close"]:
                    lignes[-1]["desc"] += mots
        if not lignes:
            continue

        for ligne in lignes:
            national = re.sub(r"\D", "", ligne["code"])
            if len(national) != 8 or national in vus:
                continue
            toks = ligne["toks"]
            gaps: List[str] = []
            taxes: List[Dict] = []
            valeurs: Dict[str, Optional[float]] = {}

            brutes, refus = _valeurs_de_la_ligne(toks)
            if refus:
                stats[
                    {
                        "COLONNES_NON_IDENTIFIEES": "lignes_colonnes_non_identifiees",
                        "DEUX_VALEURS_DANS_LA_MEME_COLONNE": "lignes_deux_valeurs_dans_une_colonne",
                        "AUCUNE_VALEUR_SUR_LA_LIGNE": "lignes_sans_aucune_valeur",
                    }[refus]
                ] += 1
                gaps.append(refus)
            for nom, _x, libelle in COLONNES:
                brut = brutes.get(nom)
                if brut is None:
                    continue
                taux, motif_v = lire_valeur(brut)
                if motif_v == "HORS_CHAMP_DE_LA_TVA":
                    # L'exoneration est une information PUBLIEE : on la porte,
                    # sans taux, plutot que de la laisser passer pour un oubli.
                    stats["tva_exoneree"] += 1
                    gaps.append(f"{nom}_{motif_v}")
                    taxes.append(_taxe(nom, None, brut, libelle, preferentiel=False))
                    continue
                if motif_v:
                    gaps.append(f"{nom}_{motif_v}")
                    continue
                valeurs[nom] = taux
                taxes.append(
                    _taxe(
                        nom,
                        taux,
                        brut,
                        libelle,
                        preferentiel=nom in ("COMESA", "AFCFTA", "SADC", "SADC_ZAF"),
                    )
                )

            if "DD" not in valeurs:
                stats["sans_droit_npf"] += 1
                gaps.append("DROIT_NPF_NON_LU")
            for nom, cle in (
                ("AFCFTA", "avec_zlecaf"),
                ("COMESA", "avec_comesa"),
                ("SADC", "avec_sadc"),
                ("EXC", "avec_accise"),
                ("TVA", "avec_tva"),
                ("AIT", "avec_ait"),
            ):
                if nom in valeurs:
                    stats[cle] += 1
            if "DD_PLEIN" in valeurs and "DD" in valeurs and valeurs["DD_PLEIN"] != valeurs["DD"]:
                stats["plein_droit_different_du_npf"] += 1
            # Le paragraphe 5 de l'Order fait des colonnes 6 a 9 des REMISES du
            # plein droit : aucune ne devrait donc le depasser. Sur 157 lignes le
            # bareme les depasse pourtant — 3004.90.90 porte « Free » aux colonnes
            # 5 et 6 et 2 % au COMESA, 2801.30.00 porte 5 % au NPF et 6 % au
            # COMESA. Verifie page a page, c'est le DOCUMENT qui est ainsi : ces
            # taux sont donc servis tels quels, et la ligne porte l'anomalie pour
            # que personne n'applique une preference pire que le droit commun
            # sans l'avoir vue.
            plein = valeurs.get("DD_PLEIN")
            if plein is not None and any(
                valeurs.get(nom) is not None and valeurs[nom] > plein
                for nom in ("DD", "COMESA", "AFCFTA", "SADC", "SADC_ZAF")
            ):
                stats["preference_superieure_au_plein_droit"] += 1
                gaps.append("PREFERENCE_SUPERIEURE_AU_PLEIN_DROIT")

            # Les points de conduite qui menent la designation jusqu'a la colonne
            # des unites ne font pas partie du libelle.
            designation = " ".join(" ".join(ligne["desc"]).split())
            designation = re.sub(r"(?:\s*\.){2,}", " ", designation)
            designation = re.sub(r"[\s.]*$", "", " ".join(designation.split()))
            vus.add(national)
            positions.append(
                {
                    "national_code": national,
                    "hs6": national[:6],
                    "chapter": national[:2],
                    "heading": ligne["code"][:7],
                    "statistical_unit": _unite(toks),
                    "designation": {
                        "en": designation,
                        "fr": "",
                        "verbatim": designation,
                    },
                    "taxes": taxes,
                    "preferential_rates": [],
                    "restrictions": [],
                    "source_gaps": gaps,
                    "page_source": index + 1,
                    "source": SOURCE,
                }
            )
    return positions, stats


def construire(chemin: Path) -> Dict:
    positions, stats = extraire(chemin)
    codes = sorted({t["code"] for p in positions for t in p["taxes"]})
    return {
        "country": "MWI",
        "country_name": "Malawi",
        "source": SOURCE,
        "source_url": SOURCE_URL,
        "source_legal": (
            "Customs and Excise Act (Cap. 42:01) : s.72 et s.89 (tarif et remises), "
            "s.111(2) et Schedule A (valeur des marchandises importees — prix normal)"
        ),
        "source_quality": "crawled_authentic",
        "source_sha256": hashlib.sha256(chemin.read_bytes()).hexdigest(),
        "extracted_at": date.today().isoformat(),
        "calculation_rules": {
            "order": ["DD", "EXC", "TVA", "AIT"],
            "bases": {"DD": {"basis": "CIF", "type": "ad_valorem", "source": ACTE_DD}},
            "source": (
                "Droit de douane de la COLONNE 6, celle dont beneficie toute partie "
                "contractante du GATT (Order, par. 5(a)(iii)) : c'est le taux NPF. La "
                "colonne 5 est le PLEIN DROIT, conservee a part sous le code DD_PLEIN. "
                "Assiette : prix normal de la Schedule A, marchandises livrees au port "
                "d'introduction au Malawi, tous frais du vendeur inclus — le CIF par "
                "son contenu, la Definition de Bruxelles par sa forme. Accise, TVA et "
                "Advance Income Tax sont portees SANS assiette : le decret en donne le "
                "taux, aucun texte lu n'en donne l'assiette."
            ),
        },
        "stats": dict(
            stats,
            total_positions=len(positions),
            unique_tax_codes=codes,
            chapters_covered=len({p["chapter"] for p in positions}),
        ),
        "sub_positions": positions,
    }


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    if len(sys.argv) < 2:
        print(f"usage: {sys.argv[0]} <chemin du PDF de l'Order MRA>", file=sys.stderr)
        return 2
    donnees = construire(Path(sys.argv[1]))
    s = donnees["stats"]
    if s["total_positions"] < 5000:
        print(
            f"Collecte refusee : {s['total_positions']} positions lues, moins de 5 000.",
            file=sys.stderr,
        )
        return 1
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    (DATA_DIR / "MWI_tariffs.json").write_text(
        json.dumps(donnees, ensure_ascii=False, indent=1), encoding="utf-8"
    )
    logger.info(
        "MWI : %s positions, %s chapitres, codes %s",
        s["total_positions"],
        s["chapters_covered"],
        ",".join(s["unique_tax_codes"]),
    )
    logger.info(
        "  lignes refusees : colonnes non identifiees %s | deux valeurs dans "
        "une colonne %s | aucune valeur %s || sans droit NPF %s",
        s["lignes_colonnes_non_identifiees"],
        s["lignes_deux_valeurs_dans_une_colonne"],
        s["lignes_sans_aucune_valeur"],
        s["sans_droit_npf"],
    )
    logger.info(
        "  ZLECAf %s | COMESA %s | SADC %s | accise %s | TVA %s (dont %s " "exonerees) | AIT %s",
        s["avec_zlecaf"],
        s["avec_comesa"],
        s["avec_sadc"],
        s["avec_accise"],
        s["avec_tva"],
        s["tva_exoneree"],
        s["avec_ait"],
    )
    logger.info(
        "  plein droit different du NPF : %s | preference superieure au plein "
        "droit (anomalie du document) : %s",
        s["plein_droit_different_du_npf"],
        s["preference_superieure_au_plein_droit"],
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
