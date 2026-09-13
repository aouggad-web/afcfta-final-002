# Pourquoi le calculateur a deux moteurs

**Question posée :** si l'on dispose d'un tarif avec des sous-positions
nationales portant droits, taxes, formalités et réglementation, pourquoi ces
complications ?

**Réponse courte :** parce que cette prémisse n'est vraie pour aucun des 53 pays
mesurés. La complication ne vient pas du calcul, elle vient de ce que les
fichiers tarifaires du dépôt sont sept structures de données différentes portant
le même nom.

Mesure du 13 septembre 2026 sur les 53 fichiers de `backend/data/crawled/`.

## 1. Le test de la prémisse : 0 pays sur 53

Cinq critères testés par pays : sous-positions nationales (codes de plus de six
chiffres), droit de douane, TVA, formalités par ligne, réglementation par ligne.

**Aucun pays ne satisfait les cinq**, et la raison est structurelle plutôt que
statistique : **aucun fichier ne porte à la fois les formalités et la
réglementation par ligne**. L'Algérie et le Maroc ont les formalités sans la
réglementation ; la Tunisie a la réglementation sans les formalités. Ce constat
ne dépend pas de la détection des taxes, contrairement au décompte détaillé des
critères, volontairement écarté ici (voir la section 7).

| Critère | Réalité mesurée |
|---|---|
| Sous-positions nationales | **33 pays** en ont ; **13 pays n'en ont aucune** (moyenne NPF WITS au SH6 seulement) ; **5 pays SACU** mélangent codes à 6 et à 8 chiffres dans le même fichier |
| Formalités par ligne | **2 pays** : Algérie et Maroc (100 %). Égypte à 5 %. Les 48 autres n'en portent aucune |
| Réglementation par ligne | **1 pays** : Tunisie |
| Fichiers vides | Djibouti, Érythrée |

## 2. Sept façons d'écrire « droit de douane »

C'est le cœur du problème. Le même concept, dans le même dépôt, au même niveau
de nomenclature :

| Pays | Où se lit le droit | Forme du taux |
|---|---|---|
| Algérie, Égypte et 33 autres | `taxes` indexé par code — `taxes.DD.rate` | nombre : `5.0` |
| Maroc | `taxes` indexé par **libellé français** — `taxes["Droit d'Importation (DI)"]` | chaîne : `'2.5 %'` |
| Afrique du Sud, SACU, Nigeria | `taxes[]` liste, entrées à `code` | `rate_pct: null` + `specific_value: "8c/kg"` |
| Tunisie | `taxes_import[]` liste | `rate_pct` + `assiette: "SOMME D.T (G=0.1.2.3.4."` |
| Kenya et les 6 autres pays EAC | `taxes_detail[]` liste, entrées à `tax_name` | `rate` + `base: "CIF+Duty+Fees"` |
| Ghana | champ direct `dd`, aucune collection de taxes | nombre : `10.0` |

À quoi s'ajoutent quatre conteneurs de positions distincts : `sub_positions[]`
(18 fichiers), `positions[]` (28), les deux (6), et
`tariff_lines[].sub_positions[]` (1).

Les libellés eux-mêmes ne sont pas homogènes : l'Égypte nomme ses taxes en arabe
(`رسم محصلة لحساب غرفة دخان`), le Maroc en français, l'EAC en anglais. Les
assiettes sont du texte libre non normalisé : `"VAL.DOU(D)+R(DT) GR.0"`,
`"SOMME D.T"`, `"CIF+Duty+Fees"`, `"CIF"`.

## 3. Pourquoi cela produit deux moteurs

Personne n'écrit un lecteur correct pour cela en une seule fois.

La rédaction de cette note en est la démonstration. Trois versions de la sonde de
mesure ont été nécessaires :

1. La première rapportait « 0 % de formalités partout » — mauvaise clé : le champ
   est `formalities`, pas `administrative_formalities`.
2. La deuxième rapportait « aucun droit au Ghana, au Kenya, au Maroc » — elle ne
   gérait ni le champ direct `dd`, ni l'indexation par libellé.
3. La troisième manquait encore les sept pays de l'EAC — `taxes_detail` avait
   échappé aux deux premières.

Un développeur devant la même donnée fait la même chose, à ceci près qu'il livre
entre deux itérations. C'est l'origine des deux moteurs :

- **`POST /calculate-tariff` est le moteur d'origine.** Il lit une couche
  *normalisée*, c'est-à-dire aplatie de force vers un schéma unique. Cela
  fonctionne pour les 35 pays en `taxes` indexé par code, et détruit de
  l'information pour les autres : le Ghana y perd ses 6 129 codes nationaux,
  réduits à 5 387 lignes SH6.
- **`GET /authentic-tariffs/calculate/...` a été ajouté ensuite** pour les pays où
  cette perte était inacceptable — Algérie, Tunisie, Égypte, avec leurs vraies
  sous-positions et leurs vraies assiettes.
- **Le premier n'a jamais été retiré.** Le frontend enchaîne les deux
  (`frontend/src/components/calculator/CalculatorTab.jsx:415`) :

```js
try   { GET /authentic-tariffs/calculate/... }   // le moteur récent
catch { POST /calculate-tariff }                 // l'ancien, en repli
```

Le défaut de conception est là : **le `catch` est silencieux**. Le second chemin
n'est pas un repli de secours, c'est un second calculateur, avec ses propres
données, ses propres assiettes et ses propres réponses. Selon celui qui répond,
l'utilisateur voit 195 ou 300 sur la même position égyptienne.

## 4. Le vrai coupable : deux sources, pas deux moteurs

Avec un moteur unique, le défaut égyptien subsisterait, parce que la
contradiction est en amont du calcul :

| Fichier | Valeur pour EGY `0207110000` |
|---|---|
| `backend/data/EGY_tariffs.json` (canonique) | `dd: 19.5` |
| `backend/data/crawled/EGY_tariffs.json` (crawl récent) | `taxes.ID.rate: 30.0` |

Deux fichiers, deux valeurs, **aucune règle écrite désignant celle qui prime**.
Le moteur prioritaire lit le canonique périmé, le POST lit le crawl. Chacun est
cohérent avec sa source ; le système n'est cohérent avec rien.

C'est pourquoi la phase 1 du plan de correction s'appelle *résolution de données
unique* et passe avant l'unification des moteurs.

## 5. La distinction qui décide du plan

**Complexité irréductible.** Sept représentations fiscales, des droits aux
centimes par kilogramme, des assiettes en texte libre, des libellés en trois
langues. C'est la réalité de 54 administrations douanières ; elle ne disparaîtra
pas. Elle doit être absorbée **une seule fois, à l'entrée**, par un résolveur qui
connaît les sept schémas et rend un objet unique portant sa provenance.

**Complexité accidentelle.** Deux moteurs, deux politiques de priorité, un repli
silencieux, une couche dérivée de 2 Go régénérée au hasard, des unités
contradictoires entre les deux API — pourcentage d'un côté, fraction de l'autre.
C'est de la dette technique, pas de la douane, et c'est ce que le plan supprime.

Une fois la première absorbée, un seul calculateur suffit : il n'a plus besoin de
savoir que le Maroc indexe ses taxes par libellé ni que l'Afrique du Sud facture
au centime par kilogramme.

## 6. Ce que la prémisse deviendra

La prémisse de départ n'est pas fausse, elle est **prématurée**. Le jour où les
54 pays porteront sous-positions, droits, taxes, formalités et réglementation
dans un schéma unique, un calculateur simple suffira — et la question ne se
posera plus. Aujourd'hui deux pays sur 54 ont leurs formalités par ligne.

Combler cet écart est un travail de collecte de données (phase 5 du plan), pas un
travail sur le calculateur. Les deux pistes ont des calendriers distincts, et
aucune ne doit attendre l'autre.

## 7. Mesure par pays

Colonnes retenues : celles que la sonde lit de façon fiable. **Les colonnes
« droit » et « TVA » ont été volontairement retirées** : leur détection dépend du
schéma de taxes propre à chaque pays, et c'est précisément ce que cette note
démontre — un comptage uniforme y produit des faux négatifs. Le schéma est donné
en dernière colonne à la place.

« Sous-pos. nat. » = part des positions échantillonnées portant un code de plus
de six chiffres. « Formalités » et « Réglementation » = part des positions
portant un contenu non vide. Échantillon de 400 positions par fichier : la mesure
établit le cas dominant, pas les cas rares — les 48 restrictions par pays EAC
signalées par l'audit, par exemple, ne ressortent pas d'un tel échantillon.

| Pays | Lignes | Sous-pos. nat. | Formalités | Réglementation | Schéma des taxes |
|---|---:|---|---|---|---|
| AGO | 5388 | aucune | — | — | `taxes` indexé par code |
| BDI | 5984 | 100 % | — | — | `taxes_detail[]` liste |
| BEN | 6129 | 100 % | — | — | `taxes` indexé par code |
| BFA | 6129 | 100 % | — | — | `taxes` indexé par code |
| BWA | 8589 | 40 % | — | — | `taxes[]` liste |
| CAF | 5239 | 100 % | — | — | `taxes` indexé par code |
| CIV | 6129 | 100 % | — | — | `taxes` indexé par code |
| CMR | 5239 | 100 % | — | — | `taxes` indexé par code |
| COD | 5984 | 100 % | — | — | `taxes_detail[]` liste |
| COG | 5239 | 100 % | — | — | `taxes` indexé par code |
| COM | 5388 | aucune | — | — | `taxes` indexé par code |
| CPV | 6129 | 100 % | — | — | `taxes` indexé par code |
| DJI | 0 | — | — | — | fichier vide |
| DZA | 17226 | 100 % | 100 % | — | `taxes` indexé par code |
| EGY | 8818 | 100 % | 5 % | — | `taxes` indexé par code |
| ERI | 0 | — | — | — | fichier vide |
| ETH | 6296 | 100 % | — | — | `taxes` indexé par code |
| GAB | 5239 | 100 % | — | — | `taxes` indexé par code |
| GHA | 6129 | 100 % | — | — | champ direct `dd` |
| GIN | 6129 | 100 % | — | — | `taxes` indexé par code |
| GMB | 6129 | 100 % | — | — | `taxes` indexé par code |
| GNB | 6129 | 100 % | — | — | `taxes` indexé par code |
| GNQ | 5239 | 100 % | — | — | `taxes` indexé par code |
| KEN | 5984 | 100 % | — | — | `taxes_detail[]` liste |
| LBR | 6129 | 100 % | — | — | `taxes` indexé par code |
| LBY | 5388 | aucune | — | — | `taxes` indexé par code |
| LSO | 8589 | 40 % | — | — | `taxes[]` liste |
| MAR | 13114 | 100 % | 100 % | — | `taxes` indexé par libellé FR |
| MDG | 5624 | aucune | — | — | `taxes` indexé par code |
| MLI | 6129 | 100 % | — | — | `taxes` indexé par code |
| MOZ | 5388 | aucune | — | — | `taxes` indexé par code |
| MRT | 5388 | aucune | — | — | `taxes` indexé par code |
| MUS | 5619 | aucune | — | — | `taxes` indexé par code |
| MWI | 5388 | aucune | — | — | `taxes` indexé par code |
| NAM | 8589 | 40 % | — | — | `taxes[]` liste |
| NER | 6129 | 100 % | — | — | `taxes` indexé par code |
| NGA | 6363 | 100 % | — | — | `taxes[]` liste |
| RWA | 5984 | 100 % | — | — | `taxes_detail[]` liste |
| SDN | 5388 | aucune | — | — | `taxes` indexé par code |
| SEN | 6129 | 100 % | — | — | `taxes` indexé par code |
| SLE | 6129 | 100 % | — | — | `taxes` indexé par code |
| SSD | 5984 | 100 % | — | — | `taxes_detail[]` liste |
| STP | 5388 | aucune | — | — | `taxes` indexé par code |
| SWZ | 8589 | 40 % | — | — | `taxes[]` liste |
| SYC | 5396 | aucune | — | — | `taxes` indexé par code |
| TCD | 5239 | 100 % | — | — | `taxes` indexé par code |
| TGO | 6129 | 100 % | — | — | `taxes` indexé par code |
| TUN | 17542 | 100 % | — | 100 % | `taxes_import[]` liste |
| TZA | 5984 | 100 % | — | — | `taxes_detail[]` liste |
| UGA | 5984 | 100 % | — | — | `taxes_detail[]` liste |
| ZAF | 8589 | 40 % | — | — | `taxes[]` liste |
| ZMB | 5613 | aucune | — | — | `taxes` indexé par code |
| ZWE | 5388 | aucune | — | — | `taxes` indexé par code |

## Portée

Cette note décrit les fichiers versionnés au 13 septembre 2026. Elle ne dit rien
du contenu de PostgreSQL en production, ni de l'exactitude juridique des taux :
un fichier bien structuré peut porter un taux périmé, et un fichier mal structuré
un taux exact. Les deux questions sont distinctes et traitées séparément dans
`docs/PLAN_CORRECTION_CALCULATEUR_2026-09.md`.

Documents liés :

- `docs/PLAN_CORRECTION_CALCULATEUR_2026-09.md` — plan de correction en six phases
- `docs/MESURE_REFERENCE_CALCULATEUR_2026-09-13.md` — 318 divergences sur 320 positions
- `docs/DECISION_INDISPONIBILITE_CALCULATEUR.md` — politique d'indisponibilité, en attente d'arbitrage
- `backend/tests/fixtures/calculator_golden.json` — corpus figé des dix cas de l'audit
