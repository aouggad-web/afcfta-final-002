# ZLECAf Trade Calculator - PRD

## Original Problem Statement
Build a comprehensive regulatory data engine for all 54 AfCFTA countries with a full-stack trade calculator application featuring tariff calculations, regulatory compliance, and trade analytics.

## Core Requirements
1. **Regulatory Engine**: Process, validate, and serve detailed tariff and compliance data for all African countries
2. **Trade Calculator**: Calculate import taxes comparing NPF vs ZLECAf regimes with savings display
3. **Multi-Country Support**: Cover all 54 AfCFTA member states
4. **Data Accuracy**: Display authentic national tariff positions with exact descriptions
5. **Statut juridique du SaaS — INFORMATIF, NON OPPOSABLE** : le SaaS est un outil informatif ; il ne crée aucun droit, n'engage pas l'administration et ne remplace pas les publications officielles de l'autorité douanière (tarif officiel, JO) qui seules font foi. Cela n'exonère pas de la rigueur documentaire : traçabilité SHA-256, verbatim de la source, écarts documentés sans arbitrage, aucun taux inventé.
6. **Vérification de l'audit (mission)** : chaque audit documentaire (`scripts/audit_tariff_documentation.py`) doit vérifier que le cadre informatif est respecté — disclaimer « outil informatif, non opposable » présent dans les rapports, absence de toute formulation d'opposabilité (dimension `informative_framing`, bloc `legal_framing`), en plus des contrôles techniques (doublons, SH6, taux, taxes sans unité, comparaison source).
7. **Recherche des actes juridiques officiels (rigueur)** : pour chaque pays, rechercher et archiver avec SHA-256 les actes qui fondent le tarif — code des douanes, loi de finances/articles douaniers, décret/arrêté du tarif, loi de ratification des accords (ZLECAf…), circulaires tarifaires — dans `data/sources/<ISO>/_manifest.json`. Chaque acte archivé renforce la crédibilité documentaire du SaaS sans lui conférer d'opposabilité.
8. **Interdits absolus** : pas de mock, pas de synthèse, pas d'extrapolation. Les taux, assiettes, libellés et formalités proviennent exclusivement de la source officielle (verbatim). Toute donnée non publiée par la source reste un écart documenté (`source_gaps`), jamais comblé par calcul ou inférence. L'audit vérifie l'absence de marqueurs mock/synthèse/extrapolation (dimension `verbatim_integrity`).

## Architecture
- **Backend**: FastAPI (Python)
- **Frontend**: React + Vite + Tailwind CSS + Shadcn UI
- **Database**: MongoDB (primary), PostgreSQL (regulatory data - migration done)
- **Caching**: Redis

## What's Been Implemented

### August 13, 2026 — Stripe (abonnements SaaS) + sécurité (rate-limiting, GeoIP)
- **Stripe** : sandbox de test réclamable provisionné (Flow A officiel Emergent), catalogue créé (Starter 9$/Pro 19$/Business 59$ mensuel + annuel), fiscalité automatique Stripe activée (Managed Payments/SMP, compte DE). Checkout, webhook, portail client et page `pricing.html` (déjà câblée en amont par un PR upstream) testés de bout en bout avec de vrais paiements test (carte 4242...). 2 bugs critiques trouvés par l'agent de test et corrigés : URL du webhook Stripe mal configurée (`/api/stripe/webhook` → `/api/billing/webhook`) et `BILLING_SUCCESS_URL`/`BILLING_CANCEL_URL` non définies (404 après paiement). Lien "Tarifs" ajouté à la sidebar/topbar. Chargily (Algérie/DZD) reste en stub par défaut (`CHARGILY_ENABLED=false`, Phase 2).
- **MaxMind GeoIP local** : base `GeoLite2-Country.mmdb` téléchargée (mirroir communautaire, sans compte MaxMind), `GEOIP_DB_PATH` configuré, `geoip2` installé. Testé : IP algérienne → verrou Chargily/DZD actif ; IP US → Stripe/USD. Vérifié en local (localhost:8001) car l'ingress externe réécrit `X-Forwarded-For` avec la vraie chaîne (empêche l'usurpation, comportement sain).
- **Détection IP client fiable** : `TRUSTED_PROXY_HOPS=3` câblé dans `geo_service.py`, vérifié via `/api/billing/geo-diagnostic` = IP réelle (confirmé avec `api.ipify.org`).
- **Rate-limiting** : bug trouvé (exemption par défaut matchant toutes les routes, rate-limiter inactif depuis l'origine) corrigé indépendamment à la fois localement et par un PR upstream parallèle (`claude/rate-limit-fix`) — les deux convergent, actif et vérifié (429 déclenché au-delà de 10/min sur `/api/auth/*`, 120/min ailleurs).
- **Bug récurrent (4 occurrences)** : `AfcftaSidebar.jsx` perd ses imports lucide-react (`Mail/User/LogOut/Tag`) à chaque `git reset --hard origin/main` car jamais poussé sur GitHub — réappliqué à chaque fois, l'utilisateur a été prévenu d'utiliser "Save to Github" pour stopper la récidive.
- Identifiants Stripe/test : voir `/app/memory/test_credentials.md`.


### August 9, 2026 — Couche SaaS : comptes utilisateurs + formulaire de contact + emails transactionnels
- Nouveau système d'authentification JWT (cookie httpOnly, 7 jours) : `POST /api/auth/register`, `/login`, `/logout`, `GET /api/auth/me` (fichiers `backend/routes/user_auth.py`, `backend/services/user_auth_service.py`).
- Protection anti-brute-force : 5 échecs de connexion par email → verrouillage 429 pendant 15 min (`login_attempts`, clé = email ; corrigé d'un bug d'IP instable derrière l'ingress).
- Compte admin auto-seedé au démarrage depuis `.env` (`ADMIN_EMAIL`/`ADMIN_PASSWORD`).
- Formulaire de contact (`POST /api/contact`) → stocke en base (`contact_messages`) + notifie l'admin par email.
- Emails transactionnels réels via SMTP Zoho Mail (`backend/services/email_service.py`, vars `SAAS_SMTP_*` dans `.env`) : email de bienvenue à l'inscription + notification admin sur contact. Script de test manuel : `backend/scripts/test_saas_email.py`.
- Frontend : `AuthContext.jsx`, `AuthModal.jsx` (connexion/inscription, thème sombre cohérent avec l'app), `ContactTab.jsx`, nouvel onglet "Contact" + bouton Connexion/Déconnexion dans la sidebar et la topbar mobile.
- Testé via `testing_agent_v4_fork` : 11/11 tests pytest backend + tests UI Playwright, 100% de réussite, aucune régression sur le reste du dashboard (S1-S6 Opportunités inclus). Deux bugs réels trouvés et corrigés pendant le développement (comparaison de dates naïve/avec-fuseau, identifiant IP instable pour le brute-force) + un défaut visuel (modale au thème clair) corrigé après le rapport de test.
- Identifiants : voir `/app/memory/test_credentials.md`.

### July 21 – August 9, 2026 — Synchronisations GitHub multiples (`sync_emergent.sh`)
- Import successif de PR #293 à PR #373 (dépôt `aouggad-web/afcfta-final-002`), incluant : module « Flux stratégiques » (nouvel onglet **S6**, capacité industrielle — `strategic_trade_service.py`, endpoint `/api/strategic/flows/{iso3}`), recherche nom de marchandise → code SH (index OMD), fiches pays WB/FMI 2025, garde-fou fail-closed sur mesures ZLECAf non traçables (DZA/TUN/MAR), vérification massive de données fiscales/TVA par pays (UEMOA, CEMAC, EAC, Egypte, Maurice, Tunisie...), dissociation des acteurs réglementaires historiques.
- Bug connu (non-bloquant) : l'étape 4 (auto-test) du script `sync_emergent.sh` échoue parfois avec `ModuleNotFoundError: No module named 'engine'` car elle n'ajoute pas la racine du dépôt au PYTHONPATH — le backend réel fonctionne correctement malgré cet échec ; il faut simplement relancer `cd frontend && yarn build && sudo supervisorctl restart frontend` manuellement si l'étape 5 a été sautée.
- Découverte importante : le backend tourne via `uvicorn --workers 2` **sans** `--reload` — tout changement de code backend nécessite un `sudo supervisorctl restart backend` explicite (pas de hot-reload automatique).

### June 7, 2026 — Recherche SH2/SH4/SH6 + Intitulé (Statistiques → Par Pays & SH6)
- Sous-module « Par Pays & SH6 » : recherche en **onglets séparés Chapitre (SH2) / Position (SH4) / Sous-position (SH6)**, chacun avec agrégation correcte (SH2 = tout le chapitre, SH4 = toute la position, SH6 = sous-position exacte).
- Nouvel **onglet « Intitulé »** affichant le libellé officiel OMD du code SH sélectionné (FR/EN, chapitre, position, catégorie).
- Backend : param `level` (hs2/hs4/hs6) sur `/api/oec/country/{iso3}/hs6/{code}/history` (filtrage explicite par niveau via les 6 derniers chiffres de l'ID OEC) ; nouvel endpoint `/api/hs-codes/label/{code}`.
- Le changement d'onglet relance automatiquement la requête au bon niveau. Testé via curl + screenshots (Algérie ch.27 = 205,6 Md$ cumulés).


### June 7, 2026 — Calculateur de fret terrestre (Logistique → Terrestre)
- Calculateur de fret routier/ferroviaire sur les **15 corridors PIDA** africains (longueur réelle, postes-frontières, OSBP, opérateurs).
- Modèle : transport ($/tonne-km × tonnage × distance × coef. marchandise) + franchissement frontières (réduit pour OSBP) + documentation ; choix du mode (route/rail selon corridor) ; délais selon vitesse + attentes frontières.
- Calibré Banque Mondiale SSATP / UNECA / AfDB 2024. Endpoints : `GET /api/logistics/land/fees/{corridors|cargo-types|cost}`.
- Frontend : `LandFreightCalculator.jsx` intégré dans l'onglet « Terrestre (Corridors) ».
- Testé : curl + screenshot (Abidjan-Lagos route 30 t = 4 080 $, 0,1371 $/tonne-km).


### June 7, 2026 — Calculateur de fret aérien (Logistique → Aérien)
- Nouveau calculateur de fret aérien couvrant les **64 aéroports cargo** africains (registre `logistics_air_data`).
- Méthodologie IATA TACT : poids taxable = max(poids réel, poids volumétrique à 167 kg/m³), + FSC (carburant), SSC (sûreté), manutention/LTA, charge minimale ; coefficients par nature de marchandise (général, périssable, pharma, DGR, valeur, animaux vivants).
- Modèle distance-coût calibré (IATA TACT 2024 + tarifs cargo compagnies africaines) ; sélection des compagnies par région ; délais selon connectivité hub.
- Endpoints : `GET /api/logistics/air/fees/airports`, `/air/fees/commodities`, `/air/fees/cost`.
- Frontend : `AirFreightCalculator.jsx` intégré dans l'onglet « Aérien (Fret) », sélecteurs groupés par région, décomposition des coûts + poids taxable.
- Testé via curl + screenshot (Nairobi→Lagos 1000 kg/4 m³ périssable = 4 590 $).


### June 7, 2026 — Expansion du calculateur de fret maritime (Logistique)
- Couverture portuaire passée de **21 → 55 ports** africains à conteneurs (5 façades : Méditerranée, Atlantique, Mer Rouge, Océan Indien, îles).
- Matrice de routes complète : **1 485 paires** (32 routes "benchmark" tarifs armateurs publiés + 1 453 routes modélisées).
- Modèle distance-coût calibré (Drewry 2024 / UNCTAD MRTS 2024) avec distances maritimes réalistes via points de passage (Gibraltar, Suez, Bab-el-Mandeb, Cap de Bonne-Espérance).
- Nouvel endpoint `GET /api/logistics/fees/ports` ; frontend charge les ports dynamiquement, sélecteurs groupés par région, badge provenance "Publié/Estimé", tableau plafonné à 250 lignes.
- Fichiers : `backend/logistics_fees_data.py` (réécrit), `backend/routes/logistics.py`, `frontend/src/components/logistics/ShippingFeesCalculator.jsx`.
- Testé via curl (endpoints) + screenshot (UI Lomé→Mombasa OK).
- ⚠️ Disque `/app` était plein à 100% — caches nettoyés (~1,9 Go libres). Sauvegarde locale pré-pull GitHub dans `/app/.local_backups/`.


### March 15, 2026 - PostgreSQL Migration Complete
- ✅ Migrated all 54 countries to PostgreSQL (894,783 records)
- ✅ Created full-text search index for French descriptions
- ✅ New `/api/postgres-tariffs/*` API endpoints
- ✅ Frontend updated to use PostgreSQL API with fallback
- ✅ Real national tariff descriptions (e.g., Kenya: "Café Arabica AA" instead of "Type 1")
- Note: Some countries (Algeria) use generic labels in their official nomenclature

### March 15, 2026 - Banking System Integration
- ✅ Added Banking tab with full African banking system data
- ✅ Integrated `banking_system` module (banks_registry, foreign_exchange, trade_finance, risk_assessment, compliance)
- ✅ Created `/api/banking/*` endpoints for country banks, regulations, risk assessment
- ✅ BankingInfoPanel component with tabs: Banks, Forex, Risk, Instruments, Payment Systems, Compliance

### March 15, 2026 - GitHub Update
- Added African currencies system (`currencies.py`, `exchange_rates.py`)
- Added AI intelligence routes (`ai_intelligence.py`, `investment_intelligence.py`)
- Added regional analytics dashboard
- Added shipping fees calculator
- Added comprehensive search component

### Previous Sessions
- ✅ Built Regulatory Engine v3
- ✅ PostgreSQL migration (1.5GB regulatory data)
- ✅ Text Search API (French/English support)
- ✅ Redis caching implementation
- ✅ OEC data audit (fixed NaN values)
- ✅ UI flickering fix
- ✅ Calculator UI enhancements

## Pending Issues
1. **P0**: National positions display "Type 1, Type 2" instead of exact descriptions
2. **P1**: Core API still uses flat files (.jsonl) instead of PostgreSQL

## Prioritized Backlog

### P0 (Critical)
- [ ] Fix national position descriptions in calculator

### P1 (High)
- [ ] Refactor `/api/authentic-tariffs/calculate` to use PostgreSQL
- [ ] Refactor `/api/regulatory-engine/details` to use PostgreSQL

### P2 (Medium)
- [ ] Integrate Sankey Diagram (PR pending)
- [ ] Full API v2 migration

### P3 (Low)
- [ ] Add RASD (Sahrawi Arab Democratic Republic) as 55th country
- [ ] Audit economic indicators

### P4 (Enhancement)
- [ ] Enhanced country profile pages
- [ ] Mobile API optimization

## API Endpoints
- `GET /api/health` - Health check
- `POST /api/authentic-tariffs/calculate` - Tariff calculation
- `GET /api/authentic-tariffs/country/{iso3}/sub-positions/{hs6}` - Sub-positions
- `GET /api/commodities/search` - Text search (PostgreSQL)
- `GET /api/statistics` - Dashboard statistics
- `GET /api/currencies` - African currencies (NEW)
- `GET /api/exchange-rates` - Exchange rates (NEW)
- `GET /api/banking` - Banking information (NEW)

## Credentials
- **PostgreSQL**: set `POSTGRES_URL` in `.env` (see `.env.example`)
- **Redis**: set `REDIS_URL` in `.env` (see `.env.example`)

## Tech Stack Versions
- Python 3.11+
- React 18
- FastAPI 0.100+
- PostgreSQL 15
- Redis 7

## Session Update (Sept 2026) - GitHub pull ("main" branch) + backend routing fix
- Workspace was on a diverged local branch "Main" (capital M, 2 commits ahead of a common ancestor with the repo's real default branch). Per user's explicit choice ("celle qui contient le plus de fichiers"), hard-switched the workspace to `origin/main` (lowercase, default branch, commit c4478d55), replacing all prior content.
- Backend failed to start post-pull; fixed two crashes in `backend/server.py`: (1) `ModuleNotFoundError: No module named 'engine'` — this is the SAME issue noted in the July/August log above where `sync_emergent.sh`'s self-test hits this, but here it broke the actual running server, not just the sync script's self-test — fixed by inserting the repo root into `sys.path` at import time so it doesn't depend on `sync_emergent.sh` being run; (2) `if db:` on a pymongo `Database` object raises `NotImplementedError` — changed to `if db is not None:`.
- **Major regression found and fixed**: `server.py` was not calling `routes.register_routes(api_router)` — around 30 routers (oec, hs_codes, countries, tariffs, statistics, etl, substitution, gemini_analysis, rules_of_origin, hs6_database, authentic_tariffs, banking, insurance, currencies, mobile, graphql, regulatory_*, reports, strategic_intelligence, user_auth, billing, contact, health...) were unmounted, causing 404s on almost the entire `/api` surface except `production` and a hand-picked handful. Replaced the stale manual mounting block with `register_routes(api_router)`. Confirmed via testing agent: 33/35 endpoints now respond with real data.
- Fixed `POST /api/contact` 500 (`await` on synchronous pymongo `insert_one()`) and `/api/currencies` double-`/api` prefix bug.
- Corrected `frontend/.env` `REACT_APP_BACKEND_URL` to this pod's URL, installed backend/frontend deps, both services running.
- **Known limitation, not touched pending user input**: frontend entry point `src/index.js` only wires 6 of 11 sidebar modules; Dashboard/Calculateur/Statistiques/Logistique/Profils show "Module en développement" placeholders. `src/App.js` has apparently fuller tab implementations but is not the active entry and its currency relative to `index.js`'s migrated modules is unverified — did not swap to avoid regressing the working modules (Production, R. d'Origine, Contact, Finance all verified working).

## Session Update (Sept 2026) - Full module wiring + design restoration
- User reported: "les couleurs du frontend ont changé radicalement, tout le design est perdu" after the GitHub pull, and asked to investigate wiring App.js's Dashboard/Calculateur/Statistiques/Logistique tabs.
- Root cause (two combined bugs): (1) `frontend/src/index.js` (the active Vite entry per `index.html`) rendered its own stripped-down local `App` with `ModulePlaceholder` for Dashboard/Calculateur/Statistiques/Logistique/Profils, instead of the full `AppWithAuth` component exported by `frontend/src/App.js`; (2) the Tailwind CSS entry stylesheet `frontend/src/index.css` (contains `@tailwind base/components/utilities` + imports `styles/layout.css`, `styles/tabs.css`, `styles/statistics.css`) was never imported by any JS file, so Tailwind utility classes (grid, rounded-2xl, spacing, card layout) never made it into the Vite build even though `tailwind.config.cjs`/`postcss.config.cjs` were correctly configured.
- Fix: rewrote `frontend/src/index.js` to import `./index.css` (Tailwind + layout/tabs/statistics), `./i18n` (i18next init, required by `App.js`'s `useTranslation()`), and render `AppWithAuth` from `./App`. Rebuilt the Vite production bundle (`yarn build`) and restarted frontend.
- Result: all 11 sidebar modules (Tableau de bord, Calculateur, Statistiques, Production, Logistique, Finance, Outils, R. d'Origine, Profils, Opportunités, Contact) now render with real content and the intended dark navy/gold-copper "Kente/zellige" themed design (previously a generic purple-gradient sidebar with plain unstyled text due to missing Tailwind CSS). Verified via `auto_frontend_testing_agent`: all 10+ modules tested, no placeholders remaining, no regressions on previously-working modules (Production, R. d'Origine, Contact, Finance, Opportunités).
- Minor non-blocking items noted by testing agent: `/api/production/statistics` and `/api/production/macro/{iso3}` return 404 (Production module still functional overall); not fixed this session, low priority.

## Session Update (Sept 2026) - Production module: /api/production/statistics + /api/production/macro endpoints
- Added `GET /api/production/statistics` (years covered per dimension: value_added_macro/agriculture_faostat/manufacturing_unido/mining_usgs) and `GET /api/production/macro/{country_iso3}` (sectoral GDP value-added breakdown + GDP growth) to `backend/routes/production.py`, backed by real World Bank WDI data already committed in `backend/etl/macro_wdi_data.py` / `backend/etl/macro_extended.py` (previously unused/unwired).
- Added small `get_covered_years()` helper to `backend/etl/isic4_idsb_data.py`.
- Fixes the Production → Macro sub-tab, which previously showed "Aucune donnée disponible pour ce pays." because these two endpoints didn't exist.
- Verified via `deep_testing_backend_v2` (41/42 endpoints passing, tested DZA/MAR/EGY/KEN/ZAF with varying real data, 404 on invalid country code, no regressions) and `auto_frontend_testing_agent` (Macro sub-tab renders real line/bar charts + GDP growth + sector cards, no console errors, no regressions on Agriculture/Manufacturing/Mining sub-tabs).
- Known pre-existing gap, not in this session's scope: Manufacturing sub-tab's `/api/production/unido/*` endpoints and Mining sub-tab's `/api/production/mining/{iso3}` endpoint are still missing (404), though both sub-tabs degrade gracefully without crashing.

## Session Update (Sept 2026) - Lint cleanup
Fixed 31 blocking lint errors reported by pre-completion checks:
- Route shadowing fixed in backend/routes/logistics.py (ports/search, air/airports/search moved before parameterized routes) and backend/routes/tariffs.py (country-hs6-tariffs/available and /all moved before /{hs6_code})
- Removed duplicate merge-conflict code blocks (F811/F601) in backend/routes/ai_intelligence.py (kept engine-based scoring implementation), backend/services/crawlers/dza_tariff_connector.py (kept NorthAfricaCrawlerBase-based class, unused legacy aiohttp crawler removed), backend/crawlers/countries/uma_member_scraper.py (deduped COUNTRY_CONFIGS entries EGY/TUN/LBY/MRT/SDN and duplicate functions)
- Fixed bare except clauses in backend/routes/health.py and backend/etl/news_aggregator.py
- Removed duplicate test method in backend/tests/test_north_africa_tariff_system.py
- Verified via `ruff check` (no route-shadowing/F811/F601/E722 remain) and curl smoke tests on affected endpoints
