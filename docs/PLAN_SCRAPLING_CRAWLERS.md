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

## 4. Contrat de sortie v2 — le périmètre de capture par position (4 exigences)

Le crawlé algérien capture déjà `taxes` + `advantages` + `formalities`
(17 025/17 061 positions) mais en texte semi-libre. Le contrat v2 **structure**
les 4 familles d'informations exigées, par position tarifaire nationale :

```json
{
  "country": "DZA", "source": "…", "extracted_at": "…",
  "source_quality": "crawled_authentic",
  "stats": {"sections": n, "chapters": n, "sub_positions": n, "errors": 0},

  "calculation_rules": {                      // ← (2) MÉTHODE DE CALCUL, niveau pays
    "order": ["DD", "TCS", "PRCT", "DAPS", "TVA"],
    "bases": {
      "DD":   {"basis": "CIF", "type": "ad_valorem"},
      "TVA":  {"basis": "CIF + DD + TCS + PRCT + DAPS", "type": "ad_valorem"},
      "DAPS": {"basis": "CIF", "type": "ad_valorem_ou_specifique", "note": "…"}
    },
    "source": "Code des douanes / Loi de finances (références citées)"
  },

  "regimes_registry": [                       // ← (4) RÉFÉRENTIEL DES RÉGIMES, niveau pays
    {"code": "ZLECAF",    "name": "Zone de libre-échange continentale africaine", "kind": "ALE"},
    {"code": "ZALE",      "name": "Zone arabe de libre-échange (GAFTA)",          "kind": "ALE"},
    {"code": "UE_ASSOC",  "name": "Accord d'association UE",                      "kind": "ALE"},
    {"code": "CONV_JOR",  "name": "Convention algéro-jordanienne",                "kind": "convention_bilaterale"},
    {"code": "HYDROCARB", "name": "Régime des activités hydrocarbures",           "kind": "regime_economique"},
    {"code": "ANDI_INVEST","name": "Avantages investissement (ANDI/AAPI)",        "kind": "regime_economique"}
  ],

  "sub_positions": [{
    "hs_code": "0101211100", "heading": "01.01", "chapter": "01",
    "name": "…", "description": "…",

    "taxes": {                                // ← (1) TAUX + DÉNOMINATIONS EXACTES
      "DD":  {"name": "Droit de Douane", "rate": 15.0, "raw": "15%"},
      "TVA": {"name": "Taxe sur la Valeur Ajoutée", "rate": 19.0, "raw": "19%"},
      "TCS": {"name": "Taxe de Contrôle Sanitaire", "rate": 3.0, "raw": "3%"}
    },

    "formalities": [{                         // ← (3) FORMALITÉS PAR POSITION
      "document": "Dérogation sanitaire vétérinaire",
      "issuing_authority": "Ministère de l'Agriculture",
      "raw": "Derogation sanitaire veterinaire (m. agriculture)"
    }, {
      "document": "Visa de contrôle sanitaire vétérinaire",
      "issuing_authority": "Ministère de l'Agriculture",
      "raw": "…"
    }],

    "advantages": [{                          // ← (4) AVANTAGES FISCAUX PAR POSITION
      "regime": "ZLECAF", "tax": "DD", "rate": 0.0,
      "requires": "Certificat d'origine ZLECAf",
      "condition_raw": "Certificat d'Origine dans le cadre ZLECAf - Exonération D.D"
    }, {
      "regime": "ZALE", "tax": "DD", "rate": 0.0,
      "requires": "Certificat d'origine ZALE",
      "condition_raw": "…"
    }, {
      "regime": "CONV_JOR", "tax": "DD+DAPS", "rate": 0.0,
      "condition_raw": "Exonération d.d et d.a.p dans cadre convention algéro-jordanienne"
    }]
  }]
}
```

Règles de capture :

- **(2) Méthode de calcul** : rarement publiée par position — capturée au
  **niveau pays** (`calculation_rules` : ordre d'application, assiette de
  chaque taxe, ad valorem vs spécifique) depuis le code des douanes / la loi de
  finances, avec références citées. Les exceptions par position (taux
  spécifiques, minima de perception) sont portées dans `taxes.{X}.calculation`.
- **(3) Formalités** : normalisées en `{document, issuing_authority, raw}` —
  le texte brut est TOUJOURS conservé (`raw`) ; le parseur extrait document et
  autorité (motif « libellé (autorité) » du portail algérien). Non parsable →
  `raw` seul, jamais perdu.
- **(4) Avantages fiscaux** : normalisés en `{regime, tax, rate, requires,
  condition_raw}` et rattachés au `regimes_registry` du pays — **tous les
  régimes**, pas seulement les ALE : accords d'association (UE), zone arabe
  (ZALE/GAFTA), conventions bilatérales, **régimes économiques particuliers**
  (hydrocarbures, investissement, franchises). Régime non reconnu →
  `regime: "AUTRE"` + texte brut conservé.

Rétro-compatibilité : les champs v1 (`taxes`, `advantages`, `formalities`)
restent lisibles par `load_crawled_position_index` — le Calculateur continue de
fonctionner pendant la migration ; l'affichage des formalités/avantages
structurés enrichit `RegulatoryDetailsPanel` (déjà présent dans l'UI
Calculateur). Étape ultérieure (V2 moteur) : utiliser `regimes_registry` +
`advantages` pour proposer automatiquement le **meilleur régime applicable**
dans le calcul (aujourd'hui seul le régime ZLECAf est calculé).

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
| Formalités + avantages des pivots (colonnes `Formalites_particulieres` / `Avantages_fiscaux` du CSV) | concordance texte brut 12/12 ; parsing structuré ≥ 90 % (le reste conservé en `raw`) |
| Régimes détectés sur l'ensemble (ZLECAf, ZALE, conventions, régimes économiques) | chaque régime du `regimes_registry` observé ≥ 1 fois ; 0 avantage perdu vs v1 |
| Schéma + validators existants (`crawlers/validators/`) | 0 erreur |
| `stats.errors` | 0 |

> **Découverte S1 (2026-07-04)** — le gate, testé à vide sur les données du
> dépôt, a déjà détecté que **5 des 11 pivots CSV divergent du JSON crawlé**
> (millésimes différents : DD 5↔15 %, TVA 9↔19 %, sucre, carburants — les deux
> sources citent conformepro.dz à des dates différentes). Preuve que le
> harnais fonctionne. **L'arbitrage = le crawl frais de S2** sur la source
> officielle ; les pivots CSV seront re-vérifiés et re-datés à cette occasion.

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

## 7. Tarif régional ≠ tarif pays — LES DEUX COUCHES sont obligatoires

⚠️ **Principe non négociable** (correction de cap) : un tarif extérieur commun
(TEC CEDEAO/CEMAC, CET EAC, SACU) **n'harmonise QUE le droit de douane (DD)** à
l'importation depuis hors-bloc. Il ne dit **rien** des :

- **taxes nationales** propres à chaque pays membre : TVA (taux national), droits
  d'accise / excise, prélèvements et redevances (ex. Railway Development Levy et
  Import Declaration Fee au Kenya, taxes infrastructures, prélèvements
  statistiques…) — **différents d'un pays à l'autre du même bloc** ;
- **formalités particulières** par position et par pays (documents exigibles,
  autorité qui les délivre) ;
- **régimes et avantages nationaux** (exonérations d'investissement, franchises,
  régimes hydrocarbures, listes sensibles/exclusions propres au pays).

Donc pour un pays d'un bloc, la donnée finale = **DD régional (TEC/CET) + couche
NATIONALE complète** (taxes hors DD, formalités, régimes). Un `{ISO3}_tariffs.json`
n'est **jamais** un simple copier-coller du TEC.

Conséquence sur la méthode :

1. Le **TEC/CET** sert de **socle DD** partagé (une source pour le bloc) et de
   **contrôle croisé** du DD crawlé par pays.
2. La **couche nationale** est **toujours** crawlée depuis la **source nationale**
   du pays (portail douanes national) — comme pour l'Algérie (DD + TVA + TCS +
   PRCT + DAPS + formalités + avantages, tous nationaux).
3. Le contrat v2 porte déjà tout ceci par position (`taxes` multiples,
   `formalities`, `advantages`, `calculation_rules` du pays) : **aucune évolution
   de schéma**, seulement la discipline de sourcer les deux couches.
4. Le gate qualité par pays vérifie la présence de la couche nationale : un
   fichier qui n'aurait QUE le DD (taxes = {DD} seul, 0 formalité, 0 régime)
   pour un pays connu pour en avoir → **FAIL** (règle « couche nationale
   manquante »).

## 8. Vagues de déploiement (ordre = valeur / effort)

| Vague | Pays | Socle DD | Couche nationale (obligatoire) |
|---|---|---|---|
| **0 — Étalon** | DZA | national | ✅ déjà complète (17 061 positions) |
| **1 — Maghreb** | TUN, MAR, EGY | national | crawl portail national (pivots CSV TUN/MAR) |
| **2 — Blocs : socle DD** | TEC CEDEAO (15), CET EAC (7), TEC CEMAC (6) | **1 source/bloc** | *ne suffit pas* — déclenche la vague 3 |
| **3 — Blocs : couche nationale** | chaque pays membre des blocs | hérité du TEC | crawl portail national (taxes hors DD + formalités + régimes) |
| **4 — Reste** | ZAF/SACU, reste COMESA, îles | selon bloc | même règle : DD + national |

Le TEC accélère le **socle DD** de dizaines de pays d'un coup (vague 2), mais la
**couverture réelle** d'un pays n'est atteinte qu'après sa couche nationale
(vague 3). Un pays n'est marqué `crawled_authentic` que lorsque **les deux
couches** sont présentes et passent le gate.

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
