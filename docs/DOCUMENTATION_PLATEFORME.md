# Documentation complète de la plateforme — Calculateur Commercial ZLECAf / AfCFTA

> Document de référence technique de la plateforme.
> Repo : `aouggad-web/afcfta-final-002` — Version applicative : 3.0.0 (backend), 2.0.0 (README historique).
> Dernière mise à jour de ce document : 2026-06-18.

Ce document décrit l'intégralité de la plateforme : architecture, backend (API FastAPI),
frontend (React), pipeline de données/crawling/ETL, moteur de calcul tarifaire, règles
d'origine ZLECAf, et l'état connu du projet. Il sert de point d'entrée unique pour
comprendre le système.

---

## 1. Vue d'ensemble

La plateforme est un **calculateur de droits de douane et système d'information commerciale**
pour la **Zone de Libre-Échange Continentale Africaine (ZLECAf / AfCFTA)**, couvrant les
54 États membres de l'Union africaine.

Fonctions principales :
- **Calcul tarifaire** entre pays africains : taux NPF (droit commun) vs taux préférentiel ZLECAf, avec ventilation complète des taxes (DD, TVA, taxes parafiscales) en cascade.
- **Règles d'origine** ZLECAf par code SH (Annexe 2 + Appendice IV de l'Accord).
- **Profils pays** : données économiques, commerciales, de production et logistiques.
- **Statistiques commerciales** (OEC, COMTRADE, UNCTAD), opportunités de substitution aux importations, logistique multimodale, banque/finance commerciale.
- **Données tarifaires authentiques** crawlées depuis les portails douaniers nationaux, avec un modèle strict de provenance/authenticité (jamais de donnée fabriquée servie comme réelle).

Principe directeur du projet : **« rien que de l'authentique avec sources »** — la donnée
tarifaire servie doit provenir d'une source officielle traçable, sinon elle est dégradée
explicitement (« pas de donnée ») plutôt que fabriquée.

---

## 2. Stack technique

| Couche | Technologie |
|--------|-------------|
| Backend | **FastAPI** (Python 3.11), Uvicorn (ASGI) |
| Bases de données | **MongoDB** (Motor async — historique, analytics, clés API) + **PostgreSQL** (SQLAlchemy — devises, taux de change, source tarifaire canonique « postgres-first ») |
| Frontend | **React 19** (Create React App + Craco), **Radix UI** + **Shadcn/ui**, **Tailwind CSS** |
| Visualisation | Recharts (graphiques), React-Leaflet (cartes) |
| i18n | i18next / react-i18next — bilingue **FR/EN** (défaut FR) |
| HTTP client (front) | axios (intercepteur rejetant les réponses HTML) |
| APIs externes | World Bank, OEC.world, WTO (WITS/TRAINS), FAOSTAT, UNCTAD, Google Gemini (optionnel) |
| Notifications | Email (SMTP) + Slack (webhooks) |
| Déploiement | Docker / docker-compose ; GitHub Actions pour la mise à jour quotidienne des données |

---

## 3. Architecture générale

```
                    ┌──────────────────────────────────────────────┐
                    │           Frontend React (SPA, 10 onglets)     │
                    │  Calculateur · Profils · Stats · Règles ·      │
                    │  Opportunités · Logistique · Banque · Outils   │
                    └───────────────────────┬──────────────────────┘
                                            │  HTTP /api (axios, REACT_APP_BACKEND_URL)
                    ┌───────────────────────▼──────────────────────┐
                    │              Backend FastAPI (/api)            │
                    │  Auth par clé API · CORS · CSRF · Rate-limit   │
                    │  ~40 routers (calculator, authentic_tariffs,   │
                    │  rules_of_origin, dismantlement, statistics…)  │
                    └──────┬───────────────────────────┬────────────┘
                           │                           │
              ┌────────────▼─────────┐      ┌───────────▼───────────────┐
              │  Services tarifaires  │      │  Bases de données          │
              │  (priorité postgres-  │      │  MongoDB · PostgreSQL      │
              │   first puis legacy)  │      └────────────────────────────┘
              └────────────┬─────────┘
                           │ lit
              ┌────────────▼───────────────────────────────────────────┐
              │  Données tarifaires (backend/data/)                      │
              │  crawled/{ISO3}_tariffs.json · tariffs/ · zlecaf_*.json  │
              │  Validées par tariff_crawl/canonical.py (authenticité)   │
              └────────────▲───────────────────────────────────────────┘
                           │ alimente
              ┌────────────┴─────────┐      ┌────────────────────────────┐
              │  Crawlers (Python     │      │  Moteur ETL/canonisation    │
              │  async, 54 pays)      │      │  engine/ + backend/etl/     │
              └───────────────────────┘      └────────────────────────────┘
```

---

## 4. Backend

### 4.1 Point d'entrée — `backend/server.py`

- Application FastAPI, titre « Système Commercial ZLECAf - API Complète » (v3.0.0). Entrée ASGI : `server:app`.
- Charge `.env` **avant** d'importer les modules (pour que `auth.py` lise `SECRET_KEY` à temps).
- **Middleware** : CORS (origines via `ALLOWED_ORIGINS`), `SecurityHeadersMiddleware` (CSP), `CSRFMiddleware` (exempte `/api/health`, `/api/crawl`, `/api/tariff-data/collect`), `RateLimitMiddleware` (120 req/min, burst 20). Logging structuré ISO.
- **MongoDB** (Motor) : `MONGO_URL` optionnel, pool 5–50 connexions ; indexe au démarrage `customs_data`, `tariff_lines`, `api_keys`.
- **PostgreSQL** (optionnel) : `POSTGRES_URL`, source tarifaire canonique « postgres-first ».
- **Auth par clé API** (`auth.py`) : header `X-API-Key`, hachage SHA-256 stocké en collection `api_keys`, deux niveaux (`require_auth`, `require_admin`). **Fallback** : si MongoDB indisponible, toutes les requêtes passent en `{"tier":"public","no_db":True}` (pratique en local/tests).
- **Démarrage** : indexes DB, injection de la DB dans `auth`/`calculator`, chargement du service de données crawlées, du service ETL, du scheduler de taux de change (toutes les 4h), de l'orchestrateur de crawl.

> ⚠️ **Problème connu (environnement)** : `server.py` importe `motor.motor_asyncio`, qui échoue actuellement avec `ImportError: cannot import name '_QUERY_OPTIONS' from 'pymongo.cursor'` (incompatibilité de versions motor/pymongo). **Conséquence** : le serveur ne démarre pas tel quel dans ce sandbox, et les tests d'intégration qui requièrent un serveur live (`test_rules_of_origin.py`, `test_smart_search_chapters.py`) ne peuvent pas s'exécuter ici. À corriger en alignant les versions `motor`/`pymongo` dans `requirements.txt`.

### 4.2 Routage — `backend/routes/__init__.py`

Tous les routers sont montés sous le préfixe **`/api`**. `/api/health` est public ; tout le reste exige une clé API valide (sauf mode no-DB). Routers principaux :

| Module | Préfixe | Rôle |
|--------|---------|------|
| `health.py` | `/health` | Santé / statut (public) |
| `calculator.py` | `/calculate-tariff` | **Calculateur tarifaire principal** (POST) |
| `authentic_tariffs.py` | `/authentic-tariffs` | Données tarifaires officielles par pays (résumé, ligne, sous-positions, calcul) |
| `tariffs_calculation.py` | `/tariffs` | Utilitaires de calcul (taux chapitre, TVA…) |
| `rules_of_origin.py` | `/rules-of-origin` | Règles d'origine ZLECAf (Appendice IV) par code SH |
| `dismantlement.py` | `/dismantlement` | Calendrier de démantèlement ZLECAf par pays |
| `hs6_database.py` | `/hs6` | Recherche SH6 (moteur de scoring texte/préfixe) |
| `countries.py` | `/countries` | Profils pays & données économiques |
| `statistics.py` | `/statistics` | Analytique commerciale |
| `oec.py` | `/oec` | Statistiques commerciales OEC |
| `production.py`, `logistics.py`, `banking.py`, `substitution.py`, `ai_intelligence.py`, `regional_analytics.py`, `news.py`, `exchange_rates.py`, `currencies.py`, `etl.py`, `crawl.py`, `tariff_data.py`… | divers | Production, logistique multimodale, banque/finance, substitution aux imports, IA, analytique régionale, actualités, devises/FX, administration ETL/crawl. (~40 routers au total, beaucoup montés conditionnellement selon les imports disponibles.) |

### 4.3 Pipeline de calcul tarifaire — `POST /api/calculate-tariff`

Fichier central : `backend/routes/calculator.py`. Déroulé :

1. **Validation des pays** : `origin_country` / `destination_country` (ISO2 ou ISO3), recherche dans `AFRICAN_COUNTRIES` ; HTTP 400 si hors ZLECAf.
2. **Normalisation du code SH** : nettoyage (points/espaces), extraction SH6 (6 premiers chiffres), code secteur (2 chiffres).
3. **Priorité des sources de données (3 niveaux)** :
   - **Priorité 1 — `crawled_authentic`** : `crawled_service.lookup(dest_iso3, hs_code_clean)` → position nationale complète (taxes, avantages fiscaux, formalités, source). Précision : `national_position` (la plus fine).
   - **Priorité 2 — `collected_verified`** : `tariff_service.get_tariff_precision_info(...)` → taux + source + précision (sous-position / hs6_country / chapitre).
   - **Priorité 3 — `etl_fallback`** : modules ETL (`get_sub_position_rate`, `get_country_hs6_tariff`, `get_tariff_rate_for_country`). Toujours disponible.
   Chaque niveau renseigne `data_source`, `tariff_precision`, `confidence_level` pour la traçabilité.
4. **Extraction des taux** : NPF (droit de douane DD/DI), TVA, autres taxes (redevance statistique, prélèvements communautaires…).
5. **Taux préférentiel ZLECAf** :
   - Méthode générique (tous pays sauf DZA) : `zlecaf_rate = normal_rate × facteur_de_réduction` via `get_zlecaf_reduction_factor(dest_iso3, catégorie_produit)`.
   - **Override Algérie (DZA)** : `compute_dza_zlecaf_rate()` (voir §7) remplace le facteur générique par le calendrier authentique de la circulaire DGD 482/2024.
6. **Ventilation complète des taxes** : `backend/services/tax_computation.py` — moteur pur (sans I/O) qui calcule en cascade les bases (CIF, CIF+DD, …), résout itérativement les dépendances (la TVA dépend du DD déjà calculé), applique les plafonds, et produit `taxes_breakdown` + `taxes_summary` sous les deux régimes (NPF vs ZLECAf), avec économies.
7. **Localisation multidevise** : conversion des montants USD → devise locale du pays (services `currencies` + `exchange_rates`) ; dégradation propre si le taux FX est indisponible.
8. **Enrichissement règles d'origine** : `etl/afcfta_rules_of_origin.get_rule_of_origin(hs6, "fr")` (voir §6).
9. **Données complémentaires** : top producteurs africains (OEC), données économiques (World Bank), variations de sous-positions + avertissement de taux variable.

Réponse : modèle Pydantic `TariffCalculationResponse` (`backend/models.py`) — identifiants, taux & montants NPF, taux & montants ZLECAf, économies, **journaux de calcul** pas-à-pas (avec références légales), traçabilité (`data_source`, `tariff_precision`, `confidence_level`), tableau de taxes, bloc devise, règles d'origine, top producteurs, données pays.

### 4.4 Couche services (`backend/services/`)

| Service | Rôle |
|---------|------|
| `tariff_provider_service.py` | **Façade postgres-first** : tente PostgreSQL puis bascule sur le service authentique (legacy). |
| `postgres_tariff_service.py` | Accès SQLAlchemy aux tables tarifaires PostgreSQL (`get_countries`, `get_tariff_line`, `get_sub_positions`, `get_country_summary`). |
| `authentic_tariff_service.py` | Orchestration multi-sources (postgres / crawled / ETL legacy) ; nomenclature, taxes, avantages, formalités. |
| `crawled_data_service.py` | Singleton lazy-load des fichiers `data/crawled/{ISO3}_tariffs.json` ; normalise les positions ; indexe par code et par SH6. API : `load(force=True)` puis `_ensure_country_loaded(ISO3)` puis `lookup(...)`. |
| `tax_computation.py` | Moteur de ventilation des taxes en cascade (NPF & ZLECAf), plafonds, localisation multidevise. |
| `zlecaf_schedule_dza.py` | Calendrier de démantèlement ZLECAf spécifique à l'Algérie (circulaire DGD 482/2024) — voir §7. |
| `tariff_data_collector.py`, `wto_service.py`, `oec_trade_service.py`, `exchange_rates.py`, `regional_intelligence_service.py`, … | Collecte, intégrations API externes, FX, intelligence régionale. |

### 4.5 Modèle d'authenticité — `backend/tariff_crawl/`

- `manifest.py` définit l'énumération `Provenance` et `AUTHENTIC_PROVENANCES = {NATIONAL_CRAWL, REGIONAL_CET, WTO_MFN_HS6}`. `ESTIMATED`/`NONE` ne sont **pas** authentiques.
- `canonical.py::validate_authenticity(doc)` rejette : document vide, provenance absente/non authentique, ou toute position taguée `etl_computed`/`estimated`/`synthetic`/`generated`/`chapter_replicated` (`NON_AUTHENTIC_QUALITY_TAGS`). `PROVENANCE_SYNONYMS` mappe les alias de crawler (ex. `crawled_authentic` → `national_crawl`).
- `NATIONAL_CRAWL_READY` (portails validés) : **DZA** (conformepro.dz / douane.gov.dz), **EGY** (customs.gov.eg), **MAR** (douane.gov.ma/adil), **TUN** (douane.gov.tn).

---

## 5. Frontend

### 5.1 Stack & build
React 19 via CRA + **Craco** (proxy dev `/api` → `http://localhost:8000`). UI : Radix + Shadcn/ui + Tailwind (thème clair/sombre persistant en `localStorage` `zlecaf_theme`). axios avec intercepteur rejetant le HTML. URL backend via `REACT_APP_BACKEND_URL`. i18n FR/EN (i18next, locales `src/i18n/locales/{fr,en}.json`).

### 5.2 Structure
- Entrée : `frontend/src/index.js` → `App.js`. **Pas de React Router** : navigation par onglets via l'état `activeTab`.
- Onglets : `dashboard`, `calculator`, `statistics`, `opportunities`, `production`, `logistics`, `banking`, `tools`, `rules`, `profiles`.
- Layout : `AfcftaSidebar` (desktop), `AfcftaTopbar` (mobile), `KpiRow`, `SectionHeader`.

### 5.3 Flux clé — le calculateur (`components/calculator/CalculatorTab.jsx`)
Formulaire (origine, destination, code SH 6–12 chiffres, valeur USD). Au calcul :
1. **Priorité 1** : `GET /api/authentic-tariffs/calculate/{destISO3}/{hsCode}?value=…&language=…`
2. **Fallback** : `POST /api/calculate-tariff` (corps `{origin_country, destination_country, hs_code, value, language}`).
Affichage : comparaison NPF vs ZLECAf + économies, ventilation en cascade (valeur → DD → TVA sur CIF+DD → autres taxes), journal de calcul, graphiques (Recharts), calendrier de démantèlement, panneau règles d'origine, comparaison multi-pays, export PDF/Excel. Aides à la sélection SH : `SmartHSSearch`, `HSCodeBrowser`, `ProductKeywordSearch`.

### 5.4 Autres flux
Profils pays (`CountryProfilesTab`), statistiques (OEC/COMTRADE/UNCTAD), règles d'origine (`RulesTab` → `GET /api/rules-of-origin/{hsCode}`), opportunités/substitution, logistique multimodale, banque (FX, trade finance, conformité).

---

## 6. Règles d'origine ZLECAf (Annexe 2 + Appendice IV)

Deux documents officiels font foi (fournis et lus attentivement) :

### 6.1 Annexe 2 — Règles d'origine (texte juridique)
- **Critères conférant l'origine** (art. 4) : (a) **entièrement obtenu** (art. 5) ou (b) **transformation substantielle** (art. 6).
- **Art. 5 — entièrement obtenu** : produits minéraux/végétaux/animaux nés-élevés-récoltés sur le territoire, pêche par « leurs navires » (conditions d'équipage 50%/40%, exception îles), etc.
- **Art. 6 — transformation substantielle** : un des critères — valeur ajoutée, teneur en matières non originaires, changement de position (CTH) / sous-position (CTSH), procédés spécifiques. Les produits de l'**Appendice IV** suivent les règles qui y sont définies.
- **Art. 6A — tolérance** : matières non originaires admises jusqu'à **15% du prix départ usine**, **sauf chapitres 50–63** (textiles).
- **Art. 7 — opérations ne conférant pas l'origine** (de minimis) : conservation, conditionnement simple, étiquetage, mélange simple, montage simple, abattage…
- **Art. 8 — cumul** : tous les États parties = un seul territoire.
- **Preuve d'origine** (art. 17–31) : certificat d'origine (Appendice I) ou déclaration d'origine ; validité 12 mois ; exportateur agréé ; cumul, transport direct, vérification a posteriori (6 mois).
- **Art. 42 — arrangements transitoires** : plusieurs définitions et règles hybrides de l'Appendice IV restent **en suspens** ; en attendant, les règles d'origine des régimes commerciaux existants s'appliquent.

### 6.2 Appendice IV — Règles spécifiques par produit (PSR), COM-12, décembre 2023
Tableau à 3 colonnes : (1) chapitre/position/sous-position SH, (2) désignation, (3) règle conférant l'origine.

**Types de règles rencontrés** :
- **WO** — « Fabrication dans laquelle toutes les matières utilisées doivent être entièrement obtenues » (ex. ch. 1–10, 25, 26, café ch. 9, sucre ch. 17, tabac brut ch. 24).
- **CTH / CTSH / CC** — changement de position / sous-position / chapitre (« à partir de matières de toute position autre que celle du produit »).
- **VA<NN>** — valeur des matières non originaires ≤ NN% du prix départ usine (souvent 60%, parfois 40%/50%), fréquemment assortie d'un **réexamen après 5 ans** ou d'une **phase temporelle** (« 60% pendant 3/5 ans, puis entièrement obtenu »).
- **SP** — procédés spécifiques (ex. raffinage et procédés des positions 27.07–27.13).
- **Règles chimiques (Note 8, ch. 28–38)** : réaction chimique, purification, mélange, changement de taille de particules, séparation d'isomères — alternatives au CTH/VA.
- **Hybrides** : plusieurs alternatives reliées par « Ou ».

**Conventions importantes** :
- Préfixe **« ex »** = la règle ne couvre qu'une partie du chapitre/position.
- Texte entre **`[...]`** ou mention **« À déterminer »** = règle **non encore adoptée** → statut **YTB** (yet to be agreed). Aucun chiffre final ne doit être inventé pour ces lignes.
- Exposants en bas de page = dates d'adoption par le Conseil des Ministres (non normatifs).

**Notes sectorielles** : pétrole (Note 4, procédés spécifiques) ; textiles (Notes 5–7 : définition fibres naturelles, tolérance de poids entre matières textiles de base, doublures) ; chimie (Note 8) ; **véhicules ch. 87 (Note 9)** : définition du montage carrosserie/châssis.

**Constats vérifiés directement dans la source** (exemples) :
- **Café (09) / céréales (10)** : WO. ✔
- **Vêtements ch. 62** : défaut « Fabrication à partir de fils » (**YARN**) ; **mais sous-positions 6203.11/31/41 (costumes en laine) = CTH** (règle propre, réexamen 5 ans). → Le code 620311 relève donc authentiquement de **CTH**, pas du défaut chapitre YARN.
- **Véhicules ch. 87** : 87.01, 87.03–87.08, 87.10–87.12 = **« À déterminer » (YTB)** ; 87.02 (bus) = **VA60**.
- **Textiles** : plusieurs positions 58.01–58.04 bracketées = YTB ; ch. 85 (électrique) = **CTH Ou VA60** de façon récurrente.

> Voir §10 (état connu) pour le statut d'implémentation du moteur de règles d'origine.

---

## 7. Démantèlement tarifaire ZLECAf — cas Algérie (déjà livré)

Module : `backend/services/zlecaf_schedule_dza.py` (+ tests `backend/tests/test_zlecaf_schedule_dza.py`, 17 tests). Source : **circulaire DGD n°482/DGD/SP/D.042/24 du 22/10/2024** et ses listes de concessions (A/B/C).

Points clés (corrige le facteur générique, faux pour l'Algérie) :
- **9 pays partenaires actifs** seulement (ZAF, CMR, EGY, GHA, KEN, MUS, RWA, TZA, TUN) ont déclenché l'application effective ; les autres restent au **droit commun (NPF)** à l'import en Algérie.
- **Listes de produits** : (A) ~90% des lignes, démantelée d'ici 2025/2030 ; (B) 1 163 codes HS10, grâce puis démantèlement ; (C) 456 codes, **exclus** (toujours au droit commun).
- **Deux calendriers** : standard, ou **principe de réciprocité** (13 pays non-PMA appliquant le calendrier PMA) — réduction pluriannuelle plus longue.
- **Positions gelées** (textiles, véhicules) tant que les règles d'origine ne sont pas finalisées → droit commun maintenu.
- **DAPS** (droit additionnel provisoire de sauvegarde) exonéré pour les listes (A)/(B) non gelées des partenaires actifs.

Intégration : override dans `routes/calculator.py` lorsque `dest_iso3 == "DZA"`. **Committé** sur la branche `claude/setup-github-cli-EngUf` (commit `98e0cdc1`).

---

## 8. Données, crawling & ETL

### 8.1 Inventaire
- `./data/` : données de référence statiques (ports, aéroports, corridors terrestres, production, devises, zones franches…).
- `backend/data/crawled/{ISO3}_tariffs.json` : snapshots de crawl. **47 fichiers** présents ; 4 sont des crawls nationaux **authentiques volumineux et validés** (DZA ~26 Mo / 17 061 positions, TUN ~45 Mo, EGY ~19,5 Mo, MAR ~5 Mo) ; plusieurs fichiers volumineux proviennent de sources régionales/templates (à ne pas confondre avec un crawl national validé) ; **~11 fichiers sont des stubs quasi-vides** (~700 octets : AGO, COM, DJI, ERI, MDG, MOZ, MRT, MWI, STP, ZMB, ZWE).
- `backend/data/tariffs/` : versions tarifaires « production ».
- `backend/data/zlecaf_dza/` : `list_b_codes.json` (1 163 codes), `list_c_codes.json` (456 codes) — concessions ZLECAf Algérie.
- `backend/data/zlecaf_rules_of_origin.json` : règles d'origine structurées (96 chapitres + 101 positions + 12 sous-positions) — **fichier nouvellement produit, en cours de finalisation** (voir §10).

### 8.2 Schéma d'une position tarifaire crawlée (DZA, schéma récent)
```json
{
  "hs_code": "0101211100",
  "raw_code": "01.01.211100",
  "heading": "01.01", "chapter": "01",
  "name": "…désignation…",
  "taxes": { "DD": {"name":"Droit de Douane","rate":15.0,"raw":"15%"},
             "TVA": {"rate":19.0}, "TCS": {...}, "PRCT": {...} },
  "advantages": [ {"tax":"D.D","rate":0.0,"condition_fr":"…"} ],
  "formalities": [],
  "source_url": "https://conformepro.dz/…",
  "source_quality": "crawled_authentic"
}
```
(Un schéma plus ancien utilise `taxes_detail` sous forme de liste `{tax, rate, observation}` ; les deux sont normalisés par `crawled_data_service._normalize_dza()`.)

### 8.3 Moteurs ETL/canonisation
- `engine/` (racine) : moteur d'ingestion/canonisation découplé — adaptateurs pays, converters par bloc régional (ECOWAS, CEMAC, EAC, SACU), schéma canonique v4 (provenance, fiabilité A/B/C/D, base du droit, types de mesure, séquence d'application), sortie JSONL.
- `tariff_engine/` (racine) : pipeline legacy PDF→CSV (surtout EAC).
- `backend/etl/` : modules de données — notamment `afcfta_rules_of_origin.py` (règles d'origine), `hs6_database.py`, connecteurs taxes pays (DZA/MAR/TUN), `africa_formalities.py`.
- `backend/crawlers/` : scrapers Python async (httpx, rate-limit, retries), registre 54 pays (`all_countries_registry.py`), `ScraperFactory`.

### 8.4 Automatisation
`.github/workflows/auto_update_data.yml` : rafraîchissement quotidien (cron 02:00 UTC) via `backend/update_data_automated.py` (World Bank, OEC, production), ouvre une PR si changements (jamais de commit direct sans revue). Migrations PostgreSQL dans `./migrations` (devises, taux de change, indexes clés API).

---

## 9. Tests & qualité

- Suite : `backend/tests/` (~36 modules). Lancement : `cd backend && python3 -m pytest tests/`.
- **Tests purs (unitaires, sans I/O), au vert** : `test_tax_computation.py`, `test_zlecaf_schedule_dza.py` (17), `test_tariff_crawl_pipeline.py`, `test_crawled_lookup_hs6.py`, etc.
- **Échecs/erreurs pré-existants connus** (indépendants des travaux récents) :
  - `test_export.py` : **échoue à l'import** (motor/pymongo `_QUERY_OPTIONS`). ⚠️ *(L'agent de doc backend l'a indiqué « PASS » par erreur ; vérification directe : il ne collecte pas.)*
  - `test_rules_of_origin.py`, `test_smart_search_chapters.py` : **tests d'intégration nécessitant un serveur live** (impossible ici car `server.py` ne démarre pas — voir §4.1).
  - `test_north_africa_tariff_system.py` : nombreuses erreurs (event loop async / dépendances).
- Sur l'ensemble (hors `test_export.py`) : ~562 passés / 333 échoués / 17 erreurs — l'essentiel des échecs venant des tests d'intégration non exécutables dans ce sandbox.

---

## 10. État connu, limites et travaux en cours

### Livré et committé (branche `claude/setup-github-cli-EngUf`)
- **Crawl national DZA complet** : `DZA_tariffs.json` fusionné, 17 061 positions authentiques (chap. 01–98 sauf 22, 24 absents à la source, et 77 réservé), validé `✓ AUTHENTIQUE & INGESTIBLE` (commit `a8c88ab2`).
- **Calendrier ZLECAf Algérie** (circulaire DGD 482/2024) : `zlecaf_schedule_dza.py` + override calculateur + 17 tests (commit `98e0cdc1`).

### En cours / non finalisé (changements non committés dans le working tree)
- **Reconstruction du moteur de règles d'origine** : un fichier `backend/data/zlecaf_rules_of_origin.json` (96 ch. / 101 pos. / 12 sous-pos.) a été produit depuis l'Appendice IV, et `routes/rules_of_origin.py` / `constants.py` / `etl/afcfta_rules_of_origin.py` / `routes/__init__.py` modifiés. **Incohérences à corriger avant commit** :
  - Désalignement de noms de champs entre la route et le JSON (la route lit `rule_code`/`threshold_pct`/`rule_text_fr` ; le JSON expose `code`/`threshold`/`raw_fr`).
  - `origin_types` non peuplé (noms de règles bilingues manquants).
  - Pas de matching au niveau **sous-position** (nécessaire pour 620311 = CTH).
  - **Décision actée** : servir le **CTH authentique** pour 620311 et corriger le test `test_rules_of_origin.py` en conséquence (les autres sous-positions du ch. 62 gardent YARN).
- **Décision actée** : finaliser proprement (route ↔ JSON alignés, matching sous-position→position→chapitre, `origin_types` bilingue, câblage `__init__.py`, vérification via un harnais TestClient sans MongoDB), puis commit + push.

### Lacunes de données identifiées
- **Chapitres 22 (boissons) et 24 (tabac)** : absents du crawl tarifaire DZA (les portails .dz renvoient 403 dans ce sandbox ; tentative `curl` + WebFetch infructueuse). À récupérer (upload de pages HTML brutes envisagé). NB : ces chapitres **ont** des règles d'origine dans l'Appendice IV (CTH/VA60), distinctes des taux tarifaires manquants.

### Dette technique
- **Incompatibilité motor/pymongo** bloquant le démarrage du serveur et les tests d'intégration → aligner les versions.
- `routes/__init__.py` contient des blocs de chargement de règles d'origine **dupliqués** (à dédupliquer).
- Nombreux fichiers `crawled/*_tariffs.json` non authentiques (stubs ou templates) à remplacer par des crawls nationaux / CET régionaux validés.

---

## 11. Démarrage rapide (développement)

```bash
# Backend (après correction motor/pymongo)
cd backend && python3 -m uvicorn server:app --reload --port 8000

# Frontend
cd frontend && yarn install && yarn start    # proxy /api -> :8000

# Tests backend (hors intégration nécessitant un serveur)
cd backend && python3 -m pytest tests/ -q --ignore=tests/test_export.py

# Valider l'authenticité d'un fichier tarifaire
python3 scripts/crawl_all_countries.py --validate-file DZA
```

---

*Fin du document.*
