# ZLECAf Trade Calculator — Audit consolidé et plan technique d'amélioration

**Dépôt de référence :** `aouggad-web/afcfta-final-002`
**Version exclue du périmètre :** `afcfta-final-03`
**Date du document initial :** 12 juillet 2026
**Date de cette révision :** 13 juillet 2026 — **v2, vérifiée directement sur le code source**
**Statut :** document de cadrage, de priorisation et de pilotage technique
**Public cible :** direction produit, équipe technique, experts douaniers, data engineers et partenaires institutionnels

> **Note sur cette révision.** Toutes les affirmations factuelles de la version 1 ont été rejouées contre le code réel du dépôt (routes backend, fichiers de données, tests, CI, sécurité). La quasi-totalité des constats initiaux sont confirmés — souvent avec plus de précision que l'audit initial. Trois corrections factuelles et quatre constats supplémentaires, plus graves que ce que le document initial laissait supposer, ont été ajoutés. Chaque section modifiée porte la mention **[Vérifié 13/07]**. Le détail des preuves (fichier:ligne) figure en Annexe A.

---

## 1. Objet du document

Ce document consolide les résultats de l'audit de `afcfta-final-002` et transforme les recommandations en un plan d'exécution technique doté d'objectifs clairs et mesurables.

Il couvre :

- le moteur tarifaire et fiscal ;
- la provenance et la certification des données ;
- les données tarifaires algériennes ;
- le module Opportunités ;
- le parcours « Sourcing Import » destiné aux importateurs nord-africains ;
- l'architecture applicative, la sécurité, les tests et l'industrialisation ;
- la feuille de route, les responsabilités, les KPI et les critères de recette.

Ce document ne constitue pas une certification juridique des tarifs. Les références réglementaires primaires devront être validées par un expert douanier avant qu'une donnée soit qualifiée `VERIFIED/A`.

---

## 2. Vision produit

La plateforme doit convertir la ZLECAf en décisions commerciales exécutables. Elle doit répondre, de façon traçable, à deux familles de questions.

### 2.1 Calcul réglementaire

Pour un produit, une origine, une destination et une valeur commerciale :

1. quel code national est utilisé ;
2. quels droits, taxes et formalités s'appliquent ;
3. quelle préférence est accessible ;
4. quelles règles d'origine doivent être satisfaites ;
5. quel est le coût total de l'opération ;
6. quelles sources et quel niveau de confiance soutiennent le résultat.

### 2.2 Intelligence commerciale

Pour un exportateur ou un importateur :

1. quel produit acheter ou vendre ;
2. vers quel marché ou depuis quel fournisseur ;
3. dans quel volume et à quelle période ;
4. avec quel coût rendu, délai, risque et financement ;
5. avec quel avantage tarifaire réellement applicable ;
6. avec quelle qualité de données.

---

## 3. Synthèse exécutive de l'audit

`afcfta-final-002` est le socle le plus abouti. Le dépôt contient une couverture fonctionnelle large, une interface riche, un modèle de provenance v4, un moteur de calcul déterministe, un adaptateur Algérie, des modules d'opportunités et une base de sécurité API.

Le principal risque n'est pas l'absence de fonctionnalités. Il réside dans la coexistence de plusieurs générations d'architecture et de plusieurs chemins de calcul. En l'état, deux parcours pourraient produire des réponses différentes pour une même opération — **et un cas au moins produit aujourd'hui une collision de route silencieuse (voir 4.2)**.

Les cinq priorités sont donc :

1. restaurer une chaîne de confiance incontestable pour les données ;
2. désigner un moteur de calcul souverain et un endpoint public unique ;
3. publier un manifeste unique du dataset réellement servi ;
4. certifier progressivement l'Algérie à partir de sources primaires ;
5. transformer le module Opportunités en outil de décision et de sourcing mesurable.

**[Vérifié 13/07]** Une sixième priorité doit être ajoutée, car elle conditionne toutes les autres : **rendre la CI réellement bloquante et fermer l'accès public par défaut aux routes de données** (voir 4.5 et 4.6). En l'état, un code qui casse les tests backend peut être fusionné sans échec CI, et les données tarifaires sont accessibles sans clé API par défaut.

### 3.1 Niveau de maturité estimé

| Domaine | Maturité actuelle | Cible | Priorité |
|---|---:|---:|---:|
| Couverture fonctionnelle | Élevée | Élevée | Maintenir |
| Unicité du moteur | Faible | Très élevée | P0 |
| Provenance des données | Moyenne | Très élevée | P0 |
| Certification réglementaire | Faible à moyenne | Élevée | P0/P1 |
| Module Opportunités | Élevée fonctionnellement | Élevée et certifiée | P1 |
| Coût total rendu | Partiel | Complet | P1 |
| Sécurité commerciale | Moyenne | Élevée | P2 |
| CI et certification des lots | Faible (non bloquante) | Très élevée | **P0** |

---

## 4. Résultats détaillés de l'audit

## 4.1 Schéma de provenance v4

Le dépôt contient déjà les concepts structurants suivants :

- statuts `VERIFIED`, `PARTIAL`, `SYNTHETIC` ;
- grades de fiabilité `A`, `B`, `C`, `D` ;
- provenance structurée ;
- références juridiques ;
- bases et séquences de calcul ;
- adaptateur `dza_conformepro_adapter.py` ;
- moteur déterministe `engine/calculation.py`.

### Constats **[Vérifié 13/07 — confirmé avec citation exacte]**

- L'adaptateur ConformePro qualifie correctement la source algérienne comme secondaire : `PARTIAL/B`. Le code lui-même le documente noir sur blanc : *« Statut de provenance émis : PARTIAL / fiabilité B. conformepro.dz est un agrégateur privé du tarif intégré algérien — pas la source primaire (DGD / Journal Officiel). Les lignes passeront VERIFIED/A après recoupement avec le tarif officiel DGD. »* (`engine/adapters/dza_conformepro_adapter.py:14-17`, statut effectivement posé lignes 114-116).
- Un artefact de statut déclare néanmoins l'Algérie `VERIFIED/A` : `engine/output/DATA_STATUS.json` (et sa copie identique `frontend/public/data/DATA_STATUS.json`) contient `"DZA": {"data_status": "VERIFIED", "reliability": "A", "lines_total": 17115, ...}`.
- Cette contradiction constitue un défaut bloquant de gouvernance des données, **et elle est directement servie au frontend** puisque la copie vivant sous `frontend/public/data/` est celle que l'interface consomme.
- Une URL officielle ne suffit pas à qualifier une ligne `VERIFIED/A` : la preuve doit porter sur le document, la version, l'extraction et le contrôle.

### Règle cible

Une mesure ne peut être promue `VERIFIED/A` que si les cinq conditions suivantes sont vraies :

1. source réglementaire primaire ;
2. document et référence juridique précis ;
3. date d'effet ou version connue ;
4. preuve d'extraction reproductible ;
5. validation automatisée et/ou revue experte réussie.

---

## 4.2 Moteur de calcul tarifaire

Le moteur de référence a été validé sur la position algérienne `0101211100`.

### Cas de référence **[Vérifié 13/07 — reproduit exactement]**

Le cas suivant existe littéralement dans `engine/tests/test_calculation_dza.py` (lignes 119-150), avec les mêmes valeurs d'entrée et les mêmes assertions (`total_duties_taxes == 199_000.0`, économie ZLECAf `== 54_500.0`).

| Élément | Valeur |
|---|---:|
| Valeur CAF | 1 000 000 DZD |
| Droit de douane | 5 % |
| TCS | 3 % |
| PRCT | 2 % |
| TVA | 9 % sur base cumulative |
| Total NPF | 199 000 DZD |
| Taux effectif NPF | 19,90 % |
| Total ZLECAf | 144 500 DZD |
| Économie estimée | 54 500 DZD |

Le moteur émet également un avertissement lorsque la provenance est `PARTIAL`.

### Risque architectural **[Vérifié 13/07 — confirmé et aggravé]**

Plusieurs routes de calcul coexistent, toutes montées sous le préfixe `/api` (`backend/server.py`, `backend/routes/__init__.py`) :

- `/api/calculate-tariff` (`backend/routes/calculator.py`) ;
- `/api/authentic-tariffs/calculate` (`backend/routes/authentic_tariffs.py`) ;
- `/api/calculate/detailed` — **et non `/tariffs/calculate/detailed` comme indiqué en v1** (`backend/routes/tariffs.py:473`, router sans préfixe) ;
- `/api/enhanced-calculator/dza` (`backend/routes/enhanced_calculator.py`) ;
- `/api/postgres-tariffs/calculate` (`backend/routes/postgres_tariffs.py`) ;
- `/api/regulatory-engine/*` — **n'a pas de sous-route `/calculate`** ; il expose `/countries`, `/details`, `/details/all`, `/summary/{country}` uniquement, servis via `engine/api/engine_service.py`.

**Constat supplémentaire critique, absent de la v1 :** `backend/routes/regional_calculator.py` déclare son routeur avec le préfixe `/enhanced-calculator` — **le même préfixe** que `backend/routes/enhanced_calculator.py`. Les deux fichiers cohabitent donc dans le même espace de routes (`/api/enhanced-calculator/*`) avec des services backend différents (`services/enhanced_calculator_service.py` contre la logique propre à `regional_calculator.py`). Selon l'ordre de montage des routeurs dans `backend/routes/__init__.py`, l'un peut masquer des routes de l'autre sans qu'aucune erreur ne soit levée au démarrage. C'est exactement le type de risque que ce document dénonce en 3 — sauf que là, ce n'est pas un risque théorique, c'est une collision déjà présente dans le code.

`authentic_tariffs.py` et `postgres_tariffs.py` partagent en réalité le même service (`services/authentic_tariff_service.py`) : ce ne sont pas deux moteurs indépendants, mais deux façades sur le même calcul — ce qui limite un peu le risque de divergence pour ce couple précis, sans le supprimer pour les autres routes.

Le frontend appelle plusieurs circuits, notamment depuis `CalculatorTab.jsx`, confirmé avec au moins 5 endpoints distincts appelés en cascade avec repli (`/authentic-tariffs/calculate/...`, `/calculate-tariff`, `/calculate/detailed/...`, `/postgres-tariffs/.../sub-positions` avec repli vers `/tariffs/sub-positions`, `/hs6-tariffs/code/...`). Il n'existe donc pas encore de moteur souverain garanti de bout en bout.

**Constat supplémentaire :** `engine/calculation.py` — présenté comme le futur noyau — est aujourd'hui **du code mort**. Une recherche exhaustive montre qu'il n'est importé que par son propre test (`engine/tests/test_calculation_dza.py`). Aucune des sept routes ci-dessus, pas même `regulatory-engine` (qui pourtant s'en rapproche le plus conceptuellement), ne l'appelle : `engine/api/engine_service.py` réimplémente sa propre logique de calcul en parallèle. Adopter `engine/calculation.py` comme noyau (Lot 3) n'est donc pas un simple changement de routage : c'est un branchement à créer de zéro entre un module non utilisé et sept points d'entrée qui ont chacun leur propre logique.

**Constat supplémentaire :** un espace `/api/v2` **existe déjà** (`backend/api/v2/endpoints.py`, préfixe `/v2` monté sous `/api`), mais il expose `/search/comprehensive`, `/bulk/tariff-calculations`, `/bulk/investment-analysis`, `/analytics/dashboard`, `/ai/recommendations`, `/mobile/quick-lookup` — **aucune route `/calculations`**. La recommandation ci-dessous est donc à lire comme « ajouter `/api/v2/calculations` dans l'espace v2 existant », pas comme la création d'un nouvel espace.

### Décision recommandée

- `engine/calculation.py` devient le noyau fiscal déterministe (à brancher effectivement — il ne l'est pas aujourd'hui).
- Le modèle canonique v4 devient le contrat d'entrée obligatoire.
- Un service d'orchestration unique gère classification, origine, tarifs, formalités et calcul.
- `/api/v2/calculations` est ajouté à l'espace `/api/v2` déjà existant et devient l'interface publique stable.
- La collision de préfixe entre `regional_calculator.py` et `enhanced_calculator.py` est résolue avant tout autre chantier sur ces routes (renommage de préfixe ou fusion).
- Les anciennes routes sont transformées en adaptateurs temporaires, puis dépréciées.

---

## 4.3 Inventaires et datasets

Les artefacts observés ne décrivent pas la même photographie **[Vérifié 13/07 — chiffres confirmés exacts, pas seulement « environ »]** :

| Artefact | Couverture annoncée | Vérification |
|---|---:|---|
| `pipeline_report.json` | 762 213 enregistrements / 46 pays | Exact : `total_records: 762213`, 46 entrées dans `countries_processed` |
| `DATA_STATUS.json` | 279 002 lignes / 40 pays | Exact : `summary.countries: 40`, `summary.lines_total: 279002` — fichier dupliqué à l'identique dans `engine/output/` et `frontend/public/data/` |
| `DZA_summary.json` | 16 569 enregistrements | Exact : `record_count: 16569` |
| Statut DZA dans `DATA_STATUS.json` | 17 115 lignes | Exact, mais **incohérent avec le chiffre précédent** |

**Constat supplémentaire :** les deux chiffres algériens (16 569 et 17 115) ne sont pas juste des arrondis différents d'une même mesure — ils proviennent de deux étapes de pipeline distinctes qui ne se recoupent pas. Tant que cet écart de 546 lignes n'est pas expliqué, aucun des deux chiffres ne peut servir de référence de couverture pour l'Algérie.

### Risques

- lot de production non identifiable ;
- index construits à partir d'une génération différente ;
- fallback implicite vers des données obsolètes ;
- incohérence entre chiffres d'audit, API et interface ;
- présence historique de pays ayant presque tous le même nombre de lignes, signature probable d'un gabarit HS6 partagé.

**[Vérifié 13/07]** Ce dernier point est confirmé de façon frappante : un échantillon de fichiers `*_summary.json` (54 au total dans `engine/output/`) montre un nombre d'enregistrements resserré entre **16 567 et 16 575**, quelle que soit la taille réelle de l'économie du pays — Comores et Djibouti (économies minuscules) affichent des volumes du même ordre que l'Égypte, le Maroc ou l'Afrique du Sud (16 568-16 575). Cette absence de variance est incompatible avec des nomenclatures tarifaires nationales authentiques, dont la longueur varie normalement fortement d'un pays à l'autre, et corrobore l'hypothèse d'un gabarit HS6 commun dupliqué par pays.

**Constat supplémentaire :** aucun registre de dataset actif n'existe. `backend/tariff_crawl/manifest.py` a été identifié comme candidat mais ne fait que classer, par pays, la **source** à utiliser (`national_crawl` > `regional_cet` > `wto_mfn_hs6` > `estimated` > `none`) — il ne porte aucune notion de version de dataset `ACTIVE`/`DRAFT`/`RETIRED` servie par l'API. `frontend/public/manifest.json` est un manifeste PWA sans rapport. Le manifeste de dataset recommandé en 7.5 est donc entièrement à construire, pas à étendre.

### Décision recommandée

Créer un manifeste unique par publication et interdire à l'API de charger un lot non déclaré `ACTIVE`.

---

## 4.4 Données synthétiques et données héritées

Les anciennes générations contiennent des profils de volume très similaires entre pays. Cette homogénéité est compatible avec une construction à partir d'un modèle commun plutôt qu'avec des nomenclatures nationales authentiques — **confirmé quantitativement en 4.3 (bande 16 567-16 575 quel que soit le pays)**.

### Garde-fous obligatoires

- aucune donnée synthétique présentée comme tarif légal ;
- badge visible et non ambigu dans l'interface ;
- aucune promotion automatique vers `PARTIAL` ou `VERIFIED` ;
- aucune valeur numérique de secours dans le frontend ;
- exclusion des données `SYNTHETIC` des classements commerciaux par défaut ;
- rapport de similarité inter-pays à chaque build de dataset.

---

## 4.5 Sécurité et modèle commercial

La base actuelle comprend notamment **[Vérifié 13/07 — détail exact]** :

- hachage SHA-256 des clés (`backend/auth.py`, fonction `_hash_key`) ;
- création et révocation des clés (`POST`/`DELETE /admin/keys`, révocation en soft-delete) ;
- niveaux d'accès : `free`, `basic`, `pro`, `admin`, `standard` (`VALID_TIERS`, `backend/routes/admin_keys.py`) ;
- quotas pour certains appels IA, **appliqués uniquement aux routes IA/Claude** (`AI_TIER_QUOTAS`, `backend/auth.py`), pas au reste de l'API ;
- protection de routes administratives via une dépendance `require_admin` (403 hors tier `admin`) ;
- CORS configurable via la variable `ALLOWED_ORIGINS` (`backend/server.py`) ;
- MongoDB et Redis isolés dans la configuration Docker : chacun lié uniquement à `127.0.0.1`, `cap_drop: ALL`, `no-new-privileges`, Redis avec mot de passe obligatoire ;
- backend en lecture seule dans le conteneur (`read_only: true`, `tmpfs` pour `/tmp`, utilisateur non-root).

Nuance à noter : les trois services Docker partagent le même réseau bridge — l'isolation vient du binding de port et des capabilities, pas d'une segmentation réseau.

### Écarts **[Vérifié 13/07 — confirmés et précisés]**

- **`PUBLIC_DATA_ACCESS=true` est la valeur par défaut**, pas seulement une option possible : `backend/auth.py` lit `os.getenv("PUBLIC_DATA_ACCESS", "true")`, et quand elle est vraie, `require_auth` laisse passer les requêtes non authentifiées avec un tier `"public"`. La quasi-totalité des routeurs de données utilisent cette dépendance générique. Autrement dit, **en configuration par défaut, les routes tarifaires sont ouvertes sans clé** — ce n'est pas une possibilité résiduelle, c'est le comportement standard tant que personne ne bascule explicitement la variable.
- le module « Opportunités », étiqueté « Premium » jusque dans le frontend (`App.js`, onglet « Opportunités (Premium) »), est enregistré côté backend avec **la même dépendance d'authentification générique que n'importe quelle autre route de données** (`backend/routes/__init__.py`, `reports.py`) — aucune vérification de tier `pro`/`premium` n'existe dans `reports.py`. Sous `PUBLIC_DATA_ACCESS=true`, ce module est donc accessible sans clé du tout, en contradiction directe avec son étiquette commerciale.
- un rate limiting général existe bel et bien — middleware global (`backend/middlewares/rate_limiter.py`, 120 req/min, burst 20), appliqué à la quasi-totalité des routes hors `/api/health`. **Mais la clé de compteur est `IP:route`, pas la clé API** : deux clés API différentes derrière la même IP partagent le même quota, et une clé utilisée depuis plusieurs IP n'est jamais limitée par clé. Le rate limiting « par clé et par IP » annoncé n'existe donc que pour la moitié IP.
- les fonctions d'export, d'archivage et de consommation ne sont pas clairement associées aux formules commerciales.

---

## 4.6 Tests et qualité technique

### Points forts **[Vérifié 13/07 — chiffres corrigés]**

- tests backend nombreux ;
- tests des taxes, règles d'origine, logistique, provenance et crawlers ;
- tests frontend Vitest ;
- validation syntaxique Python ;
- cas réglementaire algérien de référence ;
- **`test_report_engine.py` contient 81 fonctions de test et 268 assertions** — plus que les « plus de 80 contrôles » annoncés en v1, et le fichier est hermétique (FX simulé via `monkeypatch`, aucun appel réseau réel).

### Limites **[Vérifié 13/07 — mécanisme précisé]**

- **16 autres fichiers de test** (`test_rules_of_origin.py`, `test_multi_country_and_taxes.py`, `test_banking_routes.py`, `test_oec_api.py`, etc.) dépendent effectivement d'un serveur déjà lancé (URLs `localhost:8001`/`8000` en dur, appels `requests.get`) ; `conftest.py` sonde la joignabilité et **les *skip* silencieusement** — sans serveur actif, ces suites ne signalent aucun échec, elles disparaissent simplement du rapport.
- la suite complète n'a pas été exécutée durant l'audit ;
- les imports optionnels peuvent masquer des indisponibilités ;
- les dépendances sont nombreuses et fortement figées ;
- aucune preuve unique de certification CI regroupant code, frontend, données et Docker n'est matérialisée.

**Constat supplémentaire, le plus important de cette révision :** la CI existante (`.github/workflows/ci.yml`) exécute bien des tests backend, mais avec `continue-on-error: true` sur la passe complète de `backend/tests/` — **un test backend qui échoue ne fait pas échouer la CI**. Seuls deux fichiers de test précis sont exécutés en mode strict ; le reste du dossier est déjà « best effort ». Sur les douze étapes de pipeline proposées en section 10 (Lot 9), seules deux existent partiellement aujourd'hui (tests backend non bloquants, tests frontend + build) : aucune des dix autres (contrat API, non-régression fiscale, validation de schéma, contrôle de provenance, détection de templating, cohérence manifeste/index, build Docker, test de démarrage, scan de sécurité, rapport de couverture) n'est présente dans les workflows GitHub Actions du dépôt.

Ce constat change la priorité relative du Lot 9 : il ne s'agit pas d'ajouter une CI de certification à une CI déjà fiable, mais de **rendre bloquant ce qui existe déjà avant d'empiler de nouvelles vérifications** — sans quoi les nouvelles étapes hériteraient du même défaut de gouvernance.

---

## 5. Audit du module Opportunités

## 5.1 Capacités actuelles **[Vérifié 13/07 — chemin corrigé]**

L'interface active est `frontend/src/components/reports/OpportunityReportTab.jsx` — **et non sous `components/opportunities/` comme le nom pourrait le laisser penser** ; c'est la seule interface Opportunités importée dans `App.js` (onglet « Opportunités (Premium) »). Elle couvre exactement les six modes annoncés :

- recherche de marchés pour un produit (`MarketSeekingView`) ;
- opportunité bilatérale produit-marché (`BilateralView`) ;
- export direct (`DirectExportView`) ;
- transformation industrielle (`TransformationView`) ;
- opportunités d'importation (`ImportOpportunitiesView`) ;
- estimation du besoin national (`NationalNeedView`).

Le moteur `backend/services/report_engine.py` orchestre notamment :

- flux commerciaux OEC ;
- production FAO, USGS ou UNIDO ;
- tarifs et préférences ZLECAf (via `benchmarking_service`) ;
- logistique multimodale (`logistics_opportunity_adapter`) ;
- fret ;
- financement du commerce, change et paiement (`finance_opportunity_adapter`) ;
- risque pays ;
- contexte macroéconomique — **nuance : ce dernier point est délégué à l'adaptateur finance et consommé côté frontend (`fin_profile.destination_macro`), il n'est pas calculé directement dans `report_engine.py`**.

## 5.2 Score actuel **[Vérifié 13/07 — confirmé exact]**

| Composante | Poids actuel |
|---|---:|
| Potentiel du marché | 25 % |
| Capacité de production | 25 % |
| Accessibilité logistique | 20 % |
| Faisabilité financière | 20 % |
| Risque pays | 10 % |

Confirmé au code près (`DEFAULT_WEIGHTS`, `report_engine.py`). Les composantes absentes sont exclues et les poids restants sont renormalisés : confirmé dans `_end_to_end_score`, qui divise la somme pondérée par le total des poids effectivement comptés.

## 5.3 Forces

- score détaillé et explicable ;
- valeurs absentes renvoyées comme indisponibles dans le moteur récent ;
- estimations signalées ;
- sources et méthodologies exposables ;
- prudence vis-à-vis des préférences en cas de réexportation ;
- couverture de tests importante ;
- scénarios export, import et transformation déjà structurés.

## 5.4 Faiblesses

### Protection Premium incomplète **[Vérifié 13/07 — confirmé, voir aussi 4.5]**

Le nom Premium n'est pas encore traduit en contrôle d'accès, quota et facturation techniques : `reports.py` utilise la même dépendance d'authentification générique que le reste de l'API, sans vérification de tier.

### Ancien module toujours présent **[Vérifié 13/07 — confirmé avec inventaire précis]**

Le dossier `frontend/src/components/opportunities/` contient une architecture héritée orpheline — confirmé qu'aucun fichier en dehors de ce dossier ne l'importe (`App.js` n'importe que `OpportunityReportTab` depuis `components/reports/`). Il comprend 10 fichiers (`OpportunitiesTab.jsx`, `AIAnalysis.jsx`, `BilateralTariffComparator.jsx`, `CountryComparison.jsx`, `OpportunitySummary.jsx`, `ProductAnalysisView.jsx`, `SubstitutionAnalysis.jsx`, `TradeSankeyDiagram.jsx`, `ValueChains.jsx`, `ZlecafImpactSimulator.jsx`) plus un `index.js`, avec des chiffres et multiplicateurs codés en dur — par exemple `ValueChains.jsx` (constantes `DEFAULT_VALUE_CHAINS` avec des valeurs en milliards codées en dur) ou `OpportunitiesTab.jsx` (repli sur `1650` milliards de commerce africain total, croissance annoncée `'+12.3%'` en dur). Ces éléments doivent être isolés ou supprimés afin d'éviter leur réactivation accidentelle.

### Coût rendu incomplet **[Vérifié 13/07 — confirmé]**

Le calcul correspond surtout à `FOB + fret` — confirmé dans `_landed_cost()` (`report_engine.py`), dont le commentaire précise lui-même que le change est « inclus séparément (voir volet finance) ». Il n'intègre pas systématiquement :

- assurance ;
- CAF ;
- droits et taxes cumulatives ;
- frais portuaires et de dédouanement ;
- transport intérieur ;
- stockage ;
- financement ;
- change ;
- formalités.

### Score avec faible couverture **[Vérifié 13/07 — correction factuelle importante]**

**Le champ `weight_coverage` n'est pas seulement une recommandation : il existe déjà dans le code** (`report_engine.py`, champ retourné `"weight_coverage": round(weight_used, 3)`) et il est déjà affiché dans l'interface (`OpportunityReportTab.jsx`, « Couverture X % »). Ce qui manque réellement n'est donc pas le calcul de couverture, mais **la règle de publication** : rien n'empêche aujourd'hui d'afficher un classement complet avec une couverture de 20 %. Le tableau ci-dessous reste la cible, mais le travail restant est un seuil de dégradation d'affichage à brancher sur une valeur déjà calculée, pas une nouvelle métrique à créer.

| Couverture | Règle d'affichage cible |
|---|---|
| ≥ 80 % | Score exploitable |
| 60–79 % | Score provisoire |
| 40–59 % | Indication partielle, sans classement principal |
| < 40 % | Aucun classement |

### Normalisation trop uniforme

Des seuils absolus identiques ne conviennent pas à tous les produits. Les scores doivent être normalisés par SH6, famille sectorielle ou percentile continental.

### Dépendance OEC

Le module nécessite un cache persistant, des snapshots versionnés, une source secondaire, un indicateur de fraîcheur et une stratégie de continuité contrôlée.

---

## 6. Parcours cible « Sourcing Import — Afrique du Nord »

## 6.1 Persona prioritaire

Importateur ou centrale d'achat en Algérie, au Maroc, en Tunisie, en Égypte ou en Libye recherchant de gros volumes de denrées alimentaires africaines : bananes, café, noix de cajou, arachides, amandes ou autres fruits à coque.

## 6.2 Entrées utilisateur

- pays et port de destination ;
- produit et code SH6 ;
- volume annuel et volume par expédition ;
- qualité, variété, calibre et conditionnement ;
- fréquence souhaitée ;
- certification sanitaire et commerciale ;
- Incoterm ;
- prix cible et devise ;
- fenêtre de livraison ;
- tolérance au risque ;
- nombre maximal de pays fournisseurs.

## 6.3 Analyse attendue

| Dimension | Résultat attendu |
|---|---|
| Capacité exportable | Production moins consommation et engagements export connus |
| Volume disponible | Compatibilité avec le besoin et la saison |
| Prix | Prix export et intervalle de confiance |
| Coût total rendu | CAF, fiscalité, port, intérieur, financement et change |
| ZLECAf | Préférence réellement applicable et condition d'origine |
| Sanitaire | SPS, phytosanitaire, traçabilité et documents |
| Logistique | Lignes, transit, transbordement et chaîne du froid |
| Fournisseurs | Organisations et entreprises vérifiables |
| Risque | Pays, fournisseur, paiement et concentration |
| Résilience | Scénario multi-origines et solution de repli |

## 6.4 Produits pilotes

| Produit | Code indicatif | Travail requis |
|---|---|---|
| Bananes fraîches | SH 080390 | variété, chaîne du froid, mûrisserie, saisonnalité |
| Café | SH 0901 | vert/torréfié, arabica/robusta, grade, certification |
| Noix de cajou | SH6 à préciser selon état | brute/décortiquée, rendement et transformation |
| Arachides | SH6 à préciser | coque/décortiquée, aflatoxines, usage |
| Amandes et autres fruits à coque | SH6 à préciser | espèce, état, calibre et origine |

Le terme « noix » ne doit jamais être utilisé comme unité de calcul sans classification SH6 et spécification commerciale.

## 6.5 Sortie du rapport

Le rapport classe au minimum :

1. l'origine au coût total le plus faible ;
2. l'origine offrant le volume le plus sûr ;
3. la meilleure origine ZLECAf ;
4. l'origine au risque le plus faible ;
5. la meilleure combinaison multi-origines.

Pour chaque scénario :

- tonnage attribué ;
- prix par tonne ;
- coût total rendu ;
- droits, taxes et économie ZLECAf ;
- délai et fenêtre d'approvisionnement ;
- documents nécessaires ;
- contraintes SPS ;
- score de risque ;
- niveau de confiance ;
- sources et date de référence.

---

## 7. Architecture technique cible

## 7.1 Principes

1. Une seule donnée canonique par version de dataset.
2. Un seul moteur fiscal souverain.
3. Une provenance au niveau de chaque mesure.
4. Aucun fallback numérique silencieux.
5. Tout rapport est reproductible par identifiants de version.
6. Les estimations sont séparées des faits réglementaires.
7. La qualité des données influence le score et sa publication.

## 7.2 Composants cibles

| Composant | Responsabilité |
|---|---|
| Ingestion | Collecte, extraction, normalisation et preuve source |
| Validation | Schéma, cohérence, duplication, authenticité et contrôles métier |
| Registry | Manifeste, versions, statut ACTIVE et empreintes |
| Tariff Core | Mesures, séquence fiscale et calcul déterministe |
| Origin Core | Éligibilité ZLECAf et justification |
| Landed Cost | CAF, fiscalité, logistique, financement et change |
| Opportunity Engine | demande, offre, score et scénarios |
| Sourcing Optimizer | allocation multi-origines sous contraintes |
| API v2 | contrat stable, authentification et quotas |
| Frontend | collecte des paramètres, restitution et confiance |
| Audit & Monitoring | logs, métriques, alertes et reproductibilité |

## 7.3 Contrat minimal du calcul

```json
{
  "request_id": "uuid",
  "classification": {},
  "provenance": {},
  "measures_applied": [],
  "calculation_steps": [],
  "npf_result": {},
  "preferential_result": {},
  "origin_eligibility": {},
  "formalities": [],
  "warnings": [],
  "legal_references": [],
  "calculation_version": "...",
  "dataset_version": "..."
}
```

## 7.4 Contrat minimal d'un indicateur d'opportunité

```json
{
  "value": null,
  "unit": "USD",
  "status": "VERIFIED|PARTIAL|ESTIMATED|UNAVAILABLE",
  "reliability": "A|B|C|D",
  "source": {},
  "reference_period": "2025",
  "retrieved_at": "ISO-8601",
  "methodology": "...",
  "warnings": []
}
```

## 7.5 Manifeste du dataset

Chaque lot publié doit contenir :

- `dataset_id` et version du schéma ;
- commit du code d'ingestion ;
- date de génération ;
- sources et périodes ;
- lignes par pays ;
- répartition par statut et grade ;
- empreinte SHA-256 des fichiers ;
- version des index ;
- résultats QA ;
- approbateur ;
- statut `DRAFT`, `VALIDATED`, `ACTIVE` ou `RETIRED`.

**[Vérifié 13/07]** Rappel : ce manifeste est à construire intégralement — aucun artefact existant ne s'en approche (voir 4.3).

---

## 8. Score d'opportunité 2.0

## 8.1 Pondération recommandée

| Dimension | Poids |
|---|---:|
| Demande observée | 20 % |
| Croissance de la demande | 10 % |
| Capacité exportable | 15 % |
| Avantage tarifaire effectif | 15 % |
| Logistique | 15 % |
| Financement et paiement | 10 % |
| Risque marché | 10 % |
| Barrières non tarifaires | 5 % |

## 8.2 Règles

- normalisation par percentiles SH6 ou groupe de produits ;
- période glissante de 3 à 5 ans pour la croissance ;
- pénalité de fraîcheur ;
- pénalité de concentration fournisseur ;
- pénalité de données estimées ;
- exclusion du classement si couverture inférieure à 40 % (à brancher sur le `weight_coverage` déjà calculé, voir 5.4) ;
- affichage distinct du score commercial et du score de confiance ;
- pondérations configurables selon le profil : exportateur, importateur, banque, transitaire, investisseur ou administration.

---

## 9. Coût total rendu cible

Le coût total doit être calculé sans confondre données certaines et hypothèses.

\[
CTD = FOB + Fret + Assurance + Droits + Taxes + Port + Dédouanement + Transport\ intérieur + Stockage + Financement + Change + Formalités
\]

Chaque poste porte : montant, devise, statut, source, hypothèse et intervalle d'incertitude.

Trois scénarios sont obligatoires :

- prudent : coûts hauts, délais longs, pénétration faible ;
- central : hypothèses médianes ;
- offensif : coût logistique optimisé et volume supérieur.

---

## 10. Plan technique détaillé et mesurable

La feuille de route proposée s'étend sur 12 semaines. Les durées sont indicatives et supposent une petite équipe pluridisciplinaire disponible.

## Lot 0 — Baseline et gouvernance

**Période :** semaine 1
**Objectif :** établir une référence incontestable du code, des données et des décisions.

### Travaux

- geler le périmètre sur `afcfta-final-002` ;
- créer un registre des décisions d'architecture ;
- inventorier routes, services, collections, fichiers et index ;
- identifier précisément le dataset servi ;
- capturer une baseline des tests et performances ;
- nommer les responsables produit, douane, data, backend et frontend.
- **[Ajout 13/07]** résoudre la collision de préfixe `/enhanced-calculator` entre `regional_calculator.py` et `enhanced_calculator.py` avant tout autre travail sur les routes de calcul.

### Livrables

- cartographie technique ;
- registre des routes ;
- inventaire des datasets ;
- matrice RACI ;
- baseline CI et performance.

### Critères d'acceptation

- 100 % des endpoints de calcul associés à leur service réel ;
- 100 % des datasets accessibles inventoriés ;
- un seul lot identifié comme lot actuellement servi ;
- propriétaire désigné pour chaque composant critique ;
- **[Ajout 13/07]** zéro collision de préfixe de route détectée par un script de vérification statique des routeurs FastAPI.

## Lot 1 — Verrouillage de la provenance

**Période :** semaines 1 à 2
**Objectif :** atteindre zéro promotion abusive vers `VERIFIED/A`.

### Travaux

- corriger DZA de `VERIFIED/A` vers `PARTIAL/B` lorsque la source est ConformePro (dans `engine/output/DATA_STATUS.json` **et** sa copie `frontend/public/data/DATA_STATUS.json`) ;
- réconcilier les deux chiffres de couverture algérienne (16 569 vs 17 115 lignes) avant de publier tout chiffre de couverture DZA ;
- introduire la provenance au niveau de chaque mesure ;
- créer une machine d'état interdisant les promotions implicites ;
- valider les références juridiques et périodes ;
- ajouter un contrôle anti-template inter-pays (seuil d'alerte si l'écart-type des volumes par pays reste sous un seuil suspect, cf. bande 16 567-16 575 observée) ;
- rendre la provenance visible dans tous les calculs.

### KPI

| KPI | Cible |
|---|---:|
| Mesures sans statut | 0 |
| Promotions illégitimes détectées dans le lot publié | 0 |
| Résultats API exposant dataset et provenance | 100 % |
| Tests de règles de statut réussis | 100 % |

### Critère Go/No-Go

Le lot ne peut être publié si une mesure secondaire ou synthétique est marquée `VERIFIED/A`.

## Lot 2 — Dataset Registry et manifeste unique

**Période :** semaines 2 à 3
**Objectif :** rendre toute réponse reproductible à partir d'un seul dataset actif.

### Travaux

- définir le schéma du manifeste ;
- calculer les empreintes ;
- lier index, fichiers et rapports QA ;
- créer le mécanisme atomique d'activation ;
- supprimer les fallbacks vers des lots non actifs ;
- archiver les anciens lots comme `RETIRED` ;
- **[Ajout 13/07]** éliminer la duplication silencieuse entre `engine/output/DATA_STATUS.json` et `frontend/public/data/DATA_STATUS.json` en faisant du second une copie générée automatiquement du premier (jamais éditée à la main), ou en servant directement le premier via l'API.

### KPI

| KPI | Cible |
|---|---:|
| Datasets actifs simultanément | 1 |
| Fichiers actifs avec empreinte | 100 % |
| Réponses avec `dataset_version` | 100 % |
| Écarts entre manifeste et index | 0 |

## Lot 3 — Moteur souverain et API v2

**Période :** semaines 3 à 5
**Objectif :** garantir un résultat identique quel que soit le parcours utilisateur.

### Travaux

- déclarer `engine/calculation.py` comme noyau et **le brancher effectivement** — aujourd'hui il n'est appelé par aucune route (voir 4.2) ;
- créer le service d'orchestration ;
- ajouter `/calculations` à l'espace `/api/v2` déjà existant (`backend/api/v2/endpoints.py`) ;
- brancher origine, formalités et provenance ;
- adapter temporairement les anciennes routes ;
- migrer `CalculatorTab.jsx` ;
- instrumenter les divergences pendant la transition.

### KPI

| KPI | Cible |
|---|---:|
| Parcours frontend utilisant l'API v2 | 100 % |
| Divergences sur le corpus de référence | 0 |
| Calculs avec étapes explicites | 100 % |
| p95 hors dépendances externes | < 500 ms |
| Erreurs serveur sur cas valides | < 0,5 % |

### Critère Go/No-Go

Zéro divergence sur au moins 100 cas réglementaires de référence couvrant droits ad valorem, taxes cumulatives, exonérations et préférences.

## Lot 4 — Certification Algérie

**Période :** semaines 4 à 8
**Objectif :** établir l'Algérie comme premier pays de référence certifiable.

### Travaux

- importer les 98 chapitres ConformePro comme `PARTIAL/B` ;
- réconcilier nombres de lignes et sous-positions (y compris l'écart 16 569 / 17 115 identifié en 4.3) ;
- constituer la bibliothèque DGD/Journal officiel ;
- recouper DD, TVA, TCS, PRCT, DAPS, TIC, avantages et formalités ;
- promouvoir mesure par mesure ;
- constituer un corpus de cas validés par expert.

### KPI

| KPI | Cible à S8 |
|---|---:|
| Chapitres importés | 98/98 |
| Lignes sans classification nationale valide | < 0,5 % |
| Mesures avec référence exploitable | ≥ 95 % |
| Positions prioritaires certifiées par source primaire | ≥ 1 000 |
| Cas experts de non-régression | ≥ 100 |
| Écart monétaire sur cas experts | 0 DZD hors règles d'arrondi documentées |

## Lot 5 — Assainissement du module Opportunités

**Période :** semaines 3 à 5
**Objectif :** éliminer toute donnée commerciale de secours non sourcée.

### Travaux

- confirmer `OpportunityReportTab.jsx` (`frontend/src/components/reports/`) comme interface active ;
- isoler ou retirer l'ancien module `frontend/src/components/opportunities/` (10 fichiers orphelins identifiés, voir 5.4) ;
- supprimer constantes et multiplicateurs de fallback (ex. `ValueChains.jsx`, `OpportunitiesTab.jsx`) ;
- ajouter un lint/test de constantes interdites ;
- imposer `UNAVAILABLE` en cas d'absence ;
- **brancher le seuil de publication sur `weight_coverage`, déjà calculé et déjà affiché** — il ne reste qu'à en faire une règle de dégradation d'affichage, pas une nouvelle métrique (voir 5.4).

### KPI

| KPI | Cible |
|---|---:|
| Fallbacks numériques non sourcés | 0 |
| Indicateurs portant statut et source | 100 % |
| Rapports avec couverture affichée | 100 % (déjà acquis) |
| Classements publiés sous 40 % de couverture | 0 |

## Lot 6 — Score 2.0 et coût total rendu

**Période :** semaines 5 à 8
**Objectif :** produire une recommandation financièrement exploitable.

### Travaux

- calibrer les percentiles par SH6 ;
- intégrer croissance, avantage tarifaire et barrières non tarifaires ;
- construire le moteur de coût total (au-delà du simple FOB + fret actuel de `_landed_cost()`) ;
- distinguer coûts vérifiés, estimés et absents ;
- générer trois scénarios ;
- ajouter analyses de sensibilité fret et change.

### KPI

| KPI | Cible |
|---|---:|
| Postes de coût explicitement qualifiés | 100 % |
| Rapports avec bas/central/haut | 100 % |
| Erreur du coût sur cas documentés | ≤ 2 % |
| Produits pilotes avec benchmark SH6 | ≥ 5 |
| Rapports indiquant coûts non inclus | 100 % |

## Lot 7 — MVP Sourcing Import

**Période :** semaines 7 à 10
**Objectif :** comparer des fournisseurs africains pour cinq produits alimentaires à gros volume vers l'Afrique du Nord.

### Périmètre MVP

- destinations : Algérie, Maroc et Tunisie ;
- produits : bananes, café, cajou, arachides, amandes ;
- scénarios mono-origine et multi-origines ;
- coût rendu jusqu'au port de destination ;
- contrôles SPS et documents principaux ;
- sources et confiance visibles.

### Travaux

- modèle de spécification d'achat ;
- connecteurs offre, commerce, prix et logistique ;
- moteur de capacité exportable ;
- optimisation multi-origines sous contraintes ;
- fiche fournisseur avec statut de vérification ;
- interface de comparaison et export du rapport.

### KPI

| KPI | Cible MVP |
|---|---:|
| Produits complètement paramétrés | 5 |
| Destinations nord-africaines | 3 |
| Origines comparables par produit | ≥ 3 lorsque les données le permettent |
| Rapports avec option multi-origines | 100 % |
| Fournisseurs affichés sans source vérifiable | 0 |
| Temps de génération p95 | < 15 s avec cache |
| Cas pilotes validés par importateurs | ≥ 10 |

## Lot 8 — Sécurité commerciale et Premium

**Période :** semaines 8 à 10
**Objectif :** rendre l'accès Premium techniquement effectif et mesurable.

### Travaux

- définir les plans Public, Basic, Premium et Enterprise ;
- ajouter entitlements et quotas — **en priorité sur `reports.py`, qui n'a aujourd'hui aucune vérification de tier malgré son étiquette « Premium »** ;
- basculer `PUBLIC_DATA_ACCESS` à `false` par défaut en environnement de production, avec activation explicite et documentée si un accès public est réellement souhaité ;
- passer le rate limiting d'une clé `IP:route` à une clé combinant API key et IP, pour que la limite par clé soit réellement effective ;
- expiration et rotation des clés ;
- journalisation des rapports ;
- protection contre l'énumération massive ;
- génération asynchrone et archivage ;
- exports PDF/Excel réservés selon formule.

### KPI

| KPI | Cible |
|---|---:|
| Routes Premium protégées | 100 % |
| Requêtes tarifaires commerciales tracées | 100 % |
| Tests d'autorisation négatifs réussis | 100 % |
| Clés avec expiration/rotation | 100 % |
| Contournements de quota au test | 0 |
| Accès public par défaut en production | Désactivé |

## Lot 9 — CI de certification et observabilité

**Période :** semaines 10 à 12
**Objectif :** empêcher toute publication non conforme.

**[Ajout 13/07]** Préalable indispensable : retirer `continue-on-error: true` de l'étape de tests backend dans `.github/workflows/ci.yml`. Aujourd'hui cette étape échoue silencieusement sans bloquer la fusion — toute nouvelle étape de certification ajoutée par ce lot hériterait du même défaut si ce point n'est pas traité en premier.

### Pipeline obligatoire

1. tests unitaires backend (**bloquant, sans `continue-on-error`**) ;
2. tests frontend ;
3. tests contractuels API ;
4. non-régression fiscale ;
5. validation du schéma ;
6. contrôle de provenance ;
7. détection de templating ;
8. cohérence manifeste/index ;
9. build Docker ;
10. test de démarrage ;
11. scan de sécurité ;
12. rapport de couverture.

### KPI

| KPI | Cible |
|---|---:|
| Publications contournant la CI | 0 |
| Étapes bloquantes automatisées | 12/12 |
| Disponibilité API mensuelle | ≥ 99,5 % |
| Calculs reproductibles par version | 100 % |
| Temps moyen de diagnostic d'un calcul | < 15 min |

---

## 11. Jalons de pilotage

| Jalon | Échéance cible | Résultat observable |
|---|---|---|
| J1 — Baseline | Fin S1 | routes et dataset actif identifiés, collision `/enhanced-calculator` résolue |
| J2 — Confiance | Fin S2 | zéro promotion abusive |
| J3 — Registry | Fin S3 | manifeste unique actif |
| J4 — API souveraine | Fin S5 | frontend migré et zéro divergence |
| J5 — Opportunités assainies | Fin S5 | zéro fallback numérique, seuil de couverture branché |
| J6 — Algérie intermédiaire | Fin S8 | 98 chapitres et 1 000 positions prioritaires certifiées |
| J7 — Coût rendu | Fin S8 | scénarios complets sur produits pilotes |
| J8 — Sourcing MVP | Fin S10 | cinq produits, trois destinations |
| J9 — Certification production | Fin S12 | CI complète et bloquante, sécurité et observabilité |

---

## 12. Matrice RACI recommandée

| Domaine | Responsable | Approbateur | Consulté |
|---|---|---|---|
| Provenance | Data lead | Expert douanier | Backend |
| Calcul fiscal | Backend lead | Expert douanier | QA |
| Origine ZLECAf | Expert origine | Direction produit | Backend |
| Manifeste | Data engineering | Tech lead | DevOps |
| Opportunités | Product/data analyst | Product owner | Experts sectoriels |
| Sourcing | Product owner | Direction | Importateurs pilotes |
| Sécurité | Backend/DevOps | Tech lead | Product owner |
| Certification CI | QA/DevOps | Tech lead | Tous responsables |

Une même personne peut cumuler plusieurs rôles dans une petite équipe, mais aucune promotion `VERIFIED/A` ne devrait être approuvée uniquement par l'auteur de l'extraction.

---

## 13. Registre des risques

| Risque | Probabilité | Impact | Réponse |
|---|---:|---:|---|
| Tarif synthétique présenté comme réel | Élevée | Critique | blocage CI et badge obligatoire |
| Divergence entre calculateurs | Élevée | Critique | moteur souverain et tests parallèles |
| Collision de préfixe de routes non détectée | **Avérée** | Élevé | script de vérification statique des routeurs en CI |
| Source privée qualifiée A | Élevée | Élevé | machine d'état et revue experte |
| Dataset non identifiable | Élevée | Élevé | manifeste ACTIVE unique |
| Accès public par défaut en production | **Avérée** | Élevé | bascule `PUBLIC_DATA_ACCESS=false` par défaut |
| CI non bloquante masquant des régressions | **Avérée** | Élevé | retrait de `continue-on-error` sur les tests backend |
| Score avec données insuffisantes | Moyenne | Élevé | seuil de couverture (déjà calculé, à activer) |
| Coût rendu incomplet interprété comme total | Élevée | Élevé | libellé, contrat et postes absents |
| Dépendance à OEC | Moyenne | Moyen | cache, snapshots et seconde source |
| Fallback frontend réactivé | Moyenne | Élevé | suppression et test statique |
| Accès Premium non protégé | **Avérée** | Élevé | entitlements et quotas sur `reports.py` |
| Fournisseur non vérifié affiché | Moyenne | Élevé | statut fournisseur et preuve |
| Données SPS obsolètes | Moyenne | Critique | fraîcheur, source primaire et avertissement |
| Planning sous-estimé | Moyenne | Moyen | jalons Go/No-Go et réduction du MVP |

---

## 14. Backlog prioritaire

### P0 — Bloquant confiance

- corriger les statuts Algérie incohérents (`VERIFIED/A` vs `PARTIAL/B`, et l'écart 16 569 / 17 115 lignes) ;
- identifier le dataset réellement servi ;
- empêcher les promotions abusives ;
- créer le manifeste actif ;
- déclarer et **brancher réellement** le moteur souverain (`engine/calculation.py` n'est appelé par aucune route aujourd'hui) ;
- supprimer les fallbacks numériques visibles ;
- **résoudre la collision de préfixe `/enhanced-calculator`** (`regional_calculator.py` vs `enhanced_calculator.py`) ;
- **retirer `continue-on-error` sur les tests backend en CI** ;
- **basculer `PUBLIC_DATA_ACCESS` à `false` par défaut en production**.

### P1 — Valeur commerciale

- migrer le frontend vers API v2 ;
- provenance par mesure ;
- score 2.0 ;
- coût total rendu ;
- certification Algérie ;
- MVP Sourcing Import ;
- activer le seuil de publication sur `weight_coverage` (déjà calculé, non exploité).

### P2 — Industrialisation

- offre Premium avec entitlement réel sur `reports.py` ;
- quotas et sécurité, rate limiting combiné clé+IP ;
- exports et archivage ;
- observabilité ;
- CI de certification complète (10 étapes restantes) ;
- alertes de mise à jour.

### P3 — Extension

- Maroc/ADIL ou EAC CET après stabilisation ;
- nouvelles destinations nord-africaines ;
- nouveaux produits agricoles ;
- portefeuille et alertes ;
- API Enterprise.

---

## 15. Cas de recette obligatoires

### Calculateur

1. Algérie `0101211100`, NPF et ZLECAf.
2. Taxe cumulative sans mesure amont : avertissement obligatoire.
3. Droit spécifique non résolu : résultat partiel, jamais zéro implicite.
4. Source ConformePro : `PARTIAL/B`.
5. Mesure recoupée au Journal officiel : promotion contrôlée.
6. Absence de réciprocité : aucune préférence automatique.
7. Réexportation sans origine : préférence refusée.
8. **[Ajout 13/07]** Un même calcul soumis à `/calculate-tariff`, `/authentic-tariffs/calculate` et `/postgres-tariffs/calculate` doit produire un résultat identique (ou une divergence documentée et justifiée) — test de non-régression croisé entre routes.

### Opportunités

1. produit sans donnée OEC ;
2. corridor sans fret fiable ;
3. production non confirmée ;
4. score sous 40 % de couverture ;
5. comparaison de marchés avec fraîcheurs différentes ;
6. transformation avec règle d'origine ;
7. sensibilité au change et au fret.

### Sourcing alimentaire

1. bananes vers Alger avec chaîne du froid ;
2. café vert vers Casablanca ;
3. cajou brute versus décortiquée ;
4. arachides avec contrainte aflatoxines ;
5. besoin dépassant la capacité d'une origine ;
6. allocation sur trois origines ;
7. rupture saisonnière ;
8. fournisseur sans preuve ;
9. préférence ZLECAf non démontrée ;
10. comparaison coût bas/central/haut.

---

## 16. Définition de « terminé »

Une fonctionnalité n'est terminée que si :

- son contrat est versionné ;
- ses données portent provenance et fraîcheur ;
- les erreurs et absences sont explicites ;
- les tests unitaires, contractuels et métier réussissent **et sont exécutés en mode bloquant en CI** ;
- les logs permettent de reproduire le résultat ;
- la documentation utilisateur est mise à jour ;
- les critères d'acceptation sont mesurés ;
- aucune régression de confiance n'est introduite.

---

## 17. Tableau de bord de direction

Le pilotage hebdomadaire doit afficher au minimum :

| Indicateur | Formule |
|---|---|
| Couverture certifiée | mesures `VERIFIED/A` / mesures actives |
| Couverture utile | mesures `VERIFIED + PARTIAL` / mesures actives |
| Dette synthétique | mesures `SYNTHETIC` / mesures actives |
| Reproductibilité | réponses avec versions / réponses totales |
| Divergence moteur | cas divergents / corpus exécuté |
| Qualité Opportunités | indicateurs sourcés / indicateurs affichés |
| Couverture score | poids disponibles / poids théoriques |
| Précision coût rendu | erreur moyenne sur cas documentés |
| Adoption Sourcing | rapports complets / sessions initiées |
| Conversion Premium | comptes Premium / comptes actifs éligibles |
| Fiabilité service | succès API / requêtes valides |
| **[Ajout 13/07]** CI bloquante | étapes bloquantes actives / étapes du pipeline cible (12) |

---

## 18. Décisions immédiates proposées

À valider avant le démarrage :

1. `afcfta-final-002` demeure l'unique socle de travail.
2. `engine/calculation.py` devient le noyau fiscal souverain — **et doit être effectivement branché**, pas seulement désigné.
3. ConformePro reste `PARTIAL/B` jusqu'au recoupement primaire, dans les deux copies de `DATA_STATUS.json`.
4. Un seul dataset peut être `ACTIVE`.
5. Les données synthétiques ne participent pas aux classements par défaut.
6. `OpportunityReportTab.jsx` (sous `components/reports/`) reste l'interface Opportunités de référence.
7. Aucun score n'est classé sous 40 % de couverture — en s'appuyant sur `weight_coverage`, déjà calculé.
8. Le premier MVP Sourcing cible Algérie, Maroc, Tunisie et cinq produits.
9. Le lancement production est conditionné à la CI de certification **rendue bloquante**, pas seulement étendue.
10. **[Ajout 13/07]** La collision de préfixe `/enhanced-calculator` est corrigée avant tout développement additionnel sur les routes de calcul.
11. **[Ajout 13/07]** `PUBLIC_DATA_ACCESS` passe à `false` par défaut dès l'environnement de production.

---

## 19. Résultat attendu à 12 semaines

À l'issue du programme, la plateforme doit être capable de démontrer :

- un moteur tarifaire unique utilisé par tous les parcours ;
- une provenance explicite jusqu'au niveau de la mesure ;
- un dataset actif versionné et reproductible ;
- une base Algérie complète en `PARTIAL/B`, avec au moins 1 000 positions prioritaires promues sur preuve primaire ;
- zéro fallback numérique non sourcé dans Opportunités ;
- un score commercial accompagné de son score de confiance ;
- un coût rendu complet ou une liste explicite des coûts manquants ;
- un MVP de sourcing sur cinq produits alimentaires et trois destinations nord-africaines ;
- une offre Premium effectivement protégée ;
- une CI empêchant la publication de données non conformes, **de façon réellement bloquante**.

La réussite du programme ne se mesure pas au nombre de nouvelles fonctionnalités, mais à la capacité de produire une recommandation commerciale traçable, reproductible et suffisamment fiable pour soutenir une décision réelle d'importation ou d'exportation.

---

## 20. Note méthodologique

Le présent document consolide les constats issus de l'audit technique réalisé sur la branche principale de `afcfta-final-002` et les recommandations fonctionnelles formulées pour les modules Calculateur, Opportunités et Sourcing Import. Les estimations de durée devront être recalibrées après le Lot 0, sur la base de l'équipe effectivement mobilisée, de l'état de la CI et de l'accès aux sources réglementaires primaires.

**[Ajout 13/07]** Cette révision v2 a été produite par vérification directe et systématique du code source du dépôt (lecture de fichiers, recherche de motifs, inspection des routes FastAPI, des workflows CI et des fichiers de données), et non par relecture documentaire seule. Le détail des preuves figure en Annexe A.

---

## 21. Modèle opérationnel réel : expert unique amplifié par l'IA

Le projet est dirigé et arbitré par une seule personne disposant d'une expertise douanière africaine couvrant la classification, la valeur, l'origine, les régimes tarifaires, les procédures, la facilitation, le contrôle et l'économie du commerce international. Son développement a été accéléré par une chaîne d'outils d'intelligence artificielle et de prototypage comprenant notamment ChatGPT, Emergent, Replit, GitHub Copilot, GitHub et Claude.

Ce contexte impose une adaptation de la feuille de route : la plateforme ne doit pas reproduire l'organisation coûteuse d'un grand éditeur de données. Elle doit appliquer une logique de contrôle par les risques, d'automatisation maximale et de validation humaine concentrée sur les exceptions.

### 21.1 Répartition des responsabilités

| Fonction | Responsable |
|---|---|
| Vision, priorités et doctrine douanière | Expert fondateur |
| Arbitrage des divergences réglementaires | Expert fondateur |
| Recherche et présélection documentaire | Agents IA |
| Extraction et normalisation | Pipelines + IA |
| Développement et tests | IA de code sous contrôle du fondateur |
| Contrôles de cohérence | CI automatisée |
| Validation finale des cas sensibles | Expert fondateur |
| Publication | Pipeline contrôlé avec Go/No-Go |

### 21.2 Principe de contrôle par exception

Le fondateur ne doit pas vérifier manuellement chaque ligne. Le système doit lui présenter uniquement :

- les divergences entre sources ;
- les taxes complexes ou cumulatives ;
- les droits spécifiques, mixtes ou contingents ;
- les changements de texte ;
- les classifications ambiguës ;
- les préférences non réciproques ;
- les règles d'origine complexes ;
- les exigences SPS susceptibles de bloquer une opération ;
- les positions à forte demande commerciale.

### 21.3 Collecte guidée par la demande

La couverture doit progresser en fonction des recherches et des revenus :

1. une demande utilisateur révèle un pays-produit insuffisamment couvert ;
2. le besoin entre dans une file de recherche priorisée ;
3. les agents collectent les sources accessibles ;
4. les pipelines extraient et comparent ;
5. l'expert tranche uniquement les anomalies ;
6. le lot est publié avec son niveau réel de confiance.

La formule de priorité devient :

\[
Priorité = Demande\ utilisateur \times Valeur\ commerciale \times Accessibilité\ documentaire \times Réutilisabilité
\]

---

## 22. Le module statistique comme socle transversal

Le module statistique doit être élevé au rang de moteur central. Il dessert les professionnels du commerce, mais également la presse, les universités, les administrations, les chambres de commerce, les banques et les institutions régionales.

### 22.1 Fonctions cibles

| Parcours | Capacités |
|---|---|
| Produit | importateurs, exportateurs, partenaires, séries, quantités et croissance |
| Pays | profil commercial, produits, partenaires, déficits et excédents |
| Comparaison | comparaison de deux à cinq pays sur une même base |
| Bilatéral | échanges, complémentarité et potentiel non exploité |
| Intra-africain | part africaine, substitution et dépendance extérieure |
| Presse | graphiques, chiffres clés, source et citation |
| Recherche | séries téléchargeables, méthodologie et métadonnées |

### 22.2 Doctrine statistique

La plateforme doit employer l'expression « données commerciales sourcées et traçables » plutôt que « chiffres vrais » sans nuance. Elle doit distinguer :

- données déclarées par le pays ;
- données miroir ;
- données harmonisées ;
- estimations ;
- quantités absentes ;
- valeurs révisées ;
- changements de révision SH.

### 22.3 Contrat minimal d'un flux commercial

```json
{
  "reporter": "DZA",
  "partner": "CIV",
  "flow": "IMPORT",
  "hs_code": "090111",
  "hs_revision": "HS2022",
  "period": "2024",
  "trade_value": 0,
  "net_weight": null,
  "quantity": null,
  "quantity_unit": null,
  "source": "OEC|UN_COMTRADE|NATIONAL",
  "data_type": "REPORTED|MIRROR|ESTIMATED",
  "retrieved_at": "ISO-8601",
  "dataset_version": "...",
  "reliability": "A|B|C|D"
}
```

### 22.4 Architecture multi-fournisseurs

Le frontend ne doit jamais dépendre directement d'OEC ou d'une future API payante. Une interface `TradeDataProvider` doit normaliser tous les fournisseurs :

```python
class TradeDataProvider:
    def get_trade_by_product(...): ...
    def get_trade_by_country(...): ...
    def get_bilateral_trade(...): ...
    def get_time_series(...): ...
    def get_quantities(...): ...
    def get_metadata(...): ...
```

Fournisseurs envisageables :

- OEC historique ou sous licence adaptée ;
- UN Comtrade ;
- données nationales ;
- API professionnelle future ;
- snapshots autorisés et versionnés.

L'entrepôt interne doit conserver les résultats normalisés afin de réduire les coûts, garantir la reproductibilité et éviter un appel payant à chaque consultation.

### 22.5 Contrôles de qualité

- rupture anormale entre deux années ;
- valeur sans quantité ;
- prix unitaire apparent aberrant ;
- doublon reporter-partner-produit-période ;
- conflit entre donnée déclarée et miroir ;
- confusion entre SH1992, SH2012, SH2017 et SH2022 ;
- année partielle présentée comme complète ;
- réexportation probable ;
- révision rétrospective d'une série.

---

## 23. Croisement commerce, production, logistique et origine

La plateforme doit produire une lecture intégrée plutôt que quatre bases juxtaposées.

### 23.1 Commerce et production

Le croisement permet de distinguer un producteur, un transformateur et un réexportateur.

\[
Disponibilité\ apparente = Production + Importations - Exportations
\]

\[
Dépendance\ aux\ importations = \frac{Importations}{Production + Importations - Exportations}
\]

Ces résultats sont qualifiés `ESTIMATED` si la consommation, les pertes ou les stocks ne sont pas observés.

### 23.2 Commerce et logistique

Chaque relation produit-pays doit être enrichie par :

- port d'origine et port de destination ;
- ligne directe ou transbordement ;
- distance et délai ;
- conteneur sec, frigorifique ou vrac ;
- coût par tonne ;
- transport intérieur ;
- congestion et saisonnalité ;
- fiabilité de la donnée logistique.

### 23.3 Commerce et origine

Un flux exporté par un pays africain n'est pas automatiquement originaire de ce pays. Le moteur doit confronter :

- production nationale ;
- importations d'intrants ou du produit ;
- niveau de transformation ;
- règle spécifique au produit ;
- cumul autorisé ;
- document de preuve requis.

### 23.4 Commerce et réglementation

Le module statistique alimente le calculateur et non l'inverse : les marchés à fort volume sont utilisés pour prioriser la certification des tarifs, taxes, formalités et mesures SPS.

---

## 24. Produits analytiques et communautés utilisatrices

| Produit | Public | Résultat |
|---|---|---|
| Observatoire du commerce africain | Presse, universités, institutions | séries, graphiques et tendances |
| Fiche produit africaine | Importateurs et exportateurs | commerce, production, tarif, origine et logistique |
| Fiche pays | Tous publics | structure commerciale et opportunités |
| Comparateur de marchés | Professionnels et chercheurs | comparaison de deux à cinq pays |
| Analyse bilatérale | Chambres et administrations | complémentarité et potentiel |
| Sourcing Import | Importateurs | fournisseurs, volumes, coût et risques |
| Rapport expert | Entreprises | étude validée et décisionnelle |
| API | Plateformes et institutions | intégration de données versionnées |

Pour la presse et l'université, chaque export doit comprendre la source, la période, la date d'extraction, la méthodologie, les limites et une citation recommandée.

---

## 25. Commercialisation adaptée à la maturité des données

La grille commerciale fournie constitue une bonne hypothèse de marché, mais les droits d'accès doivent être alignés sur la maturité réelle — **et sur l'état actuel de la protection technique, qui est aujourd'hui insuffisant pour facturer un accès Premium (voir 4.5)**.

### 25.1 Offres recommandées au lancement

| Offre | Prix indicatif | Contenu sécurisé au lancement |
|---|---:|---|
| Free | 0 $ | exploration, statistiques historiques, cinq calculs/jour |
| Pro | 29 $/mois | statistiques avancées, exports, rapports indicatifs |
| Business | 99 $/mois | cinq utilisateurs, comparaisons, rapports et petit quota API |
| Rapport expert | 99 à 499 $ | dossier produit-pays avec validation humaine |
| Veille | 19 $/mois | bulletin sourcé et alertes |
| API | après pilote | données autorisées à la redistribution et SLA réaliste |

### 25.2 Corrections nécessaires avant publication

- remplacer « données de 54 pays en temps réel » par une couverture détaillée par statut ;
- remplacer « mise à jour quotidienne des données » par « surveillance régulière et mises à jour selon les sources » ;
- ne pas annoncer 99,9 %, 99,99 % ou on-premise avant capacité opérationnelle démontrée ;
- ne pas employer « certification accréditée » sans organisme partenaire et convention signée ;
- ne pas vendre une API illimitée ;
- ne pas redistribuer une donnée achetée sans licence explicite ;
- harmoniser les quotas entre Business et les offres API autonomes ;
- séparer rapport automatisé et rapport vérifié par l'expert ;
- **ne pas commercialiser l'onglet « Opportunités (Premium) » comme payant tant que `reports.py` n'impose pas de vérification de tier (voir 4.5 et Lot 8).**

### 25.3 Monétisation prioritaire

La meilleure source de revenu initiale n'est pas l'API de masse. Elle est constituée par :

1. rapports expert à la demande ;
2. analyses de sourcing ;
3. abonnements Pro ;
4. veille tarifaire et statistique ;
5. contrats institutionnels pilotes ;
6. API après sécurisation des licences et de la qualité.

---

## 26. Extension de la feuille de route

### Lot 10 — Entrepôt statistique et providers

**Objectif :** rendre le module statistique indépendant de tout fournisseur unique.

**Critères mesurables :**

- quatre parcours opérationnels : produit, pays, bilatéral et comparatif ;
- 100 % des séries avec source, période et version ;
- zéro appel fournisseur direct depuis le frontend ;
- deux providers fonctionnels ;
- temps de réponse p95 inférieur à deux secondes depuis le cache ;
- réconciliation des révisions SH documentée.

### Lot 11 — Production et logistique

**Objectif :** enrichir cinq produits alimentaires pilotes.

**Critères mesurables :**

- production, commerce et logistique reliés pour cinq produits ;
- trois origines comparables par produit lorsque disponibles ;
- saisonnalité et ports documentés ;
- chaque estimation qualifiée ;
- dix cas métier validés.

### Lot 12 — Pilote commercial

**Objectif :** tester la disposition à payer avant l'achat de données coûteuses.

**Critères mesurables :**

- 20 utilisateurs pilotes ;
- 10 professionnels interrogés ;
- cinq abonnements ou rapports payants ;
- revenu mensuel récurrent cible de 300 $ ;
- coût technique mensuel inférieur à 150 $ hors acquisition exceptionnelle de données ;
- aucune promesse commerciale non soutenue par une capacité mesurée.

---

## Annexe A — Preuves de vérification terrain (13 juillet 2026)

Vérification effectuée par lecture directe du code source du dépôt `aouggad-web/afcfta-final-002`, branche `claude/audit-improve-markdown-cxm215`.

| # | Constat de la v1 | Verdict | Preuve |
|---|---|---|---|
| 1 | `engine/calculation.py` = noyau déterministe | Partiellement vrai | Module propre, mais code mort : seul importeur = son propre test `engine/tests/test_calculation_dza.py` |
| 2 | Adaptateur ConformePro = `PARTIAL/B` | Vrai | `engine/adapters/dza_conformepro_adapter.py:14-17,114-116` |
| 3 | 7 routes de calcul concurrentes | Vrai, avec correction de chemin | `/api/calculate/detailed` (pas `/tariffs/calculate/detailed`) ; collision de préfixe `regional_calculator.py` / `enhanced_calculator.py` non signalée en v1 |
| 4 | `CalculatorTab.jsx` appelle plusieurs circuits | Vrai | ≥ 5 endpoints distincts avec repli en cascade |
| 5 | Pas de `/api/v2/calculations` | Vrai, avec précision | L'espace `/api/v2` existe déjà (`backend/api/v2/endpoints.py`), seule la route `/calculations` manque |
| 6 | Cas de référence DZA `0101211100` | Vrai | `engine/tests/test_calculation_dza.py:119-150`, assertions exactes |
| 7 | `pipeline_report.json` 762 213 / 46 pays | Vrai, exact | `engine/output/pipeline_report.json` |
| 8 | `DATA_STATUS.json` 279 002 / 40 pays, DZA 17 115 | Vrai, exact | Fichier dupliqué dans `engine/output/` et `frontend/public/data/` |
| 9 | `DZA_summary.json` 16 569 | Vrai, exact | Incohérent avec le 17 115 ci-dessus (écart non expliqué) |
| 10 | Contradiction VERIFIED/A vs PARTIAL/B | Confirmé | Citation exacte du code, voir #2 |
| 11 | Gabarit HS6 partagé inter-pays | Confirmé quantitativement | Bande 16 567-16 575 sur échantillon de 8+ pays de tailles économiques très différentes |
| 12 | Pas de manifeste ACTIVE/DRAFT/RETIRED | Vrai | `backend/tariff_crawl/manifest.py` classe des sources, pas des versions de dataset |
| 13 | `OpportunityReportTab.jsx` interface active | Vrai, chemin corrigé | `frontend/src/components/reports/OpportunityReportTab.jsx`, pas sous `opportunities/` |
| 14 | Poids de score 25/25/20/20/10 | Vrai, exact | `backend/services/report_engine.py`, `DEFAULT_WEIGHTS` |
| 15 | Renormalisation sur composantes manquantes | Vrai | `_end_to_end_score`, division par `weight_used` |
| 16 | Ancien module opportunités orphelin | Vrai | 10 fichiers sous `frontend/src/components/opportunities/`, aucun import externe |
| 17 | Coût rendu = FOB + fret seulement | Vrai | `_landed_cost()`, `report_engine.py` |
| 18 | `weight_coverage` = recommandation | **Faux — déjà implémenté** | Champ retourné par `report_engine.py` et déjà affiché dans `OpportunityReportTab.jsx` |
| 19 | Hachage SHA-256, tiers, quotas IA | Vrai | `backend/auth.py` |
| 20 | `PUBLIC_DATA_ACCESS` peut ouvrir l'accès public | Vrai, et c'est la valeur **par défaut** | `backend/auth.py`, `os.getenv("PUBLIC_DATA_ACCESS", "true")` |
| 21 | Premium non protégé par entitlement strict | Vrai | `reports.py` utilise la dépendance d'auth générique, aucune vérification de tier |
| 22 | Rate limiting par clé et IP non démontré partout | Vrai, précisé | Middleware global existe (`rate_limiter.py`, clé `IP:route`), mais aucune limite par clé API |
| 23 | Isolation Mongo/Redis, backend read-only | Vrai | `docker-compose.yml`, `Dockerfile` |
| 24 | `test_report_engine.py` > 80 contrôles | Vrai, précisé | 81 fonctions de test, 268 assertions |
| 25 | Tests dépendant d'un serveur déjà lancé | Vrai, mécanisme précisé | 16 fichiers, `conftest.py` les *skip* silencieusement si le serveur est injoignable |
| 26 | Pas de CI de certification unique | Vrai, et **aggravé** | CI existante avec tests backend en `continue-on-error: true` (non bloquant) ; 10 des 12 étapes cibles totalement absentes |

---
