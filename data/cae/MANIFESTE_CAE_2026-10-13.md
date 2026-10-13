# Manifeste CAE — textes officiels (2026-10-13)

Règle : PDF officiels tels quels, URL d'origine, date légale, SHA-256. Ce qui n'a pas pu être obtenu est noté avec la raison — aucun taux repris d'une source secondaire.

## 1-2. TEC consolidé, gazettes et stays
| Document | Statut |
|---|---|
| TEC EAC 2022 consolidé (maj juin 2025, 577 p.) | déjà au dépôt : `backend/data/legal_refs/zlecaf_application/sources/TZA_tra_cet_eac_2022_maj_2025-06.pdf` — SHA-256 `9d894c290304a75b2a77db3d16eabc73aa172eeb3a09a0d76668e6fc95b9af9f` |
| EAC Gazette Vol. AT 1 No. 19 (30/06/2025) | `data/sources/eac/official/EAC_Vol_AT_1_No_19_2025-06-30.pdf` — SHA `a0eba597d086…` (registre `data/eac/eac_gazette_register.json`) |
| EAC Gazette Vol. AT 1 No. 26 (14/08/2025) | `data/sources/eac/official/EAC_Vol_AT_1_No_26_2025-08-14.pdf` — SHA `1ce290fca48b…` |
| EAC Gazette Vol. AT 1 No. 16 (30/06/2026) — **Legal Notice EAC/160/2026** (stays de l'exercice 2026/27, Tables I-IX) | `data/sources/eac/official/EAC_Vol_AT_1_No_16_2026-06-30.pdf` — SHA `555b8fdd7cc8…` ; texte intégral déposé : `backend/data/legal_refs/zlecaf_application/sources/EAC_gazette_AT1_16_2026-06-30.texte-extrait.txt` (SHA `f3e86de00515…`) |

Stays 2026/27 : le Legal Notice EAC/160/2026 porte les mesures approuvées par pays (Uganda, Burundi, Rwanda « to stay the application of the EAC CET … at 0 % … for one year », etc.), Tables I-IX. Extraction complète de la Table I (325 lignes) restée partielle dans le registre (15 lignes Kenya + 12 lignes TZ/UG/RW/BI) : le texte intégral est désormais déposé pour lecture. Téléchargement direct eac.int bloqué (403/404 curl) — copies issues du registre du dépôt.

## 3. Les 4 lignes TEC (TEC 2022 maj 2025-06, pages du PDF)
| Ligne | Page | Droit |
|---|---|---|
| 5302.10.00 — True hemp, raw or retted | 280 | **0 %** |
| 5811.00.00 — Quilted textile products | 302 | **25 %** |
| 9209.92.00 — Parts for musical instruments of heading 92.02 | 534 | **10 %** |
| 9209.94.00 — Parts for musical instruments of heading 92.07 | 534 | **10 %** |

## 4-6. Rwanda
| Document | URL | SHA-256 |
|---|---|---|
| **Loi n° 011/2025 du 27/05/2025 portant accise** (Official Gazette n° Special du 29/05/2025, bilingue, annexe) | https://www.rra.gov.rw/fileadmin/user_upload/Law_on_Excise_Duty_May_2025.pdf | `32e34ac1be0a8c3806f24e398b4adc9ff2fb1e9256f5c290ceb05549cefd163a` |
| Official Gazette n° Special du 14/09/2023 (version précédente des lois fiscales) | https://www.minijust.gov.rw/index.php?eID=dumpFile&f=74585&t=f&token=a47c5459b0fc8a16732080484451fbc6d7a6e134 | `ee363385ee01b98e58520bdf6cb1a48d5db79b5759cdf9cbd04215a086126787` |
| RRA — barème des taux (RATES), **non daté, antérieur à la loi 011/2025 et dépassé** (cigarettes : 30 FRW par paquet, contre 230 FRW dans la loi) — à ne pas utiliser comme taux en vigueur | https://www.rra.gov.rw/fileadmin/user_upload/announce/RATES.pdf | `7eac580b55445f2ecf31880e96b68ed7ab4f10599d9fa404785a3c9d806dc5ec` |

Loi 011/2025 : la base des **cigarettes** est « the combination of a specific base and the retail price, tax inclusive » (art. 6, paragraphe (1)(c)) — à lire pour le tabac. Non obtenus à ce stade : Finance Law 2026 (pas encore publiée en PDF trouvé sur rra.gov.rw/parlement), guide tarifaire RRA (non trouvé), textes des prélèvements (Infrastructure Development Levy, prélèvement UA 0,2 %, frais d'inspection qualité, retenue à la source) — lois de finances à identifier par numéro.

## 7-9. Tanzanie — non obtenus à ce stade
Amendements à l'Excise Act Cap. 147 (lois 8/2020, 3/2021, 5/2022, 9/2022, 3/2023, 7/2023, 6/2024), Finance Acts 2025-2026, Fourth Schedule à jour, TRA Customs Tariff Guide 2026, RDL et CPF : le site TRA et le portail des lois tanzanien n'ont pas répondu pendant la session. Le TEC 2022 maj 2025-06 (déjà au dépôt, SHA `9d894c29…`) couvre les taux TEC ; le UGA_ura_cet_eac_2022.pdf (SHA `b0fc579e…`) est la version d'origine de juin 2022 (560 p.), **sans les amendements jusqu'à juin 2025** : ne pas l'employer à la place de la consolidation (ex. 2106.90.20 : 0 % chez l'URA, 25 % dans la consolidation de juin 2025, p. 90 des deux PDF).

## 10-12. Ouganda — non obtenus à ce stade
Ordonnance TVA art. 78(2) (18 %), Excise Duty (Amendment) Acts 2024/2025/2026 + Schedule 2, prélèvements (infrastructure levy, retenue à la source, prélèvement environnemental) : à chercher sur ura.go.ug / ulii.org lors d'une session dédiée.

## 15-16. Kenya
| Document | URL | SHA-256 |
|---|---|---|
| **Finance Act 2026** (Act No. 19 of 2026) | https://new.kenyalaw.org/akn/ke/act/2026/19/eng@2026-06-26/source.pdf (copie KRA : https://www.kra.go.ke/images/publications/Finance-Act-2026.pdf) | `809ed38b9fdc94983460b99b134b26f24080eb152b20c2dedd21dc6cee9919af` (identique pour les deux copies) |

Ajustement à l'inflation des accises : le dernier avis trouvé est le KRA « Adjustment of Excise Duty Rates … by the Finance Act, 2025 » (publié en 2025) ; pas d'Order 2026 trouvé sur kenyalaw à la date de la session. Remise conditionnelle : la gazette AT1-16 porte « Stay of the application of the conditions specified in item 8 of Legal Notice No. EAC/39/2013 » (Legal Notice EAC/175/2026, p. 121 du PDF, texte intégral déposé) ; l'avis EAC/39/2013 a été obtenu ensuite (voir plus bas). Les remises que l'ancienne source applique au Kenya sont celles du Legal Notice EAC/161/2026 (Table A, même gazette) et de l'EAC/177/2025 : l'EAC/39/2013 ne sert qu'à lire les conditions de son item 8.

## 17-18. Burundi, Soudan du Sud, RDC — non obtenus à ce stade
Lois de finances, lois d'accise et redevances : serveurs officiels (Burundi finances, Soudan du Sud, RDC) non consultés faute de temps ; à faire lors d'une session dédiée. Question tarif RDC : à trancher avec un document officiel (la RDC, membre CAE depuis 2022, n'applique pas encore le TEC selon les sources publiques — à confirmer par un acte de la DGDDI).

## Complément du 13/10/2026 (session 2)

### Avis EAC/39/2013 — OBTENU (texte de référence de l'item 8, motos CKD)
`backend/data/legal_refs/zlecaf_application/sources/EAC_legal_notice_39_2013.texte-extrait.txt` — SHA-256 `3dfb7c935855de60b0421bd524ffdcf115d2a9e1910a24b66beb698944c82ea9`.
Source : Kenya Law, page « EAC Legal Notices 2013 » (https://kenyalaw.org/kl/index.php?id=4207 — page directe en 4xx aujourd'hui ; copie Wayback du 08/10/2025 utilisée). Contenu : remises approuvées par le Conseil des ministres (EACCMA 2004, s. 140 ; Duty Remission Regulations 2008) — tableau HS code / description / remise par pays (« Kenya to apply a duty rate of 10% for one year », « Uganda and Tanzania 0% for one year », etc.) ; **item 8** : CKD kits de motos (8711.10–8711.90), remise conditionnée aux fabricants produisant au moins le cadre principal ou la suspension (ou une combinaison de composants) dans la CAE. La Gazette AT1-16 du 30/06/2026 suspend certaines conditions de cet item 8 (Legal Notice EAC/175/2026, p. 121). Extrait coupé à la date de signature de l'avis (les avis EAC/40 et EAC/42/2013 qui suivaient sur la page en sont exclus) ; texte capturé d'une page web archivée, PDF de la gazette 2013 non obtenu.

### Tanzanie — Excise Act Cap. 147 + Fourth Schedule à jour — OBTENU
- `TZ_excise_cap147_consolidated_2025_oag.pdf` (108 p., ©2025 OAG, R.E. 2023 avec taux à jour) — SHA `4e874f11a067c8ebfce97797ee03ff9e470d0d9b84cd91de4f98eb033e541bac` — URL : https://a-tla.org/sites/default/files/2026-05/Tanzania%20-%20THE%20EXCISE%20%28MANAGEMENT%20AND%20TARIFF%29%20ACT%2C%20Cap.%20147.pdf
- Version R.E. 2019 (Ministère des Finances) : `TZ_excise_cap147_RE2019_mof.pdf` — SHA `045baad38a9e506a49733d41c92553e983b204dcf1ba88c09260545bdc09f9c0` — URL : https://www.mof.go.tz/uploads/documents/en-1676545092-THE%20EXCISE%20(MANAGEMENT%20AND%20TARIFF)%20ACT,%20CAP%20147%20R.E%202019.pdf
- **Tabac (Fourth Schedule, colonne « New Rate »)** : cigarettes 2402.20.10/.90 — sans filtre + tabac local >75 % : 14 936,40 TZS/mil ; avec filtre + tabac local >75 % : 35 310,00 TZS/mil ; **autres (imports) : 67 076,10 TZS par 1 000 bâtonnets** ; 2402.90.00 et 2403.11.00 : **30 % ad valorem** ; 2403.19.00 tabac à rouler — autres/imports : **33 878,88 TZS/kg**. Quantité attendue par le socle : milliers de bâtonnets (2402.20) et kilogrammes (2403).
- Assiette à l'import : non lue dans le Cap. 147 (elle relève de l'EACCMA/s.17 du texte d'origine) — reste à vérifier.
- Amendements isolés (lois 8/2020, 3/2021, 5/2022, 9/2022, 3/2023, 7/2023, 6/2024) : intégrés à la consolidation ©2025 OAG ; l'Act 9/2022 individuel est disponible (tanzlii, `tz-act-2022-9-publication-document.pdf`) — non déposé séparément. Finance Acts 2025/2026 et TRA Customs Tariff Guide 2026 : non obtenus (sites TRA/treasury non répondus).

### Ouganda — OBTENU (partiel)
- **Excise Duty (Amendment) Act 2025** (Act 14/2025) : `UGA_excise_duty_amendment_2025_act14.pdf` — SHA `ad73cefdb9e65e4229e9161ef50882b104858c9c538b0a0bd6c498ca60a9b4cd` — https://media.ulii.org/media/legislation/128248/source_file/0a168c993597403a/ug-act-2025-14-publication-document.pdf
- **Excise Duty (Amendment) Act 2026** (Act 22/2026, gazette du 28/08/2026, 4 p.) : `UGA_excise_duty_amendment_2026_act22.pdf` — SHA `1d2c8ba1cec9d7a91e9da97a6f3bc8d44baac0c4558a8a1458179c83e3ee0a8d` — https://media.ulii.org/media/legislation/131779/source_file/e433959f43fb95a4/ug-act-2026-22-publication-document.pdf
- **VAT Act Cap. 349 consolidé** : `UGA_vat_cap349_consolidated.pdf` — SHA `388c0abbebe3649419665c946458c117a298d9ed50c2a5b68d0ea9c6a26881ad` — https://a-tla.org/sites/default/files/2026-03/Uganda%20-%20Value%20Added%20Tax%20Chapter%20349.pdf. **L'art. 78 porte « Regulations and amendment of Schedules »** : pas d'ordonnance ministérielle fixant le 18 % trouvée ; le taux reste à fonder sur le texte (Premier Schedule/s. 14) — vérification restante.
- URA « Tax Amendments FY 2026/27 » : `UGA_ura_tax_amendments_fy2026-27.pdf` — SHA `1c4af2fc05a22ce7b2d2600a665d45a3c44a25fe05304bc28a7cc669287a88b5` — https://ura.go.ug/en/download/tax-amendments-fy-2026-2027/
- URA « Tax Amendments 2024/25 » : https://ura.go.ug/wp-content/uploads/2024/06/Final-Tax-amendments-2024-25.pdf (40 p.) — non déposé (résumé URA ; les actes sont déposés).
- Schedule 2 complet (principal Excise Duty Act Cap. 340 consolidé) : l'ULII 2014/2 renvoyait 4xx — reste à télécharger.
- 2024 : `bills.parliament.ug/attachments/Excise Duty (Amendment) Act, 2024.pdf` déposé en local (`UGA_excise_amendment_2024.pdf`, scanné, OCR imparfait) — non déposé dans le git ; à re-scanner si nécessaire.
- Prélèvements à l'importation (infrastructure levy, retenue à la source, prélèvement environnemental) : textes non encore identifiés individuellement — couverts par les URA Tax Amendments ci-dessus à lire.

### Reste non obtenu
Burundi, Soudan du Sud, RDC (lois de finances, accises, redevances ; question TEC vs tarif national RDC) : non traités à ce stade.

## Session 3 — 13/10/2026 (suite)

### 1. Tanzanie — valeur imposable de l'accise à l'importation : **RÉSOLU**
Cap. 147, **art. 144(1)(a)** (consolidation 2025 ; art. 141 en R.E. 2019) : « the excisable value of a scheduled article shall — (a) in respect of a scheduled article imported, be the value declared and determined in accordance with the provisions of the Customs (Management and Tariff) Act **taking into account the import duty payable** ».
**Assiette = valeur en douane (EACCMA art. 122 / Fourth Schedule OMC, soit la valeur transactionnelle CIF) + droit de douane.** Ni CIF seule, ni TVA/accise dans la base. Source : `TZ_excise_cap147_consolidated_2025_oag.pdf` (déjà déposé) et `TZ_excise_cap147_RE2019_mof.pdf`.

### 2. Ouganda — taux de TVA 18 % : **NON FONDÉ SUR UN TEXTE LU**
VAT Act Cap. 349 consolidé (déposé) : l'art. 4 « Charge of tax » ne porte pas de taux ; l'art. 78 est « Regulations and amendment of Schedules » ; le Premier Schedule liste des organisations internationales — **aucune des consolidations lues n'énonce le 18 %**. URA (document officiel « Value Added Tax 2023-24 ») applique 18 %. Reste à trouver : l'acte (loi de finances ou instrument statutaire) qui a fixé 18 % — non obtenu à cette session.

### 3. Ouganda — Schedule 2 complet : **OBTENU**
`UGA_excise_cap340_consolidated_2025-07.pdf` — Excise Duty Act (Chapter 336), legislation as at 31/12/2023 (ULII/Laws.Africa, PDF créé 17/03/2026) — SHA `986154f132dd1b7c68afc0e50e451b0caa8ce74089fcc9050b204022f80a07bd` — https://ulii.org/akn/ug/act/2014/11/eng@2023-12-31/source
Schedule 2 intégral, dont tabac : cigarettes imported **soft cap 75 000 Ushs/1 000 bâtonnets**, **hinge lid 100 000 Ushs/1 000 bâtonnets** ; cigares/cigarillos 200 % ; + les amendements 2025 (Act 14) et 2026 (Act 22) déjà déposés modifient ce Schedule.
Remarque : la consolidation est au 31/12/2023 — les modifications 2024-2026 portées par les deux Acts déposés doivent être lues par-dessus.

### 4. Tanzanie — Finance Act 2025 : **OBTENU**
`TZ_finance_act_2025_mof.pdf` (107 p.) — SHA `394e1f80909f5cf4546b48faa498e7413589ba0368c4b28636ddd3182c181695` — https://www.mof.go.tz/uploads/text-editor/files/FINANCE%20ACT%202025_1750842655.pdf

### 5. Rwanda — loi de finances 2025/2026 : **OBTENU**
`RWA_finance_law_2025-2026_official_gazette.pdf` (551 p., Official Gazette n° Special du 01/07/2025, loi n° 018/2025) — SHA `dbda79b22cef7731355ffa866249d4920d113ad01714b83822a31f29aadea777` — https://www.minecofin.gov.rw/fileadmin/user_upload/Minecofin/Publications/REPORTS/National_Budget/Annual_State_Finance_Laws/2025_to_2026_Original_Finance_Law/2025_-_2026_Original_Finance_Law_.pdf

### 6. Reste non obtenu (raison)
- **Tanzanie** : Finance Act 2026 (promulgué ? pas de PDF officiel trouvé) ; TRA Customs Tariff Guide 2026 (tra.go.tz non consultable pendant la session) ; RDL et CPF (textes : RDL sous Finance Act/Railways Act, CPF 10 % FOB plafonné — à confirmer sur les textes, sites TRA/MoF non répondus).
- **Ouganda** : ordonnance/instrument fixant le 18 % (voir 2) ; prélèvements à l'importation un par un (infrastructure levy, retenue à la source 6 % Income Tax Act, prélèvement environnemental — Schedule 2) : à documenter depuis les Acts déposés.
- **Rwanda** : guide tarifaire RRA (non trouvé) ; prélèvements à l'importation (IDL, UA 0,2 %, inspection qualité, WHT) : textes à identifier par numéro dans la LF 2025/2026 déposée ci-dessus.
- **Burundi** : LF 2025/26 ou 2026/27, loi d'accise et barème, redevances — non obtenus (sites officiels non consultables).
- **Soudan du Sud** : idem.
- **RDC** : acte DGDDI sur le tarif appliqué (TEC CAE vs tarif national), tarif national, LF et barème accises — non obtenus.

## Session 4 — 13/10/2026 (Burundi, Soudan du Sud, RDC)

| Document | Statut | URL | SHA-256 |
|---|---|---|---|
| **Burundi — Loi n° 1/12 du 24/06/2025 portant Budget Général 2025/2026** (21 p.) | **OBTENU** (site officiel Ministère des Finances) | https://finances.gov.bi/wp-content/uploads/2025/06/LOI-DE-FINANCES-2025-2026.pdf | `a3b9ab303a34950f90a0d82411bd36af62202df8d09e6de932ab3414ed25a12f` |
| **Soudan du Sud — Taxation Act 2009, Revised Edition 2021** (consolidation NRA, 112 p.) | **OBTENU** (National Revenue Authority, cms.nra.gov.ss) | https://cms.nra.gov.ss/uploads/TAXATION_ACT_2021_R_E_CONSOLIDATED_f4f9ed8876.pdf | `b245e3af4ae3c2479a7cc1931296f76f04ddde2d570b1557d601e02725a89705` |
| **RDC — Ordonnance-loi n° 011-2012 du 21/09/2012 instituant le tarif des droits et taxes à l'importation** (10 p.) | **OBTENU** mais hébergement privé (droitcongolais.info) — le texte légal est celui-ci ; J.O. RDC 18/10/2012 n° spécial p. 59. À remplacer par une copie DGDDI/leganet.cd si disponible | https://www.droitcongolais.info/files/651.09.12-Ordonannce-loi-du-21-septembre-2012_Tarif_taxes-a-l-importation.pdf | `332b2a03e188886de555e519562a1e7f9012d2e6c59b4cbb8ebee497f9d5cc55` |
| **RDC — Projet de loi de finances 2026** (20 p.) | **OBTENU** (budget.gouv.cd, Ministère du Budget) — PROJET, pas la loi promulguée | https://www.budget.gouv.cd/wp-content/uploads/budget2026/plf2026/document_num_1_projet_de_loi_de_finances_2026.pdf | `02250658e4dd1d5fb2b4c60a385252c3b25e6fb0df9fc162829ece4da4df50b5` |

### RDC — réponse sur le tarif appliqué
L'ordonnance-loi n° 011-2012 (en vigueur, modifiée et complétée à ce jour — elle est toujours citée comme texte de base par la loi n° 18-002 du 13/03/2018 portant Code des accises) institue le **tarif national des droits et taxes à l'importation** de la RDC. La RDC, membre CAE depuis 2022, **continue donc d'appliquer son tarif national** — aucun acte DGDDI trouvé annonçant l'application du TEC CAE. Codes des accises : loi n° 18-002 du 13/03/2018 (texte sur leganet.cd, hébergement à confirmer officiel).

### Reste non obtenu
- Burundi : loi d'accise et barème consolidés (OBR, obr.bi — à extraire de la rubrique Lois et règlements), redevances douanières.
- Soudan du Sud : Financial Act 2025/26 (pas de PDF officiel trouvé), barème d'accise séparé (intégré au Taxation Act).
- RDC : loi de finances 2026 promulguée (seul le PLF 2026 déposé), barème d'accises détaillé du Code 18-002 (annexe produits/taux à extraire), copie officielle DGDDI de l'OL 011-2012.

## Session 5 — 13/10/2026 (Tanzanie : FA 2026, Railways Act, IDL)

| Document | Statut | URL | SHA-256 |
|---|---|---|---|
| **Tanzanie — Finance Act 2026 (Act No. 2 of 2026)**, gazette du 30/06/2026, en vigueur 01/07/2026 (57 p.) | **OBTENU** (oagmis.oag.go.tz, base officielle OAG) | https://oagmis.oag.go.tz/portal/bills/eyJpdiI6Ii9nbFkxT0NCZG1JczZaZGt4Z1pnTnc9PSIsInZhbHVlIjoid1JRbFp5ZGt3dkI4d2R5ZWVBV3ZLQT09IiwibWFjIjoiYjNmM2JhOTdjN2MwMDQ4ZDQyZjc5MWY3YzI1YjM0OTU0YzBlYWNlNjQzMDZmYTYwM2QxYmY2YWJkMzBjM2ZhZCIsInRhZyI6IiJ9/download | `ea7ad0181a36a7d23b78670e430868903a6a55e2a9d05ed2c8e77c8bd619e9f7` |
| **Tanzanie — Railways Act, Cap. 170 R.E. 2023** (LATRA/OAG, 84 p.) | **OBTENU** | https://www.latra.go.tz/uploads/documents/sw-1768543378-RE2023-The%20Railways%20Act.pdf | `0f23e13df6964d27dccc17c20ec3fdd0363096307fce920e0cbf42ee197a0a1e` |

### Ce que la Finance Act 2026 change (pour le socle)
- **Tabac — nouveaux taux au 01/07/2026 (remplacent ceux du Cap. 147 consolidé)** : cigarettes 2402.20.10/.90 « Other » (imports) : **72 462,19 TZS par 1 000 bâtonnets** ; locales sans filtre >75 % : 16 151,31 TZS/mil ; locales avec filtre >75 % : 38 154,80 TZS/mil ; 2403.19.00 « Other/Imported » : **36 609,19 TZS/kg** ; locales >75 % : 10 388,00 TZS/kg ; 2403.91/.99 : 36 609,19 TZS/kg. Les lignes du Cap. 147 consolidé (67 076,10 / 33 878,88) sont donc **historiques** au 01/07/2026.
- **Railway Development Levy (Railways Act Cap. 170, s. 72)** : le texte R.E. 2023 porte **1,5 % de la valeur en douane** ; la FA 2023 l'avait porté à **2 %** (FB Attorneys/Clyde & Co, sources secondaires) — **l'écart reste à trancher sur un texte** (reprint à jour ou FA 2023). FA 2026 : s. 61 ajoute des exemptions (dont préservatifs HS 4014.10.00) et précise la répartition du produit.
- **Industrial Development Levy (IDL)** : prélèvement à l'importation institué par l'**Imports Control Act (Cap. 276), s. 18A + Schedule** — FA 2026 (s. 18-19) : ajoute l'**exonération des marchandises originaires des États partenaires CAE respectant les règles d'origine CAE** (avec clause de rétorsion) ; met à jour le Schedule (taux 5–10 % sur lignes ciblées : cahiers, filets de pêche, structures métalliques, portes/fenêtres aluminium, remorques).
- Custom Processing Fee : **aucune trace dans la FA 2026** ; son statut actuel reste à confirmer sur les textes TRA.

### Statut tabac Tanzanie (pour la PR socle)
Taux spécifiques en vigueur au 01/07/2026 = ceux de la **FA 2026** ci-dessus ; le socle doit demander l'unité (millier de bâtonnets / kg) et appliquer la base CIF + DD (art. 144(1)(a) Cap. 147).

## Session 6 — RDC (priorité)

| Document | Statut | URL | SHA-256 |
|---|---|---|---|
| **RDC — Loi n° 25/060 du 29/12/2025 portant loi de finances pour l'exercice 2026** (volet recettes, 250 p.) | **OBTENU** (budget.gouv.cd, Ministère du Budget) | https://budget.gouv.cd/wp-content/uploads/budget2026/lf_2026_recettes.pdf | `6b1f0c92f07d6fda86a1e5178da3b3924e5a838e4b56e0dec1e3f953de63bd24` |

**Réponse à la question du tarif (étayée par un texte officiel)** : l'exposé des motifs de la LF 2026 fonde les « droits de douane et autres droits à l'importation » sur l'**ordonnance-loi n° 011/2012 du 21/09/2012 (tarif des droits et taxes à l'importation), telle que modifiée et complétée à ce jour** (et l'OL 012/2012 à l'export). **La RDC applique donc son tarif national, pas le TEC CAE** — aucune mesure d'application du TEC n'est citée. Le tarif national applicable = OL 011-2012 + ses modifications (déposée ; hébergement privé à remplacer par une copie DGDDI).

Reste RDC : annexe/amendements de l'OL 011-2012 (révisions 2023-2025), barème d'accises détaillé du Code (loi 18-002), acte DGDDI explicite éventuel.

### RDC — compléments DGDA (session 6)
| Document | Statut | URL | SHA-256 |
|---|---|---|---|
| **RDC — Code des accises (loi n° 18-002 du 13/03/2018), copie DGDA** (22 p.) | **OBTENU** (douane.gouv.cd, DGDA officielle) | https://douane.gouv.cd/wp-content/uploads/2022/04/Code-des-accises.pdf | `380bc2889adeedb5fb643a6c1adc495ce57e678790da8b38904f71a0383f278c` |

**Tarif SH 2022 de la DGDA** : le communiqué officiel du 30/12/2021 (« Tarif des droits et taxes à l'importation et à l'exportation aligné sur la version SH 2022 », https://douane.gouv.cd/dgda/tarif-des-droits-et-taxes-a-limportation-et-a-lexportation-aligne-sur-la-version-sh-2022/) confirme que la DGDA applique depuis le 01/01/2022 un **tarif national aligné sur le SH 2022** (déployé dans SYDONIA) — aucun fichier tarifaire public au téléchargement ; l'OL 011-2012 déposée reste le fondement légal. Liste des exonérations DGDA : https://douane.gouv.cd/wp-content/uploads/2022/03/LISTE-DES-EXONERATIONS-22-03.pdf
