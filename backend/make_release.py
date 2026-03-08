#!/usr/bin/env python3
"""
Lyra+ Data Release Pipeline
Génère les jeux de données ZLECAf pour le frontend
"""

import json
import csv
import os
import sys
import argparse
from pathlib import Path

# Fichiers attendus dans frontend/public/data/
EXPECTED_FILES = [
    'zlecaf_tariff_lines_by_country.json',
    'zlecaf_africa_vs_world_tariffs.xlsx',
    'zlecaf_rules_of_origin.json',
    'zlecaf_dismantling_schedule.csv',
    'zlecaf_tariff_origin_phase.json',
]


def generate_demo_data(output_dir: Path):
    """
    Génère des données de démonstration pour les tests
    En production, remplacer par l'intégration e-Tariff/UNCTAD/OEC réelle
    """
    print("🔄 Génération des données de démonstration...")
    
    # 1. zlecaf_tariff_lines_by_country.json
    tariff_lines = {
        "metadata": {
            "version": "1.0",
            "generated_at": "2024-01-15T10:00:00Z",
            "source": "Demo Mode - ZLECAf Schedules"
        },
        "countries": {
            "MA": {
                "name": "Maroc",
                "total_lines": 6127,
                "categories": {
                    "A": 4500,
                    "B": 1200,
                    "C": 427
                }
            },
            "ZA": {
                "name": "Afrique du Sud",
                "total_lines": 7852,
                "categories": {
                    "A": 6000,
                    "B": 1500,
                    "C": 352
                }
            },
            "CM": {
                "name": "Cameroun",
                "total_lines": 5800,
                "categories": {
                    "A": 3800,
                    "B": 1400,
                    "C": 600
                }
            },
            "CF": {
                "name": "République Centrafricaine",
                "total_lines": 4200,
                "categories": {
                    "A": 2800,
                    "B": 1000,
                    "C": 400
                }
            },
            "TD": {
                "name": "Tchad",
                "total_lines": 4500,
                "categories": {
                    "A": 3000,
                    "B": 1100,
                    "C": 400
                }
            },
            "CG": {
                "name": "République du Congo",
                "total_lines": 4800,
                "categories": {
                    "A": 3200,
                    "B": 1200,
                    "C": 400
                }
            },
            "GQ": {
                "name": "Guinée Équatoriale",
                "total_lines": 3500,
                "categories": {
                    "A": 2300,
                    "B": 850,
                    "C": 350
                }
            },
            "GA": {
                "name": "Gabon",
                "total_lines": 5200,
                "categories": {
                    "A": 3500,
                    "B": 1200,
                    "C": 500
                }
            }
        }
    }
    
    with open(output_dir / 'zlecaf_tariff_lines_by_country.json', 'w', encoding='utf-8') as f:
        json.dump(tariff_lines, f, indent=2, ensure_ascii=False)
    print(f"   ✅ zlecaf_tariff_lines_by_country.json créé")
    
    # 2. zlecaf_rules_of_origin.json
    rules_of_origin = {
        "metadata": {
            "version": "1.0",
            "source": "ZLECAf Annex 2"
        },
        "rules": {
            "01": {
                "chapter": "01",
                "description": "Animaux vivants",
                "rule": "Entièrement obtenus",
                "regional_content": 100
            },
            "84": {
                "chapter": "84",
                "description": "Machines et appareils mécaniques",
                "rule": "Changement de classification tarifaire ou 40% de contenu régional",
                "regional_content": 40
            }
        }
    }
    
    with open(output_dir / 'zlecaf_rules_of_origin.json', 'w', encoding='utf-8') as f:
        json.dump(rules_of_origin, f, indent=2, ensure_ascii=False)
    print(f"   ✅ zlecaf_rules_of_origin.json créé")
    
    # 3. zlecaf_dismantling_schedule.csv
    dismantling_data = [
        ["Country", "HS2", "Category", "Year_0", "Year_5", "Year_10", "Year_13"],
        ["MA", "84", "A", "10.0", "5.0", "2.0", "0.0"],
        ["MA", "85", "B", "15.0", "10.0", "5.0", "0.0"],
        ["ZA", "84", "A", "8.0", "4.0", "1.0", "0.0"],
        ["ZA", "61", "C", "20.0", "15.0", "10.0", "5.0"],
        # CEMAC countries (CEMAC CET: 5/10/20/30%)
        ["CM", "27", "A", "5.0", "2.5", "0.0", "0.0"],
        ["CM", "44", "B", "10.0", "7.0", "3.0", "0.0"],
        ["CM", "84", "A", "10.0", "5.0", "2.0", "0.0"],
        ["CF", "27", "A", "5.0", "2.5", "0.0", "0.0"],
        ["TD", "27", "A", "5.0", "2.5", "0.0", "0.0"],
        ["CG", "27", "A", "5.0", "2.5", "0.0", "0.0"],
        ["GQ", "27", "A", "5.0", "2.5", "0.0", "0.0"],
        ["GA", "44", "B", "10.0", "7.0", "3.0", "0.0"],
        ["GA", "26", "A", "5.0", "2.5", "0.0", "0.0"],
    ]
    
    with open(output_dir / 'zlecaf_dismantling_schedule.csv', 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerows(dismantling_data)
    print(f"   ✅ zlecaf_dismantling_schedule.csv créé")
    
    # 4. zlecaf_tariff_origin_phase.json
    tariff_origin_phase = {
        "metadata": {
            "description": "Integrated tariff, origin rules, and phase-out schedule"
        },
        "data": {
            "MA": {
                "84": {
                    "category": "A",
                    "rule": "40% regional content",
                    "phases": {
                        "2024": 5.0,
                        "2029": 2.0,
                        "2034": 0.0
                    }
                }
            }
        }
    }
    
    with open(output_dir / 'zlecaf_tariff_origin_phase.json', 'w', encoding='utf-8') as f:
        json.dump(tariff_origin_phase, f, indent=2, ensure_ascii=False)
    print(f"   ✅ zlecaf_tariff_origin_phase.json créé")
    
    # 5. zlecaf_africa_vs_world_tariffs.xlsx (créer un placeholder CSV car openpyxl est optionnel)
    # En production, utiliser openpyxl pour créer un vrai fichier Excel
    print(f"   ⚠️  zlecaf_africa_vs_world_tariffs.xlsx nécessite openpyxl (mode CSV)")
    with open(output_dir / 'zlecaf_africa_vs_world_tariffs.csv', 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerows([
            ["Country", "Sector", "AfCFTA_Tariff", "World_Tariff", "Savings_Percent"],
            ["MA", "84", "5.0", "15.0", "66.7"],
            ["ZA", "85", "3.0", "12.0", "75.0"],
        ])


def main():
    parser = argparse.ArgumentParser(description='Lyra+ Data Release Pipeline')
    parser.add_argument('--demo', action='store_true', 
                        help='Mode démonstration avec données simulées')
    parser.add_argument('--output', type=str, 
                        default='frontend/public/data',
                        help='Répertoire de sortie (défaut: frontend/public/data)')
    
    args = parser.parse_args()
    
    # Déterminer le chemin de sortie
    script_dir = Path(__file__).parent.parent
    output_dir = script_dir / args.output
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("=" * 60)
    print("🚀 LYRA+ DATA RELEASE PIPELINE")
    print("=" * 60)
    print(f"Mode: {'DEMO' if args.demo else 'PRODUCTION'}")
    print(f"Sortie: {output_dir}")
    print()
    
    if args.demo:
        generate_demo_data(output_dir)
    else:
        print("❌ Mode production non implémenté")
        print("TODO: Intégrer les sources réelles:")
        print("  - e-Tariff Portal (tariff schedules)")
        print("  - UNCTAD TRAINS (trade data)")
        print("  - OEC Observatory (economic complexity)")
        sys.exit(1)
    
    print()
    print("=" * 60)
    print("✅ PIPELINE COMPLÉTÉ")
    print("=" * 60)
    
    # Vérifier les fichiers générés
    print("\n📋 Fichiers générés:")
    for filename in os.listdir(output_dir):
        if filename != '.gitkeep':
            filepath = output_dir / filename
            size = filepath.stat().st_size
            print(f"   ✓ {filename} ({size} bytes)")


if __name__ == "__main__":
    main()
