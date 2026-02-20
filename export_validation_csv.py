#!/usr/bin/env python3
"""
Exporter le fichier de validation en CSV pour l'utilisateur
"""
import pandas as pd


def export_to_csv():
    # Lire le fichier CSV original
    df = pd.read_csv('/app/ZLECAF_54_PAYS_DONNEES_COMPLETES.csv')

    # Créer le fichier de validation avec colonnes supplémentaires
    validation_df = df.copy()

    # Ajouter les colonnes de validation
    validation_df['STATUT_VALIDATION'] = validation_df['Notes_Validation']
    validation_df['CORRECTIONS_PIB'] = ''
    validation_df['CORRECTIONS_POPULATION'] = ''
    validation_df['CORRECTIONS_IDH'] = ''
    validation_df['CORRECTIONS_SECTEURS'] = ''
    validation_df['SOURCES_SUPPLEMENTAIRES'] = ''
    validation_df['COMMENTAIRES'] = ''
    validation_df['VALIDE_PAR'] = ''
    validation_df['DATE_VALIDATION'] = ''

    # Réorganiser les colonnes pour faciliter la validation
    columns_final = [
        'Pays', 'Code_ISO', 'STATUT_VALIDATION', 'PIB_2024_Mds_USD',
        'CORRECTIONS_PIB', 'Population_2024_M', 'CORRECTIONS_POPULATION',
        'PIB_par_habitant_USD', 'IDH_2024', 'CORRECTIONS_IDH',
        'Rang_Afrique_IDH', 'Croissance_2024_Pct', 'Secteur_1',
        'Part_Secteur_1_Pct', 'Secteur_2', 'Part_Secteur_2_Pct', 'Secteur_3',
        'Part_Secteur_3_Pct', 'CORRECTIONS_SECTEURS', 'Sources_Principales',
        'SOURCES_SUPPLEMENTAIRES', 'COMMENTAIRES', 'VALIDE_PAR',
        'DATE_VALIDATION'
    ]

    validation_final = validation_df[columns_final]

    # Sauvegarder en CSV
    validation_final.to_csv('/app/ZLECAF_VALIDATION.csv',
                            index=False,
                            encoding='utf-8')

    print("✅ Fichier CSV de validation créé: /app/ZLECAF_VALIDATION.csv")

    # Afficher un aperçu
    print("\n📋 APERÇU DU FICHIER (5 premiers pays):")
    print(validation_final.head().to_string())

    # Statistiques
    status_counts = validation_df['Notes_Validation'].value_counts()
    print(f"\n📊 RÉPARTITION:")
    for status, count in status_counts.items():
        print(f"   • {status}: {count} pays")

    return validation_final


if __name__ == "__main__":
    export_to_csv()
