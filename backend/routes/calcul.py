"""
Route unique de calcul — chantier L3.

Un point d'entrée, `POST /calcul`, entre la donnée du crawler et le montant
affiché. Il enchaîne quatre gestes et aucun autre : résoudre la position au
socle, établir le périmètre de la préférence, liquider, répondre en disant d'où
vient chaque chiffre.

Ce que cette route ne fait pas, délibérément : aucun repli silencieux vers une
autre source, aucun taux dérivé du NPF par un coefficient, aucune position
voisine servie à la place de celle qui manque. Une indisponibilité est une
réponse, pas une panne à masquer.

**Le bloc réglementaire (chantier L4)** — formalités, prestataires mandatés,
frais vérifiés — est joint ici, et il est de nature différente du reste : il
ne dépend ni du socle ni du moteur, seulement du couple origine/destination et
de la valeur. `build_regulatory_blocks` se déclare point d'entrée unique de
toutes les routes de calcul, précisément pour que cette ventilation ne change
pas selon le chemin emprunté ; ne pas l'appeler ici faisait dire à la même
importation deux choses différentes selon la route servie.

Deux règles le gouvernent, reprises telles quelles du chemin historique :
il n'entre **jamais** dans le coût douanier — les droits et taxes restent le
seul contenu de `npf`/`preference` — et son indisponibilité ne fait jamais
échouer le calcul tarifaire : les trois champs valent alors `None`, qui se lit
« non disponible », jamais « zéro frais ».
"""

from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from services import socle
from services.calcul import calculer
from services.preference import simulations_regionales, taux_preferentiels
from services.regulatory_fee_service import build_regulatory_blocks

logger = logging.getLogger(__name__)
router = APIRouter()

#: Les trois champs du bloc réglementaire, nommés une fois pour que la réponse
#: les porte tous les trois ou aucun — un bloc à moitié servi laisserait croire
#: qu'un volet est vide alors qu'il n'a pas été consulté.
REGLEMENTAIRE = ("regulatory_compliance", "regulatory_cost", "regulatory_reported")


class DemandeCalcul(BaseModel):
    destination: str = Field(..., description="Pays d'importation (ISO-3)")
    origine: Optional[str] = Field(None, description="Pays d'origine (ISO-3)")
    code_sh: str = Field(..., description="Code SH6 ou position nationale")
    valeur_cif: float = Field(..., ge=0, description="Valeur en douane")
    quantite: Optional[float] = Field(
        None,
        gt=0,
        description=(
            "Requise par les droits spécifiques (poids, litres, unités). "
            "Strictement positive : une quantité nulle n'est pas une quantité "
            "connue. Acceptée à 0, elle liquidait le droit spécifique à 0,00 "
            "et déclarait le total COMPLET — un droit effacé en silence, dont "
            "l'écart n'est pas un arrondi mais le droit entier. Une quantité "
            "inconnue s'omet, et le moteur la réclame (`QUANTITE_REQUISE`)."
        ),
    )
    taux_de_change: Optional[float] = Field(
        None,
        gt=0,
        description="Requis par les assiettes plafonnées ou spécifiques en devise étrangère",
    )
    devise_cif: Optional[str] = Field(
        None,
        description=(
            "Devise (ISO 4217) de `valeur_cif`. Omise, elle est supposée être "
            "celle du tarif national. Un droit spécifique publié dans une "
            "autre devise que `devise_cif` exige `taux_de_change`, faute de "
            "quoi il reste indisponible plutôt que mélangé à la valeur CIF."
        ),
    )


@router.post("/calcul", summary="Liquider les droits et taxes d'une importation")
def calcul(demande: DemandeCalcul):
    # Route synchrone à dessein : le chargement du socle hache et charge
    # jusqu'à 60 Mo de JSON par pays manqué en cache. FastAPI exécute une
    # route `def` classique dans son bassin de fils ; la déclarer `async def`
    # bloquerait la boucle d'événements — et toutes les requêtes concurrentes
    # du même worker — le temps de ce calcul.
    try:
        position, provenance = socle.position(demande.destination, demande.code_sh)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc).strip('"')) from exc
    except socle.SocleIndisponible as exc:
        # Un socle absent ou périmé ne se contourne pas par une autre source :
        # il rend le service indisponible, et le dit.
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    preference = {"applique": False, "statut": "ORIGINE_NON_FOURNIE", "taux": {}}
    if demande.origine:
        preference = taux_preferentiels(
            position, demande.destination, demande.origine, demande.code_sh
        )

    position, complements = _completer_famille_absente(position, demande.destination, provenance)

    resultat = calculer(
        position,
        demande.valeur_cif,
        quantite=demande.quantite,
        taux_de_change=demande.taux_de_change,
        taux_preferentiels=preference.get("taux") or None,
        devise_position=provenance.get("devise_nationale"),
        devise_cif=demande.devise_cif,
        couverture=provenance.get("couverture"),
    )
    resultat["provenance"] = provenance
    resultat["complements_nationaux"] = complements
    # Une interdiction d'importation est une RÉPONSE, et elle doit sortir comme
    # telle. Sans ce champ, une position prohibée se présente exactement comme
    # une position dont le calcul a échoué : l'opérateur lit « indisponible »
    # là où le tarif de destination dit « interdit », et peut croire à une
    # lacune de données sur une marchandise qui ne peut pas entrer.
    # Relevé sur le tarif libyen 2022 : 46 positions du socle portent
    # « ممنوع استيراده ». Elles ne portent aucun droit, et c'est normal.
    if position.get("restrictions"):
        resultat["restrictions"] = position["restrictions"]
    # Régimes régionaux que le tarif publie pour ce couloir, sans les
    # appliquer : le total servi reste celui du régime retenu ci-dessus.
    # Taire une colonne à 0 % que le tarif de destination publie n'est pas
    # plus neutre que d'en inventer une — voir simulations_regionales.
    resultat["simulations_regionales"] = _chiffrer_simulations(
        (
            simulations_regionales(position, demande.destination, demande.origine)
            if demande.origine
            else []
        ),
        position,
        demande,
        provenance,
        resultat,
    )
    resultat.update(_regimes(preference))
    resultat.update(_bloc_reglementaire(demande.destination, demande.origine, demande.valeur_cif))
    return resultat


def _chiffrer_simulations(simulations, position, demande, provenance, resultat):
    """Chiffrer chaque simulation en relançant le moteur, pas à la main.

    Un taux seul ne répond pas à la question de l'opérateur : « combien je
    paierais sous ce régime ». Le calculer ici avec une multiplication
    ignorerait l'assiette réelle du droit, son éventuel plafond, la devise de
    la position et la cascade des prélèvements qui s'appuient dessus — quatre
    occasions de rendre un montant faux. Le moteur sait déjà tout cela : on lui
    repasse la position avec le seul taux préférentiel substitué.

    ``ecart_vs_total_servi`` est nommé ainsi, et non « économie » : le mot
    supposerait que la simulation est acquise, alors que sa réserve d'origine
    est précisément ce que le moteur ne vérifie pas. Un écart se constate, une
    économie se promet.
    """
    # L'écart n'a de sens que contre un total NPF réellement liquidé. Quand le
    # NPF est PARTIEL ou INDISPONIBLE, son « total » est la somme des seules
    # lignes calculables — le comparer ferait lire un écart NÉGATIF sur une
    # simulation pourtant avantageuse, ce qui est pire que pas d'écart du tout.
    # Cas rencontré : ZAF/020110, dont le droit composé « 40% or 240c/kg »
    # n'est pas liquidable, faisait afficher −15 000 sur une franchise SADC.
    bloc_npf = resultat.get("npf") or {}
    servi = bloc_npf.get("total_a_payer") if bloc_npf.get("etat") == "COMPLET" else None
    motif_sans_ecart = (
        None
        if servi is not None
        else ("total NPF non liquidé (" + str(bloc_npf.get("etat")) + ") : aucun écart comparable")
    )
    chiffrees = []
    for simulation in simulations:
        entree = dict(simulation)
        try:
            simule = calculer(
                position,
                demande.valeur_cif,
                quantite=demande.quantite,
                taux_de_change=demande.taux_de_change,
                taux_preferentiels={
                    simulation["prelevement"]: {"taux": simulation["taux_publie_pct"]}
                },
                devise_position=provenance.get("devise_nationale"),
                devise_cif=demande.devise_cif,
                couverture=provenance.get("couverture"),
            )
        except Exception as exc:  # pragma: no cover - le moteur ne doit pas faire tomber la route
            logger.warning("Simulation %s non chiffrée : %s", simulation.get("regime"), exc)
            entree["total_simule"] = None
            entree["etat_simule"] = "CHIFFRAGE_INDISPONIBLE"
            chiffrees.append(entree)
            continue
        bloc = simule.get("preference") or {}
        total = bloc.get("total_a_payer")
        entree["total_simule"] = total
        entree["etat_simule"] = bloc.get("etat")
        entree["lignes_simulees"] = bloc.get("lignes")
        entree["ecart_vs_total_servi"] = (
            round(servi - total, 2) if (servi is not None and total is not None) else None
        )
        if entree["ecart_vs_total_servi"] is None and motif_sans_ecart:
            entree["ecart_indisponible_motif"] = motif_sans_ecart
        chiffrees.append(entree)
    return chiffrees


def _completer_famille_absente(position: dict, destination: str, provenance: dict):
    """Ajouter la TVA nationale documentée quand la source n'en porte aucune.

    Deux conditions, cumulatives et strictes : la couverture du pays doit
    déclarer la famille entièrement absente, **et** une fiche doit établir le
    taux sur source primaire. Faute de l'une ou de l'autre, rien n'est ajouté
    et le manque reste nommé — un trou signalé vaut mieux qu'un taux prêté.

    Le complément n'est pas silencieux : la ligne porte sa source et sa
    réserve, et la réponse l'annonce dans `complements_nationaux`, pour qu'il
    ne puisse jamais passer pour une donnée collectée position par position.

    Cas traité aujourd'hui : l'Afrique du Sud, dont le crawl SARS ne porte
    aucune TVA alors qu'elle est due — et qui est le point de liquidation réel
    d'une grande part des importations de la SACU, dont elle assure le
    dédouanement pour les membres enclavés.
    """
    couverture = provenance.get("couverture") or {}
    if couverture.get("tva") is not False:
        return position, []
    entree = socle.tva_nationale(destination)
    if not entree:
        return position, []
    if any((droit.get("famille") == "tva") for droit in position.get("droits") or []):
        return position, []

    ligne = {
        "code": entree["code"],
        "libelle": entree["libelle"],
        "famille": entree["famille"],
        "taux": entree["taux"],
        "assiette": entree["assiette"],
        "source": entree["source"],
        "note": entree["note"],
        "classification_source": "table_nationale_documentee",
    }
    position = dict(position, droits=list(position.get("droits") or []) + [ligne])
    complement = {
        "code": entree["code"],
        "taux_pct": entree["taux"],
        "assiette": entree["assiette"],
        "source": entree["source"],
        "fiche": entree["fiche"],
        "note": entree["note"],
        "motif": "FAMILLE_ABSENTE_DE_LA_SOURCE",
    }
    if entree.get("reserve_assiette"):
        complement["reserve_assiette"] = entree["reserve_assiette"]
    return position, [complement]


def _regimes(preference: dict) -> dict:
    """Dire quel régime a joué, sans jamais l'appeler ZLECAf quand il ne l'est pas.

    Deux membres d'une même union douanière échangent en libre circulation, un
    régime *distinct* de la ZLECAf et prioritaire sur elle. Servir cette
    franchise sous la clé `preference_zlecaf` ferait afficher « préférence
    ZLECAf appliquée » là où la ZLECAf est précisément écartée — la même
    confusion de régimes qu'une colonne COMESA lue comme un taux ZLECAf.
    """
    infos = {cle: valeur for cle, valeur in preference.items() if cle != "taux"}
    resultat = {"regime_commercial": infos}
    # Le cas nommé, et lui seul, est réécrit : tout le reste — ZLECAf servie,
    # refusée, ou origine non fournie — passe tel quel. Tester le complément
    # (« tout sauf ZLECAF ») rangeait une demande sans origine parmi les
    # unions douanières, et lui faisait nommer un bloc qui n'existait pas.
    if infos.get("regime") == "UNION_DOUANIERE":
        resultat["preference_zlecaf"] = {
            "applique": False,
            "regime": infos.get("regime"),
            "statut": "REGIME_UNION_DOUANIERE",
            "note": (
                f"La ZLECAf ne s'applique pas ici : {infos.get('libelle_bloc')} "
                "est une union douanière, et ses membres échangent entre eux en "
                "libre circulation — un régime distinct, et plus avantageux, que "
                "le démantèlement progressif de la ZLECAf."
            ),
        }
    else:
        resultat["preference_zlecaf"] = infos
    return resultat


def _bloc_reglementaire(destination: str, origine: Optional[str], valeur_cif: float) -> dict:
    """Formalités, prestataires mandatés et frais vérifiés — informatif, jamais
    additionné aux droits.

    `fob_value` reçoit la valeur CIF, comme le fait le chemin historique. Ce
    n'est pas exact au sens douanier — le FOB exclut fret et assurance — mais
    les deux routes doivent répondre la même chose sur la même importation :
    corriger ici seulement ferait diverger les deux chemins juste avant de les
    réunir. La correction, si elle vient, vaudra pour le point d'entrée commun.
    """
    origine_iso3 = (origine or "").upper() or None
    try:
        blocs = build_regulatory_blocks(
            destination.upper(), origine_iso3, fob_value=valeur_cif, cif_value=valeur_cif
        )
    except Exception as exc:  # garde-fou : le calcul tarifaire n'en dépend pas
        logger.warning(
            "Bloc réglementaire indisponible pour %s->%s (calcul tarifaire non affecté) : %s",
            origine_iso3,
            destination,
            exc,
        )
        return {
            "regulatory_compliance": None,
            "regulatory_cost": None,
            "regulatory_reported": None,
        }
    return {cle: blocs[cle] for cle in REGLEMENTAIRE}


@router.get("/calcul/pays", summary="Pays servis par le socle, et leur couverture")
def pays():
    try:
        servis = socle.pays_servis()
    except socle.SocleIndisponible as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    manifeste = socle.manifeste()
    return {
        "socle_version": manifeste.get("socle_version"),
        "construit_le": manifeste.get("construit_le"),
        "totaux": manifeste.get("totaux"),
        "pays": servis,
    }
