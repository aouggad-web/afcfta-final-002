"""
Le collecteur UNIDO ne collecte jamais sans vérification TLS.

POURQUOI CE GARDE-FOU
----------------------
Une première version de `_ssl_context()` basculait en ``CERT_NONE`` quand la
vérification échouait, au motif que « le sandbox manque de bundle CA, pas le
site ». Le raisonnement est invérifiable de l'intérieur — un certificat refusé
faute d'autorité et un certificat refusé parce qu'il est faux se présentent
exactement pareil — et les conséquences sont asymétriques : ce script est fait
pour être rejoué pays par pays, et une statistique entrée par un canal non
authentifié ne se distingue plus d'une statistique saine une fois versée.

C'est corrigé. Ce fichier existe pour que ça le reste : le correctif sans
garde-fou se réintroduit au premier refactor, sans que rien ne tombe.

CE QUE CES TESTS NE FONT PAS
-----------------------------
Ils ne présument RIEN de la forme du correctif. Une version antérieure de ce
fichier vérifiait la signature d'une fonction `_probe` et l'existence d'une
liste de bundles candidats — des détails de MON implémentation, pas la règle.
Confrontés à une autre implémentation, également correcte et plus simple, trois
de ces quatre tests tombaient à tort. Un garde-fou couplé à une structure ne
garde pas une règle : il gêne quiconque veut l'écrire autrement.

Ne restent donc que deux assertions, portant sur l'invariant lui-même.
"""

import io
import os
import sys
import tokenize

_backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

_SCRIPT = os.path.join(_backend_dir, "scripts", "fetch_unido_indstat.py")


def _source() -> str:
    with open(_SCRIPT, encoding="utf-8") as fh:
        return fh.read()


def _executable_source() -> str:
    """Le source PRIVÉ de ses commentaires et de ses chaînes.

    Chercher « CERT_NONE » dans le fichier brut attraperait la docstring qui
    explique pourquoi on ne l'utilise plus — un test qui interdit d'expliquer
    ce qu'il interdit est un mauvais test. On compare donc sur les seuls
    jetons réellement exécutés.
    """
    jetons = []
    with io.open(_SCRIPT, "rb") as fh:
        for tok in tokenize.tokenize(fh.readline):
            if tok.type in (tokenize.COMMENT, tokenize.STRING):
                continue
            jetons.append(tok.string)
    return " ".join(jetons)


def test_verification_is_never_disabled():
    code = _executable_source()
    assert "CERT_NONE" not in code, (
        "le collecteur désactive la vérification TLS : une donnée entrée par "
        "un canal non authentifié ne se distingue plus d'une donnée saine"
    )
    assert "check_hostname" not in code, (
        "le collecteur désactive la vérification du nom d'hôte"
    )
    # La suppression bandit qui accompagnait le repli n'a plus lieu d'être ;
    # elle vit dans un commentaire, donc on la cherche dans le brut.
    assert "nosec B501" not in _source()


def test_a_certificate_failure_ends_the_collection():
    """L'échec doit être FRANC, où qu'il soit traité.

    Sans cette assertion, remplacer le refus par une relance silencieuse
    passerait le test précédent tout en laissant la collecte tourner en rond
    sur un canal douteux. On vérifie que le script NOMME le cas et qu'il en
    sort, sans présumer dans quelle fonction ni sous quelle forme.
    """
    src = _source()
    assert "CERTIFICATE_VERIFY_FAILED" in src, (
        "le script ne distingue pas l'échec de certificat des autres erreurs "
        "réseau : il le relancerait comme un 5xx passager"
    )
    code = _executable_source()
    assert "SystemExit" in code, (
        "un échec de certificat doit terminer la collecte, pas la faire "
        "recommencer"
    )
