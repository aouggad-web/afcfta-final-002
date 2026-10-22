"""Statuts des formalités administratives, et sources qui les publient de
façon exhaustive. Partagés par la consultation du socle (routes/consultation.py)
et l'ancien service (services/authentic_tariff_service.py)."""

#: États d'une demande de formalités. Les trois se confondaient en une liste
#: vide, et cette confusion est la plus coûteuse du produit : une absence
#: d'information n'est pas une absence d'obligation.
FORMALITES_DOCUMENTEES = "DOCUMENTEES"
FORMALITES_AUCUNE_PARTICULIERE = "AUCUNE_FORMALITE_PARTICULIERE"
FORMALITES_NON_ETABLIES = "NON_ETABLIES"
FORMALITES_POSITION_INTROUVABLE = "POSITION_INTROUVABLE"

#: PAYS DONT LA SOURCE PUBLIE SES FORMALITÉS DE FAÇON EXHAUSTIVE.
#:
#: Pour ces pays — et pour eux seuls — une liste vide n'est PAS une lacune :
#: c'est un constat de la source, qui publie le bloc quand une formalité
#: particulière existe et ne publie rien quand il n'y en a pas. Le produit dit
#: alors quelque chose de POSITIF au lieu d'une réserve.
#:
#: Ce que cet état n'affirme toujours PAS : que l'importation soit dispensée de
#: toute obligation. Il dit qu'aucune formalité PARTICULIÈRE ne frappe cette
#: marchandise. Les obligations générales du pays — déclaration en douane,
#: domiciliation bancaire — ne sont volontairement pas portées par le produit :
#: elles s'appliquent à toute importation sans distinction de position, et
#: l'opérateur qui consulte une position tarifaire les connaît. Décision du
#: propriétaire, prise le 21/09/2026 — déclarée ici pour qu'elle ne soit pas
#: reprise plus tard comme un oubli.
#:
#: La « déclaration d'importation du produit » algérienne (code 910) n'est pas
#: l'une de ces obligations générales : c'est une demande adressée au contrôle
#: de la qualité du ministère du Commerce, attachée à des marchandises
#: précises — une formalité PARTICULIÈRE, servie avec son code comme les autres.
#:
#: Pour ces pays, formalites_et_statut lit la fiche de la position, jamais
#: l'agrégat SH6 : la formalité d'une position ne vaut pas pour ses voisines
#: du même SH6.
#:
#: Chaque entrée exige sa preuve, relevée sur le portail. Ne jamais ajouter un
#: pays ici « par analogie » : c'est exactement la généralisation que le Maroc a
#: démentie sur les droits nuls.
SOURCES_EXHAUSTIVES_FORMALITES = {
    "DZA": (
        "La fiche « sous-position » de l'e-service DGD publie le tableau "
        "« Formalités Administratives Particulières » (code, document) quand "
        "une formalité particulière frappe la position, et aucun tableau sinon. "
        "Vérifié sur la fiche même de chaque position : relevé des 03 et 04/10/2026, "
        "17 345 fiches sur 17 345 codes officiels, 8 671 avec tableau, 8 674 "
        "sans (data/dza/releve_dgd.json)."
    ),
}

#: Réserves écrites dans la réponse plutôt que laissées à chaque écran.
RESERVES_FORMALITES = {
    # Un CONSTAT, pas une réserve : la source publie ses formalités quand
    # elles existent, et n'en publie aucune ici. Dire « non établies »
    # serait sous-estimer ce que l'on sait.
    FORMALITES_AUCUNE_PARTICULIERE: (
        "Aucune formalité administrative particulière n'est publiée pour "
        "cette position. Les obligations générales à l'importation "
        "demeurent."
    ),
    FORMALITES_NON_ETABLIES: (
        "Formalités non établies pour cette position. Une absence "
        "d'information n'est pas une absence d'obligation : vérifier "
        "auprès de l'administration douanière de destination."
    ),
    FORMALITES_POSITION_INTROUVABLE: (
        "Position introuvable dans les données servies pour ce pays : "
        "aucune formalité n'a pu être recherchée."
    ),
}
