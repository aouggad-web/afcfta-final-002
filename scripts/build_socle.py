#!/usr/bin/env python3
"""
Construction du socle de calcul — chantier L1.

Lit les fichiers produits par le crawler et écrit, par pays, un fichier plat
au schéma unique que le moteur de calcul consomme.

Règles, sans exception :

- **aucune valeur inventée** : un champ absent de la source est absent du socle.
  Un taux manquant vaut ``null``, jamais ``0`` ;
- **aucun taux recalculé** : la passe recopie, elle ne dérive pas ;
- **l'assiette vient de la source** quand la source la porte. Sinon seulement,
  elle vient de ``backend/socle/assiettes_pays.json`` — jamais du code ;
- **la provenance suit la donnée** : chaque droit porte sa source, sa qualité et
  le cas échéant la note de la source (taux non vérifié position par position,
  classification estimée, moyenne WITS).

Les colonnes préférentielles (AfCFTA, SADC, EU/UK, EFTA, MERCOSUR, COMESA) sont
conservées à part : elles décrivent un autre régime et n'entrent jamais dans la
cascade NPF.

Usage :
    python3 scripts/build_socle.py                # tous les pays
    python3 scripts/build_socle.py CIV KEN TUN    # une sélection
"""

from __future__ import annotations

import collections
import csv
import glob
import hashlib
import importlib
import importlib.util
import json
import os
import re
import sys
import tempfile
from datetime import datetime, timezone

SOCLE_VERSION = "1"

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CRAWL_DIR = os.path.join(REPO, "backend", "data", "crawled")
ETL_DIR = os.path.join(REPO, "backend", "data")
SOCLE_DIR = os.path.join(REPO, "backend", "socle")
ASSIETTES_PATH = os.path.join(SOCLE_DIR, "assiettes_pays.json")
LIVRE_TARIFAIRE_ETH = os.path.join(
    REPO, "backend", "data", "legal_refs", "zlecaf_application", "sources", "ETH_livre_tarifaire_2021.droits.csv"
)
ACCISE_ETH = os.path.join(
    REPO,
    "backend",
    "data",
    "legal_refs",
    "zlecaf_application",
    "sources",
    "ETH_accise_annexeI_proc1287-2023.csv",
)
IAT_NGA_2026 = os.path.join(
    REPO, "backend", "data", "legal_refs", "zlecaf_application", "sources", "NGA_SI29_2026_IAT.csv"
)
DROITS_AGO_2026 = os.path.join(
    REPO, "backend", "data", "legal_refs", "zlecaf_application", "sources", "AGO_Lei14-25_anexo_III.csv"
)
# Positions SH 2022 que la liste IAT désigne par un code d'une nomenclature
# antérieure, ou sous un même code à deux taux (groupes électrogènes « basic » /
# « soundproof ») : l'IAT n'y est pas attribuable sans deviner.
IAT_NGA_AMBIGUS = {
    **dict.fromkeys(["3004410000", "3004420000", "3004430000", "3004490000"], "3004.40.00.00 : 20 %"),
    **dict.fromkeys(["6907210000", "6907220000", "6907230000", "6907300000"], "6907.90.00.00 : 15 %"),
    **dict.fromkeys(["8903310000", "8903320000", "8903330000"], "8903.92.00.00 : 50 %"),
    **dict.fromkeys(["8502119000", "8502129000", "8502139000", "8502209000"], "15 % (basic) ou 35 % (soundproof)"),
}

# ── Familles de prélèvements ──────────────────────────────────────────────────
# Les sept familles relevées dans les sources. L'ordre est celui de la
# liquidation douanière : droits, puis prélèvements, redevances, accises, TVA,
# et enfin ce qui s'assied sur la TVA.
FAMILLES = {
    "DD": "droit",
    "RS": "communautaire",
    "PCS": "communautaire",
    "PCC": "communautaire",
    "PC-AES": "communautaire",
    "PCAES": "communautaire",
    "PUA": "communautaire",
    "TCI": "communautaire",
    "CIA": "communautaire",
    "RI": "communautaire",
    "OHADA": "communautaire",
    "TS": "communautaire",
    "CEDEAO": "communautaire",
    "EXIM": "redevance",
    "SIL": "redevance",
    "RPD": "redevance",
    "RTL": "redevance",  # redevance de traitement et de liquidation (GN)
    "CA": "redevance",  # centime additionnel (GN)
    "PNS": "redevance",  # prélèvement national de solidarité (TG)
    "RAU": "redevance",  # redevance d'aménagement urbain (BJ)
    "IDF": "redevance",
    "RDL": "redevance",
    "INFRA": "redevance",
    "CISS": "redevance",
    "PSV": "redevance",
    "DSV": "redevance",
    "TCL": "redevance",
    "EXC": "accise",
    "EXS": "accise",  # accise spécifique, Schedule 1 Part 2A (ZA)
    "EXA": "accise",  # accise ad valorem, Schedule 1 Part 2B (ZA)
    "EVB": "accise",  # prélèvement environnemental, sacs plastiques, Part 3A (ZA)
    "EVL": "accise",  # prélèvement environnemental, lampes à filament, Part 3C (ZA)
    "EVC": "accise",  # prélèvement environnemental, CO2 des véhicules, Part 3D (ZA)
    "EVT": "accise",  # prélèvement environnemental, pneus, Part 3E (ZA)
    "FLV": "accise",  # taxe sur les carburants, Part 5A (ZA)
    "RAF": "accise",  # Road Accident Fund levy, Part 5B (ZA)
    "HPL": "accise",  # Health Promotion Levy, boissons sucrées, Part 7A (ZA)
    "EVN": "accise",  # prélèvement environnemental, Part 3 (NA)
    "ATL": "accise",  # Alcohol and Tobacco Levy (SZ)
    "ALV": "accise",  # prélèvement sur l'alcool importé (BW)
    "TAPL": "accise",  # Tobacco and Alcoholic Products Levy (LS)
    "ISCP": "accise",
    "DA": "accise",
    "TIC": "accise",
    "IAT": "accise",
    "TSP": "accise",
    "TP": "accise",
    "DUS": "accise",
    "TUB": "accise",
    "TUF": "accise",
    "SPEC": "accise",
    "SUR": "accise",
    "SWL": "accise",
    "ICE": "accise",  # imposto sobre consumos especiais (CV, MZ)
    "ICES": "accise",  # ICE spécifique par véhicule (CV)
    "TET": "accise",  # taxe spécifique sur le tabac (CV)
    "TEA": "accise",  # taxe spécifique sur l'alcool (CV)
    "DAPS": "droit",  # droit additionnel provisoire de sauvegarde (DZ)
    "TPI": "redevance",  # taxe parafiscale à l'importation (MA)
    "TCS": "accise",  # taxe de consommation spécifique (DZ)
    "MID": "accise",  # MID levy, Excise Act s.3A (MU)
    "TVA": "tva",
    "PRCT": "post_tva",
    "WHR": "post_tva",
    "NHIL": "fonds",
    "GETFUND": "fonds",
}
#: Ordre de liquidation. « autre » précède la TVA à dessein : un prélèvement
#: que le socle ne sait pas classer reste un prélèvement d'entrée, et doit
#: entrer dans une assiette « CIF + tous les droits sauf la TVA ». Le placer en
#: fin de liste l'en aurait exclu — une omission silencieuse, donc un montant
#: faux qui a l'air juste.
ORDRE_FAMILLES = [
    "droit",
    "communautaire",
    "redevance",
    "accise",
    "fonds",
    "autre",
    "tva",
    "post_tva",
]

#: Colonnes qui décrivent un régime préférentiel, jamais un prélèvement dû.
#: ``GENERAL`` en est absent : dans les fichiers SACU c'est le droit NPF.
PREFERENTIELS = {
    "AFCFTA": "AFCFTA",
    "ZLECAF": "AFCFTA",
    "SADC": "SADC",
    "COMESA": "COMESA",
    "D2R": "COMESA",
    "EU_UK": "EU_UK",
    "EUUK": "EU_UK",
    "EFTA": "EFTA",
    "MERCOSUR": "MERCOSUR",
    # Colonne du tarif libyen : « التعريفة التفضيلية لدول جامعة الدول العربية »,
    # tarif préférentiel pour les États de la Ligue des États arabes. Le nom du
    # régime reprend l'en-tête et rien de plus : ni le tarif ni la loi libyenne
    # n'invoquent la GZALE/GAFTA, et la composition retenue par la douane
    # libyenne n'est établie par aucune source consultée.
    # La table est interrogée sur le code NORMALISÉ (`_norm` retire tirets,
    # points, espaces et soulignés) : la clé s'écrit donc sans souligné, comme
    # « EUUK » à côté de « EU_UK ». Écrite « LIGUE_ARABE », l'entrée serait
    # morte et la colonne tomberait dans la cascade NPF comme un droit dû.
    "LIGUEARABE": "LIGUE_ARABE",
    # Le tarif malawien publie DEUX colonnes SADC, et sa propre loi les
    # distingue : « for imports from other Member States other than South
    # Africa » (col. 8) et « for imports from South Africa only » (col. 9).
    # Sans une clé propre à la seconde, les deux se rangeraient sous « SADC » et
    # le garde de collision retirerait la préférence des deux — ce qui serait
    # honnête mais perdrait une donnée que la source publie clairement.
    "SADCZAF": "SADC_ZAF",
    # Le tarif seychellois ne publie pas UN taux préférentiel par régime mais un
    # CALENDRIER : cinq taux SADC et cinq taux ZLECAf, un par année civile de 2022
    # à 2026 (S.I. 113 of 2022, en-tête du barème). Les ranger tous sous « SADC » et
    # « AFCFTA » ferait jouer le garde de collision et retirerait la préférence de
    # toutes ces lignes ; les laisser hors de cette table serait bien pire — chaque
    # millésime tomberait dans la cascade NPF comme un droit DÛ, et une position à
    # 25 % de droit se verrait réclamer treize fois. Chaque millésime est donc un
    # régime nommé, et le collecteur sert EN PLUS, sous le nom sans millésime, celui
    # de l'année en vigueur.
    **{f"SADC{annee}": f"SADC_{annee}" for annee in range(2022, 2027)},
    **{f"AFCFTA{annee}": f"AFCFTA_{annee}" for annee in range(2022, 2027)},
    # Commission de l'océan Indien : la Schedule II du même instrument accorde
    # « a rate of duty of 5% lower than the rate of duty prescribed in sub column 5 ».
    # C'est une préférence par origine, pas un prélèvement.
    "COI": "COI",
    # Malawi, colonne 5 : le PLEIN DROIT, dont les colonnes 6 à 9 sont des
    # remises par origine (Order 2022, par. 5). C'est un taux ALTERNATIF au
    # droit NPF (col. 6), pas un second droit : rangé parmi les droits, il
    # s'additionnait au NPF sur 7 119 positions (25 % + 30 % sur les
    # cigarettes 2402.20).
    "DDPLEIN": "PLEIN_DROIT",
}

#: PAYS DONT LE CODE PUBLIÉ PORTE UNE CLÉ DE CONTRÔLE, et la longueur de la
#: POSITION TARIFAIRE sans elle. Déclaré pays par pays, jamais déduit d'une
#: longueur : une nomenclature peut légitimement compter onze chiffres.
#:
#: La Tunisie publie `01012100015`. Ce n'est pas une position à onze chiffres :
#: c'est la sous-position `0101210001` suivie de la clé `5`, que le déclarant
#: saisit avec le code sur la déclaration en douane. La preuve est dans la
#: donnée — tronquer les 17 541 codes au dixième caractère donne 17 541
#: préfixes DISTINCTS, zéro collision. Si le onzième chiffre était un niveau de
#: subdivision, plusieurs codes partageraient leur parent ; aucun ne le fait,
#: il est donc fonctionnellement déterminé par les dix premiers. Et il est
#: uniformément réparti de 0 à 9, ce qu'un niveau tarifaire n'est jamais.
#:
#: CE QUE COÛTAIT L'ABSENCE DE CETTE TABLE. Le socle s'indexait sur le code
#: PLUS sa clé, si bien que le code qu'un déclarant tape — dix chiffres — se
#: voyait répondre « Position nationale introuvable ». Et le sélecteur
#: affichait « HS11 digits » : le produit affirmait une nomenclature tunisienne
#: à onze chiffres, qui n'existe pas.
#:
#: NE PAS Y VERSER L'ÉTHIOPIE sur la foi de la même longueur. Ses 6 296 codes
#: font aussi onze caractères, mais le onzième est TOUJOURS « 0 » : c'est un
#: remplissage, pas une clé. Même symptôme, cause différente, à examiner pour
#: elle-même.
CLE_DE_CONTROLE_SUFFIXE = {
    # Tunisie — douane.gov.tn/tarifwebnew : position à 10 chiffres + 1 de clé.
    "TUN": 10,
}


#: Les régimes que la collecte range dans `preferential_rates` plutôt que dans
#: `taxes`, PAYS PAR PAYS.
#:
#: POURQUOI UNE SECONDE TABLE, ET POURQUOI PAR PAYS. `PREFERENTIELS` est
#: interrogée avec le code d'une colonne de taxe ; ici la source nomme le régime
#: elle-même, dans un champ à part. Verser ces noms dans `PREFERENTIELS`
#: changerait le sort des colonnes homonymes de TOUS les autres pays — « UE »,
#: « INDE », « UK » sont des mots trop courants pour qu'on les rende
#: préférentiels partout sur la foi d'un seul tarif. Chaque pays déclare donc
#: les siens, et un régime absent de sa table n'est PAS servi : il est compté
#: et écarté, jamais rabattu sur la cascade NPF où il deviendrait un droit dû.
REGIMES_PAR_PAYS = {
    # Maurice — mra.mu, Customs Tariff Schedules (HS 2022). Douze colonnes
    # préférentielles, que le tarif nomme en toutes lettres.
    "MUS": {
        "ZLECAF": "AFCFTA",
        "SADC": "SADC",
        # DEUX COLONNES COMESA, ET ELLES DIVERGENT. Le tarif publie « COMESA
        # Group I » et « COMESA Group II » ; leurs taux diffèrent sur 504
        # positions. Les ranger tous deux sous « COMESA » ferait jouer le garde
        # de collision et retirerait la préférence de ces 504 lignes. Chacune
        # garde donc son nom, comme les deux colonnes SADC du Malawi.
        "COMESA_I": "COMESA_I",
        "COMESA_II": "COMESA_II",
        # « Indian Ocean Commission » : la Commission de l'océan Indien, que le
        # tarif seychellois sert déjà sous « COI ». Même organisation, même nom.
        "IOC": "COI",
        # L'Union européenne et le Royaume-Uni ont ICI DEUX COLONNES DISTINCTES
        # — « European Community » et « United Kingdom ». Leurs taux coïncident
        # aujourd'hui sur les 6 932 positions comparables, mais les fondre sous
        # « EU_UK » serait une interprétation : le tarif les sépare, on les sert
        # séparés.
        "UE": "UE",
        "UK": "UK",
        "INDE": "INDE",
        "PAKISTAN": "PAKISTAN",
        "CHINE": "CHINE",
        "TURKIYE": "TURKIYE",
        "EAU": "EAU",
    },
    # Tunisie — douane.gov.tn/tarifwebnew (Tarif Web 2026). Le tarif publie une
    # colonne par PARTENAIRE, nommee en toutes lettres avec son code pays, et
    # non par bloc. UNE SEULE est servie : l'Algerie.
    #
    # POURQUOI UNE SEULE. La colonne ZLECAf du meme tarif n'est PAS SERVIE, et
    # ce refus est le coeur de cette entree. Elle ne prend que quatre valeurs
    # sur 84 712 entrees — 0, 40, 80 et 87,5 — et 58 939 d'entre elles, soit
    # 69,6 %, DEPASSENT le droit NPF de leur propre position. Deux captures du
    # portail le montrent sur la meme valeur : sur les bananes fraiches
    # (08039010002) le droit est de 50 % et la colonne affiche 40 % ; sur une
    # huile moteur (27101981100) le droit est de 0 % et la colonne affiche
    # encore 40 %. Un TAUX suit le droit de sa position ; un COEFFICIENT de
    # demantelement ne le suit pas. La source intitule pourtant la colonne
    # « Taux Preferentiel ». Tant que la douane tunisienne n'aura pas tranche,
    # la servir ferait payer 40 % de la valeur CIF sur 20 149 lignes que le
    # tarif laisse en FRANCHISE. Elle est donc ecartee, et comptee.
    #
    # L'ALGERIE, ELLE, EST SANS AMBIGUITE : 13 362 entrees, TOUTES a 0 %,
    # aucune au-dessus du droit NPF. La source lui attribue deux fondements a
    # la fois — « ZALE (GAFTA) » et « accord bilateral TUN-DZA » — et le
    # regime est nomme par le PARTENAIRE, non par l'un de ces deux titres,
    # parce que la source ne dit pas lequel emporte l'autre.
    "TUN": {"ALGERIE": "DZA"},
    # Madagascar — tarif des douanes 2026 (douanes.gov.mg). Le tarif publie une
    # colonne « DD APEi » : le droit de douane préférentiel de l'Accord de
    # partenariat économique intérimaire (APEi, Union européenne). Elle est
    # servie sous « UE », régime que la table PREFERENTIELS connaît déjà — la
    # laisser hors de cette table la ferait tomber dans la cascade NPF comme un
    # droit dû.
    "MDG": {"APEI": "UE"},
}


def _est_une_interdiction(restriction) -> bool:
    """Vrai si la restriction interdit l'importation, pas seulement l'encadre.

    Le champ `restrictions` des sources mêle deux natures : une INTERDICTION
    (le tarif libyen, « ممنوع استيراده » — la marchandise ne peut pas entrer)
    et une MENTION RÉGLEMENTAIRE (la source égyptienne, autorisations et
    normes — la marchandise entre, sous condition). Les confondre ferait
    passer 26 502 positions égyptiennes pour prohibées.
    """
    return isinstance(restriction, dict) and restriction.get("type") == "IMPORTATION_INTERDITE"


def _norm(code: str) -> str:
    return re.sub(r"[.\s/_-]", "", str(code or "")).upper()


def code_canonique(code: str, libelle: str = "") -> str:
    """Ramener un code source au vocabulaire du socle, sans perdre l'original.

    Le texte testé garde le code **non normalisé** : plusieurs sources — le
    Maroc, l'EAC, le Ghana — emploient le libellé complet comme clé de taxe
    (« Droit d'Importation (DI) »), que la normalisation rendrait illisible.
    """
    t = f"{code} {_norm(code)} {libelle or ''}".lower()
    # Sources qui emploient le libellé complet comme clé : le sigle officiel est
    # entre parenthèses en fin de libellé (« … (TPI) », « … (IDF) »).
    sigle = re.search(r"\(([A-Za-z][A-Za-z0-9./ -]{1,12})\)\s*$", str(code or "").strip())
    n = _norm(sigle.group(1)) if sigle else _norm(code)

    if n in {"DD", "DI", "ID", "DROIT", "GENERAL", "CET", "DR"}:
        return "DD"
    # Droit de douane SECTORIEL. Le tarif tunisien décline son droit par produit
    # — « DD/VEH.AU » (véhicules, 667 positions), « DD/AUT.CA » (autres
    # carburants, 57), « DD/FUEL » (34), « DD/MAZOUT » (20), « DD/PET.BR »
    # (pétrole brut, 8) — avec des taux bien réels : 0 %, 15 %, 30 %.
    # Faute d'être reconnus, ces 786 droits étaient rangés en famille « autre ».
    # Leurs MONTANTS étaient justes, ils étaient liquidés ; c'est leur nature
    # qui était perdue, et avec elle la possibilité de dire que la position
    # porte un droit de douane. Aucune de ces positions ne porte par ailleurs un
    # DD générique : le rattachement ne peut donc pas écraser un autre droit.
    if re.match(r"^DD\s*[/-]", str(code or "").strip(), re.I):
        return "DD"
    if n in {"TVA", "TVAI", "TVAAP", "TVAAPTAXE", "VAT", "IVA"}:
        return "TVA"
    if "value added" in t or "valeur ajout" in t or "valor acrescentado" in t:
        return "TVA"
    if "import duty" in t or "customs duty" in t or "droit de douane" in t:
        return "DD"
    if "droit d'importation" in t or "importation (d" in t:
        return "DD"
    if n in {"IDF", "IMPORTDEC", "IMPORTDECL"} or "import declaration" in t:
        return "IDF"
    if n in {"RDL", "RAILWAYDE"} or "railway development" in t:
        return "RDL"
    if "infrastructure levy" in t:
        return "INFRA"
    if n in {"GETFL", "GETFUND"} or "education trust" in t:
        return "GETFUND"
    if n == "NHIL" or "health insurance" in t:
        return "NHIL"
    if "excise" in t or n in {"EXC", "EXCISE"}:
        return "EXC"
    if n.startswith("RPD"):
        return "RPD"
    if n in {"DSV", "DROITSANITVETERINA"} or "sanit" in t:
        return "DSV"
    if n in {"WHR"} or "withhold" in t:
        return "WHR"
    if n in {"SR", "SUR"} or "surtax" in t:
        return "SUR"
    if n in {"PCAES"}:
        return "PC-AES"
    return n


def famille(code_canon: str) -> str:
    # Tunisie : TVA/AUTO, TVA/PP, TVA/MTK… sont des TVA (« TVA VOIT.AUTOS »).
    # Gardées sous leur code — cinq positions 87.01 en portent deux —, mais
    # rangées dans la famille tva, que l'assiette « TOUS_SAUF_TVA » exclut.
    if code_canon.startswith("TVA"):
        return "tva"
    return FAMILLES.get(code_canon, "autre")


# ── Assiettes ─────────────────────────────────────────────────────────────────
#: Expressions d'assiette relevées dans les sources → grammaire du socle.
#: Toute expression non listée est rendue indisponible et signalée : il vaut
#: mieux un socle qui dit « je ne sais pas » qu'un socle qui suppose « CIF ».
ASSIETTES_SOURCE = {
    "CIF": ("CIF", None),
    "CIF + DD": ("CIF+DD", None),
    "CIF+DD": ("CIF+DD", None),
    "CIF + DD + RS + PCS": ("CIF+DD+RS+PCS", None),
    "CIF + DD + TCI": ("CIF+DD+TCI", None),
    # Maurice — VAT Act 1998, s.13 : valeur en douane + droit de douane
    # ET ACCISE. Le profil générique posait « CIF+DD », qui omet l'accise
    # et sous-facturait la TVA sur les positions qui en portent une.
    "CIF+DD+EXC": ("CIF+DD+EXC", None),
    # Mozambique — Lei n.º 11/2016, art. 15 : l'ICE s'assoit sur le valor
    # aduaneiro augmenté des droits (§6), et l'IVA sur le valor aduaneiro
    # augmenté des droits, de l'ICE et de la sobretaxa (§7).
    "CIF+DD+ICE+SOBRETX": ("CIF+DD+ICE+SOBRETX", None),
    # Cap-Vert — Código do ICE, art. 13 : l'ICE s'assoit sur la valeur en
    # douane et tous les droits et taxes, lui-même exclu (DI, taxa comunitária,
    # taxes spécifiques du tabac et de l'alcool) ;
    # Regulamento do IVA, art. 16 : valeur en douane + tous droits sauf l'IVA.
    "CIF+DD+PCC": ("CIF+DD+PCC", None),
    "CIF+DD+PCC+TET": ("CIF+DD+PCC+TET", None),  # cigarettes : taxe de 180$00 par paquet
    "CIF+DD+PCC+TEA": ("CIF+DD+PCC+TEA", None),  # boissons alcooliques : taxe par litre
    "CIF+TOUS_SAUF_TVA": ("CIF+TOUS_SAUF_TVA", None),
    "CIF + DD + EXC": ("CIF+DD+EXC", None),
    "CIF+DUTY": ("CIF+DD", None),
    "CIF+DUTY+FEES": ("CIF+TOUS_SAUF_TVA", None),
    "CIF+DUTY+LEVIES": ("CIF+TOUS_SAUF_TVA", None),
    "CIF (PLAFOND 15 000 XAF)": ("CIF", {"montant": 15000.0, "devise": "XAF"}),
    # Tunisie — libellés du tarif intégré (SINDA)
    "VALEUR DOUANE DINARS": ("CIF", None),
    "VALEUR DOUANE": ("CIF", None),
    "QCS": ("xQTE", None),
    "PN (KG)": ("xQTE", None),  # poids net : droit liquidé à la quantité
    "VAL DOUANE+ SOMME DT": ("CIF+TOUS_SAUF_SOI", None),
}

#: Assiettes que la source exprime mais que le socle ne traduit **pas**, avec
#: le motif. Les nommer vaut mieux que les ramener de force à « CIF » : une
#: assiette approchée produit un montant faux qui a l'air juste.
ASSIETTES_NON_TRADUITES = {
    "PN(KG)/100 EXCES": "droit au poids avec seuil d'excédent — la règle de seuil n'est pas publiée avec la ligne",
    "VARIABLE": "la source déclare l'assiette variable",
    # Tunisie : la « quantité complémentaire d'importation » n'a pas d'unité
    # publiée — le champ QCI est vide sur les 17 542 positions du Tarif Web.
    # Liquider à la quantité saisie servait 990 droits dans une unité devinée.
    "QCI": "quantité complémentaire d'importation : unité non publiée par la source (QCI vide)",
}


def assiette_depuis_source(brut):
    """Traduire l'assiette portée par la source.

    Retourne ``(assiette, plafond, motif_non_traduite)``. Une assiette illisible
    ou volontairement non traduite reste ``None`` et porte son motif : le socle
    dit alors qu'il ne sait pas, au lieu de supposer « CIF ».
    """
    if not brut:
        return None, None, None
    texte = " ".join(str(brut).split()).upper()
    if texte in ASSIETTES_NON_TRADUITES:
        return None, None, ASSIETTES_NON_TRADUITES[texte]
    if texte in ASSIETTES_SOURCE:
        a, plafond = ASSIETTES_SOURCE[texte]
        return a, plafond, None
    # Tunisie : « VAL.DOU(D)+R(DT) GR.x » = valeur en douane augmentée des droits
    # et taxes — Code de la TVA art. 6 § II-1 : « tous droits et taxes inclus à
    # l'exclusion de la taxe sur la valeur ajoutée » (fiche TUN_assiette_TVA).
    if texte.startswith("VAL.DOU") and "R(DT)" in texte:
        return "CIF+TOUS_SAUF_TVA", None, None
    # Tunisie : « SOMME D.T (G=...) » = somme des droits et taxes, hors valeur
    if texte.startswith("SOMME D.T"):
        return "SOMME(TOUS_SAUF_SOI)", None, None
    return None, None, f"expression non reconnue : {texte[:60]}"


def charger_assiettes_pays():
    """La table d'assiettes versionnée ; absente ou illisible, la construction s'arrête."""
    try:
        return _lire_assiettes_pays()
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        raise SystemExit(
            f"[build_socle] {os.path.relpath(ASSIETTES_PATH, REPO)} absent ou illisible : {exc}"
        ) from exc


def _lire_assiettes_pays():
    with open(ASSIETTES_PATH, encoding="utf-8") as f:
        charge = json.load(f)
    pays = charge.get("pays") if isinstance(charge, dict) else None
    if not isinstance(pays, dict):
        raise ValueError("table d'assiettes non conforme")
    return pays


def _entree_exploitable(entree):
    """Une entrée de manifeste que les totaux savent lire.

    Il ne s'agit pas de valider le manifeste, mais de ne pas se faire
    interrompre par une entrée tronquée : `etat` et `compteurs.positions` /
    `compteurs.droits` sont lus sans garde plus bas.
    """
    if not isinstance(entree, dict) or not entree.get("etat"):
        return False
    compteurs = entree.get("compteurs")
    return isinstance(compteurs, dict) and all(
        isinstance(compteurs.get(cle), int) for cle in ("positions", "droits")
    )


def _ecrire_json_atomique(chemin, contenu, **kwargs):
    os.makedirs(os.path.dirname(chemin), exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(
        dir=os.path.dirname(chemin), prefix=f"{os.path.basename(chemin)}.", suffix=".tmp", text=True
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(contenu, f, **kwargs)
        os.replace(tmp_path, chemin)
    except Exception:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


def assiettes_du_fichier(donnees):
    """Assiettes déclarées à la racine du fichier source, par code de taxe.

    Dix-sept fichiers portent une règle de calcul globale (``calculation_rules``
    ou ``calculation_method``). Quand elle nomme l'assiette d'une taxe, elle est
    de la donnée : elle prime donc sur la table codée, et ne cède qu'à une
    assiette portée par la ligne elle-même.
    """
    regles = donnees.get("calculation_rules") or {}
    bases = regles.get("bases") if isinstance(regles, dict) else None
    out = {}
    for code, spec in (bases or {}).items():
        if not isinstance(spec, dict):
            continue
        assiette, plafond, _ = assiette_depuis_source(spec.get("basis"))
        if assiette:
            out[code_canonique(code)] = (assiette, plafond)
    return out


def methode_verbatim(donnees):
    """Conserver la méthode publiée par la source, sans l'interpréter."""
    for cle in ("calculation_method", "calculation_rules"):
        valeur = donnees.get(cle)
        if isinstance(valeur, dict) and valeur:
            return {"champ": cle, "contenu": valeur}
    return None


# ── Lecture des taux ──────────────────────────────────────────────────────────
_MOTS_ZERO = {"free", "exempt", "exonere", "exonéré", "nil", "gratuit"}


def lire_taux(valeur):
    """Lire un taux sans jamais fabriquer de valeur. ``None`` si illisible."""
    if isinstance(valeur, bool):
        return None
    if isinstance(valeur, (int, float)):
        # Un taux n'est jamais négatif : « -1 » est le marqueur « taux
        # variable » des crawls CEMAC (droit d'accise DA, 292 positions dans
        # six pays). Lu tel quel, il liquidait une accise NÉGATIVE dans un
        # total COMPLET.
        return float(valeur) if valeur >= 0 else None
    if isinstance(valeur, str):
        v = valeur.strip().lower()
        if v in _MOTS_ZERO:
            return 0.0
        m = re.search(r"-?\d+(?:[.,]\d+)?", v)
        if m:
            taux = float(m.group(0).replace(",", "."))
            return taux if taux >= 0 else None
    return None


_TAUX_PUR = re.compile(r"^\s*-?\d+(?:[.,]\d+)?\s*%?\s*$")


def _est_un_taux(brut) -> bool:
    """Vrai si le verbatim est un taux et rien d'autre."""
    if isinstance(brut, (int, float)) and not isinstance(brut, bool):
        return True
    texte = str(brut or "").strip()
    return texte.lower() in _MOTS_ZERO or bool(_TAUX_PUR.match(texte))


#: Sous-unités monétaires rencontrées dans les tarifs. Un droit publié en
#: centimes vaut un centième de l'unité : lire « 8c/kg » comme « 8 par kg »
#: surestime le droit d'un facteur cent.
SOUS_UNITES = {"c": 100, "cent": 100, "cents": 100, "ct": 100}

_SPECIFIQUE = re.compile(
    # La devise peut précéder le montant : le tarif seychellois écrit
    # « SCR5.13/kg » (253 droits), illisibles tant que seul « 8c/kg » l'était.
    r"^\s*(?P<prefixe>[A-Z]{3}(?=\d))?(?P<montant>-?\d+(?:[.,]\d+)?)\s*(?P<monnaie>[A-Za-zÀ-ÿ]*)\s*(?:/\s*(?P<quantite>[A-Za-zÀ-ÿ0-9]+))?",
)


def lire_specifique(expression):
    """Décomposer « 8c/kg », « 0.8 dinars », « 136c/li » en montant et unités.

    Retourne ``None`` si l'expression n'est pas lisible : un droit spécifique
    qu'on ne sait pas lire reste indisponible, il n'est jamais approché.
    """
    if not expression:
        return None
    m = _SPECIFIQUE.match(str(expression))
    if not m:
        return None
    if m.group("prefixe") and m.group("monnaie"):
        # « SCR5perpackof20 » : l'unité de quantité n'est pas lisible.
        return None
    montant = float(m.group("montant").replace(",", "."))
    monnaie = (m.group("prefixe") or m.group("monnaie") or "").lower()
    diviseur = SOUS_UNITES.get(monnaie)
    return {
        "montant": montant / diviseur if diviseur else montant,
        "unite_monetaire": "unite_principale" if diviseur else (monnaie or None),
        "sous_unite_source": monnaie if diviseur else None,
        "unite_quantite": (m.group("quantite") or "").lower() or None,
        "brut": str(expression),
    }


def nettoyer_code(*candidats) -> str:
    for c in candidats:
        if c is None:
            continue
        chiffres = re.sub(r"\D", "", str(c))
        if len(chiffres) >= 6:
            return chiffres
    return ""


# Un droit servi depuis WITS/UNCTAD-TRAINS n'est pas une position nationale : la
# Banque mondiale agrège les lignes du tarif national au niveau SH6. La
# sous-position réelle peut donc porter un autre taux. La TVA de ces mêmes pays
# porte déjà sa réserve ; le droit de douane ne la portait pas, alors que c'est lui
# qui vient de l'agrégat. Il la porte désormais aussi : l'opérateur lit la même
# mise en garde sur les deux lignes d'une même position.
RESERVE_WITS = (
    "Taux MFN appliqué agrégé au niveau SH6 par WITS/UNCTAD-TRAINS (Banque "
    "mondiale), non vérifié position par position : la nomenclature nationale "
    "peut porter un taux différent au niveau de la sous-position."
)


def _vient_de_wits(source) -> bool:
    texte = str(source or "").upper()
    return "WITS" in texte or "UNCTAD-TRAINS" in texte or "TRAINS" in texte


#: Droit composé dont la DÉSIGNATION porte le taux, et dont la règle de
#: liquidation est ÉNONCÉE. Le tarif extérieur commun de l'EAC procède ainsi
#: pour ses produits sensibles : la colonne de taux est vide — la source note
#: « Rate determined by national schedule » — et le barème est écrit dans le
#: libellé, « 75% or $345/MT whichever is higher ».
#:
#: Sans cette lecture, ces positions n'ont AUCUN droit et se servent comme si
#: rien n'était dû : 273 positions sur les sept pays de l'EAC, dont tout le riz
#: et tout le sucre. Relevé le 2026-09-18, en quatre barèmes seulement —
#: 25 %/200 $ la tonne (154), 100 %/460 $ (63), 75 %/345 $ (35) et
#: 35 %/0,40 $ le kilo (21) — sans une seule forme non reconnue.
#:
#: Ici la règle est dans l'expression — « whichever is higher ». Pour le
#: « 40% or 240c/kg » sud-africain, elle est dans les General Notes SARS (B.3) :
#: voir MOTIF_COMPOSE_SARS.
MOTIF_COMPOSE_DESIGNATION = re.compile(
    r"([\d]+(?:[.,][\d]+)?)\s*%\s*or\s*(?:\$|USD|US\$)\s*([\d]+(?:[.,][\d]+)?)\s*/\s*"
    r"(MT|kg|t|L)\b\s*whichever\s+is\s+(higher|lower)",
    re.I,
)

REGLES_COMPOSEES = {"higher": "LE_PLUS_ELEVE", "lower": "LE_MOINS_ELEVE"}

#: Tarif SARS (SACU) : « 40% or 240c/kg ». La règle n'est pas dans la colonne mais
#: dans les General Notes du Schedule No. 1, partie B, note 3 : chaque partie
#: séparée par « or » est un taux complet, et s'applique « such rate of duty
#: yielding the higher or highest amount of duty ». Seule la forme au kilo est
#: retenue : « 500c/2u » (la paire) reste non tranché. « 55c/kg less 90% » est un
#: taux complet lui aussi — voir MOTIF_DEDUCTION_SARS.
MOTIF_COMPOSE_SARS = re.compile(
    r"^\s*\d+(?:[.,]\d+)?\s*%\s*or\s*(\d{1,3}(?: \d{3})+|\d+(?:,\d+)?)c/kg"
    r"(?:\s+less\s+\d+(?:,\d+)?%)?\s*$"
)

#: « 110c/kg less 80% with a maximum of 37% », « 10% or 55c/kg less 90% » : dans
#: la colonne des taux, « % » signifie « per cent AD VALOREM » (General Notes,
#: G.53), sur la « value for duty purposes » (C.). La part spécifique est donc
#: diminuée de 80 % de la valeur en douane — et non de 80 % d'elle-même. La
#: colonne AfCFTA le confirme : « 344c/kg less 34% with a maximum of 17,6% » est
#: le NPF « 860c/kg less 85% with a maximum of 44% » multiplié par 0,4, terme à
#: terme, ce qui n'est vrai que de cette lecture. Fiche
#: SACU_formule_less_2026-10-25.json.
MOTIF_DEDUCTION_SARS = re.compile(r"c/kg\s+less\s+(\d+(?:,\d+)?)%", re.I)


def droit_compose_depuis_designation(designation, source):
    """Rendre le droit composé écrit dans une désignation, ou ``None``.

    Ne rend un droit que si les DEUX composantes et la RÈGLE sont lues. Une
    désignation qui ne porte pas la formule complète ne produit rien — elle
    tombe alors sur la ligne sans taux, qui dit l'indisponibilité.
    """
    texte = designation
    if isinstance(texte, dict):
        texte = texte.get("en") or texte.get("fr") or texte.get("ar") or ""
    m = MOTIF_COMPOSE_DESIGNATION.search(str(texte or ""))
    if not m:
        return None
    ad_valorem = float(m.group(1).replace(",", "."))
    montant = float(m.group(2).replace(",", "."))
    return {
        "code": "DD",
        "code_source": "DD",
        "libelle": "Droit de douane (produit sensible, barème national)",
        "famille": "droit",
        "taux": ad_valorem,
        "assiette": "CIF",
        "assiette_origine": "designation",
        "specifique": {
            "montant": montant,
            "unite_monetaire": "USD",
            "unite_quantite": m.group(3).lower(),
            "brut": m.group(0),
        },
        "compose": True,
        "regle_composee": REGLES_COMPOSEES[m.group(4).lower()],
        "expression_brute": m.group(0),
        "source": source,
        "note": (
            "Taux absent de la colonne du tarif — la source note « Rate determined "
            "by national schedule » — et porté par la désignation de la position. "
            "Les deux composantes et la règle de liquidation sont citées telles "
            "qu'écrites."
        ),
    }


# ── Adaptateurs : une fonction par forme de ligne fiscale ─────────────────────
def _droit(
    code_src,
    libelle,
    taux,
    assiette_brute,
    source,
    note=None,
    specifique=None,
    qualite=None,
    classification=None,
    regle_composee=None,
):
    canon = code_canonique(code_src, libelle)
    prefer = PREFERENTIELS.get(_norm(code_src))
    assiette, plafond, motif = assiette_depuis_source(assiette_brute)
    return {
        "code": canon,
        "code_source": str(code_src),
        "libelle": libelle or canon,
        "famille": famille(canon),
        "taux": taux,
        "specifique": specifique,
        "assiette": assiette,
        "assiette_origine": "source" if assiette else None,
        "assiette_non_traduite": motif if assiette_brute and not assiette else None,
        "plafond": plafond,
        "source": source,
        "qualite": qualite,
        "note": note if note else (RESERVE_WITS if _vient_de_wits(source) else None),
        "classification_source": classification,
        # La règle qui départage un droit composé ne se devine pas : elle vient
        # de la source, quand la source l'énonce. Le tarif zimbabwéen le fait
        # (« the rate of duty yielding the higher amount of duty shall be
        # applicable ») ; le tarif sud-africain ne le fait pas, et son droit
        # composé reste donc non liquidable.
        "regle_composee": regle_composee,
        "_preferentiel": prefer,
    }


def droits_depuis_dict(taxes, source_defaut):
    """Schéma ``taxes: {CODE: taux}`` ou ``{CODE: {name, rate, ...}}``."""
    out = []
    for code, valeur in (taxes or {}).items():
        info = valeur if isinstance(valeur, dict) else {}
        taux = lire_taux(info.get("rate", info.get("rate_pct")) if info else valeur)
        out.append(
            _droit(
                code,
                info.get("name") or info.get("label") or "",
                taux,
                info.get("base") or info.get("assiette"),
                info.get("source") or source_defaut,
                note=info.get("note"),
                qualite=info.get("source_quality"),
                classification=info.get("classification_source"),
            )
        )
    return out


def droits_depuis_liste(taxes, source_defaut):
    """Schémas ``taxes_detail: [...]``, ``taxes: [...]``, ``taxes_import: [...]``."""
    out = []
    for row in taxes or []:
        if not isinstance(row, dict):
            continue
        code = row.get("tax_code") or row.get("code") or row.get("tax") or row.get("tax_name")
        libelle = row.get("tax_name") or row.get("name") or row.get("observation") or ""
        taux = lire_taux(row.get("rate") if row.get("rate") is not None else row.get("rate_pct"))
        if str(row.get("rate_type") or "").lower() == "specific":
            # « rate_type: specific » (Côte d'Ivoire, PSV et SPEC, 60 droits) :
            # « 1000 » est un montant par unité, d'unité non publiée — pas
            # 1 000 %. Rien n'est liquidable, rien n'est affiché comme taux.
            taux = None
        if taux is None and _est_un_taux(row.get("raw_value")):
            # Le verbatim ne sert de taux que s'il EST un taux (« 20 », « 5 % »,
            # « Free »). « Rs 1,692.50/L Ab alco* » (accise mauricienne, 189
            # droits) devenait 1,692 % ; « 0.0099 MZN Per 1 KG » (plancher ICE
            # mozambicain, 80) devenait 0,0099 % — affichés comme des taux.
            taux = lire_taux(row.get("raw_value"))
        # Un droit peut porter DEUX composantes. Le tarif SARS publie
        # « 40% or 240c/kg » sur 140 positions : `rate_pct` 40,0 ET
        # `specific_component` « 240c/kg », avec `compound: true`.
        #
        # La première version ne lisait que `specific_value`, et seulement en
        # l'absence de taux ad valorem. Un droit composé perdait donc
        # silencieusement sa part spécifique ET son verbatim : le moteur
        # servait 40 % comme s'il était le droit entier. Sur la position
        # 020110, la part spécifique l'emporte en dessous de 6,00 ZAR/kg de
        # valeur unitaire — l'écart n'est pas théorique.
        #
        # Les deux composantes sont désormais conservées, avec l'expression
        # brute. Laquelle s'applique n'est PAS tranchée ici : le crawl a
        # délibérément gardé `raw_value verbatim` sans décider, et le moteur
        # ne doit pas décider à sa place.
        specifique = row.get("specific_value") or row.get("specific_component")
        compose = bool(row.get("compound")) and taux is not None and specifique

        # Deux formes composées coexistent dans le tarif SARS, et elles n'ont
        # PAS le même statut.
        #
        # « 450c/kg with a maximum of 96% » (46 positions) énonce sa propre
        # règle : le droit est le spécifique, borné à un pourcentage de la
        # valeur. Rien n'est laissé à deviner. Le crawl, lui, a rangé 96,0 dans
        # `rate_pct` — c'est-à-dire le PLAFOND pris pour le TAUX. Le moteur
        # liquidait donc 96 % ad valorem là où le droit dû est 450c/kg, soit
        # environ 9 % pour du lait en poudre à 50 ZAR/kg : un facteur dix.
        #
        # « 40% or 240c/kg » (94 positions) est l'autre forme : la colonne ne dit
        # pas laquelle des deux composantes s'applique, les General Notes SARS
        # (B.3) le disent ; voir `compose` et MOTIF_COMPOSE_SARS.
        plafond_ad_valorem = None
        brut = str(row.get("raw_value") or "")
        borne = re.search(r"maximum of\s+([\d]+(?:[.,][\d]+)?)\s*%", brut, re.I)
        if borne and specifique:
            plafond_ad_valorem = float(borne.group(1).replace(",", "."))
            taux = None  # 96 % est la BORNE, pas le taux : ne pas le liquider
            compose = False
        if specifique and row.get("rate_pct") is None:
            taux = None
        source_ligne = row.get("source") or source_defaut
        # « 110c/kg less 80% » : sans sa déduction, la part spécifique surestime
        # le droit de 80 % de la valeur. La déduction se conserve. Toute autre
        # expression en « less » — hors tarif SARS, autre unité, autre écriture
        # du pourcentage, part spécifique perdue à la collecte (le 80 de
        # `rate_pct` serait alors servi à 80 %) — n'est pas liquidable.
        deduction = MOTIF_DEDUCTION_SARS.search(brut) if specifique else None
        deduction_ad_valorem = None
        note = row.get("note")
        if deduction and "sars.gov.za" in str(source_ligne):
            deduction_ad_valorem = float(deduction.group(1).replace(",", "."))
        elif re.search(r"\bless\b", brut, re.I):
            taux, specifique, compose, plafond_ad_valorem = None, None, False, None
            note = f"« {brut} » : la portée de « less » n'est pas établie pour cette forme ou cette source."
        compose_sars = (
            MOTIF_COMPOSE_SARS.match(brut) if compose and "sars.gov.za" in str(source_ligne) else None
        )
        if compose_sars:
            # « 2 500c/kg » : la collecte a perdu le chiffre avant l'espace des
            # milliers (« 500c/kg ») ; la part spécifique se relit sur le verbatim.
            specifique = compose_sars.group(1).replace(" ", "") + "c/kg"
        milliers = re.match(r"^\s*(\d{1,3}(?: \d{3})+)c/kg\b", brut) if specifique else None
        if milliers and "sars.gov.za" in str(source_ligne):
            # Même perte quand la part spécifique ouvre l'expression
            # (« 2 500c/kg with a maximum of 96% », « … less 80% »).
            specifique = milliers.group(1).replace(" ", "") + "c/kg"
        # « 40% + US$0.50/L » (Zimbabwe, 356 droits) ou « 15%+SCR5.13/kg »
        # (Seychelles, 5) : le « + » de la source rend les DEUX composantes
        # dues. Sans ce marqueur, le moteur liquidait la seule part ad valorem
        # et déclarait le total COMPLET.
        cumulatif = (
            not compose
            and taux is not None
            and bool(specifique)
            and re.search(r"%\s*\+", brut) is not None
        )
        out.append(
            _droit(
                code,
                libelle,
                taux,
                row.get("base") or row.get("assiette"),
                row.get("source") or source_defaut,
                note=note,
                specifique=specifique,
                qualite=row.get("source_quality"),
                classification=row.get("classification_source"),
            )
        )
        if plafond_ad_valorem is not None:
            out[-1]["plafond_ad_valorem_pct"] = plafond_ad_valorem
            out[-1]["expression_brute"] = brut
        if deduction_ad_valorem is not None:
            out[-1]["deduction_ad_valorem_pct"] = deduction_ad_valorem
        if cumulatif:
            out[-1]["cumulatif"] = True
            out[-1]["expression_brute"] = brut
        if compose:
            # Le verbatim est ce qui permet à l'opérateur — et au relecteur —
            # de constater que le droit a deux composantes, sans que le socle
            # ait eu à choisir entre elles.
            out[-1]["expression_brute"] = str(row.get("raw_value") or "")
            out[-1]["compose"] = True
            # Si — et seulement si — la source énonce la règle de départage,
            # elle est reportée telle quelle et le moteur peut liquider.
            regle = REGLES_COMPOSEES.get(str(row.get("compound_rule") or "").lower())
            if regle:
                out[-1]["regle_composee"] = regle
            elif compose_sars:
                out[-1]["regle_composee"] = "LE_PLUS_ELEVE"
                out[-1]["note"] = (
                    "SARS, Schedule No. 1, General Notes, B.3 : « each such part shall be deemed to be a separate "
                    "and complete rate of duty and such rate of duty yielding the higher or highest amount of duty "
                    "shall be applicable »."
                )
    return out


def preferences_depuis_liste(regimes, entrees, source_defaut, compteurs=None):
    """Les taux d'un champ ``preferential_rates``, sous les régimes du pays.

    Le champ existe parce que certaines sources publient leurs colonnes
    préférentielles à part, au lieu de les mêler aux taxes. Le socle ne le
    lisait pas : 83 176 taux mauriciens, dont la colonne ZLECAf de 6 932
    positions, étaient collectés puis jetés à la construction.

    UN RÉGIME QUE LA TABLE DU PAYS NE NOMME PAS N'EST PAS SERVI. Il est compté
    et écarté. C'est la seule issue sûre : le rendre sans le nommer le ferait
    tomber dans la cascade NPF comme un droit DÛ, et une préférence deviendrait
    une surtaxe.
    """
    out = []
    for e in entrees or []:
        if not isinstance(e, dict):
            continue
        # DEUX ECRITURES POUR UNE MEME CHOSE. Maurice nomme le regime dans
        # `regime` et son taux dans `rate_pct` ; la Tunisie nomme le PARTENAIRE
        # dans `country_name` et son taux dans `rate` (« 0 % »). Les deux sont
        # des colonnes preferentielles de la source : une seule lecture les
        # prend, plutot qu'une fonction par pays.
        nom = e.get("regime") or e.get("code") or e.get("country_name")
        regime = regimes.get(str(nom))
        if regime is None:
            if compteurs is not None:
                compteurs["preferentiels_non_nommes"] += 1
            continue
        # Un taux que la source déclare non liquidable — contingent tarifaire,
        # droit spécifique — n'est pas un taux : il est rendu sans valeur, avec
        # le motif que la source donne, plutôt que servi à zéro.
        brut = e.get("rate_pct") if "rate_pct" in e else e.get("rate")
        d = _droit(
            str(nom),
            e.get("regime_name_fr") or e.get("colonne_source") or str(nom),
            lire_taux(brut) if not e.get("non_liquidable") else None,
            None,
            e.get("source") or source_defaut,
            note=e.get("non_liquidable") or None,
        )
        d["_preferentiel"] = regime
        out.append(d)
    return out


def _unites_des_quantites_tun(rows, droits, qcs):
    """Tunisie : l'assiette d'un droit spécifique NOMME sa quantité — « PN (KG) »,
    le poids net en kilos ; « QCS », l'unité statistique de la position (« KG
    NET », « NOMBRE », « LITRE »…). Sans elle, « 0.1 dinars » se multipliait par
    une quantité saisie dans n'importe quelle unité."""
    unites = {"PN (KG)": "kg", "QCS": (qcs or "").strip().lower() or None}
    for row, d in zip([r for r in rows if isinstance(r, dict)], droits):
        unite = unites.get(" ".join(str(row.get("assiette") or "").split()).upper())
        if unite and d.get("specifique") and not isinstance(d["specifique"], dict):
            lu = lire_specifique(d["specifique"])
            if lu is not None:
                lu["unite_quantite"] = lu["unite_quantite"] or unite
                d["specifique"] = lu


#: Droit unique de sortie ivoirien (DUS), par début de code : ce que la
#: procédure de dédouanement de la DGD (docs_officiels/PROCEDURE-DEDOUANEMENT-
#: IMPORT-EXPORT-MARITIME.pdf, « Liste des marchandises soumises au DUS »)
#: établit au-delà du chiffre que le tarif publie sans unité. « Les prix CAF et
#: les taux sont fixés par le Conseil des ministres avant le début de chaque
#: campagne » : le prix CAF de référence n'est pas collecté, aucune de ces
#: assiettes n'est donc liquidable, sauf le karité, droit spécifique.
#: (préfixes, taux retenu ou None, spécifique, note)
DUS_CIV = [
    # Café et ses extraits (2101.11/12) ; pas la chicorée (2101.30), que la
    # liste DGD ne nomme pas.
    (("0901", "210111", "210112"), "taux", None,
     "Procédure DGD : « CAFE (TAUX = 5% DU PRIX CAF DE REFERENCE) ». Le prix CAF de référence est fixé en "
     "Conseil des ministres à chaque campagne : non collecté."),
    (("1801", "1802", "1803", "1804", "1805", "1806"), "taux", None,
     "Procédure DGD : « CACAO (TAUX = 14.6 % DU PRIX CAF DE REFERENCE POUR LA FEVE) ». Le prix CAF de "
     "référence est fixé en Conseil des ministres à chaque campagne : non collecté."),
    (("1207991",), None, "10 FCFA/kg",
     "Procédure DGD : « GRAINE DE KARITE 10 F / KG » — droit spécifique ; le tarif du 27/03/2026 publie « 10 » "
     "sans unité."),
    (("0801",), None, None,
     "Procédure DGD : « NOIX DE CAJOU (PAR CAMPAGNE) » — taux et prix fixés à chaque campagne ; le tarif du "
     "27/03/2026 publie « 10 » sans unité."),
    (("080270",), None, None,
     "La procédure DGD publie « NOIX DE COLAS 10,2 F / KG », le tarif du 27/03/2026 « 14 » sans unité : les "
     "deux ne s'accordent pas."),
    (("44",), "taux", None,
     "Procédure DGD : « BOIS PAR CUBAGE ET ESPECE » — l'assiette (cubage et espèce) n'est pas collectée."),
]


#: Droits de sortie fixés par un TEXTE, position par position, quand la collecte
#: du tarif n'en porte pas : {iso: (source, droit par défaut ou None, {code: droit})}.
#: Un droit : (taux, spécifique, note). Un taux à None reste non liquidable et
#: dit pourquoi ; une position SH6 qui regroupe une ligne nationale taxée renvoie
#: à la position nationale plutôt que d'hériter du défaut.
_EXPORT_GHA_DEFAUT = (
    0.0, None,
    "Customs Act, Fourth Schedule, Part A, 4A.13 : « All other goods grown, produced or manufactured in "
    "Ghana » 0 %. L'annexe ne vise que les biens nationaux (Part A) ; les exemptions de la Part B "
    "(État, missions diplomatiques…) ne sont pas appliquées.",
)
_EXPORT_GHA_CACAO = (
    None, None,
    "4A.4 Cocoa Beans : « The rate to be determined by the Minister for Finance and Economic Planning » "
    "— taux non publié au tarif.",
)
_EXPORT_SEN_ARACHIDE = (
    None, None,
    "Le projet de loi de finances 2026 annonce la « réactivation des droits de sortie sur les exportations "
    "d'arachide » (exposé, 9 milliards FCFA attendus) ; le texte qui en fixe le taux n'a pas été consulté.",
)
_EXPORT_SEN_OR = (
    None, None,
    "Le projet de loi de finances 2026 projette une « taxe sur l'exportation d'or » (exposé, 26,3 milliards "
    "FCFA) ; le texte qui en fixe le taux et l'assiette n'a pas été consulté.",
)
EXPORT_PAR_TEXTE = {
    "GHA": (
        "Customs (Amendment) Act, 2015 (Act 905), Fourth Schedule — Export Duty "
        "(data/ghana/docs_officiels/CUSTOMS-ACT-TARIFF-CET-HS-CODES.pdf)",
        _EXPORT_GHA_DEFAUT,
        {
            "2710192100": (None, "0.02 USD/litre", "4A.7 Gas oil : $0.02/litre."),
            # Le droit ne vaut que pour l'usage qu'il nomme : sans lui, la
            # ligne reste à établir, ni 0,09 $ ni le 0 % de 4A.13.
            "2710191100": (
                None, None,
                "4A.6 « Aviation Turbine Kerosene for international flights only » : $0.09/litre, pour "
                "le seul carburéacteur destiné aux vols internationaux ; à défaut, 4A.13 (0 %). L'usage "
                "n'est pas établi : à préciser.",
            ),
            # « Cocoa Beans » sans autre précision : fèves brutes, torréfiées
            # et brisures (1801.00.11 à 1801.00.30).
            **{code: _EXPORT_GHA_CACAO for code in (
                "1801001100", "1801001200", "1801001900", "1801002000", "1801003000")},
        },
    ),
    "SEN": (
        "Loi de finances pour 2026, art. 19 (texte du projet : data/senegal/docs_officiels/PLF-2026-SENEGAL.pdf)",
        None,
        {
            **{
                code: (
                    None, "32 FCFA/kg",
                    "Art. 19 : « Le taux du droit de sortie est fixé à 32 F CFA par kilogramme net de noix de "
                    "cajou » ; liquidé « comme en matière de douane ». Texte du projet de loi de finances : la "
                    "loi n° 2025-19 promulguée n'a pas été consultée.",
                )
                for code in ("0801310000", "0801320000")
            },
            **{code: _EXPORT_SEN_ARACHIDE for code in (
                "1202300000", "1202411000", "1202419000", "1202421000", "1202429000")},
            **{code: _EXPORT_SEN_OR for code in (
                "7108110000", "7108120000", "7108131000", "7108139000", "7108200000")},
        },
    ),
}


def droits_export_par_texte(iso, positions):
    """Droits de sortie de `EXPORT_PAR_TEXTE` pour les positions du socle."""
    regle = EXPORT_PAR_TEXTE.get(iso)
    if not regle:
        return {}
    source, defaut, par_code = regle
    sortie = {}
    for code in positions:
        droit = par_code.get(code)
        if droit is None and len(code) == 6 and any(c.startswith(code) for c in par_code):
            droit = (None, None, "Position SH6 qui regroupe des lignes nationales de droits de sortie différents : "
                                 "préciser la position nationale.")
        droit = droit or defaut
        if droit is None:
            continue
        taux, brut, note = droit
        specifique = lire_specifique(brut) if brut else None
        d = _droit("EXPORT", "Droit de sortie", taux, "CIF" if taux is not None else None, source, note=note)
        d.update(code="EXPORT", famille="export")
        if specifique:
            d.update(specifique=specifique, assiette="xQTE", assiette_origine="source")
        sortie[code] = [{k: v for k, v in d.items() if v is not None}]
    return sortie


def droits_export_du_fichier(iso, donnees):
    """Droits et taxes à l'EXPORTATION, par code national : ``{code: [droits]}``.

    Trois collectes en portent ligne par ligne : la Tunisie (``taxes_export``,
    Tarif Web), la Côte d'Ivoire (colonne DUS du tarif SYDAM) et Madagascar
    (colonne DS du tarif national 2026, ``taxes_export``). Le code de la source
    est gardé tel quel : « DD/PET.BR » est un droit de sortie, pas le droit de
    douane de l'import."""
    source = donnees.get("source") or donnees.get("source_name") or ""
    sortie = {}
    if iso == "TUN":
        for ligne in donnees.get("sub_positions") or []:
            rows = [r for r in ligne.get("taxes_export") or [] if isinstance(r, dict)]
            code = nettoyer_code(ligne.get("hs_code"))
            if not rows or not code:
                continue
            droits = droits_depuis_liste(rows, source)
            _unites_des_quantites_tun(rows, droits, ligne.get("qcs"))
            for row, d in zip(rows, droits):
                d.update(code=str(row.get("code")), famille="export")
            # Le moteur liquide dans l'ordre servi : la RPD, assise sur la somme
            # des autres droits (« SOMME D.T »), vient en dernier — comme à
            # l'import (`_ordre_tunisie`) ; sinon sa base serait nulle.
            droits.sort(key=lambda d: str(d.get("assiette") or "").startswith("SOMME"))
            sortie[code] = [{k: v for k, v in d.items() if v is not None} for d in droits]
    elif iso == "CIV":
        for ligne in donnees.get("positions") or []:
            code = nettoyer_code(ligne.get("code_clean"), ligne.get("hs_code"), ligne.get("code"))
            for row in ligne.get("taxes_detail") or []:
                if not isinstance(row, dict) or row.get("tax_code") != "DUS" or not code:
                    continue
                regle = next((r for r in DUS_CIV if code.startswith(r[0])), None)
                taux = lire_taux(row.get("rate"))
                note = "Assiette « variable » au tarif : non établie."
                specifique = None
                if regle:
                    _, garde, brut, note = regle
                    taux = taux if garde == "taux" else None
                    specifique = lire_specifique(brut) if brut else None
                d = _droit("DUS", row.get("tax_name") or "Droit Unique de Sortie", taux, None, source, note=note)
                d.update(code="DUS", famille="export")
                if specifique:
                    d.update(specifique=specifique, assiette="xQTE", assiette_origine="source")
                sortie.setdefault(code, []).append({k: v for k, v in d.items() if v is not None})
    elif iso == "MDG":
        for ligne in donnees.get("sub_positions") or []:
            code = nettoyer_code(ligne.get("hs_code"))
            for row in ligne.get("taxes_export") or []:
                if not isinstance(row, dict) or not code:
                    continue
                # « Valeur » : la colonne d'unité du DS nomme la valeur en douane
                # pour assiette ; toute autre unité n'est pas traduite.
                assiette = "VALEUR DOUANE" if row.get("assiette_publiee") == "Valeur" else row.get("assiette_publiee")
                d = _droit("DS", row.get("name") or "Droit de sortie", row.get("rate"), assiette,
                           row.get("source") or source, note=row.get("note"))
                d.update(code="DS", famille="export")
                sortie.setdefault(code, []).append({k: v for k, v in d.items() if v is not None})
    return sortie


def lignes_du_fichier(donnees, regimes=None, compteurs=None):
    """Rendre (code, designation, unite, droits_bruts) pour les six schémas."""
    source_defaut = donnees.get("source") or donnees.get("source_name") or ""
    regimes = regimes or {}

    for cle in ("positions", "sub_positions"):
        for ligne in donnees.get(cle, []) or []:
            if not isinstance(ligne, dict):
                continue
            code = nettoyer_code(
                ligne.get("code_clean"),
                ligne.get("hs_code"),
                ligne.get("code"),
                ligne.get("code_raw"),
                # `national_code` doit passer AVANT `hs6`, sans quoi une collecte
                # nationale est rabattue sur six chiffres et ses sous-positions
                # entrent en collision. La Libye perdait ainsi 349 de ses 5 920
                # positions, sans que rien ne le signale.
                ligne.get("national_code"),
                ligne.get("hs6"),
            )
            if not code:
                continue
            droits = []
            if isinstance(ligne.get("taxes_detail"), list):
                droits = droits_depuis_liste(ligne["taxes_detail"], source_defaut)
            elif isinstance(ligne.get("taxes"), list):
                droits = droits_depuis_liste(ligne["taxes"], source_defaut)
            elif isinstance(ligne.get("taxes"), dict):
                droits = droits_depuis_dict(ligne["taxes"], source_defaut)
            elif isinstance(ligne.get("taxes_import"), list):
                droits = droits_depuis_liste(ligne["taxes_import"], source_defaut)
                _unites_des_quantites_tun(ligne["taxes_import"], droits, ligne.get("qcs"))
            colonnes = ligne.get("preferential_rates")
            if not isinstance(colonnes, list):
                colonnes = ligne.get("preferences")
            if regimes and isinstance(colonnes, list):
                droits = droits + preferences_depuis_liste(
                    regimes, colonnes, source_defaut, compteurs
                )
            yield (
                code,
                ligne.get("designation") or ligne.get("name") or ligne.get("description") or "",
                ligne.get("unit") or ligne.get("statistical_unit"),
                droits,
                ligne.get("source") or source_defaut,
                ligne.get("restrictions"),
            )

    # Schéma « tariff_lines[] » : la ligne SH6 porte les taxes, ses enfants
    # nationaux portent leur propre droit de douane. Les deux sont adressables.
    for ligne in donnees.get("tariff_lines", []) or []:
        if not isinstance(ligne, dict):
            continue
        droits_parent = droits_depuis_liste(ligne.get("taxes_detail"), source_defaut)
        designation = ligne.get("description_fr") or ligne.get("description_en") or ""
        hs6 = nettoyer_code(ligne.get("hs6"))
        enfants = ligne.get("sub_positions") or []
        if hs6:
            yield (
                hs6,
                designation,
                ligne.get("unit"),
                droits_parent,
                ligne.get("dd_source") or source_defaut,
                ligne.get("restrictions"),
            )
        for enfant in enfants:
            if not isinstance(enfant, dict):
                continue
            code = nettoyer_code(enfant.get("code"))
            if not code:
                continue
            # Le droit de douane de l'enfant prime sur celui du parent ; les
            # autres prélèvements du parent s'appliquent à l'enfant.
            droits = []
            dd_enfant = lire_taux(enfant.get("dd"))
            for d in droits_parent:
                if d["code"] == "DD" and dd_enfant is not None:
                    d = dict(d, taux=dd_enfant, source=enfant.get("source") or d["source"])
                droits.append(d)
            if dd_enfant is not None and not any(d["code"] == "DD" for d in droits_parent):
                droits.insert(
                    0,
                    _droit(
                        "DD",
                        "Droit de douane",
                        dd_enfant,
                        None,
                        enfant.get("source") or source_defaut,
                    ),
                )
            yield (
                code,
                enfant.get("description_fr") or enfant.get("description_en") or designation,
                ligne.get("unit"),
                droits,
                enfant.get("source") or source_defaut,
                enfant.get("restrictions") or ligne.get("restrictions"),
            )


# ── Construction ──────────────────────────────────────────────────────────────
def sha256(chemin: str) -> str:
    h = hashlib.sha256()
    with open(chemin, "rb") as f:
        for bloc in iter(lambda: f.read(1 << 20), b""):
            h.update(bloc)
    return h.hexdigest()


#: Pays dont le tarif ne publie sa désignation que dans une langue, et pour
#: lesquels l'utilisateur a demandé que le socle serve aussi un libellé français
#: et anglais. LISTE NOMMÉE, pays par pays : rien n'est enrichi sans y figurer.
#: Le libellé NATIONAL n'est jamais remplacé — il reste le verbatim qui fait foi.
PAYS_LIBELLES_TRADUITS = {
    "MOZ": "pt",  # Pauta Aduaneira, portugais
    "EGY": "ar",  # tarif douanier égyptien, arabe — et son libellé est VIDE
    "AGO": "pt",  # Pauta Aduaneira, portugais
}

LIBELLES_SH6_PATH = os.path.join(ETL_DIR, "hs6_designations_fr_en.json")


def charger_libelles_sh6():
    """Les libellés SH6 en français et en anglais, EMPRUNTÉS à d'autres tarifs
    nationaux par scripts/construire_libelles_sh6.py — jamais traduits ici."""
    try:
        with open(LIBELLES_SH6_PATH, encoding="utf-8") as f:
            charge = json.load(f)
    except (OSError, json.JSONDecodeError):
        return {}
    table = charge.get("libelles")
    return table if isinstance(table, dict) else {}


def traduire_designation(designation, hs6, libelles, langue_origine):
    """Ajouter `fr` et `en` à une désignation, SANS toucher au libellé national.

    Les libellés empruntés décrivent le PARENT SH6, pas la subdivision
    nationale : la désignation le déclare, pour que personne ne les prenne
    pour le libellé de la ligne servie.
    """
    entree = libelles.get(hs6) or {}
    if not entree:
        return designation
    if isinstance(designation, str):
        designation = {langue_origine: designation, "verbatim": designation}
    elif isinstance(designation, dict):
        designation = dict(designation)
    else:
        return designation
    ajoutes = []
    for langue in ("fr", "en"):
        if not entree.get(langue):
            continue
        # Ne JAMAIS écraser un libellé que le tarif national publie lui-même.
        if str(designation.get(langue) or "").strip():
            continue
        designation[langue] = entree[langue]
        designation[f"{langue}_source"] = entree.get(f"{langue}_source")
        ajoutes.append(langue)
    if ajoutes:
        designation["langues_empruntees"] = ajoutes
        designation["niveau_libelle_emprunte"] = "SH6"
    return designation


def sources_disponibles():
    """Le crawl d'abord ; le fichier ETL seulement là où aucun crawl n'existe."""
    sources = {}
    for chemin in sorted(glob.glob(os.path.join(CRAWL_DIR, "*_tariffs.json"))):
        iso = os.path.basename(chemin)[:3]
        if "_progress_" in os.path.basename(chemin):
            continue
        sources[iso] = (chemin, "crawl")
    for chemin in sorted(glob.glob(os.path.join(ETL_DIR, "*_tariffs.json"))):
        iso = os.path.basename(chemin)[:3]
        sources.setdefault(iso, (chemin, "etl"))
    return sources


#: Cameroun : le crawl marquait le droit d'accises « variable » (-1) sur 292
#: positions tirées d'un repère typographique — tissus de coton, médicaments et
#: sel compris, voitures et cosmétiques omis. La liste et les taux viennent du
#: CGI (annexe II, art. 142) ; l'assiette de la TVA, de son art. 138 (1).
#: Gabon : même marquage du crawl ; liste et taux du CGI gabonais (art. 250),
#: assiette de la TVA de son art. 216.
#: Code du prélèvement → bloc dont les originaires en sont exclus.
#: Le PNS du Togo ne frappe que les marchandises importées hors CEDEAO.
EXONERATION_ORIGINE = {
    "PCS": "UEMOA", "PCC": "CEDEAO", "CEDEAO": "CEDEAO", "PUA": "UA", "PC-AES": "AES_UEMOA", "PNS": "CEDEAO",
}
#: Pays où ces prélèvements sont perçus (le PCS hors UEMOA serait un autre droit).
BLOCS_DESTINATION = {
    "UEMOA": {"BEN", "BFA", "CIV", "GNB", "MLI", "NER", "SEN", "TGO"},
    "CEDEAO": {"BEN", "BFA", "CPV", "CIV", "GMB", "GHA", "GIN", "GNB", "LBR", "MLI", "NER", "NGA", "SEN", "SLE", "TGO"},
    # PC-AES : perçu par les trois États de l'AES ; ni les originaires de l'AES
    # ni ceux de l'UEMOA, union douanière avec eux, n'y sont soumis.
    "AES_UEMOA": {"BFA", "MLI", "NER"},
}

ACCISES_PAYS = {
    "CMR": os.path.join(REPO, "backend", "data", "zlecaf_cmr", "droit_accises_cgi2025.json"),
    "GAB": os.path.join(REPO, "backend", "data", "zlecaf_gab", "droit_accises_cgi2025.json"),
    "COG": os.path.join(REPO, "backend", "data", "zlecaf_cog", "droit_accises_lf2026.json"),
    "CAF": os.path.join(REPO, "backend", "data", "zlecaf_caf", "droit_accises_cgi2023.json"),
    "GNQ": os.path.join(REPO, "backend", "data", "zlecaf_gnq", "droit_accises_lp2020.json"),
    "SEN": os.path.join(REPO, "backend", "data", "zlecaf_sen", "droit_accises_cgi2025.json"),
    "GHA": os.path.join(REPO, "backend", "data", "zlecaf_gha", "droit_accises_act878.json"),
    "BFA": os.path.join(REPO, "backend", "data", "zlecaf_bfa", "droit_accises_cgi2026.json"),
    "TGO": os.path.join(REPO, "backend", "data", "zlecaf_tgo", "droit_accises_cgi2025.json"),
    "TCD": os.path.join(REPO, "backend", "data", "zlecaf_tcd", "droit_accises_lf2026.json"),
}


# Assiette de l'accise quand le tarif collecté ne la donne pas : une table par
# pays, tirée de sa loi d'accise.
ASSIETTE_ACCISE_PAYS = {
    "MUS": os.path.join(REPO, "backend", "data", "zlecaf_mus", "assiette_accise_excise_act.json"),
}


def _assiette_accise(iso, positions):
    with open(ASSIETTE_ACCISE_PAYS[iso], encoding="utf-8") as f:
        table = json.load(f)
    ad_valorem, occasion = set(table["ad_valorem"]), set(table["occasion"])
    annexe = ad_valorem | occasion | set(table["specifique"])
    montants = table.get("montants_specifiques", {})
    non_liquidables = {
        code: (brut, groupe["raison"])
        for groupe in table.get("specifiques_non_liquidables", {}).values()
        for code, brut in groupe["codes"].items()
    }
    for code, position in positions.items():
        for d in position.get("droits") or []:
            if d.get("famille") != "accise" or d.get("assiette"):
                continue
            if d.get("taux") is None and not d.get("specifique"):
                if code in montants:
                    m = montants[code]
                    d["specifique"] = {
                        "montant": m["montant"], "unite_monetaire": "unite_principale", "sous_unite_source": None,
                        "unite_quantite": m["unite_quantite"], "brut": m["brut"]}
                    d["assiette"] = "xQTE"
                    d["assiette_origine"] = "droit_specifique"
                    d["source"] = table["source"]
                    d["note"] = f"First Schedule, Part I : « {m['brut']} »."
                elif code in non_liquidables:
                    brut, raison = non_liquidables[code]
                    d["note"] = f"First Schedule, Part I : « {brut} » ; {raison} — non liquidable en l'état."
                continue
            if d.get("taux") is None:
                continue
            if code in ad_valorem or (d["taux"] == 0 and code in annexe):
                d["assiette"] = table["assiette"]
                d["assiette_origine"] = "regle_de_pays"
                d["note"] = table["assiette_reference"]
            elif code in occasion:
                d["note"] = (
                    "Véhicule d'occasion : la « value at importation » est déterminée selon des "
                    "modalités prescrites (Excise Act s.2), non lues — non liquidable en l'état."
                )
            else:
                d["note"] = (
                    "Position absente de la First Schedule de l'Excise Act en vigueur : "
                    "le taux collecté n'est pas confirmé — non liquidable en l'état."
                )


def _ordre_tunisie(positions):
    """Tunisie : la TVA s'assoit sur tous les droits et taxes sauf elle-même
    (Code de la TVA art. 6) et la RPD sur la somme des droits et taxes des
    groupes 0 à 4, TVA comprise (Tarif Web « SOMME D.T (G=0.1.2.3.4.) »). Le
    moteur liquide dans l'ordre : TVA après les autres droits, RPD en dernier.
    Minimum de perception de la RPD : 10 dinars par article de déclaration
    (loi n° 87-83, art. 51, modifié par la loi n° 2012-27, art. 57)."""
    for position in positions.values():
        droits = position.get("droits") or []
        rpd = [d for d in droits if d.get("code") == "RPD"]
        tva = [d for d in droits if d.get("famille") == "tva"]
        autres = [d for d in droits if d not in rpd and d not in tva]
        for d in rpd:
            if d.get("taux"):
                d["minimum_perception"] = {"montant": 10.0, "devise": "TND"}
            d["note"] = (
                "3 % de la somme des droits et taxes liquidés, TVA comprise ; minimum de "
                "perception 10 dinars par article de déclaration (loi n° 2012-27, art. 57)."
            )
        position["droits"] = autres + tva + rpd


def _ordre_ethiopie(positions):
    """Éthiopie : assiettes et ordre de liquidation fixés par les textes.
    Accise : valeur en douane + droit de douane (Excise Tax Proclamation
    1186/2020, art. 9(2)). TVA : valeur + droit, accise et autres charges, hors
    TVA et avance d'impôt (VAT Proclamation 1341/2024, art. 27). Surtaxe : CIF +
    droit + TVA + accise (Council of Ministers Regulation 133/2007). WHR : 3 % de
    la valeur CIF, importations commerciales (Income Tax Proclamation 979/2016,
    art. 85)."""
    assiettes = {
        "EXC": ("CIF+DD", "Excise Tax Proclamation 1186/2020, art. 9(2) : valeur en douane + droit de douane."),
        "TVA": (
            "CIF+TOUS_SAUF_TVA",
            "VAT Proclamation 1341/2024, art. 27 : valeur en douane + droit, accise et autres charges, "
            "hors TVA et avance d'impôt sur le revenu.",
        ),
        "SUR": ("CIF+DD+EXC+TVA", "Council of Ministers Regulation 133/2007 : CIF + droit + TVA + accise."),
        "WHR": (
            "CIF",
            "Income Tax Proclamation 979/2016, art. 85 : avance de 3 % de la valeur CIF, importations "
            "à usage commercial, imputable sur l'impôt sur le revenu.",
        ),
        "SWL": (
            "CIF",
            "Social Welfare Levy on Imported Goods Regulation 519/2022, art. 5 : valeur CIF.",
        ),
    }
    rang = {"EXC": 1, "TVA": 3, "SUR": 4, "WHR": 5, "SWL": 6}
    for position in positions.values():
        droits = position.get("droits") or []
        for d in droits:
            if d.get("code") in assiettes:
                d["assiette"], note = assiettes[d["code"]]
                d["note"] = f"{note} {d['note']}" if d.get("note") else note
                d["assiette_origine"] = "regle_de_pays"
        position["droits"] = sorted(droits, key=lambda d: rang.get(d.get("code"), 2 if d.get("code") != "DD" else 0))


#: Barème d'accise éthiopien (CSV ACCISE_ETH), au plus près du Premier
#: Schedule : sous-positions nommées par l'annexe, codes du livre tarifaire
#: rapportés au portail par leur libellé (3304.9990 → 3304.99.10). Les lignes
#: conditionnées hors nomenclature — véhicules selon l'âge, bières selon la
#: teneur en matières premières locales, chapitre 15 selon graisses saturées,
#: chapitre 27 restreint à certains carburants, chapitre 71 restreint aux
#: ornements — n'y sont pas : elles restent au portail.
SOURCE_ACCISE_ETH = (
    "Excise Tax Proclamation 1186/2020, Premier Schedule (annexe I de la "
    "Proclamation 1287/2023, Negarit Gazette n° 39 du 15/09/2023) ; directive "
    "1007/2024 pour les taux spécifiques."
)


def _accise_ethiopie(positions, compteurs):
    """Éthiopie : barème d'accise consolidé (Premier Schedule tel que remplacé
    par l'annexe I de la Proclamation 1287/2023 ; taux spécifiques remplacés
    par la directive 1007/2024 ; fiche ETH_accise_bareme_SWL_2026-10-12.json).

    Le portail publie un taux d'accise ad valorem par position ; une case vide
    y est un 0 % publié, que la collecte écartait (voir _droits_livre_ethiopie).
    Le barème ne le remplace donc pas par un taux tiré d'une fourchette de
    l'annexe : il porte seulement, sur le taux publié qu'il confirme, la
    composante spécifique et la règle de liquidation (« 40 % or 28 Birr per
    liter whichever is higher » : LE_PLUS_ELEVE ; « 30 % + 20 Birr per pack » :
    cumulatif). Seule exception : l'accise purement spécifique (sacs de caisse,
    103 Birr/kg), sans part ad valorem que le portail puisse afficher."""
    with open(ACCISE_ETH, encoding="utf-8") as f:
        lignes = list(csv.DictReader(f))
    for code, position in positions.items():
        ligne = next((l for l in lignes if _couvre_accise_eth(l, code)), None)
        if ligne is None:
            continue
        droits = position.get("droits") or []
        existant = next((d for d in droits if d.get("code") == "EXC" and d.get("taux") is not None), None)
        if existant is not None:
            if ligne["taux_ad_valorem"] and float(ligne["taux_ad_valorem"]) != existant["taux"]:
                existant["note"] = (
                    f"Le barème de l'annexe I porte {ligne['taux_ad_valorem']} %"
                    + (f" ({ligne['condition']})" if ligne["condition"] else "")
                    + " : taux du portail conservé, à confronter."
                )
                continue
            existant["source"] = SOURCE_ACCISE_ETH
            _porter_composantes_accise(existant, ligne)
            continue
        if ligne["regle"] != "SPECIFIQUE" or any(d.get("code") == "EXC" for d in droits):
            continue
        d = _droit("EXC", "Excise Tax", None, None, SOURCE_ACCISE_ETH)
        _porter_composantes_accise(d, ligne)
        d["note"] = f"Accise spécifique de l'annexe I, directive 1007/2024 : {ligne['verbatim']} ({ligne['condition']})."
        droits.append(d)
        compteurs["assiettes_table"] += 1
        position["droits"] = droits


def _porter_composantes_accise(d, ligne):
    if ligne["specifique_montant"]:
        d["specifique"] = {
            "montant": float(ligne["specifique_montant"]),
            "unite_monetaire": "ETB",
            "unite_quantite": ligne["unite_quantite"] or None,
            "brut": ligne["verbatim"],
        }
    if ligne["regle"] == "LE_PLUS_ELEVE":
        d["compose"] = True
        d["regle_composee"] = "LE_PLUS_ELEVE"
    elif ligne["regle"] == "CUMULATIF":
        d["cumulatif"] = True
    d["expression_brute"] = ligne["verbatim"] or None


def _couvre_accise_eth(ligne, code):
    """Vrai si la ligne du barème couvre le code de la position : bornes
    comparées sur leur propre longueur (« 50 » à « 56 » : chapitres 50 à 56)."""
    de, a = ligne["code_de"].strip(), ligne["code_a"].strip()
    return bool(de) and de <= code[: len(de)] and code[: len(a)] <= a


#: Surtaxe (Regulations 133/2007, art. 5(1)(a) et annexe, version amharique
#: qui fait foi) : engrais (31) ; « ነዳጅ » carburants — pétrole brut et huiles
#: (27.09, 27.10), gaz de pétrole (27.11), coke de pétrole (2713.11, 2713.12) —
#: et lubrifiants (34.03) ; « የጭነትና የሕዝብ ማመላለሻ ተሽከርካሪዎች » véhicules de
#: fret et de transport de personnes et véhicules à usage spécial (87.02 à
#: 87.05) ; aéronefs, engins spatiaux et leurs parties (88). Vaseline et
#: paraffine (27.12), bitume (2713.20, 2713.90) et motocycles (87.11) n'en sont
#: pas : surtaxe due.
SURTAXE_EXEMPTEE_ETH = (
    "31", "2709", "2710", "2711", "271311", "271312", "3403", "8702", "8703", "8704", "8705", "88",
)
#: Produits que le rapport du ministère des Finances (2022) dit exclus de la
#: surtaxe par une directive prise en vertu de l'art. 5(2) : aucune directive
#: trouvée, la surtaxe de l'art. 2 est servie et l'allégation dite en note.
SURTAXE_DIRECTIVE_NON_TROUVEE_ETH = ("02", "0701", "1202", "1701")
NOTE_VOITURES_ETH = (
    " Voitures particulières : exemptées de surtaxe comme véhicules « for freight and passengers » "
    "(annexe, version anglaise ; rapport du ministère des Finances : « including buses ») ; la version "
    "amharique dit « የሕዝብ ማመላለሻ » (transport de personnes, ou transport public) : à confirmer."
)
NOTE_DIRECTIVE_ETH = (
    "Le rapport du ministère des Finances sur les dépenses fiscales à l'importation (2022) dit ce produit "
    "exclu de la surtaxe par une directive ultérieure (art. 5(2)) ; aucune directive trouvée : surtaxe "
    "servie selon l'art. 2. "
)
NOTE_SURTAXE_ETH = (
    "Surtaxe de 10 % sur toute importation hors exemptions (Import Sur-Tax Council of Ministers "
    "Regulations 133/2007, Negarit Gazeta n° 23 du 11/04/2007, art. 2 à 5 et annexe). Exemptions liées "
    "à l'importateur ou à l'emploi, non servies par position : biens d'équipement (« Capital (Investment "
    "goods) »), personnes exonérées de droits de douane (art. 5(1)(b)), taux préférentiels de la seconde "
    "annexe (industries locales)."
)
NOTE_SWL_ETH = (
    "Social Welfare Levy on Imported Goods Regulation 519/2022 : 3 % de la valeur CIF (art. 4 et 5), "
    "sur les marchandises que la surtaxe ne frappe pas (art. 6(2) : exemptées « goods that are subject to "
    "the sur tax ») ; n'entre dans la base d'aucune autre taxe. Exonérations par bénéficiaire ou usage de "
    "la directive 1023/2024 (dons, accords internationaux, défense, banque centrale), non servies par "
    "position."
)


def _surtaxe_et_swl_ethiopie(positions, compteurs):
    """Éthiopie : surtaxe ou taxe sociale, l'une excluant l'autre (fiche
    ETH_surtaxe_SWL_2026-10-12.json). Surtaxe de 10 % sur toute importation
    hors exemptions de l'art. 5 du Règlement 133/2007 ; la taxe sociale de 3 %
    de la valeur CIF (Règlement 519/2022) exempte ce que la surtaxe frappe
    (art. 6(2)) et ne vise donc que les catégories exemptées de surtaxe.

    Le portail ne porte la surtaxe que sur deux positions (colonne SR) ; leur
    taux publié est conservé."""
    for code, position in positions.items():
        droits = [d for d in position.get("droits") or [] if d.get("code") != "SWL"]
        if any(d.get("code") == "SUR" for d in droits):
            position["droits"] = droits
            continue
        if code.startswith(SURTAXE_EXEMPTEE_ETH):
            d = _droit("SWL", "Social Welfare Levy (taxe sociale)", 3.0, None, "Regulation 519/2022")
            d["note"] = NOTE_SWL_ETH + (NOTE_VOITURES_ETH if code.startswith("8703") else "")
        else:
            d = _droit("SR", "Surtax", 10.0, None, "Council of Ministers Regulation 133/2007")
            directive = code.startswith(SURTAXE_DIRECTIVE_NON_TROUVEE_ETH)
            d["note"] = (NOTE_DIRECTIVE_ETH if directive else "") + NOTE_SURTAXE_ETH
        compteurs["assiettes_table"] += 1
        position["droits"] = droits + [d]


def _droits_livre_ethiopie(positions, compteurs):
    """Éthiopie : droit de douane perdu à la collecte, rétabli par le livre
    tarifaire du ministère des Finances (édition révisée de 2021, fiche
    ETH_droits_livre_tarifaire_2021-10-07.json) quand le livre le dit nul.

    La collecte du 05/07/2026 écartait chaque droit publié à 0 %
    (`tax_values[i] > 0`, voir .github/workflows/veille_eth_crawl.yml) : sa
    case vide est un 0 % du portail, pas un taux absent. Le livre le confirme,
    « Free » sur 96 % de ces positions contre 0,4 % ailleurs. Il ne comble donc
    que ses « Free ». Un taux non nul du livre contredit le 0 % que le portail
    publiait très probablement : le droit reste à compléter, le conflit en
    note, jusqu'à une collecte fraîche. Une sous-position dont la portée a
    changé en SH 2022 n'est pas comblée."""
    with open(LIVRE_TARIFAIRE_ETH, encoding="utf-8") as f:
        livre = {r["code"].replace(".", ""): r["taux"] for r in csv.DictReader(f)}
    # Le livre est en SH 2017, le portail en SH 2022 : une sous-position dont la
    # table I de l'OMD (SH 2022 -> SH 2017) dit la portée modifiée n'est pas comblée.
    spec = importlib.util.spec_from_file_location(
        "concordance_tun", os.path.join(REPO, "backend", "scripts", "extraire_concordance_tun.py")
    )
    concordance = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(concordance)
    modifiees = concordance.lire_table_i()
    for code, position in positions.items():
        if code[:6] in modifiees:
            continue
        for d in position.get("droits") or []:
            taux = livre.get(code[:8])
            if d.get("code") != "DD" or d.get("taux") is not None or taux in (None, "Prohibited"):
                continue
            d["libelle"] = "Droit de douane"
            ligne = f"{code[:4]}.{code[4:8]}"
            if taux != "Free":
                d["note"] = (
                    "Droit écarté par la collecte du portail, qui omettait les taux à 0 % ; "
                    f"le livre tarifaire 2021 porte {taux.rstrip('%')} % sous {ligne} : à vérifier au portail."
                )
                continue
            d["taux"] = 0.0
            d["source"] = "Livre tarifaire du ministère des Finances, édition révisée 2021"
            d["note"] = (
                "Droit écarté par la collecte du portail, qui omettait les taux à 0 % ; "
                f"« Free » au livre tarifaire 2021 sous {ligne}."
            )
            compteurs["taux_indisponibles"] -= 1
def _iat_nigeria_2026(positions, compteurs):
    """Nigéria : IAT de la Customs, Excise Tariff, Etc. (Variation) Order 2026
    (S.I. 29, Gazette n° 79 du 1er mai 2026, First Schedule ; fiche
    NGA_IAT_SI29_2026-10-08.json). Elle révoque l'Order de 2023 : une position
    absente de la liste ne porte plus d'IAT."""
    with open(IAT_NGA_2026, encoding="utf-8") as f:
        liste = {r["code"].replace(".", ""): float(r["iat"]) for r in csv.DictReader(f)}
    for code, position in positions.items():
        droits = position.get("droits") or []
        for d in droits:
            if d.get("code") != "IAT":
                continue
            avant = d.get("taux")
            d["source"] = "Customs, Excise Tariff, Etc. (Variation) Order 2026 (S.I. 29), First Schedule"
            if code in IAT_NGA_AMBIGUS:
                d["taux"] = None
                d["note"] = (
                    "IAT 2026 non attribuable : la liste vise cette position sous un code ancien ou à "
                    "deux taux (" + IAT_NGA_AMBIGUS[code] + ")."
                )
            elif code in liste:
                d["taux"] = liste[code]
                d["note"] = "Liste IAT de l'Order 2026, en vigueur au 1er mai 2026."
            else:
                d["taux"] = 0.0
                d["note"] = "Position absente de la liste IAT de l'Order 2026, qui révoque celui de 2023."
            compteurs["taux_indisponibles"] += (d["taux"] is None) - (avant is None)
            # Ciments 2523 : IAT vide au portail et « accise » égale à l'IAT de la liste,
            # dont le total (droit + IAT) exclut une accise de même taux.
            for e in droits:
                if avant is None and d["taux"] and e.get("code") == "EXC" and e.get("taux") == d["taux"]:
                    e["taux"] = None
                    e["note"] = (
                        "Accise du portail égale à l'IAT de la liste de l'Order 2026, IAT absente "
                        "au portail : vraisemblablement l'IAT mal rangée, non servie deux fois."
                    )
                    compteurs["taux_indisponibles"] += 1


#: Sierra Leone : Part II du Schedule du Customs Tariff Act 1978, abrogée et
#: remplacée par le Finance Act 2026, s.2 (fiche SLE_droits_nationaux_2026-10-25.json).
#: Seules les lignes que le tarif servi (TEC CEDEAO, SH 2017) isole sans les
#: déborder. (positions, taux %, item de la Part II)
DROITS_NATIONAUX_SLE = (
    (("040711", "040719", "040721", "040729", "040790"), 35.0, "i, imported eggs"),
    (("2103200000",), 35.0, "ii, imported tomato ketchup and other tomato sauces"),
    (("2104109000",), 35.0, "iv, imported maggi cube"),
    (("220110", "220190", "2202100000"), 35.0, "v, imported bottled water"),
    (("271112", "271113", "271119"), 0.0, "vi, LPG (butane/propane)"),
    (("4404200000",), 35.0, "vii, wooden poles"),
    (("4412100000", "4412310000", "4412330000"), 35.0, "viii, imported plywood"),
    (("7317009000",), 30.0, "x, imported nails"),
    (("732111", "7321900000"), 0.0, "xi, LPG stoves and others (including accessories)"),
)


def _droits_nationaux_sle(positions):
    for code, position in positions.items():
        regle = next((r for r in DROITS_NATIONAUX_SLE if code.startswith(r[0])), None)
        if regle is None:
            continue
        for d in position.get("droits") or []:
            if d.get("code") == "DD":
                d["taux"] = regle[1]
                d["source"] = "Customs Tariff Act 1978, Schedule, Part II (Finance Act 2026, s.2)"
                d["note"] = f"Taux national de la Part II, item {regle[2]}, en vigueur au 1er janvier 2026."


def _droits_angola_2026(positions, compteurs):
    """Angola : droit de douane de 2026 (Lei n.º 14/25, OGE 2026 ; fiche
    AGO_droits_2026-10-25.json). Taux de l'Anexo III (art. 31.º n.º 6) ; ailleurs,
    minimum de 5 % (art. 31.º n.º 3), « Livre » excepté. Une position de la Pauta
    2024 que l'Anexo III subdivise en codes qu'elle n'a pas perd son taux."""
    with open(DROITS_AGO_2026, encoding="utf-8") as f:
        anexo = {r["code"]: r for r in csv.DictReader(f, delimiter=";")}
    subdivisions = collections.defaultdict(list)
    for code, r in anexo.items():
        if code not in positions:
            taux = "Livre" if r["taux"] == "Livre" else f"{r['taux']} %"
            subdivisions[code[:6]].append(f"{code[:4]}.{code[4:6]}.{code[6:]} : {taux}")
    for code, position in positions.items():
        dd = next((d for d in position.get("droits") or [] if d.get("code") == "DD"), None)
        if dd is None:
            continue
        _compter_ligne(dd, compteurs, -1)
        avant = "illisible" if dd["taux"] is None else f"{dd['taux']:g} %"
        if code in anexo:
            r = anexo[code]
            dd["taux"] = 0.0 if r["taux"] in ("Livre", "0") else float(r["taux"])
            dd["source"] = "Lei n.º 14/25 (OGE 2026), art. 31.º n.º 6 et Anexo III"
            dd["note"] = f"Taux de l'Anexo III (Diário, p. {r['page_diario']}) ; Pauta 2024 : {avant}."
        elif code.endswith("00") and subdivisions.get(code[:6]):
            dd["taux"] = None
            dd["note"] = ("L'Anexo III de la Lei n.º 14/25 subdivise cette position : "
                          f"{', '.join(subdivisions[code[:6]])}. Taux à lire sur la sous-position.")
        elif dd["taux"] is not None and 0 < dd["taux"] < 5:
            dd["taux"] = 5.0
            dd["source"] = "Lei n.º 14/25 (OGE 2026), art. 31.º n.º 3"
            dd["note"] = f"Taux minimum de 5 % pour 2026 ; Pauta 2024 : {avant}."
        _compter_ligne(dd, compteurs, 1)


def _taux_tva_legaux():
    """La table TAUX_TVA_LEGAUX de backend/services/tax_profile_data.py."""
    if REPO not in sys.path:
        sys.path.insert(0, REPO)
    return importlib.import_module("backend.services.tax_profile_data").TAUX_TVA_LEGAUX


def _taux_tva_hors_la_loi(regle, positions, compteurs):
    """Un taux de TVA collecté que la loi du pays ne connaît pas (1 % ou 17,5 %
    sur quelques positions du portail nigérian) n'est pas servi : la TVA reste
    à compléter, avec le taux collecté en note. Fiche : regle["fiche"]."""
    for position in positions.values():
        for d in position.get("droits") or []:
            if d.get("code") != "TVA" or d.get("taux") is None or d["taux"] in regle["taux"]:
                continue
            taux_lu = f"{d['taux']:g}".replace(".", ",")
            d["note"] = f"Taux de TVA collecté au portail : {taux_lu} %. {regle['loi']} : à vérifier au portail."
            d["taux"] = None
            compteurs["taux_indisponibles"] += 1


def _redevance_informatique_cmr(positions):
    """Cameroun : redevance informatique à 1 % de la valeur imposable, sans plafond
    à l'importation (loi de finances 2023, art. 9 a), maintenu par la loi de
    finances 2026, art. 12 a) ; fiche CMR_redevance_informatique_2026-10-09.json).
    Le crawl porte encore 0,45 % avec un plafond de 15 000 XAF sur la base : le
    régime de 2018, où le plafond visait déjà le montant, à l'exportation."""
    for position in positions.values():
        for d in position.get("droits") or []:
            if d.get("code") != "RI":
                continue
            # L'assiette reste celle de la source (CIF) : c'est la « valeur
            # imposable » de la loi ; seuls le taux et le plafond changent.
            d["taux"] = 1.0
            d["plafond"] = None
            d["source"] = "Loi de finances 2023 du Cameroun, art. 9 a)"
            d["note"] = (
                "Loi de finances 2023, art. 9 a), maintenu par la loi de finances 2026, art. 12 a) : "
                "« 1% de la valeur imposable des marchandises. Ce prélèvement est plafonné à "
                "15 000 F CFA par déclaration à l'exportation » ; pas de plafond à l'importation."
            )


#: Maurice : MID levy (Excise Act s.3A, First Schedule Part II, version consolidée
#: MRA du 01.10.2026), en roupies par unité ; fiche MUS_mid_levy_2026-10-25.json.
MID_MUS = {
    "27011100": (0.30, "kg"), "27011200": (0.30, "kg"), "27011900": (0.30, "kg"),
    "27101931": (0.30, "litre"), "27101939": (0.30, "litre"), "27101969": (0.30, "litre"),
    "27111310": (0.30, "kg"), "27111320": (0.30, "kg"), "27111390": (0.30, "kg"),
}


def _mid_levy_maurice(positions, compteurs):
    """La MID levy entre dans l'assiette de la TVA (VAT Act 1998, s.13 (c))."""
    for code, position in positions.items():
        droits = position.get("droits") or []
        mid = next((d for d in droits if d.get("code") == "MID"), None)
        if not mid:
            continue
        _compter_ligne(mid, compteurs, -1)
        if code in MID_MUS:
            montant, unite = MID_MUS[code]
            brut = f"{montant * 100:g} cents per {unite}"
            mid.update(taux=None, assiette="xQTE", assiette_origine="droit_specifique", specifique={
                "montant": montant, "unite_monetaire": "unite_principale", "sous_unite_source": None,
                "unite_quantite": unite, "brut": brut})
            mid["note"] = f"Excise Act s.3A et First Schedule, Part II : « {brut} »."
        elif mid.get("taux") == 0:
            # Montant nul quelle que soit l'assiette : CIF ne bloque pas la TVA.
            mid.update(assiette="CIF", assiette_origine="regle_de_pays")
            mid["note"] = "Excise Act s.3A et First Schedule, Part II : MID levy à 0."
        _compter_ligne(mid, compteurs, 1)
        for d in droits:
            if d.get("famille") == "tva" and d.get("assiette") == "CIF+DD+EXC":
                _compter_ligne(d, compteurs, -1)
                d.update(assiette="CIF+DD+EXC+MID", assiette_origine="regle_de_pays")
                d["note"] = (
                    "VAT Act 1998 s.13 : valeur en douane + droit de douane + accise + MID levy ; "
                    "les CO2 et energy levies ne sont pas collectés."
                )
                _compter_ligne(d, compteurs, 1)


#: Mauritanie : droits d'accises à l'importation (CGI, art. 263, rédaction de la loi
#: de finances rectificative 2025 ; produits pétroliers de l'art. 3.2.1 de la loi de
#: finances rectificative 2026). Fiche MRT_accises_2026-10-25.json.
#: Ad valorem : (positions, taux %, cumul spécifique en MRU par paquet de 20 ou None).
ACCISES_MRT = (
    (("2402100000", "2402200000"), 47.0, 1.6),
    (("2401", "2403"), 80.0, None),
    (("2203001000", "2203009000", "2206001000"), 225.0, None),
    (("2204210000", "2204220000", "2204291000", "2204299000", "2205100000", "2205900000", "2206009100",
      "2206009900"), 239.0, None),
    (("2204100000",), 259.0, None),
    (("2208201000", "2208209000", "2208300000", "2208400000", "2208500000", "2208600000"), 324.0, None),
    (("3923210000", "3923290000", "3923900000"), 35.0, None),
    (("2202991000", "2202999000", "2009"), 30.0, None),
    (("1704", "1806310000", "1806321000", "1806329000", "1806901000", "1905310000", "1905320000",
      "1905900000"), 20.0, None),
)
#: Spécifiques : (positions, MRU, unité de quantité).
ACCISES_MRT_SPECIFIQUES = (
    (("2710123000",), 1.33, "l"),
    (("2710124000", "2710125000"), 9.98, "l"),
    (("2710192100",), 6.52, "l"),
    (("2710191100",), 2.16, "l"),
    (("2710192400",), 0.71, "l"),
    (("2710192200", "2710192300"), 0.45, "l"),
    (("2710191200",), 1.86, "l"),
    (("2710193200", "2710193910", "2710193990"), 3.42, "l"),
    (("7108131000", "7108139000"), 100.0, "g"),
)
#: LFR 2026, art. 3.2.1 b) : produits exemptés de la RS ; DD de 10 % sur trois d'entre eux.
PETROLE_SANS_RS_MRT = ("2710124000", "2710125000", "2710192100", "2710191100", "2710192400")
PETROLE_DD_10_MRT = ("2710124000", "2710125000", "2710192100")


def _accises_mauritanie(positions, compteurs):
    """Mauritanie : droits d'accises (CGI, art. 263) et taxe de lutte contre le cancer
    (art. 266 bis), avant la TVA. Assiette des accises ad valorem (art. 262) : valeur en
    douane majorée des droits et taxes dus à l'entrée, TVA et accises exclues."""
    source = "CGI de Mauritanie, art. 263 (loi de finances rectificative 2025)"
    for code, position in positions.items():
        droits = position.setdefault("droits", [])
        if code in PETROLE_SANS_RS_MRT:
            for d in droits:
                if d.get("code") == "RS":
                    d["taux"] = 0.0
                    d["note"] = "Loi de finances rectificative 2026, art. 3.2.1 b) : exempté de la redevance statistique."
                if d.get("code") == "DD" and code in PETROLE_DD_10_MRT:
                    d["taux"] = 10.0
                    d["note"] = "Loi de finances rectificative 2026, art. 3.2.1 b) : droit de douane de 10 %."
        lignes = []
        if code.startswith("24"):
            lignes.append({"code": "TLC", "code_source": "TLC", "famille": famille("TLC"),
                           "libelle": "Taxe de recherche et de lutte contre le cancer", "taux": 10.0,
                           "specifique": None, "assiette": "CIF", "assiette_origine": "regle_de_pays",
                           "source": "CGI de Mauritanie, art. 266 bis (loi de finances rectificative 2025)",
                           "note": "10 % de la valeur en douane des produits du chapitre 24 importés."})
        base = {"code": "EXC", "code_source": "DA", "famille": famille("EXC"), "libelle": "Droits d'accises"}
        regle = next((r for r in ACCISES_MRT if code.startswith(r[0])), None)
        if regle:
            _, taux, paquet = regle
            assiette = "CIF+DD+RS+PC+TLC" if lignes else "CIF+DD+RS+PC"
            ligne = {**base, "taux": taux, "specifique": None, "assiette": assiette,
                     "assiette_origine": "regle_de_pays", "source": source,
                     "note": "Art. 262 : valeur en douane majorée des droits et taxes dus à l'entrée, hors TVA "
                             "et accises."}
            if paquet:
                brut = f"{taux:g} % + {paquet:g} Ouguiya le paquet de 20 cigarettes".replace(".", ",")
                ligne.update(cumulatif=True, expression_brute=brut, specifique={
                    "montant": paquet, "unite_monetaire": "unite_principale", "sous_unite_source": None,
                    "unite_quantite": "paquet de 20 cigarettes", "brut": brut})
            lignes.append(ligne)
        regle = next((r for r in ACCISES_MRT_SPECIFIQUES if code.startswith(r[0])), None)
        if regle:
            _, montant, unite = regle
            brut = f"{montant:g} MRU/{unite}".replace(".", ",")
            lignes.append({**base, "taux": None, "specifique": {
                "montant": montant, "unite_monetaire": "unite_principale", "sous_unite_source": None,
                "unite_quantite": unite, "brut": brut}, "assiette": "xQTE", "assiette_origine": "droit_specifique",
                "source": "Loi de finances rectificative 2026, art. 3.2.1 a)" if code in PETROLE_SANS_RS_MRT
                else source,
                "note": f"{brut} à l'importation."})
        rang = next((i for i, d in enumerate(droits) if d.get("famille") == "tva"), len(droits))
        for ligne in lignes:
            droits.insert(rang, ligne)
            rang += 1
            _compter_ligne(ligne, compteurs, 1)


def _regles_cedeao_hors_uemoa():
    """TVA_CEDEAO_HORS_UEMOA et PRELEVEMENTS_CEDEAO_HORS_UEMOA de
    backend/services/tax_profile_data.py, partagées avec l'ancien chemin."""
    if REPO not in sys.path:
        sys.path.insert(0, REPO)
    profils = importlib.import_module("backend.services.tax_profile_data")
    return profils.TVA_CEDEAO_HORS_UEMOA, profils.PRELEVEMENTS_CEDEAO_HORS_UEMOA


NOTE_PCC_GMB = (
    "Prélèvement communautaire CEDEAO : 0,5 % (protocole A/P1/7/96, art. 7) sur les importations hors CEDEAO. "
    "La FAQ douane de la GRA indique « ECOWAS Levy- 1% of CIF », sans texte trouvé."
)


def _prelevements_cedeao_hors_uemoa(iso, positions, compteurs):
    """Gambie, Liberia, Sierra Leone : les crawls recopient le tarif
    du Bénin (« réf. État membre BEN ») avec sa redevance statistique de 1 % et
    son assiette de TVA « CIF+DD+RS+PCS », béninoises. Aucun texte de ces pays
    ne les établit (fiche CEDEAO_hors_UEMOA_prelevements_2026-10-12.json) : la
    redevance est retirée, la TVA/GST prend l'assiette et le taux de la loi
    nationale, et les prélèvements nationaux connus sont ajoutés avec leur
    réserve en note. La TVA est liquidée en dernier."""
    regles_tva, prelevements = _regles_cedeao_hors_uemoa()
    taux_tva, note_tva = regles_tva[iso]
    for position in positions.values():
        droits = []
        for d in position.get("droits") or []:
            if d.get("code") == "RS":
                if d.get("assiette_origine") == "source":
                    compteurs["assiettes_source"] -= 1
                continue
            if d.get("code") == "TVA":
                if d.get("assiette_origine") == "source":
                    compteurs["assiettes_source"] -= 1
                    compteurs["assiettes_table"] += 1
                d["taux"] = taux_tva
                d["assiette"] = "CIF+TOUS_SAUF_TVA"
                d["assiette_origine"] = "regle_de_pays"
                d["source"] = "fiche CEDEAO_hors_UEMOA_prelevements_2026-10-12.json"
                d["note"] = note_tva
            elif d.get("code") == "PCC" and iso == "GMB":
                d["note"] = NOTE_PCC_GMB
            droits.append(d)
        for code, libelle, taux, note in prelevements.get(iso, []):
            d = _droit(code, libelle, taux, "CIF", "fiche CEDEAO_hors_UEMOA_prelevements_2026-10-12.json")
            d["assiette_origine"] = "regle_de_pays"
            d["note"] = note
            compteurs["assiettes_table"] += 1
            droits.append(d)
        position["droits"] = [d for d in droits if d.get("famille") != "tva"] + [
            d for d in droits if d.get("famille") == "tva"
        ]


def _sans_redevance_informatique_gnq(positions, compteurs):
    """Guinée équatoriale : pas de redevance informatique. Le fichier collecté
    recopie le tarif camerounais (« derived_from »: « CMR ») et sa redevance
    nationale ; aucune loi équato-guinéenne lue ne l'institue (Ley 10/2017 et
    Ley de Tasas 2025 ; fiche GNQ_redevance_informatique_2026-10-10.json)."""
    for position in positions.values():
        droits = position.get("droits") or []
        retenus = [d for d in droits if d.get("code") != "RI"]
        compteurs["assiettes_source"] -= len(droits) - len(retenus)
        position["droits"] = retenus


#: Libye : source et motif des deux compléments nationaux du crawl, servis
#: sans taux (fiche LBY_TSP_TP_taux_2026-10-10.json).
TSP_TP_LIBYE = {
    "TSP": (
        "Aucun texte libyen trouvé (fiche LBY_TSP_TP_taux_2026-10-10.json)",
        "Taxe des services portuaires à 4 % : aucun texte libyen trouvé ne l'établit. La page PwC d'où le "
        "crawl la tenait (revue le 31 mai 2026) ne cite plus ni « Port Services Tax » ni 4 % ; elle signale "
        "une « service fee » de 5 % sur la valeur de la plupart des importations, sans texte. La décision "
        "du Comité populaire général des Chaabiyat n° 3 de 2005 (« redevance pour services "
        "d'importation »), citée par la décision n° 17/2007, pourrait fonder un tel prélèvement ; son texte "
        "et son taux n'ont pas été obtenus. La redevance de quai souveraine du règlement de 2025 (décision "
        "du Conseil des ministres n° 393/2025, art. 25) est spécifique : 2,00 LYD par tonne ou par m³, le "
        "plus élevé des deux, minimum 50 LYD par bon de livraison.",
    ),
    "TP": (
        "Loi n° 19/1992 (Libye), art. 1 ; taux non établi (fiche LBY_TSP_TP_taux_2026-10-10.json)",
        "Taxe de production ou de consommation : instituée par la loi n° 19/1992 (art. 1) sur les "
        "marchandises importées désignées par décision, au taux fixé pour chacune ; maintien en vigueur non "
        "confirmé. La grille de 2002 (décision n° 6/2002) en désigne 40 catégories, à des taux non nuls de "
        "7 % à 50 % à l'importation, sans correspondance établie avec les positions du tarif ; elle a pu être "
        "modifiée en 2005 (décisions n° 103 et 114/2005, non obtenues). Aucun texte trouvé ne fixe le taux "
        "uniforme de 2 % du crawl.",
    ),
}


#: CAE (fiche CAE_TEC_TVA_tabac_2026-10-13.json). Quatre positions du TEC 2022
#: que la collecte ne porte pas, lues dans sa consolidation de juin 2025
#: (sources/TZA_tra_cet_eac_2022_maj_2025-06.pdf, page entre parenthèses).
#: La RDC n'y est pas : elle applique son tarif national (ordonnance-loi
#: n° 011-2012 du 21/09/2012), aucun acte n'appliquant le TEC n'ayant été trouvé.
PAYS_TEC_CAE = {"KEN", "RWA", "TZA", "UGA", "BDI", "SSD"}
TEC_CAE_COMPLEMENTS = {
    "53021000": (0.0, "p. 280"),
    "58110000": (25.0, "p. 302"),
    "92099200": (10.0, "p. 534"),
    "92099400": (10.0, "p. 534"),
}
#: TVA à l'importation sur la valeur et tous les droits et taxes sauf elle-même ;
#: la collecte n'y mettait que le droit de douane.
TVA_CAE = {
    "RWA": "Loi n° 049/2023 portant TVA (Rwanda), art. 16 (1) (d) : « the amount of customs duty, excise, "
    "port charges or other fiscal charges other than value added tax payable in respect of imported goods ». "
    "Réserve : l'assiette servie comprend la valeur en douane et les droits liquidés ici ; les frais portuaires et "
    "les services liés à l'importation (art. 16 (1) (c) et (d)), hors du calcul, n'y sont pas.",
    "TZA": "Value Added Tax Act 2014 (Tanzanie), s. 9 : valeur en douane, « (b) the amount of any customs duty "
    "payable on the import; and (c) the amount of any tax, levy, fee, or fiscal charge other than customs duty "
    "and value added tax payable on the import of the goods ». Réserve : l'assiette servie comprend la valeur en "
    "douane et les droits liquidés ici ; la Railway Development Levy, l'Industrial Development Levy et la "
    "Customs Processing Fee, non encore liquidées, n'y sont pas.",
}
#: Accise sur le tabac importé : (préfixes, taux, spécifique, note). taux et
#: spécifique tous deux None : le taux dépend d'une donnée que la position ne
#: porte pas. Une position absente du barème perd son accise (« retirer »).
TABAC_CAE = {
    "TZA": [
        (("24022010", "24022090"), None, ("72462.19", "mil"),
         "Finance Act 2026 (Tanzanie, Act No. 2/2026), art. 10 (a), Fourth Schedule du Cap. 147, en vigueur au "
         "1er juillet 2026 : cigarettes « Other » 72 462,19 TZS par millier ; les taux de 16 151,31 et "
         "38 154,80 TZS visent les cigarettes produites localement à plus de 75 % de tabac tanzanien. "
         "Quantité en milliers."),
        (("24031900", "24039100", "24039900"), None, ("36609.19", "kg"),
         "Finance Act 2026 (Tanzanie), art. 10 (a), Fourth Schedule : « Other/Imported » 36 609,19 TZS par kg."),
        (("24021000", "24029000", "24031100"), "retirer", None,
         "Finance Act 2026 (Tanzanie), art. 10 (a) : les positions 24.02 et 24.03 substituées au Fourth "
         "Schedule ne comprennent pas 2402.10, 2402.90 ni 2403.11."),
    ],
    "UGA": [
        (("24022010", "24022090"), None, None,
         "Excise Duty Act Cap. 336, Schedule 2, item 1 (a) et (b), remplacés par l'Excise Duty (Amendment) Act "
         "2025 (Act 14) : cigarettes importées 150 000 Ushs (« soft cap ») ou 200 000 Ushs (« hinge lid ») par "
         "1 000 ; le conditionnement n'est pas dans la position."),
        (("24021000", "24029000", "2403"), 200.0, None,
         "Excise Duty Act Cap. 336, Schedule 2, item 1 (c) à (f) : 200 % ; assiette s. 1 (8) : valeur en douane "
         "et droit d'importation."),
    ],
    "RWA": [
        (("24022010", "24022090", "24029000"), None, None,
         "Loi n° 011/2025 portant droit d'accise (Rwanda), annexe, n° 13 : « 36% of retail price tax inclusive "
         "of a pack of 20 rods plus Frw 230 per pack » ; art. 6 (1) (c). Le prix de détail n'est pas une "
         "donnée du calcul : accise non liquidée."),
        (("24021000",), 160.0, None, "Loi n° 011/2025 (Rwanda), annexe, n° 14 : cigares 160 %."),
    ],
}


def _cae(iso, positions, compteurs):
    """CAE : quatre positions du TEC, assiette de la TVA (RWA, TZA) et accise sur
    le tabac (RWA, TZA, UGA). Fiche CAE_TEC_TVA_tabac_2026-10-13.json."""
    for code, (taux, page) in TEC_CAE_COMPLEMENTS.items():
        for d in (positions.get(code) or {}).get("droits") or []:
            if d.get("code") == "DD" and d.get("taux") is None:
                d["taux"] = taux
                d["libelle"] = "Droit de douane (TEC CAE)"
                d["source"] = "TEC CAE 2022, consolidation de juin 2025 (TRA), " + page
                d.pop("note", None)
                compteurs["taux_indisponibles"] -= 1
    if iso in TVA_CAE:
        for position in positions.values():
            for d in position.get("droits") or []:
                if d.get("famille") == "tva" and d.get("assiette") and d["assiette"] != "CIF+TOUS_SAUF_TVA":
                    if d.get("assiette_origine") == "source":
                        compteurs["assiettes_source"] -= 1
                        compteurs["assiettes_table"] += 1
                    d["assiette"] = "CIF+TOUS_SAUF_TVA"
                    d["assiette_origine"] = "regle_de_pays"
                    d["note"] = TVA_CAE[iso]
    for code, position in positions.items():
        regle = next((r for r in TABAC_CAE.get(iso, []) if code.startswith(r[0])), None)
        if regle is None:
            continue
        _, taux, specifique, note = regle
        droits = position.get("droits") or []
        exc = next((d for d in droits if d.get("code") == "EXC"), None)
        if exc is not None:
            _compter_ligne(exc, compteurs, -1)
        if taux == "retirer":
            if exc is not None:
                droits.remove(exc)
            continue
        if exc is None:
            exc = {"code": "EXC", "code_source": "EXC", "famille": famille("EXC")}
            rang = next((i for i, d in enumerate(droits) if d.get("famille") == "tva"), len(droits))
            droits.insert(rang, exc)
        exc.update(libelle="Excise duty", taux=taux, source=note.split(" : ")[0], note=note)
        exc.pop("specifique", None)
        if specifique:
            montant, unite = specifique
            exc["specifique"] = {
                "montant": float(montant), "unite_monetaire": "unite_principale", "sous_unite_source": None,
                "unite_quantite": unite, "brut": f"{montant} TZS/{unite}",
            }
            exc["assiette"], exc["assiette_origine"] = "xQTE", "droit_specifique"
        elif taux is None:
            # Ni le prix de détail (RWA) ni le conditionnement (UGA) ne sont des
            # données du calcul : pas d'assiette à servir.
            exc["assiette"], exc["assiette_origine"] = None, None
        else:
            exc["assiette"], exc["assiette_origine"] = "CIF+DD", "regle_de_pays"
        _compter_ligne(exc, compteurs, 1)


#: Exceptions au TEC de l'exercice 2026/27 (Legal Notice EAC/160/2026), lues
#: dans la Gazette par scripts/extraire_mesures_tec_cae_2026.py.
MESURES_TEC_CAE = os.path.join(REPO, "data", "eac", "mesures_tec_cae_2026_27.json")
#: La Table X amende le TEC lui-même ; les autres le suspendent pour un pays :
#: elles passent après.
ORDRE_TABLES_CAE = ["X", "I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX"]


def _droit_mesure_cae(droit):
    """Champs d'une ligne DD pour le droit d'une mesure EAC/160/2026."""
    spec = droit.get("specifique")
    champs = {"taux": droit.get("taux"), "compose": None, "regle_composee": None, "expression_brute": None,
              "specifique": None, "assiette": "CIF", "assiette_origine": "regle_de_pays"}
    if spec:
        champs["specifique"] = {**spec, "brut": f"US$ {spec['montant']:g} / {spec['unite_quantite']}"}
        if droit.get("taux") is None:
            champs["assiette"], champs["assiette_origine"] = "xQTE", "droit_specifique"
        else:
            champs["compose"], champs["regle_composee"] = True, droit["regle"]
            champs["expression_brute"] = f"{droit['taux']:g}% or US$ {spec['montant']:g} / {spec['unite_quantite']} " \
                "whichever is higher"
    return champs


def _mesures_tec_cae(iso, positions, compteurs):
    """Droits de l'exercice 2026/27 à la place du TEC (EAC/160/2026). Une mesure
    conditionnelle (importateur, usage, sous-produit) ne change pas le droit :
    elle est rappelée en note."""
    with open(MESURES_TEC_CAE, encoding="utf-8") as f:
        mesures = json.load(f)["mesures"]
    mesures.sort(key=lambda m: ORDRE_TABLES_CAE.index(m["table"]))
    for mesure in mesures:
        prefixes = [c.replace(".", "") for c in mesure["positions"]]
        ref = f"Legal Notice EAC/160/2026, Table {mesure['table']}, n° {mesure['sn']} (p. {mesure['page']})"
        for decision in mesure["decisions"]:
            if iso not in (decision.get("pays") or [iso if mesure["table"] in ("VIII", "IX") else None]):
                continue
            exclus = {c.replace(".", "") for c in decision.get("exclusions", [])}
            applicable = decision.get("lu") and not decision.get("restriction")
            for code, position in positions.items():
                if not any(code.startswith(p) for p in prefixes) or any(code.startswith(x) for x in exclus):
                    continue
                dd = next((d for d in position.get("droits") or [] if d.get("code") == "DD"), None)
                if dd is None:
                    continue
                if not applicable:
                    note = f"Mesure conditionnelle, non appliquée ({ref}) : {decision['decision']}"
                    dd["note"] = (dd.get("note", "") + " " + note).strip()
                    continue
                _compter_ligne(dd, compteurs, -1)
                for cle, valeur in _droit_mesure_cae(decision["droit"]).items():
                    if valeur is None:
                        dd.pop(cle, None)
                    else:
                        dd[cle] = valeur
                dd["libelle"] = "Droit de douane (exercice 2026/27)"
                dd["source"] = ref
                dd["note"] = decision["decision"] if mesure["table"] not in ("III", "IV", "V", "VI", "VII") else (
                    f"{ref} : taux de l'en-tête de la table")
                if decision.get("exception"):
                    dd["note"] += f" — exception non appliquée par position : {decision['exception']}"
                _compter_ligne(dd, compteurs, 1)


#: Accises du tarif sud-africain (Schedule 1 Part 2A et 2B, SARS), lues par
#: scripts/extraire_accises_zaf.py. Fiche ZAF_accises_2026-10-14.json.
ACCISES_ZAF = os.path.join(REPO, "data", "zaf", "accises_sch1_part2.json")
#: Customs and Excise Act 1964, s.65(8)(a) : l'accise ad valorem d'un bien
#: importé porte sur la valeur transactionnelle majorée de 15 %, plus les droits
#: non remis de la Part 1 et de la Part 2A, sans l'accise ad valorem elle-même.
ASSIETTE_EXA_ZAF = "FOBx1.15+DD+EXS"
UNITES_ACCISE_ZAF = {"kg": "kg", "li": "li", "ml": "ml", "10cigarettes": "10 cigarettes", "10sticks": "10 sticks"}
#: Les autres États de la SACU appliquent les taux d'accise communs (accord
#: SACU 2002, art. 21 et 22), ceux du tarif sud-africain ; fiche
#: SACU_accises_BLNE_2026-10-20.json. Seule la valeur de l'accise ad valorem
#: relève de chaque loi nationale : (assiette, référence). Botswana : prix de
#: gros sur le marché botswanais, que le calcul ne connaît pas.
ASSIETTE_EXA_SACU = {
    "ZAF": (ASSIETTE_EXA_ZAF, "s.65(8)(a)"),
    "NAM": ("FOBx1.15+DD+EXS", "Customs and Excise Act 20/1998 (Namibie), s.75(9)(a)"),
    "SWZ": ("FOBx1.15+DD+EXS", "Customs and Excise Act 1971 (Eswatini), s.65(7)(a)"),
    "LSO": ("FOBx1.15+DD", "Customs and Excise Act 10/1982 (Lesotho), s.67(6)(a)"),
    "BWA": (None, "Excise Duty Act 2018 (Botswana), s.69(1)"),
}


def _accises_zaf(positions, compteurs, iso="ZAF"):
    """Afrique du Sud : accise spécifique (Part 2A, code EXS) et ad valorem
    (Part 2B, code EXA), dues à l'importation sur les biens de même nature que
    ceux fabriqués dans la République (Part 2, Section B, note 1). Mêmes taux
    pour les autres États de la SACU, sur la valeur de leur loi nationale."""
    assiette_exa, ref_valeur = ASSIETTE_EXA_SACU[iso]
    with open(ACCISES_ZAF, encoding="utf-8") as f:
        articles = json.load(f)["articles"]
    for article in articles:
        prefixe = article["sous_position"].replace(".", "")
        code_ligne = "EXS" if article["partie"] == "2A" else "EXA"
        source = (f"Customs and Excise Act 1964, Schedule No. 1 Part {article['partie']}, "
                  f"article {article['article']} ({article['sous_position']})")
        if iso != "ZAF":
            source = f"Taux commun SACU (accord SACU 2002, art. 21 et 22) : {source}"
        for code, position in positions.items():
            if not code.startswith(prefixe):
                continue
            droits = position.setdefault("droits", [])
            if any(d.get("code") == code_ligne for d in droits):
                continue
            ligne = {"code": code_ligne, "code_source": code_ligne, "famille": famille(code_ligne),
                     "libelle": "Specific excise duty" if code_ligne == "EXS" else "Ad valorem excise duty",
                     "taux": None, "specifique": None, "source": source, "note": article["brut"]}
            if article.get("unite") == "li aa":
                # Par litre d'alcool absolu : le titre alcoométrique n'est pas une
                # donnée du calcul.
                ligne["assiette"], ligne["assiette_origine"] = None, None
                ligne["note"] = (f"{article['brut']} : par litre d'alcool absolu ; le titre alcoométrique "
                                 "n'est pas une donnée du calcul, accise non liquidée.")
            elif article.get("unite"):
                ligne["specifique"] = {
                    "montant": article["montant"], "unite_monetaire": "unite_principale",
                    "sous_unite_source": None, "unite_quantite": UNITES_ACCISE_ZAF[article["unite"]],
                    "brut": article["brut"],
                }
                ligne["assiette"], ligne["assiette_origine"] = "xQTE", "droit_specifique"
            elif article.get("renvoi"):
                # Véhicules (articles 126.02 à 126.05) : taux de ((0,00003 × B) − 0,75) %,
                # plafonné à 30 %, B étant la valeur de la s.65(8)(a) : un taux qui
                # dépend de la valeur n'est pas servi.
                ligne["assiette"] = assiette_exa
                ligne["assiette_origine"] = "regle_de_pays" if assiette_exa else None
                ligne["note"] = ("Part 2B, note 2 (b) : taux de ((0,00003 × B) − 0,75) %, plafonné à 30 %, "
                                 f"B étant la valeur de la {ref_valeur} ; taux fonction de la valeur, non servi.")
            elif code_ligne == "EXA" and assiette_exa is None:
                ligne["taux"] = article["taux"]
                ligne["assiette"], ligne["assiette_origine"] = None, None
                ligne["note"] = (f"{article['brut']} sur la valeur de la {ref_valeur} : prix de gros sur le "
                                 "marché botswanais, inconnu du calcul ; accise non liquidée.")
            elif code_ligne == "EXA":
                ligne["taux"] = article["taux"]
                ligne["assiette"], ligne["assiette_origine"] = assiette_exa, "regle_de_pays"
            else:
                ligne["taux"] = article["taux"]  # « free » de la Part 2A
                ligne["assiette"], ligne["assiette_origine"] = "FOB", "regle_de_pays"
            rang = next((i for i, d in enumerate(droits) if d.get("famille") == "tva"), len(droits))
            droits.insert(rang, ligne)
            _compter_ligne(ligne, compteurs, 1)


#: Prélèvements du tarif sud-africain (Schedule 1 Parts 3A, 3C, 3D, 3E, 5A, 5B
#: et 7A), lus par scripts/extraire_prelevements_zaf.py. Fiche
#: ZAF_prelevements_2026-10-14.json.
PRELEVEMENTS_ZAF = os.path.join(REPO, "data", "zaf", "prelevements_sch1_parts3_5_7.json")
CODES_PRELEVEMENTS_ZAF = {
    "3A": ("EVB", "Environmental levy (plastic bags)"),
    "3C": ("EVL", "Environmental levy (electric filament lamps)"),
    "3D": ("EVC", "Environmental levy (CO2 emissions of motor vehicles)"),
    "3E": ("EVT", "Environmental levy (tyres)"),
    "5A": ("FLV", "Fuel levy"),
    "5B": ("RAF", "Road Accident Fund levy"),
    "7A": ("HPL", "Health promotion levy (sugary beverages)"),
}
#: Part 7A, note 5 (b) : sans rapport d'essai, une boisson sucrée est réputée
#: contenir 20 g de sucre pour 100 ml.
SUCRE_REPUTE_ZAF = 20
UNITES_PRELEVEMENT_ZAF = {"li": "li", "bag": "sac", "kg": "kg", "lamp": "lampe"}

#: Afrique du Sud : liste SARS des marchandises prohibées ou réglementées du
#: 23/10/2026 (feuilles « Imports » et « Exports ») et avis des 19 et 22/10/2026 ;
#: fiche ZAF_controles_sars_2026-10-26.json. Formalités et contrôles, sans effet
#: sur les droits. 9505.10 est sortie du contrôle de Port Health le 22/10/2026.
SOURCE_SARS_ZAF = "SARS — Prohibited and Restricted Imports and Exports list, 23 October 2026"
PHO_PEINTURE_ZAF = (
    "PHYSICAL_INSPECTION_PORT_HEALTH",
    "The product must be detained for physical inspection and monitoring by Port Health (BMA) to ensure "
    "compliance with the Regulations Relating to Lead in Paint or Coating Materials",
    "Hazardous Substances Act No. 15 of 1973",
    "Retenue pour inspection physique et suivi par Port Health (BMA) : conformité au règlement sur le plomb "
    "dans les peintures et revêtements. La mainlevée dépend de ce contrôle.",
)
PHO_SUBSTANCES_ZAF = (
    "PHYSICAL_INSPECTION_PORT_HEALTH",
    "The product must be detained for physical inspection and sampling by Port Health (BMA) to ensure "
    "compliance with the regulations.",
    "Hazardous Substances Act No. 15 of 1973",
    "Retenue pour inspection physique et prélèvement par Port Health (BMA) : conformité au Hazardous "
    "Substances Act. La mainlevée dépend de ce contrôle.",
)
NRCS_ZAF = (
    "NRCS_LETTER_OF_AUTHORITY",
    "LOA required from NRCS",
    "NRCS Act No 5 of 2008",
    "Lettre d'autorisation (LOA) du NRCS.",
)
CONTROLES_IMPORT_ZAF = {
    "950590": (PHO_PEINTURE_ZAF,),
    "95030010": (NRCS_ZAF, PHO_PEINTURE_ZAF),
    "95030090": (NRCS_ZAF, PHO_PEINTURE_ZAF),
    "290124": (PHO_SUBSTANCES_ZAF,),
    "290220": (PHO_SUBSTANCES_ZAF,),
    "290230": (
        ("ITAC_IMPORT_PERMIT", "Import permit required from ITAC",
         "International Trade Administration Act, 2002 (Act 71 of 2002)", "Permis d'importation de l'ITAC."),
        PHO_SUBSTANCES_ZAF,
    ),
}
ITAC_EXPORT_ZAF = (
    "ITAC_EXPORT_PERMIT",
    "Export permit required from ITAC",
    "International Trade Administration Act (Act 71 of 2002)",
    "Permis d'exportation de l'ITAC (marchandise retenue pour l'ITAC).",
)
CONTROLES_EXPORT_ZAF = {
    "253090": (ITAC_EXPORT_ZAF,),
    "290230": (
        ("SAPS_RECOMMENDATION",
         "Lodge application to Controlling Authority for recommendation before submitting application to ITAC: "
         "Controlling Authority : South African Police Service",
         "International Trade Administration Act (Act 71 of 2002)",
         "Recommandation du South African Police Service avant la demande de permis à l'ITAC."),
        ITAC_EXPORT_ZAF,
    ),
}
#: Avis SARS du 22/10/2026 : exclusion d'un produit que le code SH seul ne distingue pas.
EXCLUSIONS_EXPORT_ZAF = {
    "253090": {
        "produit": "Pyrophyllite",
        "verbatim": "Tariff subheading 2530.90 is subject to ITAC export control measures. However, the product "
                    "Pyrophyllite is excluded from these measures and should therefore be exempted from tariff "
                    "subheading 2530.90.",
        "source": "SARS — Updated Prohibited and Restricted Imports and Exports list, 22 October 2026",
        "note": "Le code 2530.90 ne suffit pas : la pyrophyllite en est exclue, à vérifier sur la désignation de la "
                "marchandise.",
    },
}


def _controles_sars_zaf(positions):
    def formalite(regle):
        code, verbatim, base, fr = regle
        return {"code": code, "texte": verbatim, "document_fr": fr, "document_en": verbatim,
                "base_legale": base, "source": SOURCE_SARS_ZAF}

    for code, regles in CONTROLES_IMPORT_ZAF.items():
        if code in positions:
            positions[code].setdefault("formalites", []).extend(formalite(r) for r in regles)
    for code, regles in CONTROLES_EXPORT_ZAF.items():
        if code in positions:
            controles = [formalite(r) for r in regles]
            if code in EXCLUSIONS_EXPORT_ZAF:
                for c in controles:
                    c["exclusion_produit"] = EXCLUSIONS_EXPORT_ZAF[code]
            positions[code]["formalites_export"] = controles


#: La liste SARS entière, mesures par ligne tarifaire, lue par
#: scripts/extraire_liste_sars_zaf.py ; fiche ZAF_liste_sars_2026-10-26.json.
LISTE_SARS_ZAF = os.path.join(REPO, "data", "zaf", "liste_sars_pr_2026-10-23.json")


def _liste_sars_zaf(positions):
    """Une ligne de la liste vaut pour les positions qu'elle couvre (son code en
    est le préfixe) ; plus fine que la position du socle, elle n'en couvre qu'une
    partie, dite par `portee_partielle` et le code SARS. Les lignes des contrôles
    déjà rédigés (CONTROLES_IMPORT_ZAF, CONTROLES_EXPORT_ZAF) ne sont pas reprises."""
    with open(LISTE_SARS_ZAF, encoding="utf-8") as f:
        liste = json.load(f)
    par_sh4 = {}
    for code in positions:
        par_sh4.setdefault(code[:4], []).append(code)
    deja = {"import": set(CONTROLES_IMPORT_ZAF), "export": set(CONTROLES_EXPORT_ZAF)}
    for ligne in liste["lignes"]:
        sens, chiffres = ligne["sens"], ligne["chiffres"]
        if chiffres in deja[sens]:
            continue
        mesure = " ".join(
            texte for texte in (
                ligne["restriction"],
                f"Action: {ligne['action']}." if ligne["action"] else None,
                f"Documents: {ligne['documents']}." if ligne["documents"] else None,
            ) if texte
        )
        champ = "formalites" if sens == "import" else "formalites_export"
        for code in par_sh4.get(chiffres[:4], ()):
            if not (code.startswith(chiffres) or chiffres.startswith(code)):
                continue
            positions[code].setdefault(champ, []).append({
                "code": f"SARS_PR {ligne['code_sars']}",
                "texte": mesure,
                "document_fr": mesure,
                "document_en": mesure,
                "issuing_authority": ligne["autorite"],
                "base_legale": ligne["autorite"],
                "code_sars": ligne["code_sars"],
                "portee_partielle": len(chiffres) > len(code),
                "source": liste["source"],
            })


def _prelevements_zaf(positions, compteurs):
    """Afrique du Sud : prélèvements environnementaux, taxe sur les carburants,
    Road Accident Fund levy et Health Promotion Levy, dus à l'importation en
    plus des droits des Parts 1 et 2."""
    with open(PRELEVEMENTS_ZAF, encoding="utf-8") as f:
        articles = json.load(f)["articles"]
    for article in articles:
        code_ligne, libelle = CODES_PRELEVEMENTS_ZAF[article["partie"]]
        prefixe = article["sous_position"].replace(".", "")
        source = (f"Customs and Excise Act 1964, Schedule No. 1 Part {article['partie']}, "
                  f"article {article['article']} ({article['sous_position']})")
        for code, position in positions.items():
            if not code.startswith(prefixe):
                continue
            droits = position.setdefault("droits", [])
            if any(d.get("code") == code_ligne for d in droits):
                continue
            ligne = {"code": code_ligne, "code_source": code_ligne, "famille": famille(code_ligne),
                     "libelle": libelle, "taux": None, "specifique": None, "assiette": None,
                     "assiette_origine": None, "source": source, "note": article["brut"]}
            montant, unite = article.get("montant"), article.get("unite")
            if article["partie"] == "3E" and not prefixe.startswith("40"):
                # Pneus montés sur un véhicule ou une roue : le prélèvement porte sur
                # la masse nette des pneus (note 3), qui n'est pas une donnée du calcul.
                montant = None
                ligne["note"] = (f"{article['brut']} sur la masse nette des pneus montés (Part 3E, note 3) ; "
                                 "masse des pneus non connue du calcul, prélèvement non liquidé.")
            elif article.get("par_g_km_co2"):
                ligne["note"] = (f"{article['brut']} : émissions de CO2 du rapport d'essai ou, à défaut, "
                                 "de la cylindrée (Part 3D, note 5) ; non connues du calcul, prélèvement "
                                 "non liquidé.")
            elif article.get("par_gramme_de_sucre"):
                if prefixe.startswith("2202"):
                    # Boisson prête à boire : teneur réputée de la note 5 (b), par litre.
                    montant = round((SUCRE_REPUTE_ZAF - article["seuil_g_100ml"])
                                    * article["par_gramme_de_sucre"] * 10, 6)
                    unite = "li"
                    ligne["note"] = (f"{article['brut']} ; teneur réputée de 20 g/100 ml faute de rapport "
                                     "d'essai (Part 7A, note 5 (b)) : 16 g × 2,21 c par 100 ml, soit "
                                     f"{montant:g} R par litre. Un rapport d'essai accrédité peut la réduire.")
                else:
                    ligne["note"] = (f"{article['brut']} : préparation à diluer, teneur calculée sur la "
                                     "boisson reconstituée (Part 7A, note 6) ; volume non connu du calcul, "
                                     "prélèvement non liquidé.")
            if article.get("taux") is not None:
                ligne["taux"], ligne["assiette"], ligne["assiette_origine"] = article["taux"], "FOB", "regle_de_pays"
            elif montant is not None:
                ligne["specifique"] = {
                    "montant": montant, "unite_monetaire": "unite_principale", "sous_unite_source": None,
                    "unite_quantite": UNITES_PRELEVEMENT_ZAF[unite], "brut": article["brut"],
                }
                ligne["assiette"], ligne["assiette_origine"] = "xQTE", "droit_specifique"
            rang = next((i for i, d in enumerate(droits) if d.get("famille") == "tva"), len(droits))
            droits.insert(rang, ligne)
            _compter_ligne(ligne, compteurs, 1)


#: Prélèvements nationaux dus à l'importation au Botswana et en
#: Eswatini, dont le taux en vigueur n'est pas collecté (fiche
#: SACU_accises_BLNE_2026-10-20.json) : la ligne est servie sans taux, le total
#: est incomplet plutôt que présenté comme complet. Fuel levy et prélèvement
#: environnemental : Parts 5 et 3 de la Schedule 1 nationale, même structure
#: que le tarif sud-africain (accord SACU art. 22), dont les positions sont
#: reprises. Namibie : voir PRELEVEMENTS_NAM. Lesotho : prélèvement sur le tabac
#: et l'alcool, voir TAPL_LESOTHO.
#: Botswana, alcool : fiche BWA_prelevement_alcool_2026-10-23.json.
#: (code, libellé, parties sud-africaines ou sous-positions, assiette, source, note)
PRELEVEMENTS_SACU_NON_COLLECTES = {
    "BWA": [
        ("FLV", "Fuel levy", {"5A"}, None,
         "Excise Duty Act 2018 (Botswana), s.2 : « fuel levy » (Schedule No. 1 Part 5)", ""),
        ("ALV", "Levy on intoxicating liquor",
         ("19019020", "2203", "2204", "2205", "2206", "2207", "2208"),
         "CIF+DD",
         "Control of Goods (Intoxicating Liquor (Levy)) Regulations 2008 (Botswana), règl. 2(b), 3(b) et annexe",
         "30 % au texte de 2008 (S.I. 91 et 111 de 2008), modifié depuis ; "),
    ],
    "SWZ": [
        ("ATL", "Alcohol and Tobacco Levy",
         ("2203", "2204", "2205", "2206", "2208", "2402", "240311", "240319", "240399"),
         "FOB+DD+EXS+EXA",
         "Alcohol and Tobacco Levy Act 2019 (Eswatini), s.3(1)(b), s.4(2) et annexe, item 1",
         "7 % à l'annexe de la loi de 2019 (boissons alcoolisées hors bière traditionnelle, cigares, "
         "cigarettes, tabac à pipe et à priser) ; "),
    ],
}


#: Positions du périmètre que le texte exclut. Eswatini : l'annexe de la loi de
#: 2019 (item 1(a)) vise « alcoholic beverages of all kinds other than
#: traditional beer » ; le tarif isole la bière traditionnelle africaine en
#: 2203.00.05 et 2206.00.15.
EXCLUSIONS_PRELEVEMENTS_SACU = {
    ("SWZ", "ATL"): ("22030005", "22060015"),
}


def _prelevements_sacu_non_collectes(iso, positions, compteurs):
    """Botswana, Namibie, Eswatini : prélèvements nationaux à l'importation
    déclarés sans taux sur leurs positions, faute de barème en vigueur."""
    with open(PRELEVEMENTS_ZAF, encoding="utf-8") as f:
        articles = json.load(f)["articles"]
    for code_ligne, libelle, perimetre, assiette, source, note in PRELEVEMENTS_SACU_NON_COLLECTES[iso]:
        if isinstance(perimetre, set):
            prefixes = tuple(a["sous_position"].replace(".", "") for a in articles if a["partie"] in perimetre)
        else:
            prefixes = perimetre
        exclues = EXCLUSIONS_PRELEVEMENTS_SACU.get((iso, code_ligne), ())
        for code, position in positions.items():
            if not code.startswith(prefixes) or code in exclues:
                continue
            droits = position.setdefault("droits", [])
            if any(d.get("code") == code_ligne for d in droits):
                continue
            ligne = {"code": code_ligne, "code_source": code_ligne, "famille": famille(code_ligne),
                     "libelle": libelle, "taux": None, "specifique": None, "assiette": assiette,
                     "assiette_origine": "regle_de_pays" if assiette else None, "source": source,
                     "note": note + "taux en vigueur non collecté : prélèvement dû à l'importation, "
                                    "non liquidé, total incomplet."}
            rang = next((i for i, d in enumerate(droits) if d.get("famille") == "tva"), len(droits))
            droits.insert(rang, ligne)
            _compter_ligne(ligne, compteurs, 1)


#: Namibie : fuel levy (Part 5A) et prélèvements environnementaux (Part 3) de la
#: Schedule No. 1 nationale, lus par scripts/extraire_prelevements_nam.py dans
#: les Gazettes (GN 100/2016, GN 225/2019, GN 226/2019, GN 131/2020). Fiche
#: NAM_prelevements_2026-10-25.json.
PRELEVEMENTS_NAM = os.path.join(REPO, "data", "nam", "prelevements_sch1_parts3_5.json")
LIBELLES_PRELEVEMENTS_NAM = {
    "5A": ("FLV", "Fuel levy"),
    "3A": ("EVN", "Environmental levy (electric filament lamps, tyres)"),
    "3B": ("EVN", "Environmental levy (CO2 emissions of motor vehicles)"),
    "3C": ("EVN", "Environmental levy (road wheels fitted with tyres)"),
    "3D": ("EVN", "Environmental levy (lubricant oils, plastic bags, batteries)"),
}
UNITES_PRELEVEMENT_NAM = {"li": "li", "bag": "sac", "lamp": "lampe", "tyre": "pneu"}
#: Les textes de 2019 nomment la série 2710.12.xx ; le tarif servi la dédouble
#: en 2710.19.xx, sous les mêmes définitions (« as defined in Additional Note 1 »),
#: et le tarif sud-africain y porte sa propre fuel levy : le prélèvement suit.
#: « 2710.19 Other » de la Section D, résiduel en 2019, couvrirait aujourd'hui
#: les carburants de cette série dédoublée : il n'est pas repris. Les pneus
#: rechapés ou usagés excluent les chapes et flaps de 4012.90 (Section B, note 6).
SERIE_DEDOUBLEE_NAM = ("2710.12.", "2710.19.")
EXCLUSIONS_PRELEVEMENTS_NAM = {("3D", "2710.19"): (), ("3A", "4012"): ("401290",)}


def _prelevements_nam(positions, compteurs):
    """Namibie : fuel levy et prélèvements environnementaux dus à l'importation."""
    with open(PRELEVEMENTS_NAM, encoding="utf-8") as f:
        articles = json.load(f)["articles"]
    for article in articles:
        cle = (article["partie"], article["sous_position"])
        if cle in EXCLUSIONS_PRELEVEMENTS_NAM and not EXCLUSIONS_PRELEVEMENTS_NAM[cle]:
            continue
        exclues = EXCLUSIONS_PRELEVEMENTS_NAM.get(cle, ())
        code_ligne, libelle = LIBELLES_PRELEVEMENTS_NAM[article["partie"]]
        prefixes = [article["sous_position"]]
        if article["sous_position"].startswith(SERIE_DEDOUBLEE_NAM[0]):
            prefixes.append(article["sous_position"].replace(*SERIE_DEDOUBLEE_NAM))
        prefixes = tuple(p.replace(".", "") for p in prefixes)
        source = (f"Customs and Excise Act 20/1998 (Namibie), Schedule No. 1 Part "
                  f"{article['partie'][0]}{'' if article['partie'] == '5A' else ' Section ' + article['partie'][1]}, "
                  f"{article['sous_position']} ({article['source']}, p. {article['page']})")
        for code, position in positions.items():
            if not code.startswith(prefixes) or code.startswith(exclues):
                continue
            droits = position.setdefault("droits", [])
            if any(d.get("code") == code_ligne for d in droits):
                continue
            ligne = {"code": code_ligne, "code_source": code_ligne, "famille": famille(code_ligne),
                     "libelle": libelle, "taux": None, "specifique": None, "assiette": None,
                     "assiette_origine": None, "source": source, "note": article["brut"]}
            if article.get("par_g_km_co2"):
                ligne["note"] = (f"{article['brut']} : émissions de CO2 du certificat du constructeur ou, à "
                                 "défaut, de la cylindrée (Section B, note 5) ; non connues du calcul, "
                                 "prélèvement non liquidé. Prélèvement unique (note 9).")
            elif article.get("taux") is not None:
                ligne["taux"] = article["taux"]
                ligne["note"] = (f"{article['brut']} : la valeur sur laquelle porte ce taux n'est pas définie par "
                                 "la Section D ; assiette non établie, prélèvement non liquidé.")
            elif article.get("montant") == 0:
                ligne["taux"], ligne["assiette"], ligne["assiette_origine"] = 0.0, "FOB", "regle_de_pays"
            else:
                ligne["specifique"] = {
                    "montant": article["montant"], "unite_monetaire": "unite_principale",
                    "sous_unite_source": None, "unite_quantite": UNITES_PRELEVEMENT_NAM[article["unite"]],
                    "brut": article["brut"],
                }
                ligne["assiette"], ligne["assiette_origine"] = "xQTE", "droit_specifique"
            rang = next((i for i, d in enumerate(droits) if d.get("famille") == "tva"), len(droits))
            droits.insert(rang, ligne)
            _compter_ligne(ligne, compteurs, 1)


#: Lesotho : Tobacco and Alcoholic Products Levy Act 2023 (Act 1/2023, en vigueur
#: le 01/03/2023 par la LN 22/2023), barème de la LN 58/2025 au 01/04/2025
#: (fiche LSO_prelevement_tabac_alcool_2026-10-25.json). « Alcoholic products »
#: (s.2) exclut la bière traditionnelle, isolée en 2203.00.05 et 2206.00.15 ;
#: l'éthanol (22.07) et les produits à inhaler (24.04) sont laissés hors du
#: périmètre. (positions, taux %, positions exclues)
TAPL_LESOTHO = (
    (("2203", "2204", "2205", "2206", "2208"), 10.0, ("22030005", "22060015")),
    (("2401", "2402", "2403"), 20.0, ()),
)


def _prelevement_tapl_lesotho(positions, compteurs):
    """Lesotho : prélèvement sur les produits du tabac et les boissons
    alcoolisées importés, sur la valeur en douane, les services accessoires
    (transport, assurance) et les droits hors TVA (s.7(2))."""
    for prefixes, taux, exclues in TAPL_LESOTHO:
        for code, position in positions.items():
            if not code.startswith(prefixes) or code in exclues:
                continue
            droits = position.setdefault("droits", [])
            ligne = {"code": "TAPL", "code_source": "TAPL", "famille": famille("TAPL"),
                     "libelle": "Tobacco and Alcoholic Products Levy", "taux": taux, "specifique": None,
                     "assiette": "CIF+DD+EXS+EXA", "assiette_origine": "regle_de_pays",
                     "source": "Tobacco and Alcoholic Products Levy Act 2023 (Lesotho), s.6 et s.7(2) ; "
                               "barème : LN 58/2025, en vigueur le 01/04/2025",
                     "note": "Valeur imposable : valeur en douane, droits et charges fiscales hors TVA, "
                             "transport et assurance (s.7(2)). Comprise dans l'assiette de la TVA."}
            rang = next((i for i, d in enumerate(droits) if d.get("famille") == "tva"), len(droits))
            droits.insert(rang, ligne)
            _compter_ligne(ligne, compteurs, 1)


#: Sierra Leone : accise à l'importation (Excise Act 1982, s.5(b) dans la
#: rédaction du Finance Act 2025), First Schedule telle que la modifient les
#: Finance Acts 2021, 2024 et 2026 (fiche SLE_accises_2026-10-25.json). Montants
#: en leones. Liquidées : (positions, montant, unité de quantité, barème, source).
ACCISES_SLE = (
    (("2203001000", "2203009000"), 15.0, "li", "Le15 per litre (import, alcoholic content <10%)",
     "Finance Act 2024, s.4(a) (heading 2203)"),
    (("2401",), 98.0, "kg", "NLe98 per kg", "Finance Act 2026, s.3(a) (item 24.01)"),
    (("2402100000",), 38.0, "paquet", "NLe38 per packet", "Finance Act 2026, s.3(a) (item 24.02)"),
    (("2402200000",), 3.0, "paquet de 20 cigarettes", "NLe3 per packet of 20 sticks",
     "Finance Act 2026, s.3(a) (item 24.02)"),
    (("2403190000", "2403910000", "2403991000", "2403999000"), 98.0, "kg", "NLe98 per kg",
     "Finance Act 2026, s.3(a) (item 24.03)"),
    (("2523",), 0.2, "kg", "NLe 10.0 per 50kg", "Finance Act 2026, s.3(b) (item 25.23)"),
    (("2710191200",), 2.0, "li", "Kerosene NLe2.0 per litre", "Finance Act 2026, s.3(c) (item 27.10 A)"),
    (("2710124000", "2710125000"), 5.0, "li", "Petrol NLe5.0 per litre", "Finance Act 2026, s.3(c) (item 27.10 B)"),
    (("2710192100",), 5.0, "li", "Diesel NLe5.0 per litre", "Finance Act 2026, s.3(c) (item 27.10 C)"),
    (("2710192200", "2710192300", "2710192400", "2710192500"), 7.4, "li", "Fuel oil NLe7.40 per litre",
     "Finance Act 2026, s.3(c) (item 27.10 D)"),
    (("2710193100", "2710193200", "2710193910", "2710193990"), 4.0, "li", "Lubricating oils NLe4.00 per litre",
     "Finance Act 2026, s.3(c) (item 27.10 E)"),
    (("3923210000", "3923290000"), 16.0, "kg", "Polyethene (plastic) bags Le16.0 per kg",
     "Finance Act 2024, s.4(l) (item 39.23 A)"),
)
#: Déclarées sans liquidation : (positions, taux ad valorem ou None, source, motif).
ALCOOL_SLE = ("taux à l'importation selon le titre alcoométrique : Le10 (<10 %), Le12 (>10 à 20 %), Le14 (20 à "
              "30 %), Le16 (30 à 40 %), Le22 (>40 %) par litre ; titre non connu du calcul, accise non liquidée.")
VALEUR_SLE = ("valeur imposable de l'accise ad valorem à l'importation non établie (texte de l'Excise Act 1982 "
              "non obtenu) ; accise non liquidée.")
ACCISES_SLE_NON_LIQUIDEES = (
    (("2204", "2205", "2208", "2206001000", "2206009900"), None,
     "Finance Act 2024, s.4(b) à (e) (headings 2204, 2205, 2206, 2208)", ALCOOL_SLE),
    (("2207",), None, "Finance Act 2024, s.4(f) (heading 2207)",
     "Extra neutral alcohol (>= 95 %) : Le22 par litre à l'importation ; importé comme matière première, "
     "l'accise est payée sur la vente du produit fini. Titre et usage non connus du calcul, accise non liquidée."),
    (("2202100000", "2202991000", "2202999000", "2009"), None, "Finance Act 2024, s.4(h) (heading 20.09)",
     "Boissons non alcoolisées et jus additionnés de sucre : Le0.03 par gramme de sucre à partir de 10 g par "
     "litre, 0 en dessous ; teneur en sucre ajouté non connue du calcul, accise non liquidée."),
    (("2402900000",), None, "Finance Act 2026, s.3(a) (item 24.02)",
     "Cigares (NLe38 par paquet) ou cigarettes (NLe3 par paquet de 20) en succédanés de tabac : la position "
     "ne dit pas lequel, accise non liquidée."),
    (("2403110000",), None, "Finance Act 2026, s.3(a) (item 24.03)",
     "Shisha : NLe98 par kg et NLe225 par litre ; deux quantités, le calcul n'en reçoit qu'une, accise non "
     "liquidée."),
    (("151190", "151710"), 10.0, "Finance Act 2021, s.4(a) (items 15.11, 15.17)", VALEUR_SLE),
    (("340111", "340119", "340120", "291560", "291570", "382311"), 20.0,
     "Finance Act 2021, s.4(b) (items 34.01, 29.15, 38.23)", VALEUR_SLE),
    (("7317001000",), 5.0, "Finance Act 2021, s.4(d) (item 73.17)", VALEUR_SLE),
)


def _accises_sierra_leone(positions, compteurs):
    """Sierra Leone : accise due à l'importation, avant la GST qui l'inclut
    (GST Act 2009, s.26(1)(c))."""
    def inserer(droits, ligne):
        rang = next((i for i, d in enumerate(droits) if d.get("famille") == "tva"), len(droits))
        droits.insert(rang, ligne)
        _compter_ligne(ligne, compteurs, 1)

    base = {"code": "EXC", "code_source": "EXC", "famille": famille("EXC"), "libelle": "Excise duty"}
    for code, position in positions.items():
        droits = position.setdefault("droits", [])
        for prefixes, montant, unite, brut, source in ACCISES_SLE:
            if code.startswith(prefixes):
                inserer(droits, {**base, "taux": None, "specifique": {
                    "montant": montant, "unite_monetaire": "unite_principale", "sous_unite_source": None,
                    "unite_quantite": unite, "brut": brut}, "assiette": "xQTE",
                    "assiette_origine": "droit_specifique", "source": f"Excise Act 1982, First Schedule ; {source}",
                    "note": brut})
                break
        else:
            for prefixes, taux, source, note in ACCISES_SLE_NON_LIQUIDEES:
                if code.startswith(prefixes):
                    inserer(droits, {**base, "taux": taux, "specifique": None, "assiette": None,
                                     "assiette_origine": None, "source": f"Excise Act 1982, First Schedule ; {source}",
                                     "note": note})
                    break


def _compter_ligne(d, compteurs, signe):
    if d.get("taux") is None and not d.get("specifique"):
        compteurs["taux_indisponibles"] += signe
    if d.get("taux") is None and d.get("specifique"):
        compteurs["droits_specifiques"] += signe
    if not d.get("assiette"):
        cle = "assiettes_indisponibles"
    elif d.get("assiette_origine") == "source":
        cle = "assiettes_source"
    else:
        cle = "assiettes_table"
    compteurs[cle] += signe


#: Égypte (fiche EGY_TVA_taxe_de_table_2026-10-14.json). Les assiettes de la TVA
#: et de la Taxe de Table sont dans assiettes_pays.json (loi 67/2016, art. 10 et
#: 39) ; restent ici l'ordre des lignes, les tabacs du tableau, partie I, la
#: Taxe de Table des alcools et des cigarettes, que la collecte ne chiffre pas,
#: l'assiette des redevances publiées sans elle, et les montants que la douane
#: publie en EGP au kilo ou au litre.
TAXE_DE_TABLE_EGY = "ضريبةالجدول"
MINIMUMS_EGY = {"ضريبةالجدول2", "VAT2"}
#: Droit de douane au kilo net (tabacs) : « 150 جنية لكل كيلو جرام صافى ».
DD_AU_KILO_EGY = re.compile(r"^([\d.]+) جنية لكل كيلو جرام صافى$")
#: Minimum de la Taxe de Table, publié sur la ligne qui la suit : « بحد ادنى 50
#: جنية لكل كج مصنع صافى », « بحد ادنى 15 جنية لكل لتر سائل ».
MINIMUM_EGY = re.compile(r"^بحد ادنى ([\d.]+) جنية لكل (كيلو جرام صافى|كج مصنع صافى|لتر سائل)$")
UNITES_EGY = {"كيلو جرام صافى": "kg", "كج مصنع صافى": "kg", "لتر سائل": "l"}
TABAC_TAXE_DE_TABLE_EGY = (
    "Loi n° 67/2016, tableau annexé, partie I (« سلع وخدمات تخضع لضريبة الجدول فقط ») : les tabacs sont "
    "soumis à la seule Taxe de Table, que la douane publie sous « TVA ». Assiette de l'art. 39 (b)."
)
#: Alcools : la douane impose la Taxe de Table (instruction ر7065 « تفرض ضريبة
#: الجدول علي الكحول ») sans en publier le taux. Taux du tableau de 2016, appliqués
#: sur décision avec leur réserve : préfixe -> (taux %, minimum EGP/l, item).
INSTRUCTION_ALCOOLS_EGY = "ر7065"
TAXE_DE_TABLE_ALCOOLS_EGY = {
    "2203": (250.0, 5.0, "item 4, bière alcoolisée : 250 % avec un minimum de 500 EGP par hectolitre (5 EGP/l)"),
    "2204": (150.0, 15.0, "item 3 (c), vins et boissons fermentées : 150 % avec un minimum de 15 EGP par litre"),
    "2205": (150.0, 15.0, "item 3 (c), vins et boissons fermentées : 150 % avec un minimum de 15 EGP par litre"),
    "2206": (150.0, 15.0, "item 3 (c), vins et boissons fermentées : 150 % avec un minimum de 15 EGP par litre"),
    "2208": (150.0, 15.0, "item 3 (d), spiritueux : 150 % avec un minimum de 15 EGP par litre"),
}
RESERVE_ALCOOLS_EGY = (
    "Instruction ر7065 de la douane : Taxe de Table due, taux non publié. Loi n° 67/2016, tableau annexé, "
    "partie II, {item}. Taux de 2016 appliqué sur décision, sous réserve d'une modification ultérieure du "
    "tableau ; le minimum se liquide sur la quantité en litres."
)
#: Redevances publiées en % sans assiette, qu'aucun texte lu ne fixe.
REDEVANCES_EGY = {
    "رسممحصلةلحسابغرفةنسيج",
    "رسممحصلةلحسابغرفةجلود",
    "رسممحصلةلحسابغرفةدخان",
    "تامينصحىوزارةالصحة",
}
RESERVE_REDEVANCES_EGY = (
    "Publiée en % par la douane, sans assiette, et aucun texte lu ne la fixe : liquidée sur la valeur en "
    "douane, sur décision, sous réserve."
)
#: Taxe de Table que la douane impose par instruction, sans la publier parmi les
#: taxes de la position (2404). Tabac chauffé : ر7058, « 1800 جنيه على الكيلو
#: جرام صافى ». Liquide des cigarettes électroniques : ر7059, ر7061, ر7062 et
#: ر7067, chacune « 4 جنيه لكل مليليتر سائل », les trois dernières « en plus »
#: des précédentes : cumulées sur décision du 20/10/2026 (16 EGP/ml).
INSTRUCTION_TABAC_CHAUFFE_EGY = "ر7058"
TABAC_CHAUFFE_EGY = re.compile(r"بواقع ([\d.]+) جنيه على الكيلو جرام صافى")
INSTRUCTIONS_LIQUIDE_EGY = ("ر7059", "ر7061", "ر7062", "ر7067")
LIQUIDE_EGY = re.compile(r"بواقع ([\d.]+) جنيه لكل مليليتر سائل")
SOURCE_INSTRUCTIONS_EGY = "customs.gov.eg — instructions de la position (Autorité égyptienne des douanes)"
TAXE_DE_TABLE_LIQUIDE_EGY = (
    "Instructions {codes} de la douane : Taxe de Table de 4 EGP par millilitre de liquide chacune, les dernières "
    "« en plus » des précédentes. Cumulées sur décision du 20/10/2026, sous réserve : {total} EGP par millilitre."
)
#: Taxe de Table que la douane subordonne à l'usage de la marchandise, par
#: instruction : instruction -> (code de l'usage, libellé, remplace la TVA).
#: ر7018 : « 5 % بدلا من 14% ق.ض » — au lieu de la TVA de 14 %. Le taux est lu
#: dans le texte de l'instruction ; l'usage est déclaré au calcul.
USAGES_EGY = {
    "ر7009": ("HUILE_NON_SUBVENTIONNEE", "Huile alimentaire non subventionnée", False),
    "ر7018": ("USAGE_DOMESTIQUE", "Usage domestique", True),
    "ر7027": ("PESTICIDE_AGRICOLE", "Pesticide agricole", False),
    "ر7100": ("ENGRAIS", "Engrais", False),
}
TAUX_INSTRUCTION_EGY = re.compile(r"([\d.]+)\s*%")
TAXE_DE_TABLE_CIGARETTES_EGY = (
    "Loi n° 67/2016, tableau annexé, partie I, item 1 (b) 3 : cigarettes, 50 % du prix de vente au "
    "consommateur final plus 275, 425 ou 525 piastres par paquet selon ce prix. Le prix de vente n'est pas une "
    "donnée du calcul : Taxe de Table non liquidée."
)


#: Formalités administratives publiées par la source, position par position.
#: Maroc (ADIL) : l'en-tête de la rubrique n'est pas une formalité ; la mention
#: « aucun document à présenter et aucune norme à respecter » est un constat de
#: la source, porté comme tel (`formalites_aucune`).
EN_TETE_FORMALITES_MAR = "Documents et Normes à l'Import."
AUCUNE_FORMALITE_MAR = '"AUCUN DOCUMENT A PRéSENTERETAUCUNE NORME A RESPECTER."'
#: Égypte : la douane publie ses instructions en arabe. L'ancien fichier ETL en
#: porte une traduction française et anglaise, sans source officielle : elle
#: n'accompagne le texte que si le code et le texte arabe sont les mêmes.
TRADUCTIONS_EGY = os.path.join(ETL_DIR, "EGY_tariffs.json")


def _traductions_egy():
    with open(TRADUCTIONS_EGY, encoding="utf-8") as f:
        lignes = json.load(f).get("tariff_lines") or []
    return {
        (x["code"], x["document_ar"].strip()): (x.get("document_fr"), x.get("document_en"))
        for ligne in lignes
        for x in ligne.get("administrative_formalities") or []
        if x.get("code") and x.get("document_ar")
    }


def _formalite(iso, item, traductions):
    """Une formalité de la source dans la forme commune, ou None."""
    if isinstance(item, str):
        texte = item.strip()
        if not texte or texte in (EN_TETE_FORMALITES_MAR, AUCUNE_FORMALITE_MAR):
            return None
        return {"code": None, "texte": texte, "document_fr": texte, "document_en": texte}
    if not isinstance(item, dict):
        return None
    if "code_verbatim" in item:  # Égypte
        code, texte = item["code_verbatim"], (item.get("text_verbatim") or "").strip()
        arabe = texte.split("-", 1)[1].strip() if texte.startswith(code + "-") else texte
        fr, en = traductions.get((code, arabe), (None, None))
        f = {"code": code, "texte": texte, "document_fr": fr or texte, "document_en": en or texte}
        if fr or en:
            f["traduction_non_officielle"] = True
        return f
    if "sigle" in item:  # Maurice
        texte = item.get("verbatim") or item["sigle"]
        libelle = f"{item['sigle']} — {item['organisme']}" if item.get("organisme") else texte
        return {"code": item["sigle"], "texte": texte, "document_fr": libelle, "document_en": libelle}
    if "type" in item and "description" in item:  # Mauritanie
        return {
            "code": item["type"],
            "texte": item["description"],
            "document_fr": item["description"],
            "document_en": item["description"],
            "base_legale": item.get("base_legale"),
        }
    texte = (item.get("text_verbatim") or item.get("description") or "").strip()  # Algérie, Tunisie
    if not texte:
        return None
    return {"code": item.get("code"), "texte": texte, "document_fr": texte, "document_en": texte}


def _formalites(iso, donnees, positions):
    """Porter sur chaque position les formalités que la source publie pour elle
    (`formalities`, ou `reglementation_import` en Tunisie)."""
    traductions = _traductions_egy() if iso == "EGY" else {}
    longueur_position = CLE_DE_CONTROLE_SUFFIXE.get(iso)
    for cle in ("positions", "sub_positions"):
        for ligne in donnees.get(cle, []) or []:
            if not isinstance(ligne, dict):
                continue
            brutes = ligne.get("formalities") or ligne.get("reglementation_import")
            if not isinstance(brutes, list) or not brutes:
                continue
            code = nettoyer_code(
                ligne.get("code_clean"),
                ligne.get("hs_code"),
                ligne.get("code"),
                ligne.get("code_raw"),
                ligne.get("national_code"),
                ligne.get("hs6"),
            )
            if longueur_position and len(code) == longueur_position:
                code = code.zfill(longueur_position + 1)
            if longueur_position and len(code) == longueur_position + 1:
                code = code[:longueur_position]
            position = positions.get(code)
            if position is None:
                continue
            formalites = [f for f in (_formalite(iso, x, traductions) for x in brutes) if f]
            if formalites:
                position["formalites"] = formalites
            elif AUCUNE_FORMALITE_MAR in brutes:
                position["formalites_aucune"] = True


#: Maroc : la nomenclature que le portail ADIL publie aujourd'hui. Le relevé des
#: droits (11/02/2026) porte des positions que le tarif a depuis redécoupées, et
#: ignore celles qui les remplacent ; les fiches de ces dernières ne sont pas
#: accessibles à la collecte (pare-feu du portail, 21/10/2026).
NOMENCLATURE_MAR = os.path.join(REPO, "data", "morocco", "adil_nomenclature_2026-10-21.json")
NOTE_POSITION_NOUVELLE_MAR = (
    "Position publiée par la nomenclature du portail ADIL au {date}, absente du "
    "relevé des droits du {collecte} : droits et taxes à compléter. Le total ne "
    "peut pas être servi."
)


SOURCE_NOMENCLATURE_MAR = "douane.gov.ma/adil — nomenclature"


def _texte_adil(texte):
    """Le texte ADIL, sauts de ligne (« \\r », « £ ») rendus en espaces."""
    return " ".join(texte.replace("\r", " ").replace("£", " ").split())


def _designation_hierarchique_maroc(code, publiees, titres, libelles_sh6):
    """La désignation d'une position nouvelle, du titre de position à la ligne.

    Le libellé terminal de l'ADIL (« autres ») ne dit pas de quelle
    marchandise il s'agit. Les titres sont ceux dont le code est un préfixe de
    la position : rien n'est déduit de l'indentation publiée, qui n'est pas
    fiable. Quand l'ADIL ne publie de titre ni à six ni à huit chiffres
    (0902.10), le libellé SH6 emprunté le remplace, sa source nommée ; un
    titre à huit chiffres tient lieu de titre SH6 (0405.10.00 « Beurre »)."""
    niveaux = []
    for longueur in (4, 6, 8):
        prefixe = code[:longueur]
        if prefixe in titres:
            niveaux.append({"code": prefixe, "texte": _texte_adil(titres[prefixe]), "source": SOURCE_NOMENCLATURE_MAR})
        elif longueur == 6 and code[:8] not in titres and (libelles_sh6.get(prefixe) or {}).get("fr"):
            emprunt = libelles_sh6[prefixe]
            niveaux.append(
                {"code": prefixe, "texte": emprunt["fr"], "source": f"libellé SH6 emprunté — {emprunt.get('fr_source')}"}
            )
    niveaux.append({"code": code, "texte": _texte_adil(publiees[code]), "source": SOURCE_NOMENCLATURE_MAR})
    return {"fr": " — ".join(n["texte"] for n in niveaux), "hierarchie": niveaux}


def _nomenclature_maroc(positions, compteurs, collecte):
    """Aligner les positions sur la nomenclature publiée : retirer celles
    qu'elle ne porte plus, ajouter celles qui manquent, SANS droit connu.

    Les 142 positions dont le relevé ne portait aucune taxe sont toutes parmi
    les retirées : le portail était muet parce qu'elles n'existaient plus.
    Rendre le bloc qui trace l'opération dans le socle."""
    with open(NOMENCLATURE_MAR, encoding="utf-8") as f:
        nomenclature = json.load(f)
    publiees = nomenclature["positions"]
    retirees = sorted(set(positions) - set(publiees))
    ajoutees = sorted(set(publiees) - set(positions))
    for code in retirees:
        for d in positions.pop(code)["droits"]:
            _compter_ligne(d, compteurs, -1)
            if d.get("libelle") == "Droit de douane — taux absent de la source":
                compteurs["droits_absents_completes"] -= 1
    assiettes = collections.Counter(
        d.get("assiette")
        for p in positions.values()
        for d in p["droits"]
        if d.get("famille") == "droit" and d.get("assiette")
    )
    note = NOTE_POSITION_NOUVELLE_MAR.format(
        date=_date_fr(nomenclature["releve_le"]), collecte=_date_fr(collecte[:10])
    )
    libelles_sh6 = charger_libelles_sh6()
    for code in ajoutees:
        positions[code] = {
            "designation": _designation_hierarchique_maroc(code, publiees, nomenclature["titres"], libelles_sh6),
            "hs6": code[:6],
            "chapitre": code[:2],
            "droits": [
                {
                    "code": "DD",
                    "code_source": "DD",
                    "libelle": "Droit de douane — taux à compléter",
                    "famille": "droit",
                    "taux": None,
                    "assiette": assiettes.most_common(1)[0][0],
                    "assiette_origine": "regle_de_pays",
                    "source": SOURCE_NOMENCLATURE_MAR,
                    "note": note,
                }
            ],
            "source": SOURCE_NOMENCLATURE_MAR,
        }
        _compter_ligne(positions[code]["droits"][0], compteurs, 1)
    compteurs["positions_retirees_nomenclature"] = len(retirees)
    compteurs["positions_ajoutees_nomenclature"] = len(ajoutees)
    return {
        "nom": SOURCE_NOMENCLATURE_MAR,
        "fichier": os.path.relpath(NOMENCLATURE_MAR, REPO),
        "sha256": sha256(NOMENCLATURE_MAR),
        "releve_le": nomenclature["releve_le"],
        "positions_publiees": len(publiees),
        "retirees": retirees,
        "ajoutees": ajoutees,
    }


def _date_fr(iso_date):
    annee, mois, jour = iso_date.split("-")
    return f"{jour}/{mois}/{annee}"


def _egypte(positions, compteurs, donnees):
    """Égypte : lignes publiées deux fois, tabacs, redevances, Taxe de Table des
    alcools et des cigarettes, droits au kilo et minimums de la Taxe de Table,
    ordre des lignes. Fiche
    EGY_TVA_taxe_de_table_2026-10-14.json."""
    instructions = {
        str(x.get("hs_code")): x.get("official_instructions") or []
        for x in donnees.get("sub_positions") or []
    }
    publiees = {str(x.get("hs_code")): x.get("taxes") or {} for x in donnees.get("sub_positions") or []}

    def specifique(montant, unite, brut):
        return {
            "montant": float(montant),
            "unite_monetaire": "unite_principale",
            "sous_unite_source": None,
            "unite_quantite": unite,
            "brut": brut,
        }

    for code, position in positions.items():
        droits = position.get("droits") or []
        # Une ligne publiée deux fois (8481.80.90.90 : « ID 60 % » et « TVA 14 % »
        # répétées) se lit en ID2/VAT2 ; la compter ferait payer le droit deux fois.
        for double, principal in (("ID2", "DD"), ("VAT2", "TVA")):
            d = next((x for x in droits if x.get("code") == double), None)
            p = next((x for x in droits if x.get("code") == principal), None)
            if d is not None and p is not None and d.get("taux") is not None and d.get("taux") == p.get("taux"):
                _compter_ligne(d, compteurs, -1)
                droits.remove(d)
        if code.startswith("24"):
            for d in droits:
                if d.get("famille") == "tva" and d.get("taux") not in (None, 0.0, 14.0):
                    d.update(
                        code=TAXE_DE_TABLE_EGY,
                        libelle="Taxe de Table (publiée sous « TVA »)",
                        famille="autre",
                        note=TABAC_TAXE_DE_TABLE_EGY,
                    )
        for d in droits:
            if d.get("code") in REDEVANCES_EGY and d.get("taux") is not None and not d.get("assiette"):
                _compter_ligne(d, compteurs, -1)
                d.update(assiette="CIF", assiette_origine="decision", note=RESERVE_REDEVANCES_EGY)
                _compter_ligne(d, compteurs, 1)
        if not any(d.get("code") == TAXE_DE_TABLE_EGY for d in droits):
            d = None
            alcool = TAXE_DE_TABLE_ALCOOLS_EGY.get(code[:4])
            if alcool and any(i.startswith(INSTRUCTION_ALCOOLS_EGY) for i in instructions.get(code, [])):
                taux, minimum, item = alcool
                brut = f"{taux:g} % (minimum {minimum:g} EGP/l)"
                d = {
                    "taux": taux,
                    "assiette": "CIF+TOUS_SAUF_TVA",
                    "assiette_origine": "texte_primaire",
                    "specifique": {
                        "montant": minimum,
                        "unite_monetaire": "unite_principale",
                        "sous_unite_source": None,
                        "unite_quantite": "l",
                        "brut": brut,
                    },
                    "compose": True,
                    "regle_composee": "LE_PLUS_ELEVE",
                    "expression_brute": brut,
                    "note": RESERVE_ALCOOLS_EGY.format(item=item),
                }
            elif code.startswith("240220"):
                d = {"assiette": None, "assiette_origine": None, "note": TAXE_DE_TABLE_CIGARETTES_EGY}
            consignes = [i for i in instructions.get(code, []) if i[:5] == INSTRUCTION_TABAC_CHAUFFE_EGY]
            liquide = [i for i in instructions.get(code, []) if i[:5] in INSTRUCTIONS_LIQUIDE_EGY]
            m = TABAC_CHAUFFE_EGY.search(consignes[0]) if consignes else None
            if d is None and m:
                brut = consignes[0]
                d = {
                    "assiette": "xQTE",
                    "assiette_origine": "droit_specifique",
                    "specifique": specifique(m[1], "kg", brut),
                    "expression_brute": brut,
                    "note": f"Instruction {INSTRUCTION_TABAC_CHAUFFE_EGY} de la douane : {m[1]} EGP par kilo net.",
                    "source": SOURCE_INSTRUCTIONS_EGY,
                }
            elif d is None and liquide:
                total = sum(float(LIQUIDE_EGY.search(i)[1]) for i in liquide)
                brut = " ; ".join(liquide)
                d = {
                    "assiette": "xQTE",
                    "assiette_origine": "droit_specifique",
                    "specifique": specifique(total, "ml", brut),
                    "expression_brute": brut,
                    "note": TAXE_DE_TABLE_LIQUIDE_EGY.format(
                        codes=", ".join(i[:5] for i in liquide), total=f"{total:g}"
                    ),
                    "source": SOURCE_INSTRUCTIONS_EGY,
                }
            if d is not None:
                d.setdefault("source", "Loi n° 67/2016 (TVA), art. 36 et tableau annexé")
                d.update(
                    code=TAXE_DE_TABLE_EGY,
                    code_source="ضريبة الجدول",
                    libelle="Taxe de Table",
                    famille="autre",
                )
                droits.append(d)
                _compter_ligne(d, compteurs, 1)
        usages = []
        for texte in instructions.get(code, []):
            if texte[:5] not in USAGES_EGY:
                continue
            usage, libelle, remplace_tva = USAGES_EGY[texte[:5]]
            usages.append(
                {
                    "code": usage,
                    "libelle": libelle,
                    "instruction": texte[:5],
                    "texte": texte,
                    "ajouter": [
                        {
                            "code": TAXE_DE_TABLE_EGY,
                            "code_source": "ضريبة الجدول",
                            "libelle": "Taxe de Table",
                            "famille": "autre",
                            "taux": float(TAUX_INSTRUCTION_EGY.search(texte)[1]),
                            "assiette": "CIF+TOUS_SAUF_TVA",
                            "assiette_origine": "texte_primaire",
                            "source": SOURCE_INSTRUCTIONS_EGY,
                            "note": f"Instruction {texte[:5]} de la douane, sur usage déclaré : « {texte} ».",
                        }
                    ],
                    "retirer": ["TVA"] if remplace_tva else [],
                }
            )
        if usages:
            position["usages"] = usages
        taxes = publiees.get(code, {})
        dd = next((x for x in droits if x.get("code") == "DD"), None)
        brut = ((taxes.get("ID") or {}).get("raw") or "").strip()
        m = DD_AU_KILO_EGY.match(brut)
        if m and dd is not None and dd.get("taux") is None and not dd.get("specifique"):
            _compter_ligne(dd, compteurs, -1)
            dd.update(
                assiette="xQTE",
                assiette_origine="droit_specifique",
                specifique=specifique(m[1], "kg", brut),
                expression_brute=brut,
            )
            _compter_ligne(dd, compteurs, 1)
        # Le minimum publié sur sa propre ligne borne la Taxe de Table, il ne
        # s'y ajoute pas : la plus élevée des deux est due (tableau, « القيمة
        # (٢٠٠٪) بحد أدنى ٥٠ جنيهًا لكل كجم مصنع »).
        tt = next((x for x in droits if x.get("code") == TAXE_DE_TABLE_EGY), None)
        for minimum in [x for x in droits if x.get("code") in MINIMUMS_EGY]:
            brut = ((taxes.get(minimum.get("code_source")) or {}).get("raw") or "").strip()
            m = MINIMUM_EGY.match(brut)
            if not m or minimum.get("taux") is not None or tt is None or tt.get("taux") is None or tt.get("specifique"):
                continue
            tt.update(
                specifique=specifique(m[1], UNITES_EGY[m[2]], brut),
                compose=True,
                regle_composee="LE_PLUS_ELEVE",
                expression_brute=f"{tt['taux']:g} % ; {brut}",
            )
            _compter_ligne(minimum, compteurs, -1)
            droits.remove(minimum)
        # La Taxe de Table et la TVA s'assoient sur les droits et taxes qui les
        # précèdent : la Taxe de Table vient après les autres prélèvements, un
        # minimum qui n'a pas pu lui être joint après elle, la TVA en dernier.
        def rang(d):
            if d.get("famille") == "tva":
                return 3
            if d.get("code") in MINIMUMS_EGY:
                return 2
            return 1 if d.get("code") == TAXE_DE_TABLE_EGY else 0

        droits.sort(key=rang)


def _tsp_tp_libye(positions, compteurs):
    """Libye : aucun texte trouvé ne fonde la « Port Services Tax » à 4 % ni la
    « Production Tax » à 2 % du crawl (fiche LBY_TSP_TP_taux_2026-10-10.json).
    Les lignes restent, sans taux, à compléter ; elles étaient déjà sans assiette."""
    for position in positions.values():
        for d in position.get("droits") or []:
            if d.get("code") not in TSP_TP_LIBYE:
                continue
            if d.get("taux") is not None:
                compteurs["taux_indisponibles"] += 1
            d["taux"] = None
            d["source"], d["note"] = TSP_TP_LIBYE[d["code"]]


def _ait_malawi(positions, compteurs):
    """Malawi : Advance Income Tax à l'importation sur la valeur des marchandises
    au point d'entrée (Taxation Act s.102B(1), taux porté de 3 % à 10 % par le
    Taxation (Amendment) Act 2023, s.8 ; fiche MWI_assiette_AIT_2026-10-08.json).
    Le taux reste celui de la colonne 12 de l'Order."""
    for position in positions.values():
        for d in position.get("droits") or []:
            if d.get("code") != "AIT":
                continue
            if not d.get("assiette"):
                compteurs["assiettes_indisponibles"] -= 1
                compteurs["assiettes_table"] += 1
            d["assiette"] = "CIF"
            d["assiette_origine"] = "regle_de_pays"
            d["note"] = (
                "Taxation Act s.102B(1), modifié par le Taxation (Amendment) Act 2023 : « ten per centum "
                "of the value of goods at the port of entry into Malawi ». Acompte d'impôt sur le revenu, "
                "imputable ; non dû sur certificat d'exemption, par un ministère, une personne exonérée, ou "
                "sous la section XXII de l'Order (s.102B(3))."
            )
            if d.get("taux") not in (None, 10.0):
                d["note"] = (
                    f"La colonne 12 de l'Order 2022 porte {d['taux']:g} % alors que la s.102B(1) fixe 10 % "
                    "depuis le Taxation (Amendment) Act 2023 : taux non attribuable sans deviner."
                )
                d["taux"] = None
                compteurs["taux_indisponibles"] += 1
        # L'AIT est « charged and payable on the importation of goods » (s.102B(2)) :
        # elle entre dans « all import duties and taxes » de la TVA (VAT Act s.28).
        if any(d.get("code") == "AIT" for d in position.get("droits") or []):
            for d in position["droits"]:
                if d.get("code") == "TVA":
                    d["assiette"] = "CIF+DD+EXC+AIT"
                    d["assiette_origine"] = "regle_de_pays"
                    d["note"] = (
                        "col. 11 — TVA. Assiette : Value Added Tax Act (Cap. 42:02) s.28 : « the import value "
                        "calculated in accordance with the Customs and Excise Act with the addition of all import "
                        "duties and taxes, but excluding Value Added Tax » ; l'Advance Income Tax en fait partie : "
                        "« charged and payable on the importation of goods » (Taxation Act s.102B(2))."
                    )


def _prelevements_senegal(positions, compteurs):
    """Sénégal : prélèvements d'entrée selon les FAQ de la DGD (2026) « Comment
    faire pour savoir les frais de dédouanement » et « Comment dédouaner un
    véhicule ? » (fiche SEN_taxes_specifiques_2026-10-10.json). Le crawl
    portait un PCS de 1 % au lieu de 0,8 %, et
    omettait le PROMAD (2 % de la valeur en douane) et le COSEC (0,4 %, dû par
    voie maritime seulement, liquidé comme dans les tableaux de la DGD, le mode
    de transport n'étant pas connu du moteur). Le PUA de 0,2 % du crawl, absent
    des tableaux de la DGD, est maintenu en attendant confirmation."""
    note_dgd = (
        "FAQ DGD 2026 « Comment faire pour savoir les frais de dédouanement de ma marchandise ? » "
        "et tableaux des taux cumulés des véhicules."
    )
    for code, position in positions.items():
        droits = []
        for d in position.get("droits") or []:
            if d.get("code") == "PUA":
                d["note"] = (
                    "Prélèvement de l'Union africaine, 0,2 % (taux de la source) : absent des tableaux de la DGD, "
                    "liquidé par la douane ivoirienne (circulaire DGD n° 2258) ; maintenu, application au Sénégal à confirmer."
                )
            if d.get("code") == "PCS":
                d["taux"] = 0.8
                d["note"] = "Prélèvement communautaire de solidarité : 0,8 % (" + note_dgd + ")"
            droits.append(d)
        libelle_pos = (position.get("designation") or "").lower()
        # Mots entiers : « usages spéciaux » n'est pas « usagé ».
        if re.search(r"\busagée?s?\b|\bd'occasion\b", libelle_pos):
            etat_taux = 3.0
        elif re.search(r"\bneu(f|fs|ve|ves)\b", libelle_pos):
            etat_taux = 1.0
        else:
            etat_taux = None
        if droits and (code[:4] in ("8702", "8703", "8704", "8705") or code[:6] == "870120") and not any(d.get("code") == "DENR" for d in droits):
            rang = next((i for i, d in enumerate(droits) if d.get("famille") == "tva"), len(droits))
            droits.insert(
                rang,
                {
                    "code": "DENR",
                    "code_source": "DENR",
                    "libelle": "Droit d'enregistrement des véhicules",
                    "famille": famille("DENR"),
                    "taux": etat_taux,
                    "assiette": "CIF+DD+RS",
                    "assiette_origine": "regle_de_pays",
                    "source": "Direction générale des douanes du Sénégal",
                    "note": "Droit d'enregistrement : 1 % pour un véhicule neuf, 3 % d'occasion, « (Base + DD + RS) × taux » "
                    "(" + note_dgd + ")" + (" ; état lu dans le libellé de la position." if etat_taux is not None
                                             else " ; l'état neuf ou d'occasion n'est pas dans la position."),
                },
            )
            compteurs["assiettes_table"] += 1
            if etat_taux is None:
                compteurs["taux_indisponibles"] += 1
        conditionnelles = []
        if code[:4] in ("2203", "2204", "2205", "2206", "2208") and code not in ("2206009100", "2206009900"):  # art. 412, 3°
            conditionnelles.append((
                "TAA", "Taxe additionnelle sur les alcools",
                "800 F par litre d'alcool au-delà de 6° et jusqu'à 15°, 3 000 F au-delà de 15° (CGI art. 413 ; "
                "tableau des mesures fiscales de la DGID) : le degré et le volume ne sont pas dans la position.",
            ))
        if code[:6] in ("240220", "240290"):
            conditionnelles.append((
                "STC", "Surtaxe sur les cigarettes",
                "Surtaxe sur les cigarettes, perçue au cordon douanier (" + note_dgd + ") : taux et assiette non publiés dans les textes lus.",
            ))
        if code in ("2002901100", "2002901900", "2002902000"):
            conditionnelles.append((
                "TCI", "Taxe conjoncturelle à l'importation",
                "Due sur le concentré de tomate quand la valeur CAF est inférieure au prix de déclenchement (" + note_dgd + ").",
            ))
        for code_c, libelle_c, note_c in conditionnelles:
            if droits and not any(d.get("code") == code_c for d in droits):
                rang = next((i for i, d in enumerate(droits) if d.get("famille") == "tva"), len(droits))
                droits.insert(rang, {
                    "code": code_c, "code_source": code_c, "libelle": libelle_c, "famille": famille(code_c),
                    "taux": None, "assiette": "CIF", "assiette_origine": "regle_de_pays",
                    "source": "Direction générale des douanes du Sénégal", "note": note_c,
                })
                compteurs["assiettes_table"] += 1
                compteurs["taux_indisponibles"] += 1
        if droits and not any(d.get("code") == "COSEC" for d in droits):
            rang = next((i for i, d in enumerate(droits) if d.get("famille") == "tva"), len(droits))
            droits.insert(
                rang,
                {
                    "code": "COSEC",
                    "code_source": "COSEC",
                    "libelle": "Prélèvement au profit du Conseil sénégalais des chargeurs",
                    "famille": famille("COSEC"),
                    "taux": 0.4,
                    "assiette": "CIF",
                    "assiette_origine": "regle_de_pays",
                    "source": "Direction générale des douanes du Sénégal",
                    "note": "COSEC 0,4 %, « uniquement par voie maritime » (" + note_dgd + ") : liquidé comme dans "
                    "les tableaux de la DGD ; à retirer pour un transport terrestre ou aérien.",
                },
            )
            compteurs["assiettes_table"] += 1
        if droits and not any(d.get("code") == "PROMAD" for d in droits):
            rang = next((i for i, d in enumerate(droits) if d.get("famille") == "tva"), len(droits))
            droits.insert(
                rang,
                {
                    "code": "PROMAD",
                    "code_source": "PROMAD",
                    "libelle": "Prélèvement pour la modernisation de l'administration des douanes",
                    "famille": famille("PROMAD"),
                    "taux": 2.0,
                    "assiette": "CIF",
                    "assiette_origine": "regle_de_pays",
                    "source": "Direction générale des douanes du Sénégal",
                    "note": "PROMAD 2 % de la valeur en douane (" + note_dgd + ")",
                },
            )
            compteurs["assiettes_table"] += 1
        position["droits"] = droits


def _prelevements_ghana(positions, compteurs):
    """Ghana : la collecte ne porte que DD, NHIL, GETFund et TVA. Prélèvements
    à l'importation sur la valeur c.a.f. (MoFEP/IFS, « A survey of the Ghanaian
    tax system », 2026, tableau 3.9) : ECOWAS Levy 0,5 %, AU Import Levy 0,2 %,
    EXIM Levy 0,75 % (Act 911, s. 29, hors produits pétroliers), Special Import
    Levy 2 % (Act 861, hors produits pétroliers, engrais, machines et
    équipements ; chapitres 84 et 85 sans taux, faute de liste). TVA,
    NHIL et GETFund sur une même base (GRA) : valeur en douane + droits et taxes
    à l'importation autres que la TVA (VAT Act 2025, Act 1151, s. 45(1)). Fiche :
    GHA_prelevements_TVA_2026-10-10.json."""
    mofep = "MoFEP/IFS, A survey of the Ghanaian tax system (2026), tableau 3.9"
    ajouts = [
        ("CEDEAO", "ECOWAS Levy", 0.5, "« All imported goods from non-ECOWAS states » : non dû sur les origines CEDEAO."),
        ("PUA", "AU Import Levy", 0.2, "African Union Import Levy Act 2017 (Act 952) : « All imported goods from non-AU states »."),
        ("EXIM", "Export-Import Levy", 0.75, "Act 911, s. 29 : « on the dutiable value of any product imported for commercial purposes except petroleum products »."),
        ("SIL", "Special Import Levy", 2.0, "Special Import Levy Act 2013 (Act 861) : « All imports, except for petroleum products, fertilisers, and machinery and equipment » ; produits pétroliers lus comme les positions 27.09 et 27.10, engrais comme le chapitre 31 ; exemptions de la First Schedule non relevées."),
    ]
    codes = "+".join(["DD"] + [c for c, _, _, _ in ajouts])
    # Le droit d'accises (barème ACCISES_PAYS, passe suivante) entre dans la base
    # commune ; absent de la position, il est sans objet.
    for code, position in positions.items():
        droits = position.get("droits") or []
        if not droits:
            continue
        presents = {d.get("code") for d in droits}
        rang = next((i + 1 for i, d in enumerate(droits) if d.get("code") == "DD"), 0)
        for c, libelle, taux, note in ajouts:
            if c in presents:
                continue
            if c == "EXIM" and code[:4] in ("2709", "2710", "2711", "2712", "2713"):
                continue
            if c == "SIL" and (code[:4] in ("2709", "2710") or code[:2] == "31"):
                continue
            if c == "SIL" and code[:2] in ("84", "85"):
                taux = None
                note += " Machines et équipements (chapitres 84 et 85) exclus, sans liste des positions concernées : taux non établi."
                compteurs["taux_indisponibles"] += 1
            droits.insert(
                rang,
                {
                    "code": c,
                    "code_source": c,
                    "libelle": libelle,
                    "famille": famille(c),
                    "taux": taux,
                    "assiette": "CIF",
                    "assiette_origine": "regle_de_pays",
                    "source": "Ghana Revenue Authority (Customs Division)",
                    "note": f"{note} ({mofep})",
                },
            )
            rang += 1
            compteurs["assiettes_table"] += 1
        for d in droits:
            if d.get("code") in ("TVA", "NHIL", "GETFUND") and d.get("assiette"):
                if d.get("assiette_origine") == "source":
                    compteurs["assiettes_source"] -= 1
                    compteurs["assiettes_table"] += 1
                d["assiette"] = "CIF+" + codes + "+DA"
                d["assiette_origine"] = "regle_de_pays"
                d["note"] = (
                    "VAT Act 2025 (Act 1151), s. 45(1) : « (a) the import value [...] (b) the import duties and taxes "
                    "other than the Tax » ; GRA : « the VAT, the NHIL and the GETFund Levy are all charged on the same base »."
                )
        position["droits"] = droits


def _prelevements_mali(positions, compteurs):
    """Mali : tarif de la DGD (TEC CEDEAO, édition du Mali, 28/12/2023 ; fiche
    MLI_prelevements_TVA_2026-10-10.json), sans assiette pour l'ISCP, la TAI, la
    TCI ni la TVA. CGI art. 243 : ISCP sur « la valeur en douane majorée des
    droits et taxes dus à l'entrée, à l'exception de la TVA » ; CGI art. 198 et
    199 : TVA sur la valeur CAF, y compris « les impôts, taxes, droits et
    prélèvements de toute nature à l'exception de la TVA »."""
    entree = "DD+RS+PCS+PC-AES+TAI+TCI"
    cgi = "Code général des impôts du Mali (DGI, édition mise à jour au 02/08/2017)"
    for position in positions.values():
        for d in position.get("droits") or []:
            code = d.get("code")
            if code in ("TAI", "ISCP", "TVA") and not d.get("assiette"):
                compteurs["assiettes_indisponibles"] -= 1
                compteurs["assiettes_table"] += 1
                d["assiette_origine"] = "regle_de_pays"
            if code == "TAI":
                d["famille"] = famille("DD")
                d["assiette"] = "CIF"
                d["note"] = "Taxe d'ajustement à l'importation, perçue sur la valeur CAF comme le droit de douane."
            elif code == "ISCP":
                d["assiette"] = "CIF+" + entree
                d["note"] = (
                    f"{cgi}, art. 243 : « à l'importation, par la valeur en douane majorée des droits et taxes "
                    "dus à l'entrée, à l'exception de la TVA »."
                )
            elif code == "TVA":
                d["assiette"] = "CIF+TOUS_SAUF_TVA"
                d["note"] = (
                    f"{cgi}, art. 198 : « pour les produits importés par la valeur CAF Franco frontière » ; art. 199 : "
                    "« Sont à inclure dans la base d'imposition : les impôts, taxes, droits et prélèvements de toute "
                    "nature à l'exception de la TVA »."
                )
                if d.get("taux") is None:
                    # Case TVA vide du tarif de 2023 (8708.22, 9508.21 à 9508.40,
                    # 9701.29), positions absentes des listes du CGI (art. 195 IV,
                    # point D) : taux de droit commun.
                    d["taux"] = 18.0
                    compteurs["taux_indisponibles"] -= 1
                    d["note"] += (
                        f" Art. 229 : « 18 % pour les autres produits et les services non exonérés » ; la case "
                        "TVA du tarif de la DGD est vide sur cette position."
                    )
            elif code == "TCI":
                d["note"] = (
                    "Taxe conjoncturelle à l'importation : assise sur un prix de déclenchement non publié ; "
                    "l'ISCP et la TVA de la position restent indisponibles."
                )
            elif code == "PC-AES":
                d["note"] = (
                    "Colonne PC (0,5 %) du tarif de 2023, prélèvement de la CEDEAO quittée le 29/01/2025 ; servie "
                    "comme prélèvement confédéral de l'AES au même taux (décision du 28/03/2025), dont sont exclues "
                    "les marchandises originaires de l'AES et de l'UEMOA (art. 1er et 4)."
                )


def _prelevements_burkina(positions):
    """Burkina Faso : la collecte porte un PCS de 1 % ; le taux communautaire est
    de 0,8 % (circulaire DGD de Côte d'Ivoire n° 2258, tarif de la DGD du Mali ;
    fiche BFA_prelevements_TVA_2026-10-11.json)."""
    for position in positions.values():
        for d in position.get("droits") or []:
            if d.get("code") == "PCS" and d.get("taux") == 1.0:
                d["taux"] = 0.8
                d["note"] = (
                    "Prélèvement communautaire de solidarité de l'UEMOA : 0,8 % (circulaire DGD n° 2258 de Côte "
                    "d'Ivoire : PCS « en vigueur » au taux de 0,8 % ; tarif de la DGD du Mali, colonne PCS)."
                )


def _pcs_uemoa(positions):
    """PCS : 0,8 % de la valeur en douane des marchandises importées des pays
    tiers (acte additionnel n° 01/2019/CCEG/UEMOA, art. 1er ; fiche
    UEMOA_AES_PCS_PC-AES_2026-10-11.json). Les collectes du Niger, du Bénin, du Togo
    et de la Guinée-Bissau portent encore 1 % (le Burkina a sa passe)."""
    for position in positions.values():
        for d in position.get("droits") or []:
            if d.get("code") == "PCS" and d.get("taux") == 1.0:
                d["taux"] = 0.8
                d["source"] = "Acte additionnel n° 01/2019/CCEG/UEMOA"
                d["note"] = (
                    "Acte additionnel n° 01/2019/CCEG/UEMOA, art. 1er : « maintenu à 0,80 % de la valeur en douane "
                    "des marchandises importées des pays tiers » (la collecte portait 1 %)."
                )


#: Burkina Faso : droits du TEC UEMOA 2022 que la collecte de février 2026
#: sous-évalue (fiche BFA_droits_TEC_2026-10-11.json).
DD_TEC_BFA = {"0701900000": 35.0, "0703100000": 35.0, "1511100000": 10.0}


def _droits_tec_burkina(positions):
    for code, taux in DD_TEC_BFA.items():
        for d in (positions.get(code) or {}).get("droits") or []:
            if d.get("code") == "DD" and d.get("taux") != taux:
                d["note"] = f"TEC UEMOA 2022 : {taux:g} % (la collecte portait {d['taux']:g} %)."
                d["taux"] = taux


#: Niger, loi de finances 2026 (ordonnance n° 2025-44, art. 13 ; CGI art. 322
#: nouveau, 2°), tableau réécrit par la première loi de finances rectificative
#: (ordonnance n° 2026-45, art. 7) : TVA exonérée à l'importation, par préfixe NTS.
TVA_EXONEREE_NER = (
    "0401", "0701", "0714", "10", "11062011", "11062012", "19011000", "22071010", "2501", "2705",
    "27101912", "27111300", "2936", "29392000", "2941", "30", "37011000", "37021000", "38089210",
    "38089290", "4014", "40151100", "42060000", "49019910", "4902", "49070000", "84139120", "84139190",
    "84139200", "84192000", "84249000", "87011000", "8713", "87142000", "9011", "9012", "9018",
    "9019", "90200000", "9021",
    # « Ex. position » 90.22 et 94.02 : seules les sous-positions dont le libellé
    # dit l'usage médical, chirurgical, dentaire ou vétérinaire.
    "9022130000", "9022140000", "9022210000", "9402101000", "9402900000",
)
#: Exonération dont le périmètre ne se lit pas dans la position.
TVA_EXONEREE_NER_A_TRANCHER = {
    "1006": "céréales exonérées « à l'exception du riz de luxe », que la nomenclature ne distingue pas",
    "9022120000": "« Ex. position 90 22 » : usage médical non dit par le libellé",
    "9022300000": "« Ex. position 90 22 » : usage médical non dit par le libellé",
    "9022900000": "« Ex. position 90 22 » : usage médical non dit par le libellé",
}


def _tva_exoneree_niger(positions, compteurs):
    """Niger : exonérations de TVA à l'importation de la loi de finances 2026 et
    de sa première rectification (fiche NER_TVA_exonerations_LF2026_2026-10-11.json)."""
    reference = "Ordonnance n° 2026-45 (première rectification de la loi de finances 2026), art. 7 : CGI art. 322 nouveau, 2°"
    for code, position in positions.items():
        motif = next((m for p, m in TVA_EXONEREE_NER_A_TRANCHER.items() if code.startswith(p)), None)
        exoneree = motif is None and code.startswith(TVA_EXONEREE_NER)
        if not (motif or exoneree):
            continue
        for d in position.get("droits") or []:
            if d.get("code") != "TVA" or d.get("taux") is None:
                continue
            if exoneree:
                d["taux"] = 0.0
                d["note"] = f"{reference} : « les importations et les ventes des produits énumérés »."
            else:
                d["taux"] = None
                d["note"] = f"{reference} : {motif}."
                compteurs["taux_indisponibles"] += 1


def _prelevements_guinee(positions, compteurs):
    """Guinée : tarif de la DGD (SH 2022 ; fiche GIN_prelevements_TVA_2026-10-11.json).
    CGI (texte 2022 du Ministère du Budget), art. 436 : accise ad valorem sur « la valeur CAF [...] majorée de
    l'ensemble des droits perçus au cordon douanier, à l'exception de la TVA » ;
    TVA sur la valeur en douane augmentée des droits et taxes de toute nature
    liquidés par la douane (arrêté du 31/03/2017, art. 12 ; Ministère du Budget)."""
    for position in positions.values():
        for d in position.get("droits") or []:
            if d.get("code") not in ("DA", "TVA"):
                continue
            if not d.get("assiette"):
                compteurs["assiettes_indisponibles"] -= 1
                compteurs["assiettes_table"] += 1
            elif d.get("assiette_origine") == "source":
                compteurs["assiettes_source"] -= 1
                compteurs["assiettes_table"] += 1
            d["assiette_origine"] = "regle_de_pays"
            d.pop("assiette_non_traduite", None)
            if d["code"] == "DA":
                d["assiette"] = "CIF+DD+RTL+PCC+CA"
                d["note"] = (
                    "Code général des impôts de Guinée (texte 2022 publié par le Ministère du Budget), art. 436 : "
                    "« la valeur CAF [...] majorée de l'ensemble des droits perçus au cordon douanier, à l'exception "
                    "de la TVA » ; « Les tarifs des droits d'accises sur les produits imposables importés sont fixés "
                    "dans le TARIF DES DOUANES »."
                )
            else:
                d["assiette"] = "CIF+TOUS_SAUF_TVA"
                d["note"] = (
                    "Arrêté du 31/03/2017, art. 12 : « L'assiette de la TVA intègre le montant des Droits et taxes de "
                    "Douane effectivement appliqué » ; valeur en douane augmentée des droits et taxes de toute nature "
                    "liquidés par l'administration des douanes, à l'exception de la TVA (Ministère du Budget)."
                )


def _prelevements_cote_divoire(positions, compteurs):
    """Côte d'Ivoire : tarif officiel de la DGD (TEC CEDEAO 2022 enrichi de la
    taxation nationale, mise à jour du 27/03/2026 ; fiche
    CIV_prelevements_TVA_2026-10-10.json). Il porte RS, PCS, PCC et PUA
    (circulaire DGD n° 2258) mais aucune assiette. Assiette des taxes spéciales
    du CGI art. 418 (boissons, tabacs, cosmétiques, marbres) : valeur en douane
    augmentée de tous les droits et taxes hormis la TVA ; assiette de la TVA :
    valeur en douane majorée des droits et taxes perçus à l'entrée (directive
    n° 02/98/CM/UEMOA, art. 27). Le droit unique de sortie, dû à l'exportation,
    n'entre pas dans le calcul d'une importation."""
    entree = "DD+RS+PCS+PCC+PUA+TAI+TCI"
    speciales = ("TSBPT", "TAB", "TCB", "TSM")
    omc = "Examen des politiques commerciales de la Côte d'Ivoire, OMC WT/TPR/S/362 (2017), § 3.24 et 3.26"

    def vers_table(d):
        # Une assiette réécrite par la règle du pays quitte le compteur de son origine.
        if d.get("assiette_origine") == "source":
            compteurs["assiettes_source"] -= 1
            compteurs["assiettes_table"] += 1
        elif d.get("assiette_origine") == "source_fichier":
            compteurs["assiettes_fichier"] -= 1
            compteurs["assiettes_table"] += 1

    for code_position, position in positions.items():
        droits = []
        for d in position.get("droits") or []:
            if d.get("code") == "TSBPT" and code_position.startswith("2002") and d.get("taux") is not None:
                # Tomates préparées : l'art. 418 ne vise que les boissons ; aucun
                # texte ne fonde le taux de 25 % publié dans la colonne TSB.
                d["taux"] = None
                compteurs["taux_indisponibles"] += 1
                d["note"] = (
                    "Colonne TSB du tarif de la DGD (25 %) sur des tomates préparées : la taxe spéciale de "
                    "l'art. 418 du CGI ne vise que les boissons (tableau synoptique DGI 2025) ; aucun texte "
                    "trouvé pour ce taux. À compléter."
                )
            if d.get("code") == "TAI":
                if not d.get("assiette"):
                    compteurs["assiettes_indisponibles"] -= 1
                    compteurs["assiettes_table"] += 1
                else:
                    vers_table(d)
                d["libelle"] = "Taxe d'ajustement à l'importation"
                d["famille"] = famille("DD")
                d["assiette"] = "CIF"
                d["assiette_origine"] = "regle_de_pays"
                d["note"] = (
                    "Taxe d'ajustement à l'importation, perçue sur la valeur en sus du TEC "
                    f"({omc}) ; taux publié au tarif officiel de la DGD."
                )
            if d.get("code") == "TPQ" and d.get("taux") is not None:
                d["libelle"] = "Taxe de péréquation sur le sucre"
                d["taux"] = None
                compteurs["taux_indisponibles"] += 1
                d["note"] = (
                    "« égale à la différence entre la valeur c.a.f. et le prix de déclenchement de la TCI, ce "
                    f"dernier formant la base imposable pour les autres droits et taxes » ({omc}) : dépend de la "
                    "valeur déclarée et du prix de déclenchement en vigueur."
                )
            if d.get("code") == "DUS":
                compteurs["assiettes_source" if d.get("assiette") else "assiettes_indisponibles"] -= 1
                if d.get("taux") is None:
                    compteurs["taux_indisponibles"] -= 1
                continue
            if d.get("code") in speciales and d.get("assiette"):
                vers_table(d)
                d["assiette"] = "CIF+" + entree
                d["assiette_origine"] = "regle_de_pays"
                if d.get("taux") is not None:
                    # Un taux retiré faute de texte (tomates préparées) garde sa
                    # propre note : l'art. 418 ne le fonde pas.
                    d["note"] = (
                        "CGI art. 418 (tableau synoptique DGI 2025) : « assises, à l'importation, sur la valeur "
                        "en douane des produits importés, augmentée de tous les droits et taxes hormis la TVA »."
                    )
            droits.append(d)
        presentes = [d["code"] for d in droits if d.get("code") in speciales]
        for d in droits:
            if d.get("famille") == "tva" and d.get("assiette"):
                vers_table(d)
                d["assiette"] = "+".join(["CIF", entree] + presentes)
                d["assiette_origine"] = "regle_de_pays"
                d["note"] = (
                    "Directive n° 02/98/CM/UEMOA, art. 27 a) : « par la valeur en douane majorée des droits "
                    "et taxes perçus à l'entrée, à l'exception de la Taxe sur la Valeur Ajoutée elle-même »."
                )
        if any(d.get("code") == "TPQ" for d in droits):
            # Sucre : le prix de déclenchement de la TCI, non publié, forme la base
            # des autres droits ; les liquider sur la valeur c.a.f. sous-évaluerait.
            for d in droits:
                if d.get("code") == "TPQ" or not d.get("assiette"):
                    continue
                vers_table(d)
                compteurs["assiettes_table"] -= 1
                compteurs["assiettes_indisponibles"] += 1
                d["assiette"] = None
                d["assiette_origine"] = None
                d["note"] = (
                    "Base imposable : prix de déclenchement de la TCI, « ce dernier formant la base imposable "
                    f"pour les autres droits et taxes » ({omc}) ; prix non publié."
                )
        position["droits"] = droits


def _accises_du_cgi(iso, positions, compteurs):
    with open(ACCISES_PAYS[iso], encoding="utf-8") as f:
        table = json.load(f)
    for code, position in positions.items():
        droits = [d for d in position.get("droits") or [] if d.get("code") != "DA"]
        for regle in table["regles"]:
            if code in regle.get("exclusions", []):
                continue
            if any(code.startswith(p) for p in regle["prefixes"]):
                # Avant la TVA, qui s'assoit sur lui : le moteur liquide dans l'ordre.
                # Ghana : avant le NHIL et le GETFund aussi, assis sur la même base.
                avant = table.get("inserer_avant_familles", ["tva"])
                rang = next(
                    (i for i, d in enumerate(droits) if d.get("famille") in avant), len(droits)
                )
                droits.insert(
                    rang,
                    {
                        "code": "DA",
                        "code_source": "DA",
                        "libelle": "Droit d'accises",
                        "famille": famille("DA"),
                        "taux": regle["taux"],
                        "assiette": table["assiette"],
                        "assiette_origine": "regle_de_pays",
                        "source": table["source"],
                        "note": " ".join(
                            x for x in (regle.get("motif"), regle["reference"], regle.get("reserve")) if x
                        ),
                    }
                )
                break
        for d in droits:
            if d.get("famille") == "tva" and d.get("assiette"):
                if d.get("assiette_origine") == "source":
                    compteurs["assiettes_source"] -= 1
                    compteurs["assiettes_table"] += 1
                d["assiette"] = table["tva_assiette"]
                d["assiette_origine"] = "regle_de_pays"
                d["note"] = table["tva_assiette_reference"]
        position["droits"] = droits


def _lignes_liquidables(position):
    """Pour chaque ligne de la position : le moteur la liquide-t-il ? C'est le
    moteur lui-même qui en juge (services/calcul.calculer), quantité, valeur
    FOB et taux de change fournis : le compteur ne peut pas diverger de lui.
    Une TVA assise sur un DA sans taux, un droit spécifique illisible, un
    composé sans règle de départage ne comptent donc pas."""
    droits = position.get("droits") or []
    if not droits:
        return []
    backend = os.path.join(REPO, "backend")
    if backend not in sys.path:
        sys.path.insert(0, backend)
    from services.calcul import calculer

    lignes = calculer(position, 1000.0, quantite=1.0, taux_de_change=1.0, valeur_fob=1000.0)["npf"]["lignes"]
    statuts = collections.defaultdict(list)
    for ligne in lignes:
        statuts[ligne.get("code")].append(ligne.get("statut"))
    return [(statuts[d.get("code")] or [None]).pop(0) == "CALCULE" for d in droits]


#: Libéria : accise à l'importation (Liberia Revenue Code, ch. 11, Schedule 1 de
#: la consolidation 2020 ; lignes remplacées par le Tax Amendment Act de
#: décembre 2025, publié le 01/04/2026). Fiche LBR_accises_2026-10-25.json.
#: Spécifiques, en dollars US : (positions, montant, unité de quantité, barème).
ACCISES_LBR = (
    (("2009",), 0.45, "li", "US$0.45/L"),
    (("2201",), 0.15, "li", "US$0.15/L"),
    (("2202",), 0.45, "li", "US$0.45/L"),
    (("2203", "2204", "2205", "2206"), 1.0, "li", "US$1.00/L"),
    (("2208",), 3.0, "li", "US$3.00/L"),
    (("2401", "2403"), 25.0, "kg", "US$25.00/Kg"),
    (("2402100000",), 0.5, "paquet de 20", "US$0.50 / pack of 20 sticks"),
    (("2402200000",), 0.5, "paquet de 20 cigarettes", "US$0.50 / pack of 20 sticks"),
    (("2402900000",), 0.25, "unité", "US$0.25 / stick"),
)
#: Ad valorem, s.1110(c) : (positions, taux %, ligne du Schedule 1 de 2020).
ACCISES_LBR_AD_VALOREM = (
    (("9614",), 50.0, "9614, smoking pipes and cigar or cigarette holders"),
    (("3303", "3304", "3305", "3307"), 20.0, "33, cosmetics and cosmetic aids"),
    (("1701991000", "1701999000"), 5.0, "1701.99.10.00 et 1701.99.90.00, sugar"),
    (("7113", "7114", "7115", "7116", "7117", "7118"), 10.0, "7113-7118, jewelry"),
    (("9504",), 30.0, "9504, gambling equipment"),
)


def _accises_liberia(positions, compteurs):
    """Libéria : accise due à l'importation (s.1105(b)), avant la GST."""
    base = {"code": "EXC", "code_source": "EXC", "famille": famille("EXC"), "libelle": "Excise tax"}
    for code, position in positions.items():
        ligne = None
        for prefixes, montant, unite, brut in ACCISES_LBR:
            if code.startswith(prefixes):
                ligne = {**base, "taux": None, "specifique": {
                    "montant": montant, "unite_monetaire": "USD", "sous_unite_source": None,
                    "unite_quantite": unite, "brut": brut}, "assiette": "xQTE", "assiette_origine": "droit_specifique",
                    "source": "Liberia Revenue Code, ch. 11, Schedule 1 (Tax Amendment Act of December 2025)",
                    "note": f"{brut} à l'importation, en dollars US (s.1110(a) : volume importé)."}
                break
        for prefixes, taux, article in ACCISES_LBR_AD_VALOREM:
            if ligne is None and code.startswith(prefixes):
                ligne = {**base, "taux": taux, "specifique": None, "assiette": "CIF+DD+PCC+CUF",
                         "assiette_origine": "regle_de_pays",
                         "source": f"Liberia Revenue Code, ch. 11, Schedule 1 ({article})",
                         "note": "s.1110(c) : valeur CIF, droit de douane, redevances douanières, prélèvement "
                                 "CEDEAO et autres droits, hors GST."}
        if ligne:
            droits = position.setdefault("droits", [])
            rang = next((i for i, d in enumerate(droits) if d.get("famille") == "tva"), len(droits))
            droits.insert(rang, ligne)
            _compter_ligne(ligne, compteurs, 1)


#: Angola : Imposto Especial de Consumo à l'importation (Lei n.º 16/21, Anexo I ;
#: spiritueux et tabac remplacés pour 2026 par la Lei n.º 14/25, art. 34.º et
#: Anexo IV). Codes de 2021 reportés sur la Pauta 2024 (SH 2022). Fiche
#: AGO_IEC_2026-10-25.json. (positions, taux %, référence).
IEC_AGO = (
    (("220210",), 3.0, "Lei n.º 16/21, Anexo I, 2202.10.00"),
    (("220291", "220299", "2203"), 4.0, "Lei n.º 16/21, Anexo I, 2202.91.00, 2202.99.00, 2203.00.00"),
    (("220410", "220421", "220422", "220429", "2205", "2206"), 8.0, "Lei n.º 16/21, Anexo I, 22.04 à 22.06"),
    (("2207",), 15.0, "Lei n.º 16/21, Anexo I, 22.07"),
    (("2208",), 25.0, "Lei n.º 14/25 (OGE 2026), art. 34.º et Anexo IV, 22.08"),
    (("2401", "2402", "2403"), 50.0, "Lei n.º 14/25 (OGE 2026), art. 34.º et Anexo IV, 24.01 à 24.03"),
    (("36041000",), 19.0, "Lei n.º 16/21, Anexo I, 3604.10.00"),
    (("39232110", "39232910"), 2.0, "Lei n.º 16/21, Anexo I, 3923.21.10 et 3923.29.10"),
    (("39232190", "39232990"), 19.0, "Lei n.º 16/21, Anexo I, 3923.21.90 et 3923.29.90"),
    (("4012",), 19.0, "Lei n.º 16/21, Anexo I, 40.12"),
    (("7113", "7114"), 15.0, "Lei n.º 16/21, Anexo I, 71.13 et 71.14"),
    (("87032449", "87032459", "87033359", "87033369", "87042110", "87042111", "87042113", "87042114"), 5.0,
     "Lei n.º 16/21, Anexo I, 8703.24, 8703.33 et 8704.21"),
    (("8801", "88021100", "88022000", "890321", "890322", "890323", "890331", "890332", "890333"), 20.0,
     "Lei n.º 16/21, Anexo I, 88.01, 88.02 et 89.03"),
    (("93032000", "93033000"), 50.0, "Lei n.º 16/21, Anexo I, 9303.20.00 et 9303.30.00"),
    (("9701", "9702", "9703", "9704", "9705", "9706"), 5.0, "Lei n.º 16/21, Anexo I, 97.01 à 97.06"),
)


def _iec_angola(positions, compteurs):
    """Angola : IEC dû au desembaraço aduaneiro (art. 8.º), sur le valor
    aduaneiro (art. 7.º n.º 1 b)), avant l'IVA dont l'assiette le comprend."""
    for code, position in positions.items():
        regle = next((r for r in IEC_AGO if code.startswith(r[0])), None)
        if regle is None:
            continue
        _, taux, reference = regle
        ligne = {"code": "EXC", "code_source": "IEC", "famille": famille("EXC"),
                 "libelle": "Imposto Especial de Consumo", "taux": taux, "specifique": None,
                 "assiette": "CIF", "assiette_origine": "regle_de_pays", "source": reference,
                 "note": "Lei n.º 16/21, art. 7.º n.º 1 b) : valor aduaneiro des biens importés. Exonérations "
                         "de l'art. 6.º (matières premières et usage médical sous déclaration d'exclusivité, "
                         "véhicules électriques, etc.) non distinguées."}
        droits = position.setdefault("droits", [])
        rang = next((i for i, d in enumerate(droits) if d.get("famille") == "tva"), len(droits))
        droits.insert(rang, ligne)
        _compter_ligne(ligne, compteurs, 1)


#: Mozambique : taux spécifiques de l'ICE (Código do ICE, Lei n.º 19/2022, tabela
#: anexa, colonne 2025, prorogée pour 2026-2027 par la Lei n.º 7/2025). La Pauta
#: les publie en « ICE_VAL_MIN » ; la tabela en donne l'unité, que la Pauta
#: altère parfois (« 7.71 MZN Per 1 KG » pour « 7,71/Litro »). Fiche
#: MOZ_ice_especifico_2026-10-26.json. Code → (montant en MT, unité, tabela).
ICE_ESPECIFICO_MOZ = {
    "22029990": (1.99, "litre", "1,99/Litro"),
    "22030060": (5.5, "litre", "5,50/Litro"),
    "24021000": (550, "kg", "550/kg"),
    "24022000": (540, "millier de cigarettes", "540/mil Unid"),
    "24029000": (590, "kg", "590/kg"),
    "24031100": (640, "kg", "640/kg"),
    "24031900": (640, "kg", "640/kg"),
    "24039100": (640, "kg", "640/kg"),
    "24039900": (640, "kg", "640/kg"),
    "27101229": (0.51, "litre", "0,51/Litro"),
    "27101231": (4.67, "litre", "4,67/Litro"),
    "27101239": (7.71, "litre", "7,71/Litro"),
    "27101240": (1.02, "litre", "1,02/Litro"),
    "27101290": (1.02, "litre", "1,02/Litro"),
    "27101921": (1.02, "litre", "1,02/Litro"),
    "27101929": (1.02, "litre", "1,02/Litro"),
    "27101939": (4.27, "litre", "4,27/Litro"),
    "27101945": (0.75, "litre", "0,75/Litro"),
    "27111100": (0.35, "kg", "0,35/Kg"),
    "27111200": (0.66, "kg", "0,66/Kg"),
    "27111300": (0.66, "kg", "0,66/Kg"),
    "27111910": (0.66, "kg", "0,66/Kg"),
    "39232920": (105, "kg", "105/kg"),
    "39233030": (30, "kg", "30/kg"),
    "39239090": (30, "kg", "30/kg"),
    "87021020": (455000, "unité", "455.000/unid"),
    "87031020": (65000, "unité", "65.000/unid"),
    "87032120": (12000, "unité", "12.000/unid"),
    "87032220": (15000, "unité", "15.000/unid"),
    "87032390": (75000, "unité", "75.000/unid"),
    "87032490": (145000, "unité", "145.000/unid"),
    "87033120": (32000, "unité", "32.000/unid"),
    "87033290": (109000, "unité", "109.000/unid"),
    "87033390": (109000, "unité", "109.000/unid"),
    "87039020": (155000, "unité", "155.000/unid"),
    "87042120": (175000, "unité", "175.000/unid"),
    "87042140": (125000, "unité", "125.000/unid"),
    "87043120": (90000, "unité", "90.000/unid"),
}
#: Taux au gramme de sucre contenu dans 100 ml (méthode 1 de la tabela) ou au
#: litre d'alcool pur (méthodes 2 à 4) : le calcul ne reçoit ni la teneur en
#: sucre ni le titre alcoométrique. Préfixe → tabela ; le premier qui couvre le
#: code l'emporte.
ICE_NON_LIQUIDABLE_MOZ = (
    ("2009", "0,0099/g de Aç.Cont.100 ml", "sucre"),
    ("210690", "0,0140/g de Aç. Cont.100ml", "sucre"),
    ("22029910", "0,0147/g de Aç.Cont.100 ml", "sucre"),
    ("22042910", "470/Litro Alc.", "alcool"),
    ("2203", "475/Litro Alc.", "alcool"),
    ("2204", "619/Litro Alc.", "alcool"),
    ("2205", "619/Litro Alc.", "alcool"),
    ("2206", "475/Litro Alc.", "alcool"),
    ("22071090", "600/Litro Alc.", "alcool"),
    ("22072000", "460/Litro Alc.", "alcool"),
    ("22089010", "435/Litro Alc.", "alcool"),
    ("22089020", "280/Litro Alc.", "alcool"),
    ("2208", "460/Litro Alc.", "alcool"),
)
SOURCE_ICE_MOZ = (
    "Código do ICE (Lei n.º 19/2022, BR I série n.º 251 du 29/12/2022), tabela anexa ; "
    "taux prorogés pour 2026-2027 par la Lei n.º 7/2025"
)


def _ice_mocambique(positions, compteurs):
    """Mozambique : la ligne « ICE_VAL_MIN » de la Pauta est le taux spécifique
    de l'ICE, fondu dans la ligne ICE de la position. Ad valorem et spécifique
    prévus ensemble : « aplica-se a que resultar maior valor do imposto »
    (Código do ICE, art. 9 n.º 3)."""
    for code, position in positions.items():
        droits = position.get("droits") or []
        minimum = next((d for d in droits if d.get("code_source") == "ICE_VAL_MIN"), None)
        if minimum is None:
            continue
        ice = next((d for d in droits if d.get("code") == "ICE"), None)
        for d in (minimum, ice):
            if d is not None:
                _compter_ligne(d, compteurs, -1)
        if ice is None:
            ice = minimum
            ice.update(code="ICE", libelle="Imposto sobre Consumos Específicos", famille=famille("ICE"))
        else:
            droits.remove(minimum)
        ice["source"] = SOURCE_ICE_MOZ
        if code in ICE_ESPECIFICO_MOZ:
            montant, unite, brut = ICE_ESPECIFICO_MOZ[code]
            ice["specifique"] = {"montant": montant, "unite_monetaire": "unite_principale",
                                 "sous_unite_source": None, "unite_quantite": unite, "brut": brut}
            if ice.get("taux") is None:
                ice.update(assiette="xQTE", assiette_origine="droit_specifique")
                ice["note"] = f"Tabela anexa : « {brut} »."
            else:
                ice.update(compose=True, regle_composee="LE_PLUS_ELEVE",
                           expression_brute=f"{ice['taux']:g} % ou {brut}")
                ice["note"] = (f"Tabela anexa : {ice['taux']:g} % ou « {brut} » ; art. 9 n.º 3 : « aplica-se a "
                               "que resultar maior valor do imposto ».")
        else:
            _, brut, teneur = next(r for r in ICE_NON_LIQUIDABLE_MOZ if code.startswith(r[0]))
            motif = (
                f"« {brut} » porte sur les grammes de sucre contenus dans 100 ml, teneur que le calcul ne reçoit pas"
                if teneur == "sucre"
                else f"« {brut} » porte sur le litre d'alcool pur, titre alcoométrique que le calcul ne reçoit pas"
            )
            if ice.get("taux") is not None:
                motif += (f" ; l'ad valorem de {ice['taux']:g} % n'est qu'une borne basse, l'art. 9 n.º 3 "
                          "retenant le plus élevé des deux")
                ice["taux"] = None
            ice["note"] = f"Tabela anexa : {motif} — non liquidable en l'état."
        _compter_ligne(ice, compteurs, 1)


#: Tchad : colonne « Taux taxe spécifique » de l'art. 36 de la LF 2021, rédaction
#: de la LF 2026 (art. 44). Fiche TCD_droit_accises_2026-10-26.json.
#: (positions, exclusions, taux %, (montant FCFA, unité) ou None, tableau).
TAXE_SPECIFIQUE_TCD = (
    (("2202",), (), None, (50, "bouteille ou canette"), "50 FCFA/Bouteille ou cannette importée"),
    (("2203",), (), 10.0, None, "10%"),
    (("2204", "2205"), (), 15.0, None, "15%"),
    (("2208",), (), 20.0, None, "20%"),
    (("2402",), (), None, (50, "paquet"), "50FCFA/Paquet"),
    (("2403",), ("24039920",), None, (50, "paquet"), "50FCFA/Paquet"),
    (("870324", "870333"), (), 20.0, None, "20%"),
    (("3917", "3923", "3924", "3926"), (), 10.0, None, "10%"),
    (("29072200",), (), 30.0, None, "30%"),
    (("08041000",), (), 30.0, None, "30%"),
)
SOURCE_TAXE_SPECIFIQUE_TCD = (
    "Loi de finances pour 2021, art. 36 (nouveau), rédaction de la loi de finances pour 2026 "
    "(loi n° 008/AN/SENAT/2025), art. 44"
)


def _taxe_specifique_tchad(positions, compteurs):
    """Tchad : la taxe spécifique au montant par unité se liquide sur la
    quantité ; au pourcentage, sa base n'est pas énoncée — l'art. 36 n'énonce
    que celle du droit d'accises —, elle est portée sans assiette."""
    for code, position in positions.items():
        regle = next((r for r in TAXE_SPECIFIQUE_TCD if code.startswith(r[0]) and code not in r[1]), None)
        if regle is None:
            continue
        _, _, taux, montant, brut = regle
        ligne = {"code": "SPEC", "code_source": "SPEC", "famille": famille("SPEC"), "libelle": "Taxe spécifique",
                 "taux": taux, "specifique": None, "assiette": None, "assiette_origine": None,
                 "source": SOURCE_TAXE_SPECIFIQUE_TCD}
        if montant:
            ligne.update(specifique={"montant": montant[0], "unite_monetaire": "unite_principale",
                                     "sous_unite_source": None, "unite_quantite": montant[1], "brut": brut},
                         assiette="xQTE", assiette_origine="droit_specifique")
            ligne["note"] = f"Art. 36, colonne « Taux taxe spécifique » : « {brut} »."
        else:
            ligne["note"] = (f"Art. 36, colonne « Taux taxe spécifique » : {brut} ; l'article n'en énonce pas la "
                             "base (seule celle du droit d'accises l'est) — non liquidable en l'état.")
        droits = position.setdefault("droits", [])
        rang = next((i for i, d in enumerate(droits) if d.get("famille") == "tva"), len(droits))
        droits.insert(rang, ligne)
        _compter_ligne(ligne, compteurs, 1)


def construire_pays(iso, chemin, origine, assiettes_pays):
    langue_origine = PAYS_LIBELLES_TRADUITS.get(iso)
    libelles_sh6 = charger_libelles_sh6() if langue_origine else None
    with open(chemin, encoding="utf-8") as f:
        donnees = json.load(f)

    profil = assiettes_pays.get(iso, {})
    assiettes_codees = profil.get("taxes", {})
    assiettes_fichier = assiettes_du_fichier(donnees)

    source_defaut_pays = donnees.get("source") or donnees.get("source_name") or ""
    positions = {}
    compteurs = {
        "positions": 0,
        "droits": 0,
        "droits_liquidables": 0,
        "positions_liquidables": 0,
        "preferentiels": 0,
        "preferentiels_specifiques": 0,
        "preferentiels_collision": 0,
        "preferentiels_non_nommes": 0,
        "taux_indisponibles": 0,
        "assiettes_source": 0,
        "assiettes_fichier": 0,
        "assiettes_table": 0,
        "assiettes_indisponibles": 0,
        "sans_designation": 0,
        "droits_specifiques": 0,
        "droits_composes": 0,
        "restrictions": 0,
        "interdictions": 0,
        "droits_absents_completes": 0,
        "droits_lus_en_designation": 0,
        "classification_estimee": 0,
    }
    familles_vues = set()
    #: Les couples (position, régime) où deux colonnes se réclament du même
    #: régime préférentiel. Rapportés, jamais absorbés.
    collisions = []

    for code, designation, unite, droits, source_ligne, restrictions in lignes_du_fichier(
        donnees, REGIMES_PAR_PAYS.get(iso), compteurs
    ):
        # LA CLÉ DE CONTRÔLE N'EST PAS UNE SUBDIVISION TARIFAIRE. Elle est
        # détachée ici, au point unique où le pays est connu et où les six
        # schémas de lecture se rejoignent — la poser dans le générateur
        # obligerait à la répéter six fois, et `iso` n'y est pas défini.
        cle_controle = None
        longueur_position = CLE_DE_CONTROLE_SUFFIXE.get(iso)
        if longueur_position and len(code) == longueur_position:
            # Un chiffre de moins que code + clé : le zéro de tête a été perdu
            # à la collecte (Tunisie : « 4039011010 » pour 0403.90.11.01.0).
            code = code.zfill(longueur_position + 1)
        if longueur_position and len(code) == longueur_position + 1:
            code, cle_controle = code[:longueur_position], code[longueur_position:]

        retenus, prefs = [], {}
        position_complete = True
        for d in droits:
            regime = d.pop("_preferentiel", None)
            if regime is not None:
                # Une colonne préférentielle est conservée telle quelle, sous son
                # propre régime. Elle n'entre jamais dans la cascade NPF.
                # Le régime est celui que `_droit` a déjà posé — soit par
                # `PREFERENTIELS` quand il vient d'une colonne de taxe, soit par
                # `REGIMES_PAR_PAYS` quand la source le nomme elle-même. Le
                # rechercher une seconde fois interdisait le second cas.
                # DEUX COLONNES NE PEUVENT PAS SE PARTAGER UN RÉGIME EN SILENCE.
                # `prefs` est un dictionnaire : une seconde colonne rangée sous le
                # même régime écrasait la première sans rien dire. Le tarif
                # malawien en donne le cas — il publie DEUX colonnes SADC, l'une
                # « for imports from other Member States other than South Africa »
                # (col. 8), l'autre « for imports from South Africa only »
                # (col. 9) — et la distinction que sa loi établit disparaîtrait.
                # Le taux servi serait alors celui de la dernière colonne lue :
                # crédible, et faux pour la moitié des origines.
                if regime in prefs:
                    # Deux cas, et un seul est dangereux. Si les deux colonnes
                    # portent LE MÊME taux, le doublon est sans effet et l'on
                    # garde ce qu'on a. Si elles DIVERGENT, aucune ne peut être
                    # retenue : servir l'une ou l'autre serait juste pour une
                    # moitié des origines et faux pour l'autre. Le régime est
                    # alors retiré — le moteur ne servira pas de préférence, au
                    # lieu d'en servir une tirée au sort — et la collision est
                    # comptée pour que le relecteur la voie.
                    ancien = prefs.get(regime) or {}
                    if ancien.get("taux") == d["taux"] and not d.get("specifique"):
                        continue
                    compteurs["preferentiels_collision"] += 1
                    collisions.append((code, regime, d["code_source"]))
                    prefs[regime] = {
                        "taux": None,
                        "motif": "DEUX_COLONNES_POUR_UN_MEME_REGIME",
                    }
                    continue
                # La colonne se conserve sous la même forme qu'un droit NPF —
                # taux ad valorem OU montant spécifique — parce qu'elle en prend
                # la forme : 181 lignes sud-africaines opposent un « 8c/kg » NPF
                # à un « 3,2c/kg » AfCFTA. N'en garder que le taux perdrait le
                # droit préférentiel de toutes ces positions.
                if d["taux"] is not None and d.get("specifique"):
                    # Droit COMPOSÉ dans une colonne préférentielle
                    # (« 40% or 240c/kg » — 140 entrées AfCFTA du crawl SARS) :
                    # les DEUX composantes se conservent, avec le verbatim.
                    # Servir 40 % ad valorem seul remplacerait le droit composé
                    # entier : c'est au moteur de départager selon la règle
                    # reportée (regle_composee), ou de refuser faute de règle
                    # (REGLE_COMPOSEE_NON_ETABLIE), pas au socle d'amputer.
                    prefs[regime] = {
                        "taux": d["taux"],
                        "specifique": lire_specifique(d["specifique"])
                        or {
                            "brut": str(d["specifique"]),
                            "montant": None,
                            "motif": "expression non lisible",
                        },
                        "compose": True,
                        "expression_brute": d.get("expression_brute") or "",
                    }
                    if d.get("regle_composee"):
                        prefs[regime]["regle_composee"] = d["regle_composee"]
                    if d.get("cumulatif"):
                        # « 7%+SCR5/kg » (Seychelles, colonnes ZLECAf, SADC,
                        # COMESA) : les deux composantes sont dues, comme au NPF.
                        prefs[regime]["compose"] = False
                        prefs[regime]["cumulatif"] = True
                    if d.get("plafond_ad_valorem_pct") is not None:
                        prefs[regime]["plafond_ad_valorem_pct"] = d["plafond_ad_valorem_pct"]
                    if d.get("deduction_ad_valorem_pct") is not None:
                        prefs[regime]["deduction_ad_valorem_pct"] = d["deduction_ad_valorem_pct"]
                    compteurs["preferentiels_specifiques"] += 1
                elif d["taux"] is None and d.get("specifique"):
                    prefs[regime] = {
                        "taux": None,
                        "specifique": lire_specifique(d["specifique"])
                        or {
                            "brut": str(d["specifique"]),
                            "montant": None,
                            "motif": "expression non lisible",
                        },
                    }
                    # « 180c/kg with a maximum of 38,4 % » (colonne AfCFTA) : la
                    # borne fait partie du droit — la perdre servirait le
                    # spécifique sans plafond, là où la source en énonce un.
                    if d.get("plafond_ad_valorem_pct") is not None:
                        prefs[regime]["plafond_ad_valorem_pct"] = d["plafond_ad_valorem_pct"]
                        prefs[regime]["expression_brute"] = d.get("expression_brute") or ""
                    if d.get("deduction_ad_valorem_pct") is not None:
                        prefs[regime]["deduction_ad_valorem_pct"] = d["deduction_ad_valorem_pct"]
                    compteurs["preferentiels_specifiques"] += 1
                elif d["taux"] is None and d.get("note"):
                    # UN TAUX ABSENT DOIT DIRE POURQUOI. La source mauricienne
                    # déclare 129 colonnes non liquidables — 109 sous contingent
                    # tarifaire, 20 en droit spécifique — et ce motif se perdait
                    # ici : la préférence sortait en `{"taux": null}` nu,
                    # indiscernable d'une colonne que le collecteur n'a pas su
                    # lire. Ce n'est pas la même chose pour l'opérateur.
                    prefs[regime] = {"taux": None, "motif": d["note"]}
                else:
                    prefs[regime] = {"taux": d["taux"]}
                compteurs["preferentiels"] += 1
                continue
            if d["assiette"] is not None:
                compteurs["assiettes_source"] += 1
            elif d["code"] in assiettes_fichier:
                assiette, plafond = assiettes_fichier[d["code"]]
                d["assiette"] = assiette
                d["assiette_origine"] = "source_fichier"
                d["plafond"] = d["plafond"] or plafond
                compteurs["assiettes_fichier"] += 1
            elif assiettes_codees.get(d["code"]):
                codee = assiettes_codees[d["code"]]
                d["assiette"] = codee["assiette"]
                d["assiette_origine"] = codee["origine_assiette"]
                compteurs["assiettes_table"] += 1
            else:
                compteurs["assiettes_indisponibles"] += 1
            if d["specifique"] and not isinstance(d["specifique"], dict):
                # La décomposition vaut pour TOUTE composante spécifique, y
                # compris celle d'un droit composé qui porte aussi un taux :
                # le moteur refuse une chaîne (« 1.50 USD/kg ») pour ne pas en
                # relire le seul nombre, et rendait donc QUANTITE_REQUISE sur
                # les 61 droits zimbabwéens « X % or US$ Y/kg » alors même que
                # la quantité était fournie et la règle de départage énoncée.
                d["specifique"] = lire_specifique(d["specifique"]) or {
                    "brut": str(d["specifique"]),
                    "montant": None,
                    "motif": "expression non lisible",
                }
            if (
                d.get("deduction_ad_valorem_pct") is not None
                or d.get("plafond_ad_valorem_pct") is not None
            ):
                # « less 80% » et « with a maximum of 96% » se prennent sur la
                # valeur en douane : celle que l'assiette du pays donne au droit
                # (FOB en SACU), retenue avant que la part spécifique ne fasse
                # passer le droit à la quantité. Les colonnes préférentielles
                # s'y rapportent aussi.
                d["assiette_valeur"] = d["assiette"]
            if d["specifique"] and d["taux"] is None and not d.get("assiette_non_traduite"):
                # Une assiette que la source décrit sans qu'on sache la traduire
                # (« PN(KG)/100 EXCES », « QCI ») reste non traduite : la forcer
                # à la quantité liquidait 1 156 droits tunisiens malgré leur réserve.
                # Un droit spécifique se liquide à la quantité, jamais sur la
                # valeur. Si l'assiette héritée dit « CIF », elle décrit le
                # droit ad valorem de la ligne, pas celui-ci : la laisser
                # ferait lire « 8c/kg » comme « 8 % ».
                d["assiette"] = "xQTE"
                d["assiette_origine"] = "droit_specifique"
                d["plafond"] = None
                compteurs["droits_specifiques"] += 1
            if d["taux"] is None and not d["specifique"]:
                compteurs["taux_indisponibles"] += 1
            if d.get("classification_source") == "estimation_ia":
                compteurs["classification_estimee"] += 1
            familles_vues.add(d["famille"])
            # Un droit est liquidable s'il porte de quoi produire un montant :
            # une assiette, et soit un taux, soit un montant spécifique lisible.
            # La quantité, elle, dépend de la demande — elle n'est pas un défaut
            # de la donnée et n'entre pas dans ce compte.
            specifique_lisible = (
                isinstance(d.get("specifique"), dict) and d["specifique"].get("montant") is not None
            )
            # Un droit COMPOSÉ porte ses deux composantes mais pas la règle qui
            # les départage : le moteur refuse de le liquider. Le compter ici
            # comme liquidable ferait dire au manifeste qu'un montant est
            # calculable là où la réponse servie est une indisponibilité
            # nommée — deux vérités pour un même droit.
            if d.get("compose"):
                compteurs["droits_composes"] = compteurs.get("droits_composes", 0) + 1
                position_complete = False
            elif d["assiette"] and (d["taux"] is not None or specifique_lisible):
                compteurs["droits_liquidables"] += 1
            else:
                position_complete = False
            retenus.append({k: v for k, v in d.items() if v is not None})

        retenus.sort(key=lambda d: ORDRE_FAMILLES.index(d.get("famille", "autre")))
        if not designation:
            compteurs["sans_designation"] += 1
        if libelles_sh6 is not None:
            designation = traduire_designation(designation, code[:6], libelles_sh6, langue_origine)
        positions[code] = {
            "designation": designation,
            "hs6": code[:6],
            "chapitre": code[:2],
            "droits": retenus,
        }
        if cle_controle:
            # Conservée pour la saisie de la déclaration, mais hors du code :
            # le sélecteur affiche la position, pas la position plus sa clé.
            positions[code]["cle_controle"] = cle_controle
        if unite:
            positions[code]["unite"] = unite
        if prefs:
            positions[code]["preferentiels"] = prefs
        if source_ligne:
            positions[code]["source"] = source_ligne
        # Une interdiction d'importation est une RÉPONSE, pas une absence. Sans
        # elle, une position prohibée se présente comme un calcul indisponible —
        # l'opérateur lit « on ne sait pas » là où le tarif dit « interdit ».
        # Relevé sur le tarif libyen 2022 : 62 positions portent
        # « ممنوع استيراده ». Elles ne portent aucun droit, et c'est normal.
        if restrictions:
            positions[code]["restrictions"] = restrictions
            compteurs["restrictions"] = compteurs.get("restrictions", 0) + len(restrictions)
            compteurs["interdictions"] = compteurs.get("interdictions", 0) + sum(
                1 for r in restrictions if _est_une_interdiction(r)
            )
        compteurs["positions"] += 1
        compteurs["droits"] += len(retenus)
        if retenus and position_complete:
            compteurs["positions_liquidables"] += 1

    # ── Une position sans droit, dans un pays qui en publie ────────────────
    # Le socle ne liquide que ce qu'il porte. Une position dépourvue de toute
    # ligne de droit se sert donc COMPLÈTE, sans droit de douane — un total qui
    # paraît entier et ne l'est pas. Mesuré sur le socle du 2026-09-18 :
    # 2 915 positions dans ce cas, sur douze pays, dont 12 444,00 servis
    # « COMPLET » pour DZA/2710122400 avec accise, TVA et zéro droit.
    #
    # Trois causes distinctes ont été trouvées en remontant aux sources : un
    # zéro publié supprimé à la collecte (Éthiopie), une source qui ne publie
    # rien (Maroc, dont le champ `taxes` est vide), et un droit bien présent
    # mais non reconnu (les droits sectoriels tunisiens, traités plus haut).
    # Aucune ne justifie de servir la position comme si rien n'était dû.
    #
    # La ligne est donc posée SANS TAUX : le moteur la déclare indisponible et
    # refuse le total, au lieu de le rendre amputé. Elle n'est posée que si le
    # pays publie des droits ailleurs — un pays qui n'en collecte aucun
    # (couverture sans la famille « droit ») n'en reçoit pas, et une position
    # dont l'importation est interdite non plus : là, l'absence est la réponse.
    if "droit" in familles_vues:
        # L'assiette du droit de douane est une règle de PAYS, pas de position :
        # on reprend celle que la même source pose sur ses autres positions,
        # plutôt que d'en supposer une. Sans elle, le moteur signalerait une
        # assiette manquante là où c'est le TAUX qui manque — un motif juste
        # mais qui désigne le mauvais trou.
        assiettes_du_droit = collections.Counter(
            d.get("assiette")
            for pos in positions.values()
            for d in pos["droits"]
            if d.get("famille") == "droit" and d.get("assiette")
        )
        assiette_courante = assiettes_du_droit.most_common(1)[0][0] if assiettes_du_droit else None
        for code, position in positions.items():
            # SEULE une interdiction d'importer explique l'absence de droit.
            # Le champ `restrictions` transporte aussi des mentions
            # RÉGLEMENTAIRES — la source égyptienne en porte 26 502, du type
            # « ق3034 : pas de déclaration d'export des espèces CITES sans
            # accord du jardin zoologique ». Une marchandise soumise à
            # autorisation entre quand même, et son droit reste dû : la traiter
            # comme prohibée dispenserait 26 502 positions de déclarer un droit
            # manquant, sur la foi d'une note qui ne dit rien du droit.
            if any(_est_une_interdiction(r) for r in position.get("restrictions") or []):
                continue
            if any(d.get("famille") == "droit" for d in position["droits"]):
                continue
            # Le barème peut être écrit dans la désignation : on le lit avant de
            # conclure à l'absence. Une absence déclarée vaut mieux qu'un
            # silence, mais un droit lu vaut mieux qu'une absence déclarée.
            compose = droit_compose_depuis_designation(
                position.get("designation"), position.get("source") or source_defaut_pays
            )
            if compose:
                position["droits"].insert(0, compose)
                compteurs["droits"] += 1
                compteurs["droits_composes"] = compteurs.get("droits_composes", 0) + 1
                compteurs["droits_lus_en_designation"] = (
                    compteurs.get("droits_lus_en_designation", 0) + 1
                )
                continue
            position["droits"].insert(
                0,
                {
                    "code": "DD",
                    "code_source": "DD",
                    "libelle": "Droit de douane — taux absent de la source",
                    "famille": "droit",
                    "taux": None,
                    "assiette": assiette_courante,
                    "assiette_origine": "regle_de_pays" if assiette_courante else None,
                    "source": position.get("source") or source_defaut_pays,
                    "note": (
                        "Aucun droit de douane n'est publié pour cette position, alors "
                        "que la source en publie pour d'autres. Le total ne peut pas "
                        "être servi comme complet : le droit est déclaré indisponible "
                        "plutôt que supposé nul."
                    ),
                },
            )
            compteurs["droits"] += 1
            compteurs["taux_indisponibles"] += 1
            compteurs["droits_absents_completes"] = compteurs.get("droits_absents_completes", 0) + 1

    _formalites(iso, donnees, positions)
    nomenclature_publiee = None
    if iso == "MAR":
        nomenclature_publiee = _nomenclature_maroc(positions, compteurs, donnees.get("extracted_at") or "")
    if iso == "TUN":
        _ordre_tunisie(positions)
    if iso == "NGA":
        _iat_nigeria_2026(positions, compteurs)
    if iso == "SLE":
        _droits_nationaux_sle(positions)
    if iso == "AGO":
        _droits_angola_2026(positions, compteurs)
    if iso in _taux_tva_legaux():
        _taux_tva_hors_la_loi(_taux_tva_legaux()[iso], positions, compteurs)
    if iso == "MWI":
        _ait_malawi(positions, compteurs)
    if iso == "CMR":
        _redevance_informatique_cmr(positions)
    if iso == "MRT":
        _accises_mauritanie(positions, compteurs)
    if iso == "GNQ":
        _sans_redevance_informatique_gnq(positions, compteurs)
    if iso in _regles_cedeao_hors_uemoa()[0]:
        _prelevements_cedeao_hors_uemoa(iso, positions, compteurs)
    if iso == "MUS":
        _mid_levy_maurice(positions, compteurs)
    if iso == "LBY":
        _tsp_tp_libye(positions, compteurs)
    if iso == "LBR":
        _accises_liberia(positions, compteurs)
    if iso == "AGO":
        _iec_angola(positions, compteurs)
    if iso == "MOZ":
        _ice_mocambique(positions, compteurs)
    if iso == "TCD":
        _taxe_specifique_tchad(positions, compteurs)
    if iso in ASSIETTE_EXA_SACU:
        _accises_zaf(positions, compteurs, iso)
    if iso in PRELEVEMENTS_SACU_NON_COLLECTES:
        _prelevements_sacu_non_collectes(iso, positions, compteurs)
    if iso == "NAM":
        _prelevements_nam(positions, compteurs)
    if iso == "LSO":
        _prelevement_tapl_lesotho(positions, compteurs)
    if iso == "SLE":
        _accises_sierra_leone(positions, compteurs)
    if iso == "ZAF":
        _prelevements_zaf(positions, compteurs)
        _controles_sars_zaf(positions)
        _liste_sars_zaf(positions)
    if iso in PAYS_TEC_CAE:
        _cae(iso, positions, compteurs)
        _mesures_tec_cae(iso, positions, compteurs)
    if iso == "EGY":
        _egypte(positions, compteurs, donnees)
    if iso == "ETH":
        _droits_livre_ethiopie(positions, compteurs)
        _accise_ethiopie(positions, compteurs)
        _surtaxe_et_swl_ethiopie(positions, compteurs)
        _ordre_ethiopie(positions)

    if iso == "SEN":
        _prelevements_senegal(positions, compteurs)
    if iso == "CIV":
        _prelevements_cote_divoire(positions, compteurs)
    if iso == "GHA":
        _prelevements_ghana(positions, compteurs)
    if iso == "MLI":
        _prelevements_mali(positions, compteurs)
    if iso == "BFA":
        _prelevements_burkina(positions)
        _droits_tec_burkina(positions)
    if iso == "NER":
        _tva_exoneree_niger(positions, compteurs)
    if iso in BLOCS_DESTINATION["UEMOA"]:
        _pcs_uemoa(positions)
    if iso == "GIN":
        _prelevements_guinee(positions, compteurs)

    if iso in ACCISES_PAYS or iso in ASSIETTE_ACCISE_PAYS:
        # Les compteurs par ligne lue ont déjà compté les accises du crawl : on
        # retranche celles d'avant et on ajoute celles d'après.
        def _da():
            return [
                dict(d)
                for p in positions.values()
                for d in p.get("droits") or []
                if d.get("famille") == "accise"
            ]

        avant = _da()
        if iso in ACCISES_PAYS:
            _accises_du_cgi(iso, positions, compteurs)
        if iso in ASSIETTE_ACCISE_PAYS:
            _assiette_accise(iso, positions)
        apres = _da()
        for lignes, signe in ((avant, -1), (apres, 1)):
            for d in lignes:
                if d.get("taux") is None and not d.get("specifique"):
                    compteurs["taux_indisponibles"] += signe
                if d.get("taux") is None and d.get("specifique"):
                    compteurs["droits_specifiques"] += signe
                if not d.get("assiette"):
                    cle = "assiettes_indisponibles"
                elif d.get("assiette_origine") == "source":
                    cle = "assiettes_source"
                elif d.get("assiette_origine") == "source_fichier":
                    cle = "assiettes_fichier"
                else:
                    cle = "assiettes_table"
                compteurs[cle] += signe

    # Prélèvements communautaires dont les originaires du bloc sont exclus
    # (backend/services/exoneration_origine.py) : la route les retire selon
    # l'origine déclarée.
    for position in positions.values():
        for d in position.get("droits") or []:
            bloc = EXONERATION_ORIGINE.get(d.get("code"))
            if bloc and (bloc == "UA" or iso in BLOCS_DESTINATION[bloc]):
                d["exoneration_origine"] = bloc

    # Les compteurs s'incrémentaient PAR LIGNE LUE. Deux lignes qui portent le
    # même code sont comptées deux fois et servies une seule : le compteur
    # annonçait donc plus de positions que le socle n'en porte, et c'est ce qui
    # a masqué la perte de 349 positions libyennes rabattues sur le SH6.
    # Ils comptent désormais ce qui est RÉELLEMENT SERVI.
    # Les passes par pays (prélèvements, accises) ajoutent des familles après la
    # lecture : la couverture se lit sur ce qui est servi.
    # Droits de sortie : servis à part (`droits_export`), jamais mêlés aux droits
    # de l'importation qu'ils ne concernent pas.
    longueur_position = CLE_DE_CONTROLE_SUFFIXE.get(iso)
    for code, droits in droits_export_du_fichier(iso, donnees).items():
        if longueur_position and len(code) in (longueur_position, longueur_position + 1):
            code = code.zfill(longueur_position + 1)[:longueur_position]
        if code in positions:
            positions[code]["droits_export"] = droits
            compteurs["positions_export"] = compteurs.get("positions_export", 0) + 1
    for code, droits in droits_export_par_texte(iso, positions).items():
        positions[code]["droits_export"] = droits
        compteurs["positions_export"] = compteurs.get("positions_export", 0) + 1
    familles_vues = {d["famille"] for p in positions.values() for d in p.get("droits") or [] if d.get("famille")}
    compteurs["positions"] = len(positions)
    compteurs["droits"] = sum(len(p.get("droits") or []) for p in positions.values())
    compteurs["droits_composes"] = sum(
        1 for p in positions.values() for d in p.get("droits") or [] if d.get("compose")
    )
    liquidables = {code: _lignes_liquidables(p) for code, p in positions.items()}
    compteurs["droits_liquidables"] = sum(sum(v) for v in liquidables.values())
    compteurs["positions_liquidables"] = sum(1 for v in liquidables.values() if v and all(v))

    socle = {
        "iso3": iso,
        "socle_version": SOCLE_VERSION,
        "source": {
            "fichier": os.path.relpath(chemin, REPO),
            "origine": origine,
            "nom": donnees.get("source") or donnees.get("source_name") or "",
            "url": donnees.get("source_url"),
            "qualite": donnees.get("source_quality"),
            "nomenclature": donnees.get("nomenclature") or donnees.get("hs_version"),
            "collecte": (
                donnees.get("extracted_at")
                or donnees.get("extraction_date")
                or donnees.get("generated_at")
            ),
            "sha256": sha256(chemin),
        },
        "assiettes": {
            "reference_legale": profil.get("reference_legale", ""),
            "origine": "source_et_table" if profil else "source_seule",
            "methode_publiee": methode_verbatim(donnees),
        },
        "couverture": {
            "familles": sorted(familles_vues),
            "droit_de_douane": "droit" in familles_vues,
            "tva": "tva" in familles_vues,
            "positions_liquidables": compteurs["positions_liquidables"],
            "droits_liquidables": compteurs["droits_liquidables"],
            # L'état ne se déduit PAS de la seule présence des familles : un
            # pays peut porter un droit et une TVA sans qu'aucun des deux soit
            # liquidable, faute d'assiette ou de taux. C'est le cas de l'Angola,
            # dont les 5 388 TVA n'ont pas d'assiette tracée. Annoncer COMPLET
            # là-dessus reproduirait les « 100 % de couverture » déduits de
            # listes non vides que l'audit reprochait au module.
            "etat": (
                "VIDE"
                if compteurs["positions"] == 0
                else (
                    "COMPLET"
                    if (
                        {"droit", "tva"} <= familles_vues
                        and compteurs["droits_liquidables"] == compteurs["droits"]
                    )
                    else "PARTIEL"
                )
            ),
            "motif": (
                None
                if compteurs["positions"] == 0
                or (
                    {"droit", "tva"} <= familles_vues
                    and compteurs["droits_liquidables"] == compteurs["droits"]
                )
                else "; ".join(
                    filter(
                        None,
                        [
                            (
                                None
                                if "droit" in familles_vues
                                else "aucun droit de douane à la source"
                            ),
                            None if "tva" in familles_vues else "aucune TVA à la source",
                            (
                                f"{compteurs['droits'] - compteurs['droits_liquidables']} droits "
                                f"sur {compteurs['droits']} non liquidables"
                                if compteurs["droits_liquidables"] != compteurs["droits"]
                                else None
                            ),
                        ],
                    )
                )
            ),
        },
        "compteurs": compteurs,
        # Pas d'horodatage ici, à dessein : un socle reconstruit depuis les
        # mêmes sources doit être identique à l'octet près, sinon son empreinte
        # change sans que la donnée ait bougé et le manifeste devient faux. La
        # date de construction vit au manifeste, qui n'est pas empreint.
        "positions": positions,
    }
    if nomenclature_publiee:
        socle["nomenclature_publiee"] = nomenclature_publiee
    if iso in CLE_DE_CONTROLE_SUFFIXE:
        # Posée seulement pour les pays concernés : les 53 autres fichiers
        # restent alors identiques au bit près, et le manifeste ne signale que
        # ce qui a réellement changé.
        socle["nomenclature"] = {
            "longueur_position": CLE_DE_CONTROLE_SUFFIXE[iso],
            "cle_controle": "suffixe d'un chiffre, saisi avec le code sur la déclaration",
        }

    return socle, compteurs


def main(argv):
    os.makedirs(SOCLE_DIR, exist_ok=True)
    assiettes_pays = charger_assiettes_pays()
    sources = sources_disponibles()
    demandes = [a.upper() for a in argv[1:]] or sorted(sources)

    # Une construction partielle ne doit pas amputer le manifeste : les pays
    # non reconstruits restent sur disque, et les retirer de l'index les rendrait
    # introuvables alors qu'ils sont servables. On repart donc de l'existant.
    # Un manifeste illisible ou non conforme se reconstruit, il n'arrête pas la
    # construction : les fichiers pays présents sur disque restent servables, et
    # échouer ici les rendrait introuvables pour rien. On repart alors d'un
    # index vide, que la boucle ci-dessous regarnit.
    ancien = {}
    chemin_manifeste = os.path.join(SOCLE_DIR, "MANIFESTE.json")
    if os.path.exists(chemin_manifeste):
        try:
            with open(chemin_manifeste, encoding="utf-8") as f:
                charge = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            print(f"[build_socle] manifeste illisible ({exc}) : reconstruction depuis zéro")
            charge = None
        pays_existants = charge.get("pays") if isinstance(charge, dict) else None
        ancien = pays_existants if isinstance(pays_existants, dict) else {}
    manifeste = {
        "socle_version": SOCLE_VERSION,
        "construit_le": datetime.now(timezone.utc).isoformat(),
        # Les entrées non reconstruites sont conservées, même si leur fichier
        # n'est pas sur le disque à cet instant : dans un clone frais, le
        # manifeste est versionné quand les 54 fichiers pays ne le sont pas, et
        # les filtrer sur leur présence réduirait l'index au seul pays demandé.
        # L'absence d'un fichier se dit déjà au chargement (`SocleIndisponible :
        # fichier de socle absent — le régénérer`), ce qui est une panne
        # nommée ; un pays disparu de l'index, lui, est muet.
        #
        # Conservées, mais pas au prix d'un plantage : les totaux plus bas
        # lisent `etat` et `compteurs`, et une entrée tronquée les ferait
        # échouer sur un KeyError — exactement l'interruption que la tolérance
        # au manifeste illisible existe pour éviter. Une entrée inexploitable
        # est donc écartée, comme le serait un manifeste entier illisible.
        "pays": {iso: e for iso, e in ancien.items() if _entree_exploitable(e)},
        "totaux": {},
    }
    vides = []

    for iso in demandes:
        if iso not in sources:
            print(f"  {iso} : aucune source", file=sys.stderr)
            continue
        chemin, origine = sources[iso]
        socle, c = construire_pays(iso, chemin, origine, assiettes_pays)
        etat = socle["couverture"]["etat"]
        sortie = os.path.join(SOCLE_DIR, f"{iso}.json")
        with open(sortie, "w", encoding="utf-8") as f:
            json.dump(socle, f, ensure_ascii=False, separators=(",", ":"))
        manifeste["pays"][iso] = {
            "fichier": f"{iso}.json",
            "origine": origine,
            "source_fichier": socle["source"]["fichier"],
            "source_sha256": socle["source"]["sha256"],
            "socle_sha256": sha256(sortie),
            "collecte": socle["source"]["collecte"],
            "etat": etat,
            "familles": socle["couverture"]["familles"],
            "compteurs": c,
        }
        print(
            f"  {iso} {origine:5} {etat:8} {c['positions']:6d} pos {c['droits']:7d} droits"
            f"  taux? {c['taux_indisponibles']:5d}  assiette? {c['assiettes_indisponibles']:6d}"
        )

    # Les totaux sont recalculés sur l'index entier, pas sur la seule sélection.
    vides = sorted(i for i, v in manifeste["pays"].items() if v["etat"] == "VIDE")
    manifeste["totaux"] = {
        "pays": len(manifeste["pays"]),
        "pays_vides": vides,
        "pays_partiels": sorted(i for i, v in manifeste["pays"].items() if v["etat"] == "PARTIEL"),
        "positions": sum(v["compteurs"]["positions"] for v in manifeste["pays"].values()),
        "droits": sum(v["compteurs"]["droits"] for v in manifeste["pays"].values()),
        "droits_liquidables": sum(
            v["compteurs"].get("droits_liquidables", 0) for v in manifeste["pays"].values()
        ),
    }
    with open(os.path.join(SOCLE_DIR, "MANIFESTE.json"), "w", encoding="utf-8") as f:
        json.dump(manifeste, f, ensure_ascii=False, indent=2)

    totaux = manifeste["totaux"]
    print(
        f"\n{totaux['pays']} pays — {totaux['positions']} positions, "
        f"{totaux['droits']} droits dont {totaux['droits_liquidables']} liquidables"
    )
    if vides:
        print(f"Pays sans aucune position (déclarés vides, jamais estimés) : {', '.join(vides)}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
