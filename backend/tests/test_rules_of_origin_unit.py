"""
Unit tests for the rules-of-origin single source of truth.

Covers routes.rules_of_origin.get_rule_of_origin(), the function shared by
etl/hs6_database.py since the Phase 1 consolidation
that retired the separate, drifting etl.afcfta_rules_of_origin dataset.

Regression target: HS6 codes under heading 62.03 (men's suits) that don't
have their own explicit subheading rule (e.g. 620319) must resolve via the
heading-level CTH rule, not silently fall back to chapter 62's YARN default
— that exact fallback was the bug in the now-retired dataset.
"""

import asyncio
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import routes.rules_of_origin as roo


def _load_rules_data():
    path = os.path.join(os.path.dirname(__file__), "..", "data", "zlecaf_rules_of_origin.json")
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def setup_module(module):
    data = _load_rules_data()
    roo.init_data(data, data.get("origin_types"))


def test_heading_6203_fallback_no_longer_uses_chapter_yarn_rule():
    result = roo.get_rule_of_origin("620319", "fr")
    assert result["primary_rule"]["code"] == "CTH"
    assert result["source"] == "HEADING"
    # CTH has no percentage threshold in the dataset (it's a tariff-
    # classification-change rule, not a value-content rule) - None is the
    # correct, intentional value here, not a missing default to fabricate.
    # See routes/rules_of_origin.py::_regional_content.
    assert result["regional_content"] is None


def test_explicit_subheading_6203_still_resolves_via_subheading():
    result = roo.get_rule_of_origin("620311", "fr")
    assert result["primary_rule"]["code"] == "CTH"
    assert result["source"] == "SUBHEADING"


def test_wholly_obtained_products():
    for hs6 in ("100110", "090111"):
        result = roo.get_rule_of_origin(hs6, "fr")
        assert result["primary_rule"]["code"] == "WO"
        # WO is 100% regional content by definition, even though the
        # dataset's own `threshold` field is null for WO entries.
        assert result["regional_content"] == 100


def test_unknown_chapter_returns_ytb_shaped_fallback_without_crashing():
    result = roo.get_rule_of_origin("999999", "fr")
    assert result["status"] == "UNKNOWN"
    assert result["primary_rule"]["code"] == "YTB"
    assert result["source"] == "NONE"


def test_short_and_long_hs_codes_are_normalized():
    heading_only = roo.get_rule_of_origin("6203", "fr")
    assert heading_only["primary_rule"]["code"] == "CTH"

    eight_digit = roo.get_rule_of_origin("62031900", "fr")
    assert eight_digit["primary_rule"]["code"] == "CTH"
    assert eight_digit["source"] == "HEADING"


def test_shape_matches_legacy_etl_consumers():
    result = roo.get_rule_of_origin("850440", "fr")
    for key in (
        "hs6_code",
        "heading",
        "chapter",
        "chapter_description",
        "status",
        "primary_rule",
        "alternative_rule",
        "regional_content",
        "notes",
        "source",
        "source_detail",
    ):
        assert key in result
    assert "code" in result["primary_rule"]
    assert "name" in result["primary_rule"]
    assert "description" in result["primary_rule"]
    assert "explanation" in result["primary_rule"]


# --- Phase 2: HS6 granularity expansion regression tests -------------------
#
# These cover entries added by parsing the official AfCFTA Appendice IV PSR
# document (user-provided source, December 2023 / 12th Council of Ministers)
# directly, expanding heading/subheading coverage from 101/15 to 239/49.
# Every assertion below is grounded in that document's literal text - no
# threshold or rule code here was invented.


def test_phase2_heading_coverage_expanded_well_beyond_phase1():
    headings = roo.RULES_DATA.get("headings", {})
    subheadings = roo.RULES_DATA.get("subheadings", {})
    assert len(headings) >= 240
    assert len(subheadings) >= 45


def test_phase2_bracketed_source_code_maps_to_ytb_not_a_guessed_rule():
    # Source document lists "[52.04]" (brackets = not yet adopted) for
    # cotton sewing thread - must resolve to YTB, never a fabricated CTH/VA.
    result = roo.get_rule_of_origin("520400", "fr")
    assert result["primary_rule"]["code"] == "YTB"
    assert result["regional_content"] is None


def test_phase2_new_heading_cth_rule_grounded_in_source_text():
    # 85.19 (sound recording/reproducing apparatus): "Fabrication à partir
    # de matières de toute position autre que celle du produit" -> CTH.
    result = roo.get_rule_of_origin("851900", "fr")
    assert result["primary_rule"]["code"] == "CTH"
    assert result["source"] == "HEADING"


def test_phase2_new_heading_va_threshold_matches_source_percentage():
    # 84.01 (nuclear reactors): "...n'excède pas 60 %..." -> VA60,
    # implied regional content 40 (100 - 60), not an invented figure.
    result = roo.get_rule_of_origin("840100", "fr")
    assert result["primary_rule"]["code"] == "VA60"
    assert result["regional_content"] == 40


def test_phase2_existing_phase1_subheading_entries_untouched():
    # The Phase 1 6203.11/31/41 entries must survive Phase 2 merge unchanged
    # (merge policy: never overwrite an existing chapter/heading/subheading).
    for hs6 in ("620311", "620331", "620341"):
        result = roo.get_rule_of_origin(hs6, "fr")
        assert result["primary_rule"]["code"] == "CTH"
        assert result["source"] == "SUBHEADING"


# --- Copilot review follow-up: extraction-artifact regressions -------------


def test_no_glued_words_around_ou_alternative_marker():
    # Heading 50.01's source rule splits two "Ou"-joined alternatives with
    # no delimiter ("...produitOuImpression...") - the raw text stored in
    # the dataset must have the word boundary restored, not the glued
    # artifact.
    raw = roo.RULES_DATA["headings"]["5001"]["raw_fr"]
    assert "produitOu" not in raw
    assert "nonimprimé" not in raw


def test_no_leaked_rule_sentence_in_description():
    # Heading 84.56's source table has a malformed column boundary that
    # bleeds a "Fabrication dans laquelle..." rule fragment into the
    # product description cell - that duplicate fragment must not surface
    # in description_fr.
    result = roo.get_rule_of_origin("845600", "fr")
    assert "Fabrication dans laquelle" not in result["primary_rule"]["description"]


def test_empty_source_row_is_omitted_not_fabricated():
    # Subheading 6212.90 has a genuinely empty description and rule cell
    # in the source document - rather than fabricate placeholder content,
    # it must be absent so HS 621290 falls back to heading 62.12's rule.
    assert "621290" not in roo.RULES_DATA.get("subheadings", {})
    result = roo.get_rule_of_origin("621290", "fr")
    assert result["source"] in ("HEADING", "CHAPTER")


def test_empty_ytb_rule_text_normalized_to_a_determiner():
    # Subheading 6207.19 is YTB with an empty rule cell in the source -
    # raw_fr must show the dataset's existing "not yet agreed" placeholder
    # rather than an empty string.
    assert roo.RULES_DATA["subheadings"]["620719"]["raw_fr"] == "À déterminer"
    result = roo.get_rule_of_origin("620719", "fr")
    assert result["primary_rule"]["code"] == "YTB"


# --- Phase 3: plain-language rule explanations ------------------------------


def test_every_origin_type_has_an_explanation_in_both_languages():
    for code, entry in roo.ORIGIN_TYPES.items():
        explanation = entry.get("explanation")
        assert explanation, f"{code} is missing an explanation"
        assert explanation.get("fr"), f"{code} is missing a French explanation"
        assert explanation.get("en"), f"{code} is missing an English explanation"


def test_get_rule_of_origin_includes_explanation_for_each_language():
    result_fr = roo.get_rule_of_origin("620319", "fr")
    assert result_fr["primary_rule"]["explanation"] == roo.ORIGIN_TYPES["CTH"]["explanation"]["fr"]

    result_en = roo.get_rule_of_origin("620319", "en")
    assert result_en["primary_rule"]["explanation"] == roo.ORIGIN_TYPES["CTH"]["explanation"]["en"]


def test_explanation_absent_for_unknown_code_path():
    result = roo.get_rule_of_origin("999999", "fr")
    assert result["primary_rule"]["explanation"] == roo.ORIGIN_TYPES["YTB"]["explanation"]["fr"]


def test_explanations_are_grounded_in_annexe_2_articles():
    # Explanations cite the actual AfCFTA Annexe 2 sur les Règles d'Origine
    # articles each rule code implements (art. 4-6), not generic textbook
    # ROO phrasing, so the wording is traceable to the authoritative source.
    grounding = {
        "WO": "5",
        "CTH": "6(1)(c)",
        "CTSH": "6(1)(d)",
        "VA": "6(1)(b)",
        "VA60": "6(1)(b)",
        "SP": "6(1)(e)",
    }
    for code, article_ref in grounding.items():
        explanation = roo.ORIGIN_TYPES[code]["explanation"]["fr"]
        assert article_ref in explanation, f"{code} explanation doesn't cite art. {article_ref}"
        assert "Annexe 2" in explanation


def test_va_threshold_explanation_states_the_specific_percentage():
    result = roo.get_rule_of_origin("840100", "fr")
    assert result["primary_rule"]["code"] == "VA60"
    assert "60" in result["primary_rule"]["explanation"]


# --- Legacy `rule` shape read by frontend/.../RulesTab.jsx -----------------


def test_endpoint_value_added_threshold_is_null_for_a_cth_rule():
    # 85.19 is a CTH rule: Appendice IV gives it no value threshold, so the
    # endpoint must not hand the screen a percentage (it used to send 60).
    cth = asyncio.run(roo.get_rules_of_origin("851900", lang="fr"))
    assert cth["rules"]["primary_rule"]["code"] == "CTH"
    assert cth["rule"]["value_added_threshold"] is None

    # A VA60 rule keeps its implied regional content (100 - 60).
    va60 = asyncio.run(roo.get_rules_of_origin("840100", lang="fr"))
    assert va60["rule"]["value_added_threshold"] == 40


def test_endpoint_requirement_is_the_rule_text_not_the_product_designation():
    # In the dataset, description_fr is the product designation (85.19:
    # "Appareils d'enregistrement du son…") and raw_fr the Appendice IV rule.
    # raw_fr exists in French only, so English gets that same text too.
    for hs6, heading in (("851981", "8519"), ("040310", "0403")):
        entry = roo.RULES_DATA["headings"][heading]
        for lang in ("fr", "en"):
            result = asyncio.run(roo.get_rules_of_origin(hs6, lang=lang))
            assert result["matched_code"] == heading
            assert result["rule"]["psr"] == entry["raw_fr"]
            assert result["rules"]["primary_rule"]["description"] == entry["raw_fr"]
            assert entry["description_fr"] not in result["rule"].values()


def test_endpoint_has_no_english_rule_text_to_offer():
    # No English version of the rule exists in the dataset: rule_text_en is
    # empty, not the English product name (04.03: "Buttermilk, curdled
    # milk, yogurt, kephir").
    result = asyncio.run(roo.get_rules_of_origin("040310", lang="en"))
    assert result["rules"]["rule_text_en"] == ""


def test_endpoint_distinguishes_designation_and_negotiated_requirement():
    result = asyncio.run(roo.get_rules_of_origin("600110", lang="ar"))
    assert result["status"] == "YTB"
    assert result["product_description_fr"]
    assert result["rule"]["psr"] == ""
    assert result["rule"]["value_added_threshold"] is None


def test_endpoint_exposes_note_25_without_claiming_an_effective_threshold():
    for code in ("841410", "841911"):
        result = asyncio.run(roo.get_rules_of_origin(code, lang="fr"))
        assert result["rules"]["threshold_note_fr"].startswith("Note 2.5")
        assert result["rules"]["threshold_pct"] is None
        assert result["rule"]["value_added_threshold"] is None


def test_internal_origin_summary_matches_api_when_threshold_is_unconfirmed():
    for code in ("841410", "841911", "600110"):
        public = asyncio.run(roo.get_rules_of_origin(code, lang="fr"))
        internal = roo.get_rule_of_origin(code, "fr")
        assert public["rules"]["regional_content"] is None
        assert internal["regional_content"] is None
        explanation = public["rules"]["primary_rule"]["explanation"]
        assert explanation == internal["primary_rule"]["explanation"]
        # Pending rule: Appendix IV note 2.4 explanation. Note 2.5: the generic value
        # criterion, which names no percentage (never the disputed 60 %).
        expected = "YTB" if public["status"] == "YTB" else "VA"
        assert explanation == roo.ORIGIN_TYPES[expected]["explanation"]["fr"]
        assert "60 %" not in explanation
    assert roo.get_rule_of_origin("840100", "fr")["regional_content"] == 40


def test_calculator_legal_reference_cites_the_resolved_row():
    for requested, kind, matched in (
        ("851981", "heading", "8519"),
        ("620719", "subheading", "620719"),
        ("600110", "chapter", "60"),
    ):
        result = asyncio.run(roo.get_rules_of_origin(requested, lang="fr"))
        reference = result["legal_reference"]
        assert reference["match_type"] == kind
        assert reference["matched_code"] == matched
        assert "Annexe 2" in reference["instrument_fr"]
        assert reference["source_version"]
    pending = asyncio.run(roo.get_rules_of_origin("600110", lang="fr"))
    assert any("2.4" in note for note in pending["legal_reference"]["notes_fr"])
    qualified = asyncio.run(roo.get_rules_of_origin("841410", lang="fr"))
    assert any("2.5" in note for note in qualified["legal_reference"]["notes_fr"])


def test_legal_reference_cites_the_annexe_2_article_of_the_criterion():
    # Each article is the one the rule type's own explanation already cites.
    for code, article in roo._CRITERION_ARTICLES.items():
        assert article in roo.ORIGIN_TYPES[code]["explanation"]["fr"], code

    # Every Appendix IV row rests on art. 6(2) of Annex 2 (official text,
    # Algerian Customs): "les marchandises listées à l'Appendice IV [...] se
    # qualifient comme marchandises originaires si elles satisfont aux règles
    # définies dans les présentes"; the criterion's article follows.
    appendix_iv = "Annexe 2, article 6(2) (règles de l'Appendice IV)"
    cth = asyncio.run(roo.get_rules_of_origin("851981", lang="fr"))["legal_reference"]
    assert cth["articles_fr"] == [
        appendix_iv,
        "Annexe 2, article 6(1)(c) (Changement de Position Tarifaire)",
    ]
    assert cth["location_fr"] == "position 85.19"

    wo = asyncio.run(roo.get_rules_of_origin("040110", lang="fr"))["legal_reference"]
    assert wo["articles_fr"] == [appendix_iv, "Annexe 2, art. 4(a) et art. 5 (Entièrement Obtenu)"]

    pending = asyncio.run(roo.get_rules_of_origin("600110", lang="fr"))["legal_reference"]
    # A rule not yet adopted: Appendix IV note 2.4, and Annex 2 art. 42 quoted
    # verbatim (official text, Algerian Customs), without asserting its scope.
    assert pending["articles_fr"] == [
        "Annexe 2, article 42, alinéas 1(c) et 3 (dispositions en suspens)"
    ]
    assert pending["notes_fr"] == [
        "Appendice IV, note 2.4 (règle pas encore adoptée par les institutions "
        "de négociation de la ZLECAf)"
    ]
    ytb = roo.ORIGIN_TYPES["YTB"]["explanation"]
    assert "note 2.4" in ytb["fr"] and "note 2.4" in ytb["en"]
    assert (
        "« En attendant l'adoption des dispositions en suspens, les États parties conviennent "
        "que les Règles d'Origine des régimes commerciaux existants sont applicables. »"
    ) in ytb["fr"]


# --- The rule code only describes rows whose text states its criterion -----


def test_code_derived_name_explanation_and_article_only_when_the_text_states_it():
    appendix_iv = "Annexe 2, article 6(2) (règles de l'Appendice IV)"
    # 21.05 is coded WO, but its text only requires the materials of chapters
    # 2, 4, 7, 8, 17 and 18 to be originating: the wholly-obtained name,
    # explanation, art. 4(a)/5 and 100 % regional content would contradict it.
    ice_cream = asyncio.run(roo.get_rules_of_origin("210500", lang="fr"))
    rule = ice_cream["rules"]["primary_rule"]
    assert rule["code"] == "WO" and rule["matches_text"] is False
    assert rule["name"] == "Règle propre à cette ligne de l'Appendice IV"
    assert rule["explanation"] == ""
    assert ice_cream["rules"]["regional_content"] is None
    assert ice_cream["rule"]["wholly_obtained"] is False
    assert ice_cream["legal_reference"]["articles_fr"] == [appendix_iv]
    assert roo.get_rule_of_origin("210500", "fr")["regional_content"] is None

    # Wine: CTH plus "les raisins [...] doivent être entièrement obtenus".
    wine = asyncio.run(roo.get_rules_of_origin("220421", lang="fr"))["rules"]["primary_rule"]
    assert wine["matches_text"] is False and wine["explanation"] == ""

    # A row whose text is exactly its code's criterion keeps everything.
    cth = asyncio.run(roo.get_rules_of_origin("851981", lang="fr"))["rules"]["primary_rule"]
    assert cth["matches_text"] is True
    assert cth["name"] == "Changement de Position Tarifaire"
    assert cth["explanation"] == roo.ORIGIN_TYPES["CTH"]["explanation"]["fr"]
    wholly = roo.get_rule_of_origin("270900", "fr")
    assert wholly["primary_rule"]["name"] == "Entièrement Obtenu"
    assert wholly["regional_content"] == 100


def test_glued_ou_alternatives_are_split():
    # "produitOu Fabrication" and "OuFabrication" in the source text.
    assert roo._rule_branches(roo.RULES_DATA["headings"]["8516"]["raw_fr"]) == [
        "Fabrication à partir de matières de toute position autre que celle du produit",
        "Fabrication dans laquelle la valeur des matières utilisées n'excède pas 60 % "
        "du prix départ usine du produit",
    ]
    assert len(roo._rule_branches(roo.RULES_DATA["headings"]["8525"]["raw_fr"])) == 2


def test_pending_and_note_25_rules_are_never_named_by_the_disputed_criterion():
    # Chapter 60 is coded YARN but not adopted: named as pending, not "fils".
    pending = asyncio.run(roo.get_rules_of_origin("600110", lang="fr"))["rules"]["primary_rule"]
    assert pending["name"] == roo.ORIGIN_TYPES["YTB"]["fr"]
    # Note 2.5 rows: named by the value criterion, never "Max 60 %".
    for code in ("841410", "841911"):
        result = asyncio.run(roo.get_rules_of_origin(code, lang="fr"))
        assert result["rules"]["primary_rule"]["name"] == roo.ORIGIN_TYPES["VA"]["fr"]
        assert all("60" not in a for a in result["legal_reference"]["articles_fr"])
        assert (
            roo.get_rule_of_origin(code, "fr")["primary_rule"]["name"]
            == roo.ORIGIN_TYPES["VA"]["fr"]
        )


# --- Appendix IV notes: sorted, internal ones never served ------------------

_INTERNAL_VOCABULARY = (
    "module Python",
    "headings[",
    "alt_code",
    "régression",
    "Bracketed",
    "bracketed",
    "texte plain",
    "littéralement",
    "YTB",
    "retombe",
    "prime sur ce défaut",
)


def test_only_source_notes_are_served():
    served = 0
    for level in ("chapters", "headings", "subheadings"):
        for key, entry in roo.RULES_DATA[level].items():
            for note in entry.get("notes") or []:
                served += 1
                assert not any(word in note for word in _INTERNAL_VOCABULARY), (key, note)
            for note in entry.get("curation_notes") or []:
                assert note not in (entry.get("notes") or [])
    assert served == 41
    result = asyncio.run(roo.get_rules_of_origin("850440", lang="fr"))
    assert result["rules"]["applicable_notes"] == []  # chapter 85: internal note only
    assert "curation_notes" not in json.dumps(result)


def test_notes_corrected_from_the_official_french_appendix_iv():
    # Footnote 27 (p. 68): the chapter rule itself was approved.
    ch61 = roo.RULES_DATA["chapters"]["61"]["notes"]
    assert ch61 == [
        "Le chapitre 61 doit encore être finalisé. La règle du chapitre a été approuvée, "
        "mais les États membres disposent d'une certaine souplesse pour soumettre des "
        "exceptions pour les rubriques et sous-rubriques"
    ]
    # Note 8: rules 3 (mixtures) and 4 (particle size) do not cover chapter 28.
    (ch28,) = roo.RULES_DATA["chapters"]["28"]["notes"]
    assert "Règle 1 : Origine de la réaction chimique" in ch28
    assert "mélange" not in ch28.lower() and "particules" not in ch28


def test_note_9_is_on_the_headings_it_governs_verbatim():
    # Note 9 (Appendix IV, p. 14-15) defines vehicle construction or assembly
    # only for the vehicles listed in 9.1/9.2 (87.01 to 87.04, bodies of 87.07)
    # and for chassis (9.3, 87.06): not on chapter 87, shown for 87.13.
    assert roo.RULES_DATA["chapters"]["87"]["notes"] == []
    assert roo.RULES_DATA["headings"]["8705"]["notes"] == []
    for heading in ("8701", "8702", "8703", "8704", "8706", "8707"):
        (note,) = roo.RULES_DATA["headings"][heading]["notes"]
        assert note.startswith("Note 9 de l'Appendice IV: 9.1 Dans le cas de tracteurs routiers")
        assert "9.3 Dans le cas de châssis équipés de moteurs" in note
    wheelchairs = asyncio.run(roo.get_rules_of_origin("871310", lang="fr"))
    assert wheelchairs["rules"]["applicable_notes"] == []


def test_value_rules_cite_the_non_originating_content_criterion():
    # Annex 2 art. 6(1)(b) "la teneur des matières non originaires", the
    # percentages of Appendix IV (art. 6A(1)(b)); (a) value added is another criterion.
    va60 = asyncio.run(roo.get_rules_of_origin("850440", lang="fr"))["legal_reference"]
    assert "Annexe 2, article 6(1)(b) (Max 60% valeur non-originaire)" in va60["articles_fr"]
    for code in ("VA", "VA15", "VA40", "VA50", "VA60", "VA65"):
        assert "6(1)(b)" in roo.ORIGIN_TYPES[code]["explanation"]["fr"]
        assert "6(1)(a)" not in roo.ORIGIN_TYPES[code]["explanation"]["fr"]


def test_change_of_chapter_rests_on_article_6_2_not_6_1_c():
    # Annex 2 art. 6(1)(c) is "le changement de position tarifaire" (4 digits,
    # art. 1(o)); art. 6(1) has no chapter-level criterion, so a change of
    # chapter is an Appendix IV rule applied under art. 6(2) (Appendix IV note 1.1).
    assert "CC" not in roo._CRITERION_ARTICLES
    for lang, article in (("fr", "article 6(2)"), ("en", "Art. 6(2)")):
        explanation = roo.ORIGIN_TYPES["CC"]["explanation"][lang]
        assert article in explanation and "6(1)(c)" not in explanation
    # The only CC rows (82.13, 8212.20) read "de toute position": their own text.
    for code in ("821320", "821220"):
        reference = asyncio.run(roo.get_rules_of_origin(code, lang="fr"))["legal_reference"]
        assert reference["articles_fr"] == ["Annexe 2, article 6(2) (règles de l'Appendice IV)"]
