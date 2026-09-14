# Assiettes et méthodes de calcul — état des lieux

**Constat bloquant : le dépôt détient deux descriptions de l'assiette, elles ne
s'accordent pas, et le moteur n'en lit qu'une.**

Ce document consigne ce que mesure `scripts/inventory_tax_bases.py`, dont le
rapport est versionné dans `reports/ASSIETTES_ET_METHODES.json`.

## Pourquoi l'assiette n'est pas un détail

Une taxe n'est pas un taux : c'est un taux **et** une assiette. Servir 18 % de
TVA sans savoir si l'assiette est `CIF`, `CIF + DD` ou `CIF + DD + RS + PCS`,
c'est fabriquer un montant — exactement ce que la doctrine de ce dépôt interdit.

Et ce qui compte n'est pas de quelle administration relève le prélèvement. Droit
de douane, droits connexes, taxes à effet équivalent, taxes intérieures et
accises perçues à l'occasion du dédouanement : tout ce que l'opérateur paie au
passage en douane entre dans le coût, pourvu que la source le publie et que la
provenance soit tracée.

## Les deux sources de vérité

| | Où | Qui la lit |
|---|---|---|
| **Assiette publiée** | champ `base` des fichiers `backend/data/crawled/*_tariffs.json` | personne |
| **Table codée** | `COUNTRY_TAX_PROFILES` dans `authentic_tariff_service.py`, 37 pays | `compute_tax_cascade()`, seule |

Le moteur applique la table. Là où elle diverge de la source, le montant servi
est faux.

## Ce que les sources publient réellement

Seize expressions d'assiette distinctes. Pour la TVA, le CIF seul est
l'exception :

| Assiette de la TVA publiée par la source | Pays |
|---|---|
| `CIF + DD + RS + PCS` | 11 — CEDEAO / UEMOA |
| `CIF + DD + TCI` | 6 — CEMAC |
| `CIF + Duty` | 5 — EAC |
| `CIF + Duty + Fees` | Kenya |
| `CIF + Duty + Levies` | Ouganda |
| `VAL.DOU(D)+R(DT) GR.0` | Tunisie |
| `CIF` seul | Côte d'Ivoire |

## Les quinze désaccords

```
BEN BFA CPV GMB GNB LBR MLI NER SEN SLE TGO   TVA   source CIF+DD+RS+PCS   table CIF+DD
KEN                                           TVA   source CIF+DD+Fees     table CIF+DD
UGA                                           TVA   source CIF+DD+Levies   table CIF+DD
TUN                                           TVA   source VAL.DOU+R(DT)   table CIF+DD
CIV                                           TVA   source CIF             table CIF+DD
```

**L'erreur va dans les deux sens**, ce qui exclut toute correction par
coefficient. Sur une opération à 10 000 de CIF :

| | Écart | En part du CIF |
|---|---:|---:|
| Bénin — TVA sous-évaluée (la table omet RS et PCS) | 36,00 | 0,36 % |
| Côte d'Ivoire — TVA sur-évaluée (la table ajoute un DD absent de la source) | 360,00 | 3,60 % |

**14 pays n'ont aucun profil codé** et tombent sur le défaut du moteur — « TVA
sur CIF + DD » — qui est faux pour toute la CEDEAO.

## Les assiettes qui ne sont pas des valeurs

Treize couples pays/taxe portent une assiette non valorielle. Les fondre dans la
cascade produirait des montants faux :

- **quantitatives** — `PN (KG)`, `QCS`, `PN(KG)/100 EXCES` : onze taxes
  tunisiennes, assises sur un poids ou une quantité, pas sur une valeur ;
- **plafonnées** — `CIF (plafond 15 000 XAF)` : la redevance informatique
  camerounaise et équato-guinéenne.

## État de la connaissance, sur 247 couples pays/taxe

| Statut | Couples |
|---|---:|
| `lue_dans_la_source` | 158 |
| `table_codee_seule` | 34 |
| `non_documentee` | 55 |

`non_documentee` dit que le dépôt ignore l'assiette, **pas** qu'elle n'existe
pas : beaucoup d'administrations ne répètent pas dans leur nomenclature une
convention qu'elles publient ailleurs.

## Premier désaccord tranché : l'UEMOA, sur source primaire

**Directive n° 02/98/CM/UEMOA du 22 décembre 1998, article 27 a), deuxième
tiret** — texte OCRisé et archivé, fiche
`backend/data/legal_refs/zlecaf_application/UEMOA_assiette_TVA_2026-09-14.json` :

> « en ce qui concerne les importations par la **valeur en douane majorée des
> droits et taxes perçus à l'entrée, à l'exception de la Taxe sur la Valeur
> Ajoutée elle-même**. »

L'assiette est donc la valeur en douane **augmentée de tous les droits et taxes
d'entrée, sans énumération limitative**, la TVA seule étant exclue de sa propre
assiette. Huit États sont liés : Bénin, Burkina Faso, Côte d'Ivoire,
Guinée-Bissau, Mali, Niger, Sénégal, Togo.

**Les deux descriptions du dépôt sont fausses, à des degrés différents.** La
table codée applique `CIF + DD` et ampute l'assiette de toutes les autres taxes.
Le champ `base` des fichiers déclare `CIF + DD + RS + PCS` : incomplet lui aussi,
il omet PCC et PUA (Bénin, Guinée-Bissau, Sénégal, Togo) ou PCAES (Burkina Faso,
Mali, Niger).

Bénin, CIF 10 000, DD 20 %, RS 1 %, PCS 1 %, PCC 0,5 %, PUA 0,2 %, TVA 18 % :

| Lecture | Assiette | TVA | Écart |
|---|---:|---:|---:|
| Table codée du moteur | 12 000,00 | 2 160,00 | −48,60 |
| Champ `base` du fichier | 12 200,00 | 2 196,00 | −12,60 |
| **Directive art. 27 a)** | **12 270,00** | **2 208,60** | — |

**Le cas ivoirien est élucidé, et l'hypothèse était la bonne.** Le fichier
déclare `CIF` seul et ne porte ni RS, ni PCS, ni PUA dans ses données — ces trois
taxes ne figurent que dans une note en prose du fichier lui-même : « Les taxes
PCS (0,8 %), PUA (0,2 %) et RS (1 %) s'appliquent à toutes les importations ».
L'assiette déclarée est donc cohérente avec une **collecte incomplète**, pas avec
une règle nationale distincte. La Côte d'Ivoire suit la même règle que ses sept
partenaires ; c'est le crawl qu'il faut compléter.

**Portée à ne pas dépasser.** Cap-Vert, Gambie, Liberia et Sierra Leone figurent
dans les quinze désaccords mais sont membres de la CEDEAO **sans** être membres
de l'UEMOA : cette directive ne les lie pas, et leur assiette relève d'un
fondement qui reste à établir. Leur appliquer l'article 27 serait étendre une
règle au-delà de sa portée.

## Deuxième et troisième désaccords : le Kenya et l'Ouganda

Fiche `EAC_assiette_TVA_2026-09-14.json`, extraits archivés.

**Kenya — VAT Act No. 35 of 2013, section 14 (1)** : l'assiette est la valeur en
douane, plus le fret et l'assurance non déjà inclus, plus « *the amount of duty
of customs* ».

**Un piège de lecture s'y cache, et j'ai failli y tomber.** Lu seul, l'alinéa (c)
se comprend comme le seul droit de douane, et conduirait à conclure `CIF + DD` —
donnant raison à la table codée. C'est la **définition** de l'expression,
ailleurs dans la loi, qui renverse le sens :

> « *duty of customs* » means import duty, excise duty, export duty,
> countervailing duty, **levy, cess, tax or surtax** charged under any law for the
> time being in force relating to customs or excise.

**Ouganda — VAT Act, Chapter 349, section 23** : « *the amount of customs duty,
excise tax and **any other fiscal charge other than tax** payable on those
goods* », « tax » désignant la TVA elle-même.

Les deux lois élargissent donc l'assiette bien au-delà du droit de douane. La
table codée, qui applique `CIF + DD`, est fausse pour les deux pays. Le champ
`base` — `CIF+Duty+Fees` et `CIF+Duty+Levies` — va dans le bon sens mais reste
plus étroit que les textes, qui ne limitent pas : l'accise n'y figure pas.

Burundi, Rwanda et Tanzanie déclarent `CIF+Duty` et s'accordaient avec la table :
ils n'étaient pas en désaccord, leurs lois n'ont pas été lues, et cette
détermination ne leur est pas étendue.

## Les quatre CEDEAO non-UEMOA : un constat d'une autre nature

Fiche `ECOWAS_derives_BEN_2026-09-14.json`.

En cherchant le fondement de leur assiette, j'ai trouvé autre chose. **Les
fichiers du Cap-Vert, de la Gambie, du Liberia et de la Sierra Leone ne sont pas
des collectes nationales** : ils portent `derived_from: "BEN"` et se déclarent
« réf. État membre BEN ». Mesuré : 6 129 positions chacun, les mêmes codes que le
Bénin, **droit de douane identique sur 6 129 positions sur 6 129**. Seul le taux
de TVA national est substitué.

**Cette déclaration est honnête** — rien n'est dissimulé, et le raisonnement est
défendable pour le droit de douane : le Tarif Extérieur Commun est réellement
commun aux quinze États de la CEDEAO, le PCC à 0,5 % également.

**Mais la dérivation va trop loin sur deux prélèvements.** La note de ces fichiers
affirme que les « prélèvements communautaires » sont identiques entre États
membres. Le **PCS** (Prélèvement Communautaire de Solidarité) et le **PUA**
(Prélèvement UEMOA) sont des prélèvements de l'**UEMOA**. Ces quatre pays sont
membres de la CEDEAO mais **non de l'UEMOA** : ils ne les acquittent pas. Les
fichiers leur en attribuent pourtant 1,0 % et 0,2 %.

Sur 10 000 de CIF, ces quatre pays se voyaient facturer **120,00 de prélèvements
sans fondement** — 1,20 % du CIF — plus la TVA assise dessus.

**Corrigé.** Le PCS et le PUA sont retirés des quatre jeux : 12 258 entrées par
pays dans `taxes` et autant dans `taxes_detail`, soit **49 032 entrées** au
total. Sceaux refaits, empreintes propagées au manifeste, `verify_crawled_file`
valide sur les quatre. Cap-Vert, CIF 10 000 : le total des taxes passe de
4 070,00 à 3 950,00.

Les clés sont **retirées, non mises à zéro** — la distinction est la même que
celle de la note d'indisponibilité. Dans le schéma du dépôt une taxe absente est
`ABSENTE`, jamais nulle, et la doctrine interdit de réputer non due une taxe
qu'on ignore. Servir zéro aurait été la même faute que servir la valeur
béninoise, dans l'autre sens. Le droit de douane, la Redevance Statistique et le
PCC sont conservés : ils relèvent du TEC CEDEAO et s'appliquent bien aux quinze
États.

Leur assiette de TVA reste donc sans fondement établi : le champ `base` y est
l'expression béninoise, et la directive UEMOA ne les lie pas.

**Un indice supplémentaire, non tranché.** Le fichier béninois porte le PCS à
1,0 %, quand la note du fichier ivoirien écrit 0,8 % — le taux maintenu par le
20ᵉ sommet de l'UEMOA depuis 2017. Les deux ne peuvent être vrais ensemble. À
vérifier sur l'acte additionnel en vigueur.

## Le quinzième et dernier : la Tunisie

Fiche `TUN_assiette_TVA_2026-09-14.json`, extrait archivé.

**Code de la taxe sur la valeur ajoutée, article 6 § II-1** :

> « À l'importation, la valeur imposable est constituée : 1- s'il s'agit d'une
> importation réalisée par un assujetti [...] par la **valeur en douane, tous
> droits et taxes inclus à l'exclusion de la taxe sur la valeur ajoutée**. »

Même règle de fond qu'en UEMOA, au Kenya et en Ouganda, formulée autrement. La
table codée applique `CIF + DD` **en citant cet article même** : sa propre
référence la contredit.

### Décodage de l'encodage du Tarif Web

| Libellé publié | Lecture |
|---|---|
| `VALEUR DOUANE DINARS` | valeur en douane — droit de douane, droits de consommation ad valorem |
| `VAL.DOU(D)+R(DT) GR.0` | valeur en douane + droits et taxes du groupe 0 — assiette de la TVA |
| `SOMME D.T (G=0.1.2.3.4.` | somme des droits et taxes des groupes 0 à 4 — redevance de prestation douanière |
| `VAL DOUANE+ SOMME DT` | valeur en douane + somme des droits et taxes — taxe AIR |
| `QCS`, `QCI`, `PN (KG)` | quantités : assiettes spécifiques, aucune cascade ne s'y applique |

### Une règle que le calculateur ne peut pas servir

L'alinéa 2 du même article **majore de 25 % la valeur imposable** lorsque
l'importateur n'est pas assujetti. Le calculateur ne connaît pas la qualité de
l'importateur : à signaler, non à deviner.

### Deux défauts trouvés au passage

**`data/sources/TUN/tarifweb2026/tax_codes_and_assiettes.json` ne documente
rien.** Il se présente comme le « registre verbatim des codes de taxes et de
leurs assiettes », et le bloc `calculation_method` du tarif tunisien le cite
comme registre complet des 46 codes. Or **ses 46 entrées portent une charge
rigoureusement identique** : mêmes assiettes, même libellé `.PREST.DOUA/EXP`,
même cotation « export », mêmes 17 500 lignes. L'agrégation par code a échoué et
répété un agrégat global.

La donnée tarifaire, elle, est saine : le dépouillement direct rend **36 codes à
l'importation avec des assiettes variées**. Seul le registre récapitulatif est
faux.

**La base légale citée ne porte pas l'assiette.** Le bloc `calculation_method`
cite `CD_12.pdf` comme fondement des assiettes. Ce PDF fait une page et ne
contient que l'article 297, qui charge la douane de recouvrer les taxes
intérieures exigibles à l'importation. C'est une base pertinente pour le
*périmètre* des taxes perçues au dédouanement — et elle conforte le critère
retenu pour cet inventaire — mais elle ne dit rien de l'assiette.

## Les quinze désaccords, tranchés

| Fondement | Pays | Verdict |
|---|---|---|
| Directive UEMOA art. 27 a) | BEN BFA CIV GNB MLI NER SEN TGO | table **et** champ `base` trop étroits |
| Kenya VAT Act s. 14 + définition | KEN | table fausse ; `base` trop étroit |
| Ouganda VAT Act s. 23 | UGA | idem |
| Code TVA tunisien art. 6 § II-1 | TUN | table fausse, en citant l'article qui la contredit |
| Constat de dérivation | CPV GMB LBR SLE | jeux transposés du Bénin ; PCS et PUA retirés |

**Les quatre textes disent la même chose** : la valeur en douane augmentée de
tous les droits et taxes perçus à l'entrée, la TVA seule exclue de sa propre
assiette. Aucun ne se limite au droit de douane, et la table codée s'y limite
partout.

## Ce qui reste à trancher

Aucun des quinze désaccords n'est résolu ici, et le rapport n'en tranche aucun.
Deux lectures restent ouvertes, à départager **pays par pays** :

1. la table codée est périmée et la source fait foi — la cohérence par bloc
   régional plaide fortement en ce sens ;
2. certaines entrées de la table encodent une règle réelle que le champ `base`
   du crawl résume mal — auquel cas c'est le crawl qu'il faut creuser.

Le cas ivoirien **a été tranché** sur source primaire, voir la section
précédente : collecte incomplète, non règle nationale.

**Les quinze désaccords sont qualifiés.** Ce qui reste n'est plus du diagnostic
mais de la mise en œuvre et des questions neuves :

1. **Faire lire au moteur l'assiette réelle.** `compute_tax_cascade()` applique
   toujours `COUNTRY_TAX_PROFILES`, qui est faux partout où un texte a été lu.
   Aucune correction n'a encore été appliquée au calcul.
2. Établir les lois de TVA du Cap-Vert, de la Gambie, du Liberia et de la Sierra
   Leone, seuls pays sans fondement établi.
3. Trancher le taux du PCS, 1,0 % dans le fichier béninois contre 0,8 % dans la
   note ivoirienne.
4. Régénérer ou retirer le registre tunisien `tax_codes_and_assiettes.json`.
5. Compléter la collecte ivoirienne : RS, PCS et PUA annoncés en note, absents
   des données.

## Conséquence sur la politique d'indisponibilité

`docs/DECISION_INDISPONIBILITE_CALCULATEUR.md` proposait de servir le taux de TVA
national quand le tarif est muet. **Cette proposition est suspendue jusqu'à
résolution du présent constat** : un taux sans son assiette ne produit pas un
montant, et servir un taux national sur une assiette supposée reviendrait à
fabriquer un chiffre.
