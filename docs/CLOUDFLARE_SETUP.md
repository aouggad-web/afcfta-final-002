# Intégrer Cloudflare (détection du pays de facturation)

Objectif : que le backend connaisse de façon **fiable** le pays de l'utilisateur,
afin d'imposer Chargily (dinars, CIB/Edahabia) aux connexions algériennes, comme
l'exige le contrôle des changes.

Cloudflare est la voie la plus simple : son edge ajoute l'en-tête `CF-IPCountry`
à chaque requête, sans base de données à installer ni à mettre à jour.

---

## Le point à ne pas rater

Un en-tête HTTP n'est qu'un texte. Si votre API reste joignable en direct,
n'importe qui peut faire :

```bash
curl https://api.afcfta-zlecaf.com/api/billing/checkout -H 'CF-IPCountry: FR' ...
```

…et contourner le verrou. **Le backend n'accepte donc `CF-IPCountry` que si la
requête prouve qu'elle vient de Cloudflare.** Sans cette preuve, l'en-tête est
ignoré, le pays reste indéterminé, et l'on retombe sur le choix manuel de
l'utilisateur.

Deux façons de fournir cette preuve — l'option 1 est recommandée.

---

## Étape 1 — Mettre le domaine derrière Cloudflare

1. Créez un compte sur [cloudflare.com](https://cloudflare.com) (le plan gratuit
   suffit) et ajoutez le domaine `afcfta-zlecaf.com`.
2. Cloudflare vous donne deux serveurs de noms. Remplacez-les chez votre
   registrar (là où le domaine a été acheté). La propagation prend de quelques
   minutes à 24 h.
3. Dans **DNS**, vérifiez que l'enregistrement de l'API (par exemple `api`)
   affiche un **nuage orange** (« Proxied »). Gris = trafic direct, donc aucun
   en-tête `CF-*` : c'est l'erreur classique.

> La page statique et l'API peuvent être sur des hébergeurs différents ; seul
> l'enregistrement qui sert **l'API** doit être proxifié pour cette
> fonctionnalité.

---

## Étape 2 (recommandée) — Secret partagé

Le backend ne croira les en-têtes `CF-*` que si Cloudflare joint un secret que
seul lui connaît.

1. Générez le secret :

   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```

2. Dans Cloudflare : **Rules → Transform Rules → Modify Request Header →
   Create rule**.
   - *When incoming requests match* : `Hostname equals api.afcfta-zlecaf.com`
     (ou « All incoming requests »).
   - *Then* : **Set static** — nom `X-Edge-Secret`, valeur = le secret généré.
   - Déployez.

3. Côté serveur, dans `.env` :

   ```
   CLOUDFLARE_EDGE_SECRET=le-secret-généré
   ```

4. Redémarrez le backend.

Avantage : aucune liste d'adresses IP à maintenir, et le secret protège aussi
contre les appels directs à l'origine en général.

---

## Étape 2 bis (alternative) — Verrouiller l'origine au réseau

Si vous préférez ne pas gérer de secret, il faut rendre l'origine **réellement
injoignable** hors Cloudflare, puis l'indiquer au backend :

```
TRUST_CLOUDFLARE_HEADERS=true
```

Cette option fait confiance à l'en-tête **sans le vérifier** : elle n'est sûre
que si l'origine est effectivement fermée. Deux manières :

- **Cloudflare Tunnel** (le plus propre) : l'origine n'expose aucun port public.
- **Pare-feu** : n'autoriser que les plages publiées sur
  [cloudflare.com/ips](https://www.cloudflare.com/ips/).

Ne cochez pas cette option « pour voir » : elle rouvre exactement le
contournement décrit plus haut.

---

## Étape 3 — En-têtes de proxy : ne pas élargir sans raison

Le backend ne lit `X-Forwarded-For` que si le pair direct (`request.client.host`,
l'adresse qui ouvre la connexion) est un relais approuvé, réglé par
`TRUSTED_PROXY_CIDRS` (plages séparées par des virgules) :

- variable absente (défaut) : toute adresse non routable sur Internet (privée,
  boucle locale, CGNAT `100.64.0.0/10`, IPv6 locale) — cas d'un ingress interne ;
- liste explicite : ces plages seulement (par exemple un répartiteur de charge à
  adresse publique) ;
- vide (`TRUSTED_PROXY_CIDRS=`) : aucun relais. À utiliser derrière un relais
  réseau de niveau 4 (NAT Docker, Service Kubernetes en SNAT) qui n'ajoute pas
  `X-Forwarded-For` : sinon celui du client passerait pour celui du relais.

Le conteneur lance uvicorn avec `--proxy-headers --forwarded-allow-ips`, dont le
défaut est `127.0.0.1`. **Gardez ce défaut et ne passez jamais à
`UVICORN_FORWARDED_ALLOW_IPS=*`** : uvicorn remplacerait alors `request.client`
par l'entrée la plus à gauche de `X-Forwarded-For`, fournie par le client, et la
vérification du relais la croirait — n'importe qui choisirait son IP, donc son
pays.

N'exposez jamais directement le proxy de Vite (`yarn dev` ou `vite preview`) :
il transmet tel quel le `X-Forwarded-For` du client, que le backend reçoit de
`127.0.0.1`.

Les en-têtes Cloudflare (`CF-Connecting-IP`, `CF-IPCountry`) ne dépendent pas de
ce réglage : leur preuve est le secret de l'étape 2.

---

## Étape 4 — Vérifier

Depuis l'extérieur, l'appel doit refléter votre pays réel :

```bash
curl -s https://api.afcfta-zlecaf.com/api/billing/payment-context | jq
# {"provider":"stripe","country":"FR","locked":false,"currency":"USD"}
```

Puis vérifiez que la falsification **ne prend pas** :

```bash
curl -s https://api.afcfta-zlecaf.com/api/billing/payment-context \
  -H 'CF-IPCountry: DZ' | jq '.locked'
# false attendu — l'en-tête forgé est ignoré, faute du secret
```

Si `locked` passe à `true` sur cette seconde commande, la protection n'est pas
active : vérifiez `CLOUDFLARE_EDGE_SECRET` et que `TRUST_CLOUDFLARE_HEADERS`
n'est pas resté à `true` sur une origine ouverte.

Pour confirmer le comportement algérien sans se rendre en Algérie, testez
depuis un VPN sortant en Algérie, ou posez temporairement
`billing_stripe_exemption` sur un compte de test pour vérifier la dérogation.

---

## Sans Cloudflare — base MaxMind locale

C'est la voie **recommandée quand l'hébergeur ne garantit pas le passage des
en-têtes personnalisés** jusqu'au backend (cas d'Emergent, dont l'ingress n'est
pas documenté sur ce point). Elle ne dépend d'aucun en-tête : la géolocalisation
se fait dans le backend, à partir de l'IP client.

```bash
# 1. Compte gratuit : https://www.maxmind.com/en/geolite2/signup
#    puis My Account > Manage License Keys
export MAXMIND_LICENSE_KEY=votre_clé

# 2. Télécharger la base (~9 Mo)
python scripts/geoip_update.py --dest /app/data/geoip

# 3. Dans .env
GEOIP_DB_PATH=/app/data/geoip/GeoLite2-Country.mmdb
```

Le paquet `geoip2` est déjà dans `requirements.txt`. Le backend charge la base
au premier appel et l'utilise en repli des en-têtes Cloudflare. MaxMind la met à
jour deux fois par semaine : un cron hebdomadaire relançant le script suffit.

Si **aucune** des deux sources n'est configurée, rien ne casse : le pays reste
indéterminé et le sélecteur manuel fait foi.

---

## Diagnostiquer ce que l'ingress laisse passer

Plutôt que de deviner ce que votre hébergeur transmet au backend, mesurez-le.
Depuis l'extérieur :

```bash
curl -s https://<votre-domaine>/api/billing/geo-diagnostic | jq
```

```json
{
  "client_ip": "41.100.0.9",
  "detected_country": "DZ",
  "cloudflare_trusted": false,
  "geoip_db_configured": true,
  "headers_seen": {
    "cf_ipcountry": false,
    "cf_connecting_ip": false,
    "x_edge_secret": false,
    "x_forwarded_for_hops": 2
  },
  "asgi_client_is_private": true,
  "proxy_peer_trusted": true
}
```

Comment lire le résultat :

- **`client_ip` correspond à votre IP publique réelle** → la géolocalisation
  MaxMind fonctionnera. C'est la condition essentielle.
- **`client_ip` est `null`** ou vaut une adresse interne → si
  `proxy_peer_trusted` est `false`, le pair direct n'est pas reconnu comme
  relais : renseignez `TRUSTED_PROXY_CIDRS` avec la plage de l'ingress. Sinon,
  ajustez `TRUSTED_PROXY_HOPS` en vérifiant `x_forwarded_for_hops`. Sans IP
  réelle, **aucune** méthode de géolocalisation ne peut fonctionner.
- **Falsification** : rappelez la route avec
  `-H 'X-Forwarded-For: 8.8.8.8, 1.1.1.1'` ; `client_ip` doit rester votre IP
  réelle.
- **`headers_seen.cf_ipcountry` est `true`** → l'ingress laisse bien passer les
  en-têtes Cloudflare ; vous pouvez utiliser la voie Cloudflare ci-dessus.
- **`x_edge_secret` est `true` mais `cloudflare_trusted` est `false`** → la
  Transform Rule fonctionne mais `CLOUDFLARE_EDGE_SECRET` ne correspond pas
  (ou n'est pas chargé côté serveur).

Cette route ne divulgue que des informations sur la requête de l'appelant
lui-même — aucune donnée d'un autre utilisateur.
