# -*- coding: utf-8 -*-
"""L'inventaire fiscal doit lire les clés réelles, et garder la source la plus riche.

Deux défauts de cet inventaire ont produit des chiffres publiés qui étaient
faux, et aucun test ne les couvrait :

  - la clé de code n'était lue que sous le nom « code », alors que dix-neuf pays
    CEDEAO et CEMAC écrivent « tax_code » et le schéma canonique v4 « tax ».
    117 197 entrées ressortaient « à code vide » ; il y en a 6 086 ;
  - la déduplication traitait la collection compacte « taxes » avant
    « taxes_detail », gardant un taux nu au lieu d'un taux avec son assiette.
    442 961 assiettes publiées par la source étaient déclarées absentes.

Un refactor peut rétablir l'un ou l'autre en silence. Ces tests l'empêchent.
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from tax_coverage_inventory import declared_base, tax_entries  # noqa: E402


def _codes(position: dict) -> list[str]:
    return [code for code, _label, _value in tax_entries(position)]


def test_les_trois_orthographes_de_la_cle_de_code_sont_lues():
    """« code », « tax_code » et « tax » désignent la même chose."""
    for cle in ("code", "tax_code", "tax"):
        position = {"taxes_detail": [{cle: "DD", "rate": 20.0}]}
        assert _codes(position) == ["DD"], cle


def test_un_code_absent_reste_vide_sans_etre_invente():
    """Ne pas lire une clé est un défaut ; en inventer une en serait un pire."""
    position = {"taxes_detail": [{"rate": 20.0}]}
    assert _codes(position) == [""]


def test_la_collection_detaillee_prime_sur_la_compacte():
    """Le cas CEDEAO : mêmes taxes des deux côtés, l'assiette d'un seul côté.

    C'est l'ordre qui déplace 442 961 classifications. Inversé, l'entrée
    compacte est vue la première, marque le code comme traité, et l'entrée
    riche est écartée comme doublon — l'assiette publiée devient absente.
    """
    position = {
        "taxes": {"DD": 20.0},
        "taxes_detail": [
            {"tax_code": "DD", "tax_name": "Droit de Douane", "rate": 20.0, "base": "CIF"}
        ],
    }
    entrees = tax_entries(position)
    premier_dd = next(valeur for code, _label, valeur in entrees if code == "DD")
    assert declared_base(premier_dd) == "CIF", (
        "la première entrée DD rencontrée doit être celle qui porte l'assiette : "
        "c'est elle que la déduplication retient"
    )
