# Crawlers locaux — Phase 1

Ces scripts s'exécutent sur **votre machine locale** (pas sur Replit) car les portails
douaniers africains bloquent les serveurs cloud US.

## Prérequis

```bash
pip install requests beautifulsoup4
```

## Scripts disponibles

| Script | Pays | Source |
|--------|------|--------|
| `crawl_zaf_sars.py` | ZAF + NAM/BWA/LSO (SACU) | tariff.sars.gov.za |
| `crawl_mar_adil.py` | MAR | adil.douane.gov.ma |
| `crawl_egy_egyptariffs.py` | EGY | egyptariffs.com |
| `crawl_eth_erca.py` | ETH | customs.erca.gov.et |
| `crawl_mus_mra.py` | MUS | mra.mu |

## Utilisation

```bash
# Un pays complet
python crawl_zaf_sars.py --out zaf_raw.json

# Tester sur 3 chapitres d'abord
python crawl_zaf_sars.py --chapters 01 02 03 --out zaf_test.json

# Ralentir si le site limite les requêtes
python crawl_mar_adil.py --delay 3.0 --out mar_raw.json
```

## Sortie attendue

Chaque script génère un fichier `xxx_raw.json` avec cette structure :

```json
{
  "country_code": "ZAF",
  "country_name": "South Africa",
  "source": "SARS",
  "source_url": "https://tariff.sars.gov.za",
  "crawled_at": "2026-06-12T...",
  "data_type": "raw_crawl",
  "notes": ["..."],
  "positions": [
    {
      "code": "01012100",
      "description_en": "Pure-bred breeding animals",
      "dd_rate": 0.0,
      "vat_rate": 15.0,
      "chapter": "01",
      "digits": 8
    }
  ],
  "total": 6500
}
```

## Étape suivante

1. Exécuter les scripts sur votre machine
2. Uploader les fichiers `*_raw.json` sur Replit dans `backend/data/raw_crawls/`
3. Sur Replit : le script `ingest_raw_crawl.py` convertit automatiquement en format `national_positions`

## Notes sur les accès

- **SARS (ZAF)** : peut nécessiter un navigateur humain — si bloqué, télécharger
  le PDF Schedule 1 Part 1 depuis le site SARS et uploader le PDF directement
- **ADIL (MAR)** : utilise des sessions — si bloqué après 10 chapitres, relancer
  avec `--chapters 11 12 ...`
- **ERCA (ETH)** : le site redirige, le script suit automatiquement
- **egyptariffs.com** : détection automatique de l'URL de recherche active
