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
| RRA — barème des taux (RATES) | https://www.rra.gov.rw/fileadmin/user_upload/announce/RATES.pdf | `7eac580b55445f2ecf31880e96b68ed7ab4f10599d9fa404785a3c9d806dc5ec` |

Loi 011/2025 : la base des **cigarettes** est « the combination of a specific base and the retail price, tax inclusive » (art. 2/3 du texte) — à lire pour le tabac. Non obtenus à ce stade : Finance Law 2026 (pas encore publiée en PDF trouvé sur rra.gov.rw/parlement), guide tarifaire RRA (non trouvé), textes des prélèvements (Infrastructure Development Levy, prélèvement UA 0,2 %, frais d'inspection qualité, retenue à la source) — lois de finances à identifier par numéro.

## 7-9. Tanzanie — non obtenus à ce stade
Amendements à l'Excise Act Cap. 147 (lois 8/2020, 3/2021, 5/2022, 9/2022, 3/2023, 7/2023, 6/2024), Finance Acts 2025-2026, Fourth Schedule à jour, TRA Customs Tariff Guide 2026, RDL et CPF : le site TRA et le portail des lois tanzanien n'ont pas répondu pendant la session. Le TEC 2022 maj 2025-06 (déjà au dépôt, SHA `9d894c29…`) couvre les taux TEC ; le UGA_ura_cet_eac_2022.pdf (SHA `b0fc579e…`) est le même TEC côté URA.

## 10-12. Ouganda — non obtenus à ce stade
Ordonnance TVA art. 78(2) (18 %), Excise Duty (Amendment) Acts 2024/2025/2026 + Schedule 2, prélèvements (infrastructure levy, retenue à la source, prélèvement environnemental) : à chercher sur ura.go.ug / ulii.org lors d'une session dédiée.

## 15-16. Kenya
| Document | URL | SHA-256 |
|---|---|---|
| **Finance Act 2026** (Act No. 19 of 2026) | https://new.kenyalaw.org/akn/ke/act/2026/19/eng@2026-06-26/source.pdf (copie KRA : https://www.kra.go.ke/images/publications/Finance-Act-2026.pdf) | `809ed38b9fdc94983460b99b134b26f24080eb152b20c2dedd21dc6cee9919af` (identique pour les deux copies) |

Ajustement à l'inflation des accises : le dernier avis trouvé est le KRA « Adjustment of Excise Duty Rates … by the Finance Act, 2025 » (publié en 2025) ; pas d'Order 2026 trouvé sur kenyalaw à la date de la session. Remise conditionnelle : la gazette AT1-16 porte « Stay of the application of the conditions specified in item 8 of Legal Notice No. EAC/39/2013 » (p. 122 du PDF, texte intégral déposé) — c'est le cadre de remise conditionnelle visé ; l'avis EAC/39/2013 lui-même reste à obtenir.

## 17-18. Burundi, Soudan du Sud, RDC — non obtenus à ce stade
Lois de finances, lois d'accise et redevances : serveurs officiels (Burundi finances, Soudan du Sud, RDC) non consultés faute de temps ; à faire lors d'une session dédiée. Question tarif RDC : à trancher avec un document officiel (la RDC, membre CAE depuis 2022, n'applique pas encore le TEC selon les sources publiques — à confirmer par un acte de la DGDDI).
