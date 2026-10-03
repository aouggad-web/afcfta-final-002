import gzip
import json
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parents[1] / "data" / "official_preferential"

# Les instantanés portent leur date de collecte dans leur nom : deux campagnes
# coexistent, et confondre leurs dates masquerait une provenance fausse.
AUGUST = "2026-08-17"
SEPTEMBER = "2026-09-13"
OCTOBER = "2026-10-03"

EXPECTED_MINIMUM_LINES = {
    ("EAC", AUGUST): 4000,
    ("ECOWAS", AUGUST): 4000,
    ("CEMAC", AUGUST): 4000,
    ("EGY", AUGUST): 8000,
    ("TUN", AUGUST): 15000,
    ("ETH", AUGUST): 4000,
    ("ZMB", AUGUST): 4000,
    # Maroc et Zimbabwe : seules destinations de l'e-Tariff Book publiant un
    # barème qui manquaient au dépôt. Le Maroc en publie deux — démantèlement
    # sur 5 ans et sur 10 ans — d'où le seuil doublé.
    ("MAR", SEPTEMBER): 28000,
    ("ZWE", SEPTEMBER): 4000,
    # Tunisie recollectée : l'instantané d'août n'avait pas les chapitres 29,
    # 84 et 85, que l'API ne rend pas à la recherche par chapitre.
    ("TUN", OCTOBER): 23000,
    # Maroc recollecté : il manquait les chapitres 29, 39, 84 et 85.
    ("MAR", OCTOBER): 36000,
    ("ECOWAS", OCTOBER): 6000,
}


def test_all_priority_offer_snapshots_are_complete_and_non_executable():
    for (offer, collected_at), minimum in EXPECTED_MINIMUM_LINES.items():
        path = DATA_DIR / f"{offer}_afcfta_etariff_{collected_at}.json.gz"
        payload = json.loads(gzip.decompress(path.read_bytes()).decode("utf-8"))
        line_count = sum(payload["schedule_line_counts"].values())
        assert line_count >= minimum
        assert payload["legal_effect_status"] == "OFFER_ONLY"
        assert payload["execution_authorized"] is False
        assert payload["source_url"] == "https://etariff.au-afcfta.org/"
        assert payload["source_api_url"].startswith("https://prod-afcfta-api.azurewebsites.net/")
        # La date portée par le nom du fichier doit être celle des métadonnées :
        # un instantané nommé d'une autre date que sa collecte est une
        # provenance fausse, et c'est précisément ce que l'audit reproche.
        assert payload["collected_at"] == collected_at


def test_september_snapshots_carry_the_union_statement_verbatim():
    """
    L'Union africaine ne qualifie pas ces barèmes d'offres en attente.

    Son portail écrit que l'offre « a été adoptée et incluse dans la directive
    ministérielle relative à la liste provisoire de concessions tarifaires ».
    Le fichier doit porter cette déclaration mot pour mot, à côté du verdict du
    dépôt : sans elle, `legal_effect_status=OFFER_ONLY` serait la seule lecture
    disponible et la nuance juridique disparaîtrait.
    """
    for offer in ("MAR", "ZWE"):
        path = DATA_DIR / f"{offer}_afcfta_etariff_{SEPTEMBER}.json.gz"
        payload = json.loads(gzip.decompress(path.read_bytes()).decode("utf-8"))

        statement = payload["source_status_statement"]
        assert statement, f"{offer}: déclaration de la source absente"
        assert "directive ministérielle" in statement["fr"].lower()

        # Le verdict du dépôt reste distinct de la déclaration de la source.
        assert payload["legal_effect_status"] == "OFFER_ONLY"
        assert payload["execution_authorized"] is False


def test_morocco_publishes_two_distinct_dismantling_calendars():
    """
    Les deux barèmes marocains ne sont pas deux rendus du même calendrier.

    L'Union africaine les nomme « Schedule 1 - 5 year Schedule » et
    « Schedule 2 - 10 year Schedule » ; le contenu doit le confirmer, sinon
    l'instantané présenterait deux fois la même concession.
    """
    path = DATA_DIR / f"MAR_afcfta_etariff_{SEPTEMBER}.json.gz"
    payload = json.loads(gzip.decompress(path.read_bytes()).decode("utf-8"))

    first = {row["hs_code"]: row for row in payload["schedules"]["1"]}
    second = {row["hs_code"]: row for row in payload["schedules"]["2"]}
    shared = set(first) & set(second)
    assert len(shared) > 10_000

    horizons = {
        (first[code]["time_frame_years"], second[code]["time_frame_years"])
        for code in shared
        if first[code]["time_frame_years"] and second[code]["time_frame_years"]
    }
    # Le barème 2 étale toujours le démantèlement au moins autant que le 1.
    assert horizons and all(short <= long for short, long in horizons)
    assert any(short < long for short, long in horizons)


def test_snapshots_cover_every_requested_destination():
    destination_to_offer = {
        "KEN": "EAC",
        "RWA": "EAC",
        "GHA": "ECOWAS",
        "CIV": "ECOWAS",
        "NGA": "ECOWAS",
        "CMR": "CEMAC",
        "EGY": "EGY",
        "TUN": "TUN",
        "ETH": "ETH",
        "ZMB": "ZMB",
    }
    for offer in destination_to_offer.values():
        assert (DATA_DIR / f"{offer}_afcfta_etariff_{AUGUST}.json.gz").exists()
    for offer in ("MAR", "ZWE"):
        assert (DATA_DIR / f"{offer}_afcfta_etariff_{SEPTEMBER}.json.gz").exists()


def _lignes(offer, date, schedule="1"):
    path = DATA_DIR / f"{offer}_afcfta_etariff_{date}.json.gz"
    payload = json.loads(gzip.decompress(path.read_bytes()).decode("utf-8"))
    return {row["hs_code"]: row for row in payload["schedules"][schedule]}


def test_october_snapshots_have_the_chapters_earlier_ones_missed():
    """Le chapitre vide est relu position par position : les chapitres
    manquants sont présents, et aucune ligne antérieure n'a changé."""
    for offer, avant, manquants in (
        ("TUN", AUGUST, {"29", "84", "85"}),
        ("MAR", SEPTEMBER, {"29", "39", "84", "85"}),
        ("CEMAC", AUGUST, {"84"}),
        ("EGY", AUGUST, {"84"}),
        ("ECOWAS", AUGUST, {"84"}),
    ):
        ancien, octobre = _lignes(offer, avant), _lignes(offer, OCTOBER)
        assert manquants <= {code[:2] for code in octobre}
        assert all(octobre.get(code) == row for code, row in ancien.items())
