#!/usr/bin/env python3
"""Tarif douanier de l'Angola — Pauta Aduaneira 2024.

Source : DECRETO LEGISLATIVO PRESIDENCIAL n.º 1/24 du 3 janvier 2024, publie au
Diario da Republica, I Serie n.º 2, qui approuve la « Pauta Aduaneira dos Direitos
de Importacao e Exportacao » en version 2022 du Systeme harmonise et ses Instrucoes
Preliminares, et abroge le Decreto Legislativo Presidencial n.º 10/19 du 29 novembre
2019. 345 pages, servi par le Ministere des Finances angolais.

CE DOCUMENT EST UN SCAN INTEGRAL : ZERO OCTET DE COUCHE TEXTE.
C'est ce qui l'avait laisse de cote jusqu'ici, et c'est ce que ce collecteur leve.
Il ne lit pas un texte, il lit une IMAGE — et il ne demande pas a l'OCR de retrouver
une mise en page, parce qu'un OCR de pleine page rend « r]ao » pour un « 30 » et
« EE » pour un code. Le bareme est un TABLEAU REGLE : ses traits se detectent sur
l'image, chaque colonne est decoupee en bande, et chaque bande est lue avec LE SEUL
VOCABULAIRE QU'ELLE PEUT CONTENIR. Les codes sortent alors intacts et les taux
aussi.

LA CARTE DES COLONNES EST DANS LE TEXTE, PAS DEDUITE DE L'EN-TETE.
Instrucoes Preliminares, article 2, liste des abreviations :
  « R.G. — Regime Geral ; SADC — Comunidade de Desenvolvimento da Africa Austral ;
    UA — Uniao Africana ; ZCLCA — Zona de Comercio Livre Continental Africana ;
    PREF — Preferenciais ; CIF — Cost, Insurance and Freight »
et article 43 :
  « 1. Os beneficios fiscais aduaneiros automaticos e reais [...] sao os indicados a
    taxa LIVRE (0%), na coluna 4 da mesma.
    2. As colunas 5 (SADC) e 6 (ZCLCA), estao RESERVADAS a aplicacao de taxas
    preferenciais, A SEREM DEFINIDAS EM LEGISLACAO ESPECIFICA, no ambito da adesao e
    implementacao do Protocolo sobre Trocas Comerciais da Comunidade de
    Desenvolvimento da Africa Austral (SADC) e da Zona de Comercio Livre Continental
    Africana (ZCLCA). »

DEUX CONSEQUENCES, ET ELLES SONT DECISIVES.

  — « LIVRE » EST UN ZERO PUBLIE, et le texte le dit entre parentheses : « taxa
    Livre (0%) ». C'est meme un BENEFICE FISCAL nomme, pas une case oubliee. Il y en
    a 2 151 sur 5 835 positions, plus du tiers du tarif. Une premiere passe de ce
    collecteur, qui ne cherchait que des chiffres dans la colonne 4, les effacait
    toutes : un tiers du tarif se serait servi « droit indisponible » alors que la
    loi lui donne un droit, et ce droit est zero.

  — L'ANGOLA PUBLIE UNE COLONNE ZLECAf ET LA LAISSE VIDE, EXPRES. Les colonnes 5 et
    6 sont « reservadas [...] a serem definidas em legislacao especifica » : elles
    attendent leur texte d'application. Verifie sur les 5 835 positions du document,
    elles ne portent AUCUNE valeur. Servir une preference ZLECAf angolaise serait
    donc inventer une exoneration que le legislateur a explicitement remise a plus
    tard. Le collecteur porte la colonne, vide, avec son motif.

L'ASSIETTE EST LE CIF, ET DEUX TEXTES SE REPONDENT.
Instrucoes Preliminares, article 58 :
  « 2. Os direitos aduaneiros incidentes na importacao sao [...] calculados mediante
    a aplicacao das taxas indicadas nas respectivas colunas de tributacao da Pauta
    Aduaneira. 3. Os emolumentos gerais aduaneiros sao calculados mediante a
    aplicacao da taxa de 2%. [...] 5. As taxas a que se referem os numeros
    anteriores sao taxas «ad valorem» e INCIDEM SOBRE O VALOR ADUANEIRO da mercadoria
    expresso em moeda nacional. »
Et le Codigo Aduaneiro (Decreto-Lei n.º 05/06), article 117.º n.º 2, dit ce QU'EST ce
valor aduaneiro : le prix paye augmente du transport, de la manutention et de
l'assurance jusqu'au port d'importation — le CIF, que la liste des abreviations de
l'IPP nomme d'ailleurs elle-meme.

UN SECOND PRELEVEMENT EST DU SUR LA MEME ASSIETTE : les EMOLUMENTOS GERAIS
ADUANEIROS, 2 % du valor aduaneiro (art. 58 n.º 3 et n.º 5). Ils ne sont pas dans les
colonnes du bareme — c'est une regle generale de l'IPP — et ils survivent aux
exonerations : l'article 43 n.º 4 exempte « os direitos aduaneiros, COM EXCEPCAO da
taxa devida pela prestacao de servicos ». Deux taux sectoriels existent, 0,1 % pour le
petrole et 2 % pour les mines (art. 58 n.º 4) ; ils dependent d'un regime que le
calculateur ne connait pas et ne sont pas appliques.

CE QUI N'EST PAS COLLECTE ICI : l'Imposto Especial de Consumo et l'Imposto sobre o
Valor Acrescentado. L'IPP les nomme dans ses abreviations mais ne donne ni leurs taux
ni leur champ ; ils relevent de leurs propres codes, non lus ici.
"""

import collections
import csv
import hashlib
import json
import logging
import re
import subprocess
import sys
from datetime import date
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pymupdf

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "crawled"
SOURCE = (
    "Pauta Aduaneira dos Direitos de Importacao e Exportacao — Decreto Legislativo "
    "Presidencial n.º 1/24 du 3 janvier 2024, Diario da Republica I Serie n.º 2"
)
SOURCE_URL = (
    "https://www.ucm.minfin.gov.ao/cs/groups/public/documents/document/"
    "aw4z/nzcw/~edisp/minfin3770211.pdf"
)
ACTE_DD = (
    "Instrucoes Preliminares da Pauta, art. 58.º n.º 5 — « As taxas [...] sao taxas "
    "« ad valorem » e incidem sobre o valor aduaneiro da mercadoria » ; et "
    "Codigo Aduaneiro (Decreto-Lei n.º 05/06), art. 117.º n.º 2, qui ajoute au prix "
    "paye le transport, la manutention et l'assurance jusqu'au port d'importation — "
    "le CIF, que la liste des abreviations de l'IPP nomme elle-meme"
)

#: Resolution de rendu. A 300 points par pouce, les chiffres d'une cellule de taux
#: font une vingtaine de pixels de haut : c'est le minimum pour que l'OCR ne confonde
#: pas un 5 et un 6.
DPI = 300
#: Le code d'une sous-position angolaise. Le bareme porte aussi des positions a
#: quatre chiffres (« 28.18 ») et des intitules de groupe : eux ne portent pas de
#: taux et ne deviennent pas des positions.
RX_SOUS_POSITION = re.compile(r"^\d{4}\.\d{2}\.\d{2}$")
#: Le vocabulaire ferme d'une cellule de taux : un nombre, ou « Livre ».
RX_TAUX = re.compile(r"^\d{1,3}(?:[.,]\d{1,2})?$")
RX_LIVRE = re.compile(r"^livre$", re.I)
#: Le vocabulaire des unites de quantite de la colonne 3.
RX_UNITE = re.compile(r"^(Kg|Un|U|l|L|m|m2|m3|g|t|ct|par|dz|[0-9]{1,4}\s?[A-Za-z]{1,3})$")

#: Les six colonnes du bareme, dans l'ordre ou l'IPP les numerote.
COLONNES = [
    (0, "code", "col. 1 — codigo"),
    (1, "designacao", "col. 2 — designacao das mercadorias"),
    (2, "unidade", "col. 3 — UQ, unidade de quantidade"),
    (3, "DD", "col. 4 — R.G, Regime Geral : le droit de douane de droit commun"),
    (4, "SADC", "col. 5 — PREF. SADC"),
    (5, "AFCFTA", "col. 6 — PREF. U.A / ZCLCA, Zone de libre-echange continentale africaine"),
]
#: Le vocabulaire de chaque colonne. Lire une cellule etroite dans une page entiere
#: fait prendre a tesseract les traits du tableau pour des lettres.
CONFIGS = {
    0: ["--psm", "6", "-c", "tessedit_char_whitelist=0123456789."],
    1: ["-l", "por", "--psm", "6"],
    2: ["-l", "por", "--psm", "6"],
    3: ["-l", "por", "--psm", "6", "-c", "tessedit_char_whitelist=0123456789.,Livrel"],
    4: ["-l", "por", "--psm", "6", "-c", "tessedit_char_whitelist=0123456789.,Livrel"],
    5: ["-l", "por", "--psm", "6", "-c", "tessedit_char_whitelist=0123456789.,Livrel"],
}

#: Emolumentos gerais aduaneiros — IPP art. 58.º n.º 3.
EMOLUMENT_TAUX = 2.0
EMOLUMENT_NOTE = (
    "Emolumentos gerais aduaneiros. TAUX GENERAL de 2 % pose par l'article 58.º n.º 3 "
    "des Instrucoes Preliminares, sur la meme assiette que le droit — le valor "
    "aduaneiro (n.º 5). Il n'est pas dans les colonnes du bareme : c'est une regle "
    "generale, et elle survit aux exonerations, l'article 43.º n.º 4 exemptant « os "
    "direitos aduaneiros, com excepcao da taxa devida pela prestacao de servicos ». "
    "DEUX TAUX SECTORIELS EXISTENT ET NE SONT PAS APPLIQUES : 0,1 % pour le secteur "
    "petrolier et 2 % pour le secteur minier (art. 58.º n.º 4), qui dependent d'un "
    "regime douanier que le calculateur ne connait pas."
)
PREFERENCE_RESERVEE = (
    "COLONNE PUBLIEE ET VIDE, ET C'EST VOULU. L'article 43.º n.º 2 des Instrucoes "
    "Preliminares dit que « as colunas 5 (SADC) e 6 (ZCLCA) estao RESERVADAS a "
    "aplicacao de taxas preferenciais, A SEREM DEFINIDAS EM LEGISLACAO ESPECIFICA, no "
    "ambito da adesao e implementacao do Protocolo sobre Trocas Comerciais da "
    "Comunidade de Desenvolvimento da Africa Austral (SADC) e da Zona de Comercio "
    "Livre Continental Africana (ZCLCA) ». Verifie sur les 5 835 positions du "
    "document : aucune ne porte de valeur. Servir une preference angolaise serait "
    "donc inventer une exoneration que le legislateur a lui-meme remise a plus tard."
)


def _grouper(valeurs: List[int], tolerance: int = 3) -> List[int]:
    """Reduire une suite d'abscisses contigues au centre de chaque trait."""
    out: List[List[int]] = []
    for x in valeurs:
        if out and x - out[-1][-1] <= tolerance:
            out[-1].append(x)
        else:
            out.append([x])
    return [sum(g) // len(g) for g in out]


def tableaux(sombre, largeur: int, hauteur: int) -> List[Dict]:
    """Les tableaux de la page, chacun avec ses traits verticaux et horizontaux.

    LE SEUIL NE PEUT PAS ETRE RAPPORTE A LA HAUTEUR DE LA PAGE. Page 186 du Diario,
    le bareme n'occupe que le bas de la feuille : ses traits verticaux font 150
    pixels sur 3 508, et un seuil « un quart de la page » les rejetait tous — la page
    entiere etait perdue. On cherche donc d'abord les traits HORIZONTAUX, longs quoi
    qu'il arrive ; on en deduit l'etendue verticale du tableau ; et l'on ne cherche
    les traits verticaux que LA, rapportes a la hauteur du tableau.
    """
    hor = _grouper([y for y in range(hauteur) if sombre[y, :].sum() > largeur * 0.35])
    if len(hor) < 3:
        return []
    groupes: List[List[int]] = []
    for y in hor:
        if groupes and y - groupes[-1][-1] <= 300:
            groupes[-1].append(y)
        else:
            groupes.append([y])

    sortie = []
    for bornes in groupes:
        if len(bornes) < 3:
            continue
        haut, bas = bornes[0], bornes[-1]
        colonne = sombre[haut:bas, :]
        vert = _grouper([x for x in range(largeur) if colonne[:, x].sum() > (bas - haut) * 0.40])
        sortie.append({"vert": vert, "hor": bornes})
    return sortie


def _tsv(chemin: Path, config: List[str]) -> List[Dict]:
    """Les mots d'une image, avec leurs coordonnees et la confiance de l'OCR."""
    rendu = subprocess.run(
        ["tesseract", str(chemin), "stdout", *config, "tsv"],
        capture_output=True,
        text=True,
        timeout=300,
    )
    mots = []
    for r in csv.DictReader(rendu.stdout.splitlines(), delimiter="\t", quoting=csv.QUOTE_NONE):
        texte = (r.get("text") or "").strip()
        if r.get("level") == "5" and texte and float(r.get("conf") or -1) >= 0:
            mots.append(
                {
                    "x": int(r["left"]),
                    "y": int(r["top"]),
                    "w": int(r["width"]),
                    "h": int(r["height"]),
                    "conf": float(r["conf"]),
                    "t": texte,
                }
            )
    return mots


def _texte_utile(bande) -> Optional[int]:
    """L'abscisse ou le libelle s'arrete et ou commencent ses points de conduite.

    UNE LIGNE DE POINTS REND L'OCR AVEUGLE. « -- Outros.......................... »
    occupe 1 009 pixels de large dont 130 de texte : tesseract y voit une ligne
    presque vide, renonce a l'analyser et ne rend RIEN. 536 designations sur 5 830
    manquaient pour cette seule raison — « Outros », « Asininos », les libelles les
    plus courts et les plus frequents du bareme.

    Les points se distinguent du texte par leur HAUTEUR D'ENCRE : un point fait
    quelques pixels, une lettre en fait une vingtaine. On coupe donc la cellule la ou
    la hauteur d'encre retombe durablement sous le tiers de sa valeur maximale.
    """
    encre = bande < 128
    if not encre.any():
        return None
    # Les traits du tableau traversent la cellule de part en part : ils ne sont pas
    # de l'encre de texte.
    garde = np.array([encre[y].mean() <= 0.6 for y in range(bande.shape[0])])
    if not garde.any():
        return None
    utile = encre[garde]
    hauteurs = np.zeros(utile.shape[1], dtype=int)
    for x in range(utile.shape[1]):
        colonne = np.flatnonzero(utile[:, x])
        if colonne.size:
            hauteurs[x] = colonne[-1] - colonne[0] + 1
    if not hauteurs.any():
        return None
    seuil = max(4, int(hauteurs.max()) // 3)
    forts = np.flatnonzero(hauteurs >= seuil)
    return int(forts.max()) + 12 if forts.size else None


def _bande(y: int, hor: List[int]) -> Optional[int]:
    for i in range(len(hor) - 1):
        if hor[i] <= y < hor[i + 1]:
            return i
    return None


def lire_la_page(doc, index: int, dossier: Path) -> Tuple[Optional[List[Dict]], Dict]:
    """Les lignes d'une page, cellule par cellule.

    Une page dont la grille ne montre pas SES SEPT TRAITS VERTICAUX — les six
    colonnes de l'IPP — n'est pas une page de bareme, ou elle est deformee : elle
    n'est pas lue sur une grille supposee, elle est declaree.
    """
    from PIL import Image

    pm = doc[index].get_pixmap(dpi=DPI)
    a = np.frombuffer(pm.samples, dtype=np.uint8).reshape(pm.height, pm.width, pm.n)
    sombre = a[:, :, :3].mean(axis=2) < 128
    grilles = [g for g in tableaux(sombre, pm.width, pm.height) if len(g["vert"]) == 7]
    if not grilles:
        return None, {"motif": "GRILLE_NON_RECONNUE"}

    img = Image.fromarray(a[:, :, :3])
    sortie = []
    for numero, grille in enumerate(grilles):
        vert, hor = grille["vert"], grille["hor"]
        lignes: Dict[int, Dict[int, List[Dict]]] = {}
        for rang, (x0, x1) in enumerate(zip(vert, vert[1:])):
            if rang == 1:
                # La designation se lit CELLULE PAR CELLULE, rognee sur son texte :
                # en bande entiere, une ligne de points rend l'OCR aveugle.
                for r in range(len(hor) - 1):
                    haut, bas = hor[r], hor[r + 1]
                    if bas - haut < 12:
                        continue
                    cellule = a[haut:bas, x0 + 6 : x1 - 6, :3].mean(axis=2)
                    fin = _texte_utile(cellule)
                    if fin is None:
                        continue
                    cellule_img = dossier / f"p{index + 1:03d}_{numero}_d{r}.png"
                    img.crop((x0 + 6, haut, x0 + 6 + fin, bas)).save(cellule_img)
                    mots = _tsv(cellule_img, CONFIGS[1])
                    cellule_img.unlink(missing_ok=True)
                    for m in mots:
                        m["y"] += haut
                        m["x"] += x0 + 6
                        lignes.setdefault(r, {}).setdefault(1, []).append(m)
                continue
            bande_img = dossier / f"p{index + 1:03d}_{numero}_c{rang}.png"
            img.crop((x0 + 6, hor[0], x1 - 6, hor[-1])).save(bande_img)
            for m in _tsv(bande_img, CONFIGS[rang]):
                m["y"] += hor[0]
                m["x"] += x0 + 6
                r = _bande(m["y"] + m["h"] // 2, hor)
                if r is not None:
                    lignes.setdefault(r, {}).setdefault(rang, []).append(m)
            bande_img.unlink(missing_ok=True)

        for r in sorted(lignes):
            cellules = {}
            for rang, mots in lignes[r].items():
                mots.sort(key=lambda m: m["x"])
                cellules[rang] = {
                    "texte": " ".join(m["t"] for m in mots),
                    "conf": min(m["conf"] for m in mots),
                    # La confiance MOT PAR MOT sert a couper le bruit des points de
                    # conduite : voir `nettoyer_designation`.
                    "mots": [(m["t"], m["conf"]) for m in mots],
                }
            sortie.append({"tableau": numero, "rang": r, "cellules": cellules})
    return sortie, {"colonnes": [g["vert"] for g in grilles]}


def lire_taux(cellule: str) -> Tuple[Optional[float], Optional[str]]:
    """Rendre (taux, motif) pour une cellule de la colonne 4, 5 ou 6.

    « Livre » EST UN ZERO PUBLIE, et l'article 43.º n.º 1 le dit entre parentheses :
    « taxa Livre (0%) ». C'est un benefice fiscal nomme, pas une case oubliee.

    Rien n'est rattrape : « ivre », « Livre ivre », « 20. » sont des lectures
    abimees, et meme si l'on devine ce qu'elles voulaient dire, les deviner ici
    reviendrait a servir un droit que le collecteur n'a pas lu. Six cellules sur
    5 835 sont dans ce cas ; elles sont declarees.
    """
    brut = (cellule or "").strip()
    if not brut:
        return None, "CELLULE_VIDE"
    if RX_LIVRE.match(brut):
        return 0.0, None
    if RX_TAUX.match(brut):
        return float(brut.replace(",", ".")), None
    return None, "LECTURE_ABIMEE"


#: En deca de cette confiance, un mot de fin de libelle n'est pas un mot : c'est la
#: ligne de points qui mene la designation jusqu'a la colonne des taux, et que l'OCR
#: rend en charabia. Sur 0307.60.00, « - Caracois, excepto do mar.......... » sort en
#: « Caracois 95 | excepto 95 | do 88 | mar... 12 | stars 0 » : le dernier jeton est
#: du bruit pur, l'avant-dernier un vrai mot que ses points ont fait douter.
CONFIANCE_MINIMALE = 10.0
RX_POINTS = re.compile(r"[.\u2026]{2,}")


def nettoyer_designation(mots) -> str:
    """Le libelle, sans les points de conduite ni ce que l'OCR en a fait.

    Les points qui menent la designation jusqu'a la colonne des taux ne font pas
    partie du libelle, et l'OCR les rend en mots qui n'existent pas. On ne les
    reconnait pas a leur forme — ce serait deviner — mais a LA CONFIANCE QUE L'OCR
    LEUR DONNE LUI-MEME, qui s'effondre a la fin de la ligne.

    Deux precautions. Les points sont OTES AVANT de juger, sinon « mar... » — un vrai
    mot dont les points ont fait chuter la confiance a 12 — serait coupe avec eux.
    Et seule la QUEUE est coupee : un mot peu sur au milieu d'un libelle y porte du
    sens, et le retirer abimerait la designation au lieu de la nettoyer.
    """
    if isinstance(mots, str):
        suite = [(m, 100.0) for m in mots.split()]
    else:
        suite = [(m, c) for m, c in (mots or [])]
    suite = [(RX_POINTS.sub("", m), c) for m, c in suite]
    while suite and (not suite[-1][0] or suite[-1][1] < CONFIANCE_MINIMALE):
        suite.pop()
    texte = " ".join(m for m, _c in suite if m)
    texte = re.sub(r"^[\s.\-\u2013\u2014\u201c\u201d]+", "", " ".join(texte.split()))
    return re.sub(r"[\s.\-\u2013\u2014]+$", "", texte)


def _taxe(
    code: str, libelle: str, taux: Optional[float], brut: str, note: str, assiette: Optional[str]
) -> Dict:
    return {
        "code": code,
        "name": libelle,
        "rate_pct": taux,
        "raw_value": brut,
        "specific_value": None,
        "source": SOURCE,
        "base": assiette,
        "base_source": ACTE_DD if assiette else None,
        "note": note,
    }


def _position(code: str, cellules: Dict[int, Dict], page: int, stats: Dict) -> Dict:
    national = code.replace(".", "")
    designation = nettoyer_designation(
        (cellules.get(1) or {}).get("mots") or (cellules.get(1) or {}).get("texte", "")
    )
    unite_brute = ((cellules.get(2) or {}).get("texte", "") or "").strip()
    unite = unite_brute if RX_UNITE.match(unite_brute) else ""
    gaps: List[str] = []
    taxes: List[Dict] = []

    brut = ((cellules.get(3) or {}).get("texte", "") or "").strip()
    taux, motif = lire_taux(brut)
    if motif:
        stats["sans_droit"] += 1
        stats[f"motif_{motif.lower()}"] += 1
        gaps.append(f"DD_{motif}")
    else:
        if taux == 0.0:
            stats["droit_livre"] += 1
        taxes.append(
            _taxe(
                "DD",
                "Direitos de importacao — coluna 4, Regime Geral",
                taux,
                brut,
                "Droit de douane du REGIME GERAL, colonne 4 du bareme. "
                + (
                    "Le document ecrit « Livre », et l'article 43.º n.º 1 des "
                    "Instrucoes Preliminares en donne la valeur entre parentheses : "
                    "« taxa Livre (0%) ». C'est un BENEFICE FISCAL automatique et "
                    "reel que le texte nomme, pas une case oubliee. "
                    if taux == 0.0
                    else ""
                )
                + "Assiette : le valor aduaneiro (IPP art. 58.º n.º 5), que le Codigo "
                "Aduaneiro art. 117.º n.º 2 definit comme le prix paye augmente du "
                "transport, de la manutention et de l'assurance jusqu'au port — le CIF.",
                "CIF",
            )
        )

    # Les emolumentos gerais aduaneiros ne sont pas dans les colonnes : c'est une
    # regle generale de l'IPP, due sur la meme assiette que le droit.
    taxes.append(
        _taxe("EGA", "Emolumentos gerais aduaneiros", EMOLUMENT_TAUX, "2%", EMOLUMENT_NOTE, "CIF")
    )
    stats["emolument"] += 1

    # Les deux colonnes preferentielles sont publiees et vides, et le texte dit
    # pourquoi. Elles sont portees SANS TAUX, avec leur motif.
    for rang, nom, libelle in (
        (4, "SADC", "col. 5 — PREF. SADC"),
        (5, "AFCFTA", "col. 6 — PREF. U.A / ZCLCA"),
    ):
        contenu = ((cellules.get(rang) or {}).get("texte", "") or "").strip()
        if contenu:
            stats["preference_inattendue"] += 1
            gaps.append(f"{nom}_VALEUR_INATTENDUE_{contenu}")
            continue
        taxes.append(_taxe(nom, libelle, None, "", PREFERENCE_RESERVEE, None))
    gaps.append("PREFERENCES_RESERVEES_PAR_L_ARTICLE_43")

    if not designation:
        stats["sans_designation"] += 1
        gaps.append("DESIGNATION_NON_LUE")
    if not unite:
        gaps.append("UNITE_NON_LUE")

    return {
        "national_code": national,
        "hs6": national[:6],
        "chapter": national[:2],
        # Le document ecrit ses positions « 03.07 » : le socle porte la meme forme.
        "heading": f"{national[:2]}.{national[2:4]}",
        "statistical_unit": unite,
        "designation": {"pt": designation, "fr": "", "verbatim": designation},
        "taxes": taxes,
        "preferential_rates": [],
        "restrictions": [],
        "source_gaps": gaps,
        "page_source": page,
        "source": SOURCE,
    }


def extraire(chemin: Path, dossier: Path) -> Tuple[List[Dict], Dict]:
    doc = pymupdf.open(chemin)
    dossier.mkdir(parents=True, exist_ok=True)
    positions: List[Dict] = []
    vus = set()
    stats: Dict[str, int] = collections.Counter()
    stats.update({"pages": doc.page_count})

    for index in range(doc.page_count):
        lignes, _info = lire_la_page(doc, index, dossier)
        if lignes is None:
            stats["pages_sans_grille"] += 1
            continue
        stats["pages_lues"] += 1
        for ligne in lignes:
            cellules = {int(k): v for k, v in ligne["cellules"].items()}
            code = ((cellules.get(0) or {}).get("texte", "") or "").replace(" ", "")
            if not RX_SOUS_POSITION.match(code):
                continue
            national = code.replace(".", "")
            if national in vus:
                stats["doublon"] += 1
                continue
            vus.add(national)
            positions.append(_position(code, cellules, index + 1, stats))
        logger.info("  page %s : %s positions", index + 1, len(positions))

    stats["total_positions"] = len(positions)
    stats["chapters_covered"] = len({p["chapter"] for p in positions})
    return positions, dict(stats)


def construire(chemin: Path, dossier: Path) -> Dict:
    positions, stats = extraire(chemin, dossier)
    codes = sorted({t["code"] for p in positions for t in p["taxes"]})
    return {
        "country": "AGO",
        "country_name": "Angola",
        "source": SOURCE,
        "source_url": SOURCE_URL,
        "source_legal": (
            "Decreto Legislativo Presidencial n.º 1/24 de 3 de Janeiro, que aprova a "
            "Pauta Aduaneira dos Direitos de Importacao e Exportacao e as respectivas "
            "Instrucoes Preliminares — art. 2.º (abreviaturas), art. 43.º (beneficios "
            "fiscais aduaneiros et colonnes preferentielles reservees), art. 58.º "
            "(direitos e demais imposicoes devidos na importacao) ; Codigo Aduaneiro "
            "(Decreto-Lei n.º 05/06), art. 117.º n.º 2 et art. 119.º (valor aduaneiro)"
        ),
        "source_quality": "crawled_authentic",
        "source_sha256": hashlib.sha256(chemin.read_bytes()).hexdigest(),
        "extracted_at": date.today().isoformat(),
        "methode": (
            "LECTURE OPTIQUE D'UN SCAN. Le Diario promulgue ne porte AUCUNE couche "
            "texte : 345 pages, zero octet. Le bareme etant un tableau REGLE, ses "
            "traits sont detectes sur l'image, chaque colonne est decoupee en bande, "
            "et chaque bande est lue avec le seul vocabulaire qu'elle peut contenir — "
            "chiffres et points pour les codes, chiffres et « Livre » pour "
            "les taux. Un OCR de pleine page rend « r]ao » pour un "
            "« 30 » et « EE » pour un code : c'est le decoupage "
            "par colonne qui rend la lecture fiable, pas l'OCR seul."
        ),
        "calculation_rules": {
            "order": ["DD", "EGA"],
            "bases": {
                "DD": {"basis": "CIF", "type": "ad_valorem", "source": ACTE_DD},
                "EGA": {"basis": "CIF", "type": "ad_valorem", "source": ACTE_DD},
            },
            "source": (
                "Deux prelevements sur la meme assiette, le valor aduaneiro : le droit "
                "de douane du Regime Geral (colonne 4 du bareme) et les emolumentos "
                "gerais aduaneiros, 2 % poses par l'article 58.º n.º 3 des Instrucoes "
                "Preliminares. L'article 58.º n.º 5 dit que les deux sont ad valorem et "
                "portent sur le valor aduaneiro ; le Codigo Aduaneiro art. 117.º n.º 2 "
                "dit que ce valor aduaneiro comprend le transport, la manutention et "
                "l'assurance jusqu'au port — c'est le CIF. LES COLONNES 5 (SADC) ET 6 "
                "(ZCLCA) SONT PUBLIEES ET VIDES : l'article 43.º n.º 2 les declare "
                "reservees, leurs taux restant « a serem definidas em legislacao "
                "especifica ». Ni l'Imposto Especial de Consumo ni l'Imposto sobre "
                "o Valor Acrescentado ne figurent a ce bareme."
            ),
        },
        "stats": stats,
        "sub_positions": positions,
        "unique_tax_codes": codes,
    }


def main(argv=None) -> int:
    logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(message)s")
    argv = list(argv if argv is not None else sys.argv[1:])
    if len(argv) < 1:
        print("usage: angola_pauta_2024_scraper.py <diario.pdf> [dossier_travail]", file=sys.stderr)
        return 2
    chemin = Path(argv[0])
    if not chemin.exists():
        print(f"Fichier introuvable : {chemin}", file=sys.stderr)
        return 2
    if not subprocess.run(["which", "tesseract"], capture_output=True).stdout.strip():
        print("tesseract est requis : le document est un scan sans couche texte.", file=sys.stderr)
        return 2
    dossier = Path(argv[1]) if len(argv) > 1 else Path("/tmp/ago_ocr")
    donnees = construire(chemin, dossier)
    s = donnees["stats"]
    if s["total_positions"] < 5000:
        print(
            f"Collecte refusee : {s['total_positions']} positions lues, moins de 5 000.",
            file=sys.stderr,
        )
        return 1
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    (DATA_DIR / "AGO_tariffs.json").write_text(
        json.dumps(donnees, ensure_ascii=False, indent=1), encoding="utf-8"
    )
    print(
        f"AGO : {s['total_positions']} positions, {s['chapters_covered']} chapitres, "
        f"codes {','.join(donnees['unique_tax_codes'])}"
    )
    print(
        f"  pages lues {s.get('pages_lues', 0)} | sans grille "
        f"{s.get('pages_sans_grille', 0)} sur {s['pages']}"
    )
    print(
        f"  droit a « Livre » (0 %) {s.get('droit_livre', 0)} | sans droit "
        f"{s.get('sans_droit', 0)} | sans designation {s.get('sans_designation', 0)}"
    )
    print(
        f"  emoluments portes {s.get('emolument', 0)} | valeur inattendue en colonne "
        f"preferentielle {s.get('preference_inattendue', 0)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
