"""
Droits et taxes à l'EXPORTATION — `POST /calcul/export`.

Un autre impôt sur une autre opération : ce n'est pas un second calcul de
l'importation. Les droits de sortie sont lus au socle (`droits_export` des
positions nationales, voir `build_socle.droits_export_du_fichier`) et liquidés
par le même moteur que `POST /calcul`, avec les mêmes refus : une assiette non
collectée, un taux sans unité ou une quantité manquante rendent la ligne
indisponible et la nomment, jamais un zéro.

S'y ajoutent les perceptions de sortie publiées hors du tarif douanier
(`HORS_TARIF` : à Madagascar, les DTSPM du Code minier ; au Mali, la TEOAPM du
CGI), quand l'exportateur déclare la catégorie que le texte vise. Au Cameroun
et au Congo, le droit de sortie commun dépend du degré de transformation du
produit (`SELON_TRANSFORMATION`), que l'exportateur déclare aussi.
"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from services import socle
from services.calcul import DEVISES_PUBLIEES, calculer

AUCUN_DROIT = "AUCUN_DROIT_PUBLIE"

#: Perceptions à la sortie publiées HORS du tarif douanier. Elles ne visent pas
#: des positions mais une catégorie de marchandises ou d'exportateurs que le
#: texte définit : aucune position n'y est rattachée par déduction, l'exportateur
#: la déclare. Madagascar : fiche MDG_DTSPM_code_minier_2026-10-25.json ; Mali :
#: fiche MLI_TEOAPM_CGI_2026-10-26.json.
HORS_TARIF = {
    "MDG": {
        "champ": "produit_minier",
        "question": "Produit des mines au sens du Code minier (substance minérale ni de carrière ni fossile) ?",
        "question_en": "Mining product within the meaning of the Mining Code (mineral substance, not quarry or fossil)?",
        "question_transformation": "Substance transformée au sens du Code (abattement de 30 %, art. 288) ?",
        "question_transformation_en": "Processed substance within the meaning of the Code (30% abatement, art. 288)?",
        "abattement_transformation": 0.3,
        "source": "Code minier (loi n° 2023-007), art. 283, 284 et 288",
        "assiette": (
            "Assiette légale : valeur FOB au cours international au moment de l'exportation, établie par le "
            "ministère des Mines avec la douane (art. 284) — c'est elle qu'il faut saisir."
        ),
        # Art. 285 : aucune autre perception sur les produits des mines, sortie
        # comprise. Un DS non nul au tarif le contredit : montré, pas tranché.
        "conflit_tarif": (
            "Le Code minier (art. 285) exclut toute autre perception sur les produits des mines, sortie comprise ; "
            "le tarif 2026 publie pourtant ce droit : à vérifier auprès de la douane."
        ),
        "lignes": [
            ("DTSPM.RISTOURNE", "Ristourne minière (DTSPM, collectivités territoriales)", 2.0),
            ("DTSPM.REDEVANCE", "Redevance minière (DTSPM, État)", 3.0),
        ],
    },
    "MLI": {
        "champ": "produit_minier",
        "question": "Or ou autre produit minier, exporté par un exportateur non régi par le Code minier ?",
        "question_en": "Gold or other mining product, exported by an exporter not governed by the Mining Code?",
        "source": "Code général des impôts, art. 253-AG à 253-AK (L.F.2017, L.F.R.2017)",
        "assiette": (
            "Assiette légale : « la valeur du produit à l'exportation » (art. 253-AI). CGI publié par la DGI, à jour "
            "de la loi de finances 2018 ; ses modifications postérieures (dont l'ordonnance n° 2025-006) n'ont pas "
            "été consultées."
        ),
        "lignes": [
            ("TEOAPM", "Taxe due par les exportateurs d'or et autres produits miniers non régis par le Code minier",
             2.0),
        ],
    },
}

#: Droit de sortie dont le taux tient au degré de transformation du produit,
#: que la position ne dit pas. Le socle porte ce droit à taux non établi et
#: marqué `selon_transformation` (`build_socle.EXPORT_PAR_TEXTE`) ; la réponse
#: de l'exportateur le fixe. Fiches CMR_droit_de_sortie_LF2018_LF2026_2026-10-28.json
#: et COG_droit_de_sortie_LFR2021_LF2026_2026-10-29.json.
SELON_TRANSFORMATION = {
    "CMR": {
        "champ": "produit_fini",
        "question": "Produit fini, manufacturé ou transformé au Cameroun (sinon : brut ou semi-fini) ?",
        "question_en": "Finished product, manufactured or processed in Cameroon (otherwise: raw or semi-finished)?",
        "oui": (0.0, "Produit manufacturé ou transformé au Cameroun au sens de produit fini : exonéré (LF 2020, art. 5)."),
        "non": (2.0, "Produit brut : taux commun de 2 % de la valeur imposable (LF 2018, art. 2) ; produit semi-fini : "
                     "2 % de la valeur FOB (LF 2023, art. 10)."),
    },
    "COG": {
        "champ": "produit_fini",
        "question": "Produit transformé d'origine congolaise (issu d'une ouvraison ou d'une transformation au Congo) ?",
        "question_en": "Processed product of Congolese origin (worked or processed in Congo)?",
        "oui": (0.0, "Produit transformé d'origine congolaise : exonéré du droit de sortie (LFR 2021, point 42, 2)."),
        "non": (2.0, "Taux général du droit de sortie : 2 % de la valeur en douane (LFR 2021, point 42, 1)."),
    },
}

router = APIRouter()
router_couverture = APIRouter()


class DemandeExport(BaseModel):
    pays: str = Field(..., description="Pays d'exportation (ISO3)")
    code_sh: str = Field(..., description="Position nationale du tarif du pays d'exportation")
    valeur: float = Field(..., ge=0, description="Valeur en douane à l'exportation")
    devise: Optional[str] = Field(
        default=None,
        description=(
            "Devise (ISO 4217) de `valeur`. Un droit spécifique publié dans la devise nationale "
            "exige alors `taux_de_change`."
        ),
    )
    quantite: Optional[float] = Field(
        default=None, ge=0, description="Quantité, dans l'unité que nomme le droit spécifique"
    )
    taux_de_change: Optional[float] = Field(
        default=None,
        gt=0,
        description=(
            "Unités de `devise` pour UNE unité de la monnaie du tarif (comme pour `POST /calcul`) : "
            "valeur en USD, droit en dinars → environ 0,32, pas 3,1."
        ),
    )
    produit_minier: Optional[bool] = Field(
        default=None,
        description=(
            "Perception hors tarif : à Madagascar, produit des mines au sens du Code minier (DTSPM) ; au Mali, or "
            "ou produit minier d'un exportateur non régi par le Code minier (TEOAPM). Omis : non établi."
        ),
    )
    produit_minier_transforme: bool = Field(
        default=False, description="Madagascar : substance transformée au sens du Code (abattement de 30 %)."
    )
    produit_fini: Optional[bool] = Field(
        default=None,
        description=(
            "Cameroun : produit fini, manufacturé ou transformé au Cameroun (exonéré) ; sinon brut ou semi-fini "
            "(2 %). Congo : produit transformé d'origine congolaise (exonéré) ; sinon 2 %. Omis : le droit de "
            "sortie commun reste à établir."
        ),
    )


def _selon_transformation(pays: str, droits: list, demande: DemandeExport) -> list:
    """Fixer, d'après la réponse de l'exportateur, les droits que le socle
    marque `selon_transformation` ; sans réponse, ils restent à établir."""
    regle = SELON_TRANSFORMATION.get(pays)
    if not regle:
        return droits
    reponse = getattr(demande, regle["champ"])
    sortie = []
    for d in droits:
        if d.get("selon_transformation"):
            if reponse is None:
                d = {**d, "note": "À établir : " + regle["question"] + " " + d.get("note", "")}
            else:
                taux, motif = regle["oui" if reponse else "non"]
                d = {**d, "taux": taux, "assiette": "CIF", "note": motif + " " + d.get("note", "")}
        elif d.get("note_si_transforme") and reponse is not False:
            # Perception dont seul le taux du produit brut est établi
            # (redevance informatique du Congo) : transformé ou sans réponse,
            # elle reste à établir.
            prefixe = "À établir : " + regle["question"] + " " if reponse is None else ""
            d = {**d, "taux": None, "assiette": None, "note": prefixe + d["note_si_transforme"]}
        sortie.append(d)
    return sortie


def _hors_tarif(pays: str, demande: DemandeExport) -> list:
    """Lignes des perceptions de sortie publiées hors du tarif, pour ce pays."""
    regle = HORS_TARIF.get(pays)
    if not regle or demande.produit_minier is False:
        return []
    lignes = []
    abattement = regle.get("abattement_transformation")
    for code, libelle, taux in regle["lignes"]:
        ligne = {"code": code, "libelle": libelle, "famille": "export", "source": regle["source"]}
        if demande.produit_minier is None:
            # Sans réponse, la ligne reste à établir : la taire ferait lire
            # « exonéré » au DS du tarif pour de l'or qui doit 5 %.
            ligne.update(taux=None, assiette=None, note="À établir : " + regle["question"])
        elif abattement and demande.produit_minier_transforme:
            ligne.update(
                taux=round(taux * (1 - abattement), 4),
                assiette="CIF",
                note=f"{taux:g} % réduit de {abattement:.0%} (substance transformée, art. 288). {regle['assiette']}",
            )
        else:
            ligne.update(taux=taux, assiette="CIF", note=regle["assiette"])
        lignes.append(ligne)
    return lignes


def _pays_export():
    """Pays dont le socle porte des droits de sortie, et combien de positions ;
    s'y ajoutent, à 0 position, ceux dont la seule perception est hors tarif."""
    manifeste = socle.manifeste().get("pays", {})
    pays = {
        iso: entree["compteurs"]["positions_export"]
        for iso, entree in manifeste.items()
        if entree.get("compteurs", {}).get("positions_export")
    }
    for iso in HORS_TARIF:
        if iso in manifeste:
            pays.setdefault(iso, 0)
    return pays


@router.post("/calcul/export", summary="Liquider les droits et taxes d'une exportation")
def calcul_export(demande: DemandeExport):
    pays = demande.pays.upper()
    try:
        couverts = _pays_export()
    except socle.SocleIndisponible as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    if pays not in couverts:
        raise HTTPException(
            status_code=404,
            detail=f"{pays} : aucun droit à l'exportation collecté au socle.",
        )
    try:
        position, provenance = socle.position(pays, demande.code_sh)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except KeyError as exc:
        code = socle.normaliser_code(demande.code_sh)
        sous = socle.positions_nationales(pays, code) if len(code) == 6 else []
        if sous:
            raise HTTPException(
                status_code=422,
                detail={
                    "code": "POSITION_NATIONALE_REQUISE",
                    "message": f"{pays}/{code} : {len(sous)} positions nationales sous ce SH6 — choisir la position.",
                    "positions": sous,
                },
            ) from exc
        raise HTTPException(status_code=404, detail=str(exc).strip('"')) from exc
    except socle.SocleIndisponible as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    droits = _selon_transformation(pays, position.get("droits_export") or [], demande)
    hors_tarif = _hors_tarif(pays, demande)
    conflit = HORS_TARIF.get(pays, {}).get("conflit_tarif")
    if hors_tarif and demande.produit_minier and conflit:
        droits = [{**d, "note": conflit} if d.get("taux") else d for d in droits]
    resultat = calculer(
        {**position, "droits": droits + hors_tarif},
        demande.valeur,
        quantite=demande.quantite,
        taux_de_change=demande.taux_de_change,
        devise_position=provenance.get("devise_nationale"),
        devise_cif=demande.devise,
    )
    export = resultat["npf"]
    # Valeur et droits de sortie ne s'additionnent pas en un « total à payer ».
    export.pop("total_a_payer", None)
    if not droits and not hors_tarif:
        # Le tarif collecté ne porte aucun droit de sortie pour la position.
        # Ce que le tarif ne publie pas (redevances hors tarif) n'y est pas.
        export["etat"] = AUCUN_DROIT
    return {
        "pays": pays,
        "position": resultat["position"],
        "valeur": demande.valeur,
        "droits_export_publies": bool(droits),
        "export": export,
        "change_requis": _change_requis(export, droits + hors_tarif, provenance, demande),
        "provenance": provenance,
    }


def _change_requis(export: dict, droits: list, provenance: dict, demande: DemandeExport) -> list:
    """Les paires de devises qu'un droit attend pour être converti, dites, pas
    devinées : `taux_de_change` vaut des unités de `devise_valeur` pour UNE unité
    de `devise_droit` — la monnaie du tarif, ou l'USD/EUR que le tarif publie
    lui-même (« $0.02/litre » au Ghana)."""
    nationale = provenance.get("devise_nationale")
    par_code = {d.get("code"): d for d in droits}
    paires = []
    for ligne in export.get("lignes") or []:
        if ligne.get("statut") != "TAUX_DE_CHANGE_REQUIS":
            continue
        specifique = (par_code.get(ligne.get("code")) or {}).get("specifique")
        unite = str((specifique or {}).get("unite_monetaire") or "").upper() if isinstance(specifique, dict) else ""
        paire = {
            "devise_droit": unite if unite in DEVISES_PUBLIEES else nationale,
            "devise_valeur": (demande.devise or nationale or "").upper(),
        }
        if paire not in paires:
            paires.append(paire)
    return paires


@router_couverture.get("/calcul/export/pays", summary="Pays dont le socle porte des droits de sortie")
def pays_export():
    try:
        return {
            "pays": _pays_export(),
            # Ce que l'écran doit demander pour les perceptions hors tarif.
            "questions": {
                iso: {
                    k: regle.get(k)
                    for k in ("champ", "question", "question_en", "question_transformation",
                              "question_transformation_en")
                }
                for iso, regle in {**HORS_TARIF, **SELON_TRANSFORMATION}.items()
            },
        }
    except socle.SocleIndisponible as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
