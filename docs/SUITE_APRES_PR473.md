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
| 1 | Unité des taxes spécifiques | un **montant faux**, dans les deux sens | 2 435 positions |
| 2 | Crawler ghanéen | une ligne **plus grossière** que celle qu'il déclare | 5 387 servies |
| 3 | Algérie — règle du moins-disant | un droit **plus cher** sous préférence que sous NPF | 8 positions |
| 4 | Quatre pays dérivés du Bénin | une assiette de TVA **non fondée** | 4 pays |
| 5 | Taux du PCS | un écart de 0,2 point **non tranché** | UEMOA |
| 6 | Maroc en application | une préférence **affichée mais non appliquée** | 40 origines |
| 7 | Règles fiscales éthiopiennes | rien encore — `OFFER_ONLY` (hors moins-disant, cf. n° 3) | en attente |

---

## 1. L'unité des taxes spécifiques — le dernier montant faux connu

**Le défaut.** `_parse_crawled_tax_rate` extrait le premier nombre d'une chaîne
sans regarder son unité. Un montant unitaire devient donc un pourcentage.

**Ce que portent réellement les données.** Une seule unité apparaît dans
l'ensemble des fichiers collectés, et elle est tunisienne :

| Valeur source observée | Assiette déclarée | Lue par le moteur comme |
|---|---|---|
| `0.1 dinars` — droit sanitaire vétérinaire | `QCS` (quantité) | 0,1 % |
| `1.2 dinars` — prélèvement CGC bovins/viande | `PN` (poids net) | 1,2 % |
| `0.012 dinars` — taxe municipale d'abattage | quantité | 0,012 % |

**2 435 occurrences, toutes en dinars, toutes tunisiennes.** Recomptées le
15 septembre sur `backend/data/crawled` et `crawled_normalized` : aucune autre
unité, dans aucun autre pays. La Tunisie compte en dinars — elle n'appartient
à aucune zone franc CFA — et c'est le seul pays dont les données portent des
taxes assises sur une quantité.

*Précision sur la méthode.* La caractérisation du lecteur a été obtenue en lui
soumettant des chaînes construites (`1000 FCFA/litre`, `15 DT/kg`) pour montrer
qu'il ignore l'unité quelle qu'elle soit. **Ces chaînes ne figurent pas dans les
données** : ce sont des sondes, pas des observations. Une version antérieure de
ce document les présentait dans la même colonne que les valeurs tunisiennes
réelles, ce qui laissait croire à des montants en francs CFA dans un tarif
libellé en dinars. L'erreur est corrigée ici.

**Ce qui se passe vraiment aujourd'hui.** Sur le chemin tunisien en production,
les données passent par l'ETL, qui ramène ces taxes à un taux nul : elles
**disparaissent** au lieu d'être converties. Le total est donc sous-évalué. La
conversion en pourcentage guette sur les autres chemins de lecture.

Les deux traitements sont fautifs, et pour la même raison : une taxe assise sur
une quantité n'est ni un pourcentage ni un zéro. C'est une taxe **non liquidable
en l'état**, qui doit être déclarée telle quelle.

**Pourquoi ce chantier a été séparé.** Il modifie des taux sur 2 435 positions.
Le mêler au changement d'assiette de la PR #473 aurait rendu les deux
inauditables — on n'aurait plus su lequel expliquait quel écart.

**Critères d'acceptation.**

- Aucune valeur non ad valorem n'est jamais rendue comme un taux.
- Une taxe spécifique présente dans la source ressort `SPECIFIQUE_SANS_QUANTITE`,
  avec son montant unitaire et son assiette déclarée, jamais un zéro muet.
- Le total d'une position qui en porte une est déclaré **non liquidable**
  plutôt que servi incomplet — la règle du dépôt sur l'absence s'applique ici
  comme ailleurs.
- Mesure avant/après publiée : combien de positions changent, dans quel sens,
  et de combien.
- Un test qui mord sur chacune des trois valeurs réellement observées, et sur
  une unité arbitraire, pour que la garde ne dépende pas du libellé rencontré.

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

### Ce qui reste : la règle du moins-disant

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

Les huit sont des viandes bovines du chapitre 0201 : NPF 5 %, taux de base 2019
à 30 %, donc 24 % en 2026 sous calendrier standard. Un importateur n'invoquerait
évidemment jamais une préférence plus chère que le droit commun — mais le
calculateur, lui, la lui sert.

**C'est la règle du moins-disant**, celle que le règlement éthiopien énonce à son
article 3(5) et que ce document rangeait au chantier n° 7 en la croyant « sans
effet tant que l'Éthiopie reste `OFFER_ONLY` ». Elle mord ici, aujourd'hui, en
production, sur huit positions algériennes.

**Critères d'acceptation.**

- Le taux préférentiel servi n'excède jamais le NPF de la même position.
- Le plancher est appliqué comme une **règle générale**, pas comme un correctif
  algérien : tout régime préférentiel du moteur en relève.
- Le résultat dit laquelle des deux voies a été retenue, et pourquoi.
- Un test qui mord sur `0201101100` — NPF 5 %, base 2019 à 30 %.

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
