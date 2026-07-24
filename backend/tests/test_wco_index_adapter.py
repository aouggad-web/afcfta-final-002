import asyncio
import hashlib
import json
from pathlib import Path

from routes.hs_codes import search_product_index
from services import omd_hs_index_service
from services.wco_index_adapter import get_wco_index_metadata, search_wco_index

DATA_DIR = Path(__file__).resolve().parents[1] / "data"


def test_adapter_uses_unchanged_canonical_corpus_and_metadata():
    index_path = DATA_DIR / "omd_hs_index.json"
    metadata = get_wco_index_metadata()
    assert hashlib.sha256(index_path.read_bytes()).hexdigest() == metadata["source_sha256"]
    assert metadata == {
        "hs_version": "HS2022",
        "edition": 7,
        "entry_count": 6344,
        "source_sha256": "c84ea861a183b0c25a16ae343f7f4c3e04fac439822ca62930e09355175f2c87",
        "acquisition_date": None,
        "source_url": None,
        "license_status": "TO_BE_VERIFIED",
        "redistribution_allowed": False,
    }
    corpora = []
    for path in DATA_DIR.glob("omd_hs_index*.json"):
        payload = json.loads(path.read_text(encoding="utf-8"))
        if "entries" in payload:
            corpora.append(path.name)
    assert corpora == ["omd_hs_index.json"]


def test_palm_oil_results_are_consistent_before_and_after_adapter():
    raw = omd_hs_index_service.search("huile de palme", limit=10)
    adapted = search_wco_index("huile de palme", limit=10)
    assert adapted["matches"][0]["label"] == raw["results"][0]["label"]
    assert [p["code"] for p in adapted["matches"][0]["candidate_positions"]] == raw["results"][0][
        "hs_codes"
    ]
    assert "1511" in raw["results"][0]["hs_codes"]


def test_cross_reference_and_ambiguous_term_are_preserved():
    cross_reference = search_wco_index("abricots", limit=10)
    assert any(match["references"] for match in cross_reference["matches"])
    ambiguous = search_wco_index("or", limit=20)
    assert ambiguous["count"] > 1
    assert len({match["label"] for match in ambiguous["matches"]}) > 1


def test_hs4_position_is_not_expanded_to_hs6():
    result = search_wco_index("huile de palme", limit=1)
    positions = result["matches"][0]["candidate_positions"]
    assert any(p == {"code": "1511", "level": "HS4"} for p in positions)
    assert not any(p["code"].startswith("1511") and len(p["code"]) == 6 for p in positions)


def test_adapter_rejects_a_different_hs_version():
    try:
        search_wco_index("huile de palme", hs_version="HS2017")
    except ValueError as exc:
        assert "HS2022" in str(exc)
    else:
        raise AssertionError("A mismatched HS version must be rejected")


def test_product_index_endpoint_returns_search_results_not_the_corpus():
    result = asyncio.run(search_product_index(q="huile de palme", language="fr", limit=2))
    assert result["results"]
    assert result["metadata"]["hs_version"] == "HS2022"
    assert result["metadata"]["redistribution_allowed"] is False
    assert "entries" not in result
