# Instruction pour le pod Emergent — Production (ISIC4 / IDSB) et Opportunités

> Note à lire. La seule chose à exécuter dans le **Shell Emergent** est la
> commande de la section 1 — le reste est du Markdown, pas du shell.
> Rédigée le 2026-09-12, après la fusion des PR #467 (Production) et #468
> (Opportunités) dans `main`.

## 0. Règle qui prime sur tout le reste

**GitHub est la source de vérité.** Le pod n'audite pas sa copie locale, ne
compare rien, ne corrige rien à la main : il applique `origin/main` telle
quelle. Toute modification faite dans le shell Emergent et non poussée sur
GitHub **sera écrasée**. C'est voulu — c'est ce qui a éliminé les déploiements
à copie partielle.

Exceptions réellement préservées par le script : `/app/backend/.env`,
`node_modules`, le venv, et les bases GeoIP (`data/geoip`,
`backend/data/geoip`, non versionnées).

`backend/data/news_cache.json` n'est **pas** exclu, contrairement à ce que
laisse entendre l'ancien runbook : `git reset --hard` le réinitialise s'il est
suivi, `git clean -fd` le supprime sinon. Sans conséquence — `etl/news_aggregator.py`
le reconstruit à la première requête — mais ne comptez pas dessus.

## 1. La commande — une seule

```bash
BRANCH=main bash sync_emergent.sh
```

Ne lancez **pas** `start.sh` sous Emergent : supervisord gère les services, et
`sync_emergent.sh` fait déjà `supervisorctl restart all`.

Le script applique `origin/main` (`git reset --hard` + `git clean -fd`),
vérifie que la copie est complète, réinstalle le backend, contrôle imports et
données, **reconstruit le frontend** (`yarn build` → `frontend/build`, que
`vite preview` sert) puis redémarre.

> Le rebuild frontend n'est pas optionnel : `frontend/build` est ignoré par
> git. Sans lui, **aucun changement d'écran n'apparaît jamais**, quel que soit
> l'état de la branche.

## 2. Variables d'environnement — à fixer une fois dans le pod

| Variable | Valeur | Raison |
|---|---|---|
| `BACKEND_PORT` | `8001` | port imposé par l'ingress Kubernetes |
| `FRONTEND_PORT` | `3000` | idem |

À fixer dans l'environnement Emergent, **jamais** en patchant
`vite.config.js` / `package.json` : ces fichiers lisent l'environnement, donc
un `git reset` ne casse plus la configuration de ports.

Les secrets runtime vivent dans `/app/backend/.env` (gabarit :
`docs/emergent.env.template`), préservé par le script. Les secrets de build
restent dans GitHub Secrets — ne pas mélanger les deux.

## 3. Vérification après synchronisation

```bash
supervisorctl status

# santé générale du moteur
curl -s http://localhost:8001/api/reports/health
curl -s http://localhost:8001/api/reports/oec-health   # statistics_free.reachable: true
```

### Ce que cette synchronisation apporte — à vérifier explicitement

Le module **Production / Manufacturing** sert désormais les **54 pays** en
classes ISIC Rev.4, contre 20 avant (les 34 autres renvoyaient un 404 et un
écran vide).

```bash
# 54 pays au total : 20 mesurés UNIDO + 34 en estimation structurelle
curl -s "http://localhost:8001/api/production/isic4/countries?include_estimates=true" \
  | head -c 600

# un pays MESURÉ (data_basis: UNIDO_MEASURED)
curl -s "http://localhost:8001/api/production/isic4/KEN" | head -c 400

# un pays ESTIMÉ (data_basis: ESTIMATED_FROM_ISIC2)
curl -s "http://localhost:8001/api/production/isic4/DZA" | head -c 400

# séries IDSB/INDSTAT groupées — une requête au lieu de 130
curl -s "http://localhost:8001/api/production/isic4/KEN/timeseries" | head -c 400
```

À l'écran (onglet Production → Manufacturing) :

1. la colonne **« Libellé »** est remplie (elle était vide partout — un simple
   nom de champ) ;
2. un pays sans données UNIDO affiche un **bandeau ambre de méthode** et des
   pastilles de nature par ligne ;
3. le clic sur une ligne ISIC2 déplie le **tableau ISIC4 / IDSB** lisible
   (en-tête et première colonne figés) ;
4. le bouton **PDF** produit la méthode, la vue d'ensemble par division, puis
   le détail par classe.

### Lecture des données — non négociable

Deux niveaux distincts, et les confondre fait lire une estimation comme une
mesure.

`data_basis` qualifie le **pays** :

- `UNIDO_MEASURED` — le pays est présent dans le jeu au niveau classe ;
- `ESTIMATED_FROM_ISIC2` — il en est absent, sa structure est reconstruite.

`data_nature` qualifie **chaque indicateur**, et c'est lui qui tranche :

- `OFFICIAL_STATISTICS` — statistiques officielles INDSTAT ;
- `UNIDO_DERIVED_ESTIMATE` — estimations dérivées IDSB ;
- `STRUCTURAL_ESTIMATE_FROM_ISIC2` — **estimation
  structurelle**, répartition **à parts égales** entre les classes d'une
  division. Elle **situe** un secteur, elle ne permet pas d'en **comparer**
  deux. Une division absente n'est pas nulle : elle n'est pas renseignée.

Un pays `UNIDO_MEASURED` **mélange** les deux premières natures : la route le
dit elle-même (`data_includes`). Lire ses lignes en bloc comme « officielles »
est précisément l'erreur à ne pas commettre.

Aucune valeur manquante n'est remplacée par 0 (principe `no_missing_as_zero`
du registre des sources). Si un chiffre manque, la cellule affiche un tiret
cadratin « — », à l'écran comme dans le PDF. Un tiret n'est pas un zéro.

**Règle absolue : aucune donnée estimée dans le calcul tarifaire.** Le module
Production peut estimer ; le Calculateur, jamais.

## 4. En cas de « la PR est mergée mais rien ne change »

Dans l'ordre, les trois causes déjà rencontrées :

1. le frontend n'a pas été reconstruit → relancer `sync_emergent.sh` (seul
   point d'entrée fiable) ;
2. un cache de service sert d'anciens payloads (TTL 24 h) → le
   `_CACHE_SCHEMA_VERSION` doit avoir été incrémenté côté dépôt. Le script
   contrôle un **plancher** (`>= 3`), pas la péremption : une copie en v3 ou
   plus passe même si un changement de forme exigeait un nouvel incrément.
   Le garde-fou est donc partiel ;
3. le composant n'est pas monté par `App.js` — aucun cache ni build ne peut
   faire apparaître un écran qui n'est jamais rendu.

## 5. Module Opportunités — le besoin national devient réaliste

Fusionné en même temps (PR #468). Le module désignait comme marchés des pays
auto-suffisants et des pays qui ne consomment pas le produit :

| Cas | Avant | Après |
|---|---|---|
| Manioc → Algérie | 7 350 000 | **non établi** |
| Huile de palme → Algérie | 853 000 | **non établi** |
| Bananes → Cameroun | 1 650 000 | **0** — auto-suffisant |
| Bananes → Algérie | 1 010 000 | **1 010 000** — marché réel préservé |
| Huile de palme → Égypte | 1 950 000 | **1 950 000** — préservé |

Un exportateur ne peut servir que ce que le pays **ne produit pas** : la
production nationale est soustraite (`importable_need`), et c'est sur cette
grandeur que les marchés sont classés.

Le module Opportunités est réservé aux abonnements payants : sur le pod (avec
base), un appel anonyme reçoit un 403. On interroge donc l'application dans le
processus, sans base (comme la CI) :

```bash
cd /app/backend && MONGO_URL= python - <<'EOF'
from fastapi.testclient import TestClient
import server
c = TestClient(server.app)
for hs in ("0714", "0803"):
    print(hs, c.get(f"/api/reports/national-need?hs_code={hs}&country=DZA").json())
EOF
```

Le premier doit être **non établi** ; le second doit **rester un marché réel**.
C'est le garde-fou essentiel : une absence de preuve n'est pas une preuve
d'absence. Sans flux d'importation connu, le panier de consommation est
« invérifiable » — le besoin est conservé et signalé peu fiable, jamais
supprimé en silence.

## 6. Si le pod dit avoir des correctifs locaux que GitHub n'a pas

`sync_emergent.sh` fait un `git reset --hard` : un correctif local non poussé
est détruit. La réponse n'est donc **jamais** « garde-le en local » ni
« pousse-le depuis le pod sans le montrer ». La réponse est : **montre le
`git diff`**, on juge sur pièces, et ce qui doit vivre part sur GitHub.

Le pod n'a pas les moyens de trancher seul : il voit sa copie, pas l'historique.
Vérifié le 2026-09-13 sur `origin/main`, sur ses cinq affirmations :

| Affirmation du pod | Vérification sur `main` |
|---|---|
| marqueurs de conflit dans `calculator.py`, `tax_computation.py`, `authentic_tariffs.py`, `postgres_tariffs.py` | **faux** — zéro marqueur, et zéro sur tout le dépôt (résolus par la PR #466, commit `0cbcc7a4`) |
| `routes/contact.py` cassé (`await` manquant) | **faux** — le fichier est correct et complet sur `main` |
| `frontend/src/index.js` cassé | **vrai** — voir ci-dessous |

Trois des quatre fichiers cités sont dans `backend/routes/` — `calculator.py`,
`authentic_tariffs.py`, `postgres_tariffs.py` — et seul `tax_computation.py`
est dans `backend/services/`. Une copie locale périmée décrit l'état d'avant,
pas l'état du dépôt.

### Le point d'entrée du frontend — régression, corrigée depuis

Contexte historique — **réglé par la PR qui apporte cette note**. Conservé
parce que c'est le meilleur exemple de la troisième cause listée en section 4.

`frontend/index.html` charge `/src/index.js`, et cet `index.js` rendait une
coquille réduite : cinq modules sur onze y étaient des `ModulePlaceholder`.
`App.js` — les onze modules, le thème, le topbar, l'i18n — n'était importé par
personne. La chaîne réellement montée était
`index.js → Production.js → ISIC4DetailTable.js`, alors que le travail de la
PR #467 vit dans `ProductionTab.jsx → ProductionManufacturing.jsx`,
atteignable seulement depuis `App.js`. L'API servait les 54 pays sans que rien
n'en paraisse à l'écran, et aucune synchronisation n'y aurait rien changé.

`index.js` est désormais un point d'entrée mince qui monte `App`, et cinq tests
gardent ce câblage. **Rien à corriger dans le pod** : synchronisez sur `main`
une fois cette PR fusionnée.

## 6 bis. Alerte « contrôle des crons » (point 17 de l'audit de sécurité)

Le backend relance toutes les heures `scripts/controle_crons_emergent.sh`, le
même contrôle que l'étape 1bis de `sync_emergent.sh`. Il signale :
- une ligne de `webhook-crons` hors de la forme rendue par Emergent ;
- une tâche `dispatch_webhook` alors que `.emergent/crons.yml` n'existe pas, ou
  un `crons.yml` absent du manifeste ;
- un octet de contrôle ou non ASCII dans un fichier de cron ;
- un fichier inattendu dans `/etc/cron.d`. Le relevé du 06/11/2026 y trouve
  `.placeholder`, `e2scrub_all` et `webhook-crons` ;
- une crontab d'utilisateur ;
- un script de `.emergent/cron/` différent de `scripts/crons_emergent_sha256.txt` ;
- un fichier Debian lancé en root différent du même manifeste : `/etc/crontab`,
  `/etc/cron.daily/apt-compat`, `/etc/cron.daily/dpkg` et
  `/etc/supervisor/supervisord.conf` (empreintes du relevé du 06/11/2026,
  identiques aux fichiers des paquets bookworm officiels) ;
- dans `/etc/cron.hourly`, `cron.daily`, `cron.weekly`, `cron.monthly` et
  `cron.yearly`, un fichier absent du manifeste. Les noms contenant un point
  (`.placeholder`, `x.sh`…) ne sont pas signalés : `run-parts` ne les lance
  jamais ;
- un `/etc/anacrontab` ou une file d'attente `at` non vide
  (`/var/spool/cron/atjobs`, `atspool`) : ni anacron ni at ne sont installés ;
- dans `/etc/supervisor/conf.d`, un fichier autre que `supervisord.conf`,
  `supervisord_code_server.conf`, `supervisord_nginx_proxy.conf` et
  `webhook-crond.conf` ; un programme supervisord (`[program:…]`) autre que
  `backend`, `frontend`, `mongodb`, `code-server`, `nginx-code-proxy` et
  `webhook-crond` (l'un d'eux disparu rend le contrôle incomplet, code 2). Le
  contenu de ces fichiers d'Emergent (commandes lancées) n'est pas comparé.

Le verdict est publié, sans détail, dans `components.crons` de
`/api/health/status`. La tâche GitHub « Surveillance sécurité » le lit toutes les
six heures et échoue, avec un e-mail, si le verdict n'est pas « ok » ou s'il a
plus de deux heures.

Une anomalie reste affichée, même si la ligne en cause a disparu depuis, jusqu'à
l'effacement de `/app/.afcfta-crons-anomalie`. Ce fichier est sur le volume du
pod : il survit au redémarrage du backend, à la synchronisation et à la reprise
du pod, et ne disparaît qu'avec la reconstruction du volume. Après une fausse
alerte avérée seulement, l'effacer à la main (`rm -f /app/.afcfta-crons-anomalie`),
avant toute synchronisation. La page reste en « anomalie » jusqu'au contrôle
suivant, au plus une heure, ou jusqu'à un redémarrage du backend
(`supervisorctl restart backend`), qui refait aussitôt le contrôle. Relancer
la tâche GitHub seulement après.

**Sur alerte « ANOMALIE, compromission possible »** (verdict `anomalie`) :

Ne pas resynchroniser : la synchronisation relancerait le pod avec les
secrets sans retirer une ligne plantée, et effacerait des traces. Ne pas
effacer `/app/.afcfta-crons-anomalie` et ne pas corriger les crons à la main.

1. **Relevé en lecture seule.** Message à coller dans Emergent :

   ```text
   Contrôle de sécurité en LECTURE SEULE : ne modifie, n'efface, ne redémarre et ne synchronise rien. N'affiche aucune valeur de secret.
   1. cat /app/.afcfta-crons-anomalie
   2. grep -n "Crons du pod" /var/log/supervisor/backend.err.log | tail -5
   3. cd /app && env -u EMERGENT_DIR -u CRON_D -u CRON_SPOOL -u MANIFESTE -u RACINE_SYSTEME bash scripts/controle_crons_emergent.sh; echo "code=$?"
   4. ls -la /etc/cron.d/ /etc/cron.hourly/ /etc/cron.daily/ /etc/cron.weekly/ /etc/cron.monthly/ /etc/cron.yearly/ /etc/supervisor/conf.d/ /var/spool/cron/ /var/spool/cron/crontabs/ 2>&1
   5. git -C /app log --oneline -1 ; git -C /app status --short .emergent | head -20
   Renvoie-moi toutes les sorties telles quelles.
   ```

   Le journal tient chaque contrôle sur une seule ligne (retours à la ligne
   écrits `\n`), et le contrôle masque déjà les valeurs des lignes signalées.
   Faire analyser la réponse (fausse alerte ou anomalie réelle) avant toute
   autre action.

2. **Fausse alerte avérée** (cas le plus probable : Emergent a mis à jour ses
   scripts de `.emergent/cron/`, dont l'empreinte ne correspond plus au
   manifeste) :
   1. corriger dans une PR ce qui déclenche l'alerte, le plus souvent
      `scripts/crons_emergent_sha256.txt` après relecture du changement
      d'Emergent, puis la fusionner. Pour une empreinte `/etc/…` (image du pod
      mise à jour par Emergent), ne la remplacer qu'après l'avoir retrouvée
      dans le paquet Debian officiel correspondant (deb.debian.org ou
      security.debian.org) ;
   2. message à coller dans Emergent :

      ```text
      Fausse alerte confirmée et corrigée sur main. Exécute, dans cet ordre :
      rm -f /app/.afcfta-crons-anomalie
      cd /app && BRANCH=main bash sync_emergent.sh
      Renvoie-moi la ligne de l'étape « 1bis/6 » et celle qui la suit.
      ```

      La synchronisation est indispensable : le contrôle lit le manifeste du
      pod (`/app/scripts/crons_emergent_sha256.txt`), que la fusion ne change
      pas. Sans elle, le contrôle relancé au redémarrage relirait l'ancien
      manifeste et recréerait l'anomalie. L'effacement passe avant : la
      synchronisation redémarre le backend, dont le premier contrôle doit
      alors donner « ok ». Si l'étape 1bis affiche encore « ⚠ », s'arrêter
      là : la correction ne couvre pas tout.

      Si rien n'est à corriger dans le dépôt (cause disparue et comprise), le
      message se réduit à
      `rm -f /app/.afcfta-crons-anomalie && supervisorctl restart backend`.
   3. vérifier que `components.crons` de `/api/health/status` est repassé à
      « ok », puis relancer la tâche GitHub.

3. **Anomalie réelle, ou doute :**
   1. demander au support d'Emergent d'exporter la base MongoDB (comptes,
      abonnements) avant toute reconstruction, et lui demander si la
      reconstruction la conserve ;
   2. faire reconstruire le pod ET son volume par le support d'Emergent : une
      ligne plantée survit sur le volume ;
   3. changer tous les secrets : régénérer chaque valeur chez son fournisseur,
      puis la saisir dans la carte sécurisée d'Emergent, jamais dans une
      conversation. Sont concernés `JWT_SECRET`, `ADMIN_PASSWORD`, la clé
      secrète Supabase (`sb_secret_…`), les clés Stripe et Chargily (secrète
      et webhook), la clé Resend, `CLOUDFLARE_EDGE_SECRET`, les clés Anthropic
      et Gemini, le mot de passe MongoDB et toute autre clé de `backend/.env` ;
   4. retirer puis redonner à Emergent son accès GitHub (GitHub → Settings →
      Applications) ;
   5. synchroniser sur `main` : l'étape 1bis doit afficher « ✓ », puis la
      tâche GitHub doit repasser au vert.

**Sur alerte « surveillance indisponible »** (pod injoignable, réponse
Cloudflare, verdict absent, incomplet ou trop ancien) : ce n'est pas un signe
de compromission. Vérifier que le pod et le backend tournent, puis relancer la
tâche. Si Cloudflare répond 403 ou 503 aux exécuteurs GitHub, demander à
Emergent d'autoriser `/api/health/status`. Une réponse HTTP 404 vient le plus
souvent de la préversion en veille, quand personne n'est actif sur Emergent :
ouvrir Emergent, attendre que l'aperçu réponde, puis relancer la tâche
(Actions → Surveillance sécurité → Re-run jobs).

**Mise en place, une fois :**
1. Créer la variable de dépôt `URL_SANTE_STATUS`, qui vaut l'adresse
   `https://<pod>/api/health/status`.
2. Lancer la tâche une première fois à la main (Actions → Surveillance
   sécurité → Run workflow).

Si Emergent met à jour ses scripts de `.emergent/cron/`, relire le changement,
puis mettre à jour le manifeste dans la même PR : le test
`test_le_manifeste_correspond_aux_scripts_versionnes` l'exige.

## 7. Ce qui n'est PAS concerné

- **Chantier tarifaire et module Calculateur** — travaux arrêtés. Aucun
  changement attendu de ce côté ; ne rien y toucher.
