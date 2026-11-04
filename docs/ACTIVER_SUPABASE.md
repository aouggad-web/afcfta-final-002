# Activer Supabase pour les comptes utilisateurs

Supabase gère l'inscription, la confirmation de l'adresse e-mail, le mot de passe
oublié et les sessions. Le backend garde la fiche de chaque compte dans MongoDB
(formule, rôle, quotas) et la relie au compte Supabase par l'adresse e-mail.

Tant que les variables `SUPABASE_*` ne sont pas renseignées, l'ancien système de
comptes reste seul actif. Dès qu'elles le sont :

- l'inscription et la connexion passent par Supabase ;
- les anciennes routes `/api/auth/register` et `/api/auth/login` répondent 410 ;
- les sessions déjà ouvertes par l'ancien système restent valables jusqu'à leur
  expiration, 7 jours au plus.

**Ordre à respecter.** Il faut configurer le projet, transférer les comptes, puis
renseigner les quatre variables d'un coup. Si le backend connaît Supabase avant
l'interface, plus personne ne peut se connecter.

## 1. Configurer le projet Supabase

Toutes ces étapes se font dans le tableau de bord du projet. Aucune clé ne doit
être collée dans une conversation ni dans un fichier du dépôt.

### Adresses autorisées

**Authentication → URL Configuration** :

- **Site URL** : l'adresse de l'application, **sans `/` final**, par exemple
  `https://git-sync-41.preview.emergentagent.com` pour la préproduction.
- **Redirect URLs** : la même adresse, **exacte**. Pas de motif `*` ni `**` : un
  motif permettrait de renvoyer un lien de connexion vers un autre site.

### Inscription par e-mail

**Authentication → Sign In / Providers → Email** :

- Email : activé.
- **Confirm email** : activé. Le backend refuse de relier un compte dont
  l'adresse n'est pas confirmée.
- **Secure email change** : activé.
- Longueur minimale du mot de passe : 8 caractères, lettres et chiffres.

### Envoi des e-mails (SMTP Zoho)

**Authentication → Emails → SMTP Settings**, puis **Enable custom SMTP** :

| Champ | Valeur |
|---|---|
| Sender email | l'adresse d'envoi Zoho, par exemple `no-reply@afcfta-zlecaf.com` |
| Sender name | `ZLECAf` |
| Host | `smtp.zoho.eu` (ou `smtp.zoho.com`, selon le centre de données du compte Zoho) |
| Port | `465` |
| Username | l'adresse d'envoi |
| Password | un **mot de passe d'application** Zoho, pas le mot de passe du compte |

Le SMTP intégré de Supabase n'envoie que quelques e-mails par heure : il ne
suffit pas pour des testeurs.

### Modèles d'e-mail : liens par `token_hash`

L'application utilise le flux PKCE (audit M6). Avec les modèles par défaut, un
lien de confirmation ouvert sur un autre appareil que celui de l'inscription
échouerait. Dans **Authentication → Emails → Templates**, remplacer le lien de
chaque modèle :

| Modèle | Lien |
|---|---|
| Confirm signup | `<a href="{{ .SiteURL }}/?token_hash={{ .TokenHash }}&type=email">Confirmer mon adresse</a>` |
| Reset password | `<a href="{{ .SiteURL }}/?token_hash={{ .TokenHash }}&type=recovery">Choisir un nouveau mot de passe</a>` |
| Change email address | `<a href="{{ .SiteURL }}/?token_hash={{ .TokenHash }}&type=email_change">Confirmer ma nouvelle adresse</a>` |

L'application efface ce jeton de la barre d'adresse dès l'ouverture de la page.
Ensuite, deux cas :
- le navigateur qui a fait la demande (inscription, mot de passe oublié) attend
  ce lien : il le vérifie aussitôt, et refuse un lien qui concerne une autre
  adresse ;
- sinon (autre appareil, lien transmis, scanner de messagerie), le lien n'est
  vérifié qu'après un clic sur « Continuer ». Un lien obtenu par un tiers pour
  son propre compte ne peut donc pas connecter quelqu'un à son insu.

L'adresse du compte connecté est toujours affichée. Un lien expiré ou déjà
utilisé affiche un message.

### Sessions

**Authentication → Sessions** (valeurs par défaut, à vérifier) :

- durée du jeton d'accès (JWT expiry) : 3600 secondes. Le cookie de session de
  l'application expire avec lui. Une session révoquée dans Supabase tombe donc
  en moins d'une heure ;
- rotation des jetons de rafraîchissement : activée.

## 2. Transférer les comptes existants

Le script `scripts/migrate_users_to_supabase.py` copie chaque compte MongoDB dans
Supabase avec **le même mot de passe** : son hachage bcrypt est importé tel quel,
et personne n'a à le réinitialiser. Le script ne supprime rien de MongoDB et peut
être relancé sans créer de doublon.

Sur le pod, les clés sont fournies dans l'environnement du seul script, sans
toucher au `.env` :

1. À blanc, sans rien écrire : `python scripts/migrate_users_to_supabase.py`
2. Transfert réel : `python scripts/migrate_users_to_supabase.py --apply`

Variables lues : `MONGO_URL`, `DB_NAME`, `SUPABASE_URL`, `SUPABASE_SECRET_KEY`.
Les comptes transférés sont considérés comme confirmés. L'option
`--require-confirmation` leur demande de confirmer leur adresse.

## 3. Renseigner les variables et redéployer

| Fichier sur le pod | Variable | Où la trouver |
|---|---|---|
| `/app/backend/.env` | `SUPABASE_URL` | Project Settings → API : l'URL du projet |
| `/app/backend/.env` | `SUPABASE_SECRET_KEY` | Project Settings → API Keys : la clé secrète (`sb_secret_…`), **jamais côté interface** |
| `/app/frontend/.env` | `VITE_SUPABASE_URL` | la même URL |
| `/app/frontend/.env` | `VITE_SUPABASE_PUBLISHABLE_KEY` | Project Settings → API Keys : la clé publique (`sb_publishable_…`) |

Les variables `VITE_*` doivent aller dans `/app/frontend/.env`, pas dans celui
du backend : Vite ne lit que ce fichier, au moment de la compilation. La
synchronisation (`sync_emergent.sh`) recompile l'interface.

Juste après, relancer `python scripts/migrate_users_to_supabase.py --apply`. Les
comptes créés entre le premier transfert et l'activation sont ainsi transférés
à leur tour. L'ancienne inscription étant désormais fermée, il n'en apparaîtra
plus de nouveaux.

## 4. Vérifier

1. Une inscription avec une nouvelle adresse envoie un e-mail depuis l'adresse
   Zoho. Le lien ouvre l'application, connecté.
2. Le même lien, rouvert, affiche « Ce lien a expiré ou a déjà servi ».
3. « Mot de passe oublié » envoie un lien qui ouvre la saisie du nouveau mot de
   passe, aussi depuis un autre appareil.
4. Le compte admin se connecte avec son mot de passe actuel, et garde son accès
   illimité (`ADMIN_ACCES_ILLIMITE`).
5. L'ancienne route de connexion est fermée : `POST /api/auth/login` répond 410
   quand la requête porte le jeton CSRF. Sans lui, la protection CSRF répond
   d'abord par 403 : faire d'abord un `GET /api/health`, puis envoyer le cookie
   `csrf_token` et l'en-tête `X-CSRF-Token` reçus.

## Revenir en arrière

Retirer les quatre variables et redéployer remet l'ancien système en service.
Les fiches MongoDB n'ont pas été modifiées, en dehors de leur lien
`supabase_id`. Trois conséquences :

- toutes les sessions Supabase sont coupées aussitôt : chacun doit se
  reconnecter ;
- un mot de passe changé entre-temps dans Supabase ne l'est pas dans MongoDB :
  c'est l'ancien qui redevient valable ;
- les comptes **créés** pendant l'activation n'ont pas de mot de passe dans
  MongoDB : ils ne peuvent plus se connecter du tout. Les compter avant de
  revenir en arrière :
  `db.users.count_documents({"supabase_id": {"$exists": True}, "password_hash": {"$exists": False}})`.
