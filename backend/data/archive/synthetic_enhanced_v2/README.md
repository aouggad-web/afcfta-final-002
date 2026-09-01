# Archive — fichiers tarifs synthétiques (`enhanced_v2`) retirés du service

**Date** : 2026-09-01 — Audit `audits/AUDIT_CALCULATEUR_DONNEES_TARIFAIRES_2026-09-01.md`, action P0-1.

## Pourquoi ce retrait

Les 14 fichiers pays ci-dessous étaient au format `enhanced_v2` **sans statut de
provenance** (`data_status` absent) et avec des sous-positions 10 chiffres
**générées par template** (ex. `source: "Nomenclature nationale AGO (type: use)"`,
libellés génériques « Usage spécifique » / « Autre usage », ~16 141 sous-positions
identiques par pays). Ils violaient la doctrine tarifaire du projet
(README §« Doctrine tarifaire : re-collecte officielle uniquement ») :
*refuser les lignes estimées, synthétiques, générées ou répliquées par chapitre*,
et étaient pourtant servis par l'API de production.

Pays concernés : **AGO, COM, DJI, ERI, LBY, MDG, MOZ, MRT, MWI, SDN, STP, SYC, ZMB, ZWE**.

## Contenu

- `root/` : copies issues de `backend/data/` (chemin de service `authentic_tariff_service`)
- `tariffs_dir/` : copies issues de `backend/data/tariffs/` (chemin `tariff_data_service`)

## Ce qui est servi à la place (honnête)

Ces pays **ne disparaissent pas** de la plateforme :

- Le moteur de calcul continue de servir leurs taux **MFN HS6 officiels**
  (WITS / UNCTAD-TRAINS — Banque mondiale, source vérifiable) via les fichiers
  crawlés `backend/data/crawled/{ISO3}_tariffs.json`.
- Les endpoints nationaux (sous-positions 8-10 chiffres, lignes détaillées)
  retournent désormais une **erreur explicite** `COUNTRY_NOT_RECRAWLED`
  (voir `backend/services/tariff_doctrine.py`) au lieu de données fabriquées.

## Ré-activation

Un pays sort de cet état uniquement par un **crawl national authentique**
(`backend/scripts/crawl_all_countries.py --run/--validate-file {ISO3}`),
produisant un fichier `canonical_v4` avec `data_status` vérifiable
(VERIFIED / CRAWLED_AUTHENTIC), `source_name` et `source_url`.
