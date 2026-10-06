# Programme d'exécution — Plan de simplification

> Met en œuvre `docs/PLAN_SIMPLIFICATION_2026-10-01.md`. Le plan dit **quoi** et
> **pourquoi** ; ce programme dit **qui fait quoi, dans quel ordre, avec quelle
> commande de contrôle, et quand c'est fini**. Démarrage proposé : lundi
> 5 octobre 2026. Durée : 6 semaines pour O1, O2, O3, O5 et O4-a/b/c ; O4-d/e
> se poursuivent pays par pays.

---

## 1. Règles du jeu (valables pour chaque lot)

1. **Une PR par lot**, en brouillon, sur une branche `simplif/<lot>` (ex.
   `simplif/O1-a-verdict`). Aucun lot ne mélange deux objectifs.
2. **En tête de chaque PR, deux lignes obligatoires** : ce que le lot
   **retire** (lignes, fichiers, routes, statuts, documents) et ce qu'il
   **ajoute**. Si l'ajout dépasse le retrait sans justification écrite, la PR
   est refusée (règle du plan).
3. **Contrôles avant d'ouvrir la PR**, depuis la racine :
   ```bash
   python3 -m pytest backend/tests -q
   python3 -m flake8 .
   black --line-length 100 --check <fichiers modifiés>
   python3 scripts/verifier_fiche.py --toutes        # si une fiche est touchée
   (cd frontend && npm run test && npm run build)    # si l'interface est touchée
   ```
4. **Revue Codex systématique** (`@codex review`), puis relecture du
   propriétaire. Fusion **uniquement** par le propriétaire.
5. **Aucune donnée tarifaire modifiée pour faire passer un test.** Aucun taux
   inventé. Un manque se déclare (`INDISPONIBLE`, `PARTIEL`), il ne se comble
   pas par défaut.
6. **Le plan est mis à jour dans la même PR** quand un lot change un chiffre
   du plan (compte de couples, lignes, pays).

---

## 2. Jalon 0 — Décisions du propriétaire (avant le lundi 5 octobre)

Rien ne démarre sur O1-d, O4 et O5-d sans ces réponses. Le reste peut
démarrer.

| # | Décision | Bloque | Recommandation |
|---|---|---|---|
| D1 | Les cinq libellés du verdict + « même union douanière » | O1-d | valider |
| D2 | Taux de l'offre affiché « à titre indicatif » (verdicts 2 et 3) | O1-d | oui |
| D3 | Cible de déploiement unique | O5-a, O5-d | celle de la production actuelle |
| D4 | Classement « plus avantageux » autorisé | O4-e | oui, entre régimes appliqués |
| D5 | « Plus avantageux » au total liquidé | O4-e | oui |
| D6 | Archivage des plans remplacés | O2-d | oui, dans `docs/archive/` |
| D7 | Mauritanie dans la GZALE | O4-a | rien servi avant source primaire |

**Livrable du jalon** : les réponses inscrites au § 8 du plan (une PR de
quelques lignes).

---

## 3. Calendrier semaine par semaine

### Semaine 1 (5–9 octobre) — retirer ce qui ment, poser la source unique

| Lot | Branche | Durée | Dépend de |
|---|---|---|---|
| **O2-0** Retrait des routes qui inventent un taux | `simplif/O2-0-taux-inventes` | ½ jour | — |
| **O1-a** Tables ratification + offre, verdict dans la matrice | `simplif/O1-a-verdict` | 3 jours | — |
| **O3** Script du rapport des manques | `simplif/O3-manques` | 2 jours | — (parallèle) |

### Semaine 2 (12–16 octobre) — le registre lit les fiches, la production se construit d'une seule façon

| Lot | Branche | Durée | Dépend de |
|---|---|---|---|
| **O1-b** Registre lu depuis les fiches ; SYC ; DZA sur `/calcul` | `simplif/O1-b-registre` | 3 jours | O1-a |
| **O1-c** `verdict` dans la réponse de `/calcul` | `simplif/O1-c-api` | 1 jour | O1-b |
| **O5-a** Une construction (`make release`, socle dans l'image) | `simplif/O5-a-release` | 1 jour | D3 |
| **O5-b** Démarrage fail-closed + `/api/health` | `simplif/O5-b-health` | 1 jour | O5-a |

### Semaine 3 (19–23 octobre) — l'écran de résultats et la bascule

| Lot | Branche | Durée | Dépend de |
|---|---|---|---|
| **O1-d** Carte-verdict + écran replié + défauts d'affichage | `simplif/O1-d-ecran` | 3 jours | O1-c, D1, D2 |
| **O2-a** 3 champs d'interface + remise kényane au moteur | `simplif/O2-a-bascule` | 3 jours | — |

### Semaine 4 (26–30 octobre) — retirer l'ancien chemin

| Lot | Branche | Durée | Dépend de |
|---|---|---|---|
| **O2-b** Retrait des anciennes routes et du repli | `simplif/O2-b-retrait` | 3 jours | O2-a, O1-d |
| **O2-c** Retrait des copies de données (après qualification des écarts GNB/TCD) | `simplif/O2-c-donnees` | 1 jour | O2-b |
| **O2-d** `docs/README.md` + archivage | `simplif/O2-d-docs` | ½ jour | D6 |
| **O5-c** Rapports hebdomadaires + alerte d'échec de crawl | `simplif/O5-c-rapports` | 1 jour | O1-a, O3 |
| **O5-d** `docs/EXPLOITATION.md` | `simplif/O5-d-exploitation` | ½ jour | D3, O5-b |

### Semaines 5–6 (2–13 novembre) — accords autres que la ZLECAf

| Lot | Branche | Durée | Dépend de |
|---|---|---|---|
| **O4-a** Registre des accords (une seule liste de membres) | `simplif/O4-a-accords` | 3 jours | D7 |
| **O4-b** « Accords ouverts pour ce couple » | `simplif/O4-b-ouverts` | 1 jour | O4-a |
| **O4-c** Servir les colonnes déjà collectées (TUN, LBY, ETH, MUS, SADC) | `simplif/O4-c-colonnes` | 3 jours | O4-a |
| **O5-e** Retrait de `crawled_normalized/` | `simplif/O5-e-normalized` | ½ jour | O2-b |

### Ensuite — au fil des pays

| Lot | Rythme | Dépend de |
|---|---|---|
| **O4-d** Collecte GZALE, Agadir, bilatéraux, règles d'origine | une PR par pays et par accord | O4-a |
| **O4-e** Le comparatif dans les résultats | après les 3 premiers pays O4-d | O4-c, D4, D5 |
| Collecte ZLECAf (36 pays non recherchés) | une PR par pays, ordre donné par le rapport O3 | O3 |

---

## 4. Fiches de lot

Chaque fiche se copie telle quelle comme consigne de la session de travail.

### O2-0 — Retrait des routes qui inventent un taux

- **Retire** : `bulkTariffCalculation` dans `backend/api/graphql/schema.py`
  (taux fixe de 5 %) ; la route `POST /regional-calculator/*` et
  `services/enhanced_calculator_v3.py` (médiane de bande, GZALE ajoutée à
  tous les pays), sauf si un appelant de l'interface existe — le vérifier par
  `grep -rn "regional-calculator" frontend/src`.
- **Tests** : un test qui échoue si une réponse porte un `tariffRatePct` non
  issu du socle ; suppression des tests qui ne testaient que ces routes.
- **Fini quand** : `grep -rn "rate = 5.0" backend/` ne renvoie rien ;
  CI verte.

### O1-a — Verdict par couple

- **Ajoute** :
  - `backend/data/legal_refs/zlecaf_application/ratification_ua_2026-05-22.json`
    (54 lignes, dates, depuis le PDF archivé ; SOM non ratifiante) ;
  - `…/offres_ua_2025-07.json` (offre soumise / adoptée / aucune ; « aucune »
    pour DJI, ERI, LBY, SDN, SOM selon EX.CL/1625) ;
  - champ `verdict`, `piece_manquante`, `date_preuve` dans
    `reports/ETAT_APPLICATION_BILATERAL.json`.
- **Modifie** : `scripts/build_bilateral_application_matrix.py` (lit les
  fiches au lieu des 6 destinations en dur ; ratification des deux pays ;
  unions douanières) ; `backend/services/zlecaf_membership_status.py` (lit la
  table ; code inconnu → `INCONNU`, plus jamais « ratifié »).
- **Tests** : `test_bilateral_application_matrix.py` étendu — 2 862 couples,
  un verdict chacun ; un test par verdict ; test SOM ; test « matrice
  versionnée = matrice régénérée » ; test « registre, fichier d'état et
  matrice concordent ».
- **Fini quand** : les comptes réels remplacent les « ≈ » du § 2.1 du plan.

### O1-b — Registre lu depuis les fiches

- **Retire** : les listes d'origines écrites dans
  `zlecaf_implementation_registry.py` ; la liste morte EGY/MAR/RWA de
  `OFFER_DATASETS`.
- **Ajoute** : SYC (SI 113/2022) ; DZA routée par `preference.py` pour que le
  calendrier et le DAPS s'appliquent sur `/calcul`.
- **Tests** : DZA←EGY sur `/calcul` ; SYC←origine admise ; tous les tests
  `test_zlecaf_*` existants restent verts.

### O1-c — Verdict dans l'API

- **Ajoute** à la réponse de `POST /calcul` : `verdict`, `phrase`,
  `piece_manquante`, `preuve`, `sens_inverse`, `etat_ligne`.
- **Tests** : 5 verdicts + union douanière + sens inverse dans
  `test_calcul_route.py`.

### O1-d — L'écran de résultats

- **Ajoute** : composant `VerdictZlecaf.jsx` (une carte, deux sens).
- **Retire** : la logique de statut de `zlecafAvailability.js` (réduite à
  l'affichage) ; le pied de page dupliqué ; les `|| 0` sur les totaux.
- **Corrige** : `INDISPONIBLE` ≠ 0 % ; `PARTIEL` marqué ; total d'union
  douanière visible ; calendrier de démantèlement alimenté par le vrai NPF ;
  source et date de collecte affichées ; panneau réglementaire sans totaux
  concurrents.
- **Tests** : `vitest` — un rendu par verdict ; un rendu `INDISPONIBLE`.
- **Fini quand** : la carte et les deux totaux tiennent sur un écran mobile
  sans défilement.

### O2-a — Bascule vers la route unique

- **Interface** : envoyer `devise_cif`, `taux_de_change`, `valeur_fob` à
  `POST /calcul`.
- **Moteur** : ajouter la remise kényane à `DemandeCalcul` et à
  `services/calcul.py`, avec les mêmes garde-fous que l'ancien chemin.
- **Puis** : étendre `SOCLE_EN_PREMIER` aux 52 pays servis.
- **Tests** : corpus figé sur `/calcul` ; ZAF avec valeur FOB ; KEN avec et
  sans remise ; `scripts/diff_engines.py` comparé à `/calcul`.

### O2-b — Retrait de l'ancien chemin

- **Retire** : `GET/POST /authentic-tariffs/calculate`, `POST /calculate-tariff`,
  `regulatory-engine`, `enhanced_calculator*`, `calculate/detailed`,
  `postgres-tariffs/calculate`, `v2/calculations`, le repli de
  `CalculatorTab.jsx`.
- **Fini quand** : une seule route de calcul montée ; la chaîne passe sous
  11 191 lignes (mesure publiée dans la PR).

### O2-c — Copies de données

- **D'abord** : un tableau des écarts entre `backend/data/tariffs/` et
  `backend/data/*_tariffs.json` (GNB, TCD, et les autres), chacun tranché.
- **Retire** : `backend/data/tariffs/`, `engine/output/`,
  `tariff_engine/`, la génération de fichier à la demande de
  `routes/tariff_data.py`.
- **Garde** : les fichiers `*_progress_*` (constructeurs EGY/DZA).

### O2-d — Documents

- **Ajoute** : `docs/README.md` (cinq documents vivants).
- **Déplace** : les autres plans et audits vers `docs/archive/`, chacun avec
  une ligne « remplacé par ».

### O3 — Rapport des manques

- **Ajoute** : `scripts/rapport_manques_pays.py` → `reports/MANQUES_PAR_PAYS.md`
  et `.json` ; colonnes du § 4.1 du plan, dont réglementation par pays.
- **Retire** (archive) : `reports/CARENCES_CALCULATEUR_*`,
  `NATIONAL_TAX_COMPLETION_STATUS.md`, `KEN_DATA_GAPS.md`,
  `docs/COLLECTE_DONNEES_MANQUANTES.md`.
- **Tests** : 54 lignes ; aucune cellule vide ; test « rapport versionné =
  rapport régénéré ».

### O5-a / O5-b — Construction et démarrage

- `Makefile` : `make release` = vérifier les empreintes → `build_socle.py` →
  tests → image.
- `Dockerfile` : appelle `make release` ; plus de construction propre.
- Démarrage : refus si socle absent ou empreinte fausse.
- `/api/health` : version et empreinte du socle, date, comptes
  COMPLET/PARTIEL/VIDE, pays à collecte > 6 mois.
- **Fini quand** : l'image construite en CI répond sur `POST /calcul`.

### O5-c / O5-d — Rapports et exploitation

- Workflow hebdomadaire : régénère matrice + manques, ouvre une PR si
  changement ; alerte si un crawl planifié échoue deux fois.
- `docs/EXPLOITATION.md` : déployer, revenir en arrière, recharger un pays,
  lire `/api/health`.

### O4-a / O4-b / O4-c — Accords

- `backend/data/agreements/accords.json` : un accord = parties datées et
  sourcées, démantèlement, règle d'origine, justificatif.
- **Retire** : les cinq autres listes de membres (`country_codes.py`,
  `regional_analytics.py`, `all_countries_registry.py`,
  `north_africa_intelligence.py`, `uma_constants.py`) — elles lisent le
  registre.
- O4-b : liste des accords ouverts pour un couple, sous la carte-verdict.
- O4-c : `build_socle.py` garde les colonnes ZALE (MAR, EGY), Agadir,
  bilatérales, `LIGUE_ARABE`, `D2R`, `COMESA_I/II`, chacune sous son régime ;
  plancher NPF testé.

---

## 5. Suivi

| Rituel | Quand | Contenu |
|---|---|---|
| Point d'avancement | chaque vendredi | tableau ci-dessous mis à jour dans ce fichier ; lignes retirées / ajoutées de la semaine |
| Revue | chaque PR | Codex, puis le propriétaire |
| Rapport automatique | chaque lundi (après O5-c) | `MANQUES_PAR_PAYS` et matrice des verdicts |

### Tableau de bord

| Lot | État | PR | Retiré | Ajouté |
|---|---|---|---|---|
| Jalon 0 | à faire | — | — | — |
| O2-0 | à faire | — | — | — |
| O1-a | à faire | — | — | — |
| O3 | à faire | — | — | — |
| O1-b | à faire | — | — | — |
| O1-c | à faire | — | — | — |
| O5-a | à faire | — | — | — |
| O5-b | à faire | — | — | — |
| O1-d | à faire | — | — | — |
| O2-a | à faire | — | — | — |
| O2-b | à faire | — | — | — |
| O2-c | à faire | — | — | — |
| O2-d | à faire | — | — | — |
| O5-c | à faire | — | — | — |
| O5-d | à faire | — | — | — |
| O4-a | à faire | — | — | — |
| O4-b | à faire | — | — | — |
| O4-c | à faire | — | — | — |
| O5-e | à faire | — | — | — |

### Indicateurs de fin (6 semaines)

| Indicateur | Aujourd'hui | Cible |
|---|---:|---:|
| Routes de calcul montées | 15 | 1 |
| Lignes de la chaîne de calcul | ≈ 14 240 | < 11 191, puis ≈ 1 500 |
| Pays sur la route unique | 2 (+14 en repli) | 52 |
| Sources du statut ZLECAf | 4 | 1 |
| Couples avec un verdict unique | 0 | 2 862 |
| Listes de membres d'accords | 6 | 1 |
| Façons de construire / déployer | 6 | 1 |
| Taux inventés servis par une route | 2 | 0 |
