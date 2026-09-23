"""
Calendrier de démantèlement tarifaire ZLECAf à l'IMPORTATION au Kenya.

Source authentique : *EAC Provisional Schedule of Tariff Concessions for the
African Continental Free Trade Area (AfCFTA): Category A Products* — Legal
Notice EAC/321/2022, Journal officiel de l'EAC du 6 septembre 2022, pris par
le Conseil des ministres de l'EAC sur le fondement de la section 112 (1) (b)
de l'*East African Community Customs Management Act, 2004*.

UNITÉ : pourcentages de bout en bout, comme partout ailleurs dans le moteur.
Un taux publié à 2,5 vaut 2,5 % et se transporte tel quel jusqu'au calcul.

Ce module rend un TAUX LU, jamais calculé. Le barème publie dix colonnes
annuelles par position et ce sont elles qui font foi. Qu'elles vaillent
exactement ``base x (1 - n/10)`` sur les 53 420 colonnes du document est un
contrôle du script d'extraction, pas la règle de production.

QUATRE POINTS SANS LESQUELS CE CALENDRIER SERAIT FAUX :

1. **Le périmètre est le droit de douane SEUL.** Le tarif kényan porte aussi
   l'*Import Declaration Fee* (3,5 %) et le *Railway Development Levy* (2 %).
   Le socle les classe déjà en ``redevance`` et non en ``droit``. L'article
   7(3) du Protocole sur le commerce des marchandises définit pourtant le
   droit d'importation de façon large — « any duty or charge of any kind
   imposed on or in connection with the importation » — avec quatre
   exclusions, dont les redevances conformes à l'article VIII du GATT.
   **Aucune détermination publiée ne qualifie l'IDF ni le RDL** au regard de
   cette définition, et les listes d'exonération du *Miscellaneous Fees and
   Levies Act 2016* ne visent que l'origine EAC. Le moteur sert donc ce que
   le Kenya perçoit : les deux restent dus au taux plein. Ce n'est pas un
   périmètre vérifié, c'est un constat de droit positif.

2. **Le barème ne couvre pas tout le tarif.** 611 positions kényanes sur
   5 935 n'y figurent pas — produits sensibles et catégories B et C, dont
   aucun barème n'est publié. Une position absente ne se déduit pas : elle
   rend ``None`` et le NPF s'applique.

3. **Onze lignes d'aciers portent un taux composite** que la grammaire du
   moteur ne liquide pas. Elles sont hors barème, et les ramener à leur
   volet ad valorem servirait un droit inférieur à celui qui est dû.

4. **La date d'opposabilité n'est pas celle du calendrier.** Le calendrier
   est réputé avoir commencé le 1er janvier 2021 (Directive ministérielle
   1/2021, §11), mais l'instrument n'a été gazetté que le 6 septembre 2022,
   et le §15 de la même directive dispense expressément de tout
   remboursement des droits perçus entre les deux dates. Avant la
   gazettisation, aucune préférence n'est servie.

Le périmètre des ORIGINES admises ne relève pas de ce module : il est au
registre d'application (``zlecaf_implementation_registry``), qui le tient de
l'Annexe 1 de la Directive ministérielle 1/2021. Le barème, lui, ne nomme
aucun pays — vérifié sur ses 347 pages.
"""

from __future__ import annotations

import datetime
import json
import logging
from pathlib import Path
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

DOSSIER = Path(__file__).resolve().parent.parent / "data" / "zlecaf_ken"

with open(DOSSIER / "bareme_categorie_a.json", encoding="utf-8") as f:
    _BAREME = json.load(f)

#: Taux EN POURCENTAGE, tels que le Journal officiel les publie.
POSITIONS = _BAREME["positions"]
PREMIERE_ANNEE = _BAREME["_premiere_annee"]
DERNIERE_ANNEE = _BAREME["_derniere_annee"]
LIGNES_COMPOSITES = frozenset(_BAREME["_lignes_ecartees"]["taux_composite"])

#: Date de gazettisation de la Legal Notice EAC/321/2022 : avant elle, rien
#: n'est opposable au Kenya, quoi que dise le calendrier.
OPPOSABLE_A_PARTIR_DU = datetime.date(2022, 9, 6)

LIBELLE = (
    "Legal Notice EAC/321/2022, barème provisoire ZLECAf catégorie A "
    "(Journal officiel de l'EAC du 06/09/2022), colonne {annee}"
)

#: Rubriques SANS RÈGLE D'ORIGINE ARRÊTÉE dans l'Appendice IV à l'Annexe 2,
#: version du 12e Conseil des ministres (décembre 2023) : « Yet to be agreed »,
#: ou entre crochets (note 2.4). Fiche :
#: ZLECAF_appendice_IV_regles_non_arretees_2026-09-23.json.
#:
#: Le §17 de la Directive 1/2021 PERMET de ne pas appliquer la préférence à ces
#: produits — l'Algérie l'a fait, par sa circulaire. Le barème kényan, lui, ne
#: les gèle pas : la préférence publiée est servie, avec une réserve. Liste
#: tenue ici pour le Kenya seul, même si elle coïncide avec celle de l'Algérie :
#: la base juridique n'est pas la même.
RUBRIQUES_SANS_REGLE_D_ORIGINE = (
    ("5111", "5113"),
    ("5204", "5212"),
    ("5309", "5309"),
    ("5407", "5408"),
    ("5512", "5516"),
    ("5801", "5804"),
    ("5806", "5806"),
    ("5810", "5810"),
    ("6001", "6006"),  # chapitre 60 entier
    ("6301", "6306"),
    ("8701", "8701"),
    ("8703", "8708"),
    ("8710", "8712"),
)

RESERVE_REGLE_D_ORIGINE = (
    "Règle d'origine ZLECAf non arrêtée pour la rubrique {rubrique} dans "
    "l'Appendice IV à l'Annexe 2 (Conseil des ministres, décembre 2023). La "
    "Directive 1/2021 (§17) permet de ne pas appliquer la préférence à ce "
    "produit ; le barème kényan ne l'exclut pas. L'adoption des règles "
    "manquantes est annoncée par le gouvernement sud-africain (dtic, mars 2026) "
    "et, par l'Assemblée de l'UA en février 2026, par tralac ; ni la décision, "
    "ni les règles adoptées, ni leur mécanisme transitoire n'ont été retrouvés. "
    "La préférence peut ne pas être accordée en douane."
)


def _normaliser(hs_code: str) -> str:
    """Le barème indexe en SH à huit chiffres pointés (1702.30.00) ; le socle, sans points."""
    brut = (hs_code or "").replace(".", "").replace(" ", "")
    if len(brut) != 8:
        return ""
    return f"{brut[0:4]}.{brut[4:6]}.{brut[6:8]}"


def compute_ken_zlecaf_rate(
    hs_code: str,
    origin_iso3: str,
    as_of: Optional[datetime.date] = None,
) -> Tuple[Optional[float], Optional[str]]:
    """Taux DD ZLECAf à l'importation au Kenya, pour une position et une date.

    Rend ``(taux_pct, libellé de la source)``, ou ``(None, None)`` quand le
    barème ne couvre pas la position ou que la date est hors calendrier. Un
    ``None`` laisse l'appelant au régime NPF : rien n'est dérivé du plein
    droit par un coefficient.

    ``origin_iso3`` n'est PAS vérifié ici : l'admission de l'origine est
    tranchée en amont par le registre d'application, et ce module ne fait que
    lire un barème qui ne nomme aucun pays. Le paramètre est conservé pour
    que la signature soit celle du calendrier algérien, et parce qu'un jour
    une origine pourrait emporter un calendrier distinct.
    """
    if not origin_iso3:
        return None, None
    jour = as_of or datetime.date.today()
    if jour < OPPOSABLE_A_PARTIR_DU:
        return None, None

    code = _normaliser(hs_code)
    if not code:
        return None, None
    ligne = POSITIONS.get(code)
    if ligne is None:
        # Position hors barème : sensible, catégorie B ou C, ou taux composite.
        return None, None

    annee = min(max(jour.year, PREMIERE_ANNEE), DERNIERE_ANNEE)
    annuites = ligne["annuites_pct"]
    if len(annuites) != 10:
        logger.warning("Barème ZLECAf KEN : %s porte %d annuités", code, len(annuites))
        return None, None
    return float(annuites[annee - PREMIERE_ANNEE]), LIBELLE.format(annee=annee)


def reserve_regle_d_origine(hs_code: str) -> Optional[str]:
    """La réserve à joindre à la préférence, ou None si la rubrique a sa règle."""
    rubrique = (hs_code or "").replace(".", "").replace(" ", "")[:4]
    if len(rubrique) != 4:
        return None
    for debut, fin in RUBRIQUES_SANS_REGLE_D_ORIGINE:
        if debut <= rubrique <= fin:
            return RESERVE_REGLE_D_ORIGINE.format(rubrique=f"{rubrique[:2]}.{rubrique[2:]}")
    return None


def ligne_du_journal_officiel(
    hs_code: str, origin_iso3: str, as_of: Optional[datetime.date] = None
) -> Optional[dict]:
    """La ligne du barème gazetté, sous la forme que rend le résolveur des
    taux officiels — pour que le chemin historique serve le Journal officiel,
    et non l'e-Tariff Book du Secrétariat.

    Les deux divergent sur 275 lignes : l'e-Tariff Book calcule sur une base
    de 25 % là où le Journal officiel porte 35 % (bande du TEC de 2022), et il
    ignore 1 072 lignes du barème. Le Journal officiel est l'acte que la douane
    kényane applique.
    """
    jour = as_of or datetime.date.today()
    taux, _ = compute_ken_zlecaf_rate(hs_code, origin_iso3, jour)
    if taux is None:
        return None
    annee = min(max(jour.year, PREMIERE_ANNEE), DERNIERE_ANNEE)
    return {
        "hs_code": _normaliser(hs_code).replace(".", ""),
        "country_iso3": "KEN",
        "agreement": "AfCFTA",
        "source_title": _BAREME["_instrument"],
        "source_date": OPPOSABLE_A_PARTIR_DU.isoformat(),
        "source_url": _BAREME["_url"],
        "source_api_url": None,
        "source_column": str(annee),
        "schedule": "EAC/321/2022",
        "schedule_year": annee - PREMIERE_ANNEE + 1,
        "rate_expression": f"{taux:g}%",
        "ad_valorem_rate_pct": taux,
        "rate_kind": "AD_VALOREM",
        "calculation_status": "CALCULABLE",
    }
