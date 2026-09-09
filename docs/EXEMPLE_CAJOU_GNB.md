# Exemple déroulé — Noix de cajou de Guinée-Bissau vers l'Algérie

> **Mise à jour (2026-07-04)** : après l'enrichissement FAOSTAT (workflow
> `production_etl`), la couverture cajou est passée de **4 à 18 producteurs
> enregistrés** avec séries 2019-2024. Le rang réel de la Guinée-Bissau est
> **7ᵉ** (90 229 t en 2024, part continentale 3,5 % ; top : CIV 944 673 t,
> TZA 528 262 t, GHA 218 576 t, BEN 212 624 t…). Le caveat de couverture
> ci-dessous — écrit lors du déroulé initial — est donc **levé** ; les
> chiffres du déroulé restent l'instantané daté du 2026-07-02.

Cas réel de bout en bout : **cajou brut en coque (SH 080131)**, producteur
**GNB (Guinée-Bissau)**, marché cible **DZA (Algérie)**. Déroulé le 2026-07-02
dans un environnement **sans OEC ni datasets World Bank** (API bloquées) — les
chiffres ci-dessous montrent donc aussi comment le module dégrade proprement.
Pour la version « réseau ouvert » : workflow Actions ou Codespaces
(`docs/EXECUTER_DEPUIS_GITHUB.md`), qui active `market_potential` (OEC) et
L3/réserves (World Bank).

```bash
cd backend
python -m scripts.smoke_opportunites --hs-code 080131 --producer GNB --destination DZA
```

## 1. Couverture des données production (FAO)

`producer_supply` (S2) — **réel, sourcé FAOSTAT QCL** :

| | |
|---|---|
| Production GNB 2023 | **200 000 t** de « Cashew nuts » |
| Part continentale | **11,56 %** (total enregistré : 1 730 000 t) |
| Rang | **3ᵉ** des producteurs enregistrés |
| Top producteurs | CIV 1 100 000 t (63,6 %) · TZA 280 000 t (16,2 %) · GNB 200 000 t · MOZ 150 000 t |

⚠ **Couverture partielle assumée** : le dataset ne contient que 4 producteurs
de cajou (le champ statique `rank_africa` de la ligne GNB dit 4, le classement
recalculé sur les lignes présentes dit 3 — d'autres producteurs réels comme le
Bénin, le Nigeria ou le Burkina Faso n'ont pas de ligne cajou). Le moteur ne
classe que ce qui est enregistré, il n'invente rien. **Levier** : étendre les
lignes FAOSTAT cajou dans `data/json/production_africaine.json`.

## 2. S2 — quels marchés africains viser ? (`/reports/direct-export`)

`GET /api/reports/direct-export?hs_code=080131&producer=GNB&top_k=5`

Classement par besoin estimé (L2, proxy population) puis deep-dive par score :

| Marché | Score bout en bout | Besoin estimé (L2, borne basse) |
|---|---|---|
| EGY | 0.499 | 130 516 t |
| COD | 0.499 | 114 313 t |
| TZA | 0.499 | 76 166 t |
| NGA | 0.426 | 278 765 t |
| ETH | 0.271 | 146 719 t |

Le classement final est par **score** (NGA et ETH ont les plus gros besoins mais
un financement plus faible, et pour ETH une logistique à 0 et un tarif
indisponible).

L'Algérie (besoin ≈ 57 029 t) n'entre pas dans le top 5 par besoin — elle est
ici **imposée comme cible** (`--destination DZA`), ce que le script supporte.

## 3. S3 — besoin national algérien (`/reports/national-need`)

`GET /api/reports/national-need?hs_code=080131&country=DZA`

- **≈ 57 029 t/an**, `estimation_level: 2` (« Proxy population »),
  `is_estimation: true` — formule, intrants (population 44,7 M, disponibilité
  continentale 0,001276 t/hab) et sources exposés dans la réponse.
- **Borne basse** : la référence par habitant est calculée sur la production
  continentale seule (imports continentaux indisponibles sans OEC).
- L3 (ajustement PIB/hab) inactif ici — s'active dès que `wb_gdp_pc.json`
  existe (ETL World Bank du workflow).
- `suggested_supplier` : CIV (1ᵉʳ producteur continental) — le module propose
  honnêtement le leader, pas le pays qu'on étudie.

## 4. Rapport bilatéral ultra-fin GNB → DZA (`/reports/opportunity`)

`GET /api/reports/opportunity?hs_code=080131&origin=GNB&destination=DZA&goods_value_usd=50000&mode=ultra_fine`

Hypothèses d'expédition par défaut : FOB 50 000 $, 21,6 t / 33,5 m³ (1 TEU).

**Tarif : pas d'avantage ZLECAf pour cette paire** (fourni hors score) :

| | |
|---|---|
| Droit national DZA (080131) | **30 %** (source : DG des Douanes — Algérie) |
| Régime appliqué à GNB | **NPF 30 %** — la ZLECAf n'est pas encore activée pour la Guinée-Bissau à l'import en Algérie (réciprocité : 9 partenaires actifs seulement, circulaire DGD 482/2024) |
| Avantage | **0 point** (indice 0.0) |

C'est la même règle que le calculateur : l'Algérie n'accorde les taux ZLECAf
qu'à ses 9 partenaires actifs (ZAF, CMR, EGY, GHA, KEN, MUS, RWA, TZA, TUN).
Un partenaire actif comme l'**Égypte** obtiendrait ici 30 % → **0 %**
(liste A, calendrier standard).

**Logistique** : maritime direct **Bissau (GWOXB) → Oran (DZORN)**, 3 541 km,
fréquence hebdomadaire, fret modélisé **985 $** → coût rendu **50 985 $**.

**Score de bout en bout : 0.453** (couverture des poids : 0.75) :

| Composante | Poids | Sous-score |
|---|---|---|
| market_potential | 0.25 | **exclue** (OEC injoignable — jamais estimée) |
| supply_capacity | 0.25 | 0.462 |
| logistics_accessibility | 0.20 | 0.533 |
| financing_feasibility | 0.20 | 0.437 |
| country_risk | 0.10 | 0.300 |

**Priority tier : PASS** — lecture honnête : pas de préférence tarifaire
(NPF 30 %), score médian (financement, risque pays) et demande réelle
algérienne non mesurée (OEC injoignable ici). Le corridor GNB → DZA n'est
donc pas prioritaire aujourd'hui — les marchés du top S2 (l'Égypte en tête,
meilleur couple besoin × score) sont de meilleurs candidats pour le cajou
bissau-guinéen. Rejouer via le workflow Actions avec OEC actif ajoute
`market_potential` au score et remplace la borne basse démographique par les
imports observés.

## 5. Variantes à un paramètre près

- **Cajou décortiqué** : `--hs-code 080132` (transformation locale = S1 :
  `/reports/transformation?input_hs_code=080131&input_origin=GNB&producer=...&finished_hs_code=080132&...`).
- **Meilleur marché S2 au lieu de DZA** : omettre `--destination`.
- Appels prêts dans `requests.http` (bloc « Exemple cajou »).
