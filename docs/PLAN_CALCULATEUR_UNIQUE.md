# Plan — un seul calculateur, alimenté par le crawl, arithmétique minimale

**Objet :** en finir avec le module calculateur. Une chaîne unique, alimentée par
les fichiers produits par le crawler, une arithmétique réduite au strict
nécessaire, et des montants qui incluent **tous** les droits et taxes perçus par
la douane à l'importation.

**Ce document remplace** `docs/PLAN_CORRECTION_CALCULATEUR_2026-09.md`, dont les
phases 1 à 4 conservaient la structure à corriger au lieu de la supprimer. La
phase 0 de ce plan (harnais différentiel, corpus figé, note d'indisponibilité)
est acquise et reste utilisée ici comme instrument de mesure.

**Mesures de ce document :** relevés le 15 septembre 2026 sur
`main@2f8e74b`, par lecture directe des fichiers du dépôt.

---

## 1. Ce qui est mesuré aujourd'hui

### 1.1 La surface du module

| Élément | Lignes |
|---|---:|
| `services/authentic_tariff_service.py` | 2 447 |
| `routes/calculator.py` (chemin POST concurrent) | 1 138 |
| `routes/authentic_tariffs.py` | 765 |
| `services/enhanced_calculator_service.py` + `_v2` + `_v3` | 1 379 |
| `services/postgres_tariff_service.py` | 520 |
| `services/regulatory_fee_service.py` | 552 |
| `routes/tariffs_calculation.py` | 406 |
| `services/tax_computation.py` | 389 |
| `services/official_preferential_rates.py` | 412 |
| `services/tariff_doctrine.py` | 339 |
| `services/export_tariff_service.py` | 259 |
| `services/national_legal_calculation_service.py` + Kenya | 212 |
| `services/tariff_provider_service.py` | 159 |
| `routes/enhanced_calculator.py` | 145 |
| `components/calculator/CalculatorTab.jsx` | 2 016 |
| **Total** | **11 191** |

Trois moteurs de cascade coexistent (`compute_tax_cascade`,
`compute_dual_breakdown`, la cascade inline du POST), quatre générations de
« calculateur enrichi », et **deux jeux de données parallèles** :
`backend/data/ISO_tariffs.json` (40 fichiers, dérivés ETL) et
`backend/data/crawled/ISO_tariffs.json` (53 fichiers, produits du crawler).

Résultat mesuré au 13 septembre (`docs/MESURE_REFERENCE_CALCULATEUR_2026-09-13.md`) :
**318 divergences sur 320 positions** entre les deux chemins servis par
l'interface. Deux positions concordent.

### 1.2 Ce que le crawl contient réellement

53 pays, **342 176 positions**, 590 Mo. Relevé du 15 septembre :

| Famille de schéma | Pays | Forme des taxes |
|---|---:|---|
| `positions[]` + `taxes{}` + `taxes_detail[]` | 19 | UEMOA/CEMAC, base explicite |
| `sub_positions[]` + `taxes{}` | 17 | dict code → taux |
| `positions[]` + `taxes_detail[]` | 8 | EAC + Ghana, base explicite |
| `positions[]` + `taxes[]` | 6 | SACU + Nigeria, liste de colonnes |
| forme propre non lue aujourd'hui | 3 | TUN (`taxes_import[]`), DJI et ERI (vides) |

**Cinq schémas, pas cinquante-trois.** C'est le fait central du plan : la
diversité apparente des sources se réduit à cinq formes, réductibles en une
seule passe.

Deux constats de même portée :

1. **L'assiette est déjà dans la donnée pour 26 pays.** Les fichiers UEMOA,
   CEMAC, EAC et Ghana portent un champ `base` dont le vocabulaire complet
   tient en neuf expressions : `CIF`, `CIF + DD`, `CIF + DD + RS + PCS`,
   `CIF + DD + TCI`, `CIF+Duty`, `CIF+Duty+Fees`, `CIF+Duty+Levies`,
   `CIF (plafond 15 000 XAF)`, `variable`. La Tunisie porte la sienne sous
   `assiette` (`VALEUR DOUANE`, `VAL.DOU(D)+R(DT)`, `SOMME D.T`, `QCS`).
   Aujourd'hui ce champ est ignoré : `COUNTRY_TAX_PROFILES` (37 pays, codée à
   la main) le remplace, et `ASSIETTE_TVA_ETABLIE` (10 pays) corrige ensuite
   la table codée. Deux couches de correction sur une donnée qui était juste.

2. **Le crawl porte déjà les colonnes préférentielles.** Les cinq pays SACU
   exposent une colonne `AfCFTA` par position, à côté de `GENERAL`, `SADC`,
   `EU_UK`, `EFTA`, `MERCOSUR`. L'Éthiopie expose `D2R`, qui est la colonne
   **COMESA** et non ZLECAf. Ces colonnes sont aujourd'hui **écartées** par
   `_PREFERENTIAL_RATE_CODES` au lieu d'être servies chacune sous son propre
   régime — la colonne `AfCFTA` pour la ZLECAf, les autres pour leurs accords
   respectifs, jamais l'une pour l'autre (§3).

### 1.3 Les taxes présentes, par famille

Relevé sur les 1 500 premières positions de chaque pays. Les codes distincts se
rangent en **sept** familles, et aucune autre :

| Famille | Codes rencontrés |
|---|---|
| Droit de douane | `DD`, `ID`, `DI`, `GENERAL`, `CET Import Duty`, `Droit d'Importation` |
| Prélèvements communautaires | `RS`, `PCS`, `PCC`, `PC-AES`, `PUA`, `TCI`, `CIA`, `RI`, `OHADA`, `TS`, `CEDEAO` |
| Redevances et services | `RPD/IMPOR`, `IDF`, `RDL`, `Infrastructure Levy`, `CISS`, `PSV`, `DSV`, `TCL` |
| Accises et taxes spéciales | `EXC`, `Excise Duty`, `DA`, `TIC`, `IAT`, `TSP`, `TP`, `DUS`, `TUB`, `TUF`, `SPEC` |
| TVA et équivalents | `TVA`, `TVA/AP`, `VAT`, `IVA` |
| Prélèvements post-TVA | `PRCT` (précompte DZ 2 %), `WHR` (withholding ET) |
| Fonds affectés | `NHIL`, `GETFL/GETFUND` |

Le calculateur actuel en sert une partie ; le plan les sert toutes, parce que
c'est ce que la douane liquide.

### 1.4 Les trous, nommés

| Trou | Portée | Traitement retenu |
|---|---|---|
| DJI, ERI : fichiers vides | 2 pays | `INDISPONIBLE` déclaré, jamais estimé |
| TUN : schéma `taxes_import[]` non lu | 17 542 positions | adaptateur au chantier L1 |
| SACU (ZAF, NAM, BWA, LSO, SWZ) : le crawl SARS ne porte **aucune TVA** | 5 pays | collecte des cinq TVA nationales — chantier C1 (§6.1). Total `PARTIEL` marqué en attendant, jamais un taux fabriqué |
| GHA : `taxes_detail[].tax` sans clé `code` | 5 387 lignes | adaptateur au chantier L1 |
| SOM : pas de crawl, seulement le fichier ETL | 1 pays | entré dans le socle comme 54ᵉ source — son fichier a le schéma `tariff_lines[]` du Ghana, donc aucun adaptateur supplémentaire ; l'origine ETL est étiquetée sur chaque position, mais le chemin d'exécution reste unique |
| 339 fichiers `*_progress_*.json` (~3,8 Go) | dépôt | supprimés, ce sont des reliquats de crawl |

---

## 2. La cible

Quatre objets, et rien d'autre entre la donnée du crawler et le montant affiché.

```
crawl/ISO_tariffs.json  ──(1) socle : une passe, hors ligne ──►  socle/ISO.json
                                                                      │
                                              (2) moteur : lookup + cascade
                                                                      │
                                              (3) une route : POST /api/calculate
                                                                      │
                                              (4) un appel dans l'interface
```

### 2.1 Le socle (construit hors ligne, versionné par empreinte)

Une passe unique lit les cinq schémas du crawl et écrit, par pays, un fichier
plat au **schéma unique** :

```json
{
  "iso3": "CIV",
  "source": { "nom": "douanes.ci", "url": "...", "collecte": "2026-08-30",
              "sha256": "...", "nomenclature": "SH2022" },
  "positions": {
    "7612900000": {
      "designation": "Réservoirs, fûts, bidons en aluminium",
      "unite": "QA",
      "droits": [
        { "code": "DD",  "libelle": "Droit de douane", "famille": "droit",
          "taux": 20.0, "assiette": "CIF" },
        { "code": "TVA", "libelle": "Taxe sur la valeur ajoutée", "famille": "tva",
          "taux": 18.0, "assiette": "CIF+DD+RS+PCS" }
      ],
      "preferentiels": { "AFCFTA": null, "SADC": null }
    }
  }
}
```

Règles de la passe, sans exception :
- **aucune valeur inventée** : un champ absent de la source est absent du socle ;
- **aucun taux recalculé** : la passe recopie, elle ne dérive pas ;
- l'assiette vient de la source quand la source la porte, sinon d'une table de
  27 lignes (`socle/assiettes_pays.json`, une ligne par pays, avec sa référence
  légale) — jamais du code ;
- chaque position porte l'empreinte du fichier source dont elle vient.

Le socle est un artefact de construction : régénéré par `make socle`, vérifié
par empreinte au démarrage, et refusé s'il ne correspond pas au crawl présent.

### 2.2 Le moteur (cible : 200 lignes)

Une fonction, cinq primitives d'assiette et un modificateur, aucune
connaissance par pays :

| Primitive | Sens | Exemple |
|---|---|---|
| `CIF` | valeur en douane | `DD`, `RS`, `IDF` |
| `CIF+<codes>` | CIF augmenté du montant des droits nommés | `TVA` sur `CIF+DD+TCI` |
| `SOMME(<codes>)` | somme de montants de droits, **sans** le CIF | `RPD/IMPOR` TUN, assiette `SOMME D.T` |
| `%<CODE>` | pourcentage du **montant** d'un autre droit, que l'assiette nomme | `CAC` CEMAC, centimes additionnels sur le droit |
| `×QTE` | droit spécifique : montant unitaire × quantité | `DSV` TUN, `0,1 dinar`/QCS |

Et un **modificateur**, applicable à n'importe laquelle : `plafond(montant,
devise)` — le cas `CIF (plafond 15 000 XAF)` relevé sur 3 000 positions
CEMAC. Un plafond exprimé dans une devise autre que celle de la valeur déclarée
exige une conversion : tant que le taux de change du jour de liquidation n'est
pas fourni, le droit plafonné est rendu `PARTIEL` avec le paramètre manquant
nommé, jamais approché.

Cinq primitives et un modificateur : c'est le compte exact des formes relevées
dans les sources (neuf expressions `base` + quatre `assiette` tunisiennes). Une
assiette qui n'entrerait dans aucune est un `INDISPONIBLE` motivé, pas une
sixième primitive ajoutée à la hâte.

**Aucune méthode nationale n'est figée dans le moteur.** Les codes de
prélèvements sont portés par les assiettes, jamais écrits dans le code : `%DD`
n'est qu'un cas de `%<CODE>`. Le seul terme que le moteur connaisse est la TVA,
et parce que la grammaire le lui impose — « CIF + tous les droits sauf la TVA »
doit savoir laquelle exclure. Quels prélèvements existent, dans quel ordre ils
se liquident, sur quelle assiette, et lesquels une préférence remise : tout
cela vient du socle ou de l'appelant.

Corollaire, qui vaut règle : **un composant d'assiette qui manque n'est jamais
compté pour zéro.** Si la TVA s'assied sur `CIF+DD+TCI` et que le TCI n'a pas
pu être liquidé, l'assiette est amputée : le moteur le dit et rend la ligne
indisponible, au lieu d'un montant plus faible et crédible. Un code que la
position ne porte pas, en revanche, est simplement sans objet — signalé, et le
calcul se poursuit.

Deux règles générales, qui remplacent trente-sept profils :
- `CIF+TOUS_SAUF_TVA` est une **formule**, pas une énumération : la TVA
  s'assied sur la valeur en douane augmentée de tous les prélèvements d'entrée,
  elle seule exclue. C'est la règle de la directive UEMOA 02/98 art. 27 a), du
  CGI marocain art. 96, du VAT Act ghanéen 870 et du code tunisien. Là où le
  socle porte une assiette explicite, elle prime.
- un droit spécifique sans quantité fournie ne produit **pas** de montant : il
  produit un `PARAMETRE_REQUIS` nommé, et le total est marqué partiel.

Ordre de liquidation : droits → prélèvements → redevances → accises → TVA →
prélèvements post-TVA. Un cycle dans les assiettes est refusé au chargement du
socle, pas au calcul.

Sortie : une ligne par droit (`code`, `libellé`, `assiette`, `montant`,
`source`), un total, un taux effectif, et un état par position —
`COMPLET`, `PARTIEL`, `INDISPONIBLE`.

### 2.3 Une route

`POST /api/calculate` : `{origine, destination, code_sh, valeur_cif, quantité?,
devise?}` → le résultat ci-dessus, pour les deux régimes (NPF et ZLECAf) dans
la même réponse. Toutes les autres routes de calcul sont supprimées ou
délèguent à celle-ci.

### 2.4 Un appel dans l'interface

Un `fetch`, pas de `try/catch` silencieux vers un second chemin. Une erreur du
serveur s'affiche.

---

## 3. Le régime ZLECAf

**Le verrou juridique existant est conservé intégralement.** Aucun taux
préférentiel n'est liquidé sans que `zlecaf_implementation_registry` autorise
le couloir : un instrument d'application en vigueur, un ensemble de pays
d'origine acceptés de façon réciproque, et un barème au niveau de la ligne. Ce
registre est *fail-closed* par construction ; `OFFER_ONLY` et
`PARTNER_NOTICE_REQUIRED` ne valent pas autorisation. Le plan ne touche pas à
cette porte — il ne change que ce qui la franchit.

Une fois le couloir autorisé, le taux vient de **deux** sources, dans cet
ordre :

1. la **colonne AfCFTA de la position** quand le crawl la porte — aujourd'hui
   les cinq pays SACU. La colonne doit nommer la ZLECAf ; une colonne d'un
   autre régime n'est jamais lue comme préférence ZLECAf ;
2. l'**offre nationale publiée** (`etl/afcfta_national_offers.py`), et
   seulement quand le registre a autorisé le couloir.

Sinon : `PREFERENCE_NON_TRACEE`. Pas de coefficient de démantèlement générique
appliqué au NPF.

Deux précisions qui évitent une régression :

- **`D2R` n'est pas une colonne ZLECAf.** C'est la colonne préférentielle
  COMESA de la source éthiopienne (`authentic_tariff_service.py:558`). Elle
  reste servie comme donnée, sous un régime COMESA distinct et validé à part.
  L'utiliser comme taux ZLECAf ferait payer un taux COMESA à une origine qui
  n'y a pas droit. Il en va de même de `SADC`, `EU_UK`, `EFTA` et `MERCOSUR`.
- **Une offre publiée seule ne fait pas un droit dû.**
  `resolve_published_offer_rate` est explicitement *informational* : elle
  répond « ce que le livre tarifaire publie », pas « ce qui est légalement
  exigible ». Hors couloir autorisé, elle reste un affichage « à vérifier
  auprès des douanes locales », jamais un montant.

Deux règles de fond :

- **la préférence ne réduit que les prélèvements qu'un texte lui désigne — et
  ce périmètre est national, jamais déduit.** « Seul le droit de douane est
  démantelé » est la figure la plus courante, pas une règle générale : l'Algérie
  exonère aussi le **DAPS** pour les produits des listes (A) et (B) admis sous
  ZLECAf (circulaire 482/2024, partie II-2, citant l'art. 2 de la loi de
  finances complémentaire 2018 ; déjà encodé dans
  `services/zlecaf_schedule_dza.py`). L'oublier n'est pas une approximation :
  sur la position `2201101100`, à 100 000 DA de valeur, le total liquidé passe
  de 108 006 DA — DD seul remis — à 24 440 DA, soit un écart de 83 566 DA.
  Le moteur reçoit donc une table `{code: taux}` établie en amont ; il ne
  décide ni du droit à la préférence, ni de son périmètre.
- **tout prélèvement absent de cette table reste dû à son taux NPF.** TVA,
  accises et redevances ne sont pas « remisées » ; elles suivent mécaniquement
  l'assiette réduite quand elle les concerne. C'est ce qui rend le montant
  ZLECAf réaliste au lieu d'optimiste.
- origine hors ZLECAf → régime NPF, même décision sur toute la chaîne.

---

## 4. Ce qui est supprimé

| Supprimé | Lignes | Remplacé par |
|---|---:|---|
| `routes/calculator.py` (POST concurrent) | 1 138 | la route unique |
| `enhanced_calculator_service` + `_v2` + `_v3` | 1 379 | le moteur |
| `services/tax_computation.py` | 389 | le moteur |
| `postgres_tariff_service` dans le chemin de calcul | 520 | le socle |
| `COUNTRY_TAX_PROFILES` (37 profils) + `ASSIETTE_TVA_ETABLIE` | ~420 | `assiettes_pays.json`, 27 lignes |
| `national_legal_calculation_service` + Kenya | 212 | le moteur |
| `tariff_provider_service` | 159 | le socle |
| fichiers `backend/data/*_tariffs.json` dans le calcul | 40 fichiers | socle — SOM compris, entré comme 54ᵉ source et étiqueté `etl` |
| `backend/data/tariffs/` — copie à l'octet près du précédent | 40 fichiers, 336 Mo | supprimée : deux chemins vers la même donnée |
| `backend/data/crawled/*_progress_*.json` | 339 fichiers, ~3,8 Go | — |

Cible : **11 191 → environ 1 500 lignes** sur la chaîne de calcul, interface
comprise. Le chiffre est un critère d'acceptation, pas une estimation : un
chantier qui ne réduit pas est un chantier qui a échoué.

Ce qui **n'est pas** supprimé : les colonnes affichées, les formalités
administratives, les avantages fiscaux, le journal de calcul, le comparatif
multi-pays. Ils consomment la nouvelle sortie.

---

## 5. Les chantiers, dans l'ordre

Chacun est livrable seul, mesuré par le harnais de la phase 0.

### L1 — Le socle (le seul chantier de données)

| | |
|---|---|
| **Livrable** | `scripts/build_socle.py` + `backend/socle/ISO.json` (**54 pays** : 53 du crawl + SOM) + `socle/assiettes_pays.json` |
| **Contenu** | les cinq adaptateurs de schéma, dont TUN `taxes_import[]` et GHA `taxes_detail[].tax` — le même adaptateur `tariff_lines[]` couvre SOM |
| **Acceptation** | **347 778 positions** lues (342 176 du crawl + 5 602 SOM), 0 perdue ; chaque position porte source, date, empreinte, et son origine (`crawl` ou `etl`) ; DJI/ERI déclarés vides ; aucun taux absent converti en 0 ; **aucun chargeur d'exécution ne lit plus `backend/data/*_tariffs.json`** ; le socle se régénère en moins de 5 minutes |

### L1b — PostgreSQL régénéré depuis le socle

Le sens du flux s'inverse : la base cesse d'être une source et devient une
**projection** du socle. Elle n'a alors plus rien à dire que le fichier ne dise
déjà.

| | |
|---|---|
| **Livrable** | `scripts/load_socle_to_postgres.py` — vidage et rechargement intégral depuis le socle, en une transaction, plus une table `socle_manifest` portant la version du socle et son SHA-256 |
| **Schéma** | aligné sur le socle : un pays, une position, et **une ligne par droit** (code, libellé, famille, taux, assiette, source). Fin de `total_npf_pct` servi comme `dd_rate` (`postgres_tariff_service.py:111`) : un total n'est pas un droit de douane |
| **Acceptation** | rejouer le chargement sur le même socle redonne la base à l'identique ; le service **refuse de servir** si l'empreinte de `socle_manifest` ne correspond pas au socle présent sur disque — une base périmée devient inerte au lieu de contredire silencieusement les fichiers ; les trois scripts de migration (`migrate_all.py`, `fast_migration.py`, `run_migration.py`), `engine/pipeline.py` et `backend/data/tariffs/` sont supprimés |

Une fois L1b livré, la préséance n'est plus un arbitrage : base et fichiers
disent la même chose par construction, et le seul cas où ils divergent est un
socle non rechargé — que l'empreinte détecte.

### L2 — Le moteur

| | |
|---|---|
| **Livrable** | `backend/services/calcul.py`, 200 lignes, sans import de service |
| **Acceptation** | les cinq primitives et le modificateur `plafond` couvrent les neuf expressions d'assiette relevées + les quatre tunisiennes ; les **sept** familles de taxes sont liquidées, `NHIL`/`GETFUND` compris ; un test par primitive et un test de plafond ; aucune table par pays dans le code |

### L3 — La route unique

| | |
|---|---|
| **Livrable** | `POST /api/calculate` ; les routes existantes délèguent ou disparaissent |
| **Acceptation** | `scripts/diff_engines.py` ne trouve plus de second chemin à comparer ; les 320 positions de la mesure de référence donnent un résultat unique ; les 23 cas du corpus figé passent, les 6 `xfail` sont levés ou motivés |

### L4 — L'interface

| | |
|---|---|
| **Livrable** | `CalculatorTab.jsx` ramené à un appel ; `calculatorFallback.js` supprimé |
| **Acceptation** | plus aucun `catch` silencieux ; la réponse affiche la source, le fichier et la date de collecte réellement utilisés ; un `INDISPONIBLE` s'affiche comme tel et non comme 0 |

### L5 — La preuve de réalisme

| | |
|---|---|
| **Livrable** | `backend/tests/fixtures/liquidations_reelles.json` : au moins **5 liquidations douanières réelles par pays servi**, avec la quittance ou la simulation officielle en pièce jointe |
| **Acceptation** | écart ≤ 1 % sur le total liquidé, ou un écart expliqué ligne à ligne. **C'est le seul critère qui prouve « des montants proches de la réalité » ; sans lui, le reste n'est qu'une cohérence interne.** |

### L6 — Le verrou

| | |
|---|---|
| **Livrable** | intégration continue : corpus figé + liquidations réelles + vérification d'empreinte du socle |
| **Acceptation** | un écart nouveau fait échouer la construction ; un socle périmé refuse de servir |

**Dépendances :** L1 → L1b → L2 → L3 → L4. L5 démarre dès L2 (elle mesure le moteur,
pas l'interface). L6 clôt. Les chantiers de collecte C1 et C2 (§6) sont
parallèles : ils n'en bloquent aucun.

---

## 6. Décisions arbitrées et chantiers de collecte

Les deux premières décisions sont tranchées : **on collecte**. Elles cessent
d'être des arbitrages et deviennent des chantiers, avec leurs sources nommées
et leur critère d'acceptation. La troisième reste ouverte.

### 6.1 SACU — ce que la douane liquide réellement

La SACU n'est pas cinq régimes juxtaposés, c'est **une union douanière à
territoire douanier unique**, et cela change la lecture des fichiers :

- **le droit de douane est commun.** Le tarif extérieur commun est celui de
  l'annexe 1 du SARS Schedule 1. Si les cinq fichiers crawlés portent des
  colonnes de droits identiques, ce n'est pas un défaut de collecte : c'est le
  droit applicable. Le socle peut donc légitimement servir la même colonne aux
  cinq, à condition de le **dire** dans la provenance de la position ;
- **les droits sont perçus une fois, à la première entrée** dans le territoire
  douanier commun — un conteneur dédouané à Durban pour un importateur du
  Lesotho acquitte le droit à Durban, puis circule sans nouveau droit à
  l'intérieur de l'union ;
- **les recettes sont mises en commun.** Droits de douane, accises et droits
  additionnels perçus dans la zone alimentent le *Common Revenue Pool*, tenu
  et administré par l'Afrique du Sud, puis redistribué aux membres selon la
  formule de partage (composantes douanière, accises, développement). C'est
  exactement le mécanisme que vous signalez ;
- **la TVA à l'importation, elle, n'entre pas dans le pool.** C'est un impôt
  intérieur, dû à l'importation dans chaque État membre, qu'elle vienne d'un
  autre membre ou du reste du monde.

**Conséquence pour le calculateur, et elle est nette :** la mise en commun est
un transfert budgétaire *entre États*. Elle ne change rien à ce que
l'importateur acquitte. Le calculateur répond « combien dois-je payer », pas
« à qui l'argent revient in fine » — le pool ne doit donc **jamais** entrer
dans le montant liquidé. Il a sa place dans la note de provenance, pas dans
l'arithmétique.

Et surtout : puisque la TVA est hors pool et reste nationale, **la collecte des
cinq TVA reste indispensable**. C'est ce qui manque aujourd'hui, et le pool ne
le remplace pas.

#### Chantier C1 — collecte des TVA à l'importation SACU

Le dispositif existe déjà et il est strict : `NationalTaxScraper`
(`backend/crawlers/countries/national_tax_scraper.py`) archive le document
officiel avec son SHA-256 et interdit toute extraction de taux sans adaptateur
dédié (`rate_extraction: FORBIDDEN_WITHOUT_DEDICATED_ADAPTER`). Deux pays
seulement sont passés par lui à ce jour (UGA, GHA). Les cinq sources SACU sont
**déjà enregistrées** dans `all_countries_registry.py`, toutes en
`PENDING_OFFICIAL_COLLECTION` :

| Pays | Administration | État de l'URL au 15/09/2026 |
|---|---|---|
| ZAF | South African Revenue Service (SARS) | joignable (200) |
| BWA | Botswana Unified Revenue Service (BURS) | joignable (200) |
| NAM | Namibia Revenue Agency (NamRA) | enregistrée, non vérifiée — injoignable depuis l'environnement de collecte |
| LSO | Lesotho Revenue Authority (LRA) | enregistrée, non vérifiée — injoignable depuis l'environnement de collecte |
| SWZ | Eswatini Revenue Service | **aucune URL identifiée** — à trouver avant toute collecte |

Instrument visé par pays : la loi TVA en vigueur (pour l'Afrique du Sud, le
*VAT Act* 89/1991 et sa liste de produits détaxés), plus les avis de taux en
vigueur.

| | |
|---|---|
| **Livrable** | cinq documents archivés avec SHA-256 sous `backend/data/national_taxes/raw/<ISO>/`, un adaptateur d'extraction par instrument, et le taux versé au socle |
| **Acceptation** | chaque TVA servie porte sa référence légale, sa date d'entrée en vigueur et l'empreinte du document ; **aucun taux saisi à la main, aucun taux repris d'un pays voisin** ; les positions détaxées ou exonérées sont traitées comme telles et non au taux plein |
| **Tant que ce n'est pas fait** | le total SACU reste `PARTIEL`, hors TVA, explicitement marqué. Un montant incomplet et signalé vaut mieux qu'un montant complet et inventé |

#### Chantier C2 — dépasser WITS sur les treize pays sans nomenclature nationale

Treize pays sont aujourd'hui servis en moyenne NPF SH6 issue de WITS/TRAINS
(`crawled_data_service.py:305`) : **AGO, COM, LBY, MDG, MOZ, MRT, MUS, MWI,
SDN, STP, SYC, ZMB, ZWE**. Une moyenne SH6 n'est pas un tarif : elle ne
distingue pas les sous-positions nationales et elle vieillit sans le dire.

Les treize ont, eux aussi, une source fiscale nationale déjà enregistrée au
registre. La recherche porte donc sur le tarif lui-même : portail douanier
national, tarif intégré publié, loi de finances annuelle, ou tarif du bloc
régional quand il est effectivement transposé.

| | |
|---|---|
| **Livrable** | par pays : une énumération nationale datée, ou le constat argumenté qu'aucune source publique n'existe |
| **Acceptation** | un pays quitte l'état « moyenne WITS » **uniquement** contre une nomenclature nationale sourcée ; le déficit de couverture est chiffré pays par pays, plus jamais indéterminé |
| **Tant que ce n'est pas fait** | servis, mais étiquetés `moyenne NPF SH6` dans la réponse **et** dans l'interface, jamais présentés comme tarif national |

C1 et C2 sont des chantiers de **données**, parallèles à L1-L6 : ils ne
bloquent aucune livraison logicielle, et le socle les absorbe sans changer de
schéma dès qu'un taux sourcé arrive.

### 6.2 PostgreSQL — comment son contenu est produit, et ce qui en découle

La question n'est pas « faut-il une base », mais « d'où vient ce qu'elle
sert ». Chaîne remontée le 15 septembre 2026, pièces à l'appui.

**Ce que le code fait.** `_get_postgres_provider()` est consulté **en premier**
à quatre endroits (`authentic_tariff_service.py:903, 1007, 1138, 1295`), et
`tariff_provider_service` affiche une politique « PostgreSQL d'abord ». Si la
base répond, son taux gagne. Si elle est absente, en panne, ou simplement vide
pour cette ligne, le code retombe **silencieusement** sur les fichiers
(`_log_etl_fallback`). Même position, même valeur CIF, deux montants possibles
selon l'état d'une base que le dépôt ne contient pas.

**Comment la base est remplie.** `engine/migrate_all.py` lit des fichiers
`<ISO>_canonical.jsonl` dans `/app/engine/output/` et les insère en base. Ces
fichiers sont produits par `engine/pipeline.py`, qui lit
`/app/backend/data/tariffs/<ISO>_tariffs.json` — un **troisième** jeu de
données, par ailleurs copie à l'octet près de `backend/data/*_tariffs.json`
(336 Mo dupliqués, vérifié sur CIV, KEN, ZAF).

**Ce que le seul rapport de génération conservé établit.**
`engine/output/pipeline_report.json` :

| Fait | Valeur |
|---|---|
| Date de génération | **1ᵉʳ mars 2026**, 17:37:10 → 17:37:47 |
| Durée totale | **37 secondes** pour 46 pays |
| Enregistrements produits | **762 213** |
| Par pays | **16 567 à 16 573** — un écart de **6 enregistrements sur 46 pays** |
| Djibouti et Érythrée | **16 570 enregistrements chacun** |

**Trois conclusions, et elles sont factuelles :**

1. **Les `*_canonical.jsonl` chargés en base ne sont pas versionnés.** Le dépôt
   ne conserve que les 54 `_summary.json`. Ce qui est en production ne peut
   donc être ni reconstruit, ni audité, ni comparé depuis ce dépôt.
2. **Ils n'ont pas été produits depuis les fichiers actuels.** Ceux-ci donnent
   aujourd'hui 2 063 à 8 746 sous-positions selon le pays — des comptes variés,
   cohérents avec les nomenclatures nationales. La génération de mars en a
   produit 16 570 pour **tout le monde**. La source de mars n'existe plus.
3. **Un écart de 6 enregistrements sur 46 pays n'est pas la signature de 46
   tarifs nationaux distincts.** C'est celle d'une expansion par gabarit. Que
   Djibouti et l'Érythrée — dont le crawl est vide aujourd'hui et qui n'ont
   aucun fichier dans le jeu source actuel — pèsent exactement 16 570
   enregistrements comme les autres achève la démonstration.

**Un quatrième fait, relevé en cherchant le schéma.** Le service interroge
trois tables — `measures`, `requirements`, `fiscal_advantages` — qu'**aucun
script du dépôt ne crée** : les trois migrations présentes rangent ces données
en colonnes `JSONB` sur `commodities`. Le schéma réellement en production n'a
donc pas été créé par le code versionné. À la question « d'où viennent les
données PostgreSQL », la réponse honnête est : *ce dépôt ne permet pas de le
dire* — ni les fichiers chargés, ni le schéma qui les porte, ni le script qui
l'a créé n'y figurent.

**Décision : le flux est inversé — le socle alimente la base.** PostgreSQL
cesse d'être une source concurrente pour devenir une projection du socle,
reconstruite par `scripts/load_socle_to_postgres.py` (chantier L1b). La charge
de la preuve s'inverse du même coup : Un taux qu'aucun fichier tracé ne porte ne peut pas être servi,
quelle que soit la base qui le contient — c'est la règle 1, appliquée sans
exception. PostgreSQL garde son emploi utile — servir vite une recherche sur
347 778 positions — mais **alimenté par le socle** : il ne peut alors plus
contredire le fichier, seulement le restituer. C'est bien le dernier crawl,
donc la donnée vraie, qui devient la source de la base, et non l'inverse.

**Ce que cela coûte.** On perd la possibilité de corriger un taux en production
par une écriture en base, sans recollecte. C'est exactement ce que la règle 2
interdit par ailleurs.

**Ce qui reste à faire avant la bascule, et c'est borné :** exporter le contenu
de la base de production, le comparer au socle, et publier la liste des taux
qui n'y figurent pas. Chacun est alors soit rattaché à une source et versé au
socle, soit écarté. Aucun n'est conservé au seul motif qu'il est en base. Cet
export est à faire **avant** le premier rechargement, puisque celui-ci vide la
table : c'est la seule fenêtre où le contenu actuel est encore observable.

## 7. Les règles de ce plan

1. **Une seule source : le crawl.** Un taux servi vient d'un fichier du
   crawler, identifié par son empreinte, ou n'est pas servi.
2. **Aucune valeur fabriquée.** Ni un 0 par défaut, ni un taux de chapitre, ni
   une base légale attribuée par appartenance régionale.
3. **La donnée prime sur le code.** Une assiette présente dans la source
   l'emporte sur toute table écrite à la main.
4. **Toutes les taxes de la douane, ou un total marqué partiel.** Un total qui
   omet une accise n'est pas « prudent », il est faux.
5. **Réduire est le livrable.** Chaque chantier supprime plus de lignes qu'il
   n'en ajoute. Un correctif qui ajoute une couche est refusé.
6. **Aucune donnée tarifaire n'est modifiée pour faire passer un test.** Une
   donnée fausse se corrige par recollecte, tracée à part.

---

## 8. Hors périmètre

- La recollecte des pays vides (DJI, ERI). Les deux autres fronts de collecte
  — TVA SACU et dépassement de WITS — sont désormais dans le périmètre, comme
  chantiers C1 et C2 du §6, avec leur calendrier propre.
- La validation juridique pays par pays des 54 nomenclatures. Ce plan garantit
  que le taux **collecté** est celui qui est **servi**, liquidé sur la bonne
  assiette et identifiable jusqu'à son fichier. Il ne certifie pas
  l'exhaustivité juridique d'un pays.
- Les frais hors douane (fret, assurance, manutention portuaire, honoraires de
  transitaire). Ils relèvent du module logistique, pas du calcul des droits.
