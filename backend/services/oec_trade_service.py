"""
Service d'intégration avec l'API OEC (Observatory of Economic Complexity)
=========================================================================
Permet de récupérer les statistiques commerciales par:
- Code HS (HS4, HS6)
- Pays exportateur/importateur
- Année

API Documentation: https://oec.world/en/resources/documentation

MISE À JOUR 2025: Les données 2024 sont maintenant disponibles
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional

import httpx

logger = logging.getLogger(__name__)

# Configuration de l'API OEC
OEC_BASE_URL = "https://api.oec.world/tesseract/data.jsonrecords"

# Cubes disponibles (datasets)
# On utilise HS Rev. 2017 car c'est le plus proche de SH2022 et couvre les données récentes
OEC_CUBES = {
    "hs92": "trade_i_baci_a_92",  # HS Rev. 1992 (1995-2024)
    "hs96": "trade_i_baci_a_96",  # HS Rev. 1996 (1998-2024)
    "hs02": "trade_i_baci_a_02",  # HS Rev. 2002 (2003-2024)
    "hs07": "trade_i_baci_a_07",  # HS Rev. 2007 (2008-2024)
    "hs12": "trade_i_baci_a_12",  # HS Rev. 2012 (2013-2024)
    "hs17": "trade_i_baci_a_17",  # HS Rev. 2017 (2018-2024) - UTILISÉ PAR DÉFAUT
}

# Année par défaut pour les requêtes - 2024 maintenant disponible
DEFAULT_YEAR = 2024

# Cube par défaut - HS Rev. 2017 pour cohérence avec SH2022
DEFAULT_CUBE = "hs17"

# Mapping des préfixes OEC par section HS (pour HS6)
# L'API OEC utilise un préfixe basé sur la section HS
OEC_HS6_PREFIXES = {
    # Section I - Animaux vivants et produits du règne animal (Ch. 01-05)
    (1, 5): 1,
    # Section II - Produits du règne végétal (Ch. 06-14)
    (6, 14): 2,
    # Section III - Graisses et huiles (Ch. 15)
    (15, 15): 3,
    # Section IV - Produits alimentaires, boissons, tabacs (Ch. 16-24)
    (16, 24): 4,
    # Section V - Produits minéraux (Ch. 25-27)
    (25, 27): 5,
    # Section VI - Produits chimiques (Ch. 28-38)
    (28, 38): 6,
    # Section VII - Matières plastiques et caoutchouc (Ch. 39-40)
    (39, 40): 7,
    # Section VIII - Peaux, cuirs (Ch. 41-43)
    (41, 43): 8,
    # Section IX - Bois (Ch. 44-46)
    (44, 46): 9,
    # Section X - Pâtes de bois, papier (Ch. 47-49)
    (47, 49): 10,
    # Section XI - Matières textiles (Ch. 50-63)
    (50, 63): 11,
    # Section XII - Chaussures, coiffures (Ch. 64-67)
    (64, 67): 12,
    # Section XIII - Ouvrages en pierres (Ch. 68-70)
    (68, 70): 13,
    # Section XIV - Perles, pierres, métaux précieux (Ch. 71)
    (71, 71): 14,
    # Section XV - Métaux communs (Ch. 72-83)
    (72, 83): 15,
    # Section XVI - Machines, appareils (Ch. 84-85)
    (84, 85): 16,
    # Section XVII - Matériel de transport (Ch. 86-89)
    (86, 89): 17,
    # Section XVIII - Instruments optiques (Ch. 90-92)
    (90, 92): 18,
    # Section XIX - Armes (Ch. 93)
    (93, 93): 19,
    # Section XX - Marchandises diverses (Ch. 94-96)
    (94, 96): 20,
    # Section XXI - Objets d'art (Ch. 97)
    (97, 97): 21,
}

# Codes ISO des pays africains pour l'OEC
AFRICAN_COUNTRIES_OEC = {
    "DZA": {"oec_id": "afdza", "name_fr": "Algérie", "name_en": "Algeria"},
    "AGO": {"oec_id": "afago", "name_fr": "Angola", "name_en": "Angola"},
    "BEN": {"oec_id": "afben", "name_fr": "Bénin", "name_en": "Benin"},
    "BWA": {"oec_id": "afbwa", "name_fr": "Botswana", "name_en": "Botswana"},
    "BFA": {"oec_id": "afbfa", "name_fr": "Burkina Faso", "name_en": "Burkina Faso"},
    "BDI": {"oec_id": "afbdi", "name_fr": "Burundi", "name_en": "Burundi"},
    "CPV": {"oec_id": "afcpv", "name_fr": "Cap-Vert", "name_en": "Cape Verde"},
    "CMR": {"oec_id": "afcmr", "name_fr": "Cameroun", "name_en": "Cameroon"},
    "CAF": {
        "oec_id": "afcaf",
        "name_fr": "République centrafricaine",
        "name_en": "Central African Republic",
    },
    "TCD": {"oec_id": "aftcd", "name_fr": "Tchad", "name_en": "Chad"},
    "COM": {"oec_id": "afcom", "name_fr": "Comores", "name_en": "Comoros"},
    "COG": {"oec_id": "afcog", "name_fr": "Congo", "name_en": "Congo"},
    "COD": {"oec_id": "afcod", "name_fr": "RD Congo", "name_en": "DR Congo"},
    "CIV": {"oec_id": "afciv", "name_fr": "Côte d'Ivoire", "name_en": "Ivory Coast"},
    "DJI": {"oec_id": "afdji", "name_fr": "Djibouti", "name_en": "Djibouti"},
    "EGY": {"oec_id": "afegy", "name_fr": "Égypte", "name_en": "Egypt"},
    "GNQ": {"oec_id": "afgnq", "name_fr": "Guinée équatoriale", "name_en": "Equatorial Guinea"},
    "ERI": {
        "oec_id": "aferi",
        "name_fr": "Érythrée",
        "name_en": "Eritrea",
        "zlecaf_signatory": False,
        "note": "Seul membre UA non signataire de la ZLECAf",
    },
    "SWZ": {"oec_id": "afswz", "name_fr": "Eswatini", "name_en": "Eswatini"},
    "ETH": {"oec_id": "afeth", "name_fr": "Éthiopie", "name_en": "Ethiopia"},
    "GAB": {"oec_id": "afgab", "name_fr": "Gabon", "name_en": "Gabon"},
    "GMB": {"oec_id": "afgmb", "name_fr": "Gambie", "name_en": "Gambia"},
    "GHA": {"oec_id": "afgha", "name_fr": "Ghana", "name_en": "Ghana"},
    "GIN": {"oec_id": "afgin", "name_fr": "Guinée", "name_en": "Guinea"},
    "GNB": {"oec_id": "afgnb", "name_fr": "Guinée-Bissau", "name_en": "Guinea-Bissau"},
    "KEN": {"oec_id": "afken", "name_fr": "Kenya", "name_en": "Kenya"},
    "LSO": {"oec_id": "aflso", "name_fr": "Lesotho", "name_en": "Lesotho"},
    "LBR": {"oec_id": "aflbr", "name_fr": "Liberia", "name_en": "Liberia"},
    "LBY": {"oec_id": "aflby", "name_fr": "Libye", "name_en": "Libya"},
    "MDG": {"oec_id": "afmdg", "name_fr": "Madagascar", "name_en": "Madagascar"},
    "MWI": {"oec_id": "afmwi", "name_fr": "Malawi", "name_en": "Malawi"},
    "MLI": {"oec_id": "afmli", "name_fr": "Mali", "name_en": "Mali"},
    "MRT": {"oec_id": "afmrt", "name_fr": "Mauritanie", "name_en": "Mauritania"},
    "MUS": {"oec_id": "afmus", "name_fr": "Maurice", "name_en": "Mauritius"},
    "MAR": {"oec_id": "afmar", "name_fr": "Maroc", "name_en": "Morocco"},
    "MOZ": {"oec_id": "afmoz", "name_fr": "Mozambique", "name_en": "Mozambique"},
    "NAM": {"oec_id": "afnam", "name_fr": "Namibie", "name_en": "Namibia"},
    "NER": {"oec_id": "afner", "name_fr": "Niger", "name_en": "Niger"},
    "NGA": {"oec_id": "afnga", "name_fr": "Nigeria", "name_en": "Nigeria"},
    "RWA": {"oec_id": "afrwa", "name_fr": "Rwanda", "name_en": "Rwanda"},
    # RASD - République Arabe Sahraouie Démocratique
    # Membre fondateur de l'Union Africaine - Signataire de la ZLECAf
    # ATTENTION: Pas de données commerciales disponibles (territoire occupé)
    "ESH": {
        "oec_id": None,
        "name_fr": "RASD (Sahara Occidental)",
        "name_en": "Sahrawi Arab Democratic Republic",
        "has_trade_data": False,
        "zlecaf_signatory": True,
        "note": "Membre UA - Pas de statistiques commerciales",
    },
    "STP": {
        "oec_id": "afstp",
        "name_fr": "São Tomé-et-Príncipe",
        "name_en": "São Tomé and Príncipe",
    },
    "SEN": {"oec_id": "afsen", "name_fr": "Sénégal", "name_en": "Senegal"},
    "SYC": {"oec_id": "afsyc", "name_fr": "Seychelles", "name_en": "Seychelles"},
    "SLE": {"oec_id": "afsle", "name_fr": "Sierra Leone", "name_en": "Sierra Leone"},
    "SOM": {"oec_id": "afsom", "name_fr": "Somalie", "name_en": "Somalia"},
    "ZAF": {"oec_id": "afzaf", "name_fr": "Afrique du Sud", "name_en": "South Africa"},
    "SSD": {"oec_id": "afssd", "name_fr": "Soudan du Sud", "name_en": "South Sudan"},
    "SDN": {"oec_id": "afsdn", "name_fr": "Soudan", "name_en": "Sudan"},
    "TZA": {"oec_id": "aftza", "name_fr": "Tanzanie", "name_en": "Tanzania"},
    "TGO": {"oec_id": "aftgo", "name_fr": "Togo", "name_en": "Togo"},
    "TUN": {"oec_id": "aftun", "name_fr": "Tunisie", "name_en": "Tunisia"},
    "UGA": {"oec_id": "afuga", "name_fr": "Ouganda", "name_en": "Uganda"},
    "ZMB": {"oec_id": "afzmb", "name_fr": "Zambie", "name_en": "Zambia"},
    "ZWE": {"oec_id": "afzwe", "name_fr": "Zimbabwe", "name_en": "Zimbabwe"},
}


def build_trade_series(
    exports_rows: Optional[List[Dict]],
    imports_rows: Optional[List[Dict]],
    years: List[int],
) -> List[Dict]:
    """
    Agrège des lignes OEC (drilldown par année) en une série temporelle
    exports/imports/balance, une entrée par année demandée.

    Fonction pure (sans réseau) : facilite le test du parsing/agrégation.
    Les listes de lignes peuvent être None (flux absent).
    """

    def agg(rows: Optional[List[Dict]]) -> Dict[int, float]:
        totals = {y: 0.0 for y in years}
        for row in rows or []:
            year = row.get("Year")
            if year in totals:
                totals[year] += float(row.get("Trade Value") or 0)
        return totals

    exports = agg(exports_rows)
    imports = agg(imports_rows)
    series = []
    for year in years:
        exp = round(exports[year], 2)
        imp = round(imports[year], 2)
        series.append(
            {"year": year, "exports": exp, "imports": imp, "balance": round(exp - imp, 2)}
        )
    return series


class OECTradeService:
    """Service pour interroger l'API OEC"""

    def __init__(self, api_token: Optional[str] = None):
        self.api_token = api_token
        self.timeout = 30.0

        # Optional cache integration
        try:
            from services.cache_service import (
                cache_get,
                cache_get_stale,
                cache_set,
                generate_cache_key,
            )

            self._cache_get = cache_get
            self._cache_get_stale = cache_get_stale
            self._cache_set = cache_set
            self._cache_key = generate_cache_key
            self._cache_available = True
        except ImportError:
            self._cache_available = False

    async def _make_request(self, params: Dict) -> Dict:
        """Effectue une requête à l'API OEC avec mise en cache optionnelle."""
        if self.api_token:
            params["token"] = self.api_token

        # Build a stable cache key from sorted params (excluding token)
        cache_key = None
        if self._cache_available:
            cache_params = {k: v for k, v in params.items() if k != "token"}
            raw_key = json.dumps(cache_params, sort_keys=True)
            cache_key = self._cache_key("oec_request", raw_key)
            cached = self._cache_get(cache_key)
            if cached is not None:
                return cached

        def _sanitize(text: str) -> str:
            # Never let the API token leak into logs or responses (httpx error
            # strings often embed the full request URL incl. ?token=...).
            if self.api_token:
                text = text.replace(self.api_token, "***")
            return text

        def _on_failure(err: str) -> Dict:
            err = _sanitize(err)
            # Stale-on-error: serve the last cached value if OEC is down/rate-limited.
            if cache_key is not None:
                stale = self._cache_get_stale(cache_key)
                if stale is not None:
                    logger.warning("OEC unavailable (%s) — serving stale cache", err)
                    return stale
            return {"error": err, "data": []}

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.get(OEC_BASE_URL, params=params)
                response.raise_for_status()
                data = response.json()
                if self._cache_available and "error" not in data:
                    self._cache_set(cache_key, data, "oec_data")
                return data
            except httpx.HTTPStatusError as e:
                # Status code only — avoid echoing the URL (which carries the token).
                logger.error(f"OEC API error: {e.response.status_code}")
                return _on_failure(f"OEC API error {e.response.status_code}")
            except Exception as e:
                logger.error("OEC request failed: %s", _sanitize(str(e)))
                return _on_failure(str(e))

    def _build_params(
        self,
        cube: str,
        drilldowns: List[str],
        measures: List[str],
        cuts: Optional[Dict] = None,
        limit: int = 100,
    ) -> Dict:
        """Construit les paramètres de requête"""
        params = {
            "cube": cube,
            "drilldowns": ",".join(drilldowns),
            "measures": ",".join(measures),
            "limit": limit,
        }
        if cuts:
            for key, value in cuts.items():
                params[key] = value
        return params

    async def get_exports_by_product(
        self, country_iso3: str, year: int, hs_level: str = "HS4", limit: int = 50
    ) -> Dict:
        """
        Récupère les exportations d'un pays par produit avec valeur et volume.
        Utilise le cube HS17 (compatible SH2022) avec HS4 par défaut.
        HS4 offre un bon équilibre entre granularité et couverture des données.

        IMPORTANT: Récupère d'abord le total global, puis les produits détaillés.

        Args:
            country_iso3: Code ISO3 du pays (ex: "NGA" pour Nigeria)
            year: Année (ex: 2022)
            hs_level: Niveau HS (HS2, HS4, HS6) - HS4 par défaut
            limit: Nombre max de résultats à retourner
        """
        country_info = AFRICAN_COUNTRIES_OEC.get(country_iso3.upper())
        if not country_info:
            return {"error": f"Country {country_iso3} not found", "data": []}

        # 1. D'abord, récupérer le TOTAL GLOBAL des exportations (sans drilldown par produit)
        total_params = self._build_params(
            cube=OEC_CUBES[DEFAULT_CUBE],
            drilldowns=["Year", "Exporter Country"],
            measures=["Trade Value", "Quantity"],
            cuts={"Year": str(year), "Exporter Country": country_info["oec_id"]},
            limit=1,
        )
        total_result = await self._make_request(total_params)
        global_total_value = 0
        global_total_quantity = 0
        if total_result.get("data"):
            global_total_value = total_result["data"][0].get("Trade Value", 0)
            global_total_quantity = total_result["data"][0].get("Quantity", 0)

        # 2. Ensuite, récupérer les produits détaillés (avec une limite plus élevée)
        params = self._build_params(
            cube=OEC_CUBES[DEFAULT_CUBE],
            drilldowns=["Year", "Exporter Country", hs_level],
            measures=["Trade Value", "Quantity"],
            cuts={"Year": str(year), "Exporter Country": country_info["oec_id"]},
            limit=2000,  # Augmenté pour couvrir tous les produits
        )

        result = await self._make_request(params)
        return self._format_product_response(
            result,
            "exports",
            country_info,
            limit,
            global_total_value=global_total_value,
            global_total_quantity=global_total_quantity,
        )

    async def get_imports_by_product(
        self, country_iso3: str, year: int, hs_level: str = "HS4", limit: int = 50
    ) -> Dict:
        """
        Récupère les importations d'un pays par produit avec valeur et volume.
        Utilise le cube HS17 (compatible SH2022) avec HS4 par défaut.

        IMPORTANT: Récupère d'abord le total global, puis les produits détaillés.
        """
        country_info = AFRICAN_COUNTRIES_OEC.get(country_iso3.upper())
        if not country_info:
            return {"error": f"Country {country_iso3} not found", "data": []}

        # 1. D'abord, récupérer le TOTAL GLOBAL des importations (sans drilldown par produit)
        total_params = self._build_params(
            cube=OEC_CUBES[DEFAULT_CUBE],
            drilldowns=["Year", "Importer Country"],
            measures=["Trade Value", "Quantity"],
            cuts={"Year": str(year), "Importer Country": country_info["oec_id"]},
            limit=1,
        )
        total_result = await self._make_request(total_params)
        global_total_value = 0
        global_total_quantity = 0
        if total_result.get("data"):
            global_total_value = total_result["data"][0].get("Trade Value", 0)
            global_total_quantity = total_result["data"][0].get("Quantity", 0)

        # 2. Ensuite, récupérer les produits détaillés (avec une limite plus élevée)
        # Utiliser une limite de 2000 pour couvrir la plupart des cas
        params = self._build_params(
            cube=OEC_CUBES[DEFAULT_CUBE],
            drilldowns=["Year", "Importer Country", hs_level],
            measures=["Trade Value", "Quantity"],
            cuts={"Year": str(year), "Importer Country": country_info["oec_id"]},
            limit=2000,  # Augmenté pour couvrir tous les produits
        )

        result = await self._make_request(params)
        return self._format_product_response(
            result,
            "imports",
            country_info,
            limit,
            global_total_value=global_total_value,
            global_total_quantity=global_total_quantity,
        )

    def _get_hs6_prefix(self, hs_code: str) -> int:
        """
        Détermine le préfixe OEC correct basé sur le chapitre HS.
        L'API OEC utilise des préfixes différents selon la section du Système Harmonisé.
        """
        # Extraire le chapitre (2 premiers chiffres)
        chapter = int(hs_code[:2])

        # Trouver le préfixe correspondant
        for (start, end), prefix in OEC_HS6_PREFIXES.items():
            if start <= chapter <= end:
                return prefix

        # Fallback par défaut
        return 2

    def _format_oec_hs6_id(self, hs_code: str) -> str:
        """
        Formate un code HS6 pour l'API OEC.

        L'OEC utilise un format spécifique: {prefix}{6-digit-hs-code}
        Le préfixe dépend de la section HS du produit.

        Exemples:
            - 090111 (café) -> Section II (Ch.06-14) -> préfixe 2 -> 2090111
            - 180100 (cacao) -> Section IV (Ch.16-24) -> préfixe 4 -> 4180100
            - 270900 (pétrole) -> Section V (Ch.25-27) -> préfixe 5 -> 5270900
            - 710812 (or) -> Section XIV (Ch.71) -> préfixe 14 -> 14710812
            - 520100 (coton) -> Section XI (Ch.50-63) -> préfixe 11 -> 11520100
        """
        # Normaliser le code à 6 chiffres
        hs6 = hs_code.zfill(6)[:6]

        # Obtenir le préfixe basé sur le chapitre
        prefix = self._get_hs6_prefix(hs6)

        return f"{prefix}{hs6}"

    async def get_trade_by_hs_code(
        self, hs_code: str, year: int, trade_flow: str = "exports", limit: int = 50
    ) -> Dict:
        """
        Récupère les statistiques commerciales pour un code HS6 spécifique avec valeur et volume.

        Utilise le cube HS Rev. 2017 (compatible SH2022) avec des codes HS6
        pour assurer la cohérence des données.
        """
        # Normaliser le code en HS6 (ajouter des zéros si nécessaire)
        hs6_code = hs_code.zfill(6)[:6]
        if len(hs_code) == 4:
            # Si code HS4 fourni, on ajoute '00' pour avoir le code générique HS6
            hs6_code = hs_code.zfill(4) + "00"

        oec_hs_id = self._format_oec_hs6_id(hs6_code)

        if trade_flow == "exports":
            drilldowns = ["Year", "Exporter Country"]
        else:
            drilldowns = ["Year", "Importer Country"]

        # Utiliser le cube HS17 (compatible SH2022) avec HS6
        # Inclure Trade Value et Quantity (volume)
        params = self._build_params(
            cube=OEC_CUBES[DEFAULT_CUBE],
            drilldowns=drilldowns,
            measures=["Trade Value", "Quantity"],
            cuts={"Year": str(year), "HS6": oec_hs_id},
            limit=limit,
        )

        result = await self._make_request(params)
        return self._format_hs_response(result, hs6_code, year, trade_flow)

    def _filter_rows_by_level(self, rows: List[Dict], code_digits: str, level: str) -> List[Dict]:
        """
        Filtre les lignes OEC par niveau SH (agrégation explicite, sans fallback) :
        - hs2 : tout le chapitre (2 chiffres)
        - hs4 : toute la position (4 chiffres)
        - hs6 : la sous-position exacte (6 chiffres)
        L'ID OEC vaut {prefixe}{6 chiffres} → les 6 derniers caractères sont le vrai code HS6.
        """
        ndig = {"hs2": 2, "hs4": 4, "hs6": 6}.get(level, 6)
        target = code_digits[:ndig]
        out = []
        for r in rows:
            real_hs6 = str(r.get("HS6 ID", ""))[-6:]
            if real_hs6[:ndig] == target:
                out.append(r)
        return out

    def _filter_rows_by_hs(self, rows: List[Dict], oec_hs_id: str) -> List[Dict]:
        """
        Filtre les lignes OEC par code HS avec fallback progressif.
        L'API OEC ne supporte pas le filtrage par HS6 ID côté serveur —
        on filtre côté client avec dégradation HS6 → HS4 → HS2.
        """
        # Tentative 1 : correspondance exacte HS6 (ex: 5271019)
        exact = [r for r in rows if str(r.get("HS6 ID", "")) == oec_hs_id]
        if exact:
            return exact

        # Tentative 2 : préfixe HS4 (ex: 52710 pour 5271019)
        hs4_prefix = oec_hs_id[:5] if len(oec_hs_id) >= 5 else oec_hs_id
        hs4_match = [r for r in rows if str(r.get("HS6 ID", "")).startswith(hs4_prefix)]
        if hs4_match:
            return hs4_match

        # Tentative 3 : préfixe HS2 / chapitre (ex: 527 pour ch27)
        chapter_prefix = oec_hs_id[:3] if len(oec_hs_id) >= 3 else oec_hs_id
        return [r for r in rows if str(r.get("HS6 ID", "")).startswith(chapter_prefix)]

    async def get_country_hs6_history(
        self,
        country_iso3: str,
        hs_code: str,
        n_years: int = 5,
        end_year: int = DEFAULT_YEAR,
        level: str = None,
    ) -> Dict:
        """
        Retourne l'historique commercial (exports + imports) d'un pays africain pour un HS6 donné,
        sur les `n_years` dernières années disponibles (par défaut 5 ans jusqu'à `DEFAULT_YEAR`).

        Stratégie :
        - 2 requêtes seulement (exports + imports) sans filtre HS6 côté API
          (l'API OEC Tesseract ne supporte pas le filtre HS6 ID en paramètre GET)
        - Filtrage client-side par HS6 ID avec fallback HS4 → HS2
        - Agrégation par année

        Source: OEC / BACI (cube HS Rev. 2017).
        """
        iso3 = country_iso3.upper()
        country_info = AFRICAN_COUNTRIES_OEC.get(iso3)
        if not country_info:
            return {"error": f"Country {iso3} not found", "country": iso3}

        oec_id = country_info.get("oec_id")
        if not oec_id:
            return {"error": f"No OEC trade data for {iso3}", "country": iso3}

        # Normalize HS + déterminer le niveau (sh2 / sh4 / sh6)
        hs_clean = "".join(c for c in str(hs_code) if c.isdigit())
        if not hs_clean:
            return {"error": "Invalid HS code", "hs_code": hs_code}
        lvl = (level or "").lower()
        if lvl not in ("hs2", "hs4", "hs6"):
            lvl = {2: "hs2", 4: "hs4"}.get(len(hs_clean), "hs6")
        ndig = {"hs2": 2, "hs4": 4, "hs6": 6}[lvl]
        code_digits = hs_clean[:ndig].zfill(ndig)
        # Code HS6 d'affichage (complété par des zéros) + ID OEC (préfixe de section)
        hs6_code = (code_digits + "0000")[:6]
        oec_hs_id = self._format_oec_hs6_id(hs6_code)

        years = list(range(end_year - n_years + 1, end_year + 1))
        start_year = years[0]

        async def fetch_flow(flow: str) -> tuple:
            """Récupère toutes les années + tous les HS6 pour un pays/flux, filtre client-side.
            Retourne (by_year_dict, hs_labels_dict) où hs_labels_dict = {hs6_id: label}."""
            country_dim = "Exporter Country" if flow == "exports" else "Importer Country"
            params = self._build_params(
                cube=OEC_CUBES[DEFAULT_CUBE],
                drilldowns=["Year", "HS6"],
                measures=["Trade Value", "Quantity"],
                cuts={
                    country_dim: oec_id,
                    "Year": ",".join(str(y) for y in years),
                },
                limit=50000,
            )
            try:
                resp = await self._make_request(params)
                all_rows = resp.get("data") or []
                # Filtre client-side par niveau SH (sh2 chapitre / sh4 position / sh6 sous-position)
                matched = self._filter_rows_by_level(all_rows, code_digits, lvl)
                # Agrégation par année + collecte des libellés HS6
                by_year: Dict[int, Dict] = {}
                hs_labels: Dict[str, Dict] = {}  # hs6_id → {label, trade_value}
                for row in matched:
                    y = row.get("Year")
                    if y not in years:
                        continue
                    if y not in by_year:
                        by_year[y] = {"trade_value": 0.0, "quantity": 0.0}
                    tv = float(row.get("Trade Value") or 0)
                    by_year[y]["trade_value"] += tv
                    by_year[y]["quantity"] += float(row.get("Quantity") or 0)
                    # Libellé HS6
                    hid = str(row.get("HS6 ID", ""))
                    hlabel = row.get("HS6", "")
                    if hid and hlabel:
                        if hid not in hs_labels:
                            hs_labels[hid] = {"hs6_id": hid, "label": hlabel, "trade_value": 0.0}
                        hs_labels[hid]["trade_value"] += tv
                return by_year, hs_labels
            except Exception as exc:
                logger.error(f"OEC fetch_flow {flow} error: {exc}")
                return {}, {}

        # 2 requêtes en parallèle (exports + imports)
        (exports_by_year, exp_labels), (imports_by_year, imp_labels) = await asyncio.gather(
            fetch_flow("exports"),
            fetch_flow("imports"),
        )

        # Fusionner les libellés exports + imports, trier par valeur décroissante
        all_labels: Dict[str, Dict] = {}
        for hid, info in {**imp_labels, **exp_labels}.items():
            if hid not in all_labels:
                all_labels[hid] = {"hs6_id": hid, "label": info["label"], "trade_value": 0.0}
            all_labels[hid]["trade_value"] += info["trade_value"]
        hs_labels_sorted = sorted(all_labels.values(), key=lambda x: -x["trade_value"])

        # Construction des séries temporelles
        exports_data = []
        imports_data = []
        chart_rows = []
        for y in years:
            exp = exports_by_year.get(y)
            imp = imports_by_year.get(y)
            exp_val = round(exp["trade_value"], 2) if exp else 0
            exp_qty = round(exp["quantity"], 2) if exp else 0
            imp_val = round(imp["trade_value"], 2) if imp else 0
            imp_qty = round(imp["quantity"], 2) if imp else 0

            exports_data.append(
                {
                    "year": y,
                    "trade_value": exp_val,
                    "quantity": exp_qty,
                    **({"no_data": True} if not exp else {}),
                }
            )
            imports_data.append(
                {
                    "year": y,
                    "trade_value": imp_val,
                    "quantity": imp_qty,
                    **({"no_data": True} if not imp else {}),
                }
            )
            chart_rows.append(
                {
                    "year": y,
                    "exports": exp_val,
                    "imports": imp_val,
                    "balance": round(exp_val - imp_val, 2),
                }
            )

        any_exports = any(e["trade_value"] > 0 for e in exports_data)
        any_imports = any(i["trade_value"] > 0 for i in imports_data)

        # Niveau de correspondance = niveau demandé (filtrage explicite)
        match_level = lvl if hs_labels_sorted else "none"

        # Code HS4 (4 chiffres significatifs)
        hs4_code = hs6_code[:4]

        return {
            "country_iso3": iso3,
            "country_name": country_info.get("name_fr") or country_info.get("name") or iso3,
            "hs_code": hs6_code,
            "hs_query": code_digits,
            "level": lvl,
            "hs4_code": hs4_code,
            "oec_hs_id": oec_hs_id,
            "hs_labels": hs_labels_sorted,  # [{hs6_id, label, trade_value}, ...]
            "match_level": match_level,  # "hs6" | "hs4" | "hs2" | "none"
            "years": years,
            "exports": exports_data,
            "imports": imports_data,
            "chart_rows": chart_rows,
            "source": "OEC / BACI (HS Rev. 2017)",
            "currency": "USD",
            "has_data": any_exports or any_imports,
        }

    async def get_country_trade_series(
        self,
        country_iso3: str,
        start_year: int = 2018,
        end_year: int = DEFAULT_YEAR,
    ) -> Dict:
        """
        Série temporelle du commerce total (tous produits) d'un pays africain:
        exports, imports et balance par année sur la plage `start_year..end_year`.

        Deux requêtes seulement (exports + imports), drilldown par année — l'OEC
        agrège sur tous les produits. Source: OEC / BACI (cube HS Rev. 2017).
        """
        iso3 = country_iso3.upper()
        country_info = AFRICAN_COUNTRIES_OEC.get(iso3)
        if not country_info:
            return {"error": f"Country {iso3} not found", "country": iso3}
        oec_id = country_info.get("oec_id")
        if not oec_id:
            return {"error": f"No OEC trade data for {iso3}", "country": iso3}

        if end_year < start_year:
            start_year, end_year = end_year, start_year
        years = list(range(start_year, end_year + 1))

        async def fetch_flow(flow: str) -> List[Dict]:
            country_dim = "Exporter Country" if flow == "exports" else "Importer Country"
            params = self._build_params(
                cube=OEC_CUBES[DEFAULT_CUBE],
                drilldowns=["Year"],
                measures=["Trade Value"],
                cuts={country_dim: oec_id, "Year": ",".join(str(y) for y in years)},
                limit=1000,
            )
            try:
                resp = await self._make_request(params)
                return resp.get("data") or []
            except Exception as exc:
                logger.error(f"OEC trade series {flow} error: {exc}")
                return []

        exports_rows, imports_rows = await asyncio.gather(
            fetch_flow("exports"),
            fetch_flow("imports"),
        )
        chart_rows = build_trade_series(exports_rows, imports_rows, years)

        return {
            "country_iso3": iso3,
            "country_name": country_info.get("name_fr") or country_info.get("name") or iso3,
            "years": years,
            "chart_rows": chart_rows,
            "source": "OEC / BACI (HS Rev. 2017)",
            "currency": "USD",
            "has_data": any(r["exports"] > 0 or r["imports"] > 0 for r in chart_rows),
        }

    async def get_bilateral_trade(
        self,
        exporter_iso3: str,
        importer_iso3: str,
        year: int,
        hs_level: str = "HS4",
        limit: int = 50,
    ) -> Dict:
        """
        Récupère le commerce bilatéral entre deux pays avec valeur et volume.
        Utilise le cube HS17 (compatible SH2022) avec HS4 par défaut.

        IMPORTANT: On récupère 500 produits de l'API pour avoir tous les produits
        y compris les produits énergétiques (pétrole, gaz), puis on trie et limite.
        """
        exporter_info = AFRICAN_COUNTRIES_OEC.get(exporter_iso3.upper())
        importer_info = AFRICAN_COUNTRIES_OEC.get(importer_iso3.upper())

        if not exporter_info:
            return {"error": f"Exporter country {exporter_iso3} not found", "data": []}
        if not importer_info:
            return {"error": f"Importer country {importer_iso3} not found", "data": []}

        # Récupérer TOUS les produits (500) pour avoir une vue complète
        # incluant les produits énergétiques qui peuvent être loin dans la liste
        params = self._build_params(
            cube=OEC_CUBES[DEFAULT_CUBE],
            drilldowns=["Year", "Exporter Country", "Importer Country", hs_level],
            measures=["Trade Value", "Quantity"],
            cuts={
                "Year": str(year),
                "Exporter Country": exporter_info["oec_id"],
                "Importer Country": importer_info["oec_id"],
            },
            limit=500,  # Récupérer plus de données pour avoir tous les produits importants
        )

        result = await self._make_request(params)
        return self._format_bilateral_response(result, exporter_info, importer_info, year, limit)

    async def get_available_years(self) -> List[int]:
        """Retourne les années disponibles dans l'API pour le cube HS17"""
        # Le cube HS Rev. 2017 couvre 2018-2024
        return list(range(2018, 2025))

    async def get_top_african_exporters(self, hs_code: str, year: int, limit: int = 20) -> Dict:
        """
        Récupère les principaux exportateurs africains pour un produit.
        Utilise le cube HS17 avec des codes HS6 pour la cohérence SH2022.
        """
        # Normaliser le code en HS6
        hs6_code = hs_code.zfill(6)[:6]
        if len(hs_code) == 4:
            hs6_code = hs_code.zfill(4) + "00"

        oec_hs_id = self._format_oec_hs6_id(hs6_code)

        params = self._build_params(
            cube=OEC_CUBES[DEFAULT_CUBE],
            drilldowns=["Year", "Exporter Country"],
            measures=["Trade Value"],
            cuts={"Year": str(year), "HS6": oec_hs_id},
            limit=200,  # Get more to filter African countries
        )

        result = await self._make_request(params)

        # Filter only African countries
        african_oec_ids = {v["oec_id"] for v in AFRICAN_COUNTRIES_OEC.values()}
        african_data = []

        for row in result.get("data", []):
            country_id = row.get("Exporter Country ID", "")
            if country_id in african_oec_ids:
                african_data.append(row)

        # Sort by trade value
        african_data.sort(key=lambda x: x.get("Trade Value", 0), reverse=True)

        return {
            "hs_code": hs_code,
            "year": year,
            "total_countries": len(african_data),
            "data": african_data[:limit],
            "source": "OEC/BACI",
        }

    async def get_top_african_importers(self, hs_code: str, year: int, limit: int = 54) -> Dict:
        """
        Principaux IMPORTATEURS africains d'un produit — miroir de
        ``get_top_african_exporters``. UNE seule requête (cut HS6, drilldown
        Importer Country) sur le canal OEC gratuit du module Statistiques,
        avec son cache — remplace le fan-out 54 pays du module Opportunités.
        """
        hs6_code = hs_code.zfill(6)[:6]
        if len(hs_code) == 4:
            hs6_code = hs_code.zfill(4) + "00"

        oec_hs_id = self._format_oec_hs6_id(hs6_code)

        params = self._build_params(
            cube=OEC_CUBES[DEFAULT_CUBE],
            drilldowns=["Year", "Importer Country"],
            measures=["Trade Value"],
            cuts={"Year": str(year), "HS6": oec_hs_id},
            limit=200,
        )

        result = await self._make_request(params)

        african_by_oec_id = {
            v["oec_id"]: (iso3, v) for iso3, v in AFRICAN_COUNTRIES_OEC.items() if v.get("oec_id")
        }
        african_data = []
        for row in result.get("data", []):
            hit = african_by_oec_id.get(row.get("Importer Country ID", ""))
            if not hit:
                continue
            iso3, info = hit
            value = row.get("Trade Value") or 0
            if value > 0:
                african_data.append(
                    {
                        "country_iso3": iso3,
                        "country_name": info.get("name_fr") or info.get("name_en") or iso3,
                        "hs_code": hs6_code,
                        "import_value": value,
                    }
                )

        african_data.sort(key=lambda x: x["import_value"], reverse=True)
        return {
            "hs_code": hs_code,
            "year": year,
            "total_countries": len(african_data),
            "data": african_data[:limit],
            "source": "OEC/BACI (canal gratuit du module Statistiques)",
        }

    def _format_product_response(
        self,
        result: Dict,
        flow: str,
        country_info: Dict,
        limit: int = 50,
        global_total_value: float = 0,
        global_total_quantity: float = 0,
    ) -> Dict:
        """
        Formate la réponse pour les produits, triée par valeur décroissante.

        Args:
            result: Résultat de la requête OEC
            flow: Type de flux ('exports' ou 'imports')
            country_info: Informations sur le pays
            limit: Nombre de produits à retourner
            global_total_value: Total global des échanges (calculé séparément)
            global_total_quantity: Quantité totale globale
        """
        data = result.get("data", [])

        # Trier par Trade Value décroissante
        sorted_data = sorted(data, key=lambda x: x.get("Trade Value", 0), reverse=True)

        # Limiter au nombre demandé pour l'affichage
        limited_data = sorted_data[:limit]

        # Calculer les totaux des données récupérées (pour comparaison)
        fetched_total_value = sum(row.get("Trade Value", 0) for row in sorted_data)
        fetched_total_quantity = sum(row.get("Quantity", 0) for row in sorted_data)

        # Utiliser le total global s'il est disponible, sinon utiliser le total calculé
        final_total_value = global_total_value if global_total_value > 0 else fetched_total_value
        final_total_quantity = (
            global_total_quantity if global_total_quantity > 0 else fetched_total_quantity
        )

        return {
            "country": country_info,
            "trade_flow": flow,
            "total_products": len(sorted_data),
            "total_products_displayed": len(limited_data),
            "total_value": final_total_value,  # Total GLOBAL (valeur correcte)
            "total_value_fetched": fetched_total_value,  # Total des données récupérées (pour debug)
            "total_quantity": final_total_quantity,
            "quantity_unit": "tonnes",
            "currency": "USD",
            "data": limited_data,
            "source": "OEC/BACI",
            "retrieved_at": datetime.utcnow().isoformat(),
        }

    def _format_hs_response(self, result: Dict, hs_code: str, year: int, flow: str) -> Dict:
        """Formate la réponse pour un code HS, triée par valeur décroissante"""
        data = result.get("data", [])

        # Trier par Trade Value décroissante
        sorted_data = sorted(data, key=lambda x: x.get("Trade Value", 0), reverse=True)

        # Calculer le volume total
        total_quantity = sum(row.get("Quantity", 0) for row in sorted_data)

        return {
            "hs_code": hs_code,
            "year": year,
            "trade_flow": flow,
            "total_countries": len(sorted_data),
            "total_value": sum(row.get("Trade Value", 0) for row in sorted_data),
            "total_quantity": total_quantity,
            "quantity_unit": "tonnes",
            "currency": "USD",
            "data": sorted_data,
            "source": "OEC/BACI",
            "retrieved_at": datetime.utcnow().isoformat(),
        }

    def _format_bilateral_response(
        self, result: Dict, exporter: Dict, importer: Dict, year: int, limit: int = 50
    ) -> Dict:
        """Formate la réponse pour le commerce bilatéral, triée par valeur décroissante"""
        data = result.get("data", [])

        # Trier par Trade Value décroissante pour avoir les produits les plus importants en premier
        sorted_data = sorted(data, key=lambda x: x.get("Trade Value", 0), reverse=True)

        # Calculer les totaux sur TOUTES les données (avant limitation)
        total_value = sum(row.get("Trade Value", 0) for row in sorted_data)
        total_quantity = sum(row.get("Quantity", 0) for row in sorted_data)

        # Limiter au nombre demandé APRÈS le tri
        limited_data = sorted_data[:limit]

        return {
            "exporter": exporter,
            "importer": importer,
            "year": year,
            "total_products": len(sorted_data),  # Nombre total de produits
            "displayed_products": len(limited_data),  # Nombre affiché
            "total_value": total_value,
            "total_quantity": total_quantity,
            "quantity_unit": "tonnes",
            "currency": "USD",
            "data": limited_data,
            "source": "OEC/BACI",
            "retrieved_at": datetime.utcnow().isoformat(),
        }

    async def get_revealed_comparative_advantage(
        self,
        country_iso3: str,
        year: int,
        hs_level: str = "HS4",
        limit: int = 30,
    ) -> Dict:
        """
        Calcule l'avantage comparatif révélé (RCA, indice de Balassa) d'un pays
        pour chaque produit, à un niveau SH choisi (HS2, HS4 ou HS6).

        RCA = (X_cp / X_c) / (X_wp / X_w)
          X_cp = exportations du produit p par le pays c
          X_c  = exportations totales du pays c
          X_wp = exportations mondiales du produit p
          X_w  = exportations mondiales totales

        RCA > 1 ⇒ le pays est relativement spécialisé (avantage révélé) dans p.

        2 appels API: exports du pays par produit + exports mondiaux par produit
        (même niveau SH), tous deux mis en cache.
        """
        if hs_level not in ("HS2", "HS4", "HS6"):
            return {"error": f"Invalid hs_level '{hs_level}' (HS2, HS4, HS6)"}

        country_info = AFRICAN_COUNTRIES_OEC.get(country_iso3.upper())
        if not country_info:
            return {"error": f"Country {country_iso3} not found", "data": []}

        # 1) Exports du pays par produit (X_cp) + total pays (X_c)
        country_resp = await self.get_exports_by_product(
            country_iso3, year, hs_level=hs_level, limit=5000
        )
        if "error" in country_resp:
            return {"error": country_resp["error"], "data": []}
        country_rows = country_resp.get("data", [])
        x_c = country_resp.get("total_value", 0) or sum(
            r.get("Trade Value", 0) for r in country_rows
        )
        if not x_c or not country_rows:
            return {"error": "No export data for this country/year", "data": []}

        # 2) Exports mondiaux par produit (X_wp) + total monde (X_w)
        world_params = self._build_params(
            cube=OEC_CUBES[DEFAULT_CUBE],
            drilldowns=["Year", hs_level],
            measures=["Trade Value"],
            cuts={"Year": str(year)},
            limit=10000,
        )
        world_result = await self._make_request(world_params)
        if "error" in world_result:
            return {"error": world_result["error"], "data": []}
        world_rows = world_result.get("data", [])
        id_field = f"{hs_level} ID"
        world_by_id = {}
        x_w = 0
        for r in world_rows:
            val = r.get("Trade Value", 0) or 0
            x_w += val
            wid = r.get(id_field)
            if wid is not None:
                world_by_id[wid] = world_by_id.get(wid, 0) + val
        if not x_w:
            return {"error": "No world export data for this year", "data": []}

        # 3) Calcul du RCA par produit
        results = []
        for r in country_rows:
            x_cp = r.get("Trade Value", 0) or 0
            if x_cp <= 0:
                continue
            pid = r.get(id_field)
            x_wp = world_by_id.get(pid, 0)
            if x_wp <= 0:
                continue
            rca = (x_cp / x_c) / (x_wp / x_w)
            results.append(
                {
                    "hs_code": str(pid)[-int(hs_level[2:]) :] if pid is not None else "",
                    "product": r.get(hs_level, ""),
                    "country_value": x_cp,
                    "country_share": (x_cp / x_c) * 100,
                    "world_share": (x_wp / x_w) * 100,
                    "rca": round(rca, 3),
                    "has_advantage": rca >= 1,
                }
            )

        # Trier par RCA décroissant (produits les plus spécialisés en premier)
        results.sort(key=lambda x: x["rca"], reverse=True)
        advantage_count = sum(1 for r in results if r["has_advantage"])

        return {
            "country": country_info,
            "year": year,
            "hs_level": hs_level,
            "total_exports": x_c,
            "world_exports": x_w,
            "total_products": len(results),
            "products_with_advantage": advantage_count,
            "currency": "USD",
            "data": results[:limit],
            "methodology": "Balassa RCA = (Xcp/Xc)/(Xwp/Xw); RCA>1 = avantage comparatif révélé",
            "source": "OEC/BACI",
            "retrieved_at": datetime.utcnow().isoformat(),
        }

    async def get_trade_complementarity(
        self,
        exporter_iso3: str,
        importer_iso3: str,
        year: int,
        hs_level: str = "HS4",
        limit: int = 20,
    ) -> Dict:
        """
        Indice de complémentarité commerciale (TCI) entre un exportateur i et un
        importateur j, à un niveau SH choisi (HS2, HS4 ou HS6).

        TCI_ij = 100 * (1 - Σ_k |m_jk - x_ik| / 2)
          x_ik = part du produit k dans les exportations de i
          m_jk = part du produit k dans les importations de j

        TCI ∈ [0, 100]. Plus il est élevé, plus le profil d'export de i
        correspond au profil d'import de j ⇒ fort potentiel d'échange (utile
        pour évaluer le potentiel commercial intra-ZLECAf).

        2 appels API mis en cache : exports de i + imports de j (même niveau SH).
        """
        if hs_level not in ("HS2", "HS4", "HS6"):
            return {"error": f"Invalid hs_level '{hs_level}' (HS2, HS4, HS6)"}

        exp_info = AFRICAN_COUNTRIES_OEC.get(exporter_iso3.upper())
        imp_info = AFRICAN_COUNTRIES_OEC.get(importer_iso3.upper())
        if not exp_info:
            return {"error": f"Exporter country {exporter_iso3} not found"}
        if not imp_info:
            return {"error": f"Importer country {importer_iso3} not found"}

        exp_resp = await self.get_exports_by_product(
            exporter_iso3, year, hs_level=hs_level, limit=5000
        )
        if "error" in exp_resp:
            return {"error": exp_resp["error"]}
        imp_resp = await self.get_imports_by_product(
            importer_iso3, year, hs_level=hs_level, limit=5000
        )
        if "error" in imp_resp:
            return {"error": imp_resp["error"]}

        id_field = f"{hs_level} ID"
        x_total = exp_resp.get("total_value", 0) or sum(
            r.get("Trade Value", 0) for r in exp_resp.get("data", [])
        )
        m_total = imp_resp.get("total_value", 0) or sum(
            r.get("Trade Value", 0) for r in imp_resp.get("data", [])
        )
        if not x_total or not m_total:
            return {"error": "Insufficient export/import data for this selection"}

        # Parts par produit + libellés
        x_share, m_share, labels = {}, {}, {}
        for r in exp_resp.get("data", []):
            pid = r.get(id_field)
            if pid is None:
                continue
            x_share[pid] = x_share.get(pid, 0) + (r.get("Trade Value", 0) or 0) / x_total
            labels.setdefault(pid, r.get(hs_level, ""))
        for r in imp_resp.get("data", []):
            pid = r.get(id_field)
            if pid is None:
                continue
            m_share[pid] = m_share.get(pid, 0) + (r.get("Trade Value", 0) or 0) / m_total
            labels.setdefault(pid, r.get(hs_level, ""))

        # TCI
        all_ids = set(x_share) | set(m_share)
        disparity = sum(abs(m_share.get(k, 0) - x_share.get(k, 0)) for k in all_ids)
        tci = 100 * (1 - disparity / 2)

        # Opportunités : produits où i exporte ET j importe (recouvrement offre/demande)
        opportunities = []
        for k in set(x_share) & set(m_share):
            xs, ms = x_share[k], m_share[k]
            opportunities.append(
                {
                    "hs_code": str(k)[-int(hs_level[2:]) :],
                    "product": labels.get(k, ""),
                    "exporter_export_share": round(xs * 100, 2),
                    "importer_import_share": round(ms * 100, 2),
                    "match_score": round(min(xs, ms) * 100, 2),
                }
            )
        opportunities.sort(key=lambda o: o["match_score"], reverse=True)

        return {
            "exporter": exp_info,
            "importer": imp_info,
            "year": year,
            "hs_level": hs_level,
            "tci": round(tci, 1),
            "matching_products": len(opportunities),
            "top_opportunities": opportunities[:limit],
            "methodology": "TCI = 100·(1 − Σ|m_jk − x_ik|/2). TCI élevé ⇒ profil d'export de i compatible avec le profil d'import de j.",
            "source": "OEC/BACI",
            "retrieved_at": datetime.utcnow().isoformat(),
        }

    async def get_africa_totals(self, year: int) -> Dict:
        """
        Récupère les totaux d'exportations et d'importations pour toute l'Afrique.
        Fait une requête agrégée à l'API OEC pour tous les pays africains.

        Args:
            year: Année des données

        Returns:
            Totaux des exports et imports africains
        """
        try:
            # Construire la liste des IDs OEC pour tous les pays africains
            african_ids = [info["oec_id"] for info in AFRICAN_COUNTRIES_OEC.values()]

            # Requête pour les exportations totales africaines
            exports_params = self._build_params(
                cube=OEC_CUBES[DEFAULT_CUBE],
                drilldowns=["Year", "Exporter Country"],
                measures=["Trade Value", "Quantity"],
                cuts={
                    "Year": str(year),
                },
                limit=100,
            )
            exports_result = await self._make_request(exports_params)

            # Filtrer et sommer uniquement les pays africains
            total_exports = 0
            total_exports_qty = 0
            exports_by_country = []
            for row in exports_result.get("data", []):
                country_id = row.get("Exporter Country ID", "")
                if country_id in african_ids:
                    value = row.get("Trade Value", 0)
                    qty = row.get("Quantity", 0)
                    total_exports += value
                    total_exports_qty += qty
                    exports_by_country.append(
                        {
                            "country_id": country_id,
                            "country_name": row.get("Exporter Country", ""),
                            "value": value,
                            "quantity": qty,
                        }
                    )

            # Requête pour les importations totales africaines
            imports_params = self._build_params(
                cube=OEC_CUBES[DEFAULT_CUBE],
                drilldowns=["Year", "Importer Country"],
                measures=["Trade Value", "Quantity"],
                cuts={
                    "Year": str(year),
                },
                limit=100,
            )
            imports_result = await self._make_request(imports_params)

            # Filtrer et sommer uniquement les pays africains
            total_imports = 0
            total_imports_qty = 0
            imports_by_country = []
            for row in imports_result.get("data", []):
                country_id = row.get("Importer Country ID", "")
                if country_id in african_ids:
                    value = row.get("Trade Value", 0)
                    qty = row.get("Quantity", 0)
                    total_imports += value
                    total_imports_qty += qty
                    imports_by_country.append(
                        {
                            "country_id": country_id,
                            "country_name": row.get("Importer Country", ""),
                            "value": value,
                            "quantity": qty,
                        }
                    )

            # Trier par valeur décroissante
            exports_by_country.sort(key=lambda x: x["value"], reverse=True)
            imports_by_country.sort(key=lambda x: x["value"], reverse=True)

            return {
                "year": year,
                "total_exports": total_exports,
                "total_imports": total_imports,
                "total_exports_quantity": total_exports_qty,
                "total_imports_quantity": total_imports_qty,
                "exports_billions": round(total_exports / 1e9, 2),
                "imports_billions": round(total_imports / 1e9, 2),
                "trade_balance": total_exports - total_imports,
                "top_10_exporters": exports_by_country[:10],
                "top_10_importers": imports_by_country[:10],
                "total_countries_with_data": len(exports_by_country),
                "currency": "USD",
                "source": "OEC/BACI",
                "retrieved_at": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Error getting Africa totals: {str(e)}")
            return {"error": str(e)}


# Instance globale du service
oec_service = OECTradeService()


# Fonctions utilitaires pour l'API
async def get_country_exports(country_iso3: str, year: int, limit: int = 50) -> Dict:
    """Raccourci pour obtenir les exports d'un pays"""
    return await oec_service.get_exports_by_product(country_iso3, year, limit=limit)


async def get_country_imports(country_iso3: str, year: int, limit: int = 50) -> Dict:
    """Raccourci pour obtenir les imports d'un pays"""
    return await oec_service.get_imports_by_product(country_iso3, year, limit=limit)


async def get_product_trade_stats(hs_code: str, year: int, flow: str = "exports") -> Dict:
    """Raccourci pour obtenir les stats d'un produit"""
    return await oec_service.get_trade_by_hs_code(hs_code, year, flow)


async def get_african_top_exporters(hs_code: str, year: int, limit: int = 10) -> Dict:
    """Raccourci pour obtenir les top exportateurs africains"""
    return await oec_service.get_top_african_exporters(hs_code, year, limit)


def get_african_countries_list(language: str = "fr") -> List[Dict]:
    """Retourne la liste des pays africains avec leurs codes, triés correctement"""
    import unicodedata

    def normalize_for_sort(text: str) -> str:
        """Normalise le texte pour le tri (retire les accents)"""
        return "".join(
            c for c in unicodedata.normalize("NFD", text.lower()) if unicodedata.category(c) != "Mn"
        )

    name_key = f"name_{language}"
    return [
        {
            "iso3": iso3,
            "oec_id": info.get("oec_id"),
            "name": info.get(name_key, info["name_en"]),
            "has_trade_data": info.get("has_trade_data", True),
            "zlecaf_signatory": info.get("zlecaf_signatory", True),
            "note": info.get("note", ""),
        }
        for iso3, info in sorted(
            AFRICAN_COUNTRIES_OEC.items(), key=lambda x: normalize_for_sort(x[1].get(name_key, ""))
        )
    ]


def get_country_name_to_iso3_mapping() -> Dict[str, str]:
    """
    Crée un mapping inversé des noms de pays (name_en) vers ISO3.
    Utile pour le frontend qui reçoit des noms de pays de l'API OEC
    et doit les convertir en codes ISO3 pour afficher les drapeaux.

    The mapping keys use the "name_en" field from AFRICAN_COUNTRIES_OEC entries.

    Inclut également des variantes de noms pour une meilleure compatibilité
    avec les différentes représentations possibles des noms de pays dans l'API OEC.

    Returns:
        Dict[str, str]: Mapping of country names to ISO3 codes
    """
    mapping = {}

    for iso3, info in AFRICAN_COUNTRIES_OEC.items():
        # Nom principal en anglais
        name_en = info["name_en"]
        mapping[name_en] = iso3

        # Ajouter des variantes communes pour certains pays
        # Ces variantes sont nécessaires car l'API OEC peut retourner des noms différents
        if iso3 == "COG":
            # Congo peut être "Congo" ou "Republic of the Congo"
            mapping["Republic of the Congo"] = iso3
        elif iso3 == "COD":
            # DR Congo peut avoir plusieurs variantes
            mapping["Democratic Republic of the Congo"] = iso3
            mapping["Congo, Dem. Rep."] = iso3
        elif iso3 == "CIV":
            # Côte d'Ivoire peut apparaître avec ou sans accents (name_en est "Ivory Coast")
            mapping["Cote d'Ivoire"] = iso3
            mapping["Côte d'Ivoire"] = iso3
        elif iso3 == "STP":
            # São Tomé avec et sans accents
            mapping["Sao Tome and Principe"] = iso3

    return mapping
