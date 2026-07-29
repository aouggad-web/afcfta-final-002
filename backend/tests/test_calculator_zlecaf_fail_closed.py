"""
Vérifie que l'endpoint /calculate-tariff (routes/calculator.py) applique le
principe « fail-closed » : une donnée NPF authentique ne constitue jamais, à
elle seule, une preuve de préférence ZLECAf.

Correctif regroupant, de façon cohérente (structurellement dépendants) :
  1. Le garde-fou central multipays (services.authentic_tariff_service.
     resolve_zlecaf_context — déjà présent et testé sur `main`, commit
     cbc5610d, indépendamment de ce correctif).
  2. La suppression des 3 sites de fabrication `get_zlecaf_reduction_factor`
     (formule générique PMA/catégorie/année, sans source) dans calculator.py.
  3. La neutralisation transactionnelle WITS/UNCTAD-TRAINS (duty_status=
     INDICATIVE_MFN, aucune préférence ZLECAf calculée sur cette base).

Réseau neutralisé (OEC/World Bank monkeypatchés) : suite hermétique.
"""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient


@pytest.fixture()
def client(monkeypatch):
    from routes import calculator as calc
    from services.crawled_data_service import crawled_service

    # crawled_service.load() n'est appelé qu'au démarrage de server.py (event
    # de startup) — jamais déclenché par une app FastAPI minimale construite
    # directement sur le routeur. Sans cet appel, PRIORITY 1 (crawled_service.
    # is_loaded()) est silencieusement ignorée et tous les cas retombent sur
    # PRIORITY 3 (repli générique par chapitre) : le test croirait alors
    # exercer le garde-fou central alors qu'il ne teste que le repli ETL.
    crawled_service.load()

    async def _no_producers(*a, **k):
        return []

    async def _no_wb(*a, **k):
        return {}

    monkeypatch.setattr(calc.oec_client, "get_top_producers", _no_producers)
    monkeypatch.setattr(calc.wb_client, "get_country_data", _no_wb)

    app = FastAPI()
    app.include_router(calc.router, prefix="/api")
    return TestClient(app, raise_server_exceptions=True)


def _calc(client, origin, dest, hs_code="010121", value=10000.0):
    resp = client.post(
        "/api/calculate-tariff",
        json={
            "origin_country": origin,
            "destination_country": dest,
            "hs_code": hs_code,
            "value": value,
        },
    )
    assert resp.status_code == 200, resp.text
    return resp.json()


# ==================== Champs de statut ====================


def test_response_exposes_honesty_status_fields(client):
    """Les champs de statut additifs sont toujours présents (contrat élargi)."""
    data = _calc(client, "EGY", "KEN")
    for field in (
        "duty_status",
        "dd_available",
        "trade_regime",
        "zlecaf_preference_applied",
        "zlecaf_status",
    ):
        assert field in data, f"champ de statut manquant : {field}"
    assert data["duty_status"] in ("PAYABLE", "INDICATIVE_MFN", "UNAVAILABLE")
    assert data["zlecaf_status"] in ("DOCUMENTED", "NOT_AVAILABLE")
    assert data["country_enrichment"]["country_iso3"] == "KEN"


def test_south_sudan_does_not_expose_legacy_estimated_vat(client):
    data = _calc(client, "KEN", "SSD")
    assert data["normal_vat_rate"] is None
    assert data["normal_vat_amount"] is None
    assert data["zlecaf_vat_rate"] is None
    assert data["zlecaf_vat_amount"] is None
    assert not any(item.get("code") in {"TVA", "VAT"} for item in (data.get("taxes_detail") or []))
    consumption_tax = data["country_enrichment"]["consumption_tax"]
    assert consumption_tax["tax_type"] == "IMPORT_SALES_TAX"
    assert consumption_tax["status"] == "NOT_AVAILABLE"
    assert consumption_tax["standard_rate"] is None
    assert data["country_enrichment"]["required_documents_status"] == "DOCUMENTED"


# ==================== 1. Une donnée NPF seule ne génère jamais de préférence ====================


def test_no_generic_zlecaf_zero_for_ratified_without_schedule(client):
    """Deux pays ratifiés mais sans barème préférentiel par ligne vérifié :
    le taux ZLECAf ne doit PAS être fabriqué (fallback interdit) — la réponse
    indique l'absence de préférence via zlecaf_tariff_rate=None. savings=None
    (et non 0) : aucun calcul préférentiel n'a été effectué, un 0 affirmerait
    à tort qu'un calcul a eu lieu et n'a rien trouvé à réduire."""
    data = _calc(client, "EGY", "KEN")
    assert data["zlecaf_tariff_rate"] is None
    assert data["zlecaf_tariff_amount"] is None
    assert data["zlecaf_status"] == "NOT_AVAILABLE"
    assert data["zlecaf_preference_applied"] is False
    assert data["savings"] is None


def test_non_ratified_origin_gets_no_preference(client):
    """Origine non signataire (Érythrée) : aucune préférence ZLECAf —
    zlecaf_tariff_rate=None pour indiquer l'absence de préférence, savings=None
    (aucun calcul préférentiel effectué, distinct d'une économie nulle)."""
    data = _calc(client, "ERI", "KEN")
    assert data["zlecaf_preference_applied"] is False
    assert data["zlecaf_tariff_rate"] is None
    assert data["zlecaf_status"] == "NOT_AVAILABLE"
    assert data["savings"] is None


# ==================== 2. WITS/TRAINS reste INDICATIVE_MFN ====================


def test_wits_country_stays_indicative_mfn_no_preference(client):
    """MOZ est sourcé WITS/UNCTAD-TRAINS (source_quality=
    crawled_authentic_partial_national) : duty_status doit être
    INDICATIVE_MFN et zlecaf_tariff_rate=None (aucune préférence ZLECAf)."""
    data = _calc(client, "EGY", "MOZ")
    assert data["duty_status"] == "INDICATIVE_MFN"
    assert data["zlecaf_preference_applied"] is False
    assert data["zlecaf_tariff_rate"] is None
    assert data["zlecaf_status"] == "NOT_AVAILABLE"
    assert data["savings"] is None
    assert "WITS" in data["zlecaf_note"] or "TRAINS" in data["zlecaf_note"]


def test_wits_tariff_precision_marked_unverified_not_national_position(client):
    """L'agrégat WITS ne doit jamais être présenté comme une position
    tarifaire nationale vérifiée (tariff_precision, seul champ de précision
    réellement exposé par l'API — rate_source est une variable interne non
    exposée dans le contrat de réponse)."""
    data = _calc(client, "EGY", "MOZ")
    assert data["tariff_precision"] == "sh6_mfn_average_unverified"
    assert data["tariff_precision"] != "national_position"


# ==================== 3. Aucune chaîne "ZLECAf (catégorie)" fabriquée ====================


def test_no_generic_category_based_zlecaf_string_anywhere(client):
    """La formule générique PMA/catégorie (get_zlecaf_reduction_factor) est
    supprimée : sa signature textuelle ne doit plus jamais apparaître."""
    pairs = [
        ("EGY", "KEN"),
        ("ERI", "KEN"),
        ("EGY", "MOZ"),
        ("BWA", "ZAF"),
        ("EGY", "DZA"),
    ]
    for origin, dest in pairs:
        data = _calc(client, origin, dest)
        note = str(data.get("zlecaf_note", "")) + str(data.get("trade_regime", ""))
        assert "ZLECAf (" not in note, f"formule générique détectée pour {origin}->{dest}"


# ==================== 4. Taux absent reste signalé, jamais un 0 % silencieux ====================


def test_duty_status_unavailable_when_no_dd_in_source(client):
    """Quand aucun droit de douane n'est trouvé dans une source crawled,
    dd_available doit être False et duty_status UNAVAILABLE — jamais un 0 %
    présenté comme vérifié sans indication."""
    # Recherche d'un cas réel : on ne force pas artificiellement un pays sans
    # DD ; ce test vérifie la cohérence du contrat plutôt qu'un cas particulier
    # non garanti stable dans le temps.
    data = _calc(client, "EGY", "KEN")
    if data["dd_available"] is False:
        assert data["duty_status"] == "UNAVAILABLE"
        assert data["duty_notice"] is not None
    else:
        assert data["duty_status"] != "UNAVAILABLE"


# ==================== 5. Le calcul NPF continue de fonctionner ====================


def test_npf_calculation_still_produces_a_rate(client):
    """Le régime NPF doit toujours produire un taux et un montant, quel que
    soit le statut de la préférence ZLECAf."""
    data = _calc(client, "EGY", "KEN")
    assert isinstance(data["normal_tariff_rate"], (int, float))
    assert data["normal_tariff_rate"] >= 0
    assert isinstance(data["normal_tariff_amount"], (int, float))


# ==================== 6. Les taxes traçables restent inchangées ====================


def test_traceable_vat_and_taxes_unaffected_by_guard(client):
    """La TVA et les autres taxes tracées ne doivent pas être altérées par le
    garde-fou ZLECAf : seule la composante ZLECAf est concernée."""
    data = _calc(client, "EGY", "KEN")
    assert isinstance(data["normal_vat_rate"], (int, float))
    assert data["normal_vat_rate"] >= 0
    assert data.get("taxes_detail") is not None or data["normal_vat_rate"] >= 0


# ==================== 7. Une préférence documentée continue de fonctionner ====================


def test_customs_union_eligibility_with_zero_npf_line(client):
    """Éligibilité juridique : paire intra-union douanière (SACU) sur une
    ligne déjà à 0 % NPF (chevaux vivants). Régime et taux garantis par le
    garde-fou, mais 0 %→0 % n'est pas une réduction effective."""
    data = _calc(client, "BWA", "ZAF", hs_code="010121")
    assert data["trade_regime"] == "CUSTOMS_UNION"
    assert data["trade_regime_code"] == "SACU"
    assert data["zlecaf_tariff_rate"] == 0.0
    assert data["normal_tariff_rate"] == 0.0
    assert data["zlecaf_status"] == "DOCUMENTED"  # régime résolu, même sans réduction
    assert data["zlecaf_preference_applied"] is False  # rien à réduire
    assert data["savings"] == 0  # calcul effectué, économie nulle (≠ absence de calcul)


def test_customs_union_reduction_with_nonzero_npf_line(client):
    """Réduction économique effective : même union douanière (SACU), mais sur
    une ligne à droit NPF non nul (corbillards, 20 % — donnée statique
    sars.gov.za, stable quel que soit l'ordre d'exécution des tests)."""
    data = _calc(client, "BWA", "ZAF", hs_code="870323")
    assert data["trade_regime"] == "CUSTOMS_UNION"
    assert data["trade_regime_code"] == "SACU"
    assert data["normal_tariff_rate"] == pytest.approx(0.20)
    assert data["zlecaf_tariff_rate"] == 0.0
    assert data["zlecaf_status"] == "DOCUMENTED"
    assert data["zlecaf_preference_applied"] is True
    assert data["savings"] is not None and data["savings"] > 0


def test_dza_national_offer_still_applies_via_guard(client):
    """L'offre nationale algérienne (circulaire DGD 482/2024) reste appliquée,
    mais désormais via le garde-fou central — un partenaire actif (EGY) doit
    résoudre un régime cohérent."""
    data = _calc(client, "EGY", "DZA")
    assert data["trade_regime"] in ("ZLECAF", "CUSTOMS_UNION", "NPF", "FTA_CONDITIONAL")
    assert "zlecaf_note" in data


# ==================== 8. Pays non applicables restent en NPF ====================


def test_non_active_dza_partner_stays_npf_not_zlecaf(client):
    """Réciprocité DZA (circulaire 482/2024) non contournée : un pays ratifié
    ZLECAf mais non listé comme partenaire actif algérien ne doit recevoir
    aucune préférence. SEN est ratifié mais absent de ACTIVE_PARTNERS
    (zlecaf_schedule_dza.py) — vérifié directement contre le module, pas
    supposé, pour ne pas dépendre d'une liste qui peut évoluer."""
    from services.zlecaf_schedule_dza import ACTIVE_PARTNERS

    assert "SEN" not in ACTIVE_PARTNERS, (
        "précondition du test invalidée : SEN a été ajouté aux partenaires "
        "actifs DZA — choisir un autre pays ratifié hors de cette liste"
    )
    data = _calc(client, "SEN", "DZA")
    assert data["zlecaf_preference_applied"] is False
    assert data["zlecaf_tariff_rate"] is None
    assert data["zlecaf_status"] == "NOT_AVAILABLE"
    assert data["savings"] is None


def test_gha_synthetic_zero_rate_rejected(client):
    """Ghana : `backend/data/crawled/GHA_tariffs.json` portait, sur 100 % de
    ses 5 387 lignes, la paire synthétique `zlecaf_rate=0.0`/
    `zlecaf_source="ZLECAf"` — fabriquée, non sourcée. Nettoyée physiquement
    (branche `claude/ghana-crawled-zlecaf-cleanup`) : la paire ne doit plus
    exister sur le fichier, et le garde-fou de calculator.py (toujours en
    place, seconde ligne de défense) doit continuer à ne produire aucune
    préférence à partir de cette absence, même pour un pays par ailleurs
    ratifié."""
    from services.crawled_data_service import crawled_service

    raw = crawled_service.lookup("GHA", "010121")
    assert raw is not None
    assert raw.get("zlecaf_rate") is None, (
        "régression : GHA_tariffs.json porte de nouveau un zlecaf_rate " "fabriqué sur cette ligne"
    )
    assert not raw.get("zlecaf_source"), (
        "régression : GHA_tariffs.json porte de nouveau un zlecaf_source "
        "fabriqué sur cette ligne"
    )

    data = _calc(client, "EGY", "GHA")
    assert data["zlecaf_preference_applied"] is False
    assert data["zlecaf_tariff_rate"] is None
    assert data["zlecaf_status"] == "NOT_AVAILABLE"
    assert data["savings"] is None


def test_gha_crawled_file_physically_clean_of_any_zlecaf_key():
    """Balayage exhaustif des 5 387 lignes de
    `backend/data/crawled/GHA_tariffs.json` : zéro clé `zlecaf_rate`/
    `zlecaf_source`/`zlecaf_total_taxes` restante, quelle que soit la valeur
    (pas seulement la paire 0.0/"ZLECAf" connue) — et les champs
    NPF/fiscalité (dd_rate, dd_source, vat_rate, taxes_detail) restent
    présents et non vides."""
    import json

    from services.crawled_data_service import CRAWLED_DIR

    path = CRAWLED_DIR / "GHA_tariffs.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    lines = data["tariff_lines"]
    assert len(lines) == 5387, f"précondition invalidée : {len(lines)} lignes trouvées"

    lines_with_zlecaf_key = 0
    lines_missing_npf = 0
    for line in lines:
        if any(k in line for k in ("zlecaf_rate", "zlecaf_source", "zlecaf_total_taxes")):
            lines_with_zlecaf_key += 1
        if (
            line.get("dd_rate") is None
            or not line.get("dd_source")
            or line.get("vat_rate") is None
            or not line.get("taxes_detail")
        ):
            lines_missing_npf += 1

    assert lines_with_zlecaf_key == 0, (
        f"{lines_with_zlecaf_key} ligne(s) portent encore une clé zlecaf_* — " "nettoyage incomplet"
    )
    assert lines_missing_npf == 0, (
        f"{lines_missing_npf} ligne(s) ont perdu leurs champs NPF/fiscalité " "pendant le nettoyage"
    )


_FABRICATED_ZLECAF_MARKERS = {
    "ZLECAf",
    "ZLECAf (produit normal)",
    "ZLECAf (produit sensible)",
}


def test_tariffs_54_files_physically_clean_of_synthetic_zlecaf_markers(client):
    """Vérification EXHAUSTIVE post-assainissement (100 % des fichiers, 100 %
    des lignes, pas un sondage) : les 54 fichiers `backend/data/tariffs/*.json`
    — chemin PRIORITY 2, servi par `tariff_data_service.py`, distinct des 53
    fichiers actifs `backend/data/crawled/*.json` (PRIORITY 1, dont GHA fait
    partie ; les deux jeux de fichiers ne se recouvrent pas) — ne portent plus
    AUCUN des 3 marqueurs fabriqués historiquement présents sur 100 % de leurs
    ~293 000 lignes (`"ZLECAf"`, `"ZLECAf (produit normal)"`,
    `"ZLECAf (produit sensible)"` — cf. branche
    `claude/tariffs-zlecaf-synthetic-cleanup`) : ni `zlecaf_rate`, ni
    `zlecaf_source`, ni `zlecaf_total_taxes` ne doivent plus exister sur
    aucune ligne. Aucun champ non-ZLECAf n'a été touché par ce nettoyage
    (dd_rate, vat_rate, taxes_detail, sous-positions, etc. strictement
    préservés — vérifié séparément par hash structurel avant/après lors du
    nettoyage, hors périmètre de ce test qui porte sur l'état final)."""
    import json

    # Réutilise DATA_DIR de tariff_data_service (source unique de vérité pour
    # ce chemin) plutôt qu'un chemin absolu codé en dur — robuste à tout
    # emplacement de checkout (CI, autre poste).
    from services.tariff_data_service import DATA_DIR, tariff_service

    files = sorted(DATA_DIR.glob("*_tariffs.json"))
    assert len(files) == 54, f"précondition invalidée : {len(files)} fichiers trouvés, 54 attendus"

    tariff_service.load()

    total_lines_checked = 0
    lines_with_any_zlecaf_key = 0
    lines_with_known_marker = 0

    for path in files:
        country_code = path.name.replace("_tariffs.json", "")
        with open(path, "r", encoding="utf-8") as fh:
            raw = json.load(fh)
        for line in raw.get("tariff_lines", []):
            total_lines_checked += 1
            hs6 = line.get("hs6", "")
            if any(k in line for k in ("zlecaf_rate", "zlecaf_source", "zlecaf_total_taxes")):
                lines_with_any_zlecaf_key += 1
            if line.get("zlecaf_source") in _FABRICATED_ZLECAF_MARKERS:
                lines_with_known_marker += 1
            # Le chemin runtime (get_zlecaf_rate) ne doit jamais renvoyer un
            # taux pour une ligne qui n'a plus de zlecaf_rate en source.
            rate, source = tariff_service.get_zlecaf_rate(country_code, hs6)
            assert (
                rate is None
            ), f"{country_code}/{hs6} : taux inattendu après nettoyage (rate={rate})"
            assert source == ""

    assert (
        total_lines_checked > 250_000
    ), f"précondition invalidée : seulement {total_lines_checked} lignes lues sur 54 fichiers"
    assert lines_with_any_zlecaf_key == 0, (
        f"{lines_with_any_zlecaf_key} ligne(s) sur {total_lines_checked} portent encore "
        f"une clé zlecaf_rate/zlecaf_source/zlecaf_total_taxes — nettoyage incomplet"
    )
    assert lines_with_known_marker == 0


def test_tariff_data_service_still_rejects_marker_if_reintroduced(client):
    """Test anti-réintroduction : le garde-fou runtime de
    `tariff_data_service.get_zlecaf_rate` (ajouté sur
    `claude/zlecaf-fail-closed-guard`, PR #321) doit continuer de rejeter les
    3 marqueurs fabriqués connus même après l'assainissement physique des
    données — deuxième ligne de défense si un futur script de régénération
    (ex. `upgrade_to_enhanced_v2.py`, déjà identifié comme fabricateur)
    réintroduisait accidentellement l'un de ces marqueurs sur une ligne."""
    from services.tariff_data_service import tariff_service

    tariff_service.load()
    for marker in _FABRICATED_ZLECAF_MARKERS:
        line = {"zlecaf_rate": 12.5, "zlecaf_source": marker}
        # Simule get_tariff_line() en injectant directement une ligne dans
        # l'index pour isoler la logique de rejet de get_zlecaf_rate, sans
        # dépendre d'une ligne réelle du dataset (qui n'en porte plus aucune).
        tariff_service._hs6_index.setdefault("_TEST_REINTRODUCTION", {})["999999"] = line
        rate, source = tariff_service.get_zlecaf_rate("_TEST_REINTRODUCTION", "999999")
        del tariff_service._hs6_index["_TEST_REINTRODUCTION"]
        assert (
            rate is None
        ), f"marqueur {marker!r} réintroduit accepté comme taux réel (rate={rate})"
        assert source == ""


# ==================== 9. Réciprocité / garde-fous existants non contournés ====================


def test_zaf_partner_not_active_stays_npf(client):
    """Un partenaire non activé pour l'Afrique du Sud (hors SACU/SADC) ne doit
    recevoir aucune préférence ZLECAf tant que l'échange bilatéral n'est pas
    confirmé (newsletter dtic/SARS). COM (Comores) vérifié directement absent
    de ACTIVE_PARTNERS_ZAF, pas supposé."""
    from services.zlecaf_schedule_zaf import ACTIVE_PARTNERS_ZAF

    assert "COM" not in ACTIVE_PARTNERS_ZAF, (
        "précondition du test invalidée : COM a été ajouté aux partenaires "
        "actifs ZAF — choisir un autre pays hors de cette liste"
    )
    data = _calc(client, "COM", "ZAF", hs_code="010121")
    assert data["trade_regime"] != "CUSTOMS_UNION"  # Comores hors SACU
    assert data["zlecaf_preference_applied"] is False
    assert data["zlecaf_tariff_rate"] is None
    assert data["zlecaf_status"] == "NOT_AVAILABLE"
    assert data["savings"] is None


# ==================== 10. authentic_tariff_service.calculate_import_taxes ====================
# Chemin runtime DISTINCT de routes/calculator.py : consommé par
# routes/authentic_tariffs.py et routes/postgres_tariffs.py (POST
# /postgres-tariffs/calculate). Lit backend/data/{ISO3}_tariffs.json (miroir
# plat, pas backend/data/tariffs/) via authentic_tariff_service.DATA_DIR.
# Après le nettoyage des marqueurs zlecaf_* fabriqués sur ce miroir, une
# ligne éligible ZLECAf (régime "ZLECAf", implémenteur actif) mais sans taux
# préférentiel tracé ne doit produire NI erreur NI un repli silencieux vers 0
# (`or 0`, corrigé) — les économies doivent rester `None`, jamais `0.0`.


def test_authentic_tariff_service_untraceable_zlecaf_line_has_null_savings():
    """Afrique du Sud, partenaire ZLECAf actif (hors SACU), ligne sans taux
    préférentiel tracé dans la source : la préférence est NON_AVAILABLE et
    les économies sont `None`, pas un 0 % fabriqué par un ancien repli
    `line.get("zlecaf_rate") or 0`."""
    from services.authentic_tariff_service import get_tariff_line
    from services.zlecaf_schedule_zaf import zaf_partner_active

    assert zaf_partner_active("MAR"), (
        "précondition invalidée : MAR n'est plus un partenaire ZLECAf actif "
        "pour l'Afrique du Sud — choisir un autre partenaire actif"
    )
    line = get_tariff_line("ZAF", "020110")
    assert line is not None and (line.get("dd_rate") or 0) > 0, (
        "précondition invalidée : besoin d'une ligne ZAF avec dd_rate > 0 et "
        "sans zlecaf_rate traçable (nettoyage des marqueurs fabriqués)"
    )
    assert "zlecaf_rate" not in line, (
        "précondition invalidée : cette ligne porte encore un zlecaf_rate "
        "(le nettoyage du miroir plat a-t-il régressé ?)"
    )

    from services.authentic_tariff_service import calculate_import_taxes

    result = calculate_import_taxes("ZAF", "020110", 1000, origin_country="MAR")

    assert result["trade_regime"] == "ZLECAF"
    assert result["zlecaf_eligible"] is True
    assert result["zlecaf_preference_applied"] is False
    assert result["zlecaf_status"] == "NOT_AVAILABLE"
    assert result["savings"]["amount"] is None
    assert result["savings"]["percentage"] is None
    # Le droit reste au taux NPF réel de la source — aucune exonération
    # fabriquée (pas de 0.0 silencieux).
    assert result["rates"]["dd_rate_pct"] == line["dd_rate"]


def test_authentic_tariff_service_customs_union_savings_stay_documented():
    """Contrôle négatif : un régime structurellement vérifié (union
    douanière SACU) ne doit pas être requalifié en NOT_AVAILABLE — il
    produit un taux et des économies concrets, traçables par construction."""
    from services.authentic_tariff_service import calculate_import_taxes

    result = calculate_import_taxes("ZAF", "020110", 1000, origin_country="BWA")

    assert result["trade_regime"] == "CUSTOMS_UNION"
    assert result["zlecaf_status"] == "DOCUMENTED"
    assert result["savings"]["amount"] is not None
    assert result["savings"]["amount"] > 0


def test_authentic_tariff_service_no_origin_is_documented_zero_not_null():
    """Contrôle négatif : sans pays d'origine, le régime NPF est une
    conclusion déterministe (pas une donnée manquante) — économies
    vérifiées à 0, jamais `None`."""
    from services.authentic_tariff_service import calculate_import_taxes

    result = calculate_import_taxes("ZAF", "020110", 1000, origin_country=None)

    assert result["trade_regime"] == "NPF"
    assert result["zlecaf_status"] == "DOCUMENTED"
    assert result["savings"]["amount"] == 0.0
