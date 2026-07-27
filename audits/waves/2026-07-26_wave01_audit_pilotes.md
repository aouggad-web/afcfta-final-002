# Vague 01 — Audit contradictoire et reproductible des 6 pays pilotes

**Branche** : `claude/official-data-wave-01` (travail exclusif sur cette branche)
**Base** : `origin/main` @ `1be67b6d`
**Ordre d'audit** : ZAF → KEN → TUN → MAR → EGY → DZA
**Date de la vague** : 2026-07-26 (révision contradictoire)
**Portée de cette révision** : audit exclusivement en lecture sur le code et
les données. Aucun fichier JSON pays, aucun calculateur, aucun moteur,
aucun test n'a été modifié — seul ce document d'audit a été créé/modifié.

---

## 0. Principe directeur du SaaS — cadrage impératif de cette révision

Le produit audité est un **outil d'information et de simulation commerciale**,
**non juridique et non opposable** à l'administration douanière. Il n'a pas
vocation à certifier juridiquement les tarifs ni à se substituer aux
autorités compétentes.

**Règle centrale** : une donnée **traçable** (origine identifiable — fichier
source, portail officiel, champ nommé, mécanisme d'extraction ou de calcul
inspectable) peut être affichée **à titre informatif**, même lorsque sa
valeur juridique ou sa date d'effet n'est pas certifiée. En revanche, toute
donnée **simulée, inventée, extrapolée, mockée, ou dont l'origine n'est pas
identifiable** est strictement interdite dans le SaaS, sous quelque forme
que ce soit — stockage, moteur de calcul, API, interface, ou fallback.

**Trois notions à ne jamais confondre** :

1. **Absence de certification juridique** : la donnée reste exploitable à
   titre informatif si son origine est identifiable — ce n'est **pas** un
   motif de blocage.
2. **Absence de traçabilité** : la donnée est **interdite** dans le SaaS —
   c'est le seul motif d'exclusion du flux actif.
3. **Absence d'un taux indispensable** : seul le **calcul concerné** devient
   indisponible (`CALCULATION_UNAVAILABLE`) — pas nécessairement toute la
   ligne tarifaire, qui peut rester affichable pour ses autres composantes.

**Statuts applicables** (vocabulaire unique à utiliser pour toute donnée) :

| Statut | Signification |
|---|---|
| `DOCUMENTED` | Source identifiable, documentation suffisante |
| `PARTIAL` | Donnée traçable, mais documentation incomplète |
| `UNVERIFIED` | Origine identifiable, mais contrôle insuffisant |
| `NOT_AVAILABLE` | Aucune donnée traçable exploitable |
| `NOT_APPLICABLE` | Élément non applicable à ce cas |

`CALCULATION_UNAVAILABLE` est réservé aux cas où un **taux indispensable au
calcul** est réellement absent. L'absence d'archive officielle, de hash
indépendant, ou de date d'effet juridiquement certifiée **ne suffit pas, à
elle seule**, à interdire un calcul informatif à partir d'une donnée par
ailleurs traçable.

**Mention obligatoire, visible sur toute simulation** :
> « Simulation informative — non opposable à l'administration douanière.
> Vérifiez les taux, conditions préférentielles et formalités auprès des
> autorités compétentes avant toute opération. »

Ce cadrage régit désormais l'interprétation de l'intégralité du présent
document. Les sections suivantes ont été revues pour appliquer cette
distinction : les données présentant un **marqueur de fabrication confirmé**
(texte générique appliqué uniformément, sans origine par ligne identifiable)
restent interdites de tout usage — c'est le cas de KEN et DZA (§4.2, §4.6).
Les données dont l'origine est identifiable mais dont seule la certification
juridique ou la portée par partenaire est incomplète (ZAF, EGY, TUN, MAR)
sont **reclassées** de « à ne pas afficher » vers « affichable à titre
informatif avec statut `PARTIAL`/`UNVERIFIED` » — voir le tableau révisé §3.

---

## 1. Résumé exécutif

Cet audit reproduit, avec commande exacte et population totale pour chaque
comptage, l'état réel des fichiers **effectivement chargés au runtime** par
le calculateur pour les 6 pays pilotes.

**Verdict global** : sur les 6 pays, **3 portent des marqueurs de
fabrication confirmés** dans les données tarifaires elles-mêmes (KEN, EGY,
DZA — préférences ZLECAf génériques ou non sourcées appliquées à des
milliers de lignes). **1 pays (MAR) a été mal diagnostiqué dans la version
précédente de ce rapport** : les codes se terminant par `00` sont une
notation ADIL native (heading sans subdivision nationale), pas un padding
fabriqué — la révision ci-dessous corrige ce faux positif. **ZAF et TUN**
n'ont aucun marqueur de fabrication détecté dans les données elles-mêmes,
mais présentent un déficit structurel : aucun champ ne rattache une ligne à
un partenaire admissible, une réciprocité ou une règle d'origine — la
distinction entre *taux disponible* et *préférence juridiquement applicable*
n'existe dans aucun des 6 fichiers.

**Fait de gouvernance majeur, vérifié dans le code** : `SUPPORTED_JURISDICTIONS`
(`backend/services/national_legal_calculation_service.py:51-53`) ne contient
**que KEN**. `NATIONAL_OFFER_REGISTRY` (`backend/etl/afcfta_national_offers.py:82-93`)
ne contient **que DZA**, avec `source_id="DZA-DGD-482-2024-PENDING"` et
`publication_url=None` — aucune URL officielle de publication n'est
enregistrée dans le dépôt ; l'accessibilité ou la publication externe de la
circulaire n'a pas été établie pendant cet audit. Aucun des 6 pays pilotes n'a donc, à ce jour, une
offre ZLECAf nationale enregistrée comme juridiquement opposable dans le
moteur ; toute préférence affichée pour ces pays passe par le canevas
générique `AFCFTA_CANVAS_HS2` ou par les champs bruts non filtrés des
fichiers `_tariffs.json` audités ci-dessous — c'est cette seconde voie qui
porte le risque documenté en §5.

---

## 2. Méthodologie

### 2.1 Fichiers réellement consommés au runtime

Le chemin de chargement effectif est `backend/services/crawled_data_service.py`.
Constat de code (lignes 9, 47, 61-83) :

```python
CRAWLED_DIR = Path(__file__).parent.parent / "data" / "crawled"
...
files = list(CRAWLED_DIR.glob("*_tariffs.json"))
...
if "sub_positions" in data and not data.get("tariff_lines"):
    positions = data.get("sub_positions", [])
elif "tariff_lines" in data:
    positions = self._convert_tariff_lines_to_positions(data, country_code)
else:
    positions = data.get(positions_key, [])   # positions_key = "positions"
```

**Conclusion vérifiée** : pour les 6 pilotes, ce sont exclusivement les
fichiers suivants qui sont chargés, avec la clé de liste indiquée :

| Pays | Fichier | Clé de liste | Schéma |
|---|---|---|---|
| ZAF | `backend/data/crawled/ZAF_tariffs.json` | `positions` | branche `else` |
| KEN | `backend/data/crawled/KEN_tariffs.json` | `positions` | branche `else` |
| TUN | `backend/data/crawled/TUN_tariffs.json` | `sub_positions` | branche `if` |
| MAR | `backend/data/crawled/MAR_tariffs.json` | `sub_positions` | branche `if` |
| EGY | `backend/data/crawled/EGY_tariffs.json` | `sub_positions` | branche `if` |
| DZA | `backend/data/crawled/DZA_tariffs.json` | `sub_positions` | branche `if` |

Les artefacts `engine/output/*_summary.json` et `frontend/public/data/DATA_STATUS.json`
**ne sont pas** dans ce chemin de chargement — ils alimentent un statut
affiché côté frontend, pas le calcul lui-même. Non audités ici (hors
périmètre de cette vague, déjà signalés dans l'audit consolidé
`audits/AUDIT_ET_PLAN_TECHNIQUE_AFCFTA_FINAL_002.md:180-199`).

### 2.2 Principe de comptage

Chaque comptage ci-dessous précise : fichier source, champ inspecté,
filtre exact, population totale (dénominateur), résultat (numérateur), et
la commande Python reproductible (exécutable telle quelle depuis la racine
du dépôt, aucune dépendance autre que la bibliothèque standard `json`/
`collections.Counter`).

### 2.3 Empreinte Git au moment de l'audit

```
$ git rev-parse HEAD
940cd33bd94bbf80d6f0d2e4b5a19e5a3388da4d
$ git branch --show-current
claude/official-data-wave-01
$ git rev-parse origin/main
1be67b6da14e0a03c731ab3d82b23b4180107bb6
```

---

## 3. Tableau de synthèse par pays

| Pays | Fichier | Source déclarée | Positions | Statut fabrication | Statut d'affichage informatif |
|---|---:|---|---:|---|---|
| ZAF | `ZAF_tariffs.json` | sars.gov.za | 8 589 | Aucun marqueur ; origine identifiable (colonne AfCFTA du barème SARS) | `PARTIAL` — affichable à titre informatif ; portée par partenaire et certification juridique non établies |
| KEN | `KEN_tariffs.json` | EAC CET 2022 (kra.go.ke) | 5 984 | **Interdit** : texte générique sans origine par ligne, 100 % des positions | `NOT_AVAILABLE` pour la composante ZLECAf uniquement — à **exclure du flux actif** ; CET/IDF/RDL/VAT restent `DOCUMENTED` |
| TUN | `TUN_tariffs.json` | douane.gov.tn/tarifweb2025 | 17 512 | Aucun marqueur ; structure hétérogène par pays/produit, origine identifiable | `PARTIAL` — affichable à titre informatif ; régime juridique (GAFTA/ZLECAf) non distingué par ligne |
| MAR | `MAR_tariffs.json` | douane.gov.ma/adil | 13 114 | **Faux positif infirmé** : les éléments techniques rendent l'hypothèse du padding artificiel peu probable ; DI/TPI/TVA d'origine identifiable | `NOT_AVAILABLE` pour ZLECAf (aucun champ n'existe dans ce fichier — rien à afficher, ce n'est pas une donnée bannie) ; DI/TPI/TVA `PARTIAL` |
| EGY | `EGY_tariffs.json` | customs.gov.eg | 8 746 | Aucune fabrication : `zlecaf_rate` est **calculé par règle** sur notes officielles réelles ; reproductibilité **démontrée empiriquement** (0 divergence/6 417) — voir §4.5 | Scindé : **6 417 lignes `PARTIAL`** (note AfCFTA confirmée, chaîne reproductible) ; **2 276 lignes `UNVERIFIED`** (copie du DD sans note, `zlecaf_source` discriminant non persisté) ; **53 lignes `NOT_AVAILABLE`** (`null`, correct) |
| DZA | `DZA_tariffs.json` | conformepro.dz (agrégateur secondaire) | 17 061 | **Interdit** : texte générique identique sans origine par ligne, 4 119 positions ; source elle-même `PARTIAL` | `NOT_AVAILABLE` pour cette composante — à **exclure du flux actif** ; reste du fichier `PARTIAL` (source secondaire). Circulaire 482/2024 : `NOT_AVAILABLE` (aucune copie exploitable collectée — voir §4.6) |

---

## 4. Audit détaillé par pays (ordre imposé : ZAF → KEN → TUN → MAR → EGY → DZA)

### 4.1 ZAF — Afrique du Sud

**Source** : `sars.gov.za` — SARS Customs & Excise Tariff (SACU).
**Extraction déclarée** : `2026-02-17T22:11:19`.
**Fichier** : `backend/data/crawled/ZAF_tariffs.json`, clé `positions`.

**Comptage 1 — population et colonnes fiscales présentes**

```python
import json
d = json.load(open("backend/data/crawled/ZAF_tariffs.json"))
positions = d["positions"]
print(len(positions))  # population totale
codes = set()
for p in positions:
    for t in p.get("taxes", []):
        codes.add(t.get("code"))
print(sorted(codes))
```
Résultat : population = **8 589**. Colonnes présentes sur 100 % des
positions : `AfCFTA`, `EFTA`, `EU_UK`, `GENERAL`, `MERCOSUR`, `SADC`.

**Comptage 2 — colonne AfCFTA, distinction taux disponible vs applicabilité**

```python
zero_free = null = nonzero = 0
for p in positions:
    for t in p["taxes"]:
        if t["code"] == "AfCFTA":
            if t["rate_pct"] == 0.0 and t["raw_value"] == "free":
                zero_free += 1
            elif t["rate_pct"] is None:
                null += 1
            else:
                nonzero += 1
print(zero_free, null, nonzero)
```
Population = 8 589. Résultat : `rate_pct=0.0 & raw_value="free"` = **4 654** ;
`rate_pct=None` = **185** ; `rate_pct` non nul = **3 750** (distribution
observée : 4,0 % ×790, 6,0 % ×684, 8,0 % ×528, 10,0 % ×227, 8,8 % ×218,
20,0 % ×201...).

**Analyse — trois constats à statut distinct, à ne pas fusionner.**

Sous le principe directeur du §0 (une donnée traçable est affichable à
titre informatif même sans certification juridique), ces trois constats se
combinent en un statut d'affichage unique `PARTIAL` — mais chacun répond à
une question différente et doit rester distingué :

1. **Fait comptable (confirmé)** : 4 654 lignes du fichier contiennent une
   valeur `AfCFTA` égale à `rate_pct=0.0` avec `raw_value="free"` (comptage
   direct, reproductible, voir Comptage 2 ci-dessus). Ceci est un fait sur
   le contenu du fichier, pas une affirmation sur la portée juridique du
   taux.
2. **Traçabilité de l'origine (confirmée)** : ces structures ne
   comportent **aucun** champ définissant les partenaires admissibles. La
   structure de l'objet `taxes[i]` est strictement
   `{code, name, rate_pct, raw_value}` (vérifié par inspection directe des
   clés : `p["taxes"][0].keys()` =
   `dict_keys(['code', 'name', 'rate_pct', 'raw_value'])`) — aucun
   `applicable_partners`, aucune date d'effet, aucune règle d'origine.
   L'origine de la valeur elle-même (colonne AfCFTA du barème SARS) reste
   cependant identifiable — c'est ce qui rend la donnée affichable à titre
   informatif (`PARTIAL`), et non `NOT_AVAILABLE`.
3. **Certification juridique et applicabilité produit-partenaire : `PARTIAL`,
   pas `NOT_AVAILABLE`.** Leur seule présence dans le JSON prouve qu'une
   valeur a été extraite d'une colonne nommée « AfCFTA » du barème SARS —
   **pas** qu'elle est actuellement opposable à un envoi donné. Cela
   dépendrait du partenaire d'origine, de sa propre mise en œuvre effective
   de la ZLECAf, et de la règle d'origine du produit — aucun de ces trois
   éléments n'est présent ligne à ligne dans ce fichier, et la source
   officielle SARS correspondante (Schedule 1 Part 1) n'est pas ingérée ni
   reliée à ces lignes (voir statut `SOURCE_PENDING_COLLECTION` ci-dessous).
   Ces taux ne doivent donc pas être qualifiés de « certifiés » ou
   « opposables » sur la seule base de leur présence dans le fichier — mais
   ils **peuvent** être affichés à titre informatif, avec la mention de
   portée §0, tant que leur statut `PARTIAL` (et non `DOCUMENTED`) reste
   visible.

**Croisement avec la documentation déjà archivée**
(`docs/data-sources/ZAF_SOURCE_REGISTER.md:13,26-35`, statut confirmé par
lecture directe du fichier) :
> « Le barème de concessions ligne à ligne (« colonne AfCFTA » de Schedule
> No. 1 Part 1...) est localisé et confirmé publiquement accessible, mais
> **non téléchargé ni extrait**... Tant que ce barème n'est pas ingéré,
> l'Afrique du Sud n'est pas enregistrée comme offre nationale ZLECAf
> (`NATIONAL_OFFER_REGISTRY`)... une classification y serait actuellement
> servie par le canevas générique (`AFCFTA_CANVAS_HS2`), jamais fabriquée. »

Ce texte, déjà présent dans le dépôt avant cette vague, est cohérent avec le
comptage ci-dessus : le fichier `ZAF_tariffs.json` contient un extrait
« brut » de la colonne AfCFTA (issu d'un crawl SARS antérieur, source
`sars.gov.za` déclarée), **distinct** du PDF Schedule 1 Part 1 complet
(24 juillet 2026) mentionné comme `SOURCE_PENDING_COLLECTION` dans le
registre. Il existe donc une **divergence non résolue entre deux
générations de collecte ZAF** que cette vague ne tranche pas (hors
périmètre : pas de re-collecte autorisée ici).

**Statut de source** :

| Source | Institution | Titre | URL | Date consultation | Date/version | Portée | Statut |
|---|---|---|---|---|---|---|---|
| `ZAF-SARS-SCH1P1-AFCFTA-COLUMN` | SARS | Schedule No. 1 Part 1, chapitres 1-99, colonne AfCFTA | `sars.gov.za/legal-lprim-ce-sch1p1chpt1-to-99...` | 2026-07-25 (tentative), PDF confirmé accessible (HTTP 200 en curl direct, 403 en HEAD via proxy WebFetch) | 2026-07-24 (mise à jour SARS) | Barème complet 99 chapitres | `SOURCE_PENDING_COLLECTION` (non ingéré, cf. registre) |
| `ZAF_tariffs.json` (fichier runtime) | sars.gov.za (déclaré) | SARS Customs & Excise Tariff (SACU) | non consignée dans le fichier lui-même | 2026-02-17 (`extraction_date`) | inconnue (pas de date de version SARS dans le fichier) | 8 589 positions, 6 colonnes tarifaires | `PARTIAL` — données tarifaires plausibles mais sans traçabilité de version ni portée par partenaire |

### 4.2 KEN — Kenya

**Source** : EAC Common External Tariff 2022 (kra.go.ke).
**Extraction déclarée** : `2026-02-18T10:54:33`.
**Fichier** : `backend/data/crawled/KEN_tariffs.json`, clé `positions`.

**Comptage 1 — population et texte générique ZLECAf**

```python
import json
d = json.load(open("backend/data/crawled/KEN_tariffs.json"))
positions = d["positions"]
print(len(positions))  # population totale = dénominateur
n = sum(1 for p in positions
        if any(a.get("name") == "AfCFTA Tariff Concession"
               for a in p.get("fiscal_advantages", [])))
print(n)
```
Population = **5 984**. Résultat = **5 984 / 5 984 (100 %)**.

Texte exact, identique sur les 5 984 lignes (vérifié par inspection directe,
pas d'échantillonnage) :
```json
{"name": "AfCFTA Tariff Concession",
 "description": "Progressive duty reduction for AfCFTA member states",
 "conditions": "AfCFTA Certificate of Origin required"}
```

**Verdict — ceci n'est pas un cas « traçable mais non certifié », c'est un
cas d'origine non identifiable, donc interdit.** Ce texte ne porte ni taux,
ni calendrier, ni partenaire admis, ni date d'effet — c'est un gabarit
narratif **identique sur 100 % des lignes**, sans aucune variation
produit par produit. Contrairement à ZAF (§4.1) ou EGY (§4.5), où la valeur
varie ligne à ligne et peut être reliée à un champ ou un mécanisme de calcul
identifiable, rien ici ne distingue une ligne d'une autre : il n'y a pas
d'origine par ligne à tracer. Sous le principe directeur du §0, cette
absence de traçabilité — pas l'absence de certification — est le motif
d'exclusion. **Statut : `NOT_AVAILABLE` pour cette composante, à exclure du
flux actif** (stockage, calcul, API, interface, fallback).

Par ailleurs, aucune offre nationale kényane officiellement publiée et
exploitable n'a été retrouvée dans les sources consultées pendant cet audit
(recherché sur kra.go.ke, Kenya Law, National Treasury — aucun document
trouvé décrivant un calendrier de démantèlement kényan). **Cette absence de
résultat ne constitue pas une preuve d'inexistence.** Statut de cette
recherche de source : `SOURCE_BLOCKED` (concept distinct du statut
d'affichage de la donnée elle-même, ci-dessus).
Confirmé côté code : `NATIONAL_OFFER_REGISTRY`
(`backend/etl/afcfta_national_offers.py:82-93`) **ne contient pas** KEN.

**Comptage 2 — droit CET (EAC), pour ne pas jeter les données réelles avec les fabriquées**

```python
from collections import Counter
cet_rates = Counter()
cet_null = 0
for p in positions:
    for t in p.get("taxes_detail", []):
        if t.get("is_cet") is True:
            r = t.get("rate")
            cet_null += (r is None)
            if r is not None: cet_rates[r] += 1
print(cet_null, dict(cet_rates))
```
Population = 5 984 positions (5 893 avec `CET Import Duty` standard + 48
`CET Import Duty (Sensitive Item)`, 43 sans aucune entrée `is_cet` détectée
dans l'échantillon de clé `is_cet` — total lignes taxes_detail = 23 958,
soit 4 taxes/position en moyenne). Résultat : `rate=None` = **48** (régime
« sensitive item », cohérent avec le régime EAC) ; distribution non-nulle :
0 % ×2 234, 25 % ×1 962, 10 % ×1 169, 35 % ×493, 50 % ×19, 60 % ×15, 6 % ×1.
**Ce comptage est authentique** — pas de marqueur de fabrication sur le CET,
l'IDF (3,5 %), le RDL (2,0 %) ni la VAT (16 %). Statut : `DOCUMENTED` — ces
composantes restent pleinement affichables, y compris après exclusion de la
composante ZLECAf ci-dessus (l'interdiction porte sur *cette* composante
précise, pas sur la ligne tarifaire entière).

**Distinction imposée** : *existence d'un taux CET* (réel, sourcé EAC) ≠
*éligibilité à une préférence ZLECAf* (aucune preuve) ≠ *partenaire admis*
(aucun) ≠ *réciprocité* (non documentée) ≠ *règle d'origine* (le texte
mentionne « AfCFTA Certificate of Origin required » sans préciser laquelle)
≠ *réduction économique effective* (aucun taux préférentiel chiffré n'est
associé à ce texte — c'est une description, pas une donnée).

**Statut de source** :

| Source | Institution | Titre | URL | Date consultation | Statut |
|---|---|---|---|---|---|
| `KE-EAC-CET-2022-JUN2025` | East African Community | EAC CET — 2022, version actualisée juin 2025 | archivée (`data/sources/kenya/official/`) | 2026-07-25 (inventaire existant) | `DOCUMENTED` pour le CET/IDF/RDL/VAT — `NOT_AVAILABLE` pour la composante ZLECAf |
| Offre ZLECAf nationale KEN | — | — | — | recherché, non trouvé dans cette vague | `SOURCE_BLOCKED` (aucun document identifié ; absence de résultat ≠ preuve d'inexistence, mais aucune source ne peut être citée) |

### 4.3 TUN — Tunisie

**Source** : `douane.gov.tn/tarifweb2025`.
**Fichier** : `backend/data/crawled/TUN_tariffs.json`, clé `sub_positions`.

**Comptage 1 — population et structure des préférences**

```python
import json
from collections import Counter
d = json.load(open("backend/data/crawled/TUN_tariffs.json"))
positions = d["sub_positions"]
print(len(positions))
rate_dist = Counter()
for p in positions:
    for pref in p.get("preferences", []):
        rate_dist[str(pref.get("rate")).strip()] += 1
print(dict(rate_dist))
```
Population = **17 512**. Distribution des taux dans `preferences` (toutes
lignes × tous partenaires confondus, total occurrences = 213 102) :
`0 %` ×172 137 ; `50 %` ×38 490 ; `80 %` ×1 261 ; `75 %` ×1 193 ; `89 %` ×14 ;
`100 %` ×6 ; `63 %` ×1.

**Comptage 2 — hétérogénéité par pays et par produit (test de non-fabrication)**

```python
p0 = positions[0]  # code=01012100015
for pref in p0["preferences"]:
    print(pref)
```
Résultat pour une seule position (chevaux de course reproducteurs) :
EGYPTE=0 %, CAMEROUN=50 %, MAURICE=0 %, RUANDA=0 %, PALESTINE=0 %,
GHANA=50 %, TANZANIE=0 %, KENYA=50 %, KOWEIT=0 %.

**Analyse** : sur un même produit, le taux varie selon le partenaire
(0 % ou 50 % selon le pays), et pour un même partenaire (ex. KENYA), le
taux varie selon les produits (KENYA a 12 830 occurrences dont 0 à 0 % —
donc jamais 0 % sur l'échantillon de comptage global, voir tableau
ci-dessous). Cette hétérogénéité croisée pays×produit est **incompatible
avec une valeur par défaut fabriquée** (qui serait uniforme) et cohérente
avec une extraction réelle depuis tarifweb.tn.

**Comptage 3 — présence des partenaires ZLECAf dans `preferences`**

```python
zlecaf_candidates = ["MAROC","ALGERIE","EGYPTE","CAMEROUN","MAURICE",
                      "RUANDA","GHANA","KENYA","TANZANIE","PALESTINE"]
by_zero = Counter(); by_nonzero = Counter()
for p in positions:
    for pref in p.get("preferences", []):
        c = pref.get("country_name")
        if str(pref.get("rate")).strip() == "0 %": by_zero[c] += 1
        else: by_nonzero[c] += 1
for c in zlecaf_candidates:
    print(c, by_zero[c], by_nonzero[c])
```
Résultat (population par pays = nombre de lignes où ce pays apparaît dans
`preferences`, pas 17 512) :

| Partenaire | 0 % | non-0 % | total lignes portant ce partenaire |
|---|---:|---:|---:|
| MAROC | 13 706 | 1 | 13 707 |
| ALGERIE | 13 332 | 0 | 13 332 |
| EGYPTE | 10 615 | 24 | 10 639 |
| CAMEROUN | 0 | 12 830 | 12 830 |
| MAURICE | 12 830 | 0 | 12 830 |
| RUANDA | 12 830 | 0 | 12 830 |
| GHANA | 0 | 12 830 | 12 830 |
| KENYA | 0 | 12 830 | 12 830 |
| TANZANIE | 12 830 | 1 251 | 14 081 |
| PALESTINE | 17 506 | 0 | 17 506 |

**Constat critique — accord non identifié.** La colonne `preferences` de
`tarifweb.tn` liste des taux par **pays partenaire**, mais **ne précise pas
le régime juridique** (accord bilatéral, GATT, Ligue arabe, ou ZLECAf). Le
fait que MAROC/ALGERIE/EGYPTE/PALESTINE soient très majoritairement à 0 %
peut refléter des accords **préexistants à la ZLECAf** (Grande zone arabe de
libre-échange — GZALE/GAFTA, dont la Tunisie est membre depuis 1998).
CAMEROUN/GHANA/KENYA à 50 % (jamais 0 % dans cet échantillon) sont
incompatibles avec une exonération ZLECAf généralisée, ce qui **exclut** la
lecture « ZLECAf = 0 % partout » et confirme qu'aucune extrapolation
« pays africain donc préférentiel » n'a été appliquée — mais ne permet pas
non plus de confirmer que les taux à 0 % pour MAROC/ALGERIE/EGYPTE
proviennent de la ZLECAf plutôt que de GAFTA.

**Verdict** : structure `preferences` **plausiblement authentique**
(hétérogénéité croisée forte, origine identifiable — tarifweb.tn), mais
**le régime juridique associé à chaque taux n'est pas déterminable depuis
ce fichier seul**. Statut : `PARTIAL` — affichable à titre informatif,
conservé tel quel, aucune donnée à supprimer ; mais aucune préférence
ZLECAf ne doit être déclarée juridiquement **applicable** (opposable) à
partir de cette seule colonne tant que le régime (GAFTA vs ZLECAf) n'est
pas distingué. La distinction affichage informatif / applicabilité
juridique (§0) s'applique ici explicitement.

**Statut de source** :

| Source | Institution | Titre | URL | Date consultation | Statut |
|---|---|---|---|---|---|
| tarifweb 2025 | Douane tunisienne | Tarif intégré, préférences par pays | douane.gov.tn/tarifweb2025 (portail applicatif, pas de PDF unique) | 2026-02-11 (`extracted_at` du fichier) | `PARTIAL` — données plausibles, régime juridique (GAFTA/ZLECAf) non distingué par ligne |

### 4.4 MAR — Maroc

**Source** : `douane.gov.ma/adil`.
**Fichier** : `backend/data/crawled/MAR_tariffs.json`, clé `sub_positions`.

**Comptage 1 — population et longueur des codes**

```python
import json
from collections import Counter
d = json.load(open("backend/data/crawled/MAR_tariffs.json"))
positions = d["sub_positions"]
print(len(positions))
lengths = Counter(len(p["code"]) for p in positions)
print(dict(lengths))
```
Population = **13 114**. Tous les codes font exactement 10 caractères
(`{10: 13114}`) — aucune variation de longueur.

**Comptage 2 — ventilation `00` terminal vs non-`00`, avec test de coexistence intra-heading**

```python
padded_00 = sum(1 for p in positions
                if p["code"].endswith("00") and len(p["code"]) == 10)
native = 13114 - padded_00
print(padded_00, native)

# Test décisif : le même en-tête HS4 contient-il les deux formes ?
h0101 = [p["code"] for p in positions if p["code"].startswith("0101")]
print(sorted(h0101))
```
Population = 13 114. Résultat : codes finissant par `00` = **6 616** ;
codes non-`00` = **6 498**. Sur l'en-tête `0101` (chevaux) :
`['0101210000', '0101291000', '0101292000', '0101299000', '0101300010',
'0101300090', '0101900000']` — **les deux formes coexistent dans le même
en-tête**, avec des désignations distinctes et cohérentes pour chacune
(`0101210000` = « Reproducteurs de race pure », `0101300010` = « ânes,
espèces domestiques, reproducteurs de race pure »).

**Vérification de la source du code** — inspection de
`backend/crawlers/countries/morocco_douane_scraper.py:61-63` :
```python
match = re.search(r"info_x\.asp\?position=(\d{10})", href)
```
Le crawler **extrait directement** un identifiant à 10 chiffres depuis le
HTML servi par le portail ADIL (paramètre `position=` de l'URL officielle
`info_x.asp`) — il n'existe **aucune ligne de code, dans ce scraper, qui
ajoute, tronque ou complète un code**. Le suffixe `00` est donc **produit
par ADIL lui-même**, pas par le pipeline de collecte. Confirmé également par
recherche négative :

```python
# Marqueurs upgrade_v2 recherchés — tous absents
n = len(positions)
impdec = sum(1 for p in positions
             for f in p.get("administrative_formalities", [])
             if isinstance(f, dict) and f.get("code") == "IMPDEC")
kg = sum(1 for p in positions if p.get("unit") == "KG")
sous_pos = sum(1 for p in positions
               if isinstance(p.get("description"), str)
               and p["description"].startswith("Sous-position"))
print(impdec, kg, sous_pos)  # 0 0 0
```
**Résultat : 0, 0, 0** — aucun des marqueurs de `upgrade_to_enhanced_v2.py`
(IMPDEC par défaut, unité `KG` par défaut, description synthétique) n'est
présent dans MAR. Ce script n'a jamais été appliqué à ce fichier. La
structure observée (`code`, `designation`, `chapter`, `taxes` en valeurs
brutes de type `"2.5 %"`, `formalities` en libellés textuels) est celle
d'une extraction ADIL directe, pas d'un pipeline d'enrichissement.

**Correction par rapport à la version précédente de ce rapport** : la
version du 2026-07-26 (avant cette révision) qualifiait les 6 616 codes
`00` de « padding artificiel documenté dans `upgrade_to_enhanced_v2.py:219,225` ».
Cette affirmation est **infirmée** par (a) l'absence de tout marqueur
`upgrade_v2` dans le fichier, (b) la coexistence de formes `00` et non-`00`
dans un même en-tête avec des désignations distinctes et cohérentes, et
(c) l'inspection du crawler source qui ne pratique aucune concaténation. Le
suffixe `00` documente vraisemblablement, dans la nomenclature ADIL, un
niveau hiérarchique où la position nationale ne subdivise pas davantage le
code SH8/SH9 publié — hypothèse cohérente avec les données mais **non
confirmée positivement** faute d'une documentation ADIL explicite sur la
sémantique du suffixe consultée dans cette vague.

**Ce fichier ne porte aucune donnée ZLECAf** (aucun champ `zlecaf_rate`,
`preferences` ou `advantages` lié à la ZLECAf n'existe dans MAR — vérifié :
`'zlecaf_rate' in p` = 0/13 114). Statut ZLECAf : `NOT_AVAILABLE` — au sens
strict « aucune donnée traçable exploitable », et non « donnée bannie » :
il n'y a simplement rien à afficher, aucune interdiction ne s'applique ici.
Les composantes DI/TPI/TVA, elles, sont d'origine identifiable (portail
ADIL) et affichables à titre informatif : statut `PARTIAL`.

**Statut de source** :

| Source | Institution | Titre | URL | Date consultation | Statut |
|---|---|---|---|---|---|
| ADIL (portail) | ADII / douane.gov.ma | Positions tarifaires nationales, DI/TPI/TVA | douane.gov.ma/adil (portail dynamique, `info_x.asp`) | 2026-02-11 (`extracted_at`) | `PARTIAL` — extraction plausible, sémantique du suffixe `00` non confirmée par documentation officielle explicite ; aucune donnée ZLECAf présente |

### 4.5 EGY — Égypte

**Source** : Egyptian Customs Authority (customs.gov.eg/Services/Tarif).
**Fichier** : `backend/data/crawled/EGY_tariffs.json`, clé `sub_positions`.

**Comptage 1 — population et réconciliation de la contradiction 964 vs 6 320**

```python
import json
from collections import Counter
d = json.load(open("backend/data/crawled/EGY_tariffs.json"))
positions = d["sub_positions"]
print(len(positions))

zlecaf_0 = [p for p in positions if p.get("zlecaf_rate") == 0.0]
print(len(zlecaf_0))

dd_bucket = Counter()
for p in zlecaf_0:
    dd = p.get("taxes", {}).get("DD")
    dd_rate = dd.get("rate_pct", dd.get("rate")) if isinstance(dd, dict) else dd
    dd_bucket["DD=0.0"] += (dd_rate in (0.0, 0))
    dd_bucket["DD>0"] += (isinstance(dd_rate, (int, float)) and dd_rate not in (0.0, 0))
print(dict(dd_bucket))
```
Population = **8 746**. `zlecaf_rate = 0.0` (toutes lignes confondues) =
**6 320**. Ventilation : `DD = 0.0` (0 %→0 %, aucune réduction possible) =
**963** ; `DD > 0` (préférence apparente) = **5 357**.

**Réconciliation explicite** : le chiffre « 964 » cité dans une version
antérieure de cet audit était **erroné**. Le recomptage reproductible
donne, sur les mêmes données :
- **6 320** lignes avec `zlecaf_rate = 0.0` (population totale) ;
- **963** de ces lignes avec un droit NPF (DD) égal à zéro ;
- **5 357** de ces lignes avec un droit NPF (DD) strictement supérieur à
  zéro ;
- vérification : 963 + 5 357 = 6 320 ✓ (identité exacte, recomptée deux
  fois avec des scripts indépendants, même résultat les deux fois).

L'écart d'une unité entre l'ancien chiffre « 964 » et le chiffre
reproductible « 963 » n'a pas pu être reconstruit : aucune trace de la
méthode de comptage utilisée pour produire « 964 » n'a été retrouvée dans
cette vague, et aucune hypothèse (arrondi, double-comptage, filtre
légèrement différent) n'a pu être confirmée ou infirmée avec certitude.
Le chiffre « 964 » doit donc être considéré comme **incorrect et
abandonné** ; **963** est la valeur actuelle, reproductible, à retenir.
La distinction importante que masquait la formulation initiale : sur les 6 320 lignes à
`zlecaf_rate=0.0`, **5 357 ont un DD strictement positif** — ce sont ces
5 357 lignes qui représentent une **exonération ZLECAf potentielle non
prouvée** (le taux existe dans le fichier, mais aucune portée par
partenaire, aucune date d'effet, aucune règle d'origine ne l'accompagne).
Les 963 restantes (DD déjà à 0 %) ne peuvent, par construction, représenter
aucune réduction économique quel que soit le régime.

**Comptage 2 — lignes zlecaf_rate non nul, pour ne pas sur-généraliser**

```python
zlecaf_rates = Counter()
for p in positions:
    z = p.get("zlecaf_rate")
    if isinstance(z, (int, float)) and z != 0.0:
        zlecaf_rates[z] += 1
print(sum(zlecaf_rates.values()), dict(zlecaf_rates.most_common(10)))
```
Population = 8 746. Résultat : **2 373** lignes à `zlecaf_rate` non nul
(3,0 % ×593, 10,0 % ×560, 5,0 % ×369, 20,0 % ×186, 30,0 % ×159, 2,0 % ×119,
0,8 % ×91, 40,0 % ×80, 60,0 % ×68, 135,0 % ×27...). **53** lignes à
`zlecaf_rate = null` (traitement correct : absence non convertie en zéro).

**Analyse** — la présence de taux non nuls, non uniformes, variés (jusqu'à
135 %, valeur incompatible avec une préférence, probablement un droit
spécifique mal étiqueté ou un taux composé) suggère que le champ
`zlecaf_rate` **n'est pas systématiquement une valeur par défaut à 0**, mais
son origine documentaire (quel texte égyptien fixe ces taux, à quelle date,
pour quels partenaires) **n'est pas tracée au niveau de la ligne active du
fichier**. Aucun champ `source_id`, `legal_reference` ou `effective_from`
n'accompagne `zlecaf_rate` dans `EGY_tariffs.json`.

**Découverte du mécanisme de calcul (inspection de code, pas de nouvelle
collecte)** : `backend/scripts/build_egy_tariffs_v2.py:73-110`
(fonction `afcfta_advantages`) montre que `zlecaf_rate` n'est **pas une
valeur arbitraire** — elle est **calculée par une règle** à partir des
notes réglementaires officielles égyptiennes réelles, scannées et
présentes dans le fichier sous `official_instructions` (texte arabe brut,
ex. « ر6790 », « ر6791 »). Le docstring du script (lignes 5-12) cite ces
codes explicitement :
```
ر6790 — AfCFTA Group [A]: 100% DD reduction  (→ 0%)
ر6791 — AfCFTA Group [B]:  60% DD reduction  (→ DD × 0.4)
ر6792 / ر6793 — category-based AfCFTA rates
```
Chaque branche de la règle porte une `legal_ref` explicite (ex. « Tarif
douanier égyptien — note ر6790 ; AfCFTA Protocol on Trade in Goods »,
`build_egy_tariffs_v2.py:89,100`). **Cette richesse (regime, legal_ref,
condition_fr) est calculée, mais volontairement non recopiée sur la ligne
`sub_position` du fichier `EGY_tariffs.json` chargé au runtime** — le
commentaire du script l'explicite (`build_egy_tariffs_v2.py:218-221`) :
« Canonical sub_position is kept lean: the AfCFTA treatment is already
captured in zlecaf_rate / fiscal_advantages. The verbatim official Arabic
instructions (source evidence) are preserved once, in the crawled evidence
file. » Autrement dit : l'évidence brute (`official_instructions`) **est**
présente dans le fichier actif à côté du taux calculé, mais pas
l'explication de la règle qui l'a produit.

**Test empirique de reproductibilité (exigé avant toute qualification
`PARTIAL`)** — la seule inspection du code ne suffit pas à démontrer que la
chaîne est reproductible : il faut la ré-exécuter sur les données réelles et
comparer au résultat stocké. Réimplémentation fidèle de la fonction
(constantes `AFCFTA_A_100="ر6790"`, `AFCFTA_B_60="ر6791"`,
`AFCFTA_A_CAT="ر6792"`, `AFCFTA_B_CAT="ر6793"`, logique
`build_egy_tariffs_v2.py:73-123`), exécutée sur les 8 746 `official_instructions`
et `zlecaf_rate` réellement stockés dans `EGY_tariffs.json` :

```python
def _has(instructions, code):
    return any(i.startswith(code) for i in instructions)

def afcfta_zlecaf_rate(dd_rate, instructions):
    if _has(instructions, "ر6790"): return 0.0
    if _has(instructions, "ر6791") and dd_rate is not None:
        return round(dd_rate * 0.4, 3)
    if (_has(instructions, "ر6792") or _has(instructions, "ر6793")):
        return dd_rate
    return None  # aucune note AfCFTA identifiée

match = mismatch = 0
for p in positions:
    dd = p["taxes"]["DD"]["rate"]; instr = p["official_instructions"]
    recomputed = afcfta_zlecaf_rate(dd, instr)
    if recomputed is None: continue
    if p["zlecaf_rate"] == recomputed: match += 1
    else: mismatch += 1
print(match, mismatch)
```
Population = 8 746. Résultat : **6 417** lignes portent une note AfCFTA
réelle (`ر6790`/`ر6791`/`ر6792`/`ر6793`) — **concordance exacte 6 417/6 417,
0 divergence**. La chaîne règle→notes→calcul→valeur stockée est intégralement
démontrée et reproductible pour ce sous-ensemble.

**Découverte critique sur le sous-ensemble restant** — inspection de
`build_egy_tariffs_v2.py:115-123` (branche finale de la fonction) :
```python
# No AfCFTA note → excluded / sensitive list, MFN rate maintained
return dd_rate, "Hors démantèlement ZLECAf — taux NPF maintenu (liste d'exclusion)", advantages
```
Quand **aucune** note AfCFTA n'est identifiée, la fonction retourne quand
même une valeur (`dd_rate`, pas `None`) accompagnée d'un `zlecaf_source`
explicite signalant l'absence de traitement ZLECAf. **Ce `zlecaf_source`
est calculé mais jamais persisté dans le fichier runtime** : la ligne
d'assemblage `crawled_subs.append(...)` (`build_egy_tariffs_v2.py:349-362`)
ne retient que `zlecaf_rate`, pas le second élément du triplet retourné
(`c_zlecaf, _, _ = afcfta_advantages(...)`, `_` = valeur explicitement
écartée, ligne 327). Vérifié sur les données réelles : **2 276 lignes**
n'ont aucune note AfCFTA et ont `zlecaf_rate == DD` dans **100 % des cas**
(2 276/2 276) — confirmant que ce sous-ensemble n'est pas une préférence
ZLECAf réelle, mais une **copie du taux NPF sous un nom de champ ZLECAf**,
sans le label qui permettrait de le distinguer d'une vraie réduction.

**Conséquence pour le statut — qualification scindée, pas monolithique** :
- **6 417 lignes** (note AfCFTA confirmée, chaîne reproductible démontrée
  empiriquement) : `PARTIAL` — traçable, reproductible, préférence réelle ;
  documentation incomplète au niveau de la ligne (`legal_ref`/`regime` non
  recopiés), mais aucune ambiguïté sur la nature de la donnée.
- **2 276 lignes** (aucune note, `zlecaf_rate` = copie du DD) : **`UNVERIFIED`**,
  pas `PARTIAL`. L'origine du mécanisme est identifiable (code cité
  ci-dessus), mais le fichier runtime ne permet pas de distinguer cette
  copie d'une préférence réelle sans relire le code source — c'est
  exactement le « contrôle insuffisant » que `UNVERIFIED` est censé
  signaler. Présenter ce champ comme une donnée ZLECAf sans cette
  distinction serait trompeur, même si la valeur elle-même n'est pas
  fabriquée.
- **53 lignes** `zlecaf_rate = null` : traitement correct, `NOT_AVAILABLE`
  au sens strict (absence non convertie en zéro).

Ni les 6 417, ni les 2 276 ne peuvent être qualifiées `DOCUMENTED`. Aucune
des deux ne relève de l'interdiction absolue au sens de KEN (§4.2) et DZA
(§4.6) — il ne s'agit pas d'un texte générique sans origine, mais de deux
sous-populations d'un même mécanisme, dont l'une nécessite un
enrichissement (`legal_ref`) et l'autre une correction de fond (persister
`zlecaf_source` ou exclure le champ pour ces lignes) avant de pouvoir
prétendre à un statut supérieur.

**Statut de source** :

| Source | Institution | Titre | URL | Date consultation | Statut |
|---|---|---|---|---|---|
| customs.gov.eg/Services/Tarif | Egyptian Customs Authority | Service tarifaire, DD/TVA + champ zlecaf_rate | customs.gov.eg/Services/Tarif | non consignée (`extracted_at` absent du fichier, champ `null`) | `PARTIAL` pour la composante `zlecaf_rate` (mécanisme de calcul et évidence brute identifiables, `legal_ref` non recopiée par ligne — voir §4.5) ; DD/TVA `PARTIAL` (source plausible mais date de consultation manquante) |

### 4.6 DZA — Algérie

**Source** : `conformepro.dz` (déclare « données douane.gov.dz »).
**Fichier** : `backend/data/crawled/DZA_tariffs.json`, clé `sub_positions`.

**Comptage 1 — population et texte générique ZLECAf**

```python
import json
d = json.load(open("backend/data/crawled/DZA_tariffs.json"))
positions = d["sub_positions"]
print(len(positions))
n = 0
for p in positions:
    for adv in p.get("advantages", []):
        cond = str(adv.get("condition_fr", ""))
        if "Certificat d'Origine dans le cadre ZLECAf" in cond and "Exonération DD" in cond:
            n += 1
            break
print(n)
```
Population = **17 061**. Résultat = **4 119 / 17 061 (24,1 %)**.

Texte exact (identique sur les 4 119 lignes, vérifié par comparaison
directe de chaîne, pas d'échantillonnage) :
```json
{"tax": "D.D", "rate": 0.0,
 "condition_fr": "Certificat d'Origine dans le cadre ZLECAf - Exonération DD"}
```

**Croisement avec le statut de source déjà documenté dans le code** —
`engine/adapters/dza_conformepro_adapter.py:14-17` (citation exacte,
inspection directe du fichier) :
> « Statut de provenance émis : PARTIAL / fiabilité B. conformepro.dz est
> un agrégateur privé du tarif intégré algérien — pas la source primaire
> (DGD / Journal Officiel). Les lignes passeront VERIFIED/A après
> recoupement avec le tarif officiel DGD. »

**Croisement avec `NATIONAL_OFFER_REGISTRY`** —
`backend/etl/afcfta_national_offers.py:82-93` (inspection directe) :
```python
"DZA": NationalOfferAdapter(
    iso3="DZA", hs_precision=10, classify=_dza_classify,
    legal_reference="Circulaire DGD n°482/DGD/SP/D.042/24 du 22/10/2024, ...",
    source_id="DZA-DGD-482-2024-PENDING",
    publication_url=None,
    ...
)
```
Le code lui-même encode `source_id` avec le suffixe `-PENDING` et
`publication_url=None`. Ceci prouve uniquement que **le dépôt ne contient
pas de publication officielle collectée** pour cette circulaire — pas que
la circulaire n'existe pas ou n'est pas publiée par ailleurs : son
accessibilité ou sa publication externe réelle n'a pas été établie pendant
cet audit. Le commentaire adjacent (lignes 75-81 du même fichier) précise :
> « le texte de la circulaire n'est, à ce jour, accessible sur aucun portail
> public interrogeable (douane.gov.dz et mfdgi.gov.dz injoignables au moment
> de la collecte) ; le contenu du calendrier est néanmoins repris fidèlement
> de la citation détaillée par article/partie déjà consignée dans
> `services/zlecaf_schedule_dza.py`. »

**Analyse — comme KEN (§4.2), ceci est un cas d'origine non identifiable,
donc interdit, pas un cas de certification manquante.** Les 4 119 lignes
`advantages[ZLECAf]` du fichier `DZA_tariffs.json` (chargé par
`crawled_data_service.py`) portent un texte **générique et non daté,
identique sur les 4 119 lignes**, sans aucune variation produit par
produit — contrairement à EGY (§4.5), où le taux est calculé par une règle
inspectable et varie ligne à ligne. Il n'y a ici aucune origine par ligne à
tracer. **Statut : `NOT_AVAILABLE` pour cette composante, à exclure du flux
actif.** Le reste du fichier (taxes DD/TCS/PRCT/TVA) reste `PARTIAL` (source
secondaire `conformepro.dz`, non fabriquée — voir tableau ci-dessous).

Il existe par ailleurs, comme pour ZAF, une **divergence entre deux
générations/chemins de données algériennes** : le fichier brut `crawled`
(source secondaire, texte générique interdit ci-dessus) et un service
séparé `zlecaf_schedule_dza.py` qui prétend porter un calendrier plus
précis par article/partie, mais sourcé sur une circulaire dont ni le
contenu ni la portée n'ont été vérifiés directement dans cette vague (non
audité — fichier séparé, pas dans le chemin de chargement
`crawled_service`).

Une URL a été communiquée en cours d'audit
(`douane.gov.dz/IMG/pdf/circulaire_no_482_dgd_du_22-10-2024_mise_en_oeuvre_zlecaf.pdf`).
Tentative de vérification : le fetch applicatif standard a retourné
HTTP 403 ; une vérification directe (`openssl s_client`) a confirmé que le
serveur `www.douane.gov.dz` répond bien et présente un certificat pour
`*.douane.gov.dz`, mais dont la chaîne est incomplète côté serveur
(intermédiaire Sectigo manquant, `unable to verify the first certificate`).
Conformément à la politique de cet environnement, la vérification TLS n'a
pas été contournée et **aucune copie officielle exploitable de ce document
n'a été collectée**. Ce blocage est de nature technique (TLS) et **ne
prouve ni l'absence de publication ni l'inexistence de la circulaire** — il
signifie seulement que son contenu, sa date d'effet et sa portée n'ont pas
pu être vérifiés dans cette vague. En l'absence de vérification, cette
source **ne doit déclencher aucun calcul préférentiel**. Statut inchangé :
`SOURCE_BLOCKED`.

**Statut de source** :

| Source | Institution | Titre | URL | Date consultation | Statut |
|---|---|---|---|---|---|
| conformepro.dz | agrégateur privé | Tarif intégré algérien | conformepro.dz | 2026-06-17 (`extracted_at`) | `PARTIAL` (statut `PARTIAL/B` déjà posé par le code, confirmé) |
| Circulaire 482/2024 | DGD (Direction Générale des Douanes) | Schéma général du traitement tarifaire à l'importation des produits dans le cadre de la ZLECAf | `douane.gov.dz/IMG/pdf/circulaire_no_482_dgd_du_22-10-2024_mise_en_oeuvre_zlecaf.pdf` (communiquée, non vérifiée) | tentée le 2026-07-27, non aboutie (HTTP 403 puis chaîne TLS incomplète côté serveur) | `SOURCE_BLOCKED` — aucune copie exploitable collectée ; contenu, date d'effet et portée non vérifiés ; ne prouve ni publication ni absence de publication |

---

## 5. Marqueurs suspects — tableau consolidé

| Pays | Marqueur | Champ | Population | Résultat | Nature confirmée | Statut d'affichage |
|---|---|---|---:|---:|---|---|
| ZAF | `AfCFTA.rate_pct=0.0 & raw_value="free"` sans partenaire | `positions[].taxes[]` | 8 589 | 4 654 | Origine identifiable (colonne SARS), portée juridique non prouvée par ligne | `PARTIAL` |
| KEN | Texte générique `AfCFTA Tariff Concession` | `positions[].fiscal_advantages[]` | 5 984 | 5 984 (100 %) | **Origine non identifiable** — narration uniforme sans taux ni variation par ligne | `NOT_AVAILABLE` (interdit) |
| TUN | Colonne `preferences` par pays | `sub_positions[].preferences[]` | 17 512 | n/a (hétérogène) | Origine identifiable, hétérogène par pays/produit ; régime juridique (GAFTA/ZLECAf) non distingué | `PARTIAL` |
| MAR | Codes se terminant par `00` | `sub_positions[].code` | 13 114 | 6 616 | **Faux positif infirmé** — notation ADIL native, pas de padding | `PARTIAL` (DI/TPI/TVA) |
| EGY | `zlecaf_rate=0.0` avec DD>0 | `sub_positions[].zlecaf_rate` | 8 746 | 5 357 (sous-ensemble de 6 320) | Scindé par test empirique (§4.5) : préférence réelle si note AfCFTA présente, copie du DD sinon | `PARTIAL` (6 417 avec note) / `UNVERIFIED` (2 276 sans note) |
| DZA | Texte générique « Exonération DD » ZLECAf | `sub_positions[].advantages[]` | 17 061 | 4 119 (24,1 %) | **Origine non identifiable** — narration uniforme, source du fichier elle-même secondaire | `NOT_AVAILABLE` (interdit) |

---

## 6. Comptages réconciliés (résolution des contradictions antérieures)

- **EGY 964 vs 6 320** : l'ancien chiffre « 964 » était **erroné** et est
  abandonné. Recomptage reproductible : 6 320 = population totale
  `zlecaf_rate=0.0` ; **963** = sous-population où `DD=0.0` également
  (aucune réduction possible arithmétiquement) ; 5 357 = sous-population où
  `DD>0` (exonération apparente non prouvée). 963 + 5 357 = 6 320 ✓ (recoupé
  deux fois, cohérent). La cause exacte de l'ancien écart d'une unité
  (964 vs 963) n'a pas pu être reconstruite ; 963 est la valeur actuelle à
  retenir.
- **MAR padding `00`** : **contradiction résolue en sens inverse de
  l'audit initial**. L'hypothèse « padding fabriqué par
  `upgrade_to_enhanced_v2.py`» est **infirmée** : (a) recherche négative des
  4 marqueurs caractéristiques de ce script (IMPDEC, KG, description
  synthétique, `sensitivity`) = 0 sur les 13 114 lignes ; (b) inspection du
  crawler source ne montre aucune concaténation de code ; (c) coexistence de
  formes `00`/non-`00` dans un même en-tête HS4 avec désignations
  cohérentes et distinctes.
- **KEN et DZA** : pas de contradiction numérique à réconcilier, mais
  confirmation croisée entre le comptage direct sur le fichier `crawled` et
  la documentation déjà présente dans le code (`NATIONAL_OFFER_REGISTRY`
  n'a pas KEN ; DZA y figure avec statut `PENDING` explicite).

---

## 7. Risques pour le calculateur

1. **KEN** : si `fiscal_advantages` est consommé sans filtre par une route
   de calcul, les 5 984 positions afficheraient une « concession AfCFTA »
   sans aucun taux chiffré associé — au mieux un texte creux, au pire une
   fausse impression d'éligibilité automatique. Risque : moyen (le texte ne
   porte pas de `rate`, donc il ne peut pas directement fabriquer un montant
   erroné, mais il peut induire en erreur un affichage UI listant les
   « avantages » disponibles).
2. **EGY** : risque scindé, désormais démontré empiriquement (§4.5). Pour
   les **6 417 lignes à note AfCFTA confirmée** (`PARTIAL`), le risque est
   un affichage sans mention de portée (§0), pas une fabrication — risque
   **moyen**. Pour les **2 276 lignes sans note** (`UNVERIFIED`), le risque
   est **plus sérieux** : `zlecaf_rate` y est une copie exacte du DD, sans
   le `zlecaf_source` qui signalerait « hors démantèlement ZLECAf, taux NPF
   maintenu ». Un calcul qui afficherait ce champ comme une préférence
   ZLECAf produirait une **fausse impression de traitement préférentiel là
   où il n'y en a aucun**. Risque : **élevé** pour ce sous-ensemble tant que
   `zlecaf_source` n'est pas persisté ou que le champ n'est pas exclu pour
   ces lignes.
3. **DZA** : les 4 119 lignes `advantages[ZLECAf]` restent, elles,
   interdites (§4.6 — aucune origine par ligne identifiable, contrairement
   à EGY). Risque : **élevé** si `rate: 0.0` est utilisé tel quel — c'est un
   champ numérique directement exploitable par un calcul, sans aucune
   traçabilité par ligne, partiellement atténué par le statut `PARTIAL`
   déjà documenté au niveau de l'adaptateur (si le calculateur respecte ce
   statut en amont).
4. **ZAF** : 3 750 lignes à taux AfCFTA non nul, réelles mais sans portée
   par partenaire — un calcul qui appliquerait ce taux à *tout* partenaire
   ZLECAf sans vérifier son admissibilité individuelle produirait une
   préférence non garantie pour les partenaires dont la mise en œuvre
   ZAF↔partenaire n'est pas confirmée. Risque : moyen à élevé selon
   l'usage réel du champ par les routes de calcul (non auditées dans cette
   vague — hors périmètre, aucune modification de moteur autorisée).
5. **TUN** : risque de confusion GAFTA/ZLECAf si `preferences` est
   consommé sans distinguer le régime juridique associé à chaque taux.
   Risque : moyen.
6. **MAR** : aucun risque de fabrication identifié dans les données
   elles-mêmes ; risque documentaire résiduel : la sémantique du suffixe
   `00` reste une hypothèse non confirmée par une source ADIL explicite.

---

## 8. Corrections proposées (documentées, **non appliquées** dans cette vague)

| Pays | Correction proposée | Portée | Pourquoi non appliquée ici |
|---|---|---|---|
| KEN | Retirer les 5 984 entrées `fiscal_advantages[AfCFTA Tariff Concession]` du fichier `KEN_tariffs.json` (origine non identifiable — interdiction absolue, pas un cas `PARTIAL`), ou les marquer explicitement `status: NOT_AVAILABLE` côté consommateur | 1 fichier JSON | Interdiction absolue de cette vague : « ne modifier aucun JSON pays » |
| EGY | Pour les 6 417 lignes à note AfCFTA confirmée : **ne pas supprimer** `zlecaf_rate` (`PARTIAL`), recopier `legal_ref`/`regime`/`condition_fr` (déjà calculés par `afcfta_advantages`) sur la ligne active. Pour les 2 276 lignes sans note : persister le `zlecaf_source` actuellement écarté (`_`, ligne 327 du script) ou exposer `zlecaf_rate: null` pour ces lignes tant que la distinction n'est pas visible côté données (`UNVERIFIED` → viser `PARTIAL` après correction) | 1 fichier JSON (enrichissement pour l'un, correction de fond pour l'autre) | Modification de JSON pays interdite dans cette vague |
| DZA | Retirer les 4 119 `advantages[ZLECAf]` génériques (origine non identifiable — interdiction absolue) ou les relier explicitement au calendrier détaillé de `zlecaf_schedule_dza.py` si celui-ci est jugé plus fiable (à auditer séparément) | 1 fichier JSON + 1 service séparé | Interdiction absolue de cette vague : « ne modifier aucun JSON pays » |
| ZAF | Ajouter un champ `applicable_partners` par ligne AfCFTA, dérivé de l'offre nationale ZAF une fois le PDF Schedule 1 Part 1 complet ingéré (déjà `SOURCE_PENDING_COLLECTION`) — la donnée reste affichable `PARTIAL` en attendant | 1 fichier JSON, nécessite re-collecte | Re-collecte hors périmètre de cette vague (audit seul) |
| TUN | Ajouter un champ `regime` (`GAFTA` / `ZLECAF` / `BILATERAL` / `UNKNOWN`) par entrée de `preferences`, après recherche du texte juridique associé à chaque accord — la donnée reste affichable `PARTIAL` en attendant | 1 fichier JSON, nécessite recherche complémentaire | Idem |
| MAR | Aucune correction de données requise ; documenter la sémantique du suffixe `00` auprès d'une source ADIL explicite si trouvée dans une vague future | Documentation seule | Recherche complémentaire non menée ici |

Ces corrections **ne doivent être exécutées que dans une itération
distincte, explicitement autorisée**, un pays par commit, avec tests de
non-régression avant tout push.

---

## 9. Tests futurs recommandés (non écrits, non exécutés dans cette vague)

- Test interdisant toute entrée `fiscal_advantages`/`advantages` dont le
  texte est identique sur plus de N % des positions d'un pays sans qu'un
  champ `rate` numérique daté et sourcé l'accompagne (couvrirait KEN et
  DZA).
- Test garantissant qu'un champ `zlecaf_rate` (ou équivalent) traçable mais
  incomplètement documenté (pas de `source_id`/`effective_from` au niveau
  de la ligne) est exposé avec un statut `PARTIAL` explicite côté API,
  jamais présenté comme `DOCUMENTED`/certifié (couvrirait EGY — sans
  bannir la donnée, conformément au principe directeur §0).
- Test de cohérence croisée `NATIONAL_OFFER_REGISTRY` / `SUPPORTED_JURISDICTIONS`
  vs les pays exposant des champs ZLECAf dans `backend/data/crawled/*.json`
  — actuellement KEN, EGY, DZA, ZAF exposent des données ZLECAf dans leurs
  fichiers `crawled` sans figurer (ZAF, KEN, EGY) ou en figurant `PENDING`
  (DZA) dans le registre officiel — cette divergence devrait être
  détectée automatiquement.
- Test de non-régression sur MAR garantissant qu'aucun futur passage par
  `upgrade_to_enhanced_v2.py` n'introduit les marqueurs recherchés en §4.4
  (IMPDEC, KG, description synthétique, sensitivity).
- Test TUN vérifiant qu'aucune route ne traite une entrée `preferences`
  comme ZLECAf sans un champ `regime` explicite (à créer, cf. §8).

---

## 10. Sources consultées — registre consolidé

| ID | Pays | Institution | Titre | URL | Date consultation | Date/version | Portée | Statut |
|---|---|---|---|---|---|---|---|---|
| `ZAF-SARS-SCH1P1-AFCFTA-COLUMN` | ZAF | SARS | Schedule No. 1 Part 1, colonne AfCFTA | sars.gov.za/legal-lprim-ce-sch1p1chpt1-to-99... | 2026-07-25 (tentative confirmée HTTP 200 en curl direct) | 2026-07-24 | 99 chapitres | `SOURCE_PENDING_COLLECTION` |
| `ZAF_tariffs.json` (interne) | ZAF | sars.gov.za (déclaré) | SARS Customs & Excise Tariff (SACU) | non consignée | 2026-02-17 | inconnue | 8 589 positions | `PARTIAL` |
| `KE-EAC-CET-2022-JUN2025` | KEN | EAC | CET 2022, actualisé juin 2025 | archivé localement | 2026-07-25 | 2025-06 | tarif complet | `DOCUMENTED` (hors composante ZLECAf, elle-même `NOT_AVAILABLE`) |
| Offre ZLECAf KEN | KEN | — | — | recherchée, non trouvée | 2026-07-27 | — | — | `SOURCE_BLOCKED` |
| tarifweb 2025 | TUN | Douane tunisienne | Tarif intégré + préférences | douane.gov.tn/tarifweb2025 | 2026-02-11 | 2025 | 17 512 positions | `PARTIAL` |
| ADIL | MAR | ADII | Positions tarifaires nationales | douane.gov.ma/adil | 2026-02-11 | inconnue | 13 114 positions | `PARTIAL` |
| Service tarifaire | EGY | Egyptian Customs Authority | DD/TVA + zlecaf_rate | customs.gov.eg/Services/Tarif | non consignée | inconnue | 8 746 positions | Scindé : `PARTIAL` (6 417, note AfCFTA confirmée) / `UNVERIFIED` (2 276, copie du DD sans note) — voir §4.5 |
| conformepro.dz | DZA | agrégateur privé | Tarif intégré algérien | conformepro.dz | 2026-06-17 | inconnue | 17 061 positions | `PARTIAL` (le code cite en interne « PARTIAL/B », terminologie propre à l'adaptateur — statut canonique de ce rapport : `PARTIAL`) |
| Circulaire 482/2024 | DZA | DGD | Traitement tarifaire ZLECAf à l'importation | `douane.gov.dz/IMG/pdf/circulaire_no_482_dgd_du_22-10-2024_mise_en_oeuvre_zlecaf.pdf` (communiquée, non vérifiée) | tentée le 2026-07-27, non aboutie (HTTP 403 puis chaîne TLS incomplète côté serveur, non contournée) | 2024-10-22 (date du texte, contenu non vérifié) | inconnue | `SOURCE_BLOCKED` — aucune copie exploitable collectée ; ne prouve ni publication ni absence de publication ; ne déclenche aucun calcul préférentiel |

---

## 11. Limites de cet audit

- Aucune **collecte de nouvelle donnée pays** n'a été effectuée pendant
  cette révision, et aucun contournement de vérification TLS n'a eu lieu à
  aucun moment. Une seule tentative de **vérification d'une source déjà
  communiquée** a été menée (URL de la circulaire DZA 482/2024, voir §4.6) :
  un fetch applicatif standard (HTTP 403) puis une vérification directe
  (`openssl s_client`) ayant révélé une chaîne de certificat incomplète
  côté serveur — vérification TLS non contournée, aucune copie officielle
  collectée. Cette tentative n'a produit **aucune nouvelle donnée ingérée**
  dans les comptages ou statuts de ce rapport.
- Le statut `SOURCE_PENDING_COLLECTION` (ZAF, Schedule 1 Part 1) et
  `SOURCE_BLOCKED` (offre KEN ; circulaire DZA 482/2024, dont l'unique
  tentative de vérification est documentée en §4.6) reflètent l'état
  documenté dans le dépôt et le résultat de cette tentative — aucune
  collecte de contenu nouveau n'en résulte.
- L'hypothèse retenue pour MAR (suffixe `00` = notation ADIL native) est
  la mieux étayée par les preuves disponibles (absence de marqueurs de
  fabrication, code source du crawler, coexistence intra-en-tête), mais
  reste une **inférence**, non une confirmation par documentation ADIL
  explicite sur la sémantique du suffixe.
- Pour TUN, l'audit ne permet pas de distinguer, à l'intérieur de la
  colonne `preferences`, les taux relevant de la ZLECAf de ceux relevant de
  GAFTA ou d'accords bilatéraux — seule une recherche documentaire
  complémentaire (hors périmètre ici) pourrait trancher.
- `engine/output/*_summary.json` et `frontend/public/data/DATA_STATUS.json`
  n'ont pas été réaudités dans cette révision (déjà signalés comme
  gabarit HS6 dupliqué dans l'audit consolidé antérieur, et confirmés hors
  du chemin de chargement runtime du calculateur — voir §2.1).
- Aucun test automatisé n'a été exécuté (interdiction explicite de modifier
  tests/calculateur/moteur dans cette vague) ; les comptages ci-dessus sont
  reproductibles indépendamment via les commandes Python fournies.

---

## 12. Empreinte Git auditée

```
$ git branch --show-current
claude/official-data-wave-01

$ git rev-parse origin/main
1be67b6da14e0a03c731ab3d82b23b4180107bb6

$ git log --oneline origin/main..HEAD
7b337bb4 docs(audit): document official-data wave 01 findings
940cd33b docs(wave01): audit factuel des 6 pays pilotes ZAF/KEN/TUN/MAR/EGY/DZA
```

Ce fichier est le seul modifié par les deux commits de la branche :
`940cd33b` (première version de l'audit) et `7b337bb4` (validation
contradictoire et corrections). **Avertissement de fragilité** : ces SHA
identifient l'état de la branche `claude/official-data-wave-01`, pas
l'historique final de `main`. La PR associée (#319) doit être fusionnée
exclusivement par *Squash and merge* — après fusion, aucun de ces deux SHA
n'existera dans `main` ; c'est le SHA du commit de squash qui fera foi.
Pour retrouver l'état exact ayant produit ce document, se référer à la PR
GitHub elle-même plutôt qu'à ces empreintes de branche.

---

**Rappel de portée** : ce document est un audit d'un outil d'information et
de simulation, non juridique et non opposable à l'administration douanière
(§0). Il ne constitue ni une certification juridique des taux ZLECAf, ni
une autorisation d'ajouter un pays à `SUPPORTED_JURISDICTIONS` ou
`NATIONAL_OFFER_REGISTRY`. Toute préférence ZLECAf pour les 6 pays pilotes
reste, à l'issue de cet audit :
- `NOT_AVAILABLE`, pour la composante ZLECAf de KEN et DZA (texte générique
  sans origine par ligne identifiable — interdit, à exclure du flux actif) ;
- `PARTIAL`, pour ZAF, TUN, et le sous-ensemble EGY à note AfCFTA confirmée
  (6 417/8 746 lignes — origine identifiable, chaîne reproductible
  démontrée empiriquement §4.5, certification juridique incomplète,
  affichable à titre informatif) ;
- `UNVERIFIED`, pour le sous-ensemble EGY sans note AfCFTA (2 276/8 746
  lignes — mécanisme identifiable mais `zlecaf_source` discriminant non
  persisté, ambiguïté entre préférence réelle et copie du DD) ;
- `NOT_AVAILABLE`, pour MAR (aucun champ ZLECAf présent — rien à afficher).

Aucune n'est `DOCUMENTED` ni appliquée par défaut comme réduction opposable.

**Principe d'interdiction** : toute donnée simulée, inventée, extrapolée,
mockée, artificiellement générée ou dont l'origine n'est pas identifiable
est strictement interdite dans le SaaS, sous quelque forme que ce soit.

Toute simulation produite à partir de ces données doit porter la mention :
> « Simulation informative — non opposable à l'administration douanière.
> Vérifiez les taux, conditions préférentielles et formalités auprès des
> autorités compétentes avant toute opération. »
