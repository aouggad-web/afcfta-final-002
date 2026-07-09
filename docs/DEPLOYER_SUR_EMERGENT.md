# Déployer / synchroniser sur Emergent

**Principe : GitHub est la source de vérité.** Emergent ne doit ni analyser ni
auditer sa copie locale par rapport au dépôt — il applique la branche GitHub
telle quelle. Toute modification faite directement dans le shell Emergent et
non poussée sur GitHub est écrasée par la synchronisation. C'est voulu : ça
élimine définitivement les déploiements à copie partielle/périmée (cause du
bug `No module named 'services.regional_blocs'` vu en production).

Seule exception légitime : `backend/data/news_cache.json` est un cache
régénéré automatiquement par `etl/news_aggregator.py` — le perdre au reset
n'a aucune conséquence, il se reconstruit tout seul à la prochaine requête.

## Procédure définitive (une commande, mode supervisor)

Emergent gère les services via **supervisord** (backend `uvicorn --port 8001`,
frontend **`vite preview --port 3000`** qui sert `frontend/build`). Dans ce
mode, la synchronisation doit TOUJOURS reconstruire le frontend et redémarrer
par supervisord. `sync_emergent.sh` le détecte automatiquement — une seule
commande dans le **Shell Emergent** :

```bash
BRANCH=main bash sync_emergent.sh
```

Quand `supervisorctl` est présent, le script :
- **reconstruit toujours** le frontend (`yarn build`) — `SKIP_BUILD` est
  ignoré, car `vite preview` sert `frontend/build` (ignoré par git) : sans
  rebuild, **les mises à jour ne s'affichent jamais** ;
- **redémarre par supervisord** (`supervisorctl restart all`) — jamais de
  `pkill` ni de `start.sh`, donc aucun conflit de port et le terminal n'est
  pas bloqué.

Ne lancez donc PAS `start.sh` sous Emergent : supervisord s'en charge.

### Variables d'environnement à fixer UNE FOIS (profil supervisord)

- `BACKEND_PORT=8001` / `FRONTEND_PORT=3000` : ports imposés par l'ingress
  Kubernetes. **À fixer dans l'environnement Emergent, pas en patchant
  `vite.config.js`/`package.json`** — ces fichiers lisent désormais
  `VITE_PORT`/`PORT`/`VITE_BACKEND_URL`, donc un `git reset` ne les écrase
  plus jamais fonctionnellement.
- Le rechargement HMR est déjà neutralisé par `vite preview` (aucun websocket
  HMR). `VITE_HMR=off` reste disponible pour le mode `vite` dev si un jour
  vous l'utilisez (voir section ci-dessous).

### Bug « retour au dashboard / rechargement chaque minute » — corrigé

Cause : derrière l'ingress Kubernetes, le websocket HMR (rechargement à chaud)
du **serveur de dev Vite** tentait de se connecter au port interne de Vite, que
l'ingress ne route pas ; la connexion était coupée au bout de ~60 s et le client
Vite **rechargeait toute la page**. Comme la navigation entre modules est gérée
en mémoire (pas dans l'URL), chaque rechargement renvoyait au dashboard.

Réglé de DEUX façons complémentaires :

1. **Emergent sert l'app via `vite preview`** (et non le serveur de dev) :
   `vite preview` n'a **aucun websocket HMR** — plus aucune boucle de
   rechargement possible. C'est le réglage retenu côté supervisord.
2. **Filet de sécurité dans le dépôt**, utiles hors `vite preview` :
   - `vite.config.js` lit la config HMR depuis l'environnement : `VITE_HMR=off`
     désactive HMR ; `VITE_HMR_CLIENT_PORT=443 VITE_HMR_PROTOCOL=wss` le fait
     passer par l'ingress.
   - l'onglet actif est persisté en `sessionStorage` : même si un rechargement
     survient pour une autre raison (service worker...), l'utilisateur revient
     sur son module au lieu du dashboard.

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
5. **Reconstruit** le frontend (`yarn build` → `frontend/build`). Sous
   supervisord, toujours ; en dev local seulement, `SKIP_BUILD=1` le saute.
6. **Redémarre** : `supervisorctl restart all` si supervisord est présent,
   sinon arrêt des serveurs de dev périmés (`pkill`).

### Pourquoi le `git reset --hard` ne casse plus la config de ports Emergent

Avant cette session, `vite.config.js` codait en dur `port: 5000` et le proxy
`http://localhost:8000`, et `package.json` codait `--port 5000` dans son
script `start` — Emergent devait donc **patcher ces fichiers localement**
pour tenir sur ses ports imposés (ex. 3000 / 8001), et chaque synchronisation
écrasait ce patch. Ces trois fichiers lisent maintenant les ports depuis
l'environnement (`VITE_PORT`/`PORT`/`FRONTEND_PORT`/`BACKEND_PORT`/
`VITE_BACKEND_URL`), avec les mêmes défauts qu'avant si rien n'est défini —
la configuration de ports d'Emergent devient une variable d'environnement
persistante, plus un patch de fichier voué à disparaître au prochain reset.

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

## Ce que cette synchronisation apporte (session du 2026-07-09)

- **Dimensionnement conteneurs sur valeur FOB** : le coût rendu (S1/S2/S4 +
  Opportunités IA) ne facture plus systématiquement UN SEUL conteneur 20′ —
  le poids est estimé depuis la valeur FOB, le nombre et le type de
  conteneurs (20′/40′) en découlent, le fret est multiplié en conséquence.
- **Route terre+mer pour les origines enclavées** : un pays enclavé
  *exportateur* (ex. Éthiopie) n'était comparé qu'à l'avion, faute de route
  terre→port→mer symétrique et faute de corridor Éthiopie-Djibouti dans le
  registre PIDA. Les deux sont corrigés (`_land_then_sea_option()` + 2
  corridors réels ajoutés) : ETH→KEN passe de 35 665 $ (avion) à 1 362 $
  (rail+mer via Djibouti).
- **Indice valeur/poids à cours mondiaux réels** : 21 cours réels, datés et
  sourcés (ICE, LME, CBOT, COMEX, Platts, Bursa Malaysia, SICOM, Mombasa)
  remplacent l'estimation par chapitre SH quand un cours existe pour le
  produit — `classification_source: "cours_mondial"` vs `"estimation_chapitre"`.
  Sert aussi de repère grossier de négociation d'achat (`negotiation_reference`,
  avec garde-fou explicite : cours de référence pour un grade standard, pas
  un devis garanti).
- **Rafraîchissement quotidien automatique des cours** : nouveau workflow
  GitHub Actions `update_market_prices` (13 contrats, jours ouvrés 05:30 UTC)
  écrit `data/json/cours_mondiaux.json`, prioritaire sur les valeurs
  statiques dans `shipment_estimator`. Rien à faire côté Emergent — c'est un
  fichier de données synchronisé comme les autres par `sync_emergent.sh`.

## Démarrer après synchronisation

- **Sous Emergent (supervisord)** : rien à lancer, `sync_emergent.sh` a déjà
  redémarré les services. Vérifier : `supervisorctl status`.
- **Dev local** (hors supervisord) :

  ```bash
  BACKEND_PORT=8001 FRONTEND_PORT=3000 VITE_HMR=off bash start.sh
  # ou mono-processus (FastAPI sert l'API ET le frontend buildé) :
  cd backend && python -m uvicorn server:app --host 0.0.0.0 --port "${BACKEND_PORT:-8000}"
  ```

## Vérifier que tout est branché

```bash
curl -s http://localhost:${BACKEND_PORT:-8000}/api/reports/health       # sources du moteur
curl -s http://localhost:${BACKEND_PORT:-8000}/api/reports/oec-health    # canal OEC gratuit
```

- `oec-health` → `channels.statistics_free.reachable: true` : l'OEC gratuit
  répond (aucun token requis). Emergent a le réseau ouvert, contrairement aux
  bacs à sable.

## Quelle branche déployer ?

- **`main`** : toutes les améliorations (PR #222 comprise) y sont mergées.
  Déployer avec `BRANCH=main bash sync_emergent.sh`.
- Une branche de travail en cours ne se déploie que pour tester une PR non
  encore mergée : `BRANCH=<nom-de-branche> bash sync_emergent.sh`.
