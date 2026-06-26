#!/usr/bin/env python3
"""
Analyser le fichier de validation fourni par l'utilisateur
"""
import numpy as np
import pandas as pd


def analyze_validation_file():
    try:
        # Lire le fichier Excel
        print("📋 ANALYSE DU FICHIER DE VALIDATION FOURNI")
        print("=" * 60)

        # Lire toutes les feuilles
        excel_file = pd.ExcelFile("/app/validation_master.xlsx")
        print(f"📊 Feuilles disponibles: {excel_file.sheet_names}")

        # Analyser chaque feuille
        for sheet_name in excel_file.sheet_names:
            print(f"\n📑 FEUILLE: {sheet_name}")
            print("-" * 40)

            try:
                df = pd.read_excel("/app/validation_master.xlsx", sheet_name=sheet_name)
                print(f"   Dimensions: {df.shape[0]} lignes × {df.shape[1]} colonnes")
                print(f"   Colonnes: {list(df.columns)}")

                # Afficher un aperçu
                if not df.empty:
                    print("\n   📋 Aperçu (5 premières lignes):")
                    print(df.head().to_string())

            except Exception as e:
                print(f"   ❌ Erreur lecture feuille {sheet_name}: {e}")

        # Se concentrer sur la feuille principale (probablement la première)
        main_sheet = excel_file.sheet_names[0]
        df_main = pd.read_excel("/app/validation_master.xlsx", sheet_name=main_sheet)

        print(f"\n🎯 ANALYSE DÉTAILLÉE DE LA FEUILLE PRINCIPALE: {main_sheet}")
        print("=" * 60)
        print(f"Nombre de pays: {len(df_main)}")

        # Identifier les colonnes clés
        colonnes = df_main.columns.tolist()
        print(f"\n📊 COLONNES IDENTIFIÉES:")
        for i, col in enumerate(colonnes, 1):
            print(f"   {i:2d}. {col}")

        # Analyser le contenu
        print(f"\n📈 ÉCHANTILLON DE DONNÉES:")
        if not df_main.empty:
            # Afficher quelques pays pour analyse
            for i in range(min(3, len(df_main))):
                print(f"\n   Pays {i+1}: {df_main.iloc[i].to_dict()}")

        return df_main, excel_file.sheet_names

    except Exception as e:
        print(f"❌ Erreur lors de l'analyse: {e}")
        return None, []


if __name__ == "__main__":
    analyze_validation_file()
