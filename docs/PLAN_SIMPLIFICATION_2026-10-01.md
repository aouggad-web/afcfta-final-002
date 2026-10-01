# Plan — Simplifier : une question, une réponse, un chemin

> Établi le 1ᵉʳ octobre 2026 sur `main@e42c223`, par lecture directe du dépôt
> (copie locale et digest gitingest du même commit : 1 957 fichiers de moins de
> 50 ko, environ 4,4 M de tokens). Ce document **ne modifie aucune donnée**.
> Il fixe cinq objectifs, leur ordre, et le critère qui dit qu'ils sont
> atteints.
>
> **Règle de ce plan : chaque lot doit retirer plus de choses qu'il n'en
> ajoute** (code, fichiers, statuts, documents). Un lot qui ajoute une couche
> sans en retirer une est refusé.

---

## 0. En une page

| # | Objectif | Ce que l'utilisateur ou le propriétaire voit à la fin | Critère d'acceptation |
|---|---|---|---|
| **O1** | Le calculateur répond **d'abord** à « la ZLECAf s'applique-t-elle entre ces deux pays ? » | Une carte-verdict en tête des résultats : **5 réponses possibles**, une couleur, une phrase, la preuve (acte, date, lien), puis le montant | 100 % des 2 916 couples ont **un seul** verdict, servi par **une seule** source ; l'interface ne calcule aucun statut |
| **O2** | Un seul chemin de calcul, un seul socle, une seule source par information | Le même montant, quelle que soit la route ou l'écran | 1 route de calcul, 1 appel dans l'interface, 0 repli silencieux, 1 fichier faisant foi par type d'information |
| **O3** | Le propriétaire sait **ce qui manque, pays par pays** | Un tableau unique, régénéré automatiquement : tarif, TVA, assiettes, formalités, preuves ZLECAf, accords | 54 lignes, aucune case vide « inconnue », une priorité par pays |
| **O4** | Comparer ZLECAf / GZALE / accords bilatéraux / communauté économique, et dire lequel est **le plus avantageux** | Pour un couple : un tableau des régimes ouverts, leur statut, leur montant, la règle d'origine, et le régime le moins coûteux mis en avant | Aucun taux d'un régime servi sous le nom d'un autre ; « plus avantageux » choisi **uniquement** parmi les régimes au statut « appliqué » |
| **O5** | Une production qui se maintient seule | Une seule construction, un seul déploiement, un serveur qui refuse de démarrer sur une donnée altérée, des rapports régénérés chaque semaine | Même résultat en local, en CI et en production ; `/api/health` dit l'état des données ; une procédure d'exploitation d'une page |

Ordre : **O1 → O2 → O4**, avec **O3 et O5 en parallèle** dès la première
semaine (O3 est un script de lecture ; O5 ne touche pas au calcul).

---

## 1. Constat mesuré — pourquoi simplifier

### 1.1 Trop de statuts pour une seule question

La question « la ZLECAf s'applique-t-elle entre A et B ? » reçoit aujourd'hui
**quatre vocabulaires**, rangés dans **quatre endroits** qui ne disent pas la
même chose :

| Endroit | Vocabulaire | Nombre d'états |
|---|---|---:|
| `backend/services/zlecaf_implementation_registry.py` (le verrou du calcul) | `APPLIED`, `OFFER_ONLY`, `PARTNER_NOTICE_REQUIRED`, `NOT_AVAILABLE` | 4 |
| `backend/data/legal_refs/zlecaf_application/etat_application_54_pays_2026-09-13.json` | `APPLIQUE`, `PREUVES_ASSEMBLEES`, `INSTRUMENT_VERIFIE_BAREME_MANQUANT`, `NOTIFICATION_PARTENAIRES_REQUISE`, `OFFRE_SEULE`, `NON_APPLIQUE_PRESUME`, `NON_RECHERCHE`, `ORIGINES_PUBLIEES_SEMANTIQUE_INDETERMINEE`, `INSTRUMENT_RAPPORTE_NON_PRIMAIRE` | 9 |
| `reports/ETAT_APPLICATION_BILATERAL.json` (matrice des couples) | `ACCORDEE`, `NON_ACCORDEE`, `ADMISSION_PAR_REGLE`, `DESTINATION_NON_ETABLIE`, `ORIGINE_NON_RATIFIANTE`, `MEME_PAYS` | 6 |
| `frontend/src/components/calculator/zlecafAvailability.js` | `DOCUMENTED`, `OFFER_ONLY`, `PARTNER_NOTICE_REQUIRED`, `NOT_AVAILABLE` | 4 |

Conséquence relevée : les sources divergent déjà.

| Fait | Fichier d'état | Registre du calcul | Matrice bilatérale |
|---|---|---|---|
| Pays « appliqués » | 8 : EGY, KEN, MAR, RWA, SYC, TZA, UGA, ZAF | 6 `APPLIED` : KEN, TZA, RWA, UGA, EGY, MAR (+ ZAF et DZA par modules à part) | 6 destinations **écrites en dur** : DZA, EGY, KEN, MAR, TUN, ZAF |
| Seychelles | `APPLIQUE` (SI 113/2022) | **absentes** → `NOT_AVAILABLE` | non établie |
| Algérie | `PREUVES_ASSEMBLEES` | servie par l'ancien chemin seulement ; **jamais** par `POST /calcul` (`preference.py:223`) | établie |
| Ghana, Tunisie, Zimbabwe, Burundi | 4 niveaux différents | `OFFER_ONLY` ou `NOT_AVAILABLE` | — |
| Ratification | — | `zlecaf_membership_status.py` : 5 non-ratifiants, **tout autre code = ratifié par défaut** | origine seulement, jamais la destination |

Trois défauts qui touchent directement l'utilisateur :

1. **Somalie** : la liste de l'UA au 22/05/2026 (archivée,
   `sources/AU_liste_signatures_ratifications_zlecaf_2026-05-22.pdf`, ligne 45)
   la donne **signataire, non ratifiante** ; le code la traite comme ratifiante,
   parce que le défaut est « ratifié ». Six pays n'ont pas ratifié — BEN, ERI,
   LBY, SDN, SOM, SSD — et non cinq.
2. **Unions douanières ignorées par la matrice** : Kenya ← Tanzanie y figure
   `NON_ACCORDEE`, alors que le moteur applique à juste titre l'union douanière
   EAC à 0 %. 148 couples sont dans ce cas.
3. **L'interface confond** `OFFER_ONLY` et `PARTNER_NOTICE_REQUIRED` : même
   bandeau « Offre publiée … à vérifier » (`CalculatorTab.jsx:804-807`,
   `1755-1780`). Et `KpiRow.jsx:18` écrit en dur « 54 signataires · 48
   ratifications » au lieu de le lire.

### 1.2 Trop de chemins pour un seul montant

`docs/PLAN_CALCULATEUR_UNIQUE.md` (15/09) visait **11 191 → ~1 500 lignes** et
**un seul appel** dans l'interface. Le socle et le moteur existent
(`backend/socle/`, `backend/services/calcul.py`, `preference.py`), mais
l'ancien chemin n'a pas été retiré et l'interface a **grossi** :
`CalculatorTab.jsx` est passé de 2 016 à **2 522 lignes**, et le dossier
`components/calculator/` compte 6 737 lignes. L'interface interroge d'abord le
nouveau moteur pour **2 pays seulement**, l'ancien pour 38 (§ 3.1).

### 1.3 Trop de documents pour une seule direction

154 fichiers Markdown, dont une cinquantaine de plans, audits, états et
instructions (racine, `docs/`, `audits/`, `reports/`), et six façons
documentées de lancer ou de publier l'application (Emergent, Replit, Docker,
VS Code, GitHub Pages, script `start.sh`). Plusieurs plans se remplacent les uns les autres
(`PLAN_CORRECTION_CALCULATEUR` → `PLAN_CALCULATEUR_UNIQUE`) sans que l'ancien
soit archivé. C'est l'origine de l'« errance » : chaque session repart d'un
document différent.

### 1.4 Ce qui est solide et qu'on garde tel quel

- **La règle de preuve** (`docs/PLAN_APPLICATION_ZLECAF_2026-09-24.md` § 2) :
  acte national + liste nominative des origines + barème ligne par ligne, sur
  source primaire. Ce plan ne l'assouplit pas ; il simplifie **l'affichage** de
  son résultat.
- **Le verrou fail-closed** : aucun taux préférentiel n'est liquidé sans couloir
  autorisé.
- **Le socle** (`backend/socle/MANIFESTE.json` : 54 pays, 368 260 positions,
  23 `COMPLET`, 29 `PARTIEL`, 2 `VIDE`) et les fiches par pays.

---

## 2. O1 — Le verdict ZLECAf en tête des résultats

### 2.1 Les cinq réponses

La réponse porte sur un **sens** de flux : origine O → destination D (c'est la
destination qui accorde ou non la préférence). Les quatre catégories demandées,
plus une cinquième indispensable pour ne rien classer à tort :

| Verdict | Couleur | Phrase affichée | Ce que le calculateur fait |
|---|---|---|---|
| **1. ZLECAf appliquée** | vert | « La ZLECAf est appliquée par D aux produits de O. » + acte, date, lien | Calcule NPF **et** ZLECAf, affiche l'économie |
| **2. Documentée, preuve manquante** | orange | « D a pris un acte d'application, mais [la liste des origines / le barème / le sens du taux] manque. » | Calcule le NPF ; nomme la pièce manquante ; taux de l'offre affiché **à titre indicatif** s'il existe |
| **3. Offre seulement** | jaune | « D a une offre tarifaire adoptée par l'UA, aucun acte national d'application n'est vérifié. » | Calcule le NPF ; taux de l'offre **indicatif** s'il est au dépôt |
| **4. Ratifiée, sans offre** | gris | « D a ratifié l'accord mais n'a pas d'offre tarifaire publiée. » | Calcule le NPF |
| **5. Non applicable** | rouge | « O (ou D) n'a pas ratifié » **ou** « D applique la ZLECAf, mais sa liste ne nomme pas O » | Calcule le NPF ; donne la raison |

Le verdict 5 regroupe deux raisons différentes, toujours écrites en clair
dans la phrase : la ratification manque, ou bien la destination applique
l'accord sans admettre cette origine.

**Cas particulier, traité avant tout le reste : même union douanière** (SACU,
EAC, CEMAC, UEMOA). La carte dit « Union douanière EAC : libre circulation,
la ZLECAf est sans objet entre ces deux pays » et le calcul sert le régime de
l'union. C'est déjà ce que fait le moteur (`regional_blocs.same_customs_union`) ;
seul l'affichage manque.

Sous la carte, une ligne pour le **sens inverse** (D → O), puisque la question
posée est « entre ces deux pays » et que la réciprocité n'est pas garantie
(8 asymétries déjà constatées, ex. Algérie → Kenya accordé, Kenya → Algérie
non).

**Le verdict dépend aussi de la date d'importation.** Les dates d'entrée en
vigueur diffèrent selon le pays d'origine (dates par origine pour l'Afrique du
Sud, groupes à 5 et 10 ans pour l'Égypte et le Maroc, démarrage de l'Ouganda
au 13/02/2026). Le verdict est donc calculé à la date du jour, et la carte
affiche cette date.

**Répartition attendue des 2 862 couples** (hors couples d'un pays avec
lui-même), estimée le 01/10/2026 à partir des données actuelles et de la
liste de l'UA. Le lot O1-a la recalculera.

| Verdict | Couples |
|---|---:|
| Même union douanière | 148 |
| 1 — Appliquée | 189 |
| 2 — Documentée, preuve manquante | 323 |
| 3 — Offre seulement | 1 365, dont 1 234 où **personne n'a encore cherché** l'acte national |
| 4 — Ratifiée, sans offre | 94 |
| 5 — Non applicable | 743, dont 580 pour défaut de ratification et 163 pour origine non admise |

Le chiffre qui oriente la collecte est celui du verdict 3 : **1 234 couples
sont « offre seulement » faute de recherche**, et non faute d'acte. La carte le
dit (« application non encore vérifiée »), pour ne pas laisser croire qu'une
recherche a conclu à l'absence d'acte.

### 2.2 La règle de décision — une fonction, appliquée dans l'ordre

```
verdict(O, D, date) :
  0. O et D dans la même union douanière                           → cas particulier « union douanière »
  1. O ou D non ratifiant (BEN, ERI, LBY, SDN, SOM, SSD au 22/05/2026) → 5 Non applicable
  2. D a une liste vérifiée ET O n'y figure pas                     → 5 Non applicable
  3. D au niveau APPLIQUE, O sur la liste de D, barème ligne présent → 1 Appliquée
  4. D a un acte national vérifié ou rapporté (niveaux du verdict 2
     ci-dessous), ou admet les origines par une règle (GHA, NGA),
     ou est APPLIQUE mais la ligne manque au barème                  → 2 Documentée, preuve manquante
  5. D a une offre adoptée par l'UA (e-Tariff Book)                 → 3 Offre seulement
  6. sinon                                                          → 4 Ratifiée, sans offre
```

Correspondance avec les neuf niveaux actuels du fichier d'état :

| Niveau actuel | Verdict |
|---|---|
| `APPLIQUE` (+ origine admise + ligne au barème) | 1 |
| `PREUVES_ASSEMBLEES`, `INSTRUMENT_VERIFIE_BAREME_MANQUANT`, `NOTIFICATION_PARTENAIRES_REQUISE`, `ORIGINES_PUBLIEES_SEMANTIQUE_INDETERMINEE`, `INSTRUMENT_RAPPORTE_NON_PRIMAIRE` | 2 |
| `OFFRE_SEULE` ; `NON_RECHERCHE` ou `NON_APPLIQUE_PRESUME` **avec** offre UA | 3 |
| `NON_RECHERCHE` **sans** offre UA | 4 |

Les neuf niveaux restent dans les fiches : ils servent au travail de preuve.
L'utilisateur, lui, n'en voit que cinq.

### 2.3 Une seule source, générée

1. **Un seul fichier fait foi** : `reports/ETAT_APPLICATION_BILATERAL.json`,
   généré par `scripts/build_bilateral_application_matrix.py` **à partir des
   fiches**, enrichi d'un champ `verdict` (1 à 5), de `piece_manquante`, et
   de la date de la preuve. Le générateur cesse d'écrire en dur ses six
   destinations : il lit les fiches, contrôle la ratification **des deux**
   pays et les unions douanières. Il s'appuie sur deux tables qui n'existent
   pas encore sous forme lisible par machine :
   - **ratification** : une table datée de 54 lignes, tirée du PDF de l'UA
     archivé. Un code absent de la table donne « inconnu », plus jamais
     « ratifié » par défaut ;
   - **offre tarifaire** : une ligne par pays (soumise, adoptée, aucune), y
     compris le « aucune offre » explicite de DJI, ERI, LBY, SDN, SOM, et le cas
     STP à trancher.
2. `zlecaf_implementation_registry.RECORDS` est **lu depuis les fiches**, plus
   écrit à la main — c'est déjà la règle 6 du plan d'application (« une liste
   recopiée dans le code est refusée »).
3. L'API renvoie `verdict`, `phrase`, `piece_manquante`, `preuve` ; l'interface
   **affiche** et ne déduit plus rien (`zlecafAvailability.js` réduit à un
   affichage).
4. Un test CI échoue si le registre, le fichier d'état et la matrice ne disent
   pas la même chose pour un couple.

### 2.4 L'écran de résultats, simplifié

Ordre d'affichage, de haut en bas, et rien d'autre au premier niveau :

1. **Carte-verdict** (§ 2.1) — pour les deux sens.
2. **Deux montants** côte à côte : total NPF, total ZLECAf (ou « non calculé »
   et la raison). L'économie seulement si les deux sont `COMPLET`.
3. **État du calcul** : `COMPLET` / `PARTIEL` (avec ce qui manque, ex. « TVA
   non collectée ») / `INDISPONIBLE`.
4. **Source** : fichier, date de collecte.
5. Le reste — détail ligne à ligne, journal, formalités, réglementation,
   calendrier de démantèlement, comparatif multi-pays — **replié** sous
   « Voir le détail ».

Défauts d'affichage relevés, corrigés dans le même lot :

| Défaut | Où | Effet pour l'utilisateur |
|---|---|---|
| Un total `INDISPONIBLE` s'affiche « 0,0 % » | `CalculatorTab.jsx:1740` (`total_taxes_npf \|\| 0`) | croit ne rien payer |
| Un total `PARTIEL` s'affiche sans marque | idem | croit le total complet |
| Entre membres d'une union douanière, le total à 0 % est calculé mais la carte dit « Taux non disponible » | cartes de synthèse | ne voit pas son meilleur régime |
| Le calendrier de démantèlement reçoit toujours un NPF à 0 | `CalculatorTab.jsx:1828` | lit « déjà en franchise » partout |
| Le panneau réglementaire affiche des totaux d'une autre source, sans contrôle d'origine | `RegulatoryDetailsPanel.jsx` | voit deux totaux différents |
| Source et date de collecte jamais affichées ; `last_verified` vaut `'2025-02'` par défaut | ancien chemin | ne sait pas de quand date le taux |

### 2.5 Livrables et critères — O1

| Lot | Livrable | Acceptation |
|---|---|---|
| O1-a | Tables ratification + offre ; `verdict` ajouté à la matrice générée ; test de cohérence registre / état / matrice ; test « matrice à jour » | 2 916 couples, chacun un verdict ; Somalie non ratifiante ; aucun défaut « ratifié » ; les divergences du § 1.1 disparaissent ; test CI rouge si elles reviennent |
| O1-b | `RECORDS` lu depuis les fiches ; Seychelles branchées ; Algérie servie par `POST /calcul` | plus aucune liste d'origines écrite dans `zlecaf_implementation_registry.py` ; un test DZA←EGY sur la route unique |
| O1-c | Champ `verdict` dans la réponse de la route de calcul | un test par verdict (5 tests), plus un test sens inverse |
| O1-d | Carte-verdict + écran replié | le premier écran tient sans défilement sur mobile ; aucun statut calculé côté interface |

---

## 3. O2 — Un chemin, un socle, une source par information

### 3.1 Inventaire de départ

**Quinze routes de calcul sont montées ; trois produisent un montant que
l'interface affiche, et une quatrième affiche des totaux d'une autre source :**

| Route | Moteur | Appelée par l'interface |
|---|---|---|
| `POST /api/calcul` (`routes/calcul.py`) | socle + `services/calcul.py` + `preference.py` — **la cible** | **en premier pour 2 pays** (`SOCLE_EN_PREMIER = {'TUN', 'MUS'}`, `CalculatorTab.jsx:478`) ; en repli pour 14 autres (AGO COM DJI ERI LBY MDG MOZ MRT MWI SDN STP SYC ZMB ZWE) |
| `GET /api/authentic-tariffs/calculate/{pays}/{code}` | `authentic_tariff_service.py` (2 673 lignes), PostgreSQL d'abord si configuré, puis fichiers ETL | **en premier pour 38 pays**, et par le comparatif multi-pays |
| `GET /api/regulatory-engine/details` | `engine/output/` (gabarit du 1ᵉʳ mars 2026) | panneau réglementaire du calculateur : affiche des totaux NPF/ZLECAf **sans contrôle d'origine**, avec `\|\| 0` |
| `GET /api/dismantlement/…` | calendrier linéaire générique 5/10/13 ans | panneau « calendrier de démantèlement » |
| `POST /api/calculate-tariff` (1 138 lignes) et 10 autres (`enhanced_calculator`, `calculate/detailed`, `regional-calculator`, `postgres-tariffs/calculate`, `v2`, GraphQL…) | divers | **non** — mais toujours montées |

Deux d'entre elles servent des chiffres qui ne viennent d'aucune source :
**GraphQL `bulkTariffCalculation` renvoie un taux fixe de 5 % étiqueté
« AfCFTA preferential »** (`api/graphql/schema.py:118`), et
`regional-calculator` retombe sur la médiane d'une bande de taux
(`enhanced_calculator_v3.py:241`). Elles sont à retirer **en premier**.

**Pourquoi la bascule vers la route unique s'est arrêtée** — le commentaire de
`CalculatorTab.jsx:448-477` le dit, et c'est la clé d'O2 : l'interface
**n'envoie pas** à `POST /calcul` la devise du CIF, le taux de change ni la
**valeur FOB** (la SACU liquide sur le FOB : 41 % des positions sud-africaines
répondent `VALEUR_FOB_REQUISE`), ni les réponses du formulaire de remise
kényane. Ce n'est pas un problème de moteur : **ce sont quatre champs de
formulaire.** Une fois ces champs envoyés, `SOCLE_EN_PREMIER` peut couvrir les
52 pays servis, et l'ancien chemin peut être retiré.

**Les jeux de données lus à l'exécution :**

| Dossier | Contenu | Statut cible |
|---|---|---|
| `backend/data/crawled/*_tariffs.json` | 53 fichiers, 779 Mo — sortie du crawler | **source** du socle |
| `backend/socle/<ISO>.json` | non versionné, construit par `build_socle.py` | **seul lu par le calcul** |
| `backend/data/*_tariffs.json` | 40 fichiers ETL, 391 Mo, encore lus par l'ancien chemin | retirés du calcul |
| `backend/data/tariffs/` | 40 fichiers, 336 Mo — copie à l'octet près du précédent ; `routes/tariff_data.py:97-102` **écrit** un fichier à la demande quand il manque | supprimé |
| `backend/data/crawled_normalized/` | ~2 Go, construit au démarrage ou dans l'image | supprimé avec l'ancien chemin (O5-e) |
| `engine/output/` | gabarit de mars 2026, sans les fichiers chargés | supprimé |
| PostgreSQL | consulté en premier quand configuré ; contenu non reproductible depuis le dépôt | projection du socle, ou rien |

Morts à l'exécution, à retirer sans risque : 99 fichiers `*_progress_*` (61 Mo),
`tariff_engine/` (non importé), `data/archive/` et `backend/data/archive/`
(664 Mo).

**Taille de la chaîne de calcul** : les fichiers du relevé du 15/09 font
11 865 lignes (contre 11 191), et le nouveau chemin en ajoute ~2 380
(`routes/calcul.py`, `services/calcul.py`, `preference.py`, `socle.py`,
`unifiedCalculator.js`). **Environ 14 240 lignes pour une cible de 1 500.** Le
nouveau moteur s'est ajouté à l'ancien au lieu de le remplacer : c'est
exactement ce qu'O2 doit inverser.

### 3.2 La table « qui fait foi »

Une ligne par type d'information, un seul fichier, un seul lecteur autorisé.
Tout autre lecteur est supprimé.

| Information | Fait foi | Lu par |
|---|---|---|
| Tarif NPF, taxes, assiettes | `backend/socle/<ISO>.json` (construit par `scripts/build_socle.py`) | `services/calcul.py` |
| Assiettes, TVA de repli, devises | `backend/socle/assiettes_pays.json`, `tva_nationale.json`, `devises_pays.json` | `build_socle.py` |
| Application ZLECAf (pays et couples) | fiches `backend/data/legal_refs/zlecaf_application/` → `reports/ETAT_APPLICATION_BILATERAL.json` | `preference.py` |
| Barèmes préférentiels (offres UA) | `backend/data/official_preferential/*.json.gz` | `official_preferential_rates.py` |
| Accords autres que la ZLECAf | `backend/data/agreements/` (O4) | `preference.py` |
| PostgreSQL | **projection** du socle (L1b du plan unique), jamais une source | recherche seulement |

### 3.3 Les retraits

1. **Finir L2 → L4 de `PLAN_CALCULATEUR_UNIQUE.md`** : route unique, un appel
   dans l'interface, retrait du repli silencieux, retrait des anciennes routes
   et services de calcul. Critère inchangé : la chaîne de calcul **diminue**.
2. **Documents** : un seul `docs/README.md` « par où commencer » qui pointe
   vers **cinq** documents vivants (ce plan, la règle de preuve, le plan
   calculateur unique, la méthode du socle, le déploiement). Tous les autres
   plans, audits et états datés partent dans `docs/archive/` avec une ligne
   « remplacé par … ». Rien n'est supprimé, tout est rangé.
3. **Déploiement** : une seule cible documentée (décision D3 du propriétaire,
   § 8) ; les autres guides vont aux archives (voir O5).
4. **Reliquats** : la liste des fichiers et dossiers sans lecteur à
   l'exécution est publiée, puis retirée en un lot séparé, après accord.

### 3.4 Lots et critères — O2

| Lot | Livrable | Acceptation |
|---|---|---|
| O2-0 | retrait immédiat des deux routes qui inventent un taux (GraphQL `bulkTariffCalculation`, `regional-calculator`) | aucune route ne renvoie un taux qui ne vient pas d'un fichier tracé |
| O2-a | l'interface envoie devise, taux de change, valeur FOB et réponses de remise à `POST /calcul` | `SOCLE_EN_PREMIER` couvre les 52 pays servis ; les 23 cas du corpus figé passent sur la route unique |
| O2-b | retrait de `GET /authentic-tariffs/calculate`, `POST /calculate-tariff`, `regulatory-engine`, des `enhanced_calculator*` et du repli dans l'interface | une seule route de calcul ; la chaîne passe **sous** 11 191 lignes (niveau du 15/09), puis vers la cible de ~1 500 |
| O2-c | retrait de `backend/data/tariffs/`, des `*_tariffs.json` du calcul, de `engine/output/`, des reliquats morts | aucun lecteur d'exécution hors socle (test) ; plus d'écriture de fichier à la demande |
| O2-d | `docs/README.md` « par où commencer » ; archivage des plans remplacés | 5 documents vivants ; chaque document archivé dit par quoi il est remplacé |

---

## 4. O3 — Ce qui manque, pays par pays

### 4.1 Le livrable

Un script de lecture, sans réseau : `scripts/rapport_manques_pays.py` →
`reports/MANQUES_PAR_PAYS.md` (+ `.json`), régénéré en CI à chaque fusion.
Il **remplace** les rapports de carences épars (`reports/CARENCES_CALCULATEUR_*`,
`NATIONAL_TAX_COMPLETION_STATUS.md`, `KEN_DATA_GAPS.md`,
`docs/COLLECTE_DONNEES_MANQUANTES.md`), qui passent aux archives.

Une ligne par pays, colonnes fixes, toutes lues dans les fichiers qui font foi
(§ 3.2) :

| Colonne | Lue dans | Valeurs |
|---|---|---|
| Tarif | `MANIFESTE.json` | `national` / `moyenne SH6` / `vide` + nb de positions |
| Fraîcheur | `MANIFESTE.json` (`collecte`) | date ; **alerte au-delà de 6 mois** ou date absente |
| Liquidable | `MANIFESTE.json` | % de positions liquidables |
| TVA | socle / `tva_nationale.json` | `par ligne` / `taux standard de repli` / `absente` |
| Assiettes | `assiettes_pays.json` | `établie` / `absente` |
| Formalités, réglementation | socle | `par ligne` / `absentes` |
| ZLECAf — acte national | fiches | référence + date, ou `non trouvé` / `non recherché` |
| ZLECAf — liste des origines | fiches | nb d'origines, ou `manquante` |
| ZLECAf — barème ligne par ligne | `official_preferential/` | fichier + date, ou `manquant` |
| Ratification, offre UA | registre UA archivé, `afcfta_status_matrix` | oui / non |
| Autres accords (O4) | `agreements/` | GZALE, CER, bilatéraux : documentés ou non |
| **Prochaine pièce à obtenir** | fiche du pays | le document précis, son émetteur |
| **Priorité** | calculée | voir § 4.2 |

### 4.2 La priorité, en une règle

Priorité 1 : la pièce qui fait passer **un couple au verdict 1** (appliquée) ou
qui rend un pays `COMPLET`. Priorité 2 : la fraîcheur (tarifs collectés il y a
plus de six mois). Priorité 3 : le reste. Le volume d'échanges du couple sert à
départager à priorité égale.

### 4.3 Premier inventaire — au 1ᵉʳ octobre 2026

Voir l'**annexe A**. Il est produit à la main pour ce plan, à partir des mêmes
fichiers ; le script du § 4.1 le remplacera.

---

## 5. O4 — ZLECAf, GZALE, bilatéraux, communautés économiques : lequel est le plus avantageux ?

### 5.1 Ce qui existe

| Régime | Composition des membres | Taux au dépôt | Servi par le calcul |
|---|---|---|---|
| **Unions douanières** (SACU, EAC, CEMAC, UEMOA) | `services/regional_blocs.py` | règle : 0 % de droit de douane entre membres | **oui**, et prioritaire sur la ZLECAf |
| **ZLE régionales** (SADC, COMESA) | `regional_blocs.py` | colonnes SADC/COMESA de certains tarifs (SACU, AGO, MWI, SYC, MUS, ETH) | **simulées**, affichées, jamais appliquées, ordre alphabétique |
| **CEDEAO** (ZLE, ETLS) | `regional_blocs.py` | **aucune colonne** dans aucun tarif | non |
| **GZALE** (Grande zone arabe de libre-échange) | 7 pays (DZA, EGY, LBY, MAR, MRT, SDN, TUN) dans `north_africa_intelligence.py`, **sans source** ; la Mauritanie y figure sans justification | **Tunisie** : 0 % dominant pour l'Algérie (13 362 lignes), le Maroc (13 735) et l'Égypte (10 632) ; **Libye** : colonne `LIGUE_ARABE` (5 849 lignes) ; **Algérie** : mention en texte libre « -zale- exo d.d » | **Algérie seule**, côté Tunisie ; le reste est collecté puis **écarté** par `scripts/build_socle.py:248` |
| **Agadir** (EGY, MAR, TUN + Jordanie) | 2 listes en dur | aucun taux propre | non |
| **Bilatéraux africains** | — | en texte ou en note administrative : DZA–TUN, EGY–TUN, EGY–SDN, EGY–MAR (côté Égypte), TUN–MAR (côté Tunisie) ; **rien** pour MAR–MRT, TUN–LBY, EGY–LBY | Algérie → Tunisie en simulation seulement |
| **Règles d'origine** | — | **ZLECAf seulement** (`backend/data/zlecaf_rules_of_origin.json`) | — |

Deux faits commandent la conception :

1. **Il y a au moins six listes de membres** (`regional_blocs.py`,
   `country_codes.py`, `intelligence/analytics/regional_analytics.py`,
   `crawlers/all_countries_registry.py`, `north_africa_intelligence.py`,
   `uma_constants.py`) **et elles se contredisent** : le Burkina Faso, le Mali et
   le Niger sont encore dans la CEDEAO, les Seychelles sont dans le COMESA dans
   un fichier et pas dans l'autre, et `enhanced_calculator_v3.py:436` ajoute la
   GZALE à **tous** les pays, CEMAC comprise.
2. **Le moteur refuse aujourd'hui de classer les régimes**, faute de règles
   d'origine vérifiées (`preference.py:513-515`). C'est juste : un taux à 0 %
   ne sert à rien si la marchandise ne peut pas prouver son origine. Le
   comparatif doit donc porter **le montant et la condition d'origine
   ensemble**.

### 5.2 Exemples réels que le comparatif doit savoir traiter

Tirés des données du dépôt, sans calcul supplémentaire :

- **Tunisie ← Algérie, Maroc, Égypte** : le tarif tunisien ne leur accorde
  **pas** la ZLECAf (seules 8 origines y sont admises), mais leur accorde la
  GZALE à 0 % sur plus de 10 000 lignes. Pour ces trois flux, la GZALE n'est
  pas seulement le régime le plus avantageux : c'est **le seul** régime
  préférentiel ouvert.
- **Libye et Soudan** n'ont **pas ratifié** la ZLECAf (liste UA du 22/05/2026).
  Avec l'Égypte, la Tunisie, le Maroc et l'Algérie, seule la GZALE, ou le
  COMESA, ou un accord bilatéral peut jouer.
- **Égypte ← Maroc, Tunisie, Algérie** : la ZLECAf égyptienne ne couvre que la
  liste A, et la GZALE s'applique en principe à tout le tarif sauf
  exceptions. Laquelle des deux est la moins chère dépend de la ligne, et ne
  peut pas être tranchée sans les taux GZALE égyptiens, qui manquent.
- **Kenya ← Tanzanie** (même union douanière) : l'union douanière EAC à 0 %
  prime ; la ZLECAf est sans objet.

### 5.3 La cible — un tableau par couple

Pour un couple O → D et une ligne tarifaire, une ligne par régime :

| Régime | Statut | Droit de douane | Total liquidé | Écart avec le NPF | Règle d'origine | Justificatif |
|---|---|---|---|---|---|---|
| NPF | appliqué | … | … | — | aucune | — |
| ZLECAf | verdict 1 à 5 (§ 2.1) | … | … | … | Annexe 2, Appendice IV | certificat ZLECAf |
| GZALE | appliqué / documenté sans taux / non applicable | … | … | … | règles d'origine arabes | certificat GZALE |
| Union douanière ou CER | … | … | … | … | règle de la communauté | certificat de la communauté |
| Bilatéral O–D | … | … | … | … | règle de l'accord | certificat de l'accord |

Règles :

1. **Un régime = son propre verrou et sa propre colonne.** Jamais le taux d'un
   régime servi sous le nom d'un autre : ni la colonne COMESA comme taux
   ZLECAf, ni la colonne ZALE tunisienne comme taux ZLECAf.
2. **Un taux préférentiel n'est jamais servi au-dessus du NPF.** Les quelques
   valeurs ZALE tunisiennes à 63, 80 ou 89 % sur des lignes à NPF 0 % sont
   traitées comme sens non établi, et non comme taux.
3. **« Le plus avantageux »** = le total liquidé le plus bas **parmi les
   régimes au statut « appliqué »** (on compare le total, pas le seul droit de
   douane : le DAPS algérien ou la TPI marocaine changent le classement). Les
   autres régimes restent affichés en dessous, avec ce qui leur manque.
4. Le classement est toujours accompagné de la condition : « le moins coûteux,
   **si** la marchandise satisfait à la règle d'origine de ce régime ».

### 5.4 Les lots, dans l'ordre

| Lot | Livrable | Acceptation |
|---|---|---|
| **O4-a — Un registre des accords** | `backend/data/agreements/accords.json` : par accord, la nature (union douanière, ZLE, bilatéral), les parties avec leurs dates et leur **source primaire**, la règle de démantèlement, la référence de la règle d'origine, le justificatif. Il **remplace** les six listes de membres, et les calculateurs « étiquettes sans taux » (`enhanced_calculator_v3`, `regional_intelligence_service`, `routes/regional_calculator.py`, `routes/uma_regions.py`) sont retirés ou branchés sur lui | une seule liste de membres dans le dépôt ; composition GZALE établie sur source primaire (Ligue arabe, ou base des accords régionaux de l'OMC) ; Mauritanie tranchée ; CEDEAO à jour ; test : aucun autre fichier ne déclare de membres |
| **O4-b — « Accords ouverts pour ce couple »** | pour tout couple, la liste des accords auxquels les deux pays sont parties, **sans taux** | les 2 862 couples renseignés ; affiché sous la carte-verdict ZLECAf |
| **O4-c — Servir ce qui est déjà collecté** | colonnes ZALE tunisiennes pour MAR et EGY, `LIGUE_ARABE` libyenne, colonne COMESA éthiopienne (`D2R`), `COMESA_I/II` mauricien, colonnes SADC : chacune sous **son** régime | aucune colonne collectée n'est écartée sans motif écrit au manifeste ; plancher NPF testé |
| **O4-d — Collecter ce qui manque** | taux GZALE au Maroc (portail ADIL), en Égypte (portail des douanes), en Algérie (texte → colonne), au Soudan ; textes des accords bilatéraux (DZA–TUN, EGY–TUN, EGY–SDN, TUN–MAR, MAR–MRT, TUN–LBY) ; règles d'origine GZALE, Agadir, COMESA, SADC, CEDEAO, EAC | une fiche par accord et par pays, sur le modèle des fiches ZLECAf (acte, date, SHA-256, verbatim) |
| **O4-e — Le comparatif** | le tableau du § 5.3 dans les résultats, sous la carte-verdict, replié par défaut sauf quand un régime bat la ZLECAf | un test par cas du § 5.2 ; un régime sans règle d'origine connue n'est jamais classé premier |

O4-a et O4-b sont rapides et utiles tout de suite. O4-c ne demande aucune
collecte. O4-d est le gros du travail, il avance pays par pays comme les
fiches ZLECAf.

---

## 6. O5 — Une production qui se maintient seule

### 6.1 Constat

- **Deux constructions concurrentes.** Le `Dockerfile` vérifie les empreintes
  puis construit `crawled_normalized/` (2 Go, la couche de l'**ancien**
  chemin), mais **pas le socle** du nouveau. Le socle n'est construit qu'en CI
  (`ci.yml:101`) et par `sync_emergent.sh:181`. Selon la façon de déployer,
  `POST /calcul` répond `SocleIndisponible` ou fonctionne : la même version du
  code se comporte différemment selon l'hébergeur.
- **Six façons de lancer l'application** (Docker, Emergent, Replit, VS Code,
  `start.sh`, GitHub Pages), chacune avec son guide.
- **11 workflows GitHub**, dont 5 planifiés (données de marché, fret,
  production, veille ETH), sans tableau de bord commun de leur état.
- **La fraîcheur des tarifs n'est surveillée nulle part** : 22 pays ont une
  collecte de plus de 6 mois (février 2026), et 6 pays servis n'ont **aucune
  date** de collecte au manifeste (CPV, GMB, GNB, GNQ, LBR, SLE) — annexe A.

### 6.2 La cible

| Élément | Règle |
|---|---|
| **Une construction** | une seule commande, `make release` : vérifier les empreintes → `build_socle.py` → tests → image. Toute cible de déploiement l'appelle ; aucune ne construit autrement |
| **Une cible de déploiement documentée** | choisie par le propriétaire (§ 8) ; les autres guides passent aux archives |
| **Démarrage fail-closed** | le serveur refuse de démarrer si le socle manque ou si son empreinte ne correspond pas au manifeste ; plus de « certains pays seront indisponibles » silencieux |
| **`/api/health` dit la vérité sur les données** | version et empreinte du socle, date de construction, nombre de pays `COMPLET` / `PARTIEL` / `VIDE`, nombre de pays à collecte de plus de 6 mois |
| **Un rapport hebdomadaire** | un workflow planifié régénère `MANQUES_PAR_PAYS` (O3) et la matrice des verdicts (O1), et ouvre une PR s'ils ont changé ; une alerte si un crawl planifié échoue deux fois de suite |
| **Une procédure d'exploitation d'une page** | `docs/EXPLOITATION.md` : déployer, revenir en arrière, recharger un pays, lire `/api/health`, à qui s'adresser |

### 6.3 Lots et critères — O5

| Lot | Livrable | Acceptation |
|---|---|---|
| O5-a | `make release` + `Dockerfile` qui construit le socle | l'image démarre et `POST /calcul` répond sur 52 pays ; même résultat en local, en CI et en production |
| O5-b | démarrage fail-closed + `/api/health` enrichi | un socle altéré empêche le démarrage (test) ; `/api/health` expose les champs ci-dessus |
| O5-c | workflow hebdomadaire des rapports + alerte d'échec de crawl | une PR automatique quand un verdict ou un manque change |
| O5-d | `docs/EXPLOITATION.md`, une seule cible de déploiement | un nouveau venu déploie en suivant une seule page |
| O5-e | retrait de la couche `crawled_normalized/` | possible seulement après O2 (plus aucun lecteur) ; 2 Go en moins par image |

---

## 7. Calendrier et dépendances

```
Semaine 1      O2-0  retrait des deux routes qui inventent un taux (une journée)
               O1-a  verdict + tables ratification/offre + tests de cohérence
               O3    script du rapport des manques (en parallèle)
Semaine 2      O1-b/c  registre lu depuis les fiches, SYC, DZA, verdict dans l'API
               O5-a/b  une construction, démarrage fail-closed, health
Semaine 3      O1-d  carte-verdict et écran replié
               O2-a  les quatre champs manquants → les 52 pays sur la route unique
Semaine 4      O2-b/c/d  retrait de l'ancien chemin, des copies de données, rangement des documents
               O5-c/d  rapports planifiés, procédure d'exploitation
Semaine 5-6    O4-a/b/c  registre des accords, accords ouverts, colonnes déjà collectées
ensuite        O4-d/e  collecte GZALE et bilatéraux, comparatif — pays par pays
               O5-e  retrait de crawled_normalized/
```

Une PR par lot, relue avant fusion. Chaque PR indique, en tête, **ce qu'elle
retire** (lignes, fichiers, statuts, documents).

## 8. Décisions réservées au propriétaire

| # | Décision | Recommandation |
|---|---|---|
| D1 | Valider les cinq libellés du verdict et le cas « même union douanière » (§ 2.1) | les valider tels quels |
| D2 | Afficher le taux de l'offre UA « à titre indicatif » pour les verdicts 2 et 3 ? | oui, avec la mention « non applicable en l'état, à vérifier en douane » |
| D3 | Choisir **la** cible de déploiement | celle qui sert la production aujourd'hui ; les autres passent aux archives |
| D4 | Autoriser le classement « le plus avantageux » (§ 5.3), aujourd'hui refusé par le moteur faute de règles d'origine | oui, mais seulement entre régimes « appliqués » et toujours avec la règle d'origine affichée |
| D5 | « Plus avantageux » au total liquidé ou au seul droit de douane ? | au total liquidé |
| D6 | Archiver les plans et audits remplacés (§ 3.3) | oui, dans `docs/archive/`, sans suppression |
| D7 | Composition de la GZALE : la Mauritanie y est-elle ? | ne rien servir avant la source primaire (O4-a) |

## 9. Ce que ce plan ne fait pas

- Il n'assouplit pas la règle de preuve ZLECAf : un verdict 1 exige toujours
  l'acte, la liste des origines et le barème.
- Il ne fabrique aucun taux : un régime sans taux sourcé est affiché « documenté,
  non chiffré », jamais estimé.
- Il ne touche pas aux modules hors calculateur (logistique, finance,
  opportunités), sauf pour retirer ce qui en double les listes de membres.

---

## Annexe A — Ce qui manque, pays par pays (au 1ᵉʳ octobre 2026)

Lu dans `backend/socle/MANIFESTE.json` (construit le 28/09/2026),
`tva_nationale.json`, `assiettes_pays.json`, le fichier d'état ZLECAf et la
liste de l'UA du 22/05/2026. Produit à la main pour ce plan ; le script d'O3 le
remplacera et y ajoutera la « prochaine pièce à obtenir » de chaque pays.

⚠ = collecte de plus de 6 mois. « Positions liquidables » = part des positions
dont **tous** les droits ont un taux et une assiette.

| Pays | Tarif (socle) · positions | Collecte | Positions liquidables | TVA | Assiette | Ratif. | Offre UA | ZLECAf (fiche) |
|---|---|---|---:|---|---|---|---|---|
| AGO | partiel · 5959 | 2026-09-19 | 100 % | taux standard (repli) | établie | oui | oui | non recherché |
| BDI | partiel · 5935 | 2026-02-18 ⚠ | 99 % | par ligne | établie | oui | oui | offre seule (recherche faite) |
| BEN | complet · 6129 | 2026-02-19 ⚠ | 100 % | par ligne | établie | non | oui | non recherché |
| BFA | complet · 6129 | 2026-02-19 ⚠ | 100 % | par ligne | établie | oui | oui | non recherché |
| BWA | partiel · 8589 | 2026-08-29 | 99 % | **absente** | établie | oui | oui | non recherché |
| CAF | complet · 5239 | 2026-02-19 ⚠ | 100 % | par ligne | établie | oui | oui | non recherché |
| CIV | partiel · 6129 | 2026-02-19 ⚠ | 98 % | par ligne | établie | oui | oui | acte, liste des origines manquante |
| CMR | complet · 5239 | 2026-02-19 ⚠ | 100 % | par ligne | établie | oui | oui | offre seule (recherche faite) |
| COD | partiel · 5935 | 2026-02-18 ⚠ | 99 % | par ligne | **absente** | oui | oui | non recherché |
| COG | complet · 5239 | 2026-02-19 ⚠ | 100 % | par ligne | établie | oui | oui | non recherché |
| COM | complet · 5388 | 2026-07-05 | 100 % | par ligne | établie | oui | oui | non recherché |
| CPV | complet · 6129 | **absente** | 100 % | par ligne | **absente** | oui | oui | non recherché |
| DJI | **vide** | **absente** | — | taux standard (repli) | **absente** | oui | **aucune** | non recherché |
| DZA | partiel · 17226 | 2026-08-29 | 99 % | par ligne | établie | oui | oui | preuves réunies, branchement à faire |
| EGY | partiel · 8818 | 2026-08-29 | 94 % | par ligne | établie | oui | oui | appliquée |
| ERI | **vide** | **absente** | — | **absente** | **absente** | non | **aucune** | non recherché |
| ETH | partiel · 6296 | 2026-07-05 | 0 % | par ligne | établie | oui | oui | acte, liste des origines manquante |
| GAB | complet · 5239 | 2026-02-19 ⚠ | 100 % | par ligne | établie | oui | oui | non recherché |
| GHA | complet · 11516 | 2026-06-16 | 100 % | par ligne | établie | oui | oui | acte, liste des origines manquante |
| GIN | complet · 6129 | 2026-02-19 ⚠ | 100 % | par ligne | établie | oui | oui | non recherché |
| GMB | complet · 6129 | **absente** | 100 % | par ligne | établie | oui | oui | non recherché |
| GNB | complet · 6129 | **absente** | 100 % | par ligne | établie | oui | oui | non recherché |
| GNQ | complet · 5239 | **absente** | 100 % | par ligne | établie | oui | oui | non recherché |
| KEN | partiel · 5935 | 2026-02-18 ⚠ | 99 % | par ligne | établie | oui | oui | appliquée |
| LBR | complet · 6129 | **absente** | 100 % | par ligne | établie | oui | oui | non recherché |
| LBY | partiel · 5920 | 2026-09-18 | 0 % | **absente** | **absente** | non | **aucune** | non recherché |
| LSO | partiel · 8589 | 2026-08-29 | 99 % | **absente** | établie | oui | oui | non recherché |
| MAR | partiel · 13114 | 2026-02-11 ⚠ | 99 % | par ligne | établie | oui | oui | appliquée |
| MDG | complet · 6544 | 2026-09-21 | 100 % | par ligne | établie | oui | oui | non recherché |
| MLI | complet · 6129 | 2026-02-19 ⚠ | 100 % | par ligne | établie | oui | oui | non recherché |
| MOZ | partiel · 5822 | 2026-09-18 | 98 % | par ligne | établie | oui | oui | non recherché |
| MRT | complet · 6129 | 2026-09-18 | 100 % | par ligne | établie | oui | oui | non recherché |
| MUS | partiel · 6941 | 2026-09-18 | 90 % | par ligne | établie | oui | oui | non recherché |
| MWI | partiel · 7364 | 2026-09-19 | 0 % | par ligne | établie | oui | oui | non recherché |
| NAM | partiel · 8589 | 2026-08-29 | 99 % | **absente** | établie | oui | oui | non recherché |
| NER | complet · 6129 | 2026-02-19 ⚠ | 100 % | par ligne | établie | oui | oui | non recherché |
| NGA | partiel · 6350 | 2026-02-17 ⚠ | 94 % | par ligne | établie | oui | oui | acte, liste des origines manquante |
| RWA | partiel · 5935 | 2026-02-18 ⚠ | 99 % | par ligne | établie | oui | oui | appliquée |
| SDN | partiel · 5388 | 2026-07-05 | 0 % | par ligne | **absente** | non | **aucune** | non recherché |
| SEN | complet · 6129 | 2026-02-19 ⚠ | 100 % | par ligne | établie | oui | oui | non recherché |
| SLE | complet · 6129 | **absente** | 100 % | par ligne | établie | oui | oui | non recherché |
| SOM | partiel · 11545 | 2026-06-16 | 100 % | **absente** | établie | non | **aucune** | non recherché |
| SSD | partiel · 5935 | 2026-02-18 ⚠ | 99 % | par ligne | **absente** | non | oui | non recherché |
| STP | complet · 5388 | 2026-07-05 | 100 % | par ligne | établie | oui | **aucune** | non recherché |
| SWZ | partiel · 8589 | 2026-08-29 | 99 % | **absente** | établie | oui | oui | non recherché |
| SYC | partiel · 6019 | 2026-09-19 | 100 % | **absente** | établie | oui | oui | appliquée |
| TCD | complet · 5239 | 2026-02-19 ⚠ | 100 % | par ligne | établie | oui | oui | non recherché |
| TGO | complet · 6129 | 2026-02-19 ⚠ | 100 % | par ligne | établie | oui | oui | non recherché |
| TUN | partiel · 17542 | 2026-08-30 | 100 % | par ligne | établie | oui | oui | acte vérifié, barème manquant |
| TZA | partiel · 5935 | 2026-02-18 ⚠ | 99 % | par ligne | établie | oui | oui | appliquée |
| UGA | partiel · 5935 | 2026-02-18 ⚠ | 99 % | par ligne | établie | oui | oui | appliquée |
| ZAF | partiel · 8589 | 2026-08-29 | 99 % | taux standard (repli) | établie | oui | oui | appliquée |
| ZMB | partiel · 6753 | 2026-09-18 | 96 % | par ligne | établie | oui | oui | acte, liste des origines manquante |
| ZWE | partiel · 6637 | 2026-09-18 | 97 % | **absente** | établie | oui | oui | non appliquée (indices secondaires) |

### Ce que le tableau dit, en six lignes

1. **Données vides** : Djibouti, Érythrée — aucun tarif.
2. **Calcul impossible sur la quasi-totalité des lignes** : Éthiopie, Libye,
   Malawi, Soudan (0 % de positions entièrement liquidables : taux ou
   assiettes manquants).
3. **TVA absente** : BWA, ERI, LBY, LSO, NAM, SOM, SWZ, SYC, ZWE ; TVA au seul
   taux standard de repli : AGO, DJI, ZAF.
4. **Assiette absente** : COD, CPV, DJI, ERI, LBY, SDN, SSD.
5. **Tarifs à rafraîchir** : 22 pays collectés en février 2026, dont le Maroc,
   le Kenya, le Nigeria, la Côte d'Ivoire et toute la zone UEMOA/CEMAC ; 6 pays
   sans date de collecte.
6. **ZLECAf** : 36 pays jamais recherchés ; 5 pays avec un acte mais sans
   liste d'origines (CIV, ETH, GHA, NGA, ZMB) ; Tunisie sans barème ; Algérie
   et Seychelles prouvées mais pas branchées sur la route unique.

**Formalités et réglementation** : le socle n'en porte pour aucun pays. Dans
les fichiers crawlés, seuls l'Algérie et le Maroc ont des formalités par ligne,
et la Tunisie sa réglementation : 51 pays n'ont ni l'un ni l'autre. C'est
pourquoi la colonne n'est pas répétée dans le tableau.
