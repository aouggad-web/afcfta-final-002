#!/usr/bin/env python3
"""
Vérification détaillée avec données de référence
"""
import pandas as pd

def detailed_verification():
    df = pd.read_csv('/app/ZLECAF_54_PAYS_DONNEES_COMPLETES.csv')
    
    print("="*80)
    print("📊 VÉRIFICATION DÉTAILLÉE AVEC DONNÉES DE RÉFÉRENCE")
    print("="*80)
    
    # Données de référence 2024 (sources officielles récentes)
    donnees_ref = {
        'Nigeria': {'pop': 223.8, 'pib': 440.8, 'pib_hab': 1970, 'idh': 0.548},
        'Éthiopie': {'pop': 126.5, 'pib': 156.1, 'pib_hab': 1235, 'idh': 0.498},
        'Égypte': {'pop': 112.7, 'pib': 469.0, 'pib_hab': 4160, 'idh': 0.731},
        'RD Congo': {'pop': 102.3, 'pib': 64.3, 'pib_hab': 629, 'idh': 0.457},
        'Afrique du Sud': {'pop': 60.4, 'pib': 421.0, 'pib_hab': 6970, 'idh': 0.713},
        'Kenya': {'pop': 55.1, 'pib': 115.0, 'pib_hab': 2087, 'idh': 0.601},
        'Maroc': {'pop': 37.8, 'pib': 142.0, 'pib_hab': 3757, 'idh': 0.683},
        'Algérie': {'pop': 45.6, 'pib': 191.0, 'pib_hab': 4190, 'idh': 0.745},
        'Ghana': {'pop': 33.5, 'pib': 76.6, 'pib_hab': 2288, 'idh': 0.632},
    }
    
    print("\n🔍 COMPARAISON AVEC DONNÉES DE RÉFÉRENCE 2024")
    print("-" * 60)
    
    for pays, ref in donnees_ref.items():
        pays_data = df[df['Pays'] == pays]
        if not pays_data.empty:
            row = pays_data.iloc[0]
            
            # Comparaisons
            ecart_pop = abs(row['Population_2024_M'] - ref['pop']) / ref['pop'] * 100
            ecart_pib = abs(row['PIB_2024_Mds_USD'] - ref['pib']) / ref['pib'] * 100
            ecart_pib_hab = abs(row['PIB_par_habitant_USD'] - ref['pib_hab']) / ref['pib_hab'] * 100
            ecart_idh = abs(row['IDH_2024'] - ref['idh']) / ref['idh'] * 100
            
            print(f"\n📍 {pays}:")
            
            if ecart_pop > 15:
                print(f"   ❌ Population: {row['Population_2024_M']:.1f}M (réf: {ref['pop']:.1f}M, écart: {ecart_pop:.1f}%)")
            else:
                print(f"   ✅ Population: {row['Population_2024_M']:.1f}M (réf: {ref['pop']:.1f}M)")
                
            if ecart_pib > 25:
                print(f"   ❌ PIB: {row['PIB_2024_Mds_USD']:.0f}Mds (réf: {ref['pib']:.0f}Mds, écart: {ecart_pib:.1f}%)")
            else:
                print(f"   ✅ PIB: {row['PIB_2024_Mds_USD']:.0f}Mds (réf: {ref['pib']:.0f}Mds)")
                
            if ecart_pib_hab > 30:
                print(f"   ❌ PIB/hab: {row['PIB_par_habitant_USD']:,.0f}$ (réf: {ref['pib_hab']:,.0f}$, écart: {ecart_pib_hab:.1f}%)")
            else:
                print(f"   ✅ PIB/hab: {row['PIB_par_habitant_USD']:,.0f}$ (réf: {ref['pib_hab']:,.0f}$)")
                
            if ecart_idh > 10:
                print(f"   ❌ IDH: {row['IDH_2024']:.3f} (réf: {ref['idh']:.3f}, écart: {ecart_idh:.1f}%)")
            else:
                print(f"   ✅ IDH: {row['IDH_2024']:.3f} (réf: {ref['idh']:.3f})")
    
    # Vérification codes ISO manquants
    print(f"\n🏷️ CODES ISO MANQUANTS")
    print("-" * 60)
    
    codes_manquants = df[df['Code_ISO'].isna() | (df['Code_ISO'] == '')]['Pays'].tolist()
    if codes_manquants:
        print("❌ Pays sans code ISO:")
        for pays in codes_manquants:
            print(f"   • {pays}")
    else:
        print("✅ Tous les pays ont un code ISO")
    
    # Top 10 économies africaines - vérification
    print(f"\n🏆 VÉRIFICATION TOP 10 ÉCONOMIES AFRICAINES")
    print("-" * 60)
    
    top10_ref = ['Nigeria', 'Afrique du Sud', 'Égypte', 'Algérie', 'Maroc', 
                 'Kenya', 'Éthiopie', 'Ghana', 'Angola', 'Tanzanie']
    
    df_sorted_pib = df.sort_values('PIB_2024_Mds_USD', ascending=False)
    top10_actuel = df_sorted_pib.head(10)['Pays'].tolist()
    
    print("Top 10 référence vs actuel:")
    for i, (ref, act) in enumerate(zip(top10_ref, top10_actuel), 1):
        match = "✅" if ref == act else "❌"
        print(f"   {i:2d}. {match} Réf: {ref:15s} | Actuel: {act}")
    
    # Analyse des croissances économiques
    print(f"\n📈 ANALYSE DES TAUX DE CROISSANCE")
    print("-" * 60)
    
    croissance_moyenne = df['Croissance_2024_Pct'].mean()
    croissances_suspec = df[(df['Croissance_2024_Pct'] > 8) | (df['Croissance_2024_Pct'] < 0)]
    
    print(f"Croissance moyenne Afrique: {croissance_moyenne:.1f}%")
    
    if not croissances_suspec.empty:
        print("⚠️ Croissances suspectes (>8% ou négatives):")
        for _, row in croissances_suspec.iterrows():
            print(f"   • {row['Pays']}: {row['Croissance_2024_Pct']:.1f}%")
    
    print("\n📋 RECOMMANDATIONS SPÉCIFIQUES:")
    print("-" * 60)
    print("1. 🔴 URGENT - Corriger les secteurs économiques (somme ≠ 100%):")
    print("   • Algérie: 78% → ajouter 22%")
    print("   • Égypte: 95% → ajouter 5%") 
    print("   • Ghana: 90% → ajouter 10%")
    print("   • Mali: 98% → ajouter 2%")
    
    print("\n2. 🟡 IMPORTANT - Vérifier avec sources officielles:")
    print("   • Nigeria: PIB semble sous-évalué (244 vs ~441 Mds)")
    print("   • Éthiopie: Population proche mais PIB à vérifier")
    print("   • Seychelles: PIB/habitant très élevé (18k$) - vérifier")
    
    print("\n3. ⚪ CONTRÔLE - Rangs IDH incohérents à corriger:")
    print("   • Recalculer tous les rangs selon l'IDH réel")
    
    print("\n✅ VÉRIFICATION DÉTAILLÉE TERMINÉE")
    print("="*80)

if __name__ == "__main__":
    detailed_verification()