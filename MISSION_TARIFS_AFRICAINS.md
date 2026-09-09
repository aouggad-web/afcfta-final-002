# Mission — Collecte et implémentation des tarifs africains authentiques

> Charte de la branche `feat/tarifs-africains-authentiques`.
> Objectif stratégique : **collecter et implémenter les tarifs africains**, les
> documenter et les sourcer avec exactitude, efficacité et authenticité.
> **Pas de mock, pas d'hallucination, pas d'analyse spéculative — rien que les
> vrais, en application** — incluant les avantages ZLECAf et les outils de son
> exécution.
>
> **Périmètre SaaS : le commerce africain avec le monde** — pas seulement le
> commerce intra-africain. Quatre flux couverts :
> 1. **Intra-africain** (ZLECAf, CEMAC, CEDEAO, SADC, EAC, COMESA, AMU…)
> 2. **Afrique → monde** (accès préférentiels aux marchés tiers : EPA UE,
>    AGOA États-Unis, GSP, accords bilatéraux Turquie/UK/Chine…)
> 3. **Monde → Afrique** (taux NPF appliqués par les douanes africaines aux
>    importations tierces, accords signés par chaque pays)
> 4. **Chaînes de valeur transitant par l'Afrique** (régimes économiques,
>    admission temporaire, plateformes/logistiques)

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

## 2 bis. Règle NPF — référence obligatoire (par pays, par code)

1. **Le taux NPF (nation la plus favorisée / MFN) de chaque pays africain est
   la référence de base** de sa grille tarifaire : c'est le taux appliqué aux
   importations du reste du monde (membres OMC sans accord préférentiel).
2. **Toute préférence s'exprime par rapport au NPF** : marge de préférence =
   NPF − taux préférentiel. Sans NPF vérifié, la marge est **indisponible**
   (jamais estimée).
3. Le NPF provient de la **source tarifaire officielle nationale** du pays
   (portail douanier, tarif légal, JORT/gazette équivalent) — archivé SHA-256.
   Les bases tierces (WTO, ITC MacMap, UNCTAD TRAINS) ne servent que de
   **contre-vérification**, signalées comme sources secondaires.
4. Chaque partenaire préférentiel d'un pays est documenté avec **tous les
   accords applicables** : blocs régionaux (ZLECAf, ZALE pour les États
   arabes, CEMAC, CEDEAO, EAC, SADC, COMESA, AMU…), EPAs (UE/RU),
   AGOA, GSP, accords bilatéraux (Turquie, Chine, Inde…) — avec le
   **statut d'application réel** (en vigueur, signé non appliqué, en
   négociation — jamais présentés comme appliqués si ce n'est pas le cas).
5. **Avantages fiscaux** : les régimes incitatifs de chaque pays (exonérations
   à l'importation, régimes suspensifs, admission temporaire, entrepôts et
   zones franches, avantages à l'exportation, codes de réglementation) sont
   collectés **exclusivement depuis les textes officiels et portails
   douaniers/fiscaux** archivés — jamais depuis des brochures ou des
   synthèses non opposables.

## 2 ter. Périmètre SaaS — le commerce africain avec le monde

Le calculateur et le module Opportunités couvrent les quatre flux :
- **Import africain** : pour tout pays africain couvert, taux appliqué à une
  origine donnée (NPF si aucun accord, préférentiel sinon, avec zone et
  référence juridique).
- **Export africain** : taux d'entrée constatés sur les marchés tiers quand
  les sources officielles de ces marchés sont collectées (même méthode), sinon
  indisponible.
- **Préférences mondiales dont bénéficie l'Afrique** : EPA UE, AGOA (éligibilité
  produit par produit quand la source officielle existe), GSP, accords
  bilatéraux — traités comme des jeux de taux à part entière, zonés et sourcés.
- **Comparaison NPF ↔ préférentiel** exposée dans l'API : l'avantage réel
  (économie de droits) par partenaire et par code, avec base juridique.

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
- **Canonique TUN régénéré** : `backend/data/crawled/TUN_tariffs.json`
  (source 2026 en application — 17 542 codes, 219 845 préférences **zonées** à
  100 %, réglementation documents préservée du crawl précédent).
- **Réconciliation juin 2025 ↔ août 2026** :
  `reports/TUN_RECONCILIATION_2026-08-30.json` — 16 782 taux identiques,
  **492 changements réels** (TVA 19→7 % sur 90 codes, DC sucres/chocolats,
  carburants, montures 43→10 %…), 620 améliorations de capture, 83 codes
  restructurés. Zéro arbitrage : tout est documenté.
- **Corpus JORT** : lois de finances 2010→2026 (références JORT exactes,
  161 articles fiscaux localisés) + contingents + arrêtés taxes.
  PDFs archivés SHA-256 : `data/sources/TUN/jort/`.
- **Registre des zones préférentielles TUN** (ZALE/ZLECAf/UE/AELE/bilatéraux)
  avec statistiques observées par partenaire — base de la règle NPF côté TUN :
  la colonne DD du tarif (taux normal) sert de NPF tunisien.
- **Crawlers réutilisables** : `scripts/tun_recrawl_rates.py`,
  `scripts/tun_build_canonical.py`, `scripts/jort_crawler.py`,
  `scripts/jort_lf_pipeline.py`, `scripts/tun_reconcile.py`.

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

1. **Base NPF par pays africain couvert** : identifier le portail tarifaire
   officiel de chaque pays (DZA, TUN, EGY, ZAF, KEN, MAR…) et collecter le
   NPF national (référence obligatoire pour toute marge de préférence).
2. **Registre d'accords par pays** : blocs régionaux + accords avec le monde
   (EPA, AGOA, GSP, bilatéraux) avec statut d'application réel — un fichier
   par pays, méthode DZA.
3. **Avantages fiscaux** : collecter par pays les régimes incitatifs depuis
   les textes officiels (codes de réglementation douanière, régimes
   économiques, zones franches) — archivage SHA-256.
4. Archiver le **BOD 2023→2026** (SHA-256) et rattacher les changements de
   taux aux bulletins (entre deux éditions du tarif).
5. Rattacher **chaque préférence ZLECAf à son acte** (décrets/arrêtés
   tunisiens d'application des offres + JORT) — puis idem pour les partenaires
   (offres tarifaires publiées par les douanes nationales).
6. Exposer dans l'API : **zone d'accord** + **marge de préférence vs NPF** sur
   chaque taux (calculateur et module Opportunités), filtres ZALE/ZLECAf/UE/
   AGOA/monde.
