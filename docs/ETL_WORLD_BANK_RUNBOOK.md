# Runbook ETL — World Bank (PIB/habitant + réserves de change)

Ce runbook explique comment produire les deux jeux de données World Bank qui
enrichissent le module Opportunités. **Ils sont optionnels** : en leur absence,
le module dégrade gracieusement (indicateurs marqués `available: false`,
estimation des besoins nationaux plafonnée au niveau 2). Aucune valeur n'est
inventée.

> ⚠️ L'API World Bank est **bloquée par la politique réseau** dans certains bacs
> à sable (CI/dev), exactement comme l'OEC. Exécuter ces ETL sur un environnement
> disposant d'un accès réseau sortant (déploiement, machine locale). L'API World
> Bank **ne nécessite aucune clé**.

---

## 1. PIB par habitant → `data/json/wb_gdp_pc.json`

**Indicateur** : `NY.GDP.PCAP.CD` (GDP per capita, current US$).
**Consommé par** : `services/demand_estimation_service.py` (ajustement niveau de
vie, **niveau L3** de l'estimation des besoins nationaux).

```bash
cd backend
python -m etl.fetch_wb_gdp
# → écrit ../data/json/wb_gdp_pc.json  (format plat {ISO3: {value, year}})
```

**Effet une fois présent** : l'estimation des besoins nationaux passe
automatiquement de L2 (proxy population) à **L3** :

```
besoin_L3 = besoin_L2 × (PIB/hab_pays ÷ PIB/hab_moyen)^ε
```

(ε = élasticité-revenu, par défaut 0,4, exposée dans le payload). Aucun autre
changement de code n'est requis : le service détecte le fichier et l'utilise.

---

## 2. Réserves de change + couverture des importations → `data/json/wb_reserves.json`

**Indicateurs** :
- `FI.RES.TOTL.CD` — réserves totales (or inclus), US$ courant → réserves de change.
- `FI.RES.TOTL.MO` — réserves totales en mois d'importations → couverture.

**Consommé par** : `services/macro_indicators_service.py`
(`get_fx_reserves`, `get_import_cover`) → volet macro du rapport bilatéral +
composante « capacité à payer » de la faisabilité de financement.

```bash
cd backend
python -m etl.fetch_wb_reserves
# → écrit ../data/json/wb_reserves.json  (structure {countries: {ISO3: {...}}})
```

**Effet une fois présent** : les cartes « Réserves de change » et « Couverture
des importations » du rapport passent de « À produire via ETL BM » aux valeurs
réelles datées ; la couverture des importations (≥ 3 mois = sain) alimente
l'indice de faisabilité de financement.

---

## Vérification post-exécution

```bash
# PIB/hab bien ingéré et L3 actif :
curl -s "$API/reports/national-need?hs_code=180100&country=NGA" | jq '.estimation_level, .inputs.gdp_adjustment_factor'
# attendu : 3  et un facteur non-null

# Réserves ingérées :
curl -s "$API/reports/macro/NGA" | jq '.fx_reserves.available, .import_cover.available'
# attendu : true  true
```

## Fréquence recommandée

Ces indicateurs sont **annuels**. Un rafraîchissement **trimestriel** suffit
(les révisions World Bank sont peu fréquentes). Les fichiers produits sont
committables dans `data/json/` pour un déploiement reproductible, ou régénérés
par un cron sur l'environnement réseau.

## Discipline

- Les ETL **n'inventent jamais** : un pays/indicateur sans observation est
  simplement **omis** du fichier de sortie (la dernière observation non nulle
  est retenue, avec son année).
- Tant qu'un fichier est absent, le code aval renvoie `available: false` avec une
  note — il ne comble jamais le trou par une estimation déguisée en mesure.
