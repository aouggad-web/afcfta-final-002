# Plan technique — Fret maritime vraquier (bulk carrier)

**Dépôt :** `aouggad-web/afcfta-final-002`
**Date :** 13 juillet 2026
**Statut :** plan de cadrage, à valider avant tout développement
**Prérequis :** correctif « réalisme du fret aérien » fusionné (PR #244) — le classifieur `classify_bulk_commodity()` et le drapeau `is_bulk_commodity` existent déjà.

---

## 1. Objet et problème à résoudre

Depuis la PR #244, les marchandises en vrac (ciment, minerai de fer, céréales, charbon, engrais, sucre brut, pétrole brut) sont correctement exclues du fret aérien et basculent sur le type de cargaison terrestre `bulk`. Mais **l'option maritime utilise toujours le tarif conteneurisé comme repère**, avec une note honnête (`bulk_cargo_note`) précisant que le coût réel d'un affrètement en vrac diffère.

Ce plan décrit comment remplacer ce repère par un **vrai modèle de fret vraquier en USD/tonne**, cohérent avec la discipline du dépôt : sources publiées, drapeau `is_modeled`, aucun chiffre fabriqué sans qualification.

### Réalité métier à respecter

Le vrac ne se résume pas à « gros navire » :

- **Un petit tonnage de vrac voyage réellement en conteneur** (riz ensaché, ciment en sacs, big bags). En dessous d'un seuil, le tarif conteneurisé n'est pas un pis-aller, c'est le mode réel.
- **L'affrètement vraquier n'est réaliste qu'à partir de plusieurs milliers de tonnes** (taille de lot minimale d'une cale ou d'un navire).
- **Le vrac liquide (pétrole brut, SH 2709) relève des tankers**, un marché entièrement différent du vrac sec — à traiter séparément ou à exclure explicitement.
- **Tous les ports africains n'acceptent pas tous les navires** : tirant d'eau et équipements (silos à grains, terminaux minéraliers) limitent la classe de navire utilisable.

---

## 2. Architecture existante sur laquelle s'appuyer

| Brique existante | Réutilisation prévue |
|---|---|
| `backend/logistics_fees_data.py` — 55 ports avec lat/lon/côte, `_sea_distance_nm()` (routage par points de passage : Gibraltar, Suez, Bab-el-Mandeb, Cap), routes benchmark publiées + modèle distance-coût `is_modeled` | Même registre de ports, même calcul de distance, même dualité benchmark/modèle pour le vrac |
| `backend/services/shipment_estimator.py` — `classify_bulk_commodity()` (catégories `bulk_mineral` / `bulk_agri`), estimation de poids depuis la valeur FOB | Point d'entrée de la classification ; à enrichir avec la classe de navire et les seuils de bascule |
| `backend/services/multimodal_freight_service.py` — `compare_multimodal()`, `_sea_options()`, `is_bulk_commodity`/`bulk_label`/`bulk_cargo_note` | Nouveau générateur `_bulk_sea_options()` branché quand vrac + tonnage ≥ seuil |
| `backend/logistics_land_fees_data.py` — `CARGO_FACTORS` avec type `bulk` (facteur 0.90) | Jambe terrestre déjà correcte, rien à changer |
| Workflow `update_market_prices` + `data/json/cours_mondiaux.json` (cours rafraîchis avec repli statique daté) | Même patron pour rafraîchir les indices de fret vraquier |

---

## 3. Modèle cible

### 3.1 Segmentation des navires (vrac sec)

| Classe | Port en lourd (dwt) | Marchandises types | Contrainte portuaire |
|---|---:|---|---|
| Handysize | 10 000 – 39 999 t | ciment/clinker, engrais, sucre, sel, soufre, gypse, tourteaux, ferraille, bois, aciers semi-finis, petits lots céréaliers | accepté presque partout |
| Supramax/Ultramax | 40 000 – 64 999 t | céréales, charbon, engrais, concentrés de minerais, phosphates, cacao méga-lot | tirant d'eau ≥ ~12 m |
| Panamax | 65 000 – 99 999 t | céréales, charbon, minerai, bauxite | tirant d'eau ≥ ~13,5 m |
| Capesize | ≥ 100 000 t | minerai de fer, charbon, bauxite | rares terminaux africains dédiés (ex. Saldanha, Nouadhibou minéralier) |

La liste complète des produits couverts, par code SH et par catégorie logistique, figure en **Annexe A** — elle constitue la table de référence unique (`SH → catégorie vrac → classes de navires admissibles`) que le Lot A implémentera dans `classify_bulk_commodity()`.

### 3.2 Bascule par taille de lot (par expédition)

| Tonnage du lot | Mode maritime retenu | Affichage |
|---|---|---|
| < 2 000 t | Conteneur (marchandise ensachée/big bags) | tarif conteneurisé actuel, avec note « vrac ensaché en conteneur — pratique réelle pour ce tonnage » |
| 2 000 – 10 000 t | Vraquier handysize (lot partiel ou complet) | USD/t vraquier |
| > 10 000 t | Classe de navire choisie selon tonnage + contraintes du port | USD/t vraquier |

Les deux seuils sont des **paramètres nommés à valider** (`BULK_CHARTER_MIN_TONNES`, `BULK_FULL_VESSEL_TONNES`) — valeurs ci-dessus proposées à dire d'expert, ajustables sans toucher au code appelant. Les produits **bi-modes** (riz, cacao, arachides, farines…) portent un seuil propre, défini ligne par ligne en Annexe A (A.5), qui prime sur le seuil global.

### 3.3 Formule de coût (USD/tonne)

```
Coût total vrac = fret océanique (USD/t)
                + frais de chargement au port d'origine (USD/t)
                + frais de déchargement au port de destination (USD/t)
```

- **Fret océanique** : `USD/t = f(distance_nm, classe navire)` — modèle distance-coût calibré sur des routes benchmark publiées (même approche que `_model_route()` pour le conteneur), borné par classe de navire. Chaque route benchmark porte sa source et sa période ; toute route générée par le modèle porte `is_modeled: True` et l'avertissement ±25-30 % (le marché vraquier est plus volatil que le conteneur).
- **Frais portuaires vrac** : équivalent vrac du `PORT_THC` conteneur — barème USD/t par port (grue/portique, silo, cadence), issu des barèmes publiés des autorités portuaires quand disponibles, sinon barème régional modélisé et signalé.
- **Surestaries (demurrage)** : non chiffrées en v1 — mentionnées comme poste non inclus dans le disclaimer (cohérent avec la doctrine « liste explicite des coûts manquants »).

### 3.4 Contraintes portuaires

Ajouter deux attributs au registre `PORTS` (ou une table parallèle pour ne pas gonfler l'existant) :

- `max_draft_m` (tirant d'eau admissible) → plafonne la classe de navire ;
- `bulk_terminals` (liste : `grain`, `mineral`, `cement`, `general`) → si le terminal requis manque, l'option est dégradée (classe inférieure) ou marquée indisponible avec note, jamais inventée.

### 3.5 Vrac liquide

**Hors périmètre v1.** Tous les produits transportés par navire-citerne — pétrole brut (2709), produits raffinés (2710), GPL/GNL (2711), huiles végétales en vrac (1507–1518, dont palme 1511), mélasses (1703), ammoniac (2814), bitumes (2713–2715), éthanol en vrac (2207) — reçoivent une option maritime `UNAVAILABLE` avec note explicite : « marché tanker (affrètement citerne) non couvert par ce comparateur ». Pas de proxy conteneur, pas de proxy vrac sec — les deux seraient faux. Exception : les huiles végétales conditionnées (bidons, flexitanks) sous le seuil de lot restent en conteneur, comme tout vrac ensaché.

---

## 4. Sources de données et fraîcheur

| Donnée | Source primaire visée | Repli |
|---|---|---|
| Routes benchmark USD/t céréales | routes publiées type IGC Grain Freight (ex. US Gulf→Maroc, mer Noire→Égypte/Algérie), rapports publics | modèle distance-coût `is_modeled` |
| Indices vrac sec | Baltic Exchange (BDI/BHSI/BSI/BPI) via sources publiques citables | valeurs statiques datées dans le code, comme `_WORLD_MARKET_BENCHMARKS` |
| Frais portuaires vrac | barèmes publiés des autorités portuaires africaines (EPAL, OMMP, Namport, TPA...) | barème régional modélisé et signalé |
| Tirants d'eau / terminaux | fiches port des autorités portuaires | attribut absent → pas de contrainte appliquée, note « non vérifié » |

**Rafraîchissement** : étendre le patron existant (`etl/update_world_market_prices.py` + workflow quotidien → `data/json/`) avec un fichier `fret_vraquier.json` : entrées live qui priment sur les valeurs statiques, entrée invalide ignorée, jamais de cours douteux appliqué. Chaque valeur porte `as_of`, `source`, `raw_quote`.

---

## 5. Découpage en lots

### Lot A — Données socle (sans impact utilisateur)
- `backend/logistics_bulk_fees_data.py` : classes de navires, routes benchmark sourcées, modèle distance-coût vrac, frais portuaires vrac, `get_bulk_freight_cost(origin_locode, destination_locode, tonnes, vessel_class=None)`.
- Table de contraintes portuaires (tirant d'eau, terminaux).
- Réécrire `classify_bulk_commodity()` à partir de la **table de référence complète de l'Annexe A** (vrac sec majeur / vrac sec mineur / vrac liquide / conventionnel-neo-bulk / bi-mode), avec classes de navire admissibles, seuil de bascule propre au produit et drapeau `liquid`. Effet immédiat : la couverture de l'exclusion aérienne et du type de cargaison terrestre `bulk` s'étend d'office à tous ces produits, avant même le branchement maritime du Lot B.
- Tests unitaires du module seul + tests de la classification étendue (un cas par catégorie de l'Annexe A).

**Critères d'acceptation** : 100 % des routes benchmark avec source et période ; toute route modélisée marquée `is_modeled` ; distance vrac = distance conteneur pour une même paire de ports (même `_sea_distance_nm`) ; 100 % des lignes de l'Annexe A couvertes par un test de classification.

### Lot B — Intégration au comparateur multimodal
- `_bulk_sea_options()` dans `multimodal_freight_service.py`, branché selon les seuils de lot (3.2) ; en-dessous du seuil, l'option conteneur actuelle est conservée avec la note « ensaché » ; le `bulk_cargo_note` proxy actuel disparaît au profit du vrai tarif.
- Nouveau mode d'option `sea_bulk` (classe navire, USD/t, total, sources, `is_modeled`).
- Vrac liquide → option maritime `UNAVAILABLE` avec note.
- CO₂ : facteur vraquier (≈ 5-8 g/t-km, inférieur au porte-conteneurs) ajouté à `CO2_FACTORS_G_PER_TKM` avec source.

**Critères d'acceptation** : ciment 26 400 kg DZA→MAR reste en conteneur ensaché (sous le seuil) ; blé 25 000 t obtient une option `sea_bulk` supramax/panamax chiffrée en USD/t ; minerai de fer vers un port sans terminal minéralier → dégradation ou indisponibilité explicite, jamais un chiffre silencieux ; café/marchandise générale strictement inchangés (non-régression sur les 110 tests actuels).

### Lot C — Répercussion dans Opportunités
- `logistics_opportunity_adapter` / `report_engine` : pour un vrac au-dessus du seuil, le coût rendu utilise `USD/t × tonnage` au lieu de `coût/conteneur × nombre de conteneurs` ; `shipment_estimator` fournit le tonnage (déjà le cas) et la classe de navire.
- Affichage frontend (`MultimodalComparator.jsx`, rapports Opportunités) : badge classe de navire, USD/t, mention du mode retenu et de la raison (ensaché / affrètement / indisponible).

**Critères d'acceptation** : un rapport Opportunités blé Algérie affiche un coût rendu fondé sur l'affrètement, avec décomposition et sources ; aucun rapport n'affiche simultanément « conteneurs nécessaires » et « affrètement vrac ».

### Lot D — Fraîcheur et industrialisation
- Workflow de rafraîchissement des indices (patron `update_market_prices`), fichier `data/json/fret_vraquier.json`, repli statique daté.
- Tests de l'ETL (patron `test_update_world_market_prices.py`).

**Critères d'acceptation** : une entrée live invalide n'écrase jamais une valeur statique ; chaque valeur servie porte `as_of` et `source`.

---

## 6. Décisions à valider avant le Lot A

1. **Seuils de bascule** : 2 000 t (conteneur→vraquier) et 10 000 t (choix de classe) par défaut, avec seuil propre par produit pour les bi-modes (Annexe A, ex. cacao méga-lot ≥ 12 000 t) — à confirmer ou ajuster à dire d'expert douanier/logistique.
2. **Vrac liquide exclu en v1** (option maritime indisponible avec note) — confirmer.
3. **Granularité v1 des classes** : 4 classes (handysize/supramax/panamax/capesize) suffisent-elles, ou faut-il distinguer handymax ?
4. **Périmètre ports v1** : les 55 ports existants avec attributs vrac renseignés progressivement (attribut absent = pas de contrainte, marqué « non vérifié »), plutôt qu'un sous-ensemble bloquant.
5. **Produits pilotes de recette** : la **classification** couvre d'emblée tous les produits de l'Annexe A ; la **recette chiffrée** (validation des coûts) porte sur des pilotes représentatifs de chaque catégorie — proposé : blé vers Alger (vrac agricole majeur), ciment/clinker intra-Maghreb (vrac mineur), minerai de fer Mauritanie→export (capesize/minéralier), engrais Maroc→Afrique de l'Ouest (vrac mineur), sucre brut vers Afrique de l'Est (vrac mineur), bauxite Guinée→export (vrac majeur), tourteaux de soja import (vrac agro-industriel), cacao Abidjan→Europe en méga-lot (bi-mode, seuil élevé), bois débité Cameroun/Gabon→export (conventionnel), ferraille import Turquie→Afrique de l'Ouest (neo-bulk).
6. **Produits bi-modes** (riz, sucre, cacao, arachides en coque décortiquées, farines) : valider produit par produit le mode par défaut sous le seuil (conteneur ensaché) et le seuil de bascule propre (Annexe A).

---

## 7. Risques et parades

| Risque | Parade |
|---|---|
| Tarifs vraquiers publics rares/volatils | dualité benchmark/`is_modeled` + fourchette ±25-30 % affichée + `as_of` obligatoire |
| Confusion utilisateur conteneur vs vrac | le mode retenu et sa raison sont toujours affichés (ensaché / affrètement / indisponible) |
| Fausse précision sur les frais portuaires | barème régional modélisé signalé comme tel, jamais présenté comme tarif officiel |
| Contraintes portuaires incomplètes | attribut absent = pas de contrainte + note « non vérifié », jamais de blocage inventé |
| Régression sur le flux conteneur existant | Lot B gardé derrière le drapeau `is_bulk_commodity` + suite de tests actuelle (110 tests) exécutée à chaque lot |

---

## 8. Estimation d'effort (indicative)

| Lot | Effort | Dépendance |
|---|---|---|
| A — Données socle | 2-3 sessions | validation des décisions §6 |
| B — Comparateur | 1-2 sessions | Lot A |
| C — Opportunités + UI | 1-2 sessions | Lot B |
| D — Fraîcheur | 1 session | Lot A (parallélisable avec B/C) |

Le Lot A ne modifie aucun comportement visible : il peut être fusionné indépendamment et sans risque dès validation du plan.

---

## Annexe A — Table de référence complète des produits éligibles au vrac

Cette table est la **source de vérité unique** que le Lot A implémente dans `classify_bulk_commodity()`. Elle remplace la liste partielle actuelle (chapitres 25/26/27, 10, 1201, 1701, 31) et couvre l'ensemble des produits susceptibles d'utiliser le mode vraquier, pertinents pour le commerce africain. Recherche par spécificité décroissante (SH6 → SH4 → chapitre), comme aujourd'hui.

Colonnes : classes de navire admissibles ; **seuil** = tonnage de lot en-dessous duquel le mode réel reste le conteneur ensaché/conditionné (défaut 2 000 t sauf mention).

### A.1 Vrac sec majeur (grands volumes, panamax/capesize possibles)

| SH | Produit | Classes navire | Pertinence Afrique |
|---|---|---|---|
| 2601 | Minerai de fer | panamax, capesize | Mauritanie, Afrique du Sud, Libéria, Sierra Leone |
| 2606 (+2818) | Bauxite (et alumine) | panamax, capesize | Guinée (1er exportateur mondial), Ghana, Sierra Leone |
| 2701–2704 | Charbon, lignite, coke | supramax → capesize | Afrique du Sud, Mozambique (export) ; imports cimenteries |
| 1001 | Blé | handysize → panamax | 1er poste d'import céréalier du Maghreb et de l'Égypte |
| 1003 | Orge | handysize → panamax | imports Maghreb (aliment du bétail) |
| 1005 | Maïs | handysize → panamax | imports Afrique du Nord/Ouest ; exports Afrique australe |
| 1007 | Sorgho | handysize, supramax | Sahel, Soudan |
| 1201 | Soja (fèves) | supramax → panamax | imports trituration Maghreb/Égypte |
| 2510 | Phosphates naturels | handysize → panamax | Maroc, Tunisie, Sénégal, Togo (exports majeurs) |

### A.2 Vrac sec mineur (handysize/supramax)

| SH | Produit | Classes navire | Pertinence Afrique |
|---|---|---|---|
| 2523 | Ciment et clinker | handysize, supramax | flux intra-africains massifs ; imports clinker |
| 1701 | Sucre brut | handysize, supramax | imports raffineries (Algérie, Nigéria) ; exports Eswatini, Maurice |
| 1006 | Riz | handysize (**seuil 5 000 t** — massivement ensaché en conteneur en-dessous) | 1er poste alimentaire d'import Afrique de l'Ouest |
| 1002/1004/1008 | Seigle, avoine, autres céréales | handysize | marginal |
| 1101–1104 | Farines et semoules (**bi-mode**) | handysize (**seuil 5 000 t**) | imports Sahel |
| 1107 | Malt | handysize | imports brasseries |
| 1205/1206/1207 | Colza, tournesol, autres oléagineux | handysize, supramax | imports trituration |
| 1202 | Arachides (**bi-mode**) | handysize (**seuil 5 000 t** — conteneur dominant) | Sénégal, Soudan (exports) |
| 2302 | Sons et remoulages | handysize | aliment du bétail |
| 2304–2306 | Tourteaux (soja, arachide, autres) | handysize, supramax | imports aliment du bétail ; exports huileries |
| 2308/2309 | Préparations pour animaux (vrac) | handysize | imports élevage |
| 0714 | Manioc séché (cossettes) | handysize | Afrique de l'Ouest/Centrale |
| 1801 | Cacao en fèves (**bi-mode**) | supramax méga-lot (**seuil 12 000 t** — sacs/conteneurs en-dessous) | Côte d'Ivoire, Ghana, Cameroun : le méga-vrac ABJ/Tema→Europe existe réellement |
| 2501 | Sel | handysize | Namibie, Égypte (exports) |
| 2503 | Soufre | handysize, supramax | intrant acide phosphorique (Maroc, imports massifs) |
| 2507/2508 | Kaolin, argiles | handysize | céramique |
| 2515/2516 | Marbre, granit (blocs) | handysize (conventionnel) | Égypte, Zimbabwe, Namibie |
| 2517/2521 | Granulats, castines | handysize | BTP côtier |
| 2520 | Gypse | handysize | cimenteries |
| 2602 | Minerai de manganèse | supramax, panamax | Gabon (2e mondial), Afrique du Sud, Ghana |
| 2603 | Concentrés de cuivre | handysize, supramax | Zambie, RDC (via ports) |
| 2604/2605 | Nickel, cobalt (concentrés) | handysize | Madagascar, RDC |
| 2607/2608 | Plomb, zinc (concentrés) | handysize | Maroc, Namibie |
| 2610 | Minerai de chrome | supramax | Afrique du Sud, Zimbabwe, Madagascar |
| 2614/2615 | Titane, zirconium (sables minéralisés) | handysize | Sénégal, Mozambique, Madagascar, Sierra Leone |
| 2609/2611–2617 | Autres minerais (étain, tungstène…) | handysize | Nigéria, RDC, Rwanda |
| 2618/2619 | Scories et laitiers | handysize | sidérurgie |
| 2713 (coke de pétrole) | Petcoke | supramax | combustible cimenteries |
| 31 (3102–3105) | Engrais (urée, DAP, potasse, NPK) | handysize, supramax | Maroc/OCP (export mondial), imports massifs partout |
| 7204 | Ferraille | handysize, supramax | imports aciéries (Afrique de l'Ouest, Égypte) |

### A.3 Conventionnel / neo-bulk (cales vraquiers ou navires conventionnels)

| SH | Produit | Classes navire | Remarque |
|---|---|---|---|
| 4401 | Copeaux et plaquettes de bois | handysize, supramax | biomasse |
| 4403/4406/4407 | Grumes, traverses, bois sciés | handysize (conventionnel) | Cameroun, Gabon, Congo, Ghana — exports majeurs |
| 47 (4701–4705) | Pâtes de bois | handysize | conditionné en balles |
| 7201/7203 | Fontes, produits ferreux primaires | handysize | sidérurgie |
| 7207–7216 | Aciers semi-finis et longs (billettes, barres, profilés) | handysize (neo-bulk) | imports BTP massifs |
| 7208–7212 | Aciers plats (bobines) | handysize (neo-bulk) | imports industrie |

Ces produits n'utilisent pas l'aérien et rarement le conteneur au-delà de petits lots — même traitement que le vrac sec mineur en v1, avec note « conventionnel/neo-bulk » dans la sortie.

### A.4 Vrac liquide (tankers — hors périmètre v1, option maritime `UNAVAILABLE` avec note)

| SH | Produit | Marché |
|---|---|---|
| 2709 | Pétrole brut | tanker (VLCC/Suezmax/Aframax) |
| 2710 | Produits raffinés (gazole, essence, jet, fuel) | product tanker |
| 2711 | GPL / GNL | gazier |
| 2712–2715 (hors petcoke) | Bitumes, paraffines | bitumier |
| 1507–1518 | Huiles végétales en vrac (palme, soja, tournesol…) | chemical/product tanker ; conteneur (flexitank) sous le seuil |
| 1703 | Mélasses | tanker |
| 2207 | Éthanol en vrac | chemical tanker |
| 2814 | Ammoniac | gazier |
| 28/29 (sélection) | Acides et chimie liquide de base (ex. 2807 acide sulfurique) | chemical tanker |

### A.5 Produits bi-modes — règle de traitement

Pour les produits marqués **bi-mode** (riz, farines, arachides, cacao, sucre blanc 1701.99…), le mode par défaut sous le seuil propre au produit est le **conteneur ensaché** (pratique réelle dominante en Afrique), et le vraquier n'est proposé qu'au-delà. Le seuil est un paramètre par ligne de la table, pas une constante globale — c'est ce qui évite à la fois le « ciment par avion » d'hier et un « 500 t de riz en supramax » demain.

### A.6 Produits exclus de cette table

Café (0901), thé (0902), coton (5201), noix de cajou, fruits et légumes, viandes, poissons, produits manufacturés : jamais vraquiers en pratique commerciale courante — ils restent au régime général (conteneur, reefer le cas échéant, aérien sous plafond de poids). Toute demande utilisateur récurrente sur un produit absent de la table alimente la file de priorisation (doctrine de collecte guidée par la demande, §21.3 de l'audit).
