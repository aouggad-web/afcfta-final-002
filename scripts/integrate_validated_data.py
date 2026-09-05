#!/usr/bin/env python3
"""
Intégrer les données validées du fichier Excel dans notre application ZLECAf
"""
import json

import numpy as np
import pandas as pd


def integrate_validated_data():
    print("🔄 INTÉGRATION DES DONNÉES VALIDÉES")
    print("=" * 60)

    # Lire les données 2024 (plus récentes)
    try:
        df_2024 = pd.read_excel("/app/validation_master.xlsx", sheet_name="2024_compilé_ZLECAf")
        df_2023 = pd.read_excel("/app/validation_master.xlsx", sheet_name="2023_compilé_ZLECAf")
        print(f"✅ Données 2024: {len(df_2024)} pays")
        print(f"✅ Données 2023: {len(df_2023)} pays")
    except Exception as e:
        print(f"❌ Erreur lecture fichier: {e}")
        return

    # Fusionner les données 2023 et 2024, en privilégiant 2024 quand disponible
    print("\n🔗 FUSION DES DONNÉES 2023-2024")
    print("-" * 40)

    countries_data = {}

    for _, row in df_2024.iterrows():
        pays = row["Pays"]
        code = row["Code_ISO"]

        # Utiliser 2024 si disponible, sinon 2023
        row_2023 = df_2023[df_2023["Pays"] == pays]

        # Récupérer les données 2024 en priorité, 2023 en fallback
        pib_2024 = row["PIB_2024_Mds_USD"] if pd.notna(row["PIB_2024_Mds_USD"]) else None
        pop_2024 = row["Population_2024_M"] if pd.notna(row["Population_2024_M"]) else None
        pib_hab_2024 = (
            row["PIB_par_habitant_2024_USD"] if pd.notna(row["PIB_par_habitant_2024_USD"]) else None
        )

        # Si 2024 manque, utiliser 2023
        if pib_2024 is None and not row_2023.empty:
            pib_2024 = (
                row_2023.iloc[0]["PIB_2023_Mds_USD"]
                if pd.notna(row_2023.iloc[0]["PIB_2023_Mds_USD"])
                else None
            )

        if pop_2024 is None and not row_2023.empty:
            pop_2024 = (
                row_2023.iloc[0]["Population_2023_M"]
                if pd.notna(row_2023.iloc[0]["Population_2023_M"])
                else None
            )

        if pib_hab_2024 is None and not row_2023.empty:
            pib_hab_2024 = (
                row_2023.iloc[0]["PIB_par_habitant_2023_USD"]
                if pd.notna(row_2023.iloc[0]["PIB_par_habitant_2023_USD"])
                else None
            )

        # Calculer PIB/habitant si manquant
        if pib_hab_2024 is None and pib_2024 and pop_2024:
            pib_hab_2024 = (pib_2024 * 1000) / pop_2024

        # Informations ZLECAf
        zlecaf_ratifie = row["ZLECAf_Ratifie"] if pd.notna(row["ZLECAf_Ratifie"]) else "Inconnu"
        date_ratif = (
            row["Date_Ratification_ZLECAf"] if pd.notna(row["Date_Ratification_ZLECAf"]) else None
        )

        # Données commerciales 2024 ou 2023
        exports_2024 = row["Exports_Biens_2024_Mds_USD"]
        imports_2024 = row["Imports_Biens_2024_Mds_USD"]

        if pd.isna(exports_2024) and not row_2023.empty:
            exports_2024 = row_2023.iloc[0]["Exports_Biens_2023_Mds_USD"]
            imports_2024 = row_2023.iloc[0]["Imports_Biens_2023_Mds_USD"]

        # Construction de l'entrée pays
        countries_data[code] = {
            "name": pays,
            "code": code,
            "gdp_usd_2024": pib_2024,
            "population_2024": pop_2024,
            "gdp_per_capita_2024": pib_hab_2024,
            "zlecaf_ratified": zlecaf_ratifie,
            "zlecaf_ratification_date": str(date_ratif) if date_ratif else None,
            "exports_2024": exports_2024 if pd.notna(exports_2024) else None,
            "imports_2024": imports_2024 if pd.notna(imports_2024) else None,
            "growth_2024": (
                row["Croissance_2024_Pct"] if pd.notna(row["Croissance_2024_Pct"]) else None
            ),
            "sources": row["Sources_Principales"] if pd.notna(row["Sources_Principales"]) else "",
            "validation_status": (
                row["STATUT_VALIDATION"] if pd.notna(row["STATUT_VALIDATION"]) else ""
            ),
            "oec_url": row["OEC_Profile_URL"] if pd.notna(row["OEC_Profile_URL"]) else "",
        }

        print(f"   ✅ {pays} ({code}): PIB={pib_2024}, Pop={pop_2024}")

    print(f"\n📊 STATISTIQUES D'INTÉGRATION")
    print("-" * 40)

    # Statistiques
    pays_avec_pib = sum(1 for v in countries_data.values() if v["gdp_usd_2024"])
    pays_avec_pop = sum(1 for v in countries_data.values() if v["population_2024"])
    pays_ratifies = sum(1 for v in countries_data.values() if v["zlecaf_ratified"] == "Oui")

    print(f"   • Total pays: {len(countries_data)}")
    print(f"   • Avec PIB 2024: {pays_avec_pib}")
    print(f"   • Avec Population 2024: {pays_avec_pop}")
    print(f"   • ZLECAf ratifié: {pays_ratifies}")

    # Mise à jour du fichier country_data.py
    print(f"\n🔄 MISE À JOUR DU FICHIER COUNTRY_DATA.PY")
    print("-" * 40)

    # Créer la structure pour country_data.py
    new_country_data = {}

    for code, data in countries_data.items():
        if data["gdp_usd_2024"] or data["population_2024"]:  # Seulement si on a des données
            new_country_data[code] = {
                "name": data["name"],
                "gdp_usd_2024": float(data["gdp_usd_2024"]) if data["gdp_usd_2024"] else 0,
                "gdp_per_capita_2024": (
                    float(data["gdp_per_capita_2024"]) if data["gdp_per_capita_2024"] else 0
                ),
                "population_2024": float(data["population_2024"]) if data["population_2024"] else 0,
                "development_index": 0.500,  # Valeur par défaut à mettre à jour avec IDH
                "africa_rank": 25,  # À calculer selon PIB ou IDH
                "growth_forecast_2024": (
                    f"{data['growth_2024']:.1f}%" if data["growth_2024"] else "3.0%"
                ),
                "key_sectors": [  # À compléter avec les données sectorielles
                    {"name": "Agriculture", "pib_share": 30.0, "description": "Secteur primaire"},
                    {"name": "Services", "pib_share": 45.0, "description": "Secteur tertiaire"},
                    {"name": "Industrie", "pib_share": 25.0, "description": "Secteur secondaire"},
                ],
                "zlecaf_potential": {
                    "level": "Modéré",
                    "description": f'Potentiel commercial avec ratification ZLECAf: {data["zlecaf_ratified"]}',
                    "key_opportunities": [
                        "Commerce intra-africain",
                        "Intégration régionale",
                        "Réduction tarifaire",
                    ],
                },
                "main_exports": ["Données à compléter"],
                "main_imports": ["Données à compléter"],
            }

    # Sauvegarder les nouvelles données
    with open("/app/country_data_updated.py", "w", encoding="utf-8") as f:
        f.write("# Données économiques mises à jour avec fichier de validation\n")
        f.write("# Sources: UNCTAD, World Bank, PNUD, OEC\n\n")
        f.write("REAL_COUNTRY_DATA = ")
        f.write(json.dumps(new_country_data, indent=4, ensure_ascii=False))
        f.write("\n\n")
        f.write("def get_country_data(country_code):\n")
        f.write(
            '    """Retourne les données économiques réelles d\'un pays ou des données par défaut"""\n'
        )
        f.write("    return REAL_COUNTRY_DATA.get(country_code, {\n")
        f.write("        'name': f'Pays {country_code}',\n")
        f.write("        'gdp_usd_2024': 10000000000,\n")
        f.write("        'gdp_per_capita_2024': 1000,\n")
        f.write("        'development_index': 0.500,\n")
        f.write("        'africa_rank': 25,\n")
        f.write("        'population_2024': 10000000,\n")
        f.write("        'growth_forecast_2024': '3.0%',\n")
        f.write("        'key_sectors': [],\n")
        f.write("        'zlecaf_potential': {'level': 'Modéré'},\n")
        f.write("        'main_exports': [],\n")
        f.write("        'main_imports': []\n")
        f.write("    })\n")

    print(f"✅ Fichier country_data_updated.py créé avec {len(new_country_data)} pays")

    # Créer un CSV mis à jour pour l'application
    print(f"\n📊 CRÉATION CSV POUR L'APPLICATION")
    print("-" * 40)

    df_final = []
    for code, data in new_country_data.items():
        df_final.append(
            {
                "Pays": data["name"],
                "Code_ISO": code,
                "PIB_2024_Mds_USD": data["gdp_usd_2024"] / 1000000000,  # Conversion en milliards
                "Population_2024_M": data["population_2024"] / 1000000,  # Conversion en millions
                "PIB_par_habitant_USD": data["gdp_per_capita_2024"],
                "IDH_2024": data["development_index"],
                "Rang_Afrique": data["africa_rank"],
                "Croissance_2024_Pct": data["growth_forecast_2024"].replace("%", ""),
                "Secteur_1": (
                    data["key_sectors"][0]["name"] if data["key_sectors"] else "Agriculture"
                ),
                "Part_Secteur_1_Pct": (
                    data["key_sectors"][0]["pib_share"] if data["key_sectors"] else 30
                ),
                "Secteur_2": (
                    data["key_sectors"][1]["name"] if len(data["key_sectors"]) > 1 else "Services"
                ),
                "Part_Secteur_2_Pct": (
                    data["key_sectors"][1]["pib_share"] if len(data["key_sectors"]) > 1 else 45
                ),
                "Secteur_3": (
                    data["key_sectors"][2]["name"] if len(data["key_sectors"]) > 2 else "Industrie"
                ),
                "Part_Secteur_3_Pct": (
                    data["key_sectors"][2]["pib_share"] if len(data["key_sectors"]) > 2 else 25
                ),
                "Sources_Principales": countries_data[code].get("sources", ""),
                "Notes_Validation": "Mis à jour avec fichier validation",
            }
        )

    df_csv = pd.DataFrame(df_final)
    df_csv.to_csv("/app/ZLECAF_DATA_UPDATED.csv", index=False, encoding="utf-8")

    print(f"✅ Fichier ZLECAF_DATA_UPDATED.csv créé")

    # Résumé final
    print(f"\n✅ INTÉGRATION TERMINÉE")
    print("=" * 60)
    print("Fichiers créés:")
    print("   • country_data_updated.py - Code Python mis à jour")
    print("   • ZLECAF_DATA_UPDATED.csv - Données CSV pour l'application")
    print("\nProchaines étapes:")
    print("   1. Remplacer country_data.py par country_data_updated.py")
    print("   2. Redémarrer l'application backend")
    print("   3. Tester les nouvelles données")

    return new_country_data


if __name__ == "__main__":
    integrate_validated_data()
