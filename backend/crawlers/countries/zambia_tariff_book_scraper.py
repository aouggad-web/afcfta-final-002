#!/usr/bin/env python3
"""Tarif douanier de la Zambie — Customs and Excise Tariff, edition janvier 2026.

Source : ZAMBIA REVENUE AUTHORITY, « CUSTOMS AND EXCISE TARIFF », nomenclature
SH de l'OMD, derniere mise a jour janvier 2026, 682 pages. Le document reproduit
la PREMIERE ANNEXE (section 72) de la Customs and Excise Act, et ses
« ADDITIONAL ZAMBIAN RULES » sont celles de l'annexe legale elle-meme : on les
retrouve mot pour mot dans l'Acte publie par le Parlement.

Remplace la moyenne SH6 WITS/UNCTAD-TRAINS qui servait 5 388 positions sans
aucune designation.

TROIS ASSIETTES, TOUTES TROIS ENONCEES PAR LA LOI.

  DD   sur CIF
       Cinquieme annexe (sections 85 et 88), clause 2(1) : « The customs value
       of imported goods shall be their transaction value, that is, the price
       paid or payable for the goods when sold for export to Zambia, adjusted
       in accordance with clause 3 ». La clause 3(1)(a) y ajoute (vii) les
       transports et assurances « until the goods have left the country of
       export » ET (viii) ceux « from the time the goods have left the country
       of export ». Prix paye + fret + assurance jusqu'a l'arrivee : c'est le
       CIF. La regle 2(a) des Additional Zambian Rules confirme l'assiette du
       taux ad valorem : « Rates of duty shown as a percentage, denoted by the
       symbol % are to be calculated as a percentage of the Value For Duty
       Purpose ».

  EXC  sur CIF+DD
       Section 88 : « The value for the purposes of assessing the amount of
       excise duty due on goods imported into Zambia shall be the customs value
       determined in accordance with the Fifth Schedule to this Act AND ANY
       CUSTOMS DUTY PAYABLE on those goods. »

  TVA  sur CIF+DD+EXC
       Value Added Tax Act (Cap. 331), section 10(3) : « The taxable value of
       imported goods shall be determined as for a duty of customs, but shall
       be taken to include THE AMOUNT OF ANY DUTY OR OTHER IMPOST PAYABLE
       OTHERWISE THAN UNDER THIS ACT in respect of the importation. »

LA REGLE DU « or » EST ENONCEE, ET ELLE EST STATUTAIRE. Additional Zambian
Rules, regle 2(b) : « Where the alternative rates of duty are specified, the
rate which yields the greater amount of duty shall apply. » Un droit
« 25% or K1 per Kg » est donc LIQUIDABLE, sous la regle LE_PLUS_ELEVE. C'est le
meme cas qu'au Zimbabwe, et l'exact contraire du tarif sud-africain, dont la
meme forme reste REFUSEE parce qu'aucun texte n'y dit laquelle des deux
composantes s'applique.

LA COLONNE DE TVA NE PORTE PAS UN TAUX, MAIS UNE LETTRE — et c'est la loi qui
la definit, non une legende du document (il n'en publie aucune) :
  S  standard rated   VAT Act s.9(1)-(2) : la TVA est due au « prescribed rate »
  E  exempt           VAT Act, definition : « "exempt importation" means an
                      importation of goods described in the First Schedule »
  Z  zero-rated       VAT Act, definition : « "zero-rated supply" means a supply
                      of goods or services described in the Second Schedule » ;
                      s.9(4) : « the prescribed rate of tax in the case of a
                      zero-rated supply shall be regarded as zero »
Le TAUX standard, lui, n'est pas dans le tarif. La section 9(3) de l'Acte porte
« seventeen and a half per centum, unless the Minister, by statutory order,
determines a lower rate » : le texte consolide donne donc 17,5 %, qui n'est PLUS
le taux en vigueur. Le taux servi est celui qu'enonce l'autorite qui le percoit
— ZRA, VAT Guide : « Currently the Standard rate is 16% » — avec sa reserve :
l'ordre statutaire qui le fixe n'a pas ete identifie. Servir 17,5 % parce que
l'Acte le porte surfacturerait chaque importation zambienne d'un dixieme.

QUATRE PIEGES DU DOCUMENT, tous releves en le lisant.

1. LES CELLULES DE TAUX NE SONT PAS SUR LA BANDE DU CODE. Elles tombent une a
   trois unites plus bas, et jusqu'a vingt quand la designation se replie sur
   plusieurs lignes : sur 0301.91.00 le code est a y=383 et ses taux a y=402.
   Un decoupage par bande arrondie separait donc la ligne de ses propres taux —
   3 987 lignes sur 8 807, soit 45 %, se lisaient sans aucune valeur. Une
   position est donc prolongee par les bandes qui la suivent TANT QU'AUCUN
   nouveau code n'apparait.

2. LES EN-TETES DE COLONNES NE FIGURENT QUE SUR 39 PAGES sur 652, et a des x
   qui varient de 290 a 381. Aucune fenetre figee ne tient, et il n'y a pas
   assez d'en-tetes pour calibrer page par page. CHAQUE PAGE EST DONC CALIBREE
   SUR SES PROPRES DONNEES : les lettres de TVA forment un amas en x tres
   serre (ecart median 0,0 sur la page), qui sert d'ancre ; les colonnes de
   droits se lisent a sa gauche.

3. L'ASTERISQUE N'EST PAS UN TAUX, C'EST UN RENVOI — et la note porte le droit.
   « * » dans la colonne des droits renvoie a une note de bas de page qui
   enonce le droit en entier : « *25% or K1 per Kg whichever is greater. » Lire
   l'asterisque comme un taux absent perdrait ces droits ; l'ignorer les
   perdrait aussi. Les notes sont donc relevees par page et appariees par le
   NOMBRE d'asterisques (*, **, ***). D'autres notes qualifient la TVA
   (« *Eligible for Vat Zero rating », 47 fois).

4. « - » DANS LA COLONNE D'ACCISE N'EST PAS UNE LACUNE, C'EST UN ZERO PUBLIE :
   la position n'est pas soumise a l'accise. De meme « free » vaut zero pour le
   droit de douane. Une cellule VIDE, en revanche, reste une absence. Les trois
   cas sont distingues : `lire_taux` rend un motif, jamais un zero par defaut.

LES MONTANTS SPECIFIQUES SONT EN KWACHA, et le tarif emploie DEUX notations :
« K2.00/l », « K40/ton », « K750/mille » et « KR6,000 », « KR0.85 per kg ». KR
est la notation du kwacha rebase (2013), K celle d'aujourd'hui ; ce sont la meme
unite. Le montant est donc porte avec sa notation d'origine en verbatim, et la
devise normalisee a ZMW — sans jamais convertir.
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
SOURCE = "Customs and Excise Tariff (Customs and Excise Act, First Schedule) — edition janvier 2026"
SOURCE_URL = "https://www.zra.org.zm/wp-content/uploads/2026/08/Customs-Tariff-Book.pdf"
ACTE_DD = "Customs and Excise Act, Cinquieme annexe (s.85, s.88), cl. 2(1) et 3(1)(a)(vii)-(viii)"
ACTE_EXC = "Customs and Excise Act, s.88"
ACTE_TVA = "Value Added Tax Act (Cap. 331), s.10(3)"

#: Le code d'une sous-position zambienne : quatre chiffres, deux, deux — avec un
#: POINT FINAL optionnel, que la source ajoute sur deux positions (« 2807.00.10. »
#: et « 4017.00.30. »). Exiger la forme exacte les faisait disparaitre en
#: silence, avec leurs droits ; le PDF porte 6 753 codes distincts, et il faut
#: les 6 753.
RX_CODE = re.compile(r"^\d{4}\.\d{2}\.\d{2}\.?$")
#: La lettre de la colonne de TVA — l'ancre de la ligne.
RX_TVA = re.compile(r"^([SEZ])(\*+)?$")
#: Un taux ad valorem, ou l'un des deux mots qui valent zero.
RX_PCT = re.compile(r"^(\d+(?:[.,]\d+)?)\s*%$")
RX_ZERO = re.compile(r"^(free|Free|FREE)$", re.I)
#: Un montant specifique en kwacha : « K2.00/l », « KR0.85 per kg », « K40/ton ».
RX_MONTANT = re.compile(
    r"^K\.?R?\s*([\d.,]+)\s*(?:/|per\s+)\s*([A-Za-z/]+)$", re.I
)
#: Le renvoi de note de bas de page, dans une cellule de taux.
RX_RENVOI = re.compile(r"^(\*+)$")
#: Une note de bas de page enoncant un droit compose. La regle y est ecrite.
RX_NOTE_COMPOSEE = re.compile(
    r"^(\*+)\s*(\d+(?:[.,]\d+)?)\s*%\s*or\s*K\.?R?\s*([\d.,]+)\s*"
    r"(?:per\s+|/\s*)([A-Za-z]+(?:\s*/\s*[A-Za-z]+)?)",
    re.I,
)
#: Une note qui qualifie la TVA de la ligne. Relevees sur le document :
#: « Eligible for Vat Zero rating » (47 fois), « are VAT standard rated »,
#: « is VAT Exempt ».
RX_NOTE_TVA = re.compile(
    r"(Eligible for Vat|VAT Zero rating|VAT standard rated|VAT Exempt)", re.I
)
RX_NOTE = re.compile(r"^(\*+)\s*(.*)$")

#: Tolerance de regroupement vertical : deux tokens a moins de cela sont sur la
#: meme ligne visuelle. Mesuree sur le document — l'interligne y est d'environ 10.
TOLERANCE_Y = 4.0
#: L'abscisse dominante de la colonne de TVA, pour les pages ou les lettres sont
#: trop peu nombreuses pour donner une mediane. Elle ne sert qu'a placer l'ancre :
#: les colonnes de droits, elles, sont TOUJOURS calibrees sur les donnees de la
#: page, et une page qui ne se calibre pas voit ses lignes DECLAREES.
X_TVA_DOMINANT = 381.0

#: Le vocabulaire ferme de la colonne « Stat. Unit of Qty », releve sur le
#: document. Il sert a reconnaitre la colonne, pas a la deviner.
UNITES = {
    "kg", "no.", "no", "m2", "m3", "tonne", "litre", "l", "pair", "g", "u",
    "quintal", "mille", "carat", "ct", "dozen", "unit", "units", "-", "km",
    "sq.m", "cu.m", "1000u", "head", "number", "gram", "grams", "kwh", "mt",
}


def lire_taux(cellule: str) -> Tuple[Optional[float], Optional[str], Optional[str]]:
    """Rendre (taux, verbatim, motif) pour une cellule de droit.

    « - » et « free » sont des ZEROS PUBLIES : la position n'est pas soumise, ou
    en est exoneree. C'est une donnee. Une cellule VIDE est une absence, et un
    montant specifique n'est pas un pourcentage : les deux rendent un motif.
    """
    brut = (cellule or "").strip()
    if not brut:
        return None, None, "CELLULE_VIDE"
    if brut in ("-", "_", "–", "—"):
        return 0.0, brut, None
    if RX_ZERO.match(brut):
        return 0.0, brut, None
    m = RX_PCT.match(brut)
    if m:
        return float(m.group(1).replace(",", ".")), brut, None
    if RX_MONTANT.match(brut):
        return None, brut, "MONTANT_SPECIFIQUE"
    if RX_RENVOI.match(brut):
        return None, brut, "RENVOI_EN_NOTE"
    return None, brut, "EXPRESSION_NON_LUE"


def lire_montant(cellule: str) -> Optional[str]:
    """« K2.00/l » -> « 2.00 ZMW/l », la forme que le socle sait decomposer."""
    m = RX_MONTANT.match((cellule or "").strip())
    if not m:
        return None
    unite = m.group(2).lower().strip("/")
    return f"{m.group(1).replace(',', '')} ZMW/{unite}"


def notes_de_la_page(page) -> Dict[str, str]:
    """Les notes de bas de page, indexees par leur nombre d'asterisques.

    Reconstruites sur les LIGNES VISUELLES, et non sur l'ordre des lignes de
    `get_text()` : celui-ci entrelace les cellules du tableau, et la recherche
    d'une continuation y attrapait des designations (« *- Cotton-seed oil and
    its fractions: ») ou un numero de position (« *04.06 »).

    Une note n'est retenue que si elle a la forme d'une note QU'ON SAIT LIRE :
    un droit alternatif (« *15% or KR3.50 per kg whichever is greater ») ou une
    qualification de TVA (« *Eligible for Vat Zero rating »). Le reste n'est pas
    devine.
    """
    notes: Dict[str, str] = {}
    for _y, toks in _bandes(page.get_text("words")):
        if not toks:
            continue
        # L'asterisque est parfois COLLE a la valeur : « *25% or KR4.00 per Kg »
        # se lit en un seul token « *25% ». Exiger un renvoi seul faisait manquer
        # ces notes, et les 120 droits qui y renvoient.
        tete = re.match(r"^(\*+)(.*)$", toks[0][1])
        if not tete:
            continue
        marque = tete.group(1)
        texte = " ".join([tete.group(2)] + [m for _x, m in toks[1:]])
        # « KR3. 50 » : le tarif coupe ses montants en deux tokens.
        texte = re.sub(r"(\d)\.\s+(\d)", r"\1.\2", texte)
        texte = re.sub(r"\s+", " ", texte).strip()
        if not texte:
            continue
        candidate = f"{marque}{texte}"
        if RX_NOTE_COMPOSEE.match(candidate) or RX_NOTE_TVA.search(texte):
            notes.setdefault(marque, candidate)
    return notes


def _bandes(mots, tolerance: float = TOLERANCE_Y):
    """Regrouper les tokens par ligne VISUELLE, et non par y arrondi.

    Les cellules de taux tombent une a trois unites sous la bande du code :
    arrondir les separait de leur propre ligne.
    """
    groupes: List[Tuple[float, List[Tuple[float, str]]]] = []
    for x0, y0, _x1, _y1, mot, *_ in sorted(mots, key=lambda w: (w[1], w[0])):
        if groupes and abs(y0 - groupes[-1][0]) <= tolerance:
            groupes[-1][1].append((x0, mot))
        else:
            groupes.append((y0, [(x0, mot)]))
    return [(y, sorted(toks)) for y, toks in groupes]


def _ancre_tva(mots) -> Optional[float]:
    """L'abscisse de la colonne de TVA, lue sur les donnees de LA page."""
    xs = [w[0] for w in mots if RX_TVA.match(w[4]) and w[0] > 250]
    if len(xs) < 3:
        return None
    xs.sort()
    return xs[len(xs) // 2]


def _est_taux(mot: str) -> bool:
    """Le token a-t-il la FORME d'une valeur de droit ?

    C'est cette grammaire, et non une fenetre en x, qui reconnait une cellule de
    droit : concatener tout ce qui tombe dans une fenetre y faisait entrer le
    NUMERO DE PAGE (« 40% 33 ») et des mots de la designation.
    """
    return bool(
        RX_PCT.match(mot) or RX_ZERO.match(mot) or RX_MONTANT.match(mot)
        or RX_RENVOI.match(mot) or mot in ("-", "_", "–", "—")
    )


def _est_taux_franc(mot: str) -> bool:
    """Une forme qui ne peut PAS apparaitre dans une designation.

    Le tiret en est exclu a dessein : « - Horses: », « -- Other » ouvrent les
    designations du tarif. Le compter comme une valeur empechait 354 pages sur
    682 de se calibrer, et faisait declarer 1 666 positions pour rien.
    """
    return bool(RX_PCT.match(mot) or RX_ZERO.match(mot) or RX_MONTANT.match(mot))


def _colonnes_de_la_page(lignes, ancre: float) -> Optional[Tuple[float, float, float]]:
    """Les abscisses des colonnes unite / DD / accise, lues sur LA page.

    Les en-tetes ne figurent que sur 39 pages sur 652 et les colonnes derivent
    d'une page a l'autre : c'est donc la page qui se calibre sur ses propres
    lignes. On ne retient que les formes franches — pourcentage, « free »,
    montant en kwacha — et la mediane absorbe les quelques lignes ou le droit
    est un renvoi en note.
    """
    xs_dd: List[float] = []
    xs_unite: List[float] = []
    for ligne in lignes:
        # Le renvoi en note OCCUPE la cellule du droit de douane : sur
        # 2203.00.90, « ** » est a 285 et le 40 % d'accise a 317. Ne compter que
        # les formes franches faisait prendre la colonne d'accise pour celle du
        # droit, et la page entiere etait declaree.
        francs = [(x, m) for x, m in ligne["toks"]
                  if x < ancre - 5 and (_est_taux_franc(m) or RX_RENVOI.match(m))]
        if not francs:
            continue
        xs_dd.append(francs[0][0])
        unites = [x for x, m in ligne["toks"]
                  if m.lower() in UNITES and x < francs[0][0] - 5]
        if unites:
            xs_unite.append(unites[-1])
    if len(xs_dd) < 3:
        return None

    def med(valeurs):
        return sorted(valeurs)[len(valeurs) // 2]

    x_dd = med(xs_dd)
    # La colonne d'accise se lit a DROITE du droit de douane — jamais sur lui.
    # Une premiere version prenait la mediane des secondes valeurs franches de
    # chaque ligne : sur une page ou deux lignes seulement en portaient deux
    # (deux « 40% » d'une ligne fondue), cette mediane retombait SUR la colonne
    # du droit de douane, l'ordre des colonnes devenait faux et la page entiere
    # etait declaree. C'est ce qui coutait 265 droits que le tarif enonce.
    droite = [x for ligne in lignes for x, m in ligne["toks"]
              if x_dd + 10 < x < ancre - 8
              and (_est_taux_franc(m) or m in ("-", "_", "\u2013", "\u2014"))]
    if len(droite) < 3:
        return None
    x_exc = med(droite)
    x_unite = med(xs_unite) if len(xs_unite) >= 2 else x_dd - 38.0
    if not (x_unite < x_dd < x_exc < ancre):
        return None
    return x_unite, x_dd, x_exc


def _valeur(toks, centre: float, demi: float = 16.0) -> Tuple[Optional[str], Optional[str]]:
    """La valeur de droit de la colonne, ou un motif de refus.

    Rend (valeur, motif). Deux valeurs dans la meme colonne ne sont pas
    arbitrees : c'est le signe que deux lignes se sont fondues, et la ligne est
    declaree plutot que servie au hasard.
    """
    cands = [m for x, m in toks if centre - demi <= x < centre + demi and _est_taux(m)]
    if not cands:
        return None, "CELLULE_VIDE"
    if len(set(cands)) > 1:
        return None, "DEUX_VALEURS_DANS_LA_COLONNE"
    return cands[0], None


def _unite(toks, centre: float, demi: float = 20.0) -> str:
    """L'unite statistique, prise dans son vocabulaire ferme."""
    cands = [m for x, m in toks if centre - demi <= x < centre + demi
             and m.lower() in UNITES]
    return cands[0] if cands else ""


def _motif_dd(motif: Optional[str], motif_colonne: Optional[str],
              brut: Optional[str], note: Optional[str]) -> Optional[str]:
    """Pourquoi ce droit de douane n'est pas servi — sur la ligne, toujours.

    Une indisponibilite MUETTE se lit comme une donnee manquante sans cause :
    l'operateur ne peut ni la contester ni la combler. Chaque cas porte donc son
    motif, y compris la cellule vide, qui n'en avait pas.
    """
    if motif_colonne == "DEUX_VALEURS_DANS_LA_COLONNE":
        return ("Deux valeurs distinctes dans la colonne du droit de douane : le "
                "signe que deux lignes du bareme se sont fondues. Aucune n'est "
                "retenue — arbitrer au hasard servirait un droit faux.")
    if motif == "CELLULE_VIDE":
        return ("Aucune valeur dans la colonne du droit de douane a cette ligne. "
                "Declaree indisponible : une cellule vide n'est pas un zero.")
    if motif == "RENVOI_EN_NOTE":
        return ("Le tarif renvoie a une note de bas de page (« " + (brut or "*")
                + " ») que la collecte n'a pas retrouvee sur les pages voisines. "
                "Le droit existe mais n'est pas lu : declare indisponible.")
    if motif == "EXPRESSION_NON_LUE":
        return (f"Cellule « {brut} » non interpretee — declaree indisponible "
                "plutot que servie fausse.")
    return note if note else None


def _position_declaree(ligne, index: int, national: str) -> Dict:
    """Une ligne dont la page ne s'est pas calibree : declaree, jamais devinee.

    Elle porte son code, sa page et son verbatim, et AUCUN taux — de sorte que
    le moteur reponde « indisponible » au lieu d'un montant vraisemblable.
    """
    brut = " ".join(m for _x, m in ligne["toks"] if not RX_CODE.match(m))
    return {
        "national_code": national,
        "hs6": national[:6],
        "chapter": national[:2],
        "heading": ligne["code"][:7],
        "statistical_unit": "",
        "designation": {"en": "", "fr": "", "verbatim": " ".join(brut.split())},
        "taxes": [{
            "code": "DD", "name": "Customs duty", "name_fr": "Droit de douane",
            "rate_pct": None, "raw_value": "", "specific_value": None,
            "base": "CIF", "base_source": ACTE_DD, "source": SOURCE,
            "note": "Page non calibrable : moins de trois lignes y ont une forme "
                    "certaine, et les colonnes ne s'y lisent donc pas. Le droit est "
                    "declare indisponible plutot que lu sur un calibrage suppose.",
        }],
        "preferential_rates": [],
        "restrictions": [],
        "source_gaps": ["PAGE_NON_CALIBREE"],
        "page_source": index + 1,
        "source": SOURCE,
    }


def extraire(chemin: Path) -> Tuple[List[Dict], Dict[str, int]]:
    doc = pymupdf.open(chemin)
    positions: List[Dict] = []
    vus = set()
    stats = {
        "pages": doc.page_count,
        "pages_calibrees_sur_donnees": 0,
        "pages_calibrage_dominant": 0,
        "droits_composes": 0,
        "accises_specifiques": 0,
        "taux_non_lus": 0,
        "sans_lettre_tva": 0,
        "pages_non_calibrees": 0,
        "lignes_non_calibrees": 0,
        "notes_appariees": 0,
        "tva_standard": 0,
        "tva_exoneree": 0,
        "tva_taux_zero": 0,
    }

    for index in range(doc.page_count):
        page = doc[index]
        mots = page.get_text("words")
        if not mots:
            continue
        ancre = _ancre_tva(mots)
        if ancre is None:
            ancre = X_TVA_DOMINANT
            calibre_sur_donnees = False
        else:
            calibre_sur_donnees = True
        # La note de bas de page deborde sur la page SUIVANTE : les renvois des
        # positions de beurre 0405.x sont page 52, leur note — « *25% or KR0.85
        # per kg whichever is the greater » — page 53. La chercher sur la seule
        # page du renvoi laissait 146 droits sans valeur.
        # La note ne vit pas forcement sur la page de son renvoi : elle deborde
        # sur la SUIVANTE (les beurres 0405.x page 52, leur note page 53) ou
        # ouvre la suivante (les huiles page 87, leur note en HAUT de la 88).
        # On regarde donc autour, en n'acceptant que les formes qu'on sait lire.
        notes = notes_de_la_page(page)
        for voisine in (index + 1, index + 2, index - 1):
            if not 0 <= voisine < doc.page_count:
                continue
            for marque, texte in notes_de_la_page(doc[voisine]).items():
                notes.setdefault(marque, texte)
        bandes = _bandes(mots)

        # Une ligne du bareme commence a la bande de son code et se prolonge par
        # les bandes suivantes tant qu'aucun nouveau code n'apparait : c'est ainsi
        # que les cellules de taux, qui tombent plus bas, la rejoignent.
        lignes: List[Dict] = []
        for _y, toks in bandes:
            code = next((m for x, m in toks if RX_CODE.match(m)), None)
            if code:
                lignes.append({"code": code, "toks": list(toks)})
            elif lignes:
                lignes[-1]["toks"] += toks

        colonnes = _colonnes_de_la_page(lignes, ancre)
        if colonnes is None:
            # Faute de trois lignes de forme certaine, la page ne se calibre pas.
            # Ses lignes sont declarees plutot que lues sur un calibrage suppose.
            stats["pages_non_calibrees"] += 1
            for ligne in lignes:
                national = ligne["code"].replace(".", "")
                if national in vus:
                    continue
                vus.add(national)
                stats["lignes_non_calibrees"] += 1
                positions.append(_position_declaree(ligne, index, national))
            continue
        x_unite, x_dd, x_exc = colonnes

        vu_ici = False
        for ligne in lignes:
            national = ligne["code"].replace(".", "")
            if national in vus:
                continue
            toks = ligne["toks"]
            lettres = [m for x, m in toks if RX_TVA.match(m) and abs(x - ancre) < 13.0]
            cell_unite = _unite(toks, x_unite)
            cell_dd, motif_col_dd = _valeur(toks, x_dd)
            cell_exc, motif_col_exc = _valeur(toks, x_exc)

            m_tva = RX_TVA.match(lettres[0]) if len(set(lettres)) == 1 else None
            gaps: List[str] = []
            if not m_tva:
                stats["sans_lettre_tva"] += 1
                gaps.append(
                    "DEUX_LETTRES_TVA" if len(set(lettres)) > 1 else "LETTRE_TVA_NON_LUE"
                )
            if motif_col_dd == "DEUX_VALEURS_DANS_LA_COLONNE":
                gaps.append("DD_" + motif_col_dd)
            if motif_col_exc == "DEUX_VALEURS_DANS_LA_COLONNE":
                gaps.append("EXC_" + motif_col_exc)

            taxes: List[Dict] = []
            renvoi_dd = RX_RENVOI.match(cell_dd.strip()) if cell_dd else None
            note_dd = notes.get(renvoi_dd.group(1)) if renvoi_dd else None
            compose = RX_NOTE_COMPOSEE.match(note_dd) if note_dd else None

            if compose:
                # La note porte le droit en entier, et ENONCE sa regle
                # (« whichever is the greater »), que la regle 2(b) des
                # Additional Zambian Rules pose par ailleurs pour tout le tarif.
                stats["droits_composes"] += 1
                stats["notes_appariees"] += 1
                taxes.append({
                    "code": "DD", "name": "Customs duty",
                    "name_fr": "Droit de douane",
                    "rate_pct": float(compose.group(2).replace(",", ".")),
                    "specific_value": (
                        f"{compose.group(3).replace(',', '')} ZMW/"
                        f"{compose.group(4).lower().strip('/')}"
                    ),
                    "specific_currency": "ZMW",
                    "raw_value": note_dd,
                    "compound": True, "compound_rule": "higher",
                    "base": "CIF", "base_source": ACTE_DD, "source": SOURCE,
                    "note": "Droit compose dont la REGLE EST ENONCEE : la note de "
                            "bas de page porte « whichever is the greater », et la "
                            "regle 2(b) des Additional Zambian Rules la pose pour "
                            "tout le tarif — « the rate which yields the greater "
                            "amount of duty shall apply ».",
                })
            else:
                taux_dd, brut_dd, motif_dd = lire_taux(cell_dd)
                specifique = lire_montant(cell_dd)
                if motif_dd == "RENVOI_EN_NOTE" and note_dd:
                    stats["notes_appariees"] += 1
                if motif_dd in ("EXPRESSION_NON_LUE", "CELLULE_VIDE") or (
                    motif_dd == "RENVOI_EN_NOTE" and not compose
                ):
                    stats["taux_non_lus"] += 1
                    gaps.append(f"DD_{motif_dd}")
                taxes.append({
                    "code": "DD", "name": "Customs duty",
                    "name_fr": "Droit de douane",
                    "rate_pct": taux_dd if not specifique else None,
                    "specific_value": specifique,
                    "specific_currency": "ZMW" if specifique else None,
                    "raw_value": brut_dd or "",
                    "base": "CIF", "base_source": ACTE_DD, "source": SOURCE,
                    "note": _motif_dd(motif_dd, motif_col_dd, brut_dd, note_dd),
                })

            taux_exc, brut_exc, motif_exc = lire_taux(cell_exc)
            spec_exc = lire_montant(cell_exc)
            if spec_exc:
                stats["accises_specifiques"] += 1
            if motif_exc != "CELLULE_VIDE":
                taxes.append({
                    "code": "EXC", "name": "Excise duty",
                    "name_fr": "Droit d'accise",
                    "rate_pct": taux_exc if not spec_exc else None,
                    "specific_value": spec_exc,
                    "specific_currency": "ZMW" if spec_exc else None,
                    "raw_value": brut_exc or "",
                    "base": "CIF+DD", "base_source": ACTE_EXC, "source": SOURCE,
                    "note": ("« - » au tarif : la position n'est pas soumise a "
                             "l'accise. C'est un zero publie, pas une lacune."
                             if brut_exc in ("-", "_", "–", "—") else None),
                })
            elif motif_exc == "CELLULE_VIDE":
                gaps.append("EXC_CELLULE_VIDE")

            if m_tva:
                lettre = m_tva.group(1)
                taxes.append(_tva(lettre, notes.get(m_tva.group(2) or ""), stats))

            designation = " ".join(
                m for x, m in toks
                if x < x_unite - 20.0 and not RX_CODE.match(m)
            )
            vus.add(national)
            vu_ici = True
            positions.append({
                "national_code": national,
                "hs6": national[:6],
                "chapter": national[:2],
                "heading": ligne["code"][:7],
                "statistical_unit": cell_unite.strip(),
                "designation": {
                    "en": " ".join(designation.split()),
                    "fr": "",
                    "verbatim": " ".join(designation.split()),
                },
                "taxes": taxes,
                "preferential_rates": [],
                "restrictions": [],
                "source_gaps": gaps,
                "page_source": index + 1,
                "source": SOURCE,
            })
        if vu_ici:
            if calibre_sur_donnees:
                stats["pages_calibrees_sur_donnees"] += 1
            else:
                stats["pages_calibrage_dominant"] += 1

    return positions, stats


#: Le taux standard de TVA n'est PAS dans le tarif. La s.9(3) de l'Acte porte
#: 17,5 % « unless the Minister, by statutory order, determines a lower rate » :
#: le texte consolide est donc perime. Le taux retenu est celui qu'enonce
#: l'autorite qui le percoit, avec sa reserve.
TVA_TAUX_STANDARD = 16.0
TVA_SOURCE_TAUX = (
    "ZRA, VAT Guide : « Currently the Standard rate is 16% ». L'ordre statutaire "
    "que la s.9(3) du Value Added Tax Act prevoit n'a PAS ete identifie ; le taux "
    "de 17,5 % que porte le texte consolide de l'Acte n'est plus en vigueur et "
    "n'est donc pas servi."
)


def _tva(lettre: str, note: Optional[str], stats: Dict[str, int]) -> Dict:
    """La ligne de TVA, d'apres la LETTRE du tarif et la loi qui la definit.

    Le tarif ne publie aucune legende : le sens des trois lettres vient du Value
    Added Tax Act lui-meme, qui definit « exempt importation » par sa premiere
    annexe et « zero-rated supply » par sa seconde.
    """
    commun = {
        "code": "TVA", "name": "Value added tax", "name_fr": "Taxe sur la valeur ajoutee",
        "base": "CIF+DD+EXC", "base_source": ACTE_TVA, "source": SOURCE,
        "specific_value": None, "specific_currency": None,
    }
    if lettre == "S":
        stats["tva_standard"] += 1
        return dict(commun, rate_pct=TVA_TAUX_STANDARD, raw_value="S",
                    note="Lettre « S » au tarif : standard rated. " + TVA_SOURCE_TAUX
                         + (f" Note du tarif : {note}" if note else ""))
    if lettre == "E":
        stats["tva_exoneree"] += 1
        # L'assiette est CONSERVEE : le taux est nul, donc le montant l'est aussi,
        # et la ligne se lit « TVA 0 % — exoneration » au lieu de « assiette
        # indisponible », qui ferait croire a une lacune de collecte.
        return dict(commun, rate_pct=0.0, raw_value="E",
                    note="Lettre « E » au tarif : exempt importation. Value Added Tax "
                         "Act : « \"exempt importation\" means an importation of goods "
                         "described in the First Schedule ». Exoneration PUBLIEE, non "
                         "une lacune."
                         + (f" Note du tarif : {note}" if note else ""))
    stats["tva_taux_zero"] += 1
    return dict(commun, rate_pct=0.0, raw_value="Z",
                note="Lettre « Z » au tarif : zero-rated. Value Added Tax Act : "
                     "« \"zero-rated supply\" means a supply of goods or services "
                     "described in the Second Schedule », et s.9(4) : « the prescribed "
                     "rate of tax in the case of a zero-rated supply shall be regarded "
                     "as zero »."
                     + (f" Note du tarif : {note}" if note else ""))


def construire(chemin: Path) -> Dict:
    positions, stats = extraire(chemin)
    codes = sorted({t["code"] for p in positions for t in p["taxes"]})
    return {
        "country": "ZMB",
        "country_name": "Zambie",
        "source": SOURCE,
        "source_url": SOURCE_URL,
        "source_legal": (
            "Customs and Excise Act : s.72 (First Schedule, customs tariff), s.88 "
            "(valeur d'assiette de l'accise a l'importation), Cinquieme annexe "
            "(valeur en douane) ; Value Added Tax Act Cap. 331, s.9 et s.10(3)"
        ),
        "source_quality": "crawled_authentic",
        "source_sha256": hashlib.sha256(chemin.read_bytes()).hexdigest(),
        "extracted_at": date.today().isoformat(),
        "calculation_rules": {
            "order": ["DD", "EXC", "TVA"],
            "bases": {
                "DD": {"basis": "CIF", "type": "ad_valorem", "source": ACTE_DD},
                "EXC": {"basis": "CIF+DD", "type": "mixed", "source": ACTE_EXC},
                "TVA": {"basis": "CIF+DD+EXC", "type": "ad_valorem", "source": ACTE_TVA},
            },
            "source": (
                "Cascade etablie article par article : DD sur la valeur en douane "
                "(Cinquieme annexe cl. 2 et 3(1)(a)(vii)-(viii) : prix paye + fret + "
                "assurance = CIF) ; accise sur « the customs value […] and any customs "
                "duty payable » (s.88) ; TVA sur la valeur en douane augmentee de « any "
                "duty or other impost payable otherwise than under this Act » (VAT Act "
                "s.10(3)). Un droit « X% or K Y per unit » est liquide selon la regle "
                "que le tarif enonce lui-meme — regle 2(b) des Additional Zambian "
                "Rules : le plus eleve des deux."
            ),
        },
        "stats": dict(stats, total_positions=len(positions), unique_tax_codes=codes,
                      chapters_covered=len({p["chapter"] for p in positions})),
        "sub_positions": positions,
    }


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    if len(sys.argv) < 2:
        print(f"usage: {sys.argv[0]} <chemin du PDF du tarif ZRA>", file=sys.stderr)
        return 2
    chemin = Path(sys.argv[1])
    donnees = construire(chemin)
    s = donnees["stats"]
    if s["total_positions"] < 5000:
        print(f"Collecte refusee : {s['total_positions']} positions lues, moins de 5 000.",
              file=sys.stderr)
        return 1
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    (DATA_DIR / "ZMB_tariffs.json").write_text(
        json.dumps(donnees, ensure_ascii=False, indent=1), encoding="utf-8"
    )
    logger.info(
        "ZMB : %s positions, %s chapitres, codes %s",
        s["total_positions"], s["chapters_covered"], ",".join(s["unique_tax_codes"]),
    )
    logger.info(
        "  pages calibrees sur donnees %s | sur calibrage dominant %s",
        s["pages_calibrees_sur_donnees"], s["pages_calibrage_dominant"],
    )
    logger.info(
        "  droits composes %s | accises specifiques %s | notes appariees %s "
        "| taux non lus %s | sans lettre TVA %s",
        s["droits_composes"], s["accises_specifiques"], s["notes_appariees"],
        s["taux_non_lus"], s["sans_lettre_tva"],
    )
    logger.info(
        "  TVA : standard %s | exoneree %s | taux zero %s",
        s["tva_standard"], s["tva_exoneree"], s["tva_taux_zero"],
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
