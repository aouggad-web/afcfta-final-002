# Audit approfondi — Plateforme AfCFTA / ZLECAf

> État des lieux complet (backend, frontend, données, infra) + feuille de route d'améliorations et nouvelles fonctionnalités.
> Date : 2026-06-26

---

## 1. Synthèse exécutive

La plateforme est **mature et riche fonctionnellement** : couverture des 55 pays africains, calculateur tarifaire avancé, statistiques commerciales (OEC en temps réel), logistique multimodale, règles d'origine, profils pays, banque/finance. L'architecture backend (FastAPI modulaire, 30+ routeurs) et frontend (React 19 + Vite, 10 onglets) est solide.

**Note globale par axe :**

| Axe | Note | Commentaire |
|---|---|---|
| Couverture fonctionnelle | 🟢 Excellent | 10 domaines métier, très complet |
| Couverture des données | 🟢 Excellent | 55/55 pays, 96/97 chapitres HS, données à jour (juin 2026) |
| Qualité du code / architecture | 🟡 Bon | Modulaire mais quelques dettes (limites en dur, données hardcodées) |
| Tests | 🔴 Faible | Backend partiel (41 fichiers, masqués par `continue-on-error`), **frontend = 0 test** |
| CI/CD | 🟡 Moyen | Pas de lint, pas de scan sécu, tests frontend absents |
| Sécurité | 🟡 Moyen | Auth par clé API + CORS OK, mais pas de rate-limiting par tier, CSRF déclaré non implémenté |
| Observabilité | 🔴 Faible | Pas de Sentry, pas de métriques, logs basiques |
| Fraîcheur / versioning des données | 🟡 Moyen | Données récentes mais **aucun horodatage/versioning** dans les fichiers tarifaires |

---

## 2. État actuel — par couche

### 2.1 Backend (FastAPI v3.0.0)
- **Entrée** : `backend/server.py` — middleware CORS, security headers, rate-limit (120 req/min), auth `X-API-Key`.
- **30+ routeurs** (`backend/routes/`) : calculator, tariffs, hs_codes, countries, logistics, rules_of_origin, trade_data, statistics, banking, news, regional_analytics, currencies, exchange_rates, crawl, admin.
- **Sources de données** :
  - **Live** : OEC (statistiques commerciales temps réel via `httpx`), WTO (partiel).
  - **Statique** : 59 JSON tarifaires + 55 datasets enrichis (`backend/data/tariffs/`), règles d'origine JSON, données régionales.
  - **Base** : MongoDB optionnelle (auth, customs), PostgreSQL conditionnel (cache tarifaire), Redis optionnel.
- **Domaines bien développés** : tarifs MFN/ZLECAf, règles d'origine, logistique maritime/terrestre, banque, intelligence régionale.
- **Domaines faibles/stubs** : logistique aérienne (placeholder), chaînes de valeur (minimal), zones franches (stub 901 octets), réserves d'or (stub 613 octets).

### 2.2 Frontend (React 19 + Vite)
- **10 onglets** : Dashboard, Calculateur, Statistiques, Opportunités, Production, Logistique, Banque, Outils, Règles d'origine, Profils.
- **Points forts** : calculateur (80 Ko, recherche HS intelligente, comparaison multi-pays), statistiques (10 sous-onglets, cartes Leaflet, treemap, RCA, complémentarité), logistique (22 composants multimodaux).
- **Visualisation** : Recharts 3.3 + Leaflet. Manque : heatmaps de paires de pays, graphes réseau de chaînes de valeur, séries temporelles (beaucoup de snapshots statiques 2024).
- **i18n** : i18next FR/EN, mais ~58 composants avec des objets `texts={fr,en}` codés en dur → couverture partielle/incohérente.
- **Export** : `ExportTools.jsx` (PDF/CSV/PNG) — présent dans Statistiques & Calculateur, **absent** d'Opportunités, Production, Logistique.

### 2.3 Données
- **55/55 pays** avec données tarifaires ; Érythrée (non-signataire) et RASD correctement marqués.
- **HS6** : 5 831 codes, 96/97 chapitres (chapitre 77 = limitation HS standard, non bloquant).
- **Règles d'origine** : 96/97 chapitres, statut « AGREED », source Appendix IV (PSR).
- **Fraîcheur** : tarifs régénérés juin 2026, OEC jusqu'à 2024, RoO juin 2026.
- **Fix Algérie (PR #80)** : résolu — DZA montre 5 533 lignes « VERIFIED », plus de placeholders « Type N ».
- **QA en place** : `backend/crawlers/validators/` (complétude 80%, fraîcheur 90j, outliers 3σ), scripts de nettoyage.

### 2.4 Infra / CI/CD
- **CI** (`.github/workflows/ci.yml`) : détection conflits, pytest backend (avec `continue-on-error`), build frontend.
- **Déploiement** : Replit (primaire) + Docker Compose (MongoDB + Redis + backend) ; Dockerfile multi-stage non-root durci.
- **Manques** : pas de lint en CI (black/flake8/mypy installés mais non exécutés), pas de tests frontend, pas de scan sécu (Bandit/Trivy), pas d'Alembic, pas de Sentry.

---

## 3. Problèmes identifiés (par priorité)

### 🔴 P1 — Critiques / dette technique bloquante
1. **Bug RCA/TCI : limite `2000` en dur** (`oec_trade_service.py:270` et `:325`). Pour les grands exportateurs (Égypte, Nigéria, Afrique du Sud) avec >2000 lignes HS6, les résultats sont **silencieusement tronqués** → RCA et indice de complémentarité commerciale faussés. *(Déjà identifié, traité comme suivi séparé.)*
2. **Frontend : 0 test.** Aucun Jest/Vitest/RTL/Playwright. Risque de régression élevé (ex. le fix du sélecteur d'année aurait pu casser silencieusement).
3. **CI masque les échecs** : `continue-on-error: true` sur les tests backend → un test cassé ne bloque pas le merge.

### 🟡 P2 — Importants
4. **Données dashboard hardcodées** (`analytics/dashboard_generator.py`) — « realistic hardcoded data » au lieu de calculs réels.
5. **Aucun versioning/horodatage des données tarifaires** → impossible de tracer les changements ou d'afficher « dernière mise à jour » de façon fiable par fichier.
6. **i18n incohérente** : 58+ composants avec traductions en dur hors du système i18next central.
7. **Sécurité** : CSRF déclaré dans CORS mais **middleware non implémenté** ; pas de rate-limiting par tier de clé ; pas de quotas d'usage.
8. **Pas d'observabilité** : ni Sentry, ni métriques Prometheus, ni logging requête/réponse.

### 🟢 P3 — Améliorations / polish
9. Export (PDF/CSV) absent de 3 onglets majeurs.
10. États de chargement/erreur incohérents côté frontend (pas de skeletons, pas de toasts d'erreur, pas de retry).
11. Stubs : logistique aérienne, zones franches, chaînes de valeur, réserves d'or.
12. Accessibilité partielle (28 occurrences ARIA, tables sans `scope`, contraste non vérifié).

---

## 4. Améliorations recommandées (correctifs sur l'existant)

| # | Amélioration | Effort | Impact |
|---|---|---|---|
| A1 | **Corriger la troncature RCA/TCI** : paginer l'API OEC (boucle jusqu'à épuisement) ou propager réellement `limit`. | M | Élevé |
| A2 | **Suite de tests frontend** : Vitest + React Testing Library sur les composants critiques (Calculator, TradeComparison, ExportTools) + 2-3 E2E Playwright. | L | Élevé |
| A3 | **Durcir la CI** : retirer `continue-on-error`, ajouter lint (black/flake8/eslint), exécuter les tests frontend, ajouter Bandit + Trivy. | M | Élevé |
| A4 | **Versioning des données** : ajouter `generated_at`, `source`, `version` à chaque fichier tarifaire + endpoint `/api/data/freshness` exposant la fraîcheur par domaine. | M | Élevé |
| A5 | **Centraliser l'i18n** : migrer les objets `texts` codés en dur vers `i18n/locales/{fr,en}.json`. | L | Moyen |
| A6 | **Remplacer les données dashboard hardcodées** par des agrégats calculés depuis les vraies sources. | M | Moyen |
| A7 | **Observabilité** : intégrer Sentry (back+front) + endpoint `/metrics` Prometheus + logging structuré requête/réponse. | M | Moyen |
| A8 | **Sécurité** : implémenter le middleware CSRF, rate-limiting par tier, quotas par clé API. | M | Moyen |
| A9 | **Généraliser Export** (PDF/CSV/PNG) à Opportunités, Production, Logistique. | S | Moyen |
| A10 | **UX résilience** : composant Skeleton unifié, toasts d'erreur (Sonner déjà installé), retry automatique sur échec API, états vides. | M | Moyen |
| A11 | **Alembic** pour les migrations PostgreSQL (versionnage du schéma). | S | Moyen |
| A12 | **Accessibilité** : `scope` sur tables, audit contraste WCAG AA, labels ARIA manquants. | S | Faible |

---

## 5. Nouvelles fonctionnalités proposées (pour être exhaustif)

### 5.1 Intelligence commerciale & analyse
- **F1 — Comparateur tarifaire bilatéral** : endpoint + UI dédiés pour comparer les tarifs entre **une paire de pays** sur un produit (manque identifié côté backend).
- **F2 — Simulateur d'impact ZLECAf** : « si j'exporte le produit X de A vers B, voici l'économie tarifaire année par année (calendrier de démantèlement) » avec projection cumulée.
- **F3 — Historique & suivi des changements tarifaires** : timeline des modifications par pays/produit (nécessite A4 versioning).
- **F4 — Heatmap d'intensité commerciale** entre paires de pays + **graphe réseau** des chaînes de valeur (au-delà du Sankey actuel).
- **F5 — Séries temporelles enrichies** : exploiter les années OEC 2018-2024 (cube HS Rev. 2017) pour de vraies courbes de tendance, pas des snapshots 2024.

### 5.2 Personnalisation & utilisateur
- **F6 — Comptes utilisateurs** (actuellement stateless) : sauvegarde des calculs, favoris produits/pays, dashboards persistants (le drag-drop existe déjà mais sans persistance).
- **F7 — Alertes & notifications** : abonnement aux changements tarifaires d'un produit/pays (Sonner installé, sous-utilisé ; backend a un « notifications manager » non branché).
- **F8 — Recherche globale cross-app** (actuellement la recherche HS n'existe que dans le Calculateur).
- **F9 — Espace de travail / panier d'analyse** : regrouper plusieurs produits/pays pour un rapport consolidé exportable.

### 5.3 Données & couverture
- **F10 — Compléter les stubs** : logistique aérienne (vraies routes/tarifs), zones franches, chaînes de valeur sectorielles, réserves stratégiques.
- **F11 — Endpoint « rapport de qualité des données »** : surfacer les validators QA existants vers le frontend (transparence sur complétude/fraîcheur).
- **F12 — Intégration WITS/Banque Mondiale & UNCTAD** complète (référencées mais partielles) pour croiser les sources.
- **F13 — Données de mesures non-tarifaires (MNT/NTM)** : un angle mort majeur du commerce intra-africain réel.

### 5.4 API & écosystème
- **F14 — API publique documentée + clés self-service** (portail développeur) pour valoriser la donnée auprès de tiers.
- **F15 — Export programmatique en masse** (au-delà de `TariffDownloads.jsx`) : statistiques, production, logistique en CSV/JSON/Parquet.
- **F16 — Assistant IA conversationnel** unifié (briques Gemini/AI déjà présentes en silos : AIAnalysis, AIRecommendations, AITradeSummary) → un copilote unique « pose ta question commerce ».

---

## 6. Feuille de route suggérée (séquencement)

**Sprint 1 — Fondations qualité (P1)**
- A1 (fix RCA/TCI) · A2 (tests frontend) · A3 (durcir CI)

**Sprint 2 — Fiabilité données & observabilité (P2)**
- A4 (versioning + `/api/data/freshness`) · A6 (dashboard réel) · A7 (Sentry/metrics) · A11 (Alembic)

**Sprint 3 — Sécurité & UX (P2/P3)**
- A8 (CSRF/quotas) · A9 (export généralisé) · A10 (résilience UX) · A5 (i18n centralisée)

**Sprint 4 — Nouvelles fonctions à forte valeur**
- F1 (comparateur bilatéral) · F2 (simulateur impact) · F5 (séries temporelles) · F11 (rapport qualité données)

**Sprint 5 — Différenciation**
- F6/F7 (comptes + alertes) · F4 (heatmap/réseau) · F16 (copilote IA unifié) · F13 (mesures non-tarifaires)

---

*Audit réalisé par analyse statique du dépôt (backend, frontend, données, infra). Les estimations d'effort sont indicatives : S = quelques jours, M = ~1-2 semaines, L = plusieurs semaines.*
