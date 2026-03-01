"""
Pipeline de génération des données canoniques
=============================================

Génère les fichiers JSONL canoniques et les index de recherche
pour le Moteur Réglementaire AfCFTA v3.
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

# Ajouter le répertoire engine au path
sys.path.insert(0, str(Path(__file__).parent))

from adapters.dza_adapter import DZAAdapter
from schemas.canonical_model import CanonicalTariffLine


class RegulatoryPipeline:
    """Pipeline de génération des données canoniques"""
    
    def __init__(self, output_dir: str = "/app/engine/output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Registre des adaptateurs par pays
        self.adapters = {
            "DZA": DZAAdapter,
            # Ajouter d'autres adaptateurs ici
        }
        
        self.stats = {}
    
    def run(self, countries: List[str] = None) -> Dict[str, Any]:
        """
        Exécute le pipeline pour les pays spécifiés.
        Si countries est None, traite tous les pays disponibles.
        """
        if countries is None:
            countries = list(self.adapters.keys())
        
        results = {
            "started_at": datetime.now().isoformat(),
            "countries_processed": [],
            "countries_failed": [],
            "total_records": 0
        }
        
        for iso3 in countries:
            if iso3 not in self.adapters:
                print(f"[WARNING] Pas d'adaptateur pour {iso3}")
                results["countries_failed"].append({
                    "country": iso3,
                    "error": "No adapter available"
                })
                continue
            
            try:
                count = self._process_country(iso3)
                results["countries_processed"].append({
                    "country": iso3,
                    "records": count
                })
                results["total_records"] += count
                print(f"[OK] {iso3}: {count} enregistrements")
            except Exception as e:
                print(f"[ERROR] {iso3}: {str(e)}")
                results["countries_failed"].append({
                    "country": iso3,
                    "error": str(e)
                })
        
        # Générer les index
        self._build_indexes()
        
        results["completed_at"] = datetime.now().isoformat()
        
        # Sauvegarder le rapport
        report_path = self.output_dir / "pipeline_report.json"
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        return results
    
    def _process_country(self, iso3: str) -> int:
        """Traite un pays et génère le fichier JSONL"""
        adapter_class = self.adapters[iso3]
        adapter = adapter_class()
        
        output_file = self.output_dir / f"{iso3}_canonical.jsonl"
        count = 0
        
        # Index par code national
        national_index = {}
        # Index par HS6
        hs6_index = {}
        
        with open(output_file, 'w', encoding='utf-8') as f:
            for line_num, record in enumerate(adapter.transform()):
                # Sérialiser en JSONL
                json_line = record.model_dump_json()
                f.write(json_line + '\n')
                
                # Construire les index
                nat_code = record.commodity.national_code
                hs6 = record.commodity.hs6
                
                national_index[nat_code] = {
                    "line": line_num,
                    "hs6": hs6,
                    "chapter": record.commodity.chapter
                }
                
                if hs6 not in hs6_index:
                    hs6_index[hs6] = []
                hs6_index[hs6].append({
                    "national_code": nat_code,
                    "line": line_num
                })
                
                count += 1
        
        # Sauvegarder les index
        self._save_index(f"{iso3}_index_national.json", national_index)
        self._save_index(f"{iso3}_index_hs6.json", hs6_index)
        
        # Sauvegarder le résumé
        summary = adapter.get_summary()
        summary["output_file"] = str(output_file)
        summary["record_count"] = count
        summary["generated_at"] = datetime.now().isoformat()
        
        summary_path = self.output_dir / f"{iso3}_summary.json"
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        self.stats[iso3] = summary
        
        return count
    
    def _save_index(self, filename: str, data: Dict):
        """Sauvegarde un fichier d'index"""
        index_dir = self.output_dir / "indexes"
        index_dir.mkdir(exist_ok=True)
        
        path = index_dir / filename
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False)
    
    def _build_indexes(self):
        """Construit les index globaux"""
        # Index des pays disponibles
        countries_index = {
            "available_countries": list(self.stats.keys()),
            "total_records": sum(s.get("record_count", 0) for s in self.stats.values()),
            "generated_at": datetime.now().isoformat()
        }
        
        self._save_index("countries_index.json", countries_index)


def main():
    """Point d'entrée du pipeline"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Pipeline Moteur Réglementaire AfCFTA v3")
    parser.add_argument(
        "--countries",
        nargs="+",
        help="Codes ISO3 des pays à traiter (ex: DZA MAR)",
        default=None
    )
    parser.add_argument(
        "--output",
        help="Répertoire de sortie",
        default="/app/engine/output"
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("  Moteur Réglementaire AfCFTA v3 - Pipeline")
    print("=" * 60)
    
    pipeline = RegulatoryPipeline(output_dir=args.output)
    results = pipeline.run(countries=args.countries)
    
    print("\n" + "=" * 60)
    print("  Résumé")
    print("=" * 60)
    print(f"Pays traités: {len(results['countries_processed'])}")
    print(f"Total enregistrements: {results['total_records']}")
    if results['countries_failed']:
        print(f"Échecs: {len(results['countries_failed'])}")
    print(f"Rapport: {args.output}/pipeline_report.json")


if __name__ == "__main__":
    main()
