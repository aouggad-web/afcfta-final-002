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
}


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
        "note": note,
        "classification_source": classification,
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
        specifique = row.get("specific_value")
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
    return out


def lignes_du_fichier(donnees):
    """Rendre (code, designation, unite, droits_bruts) pour les six schémas."""
    source_defaut = donnees.get("source") or donnees.get("source_name") or ""

    for cle in ("positions", "sub_positions"):
        for ligne in donnees.get(cle, []) or []:
            if not isinstance(ligne, dict):
                continue
            code = nettoyer_code(
                ligne.get("code_clean"),
                ligne.get("hs_code"),
                ligne.get("code"),
                ligne.get("code_raw"),
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
            yield (
                code,
                ligne.get("designation") or ligne.get("name") or ligne.get("description") or "",
                ligne.get("unit") or ligne.get("statistical_unit"),
                droits,
                ligne.get("source") or source_defaut,
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
            )


# ── Construction ──────────────────────────────────────────────────────────────
def sha256(chemin: str) -> str:
    h = hashlib.sha256()
    with open(chemin, "rb") as f:
        for bloc in iter(lambda: f.read(1 << 20), b""):
            h.update(bloc)
    return h.hexdigest()


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
    with open(chemin, encoding="utf-8") as f:
        donnees = json.load(f)

    profil = assiettes_pays.get(iso, {})
    assiettes_codees = profil.get("taxes", {})
    assiettes_fichier = assiettes_du_fichier(donnees)

    positions = {}
    compteurs = {
        "positions": 0,
        "droits": 0,
        "droits_liquidables": 0,
        "positions_liquidables": 0,
        "preferentiels": 0,
        "preferentiels_specifiques": 0,
        "taux_indisponibles": 0,
        "assiettes_source": 0,
        "assiettes_fichier": 0,
        "assiettes_table": 0,
        "assiettes_indisponibles": 0,
        "sans_designation": 0,
        "droits_specifiques": 0,
        "classification_estimee": 0,
    }
    familles_vues = set()

    for code, designation, unite, droits, source_ligne in lignes_du_fichier(donnees):
        retenus, prefs = [], {}
        position_complete = True
        for d in droits:
            if d.pop("_preferentiel", None) is not None:
                # Une colonne préférentielle est conservée telle quelle, sous son
                # propre régime. Elle n'entre jamais dans la cascade NPF.
                regime = PREFERENTIELS[_norm(d["code_source"])]
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
            if d["specifique"] and d["taux"] is None:
                # Un droit spécifique se liquide à la quantité, jamais sur la
                # valeur. Si l'assiette héritée dit « CIF », elle décrit le
                # droit ad valorem de la ligne, pas celui-ci : la laisser
                # ferait lire « 8c/kg » comme « 8 % ».
                d["assiette"] = "xQTE"
                d["assiette_origine"] = "droit_specifique"
                d["plafond"] = None
                d["specifique"] = lire_specifique(d["specifique"]) or {
                    "brut": str(d["specifique"]),
                    "montant": None,
                    "motif": "expression non lisible",
                }
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
            if d["assiette"] and (d["taux"] is not None or specifique_lisible):
                compteurs["droits_liquidables"] += 1
            else:
                position_complete = False
            retenus.append({k: v for k, v in d.items() if v is not None})

        retenus.sort(key=lambda d: ORDRE_FAMILLES.index(d.get("famille", "autre")))
        if not designation:
            compteurs["sans_designation"] += 1
        positions[code] = {
            "designation": designation,
            "hs6": code[:6],
            "chapitre": code[:2],
            "droits": retenus,
        }
        if unite:
            positions[code]["unite"] = unite
        if prefs:
            positions[code]["preferentiels"] = prefs
        if source_ligne:
            positions[code]["source"] = source_ligne
        compteurs["positions"] += 1
        compteurs["droits"] += len(retenus)
        if retenus and position_complete:
            compteurs["positions_liquidables"] += 1

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
