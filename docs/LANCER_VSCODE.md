# Lancer le module Opportunités dans VS Code (avec OEC réel)

Guide pas-à-pas pour exécuter backend + frontend en local dans VS Code. En local
ta machine a accès à Internet → l'**OEC répond** (contrairement au bac à sable).

## Prérequis
- Python 3.11+, Node 18+ et Yarn, l'extension **Python** de VS Code
  (optionnel : **REST Client** pour `requests.http`).

## 1. Ouvrir le projet
```bash
git fetch origin
git checkout claude/opportunites-scenario-s2   # ou main si la PR #182 est mergée
```
Puis **File → Open Folder** sur le dossier du repo.

## 2. Backend (terminal 1)
```bash
python -m venv .venv
source .venv/bin/activate            # Windows : .venv\Scripts\activate
pip install -r backend/requirements.txt
```
VS Code : `Ctrl+Shift+P` → **Python: Select Interpreter** → choisis `.venv`.

Crée un **`.env` à la racine** (copie de `.env.example`) avec au minimum :
```ini
SECRET_KEY=une-chaine-aleatoire-d-au-moins-32-caracteres
PUBLIC_DATA_ACCESS=true
# OEC : rien si tier gratuit ; sinon ton token :
OEC_API_TOKEN=ton_token_oec
```
Lancer :
```bash
cd backend
uvicorn server:app --reload --port 8000
```

## 3. Frontend (terminal 2 — split terminal)
```bash
cp frontend/.env.example frontend/.env      # contient VITE_BACKEND_URL=http://localhost:8000
cd frontend
yarn install
yarn start                                   # http://localhost:5000
```

## 4. Vérifier l'OEC
- Ouvre `requests.http` (à la racine) et clique **Send Request** sur *Diagnostic OEC* →
  attendu `"reachable": true`.
- Ou dans le navigateur : http://localhost:5000 → onglet **Opportunités** →
  **Trouver des marchés / S2 / S3**.

## 5. Fichiers `.vscode/` (debug + tests)
Le dossier `.vscode/` est **git-ignoré** par le projet : crée-le localement et colle
ces fichiers.

`.vscode/launch.json` — debug du backend (breakpoints dans les services) :
```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Backend (uvicorn)",
      "type": "debugpy",
      "request": "launch",
      "module": "uvicorn",
      "args": ["server:app", "--reload", "--port", "8000"],
      "cwd": "${workspaceFolder}/backend",
      "envFile": "${workspaceFolder}/.env",
      "console": "integratedTerminal"
    }
  ]
}
```

`.vscode/settings.json` — interpréteur + tests pytest :
```json
{
  "python.defaultInterpreterPath": "${workspaceFolder}/.venv/bin/python",
  "python.testing.pytestEnabled": true,
  "python.testing.unittestEnabled": false,
  "python.testing.pytestArgs": ["backend/tests"]
}
```

`.vscode/tasks.json` — lancer backend/frontend depuis la palette (`Run Task`) :
```json
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "Backend: uvicorn",
      "type": "shell",
      "command": "${workspaceFolder}/.venv/bin/python -m uvicorn server:app --reload --port 8000",
      "windows": { "command": "${workspaceFolder}\\.venv\\Scripts\\python.exe -m uvicorn server:app --reload --port 8000" },
      "options": { "cwd": "${workspaceFolder}/backend" },
      "isBackground": true,
      "problemMatcher": []
    },
    {
      "label": "Frontend: yarn start",
      "type": "shell",
      "command": "yarn start",
      "options": { "cwd": "${workspaceFolder}/frontend" },
      "isBackground": true,
      "problemMatcher": []
    }
  ]
}
```
- **Debug** : onglet *Run and Debug* → *Backend (uvicorn)* → F5.
- **Tests** : onglet *Testing* → exécute les ~50 tests `pytest`.
- **Tâches** : `Ctrl+Shift+P` → *Tasks: Run Task* → *Backend* / *Frontend*.

## Bonus — données World Bank (facultatif)
```bash
cd backend
python -m etl.fetch_wb_gdp        # active le niveau L3 des besoins (PIB/hab)
python -m etl.fetch_wb_reserves   # réserves de change + couverture d'import
```
