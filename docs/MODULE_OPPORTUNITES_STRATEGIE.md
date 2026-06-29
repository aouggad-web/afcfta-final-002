# Module « Opportunités » — Stratégie, méthodologie et architecture

_Plateforme ZLECAf / AfCFTA — Note technique et éditoriale_
_Dernière mise à jour : 2026-06-29_

---

## 1. Stratégie

Le module **Opportunités** est le cœur analytique de la plateforme : il doit aider
décideurs publics, exportateurs et investisseurs à identifier des débouchés
commerciaux intra-africains concrets sous la ZLECAf.

La stratégie repose sur un principe directeur unique :

> **Tout chiffre affiché doit être réel et traçable, ou clairement signalé comme
> indisponible — jamais inventé.**

Ce principe découle d'un constat d'audit : plusieurs sous-onglets renvoyaient des
chiffres **générés par un modèle de langage (LLM)** présentés comme faisant
autorité (avec une liste de « sources » OEC/FMI/UNCTAD trompeuse), et le module
de substitution mélangeait une petite table codée en dur avec des
**multiplicateurs aléatoires** (`random.uniform`). Les volumes changeaient à
chaque appel et ne correspondaient à aucune source vérifiable.

La stratégie a donc consisté à **ré-ancrer chaque sous-onglet sur les jeux de
données réels déjà présents dans le code mais sous-exploités**, et à reléguer
l'IA à un rôle de rédaction de texte (jamais de production de chiffres).

---

## 2. Objectifs

| # | Objectif | Indicateur de réussite |
|---|----------|------------------------|
| 1 | Supprimer toute donnée fabriquée (aléatoire ou LLM) des chiffres affichés | Plus aucun `random.*` dans les services servant le module ; plus aucun chiffre LLM présenté comme factuel |
| 2 | Rendre les résultats **reproductibles** | Deux appels identiques renvoient exactement le même résultat |
| 3 | Couvrir les **54 pays** ZLECAf, pas seulement une poignée | Données dérivées de jeux couvrant les 54 pays |
| 4 | **Préserver l'expérience** (aucune régression frontend) | Forme des réponses API inchangée ; `yarn build` OK |
| 5 | **Tracer** chaque chiffre jusqu'à sa source | Champ `sources` / `data_source` réel ; champs non sourçables en `null` |
| 6 | Réduire les coûts | Les endpoints ré-ancrés n'appellent plus le LLM (zéro quota IA) |

---

## 3. Méthodologie

### 3.1 Démarche générale

1. **Audit** — cartographie de chaque sous-onglet → endpoint → service → source
   de données, avec un verdict par endpoint :
   `RÉEL` / `GÉNÉRÉ-PAR-IA` / `ALÉATOIRE` / `MOCK-CODÉ-EN-DUR` / `MIXTE`.
2. **Décision pilotée par l'utilisateur** — pour chaque catégorie à risque,
   choix explicite de la direction (ancrage réel, étiquetage honnête, ou report).
3. **Ré-ancrage incrémental, onglet par onglet** — un service `real_*` dédié par
   onglet, branché en remplacement de l'appel LLM dans la route, **sans changer
   la forme de la réponse** consommée par le frontend.
4. **Vérification** — tests unitaires hermétiques (sources simulées, sans
   réseau), `black` / `isort` / `flake8`, revue Copilot, fusion.

### 3.2 Règles de non-fabrication appliquées

- Les **parts, totaux et potentiels** sont **calculés** à partir des valeurs
  réelles (jamais saisis à la main).
- Un **potentiel de substitution/complémentarité** est **borné par la capacité
  réelle** (`min(import, capacité d'export africaine)`).
- Un champ **sans source** (inflation, économies tarifaires, total
  intra-africain continental, secteurs continentaux) est renvoyé **`null` / vide**
  — jamais estimé.
- Quand une source réelle est **injoignable**, les tableaux reviennent **vides**
  et la réponse est **marquée** (`is_estimation`, `data_quality`) plutôt que
  remplie de valeurs inventées.
- Les résultats sont **déterministes** : suppression de tout `random.*`.

### 3.3 Rôle de l'IA

L'IA (Claude) **ne produit plus de chiffres** dans les onglets ré-ancrés. Là où
une analyse qualitative reste utile (ex. Chaînes de Valeur, encore à arbitrer),
le principe retenu est : **chiffres = sources réelles, texte = IA clairement
étiquetée**.

---

## 4. Moyens mis en place

### 4.1 Sources de données réelles exploitées

| Source | Nature | Utilisée pour |
|--------|--------|---------------|
| **OEC** (Observatory of Economic Complexity, BACI / UN Comtrade) | Flux commerciaux réels par pays / produit / partenaire | Exportateurs & importateurs par produit, flux bilatéraux, substitution, complémentarité |
| **`country_data.REAL_COUNTRY_DATA`** | 54 pays — PIB, croissance, population, IDH, rang (FMI / Banque Mondiale / PNUD) | Comparaison économique, profils pays |
| **`production_capacity_service`** | 722 enregistrements FAOSTAT / USGS / UNIDO / Banque Mondiale | Capacités de production par produit |
| **`hs6_database`** (WCO HS 2022) | ~5 800 codes SH6 | Nomenclature produit, taille de l'univers SH |
| **Jeu commercial 2024 curé** (`TRADE_PERFORMANCE_GLOBAL_2024`) | Exports/imports par pays, OEC/BM/FMI | Vue d'ensemble continentale |
| **Calendrier officiel de démantèlement ZLECAf** + tarifs nationaux | Annexe 1 du Protocole sur le commerce des marchandises | Simulateur ZLECAf, comparateur bilatéral |

### 4.2 Services « réels » créés / modifiés

| Service | Onglet | Remplace |
|---------|--------|----------|
| `real_substitution_service` | Substitution | Table statique + `random` |
| `real_product_service` | Par Produit | Appel LLM `analyze_product_by_hs_code` |
| `real_comparison_service` | Comparaison | Appel LLM `compare_countries` |
| `real_summary_service` | Vue d'ensemble | Appel LLM `get_trade_summary` |
| `real_trade_data_service.get_bilateral_trade` | (connecteur) | _nouveau_ — flux directionnel A→B réel OEC |

### 4.3 Garde-fous d'ingénierie

- **Cache** par service (TTL 1 h) pour limiter la latence des appels OEC.
- **Parallélisation** des appels OEC (`asyncio.gather`) et **indices pré-agrégés**
  par chapitre SH pour éviter les appels N×16.
- **Tests hermétiques** (OEC simulé, sans réseau) : 19 tests couvrant valeurs
  réelles, reproductibilité, repli, erreurs d'entrée.
- **Qualité de code** : `black`, `isort`, `flake8` appliqués (alignés sur la CI).

---

## 5. Architecture du module

### 5.1 Vue d'ensemble (frontend → API → services → données)

> ℹ️ **Schéma logique** — il illustre les flux, pas l'arborescence exacte des
> fichiers. Les chemins réels sont rappelés sous le schéma ; en résumé, le
> frontend est sous `frontend/src/` et, côté backend, `routes/`, `services/`,
> `country_data.py` et `etl/` sont tous des frères sous `backend/` (les
> `services/` ne sont **pas** dans `routes/`).

```
Frontend (frontend/src/)
  App.js  (onglet "opportunities")
   └── components/opportunities/OpportunitiesTab.jsx   (conteneur, 8 sous-onglets)
        ├── AIAnalysis.jsx ............ GET /ai/opportunities/{pays}   (MIXTE : IA + OEC)
        ├── SubstitutionAnalysis.jsx .. GET /substitution/...          (RÉEL — OEC)
        ├── ZlecafImpactSimulator.jsx . GET /dismantlement/impact/...  (RÉEL — calendrier ZLECAf)
        ├── BilateralTariffComparator.. GET /bilateral-tariff/...      (RÉEL — tarifs + schedule)
        ├── OpportunitySummary.jsx ..... GET /ai/summary               (RÉEL — agrégats sourcés)
        ├── ValueChains.jsx ............ GET /ai/value-chains          (⏸ à arbitrer)
        ├── ProductAnalysisView.jsx .... GET /ai/product/{hs}          (RÉEL — OEC + production)
        └── CountryComparison.jsx ...... GET /ai/compare               (RÉEL — country_data + OEC)

Backend (backend/)
  routes/                         services/
   ├ gemini_analysis.py (/ai)      ├ real_substitution_service.py
   ├ substitution.py               ├ real_product_service.py
   ├ production.py                  ├ real_comparison_service.py
   ├ hs_codes.py                    ├ real_summary_service.py
   ├ statistics.py                  ├ real_trade_data_service.py  (connecteurs OEC)
   ├ dismantlement.py               └ production_capacity_service.py
   └ tariffs.py                          └ data/json/production_africaine.json
                                              (FAOSTAT/USGS/UNIDO/BM)
  country_data.py  (REAL_COUNTRY_DATA, 54 pays)
  etl/hs6_database.py  (nomenclature WCO HS)
```

Les routes `/ai/*` (fichier `routes/gemini_analysis.py`) délèguent désormais aux
services `real_*` pour les onglets ré-ancrés.

### 5.2 Flux type — « Par Produit » (exemple représentatif)

```
GET /ai/product/{hs_code}
  → real_product_service.analyze_product_by_hs_code(hs)
      ├── real_trade_service.get_african_exporters_for_product(hs)   [OEC]
      ├── real_trade_service.get_african_importers_for_product(hs)   [OEC]
      ├── production_capacity_service.get_continental_producers(hs)  [FAO/USGS/UNIDO]
      └── get_product_name(hs)                                       [WCO HS]
  → réponse : produit, top exportateurs/importateurs (parts calculées),
              capacités de production, sources, is_estimation, data_quality
```

### 5.3 Principes d'architecture retenus

- **Un service `real_*` par onglet**, symétriques (mêmes conventions :
  cache, `is_estimation`, `data_source`, wrapper de classe singleton).
- **La route reste stable** (même chemin, même forme de réponse) : seul le
  fournisseur de données change. Aucune modification frontend nécessaire.
- **Séparation nette** : connecteurs de données bruts (`real_trade_data_service`)
  ↔ services métier (`real_*_service`) ↔ routes (exposition HTTP).
- **Dégradation gracieuse** : source injoignable → réponse réelle partielle ou
  vide **étiquetée**, jamais une invention ; le frontend ne bascule donc pas sur
  ses propres données factices.

---

## 6. Avertissements

> ⚠️ **À lire avant toute mise en production ou communication chiffrée.**

1. **Validation OEC en conditions réelles non effectuée dans l'environnement de
   développement.** L'API OEC (`api-v2.oec.world`) est **bloquée par la politique
   réseau (403)** de l'environnement d'exécution. Toute la logique a été validée
   avec des **données OEC simulées** et des **jeux de données statiques réels**.
   La **validation de bout en bout avec les vrais chiffres OEC doit être réalisée
   sur l'environnement de déploiement** (qui dispose de l'accès réseau OEC).

2. **Latence OEC.** Les onglets interrogeant OEC en direct (Par Produit,
   Comparaison) effectuent plusieurs appels réseau. Un cache (1 h) et la
   parallélisation atténuent l'impact, mais la première requête peut être lente,
   et un OEC lent/indisponible renvoie des tableaux **vides** (marqués
   `is_estimation`).

3. **Champs volontairement absents.** Certaines valeurs ne disposent d'aucune
   source dans l'application et sont renvoyées en `null` / vide **par choix de
   non-fabrication** : inflation (Comparaison), économies tarifaires précises,
   total intra-africain continental et secteurs continentaux (Vue d'ensemble).
   Ce n'est pas un bug.

4. **Granularité des données.**
   - Les agrégats de complémentarité/substitution sont appariés au niveau du
     **chapitre SH2**, pas du SH6 — c'est une approximation volontaire.
   - Le simulateur ZLECAf et le comparateur bilatéral utilisent un taux NPF au
     niveau **chapitre SH2** avec **repli par défaut (15 % puis 10 %)** quand un
     couple pays/chapitre est manquant (la source est indiquée dans
     `npf_rate_source`).
   - `TRADE_PERFORMANCE_GLOBAL_2024` (Vue d'ensemble) est un jeu **curé statique**
     2024 : crédible et sourcé, mais **non rafraîchi en direct** (« faire
     confiance au curateur »).

5. **Onglet « Chaînes de Valeur » non encore ré-ancré.** Ses champs structurels
   (étapes, % de valeur ajoutée, goulots, investissement requis) **n'ont aucune
   source réelle** et restent, en l'état, alimentés par l'IA et/ou une ossature
   curée côté frontend. **Décision en attente.**

6. **Repli frontend codé en dur — à retirer.** Certains composants
   (`ProductAnalysisView.jsx`, `CountryComparison.jsx`, `OpportunitySummary.jsx`)
   contiennent encore des **tableaux de secours codés en dur** (ex. valeur
   intra-africaine `186`). Ils sont désormais largement **inatteignables** (le
   backend renvoie toujours une structure sourcée), mais devraient être nettoyés
   lors d'une passe frontend pour éviter toute confusion future.

7. **Données ≠ conseil.** Les chiffres décrivent des flux et capacités observés ;
   ils n'intègrent pas les barrières non tarifaires, la logistique fine, ni le
   risque pays au-delà des indicateurs publiés. Ils éclairent une décision, ils
   ne la remplacent pas.

---

_Fin du document._
