# Passage en production — liste de contrôle

Ouvrir le site au public, dans l'ordre : décisions, réglages, textes, vérifications.
« À confirmer » signale une information absente du dépôt ; la ligne dit où la trouver.
Aucune valeur de secret ne doit être affichée ni collée dans une conversation
(docs/ACTIVER_SUPABASE.md:21-22 ; docs/INSTRUCTION_POD_EMERGENT.md:344-349).

Les numéros de ligne renvoient à l'état du dépôt après la PR #787 (07/11/2026).
Les cases cochées sont des décisions déjà prises par l'exploitant.

`<domaine>` désigne l'hôte définitif de l'application, choisi au point 1.1.

## 1. Décisions à prendre

- [ ] **1.1 Domaine définitif de l'application.** `www.afcfta-zlecaf.com` sert aujourd'hui la vitrine GitHub Pages (`site/CNAME` ; `.github/workflows/pages.yml:7-9`). L'application tourne sur l'aperçu `*.preview.emergentagent.com`, « éphémère et non destinée à la production » (audit C1, point 3, :56 ; §6.3, :265). Choisir l'hôte de l'application et celui de la vitrine. Interface et API sur la même origine : c'est la configuration vérifiée (audit E6, :213). Sinon, il faut aussi `VITE_BACKEND_URL` (connect-src, audit INFO-3, :248) et `ALLOWED_ORIGINS`.
- [x] **1.2 `ADMIN_ACCES_ILLIMITE` : maintenu à `true` en production** (décision de l'exploitant du 06/11/2026 ; audit E1 « Reste », :133 ; `backend/entitlements.py:281-288`). Il vaut `true` sur le pod (audit :320) et dans le gabarit (`docs/emergent.env.template:63-67`) ; le défaut, sans la variable, est `false` (`.env.example:53`) : la poser sur le déploiement de production. Conséquence acceptée : une session admin volée donne tous les modules sans quota, le téléchargement des tarifs et les exports CSV et Excel. Le mot de passe admin doit donc rester fort (contrôlé au démarrage, audit E3).
- [ ] **1.3 Accès de l'équipe de maintenance** (« à décider pour la production », audit :133). Qui garde un accès au pod Emergent, au compte admin de l'application et aux tableaux de bord Supabase, Stripe, Chargily, Resend, Cloudflare et GitHub ? Tous les agents agissent sous l'identité du propriétaire GitHub (audit C3, :108). Liste à établir hors du dépôt.
- [x] **1.4 Envoi des e-mails : Zoho pour le backend, Resend pour les comptes** (décision du 06/11/2026). Le backend (bienvenue, abonnement et paiement, livraison des achats, formulaire de contact) envoie par `smtp.zoho.com` : 17 envois réussis, 0 échec, relevés sur le pod (`docs/ACTIVER_SUPABASE.md:51-55`). Supabase envoie les e-mails de compte par Resend. `confidentialite.html:69-70` est aligné. Reste à confirmer chez Zoho : le volume d'envoi permis par l'offre souscrite (`docs/ACTIVER_SUPABASE.md:45-47` décrit l'offre gratuite, qui refuse le SMTP).
- [ ] **1.5 Volume d'e-mails.** L'offre gratuite de Resend permet 3 000 e-mails par mois et 100 par jour (`docs/ACTIVER_SUPABASE.md:89-90`). Choisir l'offre selon le trafic attendu (tarifs : à confirmer chez Resend).
- [x] **1.5 bis Exports** (décision de l'exploitant du 06/11/2026, audit E1 « Exports ») : CSV, Excel et bouton JSON réservés à la session admin, aucune exception pour une clé API ; PDF permis à toutes les formules, sauf dans le module Outils (qui n'en a aucun) ; quotas de PDF par formule à définir plus tard. À faire avant l'ouverture :
  - décider comment prévenir les abonnés actuels : Pro et Business perdent l'Excel, Starter le CSV, les plans API vendus le CSV et l'Excel ;
  - corriger les descriptions des produits Starter et Pro dans le tableau de bord Stripe (voir Stripe ci-dessous), et vérifier celles de Chargily ;
  - « Rapports PDF automatisés » (Business, `pricing.html`) : vérifier qu'une fonction y correspond, sinon retirer la mention.
- [ ] **1.6 Chargily dès l'ouverture ?** Avec `CHARGILY_ENABLED=false`, la branche algérienne répond 501 (gabarit :101-102). Or les CGU promettent CIB/Edahabia aux comptes créés en Algérie (`cgu.html:57-60`), conformément au contrôle des changes (`docs/CLOUDFLARE_SETUP.md:3-5`). Deux choix : ouvrir avec Chargily en mode live, ou modifier les CGU.
- [ ] **1.7 TVA par Stripe Tax.** Les CGU annoncent une TVA calculée automatiquement par Stripe (`cgu.html:56`). Il faut pour cela `STRIPE_AUTOMATIC_TAX=true` et Stripe Tax entièrement configuré (adresse d'origine, immatriculations). Sinon, Stripe refuse de créer la session de paiement (gabarit :88-90 ; `backend/services/stripe_service.py:83-92`). Deux choix : activer Stripe Tax, ou modifier les CGU.
- [ ] **1.8 Projet Supabase : celui de la préproduction ou un projet dédié ?** Un projet n'a qu'une Site URL, et les liens des e-mails la reprennent (`{{ .SiteURL }}`, `docs/ACTIVER_SUPABASE.md:98`). Si la préproduction garde le même projet, ses e-mails de confirmation renverront vers la production.
- [ ] **1.9 Aperçu Emergent dans une iframe.** `frame-ancestors https://app.emergent.sh` (`frontend/securite/entetes.js:28-29`) et le cookie `SameSite=None` (`backend/middlewares/csrf_protection.py:47-61`) ne servent qu'à l'aperçu (audit INFO-4 « Reste », :249). Les garder sur le domaine définitif, ou les restreindre (ce serait un changement de code, hors de cette liste).
- [ ] **1.10 Risques résiduels à accepter par écrit :**
  - E2 (« Restent », :151-155) : la première construction de l'inventaire régional prend environ 10 s de CPU après un redémarrage ; le cache du socle est limité à 4 pays ; si Redis tombe après s'être connecté, chaque appel retente la connexion. Le délai de `googlenewsdecoder` et l'attente des deux clients Redis sont corrigés (06/11/2026) ;
  - E5 (:202-204) ;
  - INFO-7 (:252) : `jort_crawler.py` lit son site en http (collecteur, pas le site public) ;
  - INFO-10 (:255) : pas d'empreintes de paquets, aucune alerte sur une nouvelle vulnérabilité ;
  - point 17 (« Limites », :343) ;
  - un seul worker (`DEPLOYMENT.md:260-263`).

## 2. Réglages chez les prestataires

### Emergent

- [ ] **Déploiement de production.** Le dépôt ne décrit que le pod d'aperçu synchronisé par `sync_emergent.sh` (`docs/DEPLOYER_SUR_EMERGENT.md:14-34`). Rien n'y décrit la mise en production d'Emergent (« Deploy », domaine personnalisé). À confirmer auprès d'Emergent :
  - comment rattacher `<domaine>` ;
  - si ce déploiement reprend le pod d'aperçu (supervisord, `/app/backend/.env`, MongoDB) ou en crée un distinct (`docs/INSTRUCTION_POD_EMERGENT.md:16-18, 73-75`). Le gabarit suppose un hôte `*.emergent.host` (`docs/emergent.env.template:25`).
- [ ] **À confirmer auprès d'Emergent :**
  - le déploiement de production ne se met pas en veille (l'aperçu répond 404 quand personne n'est actif, `docs/INSTRUCTION_POD_EMERGENT.md:359-361`) ;
  - il tourne sans `--reload` (audit, point 17, :343) ;
  - l'utilisateur des programmes supervisord (audit §6.6, :273) ;
  - le pays des serveurs (`confidentialite.html:66`) ;
  - la durée de conservation des journaux (audit :343) ;
  - la sauvegarde de MongoDB et sa conservation en cas de reconstruction (`docs/INSTRUCTION_POD_EMERGENT.md:339-341`).
- [ ] **`/app/backend/.env` de production :**
  - `APP_ENV=production` et `HTTPS_ENABLED=true` (audit M8, :236 ; gabarit :13, :26) ;
  - `MONGO_URL` renseigné : sans base, ni les quotas ni les clés API ne sont appliqués (gabarit :35-38 ; audit E1, :127) ;
  - `ALLOWED_ORIGINS` = les origines exactes de `<domaine>`, aucun autre aperçu (audit E6, :213 ; `backend/cors_config.py:42-52`) ;
  - `FRONTEND_URL` (gabarit :28) ;
  - `BILLING_SUCCESS_URL` et `BILLING_CANCEL_URL` sur `<domaine>/pricing.html`. La valeur par défaut, `https://afcfta-zlecaf.com/pricing.html` (`backend/routes/billing.py:59-75`), pointe aujourd'hui sur la vitrine et non sur l'application ;
  - `JWT_SECRET` d'au moins 32 caractères et `ADMIN_PASSWORD` d'au moins 12, contrôlés sans affichage (audit §6.2, :264) ;
  - `ADMIN_ACCES_ILLIMITE` selon le point 1.2 ;
  - `UVICORN_FORWARDED_ALLOW_IPS` et `FORWARDED_ALLOW_IPS` jamais à `*` (gabarit :124-130 ; audit E5, :204).
- [ ] **`/app/frontend/.env`** : `VITE_SUPABASE_URL` et `VITE_SUPABASE_PUBLISHABLE_KEY` du projet retenu au point 1.8, puis une synchronisation, qui recompile l'interface (`docs/ACTIVER_SUPABASE.md:161-170`).
- [ ] **Synchronisations** : par le terminal Emergent, jamais par le chat de l'agent, et jamais de secret dans le chat ; les clés se saisissent par la carte sécurisée (`docs/INSTRUCTION_POD_EMERGENT.md:25-48`).
- [ ] **« Save to GitHub » d'Emergent** sur une branche dédiée, jamais `main` (audit C3, :108 ; phase 0.4, :299).

### GitHub

- [ ] **`URL_SANTE_STATUS`** : repointer la variable de dépôt sur `https://<domaine>/api/health/status` (`docs/INSTRUCTION_POD_EMERGENT.md:364-368`). La tâche ne lit qu'une adresse (`.github/workflows/surveillance_securite.yml:31`) : l'aperçu ne sera plus surveillé. Le contrôle horaire ne tourne que sous le supervisord d'Emergent (audit :343) : à confirmer qu'il tourne bien sur le déploiement de production.
- [ ] **Vitrine** : le domaine reste vérifié et Pages ne publie que `site/` (audit phase 0.1, :296 ; INFO-1, :246). Si la vitrine change d'hôte : `site/CNAME` et le domaine dans Settings → Pages (`pages.yml:7-9`).
- [ ] **Jeton OEC ou clé Comtrade** gardés ailleurs : les régénérer par précaution (audit §6.1, :263).

### Supabase

- [ ] **Authentication → URL Configuration** :
  - Site URL = `https://<domaine>`, sans `/` final ;
  - Redirect URLs = la même adresse, exacte : aucun `*` ni `**`, et surtout aucun `*.emergentagent.com` ;
  - retirer l'adresse de l'aperçu si elle n'est plus servie.

  Sources : `docs/ACTIVER_SUPABASE.md:26-31` ; audit §6.5, :272 ; M6, :234.
- [ ] **Paramètres à vérifier :**
  - Confirm email et Secure email change activés (`docs/ACTIVER_SUPABASE.md:35-41`) ;
  - SMTP Resend : hôte `smtp.resend.com`, port 465, identifiant `resend`, expéditeur `noreply@afcfta-zlecaf.com` (`:70-80`) ;
  - les trois modèles `token_hash` (`:104-112`) ;
  - jeton d'accès de 3 600 s et rotation des jetons de rafraîchissement (`:130-137`).
- [ ] **Région du projet** : à confirmer dans Project Settings. La page Confidentialité déclare « Union européenne » (`confidentialite.html:64`).

### Resend

- [ ] **Domaine** : `afcfta-zlecaf.com` marqué « Verified », avec `send` et `rsend` en DNS only (nuage gris) chez Cloudflare (`docs/ACTIVER_SUPABASE.md:57-66`).
- [ ] **Clés** : la clé `supabase-smtp` a la permission Sending access, limitée au domaine ; la clé « Onboarding », qui a tous les droits, est supprimée (`docs/ACTIVER_SUPABASE.md:67-69`).

### Cloudflare

- [ ] **Enregistrement de `<domaine>` vers Emergent.** Le mode (proxy orange ou DNS only) est à confirmer selon les instructions de domaine personnalisé d'Emergent, absentes du dépôt. Garder le mode SSL « Complet » et la redirection `http://*` → `https://` (audit phase 0.1, :296). Le mode « Complet (strict) » demande un certificat d'origine valide : à confirmer avec Emergent.
- [ ] **Si l'enregistrement est proxifié :**
  - ajouter la Transform Rule `X-Edge-Secret` et la même valeur dans `CLOUDFLARE_EDGE_SECRET` (`docs/CLOUDFLARE_SETUP.md:47-71`) ;
  - l'ingress d'Emergent ne transmet peut-être pas ces en-têtes (non confirmé) : la base MaxMind sert de repli (`CLOUDFLARE_SETUP.md:157-162` ; gabarit :131-135) ;
  - ne jamais régler `TRUST_CLOUDFLARE_HEADERS=true` sur une origine ouverte (`CLOUDFLARE_SETUP.md:87-96`).
- [ ] **`TRUSTED_PROXY_HOPS`** : la re-mesurer sur `<domaine>` (gabarit :142-150). La valeur 3 a été mesurée sur l'aperçu (audit E5, :196) ; un relais de plus change le compte. Trop bas : une IP d'infrastructure commune à tous les visiteurs. Trop haut : une IP falsifiable (audit :191).
- [ ] **`/api/health/status`** : ne pas le bloquer aux exécuteurs GitHub (`docs/INSTRUCTION_POD_EMERGENT.md:357-359`).

### Stripe (mode live)

- [ ] **Vérification du compte**, qui débloque le mode live et les virements (`docs/PLAN_INTEGRATION_STRIPE_CHARGELY.md:4-6`) : à confirmer dans le tableau de bord.
- [ ] **Clés et prix** : clés `sk_live_`/`pk_live_`, puis `scripts/stripe_setup.py` relancé avec la clé live et les nouveaux `STRIPE_PRICE_*` reportés. Le script ne modifie pas un produit déjà créé : les descriptions Starter et Pro (plus de CSV ni d'Excel, point 1.5 bis) sont à reprendre aussi dans le tableau de bord. Les identifiants du gabarit sont ceux du mode test (gabarit :80-82, :91-96). Archiver les anciens prix en USD (`scripts/stripe_setup.py:23-24`).
- [ ] **Webhook live** sur `https://<domaine>/api/billing/webhook`, avec son nouveau `STRIPE_WEBHOOK_SECRET` (gabarit :85-87). Événements à cocher, ceux que traite le code : `checkout.session.completed`, `customer.subscription.updated`, `customer.subscription.deleted`, `invoice.payment_failed` (`backend/routes/billing.py:645-732`).
- [ ] **Stripe Tax** selon le point 1.7.
- [ ] **Portail client en mode live** : à confirmer dans le tableau de bord qu'il est activé. « Gérer mon abonnement » l'ouvre (`cgu.html:66`) et y revient par `BILLING_CANCEL_URL` (`billing.py:263, 458`).

### Chargily (mode live, si retenu au point 1.6)

- [ ] **Réglages** : `CHARGILY_ENABLED=true`, clé secrète et secret de webhook du mode live (gabarit :101-105). `CHARGILY_API_BASE` doit viser l'API live ; défaut : `https://pay.chargily.net/api/v2` (`backend/services/chargily_service.py:34`). À confirmer dans la documentation de Chargily.
- [ ] **Webhook** `https://<domaine>/api/billing/chargily/webhook` (`billing.py:10`), déclaré dans le tableau de bord de Chargily : le code n'envoie aucune adresse de webhook avec le paiement (`chargily_service.py:93-101`). À confirmer côté Chargily.

## 3. Textes légaux

- [ ] **`confidentialite.html`, passages `<mark>`** :
  - :38 date d'entrée en vigueur ;
  - :43 dénomination, forme juridique, siège, n° RC/NIF ;
  - :44 délégué à la protection des données ;
  - :66 pays des serveurs, à demander à Emergent ;
  - :74 autorisation de l'ANPDP (loi n° 18-07) ;
  - :82 durée de conservation comptable ;
  - :83 durée de conservation des messages de contact.
- [ ] **`confidentialite.html:81`** : déclarer la durée de conservation des journaux du pod, à demander à Emergent (audit, point 17, :343).
- [ ] **`cgu.html`, passages `<mark>`** :
  - :35 date d'entrée en vigueur ;
  - :38 éditeur (dénomination, forme, capital, siège, n° RC/NIF), directeur de la publication, adresse de l'hébergeur ;
  - :56 régime de TVA de Chargily ;
  - :71 droit de rétractation ;
  - :84 dénomination ;
  - :87 plafond de responsabilité ;
  - :96 droit applicable et ville du tribunal.
- [ ] **Nom de la société** : le même partout. On trouve aujourd'hui « ZLECAf Intelligence » (`cgu.html:6, 38`), « Intelligence Trade Africa (dénomination en projet) » (`cgu.html:38`) et « AF Trade Intelligence » comme expéditeur des e-mails (`docs/ACTIVER_SUPABASE.md:76`).
- [ ] **Relecture par un juriste** des deux pages, avant publication (commentaires de tête : `confidentialite.html:8-13`, `cgu.html:8-14`).
- [ ] **Versions** : après toute modification de fond, incrémenter `TERMS_VERSION` (`frontend/src/lib/supabase.js:49`, aujourd'hui `2026-11`) et la version affichée. `cgu.html:35` affiche encore `2026-09`, `confidentialite.html:38` affiche `2026-11`.
- [ ] **Prix** : ceux de `pricing.html`, qui fait partie des CGU (`cgu.html:56`), doivent égaler la grille de `backend/pricing.py:34-40` et les prix live de Stripe.

## 4. Vérifications après la bascule (de l'extérieur, lecture seule)

- [ ] **`https://<domaine>/api/health`** : 200, base connectée (audit :334).
- [ ] **En-têtes de sécurité** :
  - HSTS `max-age=31536000` (audit M8, :236) ;
  - cookie `__Host-csrf_token` en `Secure`, `Path=/` et `Partitioned`, sans `Domain` (INFO-4, :249) ;
  - CSP de la page en `script-src 'self' 'nonce-…'`, sans CDN, et aucune violation dans la console (INFO-3, :248 ; :319).
- [ ] **CORS** : avec `Origin: https://afcfta.trade` ou `http://localhost:3000`, aucun `Access-Control-Allow-Origin` ; l'interface appelle l'API sans erreur (audit E6, :217-221).
- [ ] **IP client** : refaire la procédure §6.4 sur `<domaine>` (audit :266-271). Attendus : `proxy_peer_trusted` = `true`, `client_ip` = l'IP réelle, en-têtes forgés ignorés, y compris sur deux lignes.
- [ ] **Pays forgé** : `/api/billing/payment-context` avec `-H 'CF-IPCountry: DZ'` doit renvoyer `locked: false` (`docs/CLOUDFLARE_SETUP.md:139-149`).
- [ ] **Accès sans compte** : 403 sur Opportunités, les rapports, le téléchargement d'un tarif, l'API v2, l'export et `/api/performance/metrics` ; 405 sur `POST /api/graphql` (audit :314-318).
- [ ] **Comptes** : refaire les 6 contrôles de `docs/ACTIVER_SUPABASE.md:177-201` avec `SITE=https://<domaine>` :
  - e-mail reçu de `noreply@afcfta-zlecaf.com` ;
  - lien ouvert sur un autre appareil ;
  - lien déjà utilisé ;
  - mot de passe oublié ;
  - connexion du compte admin ;
  - ancienne route de connexion en 410.

  Le logo des e-mails s'affiche (`:100-102`).
- [ ] **Paiement live** : un achat Stripe réel.
  - L'accès s'ouvre par le webhook seulement (`backend/routes/billing.py:11-12`).
  - Le montant égale `backend/pricing.py:34-40`.
  - Le retour se fait sur `<domaine>/pricing.html?checkout=success`.
  - Le portail client s'ouvre.

  Même contrôle pour Chargily, depuis l'Algérie ou un VPN algérien (`docs/CLOUDFLARE_SETUP.md:151-153`). Remboursement de ces achats d'essai : à décider.
- [ ] **Surveillance** : Actions → Surveillance sécurité → Run workflow. Attendus : HTTP 200 et verdict « ok » (`docs/INSTRUCTION_POD_EMERGENT.md:364-368` ; `surveillance_securite.yml:57-75`).
- [ ] **Pages légales sans passage à compléter** : `curl -s https://<domaine>/cgu.html | grep -c '</mark>'` doit afficher 0, de même pour `confidentialite.html` ; aujourd'hui : 7 et 7. Chercher la balise fermante : le commentaire de tête contient `<mark>` (`confidentialite.html:10`).
- [ ] **`APP_ENV=production`** : contrôle par l'exploitant dans le shell, sans afficher de valeur. Un 404 sur `/api/docs` ne le prouve pas (audit :299).
- [ ] **Vitrine** : les documents internes répondent toujours 404 (audit :33).
