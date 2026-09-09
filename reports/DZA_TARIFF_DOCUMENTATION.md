# Documentation tarifaire DZA — 2026-07-24

> Audit local en lecture seule. Aucun taux ni fichier source n'a été modifié. Ce document décrit la qualité documentaire disponible et ne constitue pas une validation administrative.

## Résultat informatif

- Statut global : **INFORMATIVE_PARTIAL**
- source : **UNVERIFIED**
- temporal_validity : **PARTIAL**
- classification : **DOCUMENTED**
- taxes_and_levies : **PARTIAL**
- preference_and_origin : **PARTIAL**
- formalities : **PARTIAL**

## Inventaire et consommation

- Fichier canonique parent : backend/data/DZA_tariffs.json (5533 lignes SH6).
- Fichier national effectif : backend/data/crawled/DZA_tariffs.json (17061 lignes, 17061 codes nationaux, 5515 SH6).
- Fichier enrichi de repli : backend/data/crawled/DZA_tariffs_enriched.json.
- Artefacts locaux apparentés hachés : 5 (les CSV de validation restent secondaires).
- Services/routes : TariffProviderService → authentic_tariff_service; routes /authentic-tariffs/country/...; index détaillé pour les codes nationaux.
- Import/normalisation : backend/scripts/build_dza_tariffs_complete.py, backend/scripts/enrich_dza_fast_json.py, backend/etl/dza_tariff_connector.py, engine/converters/dza_converter.py, engine/adapters/dza_conformepro_adapter.py.

## Provenance locale

- Autorité déclarée : conformepro.dz (données douane.gov.dz).
- Titre : Tarif national intégré — données de crawl conformepro.dz.
- URL de ligne : https://conformepro.dz/resources/tarif-douanier/sous-position/01.01.211100/chevaux-reproducteurs-de-race-pure-de-course-de-pur-sang-arabe; URL d'acquisition déclarée : https://conformepro.dz/resources/tarif-douanier; autorité douanière : https://www.douane.gov.dz.
- Archive officielle locale : **non retrouvée**.
- SHA-256 du fichier effectif : ade8c03f10217a6c4d58916a9adc99e305802a80783266837fa03a09a543d3d2.
- Extraction : 2026-06-17T20:33:09.090295 (ce n'est pas une date d'effet).
- Publication/effet : non documentée / non documentée.
- Version SH dans les métadonnées : non déclarée; déclaration trouvée dans l'adaptateur : HS2022 (statut : UNVERIFIED).

Les champs data_status, reliability et source_quality ont été conservés pour comparaison mais n'ont pas servi au statut documentaire.

## Contrôles automatiques

- Lignes aplaties : **17061**; codes uniques : **17061**.
- Doublons : **0**; codes invalides : **0**.
- SH6 manquants : **0**; descriptions manquantes : **0**.
- Taux DD manquants : **236**; taux non analysables : **0**.
- Droits spécifiques/composites : **0**; taxes sans unité : **0**.
- Incohérences chapitre/SH6 : **0**; dates manquantes : **17061**.
- Taxes : DAPS (779), DD (16825), PRCT (17061), TCS (15762), TIC (160), TVA (16805).

## Échantillon rapide (10 lignes)

| Catégorie | Code national | SH6 | Description | Comparaison |
|---|---:|---:|---|---|
| agriculture | 0101211100 | 010121 | Chevaux vivants de pur-sang arabe, destinés à la reproduction de race pure et à la course. | NOT_AVAILABLE |
| alimentation | 1601001000 | 160100 | Préparations alimentaires à base de viande (hachée ou transformée) conditionnées en boyaux ou contenants similaires (charcuterie), excluant la volaille ou le foie. | NOT_AVAILABLE |
| médicament | 3001201000 | 300120 | Extraits de glandes ou d'autres organes ou de leurs sécrétions, d'origine humaine, à usages opothérapiques (thérapie organique). | NOT_AVAILABLE |
| textile | 5001000000 | 500100 | Cocons de vers à soie propres au dévidage (aptes à être déroulés pour obtenir du fil de soie). | NOT_AVAILABLE |
| machine | 8401100000 | 840110 | Installations complexes conçues pour initier, soutenir et contrôler une réaction nucléaire en chaîne, utilisées principalement pour la production d'énergie électrique, la recherche ou la production d'isotopes. | NOT_AVAILABLE |
| électronique | 8501101100 | 850110 | Moteurs électriques universels, d'une puissance n'excédant pas 37,5 W, spécifiquement d'une puissance inférieure à 18,65 W. | NOT_AVAILABLE |
| véhicule | 8701101000 | 870110 | Collections (CKD/SKD) de tracteurs à essieu simple, généralement utilisés pour le labour et la culture dans les petites exploitations agricoles (motoculteurs), destinés aux industries de montage. | NOT_AVAILABLE |
| produit chimique | 2801100000 | 280110 | Élément chimique non métallique, le Chlore (Cl), souvent utilisé comme agent désinfectant ou dans l'industrie chimique. | NOT_AVAILABLE |
| matière première | 2501001000 | 250100 | Sel pur (chlorure de sodium) d'une grande pureté, utilisé dans diverses applications chimiques, pharmaceutiques ou industrielles. | NOT_AVAILABLE |
| produit exonéré ou à taux nul | 9800000000 | 980000 | Vêtements, articles de toilette et autres biens neufs ou usagés destinés à l'usage personnel du voyageur (souvent exemptés de droits/taxes à l'importation). | NOT_AVAILABLE |

Aucune ligne n'a pu être comparée à une archive officielle locale; aucun écart de taux n'est affirmé.

## Disponibilité par position

- Total positions : **17061**.
- Simulables : **139**.
- Calcul indisponible : **0**.
- Revue requise : **16922**.

## Analyse des DD manquants

- Lignes DD absentes/non analysables : **236**.
- Causes : EXPLICIT_EXEMPT (131), TRUE_MISSING (105).
Aucune cause n'est transformée en taux numérique.

## Lacunes et actions

- Archive officielle tarifaire non retrouvée localement.
- Date de publication et date d'effet documentées absentes.
- Version SH explicite absente des métadonnées JSON consommées.
- Écart entre les lignes canoniques et crawled; les divergences restent en revue.
- Action : Archiver le document tarifaire de l'autorité déclarée sans remplacer le fichier actuel.
- Action : Comparer un échantillon de lignes et conserver les empreintes des documents.
- Action : Documenter la version SH et les dates de publication/effet.
- Action : Résoudre les divergences entre artefacts avant une utilisation documentaire plus forte.

Le même contrôle peut être relancé pour les autres pays en paramètre; aucun script séparé n'est créé.
