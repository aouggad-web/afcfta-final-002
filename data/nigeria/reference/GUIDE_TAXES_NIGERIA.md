# Nigeria — Ensemble des taxes, droits de douane, accises et levies (par position tarifaire)

Date de collecte : octobre 2026. Base : **TEC CEDEAO (ECOWAS CET) 2022-2027** — nomenclature SH 2022
à 10 chiffres, édition enrichie **27/03/2026** (source : douanes.ci, version SYDAM WORLD) +
**Mesures de politique fiscale 2026 (FPM)** du Nigeria (circulaire Ministère des Finances du
01/04/2026, OCR).

## Fichiers livrés

1. **nigeria_tarif_base_cet_complet.csv** — **6 352 positions à 10 chiffres** (nomenclature CET
   complète) : code HS-10, description (FR), **droit de douane CET (bandes 0/5/10/20/35 % + cas
   particuliers 15/30/50 %)**, colonne fiabilité (taux douteux = « a_verifier », 1 ligne).
2. **nigeria_iat_2026.csv** — taxe d'ajustement à l'importation (IAT) 2026 : 72 des 192 lignes
   extraites par OCR (annexe scannée) ; PDF officiel complet dans `sources/`.
3. **nigeria_national_list_2026.csv** — liste nationale 2026 (droits réduits unilatéraux) :
   64 des 127 lignes (OCR).
4. **nigeria_prohibition_2026.csv** — liste d'interdiction à l'importation révisée 2026 (87 codes).
5. **nigeria_excise_2026.csv** — produits passibles d'accises (annexe IV FPM 2026).
6. `sources/` — TEC CEDEAO enrichi 27/03/2026, nomenclature SH 2022, circulaire FPM 2026 (PDF).

## 1. Droits de douane à l'importation (par ligne, fichier CSV)

Bandes TEC CEDEAO : 0 % (biens sociaux essentiels), 5 % (produits de première nécessité, matières
premières, biens d'équipement), 10 % (intrants/produits intermédiaires), 20 % (biens de
consommation finaux), 35 % (produits spécifiques de développement économique).
Répartition des 6 352 lignes : 5 % → 2 350 ; 20 % → 2 297 ; 10 % → 1 444 ; 35 % → 144 ; 0 % → 101 ;
autres → 16.

**Spécificités Nigeria 2026** : la liste nationale réduit unilatéralement le droit CET sur 127
lignes (ex. bovins reproducteurs 0101.21 : 5 % → 0 %) — accès réservé aux investisseurs/
manufacteurs vérifiés utilisant les produits comme intrants.

## 2. Taxes et levies à l'importation (transversales)

| Taxe / levy | Taux | Assise | Base légale |
|---|---|---|---|
| **Droit de douane CET** | 0–35 % (par ligne) | FOB | Règlement TEC CEDEAO / Customs & Excise Tariff Act |
| **Surcharge consolidée (port + CISS + autres prélèvements portuaires)** | **7 %** | FOB + droits | FPM 2023 (consolidation des levies portuaires) |
| **Levy UA/CEDEAO (CETA s.15, Finance Act 2023)** | **0,5 %** | valeur des biens éligibles importés hors Afrique | Finance Act 2023 |
| **IAT — Import Adjustment Tax** | variable, 192 lignes en 2026 | FOB + droits | FPM 2026 annexe I (réduction ~10 %/an → 0 % en 2036 ; véhicules 2000–3999 cc : 2 %, ≥4000 cc : 4 % ; VE/bus/motos et véhicules <2000 cc exemptés) |
| **Accises (excise duties)** | voir annexe IV | — | FPM 2026 : boissons non alcoolisées, boissons alcoolisées, cigarettes/tabac, plastiques à usage unique |
| **Green Tax Surcharge** | véhicules ≥ 2000 cc (barème en annexe FPM 2026) | — | FPM 2026 |
| **TVA** | **7,5 %** | FOB + droits + surcharge + autres taxes | Finance Act 2019/2020 (VAT Act) |
| Précompte importation (WHT/VAT at source) | variables | — | Finance Acts |

Ordre indicatif de calcul : FOB → fret/assurance → **CIF** → droit CET → surcharge 7 % → levy 0,5 %
→ IAT → accise → Green Tax → TVA 7,5 % sur le cumul.

## 3. Taxes à l'exportation

- **Aucun droit de douane à l'exportation** : le tarif nigérian ne comporte pas de droits à
  l'exportation (les annexes du Customs & Excise Tariff Act ne les prévoient plus).
- **Liste d'interdiction à l'exportation** (annexe VI FPM 2026, Schedule 6 CET) : bois, charbon,
  minerai non transformé, artefacts culturels, etc. — restriction quantitative, pas un droit.
- Les politiques de restriction devises (Form M, repatriation) s'appliquent indépendamment.

## 4. Restrictions à l'importation

Liste révisée 2026 (annexe III FPM) : 115 codes interdits hors-CEDEAO ; **déprohibition 2026** :
volailles vivantes, certaines viandes, huiles comestibles, produits cacao, pâtes alimentaires,
jus de fruits, bières — détaillées dans `nigeria_prohibition_2026.csv` (OCR partiel).

## 5. Réserves

- Les annexes 2026 (IAT 192 lignes, liste nationale 127 lignes, accises) proviennent d'un PDF
  **scanné** : extraction OCR partielle (codes fiables, taux à vérifier) — le PDF officiel complet
  est fourni dans `sources/nigeria_fpm_tariff_amendments_2026.pdf`.
- Le portail NCS (cet.customs.gov.ng) reste la référence de classification en ligne (protection
  Cloudflare, non interrogeable par script).
- Vérifier les circulaires ultérieures à avril 2026 auprès du Nigeria Customs Service avant toute
  opération.

## Sources

- TEC CEDEAO enrichi 27/03/2026 : douanes.ci (apps.douanes.ci/info/tec)
- Circulaire FPM 2026 + annexes : customs.gov.ng / policyregistry.org
- FPM 2023 (consolidation levies, IAT véhicules) : KPMG Nigeria / mondaq
- Analyse FAS/USDA NI2026-0010 (résumé des annexes 2026)
