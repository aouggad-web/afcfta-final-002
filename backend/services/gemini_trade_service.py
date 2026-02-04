"""
Gemini Trade Analysis Service
Uses Google Gemini via Emergent LLM Key for intelligent trade analysis
IMPROVED: Based on AI Studio app prompts for better data quality
"""
import os
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from dotenv import load_dotenv

from emergentintegrations.llm.chat import LlmChat, UserMessage

load_dotenv()

logger = logging.getLogger(__name__)

# System instruction - IMPROVED from AI Studio app
TRADE_SYSTEM_INSTRUCTION = """
You are a senior AfCFTA trade economist and industrial data analyst.

SOURCES & AUTHORITY:
Prioritize data from: IMF (FMI), World Bank (BM), UNCTAD, WTO (OMC), OEC, and WCO (OMD).

METHODOLOGY:
1. EXPORT MODE: Focus on COMPARATIVE ADVANTAGE. What does the country currently produce and export well?
2. IMPORT MODE: Focus on CONSUMPTION & INDUSTRIAL NEEDS. What does the country lack?
3. INDUSTRIAL MODE (Value Chain): Use "Transformation Logic". Analyze IMPORTS of intermediate goods (Inputs) to forecast CAPACITY to EXPORT finished goods (Outputs).

DATA SANITIZATION RULES (CRITICAL):
1. FLAGGING & RE-EXPORTS: 
   - FOR LIBERIA (LBR): EXCLUDE HS Code 89 (Ships/Boats). These are "Flag of Convenience" registrations, not real industrial trade.
   - FOR DJIBOUTI/TOGO: Distinguish between TRANSIT trade to hinterland (Eth/BF/Niger) and local economy.
2. HYDROCARBONS: For Algeria/Angola/Nigeria, acknowledge oil/gas but prioritize NON-OIL diversification opportunities (Agriculture, Manufacturing).
3. DATA INTEGRITY: Use verified stats (IMF/UNCTAD). If data implies huge exports of a product not produced locally (e.g., Electronics from Benin), flag as Re-export or informal trade.

RULES:
1. GAI INDEX (CRITICAL): Use "The European House - Ambrosetti" Global Attractiveness Index.
   - **DO NOT DEFAULT TO 30**. A score of 30 is a generic placeholder and is INCORRECT for most leading African economies.
   - Real range reference: South Africa (~55-60), Morocco (~50-55), Egypt (~40-50).
   - If 2024 data is missing, strictly use 2023 or 2022 data.
2. HDI (UNDP) BENCHMARKS:
   - High HDI African Nations: Mauritius, Seychelles, Algeria, Tunisia, Egypt, Libya, South Africa.
   - ALGERIA SPECIFIC: Score ~0.763, World Rank ~96, African Rank ~3.
3. INFLATION & UNEMPLOYMENT (STRICT):
   - INFLATION: Use IMF World Economic Outlook (WEO) October 2024 data. Metric: "Inflation, Average Consumer Prices".
   - UNEMPLOYMENT: Use World Bank / ILO Modelled Estimates. Metric: "Unemployment, total (% of total labor force)".
   - DATA GAPS: DO NOT use regional averages. If exact data is missing, return null.
   - **VERIFICATION**: A 5-6% inflation rate is MODERATE. Do not flag as high. High is >15%.
4. UNITS: Trade values in Million USD (MUSD).
5. REGIONAL: Focus on Intra-African trade under AfCFTA.
6. TARIFFS: 'tariff_reduction' must be the DIFFERENCE between the destination's MFN (External) tariff and the AfCFTA rate (typically 0%).

Always respond in the language requested (French or English).
"""


class GeminiTradeService:
    """
    Service for AI-powered trade analysis using Gemini
    IMPROVED with AI Studio-quality prompts
    """
    
    def __init__(self):
        self.api_key = os.environ.get("EMERGENT_LLM_KEY")
        if not self.api_key:
            logger.warning("EMERGENT_LLM_KEY not found in environment")
        self._session_counter = 0
    
    def _get_chat(self, session_suffix: str = "") -> LlmChat:
        """Create a new chat instance with Gemini"""
        self._session_counter += 1
        session_id = f"trade-analysis-{self._session_counter}-{session_suffix}"
        
        chat = LlmChat(
            api_key=self.api_key,
            session_id=session_id,
            system_message=TRADE_SYSTEM_INSTRUCTION
        )
        chat.with_model("gemini", "gemini-2.0-flash")
        return chat
    
    async def analyze_trade_opportunities(
        self,
        country_name: str,
        mode: str = "export",  # export, import, industrial
        lang: str = "fr"
    ) -> Dict:
        """
        Analyze trade opportunities for a country using AI
        IMPROVED prompts based on AI Studio app
        """
        if not self.api_key:
            return {"error": "API key not configured", "opportunities": []}
        
        try:
            chat = self._get_chat(f"{country_name}-{mode}")
            
            lang_instruction = "Réponds en français." if lang == "fr" else "Respond in English."
            
            if mode == "export":
                prompt = f"""
{lang_instruction}

Identifie 15 opportunités d'EXPORT intra-africaines VÉRIFIÉES pour {country_name}.
Focus sur les produits où {country_name} a un avantage comparatif révélé ou une capacité de production élevée.

Exemple: Si tu analyses le Bénin, suggère Coton, Noix de cajou, Textiles vers des partenaires comme Nigeria, Togo.

CALCUL DES TARIFS: 'tariff_reduction' doit être la DIFFÉRENCE entre le tarif MFN (Externe) de la destination et le taux ZLECAf (0%).

Pour chaque opportunité, fournis EXACTEMENT ce format JSON:
{{
  "product": {{
    "name": "Nom du produit en {lang}",
    "hs_code": "Code HS 4-6 chiffres",
    "hs4_name": "Nom de la position HS4"
  }},
  "exporting_country": "{country_name}",
  "potential_partner": "Pays africain partenaire",
  "current_source": "Source actuelle si substitution",
  "rationale": "Justification stratégique détaillée (3-4 phrases)",
  "year": 2023,
  "potential_value_musd": 0.0,
  "current_value_musd": 0.0,
  "tariff_reduction": 0.0,
  "data_source": "IMF/UNCTAD/OEC",
  "is_estimation": false
}}

Réponds avec un JSON valide: {{"opportunities": [...], "sources": ["..."], "analysis_date": "..."}}
"""
            elif mode == "import":
                prompt = f"""
{lang_instruction}

Identifie 15 besoins d'IMPORT stratégiques pour {country_name} qui pourraient être satisfaits par d'autres pays africains.
Focus sur les produits essentiels, machines industrielles ou gaps énergétiques.

CALCUL DES TARIFS: 'tariff_reduction' représente les économies vs importation de sources non-africaines.

Pour chaque opportunité, fournis EXACTEMENT ce format JSON:
{{
  "product": {{
    "name": "Nom du produit en {lang}",
    "hs_code": "Code HS 4-6 chiffres",
    "hs4_name": "Nom de la position HS4"
  }},
  "importing_country": "{country_name}",
  "potential_supplier": "Pays africain fournisseur",
  "current_source": "Source actuelle (ex: Chine, Europe)",
  "rationale": "Justification détaillée (3-4 phrases)",
  "year": 2023,
  "import_value_musd": 0.0,
  "substitution_potential_musd": 0.0,
  "tariff_reduction": 0.0,
  "data_source": "IMF/UNCTAD/OEC",
  "is_estimation": false
}}

Réponds avec un JSON valide: {{"opportunities": [...], "sources": ["..."], "analysis_date": "..."}}
"""
            else:  # industrial
                prompt = f"""
{lang_instruction}

Analyse les IMPORTS d'intrants industriels de {country_name} (produits semi-finis, matières premières) à partir des données UNCTAD 2023-2024.
Identifie 15 opportunités de Transformation (Chaîne de Valeur):
- Quels intrants sont importés?
- Quels produits finis pourraient être exportés après transformation?

Exemple: S'ils importent du 'Tissu', ils peuvent exporter des 'Vêtements'.

Pour chaque opportunité, fournis EXACTEMENT ce format JSON:
{{
  "product": {{
    "name": "Produit fini exportable",
    "hs_code": "Code HS du produit fini",
    "hs4_name": "Position HS4 du produit fini"
  }},
  "industrial_input": {{
    "name": "Intrant importé",
    "hs_code": "Code HS de l'intrant",
    "import_volume": "Volume importé (ex: 45,000 Tonnes)"
  }},
  "exporting_country": "{country_name}",
  "target_markets": ["Marché 1", "Marché 2", "Marché 3"],
  "transformation_logic": "Explication de la transformation industrielle (2-3 phrases)",
  "estimated_production": "Quantité estimée de production (ex: 10M Unités)",
  "potential_value_musd": 0.0,
  "tariff_reduction": 0.0,
  "data_source": "UNCTAD/UNIDO",
  "is_estimation": true
}}

IMPORTANT - Ajoute aussi une section 'expected_results' avec les résultats attendus à 3 et 5 ans:
{{
  "opportunities": [...],
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
  "sources": ["..."],
  "analysis_date": "..."
}}
"""
"""
            
            message = UserMessage(text=prompt)
            response = await chat.send_message(message)
            
            # Parse JSON response
            result = self._parse_json_response(response)
            result["country"] = country_name
            result["mode"] = mode
            result["generated_by"] = "Gemini AI"
            
            return result
            
        except Exception as e:
            logger.error(f"Error in trade opportunity analysis: {str(e)}")
            return {"error": str(e), "opportunities": []}
    
    async def get_country_economic_profile(
        self,
        country_name: str,
        lang: str = "fr"
    ) -> Dict:
        """
        Generate comprehensive economic profile for a country
        IMPROVED with parallel requests like AI Studio
        """
        if not self.api_key:
            return {"error": "API key not configured"}
        
        try:
            chat = self._get_chat(f"profile-{country_name}")
            
            lang_instruction = "Réponds en français." if lang == "fr" else "Respond in English."
            
            prompt = f"""
{lang_instruction}

Génère un profil économique et commercial complet pour {country_name} basé sur les données officielles les plus récentes.

SOURCES CRITIQUES ET RÈGLES:
1. INFLATION (CPI %): STRICTEMENT **IMF World Economic Outlook (Oct 2024)** "Inflation, Average Consumer Prices".
2. CHÔMAGE (%): STRICTEMENT **World Bank / ILO Modelled Estimates**.
3. PIB & DETTE: IMF WEO October 2024.
4. GAI (Attractivité): "The European House - Ambrosetti" Global Attractiveness Index.
   - **NE PAS METTRE 30 PAR DÉFAUT**. Scores réels: Afrique du Sud ~57, Égypte ~42, Maroc ~52.
5. HDI: UNDP 2024/2025.

DONNÉES REQUISES (structure JSON exacte):

{{
  "economic_indicators": {{
    "gdp_billion_usd": 0.0,
    "gdp_per_capita_usd": 0.0,
    "gdp_growth_percent": 0.0,
    "inflation_percent": 0.0,
    "unemployment_percent": 0.0,
    "total_debt_gdp_percent": 0.0,
    "domestic_debt_gdp_percent": 0.0,
    "external_debt_gdp_percent": 0.0,
    "foreign_reserves_billion": 0.0,
    "gold_reserves_tonnes": 0.0,
    "data_year": 2024
  }},
  "development_indices": {{
    "hdi_score": 0.0,
    "hdi_world_rank": 0,
    "hdi_africa_rank": 0,
    "gai_score": 0.0,
    "gai_world_rank": 0,
    "gai_africa_rank": 0,
    "gai_category": "A/B/C/D"
  }},
  "trade_summary": {{
    "total_exports_musd": 0.0,
    "total_imports_musd": 0.0,
    "trade_balance_musd": 0.0,
    "intra_african_trade_percent": 0.0,
    "top_export_partners": [{{"country": "", "value_musd": 0, "is_african": false}}],
    "top_import_partners": [{{"country": "", "value_musd": 0, "is_african": false}}],
    "top_exports": [{{"product": "", "hs_code": "", "value_musd": 0}}],
    "top_imports": [{{"product": "", "hs_code": "", "value_musd": 0}}]
  }},
  "afcfta_potential": {{
    "key_opportunities": ["Opportunité 1", "Opportunité 2", "Opportunité 3"],
    "regional_memberships": ["CEDEAO/SADC/EAC/UMA..."],
    "comparative_advantages": ["Avantage 1", "Avantage 2", "Avantage 3"]
  }},
  "sources": ["IMF WEO Oct 2024", "World Bank", "UNCTAD"],
  "data_verification": "VERIFIED" ou "CONTAINS_ESTIMATIONS"
}}

Réponds en JSON valide uniquement.
"""
            
            message = UserMessage(text=prompt)
            response = await chat.send_message(message)
            
            result = self._parse_json_response(response)
            result["country"] = country_name
            result["generated_by"] = "Gemini AI"
            result["generation_date"] = datetime.utcnow().isoformat()
            
            return result
            
        except Exception as e:
            logger.error(f"Error generating country profile: {str(e)}")
            return {"error": str(e)}
    
    async def analyze_product_by_hs_code(
        self,
        hs_code: str,
        lang: str = "fr"
    ) -> Dict:
        """
        Analyze a product by HS code for African trade
        IMPROVED with AI Studio structure
        """
        if not self.api_key:
            return {"error": "API key not configured"}
        
        try:
            chat = self._get_chat(f"product-{hs_code}")
            
            lang_instruction = "Réponds en français." if lang == "fr" else "Respond in English."
            
            prompt = f"""
{lang_instruction}

Récupère les données ITC TradeMap et UNCTADstat 2023 pour le code HS {hs_code}.
Fournis les valeurs commerciales déclarées pour les 15 PREMIERS partenaires africains.

Structure JSON requise:

{{
  "product": {{
    "name": "Nom du produit",
    "hs_code": "{hs_code}",
    "hs2_code": "XX",
    "hs2_name": "Chapitre HS",
    "hs4_code": "XXXX",
    "hs4_name": "Position HS4"
  }},
  "african_trade_summary": {{
    "total_african_exports_musd": 0.0,
    "total_african_imports_musd": 0.0,
    "intra_african_trade_musd": 0.0
  }},
  "top_african_exporters": [
    {{
      "country": "Pays",
      "export_value_musd": 0.0,
      "world_share_percent": 0.0,
      "historical_data": [
        {{"year": 2021, "value_musd": 0.0}},
        {{"year": 2022, "value_musd": 0.0}},
        {{"year": 2023, "value_musd": 0.0}}
      ]
    }}
  ],
  "top_african_importers": [
    {{
      "country": "Pays",
      "import_value_musd": 0.0,
      "main_sources": ["Source 1", "Source 2"],
      "historical_data": [
        {{"year": 2021, "value_musd": 0.0}},
        {{"year": 2022, "value_musd": 0.0}},
        {{"year": 2023, "value_musd": 0.0}}
      ]
    }}
  ],
  "production_capacities": [
    {{
      "country": "Pays",
      "capacity": 0.0,
      "unit": "tonnes/units",
      "source": "FAOSTAT/UNIDO/USGS"
    }}
  ],
  "substitution_opportunities": [
    {{
      "importer": "Pays importateur",
      "potential_supplier": "Fournisseur africain",
      "current_source": "Source actuelle",
      "potential_value_musd": 0.0,
      "rationale": "Justification"
    }}
  ],
  "sources": ["ITC TradeMap", "UNCTADstat"],
  "data_year": 2023
}}

Réponds en JSON valide uniquement.
"""
            
            message = UserMessage(text=prompt)
            response = await chat.send_message(message)
            
            result = self._parse_json_response(response)
            result["hs_code"] = hs_code
            result["generated_by"] = "Gemini AI"
            result["generation_date"] = datetime.utcnow().isoformat()
            
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing product {hs_code}: {str(e)}")
            return {"error": str(e)}
    
    async def get_trade_balance_analysis(
        self,
        country_name: str,
        lang: str = "fr"
    ) -> Dict:
        """
        Get trade balance history and analysis for a country
        IMPROVED with AI Studio approach
        """
        if not self.api_key:
            return {"error": "API key not configured"}
        
        try:
            chat = self._get_chat(f"balance-{country_name}")
            
            lang_instruction = "Réponds en français." if lang == "fr" else "Respond in English."
            
            prompt = f"""
{lang_instruction}

Extrais les données de Commerce de Marchandises (Exports/Imports) pour {country_name} (2020-2025) 
à partir du IMF World Economic Outlook (Oct 2024).

IMPORTANT: 
- Fournis STRICTEMENT UNE entrée par année
- Valeurs en MILLIONS de USD (MUSD)
- Pour le Bénin (exemple): Exports ~3500-4500 MUSD, Imports ~4000-5000 MUSD
- Pour l'Algérie: Assure-toi que l'excédent de $10B+ du gaz naturel est reflété

Structure JSON:

{{
  "trade_balance_history": [
    {{
      "year": 2020,
      "total_exports_musd": 0.0,
      "total_imports_musd": 0.0,
      "balance_musd": 0.0,
      "is_estimation": false
    }}
  ],
  "analysis": {{
    "trend": "surplus/deficit/equilibre",
    "trend_direction": "improving/declining/stable",
    "key_factors": ["Facteur 1", "Facteur 2"],
    "outlook": "Perspectives court terme (2-3 phrases)"
  }},
  "sources": ["IMF WEO Oct 2024"],
  "data_verification": "VERIFIED"
}}

Réponds en JSON valide uniquement.
"""
            
            message = UserMessage(text=prompt)
            response = await chat.send_message(message)
            
            result = self._parse_json_response(response)
            result["country"] = country_name
            result["generated_by"] = "Gemini AI"
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting trade balance: {str(e)}")
            return {"error": str(e)}
    
    async def get_trade_summary(
        self,
        lang: str = "fr"
    ) -> Dict:
        """
        Generate a comprehensive African trade summary for the "Vue d'ensemble" tab
        Returns aggregate stats across all African countries
        """
        if not self.api_key:
            return {"error": "API key not configured"}
        
        try:
            chat = self._get_chat("summary-overview")
            
            lang_instruction = "Réponds en français." if lang == "fr" else "Respond in English."
            
            prompt = f"""
{lang_instruction}

Génère un résumé complet du commerce africain basé sur les données IMF DOTS 2024 et UNCTAD 2024.

IMPORTANT: Utilise des données RÉALISTES et VÉRIFIÉES.
- Commerce total africain: ~$1.4-1.8 trillion USD (2024)
- Commerce intra-africain: ~15-18% du total (~$180-220 milliards)
- 54 pays membres de la ZLECAf

Structure JSON requise:

{{
  "overview": {{
    "total_african_trade_billion_usd": 1650,
    "intra_african_trade_billion_usd": 186,
    "intra_african_share_percent": 11.3,
    "afcfta_countries": 54,
    "total_opportunities_identified": 5387,
    "year": 2024
  }},
  "top_trading_countries": [
    {{"name": "Pays", "iso3": "XXX", "trade_volume_billion": 0.0, "rank": 1}}
  ],
  "top_sectors": [
    {{"name": "Secteur", "hs_chapter": "XX", "value_billion": 0.0, "opportunities_count": 0}}
  ],
  "growth_metrics": {{
    "yoy_growth_percent": 0.0,
    "projected_2030_trade_billion": 0.0,
    "afcfta_boost_potential_percent": 0.0
  }},
  "regional_blocs": [
    {{"name": "CEDEAO/SADC/EAC/etc", "members": 0, "intra_bloc_trade_billion": 0.0}}
  ],
  "sources": ["IMF DOTS 2024", "UNCTAD 2024", "AfCFTA Secretariat"],
  "data_quality": "VERIFIED"
}}

Réponds en JSON valide uniquement.
"""
            
            message = UserMessage(text=prompt)
            response = await chat.send_message(message)
            
            result = self._parse_json_response(response)
            result["generated_by"] = "Gemini AI"
            result["generation_date"] = datetime.utcnow().isoformat()
            
            return result
            
        except Exception as e:
            logger.error(f"Error generating trade summary: {str(e)}")
            return {"error": str(e)}
    
    async def get_value_chains_analysis(
        self,
        sector: str = None,
        lang: str = "fr"
    ) -> Dict:
        """
        Generate value chain analysis for African sectors
        Used for "Chaînes de Valeur" tab
        """
        if not self.api_key:
            return {"error": "API key not configured"}
        
        try:
            chat = self._get_chat(f"value-chains-{sector or 'all'}")
            
            lang_instruction = "Réponds en français." if lang == "fr" else "Respond in English."
            
            sector_filter = f"Concentre-toi sur le secteur {sector}." if sector else "Analyse les 6 principales chaînes de valeur africaines."
            
            prompt = f"""
{lang_instruction}

{sector_filter}

Génère une analyse des chaînes de valeur africaines basée sur FAOSTAT, UNIDO, UNCTAD et ITC TradeMap 2024.

DONNÉES CRITIQUES:
- Café: Éthiopie (496K tonnes), Ouganda (288K), Kenya (42K)
- Cacao: Côte d'Ivoire (2.2M tonnes, 45% mondial), Ghana (800K, 16%)
- Coton: Mali (780K), Burkina Faso (600K), Bénin (550K)
- Pétrole: Nigeria (1.8M barils/j), Angola (1.2M), Algérie (1M)
- Minéraux: Afrique du Sud (#1 platine, or), RD Congo (#1 cobalt)
- Automobile: Afrique du Sud (450K véhicules), Maroc (180K)

Structure JSON requise:

{{
  "value_chains": [
    {{
      "id": "coffee",
      "name": {{"fr": "Café", "en": "Coffee"}},
      "icon": "☕",
      "hs_code": "0901",
      "color": "#7c3aed",
      "stages": [
        {{
          "name": {{"fr": "Production", "en": "Production"}},
          "countries": ["ETH", "UGA", "KEN"],
          "value_billion": 2.8
        }}
      ],
      "top_producers": [
        {{
          "country": "Éthiopie",
          "iso3": "ETH",
          "production_tonnes": 496000,
          "market_share_percent": 42
        }}
      ],
      "intra_african_potential_musd": 450,
      "global_exports_musd": 3200,
      "afcfta_opportunities": [
        "Réduction tarifaire jusqu'à 90%",
        "Règles d'origine favorisant transformation locale"
      ]
    }}
  ],
  "transformation_opportunities": [
    {{
      "input_product": "Café vert",
      "output_product": "Café torréfié",
      "value_added_percent": 300,
      "key_countries": ["ETH", "KEN", "TZA"]
    }}
  ],
  "sources": ["FAOSTAT 2024", "UNIDO INDSTAT", "ITC TradeMap"],
  "data_year": 2024
}}

Réponds en JSON valide uniquement.
"""
            
            message = UserMessage(text=prompt)
            response = await chat.send_message(message)
            
            result = self._parse_json_response(response)
            result["generated_by"] = "Gemini AI"
            result["generation_date"] = datetime.utcnow().isoformat()
            
            return result
            
        except Exception as e:
            logger.error(f"Error generating value chains: {str(e)}")
            return {"error": str(e)}
    
    def _parse_json_response(self, response: str) -> Dict:
        """Parse JSON from AI response, handling markdown code blocks"""
        try:
            # Clean response
            cleaned = response.strip()
            
            # Remove markdown code blocks
            if cleaned.startswith("```json"):
                cleaned = cleaned.replace("```json", "", 1)
            if cleaned.startswith("```"):
                cleaned = cleaned.replace("```", "", 1)
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            
            cleaned = cleaned.strip()
            
            # Find JSON object or array
            json_match = None
            for start_char, end_char in [('{', '}'), ('[', ']')]:
                start_idx = cleaned.find(start_char)
                if start_idx != -1:
                    # Find matching end
                    depth = 0
                    for i, char in enumerate(cleaned[start_idx:]):
                        if char == start_char:
                            depth += 1
                        elif char == end_char:
                            depth -= 1
                            if depth == 0:
                                json_match = cleaned[start_idx:start_idx + i + 1]
                                break
                    if json_match:
                        break
            
            if json_match:
                return json.loads(json_match)
            
            # Try parsing entire response
            return json.loads(cleaned)
            
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse JSON response: {e}")
            return {
                "raw_response": response,
                "parse_error": str(e)
            }


# Singleton instance
gemini_trade_service = GeminiTradeService()
