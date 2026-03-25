# 🔒 Checklist de Sécurité — ZLECAf Trade Calculator

## ✅ Actions Complétées

- [x] Fichiers parasites supprimés de la racine
- [x] Données organisées dans data/{csv,json,xlsx}/
- [x] .gitignore renforcé
- [x] .env.example documenté
- [x] Structure de dossiers propre

## ⚠️ Actions Requises (Manuelles)

### Après le merge sur GitHub :

1. **Gmail/SMTP**
   - [ ] Révoquer l'App Password actuel
   - [ ] Créer un nouveau App Password
   - [ ] Mettre à jour le .env de production

2. **Slack Webhook**
   - [ ] Regénérer l'URL dans Settings > Incoming Webhooks
   - [ ] Mettre à jour le .env de production

3. **MongoDB Atlas**
   - [ ] Changer le mot de passe de l'utilisateur DB
   - [ ] Mettre à jour le MONGO_URL en production

4. **Déploiement**
   - [ ] Redéployer le service avec les nouveaux credentials

## 🛡️ Recommandations Futures

- [ ] Activer le rate limiting avec slowapi
- [ ] Implémenter le CSP (Content Security Policy) strict
- [ ] Ajouter des tests de sécurité automatisés
- [ ] Configurer les alertes de sécurité GitHub
