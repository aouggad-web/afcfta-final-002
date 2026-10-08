"""
Réseau ZLECAf : statut de mise en œuvre de chaque État et liaisons
préférentielles entre États, pour la carte « Réseau ZLECAf ».

Rien n'est saisi ici : tout est lu dans les modules qui servent déjà le moteur
de calcul, et chaque statut porte la ou les preuves qui le fondent.

* Signature et ratification : ``zlecaf_membership_status`` (the dtic / SARS,
  « Update on the AfCFTA », mars 2026).
* Offre acceptée : Annexe 1 de la Directive ministérielle 1/2021
  (``ANNEXE1_PARTIES_2021``), moins les parties qui n'ont pas ratifié.
* Offre déposée : barème d'offre archivé dans le dépôt (``OFFER_DATASETS``).
* Instrument national publié : enregistrement ``PARTNER_NOTICE_REQUIRED`` du
  registre de mise en œuvre — texte adopté, liste des partenaires non publiée.
* Déploiement : l'État applique la préférence à l'importation (enregistrement
  ``APPLIED`` en vigueur, ou liste dtic de l'Afrique du Sud), ou une source le
  nomme parmi les partenaires qui ont déclenché l'application réciproque
  (circulaire algérienne DGD 482/2024, liste dtic des « implementing
  countries »).

Le statut retenu est le plus avancé des niveaux établis ; un État non signataire
ou non ratifiant reste à ce statut quelles que soient les autres mentions.

Une liaison A → B signifie : « A applique la préférence ZLECAf aux produits
originaires de B », d'après l'instrument de A. Les origines non ratifiantes sont
écartées, comme le fait le moteur. Pour l'EAC, la liste d'origines est un
plafond (voir ``KENYA_ORIGINS_RESERVES``) ; la note de la preuve le dit.

Le PIB est celui de la Banque mondiale (``worldbank_data_latest.json``,
indicateur GDP, dollars courants) pour une seule année, ``PIB_ANNEE`` : un pays
sans valeur pour cette année reçoit ``None``, jamais la valeur d'une autre année.
"""

from __future__ import annotations

import json
from datetime import date
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Optional

from constants import AFRICAN_COUNTRIES
from services import zlecaf_implementation_registry as registry
from services import zlecaf_membership_status as membership
from services.zlecaf_schedule_dza import ACTIVE_PARTNERS as DZA_PARTNERS
from services.zlecaf_schedule_zaf import ACTIVE_PARTNERS_ZAF

PIB_ANNEE = "2024"

WORLDBANK_PATH = (
    Path(__file__).resolve().parent.parent.parent / "data" / "json" / "worldbank_data_latest.json"
)

# Niveaux, du moins avancé au plus avancé. L'ordre est aussi celui de la légende.
NON_SIGNATAIRE = "non_signataire"
SIGNE_NON_RATIFIE = "signe_non_ratifie"
RATIFIE = "ratifie"
OFFRE_DEPOSEE = "offre_deposee"
OFFRE_ACCEPTEE = "offre_acceptee"
INSTRUMENT_PUBLIE = "instrument_publie"
DEPLOIEMENT = "deploiement"

NIVEAUX = [
    NON_SIGNATAIRE,
    SIGNE_NON_RATIFIE,
    RATIFIE,
    OFFRE_DEPOSEE,
    OFFRE_ACCEPTEE,
    INSTRUMENT_PUBLIE,
    DEPLOIEMENT,
]

SOURCE_ADHESION = "the dtic / SARS, « Update on the AfCFTA », newsletter mars 2026"
SOURCE_ANNEXE1 = (
    "Directive ministérielle 1/2021 (AfCFTA/COM/7/DIRECTIVE/FINAL), Annexe 1, "
    "Conseil des ministres de la ZLECAf, Accra, 10/10/2021"
)
SOURCE_ZAF = (
    "the dtic / SARS, « Update on the AfCFTA », mars 2026 — liste des "
    "« implementing countries » ouverts aux exportateurs sud-africains"
)
SOURCE_DZA = (
    "Circulaire DGD n°482/DGD/SP/D.042/24 du 22/10/2024 — partenaires ayant "
    "déclenché l'application effective et réciproque avec l'Algérie"
)


def _preuve(niveau: str, source: str, url: Optional[str] = None, note: Optional[str] = None):
    out = {"niveau": niveau, "source": source}
    if url:
        out["url"] = url
    if note:
        out["note"] = note
    return out


@lru_cache(maxsize=1)
def _pib(path: Path = WORLDBANK_PATH) -> Dict[str, Optional[float]]:
    try:
        data = json.loads(path.read_text(encoding="utf-8")).get("data", {})
    except (OSError, ValueError):
        return {}
    out: Dict[str, Optional[float]] = {}
    for iso3, info in data.items():
        valeur = ((info.get("indicators") or {}).get("GDP") or {}).get(PIB_ANNEE)
        out[iso3] = float(valeur) if valeur is not None else None
    return out


def _records_en_vigueur(jour: date):
    for iso3, record in registry.RECORDS.items():
        if record.status == registry.APPLIED and registry.application_commencee(iso3, jour):
            yield iso3, record


def construire_reseau(jour: Optional[date] = None) -> dict:
    """Statuts des États de ``AFRICAN_COUNTRIES`` et liaisons préférentielles."""
    jour = jour or date.today()
    iso3s = [c["iso3"] for c in AFRICAN_COUNTRIES]
    preuves: Dict[str, List[dict]] = {k: [] for k in iso3s}

    def ajouter(iso3: str, preuve: dict) -> None:
        if iso3 in preuves:
            preuves[iso3].append(preuve)

    for iso3 in iso3s:
        statut = membership.ratification_status(iso3)
        if statut == membership.STATUS_NOT_SIGNED:
            ajouter(iso3, _preuve(NON_SIGNATAIRE, SOURCE_ADHESION))
        elif statut == membership.STATUS_SIGNED_NOT_RATIFIED:
            ajouter(iso3, _preuve(SIGNE_NON_RATIFIE, SOURCE_ADHESION))
        else:
            ajouter(
                iso3,
                _preuve(
                    RATIFIE,
                    SOURCE_ADHESION,
                    note="Ratification : statut par défaut des États que la source ne cite "
                    "ni parmi les non-signataires ni parmi les non-ratifiants.",
                ),
            )

    for iso3, jeu in registry.OFFER_DATASETS.items():
        ajouter(
            iso3, _preuve(OFFRE_DEPOSEE, f"Barème d'offre archivé dans le dépôt (jeu « {jeu} »)")
        )

    for iso3 in registry.ANNEXE1_PARTIES_2021:
        ajouter(
            iso3,
            _preuve(OFFRE_ACCEPTEE, SOURCE_ANNEXE1, note=registry.KENYA_ORIGINS_RESERVES),
        )

    for iso3, record in registry.RECORDS.items():
        if record.status == registry.PARTNER_NOTICE_REQUIRED:
            ajouter(
                iso3,
                _preuve(
                    INSTRUMENT_PUBLIE, record.instrument_title, record.instrument_url, record.note
                ),
            )

    liaisons: List[dict] = []
    for iso3, record in _records_en_vigueur(jour):
        ajouter(
            iso3,
            _preuve(DEPLOIEMENT, record.instrument_title, record.instrument_url, record.note),
        )
        for origine in sorted(record.accepted_origins):
            liaisons.append(
                {
                    "importateur": iso3,
                    "origine": origine,
                    "source": record.instrument_title,
                    "url": record.instrument_url,
                }
            )

    # Afrique du Sud : elle applique la préférence aux « implementing
    # countries » de la liste dtic, qui sont eux-mêmes en application.
    ajouter("ZAF", _preuve(DEPLOIEMENT, SOURCE_ZAF))
    for partenaire in sorted(ACTIVE_PARTNERS_ZAF):
        ajouter(partenaire, _preuve(DEPLOIEMENT, SOURCE_ZAF))
        liaisons.append({"importateur": "ZAF", "origine": partenaire, "source": SOURCE_ZAF})

    # Algérie : ses partenaires actifs ont déclenché l'application réciproque.
    for partenaire in sorted(DZA_PARTNERS):
        ajouter(partenaire, _preuve(DEPLOIEMENT, SOURCE_DZA))

    ratifiants = {
        k for k in iso3s if membership.ratification_status(k) == membership.STATUS_RATIFIED
    }
    vues = set()
    liaisons_retenues = []
    for lien in liaisons:
        cle = (lien["importateur"], lien["origine"])
        if cle in vues or lien["origine"] == lien["importateur"]:
            continue
        if lien["importateur"] not in ratifiants or lien["origine"] not in ratifiants:
            continue
        vues.add(cle)
        liaisons_retenues.append(lien)

    pib = _pib()
    pays = []
    for c in AFRICAN_COUNTRIES:
        iso3 = c["iso3"]
        niveaux = {p["niveau"] for p in preuves[iso3]}
        if NON_SIGNATAIRE in niveaux:
            statut = NON_SIGNATAIRE
        elif SIGNE_NON_RATIFIE in niveaux:
            statut = SIGNE_NON_RATIFIE
        else:
            statut = max(niveaux, key=NIVEAUX.index)
        pays.append(
            {
                "iso3": iso3,
                "iso2": c["code"],
                "statut": statut,
                "preuves": sorted(preuves[iso3], key=lambda p: -NIVEAUX.index(p["niveau"])),
                "pib_usd": pib.get(iso3),
            }
        )

    return {
        "date": jour.isoformat(),
        "niveaux": NIVEAUX,
        "pib_annee": int(PIB_ANNEE),
        "pib_source": "Banque mondiale (API WDI), PIB en dollars US courants",
        "pays": pays,
        "liaisons": liaisons_retenues,
        "limites": [
            "La source continentale compte 48 offres vérifiées et 25 États en "
            "application effective sans les nommer : seuls les États nommés par "
            "une source du dépôt sont classés à ces niveaux.",
            "L'Annexe 1 (offres acceptées) date d'octobre 2021 ; sa révision "
            "annuelle n'a pas été retrouvée.",
            "Pour l'EAC, la liste d'origines admises est un plafond, pas la liste "
            "des États ayant effectivement commencé à appliquer leur barème.",
        ],
    }
