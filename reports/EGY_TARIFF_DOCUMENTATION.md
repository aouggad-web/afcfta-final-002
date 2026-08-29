# Documentation tarifaire EGY — 2026-08-29

> Audit local en lecture seule. Aucun taux ni fichier source n'a été modifié. **Outil informatif, non opposable** : le SaaS ne crée aucun droit et n'engage pas l'administration ; seules les publications officielles de l'autorité douanière font foi. Ce document décrit la qualité documentaire disponible — il ne constitue ni une validation administrative, ni un conseil juridique.

## Cadre d'usage — outil informatif, non opposable

- Statut du SaaS : **INFORMATIF_NON_OPPOSABLE** — il ne crée aucun droit et n'engage pas l'administration.
- Les publications officielles de l'autorité douanière (tarif officiel, JO, arrêtés) seules sont opposables.
- Le SaaS fournit des repères documentaires sourcés ; il ne constitue ni une décision douanière, ni un conseil juridique, ni une validation administrative.
- La rigueur documentaire (SHA-256, verbatim, écarts documentés sans arbitrage, aucun taux inventé) reste exigée et ne confère pas d'opposabilité.

## Cadre d'usage — outil informatif, non opposable

- Statut du SaaS : **INFORMATIF_NON_OPPOSABLE** — il ne crée aucun droit et n'engage pas l'administration.
- Les publications officielles de l'autorité douanière (tarif officiel, JO, arrêtés) seules sont opposables.
- Le SaaS fournit des repères documentaires sourcés ; il ne constitue ni une décision douanière, ni un conseil juridique, ni une validation administrative.
- La rigueur documentaire (SHA-256, verbatim, écarts documentés sans arbitrage, aucun taux inventé) reste exigée et ne confère pas d'opposabilité.

## Résultat informatif

- Statut global : **INFORMATIVE_PARTIAL**
- source : **DOCUMENTED**
- temporal_validity : **PARTIAL**
- classification : **DOCUMENTED**
- taxes_and_levies : **PARTIAL**
- preference_and_origin : **NOT_AVAILABLE**
- formalities : **PARTIAL**
- informative_framing : **DOCUMENTED**
- verbatim_integrity : **DOCUMENTED**

## Inventaire et consommation

- Fichier canonique parent : backend/data/EGY_tariffs.json (5541 lignes SH6).
- Fichier national effectif : backend/data/crawled/EGY_tariffs.json (8818 lignes, 8818 codes nationaux, 5574 SH6).
- Fichier enrichi de repli : absent.
- Artefacts locaux apparentés hachés : 4 (les CSV de validation restent secondaires).
- Services/routes : TariffProviderService → authentic_tariff_service; routes /authentic-tariffs/country/...; index détaillé pour les codes nationaux.
- Import/normalisation : non identifié.

## Provenance locale

- Autorité déclarée : customs.gov.eg — Autorité Égyptienne des Douanes.
- Titre : customs.gov.eg — Autorité Égyptienne des Douanes.
- URL de ligne : https://www.customs.gov.eg/Services/Tarif; URL d'acquisition déclarée : non indiquée; autorité douanière : non indiquée.
- Archive officielle locale : **disponible**.
- SHA-256 du fichier effectif : 25852dffb6af464ffcb4c38b82cd41fc5585e150d03bfcc2b397dfe71091118c.
- Extraction : 2026-08-29T21:57:37.493425+00:00 (ce n'est pas une date d'effet).
- Publication/effet : non documentée / non documentée.
- Version SH dans les métadonnées : non déclarée; déclaration trouvée dans l'adaptateur : aucune (statut : NOT_AVAILABLE).

Les champs data_status, reliability et source_quality ont été conservés pour comparaison mais n'ont pas servi au statut documentaire.

## Contrôles automatiques

- Lignes aplaties : **8818**; codes uniques : **8818**.
- Doublons : **0**; codes invalides : **0**.
- SH6 manquants : **0**; descriptions manquantes : **8803**.
- Taux DD manquants : **8803**; taux non analysables : **0**.
- Droits spécifiques/composites : **7976**; taxes sans unité : **7976**.
- Incohérences chapitre/SH6 : **0**; dates manquantes : **8818**.
- Taxes : DD (15), ID (8764), ID_2 (1), TVA (8808), VAT_2 (17), تامين صحى وزارة الصحة (18), رسم محصلة لحساب غرفة دخان (6), رسم محصلة لحساب غرفة نسيج (217), رسم محصلة لحساب غرفةجلود (8), ضريبة الجدول (187), ضريبة الجدول_2 (2).

## Échantillon rapide (10 lignes)

| Catégorie | Code national | SH6 | Description | Comparaison |
|---|---:|---:|---|---|
| agriculture | 0101210000 | 010121 |  | NOT_AVAILABLE |
| alimentation | 1601000000 | 160100 |  | NOT_AVAILABLE |
| médicament | 3001200000 | 300120 |  | NOT_AVAILABLE |
| textile | 5001000000 | 500100 |  | NOT_AVAILABLE |
| machine | 8401100000 | 840110 |  | NOT_AVAILABLE |
| électronique | 8501100000 | 850110 |  | NOT_AVAILABLE |
| véhicule | 8701100010 | 870110 |  | NOT_AVAILABLE |
| produit chimique | 2801100000 | 280110 |  | NOT_AVAILABLE |
| matière première | 2501000010 | 250100 |  | NOT_AVAILABLE |
| produit exonéré ou à taux nul | 0101290000 | 010129 |  | NOT_AVAILABLE |

Aucune ligne n'a pu être comparée à une archive officielle locale; aucun écart de taux n'est affirmé.

## Disponibilité par position

- Total positions : **8818**.
- Simulables : **0**.
- Calcul indisponible : **72**.
- Revue requise : **8746**.

## Analyse des DD manquants

- Lignes DD absentes/non analysables : **8803**.
- Causes : DESCRIPTIVE_LINE (10), EXPLICIT_FREE (1790), TRUE_MISSING (7003).
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
