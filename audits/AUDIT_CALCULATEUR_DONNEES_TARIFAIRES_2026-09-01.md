# AUDIT DU MODULE CALCULATEUR & DES DONNÉES TARIFAIRES — 2026-09-01

Périmètre : module calculateur, authenticité/précision des fichiers tarifs africains (sous-positions 8–10 chiffres), intitulés exacts des droits et taxes, méthodes de calcul, formalités/documents/autorités, avantages fiscaux FTA, bases légales, traçabilité, sécurisation crypto.

Environnements audités : local (branche `feat/tarifs-africains-authentiques`), GitHub `aouggad-web/afcfta-final-002`, preview Emergent `https://commerce-viewer.preview.emergentagent.com`.

---

## 1. ÉTAT DES TROIS ENVIRONNEMENTS

| Environnement | État |
|---|---|
| **Local** | Branche `feat/tarifs-africains-authentiques`, **21 commits devant `main`** (re-crawl TUN Tarif Web 2026 : 17 542 codes, réconciliation 492 changements documentés ; corpus JORT SHA-256 ; canonique TUN 219 845 préférences zonées). Changements non commités liés au module production/FAOSTAT (hors périmètre tarifs). |
| **GitHub** | Repo public, 3 603 commits, **12 PRs ouvertes** ; la branche des tarifs authentiques est poussée mais **non fusionnée dans main** (main local en retard de 525 commits). |
| **Preview Emergent** | API en ligne (`/api/health` healthy), mais sert les données du **16 juin 2026** — le re-crawl TUN d'août 2026 n'y est **pas déployé**. |

**Verdict 1** : la donnée la plus fraîche et la plus fiable est locale, sur une branche non fusionnée et non déployée. Le preview a ~2 mois de retard.

---

## 2. AUTHENTICITÉ DES FICHIERS PAYS — 54 PAYS

Statistiques mesurées sur `backend/data/*_tariffs.json` (fichiers servis, vérifiés aussi sur le preview) :

| Statut | Pays | Nb | Nature |
|---|---|---|---|
| **Authentique** (VERIFIED/A ou CRAWLED_AUTHENTIC) | DZA, EGY, ETH, MAR, MUS, TUN | **6/54** | Crawl national officiel, sous-positions nationales réelles 8–11 chiffres |
| **Partiel** (PARTIAL/B) | 34 pays (blocs EAC, CEDEAO/TEC, CEMAC, SACU…) | **34/54** | Tarif Extérieur Commun régional répliqué par pays — codes réels du TEC mais **pas de nomenclature nationale propre** |
| **SYNTHÉTIQUE** (format `enhanced_v2`, aucun statut) | AGO, COM, DJI, ERI, LBY, MDG, MOZ, MRT, MWI, SDN, STP, SYC, ZMB, ZWE | **14/54** | **Sous-positions 10 chiffres GÉNÉRÉES par template** : `source: "Nomenclature nationale AGO (type: use)"`, ~16 141 sous-positions par pays (toutes identiques), libellés génériques (« Usage spécifique », « Autre usage ») |

### 🔴 Constat critique n°1 — violation de la doctrine en production
Les 14 pays synthétiques sont **servis en production** sur le preview (vérifié : `GET /api/authentic-tariffs/country/AGO/sub-positions/010121` → `0101210010 « (type: use) »`). Ceci viole directement la doctrine du README (« refuser les lignes estimées, synthétiques, générées ou répliquées par chapitre ») et le manifeste de crawl (`ESTIMATED` = rejeté). `crawl_all_countries.py --validate-file` les rejetterait, mais le chemin de service (fallback ETL → PostgreSQL) ne passe pas par cette validation.

### Précision des codes (pays authentiques)
- **DZA** : 17 115 sous-positions **10 chiffres** (source DGD douane.gov.dz)
- **EGY** : 8 746 sous-positions **10 chiffres** (customs.gov.eg)
- **TUN** : 17 512 sous-positions **11 chiffres** (Tarif Web douane.gov.tn — réel, l'11e chiffre est un variant national)
- **ZAF** : 4 260 sous-positions **8 chiffres** mais **seulement 1 291/5 619 lignes couvertes** (SARS Part 1)
- **KEN** : 5 984 sous-positions **8 chiffres** (EAC CET 2022)

### 🔴 Constat critique n°2 — divergence DZA
Deux copies concurrentes : `backend/data/DZA_tariffs.json` (29/08/2026, CRAWLED_AUTHENTIC, sha256 `423e84c3…`) ≠ `backend/data/tariffs/DZA_tariffs.json` (16/06/2026, VERIFIED, sha256 `d2ea15d5…`). Le rapport de réconciliation local indique **16 922 positions en conflit** (sur 17 115) à revoir entre canonique et crawl. Risque : selon le chemin de chargement, deux taux différents pour le même code.

---

## 3. DROITS & TAXES — INTITULÉS, TAUX, MÉTHODES DE CALCUL

**Points forts** :
- Moteur cascade déterministe (`engine/calculation.py`, `backend/services/tax_computation.py`) : résolution itérative des assiettes déclarées (« CIF + DAPS + DD », « VAL.DOU(D)+R(DT) GR.0 »), plafonds (ex. RI plafond 15 000 XAF CEMAC), journal de calcul étape par étape avec références légales.
- Types de taux gérés : ad valorem, spécifique, mixte, alternatif (ex. EAC « 75 % ou $345/MT le plus élevé »), exonération.
- Profils fiscaux par pays avec citations légales (DZA art. 21 CTCA + Circ. 419 DGD ; MAR CGI art. 96 ; GHA VAT Act 870 ; NGA VAITA s.2 ; ZAF VAT Act s.13(2) ; CEMAC directive art. 9).
- Vérifié sur le preview : calcul DZA 010121 NPF/ZLECAf correct (DD 5 % → 0 % ZLECAf liste A 2026, cascade TVA base CIF+DAPS+DD, PRCT 2 %), `cascade_legal_source` citée.

**Points faibles** :
- `taxes_detail` du format servi `canonical_v4` : `observation` parfois réduit au sigle (« TCS », « PRCT ») au lieu de l'intitulé légal complet ; l'intitulé complet n'est garanti que dans les fichiers crawlés (labels DGD « MATCHED_DGD_LIST », désignations TUN, texte officiel arabe EGY).
- **3 moteurs de calcul coexistent** et peuvent diverger : `postgres_tariff_service.calculate_tariffs()` (modèle simplifié valeur×taux), cascade `tax_computation.py`, et `enhanced_calculator_service.py`. Selon la route/source, le résultat peut différer. L'agrégation HS6 par `AVG(total_npf_pct)` en PG est une approximation.
- Ordre de cascade DZA incohérent entre moteurs (Circ. 419 : DD→TCS→PRCT→TVA avec TVA base CIF+DD+TCS+PRCT ; le preview applique TVA base CIF+DAPS+DD puis PRCT après TVA).

---

## 4. FORMALITÉS, DOCUMENTS, AUTORITÉS DÉLIVRANTES

- Les formalités administratives par sous-position existent (`administrative_formalities[]` : code + intitulé du document), héritées des régimes nationaux crawlés (ex. DZA : « Dérogation sanitaire vétérinaire », « Visa de contrôle sanitaire vétérinaire »).
- **Faiblesse** : l'autorité délivrante est **embarquée dans le texte libre** — « (m. agriculture) » — et non dans un champ structuré. Le schéma v4 (`requirements.issuing_authority`) et la table PostgreSQL `requirements(issuing_authority)` existent, mais le JSON servi ne les alimente pas.
- Granularité : les formalités sont attachées à la **ligne HS6**, pas à chaque sous-position 10 chiffres (les réglementations nationales les publient par position tarifaire).

## 5. AVANTAGES FISCAUX / FTA

- **Solide** pour DZA : calendrier de démantèlement authentique (Circulaire DGD n°482 du 22/10/2024, listes A/B/C HS10, taux de base 2019 gelés, 9 partenaires actifs, DAPS éliminé pour listes A/B, positions gelées textiles/véhicules → NPF). ZAF : 14 partenaires actifs (dtic/SARS).
- `fiscal_advantages[]` par ligne avec conditions sourcées (convention algéro-jordanienne, ZALE, ZALE/ZLECAf/UE/AELE + bilatéraux TUN — 219 845 préférences zonées).
- Choix d'honnêteté correct : MAR exclu des implémenteurs actifs (contradiction de sources tralac vs douane.gov.ma) → préférences ZLECAf non appliquées vers MAR avec note explicative.
- **Faiblesse** : pour la majorité des pays, `zlecaf_rate` provient du **canevas générique Annexe 1 PCM** (`backend/etl/afcfta_schedule.py`), pas d'offres nationales vérifiées ; `zlecaf_source` = « ZLECAf » sans URL.

## 6. BASES LÉGALES, TRAÇABILITÉ, CRYPTO

**Traçabilité — bonnes bases** :
- Modèle `Provenance` v4 (data_status VERIFIED/PARTIAL/SYNTHETIC, fiabilité A–D, source_url, disclaimer légal obligatoire si non-VERIFIED).
- Échelle de provenance du manifeste crawl : NATIONAL_CRAWL(4) > REGIONAL_CET(3) > WTO_MFN_HS6(2) > ESTIMATED(1, rejeté).
- Registres SHA-256 des documents sources archivés (JORT 2010–2026, PDFs SARS, Kenya legal_sources, corpus WCO).
- `--validate-file` : rejette source/source_url manquants, positions estimées/synthétiques, fichiers vides, et détecte les écema d'ingestion.

**🔴 Constat critique n°3 — aucune sécurité cryptographique de bout en bout** :
- Les SHA-256 enregistrés (manifestes, registres, `data/coverage/*_documentation_status.json`) **ne sont jamais re-vérifiés au chargement des données** — aucune fonction de vérification d'intégrité dans `authentic_tariff_service`, `crawled_data_service`, `postgres_tariff_service`.
- Aucune signature numérique, aucun HMAC, aucune chaîne d'intégrité source→fichier→API. Une altération de fichier entre l'audit et le service serait invisible.
- Pas de provenance par ligne dans les JSON servis (uniquement au niveau `summary`) ; pas de versioning horodaté des fichiers (seul `generated_at`).
- Auth API correcte par ailleurs (clés hachées SHA-256, `_validate_iso3` anti-path-traversal).

---

## 7. RECOMMANDATIONS PRIORITAIRES

| # | Priorité | Action |
|---|---|---|
| 1 | **P0** | Retirer du service les 14 fichiers `enhanced_v2` synthétiques (AGO, COM, DJI, ERI, LBY, MDG, MOZ, MRT, MWI, SDN, STP, SYC, ZMB, ZWE) ; les remplacer par une réponse explicite « pays non encore recrawlé » conformément à la doctrine. Vider aussi les lignes correspondantes de PostgreSQL si migrées. |
| 2 | **P0** | Unifier les 2 fichiers DZA (supprimer la copie de `backend/data/tariffs/` ou en faire un alias versionné) ; résoudre les 16 922 conflits de réconciliation canonique↔crawl. |
| 3 | **P1** | Intégrité runtime : manifeste SHA-256 par fichier pays, vérifié au chargement (et idéalement signature HMAC/ed25519 du manifeste) ; refuser le service si hash ≠ manifeste. |
| 4 | **P1** | Ajouter la provenance **par ligne** (data_status, source_name, source_url, legal_basis) dans le format servi + colonnes correspondantes en PostgreSQL ; intitulés légaux complets dans `taxes_detail[].observation`. |
| 5 | **P1** | Structurer `issuing_authority` des formalités (champ dédié alimenté depuis les réglementations crawlées, ex. « Ministère de l'Agriculture — Services vétérinaires »). |
| 6 | **P1** | Passer `--validate-file` en **gate obligatoire du déploiement** (CI GitHub Action) : aucun fichier pays servi sans validation verte. |
| 7 | **P2** | Unifier les 3 moteurs de calcul : route unique → moteur cascade avec assiettes légales ; déprécier le calcul simplifié de `postgres_tariff_service`. |
| 8 | **P2** | Fusionner la PR `feat/tarifs-africains-authentiques` (re-crawl TUN août 2026) et redéployer le preview. |
| 9 | **P2** | Re-crawl national des 34 pays PARTIAL (nomenclatures 8–10 chiffres propres, au-delà des TEC régionaux) ; compléter ZAF 8 chiffres (4 329 lignes manquantes). |
| 10 | **P3** | Aligner l'ordre de cascade DZA sur la Circulaire 419 dans tous les moteurs (TVA base CIF+DD+TCS+PRCT) et documenter la divergence éventuelle avec l'application réelle DGD. |

---

## 8. SYNTHÈSE

Le socle est solide : moteur de calcul cascade avec assiettes légales résolues, journal de calcul, doctrine d'authenticité, validateur de fichiers et registres SHA-256 des sources. **6 pays sur 54 sont réellement authentiques à la précision nationale 8–11 chiffres** ; 34 servent un TEC régional honnête mais approximé au niveau national ; **14 pays servent des données synthétiques en production, ce qui est le non-respect le plus grave de la doctrine du projet**, et l'intégrité des fichiers n'est protégée par aucune vérification cryptographique au runtime.

---

## 9. MISE EN ŒUVRE (2026-09-01) — P0 + DIRECTIVES

### 9.1 P0-1 — Gate doctrine implémenté

- **`backend/services/tariff_doctrine.py`** (nouveau) : contrôle unique de servabilité
  (`data_format == canonical_v4` + `data_status ∈ {VERIFIED, PARTIAL, CRAWLED_AUTHENTIC}` +
  `source_name`/`source_url` obligatoires), message FR/EN explicite `COUNTRY_NOT_RECRALLED`,
  marquage des frais de prestataires (`provider_fee_flags`).
- Gate appliqué à : `authentic_tariff_service.load_country_tariffs` (refus au chargement),
  facade `tariff_provider_service` (**avant PostgreSQL** — bloque la donnée migrée éventuelle),
  routes `/authentic-tariffs/*` (404 explicite doctrine), route legacy `/calculate-tariff`.
- **14 fichiers synthétiques archivés** (`backend/data/archive/synthetic_enhanced_v2/`,
  des deux répertoires de service, avec README documentant la décision). Ces pays restent
  servis honnêtement au niveau HS6 MFN via les données crawlées WITS/UNCTAD-TRAINS.
- Correction d'un bug bloquant préexistant : 3 scripts de crawl TUN exécutaient
  `asyncio.run(main())` **au niveau module** → chaque import du backend lançait un crawl
  live de douane.gov.tn (import routes > 4 min → 7,9 s après guard `if __name__`).

### 9.2 P0-2 — Unification DZA

- Copie périmée juin 2026 archivée (`backend/data/archive/superseded/`) ; le fichier
  racine août 2026 (CRAWLED_AUTHENTIC) est la source unique de vérité.
- **Arbitrage par la source gouvernementale** : les codes en conflit (ex. `2930100000` :
  juin 5 % vs août 15 %) vérifiés en direct sur conformepro.dz (données DGD douane.gov.dz)
  → **15 % officiel : le fichier d'août est correct**, la copie juin était erronée.
- `summary.source_url` complété sur le fichier DZA (exigence doctrine), format indent=2 préservé.

### 9.3 Directives : import/export par pays + prestataires

- **`backend/services/export_tariff_service.py`** (nouveau) : cascade de calcul à
  l'**export** par pays, sur les données officielles crawlées, avec résolution des
  assiettes officielles déclarées (« SOMME D.T », « VALEUR DOUANE DINARS », « PN (KG) »,
  « QCS ») et droits spécifiques (ex. TUN : taxe ferrailles 0,3 dinars/kg).
- **Registre des prestataires délégataires de missions régaliennes**
  (`backend/data/customs_providers/providers_registry.json`) : prestataire, missions
  déléguées, codes de redevance, **payeur (État ou opérateurs économiques)**, base légale,
  URL — uniquement des entrées vérifiées (TUN : redevances de prestations douanières
  RPD/IMPOR + RPD/EXPOR, payées par les opérateurs économiques, source douane.gov.tn) ;
  les autres pays restent explicitement « A_DOCUMENTER » (doctrine).
- Nouvelles routes : `GET/POST /authentic-tariffs/export-calculate`,
  `GET /authentic-tariffs/country/{iso3}/export-taxes/{hs_code}`,
  `GET /authentic-tariffs/country/{iso3}/tariff-system`.
- Frais de prestataires marqués `is_provider_fee` dans les réponses (import et export).

### 9.4 Vérification pays par pays contre les sources gouvernementales

Harnais : `backend/scripts/verify_government_sources.py` (relit la source officielle
avec les parseurs de production et compare ligne à ligne). Rapports dans
`data/coverage/verification_gouvernementale/` :

| Pays | Source gouvernementale | Échantillon | Résultat |
|---|---|---|---|
| **TUN** | douane.gov.tn (Tarif Web) | 6 | **6/6 conformes** (DD ligne à ligne, codes export aussi) |
| **DZA** | conformepro.dz (données DGD douane.gov.dz) | 4 dont 2 codes en conflit | **4/4 conformes** — conflits arbitrés en faveur du fichier d'août |
| **EGY** | customs.gov.eg (Tarif officiel JSON) | 5 | **5/5 conformes** (DD « ضريبة الوارد », VAT, instructions FTA) |
| **MAR** | douane.gov.ma/adil | 4 | **Source injoignable depuis cet environnement** (rapport honnête, à reprogrammer depuis l'environnement de crawl) |

Écart de source détecté à corriger : **MUS** — le fichier crawlé est sourcé
WITS/UNCTAD-TRAINS (Banque mondiale) alors que le fichier canonique revendique
« MRA Integrated Tariff Schedule » : à vérifier contre l'autorité mauricienne avant
de maintenir le statut VERIFIED.

### 9.5 Tests

`backend/tests/test_tariff_doctrine.py` — **23 tests verts** : gate doctrine
(refus synthétique, acceptation conforme, statuts par pays), unicité DZA, blocage
facade même avec PostgreSQL, messages explicites de routes, taxes export TUN
(ad valorem dattes 1 %, spécifique ferrailles dinars/kg, assiettes officielles),
registre prestataires (payeur, entrées non vérifiées jamais servies). Non-régression :
les 50 échecs préexistants du jeu lié sont identiques à la baseline HEAD (vérifiée
via worktree git) ; 2 tests SDN/STP passent en skip (fichiers synthétiques retirés —
comportement doctrine attendu).
