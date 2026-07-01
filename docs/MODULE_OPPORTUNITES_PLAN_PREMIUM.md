# Module « Opportunités » Premium — Plan d'évolution

_Plateforme ZLECAf / AfCFTA — Note de cadrage produit & technique_
_Créé le : 2026-07-01_
_Document compagnon de `MODULE_OPPORTUNITES_STRATEGIE.md` (qui décrit l'existant retiré de la plateforme)._

---

## 0. Objet du document

Le module Opportunités a été **retiré de l'interface publique** (PR #178) parce
qu'il dépendait de flux commerciaux fins (par produit, bilatéraux) exigeant un
accès **OEC en direct** aujourd'hui indisponible/instable, tout en conservant
l'intégralité du code pour une reprise.

Ce document **établit le plan de cette reprise** : transformer Opportunités en un
**outil ultra-premium de génération de rapports sectoriels et périodiques à la
demande**, en **intégrant de nouveaux indicateurs et jeux de données** — et en
particulier en **connectant la logistique et le système bancaire**, deux modules
déjà riches de la plateforme mais aujourd'hui cloisonnés de l'analyse
d'opportunités.

Le fil directeur reste **inchangé** : *tout chiffre affiché doit être réel et
traçable, ou clairement signalé comme indisponible — jamais inventé.*

---

## 1. Vision produit

### 1.1 Positionnement

De **onglet exploratoire gratuit** → vers **service d'intelligence commerciale
premium**, réservé à des clients identifiés (institutions, agences de promotion
des exportations, banques, grands exportateurs), délivrant des **rapports
actionnables** plutôt que des tableaux à explorer soi-même.

### 1.2 Proposition de valeur différenciante

L'apport unique n'est pas « encore des chiffres de commerce » — c'est de
**boucler la chaîne de décision d'export** en un seul rapport :

> **« Quel produit, vers quel marché, à quel coût rendu, financé comment, avec
> quel risque ? »**

Aujourd'hui la plateforme sait répondre séparément à :
- *quoi/où* (flux OEC, substitution, capacités de production) — module Opportunités ;
- *comment l'acheminer et à quel coût* (ports, aéroports, corridors, THC, frais) — module Logistique ;
- *comment le payer/financer et avec quel risque* (trade finance, change, PAPSS, risque pays) — module Banque.

Le module premium **fusionne ces trois angles** en un score et un récit
d'opportunité **de bout en bout**. C'est la synthèse logistique + bancaire qui
justifie le positionnement ultra-premium.

---

## 2. Nouveaux indicateurs & sources de données

### 2.1 Déjà disponibles dans la plateforme (à brancher, pas à créer)

| Domaine | Actif existant | Ce qu'il apporte à Opportunités |
|---------|----------------|----------------------------------|
| Commerce | `real_trade_data_service` (OEC), Afreximbank ATR 2026 (`afreximbank_atr2026.json`) | Flux par produit/bilatéraux ; ancrage macro intra-africain réel (213,8 Md$, exports 685,2 Md$) |
| Économie pays | `country_data.REAL_COUNTRY_DATA` (54 pays) | PIB, croissance, IDH, secteurs, exports/imports principaux |
| Production | `production_capacity_service` (FAO/USGS/UNIDO/BM) | Capacité réelle d'export africaine par produit (borne les potentiels) |
| Nomenclature | `etl/hs6_database` (WCO HS 2022, ~5 800 codes) | Univers produit, désignations |
| **Logistique** | `routes/logistics.py` (+ `logistics_data`, `logistics_air_data`, `logistics_land_data`, `free_zones_data`, `logistics_*_fees_data`, `multimodal_freight_service`) | Ports (TEU), aéroports (cargo), corridors terrestres, zones franches, opérateurs, **frais/THC/coût de route**, comparaison multimodale |
| **Banque** | `routes/banking.py` (+ `banking_system`, `currencies`, `exchange_rates`) | Banques par pays, banques régionales, **change (taux/conversion)**, **trade finance (instruments + recommandation)**, **systèmes de paiement (PAPSS, SWIFT, mobile money)**, **évaluation du risque pays**, conformité |

> **Point clé :** logistique et banque ne sont pas à construire — elles existent
> avec leurs endpoints. Le travail est de les **appeler depuis le moteur
> d'opportunités** et de les **agréger** dans le rapport.

### 2.2 À intégrer via API payantes / externes (reprise premium)

| Source | Nature | Statut |
|--------|--------|--------|
| **OEC — plan payant** | Flux BACI/Comtrade complets, à jour, sans blocage réseau | Cible principale (lève le 403 actuel) |
| UN Comtrade (premium) | Alternative/complément flux | À évaluer |
| WITS / Banque Mondiale | Tarifs NPF & préférentiels détaillés | À évaluer (partiellement déjà curé) |
| Indices logistiques (LPI Banque Mondiale, indices de connectivité maritime CNUCED) | Qualité/coût logistique par pays | À intégrer côté Logistique |
| Barrières non tarifaires (base ONE-STOP / tradebarriers.africa) | BNT par produit/marché | Nouveau — comble l'avertissement §6.7 de la stratégie |
| Risque pays (notations, indices de gouvernance) | Enrichit l'évaluation risque bancaire | À évaluer |

Chaque nouvelle source suit la **discipline de non-fabrication** : champ sourcé
→ affiché avec attribution ; champ non sourçable → `null`/« — ».

### 2.3 Nouveaux indicateurs composites proposés

Tous **calculés** à partir de sources réelles, jamais saisis :

1. **Coût rendu estimé (landed cost)** = valeur FOB + fret (logistique : route/THC/frais) + coûts de change (banque). Renvoyé avec la décomposition et les sources ; `null` si un maillon manque.
2. **Indice de faisabilité de financement** = disponibilité d'instruments trade finance + couverture PAPSS + profil de risque pays (module banque).
3. **Score d'opportunité de bout en bout** = combinaison transparente et pondérée de : potentiel de marché (flux OEC), capacité d'export (production), accessibilité logistique, faisabilité financière, risque. **Pondérations affichées et paramétrables** — pas de boîte noire.
4. **Fenêtre tarifaire ZLECAf** = gain tarifaire à date selon le calendrier de démantèlement (déjà calculé par `dismantlement`).

---

## 3. Possibilités fonctionnelles (rapports à la demande)

### 3.1 Types de rapports

- **Rapport sectoriel** : un produit / chapitre SH → marchés cibles classés par score de bout en bout, avec volet logistique et volet financement par marché.
- **Rapport pays** : un pays exportateur → portefeuille d'opportunités priorisées.
- **Rapport corridor** : une paire origine-destination → produits porteurs + itinéraire logistique optimal + montage financier type.
- **Rapport périodique** (abonnement) : réédition automatique (mensuelle/trimestrielle) avec suivi d'évolution des indicateurs.

### 3.2 Contenu type d'un rapport sectoriel

1. Synthèse exécutive (texte IA **étiqueté**, chiffres sourcés).
2. Demande de marché : importateurs africains du produit (OEC), tendances (Afreximbank/OEC).
3. Offre : capacités de production africaines (FAO/USGS/UNIDO).
4. **Volet logistique** : ports/aéroports/corridors desservant les marchés, coût de route, comparaison multimodale, zones franches pertinentes.
5. **Volet bancaire/financier** : instruments de trade finance recommandés, couverture PAPSS/paiement, taux de change, évaluation du risque pays.
6. Cadre tarifaire ZLECAf : gain tarifaire à date, NPF vs préférentiel.
7. Score de bout en bout + décomposition + limites de données explicites.
8. Sources & horodatage.

---

## 4. Architecture cible

### 4.1 Principe

Réutiliser l'architecture « un service `real_*` par angle » de la stratégie, et
ajouter une **couche d'orchestration** qui compose commerce + logistique +
banque en un rapport.

```
                    ┌─────────────────────────────────────────────┐
                    │  report_engine  (nouveau — orchestrateur)     │
                    │  compose + calcule les indicateurs composites │
                    └───────────────┬───────────────────────────────┘
        ┌───────────────────────────┼───────────────────────────────┐
        ▼                           ▼                               ▼
  Commerce                     Logistique                        Banque
  real_trade_data_service      logistics_* / multimodal_freight  banking_system / currencies
  real_product/comparison/…    (ports, air, land, fees, zones)   exchange_rates
  production_capacity_service                                     (trade finance, PAPSS, risque)
  afreximbank_data
        │
        ▼
  Sources externes payantes (OEC plan payant, WITS, LPI, BNT…)  ← connecteurs à ajouter
```

### 4.2 Nouveaux composants à créer

- `services/report_engine.py` — orchestrateur : reçoit une requête de rapport, appelle les services d'angle **en parallèle** (`asyncio.gather`), calcule les indicateurs composites (§2.3), assemble un objet rapport structuré.
- `services/logistics_opportunity_adapter.py` — expose au moteur les coûts/itinéraires logistiques pour une paire produit/marché (enrobe `logistics_*` + `multimodal_freight_service`).
- `services/finance_opportunity_adapter.py` — expose faisabilité de financement, PAPSS, change, risque (enrobe `banking_system` + `exchange_rates`).
- `routes/reports.py` — endpoints premium (§4.3), protégés par contrôle d'accès (§5).
- Génération de sortie : rapport JSON structuré → rendu **PDF/HTML** (gabarit), pour livraison client.

### 4.3 Endpoints premium envisagés

- `POST /reports/sectoral` (produit/chapitre → rapport)
- `POST /reports/country` (pays → portefeuille)
- `POST /reports/corridor` (origine-destination → rapport)
- `GET  /reports/{id}` (récupération), `GET /reports/{id}/pdf`
- `POST /reports/subscriptions` (rapports périodiques)

### 4.4 Réutilisation de l'existant

Les endpoints logistique (`/logistics/fees/route`, `/logistics/multimodal/compare`,
`/logistics/land/fees/cost`, `/logistics/air/fees/cost`…) et banque
(`/banking/trade-finance/recommend`, `/banking/payment-systems/regional`,
`/banking/forex/convert`, `/banking/countries/{code}/risk-assessment`) existent
déjà : les adaptateurs les appellent en interne plutôt que de dupliquer la
logique.

---

## 5. Contrôle d'accès & offre premium

- **Tiers d'accès** : `public` (reste de la plateforme) / `premium` (rapports à la demande) / `enterprise` (périodiques + volumes + export). L'auth existante (`require_auth`, MongoDB) fournit le socle ; ajouter un champ de tier et une vérification sur `routes/reports.py`.
- **Quotas & journalisation** : nombre de rapports/mois par tier ; horodatage et traçabilité des sources par rapport généré.
- **Facturation** : hors périmètre technique immédiat, mais l'architecture (tier + quotas) doit la permettre.
- **Dégradation gracieuse** : si une source payante (OEC) est momentanément indisponible, le rapport est **généré partiel et étiqueté**, jamais complété par des valeurs inventées.

---

## 6. Feuille de route par phases

| Phase | Contenu | Dépendances |
|-------|---------|-------------|
| **P0 — Socle** | Réactiver le code conservé en environnement de déploiement avec **OEC payant** ; valider les services `real_*` de bout en bout avec de vrais chiffres | Accès OEC payant |
| **P1 — Adaptateurs** | `logistics_opportunity_adapter` + `finance_opportunity_adapter` (branchement des modules existants) | P0 |
| **P2 — Moteur & indicateurs** | `report_engine` + indicateurs composites (landed cost, faisabilité financement, score bout-en-bout) | P1 |
| **P3 — Rapports & rendu** | `routes/reports.py`, gabarits PDF/HTML, rapports sectoriel/pays/corridor | P2 |
| **P4 — Premium & périodiques** | Tiers/quotas, abonnements, rapports périodiques automatiques | P3 |
| **P5 — Enrichissement** | BNT, LPI, indices de connectivité, risque pays externes | En continu |

---

## 7. Garde-fous (rappel)

1. **Non-fabrication** : aucun `random.*`, aucun chiffre LLM présenté comme factuel ; champ non sourçable → `null`/« — ». L'IA rédige le texte, **jamais les chiffres**.
2. **Traçabilité** : chaque indicateur porte sa/ses source(s) et un horodatage ; les indicateurs composites exposent leur **décomposition et leurs pondérations**.
3. **Déterminisme** : deux rapports identiques (mêmes entrées, même instantané de données) donnent le même résultat.
4. **Validation OEC réelle** : à faire sur l'environnement de déploiement (le dev est bloqué 403).
5. **Données ≠ conseil** : le rapport éclaire une décision, il ne la remplace pas ; limites de données affichées explicitement.

---

_Fin du document._
