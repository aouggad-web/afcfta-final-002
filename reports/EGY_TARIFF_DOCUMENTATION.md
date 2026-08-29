# Documentation tarifaire EGY — 2026-07-24

> Audit local en lecture seule. Aucun taux ni fichier source n'a été modifié. Ce document décrit la qualité documentaire disponible et ne constitue pas une validation administrative.

## Résultat informatif

- Statut global : **INFORMATIVE_PARTIAL**
- source : **UNVERIFIED**
- temporal_validity : **PARTIAL**
- classification : **DOCUMENTED**
- taxes_and_levies : **PARTIAL**
- preference_and_origin : **NOT_AVAILABLE**
- formalities : **NOT_AVAILABLE**

## Inventaire et consommation

- Fichier canonique parent : backend/data/EGY_tariffs.json (5541 lignes SH6).
- Fichier national effectif : backend/data/crawled/EGY_tariffs.json (8746 lignes, 8746 codes nationaux, 5541 SH6).
- Fichier enrichi de repli : absent.
- Artefacts locaux apparentés hachés : 4 (les CSV de validation restent secondaires).
- Services/routes : TariffProviderService → authentic_tariff_service; routes /authentic-tariffs/country/...; index détaillé pour les codes nationaux.
- Import/normalisation : non identifié.

## Provenance locale

- Autorité déclarée : Egyptian Customs Authority (customs.gov.eg/Services/Tarif).
- Titre : Egyptian Customs Authority (customs.gov.eg/Services/Tarif).
- URL de ligne : https://customs.gov.eg/Services/Tarif; URL d'acquisition déclarée : non indiquée; autorité douanière : non indiquée.
- Archive officielle locale : **non retrouvée**.
- SHA-256 du fichier effectif : c97045a4fc5909382b6a8ebce412af75e9cdded924c805f523c2030c36e1d065.
- Extraction : 2026-06-13T22:04:10.339176+00:00 (ce n'est pas une date d'effet).
- Publication/effet : non documentée / non documentée.
- Version SH dans les métadonnées : non déclarée; déclaration trouvée dans l'adaptateur : aucune (statut : NOT_AVAILABLE).

Les champs data_status, reliability et source_quality ont été conservés pour comparaison mais n'ont pas servi au statut documentaire.

## Contrôles automatiques

- Lignes aplaties : **8746**; codes uniques : **8746**.
- Doublons : **0**; codes invalides : **0**.
- SH6 manquants : **0**; descriptions manquantes : **2**.
- Taux DD manquants : **0**; taux non analysables : **0**.
- Droits spécifiques/composites : **7677**; taxes sans unité : **7677**.
- Incohérences chapitre/SH6 : **0**; dates manquantes : **8746**.
- Taxes : DD (8746), TJ (188), TVA (8709).

## Échantillon rapide (10 lignes)

| Catégorie | Code national | SH6 | Description | Comparaison |
|---|---:|---:|---|---|
| agriculture | 0101210000 | 010121 | Chevaux vivants (non reproducteurs) | NOT_AVAILABLE |
| alimentation | 1601000000 | 160100 | Saucisses et produits similaires | NOT_AVAILABLE |
| médicament | 3001200000 | 300120 | Extraits de glandes ou d'autres organes ou de leurs sécrétions | NOT_AVAILABLE |
| textile | 5001000000 | 500100 | Cocons de vers à soie | NOT_AVAILABLE |
| machine | 8401100000 | 840110 | Réacteurs nucléaires | NOT_AVAILABLE |
| électronique | 8501100000 | 850110 | Moteurs électriques ≤37,5W | NOT_AVAILABLE |
| véhicule | 8701100010 | 870110 | Tracteurs agricoles à roues | NOT_AVAILABLE |
| produit chimique | 2801100000 | 280110 | Chlore | NOT_AVAILABLE |
| matière première | 2501000010 | 250100 | Sel (y compris le sel préparé pour la table et le sel dénaturé) et chlorure de sodium pur | NOT_AVAILABLE |
| produit exonéré ou à taux nul | 2207101000 | 220710 | Alcool éthylique non dénaturé >80% | NOT_AVAILABLE |

Aucune ligne n'a pu être comparée à une archive officielle locale; aucun écart de taux n'est affirmé.

## Disponibilité par position

- Total positions : **8746**.
- Simulables : **38**.
- Calcul indisponible : **0**.
- Revue requise : **8708**.

## Analyse des DD manquants

- Lignes DD absentes/non analysables : **0**.
- Causes : aucune.
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
