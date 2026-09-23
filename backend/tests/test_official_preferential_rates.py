import gzip
import json
from importlib import import_module

from services import authentic_tariff_service
from services.authentic_tariff_service import resolve_zlecaf_context
from services.official_preferential_rates import (
    DATASETS,
    _carte_origines_nationale,
    _load_dataset,
    _resolve_offer_line,
    resolve_official_preferential_rate,
    resolve_published_offer_rate,
)
from services.zlecaf_implementation_registry import (
    APPLIED,
    NOT_AVAILABLE,
    OFFER_DATASETS,
    OFFER_ONLY,
    PARTNER_NOTICE_REQUIRED,
    RECORDS,
    implementation_decision,
)

from scripts.extract_sars_afcfta_schedule import (
    SOURCE_SHA256,
    classify_rate_expression,
    write_dataset,
)

collector = import_module("scripts.collect_afcfta_etariff_book")


def test_dataset_records_the_reviewed_sars_revision():
    rate = resolve_official_preferential_rate("ZAF", "010121")
    assert rate["source_pdf_sha256"] == SOURCE_SHA256


def test_rate_expression_classification_never_flattens_compound_duties():
    assert classify_rate_expression("free")["ad_valorem_rate_pct"] == 0.0
    assert classify_rate_expression("8,8%")["ad_valorem_rate_pct"] == 8.8
    compound = classify_rate_expression("40% or 240c/kg")
    assert compound["rate_kind"] == "COMPOUND"
    assert compound["ad_valorem_rate_pct"] is None
    assert compound["calculation_status"] == "REQUIRES_QUANTITY"


def test_resolves_exact_free_and_ad_valorem_lines():
    free = resolve_official_preferential_rate("ZAF", "0101.21")
    assert free["hs_code"] == "010121"
    assert free["rate_expression"] == "free"
    assert free["ad_valorem_rate_pct"] == 0.0

    percent = resolve_official_preferential_rate("ZAF", "07108090")
    assert percent["rate_expression"] == "4%"
    assert percent["ad_valorem_rate_pct"] == 4.0


def test_compound_line_is_documented_but_not_value_only_calculable():
    rate = resolve_official_preferential_rate("ZAF", "020110")
    assert rate["rate_expression"] == "40% or 240c/kg"
    assert rate["calculation_status"] == "REQUIRES_QUANTITY"
    assert rate["ad_valorem_rate_pct"] is None


def test_resolution_fails_closed_for_ambiguous_or_unknown_codes():
    # 0201 has multiple national lines: never choose one from a short prefix.
    assert resolve_official_preferential_rate("ZAF", "0201") is None
    assert resolve_official_preferential_rate("ZAF", "999999") is None
    assert resolve_official_preferential_rate("KEN", "010121") is None


def test_zaf_context_uses_the_official_rate_after_legal_gates():
    context = resolve_zlecaf_context("ZAF", "DZA", "07108090", 10.0, None)
    assert context["trade_regime"] == "ZLECAF"
    assert context["dd_rate_pct"] == 4.0
    assert context["preference_applied"] is True
    assert context["zlecaf_rate_expression"] == "4%"
    assert context["zlecaf_rate_source"]["page"] == 47


def test_zaf_context_neutralizes_compound_duty_without_quantity():
    context = resolve_zlecaf_context("ZAF", "DZA", "020110", 40.0, None)
    assert context["trade_regime"] == "ZLECAF"
    assert context["dd_rate_pct"] is None
    assert context["preference_applied"] is False
    assert context["zlecaf_rate_expression"] == "40% or 240c/kg"
    assert context["zlecaf_rate_calculation_status"] == "REQUIRES_QUANTITY"


def test_kenya_applies_only_to_the_21_origins_named_by_kra():
    accepted = implementation_decision("KEN", "GHA")
    assert accepted["applied"] is True
    assert accepted["status"] == APPLIED
    assert accepted["record"].instrument_id == "EAC/321/2022"

    # Algeria is in the e-Tariff Book query but not in KRA's accepted list.
    refused = implementation_decision("KEN", "DZA")
    assert refused["applied"] is False
    assert refused["status"] == "NOT_AVAILABLE"


def test_kenya_uses_the_exact_eac_line_and_2026_tier():
    # Lu dans le Journal officiel (Legal Notice EAC/321/2022), colonne 2026 —
    # plus dans l'e-Tariff Book du Secrétariat, qui en diverge.
    rate = resolve_official_preferential_rate("KEN", "01012900", "GHA", as_of_year=2026)
    assert rate["hs_code"] == "01012900"
    assert rate["schedule"] == "EAC/321/2022"
    assert rate["schedule_year"] == 6
    assert rate["source_column"] == "2026"
    assert rate["rate_expression"] == "10%"
    assert rate["ad_valorem_rate_pct"] == 10.0


def test_kenya_serves_the_gazetted_base_not_the_etariff_book():
    """0201.10.00 : base 35 % au Journal officiel, sixième annuité 14,0 %.
    L'e-Tariff Book, parti d'une base de 25 %, servait 10 %."""
    rate = resolve_official_preferential_rate("KEN", "02011000", "GHA", as_of_year=2026)
    assert rate["ad_valorem_rate_pct"] == 14.0
    # Ligne du barème absente de l'e-Tariff Book : désormais servie.
    assert resolve_official_preferential_rate("KEN", "51111100", "GHA", as_of_year=2026)
    # Ligne à taux composite, écartée du barème : jamais aplatie à 0 %.
    assert resolve_official_preferential_rate("KEN", "72139110", "GHA", as_of_year=2026) is None

    context = resolve_zlecaf_context("KEN", "GHA", "01012900", 25.0, None)
    assert context["trade_regime"] == "ZLECAF"
    assert context["dd_rate_pct"] == 10.0
    assert context["zlecaf_rate_source"]["implementation_instrument"] == "EAC/321/2022"


def test_offer_lookup_keeps_exact_nine_digit_lines_and_clamps_final_tier():
    line = {
        "hs_code": "123456789",
        "annual_rate_expressions": {"1": "10", "10": "0"},
    }
    dataset = {
        "legal_effect_status": "OFFER_ONLY",
        "execution_authorized": False,
        "origin_schedule_map": {"AO": "1"},
        "_schedule_indexes": {"1": {line["hs_code"]: line}},
        "agreement": "AfCFTA",
        "source_title": "Official test offer",
        "source_url": "https://example.test/offer",
        "source_api_url": "https://example.test/offer/api",
        "collected_at": "2026-08-17",
    }

    rate = _resolve_offer_line(dataset, "TUN", "AGO", "123456789", 2031)

    assert rate["hs_code"] == "123456789"
    assert rate["schedule"] == "1"  # legacy ISO2 snapshot remains readable
    assert rate["schedule_year"] == 10
    assert rate["source_column"] == "year10"
    assert rate["ad_valorem_rate_pct"] == 0.0


def test_collector_normalizes_origin_schedule_keys_to_iso3(monkeypatch):
    monkeypatch.setattr(
        collector,
        "_request_json",
        lambda *_args, **_kwargs: [{"isHeading": False, "regionCode": "EG", "schedule": "1"}],
    )

    mapping = collector._origin_schedule_map("EG", "EG", ["AO", "BF"])

    assert mapping == {"AGO": "1", "BFA": "1"}


def test_sars_writer_emits_deterministic_gzip(tmp_path):
    output = tmp_path / "schedule.json.gz"
    payload = {"schema_version": 1, "lines": [{"hs_code": "010121"}]}

    write_dataset(output, payload)
    first = output.read_bytes()
    write_dataset(output, payload)

    assert output.read_bytes() == first
    assert json.loads(gzip.decompress(first)) == payload


def test_effective_rate_reports_the_mfn_rate_when_schedule_is_higher(monkeypatch):
    line = {
        "dd_rate": 0.0,
        "vat_rate": 15.0,
        "zlecaf_rate": None,
        "other_taxes_rate": 0.0,
        "taxes_detail": {},
        "description_fr": "Produit test",
        "description_en": "Test product",
        "fiscal_advantages": [],
        "administrative_formalities": [],
    }
    monkeypatch.setattr(authentic_tariff_service, "_get_postgres_provider", lambda: None)
    monkeypatch.setattr(
        authentic_tariff_service,
        "load_country_tariffs",
        lambda _iso3: {"generated_at": "2026-08-17"},
    )
    monkeypatch.setattr(authentic_tariff_service, "get_tariff_line", lambda *_args: dict(line))
    monkeypatch.setattr(authentic_tariff_service, "load_crawled_position_index", lambda _iso3: None)
    monkeypatch.setattr(authentic_tariff_service, "get_sub_positions", lambda *_args: [])

    result = authentic_tariff_service.calculate_import_taxes(
        "ZAF", "340700", 1000.0, origin_country="DZA"
    )

    assert result["zlecaf_rate_expression"] == "4%"
    assert result["zlecaf_preference_applied"] is False
    assert result["rates"]["effective_zlecaf_rate_pct"] == 0.0


def test_offer_and_domestication_without_partner_notice_never_calculate():
    assert implementation_decision("GHA", "KEN")["status"] == OFFER_ONLY
    assert implementation_decision("ETH", "KEN")["status"] == PARTNER_NOTICE_REQUIRED
    assert resolve_official_preferential_rate("GHA", "0101210000", "KEN") is None
    assert resolve_official_preferential_rate("ETH", "01012100", "KEN") is None

    # Statut distinct de NOT_AVAILABLE : une offre archivée ou une
    # domestication sans liste de partenaires publiée ne sont jamais
    # calculées, mais ne sont pas non plus une absence pure de source — le
    # frontend les affiche comme « à vérifier avec les douanes locales ».
    offer_only = resolve_zlecaf_context("GHA", "KEN", "0101210000", 5.0, 0.0)
    assert offer_only["trade_regime"] != "ZLECAF"
    assert offer_only["zlecaf_rate_calculation_status"] == OFFER_ONLY
    # Le taux publié est remonté à titre informatif (jamais dans dd_rate_pct,
    # qui reste le taux NPF) pour permettre l'affichage « à vérifier ».
    assert offer_only["dd_rate_pct"] == 5.0
    assert offer_only["zlecaf_offer_rate_pct"] == 2.0
    assert offer_only["zlecaf_offer_rate_expression"] == "2.0%"

    missing_notice = resolve_zlecaf_context("ETH", "KEN", "01012100", 5.0, 0.0)
    assert missing_notice["trade_regime"] != "ZLECAF"
    assert missing_notice["zlecaf_rate_calculation_status"] == PARTNER_NOTICE_REQUIRED
    assert missing_notice["dd_rate_pct"] == 5.0
    assert missing_notice["zlecaf_offer_rate_pct"] == 0.0
    assert missing_notice["zlecaf_offer_rate_expression"] == "0%"


def test_offer_rate_resolves_at_the_source_granularity_not_the_requested_code():
    # Éthiopie/Zambie/Tunisie collectent l'offre en lignes nationales plus
    # longues que le code demandé (ex. ligne éthiopienne 01012100 pour une
    # sous-position nationale 01012100000) : lire l'offre à son niveau publié
    # n'invente rien, la sous-position demandée y est incluse.
    finer = resolve_zlecaf_context("ETH", "KEN", "01012100000", 5.0, 0.0)
    assert finer["zlecaf_offer_rate_pct"] == 0.0

    # L'inverse est interdit : un SH6 ne doit jamais être résolu en piochant
    # arbitrairement l'une de ses sous-positions d'offre, qui portent des
    # concessions différentes.
    coarser = resolve_zlecaf_context("ETH", "KEN", "010121", 5.0, 0.0)
    assert coarser["zlecaf_offer_rate_pct"] is None


def test_accepted_corridor_ignores_unverified_etl_rate_when_exact_line_is_missing():
    context = resolve_zlecaf_context("KEN", "GHA", "99999999", 25.0, 0.0)

    assert context["trade_regime"] == "ZLECAF"
    assert context["zlecaf_eligible"] is True
    assert context["dd_rate_pct"] is None
    assert context["preference_applied"] is False
    assert context["zlecaf_rate_calculation_status"] == "NOT_AVAILABLE"


def test_mar_et_zwe_livrent_une_offre_archivee_sans_appliquer_la_preference():
    """Les deux ajouts à OFFER_DATASETS changent une décision publique.

    Leur statut passe de NOT_AVAILABLE à OFFER_ONLY. Ce n'est pas une
    application de préférence : le taux NPF reste servi, et une suite qui
    n'exerçait que le Ghana et l'Éthiopie ne le vérifiait pour aucun des deux.

    La décision seule ne suffit pas : elle ne rend qu'un CODE de jeu. Tant que
    ce code ne désignait aucun fichier, les 20 527 lignes collectées restaient
    injoignables et cette assertion passait quand même. On va donc jusqu'à la
    ligne servie.
    """
    for destination, dataset in (("MAR", "MAR"), ("ZWE", "ZWE")):
        decision = implementation_decision(destination, "KEN")
        assert decision["applied"] is False, destination
        assert decision["status"] == OFFER_ONLY, destination
        assert decision["tariff_dataset"] == dataset, destination

    marocaine = resolve_published_offer_rate("MAR", "0101210000", "KEN")
    assert marocaine is not None
    assert marocaine["calculation_status"] == "CALCULABLE"
    # Comparaison sur la valeur : la source écrit « 2.5 » dans une annexe et
    # « 2.50 » dans l'autre, et le barème retenu dépend de la circulaire.
    assert float(marocaine["mfn_rate_expression"]) == 2.5

    zimbabweenne = resolve_published_offer_rate("ZWE", "01012100", "KEN")
    assert zimbabweenne is not None
    assert zimbabweenne["calculation_status"] == "CALCULABLE"


def test_le_maroc_repartit_les_origines_selon_sa_circulaire_pas_selon_l_ua():
    """Les deux sources se contredisent ; c'est l'acte national qui tranche.

    L'e-Tariff Book de l'UA répartit les origines marocaines selon le statut
    PMA — Kenya sur l'annexe 5 ans, Burkina Faso sur celle de 10 ans. Les
    listes P1/P2 de la circulaire ADII 6530/223, qui répartissent selon la
    réciprocité effectivement accordée au Maroc, disent l'inverse pour ces
    deux pays comme pour 31 autres (fiche MAR_application_2026-09-13.json).

    Pour une importation AU Maroc, la circulaire fait foi : elle est ce que la
    douane applique. Servir la carte de l'UA afficherait au Kenya un taux de
    0 % là où le Maroc en est à sa sixième tranche sur dix.
    """
    kenya = resolve_zlecaf_context("MAR", "KEN", "0101210000", 2.5, 0.0)
    burkina = resolve_zlecaf_context("MAR", "BFA", "0101210000", 2.5, 0.0)

    assert kenya["zlecaf_offer_rate_source"]["schedule"] == "2"
    assert burkina["zlecaf_offer_rate_source"]["schedule"] == "1"
    assert kenya["zlecaf_offer_rate_pct"] != burkina["zlecaf_offer_rate_pct"]

    # L'offre reste informative : le droit exigible ne bouge pas.
    for contexte in (kenya, burkina):
        assert contexte["zlecaf_rate_calculation_status"] == OFFER_ONLY
        assert contexte["preference_applied"] is False
        assert contexte["dd_rate_pct"] == 2.5


def test_le_maroc_ne_sert_rien_aux_origines_absentes_de_sa_circulaire():
    """L'UA publie 48 origines, le Maroc n'en reconnaît que 40.

    Pour les 7 que l'UA cartographie sans que la circulaire les nomme, servir
    la ligne publiée montrerait une préférence que la douane marocaine
    n'accorde pas. Le silence est ici la seule réponse vraie.
    """
    for origine in ("AGO", "MDG", "MOZ", "ZWE"):
        assert resolve_published_offer_rate("MAR", "0101210000", origine) is None, origine

    # Contrôle en miroir : une destination sans acte national archivé continue
    # de s'appuyer sur la carte de l'UA, sans quoi cette garde effacerait des
    # offres légitimes ailleurs.
    zimbabwe = resolve_published_offer_rate("ZWE", "01012100", "KEN")
    assert zimbabwe is not None
    assert zimbabwe["schedule_selected_by"]["autorite"] == (
        "carte des origines du e-Tariff Book de l'UA"
    )


def test_la_carte_nationale_marocaine_est_bien_celle_de_la_fiche():
    """La carte est lue dans la fiche de détermination, jamais recopiée.

    Si quelqu'un recopiait les listes dans le code, elles divergeraient un
    jour du texte archivé qui les établit. On vérifie donc les effectifs que
    la circulaire publie : 27 pays en P1, 13 en P2.
    """
    carte = _carte_origines_nationale("MAR")

    assert carte is not None
    assert carte["instrument_id"] == "6530/223"
    assert sum(1 for b in carte["origines"].values() if b == "1") == 27
    assert sum(1 for b in carte["origines"].values() if b == "2") == 13


def test_tout_code_de_jeu_reference_designe_un_barme_lisible():
    """Le défaut que la suite précédente ne pouvait pas voir.

    Les codes de jeu vivent dans le registre d'application, les chemins de
    fichiers dans ce module : deux tables, deux fichiers, aucune couture. MAR
    et ZWE ont été collectés, référencés, et n'ont jamais été chargeables —
    sans qu'aucun test ne rougisse. On lie ici les deux tables, pour que le
    prochain barème collecté ne puisse plus rester invisible.
    """
    references = set(OFFER_DATASETS.values())
    references.update(
        record.tariff_dataset for record in RECORDS.values() if record.tariff_dataset
    )

    manquants = sorted(code for code in references if code not in DATASETS)
    assert not manquants, f"codes de jeu sans chemin de fichier : {manquants}"

    illisibles = sorted(code for code in references if _load_dataset(code) is None)
    assert not illisibles, f"codes de jeu dont le barème ne se charge pas : {illisibles}"


def test_une_destination_sans_bareme_archive_reste_indisponible():
    """Le contraste qui donne son sens à OFFER_ONLY : sans jeu, rien n'est servi."""
    decision = implementation_decision("SOM", "KEN")
    assert decision["applied"] is False
    assert decision["status"] == NOT_AVAILABLE
    assert not decision.get("tariff_dataset")
