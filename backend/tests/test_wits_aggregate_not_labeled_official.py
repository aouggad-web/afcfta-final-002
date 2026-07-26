"""
Garde-fou : les 13 pays sourcés via WITS/UNCTAD-TRAINS (agrégat MFN
SimpleAverage au SH6, source de niveau 3 dans la hiérarchie du prompt maître)
ne doivent jamais être étiquetés comme un crawl national officiel vérifié.

Bug trouvé le 2026-07-26 : `backend/routes/calculator.py` ignorait
`source_quality` et forçait `data_source = "crawled_authentic"` /
`tariff_precision = "national_position"` / `rate_source = "Tarif officiel..."`
dès qu'une position était trouvée dans data/crawled/, quelle que soit sa
provenance réelle. Un agrégat WITS (moyenne MFN, TVA nationale standard
recopiée sur chaque ligne, non vérifiée position par position) se retrouvait
donc présenté à l'utilisateur exactement comme une vraie position tarifaire
nationale — l'interdiction absolue du prompt maître ("un agrégat de niveau 3
ne doit jamais servir d'autorité primaire").

Ce module vérifie le mécanisme qui protège désormais contre cette confusion :
CrawledDataService.lookup() doit exposer `source_quality` sur chaque position
normalisée, pour que la route calculateur puisse distinguer les deux cas.
"""

import json
from pathlib import Path

import pytest
from services.crawled_data_service import crawled_service

_CRAWLED_DIR = Path(__file__).resolve().parents[1] / "data" / "crawled"

WITS_COUNTRIES = [
    "AGO",
    "COM",
    "LBY",
    "MDG",
    "MOZ",
    "MRT",
    "MUS",
    "MWI",
    "SDN",
    "STP",
    "SYC",
    "ZMB",
    "ZWE",
]

GENUINE_NATIONAL_CRAWL_COUNTRIES = ["DZA", "EGY", "MAR", "TUN"]


@pytest.fixture(scope="module", autouse=True)
def _loaded():
    crawled_service.load()
    for iso in WITS_COUNTRIES + GENUINE_NATIONAL_CRAWL_COUNTRIES:
        crawled_service._ensure_country_loaded(iso)


@pytest.mark.parametrize("iso", WITS_COUNTRIES)
def test_wits_country_file_declares_partial_national_quality(iso):
    """Le fichier source doit rester honnêtement étiqueté à la racine —
    si ce tag disparaît, le mécanisme de protection en aval perd son signal."""
    path = _CRAWLED_DIR / f"{iso}_tariffs.json"
    assert path.exists(), f"{iso}: fichier introuvable"
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data.get("source_quality") == "crawled_authentic_partial_national", (
        f"{iso}: source_quality inattendue — ce pays est sourcé via un agrégat "
        f"WITS/TRAINS (niveau 3), pas un crawl national authentique"
    )


@pytest.mark.parametrize("iso", WITS_COUNTRIES)
def test_wits_position_carries_partial_quality_flag(iso):
    """CrawledDataService.lookup() doit propager source_quality jusqu'à la
    position normalisée : c'est le seul signal que calculator.py utilise pour
    éviter de mal étiqueter ces 13 pays comme 'crawled_authentic'."""
    hs6_index = crawled_service._hs6_index.get(iso, {})
    assert hs6_index, f"{iso}: index HS6 vide"
    sample_hs6 = next(iter(hs6_index.keys()))
    result = crawled_service.lookup(iso, sample_hs6)
    assert result is not None
    assert result.get("source_quality") == "crawled_authentic_partial_national"


@pytest.mark.parametrize("iso", GENUINE_NATIONAL_CRAWL_COUNTRIES)
def test_genuine_national_crawl_is_not_flagged_as_partial_aggregate(iso):
    """Contrôle négatif : les vrais crawls nationaux (DZA/EGY/MAR/TUN) ne
    doivent PAS porter le tag WITS, sous peine de les dégrader à tort."""
    hs6_index = crawled_service._hs6_index.get(iso, {})
    assert hs6_index, f"{iso}: index HS6 vide"
    sample_hs6 = next(iter(hs6_index.keys()))
    result = crawled_service.lookup(iso, sample_hs6)
    assert result is not None
    assert result.get("source_quality") != "crawled_authentic_partial_national"


def test_wits_dd_rate_is_documented_as_simple_average_not_a_national_rate():
    """La valeur DD elle-même doit rester honnête dans sa formulation brute
    (raw) : une moyenne WITS, jamais présentée comme un taux de ligne
    tarifaire nationale précis."""
    result = crawled_service.lookup("ZMB", "010121")
    assert result is not None
    dd = next(t for t in result["taxes"] if t["code"] == "DD")
    assert "SimpleAverage" in dd["raw_value"] or "MFN" in dd["raw_value"]


def test_wits_vat_note_flags_unverified_per_line_application():
    """La TVA appliquée à chaque ligne SH6 doit conserver sa note d'honnêteté
    ('non vérifié position par position') — c'est cette note que
    calculator.py doit désormais répercuter dans vat_source."""
    result = crawled_service.lookup("ZMB", "010121")
    assert result is not None
    vat = next(t for t in result["taxes"] if t["code"] == "VAT")
    assert "non vérifié" in vat.get("note", "").lower()
