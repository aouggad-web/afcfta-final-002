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

## Étape 3 — Laisser passer les en-têtes de proxy

Le conteneur lance uvicorn avec `--proxy-headers --forwarded-allow-ips`. Par
défaut, seul `127.0.0.1` est accepté, donc l'IP réelle du client serait perdue.
Dans `.env` :

```
UVICORN_FORWARDED_ALLOW_IPS=*      # correct derrière un Tunnel ou un pare-feu fermé
```

Avec `*`, ne laissez **jamais** l'origine ouverte à l'Internet public : la
combinaison des deux permettrait d'usurper `X-Forwarded-For`.

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

## Sans Cloudflare

L'alternative est une base **MaxMind GeoLite2** locale (compte gratuit) :

```
pip install geoip2
GEOIP_DB_PATH=/chemin/vers/GeoLite2-Country.mmdb
```

Elle se met à jour manuellement (ou par cron) et fonctionne sans dépendance
externe à l'exécution. Le backend l'utilise automatiquement dès que le chemin
est renseigné, en repli des en-têtes Cloudflare.

Si **aucune** des deux sources n'est configurée, rien ne casse : le pays reste
indéterminé et le sélecteur manuel fait foi — c'est le comportement actuel.
