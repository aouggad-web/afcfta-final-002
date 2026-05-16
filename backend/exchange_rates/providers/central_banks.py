"""
African Central Banks provider – scraping des sites officiels des banques centrales.

Sources officielles par devise :
  DZD – Banque d'Algérie          https://www.bank-of-algeria.dz
  MAD – Bank Al-Maghrib            https://www.bkam.ma
  TND – Banque Centrale de Tunisie https://www.bct.gov.tn
  EGP – Central Bank of Egypt      https://www.cbe.org.eg
  NGN – Central Bank of Nigeria    https://www.cbn.gov.ng
  GHS – Bank of Ghana              https://www.bog.gov.gh
  KES – Central Bank of Kenya      https://www.centralbank.go.ke
  ETB – National Bank of Ethiopia  https://www.nbe.gov.et
  TZS – Bank of Tanzania           https://www.bot.go.tz
  UGX – Bank of Uganda             https://www.bou.or.ug
  XOF – BCEAO (parité fixe EUR)    https://www.bceao.int
  XAF – BEAC  (parité fixe EUR)    https://www.beac.int
  ZAR – SARB                       https://www.resbank.co.za
  MAD, DZD, TND – aussi via IMF IFS https://www.imf.org

Stratégie :
  1. Pour XAF et XOF : parité fixe connue (1 EUR = 655.957 CFA), calcul via EUR/USD.
  2. Pour les autres : tentative de scraping du site officiel → fallback IMF si échec.
  3. Seules les devises réellement récupérées sont incluses dans le résultat
     (pas de données inventées).
"""
import logging
import re
from typing import Dict, Optional

import requests
from bs4 import BeautifulSoup

from .base import BaseRateProvider

logger = logging.getLogger(__name__)

_TIMEOUT = 15
_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "fr-FR,fr;q=0.9,en-US;q=0.8",
}

# CFA peg: both XAF and XOF are pegged to EUR at exactly 655.957
_CFA_EUR_PEG = 655.957


def _safe_float(text: str) -> Optional[float]:
    """Parse a float from a string, ignoring spaces and commas."""
    if not text:
        return None
    cleaned = re.sub(r"[^\d.,]", "", text.strip()).replace(",", ".")
    # If there are multiple dots keep only the last one as decimal separator
    parts = cleaned.split(".")
    if len(parts) > 2:
        cleaned = "".join(parts[:-1]) + "." + parts[-1]
    try:
        return float(cleaned)
    except ValueError:
        return None


# ---------------------------------------------------------------------------
# Banque d'Algérie – DZD
# ---------------------------------------------------------------------------

def _fetch_dzd(eur_usd_rate: Optional[float] = None) -> Optional[float]:
    """
    Fetch official USD/DZD rate from Banque d'Algérie.
    Returns DZD per 1 USD, or None if unavailable.
    """
    # The Banque d'Algérie publishes its daily bulletin at:
    # https://www.bank-of-algeria.dz/html/taux_de_change.htm
    urls = [
        "https://www.bank-of-algeria.dz/html/taux_de_change.htm",
        "https://www.bank-of-algeria.dz/",
    ]
    for url in urls:
        try:
            resp = requests.get(url, timeout=_TIMEOUT, headers=_HEADERS)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")
            # Look for USD rate in tables
            for table in soup.find_all("table"):
                rows = table.find_all("tr")
                for row in rows:
                    cells = [c.get_text(strip=True) for c in row.find_all(["td", "th"])]
                    # Match row containing USD
                    if any("USD" in c or "Dollar" in c or "dollar" in c for c in cells):
                        # Try to find a rate value in the row
                        for cell in cells:
                            rate = _safe_float(cell)
                            if rate and 50 < rate < 600:  # DZD/USD plausible range
                                logger.info("BNA: DZD/USD = %.4f (from %s)", rate, url)
                                return rate
        except Exception as exc:
            logger.debug("BNA scraping failed (%s): %s", url, exc)

    # Fallback: try IMF data page for DZD
    try:
        imf_url = "https://www.imf.org/external/np/fin/data/rms_five.aspx"
        resp = requests.get(imf_url, timeout=_TIMEOUT, headers=_HEADERS)
        soup = BeautifulSoup(resp.text, "html.parser")
        for row in soup.find_all("tr"):
            cells = [c.get_text(strip=True) for c in row.find_all(["td", "th"])]
            if any("Algeria" in c or "Algerian" in c for c in cells):
                for cell in cells:
                    rate = _safe_float(cell)
                    if rate and 50 < rate < 600:
                        logger.info("IMF: DZD/USD = %.4f", rate)
                        return rate
    except Exception as exc:
        logger.debug("IMF DZD fallback failed: %s", exc)

    return None


# ---------------------------------------------------------------------------
# Bank Al-Maghrib – MAD
# ---------------------------------------------------------------------------

def _fetch_mad() -> Optional[float]:
    """
    Fetch official USD/MAD rate from Bank Al-Maghrib (BAM).
    Returns MAD per 1 USD.
    """
    # BAM publishes daily rates in JSON format
    bam_api_urls = [
        "https://www.bkam.ma/api/market/exchange-rates",
        "https://www.bkam.ma/Marchés/Principaux-indicateurs/Marché-des-changes/Cours-de-change/Cours-quotidiens",
    ]
    for url in bam_api_urls:
        try:
            resp = requests.get(url, timeout=_TIMEOUT, headers=_HEADERS)
            resp.raise_for_status()
            # Try JSON first
            try:
                data = resp.json()
                # BAM JSON might have currency array
                if isinstance(data, list):
                    for item in data:
                        code = str(item.get("code", item.get("currency", ""))).upper()
                        if "USD" in code or "Dollar" in str(item):
                            rate = item.get("rate") or item.get("value") or item.get("cours")
                            if rate:
                                r = _safe_float(str(rate))
                                if r and 5 < r < 30:  # MAD/USD plausible
                                    logger.info("BAM JSON: MAD/USD = %.4f", r)
                                    return r
                elif isinstance(data, dict):
                    rates = data.get("rates", data.get("data", {}))
                    if isinstance(rates, dict):
                        usd = rates.get("USD")
                        if usd:
                            r = _safe_float(str(usd))
                            if r and 5 < r < 30:
                                return r
            except Exception:
                pass
            # Try HTML scraping
            soup = BeautifulSoup(resp.text, "html.parser")
            for table in soup.find_all("table"):
                for row in table.find_all("tr"):
                    cells = [c.get_text(strip=True) for c in row.find_all(["td", "th"])]
                    if any("USD" in c or "Dollar" in c for c in cells):
                        for cell in cells:
                            r = _safe_float(cell)
                            if r and 5 < r < 30:
                                logger.info("BAM HTML: MAD/USD = %.4f", r)
                                return r
        except Exception as exc:
            logger.debug("BAM scraping failed (%s): %s", url, exc)
    return None


# ---------------------------------------------------------------------------
# Banque Centrale de Tunisie – TND
# ---------------------------------------------------------------------------

def _fetch_tnd() -> Optional[float]:
    """
    Fetch official USD/TND rate from BCT.
    Returns TND per 1 USD.
    """
    urls = [
        "https://www.bct.gov.tn/bct/siteprod/english/cours/cours.jsp",
        "https://www.bct.gov.tn/bct/siteprod/cours/cours.jsp",
    ]
    for url in urls:
        try:
            resp = requests.get(url, timeout=_TIMEOUT, headers=_HEADERS)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")
            for table in soup.find_all("table"):
                for row in table.find_all("tr"):
                    cells = [c.get_text(strip=True) for c in row.find_all(["td", "th"])]
                    if any("USD" in c or "Dollar" in c for c in cells):
                        for cell in cells:
                            r = _safe_float(cell)
                            if r and 1.5 < r < 6:  # TND/USD plausible
                                logger.info("BCT: TND/USD = %.4f", r)
                                return r
        except Exception as exc:
            logger.debug("BCT scraping failed (%s): %s", url, exc)
    return None


# ---------------------------------------------------------------------------
# Central Bank of Egypt – EGP
# ---------------------------------------------------------------------------

def _fetch_egp() -> Optional[float]:
    """Fetch EGP/USD from CBE. Returns EGP per 1 USD."""
    urls = [
        "https://www.cbe.org.eg/en/EconomicResearch/Statistics/Pages/ExchangeRatesListing.aspx",
    ]
    for url in urls:
        try:
            resp = requests.get(url, timeout=_TIMEOUT, headers=_HEADERS)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")
            for table in soup.find_all("table"):
                for row in table.find_all("tr"):
                    cells = [c.get_text(strip=True) for c in row.find_all(["td", "th"])]
                    if any("USD" in c or "Dollar" in c for c in cells):
                        for cell in cells:
                            r = _safe_float(cell)
                            if r and 20 < r < 100:  # EGP/USD plausible
                                logger.info("CBE: EGP/USD = %.4f", r)
                                return r
        except Exception as exc:
            logger.debug("CBE scraping failed (%s): %s", url, exc)
    return None


# ---------------------------------------------------------------------------
# Central Bank of Kenya – KES
# ---------------------------------------------------------------------------

def _fetch_kes() -> Optional[float]:
    """Fetch KES/USD from CBK. Returns KES per 1 USD."""
    try:
        url = "https://www.centralbank.go.ke/exchange-rates/"
        resp = requests.get(url, timeout=_TIMEOUT, headers=_HEADERS)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        for table in soup.find_all("table"):
            for row in table.find_all("tr"):
                cells = [c.get_text(strip=True) for c in row.find_all(["td", "th"])]
                if any("USD" in c or "Dollar" in c for c in cells):
                    for cell in cells:
                        r = _safe_float(cell)
                        if r and 80 < r < 200:  # KES/USD plausible
                            logger.info("CBK: KES/USD = %.4f", r)
                            return r
    except Exception as exc:
        logger.debug("CBK scraping failed: %s", exc)
    return None


# ---------------------------------------------------------------------------
# National Bank of Ethiopia – ETB
# ---------------------------------------------------------------------------

def _fetch_etb() -> Optional[float]:
    """Fetch ETB/USD from NBE. Returns ETB per 1 USD."""
    try:
        url = "https://www.nbe.gov.et/forex/"
        resp = requests.get(url, timeout=_TIMEOUT, headers=_HEADERS)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        for table in soup.find_all("table"):
            for row in table.find_all("tr"):
                cells = [c.get_text(strip=True) for c in row.find_all(["td", "th"])]
                if any("USD" in c or "Dollar" in c for c in cells):
                    for cell in cells:
                        r = _safe_float(cell)
                        if r and 30 < r < 200:  # ETB/USD plausible
                            logger.info("NBE: ETB/USD = %.4f", r)
                            return r
    except Exception as exc:
        logger.debug("NBE scraping failed: %s", exc)
    return None


# ---------------------------------------------------------------------------
# BCEAO – XOF (parité fixe EUR)
# ---------------------------------------------------------------------------

def _compute_xof_from_eur(eur_usd_rate: float) -> float:
    """
    XOF (CFA Franc BCEAO) is pegged to EUR at a fixed rate:
    1 EUR = 655.957 XOF (unchanged since 1999).
    Returns XOF per 1 USD using the EUR/USD cross rate.
    """
    # 1 EUR = eur_usd_rate USD  →  1 USD = (1/eur_usd_rate) EUR = (655.957/eur_usd_rate) XOF
    return _CFA_EUR_PEG / eur_usd_rate


def _compute_xaf_from_eur(eur_usd_rate: float) -> float:
    """
    XAF (CFA Franc BEAC) is also pegged to EUR at exactly 655.957.
    Returns XAF per 1 USD.
    """
    return _CFA_EUR_PEG / eur_usd_rate


# ---------------------------------------------------------------------------
# Main provider
# ---------------------------------------------------------------------------

class AfricanCentralBanksProvider(BaseRateProvider):
    """
    Provider that queries official African central bank websites
    for exchange rates of currencies not covered by standard APIs.

    Currencies targeted:
      DZD, MAD, TND, EGP, KES, ETB, XOF, XAF

    For XOF and XAF, uses the known fixed EUR peg (655.957).
    For others, scrapes official central bank HTML/JSON pages.
    """

    name = "african_central_banks"

    def fetch_rates(self, base: str = "USD") -> Optional[Dict[str, float]]:
        """
        Fetch rates for African currencies from official central bank sources.
        Only returns currencies for which reliable data was obtained.
        Always works relative to USD (base currency).
        """
        if base.upper() != "USD":
            # Cross-rate support: fetch USD-based rates then convert
            usd_rates = self.fetch_rates("USD")
            if usd_rates is None:
                return None
            base_rate = usd_rates.get(base.upper())
            if base_rate is None or base_rate == 0:
                return None
            return {code: rate / base_rate for code, rate in usd_rates.items()}

        rates: Dict[str, float] = {}

        # We need EUR/USD to compute CFA franc rates
        eur_usd_rate = self._get_eur_usd()

        # ── XOF and XAF : fixed EUR peg ──────────────────────────────────────
        if eur_usd_rate:
            try:
                rates["XOF"] = round(_compute_xof_from_eur(eur_usd_rate), 4)
                rates["XAF"] = round(_compute_xaf_from_eur(eur_usd_rate), 4)
                logger.info(
                    "CFA peg: 1 USD = %.4f XOF / %.4f XAF (EUR/USD=%.6f)",
                    rates["XOF"], rates["XAF"], eur_usd_rate,
                )
            except ZeroDivisionError:
                pass

        # ── DZD : Banque d'Algérie ────────────────────────────────────────────
        dzd = _fetch_dzd(eur_usd_rate)
        if dzd:
            rates["DZD"] = round(dzd, 4)

        # ── MAD : Bank Al-Maghrib ─────────────────────────────────────────────
        mad = _fetch_mad()
        if mad:
            rates["MAD"] = round(mad, 4)

        # ── TND : Banque Centrale de Tunisie ──────────────────────────────────
        tnd = _fetch_tnd()
        if tnd:
            rates["TND"] = round(tnd, 4)

        # ── EGP : Central Bank of Egypt ───────────────────────────────────────
        egp = _fetch_egp()
        if egp:
            rates["EGP"] = round(egp, 4)

        # ── KES : Central Bank of Kenya ───────────────────────────────────────
        kes = _fetch_kes()
        if kes:
            rates["KES"] = round(kes, 4)

        # ── ETB : National Bank of Ethiopia ──────────────────────────────────
        etb = _fetch_etb()
        if etb:
            rates["ETB"] = round(etb, 4)

        logger.info(
            "AfricanCentralBanks: fetched %d currencies: %s",
            len(rates), list(rates.keys()),
        )
        return rates if rates else None

    def _get_eur_usd(self) -> Optional[float]:
        """Fetch EUR/USD rate from Frankfurter (free ECB data)."""
        try:
            resp = requests.get(
                "https://api.frankfurter.app/latest",
                params={"from": "USD", "to": "EUR"},
                timeout=10,
            )
            resp.raise_for_status()
            data = resp.json()
            rate = data.get("rates", {}).get("EUR")
            if rate:
                return float(rate)
        except Exception as exc:
            logger.debug("EUR/USD fetch failed: %s", exc)
        return None
