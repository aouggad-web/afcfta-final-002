# Indicateurs sociaux 2024 — 54 pays ZLECAf
# Sources: FMI WEO Oct 2024 (inflation), OIT/BIT 2024 (chômage), PNUD IDH 2023/2024 (rang IDH)
# Inflation = taux moyen annuel 2024 (%)
# Unemployment = taux chômage BIT 2024 (%)
# HDI_rank = rang IDH mondial 2023 (PNUD)

SOCIAL_INDICATORS = {
    "DZA": {"inflation_rate": 5.3,  "unemployment_rate": 11.8, "hdi_rank": 91},
    "AGO": {"inflation_rate": 27.1, "unemployment_rate": 7.7,  "hdi_rank": 148},
    "BEN": {"inflation_rate": 2.3,  "unemployment_rate": 1.5,  "hdi_rank": 166},
    "BWA": {"inflation_rate": 4.3,  "unemployment_rate": 24.5, "hdi_rank": 100},
    "BFA": {"inflation_rate": 2.0,  "unemployment_rate": 5.5,  "hdi_rank": 185},
    "BDI": {"inflation_rate": 18.2, "unemployment_rate": 1.4,  "hdi_rank": 187},
    "CMR": {"inflation_rate": 6.5,  "unemployment_rate": 3.4,  "hdi_rank": 163},
    "CPV": {"inflation_rate": 4.1,  "unemployment_rate": 12.7, "hdi_rank": 126},
    "CAF": {"inflation_rate": 4.8,  "unemployment_rate": 7.0,  "hdi_rank": 188},
    "TCD": {"inflation_rate": 5.5,  "unemployment_rate": 2.0,  "hdi_rank": 190},
    "COM": {"inflation_rate": 1.5,  "unemployment_rate": 5.0,  "hdi_rank": 156},
    "COG": {"inflation_rate": 4.0,  "unemployment_rate": 9.5,  "hdi_rank": 149},
    "COD": {"inflation_rate": 15.0, "unemployment_rate": 4.2,  "hdi_rank": 179},
    "CIV": {"inflation_rate": 3.7,  "unemployment_rate": 2.4,  "hdi_rank": 166},
    "DJI": {"inflation_rate": 3.5,  "unemployment_rate": 11.0, "hdi_rank": 166},
    "EGY": {"inflation_rate": 29.5, "unemployment_rate": 6.7,  "hdi_rank": 107},
    "GNQ": {"inflation_rate": 5.5,  "unemployment_rate": 8.5,  "hdi_rank": 145},
    "ERI": {"inflation_rate": 30.0, "unemployment_rate": None, "hdi_rank": None},
    "SWZ": {"inflation_rate": 4.2,  "unemployment_rate": 26.0, "hdi_rank": 143},
    "ETH": {"inflation_rate": 28.0, "unemployment_rate": 3.5,  "hdi_rank": 175},
    "GAB": {"inflation_rate": 3.4,  "unemployment_rate": 20.0, "hdi_rank": 119},
    "GMB": {"inflation_rate": 17.5, "unemployment_rate": 9.0,  "hdi_rank": 174},
    "GHA": {"inflation_rate": 22.5, "unemployment_rate": 3.6,  "hdi_rank": 145},
    "GIN": {"inflation_rate": 12.0, "unemployment_rate": 2.7,  "hdi_rank": 178},
    "GNB": {"inflation_rate": 3.5,  "unemployment_rate": 3.0,  "hdi_rank": 177},
    "KEN": {"inflation_rate": 5.5,  "unemployment_rate": 5.7,  "hdi_rank": 145},
    "LSO": {"inflation_rate": 6.5,  "unemployment_rate": 24.0, "hdi_rank": 159},
    "LBR": {"inflation_rate": 10.5, "unemployment_rate": 2.5,  "hdi_rank": 181},
    "LBY": {"inflation_rate": 2.5,  "unemployment_rate": 19.0, "hdi_rank": 104},
    "MDG": {"inflation_rate": 8.5,  "unemployment_rate": 2.0,  "hdi_rank": 174},
    "MWI": {"inflation_rate": 22.5, "unemployment_rate": 5.5,  "hdi_rank": 174},
    "MLI": {"inflation_rate": 3.5,  "unemployment_rate": 6.0,  "hdi_rank": 186},
    "MRT": {"inflation_rate": 2.5,  "unemployment_rate": 11.5, "hdi_rank": 164},
    "MUS": {"inflation_rate": 4.5,  "unemployment_rate": 6.0,  "hdi_rank": 65},
    "MAR": {"inflation_rate": 1.9,  "unemployment_rate": 13.0, "hdi_rank": 123},
    "MOZ": {"inflation_rate": 4.0,  "unemployment_rate": 3.5,  "hdi_rank": 185},
    "NAM": {"inflation_rate": 5.3,  "unemployment_rate": 33.4, "hdi_rank": 130},
    "NER": {"inflation_rate": 3.0,  "unemployment_rate": 0.5,  "hdi_rank": 189},
    "NGA": {"inflation_rate": 33.0, "unemployment_rate": 4.9,  "hdi_rank": 163},
    "RWA": {"inflation_rate": 5.0,  "unemployment_rate": 14.5, "hdi_rank": 160},
    "STP": {"inflation_rate": 10.5, "unemployment_rate": 13.5, "hdi_rank": 140},
    "SEN": {"inflation_rate": 2.0,  "unemployment_rate": 3.3,  "hdi_rank": 170},
    "SYC": {"inflation_rate": 3.0,  "unemployment_rate": 3.0,  "hdi_rank": 73},
    "SLE": {"inflation_rate": 52.0, "unemployment_rate": 3.7,  "hdi_rank": 181},
    "SOM": {"inflation_rate": 5.0,  "unemployment_rate": 5.0,  "hdi_rank": None},
    "ZAF": {"inflation_rate": 5.3,  "unemployment_rate": 32.1, "hdi_rank": 110},
    "SSD": {"inflation_rate": 40.0, "unemployment_rate": 15.0, "hdi_rank": 186},
    "SDN": {"inflation_rate": 60.0, "unemployment_rate": 12.0, "hdi_rank": 172},
    "TZA": {"inflation_rate": 3.8,  "unemployment_rate": 2.7,  "hdi_rank": 163},
    "TGO": {"inflation_rate": 3.5,  "unemployment_rate": 1.8,  "hdi_rank": 167},
    "TUN": {"inflation_rate": 7.5,  "unemployment_rate": 15.5, "hdi_rank": 101},
    "UGA": {"inflation_rate": 4.5,  "unemployment_rate": 2.9,  "hdi_rank": 166},
    "ZMB": {"inflation_rate": 14.0, "unemployment_rate": 12.8, "hdi_rank": 166},
    "ZWE": {"inflation_rate": 20.0, "unemployment_rate": 5.0,  "hdi_rank": 146},
}


def get_social_indicators(iso3_code: str) -> dict:
    """Retourne les indicateurs sociaux pour un pays donné (ISO3)."""
    return SOCIAL_INDICATORS.get(iso3_code, {})
