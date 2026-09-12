# Instruction pour le pod Emergent — Production (ISIC4 / IDSB) et Opportunités

> À coller telle quelle dans le **Shell Emergent** du projet.
> Rédigée le 2026-09-12, après la fusion des PR #467 (Production) et #468
> (Opportunités) dans `main`.

## 0. Règle qui prime sur tout le reste

**GitHub est la source de vérité.** Le pod n'audite pas sa copie locale, ne
compare rien, ne corrige rien à la main : il applique `origin/main` telle
quelle. Toute modification faite dans le shell Emergent et non poussée sur
GitHub **sera écrasée**. C'est voulu — c'est ce qui a éliminé les déploiements
à copie partielle.

Seules exceptions préservées par le script : `/app/backend/.env`,
`node_modules`, le venv, et `backend/data/news_cache.json` (cache régénéré).

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

Trois libellés distincts, à ne jamais confondre :

- `UNIDO_MEASURED` / `OFFICIAL_STATISTICS` — statistiques officielles INDSTAT ;
- `UNIDO_DERIVED_ESTIMATE` — estimations dérivées IDSB ;
- `ESTIMATED_FROM_ISIC2` / `STRUCTURAL_ESTIMATE_FROM_ISIC2` — **estimation
  structurelle**, répartition **à parts égales** entre les classes d'une
  division. Elle **situe** un secteur, elle ne permet pas d'en **comparer**
  deux. Une division absente n'est pas nulle : elle n'est pas renseignée.

Aucune valeur manquante n'est remplacée par 0 (principe `no_missing_as_zero`
du registre des sources). Si un chiffre manque, il doit s'afficher « n.d. ».

**Règle absolue : aucune donnée estimée dans le calcul tarifaire.** Le module
Production peut estimer ; le Calculateur, jamais.

## 4. En cas de « la PR est mergée mais rien ne change »

Dans l'ordre, les trois causes déjà rencontrées :

1. le frontend n'a pas été reconstruit → relancer `sync_emergent.sh` (seul
   point d'entrée fiable) ;
2. un cache de service sert d'anciens payloads (TTL 24 h) → le
   `_CACHE_SCHEMA_VERSION` doit avoir été incrémenté côté dépôt ; le script le
   vérifie et refuse de continuer si la copie est périmée ;
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

## 6. Ce qui n'est PAS concerné

- **Chantier tarifaire et module Calculateur** — travaux arrêtés. Aucun
  changement attendu de ce côté ; ne rien y toucher.
