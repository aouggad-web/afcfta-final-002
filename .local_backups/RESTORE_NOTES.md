# Sauvegarde locale avant "Pull from GitHub"

Date : 2026-06-07
Commit git de référence (HEAD avant pull) : `a5f30a2aa72b3aad280b3e45fce1439edb52292c`

## Fichiers physiquement sauvegardés (dans /app/.local_backups/)
Ces fichiers ne sont PAS suivis par git → cette copie est leur seule sauvegarde :
- `backend.env.bak`   → restaurer vers `/app/backend/.env`   (contient SECRET_KEY, MONGO_URL, DB_NAME)
- `frontend.env.bak`  → restaurer vers `/app/frontend/.env`  (REACT_APP_BACKEND_URL, REACT_APP_API_KEY)
- `auth.py.bak`       → restaurer vers `/app/backend/auth.py` (aussi suivi par git)
- `index.js.bak`      → restaurer vers `/app/frontend/src/index.js` (aussi suivi par git)

## Données volumineuses (déjà dans git, pas de copie disque nécessaire)
- `/app/backend/data/` (788 fichiers JSON/CSV) — suivi git
- `/app/engine/output/` (218 fichiers .jsonl) — suivi git

## Procédure de restauration APRÈS un pull GitHub qui écrase des données

1. Restaurer les .env (priorité absolue) :
   cp /app/.local_backups/backend.env.bak  /app/backend/.env
   cp /app/.local_backups/frontend.env.bak /app/frontend/.env

2. Restaurer les données / auth depuis le commit de référence si écrasés par des dummy data :
   cd /app
   git checkout a5f30a2aa72b3aad280b3e45fce1439edb52292c -- backend/data
   git checkout a5f30a2aa72b3aad280b3e45fce1439edb52292c -- engine/output
   git checkout a5f30a2aa72b3aad280b3e45fce1439edb52292c -- backend/auth.py
   git checkout a5f30a2aa72b3aad280b3e45fce1439edb52292c -- frontend/src/index.js

3. Redémarrer les services :
   sudo supervisorctl restart backend frontend
