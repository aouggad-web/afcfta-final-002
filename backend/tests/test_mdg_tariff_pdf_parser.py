from pathlib import Path

from scripts.parse_mdg_tariff_pdf import build_output, parse_lines

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
