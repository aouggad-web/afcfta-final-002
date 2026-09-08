# Correctifs d'audit — lots 1 à 3

Base : 8e1db7055b2f200030c45c6f449df21f3071a9bb.

## Changements

- Retrait des taux forfaitaires par chapitre des endpoints v2.
- `/api/v2/calculations` et `/api/v2/bulk/tariff-calculations` : HTTP 503 avec le code `VERIFIED_TARIFF_PROVIDER_REQUIRED`. Ces endpoints seront réactivés après raccordement à des lignes tarifaires vérifiées côté serveur. Une provenance déclarée par le client n'est pas une preuve.
- Résumés tarifaires mobiles : valeurs nulles et `NOT_AVAILABLE`, sans préférence automatique. Nouveau namespace de cache pour exclure les anciennes réponses forfaitaires.
- Fichiers frontend : contrôle de parenté du chemin résolu, couvrant les dossiers frères et liens symboliques hors racine.
- React : repli vers le calculateur legacy uniquement si la route authentique est absente (404 standard). Refus, quotas, données manquantes et pannes restent des erreurs.

Aucune modification des jeux de données, des taux nationaux ou des colonnes du calculateur principal.

## Validation

17 tests backend ciblés passent avec FastAPI 0.110.1 / Starlette 0.37.2, via pytest :

```
python -m pytest backend/tests/test_api_v2_calculations.py backend/tests/test_mobile_tariff_provenance.py backend/tests/test_static_paths.py
```

Les tests HTTP utilisent les routers réels sur une application FastAPI de test. Ils ne chargent pas le serveur complet ni ses bases. Les sentinelles de test ne sont pas des données douanières de production.

19 tests frontend `calculatorFallback.test.js` passent et couvrent la route absente, les erreurs de données, 401/403/429/5xx, les interruptions réseau et les timeouts. La CI doit confirmer le build React et les suites complètes avant fusion.

## Impact et retour arrière

Les clients des deux calculs v2 doivent traiter le 503 ; les clients mobiles doivent afficher l'indisponibilité pour les champs nuls. La recherche et le calculateur principal restent disponibles selon leurs droits et sources existants.

Ne pas réactiver les anciennes estimations pour contourner une indisponibilité. En cas de rollback d'infrastructure, conserver ces endpoints désactivés jusqu'à correction.

## Lots suivants

1. Validation du moteur canonique : taux/quantités/assiettes manquants, dépendances, unités et devises ; ne pas produire de total complet si les entrées sont insuffisantes.
2. Position nationale exacte et réponse de sélection explicite pour les SH6 ambigus, sur l'ensemble des chemins et des replis.
3. DAPS appliqué séparément par régime et convergence des moteurs PostgreSQL/JSON.
4. Identité et quotas homogènes ; configuration proxy/HTTPS/middlewares bloquante ; reprise des webhooks après interruption.
5. Recomposition de la couverture pays par pays à partir des sources officielles et des données réellement servies.

Ce lot réduit des risques confirmés ; il ne vaut pas validation globale de mise en production.

## Lot 2 — validation du moteur canonique

`CalculationUnavailable` interrompt le calcul avant publication d'un total si les entrées indispensables sont absentes : taux/quantités non finis ou négatifs, taux manquant, mesures absentes/dupliquées, dépendances d'assiette non résolues, source manquante ou synthétique. Les assiettes FOB/OTHER ne sont plus remplacées implicitement par CAF. Un droit spécifique exige un montant, une quantité et une unité monétaire compatible ; une préférence spécifique non représentable par le schéma est refusée. Les vrais taux zéro restent valides.

Validation : 29 nouveaux tests de garde-fous et les 4 tests arithmétiques DZA existants réussissent. Ce résultat valide les contrats et la non-régression arithmétique ; il ne revalide pas juridiquement les données de référence DZA.

Ce moteur reste distinct du calculateur principal et de PostgreSQL. Le raccordement à une source serveur, les positions ambiguës et la convergence des chemins restent nécessaires. Les endpoints v2 suspendus ne sont pas réactivés par ce lot.

## Lot 3 — DAPS et sélection nationale

Le DAPS reste dans le scénario NPF. Une exemption documentée est transmise séparément au scénario ZLECAf ; les assiettes dépendantes, dont la TVA, sont recalculées. Le détail conserve les montants et taux propres aux deux régimes.

Le service de calcul authentique refuse les positions nationales absentes et les SH6 à plusieurs enfants, avec une erreur structurée et les candidats (maximum 200 codes dans la réponse). Le calculateur principal utilise également une sélection exacte sur ses données crawled, au lieu de prendre la première ligne par préfixe. Un enfant unique peut être sélectionné ; aucun suffixe national n'est inventé. Les SH2/SH4 servent à naviguer et ne sont plus acceptés comme codes de calcul. Un SH6 sans énumération nationale conserve sa politique existante de disponibilité, sans être transformé en position nationale.

Impact : un SH6 auparavant calculé arbitrairement peut maintenant demander une sélection. Le message est rendu lisiblement dans le frontend. Les routes de calcul PostgreSQL directes et les autres replis ETL restent à harmoniser ; cette correction ne certifie pas tous les chemins.

Validation du lot : 14 tests de sélection, dont 2 sur le service authentique réel avant repli, 6 tests DAPS et 15 tests fiscaux préexistants passent. Le test préexistant de change hors ligne n'est pas exécuté dans la copie locale partielle, faute des modules/données currencies ; aucun test n'est retiré ou désactivé dans le dépôt. La CI le conserve.

## Lot 4 — refus des types de taux non pris en charge

Le moteur canonique accepte explicitement les types AD_VALOREM, SPECIFIC, MIXED et EXEMPT. ALTERNATIVE est refusé avec CalculationUnavailable, même lorsque ses composantes sont renseignées : aucune méthode alternative n'est implémentée et un montant nul silencieux serait trompeur. Deux tests couvrent ce refus en NPF et ZLECAf. Les 31 tests de garde-fous et les 4 tests DZA passent localement.

La CI du lot 3 a validé le lint et le build frontend, mais reste bloquante côté backend : 7 échecs, 2182 succès et 339 tests ignorés. Quatre échecs concernent des appels SH6 devenus ambigus ; trois concernent les méthodes nationales ETH/CMR/TUN après sélection nationale. Les attentes fiscales ne doivent pas être modifiées sans inspection des lignes sources. Les gros fichiers de données nationaux n'ont pas pu être récupérés par le connecteur dans cette session. Aucun de ces tests n'est supprimé, désactivé ou affaibli dans ce lot. La PR reste en brouillon et ne doit pas être fusionnée en l'état.

## Lot 5 — régressions CI et séparation des sources

Le dépôt complet a été récupéré : le blocage d'accès aux gros fichiers est levé. Les tests CMR/TUN/DZA/ZAF utilisent maintenant les positions nationales présentes dans les données, au lieu d'un SH6 ambigu. Deux tests HTTP supplémentaires vérifient le refus 422 et les candidats pour DZA et ZAF.

Pour ETH/02011000000, le fichier crawled identifie D2R comme « COMESA Preferential Duty ». Le normaliseur exclut les colonnes préférentielles du cumul des taxes ordinaires, tout en conservant les données brutes. Le calcul n'invente plus de PRCT à partir de l'agrégat other_taxes_rate du parent SH6 lorsque la position nationale dispose de son propre détail de taxes.

Le test national ETH contrôle DD=350, TVA=202,50 et WHR=30 pour une valeur de 1 000, soit 582,50 d'après cette ligne du dépôt. Un test distinct conserve le contrôle de la cascade avec SR du miroir SH6 (737,75), sans confondre les deux sources. Ces montants sont des assertions de cohérence des données existantes ; ils ne certifient pas leur exhaustivité ni leur actualité juridique. Aucun fichier tarifaire ni taux source n'est modifié.
