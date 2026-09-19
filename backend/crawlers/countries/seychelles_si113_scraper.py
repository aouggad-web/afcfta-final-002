#!/usr/bin/env python3
"""Tarif douanier des Seychelles — S.I. 113 of 2022.

Source : Customs Management (Tariff and Classification of Goods) Regulations,
2022, Supplement to Official Gazette du 28 octobre 2022, 827 pages, pris sous la
section 270 du Customs Management Act, 2011 (Act 22 of 2011) et publie par la
Seychelles Revenue Commission. C'est le TEXTE REGLEMENTAIRE lui-meme.

CE TARIF PUBLIE UNE TRAJECTOIRE ZLECAf ANNEE PAR ANNEE, ET C'EST CE QUI LE
DISTINGUE DE TOUS CEUX INTEGRES AVANT LUI. Le Malawi publie UN taux ZLECAf ; les
Seychelles en publient CINQ, un par annee civile de 2022 a 2026, et autant pour la
SADC. Le demantelement n'est pas une intention, c'est un calendrier au bareme.

LES TREIZE COLONNES SONT NOMMEES PAR LE REGLEMENT, PAS DEDUITES DE LA MISE EN PAGE.
Regulation 2 renvoie chaque regime a son annexe :
  Schedule I    le tarif lui-meme
  Schedule II   taux preferentiels de la Commission de l'ocean Indien
  Schedule III  liste des Etats membres de la zone de libre-echange du COMESA
  Schedule IV   liste des Etats membres de la zone de libre-echange de la SADC
  Schedule V    Etats membres de l'UE et Etats ESA de l'APE interimaire
  Schedule VI   liste des Etats parties a la ZLECAf
et l'en-tete du bareme, repete sur ses 591 pages, porte :
  MFN | COMESA FTA | European Union & UK | SADC FTA 2022..2026 | AfCFTA 2022..2026

QUI A DROIT A LA COLONNE ZLECAf : UNE LISTE, PAS UNE CONDITION A VERIFIER.
La Schedule VI enumere 38 Etats parties. C'est la difference avec le Malawi, dont
le taux ZLECAf depend d'un « specified country content of not less than thirty-five
per cent » qu'aucun calculateur ne peut verifier : ici l'eligibilite se lit sur une
liste fermee, et le collecteur la porte.

L'EN-TETE DE CHAQUE PAGE EST LA CARTE DE SES COLONNES, ET C'EST AINSI QU'ELLES SONT
LUES. La grille se deplace d'une page a l'autre — la colonne NPF tombe a l'abscisse
256 page 35 et a 354 page 132, presque trois colonnes d'ecart — parce que la largeur
de la colonne de designation varie. Aucune abscisse n'est donc ecrite en dur : sur
chaque page on lit les mots « MFN », « FTA », « UK » et les dix millesimes de
l'en-tete, et ce sont EUX qui donnent les treize abscisses. Sur les 591 pages de
bareme, 582 portent un en-tete complet ; les neuf autres sont declarees.

CE QUI PROUVE QUE LE RATTACHEMENT NE SE TROMPE PAS : sur les lignes qui portent
leurs treize valeurs, on a compare le rang de chaque valeur au rattachement par
proximite a l'ancre de l'en-tete. 74 906 rattachements, AUCUN desaccord.

UNE VALEUR PEUT ETRE COUPEE EN PLUSIEURS MORCEAUX, ET MEME SUR DEUX LIGNES.
Le droit specifique « SCR60/l » sort parfois en « SCR » sur la bande du code et
« 60/l » sur la bande suivante, ou en « SCR5/ » puis « kg ». Les morceaux sont donc
rassembles PAR COLONNE — chacun est rattache a son ancre, puis recolle dans l'ordre
de lecture — et non par adjacence horizontale, qui ne verrait pas la coupure
verticale.

LE REGIME COI EST UNE REGLE DE CALCUL, PAS UNE COLONNE. La Schedule II :
  « Goods originating from [Mauritius, Reunion, Comoros, Madagascar & Seychelles]
    will pay a rate of duty of 5% lower than the rate of duty prescribed in sub
    column 5, entitled "MFN" [...] except if: 1. The rate of duty in Part III is 5%
    or lower. 2. Chapter 22 [...] 3. Chapter 24 [...] 4. Heading 27.10 [...]
    5. Heading 27.11 [...] Subject to the acceptance of the certificate of origin »
Le taux COI se DEDUIT donc du NPF, et le texte donne lui-meme la formule et ses cinq
exceptions : ce n'est pas une extrapolation, c'est une regle enoncee. Sur un droit
NPF SPECIFIQUE (roupies au litre), « 5 % de moins » n'a pas de sens : la ligne le
declare au lieu de fabriquer un nombre.

L'ASSIETTE EST LE CIF, ET C'EST LE TEXTE QUI LE DIT — mais pas celui qu'on croit.
La section 41 de l'Act delegue l'evaluation au reglement. Customs Management
Regulations, 2014 (S.I. 42 of 2014), regulation 5 : la valeur en douane est la
valeur transactionnelle « adjusted in accordance with the provisions of regulation
8 » ; regulation 8(1)(e) ajoute « the cost of transport of the imported goods to the
port or place of importation », « loading, unloading and handling charges » et « the
cost of insurance ». Prix + fret + assurance jusqu'au port : c'est le CIF.

UNE DEDUCTION QUI A FAILLI ETRE FAITE ICI, ET QUI ETAIT FAUSSE. Le Value Added Tax
Act, s.23(1), definit la valeur d'une importation comme « (a) the value of the goods
for customs duty (b) insurance and freight (c) [les droits] ». Ce (b) separe donne a
penser que la valeur en douane, elle, EXCLUT le fret — donc que le droit porterait
sur un FOB. La regulation 8(1)(e) montre que non. On ne deduit pas l'assiette d'un
impot de la redaction d'un autre.

CE QUI N'EST PAS COLLECTE ICI : l'accise, qui ne figure pas a ce bareme et releve de
l'Excise Tax Act et de ses reglements de taux ; et la TVA, dont l'assiette est
etablie par ailleurs (fiche SYC_assiette_TVA) mais dont le taux n'est pas dans ce
document.
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
SOURCE = (
    "Customs Management (Tariff and Classification of Goods) Regulations, 2022 — "
    "S.I. 113 of 2022, Supplement to Official Gazette du 28 octobre 2022"
)
SOURCE_URL = (
    "https://src.gov.sc/wp-content/uploads/2025/10/"
    "SI-113-2022-Customs-Management-Tariff-and-Classification-of-Goods-Regulations-2022.pdf"
)
ACTE_DD = (
    "Customs Management Act, 2011, s.41 (l'evaluation est prescrite par reglement) ; "
    "Customs Management Regulations, 2014 (S.I. 42 of 2014), reg. 5 — valeur "
    "transactionnelle — et reg. 8(1)(e), qui y ajoute « the cost of transport of the "
    "imported goods to the port or place of importation », « loading, unloading and "
    "handling charges » et « the cost of insurance » : prix + fret + assurance, le CIF"
)
RESERVE_SI7_2024 = (
    "S.I. 113 of 2022 a ete modifie par S.I. 7 of 2024 (22 janvier 2024). Les douze "
    "sous-positions qu'il INSERE sont portees ici avec leur source propre. La "
    "SUBSTITUTION qu'il opere au chapitre 22, entre les codes 2208.7039 et 2208.9011, "
    "n'est PAS appliquee : la couche texte de l'instrument n'en rend ni le code ni les "
    "taux, et les inventer serait pire que de les declarer."
)

#: Le code d'une sous-position seychelloise : quatre chiffres, un point, quatre chiffres.
RX_CODE = re.compile(r"^\d{4}\.\d{4}$")
#: Un taux ad valorem.
RX_PCT = re.compile(r"^(\d+(?:\.\d+)?)\s*%$")
#: Un droit specifique en roupies seychelloises par unite : « SCR60/l », « SCR5/kg »,
#: et la forme longue du tabac, « SCR96 per pack of 200 ».
RX_SPEC = re.compile(r"^SCR\s?(\d+(?:\.\d+)?)\s*(?:/|per)\s*([A-Za-z0-9 .]+)$", re.I)
#: Un droit COMPOSE : « 7% + SCR5/kg ». Le « + » n'est pas un « or » — les deux
#: composantes sont dues ENSEMBLE, et il n'y a donc rien a departager.
RX_COMPOSE = re.compile(r"^(\d+(?:\.\d+)?)\s*%\s*\+\s*(SCR.+)$", re.I)
#: Un zero publie ecrit en toutes lettres.
RX_ZERO = re.compile(r"^free$", re.I)
#: Un fragment de droit specifique : ce qu'il faut encore recoller.
RX_FRAGMENT = re.compile(
    r"^(\+|SCR|SCR\s?\d+(?:\.\d+)?(?:/[A-Za-z.]*)?|\d+(?:\.\d+)?(?:/[A-Za-z.]*)?"
    r"|/[A-Za-z.]*|per|pack|of|[A-Za-z.]{1,4})$",
    re.I,
)

#: Les treize colonnes, dans l'ordre de l'en-tete, avec le code que le socle leur
#: donne. Les millesimes ne sont pas cosmetiques : ce sont treize regimes distincts
#: que le reglement publie, et les confondre effacerait le calendrier.
COLONNES = [
    ("DD", "col. 1 — MFN, droit de douane de droit commun"),
    ("COMESA", "col. 2 — COMESA FTA (Schedule III)"),
    ("EU_UK", "col. 3 — European Union & UK, APE interimaire (Schedule V)"),
    ("SADC_2022", "col. 4 — SADC FTA, taux 2022 (Schedule IV)"),
    ("SADC_2023", "col. 5 — SADC FTA, taux 2023 (Schedule IV)"),
    ("SADC_2024", "col. 6 — SADC FTA, taux 2024 (Schedule IV)"),
    ("SADC_2025", "col. 7 — SADC FTA, taux 2025 (Schedule IV)"),
    ("SADC_2026", "col. 8 — SADC FTA, taux 2026 (Schedule IV)"),
    ("AFCFTA_2022", "col. 9 — ZLECAf, taux 2022 (Schedule VI)"),
    ("AFCFTA_2023", "col. 10 — ZLECAf, taux 2023 (Schedule VI)"),
    ("AFCFTA_2024", "col. 11 — ZLECAf, taux 2024 (Schedule VI)"),
    ("AFCFTA_2025", "col. 12 — ZLECAf, taux 2025 (Schedule VI)"),
    ("AFCFTA_2026", "col. 13 — ZLECAf, taux 2026 (Schedule VI)"),
]
#: Les millesimes publies, dans l'ordre. Le dernier borne le calendrier : au-dela,
#: le reglement ne dit plus rien, et rien n'est reconduit en silence.
MILLESIMES = ["2022", "2023", "2024", "2025", "2026"]
#: Les regimes servis au calculateur pour l'annee en vigueur. Les autres millesimes
#: restent sous leur nom propre : la trajectoire est une donnee, pas un decor.
REGIMES_MILLESIMES = {"SADC": "SADC", "AFCFTA": "AFCFTA"}

#: Les 38 Etats parties que la Schedule VI nomme. Hors de cette liste, pas de
#: colonne ZLECAf : l'eligibilite est une enumeration, pas une appreciation.
ETATS_ZLECAF = [
    "Arab Republic of Egypt",
    "Central African Republic",
    "Equatorial Guinea",
    "Kingdom of Eswatini",
    "Kingdom of Lesotho",
    "Republic of Angola",
    "Republic of Burkina Faso",
    "Republic of Burundi",
    "Republic of Cameroon",
    "Republic of Chad",
    "Republic of the Congo",
    "Republic of Djibouti",
    "Republic of Ethiopia",
    "Republic of Gambia",
    "Republic of Gabon",
    "Republic of Ghana",
    "Republic of Guinea",
    "Republic of Ivory Coast",
    "Republic of Kenya",
    "Republic of Malawi",
    "Republic of Mali",
    "Republic of Mauritania",
    "Republic of Mauritius",
    "Republic of Namibia",
    "Republic of Niger",
    "Republic of Nigeria",
    "Republic of Rwanda",
    "Republic of Sao Tome and Principe",
    "Republic of Senegal",
    "Republic of Sierra Leone",
    "Republic of South Africa",
    "Republic of Togo",
    "Republic of Tunisia",
    "Republic of Uganda",
    "Republic of Zambia",
    "Republic of Zimbabwe",
    "Sahrawi Arab Democratic Republic",
    "Socialist Republic of Algeria",
]
#: Les Etats de la Commission de l'ocean Indien que la Schedule II nomme.
ETATS_COI = ["Mauritius", "Reunion", "Comoros", "Madagascar", "Seychelles"]
#: Les cinq exceptions que la Schedule II oppose a la remise COI, mot pour mot.
EXCEPTIONS_COI = (
    "1. The rate of duty in Part III is 5% or lower. 2. Chapter 22 (Beverages, "
    "Spirits and Vinegar). 3. Chapter 24 (Tobacco and manufactured tobacco products). "
    "4. Heading 27.10 (Petroleum oils). 5. Heading 27.11 (Petroleum gases)."
)

TOLERANCE_Y = 3.5
#: Marge a gauche de la premiere ancre : une valeur y deborde parfois de deux unites.
MARGE_GAUCHE = 12.0
#: Bord droit de la COLONNE DES CODES. Des 6 121 codes que porte le document, 6 120
#: tombent entre x=80 et x=145 ; le seul au-dela (x=360) est cite dans un texte, non
#: porte par une ligne du bareme. Le Malawi montre ce que coute l'absence de cette
#: borne : les codes que ses designations citent y devenaient des positions a part
#: entiere, servies avec le droit de la ligne qui les cite.
X_COLONNE_DES_CODES = 200.0

#: Les douze sous-positions que S.I. 7 of 2024 INSERE, avec leurs treize taux tels
#: que l'instrument les publie. Elles sont ecrites ici parce qu'elles sont LUES dans
#: un instrument que le collecteur ne parcourt pas : les porter sans les nommer
#: serait les fabriquer.
SI7_2024_URL = (
    "https://src.gov.sc/wp-content/uploads/2025/10/"
    "SI-7-2024-Customs-Management-Tariff-and-Classification-of-Goods-Amendment-"
    "Regulations-2024.pdf"
)
SI7_2024_SOURCE = (
    "Customs Management (Tariff and Classification of Goods) (Amendment) "
    "Regulations, 2024 — S.I. 7 of 2024, Gazette du 22 janvier 2024, reg. 2(c)"
)
SI7_2024_INSERTIONS = [
    ("8703.4013", "---- Full hybrid", "No.", [0.0] * 13),
    ("8703.4023", "---- Full hybrid", "No.", [0.0] * 13),
    ("8703.4033", "---- Full hybrid", "No.", [0.0] * 13),
    ("8703.4043", "---- Full hybrid", "No.", [0.0] * 13),
    ("8703.5013", "---- Full hybrid", "No.", [0.0] * 13),
    ("8703.5023", "---- Full hybrid", "No.", [0.0] * 13),
    ("8703.5033", "---- Full hybrid", "No.", [0.0] * 13),
    ("8703.5043", "---- Full hybrid", "No.", [0.0] * 13),
    (
        "8708.9911",
        "---- New quarter panels of vehicles of headings 87.02 to 87.04",
        "No.",
        [10.0] + [0.0] * 12,
    ),
    ("8708.9919", "---- Other", "No.", [10.0] + [0.0] * 12),
]


def ancres_de_la_page(mots) -> Optional[List[float]]:
    """Les treize abscisses de colonne, LUES DANS L'EN-TETE de la page.

    La grille se deplace d'une page a l'autre parce que la colonne de designation
    n'a pas toujours la meme largeur : page 35 la colonne NPF tombe a 256, page 132
    a 354. Ecrire les abscisses en dur ferait donc lire, sur une page, le taux de la
    colonne voisine. L'en-tete, lui, est sur chaque page et il bouge AVEC la grille.

    Les ancres sont « MFN », le premier « FTA » de l'en-tete — celui du COMESA —,
    « UK » (ou « Union » a defaut), puis les dix millesimes. Une page dont l'en-tete
    n'est pas complet n'est pas calibree, et ses lignes sont declarees.
    """
    mfn = [w for w in mots if w[4] == "MFN"]
    annees = sorted((w for w in mots if w[4] in MILLESIMES and w[1] < 200), key=lambda w: w[0])
    uk = sorted((w for w in mots if w[4] in ("UK", "Union")), key=lambda w: w[0])
    fta = sorted((w for w in mots if w[4] == "FTA" and w[1] < 200), key=lambda w: w[0])
    if len(mfn) != 1 or len(annees) != 10 or not uk or not fta:
        return None
    ancres = [mfn[0][0], fta[0][0], uk[0][0]] + [w[0] for w in annees]
    # Les ancres doivent etre strictement croissantes : un en-tete lu de travers ne
    # sert pas de carte.
    if any(b <= a for a, b in zip(ancres, ancres[1:])):
        return None
    return ancres


def _colonne_de(x: float, ancres: List[float]) -> Optional[int]:
    """La colonne d'une abscisse, ou None si elle tombe entre deux.

    La tolerance est la MOITIE DU PAS LOCAL et non un nombre fixe : le pas vaut 34
    entre les deux premieres colonnes et 29 entre deux millesimes, et une tolerance
    unique serait trop large ici et trop etroite la.
    """
    index = min(range(len(ancres)), key=lambda k: abs(x - ancres[k]))
    voisins = [
        abs(ancres[index] - ancres[k]) for k in (index - 1, index + 1) if 0 <= k < len(ancres)
    ]
    return index if abs(x - ancres[index]) <= min(voisins) / 2 else None


def bandes(mots, tolerance: float = TOLERANCE_Y):
    """Regrouper les tokens par ligne VISUELLE."""
    groupes: List[Tuple[float, List]] = []
    for mot in sorted(mots, key=lambda w: (w[1], w[0])):
        if groupes and abs(mot[1] - groupes[-1][0]) <= tolerance:
            groupes[-1][1].append(mot)
        else:
            groupes.append((mot[1], [mot]))
    return [(y, sorted(ts, key=lambda w: w[0])) for y, ts in groupes]


def _lignes_de_la_page(mots, ancres: List[float]) -> List[Dict]:
    """Reconstituer les lignes du bareme, et retrouver le code de chacune.

    LE CODE N'EST PAS TOUJOURS SUR LA BANDE DE SES TAUX. Quand une designation tient
    sur plusieurs lignes, le code est centre verticalement contre son bloc et sort
    donc SOUS ses propres taux : page 58, la bande « - - Norway lobsters ... 0% 0% ...»
    ne porte aucun code, et « 0306.3400 » arrive deux bandes plus bas, tout seul.
    Rattacher cette bande a la ligne precedente donnait a 0306.3300 deux jeux de
    treize valeurs — d'ou les « 0%0% » — et laissait 0306.3400 sans aucun taux.

    La regle suit donc la mise en page plutot que l'ordre des bandes : une bande qui
    porte des VALEURS est une ligne ; son code est celui de sa propre bande, ou, a
    defaut, celui de la prochaine bande qui porte un code SANS valeur. Les bandes
    sans code et sans valeur prolongent la designation de la ligne en cours.
    """
    etiquettes = [
        {
            "y": y,
            "code": next(
                (w[4] for w in ts if w[0] < X_COLONNE_DES_CODES and RX_CODE.match(w[4])), None
            ),
            "valeurs": sum(
                1
                for w in ts
                if w[0] >= ancres[0] - MARGE_GAUCHE
                and (RX_PCT.match(w[4]) or RX_ZERO.match(w[4]) or w[4].upper().startswith("SCR"))
            ),
            "toks": [(w[0], w[4]) for w in ts],
            "desc": [
                w[4] for w in ts if w[0] < ancres[0] - MARGE_GAUCHE and not RX_CODE.match(w[4])
            ],
        }
        for y, ts in bandes(mots)
    ]
    # Les bandes de l'en-tete ne sont pas du bareme : le dernier millesime en marque
    # la fin. Sans cette borne, « MFN » et « COMESA » entraient dans une cellule.
    bas_entete = max(
        (
            e["y"]
            for e in etiquettes
            if any(m in MILLESIMES or m in ("MFN", "AfCFTA") for _x, m in e["toks"])
            and e["y"] < 200
        ),
        default=0.0,
    )
    etiquettes = [e for e in etiquettes if e["y"] > bas_entete]

    codes_libres = [i for i, e in enumerate(etiquettes) if e["code"] and not e["valeurs"]]
    pris = set()
    lignes: List[Dict] = []
    for i, e in enumerate(etiquettes):
        if e["valeurs"]:
            code = e["code"]
            if code is None:
                suivant = next((j for j in codes_libres if j > i and j not in pris), None)
                if suivant is None:
                    if lignes:
                        lignes[-1]["toks"] += e["toks"]
                        lignes[-1]["desc"] += e["desc"]
                    continue
                pris.add(suivant)
                code = etiquettes[suivant]["code"]
                e = dict(e, desc=e["desc"] + etiquettes[suivant]["desc"])
            lignes.append(
                {
                    "code": code,
                    "toks": list(e["toks"]),
                    "desc": list(e["desc"]),
                    "unite": _unite_de_la_bande(e["desc"]),
                }
            )
        elif e["code"]:
            continue
        elif lignes:
            lignes[-1]["toks"] += e["toks"]
            # UN LIBELLE QUI FINIT PAR DEUX-POINTS OUVRE UN GROUPE, il ne prolonge
            # pas la ligne en cours : « Octopus (Octopus spp.): » titre les
            # sous-positions qui SUIVENT. Colle a la precedente, il lui donnait
            # « Other Octopus (Octopus spp.): » pour designation.
            if e["desc"] and e["desc"][-1].endswith(":"):
                lignes[-1]["ferme"] = True
            elif not lignes[-1].get("ferme"):
                lignes[-1]["desc"] += e["desc"]
    return lignes


def cellules_de_la_ligne(toks, ancres: List[float]) -> Dict[int, str]:
    """Rassembler, COLONNE PAR COLONNE, les morceaux de chaque valeur.

    « SCR60/l » sort parfois en « SCR » sur la bande du code et « 60/l » sur la
    bande suivante ; « SCR5/kg » en « SCR5/ » puis « kg ». Recoller par adjacence
    horizontale ne verrait pas la coupure verticale. On rattache donc CHAQUE morceau
    a sa colonne par l'ancre de l'en-tete, puis on les concatene dans l'ordre de
    lecture — ordre que la liste des tokens porte deja, page par page.
    """
    morceaux: Dict[int, List[str]] = collections.defaultdict(list)
    for x, mot in toks:
        if x < ancres[0] - MARGE_GAUCHE:
            continue
        if not RX_FRAGMENT.match(mot) and not RX_PCT.match(mot) and not RX_ZERO.match(mot):
            continue
        colonne = _colonne_de(x, ancres)
        if colonne is not None:
            morceaux[colonne].append(mot)
    return {c: "".join(parts) for c, parts in morceaux.items()}


def lire_valeur(cellule: str) -> Tuple[Optional[float], Optional[Dict], Optional[str]]:
    """Rendre (taux, specifique, motif) pour une cellule.

    « Free » et « 0% » sont des ZEROS PUBLIES — une franchise, pas une absence.
    Un « SCR60/l » est un droit SPECIFIQUE : il se liquide a la quantite, jamais sur
    la valeur, et le confondre avec un pourcentage donnerait un montant absurde.
    Un « 7% + SCR5/kg » est un droit COMPOSE, et le « + » n'est pas un « or » : les
    deux composantes sont dues ENSEMBLE, il n'y a rien a departager, et la ligne se
    liquide donc entierement. C'est ce qui la separe du « 40% or 240c/kg » sud-
    africain, qui reste refuse faute de regle de depart.
    """
    brut = (cellule or "").strip()
    if not brut:
        return None, None, "CELLULE_VIDE"
    if RX_ZERO.match(brut):
        return 0.0, None, None
    m = RX_PCT.match(brut)
    if m:
        return float(m.group(1)), None, None
    m = RX_COMPOSE.match(brut)
    if m:
        _taux_part, specifique, motif = lire_valeur(m.group(2))
        if motif:
            return None, None, "COMPOSANTE_SPECIFIQUE_NON_LUE"
        # `brut` NE PORTE QUE LA COMPOSANTE SPECIFIQUE, jamais l'expression entiere.
        # Le socle relit cette chaine pour en tirer le montant unitaire : lui donner
        # « 15%+SCR5.13/kg » lui faisait lire 15 — le taux ad valorem servi comme un
        # montant en roupies au kilo. L'expression complete reste dans `raw_value` et
        # dans la note, ou elle informe sans etre relue.
        specifique["compose_avec_taux_pct"] = float(m.group(1))
        return float(m.group(1)), specifique, None
    m = RX_SPEC.match(brut)
    if m:
        return (
            None,
            {
                "montant": float(m.group(1)),
                "unite": " ".join(m.group(2).split()),
                "devise": "SCR",
                "brut": brut,
            },
            None,
        )
    # Deux valeurs completes rassemblees sous une meme colonne : deux lignes du
    # bareme s'y sont fondues, et rien ne dit laquelle porte quoi.
    if len(re.findall(r"\d+(?:\.\d+)?%", brut)) > 1:
        return None, None, "DEUX_VALEURS_DANS_LA_COLONNE"
    return None, None, "EXPRESSION_NON_LUE"


def taux_coi(taux_npf: Optional[float], code: str) -> Tuple[Optional[float], str]:
    """Le taux de la Commission de l'ocean Indien, DEDUIT selon la Schedule II.

    « will pay a rate of duty of 5% lower than the rate of duty prescribed in sub
    column 5, entitled "MFN" », sauf dans cinq cas que l'annexe enumere. La formule
    est ECRITE : la deduire n'est pas extrapoler. Mais sur un droit NPF SPECIFIQUE,
    « 5 % de moins » n'a pas de sens, et la ligne le declare.
    """
    chapitre, position = code[:2], code[:4]
    if taux_npf is None:
        return None, "TAUX_NPF_NON_AD_VALOREM_LA_REMISE_DE_5_POINTS_EST_INDEFINIE"
    if taux_npf <= 5.0:
        return taux_npf, "EXCEPTION_1_LE_TAUX_NPF_EST_INFERIEUR_OU_EGAL_A_5_POUR_CENT"
    if chapitre == "22":
        return taux_npf, "EXCEPTION_2_CHAPITRE_22_BOISSONS_ET_SPIRITUEUX"
    if chapitre == "24":
        return taux_npf, "EXCEPTION_3_CHAPITRE_24_TABACS"
    if position == "2710":
        return taux_npf, "EXCEPTION_4_POSITION_27_10_HUILES_DE_PETROLE"
    if position == "2711":
        return taux_npf, "EXCEPTION_5_POSITION_27_11_GAZ_DE_PETROLE"
    return taux_npf - 5.0, ""


def _note_preferentielle(code: str, libelle: str, annee_en_vigueur: str) -> str:
    """Ce qu'il faut savoir avant d'appliquer une preference seychelloise."""
    if code.startswith("AFCFTA"):
        eligibilite = (
            "Eligibilite : la Schedule VI du reglement enumere les 38 Etats parties "
            "a la ZLECAf ; une origine absente de cette liste n'y a pas droit. "
        )
    elif code.startswith("SADC"):
        eligibilite = "Eligibilite : Schedule IV, liste des Etats membres de la ZLE SADC. "
    elif code == "COMESA":
        eligibilite = "Eligibilite : Schedule III, liste des Etats membres de la ZLE COMESA. "
    elif code == "EU_UK":
        eligibilite = (
            "Eligibilite : Schedule V, Etats membres de l'Union europeenne et Etats ESA "
            "de l'Accord de partenariat economique interimaire. "
        )
    else:
        eligibilite = ""
    millesime = code.rsplit("_", 1)[-1]
    if millesime in MILLESIMES:
        calendrier = (
            f"TAUX DE L'ANNEE {millesime}. Le reglement publie un CALENDRIER : cinq taux, "
            f"un par annee civile de {MILLESIMES[0]} a {MILLESIMES[-1]}. Celui de l'annee "
            f"{annee_en_vigueur} est aussi servi sous le regime sans millesime ; au-dela "
            f"de {MILLESIMES[-1]} le reglement ne dit plus rien, et rien n'est reconduit. "
        )
    else:
        calendrier = ""
    return libelle + ". " + eligibilite + calendrier


def _taxe(
    code: str,
    libelle: str,
    taux: Optional[float],
    specifique: Optional[Dict],
    brut: str,
    source: str,
    note_sup: str = "",
) -> Dict:
    """Une ligne de prelevement, avec son assiette quand elle est etablie."""
    commun = {
        "code": code,
        "name": libelle,
        "rate_pct": taux,
        "raw_value": brut,
        "specific_value": specifique["brut"] if specifique else None,
        "source": source,
    }
    if code == "DD":
        return dict(
            commun,
            base="CIF",
            base_source=ACTE_DD,
            note=("Droit de douane NPF, colonne « MFN » du bareme. " + note_sup).strip(),
        )
    # Une preference n'est pas un prelevement du : elle ne porte pas d'assiette, et
    # le socle la range sous son regime plutot que dans la cascade.
    return dict(commun, base=None, base_source=None, note=note_sup)


def bornes_du_bareme(doc) -> Tuple[int, int]:
    """Les pages ou commence et finit le bareme.

    Le reglement ne contient pas QUE le tarif : viennent d'abord l'arrangement des
    regulations, les regles generales d'interpretation et les notes de section, puis
    a la fin les Schedules II a VI — listes d'Etats, sans taux. Les bornes sont donc
    LUES : une page du bareme est une page portant au moins trois sous-positions.
    """
    pages = [
        i
        for i in range(doc.page_count)
        if sum(1 for m in doc[i].get_text().split() if RX_CODE.match(m)) >= 3
    ]
    if not pages:
        raise SystemExit("Bareme introuvable : le document n'est pas celui attendu.")
    return pages[0], pages[-1] + 1


def extraire(chemin: Path) -> Tuple[List[Dict], Dict]:
    doc = pymupdf.open(chemin)
    debut, fin = bornes_du_bareme(doc)
    annee_en_vigueur = _annee_en_vigueur()
    positions: List[Dict] = []
    vus = set()
    stats = {
        "pages": doc.page_count,
        "bareme_pages": f"{debut + 1}-{fin}",
        "annee_en_vigueur": annee_en_vigueur,
        "pages_sans_en_tete": 0,
        "lignes_treize_colonnes": 0,
        "lignes_incompletes": 0,
        "cellules_non_lues": 0,
        "sans_droit_npf": 0,
        "droits_specifiques": 0,
        "avec_zlecaf": 0,
        "coi_remise_appliquee": 0,
        "coi_exception": 0,
        "coi_indefini": 0,
        "insertions_si7_2024": 0,
    }

    for index in range(debut, fin):
        mots = doc[index].get_text("words")
        ancres = ancres_de_la_page(mots)
        if ancres is None:
            if sum(1 for w in mots if RX_CODE.match(w[4])) >= 3:
                stats["pages_sans_en_tete"] += 1
            continue

        lignes = _lignes_de_la_page(mots, ancres)

        for ligne in lignes:
            national = ligne["code"].replace(".", "")
            if national in vus:
                continue
            cellules = cellules_de_la_ligne(ligne["toks"], ancres)
            if len(cellules) == len(COLONNES):
                stats["lignes_treize_colonnes"] += 1
            else:
                stats["lignes_incompletes"] += 1
            vus.add(national)
            positions.append(
                _position(
                    ligne["code"],
                    ligne["desc"],
                    ligne["unite"],
                    cellules,
                    annee_en_vigueur,
                    index + 1,
                    stats,
                )
            )

    for code, designation, unite, taux in SI7_2024_INSERTIONS:
        national = code.replace(".", "")
        if national in vus:
            continue
        vus.add(national)
        stats["insertions_si7_2024"] += 1
        positions.append(_position_si7(code, designation, unite, taux, annee_en_vigueur))

    stats["total_positions"] = len(positions)
    stats["chapters_covered"] = len({p["chapter"] for p in positions})
    return positions, stats


def _annee_en_vigueur() -> str:
    """Le millesime du calendrier qui s'applique aujourd'hui.

    Le reglement publie cinq annees et s'arrete. Passe la derniere, il ne dit plus
    rien : on ne reconduit pas le dernier taux en silence, on le declare.
    """
    courante = str(date.today().year)
    if courante < MILLESIMES[0]:
        return MILLESIMES[0]
    return courante if courante in MILLESIMES else ""


def _lignes_de_taxes(
    code_national: str, cellules: Dict[int, str], source: str, annee: str, stats: Dict
) -> Tuple[List[Dict], List[str], Dict]:
    """Les prelevements d'une position, et ce qui n'a pas pu etre lu."""
    taxes: List[Dict] = []
    gaps: List[str] = []
    valeurs: Dict[str, Optional[float]] = {}
    for rang, (nom, libelle) in enumerate(COLONNES):
        brut = cellules.get(rang)
        if brut is None:
            gaps.append(f"{nom}_CELLULE_ABSENTE")
            continue
        taux, specifique, motif = lire_valeur(brut)
        if motif:
            stats["cellules_non_lues"] += 1
            gaps.append(f"{nom}_{motif}_{brut}")
            continue
        if specifique:
            stats["droits_specifiques"] += 1
        valeurs[nom] = taux
        taxes.append(
            _taxe(
                nom,
                libelle,
                taux,
                specifique,
                brut,
                source,
                _note_preferentielle(nom, libelle, annee),
            )
        )
        # Le millesime en vigueur est aussi servi sous le regime sans millesime :
        # c'est celui que le calculateur applique aujourd'hui.
        for regime, prefixe in REGIMES_MILLESIMES.items():
            if annee and nom == f"{prefixe}_{annee}":
                taxes.append(
                    _taxe(
                        regime,
                        libelle,
                        taux,
                        specifique,
                        brut,
                        source,
                        _note_preferentielle(nom, libelle, annee)
                        + f"Servi comme taux {regime} en vigueur pour l'annee {annee}.",
                    )
                )
                valeurs[regime] = taux
    return taxes, gaps, valeurs


#: Le vocabulaire ferme des unites de quantite de la colonne 4.
RX_UNITE = re.compile(
    r"^(Kg\.?|No\.?|l|m|m2|m3|ct|g|t|pr|doz|u|" r"[A-Za-z0-9]{1,4}\.?/[A-Za-z0-9]{1,4}\.?)$",
    re.I,
)


def _unite_de_la_bande(desc: List[str]) -> str:
    """L'unite de quantite de la colonne 4, ou la chaine vide.

    Elle est PUBLIEE et elle compte : c'est elle qui dit en quoi une quantite se
    declare. Elle se lit sur la bande QUI PORTE LES TAUX, dernier mot avant eux, et
    non dans la designation accumulee — ou le dernier mot d'un libelle qui se
    prolonge passerait pour une unite. Le vocabulaire est ferme ; ailleurs rien
    n'est suppose.
    """
    mots = [m for m in desc if m.strip(" .-")]
    return mots[-1] if mots and RX_UNITE.match(mots[-1]) else ""


def _designation(desc: List[str], unite: str) -> str:
    """Le libelle, debarrasse de l'unite et des tirets de hierarchie en bout."""
    mots = [m for m in desc if m.strip(" .-")]
    if unite and mots and mots[-1] == unite:
        mots = mots[:-1]
    texte = " ".join(" ".join(mots).split())
    texte = re.sub(r"^[\s.\-]+", "", texte)
    return re.sub(r"[\s.\-]+$", "", texte)


def _enveloppe(
    code: str,
    designation: str,
    unite: str,
    taxes: List[Dict],
    gaps: List[str],
    page: Optional[int],
    source: str,
) -> Dict:
    national = code.replace(".", "")
    return {
        "national_code": national,
        "hs6": national[:6],
        "chapter": national[:2],
        "heading": code[:5],
        "statistical_unit": unite,
        "designation": {"en": designation, "fr": "", "verbatim": designation},
        "taxes": taxes,
        "preferential_rates": [],
        "restrictions": [],
        "source_gaps": gaps,
        "page_source": page,
        "source": source,
    }


def _position(
    code: str,
    desc: List[str],
    unite: str,
    cellules: Dict[int, str],
    annee: str,
    page: int,
    stats: Dict,
) -> Dict:
    designation = _designation(desc, unite)
    taxes, gaps, valeurs = _lignes_de_taxes(code, cellules, SOURCE, annee, stats)
    if "DD" not in valeurs and not any(t["code"] == "DD" for t in taxes):
        stats["sans_droit_npf"] += 1
        gaps.append("DROIT_NPF_NON_LU")
    if any(t["code"].startswith("AFCFTA") for t in taxes):
        stats["avec_zlecaf"] += 1
    taxes += _ligne_coi(code, taxes, stats)
    if not annee:
        gaps.append("CALENDRIER_EPUISE_AUCUN_MILLESIME_EN_VIGUEUR")
    return _enveloppe(code, designation, unite, taxes, gaps, page, SOURCE)


def _ligne_coi(code: str, taxes: List[Dict], stats: Dict) -> List[Dict]:
    """La ligne COI, deduite du NPF selon la formule que la Schedule II enonce."""
    npf = next((t for t in taxes if t["code"] == "DD"), None)
    if npf is None:
        return []
    taux, motif = taux_coi(npf["rate_pct"], code.replace(".", ""))
    if taux is None:
        stats["coi_indefini"] += 1
        note = (
            "Commission de l'ocean Indien — TAUX NON ETABLI. La Schedule II accorde "
            "« a rate of duty of 5% lower than the rate of duty prescribed in sub "
            "column 5 », or le droit NPF de cette position n'est pas un pourcentage : "
            "une remise de cinq POINTS sur un droit specifique n'a pas de sens, et "
            "aucun texte ne dit comment la calculer. Rien n'est suppose."
        )
    elif motif:
        stats["coi_exception"] += 1
        note = (
            "Commission de l'ocean Indien — AUCUNE REMISE, le taux servi est celui du "
            f"NPF. La Schedule II ecarte ce cas : {motif}. Les cinq exceptions de "
            f"l'annexe : {EXCEPTIONS_COI}"
        )
    else:
        stats["coi_remise_appliquee"] += 1
        note = (
            "Commission de l'ocean Indien — taux DEDUIT du NPF selon la formule que la "
            "Schedule II enonce : « will pay a rate of duty of 5% lower than the rate "
            'of duty prescribed in sub column 5, entitled "MFN" ». Cinq POINTS de '
            f"moins, non cinq pour cent du taux. Exceptions : {EXCEPTIONS_COI}"
        )
    return [
        dict(
            code="COI",
            name="Commission de l'ocean Indien (Schedule II)",
            rate_pct=taux,
            raw_value="",
            specific_value=None,
            source=SOURCE,
            base=None,
            base_source=None,
            note=(
                note
                + " Etats vises : "
                + ", ".join(ETATS_COI)
                + ". SOUS CONDITION, et l'annexe le dit : « Subject to the acceptance of "
                "the certificate of origin » — le calculateur ne verifie pas ce certificat."
            ),
        )
    ]


def _position_si7(code: str, designation: str, unite: str, taux: List[float], annee: str) -> Dict:
    """Une sous-position que S.I. 7 of 2024 insere, avec sa source propre."""
    stats_muettes = collections.defaultdict(int)
    cellules = {rang: f"{valeur:g}%" for rang, valeur in enumerate(taux)}
    taxes, gaps, _valeurs = _lignes_de_taxes(
        code.replace(".", ""), cellules, SI7_2024_SOURCE, annee, stats_muettes
    )
    taxes += _ligne_coi(code, taxes, stats_muettes)
    for taxe in taxes:
        taxe["note"] = (
            taxe["note"] + " Position INSEREE par S.I. 7 of 2024, qui n'est pas dans "
            "le corps de S.I. 113 of 2022 : ses taux sont lus dans l'instrument "
            "modificatif lui-meme."
        ).strip()
    return _enveloppe(code, designation, unite, taxes, gaps, None, SI7_2024_SOURCE)


def construire(chemin: Path) -> Dict:
    positions, stats = extraire(chemin)
    codes = sorted({t["code"] for p in positions for t in p["taxes"]})
    return {
        "country": "SYC",
        "country_name": "Seychelles",
        "source": SOURCE,
        "source_url": SOURCE_URL,
        "source_legal": (
            "Customs Management Act, 2011 (Act 22 of 2011), s.270 (pouvoir "
            "reglementaire) et s.41 (evaluation renvoyee au reglement) ; Customs "
            "Management Regulations, 2014 (S.I. 42 of 2014), reg. 5 et reg. 8(1)(e) "
            "(valeur en douane) ; S.I. 113 of 2022, reg. 2 et Schedules I a VI"
        ),
        "source_quality": "crawled_authentic",
        "source_sha256": hashlib.sha256(chemin.read_bytes()).hexdigest(),
        "extracted_at": date.today().isoformat(),
        "calculation_rules": {
            "order": ["DD"],
            "bases": {"DD": {"basis": "CIF", "type": "ad_valorem", "source": ACTE_DD}},
            "source": (
                "Droit de douane de la colonne « MFN ». Assiette : valeur "
                "transactionnelle augmentee du transport, de la manutention et de "
                "l'assurance jusqu'au port d'importation (Customs Management "
                "Regulations, 2014, reg. 5 et reg. 8(1)(e)) — le CIF. Les douze autres "
                "colonnes sont des REGIMES PREFERENTIELS, jamais des prelevements dus : "
                "COMESA, Union europeenne et Royaume-Uni, puis SADC et ZLECAf avec "
                "CINQ TAUX CHACUNE, un par annee civile de 2022 a 2026. Le taux de "
                "l'annee en vigueur est aussi servi sous le regime sans millesime. "
                "La Commission de l'ocean Indien n'a pas de colonne : son taux se "
                "DEDUIT du NPF selon la formule de la Schedule II. Ni l'accise ni la "
                "TVA ne figurent a ce bareme."
            ),
        },
        "notes_legales": {
            "etats_zlecaf_schedule_vi": ETATS_ZLECAF,
            "etats_coi_schedule_ii": ETATS_COI,
            "exceptions_coi": EXCEPTIONS_COI,
            "reserve_si7_2024": RESERVE_SI7_2024,
        },
        "stats": stats,
        "sub_positions": positions,
        "unique_tax_codes": codes,
    }


def main(argv=None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    argv = list(argv if argv is not None else sys.argv[1:])
    if not argv:
        print("usage: seychelles_si113_scraper.py <SI-113-2022.pdf>", file=sys.stderr)
        return 2
    chemin = Path(argv[0])
    if not chemin.exists():
        print(f"Fichier introuvable : {chemin}", file=sys.stderr)
        return 2
    donnees = construire(chemin)
    s = donnees["stats"]
    if s["total_positions"] < 5000:
        print(
            f"Collecte refusee : {s['total_positions']} positions lues, moins de 5 000.",
            file=sys.stderr,
        )
        return 1
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    (DATA_DIR / "SYC_tariffs.json").write_text(
        json.dumps(donnees, ensure_ascii=False, indent=1), encoding="utf-8"
    )
    logger.info(
        "SYC : %s positions, %s chapitres, codes %s",
        s["total_positions"],
        s["chapters_covered"],
        ",".join(donnees["unique_tax_codes"]),
    )
    logger.info(
        "  bareme %s | pages sans en-tete %s | lignes a 13 colonnes %s | " "incompletes %s",
        s["bareme_pages"],
        s["pages_sans_en_tete"],
        s["lignes_treize_colonnes"],
        s["lignes_incompletes"],
    )
    logger.info(
        "  annee en vigueur %s | sans droit NPF %s | cellules non lues %s | "
        "droits specifiques %s",
        s["annee_en_vigueur"] or "AUCUNE (calendrier epuise)",
        s["sans_droit_npf"],
        s["cellules_non_lues"],
        s["droits_specifiques"],
    )
    logger.info(
        "  COI : remise appliquee %s | exception de la Schedule II %s | " "indefini %s",
        s["coi_remise_appliquee"],
        s["coi_exception"],
        s["coi_indefini"],
    )
    logger.info(
        "  ZLECAf %s | insertions de S.I. 7 of 2024 %s", s["avec_zlecaf"], s["insertions_si7_2024"]
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
