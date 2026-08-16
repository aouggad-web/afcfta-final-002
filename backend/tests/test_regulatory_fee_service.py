"""Tests du moteur de frais réglementaires — les 7 statuts + règles fail-closed."""

from services.regulatory_compliance_service import get_country_regulatory_compliance
from services.regulatory_fee_service import (
    FEE_STATUSES,
    build_regulatory_cost,
    build_verified_provider_costs,
    compute_fee,
)

_SRC = "gazette-officielle-2024"


def test_calculable_percentage_of_fob_with_minimum():
    r = compute_fee(
        {
            "calculation_method": "PERCENTAGE_OF_FOB",
            "rate": 0.005,
            "minimum_amount": 250,
            "currency": "USD",
            "source": _SRC,
        },
        fob_value=100000,
        fee_exists=True,
    )
    assert r["fee_status"] == "CALCULABLE"
    assert r["calculated_amount"] == 500.0
    assert r["currency"] == "USD"
    # Le plancher s'applique quand le pourcentage est plus bas.
    low = compute_fee(
        {
            "calculation_method": "PERCENTAGE_OF_FOB",
            "rate": 0.005,
            "minimum_amount": 250,
            "currency": "USD",
            "source": _SRC,
        },
        fob_value=1000,
        fee_exists=True,
    )
    assert low["calculated_amount"] == 250.0


def test_documented_fixed_amount():
    r = compute_fee(
        {
            "calculation_method": "FIXED_AMOUNT",
            "fixed_amount": 100,
            "currency": "USD",
            "source": _SRC,
        },
        fee_exists=True,
    )
    assert r["fee_status"] == "DOCUMENTED_FIXED_AMOUNT"
    assert r["calculated_amount"] == 100.0


def test_no_source_never_produces_a_cost():
    # Règle 1 : un frais sans source officielle n'est jamais chiffré.
    r = compute_fee(
        {"calculation_method": "FIXED_AMOUNT", "fixed_amount": 100, "currency": "USD"},
        fee_exists=True,
    )
    assert r["fee_status"] == "FEE_EXISTS_AMOUNT_NOT_AVAILABLE"
    assert r["calculated_amount"] is None


def test_percentage_without_base_is_partial_never_zero():
    # Règle 3 : pas de pourcentage sans assiette explicite.
    r = compute_fee(
        {
            "calculation_method": "PERCENTAGE_OF_CIF",
            "rate": 0.005,
            "currency": "USD",
            "source": _SRC,
        },
        fob_value=100000,  # CIF non fourni → pas d'assiette pour la méthode CIF
        fee_exists=True,
    )
    assert r["fee_status"] == "PARTIAL"
    assert r["calculated_amount"] is None


def test_absent_detail_with_confirmed_existence_is_flagged():
    # Règle 2 : existence confirmée mais montant inconnu → signalé, jamais 0.
    r = compute_fee(None, fee_exists=True)
    assert r["fee_status"] == "FEE_EXISTS_AMOUNT_NOT_AVAILABLE"
    assert r["calculated_amount"] is None


def test_absent_detail_without_existence_is_not_available():
    r = compute_fee(None, fee_exists=False)
    assert r["fee_status"] == "NOT_AVAILABLE"
    assert r["calculated_amount"] is None


def test_all_returned_statuses_are_canonical():
    samples = [
        compute_fee(None, fee_exists=True),
        compute_fee(None, fee_exists=False),
        compute_fee(
            {
                "calculation_method": "FIXED_AMOUNT",
                "fixed_amount": 1,
                "currency": "USD",
                "source": _SRC,
            }
        ),
        compute_fee(
            {
                "calculation_method": "PERCENTAGE_OF_FOB",
                "rate": 0.01,
                "currency": "USD",
                "source": _SRC,
            },
            fob_value=100,
        ),
        compute_fee(
            {"calculation_method": "PERCENTAGE_OF_FOB", "currency": "USD", "source": _SRC},
            fob_value=None,
        ),
    ]
    for r in samples:
        assert r["fee_status"] in FEE_STATUSES


# ── build_regulatory_cost sur données réelles (fail-closed) ────────────────────


def test_active_provider_country_yields_unpriced_incomplete_block():
    # CMR : prestataires actifs, aucun frais chiffré publié → bloc présent mais
    # incomplet, tous FEE_EXISTS_AMOUNT_NOT_AVAILABLE, total None (jamais 0).
    rc = build_regulatory_cost(
        get_country_regulatory_compliance("CMR"), fob_value=50000, side="import"
    )
    assert rc is not None
    assert rc["complete"] is False
    assert rc["has_unpriced_fees"] is True
    assert rc["regulatory_cost_total"] is None
    assert all(li["fee_status"] != "CALCULABLE" for li in rc["line_items"])


def test_country_without_active_provider_but_undetermined_status_still_shows_formality():
    # CIV : mesures sans prestataire actif confirmé (GUCE, RFCV, BSC, VOC — statut
    # NOT_AVAILABLE, jamais NOT_APPLICABLE) restent visibles comme formalité seule,
    # jamais chiffrées, jamais masquées faute de prestataire/frais trouvé.
    rc = build_regulatory_cost(get_country_regulatory_compliance("CIV"), fob_value=50000)
    assert rc is not None
    assert rc["line_items"], "les formalités CIV à prestataire non confirmé doivent apparaître"
    for li in rc["line_items"]:
        assert li["scope"] == "formality"
        assert li["provider_status"] == "UNCONFIRMED"
        assert li["fee_status"] != "CALCULABLE"


def test_provider_and_formality_fees_are_bucketed_separately():
    rc = build_regulatory_cost(
        get_country_regulatory_compliance("CMR"), fob_value=50000, side="import"
    )
    scopes = {li["scope"] for li in rc["line_items"]}
    assert "provider" in scopes  # au moins une ligne prestataire
    # Chaque ligne est étiquetée soit formality soit provider, jamais fusionnée.
    assert scopes.issubset({"provider", "formality"})


def test_registry_stage_reflects_logistics_step_not_side():
    # `side` = axe origine/destination du registre consulté ; `stage` = étape
    # logistique réelle (amont export / aval import). Un contrôle de
    # conformité (PECAE) ou un suivi de cargaison (BESC), quoique consultés
    # via le registre de DESTINATION (side="import"), sont accomplis avant
    # embarquement dans le pays d'origine → stage="export", jamais copié
    # depuis side. Un guichet unique ou un contrôle de valeur (RFCV/CIVIC),
    # eux, restent une procédure de dédouanement à destination → stage=side.
    rc = build_regulatory_cost(
        get_country_regulatory_compliance("CMR"), fob_value=50000, side="import"
    )
    def assert_all_stages(cost_block, measure_name, expected_stage):
        matching_lines = [
            line for line in cost_block["line_items"] if line["measure_name"] == measure_name
        ]
        assert matching_lines, f"Aucune ligne trouvée pour {measure_name}"
        assert all(line["stage"] == expected_stage for line in matching_lines)

    assert_all_stages(
        rc,
        "Programme d'Évaluation de la Conformité Avant Embarquement (PECAE)",
        "export",
    )
    assert_all_stages(
        rc,
        "Bordereau Électronique de Suivi des Cargaisons (BESC)",
        "export",
    )
    assert_all_stages(
        rc,
        "Contrôle d'Identification des Véhicules Importés au Cameroun (CIVIC)",
        "import",
    )

    civ_rc = build_regulatory_cost(
        get_country_regulatory_compliance("CIV"), fob_value=50000, side="import"
    )
    assert_all_stages(
        civ_rc,
        "Bordereau de Suivi des Cargaisons (BSC)",
        "export",
    )
    assert_all_stages(
        civ_rc,
        "Guichet Unique du Commerce Extérieur (GUCE-CI)",
        "import",
    )


def test_expired_only_country_never_yields_a_provider_line():
    # Un mandat expiré n'entre jamais dans le calcul (règle 5) : CIV n'a aucun
    # acteur actif, donc aucun de ses acteurs historiques ne génère de ligne
    # "provider" ni de montant chiffré — seule la formalité elle-même apparaît.
    rc = build_regulatory_cost(get_country_regulatory_compliance("CIV"), fob_value=1)
    assert rc is not None
    assert all(li["scope"] != "provider" for li in rc["line_items"])
    assert all(li["fee_status"] != "CALCULABLE" for li in rc["line_items"])


def test_confirmed_direct_administration_measure_stays_excluded():
    # KEN-KRA-ACD est NOT_APPLICABLE (source confirmant une opération directe,
    # sans prestataire) : cette mesure reste hors du volet formalités déléguées,
    # contrairement à une mesure NOT_AVAILABLE (statut non établi).
    compliance = get_country_regulatory_compliance("KEN")
    rc = build_regulatory_cost(compliance, fob_value=50000)
    names = {li["measure_name"] for li in (rc or {}).get("line_items", [])}
    excluded = [
        m for m in compliance["measures"] if m.get("mandated_actor_status") == "NOT_APPLICABLE"
    ]
    assert excluded, "KEN doit conserver au moins une mesure NOT_APPLICABLE de référence"
    excluded_names = {m["measure_name"] for m in excluded}
    assert not (excluded_names & names)


# ── Fourchette de taux (route-dépendante) ─────────────────────────────────────


def test_rate_range_produces_bounded_min_max_amounts():
    r = compute_fee(
        {
            "calculation_method": "PERCENTAGE_OF_FOB",
            "rate_min": 0.0030,
            "rate_max": 0.0045,
            "source": _SRC,
        },
        fob_value=100000,
        fee_exists=True,
    )
    assert r["fee_status"] == "CALCULABLE"
    assert r["is_range"] is True
    assert r["calculated_amount"] is None
    assert r["calculated_amount_min"] == 300.0
    assert r["calculated_amount_max"] == 450.0
    # Ad valorem sans devise imposée : l'unité est celle de la valeur saisie.
    assert r["ad_valorem"] is True


# ── Frais VÉRIFIÉS sur source primaire (VOC Côte d'Ivoire) ────────────────────


def test_verified_voc_civ_is_calculable_range_with_sources():
    items = build_verified_provider_costs("CIV", fob_value=100000, side="import")
    assert len(items) == 1
    voc = items[0]
    assert voc["fee_status"] == "CALCULABLE"
    assert voc["is_range"] is True
    assert voc["tier"] == "VERIFIED_PRIMARY"
    assert voc["calculated_amount_min"] == 300.0
    assert voc["calculated_amount_max"] == 450.0
    # Source primaire obligatoire (règle 1) réellement présente.
    assert voc["source"] and voc["source"].startswith("http")
    assert voc["verification_sources"]
    # Seuil et conditions FCFA transmis (non appliqués numériquement — anti-FX).
    assert voc["threshold_fob_xof"] == 1000000
    assert "0,30%" in (voc["conditions"] or "")


def test_verified_costs_absent_for_uncovered_country():
    assert build_verified_provider_costs("DZA", fob_value=100000, side="import") == []


def test_verified_kenya_pvoc_bracket_from_kebs():
    items = build_verified_provider_costs("KEN", fob_value=100000, side="import")
    assert len(items) == 1
    pvoc = items[0]
    assert pvoc["fee_status"] == "CALCULABLE"
    assert pvoc["is_range"] is True
    # 0,50%-0,60% de 100000 = 500-600 (bornes ad valorem).
    assert pvoc["calculated_amount_min"] == 500.0
    assert pvoc["calculated_amount_max"] == 600.0
    assert pvoc["source"] and "kebs.org" in pvoc["source"]
    assert "300 USD" in (pvoc["conditions"] or "")


def test_verified_tanzania_pvoc_bracket_from_tbs():
    items = build_verified_provider_costs("TZA", fob_value=100000, side="import")
    assert len(items) == 1
    pvoc = items[0]
    assert pvoc["fee_status"] == "CALCULABLE"
    assert pvoc["is_range"] is True
    # 0,25%-0,53% de 100000 = 250-530.
    assert pvoc["calculated_amount_min"] == 250.0
    assert pvoc["calculated_amount_max"] == 530.0
    assert pvoc["source"] and pvoc["source"].startswith("http")


def test_verified_uganda_pvoc_bracket_from_unbs():
    items = build_verified_provider_costs("UGA", fob_value=100000, side="import")
    assert len(items) == 1
    pvoc = items[0]
    assert pvoc["fee_status"] == "CALCULABLE"
    assert pvoc["is_range"] is True
    # 0,25%-0,50% de 100000 = 250-500.
    assert pvoc["calculated_amount_min"] == 250.0
    assert pvoc["calculated_amount_max"] == 500.0
    assert pvoc["source"] and pvoc["source"].startswith("http")
    assert "235 USD" in (pvoc["conditions"] or "")


def test_verified_cameroon_pecae_bracket_with_legal_basis():
    items = build_verified_provider_costs("CMR", fob_value=100000, side="import")
    assert len(items) == 1
    pecae = items[0]
    assert pecae["fee_status"] == "CALCULABLE"
    assert pecae["is_range"] is True
    # 0,27%-0,45% de 100000 = 270-450.
    assert pecae["calculated_amount_min"] == 270.0
    assert pecae["calculated_amount_max"] == 450.0
    # Base légale (décret) citée dans les conditions.
    assert "Décret" in (pecae["conditions"] or "")


def test_verified_zimbabwe_cbca_bracket_with_statutory_instrument():
    items = build_verified_provider_costs("ZWE", fob_value=100000, side="import")
    assert len(items) == 1
    cbca = items[0]
    assert cbca["fee_status"] == "CALCULABLE"
    assert cbca["is_range"] is True
    # 0,25%-0,50% de 100000 = 250-500 (general goods).
    assert cbca["calculated_amount_min"] == 250.0
    assert cbca["calculated_amount_max"] == 500.0
    assert "S.I. 35" in (cbca["conditions"] or "")


def test_verified_gabon_progec_bracket():
    items = build_verified_provider_costs("GAB", fob_value=100000, side="import")
    assert len(items) == 1
    progec = items[0]
    assert progec["fee_status"] == "CALCULABLE"
    assert progec["is_range"] is True
    # 0,27%-0,53% de 100000 = 270-530.
    assert progec["calculated_amount_min"] == 270.0
    assert progec["calculated_amount_max"] == 530.0
    assert progec["source"] and progec["source"].startswith("http")


def test_verified_congo_brazzaville_pcec_bracket():
    # COG (Brazzaville) — distinct de COD (RDC).
    items = build_verified_provider_costs("COG", fob_value=100000, side="import")
    assert len(items) == 1
    pcec = items[0]
    assert pcec["fee_status"] == "CALCULABLE"
    assert pcec["is_range"] is True
    assert pcec["calculated_amount_min"] == 270.0
    assert pcec["calculated_amount_max"] == 530.0
    assert pcec["source"] and pcec["source"].startswith("http")


def test_verified_drc_occ_needs_cif_base_and_is_calculable_with_it():
    # OCC RDC = 2% de la valeur CIF. Sans assiette CIF → PARTIAL (fail-closed, on ne
    # substitue jamais le FOB au CIF). Avec CIF → montant unique 2% CIF.
    no_cif = build_verified_provider_costs("COD", fob_value=100000, side="import")[0]
    assert no_cif["fee_status"] == "PARTIAL"
    assert no_cif["calculated_amount"] is None
    with_cif = build_verified_provider_costs(
        "COD", fob_value=100000, cif_value=100000, side="import"
    )[0]
    assert with_cif["fee_status"] == "CALCULABLE"
    assert with_cif["is_range"] is False
    assert with_cif["calculated_amount"] == 2000.0
    assert with_cif["base_label"] == "CIF"
    # OCC est un organisme ÉTATIQUE : le prélèvement est classé perçu PUBLIC
    # (formalité), pas frais de prestataire privé.
    assert with_cif["scope"] == "formality"
    assert with_cif["collector_type"] == "STATE_BODY"
    # Split BIVAC/OCC et avertissement taxe santé documentés.
    assert "0,75%" in (with_cif["conditions"] or "")
    assert "santé" in (with_cif["conditions"] or "").lower()


def test_verified_nigeria_soncap_sc_fixed_amount():
    # SONCAP Certificate (SC) = montant FIXE par expédition (350 USD), délivré par
    # des organismes privés mandatés par la SON.
    items = build_verified_provider_costs("NGA", fob_value=100000, cif_value=100000, side="import")
    assert len(items) == 1
    sc = items[0]
    assert sc["fee_status"] == "DOCUMENTED_FIXED_AMOUNT"
    assert sc["calculated_amount"] == 350.0
    assert sc["currency"] == "USD"
    assert sc["scope"] == "provider"
    # PC (par produit) et CISS (douane) explicitement hors de cette ligne.
    assert "PC1" in (sc["conditions"] or "") and "CISS" in (sc["conditions"] or "")


def test_verified_morocco_voc_single_rate():
    # Maroc : taux unique 0,45% FOB (identique toutes routes) → montant unique.
    items = build_verified_provider_costs("MAR", fob_value=100000, side="import")
    assert len(items) == 1
    voc = items[0]
    assert voc["fee_status"] == "CALCULABLE"
    assert voc["is_range"] is False
    assert voc["calculated_amount"] == 450.0
    assert voc["stage"] == "export"
    assert voc["source"] and voc["source"].startswith("http")


def test_stage_separates_export_upstream_from_import_downstream():
    # Conformité payée par l'exportateur → étape EXPORT (amont). OCC/SONCAP payés
    # par l'importateur → étape IMPORT (aval).
    civ = build_verified_provider_costs("CIV", fob_value=100000, side="import")[0]
    ken = build_verified_provider_costs("KEN", fob_value=100000, side="import")[0]
    cod = build_verified_provider_costs("COD", fob_value=100000, cif_value=100000, side="import")[0]
    nga = build_verified_provider_costs("NGA", fob_value=100000, side="import")[0]
    assert civ["stage"] == "export" and ken["stage"] == "export"
    assert cod["stage"] == "import" and nga["stage"] == "import"


def test_every_verified_fee_carries_a_primary_source():
    # Règle 1 : chaque frais vérifié exploitable cite au moins une source (y
    # compris les frais à assiette CIF, d'où le cif_value fourni).
    for iso in ("CIV", "KEN", "TZA", "UGA", "CMR", "ZWE", "GAB", "COG", "COD", "NGA", "MAR"):
        for item in build_verified_provider_costs(
            iso, fob_value=100000, cif_value=100000, side="import"
        ):
            assert item["source"] and item["source"].startswith("http")
            assert item["verification_sources"]
