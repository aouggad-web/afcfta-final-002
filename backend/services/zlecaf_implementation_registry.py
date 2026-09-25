"""Reviewed legal gates for applying an AfCFTA import preference.

An AfCFTA tariff offer, ratification or GTI participation is not enough. A
calculation is authorised only where we have all of the following:

* a domestic/regional implementation instrument in force;
* an exact set of origin countries accepted on a reciprocal basis;
* a line-level tariff schedule; and
* the usual proof-of-origin condition (verified at customs, not by this app).

The registry is intentionally fail-closed. OFFER_ONLY and
PARTNER_NOTICE_REQUIRED records are useful audit evidence, but never authorise
a preferential calculation.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import FrozenSet, Optional

from services.zlecaf_schedule_egy import ORIGINES_PAR_GROUPE
from services.zlecaf_schedule_mar import ORIGINES_PAR_GROUPE as MAR_ORIGINES

APPLIED = "APPLIED"
OFFER_ONLY = "OFFER_ONLY"
PARTNER_NOTICE_REQUIRED = "PARTNER_NOTICE_REQUIRED"
NOT_AVAILABLE = "NOT_AVAILABLE"


@dataclass(frozen=True)
class ImplementationRecord:
    destination_iso3: str
    status: str
    instrument_id: Optional[str]
    instrument_title: str
    instrument_url: str
    effective_from: Optional[str]
    accepted_origins: FrozenSet[str]
    tariff_dataset: Optional[str]
    note: str


# Les origines admises à l'importation au Kenya ne sont PAS nommées par
# l'instrument tarifaire. Vérifié le 23/09/2026 sur le texte gazetté lui-même
# (347 pages) : ZÉRO occurrence d'un nom de pays. Sa page 1 renvoie ailleurs :
#
#   « SCHEDULE APPLICABLE TO State Parties with Provisional Schedule of Tariff
#     Concessions in Annex 1 to the Ministerial Directive on the Application of
#     Provisional Schedules of Tariff Concessions »
#
# Cette Annexe 1 — Directive ministérielle 1/2021, AfCFTA/COM/7/DIRECTIVE/FINAL,
# Conseil des ministres de la ZLECAf, Accra, 10 octobre 2021 — liste 29 parties,
# reprises ici telles qu'elle les énumère. Fiche : ZLECAF_origines_annexe1_2026-09-23.json
#
# LA LISTE PRÉCÉDENTE PORTAIT 21 PAYS ET N'AVAIT AUCUNE SOURCE. Elle était
# l'Annexe 1 privée de huit entrées (EGY, MDG, MWI, MUS, SYC, ZMB, BEN, GNB)
# sans règle qui l'explique : le Liberia, astérisqué « subject to ratification »
# au même titre que le Bénin et la Guinée-Bissau, y avait lui été conservé. Le
# commentaire qui l'accompagnait affirmait que la KRA « lists these 21 origins » ;
# le document qu'il invoquait est injoignable, et le texte normatif ne nomme
# personne.
#: L'Annexe 1 TELLE QU'ELLE EST PUBLIÉE : 29 parties, dont trois marquées
#: « * Subject to ratification ». On la consigne entière et sans retouche ; ce
#: qui en est opérant est décidé plus bas.
ANNEXE1_PARTIES_2021: FrozenSet[str] = frozenset(
    {
        # Parties ayant soumis individuellement (Annexe 1, première liste)
        "COD",  # Democratic Republic of Congo
        "EGY",  # Egypt
        "MDG",  # Madagascar
        "MWI",  # Malawi
        "MUS",  # Mauritius
        "SYC",  # Seychelles
        "ZMB",  # Zambia
        # CEMAC Member States
        "GAB",
        "CMR",
        "CAF",
        "TCD",
        "COG",
        "GNQ",
        # ECOWAS Member States + Mauritania
        "BEN",  # astérisqué : subject to ratification
        "BFA",
        "CPV",
        "CIV",
        "GMB",
        "GHA",
        "GIN",
        "GNB",  # astérisqué : subject to ratification
        "LBR",  # astérisqué : subject to ratification
        "MLI",
        "MRT",
        "NER",
        "NGA",
        "SEN",
        "SLE",
        "TGO",
    }
)

#: Les trois entrées que l'Annexe 1 marque d'un astérisque — « * Subject to
#: ratification ». L'Annexe ne les liste donc PAS inconditionnellement : les
#: retenir sans leur condition serait moins fidèle à la source, pas plus.
ANNEXE1_SOUS_RESERVE_DE_RATIFICATION: FrozenSet[str] = frozenset({"BEN", "GNB", "LBR"})

#: Des trois, deux ont depuis déposé leur ratification ; le Bénin ne l'a pas
#: fait — c'est le statut continental que le dépôt tient par ailleurs, et c'est
#: `build_bilateral_application_matrix` qui le dit, pas moi.
#:
#: La condition de l'Annexe n'est donc pas remplie pour lui. Il est écarté de la
#: liste opérante et entrera le jour où il ratifiera, sans qu'on touche à la
#: transcription de l'Annexe ci-dessus.
#:
#: Ce n'est pas une précaution de forme. Le moteur écarte déjà une origine non
#: ratifiante avant même de lire les listes, si bien qu'aucune préférence ne lui
#: serait servie dans tous les cas. Mais le dépôt tient un registre des
#: CONTRADICTIONS entre un acte national qui nomme une origine et le statut
#: continental qui la dément, et il s'impose que ce registre reste vide sur les
#: listes réelles. Déclarer le Bénin admis y aurait inscrit une contradiction
#: qui n'existe que parce qu'on aurait négligé un astérisque.
ORIGINES_ECARTEES_FAUTE_DE_RATIFICATION: FrozenSet[str] = frozenset({"BEN"})

KENYA_ACCEPTED_ORIGINS: FrozenSet[str] = (
    ANNEXE1_PARTIES_2021 - ORIGINES_ECARTEES_FAUTE_DE_RATIFICATION
)

#: CE QUE CETTE LISTE N'ÉTABLIT PAS, et qu'aucune source atteignable n'établit.
#:
#: 1. Qu'elle soit À JOUR. L'Annexe est datée d'octobre 2021 et le §20 de la
#:    directive prévoit sa révision annuelle : « Such review shall include
#:    regular updates of the Annex to this Directive. » Aucune version
#:    postérieure n'a été retrouvée.
#: 2. Que figurer à l'Annexe SUFFISE. Le §16 (ii) réserve : un État n'est pas
#:    tenu de servir la préférence « with respect to products imported from
#:    State Parties that have not yet start the implementation of their
#:    Provisional Schedules of Tariff Concessions ». Avoir SOUMIS un barème
#:    n'est pas avoir COMMENCÉ à l'appliquer. La liste de ceux qui ont commencé
#:    n'est pas publiée.
#:
#: Ces deux réserves vont dans le même sens : la liste est un PLAFOND, jamais un
#: droit acquis. Elle peut être trop large, pas trop étroite.
KENYA_ORIGINS_RESERVES = (
    "Annexe 1 datée du 10/10/2021, révision annuelle prévue (§20) mais non "
    "retrouvée ; la soumission d'un barème ne vaut pas mise en œuvre effective "
    "(§16 ii), et la liste des États ayant effectivement commencé n'est pas "
    "publiée. Liste à traiter comme un plafond."
)


RECORDS = {
    "KEN": ImplementationRecord(
        destination_iso3="KEN",
        status=APPLIED,
        instrument_id="EAC/321/2022",
        instrument_title=(
            "EAC Legal Notice EAC/321/2022 — implementation of Category A "
            "AfCFTA tariff concessions"
        ),
        instrument_url=(
            "https://www.kra.go.ke/images/publications/"
            "EAC-PROVISIONAL-SCHEDULE-OF-TARIFF-CONCESSIONS-FOR-THE-AFRICAN-"
            "CONTINENTAL-FREE-TRADE-AREA-AfCFTA-CATEGORY-A-PRODUCTS.pdf"
        ),
        effective_from="2021-01-01",
        accepted_origins=KENYA_ACCEPTED_ORIGINS,
        tariff_dataset="EAC",
        note=(
            "Catégorie A, gazetté au Journal de l'EAC le 06/09/2022. Les 29 "
            "origines viennent de l'Annexe 1 de la Directive ministérielle "
            "1/2021 (10/10/2021) : le barème lui-même ne nomme aucun pays. "
            "Trois sont sous réserve de ratification, et la liste est un "
            "plafond — voir KENYA_ORIGINS_RESERVES."
        ),
    ),
    # Les deux circulaires égyptiennes (n° 38 de 2024, complétée par la n° 44
    # de 2025) nomment 19 origines et ne réduisent que la liste A ; le taux est
    # calculé depuis le NPF par zlecaf_schedule_egy, jamais servi depuis
    # l'e-Tariff Book, dont la carte d'origines contredit l'acte national.
    "EGY": ImplementationRecord(
        destination_iso3="EGY",
        status=APPLIED,
        instrument_id="منشور اتفاقيات رقم 38 لسنة 2024",
        instrument_title=(
            "Circulaire Accords n° 38 de 2024, complétée par la n° 44 de 2025 "
            "— activation de l'AfCFTA à l'importation en Égypte"
        ),
        instrument_url="https://customs.gov.eg/Upload/ECAAdminace/ECAAdminace987843099.pdf",
        effective_from="2025-01-01",
        accepted_origins=frozenset(ORIGINES_PAR_GROUPE),
        tariff_dataset="EGY",
        note=(
            "Liste A seulement (une ligne B ou C reste au NPF), 19 origines "
            "réparties en deux groupes de 5 et 10 ans ; chapitres 50 à 63 et "
            "87 reportés (n° 44). Taux calculés depuis le NPF par le calendrier "
            "national — voir EGY_rapprochement_baremes_2026-09-24.json."
        ),
    ),
    # Le Maroc a deux textes lus intégralement : la circulaire ADII 6530/223 du
    # 22/01/2024 (liste A, listes P1/P2) et l'avenant 6627/223 du 09/01/2025
    # (codes de la liste A pour la LF2025 ; P1/P2 inchangés). Le DI vient de
    # l'e-Tariff Book sélectionné par les listes P1/P2 de la fiche ; la TPI est
    # démantelée sur le même calendrier (zlecaf_schedule_mar).
    "MAR": ImplementationRecord(
        destination_iso3="MAR",
        status=APPLIED,
        instrument_id="6530/223",
        instrument_title=(
            "Circulaire ADII n° 6530/223 — Mise en œuvre de l'Accord ZLECAf "
            "(complétée par l'avenant n° 6627/223 du 09/01/2025)"
        ),
        instrument_url="https://ecoactu.ma/wp-content/uploads/2024/01/circulaire_93343.pdf",
        effective_from="2021-01-01",
        accepted_origins=frozenset(MAR_ORIGINES),
        tariff_dataset="MAR",
        note=(
            "Liste A seulement (B et C non mises en œuvre) ; 40 origines en "
            "P1 (5 ans) et P2 (10 ans), lues dans la fiche. DI servi depuis "
            "l'e-Tariff Book sélectionné par les listes nationales ; TPI "
            "démantelée sur le même calendrier — voir zlecaf_schedule_mar.py."
        ),
    ),
    # Regulation 574/2025 is in force and contains Ethiopia's schedule, but
    # article 3(2) delegates the applicable partner list to a separate notice.
    "ETH": ImplementationRecord(
        destination_iso3="ETH",
        status=PARTNER_NOTICE_REQUIRED,
        instrument_id="Regulation 574/2025",
        instrument_title="Council of Ministers Regulation 574/2025 implementing AfCFTA tariff concessions",
        instrument_url=(
            "https://justice.gov.et/en/law/%E1%8B%A8%E1%8A%A0%E1%8D%8D%E1%88%AA"
            "%E1%8A%AB-%E1%8A%A0%E1%88%85%E1%8C%89%E1%88%AB%E1%8B%8A-%E1%8A%90"
            "%E1%8C%BB-%E1%8A%95%E1%8C%8D%E1%8B%B5-%E1%89%80%E1%8C%A0%E1%8A%93"
            "-%E1%88%B5%E1%88%9D%E1%88%9D/"
        ),
        effective_from="2025-08-14",
        accepted_origins=frozenset(),
        tariff_dataset="ETH",
        note=(
            "Le règlement est en vigueur, mais son article 3(2) exige la liste "
            "des États notifiée séparément par le ministère; liste officielle "
            "non retrouvée."
        ),
    ),
    "ZMB": ImplementationRecord(
        destination_iso3="ZMB",
        status=PARTNER_NOTICE_REQUIRED,
        instrument_id="SI 92/2024",
        instrument_title="Statutory Instrument 92 of 2024 — Zambia AfCFTA PSTC",
        instrument_url="https://www.parliament.gov.zm/node/12434",
        effective_from="2024-12-30",
        accepted_origins=frozenset(),
        tariff_dataset="ZMB",
        note=(
            "Le Parlement confirme la domestication et l'usage sous GTI, mais "
            "aucune liste officielle exhaustive des origines réciproques n'a "
            "été retrouvée."
        ),
    ),
    "CIV": ImplementationRecord(
        destination_iso3="CIV",
        status=PARTNER_NOTICE_REQUIRED,
        instrument_id="Ordonnance n° 2025-260 du 23 avril 2025",
        instrument_title="Démantèlement tarifaire ZLECAf de la Côte d'Ivoire",
        instrument_url=("https://onu.diplomatie.gouv.ci/conseil-ministre.php?lang=&num=508"),
        # L'ordonnance n'est pas en vigueur tant que les décrets d'application
        # ne sont pas pris (rapport d'activités 2025 du CN-ZLECAf).
        effective_from=None,
        accepted_origins=frozenset(),
        tariff_dataset="ECOWAS",
        note=(
            "Ordonnance n° 2025-260 du 23/04/2025 adoptée ; texte non lu ; "
            "décrets d'application et circulaires en attente (rapport CN-ZLECAf "
            "2025) ; aucune liste d'origines."
        ),
    ),
    "NGA": ImplementationRecord(
        destination_iso3="NGA",
        status=PARTNER_NOTICE_REQUIRED,
        instrument_id="PSTC gazettée en avril 2025",
        instrument_title="Nigeria — gazetting of the AfCFTA PSTC",
        instrument_url="https://x.com/AfCFTA/status/1911814539785494880",
        effective_from="2025-04-15",
        accepted_origins=frozenset(),
        tariff_dataset="ECOWAS",
        note=(
            "La domestication est confirmée, mais aucune liste officielle des "
            "corridors réciproques acceptés n'a été retrouvée."
        ),
    ),
}


# Destinations dont un barème officiel est archivé sans que l'application
# nationale et la réciprocité aient été vérifiées. Sans cette entrée, la
# décision retomberait sur NOT_AVAILABLE et ne distinguerait plus « aucune
# donnée » de « donnée collectée, portail juridique non franchi » — deux
# situations qui n'appellent pas le même travail.
OFFER_DATASETS = {
    "CMR": "CEMAC",
    "EGY": "EGY",
    "GHA": "ECOWAS",
    "MAR": "MAR",
    "RWA": "EAC",
    "TUN": "TUN",
    "ZWE": "ZWE",
}


def implementation_record(destination_iso3: str) -> Optional[ImplementationRecord]:
    return RECORDS.get((destination_iso3 or "").upper())


def implementation_decision(destination_iso3: str, origin_iso3: str) -> dict:
    """Return a fail-closed destination/origin legal application decision."""
    destination = (destination_iso3 or "").upper()
    origin = (origin_iso3 or "").upper()
    record = RECORDS.get(destination)

    if record is None:
        dataset = OFFER_DATASETS.get(destination)
        if dataset:
            return {
                "applied": False,
                "status": OFFER_ONLY,
                "tariff_dataset": dataset,
                "note": (
                    "Une offre tarifaire officielle est archivée, mais aucune "
                    "preuve nationale complète d'application et de réciprocité "
                    "pour cette origine n'a été vérifiée — taux NPF appliqué."
                ),
                "record": None,
            }
        return {
            "applied": False,
            "status": NOT_AVAILABLE,
            "tariff_dataset": None,
            "note": (
                "Aucune preuve vérifiée d'application bilatérale du tarif "
                "ZLECAf à l'importation — taux NPF appliqué."
            ),
            "record": None,
        }

    if record.status != APPLIED:
        return {
            "applied": False,
            "status": record.status,
            "tariff_dataset": record.tariff_dataset,
            "note": f"{record.note} Taux NPF appliqué.",
            "record": record,
        }

    if origin not in record.accepted_origins:
        return {
            "applied": False,
            "status": NOT_AVAILABLE,
            "tariff_dataset": record.tariff_dataset,
            "note": (
                f"{record.instrument_id} : {origin} ne figure pas dans la liste "
                "officielle des origines admises — taux NPF appliqué."
            ),
            "record": record,
        }

    return {
        "applied": True,
        "status": APPLIED,
        "tariff_dataset": record.tariff_dataset,
        "note": record.note,
        "record": record,
    }
