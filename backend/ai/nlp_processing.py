"""
NLP Search Processor for the AfCFTA trade platform.

Provides intent extraction, entity recognition, HS code fuzzy matching and
natural-language-to-HS-code conversion using only the Python standard library
(difflib) – no external ML or NLP dependencies required.
"""

from __future__ import annotations

import difflib
import re
import unicodedata
from typing import Any

# ---------------------------------------------------------------------------
# Static knowledge bases
# ---------------------------------------------------------------------------

# Common trade-intent keywords → intent label
_INTENT_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"\b(import|buy|purchase|bring in|source)\b", re.I), "import"),
    (re.compile(r"\b(export|sell|ship|send abroad|trade out)\b", re.I), "export"),
    (re.compile(r"\b(tariff|duty|tax|rate|charge|levy)\b", re.I), "tariff_lookup"),
    (re.compile(r"\b(classify|classification|hs code|hs number|heading)\b", re.I), "classification"),
    (re.compile(r"\b(invest|investment|opportunity|fdi|startup)\b", re.I), "investment"),
    (re.compile(r"\b(country|market|africa|nation|region)\b", re.I), "market_info"),
    (re.compile(r"\b(regulation|rule|requirement|standard|certificate|permit)\b", re.I), "regulatory"),
    (re.compile(r"\b(logistics|shipping|freight|transport|port|warehouse)\b", re.I), "logistics"),
]

# Entity extraction patterns
_COUNTRY_LIST = [
    "Nigeria", "South Africa", "Egypt", "Kenya", "Ethiopia", "Ghana", "Morocco",
    "Tanzania", "Rwanda", "Côte d'Ivoire", "Ivory Coast", "Senegal", "Cameroon",
    "Uganda", "Mozambique", "Zambia", "Zimbabwe", "Angola", "Sudan", "Libya",
    "Tunisia", "Algeria", "DRC", "Congo", "Botswana", "Namibia", "Mali", "Niger",
    "Burkina Faso", "Guinea", "Benin", "Togo", "Malawi", "Mauritius", "Seychelles",
]

_SECTOR_KEYWORDS: dict[str, list[str]] = {
    "agriculture": ["farm", "crop", "grain", "cocoa", "coffee", "tea", "maize",
                    "wheat", "rice", "vegetable", "fruit", "livestock", "agri", "food"],
    "technology": ["tech", "software", "app", "digital", "fintech", "saas", "ai",
                   "startup", "ict", "mobile", "internet", "ecommerce"],
    "energy": ["solar", "wind", "power", "electricity", "oil", "gas", "petroleum",
               "renewable", "hydro", "energy"],
    "manufacturing": ["factory", "plant", "production", "assembly", "textile",
                      "apparel", "garment", "steel", "cement", "automotive"],
    "finance": ["bank", "insurance", "credit", "loan", "microfinance", "capital",
                "investment", "fund", "fintech"],
    "logistics": ["port", "freight", "shipping", "transport", "warehouse", "supply chain",
                  "3pl", "customs", "clearance"],
    "healthcare": ["hospital", "clinic", "pharma", "medical", "health", "diagnostic",
                   "medicine", "drug", "biotech"],
    "retail": ["shop", "store", "supermarket", "consumer", "fmcg", "retail",
               "ecommerce", "marketplace"],
}

# Sample HS code database (chapter + heading descriptions)
_HS_CODE_DB: list[dict[str, Any]] = [
    # Chapter 01 – Live animals
    {"code": "0101", "description": "Live horses, asses, mules and hinnies"},
    {"code": "0102", "description": "Live bovine animals"},
    {"code": "0103", "description": "Live swine"},
    {"code": "0104", "description": "Live sheep and goats"},
    {"code": "0105", "description": "Live poultry"},
    # Chapter 02 – Meat
    {"code": "0201", "description": "Meat of bovine animals, fresh or chilled"},
    {"code": "0202", "description": "Meat of bovine animals, frozen"},
    {"code": "0207", "description": "Meat and edible offal of poultry"},
    # Chapter 04 – Dairy
    {"code": "0401", "description": "Milk and cream, not concentrated or sweetened"},
    {"code": "0402", "description": "Milk and cream, concentrated or sweetened"},
    {"code": "0406", "description": "Cheese and curd"},
    # Chapter 07 – Vegetables
    {"code": "0701", "description": "Potatoes, fresh or chilled"},
    {"code": "0702", "description": "Tomatoes, fresh or chilled"},
    {"code": "0703", "description": "Onions, shallots, garlic, leeks"},
    {"code": "0713", "description": "Dried leguminous vegetables, shelled"},
    # Chapter 08 – Fruits
    {"code": "0801", "description": "Coconuts, Brazil nuts, cashew nuts, fresh or dried"},
    {"code": "0802", "description": "Other nuts, fresh or dried"},
    {"code": "0803", "description": "Bananas, including plantains, fresh or dried"},
    {"code": "0804", "description": "Dates, figs, pineapples, avocados, guavas, mangoes"},
    {"code": "0901", "description": "Coffee, whether or not roasted or decaffeinated"},
    {"code": "0902", "description": "Tea, whether or not flavoured"},
    {"code": "1001", "description": "Wheat and meslin"},
    {"code": "1002", "description": "Rye"},
    {"code": "1005", "description": "Maize (corn)"},
    {"code": "1006", "description": "Rice"},
    {"code": "1201", "description": "Soya beans, whether or not broken"},
    {"code": "1511", "description": "Palm oil and its fractions, whether or not refined"},
    {"code": "1801", "description": "Cocoa beans, whole or broken, raw or roasted"},
    {"code": "1802", "description": "Cocoa shells, husks, skins and other cocoa waste"},
    {"code": "1803", "description": "Cocoa paste, whether or not defatted"},
    {"code": "1804", "description": "Cocoa butter, fat and oil"},
    {"code": "1805", "description": "Cocoa powder, not containing added sugar"},
    {"code": "1806", "description": "Chocolate and other food preparations containing cocoa"},
    # Chapter 25 – Minerals
    {"code": "2503", "description": "Sulphur of all kinds"},
    {"code": "2508", "description": "Clays"},
    {"code": "2601", "description": "Iron ores and concentrates"},
    {"code": "2603", "description": "Copper ores and concentrates"},
    {"code": "2701", "description": "Coal; briquettes, ovoids and similar solid fuels"},
    {"code": "2709", "description": "Petroleum oils and oils obtained from bituminous minerals, crude"},
    {"code": "2710", "description": "Petroleum oils, not crude"},
    # Chapter 27 – Energy
    {"code": "2711", "description": "Petroleum gas and other gaseous hydrocarbons"},
    {"code": "2716", "description": "Electrical energy"},
    # Chapter 39 – Plastics
    {"code": "3901", "description": "Polymers of ethylene, in primary forms"},
    {"code": "3902", "description": "Polymers of propylene, in primary forms"},
    # Chapter 44 – Wood
    {"code": "4401", "description": "Fuel wood; wood in chips or particles; sawdust"},
    {"code": "4403", "description": "Wood in the rough"},
    {"code": "4407", "description": "Wood sawn or chipped lengthwise"},
    # Chapter 50–63 – Textiles
    {"code": "5101", "description": "Wool, not carded or combed"},
    {"code": "5201", "description": "Cotton, not carded or combed"},
    {"code": "5208", "description": "Woven fabrics of cotton"},
    {"code": "6101", "description": "Men's overcoats and cloaks of wool or fine animal hair"},
    {"code": "6109", "description": "T-shirts, singlets and other vests, knitted or crocheted"},
    {"code": "6201", "description": "Men's overcoats, car coats, capes, cloaks and similar articles"},
    {"code": "6302", "description": "Bed linen, table linen, toilet linen and kitchen linen"},
    # Chapter 72 – Steel
    {"code": "7201", "description": "Pig iron and spiegeleisen in pigs, blocks or other primary forms"},
    {"code": "7208", "description": "Flat-rolled products of iron or non-alloy steel"},
    # Chapter 84–85 – Machinery & Electronics
    {"code": "8415", "description": "Air conditioning machines"},
    {"code": "8471", "description": "Automatic data processing machines (computers)"},
    {"code": "8517", "description": "Telephone sets including smartphones; other apparatus for transmission"},
    {"code": "8525", "description": "Transmission apparatus for radio-broadcasting or television"},
    {"code": "8544", "description": "Insulated wire, cable and other insulated electric conductors"},
    # Chapter 87 – Vehicles
    {"code": "8701", "description": "Tractors"},
    {"code": "8702", "description": "Motor vehicles for the transport of ten or more persons"},
    {"code": "8703", "description": "Motor cars and other motor vehicles for transport of persons"},
    {"code": "8704", "description": "Motor vehicles for the transport of goods"},
    # Chapter 90 – Instruments
    {"code": "9018", "description": "Instruments and appliances used in medical, surgical or veterinary sciences"},
    {"code": "9021", "description": "Orthopaedic appliances"},
    # Chapter 94 – Furniture
    {"code": "9401", "description": "Seats (other than those of heading 9402)"},
    {"code": "9403", "description": "Other furniture and parts thereof"},
]

# Natural-language synonym map → HS description keywords
_SYNONYM_MAP: dict[str, list[str]] = {
    "phone": ["telephone", "smartphone", "mobile"],
    "laptop": ["computer", "automatic data processing"],
    "car": ["motor vehicle", "motor cars"],
    "truck": ["motor vehicles for transport of goods"],
    "tractor": ["tractors"],
    "cocoa": ["cocoa beans", "chocolate"],
    "coffee": ["coffee"],
    "tea": ["tea"],
    "rice": ["rice"],
    "corn": ["maize"],
    "wheat": ["wheat"],
    "cotton": ["cotton"],
    "clothes": ["t-shirts", "overcoats", "woven fabrics"],
    "clothing": ["t-shirts", "overcoats", "garment"],
    "fabric": ["woven fabrics", "cotton", "textile"],
    "steel": ["iron", "flat-rolled products"],
    "oil": ["petroleum oils", "palm oil"],
    "gas": ["petroleum gas", "gaseous hydrocarbons"],
    "electricity": ["electrical energy"],
    "solar": ["electrical energy"],
    "furniture": ["seats", "furniture"],
    "wood": ["wood", "fuel wood", "sawn"],
    "coal": ["coal"],
    "copper": ["copper ores"],
    "iron": ["iron ores", "pig iron"],
}

# Contextual suggestion templates
_SUGGESTION_TEMPLATES: list[str] = [
    "HS code for {keyword}",
    "tariff rate for {keyword} in Nigeria",
    "import duty on {keyword} in Kenya",
    "export requirements for {keyword}",
    "AfCFTA tariff schedule for {keyword}",
]


# ---------------------------------------------------------------------------
# Text utilities
# ---------------------------------------------------------------------------

def _normalize(text: str) -> str:
    """Lowercase, strip accents, remove non-alphanumeric chars."""
    nfkd = unicodedata.normalize("NFKD", text)
    ascii_text = nfkd.encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9\s]", " ", ascii_text.lower()).strip()


def _tokenize(text: str) -> list[str]:
    return [w for w in _normalize(text).split() if len(w) > 1]


def _token_overlap(query_tokens: list[str], target_tokens: list[str]) -> float:
    if not query_tokens or not target_tokens:
        return 0.0
    matches = sum(1 for t in query_tokens if t in target_tokens)
    return matches / max(len(query_tokens), len(target_tokens))


def _sequence_similarity(a: str, b: str) -> float:
    return difflib.SequenceMatcher(None, _normalize(a), _normalize(b)).ratio()


# ---------------------------------------------------------------------------
# Main processor
# ---------------------------------------------------------------------------

class NLPSearchProcessor:
    """
    Process natural-language trade queries into structured intents and entities,
    and perform fuzzy HS code search using difflib – no external ML needed.
    """

    def __init__(self) -> None:
        self._intent_patterns = _INTENT_PATTERNS
        self._country_list = _COUNTRY_LIST
        self._sector_keywords = _SECTOR_KEYWORDS
        self._hs_db = _HS_CODE_DB
        self._synonym_map = _SYNONYM_MAP

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def process_query(self, query: str) -> dict[str, Any]:
        """
        Extract intent and named entities from a natural-language trade query.

        Returns
        -------
        dict with keys:
            ``intent``         – primary intent label (str)
            ``secondary_intents`` – additional intents (list[str])
            ``entities``       – extracted entities by type (dict)
            ``keywords``       – important extracted keywords (list[str])
            ``confidence``     – confidence of intent detection (float 0-1)
            ``normalized_query`` – cleaned query string
        """
        normalized = _normalize(query)
        tokens = _tokenize(query)

        intents: list[tuple[str, int]] = []
        for pattern, label in self._intent_patterns:
            matches = pattern.findall(query)
            if matches:
                intents.append((label, len(matches)))

        intents.sort(key=lambda x: x[1], reverse=True)
        primary_intent = intents[0][0] if intents else "general_search"
        secondary_intents = [i[0] for i in intents[1:3]]

        confidence = min(1.0, 0.5 + len(intents) * 0.1) if intents else 0.4

        entities = {
            "countries": self._extract_countries(query),
            "sectors": self._extract_sectors(query),
            "hs_codes": self._extract_hs_codes(query),
            "quantities": self._extract_quantities(query),
            "currencies": self._extract_currencies(query),
        }

        keywords = self._extract_keywords(tokens)

        return {
            "intent": primary_intent,
            "secondary_intents": secondary_intents,
            "entities": entities,
            "keywords": keywords,
            "confidence": round(confidence, 3),
            "normalized_query": normalized,
        }

    def fuzzy_hs_search(
        self,
        query: str,
        hs_codes_data: list[dict[str, Any]] | None = None,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """
        Fuzzy-search HS codes matching *query* using difflib similarity.

        Parameters
        ----------
        query:
            Natural-language or partial-code search string.
        hs_codes_data:
            Optional external HS code list (list of dicts with 'code' and
            'description'). Defaults to the built-in database.
        limit:
            Maximum number of results.

        Returns
        -------
        List of dicts: ``{code, description, similarity_score, match_type}``
        """
        db = hs_codes_data if hs_codes_data is not None else self._hs_db
        q_norm = _normalize(query)
        q_tokens = _tokenize(query)

        # Expand query using synonym map
        expanded_tokens = list(q_tokens)
        for word in q_tokens:
            if word in self._synonym_map:
                for syn in self._synonym_map[word]:
                    expanded_tokens.extend(_tokenize(syn))

        results: list[dict[str, Any]] = []
        for item in db:
            code: str = item.get("code", "")
            desc: str = item.get("description", "")
            desc_norm = _normalize(desc)
            desc_tokens = _tokenize(desc)

            # Exact code prefix match
            if q_norm.replace(" ", "").startswith(code[:4]):
                sim = 1.0
                match_type = "code_prefix"
            else:
                seq_sim = _sequence_similarity(q_norm, desc_norm)
                token_sim = _token_overlap(expanded_tokens, desc_tokens)
                sim = seq_sim * 0.5 + token_sim * 0.5
                match_type = "semantic" if token_sim > seq_sim else "fuzzy_string"

            if sim > 0.10:
                results.append(
                    {
                        "code": code,
                        "description": desc,
                        "similarity_score": round(sim, 4),
                        "match_type": match_type,
                    }
                )

        results.sort(key=lambda r: r["similarity_score"], reverse=True)
        return results[:limit]

    def natural_language_to_hs(self, description: str) -> dict[str, Any]:
        """
        Convert a natural-language product description to the most likely HS code.

        Returns the top match with metadata, or an empty-result dict.
        """
        matches = self.fuzzy_hs_search(description, limit=5)
        if not matches:
            return {
                "found": False,
                "description": description,
                "top_match": None,
                "alternatives": [],
            }

        top = matches[0]
        return {
            "found": True,
            "description": description,
            "top_match": {
                "code": top["code"],
                "description": top["description"],
                "confidence": top["similarity_score"],
            },
            "alternatives": matches[1:],
        }

    def get_search_suggestions(
        self,
        partial_query: str,
        context: dict[str, Any] | None = None,
    ) -> list[str]:
        """
        Return auto-complete / search suggestions for *partial_query*.

        Parameters
        ----------
        partial_query:
            The incomplete query typed by the user.
        context:
            Optional dict with ``sector``, ``country`` or ``intent`` to
            bias suggestions.
        """
        suggestions: list[str] = []
        q_lower = partial_query.lower().strip()
        tokens = _tokenize(partial_query)

        # 1. HS code matches (top 3)
        hs_matches = self.fuzzy_hs_search(partial_query, limit=3)
        for m in hs_matches:
            if m["similarity_score"] > 0.25:
                suggestions.append(f"HS {m['code']}: {m['description']}")

        # 2. Synonym expansions
        for token in tokens:
            if token in self._synonym_map:
                for syn in self._synonym_map[token][:2]:
                    suggestions.append(f"{partial_query.strip()} ({syn})")

        # 3. Contextual templates using extracted keywords
        keywords = self._extract_keywords(tokens)[:2]
        for kw in keywords:
            for tmpl in _SUGGESTION_TEMPLATES[:3]:
                suggestions.append(tmpl.format(keyword=kw))

        # 4. Context-aware suggestions
        if context:
            country = context.get("country", "")
            sector = context.get("sector", "")
            if country:
                suggestions.append(f"Tariff rates for {partial_query} in {country}")
                suggestions.append(f"Export requirements for {partial_query} to {country}")
            if sector:
                suggestions.append(f"{partial_query} {sector} investment opportunities")

        # Deduplicate and limit
        seen: set[str] = set()
        unique: list[str] = []
        for s in suggestions:
            key = s.lower()
            if key not in seen and len(s) > 0:
                seen.add(key)
                unique.append(s)

        return unique[:10]

    # ------------------------------------------------------------------
    # Internal entity extractors
    # ------------------------------------------------------------------

    def _extract_countries(self, text: str) -> list[str]:
        found: list[str] = []
        for country in self._country_list:
            if re.search(r"\b" + re.escape(country) + r"\b", text, re.I):
                canonical = "Côte d'Ivoire" if country.lower() == "ivory coast" else country
                if canonical not in found:
                    found.append(canonical)
        return found

    def _extract_sectors(self, text: str) -> list[str]:
        text_lower = text.lower()
        found: list[str] = []
        for sector, keywords in self._sector_keywords.items():
            for kw in keywords:
                if kw in text_lower:
                    if sector not in found:
                        found.append(sector)
                    break
        return found

    def _extract_hs_codes(self, text: str) -> list[str]:
        """Extract HS code patterns (4–10 digits, optionally dot-separated)."""
        pattern = re.compile(r"\b(\d{4}(?:[.\s]?\d{2}){0,3})\b")
        return [m.group(1) for m in pattern.finditer(text)]

    def _extract_quantities(self, text: str) -> list[dict[str, Any]]:
        """Extract numeric quantities with optional units."""
        pattern = re.compile(
            r"(\d+(?:[,\s]\d{3})*(?:\.\d+)?)\s*"
            r"(kg|ton|tonne|mt|unit|piece|pcs|container|litre|liter|barrel|bbl)?",
            re.I,
        )
        results = []
        for m in pattern.finditer(text):
            value_str = m.group(1).replace(",", "").replace(" ", "")
            try:
                value = float(value_str)
            except ValueError:
                continue
            results.append({"value": value, "unit": m.group(2) or "unit"})
        return results[:5]

    def _extract_currencies(self, text: str) -> list[dict[str, str]]:
        """Extract currency mentions."""
        pattern = re.compile(
            r"(USD|EUR|GBP|NGN|KES|ZAR|GHS|ETB|TZS|MAD|EGP|XOF|XAF|\$|€|£)"
            r"[\s]?(\d+(?:[,\s]\d{3})*(?:\.\d+)?)?",
            re.I,
        )
        results = []
        for m in pattern.finditer(text):
            results.append({"currency": m.group(1).upper(), "amount": m.group(2) or ""})
        return results[:3]

    def _extract_keywords(self, tokens: list[str]) -> list[str]:
        """Return content-bearing keywords (remove common stopwords)."""
        _STOPWORDS = {
            "the", "a", "an", "and", "or", "in", "of", "for", "to", "is",
            "are", "from", "with", "at", "by", "on", "be", "this", "that",
            "it", "i", "we", "what", "how", "do", "does", "can", "my", "me",
        }
        return [t for t in tokens if t not in _STOPWORDS and len(t) > 2]
