"""
Corpus figé du calculateur — phase 0.2 du plan de correction.

L'audit du 13 septembre 2026 a démontré dix défauts sur des positions
précises. Sans corpus versionné, « les deux chemins donnent le même montant »
reste une affirmation : ces tests l'attachent à des valeurs sources citées, avec
le chemin exact où les relire.

Deux familles, aux rôles distincts.

1. `TestCitationsDuCorpus` — **doit passer aujourd'hui.** Chaque valeur attendue
   est relue dans le fichier du dépôt qu'elle cite. Si une recollecte change un
   taux, ce test tombe et le corpus est corrigé délibérément, au lieu de
   continuer à comparer le moteur à une attente périmée.

2. `TestDroitServiParLeCheminPrioritaire` — **échecs attendus, déclarés.** Le
   moteur doit rendre le droit de la source. Les six cas où il ne le fait pas
   sont marqués `xfail(strict=True)` : la correction les fera passer au vert, et
   le xfail strict imposera alors de retirer le marqueur. Rien n'est désactivé,
   rien n'est masqué.

Seul le chemin prioritaire est exercé ici : il lit `backend/data/` et
`backend/data/crawled/`, tous deux versionnés. Le chemin POST dépend de
`backend/data/crawled_normalized/` (~2 Go, non versionné) ; sa comparaison
relève du harnais `scripts/diff_engines.py`, qui sait signaler l'absence de
cette couche au lieu de la confondre avec un défaut.
"""

import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURE = Path(__file__).parent / "fixtures" / "calculator_golden.json"

CORPUS = json.loads(FIXTURE.read_text(encoding="utf-8"))
CASES = CORPUS["cases"]
CIF = CORPUS["observation_conditions"]["cif_value"]
ORIGIN = CORPUS["observation_conditions"]["origin_country"]

CASE_IDS = [case["id"] for case in CASES]


@pytest.fixture(autouse=True)
def _neutralise_devise(monkeypatch):
    """Garder les montants dans la devise de la source, comme à l'observation."""
    import currencies.service as currency_service

    monkeypatch.setattr(currency_service, "get_by_country", lambda code: None)


# --------------------------------------------------------------------------- #
# Résolution des localisateurs
# --------------------------------------------------------------------------- #


def _crawled_entry(country: str, code: str):
    from services.authentic_tariff_service import load_crawled_position_index

    return (load_crawled_position_index(country) or {}).get(code)


def _tax_entry(entry: dict, taxes_key: str, tax_code: str):
    """
    Retrouver une taxe, que la source la porte en dictionnaire ou en liste.

    Les schémas diffèrent d'un pays à l'autre : l'Égypte indexe ses taxes par
    code (`taxes.ID`), l'Afrique du Sud et la Tunisie les listent
    (`taxes[].code`, `taxes_import[].code`).
    """
    taxes = (entry or {}).get(taxes_key)
    if isinstance(taxes, dict):
        return taxes.get(tax_code)
    if isinstance(taxes, list):
        return next((tax for tax in taxes if tax.get("code") == tax_code), None)
    return None


def _canonical(country: str) -> dict:
    path = REPO_ROOT / "backend" / "data" / f"{country}_tariffs.json"
    if not path.is_file():
        return {}
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def _canonical_line(country: str, hs6: str):
    for line in _canonical(country).get("tariff_lines", []) or []:
        if str(line.get("hs6")) == hs6:
            return line
    return None


def resolve(country: str, locator: dict):
    """Lire dans le dépôt la valeur que le corpus prétend y trouver."""
    kind = locator["kind"]

    if kind == "crawled_tax":
        tax = _tax_entry(
            _crawled_entry(country, locator["code"]),
            locator.get("taxes_key", "taxes"),
            locator["tax_code"],
        )
        assert tax is not None, f"{country}/{locator['code']} : taxe {locator['tax_code']} absente"
        return tax.get(locator["field"])

    if kind == "crawled_tax_absent":
        entry = _crawled_entry(country, locator["code"])
        assert entry is not None, f"{country}/{locator['code']} : position absente du crawl"
        return _tax_entry(entry, locator.get("taxes_key", "taxes"), locator["tax_code"])

    if kind == "crawled_field":
        entry = _crawled_entry(country, locator["code"])
        assert entry is not None, f"{country}/{locator['code']} : position absente du crawl"
        return entry.get(locator["field"])

    if kind == "crawled_absent_code":
        return _crawled_entry(country, locator["code"])

    if kind == "canonical_sub":
        line = _canonical_line(country, locator["hs6"])
        assert line is not None, f"{country} : SH6 {locator['hs6']} absent du canonique"
        sub = next(
            (
                item
                for item in line.get("sub_positions", []) or []
                if str(item.get("code")) == locator["code"]
            ),
            None,
        )
        assert sub is not None, f"{country}/{locator['code']} : sous-position absente"
        return sub.get(locator["field"])

    if kind == "canonical_hs6":
        line = _canonical_line(country, locator["hs6"])
        assert line is not None, f"{country} : SH6 {locator['hs6']} absent du canonique"
        return line.get(locator["field"])

    if kind == "canonical_absent_hs6":
        return _canonical_line(country, locator["hs6"])

    raise AssertionError(f"localisateur inconnu : {kind}")


# --------------------------------------------------------------------------- #
# 1. Les citations du corpus sont exactes
# --------------------------------------------------------------------------- #


class TestCitationsDuCorpus:
    """Le corpus cite le dépôt fidèlement — sinon les attentes sont périmées."""

    @pytest.mark.parametrize("case", CASES, ids=CASE_IDS)
    def test_source_de_verite_relue_dans_le_depot(self, case):
        truth = case["source_of_truth"]
        found = resolve(case["country"], truth["locator"])

        if "expected_specific_duty" in truth:
            assert found == truth["expected_specific_duty"]
        elif truth["locator"]["kind"] in ("crawled_tax_absent", "crawled_absent_code"):
            # Le corpus affirme une absence : elle doit être vraie dans le dépôt.
            assert found is None, f"{case['id']} : la source porte {found!r}, absence attendue"
        else:
            assert found == pytest.approx(truth["expected_dd_rate_pct"])

    @pytest.mark.parametrize(
        "case",
        [case for case in CASES if "conflicting_source" in case],
        ids=[case["id"] for case in CASES if "conflicting_source" in case],
    )
    def test_source_concurrente_relue_dans_le_depot(self, case):
        conflicting = case["conflicting_source"]
        found = resolve(case["country"], conflicting["locator"])

        if conflicting["value"] is None:
            assert found is None, f"{case['id']} : {found!r} trouvé, absence attendue"
        else:
            assert found == pytest.approx(conflicting["value"])

    def test_chaque_cas_est_rattache_a_un_travail_du_plan(self):
        for case in CASES:
            assert case.get("plan_item"), f"{case['id']} : aucun travail du plan rattaché"
            assert case.get("defect"), f"{case['id']} : défaut non décrit"


# --------------------------------------------------------------------------- #
# 2. Le droit servi est celui de la source
# --------------------------------------------------------------------------- #


def _priority_dd(country: str, code: str):
    """Droit rendu par le chemin prioritaire, ou l'échec rencontré."""
    from services import authentic_tariff_service as svc

    try:
        result = svc.calculate_import_taxes(
            country, code, CIF, language="fr", origin_country=ORIGIN
        )
    except Exception as exc:
        return {"outcome": "exception", "detail": f"{type(exc).__name__}: {exc}"}

    if result.get("error"):
        return {"outcome": "absent", "detail": str(result["error"])}

    return {
        "outcome": "ok",
        "dd_rate_pct": (result.get("rates") or {}).get("dd_rate_pct"),
        "droit_douane": ((result.get("taxes_summary") or {}).get("npf") or {}).get("droit_douane"),
    }


def _expected_marker(case):
    """Marquer xfail strict les cas dont le défaut porte sur le droit servi."""
    if case["priority_dd_matches_source"]:
        return ()
    return (
        pytest.mark.xfail(
            strict=True,
            reason=f"{case['id']} — défaut ouvert ({case['plan_item']}) : {case['defect'][:120]}",
        ),
    )


class TestDroitServiParLeCheminPrioritaire:
    """Le taux rendu doit être celui de la source citée, ou déclaré indisponible."""

    @pytest.mark.parametrize(
        "case",
        [pytest.param(case, marks=_expected_marker(case), id=case["id"]) for case in CASES],
    )
    def test_droit_conforme_a_la_source(self, case):
        expected = case["source_of_truth"]["expected_dd_rate_pct"]
        observed = _priority_dd(case["country"], case["hs_code"])

        assert observed["outcome"] == "ok", (
            f"{case['id']} : le chemin prioritaire ne sert pas la position "
            f"({observed['outcome']}: {observed.get('detail')})"
        )

        if expected is None:
            # Droit absent de la source : ni zéro fabriqué, ni exception.
            assert observed["dd_rate_pct"] is None, (
                f"{case['id']} : droit absent de la source, "
                f"{observed['dd_rate_pct']!r} servi — un zéro de repli n'est pas une exonération"
            )
        else:
            assert observed["dd_rate_pct"] == pytest.approx(expected)
            assert observed["droit_douane"] == pytest.approx(CIF * expected / 100.0)


# --------------------------------------------------------------------------- #
# 3. Le harnais classe correctement
# --------------------------------------------------------------------------- #


class TestClassementDuHarnais:
    """Le verdict du harnais différentiel ne doit pas confondre absence et zéro."""

    @staticmethod
    def _harness():
        import importlib.util

        spec = importlib.util.spec_from_file_location(
            "diff_engines", REPO_ROOT / "scripts" / "diff_engines.py"
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_zero_et_absence_ne_sont_pas_confondus(self):
        harness = self._harness()
        assert harness._close(0.0, 0.0, 0.01) is True
        assert harness._close(None, None, 0.01) is True
        assert harness._close(None, 0.0, 0.01) is False
        assert harness._close(0.0, None, 0.01) is False

    def test_couche_normalisee_absente_nest_pas_une_divergence(self):
        harness = self._harness()
        priority = {
            "status": "ok",
            "dd_rate_pct": 10.0,
            "summary": {},
            "qualification": "authentique",
        }
        post = {"status": "absent", "error": "aucune ventilation NPF dans la réponse"}

        verdict, _ = harness.classify(priority, post, normalized_present=False)
        assert verdict == harness.V_NORMALISE_ABSENT
        assert verdict not in harness.DIVERGENCE_VERDICTS

        verdict, _ = harness.classify(priority, post, normalized_present=True)
        assert verdict == harness.V_ABSENT_POST
        assert verdict in harness.DIVERGENCE_VERDICTS

    def test_qualification_divergente_est_relevee_a_montants_egaux(self):
        harness = self._harness()
        summary = {
            "droit_douane": 0.0,
            "autres_taxes": 0.0,
            "tva": 150.0,
            "total_taxes_et_droits": 150.0,
        }
        priority = {
            "status": "ok",
            "dd_rate_pct": 0.0,
            "summary": summary,
            "qualification": "authentique",
        }
        post = {
            "status": "ok",
            "dd_rate_pct": 0.0,
            "summary": summary,
            "qualification": "indicatif",
        }

        verdict, fields = harness.classify(priority, post, normalized_present=True)
        assert verdict == harness.V_ECART_QUALIFICATION
        assert fields == ["qualification"]
