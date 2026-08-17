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


# KRA's implementation material reproduces Legal Notice EAC/321/2022 and
# explicitly lists these 21 origins as eligible at import into Kenya, subject
# to reciprocity and an AfCFTA certificate of origin.
KENYA_ACCEPTED_ORIGINS: FrozenSet[str] = frozenset(
    {
        "BFA",
        "CPV",
        "CMR",
        "CAF",
        "TCD",
        "COG",
        "CIV",
        "COD",
        "GNQ",
        "GAB",
        "GMB",
        "GHA",
        "GIN",
        "LBR",
        "MLI",
        "MRT",
        "NER",
        "NGA",
        "SEN",
        "SLE",
        "TGO",
    }
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
            "https://ikesra.kra.go.ke/bitstream/handle/123456789/2484/"
            "Sensitization%20on%20EAC%20tariff%20Concession%20for%20AfCFTA%20"
            "_EXTERNAL%2027.10.2022.pdf?isAllowed=y&sequence=1"
        ),
        effective_from="2021-01-01",
        accepted_origins=KENYA_ACCEPTED_ORIGINS,
        tariff_dataset="EAC",
        note=(
            "KRA : 21 origines nommément admises; catégorie A; réciprocité et "
            "certificat d'origine ZLECAf obligatoires."
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
        instrument_id="Ordonnance du 23 avril 2025",
        instrument_title="Démantèlement tarifaire ZLECAf de la Côte d'Ivoire",
        instrument_url=("https://onu.diplomatie.gouv.ci/conseil-ministre.php?lang=&num=508"),
        effective_from="2025-04-23",
        accepted_origins=frozenset(),
        tariff_dataset="ECOWAS",
        note=(
            "L'ordonnance conditionne la préférence à la réciprocité; la liste "
            "des partenaires acceptés n'est pas publiée dans la source revue."
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


OFFER_DATASETS = {
    "CMR": "CEMAC",
    "EGY": "EGY",
    "GHA": "ECOWAS",
    "RWA": "EAC",
    "TUN": "TUN",
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
