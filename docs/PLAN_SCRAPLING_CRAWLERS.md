# PLAN — Crawlers Scrapling des tarifs douaniers (priorité absolue)

> **Objectif** : étendre les tarifs douaniers **crawlés authentiques** de 1 pays
> (Algérie) vers les 54, avec [Scrapling](https://github.com/D4Vinci/Scrapling)
> (scraping adaptatif + furtif), **intégrés dans le Calculateur en premier**,
> l'**Algérie servant d'étalon qualité**, exécution **par workflow GitHub par pays**
> (proposition retenue).

---

## 1. Ce qui existe déjà (le plan s'appuie dessus, ne réinvente rien)

| Brique | État | Rôle dans le plan |
|---|---|---|
| `data/crawled/DZA_tariffs.json` | ✅ 17 061 sous-positions SH10, taxes DD/TVA/TCS/PRCT/DAPS, avantages fiscaux, formalités (source conformepro.dz / douane.gov.dz) | **Contrat de sortie** et **étalon qualité** |
| `authentic_tariff_service.load_crawled_position_index()` | ✅ priorité 1 du Calculateur | **Intégration automatique** : produire `{ISO3}_tariffs.json` au même schéma suffit |
| `crawlers/base_scraper.py` | ✅ ScraperConfig, ScraperResult, RateLimiter | Socle des crawlers Scrapling |
| `crawlers/validators/` | ✅ tariff / consistency / data_quality validators | Niveau 1 de la validation |
| `frontend/public/{DZA,MAR,TUN}_tarif_douanier_echantillon.csv` | ✅ valeurs pivot vérifiées (SH10 → DD/TVA/TCS/PRCT) | Niveau 2 de la validation |
| `data/csv/registry.csv` + `crawlers/all_countries_registry.py` | ✅ autorité douanière + URL par pays | Carnet d'adresses des 54 sources |
| Workflows `production_etl.yml` / `opportunites_module.yml` | ✅ patterns éprouvés (dispatch, artefacts, commit conditionnel) | Modèle du workflow de crawl |

## 2. Principes non négociables

1. **Zéro fabrication** : uniquement les taux publiés par l'autorité douanière
   officielle (ou son portail agréé). Position introuvable = absente, jamais
   estimée. Chaque fichier porte `source`, `extracted_at`, `source_quality`.
2. **Respect des sources** : throttling (RateLimiter existant), User-Agent
   identifiable, pas de contournement d'authentification ; données publiques
   officielles uniquement (les tarifs douaniers sont des actes réglementaires
   publics).
3. **Aucune donnée n'entre dans `main` sans passer le gate qualité** (§5).
4. **Le Calculateur d'abord** : le seul consommateur visé en V1 est
   `load_crawled_position_index` — pas de nouveau schéma, pas de nouvelle route.

## 3. Architecture technique

```
backend/
  crawlers/
    scrapling_engine/
      __init__.py
      runner.py            # CLI : python -m crawlers.scrapling_engine.runner --country TUN
      normalizer.py        # → schéma DZA_tariffs.json (sub_positions, taxes, stats)
      quality_gate.py      # §5 : diff vs étalon / pivots / seuils — verdict PASS/FAIL
      specs/
        dza.py             # spec par pays : URLs, navigation, sélecteurs adaptatifs,
        tun.py             #   parsing des taux, particularités (listes, PDF…)
        mar.py
        ...
  requirements-crawl.txt   # scrapling + playwright — ISOLÉ (jamais dans requirements.txt :
                           #   le backend servi reste léger, Emergent/Replit non impactés)
```

- **Pourquoi Scrapling** : sélecteurs auto-relocalisés (survit aux refontes des
  sites douaniers), mode furtif (protections type Cloudflare), rendu JS via
  Playwright quand nécessaire, parsing rapide sinon.
- **Une spec par pays** = ~100-200 lignes déclaratives (URLs de nomenclature,
  itération chapitres/positions, extraction des taux). Le moteur commun fait le
  reste (throttle, retries, normalisation, stats, rapport).
- Fichiers bruts téléchargés → `backend/engine/sources/` (gitignoré) ; seul le
  JSON normalisé et validé est committé.

## 4. Contrat de sortie (inchangé = intégration Calculateur immédiate)

```json
{
  "country": "TUN", "country_name": "Tunisie",
  "source": "douane.gov.tn (portail officiel)",
  "extracted_at": "…", "source_quality": "crawled_authentic",
  "stats": {"sections": n, "chapters": n, "sub_positions": n, "errors": 0},
  "sub_positions": [{
    "hs_code": "0101211100", "heading": "01.01", "chapter": "01",
    "name": "…", "description": "…",
    "taxes": {"DD": {"name": "Droit de Douane", "rate": 15.0, "raw": "15%"}, "TVA": {…}, …}
  }]
}
```

Dès qu'un `data/crawled/{ISO3}_tariffs.json` valide existe, le Calculateur
l'utilise en **priorité 1** pour ce pays — aucun autre branchement à écrire.

## 5. Étalon Algérie — le gate qualité (cœur de la proposition)

L'Algérie a déjà un dataset crawlé authentique complet (17 061 positions).
On s'en sert pour **prouver la chaîne Scrapling avant tout nouveau pays** :

**Étape 0 (étalonnage)** : ré-crawler l'Algérie avec le moteur Scrapling, puis
`quality_gate.py` compare au dataset existant :

| Contrôle | Seuil PASS |
|---|---|
| Couverture des positions (SH10 communs) | ≥ 99,5 % |
| Divergence sur DD / TVA / TCS / PRCT / DAPS (positions communes) | **0 divergence** non expliquée |
| Valeurs pivot (12 lignes du CSV échantillon DZA) | 12/12 exactes |
| Schéma + validators existants (`crawlers/validators/`) | 0 erreur |
| `stats.errors` | 0 |

➜ Tant que l'étalonnage DZA ne passe pas, **aucun autre pays n'est crawlé**.
Une fois PASS, le même gate (schéma + pivots + spot-checks) s'applique à chaque
pays ; pour MAR/TUN les CSV échantillons servent de pivots ; pour les autres,
10-15 positions vérifiées à la main sur le site officiel avant d'écrire la spec.

**Niveau 3 (bout en bout)** : pour chaque pays validé, 3 appels
`POST /api/calculate-tariff` (produits pilotes cacao/cajou/médicaments) avant
et après intégration — le taux affiché doit correspondre au site officiel.

## 6. Workflow GitHub par pays (proposition retenue)

`.github/workflows/tariff_crawl.yml` — `workflow_dispatch` :

| Input | Défaut | Rôle |
|---|---|---|
| `country` | `DZA` | ISO3 du pays à crawler (une exécution = un pays) |
| `mode` | `validate` | `validate` = crawl + gate, artefacts seulement ; `publish` = + commit si PASS |
| `max_positions` | vide | borne pour les runs d'essai |

Étapes du job : checkout → Python 3.11 → `pip install -r backend/requirements-crawl.txt`
+ `playwright install chromium` → `runner.py --country $C` → `quality_gate.py`
(**échoue le job si FAIL**) → artefacts (JSON + rapport de gate + échantillon
HTML brut) → si `publish` et PASS : commit de `data/crawled/{ISO3}_tariffs.json`
sur une branche `crawl/{iso3}` + **PR automatique** (revue du rapport qualité
avant merge — jamais de commit direct sur `main`).

Points d'attention hérités de nos runs : `timeout-minutes` sur l'étape crawl,
retries réseau, et vérification empirique que les sites douaniers répondent
depuis les IP GitHub (l'OEC les filtre ; si un site bloque les runners, plan B :
exécution du même runner depuis Replit/Emergent puis PR manuelle).

## 7. Vagues de déploiement (ordre = valeur / effort)

| Vague | Pays | Justification |
|---|---|---|
| **0 — Étalon** | DZA | Prouver la chaîne contre les 17 061 positions existantes |
| **1 — Maghreb** | TUN, MAR, EGY | Pivots CSV déjà présents (TUN/MAR), portails douaniers structurés, gros volumes d'échanges |
| **2 — Tarifs extérieurs communs** | CEDEAO TEC (**15 pays d'un coup**), EAC CET (7), CEMAC TEC (6) | Une source = un bloc entier ; `engine/sources/eac_cet_2022.csv` et les crawlers CEMAC amorcés existent déjà |
| **3 — Reste** | ZAF/SACU, reste COMESA, îles | Au fil de l'eau, même gate |

Après les vagues 1-2 : **~30 pays** couverts par tarifs authentiques dans le
Calculateur — et mécaniquement dans les rapports Opportunités (le moteur
tarifaire est partagé).

## 8. Risques & parades

- **Anti-bot / Cloudflare** → mode furtif Scrapling ; sinon exécution hors
  runner (Replit/Emergent) ; jamais de contournement d'espace authentifié.
- **Refonte de site** → sélecteurs adaptatifs Scrapling + gate qui échoue
  bruyamment (jamais de données silencieusement fausses).
- **Sources PDF uniquement** (certains pays) → hors périmètre V1 ; noté dans le
  registre, traité en vague 3 avec un parseur PDF dédié.
- **Dérive réglementaire** (taux modifiés en cours d'année) → le workflow est
  relançable à volonté ; `extracted_at` fait foi ; diff automatique dans la PR.
- **Charge sur les sites** → RateLimiter (ex. 1 req/s), reprise sur erreur,
  cache des pages brutes.

## 9. Étapes d'exécution

1. **S1** : squelette `scrapling_engine` (runner, normalizer, quality_gate) +
   `requirements-crawl.txt` + workflow `tariff_crawl.yml` (mode `validate`).
2. **S2** : spec DZA → étalonnage contre le dataset existant → itérer jusqu'à PASS.
3. **S3** : specs TUN + MAR (pivots CSV), runs `validate` puis `publish` → PR
   par pays → merge → vérif Calculateur bout en bout.
4. **S4** : EGY puis TEC CEDEAO (vague 2) ; mise à jour du registre + docs.

**Définition de « fait »** (par pays) : gate PASS + PR mergée + 3 calculs
pilotes conformes au site officiel + pays marqué `crawled_authentic` dans le
registre.
