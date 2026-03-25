#!/usr/bin/env python3
"""
Appliquer les corrections aux fichiers backend
"""
import json
import re

def apply_tariff_corrections():
    """Appliquer les corrections tarifaires au server.py"""
    print("🔧 APPLICATION DES CORRECTIONS TARIFAIRES")
    print("=" * 60)
    
    # Lire les corrections
    with open('/app/zlecaf_corrections_2024.json', 'r', encoding='utf-8') as f:
        corrections = json.load(f)
    
    # Lire le fichier server.py
    with open('/app/backend/server.py', 'r', encoding='utf-8') as f:
        server_content = f.read()
    
    # Extraire les taux corrigés
    normal_rates = corrections['tariff_corrections']['normal_rates']
    zlecaf_rates = corrections['tariff_corrections']['zlecaf_rates']
    
    # Créer les nouvelles structures de taux
    normal_rates_str = '{\n'
    for hs2, rate in normal_rates.items():
        normal_rates_str += f'        "{hs2}": {rate:.2f}, '
    normal_rates_str = normal_rates_str.rstrip(', ') + '\n    }'
    
    zlecaf_rates_str = '{\n'
    for hs2, rate in zlecaf_rates.items():
        zlecaf_rates_str += f'        "{hs2}": {rate:.2f}, '
    zlecaf_rates_str = zlecaf_rates_str.rstrip(', ') + '\n    }'
    
    # Remplacer les anciens taux dans le fichier
    # Pattern pour normal_rates
    normal_pattern = r'normal_rates = \{[^}]+\}'
    server_content = re.sub(normal_pattern, f'normal_rates = {normal_rates_str}', server_content, flags=re.DOTALL)
    
    # Pattern pour zlecaf_rates
    zlecaf_pattern = r'zlecaf_rates = \{[^}]+\}'
    server_content = re.sub(zlecaf_pattern, f'zlecaf_rates = {zlecaf_rates_str}', server_content, flags=re.DOTALL)
    
    # Écrire le fichier modifié
    with open('/app/backend/server.py', 'w', encoding='utf-8') as f:
        f.write(server_content)
    
    print(f"   ✅ Taux normaux mis à jour: {len(normal_rates)} secteurs")
    print(f"   ✅ Taux ZLECAf mis à jour: {len(zlecaf_rates)} secteurs")
    print(f"   ✅ Fichier server.py modifié avec succès")

def apply_statistics_corrections():
    """Appliquer les corrections statistiques au server.py"""
    print(f"\n📊 APPLICATION DES CORRECTIONS STATISTIQUES")
    print("=" * 60)
    
    # Lire les corrections
    with open('/app/zlecaf_corrections_2024.json', 'r', encoding='utf-8') as f:
        corrections = json.load(f)
    
    enhanced_stats = corrections['enhanced_statistics']
    
    # Lire le fichier server.py
    with open('/app/backend/server.py', 'r', encoding='utf-8') as f:
        server_content = f.read()
    
    # Créer la nouvelle fonction de statistiques
    new_stats_function = f'''@api_router.get("/statistics")
async def get_comprehensive_statistics():
    """Récupérer les statistiques complètes ZLECAf avec données OEC 2023-2024"""
    
    # Statistiques de base depuis MongoDB
    total_calculations = await db.comprehensive_calculations.count_documents({{}})
    
    # Économies totales calculées
    pipeline_savings = [
        {{"$group": {{"_id": None, "total_savings": {{"$sum": "$savings"}}}}}}
    ]
    savings_result = await db.comprehensive_calculations.aggregate(pipeline_savings).to_list(1)
    total_savings = savings_result[0]["total_savings"] if savings_result else 0
    
    # Statistiques enrichies avec données OEC 2023-2024
    return {{
        "overview": {{
            "total_calculations": total_calculations,
            "total_savings": total_savings,
            "african_countries_members": {enhanced_stats['overview']['african_countries_members']},
            "combined_population": {enhanced_stats['overview']['combined_population']},
            "estimated_combined_gdp": {enhanced_stats['overview']['estimated_combined_gdp']},
            "zlecaf_implementation_status": "{enhanced_stats['overview']['zlecaf_implementation_status']}"
        }},
        
        "trade_evolution_2023_2024": {{
            "intra_african_trade_2023_mds_usd": {enhanced_stats['trade_evolution']['intra_african_trade_2023']},
            "intra_african_trade_2024_mds_usd": {enhanced_stats['trade_evolution']['intra_african_trade_2024']},
            "growth_rate_percent": {enhanced_stats['trade_evolution']['growth_rate_2023_2024']},
            "trend_analysis": "{enhanced_stats['trade_evolution']['trend']}"
        }},
        
        "top_exporters_2024": {json.dumps(enhanced_stats['top_exporters_2024'], ensure_ascii=False)},
        "top_importers_2024": {json.dumps(enhanced_stats['top_importers_2024'], ensure_ascii=False)},
        
        "product_analysis": {{
            "top_traded_products_2024": {json.dumps(enhanced_stats['product_analysis']['top_traded_products_2024'], ensure_ascii=False)},
            "diversification_index": {enhanced_stats['product_analysis']['diversification_index']},
            "sector_breakdown": {{
                "manufacturing_share_percent": {enhanced_stats['product_analysis']['manufacturing_share']},
                "raw_materials_share_percent": {enhanced_stats['product_analysis']['raw_materials_share']},
                "agricultural_share_percent": {enhanced_stats['product_analysis']['agricultural_share']},
                "services_share_percent": {enhanced_stats['product_analysis']['services_share']}
            }}
        }},
        
        "regional_integration": {{
            "intra_regional_flows_2024": {json.dumps(enhanced_stats['regional_integration']['intra_regional_flows_2024'], ensure_ascii=False)},
            "integration_score": {enhanced_stats['regional_integration']['integration_score']},
            "corridor_performance": {json.dumps(enhanced_stats['regional_integration']['corridor_performance'], ensure_ascii=False)}
        }},
        
        "sector_performance": {{
            "growth_by_sector_2023_2024": {json.dumps(enhanced_stats['sector_performance']['growth_by_sector'], ensure_ascii=False)},
            "promising_sectors": {json.dumps(enhanced_stats['sector_performance']['promising_sectors'], ensure_ascii=False)}
        }},
        
        "zlecaf_impact_2024": {{
            "tariff_elimination_progress": "{enhanced_stats['zlecaf_impact_metrics']['tariff_elimination_progress']}",
            "non_tariff_barriers_reduced": "{enhanced_stats['zlecaf_impact_metrics']['non_tariff_barriers_reduced']}",
            "trade_facilitation_score": {enhanced_stats['zlecaf_impact_metrics']['trade_facilitation_score']},
            "estimated_job_creation": "{enhanced_stats['zlecaf_impact_metrics']['estimated_job_creation']}",
            "sme_participation_increase": "{enhanced_stats['zlecaf_impact_metrics']['sme_participation_increase']}",
            "women_trade_participation": "{enhanced_stats['zlecaf_impact_metrics']['women_trade_participation']}"
        }},
        
        "projections": {{
            "2025": {{
                "intra_african_trade_target_mds_usd": {enhanced_stats['projections_updated']['2025']['intra_african_trade_target']},
                "tariff_elimination_target": "{enhanced_stats['projections_updated']['2025']['tariff_elimination_target']}",
                "gdp_impact": "{enhanced_stats['projections_updated']['2025']['gdp_impact']}",
                "employment_creation": "{enhanced_stats['projections_updated']['2025']['employment_creation']}"
            }},
            "2030": {{
                "intra_african_trade_target_mds_usd": {enhanced_stats['projections_updated']['2030']['intra_african_trade_target']},
                "tariff_elimination_target": "{enhanced_stats['projections_updated']['2030']['tariff_elimination_target']}",
                "gdp_impact": "{enhanced_stats['projections_updated']['2030']['gdp_impact']}",
                "employment_creation": "{enhanced_stats['projections_updated']['2030']['employment_creation']}",
                "industrialization_boost": "{enhanced_stats['projections_updated']['2030']['industrialization_boost']}"
            }}
        }},
        
        "data_sources": {json.dumps(enhanced_stats['data_sources'], ensure_ascii=False)},
        "last_updated": "{enhanced_stats['last_updated']}"
    }}'''
    
    # Remplacer l'ancienne fonction de statistiques
    stats_pattern = r'@api_router\.get\("/statistics"\).*?return \{.*?\}\s*\}\s*\}\s*\}'
    server_content = re.sub(stats_pattern, new_stats_function, server_content, flags=re.DOTALL)
    
    # Écrire le fichier modifié
    with open('/app/backend/server.py', 'w', encoding='utf-8') as f:
        f.write(server_content)
    
    print(f"   ✅ Fonction statistiques remplacée")
    print(f"   ✅ Données 2023-2024 intégrées")
    print(f"   ✅ Top exportateurs/importateurs ajoutés")
    print(f"   ✅ Analyse par groupes de produits ajoutée")
    print(f"   ✅ Performance des corridors régionaux ajoutée")

def main():
    """Application principale des corrections"""
    print("🚀 DÉMARRAGE APPLICATION DES CORRECTIONS ZLECAf")
    print("=" * 70)
    
    try:
        # Appliquer les corrections tarifaires
        apply_tariff_corrections()
        
        # Appliquer les corrections statistiques
        apply_statistics_corrections()
        
        print(f"\n🎉 TOUTES LES CORRECTIONS APPLIQUÉES AVEC SUCCÈS")
        print("=" * 70)
        print("RÉSUMÉ DES MODIFICATIONS:")
        print("   1. ✅ Taux tarifaires corrigés avec données officielles ZLECAf")
        print("   2. ✅ Statistiques enrichies avec données OEC 2023-2024")
        print("   3. ✅ Top 5 partenaires commerciaux ajoutés")
        print("   4. ✅ Analyse des groupes de produits HS2")
        print("   5. ✅ Performance des corridors régionaux")
        print("   6. ✅ Projections 2025-2030 mises à jour")
        print("")
        print("PROCHAINES ÉTAPES:")
        print("   • Redémarrer le service backend")
        print("   • Tester les nouveaux calculs tarifaires")
        print("   • Vérifier les nouvelles statistiques")
        
    except Exception as e:
        print(f"❌ Erreur lors de l'application des corrections: {e}")
        raise

if __name__ == "__main__":
    main()