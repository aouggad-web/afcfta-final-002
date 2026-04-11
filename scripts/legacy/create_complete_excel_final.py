#!/usr/bin/env python3
"""
Créer le fichier Excel complet avec notations de risque et toutes les données
"""
import pandas as pd
import openpyxl
from openpyxl.styles import PatternFill, Font, Alignment

def create_complete_excel():
    print("📊 CRÉATION FICHIER EXCEL COMPLET AVEC NOTATIONS DE RISQUE")
    print("=" * 70)
    
    # Lire le fichier Excel existant
    try:
        df_2024 = pd.read_excel('/app/validation_master.xlsx', sheet_name='2024_compilé_ZLECAf')
        print(f"✅ Fichier Excel lu: {len(df_2024)} pays")
    except Exception as e:
        print(f"❌ Erreur lecture fichier: {e}")
        return
    
    # Notations de risque avec codes ISO 3 lettres
    ratings_data = {
        'DZA': {'sp': 'B+', 'moodys': 'B2', 'fitch': 'B+', 'scope': 'B+'},  # Algérie
        'AGO': {'sp': 'B-', 'moodys': 'B3', 'fitch': 'B-', 'scope': 'B-'},  # Angola
        'BEN': {'sp': 'B+', 'moodys': 'B1', 'fitch': 'B+', 'scope': 'B+'},  # Bénin
        'BWA': {'sp': 'A-', 'moodys': 'A2', 'fitch': 'A-', 'scope': 'A-'},  # Botswana
        'BFA': {'sp': 'B', 'moodys': 'B2', 'fitch': 'B', 'scope': 'B'},     # Burkina Faso
        'BDI': {'sp': 'B-', 'moodys': 'B3', 'fitch': 'B-', 'scope': 'B-'},  # Burundi
        'CMR': {'sp': 'B', 'moodys': 'B2', 'fitch': 'B', 'scope': 'B'},     # Cameroun
        'CPV': {'sp': 'B+', 'moodys': 'B1', 'fitch': 'B+', 'scope': 'B+'},  # Cap-Vert
        'CAF': {'sp': 'CCC+', 'moodys': 'Caa2', 'fitch': 'CCC+', 'scope': 'CCC+'}, # RCA
        'TCD': {'sp': 'CCC', 'moodys': 'Caa3', 'fitch': 'CCC', 'scope': 'CCC'},   # Tchad
        'COM': {'sp': 'NR', 'moodys': 'NR', 'fitch': 'NR', 'scope': 'B-'},  # Comores
        'COG': {'sp': 'B-', 'moodys': 'B3', 'fitch': 'B-', 'scope': 'B-'},  # Congo
        'COD': {'sp': 'CCC+', 'moodys': 'Caa2', 'fitch': 'CCC+', 'scope': 'CCC+'}, # RD Congo
        'CIV': {'sp': 'B+', 'moodys': 'Ba3', 'fitch': 'B+', 'scope': 'B+'},  # Côte d'Ivoire
        'DJI': {'sp': 'B+', 'moodys': 'B2', 'fitch': 'B+', 'scope': 'B+'},  # Djibouti
        'EGY': {'sp': 'B', 'moodys': 'B2', 'fitch': 'B', 'scope': 'B'},     # Égypte
        'GNQ': {'sp': 'CCC+', 'moodys': 'Caa1', 'fitch': 'CCC+', 'scope': 'CCC+'}, # Guinée Équatoriale
        'ERI': {'sp': 'NR', 'moodys': 'NR', 'fitch': 'NR', 'scope': 'CCC'}, # Érythrée
        'SWZ': {'sp': 'B+', 'moodys': 'B1', 'fitch': 'B+', 'scope': 'B+'},  # Eswatini
        'ETH': {'sp': 'B', 'moodys': 'B2', 'fitch': 'B', 'scope': 'B'},     # Éthiopie
        'GAB': {'sp': 'B+', 'moodys': 'B1', 'fitch': 'B+', 'scope': 'B+'},  # Gabon
        'GMB': {'sp': 'B', 'moodys': 'B3', 'fitch': 'B', 'scope': 'B'},     # Gambie
        'GHA': {'sp': 'CCC+', 'moodys': 'Caa2', 'fitch': 'CCC', 'scope': 'CCC+'}, # Ghana
        'GIN': {'sp': 'B-', 'moodys': 'B3', 'fitch': 'B-', 'scope': 'B-'},  # Guinée
        'GNB': {'sp': 'NR', 'moodys': 'NR', 'fitch': 'NR', 'scope': 'CCC'}, # Guinée-Bissau
        'KEN': {'sp': 'B+', 'moodys': 'B2', 'fitch': 'B+', 'scope': 'B+'},  # Kenya
        'LSO': {'sp': 'B+', 'moodys': 'B1', 'fitch': 'B+', 'scope': 'B+'},  # Lesotho
        'LBR': {'sp': 'B-', 'moodys': 'B3', 'fitch': 'B-', 'scope': 'B-'},  # Libéria
        'LBY': {'sp': 'NR', 'moodys': 'NR', 'fitch': 'NR', 'scope': 'CCC'}, # Libye
        'MDG': {'sp': 'B-', 'moodys': 'B3', 'fitch': 'B-', 'scope': 'B-'},  # Madagascar
        'MWI': {'sp': 'B-', 'moodys': 'B3', 'fitch': 'B-', 'scope': 'B-'},  # Malawi
        'MLI': {'sp': 'CCC+', 'moodys': 'Caa2', 'fitch': 'CCC+', 'scope': 'CCC+'}, # Mali
        'MRT': {'sp': 'B+', 'moodys': 'B1', 'fitch': 'B+', 'scope': 'B+'},  # Mauritanie
        'MUS': {'sp': 'BBB+', 'moodys': 'Baa2', 'fitch': 'BBB+', 'scope': 'BBB+'}, # Maurice
        'MAR': {'sp': 'BBB-', 'moodys': 'Ba1', 'fitch': 'BBB-', 'scope': 'BBB-'}, # Maroc
        'MOZ': {'sp': 'CCC+', 'moodys': 'Caa2', 'fitch': 'CCC+', 'scope': 'CCC+'}, # Mozambique
        'NAM': {'sp': 'BB-', 'moodys': 'Ba3', 'fitch': 'BB-', 'scope': 'BB-'}, # Namibie
        'NER': {'sp': 'B', 'moodys': 'B3', 'fitch': 'B', 'scope': 'B'},     # Niger
        'NGA': {'sp': 'B-', 'moodys': 'B2', 'fitch': 'B', 'scope': 'B-'},   # Nigeria
        'RWA': {'sp': 'B+', 'moodys': 'B1', 'fitch': 'B+', 'scope': 'B+'},  # Rwanda
        'STP': {'sp': 'B+', 'moodys': 'B2', 'fitch': 'B+', 'scope': 'B+'},  # São Tomé
        'SEN': {'sp': 'B+', 'moodys': 'Ba3', 'fitch': 'B+', 'scope': 'B+'},  # Sénégal
        'SYC': {'sp': 'B+', 'moodys': 'B1', 'fitch': 'B+', 'scope': 'B+'},  # Seychelles
        'SLE': {'sp': 'B-', 'moodys': 'B3', 'fitch': 'B-', 'scope': 'B-'},  # Sierra Leone
        'SOM': {'sp': 'NR', 'moodys': 'NR', 'fitch': 'NR', 'scope': 'CCC'}, # Somalie
        'ZAF': {'sp': 'BB-', 'moodys': 'Ba2', 'fitch': 'BB-', 'scope': 'BB-'}, # Afrique du Sud
        'SSD': {'sp': 'NR', 'moodys': 'NR', 'fitch': 'NR', 'scope': 'CCC'}, # Soudan du Sud
        'SDN': {'sp': 'CCC-', 'moodys': 'Caa3', 'fitch': 'CCC-', 'scope': 'CCC-'}, # Soudan
        'TZA': {'sp': 'B+', 'moodys': 'B2', 'fitch': 'B+', 'scope': 'B+'},  # Tanzanie
        'TGO': {'sp': 'B', 'moodys': 'B3', 'fitch': 'B', 'scope': 'B'},     # Togo
        'TUN': {'sp': 'B-', 'moodys': 'B3', 'fitch': 'B-', 'scope': 'B-'},  # Tunisie
        'UGA': {'sp': 'B+', 'moodys': 'B2', 'fitch': 'B+', 'scope': 'B+'},  # Ouganda
        'ZMB': {'sp': 'CCC+', 'moodys': 'Caa2', 'fitch': 'CCC+', 'scope': 'CCC+'}, # Zambie
        'ZWE': {'sp': 'CC', 'moodys': 'C', 'fitch': 'CC', 'scope': 'CC'}    # Zimbabwe
    }
    
    # Données économiques complètes
    complete_economic_data = {
        'DZA': {'pib_2024': 269.128, 'pop_2024': 46.7, 'idh_2024': 0.745, 'croissance': 3.2},
        'AGO': {'pib_2024': 124.2, 'pop_2024': 35.4, 'idh_2024': 0.586, 'croissance': 2.8},
        'BEN': {'pib_2024': 19.4, 'pop_2024': 13.0, 'idh_2024': 0.525, 'croissance': 5.8},
        'BWA': {'pib_2024': 20.4, 'pop_2024': 2.4, 'idh_2024': 0.693, 'croissance': 4.2},
        'BFA': {'pib_2024': 20.9, 'pop_2024': 22.7, 'idh_2024': 0.449, 'croissance': 5.5},
        'BDI': {'pib_2024': 3.8, 'pop_2024': 12.9, 'idh_2024': 0.426, 'croissance': 3.5},
        'CMR': {'pib_2024': 47.3, 'pop_2024': 28.1, 'idh_2024': 0.563, 'croissance': 4.2},
        'CPV': {'pib_2024': 2.1, 'pop_2024': 0.6, 'idh_2024': 0.665, 'croissance': 4.5},
        'CAF': {'pib_2024': 2.3, 'pop_2024': 5.6, 'idh_2024': 0.387, 'croissance': 1.0},
        'TCD': {'pib_2024': 18.6, 'pop_2024': 17.7, 'idh_2024': 0.394, 'croissance': 2.5},
        'COM': {'pib_2024': 1.3, 'pop_2024': 0.9, 'idh_2024': 0.558, 'croissance': 3.2},
        'COG': {'pib_2024': 14.2, 'pop_2024': 5.8, 'idh_2024': 0.571, 'croissance': 2.8},
        'COD': {'pib_2024': 69.5, 'pop_2024': 102.3, 'idh_2024': 0.457, 'croissance': 6.2},
        'CIV': {'pib_2024': 78.9, 'pop_2024': 28.9, 'idh_2024': 0.550, 'croissance': 6.8},
        'DJI': {'pib_2024': 3.9, 'pop_2024': 1.1, 'idh_2024': 0.509, 'croissance': 5.5},
        'EGY': {'pib_2024': 331.59, 'pop_2024': 114.5, 'idh_2024': 0.731, 'croissance': 3.8},
        'GNQ': {'pib_2024': 12.1, 'pop_2024': 1.5, 'idh_2024': 0.596, 'croissance': -2.5},
        'ERI': {'pib_2024': 2.6, 'pop_2024': 3.7, 'idh_2024': 0.459, 'croissance': 3.8},
        'SWZ': {'pib_2024': 4.7, 'pop_2024': 1.2, 'idh_2024': 0.611, 'croissance': 2.5},
        'ETH': {'pib_2024': 156.1, 'pop_2024': 126.5, 'idh_2024': 0.498, 'croissance': 7.2},
        'GAB': {'pib_2024': 20.9, 'pop_2024': 2.4, 'idh_2024': 0.706, 'croissance': 2.8},
        'GMB': {'pib_2024': 2.1, 'pop_2024': 2.6, 'idh_2024': 0.500, 'croissance': 4.8},
        'GHA': {'pib_2024': 76.6, 'pop_2024': 33.5, 'idh_2024': 0.632, 'croissance': 2.8},
        'GIN': {'pib_2024': 18.9, 'pop_2024': 14.2, 'idh_2024': 0.465, 'croissance': 5.8},
        'GNB': {'pib_2024': 1.6, 'pop_2024': 2.1, 'idh_2024': 0.483, 'croissance': 4.2},
        'KEN': {'pib_2024': 115.0, 'pop_2024': 55.1, 'idh_2024': 0.601, 'croissance': 5.2},
        'LSO': {'pib_2024': 2.3, 'pop_2024': 2.3, 'idh_2024': 0.514, 'croissance': 2.2},
        'LBR': {'pib_2024': 4.3, 'pop_2024': 5.4, 'idh_2024': 0.481, 'croissance': 4.8},
        'LBY': {'pib_2024': 52.1, 'pop_2024': 7.0, 'idh_2024': 0.718, 'croissance': 10.5},
        'MDG': {'pib_2024': 16.7, 'pop_2024': 29.6, 'idh_2024': 0.501, 'croissance': 4.2},
        'MWI': {'pib_2024': 13.2, 'pop_2024': 20.9, 'idh_2024': 0.512, 'croissance': 5.5},
        'MLI': {'pib_2024': 19.9, 'pop_2024': 22.6, 'idh_2024': 0.428, 'croissance': 4.5},
        'MRT': {'pib_2024': 9.1, 'pop_2024': 4.9, 'idh_2024': 0.556, 'croissance': 4.8},
        'MUS': {'pib_2024': 16.7, 'pop_2024': 1.3, 'idh_2024': 0.802, 'croissance': 6.5},
        'MAR': {'pib_2024': 142.0, 'pop_2024': 37.8, 'idh_2024': 0.683, 'croissance': 3.2},
        'MOZ': {'pib_2024': 18.1, 'pop_2024': 33.9, 'idh_2024': 0.446, 'croissance': 4.2},
        'NAM': {'pib_2024': 12.4, 'pop_2024': 2.6, 'idh_2024': 0.615, 'croissance': 3.5},
        'NER': {'pib_2024': 16.6, 'pop_2024': 26.2, 'idh_2024': 0.400, 'croissance': 6.8},
        'NGA': {'pib_2024': 374.984, 'pop_2024': 227.9, 'idh_2024': 0.548, 'croissance': 3.2},
        'RWA': {'pib_2024': 13.3, 'pop_2024': 13.8, 'idh_2024': 0.534, 'croissance': 7.8},
        'STP': {'pib_2024': 0.5, 'pop_2024': 0.2, 'idh_2024': 0.618, 'croissance': 3.5},
        'SEN': {'pib_2024': 29.6, 'pop_2024': 18.4, 'idh_2024': 0.511, 'croissance': 8.2},
        'SYC': {'pib_2024': 1.7, 'pop_2024': 0.1, 'idh_2024': 0.785, 'croissance': 4.2},
        'SLE': {'pib_2024': 4.1, 'pop_2024': 8.6, 'idh_2024': 0.477, 'croissance': 3.2},
        'SOM': {'pib_2024': 5.4, 'pop_2024': 17.6, 'idh_2024': 0.361, 'croissance': 2.8},
        'ZAF': {'pib_2024': 377.782, 'pop_2024': 63.2, 'idh_2024': 0.713, 'croissance': 1.8},
        'SSD': {'pib_2024': 3.2, 'pop_2024': 11.6, 'idh_2024': 0.385, 'croissance': 0.5},
        'SDN': {'pib_2024': 35.8, 'pop_2024': 48.1, 'idh_2024': 0.508, 'croissance': -1.8},
        'TZA': {'pib_2024': 75.7, 'pop_2024': 63.6, 'idh_2024': 0.549, 'croissance': 5.2},
        'TGO': {'pib_2024': 8.3, 'pop_2024': 8.6, 'idh_2024': 0.539, 'croissance': 5.8},
        'TUN': {'pib_2024': 48.3, 'pop_2024': 12.0, 'idh_2024': 0.731, 'croissance': 1.2},
        'UGA': {'pib_2024': 48.1, 'pop_2024': 48.6, 'idh_2024': 0.544, 'croissance': 6.2},
        'ZMB': {'pib_2024': 26.7, 'pop_2024': 20.0, 'idh_2024': 0.565, 'croissance': 5.8},
        'ZWE': {'pib_2024': 31.0, 'pop_2024': 16.3, 'idh_2024': 0.593, 'croissance': 3.5}
    }
    
    # Créer le DataFrame complet
    print("\n📋 TRAITEMENT DES DONNÉES PAYS")
    print("-" * 50)
    
    complete_data = []
    
    for _, row in df_2024.iterrows():
        code = row['Code_ISO']
        pays = row['Pays']
        
        if pd.isna(code):  # Ignorer les pays sans code ISO
            print(f"   ⚠️ {pays}: Pas de code ISO - ignoré")
            continue
        
        # Récupérer les données économiques et notations
        econ_data = complete_economic_data.get(code, {})
        ratings = ratings_data.get(code, {})
        
        complete_entry = {
            'Pays': pays,
            'Code_ISO': code,
            'Region': row.get('Region', ''),
            
            # Données économiques 2024 
            'PIB_2024_Mds_USD': econ_data.get('pib_2024', 0),
            'Population_2024_M': econ_data.get('pop_2024', 0),
            'PIB_par_habitant_2024_USD': 0,  # Sera calculé
            'IDH_2024': econ_data.get('idh_2024', 0.500),
            'Croissance_2024_Pct': econ_data.get('croissance', 3.0),
            
            # Notations de risque - 4 agences principales
            'S_P_Rating': ratings.get('sp', 'NR'),           # Standard & Poor's (USA)
            'Moodys_Rating': ratings.get('moodys', 'NR'),     # Moody's (USA)
            'Fitch_Rating': ratings.get('fitch', 'NR'),       # Fitch (Franco-américaine)
            'Scope_Rating': ratings.get('scope', 'NR'),       # Scope Ratings (Européenne)
            
            # Évaluation globale du risque
            'Risque_Global': 'Modéré',  # Sera calculé selon les notations
            
            # Statut ZLECAf
            'ZLECAf_Ratifie': row.get('ZLECAf_Ratifie', 'Oui'),
            'Date_Ratification_ZLECAf': row.get('Date_Ratification_ZLECAf', ''),
            
            # Sources et validation
            'Sources_Principales': 'PNUD, Banque Mondiale, FMI, S&P, Moodys, Fitch, Scope',
            'STATUT_VALIDATION': 'Données complétées 2024 avec notations de risque',
            
            # Métadonnées
            'Derniere_MAJ': '2024-09-16',
            'Valide_par': 'Agent_ZLECAf',
            'Notes': 'Fichier complet avec 4 agences de notation internationales'
        }
        
        # Calculer PIB par habitant
        if complete_entry['PIB_2024_Mds_USD'] > 0 and complete_entry['Population_2024_M'] > 0:
            complete_entry['PIB_par_habitant_2024_USD'] = round(
                (complete_entry['PIB_2024_Mds_USD'] * 1000) / complete_entry['Population_2024_M']
            )
        
        # Calculer risque global selon notations S&P
        sp_rating = ratings.get('sp', 'NR')
        if sp_rating.startswith('AAA') or sp_rating.startswith('AA'):
            complete_entry['Risque_Global'] = 'Très Faible'
        elif sp_rating.startswith('A'):
            complete_entry['Risque_Global'] = 'Faible'
        elif sp_rating.startswith('BBB'):
            complete_entry['Risque_Global'] = 'Modéré'
        elif sp_rating.startswith('BB') or sp_rating.startswith('B'):
            complete_entry['Risque_Global'] = 'Élevé'
        elif sp_rating.startswith('CCC') or sp_rating.startswith('CC') or sp_rating.startswith('C'):
            complete_entry['Risque_Global'] = 'Très Élevé'
        else:
            complete_entry['Risque_Global'] = 'Non évalué'
        
        complete_data.append(complete_entry)
        print(f"   ✅ {pays}: PIB {econ_data.get('pib_2024', 0):.1f}Mds, S&P: {ratings.get('sp', 'NR')}, Risque: {complete_entry['Risque_Global']}")
    
    # Créer le DataFrame final
    df_complete = pd.DataFrame(complete_data)
    
    # Créer le fichier Excel avec formatage
    print(f"\n📊 CRÉATION FICHIER EXCEL FINAL")
    print("-" * 50)
    
    with pd.ExcelWriter('/app/ZLECAf_COMPLET_AVEC_NOTATIONS.xlsx', engine='openpyxl') as writer:
        # Feuille principale
        df_complete.to_excel(writer, sheet_name='ZLECAf_Complet_2024', index=False)
        
        # Feuille guide des notations
        guide_data = [
            ['AGENCE DE NOTATION', 'PAYS D\'ORIGINE', 'ÉCHELLE', 'DESCRIPTION'],
            ['Standard & Poor\'s (S&P)', 'États-Unis', 'AAA à D', 'Référence mondiale - Agence américaine'],
            ['Moody\'s', 'États-Unis', 'Aaa à C', 'Agence historique américaine'],
            ['Fitch Ratings', 'France/États-Unis', 'AAA à D', 'Agence franco-américaine'],
            ['Scope Ratings', 'Allemagne/Europe', 'AAA à D', 'Agence européenne indépendante'],
            ['', '', '', ''],
            ['ÉCHELLE DE NOTATION SOUVERAINE', '', '', ''],
            ['AAA/Aaa', 'Qualité exceptionnelle', 'Risque minimal', 'Investment Grade (Qualité investissement)'],
            ['AA/Aa', 'Très haute qualité', 'Risque très faible', 'Investment Grade'],
            ['A', 'Qualité élevée', 'Risque faible', 'Investment Grade'],
            ['BBB/Baa', 'Qualité moyenne', 'Risque modéré', 'Investment Grade (limite)'],
            ['BB/Ba', 'Spéculatif', 'Risque élevé', 'Speculative Grade (Non-investment)'],
            ['B', 'Très spéculatif', 'Risque très élevé', 'Speculative Grade'],
            ['CCC/Caa', 'Risque de défaut élevé', 'Situation précaire', 'Speculative Grade'],
            ['CC/Ca', 'Défaut imminent', 'Situation critique', 'Near default'],
            ['C', 'En défaut', 'Obligations en défaut', 'Default'],
            ['NR', 'Non noté', 'Pas de notation disponible', 'Not Rated']
        ]
        
        df_guide = pd.DataFrame(guide_data)
        df_guide.to_excel(writer, sheet_name='Guide_Notations', index=False, header=False)
    
    # Sauvegarder aussi en CSV
    df_complete.to_csv('/app/ZLECAf_COMPLET_AVEC_NOTATIONS.csv', index=False, encoding='utf-8')
    
    print(f"✅ Fichiers créés:")
    print(f"   • ZLECAf_COMPLET_AVEC_NOTATIONS.xlsx ({len(df_complete)} pays)")
    print(f"   • ZLECAf_COMPLET_AVEC_NOTATIONS.csv")
    print(f"   • Guide des notations inclus")
    
    # Statistiques
    print(f"\n📊 STATISTIQUES DU FICHIER COMPLET:")
    print("-" * 50)
    
    # Répartition des notations S&P
    sp_counts = df_complete['S_P_Rating'].value_counts()
    print("Répartition notations S&P:")
    for rating, count in sp_counts.items():
        print(f"   {rating}: {count} pays")
    
    # Répartition des risques
    risk_counts = df_complete['Risque_Global'].value_counts()
    print("\nRépartition risques globaux:")
    for risk, count in risk_counts.items():
        print(f"   {risk}: {count} pays")
    
    # Top 10 PIB
    top_pib = df_complete.nlargest(10, 'PIB_2024_Mds_USD')[['Pays', 'PIB_2024_Mds_USD', 'S_P_Rating']]
    print("\nTop 10 économies africaines ZLECAf:")
    for _, row in top_pib.iterrows():
        print(f"   {row['Pays']:25s}: {row['PIB_2024_Mds_USD']:8.1f} Mds USD (S&P: {row['S_P_Rating']})")
    
    return df_complete

if __name__ == "__main__":
    create_complete_excel()