"""
Réseau ZLECAf : statut de mise en œuvre de chaque État et liaisons
préférentielles entre États, pour la carte « Réseau ZLECAf ».

Rien n'est saisi ici : tout est lu dans les modules qui servent déjà le moteur
de calcul, et chaque statut porte la ou les preuves qui le fondent.

* Signature et ratification : ``zlecaf_membership_status`` (the dtic / SARS,
  « Update on the AfCFTA », mars 2026).
* Offre tarifaire : soit l'État figure à l'Annexe 1 de la Directive
  ministérielle 1/2021 (« have submitted Provisional Schedules of Tariff
  Concessions », §5), soit un barème officiel de son offre est archivé dans le
  dépôt (``OFFER_DATASETS``). Ni l'un ni l'autre ne prouve qu'il l'applique.
* Instrument national adopté : enregistrement ``PARTNER_NOTICE_REQUIRED`` du
  registre — texte adopté ou gazetté, application aux partenaires non établie.
* Déploiement : l'État applique lui-même la préférence à l'importation, par un
  instrument en vigueur à la date demandée — enregistrement ``APPLIED`` dont
  l'application a commencé, ou General Note O de l'Afrique du Sud.

Être nommé dans la liste de partenaires d'un AUTRE État (General Note O,
circulaire algérienne…) crée une liaison, jamais un déploiement : le dépôt
établit par exemple que le Burundi, nommé par l'Afrique du Sud, n'a pas de date
d'application établie (fiche BDI_application_2026-09-27.json).

Le statut retenu est le plus avancé des niveaux établis ; un État non signataire
ou non ratifiant reste à ce statut quelles que soient les autres mentions.

Une liaison A → B signifie : « A applique la préférence ZLECAf aux produits
originaires de B », d'après l'instrument de A, à partir de sa date d'effet. Les
origines non ratifiantes sont écartées, comme le fait le moteur. Pour l'EAC, la
liste d'origines est un plafond (voir ``KENYA_ORIGINS_RESERVES``).

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
from services.zlecaf_schedule_zaf import DATES_ENTREE_ZAF

PIB_ANNEE = "2024"

WORLDBANK_PATH = (
    Path(__file__).resolve().parent.parent.parent / "data" / "json" / "worldbank_data_latest.json"
)

# Niveaux, du moins avancé au plus avancé. L'ordre est aussi celui de la légende.
NON_SIGNATAIRE = "non_signataire"
SIGNE_NON_RATIFIE = "signe_non_ratifie"
RATIFIE = "ratifie"
OFFRE_TARIFAIRE = "offre_tarifaire"
INSTRUMENT_ADOPTE = "instrument_adopte"
DEPLOIEMENT = "deploiement"

NIVEAUX = [
    NON_SIGNATAIRE,
    SIGNE_NON_RATIFIE,
    RATIFIE,
    OFFRE_TARIFAIRE,
    INSTRUMENT_ADOPTE,
    DEPLOIEMENT,
]

# Libellés composés par ce module (les titres d'instruments viennent du
# registre, tels que les textes les donnent).
TEXTES = {
    "fr": {
        "adhesion": "the dtic / SARS, « Update on the AfCFTA », newsletter mars 2026",
        "ratifie_note": "Statut par défaut des États que la source ne cite ni parmi "
        "les non-signataires ni parmi les non-ratifiants.",
        "annexe1": "Directive ministérielle 1/2021 (AfCFTA/COM/7/DIRECTIVE/FINAL), "
        "Annexe 1 — liste provisoire de concessions soumise, Conseil des ministres "
        "de la ZLECAf, Accra, 10/10/2021",
        "bareme": "Barème tarifaire officiel de l'offre (jeu « {jeu} »)",
        "bareme_note": "Barème archivé ; aucune preuve nationale complète "
        "d'application n'a été vérifiée.",
        "zaf": "General Note O du Schedule No. 1 (Customs and Excise Act, 1964, "
        "Afrique du Sud), telle qu'amendée par les Notices R.4287, R.5879, R.6233, "
        "R.6595 et R.6756 du Government Gazette",
        "zaf_note": "La préférence sud-africaine court à partir de la date d'effet de "
        "la Notice qui a ajouté chaque partenaire ; les membres de la SACU échangent "
        "sous le régime SACU, pas sous la ZLECAf.",
        "pib_source": "Banque mondiale (API WDI), PIB en dollars US courants",
    },
    "en": {
        "adhesion": "the dtic / SARS, “Update on the AfCFTA” newsletter, March 2026",
        "ratifie_note": "Default status of States the source names neither among "
        "non-signatories nor among non-ratifying States.",
        "annexe1": "Ministerial Directive 1/2021 (AfCFTA/COM/7/DIRECTIVE/FINAL), "
        "Annex 1 — provisional schedule of concessions submitted, AfCFTA Council of "
        "Ministers, Accra, 10/10/2021",
        "bareme": "Official tariff schedule of the offer (dataset “{jeu}”)",
        "bareme_note": "Schedule archived; no complete national proof of application "
        "has been verified.",
        "zaf": "General Note O to Schedule No. 1 (Customs and Excise Act, 1964, South "
        "Africa), as amended by Government Gazette Notices R.4287, R.5879, R.6233, "
        "R.6595 and R.6756",
        "zaf_note": "South Africa's preference runs from the effective date of the "
        "Notice that added each partner; SACU members trade under SACU, not the "
        "AfCFTA.",
        "pib_source": "World Bank (WDI API), GDP in current US dollars",
    },
}


def _preuve(niveau: str, source: str, url: Optional[str] = None, note: Optional[str] = None):
    out = {"niveau": niveau, "source": source}
    if url:
        out["url"] = url
    if note:
        out["note"] = note
    return out


@lru_cache(maxsize=4)
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


def _date(iso: str) -> date:
    annee, mois, jour = (int(x) for x in iso.split("-"))
    return date(annee, mois, jour)


def construire_reseau(jour: Optional[date] = None, lang: str = "fr") -> dict:
    """Statuts des États de ``AFRICAN_COUNTRIES`` et liaisons préférentielles."""
    jour = jour or date.today()
    t = TEXTES["en" if lang == "en" else "fr"]
    iso3s = [c["iso3"] for c in AFRICAN_COUNTRIES]
    preuves: Dict[str, List[dict]] = {k: [] for k in iso3s}

    def ajouter(iso3: str, preuve: dict) -> None:
        if iso3 in preuves:
            preuves[iso3].append(preuve)

    for iso3 in iso3s:
        statut = membership.ratification_status(iso3)
        if statut == membership.STATUS_NOT_SIGNED:
            ajouter(iso3, _preuve(NON_SIGNATAIRE, t["adhesion"]))
        elif statut == membership.STATUS_SIGNED_NOT_RATIFIED:
            ajouter(iso3, _preuve(SIGNE_NON_RATIFIE, t["adhesion"]))
        else:
            ajouter(
                iso3,
                _preuve(RATIFIE, t["adhesion"], note=t["ratifie_note"]),
            )

    for iso3 in registry.ANNEXE1_PARTIES_2021:
        ajouter(
            iso3,
            _preuve(OFFRE_TARIFAIRE, t["annexe1"], note=registry.KENYA_ORIGINS_RESERVES),
        )

    for iso3, jeu in registry.OFFER_DATASETS.items():
        ajouter(
            iso3,
            _preuve(
                OFFRE_TARIFAIRE,
                t["bareme"].format(jeu=jeu),
                note=t["bareme_note"],
            ),
        )

    for iso3, record in registry.RECORDS.items():
        if record.status == registry.PARTNER_NOTICE_REQUIRED:
            ajouter(
                iso3,
                _preuve(
                    INSTRUMENT_ADOPTE, record.instrument_title, record.instrument_url, record.note
                ),
            )

    liaisons: List[dict] = []
    for iso3, record in registry.RECORDS.items():
        if record.status != registry.APPLIED or not registry.application_commencee(iso3, jour):
            continue
        ajouter(
            iso3,
            _preuve(DEPLOIEMENT, record.instrument_title, record.instrument_url, record.note),
        )
        for origine in sorted(record.accepted_origins):
            liaisons.append(
                {
                    "importateur": iso3,
                    "origine": origine,
                    "depuis": record.effective_from,
                    "source": record.instrument_title,
                    "url": record.instrument_url,
                }
            )

    # Afrique du Sud : General Note O, partenaire par partenaire, à sa date d'effet.
    partenaires_zaf = {p: d for p, d in sorted(DATES_ENTREE_ZAF.items()) if _date(d) <= jour}
    if partenaires_zaf:
        ajouter("ZAF", _preuve(DEPLOIEMENT, t["zaf"], note=t["zaf_note"]))
    for partenaire, depuis in partenaires_zaf.items():
        liaisons.append(
            {"importateur": "ZAF", "origine": partenaire, "depuis": depuis, "source": t["zaf"]}
        )

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
                "nom_constants": c["name"],
                "statut": statut,
                "preuves": sorted(preuves[iso3], key=lambda p: -NIVEAUX.index(p["niveau"])),
                "pib_usd": pib.get(iso3),
            }
        )

    return {
        "date": jour.isoformat(),
        "niveaux": NIVEAUX,
        "pib_annee": int(PIB_ANNEE),
        "pib_source": t["pib_source"],
        "pays": pays,
        "liaisons": liaisons_retenues,
    }
