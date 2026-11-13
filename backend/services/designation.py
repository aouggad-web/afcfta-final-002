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


def designation_publiee(valeur):
    """La désignation que le tarif du pays publie, sans les libellés que le socle
    lui emprunte (``langues_empruntees``).

    Pour l'Angola, le Mozambique et l'Égypte, le socle ajoute un libellé SH6
    français et anglais emprunté à un autre tarif. Il décrit le SH6, pas la ligne
    servie, et peut porter le niveau national du tarif qui l'a fourni (le SH6
    1006.10 se lit « de semence » au tarif CEDEAO). ``texte_designation`` lit la
    langue demandée d'abord : il le servait comme la désignation du pays, et
    l'écran disait « riz de semence » d'une position angolaise de riz paddy.
    Sans lui, le texte publié par le tarif (``verbatim``) fait foi.
    """
    if not isinstance(valeur, dict):
        return valeur
    empruntees = valeur.get("langues_empruntees") or []
    return {cle: texte for cle, texte in valeur.items() if cle not in empruntees}


def libelle_sh6_emprunte(valeur):
    """Les libellés que le socle emprunte, à part de la désignation, chacun avec
    le tarif d'où il vient, et le niveau de l'emprunt. ``None`` si rien n'est
    emprunté : l'emprunt se déclare, il ne se glisse pas dans la désignation."""
    if not isinstance(valeur, dict):
        return None
    langues = [langue for langue in valeur.get("langues_empruntees") or [] if valeur.get(langue)]
    if not langues:
        return None
    emprunt = {"niveau": valeur.get("niveau_libelle_emprunte") or "SH6"}
    for langue in langues:
        emprunt[langue] = valeur[langue]
        emprunt[f"{langue}_source"] = valeur.get(f"{langue}_source")
    return emprunt
