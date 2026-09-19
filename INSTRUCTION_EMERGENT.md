# Instruction de reprise — Emergent

> Document de passation destiné à l'agent Emergent qui reprend le dépôt.
> Référence : `main` au commit `8fab55a` (fusion de la PR #478, 19/09/2026).
> Le document d'exploitation qui l'accompagne est `ETAT_APP_POUR_EMERGENT.md`.

---

## 0. La consigne qui prime sur toutes les autres

**N'ÉCRIS AUCUN TEST.** Ni test unitaire, ni test d'intégration, ni fichier
`test_*.py`, ni `*.test.js`, ni scénario de recette. N'en ajoute pas, n'en
complète pas, n'en « répare » pas un que tu jugerais insuffisant.

La suite existante (3 009 tests) reste en place et doit continuer à passer :
tu peux **l'exécuter** pour vérifier que tu n'as rien cassé, mais tu ne
l'étends pas. Si une modification demandée exige de modifier un test existant
pour passer, **arrête-toi et signale-le** au lieu de toucher au test : dans ce
dépôt, un test qui tombe signale presque toujours un défaut réel, pas un test
trop strict.

---

## 1. Ce qu'est cette application

Un calculateur de droits et taxes à l'importation pour les 54 États africains,
sous régime ZLECAf et sous régime de droit commun. L'utilisateur saisit un pays
d'origine, un pays de destination, une position tarifaire et une valeur ; le
moteur liquide la déclaration ligne par ligne.

- **Backend** : FastAPI (Python 3.11), point d'entrée `backend/server.py`.
- **Frontend** : React + Vite, dossier `frontend/`.
- **Moteur de calcul** : `backend/routes/calcul.py` et `backend/services/calcul.py`.
- **Données tarifaires** : le « socle », décrit au §3.

En production, un seul processus : FastAPI sert l'API **et** le frontend buildé.

---

## 2. La doctrine de la donnée — à lire avant toute modification

C'est la règle structurante du projet. Elle prime sur la complétude, sur
l'esthétique d'un résultat, et sur le confort de l'utilisateur.

**Aucune valeur fiscale n'est jamais fabriquée.** Un taux, une assiette ou une
préférence que la source ne donne pas doit remonter comme une **indisponibilité
nommée** — jamais comme un zéro, jamais comme une moyenne, jamais comme une
valeur « plausible ».

Ce que cela interdit concrètement :

- remplacer une donnée manquante par `0`, par une valeur par défaut, ou par la
  valeur d'un pays voisin ;
- généraliser une règle d'un pays à un autre (« l'Algérie fait ainsi, donc le
  Maroc aussi ») — **chaque pays se traite seul** ;
- figer une méthode de calcul dans le code parce qu'elle vaut pour un pays :
  l'Algérie, par exemple, ramène aussi le DAPS à 0 %, et cette particularité ne
  doit pas devenir la règle générale ;
- « lisser » une anomalie du document officiel. Si le barème malawien publie
  132 positions dont la préférence dépasse le plein droit, on le signale, on ne
  le corrige pas.

Ce que cela impose :

- **un zéro publié est une exonération**, pas une absence. Il se sert, nommé,
  avec son montant à 0. `test_taux_zero_est_une_donnee.py` analyse l'AST des 76
  collecteurs et fait échouer toute comparaison `> 0` portant sur un nom de
  taux : ne contourne pas ce garde ;
- une donnée douteuse est **écartée, jamais devinée**. Le collecteur angolais
  refuse 25 codes dont un chiffre est mal lu plutôt que de reconstituer le bon :
  un droit réel sous un mauvais code se liquiderait sur une autre marchandise ;
- tout taux ajouté doit citer sa **source primaire** (le texte officiel,
  article par article), avec une fiche dans
  `backend/data/legal_refs/zlecaf_application/` et l'extrait archivé + SHA-256
  dans son sous-dossier `sources/`. `scripts/verifier_fiche.py` contrôle la
  chaîne ; un octet modifié dans le texte source fait échouer la fiche.

---

## 3. Le socle — comment les données arrivent jusqu'au moteur

Trois étages, dans cet ordre. **Ne saute aucun étage et ne modifie jamais un
artefact à la main.**

```
backend/data/crawled/*.json        ← VERSIONNÉ. Sortie brute des collecteurs.
        │  python3 scripts/normalize_crawled.py       (~8 min)
        ▼
backend/data/crawled_normalized/   ← GITIGNORÉ. Régénéré, jamais commité.
        │  python3 scripts/build_socle.py             (~1 min)
        ▼
backend/socle/*.json               ← GITIGNORÉ, sauf quatre fichiers (ci-dessous).
```

**Conséquence de déploiement à ne pas manquer :** un clone frais ne contient
**aucun** fichier pays du socle. L'application ne peut pas démarrer utilement
avant d'avoir reconstruit le socle. `sync_emergent.sh` le fait déjà (étapes
3ter et 3quater) ; si tu déploies autrement, lance les deux scripts toi-même.

Quatre fichiers du socle **sont** versionnés, parce qu'ils portent des
empreintes et des références légales, pas des données dérivées :

| Fichier | Rôle |
|---|---|
| `MANIFESTE.json` | empreintes SHA-256 du socle **et** des crawls sources |
| `assiettes_pays.json` | assiette de chaque prélèvement, avec sa référence légale |
| `devises_pays.json` | devise des droits spécifiques |
| `tva_nationale.json` | TVA établie sur source primaire, pour les pays dont le crawl n'en porte aucune |

`backend/services/socle.py` est **le seul point d'entrée** vers le socle. Il
vérifie deux empreintes au chargement : celle du fichier de socle contre le
manifeste, et celle du crawl source contre l'empreinte enregistrée à la
construction. Un socle périmé devient **inerte** plutôt que de servir en
silence des montants qui ne correspondent plus. Ne contourne pas ce contrôle :
si un chargement échoue, la bonne réponse est de **reconstruire**, pas de
désactiver la vérification.

Si tu modifies un crawl ou un collecteur, tu dois ensuite mettre à jour, dans
le même commit :

1. `backend/socle/MANIFESTE.json` (par `build_socle.py`) ;
2. `backend/data/source_registry_v2.json` (empreinte + `positions_count`) ;
3. `data/<pays>/legal_sources.json` (empreinte + notes).

`test_dataset_hash_stores_agree.py` échoue si l'un des trois diverge.

---

## 4. État actuel

**54 pays au socle, 367 340 positions**, dont 23 en couverture `COMPLET`,
29 en `PARTIEL`, 2 déclarés `VIDE` (Djibouti, Érythrée — déclarés vides, jamais
estimés).

Intégrés récemment, depuis le texte officiel et non depuis un agrégateur :

| Pays | Source | Positions | Particularité |
|---|---|---|---|
| Malawi | Customs and Excise (Tariffs) (No. 3) Order, 2022 | 7 364 | 9 colonnes ; la col. 5 est le plein droit, les col. 6-9 des remises par origine |
| Seychelles | S.I. 113 of 2022 | 6 019 | 13 colonnes, calendrier ZLECAf 2022-2026 ; taux COI dérivé de la Schedule II |
| Angola | DLP n.º 1/24 | 5 959 | lu **optiquement** : le Diário est un scan sans couche texte |
| Libye | tarif national 2022 | 5 920 | 62 interdictions d'importer ; pas de TVA (la loi n'en prévoit pas) |
| Mauritanie | tarif national | 6 129 | DD + RS + PC + TVA, toutes assiettes établies |

**Le cas angolais mérite une mise en garde.** Un « Projecto da Pauta » avec
couche texte circule sur le même serveur ministériel — donc beaucoup plus
facile à lire que le scan. **Il diverge de la loi sur 730 des 3 058 taux
comparables.** Ne l'utilise pas, même pour « vérifier » ou « compléter ».

Deux particularités angolaises à ne pas prendre pour des bugs :

- les colonnes 5 (SADC) et 6 (ZCLCA) sont **publiées vides, exprès** : l'art.
  43.º n.º 2 les déclare réservées à une législation à venir. Ne les remplis pas ;
- les *emolumentos gerais aduaneiros* de 2 % **survivent aux exonérations**
  (art. 43.º n.º 4), et se liquident sur la même assiette que le droit.

---

## 5. Ce qui reste ouvert — déclaré, pas comblé

Ne « répare » aucun de ces points en inventant la donnée manquante.

- **Taux de São Tomé-et-Príncipe** : non collectés. `dre.gov.st` est refusé par
  le proxy réseau (CONNECT 502). L'assiette, elle, est établie.
- **Taux des Comores** : non collectés, aucune URL citable trouvée. L'assiette
  est établie.
- **Grammaire FOB du moteur** : deux bases d'évaluation divergentes coexistent
  dans la donnée — la SACU liquide sur le prix FOB (Act 91 of 1964, s.65(1)),
  la Somalie sur le CIF. Le moteur ne reçoit qu'un seul montant, `valeur_cif`.
  Tant que le calculateur ne sait pas **ce que le prix saisi contient**, l'une
  des deux est fausse. C'est un chantier de conception, pas une correction.
- **Assiette IAT/EXC nigériane** : non établie (`etabli: false`). Les 12 700
  droits nigérians non liquidables le restent. Ne leur pose pas `CIF` de mémoire.
- **TVA somalienne** : non collectée, nommée `NON_TRACEE_A_LA_SOURCE`.
- **Résidu OCR angolais** : 8 codes sur 5 959 (0,13 %) portent une sous-position
  qui n'existe dans aucune autre nomenclature. Mesuré, déclaré dans le crawl
  (`residu_connu`) et dans `data/angola/legal_sources.json`. Ne les corrige pas
  d'après une nomenclature tierce : elle écarterait aussi des sous-positions
  proprement angolaises (2903.39 porte seize extensions nationales que personne
  d'autre ne publie).
- **Chemin historique** `/authentic-tariffs/calculate`, qui double `/calcul`.
  Sa dépose est la correction de fond, non faite.

---

## 6. Déploiement

Dans le Shell Emergent :

```bash
BRANCH=main bash sync_emergent.sh
```

Le script aligne le déploiement exactement sur `main` (`git reset --hard`),
vérifie la présence des modules critiques, réinstalle le backend, **normalise
les crawls et reconstruit le socle**, puis rebuild le frontend.

Puis :

```bash
bash start.sh    # dev : backend 8000 + Vite 5000
# ou, production mono-processus :
cd backend && python -m uvicorn server:app --host 0.0.0.0 --port 5000
```

Contrôles rapides :

```bash
curl -s http://localhost:8000/api/reports/health
curl -s http://localhost:8000/api/reports/oec-health
```

---

## 7. Conventions de code

- Python : `black --line-length 100`, `flake8 --max-line-length=110`.
- **`pytest-timeout` n'est pas installé** : ne passe jamais `--timeout`.
- La suite se lance **depuis la racine** du dépôt, pas depuis `backend/` —
  sinon les imports du paquet racine `engine/` cassent :

  ```bash
  python3 -m pytest backend/tests/ --ignore=backend/tests/test_notifications.py
  ```

- Les commentaires et messages de commit du dépôt sont **en français**. Suis
  cet usage.
- Ne commite jamais `backend/data/crawled_normalized/` ni les fichiers pays de
  `backend/socle/` : ils sont gitignorés parce qu'ils sont régénérables.

---

## 8. Résumé en cinq lignes

1. **Aucun test écrit.** Tu peux exécuter la suite, pas l'étendre.
2. Aucune valeur fiscale fabriquée : une lacune se nomme, elle ne se comble pas.
3. Un pays à la fois ; ne généralise jamais une règle nationale.
4. Le socle se reconstruit, il ne s'édite pas ; un socle périmé doit rester inerte.
5. Tout taux ajouté cite son texte officiel, article par article, avec l'extrait
   archivé et son empreinte.
