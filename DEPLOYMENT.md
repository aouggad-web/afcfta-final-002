# 🐳 Guide de Déploiement Docker

## Prérequis
- Docker 20.10+
- Docker Compose 2.0+
- 2GB RAM minimum
- 10GB espace disque disponible

## Installation rapide

### 1. Cloner le repository
```bash
git clone https://github.com/aouggad-web/afcfta-final-001.git
cd afcfta-final-001
```

### 2. Configurer les variables d'environnement
```bash
cp .env.example .env
# Éditer .env avec vos credentials
nano .env
```

### 3. Démarrer l'application
```bash
docker-compose up -d
```

### 4. Vérifier que tout fonctionne
```bash
# Vérifier les conteneurs
docker-compose ps

# Vérifier les logs
docker-compose logs -f backend

# Tester l'API
curl http://localhost:8000/health
```

## Configuration des notifications

### Email (Gmail)

1. **Activer 2FA sur Gmail**
   - Aller sur https://myaccount.google.com/security
   - Activer la validation en 2 étapes

2. **Créer un App Password**
   - Aller sur https://myaccount.google.com/apppasswords
   - Créer un nouveau mot de passe pour "Mail"
   - Copier le mot de passe généré (16 caractères)

3. **Ajouter dans .env:**
```bash
EMAIL_ENABLED=true
EMAIL_SMTP_HOST=smtp.gmail.com
EMAIL_SMTP_PORT=587
EMAIL_SMTP_USER=your-email@gmail.com
EMAIL_SMTP_PASSWORD=xxxx-xxxx-xxxx-xxxx
EMAIL_FROM=noreply@afcfta.com
EMAIL_TO=admin@domain.com,ops@domain.com
```

### Email (Outlook/Office365)

```bash
EMAIL_ENABLED=true
EMAIL_SMTP_HOST=smtp-mail.outlook.com
EMAIL_SMTP_PORT=587
EMAIL_SMTP_USER=your-email@outlook.com
EMAIL_SMTP_PASSWORD=your-password
EMAIL_FROM=your-email@outlook.com
EMAIL_TO=admin@domain.com
```

### Email (SendGrid)

```bash
EMAIL_ENABLED=true
EMAIL_SMTP_HOST=smtp.sendgrid.net
EMAIL_SMTP_PORT=587
EMAIL_SMTP_USER=apikey
EMAIL_SMTP_PASSWORD=SG.your-sendgrid-api-key
EMAIL_FROM=noreply@yourdomain.com
EMAIL_TO=admin@domain.com
```

### Slack

1. **Créer une app Slack**
   - Aller sur https://api.slack.com/apps
   - Cliquer sur "Create New App"
   - Choisir "From scratch"
   - Donner un nom (ex: "AfCFTA Crawler")

2. **Activer Incoming Webhooks**
   - Dans la sidebar, aller sur "Incoming Webhooks"
   - Activer "Activate Incoming Webhooks"
   - Cliquer sur "Add New Webhook to Workspace"
   - Sélectionner le canal de destination

3. **Copier l'URL webhook dans .env:**
```bash
SLACK_ENABLED=true
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXX
SLACK_CHANNEL=#afcfta-monitoring
```

## Commandes utiles

### Gestion des conteneurs

```bash
# Démarrer les services
docker-compose up -d

# Arrêter les services
docker-compose down

# Redémarrer un service
docker-compose restart backend

# Voir les logs en temps réel
docker-compose logs -f

# Voir les logs d'un service spécifique
docker-compose logs -f backend
docker-compose logs -f mongodb

# Voir l'état des conteneurs
docker-compose ps
```

### Gestion des données

```bash
# Sauvegarder la base de données
docker-compose exec mongodb mongodump --out /data/backup

# Restaurer la base de données
docker-compose exec mongodb mongorestore /data/backup

# Accéder au shell MongoDB
docker-compose exec mongodb mongosh

# Supprimer les volumes (ATTENTION: perte de données)
docker-compose down -v
```

### Mise à jour de l'application

```bash
# Récupérer les dernières modifications
git pull origin main

# Rebuilder et redémarrer
docker-compose up -d --build

# Voir les changements appliqués
docker-compose logs -f backend
```

### Debugging

```bash
# Entrer dans le conteneur backend
docker-compose exec backend bash

# Vérifier les variables d'environnement
docker-compose exec backend env | grep EMAIL
docker-compose exec backend env | grep SLACK

# Tester la connectivité MongoDB
docker-compose exec backend python -c "from pymongo import MongoClient; client = MongoClient('mongodb://mongodb:27017'); print(client.server_info())"
```

## Surveillance et monitoring

### Health Check

L'API expose un endpoint de santé:
```bash
curl http://localhost:8000/health
```

Réponse attendue:
```json
{
  "status": "healthy",
  "database": "connected",
  "timestamp": "2025-02-06T12:00:00Z"
}
```

### Logs

Les logs sont stockés dans:
- Backend: `docker-compose logs backend`
- MongoDB: `docker-compose logs mongodb`
- Worker logs: `./worker-logs/` (sur l'hôte)

### Métriques

Vérifier l'utilisation des ressources:
```bash
docker stats
```

## Production

### Sécurité

1. **Renseigner les secrets** : `docker compose` refuse de démarrer sans eux.
```bash
MONGO_ROOT_USER=admin                      # administration de MongoDB seulement
MONGO_ROOT_PASSWORD=your-very-secure-password-here
MONGO_APP_USER=afcfta_app                  # utilisateur du backend, readWrite sur sa base
MONGO_APP_PASSWORD=another-secure-password # lettres et chiffres (il entre dans MONGO_URL)
REDIS_PASSWORD=redis-password              # lettres et chiffres
ALLOWED_ORIGINS=https://votre-domaine.example  # origines exactes du frontend
```
L'utilisateur `MONGO_APP_USER` est créé par `docker/mongo-init/` à la création
du volume. Sur un volume existant, créez-le à la main (même commande, connecté
en root avec `mongosh`).

2. **Utiliser HTTPS**
   - Ajouter un reverse proxy (Nginx, Traefik)
   - Configurer SSL/TLS

3. **Restreindre les ports**
   - Modifier `docker-compose.yml` pour ne pas exposer MongoDB (port 27017)

4. **Variables d'environnement sensibles**
   - Ne jamais commiter le fichier `.env`
   - Utiliser un gestionnaire de secrets (Vault, AWS Secrets Manager)

### Performance

1. **Ajuster les ressources**
```yaml
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '1'
          memory: 1G
```

2. **Augmenter le nombre de workers**
```yaml
services:
  backend:
    command: uvicorn backend.server:app --host 0.0.0.0 --port 8000 --workers 4
```
Attention : le quota des calculs sans compte et le limiteur de débit sont
comptés en mémoire, par processus. Avec N workers, un visiteur dispose de
N fois son quota : gardez un seul worker tant que ces compteurs ne sont pas
partagés (par exemple dans Redis).

### Backup automatique

Créer un cron job pour sauvegarder MongoDB:
```bash
# Éditer crontab
crontab -e

# Ajouter (sauvegarde quotidienne à 2h du matin)
0 2 * * * cd /path/to/afcfta-final-001 && docker-compose exec -T mongodb mongodump --out /data/backup/$(date +\%Y\%m\%d)
```

## Troubleshooting

### Le backend ne démarre pas

1. Vérifier les logs:
```bash
docker-compose logs backend
```

2. Vérifier MongoDB:
```bash
docker-compose ps mongodb
docker-compose logs mongodb
```

3. Vérifier les variables d'environnement:
```bash
docker-compose config
```

### Les notifications ne fonctionnent pas

1. Vérifier la configuration:
```bash
docker-compose exec backend env | grep EMAIL
docker-compose exec backend env | grep SLACK
```

2. Tester la connectivité SMTP:
```bash
docker-compose exec backend python -c "
import smtplib
server = smtplib.SMTP('smtp.gmail.com', 587)
server.starttls()
print('SMTP connection OK')
"
```

3. Vérifier les logs:
```bash
docker-compose logs backend | grep -i notification
```

### MongoDB n'est pas accessible

1. Vérifier que le conteneur tourne:
```bash
docker-compose ps mongodb
```

2. Tester la connexion:
```bash
docker-compose exec mongodb mongosh --eval "db.adminCommand('ping')"
```

3. Vérifier le réseau:
```bash
docker network ls
docker network inspect afcfta_afcfta-network
```

## Support

Pour obtenir de l'aide:
- Ouvrir une issue sur GitHub
- Consulter la documentation complète
- Vérifier les logs pour plus de détails
