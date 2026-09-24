"""Une désignation bilingue rendue en texte — commune aux deux chemins de calcul.

Les crawls conservent la désignation telle que publiée, sous la forme
``{fr, en, ar, pt, full_fr, verbatim}`` ; plusieurs sources ne publient qu'en
anglais, ``fr`` y est vide. Servie telle quelle, l'interface recevait un objet
là où elle attend du texte, et React plantait au rendu (« Objects are not
valid as a React child ») : écran vide après le calcul.
"""


def texte_designation(valeur, langue="fr"):
    """La langue demandée si elle existe, sinon le texte publié (``verbatim``).

    Rien n'est traduit ni inventé : une désignation publiée en anglais reste
    en anglais.
    """
    if isinstance(valeur, dict):
        return (
            valeur.get(langue)
            or valeur.get("verbatim")
            or valeur.get("en")
            or valeur.get("fr")
            or ""
        )
    return valeur
