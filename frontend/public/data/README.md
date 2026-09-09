# ZLECAf Data Directory

Ce répertoire contient les jeux de données ZLECAf générés automatiquement par le workflow Lyra+ Ops.

## Fichiers

- `zlecaf_tariff_lines_by_country.json` - Lignes tarifaires par pays
- `zlecaf_africa_vs_world_tariffs.xlsx` - Comparaison tarifs ZLECAf vs monde
- `zlecaf_rules_of_origin.json` - Règles d'origine par secteur
- `zlecaf_dismantling_schedule.csv` - Calendrier de démantèlement tarifaire
- `zlecaf_tariff_origin_phase.json` - Données intégrées (tarifs + origine + phases)

## Génération

Ces fichiers sont automatiquement générés et mis à jour :
- **Automatiquement** : Chaque lundi à 06:15 UTC via GitHub Actions
- **Manuellement** : `python backend/make_release.py --demo`

## Mode Production

En mode production, ces fichiers seront générés à partir des sources officielles :
- e-Tariff Portal (schedules tarifaires)
- UNCTAD TRAINS (données commerciales)
- OEC Atlas (complexité économique)

Voir `docs/LYRA_OPS.md` pour plus de détails.
