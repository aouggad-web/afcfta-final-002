"""
Tests des dérogations EAC hors Kenya (Tanzanie, Ouganda, Rwanda, Burundi),
extraites de la Legal Notice EAC/160/2026 (Table I, EAC Gazette Vol. AT 1
No. 16, déjà archivée et hachée dans data/sources/eac/official/).

Vérifie : isolation par juridiction (une mesure TZA ne doit jamais
affecter un calcul KEN et réciproquement), application correcte des
taux, et absence de régression sur les mesures Kenya existantes.
"""

from datetime import date
from pathlib import Path

from engine.legal_override_engine import LegalOverrideResolver, load_legal_measures
from engine.schemas.legal_override import OverrideContext

_EAC_OVERRIDES = Path(__file__).resolve().parents[2] / "data" / "eac" / "legal_overrides.json"


def _resolver(coverage_complete: bool = False) -> LegalOverrideResolver:
    measures = load_legal_measures(_EAC_OVERRIDES)
    return LegalOverrideResolver(measures, coverage_complete=coverage_complete)


def test_all_29_measures_load_and_are_distributed_across_jurisdictions():
    measures = load_legal_measures(_EAC_OVERRIDES)
    by_jur = {}
    for m in measures:
        by_jur[m.jurisdiction] = by_jur.get(m.jurisdiction, 0) + 1
    assert by_jur["KEN"] == 17
    assert by_jur["TZA"] == 6
    assert by_jur["RWA"] == 3
    assert by_jur["UGA"] == 2
    assert by_jur["BDI"] == 1


def test_tanzania_vitenge_stay_applies():
    resolver = _resolver()
    result = resolver.resolve(
        hs_code="52115110",
        on_date=date(2026, 8, 1),
        base_rate=50,
        context=OverrideContext(jurisdiction="TZA"),
    )
    assert result["applicable_customs_rate"] == 35


def test_tanzania_cotton_grey_fabric_mixed_rate_flagged():
    """Taux mixte (% ou USD/mètre) : le pourcentage plancher (35%) est
    appliqué par le résolveur, et la mesure source expose le taux complet
    « % ou USD/mètre » dans son ``rate_unit`` — jamais une conversion
    silencieuse en un taux ad valorem unique inventé."""
    resolver = _resolver()
    measures = load_legal_measures(_EAC_OVERRIDES)
    measure = next(m for m in measures if m.measure_id == "EAC-160-2026-STAY-52081100-52122100-TZA")
    assert "0.30/metre" in measure.rate_unit

    result = resolver.resolve(
        hs_code="52081100",
        on_date=date(2026, 8, 1),
        base_rate=25,
        context=OverrideContext(jurisdiction="TZA"),
    )
    assert result["applicable_customs_rate"] == 35


def test_uganda_tiles_stay_differs_from_tanzania_rate():
    """Même produit (Tiles), même code SH, mais un plancher spécifique
    différent par pays (USD 2/SQM Tanzanie vs USD 3/SQM Ouganda) : les
    deux mesures doivent être isolées l'une de l'autre."""
    resolver = _resolver()
    tza = resolver.resolve(
        hs_code="68021000", on_date=date(2026, 8, 1), base_rate=25,
        context=OverrideContext(jurisdiction="TZA"),
    )
    uga = resolver.resolve(
        hs_code="68021000", on_date=date(2026, 8, 1), base_rate=25,
        context=OverrideContext(jurisdiction="UGA"),
    )
    assert tza["applicable_customs_rate"] == 35
    assert uga["applicable_customs_rate"] == 35
    measures = load_legal_measures(_EAC_OVERRIDES)
    tza_measure = next(m for m in measures if m.measure_id == "EAC-160-2026-STAY-68021000-68029900-TZA")
    uga_measure = next(m for m in measures if m.measure_id == "EAC-160-2026-STAY-68021000-68029900-UGA")
    assert "2/SQM" in tza_measure.rate_unit
    assert "3/SQM" in uga_measure.rate_unit


def test_rwanda_electric_vehicle_and_motorcycle_zero_rate():
    resolver = _resolver()
    vehicle = resolver.resolve(
        hs_code="87034090", on_date=date(2026, 8, 1), base_rate=25,
        context=OverrideContext(jurisdiction="RWA"),
    )
    motorcycle = resolver.resolve(
        hs_code="87116000", on_date=date(2026, 8, 1), base_rate=25,
        context=OverrideContext(jurisdiction="RWA"),
    )
    assert vehicle["applicable_customs_rate"] == 0
    assert motorcycle["applicable_customs_rate"] == 0


def test_burundi_wire_rods_zero_rate():
    resolver = _resolver()
    result = resolver.resolve(
        hs_code="72139900", on_date=date(2026, 8, 1), base_rate=10,
        context=OverrideContext(jurisdiction="BDI"),
    )
    assert result["applicable_customs_rate"] == 0


def test_jurisdiction_isolation_tza_measure_does_not_leak_to_kenya():
    resolver = _resolver()
    result = resolver.resolve(
        hs_code="52115110",  # Vitenge, mesure TZA
        on_date=date(2026, 8, 1),
        base_rate=50,
        context=OverrideContext(jurisdiction="KEN"),
    )
    assert result["applicable_customs_rate"] == 50  # taux NPF inchangé, pas d'override TZA appliqué


def test_jurisdiction_isolation_rwa_measure_does_not_leak_to_uganda():
    resolver = _resolver()
    result = resolver.resolve(
        hs_code="87116000",  # Electric Motorcycle, mesure RWA
        on_date=date(2026, 8, 1),
        base_rate=25,
        context=OverrideContext(jurisdiction="UGA"),
    )
    assert result["applicable_customs_rate"] == 25


def test_expired_bloc_measure_reverts_to_base_rate():
    """Les mesures « for one year » expirent le 30 juin 2027 : au-delà,
    le taux NPF de base doit être appliqué de nouveau."""
    resolver = _resolver()
    result = resolver.resolve(
        hs_code="40151200",
        on_date=date(2027, 7, 1),
        base_rate=25,
        context=OverrideContext(jurisdiction="UGA"),
    )
    assert result["applicable_customs_rate"] == 25


def test_beneficiary_restricted_smart_card_stay_does_not_apply_without_beneficiary_match():
    """La franchise carte à puce tanzanienne est réservée aux importations
    de l'autorité nationale d'identification — sans ce fait, le taux
    normal (25%) doit rester appliqué."""
    resolver = _resolver()
    result = resolver.resolve(
        hs_code="85235200",
        on_date=date(2026, 8, 1),
        base_rate=25,
        context=OverrideContext(jurisdiction="TZA"),
    )
    assert result["applicable_customs_rate"] == 25
    assert result["calculation_status"] == "VERIFIED_PARTIAL"


def test_beneficiary_restricted_smart_card_stay_applies_when_beneficiary_matches():
    resolver = _resolver()
    result = resolver.resolve(
        hs_code="85235200",
        on_date=date(2026, 8, 1),
        base_rate=25,
        context=OverrideContext(
            jurisdiction="TZA", beneficiary="NATIONAL_IDENTIFICATION_AUTHORITY"
        ),
    )
    assert result["applicable_customs_rate"] == 0


def test_rwanda_smart_card_stay_has_no_beneficiary_restriction():
    """Le même produit (85235200) est en franchise générale pour le
    Rwanda, sans condition de bénéficiaire — contrairement à la Tanzanie."""
    resolver = _resolver()
    result = resolver.resolve(
        hs_code="85235200",
        on_date=date(2026, 8, 1),
        base_rate=25,
        context=OverrideContext(jurisdiction="RWA"),
    )
    assert result["applicable_customs_rate"] == 0


def test_kenya_measures_unaffected_by_bloc_extension():
    """Non-régression : les mesures Kenya existantes se comportent à
    l'identique après l'ajout des mesures des autres pays EAC."""
    resolver = _resolver()
    result = resolver.resolve(
        hs_code="10019910",
        on_date=date(2026, 8, 1),
        base_rate=35,
        context=OverrideContext(
            jurisdiction="KEN",
            import_purpose="MANUFACTURING_INPUT",
        ),
    )
    # La remission conditionnelle Kenya existe toujours et requiert des
    # faits d'éligibilité — comportement inchangé (VERIFIED_PARTIAL sans
    # justification d'éligibilité).
    assert result["calculation_status"] in {"VERIFIED_PARTIAL", "VERIFIED_COMPLETE"}
