"""
Accès au socle de calcul — chantier L3.

Le socle est un artefact de construction : il est produit hors ligne par
``scripts/build_socle.py`` depuis les fichiers du crawler, et son empreinte est
consignée dans ``backend/socle/MANIFESTE.json``.

Ce module est le seul point d'entrée vers lui, et il impose une règle : **un
fichier dont l'empreinte ne correspond pas au manifeste n'est pas servi.** Un
socle périmé devient inerte, au lieu de rendre en silence des montants qui ne
correspondent plus à la donnée collectée.

**Portée de cette garantie :** deux empreintes sont vérifiées au chargement,
pas une seule — celle du socle contre le manifeste, et celle du fichier
source du crawl (versionné, donc toujours présent) contre l'empreinte que le
manifeste a enregistrée au moment de la construction. La première seule
laisserait passer un crawl remplacé sans reconstruction : deux fichiers de
socle identiques, une source différente entre-temps. Les deux vérifications
n'ont lieu qu'au chargement d'un pays absent du cache — pas à chaque requête,
ce que le cache existe précisément pour éviter.

La remontée au parent SH6 est possible mais jamais implicite : le niveau réel
de la position servie accompagne toujours le résultat.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
from collections import OrderedDict
from typing import Any, Dict, Optional, Tuple

RACINE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SOCLE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "socle")
MANIFESTE = os.path.join(SOCLE_DIR, "MANIFESTE.json")
DEVISES = os.path.join(SOCLE_DIR, "devises_pays.json")
TVA_NATIONALE = os.path.join(SOCLE_DIR, "tva_nationale.json")

_devises_cache: Optional[Dict[str, str]] = None
_tva_cache: Optional[Dict[str, Dict[str, Any]]] = None

#: Les fichiers pays pèsent de 3 à 60 Mo. On en garde quelques-uns en mémoire,
#: pas les cinquante-quatre.
_MAX_PAYS_EN_CACHE = 4
_cache: "OrderedDict[str, dict]" = OrderedDict()
_manifeste: Optional[dict] = None


class SocleIndisponible(RuntimeError):
    """Le socle n'est pas là, ou ne correspond plus à son manifeste."""


def _iso3(valeur: str) -> str:
    code = (valeur or "").strip().upper()
    if not re.fullmatch(r"[A-Z]{3}", code):
        raise ValueError(f"code pays invalide : {valeur!r}")
    return code


def manifeste() -> dict:
    global _manifeste
    if _manifeste is None:
        if not os.path.exists(MANIFESTE):
            raise SocleIndisponible("Socle absent. Le régénérer : python3 scripts/build_socle.py")
        with open(MANIFESTE, encoding="utf-8") as f:
            _manifeste = json.load(f)
    return _manifeste


def _sha256(chemin: str) -> str:
    h = hashlib.sha256()
    with open(chemin, "rb") as f:
        for bloc in iter(lambda: f.read(1 << 20), b""):
            h.update(bloc)
    return h.hexdigest()


def charger(iso3: str) -> dict:
    """Charger un pays du socle, après vérification de son empreinte."""
    iso3 = _iso3(iso3)
    if iso3 in _cache:
        _cache.move_to_end(iso3)
        return _cache[iso3]

    entree = manifeste().get("pays", {}).get(iso3)
    if entree is None:
        raise SocleIndisponible(f"{iso3} n'est pas au socle")

    chemin = os.path.join(SOCLE_DIR, entree["fichier"])
    if not os.path.exists(chemin):
        raise SocleIndisponible(
            f"{iso3} : fichier de socle absent. Le régénérer : " "python3 scripts/build_socle.py"
        )
    empreinte = _sha256(chemin)
    if empreinte != entree["socle_sha256"]:
        raise SocleIndisponible(
            f"{iso3} : le socle ne correspond plus à son manifeste "
            f"(attendu {entree['socle_sha256'][:12]}, trouvé {empreinte[:12]}). "
            "Il n'est pas servi — le régénérer : python3 scripts/build_socle.py"
        )

    # Le socle peut correspondre à son propre manifeste tout en datant d'un
    # crawl que la collecte a depuis remplacé sans reconstruction : deux
    # empreintes identiques, une source différente. Le fichier source est
    # versionné (backend/data/crawled/), donc toujours présent au chargement,
    # pas seulement en développement — revérifier son empreinte ici coûte le
    # même ordre de grandeur que celle du socle déjà payée à chaque défaut de
    # cache, pas un rehachage à chaque requête.
    source_chemin = os.path.join(RACINE, entree["source_fichier"])
    if os.path.exists(source_chemin):
        empreinte_source = _sha256(source_chemin)
        if empreinte_source != entree["source_sha256"]:
            raise SocleIndisponible(
                f"{iso3} : le crawl source a changé depuis la construction du socle "
                f"(attendu {entree['source_sha256'][:12]}, trouvé {empreinte_source[:12]}). "
                "Il n'est pas servi — le régénérer : python3 scripts/build_socle.py"
            )

    with open(chemin, encoding="utf-8") as f:
        donnees = json.load(f)
    _cache[iso3] = donnees
    _cache.move_to_end(iso3)
    while len(_cache) > _MAX_PAYS_EN_CACHE:
        _cache.popitem(last=False)
    return donnees


def pays_servis() -> Dict[str, dict]:
    """Les pays du socle, avec leur état de couverture."""
    return {
        iso: {
            "etat": entree["etat"],
            "origine": entree["origine"],
            "positions": entree["compteurs"]["positions"],
            "familles": entree.get("familles", []),
            "collecte": entree.get("collecte"),
        }
        for iso, entree in manifeste().get("pays", {}).items()
    }


def devise_nationale(iso3: str) -> Optional[str]:
    """Devise (ISO 4217) dans laquelle le tarif du pays publie ses droits
    spécifiques. ``None`` si le pays n'est pas dans la table plutôt qu'une
    devise devinée."""
    global _devises_cache
    if _devises_cache is None:
        if not os.path.exists(DEVISES):
            _devises_cache = {}
        else:
            with open(DEVISES, encoding="utf-8") as f:
                _devises_cache = json.load(f).get("pays", {})
    return _devises_cache.get(_iso3(iso3))


def tva_nationale(iso3: str) -> Optional[Dict[str, Any]]:
    """Taux de TVA établi sur source primaire pour un pays dont le crawl n'en
    porte aucun, ou ``None``.

    Cette table ne complète qu'une famille **entièrement absente** de la
    source. Elle ne corrige jamais un taux collecté position par position :
    une donnée nationale moyenne ne vaut pas mieux qu'une donnée de ligne, et
    la substituer ferait reculer la précision là où elle existe.
    """
    global _tva_cache
    if _tva_cache is None:
        if not os.path.exists(TVA_NATIONALE):
            _tva_cache = {}
        else:
            with open(TVA_NATIONALE, encoding="utf-8") as f:
                _tva_cache = json.load(f).get("pays", {})
    return _tva_cache.get(_iso3(iso3))


def normaliser_code(code: str) -> str:
    chiffres = re.sub(r"\D", "", str(code or ""))
    if len(chiffres) < 6:
        raise ValueError(f"code SH invalide : {code!r} (six chiffres au minimum)")
    return chiffres


def position(iso3: str, code: str) -> Tuple[Dict[str, Any], dict]:
    """Rendre (position, provenance) pour un code national ou SH6.

    La recherche est explicite et son résultat le dit : le code exact d'abord,
    puis le parent SH6 s'il existe. Aucune remontée au chapitre, aucune valeur
    de repli : un code introuvable lève, il ne rend pas une position voisine.

    Le niveau annoncé se lit sur le code **demandé**, pas sur le fait qu'une
    position ait été trouvée directement : un code à six chiffres reste
    « hs6 » même quand il correspond à une clé du socle, parce qu'il n'est
    pas une sous-position nationale — le confondre ferait annoncer
    `tariff_precision: sub_position` là où seule une moyenne SH6 est servie.
    """
    iso3 = _iso3(iso3)
    code = normaliser_code(code)
    donnees = charger(iso3)
    positions = donnees.get("positions", {})

    niveau = "national" if len(code) > 6 else "hs6"
    trouve = positions.get(code)
    if trouve is None and niveau == "national":
        hs6 = code[:6]
        trouve, niveau = positions.get(hs6), "hs6"
    if trouve is None:
        raise KeyError(
            f"{iso3}/{code} : position absente du socle "
            f"({donnees.get('compteurs', {}).get('positions', 0)} positions servies)"
        )

    provenance = {
        "iso3": iso3,
        "code_demande": code,
        "niveau": niveau,
        "source": donnees.get("source", {}),
        "couverture": donnees.get("couverture", {}),
        "assiettes": {
            "reference_legale": donnees.get("assiettes", {}).get("reference_legale"),
            "origine": donnees.get("assiettes", {}).get("origine"),
        },
        "devise_nationale": devise_nationale(iso3),
        "socle_version": donnees.get("socle_version"),
    }
    return trouve, provenance


def vider_cache() -> None:
    """Oublier les pays chargés, le manifeste et les tables (utile aux tests)."""
    global _manifeste, _devises_cache, _tva_cache
    _cache.clear()
    _manifeste = None
    _devises_cache = None
    _tva_cache = None
