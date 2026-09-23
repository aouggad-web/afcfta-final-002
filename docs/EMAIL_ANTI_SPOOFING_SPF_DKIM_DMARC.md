# Anti-usurpation e-mail : SPF, DKIM et DMARC pour `afcfta-zlecaf.com`

## Pourquoi ce document

La boîte `noreply@afcfta-zlecaf.com` sert à la fois d'expéditeur et de
destinataire des notifications transactionnelles (mail de bienvenue à
l'inscription, notification admin du formulaire de contact — voir
`backend/services/email_service.py`). Comme le champ `From` est toujours
`noreply@afcfta-zlecaf.com`, il ne permet **pas** à lui seul de distinguer :

1. un envoi authentifié réel via le compte SMTP Zoho (code applicatif, script,
   ou accès non autorisé au mot de passe) ;
2. une **usurpation** (« spoofing ») : un tiers externe forge l'en-tête
   `From: noreply@afcfta-zlecaf.com` dans un mail entrant, sans aucun accès au
   compte.

Les trois enregistrements DNS ci-dessous ferment le scénario 2 : correctement
configurés, un message forgé prétendant venir de votre domaine est rejeté ou
mis en quarantaine par les serveurs destinataires (et par Zoho lui-même en
entrée).

## Diagnostic d'un message suspect (avant toute action)

Ouvrez la **source / les en-têtes complets** du mail reçu et lisez la ligne
`Authentication-Results` :

- `spf=pass` **et** `dkim=pass` signés par `afcfta-zlecaf.com`
  → le message a réellement été émis par le compte Zoho. Regardez alors l'IP
  dans les lignes `Received:` :
  - IP d'un pod Emergent → test/appel légitime ;
  - IP inconnue → **compromission du mot de passe SMTP** : changez-le dans
    Zoho, puis mettez à jour `SAAS_SMTP_PASSWORD` dans les trois apps
    (Gérer les publications → Secrets).
- `spf=fail`/`softfail`, ou `dkim=fail`/absent
  → **usurpation**. Le mot de passe SMTP n'est pas en cause ; renforcez le DNS
    ci-dessous (une politique DMARC `p=reject` aurait bloqué ce message).

L'audit applicatif complète ce diagnostic : chaque appel de
`send_contact_admin_email` écrit désormais une ligne de log horodatée, et
chaque soumission via `/api/contact` enregistre l'IP appelante (`submit_ip`)
dans la collection `contact_messages`. Un message admin sans ligne de log
correspondante n'a pas été produit par vos pods.

## 1. SPF — qui a le droit d'envoyer pour votre domaine

Enregistrement TXT unique à la racine du domaine. Autorise les serveurs Zoho
et rien d'autre :

```
Type : TXT
Hôte : @            (afcfta-zlecaf.com)
Valeur : v=spf1 include:zoho.com ~all
```

- `include:zoho.com` : délègue à Zoho la liste de ses IP d'envoi.
- `~all` (softfail) au démarrage, à durcir en `-all` (hardfail) une fois que
  vous avez confirmé qu'aucun autre système légitime n'envoie pour ce domaine.
- **Un seul** enregistrement SPF par domaine — si vous ajoutez un autre
  fournisseur, combinez les `include:` dans la même ligne.

## 2. DKIM — signature cryptographique des messages

À générer côté Zoho, pas à la main :

1. Zoho Mail Admin Console → **Domains** → `afcfta-zlecaf.com` → **Email
   Configuration** → **DKIM**.
2. Créez un sélecteur (ex. `zoho` ou `default`) : Zoho fournit un nom d'hôte
   (`<sélecteur>._domainkey`) et une valeur TXT (clé publique).
3. Publiez cet enregistrement TXT chez votre registrar DNS :

```
Type : TXT
Hôte : <sélecteur>._domainkey     (ex. zoho._domainkey)
Valeur : v=DKIM1; k=rsa; p=<clé-publique-fournie-par-Zoho>
```

4. Revenez dans Zoho et cliquez **Verify** pour activer la signature.

Une fois actif, chaque mail sortant est signé ; un message forgé ne peut pas
reproduire cette signature.

## 3. DMARC — politique et rapports

Lie SPF et DKIM à une politique et vous fait remonter des rapports d'abus.
Déployez en trois temps pour ne rien casser :

**Phase 1 — observation (`p=none`)**, quelques semaines :

```
Type : TXT
Hôte : _dmarc                     (_dmarc.afcfta-zlecaf.com)
Valeur : v=DMARC1; p=none; rua=mailto:dmarc@afcfta-zlecaf.com; fo=1
```

Les rapports agrégés (`rua`) vous montrent qui envoie sous votre nom et si
SPF/DKIM passent. Vérifiez qu'aucun envoi légitime n'échoue.

**Phase 2 — quarantaine :**

```
v=DMARC1; p=quarantine; rua=mailto:dmarc@afcfta-zlecaf.com; fo=1
```

**Phase 3 — rejet (cible) :**

```
v=DMARC1; p=reject; rua=mailto:dmarc@afcfta-zlecaf.com; fo=1
```

À `p=reject`, un message usurpant `noreply@afcfta-zlecaf.com` sans SPF/DKIM
valides est refusé par les destinataires — le scénario 2 devient impossible.

## Vérification

Après propagation DNS (jusqu'à ~24 h) :

```bash
dig +short TXT afcfta-zlecaf.com            # doit montrer la ligne v=spf1
dig +short TXT zoho._domainkey.afcfta-zlecaf.com   # clé DKIM (adapter le sélecteur)
dig +short TXT _dmarc.afcfta-zlecaf.com     # doit montrer v=DMARC1
```

Envoyez ensuite un mail de test depuis l'app vers une adresse Gmail et
inspectez `Authentication-Results` dans les en-têtes reçus : `spf=pass`,
`dkim=pass`, `dmarc=pass` attendus.

## Rotation du mot de passe SMTP (si compromission confirmée)

Le code lit une seule variable, `SAAS_SMTP_PASSWORD` (voir
`backend/services/email_service.py` et `docs/emergent.env.template`).

1. Zoho → **Security** → **App Passwords** : révoquez l'ancien, générez-en un
   nouveau (les mailbox avec 2FA exigent un mot de passe d'application).
2. Mettez à jour `SAAS_SMTP_PASSWORD` dans **chacune** des trois apps
   Emergent (Gérer les publications → Secrets) — elles partagent le même
   compte SMTP.
3. Redéployez et envoyez un mail de test pour confirmer.
