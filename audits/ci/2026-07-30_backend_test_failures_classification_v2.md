# Classification révisée — 91 échecs backend

Date : 2026-07-30  
PR : #337  
Run de référence : CI #1175

## Résultat vérifié

Le run #1175 produit réellement :

- 91 échecs ;
- 1 544 tests réussis ;
- 255 tests ignorés ;
- 5 avertissements.

Le job GitHub reste affiché en succès uniquement parce que l’étape pytest conserve `continue-on-error: true`.

## Répartition exhaustive

| Catégorie | Nombre | Part | Orientation |
|---|---:|---:|---|
| A — migration/format `enhanced_v2` | 31 | 34,1 % | décision d’architecture puis réécriture ciblée |
| B — formalités administratives non prouvées | 48 | 52,7 % | supprimer ou réécrire les assertions non sourcées |
| C — tests réseau/cache non hermétiques | 3 | 3,3 % | injection et mocks déterministes |
| D — attentes statistiques/fiscales à actualiser | 5 | 5,5 % | vérification de source et date d’effet |
| E — contrats applicatifs à arbitrer | 4 | 4,4 % | décision produit puis correction code/test |
| **Total** | **91** | **100 %** | |

La matrice détaillée est enregistrée dans :

`audits/ci/2026-07-30_backend_test_failures_matrix.csv`

## Intégration de la revue Copilot

### 1. Dépendances d’environnement : catégorie F séparée

Copilot a reproduit localement des défauts supplémentaires liés à l’environnement :

- `bs4` absent ;
- `redis` absent ;
- incompatibilité `motor` / `pymongo` autour de `_QUERY_OPTIONS` ;
- bloc `TestNorthAfricaCrossValidator` / `TestNorthAfricaOrchestrator` affecté dans cet environnement local.

Ces défauts sont réels pour la portabilité de la suite, mais ils **ne figurent pas dans la liste des 91 échecs du run CI #1175**. Ils sont donc suivis comme :

- **Catégorie F — dépendances d’environnement et compatibilité du banc de test** ;
- compteur actuel dans la baseline CI #1175 : **0/91** ;
- chantier distinct : verrouillage des versions, inventaire des dépendances optionnelles et test d’import minimal.

Cette séparation évite de mélanger une erreur de dépendance locale avec une régression métier.

### 2. Niger : 19 % n’est pas le taux harmonisé UEMOA

Le registre Niger expose un taux national de TVA de 19 % avec une référence au CGI national. La correction du test devra formuler explicitement que :

- 18 % reste la référence d’harmonisation UEMOA visée par le test historique ;
- 19 % est traité comme une situation nationale documentée pour le Niger ;
- le test ne doit jamais présenter 19 % comme le nouveau taux harmonisé UEMOA ;
- la source primaire et la date d’effet doivent être conservées dans l’assertion ou sa fixture.

### 3. CMR/GNQ : absence de `data_format`

Avant de modifier les tests `enhanced_v2`, il faut trancher entre deux situations :

1. la migration `enhanced_v2` a été abandonnée au profit du modèle actuel de preuve et de disponibilité ;
2. la migration devait être appliquée mais n’a jamais été terminée.

Décision provisoire :

- ne pas accepter automatiquement `data_format=None` comme nouveau standard ;
- ne pas restaurer artificiellement des volumes ou sous-positions ;
- vérifier l’historique du script supprimé et le contrat actuel du service ;
- remplacer ensuite les seuils globaux par des assertions pays/source/statut.

### 4. Formalités administratives

Les tests de catégorie B imposent notamment `IMPDEC`, `ECTN`, `910`, `ARMAUTH`, `OCCDECL`, `FORM M`, `GOEIC` ou d’autres codes à des pays ou lignes sans preuve disponible dans les données actuelles.

La correction autorisée consiste à :

- retirer les assertions universelles non sourcées ;
- tester `NOT_AVAILABLE` ou l’absence explicite lorsque la preuve manque ;
- conserver les formalités uniquement lorsqu’une source officielle, une autorité, un périmètre produit et une date d’effet sont documentés ;
- ne jamais ajouter des documents aux données pour faire passer un test.

## Ordre de traitement proposé

### Lot 1 — intégrité des tests de formalités

Périmètre : 48 tests de catégorie B.

Objectif : éliminer les hypothèses universelles et remplacer les tests par des garde-fous de provenance et de fermeture (`NOT_AVAILABLE`).

Risque métier : élevé si la mauvaise solution consiste à fabriquer les données ; faible si seules les assertions obsolètes sont réécrites.

### Lot 2 — tests hermétiques

Périmètre : 3 tests de catégorie C.

Objectif : neutraliser réseau, cache et fournisseurs réels dans les tests unitaires, tout en gardant un test d’intégration séparé et non bloquant.

### Lot 3 — migration et formats

Périmètre : 31 tests de catégorie A.

Objectif : décider officiellement du statut de `enhanced_v2`, du script supprimé et des sous-positions nationales avant toute réécriture.

### Lot 4 — données et attentes datées

Périmètre : 5 tests de catégorie D.

Objectif : vérifier OEC, les statuts de collecte UEMOA et le cas Niger sur sources traçables.

### Lot 5 — contrats applicatifs

Périmètre : 4 tests de catégorie E.

Objectif : arbitrer le grade risque, l’API de recherche SH6 et la formule fret avant de changer le code ou les tests.

### Lot F — environnement de test

Périmètre : observations locales Copilot, hors compteur CI #1175.

Objectif : verrouiller les dépendances et ajouter un contrôle d’import/compatibilité pour `bs4`, `redis`, `motor` et `pymongo`.

## Conditions avant retrait de `continue-on-error`

1. chaque test de la matrice possède une décision documentée ;
2. aucun test n’est rendu vert par ajout de donnée douanière non sourcée ;
3. les tests unitaires ne dépendent plus du réseau ;
4. les versions de dépendances du banc de test sont reproductibles ;
5. les divergences produit sont arbitrées ;
6. la suite complète passe de manière répétée dans un ordre aléatoire et standard ;
7. le retrait de `continue-on-error` fait l’objet d’une PR distincte et finale.
