# Mise à jour tarifaire DZA — 2026-08-29 (re-crawl authentique complet)

> Reconnaissance de traçabilité : toutes les données proviennent d'extractions sourcées. Aucun taux estimé, mocké ou extrapolé. Les champs non publiés par la source sont laissés vides (`None`) et documentés comme écarts de source, jamais comblés par calcul.

## 1. Ce qui a été fait

1. **Re-crawl exhaustif** de conformepro.dz (données douane.gov.dz) : 17 115 sous-positions nationales (10 chiffres), 95 chapitres, 21 sections — crawl du 2026-08-28/29 (outil : `backend/crawlers/countries/algeria_conformepro_scraper.py`, concurrence 3, délai 1,5 s).
2. **Rattrapage des 2 sous-positions ch.98** manquées par le crawl principal (9810100000, 9810200000), vérifiées live le 2026-08-29 (`backend/data/crawled/DZA_progress_1206.json`).
3. **Reconstruction** du fichier national : `backend/scripts/build_dza_tariffs_authentic_v2.py` → `backend/data/crawled/DZA_tariffs.json`.
4. **Régénération du fichier canonique HS6** : `backend/scripts/build_dza_canonical_hs6_authentic.py` → `backend/data/DZA_tariffs.json` (l'ancien, généré le 2026-06-16 avec des taux ETL, divergeait sur **1 633 taux DD**).
5. **Archivage de 8 documents officiels** avec SHA-256 (`data/sources/DZA/legislation/_manifest.json`).
6. **Extractions verbatim** de la nomenclature officielle des taxes/F.A.P et des articles douaniers de la LF 2026.
7. **Croisement systématique** crawl ↔ Tarif d'usage DGD 2020 (898 lignes comparables).

## 2. Résultat sur les données

| Indicateur | Valeur |
|---|---|
| Sous-positions `crawled_authentic` | **17 115 / 17 115 (100%)** — 0 ligne ETL |
| Sous-positions avec formalités | 9 069 |
| Sous-positions avec avantages (FTA) | 17 048 |
| Sous-positions liées à la LF 2026 (JO n°88) | 46 |
| DD non publiés par la source (`source_gaps`) | 299 sous-positions / 296 HS6 |
| TVA non publiée par la source | 460 sous-positions |
| Taxes présentes : DD | 16 816 lignes |
| Taxes présentes : TVA | 16 655 · PRCT 17 115 · TCS 17 115 · DAPS 921 · TIC 228 |
| Fichier canonique HS6 | 5 533 lignes ; 5 237 avec DD (plage 5–60%) ; **0 incohérence** avec les sous-positions |

Chaque sous-position porte désormais : `source_url`, `crawled_at`, `date_consulted`, `source_quality`, `source_gaps` (blocs de taxes absents de la page source), formalités rapprochées de la liste F.A.P officielle (`MATCHED_DGD_FAP_LIST` ou `UNMATCHED_VERBATIM`), provisions LF 2026 (`lf2026_provisions`) et références légales (`legal_refs`).

## 3. Sources officielles archivées (SHA-256 dans `_manifest.json`)

| Document | Rôle |
|---|---|
| JO n° 88 du 31/12/2025 — **Loi de finances 2026** (douane.gov.dz) | Articles douaniers 120–143 : exemptions et taux réduits par sous-position |
| **Tarif Douanier d'usage** (DGD, éd. LF 2020) + Annexes | Nomenclature taxes (DD 0/5/15/30/60 ; TVA 0/9/19) et liste F.A.P avec autorités |
| Code des douanes — **loi 79-07** (modifiée) | Base légale douanière |
| Notes DGD 559/2023 et 4121/2024 + tables de corrélation | Amendements de structure du tarif (éclatements SPT « Autres ») |

Extractions JSON : `dgd_tax_codes_and_fap.json` (verbatim), `lf2026_customs_articles.json` (verbatim), `crosscheck_dgd_2020_vs_crawl.json` (croisement).

## 4. Vérifications et conflits documentés (non arbitrés)

1. **Concordance ancien/nouveau crawl** : 6 240 positions ch.29+ identiques à 100% (taux) → les données « crawl 2026-06-17 » étaient authentiques ; les lignes fautives venaient de l'ETL appliqué aux ch.01-28.
2. **Croisement Tarif d'usage DGD 2020 ↔ crawl** : 898 lignes comparables → **848 concordantes**, 30 absentes du portail (codes restructurés en 2023/2024), 20 divergences.
3. **Les 20 divergences — RÉSOLUES le 2026-08-29 par lecture des textes** : kits CKD « Collections pour industries de montage » (87.03) — Tarif imprimé 2020 : DD « ex » + TVA 9% ; source live 2026 : pas de bloc DD + TVA 19%. **Chaîne légale établie** :
   - **LFC 2020** (loi n° 20-07 du 4 juin 2020, JO n° 33 du 04/06/2020), **art. 60** : ensembles, sous-ensembles et accessoires importés séparément ou groupés → **DD 5% + TVA 19%** (opérateurs agréés, cahier des charges, décision d'évaluation technique du ministère chargé de l'industrie) ; matières premières → exemption DD+TVA ;
   - **LF 2021** (loi 20-19, JO n° 83 du 31/12/2020), **art. 149** : kits SKD/CKD exemptés DD+TVA uniquement pour les EPIC du secteur ANP et leurs partenariats majoritaires ; **art. 150** : note complémentaire chapitres 73/84/85/87 (admission subordonnée aux conditions réglementaires + fiche du ministère chargé de l'industrie) ;
   - **LF 2022→2026** : aucune modification de l'art. 60 LFC 2020 (vérifié sur les 5 textes).
   → **TVA 19% est le taux en vigueur** ; le 9% du tarif imprimé 2020 est antérieur à la LFC 2020. La source live est cohérente. Les régimes dérogatoires (exonérations conditionnelles) ne modifient pas le taux générique de la ligne. Détail : `crosscheck_dgd_2020_vs_crawl.json`.
4. **DD absents (299)** : la page source ne publie aucun bloc DD (blé de semence, vaccins, matériel médical, or monétaire, aéronefs, œuvres d'art...). Enregistré comme `source_gaps: ["DD"]` — **pas** interprété comme « exonéré ».
5. **Libellés PRCT/TCS** : codes absents de la liste officielle des abréviations (Tarif d'usage 2020) et de la LF 2026 → statut `UNVERIFIED_LABEL`, libellés conservés tels que publiés par la source.
6. JORADP (joradp.dz) inaccessible en recherche programmatique depuis ce réseau — vérification JO restée partielle (LF 2026 couverte via le PDF officiel de douane.gov.dz).

## 5. Provenance des fichiers

| Fichier | Statut | sha256 (tronqué) |
|---|---|---|
| `backend/data/crawled/DZA_tariffs.json` | reconstruit 2026-08-29 | bba159c9fb60e713 |
| `backend/data/DZA_tariffs.json` (canonique HS6) | régénéré 2026-08-29 | (voir `_manifest` backups) |
| Backups | `data/archive/crawled_backup/DZA_tariffs_20260829T*.json`, `DZA_canonical_hs6_20260829T112605Z.json` | |
| Rapport machine | `reports/DZA_REBUILD_RECONCILIATION.json` | |

## 6. Limites et actions restantes

- ~~Conflits TVA kits CKD~~ : **résolus** (art. 60 LFC 2020 + LF 2021 art. 149-150 ; aucune modification ultérieure). PDFs archivés : `JO_2020-33_lfc2020_loi_20-07.pdf`, `JO_2020-83_loi_finances_2021.pdf`, plus LF 2020/2022/2023/2024/2025/2026 (15 documents au total dans `_manifest.json`).
- ~~30 codes du Tarif imprimé 2020 absents du portail~~ : **tous expliqués** le 2026-08-29 — 4 par les éclatements nationaux DGD 2023/2024 (cités dans les tables de corrélation archivées : 8413.82, 8450.90.90, 8529.90.92, 8542.39.00) et 26 par la transition SH2017→SH2022 (successeurs SH2022 vérifiés sur le portail : 8517.13/14, 8517.71/77/79, 8519.81/89, 8525.81-83/89, 8541.42/43, 8541.51/59, 8543.70). Détail par code : `crosscheck_dgd_2020_vs_crawl.json` → `absent_from_crawl_analysis`.
- La correspondance formalités ↔ F.A.P est exacte uniquement (1 082 correspondances) ; les 19 641 textes non appariés restent verbatim (toute correspondance floue serait interprétative).
- ~~Références FTA~~ : **ZLECAf consolidée** le 2026-08-29 — **loi n° 20-10 du 22 octobre 2020** portant approbation de l'Accord ZLECAf (signé à Kigali, 21 mars 2018), JO n° 80 du 29/12/2020 p. 4, texte extrait verbatim (`JO_2020-80_ratification_zlecaf.pdf` + `fta_legal_refs.json`). Les avantages ZLECAf crawlés par sous-position (« Certificat d'origine dans le cadre -zale- exo d.d ») s'appuient sur cet accord approuvé. Les références JO des conventions bilatérales (algéro-jordanienne, algéro-tunisienne, ZALE) restent à consolider — avantages conservés verbatim.
