# Documentation tarifaire TUN — 2026-08-29

> Audit local en lecture seule. Aucun taux ni fichier source n'a été modifié. Ce document décrit la qualité documentaire disponible et ne constitue pas une validation administrative.

## Consolidation du fichier national autonome — 2026-08-29

> Traçabilité : aucune estimation, aucun mock. Les taux restent ceux du crawl tarifweb2025 (juin 2026), seule source de taux disponible. L'énumération officielle (codes + libellés) a été re-vérifiée en ligne le 2026-08-29 et croisée avec le fichier national ; les écarts sont documentés, jamais arbitrés ni comblés.

### Ce qui a été fait

1. **Re-vérification d'énumération** sur `douane.gov.tn/tarifwebnew/getresultat.php` : 17 542 codes + libellés officiels (`backend/data/crawled/TUN_enumeration_2026-08.json`).
2. **Correction d'un bug de parseur** : les libellés contenant un `<` littéral (ex. « cylindrée <= 1000 cm3 ») faisaient rejeter des pages entières — le premier passage n'avait capturé que 14 908 codes. Parseur corrigé + re-complétion ciblée des 56 préfixes manquants (retries ×5, 0 échec).
3. **Consolidation** du fichier national autonome `backend/data/crawled/TUN_tariffs.json` (`backend/scripts/consolidate_tun_national_file.py`) — taux strictement inchangés (vérifié : 0 ligne avec taxes/preferences modifiées).
4. **Méthode de calcul des droits et taxes ajoutée au fichier** (bloc `calculation_method` : assiettes publiées par la source, verbatim) + registre des 46 codes de taxes : `data/sources/TUN/tarifweb2026/tax_codes_and_assiettes.json`.
5. **Archivage de 24 documents officiels** avec SHA-256 (`data/sources/TUN/_manifest.json`) : Code des douanes (loi n°2008-34, 16 sections PDF dont CD_12 « Droits et taxes divers perçus par la douane »), arrêtés origine 2009, captures du portail Tarif Web 2026 (dont pages de détail live publiant les taux).
6. **Ré-audit documentaire** (`scripts/audit_tariff_documentation.py TUN`) + rapport machine `reports/TUN_CONSOLIDATION_2026-08-29.json`.

### Résultat

| Indicateur | Valeur |
|---|---|
| Sous-positions avant consolidation | 17 512 (toutes avec taux) |
| Sous-positions après consolidation | **17 625** — 17 512 avec taux + 113 nouveaux codes sans taux |
| Codes communs juin/août | 17 429 |
| Libellés comparés | 17 429 — **0 divergence substantielle** |
| Artefacts d'encodage corrigés (désignations juin avec ¿¿¿) | 347 (libellé officiel d'août appliqué uniquement si égalité normalisée) |
| Divergences résiduelles listées | 32 (casse/espaces ; voir rapport machine) |
| Nouveaux codes officiels ajoutés (sans taux) | 113 — dont ch.87 (82), ch.36 (4), ch.38 (3) ; `source_gaps: ["taux_import", "taux_export", "preferences"]` |
| Codes absents de l'énumération du jour (conservés, signalés) | 83 — `consolidation_flag: "CODE_ABSENT_ENUMERATION_2026-08-29"` ; 29/39 groupes préfixe-8 ont un successeur parmi les 113 nouveaux (restructurations, ex. véhicules hybrides ch.87) |
| Canonique HS6 (backend/data/TUN_tariffs.json) | **Non modifié** (taux inchangés) ; cohérence re-vérifiée : mêmes 48 écarts de règle de dérivation qu'avant consolidation, 0 régression ; 3 SH6 nouveaux (360340, 360350, 360360) sans taux disponibles → non générés, documentés |

Chaque sous-position neuve porte son libellé officiel du 2026-08-29 et un statut explicite « taux non publiés en ligne ». Aucun code n'a été supprimé : les 83 codes absents de la source du jour restent dans le fichier avec leurs taux de juin, signalés.

### Méthode de calcul des droits et taxes (assiettes publiées par la source)

Chaque taxe de chaque sous-position porte son **assiette** (base de calcul) dans le champ `assiette` — libellés conservés verbatim :

| Famille | Code(s) | Assiette (verbatim source) |
|---|---|---|
| Droit de douane | DDDROIT, DD/VEH, DD/AUT… | `VALEUR DOUANE DINARS` |
| TVA | TVA/APTAXE, TVA/AUTO, TVA/MTK, TVA/PP, TVA/RNTA | `VAL.DOU(D)+R(DT) GR.0` |
| Redevance/prestations douanières | RPD/IMPORREDEV, RPD/EXPORREDEV | `SOMME D.T (G=0.1.2.3.4.` (tronqué côté source) |
| Impôt réparation | AIR/IMPORAV | `VAL DOUANE+ SOMME DT` |
| Droits de consommation | DC/ALCDRT, DC/VOITDRT, DC/ESSDROIT… | `VALEUR DOUANE DINARS` (ad valorem) ou `QCI`/`QCS` (spécifiques) |
| Prélèvements spécifiques | P/L, P/H, P/BEUR/FRPREL, P/FRUITSPRELEV, P/VIANDEPRELV, TM/ABATTTAXE, T/MOTEURS… | `PN (KG)` (poids net) — spécifiques |
| Sanitaire/vétérinaire | D | `QCS` ou `PN(KG)/100 EXCES` |

Registre complet (46 codes, avec libellés et comptages) : `data/sources/TUN/tarifweb2026/tax_codes_and_assiettes.json`. Base légale archivée : **Code des douanes (loi n°2008-34 du 2 juin 2008)** — 16 sections PDF, dont **CD_12 « Droits et taxes divers perçus par la douane »** : `data/sources/TUN/code_douanes/`.

### Découverte du 2026-08-29 : les taux re-publiés en ligne

L'endpoint de détail `tarifwebnew/getresultat.php?choix=&chap=&sel=CODE` **publie à nouveau les taux** (vérifié live le 2026-08-29 sur 4 codes, dont 2 nouveaux : 87034010116 → RPD 3 % + DC/VOIT 10 % + TVA/AUTO 19 % ; 84852000008 → DD 0 % + TVA 7 % + RPD 3 %). Captures archivées : `data/sources/TUN/tarifweb2026/detail_*.html`. **Un re-crawl complet des 17 625 sous-positions (taux + assiettes + préférences) est désormais possible** — chantier suivant recommandé.

### Écarts de source documentés (non arbitrés)

- **Taux du fichier = crawl juin 2026** (extraction 2026-02-11) : les taux live re-publiés ne sont pas encore intégrés au fichier (re-crawl à lancer) ; aucune divergence n'est arbitrée avant le re-crawl.
- **83 codes absents de l'énumération du jour** : retraités ou restructurés côté source ; conservés tels quels.
- **113 nouveaux codes sans taux** : taux publiés en ligne (vérifié sur 2 échantillons) → rempliront lors du re-crawl.
- **Version SH et dates de publication/effet** : non documentées dans les métadonnées de la source.

## Résultat informatif

- Statut global : **INFORMATIVE_PARTIAL**
- source : **UNVERIFIED**
- temporal_validity : **PARTIAL**
- classification : **DOCUMENTED**
- taxes_and_levies : **PARTIAL**
- preference_and_origin : **PARTIAL**
- formalities : **PARTIAL**

## Inventaire et consommation

- Fichier canonique parent : backend/data/TUN_tariffs.json (5611 lignes SH6).
- Fichier national effectif : backend/data/crawled/TUN_tariffs.json (17625 lignes, 17625 codes nationaux, 5614 SH6).
- Fichier enrichi de repli : absent.
- Artefacts locaux apparentés hachés : 4 (les CSV de validation restent secondaires).
- Services/routes : TariffProviderService → authentic_tariff_service; routes /authentic-tariffs/country/...; index détaillé pour les codes nationaux.
- Import/normalisation : non identifié.

## Provenance locale

- Autorité déclarée : douane.gov.tn/tarifweb2025.
- Titre : douane.gov.tn/tarifweb2025.
- URL de ligne : https://www.douane.gov.tn; URL d'acquisition déclarée : non indiquée; autorité douanière : non indiquée.
- Archive officielle locale : **non retrouvée**.
- SHA-256 du fichier effectif : edb6aa0dd1d29500319f03be6a01560e4b428b1169b783f0188deb56297207a3.
- Extraction : 2026-02-11T21:50:47.838713 (ce n'est pas une date d'effet).
- Publication/effet : non documentée / non documentée.
- Version SH dans les métadonnées : non déclarée; déclaration trouvée dans l'adaptateur : aucune (statut : NOT_AVAILABLE).

Les champs data_status, reliability et source_quality ont été conservés pour comparaison mais n'ont pas servi au statut documentaire.

## Contrôles automatiques

- Lignes aplaties : **17625**; codes uniques : **17625**.
- Doublons : **0**; codes invalides : **0**.
- SH6 manquants : **0**; descriptions manquantes : **0**.
- Taux DD manquants : **113**; taux non analysables : **0**.
- Droits spécifiques/composites : **0**; taxes sans unité : **0**.
- Incohérences chapitre/SH6 : **0**; dates manquantes : **17625**.
- Taxes : AIR/IMPORAV (3269), D (245), DC/ALCDRT (461), DC/APDRT (437), DC/APPAUT (138), DC/ESSDROIT (28), DC/GPLDRT (20), DC/MTKDRT (27), DC/RNTADRT (27), DC/VOITDRT (374), DCS/ALCSURTAX (549), DCVBBADRT (489), DD (17512), DROIT (68), DRT (13), FDCSA/VTAXE (90), P/BEUR/FRPREL (57), P/FRUITSPRELEV (85), P/H (2), P/L (97), P/VIANDEPRELV (72), RPD/IMPORREDEV (17512), T/MOTEURS (35), T/PCEXT/PEAUX (2), TAXE (701), TAXE/APP (6), TAXE/FERRAILLES (44), TCATAXE (621), TLFTAXE (334), TM/ABATTTAXE (319), TMTSTAXE (4), TPETAXE (1032), TVA (17500).

## Échantillon rapide (10 lignes)

| Catégorie | Code national | SH6 | Description | Comparaison |
|---|---:|---:|---|---|
| agriculture | 01012100015 | 010121 | Chevaux de course,reproducteurs de race pure,de pur sang arabe | NOT_AVAILABLE |
| alimentation | 16010010006 | 160100 | Saucisses,saucissions et produits similaires de fois | NOT_AVAILABLE |
| médicament | 30012010004 | 300120 | Extraits,a usages opotherapiques,de glandes ou d'autres organes ou de leurs secretions, d'orgine humaine | NOT_AVAILABLE |
| textile | 50010000008 | 500100 | Cocons de vers a soie propres au devidage | NOT_AVAILABLE |
| machine | 84011000000 | 840110 | Reacteurs nucleaires | NOT_AVAILABLE |
| électronique | 85011010003 | 850110 | Moteurs sunchrones d'une puissance n'excedant pas 18 w | NOT_AVAILABLE |
| véhicule | 87011000007 | 870110 | Motoculteurs | NOT_AVAILABLE |
| produit chimique | 28011000006 | 280110 | Chlore | NOT_AVAILABLE |
| matière première | 25010010007 | 250100 | Eau de mer et eaux mères de salines | NOT_AVAILABLE |
| produit exonéré ou à taux nul | 02071130001 | 020711 | Coqs et poules non découpés en morceaux,frais ou réfrigérés,présentés plumes,vides,sans la tete ni les pattes,mais avec le cou,le coeur,le  foie et le gesier,dénommés "poulets 70%" | NOT_AVAILABLE |

Aucune ligne n'a pu être comparée à une archive officielle locale; aucun écart de taux n'est affirmé.

## Disponibilité par position

- Total positions : **17625**.
- Simulables : **12**.
- Calcul indisponible : **113**.
- Revue requise : **17500**.

## Analyse des DD manquants

- Lignes DD absentes/non analysables : **113**.
- Causes : DESCRIPTIVE_LINE (111), EXPLICIT_FREE (2).
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
