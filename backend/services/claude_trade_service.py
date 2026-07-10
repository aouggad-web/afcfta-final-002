"""
Claude AI Trade Analysis Service
Replaces Google Gemini with Anthropic Claude API
Quality parity with AI Studio app — SH2/SH4/SH6, corrected GAI anchors, full trade schema
"""

import contextvars
import json
import logging
import os
import re
from datetime import datetime, timezone
from typing import Dict, Optional

from dotenv import load_dotenv

try:
    import anthropic

    ANTHROPIC_AVAILABLE = True
except ImportError:
    anthropic = None
    ANTHROPIC_AVAILABLE = False
    logging.warning("anthropic package not installed; AI features will be disabled")

from services import manufacturing_proxy_service, production_capacity_service
from services.oec_data_service import oec_data_service
from services.oec_trade_service import DEFAULT_YEAR as OEC_DEFAULT_YEAR
from services.oec_trade_service import oec_service
from services.redis_cache_service import cache_service, get_data_freshness

load_dotenv()

logger = logging.getLogger(__name__)

# Isolée par tâche asyncio (contrairement à un attribut d'instance) — voir
# ClaudeTradeService.last_model_used pour le rationnel complet.
_last_model_used_var: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar(
    "claude_last_model_used", default=None
)

# ── Valid African ISO3 codes (AU member states with trade data) ────────────────
AFRICAN_ISO3 = {
    "DZA",
    "AGO",
    "BEN",
    "BWA",
    "BFA",
    "BDI",
    "CMR",
    "CPV",
    "CAF",
    "TCD",
    "COM",
    "COG",
    "COD",
    "DJI",
    "EGY",
    "GNQ",
    "ERI",
    "SWZ",
    "ETH",
    "GAB",
    "GMB",
    "GHA",
    "GIN",
    "GNB",
    "CIV",
    "KEN",
    "LSO",
    "LBR",
    "LBY",
    "MDG",
    "MWI",
    "MLI",
    "MRT",
    "MUS",
    "MAR",
    "MOZ",
    "NAM",
    "NER",
    "NGA",
    "RWA",
    "STP",
    "SEN",
    "SLE",
    "SOM",
    "ZAF",
    "SSD",
    "SDN",
    "TZA",
    "TGO",
    "TUN",
    "UGA",
    "ZMB",
    "ZWE",
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
   - MAURITIUS (MUS): Small-island economy that IMPORTS ~75% of its consumption needs.
     Its garment/textile exports (HS 61/62) and refined-sugar exports (HS 1701) are
     processing/re-export activity on LARGELY IMPORTED inputs (fabric, yarn, raw sugar
     under EPZ/Freeport regimes) — NEVER present Mauritius as a "leading producer" or
     "top producer" of the raw material (raw cotton, raw sugarcane, etc.). It may be
     cited only as a processor/manufacturer/exporter of the finished good, explicitly
     labeled as such, never as the source of the primary commodity.
2. NEVER CONFUSE PRODUCER WITH EXPORTER/PROCESSOR (applies to every country, not just
   the flagged cases above): "top producer" / "leading producer" / "producteur principal"
   must reflect actual primary production (harvested/extracted volume), never export
   value, re-export volume, or processing/assembly activity on imported inputs. If you
   are not confident a country actually produces the raw material domestically, omit it
   from producer rankings rather than guess — a missing entry is safer than a wrong one.
3. HYDROCARBON BIAS (mandatory diversification):
   - DZA, AGO, NGA, LBY, GAB: max 2–3 hydrocarbon items then pivot to Agriculture,
     Manufacturing, Services. The non-oil economy is the analytical focus.
   - SDN: Post-secession — most oil fields are in South Sudan (SSD).
4. DATA INTEGRITY:
   - Only include products with verified trade flows > $0.5M MUSD.
   - If a product is a plausible major export but has no domestic production base,
     flag rationale with "suspected re-export or informal cross-border trade."
5. SMALL ISLAND STATES (SYC, COM, CPV, STP): Focus on fisheries, tourism services,
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
    "algeria": "DZA",
    "algérie": "DZA",
    "angola": "AGO",
    "benin": "BEN",
    "bénin": "BEN",
    "botswana": "BWA",
    "burkina faso": "BFA",
    "burundi": "BDI",
    "cameroon": "CMR",
    "cameroun": "CMR",
    "cabo verde": "CPV",
    "cape verde": "CPV",
    "central african republic": "CAF",
    "république centrafricaine": "CAF",
    "chad": "TCD",
    "tchad": "TCD",
    "comoros": "COM",
    "comores": "COM",
    "congo": "COG",
    "republic of congo": "COG",
    "congo-brazzaville": "COG",
    "democratic republic of congo": "COD",
    "drc": "COD",
    "rdc": "COD",
    "djibouti": "DJI",
    "egypt": "EGY",
    "égypte": "EGY",
    "equatorial guinea": "GNQ",
    "guinée équatoriale": "GNQ",
    "eritrea": "ERI",
    "érythrée": "ERI",
    "eswatini": "SWZ",
    "swaziland": "SWZ",
    "ethiopia": "ETH",
    "éthiopie": "ETH",
    "gabon": "GAB",
    "gambia": "GMB",
    "gambie": "GMB",
    "ghana": "GHA",
    "guinea": "GIN",
    "guinée": "GIN",
    "guinea-bissau": "GNB",
    "guinée-bissau": "GNB",
    "ivory coast": "CIV",
    "côte d'ivoire": "CIV",
    "cote d'ivoire": "CIV",
    "kenya": "KEN",
    "lesotho": "LSO",
    "liberia": "LBR",
    "libya": "LBY",
    "libye": "LBY",
    "madagascar": "MDG",
    "malawi": "MWI",
    "mali": "MLI",
    "mauritania": "MRT",
    "mauritanie": "MRT",
    "mauritius": "MUS",
    "île maurice": "MUS",
    "ile maurice": "MUS",
    "morocco": "MAR",
    "maroc": "MAR",
    "mozambique": "MOZ",
    "namibia": "NAM",
    "namibie": "NAM",
    "niger": "NER",
    "nigeria": "NGA",
    "rwanda": "RWA",
    "sao tome and principe": "STP",
    "são tomé-et-príncipe": "STP",
    "senegal": "SEN",
    "sénégal": "SEN",
    "sierra leone": "SLE",
    "somalia": "SOM",
    "somalie": "SOM",
    "south africa": "ZAF",
    "afrique du sud": "ZAF",
    "south sudan": "SSD",
    "soudan du sud": "SSD",
    "sudan": "SDN",
    "soudan": "SDN",
    "tanzania": "TZA",
    "tanzanie": "TZA",
    "togo": "TGO",
    "tunisia": "TUN",
    "tunisie": "TUN",
    "uganda": "UGA",
    "ouganda": "UGA",
    "zambia": "ZMB",
    "zambie": "ZMB",
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
    # claude-sonnet-5: dernier Sonnet — nettement meilleur sur l'analyse
    # structurée longue ; certains proxys (ex. clé universelle Emergent)
    # peuvent ne pas encore l'exposer, d'où le repli automatique dans
    # _call_claude sur QUALITY_FALLBACK_MODEL.
    BULK_MODEL = "claude-haiku-4-5-20251001"
    QUALITY_MODEL = "claude-sonnet-5"
    QUALITY_FALLBACK_MODEL = "claude-sonnet-4-6"

    # Modèles qui rejettent les paramètres d'échantillonnage non-défaut
    # (temperature/top_p/top_k) avec une erreur 400 — cf. doc de migration
    # Anthropic "Sonnet 5 — sampling parameters not accepted". Passer
    # temperature=0.2 à l'un de ces modèles casse CHAQUE appel qualité par
    # défaut (jamais juste un repli de passerelle), d'où l'omission
    # conditionnelle ci-dessous plutôt qu'un correctif au niveau du repli.
    _NO_CUSTOM_SAMPLING_MODELS = {
        "claude-sonnet-5",
        "claude-opus-4-8",
        "claude-opus-4-7",
        "claude-fable-5",
        "claude-mythos-5",
    }

    @property
    def MODEL(self) -> str:
        import os

        if os.environ.get("CLAUDE_BULK_MODE", "").lower() in ("1", "true", "yes"):
            return os.environ.get("CLAUDE_BULK_MODEL") or self.BULK_MODEL
        return os.environ.get("CLAUDE_QUALITY_MODEL") or self.QUALITY_MODEL

    def __init__(self):
        self.api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not self.api_key:
            logger.warning("ANTHROPIC_API_KEY not found; AI features disabled")
        if not ANTHROPIC_AVAILABLE:
            logger.warning("anthropic package not installed; AI features disabled")

    def _is_ready(self) -> bool:
        return bool(ANTHROPIC_AVAILABLE and self.api_key)

    @property
    def last_model_used(self) -> Optional[str]:
        """
        Modèle réellement utilisé au dernier appel (repli compris) — pour que
        generated_by reflète la vérité, pas l'intention.

        Stocké dans une contextvar (pas un attribut d'instance) : ce service
        est un singleton module-level partagé par toutes les requêtes
        concurrentes (voir `claude_trade_service` en bas de fichier) — un
        attribut `self.` serait une donnée par-requête mutée sur un objet
        partagé, corrompue par toute requête concurrente sur le même event
        loop. Une contextvar est isolée par tâche asyncio.
        """
        return _last_model_used_var.get()

    async def _call_claude(self, user_prompt: str, max_tokens: int = 8192) -> str:
        """Call Claude API and return raw text.

        Uses streaming when max_tokens is large (>10k) because Anthropic
        requires it for operations expected to take >10 minutes. Aggregates
        the stream into the final text so the caller sees the same contract.
        """
        if not self._is_ready():
            raise RuntimeError("ANTHROPIC_API_KEY is not set or anthropic package not installed.")
        # Réinitialisé à chaque appel : si tout échoue (y compris le repli),
        # un lecteur ne doit jamais voir le modèle d'un appel précédent.
        _last_model_used_var.set(None)
        client = anthropic.AsyncAnthropic(api_key=self.api_key)
        model = self.MODEL

        async def _create(m: str) -> str:
            common_kwargs = dict(
                model=m,
                max_tokens=max_tokens,
                system=TRADE_SYSTEM_INSTRUCTION,
                messages=[{"role": "user", "content": user_prompt}],
            )
            if m not in self._NO_CUSTOM_SAMPLING_MODELS:
                common_kwargs["temperature"] = 0.2
            # Threshold below which non-streaming is fine (< ~10-min SLA).
            # Sonnet-4-6 typically outputs ~50-80 tok/s; 10 min ≈ 30-48k tokens,
            # but the API enforces streaming already at 10k so we mirror that.
            if max_tokens >= 10_000:
                chunks: list[str] = []
                async with client.messages.stream(**common_kwargs) as stream:
                    async for text in stream.text_stream:
                        chunks.append(text)
                return "".join(chunks)
            message = await client.messages.create(**common_kwargs)
            return message.content[0].text

        try:
            text = await _create(model)
            _last_model_used_var.set(model)
        except (anthropic.NotFoundError, anthropic.BadRequestError) as e:
            # Un proxy/passerelle (ex. clé universelle Emergent) peut ne pas
            # exposer le modèle demandé, ou rejeter un paramètre de requête
            # qu'il ne supporte pas encore — replier sur un modèle largement
            # disponible plutôt que de désactiver la fonctionnalité.
            if model != self.QUALITY_FALLBACK_MODEL:
                logger.warning(
                    f"Model '{model}' rejected the request ({e}); "
                    f"falling back to '{self.QUALITY_FALLBACK_MODEL}'"
                )
                text = await _create(self.QUALITY_FALLBACK_MODEL)
                _last_model_used_var.set(self.QUALITY_FALLBACK_MODEL)
            else:
                raise
        return text

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
    def _salvage_truncated_list(text: str, key: str = "opportunities") -> list:
        """
        Récupère les objets complets d'un tableau JSON tronqué — cas d'une
        réponse coupée par max_tokens : plutôt que de tout perdre (l'ancien
        comportement retournait {}), on garde les N premières opportunités
        intégralement parsées et on abandonne seulement l'objet coupé.
        """
        clean = re.sub(r"```(?:json)?\s*", "", text).replace("```", "")
        anchor = re.search(rf'"{key}"\s*:\s*\[', clean)
        if anchor:
            idx = anchor.end()
        else:
            start = clean.find("[")
            if start < 0:
                return []
            idx = start + 1
        decoder = json.JSONDecoder()
        items = []
        while idx < len(clean):
            while idx < len(clean) and clean[idx] in " \t\r\n,":
                idx += 1
            if idx >= len(clean) or clean[idx] != "{":
                break
            try:
                obj, idx = decoder.raw_decode(clean, idx)
            except json.JSONDecodeError:
                break
            if isinstance(obj, dict):
                items.append(obj)
        return items

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
                opp.setdefault(
                    "industrial_input",
                    {
                        "name": ind.get("name"),
                        "hs_code": ind.get("hs6Code") or ind.get("hs_code"),
                        "import_volume": ind.get("importVolume") or ind.get("import_volume"),
                    },
                )

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

    async def _country_opportunity_grounding(
        self, country_name: str, iso3: Optional[str], mode: str
    ) -> tuple:
        """
        Construit le bloc de DONNÉES RÉELLES injecté dans le prompt
        d'analyze_trade_opportunities, et des stats de transparence.

        Sans ce bloc, le LLM choisit ses 15 opportunités de mémoire (chiffres
        approximatifs, produits que le pays ne produit/n'échange pas) et
        l'enrichissement post-génération (OEC/production/logistique) ne peut
        plus corriger une mauvaise sélection. Deux sources :
        - production réelle du pays (FAOSTAT/USGS/UNIDO — locale, toujours
          disponible) avec rang continental et part africaine ;
        - flux commerciaux réels du pays (OEC/UN Comtrade — réseau, meilleure
          année disponible), exports pour le mode export, imports pour le mode
          import, les deux pour le mode industrial.
        """
        sections = []
        stats = {"production_products": 0, "oec_flows": 0, "oec_year": None, "assembly_signals": 0}

        if iso3:
            try:
                profile = production_capacity_service.get_country_profile(iso3, top_n=20)
                if profile.get("available"):
                    lines = []
                    for p in profile["products"]:
                        caveat = (
                            " [PARTIAL COVERAGE — never present this rank as continental leadership]"
                            if p.get("coverage_caveat")
                            else ""
                        )
                        lines.append(
                            f"- {p['commodity']} (HS {p['hs_code']}, {p['institution']} {p['year']}): "
                            f"{p['value']:,.0f} {p['unit']}, continental rank {p['rank']}/"
                            f"{p['total_countries']}, African share {p['share_pct']}%{caveat}"
                        )
                    stats["production_products"] = len(lines)
                    sections.append(
                        f"VERIFIED PRODUCTION OF {country_name} "
                        "(FAOSTAT/USGS/UNIDO, latest year — real recorded output):\n"
                        + "\n".join(lines)
                    )
            except Exception as e:
                logger.warning(f"Production grounding failed for {iso3}: {e}")

        if iso3:
            flows_wanted = {
                "export": [("TOP REAL EXPORTS", oec_data_service.get_top_exports)],
                "import": [("TOP REAL IMPORTS", oec_data_service.get_top_imports)],
                "industrial": [
                    ("TOP REAL IMPORTS (candidate INPUTS)", oec_data_service.get_top_imports),
                    ("TOP REAL EXPORTS", oec_data_service.get_top_exports),
                ],
            }.get(mode, [])
            for title, fetch in flows_wanted:
                try:
                    rows, used_year = [], None
                    for year in (OEC_DEFAULT_YEAR, OEC_DEFAULT_YEAR - 1, 2022):
                        rows = await fetch(iso3, year=year, n=15)
                        if rows:
                            used_year = year
                            break
                    if not rows:
                        continue
                    lines = [
                        f"- {r['hs6Name']} (HS {r['hs6Code']}): {r['value_musd']:,.1f} MUSD"
                        for r in rows
                    ]
                    stats["oec_flows"] += len(lines)
                    # En mode industrial, deux flux sont interrogés (imports
                    # puis exports) ; ne fixer l'année qu'une fois — sinon
                    # elle reflète arbitrairement le dernier flux exécuté au
                    # lieu du premier (primaire) si leurs replis d'année
                    # respectifs divergent. `data_year` (année du prompt +
                    # enrich_opportunities) dépend de cette valeur.
                    if stats["oec_year"] is None:
                        stats["oec_year"] = used_year
                    sections.append(
                        f"{title} OF {country_name} (OEC/UN Comtrade {used_year}, MUSD):\n"
                        + "\n".join(lines)
                    )
                except Exception as e:
                    logger.warning(f"OEC grounding ({title}) failed for {iso3}: {e}")

        # Signal d'assemblage par proxy d'intrants (mode industrial uniquement) :
        # comble le trou de données pour les biens d'équipement (réfrigérateurs,
        # climatiseurs, téléviseurs...) que FAOSTAT/USGS/UNIDO ne mesurent pas.
        # Voir services/manufacturing_proxy_service.py pour la méthodologie.
        if iso3 and mode == "industrial":
            try:
                proxy_lines = []
                for chapter in manufacturing_proxy_service.list_proxy_chapters():
                    signal = await manufacturing_proxy_service.estimate_assembly_signal(
                        iso3, chapter["hs_code"]
                    )
                    if not signal.get("available"):
                        continue
                    for inp in signal["input_signals"]:
                        if inp.get("country_import_usd") is None:
                            continue
                        rank_info = inp["continental_ranking"]
                        rank_txt = (
                            f", African importer rank {rank_info['rank']}/{rank_info['total_countries']}"
                            if rank_info.get("available") and rank_info.get("rank")
                            else ""
                        )
                        proxy_lines.append(
                            f"- {signal['output_label']} (HS {signal['hs_code']}): "
                            f"imports ${inp['country_import_usd']:,.0f} of key input "
                            f"'{inp['input_label']}' (HS {inp['input_hs6']}, {inp['year']}){rank_txt}"
                        )
                if proxy_lines:
                    stats["assembly_signals"] = len(proxy_lines)
                    sections.append(
                        f"ASSEMBLY SIGNAL FOR {country_name} (indirect estimate from key-input "
                        "imports, OEC/UN Comtrade — NOT measured production; use only as a "
                        "possible transformation opportunity, never state a production rank "
                        "or output volume from this line):\n" + "\n".join(proxy_lines)
                    )
            except Exception as e:
                logger.warning(f"Assembly-signal grounding failed for {iso3}: {e}")

        return "\n\n".join(sections), stats

    @staticmethod
    def _grounding_rules(grounding_text: str, data_year: int) -> str:
        """Bloc prompt : données réelles + règles anti-fabrication."""
        return f"""
VERIFIED REAL DATA — GROUND THE ENTIRE ANALYSIS ON THIS (platform datasets):
{grounding_text or "(no platform data reachable for this country — say so in data_quality and mark every figure as an estimate)"}

STRICT DATA RULES:
1. SELECT opportunities primarily among products present in the data above (verified
   production or actual trade flows). A product absent from the data may appear only
   with an explicit justification in its rationale.
2. REUSE the figures above EXACTLY as given, citing source and year (e.g. "FAOSTAT
   {data_year}", "OEC/UN Comtrade"). NEVER invent precise statistics, market shares
   or values that are not in the data above.
3. Any quantity NOT derived from the data above must be an order-of-magnitude estimate
   explicitly marked as such in the rationale (e.g. "estimation" / "estimate").
4. An entry flagged [PARTIAL COVERAGE] must never be described as continental
   leadership or top-producer status.
5. sourceUrl: cite the dataset name and year from the data above — NEVER fabricate a URL.
"""

    async def _hs_code_grounding(self, hs_code: str) -> tuple:
        """
        Bloc DONNÉES RÉELLES pour analyze_product_by_hs_code : producteurs
        continentaux réels (FAOSTAT/USGS/UNIDO) et importateurs africains réels
        (OEC/UN Comtrade) pour ce code HS précis.

        Sans cet ancrage, le LLM invente un "producteur majeur" de mémoire pour
        des codes HS que nos jeux de données ne mesurent pour aucun pays africain
        (ex. médicaments HS 30, téléviseurs HS 8528) — exactement le défaut
        rapporté (un petit pays cité comme producteur majeur de médicaments et
        de téléviseurs, sans aucun ancrage réel).
        """
        sections = []
        real_producer_iso3: set = set()

        try:
            prod = production_capacity_service.get_continental_producers(hs_code)
            if prod.get("available"):
                top = prod["top_producers"]
                real_producer_iso3 = {p["country_iso3"] for p in top}
                names = ", ".join(
                    f"{p['country_name']} ({p['country_iso3']}, {p['share_pct']}%)" for p in top
                )
                # Certaines catégories manufacturières (UNIDO) n'ont qu'1-2 pays
                # africains ingérés (ex. électronique, pharma) — un rang/part
                # calculé dessus n'est PAS un leadership continental réel. Sans
                # relayer ce garde-fou dans le prompt, le LLM voit "Maurice
                # (MUS, 100.0%)" et affirme "producteur majeur" sur une
                # couverture partielle — exactement le défaut rapporté pour
                # les médicaments (HS 30) et l'électronique/TV (HS 8528).
                caveat = (
                    f" [PARTIAL COVERAGE — only {len(top)} African country/ies ingested for "
                    "this product; NEVER present as continental leadership]"
                    if prod.get("coverage_caveat")
                    else ""
                )
                sections.append(
                    f"REAL PRODUCTION for {prod['commodity']} (HS {hs_code}) "
                    f"[{prod['measure']}, {prod['source']['institution']} "
                    f"{prod['year']}]: {names}{caveat}"
                )
        except Exception as e:
            logger.warning(f"Production grounding failed for HS {hs_code}: {e}")

        try:
            for year in (OEC_DEFAULT_YEAR, OEC_DEFAULT_YEAR - 1, OEC_DEFAULT_YEAR - 2):
                importers = await oec_service.get_top_african_importers(hs_code, year)
                rows = importers.get("data") or []
                if rows:
                    names = ", ".join(
                        f"{r.get('country_name')} ({r.get('country_iso3')})" for r in rows[:10]
                    )
                    sections.append(
                        f"REAL AFRICAN IMPORTERS of HS {hs_code} (OEC/UN Comtrade {year}): {names}"
                    )
                    break
        except Exception as e:
            logger.warning(f"OEC importer grounding failed for HS {hs_code}: {e}")

        return "\n\n".join(sections), real_producer_iso3

    @staticmethod
    def _product_grounding_rules(grounding_text: str, has_real_production: bool) -> str:
        """Bloc prompt pour analyze_product_by_hs_code : données réelles + anti-fabrication."""
        no_data_clause = (
            ""
            if has_real_production
            else "\n7. NO verified production data exists in this platform's datasets "
            "(FAOSTAT/USGS/UNIDO) for this HS code, for any African country. Return an "
            'EMPTY "production_capacities" array and say so explicitly in '
            "market_share_trends.notes — do NOT invent a list of producing countries for "
            "a product with no verified production source."
        )
        return f"""
VERIFIED REAL DATA — GROUND THE ENTIRE ANALYSIS ON THIS (platform datasets):
{grounding_text or "(no platform data reachable for this HS code)"}

STRICT DATA RULES:
1. "production_capacities" must list ONLY countries present in the REAL PRODUCTION
   data above, if any. A country absent from it must NEVER be called a "producteur
   majeur" / "leading producer" of this good — omit it instead of guessing.
2. An entry flagged [PARTIAL COVERAGE] above (only 1-2 African countries ingested
   for that product in our datasets) must NEVER be described as continental
   leadership, "producteur majeur", or given a leadership percentage — state only
   that it is a known producer and that African coverage for this product is
   incomplete in our data (e.g. "no comprehensive African production data exists
   for this product; X is the only country recorded, not necessarily the leader").
3. "top_african_importers" should reuse the REAL AFRICAN IMPORTERS figures above
   where available, citing "OEC/UN Comtrade" and the year given.
4. A country in "top_african_exporters" that is NOT in the REAL PRODUCTION data
   above may only be described as a processing/re-export/trade hub, explicitly
   labeled as such — never presented as a producer of the underlying good.
5. Any quantity NOT derived from the data above must be an order-of-magnitude
   estimate explicitly marked as such.
6. sourceUrl: cite the dataset name/year from the data above — NEVER fabricate a URL.{no_data_clause}
"""

    @staticmethod
    def _filter_unverified_hs_producers(result: Dict, real_producer_iso3: set) -> int:
        """
        Garde-fou anti-hallucination pour analyze_product_by_hs_code (même principe
        que _filter_unverified_raw_producers pour les chaînes de valeur) : retire
        toute entrée "production_capacities" dont le pays n'apparaît pas dans les
        producteurs réels FAOSTAT/USGS/UNIDO pour ce code HS, plutôt que de
        l'afficher comme un rang de production non vérifié.
        """
        if not real_producer_iso3:
            return 0
        entries = result.get("production_capacities")
        if not isinstance(entries, list):
            return 0
        removed = 0
        kept = []
        for e in entries:
            iso3 = (e.get("iso3") or "").upper() if isinstance(e, dict) else None
            if iso3 and iso3 not in real_producer_iso3:
                removed += 1
                continue
            kept.append(e)
        result["production_capacities"] = kept
        return removed

    async def analyze_trade_opportunities(
        self,
        country_name: str,
        mode: str = "export",
        lang: str = "fr",
    ) -> Dict:
        if not self._is_ready():
            return {"error": "ANTHROPIC_API_KEY not configured", "opportunities": []}

        # "pv" = version du prompt : incrémentée à chaque évolution majeure du
        # prompt (ici v2 : ancrage données réelles + règles anti-fabrication)
        # pour invalider les analyses en cache générées avec l'ancien prompt.
        # "model" : CLAUDE_QUALITY_MODEL/CLAUDE_BULK_MODE changent la qualité
        # de sortie sans changer country/mode/lang/pv — sans cette clé, changer
        # de modèle pour améliorer la qualité ne se voit qu'après 90 jours
        # (TTL du cache claude_analysis) ou une invalidation manuelle.
        cache_params = {
            "country": country_name,
            "mode": mode,
            "lang": lang,
            "pv": 2,
            "model": self.MODEL,
        }
        # Stamp de version des données de production : pour les modes enrichis
        # (export/industrial), tout rebuild de production_africaine.json change
        # ce stamp et invalide automatiquement les analyses en cache.
        if mode in ("export", "industrial"):
            try:
                from production_data import get_production_data_version

                cache_params["pdv"] = get_production_data_version()
            except Exception as e:
                logger.debug(f"production data version unavailable: {e}")
        cached = cache_service.get("claude_analysis", cache_params)
        if cached:
            logger.info(f"Cache HIT claude_analysis {country_name}/{mode}")
            cached["data_freshness"] = get_data_freshness(
                cached.get("_cache_metadata", {}).get("cached_at")
            )
            return cached

        lang_instr = (
            "Réponds UNIQUEMENT en français." if lang == "fr" else "Respond ONLY in English."
        )

        analyzed_iso3 = self._resolve_iso3(country_name)
        grounding_text, grounding_stats = await self._country_opportunity_grounding(
            country_name, analyzed_iso3, mode
        )
        data_year = grounding_stats.get("oec_year") or OEC_DEFAULT_YEAR
        grounding_rules = self._grounding_rules(grounding_text, data_year)
        now = datetime.now(timezone.utc)
        analysis_quarter = f"{now.year}-Q{(now.month - 1) // 3 + 1}"

        if mode == "export":
            prompt = f"""{lang_instr}

Analyze EXPORT opportunities for {country_name} within the AfCFTA framework.
{grounding_rules}
Identify exactly 15 verified intra-African export opportunities where {country_name} has
a comparative advantage or demonstrated production surplus (RCA > 1 preferred) —
grounded in the verified production and export data above.

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
  "year": {data_year},
  "potentialTradeValue": 0.0,
  "currentTradeValue": 0.0,
  "tariffReductionPotential": 0.0,
  "leadTimeSavings": 0,
  "priceCompetitiveness": 0.0,
  "rulesOfOrigin": "Specific AfCFTA RoO for this HS chapter",
  "sourceUrl": "OEC or UNCTAD reference URL or data citation",
  "entryStrategy": {{
    "quickWins": ["Concrete action 1 (3–6 months)", "Concrete action 2"],
    "keyBarriers": ["Main barrier 1", "Main barrier 2"],
    "certifications": ["Required certification or standard"],
    "priorityActions": ["Strategic step 1", "Strategic step 2", "Strategic step 3"],
    "timelineMonths": 18
  }}
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
  "analysis_date": "{analysis_quarter}"
}}"""

        elif mode == "import":
            prompt = f"""{lang_instr}

Analyze IMPORT substitution opportunities for {country_name} within the AfCFTA framework.
{grounding_rules}
Identify exactly 15 strategic import needs for {country_name} that could be sourced from
other African countries under AfCFTA preferences, replacing current extra-African suppliers —
selected primarily among the verified imports listed above.

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
  "year": {data_year},
  "currentImportValue": 0.0,
  "substitutionPotential": 0.0,
  "tariffReductionPotential": 0.0,
  "leadTimeSavings": 0,
  "priceCompetitiveness": 0.0,
  "rulesOfOrigin": "Specific AfCFTA RoO for this HS chapter",
  "sourceUrl": "OEC or UNCTAD reference",
  "entryStrategy": {{
    "quickWins": ["Immediate sourcing action 1 (0–3 months)", "Pilot procurement action 2"],
    "keyBarriers": ["Supply chain barrier 1", "Quality standard barrier 2"],
    "certifications": ["Required certification for import"],
    "priorityActions": ["Strategic sourcing step 1", "Step 2", "Step 3"],
    "timelineMonths": 12
  }}
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
  "analysis_date": "{analysis_quarter}"
}}"""

        else:  # industrial / value chain
            prompt = f"""{lang_instr}

Analyze VALUE CHAIN TRANSFORMATION opportunities for {country_name} within AfCFTA.
{grounding_rules}
Map current imports of intermediate goods (inputs) to potential manufactured exports (outputs),
anchored on the verified imports (candidate inputs) and production capacities above.

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
  "sourceUrl": "UNCTAD/UNIDO reference",
  "entryStrategy": {{
    "quickWins": ["Pilot production line action (0–6 months)", "First export contract action"],
    "keyBarriers": ["Industrial capacity barrier", "Quality certification barrier"],
    "certifications": ["ISO standard or sector-specific certification required"],
    "priorityActions": ["Investment step 1", "Capacity building step 2", "Market entry step 3"],
    "timelineMonths": 24
  }}
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
  "analysis_date": "{analysis_quarter}"
}}"""

        try:
            # 15 opportunités détaillées ≈ 9-12k tokens de JSON : 8192 tronquait
            # régulièrement la réponse (perte totale ou partielle des résultats).
            raw = await self._call_claude(prompt, max_tokens=16000)
            result = self._extract_json(raw)

            # Réponse tronquée malgré tout : récupérer les opportunités
            # complètes plutôt que de tout jeter. `result` peut être une
            # list (Claude a renvoyé un tableau JSON nu au lieu de l'enveloppe
            # {"opportunities": [...]}) — `.get()` n'existe pas dessus.
            if not result or (isinstance(result, dict) and not result.get("opportunities")):
                salvaged = self._salvage_truncated_list(raw)
                if salvaged:
                    if not isinstance(result, dict) or not result:
                        result = {}
                    result["opportunities"] = salvaged
                    result["truncated_response_salvaged"] = True
                    logger.warning(
                        f"Claude response truncated for {country_name}/{mode}; "
                        f"salvaged {len(salvaged)} complete opportunities"
                    )

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
                    result.get("opportunities", []), year=data_year
                )
                result["oec_enrichment"] = True
            except Exception as e:
                logger.warning(f"OEC enrichment failed: {e}")
                result["oec_enrichment"] = False

            # Enrich with real production capacities (FAO / USGS / UNIDO) for the
            # analyzed country — grounds each opportunity in verifiable output data
            # and African-integration scenarios. Relevant in export & industrial
            # modes where the analyzed country is the producer.
            try:
                analyzed_iso3 = self._resolve_iso3(country_name)
                if analyzed_iso3 and mode in ("export", "industrial"):
                    result["opportunities"] = production_capacity_service.enrich_opportunities(
                        result.get("opportunities", []), analyzed_iso3
                    )
                    result["production_enrichment"] = True
                else:
                    result["production_enrichment"] = False
            except Exception as e:
                logger.warning(f"Production capacity enrichment failed: {e}")
                result["production_enrichment"] = False

            # Enrich with a real logistics profile (multimodal freight cost +
            # free zones) between the analyzed country and each opportunity's
            # partner — same adapter as the Reports module
            # (services/logistics_opportunity_adapter.py). Direction follows
            # the opportunity's own trade direction: export/industrial =
            # analyzed country → partner ; import = supplier → analyzed
            # country.
            try:
                from services import shipment_estimator
                from services.logistics_opportunity_adapter import (
                    get_logistics_profile,
                    summarize_logistics_accessibility,
                )

                analyzed_iso3 = self._resolve_iso3(country_name)
                logistics_ok = 0
                if analyzed_iso3:
                    for opp in result.get("opportunities", []):
                        if mode == "import":
                            partner_name = opp.get("potential_supplier") or opp.get(
                                "potentialSupplier"
                            )
                        else:
                            partner_name = opp.get("potential_partner") or opp.get(
                                "potentialPartner"
                            )
                        partner_iso3 = self._resolve_iso3(partner_name) if partner_name else None
                        if not partner_iso3:
                            continue
                        origin_iso3, destination_iso3 = (
                            (partner_iso3, analyzed_iso3)
                            if mode == "import"
                            else (analyzed_iso3, partner_iso3)
                        )

                        # Dimensionnement conteneur : potentialTradeValue est en
                        # MILLIONS de USD (cf. schéma du prompt) — jamais un seul
                        # conteneur 20' pour une opportunité de plusieurs M$
                        # (même correctif que S1/S2/S4 du module Rapports).
                        hs6 = (opp.get("product") or {}).get("hs6Code", "")
                        value_musd = opp.get("potentialTradeValue")
                        shipment = (
                            shipment_estimator.estimate_shipment(float(value_musd) * 1_000_000, hs6)
                            if value_musd
                            else {"available": False}
                        )
                        if shipment.get("available"):
                            container_type = shipment["container_type"]
                            one_container_kg = min(
                                float(shipment["weight_kg"]),
                                float(shipment["container_capacity_kg"]),
                            )
                            profile = get_logistics_profile(
                                origin_iso3,
                                destination_iso3,
                                one_container_kg,
                                container_type=container_type,
                            )
                        else:
                            profile = get_logistics_profile(origin_iso3, destination_iso3)

                        if profile["freight"].get("available"):
                            n_containers = (
                                max(1, int(shipment["containers_needed"]))
                                if shipment.get("available")
                                else 1
                            )
                            per_container = profile.get("best_operational_cost_usd")
                            opp["logistics"] = {
                                "available": True,
                                "best_operational_cost_usd": per_container,
                                "containers_needed": n_containers,
                                "container_type": shipment.get("container_type"),
                                "total_freight_usd": (
                                    round(per_container * n_containers, 2)
                                    if per_container is not None
                                    else None
                                ),
                                "estimated_weight_kg": shipment.get("weight_kg"),
                                "accessibility_index": summarize_logistics_accessibility(
                                    profile
                                ).get("index"),
                                "free_zones_at_destination": [
                                    z.get("name")
                                    for z in profile["free_zones"].get("zones", [])[:3]
                                ],
                            }
                            logistics_ok += 1
                        else:
                            opp["logistics"] = {"available": False}
                result["logistics_enrichment"] = logistics_ok > 0
            except Exception as e:
                logger.warning(f"Logistics enrichment failed: {e}")
                result["logistics_enrichment"] = False

            result["country"] = country_name
            result["mode"] = mode
            # Transparence : sur quelles données réelles le prompt était ancré
            result["grounding"] = {
                **grounding_stats,
                "grounded": bool(
                    grounding_stats.get("production_products") or grounding_stats.get("oec_flows")
                ),
            }
            result["generated_by"] = f"Claude AI ({self.last_model_used or self.MODEL})"
            result["generated_at"] = datetime.now(timezone.utc).isoformat()
            result["data_freshness"] = get_data_freshness(None)

            cache_service.set("claude_analysis", cache_params, result, "claude_analysis")
            return result

        except Exception as e:
            logger.error(f"Error in Claude trade analysis: {e}", exc_info=True)
            return {"error": str(e), "opportunities": []}

    # ── Country Economic Profile ───────────────────────────────────────────────

    async def get_country_economic_profile(self, country_name: str, lang: str = "fr") -> Dict:
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

            result["generated_by"] = f"Claude AI ({self.last_model_used or self.MODEL})"
            result["data_freshness"] = get_data_freshness(None)
            cache_service.set("claude_profile", cache_params, result, "claude_profile")
            return result

        except Exception as e:
            logger.error(f"Error in country profile: {e}", exc_info=True)
            return {"error": str(e)}

    # ── Product Analysis ──────────────────────────────────────────────────────

    async def analyze_product_by_hs_code(self, hs_code: str, lang: str = "fr") -> Dict:
        if not self._is_ready():
            return {"error": "ANTHROPIC_API_KEY not configured"}

        # "pv" = version du prompt : v2 ajoute l'ancrage sur données réelles
        # (production_capacity_service + OEC) et les règles anti-fabrication —
        # invalide les analyses en cache générées avec l'ancien prompt non ancré.
        cache_params = {"hs_code": hs_code, "lang": lang, "pv": 2}
        cached = cache_service.get("claude_product", cache_params)
        if cached:
            cached["data_freshness"] = get_data_freshness(
                cached.get("_cache_metadata", {}).get("cached_at")
            )
            return cached

        lang_instr = "Réponds en français." if lang == "fr" else "Respond in English."

        grounding_text, real_producer_iso3 = await self._hs_code_grounding(hs_code)
        grounding_rules = self._product_grounding_rules(grounding_text, bool(real_producer_iso3))

        prompt = f"""{lang_instr}

Analyze the African trade landscape for HS code {hs_code}.
{grounding_rules}
Provide full SH hierarchy and intra-African trade analysis, grounded in the
verified data above.

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

            filtered_count = self._filter_unverified_hs_producers(result, real_producer_iso3)
            if filtered_count:
                result["unverified_producers_filtered"] = filtered_count

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

            result["generated_by"] = f"Claude AI ({self.last_model_used or self.MODEL})"
            result["data_freshness"] = get_data_freshness(None)
            cache_service.set("claude_product", cache_params, result, "claude_product")
            return result

        except Exception as e:
            logger.error(f"Error in product analysis: {e}", exc_info=True)
            return {"error": str(e)}

    # ── Trade Balance ─────────────────────────────────────────────────────────

    async def get_trade_balance_analysis(self, country_name: str, lang: str = "fr") -> Dict:
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

            result["generated_by"] = f"Claude AI ({self.last_model_used or self.MODEL})"
            result["data_freshness"] = get_data_freshness(None)
            cache_service.set("claude_balance", cache_params, result, "claude_balance")
            return result

        except Exception as e:
            logger.error(f"Error in trade balance: {e}", exc_info=True)
            return {"error": str(e)}

    # ── Value Chains ──────────────────────────────────────────────────────────

    # Codes HS représentatifs par secteur, utilisés pour ancrer le prompt sur
    # des producteurs RÉELS (FAOSTAT/USGS/UNIDO, via production_capacity_service)
    # avant de laisser le LLM générer sa propre analyse. Sans cet ancrage, le
    # LLM confond régulièrement "pays exportateur/hub de réexport" (ex. Maurice
    # — zone franche textile/sucre, qui importe ~75% de ses besoins) avec
    # "producteur principal" de matière première.
    _SECTOR_HS_SEEDS = {
        "coffee/cocoa": ["0901", "1801"],
        "cotton/textiles": ["5201", "61"],
        "minerals": ["7108", "2601", "7403", "8105"],
        "petroleum": ["2709", "2711"],
        "automotive/assembly": ["87"],
        "pharma/chemicals": ["30", "28"],
    }

    # Seuls l'agriculture (FAOSTAT) et les mines/hydrocarbures (USGS) mesurent
    # une production de MATIÈRE PREMIÈRE. Le dataset "manufacturing" (UNIDO)
    # mesure une valeur ajoutée de TRANSFORMATION — un pays qui y figure (ex.
    # Maurice pour la confection, HS 61) est un vrai transformateur, mais ça
    # ne prouve RIEN sur la production de la matière première en amont (coton
    # brut). Mélanger les deux ferait passer, à tort, un pays "manufacturing"
    # comme vérifié pour un rôle "raw_material".
    _RAW_MATERIAL_DATASETS = {"agri", "mining"}

    def _real_producers_grounding(self, sector: Optional[str]) -> tuple:
        """
        Construit (a) un bloc texte listant les producteurs RÉELS (FAOSTAT/USGS/
        UNIDO) pour les secteurs concernés et (b) l'ensemble des ISO3 confirmés
        producteurs de MATIÈRE PREMIÈRE (agri/mining uniquement — voir
        _RAW_MATERIAL_DATASETS) — pour ancrer puis vérifier la réponse du LLM.
        """
        if sector:
            sector_lower = sector.lower()
            keys = [
                k
                for k in self._SECTOR_HS_SEEDS
                if any(part in sector_lower for part in k.split("/"))
            ] or list(self._SECTOR_HS_SEEDS)
        else:
            keys = list(self._SECTOR_HS_SEEDS)

        lines = []
        real_raw_material_iso3 = set()
        seen_commodities = set()
        for key in keys:
            for hs in self._SECTOR_HS_SEEDS[key]:
                data = production_capacity_service.get_continental_producers(hs)
                if not data.get("available"):
                    continue
                commodity = data["commodity"]
                if commodity in seen_commodities:
                    continue
                seen_commodities.add(commodity)
                top = data["top_producers"][:5]
                if not top:
                    continue
                names = ", ".join(
                    f"{p['country_name']} ({p['country_iso3']}, {p['share_pct']}%)" for p in top
                )
                lines.append(
                    f"- {commodity} [{data['measure']}, {data['source']['institution']} "
                    f"{data['year']}] : {names}"
                )
                if data["dimension"] in self._RAW_MATERIAL_DATASETS:
                    real_raw_material_iso3.update(p["country_iso3"] for p in top)
        return "\n".join(lines), real_raw_material_iso3

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
        sector_focus = (
            f"Focus specifically on the {sector} value chain."
            if sector
            else "Cover 6 major value chains: coffee/cocoa, cotton/textiles, minerals, petroleum, automotive/assembly, and pharma/chemicals."
        )

        grounding_block, real_raw_material_iso3 = self._real_producers_grounding(sector)

        prompt = f"""{lang_instr}

Analyze African value chains under AfCFTA. {sector_focus}

REAL PRODUCTION DATA (FAOSTAT / USGS / UNIDO, latest year, top continental producers) —
this is the ONLY valid source for "leading_countries" of a raw-material/extraction
stage, and for any "top_producers" entry tagged role="raw_material":
{grounding_block or "(no matching dataset)"}

STRICT RULE: a country absent from the list above must NEVER be presented as a
"raw_material" producer, a "leading_country" of an extraction/cultivation stage, or
a "principal producer" — even if it is a well-known trade/logistics hub (e.g.
Mauritius, Djibouti, UAE-style free zones that re-export or process imported goods).
Such a country may only be tagged role="processor" or role="exporter", reflecting
that it transforms or re-exports goods it largely imports, never that it produces
the raw material itself.

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

Wrap in: {{"value_chains": [...], "overview": {{"total_potential_musd": 0.0, "key_bottlenecks": [], "priority_sectors": []}}}}

IMPORTANT: Return ONLY the raw JSON (no markdown fences, no prose before/after).
Keep descriptions concise (≤2 sentences each). Each stage may contain the specified
fields ONLY — no extra keys like "keyProducers", "dataSource", "valueCapture", etc.
This keeps the payload compact and parseable."""

        try:
            # 6 chaînes de valeur complètes (étapes + producteurs + opportunités)
            # dépassaient régulièrement 6000 tokens → réponse tronquée. Sonnet
            # supporte jusqu'à 64k tokens de sortie ; 32000 couvre confortablement
            # le schéma imbriqué complet même pour des réponses françaises verbeuses
            # (mesuré ~12k tokens de sortie pour 6 secteurs × schéma complet).
            raw = await self._call_claude(prompt, max_tokens=32000)
            result = self._extract_json(raw)
            if not result:
                return {"error": "Failed to parse response"}

            filtered_count = self._filter_unverified_raw_producers(result, real_raw_material_iso3)

            result["generated_by"] = f"Claude AI ({self.last_model_used or self.MODEL})"
            result["data_freshness"] = get_data_freshness(None)
            if filtered_count:
                result["unverified_producers_filtered"] = filtered_count
            cache_service.set("claude_value_chains", cache_params, result, "claude_value_chains")
            return result

        except Exception as e:
            logger.error(f"Error in value chains: {e}", exc_info=True)
            return {"error": str(e)}

    @staticmethod
    def _filter_unverified_raw_producers(result: Dict, real_raw_material_iso3: set) -> int:
        """
        Garde-fou anti-hallucination : malgré l'ancrage du prompt, un LLM peut
        encore taguer role="raw_material" un pays qui n'est en réalité qu'un
        hub de transformation/réexport (ex. Maurice, ~75% de ses besoins
        importés). Toute entrée "top_producers" en role="raw_material" dont le
        pays n'apparaît pas dans les données de production réelles (FAOSTAT/
        USGS/UNIDO) est supprimée plutôt qu'affichée comme non vérifiée — pas
        de reclassement automatique en "exporter", qui serait lui aussi une
        affirmation non sourcée. Ne touche jamais aux rôles processor/
        manufacturer/exporter, hors du champ de vérification par production
        primaire.
        """
        if not real_raw_material_iso3:
            return 0
        removed = 0
        for chain in result.get("value_chains", []) or []:
            if not isinstance(chain, dict):
                continue
            producers = chain.get("top_producers")
            if not isinstance(producers, list):
                continue
            kept = []
            for p in producers:
                if (
                    isinstance(p, dict)
                    and p.get("role") == "raw_material"
                    and p.get("iso3") not in real_raw_material_iso3
                ):
                    removed += 1
                    continue
                kept.append(p)
            chain["top_producers"] = kept
        return removed

    # ── Country Comparison ────────────────────────────────────────────────────

    def _pairwise_production_grounding(
        self, country_a: str, iso3_a: Optional[str], country_b: str, iso3_b: Optional[str]
    ) -> str:
        """
        Bloc DONNÉES RÉELLES pour compare_countries : ce que chaque pays produit
        réellement (FAOSTAT/USGS/UNIDO), pour empêcher "a_can_supply_to_b" /
        "b_can_supply_to_a" de citer un produit sans aucune base de production
        dans le pays concerné (le même défaut que pour un code HS isolé, mais
        ici pour la vue comparaison de deux pays).
        """
        sections = []
        for name, iso3 in ((country_a, iso3_a), (country_b, iso3_b)):
            if not iso3:
                continue
            try:
                profile = production_capacity_service.get_country_profile(iso3, top_n=15)
                if profile.get("available"):
                    lines = [
                        f"- {p['commodity']} (HS {p['hs_code']}, {p['institution']} {p['year']}): "
                        f"continental rank {p['rank']}/{p['total_countries']}"
                        for p in profile["products"]
                    ]
                    sections.append(
                        f"VERIFIED PRODUCTION OF {name} (FAOSTAT/USGS/UNIDO, real recorded "
                        "output):\n" + "\n".join(lines)
                    )
            except Exception as e:
                logger.warning(f"Production grounding failed for {iso3}: {e}")
        return "\n\n".join(sections)

    async def compare_countries(self, country_a: str, country_b: str, lang: str = "fr") -> Dict:
        if not self._is_ready():
            return {"error": "ANTHROPIC_API_KEY not configured"}

        # "pv" = version du prompt : v2 ajoute l'ancrage sur la production réelle
        # de chaque pays et les règles anti-fabrication — invalide les
        # comparaisons en cache générées avec l'ancien prompt non ancré.
        cache_params = {"country_a": country_a, "country_b": country_b, "lang": lang, "pv": 2}
        cached = cache_service.get("claude_comparison", cache_params)
        if cached:
            cached["data_freshness"] = get_data_freshness(
                cached.get("_cache_metadata", {}).get("cached_at")
            )
            return cached

        lang_instr = "Réponds en français." if lang == "fr" else "Respond in English."

        iso3_a = self._resolve_iso3(country_a)
        iso3_b = self._resolve_iso3(country_b)
        grounding_text = self._pairwise_production_grounding(country_a, iso3_a, country_b, iso3_b)
        grounding_rules = f"""
VERIFIED REAL DATA — GROUND "a_can_supply_to_b" / "b_can_supply_to_a" ON THIS:
{grounding_text or "(no platform production data reachable for these countries)"}

STRICT DATA RULES:
1. "a_can_supply_to_b" must list products {country_a} demonstrably produces (per
   the data above, or an uncontested, well-known comparative advantage) — never a
   product with no plausible production base in {country_a}. Same rule for
   "b_can_supply_to_a" with {country_b}.
2. A product not present in the data above must be presented as an estimate, never
   as a specific rank or "leading producer" claim.
3. If neither country has verified production data for a plausible product,
   explain that in trade_complementarity.explanation rather than inventing figures.
"""

        prompt = f"""{lang_instr}

Compare {country_a} and {country_b} as AfCFTA trade partners.
Use OEC 2023, IMF WEO Oct 2024, UNDP HDR 2023 data.
{grounding_rules}

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

            result["generated_by"] = f"Claude AI ({self.last_model_used or self.MODEL})"
            result["data_freshness"] = get_data_freshness(None)
            cache_service.set("claude_comparison", cache_params, result, "claude_comparison")
            return result

        except Exception as e:
            logger.error(f"Error in country comparison: {e}", exc_info=True)
            return {"error": str(e)}


# Singleton
claude_trade_service = ClaudeTradeService()
