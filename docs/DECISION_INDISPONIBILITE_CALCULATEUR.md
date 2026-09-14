# Politique d'indisponibilité du calculateur — note de décision (travail 0.3)

**État : proposition, en attente d'arbitrage.** Le plan de correction
(`docs/PLAN_CORRECTION_CALCULATEUR_2026-09.md`, travail 0.3) exige que cette
décision soit arrêtée **avant** de coder la phase 2. Elle est de nature
produit, pas technique : elle détermine ce que l'utilisateur voit quand une
donnée manque.

## Le problème à trancher

L'audit interdit de convertir une donnée absente en zéro — à juste titre : sur
`DZA 1001110000`, la source ne porte aucun droit de douane, et le calculateur
affiche aujourd'hui soit une exception, soit 0. Mais l'audit ne dit pas ce qui
doit s'afficher à la place, et l'interdiction seule n'est pas implémentable :
un écran doit bien montrer quelque chose.

La mesure de référence montre que le volume n'est pas marginal. Sur les seuls
cas relevés à ce jour, l'absence de droit exploitable touche 299 lignes
algériennes, 1 368 lignes éthiopiennes, 181 lignes SACU à droit spécifique et
1 655 lignes tunisiennes à taxe spécifique. Une politique trop stricte rendrait
muettes des milliers de positions ; une politique trop permissive continuerait
à publier des chiffres faux. La distinction doit donc être fine.

## Le coût mesuré, sur les 342 176 lignes collectées

`scripts/measure_unavailability_cost.py` chiffre la règle 2 sur les fichiers
tels que collectés et écrit `reports/COUT_INDISPONIBILITE.json`. Une mesure
antérieure circulait sans être portée par aucun fichier du dépôt : elle n'était
ni rejouable ni opposable, et elle est devenue fausse sans que rien ne le
signale le jour où l'inventaire fiscal a été corrigé. Celle-ci est versionnée
et testée.

| Lecture de la règle 2 | Lignes au total indisponible | Part |
|---|---:|---:|
| **Stricte** — une assiette non déclarée est une indisponibilité | 174 131 | **50,89 %** |
| **Restreinte** — seules une taxe absente ou un droit spécifique sans quantité le sont | 59 677 | **17,44 %** |
| **Résidu** — après service du taux de TVA national documenté, provenance déclarée | 4 265 | **1,25 %** |

L'écart entre les deux premières lignes est le vrai point d'arbitrage, et la
note ne le tranchait pas. Il tient à une seule question : **une assiette non
déclarée est-elle une donnée manquante ?** Le taux, lui, est publié ; seule la
convention d'assiette manque, et elle est la même — CIF — dans toutes les
nomenclatures concernées. La lecture stricte éteindrait la moitié de la
plateforme pour une convention que la source ne prend pas la peine d'écrire
parce qu'elle va de soi.

Le troisième chiffre est celui qui compte pour décider : **1,25 %**. Les
57 344 lignes dont la TVA manque sont toutes couvrables par un taux national
documenté — les 54 pays en ont un dans le dépôt. Servir ce taux en déclarant sa
provenance ramène le coût de l'option (A) de 17,44 % à 1,25 %.

Ce résidu se concentre : **34 des 51 pays n'en portent aucune ligne**.
L'Éthiopie en concentre 1 368 (21,7 % de ses lignes), la Tunisie 847, l'Algérie
299, et chacun des cinq pays SACU 182 — les droits spécifiques sans quantité,
que la règle 3 rend calculables dès que la quantité est fournie.

Ces volumes recoupent, par une mesure indépendante, ceux que cette note citait
avant qu'elle n'existe : 299 lignes algériennes et 1 368 éthiopiennes, aux
mêmes chiffres.

## Trois états, et leur affichage

| État | Signification | Ce que l'utilisateur voit | Le total est-il calculé ? |
|---|---|---|---|
| `DOCUMENTE` | La source porte une valeur exploitable pour cette position et cette taxe | Le taux, le montant, la provenance et la date de collecte | Oui |
| `INDISPONIBLE` | La taxe existe ou peut exister, mais la source ne permet pas de la liquider : champ absent, droit spécifique sans quantité, assiette non documentée | La mention « indisponible », le motif, et le paramètre manquant quand il y en a un (quantité, devise) | **Non** — le total porte la même mention, il n'est jamais complété par un zéro implicite |
| `NON_APPLICABLE_DOCUMENTE` | Une source établit qu'aucune taxe de ce type n'est due sur cette position | « Non applicable », avec la référence qui l'établit | Oui, avec une contribution nulle assumée |

Trois règles de fond en découlent.

1. **Un zéro n'est jamais produit par défaut.** Un zéro affiché vient toujours
   d'un zéro lu dans la source (`DOCUMENTE` avec un taux nul) ou d'une
   non-applicabilité établie (`NON_APPLICABLE_DOCUMENTE`). L'absence d'information
   ne produit jamais de zéro.
2. **Une seule taxe indisponible rend le total indisponible.** Publier un total
   partiel présenté comme un coût de revient serait plus trompeur qu'une
   mention d'indisponibilité : l'utilisateur prendrait une décision d'import sur
   un chiffre incomplet. La ventilation reste affichée, avec les lignes
   calculées et les lignes indisponibles distinguées.
3. **Un droit spécifique n'est pas une indisponibilité définitive.** Sur
   `ZAF 020830`, la source porte « 8c/kg » : l'expression et son unité sont
   affichées, la quantité est réclamée, et le montant devient calculable dès
   qu'elle est fournie. C'est un paramètre manquant, pas une donnée manquante.

## Ce que cette politique change par rapport à aujourd'hui

| Position | Aujourd'hui | Après |
|---|---|---|
| `DZA 1001110000` | Exception sur le chemin prioritaire ; 0 sur le POST | DD `INDISPONIBLE`, total `INDISPONIBLE` |
| `ZAF 020830` | DD 0 % et TVA de 150 calculée sur ce zéro | DD `INDISPONIBLE` avec expression « 8c/kg » et quantité réclamée ; TVA non liquidée tant que l'assiette contient un droit inconnu |
| `ETH 01013000000` | « Ligne introuvable » | Ligne servie, DD `INDISPONIBLE`, TVA 15 % `DOCUMENTE` |
| `SOM 01012100` | 0 % d'un côté, 15 % de repli de chapitre de l'autre | 0 % `DOCUMENTE` depuis le canonique, provenance régionale déclarée ; plus de tarif de chapitre |

## Le point qui demande un arbitrage

La règle 2 est la seule qui arbitre entre deux inconvénients réels, et elle
n'est pas neutre commercialement : elle rendra le total indisponible sur des
milliers de positions, là où l'interface affiche aujourd'hui un chiffre. Trois
options :

- **(A) Total indisponible dès qu'une taxe l'est** — retenue ci-dessus. La plus
  sûre juridiquement, la plus coûteuse à l'écran.
- **(B) Total partiel, explicitement étiqueté « plancher »**, avec le décompte
  des taxes non liquidées. Plus utile pour un ordre de grandeur, au risque
  qu'un total étiqueté soit lu comme un total.
- **(C) Les deux** : plancher affiché, total réputé indisponible, la distinction
  portée par le libellé et reprise dans les exports.

Recommandation : **(A) pour le chiffre mis en avant, (C) à terme** si un
plancher explicite s'avère nécessaire aux démonstrations. Commencer par (B)
reviendrait à conserver le défaut que l'audit reproche, avec une étiquette.

La mesure rend cette recommandation nettement moins coûteuse qu'elle ne le
paraissait, à une condition : **retenir la lecture restreinte de la règle 2 et
servir le taux de TVA national documenté**. L'option (A) ne rend alors muettes
que 1,25 % des lignes, contre la moitié de la plateforme sous la lecture
stricte. Sans cette condition, (A) n'est pas tenable et l'arbitrage se
déplacerait vers (C).

Deux sous-décisions en découlent, à trancher avec la principale :

1. **Une assiette non déclarée vaut-elle assiette CIF ?** Si oui, la lecture
   restreinte s'applique. Si non, (A) éteint 50,89 % des lignes.
2. **Le taux de TVA national peut-il être servi à défaut du taux porté par le
   tarif ?** Il ne s'agit pas d'inventer un taux : les 54 taux sont documentés
   et leur source nommée dans le dépôt. Mais le servir revient à compléter la
   source tarifaire par une source fiscale, ce que la provenance doit alors
   déclarer explicitement à l'utilisateur.

Cette note n'engage rien tant qu'elle n'est pas validée ; la phase 2 du plan en
dépend.
