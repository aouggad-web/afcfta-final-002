# Documentation tarifaire MAR — 2026-07-24

> Audit local en lecture seule. Aucun taux ni fichier source n'a été modifié. Ce document décrit la qualité documentaire disponible et ne constitue pas une validation administrative.

## Résultat informatif

- Statut global : **INFORMATIVE_PARTIAL**
- source : **UNVERIFIED**
- temporal_validity : **PARTIAL**
- classification : **DOCUMENTED**
- taxes_and_levies : **PARTIAL**
- preference_and_origin : **NOT_AVAILABLE**
- formalities : **PARTIAL**

## Inventaire et consommation

- Fichier canonique parent : backend/data/MAR_tariffs.json (5610 lignes SH6).
- Fichier national effectif : backend/data/crawled/MAR_tariffs.json (13114 lignes, 13114 codes nationaux, 5610 SH6).
- Fichier enrichi de repli : absent.
- Artefacts locaux apparentés hachés : 4 (les CSV de validation restent secondaires).
- Services/routes : TariffProviderService → authentic_tariff_service; routes /authentic-tariffs/country/...; index détaillé pour les codes nationaux.
- Import/normalisation : non identifié.

## Provenance locale

- Autorité déclarée : douane.gov.ma/adil.
- Titre : douane.gov.ma/adil.
- URL de ligne : https://www.douane.gov.ma; URL d'acquisition déclarée : non indiquée; autorité douanière : non indiquée.
- Archive officielle locale : **non retrouvée**.
- SHA-256 du fichier effectif : 8a8671685c7736965c1d9e38d19f9b77725f583f152df2f5d372f62b0ccc1368.
- Extraction : 2026-02-11T22:41:08.772056 (ce n'est pas une date d'effet).
- Publication/effet : non documentée / non documentée.
- Version SH dans les métadonnées : non déclarée; déclaration trouvée dans l'adaptateur : aucune (statut : NOT_AVAILABLE).

Les champs data_status, reliability et source_quality ont été conservés pour comparaison mais n'ont pas servi au statut documentaire.

## Contrôles automatiques

- Lignes aplaties : **13114**; codes uniques : **13114**.
- Doublons : **0**; codes invalides : **0**.
- SH6 manquants : **0**; descriptions manquantes : **0**.
- Taux DD manquants : **142**; taux non analysables : **0**.
- Droits spécifiques/composites : **0**; taxes sans unité : **0**.
- Incohérences chapitre/SH6 : **0**; dates manquantes : **13114**.
- Taxes : DD (12972), TAXE PARAFISCALE À L'IMPORTATION (TPI) (12971), TVA (12586).

## Échantillon rapide (10 lignes)

| Catégorie | Code national | SH6 | Description | Comparaison |
|---|---:|---:|---|---|
| agriculture | 0101210000 | 010121 | - Reproducteurs de race pure (a.) | NOT_AVAILABLE |
| alimentation | 1601001000 | 160100 | - - - de foie£- - - autres : | NOT_AVAILABLE |
| médicament | 3001200000 | 300120 | Extraits de glandes ou d'autres organes ou de leurs sécrétions | NOT_AVAILABLE |
| textile | 5001000000 | 500100 | Cocons de vers à soie propres au dévidage | NOT_AVAILABLE |
| machine | 8401200000 | 840120 | Machines et appareils pour la séparation isotopique, et leurs parties | NOT_AVAILABLE |
| électronique | 8501101000 | 850110 | - - conçus pour l'équipement de jouets ou modèles réduits pour le divertis- sement£- - - autres : | NOT_AVAILABLE |
| véhicule | 8701101100 | 870110 | - - - à moteur à explosion ou à combustion interne . | NOT_AVAILABLE |
| produit chimique | 2801100000 | 280110 | Chlore | NOT_AVAILABLE |
| matière première | 2501000011 | 250100 | - - - destinés à la transformation chimique (séparation Na du CL) pour la fabrica- tion d'autres produits | NOT_AVAILABLE |
| produit exonéré ou à taux nul | 0407111000 | 040711 | - - œufs SFP (Specified Pathogene Free) ou EMPS (Exempts de microorganismes pathogènes spécifiques) (a) | NOT_AVAILABLE |

Aucune ligne n'a pu être comparée à une archive officielle locale; aucun écart de taux n'est affirmé.

## Disponibilité par position

- Total positions : **13114**.
- Simulables : **0**.
- Calcul indisponible : **0**.
- Revue requise : **13114**.

## Analyse des DD manquants

- Lignes DD absentes/non analysables : **142**.
- Causes : DESCRIPTIVE_LINE (142).
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
