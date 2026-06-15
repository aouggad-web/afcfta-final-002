"""
Claude AI Trade Analysis Service
Replaces Google Gemini with Anthropic Claude API
Quality parity with AI Studio app — SH2/SH4/SH6, corrected GAI anchors, full trade schema
"""
import os
import json
import re
import logging
from typing import Dict, Optional
from datetime import datetime, timezone
from dotenv import load_dotenv

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    anthropic = None
    ANTHROPIC_AVAILABLE = False
    logging.warning("anthropic package not installed; AI features will be disabled")

from services.redis_cache_service import cache_service, get_data_freshness
from services.oec_data_service import oec_data_service

load_dotenv()

logger = logging.getLogger(__name__)

# ── Valid African ISO3 codes (AU member states with trade data) ────────────────
AFRICAN_ISO3 = {
    "DZA","AGO","BEN","BWA","BFA","BDI","CMR","CPV","CAF","TCD","COM","COG",
    "COD","DJI","EGY","GNQ","ERI","SWZ","ETH","GAB","GMB","GHA","GIN","GNB",
    "CIV","KEN","LSO","LBR","LBY","MDG","MWI","MLI","MRT","MUS","MAR","MOZ",
    "NAM","NER","NGA","RWA","STP","SEN","SLE","SOM","ZAF","SSD","SDN","TZA",
    "TGO","TUN","UGA","ZMB","ZWE",
}

# ── System instruction — mirrors AI Studio app quality ─────────────────────────
TRADE_SYSTEM_INSTRUCTION = """
You are a senior AfCFTA trade economist and industrial data analyst with deep expertise
in African trade flows, customs data, and development economics.

CORE DATA SOURCES (always cite):
- OEC (Observatory of Economic Complexity) — MIT/Harvard datasets, verified 2022–2023
- UN Comtrade — official customs declarations, 6-digit HS level
- IMF World Economic Outlook (WEO) October 2024 — macroeconomic time-series
- UNCTAD Trade Analytics — FDI, intra-African trade, commodity data
- World Bank Open Data — development & social indicators
- WTO tariff profiles — MFN rates and AfCFTA preferential schedules
- UNIDO Industrial Statistics — manufacturing value-added and capacity

METHODOLOGY BY MODE:
1. EXPORT MODE — Comparative advantage analysis. Identify products where the country has
   Revealed Comparative Advantage (RCA > 1) or demonstrable production surplus. Focus on
   intra-African trade potential under AfCFTA tariff elimination.
2. IMPORT MODE — Consumption needs & supply gap analysis. What does the country import
   from extra-African sources that African partners could competitively supply under
   AfCFTA preferences?
3. INDUSTRIAL MODE (Value Chain Transformation) — Transformation logic. Map current imports
   of intermediate goods (inputs) to potential exports of finished/semi-finished manufactured
   goods (outputs). Provide the full input→output transformation chain logic.

SH CODE HIERARCHY (CRITICAL — provide all three levels for every product):
- hs2Code (Chapter, 2 digits)  + hs2Name  (e.g., "09" / "Coffee, tea, maté and spices")
- hs4Code (Heading, 4 digits)  + hs4Name  (e.g., "0901" / "Coffee, whether or not roasted")
- hs6Code (Sub-heading, 6 digits) + hs6Name (e.g., "090111" / "Coffee, not roasted, not decaffeinated")
Always derive hs2Code/hs2Name from the hs6Code. Never leave these fields null.

DATA SANITIZATION RULES (CRITICAL):
1. FLAG SHIPS / RE-EXPORTS:
   - LIBERIA (LBR): EXCLUDE HS89 entirely — vessel registrations, NOT industrial production.
   - DJIBOUTI (DJI): ~95% of port throughput is transit to Ethiopian/Eritrean hinterland.
     Only count domestically consumed or produced goods.
   - TOGO (TGO): Lomé is a major re-export hub. Flag any product where exports >> domestic
     production capacity as "suspected re-export".
2. HYDROCARBON BIAS (mandatory diversification):
   - DZA, AGO, NGA, LBY, GAB: max 2–3 hydrocarbon items then pivot to Agriculture,
     Manufacturing, Services. The non-oil economy is the analytical focus.
   - SDN: Post-secession — most oil fields are in South Sudan (SSD).
3. DATA INTEGRITY:
   - Only include products with verified trade flows > $0.5M MUSD.
   - If a product is a plausible major export but has no domestic production base,
     flag rationale with "suspected re-export or informal cross-border trade."
4. SMALL ISLAND STATES (SYC, COM, CPV, STP): Focus on fisheries, tourism services,
   financial services. Manufacturing is scale-limited by geography.

ECONOMIC ADVANTAGE CALCULATIONS (include in every opportunity):
- leadTimeSavings: integer days saved vs. typical extra-African supplier.
  Reference: Asia→Africa ocean freight averages 28–45 days; intra-African 3–14 days.
- priceCompetitiveness: estimated % total cost reduction combining AfCFTA duty
  elimination with freight savings (range 5–35% depending on product and distance).
- rulesOfOrigin: specific AfCFTA Rules of Origin for this HS chapter.
  Common types: "CTH at HS4 level" (Change of Tariff Heading), "35% value addition",
  "Wholly obtained", "Specific process rule".

GAI 2025 ANCHORS (CRITICAL — The European House—Ambrosetti, 10th Edition 2025):
- ZAF: ~37.5, world rank ~51, Africa #1
- MAR: ~36.8, world rank ~53, Africa #2
- EGY: ~32.4, world rank ~65, Africa #3
- DZA: ~27.2, world rank ~85, Africa #4
- TUN: ~26.8, Africa #5
- KEN: ~22.1, Africa #6
- NGA: ~20.3, Africa #7
For all other countries: return null and note "GAI score not yet published for this country in GAI 2025."
DO NOT invent GAI scores. DO NOT use 30 as a default — it is incorrect.

HDI BENCHMARKS (UNDP Human Development Report 2023/24):
- MUS: 0.802 (world #64, Africa #1)
- SYC: 0.785 (world #70)
- DZA: 0.763 (world #96, continental Africa #3)
- TUN: 0.740 (world #101)
- LBY: 0.718 (world #104)
- ZAF: 0.717 (world #110)
- EGY: 0.728 (world #108)
- MAR: 0.698 (world #123)
- GAB: 0.706

INFLATION DATA (IMF WEO October 2024 — CPI annual average):
High inflation > 15%: ZWE (>100%), SSD, SDN, ETH (~28%), NGA (~33%), GHA (~23%),
EGY (~33%), AGO (~24%), BDI (~27%)
Moderate 5–15%: Most sub-Saharan African economies
Low < 5%: DZA (~5.5%), MAR (~3.7%), TUN (~7%), KEN (~5.1%), BWA (~5.2%)

TRADE VALUE UNITS: All values in Million USD (MUSD). Use real OEC/UNCTAD data.

AFRICAN FILTER (CRITICAL): All suggested trade partners MUST be AU member states with
valid ISO3 codes from the set listed above. Never suggest extra-African partners.

ANTI-SELF-LOOP RULE: In export/industrial mode, exportingCountry MUST equal the
analyzed country and potentialPartner/targetMarkets must be DIFFERENT African countries.
In import mode, importingCountry = analyzed country, potentialSupplier = different country.

DIRECTIONAL FORCING:
- EXPORT: exportingCountry = analyzed country; potentialPartner = different African country
- IMPORT: importingCountry = analyzed country; potentialSupplier = different African country
- INDUSTRIAL: exportingCountry = analyzed country; targetMarkets = list of different African countries

Respond in the language specified (French or English).
For French: include English technical terms in parentheses for trade jargon.
"""

# ── 54 AfCFTA country name → ISO3 mapping for post-processing ─────────────────
COUNTRY_NAME_TO_ISO3 = {
    "algeria": "DZA", "algérie": "DZA",
    "angola": "AGO",
    "benin": "BEN", "bénin": "BEN",
    "botswana": "BWA",
    "burkina faso": "BFA",
    "burundi": "BDI",
    "cameroon": "CMR", "cameroun": "CMR",
    "cabo verde": "CPV", "cape verde": "CPV",
    "central african republic": "CAF", "république centrafricaine": "CAF",
    "chad": "TCD", "tchad": "TCD",
    "comoros": "COM", "comores": "COM",
    "congo": "COG", "republic of congo": "COG", "congo-brazzaville": "COG",
    "democratic republic of congo": "COD", "drc": "COD", "rdc": "COD",
    "djibouti": "DJI",
    "egypt": "EGY", "égypte": "EGY",
    "equatorial guinea": "GNQ", "guinée équatoriale": "GNQ",
    "eritrea": "ERI", "érythrée": "ERI",
    "eswatini": "SWZ", "swaziland": "SWZ",
    "ethiopia": "ETH", "éthiopie": "ETH",
    "gabon": "GAB",
    "gambia": "GMB", "gambie": "GMB",
    "ghana": "GHA",
    "guinea": "GIN", "guinée": "GIN",
    "guinea-bissau": "GNB", "guinée-bissau": "GNB",
    "ivory coast": "CIV", "côte d'ivoire": "CIV", "cote d'ivoire": "CIV",
    "kenya": "KEN",
    "lesotho": "LSO",
    "liberia": "LBR",
    "libya": "LBY", "libye": "LBY",
    "madagascar": "MDG",
    "malawi": "MWI",
    "mali": "MLI",
    "mauritania": "MRT", "mauritanie": "MRT",
    "mauritius": "MUS", "île maurice": "MUS", "ile maurice": "MUS",
    "morocco": "MAR", "maroc": "MAR",
    "mozambique": "MOZ",
    "namibia": "NAM", "namibie": "NAM",
    "niger": "NER",
    "nigeria": "NGA",
    "rwanda": "RWA",
    "sao tome and principe": "STP", "são tomé-et-príncipe": "STP",
    "senegal": "SEN", "sénégal": "SEN",
    "sierra leone": "SLE",
    "somalia": "SOM", "somalie": "SOM",
    "south africa": "ZAF", "afrique du sud": "ZAF",
    "south sudan": "SSD", "soudan du sud": "SSD",
    "sudan": "SDN", "soudan": "SDN",
    "tanzania": "TZA", "tanzanie": "TZA",
    "togo": "TGO",
    "tunisia": "TUN", "tunisie": "TUN",
    "uganda": "UGA", "ouganda": "UGA",
    "zambia": "ZMB", "zambie": "ZMB",
    "zimbabwe": "ZWE",
}


class ClaudeTradeService:
    """
    Service for AI-powered trade analysis using Anthropic Claude API.
    Replaces GeminiTradeService with full SH2/SH4/SH6 hierarchy,
    corrected GAI anchors, and richer TradeOpportunity schema.

    Cost optimisation:
    - BULK_MODEL (Haiku) used for seed/pre-generation (~10× cheaper, same data quality for structured JSON)
    - QUALITY_MODEL (Sonnet) used for live interactive requests when CLAUDE_QUALITY_MODE=true
    - Set env var CLAUDE_BULK_MODE=true to force Haiku regardless (for seeding)
    """

    # claude-haiku-4-5: $0.80/MTok input, $4/MTok output  (~10× cheaper than Sonnet)
    # claude-sonnet-4-6: $3/MTok input, $15/MTok output
    BULK_MODEL    = "claude-haiku-4-5-20251001"
    QUALITY_MODEL = "claude-sonnet-4-6"

    @property
    def MODEL(self) -> str:
        import os
        if os.environ.get("CLAUDE_BULK_MODE", "").lower() in ("1", "true", "yes"):
            return self.BULK_MODEL
        return self.QUALITY_MODEL

    def __init__(self):
        self.api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not self.api_key:
            logger.warning("ANTHROPIC_API_KEY not found; AI features disabled")
        if not ANTHROPIC_AVAILABLE:
            logger.warning("anthropic package not installed; AI features disabled")

    def _is_ready(self) -> bool:
        return bool(ANTHROPIC_AVAILABLE and self.api_key)

    async def _call_claude(self, user_prompt: str, max_tokens: int = 8192) -> str:
        """Call Claude API and return raw text."""
        if not self._is_ready():
            raise RuntimeError(
                "ANTHROPIC_API_KEY is not set or anthropic package not installed."
            )
        client = anthropic.AsyncAnthropic(api_key=self.api_key)
        message = await client.messages.create(
            model=self.MODEL,
            max_tokens=max_tokens,
            system=TRADE_SYSTEM_INSTRUCTION,
            messages=[{"role": "user", "content": user_prompt}],
            temperature=0.2,
        )
        return message.content[0].text

    @staticmethod
    def _extract_json(text: str) -> dict:
        """Extract JSON from Claude's response, handling markdown code fences."""
        # Strip markdown fences
        clean = re.sub(r"```(?:json)?\s*", "", text).replace("```", "").strip()
        # Try direct parse
        try:
            return json.loads(clean)
        except json.JSONDecodeError:
            pass
        # Find largest JSON object / array in text
        for pattern in [r"\{[\s\S]*\}", r"\[[\s\S]*\]"]:
            match = re.search(pattern, clean)
            if match:
                try:
                    return json.loads(match.group())
                except json.JSONDecodeError:
                    pass
        return {}

    @staticmethod
    def _resolve_iso3(name: str) -> Optional[str]:
        if not name:
            return None
        token = name.strip()
        # Already an ISO3 code? (e.g. Claude returns "NGA" or "CHN")
        if re.fullmatch(r"[A-Za-z]{3}", token):
            upper = token.upper()
            # Return the code itself so African-only / self-loop guards can act on it,
            # whether it is African (in AFRICAN_ISO3) or extra-African (e.g. CHN).
            if upper in AFRICAN_ISO3 or upper in COUNTRY_NAME_TO_ISO3.values():
                return upper
            return upper
        return COUNTRY_NAME_TO_ISO3.get(token.lower())

    @staticmethod
    def _add_legacy_aliases(opp: dict, mode: str) -> None:
        """
        Emit snake_case aliases alongside the camelCase schema so downstream
        consumers (TradeSankeyDiagram, ProductAnalysisView, integration tests)
        that read legacy field names keep working. Mutates opp in place.
        """
        product = opp.get("product") or {}
        opp.setdefault("product_name", product.get("name"))
        opp.setdefault("hs_code", product.get("hs6Code") or product.get("hs4Code"))

        # Common value/field aliases (only set when source value exists)
        def alias(dst, *src_keys):
            if opp.get(dst) is not None:
                return
            for k in src_keys:
                if opp.get(k) is not None:
                    opp[dst] = opp[k]
                    return

        alias("potential_partner", "potentialPartner")
        alias("potential_supplier", "potentialSupplier")
        alias("current_source", "currentSource")
        alias("tariff_reduction", "tariffReductionPotential")
        alias("rules_of_origin", "rulesOfOrigin")
        alias("lead_time_savings", "leadTimeSavings")
        alias("price_competitiveness", "priceCompetitiveness")

        if mode == "export":
            alias("potential_value_musd", "potentialTradeValue")
            alias("current_value_musd", "currentTradeValue")
        elif mode == "import":
            alias("substitution_potential_musd", "substitutionPotential")
            alias("import_value_musd", "currentImportValue")
        elif mode == "industrial":
            # Sankey reads target_markets (array) and estimated_output (string with a number)
            markets = opp.get("targetMarkets") or opp.get("target_markets")
            if markets is not None:
                opp.setdefault("target_markets", markets)
            opp.setdefault("output_product", product.get("name"))
            opp.setdefault("potential_value_musd", opp.get("potentialTradeValue"))
            pv = opp.get("potentialTradeValue")
            if pv is not None and opp.get("estimated_output") is None:
                # Carry the trade value so the Sankey extracts a meaningful flow magnitude
                opp["estimated_output"] = f"{pv} MUSD"
            ind = opp.get("industrialInput") or opp.get("industrial_input")
            if isinstance(ind, dict):
                opp.setdefault("industrial_input", {
                    "name": ind.get("name"),
                    "hs_code": ind.get("hs6Code") or ind.get("hs_code"),
                    "import_volume": ind.get("importVolume") or ind.get("import_volume"),
                })

    def _post_process_opportunities(
        self, opportunities: list, analyzed_country: str, mode: str
    ) -> list:
        """
        Apply anti-self-loop, directional forcing, and African-only filter,
        then emit legacy snake_case aliases for downstream consumers.
        """
        analyzed_iso3 = self._resolve_iso3(analyzed_country)
        cleaned = []
        for opp in opportunities:
            product = opp.get("product", {})
            # Ensure product wrapper
            if not isinstance(product, dict):
                product = {}
                opp["product"] = product

            if mode == "export" or mode == "industrial":
                partner = opp.get("potential_partner") or opp.get("potentialPartner")
                if not partner and mode == "industrial":
                    markets = opp.get("target_markets") or opp.get("targetMarkets") or []
                    partner = markets[0] if markets else None

                # Self-loop guard
                if partner:
                    partner_iso3 = self._resolve_iso3(partner)
                    if analyzed_iso3 and partner_iso3 and partner_iso3 == analyzed_iso3:
                        continue
                    # African-only filter
                    if partner_iso3 and partner_iso3 not in AFRICAN_ISO3:
                        continue

                # Directional forcing
                opp["exporting_country"] = analyzed_country

            elif mode == "import":
                supplier = opp.get("potential_supplier") or opp.get("potentialSupplier")
                if supplier:
                    supplier_iso3 = self._resolve_iso3(supplier)
                    if analyzed_iso3 and supplier_iso3 and supplier_iso3 == analyzed_iso3:
                        continue
                    if supplier_iso3 and supplier_iso3 not in AFRICAN_ISO3:
                        continue
                opp["importing_country"] = analyzed_country

            self._add_legacy_aliases(opp, mode)
            cleaned.append(opp)

        return cleaned

    # ── Trade Opportunities ────────────────────────────────────────────────────

    async def analyze_trade_opportunities(
        self,
        country_name: str,
        mode: str = "export",
        lang: str = "fr",
    ) -> Dict:
        if not self._is_ready():
            return {"error": "ANTHROPIC_API_KEY not configured", "opportunities": []}

        cache_params = {"country": country_name, "mode": mode, "lang": lang}
        cached = cache_service.get("claude_analysis", cache_params)
        if cached:
            logger.info(f"Cache HIT claude_analysis {country_name}/{mode}")
            cached["data_freshness"] = get_data_freshness(
                cached.get("_cache_metadata", {}).get("cached_at")
            )
            return cached

        lang_instr = "Réponds UNIQUEMENT en français." if lang == "fr" else "Respond ONLY in English."

        if mode == "export":
            prompt = f"""{lang_instr}

Analyze EXPORT opportunities for {country_name} within the AfCFTA framework.

Identify exactly 15 verified intra-African export opportunities where {country_name} has
a comparative advantage or demonstrated production surplus (RCA > 1 preferred).

For EACH opportunity return this EXACT JSON structure:
{{
  "product": {{
    "name": "Product name in {lang}",
    "hs2Code": "2-digit chapter code",
    "hs2Name": "Chapter name",
    "hs4Code": "4-digit heading code",
    "hs4Name": "Heading name",
    "hs6Code": "6-digit sub-heading code",
    "hs6Name": "Sub-heading name"
  }},
  "exportingCountry": "{country_name}",
  "potentialPartner": "African destination country (ISO3 or full name)",
  "currentSource": "Current dominant supplier for that partner (if substitution)",
  "rationale": "3-4 sentence strategic justification citing OEC/UNCTAD/IMF data with specific figures",
  "year": 2023,
  "potentialTradeValue": 0.0,
  "currentTradeValue": 0.0,
  "tariffReductionPotential": 0.0,
  "leadTimeSavings": 0,
  "priceCompetitiveness": 0.0,
  "rulesOfOrigin": "Specific AfCFTA RoO for this HS chapter",
  "sourceUrl": "OEC or UNCTAD reference URL or data citation"
}}

Wrap ALL 15 in this envelope:
{{
  "opportunities": [...15 items...],
  "summary": {{
    "total_opportunities": 15,
    "total_potential_value": 0.0,
    "top_sectors": ["sector1", "sector2", "sector3"],
    "data_quality": "verified|mixed|estimated"
  }},
  "expected_results": {{
    "scenario_3_years": {{
      "export_growth_percent": 0.0,
      "new_market_penetration": 0,
      "total_export_value_musd": 0.0,
      "key_markets": ["Market 1", "Market 2"]
    }},
    "scenario_5_years": {{
      "export_growth_percent": 0.0,
      "total_export_value_musd": 0.0,
      "afcfta_share_percent": 0.0,
      "diversification_index": 0.0
    }}
  }},
  "sources": ["OEC 2023", "UN Comtrade 2023", "IMF WEO Oct 2024", "UNCTAD"],
  "analysis_date": "2024-Q4"
}}"""

        elif mode == "import":
            prompt = f"""{lang_instr}

Analyze IMPORT substitution opportunities for {country_name} within the AfCFTA framework.

Identify exactly 15 strategic import needs for {country_name} that could be sourced from
other African countries under AfCFTA preferences, replacing current extra-African suppliers.

For EACH opportunity return this EXACT JSON structure:
{{
  "product": {{
    "name": "Product name in {lang}",
    "hs2Code": "2-digit chapter code",
    "hs2Name": "Chapter name",
    "hs4Code": "4-digit heading code",
    "hs4Name": "Heading name",
    "hs6Code": "6-digit sub-heading code",
    "hs6Name": "Sub-heading name"
  }},
  "importingCountry": "{country_name}",
  "potentialSupplier": "African supplier country with proven capacity",
  "currentSource": "Current non-African dominant supplier (e.g. China, EU, India)",
  "rationale": "3-4 sentence justification with import volume data from UNCTAD/OEC",
  "year": 2023,
  "currentImportValue": 0.0,
  "substitutionPotential": 0.0,
  "tariffReductionPotential": 0.0,
  "leadTimeSavings": 0,
  "priceCompetitiveness": 0.0,
  "rulesOfOrigin": "Specific AfCFTA RoO for this HS chapter",
  "sourceUrl": "OEC or UNCTAD reference"
}}

Wrap ALL 15 in this envelope:
{{
  "opportunities": [...15 items...],
  "summary": {{
    "total_opportunities": 15,
    "total_potential_value": 0.0,
    "top_sectors": ["sector1", "sector2", "sector3"],
    "data_quality": "verified|mixed|estimated"
  }},
  "expected_results": {{
    "scenario_3_years": {{
      "import_substitution_percent": 0.0,
      "savings_musd": 0.0,
      "new_african_suppliers": 0,
      "key_products": ["Product 1", "Product 2"]
    }},
    "scenario_5_years": {{
      "import_substitution_percent": 0.0,
      "total_savings_musd": 0.0,
      "supply_chain_resilience_score": 0.0
    }}
  }},
  "sources": ["OEC 2023", "UN Comtrade 2023", "IMF WEO Oct 2024", "UNCTAD"],
  "analysis_date": "2024-Q4"
}}"""

        else:  # industrial / value chain
            prompt = f"""{lang_instr}

Analyze VALUE CHAIN TRANSFORMATION opportunities for {country_name} within AfCFTA.

Map current imports of intermediate goods (inputs) to potential manufactured exports (outputs).
Use UNCTAD 2023-2024 industrial statistics and UNIDO data.

Identify exactly 15 transformation opportunities (input → output chains).

For EACH opportunity return this EXACT JSON structure:
{{
  "product": {{
    "name": "Finished product name (output) in {lang}",
    "hs2Code": "2-digit chapter (output product)",
    "hs2Name": "Chapter name (output)",
    "hs4Code": "4-digit heading (output)",
    "hs4Name": "Heading name (output)",
    "hs6Code": "6-digit sub-heading (output)",
    "hs6Name": "Sub-heading name (output)"
  }},
  "industrialInput": {{
    "name": "Input commodity/intermediate good imported",
    "hs6Code": "6-digit HS code of input",
    "hs6Name": "Sub-heading name of input",
    "importVolume": "Annual import volume (e.g. '45,000 MT' or '$120M MUSD')"
  }},
  "exportingCountry": "{country_name}",
  "targetMarkets": ["African country 1", "African country 2", "African country 3"],
  "valueAdditionLogic": "2-3 sentences explaining the industrial transformation logic",
  "estimatedProduction": "Realistic annual production estimate (e.g. '10,000 MT/year')",
  "potentialTradeValue": 0.0,
  "tariffReductionPotential": 0.0,
  "leadTimeSavings": 0,
  "priceCompetitiveness": 0.0,
  "rulesOfOrigin": "Specific AfCFTA RoO (value addition threshold or process rule)",
  "sourceUrl": "UNCTAD/UNIDO reference"
}}

Wrap ALL 15 in this envelope:
{{
  "opportunities": [...15 items...],
  "summary": {{
    "total_opportunities": 15,
    "total_potential_value": 0.0,
    "top_sectors": ["sector1", "sector2", "sector3"],
    "data_quality": "verified|mixed|estimated"
  }},
  "expected_results": {{
    "scenario_3_years": {{
      "export_growth_percent": 0.0,
      "new_jobs_created": 0,
      "industrial_value_added_musd": 0.0,
      "key_milestones": ["Milestone 1", "Milestone 2"]
    }},
    "scenario_5_years": {{
      "export_growth_percent": 0.0,
      "new_jobs_created": 0,
      "industrial_value_added_musd": 0.0,
      "afcfta_market_share_percent": 0.0
    }}
  }},
  "sources": ["UNCTAD 2023", "UNIDO 2023", "OEC 2023", "IMF WEO Oct 2024"],
  "analysis_date": "2024-Q4"
}}"""

        try:
            raw = await self._call_claude(prompt, max_tokens=8192)
            result = self._extract_json(raw)

            if not result:
                return {
                    "error": "Failed to parse Claude response",
                    "opportunities": [],
                    "raw": raw[:500],
                }

            # Ensure opportunities is always a list
            if "opportunities" not in result:
                result = {"opportunities": result if isinstance(result, list) else []}

            # Post-processing
            result["opportunities"] = self._post_process_opportunities(
                result.get("opportunities", []), country_name, mode
            )

            # Enrich with OEC trade data for validation & real numbers
            try:
                result["opportunities"] = await oec_data_service.enrich_opportunities(
                    result.get("opportunities", []), year=2023
                )
                result["oec_enrichment"] = True
            except Exception as e:
                logger.warning(f"OEC enrichment failed: {e}")
                result["oec_enrichment"] = False

            result["country"] = country_name
            result["mode"] = mode
            result["generated_by"] = f"Claude AI ({self.MODEL})"
            result["generated_at"] = datetime.now(timezone.utc).isoformat()
            result["data_freshness"] = get_data_freshness(None)

            cache_service.set("claude_analysis", cache_params, result, "claude_analysis")
            return result

        except Exception as e:
            logger.error(f"Error in Claude trade analysis: {e}", exc_info=True)
            return {"error": str(e), "opportunities": []}

    # ── Country Economic Profile ───────────────────────────────────────────────

    async def get_country_economic_profile(
        self, country_name: str, lang: str = "fr"
    ) -> Dict:
        if not self._is_ready():
            return {"error": "ANTHROPIC_API_KEY not configured"}

        cache_params = {"country": country_name, "lang": lang, "type": "profile"}
        cached = cache_service.get("claude_profile", cache_params)
        if cached:
            cached["data_freshness"] = get_data_freshness(
                cached.get("_cache_metadata", {}).get("cached_at")
            )
            return cached

        lang_instr = "Réponds en français." if lang == "fr" else "Respond in English."

        prompt = f"""{lang_instr}

Provide a comprehensive economic and trade profile for {country_name}.

Return this EXACT JSON structure:
{{
  "country_name": "{country_name}",
  "year": 2024,
  "economic_indicators": {{
    "gdp_billion_usd": 0.0,
    "gdp_growth_percent": 0.0,
    "inflation_percent": 0.0,
    "unemployment_percent": 0.0,
    "total_debt_percent_gdp": 0.0,
    "foreign_reserves_billion_usd": 0.0,
    "gold_reserves_tons": 0.0,
    "source": "IMF WEO October 2024"
  }},
  "development_indices": {{
    "hdi": 0.000,
    "hdi_world_rank": 0,
    "hdi_africa_rank": 0,
    "gai_score": null,
    "gai_world_rank": null,
    "gai_africa_rank": null,
    "gai_note": "GAI 2025 — The European House Ambrosetti"
  }},
  "trade_summary": {{
    "total_exports_musd": 0.0,
    "total_imports_musd": 0.0,
    "trade_balance_musd": 0.0,
    "intra_african_trade_percent": 0.0,
    "top_exports": [
      {{"product": "", "hs6Code": "", "value_musd": 0.0, "main_destination": ""}}
    ],
    "top_imports": [
      {{"product": "", "hs6Code": "", "value_musd": 0.0, "main_source": ""}}
    ],
    "top_export_partners": [{{"country": "", "value_musd": 0.0, "share_percent": 0.0}}],
    "top_import_partners": [{{"country": "", "value_musd": 0.0, "share_percent": 0.0}}],
    "source": "OEC 2022-2023 / UN Comtrade"
  }},
  "afcfta_readiness": {{
    "ratified": true,
    "tariff_elimination_schedule": "",
    "key_sectors_benefiting": [],
    "major_projects": []
  }},
  "sources": ["IMF WEO Oct 2024", "UNDP HDR 2023", "OEC 2023", "World Bank 2024"]
}}"""

        try:
            raw = await self._call_claude(prompt, max_tokens=4096)
            result = self._extract_json(raw)
            if not result:
                return {"error": "Failed to parse response", "raw": raw[:500]}

            # Normalize trade summary contract for MultiCountryComparison.jsx
            # (reads data.trade_summary) — accept legacy "trade_profile" too.
            ts = result.get("trade_summary") or result.pop("trade_profile", None)
            if isinstance(ts, dict):
                if "intra_african_trade_percent" not in ts and "intra_african_share_percent" in ts:
                    ts["intra_african_trade_percent"] = ts["intra_african_share_percent"]
                result["trade_summary"] = ts

            result["generated_by"] = f"Claude AI ({self.MODEL})"
            result["data_freshness"] = get_data_freshness(None)
            cache_service.set("claude_profile", cache_params, result, "claude_profile")
            return result

        except Exception as e:
            logger.error(f"Error in country profile: {e}", exc_info=True)
            return {"error": str(e)}

    # ── Product Analysis ──────────────────────────────────────────────────────

    async def analyze_product_by_hs_code(
        self, hs_code: str, lang: str = "fr"
    ) -> Dict:
        if not self._is_ready():
            return {"error": "ANTHROPIC_API_KEY not configured"}

        cache_params = {"hs_code": hs_code, "lang": lang}
        cached = cache_service.get("claude_product", cache_params)
        if cached:
            cached["data_freshness"] = get_data_freshness(
                cached.get("_cache_metadata", {}).get("cached_at")
            )
            return cached

        lang_instr = "Réponds en français." if lang == "fr" else "Respond in English."

        prompt = f"""{lang_instr}

Analyze the African trade landscape for HS code {hs_code}.

Provide full SH hierarchy and intra-African trade analysis.

Return this EXACT JSON structure:
{{
  "product": {{
    "hs6Code": "{hs_code.zfill(6) if len(hs_code) <= 6 else hs_code}",
    "hs6Name": "Sub-heading name",
    "hs4Code": "{hs_code[:4] if len(hs_code) >= 4 else hs_code}",
    "hs4Name": "Heading name",
    "hs2Code": "{hs_code[:2]}",
    "hs2Name": "Chapter name",
    "description": "Full product description in {lang}"
  }},
  "african_trade_summary": {{
    "total_african_exports_musd": 0.0,
    "total_african_imports_musd": 0.0,
    "intra_african_trade_musd": 0.0,
    "year": 2023
  }},
  "top_african_exporters": [
    {{"country": "", "iso3": "", "value_musd": 0.0, "share_percent": 0.0, "trend": "stable|growing|declining"}}
  ],
  "top_african_importers": [
    {{"country": "", "iso3": "", "value_musd": 0.0, "share_percent": 0.0, "main_source": ""}}
  ],
  "production_capacities": [
    {{"country": "", "iso3": "", "capacity": "", "notes": ""}}
  ],
  "market_share_trends": {{
    "fastest_growing_exporter": "",
    "largest_import_dependency": "",
    "afcfta_opportunity_score": 0.0,
    "notes": ""
  }},
  "substitutes": [
    {{"hs6Code": "", "name": "", "relationship": "substitute|complement|input"}}
  ],
  "technical_specs": {{
    "quality_standards": [],
    "phytosanitary_requirements": "",
    "packaging_standards": "",
    "key_certifications": []
  }},
  "sources": ["OEC 2023", "UN Comtrade 2023", "UNCTAD"]
}}"""

        try:
            raw = await self._call_claude(prompt, max_tokens=4096)
            result = self._extract_json(raw)
            if not result:
                return {"error": "Failed to parse response"}

            # Normalize field names for ProductAnalysisView.jsx:
            # exporters → export_value_musd, importers → import_value_musd,
            # product → snake_case hs2_code/hs2_name/hs4_code/hs4_name.
            for exp in result.get("top_african_exporters", []) or []:
                if isinstance(exp, dict) and "export_value_musd" not in exp:
                    exp["export_value_musd"] = exp.get("value_musd", 0)
            for imp in result.get("top_african_importers", []) or []:
                if isinstance(imp, dict) and "import_value_musd" not in imp:
                    imp["import_value_musd"] = imp.get("value_musd", 0)
            prod = result.get("product")
            if isinstance(prod, dict):
                prod.setdefault("hs2_code", prod.get("hs2Code"))
                prod.setdefault("hs2_name", prod.get("hs2Name"))
                prod.setdefault("hs4_code", prod.get("hs4Code"))
                prod.setdefault("hs4_name", prod.get("hs4Name"))

            result["generated_by"] = f"Claude AI ({self.MODEL})"
            result["data_freshness"] = get_data_freshness(None)
            cache_service.set("claude_product", cache_params, result, "claude_product")
            return result

        except Exception as e:
            logger.error(f"Error in product analysis: {e}", exc_info=True)
            return {"error": str(e)}

    # ── Trade Balance ─────────────────────────────────────────────────────────

    async def get_trade_balance_analysis(
        self, country_name: str, lang: str = "fr"
    ) -> Dict:
        if not self._is_ready():
            return {"error": "ANTHROPIC_API_KEY not configured"}

        cache_params = {"country": country_name, "lang": lang, "type": "balance"}
        cached = cache_service.get("claude_balance", cache_params)
        if cached:
            cached["data_freshness"] = get_data_freshness(
                cached.get("_cache_metadata", {}).get("cached_at")
            )
            return cached

        lang_instr = "Réponds en français." if lang == "fr" else "Respond in English."

        prompt = f"""{lang_instr}

Provide annual trade balance data for {country_name} from 2020 to 2024.
Use IMF WEO October 2024 data. Values in Million USD (MUSD).

Return this EXACT JSON structure with one entry per year, deduplicated:
{{
  "country": "{country_name}",
  "annual_data": [
    {{
      "year": 2020,
      "exports_musd": 0.0,
      "imports_musd": 0.0,
      "balance_musd": 0.0,
      "gdp_musd": 0.0,
      "trade_to_gdp_percent": 0.0
    }}
  ],
  "trend_analysis": {{
    "direction": "surplus|deficit|balanced",
    "trend": "improving|deteriorating|stable",
    "key_drivers": [],
    "outlook": ""
  }},
  "sources": ["IMF WEO October 2024", "World Bank"],
  "notes": ""
}}"""

        try:
            raw = await self._call_claude(prompt, max_tokens=3000)
            result = self._extract_json(raw)
            if not result:
                return {"error": "Failed to parse response"}

            # Deduplicate by year
            if "annual_data" in result:
                seen_years = set()
                deduped = []
                for entry in result["annual_data"]:
                    y = entry.get("year")
                    if y not in seen_years:
                        seen_years.add(y)
                        deduped.append(entry)
                result["annual_data"] = sorted(deduped, key=lambda x: x.get("year", 0))

            result["generated_by"] = f"Claude AI ({self.MODEL})"
            result["data_freshness"] = get_data_freshness(None)
            cache_service.set("claude_balance", cache_params, result, "claude_balance")
            return result

        except Exception as e:
            logger.error(f"Error in trade balance: {e}", exc_info=True)
            return {"error": str(e)}

    # ── Value Chains ──────────────────────────────────────────────────────────

    async def get_value_chains_analysis(
        self, sector: Optional[str] = None, lang: str = "fr"
    ) -> Dict:
        if not self._is_ready():
            return {"error": "ANTHROPIC_API_KEY not configured"}

        cache_params = {"sector": sector or "all", "lang": lang}
        cached = cache_service.get("claude_value_chains", cache_params)
        if cached:
            cached["data_freshness"] = get_data_freshness(
                cached.get("_cache_metadata", {}).get("cached_at")
            )
            return cached

        lang_instr = "Réponds en français." if lang == "fr" else "Respond in English."
        sector_focus = f"Focus specifically on the {sector} value chain." if sector else \
            "Cover 6 major value chains: coffee/cocoa, cotton/textiles, minerals, petroleum, automotive/assembly, and pharma/chemicals."

        prompt = f"""{lang_instr}

Analyze African value chains under AfCFTA. {sector_focus}

For each value chain provide:
{{
  "sector": "Sector name",
  "description": "Brief description in {lang}",
  "stages": [
    {{
      "stage_number": 1,
      "name": "Stage name",
      "hs6Codes": ["HS code 1", "HS code 2"],
      "description": "What happens at this stage",
      "leading_countries": ["Country1 (ISO3)", "Country2 (ISO3)"],
      "value_added_percent": 0.0,
      "bottlenecks": ["Bottleneck 1", "Bottleneck 2"]
    }}
  ],
  "top_producers": [
    {{"country": "", "iso3": "", "role": "raw_material|processor|manufacturer|exporter", "value_musd": 0.0}}
  ],
  "afcfta_opportunities": [
    {{"description": "", "potential_value_musd": 0.0, "beneficiary_countries": []}}
  ],
  "investment_needed_musd": 0.0,
  "intra_african_trade_potential_musd": 0.0,
  "sources": []
}}

Wrap in: {{"value_chains": [...], "overview": {{"total_potential_musd": 0.0, "key_bottlenecks": [], "priority_sectors": []}}}}"""

        try:
            raw = await self._call_claude(prompt, max_tokens=6000)
            result = self._extract_json(raw)
            if not result:
                return {"error": "Failed to parse response"}

            result["generated_by"] = f"Claude AI ({self.MODEL})"
            result["data_freshness"] = get_data_freshness(None)
            cache_service.set("claude_value_chains", cache_params, result, "claude_value_chains")
            return result

        except Exception as e:
            logger.error(f"Error in value chains: {e}", exc_info=True)
            return {"error": str(e)}

    # ── Country Comparison ────────────────────────────────────────────────────

    async def compare_countries(
        self, country_a: str, country_b: str, lang: str = "fr"
    ) -> Dict:
        if not self._is_ready():
            return {"error": "ANTHROPIC_API_KEY not configured"}

        cache_params = {"country_a": country_a, "country_b": country_b, "lang": lang}
        cached = cache_service.get("claude_comparison", cache_params)
        if cached:
            cached["data_freshness"] = get_data_freshness(
                cached.get("_cache_metadata", {}).get("cached_at")
            )
            return cached

        lang_instr = "Réponds en français." if lang == "fr" else "Respond in English."

        prompt = f"""{lang_instr}

Compare {country_a} and {country_b} as AfCFTA trade partners.
Use OEC 2023, IMF WEO Oct 2024, UNDP HDR 2023 data.

Return this EXACT JSON structure:
{{
  "country_a": "{country_a}",
  "country_b": "{country_b}",
  "bilateral_trade": {{
    "exports_a_to_b_musd": 0.0,
    "exports_b_to_a_musd": 0.0,
    "balance_musd": 0.0,
    "year": 2023,
    "main_products_a_to_b": [],
    "main_products_b_to_a": []
  }},
  "economic_comparison": {{
    "gdp_a_billion": 0.0,
    "gdp_b_billion": 0.0,
    "gdp_growth_a": 0.0,
    "gdp_growth_b": 0.0,
    "hdi_a": 0.0,
    "hdi_b": 0.0,
    "gai_score_a": null,
    "gai_score_b": null,
    "inflation_a": 0.0,
    "inflation_b": 0.0
  }},
  "trade_complementarity": {{
    "score": 0.0,
    "explanation": "",
    "a_can_supply_to_b": [{{"product": "", "hs6Code": "", "potential_musd": 0.0}}],
    "b_can_supply_to_a": [{{"product": "", "hs6Code": "", "potential_musd": 0.0}}]
  }},
  "afcfta_potential": {{
    "total_potential_musd": 0.0,
    "tariff_savings_musd": 0.0,
    "key_opportunities": [],
    "barriers": []
  }},
  "sources": ["OEC 2023", "IMF WEO Oct 2024", "UNDP HDR 2023", "WTO"]
}}"""

        try:
            raw = await self._call_claude(prompt, max_tokens=4096)
            result = self._extract_json(raw)
            if not result:
                return {"error": "Failed to parse response"}

            result["generated_by"] = f"Claude AI ({self.MODEL})"
            result["data_freshness"] = get_data_freshness(None)
            cache_service.set("claude_comparison", cache_params, result, "claude_comparison")
            return result

        except Exception as e:
            logger.error(f"Error in country comparison: {e}", exc_info=True)
            return {"error": str(e)}

    # ── Trade Summary (overview) ──────────────────────────────────────────────

    async def get_trade_summary(self, lang: str = "fr") -> Dict:
        if not self._is_ready():
            return {"error": "ANTHROPIC_API_KEY not configured"}

        cache_params = {"lang": lang}
        cached = cache_service.get("claude_summary", cache_params)
        if cached:
            cached["data_freshness"] = get_data_freshness(
                cached.get("_cache_metadata", {}).get("cached_at")
            )
            return cached

        lang_instr = "Réponds en français." if lang == "fr" else "Respond in English."

        prompt = f"""{lang_instr}

Provide a comprehensive overview of African trade under AfCFTA (2023-2024 data).

Return this JSON structure:
{{
  "overview": {{
    "total_african_gdp_trillion": 0.0,
    "intra_african_trade_percent": 0.0,
    "intra_african_trade_musd": 0.0,
    "afcfta_signatories": 54,
    "afcfta_ratifications": 0,
    "year": 2023
  }},
  "top_trading_countries": [
    {{"country": "", "iso3": "", "exports_musd": 0.0, "imports_musd": 0.0, "rank": 1}}
  ],
  "top_sectors": [
    {{"sector": "", "value_musd": 0.0, "growth_percent": 0.0, "key_countries": []}}
  ],
  "key_corridors": [
    {{"from": "", "to": "", "value_musd": 0.0, "main_products": []}}
  ],
  "afcfta_progress": {{
    "tariff_liberalization_percent": 0.0,
    "implementation_challenges": [],
    "success_stories": []
  }},
  "sources": ["UNCTAD 2023", "AfCFTA Secretariat", "AU Commission", "IMF WEO Oct 2024"]
}}"""

        try:
            raw = await self._call_claude(prompt, max_tokens=3000)
            result = self._extract_json(raw)
            if not result:
                return {"error": "Failed to parse response"}

            result["generated_by"] = f"Claude AI ({self.MODEL})"
            result["data_freshness"] = get_data_freshness(None)
            cache_service.set("claude_summary", cache_params, result, "claude_summary")
            return result

        except Exception as e:
            logger.error(f"Error in trade summary: {e}", exc_info=True)
            return {"error": str(e)}


# Singleton
claude_trade_service = ClaudeTradeService()
