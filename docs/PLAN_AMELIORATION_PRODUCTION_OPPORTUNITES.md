# Production & Opportunités — analyse approfondie et plan d'amélioration

Date de l'audit : 2026-09-21. Périmètre : les deux modules `production` et
`opportunities` (front-end, back-end, données, chaîne d'ingestion).

Toutes les valeurs de cette page ont été **mesurées** sur le dépôt et sur les
sources en ligne le jour de l'audit, pas estimées. Les commandes de mesure sont
rappelées en annexe pour que chaque chiffre soit reproductible.

> **État d'avancement.** Le constat (§ 1 et 2) décrit le dépôt tel qu'il était
> à l'audit. Le tableau du § 6 marque d'un ✅ ce qui est livré depuis.
>
> | Phase | État |
> |---|---|
> | 0 — sans nouvelle source | ✅ livrée |
> | 1 — manufacturing et mining | ✅ livrée |
> | 2 — offices nationaux | ✅ 2.1, 2.2, 2.4 livrées ; **2.3 livrée pour un premier lot de cinq pays** — 1 intégré, 4 écartés avec motifs |
> | 3 — pont Production ↔ Opportunités | ✅ livrée (3.3 complétée : les Chaînes de valeur servent des producteurs réels, plus un jeu en dur) |
> | 4 — forme | ✅ 4.1, 4.3 (couleurs), 4.4 livrées ; **4.2 en suspens** (traduction ar/pt) ; la mise en page reste ouverte, versée au chantier de refonte |
> | 5 — constats nés des tests de 4.4 | ✅ livrée |
>
> **Ce qui reste ouvert, et pourquoi.** La phase 2 est le seul chantier long :
> elle avance pays par pays et dépend de ce que chaque office publie
> réellement — le lot de cinq pays traité en 2.3 en donne la mesure, un seul
> est entré. La phase 4.2 attend une traduction humaine des 854 clés, pas du
> code. La refonte UX/front est le chantier suivant, décidé après ces deux
> modules.
>
> Plusieurs actions du plan se sont révélées mal formulées à l'usage ; les
> corrections sont écrites dans les phases concernées, elles ne sont pas
> masquées.

---

## 0. Ce qu'il faut retenir

Les deux modules ne souffrent pas du même mal.

**Production** est honnête mais **maigre et figée**. Les garde-fous sont
exemplaires — le code refuse de présenter une estimation comme une mesure, et le
dit à l'écran. Mais trois des quatre dimensions sont des **dictionnaires Python
écrits à la main** qui ne se rafraîchissent jamais tout seuls, et la dimension
macro ne contient que des pourcentages sur deux ans.

Le constat le plus frappant tient en une ligne : **la plateforme jette 84 % d'un
fichier qu'elle télécharge déjà tous les mois**. Le bulk FAOSTAT contient 62 408
points de donnée sur 2019-2024 ; le script en importe 10 138. Surfaces cultivées
et rendements — 32 802 points — ne sont jamais lus.

**Opportunités** est riche mais **suspendue à une clé d'API**. Cinq de ses neuf
sous-onglets renvoient `{"error": "ANTHROPIC_API_KEY not configured"}` sans clé.
Son ancrage factuel est réel et bien construit — mais il lit la production, donc
il hérite de toutes les faiblesses ci-dessus. En particulier, l'ancrage
industriel du continent entier repose sur **15 codes SH**.

D'où la thèse de ce plan : **améliorer Production améliore mécaniquement
Opportunités**. Les deux chantiers n'en font qu'un, et il faut commencer par les
données.

---

## 1. Module Production — état mesuré

### 1.1 Le socle de données

Fichier unique : `data/json/production_africaine.json` — 8,5 Mo, `last_updated`
2026-08-25.

| Dimension | Enreg. | Pays | Années | Source |
|---|---:|---:|---|---|
| `value_added_macro` | 514 | 54 | **2023-2024** | World Bank WDI |
| `agri_faostat` | 10 138 | 54 | 2019-2024 | FAOSTAT QCL bulk |
| `manufacturing_unido` | **190** | 54 | **2024** | UNIDO INDSTAT4 |
| `mining_usgs` | 432 | **41** | 2022-2024 | USGS MCS / EIA / OPEC / WNA |
| `agri_projections` | 60 | 15 | 2025, 2030 | OCDE-FAO Outlook |

L'agriculture porte 89 % des enregistrements. Les trois autres dimensions
réunies pèsent 1 136 lignes pour 54 pays — soit, en moyenne, **7 points de
donnée par pays et par dimension**, toutes années confondues.

### 1.2 Les sept trous, par ordre de coût de réparation

**(a) Macro : que du relatif, et deux ans.** Les 514 lignes ne portent que cinq
indicateurs, tous en pourcentage : `NV.AGR.TOTL.ZS`, `NV.IND.TOTL.ZS`,
`NV.IND.MANF.ZS`, `NV.SRV.TOTL.ZS`, `NY.GDP.MKTP.KD.ZG`. Aucune valeur absolue.
On peut donc dire que l'Angola consacre 7,4 % de son PIB à l'industrie
manufacturière en 2023, mais pas combien cela fait en dollars — ni le comparer à
son voisin autrement qu'en parts. Un module qui parle d'opportunités
d'investissement sans jamais donner de montant se prive de son unité de compte.

Or ces valeurs absolues existent, gratuitement, à la même adresse déjà utilisée.
Vérifié le jour de l'audit :

```
NV.IND.MANF.CD (Nigeria) — Manufacturing, value added (current US$)
  2024  21 839 012 706      2021  53 710 232 520
  2023  45 195 964 342      2020  48 392 900 235
  2022  59 108 815 373      2019  60 811 664 917
```

La cause est à deux constantes près, dans `backend/scripts/fetch_wdi_macro.py`
(134 lignes) : `INDICATORS` (5 entrées) et `YEARS = (2023, 2024)`.

**(b) Agriculture : 84 % du fichier déjà téléchargé est jeté.** C'est le
constat le plus net de tout l'audit, et il a été vérifié en téléchargeant le
bulk le jour même.

Les 10 138 lignes ne portent qu'un seul élément, `Production` (5510, en tonnes).
Le schéma déclare pourtant `area_ha`, `yield_kg_ha` et `rank_africa` — et ces
trois champs sont **`null` sur 10 138 lignes sur 10 138**.

Or `Production_Crops_Livestock_E_Africa.zip`, que le cron mensuel télécharge
**déjà**, contient sur la seule fenêtre 2019-2024 :

| Élément FAOSTAT | Points disponibles | Points importés |
|---|---:|---:|
| 5510 — Production | 29 606 | 10 138 |
| 5312 — *Area harvested* | 16 422 | **0** |
| 5412 — *Yield* | 16 380 | **0** |
| **Total** | **62 408** | **10 138 (16 %)** |

Deux causes, cumulatives :

1. **Le filtre de commodités.** `FAOSTAT_ITEM_TO_COMMODITY` retient 69 items ;
   le fichier en contient **254** avec de la production, dont 150 avec surface
   et rendement.
2. **Les éléments non lus.** Surface et rendement ne sont simplement jamais
   parsés.

Et le fichier couvre **1961-2024** — 64 années. La plateforme en exploite 6. La
fenêtre courte n'est pas une contrainte de la source, c'est un choix du script.

L'enjeu n'est pas que du volume. Le rendement distingue un pays qui produit
beaucoup parce qu'il cultive large d'un pays qui produit beaucoup parce qu'il
cultive bien — autrement dit un pays qui a de la terre d'un pays qui a un
savoir-faire. Pour un module d'opportunités, ce n'est pas la même
recommandation.

**(c) Manufacturing : 190 lignes, une année, et une couverture en dents de
scie.** Ventilation par division ISIC :

| Division | Intitulé | Pays couverts |
|---|---|---:|
| 10 | Produits alimentaires | 54 |
| 11 | Boissons | 36 |
| 23 | Minéraux non métalliques | 18 |
| 24 | Métaux de base | 15 |
| 13 / 19 | Textiles / Coke & pétrole raffiné | 14 |
| 22 | Caoutchouc et plastiques | 13 |
| 20 | Chimie | 9 |
| 14 | Habillement | 5 |
| 16, 26, 27, 29 | Bois, électronique, équip. élec., automobile | 2 |
| 12, 17, 21, 32 | Tabac, papier, pharmacie, diamants | 1 |

Sept divisions (15, 18, 25, 28, 30, 31, 33) sont **absentes**. Et 83 des 190
lignes (44 %) portent `is_estimation: true`.

**(d) Le détail ISIC4 ne couvre que 20 pays sur 54.**
`backend/data/unido/unido_idsb_indstat_isic4_2018plus.csv.gz` contient 43 774
lignes — mais pour : AGO, BWA, CIV, CPV, EGY, GHA, KEN, MAR, MLI, MUS, MWI, NAM,
RWA, SEN, SWZ, TGO, TUN, TZA, ZMB, ZWE. Les 34 autres passent par
`_estimated_isic4_payload()`, qui répartit à parts égales la valeur d'une
division entre ses classes.

Le code est parfaitement franc sur ce que cela vaut — sa docstring dit
elle-même que « la répartition égale n'est **pas** une mesure » et qu'elle est
« inutilisable pour comparer deux classes d'une même division ». C'est la bonne
attitude. Mais cela signifie que **63 % des pays** n'ont pas de détail
manufacturier réel.

**(e) Mining : 13 pays à zéro.** BEN, CAF, COM, CPV, DJI, GMB, GNB, MUS, MWI,
SOM, STP, SWZ, SYC.

Attention au diagnostic : pour une bonne moitié d'entre eux (SYC, COM, STP, CPV,
DJI, GMB), une production extractive négligeable est la **réalité**, pas une
lacune. Les traiter comme des trous à combler produirait de la donnée fabriquée.
Pour BEN, CAF, GNB, MWI, SWZ, SOM en revanche, une production existe et manque.

**(f) L'emploi existe mais reste enfermé dans le détail ISIC4.** Le CSV UNIDO
local porte bien `01` (Establishments, 3 093 lignes), `04` (Employees, 2 527),
`05` (Wages and salaries, 2 852) et `31` (Female employees, 1 732) — et ces
indicateurs **sont** exposés par l'API et affichés par le front
(`ISIC4_INDICATOR_LABELS`).

Mais ils ne vivent que là : dans le tableau de détail ISIC4, pour les 20 pays
couverts, au clic. `production_africaine.json` ne contient **aucun**
enregistrement d'emploi. Conséquence : l'emploi n'est pas une dimension du
module, il n'entre dans aucun classement, aucune vue d'ensemble, et surtout pas
dans l'ancrage IA d'Opportunités — qui lit `production_africaine.json` via
`get_country_profile()`.

C'est dommage, parce que c'est la donnée qui transforme « ce pays produit X » en
« ce pays sait faire X, avec tant de monde ». Elle est déjà là ; elle est juste
rangée trop bas.

**(g) Le passage mensuel fait *régresser* le fichier.** Trouvé en implémentant
la phase 0, pas à l'audit initial — et c'est le défaut le plus grave de la
chaîne.

`update_production_data.yml` lance `build_production_faostat_usgs.py`, qui
n'écrit que le **socle** : 162 enregistrements macro et 166 miniers. Les
dimensions complètes (macro World Bank, minéraux étendus, prévisions OCDE-FAO)
sont posées par une seconde étape, `enrich_production_data.py` — et **aucun
workflow ne la lance**.

Un passage mensuel produit donc une PR qui ramène macro de 514 à 162 et les
mines de 432 à 166. Le garde-fou de validation ne l'attrape pas : il vérifie
`mining >= 100`, et 166 passe. Le fichier n'a survécu jusqu'ici que parce que
personne n'a laissé le cron aboutir.

### 1.3 La chaîne d'ingestion ne tourne pas

| Dimension | Rafraîchissement réel |
|---|---|
| Agriculture | ✅ cron mensuel (`update_production_data.yml`, `0 4 3 * *`) — téléchargement effectif |
| Mining | ❌ dict Python `USGS_MULTI_YEAR` écrit à la main |
| Manufacturing | ❌ `backend/etl/unido_data.py`, **1 967 lignes** écrites à la main |
| Macro | ❌ `backend/etl/macro_wdi_data.py`, généré par script — dernier passage 2026-08-25 |

`production_etl.yml` n'a **pas** de `schedule` : `workflow_dispatch` seulement.
Le seul cron existant n'actualise en pratique que l'agriculture, puisque USGS et
UNIDO sont des littéraux Python dans le script qu'il appelle.

Conséquence : **trois dimensions sur quatre dérivent** jusqu'à ce que quelqu'un
édite du Python à la main.

---

## 2. Module Opportunités — état mesuré

### 2.1 Neuf sous-onglets, deux régimes

| Sous-onglet | Ancrage | Sans `ANTHROPIC_API_KEY` |
|---|---|---|
| Analyse IA | `/ai/opportunities` | ❌ mort |
| Vue d'ensemble | `/ai/summary` | ❌ mort |
| Chaînes de valeur | `/ai/value-chains` | ❌ mort |
| Par produit | `/ai/product` | ❌ mort |
| Comparaison | `/ai/compare` | ❌ mort |
| Flux stratégiques | `/strategic/flows` | ✅ données réelles |
| Substitution | `/substitution/*` | ✅ données réelles |
| Simulateur ZLECAf | `/dismantlement/impact` | ✅ données réelles |
| Comparateur bilatéral | `/bilateral-tariff` | ✅ données réelles |

**Cinq sur neuf** renvoient `{"error": "ANTHROPIC_API_KEY not configured"}`. Le
cache IA sur disque contient **un seul fichier**. Chaque consultation non mise en
cache est donc un appel LLM facturé, et toute panne ou tout quota atteint vide
plus de la moitié du module.

### 2.2 L'ancrage factuel est bon — et c'est là qu'est le levier

`claude_trade_service._country_opportunity_grounding()` est une vraie
construction : profil de production réel du pays + flux OEC réels + tarifs, avec
une invalidation de cache indexée sur la version du fichier de production (`pdv`)
— tout rebuild de `production_africaine.json` périme automatiquement les analyses
en cache. C'est propre.

Le plafond est ailleurs. `production_capacity_service.list_tracked_products()`
renvoie **114 codes SH** :

| Dataset | Codes SH mappés |
|---|---:|
| agri | 69 |
| mining | 30 |
| **manufacturing** | **15** |
| **Total** | **114** |

Pour tout produit hors de ces 114, l'ancrage production est vide. Et le mode
« industriel » de l'analyse IA — celui qui doit répondre à « que puis-je
transformer ici ? », la question la plus rentable d'une plateforme ZLECAf —
s'appuie sur **15 codes SH pour 54 pays**.

C'est le goulot d'étranglement le plus coûteux de tout le périmètre audité.

### 2.3 Un pont construit, presque pas emprunté

`production_capacity_service` expose `get_country_profile()`,
`get_continental_producers()`, `get_capacity()`. Le front-end Opportunités ne
l'appelle qu'**une seule fois**, à `ValueChains.jsx:617`, et uniquement après une
recherche manuelle de code SH.

Le chaînage naturel — *ce pays produit ceci → voici où le vendre sous la ZLECAf,
à quel tarif, avec quelle règle d'origine* — n'existe dans aucun écran, alors que
toutes les briques sont écrites.

### 2.4 Dette de forme

| Mesure | Production | Opportunités |
|---|---:|---:|
| Clés i18n | 32 | **0** |
| Ternaires `language === 'fr'` en dur | 41 | 60 |
| `className=` | 567 | 621 |
| `style={{…}}` en ligne | 24 | **428** |
| Lignes de composants | 4 290 | ~8 000 |
| Fichiers de test front | 1 (58 lignes) | 3 |

Opportunités n'a **aucune** clé i18n : ses libellés sont dupliqués dans une
constante `TABS = { fr: [...], en: [...] }` et dans 60 ternaires dispersés.
Production passe par `t('production.*')`. Les deux modules ne se ressemblent ni
dans le code ni à l'écran — l'un est en Tailwind, l'autre à moitié en styles
inline.

Et les deux ne parlent que français et anglais, alors que les langues de travail
de la ZLECAf incluent l'arabe et le portugais. Tant qu'Opportunités n'est pas
internationalisé, ajouter `ar` et `pt` est impossible de toute façon.

---

## 3. Les sources — ce qui est réellement joignable

Testé le 2026-09-21 depuis cet environnement. Un `000` signifie « injoignable
depuis ce bac à sable », pas « site mort » : les runners GitHub ont un réseau
ouvert, comme le notent déjà les commentaires des workflows. À revalider là-bas.

### 3.1 Sources internationales

| Source | Code | Verdict |
|---|---:|---|
| **World Bank API v2** | 200 | ✅ sans clé, valeurs absolues confirmées |
| **FAOSTAT bulk (zip)** | 200 | ✅ déjà téléchargé chaque mois — exploité à 16 % |
| **OEC tesseract** | 200 | ✅ déjà utilisé |
| **UNSD SDG API** | 200 | ✅ à exploiter (ODD 9.2.1 VAM/hab., 9.2.2 emploi manuf.) |
| **UNECA ecastats** | 200 | ✅ à explorer |
| **USGS (publications)** | 200 | ✅ PDF, extraction nécessaire |
| UN Comtrade | 401 | 🔑 clé requise — la rotation de clés est **déjà codée** |
| WTO API | 401 | 🔑 clé requise |
| UNIDO stat portal | **403** | ⛔ confirme l'absence d'endpoint libre |
| AfDB / Knoema | 403 | ⛔ |
| IMF datamapper | 403 | ⛔ |
| ILOSTAT (rplumber) | 200 mais 0 ligne | ⚠️ à revalider sur runner — voir §4.3 |

### 3.2 Offices nationaux de statistique

C'est la demande explicite, et c'est aussi le gisement le plus mal exploité.

**Ce qui existe déjà.** `backend/services/national_official_stats.py`, 140
lignes, **un seul pays** : Maurice (EDB, bulletin de juillet 2024). Le module est
appelé par l'ancrage IA (`claude_trade_service.py:818`) et par
`routes/countries.py:142`.

Sa docstring pose déjà la bonne règle — valeurs reprises telles que publiées,
dans la monnaie de publication, aucune conversion maison, aucun chiffre complété
— et surtout le bon **argument** : les statistiques nationales sont la seule
source qui sépare les **exportations domestiques des réexportations**. Cette
distinction est décisive pour les règles d'origine ZLECAf : une marchandise
réexportée depuis une zone franche n'acquiert pas l'origine locale.

Le patron est écrit. Il couvre 1 pays sur 54.

**Joignabilité testée :**

| Joignables (200) | Injoignables depuis le bac à sable (000) |
|---|---|
| ZAF (Stats SA), EGY (CAPMAS), MAR (HCP), TUN (INS), TZA (NBS), MUS (Statistics Mauritius) | NGA, KEN, DZA, GHA, CIV, ETH, UGA, SEN, RWA |

**Un atout déjà en place.** Le dépôt a une discipline de registre de sources
mûre — `docs/data-sources/*_SOURCE_REGISTER.md` avec éditeur, date de
consolidation, `verification_status` et **SHA-256** par document. Elle ne sert
aujourd'hui qu'aux sources juridiques et tarifaires, sur 5 pays. Elle se
transpose telle quelle aux statistiques de production.

---

## 4. Plan d'amélioration

Quatre phases, ordonnées par rapport valeur/coût. Chaque action porte son
**critère de vérification** — au sens du § 4 de `CLAUDE.md` : un objectif qu'on
peut boucler seul, pas un « faire marcher ».

### Phase 0 — Ce qui se répare sans nouvelle source (quelques jours)

Rien ici ne demande d'autorisation, de clé, ni de source inédite. Tout est déjà
téléchargé ou déjà joignable.

| # | Action | Fichier | Vérification |
|---|---|---|---|
| 0.1 | Étendre `INDICATORS` aux valeurs absolues (`NV.IND.MANF.CD`, `NV.AGR.TOTL.CD`, `NV.IND.TOTL.CD`, `NV.SRV.TOTL.CD`, `NY.GDP.MKTP.CD`) et `YEARS` à 2015-2024 | `backend/scripts/fetch_wdi_macro.py` | `value_added_macro` passe de 514 à ≳ 4 500 lignes ; chaque pays a une série USD sur ≥ 8 ans |
| 0.2 | Parser les éléments FAOSTAT **5312** (surface) et **5412** (rendement) — le bulk est déjà téléchargé | `backend/scripts/build_production_faostat_usgs.py` | `area_ha`/`yield_kg_ha` non nuls sur ≥ 95 % des lignes de culture ; aucune valeur de production modifiée |
| 0.3 | Calculer `rank_africa` au build (champ déclaré, jamais rempli) | idem | rang continental présent par commodité × année ; classements affichables sans calcul côté client |
| 0.4 | Promouvoir l'emploi ISIC4 (`01`/`04`/`05`/`31`) en dimension du dataset principal, pas seulement en détail au clic | `backend/scripts/build_production_faostat_usgs.py`, `production_capacity_service` | l'emploi apparaît dans `production_africaine.json` et dans `get_country_profile()` pour les 20 pays ISIC4 |
| 0.5 | Faire lancer `fetch_wdi_macro.py` **et** `enrich_production_data.py` par le passage mensuel, et caler les garde-fous sur la surcouche (`mining >= 400`, `macro >= 4000`) et non sur le socle | `.github/workflows/update_production_data.yml` | le workflow échoue si le fichier produit est amputé de sa surcouche |

**Pourquoi d'abord.** Ces actions augmentent nettement le contenu utile de la
production pour un coût de quelques heures, sans ajouter une seule dépendance.
Et comme l'ancrage IA est indexé sur la version du fichier de production, **les
analyses d'Opportunités s'enrichissent automatiquement** dès le rebuild, sans
toucher à ce module.

> **Correction apportée par la mise en œuvre.** Ce plan proposait d'abord
> d'élargir `FAOSTAT_ITEM_TO_COMMODITY` de 69 à ~250 items en phase 0. C'était
> une erreur, et le dépôt l'a dit tout seul :
> `tests/test_hs_commodity_mapping.py::test_no_production_commodity_left_without_hs_mapping`
> pose un invariant explicite — **toute commodité présente dans le dataset doit
> être atteignable par un code SH**, faute de quoi sa donnée est invisible au
> module Opportunités et le calcul de besoin national retombe silencieusement
> sur un proxy.
>
> L'élargissement de l'ingestion et l'élargissement du pont SH ne sont donc pas
> deux chantiers : c'est le même. Il est déplacé en **phase 3.1**, où il doit
> être mené avec sa table de correspondance. Mesuré au passage : le bulk
> contient 254 items, dont 21 sont des **agrégats** FAOSTAT (« Cereals,
> primary », « Meat, Total ») qu'il faudra écarter sous peine de doubler chaque
> total, et le zip publie un code **CPC** par item qui permet de classer
> cultures / élevage / produits transformés sans rien deviner.

### Phase 1 — Combler manufacturing et mining (1 à 2 semaines)

**1.1 — Manufacturing, par contournement. ✅ livré.** UNIDO INDSTAT n'a pas
d'endpoint libre (403 reconfirmé). Deux voies ont été exploitées :

- **WDI `NV.IND.MANF.CD`** — valeur ajoutée manufacturière absolue. Livré en
  phase 0 : 48 pays sur 50 ont ≥ 5 ans. LBY (3 ans) et SSD (1 an) restent en
  deçà parce que la Banque mondiale n'en publie pas davantage.
- **Base ODD de l'UNSD** — l'UNSD republie librement les séries qu'UNIDO lui
  fournit comme dépositaire de la cible 9.2. Nouvelle dimension
  `manufacturing_unsd` : **912 enregistrements, 53 pays, 2015-2025**.

| Série | Pays | Points | Apport |
|---|---:|---:|---|
| `NV_IND_MANFPC` — VAM par habitant | 53 | 583 | taille rapportée à la population |
| `SL_TLF_MANF` — part de l'emploi manufacturier | 44 | 166 | poids dans l'emploi |
| `NV_IND_TECH` — part moyenne et haute technologie | 26 | 163 | **sophistication industrielle**, absente sous toute forme jusqu'ici |
| `NV_IND_SSIS` — part des petites industries | 2 | 7 | **écartée** : trop mince pour porter une lecture continentale |

> **Correction apportée par la mise en œuvre.** Le critère écrit ici — « le
> nombre de pays en `is_estimation` seule passe sous 15 » — est **inatteignable
> par cette voie**, et il fallait le dire plutôt que de le contourner. Ces 32
> pays le sont sur la *ventilation par division ISIC* ; l'UNSD republie des
> **agrégats nationaux**, pas des divisions. Aucune source libre ne publie la
> ventilation : elle reste derrière le 403.
>
> Ce que la voie UNSD apporte est autre chose, et utile : trois grandeurs
> manufacturières **mesurées** qui permettent de juger un pays sans s'appuyer
> sur l'estimation de structure. Les deux dimensions sont donc tenues
> séparées — les fondre ferait passer de l'estimé pour du mesuré.

*Vérification tenue* : dimension séparée de `manufacturing_unido`, unités et
bases de prix portées par chaque enregistrement, 13 tests.

**1.2 — Mining, en disant ce que les sources disent. ✅ livré.**

Ce plan proposait de répartir les treize pays en « production réelle à
collecter » (BEN, CAF, GNB, MWI, SWZ, SOM) et « pas de production
significative » (SYC, COM, STP, CPV, DJI, GMB). **Cette répartition était une
supposition de ma part, pas un fait sourcé** — exactement ce que le contrat de
données du dépôt interdit. Elle n'a pas été retenue.

À la place, une source publiée et lisible par machine a été trouvée : le *USGS
Mineral Commodity Summaries 2025 Data Release*, membre
`MCS2025_World_Data.csv` (ScienceBase, 1 250 lignes, production 2023 et
estimation 2024 par commodité et par pays). Il tranche la question :
**aucun des treize pays n'y figure**, alors que 32 pays africains y sont
recensés.

La réponse minière porte désormais un bloc `coverage` à trois états :

| Statut | Pays | Sens |
|---|---:|---|
| `COVERED` | 41 | production publiée par au moins une source ingérée |
| `NOT_LISTED_BY_SOURCES` | 13 | aucune production rapportée par les sources consultées |
| `LISTED_BY_USGS_NOT_INGESTED` | 0 | recensé par USGS mais pas encore ingéré — lacune de collecte |

La nuance est écrite dans la réponse et verrouillée par un test : **absent
d'USGS ne veut pas dire sans extraction**. MCS ne recense ni la production
artisanale, ni les volumes sous son seuil, ni les hydrocarbures (EIA/OPEC chez
nous) ni l'uranium (WNA). Le statut porte sur nos sources, jamais sur le pays —
le Niger l'illustre : `COVERED` par la WNA, absent d'USGS.

*Vérification tenue* : les 54 pays reçoivent une couverture, aucun onglet muet ;
9 tests.

*Trouvé au passage, non traité ici* : ce même fichier USGS recense **46
commodités africaines contre 30 ingérées**. Seize commodités sont donc
disponibles gratuitement, et remplaceraient une partie du dictionnaire Python
écrit à la main. À faire dans un lot dédié.

**1.3 — Emploi sectoriel via ILOSTAT. ✅ sondé, intégration à décider.**

L'audit avait conclu « peut-être injoignable » : l'endpoint `rplumber.ilo.org`
répond HTTP 200 et renvoie **zéro octet**. C'était le mauvais endpoint, pas une
source fermée. L'interface **SDMX** (`sdmx.ilo.org`) sert les données sans clé.
La sonde est figée dans le dépôt : `scripts/probe_ilostat_coverage.py`.

Relevé du 2026-09-21, dataflow `DF_EMP_TEMP_SEX_ECO_NB`, fenêtre 2015+ :

- **48 pays sur 54**, 6 204 observations, 2015-2025 ;
- **56 classifications d'activité** (total, agriculture, industrie, services,
  puis détail ISIC) ;
- manquants : CAF, COG, ERI, GIN, LBY, SSD ;
- contrainte : une requête portant les 54 pays est refusée (403, URL trop
  longue) — interroger par lots de 8.

**Ce que la colonne `SOURCE` révèle, et qui compte pour la phase 2** : chaque
observation nomme son enquête d'origine — « LFS - Labour Force Survey »,
« LFS - Enquête Nationale sur l'Emploi », « LFS - Enquête sur la Population
Active »… Ce sont les **enquêtes emploi des offices nationaux de statistique**,
harmonisées par l'OIT. C'est donc une voie d'accès à la statistique nationale
qui ne demande ni de négocier avec 54 offices ni d'extraire des PDF — à
verser au raisonnement de la phase 2.

*Vérification tenue* : la sonde tourne et se reproduit ; aucune ligne
d'intégration n'a été écrite avant elle.

### Phase 2 — La couche « offices nationaux de statistique »

C'est la demande explicite, et le chantier structurant. Il ne s'agit pas
d'ajouter des chiffres mais de **créer la couche qui manque**.

**2.1 — Du dictionnaire en dur au registre piloté par la donnée. ✅ livré.**

`national_official_stats.py` est désormais un lecteur ; la donnée vit dans
`data/national_stats/<ISO3>.json`, documentée par
`docs/data-sources/<ISO3>_STATS_REGISTER.md` — même discipline que les
registres juridiques du dépôt : éditeur, publication, URL, année des données,
devise, SHA-256. **Ajouter un pays ne demande plus de toucher au Python.**

Maurice est migré sans changement de comportement : le texte d'ancrage injecté
dans le prompt est identique au caractère près (`11,500 MUR Mn`).

> **Une clé a dû changer.** Le montant se lisait dans `value_mur_mn` — une clé
> portant la devise. La garder aurait obligé chaque pays ajouté à inventer la
> sienne (`value_kes_mn`, `value_ngn_mn`…), ce qui ruine l'idée même de
> registre. Le montant se lit maintenant dans `value`, l'unité dans `source`.
> Une assertion de test a été mise à jour en conséquence, et l'explication y
> figure. Les valeurs servies et les lignes d'ancrage, elles, n'ont pas bougé.

**2.2 — Classer les 54 pays par ce qu'ils publient réellement. ✅ livré.**

Le classement est **généré**, pas rédigé :
`backend/scripts/report_national_stats_coverage.py` écrit
`docs/data-sources/COUVERTURE_STATISTIQUES_NATIONALES.md`. Un tableau de
couverture écrit à la main vieillit mal et ment vite.

La phase 1 a changé l'économie de ce chantier. La sonde ILOSTAT a montré que
les enquêtes emploi des offices nationaux nous parviennent déjà harmonisées
pour 48 pays. Les paliers ne sont donc plus « portail / PDF / rien » mais
**par voie d'accès**, du moins cher au plus cher :

| Palier | Sens | Pays |
|---|---|---:|
| **A** | Collecte directe — bloc adossé à une publication nommée et datée | **2** |
| **B** | Republiée harmonisée — ILOSTAT ou UNSD, rien à négocier | **46** |
| **C** | Non atteinte | **6** |

**Et pourquoi le palier B ne suffit pas.** Les republications portent l'emploi
et l'activité. Elles ne portent pas la séparation exportations domestiques /
réexportations — que seul l'office national publie, et qui commande l'origine
ZLECAf. Un pays en palier B est **couvert pour l'emploi, découvert pour
l'origine**. C'est vers cette distinction que la collecte directe doit aller,
et vers les pays à zones franches actives d'abord.

**2.3 — Viser d'abord ce que seuls les NSO savent dire. ✅ livré — un lot de
cinq pays à zones franches actives, dont un seul est entré, et pas comme
prévu.**

Cible : Maroc, Kenya, Égypte, Togo, Djibouti — les pays où la distinction
domestique / réexportation change réellement une conclusion. Résultat :

| Pays | Issue | Motif |
|---|---|---|
| **Togo** | **INTÉGRÉ**, mais en avertissement | voir ci-dessous |
| Maroc | écarté — **sur le fond** | L'Office des Changes ne publie pas cette ventilation. L'analogue marocain est l'admission temporaire : un concept douanier *différent*. Le plaquer sur ce schéma serait une fabrication par analogie. |
| Kenya | écarté — accès | `knbs.or.ke` échoue au handshake TLS depuis le bac à sable (`unknown CA`), bundle CA du proxy compris. Ce n'est pas un refus de politique. **À revalider sur un runner** : le KNBS Economic Survey publie « Domestic Exports » et « Re-exports » en propre — c'est le meilleur candidat restant. |
| Égypte | écarté — accès | Page CAPMAS du commerce extérieur : 1 421 octets, coquille JavaScript. |
| Djibouti | écarté — accès | INSTAD : coquille de 4 309 octets, tunnel interrompu en cours d'échange. |

Aucun fichier n'est créé pour les quatre écartés : un bloc vide vaut moins
qu'un bloc absent.

**Le Togo est le cas intéressant, parce qu'il a échoué utilement.** Son
bulletin trimestriel (INSEED, 4ᵉ trimestre 2025, 137 pages) dit trois choses
qui, ensemble, ferment la porte :

1. sa note méthodologique (p. xii) pose que « L'exportation regroupe
   l'exportation simple et la réexportation » — le total publié de
   258 434,7 millions de FCFA **contient** donc les réexportations ;
2. ses 89 tableaux portent tous sur l'exportation *totale* ; les deux flux ne
   se distinguent qu'au Tableau 83, par régime douanier, **jamais par produit
   ni par client** ;
3. et ce Tableau 83 **ne se réconcilie pas** avec le total publié :
   311 490,1 pour les régimes 1xxx + 3xxx contre 258 434,7, soit 53 055,4
   d'écart. Recherche exhaustive : aucun sous-ensemble des régimes de
   réexportation ne reproduit le total sur les cinq trimestres du tableau.

Recomposer un « export domestique togolais » aurait donc été une agrégation
maison que la source elle-même contredit. Elle n'est pas faite.

**Ce qui est servi à la place**, et qui est vérifiable :

- `export_flow_caveat` — l'avertissement daté avec la définition citée. Il
  interdit de lire un chiffre d'export togolais comme de la production
  domestique — **y compris ceux d'OEC et de Comtrade, qui héritent de la même
  définition**. C'est un fait sourcé, pas un chiffre reconstitué.
- `free_zone_regimes` — quatre lignes du Tableau 83 reprises verbatim. Elles
  disent l'essentiel sur l'origine : la zone franche industrielle **reçoit**
  100 527,6 et **expédie** 84 248,9 millions de FCFA. Une zone qui importe
  plus qu'elle n'exporte en valeur transforme des intrants étrangers ; ses
  sorties n'établissent pas à elles seules l'origine togolaise.

Chaque valeur est vérifiée caractère par caractère contre le texte du PDF. Un
test interdit qu'un pays porte à la fois l'avertissement et une ventilation :
l'un des deux serait faux. Détail et empreintes :
`docs/data-sources/TGO_STATS_REGISTER.md`.

> **Une piste ouverte, non vérifiée.** Le docstring de
> `national_official_stats.py` affirme qu'« aucune source internationale ne
> publie cette ventilation ». C'est probablement trop fort : UN Comtrade porte
> des codes de flux `DX` / `RX` pour les déclarants qui les soumettent. Le
> dépôt a bien `comtrade_service.py`, mais en repli **opt-in à clé**, et
> aucune clé n'est configurée — impossible de contrôler ici quels pays
> africains soumettent réellement `RX`. Si la piste tient, elle est plus
> rentable que la collecte manuelle pays par pays. **Elle demande une clé
> Comtrade pour être tranchée, et n'a donc pas été inscrite comme un fait.**

**2.4 — La règle qui ne se négocie pas. ✅ livré et testé.**

Un bloc dépourvu d'éditeur, de publication, d'URL, d'année de données ou de
devise est **refusé au chargement** plutôt que servi à moitié
(`_REQUIRED_SOURCE_FIELDS`). Un chiffre invérifiable vaut moins qu'un chiffre
absent : il inspire confiance sans la mériter. Un test paramétré retire chacun
des cinq champs et vérifie le refus ; un autre exige qu'un pays enregistré ait
son document de registre.

### Phase 3 — Élargir le pont Production ↔ Opportunités

**3.1 — Le pont élargi par une correspondance publiée. ✅ livré.**

La chaîne retenue est sourcée de bout en bout, en deux maillons publiés :
**item FAOSTAT → CPC v2.1** (membre `*_ItemCodes.csv` du bulk FAO) puis
**CPC v2.1 → SH 2017** (table officielle UNSD `CPC21-HS2017.csv`). Aucune
attribution au jugé : rattacher une production au mauvais produit échangé
tromperait le module plus sûrement qu'une absence.

| Mesure | Avant | Après |
|---|---:|---:|
| Entrées du pont SH | 232 | **270** |
| Produits suivis (`list_tracked_products`) | 114 | **137** |
| Commodités agricoles dans la donnée | 69 | **92** |
| Lignes `agri_faostat` | 10 138 | **12 955** |

232 des 233 items non agrégés se résolvent vers un code SH, atteignant 294
codes SH6 sur 99 positions SH4.

**Le filtre d'atteignabilité, et pourquoi il fallait l'inventer.** Un item
dont tous les codes SH sont déjà pris ou contestés n'est atteignable par
aucun code : l'ingérer casserait l'invariant du dépôt. Le générateur calcule
donc l'atteignabilité par item et exporte l'ensemble des commodités
joignables ; l'ingestion s'en sert comme filtre. **L'invariant est tenu par
construction, plus par vigilance.**

**Ce qui reste hors de portée, et pourquoi.** 138 commodités sont écartées.
La cause n'est pas une lacune de la correspondance mais une propriété des
nomenclatures : **un code SH recouvre parfois plusieurs commodités FAOSTAT**.
Le SH 0201 « viande de bovins » vaut pour les bovins *et* les buffles, le
SH 0205 pour les chevaux *et* les ânes. Le pont n'associant qu'un libellé par
préfixe, trancher reviendrait à attribuer une production au mauvais produit.
Elles attendent que le pont sache exprimer une relation un-à-plusieurs.

> **Deux critères corrigés.** « ≥ 400 codes SH » confondait deux grandeurs :
> `list_tracked_products()` compte des **produits**, pas des codes SH. Les
> deux sont désormais suivis séparément. Et « ≥ 80 en manufacturing » se
> heurte au même mur qu'en phase 1 : le nombre de produits manufacturiers
> suivis est borné par les divisions ISIC présentes dans la donnée, donc par
> INDSTAT, donc par le 403. Il reste à 15.

*Vérification tenue* : invariant `test_no_production_commodity_left_without_hs_mapping`
vert, aucune résolution existante modifiée (extension purement additive),
269 tests du périmètre.

**3.2 — Le chaînage existe à l'écran. ✅ livré.**

Nouveau sous-onglet **Débouchés** dans Production : le pays choisi, sa
production réelle ligne à ligne avec son code SH, et un bouton par produit qui
ouvre la recherche de marchés — sans ressaisie. Un composant nouveau, aucun
des quatre sous-onglets existants touché.

**Le piège évité.** Le canal `sessionStorage` existait déjà, mais il ouvrait
systématiquement l'écran du *besoin national* — la perspective **importateur**
(« ce pays a-t-il besoin de ceci ? »). Or le chaînage depuis Production pose
la question inverse : « ce pays produit ceci, où le vendre ? ». Le handoff
porte donc désormais une **intention** ; `market` ouvre la recherche de
marchés, et l'absence d'intention conserve le comportement historique du
module Statistiques, inchangé.

**Le rang n'est jamais montré seul.** « 1ᵉʳ producteur » ne veut rien dire
quand trois pays sont couverts ; « 1ᵉʳ sur 3 pays couverts » se juge. Le
dénominateur accompagne donc chaque rang, et les réserves que le serveur
attache à une commodité sont rendues telles quelles — c'est le même garde-fou
que celui posé côté serveur, tenu jusqu'à l'écran.

*Vérification tenue* : 14 tests front (8 sur l'écran, 6 sur l'aiguillage du
handoff) ; suite front passée de 261 à 275 tests ; `yarn build` vert.

**3.3 — Un repli non-IA. ✅ livré (onglet principal).**

L'audit annonçait cinq sous-onglets morts sans clé. **Le compte exact est
quatre** : « Vue d'ensemble » passe par `real_summary_service` et survit.
Correction faite.

L'ancrage factuel est calculé **avant** tout appel au modèle et n'en dépend
pas. Sans clé, `analyze_trade_opportunities` sert désormais ces données —
production réelle du pays, flux commerciaux observés — au lieu d'une erreur
nue, avec un état `degraded` annoncé et le champ `error` historique conservé
pour les consommateurs qui le testent. Mesuré sur le Kenya : 2 517 caractères
d'ancrage, 20 produits avec tonnages et rangs continentaux.

Le repli s'appelle aussi seul (`factual_opportunities`), ce qui le rend utile
au-delà de l'absence de clé : quota épuisé, fournisseur indisponible.

*Vérification tenue* : 7 tests ; l'état dégradé est annoncé, jamais déguisé en
analyse complète qui n'aurait rien trouvé.

*Correction (vérifiée le 2026-09-21)* : cette phrase était fausse pour deux
des trois. **Par produit** (`real_product_service`) et **Comparaison**
(`real_comparison_service`) ne passent pas par le modèle du tout — leurs
chiffres viennent d'IMF, de la Banque mondiale, du PNUD et de l'OEC, et ces
onglets fonctionnent sans clé.

Le seul des trois qui dépende du modèle est **Chaînes de valeur**
(`get_value_chains_analysis`).

**3.3 (suite) — le repli sourcé des Chaînes de valeur. ✅ livré.** L'onglet
servait un jeu ÉCRIT EN DUR dont les valeurs par maillon n'avaient aucune
source. `factual_value_chains()` le remplace par des producteurs réels :
**6 chaînes, 13 commodités, 48 producteurs**, tirés de FAOSTAT / USGS / UNIDO
avant tout appel au modèle, donc à coût nul.

Ce que ce repli **ne fabrique pas**, et c'est le point :

- les **étapes** (`stages`) restent VIDES. Découper une filière en maillons et
  leur affecter des pays est une analyse, pas une mesure : aucune de nos
  sources ne la porte ;
- les **potentiels** (`intra_african_potential_musd`, `global_exports_musd`)
  sont absents pour la même raison.

Ce qui se perd est le récit ; ce qui reste est mesuré. L'onglet a désormais
trois états distincts à l'écran — analyse complète, repli factuel annoncé,
valeurs de référence datées (§5.1) — et 9 tests les tiennent.

### Phase 4 — Harmoniser la forme

| # | Action | État | Vérification |
|---|---|---|---|
| 4.1a | Constante `TABS` d'Opportunités → i18n | ✅ | deux listes parallèles supprimées ; libellés servis par `opportunities.tabs.*` |
| 4.1b | Parité des locales sous test | ✅ | une clé traduite d'un seul côté fait échouer la suite, au lieu d'afficher son nom à l'écran |
| 4.1c | Les **427 libellés en dur** restants → i18n | ✅ | 0 dictionnaire de langue, 0 ternaire de libellé ; 425 clés sous `opportunities`, chacune sous test |
| 4.2 | Ajouter `ar` et `pt` (langues de travail ZLECAf) | ⏸ **en suspens** | les deux locales se chargent ; RTL vérifié pour l'arabe — reste à faire TRADUIRE les 843 clés, voir ci-dessous |
| 4.3 | Couleurs sémantiques → jetons de thème | ✅ | 40 teintes converties ; 0 couleur sémantique en dur ; garde-fou `semanticColors.test.js`. La conversion de la MISE EN PAGE reste ouverte, voir ci-dessous |
| 4.4 | Tests front sur les deux modules | ✅ | les 9 sous-onglets d'Opportunités et les 5 de Production ont rendu + état d'absence ; 313 tests front (+30) |

**Le décompte de 4.1c annoncé ici était faux, et l'erreur méritait mieux
qu'une correction discrète.** Le plan comptait 173 ternaires dans 8 fichiers.
Il y en avait 200, dans 10. Surtout, il ne comptait qu'une famille sur deux.

| Famille | Annoncé | Réel |
|---|---:|---:|
| Ternaires `lang === 'fr' ? 'X' : 'Y'` | 173 | **200** |
| Dictionnaires `{ fr: {…}, en: {…} }` | *non vus* | **227** |
| **Total** | **173** | **427** |

Les dictionnaires vivaient dans 17 constantes écrites à la main, dont deux
fichiers entiers — `StrategicFlows.jsx` (34 libellés) et
`TradeSankeyDiagram.jsx` (13) — que le décompte ignorait **parce qu'ils
n'avaient aucun ternaire**. Le critère annoncé, « 0 ternaire résiduel »,
aurait donc été atteint en laissant 227 libellés en dur, et 4.2 exactement
aussi bloquée qu'avant : ajouter l'arabe aurait demandé un troisième bloc
dans chacun des 17 dictionnaires.

C'est le défaut typique d'un critère qui mesure le geste plutôt que le but.
Le but de 4.1c n'est pas de supprimer une tournure de code, c'est de rendre
4.2 possible. Le critère a été réécrit en conséquence.

**Ce qui a été fait**, en deux commits séparés pour rester relisibles :
les 200 ternaires, puis les 227 libellés de dictionnaire. Les 810 valeurs
servies (405 × 2 langues) ont été confrontées une à une au code d'origine.

**Ce qui reste en dur, délibérément :**

- **4 ternaires de code de langue** — une locale de formatage
  (`fr-FR`/`en-US`), deux arguments de `getAllCountries`, un paramètre
  `lang` de requête. Ce ne sont pas des libellés ; les traduire produirait
  un code traduit. Ils devront être **dérivés d'i18n** au moment de 4.2,
  puisqu'un choix binaire fr/en devient faux à quatre langues.
- **`difficultyLabelEn`** (SubstitutionAnalysis) traduisait les libellés
  **français que renvoyait le backend** — « Facile » → « Easy ». Ce n'était
  pas un dictionnaire de langue mais le contournement d'un défaut d'API : le
  serveur émettait du texte destiné à l'affichage au lieu d'un code stable.
  L'externaliser en i18n aurait figé le contournement.
  **✅ Corrigé à la source** : `_assess_difficulty` rend un code
  (`easy`, `moderate`, `difficult`, `very_difficult`), la répartition est
  clée dessus, et l'écran choisit les mots. `difficulty` reste servi en
  français, **déprécié**, pour ne casser aucun client externe ; le retirer
  est un geste séparé. Le défaut d'origine méritait d'être nommé : les
  tables du front étaient clés en anglais, rien ne correspondait, et toutes
  les cartes s'affichaient « Difficile » en ambre quel que soit le niveau
  réel. Un texte d'affichage est un mauvais identifiant.

**Ce que 4.2 doit encore faire**, maintenant que les deux modules sont
débloqués : **843 clés** existent en français et en anglais, sous test de
parité. Ajouter `ar` et `pt` demande trois choses de nature différente :

1. **La traduction elle-même — 1 686 chaînes, et ce n'est pas un travail de
   machine.** Le vocabulaire est celui de la politique commerciale (règles
   d'origine, valeur ajoutée manufacturière, démantèlement tarifaire), où un
   terme mal rendu change le sens d'une recommandation. Une traduction
   automatique livrée comme locale officielle serait une fabrication de plus,
   de la même famille que 5.1 : du contenu présenté comme utilisable sans que
   personne l'ait validé. **C'est la seule partie de tout ce plan qui demande
   une compétence humaine que l'outillage ne remplace pas.**
2. **Dériver d'i18n les 5 derniers codes de langue** (une locale de formatage
   dans chaque module, deux arguments de `getAllCountries`, un paramètre
   `lang` de requête). Un choix binaire fr/en devient faux à quatre langues.
3. **Le RTL de l'arabe** : `dir="rtl"`, et la relecture des mises en page qui
   supposent un sens de lecture.

---

### Phase 5 — Trois constats faits en écrivant les tests de 4.4

Ces trois points ne figuraient pas à l'audit initial. Ils sont sortis de
l'écriture des tests, ce qui est leur intérêt : aucun ne se voit en lisant le
code, tous se voient en essayant de décrire à un test ce que l'écran affiche.

| # | Action | État | Vérification |
|---|---|---|---|
| 5.1 | Valeurs servies sans source en repli | ✅ | valeurs **conservées** par décision, mais un écran de repli s'intercale, les qualifie de « valeurs de référence » et les date |
| 5.2 | Rendre visibles les états d'erreur déclarés et jamais affichés | ✅ | `ProductAnalysisView` affiche son erreur ; les deux autres annoncent leur repli (5.1) |
| 5.3 | Les libellés en dur du module **Production** → i18n | ✅ | 0 dictionnaire de langue ; 199 libellés migrés (154 de dictionnaire + 45 ternaires) ; 843 clés au total |

#### 4.3 — ce n'était pas de la cosmétique, et le critère le masquait

Le plan classait cette phase comme la seule « à n'améliorer aucune substance ».
C'est faux, et la mesure le montre. Le critère — « ≤ 50 `style={{}}` restants »
— comptait des blocs, donc il ne pouvait pas voir le vrai problème.

**Le thème sombre est celui par défaut** (`localStorage.getItem('zlecaf_theme')
|| 'dark'`). Or les couleurs écrites en dur avaient été choisies sur fond
clair. Contraste mesuré sur la carte réelle de chaque thème :

| Couleur | Emploi | Sombre (défaut) | Clair |
|---|---|---:|---:|
| `#92400e` | avertissement | **2,30:1** ✗ | 7,09:1 |
| `#1a7f37` | statistique officielle | **3,21:1** ✗ | 5,08:1 |
| `#9a6700` | estimation dérivée | **3,35:1** ✗ | 4,87:1 |
| `#0969da` | lien | **3,14:1** ✗ | 5,19:1 |
| `#4f8ef7` | accent | 5,08:1 | **3,21:1** ✗ |

**30 occurrences de texte sous le seuil AA (4,5:1) dans le thème par défaut.**
Et le motif est instructif : ce qui passe dans un thème échoue dans l'autre.
Une valeur fixe ne peut pas satisfaire deux fonds — c'est précisément ce que
les jetons résolvent, puisqu'ils changent avec le thème.

**Fait : 40 teintes sémantiques converties** (`--danger`, `--success`,
`--gold`, `--info`), plus deux dégradés. Il ne reste aucune couleur sémantique
en dur dans le module, et `semanticColors.test.js` refuse leur retour.

**Ce qui a été délibérément laissé, parce que le convertir serait une faute.**
Toute couleur en dur n'est pas fautive. Le tri a séparé deux problèmes que
« 428 styles inline » confondait :

- les **palettes catégorielles** (`COLORS`, `DEFAULT_VALUE_CHAINS[].color`)
  dont le rôle est de distinguer des séries entre elles. Mapper `#dc2626`
  (cacao) sur `--danger` ferait dire « erreur » à « cacao », et fondrait deux
  chaînes dans la même teinte. Elles posent un vrai problème — quatre palettes
  différentes coexistent dans le module, aucune n'est adaptée au thème ni
  vérifiée pour le daltonisme — mais c'est un **autre** chantier ;
- le **chrome recharts** (axes, grilles, info-bulles) : la bibliothèque ne lit
  pas les variables CSS, il faut lui passer des valeurs résolues ;
- les **replis de jeton** `var(--afcfta-muted, #667)`, déjà corrects ;
- le **blanc sur aplat coloré**, juste dans les deux thèmes.

**Deux points qui appellent encore votre arbitrage.**

1. **Les jetons eux-mêmes ne sont pas tous AA.** Après conversion, `--red`
   tombe à 2,94:1 en sombre, `--green` à 3,05:1, `--gold` à 3,72:1 en clair.
   La migration améliore beaucoup — le pire cas passe de 2,30:1 à 3,86:1 — mais
   n'atteint pas le seuil partout. Ajuster ces valeurs est une décision de
   charte graphique, pas une correction technique.
2. **Le violet n'a pas de jeton.** `#9333ea` (2 emplois dans StrategicFlows)
   n'a aucun équivalent. Il est resté en dur faute de quoi le remplacer.

**Ce qui reste hors périmètre couleur.** Les ~1 300 déclarations de mise en
page (`fontSize` 190, `display` 118, `gap` 102) : là, « passer aux jetons »
signifie passer à Tailwind, c'est-à-dire réécrire le style du module. Diff de
plusieurs milliers de lignes dont le seul juge est l'œil, qu'aucun test ne
valide. Non engagé.

#### 5.1 — Valeurs de repli : conservées, mais annoncées et datées

**Constat.** Quand l'appel n'aboutit pas, `OpportunitySummary` sert des valeurs
écrites en dur — 5 387 opportunités, 1 650 Md$ de commerce total, 186 Md$ de
commerce intra-africain, « +12,3 % » de croissance, et un tableau des huit
premiers produits dont les comptes et montants sont inventés. `ValueChains`
fait de même avec `DEFAULT_VALUE_CHAINS`.

**Le vrai défaut était plus précis que « des chiffres en dur ».** Les deux
branches rendaient le **même écran**, avec les mêmes composants. Un drapeau les
distinguait bien (`isAiGenerated`), mais il servait à *ajouter* un badge vert
quand tout allait bien. En cas d'échec, le badge disparaissait — et l'absence
d'un badge ne se remarque pas. La substitution était donc invisible.

**Décision retenue : conserver les valeurs, mais faire s'intercaler un écran.**
La propriétaire de la plateforme assume les valeurs de repli — il lui revient
de provisionner l'API, de sorte que ce chemin ne serve pratiquement jamais.
Ce qui change est qu'elles ne se substituent plus en silence :

| | Écran servi | Signe distinctif |
|---|---|---|
| Le service répond | données réelles | badge « Données enrichies par IA » |
| Le service ne répond pas | valeurs de référence | **bandeau « Valeurs de référence », daté** |

Le ton retenu est délibérément mesuré — « valeurs de référence », non « panne »
— pour ne pas alarmer un visiteur là où il n'y a qu'une donnée non actualisée.
Et comme ce chemin ne doit pas servir, le bandeau ne coûte rien à l'usage
courant : il ne parle que quand on voudrait être prévenu.

**Sur la date, un point de méthode.** Ces valeurs n'ont **aucun millésime
documenté** : rien dans le dépôt n'atteste l'année qu'elles décrivent. La seule
date vérifiable est celle de leur dernière révision dans le code — le
2026-09-09, commit `3aa882c`. C'est donc elle qui est affichée, et le libellé
dit « révisées le », non « chiffres de ». Écrire « données 2024 » aurait été
inventer une provenance, c'est-à-dire commettre à l'échelle de l'étiquette la
fabrication que ce bandeau sert précisément à éviter. **Si un chiffre change,
la clé `referenceDate` doit changer avec lui** — c'est écrit en commentaire aux
deux endroits.

**À savoir avant d'y toucher.** La condition d'entrée dans le repli n'est pas
« pas de clé d'API » mais `aiSummary.data && aiSummary.data.overview`. Elle
couvre donc aussi les échecs passagers — délai dépassé, 5xx, limite de débit,
quota — et le cas d'une réponse 200 sans `overview`. `ValueChains` a la même
forme : un `value_chains` vide renvoyé par une API en bonne santé mène au jeu
de référence. Le bandeau s'affiche dans tous ces cas, ce qui est le
comportement voulu.

#### 5.2 — Erreurs déclarées et jamais affichées

`ProductAnalysisView` alimentait un état `error` qu'il ne rendait nulle part :
l'échec partait au `console.error` et l'écran retombait sur « aucune donnée »,
qui affirme tout autre chose. **Corrigé** — l'erreur s'affiche, l'état vide ne
s'affiche plus en même temps, et le message passe par i18n.

`ValueChains` et `OpportunitySummary` gardent leur état `error` non rendu, mais
le point est **traité autrement** : chez eux l'échec n'aboutit pas à un écran
muet, il aboutit au bandeau de valeurs de référence (5.1). Afficher en plus une
erreur à côté de chiffres qualifiés serait redondant.

#### 5.3 — Production porte le même obstacle qu'Opportunités vient de lever

La phase 4.1c a sorti 427 libellés du dur côté Opportunités. Le module
**Production en compte 154**, dans 8 dictionnaires `{ fr, en }` répartis sur
5 fichiers. L'audit initial ne l'avait pas vu parce qu'il avait mesuré les
clés i18n **présentes** dans Production (32) sans mesurer les libellés
**absents** — un comptage qui ne peut que rassurer.

Tant qu'ils y sont, l'arabe et le portugais (4.2) ne couvriraient qu'un module
sur deux.

**Fait.** Le décompte s'est encore révélé court : 154 libellés de dictionnaire,
mais aussi **45 ternaires** que la première mesure n'avait pas cherchés dans ce
module. Le garde-fou `opportunitiesI18n.test.js` ne lisait qu'un répertoire ; il
lit désormais les deux, et c'est son extension qui a trouvé les 45. Un
garde-fou partiel rassure à proportion exacte de ce qu'il ignore.

**Une lacune de couverture, découverte au passage.** Trois composants
(`IsicDivisionCard`, `Isic4DetailPanel`, `EstimatedDetail`) appelaient `t()`
sans l'avoir en portée et auraient planté à l'affichage. Aucun des 313 tests
ne les atteint : ils ne se rendent que dans le détail ISIC4 **déplié**. La
phase 4.4 couvre les onglets, pas les vues au clic — à compléter.

---

## 5. Ordre d'exécution recommandé

```
Phase 0  ──► gain immédiat, zéro nouvelle source, se répercute seul
             sur Opportunités via l'invalidation de cache indexée (pdv)
   │
   ├─► Phase 1  ──► referme manufacturing et mining
   │
   ├─► Phase 3  ──► exploite ce que 0 et 1 ont produit
   │                (inutile de l'entamer avant : le plafond est la donnée)
   │
   └─► Phase 2  ──► chantier long, démarrable en parallèle dès la phase 0,
                    à mener pays par pays, palier A d'abord
```

**Phase 4** est indépendante et peut s'insérer n'importe où — c'est aussi la
seule qui n'améliore pas la substance. À ne pas faire passer devant les
phases 0 et 1.

Le piège à éviter : commencer par la phase 2, qui est la plus visible et la plus
gratifiante, alors que la phase 0 rend plus de valeur en quelques jours que la
phase 2 en un mois.

---

## 6. Critères de réussite globaux

Les lignes marquées ✅ ont été livrées par le premier lot d'implémentation
(phase 0) ; les valeurs « aujourd'hui » des autres restent celles de l'audit.

| Indicateur | Audit | Aujourd'hui | Cible |
|---|---:|---:|---:|
| ✅ Lignes macro | 514 | **5 070** | ≥ 4 500 |
| ✅ Années couvertes en macro | 2 | **10** | ≥ 8 |
| ✅ Dimensions macro en valeur absolue | 0 | **5** | 5 |
| ✅ `area_ha` / `yield_kg_ha` remplis (cultures) | 0 % | **96 %** | ≥ 95 % |
| ✅ `rank_africa` rempli | 0 % | **100 %** | 100 % |
| ✅ Le passage mensuel préserve la surcouche | non | **oui** | oui |
| ✅ Pays sans donnée minière **ni explication** | 13 | **0** | 0 |
| ✅ Indicateurs manufacturiers mesurés (hors estimation) | 0 | **3** | ≥ 3 |
| ✅ Pays avec manufacturier mesuré | 0 | **53** | ≥ 45 |
| ✅ Lignes de production hors agriculture et macro | 622 | **1 630** | ≥ 2 000 |
| ✅ Commodités agricoles importées | 69 | **92** | ≥ 90 des 233 atteignables |
| ✅ Entrées du pont SH | 232 | **293** | ≥ 260 |
| ✅ Produits suivis (`list_tracked_products`) | 114 | **161** | ≥ 130 |
| ✅ Sous-onglets Opportunités servant des faits sans clé IA | 0 / 4 | **1 / 4** | 4 / 4 |
| ✅ Parcours production → débouché à l'écran | non | **oui** | oui |
| ✅ Tests front | 261 | **324** | — |
| ✅ Commodités minières ingérées | 30 | **54** | ≥ 44 |
| Produits manufacturiers suivis | 15 | 15 | borné par INDSTAT (403) |
| Pays avec détail ISIC4 réel | 20 / 54 | 20 / 54 | ≥ 30 / 54 |
| ✅ Registre NSO piloté par la donnée | non | **oui** | oui |
| ✅ Pays classés par voie d'accès (généré) | 0 | **54** | 54 |
| Pays en collecte directe (palier A) | 1 | **2** | ≥ 10 |
| Pays atteints par republication (palier B) | 0 | **46** | ≥ 45 |
| Sous-onglets Opportunités vivants sans clé IA | 5 / 9 | **6 / 9** | 9 / 9 |
| ✅ Clés i18n Opportunités | 0 | **436** | ≥ 150 |

Deux cibles du tableau d'origine ont été retirées parce qu'elles reposaient sur
une hypothèse fausse : « pays en `is_estimation` seule < 15 » (aucune source
libre ne publie la ventilation par division ISIC, cf. phase 1.1) et « chaque
pays déclaré non extractif » (une telle déclaration demanderait une source
qui l'affirme, cf. phase 1.2).

---

## Annexe — reproduire les mesures

```bash
# Couverture par dimension et par pays
python3 - <<'PY'
import json, collections
d = json.load(open('data/json/production_africaine.json'))
for dim in ['value_added_macro','agri_faostat','manufacturing_unido','mining_usgs']:
    rows = d[dim]
    print(dim, len(rows), 'lignes,',
          len({r['country_iso3'] for r in rows}), 'pays,',
          sorted({r['year'] for r in rows}))
PY

# Pays couverts par le détail ISIC4 réel
python3 -c "
import gzip, csv
with gzip.open('backend/data/unido/unido_idsb_indstat_isic4_2018plus.csv.gz','rt') as f:
    print(sorted({r['country_iso3'] for r in csv.DictReader(f)}))"

# Plafond du pont Production <-> Opportunités
cd backend && python3 -c "
import sys; sys.path.insert(0,'.')
from services.production_capacity_service import list_tracked_products
import collections
t = list_tracked_products()
print(len(t), collections.Counter(x['dataset'] for x in t))"

# Dette de forme
grep -c "language === 'fr'" frontend/src/components/opportunities/*.jsx
grep -o 'style={{' frontend/src/components/opportunities/*.jsx | wc -l

# Ce que le bulk FAOSTAT contient, face a ce qui est importe
curl -sO https://bulks-faostat.fao.org/production/Production_Crops_Livestock_E_Africa.zip
python3 - <<'PY'
import zipfile, csv, io
z = zipfile.ZipFile('Production_Crops_Livestock_E_Africa.zip')
with z.open('Production_Crops_Livestock_E_Africa.csv') as f:
    rows = list(csv.DictReader(io.TextIOWrapper(f, encoding='utf-8-sig')))
def pts(code):
    return sum(1 for r in rows if r['Element Code'] == code
               for y in range(2019, 2025) if r.get(f'Y{y}') not in (None, '', '0'))
for code, lab in [('5510', 'Production'), ('5312', 'Area harvested'), ('5412', 'Yield')]:
    print(lab, pts(code))
PY
```
