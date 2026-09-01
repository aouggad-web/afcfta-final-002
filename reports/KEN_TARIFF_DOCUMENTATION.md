# Documentation tarifaire KEN — 2026-07-24

> Audit local en lecture seule. Aucun taux ni fichier source n'a été modifié. Ce document décrit la qualité documentaire disponible et ne constitue pas une validation administrative.

## Résultat informatif

- Statut global : **INFORMATIVE_PARTIAL**
- source : **UNVERIFIED**
- temporal_validity : **NOT_AVAILABLE**
- classification : **DOCUMENTED**
- taxes_and_levies : **PARTIAL**
- preference_and_origin : **PARTIAL**
- formalities : **NOT_AVAILABLE**

## Inventaire et consommation

- Fichier canonique parent : backend/data/KEN_tariffs.json (5604 lignes SH6).
- Fichier national effectif : backend/data/crawled/KEN_tariffs.json (5984 lignes, 5935 codes nationaux, 5604 SH6).
- Fichier enrichi de repli : absent.
- Artefacts locaux apparentés hachés : 4 (les CSV de validation restent secondaires).
- Services/routes : TariffProviderService → authentic_tariff_service; routes /authentic-tariffs/country/...; index détaillé pour les codes nationaux.
- Import/normalisation : non identifié.

## Provenance locale

- Autorité déclarée : EAC Common External Tariff 2022.
- Titre : EAC Common External Tariff 2022.
- URL de ligne : https://www.kra.go.ke/images/publications/EAC-CET-2022-VERSION-30TH-JUNE-Fn.pdf; URL d'acquisition déclarée : non indiquée; autorité douanière : non indiquée.
- Archive officielle locale : **non retrouvée**.
- SHA-256 du fichier effectif : d89c40259421ef386880c25f5f38519fb5d380ba1752558a84288b23bd37a09e.
- Extraction : non indiquée (ce n'est pas une date d'effet).
- Publication/effet : non documentée / non documentée.
- Version SH dans les métadonnées : HS 2022; déclaration trouvée dans l'adaptateur : aucune (statut : DOCUMENTED).

Les champs data_status, reliability et source_quality ont été conservés pour comparaison mais n'ont pas servi au statut documentaire.

## Contrôles automatiques

- Lignes aplaties : **5984**; codes uniques : **5935**.
- Doublons : **49**; codes invalides : **0**.
- SH6 manquants : **0**; descriptions manquantes : **0**.
- Taux DD manquants : **91**; taux non analysables : **0**.
- Droits spécifiques/composites : **0**; taxes sans unité : **0**.
- Incohérences chapitre/SH6 : **0**; dates manquantes : **5984**.
- Taxes : DD (5941), EXCISE DUTY (65), IMPORT DECLARATION FEE (IDF) (5984), RAILWAY DEVELOPMENT LEVY (RDL) (5984), TVA (5984).

## Échantillon rapide (10 lignes)

| Catégorie | Code national | SH6 | Description | Comparaison |
|---|---:|---:|---|---|
| agriculture | 01012100 | 010121 | -- Pure-bred breeding animals | NOT_AVAILABLE |
| alimentation | 16010000 | 160100 | Sausages and similar products, of meat, meat offal, blood or insects; food preparations based on these products. | NOT_AVAILABLE |
| médicament | 30012000 | 300120 | - Extracts of glands or other organs or of their secretions | NOT_AVAILABLE |
| textile | 50010000 | 500100 | Silk-worm cocoons suitable for reeling. | NOT_AVAILABLE |
| machine | 84011000 | 840110 | - Nuclear reactors | NOT_AVAILABLE |
| électronique | 85011000 | 850110 | - Motors of an output not exceeding 37.5 W | NOT_AVAILABLE |
| véhicule | 87011000 | 870110 | - Single axle tractors | NOT_AVAILABLE |
| produit chimique | 28011000 | 280110 | - Chlorine | NOT_AVAILABLE |
| matière première | 25010010 | 250100 | --- Raw salt | NOT_AVAILABLE |
| produit exonéré ou à taux nul | 04015000 | 040150 | - Of a fat content, by weight, exceeding 10% | NOT_AVAILABLE |

Aucune ligne n'a pu être comparée à une archive officielle locale; aucun écart de taux n'est affirmé.

## Disponibilité par position

- Total positions : **5984**.
- Simulables : **0**.
- Calcul indisponible : **0**.
- Revue requise : **5984**.

## Analyse des DD manquants

- Lignes DD absentes/non analysables : **91**.
- Causes : EXPLICIT_FREE (91).
Aucune cause n'est transformée en taux numérique.

## Lacunes et actions

- Archive officielle tarifaire non retrouvée localement.
- Date de publication et date d'effet documentées absentes.
- Date d'effet juridiquement documentée absente.
- Écart entre les lignes canoniques et crawled; les divergences restent en revue.
- Action : Archiver le document tarifaire de l'autorité déclarée sans remplacer le fichier actuel.
- Action : Comparer un échantillon de lignes et conserver les empreintes des documents.
- Action : Documenter la version SH et les dates de publication/effet.
- Action : Résoudre les divergences entre artefacts avant une utilisation documentaire plus forte.

Le même contrôle peut être relancé pour les autres pays en paramètre; aucun script séparé n'est créé.
