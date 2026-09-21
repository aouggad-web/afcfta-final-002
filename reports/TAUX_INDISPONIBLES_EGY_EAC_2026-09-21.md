# 394 taxes dont le taux ne se liquide pas — Égypte et les sept du TEC

> Constat mesuré le 21/09/2026 sur les crawls versionnés. **Aucune donnée n'est
> modifiée par ce document.** Il nomme deux lacunes de couverture et établit ce
> qu'il faudrait pour les combler — y compris un piège qui doublerait une taxe
> si on les comblait sans le voir.
>
> Classement **G2** : le produit **cache du vrai**. Le taux existe et n'atteint
> pas le moteur. Ce n'est pas un G1 : aucun chemin de service ne fabrique de
> valeur à leur place — vérifié au §4.

---

## 1. Ce que la mesure donne

| | Taxes à `rate: null` | Positions | Cause |
|---|---|---|---|
| **Égypte** | **58** | 40 sur 8 818 | droits spécifiques et planchers non structurés |
| **Kenya, Tanzanie, Ouganda, Rwanda, Burundi, RD Congo, Soudan du Sud** | **48 chacun — 336** | 48 par pays | produits sensibles du TEC, taux renvoyé au barème national |
| **Total** | **394** | | |

Les deux familles n'ont rien à voir l'une avec l'autre et ne se comblent pas
par le même travail.

---

## 2. Égypte — 58 taxes, deux natures qu'il faut distinguer

### 2.1 Ce que la source publie

La collecte est **fidèle** : la mention imprimée est conservée intacte dans
`raw`. C'est la **conversion** qui manque.

| Taxe | Occurrences | Mention publiée | Lecture |
|---|---|---|---|
| `ID` droit d'importation | 23 | `9 جنية لكل كيلو جرام صافى` | 9 £E par kg net |
| `VAT_2` | 16 | `بحد ادنى 60 جنية لكل كيلو جرام صافى` | **minimum** 60 £E par kg net |
| `VAT` | 12 | `0.48 جنية لكل لتر` | 0,48 £E par litre |
| `ضريبة الجدول` taxe de barème | 3 | `15 جنية لكل لتر سائل` | 15 £E par litre de liquide |
| `ضريبة الجدول_2` | 2 | `بحد ادنى 15 جنية لكل لتر سائل` | **minimum** 15 £E par litre |
| `تامين صحى وزارة الصحة` assurance santé | 2 | `0.1 جنية لكل عشرون سيجارة` | 0,1 £E par vingt cigarettes |

Concentration par chapitre : **24 tabacs (41)**, **27 combustibles minéraux
(12)**, 22 boissons alcooliques (3), 21 préparations alimentaires (1), 33
parfumerie (1).

### 2.2 LE PIÈGE — dix-huit de ces cinquante-huit ne sont pas des taxes

Sur `2401100010`, les deux entrées vont ensemble :

```
VAT    = 75 %   « 75% (من القيمة + ر.ض.جمركية) »
VAT_2  = null   « بحد ادنى 60 جنية لكل كيلو جرام صافى »   ← « avec un MINIMUM de 60 £E/kg »
```

`VAT_2` **n'est pas une taxe distincte : c'est le plancher de la `VAT` qui la
précède.** Le suffixe `_2` marque cette relation, et la correspondance est
**exacte, sans exception** :

```
code en _2   ET mention « بحد ادنى » (minimum)   18
code en _2   SANS mention de minimum              0
code de base AVEC mention de minimum              0
code de base SANS mention de minimum             40
```

**Conséquence pour qui voudra combler cette lacune :** structurer les 18
entrées `_2` comme des taxes séparées créerait dix-huit lignes fantômes qui
s'ajouteraient à la taxe dont elles sont le plancher. Le montant serait
**doublé**, et il aurait l'air plus complet qu'avant. C'est pire que la lacune.

Il reste donc **40 droits spécifiques** à structurer, et **18 planchers** à
rattacher à leur taxe — deux travaux, pas un.

### 2.3 Ce que le moteur saurait en faire

Le moteur liquide déjà les droits spécifiques : il attend
`{"montant": …, "brut": "…", "unite_quantite": "…"}` et une devise. `EGP` est
enregistré dans `backend/socle/devises_pays.json`. La grammaire existe, la
donnée n'y est pas.

**Ce qui n'est pas établi, et qu'aucune mesure ne donnera :** le `ID`
spécifique (`9 £E/kg` sur les tabacs) **remplace-t-il** l'ad valorem ou
**s'y ajoute-t-il** ? Sur les 23 positions concernées, aucune ne porte de
pourcentage en `ID`, ce qui suggère le remplacement — mais une absence n'est
pas une règle. Cela demande le tarif officiel égyptien, article par article.

### 2.4 Assiettes non établies, en plus des taux

Indépendamment des taux, trois taxes nommées égyptiennes rendent
`ASSIETTE_INDISPONIBLE` au moteur : la taxe de barème, l'assurance santé du
ministère de la Santé, et le prélèvement pour la chambre du tabac. Même avec
leurs taux, elles ne se liquideraient pas.

---

## 3. Les sept pays du TEC — 336 taxes, et une lacune honnête

Les 48 entrées sont **identiques dans les sept pays**, au code et au chapitre
près :

```
{"tax_name": "CET Import Duty (Sensitive Item)",
 "rate": null,
 "base": "CIF",
 "is_cet": true,
 "note": "Rate determined by national schedule"}
```

Chapitres : **04** produits laitiers, **10** céréales, **11** produits de la
minoterie, **17** sucres, **52** coton, **55** fibres synthétiques, **62** et
**63** vêtements et articles textiles — la liste des produits sensibles du
tarif extérieur commun.

**Cette lacune-là est correctement déclarée.** Le collecteur ne devine pas : il
dit que le taux relève du barème national de chaque pays, et laisse `null`. Le
travail n'est pas de réparer un parseur, c'est de **collecter sept barèmes
nationaux** — sept sources, sept vérifications.

Que les 48 soient identiques partout signifie aussi que la liste sensible a été
appliquée uniformément : elle est à re-vérifier pays par pays, la composition
pouvant différer (la RD Congo et le Soudan du Sud ont rejoint l'union
douanière plus tard que les autres).

---

## 4. Pourquoi c'est un G2 et non un G1

Vérifié le 21/09/2026 sur `EGY / 2401100010`, les trois chemins de service :

| Chemin | Ce qu'il rend | Verdict |
|---|---|---|
| `/calcul` — socle, chemin principal | `PARTIEL` · `DD : TAUX_INDISPONIBLE` · aucun montant | correct |
| `/authentic-tariffs/calculate` — celui que le frontend appelle | `CALCULATION_UNAVAILABLE` : « Taux absents ou **droits spécifiques** : calcul complet indisponible », avec `missing_or_non_ad_valorem_taxes` | correct, et il nomme la cause |
| `enhanced_calculator_service` — `/calculate/detailed`, `/enhanced-calculator/*` | ramenait le taux absent à `0 %` | **défectueux — corrigé par la PR #497** |

Le frontend n'appelle aucun des trois chemins du service défectueux (vérifié :
zéro occurrence de `calculate/detailed`, `tariffs/detailed`,
`enhanced-calculator` dans `frontend/src`). **Aucun montant fabriqué n'a donc
été servi par l'application** ; le défaut était réel sur trois points d'API
publics, et dormant.

C'est la raison du classement : le produit ne dit pas de faux, il se taît sur
un droit qui existe. **G2 — le produit cache du vrai.**

---

## 5. Ce qu'il faudrait, dans l'ordre du coût croissant

1. **Rattacher les 18 planchers à leur taxe** — aucune source nouvelle n'est
   nécessaire, la relation est établie ci-dessus et vérifiable dans le crawl.
   C'est le geste qui empêche une future collecte de doubler la taxe.
2. **Structurer les 40 droits spécifiques égyptiens** en `{montant, unité,
   devise}`. Les nombres sont imprimés, donc lisibles sans invention ; mais
   l'articulation avec l'ad valorem (§2.3) demande le tarif officiel.
3. **Établir l'assiette des trois taxes nommées égyptiennes** (§2.4), sur le
   code des douanes ou la loi fiscale, avec extrait archivé et empreinte.
4. **Collecter les sept barèmes nationaux du TEC** pour les produits
   sensibles — le travail le plus lourd, et celui qui ne se déduit d'aucune
   règle commune.

Rien de tout cela ne se comble en devinant. Un droit spécifique dont on ignore
l'unité, une assiette qu'on suppose, un barème national qu'on remplace par le
TEC : chacun produirait un montant faux, et les trois auraient l'air complets.
