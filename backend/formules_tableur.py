"""Neutralisation des formules de tableur dans les exports CSV et XLSX (audit M5).

Excel, LibreOffice et Google Sheets évaluent comme une formule une cellule
texte qui commence par « = », « + », « - », « @ », une tabulation ou un retour
chariot (« injection CSV ») : un `=HYPERLINK(...)` piégé glissé dans un code
pays ou une description s'exécuterait chez celui qui ouvre le fichier. Une
apostrophe en tête fait lire la cellule comme du texte.

Résidu accepté : un CSV ouvert avec le séparateur « ; » (Excel en français)
peut couper un champ sur un « ; » intérieur, devant un « = » non neutralisé.
"""

_DEBUTS_FORMULE = ("=", "+", "-", "@", "\t", "\r")


def neutraliser_formule(valeur):
    """Préfixe d'une apostrophe un texte qui serait lu comme une formule.

    Seules les chaînes de plus d'un caractère changent : un « - » ou un « + »
    seul (case vide d'un tarif) reste tel quel. Nombres, None, booléens et
    listes sont rendus inchangés : un nombre négatif reste un nombre.
    """
    if isinstance(valeur, str) and len(valeur) > 1 and valeur.startswith(_DEBUTS_FORMULE):
        return "'" + valeur
    return valeur
