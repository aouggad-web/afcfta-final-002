# Lyra+ Ops — Cron hebdo & API Health

Ce patch ajoute :
- un **workflow GitHub Actions** planifié (`lyra_plus_ops.yml`) qui régénère les jeux de données et commit automatiquement les changements dans `frontend/public/data/` ;
- une **route API** `/api/health` qui expose l'état des fichiers attendus (HTTP 200 si ok, 503 sinon).

## 1) Planification

Le cron est défini pour **tous les lundis à 06:15 UTC**. Vous pouvez ajuster la ligne :

```yaml
cron: "15 6 * * 1"
```

Format cron : `minute hour day-of-month month day-of-week`

## 2) Droits GitHub

Le workflow requiert `permissions.contents: write` pour pousser les commits. Par défaut, `secrets.GITHUB_TOKEN` suffit dans ce repo.

## 3) Passage du mode démo au mode prod

Remplacez dans l'étape du workflow :

```bash
python backend/make_release.py --demo
```

par votre pipeline réel (intégration e‑Tariff / UNCTAD / OEC):

```bash
python backend/make_release.py
```

Le script `backend/make_release.py` doit être mis à jour pour implémenter le mode production avec les sources de données officielles.

## 4) API Health

- **Endpoint**: `/api/health`
- **Réponse**: `{ ok: boolean, files: { [filename]: boolean }, message: string, timestamp: string }`
- Utilisable par Netlify / UptimeRobot pour un ping de supervision

Fichiers surveillés :
- `zlecaf_tariff_lines_by_country.json`
- `zlecaf_africa_vs_world_tariffs.xlsx`
- `zlecaf_rules_of_origin.json`
- `zlecaf_dismantling_schedule.csv`
- `zlecaf_tariff_origin_phase.json`

## 5) Tests

### Générer les données localement

```bash
python backend/make_release.py --demo
```

### Vérifier les fichiers générés

```bash
ls -lh frontend/public/data/
```

### Tester l'API Health

Démarrer le backend :

```bash
cd backend
uvicorn server:app --reload --port 8000
```

Puis tester :

```bash
curl http://localhost:8000/api/health
```

Réponse attendue quand les fichiers sont présents :

```json
{
  "ok": true,
  "files": {
    "zlecaf_tariff_lines_by_country.json": true,
    "zlecaf_africa_vs_world_tariffs.xlsx": true,
    "zlecaf_rules_of_origin.json": true,
    "zlecaf_dismantling_schedule.csv": true,
    "zlecaf_tariff_origin_phase.json": true
  },
  "message": "All data files present",
  "timestamp": "2024-01-15T10:00:00"
}
```

### Tester le workflow GitHub Actions

1. **Manuellement** : Aller sur l'onglet "Actions" du dépôt GitHub et déclencher le workflow `lyra-plus-ops` via "Run workflow"
2. **Automatiquement** : Le workflow s'exécutera tous les lundis à 06:15 UTC selon le cron configuré

## 6) Structure des fichiers de données

### zlecaf_tariff_lines_by_country.json
Contient le nombre de lignes tarifaires par pays et par catégorie (A, B, C).

### zlecaf_rules_of_origin.json
Règles d'origine ZLECAf par chapitre HS (code à 2 chiffres).

### zlecaf_dismantling_schedule.csv
Calendrier de démantèlement tarifaire par pays, secteur et catégorie.

### zlecaf_tariff_origin_phase.json
Données intégrées combinant tarifs, règles d'origine et calendrier de démantèlement.

### zlecaf_africa_vs_world_tariffs.xlsx
Comparaison des tarifs ZLECAf vs tarifs mondiaux (nécessite openpyxl).

## 7) Maintenance

- **Mise à jour des données** : Le workflow automatique s'en charge chaque semaine
- **Logs** : Consultables dans l'onglet "Actions" de GitHub
- **Erreurs** : Si le workflow échoue, vérifier les logs et les permissions GitHub
- **Mode production** : Implémenter l'intégration avec les sources officielles dans `backend/make_release.py`

## 8) Sources de données (mode production)

À implémenter :
- **e-Tariff Portal** : Schedules tarifaires officiels ZLECAf
- **UNCTAD TRAINS** : Données commerciales et tarifaires
- **OEC Atlas** : Complexité économique et flux commerciaux
- **Banque Mondiale** : Indicateurs économiques

— Lyra+
