"""
Données World Bank WDI curées — valeur ajoutée sectorielle & croissance PIB.

GÉNÉRÉ AUTOMATIQUEMENT par ``scripts/fetch_wdi_macro.py`` — NE PAS ÉDITER À LA MAIN.
Régénérer là où l'API World Bank est joignable :

    python3 scripts/fetch_wdi_macro.py

Valeurs RÉELLES publiées (World Bank World Development Indicators), aucune
synthèse. Structure : {iso3: {year: {indicateur: valeur_%}}}.
Indicateurs : agri=NV.AGR.TOTL.ZS, ind=NV.IND.TOTL.ZS, manuf=NV.IND.MANF.ZS,
serv=NV.SRV.TOTL.ZS, gdp_growth=NY.GDP.MKTP.KD.ZG.

Source   : https://data.worldbank.org/ (API v2, sans clé)
Récupéré : 2026-08-25T11:17:07.179246+00:00
Couverture : 52 pays, 500 points (pays×année).
"""

WDI_FETCHED_AT = "2026-08-25T11:17:07.179246+00:00"

WDI_MACRO = {
    "AGO": {
        2023: {"agri": 20.91, "gdp_growth": 1.32, "ind": 35.7, "manuf": 7.4, "serv": 43.55},
        2024: {"agri": 21.55, "gdp_growth": 4.95, "ind": 33.88, "manuf": 6.58, "serv": 44.61},
    },
    "BDI": {
        2023: {"agri": 34.04, "gdp_growth": 3.25, "ind": 17.37, "manuf": 12.53, "serv": 43.79},
        2024: {"agri": 35.05, "gdp_growth": 4.11, "ind": 17.26, "manuf": 12.26, "serv": 43.34},
    },
    "BEN": {
        2023: {"agri": 25.4, "gdp_growth": 6.35, "ind": 17.3, "manuf": 10.06, "serv": 47.72},
        2024: {"agri": 24.23, "gdp_growth": 7.45, "ind": 17.38, "manuf": 10.17, "serv": 48.88},
    },
    "BFA": {
        2023: {"agri": 19.01, "gdp_growth": 3.0, "ind": 25.76, "manuf": 9.93, "serv": 47.57},
        2024: {"agri": 20.92, "gdp_growth": 4.83, "ind": 26.51, "manuf": 9.5, "serv": 43.96},
    },
    "BWA": {
        2023: {"agri": 1.68, "gdp_growth": 3.21, "ind": 34.07, "manuf": 5.62, "serv": 59.19},
        2024: {"agri": 1.76, "gdp_growth": -2.78, "ind": 29.08, "manuf": 5.58, "serv": 63.51},
    },
    "CAF": {
        2023: {"agri": 28.61, "gdp_growth": 0.7, "ind": 20.71, "manuf": 17.95, "serv": 40.51},
        2024: {"agri": 27.9, "gdp_growth": 1.5, "ind": 20.03, "serv": 42.08},
    },
    "CIV": {
        2023: {"agri": 15.94, "gdp_growth": 6.6, "ind": 23.9, "manuf": 13.26, "serv": 52.27},
        2024: {"agri": 15.86, "gdp_growth": 6.02, "ind": 24.04, "manuf": 12.92, "serv": 51.86},
    },
    "CMR": {
        2023: {"agri": 17.1, "gdp_growth": 3.35, "ind": 25.13, "manuf": 13.22, "serv": 50.87},
        2024: {"agri": 18.46, "gdp_growth": 3.52, "ind": 23.24, "manuf": 12.88, "serv": 50.72},
    },
    "COD": {
        2023: {"agri": 10.38, "gdp_growth": 8.53, "ind": 39.5, "manuf": 8.25, "serv": 45.92},
        2024: {"agri": 10.08, "gdp_growth": 6.1, "ind": 38.97, "manuf": 8.6, "serv": 47.27},
    },
    "COG": {
        2023: {"agri": 8.95, "gdp_growth": 1.91, "ind": 45.22, "serv": 40.43},
        2024: {"agri": 9.44, "gdp_growth": 2.1, "ind": 40.12, "serv": 45.02},
    },
    "COM": {
        2023: {"agri": 34.16, "gdp_growth": 3.19, "ind": 10.33, "manuf": 8.02, "serv": 50.8},
        2024: {"agri": 36.07, "gdp_growth": 3.3, "ind": 9.7, "manuf": 7.16, "serv": 49.35},
    },
    "CPV": {
        2023: {"agri": 4.85, "gdp_growth": 4.79, "ind": 10.98, "manuf": 4.95, "serv": 68.89},
        2024: {"agri": 4.95, "gdp_growth": 6.99, "ind": 10.71, "manuf": 5.16, "serv": 68.83},
    },
    "DJI": {
        2023: {"agri": 2.5, "gdp_growth": 6.81, "ind": 14.43, "manuf": 4.7, "serv": 77.12},
        2024: {"agri": 2.51, "gdp_growth": 6.98, "ind": 15.91, "manuf": 5.28, "serv": 76.08},
    },
    "DZA": {
        2023: {"agri": 13.37, "gdp_growth": 4.1, "ind": 37.55, "manuf": 9.12, "serv": 45.55},
        2024: {"agri": 13.96, "gdp_growth": 3.7, "ind": 36.2, "manuf": 9.45, "serv": 46.79},
    },
    "EGY": {
        2023: {"agri": 10.6, "gdp_growth": 3.76, "ind": 32.73, "manuf": 15.06, "serv": 51.65},
        2024: {"agri": 13.71, "gdp_growth": 2.4, "ind": 32.56, "manuf": 13.89, "serv": 48.93},
    },
    "ETH": {
        2023: {"agri": 35.79, "gdp_growth": 6.59, "ind": 24.48, "manuf": 4.48, "serv": 36.98},
        2024: {"agri": 34.77, "gdp_growth": 7.61, "ind": 25.35, "manuf": 4.39, "serv": 37.47},
    },
    "GAB": {
        2023: {"agri": 6.67, "gdp_growth": 2.44, "ind": 53.87, "manuf": 20.54, "serv": 37.81},
        2024: {"agri": 6.56, "gdp_growth": 3.39, "ind": 52.9, "manuf": 19.46, "serv": 36.82},
    },
    "GHA": {
        2023: {"agri": 20.94, "gdp_growth": 3.14, "ind": 29.47, "manuf": 11.14, "serv": 43.11},
        2024: {"agri": 20.58, "gdp_growth": 5.85, "ind": 29.2, "manuf": 10.57, "serv": 43.65},
    },
    "GIN": {
        2023: {"agri": 29.47, "gdp_growth": 5.54, "ind": 25.73, "serv": 37.21},
        2024: {"agri": 30.96, "gdp_growth": 5.35, "ind": 25.12, "serv": 36.34},
    },
    "GMB": {
        2023: {"agri": 22.04, "gdp_growth": 5.92, "ind": 16.42, "manuf": 1.7, "serv": 55.03},
        2024: {"agri": 20.43, "gdp_growth": 5.55, "ind": 15.33, "manuf": 1.45, "serv": 56.79},
    },
    "GNB": {
        2023: {"agri": 36.8, "gdp_growth": 4.63, "ind": 15.41, "manuf": 8.91, "serv": 43.6},
        2024: {"agri": 41.16, "gdp_growth": 4.41, "ind": 16.0, "manuf": 9.17, "serv": 38.61},
    },
    "GNQ": {
        2023: {"agri": 2.77, "gdp_growth": -7.43, "ind": 48.29, "manuf": 22.15, "serv": 48.96},
        2024: {"agri": 2.73, "gdp_growth": 0.4, "ind": 48.41, "manuf": 25.81, "serv": 49.34},
    },
    "KEN": {
        2023: {"agri": 21.45, "gdp_growth": 5.72, "ind": 17.12, "manuf": 7.49, "serv": 55.47},
        2024: {"agri": 22.44, "gdp_growth": 4.66, "ind": 16.33, "manuf": 7.29, "serv": 55.69},
    },
    "LBR": {
        2023: {"agri": 34.57, "gdp_growth": 4.68, "ind": 23.35, "serv": 40.49},
        2024: {"agri": 33.83, "gdp_growth": 4.02, "ind": 21.97, "serv": 43.29},
    },
    "LBY": {
        2023: {"agri": 1.77, "gdp_growth": 10.2, "ind": 78.9, "serv": 23.98},
        2024: {"agri": 2.39, "gdp_growth": 1.9, "ind": 73.5, "serv": 28.34},
    },
    "LSO": {
        2023: {"agri": 6.66, "gdp_growth": 1.69, "ind": 28.52, "manuf": 14.05, "serv": 50.5},
        2024: {"agri": 6.62, "gdp_growth": 5.23, "ind": 28.1, "manuf": 12.07, "serv": 51.35},
    },
    "MAR": {
        2023: {"agri": 11.13, "gdp_growth": 3.66, "ind": 25.32, "manuf": 15.79, "serv": 53.71},
        2024: {"agri": 10.57, "gdp_growth": 3.79, "ind": 25.64, "manuf": 15.27, "serv": 52.73},
    },
    "MDG": {
        2023: {"agri": 22.22, "gdp_growth": 4.23, "ind": 23.12, "manuf": 13.01, "serv": 48.79},
        2024: {"agri": 21.92, "gdp_growth": 4.32, "ind": 22.92, "manuf": 13.12, "serv": 49.3},
    },
    "MLI": {
        2023: {"agri": 31.37, "gdp_growth": 4.76, "ind": 26.88, "manuf": 7.16, "serv": 35.51},
        2024: {"agri": 32.59, "gdp_growth": 5.02, "ind": 24.45, "manuf": 7.32, "serv": 36.07},
    },
    "MOZ": {
        2023: {"agri": 25.36, "gdp_growth": 5.5, "ind": 21.53, "manuf": 7.12, "serv": 41.1},
        2024: {"agri": 25.17, "gdp_growth": 2.15, "ind": 21.92, "manuf": 6.44, "serv": 41.08},
    },
    "MRT": {
        2023: {"agri": 19.16, "gdp_growth": 6.81, "ind": 30.94, "manuf": 6.5, "serv": 43.02},
        2024: {"agri": 19.33, "gdp_growth": 6.31, "ind": 30.51, "manuf": 5.01, "serv": 42.43},
    },
    "MUS": {
        2023: {"agri": 4.01, "gdp_growth": 4.7, "ind": 17.84, "manuf": 11.5, "serv": 64.87},
        2024: {"agri": 4.23, "gdp_growth": 4.95, "ind": 17.79, "manuf": 11.09, "serv": 64.37},
    },
    "MWI": {
        2023: {"agri": 28.87, "gdp_growth": 1.95, "ind": 19.29, "manuf": 12.8, "serv": 45.12},
        2024: {"agri": 31.79, "gdp_growth": 1.67, "ind": 17.08, "manuf": 10.97, "serv": 44.22},
    },
    "NAM": {
        2023: {"agri": 7.61, "gdp_growth": 4.32, "ind": 30.62, "manuf": 11.0, "serv": 52.98},
        2024: {"agri": 7.15, "gdp_growth": 3.78, "ind": 29.53, "manuf": 10.29, "serv": 54.06},
    },
    "NER": {
        2023: {"agri": 43.99, "gdp_growth": 2.64, "ind": 17.41, "manuf": 7.28, "serv": 34.63},
        2024: {"agri": 47.97, "gdp_growth": 8.32, "ind": 17.3, "manuf": 6.99, "serv": 32.25},
    },
    "NGA": {
        2023: {"agri": 27.72, "gdp_growth": 3.32, "ind": 19.13, "manuf": 9.27, "serv": 51.71},
        2024: {"agri": 25.87, "gdp_growth": 4.07, "ind": 18.2, "manuf": 8.66, "serv": 53.73},
    },
    "RWA": {
        2023: {"agri": 23.14, "gdp_growth": 8.56, "ind": 21.48, "manuf": 8.57, "serv": 50.33},
        2024: {"agri": 20.79, "gdp_growth": 7.23, "ind": 22.07, "manuf": 8.12, "serv": 52.19},
    },
    "SDN": {
        2023: {"agri": 30.28, "gdp_growth": -29.43, "ind": 28.34, "serv": 41.39},
        2024: {"agri": 22.18, "gdp_growth": -13.96, "ind": 23.15, "serv": 54.67},
    },
    "SEN": {
        2023: {"agri": 17.41, "gdp_growth": 4.26, "ind": 22.89, "manuf": 14.54, "serv": 49.59},
        2024: {"agri": 15.57, "gdp_growth": 6.46, "ind": 25.36, "manuf": 14.22, "serv": 49.08},
    },
    "SLE": {
        2023: {"agri": 29.05, "gdp_growth": 5.71, "ind": 26.08, "manuf": 7.67, "serv": 42.16},
        2024: {"agri": 29.16, "gdp_growth": 4.29, "ind": 25.56, "manuf": 6.96, "serv": 42.57},
    },
    "SOM": {2023: {"gdp_growth": 4.18}, 2024: {"gdp_growth": 4.11}},
    "STP": {
        2023: {"agri": 13.45, "gdp_growth": 0.37, "ind": 2.73, "manuf": 0.61, "serv": 79.48},
        2024: {"agri": 12.45, "gdp_growth": 1.48, "ind": 2.25, "manuf": 0.64, "serv": 81.05},
    },
    "SWZ": {
        2023: {"agri": 6.63, "gdp_growth": 3.53, "ind": 34.51, "manuf": 29.19, "serv": 51.89},
        2024: {"agri": 6.48, "gdp_growth": 3.03, "ind": 34.74, "manuf": 29.12, "serv": 51.36},
    },
    "SYC": {
        2023: {"agri": 2.51, "gdp_growth": 5.18, "ind": 13.3, "manuf": 4.79, "serv": 68.94},
        2024: {"agri": 2.63, "gdp_growth": 3.35, "ind": 13.42, "manuf": 5.06, "serv": 68.92},
    },
    "TCD": {
        2023: {"agri": 35.19, "gdp_growth": 4.0, "ind": 30.8, "manuf": 6.41, "serv": 30.3},
        2024: {"agri": 37.16, "gdp_growth": 4.95, "ind": 28.76, "manuf": 6.31, "serv": 31.04},
    },
    "TGO": {
        2023: {"agri": 20.77, "gdp_growth": 6.2, "ind": 20.67, "manuf": 11.84, "serv": 49.24},
        2024: {"agri": 21.34, "gdp_growth": 6.53, "ind": 20.44, "manuf": 11.42, "serv": 49.2},
    },
    "TUN": {
        2023: {"agri": 9.47, "gdp_growth": 0.18, "ind": 24.09, "manuf": 15.17, "serv": 62.09},
        2024: {"agri": 9.74, "gdp_growth": 1.61, "ind": 22.56, "manuf": 14.79, "serv": 62.61},
    },
    "TZA": {
        2023: {"agri": 23.69, "gdp_growth": 5.07, "ind": 28.03, "manuf": 8.4, "serv": 28.7},
        2024: {"agri": 23.32, "gdp_growth": 5.53, "ind": 28.57, "serv": 29.56},
    },
    "UGA": {
        2023: {"agri": 24.09, "gdp_growth": 5.34, "ind": 25.75, "manuf": 15.65, "serv": 42.51},
        2024: {"agri": 24.62, "gdp_growth": 6.06, "ind": 24.87, "manuf": 15.11, "serv": 43.14},
    },
    "ZAF": {
        2023: {"agri": 2.54, "gdp_growth": 0.81, "ind": 24.56, "manuf": 12.98, "serv": 62.72},
        2024: {"agri": 2.81, "gdp_growth": 0.53, "ind": 24.31, "manuf": 12.8, "serv": 62.99},
    },
    "ZMB": {
        2023: {"agri": 2.23, "gdp_growth": 5.37, "ind": 35.11, "manuf": 8.5, "serv": 56.82},
        2024: {"agri": 2.83, "gdp_growth": 3.82, "ind": 35.25, "manuf": 9.05, "serv": 57.19},
    },
    "ZWE": {
        2023: {"agri": 11.49, "gdp_growth": 5.35, "ind": 33.26, "manuf": 15.28, "serv": 49.56},
        2024: {"agri": 8.69, "gdp_growth": 1.68, "ind": 35.01, "manuf": 15.57, "serv": 50.58},
    },
}
