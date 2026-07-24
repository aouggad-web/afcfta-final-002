# Traçabilité de l’index alphabétique OMD

Date de l’inspection : **24 juillet 2026**

Statut : **FOUND_IN_OTHER_BRANCH**

## Conclusion

L’index recherché a été retrouvé dans Git, sur `origin/main`, dans le commit :

```text
9fdb130ea790f15070db5f5d28e4ce34b6dcea37
2026-07-22T23:31:56+01:00
feat(hs): recherche « nom de marchandise → code SH » (index OMD) (#303)
```

Il n’est pas présent dans le HEAD local inspecté
`9afd9c5a343dc9e896cba75134d0b8bb288ae3ed`. Le HEAD local est un ancêtre de
`origin/main` (`955072453019e467577c77a01923feb2b6ba7c52`) et ne contient donc
pas encore le commit OMD. Le même commit est contenu dans :

- `origin/main` et `origin/HEAD` ;
- `origin/automated-bulk-freight` ;
- `origin/automated-data-update-145` ;
- `origin/automated-data-update-146`.

Le corpus final est `backend/data/omd_hs_index.json`. Il est construit depuis
les transcriptions Markdown `backend/data/omd_index_vol1.md` et
`backend/data/omd_index_vol2.md` par `backend/etl/omd_hs_index.py`, puis chargé
directement depuis le système de fichiers Git par
`backend/services/omd_hs_index_service.py`.

Ce corpus n’est pas la table PostgreSQL `commodities` et n’est pas l’un des
fichiers `engine/output/indexes/*`. Aucun second index n’a été créé pendant
cette inspection et aucune donnée tarifaire n’a été modifiée.

## Chemin technique complet

Chemin implémenté dans le commit OMD :

```text
frontend/src/components/statistics/StatisticsTab.jsx
  └─ frontend/src/components/common/ProductHSSearch.jsx
       └─ GET ${VITE_BACKEND_URL || ""}/api/hs-codes/product-index
            q=<texte>
            language=fr|en
            limit=25
          └─ backend/routes/hs_codes.py::search_product_index
               └─ backend/services/omd_hs_index_service.py::search
                    └─ backend/data/omd_hs_index.json
                         └─ backend/etl/omd_hs_index.py
                              ├─ backend/data/omd_index_vol1.md
                              └─ backend/data/omd_index_vol2.md
```

### Interface

Le champ est le composant réutilisable `ProductHSSearch`. Il est inséré dans
`StatisticsTab` sous le titre « Trouver un code SH à partir d’un nom de
produit ». La recherche :

- démarre à deux caractères ;
- applique une temporisation de 280 ms ;
- transmet `q`, la langue d’interface et une limite de 25 ;
- ignore les réponses devenues obsolètes après une frappe plus récente.

### API et format de réponse

La route FastAPI est `GET /api/hs-codes/product-index`. Elle accepte :

- `q` : chaîne obligatoire, au moins deux caractères ;
- `language` : `fr` ou `en`, valeur par défaut `fr` ;
- `limit` : de 1 à 100, valeur par défaut 20.

La réponse a la forme :

```json
{
  "query": "huile de palme",
  "count": 1,
  "results": [
    {
      "label": "PALME — (HUILE DE)",
      "term": "PALME",
      "qualifier": "(HUILE DE)",
      "codes": [
        {
          "code": "1511",
          "level": "heading",
          "official_label": "",
          "chapter": "15",
          "chapter_name": "..."
        }
      ],
      "codes_display": "1511, 1516, 1520",
      "is_range": false,
      "see_also": null
    }
  ],
  "source": "OMD — Index alphabétique du Système Harmonisé (7e éd. 2022)",
  "language": "fr"
}
```

La route enrichit les codes SH6 avec les libellés de `HS6_DATABASE`. Elle ne
transforme pas une position SH2 ou SH4 de l’index en SH6 arbitraire et n’expanse
pas une plage en codes intermédiaires.

### Service de recherche

Le service :

- charge une seule fois le JSON, avec un cache en mémoire ;
- normalise casse, accents et ponctuation ;
- compare les mots sur leurs limites, et non par sous-chaîne ;
- exige que tous les mots de la requête correspondent ;
- tolère l’ordre des mots et les variantes singulier/pluriel par préfixe ;
- classe d’abord la correspondance exacte, le terme principal exact, le
  préfixe, puis les entrées codées et les libellés courts.

Il s’agit d’un service de recherche de candidats. Il ne constitue pas, à lui
seul, une décision de classement tarifaire.

## Contenu de l’index

| Élément | Résultat vérifié |
|---|---:|
| Version déclarée | 7e édition 2022, donc **HS2022** |
| Entrées | **6 344** |
| Entrées portant au moins un code/une position | **6 222** |
| Entrées avec renvoi `voir` | **134** |
| Entrées avec notes de classement structurées | **0** |
| SHA-256 du JSON du commit | `c84ea861a183b0c25a16ae343f7f4c3e04fac439822ca62930e09355175f2c87` |

Le JSON porte le libellé de source et le nombre d’entrées, mais ne possède pas
un champ séparé `hs_version`. La version est déduite sans ambiguïté du libellé
« 7e éd. 2022 » et des en-têtes des deux volumes.

L’index contient des termes et qualificatifs, ainsi que des renvois
alphabétiques. Il ne contient pas un thésaurus de synonymes indépendant. La
souplesse de recherche vient de la normalisation et du classement du service.
Il ne contient ni RGI, ni Notes de Section, ni Notes de Chapitre, ni Notes
explicatives, ni avis de classement.

Exemples vérifiés :

- `huile de palme` retourne en tête `PALME — (HUILE DE)` avec les positions
  candidates `1511`, `1516` et `1520` ;
- `or` retourne plusieurs candidats distincts et ne matche pas `coriandre` par
  simple sous-chaîne ;
- `ABRICOTS` conserve le renvoi `voir FRUITS` ;
- une plage telle qu’`ABACA 5305.21–5305.29` conserve seulement ses bornes.

## Source documentaire et réutilisation

Les deux fichiers Markdown se présentent comme :

```text
SYSTEME HARMONISE DE DESIGNATION ET DE CODIFICATION DE MARCHANDISE
SEPTIEME EDITION 2022
INDEX ALPHABETIQUE
```

Le dépôt ne conserve cependant pas, dans ce commit :

- l’URL d’acquisition des volumes ;
- les fichiers source d’origine et leurs empreintes ;
- une facture, licence, autorisation de reproduction ou preuve d’abonnement ;
- la date d’acquisition et l’identité de l’acquéreur ;
- des métadonnées reliant la transcription à un exemplaire OMD déterminé ;
- un contrôle ligne par ligne contre le document source.

L’OMD indique que l’Index alphabétique fait partie des outils disponibles dans
WCO Trade Tools et que les demandes de reproduction ou d’adaptation relèvent de
ses droits. Références officielles :

- <https://www.wcoomd.org/en/faq/harmonized_system_faq.aspx>
- <https://www.wcoomd.org/en/topics/nomenclature/resources/publications.aspx>

Conséquence :

- **techniquement**, le corpus peut servir à proposer des positions candidates
  pour les marchandises détaillées EAC/Kenya ;
- **juridiquement**, la réutilisation et la redistribution de cette
  transcription dans le SaaS restent à valider par la preuve de licence ou
  d’autorisation ;
- **douanièrement**, l’index ne suffit jamais à rendre un classement certain.
  Les libellés légaux, RGI, Notes et, si nécessaire, décisions de classement
  doivent être vérifiés.

## Distinction avec les autres recherches du HEAD local

Trois recherches déjà présentes dans le HEAD local ne sont pas cet index :

1. `ProductKeywordSearch.jsx` appelle
   `/api/authentic-tariffs/search/{country}`. La recherche passe par
   `TariffProviderService`, interroge d’abord les marchandises nationales
   PostgreSQL puis des fichiers nationaux. Elle porte sur le tarif d’un pays.
2. `SmartHSSearch.jsx` appelle `/api/hs6/smart-search`. Le moteur
   `backend/search/hs_code_search.py` charge les fichiers
   `tariff_engine/normalized/*.csv` quand ils sont disponibles.
3. `HSCodeSelector.jsx` appelle `/api/hs-codes/search`. Cette route parcourt
   `HS6_DATABASE`, base technique de libellés SH6, sans l’index alphabétique,
   ses qualificatifs ou ses renvois.

Les assertions de source OMD présentes dans plusieurs fichiers du corpus HS6
local ne remplacent pas une chaîne de provenance documentée.

## PostgreSQL

La configuration active n’expose ni `DATABASE_URL` ni `POSTGRES_URL` dans
l’environnement de cette inspection. Le `docker-compose.yml` attend une
connexion PostgreSQL externe ; il ne déclare pas de service PostgreSQL local.
Le client Docker n’est pas installé dans l’environnement inspecté. Le nombre de
lignes de la base d’exécution ne peut donc pas être vérifié sans nouvel accès.
Aucun secret ou URL complète de connexion n’a été affiché.

Le modèle statique `engine/database/models.py` définit la table
`public.commodities` avec :

- `country_iso3`, `national_code`, `hs6`, `digits` ;
- `description_fr`, `description_en`, `chapter`, `category`, `unit`,
  `sensitivity` ;
- totaux NPF/ZLECAf et métadonnées `source_file`, `last_updated`.

Les index déclarés couvrent :

- `(country_iso3, hs6)` ;
- `(country_iso3, national_code)` ;
- `(country_iso3, chapter)` ;
- un index GIN de recherche plein texte française selon la migration utilisée.

Le modèle n’a pas de colonnes dédiées à la version SH, aux synonymes, aux
renvois, aux notes de classement, à la licence ou à l’URL du document OMD.
L’implémentation du commit OMD ne consulte pas cette table.

## `engine/output/indexes`

Le répertoire existe dans le HEAD local et contient 109 fichiers suivis par
Git. Pour le Kenya :

- `KEN_index_hs6.json` contient **5 831** clés ;
- `KEN_index_national.json` contient **16 572** clés.

`engine/pipeline.py::RegulatoryPipeline._process_country` construit ces
dictionnaires à partir des lignes tarifaires nationales, puis
`_build_indexes()` écrit l’index global. `engine/api/engine_service.py` les
charge pour retrouver rapidement une ligne à partir d’un code.

Ce sont des index `code → ligne tarifaire`, non des index alphabétiques
`produit → code`. Ils ne sont pas reconstruits au démarrage normal du service :
il faut exécuter le pipeline. Le Dockerfile copie le dépôt dans l’image ; aucun
téléchargement externe ou volume Docker dédié à `engine/output/indexes` n’a été
trouvé.

## Environnements déployés

Une requête GET limitée vers `https://afcfta.trade` n’a pas pu être vérifiée
depuis l’environnement d’inspection en raison d’un échec TLS. L’ancienne URL de
prévisualisation référencée dans des tests du dépôt répond HTTP 404 sur
`/api/hs-codes/product-index`.

Ces résultats ne prouvent ni l’absence ni la présence de l’index sur
l’environnement de production actuel. Aucune base de production n’a été
téléchargée ou exportée.

## Adaptateur unique

Aucun nouvel adaptateur n’est créé dans le HEAD local pour les raisons
suivantes :

1. la source et son service sont absents du HEAD local ;
2. recopier le JSON ou les volumes depuis `origin/main` créerait précisément le
   corpus parallèle interdit ;
3. un adaptateur importé maintenant serait inopérant dans cette branche ;
4. le service existant constitue déjà l’accès unique au corpus et a été testé
   directement.

Après synchronisation contrôlée du HEAD local avec le commit OMD, l’interface
`search_wco_index(query, hs_version="HS2022", language=None, limit=20)` doit
être un adaptateur mince au-dessus de
`backend.services.omd_hs_index_service.search`. Elle doit ajouter la version
explicite et un score textuel sans recopier le corpus, puis être testée avant
toute connexion à `product_mapping`.

La synchronisation n’a pas été effectuée pendant cette mission : l’arbre local
contient déjà des modifications non liées, et une mise à jour de branche
dépasserait une inspection sans consentement explicite.

## Six mesures `END_USE_MEASURE`

Les six enregistrements existants ont été conservés sans `selected_hs6` :

| Gazette | Ligne | Description | Effet | SH6 |
|---|---:|---|---|---|
| EAC/177/2025 | 85 | inputs for smart telecommunication devices, including laptops and tablets | 2025-07-01 au 2026-06-30 | aucun |
| EAC/177/2025 | 86 | various inputs for animal feeds | 2025-07-01 au 2026-06-30 | aucun |
| EAC/177/2025 | 119 | inputs for pharmaceutical clean rooms | 2025-07-01 au 2026-06-30 | aucun |
| EAC/161/2026 | 79 | inputs for smart telecommunication devices, including laptops and tablets | 2026-07-01 au 2027-06-30 | aucun |
| EAC/161/2026 | 80 | various inputs for animal feeds | 2026-07-01 au 2027-06-30 | aucun |
| EAC/161/2026 | 110 | inputs for pharmaceutical clean rooms | 2026-07-01 au 2027-06-30 | aucun |

Les deux gazettes officielles archivées ont été parcourues intégralement. Pour
ces six lignes :

- la colonne code indique seulement `Various` ;
- les mentions donnent le pays, l’usage, le taux de remise et la période ;
- aucun renvoi vers une annexe détaillée n’est indiqué ;
- aucune liste de composants, matières premières, bénéficiaires nommés,
  quantités ou codes tarifaires détaillés n’a été retrouvée dans les gazettes
  acquises.

Les expressions « smart devices », « laptops and tablets », « animal feeds » et
« clean rooms » décrivent l’usage industriel final. Elles ne décrivent pas les
marchandises individuelles à classer. L’index OMD devra être appliqué aux
composants ou matières détaillés d’une annexe officielle, jamais à ces
catégories globales.

## Validations exécutées

### Index OMD du commit retrouvé

Les fichiers OMD du commit ont été extraits uniquement dans un répertoire
temporaire hors dépôt, puis le test direct du service a été exécuté :

```text
backend/tests/test_omd_hs_index.py
9 passed in 0.53s
```

Les tests couvrent notamment :

- un corpus non trivial ;
- l’ordre des mots pour `huile de palme` ;
- accents et casse ;
- la non-correspondance `or`/`coriandre` ;
- singulier/pluriel ;
- les requêtes à plusieurs mots ;
- les renvois ;
- la requête vide ;
- la normalisation des codes.

Le test frontend présent dans le commit vérifie le composant et le contrat API,
mais simule la réponse Axios ; il ne remplace pas le test direct du service. Il
a également été exécuté depuis l’extraction temporaire du commit :

```text
frontend/src/components/common/ProductHSSearch.test.jsx
3 passed in 4.97s
```

### Garde-fous `product_mapping`

Les tests locaux imposent déjà qu’un statut `END_USE_MEASURE`,
`CONTEXT_DEPENDENT`, `MULTIPLE_HS_CANDIDATES` ou `HUMAN_REVIEW_REQUIRED` ne
produise aucun overlay SH6 automatique. Un cas explicite « various raw
materials for animal feed » est également bloqué :

```text
engine/tests/test_product_mapping.py
12 passed in 0.42s
```

Pytest a seulement signalé qu’il ne pouvait pas écrire son cache dans
`.pytest_cache`; ce défaut de cache n’affecte pas les résultats.

## Données et accès encore manquants

Avant une connexion sûre aux mappings EAC/Kenya, il manque :

1. la synchronisation contrôlée du HEAD local avec le commit OMD ;
2. la preuve d’origine, d’acquisition et de licence des deux volumes ;
3. un champ de version SH explicite dans les métadonnées du corpus ;
4. les RGI, Notes de Section, Notes de Chapitre et sources de classement
   nécessaires à la validation d’un candidat ;
5. les annexes détaillées des six remissions `END_USE_MEASURE` ;
6. un accès configuré à PostgreSQL si le contenu de la base d’exécution doit
   être audité ;
7. un accès réseau fonctionnel à l’environnement de production actuel pour
   comparer la réponse déployée ;
8. un test d’intégration non simulé de l’adaptateur futur contre le corpus du
   même commit.

Tant que ces éléments manquent, l’index peut aider à la recherche et à la revue
humaine, mais ne doit ni créer une attribution SH6 certaine ni déclencher une
remission fondée uniquement sur un mot-clé.
