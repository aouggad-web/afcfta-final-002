"""
Unit tests for the rules-of-origin single source of truth.

Covers routes.rules_of_origin.get_rule_of_origin(), the function shared by
etl/hs6_database.py since the Phase 1 consolidation
that retired the separate, drifting etl.afcfta_rules_of_origin dataset.

Every HS code resolves to the row of the official French Appendix IV
(December 2023) that governs it, read with its introductory notes 2.1 to 2.4:
e.g. the 62.03 row covers only the sub-positions listed under it (note 2.3),
so 620319 falls under chapter 62's rule.
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


def test_dash_listed_rows_cover_only_their_sub_positions():
    # Note 2.3 (p. 2): each dash designates the part of the heading subject to
    # the rule. The 62.03 (p. 68), 62.07 (p. 69) and 62.08 (pp. 69-70) rows list
    # sub-positions only; the others fall under the Chapitre 62 row.
    for heading in ("6203", "6207", "6208"):
        assert heading not in roo.RULES_DATA["headings"]
    for hs6 in ("620319", "620711", "620821"):
        result = roo.get_rule_of_origin(hs6, "fr")
        assert result["source"] == "CHAPTER"
        assert result["primary_rule"]["code"] == "YARN"
    # 6207.19, 6207.22, 6207.29 and 6207.99 take the 62.07 rule, which nothing
    # brackets (note 2.4): adopted, no longer « À déterminer ».
    for hs6 in ("620719", "620722", "620729", "620799", "620811", "620829"):
        result = roo.get_rule_of_origin(hs6, "fr")
        assert result["source"] == "SUBHEADING"
        assert result["status"] == "AGREED"
        assert result["primary_rule"]["code"] == "CTH"
        assert result["primary_rule"]["matches_text"] is True
        # CTH has no percentage threshold: None, not a defaulted value.
        assert result["regional_content"] is None
    assert roo.RULES_DATA["subheadings"]["620719"]["raw_fr"] == (
        "Fabrication à partir de matières de toute position autre que celle du produit, "
        "sous réserve d'une révision après 5 ans"
    )


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
    heading_only = roo.get_rule_of_origin("8519", "fr")
    assert heading_only["primary_rule"]["code"] == "CTH"

    eight_digit = roo.get_rule_of_origin("85198100", "fr")
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
    # Headings the table does not have (44.06 to 44.12 list sub-positions only)
    # or covers only in part (notes 2.1 and 2.3) are no longer heading entries.
    headings = roo.RULES_DATA.get("headings", {})
    subheadings = roo.RULES_DATA.get("subheadings", {})
    assert len(headings) >= 230
    assert len(subheadings) >= 60


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


def test_heading_6212_sub_lines_are_paired_in_order():
    # Pp. 70-71: the dash lines « - Brassières » (p. 70), « - Gaines et
    # gaines-culottes », « - Corselettes » and « - autres » sit one line apart
    # from the codes 6212.10 to 6212.90 (p. 71), each code with an « Adopté par »
    # footnote (39 to 42). Paired in order, as in the HS, all take the 62.12 rule.
    rule = roo.RULES_DATA["headings"]["6212"]["raw_fr"]
    for hs6, designation in (
        ("621210", "- Brassières"),
        ("621220", "- Gaines et gaines-culottes"),
        ("621230", "- Corselettes"),
        ("621290", "- autres"),
    ):
        entry = roo.RULES_DATA["subheadings"][hs6]
        assert entry["product_description_fr"] == designation
        assert entry["raw_fr"] == rule
        assert entry["status"] == "AGREED" and entry["code"] == "CTH"


def test_rows_left_to_be_determined_show_that_text():
    # Column 3 of [63.01] to [63.06] reads « À déterminer » (pp. 71-73): the
    # rule text is that, not a dataset summary, and none is an « ex » row.
    for heading in ("6301", "6302", "6303", "6304", "6305", "6306"):
        entry = roo.RULES_DATA["headings"][heading]
        assert entry["raw_fr"] == "À déterminer"
        assert entry["status"] == "YTB" and entry["ex"] is False


# --- Phase 3: plain-language rule explanations ------------------------------


def test_every_origin_type_has_an_explanation_in_both_languages():
    for code, entry in roo.ORIGIN_TYPES.items():
        explanation = entry.get("explanation")
        assert explanation, f"{code} is missing an explanation"
        assert explanation.get("fr"), f"{code} is missing a French explanation"
        assert explanation.get("en"), f"{code} is missing an English explanation"


def test_get_rule_of_origin_includes_explanation_for_each_language():
    result_fr = roo.get_rule_of_origin("620311", "fr")
    assert result_fr["primary_rule"]["explanation"] == roo.ORIGIN_TYPES["CTH"]["explanation"]["fr"]

    result_en = roo.get_rule_of_origin("620311", "en")
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


def test_endpoint_applies_note_25_threshold_of_55_since_2026():
    # Note 2.5 (p. 2): 60 % "automatiquement ramenée … à 55 % à la fin d'une
    # période de cinq (5) ans, à compter du 1er janvier 2021".
    for code in ("841410", "841911"):
        result = asyncio.run(roo.get_rules_of_origin(code, lang="fr"))
        assert result["rules"]["threshold_note_fr"].startswith("Note 2.5")
        assert result["rules"]["threshold_pct"] == 55
        assert result["rules"]["regional_content"] == 45
        assert result["rule"]["value_added_threshold"] == 45
        assert "60 %" in result["rules"]["rule_text_fr"]  # the row text stays as printed


def test_internal_origin_summary_matches_api_for_note_25_and_pending_rules():
    for code, regional, expected in (
        ("841410", 45, "VA55"),
        ("841911", 45, "VA55"),
        ("600110", None, "YTB"),
    ):
        public = asyncio.run(roo.get_rules_of_origin(code, lang="fr"))
        internal = roo.get_rule_of_origin(code, "fr")
        assert public["rules"]["regional_content"] == regional
        assert internal["regional_content"] == regional
        explanation = public["rules"]["primary_rule"]["explanation"]
        assert explanation == internal["primary_rule"]["explanation"]
        assert explanation == roo.ORIGIN_TYPES[expected]["explanation"]["fr"]
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
    # 68.03 reads "Fabrication sans laquelle [...]", a typo of the official
    # text for the wording of 68.01/68.02: the same criterion.
    slate = asyncio.run(roo.get_rules_of_origin("680300", lang="fr"))
    assert slate["rules"]["primary_rule"]["matches_text"] is True
    assert slate["rules"]["primary_rule"]["name"] == "Entièrement Obtenu"
    assert slate["legal_reference"]["articles_fr"] == [
        appendix_iv,
        "Annexe 2, art. 4(a) et art. 5 (Entièrement Obtenu)",
    ]


def test_glued_ou_alternatives_are_split():
    # "produitOu Fabrication" and "OuFabrication" in the source text.
    assert roo._rule_branches(roo.RULES_DATA["headings"]["8516"]["raw_fr"]) == [
        "Fabrication à partir de matières de toute position autre que celle du produit",
        "Fabrication dans laquelle la valeur des matières utilisées n'excède pas 60 % "
        "du prix départ usine du produit",
    ]
    assert len(roo._rule_branches(roo.RULES_DATA["headings"]["8525"]["raw_fr"])) == 2


def test_pending_rules_are_named_as_such_and_note_25_rules_by_their_55_percent():
    # [Chapitre 60] is not adopted: named as pending.
    pending = asyncio.run(roo.get_rules_of_origin("600110", lang="fr"))["rules"]["primary_rule"]
    assert pending["name"] == roo.ORIGIN_TYPES["YTB"]["fr"]
    # Note 2.5 rows: the 60 % printed in the row became 55 % on 1 January 2026.
    for code in ("841410", "841911"):
        result = asyncio.run(roo.get_rules_of_origin(code, lang="fr"))
        assert result["rules"]["primary_rule"]["name"] == "Max 55% valeur non-originaire"
        assert result["legal_reference"]["articles_fr"][-1] == (
            "Annexe 2, article 6(1)(b) (Max 55% valeur non-originaire)"
        )
        assert (
            roo.get_rule_of_origin(code, "fr")["primary_rule"]["name"]
            == "Max 55% valeur non-originaire"
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
    assert served == 80
    result = asyncio.run(roo.get_rules_of_origin("850440", lang="fr"))
    assert result["rules"]["applicable_notes"] == []  # chapter 85: internal note only
    assert "curation_notes" not in json.dumps(result)
    # A rewording of the row text (already shown as the requirement) or a
    # dataset summary of its scope is not a note of Appendix IV; the footnote
    # printed on the row is (24.02: footnote 24, p. 35).
    for code, notes in (
        ("190590", []),
        (
            "240220",
            ["Adopté par la 7ème réunion du Conseil des Ministres de la ZLECAf (juillet 2022)"],
        ),
    ):
        result = asyncio.run(roo.get_rules_of_origin(code, lang="fr"))
        assert result["rules"]["applicable_notes"] == notes, code


def test_notes_corrected_from_the_official_french_appendix_iv():
    # Footnote 27 (p. 68): the chapter rule itself was approved.
    ch61 = roo.RULES_DATA["chapters"]["61"]["notes"]
    assert ch61 == [
        "Le chapitre 61 doit encore être finalisé. La règle du chapitre a été approuvée, "
        "mais les États membres disposent d'une certaine souplesse pour soumettre des "
        "exceptions pour les rubriques et sous-rubriques"
    ]
    # Footnote 28 (p. 68), verbatim.
    assert roo.RULES_DATA["chapters"]["62"]["notes"] == [
        "Adopté par la 2ème réunion extraordinaire du Conseil des Ministres de la ZLECAf (mai 2023)"
    ]
    # Note 8 (pp. 11-14) in full, on chapters 28 to 38 whose rows refer to it
    # (« Règles de traitement chimique conformément à la Note introductive 8 »):
    # its rules 3 and 4 state their own chapters.
    (note_8,) = roo.RULES_DATA["chapters"]["28"]["notes"]
    assert note_8.startswith(
        "Note 8 de l'Appendice IV: Notes pour la Section VI du Système Harmonisé "
        "Produits des industries chimiques ou des industries connexes (chapitres 28 à 38) "
        "8.1 : Les règles 1 à 7 de la présente section"
    )
    assert (
        "Règle 3 : Mélanges et mixtures 8.7 : Les produits des chapitres 30, 31, 33 à 38" in note_8
    )
    assert note_8.endswith(
        "à moins que la matière ainsi isolée n'ait subi une réaction chimique sur le "
        "territoire d'un ou de plusieurs États parties."
    )
    for chapter in range(29, 39):
        assert roo.RULES_DATA["chapters"][str(chapter)]["notes"] == [note_8]
    # Note 4 (pp. 4-6) in full: 4.1 and 4.3 for 27.07 and 27.13, 4.2 for 27.10
    # to 27.12; no pointer left on chapter 27.
    assert roo.RULES_DATA["chapters"]["27"]["notes"] == []
    for heading, start in (
        ("2707", "4.1 : Aux fins des positions 27.07 et 27.13"),
        ("2713", "4.1 : Aux fins des positions 27.07 et 27.13"),
        ("2710", "4.2 Aux fins des positions 27.10, 27.11 et 27.12"),
        ("2711", "4.2 Aux fins des positions 27.10, 27.11 et 27.12"),
        ("2712", "4.2 Aux fins des positions 27.10, 27.11 et 27.12"),
    ):
        (note,) = roo.RULES_DATA["headings"][heading]["notes"]
        assert note.startswith(f"Note 4 de l'Appendice IV: {start}")
    assert (
        "4.3 : Aux fins des positions 27.07 et 27.13"
        in roo.RULES_DATA["headings"]["2713"]["notes"][0]
    )
    # Note 2.5 (p. 2), with its printed comma.
    (note_25,) = roo.RULES_DATA["headings"]["8414"]["notes"]
    assert note_25.endswith(
        "à la fin d'une période de cinq (5) ans, à compter du 1er janvier 2021."
    )


def test_note_9_is_on_the_headings_it_governs_verbatim():
    # Note 9 (Appendix IV, p. 14-15) defines vehicle construction or assembly
    # only for the vehicles listed in 9.1/9.2 (87.01 to 87.04, bodies of 87.07)
    # and for chassis (9.3, 87.06): not on chapter 87, whose own footnote 45
    # (p. 114) is shown for 87.13.
    footnote_45 = (
        "Adopté par la 3ème réunion extraordinaire du Conseil des Ministres de la ZLECAf "
        "(juillet 2023)"
    )
    assert roo.RULES_DATA["chapters"]["87"]["notes"] == [footnote_45]
    assert roo.RULES_DATA["headings"]["8705"]["notes"] == []
    for heading in ("8701", "8702", "8703", "8704", "8706", "8707"):
        notes = roo.RULES_DATA["headings"][heading]["notes"]
        (note,) = [note for note in notes if note.startswith("Note 9")]
        assert note.startswith("Note 9 de l'Appendice IV: 9.1 Dans le cas de tracteurs routiers")
        assert "9.3 Dans le cas de châssis équipés de moteurs" in note
    wheelchairs = asyncio.run(roo.get_rules_of_origin("871310", lang="fr"))
    assert wheelchairs["rules"]["applicable_notes"] == [footnote_45]


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


def test_ex_2009_89_juice_exception_is_served_verbatim():
    # Appendix IV p. 30: the "Ex. 2009.89" row (mangosteen, kiwi, persimmon,
    # starfruit and Bush Tucker juices) has its own phased rule; the entry's
    # raw_fr is the rule of the "Autres" row, so the exception is a served note.
    result = asyncio.run(roo.get_rules_of_origin("200989", lang="fr"))
    assert result["rules"]["applicable_notes"] == [
        "Ex. 2009.89 (Jus de mangoustan, Jus de kiwi, Jus de kaki, Jus de carambole, "
        "Jus de Bush Tucker) : Fabrication dans laquelle la valeur des matières non "
        "originaires utilisées ne doit pas excéder 60 % du prix départ usine du produit "
        "pendant 5 ans, après quoi la fabrication dans laquelle tous les légumes, fruits, "
        "noix ou autres parties de plantes utilisées doivent être entièrement obtenus",
        # Footnote of the row (p. 30).
        "Adopté par la 7ème réunion du Conseil des Ministres de la ZLECAf (10 octobre 2021)",
    ]
    assert "curation_notes" not in roo.RULES_DATA["subheadings"]["200989"]


def test_no_rule_rows_are_named_as_having_no_rule_of_origin():
    # 63.09 and 63.10 read "Pas de règle" (Appendix IV p. 74): named as such, not
    # as a row-specific rule, in both outputs (the strategic-flows chip receives
    # only the name and the code).
    for code in ("630900", "631010"):
        rule = asyncio.run(roo.get_rules_of_origin(code, lang="fr"))["rules"]["primary_rule"]
        assert rule["code"] == "NONE" and rule["matches_text"] is True
        assert rule["name"] == "Pas de règle d'origine" and rule["explanation"] == ""
        assert (
            roo.get_rule_of_origin(code, "fr")["primary_rule"]["name"] == "Pas de règle d'origine"
        )
    assert roo.get_rule_of_origin("630900", "en")["primary_rule"]["name"] == "No rule of origin"


def test_row_specific_rule_comes_with_its_row_text_outside_the_endpoint():
    # The strategic-flows chip and the re-export note only get
    # get_rule_of_origin(): a row-specific name must come with the row text.
    palm = roo.get_rule_of_origin("151110", "fr")["primary_rule"]
    assert palm["name"] == "Règle propre à cette ligne de l'Appendice IV"
    assert palm["matches_text"] is False
    assert palm["rule_text_fr"] == roo.RULES_DATA["headings"]["1511"]["raw_fr"]
    assert roo.get_rule_of_origin("270900", "fr")["primary_rule"]["matches_text"] is True
    pending = roo.get_rule_of_origin("870323", "fr")["primary_rule"]  # 87.03: À déterminer
    assert pending["matches_text"] is False and pending["rule_text_fr"] == ""


def test_chapter_71_row_is_the_official_text():
    # Appendix IV pp. 77-78: change of heading Ou value of all materials
    # <= 60 %. The dataset text had a summary of its own in place of the
    # value alternative, and row-specific rules are now quoted as such.
    assert roo.RULES_DATA["chapters"]["71"]["raw_fr"] == (
        "Fabrication à partir de matières de toute position autre que celle du produit "
        "Ou Fabrication dans laquelle la valeur de toutes les matières utilisées "
        "n'excède pas 60 % du prix départ usine du produit"
    )
    rule = roo.get_rule_of_origin("711319", "fr")
    assert rule["primary_rule"]["name"] == "Changement de Position Tarifaire"
    assert rule["primary_rule"]["matches_text"] is True
    assert rule["alternative_rule"]["code"] == "VA60"
    assert rule["alternative_rule"]["explanation"] != ""


# --- Official Appendix IV applied completely (notes 2.1 to 2.4) -------------


def test_ex_rows_cover_only_the_part_they_describe():
    # Note 2.1: an "ex" rule applies only to the part described in column 2.
    # Ex 15.12 (p. 23) names sunflower and safflower oils, not cotton-seed oil;
    # Ex -22.02 (p. 32) sweetened or flavoured waters; Ex 76.01 (p. 82) alloys.
    for hs6, row, governs in (
        ("151211", "ex position 15.12", True),
        ("151219", "ex position 15.12", True),
        ("151221", "ex chapitre 15", False),
        ("220210", "ex position 22.02", True),
        ("220299", "ex chapitre 22", False),
        ("760120", "ex position 76.01", True),
        ("760110", "ex chapitre 76", False),
    ):
        result = asyncio.run(roo.get_rules_of_origin(hs6, lang="fr"))
        assert result["legal_reference"]["location_fr"] == row, hs6
        assert (result["match_type"] == "subheading") is governs, hs6
    for heading in ("1512", "2202", "7601"):
        assert heading not in roo.RULES_DATA["headings"]
    # Ex -7103.10 / Ex -7103.99 (p. 79) covers tanzanite only: the other stones
    # of those sub-positions keep the Ex - 71.03 rule, with that row as a note.
    stones = asyncio.run(roo.get_rules_of_origin("710310", lang="fr"))
    assert stones["matched_code"] == "7103"
    assert stones["rules"]["applicable_notes"] == [
        "Ex -7103.10, Ex -7103.99 (Tanzanite) : Fabrication dans laquelle toutes les "
        "matières utilisées doivent être entièrement obtenues"
    ]


def test_grouped_and_listed_rows_cover_exactly_their_codes():
    # Note 2.2: the « 41.07 à 41.13 » row (p. 49) applies to 41.12 and 41.13 too,
    # and is cited as printed. Its designation is that of 41.07 (bovine and equine
    # leather): 41.12 and 41.13 get none of their own.
    for hs6 in ("410711", "411200", "411310"):
        result = roo.get_rule_of_origin(hs6, "fr")
        assert result["source"] == "HEADING"
        assert result["primary_rule"]["rule_text_fr"] == (
            "Fabrication dans laquelle les matières des positions 41.01 à 41.06 utilisées "
            "doivent être entièrement obtenues"
        )
        endpoint = asyncio.run(roo.get_rules_of_origin(hs6, lang="fr"))
        assert endpoint["legal_reference"]["location_fr"] == "positions 41.07 à 41.13"
    for hs6 in ("411200", "411310"):
        endpoint = asyncio.run(roo.get_rules_of_origin(hs6, lang="fr"))
        assert endpoint["product_description_fr"] == ""
    # Pp. 51-52 list sub-positions of 44.06 to 44.12, not those headings: the
    # unlisted codes (coniferous sleepers, non-tropical sawn wood...) fall under
    # the Ex-chapitre 44 rule.
    for heading in ("4406", "4407", "4408", "4409", "4412"):
        assert heading not in roo.RULES_DATA["headings"]
    for hs6, source in (
        ("440612", "SUBHEADING"),
        ("440692", "SUBHEADING"),
        ("440721", "SUBHEADING"),
        ("440611", "CHAPTER"),
        ("440711", "CHAPTER"),
        ("441210", "CHAPTER"),
    ):
        assert roo.get_rule_of_origin(hs6, "fr")["source"] == source, hs6


def test_bracketed_or_undetermined_text_is_not_adopted_and_the_rest_is():
    # Note 2.4 (p. 2): bracketed text is not adopted. 63.07 (p. 73) caps the
    # value at « [50 %] »: pending, no 60 % rule.
    made_up = asyncio.run(roo.get_rules_of_origin("630790", lang="fr"))
    assert made_up["status"] == "YTB"
    assert made_up["rules"]["threshold_pct"] is None
    assert "[50 %]" in roo.RULES_DATA["headings"]["6307"]["raw_fr"]
    # 56.01 (p. 64): only the « [50 %] » alternative is bracketed; its change
    # of heading is adopted.
    wadding = asyncio.run(roo.get_rules_of_origin("560121", lang="fr"))
    assert wadding["status"] == "AGREED"
    assert wadding["rules"]["primary_rule"]["code"] == "CTH"
    assert wadding["rules"]["alternative_rule"]["code"] == "YTB"
    # Ex-CHAPITRE 63 (p. 71): an adopted change of heading, not a summary.
    textiles = roo.RULES_DATA["chapters"]["63"]
    assert (textiles["code"], textiles["status"]) == ("CTH", "AGREED")
    assert textiles["raw_fr"] == (
        "Fabrication à partir de matières de toute position autre que celle du produit"
    )
    # [Chapitre 60] (p. 67): « À déterminer » only.
    knitted = roo.RULES_DATA["chapters"]["60"]
    assert (knitted["raw_fr"], knitted["code"]) == ("À déterminer", "YTB")


def test_alternatives_printed_in_the_rows_are_served():
    # Chapters whose row prints a value alternative after « Ou » (pp. 77-122),
    # and chapters 57 and 58 their specific-process alternatives (pp. 64-65).
    for chapter, alternative in (
        ("57", "SP"),
        ("58", "SP"),
        ("70", "VA60"),
        ("74", "VA60"),
        ("75", "VA60"),
        ("86", "VA60"),
        ("88", "VA60"),
        ("89", "VA60"),
        ("91", "VA60"),
        ("93", "VA60"),
        ("95", "VA60"),
        ("96", "VA60"),
        ("97", "VA40"),
    ):
        entry = roo.RULES_DATA["chapters"][chapter]
        assert len(roo._rule_branches(entry["raw_fr"])) >= 2, chapter
        assert entry["alt_code"] == alternative, chapter
        assert roo._criterion_fits(entry, alternative=True), chapter
    # 85.43 (p. 112) prints its value alternative without « utilisées ».
    assert roo._criterion_fits(roo.RULES_DATA["headings"]["8543"], alternative=True)


def test_review_clause_worded_avec_une_revision_keeps_the_value_criterion():
    # Ex-chapitre 87 (p. 114) and 87.09 (p. 116): « …, avec une révision après 5 ans. »
    assert roo.RULES_DATA["chapters"]["87"]["raw_fr"] == (
        "Fabrication dans laquelle la valeur des matières utilisées ne doit pas excéder "
        "60 % du prix départ usine du produit, avec une révision après 5 ans."
    )
    for hs6, name, regional in (
        ("871310", "Max 60% valeur non-originaire", 40),
        ("870900", "Max 65% valeur non-originaire", 35),
    ):
        result = asyncio.run(roo.get_rules_of_origin(hs6, lang="fr"))
        assert result["rules"]["primary_rule"]["name"] == name
        assert result["rules"]["regional_content"] == regional
