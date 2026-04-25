# 📧 Guide des Notifications

## Vue d'ensemble

Le système de notifications AfCFTA supporte deux canaux:
- **Email** via SMTP (Gmail, Outlook, SendGrid, etc.)
- **Slack** via webhooks

Les notifications sont envoyées automatiquement pour:
- 🚀 Début de crawl
- ✅ Succès de crawl
- ❌ Échec de crawl
- ⚠️ Problèmes de validation des données

## Configuration Email

### Gmail

#### Prérequis
- Un compte Gmail
- 2FA activé sur le compte
- Un App Password généré

#### Étapes

1. **Activer la validation en 2 étapes**
   - Aller sur https://myaccount.google.com/security
   - Cliquer sur "Validation en 2 étapes"
   - Suivre les instructions pour l'activer

2. **Générer un App Password**
   - Aller sur https://myaccount.google.com/apppasswords
   - Sélectionner "Mail" et votre appareil
   - Cliquer sur "Générer"
   - Copier le mot de passe à 16 caractères (format: xxxx xxxx xxxx xxxx)

3. **Configuration dans .env**
```bash
EMAIL_ENABLED=true
EMAIL_SMTP_HOST=smtp.gmail.com
EMAIL_SMTP_PORT=587
EMAIL_SMTP_USER=your-email@gmail.com
EMAIL_SMTP_PASSWORD=xxxx-xxxx-xxxx-xxxx
EMAIL_FROM=noreply@afcfta.com
EMAIL_TO=admin@domain.com,ops@domain.com
```

#### Notes Gmail
- L'App Password est différent de votre mot de passe Gmail normal
- Ne partagez jamais votre App Password
- Un App Password par application est recommandé
- Vous pouvez révoquer un App Password à tout moment

### Outlook / Office365

```bash
EMAIL_ENABLED=true
EMAIL_SMTP_HOST=smtp-mail.outlook.com
EMAIL_SMTP_PORT=587
EMAIL_SMTP_USER=your-email@outlook.com
EMAIL_SMTP_PASSWORD=your-password
EMAIL_FROM=your-email@outlook.com
EMAIL_TO=recipient@domain.com
```

**Notes Outlook:**
- Utiliser le mot de passe de votre compte Outlook
- Si vous avez 2FA, créer un mot de passe d'application
- Pour Office365 professionnel, vérifier avec votre admin

### SendGrid

SendGrid est recommandé pour une utilisation en production.

1. **Créer un compte SendGrid**
   - Aller sur https://sendgrid.com
   - S'inscrire (plan gratuit: 100 emails/jour)

2. **Créer une API Key**
   - Dashboard → Settings → API Keys
   - Créer une nouvelle API Key
   - Donner les permissions "Mail Send"
   - Copier la clé (elle ne sera visible qu'une fois)

3. **Configuration**
```bash
EMAIL_ENABLED=true
EMAIL_SMTP_HOST=smtp.sendgrid.net
EMAIL_SMTP_PORT=587
EMAIL_SMTP_USER=apikey
EMAIL_SMTP_PASSWORD=SG.xxxxxxxxxxxxxxxxxxxxx
EMAIL_FROM=noreply@yourdomain.com
EMAIL_TO=admin@yourdomain.com
```

**Avantages SendGrid:**
- Haute délivrabilité
- Statistiques détaillées
- Gestion des bounces
- Template system
- API REST disponible

### AWS SES (Amazon Simple Email Service)

```bash
EMAIL_ENABLED=true
EMAIL_SMTP_HOST=email-smtp.us-east-1.amazonaws.com
EMAIL_SMTP_PORT=587
EMAIL_SMTP_USER=your-smtp-username
EMAIL_SMTP_PASSWORD=your-smtp-password
EMAIL_FROM=verified@yourdomain.com
EMAIL_TO=recipient@domain.com
```

### Autres fournisseurs SMTP

#### Mailgun
```bash
EMAIL_SMTP_HOST=smtp.mailgun.org
EMAIL_SMTP_PORT=587
```

#### SparkPost
```bash
EMAIL_SMTP_HOST=smtp.sparkpostmail.com
EMAIL_SMTP_PORT=587
```

#### SMTP personnalisé
```bash
EMAIL_SMTP_HOST=smtp.yourserver.com
EMAIL_SMTP_PORT=587  # ou 465 pour SSL
EMAIL_SMTP_USER=your-username
EMAIL_SMTP_PASSWORD=your-password
```

## Configuration Slack

### Création d'une app Slack

1. **Créer une nouvelle app**
   - Aller sur https://api.slack.com/apps
   - Cliquer sur "Create New App"
   - Choisir "From scratch"
   - Nom: "AfCFTA Crawler" (ou autre nom)
   - Workspace: sélectionner votre workspace

2. **Activer les Incoming Webhooks**
   - Dans la sidebar de votre app, cliquer sur "Incoming Webhooks"
   - Toggle "Activate Incoming Webhooks" sur ON
   - Cliquer sur "Add New Webhook to Workspace"
   - Sélectionner le canal où envoyer les notifications
   - Autoriser l'app

3. **Copier l'URL du webhook**
   - L'URL du webhook ressemble à:
     ```
     https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXX
     ```
   - Copier cette URL

4. **Configuration dans .env**
```bash
SLACK_ENABLED=true
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXX
SLACK_CHANNEL=#afcfta-monitoring
```

### Personnalisation

Vous pouvez personnaliser davantage via les variables d'environnement:

```bash
SLACK_CHANNEL=#custom-channel  # Canal de destination
SLACK_USERNAME=AfCFTA Crawler  # Nom affiché
SLACK_ICON_EMOJI=:robot_face:  # Icône personnalisée
```

### Canaux multiples

Pour envoyer vers plusieurs canaux, créez plusieurs webhooks:
```bash
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/T00/B00/XXX
# Pour ajouter d'autres canaux, modifier le code ou créer des webhooks supplémentaires
```

## Types de notifications

### 🚀 Crawl Started
Envoyée au début d'un job de crawling.

**Contenu:**
- Job ID
- Pays concerné
- Heure de début

### ✅ Crawl Success
Envoyée quand le crawl se termine avec succès.

**Contenu:**
- Job ID
- Pays concerné
- Nombre d'items scrapés
- Score de validation
- Durée d'exécution

### ❌ Crawl Failed
Envoyée en cas d'échec du crawl.

**Contenu:**
- Job ID
- Pays concerné
- Type d'erreur
- Message d'erreur détaillé

### ⚠️ Validation Issues
Envoyée quand des problèmes de qualité sont détectés.

**Contenu:**
- Job ID
- Pays concerné
- Score de validation
- Liste des problèmes détectés

## Test des notifications

### Test manuel depuis Python

```python
import asyncio
from backend.notifications import NotificationManager

async def test():
    manager = NotificationManager()
    
    # Test notification de début
    await manager.notify_crawl_start(
        job_id="test_001",
        country_code="MA",
        country_name="Morocco"
    )
    
    # Test notification de succès
    await manager.notify_crawl_success(
        job_id="test_001",
        country_code="MA",
        country_name="Morocco",
        stats={"items_scraped": 100},
        duration_seconds=120.5
    )

asyncio.run(test())
```

### Test depuis l'API

```bash
# Démarrer l'API
uvicorn backend.server:app --reload

# Lancer un crawl (qui enverra des notifications)
curl -X POST http://localhost:8000/api/crawl/start \
  -H "Content-Type: application/json" \
  -d '{"country_code": "MA"}'
```

## Désactiver les notifications

Pour désactiver temporairement:

```bash
# Désactiver email
EMAIL_ENABLED=false

# Désactiver Slack
SLACK_ENABLED=false
```

## Troubleshooting

### Les emails ne sont pas envoyés

1. **Vérifier la configuration**
```bash
docker-compose exec backend python -c "
import os
print('EMAIL_ENABLED:', os.getenv('EMAIL_NOTIFICATIONS_ENABLED'))
print('EMAIL_SMTP_HOST:', os.getenv('EMAIL_SMTP_HOST'))
print('EMAIL_SMTP_USER:', os.getenv('EMAIL_SMTP_USER'))
print('EMAIL_TO:', os.getenv('EMAIL_TO'))
"
```

2. **Tester la connexion SMTP**
```python
import smtplib
server = smtplib.SMTP('smtp.gmail.com', 587)
server.starttls()
server.login('your-email@gmail.com', 'your-app-password')
print("Connection successful!")
server.quit()
```

3. **Vérifier les logs**
```bash
docker-compose logs backend | grep -i email
docker-compose logs backend | grep -i notification
```

### Les messages Slack ne sont pas envoyés

1. **Vérifier l'URL du webhook**
```bash
curl -X POST https://hooks.slack.com/services/YOUR/WEBHOOK/URL \
  -H 'Content-Type: application/json' \
  -d '{"text": "Test message"}'
```

2. **Vérifier la configuration**
```bash
docker-compose exec backend python -c "
import os
print('SLACK_ENABLED:', os.getenv('SLACK_NOTIFICATIONS_ENABLED'))
print('SLACK_WEBHOOK_URL:', os.getenv('SLACK_WEBHOOK_URL'))
"
```

3. **Vérifier les logs**
```bash
docker-compose logs backend | grep -i slack
```

### Emails dans les spams

- Vérifier SPF, DKIM, DMARC de votre domaine
- Utiliser un service professionnel (SendGrid, SES)
- Ne pas utiliser Gmail pour un envoi en masse
- Vérifier la réputation de votre IP

## Limites et quotas

### Gmail
- **Limite gratuite:** 500 emails/jour
- **G Suite:** 2000 emails/jour
- Délai recommandé: 1-2 secondes entre emails

### SendGrid
- **Plan gratuit:** 100 emails/jour
- **Plans payants:** À partir de 15$/mois pour 40k emails

### Slack
- **Webhooks:** Pas de limite stricte, mais rate limiting à 1 message/seconde

## Bonnes pratiques

1. **Ne pas spammer**
   - Grouper les notifications similaires
   - Utiliser des résumés quotidiens pour les rapports

2. **Sécurité**
   - Ne jamais commiter les credentials dans Git
   - Utiliser des App Passwords, pas les vrais mots de passe
   - Restreindre les permissions des API keys

3. **Monitoring**
   - Surveiller les taux de bounce
   - Vérifier régulièrement que les notifications arrivent
   - Mettre en place des alertes de fallback

4. **Production**
   - Utiliser un service professionnel (SendGrid, SES)
   - Configurer des templates HTML
   - Implémenter un système de retry
   - Logger toutes les tentatives d'envoi

## Support

Pour plus d'aide:
- Consulter la documentation de votre fournisseur SMTP
- Vérifier les logs d'erreur détaillés
- Ouvrir une issue sur GitHub
