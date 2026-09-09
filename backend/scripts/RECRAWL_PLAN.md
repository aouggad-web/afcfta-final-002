# Plan de Re-Crawl Tarifaire — 54 Pays AfCFTA/ZLECAf

**Date :** Mai 2026  
**Objectif :** Extraire les données tarifaires **officielles réelles** pour les 54 pays membres de la ZLECAf, incluant :
1. Positions nationales (HS8–HS12) avec dénominations exactes
2. Tous les droits et taxes avec intitulés, taux et méthodes de calcul
3. Formalités administratives avec autorité émettrice

---

## 0. Doctrine de Re-Collecte — Priorité Absolue

Ce chantier doit repartir des **bases officielles vérifiables** pour éviter les erreurs, approximations et hallucinations des jeux précédents. Les règles suivantes sont bloquantes :

1. **Re-crawler avant de compléter** : aucune ligne tarifaire africaine ne doit être complétée par interpolation, réplication de chapitre ou valeur générée.
2. **Source officielle obligatoire** : chaque fichier pays doit porter `source` et `source_url`; chaque taux doit pouvoir être relié à un portail douanier, un PDF/Excel officiel, un tarif extérieur commun officiel ou une source multilatérale reconnue.
3. **Rejet automatique des estimations** : les tags `etl_computed`, `etl_estimated`, `estimated`, `synthetic`, `generated` et `chapter_replicated` sont non servables.
4. **Transparence utilisateur** : si un pays n'a pas encore de crawler authentique branché, le pipeline doit le signaler `skipped: no_authentic_crawler` plutôt que fabriquer un tarif.
5. **Validation avant publication** : `backend/scripts/crawl_all_countries.py --validate-file ISO3` doit réussir avant qu'un fichier `data/crawled/{ISO3}_tariffs.json` soit considéré publiable.

## 1. Format Cible Canonique

Chaque position tarifaire doit produire un objet JSON conforme au format suivant (basé sur le modèle DZA validé) :

```json
{
  "hs_code":        "7610909910",
  "hs_digits":      10,
  "heading":        "76.10",
  "chapter":        "76",
  "section":        "XV",
  "name_fr":        "Autres constructions et parties en aluminium...",
  "name_en":        "Other structures and parts of aluminium...",
  "name_ar":        "...",
  "unit":           "KG",

  "taxes": {
    "DD": {
      "code":              "DD",
      "name_fr":           "Droit de Douane",
      "name_en":           "Customs Duty",
      "rate":              30.0,
      "rate_type":         "ad_valorem",
      "base":              "CIF",
      "calculation":       "CIF × 30%",
      "authority_fr":      "Direction Générale des Douanes",
      "authority_code":    "DGD",
      "legal_ref":         "Tarif des douanes 2024",
      "source_url":        "https://conformepro.dz/...",
      "raw":               "30%"
    },
    "TVA": {
      "code":              "TVA",
      "name_fr":           "Taxe sur la Valeur Ajoutée",
      "rate":              19.0,
      "rate_type":         "ad_valorem",
      "base":              "CIF + DD + DAPS",
      "calculation":       "(CIF + DD + DAPS) × 19%",
      "authority_fr":      "Direction Générale des Impôts",
      "authority_code":    "DGI",
      "legal_ref":         "Code des Impôts Art. 21"
    }
  },

  "advantages": [
    {
      "regime":     "ZLECAf",
      "tax_code":   "DD",
      "rate":       0.0,
      "condition":  "Certificat d'Origine ZLECAf requis",
      "legal_ref":  "AfCFTA Protocol on Trade in Goods"
    }
  ],

  "formalities": [
    {
      "code":           "DI",
      "document_fr":    "Déclaration d'Importation",
      "document_en":    "Import Declaration",
      "authority_fr":   "Direction Générale des Douanes (DGD)",
      "authority_code": "DGD",
      "authority_url":  "https://douane.gov.dz",
      "is_mandatory":   true,
      "applies_to":     "all"
    }
  ],

  "source":          "conformepro.dz",
  "source_url":      "https://conformepro.dz/sous-position/76.10.909910/",
  "source_quality":  "crawled_authentic",
  "crawled_at":      "2026-05-08T14:00:00Z",
  "data_quality_flag": "verified"
}
```

### Valeurs de `source_quality`

| Valeur | Signification |
|--------|--------------|
| `crawled_authentic` | Extrait directement du portail officiel de la douane nationale |
| `pdf_official` | Extrait d'un PDF officiel (CEMAC, EAC CET, SARS Schedule 1) |
| `excel_official` | Extrait d'un Excel officiel (TEC CEDEAO, GUCE CIV) |
| `etl_verified` | Taux vérifiés manuellement sur source officielle, ETL appliqué sans invention |
| `etl_estimated` | **INTERDIT / non servable** : taux estimés par interpolation ou données non publiées officiellement |

---

## 2. Audit des Sources — État Réel

### 2.1 Accessibilité testée (Mai 2026)

| Source | URL | Status | Contenu | Méthode |
|--------|-----|--------|---------|---------|
| **DZA** conformepro.dz | conformepro.dz | ✅ 200 | 17 115 positions HS10 | HTML scraping async |
| **EGY** egyptariffs.com | egyptariffs.com/tariff/{hs10} | ✅ 200 | 292 KB/position, JSON-LD | Sitemap → position-by-position |
| **MAR** douane.gov.ma/adil | /adil/info_x.asp?position={hs10} | ✅ 200 | HTML position-by-position | Session HTTP |
| **MAR** portail principal | douane.gov.ma WAF protégé | ❌ WAF | Rejeté | Contournement nécessaire |
| **KRA EAC PDF** | kra.go.ke/.../EAC-CET-2022.pdf | ✅ 200 | 4,3 MB PDF | PyMuPDF extraction |
| **CEMAC PDF** | cameroontradeportal.cm/...pdf | ✅ 200 | 2,7 MB PDF | PyMuPDF extraction |
| **ECOWAS GUCE** | guce.gouv.ci/customs/tariff/download | ⚠️ 302 | Excel redirect | Session + download |
| **SEN** douanes.sn/sydam | /sydam/tarif?code={hs} | ✅ HTML | Page WordPress (pas API) | Nécessite endpoint SYDAM direct |
| **TUN** tarifweb2025 | tarifweb2025.douane.finances.tn | ❌ DNS | Non résolu | Vérifier URL actuelle |
| **ZAF** tariff.sars.gov.za | tariff.sars.gov.za | ❌ DNS | Non résolu | PDF Schedule 1 (alternative) |
| **NGA** customs.gov.ng | customs.gov.ng | ❌ 403 | Bloqué | ECOWAS CET PDF (alternative) |
| **GHA** UNIPASS | external.unipassghana.com | ❌ 404 | Endpoint changé | Nouveau endpoint à trouver |
| **ETH** customs.erca.gov.et | customs.erca.gov.et | ⚠️ 302 | Redirects login | Session auth |
| **CIV** guce.gouv.ci | guce.gouv.ci/pages/home | ⚠️ 302 | Redirects | Session nécessaire |

---

## 3. Cartographie des 54 Pays par Groupe Tarifaire

### Groupe A — Portails Web Officiels (HTML/JSON) — Crawl Prioritaire

| Pays | Code | Source Officielle | Taxes Clés | Positions attendues |
|------|------|------------------|------------|---------------------|
| **Algérie** | DZA | conformepro.dz ✅ FAIT | DD, DAPS, PRCT, TCS, TVA | 17 115 (HS10) |
| **Maroc** | MAR | douane.gov.ma/adil | DI (DD), TPI (0.25%), TVA 20% | ~8 000 (HS10) |
| **Egypte** | EGY | egyptariffs.com | ID, VAT 14%, ST, DT | ~8 816 (HS10) |
| **Tunisie** | TUN | tarifweb2025.douane.finances.tn | DD, FODEC 1%, TCL, TVA 19% | ~7 500 (HS10) |
| **Sénégal** | SEN | douanes.sn / SYDAM | DD-TEC, RS 1%, PCS 1%, PCC 0.5%, TVA 18% | ~6 100 (HS10) |
| **Côte d'Ivoire** | CIV | guce.gouv.ci | DD-TEC, RS 1%, PCS 1%, PCC 0.5%, TVA 18% | ~6 100 (HS10) |
| **Ethiopie** | ETH | customs.erca.gov.et | CD, VAT 15%, EL excise | ~7 000 (HS11) |

### Groupe B — PDF Officiels (extraction PyMuPDF)

#### B1 — EAC Common External Tariff (Kenya, Tanzanie, Ouganda, Rwanda, Burundi, Soudan du Sud, RDC)

**Source :** `kra.go.ke` → EAC-CET-2022-VERSION-30TH-JUNE-Fn.pdf (4,3 MB, ✅ accessible)

| Pays | Code | Taxes nationales spécifiques | Positions |
|------|------|------------------------------|-----------|
| Kenya | KEN | IDF 3.5% CIF, RDL 2% CIF, VAT 16% | ~7 000 (HS8) |
| Tanzanie | TZA | VAT 18%, port levy 1% | ~7 000 (HS8) |
| Ouganda | UGA | VAT 18%, Infrastructure Levy 1.5% | ~7 000 (HS8) |
| Rwanda | RWA | VAT 18%, CIF levy 0.5% | ~7 000 (HS8) |
| Burundi | BDI | VAT 18%, OBR surcharge | ~7 000 (HS8) |
| Soudan du Sud | SSD | VAT 18% (estimé) | ~7 000 (HS8) |
| RD Congo | COD | VAT 16%, RAE redevance | ~7 000 (HS8) |

**Méthode :** Téléchargement PDF → PyMuPDF → extraction tableaux par chapitre → application taxes nationales

#### B2 — CEMAC Common External Tariff (Cameroun, Gabon, Congo-B, RCA, Tchad, Guinée Eq.)

**Source :** `cameroontradeportal.cm` PDF CEMAC (2,7 MB, ✅ accessible)

| Pays | Code | Taxes nationales | Positions |
|------|------|-----------------|-----------|
| Cameroun | CMR | TVA 19.25%, CFC 0.25%, OHADA 0.05% | ~5 200 (HS8) |
| Gabon | GAB | TVA 18%, TSPP 4% | ~5 200 (HS8) |
| Congo-Brazzaville | COG | TVA 18.9% | ~5 200 (HS8) |
| RCA | CAF | TVA 19% | ~5 200 (HS8) |
| Tchad | TCD | TVA 18% | ~5 200 (HS8) |
| Guinée Équatoriale | GNQ | TVA 15% | ~5 200 (HS8) |

**Méthode :** PDF CEMAC → extraction 5 200+ positions (scraper existant `cameroon_cemac_scraper.py`) → appliquer taxes nationales

#### B3 — SARS Schedule 1 (Afrique du Sud + SACU)

**Source :** `sars.gov.za` → Schedule-No-1-Part-1-Chapters-1-to-99.pdf

| Pays | Code | Régime | Notes |
|------|------|--------|-------|
| Afrique du Sud | ZAF | SACU CET | Tarif le plus détaillé, ~15 000 positions HS8 |
| Botswana | BWA | SACU | Même CET que ZAF |
| Namibie | NAM | SACU | Même CET + TVA 15% |
| Lesotho | LSO | SACU | Même CET + TVA 14% |
| Eswatini | SWZ | SACU | Même CET + TVA 15% |

**Note DNS :** tariff.sars.gov.za résolution DNS échoue depuis ce serveur. Utiliser l'URL directe du PDF ou le miroir officiel.

### Groupe C — ECOWAS TEC Excel (15 pays CEDEAO)

**Source :** TEC CEDEAO Règlement C/REG.16/12/21 — Excel via guce.gouv.ci ou ECOWAS site  
**Bandes DD :** 0%, 5%, 10%, 20%, 35% — identiques pour les 15 membres

| Pays | Code | Taxes nationales spécifiques | Statut |
|------|------|------------------------------|--------|
| Nigeria | NGA | CISS 1%, ETLS 0.5%, VAT 7.5% | Prioritaire |
| Ghana | GHA | GETFUND 2.5%, NHIL 2.5%, ECOWAS Levy 1%, VAT 15% | UNIPASS 404 |
| Sénégal | SEN | RS 1%, PCS 1%, PCC 0.5%, PUA 0.2%, TVA 18% | Groupe A |
| Côte d'Ivoire | CIV | RS 1%, PCS 1%, PCC 0.5%, PUA 0.2%, TVA 18% | Groupe A |
| Mali | MLI | RS 1%, PCS 1%, PC-AES 0.5% (ex-PCC), TVA 18% | AES (ex-CEDEAO) |
| Burkina Faso | BFA | RS 1%, PCS 1%, PC-AES 0.5%, TVA 18% | AES |
| Niger | NER | RS 1%, PCS 1%, PC-AES 0.5%, TVA 19% | AES |
| Bénin | BEN | RS 1%, PCS 1%, PCC 0.5%, TVA 18% | |
| Togo | TGO | RS 1%, PCS 1%, PCC 0.5%, TVA 18% | |
| Guinée | GIN | TCI 0.5%, PCC 0.5%, TVA 18% | GNF |
| Guinée-Bissau | GNB | RS 1%, PCS 1%, PCC 0.5%, TVA 18% | XOF |
| Sierra Leone | SLE | GST 15%, ECOWAS Levy | SLL |
| Liberia | LBR | GST 7%, ECOWAS Levy | USD |
| Gambie | GMB | GST 15%, ECOWAS Levy | GMD |
| Cap Vert | CPV | IVA 15% | CVE |
| Mauritanie | MRT | TVA 16%, CEDEAO (observateur) | MRU |

### Groupe D — SADC (hors SACU)

**Sources :** portails nationaux + SADC Protocol schedules

| Pays | Code | Source | Taxes clés |
|------|------|--------|-----------|
| Mozambique | MOZ | AT Mozambique | IVA 17%, CIF levy |
| Zambie | ZMB | ZRA zambia.gov.zm | VAT 16%, Customs Levy |
| Zimbabwe | ZWE | ZIMRA zimra.org.zw | VAT 15% |
| Malawi | MWI | MRA malawi | VAT 16.5% |
| Madagascar | MDG | Douanes.gov.mg | TVA 20% |
| Maurice | MUS | MRA mauritius | VAT 15% |
| Angola | AGO | AGT angola | IVA 14% |
| Tanzanie | TZA | TRA (EAC groupe B) | VAT 18% |

### Groupe E — Afrique du Nord (hors DZA, MAR, EGY, TUN)

| Pays | Code | Source | Notes |
|------|------|--------|-------|
| Libye | LBY | customs.gov.ly | Portail souvent hors ligne, données 2021 |
| Soudan | SDN | customs.gov.sd | Portail instable |

### Groupe F — Estimation ETL vérifiée (portails inaccessibles)

Pays sans portail douanier public opérationnel — taux vérifiés sur décrets/JO officiels :

| Pays | Code | Source alternative | TVA | DD base |
|------|------|--------------------|-----|---------|
| Érythrée | ERI | Décret 2022 | 5% | COMESA CET |
| Djibouti | DJI | Revenue Authority | TVA 10% | Taux spécifiques |
| Somalie | SOM | Gov.so | 5% | Faible |
| São Tomé | STP | AFAP portal | IVA 15% | CEEAC |
| Comores | COM | AGID | TVA 10% | COMESA |
| Seychelles | SYC | SRC | VAT 15% | COMESA |
| Rwanda | RWA | RRA (EAC) | Groupe B | |

---

## 4. Plan d'Exécution par Phase

### Phase 1 — Corrections Immédiates (Sans crawl, priorité critique)

**Objectif :** Corriger les données actuellement en production sans attendre les crawls.

| Action | Fichier | Impact |
|--------|---------|--------|
| P1.1 — Ajouter `data_quality_flag` dans toutes les réponses API | `authentic_tariff_service.py` | Transparence utilisateur |
| P1.2 — Corriger `dd_source` : "Estimé ETL (TEC CEDEAO)" pas "Tarif national NGA" | `{country}_tariffs.json` | Intégrité |
| P1.3 — Supprimer pseudo-sous-positions 7/8/9 chiffres non-DZA | `crawled_data_service.py` | Données fausses supprimées |
| P1.4 — Frontend : supprimer `zlecaf_tariff_rate: 0` hardcodé | `CalculatorTab.jsx` | Calcul correct |
| P1.5 — Frontend : supprimer `/postgres-tariffs` appel primaire | `CalculatorTab.jsx` | Erreurs silencieuses |
| P1.6 — Frontend : `confidence_level` basé sur `source_quality` | `CalculatorTab.jsx` | Transparence |

---

### Phase 2 — Crawl Portails Web Officiels (Groupe A)

**Durée estimée :** 3–5 jours (un pays par session, parallélisable)

#### 2.1 Maroc (MAR) — douane.gov.ma/adil

**Scraper existant :** `morocco_douane_scraper.py`  
**Endpoint valide :** `/adil/info_x.asp?position={hs10}` (✅ 200, 948B par position)  
**Structure ADIL :**
- `/adil/info_0.asp?pos={chapitre}0100` → liste des positions du chapitre
- `/adil/info_x.asp?position={hs10}` → détail taxes par position
- `/adil/info_2.asp?pos={hs10}` → taxes détaillées (DI, TPI, TVA, TIC)

**Taxes à extraire :**

| Code | Intitulé | Taux | Base calcul | Autorité |
|------|----------|------|-------------|---------|
| DI | Droit d'Importation | 0–40% | CIF | ADII |
| TPI | Taxe Parafiscale à l'Importation | 0.25% | CIF | ADII |
| TVA | Taxe sur la Valeur Ajoutée | 7%, 10%, 14%, 20% | CIF+DI+TPI | DGI Maroc |
| TIC | Taxe Intérieure de Consommation | variable | Spécifique | ADII |

**Positions attendues :** ~8 000 (HS10 national)

**Script :** `backend/crawlers/countries/morocco_douane_scraper.py` → à corriger le WAF (utiliser `/adil/info_x.asp`)

---

#### 2.2 Egypte (EGY) — egyptariffs.com

**Scraper existant :** `egypt_tariffs_scraper.py`  
**Endpoint valide :** `egyptariffs.com/tariff/{hs10}` (✅ 200, 292KB JSON-LD)  
**Méthode :** Sitemap XML → 8 816 URLs → scraping position par position

**Taxes à extraire :**

| Code | Intitulé | Taux | Base | Autorité |
|------|----------|------|------|---------|
| ID | Import Duty (رسم الواردات) | 0–60% | CIF | Egyptian Customs Authority |
| VAT | Value Added Tax (ضريبة القيمة المضافة) | 14% | CIF+ID | ETA |
| SD | Supplementary Duty | 0–25% | CIF | ETA |
| DT | Development Levy | variable | CIF | ETA |

**Positions attendues :** ~8 816 (HS10)

**Action requise :** Ajouter extraction `SD` et `DT` dans `_extract_taxes_from_properties()` + traduction AR→FR des désignations.

---

#### 2.3 Tunisie (TUN) — tarifweb2025.douane.finances.tn

**Scraper existant :** `tunisia_douane_scraper.py`  
**DNS actuel :** Non résolu depuis ce serveur. URL à vérifier : `tarifweb.douane.finances.tn`

**Taxes à extraire :**

| Code | Intitulé | Taux | Base | Autorité |
|------|----------|------|------|---------|
| DD | Droit de Douane | 0–43% | CIF | Douane TUN |
| FODEC | Fonds de Développement de la Compétitivité Industrielle | 1% | CIF | MDICI |
| TCL | Taxe au Titre des Collectivités Locales | 0.2% | CIF+DD+FODEC | Douane |
| TVA | Taxe sur la Valeur Ajoutée | 7%, 13%, 19% | CIF+DD+FODEC+TCL | DGI TUN |
| DC | Droit de Consommation | variable | Spécifique | Douane |

**Positions attendues :** ~7 500 (HS10)

---

#### 2.4 Sénégal (SEN) — douanes.sn / SYDAM

**Scraper existant :** `senegal_tariff_scraper.py` (utilise Excel GUCE CIV)  
**Endpoint SYDAM à tester :** `https://www.douanes.sn/wp-json/wp/v2/...` ou SYDAM direct

**Méthode alternative :** Télécharger le fichier Excel TEC CEDEAO depuis GUCE CIV + appliquer taxes SEN

**Taxes à extraire :**

| Code | Intitulé | Taux | Base | Autorité |
|------|----------|------|------|---------|
| DD | Droit de Douane (TEC CEDEAO) | 0%, 5%, 10%, 20%, 35% | CIF | DGDDI |
| RS | Redevance Statistique | 1% | CIF | DGDDI |
| PCS | Prélèvement Communautaire de Solidarité UEMOA | 1% | CIF | BCEAO |
| PCC | Prélèvement Communautaire CEDEAO | 0.5% | CIF | CEDEAO |
| PUA | Prélèvement Union Africaine | 0.2% | CIF | UA |
| TVA | Taxe sur la Valeur Ajoutée | 18% | CIF+DD+RS+PCS+PCC | DGI SEN |

---

#### 2.5 Côte d'Ivoire (CIV) — guce.gouv.ci

**Scraper existant :** `cotedivoire_guce_scraper.py`  
**Méthode :** Télécharger Excel TEC CEDEAO depuis GUCE CIV (session nécessaire)

**Taxes (idem SEN + spécifiques CIV) :**

| Code | Intitulé | Taux | Base |
|------|----------|------|------|
| DD | TEC CEDEAO | 0–35% | CIF |
| RS | Redevance Statistique | 1% | CIF |
| PCS | Prélèvement Communautaire UEMOA | 1% | CIF |
| PCC | Prélèvement Communautaire CEDEAO | 0.5% | CIF |
| TVA | TVA standard | 18% | CIF+DD+RS |
| TIC | Taxe Intérieure de Consommation | produits spécifiques | Valeur |

---

### Phase 3 — Extraction PDF (Groupes B)

**Durée estimée :** 2–3 jours (PDFs déjà téléchargeables)

#### 3.1 EAC CET 2022 — 7 pays

**Script :** `backend/crawlers/countries/eac_cet_scraper.py` (existant, à améliorer)  
**PDF :** `kra.go.ke` → EAC-CET-2022-VERSION-30TH-JUNE-Fn.pdf (✅ 4,3 MB)

**Plan d'extraction PyMuPDF :**
1. Télécharger PDF → `/tmp/eac_cet_2022.pdf`
2. Détecter tableaux par page (regex code HS, taux)
3. Extraire : `hs_code` (8 chiffres) | `description_en` | `dd_rate` | `unit`
4. Appliquer taxes nationales par pays (voir tableau Groupe B1)
5. Enrichir formalités depuis portails KRA, TRA, UGA

**Amélioration requise sur le scraper EAC actuel :**
- Ajouter extraction des `excise_duty` par code HS
- Ajouter formalities avec autorité par pays
- Stocker `description_en` complète (pas tronquée)

---

#### 3.2 CEMAC PDF — 6 pays

**Script :** `backend/crawlers/countries/cameroon_cemac_scraper.py` (existant, 5 200+ positions)  
**PDF :** cameroontradeportal.cm (✅ 2,7 MB)

**Bandes CEMAC :** 0% (cat.1 matières premières), 5% (cat.2 intrants), 10% (cat.3 biens intermédiaires), 25% (cat.4 biens de consommation)

**Amélioration requise :**
- Ajouter champ `category` (catégorie 1–4)
- Ajouter `legal_ref` = "TEC CEMAC — Règlement n°17/99-CEMAC-CM-02"
- Compléter taxes nationales par pays (actuellement partielles)

---

#### 3.3 SARS Schedule 1 — ZAF + SACU

**Script :** `backend/crawlers/countries/southafrica_sars_scraper.py` (existant)  
**PDF :** SARS Schedule No. 1 Part 1 Chapters 1–99 (~700 pages)

**Problème DNS :** `tariff.sars.gov.za` non résolu. Utiliser URL PDF directe :  
`https://www.sars.gov.za/wp-content/uploads/Legal/SCEA1964/Legal-LPrim-CE-Sch1P1Chpt1-to-99-Schedule-No-1-Part-1-Chapters-1-to-99.pdf`

**Format SARS :** Taux spécifiques (ZAR/kg, ZAR/l) + ad valorem %. Extraction complexe.

---

### Phase 4 — TEC CEDEAO Excel — 13 pays restants (Groupe C)

**Source :** Excel TEC CEDEAO (même nomenclature pour tous les 15 membres)  
**Script :** `backend/crawlers/countries/ecowas_member_scraper.py` (existant)

**Plan :**
1. Obtenir le fichier Excel GUCE CIV (via session ou source alternative)
2. Parser toutes les positions (~6 100 HS10)
3. Appliquer la structure fiscale spécifique de chaque pays
4. Générer `{ISO3}_tariffs.json` pour chaque pays

**Amélioration requise sur `ecowas_member_scraper.py` :**
- Ajouter `taxes[code].base` et `taxes[code].calculation` pour chaque taxe
- Ajouter `formalities` avec autorité douanière par pays
- Ajouter `advantages` ZLECAf (schéma de démantèlement TEC)
- Distinguer les pays AES (MLI, BFA, NER) : PC-AES au lieu de PCC

**Formalities par pays CEDEAO (à ajouter) :**

| Document | Autorité NGA | Autorité SEN | Autorité GHA |
|----------|-------------|-------------|-------------|
| Déclaration d'importation | Nigeria Customs Service | DGDDI Sénégal | Ghana Revenue Authority |
| Certificat d'origine | SON/NAFDAC | Chambre de Commerce | GCNET |
| Contrôle phytosanitaire | NAFDAC/NAQS | DPVC | PPRSD |
| Inspection ETLS | SON/NAFDAC | BCEAO | GRA |

---

### Phase 5 — SADC Hors SACU (Groupe D)

**Durée estimée :** 3–4 jours (portails variés, qualité variable)

| Pays | Source | Méthode | Priorité |
|------|--------|---------|---------|
| MOZ | Autoridade Tributária | Portail web | Moyenne |
| ZMB | ZRA zambia | Portail web | Moyenne |
| ZWE | ZIMRA | PDF/portail | Moyenne |
| MWI | MRA Malawi | Portail | Basse |
| MDG | Douanes Madagascar | PDF | Basse |
| MUS | MRA Mauritius | Portail ✅ | Haute |
| AGO | AGT Angola | PDF | Moyenne |

---

### Phase 6 — ETL Vérifiée pour pays sans portail (Groupe F)

Pour les pays sans portail public opérationnel, maintenir les données ETL mais :
1. Ajouter `data_quality_flag: "etl_verified"` ou `"etl_estimated"`
2. Ajouter sources de référence (`legal_ref`, `source_url` vers JO/décret)
3. Afficher avertissement dans l'UI

---

## 5. Format de Sortie des Fichiers Crawlés

### 5.1 Fichier principal : `backend/data/crawled/{ISO3}_tariffs.json`

```json
{
  "country":        "DZA",
  "country_name":   "Algérie",
  "source":         "conformepro.dz",
  "source_quality": "crawled_authentic",
  "generated_at":   "2026-05-08T14:00:00Z",
  "crawled_at":     "2026-05-08T14:00:00Z",
  "legal_ref":      "Tarif des Douanes 2024 — Ordonnance n°17-01",
  "currency":       "DZD",
  "stats": {
    "total_positions": 17115,
    "hs_digits":       10,
    "chapters_covered": 97,
    "taxes_per_position_avg": 3.8,
    "formalities_per_position_avg": 2.1
  },
  "tax_structure": {
    "DD":   {"name": "Droit de Douane", "base": "CIF", "authority": "DGD"},
    "DAPS": {"name": "Droit Additionnel Provisoire de Sauvegarde", "base": "CIF", "authority": "DGD"},
    "PRCT":{"name": "Prélèvement de Régulation du Commerce", "base": "CIF", "authority": "DGD"},
    "TVA":  {"name": "Taxe sur la Valeur Ajoutée", "base": "CIF+DD+DAPS", "authority": "DGI"},
    "TCS":  {"name": "Taxe sur le Chiffre d'Affaires Spécifique", "base": "CIF", "authority": "DGI"}
  },
  "sub_positions": [ ... ]
}
```

### 5.2 Nommage et règles

- Un fichier par pays : `{ISO3}_tariffs.json` dans `backend/data/crawled/`
- Fichiers de progression sauvegardés : `{ISO3}_progress_{chapter}.json`
- Toujours inclure `crawled_at` (horodatage réel du crawl)
- `source_quality` = `crawled_authentic` UNIQUEMENT si extrait directement du portail officiel

---

## 6. Méthodes de Calcul des Droits — Référentiel

### 6.1 Méthodes standard par région

| Région | Ordre de calcul | Exemple (CIF = 10 000 USD) |
|--------|----------------|---------------------------|
| **Algérie DZA** | CIF → +DAPS(CIF) → +DD(CIF) → +PRCT(CIF) → TVA(CIF+DAPS+DD) | DAPS=6000, DD=3000, PRCT=200, TVA base=19000 → TVA=3610 |
| **Maroc MAR** | CIF → +DI(CIF) → +TPI(CIF) → TVA(CIF+DI+TPI) | DI=17.5%, TPI=0.25%, TVA 20% sur CIF+DI |
| **Egypte EGY** | CIF → +ID(CIF) → +SD(CIF) → VAT(CIF+ID+SD) | ID=22%, VAT=14% sur CIF+ID |
| **CEDEAO (15)** | CIF → +DD(CIF) → +RS(CIF) → +PCS(CIF) → +PCC(CIF) → TVA(CIF+DD+RS) | DD=20%, RS=1%, PCS=1%, TVA=18% |
| **CEMAC (6)** | CIF → +DD(CIF) → TVA(CIF+DD) | DD=25%, TVA=19.25% sur CIF+DD |
| **EAC (7)** | CIF → +CET(CIF) → +IDF(CIF) → VAT(CIF+CET+IDF) | CET=25%, IDF=3.5%, VAT=16% |
| **SACU/ZAF** | CIF → +CD(CIF) → VAT(CIF+CD) | CD=20%, VAT=15% sur CIF+CD |
| **Tunisie TUN** | CIF → +DD(CIF) → +FODEC(CIF) → +TCL(CIF+DD) → TVA(CIF+DD+FODEC+TCL) | Cascade complexe |

### 6.2 Règle de TVA/VAT

- **Base standard :** `TVA = (CIF + tous droits + parafiscaux) × taux_TVA`
- **Exceptions :** DZA calcule TVA sur `CIF + DAPS + DD` uniquement (pas PRCT)
- **Notation dans JSON :** `"base": "CIF + DD + DAPS"` ou `"calculation": "(CIF + 6000 + 3000) × 19%"`

---

## 7. Formalités Administratives — Référentiel par Région

### 7.1 Formalités communes (tous pays)

| Code | Document | Autorité type | Obligatoire |
|------|----------|--------------|-------------|
| DI | Déclaration d'Importation | Douane nationale | ✅ |
| CO | Certificat d'Origine | Chambre de Commerce | ✅ ZLECAf |
| BL | Connaissement / Lettre de Transport | Transporteur | ✅ |
| INV | Facture commerciale | Exportateur | ✅ |
| PL | Liste de colisage | Exportateur | ✅ |

### 7.2 Formalités spécifiques par catégorie de produit

| Catégorie HS | Document supplémentaire | Autorité émettrice |
|-------------|------------------------|-------------------|
| Ch. 01–05 (animaux) | Certificat sanitaire vétérinaire | Ministère Agriculture |
| Ch. 06–14 (végétaux) | Certificat phytosanitaire | Direction Protection Végétaux |
| Ch. 15 (huiles) | Attestation de conformité | Norme national |
| Ch. 28–38 (chimie) | Autorisation produits dangereux | Ministère Industrie |
| Ch. 87 (véhicules) | Certificat de conformité technique | Ministère Transport |
| Ch. 84–85 (machines) | Déclaration de conformité CE ou équivalent | Organisme accrédité |
| Ch. 30 (médicaments) | Autorisation de mise sur le marché | Ministère Santé |

### 7.3 Format formalité dans le JSON

```json
{
  "code":           "PHYTO",
  "document_fr":    "Certificat Phytosanitaire du pays d'origine",
  "document_en":    "Phytosanitary Certificate from Country of Origin",
  "authority_fr":   "Direction de la Protection des Végétaux (DPV)",
  "authority_code": "DPV",
  "authority_url":  "https://dpv.gov.xx",
  "ministry_fr":    "Ministère de l'Agriculture et du Développement Rural",
  "is_mandatory":   true,
  "applies_to":     "chapters:06-14",
  "legal_ref":      "Convention IPPC — CIPV"
}
```

---

## 8. Scrapers à Créer / Corriger

### 8.1 Scrapers existants à corriger

| Scraper | Problème | Correction |
|---------|---------|-----------|
| `morocco_douane_scraper.py` | WAF sur URL principale | Utiliser `/adil/info_x.asp?position={hs10}` direct |
| `egypt_tariffs_scraper.py` | Extrait seulement `ID` et `VAT`, manque `SD`, `DT` | Ajouter extraction champs additionnels JSON-LD |
| `eac_cet_scraper.py` | Manque `excise_duty`, formalities, `authority` | Enrichir extraction PyMuPDF |
| `ecowas_member_scraper.py` | Manque `taxes[].base`, `taxes[].calculation`, `formalities` | Ajouter structure complète |
| `cemac_member_scraper.py` | Manque `category CEMAC`, `legal_ref` | Ajouter catégorie 1–4 CEMAC |
| `southafrica_sars_scraper.py` | DNS `tariff.sars.gov.za` échoue | Utiliser URL PDF directe |
| `senegal_tariff_scraper.py` | SYDAM endpoint inconnu | Utiliser Excel GUCE CIV + taxes SEN |
| `ghana_unipass_scraper.py` | UNIPASS 404 | Trouver nouveau endpoint GRA/ICUMS |
| `cotedivoire_guce_scraper.py` | GUCE 302 redirect | Session + GUCE Excel download |

### 8.2 Nouveaux scrapers à créer

| Pays | Scraper à créer | Source | Priorité |
|------|----------------|--------|---------|
| MUS Maurice | `mauritius_mra_scraper.py` | edbmauritius.org / mra.mu | Haute |
| MOZ Mozambique | `mozambique_at_scraper.py` | at.gov.mz | Moyenne |
| ZMB Zambie | `zambia_zra_scraper.py` | zra.org.zm | Moyenne |
| ZWE Zimbabwe | `zimbabwe_zimra_scraper.py` | zimra.org.zw | Moyenne |
| LBY Libye | `libya_customs_scraper.py` | customs.gov.ly | Basse |
| AGO Angola | `angola_agt_scraper.py` | agt.minfin.gov.ao | Basse |
| TUN Tunisie | `tunisia_tarifweb_scraper.py` | tarifweb.douane.finances.tn | Haute |

---

## 9. Calendrier d'Exécution Recommandé

```
Semaine 1 (Corrections immédiates)
├── Phase 1 : Corrections P1.1–P1.6 (transparence API + frontend)
└── Tests sources : valider endpoints MAR, EGY, EAC PDF, CEMAC PDF

Semaine 2 (Crawls prioritaires)
├── MAR : corr. scraper + full crawl ADIL (~8 000 positions)
├── EGY : corr. scraper + full crawl sitemap (~8 816 positions)
└── TUN : trouver URL tarifweb + crawl

Semaine 3 (PDF extraction)
├── EAC CET : 7 pays (1 PDF → 7 fichiers)
├── CEMAC : 6 pays (1 PDF → 6 fichiers)
└── SARS ZAF : 1 PDF → 5 SACU fichiers

Semaine 4 (ECOWAS Excel)
├── Obtenir Excel TEC CEDEAO (GUCE ou source alternative)
└── Générer 13 pays ECOWAS restants (enrichis avec formalities + calcul)

Semaine 5 (SADC + autres)
├── MUS, MOZ, ZMB, ZWE
└── Vérification qualité + ajustements
```

---

## 10. Indicateurs de Qualité Cibles

| Indicateur | Cible | Actuel |
|-----------|-------|--------|
| Positions `crawled_authentic` | ≥ 15 pays | 1 (DZA) |
| Positions `pdf_official` | ≥ 25 pays | 0 |
| Taxes avec `base` documentée | 100% | 0% |
| Taxes avec `calculation` documentée | 100% | 0% |
| Formalités avec `authority_fr` | ≥ 80% | ~30% (DZA) |
| Formalités avec `authority_url` | ≥ 50% | 0% |
| Positions HS8+ (non HS6) | ≥ 20 pays | 1 (DZA HS10) |
| `data_quality_flag` dans toutes réponses | 100% | 0% |

---

## 11. Responsabilités & Outils Techniques

### Stack technique
- **HTTP async :** `httpx` (async), `aiohttp` pour haute concurrence
- **HTML parsing :** `BeautifulSoup4`
- **PDF extraction :** `PyMuPDF (fitz)`
- **Excel parsing :** `xlrd` (XLS), `openpyxl` (XLSX)
- **Rate limiting :** `asyncio.Semaphore` + délais adaptés (1–3s)
- **Résumable :** Progress files `{ISO3}_progress_{chapter}.json`
- **Output :** `backend/data/crawled/{ISO3}_tariffs.json`

### Contraintes à respecter
- Délai minimum 1.5s entre requêtes (éviter blocage IP)
- User-Agent réaliste (Chrome/120 Linux)
- Headers `Accept-Language: fr-FR,fr;q=0.9,ar;q=0.8`
- Retry automatique ×3 avec backoff exponentiel
- Ne jamais écraser `DZA_tariffs.json` (données validées)
- Sauvegarder progression toutes les 50 positions

---

*Document généré le 8 mai 2026 — à mettre à jour après chaque phase de crawl*
