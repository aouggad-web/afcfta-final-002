#!/usr/bin/env python3
"""Script de migration complète vers PostgreSQL"""

import os
import sys
import logging
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, '/app/engine')

from database.migration import MigrationService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/app/engine/migration.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def main():
    database_url = "postgresql://afcfta:afcfta2026@localhost:5432/afcfta_regulatory"
    
    logger.info("=" * 60)
    logger.info("MIGRATION COMPLÈTE VERS POSTGRESQL")
    logger.info(f"Démarrage: {datetime.now().isoformat()}")
    logger.info("=" * 60)
    
    try:
        service = MigrationService(database_url=database_url)
        
        # Initialize database (tables already exist but just in case)
        service.init_database()
        
        # Migrate all countries
        stats = service.migrate_all(batch_size=1000)
        
        logger.info("=" * 60)
        logger.info("MIGRATION TERMINÉE AVEC SUCCÈS")
        logger.info(f"Statistiques: {stats}")
        logger.info(f"Fin: {datetime.now().isoformat()}")
        logger.info("=" * 60)
        
        return 0
        
    except Exception as e:
        logger.error(f"ERREUR FATALE: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
