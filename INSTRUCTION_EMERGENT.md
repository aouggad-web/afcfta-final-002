# Instruction de reprise — Emergent

> Document de passation destiné à l'agent Emergent qui reprend le dépôt.
> Référence : `main` au commit `8fab55a` (fusion de la PR #478, 19/09/2026).
> Le document d'exploitation qui l'accompagne est `ETAT_APP_POUR_EMERGENT.md`.

---

## 0. La consigne qui prime sur toutes les autres

**N'ÉCRIS AUCUN TEST.** Ni test unitaire, ni test d'intégration, ni fichier
`test_*.py`, ni `*.test.js`, ni scénario de recette. N'en ajoute pas, n'en
complète pas, n'en « répare » pas un que tu jugerais insuffisant.

La suite existante (3 452 tests collectés au 21/09/2026) reste en place et
doit continuer à passer :
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

## 5. Comment on travaille — six règles

Elles ne sont pas une théorie : elles décrivent ce qui a produit, en une
journée, la récupération de 296 droits de douane algériens qu'une chaîne
automatique avait perdus pendant des mois.

**1. Un défaut, une PR, un jour.** Pas de lots. Un défaut nommé, une branche,
une fusion dans la journée. Ce qui ne tient pas dans une journée n'est pas un
défaut mais un chantier : il se traite à part, avec une décision du
propriétaire.

**2. Mesurer, jamais affirmer.** Toute affirmation porte son chiffre et la
commande qui l'a produit. « Le Maroc perd ses zéros » ne vaut rien ; « 4 droits
à 0 % sur 12 972, plancher à 2,5 % sur 51 % des lignes » se vérifie — et se
contredit. **Le message de commit EST le dossier de preuves** : le
raisonnement, les chiffres, et ce qui n'est PAS établi, écrits là où ils
survivront au projet.

**3. Tout défaut corrigé laisse un test — et son contrôle négatif.**

> **À qui cette règle s'adresse.** Elle vaut pour qui corrige la donnée ou le
> moteur dans ce dépôt. Elle ne lève PAS la consigne du §0, qui interdit à
> l'agent Emergent d'écrire ou de modifier des tests : cet agent travaille sur
> le déploiement et l'interface, il exécute la suite sans l'étendre. Les deux
> consignes ne se contredisent pas, elles s'adressent à deux rôles.
 Le test
tient deux choses : ce qui a été corrigé, et **ce qu'il ne faut pas
« finir »**. Exemple : les 296 droits algériens récupérés, ET les 3 positions
du chapitre « Effets personnels » qu'on ne comble pas. Le second compte plus
que le premier — sans lui, le prochain qui passe termine le travail et invente
trois franchises.

**4. Ce qui se décide seul, ce qui remonte.**

| Se décide seul | Remonte au propriétaire |
|---|---|
| Un correctif dont la preuve tient dans la PR | Une règle fiscale à interpréter |
| Un test déplacé parce que son exemple est devenu faux | Un choix visible par le client |
| Le refus de combler une lacune | Ce qui coûte de l'argent ou du temps récurrent |

**5. La file d'attente est ordonnée par gravité client** — voir le registre au
§6. Un G1 passe devant tout.

**6. Une seule cérémonie, et seulement avant une démonstration client :** la
grille de recette passée sur trois positions réelles de trois pays. Vingt
minutes. C'est le moment où le coût d'une erreur est maximal.

### Ce qui remplace les jalons de validation

Deux automatismes, **et un contrôle humain qui n'est pas automatisable.**

Les deux automatismes :

- **la CI** dit si le dépôt est sain ;
- **les tests ciblés avant chaque poussée, la suite complète avant chaque
  fusion.** Ne pas inverser : une poussée faite avant la fin de la suite a déjà
  coûté cinq échecs rattrapés par l'intégration.

Le contrôle humain, **distinct des deux et non couvert par eux** :

- **le propriétaire, sur un pays qu'il connaît.** Une fiche de portail produite
  à la main a trouvé ce que trois mois de chaîne automatique n'avaient pas vu.
  Ce n'est pas un contrôle qualité, c'est de l'expertise métier : aucun
  processus ne la remplace, et une méthode qui la met en bout de chaîne comme
  simple approbation la gaspille. Une CI verte ne vaut pas ce contrôle et ne
  dispense pas de le demander.

### Ce qu'on ne fait pas

Pas de programme en dix lots, pas de jalons numérotés, pas de dossier de
preuves annexe, pas une PR par pays sur 54 pays. Un tel appareil gouverne un
sous-traitant qu'on ne voit pas ; il coûte plus que le code qu'il surveille.

---

## 6. Le registre des défauts — gradué par ce qu'il en coûte au client

Ne « répare » aucun de ces points en inventant la donnée manquante.

La gravité se lit sur **ce que le produit dit à l'opérateur**, pas sur la
difficulté technique. Elle rend la priorité automatique, au lieu de la faire
débattre :

| | | Délai |
|---|---|---|
| **G1** | Le produit **affirme quelque chose de faux** qui engage l'opérateur — un montant, une obligation | immédiat |
| **G2** | Le produit **cache quelque chose de vrai** — une préférence acquise, un droit récupérable | dans la semaine |
| **G3** | Le produit est juste mais **lourd ou incohérent** — code mort, chemins concurrents, dépôt alourdi | au fil de l'eau |
| **G4** | Ce qu'on **ne sait pas encore** — lacune déclarée, en attente d'arbitrage | décision du propriétaire |

Un G1 passe devant tout le reste. Un G4 ne se traite jamais en devinant : il
attend une source ou une décision.

### G1 — le produit affirme du faux

**Aucun G1 ouvert à ce jour.** L'entrée ci-dessous est conservée réglée, parce
que le garde qu'elle a laissé derrière elle doit être compris avant qu'on y
touche.

- **Formalités : une liste vide se lisait « aucune obligation » — RÉGLÉ le
  21/09/2026** (PR #492). `get_administrative_formalities()` rendait `[]` aussi
  bien quand la position n'a aucune formalité documentée que quand elle est
  **introuvable**, et l'interface, devant cette liste vide, ne disait rien. Un
  opérateur à qui l'on n'affiche rien sur une position qu'on n'a pas trouvée
  peut importer sans licence : pas un montant faux, une infraction.

  `formalites_et_statut()` nomme désormais quatre états, et la réserve voyage
  dans la réponse de l'API, pas seulement dans l'écran.

  **Le garde à ne pas contourner.** Aucun de ces états ne peut signifier
  « aucune obligation » : le dépôt ne collecte nulle part une attestation
  d'absence d'obligation, il collecte des formalités, ou rien. Un test tombe si
  quelqu'un ajoute `AUCUNE_OBLIGATION`, `DISPENSE` ou `EXEMPT`. Sans lui, le
  prochain qui passe « termine le travail » et transforme 315 185 silences en
  autant de dispenses — la faute réparée ici, retournée.

  Une seule exception existe, et elle est verrouillée : l'Algérie, dont la
  source publie ses formalités de façon exhaustive — établi par échantillon de
  80 positions au portail, archivé dans
  `data/dza/echantillon_formalites_portail.json`. Là, et là seulement, une
  liste vide est un CONSTAT (« aucune formalité particulière »). Un test exige
  que toute entrée de `SOURCES_EXHAUSTIVES_FORMALITES` porte sa preuve
  circonstanciée : **étendre ce constat par analogie transformerait 297 794
  lacunes en autant de déclarations d'absence de formalité.**

  Ce qui reste ouvert est autre chose, et relève du G2 : 46 pays sur 54 n'ont
  AUCUNE formalité collectée, nulle part. Ce lot n'a pas comblé cette lacune,
  il a fait que le produit cesse de la présenter comme une dispense.

### G2 — le produit cache du vrai

- **394 taxes dont le taux ne se liquide pas — Égypte et les sept du TEC.**
  Mesuré le 21/09/2026 ; constat complet dans
  `reports/TAUX_INDISPONIBLES_EGY_EAC_2026-09-21.md`. Deux familles sans
  rapport l'une avec l'autre :

  **Égypte, 58 taxes sur 40 positions** — des droits spécifiques que le
  collecteur a fidèlement recopiés sans les convertir : 9 £E/kg net sur les
  tabacs, 0,48 £E/litre sur le pétrole, 15 £E/litre sur l'alcool, 0,1 £E par
  vingt cigarettes. La mention est intacte dans `raw`, en arabe ; c'est la
  structuration en `{montant, unité, devise}` qui manque, et le moteur sait
  déjà liquider cette forme.

  **LE PIÈGE, à connaître avant d'y toucher : 18 des 58 ne sont pas des
  taxes.** Le suffixe `_2` (`VAT_2`, `ضريبة الجدول_2`) marque le **plancher**
  de la taxe qui le précède — « بحد ادنى », « avec un minimum de ». La
  correspondance est exacte, 18 sur 18, vérifiable dans le crawl. Les
  structurer comme des taxes séparées créerait dix-huit lignes fantômes et
  **doublerait** le montant, avec l'air d'être plus complet. Il y a donc 40
  droits à structurer et 18 planchers à rattacher : deux travaux, pas un.

  **Sept pays du TEC — Kenya, Tanzanie, Ouganda, Rwanda, Burundi, RD Congo,
  Soudan du Sud — 48 taxes chacun, 336 en tout.** Produits sensibles du tarif
  extérieur commun (laitiers, céréales, minoterie, sucres, coton, fibres
  synthétiques, vêtements), dont le taux relève du barème national de chaque
  pays. **Cette lacune-là est correctement déclarée** : le collecteur écrit
  `note: "Rate determined by national schedule"` et laisse `null` au lieu de
  deviner. Le travail est de collecter sept barèmes nationaux, pas de réparer
  un parseur.

  Ce n'est pas un G1 : les deux chemins que l'application utilise refusent
  correctement de calculer — `/calcul` rend `PARTIEL` avec
  `TAUX_INDISPONIBLE`, et `/authentic-tariffs/calculate` rend
  `CALCULATION_UNAVAILABLE` en nommant les droits spécifiques. Seul
  `enhanced_calculator_service` ramenait le taux absent à 0 %, sur trois
  points d'API que le frontend n'appelle pas ; corrigé par la PR #497.
- **Un taux réduit réel s'affiche vide.** `RegulatoryDetailsPanel.jsx` lit
  `adv.reduced_rate_pct` quand `postgres_tariff_service.py` renvoie
  `reduced_rate` : la valeur existe, elle n'atteint jamais l'écran. Un seul
  nom de champ à aligner.
- **Éthiopie : 1 368 droits perdus à la collecte.** Le collecteur a été corrigé
  le 18/09/2026 ; la collecte, jamais refaite. Le portail `customs.erca.gov.et`
  est injoignable, une veille le sonde et collectera dès son retour. Aucun code
  à écrire.
- **Grammaire FOB et devise du moteur.** `buildCalculRequestBody` n'envoie ni
  `devise_cif`, ni `taux_de_change`, ni `valeur_fob`. La valeur en douane de la
  SACU est la valeur FOB, jamais déduite du CIF (Act 91 of 1964, s.65(1)) :
  mesuré sur les 1 500 premières positions sud-africaines, **616 — 41 % —**
  répondent `VALEUR_FOB_REQUISE`. C'est ce qui interdit d'étendre
  `SOCLE_EN_PREMIER` au-delà de la Tunisie et de Maurice. Chantier de
  conception, pas correction.
- **Remises kényanes absentes de `/calcul`.** `remission_eligibility` et ses
  cinq champs d'autorisation n'existent que sur le chemin historique.

### G3 — juste, mais lourd

- **`backend/data/crawled` versionné : 4,7 Go.** Coût mesuré : 1 min 20 de
  `checkout` par job, quatre jobs par exécution d'intégration. Et un mur à
  100 Mo par fichier, que les Seychelles approchent à 75 Mo. C'est la décision
  qui débloque l'archive des sources originales.
- **Chemin historique** `/authentic-tariffs/calculate`, qui double `/calcul`.
  Sa dépose est la correction de fond, non faite.
- **`build_regulatory_blocks()`** ne reçoit pas le code SH : le bloc commun ne
  peut donc pas décider seul du périmètre produit.
- **Le repli sur 503 du socle** ne distingue pas « socle absent » de « socle
  périmé ou corrompu ». Le second ne devrait pas se replier en silence.
- **`verify=False` dans onze collecteurs — RÉGLÉ le 21/09/2026** (PR #488,
  fusionnée). Les onze fichiers et leurs 18 occurrences sont traités ; il ne
  reste dans le code que des commentaires qui rappellent la règle. L'entrée
  est conservée parce que la règle, elle, reste valable : **si la chaîne d'un
  portail se révèle incomplète en production, la réponse est de fournir
  l'intermédiaire manquant, jamais de redésactiver la vérification.**

  Ce qui n'est PAS établi, et qui se constatera seulement en production : le
  réseau de cet environnement resigne le TLS (« Egress Gateway SDS Issuing
  CA »), si bien que les certificats observés y sont ceux de la passerelle et
  jamais ceux de l'origine. Ce qui est établi, c'est que les clients n'ont pas
  besoin de `verify=False` pour fonctionner. Deux portails — `douane.gov.tn`,
  `zra.org.zm` — échouaient déjà à travers la passerelle : si leur collecte
  s'arrête, **c'est le comportement voulu**, et elle se répare par
  l'intermédiaire, pas par un retour en arrière.

  Un piège rencontré, à connaître avant de toucher à un collecteur : le
  contournement DNS mozambicain vise une IP en posant l'en-tête `Host`. La
  vérification de nom porte sur l'hôte de l'**URL**, pas sur cet en-tête — le
  contournement était donc mort dès la vérification rétablie, et le disait
  seulement en journal. Il se répare par `extensions={"sni_hostname": ...}`,
  qui fixe le `server_hostname` de la poignée de main.

### G4 — en attente d'arbitrage ou de source

- **TROIS pays servent la TOTALITÉ de leur droit de douane depuis une moyenne
  statistique SH6** : Comores, São Tomé, Soudan. Tous de la forme
  `20.0 % (MFN, SimpleAverage, 2021)`, issus de WITS / UNCTAD-TRAINS. Une
  moyenne des lignes nationales n'est le droit d'aucune marchandise, et un SH6
  n'est pas la position qu'un déclarant saisit.

  **Madagascar est SORTI de cette liste le 21/09/2026** (PR #496) : 6 544
  positions nationales à 8 chiffres lues sur le Tarif des douanes 2026, avec
  ses deux assiettes établies sur texte primaire — DD = CIF (Code des douanes
  art. 23 §1 et §4 c) et TVA = CIF+TOUS_SAUF_TVA (CGI art. 06.01.11). Son état
  passe d'`INDICATIF` à `COMPLET`. **C'est la preuve que le contrat de collecte
  fonctionne**, et le modèle à suivre pour les trois autres.

  Le produit ne cache pas ce qui reste : un total dont une ligne vient d'une
  moyenne se déclare **`INDICATIF`**, jamais `COMPLET` (PR #494). Le montant
  reste servi, avec sa source ; c'est le mot « complet » qui était faux. Ne
  supprime pas cet état pour « faire propre ».

  Ce qu'il faut pour sortir les trois derniers est écrit :
  `docs/CONTRAT_COLLECTE_COM_MDG_SDN_STP.md` (PR #493) — forme du fichier,
  cinq refus, chaîne d'ingestion. **Le point qui décide de tout y est
  l'assiette**, pas les taux : celle des Comores est établie sur texte
  primaire, celle de São Tomé ne l'est que pour l'IVA, et **le Soudan n'a
  aucune entrée** dans `assiettes_pays.json`. Pour le Soudan, collecter les
  taux sans établir l'assiette ne produirait aucun montant liquidable.

  Sur la collecte elle-même : `dre.gov.st` est refusé par le proxy réseau
  (CONNECT 502) pour São Tomé, aucune URL citable n'a été trouvée pour les
  Comores, et le livre tarifaire officiel soudanais répond 404 — preuves
  négatives consignées dans
  `reports/COLLECTE_TARIFS_NATIONAUX_2026-09-21.md`.
- **Colonne ZLECAf tunisienne** : quatre valeurs seulement (0, 40, 80, 87,5) et
  69,6 % d'entre elles dépassent le droit NPF de leur propre position. Deux
  captures du portail confirment que notre collecte est fidèle. Servie, elle
  ferait payer 40 % de la valeur CIF sur 20 149 lignes en franchise. Refusée,
  et le refus est mesuré par un test sur la source elle-même.
- **Règle égyptienne** ر6790 / ر6791 : non tranchée.
- **Assiette IAT/EXC nigériane** : non établie (`etabli: false`). Les 12 700
  droits nigérians non liquidables le restent. Ne leur pose pas `CIF` de mémoire.
- **TVA somalienne** : non collectée, nommée `NON_TRACEE_A_LA_SOURCE`.
- **Résidu OCR angolais** : 8 codes sur 5 959 (0,13 %) portent une sous-position
  qui n'existe dans aucune autre nomenclature. Mesuré, déclaré dans le crawl
  (`residu_connu`) et dans `data/angola/legal_sources.json`. Ne les corrige pas
  d'après une nomenclature tierce : elle écarterait aussi des sous-positions
  proprement angolaises (2903.39 porte seize extensions nationales que personne
  d'autre ne publie).
- **Sort de `engine/`** : instantané figé au 01/03/2026, encore lu par
  `/regulatory-engine/details`.
- **Nomenclatures import et export** : une opération peut exiger DEUX codes
  nationaux différents — celui du pays de destination à l'import, celui du pays
  d'exportation à l'export. Aucune correspondance ne se déduit du préfixe SH6.
  Non traité.

---

## 7. Déploiement

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

## 8. Conventions de code

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

## 9. Résumé en six lignes

1. **Aucun test écrit** par l'agent Emergent. Tu peux exécuter la suite, pas
   l'étendre. (Qui corrige la donnée ou le moteur, lui, laisse un test : §5.)
2. Aucune valeur fiscale fabriquée : une lacune se nomme, elle ne se comble pas.
3. Un pays à la fois ; ne généralise jamais une règle nationale.
4. Le socle se reconstruit, il ne s'édite pas ; un socle périmé doit rester inerte.
5. Tout taux ajouté cite son texte officiel, article par article, avec l'extrait
   archivé et son empreinte.
6. Un défaut, une PR, un jour — et la priorité se lit au registre du §6 : un
   **G1**, où le produit affirme du faux, passe devant tout le reste.
