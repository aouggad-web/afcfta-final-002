# Documentation tarifaire ZAF — 2026-08-30

> Audit local en lecture seule. Aucun taux ni fichier source n'a été modifié. **Outil informatif, non opposable** : le SaaS ne crée aucun droit et n'engage pas l'administration ; seules les publications officielles de l'autorité douanière font foi. Ce document décrit la qualité documentaire disponible — il ne constitue ni une validation administrative, ni un conseil juridique.

## Complétion exhaustive ZAF — annexes SARS + ITAC — 2026-08-29

> Traçabilité : extraction verbatim des PDF officiels, taux numériques lus littéralement dans les chaînes publiées. Aucune fusion avec le taux général — sections séparées dans `schedules` du fichier national.

### Ce qui a été fait

1. **Découverte des URL exactes** des annexes via l'index Wayback CDX du répertoire `SCEA1964` (les URL devinées renvoyaient 403/404 — la page « tariff book » SARS a été restructurée).
2. **Téléchargement + archivage SHA-256** de 6 documents supplémentaires (manifeste : **7 actes**) :
   - Schedule 1 **Part 2A/2B** — droits d'accise spécifiques (140 + 148 lignes ; dates PDF 2026-04-30 / 2025-04-01)
   - **Schedule 2** — anti-dumping (Part 1 : 401 lignes), compensateurs (Part 2 : 0 ligne publiée), sauvegarde (Part 3 : 30 lignes) — date PDF **2026-07-24**
   - **Schedule 3** — rebates industriels (1 091 lignes, extents verbatim « Full duty »/%, date 2026-06-19)
   - **Schedule 8** — licences et frais (34 lignes)
   - **ITAC** — mesures anti-dumping définitives en vigueur au 31/12/2022 (références GG, 3 pages verbatim)
3. **Bloc `calculation_method`** : bases publiées (ad valorem valeur en douane ; composés c/kg, c/li, c/la ; remèdes = taux additionnels par produit ET origine ; rebates = atténuations section 75 ; accise spécifique c/l, c/kg).
4. **Bloc `policy` verbatim** déclaré → `verbatim_integrity: DOCUMENTED`.

### Résultat

| Indicateur | Valeur |
|---|---|
| Schedule 1 Part 1 (taux général + préférentiels) | 8 589 positions — AfCFTA 4 654 lignes 0 % / 3 750 > 0 |
| Schedule 2 remèdes | 431 lignes (401 AD + 30 safeguard) — 54 SH6 concernés, tous présents dans Part 1 |
| Schedule 3 rebates | 1 091 lignes |
| Accises spécifiques | 288 lignes (2A + 2B) |
| Licences (Sch 8) | 34 lignes |
| Actes archivés | **7 PDF SHA-256** (SARS ×6 + ITAC ×1) |
| Audit | source DOCUMENTED · integrity DOCUMENTED · framing DOCUMENTED |

### Écarts de source documentés (non arbitrés)

- **Part 2 countervailing : 0 ligne publiée** dans le PDF du jour (aucun droit compensateur en vigueur selon la source).
- **NRCS (spécifications obligatoires / LoA)** : inaccessible depuis ce réseau — écart documenté ; alternative à étudier : Government Gazette.
- **DALRRD / DFFE / liste TVA zéro-rated** : à sonder (prochaine phase).
- Dates d'effet juridiques : dates PDF conservées (2026-07-24, 2026-06-19, 2026-04-30…) ; version SH non déclarée explicitement dans les PDF.

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
- verbatim_integrity : **DOCUMENTED**

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
- SHA-256 du fichier effectif : 45b2c970b6083738daee6f693e725b9de8d32cb0c2033601f03e884911a0f3a2.
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
