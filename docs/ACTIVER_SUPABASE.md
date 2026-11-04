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
| Sender name | `AF Trade Intelligence` (le nom de la société, pas celui de l'institution ZLECAf) |
| Host | `smtp.zoho.eu` (ou `smtp.zoho.com`, selon le centre de données du compte Zoho) |
| Port | `465` |
| Username | l'adresse d'envoi |
| Password | un **mot de passe d'application** Zoho, pas le mot de passe du compte |

Le SMTP intégré de Supabase n'envoie que quelques e-mails par heure : il ne
suffit pas pour des testeurs.

### Modèles d'e-mail : liens par `token_hash`

L'application utilise le flux PKCE (audit M6). Avec les modèles par défaut, un
lien de confirmation ouvert sur un autre appareil que celui de l'inscription
échouerait. Les trois modèles prêts à l'emploi, en français, anglais et arabe,
avec le logo d'AF Trade Intelligence, sont dans `docs/emails-supabase/`. Leurs
liens suivent la forme `{{ .SiteURL }}/?token_hash={{ .TokenHash }}&type=…`.

**À ne faire qu'après la fusion dans `main`** et la fin du workflow `pages.yml`.
Le logo est publié par la vitrine : vérifier d'abord que
`https://www.afcfta-zlecaf.com/email/logo-af-trade-intelligence.png` s'affiche.

Dans **Authentication → Emails → Templates**, pour chaque modèle : coller l'objet
dans **Subject**, puis remplacer tout le **Message body** par le contenu complet
du fichier, et enregistrer.

| Modèle Supabase | Fichier | Subject |
|---|---|---|
| Confirm signup | `docs/emails-supabase/confirm-signup.html` | `Confirmez votre adresse e-mail · Confirm your email · أكِّد بريدك الإلكتروني` |
| Reset password | `docs/emails-supabase/reset-password.html` | `Réinitialisez votre mot de passe · Reset your password · إعادة تعيين كلمة المرور` |
| Change email address | `docs/emails-supabase/change-email.html` | `Confirmez le changement d'adresse e-mail · Confirm your email change · تأكيد تغيير البريد الإلكتروني` |

Avec « Secure email change », Supabase envoie le dernier modèle aux deux
adresses, l'ancienne et la nouvelle : son texte parle donc d'un changement à
confirmer, pas d'une nouvelle adresse.

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
   Zoho. Ouvert dans le même navigateur, le lien connecte directement et
   affiche « Connecté en tant que … ».
2. Ouvert sur un autre appareil, le même type de lien demande d'abord
   « Continuer » ; après le clic, la personne est connectée.
3. Un lien déjà utilisé, rouvert, demande « Continuer », puis affiche « Ce lien
   a expiré ou a déjà servi ».
4. « Mot de passe oublié » envoie un lien qui ouvre la saisie du nouveau mot de
   passe, avec l'adresse du compte ; depuis un autre appareil, après
   « Continuer ».
5. Le compte admin se connecte avec son mot de passe actuel, et garde son accès
   illimité (`ADMIN_ACCES_ILLIMITE`).
6. L'ancienne route de connexion est fermée : elle répond 410. La protection
   CSRF et la validation du corps passent d'abord, d'où la commande en deux
   temps (403 sans jeton CSRF, 422 sans corps JSON) :

   ```bash
   SITE=https://git-sync-41.preview.emergentagent.com
   JETON=$(curl -s -c /tmp/cookies.txt -D - -o /dev/null "$SITE/api/health" | awk -F': ' 'tolower($1)=="x-csrf-token" {print $2}' | tr -d '\r')
   curl -s -o /dev/null -w "%{http_code}\n" -b /tmp/cookies.txt -H "X-CSRF-Token: $JETON" \
     -H "Content-Type: application/json" -d '{"email":"test@example.com","password":"x"}' \
     "$SITE/api/auth/login"
   ```

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
  revenir en arrière, dans `mongosh` (après `use <DB_NAME>`) :
  `db.users.countDocuments({supabase_id: {$exists: true}, password_hash: {$exists: false}})`.
