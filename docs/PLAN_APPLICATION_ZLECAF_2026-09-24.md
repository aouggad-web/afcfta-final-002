# Plan — Débloquer l'application ZLECAf pays par pays

> À remettre au collaborateur. Ce document dit **ce qui est attendu**, **dans
> quel ordre**, **dans quelle forme**, et **ce qui sera refusé**. Chaque livraison
> est relue et corrigée avant fusion. Rien n'est fusionné sans l'accord du
> propriétaire.

---

## 0. Le problème, en une phrase

Le calculateur n'accorde aujourd'hui la préférence ZLECAf qu'à **trois pays
importateurs** : Algérie, Afrique du Sud, Kenya. Tous les autres restent au taux
NPF, même quand ils ont ratifié l'accord et même quand leur barème est déjà dans
le dépôt. La note du ministère sud-africain du commerce (dtic) et de la SARS
(mars 2026) compte pourtant **25 pays** en application effective.

## 1. Ce qui est déjà acquis — à lire avant de commencer

Tout le travail de preuve est rangé dans
`backend/data/legal_refs/zlecaf_application/` :

| Fichier | Contenu |
|---|---|
| `etat_application_54_pays_2026-09-13.json` | état par pays, niveaux de preuve, recoupements de réciprocité |
| `EGY_application_2026-09-14.json` | Égypte : circulaire n° 38, 17 origines, **preuves réunies** |
| `MAR_application_2026-09-13.json` | Maroc : circulaire 6530/223, 40 origines, **preuves réunies** |
| `TUN_application_2026-09-13.json` | Tunisie : 8 origines publiées, **sens du taux non tranché** |
| `DZA_application_2026-09-14.json` | Algérie : circulaire 482/2024 (déjà appliquée) |
| `ETH_application_2026-09-13.json` | Éthiopie : règlement 574/2025, liste des origines manquante |
| `chantier_collecte_2026-09-14.json` | ce qui manque, destination par destination |

Code concerné :

- `backend/services/zlecaf_implementation_registry.py` — le verrou. Seules les
  entrées de `RECORDS` au statut `APPLIED` débloquent un calcul.
- `backend/services/official_preferential_rates.py` — lecture des barèmes de
  l'e-Tariff Book (`data/official_preferential/*.json.gz`) et
  `CARTES_ORIGINES_NATIONALES` (choix du barème d'après l'acte national, déjà
  branché pour le Maroc).
- `backend/services/authentic_tariff_service.py` et `backend/services/preference.py`
  — les deux chemins de calcul ; ils appellent tous deux `implementation_decision`.

## 2. La règle de preuve — non négociable

Un pays importateur passe à `APPLIED` **uniquement** si les trois conditions
suivantes sont réunies sur **source primaire lue intégralement** :

1. **Un acte national en vigueur** (décret, circulaire douanière, gazette), avec
   sa référence, sa date, son URL et le SHA-256 du document archivé.
2. **La liste nominative des origines admises** par ce pays importateur.
3. **Le barème ligne par ligne** et la règle qui dit quel barème s'applique à
   quelle origine, pour quelle année.

### La réciprocité croisée est une piste, jamais une preuve

Que l'Algérie nomme la Tunisie parmi ses partenaires réciproques **ne prouve pas**
que la Tunisie accorde la ZLECAf aux produits algériens. Contre-exemple vérifié
dans le dépôt : la circulaire algérienne 482/2024 nomme la Tunisie, mais le tarif
officiel tunisien ne publie **aucune** préférence ZLECAf pour l'Algérie (ni pour
l'Égypte, ni pour le Maroc) ; la Tunisie les sert sous d'autres accords
(bilatéraux, Agadir, Grande zone arabe de libre-échange).

Une liste de partenaires publiée par un pays **A** sert donc à *choisir où
chercher* le texte du pays **B**. Elle ne remplace jamais ce texte.

## 3. Travail demandé, dans l'ordre

Une PR par pays. Ne pas passer au pays suivant avant relecture du précédent.

### Étape 1 — Égypte (preuves réunies, reste le branchement)

Acquis : circulaire Accords n° 38 (Autorité égyptienne des douanes, publiée le
31/12/2025), 17 origines en deux groupes :

- groupe **10 ans** (réciprocité) : ZAF, BWA, GHA, KEN, CMR, SWZ — 50 % de
  réduction au 1er janvier 2025 ;
- groupe **5 ans** : MAR, RWA, TZA, MUS, TUN, DZA, BDI, LSO, MWI, GMB, UGA —
  100 % de réduction au 1er janvier 2025 ;
- **liste A seulement** : les listes B et C « ne sont pas encore entrées en
  vigueur ».

À faire :

1. **Rapprocher les deux groupes de la circulaire des deux barèmes de l'UA**
   (`EGY_afcfta_etariff_2026-08-17.json.gz`). La carte de l'UA ne recouvre pas
   la circulaire : elle range par exemple l'Afrique du Sud et le Kenya avec
   l'Algérie dans le barème 1, alors que la circulaire les sépare (10 ans contre
   5 ans). Sur **au moins 20 lignes réelles** de la liste A (taux NPF variés),
   comparer pour 2025 et 2026 :
   - le taux du barème 1 et du barème 2 de l'UA ;
   - le taux qui résulte de la circulaire (NPF × part restante).

   Livrer le tableau de comparaison. **La circulaire fait foi** (même doctrine
   que le Kenya, où le Journal officiel prime sur l'e-Tariff Book). Si aucun
   barème de l'UA ne reproduit la circulaire, le taux se calcule à partir du
   NPF et du calendrier, comme pour l'Algérie (`zlecaf_schedule_dza.py`) — ne pas
   deviner, montrer.
2. **Établir le calendrier 2026 du groupe 10 ans** à partir du texte (la
   circulaire donne 50 % au 1/1/2025 ; le taux au 1/1/2026 doit être lu ou
   explicitement dérivé de la règle « annuités égales » que le texte énonce, avec
   la citation).
3. **Chercher une circulaire postérieure au 31/12/2025** sur
   `https://customs.gov.eg/Legislations/Manshorat?categoryId=4` (mise à jour des
   listes, entrée en vigueur des listes B et C). Consigner le résultat, même
   négatif, avec la date de consultation.
4. **Classer chaque ligne en A / B / C.** Une ligne B ou C reste au NPF.
5. Brancher : entrée `RECORDS["EGY"]` au statut `APPLIED`, origines = les 17 de
   la fiche, lues **depuis la fiche** (pas recopiées à la main).
6. Tests : un test par groupe (une origine 10 ans, une origine 5 ans), un test
   « origine hors liste → NPF », un test « ligne B → NPF », un test « le taux
   préférentiel n'est jamais servi au-dessus du NPF ».

### Étape 2 — Maroc (preuves réunies, deux questions ouvertes)

Acquis : circulaire ADII 6530/223 du 22/01/2024, 40 origines (P1 : 27 pays à
5 ans ; P2 : 13 pays à 10 ans), liste A seulement. La carte des origines est
**déjà branchée** (`CARTES_ORIGINES_NATIONALES`) ; seule l'entrée `RECORDS["MAR"]`
manque.

À faire :

1. **Chercher une notification postérieure au 22/01/2024** qui modifie P1/P2
   (la circulaire annonce que les listes « sont appelées à évoluer »). Résultat
   consigné, même négatif.
2. **Taxe parafiscale à l'importation (TPI) — décision du propriétaire, le
   24/09/2026** : la TPI est un prélèvement d'effet équivalent au droit de douane,
   comme le DAPS algérien. **Elle entre dans le périmètre ZLECAf** et se réduit
   avec le droit d'importation, comme la circulaire le prévoit
   (`instrument.taxes_covered` de la fiche : « DI » et « TPI »).
   - **Citer le passage de la circulaire** qui soumet la TPI au démantèlement
     (page et verbatim) et dire **selon quel calendrier** : le même que le DI
     (P1 à 5 ans, P2 à 10 ans), ou une exonération immédiate comme le DAPS ?
     Ne pas supposer, citer.
   - Vérifier ce que change l'avenant **6627/223 du 09/01/2025** (déjà listé dans
     `amendments` de la fiche).
   - Modèle de code : le DAPS algérien, exonéré par `PERIMETRES_NATIONAUX` dans
     `backend/services/preference.py` (chemin du socle). Le chemin historique
     (`authentic_tariff_service.py`) doit donner **le même résultat** : un test
     compare les deux chemins sur une même ligne.
   - La TPI ne se réduit **que** pour une origine admise **et** une ligne de la
     liste A. Hors de ces cas, elle reste pleine.
   - Attention à la TVA : son assiette est `CIF+DD+TPI`
     (`backend/socle/assiettes_pays.json`). Réduire la TPI réduit donc l'assiette
     de la TVA ; le test doit le vérifier sur un montant.
3. Brancher `RECORDS["MAR"]`, tests sur le même modèle que l'Égypte, plus un test
   TPI (origine P1, origine P2, origine hors liste).

### Étape 3 — Tunisie (bloquée, recherche de texte)

Acquis : le tarif officiel publié (douane.gov.tn) porte une préférence ZLECAf
pour **8 origines seulement** : CMR, GHA, KEN, TZA, ZAF, NGA, MUS, RWA.
**Ni l'Algérie, ni l'Égypte, ni le Maroc.**

Bloquant : le sens du pourcentage publié n'est pas connu. Sur la position
01012100015, le NPF est de 36 % et la « préférence ZLECAf » affichée de 40 %,
donc supérieure au NPF. Est-ce un taux de réduction ou un reste à payer ?

À faire :

1. **Trouver le texte d'application au Journal officiel tunisien (JORT).** Une
   source secondaire cite le JORT n° 16 du 6 avril 2023 : le retrouver sur le
   Journal officiel lui-même, l'archiver avec son SHA-256.
2. **Trancher le sens du pourcentage** à partir d'un texte (note d'application,
   circulaire de la douane tunisienne), **pas** par déduction à partir des
   chiffres.
3. Tant que ces deux points ne sont pas établis : **aucun branchement**. La
   Tunisie reste au NPF.

### Étape 4 — Les quatre pays dont il manque la liste des origines

Éthiopie (règlement 574/2025), Zambie (SI 92/2024), Côte d'Ivoire (ordonnance du
23/04/2025), Nigeria (tarif publié au journal officiel en avril 2025). Le texte
national existe ; il manque **la liste officielle des origines admises**.

Pour chacun, livrer une fiche `<ISO3>_application_<date>.json` sur le modèle de
`EGY_application_2026-09-14.json`, avec :
- le document cible (avis ministériel, circulaire douanière) ;
- les endroits cherchés et la date de consultation ;
- le résultat, même négatif.

### Étape 5 — Pays non recherchés, par ordre de priorité

Ordre fixé par le nombre de listes officielles vérifiées (Algérie, Afrique du
Sud, Maroc, Égypte, Tunisie) qui les nomment comme partenaires actifs. C'est un
ordre de recherche, pas une preuve.

| Priorité | Pays | Nommé par |
|---|---|---|
| 1 | Tanzanie, Maurice | 4 listes |
| 2 | Ouganda, Gambie, Burundi | 3 listes |
| 3 | Eswatini, Sierra Leone, Malawi, Lesotho, Botswana | 2 listes |
| 4 | les autres pays nommés par le seul Maroc | 1 liste |

Pour chaque pays : même fiche qu'à l'étape 4 (acte, origines, barème, ou
résultat négatif daté).

Point de rattrapage : `etat_application_54_pays_2026-09-13.json` classe encore
l'Afrique du Sud en `NON_RECHERCHE`, alors que le calcul l'applique déjà
(`zlecaf_schedule_zaf.py`). Mettre la fiche à jour.

## 4. Forme des livraisons

- **Une fiche JSON par pays** dans `backend/data/legal_refs/zlecaf_application/`,
  l'extrait du document dans `sources/`, contrôlée par
  `python3 scripts/verifier_fiche.py`.
- Chaque citation reprend le texte **tel qu'imprimé** (verbatim), dans sa langue
  d'origine, avec la traduction à côté.
- `etat_application_54_pays_2026-09-13.json` mis à jour dans la même PR
  (niveau du pays, preuve, `recoupements_reciprocite`).
- Contrôles avant PR, depuis la racine du dépôt :
  `python3 -m pytest`, `flake8 .`, `black --line-length 100` sur les lignes
  modifiées seulement.

## 5. Ce qui fait refuser une livraison

1. **Un pays passé en `APPLIED` sans les trois preuves du § 2.**
2. **Une origine déduite de la liste d'un autre pays** (réciprocité croisée).
3. **Une source secondaire à la place d'un texte** : presse, tralac, portails
   privés, cabinets, synthèses. Elles servent à repérer un texte, jamais à le
   remplacer.
4. **Un taux préférentiel servi au-dessus du NPF.**
5. **Une taxe ou une accise réduite** : seul le droit de douane entre dans le
   périmètre. Seule exception : un prélèvement d'effet équivalent que l'acte
   national soumet lui-même au démantèlement, texte cité (DAPS algérien, TPI
   marocaine). La TVA et les accises ne sont jamais réduites.
6. **Une liste recopiée à la main dans le code** alors qu'elle existe dans une
   fiche.
7. **Un contournement technique** : vérification TLS désactivée, proxy
   contourné. Un site inaccessible se signale, il ne se force pas.
8. **Plusieurs pays dans une même PR.**

## 6. Décisions réservées au propriétaire

Le collaborateur les pose, il ne les tranche pas :

- ~~**Maroc — TPI**~~ : **tranché le 24/09/2026** — effet équivalent au droit de
  douane, comme le DAPS algérien : réduite avec le droit (voir étape 2).
- **Égypte** : si le rapprochement montre qu'aucun barème de l'UA ne reproduit
  la circulaire, calculer à partir du NPF et du calendrier ?
- **Tunisie** : si le sens du pourcentage reste introuvable, garder le NPF et
  afficher le taux publié « à titre informatif » ?

## 7. Relecture

Chaque PR est relue avant fusion : lecture des sources archivées, contrôle des
SHA-256, recalcul de lignes au hasard, et parcours du calculateur dans
l'interface (origine admise, origine refusée, ligne hors liste A). Les écarts
sont corrigés dans la PR elle-même.
