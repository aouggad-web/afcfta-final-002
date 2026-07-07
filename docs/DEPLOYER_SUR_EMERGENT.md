# Déployer / synchroniser sur Emergent

**Principe : GitHub est la source de vérité.** Emergent ne doit ni analyser ni
auditer sa copie locale par rapport au dépôt — il applique la branche GitHub
telle quelle. Toute modification faite directement dans le shell Emergent et
non poussée sur GitHub est écrasée par la synchronisation. C'est voulu : ça
élimine définitivement les déploiements à copie partielle/périmée (cause du
bug `No module named 'services.regional_blocs'` vu en production).

## Procédure (une commande)

Dans le **Shell Emergent** du projet :

```bash
BRANCH=claude/setup-github-cli-EngUf bash sync_emergent.sh
```

Le script (`sync_emergent.sh`, à la racine) :

1. **Applique** `origin/<branche>` telle quelle : `git reset --hard` sur les
   fichiers suivis + `git clean -fd` sur les fichiers non suivis périmés
   (les `.env`, `node_modules` et venv locaux sont préservés — jamais du code).
   Aucune comparaison, aucun audit de l'état local antérieur.
2. **Vérifie** que la copie fraîchement appliquée est complète : modules du
   moteur ET fichiers de la session courante (réciprocité ZLECAf, calculateur
   corrigé, données tarifaires enrichies). **Refuse de continuer** si un
   fichier manque.
3. **Réinstalle** les dépendances backend.
4. **Contrôle imports + données** de la copie appliquée : échoue clairement si
   Emergent se retrouve avec les anciennes versions des fichiers de données
   (préférences tunisiennes absentes, TVA des pays WITS absente, registre de
   réciprocité incohérent, Ghana illisible).
5. **Reconstruit** le frontend (Vite → `frontend/build`).
6. **Arrête** les serveurs périmés pour un redémarrage propre.

## Ce que cette synchronisation apporte (session du 2026-07-06)

- **Réciprocité ZLECAf généralisée** : une préférence n'est accordée que si le
  pays de destination applique *réellement* l'accord (instrument douanier daté
  ou participation Guided Trade Initiative), pas sur simple ratification —
  le principe de la circulaire DGD 482/2024 algérienne, étendu aux 54 pays.
- **Calculateur corrigé** : les codes TVA `IVA`/`VAT` sont enfin reconnus
  (Angola, Mozambique, São Tomé, Zimbabwe, Maurice, Malawi, Soudan,
  Seychelles, Zambie) ; les 13 pays WITS (70 744 positions) sont désormais
  lisibles par le service de données crawlées ; la Tunisie récupère ses
  17 512 préférences tarifaires par pays et ses formalités ; le Ghana
  récupère ses données authentiques (bug de chemin).
- **13 pays WITS enrichis** : TVA nationale sourcée pays par pays + surcharges
  de taux par produit, chacune tracée `classification_source: "loi"` (code SH
  cité par le texte réglementaire) ou `"estimation_ia"` (correspondance SH
  établie techniquement à partir du produit nommé par la loi).
- **Module Opportunités branché** : économies tarifaires réelles (même moteur
  que le Calculateur, réciprocité incluse) et profil logistique réel (coût de
  fret multimodal, zones franches) dans la comparaison de pays et les
  opportunités par pays ; suppression du résumé LLM fabriqué (code mort).

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

- `oec-health` → `channels.statistics_free.reachable: true` : l'OEC gratuit
  répond (aucun token requis). Emergent a le réseau ouvert, contrairement aux
  bacs à sable.

## Quelle branche déployer ?

- Tant que la **PR #222** n'est pas mergée : déployer la branche
  `claude/setup-github-cli-EngUf` (elle contient tout, y compris les
  améliorations des PR précédentes déjà mergées sur `main`).
- Après merge : déployer `main` (`BRANCH=main bash sync_emergent.sh`).
