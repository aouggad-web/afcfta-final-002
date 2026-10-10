# Côte d'Ivoire — Codes du tarif enrichi SYDAM World (27/03/2026) : signification et bases

Source : analyse du fichier officiel « TEC CEDEAO 2022 version SYDAM World » (566 p., douanes.ci) + circulaire n°2258, décisions CEDEAO 1687/1688/1689, annexe fiscale 2026, PWIC/GUCE.
⚠️ Le fichier officiel ne publie pas de page de légende : les intitulés ci-dessous sont déduits des lignes réelles du tarif (produits et montants) et de la réglementation CI/UEMOA. Les codes marqués **[à confirmer DGD]** n'ont pas d'intitulé officiel publié — leur libellé exact est paramétré dans SYDAM World (module « tarif douanier et ses fonctions de taxation ») et détenu par la DGD (Direction des Systèmes d'Information / DSE) ou un CDA.

## 1. Codes certainement identifiés

| Code | Signification | Base de calcul | Produits (preuves dans le tarif) |
|---|---|---|---|
| **DD** | Droit de Douane (TEC CEDEAO) | **Valeur CAF** (ad valorem) | 0/5/10/20/35 % partout |
| **TVA** | Taxe sur la Valeur Ajoutée | **CAF + droits et taxes liquidés** (hors TVA) | 18 % ; 0 % sur exo ; certains taux spécifiques |
| **DUS** | Droit Unique de Sortie (export) | **Prix CAF de référence** fixé par décret avant campagne | Cacao 14,6 % · café 5 % · cajou/karité 10 F/kg · colas 10,2 F/kg · bois par cubage/espèce |
| **PCC** | Prélèvement Communautaire CEDEAO | Valeur CAF | 0,5 % (pays tiers CEDEAO) |
| **PCS** | Prélèvement Communautaire de Solidarité UEMOA | Valeur CAF | 0,8 % |
| **PUA** | Prélèvement de l'Union Africaine | Valeur CAF | 0,2 % |
| **RST** | Redevance Statistique (RS) | Valeur CAF | 1 % (y c. produits exonérés de DD) |
| **TAB** | **Taxe d'Abattage** (taxe spécifique viandes) | **Unité physique — FCFA/kg** | Viandes ch. 02 : **9** (F/kg) sur bovin/porcin/ovin/chevalin ; 0 sur certains abats |
| **TAI** | **Taxe Additionnelle à l'Importation** (spécifique viandes/volailles) | **FCFA/tonne** | Viandes congelées : 80 · porcines : 20 · volailles : **1 000** F/t |
| **TCI** | Taxe Conjoncturelle à l'Importation | **Prix de déclenchement UEMOA** (péréquation) ; ad valorem 10 % pour huiles raffinées | Sucre (PD 325 056/385 059 F/t), huiles végétales, concentré tomate |
| **TSS** | **Taxe Spéciale sur le Sucre** | **FCFA/kg** | Sucres ch. 17 : **100** F/kg (bruts, raffinés, sucreries) |
| **TBG** | **Taxe sur les Boissons Gazeuses** (taxe intérieure boissons) | Ad valorem (% CAF) ou spécifique selon ligne | Ch. 22 : eaux gazéifiées, sodas (voir tarif, ch. 22) |

## 2. Codes d'intitulé non publié **[à confirmer DGD]** — bases déduites du tarif

| Code | Lecture probable | Base observée dans le tarif | Produits porteurs |
|---|---|---|---|
| **TUB** | Taxe spécifique pétrolière (famille de la **TSU** — décision CEDEAO n°1688 : « produits pétroliers du chapitre 27 soumis à TSU ») | **FCFA par unité physique (kg ou litre)** : white spirit 146,59 · essence ordinaire 55 · gas-oil 84,03 · pétrole lampant 0 | Chap. 27 (carburants, huiles) |
| **TUE** | Taxe spécifique sur hydrocarbures (colonne voisinant TUB/TSU) | FCFA/unité : 7 320 (white spirit/essences) · 2 020 (essence ordinaire) · 22,49 (essence aviation) · 25 (gas-oil) | Chap. 27 |
| **TUF** | Taxe spécifique sur carburants pétroliers | FCFA/unité : 10 (fuel-oils, pétrole lampant) | Chap. 27 |
| **PSS** | Prélèvement sectoriel (colonne du bloc pétrole/bois) | Ad valorem ou spécifique selon ligne | Chap. 27, ch. 44 |
| **PSV** | Prélèvement ad valorem de couverture statistique/sectorielle | % CAF selon ligne | Selon lignes du tarif enrichi |
| **TSB** | Taxe spécifique (bloc boissons/tabacs) | Selon ligne (ch. 22/24) | Boissons, tabacs |
| **TCB** | Taxe spécifique produits manufacturés (bloc tabacs) | Selon ligne | Tabacs ch. 24 |
| **TCT** | Taxe sur produits du caoutchouc/caoutchouc (ch. 40) | Selon ligne | Caoutchouc chap. 40 |
| **TFS** | **Taxe Forestière** (sur bois) | Spécifique — valeur **5** observée sur bois bruts importés (FCFA/kg ou % selon paramétrage SYDAM) | Chap. 44 (4403.12, 4403.21…) |
| **TMP** | Taxe spécifique sur tabacs manufacturés (valeur **57** sur cigarettes) | FCFA/kg ou unité | Cigarettes 2402.20 |
| **TPQ** | Taxe spécifique sur tabacs (valeur **7** sur cigarettes) | FCFA/unité | Cigarettes 2402.20 |
| **TSM** | Taxe spécifique sur tabacs (valeur **6** sur cigarettes) | FCFA/unité | Cigarettes 2402.20 |

## 3. Règles de base générales (SYDAM World)
- **Taux en %** → toujours **valeur CAF** (FOB + fret + assurance), sauf TVA : CAF + droits et taxes liquidés.
- **Montant numérique** (9, 20, 80, 100, 1 000, 5, 57, 7, 6, 146,59, 7 320…) → **taxe spécifique** liquidée sur l'**unité de quantité** de la ligne tarifaire (kg, tonne, litre, hl) — l'unité exacte est paramétrée dans la fiche tarifaire SYDAM de la position (colonne « unité statistique »).
- Une même ligne peut cumuler taxe ad valorem + taxe spécifique (ex. viandes : TAB 9 F/kg **et** TAI en F/t ; pétrole : DD % **et** TSU en F/unité).

## 4. Comment obtenir l'intitulé officiel exact
1. **DGD — Direction des Systèmes d'Information (SYDAM World)** ou **Direction des Études et Statistiques Économiques** : table des codes taxation du module tarif (consultable en consultation « TAR » par tout CDA).
2. **Commissionnaire en Douane Agréé** : la liquidation SYDAM affiche pour chaque code le libellé complet et la base (avis de liquidation).
3. **GUCE** : tarif en ligne guce.gouv.ci/douanes/tariff (session requise pour l'export Excel qui, lui, contient les intitulés de colonnes).
