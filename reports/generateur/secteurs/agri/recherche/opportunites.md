# Module « Opportunités » (SaaS ZLECAf) : données et idées pour le Rapport Agriculture & Agroalimentaire

Extraction faite hors ligne le 27/09/2026 sur le dépôt `/home/user/afcfta-final-002`. Aucun appel à une API externe, aucun fichier du dépôt modifié.
Convention : chaque chiffre est suivi de [fichier, source déclarée dans le fichier, année]. Les chemins sont relatifs à la racine du dépôt.

---

## (a) Ce que calcule le module

**Frontend** : `frontend/src/components/opportunities/OpportunitiesTab.jsx` regroupe 9 sous-onglets : Analyse IA, Flux stratégiques, Substitution, Simulateur ZLECAf, Comparateur bilatéral, Vue d'ensemble, Chaînes de valeur, Par produit, Comparaison pays. `SectoralAnalysis.jsx` est une carte appelée depuis les vues produit et flux.

| Sous-module | Endpoint | Service backend | Données | Nature |
|---|---|---|---|---|
| Substitution (import et export) | `/api/substitution/opportunities/{import,export}/{iso3}` (`backend/routes/substitution.py`) | `backend/services/real_substitution_service.py` | **API OEC en direct** (BACI/Comtrade, HS6, 2022 par défaut). Si l'API ne répond pas, repli sur des profils statiques `COUNTRY_SUBSTITUTION_PROFILES` (10 pays), marqués `is_estimation: True` | réel si OEC répond, sinon estimation |
| Coefficient de substituabilité | `/api/substitution/feasibility/{hs}` | `backend/services/substitution_feasibility_service.py` | table de coefficients par préfixe SH (hypothèses de modélisation assumées) | modélisé |
| Flux stratégiques | `/api/strategic/flows/{iso3}` | `backend/services/strategic_trade_service.py`, `industrial_intelligence_service.py` | flux OEC, puis enrichis : règles d'origine, écart tarifaire, projets structurants, logistique | mixte |
| Analyse sectorielle ISIC/IDSB | `/api/reports/sectoral-analysis` (`backend/routes/reports.py`) | `backend/services/isic_idsb_opportunity_service.py`, `backend/etl/isic4_idsb_data.py` | `backend/data/unido/unido_idsb_indstat_isic4_2018plus.csv.gz` (UNIDO IDSB + INDSTAT, 18 à 20 pays, 2018-2023) | réel |
| Capacité de production | `/api/production/capacity` | `backend/services/production_capacity_service.py` | `data/json/production_africaine.json` (FAOSTAT QCL, USGS, UNIDO, WDI) | réel, avec scénarios modélisés |
| Chaînes de valeur | `/api/ai/value-chains`, avec repli `DEFAULT_VALUE_CHAINS` dans `ValueChains.jsx` | services IA (Claude ou Gemini) | cache `backend/data/ai_cache/zlecaf_claude_value_chains_6c94bc8c2af1.json` | **généré par IA ou codé en dur** |
| Vue d'ensemble, par produit, comparaison, Analyse IA | `/api/ai/summary`, `/api/ai/product/{hs}`, `/api/ai/compare` | services IA | aucune donnée locale | généré par IA |
| Simulateur ZLECAf, comparateur bilatéral | `/api/dismantlement/impact/...`, `/api/bilateral-tariff/...` | `zlecaf_schedule_*.py`, `official_preferential_rates.py` | `backend/data/official_preferential/*.json.gz` (e-Tariff Book UA) et tarifs nationaux `backend/data/{ISO3}_tariffs.json` | réel (officiel) |
| Adaptateur logistique | interne au moteur de rapport | `backend/services/logistics_opportunity_adapter.py`, qui appelle `multimodal_freight_service` | `data/json/corridors_terrestres*.json`, ports, zones franches | coûts modélisés (`is_modeled`) |
| Adaptateur financier | interne | `backend/services/finance_opportunity_adapter.py` | modules bancaires, PAPSS, FX, `data/json/wb_reserves.json` (WDI) | réel pour le macro. **Les modules bancaires et PAPSS n'ont pas pu tourner ici** (`pydantic` absent) |
| Intelligence régionale | routes `regional_analytics`, `sadc_intelligence` | `regional_intelligence_service.py`, `north_africa_intelligence.py`, `sadc_intelligence_service.py` | notes et scores (1 à 10) écrits en dur, sans source | qualitatif |

**Formule de substitution** (`substitution_feasibility_service.realistic_substitution_potential`) :

> potentiel = min(importations hors Afrique × coefficient de substituabilité ; capacité africaine)

La capacité africaine est la somme des exportations mondiales des 5 premiers fournisseurs africains du même HS6, ou du HS4 à défaut.

Coefficients par chapitre :
- **0,9** pour les chapitres SH 01-12, 14, 15 et 17 (« produits agricoles et alimentaires homogènes » : décision prix + logistique).
- **0,75** pour les chapitres 13, 16, 18-24 (« agroalimentaire transformé »).
- Incohérence : le cacao en fèves (1801) tombe dans le chapitre 18, donc à 0,75 au lieu de 0,9.

**Flux stratégiques** :
- Potentiel = taille du marché importateur × taux de capture. La capture vaut min(coefficient ; 0,25), donc **25 % au plus** (`strategic_trade_service._markets_for_product`).
- L'avantage tarifaire est calculé comme « NPF proxy par chapitre − 0 % ». Ce NPF provient de `backend/routes/tariffs_calculation.get_chapter_rate`, une table « simplified » : ch. 01 = 5 %, 04 = 15 %, 17 = 15 %, 22 = 20 %… **Elle n'est pas officielle.**

**Scénarios de production** (`production_capacity_service._build_scenarios`) :
- On part du TCAC observé 2021-2024, borné à [0 ; 12 %].
- Le scénario « intégration ZLECAf » ajoute +3 points, le scénario « transformation locale » +6 points, à l'horizon 2030.
- Ces majorations sont **mécaniques, pas des prévisions**.

---

## (b) Chiffres agroalimentaires extraits (données locales uniquement)

### B1. Production agricole africaine, 2023 (somme des 54 pays présents dans le fichier)

[`data/json/production_africaine.json`, bloc `agri_faostat` : « FAO FAOSTAT (Production QCL) bulk Africa », 23 800 enregistrements, 2019-2024, 227 produits, `last_updated` 22/09/2026]

- 2023 sert d'année de référence : 2024 est incomplète (3 463 enregistrements contre environ 4 080 par an).
- Le total est la somme des pays, pas l'agrégat régional FAO.
- Unité : tonnes.

| Produit (FAOSTAT) | Afrique 2023 | Var. 2019→2023 | Top producteurs 2023 (part) |
|---|---|---|---|
| Cacao (fèves) | 3,34 Mt | −10,8 % | CIV 1,82 Mt (54 %), GHA 0,65 (20 %), NGA 0,35 (10 %), CMR 0,30 (9 %) |
| Café (vert) | 1,94 Mt | +7,1 % | ETH 0,56 (29 %), UGA 0,47 (24 %), CAF 0,32 (16 %, douteux, voir (d)), GIN 0,20 |
| Noix de cajou | 2,66 Mt | **+45,4 %** | CIV 1,23 (46 %), TZA 0,31 (12 %), BEN 0,20, GHA 0,20, MOZ 0,16, BFA 0,14 |
| Coton-graine | 4,53 Mt | −15,3 % | BFA 0,72 (16 %), BEN 0,60, MLI 0,58, CMR 0,51, EGY 0,32 |
| Sésame | 3,33 Mt | −27,2 % | SDN 0,60, NGA 0,45, ETH 0,45, TZA 0,27, BFA 0,25 |
| Karité (noix) | 0,88 Mt | −1,2 % | NGA 0,36 (41 %), MLI 0,22, BFA 0,14 |
| Arachide | 16,9 Mt | ≈0 % | NGA 4,3 (25 %), SEN 1,68, SDN 1,39, GIN 1,0 |
| Maïs | 99,4 Mt | +15,9 % | ZAF 16,4 (17 %), ETH 11,5, NGA 11,1, TZA 8,0, EGY 7,4 |
| Blé | 26,2 Mt | −1,9 % | EGY 9,07 (35 %), ETH 6,09, MAR 4,16, DZA 2,5, ZAF 2,05 |
| Riz (paddy) | 43,1 Mt | +18,9 % | NGA 8,9 (21 %), EGY 6,2, MDG 5,1, TZA 3,6, GIN 3,5, MLI 3,0 |
| Sorgho, mil | 26,0 et 12,9 Mt | −7,9 et −5,0 % | NGA, ETH, SDN (sorgho). NER 3,16, MLI 1,94 (mil) |
| Manioc | 219,9 Mt | +15,2 % | NGA 62,8 (29 %), COD 45,2, GHA 26,6 |
| Canne à sucre | 93,6 Mt | −5,4 % | ZAF 17,9, EGY 14,3, ZWE 6,5, UGA 6,2, KEN 5,6, SWZ 5,2 |
| Sucre brut centrifugé | 10,9 Mt | −3,4 % | EGY 2,85 (26 %), ZAF 2,08, SWZ 0,59, UGA 0,50, KEN 0,47, ZMB 0,47 |
| Palmier à huile (régimes) | 29,5 Mt | +14,7 % | NGA 13,0 (44 %), GHA 3,4, CMR 3,2, CIV 3,2, COD 2,2 |
| Soja | 7,46 Mt | **+84,8 %** | ZAF 2,77 (37 %), NGA 1,5, ZMB 0,76, BEN 0,52 |
| Tournesol | 2,79 Mt | +15,1 % | TZA 1,17, ZAF 0,72, UGA 0,47 |
| Thé | 3,74 Mt | +23,4 % | KEN 2,58 (69 %, feuille fraîche probable, voir (d)), UGA 0,39, MWI 0,25 |
| Avocat | 1,56 Mt | **+60,8 %** | KEN 0,60 (38 %), ETH 0,21, MAR 0,12 |
| Dattes | 4,23 Mt | +9,6 % | EGY 1,70 (40 %), DZA 1,32 (31 %), SDN 0,44, TUN 0,39 |
| Oranges, petits agrumes | 10,5 et 3,7 Mt | +4,5 et +4,5 % | EGY 3,47, ZAF 1,61, DZA 1,31. EGY 1,27, MAR 0,87, ZAF 0,72 |
| Huile d'olive | 0,47 Mt | −23,1 % | TUN 0,21 (45 %), MAR 0,12, DZA 0,08 |
| Lait de vache | 42,6 Mt | +8,7 % | KEN 4,71, EGY 4,45, TZA 4,06, UGA 3,85, ZAF 3,81, ETH 3,44 |
| Lait entier en poudre | 25 kt | — | ZAF 7,1 kt, RWA 6,4, ZWE 6,1 (seulement 5 pays) |
| Viande de poulet | 7,64 Mt | +14,6 % | EGY 2,18 (28 %), ZAF 1,86 (24 %), MAR 0,57, DZA 0,43, NGA 0,33 |
| Œufs de poule | 4,11 Mt | +8,4 % | NGA 0,67, EGY 0,66, ZAF 0,48 |
| Viande bovine | 7,03 Mt | +3,5 % | ZAF 1,03, ZWE 0,74, TZA 0,61, TCD 0,55 |
| Tomate, oignon | 25,4 et 16,2 Mt | +9,5 et +9,5 % | EGY 7,1 (tomate). EGY 3,4, NER 2,1 (oignon) |
| Vanille, clou de girofle | 3,5 et 43 kt | — | MDG 87 % (vanille), MDG 57 % (girofle) |
| Gingembre | 0,90 Mt | +16,3 % | NGA 0,78 (87 %) |

Séries pays tirées de la même source :
- Cacao CIV : 2,36 Mt (2022), puis 1,82 (2023), puis 1,89 (2024).
- Cacao GHA : 1,05 Mt (2021), puis 0,53 Mt (2024).
- Cajou CIV : 0,63 Mt (2019), puis 1,23 Mt (2023), puis 0,94 Mt (2024).

**Projections** [même fichier, bloc `agri_projections`, 60 enregistrements, attribués à « OECD-FAO Agricultural Outlook 2024-2033 »] :
- Céréales 2025 → 2030 : ETH 31 → 35 Mt, NGA 29 → 32, EGY 24 → 25,5, ZAF 17,5 → 18,5.
- Racines et tubercules : NGA 120 → 135 Mt.
- Sucre : EGY 2,6 → 2,8 Mt, ZAF 2,1 → 2,3.
- Viande : ZAF 3,4 → 3,7 Mt, EGY 2,1 → 2,3.
- **Valeurs toutes arrondies, à ne citer qu'avec prudence** (voir (d)).

### B2. Demande africaine d'importation par produit HS6, 2024

[`data/json/dza_commerce_baci.json`, `meta.source` = « CEPII BACI via l'API OEC », `nature` = officiel, généré le 23/09/2026]

- Champ : les 56 lignes HS6 agroalimentaires que l'Algérie exporte pour au moins 0,5 M USD. Ce n'est donc pas un inventaire exhaustif.
- `demande_afrique` = importations de tous les pays africains sauf l'Algérie, **toutes origines confondues** (intra-africaines comprises).

| HS6 | Produit | Import. Afrique 2024 | Premiers importateurs africains 2024 |
|---|---|---|---|
| 151190 | Huile de palme raffinée | **5,73 Md USD** | EGY 1 181 M, DJI 505 M, ZAF 492 M, TGO 355 M |
| 170199 | Sucre raffiné | **4,76 Md** | SDN 525 M, LBY 483 M, SOM 334 M, MRT 275 M |
| 170114 | Sucre brut de canne | **3,37 Md** | MAR 950 M, EGY 934 M, NGA 717 M, TZA 118 M |
| 210690 | Préparations alimentaires n.d.a. | 2,37 Md | NGA 290 M, EGY 264 M, ZAF 229 M, LBY 160 M |
| 020714 | Morceaux de poulet congelés | **1,74 Md** | GHA 328 M, AGO 213 M, ZAF 192 M, COG 139 M |
| 190190 | Extraits de malt, préparations céréales/lait | 1,54 Md | SEN 288 M, NGA 239 M, MLI 111 M, MRT 89 M |
| 150710 | Huile de soja brute | 1,22 Md | MAR 462 M, ZWE 215 M, MOZ 135 M, ZMB 114 M |
| 230990 | Préparations pour l'alimentation animale | 1,02 Md | UGA 128 M, ZAF 115 M, EGY 91 M, MAR 62 M |
| 110100 | Farine de blé | 0,92 Md | SDN 252 M, SOM 119 M, MDG 72 M, DJI 67 M |
| 220210 | Eaux sucrées ou aromatisées | 0,81 Md | COD 164 M, ZAF 129 M |
| 190219 | Pâtes alimentaires | 0,81 Md | SOM 123 M, GHA 82 M, ZAF 78 M |
| 040210 | Lait en poudre écrémé | 0,76 Md | EGY 228 M, MAR 99 M, NGA 96 M, LBY 74 M |
| 151219 | Huile de tournesol raffinée | 0,76 Md | DJI 229 M, LBY 116 M, SDN 73 M |
| 010229 | Bovins vivants | 0,68 Md | MAR 259 M, EGY 196 M, ZAF 99 M |
| 190110 | Préparations pour l'alimentation infantile | 0,67 Md | EGY 86 M, LBY 74 M, NGA 58 M |
| 190531 | Biscuits sucrés | 0,60 Md | COD 92 M, MAR 48 M |
| 180690 | Préparations au chocolat | 0,38 Md | LBY 87 M, MAR 53 M, ZAF 52 M |
| 080410 | Dattes | 0,34 Md | MAR 245 M, EGY 17 M, MRT 11 M |

Exportations agroalimentaires de l'Algérie, 2024 (lignes du fichier) : 392 M USD au total, dont 200 M USD vers l'Afrique (51 %).

| Produit | 2024 | Vers l'Afrique | Rappel 2021 |
|---|---|---|---|
| Dattes | 167,8 M USD | 68,6 M | 144,0 M |
| Sucre raffiné | 101,6 M | 91,4 M (TUN 82 M, NER 6 M) | **273,0 M** |
| Farine de blé | 17,8 M | 100 % | 8,7 M |
| Pâtes | 3,4 M | 97 % | — |

Limites déclarées par le fichier :
- L'Algérie n'a pas déclaré à UN Comtrade de 2018 à 2023 ; ces années sont reconstituées à partir des déclarations des pays partenaires.
- Les échanges avec la Libye après 2019 sont sous-estimés.

### B3. Balance offre-demande industrielle agroalimentaire, 2023

[`backend/data/unido/unido_idsb_indstat_isic4_2018plus.csv.gz`]
- Dataset « IDSB 2026, ISIC Rev.4 », `data_nature` = `UNIDO_DERIVED_ESTIMATE`. Source : stat.unido.org, extrait le 01/09/2026.
- Couverture : 18 pays (AGO, BWA, CIV, CPV, EGY, GHA, KEN, MAR, MUS, MWI, NAM, RWA, SEN, SWZ, TUN, TZA, ZMB, ZWE). **NGA, ZAF, DZA et ETH sont absents.**
- Montants en USD courants.

| Classe ISIC | Import. 18 pays | Export. 18 pays | Premiers importateurs | Premiers exportateurs |
|---|---|---|---|---|
| 1040 Huiles et graisses | **7,77 Md** | 2,21 Md | EGY 3,04 Md, MAR 1,52, KEN 0,96 | TUN 547 M, CIV 349, MAR 347 |
| 1010 Viande transformée | 3,70 Md | 1,04 Md | EGY 1,25 Md, MUS 1,03, AGO 0,50, GHA 0,34 | MUS 553 M, KEN 144 M |
| 1061 Meunerie | 3,56 Md | 0,94 Md | CIV 774 M, GHA 581, SEN 524, KEN 407 | EGY 472 M, TZA 211 M |
| 1072 Sucre | 3,44 Md | 1,75 Md | MAR 1,16 Md, EGY 0,74, KEN 0,39 | EGY 719 M, MAR 405, SWZ 394, ZMB 125 |
| 1020 Poisson transformé | 2,50 Md | 3,20 Md | CIV 848 M, EGY 626, MAR 289, GHA 214 | **MAR 2,61 Md**, GHA 188 M, TZA 152 M |
| 1079 Autres produits alimentaires | 2,47 Md | 1,55 Md | EGY 524 M, MAR 364, SEN 321 | EGY 519 M, MAR 223, KEN 209, SEN 204 |
| 1050 Produits laitiers | 1,78 Md | 0,39 Md | EGY 648 M, MAR 444 M | EGY 226 M, ZMB 54 M |
| 1030 Fruits et légumes transformés | 1,09 Md | 2,77 Md | MAR 393 M | **EGY 1,61 Md**, MAR 359, CIV 230, KEN 182 |
| 1073 Cacao, chocolat, confiserie | 0,60 Md | **3,80 Md** | EGY 176 M, MAR 170 M | **CIV 2,49 Md**, GHA 791 M, EGY 272 M |
| 1200 Tabac | 1,09 Md | 2,60 Md | EGY 301 M | ZWE 1,29 Md (probablement du tabac en feuilles reclassé), MWI 391 M, TZA 373 M |
| 1080 Aliments pour animaux | 0,55 Md | 0,17 Md | MAR 115 M | EGY 60 M |

### B4. Droits de douane et catégories ZLECAf des lignes agricoles

**Offres officielles.** [`backend/data/official_preferential/*_afcfta_etariff_*.json.gz`, source « AfCFTA e-Tariff Book — Tariff Concession Schedule » (etariff.au-afcfta.org), collecte août-septembre 2026]
- Statut `OFFER_ONLY` sauf ZAF (voir README du dossier).
- Catégories : A = libéralisé ; B = sensible ; C = exclu ; « non spécifié » = ligne absente des listes A publiées.

| Offre (date de révision) | Lignes agricoles 01-24 hors catégorie A | Toutes lignes hors A |
|---|---|---|
| Maroc (30/06/2023) | **39,7 %** | 11,5 % |
| Zambie (26/10/2021) | 32,9 % | 11,4 % |
| Tunisie (20/09/2022) | 29,7 % | 12,3 % |
| CEDEAO, Ghana (26/10/2021) | 25,1 % | 10,7 % |
| CEMAC, Cameroun (26/10/2021) | 22,5 % | 11,0 % |
| Éthiopie, Zimbabwe | 16,2 % | 10,8 et 10,6 % |
| CAE, Kenya (21/07/2022) | 10,0 % | 11,1 % |
| Égypte (26/10/2021) | 8,9 % | 10,0 % |

Lignes clés :

| HS6 | Produit | Statut par offre |
|---|---|---|
| 170199 | Sucre raffiné | C : CEMAC, TUN, ETH. Non spécifié : CEDEAO, CAE (NPF « 100 % ou 460 USD/t »), ZMB, MAR, ZWE. A : EGY seulement |
| 020714 | Poulet congelé | Non spécifié : CEDEAO (NPF 35 %), MAR (NPF 40 %). B : CEMAC, TUN, ETH. A : CAE (25 %), EGY (30 %, sur 5 ans), ZWE (40 %) |
| 100630 | Riz | CAE : NPF « 75 % ou 345 USD/t », non libéralisé |
| 110100 | Farine de blé | C : CEMAC, ETH. Non spécifié : CEDEAO (20 %), CAE (50 %), MAR (70 %) |
| 180690 | Chocolat | Non spécifié : CEDEAO (NPF 35 %). C : CEMAC. B : EGY (40 %), TUN, ETH |
| 080132 | Cajou décortiqué | A : CEDEAO (20 %), CAE (25 %). C : TUN. B : EGY |

**Tarifs NPF nationaux** [`backend/data/{ISO3}_tariffs.json`, sources par pays : GRA et TEC CEDEAO, EAC CET 2022, ADII Maroc, SARS…, générés en juin 2026, fiabilité A ou B]
- Poulet congelé (020714) : 35 % dans toute la CEDEAO et la CAE, 40 % au MAR, 42 % en ZAF.
- Chocolat (180690) : 35 % en CEDEAO et CAE.
- Blé (100199) : 35 % dans la CAE, contre 5 % en CEDEAO.
- Lait en poudre (0402) : 100 % au MAR. Pour ZAF, la valeur 96 est probablement un droit spécifique mal lu (voir (d)).

### B5. Règles d'origine ZLECAf des produits agricoles

[`backend/data/zlecaf_rules_of_origin.json`, source « AfCFTA Appendix IV (PSR), décembre 2023, 12e Conseil des ministres »]

| Règle | Chapitres ou positions concernés |
|---|---|
| Entièrement obtenu (WO) au niveau du chapitre | 01, 02, 03, 04, 07, 08, 09, 10, 12, **17 (sucres)**, 20, 24 |
| Ch. 18 (cacao) | les matières des ch. 17 **et** 18 doivent être entièrement obtenues |
| Valeur des matières non originaires ≤ 60 % (VA60) pendant 3 ans, puis réexamen vers WO | 1507 (soja), 1511 (palme), 2309 (aliments du bétail) |
| VA60 pendant 5 ans, puis WO | 0403 et 0406 (produits laitiers transformés) ; 1604 (conserves de poisson, puis matières du ch. 3 WO) |
| Changement de position tarifaire (CTH) | **1101 farine de blé** (réexamen après 5 ans) ; ch. 19 (blé du ch. 11 originaire) ; ch. 21 (ou VA60) ; ch. 22 |

### B6. Logistique : fret modélisé pour des paires agroalimentaires

[`logistics_opportunity_adapter.get_freight_options`, conteneur de 20 pieds de 21,6 t, exécuté hors ligne. Coûts **modélisés** (`is_modeled`), année des données 2024]

| Liaison | Mode | Coût | Délai |
|---|---|---|---|
| TZA → KEN (cajou) | maritime | 600 USD | 4 j |
| BEN → NGA | maritime | 602 USD | 4 j |
| CIV → SEN | maritime | 780 USD | 5 j |
| MAR → SEN (conserves) | maritime | 790 USD | 5 j |
| CIV → MAR (cacao) | maritime | 930 USD | 7 j |
| ZAF → AGO (poulet) | maritime | 955 USD | 6 j |
| KEN → EGY (thé) | maritime | 1 080 USD | 13 j |
| GHA → ZAF | maritime | 1 273 USD | 11 j |
| CIV → EGY | maritime | 1 505 USD | 14 j |
| ETH → KEN (café) | rail + mer via Djibouti | 1 687 USD | 11 j |
| UGA → KEN | SGR | 1 803 USD | 6 j |
| ZMB → ZWE (maïs) | route via Beira | 1 877 USD | 7 j |
| SEN → MLI (farine) | corridor Dakar-Bamako | 2 311 USD | 8 j |
| **DZA → NER (farine)** | **Transsaharienne** | **7 842 USD, soit environ 363 USD/t** | **18 j** |

**Corridors** [`data/json/corridors_terrestres.json`, champ `stats.source_org`, année 2024 ; valeurs arrondies]

| Corridor | Transit | Passage frontière | Débit |
|---|---|---|---|
| Northern Corridor | 36 h | 6 h | 12,5 Mt |
| Abidjan-Lagos | 48 h | 18 h | 8,5 Mt, 1 850 camions/j |
| Tema-Ouagadougou | 96 h | — | 4,5 Mt |
| Abidjan-Ouagadougou | 72 h | 24 h | 2,5 Mt (source OPA) |
| Dakar-Bamako | 84 h | — | 1,2 Mt |

### B7. Finance et macroéconomie

- **Couverture des importations en mois** [`data/json/wb_reserves.json`, « World Bank WDI, FI.RES.TOTL.MO », via `macro_indicators_service.get_import_cover`] :
  - GHA 1,64 (2024), ETH 1,78 (2024), KEN 4,03 (2024), EGY 4,36 (2025), TUN 4,51 (2024), AGO 5,32 (2025), MAR 5,93 (2025), ZAF 6,22 (2025), NGA 7,12 (2025), DZA 16,53 (2024).
  - CIV et SEN absents (UEMOA).
- **Contexte** [`data/json/afreximbank_atr2026.json`, « Afreximbank, African Trade Report 2026 », année 2025] : commerce intra-africain de 213,8 Md USD (+5,5 %), exportations de marchandises de 685,2 Md USD.

### B8. Capacités et projets (base curée, sans source par chiffre)

[`data/json/industrial_capacity_intelligence.json`]

| Champion | Capacité | Intrant |
|---|---|---|
| Cevital (DZA), sucre | 2 Mt/an | sucre brut importé (HS 170114) |
| Cevital (DZA), huiles | 570 kt/an | soja brut importé |
| Semouleries (DZA) | 2,5 Mt/an | 1,8 Mt de blé importé |
| Cosumar (MAR) | 1,65 Mt | — |
| Dangote/BUA (NGA) | 1,44 et 1,5 Mt | sucre brut importé |

- Filière dattes algérienne : 1,2 Mt.
- Agrumes ZAF : 2,5 Mt.

[`data/json/projets_structurants_afrique.json`] Seuls 2 projets sont agricoles au sens strict :
- Recapitalisation de la Banque agricole du Niger, 968 M USD (source déclarée : Coface 2025).
- Extension sucrière de Lubombo (SWZ), plus de 200 M USD (source déclarée : RES 2025).

Le parc GDIZ (Bénin) : 1,4 Md USD, 1 640 ha, transformation de coton, soja, cajou et ananas ; objectif 100 % du coton local transformé d'ici 2030 ; source déclarée : Arise IIP 2025.

---

## (c) Idées et messages pour le rapport, avec leurs chiffres

1. **Les huiles végétales sont le premier trou de la balance agro-industrielle.**
   - Les importations africaines d'huile de palme raffinée atteignent 5,73 Md USD en 2024, plus 1,22 Md d'huile de soja brute et 0,76 Md d'huile de tournesol [B2].
   - Dans les 18 pays couverts par UNIDO, la classe 1040 importe 7,77 Md USD et n'en exporte que 2,21 Md [B3].
   - Pourtant, NGA, GHA, CMR et CIV produisent 29,5 Mt de régimes (+14,7 % depuis 2019), et le soja africain a presque doublé (+85 %).
   - Une fenêtre d'origine existe : la règle VA60 s'applique aux positions 1507 et 1511 pendant 3 ans. Il faut donc investir dans le raffinage **avant** le réexamen vers « entièrement obtenu ».

2. **Le sucre combine grande demande et double verrou.**
   - Demande : 4,76 Md USD de sucre raffiné et 3,37 Md de sucre brut importés en 2024 [B2]. Production africaine : 10,9 Mt de sucre brut (EGY, ZAF, SWZ, UGA, KEN, ZMB).
   - Premier verrou, l'origine : le ch. 17 est « entièrement obtenu » [B5]. Le raffinage de sucre brésilien (Cevital, Cosumar, Dangote/BUA, près de 6,6 Mt de capacité cumulée [B8]) **ne confère pas l'origine ZLECAf**.
   - Second verrou, les tarifs : le 170199 est exclu ou non libéralisé dans presque toutes les offres, sauf l'Égypte [B4].
   - Une illustration : les exportations algériennes de sucre raffiné sont passées de 273 M USD (2021) à 102 M USD (2024), dont 90 % vers l'Afrique, surtout la Tunisie [B2].
   - La vraie opportunité ZLECAf porte sur le sucre de canne africain (SWZ, ZMB, MWI, ZAF) vers les importateurs d'Afrique de l'Est et du Nord.

3. **Le poulet congelé est un marché de substitution de 1,7 Md USD.**
   - Importateurs 2024 : GHA 328 M, AGO 213 M, ZAF 192 M, COG 139 M [B2]. La production africaine a crû de 14,6 % (7,64 Mt ; EGY et ZAF font 52 %).
   - Tarifs de 35 à 42 %, mais la ligne est non libéralisée en CEDEAO et au MAR et sensible en CEMAC, TUN et ETH [B4].
   - Leviers :
     - chaîne soja + maïs vers aliment du bétail : 7,46 Mt de soja, 99,4 Mt de maïs, et 1,02 Md USD d'aliments pour animaux (230990) importés ;
     - corridor maritime ZAF → AGO à environ 955 USD le conteneur en 6 j [B6].

4. **La meunerie est le rare maillon où un intrant non africain peut conférer l'origine.**
   - La farine (1101) relève du changement de position [B5], et les pâtes du ch. 19 exigent seulement une farine originaire.
   - Demande : 0,92 Md USD de farine (SDN, SOM, MDG, DJI), 0,81 Md de pâtes [B2]. Côté UNIDO : 3,56 Md d'importations et 0,94 Md d'exportations (EGY 472 M, TZA 211 M) [B3].
   - Hubs meuniers possibles : EGY, DZA (2,5 Mt de capacité ; exportations de farine en hausse de 8,7 à 17,8 M USD, 100 % vers l'Afrique), TZA, SEN.
   - Deux réserves : le réexamen prévu après 5 ans, et les lignes farine exclues ou non libéralisées (CEMAC C, ETH C, CAE à 50 %, MAR à 70 %).

5. **Le blé offre une substitution intra-africaine structurellement limitée : à dire explicitement.**
   - Production de 26,2 Mt, stable (−1,9 % depuis 2019), concentrée chez des importateurs nets : EGY 9,07 Mt, ETH 6,09, MAR 4,16, DZA 2,5 [B1].
   - Le profil de repli du SaaS désigne pourtant EGY et ETH comme « fournisseurs potentiels » (voir (d)).
   - Recommandation : présenter le blé comme un sujet de production et de rendement (projections OCDE-FAO de céréales en hausse, ETH à 35 Mt en 2030), pas comme un sujet de substitution.

6. **Le cacao se joue sur la transformation et la mise en marché intra-africaine du chocolat.**
   - CIV et GHA pèsent 74 % des 3,34 Mt (2023). Tendance : −10,8 % depuis 2019 ; GHA est tombé à 0,53 Mt en 2024 [B1].
   - La classe UNIDO 1073 exporte déjà 3,80 Md USD (CIV 2,49 Md, GHA 0,79 Md) pour 0,60 Md importés (EGY et MAR, environ 0,35 Md à eux deux) [B3]. Les importations africaines de préparations au chocolat atteignent 0,38 Md (LBY, MAR, ZAF) [B2].
   - Contrainte : la règle d'origine du ch. 18 impose du cacao **et** du sucre africains [B5]. Il faut donc un couplage cacao ouest-africain et sucre austral ou égyptien.
   - Le chocolat reste taxé à 35 % en CEDEAO et non libéralisé [B4].
   - Couloir maritime CIV → MAR modélisé à 930 USD le conteneur en 7 j [B6].

7. **Le cajou a la plus forte dynamique primaire et une industrialisation naissante.**
   - Production de 2,66 Mt (+45 % depuis 2019), dont 46 % pour la CIV. Vient ensuite l'arc TZA–BEN–GHA–MOZ–BFA [B1].
   - Le cajou décortiqué (080132) est déjà en catégorie A en CEDEAO et dans la CAE [B4].
   - Vitrine d'investissement : GDIZ au Bénin, 1,4 Md USD [B8].
   - Idée : un couloir de noix transformées entre l'Afrique de l'Ouest et l'Afrique du Nord ou australe. Les droits NPF de 20 à 36 % donnent une marge préférentielle réelle.

8. **Les produits laitiers opposent un bassin laitier à une dépendance à la poudre.**
   - L'Afrique produit 42,6 Mt de lait de vache (KEN, EGY, TZA, UGA, ZAF, ETH) mais seulement 25 kt de lait entier en poudre [B1].
   - Elle importe 0,76 Md USD de lait écrémé en poudre (EGY, MAR, NGA) [B2]. La classe UNIDO 1050 importe 1,78 Md et exporte 0,39 Md [B3].
   - Levier : séchage de lait en Afrique de l'Est (Kenya, Ouganda). Les yaourts et fromages (0403, 0406) bénéficient de la VA60 pendant 5 ans.

9. **Le Maroc est la plateforme continentale du poisson transformé.**
   - La classe UNIDO 1020 exporte 2,61 Md USD depuis le MAR, alors que CIV (848 M), EGY (626 M) et GHA (214 M) importent [B3].
   - Conserves (1604) : VA60 pendant 5 ans [B5].
   - Liaison MAR → SEN modélisée à 790 USD le conteneur en 5 j [B6].

10. **L'Égypte fait figure de hub agro-industriel.**
    - Elle exporte 1,61 Md USD de fruits et légumes transformés, 0,72 Md de sucre et 0,47 Md de produits de meunerie [B3].
    - Elle produit 3,47 Mt d'oranges, 7,1 Mt de tomates et 1,70 Mt de dattes [B1].
    - C'est aussi l'offre ZLECAf la plus libérale sur l'agricole (8,9 % de lignes hors A) [B4].
    - Elle reste le premier importateur d'huiles (3,04 Md) et de viande (1,25 Md) [B3].

11. **Le café et le thé ouvrent un marché régional de la torréfaction et du conditionnement.**
    - Production : ETH 0,56 Mt et UGA 0,47 Mt de café ; KEN 69 % du thé africain [B1].
    - L'idée de café torréfié ETH/UGA vers les marchés urbains de la CAE et de l'Afrique du Nord figure dans le cache IA du SaaS, avec un potentiel de 480 M USD non sourcé.
    - Logistique : ETH → KEN à 1 687 USD le conteneur en 11 j via Djibouti ; UGA → KEN à 1 803 USD en 6 j par le SGR [B6].
    - Le 090111 est non libéralisé dans l'offre CAE [B4].

12. **Les produits agricoles sont les plus protégés du démantèlement ZLECAf.**
    - Part des lignes agricoles hors catégorie A : 39,7 % au Maroc, 29,7 % en Tunisie, 25,1 % en CEDEAO et 22,5 % en CEMAC.
    - Toutes lignes confondues, cette part est d'environ 11 % [B4].
    - Message politique : l'agroalimentaire, secteur le plus substituable (coefficient de 0,9 dans le modèle), est aussi le moins libéralisé. C'est le paradoxe central à documenter.

13. **Les corridors intérieurs pèsent lourd dans le coût.**
    - Un conteneur maritime côtier coûte de 600 à 1 500 USD. Il faut 1 800 à 2 300 USD vers les pays enclavés (SEN → MLI, UGA → KEN, ZMB → ZWE) et 7 842 USD en Transsaharienne (DZA → NER), soit environ 363 USD/t de farine [B6].
    - Sur Abidjan-Ouagadougou, le passage de frontière prend 24 h pour 72 h de transit [B6].
    - Conclusion : pour le Sahel, la substitution passe par les ports du golfe de Guinée (Tema, Lomé, Cotonou) et les zones franches agro de l'arrière-pays, pas par le Nord.

14. **Le risque de paiement des importations alimentaires plaide pour les règlements intra-africains.**
    - Couverture des importations : GHA 1,64 mois, ETH 1,78 mois, contre DZA 16,5 et NGA 7,1 [B7].
    - Les pays les plus exposés sont souvent de gros importateurs d'huile, de riz ou de poulet. Le règlement en monnaies locales via PAPSS, prévu par l'adaptateur financier mais non exécuté ici, est un argument pour la substitution intra-africaine.

---

## (d) Réserves sur la qualité des données

- **La substitution « réelle » n'est pas reproductible hors ligne.** Le cœur du module (importations hors Afrique par HS6 et fournisseurs africains) dépend de l'API OEC en direct. Il n'existe aucun cache local (`backend/data/_cache` est absent, `httpx` n'est pas installé). Seul `data/json/dza_commerce_baci.json` porte des flux BACI réels, et uniquement pour le périmètre de l'Algérie exportatrice.
- **Profils de repli sans source** (`COUNTRY_SUBSTITUTION_PROFILES`, `backend/services/real_substitution_service.py`) :
  - 10 pays, 20 lignes agricoles, 30,6 Md USD au total (par exemple EGY blé 4 500 M, NGA blé 3 500 M, DZA sucre 850 M, DZA lait 620 M).
  - Ni année ni source ; valeurs arrondies ; drapeau `is_estimation: True`.
  - Fournisseurs incohérents : EGY et ETH proposés pour le blé alors qu'ils en sont importateurs nets (EGY figure lui-même comme importateur de 4,5 Md dans la même table).
  - **À ne pas citer comme données.**
- **Chaînes de valeur par défaut** (`DEFAULT_VALUE_CHAINS` dans `ValueChains.jsx`, pour café, cacao et coton) : chiffres codés en dur, sans source, qui contredisent la FAOSTAT du dépôt.

  | Chiffre codé en dur | FAOSTAT 2023 du dépôt |
  |---|---|
  | Cacao CIV : 2,2 Mt (45 %) | 1,82 Mt (54 %) |
  | Café ETH : 496 kt (42 %) | 559 kt (29 %) |
  | Coton MLI : 780 kt | 583 kt de coton-graine |

  Les champs `intraAfricanPotential` (450, 680, 890) ne sont pas sourcés.
- **Cache IA des chaînes de valeur** (`backend/data/ai_cache/zlecaf_claude_value_chains_*.json`) : « generated_by: Claude AI (claude-sonnet-4-6) », mis en cache le 10/07/2026. Les potentiels (cacao transformé 1 200 M USD, café torréfié 480 M, 50,68 Md tous secteurs) sont **générés, pas mesurés**. À utiliser comme idées seulement. Il en va de même pour tous les onglets IA (résumé, produit, comparaison).
- **Écart tarifaire des flux stratégiques** : il repose sur une table NPF « simplifiée » par chapitre (`routes/tariffs_calculation.get_chapter_rate`), pas sur les tarifs nationaux. La capture est plafonnée à 25 % par hypothèse. Les scénarios de production (+3 et +6 points) sont mécaniques.
- **Projections OCDE-FAO** (`agri_projections`) : 60 valeurs toutes rondes (par exemple MAR céréales 8,0 Mt en 2025, NGA racines 120 Mt), pour des pays que l'Outlook ne publie pas tous individuellement. À vérifier à la source avant publication.
- **FAOSTAT** : source réelle, mais les drapeaux FAO (estimé ou imputé) ne sont pas conservés dans le fichier. Points à recouper :
  - Café de la Centrafrique : 203 à 325 kt sur 2019-2024, valeurs décimales et invraisemblables pour ce pays.
  - Café de la Guinée : 175 à 262 kt.
  - Thé du Kenya : 2,58 Mt, ce qui correspond à la feuille fraîche et non au thé fabriqué.
  - Valeurs rondes typiques des estimations FAO : cacao NGA 350 000 t, café GIN 200 000 t.
  - L'étiquette `sector_detail` = « Crops » est appliquée aussi au lait et à la viande.
  - L'année 2024 est incomplète : sucre brut, fibre de coton, huile d'olive et palmistes y sont absents.
- **UNIDO IDSB** : les valeurs sont des estimations dérivées par UNIDO (`UNIDO_DERIVED_ESTIMATE`). La production (Output) manque pour plusieurs pays, ce qui rend les agrégats de production et de consommation partiels ; importations et exportations sont plus complètes. 18 pays seulement (sans NGA, ZAF, ETH, et DZA hors série 2005-2017). Le tabac du Zimbabwe (1,29 Md) mêle probablement du tabac en feuilles.
- **Tarifs** :
  - Offres e-Tariff marquées `OFFER_ONLY`, non exécutoires sauf ZAF.
  - Révisions anciennes : 2021 pour CEDEAO, CEMAC, EGY et ZMB.
  - « Non spécifié » ne veut pas forcément dire « exclu ».
  - Dans les fichiers nationaux :
    - ZAF 040221 = 96 est probablement un droit spécifique lu comme ad valorem ;
    - le taux uniforme de 36 % en Tunisie mérite un contrôle ;
    - CMR 020714 = 5 % paraît bas pour la CEMAC ;
    - la RDC est tarifée « EAC CET 2022 ».
  - Fiabilité déclarée : « PARTIAL / B » pour la CEDEAO, la CAE et ZAF.
- **Données qualitatives régionales** (`regional_intelligence_service.py`, `north_africa_intelligence.py`, `sadc_intelligence_service.py`) : notes et secteurs clés codés en dur, sans source (par exemple agriculture MAR 8/10, olive_oil TUN 10). À citer comme appréciations de la plateforme uniquement.
- **Fichiers « zones franches »** (`sector_analysis.json`, `investment_opportunities.json`, `trade_facilitation_metrics.json`, `operational_details.json`, `sustainability_metrics.json`) : version 1.0.0, générés le 15/01/2025, méthodologie « Expert Assessment 2024 », scores de 0 à 100, allure de gabarit.
- **`zones_franches_afrique.json`** : aucune source ; numéros de contact à l'allure factice (par exemple « +243 81 555 0000 ») ; Bukanga Lonzo présenté « en restructuration ».
- **Autres attributions non vérifiables** :
  - `industrial_capacity_intelligence.json` : aucune source par chiffre.
  - Corridors : `source_org` indiqué, mais valeurs rondes (throughput, heures).
  - Coûts de fret : modélisés.
- **Sources fiables, utilisables telles quelles** avec leur citation :
  - FAOSTAT (`production_africaine.json`) ;
  - BACI (`dza_commerce_baci.json`) ;
  - UNIDO IDSB (CSV) ;
  - règles d'origine (Appendix IV, déc. 2023) ;
  - e-Tariff Book UA ;
  - WDI (réserves) ;
  - Afreximbank ATR 2026.
