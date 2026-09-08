# Correctifs d'audit — lot 1

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
