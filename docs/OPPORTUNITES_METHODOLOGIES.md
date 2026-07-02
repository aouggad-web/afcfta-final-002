# Module Opportunités — Méthodologies par scénario

Document de référence : **comment chaque indicateur et chaque scénario sont calculés**, avec formules, sources de données, et leviers d'amélioration. Objectif : permettre de travailler/ajuster la méthodologie en connaissance de cause.

## Principe transversal : zéro fabrication

- Toute valeur est **réelle et sourcée**, ou marquée `available: false` (jamais inventée).
- Une **estimation** (modèle) est autorisée mais **toujours étiquetée** `is_estimation: true` avec sa formule, ses intrants et ses sources — distincte visuellement du mesuré.
- Les **pondérations** des scores composites sont exposées dans le payload (jamais une boîte noire) et **renormalisées** sur les seules composantes disponibles.

---

## 1. Briques de données (réutilisées par tous les scénarios)

| Brique | Service | Source réelle | Sortie clé |
|---|---|---|---|
| Production (offre) | `production_capacity_service` | FAO (FAOSTAT), USGS, UNIDO | part continentale, rang, volume |
| Logistique | `logistics_opportunity_adapter` → `multimodal_freight_service` + `free_zones_data` | modèle coût-distance (UNCTAD MRTS, Drewry) | modes opérationnels, coût, délai, zones franches |
| Finance | `finance_opportunity_adapter` → `banking_system` + `exchange_rates` + macro | trade finance, PAPSS, risque pays, FX | instruments, couverture paiement, risque, taux |
| Macro | `macro_indicators_service` | Mo Ibrahim (GAI), World Gold Council (or), World Bank WDI (réserves, PIB/hab) | GAI, réserves de change, couverture d'import |
| Tarif | `benchmarking_service._resolve_hs6` + `authentic_tariff_service` | barèmes nationaux + démantèlement ZLECAf | droit national, taux ZLECAf, avantage |
| Demande | `demand_estimation_service` | production + population (`constants`) + PIB/hab + OEC | besoin national estimé, imports observés |
| Commerce | `real_trade_data_service` | OEC / BACI (payant/gratuit) | importateurs par produit (HS4/HS6) |

---

## 2. Indicateurs composites (formules exactes)

### 2.1 Coût rendu (landed cost)
```
coût_rendu = valeur_FOB + fret_opérationnel_le_moins_cher
```
Indisponible si l'une des jambes manque (jamais estimé). FX traité séparément (volet finance).

### 2.2 Sous-score offre (supply_capacity)
```
subscore = min(part_continentale / 25 , 1.0)     # ≥25% de part = 1.0
```
(À défaut de part : 0.5 si un volume existe, sinon 0.0.)

### 2.3 Indice d'accessibilité logistique
```
base   = min(modes_opérationnels, 3) / 3 × 0.7
bonus  = {high: 0.3, medium: 0.15, low: 0.05}[faisabilité_du_moins_cher]
indice = min(base + bonus , 1.0)
```

### 2.4 Indice de faisabilité de financement
Somme pondérée, **renormalisée sur les composantes disponibles** :
| Composante | Poids | Condition de gain |
|---|---|---|
| Instruments trade finance | 0.30 | instruments recommandés présents |
| PAPSS / système partagé | 0.20 | couverture PAPSS |
| Risque pays | 0.30 | vert=1.0 / orange=0.5 / rouge=0.2 |
| Couverture d'import (≥3 mois) | 0.20 | proportionnel, plafonné |

### 2.5 Sous-score risque pays
```
subscore = max(0, 1 − risk_score/10)     # risk_score sur 0–10
```

### 2.6 Score de bout en bout (end-to-end)
Moyenne pondérée des composantes **disponibles**, renormalisée :
```
score = Σ(poids_i × subscore_i) / Σ(poids_i disponibles)
```
Poids par défaut (`DEFAULT_WEIGHTS`, surchargeables) :
| Composante | Poids |
|---|---|
| market_potential (demande OEC par produit) | 0.25 |
| supply_capacity | 0.25 |
| logistics_accessibility | 0.20 |
| financing_feasibility | 0.20 |
| country_risk | 0.10 |
> `market_potential` requiert l'OEC payant → aujourd'hui **exclu** (jamais estimé dans le score). `weight_coverage` indique la fraction de poids réellement couverte.

### 2.7 Avantage tarifaire ZLECAf (réel)
```
hs6            = résolution HS4/HS5 → sous-position HS6 réelle (préfixe) sinon pad "00"
avantage_%     = max(droit_national − taux_ZLECAf , 0)     # taux ZLECAf manquant = 0 (cible AfCFTA, hypothèse documentée)
gain_par_1000$ = avantage_% / 100 × 1000
indice_tarif   = min(avantage_% / 20 , 1.0)                # 20% d'économie = 1.0
```
Indisponible si aucune ligne tarifaire pour le pays/produit.

### 2.8 Matrices de segmentation
**Effort / impact :**
```
effort = min( (fret / valeur_FOB) / 0.15 , 1.0 )           # 0.5 si données manquantes
impact = min( valeur_marché / 100M$ , 1.0 ) × 0.7 + 0.3    # 0.5 si demande absente
```
Quadrants : effort<0.4 & impact>0.6 → **quick_win** ; effort≥0.4 & impact>0.6 → **strategic_bet** ; effort<0.4 & impact≤0.6 → **filler** ; sinon **avoid**.

**Risque / récompense :**
```
risque     = risk_pays_normalisé×0.7 + (1 − faisabilité_financement)×0.3
récompense = offre×0.4 + demande×0.4 + indice_tarif×0.2       # si tarif indispo → 0.5/0.5 (renormalisé)
```
Quadrants : risque<0.4 & récompense>0.7 → **ideal_corridor** ; <0.4 & ≤0.7 → **safe_small** ; ≥0.4 & >0.7 → **high_reward_bet** ; sinon **avoid**.

---

## 3. Scénarios

### Rapport bilatéral (ultra-fin) — `GET /reports/opportunity?mode=ultra_fine`
**Question** : *exportateur O → marché D pour le produit P : est-ce une bonne opportunité ?*
**Méthode** : assemble toutes les briques → indicateurs composites (§2) → puis :
- **Synthèse exécutive** : priority tier (QUICK_WIN / STRATEGIC_BET / HIGH_REWARD_BET / PASS) selon score + balance opportunités/risques.
- **Narratives** factuelles sourcées (offre, logistique, financement, besoin marché).
- **Benchmarking** : top producteurs, position coût (leader uniquement — sinon indispo), infrastructure, tarif.
- **Segmentation** : matrices §2.8 + factor breakdown (chaque facteur = opportunité/risque/neutre + rationale) + priority_score.

### S1 — Transformation : import intrants → production → export — `GET /reports/transformation`
**Question** : *importer une matière, transformer localement, réexporter le produit fini : est-ce viable ?*
**Méthode (3 legs, données réelles)** :
1. **Import intrant** : logistique origine→producteur + **tarif réel** à l'entrée + coût rendu de l'intrant.
2. **Production** : capacité réelle du transformateur pour le produit fini (FAO/USGS/UNIDO).
3. **Export** : rapport bilatéral complet produit fini producteur→marché (score de bout en bout).
```
valeur_ajoutée_brute = valeur_fini − valeur_intrant       # marge_% = VA / valeur_fini
```
> **PARTIELLE** : exclut les coûts de transformation (main-d'œuvre, énergie, capital, pertes) — non disponibles. Jamais présentée comme profit net.

### S2 — Production → export direct (marchés classés) — `GET /reports/direct-export`
**Question** : *un producteur du produit P : quels marchés africains viser en export ?*
**Méthode (2 étapes)** :
1. **Passe rapide** sur les ~54 marchés candidats → besoin national estimé (§S3) pour dimensionner la demande.
2. **Deep-dive** des `top_k` plus gros besoins → rapport bilatéral complet (score, coût rendu, tarif, logistique, financement).
3. **Classement** par score de bout en bout, puis par besoin.
> Le tarif est **fourni par marché** mais **hors** du score (le score = production/logistique/financement/risque).

### S3 — Besoin national (estimation transparente) — `GET /reports/national-need`
**Question** : *quel volume du produit P le pays C consomme/importe-t-il, même sans statistique ?*
**Méthode (cascade, du mesuré au modélisé)** :
```
L1 (mesuré)   besoin = Production + Importations − Exportations          # is_estimation:false
L2 (estimé)   besoin ≈ population × (production_continentale ÷ population_continentale)
              → si imports continentaux (tonnes) fournis : (production + imports) ÷ pop_continentale
L3 (estimé+)  besoin ≈ L2 × (PIB/hab_pays ÷ PIB/hab_moyen)^ε            # ε ≈ 0.4 (élasticité-revenu)
```
- Signal complémentaire : **imports observés** (USD, OEC) — opt-in car ~54 requêtes.
- `suggested_supplier` = 1er producteur continental (≠ pays) → point de départ du rapport bilatéral.
- Chaque résultat expose `estimation_level`, `method`, `inputs` (population, production, réf/hab, facteur PIB), `sources`.

### Trouver des marchés (producteur) — `GET /reports/market-seeking`
**Question** : *pour le produit P, quels pays africains l'importent (demande) et qui le produit (offre) ?*
- **Demande** : importateurs africains via OEC (dégradation gracieuse si OEC indisponible).
- **Offre** : producteurs continentaux réels (FAO/USGS/UNIDO).

---

## 4. Endpoints (récapitulatif)

| Endpoint | Scénario |
|---|---|
| `GET /reports/opportunity?mode=standard\|ultra_fine` | Rapport bilatéral |
| `GET /reports/transformation` | S1 |
| `GET /reports/direct-export` | S2 |
| `GET /reports/national-need` | S3 |
| `GET /reports/market-seeking` | Trouver des marchés |
| `GET /reports/macro/{iso3}` | Profil macro |
| `GET /reports/oec-health`, `GET /reports/health` | Diagnostics |

---

## 5. Limites connues & leviers de travail

| Sujet | État actuel | Levier |
|---|---|---|
| **market_potential** (demande OEC par produit) | Exclu du score (OEC requis) | Brancher OEC (clé) → composante activée automatiquement |
| **L3 besoin national** (PIB/hab) | Inactif tant que `wb_gdp_pc.json` absent | Lancer `etl/fetch_wb_gdp` (réseau) |
| **Réserves de change / couverture import** | Indispo tant que `wb_reserves.json` absent | Lancer `etl/fetch_wb_reserves` |
| **Coût par producteur** (benchmark) | Indispo hors leader (pas fabriqué) | Brancher un dataset de coûts de production réels |
| **Consommation apparente L1** | Nécessite import/export pays (physiques) | Brancher quantités OEC (tonnes) par pays |
| **Pondérations des scores** | Valeurs par défaut heuristiques | Calibrer sur retours métier / cas réels (surcharge déjà supportée) |
| **Élasticité-revenu ε (L3)** | 0.4 par défaut, exposée | Différencier par catégorie de produit (denrées vs discrétionnaire) |
| **Coûts de transformation (S1)** | Non disponibles → VA brute seulement | Brancher coûts main-d'œuvre/énergie par pays/secteur |
| **Tarif ZLECAf manquant** | Traité comme 0% (cible AfCFTA) | Intégrer le calendrier de démantèlement daté (taux par année) |

---

## 6. Où intervenir dans le code

- **Formules composites & scénarios** : `backend/services/report_engine.py`
- **Estimation des besoins** : `backend/services/demand_estimation_service.py`
- **Tarif / benchmarking** : `backend/services/benchmarking_service.py`
- **Segmentation (matrices, facteurs)** : `backend/services/segmentation_service.py`
- **Narratives** : `backend/services/narrative_analysis_service.py`
- **Adaptateurs** : `logistics_opportunity_adapter.py`, `finance_opportunity_adapter.py`, `macro_indicators_service.py`
- **API** : `backend/routes/reports.py`
- **UI** : `frontend/src/components/reports/OpportunityReportTab.jsx`
- **ETL** : `backend/etl/fetch_wb_gdp.py`, `backend/etl/fetch_wb_reserves.py`
- **Tests** : `backend/tests/test_report_engine.py`
</content>
