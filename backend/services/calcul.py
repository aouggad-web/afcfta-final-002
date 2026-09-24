"""
Moteur de liquidation — chantier L2.

Une fonction, six primitives d'assiette, un modificateur. Aucune connaissance
par pays : tout ce que le moteur sait d'un pays lui vient du socle.

Les six primitives, et rien d'autre :

===========================  ================================================
``CIF``                      la valeur en douane
``CIF+<CODES>``              la valeur en douane augmentée du montant des
                             droits nommés (``CIF+DD+TCI``), ou de tous les
                             prélèvements d'entrée (``CIF+TOUS_SAUF_TVA``,
                             ``CIF+TOUS_SAUF_SOI``)
``FOB``                      la valeur FOB — la valeur en douane des pays
                             SACU, où le fret et l'assurance internationaux
                             sont exclus (Act 91/1964 s.65-67 ; fiche
                             ``SACU_assiette_DD_2026-09-17.json``). Elle ne
                             se déduit JAMAIS de la valeur CIF : la part du
                             fret et de l'assurance n'est pas connue du
                             moteur. Absente, le droit reste indisponible
                             (``VALEUR_FOB_REQUISE``) plutôt qu'assumé CIF
                             — une base CIF devinée surestimerait le droit
                             d'un montant crédible et faux.
``SOMME(TOUS_SAUF_SOI)``     la somme des autres droits, **sans** la valeur
``%<CODE>``                  un pourcentage du *montant* d'un autre droit,
                             désigné par son code (``%DD``)
``xQTE``                     droit spécifique : montant unitaire × quantité
===========================  ================================================

Plus un modificateur, ``plafond``, qui borne l'assiette.

Trois règles gouvernent tout le reste :

1. **Un élément manquant ne vaut pas zéro.** Une ligne sans taux, sans assiette
   ou sans quantité ne produit pas de montant : elle produit un manque nommé, et
   le total est marqué ``PARTIEL``.
2. **Un total partiel se dit.** Un total qui omet une accise n'est pas prudent,
   il est faux — il doit annoncer ce qu'il omet.
3. **La préférence ne réduit que les prélèvements qu'on lui désigne.** Lesquels
   relève du droit national, pas du moteur : l'Algérie exonère aussi le DAPS
   pour les produits des listes (A) et (B) admis sous ZLECAf (circulaire
   482/2024, partie II-2, citant l'art. 2 de la loi de finances complémentaire
   2018), quand ailleurs seul le droit de douane est démantelé. Le moteur reçoit
   donc la liste des taux préférentiels ; il ne la déduit jamais. Tout ce qui
   n'y figure pas reste dû au taux NPF.
4. **Une position peut être complète et son pays ne pas l'être.** Cinq pays
   SACU liquident un droit de douane sans qu'aucune TVA ne soit jamais tracée
   dans leur source. Sans le savoir, le moteur rendrait « COMPLET » sur une
   position qui n'a simplement rien à liquider en TVA — indiscernable d'un
   pays qui exonère réellement le produit. La couverture du pays (transmise en
   ``couverture``) dégrade alors l'état à ``PARTIEL`` et nomme la famille non
   tracée, avant même de calculer une économie.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from services.designation import texte_designation

#: Le seul code que le moteur connaisse, et il lui vient de la grammaire des
#: assiettes : « CIF + tous les droits **sauf la TVA** » doit savoir laquelle
#: exclure. Tout le reste — quels prélèvements existent, dans quel ordre ils se
#: liquident, sur quelle assiette, et lesquels une préférence remise — vient du
#: socle ou de l'appelant. Aucune méthode nationale n'est figée ici.
FAMILLE_TVA = "tva"

COMPLET = "COMPLET"
INDICATIF = "INDICATIF"
PARTIEL = "PARTIEL"
INDISPONIBLE = "INDISPONIBLE"

#: SOURCES QUI SONT DES MOYENNES, PAS DES TAUX.
#:
#: WITS/UNCTAD-TRAINS publie une moyenne simple des lignes nationales au niveau
#: SH6. C'est une statistique honnête de la Banque mondiale — et ce n'est PAS
#: le droit applicable à une marchandise : aucune déclaration en douane ne se
#: liquide sur une moyenne.
#:
#: Quatre pays en dépendent pour la totalité de leur droit de douane — Comores,
#: Madagascar, São Tomé, Soudan — soit 21 788 droits. Trois d'entre eux
#: rendaient jusqu'ici un total COMPLET : le produit affirmait donc une
#: liquidation entière construite sur un agrégat. Le montant reste servi, avec
#: sa source ; c'est le mot « complet » qui était faux.
SOURCES_STATISTIQUES = ("WITS", "UNCTAD-TRAINS", "TRAINS (")


def _est_moyenne_statistique(source):
    """Vrai si ce taux provient d'un agrégat statistique, non d'un tarif."""
    texte = str(source or "")
    return any(marqueur in texte for marqueur in SOURCES_STATISTIQUES)


CALCULE = "CALCULE"
MANQUE_TAUX = "TAUX_INDISPONIBLE"
MANQUE_ASSIETTE = "ASSIETTE_INDISPONIBLE"
MANQUE_QUANTITE = "QUANTITE_REQUISE"
MANQUE_CHANGE = "TAUX_DE_CHANGE_REQUIS"
MANQUE_COMPOSANT = "ASSIETTE_INCOMPLETE"
#: Valeur FOB exigée par une assiette « FOB » (SACU) et non fournie : la base
#: ne vaut jamais la valeur CIF — déduire le fret de celle-ci en inventerait
#: une. Voir la primitive ``FOB`` en tête de module.
MANQUE_FOB = "VALEUR_FOB_REQUISE"
#: Le tarif publie DEUX composantes pour un même droit — « 40% or 240c/kg »,
#: sur 140 positions sud-africaines — sans que la source dise laquelle
#: s'applique. Le crawl a délibérément gardé le verbatim sans trancher ; le
#: socle ne tranche pas davantage. Servir la seule part ad valorem donnerait un
#: montant crédible et possiblement faux : sur la position 020110, la part
#: spécifique l'emporte dès que la valeur unitaire passe sous 6,00 ZAR/kg.
MANQUE_REGLE_COMPOSEE = "REGLE_COMPOSEE_NON_ETABLIE"


def _facteur_devise_specifique(
    devise_position: Optional[str], devise_cif: Optional[str], taux_de_change: Optional[float]
) -> Optional[float]:
    """Facteur de conversion des droits spécifiques vers la devise de la valeur
    CIF déclarée.

    Un droit spécifique (« 8c/kg », « 0.1 dinars ») est publié dans la devise
    nationale du tarif. L'additionner tel quel à une valeur CIF déclarée dans
    une autre devise mélangerait deux monnaies dans le même total. Rendu :

    - ``1.0`` quand aucune conversion n'est nécessaire (devise inconnue d'un
      côté ou de l'autre, ou les deux devises coïncident) — comportement
      inchangé, aucune régression sur les positions sans ambiguïté ;
    - ``None`` quand une conversion est nécessaire mais qu'aucun taux n'est
      fourni : les droits spécifiques concernés deviennent indisponibles
      plutôt qu'additionnés dans la mauvaise devise ;
    - le taux de change lui-même sinon, à multiplier au montant unitaire.
    """
    if not devise_cif or not devise_position or devise_cif.upper() == devise_position.upper():
        return 1.0
    return taux_de_change


def _montant_unitaire(specifique: Any) -> Optional[float]:
    """Rendre le montant unitaire d'un droit spécifique, déjà ramené à l'unité
    monétaire principale par le socle (« 8c/kg » vaut 0,08 et non 8).

    La forme héritée — une chaîne — est refusée plutôt que devinée : en lire le
    seul nombre multiplierait le droit par cent sur les tarifs publiés en
    centimes, ce qui est toute la SACU.
    """
    if isinstance(specifique, dict):
        montant = specifique.get("montant")
        return float(montant) if isinstance(montant, (int, float)) else None
    return None


def _codes_de_l_assiette(assiette: str) -> List[str]:
    """« CIF+DD+TCI » → ['DD', 'TCI']. Les formes globales rendent []."""
    reste = assiette.split("+", 1)[1] if "+" in assiette else ""
    return [c for c in reste.split("+") if c and not c.startswith("TOUS_")]


def _composants(
    codes: List[str],
    montants: Dict[str, float],
    codes_de_la_position: set,
):
    """Additionner les droits nommés par une assiette.

    Un code que l'assiette nomme peut manquer pour deux raisons opposées, et
    les confondre fausse le montant sans le dire :

    - il **n'existe pas sur cette position** : le prélèvement ne s'y applique
      pas, il ne contribue à rien, et c'est normal ;
    - il **existe mais n'a pas été liquidé** : l'assiette est alors amputée de
      sa part. Le compter pour zéro rendrait un montant trop faible, crédible
      et faux. On refuse de le faire.

    Retourne ``(somme, manquants, sans_objet)``.
    """
    somme = 0.0
    manquants, sans_objet = [], []
    for code in codes:
        if code in montants:
            somme += montants[code]
        elif code in codes_de_la_position:
            manquants.append(code)
        else:
            sans_objet.append(code)
    return somme, manquants, sans_objet


def _assiette_de(
    droit: Dict[str, Any],
    cif: float,
    calcules: List[Dict[str, Any]],
    echecs: List[Dict[str, Any]],
    quantite: Optional[float],
    taux_de_change: Optional[float],
    codes_de_la_position: set,
    valeur_fob: Optional[float] = None,
):
    """Rendre (assiette, manque, détail). Une assiette introuvable ne vaut
    jamais CIF, et une assiette amputée ne se complète jamais par un zéro."""
    assiette = droit.get("assiette")
    detail: Dict[str, Any] = {}
    if not assiette:
        return None, MANQUE_ASSIETTE, detail

    montants = {d["code"]: d["montant"] for d in calcules}

    if assiette == "xQTE":
        if quantite is None:
            return None, MANQUE_QUANTITE, detail
        return quantite, None, detail

    if assiette.startswith("%"):
        # Pourcentage du montant d'un autre droit, quel qu'il soit : le code est
        # dans l'assiette, il n'est pas connu du moteur.
        reference = assiette[1:]
        base, manquants, sans_objet = _composants([reference], montants, codes_de_la_position)
        if manquants or sans_objet:
            return None, MANQUE_COMPOSANT, {"composants_absents": [reference]}
        return base, None, detail

    # Une assiette globale — « tous les droits sauf X » — additionne ce qui a
    # été liquidé. Si un prélèvement qui la compose a échoué, elle est amputée :
    # le compter pour zéro rendrait un montant trop faible, et crédible. Même
    # invariant que pour les assiettes à codes nommés, appliqué ici aussi.
    if assiette == "SOMME(TOUS_SAUF_SOI)":
        rates = [e["code"] for e in echecs]
        if rates:
            return None, MANQUE_COMPOSANT, {"composants_absents": rates}
        base = sum(montants.values())
    elif assiette == "FOB":
        # La valeur en douane SACU exclut fret et assurance internationaux :
        # elle doit être fournie, jamais déduite de la valeur CIF.
        if valeur_fob is None:
            return None, MANQUE_FOB, detail
        base = valeur_fob
    elif assiette == "CIF":
        base = cif
    elif assiette.startswith("CIF+"):
        if "TOUS_SAUF_TVA" in assiette:
            rates = [e["code"] for e in echecs if e["famille"] != FAMILLE_TVA]
            if rates:
                return None, MANQUE_COMPOSANT, {"composants_absents": rates}
            base = cif + sum(d["montant"] for d in calcules if d["famille"] != FAMILLE_TVA)
        elif "TOUS_SAUF_SOI" in assiette:
            rates = [e["code"] for e in echecs]
            if rates:
                return None, MANQUE_COMPOSANT, {"composants_absents": rates}
            base = cif + sum(montants.values())
        else:
            part, manquants, sans_objet = _composants(
                _codes_de_l_assiette(assiette), montants, codes_de_la_position
            )
            if manquants:
                return None, MANQUE_COMPOSANT, {"composants_absents": manquants}
            if sans_objet:
                detail["composants_sans_objet"] = sans_objet
            base = cif + part
    elif assiette.startswith("FOB+"):
        # Même sémantique que « CIF+<CODES> », posée sur la valeur FOB.
        if valeur_fob is None:
            return None, MANQUE_FOB, detail
        part, manquants, sans_objet = _composants(
            _codes_de_l_assiette(assiette), montants, codes_de_la_position
        )
        if manquants:
            return None, MANQUE_COMPOSANT, {"composants_absents": manquants}
        if sans_objet:
            detail["composants_sans_objet"] = sans_objet
        base = valeur_fob + part
    else:
        return None, MANQUE_ASSIETTE, detail

    plafond = droit.get("plafond")
    if plafond:
        montant_max, devise = plafond.get("montant"), plafond.get("devise")
        if taux_de_change is None and devise:
            # Un plafond exprimé dans une autre devise que la valeur déclarée
            # exige une conversion. Sans elle, la borne est inconnue : on ne
            # l'ignore pas, on le dit.
            return None, MANQUE_CHANGE, detail
        borne = montant_max * (taux_de_change or 1.0)
        base = min(base, borne)
    return base, None, detail


#: Famille socle → clé de couverture pays (`couverture` du manifeste). Une
#: position peut liquider tout ce qu'elle porte et rester malgré tout
#: incomplète si son pays ne trace pas une famille entière — c'est le cas des
#: cinq pays SACU, dont le crawl SARS ne porte aucune TVA. Confondre « rien à
#: cette ligne » et « la source ne trace pas cette famille » afficherait un
#: 0 % de TVA au lieu d'un manque nommé.
FAMILLES_COUVERTURE = {"droit_de_douane": "droit", "tva": "tva"}


def _liquider(
    droits: List[Dict[str, Any]],
    cif: float,
    quantite: Optional[float],
    taux_de_change: Optional[float],
    taux_preferentiels: Optional[Dict[str, float]],
    facteur_devise_specifique: Optional[float] = 1.0,
    couverture: Optional[Dict[str, Any]] = None,
    devise_cif: Optional[str] = None,
    valeur_fob: Optional[float] = None,
) -> Dict[str, Any]:
    lignes: List[Dict[str, Any]] = []
    calcules: List[Dict[str, Any]] = []
    manques: List[Dict[str, Any]] = []
    echecs: List[Dict[str, Any]] = []
    codes_de_la_position = {d.get("code") for d in droits}

    for droit in droits:
        code = droit.get("code", "?")
        ligne = {
            "code": code,
            "libelle": droit.get("libelle", code),
            "famille": droit.get("famille", "autre"),
            "assiette": droit.get("assiette"),
            "taux_pct": droit.get("taux"),
            "source": droit.get("source"),
        }
        for champ in ("note", "classification_source", "assiette_non_traduite"):
            if droit.get(champ):
                ligne[champ] = droit[champ]

        # La substitution préférentielle précède tout le reste : un droit
        # préférentiel peut être spécifique là où le NPF est ad valorem, ou
        # l'inverse — 181 lignes sud-africaines opposent « 8c/kg » à
        # « 3,2c/kg ». L'appliquer après la résolution de l'assiette liquiderait
        # le taux préférentiel sur l'assiette du NPF.
        if taux_preferentiels and code in taux_preferentiels:
            remise = taux_preferentiels[code]
            if not isinstance(remise, dict):
                remise = {"taux": remise}
            ligne["taux_npf_pct"] = droit.get("taux")
            if droit.get("specifique") and droit.get("taux") is None:
                ligne["specifique_npf"] = (
                    droit["specifique"].get("brut")
                    if isinstance(droit["specifique"], dict)
                    else droit["specifique"]
                )
            npf_specifique = bool(ligne.get("specifique_npf"))
            # Une préférence est une FACULTÉ : aucun importateur n'invoque un
            # régime plus cher que le droit commun. Même garde-fou que le
            # chemin historique (`plancher_npf`), posé seulement quand les
            # deux taux sont ad valorem — un spécifique et un ad valorem ne se
            # comparent pas sans quantité ni valeur.
            comparables = (
                droit.get("taux") is not None
                and not droit.get("specifique")
                and remise.get("taux") is not None
                and remise.get("specifique") is None
            )
            if comparables and remise["taux"] > droit["taux"]:
                ligne["regime_applique"] = "npf_plancher"
                ligne["plancher_npf"] = {
                    "taux_preferentiel_ecarte_pct": remise["taux"],
                    "taux_retenu_pct": droit["taux"],
                    "motif": (
                        "Le taux préférentiel dépasse le droit NPF de la même "
                        "position : c'est le NPF qui est servi."
                    ),
                }
            else:
                droit = dict(droit, taux=remise.get("taux"), specifique=remise.get("specifique"))
                ligne["taux_pct"] = droit["taux"]
                ligne["regime_applique"] = "preference"

            if npf_specifique and droit.get("specifique") is None and droit.get("taux") is not None:
                # Une remise ad valorem remplace un droit spécifique : l'assiette
                # « xQTE » que portait le NPF devient sans objet, et l'exiger
                # réclamerait une quantité qui ne sert plus à rien. C'est le cas
                # de toute franchise intra-union douanière sur une ligne publiée
                # « 8c/kg ».
                if droit["taux"] == 0:
                    # Zéro pour cent vaut zéro sur n'importe quelle assiette :
                    # celle-ci est immatérielle, on le dit plutôt que de faire
                    # dépendre un montant nul d'une quantité.
                    droit = dict(droit, assiette="CIF", plafond=None)
                    ligne["assiette"] = "CIF"
                    ligne["assiette_sans_objet"] = (
                        "taux nul : l'assiette n'influe sur aucun montant"
                    )
                else:
                    # Taux non nul sur un NPF spécifique : l'assiette ad valorem
                    # de ce prélèvement n'est pas connue. La supposer « CIF »
                    # fabriquerait un montant crédible sur une base devinée.
                    droit = dict(droit, assiette=None, plafond=None)
                    ligne["assiette"] = None

        taux = droit.get("taux")
        specifique = droit.get("specifique")
        if taux == 0 and specifique is None and isinstance(droit.get("assiette"), str) and (
            droit["assiette"] == "FOB" or droit["assiette"].startswith("FOB+")
        ):
            # Zéro pour cent vaut zéro sur n'importe quelle assiette — et en
            # particulier sur la base FOB des pays SACU : une franchise
            # intra-union (libre circulation) liquide sans valeur FOB, comme
            # elle liquide déjà sans quantité sur un NPF spécifique. Exiger la
            # valeur FOB ici rejetterait une importation dont le droit est
            # nul — rien n'est dû, la base n'influe sur aucun montant.
            droit = dict(droit, assiette="CIF", plafond=None)
            ligne["assiette"] = "CIF"
            ligne["assiette_sans_objet"] = "taux nul : l'assiette n'influe sur aucun montant"
        manque_devise = False
        regle_composee_absente = False
        compose_departage = None
        if (
            droit.get("compose")
            and droit.get("regle_composee")
            and taux is not None
            and specifique is not None
        ):
            # Droit composé dont la règle EST énoncée. Le tarif extérieur commun
            # de l'EAC écrit « 75% or $345/MT whichever is higher » : il n'y a
            # rien à deviner, seulement à appliquer. On retient donc la plus
            # élevée — ou la moins élevée — des deux composantes, et la ligne
            # dira laquelle a mordu.
            #
            # À ne pas confondre avec « 40% or 240c/kg » (SARS), qui ne dit PAS
            # laquelle s'applique : celui-là reste refusé, juste en dessous.
            compose_departage = droit["regle_composee"]
        elif droit.get("compose") and taux is not None and specifique is not None:
            # Droit composé : les deux composantes sont publiées, la règle qui
            # départage ne l'est pas. On refuse de liquider plutôt que de
            # retenir celle qui arrange — c'est la même règle que partout
            # ailleurs ici, appliquée à un cas qui y échappait.
            regle_composee_absente = True
            ligne["expression_brute"] = droit.get("expression_brute")
            ligne["composantes"] = {
                "ad_valorem_pct": taux,
                "specifique": (
                    specifique.get("brut") if isinstance(specifique, dict) else specifique
                ),
            }
            taux = None
        elif taux is None and specifique is not None:
            # Garde-fou : un droit spécifique se liquide toujours à la quantité.
            # Quelle que soit l'assiette déclarée, la lire comme ad valorem
            # transformerait « 8c/kg » en « 8 % » — un montant faux, et
            # crédible. Le socle pose déjà « xQTE » ; le moteur ne s'en remet
            # pas à lui sur ce point.
            droit = dict(droit, assiette="xQTE", plafond=None)
            ligne["assiette"] = "xQTE"
            montant_unitaire = _montant_unitaire(specifique)
            if montant_unitaire is not None and facteur_devise_specifique is None:
                # Le montant unitaire est publié dans la devise nationale du
                # tarif ; la valeur CIF est déclarée dans une autre. Sans taux
                # de change, l'additionner reviendrait à mélanger deux
                # devises dans le même total — jamais approché.
                manque_devise = True
                taux = None
            else:
                facteur = (
                    facteur_devise_specifique if facteur_devise_specifique is not None else 1.0
                )
                taux = montant_unitaire * facteur if montant_unitaire is not None else None
                if facteur != 1.0:
                    ligne["conversion_devise"] = (
                        f"montant unitaire converti au taux fourni (× {facteur})"
                    )
            ligne["montant_unitaire"] = taux
            ligne["specifique"] = (
                specifique.get("brut") if isinstance(specifique, dict) else specifique
            )
            if isinstance(specifique, dict):
                if specifique.get("unite_quantite"):
                    ligne["unite_quantite"] = specifique["unite_quantite"]
                if specifique.get("sous_unite_source"):
                    ligne["conversion"] = (
                        f"publié en {specifique['sous_unite_source']}, "
                        "ramené à l'unité monétaire principale"
                    )

        assiette, manque, detail = _assiette_de(
            droit,
            cif,
            calcules,
            echecs,
            quantite,
            taux_de_change,
            codes_de_la_position,
            valeur_fob,
        )
        ligne.update(detail)
        if regle_composee_absente:
            manque = MANQUE_REGLE_COMPOSEE
        elif manque_devise:
            manque = MANQUE_CHANGE
        elif manque is None and taux is None:
            manque = MANQUE_TAUX

        if manque:
            ligne["statut"] = manque
            ligne["montant"] = None
            manque_detail = {"code": code, "motif": manque}
            if detail.get("composants_absents"):
                manque_detail["composants"] = detail["composants_absents"]
            manques.append(manque_detail)
            echecs.append({"code": code, "famille": ligne["famille"]})
            lignes.append(ligne)
            continue

        # « xQTE » multiplie une quantité par un montant unitaire ; partout
        # ailleurs — « %DD » compris, où l'assiette est le montant du droit de
        # douane — le taux est un pourcentage.
        if droit.get("assiette") == "xQTE":
            montant = assiette * taux
        else:
            montant = assiette * taux / 100.0

        # Départage d'un droit composé dont la règle est écrite. Les deux
        # composantes sont calculées, et la ligne nomme celle qui l'emporte :
        # l'opérateur doit pouvoir constater POURQUOI il paie ce montant-là.
        if compose_departage:
            unitaire = _montant_unitaire(specifique)
            if quantite is None or unitaire is None:
                ligne["statut"] = MANQUE_QUANTITE
                ligne["montant"] = None
                ligne["expression_brute"] = droit.get("expression_brute")
                if isinstance(specifique, dict) and specifique.get("unite_quantite"):
                    ligne["unite_quantite"] = specifique["unite_quantite"]
                manques.append({"code": code, "motif": MANQUE_QUANTITE})
                echecs.append({"code": code, "famille": ligne["famille"]})
                lignes.append(ligne)
                continue
            # La composante spécifique est libellée dans SA devise — « $345/MT ».
            # La convertir exige un taux de change dès que la valeur en douane
            # n'est pas dans cette devise. Sans lui, les deux composantes ne sont
            # pas comparables, et comparer des montants de devises différentes
            # rendrait un droit faux sans le dire.
            devise_specifique = (
                specifique.get("unite_monetaire") if isinstance(specifique, dict) else None
            )
            facteur = 1.0
            if devise_specifique and devise_cif and devise_specifique != devise_cif:
                if taux_de_change is None:
                    ligne["statut"] = MANQUE_CHANGE
                    ligne["montant"] = None
                    ligne["expression_brute"] = droit.get("expression_brute")
                    ligne["devise_specifique"] = devise_specifique
                    manques.append({"code": code, "motif": MANQUE_CHANGE})
                    echecs.append({"code": code, "famille": ligne["famille"]})
                    lignes.append(ligne)
                    continue
                facteur = taux_de_change
            montant_specifique = quantite * unitaire * facteur
            retenu = (
                max(montant, montant_specifique)
                if compose_departage == "LE_PLUS_ELEVE"
                else min(montant, montant_specifique)
            )
            ligne["expression_brute"] = droit.get("expression_brute")
            ligne["composantes"] = {
                "ad_valorem_pct": taux,
                "ad_valorem_montant": round(montant, 4),
                "specifique": (
                    specifique.get("brut") if isinstance(specifique, dict) else specifique
                ),
                "specifique_montant": round(montant_specifique, 4),
            }
            ligne["regle_composee"] = compose_departage
            ligne["composante_retenue"] = "ad_valorem" if retenu == montant else "specifique"
            montant = retenu

        # « 450c/kg with a maximum of 96% » : le droit est le spécifique, borné
        # à un pourcentage de la valeur en douane. Contrairement à « 40% or
        # 240c/kg », cette forme énonce sa propre règle — il n'y a rien à
        # deviner, seulement à appliquer. La borne est nommée dans la ligne,
        # qu'elle morde ou non : l'opérateur doit pouvoir constater pourquoi
        # son droit s'arrête là.
        plafond_pct = droit.get("plafond_ad_valorem_pct")
        if plafond_pct is not None:
            borne = cif * plafond_pct / 100.0
            ligne["plafond_ad_valorem_pct"] = plafond_pct
            ligne["plafond_ad_valorem_montant"] = round(borne, 4)
            if montant > borne:
                ligne["montant_avant_plafond"] = round(montant, 4)
                ligne["plafond_applique"] = True
                montant = borne

        ligne.update({"base": round(assiette, 4), "montant": round(montant, 4), "statut": CALCULE})
        # Le montant est servi, mais il est né d'une moyenne : la ligne le dit,
        # et l'état global cessera de se déclarer complet.
        if _est_moyenne_statistique(ligne.get("source")):
            ligne["base_statistique"] = True
        lignes.append(ligne)
        calcules.append({"code": code, "montant": montant, "famille": ligne["famille"]})

    if couverture:
        familles_presentes = {l.get("famille") for l in lignes}
        for cle, famille in FAMILLES_COUVERTURE.items():
            if couverture.get(cle) is False and famille not in familles_presentes:
                manques.append({"code": famille.upper(), "motif": "NON_TRACEE_A_LA_SOURCE"})

    total = sum(d["montant"] for d in calcules)
    if not lignes:
        # Aucun droit analysé sur cette position : ce n'est pas un total
        # complet à zéro, c'est une absence de donnée. La confondre avec un
        # « rien à payer » réel serait la fabrication la plus trompeuse.
        etat = INDISPONIBLE
    elif not manques:
        # Un total dont au moins un droit vient d'une moyenne n'est pas
        # complet : il est indicatif. Le distinguer d'un PARTIEL importe —
        # PARTIEL dit qu'il manque une mesure, INDICATIF dit qu'une mesure
        # servie n'a pas la valeur d'un tarif.
        etat = INDICATIF if any(l.get("base_statistique") for l in lignes) else COMPLET
    elif not calcules:
        etat = INDISPONIBLE
    else:
        etat = PARTIEL
    return {
        "lignes": lignes,
        "manques": manques,
        "lignes_base_statistique": [l["code"] for l in lignes if l.get("base_statistique")],
        "total_droits": round(total, 2),
        "total_a_payer": round(cif + total, 2),
        "taux_effectif_pct": round(total / cif * 100, 4) if cif else None,
        "etat": etat,
    }


def calculer(
    position: Dict[str, Any],
    valeur_cif: float,
    *,
    quantite: Optional[float] = None,
    taux_de_change: Optional[float] = None,
    taux_preferentiels: Optional[Dict[str, float]] = None,
    devise_position: Optional[str] = None,
    devise_cif: Optional[str] = None,
    couverture: Optional[Dict[str, Any]] = None,
    valeur_fob: Optional[float] = None,
) -> Dict[str, Any]:
    """Liquider une position du socle, en NPF et — s'il y a lieu — en préférence.

    ``taux_preferentiels`` est une table ``{code: taux}`` établie en amont :
    le moteur applique des taux, il ne décide ni du droit à la préférence ni de
    son périmètre. Elle vaut souvent ``{"DD": 0}``, mais pas toujours — sous
    ZLECAf l'Algérie exonère aussi le DAPS, et l'y oublier surestimerait de
    70 points le droit liquidé sur les positions concernées. Tout prélèvement
    absent de la table reste dû à son taux NPF.

    ``devise_position``/``devise_cif`` : un droit spécifique est publié dans
    la devise nationale du tarif (« 8c/kg », en rands). Si la valeur CIF est
    déclarée dans une autre devise, l'additionner telle quelle mélangerait
    deux monnaies — voir ``_facteur_devise_specifique``.
    """
    if valeur_cif is None or valeur_cif < 0:
        raise ValueError("valeur_cif doit être un nombre positif")
    if valeur_fob is not None and (valeur_fob < 0 or valeur_fob > valeur_cif):
        # La valeur FOB ne peut ni être négative ni excéder la valeur CIF :
        # le fret et l'assurance ajoutés à la première composent la seconde.
        # L'inverse signalerait une déclaration incohérente, pas une base.
        raise ValueError("valeur_fob doit être positive et ne pas excéder valeur_cif")

    droits = position.get("droits") or []
    facteur_devise = _facteur_devise_specifique(devise_position, devise_cif, taux_de_change)
    resultat = {
        "position": {
            "designation": texte_designation(position.get("designation")),
            "unite": position.get("unite"),
            "source": position.get("source"),
        },
        "valeur_cif": valeur_cif,
        "npf": _liquider(
            droits,
            valeur_cif,
            quantite,
            taux_de_change,
            None,
            facteur_devise,
            couverture,
            devise_cif,
            valeur_fob,
        ),
    }
    if valeur_fob is not None:
        resultat["valeur_fob"] = valeur_fob
    if taux_preferentiels:
        resultat["preference"] = _liquider(
            droits,
            valeur_cif,
            quantite,
            taux_de_change,
            taux_preferentiels,
            facteur_devise,
            couverture,
            devise_cif,
            valeur_fob,
        )
        resultat["preference"]["prelevements_remises"] = sorted(taux_preferentiels)
        # Une économie n'est comparable que si les deux régimes sont
        # complets : soustraire un total partiel produirait un chiffre
        # plausible construit sur une base inconnue.
        npf_complet = resultat["npf"]["etat"] == COMPLET
        pref_complet = resultat["preference"]["etat"] == COMPLET
        resultat["economie"] = (
            round(resultat["npf"]["total_droits"] - resultat["preference"]["total_droits"], 2)
            if npf_complet and pref_complet
            else None
        )
    return resultat
