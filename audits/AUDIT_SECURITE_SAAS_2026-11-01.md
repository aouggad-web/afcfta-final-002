# Audit de sécurité du SaaS ZLECAf / AfCFTA — et plan de sécurisation

**Date :** 1ᵉʳ novembre 2026
**Périmètre :** backend FastAPI (`backend/`), frontend React/Vite (`frontend/`), moteur (`engine/`, `tariff_engine/`), infrastructure de déploiement (Emergent, Docker, Replit, GitHub Pages), CI/CD (`.github/workflows/`), chaîne de dépendances.
**Méthode :** lecture statique du code + énumération en mémoire des 376 routes et de leurs dépendances d'authentification ; `bandit`, `semgrep`, `pip-audit`, `npm/yarn audit` ; reproduction locale hors-ligne des dénis de service (FastAPI TestClient) ; tests passifs en lecture seule et faible volume sur la préproduction Emergent (`git-sync-41.preview.emergentagent.com`) et le domaine de production (`afcfta-zlecaf.com`) ; interrogation DNS publique et de l'API GitHub. **Aucun fichier du dépôt n'a été modifié pendant l'audit ; aucun test intrusif n'a été mené.**

> **Niveaux de confiance.** « Confirmé » = chaîne de code lue de bout en bout et/ou reproduite. « Plausible » = dépend d'une valeur d'exécution (secret, variable d'environnement, réglage de tableau de bord) que seul l'exploitant peut vérifier — ces points sont regroupés au §6 « Vérifications à faire de votre côté ».
>
> **Fait important vérifié :** le dépôt `aouggad-web/afcfta-final-002` est **privé** (API GitHub : `private: true`). Plusieurs constats de chaîne CI voient donc leur portée limitée à vos collaborateurs, et non à « tout internaute » comme une note d'audit antérieure le laissait croire. Le détournement de domaine (C1), lui, reste public et entier.

---

## 1. Synthèse exécutive

La base de sécurité applicative est **sérieuse** : CORS en liste blanche exacte, protection CSRF double-submit, signatures de webhooks Stripe/Chargily vérifiées, clés API hachées, quotas d'IA réellement appliqués, confinement du service de fichiers statiques, conteneur Docker durci (non-root, `read_only`, `cap_drop ALL`). **Il n'y a pas de faille d'injection SQL/NoSQL, de SSRF, ni de traversée de chemin exploitable depuis le réseau.**

Les risques majeurs ne sont pas dans le code métier mais **autour** : un domaine de marque non revendiqué, une chaîne de déploiement qui exécute n'importe quelle branche avec les secrets de production, des quotas payants contournables en ne se connectant pas, et quelques points de déni de service anonymes sur un worker unique.

| Axe | Note | Commentaire |
|---|---|---|
| Authentification / sessions | 🟡 Moyen | bcrypt + JWT corrects, mais pas de vérification d'email, sessions non révocables (7 j), verrouillage par email abusable |
| Autorisation / monétisation | 🟠 Faible | quotas et accès payants **non appliqués aux appels anonymes** |
| Paiement (Stripe / Chargily) | 🟢 Bon | montants côté serveur, webhooks signés et idempotents, accès accordé par webhook uniquement |
| Déni de service | 🟠 Faible | plusieurs points bloquants sur un worker unique, atteignables sans clé |
| Secrets | 🟡 Moyen | aucun secret en clair dans le dépôt ni dans l'historique ; jeton OEC qui serait journalisé (latent, corrigé), placeholders à vérifier |
| Chaîne de déploiement / CI | 🔴 Critique | déploiement de branche arbitraire avec secrets de prod ; actions non épinglées ; jetons d'écriture |
| Infrastructure / domaine | 🔴 Critique | `afcfta-zlecaf.com` non revendiqué → détournement possible |
| En-têtes / durcissement HTTP | 🟡 Moyen | HTML sans en-têtes de sécurité, `HTTPS_ENABLED=false` en préprod |
| Dépendances | 🟡 Moyen | vulnérabilités connues sur starlette, pyjwt, cryptography, urllib3, axios, dompurify |

**Décompte des constats :** 2 Critiques · 5 Élevés · 12 Moyens · 9 Faibles/Info (C2 reclassé en Moyen après vérification, voir ci-dessous).

**Suivi des corrections (PR #750, fusionnée le 01/11/2026 ; PR #753) :** C1 traité (domaine vérifié côté GitHub ; page vitrine en ligne sur `https://www.afcfta-zlecaf.com` depuis le 02/11/2026, documents internes en 404) ; INFO-1 corrigé (publication Pages limitée à `site/`) ; C2 corrigé préventivement (masquage des secrets dans les journaux, clé Comtrade en en-tête) ; E3 et M8 clos (secrets et HTTPS vérifiés sur le pod) ; C3 corrigé côté script (`sync_emergent.sh` ne déploie que `main`, contrôle des crons durci par la PR #753), ruleset GitHub restant à activer.

---

## 2. Constats CRITIQUES 🔴

### C1 — Le domaine `afcfta-zlecaf.com` n'est revendiqué par personne → détournement possible
**Confiance : Confirmé (infrastructure) ; conséquence critique.**

`https://afcfta-zlecaf.com` et `https://www.afcfta-zlecaf.com` renvoient **« Site not found · GitHub Pages »** (HTTP 404, en-tête `x-github-request-id`). Cloudflare transmet le domaine à l'infrastructure GitHub Pages, mais **aucun site GitHub ne le revendique** :
- API GitHub : `afcfta-final-002` a `has_pages: false`.
- Le workflow `jekyll-gh-pages.yml` **échoue à chaque exécution** (774 runs, tous en échec récent : *« Get Pages site failed … Not Found »*, vérifié dans les logs du run 41329985195).
- Aucun enregistrement DNS de vérification GitHub (`_github-pages-challenge-aouggad-web…`) n'existe (DNS : `NXDOMAIN`).

**Impact.** Un domaine Pages non revendiqué + sans vérification de domaine peut être capté par un autre compte GitHub qui y publierait son propre site, servi sur `afcfta-zlecaf.com` avec un certificat HTTPS valide (via Cloudflare). Or ce domaine :
- est l'URL de **retour de paiement** par défaut Stripe **et** Chargily (`backend/routes/billing.py:66-74`) ;
- porte vos **emails** (`noreply@afcfta-zlecaf.com`, `contact@afcfta-zlecaf.com` — enregistrements MX/SPF/DKIM/DMARC Zoho actifs) ;
- est le domaine de marque présenté aux clients.
Un attaquant disposant du domaine peut monter de fausses pages de connexion/paiement crédibles (hameçonnage), intercepter le trafic post-paiement, ou nuire à la réputation d'envoi.

**Correctif (≈ 15 min, à faire en priorité) :**
1. GitHub → **Settings → Pages → Add a domain** → `afcfta-zlecaf.com` ; ajoutez l'enregistrement TXT de vérification fourni dans Cloudflare ; cliquez **Verify**. Ceci verrouille le domaine sur votre compte même si vous n'utilisez pas Pages.
2. Dans Cloudflare, faites pointer `afcfta-zlecaf.com` et `www` vers **votre vraie application** (l'origine Emergent ou un reverse-proxy devant), ou supprimez les enregistrements qui mènent à Pages.
3. Décidez de l'application servie sur ce domaine (aujourd'hui l'app tourne sur l'URL Emergent `*.preview.emergentagent.com`, éphémère et non destinée à la production). Tant que ce n'est pas tranché, **désactivez** `jekyll-gh-pages.yml` (voir aussi F-INFO-1 : il publierait sinon la racine du dépôt).

---

### C2 — Jeton OEC payant écrit dans les journaux et publié dans un artefact CI
**Confiance : chemin de code Confirmé. Reclassé Moyen (latent) après vérification du 01/11/2026 — corrigé préventivement dans la PR #750.**

> **Vérification.** En production, `/api/reports/oec-health` renvoie `token_configured: false` : aucun jeton OEC n'est configuré, donc aucun n'a pu être journalisé. Le workflow Opportunités n'a tourné que 3 fois (dernière exécution en juillet 2026) et ses artefacts, conservés 30 jours, ont expiré ; un commit de juillet indique que le projet ne possède pas de jeton OEC. Aucune rotation n'est donc nécessaire. Le défaut se serait déclenché à la première configuration d'un jeton payant (OEC) ou d'une clé UN Comtrade (`subscription-key`, même mécanisme).
>
> **Correctif appliqué.** `backend/log_redaction.py` : formateur qui masque les paramètres d'URL secrets (`token`, `subscription-key`, `api_key`, `key`…) dans toute ligne journalisée, traceback comprise ; httpx et httpcore relevés à WARNING. `backend/server.py` utilise cette configuration. Le workflow Opportunités filtre `uvicorn.log` avant de le publier. Tests : `backend/tests/test_log_redaction.py`. Second chemin de fuite trouvé et couvert : `real_trade_data_service.py` journalise `str(e)` des erreurs httpx, dont le texte contient l'URL complète.
>
> **Clé UN Comtrade (le projet en possède une).** Vérifié le 01/11/2026 : le repli Comtrade est désactivé en production (`/api/oec/trade-series/sources/NGA` : `enabled: false`) et aucun workflow CI n'utilise la clé, qui n'a donc pas été exposée ; rotation inutile. La clé passe désormais dans l'en-tête `Ocp-Apim-Subscription-Key` et non plus dans l'URL (`backend/services/comtrade_service.py`, `scripts/update_comtrade_data.py`, y compris l'appel WTO du script), comme le faisait déjà `wto_service.py` ; l'API reconnaît l'en-tête (testé avec une clé factice : « invalid » et non « missing subscription key »). Tests : `backend/tests/test_comtrade_key_header.py`. La clé Anthropic, transmise en en-tête par le SDK officiel, n'a jamais été concernée.
>
> **Reste à faire, non bloquant :** pour le jeton OEC (non configuré à ce jour), les messages propres à uvicorn (exception non interceptée) ne passent pas par le formateur ; le filtre CI les couvre pour l'artefact, mais pas les journaux du superviseur Emergent.

Le jeton d'API OEC (plan payant) est passé **en paramètre d'URL** :
- `backend/services/real_trade_data_service.py:41` : `enriched["token"] = OEC_API_TOKEN` ;
- `backend/services/oec_trade_service.py:260` : `params["token"] = self.api_token`.

Or `httpx` journalise l'URL complète (avec la query string) au niveau `INFO` — **vérifié localement** : `httpx` émet `HTTP Request: GET …?cube=x&token=DEMO-TOKEN`. Le logger racine est à `INFO` (`backend/server.py:66-67`). Le jeton atterrit donc en clair dans les logs applicatifs. L'équipe connaît le problème pour une autre API (`backend/services/geo_service.py:237` : *« Jeton en en-tête, pas dans l'URL : httpx journalise les URL »*) mais le correctif n'a pas été appliqué à OEC.

Pire, la CI publie ce log : `.github/workflows/opportunites_module.yml` démarre le backend avec `OEC_API_TOKEN: ${{ secrets.OEC_API_TOKEN }}` (ligne 84), redirige vers `uvicorn.log` (ligne 87) et **téléverse `uvicorn.log` comme artefact conservé 30 jours** (lignes ~112-123, `if: always()`). GitHub masque les secrets dans les logs d'étape, **pas dans les artefacts**. Le dépôt étant privé, la portée se limite à vos collaborateurs — mais un jeton payant exfiltrable reste un « denial-of-wallet ».

**Correctif :**
1. **Révoquer et régénérer** le jeton OEC ; supprimer les artefacts `opportunites-*` existants.
2. `logging.getLogger("httpx").setLevel(logging.WARNING)` et idem `httpcore`, dans `backend/server.py`.
3. Transmettre le jeton par en-tête si OEC le permet ; sinon ajouter un filtre de log qui masque `token=…`.
4. Cesser de téléverser `uvicorn.log` brut (ou le filtrer avant upload).

---

### C3 — Le déploiement exécute n'importe quelle branche avec les secrets de production
**Confiance : Confirmé (code) ; exécution à confirmer (§6).**

`sync_emergent.sh` aligne l'arbre de travail sur une branche **choisie par une variable** puis exécute le code de cette branche avec les secrets de prod :
- `sync_emergent.sh:45` : `BRANCH="${BRANCH:-$(git rev-parse --abbrev-ref HEAD)}"` ; la doc (ligne ~13) encourage `BRANCH=claude/… bash sync_emergent.sh`.
- `:60` : `git reset --hard "origin/$BRANCH"` — **aucune** vérification de signature, ni que la branche descend de `main`, ni de checks CI requis.
- Ensuite : `pip install -r backend/requirements.txt` (:125), scripts de la branche, `importlib.import_module(...)` sur des modules de la branche (:184-242), `yarn install … || yarn install; yarn build` (:270 — exécute les scripts postinstall de **chaque** dépendance et le `vite.config.js` de la branche), puis `supervisorctl restart all` (:284).

**Chaîne d'attaque.** Ce dépôt produit en continu des branches d'agents IA (`claude/*`) construites en lisant du contenu web non fiable (crawlers de tarifs). Une branche portant un `postinstall` ou un `vite.config.js` piégé, déployée via la commande documentée, exécute du code arbitraire **avec `backend/.env`** (JWT, Stripe, Chargily, Supabase, Mongo).

**Persistance cron.** `.emergent/cron/webhook_crond.sh` copie `.emergent/cron/webhook-crons` dans `/etc/cron.d` à chaque démarrage (lignes 18-21) puis `exec cron -f`. Ce fichier `webhook-crons` est gitignoré (`.gitignore:111`) et `git clean -fd -e .emergent` (:62) le préserve : une ligne cron plantée une fois **survit** à un « re-sync de main » et aux redémarrages. De plus `.emergent/cron/dispatch_webhook.sh:64` envoie `WEBHOOK_CRON_SECRET` avec `--location-trusted` (le Bearer suit une redirection cross-host) et le secret apparaît dans les arguments de `curl`.

**Correctif :**
- N'autoriser au déploiement que `main` (ou des tags signés) : refuser `BRANCH != main`, vérifier `git merge-base --is-ancestor` et/ou `git verify-commit`.
- Protéger `main` (revue de PR + checks requis, non contournables par les Actions).
- `yarn install --frozen-lockfile --ignore-scripts` (sans repli) et `pip install --require-hashes`.
- Cesser de versionner les `.emergent/cron/*.sh` de la plateforme ; surveiller `/etc/cron.d` et `.emergent/cron/webhook-crons` ; après tout soupçon de compromission, **reconstruire le pod et son volume** plutôt que re-synchroniser.
- Sortir `WEBHOOK_CRON_SECRET` de la ligne de commande (fichier/`--config`) et retirer `--location-trusted`.

> **Corrigé dans la PR #750 (01/11/2026), côté script.** `sync_emergent.sh` ne déploie plus que `main` : toute autre valeur de `BRANCH` est refusée avant la moindre commande git. La bascule est forcée (`git fetch` avec refspec explicite, puis `git checkout -f -B main origin/main`), si bien qu'un pod resté sur une autre branche avec des modifications locales, un fichier non suivi en conflit ou un clone mono-branche n'interrompt plus le déploiement (l'ancienne commande échouait dans ces trois cas, testé). L'installation du frontend est passée à `yarn install --frozen-lockfile --ignore-scripts`, sans repli : le lockfile était à jour et le build est identique à l'octet. Une nouvelle étape 1bis, non bloquante, signale toute ligne de `webhook-crons` hors de la grammaire d'Emergent, une variable répétée, un dispatch vers un hôte hors `emergentagent.com` (y compris via `user@hôte` dans l'URL) et une divergence entre les deux fichiers ; l'alerte est rappelée en fin de déploiement. Les scripts de la plateforme (`.emergent/cron/*.sh`) n'ont pas été modifiés : Emergent les régénère. Une relecture adverse indépendante a trouvé quatre contournements dans la première version du contrôle ; tous sont corrigés et couverts par des tests (rendus réels d'Emergent : aucune fausse alerte). Une deuxième relecture en a trouvé deux autres, reproduits jusqu'à la fuite du Bearer vers un hôte tiers : une barre oblique inverse acceptée juste après l'hôte (`x.emergentagent.com\@tiers`) et une troncature à 300 octets qui cachait un `@tiers` placé plus loin. Une troisième relecture en a trouvé un dernier, reproduit de la même façon : un `ENDPOINT_URL_B64=` inoffensif caché dans la valeur de `CRON_NAME` était lu à la place de la vraie affectation. Tous trois sont corrigés dans la PR #753 : l'hôte est lu sur la valeur décodée entière de l'affectation que sh exporte réellement, et tout base64 invalide, octet hors ASCII imprimable (NUL, saut de ligne, tabulation) ou valeur de plus de 2 048 octets est signalé. Limite connue : le contrôle accepte tout sous-domaine de `emergentagent.com`, y compris l'aperçu d'un autre client d'Emergent ; il ne vérifie pas que l'hôte est celui du pod.
>
> **Reste à faire (exploitant) :** activer une ruleset GitHub sur `main` (PR obligatoire, 4 checks de CI requis, force-push et suppression bloqués, **aucune exception**, car tous les agents agissent sous l'identité du propriétaire) ; régler « Save to GitHub » d'Emergent sur une branche dédiée ; ne plus lancer `production_etl.yml` depuis `main` (il y pousse directement). Non traité : `pip install --require-hashes` (Phase 2), et la branche npm du script, qui n'est durcie que lorsque yarn est présent, ce qui est le cas sur Emergent.

---

## 3. Constats ÉLEVÉS 🟠

### E1 — Quotas et droits payants non appliqués aux appels anonymes (contournement de la monétisation)
**Confiance : Confirmé (runtime hors-ligne).**

Avec `PUBLIC_DATA_ACCESS=true` (valeur par défaut, `backend/auth.py:33`) un appel sans clé ni session reçoit le tier `public`/`free`. Or **toutes** les dépendances de comptage court-circuitent quand il n'y a pas d'utilisateur JWT :
- `backend/entitlement_guard.py:207` (`require_module`, utilisé par `reports`) : `if access.quota is not None and user is not None:` → anonyme = jamais compté ;
- `:296-300` (`require_calculations_quota`) : `if ent.daily_calculations is None or user is None: return ent` → calculs illimités ;
- `:273-274` (`require_api_access`) : `if user is None: return ent` **avant** la vérification `api_access` → l'API v2 réservée à « Business » est ouverte aux anonymes.

Reproduit en local (faux Mongo) : `/api/reports/health` ×4 en **free connecté** → `[200,200,429,429]` (quota 2/j) ; en **anonyme** → `[200,200,200,200]`. `/api/v2/analytics/dashboard` : **403** en free connecté, **200** en anonyme. Un abonné free peut aussi simplement supprimer son cookie pour échapper à son propre plafond. L'export CSV/Excel/PDF (`routers/export_router.py`, monté seulement avec `_auth`) n'applique pas non plus `export_formats`.

**Correctif :** pour les actions facturables (`/api/calcul`, `/api/reports/*`, `/api/v2/*`, exports), compter l'anonyme sur une identité stable (IP résolue par `geo_service.client_ip`, déjà calculée) **ou** exiger une identité quel que soit `PUBLIC_DATA_ACCESS`. A minima, tester `ent.api_access` **avant** le `return` anonyme dans `require_api_access`.

### E2 — Points de déni de service anonymes sur un worker unique
**Confiance : Confirmé (reproduit).** Le déploiement est mono-worker (`start.sh`, `uvicorn … --workers 1`) : tout calcul synchrone lourd dans un handler `async` gèle toute l'API.

- **ReDoS GraphQL** — `backend/api/graphql/schema.py:400` : `re.search(r"\b(query|mutation)\s+(\w+)?\s*[({]", query_str)` dans `async def graphql_endpoint`. `ariadne` n'est pas installé, donc ce repli regex est le chemin **actif**. Backtracking quadratique **mesuré localement** : 2 000 espaces = 0,023 s, 8 000 = 0,35 s (l'agent a mesuré 30 000 = 6,1 s). `POST /api/graphql {"query":"query"+" "*30000+"x"}` gèle le worker. Correctif : ancrer/borner la regex (`^\s*(query|mutation)\b`), plafonner la taille du corps, exécuter le repli via `run_in_threadpool`.
- **`/api/hs-codes/product-index`** (`hs_codes.py:227`) : `q` sans `max_length`, testé contre 6 344 entrées × tokens (`omd_hs_index_service.py`). 3 000 mots ≈ 5 s de blocage. Correctif : `max_length=200`, borner les tokens, `run_in_threadpool`.
- **`/api/consultation/{iso3}/recherche`** (`consultation.py:166,195`) : 2 regex compilées par mot × ~17 000 positions nationales. 1 000 mots sur un gros pays ≈ 12 s CPU. Correctif : borner mots/longueur de `q`.
- **`/api/news?force_refresh=true`** (`news.py:24`) : contourne le cache 24 h et déclenche ~23 flux + jusqu'à ~230 appels **bloquants** `requests` (via `googlenewsdecoder`) sur la boucle d'événements (`etl/news_aggregator.py:1358,1142`). Correctif : réserver `force_refresh` à l'admin, déporter la résolution d'URL hors boucle.
- **`/api/regional/sub-positions` et `/data-inventory`** (`regional_data.py:213,235`) : relisent **tous** les `data/crawled/*_tariffs.json` (≈ 832 Mo) sans cache à chaque requête (~9 s CPU, ~438 Mo RSS mesurés). Correctif : mettre en cache l'inventaire ou le passer derrière le module `stats`.

### E3 — Secrets d'exemple acceptés au démarrage + admin re-synchronisé depuis `.env`
**Confiance : Plausible (dépend du `.env` de prod — §6). Critique si les valeurs par défaut sont en service.**

`.env.example` porte `SECRET_KEY=your-secret-key-min-32-chars`, `JWT_SECRET=your-jwt-secret-min-32-chars`, `ADMIN_EMAIL=admin@afcfta-zlecaf.com`, `ADMIN_PASSWORD=change-me-strong-password`. `backend/services/user_auth_service.py:31` lit `os.environ["JWT_SECRET"]` **sans contrôle de force ni de placeholder**. `backend/server.py:279-311` crée un utilisateur `role:"admin"` depuis l'environnement et **re-applique ce mot de passe à chaque démarrage** (:305-309).

**Impact.** Si le `.env` de prod a été copié de l'exemple sans tout changer, n'importe qui peut se connecter en admin avec des identifiants publics, ou **forger des jetons de session HS256** (le `JWT_SECRET` étant connu). Le ré-amorçage empêche en plus de corriger un mot de passe admin depuis la base.

**Correctif :** refuser le démarrage sur un placeholder ou un secret < 32 octets (étendre `backend/validate_env.py`) ; amorcer l'admin **une seule fois**, ne jamais re-synchroniser le mot de passe ; laisser les valeurs d'exemple vides.

> **Vérification du 01/11/2026.** `JWT_SECRET` de production n'est **aucune** des deux valeurs d'exemple publiques du dépôt (`your-jwt-secret-min-32-chars`, `CHANGEZ-MOI-32-caracteres-minimum`). Test sans accès à aucun compte : un jeton signé avec chaque valeur, pour un identifiant d'utilisateur inexistant, est refusé comme « Session invalide » (comme le jeton témoin) au lieu d'« Utilisateur introuvable ». La fabrication de sessions à partir d'un secret connu est donc écartée. `SECRET_KEY` n'est plus utilisé par le backend (seul un commentaire obsolète le cite) : sa valeur est sans effet. Restent à confirmer par l'exploitant, sans les afficher : la longueur de `JWT_SECRET` et le mot de passe admin (§6).
>
> **Correctif appliqué (PR #750).** `backend/security_config.py` : en production, un `JWT_SECRET` d'exemple public arrête le démarrage ; un secret de moins de 32 caractères déclenche une alerte CRITICAL sans couper le service (même chose hors production) ; un `ADMIN_PASSWORD` d'exemple ou de moins de 12 caractères n'est jamais appliqué, et si c'est déjà le mot de passe du compte, celui-ci est verrouillé jusqu'à ce qu'un mot de passe solide le resynchronise. Le ré-amorçage depuis `.env` est conservé : c'est aujourd'hui le seul moyen de changer le mot de passe admin, l'application n'ayant pas de changement de mot de passe. Tests : `backend/tests/test_security_config.py`.

### E4 — Opérations admin de cache exposées sans authentification via GraphQL
**Confiance : Confirmé (runtime hors-ligne).** Le routeur GraphQL n'a que `_auth` (`routes/__init__.py:570`), donc anonyme. Ses mutations `invalidateCache`/`warmCache` et requêtes `getCacheStats`/`getPerformanceSummary` (`api/graphql/schema.py:224-243,183-202`) n'ont **aucune** vérification de rôle, alors que leurs équivalents REST exigent `require_admin` (`routes/performance.py`, `routes/cache.py`). Reproduit : `POST /api/graphql {invalidateCache(countryCode:"*")}` → `200` ; REST `DELETE /api/performance/cache/country/MAR` → `403 Admin tier required`. (Effet réel seulement avec Redis actif en prod.) De plus le repli renvoie `str(exc)` au client (:410-412) et le playground + le SDL complet sont servis. **Correctif :** mêmes contrôles admin qu'en REST sur les résolveurs cache/perf ; supprimer `str(exc)` ; désactiver le playground/SDL en production (`APP_ENV`).

### E5 — Détection d'IP client falsifiable → usurpation du pays de facturation et contournement du rate-limit
**Confiance : Confirmé (code) ; dépend de `TRUSTED_PROXY_HOPS` réel (§6).** `backend/services/geo_service.py:97-116` choisit l'entrée `len(entries) - TRUSTED_PROXY_HOPS` de `X-Forwarded-For`. Cette IP sert à la fois au rate-limiter (`rate_limiter.py`) **et** à la détection du pays qui impose le prestataire de paiement. En préprod j'ai observé `trusted_proxy_hops=3` et l'IP n'était pas falsifiable via les en-têtes (bon signe). Mais si la valeur déployée est trop basse pour l'ingress réel, une entrée XFF fournie par le client devient l'IP comptée : l'attaquant usurpe son pays (choix Stripe/DZD Chargily) et fragmente le compteur de débit. **Correctif :** ne faire confiance aux en-têtes `X-Forwarded-For`/`CF-*` que depuis les plages d'IP de l'ingress ; conserver le secret `CLOUDFLARE_EDGE_SECRET` (déjà prévu) comme preuve de provenance.

---

## 4. Constats MOYENS 🟡

| # | Constat | Preuve | Correctif |
|---|---|---|---|
| **M1** | **Chaîne CI** : actions épinglées par tag mutable (`peter-evans/create-pull-request@v7`), jetons `contents: write` + `persist-credentials: true`, PAT à portée `repo`, installs non figés (`pip install requests …`), pushes directs sur `main` via `GITHUB_TOKEN` (non testés par la CI) | `auto_update_data.yml:22-25,38,50,113,122` ; `production_etl.yml` ; `tariff_crawl.yml`, `veille_eth_crawl.yml` | Épingler par SHA ; PAT fine-grained limité au dépôt ou GitHub App ; `persist-credentials:false` ; `pip-compile --generate-hashes` ; transformer les pushes en PR ; `permissions: contents: read` par défaut |
| **M2** | **`.dockerignore`** : `.env`/`.env.*` ne matchent qu'à la racine ; `COPY . /app` embarque les `.env` imbriqués et `.local_backups/*.bak` (qui contiendraient `SECRET_KEY`, `MONGO_URL`) dans l'image | `.dockerignore:12-13`, `Dockerfile:25`, `.local_backups/RESTORE_NOTES.md:7-8` | Ajouter `**/.env`, `**/.env.*`, `!**/.env.example`, `.local_backups`, `**/*.bak`, `**/node_modules`, `**/.venv*`, `.emergent`, `**/*.mmdb` |
| **M3** | **Dépendances vulnérables** sur des chemins actifs (voir annexe A) : starlette 0.37.2, pyjwt 2.10.1, cryptography 46.0.2, urllib3 2.5.0, pymongo 4.17.0 ; côté front dompurify (critique), axios, react-router | `pip-audit`, `npm/yarn audit` | Montées de version de l'annexe A ; faire pointer les middlewares sur `request.scope["path"]` |
| **M4** | **Verrouillage de compte par email** : 5 échecs → blocage 15 min, indexé sur l'email seul → un tiers qui connaît l'email bloque la connexion de la victime à volonté | `routes/user_auth.py:244,250-291` | Combiner signal par compte + throttle par IP/appareil + CAPTCHA/backoff ; ne pas bloquer durement sur l'email seul |
| **M5** | **Injection de formules CSV/Excel** : `sector` (query) et des champs Mongo écrits tels quels dans les cellules ; `=HYPERLINK(...)` ressort en formule `<f>` | `routes/regional_analytics.py:145-148` → `dashboard/export_services.py:95-105` ; `routers/export_router.py` ; `frontend/src/components/common/ExportTools.jsx:100` | Préfixer par `'` toute cellule commençant par `= + - @ \t \r` ; valider `sector` contre une liste |
| **M6** | **Client Supabase par défaut** : `createClient(url,key)` sans options → `persistSession` (refresh token en `localStorage`), `flowType:'implicit'`, `detectSessionInUrl:true` → login CSRF (`#access_token=…`) et exfiltration de jeton via tout XSS | `frontend/src/lib/supabase.js:9` ; `context/AuthContext.jsx:43-55,89,143` | `auth:{flowType:'pkce'}` ; après `/api/auth/session`, `signOut({scope:'local'})` ; URLs de redirection **exactes** dans le tableau de bord Supabase + rotation des refresh tokens |
| **M7** | **Script tiers sans SRI + iframe sans sandbox** : Chart.js depuis cdnjs sans `integrity`, chargé dans une iframe same-origin sans `sandbox` (ouverte dès l'onglet Outils) | `frontend/public/tools/afcfta_business_atlas.html:9` ; `components/tools/BusinessAtlasModule.jsx:74` | Auto-héberger Chart.js ou SRI + `crossorigin` ; `sandbox="allow-scripts"` ; `textContent` au lieu de `innerHTML` (atlas:1165) |
| **M8** | **`HTTPS_ENABLED=false`** en préprod : cookies de session/CSRF **sans `Secure`**, pas de HSTS (confirmé : `csrf_token=…; SameSite=lax` sans `Secure` sur la préprod) | `.env.example` (avertissement), `middlewares/*`, `routes/user_auth.py:41` | Mettre `HTTPS_ENABLED=true` partout où l'app est servie en HTTPS. ✅ **Clos le 01/11/2026** : `HTTPS_ENABLED=true` et `APP_ENV=production` sur le pod ; vérifié de l'extérieur : HSTS `max-age=31536000`, cookies `Secure; SameSite=none; Partitioned`, aucune documentation d'API exposée |
| **M9** | **Divulgation via `str(exc)`** renvoyé au client sur de nombreuses routes ; `/docs`,`/redoc`,`/openapi.json` actifs si `APP_ENV != production` | `regional_analytics.py`, `uma_regions.py`, `investment_intelligence.py`, `banking.py:366`, `news.py:82` ; `server.py:132-135` | Messages génériques + log serveur ; forcer `APP_ENV=production` |
| **M10** | **Middlewares de sécurité en `try/except ImportError`** : un déploiement partiel démarre **sans** CSP/CSRF/rate-limit, en silence | `backend/server.py:173-197` | Échec « fail-closed » : refuser de démarrer si un middleware de sécurité manque en prod |
| **M11** | **WebSocket** : clé API en query string (journalisée par les proxys), auth ouverte si Mongo absent, pas de contrôle d'`Origin` ni de plafond de connexions | `backend/api/websocket/handlers.py:35,191…` | Clé via `Sec-WebSocket-Protocol` ou 1ᵉʳ message ; valider `Origin` ; plafonner ; garder le chemin `no_db` fermé |

---

## 5. Constats FAIBLES / INFO 🟢

- **INFO-1 — `jekyll-gh-pages.yml` publierait la racine du dépôt** (`source: ./`, `_config.yml` n'exclut pas les `*.md` racine ni `reports/`) sur `afcfta-zlecaf.com` : docs internes (`INSTRUCTION_EMERGENT.md`, audits…) exposées. À désactiver (lié à C1).
  **Devenu actif le 01/11/2026 à 21:57 UTC** : à l'activation de Pages en mode « Deploy from a branch », GitHub a commité `CNAME = www.afcfta-zlecaf.com` sur `main`, puis la publication intégrée et l'ancien workflow ont mis en ligne la racine de `main` — `INSTRUCTION_EMERGENT.html`, `ETAT_APP_POUR_EMERGENT.html`, `DEPLOYMENT.html`, `AUDIT_APPROFONDI.html`, `AUDIT_FIXES_2026-09-08.html`, `CLAUDE.html`, `data_update_report.json`… (vérifiés en 200 ; aucun secret, le présent audit n'étant pas sur `main`). **Correctif :** Settings → Pages → Source = « GitHub Actions », puis fusion de la PR #750, qui supprime ce workflow et ne publie que `site/` ; ou, en attendant, « Unpublish site ». **Exposition arrêtée le soir même** : site dépublié, les pages répondent de nouveau 404 (domaine vérifié, sans risque de détournement).
- **INFO-2 — CSP autorise `cdn.jsdelivr.net`** (`middlewares/security_headers.py`) — hôte fourre-tout, contournement CSP connu — uniquement pour le playground GraphQL (déprécié). Retirer jsDelivr de la CSP et supprimer le playground.
- **INFO-3 — HTML servi par `vite preview` sans en-têtes de sécurité** (`frontend/package.json`, `vite.config.js:98` `allowedHosts:true`). Préférer servir `frontend/build` depuis FastAPI (déjà supporté, `server.py:431-447`) pour bénéficier des en-têtes, **ou** définir `preview.headers`. Pas de sink XSS trouvé dans `src/` (React échappe, `javascript:` bloqué) → faible.
- **INFO-4 — CSRF double-submit non lié à la session**, cookie sans préfixe `__Host-`, session `SameSite=None` (`csrf_protection.py`, `services/csrf.js`). Défense en profondeur ; l'allowlist CORS exacte bloque l'attaque pratique. Renommer en `__Host-…`, dériver le jeton CSRF de la session par HMAC.
- **INFO-5 — `docker-compose`** : le backend utilise les identifiants **root** Mongo, mot de passe Redis en ligne de commande, origine `http://localhost:3000` autorisée avec credentials, images par tag. Utilisateur Mongo `readWrite` dédié, origines prod only, images par digest.
- **INFO-6 — `.replit`** : backend public `0.0.0.0:5000` sans `APP_ENV` (donc `/docs` actif) ni `HTTPS_ENABLED` ; hook `post-merge.sh` fait `pip/npm install` (scripts exécutés, erreurs masquées). Fixer `APP_ENV`/`HTTPS_ENABLED`, `npm ci --ignore-scripts`.
- **INFO-7 — TLS désactivé dans deux collecteurs** : `scripts/tun_recrawl_rates.py:30-31` (`CERT_NONE`) et `tariff_engine/ingest.py:38` (`verify=False` en repli). CLI/crawl, pas exposé HTTP → faible, mais contredit la doctrine du projet. Restaurer la vérification + certificat intermédiaire.
- **INFO-8 — `cleanup-branches.yml:9`** : `dry_run` par défaut `"false"` → un run manuel par défaut est destructif. Passer le défaut à `"true"`.
- **INFO-9 — `AdminProjectsPage.jsx`** stocke la clé admin en `localStorage` (`:39,107`) — composant **non importé** aujourd'hui (absent du bundle). Le supprimer ou passer par un rôle admin sur la session serveur.
- **INFO-10 — Hygiène des lockfiles** : `package-lock.json` sans `integrity`/`resolved` et périmé (il manque `@supabase/supabase-js`) alors que les déploiements utilisent **yarn** ; `requirements.txt` non figé (`stripe>=9`, `anthropic>=0.40`…) et divergent entre racine (Docker) et `backend/` (Emergent) ; outils de dev livrés en prod. Un seul lockfile yarn figé + un `requirements` compilé et haché.

---

## 6. Vérifications à faire de votre côté (dépendent de l'exécution)

Ces points ne peuvent être tranchés que par vous, sur l'instance de production :

1. **Jeton OEC (C2)** : ✅ vérifié le 01/11/2026 — aucun jeton configuré en production, artefacts expirés. Seul point à confirmer : si tu as un jeton OEC ou une clé Comtrade ailleurs (secret GitHub `OEC_API_TOKEN`, autre environnement), le régénérer par précaution.
2. **Secrets d'exemple (E3)** : ✅ **clos le 01/11/2026.** Contrôle exploitant sur le pod Emergent, sans affichage des valeurs : `JWT_SECRET` 64 caractères, `ADMIN_PASSWORD` 24 caractères, aucune valeur d'exemple. `JWT_SECRET` n'est pas non plus une valeur d'exemple publique (vérifié à distance) ; `SECRET_KEY` est inutilisé. Le même contrôle a montré `APP_ENV` et `HTTPS_ENABLED` absents (défauts `development` et `false`) : voir M8. À confirmer dans le terminal Emergent, avec un contrôle qui n'affiche aucune valeur : longueur de `JWT_SECRET` (≥ 32) et mot de passe admin (ni exemple, ni moins de 12 caractères). La PR #750 peut être fusionnée sans attendre : seul un secret d'exemple public, vérifié absent, bloquerait le démarrage.
3. **Domaine (C1)** : confirmer dans GitHub → Settings → Pages s'il existe un « verified domain » ; décider de l'application cible de `afcfta-zlecaf.com`.
4. **IP client (E5)** : `GET /api/billing/geo-diagnostic` avec `X-Forwarded-For: 203.0.113.9, 198.51.100.7` ; le `client_ip` renvoyé ne doit être **aucune** de ces deux valeurs.
5. **Supabase (M6)** : dans le tableau de bord, vérifier que les « Redirect URLs » ne contiennent **aucun** wildcard sur un domaine partagé (`*.emergentagent.com`).
6. **Déploiement (C3)** : confirmer sous quel utilisateur tournent les programmes supervisord et si `main` est protégée (y compris contre les Actions).

---

## 7. Ce qui est déjà bien fait (vérifié, aucun problème)

- **Pas d'injection** SQL (SQLAlchemy paramétré), NoSQL (filtres Mongo scalaires ou `ObjectId`), commande, désérialisation, SSTI, ni SSRF (hôtes sortants constants). **Pas de traversée de chemin** (`static_paths.py` confine via `relative_to`, testé avec `..`, encodage, symlinks, null bytes). **Pas de zip-slip** exploitable depuis une route.
- **Paiement** : montants côté serveur (`pricing.py`), aucune donnée de carte ne transite (Checkout hébergé), webhooks **Stripe** (signature) et **Chargily** (HMAC `compare_digest`) vérifiés, **idempotents** (index unique `payment_events.event_id` + libération sur échec), accès accordé **uniquement** par webhook. Chargily pose une `subscription_current_end` explicite (expiration correcte).
- **IA / denial-of-wallet** : les seuls appels à l'API Anthropic payante (`/api/ai/opportunities|profile|balance|value-chains`) sont derrière `check_ai_quota`, **sans** passerelle publique/no-DB (clé + quota mensuel requis). Les autres `/ai/*` sont des moteurs de calcul locaux.
- **Gestion des clés admin** : `require_admin` sur création/liste/suppression, clés `secrets.token_urlsafe(32)` hachées SHA-256, rendues une fois, validées contre une liste de tiers ; **pas de clé admin par défaut** en base ; les chaînes `zlecaf-admin-key`/`zlecaf-frontend-public-key` sont de simples placeholders, **refusées** (testé : `401`).
- **CORS** liste blanche exacte (la famille `*.preview.emergentagent.com` a été volontairement retirée), credentials-aware.
- **IDOR** : les ressources utilisateur sont toujours scopées à l'identité authentifiée ; aucun endpoint ne prend un `user_id` fourni par l'appelant.
- **Confinement JWT/alg** : session HS256 (`type==access` vérifié) ; le chemin Supabase n'accepte que ES256/RS256 (HS256 **rejeté**) et vérifie `audience`/`issuer` via JWKS → pas de confusion d'algorithme. Troncature bcrypt à 72 octets rejetée à l'inscription.
- **Aucun secret en clair** dans les fichiers suivis ni dans l'historique git : `backend/.env`, `frontend/.env`, `.github/secrets/COMTRADE_API_KEY`, `memory/test_credentials.md` ont **0 commit** (jamais versionnés). Aucun secret dans le bundle JS de production, pas de source maps.
- **Conteneur** Docker non-root, `read_only`, `tmpfs /tmp`, `cap_drop ALL`, services liés à `127.0.0.1`.

---

## 8. Plan de sécurisation (priorisé)

Mapping vers les constats entre parenthèses. Effort : XS < 1 j · S 1-3 j · M 1-2 sem · L ≥ 3 sem.

### Phase 0 — Urgences, à faire maintenant (XS/S)
1. ✅ **Revendiquer et sécuriser `afcfta-zlecaf.com`** (C1) ; désactiver `jekyll-gh-pages.yml` (INFO-1). — *XS* — domaine vérifié, `jekyll-gh-pages.yml` remplacé par `pages.yml` (seul `site/` est publié), page vitrine en ligne le 02/11/2026. Reste dans Cloudflare : mode SSL « Complet » et « Toujours utiliser HTTPS » (`http://` n'est pas encore redirigé).
2. ✅ **Masquer les secrets dans les journaux** (formateur, httpx à WARNING, `uvicorn.log` filtré en CI) — fait dans la PR #750 ; rotation inutile, aucun jeton n'étant configuré (C2). — *XS*
3. ✅ **Vérifier les secrets de prod** (E3) : `JWT_SECRET` (64 caractères) et `ADMIN_PASSWORD` (24) vérifiés sur le pod, aucune valeur d'exemple ; garde-fou de démarrage ajouté dans la PR #750. — *S*
4. **Verrouiller le déploiement sur `main`** + protéger `main` (revue + checks) (C3). — *S* — script corrigé dans la PR #750, contrôle des crons durci dans la PR #753 ; ruleset GitHub à activer par l'exploitant ; le pod Emergent doit être resynchronisé sur `main` pour en bénéficier.
5. ✅ **`HTTPS_ENABLED=true`** en production (M8), avec `APP_ENV=production` — fait et vérifié le 01/11/2026. — *XS*

### Phase 1 — Autorisation, DoS et durcissement (S/M)
6. **Appliquer les quotas aux anonymes** (ou exiger une identité) sur `/calcul`, `/reports/*`, `/v2/*`, exports (E1). — *M*
7. **Borner/déporter les points DoS** : regex GraphQL, `product-index`, `consultation`, `news force_refresh` (admin), scans `regional_data` en cache (E2). — *M*
8. **Protéger les résolveurs cache/perf GraphQL** par un contrôle admin ; retirer `str(exc)` ; désactiver playground/SDL en prod (E4). — *S*
9. **Fail-closed des middlewares de sécurité** (M10) ; neutraliser les formules CSV/Excel (M5) ; corriger le verrouillage de connexion (M4). — *S*
10. **Fiabiliser la détection d'IP** derrière l'ingress + `CLOUDFLARE_EDGE_SECRET` (E5). — *S*

### Phase 2 — Chaîne d'approvisionnement et secrets (M)
11. **Épingler les actions par SHA**, PAT fine-grained/GitHub App, `permissions: contents: read` par défaut, pushes → PR (M1). — *M*
12. **Figer les dépendances** : un lockfile yarn + `requirements` compilé/haché, `--ignore-scripts`, retirer outils de dev et paquets inutilisés (INFO-10). — *M*
13. **Monter les dépendances vulnérables** (annexe A) ; middlewares sur `request.scope["path"]` (M3). — *M*
14. **Corriger `.dockerignore`** (M2) ; durcir `docker-compose` (Mongo `readWrite`, digests) et `.replit` (INFO-5, INFO-6). — *S*
15. **Durcir le client Supabase** (PKCE, signOut local, redirections exactes) (M6) ; SRI + sandbox Business Atlas (M7). — *S*

### Phase 3 — Robustesse des comptes (M/L)
16. **Vérification d'email, réinitialisation de mot de passe, révocation de session** (jetons d'accès courts + refresh) — pistes déjà étudiées dans `audits/AUDIT_INSCRIPTION_PAIEMENT_SUPABASE_MOBILE_2026-09-25.md` (migration Supabase Auth). — *L*
17. **Observabilité sécurité** : journal structuré requête/réponse sans secret, alertes sur `/etc/cron.d` et `.emergent/cron/webhook-crons`, revue régulière des artefacts CI. — *M*

---

## Annexe A — Dépendances à mettre à jour

`[E]` = `backend/requirements.txt` (Emergent) · `[D]` = `requirements.txt` racine (Docker/CI).

| Paquet | Actuel | Corrigé | Pertinent runtime |
|---|---|---|---|
| starlette (via fastapi 0.110.1) [E,D] | 0.37.2 | ≥ 1.3.1 (FastAPI 0.162) | oui (`request.url` dans les middlewares) |
| PyJWT [E,D] | 2.10.1 | ≥ 2.15.0 | oui (JWKS Supabase + sessions HS256) |
| cryptography [E,D] | 46.0.2 | ≥ 50.0.0 (min 46.0.7) | oui (OpenSSL embarqué) |
| urllib3 [E] | 2.5.0 | ≥ 2.8.0 | oui (fetchers) |
| pymongo [E,D] | 4.17.0 | ≥ 4.18.3 | oui |
| certifi [E] | 2025.10.5 | ≥ 2026.10.18 | oui |
| aiosmtplib [D] | 3.0.1 | ≥ 5.1.2 | oui (image Docker) |
| requests [E,D] | 2.32.5 | ≥ 2.33.0 | faible |
| python-multipart [E,D] | 0.0.20 | ≥ 0.0.31 | faible (pas d'endpoint Form) |
| python-jose / passlib / ecdsa / aioredis [E] | — | **retirer** (inutilisés/abandonnés) | non |
| dompurify (via jspdf) | 3.4.12 | ≥ 3.4.17 | non (`jsPDF.html()` non utilisé) |
| axios | 1.15.2 | ≥ 1.21.0 | partiel (bundle navigateur) |
| react-router(-dom) | 7.18.1 | ≥ 7.18.2 | non (non importé) |
| vite [dev, sert la prod via `preview`] | 6.4.3 | ≥ 6.4.5 | seulement si serveur exposé |

`pip-audit` : 20 paquets vulnérables côté `backend/`, 11 côté racine. `npm audit` (prod) : 11 (1 critique, 8 high). Détails bruts conservés sous `pipaudit/`, `npm-audit/`, `yarn-audit/`.

---

*Audit réalisé par analyse du dépôt + revues parallèles (autorisation/logique métier, classes de vulnérabilités injection/SSRF/fichiers, frontend/CI/infra/dépendances) et tests passifs en lecture seule. Ce document n'est pas une certification ; les points « Plausible » du §6 doivent être confirmés sur l'instance de production.*
