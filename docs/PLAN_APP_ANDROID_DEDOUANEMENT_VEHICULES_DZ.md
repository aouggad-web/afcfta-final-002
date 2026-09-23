# Plan — Application Android « Dédouanement Véhicules Algérie »

Calcul du coût complet de dédouanement d'un véhicule importé en Algérie
(neuf, ou d'occasion de moins de 3 ans), depuis l'Europe ou la Chine.

Statut : plan de conception. Aucun code applicatif n'est encore écrit.
Base : données et moteurs existants du dépôt `afcfta-final-002`.

---

## 1. Recherche préalable — cerner la problématique

### 1.1 Ce qui existe déjà dans le dépôt (audit réel)

| Actif | Emplacement | Verdict pour ce projet |
|---|---|---|
| Tarif douanier algérien crawlé | `backend/data/crawled/DZA_tariffs_enriched.json` (38 Mo, 17 115 sous-positions, source `conformepro.dz`) | **Réutilisable comme socle**, avec réserves (§1.4) |
| Chapitre 87 (véhicules) | 735 sous-positions, dont **198 sous la position 87.03** | Couverture nomenclature suffisante |
| Champs fiscaux par ligne | `dd_rate`, `tva_rate`, `tcs_rate`, `prct_rate`, `daps_rate`, `taxes_detail[]`, `fiscal_advantages[]`, `administrative_formalities[]` | Schéma exactement adapté au besoin |
| Moteur de calcul séquencé | `engine/calculation.py` | **Réutilisable tel quel** : gère assiette (`basis`), ordre (`sequence`), `CIF_PLUS_INCLUDED`, ad valorem / spécifique / mixte |
| Cas de test DZA validé | `engine/tests/test_calculation_dza.py` | Prouve la séquence DD→TCS→PRCT→TVA(sur CAF+DD+TCS+PRCT) |
| Adaptateurs DZA | `engine/adapters/dza_adapter.py`, `dza_conformepro_adapter.py`, `engine/converters/dza_converter.py` | Pipeline d'ingestion déjà en place |
| Fret maritime & THC | `backend/logistics_fees_data.py` (1 795 l.), `data/json/ports_africains_enhanced_maritime_logistics.json` | Utile mais **conteneurisé (TEU/FEU)** — pas de RoRo |
| Taux de change | `backend/exchange_rates/service.py` | Réutilisable (conversion EUR/CNY/USD → DZD) |
| Douanes DZ (bureaux) | `data/json/douanes_africaines.json` | Ports d'Alger et d'Oran seulement |
| API calcul | `backend/routes/calculator.py`, `enhanced_calculator.py` | Points d'entrée à étendre |
| Base mobile | `frontend/src/pwa/service-worker.js` | PWA existante — **aucune base Android native** |

### 1.2 Le problème métier, en clair

Le coût réel de mise à la route d'un véhicule importé en Algérie n'est
**pas** « la valeur × un taux ». C'est la somme de quatre blocs que les
importateurs (particuliers comme concessionnaires) découvrent séquentiellement,
souvent après l'achat, et dont la mauvaise estimation est la première cause de
véhicule bloqué au port :

1. **Frais dans le pays d'expédition** (Europe ou Chine)
2. **Transport et assurance** jusqu'au port algérien
3. **Droits et taxes de douane algériens**
4. **Frais connexes en Algérie** — la partie la plus volatile, car
   dépendante du **temps** passé au port

Le bloc 4 est celui qui fait exploser les budgets : magasinage et surestaries
sont des **fonctions du nombre de jours**, donc du délai de constitution du
dossier. Une application qui ne modélise que le bloc 3 rate l'essentiel.

### 1.3 Cadre réglementaire à modéliser (points structurants)

- **Éligibilité** : deux régimes juridiquement distincts, à ne jamais confondre
  dans l'UI —
  - *Véhicule neuf* : réservé aux **concessionnaires agréés** (agrément,
    cahier des charges, quotas). Un particulier ne peut pas l'emprunter.
  - *Véhicule d'occasion* : ouvert au **particulier résident**, véhicule de
    **moins de 3 ans**, normes d'émission et de conformité technique, périodicité
    limitée par personne, et **paiement en devises propres** de l'importateur.
- **Contrôle des changes** : **domiciliation bancaire** préalable obligatoire
  (Banque d'Algérie) pour l'importation commerciale — génère ses propres frais
  et conditionne le dossier.
- **Valeur en douane** : valeur transactionnelle CAF, mais l'administration
  applique des **valeurs de référence / cotes** pour l'occasion, avec
  abattement de vétusté. → l'app doit exposer **deux valeurs** (déclarée vs
  retenue) et calculer sur la plus haute.
- **Ordre d'application des taxes** (déjà codé, cf. `engine/calculation.py`) :
  DD, TCS, PRCT sur CAF ; **TVA sur CAF + DD + TCS + PRCT**. Toute taxe
  additionnelle (TIC, DAPS) doit être insérée avec sa `sequence` et son
  assiette propre, pas empilée sur le total.
- **ZLECAf non pertinente ici** : l'origine est Europe ou Chine, donc régime
  **NPF**. Le champ `fiscal_advantages` ZLECAf du dataset doit être
  explicitement neutralisé pour ce parcours (sinon faux gain affiché).
  L'Accord d'Association **UE-Algérie** est, lui, potentiellement pertinent
  pour l'origine européenne et doit être traité comme régime préférentiel
  distinct (§3.3).

### 1.4 Écarts de données identifiés — **à traiter avant tout développement**

Ce sont les risques qui déterminent la crédibilité de l'application.

1. **DD uniforme à 5 % sur tout le chapitre 87** — vérifié : les 735
   sous-positions du chapitre 87 portent `dd_rate = 5.0`. C'est le taux des
   **collections CKD/SKD destinées au montage**, pas celui des véhicules
   finis. Publier un calcul sur cette base produirait une **sous-estimation
   massive**. → *blocage n°1 : re-sourcer les taux DD de 87.03 par cylindrée
   et motorisation depuis le tarif officiel DGD.*
2. **Incohérence inter-sources** : `frontend/public/DZA_tarif_douanier_echantillon.csv`
   donne DD = 5 % pour la ligne 0101211100, le JSON crawlé donne 15 % pour la
   même ligne. → *une règle de priorité de source et un test de non-régression
   sont nécessaires.*
3. **TIC absente** : aucune Taxe Intérieure de Consommation dans
   `taxes_detail` du chapitre 87 (seuls D.D, PRCT, T.V.A apparaissent). Or
   c'est une composante majeure du coût d'un véhicule. → *à ajouter comme
   mesure barémée.*
4. **TCS à 0 % sur tout le chapitre 87** — cohérent (taxe sanitaire), mais à
   confirmer plutôt qu'à supposer.
5. **Aucune donnée de magasinage ni de surestaries** : `grep` sur
   `surestarie|demurrage|magasinage` ne retourne que du vrac et des ports
   génériques. → *barèmes à créer intégralement.*
6. **Aucune donnée RoRo** : le fret disponible est conteneurisé (TEU/FEU/THC).
   Or le véhicule voyage majoritairement en **RoRo**, tarifé au m³ ou à
   l'unité. → *barème à créer.*
7. **Ports DZ incomplets** : seuls Alger et Oran sont référencés ; il manque
   Djen Djen, Mostaganem, Skikda, Annaba, Béjaïa.
8. **Aucune base Android** : le dépôt est FastAPI + React/PWA.

> **Conclusion de la recherche** : le dépôt fournit un excellent *moteur* et un
> *schéma* de données, mais les *valeurs* propres au dédouanement automobile
> sont soit fausses (DD 87.03), soit absentes (TIC, magasinage, surestaries,
> RoRo). Le plan ci-dessous fait donc de la **remédiation des données le
> chemin critique**, avant l'UI.

---

## 2. Périmètre de l'application

**Entrée utilisateur** → **Sortie : coût total de mise à la route, ligne par ligne, en DZD et en devise d'achat.**

### 2.1 Entrées
- Profil : particulier / concessionnaire agréé / société
- Origine : **Europe** (pays) ou **Chine**
- État : neuf / occasion (avec date de 1re mise en circulation → contrôle des 3 ans)
- Véhicule : marque, modèle, énergie (essence / diesel / hybride / électrique),
  cylindrée (cm³) ou puissance (kW pour l'électrique), poids, VIN optionnel
- Valeur d'achat + devise + Incoterm (EXW / FOB / CFR / CIF)
- Mode de transport : RoRo / conteneur / groupage
- Port de départ / port d'arrivée algérien
- Délai estimé d'enlèvement (jours) → pilote magasinage et surestaries

### 2.2 Sortie — les quatre blocs

**Bloc A — Pays d'expédition**
Prix d'achat HT, expertise / contrôle technique export, certificat de
conformité (CoC européen ; CCC + inspection pré-embarquement pour la Chine),
plaques et carte grise d'exportation, frais de dossier du vendeur ou du
mandataire, acheminement jusqu'au port, manutention à l'embarquement,
douane export, éventuelle récupération / exonération de TVA à l'export.

**Bloc B — Transport international**
Fret RoRo (unité ou m³) ou conteneur (part d'un 40′ partagé), surcharges
carburant et sécurité, assurance sur facultés (typiquement calculée sur
CAF + marge), THC au départ.

**Bloc C — Droits et taxes algériens** *(moteur `engine/calculation.py`)*
Assiette CAF retenue → D.D (par cylindrée / énergie), TCS, PRCT, DAPS le cas
échéant, **TIC**, puis **TVA 19 % sur CAF + DD + TCS + PRCT (+ TIC)**,
taxe de formalité douanière. Régime NPF, ou préférentiel UE si origine et
preuve d'origine le permettent.

**Bloc D — Frais connexes en Algérie**
THC à l'arrivée, **magasinage** (franchise puis barème progressif par jour),
**surestaries** conteneur (jours francs puis paliers), frais de transitaire /
commissionnaire en douane, frais de documentation et de déclaration (D10),
scanner, expertise et visite, certificat de conformité technique, frais
bancaires de domiciliation et de transfert, acheminement port → domicile,
carte grise et immatriculation, contrôle technique, assurance locale.

### 2.3 Ce que l'application **ne** fait **pas**
Elle ne délivre pas d'avis douanier opposable, ne préremplit aucune
déclaration officielle, et n'effectue aucun paiement. Le disclaimer déjà
présent dans le dépôt (`LEGAL_DISCLAIMER_FR`) est repris tel quel et affiché
sur chaque simulation.

---

## 3. Architecture

### 3.1 Vue d'ensemble

```
Android (Kotlin, Jetpack Compose)
        │  Retrofit / OkHttp — JSON
        ▼
FastAPI  /api/v1/vehicle-clearance/*   (backend existant, nouvelles routes)
        ▼
VehicleClearanceService  ── orchestre les 4 blocs
        ├── engine/calculation.py            (bloc C — RÉUTILISÉ)
        ├── VehicleTariffResolver            (NOUVEAU — 87.03 par critères)
        ├── CustomsValueResolver             (NOUVEAU — vétusté, cote)
        ├── OriginFeesService                (NOUVEAU — bloc A)
        ├── FreightService                   (bloc B — étend logistics_fees_data)
        ├── PortChargesService               (NOUVEAU — bloc D, temps-dépendant)
        └── exchange_rates/service.py        (RÉUTILISÉ)
```

**Décision d'architecture : calcul côté serveur, pas côté téléphone.** Les
barèmes fiscaux et portuaires changent à chaque loi de finances et à chaque
tarif portuaire. Embarquer la logique dans l'APK imposerait une mise à jour du
Play Store à chaque changement. Le serveur reste la source de vérité ; le
téléphone met en cache pour l'usage hors ligne.

### 3.2 Mode hors ligne
Un « **pack tarifaire** » versionné (chapitre 87 + barèmes + taux de change du
jour, quelques centaines de Ko) est téléchargé et stocké en **Room**. Le calcul
hors ligne rejoue la même séquence, et **chaque résultat hors ligne est
horodaté et marqué comme tel**. Au retour du réseau, l'app recalcule côté
serveur et signale tout écart. Pas de résultat hors ligne présenté comme
définitif.

### 3.3 Modèle de données (extension du schéma canonique existant)

On n'invente pas un nouveau schéma : on ajoute des `Measure` au modèle
`engine/schemas/canonical_model.py`, chacune avec sa `sequence`, sa `basis` et
ses `basis_includes`. La TIC devient une mesure barémée par cylindrée ; le
régime préférentiel UE devient un second jeu de taux, exactement comme
`zlecaf_rate_pct` l'est aujourd'hui.

Nouvelles tables de barèmes (JSON versionnés, sous `data/algeria-vehicles/`) :

| Fichier | Contenu | Clé |
|---|---|---|
| `dd_87xx_by_criteria.json` | DD par position / énergie / cylindrée | ré-sourcé DGD |
| `tic_vehicles.json` | Barème TIC | par cylindrée et énergie |
| `customs_value_reference.json` | Cotes et abattement vétusté | par âge |
| `port_storage_tariffs.json` | Magasinage par port : franchise + paliers/jour | par port |
| `demurrage_tariffs.json` | Surestaries : jours francs + paliers | par armateur / type |
| `roro_freight.json` | Fret RoRo | origine → port DZ, m³ ou unité |
| `origin_country_fees.json` | Bloc A | EU par pays, CN |
| `dz_ancillary_fees.json` | Transit, doc, scanner, expertise, banque, immat. | par poste |

Chaque fichier porte `as_of`, `source_name`, `source_url` et un
`data_status` (`VERIFIED` / `DOCUMENTED` / `ESTIMATED`), repris de la
convention déjà en vigueur dans `data/algeria-active-3/tariff_enrichment_registry.json`.
**Toute valeur non sourcée s'affiche comme estimation, jamais comme un montant ferme.**

### 3.4 API

```
GET  /api/v1/vehicle-clearance/eligibility        profil + âge → éligible / motifs
GET  /api/v1/vehicle-clearance/hs-resolve         critères véhicule → code 10 chiffres candidat
POST /api/v1/vehicle-clearance/simulate           entrées complètes → décomposition 4 blocs
GET  /api/v1/vehicle-clearance/ports              ports DZ + barèmes actifs
GET  /api/v1/vehicle-clearance/offline-pack       pack versionné (ETag)
POST /api/v1/vehicle-clearance/scenarios/compare  jusqu'à 3 scénarios
```

La réponse de `simulate` reprend la forme de `CalculationResult` :
`lines[]` avec pour chaque poste `code`, `name_fr`, `basis_label`,
`basis_amount`, `amount`, `legal_reference`, plus `warnings[]` et
`data_status`. **Aucun total n'est affiché sans sa décomposition.**

---

## 4. Application Android

**Stack** : Kotlin, Jetpack Compose (Material 3), MVVM, Hilt, Retrofit,
Room, DataStore, WorkManager (rafraîchissement du pack), minSdk 24.
**Langues** : français et arabe, avec **support RTL complet** dès la première
version — non négociable pour le marché visé.

### Parcours en 6 écrans

1. **Profil & éligibilité** — particulier / concessionnaire, résidence ; le
   contrôle des 3 ans se fait ici, avant toute saisie de prix, et **bloque**
   avec un motif explicite plutôt que d'afficher un calcul inutile.
2. **Véhicule** — origine, énergie, cylindrée, date de 1re mise en
   circulation ; résolution assistée du code SH à 10 chiffres, toujours
   modifiable manuellement et affichée à l'utilisateur.
3. **Achat & transport** — valeur, devise, Incoterm, RoRo/conteneur, ports.
4. **Délais** — jours estimés avant enlèvement, avec un curseur ; c'est
   l'écran qui rend visible le coût du temps.
5. **Résultat** — quatre blocs repliables, décomposition ligne à ligne,
   double affichage DZD / devise d'achat, part de chaque bloc dans le total.
6. **Comparaison & export** — jusqu'à 3 scénarios (Europe vs Chine, RoRo vs
   conteneur, 10 vs 30 jours), export PDF, partage.

### Principes d'interface
- Le **total apparaît en permanence** en bas d'écran et se met à jour à chaque
  saisie.
- Chaque poste porte une icône « pourquoi ce montant » ouvrant l'assiette, le
  taux et la référence légale.
- Les postes estimés sont **visuellement distincts** des postes sourcés.
- Le disclaimer est présent sur le résultat et sur le PDF exporté.

---

## 5. Lots de travail

| Lot | Objet | Dépend de | Livrable de sortie |
|---|---|---|---|
| **L0** | **Remédiation des données** : re-sourcer DD 87.03, ajouter TIC, arbitrer CSV vs JSON, compléter les ports DZ | — | Jeux de barèmes `VERIFIED`, tests de non-régression |
| **L1** | Barèmes frais connexes : magasinage, surestaries, RoRo, bloc A | L0 | 8 fichiers JSON versionnés + schéma de validation |
| **L2** | Extension moteur : mesures TIC/DAPS séquencées, régime préférentiel UE, valeur en douane avec vétusté | L0 | Tests unitaires sur cas réels |
| **L3** | Services et API des 4 blocs | L1, L2 | Routes documentées + tests d'intégration |
| **L4** | Android — socle, navigation, réseau, Room, i18n FR/AR + RTL | L3 (contrat d'API) | APK de démonstration |
| **L5** | Android — les 6 écrans | L4 | Parcours complet |
| **L6** | Hors ligne, comparaison de scénarios, export PDF | L5 | Version candidate |
| **L7** | Validation terrain avec transitaires, recette, publication | L6 | Version 1.0 |

L0 et L1 sont le chemin critique : sans eux, l'application calcule vite et
faux. L4 peut démarrer en parallèle de L2/L3 dès que le contrat d'API est figé.

---

## 6. Validation

- **Non-régression fiscale** : le cas `test_calculation_dza.py` reste vert ;
  on lui ajoute des cas 87.03 (essence 1600 cm³, diesel 2000 cm³, électrique,
  neuf vs occasion 30 mois).
- **Contrôle par l'existant** : chaque simulation est confrontée à des
  **dossiers de dédouanement réels** fournis par des transitaires — c'est le
  seul juge de paix. Objectif : écart inférieur à 5 % sur le bloc C, inférieur
  à 15 % sur le bloc D (irréductiblement variable).
- **Test des bornes** : véhicule de 35 mois vs 37 mois, cylindrée à la limite
  d'une tranche, enlèvement à J+0 et à J+60.
- **Fraîcheur des données** : toute simulation utilisant un barème dont
  l'`as_of` dépasse un seuil affiche un avertissement.

---

## 7. Risques

| Risque | Effet | Traitement |
|---|---|---|
| DD 87.03 erroné (5 % uniforme) — **confirmé** | Sous-estimation majeure, perte de crédibilité | L0 bloquant : re-sourcer avant toute publication |
| Barèmes portuaires non publics | Bloc D peu fiable | Conventions avec transitaires ; marquer `ESTIMATED` sans détour |
| Instabilité réglementaire (loi de finances annuelle) | Obsolescence | Barèmes versionnés et datés côté serveur, jamais figés dans l'APK |
| Valeur en douane retenue ≠ valeur déclarée | Écart perçu comme un bug | Afficher les deux valeurs et expliquer laquelle sert d'assiette |
| Confusion des régimes neuf / occasion | Utilisateur induit en erreur sur son droit à importer | Séparation dès l'écran 1, blocage motivé |
| Faux gain ZLECAf hérité du dataset | Montant faux à la baisse | Neutraliser explicitement `fiscal_advantages` ZLECAf pour origine UE/CN |

---

## 8. Décision demandée avant de coder

1. Confirmer la **source officielle** retenue pour les taux DD/TIC du
   chapitre 87 (tarif DGD, édition et millésime).
2. Confirmer l'accès à des **barèmes portuaires réels** (magasinage,
   surestaries) et à des **dossiers de dédouanement clos** pour la recette.
3. Trancher : **Android natif** (ce plan) ou extension de la PWA existante —
   le natif est retenu ici pour le hors ligne, mais la PWA réutiliserait
   davantage de code existant.
