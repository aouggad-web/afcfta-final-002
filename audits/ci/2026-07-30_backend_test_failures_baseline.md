# Audit initial — 91 échecs backend masqués par la CI

Date : 2026-07-30  
Branche : `codex/backend-ci-91-failures-audit`  
Base : fusion de la PR #332 (`d1e022c59f500431b7d1ebd98be1b52aef2a1a2c`)

## Objet

Ce chantier est séparé de la PR #332. Il vise à rendre la suite backend exploitable comme garde-fou de non-régression avant de supprimer `continue-on-error: true` dans `.github/workflows/ci.yml`.

Aucune correction de production, aucune donnée douanière et aucun comportement du calculateur ne sont modifiés dans cette première étape.

## Baseline reproductible

Les exécutions CI précédant et accompagnant la PR #332 montrent une baseline stable de 91 échecs :

- run #1158 : 91 failed, 1536 passed, 255 skipped ;
- run #1162 : 91 failed, 1539 passed, 255 skipped ;
- run #1175 : 91 failed, 1544 passed, 255 skipped ;
- les trois tests ajoutés par la PR #332 passent ;
- la différence de tests réussis correspond aux tests ajoutés depuis la baseline, sans réduction des 91 échecs historiques ;
- les 91 échecs sont donc antérieurs à #332.

Le workflow actuel exécute :

```yaml
python -m pytest backend/tests/ -v --tb=short --ignore=backend/tests/test_notifications.py
continue-on-error: true
```

Cette configuration permet au job `backend-tests` d’être affiché en succès alors que pytest retourne un code d’échec.

## Classification initiale

### A. Tests hérités `enhanced_v2` devenus incompatibles

Symptômes observés :

- attentes `data_format == "enhanced_v2"` alors que les registres courants exposent un autre format ;
- attentes de sous-positions nationales pour 52 ou 53 pays ;
- attentes de volumes artificiellement homogènes (`>= 16000`, `>= 5000`) ;
- script `scripts.upgrade_to_enhanced_v2` supprimé mais encore importé par les tests.

Fichiers principalement concernés :

- `backend/tests/test_cemac_tariff_system.py` ;
- `backend/tests/test_code_quality_refactoring.py` ;
- `backend/tests/test_regional_data.py`.

Décision attendue : déterminer d’abord si la migration a été abandonnée ou laissée inachevée, puis remplacer les hypothèses globales par les statuts de preuve actuels (`DOCUMENTED`, `PARTIAL`, `NOT_AVAILABLE`, etc.) et tester les données réellement disponibles par pays.

### B. Tests de formalités administratives fondés sur des données non prouvées ou anciennes

Symptômes observés :

- obligation d’avoir au moins cinq codes documentaires par pays ;
- exigence d’un document pour chaque ligne tarifaire ;
- attentes systématiques de codes génériques (`IMPDEC`, `ECTN`, `910`, `ARMAUTH`, etc.) ;
- erreurs `KeyError` sur `hs6` ou `tariff_lines` lorsque le format réel ne contient pas ces champs.

Fichier principalement concerné :

- `backend/tests/test_north_africa_tariff_system.py`.

Décision attendue : supprimer ou réécrire les assertions qui imposent des formalités non sourcées. Une absence de preuve doit rester `NOT_AVAILABLE`, jamais être convertie en document supposé.

### C. Tests non hermétiques dépendant du réseau ou de l’état externe

Symptômes observés :

- taux de change réel retourné par `open_er_api` alors que le test attend `None` ou un fournisseur simulé ;
- comportement variable selon la disponibilité réseau et le cache.

Fichiers concernés :

- `backend/tests/test_currencies_exchange_rates.py` ;
- `backend/tests/test_tax_computation.py`.

Décision attendue : isoler les fournisseurs externes par injection/mocks déterministes et séparer tests unitaires et tests d’intégration réseau.

### D. Attentes statistiques ou fiscales obsolètes

Symptômes observés :

- année OEC attendue à 2024 alors qu’une route conserve 2018 ;
- Niger attendu à 18 % de TVA alors que le registre national documenté expose 19 % ;
- statuts de collecte UEMOA attendus `pending` alors que certaines sources ont été traitées.

Fichiers concernés :

- `backend/tests/test_oec_default_year.py` ;
- `backend/tests/test_uemoa_source_collection.py`.

Décision attendue : vérifier la source officielle et la date d’effet avant de modifier le test ou la donnée. Le cas Niger doit être présenté comme une situation nationale distincte, jamais comme un taux harmonisé UEMOA de 19 %.

### E. Contrats applicatifs possiblement rompus

Symptômes observés :

- `country_risk_service` retourne `A4` alors qu’un test attend `B` ;
- route de recherche SH6 sans attribut `get_tariff_line` attendu par le test ;
- requête courte non rejetée comme prévu ;
- multiplicateur fret ne produit plus le facteur attendu.

Fichiers concernés :

- `backend/tests/test_country_risk_service.py` ;
- `backend/tests/test_hs6_smart_search_route_unit.py` ;
- `backend/tests/test_update_bulk_freight_indices.py`.

Décision attendue : comparer le comportement actuel au contrat produit avant de choisir entre correction du code et mise à jour du test.

### F. Dépendances d’environnement et compatibilité du banc de test

Copilot a reproduit localement des défauts supplémentaires impliquant `bs4`, `redis` et une incompatibilité `motor` / `pymongo`. Ces observations ne figurent pas dans les 91 échecs du run CI #1175 et sont suivies séparément pour ne pas les confondre avec la baseline métier.

Décision attendue : verrouiller les versions, inventorier les dépendances optionnelles et ajouter un contrôle d’import/compatibilité distinct.

## Matrice exhaustive livrée

La liste complète des 91 tests, leur catégorie et l’action proposée est disponible dans :

- `audits/ci/2026-07-30_backend_test_failures_matrix.csv`.

La synthèse révisée intégrant les remarques Copilot est disponible dans :

- `audits/ci/2026-07-30_backend_test_failures_classification_v2.md`.

Répartition :

- A : 31 tests ;
- B : 48 tests ;
- C : 3 tests ;
- D : 5 tests ;
- E : 4 tests ;
- total : 91 tests.

## Méthode de traitement

1. Produire la liste exhaustive des 91 tests avec catégorie, cause racine, propriétaire logique et décision proposée. **Terminé.**
2. Exécuter chaque groupe de tests de manière isolée pour détecter les dépendances d’ordre et les effets de singleton/cache.
3. Séparer :
   - tests obsolètes à réécrire ;
   - tests non hermétiques à isoler ;
   - erreurs de données à vérifier sur sources officielles ;
   - véritables défauts applicatifs à corriger.
4. Ajouter un test ciblé pour chaque correction réelle.
5. Réduire progressivement le nombre d’échecs sans masquer les résultats.
6. Retirer `continue-on-error` uniquement lorsque la suite bloquante est déterministe et alignée sur les contrats actuels.

## Garde-fous

- ne pas inventer de sous-positions nationales ;
- ne pas inventer de formalités ou certificats ;
- ne pas remplacer une absence par zéro ;
- ne pas modifier une taxe sans source officielle et date d’effet ;
- ne pas rendre un test vert en affaiblissant une exigence juridique valide ;
- documenter tout test supprimé ou remplacé avec sa justification.

## Livrables

- matrice exhaustive des 91 échecs : **livrée** ;
- classification révisée après revue Copilot : **livrée** ;
- lots de correction indépendants par catégorie : à exécuter ;
- séparation tests unitaires / intégration / données officielles : à exécuter ;
- CI affichant explicitement le nombre réel d’échecs : à exécuter ;
- suppression finale de `continue-on-error` après validation : à exécuter.

## Statut

- PR #332 : fusionnée ;
- dette backend : confirmée comme préexistante ;
- matrice des 91 échecs : complète ;
- prochaine phase : exécution isolée et correction du lot 1 sans changement de données non sourcé.
