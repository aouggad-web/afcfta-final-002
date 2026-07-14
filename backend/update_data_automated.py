#!/usr/bin/env python3
"""
Automated Data Update Script
Fetches and updates data from external sources (World Bank, FAOSTAT, etc.)
"""

import csv
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

try:
    import requests
except ImportError:
    print("⚠️  requests library not found, install with: pip install requests")
    sys.exit(1)


class DataUpdater:
    """Main class for updating data from external sources"""

    def __init__(self, verbose=True):
        self.verbose = verbose
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "AfCFTA-Data-Updater/1.0"})
        self.updates_log = []

    def log(self, message, level="INFO"):
        """Log messages"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [{level}] {message}"
        self.updates_log.append(log_entry)
        if self.verbose:
            print(log_entry)

    def fetch_world_bank_data(self, indicator, countries, date_range="2020:2024"):
        """
        Fetch data from World Bank API
        indicator: e.g., 'NY.GDP.MKTP.CD', 'SP.POP.TOTL'
        countries: list of ISO3 country codes
        date_range: plage d'années "AAAA:AAAA". Élargie pour les indicateurs
            sociaux (pauvreté, Gini) dont la dernière enquête peut remonter à
            plusieurs années (ex. pauvreté Algérie = 2011) : sans plage large,
            leur valeur réelle serait manquée et l'app retomberait sur une
            valeur curée figée.
        """
        self.log(f"Fetching World Bank data for indicator: {indicator} ({date_range})")

        # World Bank API endpoint
        # Format: https://api.worldbank.org/v2/country/{countries}/indicator/{indicator}?format=json&date=2020:2024
        countries_str = ";".join(countries)
        url = f"https://api.worldbank.org/v2/country/{countries_str}/indicator/{indicator}"
        params = {"format": "json", "date": date_range, "per_page": 2000}

        try:
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()

            if len(data) > 1 and data[1]:
                self.log(f"✓ Successfully fetched {len(data[1])} data points for {indicator}")
                return data[1]
            else:
                self.log(f"✗ No data returned for {indicator}", "WARNING")
                return []

        except Exception as e:
            self.log(f"✗ Error fetching World Bank data: {str(e)}", "ERROR")
            return []

    def update_country_profiles(self):
        """Update country economic profiles with latest World Bank data"""
        self.log("=" * 60)
        self.log("Updating country profiles from World Bank API")
        self.log("=" * 60)

        # African country ISO3 codes
        african_countries = [
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
            "CIV",
            "DJI",
            "EGY",
            "GNQ",
            "ERI",
            "ETH",
            "GAB",
            "GMB",
            "GHA",
            "GIN",
            "GNB",
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
            "SYC",
            "SLE",
            "SOM",
            "ZAF",
            "SSD",
            "SDN",
            "SWZ",
            "TZA",
            "TGO",
            "TUN",
            "UGA",
            "ZMB",
            "ZWE",
        ]

        # Fetch key indicators.
        # date_range : les indicateurs macro annuels restent sur 2020:2024 ;
        # les indicateurs sociaux (pauvreté, Gini, espérance de vie, accès
        # électricité/internet…) utilisent une plage large car leur dernière
        # valeur réelle peut remonter loin (ex. pauvreté = enquête ménages,
        # parfois 2011). wb_macro_service._latest() ne retient que la dernière
        # année réellement renseignée, avec cette année réelle affichée.
        # (name, code, date_range)
        indicators_spec = [
            ("GDP", "NY.GDP.MKTP.CD", "2020:2024"),  # GDP (current US$)
            ("GDP_per_capita", "NY.GDP.PCAP.CD", "2020:2024"),  # GDP/capita (US$)
            ("Population", "SP.POP.TOTL", "2020:2024"),  # Population, total
            ("GDP_growth", "NY.GDP.MKTP.KD.ZG", "2020:2024"),  # GDP growth (%)
            ("Inflation", "FP.CPI.TOTL.ZG", "2020:2024"),  # Inflation (annual %)
            ("Unemployment", "SL.UEM.TOTL.ZS", "2020:2024"),  # Unemployment (%)
            # Indicateurs sociaux Banque Mondiale (WDI) — alimentent le bloc
            # « Indicateurs sociaux » du Profil Pays. Chacun affiché avec sa
            # VRAIE année (fin des étiquettes d'année figées/inventées).
            ("LifeExpectancy", "SP.DYN.LE00.IN", "2000:2024"),  # espérance de vie
            ("GiniIndex", "SI.POV.GINI", "2000:2024"),  # indice de Gini
            ("Poverty3usd", "SI.POV.DDAY", "2000:2024"),  # pauvreté seuil int. (3,00$ PPA 2021)
            ("UrbanPopulation", "SP.URB.TOTL.IN.ZS", "2000:2024"),  # pop. urbaine %
            ("InternetUsers", "IT.NET.USER.ZS", "2000:2024"),  # internautes %
            ("ElectricityAccess", "EG.ELC.ACCS.ZS", "2000:2024"),  # accès électricité %
            ("FemaleLaborForce", "SL.TLF.CACT.FE.ZS", "2000:2024"),  # pop. active féminine %
        ]

        country_data = {}

        for indicator_name, indicator_code, date_range in indicators_spec:
            self.log(f"\nFetching {indicator_name}...")
            data = self.fetch_world_bank_data(indicator_code, african_countries, date_range)

            for item in data:
                country_code = item.get("countryiso3code")
                value = item.get("value")
                year = item.get("date")

                if country_code and value is not None:
                    if country_code not in country_data:
                        country_data[country_code] = {
                            "name": item.get("country", {}).get("value", ""),
                            "latest_update": datetime.now().isoformat(),
                            "indicators": {},
                        }

                    # Store values by indicator and year in a structured way
                    if indicator_name not in country_data[country_code]["indicators"]:
                        country_data[country_code]["indicators"][indicator_name] = {}

                    country_data[country_code]["indicators"][indicator_name][year] = value

            # Rate limiting - be nice to the API
            time.sleep(1)

        self.log(f"\n✓ Updated data for {len(country_data)} countries")

        # Save the updated data — dans data/json/, là où l'application le lit
        # (services/wb_macro_service.py) ; l'ancien chemin racine n'était
        # consommé par personne.
        output_file = Path(__file__).parent.parent / "data" / "json" / "worldbank_data_latest.json"

        # Garde-fou intégrité : fusion avec le fichier existant. Toute valeur
        # (pays × indicateur × année) absente de la collecte de cette run — qu'un
        # indicateur ait entièrement échoué (400 transitoire de l'API BM),
        # renvoyé une page 100 % null, ou simplement omis un pays/une année — est
        # restaurée depuis le fichier précédent. Les valeurs fraîches l'emportent
        # toujours (on ne comble que les trous). Conforme à la règle « valeurs
        # réelles uniquement, jamais effacées silencieusement ».
        countries_touched, series_restored = self._preserve_previous_values(
            output_file, country_data
        )
        if series_restored:
            self.log(
                f"✗ {series_restored} série(s) (pays × indicateur) non collectée(s) "
                f"cette run — valeurs précédentes conservées ({countries_touched} pays)",
                "WARNING",
            )

        # metadata.indicators reflète les indicateurs RÉELLEMENT présents dans la
        # sortie (fraîchement récupérés + préservés), jamais une liste déclarative
        # incluant des indicateurs absents.
        present_indicators = [
            name
            for name, _code, _range in indicators_spec
            if any(name in c.get("indicators", {}) for c in country_data.values())
        ]

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "metadata": {
                        "source": "World Bank API",
                        "updated_at": datetime.now().isoformat(),
                        "indicators": present_indicators,
                    },
                    "data": country_data,
                },
                f,
                indent=2,
                ensure_ascii=False,
            )

        self.log(f"✓ Saved data to {output_file}")
        return country_data

    @staticmethod
    def _load_existing_wb(output_file):
        """Charge le bloc `data` du fichier World Bank existant (ou {} si absent
        / illisible) — aucune exception ne doit interrompre la run."""
        try:
            with open(output_file, "r", encoding="utf-8") as f:
                return json.load(f).get("data", {}) or {}
        except (FileNotFoundError, json.JSONDecodeError, OSError):
            return {}

    def _preserve_previous_values(self, output_file, country_data):
        """
        Fusionne le fichier World Bank précédent dans les données fraîchement
        collectées, au grain (pays × indicateur × année). Pour chaque pays du
        fichier précédent :
          • un indicateur totalement absent de la collecte (échec, page 100 %
            null, ou pays omis) est restauré intégralement ;
          • un indicateur présent mais auquel il manque des années est complété
            année par année.
        Les valeurs fraîches l'emportent TOUJOURS : on ne comble que les trous,
        jamais d'écrasement. Un pays entièrement omis cette run est réintroduit
        avec toutes ses séries précédentes (aucune perte de pays).

        Ne se fie à aucun drapeau « récupéré » : seule compte la présence réelle
        d'une valeur dans `country_data`, ce qui neutralise aussi le cas d'une
        page renvoyée non vide mais entièrement `null` (rien n'y est stocké, donc
        tout est considéré comme manquant et restauré).

        Retourne (nombre de pays touchés, nombre de séries pays×indicateur
        restaurées ou complétées).
        """
        previous = self._load_existing_wb(output_file)
        countries_touched = 0
        series_restored = 0
        for iso3, prev in previous.items():
            prev_inds = {n: v for n, v in (prev or {}).get("indicators", {}).items() if v}
            if not prev_inds:
                continue
            if iso3 not in country_data:
                country_data[iso3] = {
                    "name": prev.get("name", ""),
                    "latest_update": prev.get("latest_update", datetime.now().isoformat()),
                    "indicators": {},
                }
            cur_inds = country_data[iso3]["indicators"]
            touched = False
            for name, prev_vals in prev_inds.items():
                cur_vals = cur_inds.get(name)
                if cur_vals is None:
                    cur_inds[name] = dict(prev_vals)
                    series_restored += 1
                    touched = True
                else:
                    filled = False
                    for year, val in prev_vals.items():
                        if year not in cur_vals:
                            cur_vals[year] = val
                            filled = True
                    if filled:
                        series_restored += 1
                        touched = True
            if touched:
                countries_touched += 1
        return countries_touched, series_restored

    def update_csv_data(self, worldbank_data=None):
        """Update CSV data files with latest information"""
        self.log("=" * 60)
        self.log("Updating CSV data files")
        self.log("=" * 60)

        # Check for the existence of CSV files
        csv_files = [
            "ZLECAF_54_PAYS_DONNEES_COMPLETES.csv",
            "ZLECAF_DATA_UPDATED.csv",
        ]

        base_path = Path(__file__).parent.parent
        csv_found = False

        for csv_file in csv_files:
            file_path = base_path / csv_file
            if file_path.exists():
                self.log(f"✓ Found {csv_file}")
                csv_found = True

                # If World Bank data is available, we could update the CSV
                # For now, just verify the file exists
                # Future enhancement: Parse and update CSV with new data
            else:
                self.log(f"✗ File not found: {csv_file}", "WARNING")

        if csv_found:
            self.log("✓ CSV files verified (no updates performed)")

        return True

    def update_json_data_files(self):
        """Update JSON data files"""
        self.log("=" * 60)
        self.log("Updating JSON data files")
        self.log("=" * 60)

        # Update timestamp in existing JSON files
        base_path = Path(__file__).parent.parent
        json_files = [
            "ports_africains.json",
            "airports_africains.json",
            "production_africaine.json",
        ]

        for json_file in json_files:
            file_path = base_path / json_file
            if file_path.exists():
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        data = json.load(f)

                    # Add or update metadata
                    if isinstance(data, dict):
                        if "metadata" not in data:
                            data["metadata"] = {}
                        data["metadata"]["last_updated"] = datetime.now().isoformat()
                        data["metadata"]["update_source"] = "automated_update"

                    with open(file_path, "w", encoding="utf-8") as f:
                        json.dump(data, f, indent=2, ensure_ascii=False)

                    self.log(f"✓ Updated {json_file}")
                except Exception as e:
                    self.log(f"✗ Error updating {json_file}: {str(e)}", "ERROR")
            else:
                self.log(f"✗ File not found: {json_file}", "WARNING")

        return True

    def generate_update_report(self):
        """Generate a report of all updates"""
        self.log("=" * 60)
        self.log("Generating update report")
        self.log("=" * 60)

        errors = len([log for log in self.updates_log if "ERROR" in log])
        report = {
            "timestamp": datetime.now().isoformat(),
            "status": "completed_with_errors" if errors > 0 else "completed",
            "updates_performed": len([log for log in self.updates_log if "✓" in log]),
            "warnings": len([log for log in self.updates_log if "WARNING" in log]),
            "errors": errors,
            "log": self.updates_log,
        }

        # Save report
        report_file = Path(__file__).parent.parent / "data_update_report.json"
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        self.log(f"✓ Report saved to {report_file}")

        # Print summary
        self.log("\n" + "=" * 60)
        self.log("UPDATE SUMMARY")
        self.log("=" * 60)
        self.log(f"Status: {report['status']}")
        self.log(f"Updates: {report['updates_performed']}")
        self.log(f"Warnings: {report['warnings']}")
        self.log(f"Errors: {report['errors']}")
        self.log("=" * 60)

        return report


def main():
    """Main execution function"""
    print("🚀 AfCFTA Automated Data Update")
    print("=" * 60)

    updater = DataUpdater(verbose=True)

    try:
        # Update country profiles from World Bank
        country_data = updater.update_country_profiles()

        # Update CSV files (currently just verifies existence)
        updater.update_csv_data(country_data)

        # Update JSON files
        updater.update_json_data_files()

        # Generate report
        report = updater.generate_update_report()

        # Exit with appropriate code
        # Check for any actual failures (not just API connection errors)
        critical_errors = [log for log in report["log"] if "Fatal" in log]
        if len(critical_errors) > 0:
            print("\n❌ Update failed with critical errors")
            sys.exit(1)
        elif report["updates_performed"] > 0:
            print("\n✅ Update completed successfully")
            sys.exit(0)
        else:
            print("\n⚠️  Update completed but no updates were performed")
            sys.exit(0)  # Don't fail, as this might be expected

    except Exception as e:
        print(f"\n❌ Fatal error: {str(e)}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
