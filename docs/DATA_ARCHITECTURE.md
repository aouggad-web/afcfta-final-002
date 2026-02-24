# Data Architecture and File Management

## Single Source of Truth

This document defines the canonical data files and how they should be accessed across different environments.

### Primary Data Files

The following files are the **single source of truth** for their respective data domains:

#### 1. **ports_africains.json** (288KB, 68 ports)
- **Location**: `/` (repository root)
- **Purpose**: Complete African ports database with enriched data
- **Key Fields**: 
  - Port identification (port_id, port_name, un_locode, country_iso)
  - Geolocation (geo_lat, geo_lon)
  - Performance metrics (avg_waiting_time_hours, berth_productivity, efficiency_grade)
  - Traffic evolution (historical TEU data)
  - TRS analysis (Time Release Study - customs clearance times)
  - Global benchmarks and LPI data
  - Port authority contact information
  - Shipping agents and services

**DO NOT CREATE**: ❌ `ports_africains_backup.json`, `ports_africains_old.json`, `ports_africains_enriched.json`, `ports_africains_enriched_pro.json`

#### 2. **airports_africains.json** (130KB, 64 airports)
- **Location**: `/` (repository root)
- **Purpose**: Complete African airports database
- **Key Fields**: Airport codes (IATA, ICAO), location, capacity, services

**DO NOT CREATE**: ❌ `airports_africains_original.json`

#### 3. **ZLECAf_ENRICHI_2024_COMMERCE.csv** (32KB)
- **Location**: `/` (repository root)
- **Purpose**: African Continental Free Trade Area commercial data for 2024

**DO NOT CREATE**: ❌ `.backup` files

### Other Reference Data Files

- `douanes_africaines.json` - African customs data
- `zones_franches_afrique.json` - African free zones
- `projets_structurants_afrique.json` - Major infrastructure projects
- `production_africaine.json` - African production data
- `worldbank_data_latest.json` - Latest World Bank indicators
- `corridors_terrestres.json` - Land transport corridors
- `classement_infrastructure_afrique.json` - Infrastructure rankings

## Path Resolution Pattern

To support both Docker (`/app/`) and local development environments, all scripts must use the following pattern:

```python
import os
from pathlib import Path

# Support both Docker (/app/) and local environments
ROOT_DIR = Path(os.environ.get('APP_ROOT', Path(__file__).parent))

# For root-level scripts
FILE_PATH = ROOT_DIR / 'ports_africains.json'

# For backend/ scripts (adjust parent level accordingly)
ROOT_DIR = Path(os.environ.get('APP_ROOT', Path(__file__).parent.parent))
FILE_PATH = ROOT_DIR / 'ports_africains.json'
```

### Environment Variables

- **Local Development**: Paths resolve relative to script location
- **Docker**: Set `APP_ROOT=/app` environment variable to use absolute Docker paths

## Updated Scripts

The following scripts have been updated to use the standardized path resolution:

### Root-Level Scripts
- `check_tanger.py` - Check Tanger Med port data
- `fix_tangermed_data.py` - Update Tanger Med with precise data
- `add_trs_data.py` - Add Time Release Study data to ports
- `update_all_ports_precise.py` - Update all ports with master data

### Backend Scripts
- `backend/enrich_ports_professional.py` - Enrich ports with performance metrics
- `backend/etl_unctad_maritime.py` - ETL for UNCTAD maritime data
- `backend/logistics_data.py` - Already using ROOT_DIR pattern ✅
- `backend/logistics_air_data.py` - Already using ROOT_DIR pattern ✅
- `backend/etl/ports_etl.py` - Already using ROOT_DIR pattern ✅

## Data Enrichment Pipeline

The enrichment process should follow this order to avoid conflicts:

1. **Base Data**: Start with `ports_africains.json` (primary source)
2. **ETL Enrichment**: Run `backend/etl_unctad_maritime.py` to add UNCTAD data
3. **Performance Metrics**: Run `backend/enrich_ports_professional.py` to add calculated metrics
4. **TRS Data**: Run `add_trs_data.py` to add customs clearance time analysis
5. **Port-Specific Fixes**: Run `fix_tangermed_data.py` or similar for specific corrections

**Important**: All enrichment scripts should:
- Read from the primary data file
- Write back to the same file (not create new versions)
- Use atomic writes (write to temp file, then rename) to prevent corruption

## Conflict Resolution Guidelines

### Preventing Future Conflicts

1. ✅ **DO**: Use the standardized ROOT_DIR path pattern
2. ✅ **DO**: Update the primary data file in place
3. ✅ **DO**: Use descriptive git commit messages when updating data files
4. ❌ **DON'T**: Create `.backup` or `_old` versions manually
5. ❌ **DON'T**: Use hardcoded `/app/` paths
6. ❌ **DON'T**: Create intermediate output files unless temporary
7. ✅ **DO**: Use git for version control and rollback if needed

### If Data Conflicts Occur

1. Check which file is largest and most complete (usually the primary)
2. Compare record counts and field completeness
3. Keep the most comprehensive version
4. Delete redundant copies
5. Update any scripts referencing the old files

## Testing Path Resolution

To verify scripts work in both environments:

```bash
# Test local (default)
python check_tanger.py

# Test with Docker path
APP_ROOT=/app python check_tanger.py

# Test backend script
cd backend && python enrich_ports_professional.py
```

## Questions or Issues?

If you encounter path or data conflicts:
1. Check this document first
2. Verify you're using the ROOT_DIR pattern
3. Check if you're creating duplicate files inadvertently
4. Use `git status` to see what files have changed
