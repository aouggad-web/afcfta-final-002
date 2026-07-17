import importlib.util
import sys
from pathlib import Path

# Chargement par chemin explicite : `backend/scripts` est un namespace package
# masqué par le package régulier `engine/scripts` (avec __init__.py) dès qu'un
# test antérieur ajoute engine/ au sys.path — `from scripts...` casserait alors
# toute la collection de la suite.
_MODULE_PATH = Path(__file__).parent.parent / "scripts" / "parse_mdg_tariff_pdf.py"
_spec = importlib.util.spec_from_file_location("parse_mdg_tariff_pdf", _MODULE_PATH)
_mod = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = _mod  # requis par @dataclass (résolution des annotations)
_spec.loader.exec_module(_mod)
build_output, parse_lines = _mod.build_output, _mod.parse_lines

FIXTURE = Path(__file__).parent / "fixtures" / "mdg_tariff_text_sample.txt"


def test_parse_mdg_tariff_text_sample_extracts_positions():
    positions = parse_lines(FIXTURE.read_text(encoding="utf-8").splitlines())

    assert len(positions) == 5
    assert positions[0].code == "0101.21.00"
    assert positions[0].code_clean == "01012100"
    assert positions[0].unit == "u"
    assert positions[0].chapter == "01"
    assert positions[-1].hs6 == "020110"


def test_build_output_preserves_official_pdf_provenance():
    positions = parse_lines(FIXTURE.read_text(encoding="utf-8").splitlines())
    payload = build_output(positions, source_file="engine/audits/official_sources/MDG/sample.txt")

    assert payload["country_code"] == "MDG"
    assert payload["method"] == "official_pdf_parser"
    assert payload["data_status"] == "PARTIAL"
    assert payload["total_positions"] == 5
    assert payload["positions"][1]["code_clean"] == "01012900"
