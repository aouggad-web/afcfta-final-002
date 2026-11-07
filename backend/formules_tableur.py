"""Neutralisation des formules de tableur dans les exports CSV et XLSX (audit M5).

Excel, LibreOffice et Google Sheets évaluent comme une formule une cellule
texte qui commence par « = », « + », « - », « @ », une tabulation ou un retour
chariot (« injection CSV ») : un `=HYPERLINK(...)` piégé glissé dans un code
pays ou une description s'exécuterait chez celui qui ouvre le fichier. Une
apostrophe en tête fait lire la cellule comme du texte.

Un CSV à virgules ouvert avec le séparateur « ; » (Excel en français) est
coupé à chaque « ; » et à chaque saut de ligne, même entre guillemets : chaque
morceau commence une cellule, d'où `neutraliser_formule_csv`.
"""

import re

_DEBUTS_FORMULE = ("=", "+", "-", "@", "\t", "\r")
# Après un « ; » ou un saut de ligne : guillemets éventuels, puis début de
# formule. Seul reste tel quel un signe suivi d'un « ; » ou d'un saut de ligne :
# en fin de champ, le morceau continue sur le champ suivant.
_DEBUT_INTERIEUR = re.compile(r'([;\r\n])(?="*[=+\-@\t\r](?![;\r\n]))')


def neutraliser_formule(valeur):
    """Préfixe d'une apostrophe un texte qui serait lu comme une formule.

    Seules les chaînes de plus d'un caractère changent : un « - » ou un « + »
    seul (case vide d'un tarif) reste tel quel. Nombres, None, booléens et
    listes sont rendus inchangés : un nombre négatif reste un nombre.
    """
    if isinstance(valeur, str) and len(valeur) > 1 and valeur.startswith(_DEBUTS_FORMULE):
        return "'" + valeur
    return valeur


def neutraliser_formule_csv(valeur, debut_de_ligne=False):
    """Comme `neutraliser_formule`, et aussi après chaque « ; » ou saut de ligne.

    Réservée aux CSV : une cellule XLSX n'est jamais coupée. Une liste ou un
    dictionnaire (`known_data_gaps`) est écrit par le module csv sous forme de
    texte : il est jugé sur ce texte, comme un tableau dans `escapeCell`
    (ExportTools.jsx).

    `debut_de_ligne` : premier champ d'une ligne. Son morceau continue, après
    la virgule, sur le champ suivant (`-,1+cmd|' /C calc'!A0`) : un signe seul
    ou un nombre négatif y est neutralisé lui aussi.
    """
    if isinstance(valeur, (list, tuple, dict, set)):
        valeur = str(valeur)
    if (
        debut_de_ligne
        and isinstance(valeur, (str, int, float))
        and str(valeur).startswith(_DEBUTS_FORMULE)
    ):
        valeur = "'" + str(valeur)
    valeur = neutraliser_formule(valeur)
    if isinstance(valeur, str):
        return _DEBUT_INTERIEUR.sub(r"\1'", valeur)
    return valeur
