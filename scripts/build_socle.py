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
import glob
import hashlib
import importlib
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
    "RPD": "redevance",
    "IDF": "redevance",
    "RDL": "redevance",
    "INFRA": "redevance",
    "CISS": "redevance",
    "PSV": "redevance",
    "DSV": "redevance",
    "TCL": "redevance",
    "EXC": "accise",
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
    "DAPS": "droit",  # droit additionnel provisoire de sauvegarde (DZ)
    "TPI": "redevance",  # taxe parafiscale à l'importation (MA)
    "TCS": "accise",  # taxe de consommation spécifique (DZ)
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
    "CIF + DD + EXC": ("CIF+DD+EXC", None),
    "CIF+DUTY": ("CIF+DD", None),
    "CIF+DUTY+FEES": ("CIF+TOUS_SAUF_TVA", None),
    "CIF+DUTY+LEVIES": ("CIF+TOUS_SAUF_TVA", None),
    "CIF (PLAFOND 15 000 XAF)": ("CIF", {"montant": 15000.0, "devise": "XAF"}),
    # Tunisie — libellés du tarif intégré (SINDA)
    "VALEUR DOUANE DINARS": ("CIF", None),
    "VALEUR DOUANE": ("CIF", None),
    "QCS": ("xQTE", None),
    "QCI": ("xQTE", None),
    "PN (KG)": ("xQTE", None),  # poids net : droit liquidé à la quantité
    "VAL DOUANE+ SOMME DT": ("CIF+TOUS_SAUF_SOI", None),
}

#: Assiettes que la source exprime mais que le socle ne traduit **pas**, avec
#: le motif. Les nommer vaut mieux que les ramener de force à « CIF » : une
#: assiette approchée produit un montant faux qui a l'air juste.
ASSIETTES_NON_TRADUITES = {
    "PN(KG)/100 EXCES": "droit au poids avec seuil d'excédent — la règle de seuil n'est pas publiée avec la ligne",
    "VARIABLE": "la source déclare l'assiette variable",
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
    if texte.startswith("VAL.DOU") and "R(DT)" in texte:
        return "CIF+DD", None, None
    # Tunisie : « SOMME D.T (G=...) » = somme des droits et taxes, hors valeur
    if texte.startswith("SOMME D.T"):
        return "SOMME(TOUS_SAUF_SOI)", None, None
    return None, None, f"expression non reconnue : {texte[:60]}"


def charger_assiettes_pays():
    if not os.path.exists(ASSIETTES_PATH):
        _reconstruire_assiettes_pays()
    try:
        return _lire_assiettes_pays()
    except (OSError, json.JSONDecodeError, ValueError):
        _reconstruire_assiettes_pays()
        return _lire_assiettes_pays()


def _lire_assiettes_pays():
    with open(ASSIETTES_PATH, encoding="utf-8") as f:
        charge = json.load(f)
    pays = charge.get("pays") if isinstance(charge, dict) else None
    if not isinstance(pays, dict):
        raise ValueError("table d'assiettes non conforme")
    return pays


def _assiette_depuis_profil(formule, ajouts):
    if formule == "DD_AMOUNT":
        return "MONTANT_DD"
    if formule == "CIF_PLUS_TOUTES_TAXES_SAUF_TVA":
        return "CIF+TOUS_SAUF_TVA"
    base = str(formule or "").strip() or "CIF"
    dependances = [str(code).strip().upper() for code in (ajouts or []) if code]
    return "+".join([base, *dependances]) if dependances else base


def _reconstruire_assiettes_pays():
    """Reconstruire la table d'assiettes depuis les sources versionnées du dépôt."""
    if REPO not in sys.path:
        sys.path.insert(0, REPO)

    try:
        profils = importlib.import_module("backend.services.tax_profile_data")
    except Exception as exc:
        raise RuntimeError("impossible de charger backend.services.tax_profile_data") from exc

    ASSIETTE_TVA_ETABLIE = profils.ASSIETTE_TVA_ETABLIE
    COUNTRY_TAX_PROFILES = profils.COUNTRY_TAX_PROFILES

    print(
        f"[build_socle] {os.path.relpath(ASSIETTES_PATH, REPO)} absent : reconstruction "
        "depuis COUNTRY_TAX_PROFILES",
        file=sys.stderr,
    )

    pays = {}
    for iso, profil in sorted(COUNTRY_TAX_PROFILES.items()):
        taxes = {}
        for code, spec in (profil.get("tax_bases") or {}).items():
            if not isinstance(spec, (list, tuple)) or len(spec) != 2:
                raise ValueError(f"profil fiscal invalide pour {iso}/{code}")
            formule, ajouts = spec
            taxes[code_canonique(code, code) or code] = {
                "assiette": _assiette_depuis_profil(formule, ajouts),
                "origine_assiette": "table_codee",
            }

        regle_tva = ASSIETTE_TVA_ETABLIE.get(iso)
        if regle_tva:
            taxes.setdefault("TVA", {}).update(
                {
                    "assiette": "CIF+TOUS_SAUF_TVA",
                    "origine_assiette": "texte_primaire",
                    "texte": regle_tva["texte"],
                    "fiche": regle_tva.get("fiche"),
                }
            )

        pays[iso] = {
            "reference_legale": profil.get("source", ""),
            "taxes": taxes,
        }

    _ecrire_json_atomique(ASSIETTES_PATH, {"pays": pays}, ensure_ascii=False, indent=2)


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
        return float(valeur)
    if isinstance(valeur, str):
        v = valeur.strip().lower()
        if v in _MOTS_ZERO:
            return 0.0
        m = re.search(r"-?\d+(?:[.,]\d+)?", v)
        if m:
            return float(m.group(0).replace(",", "."))
    return None


#: Sous-unités monétaires rencontrées dans les tarifs. Un droit publié en
#: centimes vaut un centième de l'unité : lire « 8c/kg » comme « 8 par kg »
#: surestime le droit d'un facteur cent.
SOUS_UNITES = {"c": 100, "cent": 100, "cents": 100, "ct": 100}

_SPECIFIQUE = re.compile(
    r"^\s*(?P<montant>-?\d+(?:[.,]\d+)?)\s*(?P<monnaie>[A-Za-zÀ-ÿ]*)\s*(?:/\s*(?P<quantite>[A-Za-zÀ-ÿ0-9]+))?",
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
    montant = float(m.group("montant").replace(",", "."))
    monnaie = (m.group("monnaie") or "").lower()
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
#: Ce cas se distingue nettement du « 40% or 240c/kg » sud-africain, que le
#: socle REFUSE de liquider : celui-là ne dit pas laquelle des deux composantes
#: s'applique, celui-ci le dit — « whichever is higher ».
MOTIF_COMPOSE_DESIGNATION = re.compile(
    r"([\d]+(?:[.,][\d]+)?)\s*%\s*or\s*(?:\$|USD|US\$)\s*([\d]+(?:[.,][\d]+)?)\s*/\s*"
    r"(MT|kg|t|L)\b\s*whichever\s+is\s+(higher|lower)",
    re.I,
)

REGLES_COMPOSEES = {"higher": "LE_PLUS_ELEVE", "lower": "LE_MOINS_ELEVE"}


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
        if taux is None:
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
        # « 40% or 240c/kg » (94 positions) est l'autre forme, et celle-là ne
        # dit pas laquelle des deux composantes s'applique. Elle reste non
        # tranchée ; voir `compose`.
        plafond_ad_valorem = None
        brut = str(row.get("raw_value") or "")
        borne = re.search(r"maximum of\s+([\d]+(?:[.,][\d]+)?)\s*%", brut, re.I)
        if borne and specifique:
            plafond_ad_valorem = float(borne.group(1).replace(",", "."))
            taux = None  # 96 % est la BORNE, pas le taux : ne pas le liquider
            compose = False
        if specifique and row.get("rate_pct") is None:
            taux = None
        out.append(
            _droit(
                code,
                libelle,
                taux,
                row.get("base") or row.get("assiette"),
                row.get("source") or source_defaut,
                note=row.get("note"),
                specifique=specifique,
                qualite=row.get("source_quality"),
                classification=row.get("classification_source"),
            )
        )
        if plafond_ad_valorem is not None:
            out[-1]["plafond_ad_valorem_pct"] = plafond_ad_valorem
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
                if d["taux"] is None and d.get("specifique"):
                    prefs[regime] = {
                        "taux": None,
                        "specifique": lire_specifique(d["specifique"])
                        or {
                            "brut": str(d["specifique"]),
                            "montant": None,
                            "motif": "expression non lisible",
                        },
                    }
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
            if d["specifique"] and d["taux"] is None:
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

    # Les compteurs s'incrémentaient PAR LIGNE LUE. Deux lignes qui portent le
    # même code sont comptées deux fois et servies une seule : le compteur
    # annonçait donc plus de positions que le socle n'en porte, et c'est ce qui
    # a masqué la perte de 349 positions libyennes rabattues sur le SH6.
    # Ils comptent désormais ce qui est RÉELLEMENT SERVI.
    compteurs["positions"] = len(positions)
    compteurs["droits"] = sum(len(p.get("droits") or []) for p in positions.values())
    compteurs["droits_composes"] = sum(
        1 for p in positions.values() for d in p.get("droits") or [] if d.get("compose")
    )
    compteurs["droits_liquidables"] = sum(
        1
        for p in positions.values()
        for d in p.get("droits") or []
        if not d.get("compose")
        and d.get("assiette")
        and (d.get("taux") is not None or d.get("specifique"))
    )
    compteurs["positions_liquidables"] = sum(
        1
        for p in positions.values()
        if (p.get("droits") or [])
        and all(
            not d.get("compose")
            and d.get("assiette")
            and (d.get("taux") is not None or d.get("specifique"))
            for d in p["droits"]
        )
    )

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
