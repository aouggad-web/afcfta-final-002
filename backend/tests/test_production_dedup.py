"""
Tests de déduplication des indicateurs de production (FAOSTAT / UNIDO)
======================================================================
Garantit l'invariant « jamais de somme entre points de donnée distincts » :
  - doublons exacts d'ingestion → 1 record conservé ;
  - collisions de libellés FAOSTAT (items anciens/nouveaux, agrégats FR→EN)
    → UNE valeur conservée (max), jamais la somme ;
  - UNIDO → l'officiel prime sur l'estimation ;
  - le dataset réel livré doit être exempt de doublons sur les clés canoniques ;
  - le chargement défensif (production_data) expose son intégrité d'ingestion.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import production_data
from production_dedup import (
    CANONICAL_KEYS,
    count_duplicates,
    dedup_agri,
    dedup_dataset,
    dedup_unido,
    deduplicate,
)


def _agri(iso3="CIV", code="0242", label="Groundnuts", year=2023, value=1000.0, **kw):
    base = {
        "country_iso3": iso3,
        "commodity_code": code,
        "element_code": "5510",
        "year": year,
        "commodity_label": label,
        "value": value,
    }
    base.update(kw)
    return base


class TestExactDuplicates:
    def test_exact_duplicate_keeps_first_never_sums(self):
        records = [_agri(value=1000), _agri(value=1000)]
        kept, stats = dedup_agri(records)
        assert len(kept) == 1
        assert kept[0]["value"] == 1000  # pas 2000
        assert stats["duplicates_removed"] == 1

    def test_same_item_different_values_keeps_deterministic_best(self):
        records = [_agri(value=900), _agri(value=1100)]
        kept, _ = dedup_agri(records)
        assert len(kept) == 1
        assert kept[0]["value"] == 1100  # max, pas somme (2000)

    def test_conflicting_values_are_counted(self):
        _, stats = dedup_agri([_agri(value=900), _agri(value=1100)])
        assert stats["value_conflicts"] == 1


class TestLabelCollisions:
    def test_old_and_new_item_codes_never_sum(self):
        """Arachides : item 0242 (moderne) + 0240 (ancien) → même mesure publiée."""
        records = [
            _agri(code="0242", value=1000),
            _agri(code="0240", value=1200),
        ]
        kept, stats = dedup_agri(records)
        assert len(kept) == 1
        assert kept[0]["value"] == 1200  # max — PAS 2200

    def test_fr_en_aggregate_collision_keeps_aggregate(self):
        """« Agrumes » (agrégat) + « Oranges » (sous-ensemble) → Citrus fruits."""
        records = [
            _agri(code="0512", label="Citrus fruits", value=1_200_000),
            _agri(code="0490", label="Citrus fruits", value=900_000),
        ]
        kept, _ = dedup_agri(records)
        assert len(kept) == 1
        assert kept[0]["value"] == 1_200_000

    def test_different_labels_are_never_merged(self):
        records = [
            _agri(code="0242", label="Groundnuts", value=1000),
            _agri(code="0026", label="Olives", value=5000),
        ]
        kept, stats = dedup_agri(records)
        assert len(kept) == 2
        assert stats["duplicates_removed"] == 0

    def test_order_of_first_occurrence_preserved(self):
        records = [
            _agri(code="0026", label="Olives", value=100),
            _agri(code="0015", label="Wheat", value=200),
            _agri(code="0026", label="Olives", value=300),
        ]
        kept, _ = dedup_agri(records)
        assert [r["commodity_label"] for r in kept] == ["Olives", "Wheat"]
        assert kept[0]["value"] == 300  # max conservé, position d'origine


class TestUnidoDedup:
    def test_official_wins_over_estimation(self):
        records = [
            {
                "country_iso3": "TUN",
                "isic_code": "13",
                "sector_detail": "Textiles",
                "year": 2023,
                "value": 1_500_000_000,
                "is_estimation": True,
            },
            {
                "country_iso3": "TUN",
                "isic_code": "13",
                "sector_detail": "Textiles",
                "year": 2023,
                "value": 1_573_000_000,
                "is_estimation": False,
            },
        ]
        kept, stats = dedup_unido(records)
        assert len(kept) == 1
        assert kept[0]["is_estimation"] is False
        assert kept[0]["value"] == 1_573_000_000

    def test_different_isic_never_merged(self):
        records = [
            {
                "country_iso3": "TUN",
                "isic_code": "13",
                "sector_detail": "Textiles",
                "year": 2023,
                "value": 100,
                "is_estimation": False,
            },
            {
                "country_iso3": "TUN",
                "isic_code": "27",
                "sector_detail": "Équipements électriques",
                "year": 2023,
                "value": 200,
                "is_estimation": False,
            },
        ]
        kept, _ = dedup_unido(records)
        assert len(kept) == 2


class TestDatasetValidation:
    def test_real_dataset_has_no_duplicates(self):
        import json

        data_file = (
            Path(__file__).resolve().parent.parent.parent
            / "data" / "json" / "production_africaine.json"
        )
        if not data_file.exists():
            return  # environnement sans dataset
        data = json.load(open(data_file, encoding="utf-8"))
        assert count_duplicates(data["agri_faostat"], CANONICAL_KEYS["agri_faostat"]) == 0
        assert count_duplicates(data["manufacturing_unido"], CANONICAL_KEYS["manufacturing_unido"]) == 0
        assert count_duplicates(data["mining_usgs"], CANONICAL_KEYS["mining_usgs"]) == 0

    def test_dedup_dataset_cleans_all_sections(self):
        data = {
            "agri_faostat": [_agri(value=100), _agri(value=100)],
            "manufacturing_unido": [],
            "mining_usgs": [],
            "value_added_macro": [],
            "countries": ["CIV"],
        }
        cleaned, stats = dedup_dataset(data)
        assert len(cleaned["agri_faostat"]) == 1
        assert stats["agri_faostat"]["duplicates_removed"] == 1
        # fichier d'origine intact
        assert len(data["agri_faostat"]) == 2


class TestLoadTimeIntegrity:
    def test_load_exposes_ingestion_integrity(self):
        import production_data as pd

        data = pd.load_production_data()
        assert data is not None
        integrity = pd.get_ingestion_integrity()
        assert integrity, "les stats de dédup doivent être calculées au chargement"
        assert set(integrity) >= {"agri_faostat", "manufacturing_unido"}
        for section, s in integrity.items():
            assert s["output"] == s["input"] - s["duplicates_removed"]

    def test_statistics_endpoint_exposes_integrity(self):
        import production_data as pd

        stats = pd.get_production_statistics()
        assert stats["ingestion_integrity"]["dedup_applied"] is True
        assert "keep_best" in stats["ingestion_integrity"]["strategy"]
        for dimension in stats["dimensions"].values():
            assert "duplicates_removed_at_load" in dimension


class TestGenericDedup:
    def test_prefer_official_flag(self):
        records = [
            {"iso": "DZA", "year": 2023, "value": 10, "is_estimation": False},
            {"iso": "DZA", "year": 2023, "value": 99, "is_estimation": True},
        ]
        kept, _ = deduplicate(records, ("iso", "year"), prefer_official=True)
        assert kept[0]["value"] == 10

    def test_no_value_max_when_non_numeric(self):
        records = [
            {"iso": "DZA", "year": 2023, "value": None},
            {"iso": "DZA", "year": 2023, "value": 5},
        ]
        kept, stats = deduplicate(records, ("iso", "year"))
        assert len(kept) == 1
        assert kept[0]["value"] == 5
        assert stats["duplicates_removed"] == 1
