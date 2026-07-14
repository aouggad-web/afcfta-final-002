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
| Handysize | 10 000 – 39 999 t | ciment, engrais, sucre, riz ensaché, petits lots céréaliers | accepté presque partout |
| Supramax/Ultramax | 40 000 – 64 999 t | céréales, charbon, engrais | tirant d'eau ≥ ~12 m |
| Panamax | 65 000 – 99 999 t | céréales, charbon, minerai | tirant d'eau ≥ ~13,5 m |
| Capesize | ≥ 100 000 t | minerai de fer, charbon | rares terminaux africains dédiés (ex. Saldanha) |

### 3.2 Bascule par taille de lot (par expédition)

| Tonnage du lot | Mode maritime retenu | Affichage |
|---|---|---|
| < 2 000 t | Conteneur (marchandise ensachée/big bags) | tarif conteneurisé actuel, avec note « vrac ensaché en conteneur — pratique réelle pour ce tonnage » |
| 2 000 – 10 000 t | Vraquier handysize (lot partiel ou complet) | USD/t vraquier |
| > 10 000 t | Classe de navire choisie selon tonnage + contraintes du port | USD/t vraquier |

Les deux seuils sont des **paramètres nommés à valider** (`BULK_CHARTER_MIN_TONNES`, `BULK_FULL_VESSEL_TONNES`) — valeurs ci-dessus proposées à dire d'expert, ajustables sans toucher au code appelant.

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

### 3.5 Vrac liquide (pétrole brut)

**Hors périmètre v1.** Le SH 2709 (et chapitre 27 liquide) reçoit une option maritime `UNAVAILABLE` avec note explicite : « marché tanker (affrètement pétrolier) non couvert par ce comparateur ». Pas de proxy conteneur, pas de proxy vrac sec — les deux seraient faux.

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
- Enrichir `classify_bulk_commodity()` : classe(s) de navire admissible(s) par produit, drapeau `liquid` pour le chapitre 27 liquide.
- Tests unitaires du module seul.

**Critères d'acceptation** : 100 % des routes benchmark avec source et période ; toute route modélisée marquée `is_modeled` ; distance vrac = distance conteneur pour une même paire de ports (même `_sea_distance_nm`).

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

1. **Seuils de bascule** : 2 000 t (conteneur→vraquier) et 10 000 t (choix de classe) — à confirmer ou ajuster à dire d'expert douanier/logistique.
2. **Vrac liquide exclu en v1** (option maritime indisponible avec note) — confirmer.
3. **Granularité v1 des classes** : 4 classes (handysize/supramax/panamax/capesize) suffisent-elles, ou faut-il distinguer handymax ?
4. **Périmètre ports v1** : les 55 ports existants avec attributs vrac renseignés progressivement (attribut absent = pas de contrainte, marqué « non vérifié »), plutôt qu'un sous-ensemble bloquant.
5. **Produits pilotes de recette** : proposé — blé vers Alger, ciment/clinker intra-Maghreb, minerai de fer Mauritanie→export, engrais Maroc→Afrique de l'Ouest, sucre brut vers Afrique de l'Est.

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
