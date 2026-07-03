# Déployer / synchroniser sur Emergent

Toutes les améliorations (module Opportunités S1→S4, régime tarifaire réel,
OEC sans token, macro World Bank) vivent dans le dépôt GitHub. Emergent déploie
**depuis GitHub** : pour que l'application affiche ces améliorations, le
déploiement doit exécuter la **dernière version du dépôt**, en entier.

> ⚠️ Le bug vu en production — `No module named 'services.regional_blocs'` —
> ne vient PAS du code (ce module est présent et testé). Il vient d'un
> déploiement Emergent qui tournait une **copie partielle / périmée** du dépôt.
> La synchronisation ci-dessous le corrige définitivement.

## Procédure (une commande)

Dans le **Shell Emergent** du projet :

```bash
bash sync_emergent.sh
```

Le script (`sync_emergent.sh`, à la racine) :

1. **Récupère** la branche courante depuis `origin` et aligne l'arbre
   exactement dessus (`git reset --hard` — supprime tout fichier périmé).
2. **Vérifie** que les modules critiques sont présents (dont `regional_blocs`,
   les barèmes ZLECAf, le moteur Opportunités, les datasets World Bank). Il
   **refuse de continuer** si un fichier manque — plus de code partiel silencieux.
3. **Réinstalle** les dépendances backend.
4. **Contrôle les imports** du moteur (échoue tôt et clairement si un import casse).
5. **Reconstruit** le frontend (Vite → `frontend/build`).
6. **Arrête** les serveurs périmés pour un redémarrage propre.

Pour forcer une branche précise (ex. après merge sur `main`) :

```bash
BRANCH=main bash sync_emergent.sh
```

## Démarrer après synchronisation

```bash
# Développement (deux serveurs, aperçu web) :
bash start.sh                    # backend 8000 + Vite 5000

# Production mono-processus (FastAPI sert l'API ET le frontend buildé) :
cd backend && python -m uvicorn server:app --host 0.0.0.0 --port 5000
```

## Vérifier que tout est branché

```bash
curl -s http://localhost:8000/api/reports/health       # sources du moteur
curl -s http://localhost:8000/api/reports/oec-health    # canal OEC gratuit
```

- `oec-health` → `channels.statistics_free.reachable: true` : l'OEC gratuit répond
  (aucun token requis). Emergent a le réseau ouvert, contrairement aux bacs à sable.
- Le module **Opportunités** expose S1 (transformation), S2 (export direct),
  S3 (besoin national), S4 (opportunités d'importation) + le rapport bilatéral
  ultra-fin. Le tarif applique la réciprocité algérienne (9 partenaires actifs) ;
  le PIB/hab (L3), les réserves et la couverture des importations viennent du
  module Profils Pays et des datasets World Bank committés.

## Quelle branche déployer ?

- Tant que la **PR #187** n'est pas mergée : déployer la branche
  `claude/setup-github-cli-EngUf` (elle contient tout).
- Après merge : déployer `main` (`BRANCH=main bash sync_emergent.sh`).
