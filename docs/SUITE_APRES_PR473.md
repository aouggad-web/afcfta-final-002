# Plan de travail — état au 15 septembre 2026

**Règle de travail.** Un chantier à la fois. Objectif défini, mesure faite, résultat vérifiable. Rien n'entre ici sans un chiffre daté et sa source.

**Critère d'ordre.** Quel défaut fait servir aujourd'hui un montant faux à un opérateur. Un mauvais chiffre passe devant un chiffre manquant, qui passe devant un rapport interne inexact.

| # | Chantier | Ce que l'opérateur subit | Mesure | État |
|---|---|---|---|---|
| 1 | Droit annoncé `0 %` sans fondement | montant **faux**, sous-évalué | 1 184 positions, 14 pays | à faire |
| 2 | Crawler ghanéen | ligne **plus grossière** que déclarée | 5 387 servies | à faire |
| 3 | Plancher NPF | droit **plus cher** sous préférence | 13 positions | **fait** — PR #474 |
| 4 | Assiette TVA de CPV, GMB, LBR, SLE | assiette **non fondée** | 4 pays | à faire |
| 5 | Taux du PCS | écart de **0,2 point** non tranché | UEMOA | à faire |
| 6 | Maroc en application | préférence **affichée, non appliquée** | 40 origines | bloqué (décision TPI) |
| 7 | Règles fiscales éthiopiennes | rien — `OFFER_ONLY` | 3 règles sur 4 | en attente |
| 8 | Divergence de sources sud-africaine | deux sources **contradictoires** | 2 positions | à trancher |

---

## 1. Le droit annoncé `0 %` sans fondement

**Objectif.** Qu'aucune position n'affirme un droit de douane nul qu'aucune source n'établit.

**Cause.** Une ligne — `backend/services/authentic_tariff_service.py:1832` :

```python
dd_rate_pct = line.get("dd_rate", 0) or 0
```

Une donnée **absente** devient une donnée **affirmée**. L'ETL écrit honnêtement `null` ; le service le remplace par un zéro qui ne plante pas.

**Mesure** (15 septembre, 53 fichiers de `backend/data`) — 1 184 positions, 4 causes :

| Cause | Positions | Pays |
|---|---:|---|
| Droit spécifique (`8c/kg`, `c/li`, `c/u`) | 365 | ZAF, BWA, LSO, NAM, SWZ |
| CET « Sensitive Item » sans taux ad valorem | 308 | BDI, COD, KEN, RWA, SSD, TZA, UGA |
| Variantes non tranchées (`[5.0, 30.0]`…) | 296 | DZA |
| Aucune donnée de taxe | 215 | EAC, MAR |

**Preuve en production.** `ZAF 020830` : SARS publie `8c/kg`, le calculateur rend `dd_rate_pct: 0` et un `npf_calculation` sans aucun droit de douane.

**Sous-ensemble : les droits spécifiques**, que les fichiers collectés distinguent déjà proprement (`rate_pct` nul, `specific_value` et assiette renseignés) :

| Pays | Lignes | Unité | Servies |
|---|---:|---|---:|
| Tunisie | 2 435 | `dinars` | 0 |
| ZAF, BWA, LSO, NAM, SWZ | 629 chacun | `c/kg`, `c/li`, `c/u` | 0 |
| **Total** | **5 580** | 6 pays | **0** |

**Piège latent à fermer en même temps.** `_parse_crawled_tax_rate` extrait le premier nombre d'une chaîne sans lire son unité : soumis aux `raw_value` réels, il rend **5 580 taux sur 5 580** (`0.1 dinars` → 0,1 % ; `8c/kg` → 8 %). Aucun appelant ne l'atteint aujourd'hui, mais par accident : `row.get("rate", row.get("rate_pct", row.get("raw_value")))` ne retombe jamais sur `raw_value` parce que la clé `rate_pct` **existe** avec la valeur `None`. Qu'un collecteur omette la clé au lieu de la mettre à nul, et les 5 580 deviennent des pourcentages.

**Précédent à suivre**, déjà dans le dépôt (`authentic_tariff_service.py:1657`) :

> « SARS Schedule 1 Part 1, colonne AfCFTA — taux officiel : 3,2c/kg. **Quantité requise pour calculer ce droit spécifique/composé.** »

**Résultat attendu.**

- Aucune valeur non ad valorem rendue comme un taux ni comme `0`.
- Les quatre causes se disent différemment : un droit spécifique, un taux non tranché et une donnée absente ne sont pas la même information.
- Le total d'une telle position est déclaré **incomplet**, jamais servi comme entier.
- `_parse_crawled_tax_rate` refuse une chaîne porteuse d'une unité.
- Mesure avant/après publiée : combien de positions changent, dans quel sens.

**Décision requise.** Si l'appelant fournit la quantité, liquide-t-on le droit spécifique ? Le dépôt porte déjà une règle en ce sens (`docs/DECISION_INDISPONIBILITE_CALCULATEUR.md`) ; elle n'est pas câblée.

---

## 2. Le crawler ghanéen

**Objectif.** Qu'un code national ghanéen soit servi par sa propre ligne, pas par sa position SH6 parente.

**Mesure.** Les quatre fichiers ghanéens du dépôt portent **5 387** lignes. Le chiffre de **6 129** codes nationaux, cité par l'audit du 13 septembre, ne figure dans **aucun** fichier : c'est un décompte à la source jamais revérifié.

**Résultat attendu.**

- Le nombre de codes publiés par le portail ghanéen est **recompté et daté** — premier travail, avant toute qualification de l'écart.
- L'écart entre codes publiés et positions servies est expliqué position par position, pas par une soustraction.
- Aucune ligne sans taux publié ne reçoit un taux inventé.

---

## 3. Plancher NPF — **fait**

**Objectif.** Qu'un taux préférentiel servi n'excède jamais le NPF de la même position. Une préférence est une faculté, pas une obligation.

**Défaut trouvé.** Trois chemins indépendants calculaient `preference_applied = taux < NPF` puis servaient le taux préférentiel quand même.

**Mesure.** 13 positions : 8 algériennes (5 bovines `0201…`, 3 de volaille `0207…`), 2 sud-africaines, 3 kényanes.

**Livré** dans la PR #474, dans le constructeur commun aux quatre chemins, avec sa déclaration `plancher_npf` du moteur jusqu'à l'écran.

**Trois défauts du correctif lui-même, trouvés en revue et corrigés** — ils valent d'être retenus :

| Défaut | Portée |
|---|---|
| le plancher éteignait `preference_applied` | les 8 positions algériennes sont **toutes** exonérées de DAPS (70 %) : le moteur annonçait « aucune préférence » en calculant 70 000 DA d'économie sur 100 000 de CIF |
| `plancher_npf` s'arrêtait au résolveur privé | les clients d'API ne recevaient que la note en prose |
| le bandeau ne s'affichait pas | le composant ne rend aucune note en régime `ZLECAF` |

> **Un garde-fou qui corrige un montant doit être vérifié sur ce qu'il laisse intact, pas seulement sur ce qu'il change.** 29 436 vérifications portaient sur le taux servi ; aucune sur le drapeau, l'API ou l'écran.

---

## 4. L'assiette de TVA de CPV, GMB, LBR, SLE

**Objectif.** Trancher les quatre derniers désaccords d'assiette de `reports/ASSIETTES_ET_METHODES.json`.

**État.** Ces quatre pays portent les fichiers béninois avec le taux de TVA substitué, honnêtement déclarés `derived_from`. Leur source publie « CIF + DD + RS + PCS » quand la table codée dit « CIF + DD ». Seuls pays CEDEAO hors UEMOA sous ce régime : la directive UEMOA ne leur est **pas** opposable — c'est pourquoi ils ont été laissés hors de la règle d'assiette.

**Résultat attendu.** Pour chacun : loi nationale de TVA lue, article sur l'assiette à l'importation cité verbatim, texte archivé et scellé, désaccord tranché. Jamais résolu en bloc au motif que les quatre se ressemblent.

---

## 5. Le taux du PCS

**Objectif.** Établir le taux applicable et depuis quand.

**État.** Le fichier béninois porte **1,0 %** (`BEN_tariffs.json`, `taxes_detail`), la note du fichier ivoirien **0,8 %** (`crawled/CIV_tariffs.json`). Les deux ne peuvent être vrais ensemble.

**Piste déjà consignée** dans `ECOWAS_derives_BEN_2026-09-14.json` : 0,8 % serait le taux maintenu par le 20e sommet de l'UEMOA depuis 2017. **Le constat ne tranche pas** — il désigne où chercher.

**Pourquoi ça compte.** L'écart se propage : le PCS entre dans l'assiette qui sert ensuite à la TVA.

**Résultat attendu.** L'acte additionnel UEMOA en vigueur, cité et archivé, et un seul taux par pays.

---

## 6. Le Maroc en application effective

**Objectif.** Passer le Maroc de `OFFER_ONLY` à préférence appliquée — 40 origines, 14 510 lignes, démantèlement entamé depuis 2021.

**Acquis.** Trois verrous sur quatre : l'acte, la liste des 40 origines, le barème par ligne (`MAR_application_2026-09-13.json`).

**Bloqué sur deux points.**

1. **La TPI.** La circulaire ADII soumet au démantèlement le droit d'importation **et** la taxe parafiscale à l'importation ; le calculateur ne réduit que le droit de douane. Appliquer la préférence sans traiter la TPI servirait un total trop élevé. **Décision requise avant tout code.**
2. **Confirmation ADII** qu'aucune notification postérieure au 22 janvier 2024 n'a modifié les listes P1/P2 — la circulaire prévient qu'elles « sont appelées à évoluer » sans nouvelle circulaire publique.

---

## 7. Les règles fiscales éthiopiennes

**État.** Quatre règles établies sur le Federal Negarit Gazette n° 55. Une est faite, trois attendent.

| Article | Règle | État |
|---|---|---|
| 3(5) | le NPF s'applique s'il est inférieur au taux ZLECAf | **fait** — chantier 3 |
| 5(2) | la surtaxe du règlement 133/2007 subsiste mais décroît avec le barème | à faire |
| 5(3) | la Social Development Levy s'éteint pour les catégories A et B | à faire |
| 3(3) | seule la catégorie A est réduite à ce jour | à faire |

Les trois restantes ne mordent sur rien tant que l'Éthiopie est `OFFER_ONLY`, faute de l'avis ministériel des origines. Les câbler d'avance serait du code non exerçable.

---

## 8. La divergence de sources sud-africaine

**Objectif.** Savoir quelle source fait foi pour l'Afrique du Sud.

**Constat** (15 septembre). Sur 2 positions, le barème SARS que sert le moteur et la colonne AfCFTA du tarif national **se contredisent** : dans le fichier national, l'AfCFTA n'excède jamais le NPF (0 sur 8 403). Le plancher rend le montant juste dans les deux lectures — la question de la source reste entière.

**Résultat attendu.** Une source désignée, son motif écrit, et l'autre citée comme divergente plutôt que silencieusement ignorée.

---

## La collecte de terrain

Trois documents **ne se lèveront pas par recherche documentaire** — le tour des sept destinations l'a établi. Ils demandent une demande directe aux administrations (`chantier_collecte_2026-09-14.json` dit quoi demander et à qui).

| Document | Pays | Où |
|---|---|---|
| Avis du Ministry of Trade and Regional Integration | Éthiopie | ministère, ou Ethiopian Customs Commission |
| Texte du Statutory Instrument n° 92 de 2024 | Zambie | supplément au Government Gazette du 30/12/2024 |
| Official Gazette portant la PSTC, avril 2025 | Nigeria | Federal Government Printer |

**Preuve alternative** : une déclaration en douane liquidée sous régime ZLECAf, avec certificat d'origine, taux appliqué et détail des prélèvements maintenus. Elle établit d'un coup les trois conditions — avec sa limite : **une déclaration isolée prouve qu'un bureau a liquidé ainsi, pas que la règle est générale.**

---

## Deux règles de méthode, acquises à leurs dépens

> **Une absence n'est un résultat que si la source interrogée était en état de répondre.**

Vaut pour les archives (52 numéros rwandais hebdomadaires contre 5 numéros nigérians pour une année entière), les sites web (146 Ko sans une occurrence du mot « origine » trahissent une coquille, pas une absence), et les tests (un garde-fou satisfait par construction ne garde rien).

> **Un garde-fou qui corrige un montant doit être vérifié sur ce qu'il laisse intact.**

Le plancher NPF a demandé trois correctifs après coup, tous sur ce qu'il touchait sans qu'on l'ait mesuré.
