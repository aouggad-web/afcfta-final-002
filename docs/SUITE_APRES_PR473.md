# Ce qui vient après la PR #473

> Établi le 15 septembre 2026, au lendemain de la fusion de `70a1fa1`.
> Ordre fondé sur une seule question : **quel défaut fait servir aujourd'hui un
> montant faux à un opérateur ?**

## L'ordre, et pourquoi

Un défaut qui fait afficher un mauvais chiffre passe devant un défaut qui fait
afficher *moins* de chiffres, lequel passe devant un rapport interne inexact.
C'est le seul critère retenu ici.

| # | Chantier | Ce que l'opérateur subit aujourd'hui | Ampleur mesurée |
|---|---|---|---|
| 1 | Valeurs non ad valorem servies `0 %` | un **droit annoncé nul** sans fondement | 1 184 positions, 14 pays |
| 2 | Crawler ghanéen | une ligne **plus grossière** que celle qu'il déclare | 5 387 servies |
| ~~3~~ | ~~Algérie — règle du moins-disant~~ | **fait** — plancher NPF général, PR #474 | ~~13 positions~~ |
| 4 | Quatre pays dérivés du Bénin | une assiette de TVA **non fondée** | 4 pays |
| 5 | Taux du PCS | un écart de 0,2 point **non tranché** | UEMOA |
| 6 | Maroc en application | une préférence **affichée mais non appliquée** | 40 origines |
| 7 | Règles fiscales éthiopiennes | rien encore — `OFFER_ONLY` (hors moins-disant, cf. n° 3) | en attente |

---

## 1. Les valeurs non ad valorem servies comme `0 %`

**Le défaut.** Une seule ligne, `authentic_tariff_service.py:1822` :

```python
dd_rate_pct = line.get("dd_rate", 0) or 0
# (`or 0` : une valeur explicitement nulle dans la donnée → 0, jamais None).
```

Le commentaire dit l'intention — éviter un plantage sur `> 0`. Le prix payé est
qu'une donnée **absente** devient une donnée **affirmée** : « droit de douane
0 % ». Ce n'est pas un trou dans l'affichage, c'est une déclaration fausse.

C'est la même forme que le plancher NPF du chantier n° 3 : la donnée juste
existe en amont, et le service la remplace par un chiffre qui ne plante pas.

**Ampleur mesurée** le 15 septembre, sur les 53 fichiers de `backend/data` :
**1 184 positions, dans 14 pays**, servent `dd_rate_pct: 0` sans qu'aucune
source ne l'établisse. Quatre causes distinctes, une seule conséquence :

| Cause | Positions | Pays |
|---|---:|---|
| Droit spécifique (`8c/kg`, `c/li`, `c/u`) | 365 | ZAF, BWA, LSO, NAM, SWZ |
| CET « Sensitive Item » sans taux ad valorem | 308 | BDI, COD, KEN, RWA, SSD, TZA, UGA |
| Variantes non tranchées (`[5.0, 30.0]`…) | 296 | DZA |
| Aucune donnée de taxe / pas de ligne DD | 215 | EAC, MAR |

**Vérifié en production.** `ZAF 020830` (« Of primates ») : la source SARS
publie `8c/kg`, l'ETL écrit honnêtement `dd_rate: null`, et le calculateur rend
`dd_rate_pct: 0` avec un `npf_calculation` qui ne contient **aucun** droit de
douane. La falsification est dans le service, pas dans la donnée.

**Les droits spécifiques, cas particulier du même défaut.** Les fichiers
collectés distinguent déjà proprement `rate_pct` (nul) de `specific_value` et de
l'assiette. Recompté le 15 septembre :

| Pays | Lignes à droit spécifique | Unité | Servies |
|---|---:|---|---:|
| Tunisie | 2 435 | `dinars` | **0** |
| ZAF, BWA, LSO, NAM, SWZ | 629 chacun | `c/kg`, `c/li`, `c/u` | **0** |
| **Total** | **5 580** | 6 pays | **0** |

*Correction d'une erreur de ce document.* Une version antérieure affirmait
« **2 435 occurrences, toutes en dinars, toutes tunisiennes** […] aucune autre
unité, dans aucun autre pays ». C'est faux : les cinq pays de la SACU portent
629 lignes chacun en cents par kilogramme, litre ou unité. Le recomptage avait
porté sur les fichiers tunisiens et conclu sur l'ensemble — l'absence constatée
là où l'on avait cherché a été prise pour une absence partout. C'est exactement
la faute que le bas de ce document met en garde de commettre.

*Précision sur la méthode, conservée.* La caractérisation du lecteur avait été
obtenue en lui soumettant des chaînes construites (`1000 FCFA/litre`,
`15 DT/kg`). **Ces chaînes ne figurent pas dans les données** : ce sont des
sondes, pas des observations. Aucun montant en francs CFA n'existe dans le
tarif tunisien, qui est libellé en dinars.

**Un piège latent, à désamorcer en même temps.** `_parse_crawled_tax_rate`
extrait le premier nombre d'une chaîne sans regarder son unité : soumis aux
`raw_value` réels, il rend **5 580 taux sur 5 580** — `0.1 dinars` devient
0,1 %, `8c/kg` devient 8 %. Aucun appelant ne l'atteint aujourd'hui, mais par
accident seulement : `row.get("rate", row.get("rate_pct", row.get("raw_value")))`
ne retombe jamais sur `raw_value`, parce que la clé `rate_pct` **existe** avec
la valeur `None`. Qu'un collecteur omette la clé au lieu de la mettre à nul, et
les 5 580 deviennent des pourcentages du jour au lendemain.

**Le dépôt porte déjà le bon geste**, sur le versant préférentiel
(`authentic_tariff_service.py:1646`) :

> « SARS Schedule 1 Part 1, colonne AfCFTA — taux officiel : 3,2c/kg.
> **Quantité requise pour calculer ce droit spécifique/composé.** »

Il y a donc un précédent à étendre au versant NPF, pas un motif à inventer.

**Critères d'acceptation.**

- Aucune valeur non ad valorem n'est jamais rendue comme un taux, ni comme `0`.
- Une position dont le droit n'est pas ad valorem le **dit** : montant unitaire,
  assiette déclarée, et mention que la quantité est requise.
- Les quatre causes sont distinguées dans le résultat : un droit spécifique, un
  taux non tranché entre variantes et une donnée absente ne se disent pas de la
  même façon à l'opérateur.
- Le total d'une telle position est déclaré **incomplet**, jamais servi comme
  s'il était entier.
- `_parse_crawled_tax_rate` refuse une chaîne porteuse d'une unité au lieu d'en
  extraire le premier nombre — le piège latent est fermé même si aucun appelant
  ne l'atteint.
- Mesure avant/après publiée : combien de positions changent, dans quel sens.

**Ce qu'il faut décider.** Quand la quantité est fournie par l'appelant, faut-il
liquider la taxe spécifique ? Le dépôt porte déjà une règle 3 en ce sens
(`docs/DECISION_INDISPONIBILITE_CALCULATEUR.md`) ; il reste à la câbler.

---

## 2. Le crawler ghanéen

**Le défaut.** La normalisation ramène les codes nationaux à des positions SH6.
L'opérateur qui déclare un code national à dix chiffres reçoit le tarif d'une
position à six — plus grossière, et potentiellement d'un autre taux.

C'est la perte la plus visible pour l'utilisateur parmi les défauts de collecte
recensés par l'audit du 13 septembre.

**État des chiffres, et ce qu'ils valent.** Les quatre fichiers ghanéens du
dépôt portent tous **5 387** lignes — vérifié. Le chiffre de **6 129** codes
nationaux, cité par l'audit et repris dans la description de la PR #473, est un
décompte **à la source** : aucun fichier du dépôt ne le porte, et il n'a pas été
revérifié ici. Le premier travail est donc de **recompter ce que le portail
ghanéen publie réellement**, avant de qualifier l'écart.

**Critères d'acceptation.**

- Le nombre de codes nationaux publiés par la source est recompté et daté.
- Un code national ghanéen est servi par sa propre ligne, pas par son parent.
- L'écart entre codes publiés et positions servies est expliqué position par
  position, et non résumé par une soustraction.
- Aucun taux n'est inventé pour combler : une ligne nationale sans taux publié
  reste sans taux.

---

## 3. L'Algérie — le dossier est fait, une seule chose reste

**Correction d'une erreur de ce document.** Une version antérieure annonçait que
« le calculateur n'a aucune donnée tarifaire préférentielle » pour l'Algérie.
C'est faux, et le propriétaire du dépôt l'a relevé : le dossier algérien a été
constitué à partir des PDF de la ZLECAf et il est **opérationnel**.

Ce que le dépôt porte, vérifié le 15 septembre :

| Élément | État |
|---|---|
| Circulaire 482/DGD du 22/10/2024 | texte intégral archivé, 73 Ko |
| Liste B (démantèlement 13 ans) | **1 163 codes** + leurs taux de base 2019 |
| Liste C (exclue) | **456 codes** |
| Calendrier de la circulaire | `circular_482_schedule.json`, standard et réciprocité |
| Partenaires actifs | 9 |
| Partenaires en réciprocité | 13 |
| Positions gelées (règles d'origine) | 13 plages de positions |
| Exonération du DAPS | implémentée, `daps_exempt()` |

Le calcul fonctionne : une importation égyptienne relevant de la liste B reçoit
son taux de base 2019 démantelé selon le calendrier standard, une kényane selon
le calendrier réciprocité, et une origine non activée reste au NPF avec la
citation de la circulaire. Le tarif collecté ne porte pas de colonne ZLECAf, et
c'est sans importance : la préférence algérienne se calcule **à partir des
listes de la circulaire**, pas d'une colonne du tarif.

### Ce qui restait : la règle du moins-disant — **fait**

Une vérification faite en corrigeant ce document a trouvé un défaut réel, et
c'est le seul.

`compute_dza_zlecaf_rate` applique le taux de base 2019 aux positions de la
liste B — à juste titre, l'article 23 de l'Accord figeant la base à l'entrée en
vigueur. Mais il ne le compare jamais au NPF courant. Quand l'Algérie a
**réduit** son droit depuis 2019, le taux « préférentiel » peut donc dépasser le
droit ordinaire.

Mesuré sur les 1 163 positions de la liste B, hors positions gelées :

| Origine | Positions où le taux ZLECAf dépasse le NPF | Écart maximal |
|---|---:|---|
| Égypte (calendrier standard) | **8** | +19,0 points |
| Kenya (calendrier réciprocité) | **8** | +21,2 points |

Les huit sont des viandes : **cinq bovines** (`0201101100`, `0201101900`,
`0201201000`, `0201202000`, `0201309100`) et **trois de volaille**
(`0207121000`, `0207122000`, `0207129000`). Toutes : NPF 5 %, taux de base 2019
à 30 %, donc 24 % en 2026 sous calendrier standard. Un importateur n'invoquerait
évidemment jamais une préférence plus chère que le droit commun — mais le
calculateur, lui, la lui sert.

*Correction.* Une version antérieure de ce paragraphe disait « les huit sont des
viandes bovines du chapitre 0201 ». Les trois positions du 0207 y échappaient :
le décompte de huit était juste, sa description ne l'était pas. Relevé en revue,
recompté sur `DZA_tariffs.json` et `list_b_base_rates.json`.

**C'est la règle du moins-disant**, celle que le règlement éthiopien énonce à son
article 3(5) et que ce document rangeait au chantier n° 7 en la croyant « sans
effet tant que l'Éthiopie reste `OFFER_ONLY` ».

**Implémentée dans la PR #474**, comme règle générale et non comme correctif
algérien : le plancher est posé dans le constructeur commun que les quatre
chemins préférentiels du moteur traversent. L'audit a montré que le même défaut
courait sur trois d'entre eux — 8 positions algériennes, 2 sud-africaines, 3
kényanes, **13 en tout**.

**Ce que la revue a rattrapé.** La première version du plancher éteignait aussi
`preference_applied`. Or les huit positions algériennes sont **toutes**
exonérées de DAPS par la circulaire 482/2024 — un droit de 70 % que la cascade
retire réellement. Le moteur annonçait donc « aucune préférence » tout en
calculant 70 000 DA d'économie sur 100 000 de CIF. Pour l'opérateur, c'est la
pire des deux erreurs : croyant n'avoir rien à gagner, il ne présente pas son
certificat d'origine et paie le plein tarif. Le plancher ne rabote désormais que
le droit de douane, et `plancher_npf` remonte jusqu'à la réponse d'API.

*La leçon, du même ordre que celle du bas de page : un garde-fou qui corrige un
montant doit être vérifié sur ce qu'il laisse intact, pas seulement sur ce qu'il
change.*

## 4. Les quatre pays dérivés du Bénin

**CPV, GMB, LBR, SLE** portent les fichiers béninois avec le taux de TVA
substitué, et l'honnêteté du dépôt les déclare `derived_from`. Ils sont quatre
des cinq désaccords restants de `reports/ASSIETTES_ET_METHODES.json` : leur
source publie « CIF + DD + RS + PCS » quand la table codée dit « CIF + DD », et
aucune loi nationale de TVA n'a été lue pour trancher.

Ce sont les seuls pays de la CEDEAO hors UEMOA sous ce régime : la directive
UEMOA ne leur est **pas** opposable, et c'est précisément pourquoi ils ont été
laissés hors de la règle d'assiette.

**Critères d'acceptation.** Pour chacun : la loi nationale de TVA lue, l'article
sur l'assiette à l'importation cité verbatim, le texte archivé et scellé, et le
désaccord tranché dans un sens ou dans l'autre — jamais laissé ouvert au motif
que les quatre se ressemblent.

---

## 5. Le taux du PCS

Le fichier béninois porte **1,0 %**, la note ivoirienne **0,8 %**. Les deux sont
dans le dépôt, et rien ne dit lequel s'applique où ni depuis quand.

C'est un écart de 0,2 point sur une assiette qui sert ensuite à la TVA : il se
propage. Petit en valeur, il est facile à trancher sur le texte UEMOA
instituant le prélèvement, et il n'y a aucune raison de le laisser traîner.

---

## 6. Le Maroc en application effective

Le Maroc est aujourd'hui `OFFER_ONLY` : son barème est **affiché** selon le
droit marocain, mais la préférence n'est pas **appliquée** au calcul. Trois
verrous des quatre sont levés (acte, liste des 40 origines, barème par ligne).

**Ce qui reste**, d'après `MAR_application_2026-09-13.json` :

- **Décider du traitement de la TPI.** La circulaire soumet au démantèlement le
  droit d'importation **et** la taxe parafiscale à l'importation ; le
  calculateur ne réduit aujourd'hui que le droit de douane. Appliquer la
  préférence sans traiter la TPI servirait un total trop élevé.
- **Confirmer auprès de l'ADII** qu'aucune notification postérieure au 22 janvier
  2024 n'a modifié les listes P1/P2 — la circulaire prévient elle-même qu'elles
  « sont appelées à évoluer » sans nouvelle circulaire publique.

C'est le chantier qui apporterait le plus à l'opérateur : 40 origines, 14 510
lignes, un démantèlement entamé depuis 2021. Mais il ne doit pas précéder la
décision sur la TPI.

---

## 7. Les règles fiscales éthiopiennes

Quatre règles ont été établies sur le Negarit Gazette et **ne sont pas
implémentées** :

| Article | Règle |
|---|---|
| 3(5) | le NPF s'applique s'il est **inférieur** au taux ZLECAf |
| 5(2) | la surtaxe du règlement 133/2007 **subsiste** mais décroît avec le barème |
| 5(3) | la Social Development Levy **s'éteint** pour les catégories A et B |
| 3(3) | seule la catégorie A est réduite à ce jour |

Elles ne mordent sur rien tant que l'Éthiopie reste `OFFER_ONLY`, faute de
l'avis ministériel des origines. Les câbler d'avance serait du code non
exerçable ; les oublier serait perdre un travail déjà fait. D'où leur place en
fin de liste — et leur consignation dans la fiche.

**La règle du moins-disant mérite une attention particulière** : elle n'est pas
propre à l'Éthiopie dans son principe, et il faudra vérifier si d'autres actes
nationaux la portent. Un calculateur qui servirait une préférence plus chère que
le NPF serait faux partout.

---

## La collecte de terrain

Trois verrous du chantier (`chantier_collecte_2026-09-14.json`) **ne se lèveront
pas par recherche documentaire** — le tour des sept destinations l'a établi :

| Document | Pays | Où |
|---|---|---|
| Avis du Ministry of Trade and Regional Integration | Éthiopie | ministère, ou Ethiopian Customs Commission |
| Texte du Statutory Instrument n° 92 de 2024 | Zambie | supplément au Government Gazette du 30/12/2024 |
| Official Gazette portant la PSTC, avril 2025 | Nigeria | Federal Government Printer |

Ils demandent une **demande directe** aux administrations. La fiche dit pour
chacun quoi demander et à qui.

À défaut, la preuve alternative reste celle que le chantier décrit : une
déclaration en douane effectivement liquidée sous régime ZLECAf, avec son
certificat d'origine, le taux appliqué et le détail des autres prélèvements
maintenus. Elle établit d'un coup les trois conditions que les textes laissent
ouvertes — avec la précaution déjà consignée : **une déclaration isolée prouve
qu'un bureau a liquidé ainsi, pas que la règle est générale.**

---

## Une règle de méthode, acquise à ses dépens

Ce travail a produit plusieurs faux constats avant de produire des vrais. Ce qui
les a tous évités, une fois la leçon apprise, tient en une phrase :

> **Une absence n'est un résultat que si la source interrogée était en état de
> répondre.**

Elle s'applique aux archives (52 numéros rwandais hebdomadaires contre 5 numéros
nigérians pour une année entière), aux sites web (146 Ko sans une occurrence du
mot « origine » trahissent une coquille, pas une absence), et aux tests (un
garde-fou satisfait par construction ne garde rien).

La vérifier coûte une minute. Ne pas la vérifier a coûté, dans cette session,
deux faux négatifs consécutifs et deux garde-fous qui ne pouvaient pas échouer.
