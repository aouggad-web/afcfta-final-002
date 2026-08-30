# Mission — Collecte et implémentation des tarifs africains authentiques

> Charte de la branche `feat/tarifs-africains-authentiques`.
> Objectif stratégique : **collecter et implémenter les tarifs africains**, les
> documenter et les sourcer avec exactitude, efficacité et authenticité.
> **Pas de mock, pas d'hallucination, pas d'analyse spéculative — rien que les
> vrais, en application** — incluant les avantages ZLECAf et les outils de son
> exécution.

## 1. Distinction stricte ZALE ≠ ZLECAf

| | **ZALE** (Zone de Libre-Échange **Arabe**) | **ZLECAf** (Zone de Libre-Échange **Continentale Africaine**) |
|---|---|---|
| Sigles | GAFTA, ZALE | AfCFTA, ZLECAf |
| Périmètre | 17+ États arabes (Ligue arabe) | 54 États africains (acc. de Kigali 2018, opérationnel 01/01/2021) |
| État pour la Tunisie | Libre-échange **effectif** (démantèlement achevé) | Démantèlement **en cours** — listes de concessions différenciées |
| Taux observés (crawl 2026-08-30) | **0 %** quasi-systématique (Égypte, Jordanie, Koweït, Palestine, Maroc, Algérie) | **40 %** (trajectoire générale), **87,5 %** (produits sensibles ~1 251 codes), **0 %** (concessions avancées, ex. Tanzanie), **80 %** (Maurice/Rwanda, couverture partielle) |

**Règles de données (non négociables)** :
1. Chaque taux préférentiel porte son attribution de zone — jamais de
   regroupement « arabe ou africain » indifférencié.
2. Un 0 % ZALE ≠ un 0 % ZLECAf : base juridique (GAFTA vs protocole ZLECAf +
   Annexe 2 règles d'origine), périmètre produits et cumul d'origine diffèrent.
3. Les taux ZLECAf > 0 % reflètent les listes de concessions tunisiennes en
   phase transitoire — ne jamais les présenter comme du libre-échange effectif.
4. Registre de référence : `backend/data/agreements/tun_preferential_zones.json`.

## 2. Principes de collecte (méthode DZA, appliqués à tous les pays)

- **Sources officielles uniquement** : douanes, ministères, journaux officiels,
  bulletins douaniers — jamais de données tierces non opposables.
- **Archivage SHA-256** de chaque document source (PDF, captures, registres)
  avec `source_url` + page de référence + date d'archivage.
- **Zéro fabrication** : une donnée manquante est marquée indisponible
  (`VERIFIED_PARTIAL`, `no_result`) — jamais extrapolée.
- **Traçabilité taux ↔ texte** : chaque taux rattaché à son acte (n° JORT,
  date, article) via les corpus JORT et BOD.
- **Réconciliation systématique** entre versions de source (documentée, sans
  arbitrage silencieux).

## 3. Sources cartographiées et vérifiées (2026-08-30)

| Source | Périmètre | État |
|---|---|---|
| `douane.gov.tn/tarifwebnew` (Tarif Web 2026) | TUN : 17 542 codes, taux + préférences par pays + assiettes | ✅ crawl complet, 0 échec |
| `douane.gov.tn/bulletin-officiel-des-douanes/` (BOD/DGD) | Circulaires, notes communes, décisions DGD 2016→2026 | ✅ identifiée, à archiver |
| `iort.gov.tn` (JORT, Imprimerie Officielle) | 6 554 journaux / 207 072 textes depuis 1956 ; recherche multicritères | ✅ crawler opérationnel, 15 LFs extraites |
| `commerce.gov.tn` (Min. Commerce) | Avis d'ouverture de contingents tarifaires (PDF mensuels) | ✅ identifiée |
| `finances.gov.tn` (Min. Finances) | Lois de finances, cadre réglementaire | ✅ identifiée |
| `douane.gov.tn/taxationveh` + `/taxationdesc` | Méthodes officielles de taxation véhicules | ✅ identifiées |

## 4. Livrables de la session 2026-08-30

- **Re-crawl TUN complet** : `backend/data/crawled/TUN_rates_2026-08-30.json`
  (17 542 codes, taxes import/export avec assiettes, préférences par pays, QCS/GU).
- **Réconciliation juin 2025 ↔ août 2026** :
  `reports/TUN_RECONCILIATION_2026-08-30.json` — 16 782 taux identiques,
  **492 changements réels** (TVA 19→7 % sur 90 codes, DC sucres/chocolats,
  carburants, montures 43→10 %…), 620 améliorations de capture, 83 codes
  restructurés. Zéro arbitrage : tout est documenté.
- **Corpus JORT** : lois de finances 2010→2026 (références JORT exactes,
  161 articles fiscaux localisés) + contingents + arrêtés taxes.
  PDFs archivés SHA-256 : `data/sources/TUN/jort/`.
- **Registre des zones préférentielles TUN** (ZALE/ZLECAf/UE/AELE/bilatéraux)
  avec statistiques observées par partenaire.
- **Crawlers réutilisables** : `scripts/tun_recrawl_rates.py`,
  `scripts/jort_crawler.py`, `scripts/jort_lf_pipeline.py`,
  `scripts/tun_reconcile.py`.

## 5. Outils d'exécution ZLECAf (existants et à consolider)

- Moteur tarifaire : `POST /api/calculate-tariff` — réciprocité ZLECAf, unions
  douanières, taux préférentiels par partenaire.
- Couche douanière généralisée : `engine/import_charges.py` +
  `engine/customs_territory_registry.py` (régionale + nationale, couvertures
  tracées) et service national (`services.national_legal_calculation_service`).
- Règles d'origine : 96 chapitres (`/api/rules-of-origin/*`).
- Opportunités : S1–S6 + bilatéral ultra-fin (`/api/reports/*`), alimenté par
  les tarifs réels, OEC, FAOSTAT/USGS/UNIDO, corridors logistiques.

## 6. Prochaines étapes

1. **Régénérer le canonique TUN** (`TUN_tariffs.json`) depuis le crawl 2026 +
   réconciliation (méthode DZA : consolidation + changelog).
2. Archiver le **BOD 2023→2026** (SHA-256) et rattacher les changements de
   taux aux bulletins (entre deux éditions du tarif).
3. Étendre la collecte aux **tarifs ZLECAf publiés par les partenaires**
   (offres tarifaires des pays cibles) — mêmes principes, même rigueur.
4. Rattacher **chaque préférence ZLECAf à son acte** (décrets/arrêtés
   tunisiens d'application des offres + JORT).
5. Exposer dans l'API la **zone d'accord** sur chaque taux préférentiel
   (filtre ZALE vs ZLECAf vs UE…) dans le calculateur et le module Opportunités.
