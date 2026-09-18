"""Un taux publié à 0 % est une donnée, pas une absence.

Un zéro au tarif n'est presque jamais du bruit : c'est une EXONÉRATION, et elle
se concentre là où les États en accordent — produits pharmaceutiques (75 % des
positions du chapitre 30 portent un droit nul), engrais (66 %), aéronefs (48 %),
livres (47 %), instruments médicaux, céréales.

Le supprimer à la collecte fait donc disparaître l'information la plus politique
du tarif, et la position se présente ensuite comme n'ayant AUCUN prélèvement —
ce qui se lit « on ne sait pas » au lieu de « c'est en franchise ».

Ce défaut a déjà frappé trois fois (Éthiopie, où 1 368 zéros sont perdus sans
retour ; Ghana ; Zambie) et dormait dans deux collecteurs de plus (Sénégal,
CEDEAO). Ces tests interdisent qu'il revienne : la seule question qu'un
collecteur a le droit de poser est `is None`, jamais `> 0`.
"""

import ast
import pathlib

import pytest

RACINE = pathlib.Path(__file__).resolve().parents[1]
COLLECTEURS = sorted((RACINE / "crawlers").rglob("*.py"))

# Ce qui, dans un nom, désigne un taux ou un montant perçu.
INDICES = ("rate", "taux", "duty", "droit", "levy", "vat", "tva", "excise", "accise")


def _designe_un_taux(noeud: ast.AST) -> bool:
    """Le nœud nomme-t-il un taux ? (`vat_rate`, `row["dd_rate"]`, `x.taux`…)"""
    if isinstance(noeud, ast.Name):
        cible = noeud.id
    elif isinstance(noeud, ast.Attribute):
        cible = noeud.attr
    elif isinstance(noeud, ast.Subscript):
        cle = noeud.slice
        cible = cle.value if isinstance(cle, ast.Constant) else ""
        if not isinstance(cible, str):
            return False
    else:
        return False
    return any(i in cible.lower() for i in INDICES)


def _comparaisons_a_zero(arbre: ast.AST):
    """Rend les comparaisons `<taux> > 0` / `>= 0.0001` et assimilées."""
    trouve = []
    for n in ast.walk(arbre):
        if not isinstance(n, ast.Compare) or len(n.ops) != 1:
            continue
        op, droite = n.ops[0], n.comparators[0]
        if not isinstance(op, ast.Gt):
            continue
        if not (isinstance(droite, ast.Constant) and droite.value == 0):
            continue
        if _designe_un_taux(n.left):
            trouve.append((n.lineno, ast.unparse(n)))
    return trouve


@pytest.mark.parametrize("chemin", COLLECTEURS, ids=lambda p: p.name)
def test_aucun_collecteur_ne_jette_un_taux_nul(chemin):
    """`> 0` sur un taux confond « publié à zéro » et « non publié »."""
    source = chemin.read_text(encoding="utf-8")
    fautes = _comparaisons_a_zero(ast.parse(source))
    assert not fautes, (
        f"{chemin.relative_to(RACINE)} écarte un taux au motif qu'il vaut 0 :\n"
        + "\n".join(f"  ligne {ligne} : {texte}" for ligne, texte in fautes)
        + "\n\nUn taux publié à 0 % est une exonération, donc une donnée. "
        "La seule absence est `None` — écrire `is not None`."
    )


def test_le_garde_reconnait_bien_le_motif_fautif():
    """Contrôle négatif : sans lui, le test passerait sur n'importe quoi."""
    fautif = ast.parse("if vat_rate > 0:\n    emettre(vat_rate)\n")
    assert _comparaisons_a_zero(fautif), "le motif fautif doit être détecté"

    correct = ast.parse("if vat_rate is not None:\n    emettre(vat_rate)\n")
    assert not _comparaisons_a_zero(correct), "`is not None` est la forme juste"

    # Un seuil qui ne porte pas sur un taux ne doit pas être happé.
    hors_sujet = ast.parse("if len(positions) > 0:\n    pass\n")
    assert not _comparaisons_a_zero(hors_sujet), "faux positif sur un décompte"
