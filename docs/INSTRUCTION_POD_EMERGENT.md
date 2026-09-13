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

```bash
curl -s "http://localhost:8001/api/reports/national-need?hs_code=0714&country=DZA"
curl -s "http://localhost:8001/api/reports/national-need?hs_code=0803&country=DZA"
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

## 7. Ce qui n'est PAS concerné

- **Chantier tarifaire et module Calculateur** — travaux arrêtés. Aucun
  changement attendu de ce côté ; ne rien y toucher.
