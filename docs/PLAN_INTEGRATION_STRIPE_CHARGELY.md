# Plan technique — Intégration paiement Stripe / Chargely

> **Statut** : proposition à valider avant développement.
> **Contexte** : compte Stripe **en cours de vérification** — le mode test est
> déjà utilisable ; le mode live (clés `sk_live_…`) et les virements (payouts)
> s'activeront à la fin de la vérification. Chargely (Algérie, CIB/Edahabia)
> arrive dans un second temps.

Ce document décrit l'architecture cible, les objets Stripe à créer, les routes
backend, les webhooks, les variables d'environnement, la sécurité et le
découpage en phases. Aucun code n'est encore écrit : les boutons de
`frontend/public/pricing.html` sont aujourd'hui des `alert()`.

---

## 1. État des lieux

| Élément | Existant | À construire |
|---|---|---|
| Page tarifs | `frontend/public/pricing.html` (statique, boutons `alert()`) | Boutons → appels API Checkout |
| Comptes utilisateurs | `backend/routes/user_auth.py` — JWT en cookie httpOnly, MongoDB | Lien user ↔ client Stripe + abonnement |
| Système clés API | `backend/auth.py` — tiers free/basic/pro/admin | Attribution automatique du tier après paiement |
| Base de données | MongoDB (motor async), injectée via `set_database()` | Collections `subscriptions`, `payment_events` |
| Emails | `backend/services/email_service.py` (transactionnel) | Emails reçu / échec / annulation |
| Backend | FastAPI, routeurs centralisés dans `backend/routes/__init__.py` via `register_routes(api_router)` ; `api_router` a le préfixe `/api` | `backend/routes/billing.py` (+ `backend/services/stripe_service.py`) |

**Décision structurante** : le tier d'abonnement (Free/Starter/Pro/Business)
devient la **source de vérité de l'accès**. Après un paiement réussi, on met à
jour le tier de l'utilisateur, qui pilote à la fois l'accès à la plateforme
(cookie de session) et, si besoin, la génération d'une clé API du bon tier.

---

## 2. Architecture cible

```
Navigateur (pricing.html / React)
   │  1. POST /api/billing/checkout  {plan, cycle}  (cookie session JWT)
   ▼
FastAPI  backend/routes/billing.py
   │  2. Résout le prix selon le PAYS de facturation :
   │        - hors Algérie → Stripe
   │        - Algérie      → Chargely (phase 2 ; stub en phase 1)
   │  3. Crée/retrouve le Customer Stripe (stripe_customer_id sur le user)
   │  4. Crée une Checkout Session (mode=subscription)
   ▼
Stripe Checkout (page hébergée par Stripe — aucune donnée carte chez nous)
   │  5. Paiement → redirection success_url / cancel_url
   ▼
Stripe → Webhook  POST /api/billing/webhook
   │  6. Vérifie la signature (STRIPE_WEBHOOK_SECRET)
   │  7. checkout.session.completed / customer.subscription.updated|deleted
   │  8. Met à jour MongoDB (subscription) + tier user + envoie l'email
   ▼
Accès plateforme mis à jour
```

**Principe clé** : on ne fait **jamais** confiance à la redirection
`success_url` pour accorder l'accès. L'accès est accordé **uniquement** par le
webhook signé. La `success_url` sert seulement à afficher un message.

### Routage par pays (Stripe vs Chargely)

- Détection du pays : champ explicite choisi par l'utilisateur au checkout
  (sélecteur pays), **pas** de géo-IP silencieuse (cf. remarque de review sur la
  page statique : on ne promet pas de « sélection automatique »).
- `pays == DZ` → flux Chargely. Sinon → flux Stripe.
- Phase 1 : la branche Chargely renvoie un `501 Not Implemented` propre + un
  message « paiement local bientôt disponible », de façon à livrer Stripe seul
  sans casser l'UX algérienne.

---

## 3. Objets Stripe à créer (dashboard ou script)

Un **Product** par plan, avec deux **Prices** (mensuel / annuel) :

| Product | Price mensuel | Price annuel | Env var (id `price_…`) |
|---|---|---|---|
| Starter | 9 $/mois | 7 $/mois (84 $/an) | `STRIPE_PRICE_STARTER_M` / `_Y` |
| Pro | 19 $/mois | 15 $/mois (180 $/an) | `STRIPE_PRICE_PRO_M` / `_Y` |
| Business | 59 $/mois | 49 $/mois (588 $/an) | `STRIPE_PRICE_BUSINESS_M` / `_Y` |

Options à la carte (phase ultérieure) : utilisateur supplémentaire (5 $),
pack requêtes API (19 $), support prioritaire (15 $), formation (99 $ one-shot),
rapports sectoriels (paiement unique), certification (paiement unique).
→ Modélisés comme Prices additionnels ou `mode=payment` (one-shot).

> Les montants et `price_id` restent **côté serveur** (variables d'env). Le
> front n'envoie qu'un identifiant logique de plan (`pro`, `business`, cycle
> `monthly`/`annual`) ; le serveur choisit le `price_id`. Cela évite toute
> manipulation du prix depuis le navigateur.

---

## 4. Modèle de données (MongoDB)

**Champs ajoutés au document `users`** :
```
stripe_customer_id      : str | null
subscription_tier       : "free" | "starter" | "pro" | "business"
subscription_status     : "active" | "past_due" | "canceled" | "trialing" | null
subscription_id         : str | null   (sub_… Stripe)
subscription_current_end: datetime | null
billing_country         : str (ISO-2)
payment_provider        : "stripe" | "chargely" | null
```

**Collection `payment_events`** (idempotence + audit) :
```
event_id (unique)  : str   (evt_… Stripe — index unique pour rejouer sans doublon)
type               : str
customer_id        : str
received_at        : datetime
payload_digest     : str
```
L'index unique sur `event_id` garantit qu'un webhook rejoué par Stripe
(at-least-once delivery) n'est traité **qu'une seule fois**.

---

## 5. Routes backend (`backend/routes/billing.py`)

Le routeur `billing` (défini avec `APIRouter(prefix="/billing")`) est monté sur
`api_router`, lui-même préfixé par `/api` dans `server.py`. Les URLs effectives
sont donc préfixées par `/api` :

| Méthode | Route effective | Auth | Rôle |
|---|---|---|---|
| POST | `/api/billing/checkout` | session JWT requise | Crée la Checkout Session, renvoie l'URL de redirection |
| POST | `/api/billing/portal` | session JWT requise | Crée une session du **Customer Portal** Stripe (gérer/annuler l'abo, changer de carte) |
| GET | `/api/billing/subscription` | session JWT requise | Renvoie l'abonnement courant de l'utilisateur (pour le dashboard) |
| POST | `/api/billing/webhook` | **signature Stripe** (pas de JWT) | Reçoit et vérifie les événements, met à jour l'état |

**Enregistrement** — suivre le pattern existant, centralisé dans
`backend/routes/__init__.py` (fonction `register_routes(api_router)`), et non un
`include_router()` direct dans `server.py`. Le routeur billing relève de la
**couche SaaS** (comptes JWT), donc à ajouter à côté de `user_auth_router` /
`contact_router`, **sans** la dépendance `_auth` (clé API) :

```python
# backend/routes/__init__.py, section SaaS
from .billing import router as billing_router
...
api_router.include_router(billing_router)   # à côté de user_auth_router / contact_router
```

L'injection de la base se fait au démarrage dans `server.py`, à côté de
`set_user_auth_db(db)` :
`from routes.billing import set_database as set_billing_db` puis
`set_billing_db(db)`.

### Événements webhook traités
- `checkout.session.completed` → rattache `subscription_id` + `customer_id`, passe le tier, email « bienvenue / reçu ».
- `customer.subscription.updated` → met à jour statut + date de fin (renouvellement, `past_due`, changement de plan).
- `customer.subscription.deleted` → repasse le user en `free`, email « abonnement terminé ».
- `invoice.payment_failed` → statut `past_due`, email d'alerte.

---

## 6. Variables d'environnement (`.env.example`)

```
# --- Stripe ---
STRIPE_SECRET_KEY=sk_test_...           # sk_live_... après vérification
STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_PRICE_STARTER_M=price_...
STRIPE_PRICE_STARTER_Y=price_...
STRIPE_PRICE_PRO_M=price_...
STRIPE_PRICE_PRO_Y=price_...
STRIPE_PRICE_BUSINESS_M=price_...
STRIPE_PRICE_BUSINESS_Y=price_...
BILLING_SUCCESS_URL=https://afcfta-zlecaf.com/merci
BILLING_CANCEL_URL=https://afcfta-zlecaf.com/tarifs

# --- Chargely (phase 2) ---
CHARGELY_API_KEY=
CHARGELY_WEBHOOK_SECRET=
CHARGELY_ENABLED=false
```

Dépendance Python : `stripe` (SDK officiel) à ajouter dans `requirements.txt`.

---

## 7. Sécurité

- **Aucune donnée de carte** ne transite ni n'est stockée chez nous : Stripe
  Checkout est une page hébergée par Stripe → conformité PCI simplifiée (SAQ A).
- **Webhook signé** : vérification obligatoire de `Stripe-Signature` avec
  `STRIPE_WEBHOOK_SECRET`. Rejet `400` si invalide. La route (chemin effectif
  `/api/billing/webhook`) doit être **exemptée de la protection CSRF** (appel
  serveur-à-serveur, pas de cookie) — à ajouter à la liste d'exemptions du
  middleware CSRF existant en visant bien le chemin préfixé `/api`.
- **Idempotence** : index unique sur `payment_events.event_id`.
- **Autorité serveur sur les prix** : le front n'envoie jamais de montant.
- **Clés secrètes** uniquement côté backend (jamais dans le bundle React /
  la page statique) ; seule la clé publishable peut être exposée.
- **CORS** : la route reste derrière `ALLOWED_ORIGINS` déjà en place.
- **`success_url` non fiable** : l'accès n'est jamais accordé sur la simple
  redirection, seulement via le webhook.

---

## 8. Découpage en phases

**Phase 1 — Stripe abonnements (mode test)**
1. `backend/services/stripe_service.py` (SDK, création customer/session/portal, vérif signature).
2. `backend/routes/billing.py` (4 routes) + enregistrement dans `backend/routes/__init__.py`.
3. Champs `users` + collection `payment_events`.
4. Brancher les 3 boutons de plan de `pricing.html` sur `/billing/checkout`.
5. Emails reçu / échec / annulation via `email_service`.
6. Tests : signature webhook, idempotence, transitions de tier (mode test + Stripe CLI `stripe listen`).

**Phase 2 — Chargely (Algérie)**
7. `backend/services/chargely_service.py` symétrique + webhook Chargely.
8. Activer le branchement `pays == DZ` (retirer le stub `501`).
9. Facturation en DZD, emails localisés.

**Phase 3 — Options à la carte & one-shot**
10. Rapports sectoriels, certification, formation (`mode=payment`).
11. Add-ons récurrents (utilisateurs, packs API, support).

**Passage en live** : à la fin de la vérification Stripe, remplacer les clés
`sk_test_…`/`pk_test_…` par les clés live et recréer l'endpoint webhook live —
le code ne change pas.

---

## 9. Ce dont j'ai besoin de toi

- Confirmer la grille tarifaire (identique à `pricing.html` : 9/19/59 $, cycles annuels 7/15/49 $).
- Créer les Products/Prices côté Stripe (ou me laisser fournir un script `stripe` qui les crée) et me communiquer les `price_id` (via variables d'env, pas en clair ici).
- Confirmer les URLs `success`/`cancel` définitives.
- Valider l'ordre des phases ci-dessus.

Une fois ce plan validé, je démarre la **Phase 1 en mode test**.
