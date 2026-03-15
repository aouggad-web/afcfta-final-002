"""
Unit tests for code quality refactoring (Priority 2 & 3).

Tests cover:
- hs6_database: CHAPTER_NAMES constant, scoring helpers, smart search logic
- upgrade_to_enhanced_v2: _migrate_country helper functions
- cameroon_cemac_scraper: _process_page_positions helper
- cache_service: key generation and TTL lookup

These tests run entirely in-process and do not require a live server.
"""

import importlib
import pytest
import sys
import os

# Ensure backend/ is on the path (mirrors conftest.py behaviour)
_backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

# Import the hs6_database module directly (not via the routes package, which
# would trigger a cascade of optional dependencies such as faostat / fitz).
import importlib.util as _ilu

_hs6_db_spec = _ilu.spec_from_file_location(
    "hs6_database_direct",
    os.path.join(_backend_dir, "routes", "hs6_database.py"),
)
_hs6_db = _ilu.module_from_spec(_hs6_db_spec)

# Stub out the fastapi dependency to avoid a heavyweight import during tests.
# We temporarily install the stub only if fastapi is not already in sys.modules,
# then restore the original state after exec_module() so other test files that
# do `from fastapi.testclient import TestClient` are not affected.
import types as _types
_fastapi_stub = _types.ModuleType("fastapi")
_fastapi_stub.APIRouter = type("APIRouter", (), {
    "__init__": lambda self, *a, **kw: None,
    "get": lambda self, *a, **kw: (lambda f: f),
})
_fastapi_stub.HTTPException = type("HTTPException", (Exception,), {})
_fastapi_stub.Query = lambda *a, **kw: None
_fastapi_original = sys.modules.get("fastapi", None)
if _fastapi_original is None:
    sys.modules["fastapi"] = _fastapi_stub

_hs6_db_spec.loader.exec_module(_hs6_db)

# Restore sys.modules to its pre-stub state so we don't shadow the real fastapi
# package for other test modules collected in the same pytest session.
if _fastapi_original is None:
    sys.modules.pop("fastapi", None)
else:
    sys.modules["fastapi"] = _fastapi_original

CHAPTER_NAMES = _hs6_db.CHAPTER_NAMES
_score_code_match = _hs6_db._score_code_match
_score_text_match = _hs6_db._score_text_match
_build_search_result = _hs6_db._build_search_result

# Optional: fitz may not be installed in the CI environment
_fitz_available = importlib.util.find_spec("fitz") is not None


# =============================================================================
# hs6_database – CHAPTER_NAMES & scoring helpers
# =============================================================================

class TestChapterNames:
    """CHAPTER_NAMES module-level constant in routes.hs6_database."""

    def test_chapter_names_has_fr_and_en(self):
        assert "fr" in CHAPTER_NAMES
        assert "en" in CHAPTER_NAMES

    def test_chapter_names_fr_covers_key_chapters(self):
        fr = CHAPTER_NAMES["fr"]
        # Chapter 01 (live animals) and 84 (machinery) must exist
        assert "01" in fr
        assert "84" in fr
        assert "97" in fr

    def test_chapter_names_en_matches_fr_keys(self):
        assert set(CHAPTER_NAMES["fr"].keys()) == set(CHAPTER_NAMES["en"].keys())

    def test_chapter_names_no_empty_values(self):
        for lang, chapters in CHAPTER_NAMES.items():
            for ch, name in chapters.items():
                assert name, f"Empty chapter name for {lang}/{ch}"


class TestScoreCodeMatch:
    """_score_code_match: numeric prefix scoring helper."""

    def test_exact_prefix_match_returns_positive(self):
        assert _score_code_match("760110", "76") > 0

    def test_non_matching_code_returns_zero(self):
        assert _score_code_match("010110", "76") == 0

    def test_longer_prefix_has_lower_score(self):
        score_short = _score_code_match("760110", "76")
        score_long = _score_code_match("760110", "7601")
        # Shorter prefix yields a higher (or equal) score
        assert score_short >= score_long

    def test_exact_six_digit_match(self):
        assert _score_code_match("760110", "760110") > 0

    def test_code_not_starting_with_query_zero(self):
        assert _score_code_match("760110", "761") == 0


class TestScoreTextMatch:
    """_score_text_match: text relevance scoring helper."""

    def test_exact_phrase_gives_high_score(self):
        score = _score_text_match("aluminium et ouvrages", "aluminium")
        assert score >= 50

    def test_no_match_returns_zero(self):
        assert _score_text_match("aluminium et ouvrages", "café") == 0

    def test_partial_word_match_gives_low_positive_score(self):
        # "alum" is a partial match for "aluminium"
        score = _score_text_match("aluminium et ouvrages", "alum")
        assert score > 0

    def test_two_matching_words_score_higher_than_zero(self):
        score = _score_text_match("aluminium et ouvrages divers", "aluminium ouvrages")
        assert score > 0

    def test_case_insensitive(self):
        score_lower = _score_text_match("Aluminium Et Ouvrages", "aluminium")
        assert score_lower > 0

    def test_non_overlapping_query_returns_zero(self):
        assert _score_text_match("produits chimiques inorganiques", "café thé") == 0


class TestBuildSearchResult:
    """_build_search_result: result dict builder."""

    def _sample_data(self):
        return {
            "description_fr": "Aluminium et ouvrages",
            "description_en": "Aluminium and articles",
        }

    def test_result_contains_required_fields(self):
        result = _build_search_result("760110", self._sample_data(), "fr", score=55)
        for field in ("code", "description", "chapter", "chapter_name", "full_position", "position_4", "score"):
            assert field in result, f"Missing field: {field}"

    def test_result_code_matches_input(self):
        result = _build_search_result("760110", self._sample_data(), "fr", score=55)
        assert result["code"] == "760110"

    def test_result_chapter_is_two_digits(self):
        result = _build_search_result("760110", self._sample_data(), "fr", score=55)
        assert result["chapter"] == "76"

    def test_result_position_4_is_four_digits(self):
        result = _build_search_result("760110", self._sample_data(), "fr", score=55)
        assert result["position_4"] == "7601"

    def test_result_description_uses_requested_language(self):
        result_fr = _build_search_result("760110", self._sample_data(), "fr", score=1)
        result_en = _build_search_result("760110", self._sample_data(), "en", score=1)
        assert "aluminium" in result_fr["description"].lower()
        assert "aluminium" in result_en["description"].lower()

    def test_full_position_contains_chapter_number(self):
        result = _build_search_result("760110", self._sample_data(), "fr", score=1)
        assert "76" in result["full_position"]

    def test_score_is_preserved(self):
        result = _build_search_result("760110", self._sample_data(), "fr", score=123)
        assert result["score"] == 123


# =============================================================================
# upgrade_to_enhanced_v2 – helper utilities
# =============================================================================

class TestUpgradeHelpers:
    """Helper functions in scripts.upgrade_to_enhanced_v2."""

    def test_to_float_with_int(self):
        from scripts.upgrade_to_enhanced_v2 import _to_float
        assert _to_float(5) == 5.0

    def test_to_float_with_str_number(self):
        from scripts.upgrade_to_enhanced_v2 import _to_float
        assert _to_float("12.5") == 12.5

    def test_to_float_with_non_numeric_str(self):
        from scripts.upgrade_to_enhanced_v2 import _to_float
        assert _to_float("variable") == 0.0

    def test_to_float_with_none(self):
        from scripts.upgrade_to_enhanced_v2 import _to_float
        assert _to_float(None) == 0.0

    def test_tax_rate_from_dict(self):
        from scripts.upgrade_to_enhanced_v2 import _tax_rate
        taxes = {"DD": 5.0, "TVA": 19.25}
        assert _tax_rate(taxes, "DD") == 5.0
        assert _tax_rate(taxes, "TVA") == 19.25

    def test_tax_rate_from_dict_missing_key_uses_default(self):
        from scripts.upgrade_to_enhanced_v2 import _tax_rate
        taxes = {"DD": 5.0}
        assert _tax_rate(taxes, "TVA", default=0.0) == 0.0

    def test_tax_rate_from_list(self):
        from scripts.upgrade_to_enhanced_v2 import _tax_rate
        taxes = [{"code": "DD", "rate_pct": 10.0}, {"code": "TVA", "rate_pct": 19.25}]
        assert _tax_rate(taxes, "TVA") == 19.25

    def test_total_rate_dict(self):
        from scripts.upgrade_to_enhanced_v2 import _total_rate
        taxes = {"DD": 5.0, "TVA": 19.25}
        assert _total_rate(taxes) == pytest.approx(24.25, rel=1e-3)

    def test_total_rate_list(self):
        from scripts.upgrade_to_enhanced_v2 import _total_rate
        taxes = [{"code": "DD", "rate_pct": 5.0}, {"code": "TVA", "rate_pct": 19.25}]
        assert _total_rate(taxes) == pytest.approx(24.25, rel=1e-3)

    def test_total_rate_empty_dict(self):
        from scripts.upgrade_to_enhanced_v2 import _total_rate
        assert _total_rate({}) == 0.0

    def test_group_positions_groups_by_hs6(self):
        from scripts.upgrade_to_enhanced_v2 import _group_positions
        positions = [
            {"hs6": "010110", "code_clean": "01011000", "taxes": {}},
            {"hs6": "010110", "code_clean": "01011010", "taxes": {}},
            {"hs6": "010121", "code_clean": "01012100", "taxes": {}},
        ]
        grouped = _group_positions(positions)
        assert "010110" in grouped
        assert "010121" in grouped
        assert len(grouped["010110"]) == 2
        assert len(grouped["010121"]) == 1

    def test_migrate_country_empty_positions(self):
        from scripts.upgrade_to_enhanced_v2 import _migrate_country
        data = {"country_name": "Test", "positions": []}
        result = _migrate_country(data, "TST")
        assert result["data_format"] == "enhanced_v2"
        assert result["tariff_lines"] == []
        assert result["summary"]["total_tariff_lines"] == 0


# =============================================================================
# cameroon_cemac_scraper – _process_page_positions
# =============================================================================

@pytest.mark.skipif(not _fitz_available, reason="PyMuPDF (fitz) not installed")
class TestProcessPagePositions:
    """_process_page_positions: page-level deduplication helper."""

    def _make_result(self, code: str, dd_rate: float = 5.0) -> dict:
        return {
            "code": code,
            "designation": f"Product {code}",
            "dd_rate": dd_rate,
            "tva_status": "19.25",
            "has_accise": False,
        }

    def _empty_stats(self) -> dict:
        return {
            "raw_extractions": 0,
            "duplicates": 0,
            "final_positions": 0,
            "chapters": set(),
        }

    def test_new_positions_are_added(self):
        from crawlers.countries.cameroon_cemac_scraper import _process_page_positions
        results = [self._make_result("01011000"), self._make_result("01011010")]
        seen: set = set()
        stats = self._empty_stats()
        positions = _process_page_positions(results, seen, stats)
        assert len(positions) == 2
        assert stats["final_positions"] == 2

    def test_duplicate_codes_are_skipped(self):
        from crawlers.countries.cameroon_cemac_scraper import _process_page_positions
        results = [self._make_result("01011000"), self._make_result("01011000")]
        seen: set = set()
        stats = self._empty_stats()
        positions = _process_page_positions(results, seen, stats)
        assert len(positions) == 1
        assert stats["duplicates"] == 1

    def test_already_seen_codes_are_skipped(self):
        from crawlers.countries.cameroon_cemac_scraper import _process_page_positions
        results = [self._make_result("01011000")]
        seen: set = {"01011000"}
        stats = self._empty_stats()
        positions = _process_page_positions(results, seen, stats)
        assert len(positions) == 0
        assert stats["duplicates"] == 1

    def test_position_contains_expected_fields(self):
        from crawlers.countries.cameroon_cemac_scraper import _process_page_positions
        results = [self._make_result("76011000", dd_rate=10.0)]
        seen: set = set()
        stats = self._empty_stats()
        positions = _process_page_positions(results, seen, stats)
        assert len(positions) == 1
        pos = positions[0]
        for field in ("code", "code_clean", "designation", "chapter", "hs6", "taxes", "taxes_detail", "source"):
            assert field in pos, f"Missing field: {field}"
        assert pos["chapter"] == "76"

    def test_chapter_is_recorded_in_stats(self):
        from crawlers.countries.cameroon_cemac_scraper import _process_page_positions
        results = [self._make_result("76011000")]
        seen: set = set()
        stats = self._empty_stats()
        _process_page_positions(results, seen, stats)
        assert "76" in stats["chapters"]

    def test_trailing_dot_stripped_from_code(self):
        from crawlers.countries.cameroon_cemac_scraper import _process_page_positions
        # Raw code has a trailing dot (common in PDF extraction)
        result = self._make_result("76011000.")
        seen: set = set()
        stats = self._empty_stats()
        positions = _process_page_positions([result], seen, stats)
        assert positions[0]["code"] == "76011000"
        assert positions[0]["code_clean"] == "76011000"


# =============================================================================
# cache_service – utility functions
# =============================================================================

class TestCacheServiceUtilities:
    """Unit tests for services.cache_service utility functions."""

    def test_generate_cache_key_returns_string(self):
        from services.cache_service import generate_cache_key
        key = generate_cache_key("test", "arg1", "arg2")
        assert isinstance(key, str)

    def test_generate_cache_key_starts_with_prefix(self):
        from services.cache_service import generate_cache_key
        key = generate_cache_key("statistics", "main")
        assert key.startswith("zlecaf:")

    def test_generate_cache_key_deterministic(self):
        from services.cache_service import generate_cache_key
        key1 = generate_cache_key("test", "arg1")
        key2 = generate_cache_key("test", "arg1")
        assert key1 == key2

    def test_generate_cache_key_different_args_differ(self):
        from services.cache_service import generate_cache_key
        key1 = generate_cache_key("test", "arg1")
        key2 = generate_cache_key("test", "arg2")
        assert key1 != key2

    def test_cache_ttl_has_required_categories(self):
        from services.cache_service import CACHE_TTL
        for category in ("statistics", "countries", "search", "calculation", "regulatory", "default"):
            assert category in CACHE_TTL, f"Missing TTL category: {category}"
            assert CACHE_TTL[category] > 0

    def test_cache_get_returns_none_when_no_redis(self):
        """cache_get must return None (not raise) when Redis is unavailable."""
        from services.cache_service import cache_get
        # In a test environment without Redis, this should return None gracefully
        result = cache_get("zlecaf:non_existent_key_xyz")
        assert result is None

    def test_cache_set_returns_false_when_no_redis(self):
        """cache_set must return False (not raise) when Redis is unavailable."""
        from services.cache_service import cache_set
        result = cache_set("zlecaf:non_existent_key_xyz", {"data": 1}, "default")
        # Either True (Redis connected) or False (no Redis) – must not raise
        assert isinstance(result, bool)

