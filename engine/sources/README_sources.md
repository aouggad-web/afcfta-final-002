# Sources tarifaires — fichiers bruts

Ce répertoire accueille les fichiers sources officiels (Excel/CSV/PDF) utilisés
par les adaptateurs de `engine/adapters/`. **Les fichiers bruts ne sont pas
versionnés** (voir `.gitignore`) — seul ce README, qui trace leur origine,
l'est.

## Convention

Pour chaque fichier déposé ici, ajouter une entrée au tableau ci-dessous avec
l'URL d'origine, la date de téléchargement et le hash SHA256
(`sha256sum <fichier>`), afin que toute personne puisse re-télécharger et
vérifier la même version.

| Fichier | Source | URL | Téléchargé le | SHA256 |
|---------|--------|-----|---------------|--------|
| `civ_tec_cedeao_enrichi_27032026.md` | Douanes CIV — TEC CEDEAO 2022 enrichi des droits et taxes nationaux (SYDAM WORLD, MAJ 27/03/2026) | https://www.douanes.ci/info/tec | 2026-06-12 | `0ccc5e078c84b56d551ee604f424a317ef9ad1b2515f06faaa1f92eb5dc05b8a` |
| `eac_cet_2022_30juin.md` | EAC CET 2022 Version (30 juin) — Annexe 1 au Protocole d'Union Douanière, EAC Gazette (PDF officiel KRA converti en Markdown) | https://www.kra.go.ke/images/publications/EAC-CET-2022-VERSION-30TH-JUNE-Fn.pdf | 2026-06-12 | `c9ec3b461fbf49171ed1393019fb0a8706247c0878d641beb0dc925259599227` |
| `eac_cet_2022.csv` | Dérivé : sortie de `eac_cet_md_to_csv.py` sur le fichier ci-dessus — 5 943 lignes SH8 (Schedule 1 + Schedule 2 sensibles) | — (généré localement) | 2026-06-12 | `61c5adad2b3aaf36553c5871e768aee9c8617b429ab9d2414b3ea70446607be5` |

### Lacunes connues du fichier EAC CET (artefacts de conversion PDF→MD)

3 positions sur 5 946 ont leurs cellules description/taux vides dans le
Markdown source (perdues à la conversion, présentes dans le PDF original) :
`5302.10.00`, `6403.51.00`, `8103.91.00`. Conformément à la politique
« pas d'extrapolation », elles sont **exclues** — à compléter en relisant
le PDF officiel.

## TEC CEDEAO — préparation du fichier

1. Télécharger le TEC officiel depuis le portail TEC des douanes ivoiriennes
   (https://www.douanes.ci/info/tec — 6 381 lignes SH10, droits + taxes
   nationales) ou auprès d'une autre source officielle :
   - ECOTIS — Commission CEDEAO : https://ecotis.projects.ecowas.int
   - DGD Sénégal : https://www.douanes.sn/ndn723/
   - DGD Bénin : https://douanes.gouv.bj/tarif-exterieur-commun-tec-cedeao-2022/
2. Exporter la feuille principale en CSV (UTF-8, délimiteur `;` ou `,`).
   Colonnes minimales attendues par `cedeao_tec_adapter.py` :
   - **Code** (`Code_SH` / `HS Code` / `NTS`) — 8 ou 10 chiffres, points tolérés
   - **Désignation** (`Designation` / `Description`)
   - **Catégorie** (`Categorie` / `Category`) — bande 0-4, **ou** une colonne
     de taux (`DD` / `Duty Rate`)
   - *(optionnel)* **Unité** (`Unite` / `SU`)
3. Lancer l'adaptateur :
   ```bash
   python engine/adapters/cedeao_tec_adapter.py \
       engine/sources/cedeao_tec_2022.csv \
       engine/output \
       --version-date 2022-01-01
   ```
   → écrit un `{ISO3}_canonical.jsonl` PARTIAL/B pour chacun des 15 membres.
4. Regénérer le registre de statut :
   ```bash
   python engine/scripts/mark_synthetic.py
   cp engine/output/DATA_STATUS.json frontend/public/data/
   ```

## Égypte (EGY) — crawl brut customs.gov.eg

| Fichier | Source | URL | Crawlé le | SHA256 |
|---------|--------|-----|-----------|--------|
| `egy_raw.json` | Moslaha El Gamareg — Tarif officiel customs.gov.eg (SH10, 8 274 positions, 95 chapitres) | https://customs.gov.eg/Services/Tarif | 2026-06-13 | `ef1d5c5ef68138a4ae89d2a70318b949d694b605f97079119973ffdafcdfc933` |

### ⚠ Défaut de mapping de colonne — NON INGESTIBLE en l'état

**73,6 % des taux DD sont erronés** (6 091 / 8 274 positions) : le crawler a
capturé la colonne TVA (`ض.ق.م`) à la place de la colonne droits de douane
(`الرسم الجمركي`). Les valeurs du type `'14% (من القيمة + ر.ض.جمركية)'`
signifient **"14 % sur (CIF + droits douane)"** — c'est la formule d'assiette
de la TVA égyptienne (Loi 67/2016), pas un taux DD.

Validation croisée confirmée :
- Ch.87 véhicules : fichier = 14 %, réel = 40–135 % → **faux**
- 7213 (fil machine acier) : fichier = 14 %, réel = 2 % → **faux**
- 0101 (chevaux) : fichier = 5 %, réel = 5 % → ✅ correct (cas des purs %)

**Action requise** : re-crawler customs.gov.eg avec mapping corrigé :
`الرسم الجمركي` → `dd_rate_raw` et `ض.ق.م` → `vat_rate_raw`.

### ✅ Données formalités exploitables (instructions غ / ق)

Le fichier contient 95 447 instructions par position, réparties en 3 types :

| Préfixe | Type | Occurrences |
|---------|------|-------------|
| ر | Notes tarifaires (accords, préférences, quotas) | 65 912 |
| غ | Conditions non-tarifaires — 60 codes uniques (autorisations préalables, certifications) | 4 047 |
| ق | Restrictions/interdictions (CITES, prohibitions, règles par pays) | 25 488 |

Les codes **غ** couvrent : quarantaine vétérinaire, autorisation Agence du
Médicament Égyptienne (EDA), contrôle phytosanitaire, certification OGM,
contrôle radiologique (Japon/Fukushima), anti-dumping.
Les codes **ق** couvrent : CITES, protocoles bilatéraux (Soudan, Syrie,
URSS-ex), prohibitions absolues à l'exportation.
Les codes **ر** incluent les taux de démantèlement ZLECAf (groupes A et B).
Ces données alimenteront le champ `requirements` du modèle canonique.

## Quarantaine — fichiers non vérifiables

Le sous-répertoire `quarantine_non_verifie/` contient les fichiers refusés par
le contrôle de provenance (`json_tariffs_adapter._validate_source`) : générés
automatiquement, sans `source_document` officiel, ou aux données démontrées
erronées. **Ils ne doivent jamais être ingérés** tant qu'ils n'ont pas été
remplacés par un document officiel vérifié.

| Fichier en quarantaine | Motif de rejet |
|------------------------|----------------|
| `RWA_tariffs.json` | Généré le jour même par script ; `zlecaf_rate` = formule 10%×DD sur toutes les lignes ; erreurs factuelles (véhicules à 0 % vs CET EAC 25 %) |
| `LBR_tariffs.json` | Idem ; doublon GST/T.V.A (même impôt compté deux fois) |
| `CMR_tariffs.json` | Idem ; aucune exonération TVA modélisée |

## Sources officielles à obtenir (données réelles uniquement)

Les téléchargements directs sont bloqués depuis cet environnement (allowlist
réseau) : déposer les fichiers ici manuellement, puis compléter le tableau
des hashes.

### EAC CET 2022 (RWA, KEN, TZA, UGA, BDI, SSD, COD, SOM)
- PDF officiel 558 p. (KRA) : https://www.kra.go.ke/images/publications/EAC-CET-2022-VERSION-30TH-JUNE-Fn.pdf
- Répertoire officiel EAC : https://www.eac.int/documents/category/eac-common-external-tariff
- Repository EAC (Annex 1 au Protocole d'Union Douanière) : https://repository.eac.int/handle/11671/24409
- Version consolidée juin 2025 (EABC) : https://eabc-online.com/download/eac-common-external-tariff-version-2022-as-updated-june-2025/
- Bandes : 0 / 10 / 25 / 35 % (4ᵉ bande 35 % en vigueur depuis le 01/07/2022)

### TEC CEEAC-CEMAC (CMR, GAB, TCD, CAF, COG, GNQ)
- **Attention** : le nouveau TEC CEEAC-CEMAC (approuvé le 18/10/2024, bandes
  0–40 %) s'applique au Cameroun depuis le **1ᵉʳ janvier 2026** — l'ancien
  tarif CEMAC 2007 est obsolète pour les taux courants.
- Cameroon Trade Portal (nomenclature) : https://www.cameroontradeportal.cm/
- Douanes Gabon (tarif CEMAC) : https://douanes.ga/
- Secrétariat CEMAC : https://www.cemac.int/

### Moteur générique `raw_crawl_adapter.py` — garde-fous anti-données-génériques

Pour ingérer efficacement un maximum de pays sans réécrire un adaptateur à
chaque fois, le moteur `engine/adapters/raw_crawl_adapter.py` convertit
n'importe quel crawl douanier « plat » via un **TaxProfile** déclaratif.

**Pour ne JAMAIS reproduire l'erreur des données génériques estampillées
réelles, trois verrous durs bloquent toute donnée non traçable :**

1. **Profil** : le droit de douane (qui varie par produit) DOIT lire son taux
   dans un champ du crawl (`rate_field`), jamais via un taux fixe codé en dur.
   Toute taxe statutaire à taux fixe (TVA, surtaxe…) DOIT citer sa base légale.
2. **Crawl** : refus si `source`/`source_url` manquants, si `data_type` est
   marqué synthétique/généré/template, si le champ de droit est absent d'une
   partie des positions (interdit de combler par 0), ou s'il n'y a qu'une seule
   bande tarifaire (signature d'un remplissage par template).
3. **Réalisme** : refus si tous les droits sont à 0 % ; avertissement si moins
   de 500 positions (tarif national probablement incomplet).

Tests : `engine/tests/test_raw_crawl_guardrails.py` PROUVENT que les données
fausses sont rejetées et que les crawls réels (ETH, MUS) passent.

Ajouter un pays = déposer son crawl officiel + ajouter un `TaxProfile` dans
`PROFILES`. Aucune donnée n'est jamais inventée par le moteur.

### MAR — Maroc (Douane / ADII — portail ADIL)
- **Source** : ADII portail ADIL — https://www.douane.gov.ma/adil/
- **Nomenclature** : NTS HS10
- **Profil** : `raw_crawl_adapter.py` → PROFILES["MAR"]
- **Structure fiscale** (ordre d'application) :
  - DD (Droit d'Importation) : % CIF — du crawl (bandes 2,5/10/17,5/25/32,5/40)
  - TPI (Taxe Parafiscale Import.) : % CIF — du crawl (≈ 0,25 %)
  - TIC (Taxe Intérieure Consom.) : % CIF — du crawl si présent
  - TVA : % de (CIF + DD + TPI + TIC) — 20 % std, 7/10/14 réduits — du crawl
- **Crawl** : `backend/scripts/crawl_mar_to_raw.py`
  - ⚠ Le crawler intégré échoue sur VSCode car `crawlers/__init__.py` importe
    `motor` (MongoDB). Ce runner autonome **contourne** ce blocage (chargement
    direct du scraper), vérifie les dépendances, et écrit `mar_raw.json`.
  - Dépendances : `pip install httpx beautifulsoup4`
  - Échantillon : `python backend/scripts/crawl_mar_to_raw.py --sample`
  - Complet : `python backend/scripts/crawl_mar_to_raw.py --out engine/sources/mar_raw.json`
  - Ingestion : `python engine/adapters/raw_crawl_adapter.py MAR engine/sources/mar_raw.json engine/output/`

### TUN — Tunisie (Douane — tarifweb / douane.gov.tn)
- **Source** : DGD Tunisie — tarifweb — https://www.douane.gov.tn/tarifweb2025/
- **Nomenclature** : NDP HS11
- **Profil** : `raw_crawl_adapter.py` → PROFILES["TUN"]
- **Structure fiscale** (ordre d'application) :
  - **Côté import** :
    - DD (Droit de Douane) : % CIF — du crawl (bandes 0/10/20/30/36)
    - DC (Droit de Consommation) : % CIF — du crawl (accise)
    - FODEC (Fonds Dév. Compétitivité) : % — du crawl (≈ 1 %)
    - TCL (Taxe Collectivités Locales) : % — du crawl
    - TVA : % de (CIF + DD + DC + FODEC + TCL) — 19 % std, 7/13 réduits — du crawl
  - **Côté export** (si présent) :
    - Prélèvement à l'Export : % — du crawl (si applicable)
- **Crawl** : `backend/scripts/crawl_tun_to_raw.py` (runner autonome, contourne
  le bug `motor` de VSCode — cf. MAR)
  - Supporte **côté import ET export** (taxes_import / taxes_export du scraper)
  - `pip install httpx beautifulsoup4`
  - `python backend/scripts/crawl_tun_to_raw.py --sample`
  - `python backend/scripts/crawl_tun_to_raw.py --out engine/sources/tun_raw.json`
  - `python engine/adapters/raw_crawl_adapter.py TUN engine/sources/tun_raw.json engine/output/`

### CEMAC — Communauté Économique et Monétaire de l'Afrique Centrale
#### (CMR, GAB, TCD, CAF, COG, GNQ)
- **Source** : Secrétariat CEMAC — https://www.cemac.int/ + douanes nationales
- **TEC CEEAC** : nouveau TEC approuvé 18/10/2024, applicable depuis 2026-01-01
- **Nomenclature** : HS2022 (international)
- **Profils** : `raw_crawl_adapter.py` → PROFILES["CMR"/"GAB"/"TCD"/"CAF"/"COG"/"GNQ"]
- **Structure fiscale** :
  - **Côté import** (TEC commun à tous les 6 membres) :
    - DD (Droit de Douane) : % CIF — du crawl (bandes 0/5/10/20/30/40)
  - **Côté export** (spécifique par membre) :
    - Réduction intra-CEMAC : 0 % fixe (accord commercial CEMAC)
    - Prélèvement à l'Export : % national — du crawl (si applicable)
  - **Remarques** :
    - Toutes les mesures import/export ont une traçabilité (rate_field ou legal_reference)
    - Pas de taux fictifs ; les droits export manquants → crawl incomplet, pas un faux 0 %
    - Accords préférentiels intra-CEMAC modélisés (réduction à 0 %)
- **Crawl** : `backend/scripts/crawl_cemac_to_raw.py` (à créer)
  - Même pattern que MAR/TUN : charge `CemacDoubleScraper` directement
  - Futures sources : portails nationaux (CMR douanes, Gabon douanes, etc.)
  - Support complet des taxes import/export pour tous les 6 membres
  - `pip install httpx beautifulsoup4`
  - `python backend/scripts/crawl_cemac_to_raw.py --sample`
  - `python engine/adapters/raw_crawl_adapter.py CMR engine/sources/cemac_raw.json engine/output/`
- **Tests** : 15 cas (`engine/tests/test_cemac_profiles.py`) valident :
  - séparation import (seq 10-50) vs export (seq 60+)
  - TEC commun appliqué identiquement aux 6 membres
  - Traçabilité complète des taux (aucun inventé)

### SACU — Union douanière d'Afrique australe (ZAF, NAM, BWA, LSO, SWZ)
- **Source** : SARS — Schedule No. 1 Part 1 (Customs Tariff, General Rate), ch. 1–99
- **URL** : https://www.sars.gov.za/legal-lprim-ce-sch1p1chpt1-to-99-schedule-no-1-part-1-chapters-1-to-99/
- **Crawl** : 12 juin 2026 (PDF SARS maj 2026-05-29) — 8 592 positions, 6/8 digits, 98 chapitres
- **Profils** : `raw_crawl_adapter.py` → PROFILES["ZAF"/"NAM"/"BWA"/"LSO"/"SWZ"]
- **Output** : `engine/output/{ZAF,NAM,BWA,LSO,SWZ}_canonical.jsonl` (8 592 lignes chacun)
- **Provenance** : VERIFIED/A (lignes au droit résolu) · PARTIAL/B (droits composés non réduits)
- **Structure fiscale** :
  - D.D = **TEC SACU commun** (identique aux 5 membres — Accord SACU 2002, art. 31) :
    34 bandes de 0 à 82 % + droits spécifiques (c/kg) + composés
  - T.V.A = taux **domestique** de chaque membre (statutaire) :
    - ZAF 15 % — Value-Added Tax Act No. 89 of 1991
    - NAM 15 % — Value-Added Tax Act No. 10 of 2000
    - BWA **14 %** — Value Added Tax Act, 2001 (14 % depuis 2021)
    - LSO 15 % — Value Added Tax Act No. 9 of 2001
    - SWZ 15 % — Value Added Tax Act No. 12 of 2011
- **Traitement honnête des droits non ad valorem** (anti-faux-0 %) :
  - droit spécifique « Nc/kg » → `RateType.SPECIFIC` (montant + unité préservés), VERIFIED
  - droit composé non résolu (ex. « 20% or 5c/kg » fragmenté) → `RateType.MIXED`,
    `rate_pct=None`, ligne **PARTIAL/B** marquée « à vérifier » — jamais un faux 0 %

### ETH — Éthiopie (Ethiopian Customs Commission)
- **Source** : Ethiopian Customs Commission (ECC)
- **URL** : https://customs.erca.gov.et/trade/customs-division/tariff
- **Crawl** : 15 juin 2026 — 2 063 positions, 11 digits, 96 chapitres
- **Adaptateur** : `engine/adapters/eth_tariff_adapter.py`
- **Output** : `engine/output/ETH_canonical.jsonl`
- **Provenance** : VERIFIED / A
- **Structure fiscale** :
  - D.D (Customs Duty) : 0 / 5 / 15 / 25 / 35 % du CIF
  - ER (Excise Duty)   : 0 / 10 / 15 / 20 / 25 / 30 / 40 / 80 / 100 % du CIF
  - SR (Surtax)        : 10 % fixe de (CIF + DD + Excise) — Proclamation 312/2002
  - T.V.A              : 15 % fixe de (CIF + DD + Excise + SR) — Proc. 285/2002
  - WHR (Withholding)  : 3 % du CIF — Income Tax Proc. 979/2016

### MUS — Maurice (Mauritius Revenue Authority)
- **Source** : MRA Integrated Tariff Schedule HS2022 (as at 01 April 2026)
- **URL** : https://www.mra.mu/download/TariffInfo010426.pdf
- **Crawl** : 15 juin 2026 — 6 073 positions, 8 digits, 90 chapitres
- **Adaptateur** : `engine/adapters/mus_tariff_adapter.py`
- **Output** : `engine/output/MUS_canonical.jsonl`
- **Provenance** : VERIFIED / A
- **Structure fiscale** :
  - D.D (MFN Duty)     : 0 / 10 / 15 / 30 / 100 % du CIF
  - Excise Duty        : 0–230 % du CIF (tabac : 230 %, alcool fort : 45-50 %)
  - T.V.A              : 0 % (1 415 positions exonérées — biens essentiels)
                         ou 15 % de (CIF + DD + Excise) — Value Added Tax Act 1998
  - Taxe environnement (EPL) : non incluse dans ce dataset

### LBR (Libéria)
- Membre CEDEAO → les taux DD sont déjà couverts par le TEC CEDEAO
  (`cedeao_tec_adapter.py`). Seules les taxes nationales LRA (GST 10 %, etc.)
  restent à documenter : https://revenue.lra.gov.lr/

## Échantillon de validation

`engine/tests/fixtures/cedeao_tec_sample.csv` est un échantillon synthétique
de 6 lignes couvrant les 5 bandes du TEC — utilisé par
`engine/tests/test_cedeao_tec_adapter.py`. Ce n'est **pas** le TEC réel.
