# Côte d'Ivoire — données tarifaires, taxes, accises et frais de prestataires (14/10/2026)

Sources officielles déposées dans `data/cote-d-ivoire/docs/` (URL + SHA-256 dans `legal_sources_tarifaires_2026-10-14.json`).

## 1. Droits et taxes à l'importation — TOUTES POSITIONS (TEC CEDEAO SH 2022, 6 381 lignes)
Taux identiques pour toutes les positions (Circulaire n° 258 du 21/07/2023, c_2258.pdf) :
| Taxe | Taux | Assiette |
|---|---|---|
| Droit de douane (DD) TEC CEDEAO | 0 % (cat. 0) / 5 % (cat. matières premières) / 10 % (cat. biens intermédiaires) / 20 % (cat. biens finaux) / 35 % (cat. biens spécifiques développement) | CAF (ad valorem) |
| Redevance Statistique (RS) | 1 % | CAF |
| Prélèvement Communautaire CEDEAO (PCC) | 0,5 % | CAF |
| Prélèvement Communautaire de Solidarité UEMOA (PCS) | 0,8 % | CAF |
| Prélèvement Union Africaine (PUA) | 0,2 % | CAF |
+ TVA 18 % (droit commun) ; TAI/TCP possibles par position (Circulaire 2549, Règlement C/REG.1/09/13 — taux fixés par arrêté produit par produit ; TCP max 2 ans).
⚠ Le tableau complet par position (TEC enrichi des taxes nationales) est publié par la DGD mais téléchargement bloqué derrière une enquête (douanes.ci/node/42571) ; non déposé.

## 2. Accises et taxes spéciales — PAR PRODUIT (note DGI « Impôts et taxes en Côte d'Ivoire », art. 403-418 CGI)
| Produit | Positions SH usuelles | Taux |
|---|---|---|
| Super carburant / essences spéciales | 2710 | 85 F/litre à 15°C |
| Essence auto | 2710 | 75 F/l |
| Gasoil | 2710 | 25 F/l |
| Huiles minérales | 2710 | 25 F/l |
| DDO | 2710 | 45 F/kg |
| Fuel-oil domestique/léger/lourd | 2710 | 10 F/kg |
| Graisses consistantes | 2710 | 20 F/kg |
| Champagnes, vins AC et mousseux | 2204, 2205, 2206, 2208 | 40 % (valeur en douane + droits et taxes hors TVA) |
| Vins ordinaires | 2204 | 35 % |
| Bières et cidres | 2203, 2206 | 17 % |
| Autres boissons alcoolisées < 35° | 2208 | 40 % |
| Autres boissons alcoolisées ≥ 35° | 2208 | 45 % |
| Boissons énergétiques | 2202 | 14 % |
| Autres boissons non alcoolisées | 2201, 2202 | 14 % |
| Tabacs (cigares, cigarillos, cigarettes, tabac à fumer, vape, chicha) | 2402, 2403, 2404 | 57 % du prix de vente HT ; minimum 20 000 F/1 000 cigarettes (LF 2025 : taxe sport 7 %, taxe SIDA/tabagisme 6 % ; min UEMOA 50 %, plafond 150 %) |
| Cartouches chargées, douilles amorcées | 9306 | 12 F/cartouche |
| Marbres | 2515 | 10 % |
| Véhicules tourisme ≥ 13 CV | 8703 | 10 % (15 % pour produits de beauté et cosmétiques contenant de l'hydroquinone, positions 3304 et 2827) |

⚠ Les positions SH ci-dessus sont les positions usuelles de ces produits ; le rattachement chiffre par chiffre est dans le tarif SYDONIA/TEC enrichi (non téléchargeable). Aucun taux inventé.

## 3. Frais des prestataires (hors fiscalité)
| Prestation | Positions concernées | Frais |
|---|---|---|
| Vérification de la Conformité (VoC) — 4 prestataires mandatés (BIVAC/Bureau Veritas, Cotecna, Intertek, SGS), décret 2017-567 | Tous produits embarqués vers la CI **sauf** exclus (annexe de l'Avis : or/métaux précieux 7106-7113, pierres précieuses 7101-7105, armes 9301-9304, animaux vivants ch. 1, poissons/viandes/légumes/fruits frais ch. 2-3 et 7-8 non congelés, floriculture ch. 6, films ch. 37, journaux ch. 49, effets/véhicules usagés, colis postaux, pétrole brut/partiellement raffiné 2709, échantillons, missions diplomatiques, régimes francs, artisanat communautaire) | Route A : 0,45 % FOB ; Route B : 0,40 % FOB ; Route C : 0,30 % FOB + minima par prestataire ; à la charge de l'exportateur ; pénalité 50 % CAF + saisine si import sans certificat |
| RFCV (contrôle documentaire de la valeur, GUCE) | Tous produits dont valeur FOB ≥ 1 000 000 F CFA ; dispense ci-dessous | (montant de la redevance non publié sur la page PWIC — non consigné faute de texte officiel) |
| Produits dispensés de RFCV mais FDI obligatoire | Or, pierres précieuses, objets d'art, métaux de récupération, explosifs, armes, animaux vivants, frais/ch. 6, films, journaux, donations, diplomatiques | — |

## 4. Non obtenus (raisons)
- **TEC enrichi par position** (douanes.ci/node/42571) : téléchargement bloqué derrière l'enquête client ; aucune copie archivée (Wayback vide).
- **Guichet tarifaire GUCE** (guce.gouv.ci/customs/tariff/rules) : accès SSO obligatoire.
- **Listes TAI par position en vigueur** : arrêtés annuels non publiés en ligne (mentionnés dans la circulaire 2549).
- **Annexe fiscale 2026** : seule la LF 2025 (dgbf.ci) était accessible.
