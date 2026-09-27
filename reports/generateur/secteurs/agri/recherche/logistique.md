# Logistique, surprimes de guerre et surcoûts carburant — filières agroalimentaires ZLECAf

*Note de recherche pour le « Rapport Agriculture & Agroalimentaire — ZLECAf ». Arrêtée au 27/09/2026.*

**Conventions.**
- **[SaaS]** : donnée lue dans le dépôt `afcfta-final-002`. Les fichiers n'ont pas été modifiés.
- **[WEB]** : source externe, avec la date de publication et l'URL.
- **[PW]** : calcul fait sur les données brutes IMF PortWatch (API ArcGIS publique `Daily_Chokepoints_Data` et `Daily_Ports_Data`), extraites le 27/09/2026. Dernières observations : 20/09/2026 pour les détroits, 18/09/2026 pour les ports. Il s'agit d'estimations AIS du FMI, pas de statistiques d'autorités portuaires.
- **[FRED]** : séries EIA diffusées par la Fed de St. Louis (DCOILBRENTEU, DJFUELUSGULF), extraites le 27/09/2026.
- **[CALC]** : calcul de l'auteur, avec ses hypothèses.
- « nm » désigne les milles nautiques.

---

## Synthèse (à reprendre en encadré)

1. **Deux crises maritimes se superposent en 2026.**
   - **Bab el-Mandeb / mer Rouge.** La crise houthie dure depuis nov. 2023. Elle s'est aggravée avec le blocus des navires liés à l'Arabie saoudite (21/07/2026), puis avec la prise de Mokha (10/09) et de l'île de Perim (11-12/09/2026).
   - **Ormuz.** La guerre États-Unis/Israël–Iran a commencé le 28/02/2026. Il y a eu un cessez-le-feu en avril-juin, puis une reprise des hostilités les 8-9/07/2026.
   - **Trafic [PW].** Bab el-Mandeb est tombé à **25,9 navires/jour en sept. 2026**, contre **74,6/jour en 2023**, soit −65 %. Ormuz est tombé à **3,9/jour**, contre 95,6, soit −96 %. Le Cap de Bonne-Espérance est passé à **86-97/jour**, contre 48,9/jour en 2023 (+76 à +98 %).
2. **Surprimes « risque de guerre » (en % de la valeur de coque, par transit d'environ 7 jours).**
   - Mer Rouge : ~0,05 % avant la crise, puis 0,7-1 % au pic de 2024.
   - 0,2 % à 1 % en 2026 selon les incidents, et 0,5 % pour Bab el-Mandeb en juillet 2026.
   - Jusqu'à **3 % à Yanbu et 7 % à Jizan** pour les navires liés à l'Arabie saoudite en sept. 2026.
   - **6-10 % à Ormuz.**
   - **~1 %** pour les ports ukrainiens en mer Noire en sept. 2026. La zone JWC a été étendue le 16/09/2026.
3. **Choc carburant [FRED].**
   - Le Brent est passé de 69 $/b en moyenne 2025 à **113 $/b en moyenne sur sept. 2026** (du 1er au 22). Le pic est de **130,8 $ le 15/09/2026**.
   - Le kérosène US Gulf est passé de 89 $/b en 2025 à **184 $/b en sept. 2026** (+107 %).
   - Le fret aérien des fleurs kényanes a doublé : de ~2,5 $/kg à **5-5,8 $/kg** en mars 2026.
4. **Ports africains : gagnants et perdants [PW].**
   - Gagnants : Tanger Med (**11,1 M EVP en 2025**, record), Walvis Bay (volumes estimés +78 % entre 2023 et août-sept. 2026), Port-Louis (soutage ×2), Abidjan (+59 %).
   - Perdants : Djibouti (EVP −10,5 % au S1 2025 et −17,5 % au S2 2025 selon la Banque mondiale), Port-Soudan et Jeddah. Jeddah a perdu 74 % de ses escales en août-sept. 2026, ce qui pèse directement sur le bétail de la Corne de l'Afrique.
5. **Le SaaS ignore le risque de guerre et le déroutement.**
   - Le moteur de fret maritime choisit toujours le trajet le plus court (Suez / Bab el-Mandeb).
   - Il n'applique aucune surprime de guerre, surcharge carburant d'urgence, ETS ni péage de Suez.
   - Ses tarifs sont figés en 2024 (`data_year: 2024`).
   - Pour le rapport, les surcoûts ci-dessous doivent être **ajoutés hors modèle**.

---

## 1. Données logistiques du SaaS (fichier, source déclarée, fiabilité)

### 1.1 Ports — `data/json/ports_africains.json`

Le fichier contient 68 enregistrements, dont environ 15 doublons à identifiant haché (ex. `SDN-PTS-3ae1c38d`). Il est lu par `backend/logistics_data.py`.

**Principaux ports agroalimentaires**

| Port | EVP 2024 [SaaS] | Tonnage 2024 | Séjour conteneur (dwell) | Source du dwell (fiabilité SaaS) | THC 20'/40' ($) — `logistics_fees_data.py` |
|---|---|---|---|---|---|
| Tanger Med | 8,2 M ⚠️ | 96 Mt | 7,8 j | Beacon / TMPA 2024 (niv. 3) | 170 / 250 |
| Alexandrie | 1,85 M | 52 Mt | 8,64 j | Egypt Customs TRS #2, 2024 (niv. 2) ; [URL](https://assets.mof.gov.eg/files/d06136d0-b7aa-11ef-9d21-798cef5fccf4.pdf) | 155 / 225 |
| Port-Saïd | 4,2 M | 48 Mt | NA | — | 160 / 230 |
| Dakar | 0,85 M | 16,5 Mt | NA | — | 180 / 270 |
| Abidjan | 1,05 M | 24,5 Mt | 3,54 j (transit 5 j) | PAA Infos #112, 2023 (niv. 2) | 185 / 275 |
| San Pedro (cacao) | 45 k | 3,8 Mt | NA | — | 185 / 275 |
| Tema | 1,2 M | 18,5 Mt | 6-12 j | GPHA / presse, estimation (niv. 3) | 178 / 265 |
| Lomé | 1,95 M | 22 Mt | 4,2 j | Ecofin 2025 (niv. 3) | 180 / 270 |
| Lagos-Apapa | 1,65 M | 42 Mt | 16,2 j | LPI 2023, moyenne nationale (niv. 2) | 230 / 340 |
| Douala | 0,85 M | 16 Mt | 12 j | estimation « free time » (niv. 5) | 195 / 290 |
| Mombasa | 1,55 M | 34,5 Mt | 3,5 j (record 2,73 j en avr. 2024) | KPA 2023 (niv. 2) | 200 / 300 |
| Dar es Salaam | 1,1 M | 18,5 Mt | 7,4 j | TASAC 2023 (niv. 2) | 210 / 320 |
| Djibouti | 1,25 M | 22 Mt | 6 j | **estimation modélisée (niv. 5)** | 205 / 305 |
| Port-Soudan | 280 k ⚠️ | 8,5 Mt | NA ; attente 150 h | aucune TRS | 180 / 265 |
| Durban | 2,85 M | 68 Mt | 2,7 j | Transnet TPT 2024 (niv. 2) | 220 / 330 |
| Le Cap | 0,92 M | 24 Mt | 5,3 j | LPI 2023, moyenne nationale | 210 / 315 |
| Walvis Bay | 0,52 M | 9,5 Mt | NA (TRS WCO/NAMRA citée) | — | 185 / 275 |
| Maputo | 0,28 M | 18,5 Mt | NA | — | 195 / 290 |
| Lobito | 0,12 M | 5,2 Mt | NA | — | 210 / 310 |

**Anomalies relevées**
- **Capacité frigorifique (reefer).** Aucune donnée de capacité reefer (prises, entrepôts froids) n'existe dans les fichiers ports. « Reefer » n'y apparaît que comme type de cargo accepté par certains agents.
- **Séries `traffic_evolution` générées par gabarit.** Sur 344 points, le ratio EVP/escales vaut **≈ 800** (médiane 800,8). Le nombre d'escales est donc calculé comme EVP ÷ 800. Les croissances sont lisses (+4 à 8 %/an). Ces séries sont illustratives.
- **Métriques sans source.** Les champs `performance_metrics` (attente, séjour) portent souvent des décimales synthétiques (62,2 h ; 71,7 h). Ils sont datés « 2025-01-16 (Données consolidées) » et n'ont pas de `source`. Ils contredisent parfois `latest_stats` : pour Mombasa, l'attente vaut 15,8 h dans un champ et 69,6 h dans l'autre.
- **LSCI.** C'est une valeur **pays** répétée pour chaque port (ex. Maroc 41,88 pour Casablanca, Tanger et Agadir). La source est la CNUCED 2023.
- **Tanger Med sous-estimé.** Le fichier indique 8,2 M EVP en 2024. Le chiffre officiel est **11,1 M EVP en 2025** (+8,4 %, donc ~10,2 M en 2024) ([TMPA, 02/02/2026](https://www.tangermed.ma/wp-content/uploads/press-releases/2026/CP-TMPA-PORT-ACTIVITY-REPORT-IN-2025.pdf)).
- **Port-Soudan incohérent.** L'enregistrement principal donne 280 000 EVP, le doublon 32 000 EVP.
- **Rotations d'avant-crise.** Les services listés restent ceux d'avant la crise, par exemple Maersk « Singapore-Colombo-Mombasa-Djibouti-Jeddah-Suez-Rotterdam ». Ils ne reflètent pas le déroutement par le Cap.
- **Djibouti non mis à jour.** Le fichier affiche « Record 1,24 M EVP 2024 » mais ignore la baisse de 2025, soit −10,5 % au S1 et −17,5 % au S2 ([Banque mondiale, MPO avril 2026](https://thedocs.worldbank.org/en/doc/65cf93926fdb3ea23b72f277fc249a72-0500042021/related/mpo-dji.pdf)).
- **LPI des ports non recoupé.** `lpi_2023` donne Kenya 2,8 (rang 68) et Côte d'Ivoire 2,8 (rang 79). Or `wb_logistics_africa.json` (WDI) n'a aucune valeur 2023 pour KEN ni CIV : les dernières datent de 2018. À recouper.
- **Fichier « enhanced ».** `ports_africains_enhanced_maritime_logistics.json` (métadonnées du 07/03/2026) ajoute surtout des annuaires d'agents (Maersk, MSC…). Les sources sont génériques (« Official company websites », « AfDB logistics data »). Il n'apporte pas de nouvelle mesure de performance.

### 1.2 Tarifs maritimes conteneurs — `backend/logistics_fees_data.py`

**Contenu**
- 55 ports et environ 1 485 routes.
- ~40 routes dites « benchmark », présentées comme « tarifs publiés ».
- Les autres routes sont **modélisées** : `teu = 175 + 0,255 × distance_nm` (arrondi à 5 $) ; FEU = 1,5 × TEU ; transit = distance ÷ 470 à 320 nm/j.

**Routage : le cœur du problème**
- `_COAST_ROUTING` retient **toujours le trajet le plus court**. Les liaisons Méditerranée ↔ océan Indien passent donc par Suez et Bab el-Mandeb.
- Aucun paramètre ne gère le déroutement par le Cap.
- `get_total_cost()` additionne fret, THC d'origine et THC de destination. L'avertissement indique « Hors : pré/post-acheminement, droits, **assurance** ».
- Le champ `data_year` est codé en dur à 2024.

**Benchmarks utiles pour l'agroalimentaire**

| Route | Distance | Transit | $/EVP | $/FEU | Source déclarée |
|---|---|---|---|---|---|
| Port-Saïd–Mombasa | 3 100 nm | 9-13 j | 720 | 1 060 | « Maersk East Africa Rate Guide 2024 ; UNCTAD MRTS 2024 p.92 » — note : « Via canal de Suez — surcharge Suez incluse » |
| Alexandrie–Mombasa | 3 180 nm | 9-13 j | 745 | 1 100 | — |
| Port-Saïd–Dar | 3 350 nm | 10-14 j | 800 | — | — |
| Tanger Med–Mombasa | 7 400 nm | 18-24 j | 1 850 | 2 750 | note : « routage Cap +7 jours » |
| Djibouti–Mombasa | 1 180 nm | — | 360 | — | — |
| Durban–Mombasa | 2 650 nm | — | 900 | — | — |
| Abidjan–Tema | 380 nm | — | 195 | — | — |
| Abidjan–Lagos | 910 nm | — | 380 | — | note : surcharge congestion Lagos +150-250 $/EVP |
| Tanger Med–Abidjan | 3 250 nm | — | 780 | — | — |
| Tanger Med–Lagos | — | — | 1 100 | — | note : PSS +200 $/EVP |
| Durban–Walvis Bay | 1 430 nm | — | 530 | — | — |

**Fiabilité des benchmarks**
- Les références « UNCTAD MRTS 2024 p.87/p.92 », « MSC Nigeria Rate Bulletin Q4-2024 » et « Drewry Nigeria Benchmark 2024 » ne sont pas vérifiables publiquement.
- Il faut traiter ces tarifs comme des **ordres de grandeur 2024 illustratifs**, pas comme des cotations.

### 1.3 Fret vraquier (céréales, engrais) — `backend/logistics_bulk_fees_data.py` + `data/json/fret_vraquier.json`

**Modèle**
- Formule : `USD/t = max(6 ; (7 + 0,004 × nm) × facteur_classe) × multiplicateur_marché`.
- Facteurs de classe : Handysize 1,0 ; Supramax 0,82 ; Panamax 0,66 ; Capesize 0,50.
- Toutes les routes sont modélisées (`is_modeled: True`), avec une fourchette de ±30 %.
- Le fichier revendique une discipline « zéro fabrication ».

**Points de calibration (moyennes 2024, « ordre de grandeur »)**
- Golfe US → Égypte, blé, Panamax : **25 $/t** (IGC).
- Mer Noire → Afrique du Nord, blé, Handysize : **16 $/t** (IGC).
- Saldanha → Qingdao, minerai, Capesize (Baltic C17) : 22 $/t.

**Multiplicateur de marché (`fret_vraquier.json`)**
- Valeur **1,3415** pour toutes les classes au 13/08/2026.
- Proxy : ETF BDRY à 13,89 contre une moyenne sur 250 jours de 10,35. Données générées par GitHub Actions, drapeau `is_live: true`.
- Ce n'est pas l'indice Baltic par classe.

**Frais portuaires vrac** : 4,5 $/t au chargement et 5,5 $/t au déchargement (ordre de grandeur modélisé).

**Exclusions** : assurance, surestaries et **péages de Suez**. Le routage reprend `_sea_distance_nm`, donc le plus court chemin.

### 1.4 Corridors terrestres — `data/json/corridors_terrestres.json` + `backend/logistics_land_fees_data.py`

**Modèle de coût**
- Route : 0,085 $/t-km. Rail : 0,045 $/t-km.
- Frontière : 450 $ par poste standard, 250 $ par poste OSBP (poste frontière à guichet unique), plus 150 $ de manutention.
- Coefficient 1,25 pour les **périssables (camion frigo)**.
- Vitesse : 300 km/j sur route, 400 km/j sur rail.
- Source déclarée : « modèle calibré SSATP/UNECA/AfDB 2024 », avec une marge de ±20-30 %.

**Coûts modélisés pour 25 t [CALC avec les fonctions du SaaS]**

| Corridor | km | Stats SaaS : transit / frontière / volume (source) | Route générale $/t | Route périssable $/t | Rail $/t | Délai modèle |
|---|---|---|---|---|---|---|
| Abidjan–Lagos | 992 | 48 h / 18 h / 8,5 Mt (CEDEAO) | 146 | 167 | — | 7-12 j (4 frontières) |
| Abidjan–Ouaga–Niamey | 1 420 | 72 h / 24 h / 2,5 Mt (OPA-BICC) | 137 | 167 | 80 (Sitarail) | 5-7 j |
| Northern Corridor, Mombasa–Kampala | 1 720 | **36 h** ⚠️ / 6 h / 12,5 Mt (NCTTCA) | 162 | 199 | 93 (SGR) | 6-8 j |
| Central Corridor, Dar–Kigali–Bujumbura | 1 650 | 72 h / 8 h / 1,85 Mt (CCTTFA) | 156 | 191 | — | 6-8 j |
| Dakar–Bamako | 1 228 | 84 h / 12 h / 1,2 Mt (« Transrail SA ») ⚠️ | 128 | 154 | 79 ⚠️ | 6-8 j |
| Lomé–Ouagadougou | 985 | 48 h / 6 h / 3,2 Mt (PAL) | 100 | 121 | — | 4-6 j |
| Tema–Ouaga–Bamako | 1 680 | 96 h / 8 h / 4,5 Mt (GPHA) | 159 | 195 | — | 6-8 j |
| Cotonou–Niamey | 1 035 | 60 h / 10 h / 2,8 Mt (PAC) | 104 | 126 | — | 4-6 j |
| Lobito (CFB) | 1 344 | 168 h / — / 0,85 Mt | 84 | 100 | — | 5-7 j |
| Maputo–Gauteng | 572 | 18 h / 8,5 Mt (MPDC) | 73 | 85 | 50 | 3-5 j |
| Beira–Harare | 850 | 48 h / 3,2 Mt | 96 | 114 | 62 | 4-6 j |
| Addis–Djibouti (route) | 910 | — | 83 | 103 | — | 3-5 j |
| Addis–Djibouti (rail) | 756 | — | — | — | 40 | 2-4 j |

**Anomalies relevées**
- **Statuts figés.** Tous les corridors sahéliens sont marqués « Opérationnel », sans aucun indicateur d'insécurité. Or le blocus du JNIM est en cours depuis sept. 2025 (voir §2.7). Le modèle n'a ni surcoût d'escorte, ni prime, ni aléa de délai.
- **Mombasa–Kampala.** Un transit de 36 h sur 1 720 km est peu plausible, et le modèle du même SaaS donne 6-8 jours. Incohérence interne.
- **Dakar–Bamako.** La source « Transrail SA » et l'option rail à 79 $/t sont à vérifier : la concession est réputée arrêtée depuis ~2018-2019 (non vérifié ici).
- **Walvis Bay.** Aucun corridor Trans-Kalahari / Walvis Bay n'existe dans le fichier (le port existe, pas le corridor).
- **Fichier « enhanced ».** `corridors_terrestres_enhanced_logistics.json` (07/03/2026) ajoute des annuaires d'opérateurs (Bolloré/AGL, etc.) et d'organes de corridor (TTCA…). Il n'apporte pas de nouvelle mesure.

### 1.5 Fret aérien (périssables) — `data/json/airports_africains.json` + `backend/logistics_air_fees_data.py`

**Hubs cargo (2024, `historical_stats`)**
- Addis-Abeba (ADD) : **520 000 t** (Ethiopian Airports Enterprise) — « plus grand hub cargo d'Afrique ».
- Johannesburg (JNB) : 405 000 t (ACSA).
- Le Caire (CAI) : 342 000 t.
- Nairobi (NBO) : **285 000 t** (KAA) — « capacité fleurs ».
- Lagos (LOS) : 125 000 t.
- Abidjan (ABJ) : 82 500 t.
- Dakar (DSS) : 78 000 t.
- Accra (ACC) : 72 000 t.
- Entebbe (EBB) : 55 000 t — café, fleurs.
- Kilimandjaro (JRO) : 32 000 t — fleurs.
- Aucun de ces chiffres n'a été recoupé (voir §5).

**Modèle**
- Taux de base : `1,5 + 0,0004 × km` $/kg, borné entre 1,6 et 4,8.
- Coefficient 1,18 pour les **périssables**.
- **Surcharge carburant (FSC) fixe de 0,65 $/kg** et surcharge sûreté de 0,12 $/kg, calibrées sur « IATA TACT 2024 ».
- La FSC est figée au niveau de 2024. Or le kérosène a doublé en glissement annuel (voir §7). Le modèle **sous-estime** donc le coût de 2026.

**Coûts modélisés, périssables, lot de 1 t [CALC]**

| Liaison | $/kg tout compris |
|---|---|
| NBO–CAI | 4,44 |
| NBO–LOS | 4,59 |
| NBO–JNB | 4,13 |
| ADD–CAI | 3,91 |
| ADD–DSS | 5,72 |
| ACC–LOS | 2,87 |

**Limite** : le registre ne contient que des aéroports africains. **Nairobi–Amsterdam n'est pas calculable dans le SaaS.**

### 1.6 LPI et connectivité — `data/json/wb_logistics_africa.json` (ETL `backend/etl_wb_logistics.py`)

**Source** : vraie extraction de l'API WDI de la Banque mondiale, collectée le 03/11/2025, 54 pays, 8 indicateurs.

**Précautions**
- Le WDI code le **LPI 2023 sous l'année « 2022 »**.
- L'indicateur LSCI `IS.SHP.LCON.XQ` est **vide pour tous les pays**, ce qui signale une lacune de l'ETL.
- L'ETL CNUCED (`etl_unctad_maritime.py`) télécharge le LSCI depuis Data360 (datacatalogfiles.worldbank.org), sans clé.

**LPI 2023 (score global sur 5)**
- 3,7 : Afrique du Sud.
- 3,1 : Botswana, Égypte.
- 2,9 : Bénin, Namibie.
- 2,8 : Rwanda.
- 2,7 : Djibouti.
- 2,6 : Nigeria, Mali.
- 2,5 : Ghana, Togo, Algérie, Maurice, RDC, Guinée, Zimbabwe, RCA.
- 2,4 : Soudan, Gabon, Liberia.
- 2,3 : Burkina Faso, Madagascar, Mauritanie.
- 2,1 : Cameroun, Angola.
- 2,0 : Somalie.
- 1,9 : Libye.

**Pays sans LPI 2023 (dernière valeur disponible)**
- Côte d'Ivoire : 3,08 (2018).
- Kenya : 2,81 (2018).
- Tanzanie : 2,99 (2016).
- Maroc : 2,54 (2018).
- Sénégal : 2,25 (2018).
- Éthiopie : 2,38 (2016).

### 1.7 Facilitation des échanges — `data/json/trade_facilitation_metrics.json`

- 30 zones franches notées de 0 à 100. Fichier généré le 15/01/2025.
- Sources : « WTO TFA Monitor, LPI, **Expert Assessment 2024** ».
- Scores composites arrondis et délais douaniers en demi-journées, par exemple :
  - Tanger Med : import 1,5 j, score 80,4.
  - Djibouti DIFTZ : 2,5 j, score 72,1.
  - Nairobi EPZ : 3 j, score 67,1.
  - Maluku (RDC) : 8 j, score 32,1.
- **À considérer comme illustratif.**

### 1.8 Comparateur multimodal — `backend/services/multimodal_freight_service.py` et `services/logistics_opportunity_adapter.py`

- Le service combine les modules ci-dessus : mer, air, terre, et mer + terre.
- Facteurs CO2 (g/t-km) : mer 10 ; rail 22 ; route 62 ; air 602 ; vrac 3-8,5.
- **Aucune** variable ne traite l'assurance, le risque de guerre, la sécurité ou une surcharge d'urgence.
- L'adaptateur « Opportunités » reprend ces coûts comme intrant du « coût rendu ». La **surprime de guerre est donc absente des coûts rendus** affichés par le SaaS.

---

## 2. Conflits et surprimes d'assurance

### 2.1 Chronologie 2023-2026 (faits datés)

| Date | Événement | Source |
|---|---|---|
| 19/11/2023 → | Début des attaques houthies contre la navigation (détournement du *Galaxy Leader*). Les grandes lignes conteneurs basculent vers le Cap. | [Wikipedia « Red Sea crisis » (tertiaire)](https://en.wikipedia.org/wiki/Red_Sea_crisis) ; contexte : [UNCTAD RMT 2025](https://unctad.org/system/files/official-document/rmt2025_en.pdf) |
| 29/01/2025 | Sortie effective du Mali, du Burkina Faso et du Niger (AES) de la CEDEAO. | [allAfrica, 29/01/2025](https://allafrica.com/stories/202501290328.html) |
| janv.-févr. 2025 | Le M23 prend Goma (janv.) puis Bukavu (16/02). | [CFR](https://www.cfr.org/global-conflict-tracker/conflict/violence-democratic-republic-congo) |
| 4-6/05/2025 | Frappes de drones sur Port-Soudan. | [ReliefWeb](https://reliefweb.int/report/sudan/drone-attacks-port-sudan-mark-dramatic-escalation) |
| 03/09/2025 | Le JNIM annonce le blocus des carburants au Mali. | [ISS Africa, 04/06/2026](https://issafrica.org/iss-today/jnim-s-blockade-tactics-threaten-west-africa-s-trade-corridors) |
| 15/11/2025 | Accord-cadre de Doha entre la RDC et l'AFC/M23. | [UA](https://au.int/en/pressreleases/20251115/auc-chairperson-welcomes-doha-framework-comprehensive-peace-agreement) |
| déc. 2025 - févr. 2026 | Retours partiels à Suez : CMA CGM sur INDAMEX, puis COSCO/OOCL et le service ME11 de Maersk à la mi-février 2026. | [Xeneta](https://www.xeneta.com/blog/largescale-return-of-container-ships-to-red-sea-in-2026-five-key-considerations-for-shippers) ; [gCaptain](https://gcaptain.com/container-shipping-returns-to-suez-despite-rising-red-sea-risks/) |
| 28/02/2026 | Début de la guerre États-Unis/Israël–Iran. Fermeture de fait d'Ormuz. | [Afreximbank](https://www.afreximbank.com/afreximbank-to-avail-us10-billion-under-its-gulf-crisis-response-programme-gcrp-to-shield-african-and-caricom-economies-from-the-ongoing-conflict/) ; [Wikipedia (tertiaire)](https://en.wikipedia.org/wiki/2026_Iran_war_fuel_crisis) |
| 02/03/2026 | CMA CGM revient sur le retour en mer Rouge de FAL1, FAL3 et MEX. Maersk redéroute ME11 et MECL par le Cap. Xeneta : « retour à grande échelle en 2026 compromis ». | [Air Cargo News, 02/03/2026](https://www.aircargonews.net/supply-chains/2026/03/box-lines-unlikely-to-return-to-suez-canal-in-2026-following-middle-east-strikes/) |
| 03/03/2026 | Circulaire JWC **JWLA-033** : Djibouti, Bahreïn, Koweït, Oman et Qatar sont ajoutés aux zones listées. | [LMA, JWLA-033 (lue)](https://lmalloyds.com/wp-content/uploads/2026/03/JWLA-033_Iran.pdf) |
| 08/04/2026 | Annonce d'un cessez-le-feu. | [Wikipedia](https://en.wikipedia.org/wiki/2026_Iran_war_fuel_crisis) |
| 17/06/2026 | Accord de cessez-le-feu États-Unis–Iran. | [Al Jazeera, 23/07/2026](https://www.aljazeera.com/economy/2026/7/23/how-shipping-insurance-rates-are-rising-as-hormuz-bab-al-mandeb-shut-down) |
| 8-9/07/2026 | Reprise des hostilités. | idem |
| 21/07/2026 | Les Houthis annoncent un **blocus des navires liés à l'Arabie saoudite** à Bab el-Mandeb. | idem |
| 29/07/2026 | **JWLA-034** : la limite nord-ouest de la zone mer Rouge passe de 18° N à **25,5° N**, ce qui couvre la côte saoudienne et Port-Soudan (19,6° N). | [NNPC Marine](https://nnpc-marine.com/update-joint-war-committee-amends-listed-areas-including-saudi-arabia/) ; [LMA](https://lmalloyds.com/wp-content/uploads/2025/06/JWLA-034-Saudi-Arabia.pdf) (non ouvert) |
| 12/08/2026 | Attaque houthie contre un navire à Bab el-Mandeb : 6 morts. | [Al Jazeera, 12/08/2026](https://www.aljazeera.com/news/2026/8/12/six-killed-in-houthi-attack-on-bab-al-mandeb-ship-yemens-government-says) |
| 10-12/09/2026 | Les Houthis prennent **Mokha** (10/09) puis l'île de **Perim/Mayyun** (11-12/09) : contrôle direct de la rive yéménite du détroit. | [Euronews, 12/09/2026](https://www.euronews.com/2026/09/12/houthis-seize-yemeni-island-in-bab-el-mandeb-taking-control-of-the-strait) ; [CNBC, 11/09/2026](https://www.cnbc.com/2026/09/11/iran-houthis-mokha-red-sea-yemen.html) ; [Carnegie, sept. 2026](https://carnegieendowment.org/emissary/2026/09/houthis-bab-al-mandeb-impacts-saudi-arabia-somaliland) |
| 15/09/2026 | Brent à **130,80 $/b**, pic de 2026. | [FRED DCOILBRENTEU](https://fred.stlouisfed.org/series/DCOILBRENTEU) |
| 16/09/2026 | **JWLA-035** : la zone listée mer Noire est étendue à presque toute la mer. | [UkrAgroConsult, 18/09/2026](https://ukragroconsult.com/en/news/expansion-of-black-sea-war-risk-zone-could-raise-insurance-and-freight-costs/) |

### 2.2 Mer Rouge / Bab el-Mandeb : niveaux de surprime « guerre » (en % de la valeur de coque, par transit)

| Période | Niveau | Source (date) |
|---|---|---|
| Avant oct. 2023 | **0,05 %**, souvent levée | S&P Global et Reuters, via résumé de recherche : [S&P](https://spglobal.com/commodity-insights/en/news-research/latest-news/shipping/021925-shipping-companies-stay-away-from-red-sea-partly-due-to-commercial-interests) ; [PolicyholderPulse](https://www.policyholderpulse.com/red-sea-transit-insurance-premiums-coverage-exclusions/) |
| Déc. 2023 - 2024 | **0,7 %**, puis **1 %** | idem |
| Mi-2025 | de 0,4 % à **1 %** | [ShipUniverse / Nautilus, 2026](https://www.nautilusshipping.com/news-and-insights/war-risk-insurance-in-2026-what-ship-owners-need-to-know) (résumé) |
| Févr. 2026 | ~**0,2 %** en période calme ; 0,3-0,7 % après incident, jusqu'à 1 % (voyage de 7 j) | [ShipUniverse, 09/02/2026](https://www.shipuniverse.com/red-sea-war-risk-pricing-in-2026-why-quotes-swing-from-0-2-to-1-overnight/) |
| 23/07/2026 | Bab el-Mandeb **0,5 %** ; mer Rouge près de la côte ouest saoudienne **0,1 %** | [Al Jazeera, 23/07/2026](https://www.aljazeera.com/economy/2026/7/23/how-shipping-insurance-rates-are-rising-as-hormuz-bab-al-mandeb-shut-down) |
| Sept. 2026 | Navires **non saoudiens** en mer Rouge : **0,2-0,3 %** | [Insurance Journal, 25/09/2026](https://www.insurancejournal.com/news/international/2026/09/25/886769.htm) |
| Sept. 2026 | **Yanbu ~3 %** (moins de 1 % début juillet), soit ~3 M$ par voyage de 7 j contre ≥ 0,1 M$ avant | idem |
| Sept. 2026 | **Jizan jusqu'à 7 %** (~1 % début juillet) | idem |

**Traduction en dollars [CALC]** : une surprime s'exprime en % de la valeur assurée du navire. Voir les exemples chiffrés au §4 : vraquier, porte-conteneurs, pétrolier.

### 2.3 Iran / Ormuz (2026) : énergie, engrais, primes

**Trafic à Ormuz [PW, navires/jour]**
- 2023 (janv.-oct.) : 95,6. 2025 : 85,5.
- 2026 : janv. 58,5 ; févr. 78,3 ; **mars 3,2** ; avr. 7,1 ; mai 3,9 ; juin 12,9 (cessez-le-feu) ; juil. 10,2 ; **août 4,7** ; **1-20 sept. 3,9** (−96 % par rapport à 2023).

**Primes à Ormuz**
- Avant la guerre : « entre 1 et 3 % ».
- En juillet 2026 : **7,5 à 10 %** de la valeur de coque ([Al Jazeera, 23/07/2026](https://www.aljazeera.com/economy/2026/7/23/how-shipping-insurance-rates-are-rising-as-hormuz-bab-al-mandeb-shut-down)).
- En sept. 2026 : **6 à 9 %** ([Insurance Journal, 25/09/2026](https://www.insurancejournal.com/news/international/2026/09/25/886769.htm)).
- Pour un pétrolier VLCC de 270 000 t, l'assurance coûterait environ **21 M$** (Al Jazeera, 23/07/2026).

**Engrais**
- Environ **un tiers** du commerce maritime mondial d'engrais passe par Ormuz ([WTO data blog, 10/07/2026](https://www.wto.org/english/blogs_e/data_blog_e/blog_dta_10jul26_451_e.htm) ; [Banque mondiale](https://blogs.worldbank.org/en/opendata/fertilizer-prices-surge-as-strait-of-hormuz-disruptions-tighten-)). Les fiches Wikipedia citent « plus de 30 % des exportations mondiales d'urée ».
- **Trajectoire de l'urée**
  - 27/02/2026 : **455-470 $/t** ([Western Producer](https://www.producer.com/news/urea-fertilizer-prices-tumble-as-strait-reopens/)).
  - Moyenne de mars 2026 : **725,6 $/t**, soit +53,7 % sur un mois et un plus haut depuis 4 ans (Banque mondiale).
  - Avril 2026 : **plus de 850 $/t**.
  - Juin 2026 : **453 $/t** après la réouverture partielle.
  - Prix de septembre après la nouvelle fermeture : **non trouvé** (voir §5).
- **Indice engrais de la Banque mondiale** : +12 % au T1 2026. La prévision annuelle 2026 dépasse **+30 %** ([Banque mondiale](https://blogs.worldbank.org/en/opendata/fertilizer-prices-surge-as-strait-of-hormuz-disruptions-tighten-) ; [Fertilizer Daily, 23/06/2026](https://www.fertilizerdaily.com/20260623-world-bank-warns-fertilizer-prices-could-surge-more-than-30-in-2026-if-hormuz-disruption-persists/)).

**Afrique de l'Est**
- En Éthiopie, l'approvisionnement en diesel est passé de 9,2 à 4,5 M litres par jour.
- Achats de panique au Kenya. L'Ouganda n'avait plus que quelques semaines de stock fin mars 2026 ([Wikipedia, tertiaire](https://en.wikipedia.org/wiki/2026_Iran_war_fuel_crisis)).

**Réponses des institutions financières africaines**
- **Afreximbank** : programme de réponse à la crise du Golfe (GCRP) de **10 Md$**, lancé le 31/03/2026. Il cible les importations de carburant, GNL, **engrais**, **alimentation** et produits pharmaceutiques ([Afreximbank](https://www.afreximbank.com/afreximbank-to-avail-us10-billion-under-its-gulf-crisis-response-programme-gcrp-to-shield-african-and-caricom-economies-from-the-ongoing-conflict/) ; [GTR](https://www.gtreview.com/news/africa/afreximbank-launches-us10bn-crisis-response-programme-amid-middle-east-conflict/)).
- **BAD** : « Global Energy and Fertilizer Crisis Response Framework » de **~5,1 Md$** (4,1 Md$ de prêts BAD + 0,96 Md$ du FAD), approuvé le 01/09/2026 pour un an ([fundsforNGOs, 17/09/2026](https://news.fundsforngos.org/2026/09/17/afdb-5-billion-africa-energy-fertilizer-shocks/)).

### 2.4 Russie-Ukraine / mer Noire (blé pour l'Égypte et l'Afrique du Nord)

**Surprimes et zone listée**
- Surprime de guerre pour les ports ukrainiens : **~1 %** de la valeur de coque en sept. 2026, contre 0,6-0,8 % fin déc. 2025.
- L'extension de zone du 16/09/2026 ajoute de 0,10 à 0,20 %.
- Pour les voyages vers le Grand Odesa, le surcoût est d'environ **150 000 $ par voyage (~2-3 $/t)**. Pour un Handysize assuré 12 M$, il faut compter 12 000 à 24 000 $ de prime additionnelle.
- Sources : [Beinsure, 23/09/2026](https://beinsure.com/black-sea-war-risk-expansion-raises-shipping-insurance-costs/) ; [UkrAgroConsult, 18/09/2026](https://ukragroconsult.com/en/news/expansion-of-black-sea-war-risk-zone-could-raise-insurance-and-freight-costs/).
- La Russie est en zone listée JWC dans son ensemble (JWLA-033).
- Le dispositif **Unity** (Marsh / Lloyd's / État ukrainien) couvre les cargaisons non militaires au départ de l'Ukraine.

**Égypte**
- Importations de blé 2025/26 estimées à environ **13-13,2 Mt**, un record. La Russie est le premier fournisseur (34,6 Mt cumulées sur 5 campagnes, contre 10,4 Mt pour l'Ukraine et 9,6 Mt pour l'UE) ([Grain Brokers Australia](https://www.grainbrokers.com.au/weekly-commentary/egypts-wheat-import-demand-growing/) ; [S&P Global](https://www.spglobal.com/energy/en/news-research/latest-news/agriculture/020725-egypts-private-sector-dominates-wheat-imports-following-state-agency-changes)).
- Mostakbal Misr remplace désormais le GASC comme acheteur public.

**Prix mondiaux**
- Indice FAO des céréales : **116,3 points en août 2026**, plus haut depuis mai 2024.
- **Blé : +15 % sur un an.** La FAO cite les « perturbations persistantes de la logistique d'exportation en mer Noire » ([FAO, sept. 2026](https://www.fao.org/newsroom/detail/supply-concerns-drive-fao-food-price-index-higher/en)).
- Indice FAO global : 133,3 points (+2,5 % sur un an).

### 2.5 Soudan (guerre depuis avril 2023)

- **Port-Soudan** est devenu la capitale administrative de fait. Il a été frappé par des drones du 4 au 6/05/2025 ([ReliefWeb](https://reliefweb.int/report/sudan/drone-attacks-port-sudan-mark-dramatic-escalation)). Les drones causent plus de 80 % des morts civiles sur les 4 premiers mois de 2026 ([ONU Info, mai 2026](https://news.un.org/en/story/2026/05/1167479)).
- **Commerce agricole** ([ONU Info, juil. 2026](https://news.un.org/en/story/2026/07/1167944) ; [HCDH, rapport du 15/07/2026](https://www.ohchr.org/en/press-releases/2026/07/sudan-war-economy-sustains-conflict-un-report-warns)) :
  - exportations agricoles : **−43 %** ;
  - exportations de bétail : **−55 %** ;
  - les zones de gomme arabique, de sésame et d'arachide (Darfour, Kordofan) sont aux mains des FSR ;
  - la gomme arabique finance l'économie de guerre.
- **Assurance** : le Soudan est en zone JWC. Depuis JWLA-034, la zone mer Rouge couvre jusqu'à 25,5° N.
- **Trafic [PW]**, en escales par jour : 1,7 (2023) → 1,3 (2025) → **1,9** (août-sept. 2026). Il y a un rebond, dont la cause n'est pas établie.

### 2.6 Est de la RDC (M23) et Grands Lacs

- Goma (janv. 2025) et Bukavu (16/02/2025) sont sous contrôle du M23.
- **Diplomatie**
  - Accord-cadre de Doha : 15/11/2025.
  - Feuille de route RDC–M23 : 24/08/2026 ([Africanews](https://www.africanews.com/2026/08/24/drc-m23-agree-peace-roadmap-as-doha-talks-seek-to-regain-momentum/)).
  - Pourparlers de Genève : sept. 2026 ([Al Jazeera, 15/09/2026](https://www.aljazeera.com/news/2026/9/15/geneva-talks-put-rwanda-drc-peace-deal-to-the-test)).
  - La mise en œuvre reste incertaine.
- **Commerce**
  - La RDC absorbe plus de **20 %** des exportations rwandaises ([KT Press, sept. 2025](https://www.ktpress.rw/2025/09/dr-congo-now-takes-in-over-20-of-rwandas-exports/)).
  - Le petit commerce vivrier Goma–Gisenyi (céréales, légumineuses, légumes, huile) fait vivre au moins **22 000** petits commerçants ([International Alert](https://www.international-alert.org/publications/crossing/) — étude ancienne).
  - Le financement du M23 repose sur la taxation des flux ([The New Humanitarian, 14/09/2026](https://www.thenewhumanitarian.org/analysis/2026/09/14/how-rwanda-backed-m23-rebels-finance-their-war-dr-congo)).
- **Implication** : les corridors Nord (Mombasa) et Central (Dar) vers l'est de la RDC subissent une double taxation (autorités et rebelles). Le SaaS n'en tient pas compte.

### 2.7 Sahel : AES, blocus du JNIM et corridors côtiers

**Rupture institutionnelle**
- La sortie de la CEDEAO est effective au 29/01/2025.
- L'AES applique un **prélèvement de 0,5 %** sur les importations en provenance de pays sans accord douanier, y compris la CEDEAO. Le transit en est exonéré ([allAfrica, 02/04/2025](https://allafrica.com/stories/202504020030.html) ; [Amani Africa](https://amaniafrica-et.org/the-withdrawal-of-aes-from-ecowas-an-opportunity-for-re-evaluating-existing-instruments-for-regional-integration/)).

**Blocus du JNIM** ([ISS Africa, 04/06/2026](https://issafrica.org/iss-today/jnim-s-blockade-tactics-threaten-west-africa-s-trade-corridors) ; [ADF, juil. 2026](https://adf-magazine.com/2026/07/mali-blockade-has-regional-impact/))
- **Début** : annoncé le 03/09/2025.
- **Pertes matérielles** : **plus de 300 camions-citernes détruits** sur les axes Sénégal, Côte d'Ivoire et Guinée, qui apportent 95 % du carburant du Mali.
- **Conteneurs bloqués**
  - De sept. à nov. 2025, **~120 conteneurs par jour** à destination du Mali étaient bloqués à Dakar.
  - Fin nov. 2025, **plus de 2 000 conteneurs** étaient immobilisés à Dakar.
  - En févr. 2026, **~4 000 conteneurs vides** étaient bloqués à Bamako.
- **Coût pour le Sénégal** : perte estimée à **15 Md FCFA par mois (~26,5 M$)**. Le Mali représentait 26,5 % des exportations sénégalaises en 2024.
- **Axe Abidjan–Bamako** : ~1,47 Mt en 2025.
- **Escalade et adaptation**
  - Attaques coordonnées le 25/04/2026.
  - Blocus des routes ouest de Bamako depuis le 30/04/2026.
  - Convois escortés de 200 à 300 citernes par semaine depuis nov. 2025.
- **Agroalimentaire** : **7 commerçants de tomates ghanéens tués** le 14/02/2026 à Titao (Burkina Faso). Le flux tomate Burkina → Ghana est directement menacé.

**Implication pour le SaaS** : les coûts Dakar–Bamako (128 $/t) et Tema–Ouaga–Bamako (159 $/t) du §1.4 sont des coûts « en paix ». Il faudrait appliquer une prime d'insécurité (escorte, attente, casse) — non modélisée.

### 2.8 Golfe de Guinée : piraterie

- **IMB, S1 2026** : **2 incidents seulement** dans le golfe de Guinée, dont une tentative d'abordage au mouillage de San Pedro (Côte d'Ivoire). Au niveau mondial, 38 incidents, le plus bas depuis 1992 (90 au S1 2025, 60 au S1 2024) ([MaritimeCyprus, 03/08/2026](https://maritimecyprus.com/2026/08/03/icc-imb-world-wide-incidents-of-piracy-and-armed-robbery-against-ships-report-from-jan-to-june-2026/)).
- **Pourtant la zone reste listée par le JWC** (JWLA-033) : Nigeria, Bénin, Togo, plus les eaux du golfe de Guinée depuis la côte togolaise (1°12' E) jusqu'au cap Lopez (Gabon, 8°42' E).
- **Conséquence pour le cacao** : Abidjan, San Pedro, Tema et Takoradi sont **à l'ouest** de la zone listée. Lomé, Cotonou, Lagos et Douala sont **dedans**.

### 2.9 Mozambique : Cabo Delgado

- **Zone JWC** (JWLA-033) : mer territoriale du Mozambique et de la Tanzanie, de la baie de Mnazi (10°19,6' S) à la baie de Lúrio (13°30' S). Le port de **Pemba (~12°58' S) est dans la zone**. Nacala (14°32' S, corridor Nacala du SaaS) est au sud, donc **hors zone**.
- **Situation** : l'insurrection de l'État islamique se poursuit en 2026. Le bilan dépasse 6 200 morts et 1,1 M de déplacés. Les attaques sont quasi hebdomadaires ([Soufan Center, 20/05/2026](https://thesoufancenter.org/intelbrief-2026-may-20/) ; [ISS](https://issafrica.org/iss-today/cabo-delgado-insurgency-persists-amid-failed-military-strategy)).

### 2.10 Libye

- Le pays est en zone JWC.
- Il y a des sabotages et des affrontements à Tripoli et Zawiya, et des blocages pétroliers récurrents de l'Est (Haftar).
- Un méthanier, l'« Arctic Meta Gas », a été attaqué le 03/03/2026 au large de Benghazi ([NorthStandard](https://north-standard.com/insights-and-resources/resources/news/libya-port-situation-and-safe-navigation) ; [Al Jazeera, 06/04/2026](https://www.aljazeera.com/amp/news/2026/4/6/libyas-oil-disputes-mirror-hormuz-crisis-fuel-european-energy-fears)).
- Le SaaS indique 120 h d'attente au port de Tripoli (sans source).

### 2.11 Zones listées par le JWC (Lloyd's) : Afrique et routes africaines

Source : texte intégral de la circulaire **JWLA-033 du 03/03/2026** ([PDF LMA](https://lmalloyds.com/wp-content/uploads/2026/03/JWLA-033_Iran.pdf)), complété par JWLA-034 (29/07/2026) et JWLA-035 (16/09/2026).

| Zone listée | Pertinence agroalimentaire africaine |
|---|---|
| **Bénin, Nigeria, Togo** ; eaux du golfe de Guinée (Togo 1°12' E → 0°40' S 3° E → cap Lopez 8°42' E) | Importations de riz, blé et sucre à Lagos, Cotonou et Lomé ; transit vers le Sahel |
| **Cabo Delgado** (10°19,6' S - 13°30' S) | Pemba ; côte sud de la Tanzanie (Mtwara : noix de cajou) |
| **Djibouti** (ajouté le 03/03/2026) | Blé et engrais pour l'Éthiopie ; café éthiopien à l'export |
| **Érythrée** (seulement au sud de 18° N) ; **Somalie** ; **Soudan** ; **Libye** | Bétail (Berbera, Bosaso) ; gomme arabique et sésame (Port-Soudan) |
| **Golfe Persique, golfe d'Oman, océan Indien, golfe d'Aden, sud de la mer Rouge**. Limites : NO = mer Rouge au sud de 18° N, portée à **25,5° N** par JWLA-034 ; E = 65° E ; SO = frontière somalienne (1°40' S, 41°34' E) → 6°45' S, 48°45' E | Toutes les routes Asie/Golfe ↔ Afrique de l'Est qui passent par le nord-ouest de l'océan Indien |
| **Pakistan** (Asie) | 1er marché du thé kényan (39 % au T1 2026) |
| Arabie saoudite (côte de la mer Rouge, hors transit), Yémen, Iran, Irak, Israël, EAU, Oman, Qatar, Koweït, Bahreïn | Débouchés : bétail vers l'Arabie saoudite, fleurs et fruits vers les EAU ; importations d'engrais et de carburant |
| **Mer Noire et mer d'Azov** (quasi entière depuis JWLA-035) ; **Russie** | Blé russe et ukrainien pour l'Égypte, l'Algérie, la Libye, le Soudan et l'Afrique de l'Est |

**Rappel** : un port ou une zone listé(e) n'a pas de taux unique. Selon la circulaire, l'application « relève d'une négociation spécifique ». La prime additionnelle est fixée par voyage et notifiée à l'avance (« held covered »).

### 2.12 Assurance-crédit, risque politique et financement du commerce

**ATIDI** (African Trade & Investment Development Insurance, ex-ATI) — exercice 2025 ([Birr Metrics](https://birrmetrics.com/atidi-profit-jumps-20-as-insured-exposure-grows-just-3/) ; [Financial Nigeria](https://www.financialnigeria.com/atidi-s-financial-results-highlight-rising-role-in-african-investment-news-3039.html)) :
- exposition brute de **9,2 Md$** (8,9 Md$ en 2024) ;
- bénéfice de 71,4 M$ (+20 %) ;
- actifs de 1,06 Md$ ;
- fonds propres de 883 M$ ;
- **plus de 93 Md$** de commerce et d'investissement facilités depuis la création ;
- 24 États membres africains ;
- risques couverts : expropriation, inconvertibilité, embargo, **violence politique**, terrorisme, défaut de sentence arbitrale.

**Déficit de financement du commerce (BAD)**
- Rapport « Trade Finance Supply in Africa: Post-COVID Trends and Emerging Opportunities », publié le 29/05/2026 ([MSME Africa](https://msmeafricaonline.com/afdb-warns-africas-trade-finance-gap-could-hit-86-6bn-threatening-smes-and-regional-trade/) ; [allAfrica](https://allafrica.com/stories/202605290298.html)).
- Déficit de **74 à 92 Md$ en 2024**, soit 5,4 % du commerce de marchandises.
- Projection 2027 : **86,6 Md$** en scénario modéré et **102,6 Md$** en scénario sévère. Les causes citées sont le conflit au Moyen-Orient, Ormuz, l'énergie et le fret.
- Taux d'approbation des demandes des PME : **63 %**, contre 80 % en moyenne.
- 36 % des banques citent le manque de devises comme premier frein.
- Référence antérieure : 81,8 Md$ en 2019 (BAD-Afreximbank 2020).

---

## 3. Coûts du fret 2025-2026

### 3.1 Indice mondial conteneurs : Drewry WCI ($ par FEU)

- **24/09/2026 : 4 468 $** (−1 % sur la semaine).
- Shanghai–Rotterdam : **3 485 $** (−4 %). Shanghai–Gênes : 3 835 $ (−5 %).
- Shanghai–Los Angeles : 7 838 $. Shanghai–New York : 10 373 $.
- Transits de Suez selon Drewry : 41 en semaine 37 et 48 en semaine 38. Selon Drewry, ce surcroît de capacité l'emporte sur les 7 annulations de départ.
- Source : [Drewry WCI, 24/09/2026](https://www.drewry.co.uk/supply-chain-advisors/supply-chain-expertise/world-container-index-assessed-by-drewry).
- Série de septembre 2026 : 4 465 $ (03/09), 4 476 $ (10/09), 4 500 $ (17/09), 4 468 $ (24/09).

### 3.2 Taux vers et depuis l'Afrique (2026)

**Asie → Mombasa**
- **5 130 à 6 270 $/FEU** en juillet 2026, soit +33 % par rapport à juin (transitaire [Sino-Shipping, mise à jour sept. 2026](https://www.sino-shipping.com/freight-china-kenya/) — source secondaire).
- **Surcharge haute saison (PSS) Maersk Chine/Hong Kong → Mombasa** de **1 000 $/20'** et **2 000 $/40'**, au 15/06/2026 ([The EastAfrican](https://www.theeastafrican.co.ke/tea/business-tech/shipping-major-raises-freight-fees-on-china-originating-cargo-5487044) — résumé).
- MSC a annoncé de nouveaux tarifs Extrême-Orient → Afrique et océan Indien en mars 2026 ([MSC](https://www.msc.com/en/newsroom/customer-advisories/2026/march/price-announcement-trade-far-east-to-africa-and-indian-ocean) — page inaccessible, 403).

**Chine → Nigeria** : **3 150 à 3 850 $ par 40'** en juin 2026 (transitaire [Tonlexing](https://www.tonlexing.com/20ft-40ft-container-shipping-costs-from-china-to-nigeria/) — secondaire).

**Comparaison intra-africaine (SaaS, 2024)**
- Mombasa–Durban : 900 $/EVP. Abidjan–Lagos : 380 $/EVP.
- À comparer avec les 5-6 k$/FEU Asie → Mombasa en 2026.
- Les segments intra-africains courts restent peu chers **en fret de base**. Mais les échanges Nord ↔ Est (Égypte/Maroc ↔ Kenya/Tanzanie) passent par la zone de crise (voir §6.3).

**Poids du transport dans la valeur des importations (CNUCED)**
- Afrique : **11,4 %**, contre 6,8 % pour les pays développés (moyenne 2005-2014). C'est la région la plus chère ([CNUCED](https://unctad.org/press-material/114-cent-value-imports-african-countries-paid-more-international-transport-any-other)).
- Dans 31 pays d'Afrique subsaharienne sur 43, le fret à l'import est 50 % plus cher que la moyenne des pays en développement.
- Pour certains pays enclavés d'Afrique centrale, il dépasse **45 %** de la valeur des importations ([CNUCED, Afrique centrale](https://unctad.org/news/why-transit-goods-so-expensive-central-africa)).

**Effet macro du déroutement (CNUCED RMT 2025)**
- Tonnes-milles : **+5,9 % en 2024**, trois fois la croissance des volumes.
- Distance moyenne parcourue : 4 831 milles en 2018, **5 245 milles en 2024**.
- Tonnage transitant par Suez début mai 2025 : **~70 % sous la moyenne de 2023** ([CNUCED RMT 2025](https://unctad.org/system/files/official-document/rmt2025_en.pdf)).

### 3.3 Surcharges des armateurs en 2026 (guerre, carburant, ETS)

| Surcharge | Montant | Date d'effet | Source |
|---|---|---|---|
| Hapag-Lloyd, surcharge risque de guerre (Golfe) | **1 500 $/EVP** ; **3 500 $ par reefer** ou équipement spécial | 02/03/2026 | [Lloyd's List](https://www.lloydslist.com/LL1156482/Carriers-rush-to-impose-war-risk-surcharges-as-Middle-East-crisis-deepens) (résumé) |
| CMA CGM, surcharge d'urgence « conflit » (Golfe) | **2 000 $/EVP ; 3 000 $/FEU ; 4 000 $ par reefer** | 02/03/2026 | idem |
| Maersk, surcharge d'urgence (Golfe et sous-continent indien → Europe/Méditerranée) | n.d. | 15/03/2026 | idem |
| CMA CGM, surcharge carburant d'urgence (long-courrier, sens principal) | **150 $/EVP**, relevée à **265 $/EVP** 11 jours plus tard | 16/03/2026 puis ~27/03/2026 | [Tradlinx](https://blogs.tradlinx.com/emergency-fuel-surcharges-in-april-2026-what-changed-since-march-and-where-the-inland-cost-wave-hits-next/) |
| Maersk, surcharge soutes d'urgence, **sur tout le réseau** (Afrique comprise) | n.d. | 25/03/2026 | [Bunker Index](https://www.bunkerindex.com/articles/article.php?a=22508&h=maersk-introduces-emergency-bunker-surcharge-amid-middle-east-fuel-crisis) |
| MSC, ONE : surcharges carburant d'urgence | n.d. | 9-25/03/2026 | Tradlinx |
| **EU ETS** : 100 % des émissions couvertes en 2026 (70 % en 2025), plus CH4 et N2O | Maersk Asie → Europe du Nord ≈ **59 €/EVP** au T1 2026. Hausse de 40-50 % par rapport à 2025 ; Hapag-Lloyd annonce ~+45 %. Shanghai → Rotterdam ≈ 168 $/FEU | 01/01/2026 | [Maersk](https://www.maersk.com/news/articles/2025/12/01/emissions-surcharge-ems-ess) ; [Hapag-Lloyd](https://www.hapag-lloyd.com/en/services-information/news/2025/11/update-on-the-european-emission-trading-system--eu-ets----full-i.html) ; [Searoutes](https://searoutes.com/en/blog/eu-ets-shipping-surcharges-impact) |

**Portée de l'ETS pour l'Afrique** : pour un trajet entre un port hors UE (Mombasa, Abidjan) et un port de l'UE, **50 %** des émissions sont soumises au système (règle ETS maritime). Montants par EVP sur les liaisons Afrique ↔ UE : **non trouvés**.

### 3.4 Fret aérien (voir aussi le §7)

**Marché mondial**
- Baltic Air Freight Index (BAI00) au 21/09/2026 : **+20,9 % sur un an**.
- Kérosène : **+116,5 % sur un an** au 18/09/2026 (moniteur IATA).
- TAC Index : la hausse du carburant « n'est pas encore pleinement répercutée ».
- Source : [Air Cargo News, 22/09/2026](https://www.aircargonews.net/data/2026/09/airfreight-rates-strong-as-peak-season-approaches/).

**Fleurs kényanes** (AP / [Morning Ag Clips, 25/03/2026](https://www.morningagclips.com/kenyas-flower-industry-loses-millions-of-dollars-weekly-due-to-the-iran-war/))
- Fret aérien vers l'Europe : **5 $/kg**, avec un pic à **5,80 $/kg**, « le plus haut en 10 ans ». C'est environ **le double** du niveau habituel (~2,50 $/kg).
- Pertes : **jusqu'à 1,4 M$ par semaine**, soit 4,2 M$ en trois semaines.
- Filière d'environ **800 M$ par an**. Europe : 70 % des débouchés ; Moyen-Orient direct : 15 %.

**Éthiopie** : Ethiopian Airlines relève de **20 %** ses tarifs « PEF » (périssables) du 08/04/2026 au 31/12/2026, en invoquant le carburant, l'**assurance** et l'exploitation ([Hortidaily, 05/05/2026](https://www.hortidaily.com/article/9834952/ethiopian-airlines-raises-air-freight-tariffs-20-percent-on-perishable-exports/)).

---

## 4. Implications concrètes pour les filières agricoles

**Méthode.** Les cas combinent les modèles du SaaS (§1), les données PortWatch et les primes observées (§2). Les hypothèses sont signalées par « H: ».
- Surprime en $/t = valeur de coque × taux ÷ tonnes transportées.
- Valeurs de coque retenues à titre d'hypothèse : Supramax ≈ 28 M$ ; porte-conteneurs ≈ 40-50 M$. **Ce sont des ordres de grandeur, pas des cotations.**

### 4.1 Blé : Djibouti / Éthiopie, Soudan, Égypte

**Djibouti depuis Novorossiïsk, en Supramax de 55 000 t**

| Poste | Via Suez | Via le Cap |
|---|---|---|
| Distance [CALC searoute] | 2 613 nm | 11 534 nm |
| Allongement | — | ×4,4 ; +26,6 jours à 14 nœuds |
| Fret, modèle SaaS × multiplicateur 1,3415 | **19 $/t** | **58 $/t** |
| Surcoût de fret par rapport à Suez | — | **+39 $/t** |

- La route du Cap n'est pas réaliste pour Djibouti, qui est à l'entrée de Bab el-Mandeb. **L'arbitrage réel consiste donc à accepter la surprime.**
- **Surprime de guerre (H: coque 28 M$)** :

  | Taux | Coût par voyage | Coût par tonne |
  |---|---|---|
  | 0,05 % (avant crise) | 14 k$ | **0,25 $/t** |
  | 0,5 % (Bab el-Mandeb, juil. 2026) | 140 k$ | **2,5 $/t** |
  | 1 % (pic) | 280 k$ | **5,1 $/t** |

- Il faut y ajouter la prime spécifique à l'escale depuis que **Djibouti est listé (03/03/2026)** — non chiffrée.
- Rapporté à un blé CIF d'environ 255 $/t (Alexandrie, 2025, non vérifié ; pour comparaison, blé US HRW à 243 $/t en moyenne 2025 selon le Pink Sheet de la Banque mondiale), la surprime ajoute **+1 à +2 %** au coût rendu. Un déroutement ajouterait environ **+15 %**, auxquels s'ajoutent les surcharges carburant.
- **Le modèle SaaS ne voit ni l'un ni l'autre.**

**Égypte (Novorossiïsk–Alexandrie)**
- Distance : 1 173 nm. Fret modèle SaaS : ~13 $/t en Supramax, ~16 $/t en Handysize. L'écart observé Russie–Égypte était d'environ 15 $/t (2025, non vérifié).
- Surprime mer Noire : ~1 % pour les ports ukrainiens (+2-3 $/t). Pour les ports russes, 0,6-0,8 % fin 2025, avant l'extension du 16/09/2026.
- **Ordre de grandeur [CALC]** : +2 à 3 $/t sur 13 Mt importées, soit **26 à 39 M$ par an** de surcoût d'assurance pour l'Égypte. C'est un plafond, si tout venait de ports à prime pleine.
- Le blé mondial est à +15 % sur un an (FAO, août 2026).

### 4.2 Thé kényan : Égypte, Pakistan, Royaume-Uni

**Mombasa–Alexandrie**

| Poste | Via Suez | Via le Cap |
|---|---|---|
| Distance [CALC] | 3 266 nm | 9 503 nm (+191 %) |
| Délai supplémentaire | — | **+18,6 jours** à 14 nœuds |
| Modèle SaaS (EVP) | ~1 010 $ ; benchmark SaaS 745 $ | ~2 600 $ |
| Surcoût par EVP | — | **+1 600 à 1 850 $** |

- Avec 20 t de thé par EVP (hypothèse), cela fait **+0,08-0,09 $/kg**, soit environ **+4 %** du prix moyen du thé à Mombasa en 2025 (**2,15 $/kg**, [Banque mondiale, Pink Sheet](https://www.worldbank.org/en/research/commodity-markets), série « Tea, Mombasa » ; 2,18 $ en 2024).
- Référence : en 2024, un 40' Mombasa–Russie est passé de 2 442 à 6 513 $ (×2,7), et le prix du thé premium de 3,03 à 4,10 $/kg ([Food Business Africa, 14/03/2024](https://www.foodbusinessafrica.com/cost-of-tea-export-surges-as-shipping-delays-hit-mombasa-port/)).

**Pakistan (39 % des exportations au T1 2026, 56,47 Mkg)**
- Pas de passage par Suez : Mombasa–Karachi fait 2 411 nm.
- Mais **le Pakistan et le nord-ouest de l'océan Indien sont en zone JWC** (JWLA-033). S'y ajoutent les surcharges carburant d'urgence (§3.3).
- Source : [Food Business MEA](https://www.foodbusinessmea.com/kenya-tea-exports-rise-6-in-q1-2026-as-pakistan-strengthens-lead/).

**Moyen-Orient (Iran, EAU)**
- 20 à 25 % des exportations, soit environ 100 Mkg par an.
- **Exportations à l'arrêt** en mars 2026 ; pertes d'environ **8 M$ par semaine** depuis le 01/03/2026.
- Les envois vers le Pakistan et l'Égypte sont déroutés par le Cap ([MarineLink, 01/04/2026](https://www.marinelink.com/blogs/blog/kenyan-tea-exports-affected-by-iran-conflict-as-stocks-104468)).

### 4.3 Fleurs coupées (Kenya, Éthiopie) et autres périssables aériens

**Fret aérien Nairobi → Europe**
- 2,5 $/kg → **5-5,8 $/kg** (mars 2026), soit **+100 à +130 %**.
- [CALC] Pour une ferme qui expédie 1 t par jour, le surcoût est de **2 500 à 3 300 $ par jour**.

**Kérosène [FRED]**
- 89 $/b en 2025, 184 $/b en sept. 2026 (+107 %).
- La FSC du SaaS, figée à 0,65 $/kg, est **obsolète**. En supposant une FSC proportionnelle au kérosène, elle serait d'environ 1,3 $/kg (H:, non observé).

**Éthiopie** : +20 % sur les tarifs périssables (avril-décembre 2026).

**Capacité** : l'offre vers le Kenya aurait baissé de **30 %**, et celle du monde de 18-20 % (floriculture.co.ke, via résumé — voir §5). Les compagnies du Golfe (Emirates, Qatar), fortement présentes sur l'Afrique de l'Est, sont touchées par les restrictions d'espace aérien et de carburant (analyse).

**Mer comme alternative** (avocats, haricots, mangues)
- Mombasa–Rotterdam fait 6 393 nm par Suez contre **8 771 nm par le Cap** (+2 378 nm, +7 jours).
- Pour les avocats, le transit dépasse 32 jours et un conteneur pour l'Europe coûte environ 3 000 $, contre 2 000 $ avant (résumé [FreshPlaza](https://www.freshplaza.com/north-america/article/9828645/the-kenyan-avocado-export-campaign-is-moving-forward-under-difficult-conditions/) — non vérifié).
- Le basculement des fleurs vers la mer reste limité par leur durée de vie.

### 4.4 Café éthiopien et importations de l'Éthiopie via Djibouti

- **96,7 %** du trafic maritime éthiopien passe par Djibouti (exercice 2025/26).
- Recette record du café : **3,0 Md$** en 2025/26, soit ~28 % des exportations ([Mereja](https://mereja.com/index/598798) — secondaire).
- **Distances [CALC]** : Djibouti–Rotterdam fait 4 669 nm par Suez contre **10 365 nm par le Cap** (+5 696 nm, **+17 jours**). Le fret aller-retour a triplé.
- **Surcoûts à l'import** : environ **+1 500 $ par 20'**, et jusqu'à **2 000 $ par boîte** avec la surprime de guerre et les surcharges d'urgence ([Mereja](https://mereja.com/index/599009) — secondaire).
- **Port de Djibouti** ([Banque mondiale, MPO avril 2026](https://thedocs.worldbank.org/en/doc/65cf93926fdb3ea23b72f277fc249a72-0500042021/related/mpo-dji.pdf)) :
  - EVP **−10,5 % au S1 2025** et **−17,5 % au S2 2025** ;
  - la Banque mondiale juge Djibouti plus vulnérable à un choc combiné pétrole + activité portuaire ;
  - le corridor éthiopien reste le stabilisateur.
- Djibouti avait d'abord profité du transbordement : le terminal de Doraleh a fait +77 % au S1 2024, à ~650 000 EVP ([Lloyd's List](https://www.lloydslist.com/LL1150516/Red-Sea-reroutings-uproot-traditional-transhipment-trends) — résumé).
- **Engrais** : l'Éthiopie importe son urée par Djibouti. Le choc sur l'urée (§2.3) touche directement la campagne.

### 4.5 Bétail de la Corne de l'Afrique et du Soudan vers l'Arabie saoudite

- **Jeddah [PW]** : escales par jour de 11,3 (2023) → 8,4 (2025) → **2,9 en août-sept. 2026** (**−74 %**). Porte-conteneurs : 6,5 → 1,3. Volumes estimés : 82 → 18 Mt par an en rythme annualisé.
- Cause : blocus houthi des navires liés à l'Arabie saoudite (21/07/2026) et extension JWC à 25,5° N (29/07/2026).
- **Implication** : le bétail vivant de Berbera, Bosaso, Djibouti et Port-Soudan vers Jeddah, marché clé du Hajj, est directement menacé. Les primes pour les ports saoudiens atteignent 3 à 7 %.
- Les exportations soudanaises de bétail ont déjà baissé de 55 %.
- Berbera [PW] reste stable à ~1 escale par jour.

### 4.6 Agrumes sud-africains

- Le Moyen-Orient absorbe normalement **~20 %** des exportations.
- Prévision CGA ramenée de 209,4 à **205,3 M de cartons de 15 kg** (−2 %), à cause des inondations et de la guerre.
- Hausse des surcharges soutes ; surcharges **doublées** sur certaines routes ; moins de navires disponibles.
- Sources : [BusinessDay, 06/08/2026](https://www.businessday.co.za/economy/2026-08-06-floods-and-middle-east-conflict-dent-south-africas-citrus-export-outlook/) ; [Fruitnet](https://www.fruitnet.com/eurofruit/south-africa-cuts-citrus-forecast-amid-seasonal-challenges/272382.article).
- Durban [PW] : 5,8 escales par jour en août-sept. 2026, contre 7,0 en 2025.

### 4.7 Cacao (Côte d'Ivoire, Ghana)

- **Pas d'exposition à Suez** vers l'Europe. Les ports d'embarquement (Abidjan, San Pedro, Tema, Takoradi) sont **hors de la zone JWC** du golfe de Guinée.
- Les surcoûts sont surtout **carburant** et **ETS** : surcharge d'urgence CMA CGM de 150 à 265 $/EVP, plus l'ETS sur 50 % des émissions vers l'UE.
- [CALC] Avec 12,5 t de fèves par EVP (H:), la surcharge carburant représente **~12 à 21 $/t**, soit **0,2-0,3 %** d'un cacao à 7 800 $/t (moyenne 2025 de la Banque mondiale). L'impact est marginal par rapport au prix.
- Les exportations vers les broyeurs asiatiques passent déjà par le Cap.
- Abidjan [PW] : escales par jour de 4,4 (2023) → 5,6 (2025) → 5,2 (2026) ; volumes estimés de 18 → 29 Mt/an.

### 4.8 Huile de palme (importations)

- **Afrique de l'Ouest** : Malaisie/Indonésie → Lagos passe par le Cap (8 303 nm). **Pas d'exposition à Bab el-Mandeb**, mais la surcharge soutes s'applique et Lagos est en zone JWC.
- **Égypte, Soudan, Djibouti** : les importations transitent par Bab el-Mandeb.
- [CALC] Pour un chimiquier/produits de 35 000 t (H: coque 40 M$) avec une surprime de 0,5 %, le surcoût est de **~5,7 $/t**. Il atteint environ 11 $/t à 1 %. Cela représente **+0,6 à 1,1 %** d'une huile de palme à ~1 007 $/t (moyenne 2025 de la Banque mondiale).
- **Afrique de l'Est** (Mombasa, Dar) : route directe sur l'océan Indien, **à la limite de la zone JWC** (ligne 10°48' N / 60°15' E → 6°45' S / 48°45' E). À vérifier cas par cas.

### 4.9 Engrais

- **Prix de l'urée** : 455-470 $/t (27/02/2026) → 725,6 $ (moyenne de mars) → plus de 850 $ (avril) → 453 $ (juin).
- **Référence d'avant-crise (Banque mondiale, Pink Sheet)** : urée à 338 $/t en moyenne 2024 et 423 $/t en 2025 ; DAP à 564 puis 685 $/t.
- **Ormuz est de nouveau quasi fermé** : 3,9 à 4,7 navires par jour en août-sept. 2026 [PW].
- Risque de **nouvelle flambée** pendant la campagne des petites pluies en Afrique de l'Est (oct.-déc.) (analyse).
- Les fonds Afreximbank (GCRP, 10 Md$) et BAD (5,1 Md$) sont les instruments disponibles.
- Le phosphate marocain (OCP) constitue une alternative intra-africaine pour le P, pas pour le N (analyse).

### 4.10 Commerce intra-africain Nord ↔ Est (ZLECAf)

**Distances [CALC]**

| Liaison | Via Suez | Via le Cap | Écart |
|---|---|---|---|
| Tanger Med–Mombasa | 5 017 nm | 7 706 nm | +54 % |
| Alexandrie–Mombasa | 3 266 nm | 9 503 nm | +191 % |

- Les routes « benchmark » du SaaS (Port-Saïd–Mombasa à 720 $/EVP « via Suez ») sont donc **les plus exposées**.
- **Recommandation** : dans le rapport, présenter les tarifs SaaS Nord ↔ Est comme des niveaux « hors crise ». Leur associer un scénario « Cap + surcharges ».

### 4.11 Sahel enclavé (Mali, Burkina Faso, Niger)

- Le coût SaaS Dakar–Bamako (128 $/t, 6-8 jours) ne reflète pas :
  - les convois escortés ;
  - les 120 conteneurs par jour bloqués (fin 2025) ;
  - le prélèvement AES de 0,5 %.
- Le coût réel n'est **pas mesuré**. Seules des pertes agrégées sont connues : 15 Md FCFA par mois pour le Sénégal.
- **Recommandation** : afficher les corridors sahéliens avec un **indicateur de risque qualitatif** plutôt qu'un coût.

---

## 5. Chiffres non vérifiés ou à recouper

**Assurance et trafic**
1. **Surprime mer Rouge avant la crise (0,05 %) et en 2024 (0,7-1 %)** : lue dans un résumé de recherche (S&P Global / Reuters). L'article source n'a pas été ouvert (403).
2. **« 1-3 % à Ormuz avant la guerre »** (Al Jazeera, 23/07/2026) : ce niveau paraît élevé pour la période d'avant 2025. Il s'agit probablement de la période qui a suivi la guerre de juin 2025. À préciser.
3. **Recettes du canal de Suez par exercice.**
   - Le résumé d'Egyptian Streets donne « 2023/24 : 9,4 Md$ ». Il s'agit probablement de 2022/23 : le chiffre couramment cité pour 2023/24 est 7,2 Md$ (−23 %) ([The National, 18/07/2024](https://www.thenationalnews.com/business/2024/07/18/egypts-suez-canal-revenue-fell-23-in-last-fiscal-year-due-to-houthi-attacks/)).
   - Pour 2025/26, « +23 % » est incohérent avec 3,9 → 4,67 Md$, qui donne +19,7 %.
   - Années civiles : 2023 = 10,25-10,3 Md$ ; 2024 ≈ 4,0 Md$ (−61 %) ; 2025 ≈ 4,2 Md$ attendus ([Euronews, 17/04/2025](https://euronews.com/business/2025/04/17/egypts-suez-canal-revenue-fell-sharply-in-2024-on-regional-tensions) ; [Business Today Egypt](https://www.businesstodayegypt.com/Article/1/6885/Suez-Canal-revenues-expected-to-reach-4-2B-in-2025)).
4. **Nombre de navires à Suez** : 13 213 en 2024 contre plus de 26 000 en 2023 (Euronews, via résumé).
5. **« 2,5 M EVP absorbés par le Cap »** (Air Cargo News, 02/03/2026) et **« 6 % de la capacité mondiale »** (résumé d'une source secondaire).
6. **Record de 24 M tpl au Cap fin avril 2026** : source secondaire (euroluminant), non vérifiée. Les données PortWatch du §6.1 la remplacent.

**Carburant et coûts de déroutement**
7. **Surcoût carburant du Cap** : +932 905 $ par voyage pour un pétrolier Asie → Europe du Nord ([SAFETY4SEA](https://safety4sea.com/an-extra-million-is-added-each-time-a-tanker-goes-around-cape-of-good-hope/)). Pour un porte-conteneurs de 24 000 EVP, 1,5-2,0 M$ par boucle (source non identifiée). Consommation +30 % par voyage.

**Fret et produits**
8. **Taux Asie → Mombasa (5 130-6 270 $/FEU) et Chine → Nigeria (3 150-3 850 $)** : transitaires, pas un indice.
9. **Attente de 14 à 21 jours à Lagos** (blog Great Hensen) : non fiable. PortWatch ne montre pas de rupture d'escales à Lagos (4,9 à 5,4 par jour).
10. **Fret des fleurs à 5,70 $/kg contre 2,40 $/kg l'année précédente** et **−30 % de capacité vers le Kenya** : floriculture.co.ke / Streamlinefeed, via résumé (page en erreur 425). La donnée AP (5-5,8 $/kg contre ~2,5) est plus sûre.
11. **Avocats kényans** : 3 000 $ contre 2 000 $ par conteneur et plus de 32 jours (résumé, source floue).
12. **Café éthiopien** : 3,0 Md$ ; 96,7 % via Djibouti ; +1 500 à 2 000 $ par boîte (Mereja, agrégateur).
13. **Blé CIF Alexandrie à 255 $/t et écart de fret Russie–Égypte de 15 $/t** : résumé de recherche, période exacte non confirmée.
14. **Prix de l'urée en septembre 2026** : non trouvé. Les données Investing/CME affichées ne sont pas datées.

**Carburant marine et aérien**
15. **VLSFO à fin septembre 2026 (Singapour 740 $, Rotterdam 621 $)** : OilPriceAPI, date exacte non confirmée. Le point du 18/08/2026 (ShipUniverse) est plus sûr.
16. **Kérosène IATA mondial à 194,90 $/b (semaine au 18/09/2026) et prévision IATA 2026 de 152 $/b** : résumé de recherche. La page IATA n'a pas été ouverte. Le +116,5 % sur un an est confirmé par Air Cargo News.

**Chronologie Iran**
17. **Chronologie des cessez-le-feu** : plusieurs sources divergent sur les dates d'accord (08/04, cessez-le-feu de 60 jours, 17/06). La fiche Wikipedia est tertiaire.

**Données du SaaS**
18. **Aéroports** : NBO 285 kt, ADD 520 kt, etc. pour 2024 — non recoupés. **Ports** : les EVP 2024 sont sans source pour la plupart des ports (champ `source` à None). **Trafic** : séries générées par gabarit (ratio 800).
19. **Corridors** : les transits (Northern Corridor à 36 h) et les volumes n'ont pas été recoupés avec les observatoires (NCTTCA, CCTTFA, OPA-BICC). La source « Transrail SA » pour Dakar–Bamako est douteuse.
20. **Frontière Bénin–Niger** : présumée fermée depuis 2023. Son statut en 2026 n'a pas été vérifié ici.
21. **Hypothèses de valeur de coque** (Supramax 28 M$, chimiquier 40 M$) et de **chargement** (20 t de thé, 12,5 t de cacao par EVP) : ce sont des hypothèses de calcul.

---

## 6. Déroutement Suez / Bab el-Mandeb → Cap de Bonne-Espérance (sous-section dédiée)

### 6.1 Trafic aux points de passage : moyennes journalières [PW]

Source : [IMF PortWatch](https://portwatch.imf.org/), jeu `Daily_Chokepoints_Data`. Calculs de l'auteur ; données jusqu'au 20/09/2026. La capacité correspond au **tonnage de port en lourd (tpl) transitant par jour, en millions de tonnes**.

| Point de passage | 2023 (janv.-oct., avant crise) | 2024 | 2025 | T1 2026 (janv.-mars) | Juin 2026 | Août 2026 | **1-20 sept. 2026** | Écart sept. 2026 / 2023 |
|---|---|---|---|---|---|---|---|---|
| **Suez**, tous navires | 73,6 | 39,6 | 38,5 | 39,1 / 41,4 / 41,0 | 40,4 | 41,0 | **41,0** | −44 % |
| Suez, porte-conteneurs | 19,6 | 8,7 | 9,2 | 9,0 / 8,7 / 9,0 | 8,4 | 9,3 | **11,1** | −43 % |
| Suez, vraquiers | 19,3 | 11,7 | 9,8 | ~10 | 12,1 | 10,0 | 9,1 | −53 % |
| Suez, Mt tpl par jour | 3,36 | 1,34 | 1,39 | ~1,4 | 1,59 | 1,38 | 1,57 | −53 % |
| **Bab el-Mandeb**, tous navires | 74,6 | 32,5 | 33,5 | 33,5 / 36,8 / 35,5 | 36,6 | 27,4 | **25,9** | **−65 %** |
| Bab el-Mandeb, porte-conteneurs | 19,3 | 5,4 | 6,7 | 6,1 / 5,8 / 5,2 | 5,5 | 4,5 | 5,3 | −73 % |
| Bab el-Mandeb, pétroliers | 26,2 | 11,6 | 11,5 | ~13-15 | 13,8 | 8,5 | 7,3 | −72 % |
| **Cap de Bonne-Espérance**, tous navires | 48,9 | 87,0 | 89,5 | 87,7 / 87,0 / 91,3 | 92,8 | 90,3 | 86,1 | **+76 %** (pic en mai 2026 : 96,9, soit +98 %) |
| Cap, porte-conteneurs | 5,9 | 19,0 | 20,2 | ~20 | 20,8 | 18,4 | 16,8 | ×2,8 |
| Cap, vraquiers | 30,7 | 41,4 | 44,6 | ~44 | 43,9 | 43,9 | 44,0 | +43 % |
| Cap, Mt tpl par jour | 3,02 | 5,23 | 5,68 | ~5,1 | 5,94 | 5,39 | 5,54 | +83 % |
| **Ormuz**, tous navires | 95,6 | 91,1 | 85,5 | 58,5 / 78,3 / **3,2** | 12,9 | 4,7 | **3,9** | −96 % |
| Gibraltar, tous navires | 146,2 | 133,3 | 135,4 | 123-141 | 132,7 | 128,6 | 133,3 | −9 % |

**Lecture**
- Le trafic de Suez (~41 par jour) dépasse celui de Bab el-Mandeb (~26 par jour) en 2026. L'écart vient des navires qui desservent les ports de la mer Rouge nord (Jeddah, Yanbu, Sokhna, Aqaba) sans franchir le détroit.
- La légère reprise des porte-conteneurs à Suez en sept. 2026 (11,1 par jour) est cohérente avec Drewry (41 → 48 transits entre les semaines 37 et 38).

### 6.2 Canal de Suez : recettes (Égypte)

**Années civiles**
- 2023 : **~10,25-10,3 Md$**, un record.
- 2024 : **~4,0 Md$**, soit **−61 %** ; environ 13 213 navires, −50 % ([Euronews / Reuters, 17/04/2025](https://euronews.com/business/2025/04/17/egypts-suez-canal-revenue-fell-sharply-in-2024-on-regional-tensions)).
- 2025 : **~4,2 Md$** attendus, +7,6 % (O. Rabie, [Business Today Egypt](https://www.businesstodayegypt.com/Article/1/6885/Suez-Canal-revenues-expected-to-reach-4-2B-in-2025)).

**Exercices budgétaires (juillet-juin)**
- 2024/25 : **3,9 Md$** (192,28 Md EGP).
- **2025/26 : 4,67 Md$** (230,22 Md EGP), annoncé le 28/06/2026 ([Egyptian Streets, 30/06/2026](https://egyptianstreets.com/2026/06/30/suez-canal-revenue-rises-23-percent-in-the-2025-2026-fiscal-year-as-regional-tensions-ease/) — voir la réserve au §5).
- Objectif de la SCA : ~10 Md$ en 2027/28.
- Début 2026 : **449 M$** encaissés au ~8 février ([Anadolu, 08/02/2026](https://www.anews.com.tr/middle-east/2026/02/08/egypts-suez-canal-posts-revenue-rebound-earning-449-million-since-start-of-2026)).

**Trafic** : la CNUCED indique un tonnage transitant par Suez à ~−70 % par rapport à la moyenne de 2023 début mai 2025. PortWatch donne −53 % en tpl pour sept. 2026.

### 6.3 Distances Suez / Cap : table et points de passage pour la carte schématique

**Méthode [CALC]**
- Outil : bibliothèque open source `searoute` 1.6 (réseau maritime MARNET d'Eurostat), unités en nm.
- Restrictions : passages arctiques exclus ; routage « Cap » en bloquant Suez, Bab el-Mandeb et Panama.
- Précision : environ ±3 %.
- Jours supplémentaires calculés à 14 nœuds, soit 336 nm par jour.

| Liaison | Via Suez / Bab el-Mandeb | Via le Cap | Écart | Jours en plus (14 nœuds) |
|---|---|---|---|---|
| **Singapour–Rotterdam** | **8 367 nm** | **11 855 nm** (par la Sonde) | **+3 488 nm (+42 %)** | **+10,4 j** |
| **Shanghai–Rotterdam** | 10 546 nm | 13 866 nm | +3 320 nm (+31 %) | +9,9 j |
| Shanghai–Gênes | 8 693 nm | 13 664 nm | +4 971 nm (+57 %) | +14,8 j |
| Colombo–Rotterdam | 6 818 nm | 10 722 nm | +3 904 nm (+57 %) | +11,6 j |
| Mundra (Inde)–Rotterdam | 6 348 nm | 11 027 nm | +4 679 nm (+74 %) | +13,9 j |
| **Mombasa–Rotterdam** | 6 393 nm | 8 771 nm | +2 378 nm (+37 %) | +7,1 j |
| **Mombasa–Alexandrie** | 3 266 nm | 9 503 nm | +6 237 nm (+191 %) | +18,6 j |
| **Djibouti–Rotterdam** | 4 669 nm | 10 365 nm | +5 696 nm (+122 %) | +17,0 j |
| Tanger Med–Mombasa | 5 017 nm | 7 706 nm | +2 689 nm (+54 %) | +8,0 j |
| Novorossiïsk–Djibouti | 2 613 nm | 11 534 nm | +8 921 nm (+341 %) | +26,6 j |
| Novorossiïsk–Mombasa | 4 337 nm | 9 940 nm | +5 603 nm (+129 %) | +16,7 j |
| Durban–Rotterdam | 7 015 nm | 7 015 nm | 0 (déjà par l'Atlantique) | — |
| Singapour–Lagos | 8 303 nm | 8 303 nm | 0 | — |

**Points de passage (latitude, longitude en degrés décimaux)**
- Les points marqués *[SaaS]* sont repris de `_WAYPOINTS` dans `backend/logistics_fees_data.py`.

| Point | Lat | Lon |
|---|---|---|
| Shanghai | 31,20 | 121,80 |
| Singapour | 1,25 | 103,85 |
| Colombo | 6,95 | 79,85 |
| Ormuz | 26,57 | 56,25 |
| **Bab el-Mandeb** *[SaaS]* | 12,60 | 43,40 |
| Djibouti | 11,60 | 43,13 |
| Port-Soudan | 19,60 | 37,23 |
| Jeddah | 21,48 | 39,17 |
| **Suez** *[SaaS]* (sud du canal ; entrée sud ~29,93 / 32,55) | 30,50 | 32,35 |
| Port-Saïd | 31,27 | 32,30 |
| **Gibraltar** *[SaaS]* | 35,95 | −5,60 |
| Tanger Med | 35,89 | −5,50 |
| Rotterdam | 51,95 | 4,05 |
| Las Palmas | 28,14 | −15,42 |
| Dakar | 14,68 | −17,43 |
| Abidjan | 5,28 | −4,02 |
| Lomé | 6,13 | 1,28 |
| Lagos | 6,43 | 3,40 |
| Walvis Bay | −22,95 | 14,50 |
| Le Cap | −33,90 | 18,43 |
| **Cap de Bonne-Espérance / Agulhas** *[SaaS]* | −34,83 | 19,50 |
| Durban | −29,88 | 31,05 |
| Port-Louis | −20,16 | 57,50 |
| Mombasa | −4,07 | 39,66 |

**Tronçons calculés [CALC searoute]**
- **Route par Suez, Singapour → Rotterdam, total ≈ 8 425 nm** :
  - Singapour → Colombo : 1 607 nm ;
  - Colombo → Bab el-Mandeb : 2 235 nm ;
  - Bab el-Mandeb → Suez : 1 187 nm ;
  - Suez → Port-Saïd : 103 nm ;
  - Port-Saïd → Gibraltar : 1 935 nm ;
  - Gibraltar → Rotterdam : 1 358 nm.
- **Route par le Cap avec escales de soutage, total ≈ 12 089 nm** (11 855 nm en direct) :
  - Singapour → Port-Louis : 3 423 nm ;
  - Port-Louis → Cap : 2 365 nm ;
  - Cap → Las Palmas : 4 547 nm ;
  - Las Palmas → Rotterdam : 1 754 nm.
- **Tronçons africains** :
  - Singapour → Durban : 4 945 nm ; Durban → Cap : 875 nm ;
  - Le Cap → Walvis Bay : 748 nm ; Le Cap → Dakar : 3 726 nm ; Dakar → Tanger Med : 1 535 nm ;
  - Lagos → Le Cap : 2 619 nm ; Abidjan → Tanger Med : 2 735 nm ;
  - Colombo → Mombasa : 2 615 nm ; Mombasa → Bab el-Mandeb : 1 810 nm ; Mombasa → Durban : 1 759 nm ;
  - Djibouti → Bab el-Mandeb : 86 nm ;
  - Shanghai → Singapour : 2 179 nm.

### 6.4 Carburant, CO2 et fret : ce que coûte le Cap

**Temps et consommation**
- Environ **+10 à 14 jours** par voyage Asie–Europe. La consommation de carburant augmente d'environ **30 %** (sources secondaires, voir §5).
- Le trajet Asie–Europe passe de 16 à 32 jours pour certains services (résumé).
- Pétrolier Asie → Europe du Nord : **+0,93 M$** par voyage ([SAFETY4SEA](https://safety4sea.com/an-extra-million-is-added-each-time-a-tanker-goes-around-cape-of-good-hope/)).

**Estimation [CALC] pour un porte-conteneurs de 15 000 EVP**
- Hypothèses (H:) : 150 t de VLSFO par jour à 18 nœuds, VLSFO à 740-831 $/t (Singapour, août-sept. 2026).
- À 18 nœuds, les +3 488 nm de Singapour–Rotterdam représentent environ **+8,1 jours**. Le chiffre de +10,4 jours du tableau §6.3 est calculé à 14 nœuds.
- **Carburant** : ~1 210 t supplémentaires, soit **0,90 à 1,0 M$ par voyage aller**.
- **CO2** : 1 210 t × 3,114 (facteur OMI du VLSFO) ≈ **3 770 t de CO2** en plus par voyage.
- **ETS** : le surcoût est surtout sur la part UE. Pour Asie → UE, 50 % des émissions sont soumises au système.

**Fret**
- Le déroutement a porté les tonnes-milles mondiales à **+5,9 % en 2024** (CNUCED).
- En 2026, le WCI Shanghai–Rotterdam (3 485 $/FEU au 24/09/2026) baisse à mesure que les transits de Suez reprennent partiellement (Drewry). Un **retour massif reste suspendu** ([Air Cargo News, 02/03/2026](https://www.aircargonews.net/supply-chains/2026/03/box-lines-unlikely-to-return-to-suez-canal-in-2026-following-middle-east-strikes/)).
- La prise de Perim (09/2026) éloigne encore la perspective d'un retour.

### 6.5 Ports africains : gagnants et perdants du déroutement [PW + sources]

Moyennes d'escales de navires marchands par jour, et volumes import + export estimés (Mt par an, rythme annualisé). Source : [IMF PortWatch](https://portwatch.imf.org/) `Daily_Ports_Data`, données jusqu'au 18/09/2026.

| Port | Escales/j 2023 (janv.-oct.) | 2024 | 2025 | Août-sept. 2026 | Volumes estimés 2023 → 2025 → août-sept. 2026 (Mt/an) | Lecture |
|---|---|---|---|---|---|---|
| **Tanger Med** | 13,5 | 12,7 | 12,7 | 12,2 | 109 → 139 → **142** (+30 %) | **Gagnant.** Officiel : **11,1 M EVP en 2025** (+8,4 %) et plus de 161 Mt ([TMPA, 02/02/2026](https://www.tangermed.ma/wp-content/uploads/press-releases/2026/CP-TMPA-PORT-ACTIVITY-REPORT-IN-2025.pdf)) |
| **Walvis Bay** | 1,4 | 1,7 | 1,8 | 2,0 | 4,1 → 5,9 → **7,3** (+78 %) | **Gagnant** : soutage navire à navire en hausse ([MarineLink](https://www.marinelink.com/news/african-bunkering-hubs-gain-ships-reroute-537175)) |
| **Port-Louis** (Maurice) | 2,8 | 2,7 | 3,0 | 2,9 | 8,3 → 9,5 → 9,2 | **Gagnant en soutage** : ventes **doublées à ~1 Mt en 2025** ; escales de soutage 207 → **294 (+42 %)** en mars 2026 ([Ship & Bunker](https://shipandbunker.com/news/emea/132582-mauritius-bunker-demand-doubled-in-2024-amid-red-sea-crisis) ; [OGME](https://www.oilandgasmiddleeast.com/news/mauritius-ship-refuelling-up-42) ; Moneyweb 2026, page 403) |
| Le Cap | 2,3 | 3,3 | 3,1 | 2,8 | 8,5 → 9,0 → 6,8 | Hausse des escales en 2024-2025 (+35-43 %) ; recul en août-sept. 2026 |
| Algoa Bay (Port Elizabeth / Ngqura) | 3,9 / 1,9 | 1,9 / 1,5 | 2,3 / 1,9 | 2,9 / 1,8 | — | Soutage offshore suspendu (saisies SARS, sept. 2023) puis **repris en févr. 2025** ([Baird Maritime](https://www.bairdmaritime.com/shipping/ports/feature-ships-bypassing-red-sea-boost-african-refueling-ports)) |
| Durban | 7,0 | 6,6 | 7,0 | **5,8** | 64 → 63 → 58 | Pas de gain net ; recul en 2026 (congestion et productivité : voir le LPI) |
| **Abidjan** | 4,4 | 4,9 | 5,6 | 5,2 | 18 → 27 → **29** | Hausse forte (transbordement Afrique de l'Ouest) |
| Lomé | 3,9 | 4,0 | 4,3 | 3,9 | 16 → 17 → 16 | Stable |
| Lagos | 5,3 | 5,1 | 5,4 | 4,9 | 21 → 25 → 23 | Stable |
| Dakar | 4,2 | 4,1 | 4,4 | 3,9 | 16 → 16 → 13 | Recul en 2026 (blocus JNIM vers le Mali) |
| **Djibouti** | 3,8 | 4,0 | 4,0 | 3,5 | 16,8 → 16,1 → 16,3 | **Perdant** : EVP −10,5 % (S1 2025) et −17,5 % (S2 2025) (Banque mondiale) ; ajouté aux zones JWC le 03/03/2026 |
| **Port-Soudan** | 1,7 | 1,4 | 1,3 | 1,9 | 5,8 → 5,4 → 8,1 | Guerre et zone JWC ; rebond récent inexpliqué |
| **Jeddah** (référence régionale) | 11,3 | 8,9 | 8,4 | **2,9** | 82 → 67 → **18** | **Effondrement** (blocus houthi, JWLA-034) |
| Port-Saïd | 2,3 | 2,2 | 2,2 | 2,0 | 3,8 → 4,2 → 3,7 | Hub de transbordement affaibli |
| Alexandrie | 9,5 | 10,5 | 11,0 | 8,4 | 39 → 57 → 45 | Recul en 2026 |
| El Sokhna (mer Rouge égyptienne) | 1,7 | 2,3 | 2,5 | **4,5** | 23 → 26 → **50** | Forte hausse en 2026 (cause non analysée, possiblement le pétrole via SUMED) |
| Mombasa | 4,0 | 4,1 | 4,5 | 4,4 | 23,5 → 29 → 27 | Volumes en hausse, mais les **porte-conteneurs** baissent (1,8 → 1,5 escale/j) : fiabilité des rotations dégradée |
| Dar es Salaam | 3,0 | 2,5 | 3,0 | 3,3 | 11 → 13 → 14 | En hausse |
| Berbera | 0,8 | 1,0 | 1,0 | 1,0 | 1,4 → 1,7 → 1,8 | Stable |
| Maputo | 2,7 | 2,6 | 2,6 | 2,7 | 25 → 26 → 32 | En hausse (vrac) |

**Autres points**
- **Les Canaries (Las Palmas)** : soutage sur la route du Cap vers l'Europe. Non mesuré ici.
- **Congestion au Cap et à Durban** : documentée en 2024. Pas de chiffre 2026 fiable trouvé.

### 6.6 Effets sur le commerce agricole africain (voir le détail au §4)

| Flux | Effet du déroutement ou de la crise | Section |
|---|---|---|
| **Thé kényan** vers l'Égypte et le Royaume-Uni | Par le Cap : +18,6 j vers Alexandrie, +7 j vers Rotterdam. Pakistan en zone JWC. Moyen-Orient à l'arrêt en mars 2026 | 4.2 |
| **Café éthiopien** via Djibouti | +17 j vers l'Europe par le Cap ; +1 500 à 2 000 $ par boîte | 4.4 |
| **Blé** pour l'Égypte, le Soudan, Djibouti et l'Éthiopie | Surprime Bab el-Mandeb 0,5-1 % et mer Noire ~1 % ; +2 à 5 $/t d'assurance ; le Cap n'est pas une option pour la mer Rouge | 4.1 |
| **Fleurs et avocats d'Afrique de l'Est** vers l'Europe | Fleurs par avion : fret ×2 ; avocats par mer : plus de 32 j | 4.3 |
| **Agrumes sud-africains** | Moyen-Orient (20 %) perturbé ; export ramené à 205,3 M de cartons | 4.6 |
| **Fruits et légumes méditerranéens** (Égypte, Maroc) vers l'Asie et le Golfe | Les flux de l'Égypte vers le Golfe et l'Asie passent par Bab el-Mandeb ou Ormuz, tous deux compromis. Le port saoudien de Jeddah s'est effondré (−74 %). Le Maroc passe par Gibraltar et le Cap : trajet plus long mais évite la zone de guerre. Non chiffré | analyse |
| **Bétail** de la Corne de l'Afrique et du Soudan vers l'Arabie saoudite | Jeddah −74 % ; primes saoudiennes de 3 à 7 % | 4.5 |

---

## 7. Surcharges de fret liées au carburant (hausse du pétrole 2026)

### 7.1 Série trimestrielle pour graphique

**Sources**
- Brent : **[FRED DCOILBRENTEU](https://fred.stlouisfed.org/series/DCOILBRENTEU)** (EIA, moyenne des cotations quotidiennes).
- Kérosène : **[FRED DJFUELUSGULF](https://fred.stlouisfed.org/series/DJFUELUSGULF)** (EIA, US Gulf Coast, en $/gallon × 42 = $/b).
- Extraction du 27/09/2026. Le T3 2026 s'arrête au 22/09.

| Trimestre | Brent ($/b) | Kérosène US Gulf ($/gal) | Kérosène ($/b) | VLSFO Singapour ($/t) | VLSFO Rotterdam ($/t) |
|---|---|---|---|---|---|
| T1 2024 | 82,92 | 2,620 | 110,0 | n.d. | n.d. |
| T2 2024 | 84,68 | 2,463 | 103,4 | n.d. | n.d. |
| T3 2024 | 80,01 | 2,199 | 92,4 | n.d. | n.d. |
| T4 2024 | 74,66 | 2,077 | 87,2 | n.d. | n.d. |
| T1 2025 | 75,87 | 2,223 | 93,4 | n.d. | n.d. |
| T2 2025 | 68,07 | 1,998 | 83,9 | n.d. | n.d. |
| T3 2025 | 69,03 | 2,121 | 89,1 | n.d. | n.d. |
| T4 2025 | 63,65 | 2,117 | 88,9 | n.d. | n.d. |
| T1 2026 | 80,72 | 2,704 | 113,6 | écart Singapour-Rotterdam record de **362 $/t** mi-mars ([MarineLink](https://www.marinelink.com/news/record-high-bunker-oil-price-difference-540175)) | — |
| T2 2026 | 102,63 | 3,633 | 152,6 | n.d. | n.d. |
| T3 2026 (au 22/09) | 94,16 | 3,772 | 158,4 | **831** (18/08) ; ~740 (fin sept., non vérifié) | **660** (18/08) ; ~621 (fin sept., non vérifié) |
| **Moyenne 2024** | **80,52** | 2,338 | 98,2 | | |
| **Moyenne 2025** | **69,14** | 2,114 | 88,8 | | |

**VLSFO** : aucune série trimestrielle libre d'accès n'a été trouvée. Seuls des points ponctuels sont disponibles ([ShipUniverse, Bunker Watch 18/08/2026](https://www.shipuniverse.com/news/bunker-watch-august-2026-ship-fuel-prices-stay-high-as-brent-tops-90-and-mgo-breaks-1400-in-fujairah/)).
- Relevés du 18/08/2026 :
  - HSFO : Singapour 647 $, Rotterdam 548 $.
  - MGO : Singapour 1 240 $, Fujairah **1 404 $**.
  - VLSFO : Fujairah 816 $, Houston 695 $.
- Prévision VLSFO pour le T4 2026 : **690 $/t**.
- Aucun prix à Durban ou dans un autre port africain n'a été trouvé.

**Mensuel 2026 [FRED]**

| Mois | Brent ($/b) | Kérosène ($/b) |
|---|---|---|
| Janv. | 66,60 | 85,3 |
| Févr. | 70,89 | 95,0 |
| **Mars** | **103,13** | 155,3 |
| **Avr.** | **117,29** | 165,0 |
| Mai | 107,14 | 165,6 |
| Juin | 85,40 | 127,8 |
| Juil. | 83,76 | 142,9 |
| Août | 91,08 | 156,4 |
| **1-22 sept.** | **112,96** | **184,0** |

- **Pic quotidien du Brent : 130,80 $ le 15/09/2026**, juste après la prise de Perim.

**Projections de l'EIA (STEO de sept. 2026)** ([Rigzone, 14/09/2026](https://www.rigzone.com/news/eia_sees_2026_oil_price_coming_in_22_higher_than_last_year-14-sep-2026-184606-article/))
- Moyenne 2025 : 69,04 $/b. Moyenne 2026 : **91,01 $/b** (+22 $).
- T4 2026 : 90,66 $. Moyenne 2027 : 73,74 $.
- Août 2026 : 91 $/b.

**IATA**
- Kérosène mondial à environ **194,90 $/b** dans la semaine au 18/09/2026, contre 141,64 $ en juin 2026 (résumé ; [IATA Fuel Monitor](https://www.iata.org/en/publications/economics/fuel-monitor/)).
- **+116,5 % sur un an** au 18/09/2026 ([Air Cargo News](https://www.aircargonews.net/data/2026/09/airfreight-rates-strong-as-peak-season-approaches/)).
- Le kérosène a dépassé 200 $/b à la mi-avril 2026 (résumé).

### 7.2 Lien entre le conflit au Moyen-Orient et les prix du carburant

**Déclencheurs**
- 28/02/2026 : début de la guerre.
- Mars : fermeture de fait d'Ormuz (3,2 navires par jour [PW]).
- Le Brent passe de 70,9 $ (févr.) à 117,3 $ (avr.) [FRED].
- L'IEA coordonne une libération de stocks de **400 M de barils**.

**Accalmie puis rechute**
- Cessez-le-feu : le Brent retombe à 83,8 $ en juillet.
- Reprise des hostilités (8-9/07), blocus houthi (21/07) et prise de Perim (09/2026) : le Brent remonte à **113 $ en moyenne** en septembre, avec un pic à 130,8 $.

**Pourquoi le kérosène et le gazole souffrent plus**
- Ils réagissent davantage que le brut : MGO à 1 404 $/t à Fujairah, kérosène +107 % contre +63 % pour le Brent en sept. 2026 par rapport à 2025.
- Raison : le Golfe exporte une grande partie des distillats moyens (analyse ; confirmé qualitativement par ShipUniverse : « middle distillates carrying an especially large premium »).

### 7.3 Surcharges carburant appliquées (mer et air)

**Mer**
- **Surcharges carburant d'urgence (EBS/EFS)** des 5 premiers armateurs (MSC, Maersk, CMA CGM, ONE, Hapag-Lloyd), annoncées entre le 9 et le 25/03/2026.
- CMA CGM : 150 $/EVP, puis **265 $/EVP**.
- Maersk : EBS **sur tout le réseau** à partir du 25/03/2026, donc Afrique comprise (§3.3).
- **BAF / surcharge soutes trimestrielle** des lignes Afrique (Maersk, MSC, CMA CGM) : montants 2025-2026 **non trouvés** (voir §5).
- **EU ETS 2026** : environ 59 €/EVP sur Asie → Europe du Nord (Maersk, T1 2026) ; 50 % des émissions pour les liaisons Afrique ↔ UE.
- **Surcharges de guerre** : Golfe 1 500 à 4 000 $ par boîte (mars 2026). Mombasa : PSS de 1 000/2 000 $ (juin 2026).

**Air**
- **Ethiopian** : +20 % sur les tarifs périssables (08/04 → 31/12/2026).
- **Fleurs kényanes** : 2,5 → 5-5,8 $/kg (mars 2026).
- Les grilles FSC par kg de Kenya Airways Cargo, Emirates SkyCargo et Air France-KLM Cargo pour 2026 **n'ont pas été trouvées**. Un document Emirates SkyCargo (conditions locales de vente, Éthiopie, 01/01/2025) existe mais n'a pas été ouvert ([PDF](https://www.skycargo.com/media/v2eb3402/01jan2025_lsc_africas_revised_ethiopia-et.pdf)).
- **Part du carburant dans le coût du fret aérien** : non vérifiée pour 2026. À titre indicatif, l'IATA situe habituellement le carburant autour d'un quart à un tiers des coûts des compagnies. À citer seulement avec la [fiche carburant IATA](https://www.iata.org/en/iata-repository/pressroom/fact-sheets/fact-sheet-fuel/) une fois vérifiée.

### 7.4 Effet sur les périssables (synthèse)

| Produit | Mode | Surcoût observé ou calculé | Source |
|---|---|---|---|
| Roses (Kenya) | Air | Fret ×2 (5-5,8 $/kg) ; pertes jusqu'à 1,4 M$ par semaine | AP, 25/03/2026 |
| Fleurs et légumes (Éthiopie) | Air | Tarif +20 % | Hortidaily, 05/05/2026 |
| Poisson frais, haricots verts, mangues | Air | Même logique que les fleurs (kérosène +107 % sur un an) ; pas de tarif spécifique trouvé | [FRED] |
| Avocats (Kenya) | Mer (reefer) | Plus de 32 j via le Cap ; ~3 000 $ contre 2 000 $ par conteneur | non vérifié |
| Agrumes (Afrique du Sud) | Mer (reefer) | Surcharges soutes doublées sur certaines routes ; Moyen-Orient perturbé | BusinessDay, 06/08/2026 |
| Tous produits en reefer vers ou via le Golfe | Mer | Surcharge de guerre **3 500 $ (Hapag-Lloyd) à 4 000 $ (CMA CGM) par reefer** | Lloyd's List, mars 2026 |
