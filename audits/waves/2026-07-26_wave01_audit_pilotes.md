# Vague 01 — Audit des 6 pays pilotes (ZAF, KEN, TUN, MAR, EGY, DZA)

**Branche** : `claude/official-data-wave-01`
**Base** : `origin/main` (commit `1be67b6d`)
**Date de la vague** : 2026-07-26
**Objectif** : audit factuel des fichiers de données actuellement chargés au
runtime pour les 6 pays pilotes, identification des marqueurs de fabrication,
et cadrage des collectes à mener depuis les sources officielles primaires.

Ce document ne modifie aucune donnée. Il est le point de départ documenté et
reproductible de la vague de collecte réelle qui suivra.

---

## 1. Portée exacte de cet audit

Fichiers audités : `backend/data/crawled/{ZAF,KEN,TUN,MAR,EGY,DZA}_tariffs.json`
— ce sont les fichiers **effectivement consommés au runtime** par
`backend/services/crawled_service.py` ; ce ne sont **pas** les artefacts
`engine/output/*` (voir §4).

Aucun test n'a été exécuté dans cet audit. Aucune donnée n'a été modifiée.

---

## 2. Résultats — synthèse

| Pays | Positions | Format | Statut source primaire | Marqueur(s) fabriqué(s) |
|---|---:|---|---|---|
| ZAF | 8 589 | `positions` (schéma SARS colonnaire) | `sars.gov.za` — PDF Schedule 1 confirmé publiquement accessible, extraction ligne à ligne **non archivée dans ce dépôt** | 4 654 lignes avec `taxes[AfCFTA].rate_pct = 0.0` + `raw_value = "free"` **sans preuve par ligne** de la portée nationale ni des partenaires admis |
| KEN | 5 984 | `positions` (EAC CET 2022) | EAC CET 2022 (kra.go.ke) — CET Import Duty **réel** (distribution 0/10/25/35 %) | **5 984** lignes portent le texte générique `fiscal_advantages[name="AfCFTA Tariff Concession"]` avec description standard **appliqué à toutes** les positions sans preuve produit-par-produit |
| TUN | 17 512 | `sub_positions` (douane.gov.tn/tarifweb2025) | tarifweb 2025 — préférences **structurées par pays** (Palestine, Tunisie-partenaires) semblent authentiques (à valider ligne-à-ligne) | Aucun marqueur trivial ; à valider en profondeur (aucun `zlecaf_rate` fabriqué, aucun IMPDEC générique) |
| MAR | 13 114 | `sub_positions` (douane.gov.ma/adil) | ADII/ADIL confirmée | **6 616** codes se terminent par `00` (padding artificiel HS8 → HS10 documenté dans `upgrade_to_enhanced_v2.py:219,225`) |
| EGY | 8 746 | `sub_positions` (customs.gov.eg) | Egyptian Customs Authority | **6 320** lignes ont `zlecaf_rate: 0.0` sans lien avec le DD (qui varie de 0 % à 50 %) — offre ZLECAf fictive |
| DZA | 17 061 | `sub_positions` (conformepro.dz) | **Source secondaire** (agrégateur privé, pas la DGD ni le JO) | **4 119** lignes portent `advantages: [{tax:"D.D", rate:0.0, condition_fr:"Certificat d'Origine dans le cadre ZLECAf - Exonération DD"}]` — chaîne littérale répétée, sans preuve par produit |

---

## 3. Détail par pays

### 3.1 ZAF — Afrique du Sud

**Source déclarée** : `sars.gov.za` — SARS Customs & Excise Tariff (SACU).
**Extraction** : `2026-02-17T22:11:19`. **Positions** : 8 589.

**Ce qui est authentique** :
- Structure colonnaire SARS conservée (GENERAL, EU_UK, EFTA, SADC, MERCOSUR, AfCFTA).
- Distribution `GENERAL` réelle : 4 595 × 0 % / 843 × 10 % / 798 × 15 % / 732 × 20 % / 269 × 25 % / 264 × 22 % / 252 × 30 % / 188 × 5 % / 170 × 45 % ...
- 182 lignes avec `GENERAL = null` (renvois, taux spécifiques) — cohérent avec le PDF SARS.
- Codes HS conservés au format publié (`0101.21` etc.), unité `u` extraite, désignation en anglais préservée.

**Ce qui est problématique** :
- La colonne **AfCFTA** présente **4 654 lignes** à `rate_pct = 0.0` avec `raw_value = "free"` — cette valeur est effectivement dans le PDF SARS, mais son application dépend, ligne par ligne, du partenaire et de la règle d'origine. Le fichier **ne porte aucun champ `applicable_partners`** ni de règle d'origine par ligne, donc son ingestion telle quelle dans le calculateur produirait des exonérations pour **tous** les partenaires ZLECAf, alors que la portée réelle est encadrée par l'offre nationale ZAF et la mise en œuvre effective.
- Le PDF Schedule 1 Part 1 (mis à jour 2026-07-24) est **confirmé publiquement accessible** (`README data/sources/south_africa/`) mais **n'est pas archivé** dans le dépôt (SHA-256, extraction reproductible manquants).

**Action recommandée pour la vague** (non exécutée ici) :
1. Archiver le PDF Schedule 1 Part 1 complet (User-Agent navigateur, sans contournement) + SHA-256 + `pdfinfo`.
2. Vérifier que la colonne AfCFTA du fichier `ZAF_tariffs.json` correspond ligne-à-ligne à cette source primaire (rapport identique/divergent/absent).
3. Attacher à chaque ligne portant un taux préférentiel la portée `applicable_partners` (établie à partir de l'offre nationale ZAF et de la mise en œuvre effective, pas déduite du taux lui-même).
4. **Ne pas exposer ZAF dans `SUPPORTED_JURISDICTIONS`** tant que la vérification n'est pas terminée.

### 3.2 KEN — Kenya

**Source déclarée** : EAC Common External Tariff 2022 (kra.go.ke).
**Extraction** : `2026-02-18T10:54:33`. **Positions** : 5 984.

**Ce qui est authentique** :
- **CET Import Duty** : distribution réelle 2 234 × 0 % / 1 962 × 25 % / 1 169 × 10 % / 493 × 35 % / 19 × 50 % / 15 × 60 % / 1 × 6 %.
- **IDF** (3,5 %), **RDL** (2,0 %) et **VAT** (16 %) appliqués correctement à toutes les positions.
- **48 lignes** marquées `CET Import Duty (Sensitive Item)` avec `rate: null` — cohérent avec le régime des « sensitive items » de l'EAC.
- 65 lignes avec `Excise Duty` — présence sélective, cohérente.

**Ce qui est fabriqué** :
- **Les 5 984 positions** (100 %) portent en `fiscal_advantages` deux entrées littéralement identiques :
  ```
  {name: "EAC Intra-Community",
   description: "0% duty for goods originating from EAC member states with valid Certificate of Origin",
   conditions: "Certificate of Origin required"}
  {name: "AfCFTA Tariff Concession",
   description: "Progressive duty reduction for AfCFTA member states",
   conditions: "AfCFTA Certificate of Origin required"}
  ```
- Ces deux textes sont **génériques** et **appliqués à toutes les lignes** sans preuve produit-par-produit ni partenaire admis. C'est **exactement le pattern interdit** par la vague (« inventer une offre ZLECAf »).
- Kenya n'a **pas** déposé d'offre ZLECAf publique avec calendrier ligne-à-ligne à ce jour ; l'inscription de « AfCFTA Tariff Concession » sur chaque ligne est donc une fabrication.

**Action recommandée** :
1. **Supprimer** les 5 984 entrées `fiscal_advantages[AfCFTA Tariff Concession]` (données non sourcées).
2. Conserver l'entrée `EAC Intra-Community` **seulement** si sa portée EAC est confirmée en tant que union douanière (elle l'est — traité EAC 1999), et la déplacer vers un registre séparé « union douanière EAC ».
3. Documenter les gazettes EAC postérieures + stays of application 2025-2026 : à collecter séparément.
4. **Ne pas exposer KEN dans `SUPPORTED_JURISDICTIONS`** ZLECAf tant qu'une offre nationale déposée n'est pas archivée.

### 3.3 TUN — Tunisie

**Source déclarée** : `douane.gov.tn/tarifweb2025`. **Positions** : 17 512.

**Ce qui semble authentique** :
- Structure `preferences` **par pays** (17 506 × PALESTINE, 14 887 × KOWEIT, 14 081 × TANZANIE, 13 800 × ROYAUME UNI, 13 800 × GROUPE PAYS UNION EUROP...) — cette variabilité par pays est cohérente avec une extraction réelle depuis tarifweb.
- `taxes_import` structuré (DDDROIT avec valeur brute `"36 %"`) ; `reglementation_import` avec codes officiels tunisiens (`705 = PR CERTIFICAT SANITAIRE`).
- `import_status` / `export_status` (« Libre ✅ ») cohérent avec l'affichage douane.tn.

**À vérifier en profondeur** :
- La liste des pays dans `preferences` inclut-elle des pays ZLECAf ? La valeur `"0 %"` est-elle un taux préférentiel authentique ou une valeur par défaut ?
- La circulaire tunisienne d'application de la ZLECAf existe-t-elle publiquement ? Recherche à mener.
- La loi de finances 2026 est un référentiel fiscal, pas un tarif ligne-par-ligne — ne pas confondre.

**Action recommandée** : audit ligne-à-ligne de `preferences` pour identifier si un partenaire ZLECAf y figure vraiment, puis validation ministérielle. Aucune donnée à supprimer pour le moment (structure semble propre).

### 3.4 MAR — Maroc

**Source déclarée** : `douane.gov.ma/adil`. **Positions** : 13 114.

**Ce qui est fabriqué** :
- **6 616 codes** (50,4 % des positions) se terminent par `00` sur 10 chiffres — signature du **padding artificiel** documenté dans
  `backend/scripts/upgrade_to_enhanced_v2.py:219,225` :
  ```python
  code10 = code_clean + "00"
  ```
  Ce padding fabrique une profondeur nationale HS10 à partir de codes HS8. Les positions ADIL réelles ne sont pas systématiquement à 10 chiffres.
- `formalities` contient uniquement des étiquettes textuelles génériques (« Documents et Normes à l'Import. »), pas des codes officiels.

**Action recommandée** :
1. Retirer le padding `+"00"` — restaurer la profondeur HS8/HS10 telle que publiée par ADII.
2. Re-collecter les formalités à partir du portail ADII (codes officiels, autorités, conditions).

### 3.5 EGY — Égypte

**Source déclarée** : Egyptian Customs Authority (`customs.gov.eg/Services/Tarif`).
**Positions** : 8 746.

**Ce qui est authentique** :
- Structure `hs_code`, `name`, `name_ar` (préservation arabe) — cohérente avec une extraction du service tarifaire.
- `taxes: {DD, TVA}` avec valeurs variables par position.
- 11 `official_instructions` par ligne en arabe préservé.

**Ce qui est fabriqué** :
- **6 320 lignes** (72 %) ont `zlecaf_rate: 0.0` alors que le DD correspondant varie de 0 % à 50 %. Aucun document officiel EGY ne confirme cette exonération générale.
- 2 373 lignes ont `zlecaf_rate` non nul (10 %, 5 %, 3 %, 0,8 %...) — **plus plausibles**, à vérifier vs. l'offre EGY.
- 53 lignes ont `zlecaf_rate: null` (traitement correct : source silencieuse).

**Action recommandée** :
1. Supprimer les 6 320 `zlecaf_rate: 0.0` — les remplacer par `null` + statut `NOT_AVAILABLE` jusqu'à confirmation officielle par produit.
2. Documenter la portée exacte de l'offre EGY (partenaires admis, date d'effet, produits couverts).
3. Conserver les 2 373 valeurs non-nulles **uniquement** si elles peuvent être reliées à un texte publié par l'autorité égyptienne.

### 3.6 DZA — Algérie

**Source déclarée** : `conformepro.dz` (déclare « données douane.gov.dz »).
**Positions** : 17 061.

**Ce qui est fabriqué** :
- **La source elle-même est secondaire** — l'audit consolidé du dépôt
  (`audits/AUDIT_ET_PLAN_TECHNIQUE_AFCFTA_FINAL_002.md:107-108`) et le code
  (`engine/adapters/dza_conformepro_adapter.py:14-17`) confirment que
  `conformepro.dz` est un agrégateur privé, **pas** la DGD ni le Journal
  officiel. Statut légitime : `PARTIAL/B`.
- **4 119 lignes** portent `advantages: [{tax: "D.D", rate: 0.0, condition_fr: "Certificat d'Origine dans le cadre ZLECAf - Exonération DD"}]` — chaîne littérale répétée 4 119 fois, sans preuve par produit ni partenaire.

**Action recommandée** :
1. Conserver le fichier en `PARTIAL/B`, ne pas le promouvoir `VERIFIED`.
2. Supprimer les 4 119 `advantages[ZLECAf]` fabriqués.
3. Rechercher la circulaire n°482/DGD/SP/D.042/24 du 22 octobre 2024 comme point de vérification prioritaire.
4. Archiver toute source primaire trouvée (JO, DGD, ministère des Finances, ministère du Commerce) avec SHA-256.

---

## 4. Alerte transversale — `engine/output/*_summary.json`

L'audit consolidé (§4.3 de `audits/AUDIT_ET_PLAN_TECHNIQUE_AFCFTA_FINAL_002.md`)
signale que les 54 fichiers `engine/output/*_summary.json` ont tous
**16 567 à 16 575 enregistrements**, indépendamment de l'économie réelle
du pays — signature d'un **gabarit HS6 dupliqué** par pays.

Ces fichiers **ne sont pas** ceux consommés au runtime par le calculateur
(qui utilise `backend/data/crawled/*.json`), mais ils sont exposés côté
frontend via `frontend/public/data/DATA_STATUS.json`. **À traiter séparément.**

---

## 5. Constats de gouvernance

1. Le script `backend/scripts/upgrade_to_enhanced_v2.py` **fabrique** :
   valeur non numérique → 0.0 (ligne 85), padding `+"00"` (219, 225),
   `_DEFAULT_ADMIN = [{code:"IMPDEC"}]` par ligne (279-281, 343), unité
   `"KG"` (338), `sensitivity: "normal"` (361), `zlecaf_rate: 0.0` fabriqué
   (364). Ce script doit être mis en quarantaine avant toute nouvelle
   régénération (déjà décidé dans le plan `logical-exploring-lovelace.md`).

2. `backend/data/crawled/QUARANTINE_SYNTHETIC/` contient déjà 10 pays
   isolés (ZAF, BEN, NER, MUS, LBR, MWI, MAR, TGO, BWA, STP) — précédent
   qui **valide la méthode** : isolation plutôt que régénération.

3. `data/sources/kenya/inventory.csv` et
   `data/sources/south_africa/inventory.csv` existent déjà (index par pays
   avec institution, titre, date légale, checksum) — infrastructure
   d'archivage à réutiliser.

---

## 6. Prochaines étapes (cadrage — pas d'exécution ici)

Ordre proposé pour la collecte réelle (à mener sur cette même branche
`claude/official-data-wave-01`, un pays par commit, sans push tant que
l'utilisateur ne l'autorise pas explicitement) :

1. **KEN** : supprimer les 5 984 `fiscal_advantages[AfCFTA]` fabriqués →
   commit `data(ken): remove fabricated generic AfCFTA concessions`.
2. **DZA** : supprimer les 4 119 `advantages[ZLECAf]` fabriqués + rechercher
   circulaire 482/2024.
3. **EGY** : convertir les 6 320 `zlecaf_rate: 0.0` en `null` + `NOT_AVAILABLE`.
4. **MAR** : retirer le padding `+"00"`.
5. **ZAF** : archiver le PDF Schedule 1 Part 1 (User-Agent navigateur) avec
   SHA-256 et rapprocher ligne-à-ligne la colonne AfCFTA du fichier.
6. **TUN** : audit ligne-à-ligne des `preferences` pour identifier les
   partenaires ZLECAf réels.

**Aucun de ces pays ne doit être ajouté à `SUPPORTED_JURISDICTIONS`** avant
que la collecte complète ne soit terminée pour ce pays.

---

**Auteur automatisé** : cette vague est menée en interaction avec l'utilisateur ;
aucun push, aucun PR, aucun ajout à `SUPPORTED_JURISDICTIONS` n'est autorisé
sans confirmation explicite.
