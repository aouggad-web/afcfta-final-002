# Checklist Sécurité ZLECAf

## Statut des corrections (à mettre à jour manuellement)

### Phase 1 — Git & Secrets
- [ ] Historique Git scanné pour secrets exposés
- [ ] `.env` retiré de l'historique avec `git-filter-repo`
- [ ] `.env` ajouté au `.gitignore`
- [ ] Credentials Gmail révoqués et régénérés
- [ ] Webhook Slack révoqué et régénéré
- [ ] Mot de passe MongoDB changé
- [ ] `git push --force --all` exécuté après purge

### Phase 2 — Nettoyage racine
- [ ] ~80 fichiers parasites supprimés (for, df, except, etc.)
- [ ] Données CSV/JSON/XLSX déplacées dans `data/`
- [ ] Imports Python mis à jour pour les nouveaux chemins
- [ ] Crawlers TypeScript déplacés dans `engine/crawlers/`

### Phase 3 — Structure
- [ ] `backup_before_github_merge/` supprimé
- [ ] `src/components/trade/` (doublon) supprimé
- [ ] Structure de dossiers propre créée
- [ ] Scripts utilitaires dans `scripts/`

### Phase 4 — Hardening Backend
- [ ] `allow_origins=["*"]` remplacé par liste explicite
- [ ] `SecurityHeadersMiddleware` ajouté à `main.py`
- [ ] Modèles Pydantic stricts appliqués aux routes
- [ ] Rate limiting installé (`pip install slowapi`)
- [ ] `.env.example` mis à jour et propre
- [ ] Tests de régression exécutés après modifications

### Vérification finale
- [ ] `docker-compose up --build` fonctionne
- [ ] `/api/health` renvoie 200
- [ ] Calcul de tarif KE→GH + code 080300 fonctionne
- [ ] Aucune clé API dans les logs
