# Documentation tarifaire ZAF — 2026-08-29

> Audit local en lecture seule. Aucun taux ni fichier source n'a été modifié. **Outil informatif, non opposable** : le SaaS ne crée aucun droit et n'engage pas l'administration ; seules les publications officielles de l'autorité douanière font foi. Ce document décrit la qualité documentaire disponible — il ne constitue ni une validation administrative, ni un conseil juridique.

## Cadre d'usage — outil informatif, non opposable

- Statut du SaaS : **INFORMATIF_NON_OPPOSABLE** — il ne crée aucun droit et n'engage pas l'administration.
- Les publications officielles de l'autorité douanière (tarif officiel, JO, arrêtés) seules sont opposables.
- Le SaaS fournit des repères documentaires sourcés ; il ne constitue ni une décision douanière, ni un conseil juridique, ni une validation administrative.
- La rigueur documentaire (SHA-256, verbatim, écarts documentés sans arbitrage, aucun taux inventé) reste exigée et ne confère pas d'opposabilité.

## Résultat informatif

- Statut global : **INFORMATIVE_PARTIAL**
- source : **DOCUMENTED**
- temporal_validity : **NOT_AVAILABLE**
- classification : **DOCUMENTED**
- taxes_and_levies : **PARTIAL**
- preference_and_origin : **NOT_AVAILABLE**
- formalities : **NOT_AVAILABLE**
- informative_framing : **DOCUMENTED**
- verbatim_integrity : **PARTIAL**

## Inventaire et consommation

- Fichier canonique parent : backend/data/ZAF_tariffs.json (5619 lignes SH6).
- Fichier national effectif : backend/data/crawled/ZAF_tariffs.json (8589 lignes, 8589 codes nationaux, 5619 SH6).
- Fichier enrichi de repli : absent.
- Artefacts locaux apparentés hachés : 4 (les CSV de validation restent secondaires).
- Services/routes : TariffProviderService → authentic_tariff_service; routes /authentic-tariffs/country/...; index détaillé pour les codes nationaux.
- Import/normalisation : non identifié.

## Provenance locale

- Autorité déclarée : sars.gov.za.
- Titre : sars.gov.za.
- URL de ligne : https://www.sars.gov.za/customs-and-excise/tariff-books/schedules/; URL d'acquisition déclarée : non indiquée; autorité douanière : non indiquée.
- Archive officielle locale : **disponible**.
- SHA-256 du fichier effectif : 23e7f03cb492b337704caea944fce64986010b14b4163039f0051692d2ce5e6d.
- Extraction : non indiquée (ce n'est pas une date d'effet).
- Publication/effet : non documentée / non documentée.
- Version SH dans les métadonnées : non déclarée; déclaration trouvée dans l'adaptateur : aucune (statut : NOT_AVAILABLE).

Les champs data_status, reliability et source_quality ont été conservés pour comparaison mais n'ont pas servi au statut documentaire.

## Contrôles automatiques

- Lignes aplaties : **8589**; codes uniques : **8589**.
- Doublons : **0**; codes invalides : **0**.
- SH6 manquants : **0**; descriptions manquantes : **0**.
- Taux DD manquants : **1**; taux non analysables : **0**.
- Droits spécifiques/composites : **1077**; taxes sans unité : **0**.
- Incohérences chapitre/SH6 : **0**; dates manquantes : **8589**.
- Taxes : AFCFTA PREFERENTIAL RATE (8589), DD (8589), EFTA PREFERENTIAL RATE (8589), EU / UK PREFERENTIAL RATE (8589), MERCOSUR PREFERENTIAL RATE (8589), SADC PREFERENTIAL RATE (8589).

## Échantillon rapide (10 lignes)

| Catégorie | Code national | SH6 | Description | Comparaison |
|---|---:|---:|---|---|
| agriculture | 010121 | 010121 | Pure-bred breeding animals | NOT_AVAILABLE |
| alimentation | 16010010 | 160100 | Paté de foie gras and foie gras (goose liver paste) | NOT_AVAILABLE |
| médicament | 300120 | 300120 | Extracts of glands or other organs or of their secretions | NOT_AVAILABLE |
| textile | 500100 | 500100 | Silk-worm cocoons suitable for reeling | NOT_AVAILABLE |
| machine | 840110 | 840110 | Nuclear reactors | NOT_AVAILABLE |
| électronique | 850110 | 850110 | Motors of an output not exceeding 37,5 W | NOT_AVAILABLE |
| véhicule | 870110 | 870110 | Single axle tractors | NOT_AVAILABLE |
| produit chimique | 280110 | 280110 | Chlorine | NOT_AVAILABLE |
| matière première | 25010010 | 250100 | Not for human consumption | NOT_AVAILABLE |
| produit exonéré ou à taux nul | 98010003 | 980100 | Electric accumulators of tariff subheadings 8507.30, 8507.50, 8507.60 and 8507.80 | NOT_AVAILABLE |

Aucune ligne n'a pu être comparée à une archive officielle locale; aucun écart de taux n'est affirmé.

## Disponibilité par position

- Total positions : **8589**.
- Simulables : **4328**.
- Calcul indisponible : **1**.
- Revue requise : **4260**.

## Analyse des DD manquants

- Lignes DD absentes/non analysables : **1**.
- Causes : TRUE_MISSING (1).
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
