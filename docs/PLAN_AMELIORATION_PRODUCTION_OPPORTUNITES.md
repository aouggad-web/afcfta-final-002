# Production & Opportunités — analyse approfondie et plan d'amélioration

Date de l'audit : 2026-09-21. Périmètre : les deux modules `production` et
`opportunities` (front-end, back-end, données, chaîne d'ingestion).

Toutes les valeurs de cette page ont été **mesurées** sur le dépôt et sur les
sources en ligne le jour de l'audit, pas estimées. Les commandes de mesure sont
rappelées en annexe pour que chaque chiffre soit reproductible.

> **État d'avancement.** Le constat (§ 1 et 2) décrit le dépôt tel qu'il était
> à l'audit. Les **phases 0 et 1 ont depuis été implémentées** : macro en
> valeurs absolues sur dix ans, surfaces et rendements FAOSTAT, rang
> continental, correction d'un passage mensuel qui faisait régresser le
> fichier, puis une dimension manufacturière mesurée contournant le 403
> d'UNIDO et une explication sourcée pour les treize pays sans donnée minière.
> Le tableau du § 6 marque d'un ✅ ce qui est livré. Deux actions du plan se
> sont révélées mal formulées à l'usage ; les corrections sont écrites en
> phase 0 et en phase 1, elles ne sont pas masquées.

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

**2.1 — Passer d'un dictionnaire en dur à un registre piloté par la donnée.**
`national_official_stats.py` devient un lecteur ; la donnée part dans
`data/national_stats/<ISO3>.json`, documentée par
`docs/data-sources/<ISO3>_STATS_REGISTER.md` — en réutilisant **exactement** la
discipline des registres juridiques existants : éditeur, publication, URL, année
des données, monnaie, SHA-256, `verification_status`.

*Vérification* : Maurice est migré sans changement de comportement (les tests de
`test_claude_opportunities_grounding.py` passent inchangés) ; ajouter un pays ne
demande plus de toucher au Python.

**2.2 — Classer les 54 pays par ce qu'ils publient réellement.** Une collecte
NSO échoue quand elle traite 54 offices comme un seul. Trois régimes :

- **Palier A — portail ou API exploitable.** Confirmés joignables : ZAF, EGY,
  MAR, TUN, TZA, MUS. À retester sur runner : KEN, RWA, UGA, GHA, NGA.
  → connecteur automatisable, sur le modèle des crawlers tarifaires existants
  (`backend/services/crawlers/`).
- **Palier B — bulletins PDF/Excel réguliers.** La plupart des offices
  francophones (ANSD Sénégal, INS Côte d'Ivoire, INS Cameroun…).
  → extraction semi-automatique + revue humaine, archivage horodaté et haché.
- **Palier C — rien d'exploitable.** → on reste sur les sources internationales,
  **et on l'affiche**.

*Vérification* : un tableau de couverture par pays, généré et non rédigé à la
main, indiquant palier, dernière collecte et fraîcheur.

**2.3 — Viser d'abord ce que seuls les NSO savent dire.** Ne pas recollecter ce
que la Banque mondiale donne déjà. Trois priorités :

1. **Exportations domestiques vs réexportations** — la distinction qui commande
   les règles d'origine ZLECAf. Introuvable ailleurs. C'est déjà la raison d'être
   du bloc Maurice ; la généraliser est **l'apport de données le plus rentable de
   tout ce plan** pour le module Opportunités.
2. **Indices et recensements de production industrielle** — la seule voie autour
   du mur UNIDO.
3. **Production infranationale** — où se trouve la capacité dans le pays, donnée
   qu'aucune source internationale ne descend.

**2.4 — La règle qui ne se négocie pas.** Valeurs reprises telles que publiées,
dans la monnaie de publication, source et année attachées, aucune conversion
maison, aucun trou comblé. Elle est déjà écrite en tête de
`national_official_stats.py` ; elle doit tenir à 54 pays comme elle tient à un.

*Vérification* : un test refuse toute entrée NSO sans `publisher`, `url`,
`data_year`, `currency` et empreinte.

### Phase 3 — Élargir le pont Production ↔ Opportunités

**3.1 — Casser le plafond des 114 codes SH, et élargir l'ingestion avec lui.**
C'est ici que revient l'élargissement des commodités FAOSTAT, parce que
l'invariant du dépôt interdit de le faire seul (voir la correction en phase 0).
Le pont et l'ingestion avancent du même pas. Trois gisements :

- **FAOSTAT** : le bulk contient 254 items, dont 233 hors agrégats, contre 69
  commodités mappées aujourd'hui. Chaque item ajouté doit arriver avec son code
  SH, sa classification CPC (cultures / élevage / transformé) et l'exclusion des
  21 agrégats ;
- descendre le mapping au SH6 là où la commodité le permet ;
- brancher la correspondance standard **ISIC ↔ chapitres SH** pour que le
  manufacturing dépasse ses 15 codes.

*Point de décision* : la table de correspondance item FAOSTAT → code SH doit
venir d'une source publiée (correspondance CPC↔SH de l'UNSD, ou table FAO), pas
d'une attribution au jugé. Une correspondance fausse est pire qu'une absence :
elle rattache une production réelle au mauvais produit échangé.

*Vérification* : `list_tracked_products()` ≥ 400 codes, dont ≥ 80 en
manufacturing ; `agri_faostat` ≳ 24 000 lignes ; l'invariant
`test_no_production_commodity_left_without_hs_mapping` reste vert ;
`production_products` relevé avant/après par pays dans les stats d'ancrage.

**3.2 — Faire exister le chaînage à l'écran.** Un parcours *pays → ce qu'il
produit → où le vendre sous la ZLECAf → à quel tarif → sous quelle règle
d'origine*. `get_country_profile()` et `get_continental_producers()` existent
déjà et ne sont appelés qu'une fois dans tout le front.

*Vérification* : depuis un pays choisi dans Production, on atteint une
opportunité chiffrée dans Opportunités sans ressaisir quoi que ce soit — le
mécanisme de handoff par `sessionStorage` existe déjà
(`zlecaf_opportunites_handoff`).

**3.3 — Un repli non-IA.** Les données d'ancrage sont calculées **avant** l'appel
au LLM. Sans clé, servir cet ancrage brut — classements, flux réels, tarifs —
plutôt qu'un message d'erreur. Le module perd sa narration, pas sa substance.

*Vérification* : avec `ANTHROPIC_API_KEY` vidée, les 9 sous-onglets affichent du
contenu ; aucun ne renvoie d'erreur nue.

### Phase 4 — Harmoniser la forme

| # | Action | Vérification |
|---|---|---|
| 4.1 | Migrer les 60 ternaires et la constante `TABS` d'Opportunités vers i18n | `opportunities.*` ≥ 150 clés ; 0 ternaire de langue résiduel |
| 4.2 | Ajouter `ar` et `pt` (langues de travail ZLECAf) | les deux locales se chargent ; RTL vérifié pour l'arabe |
| 4.3 | Réduire les 428 styles inline vers les jetons de design de Production | ≤ 50 `style={{}}` restants ; les deux modules partagent la même grammaire visuelle |
| 4.4 | Tests front sur les deux modules | ≥ 1 test de rendu et d'état d'erreur par sous-onglet (9 + 4) |

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
| ✅ Lignes de production hors agriculture et macro | 622 | **1 534** | ≥ 2 000 |
| Commodités agricoles importées | 69 / 254 | 69 / 254 | ≥ 200 / 254 |
| Codes SH reliés à la production | 114 | 114 | ≥ 400 |
| dont manufacturing | 15 | 15 | ≥ 80 |
| Commodités minières ingérées | 30 / 46 | 30 / 46 | ≥ 44 / 46 |
| Pays avec détail ISIC4 réel | 20 / 54 | 20 / 54 | ≥ 30 / 54 |
| Pays avec source NSO enregistrée | 1 | 1 | ≥ 15 (palier A + B) |
| Sous-onglets Opportunités vivants sans clé IA | 4 / 9 | 4 / 9 | 9 / 9 |
| Clés i18n Opportunités | 0 | 0 | ≥ 150 |

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
