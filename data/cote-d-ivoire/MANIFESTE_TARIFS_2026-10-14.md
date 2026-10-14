# Côte d'Ivoire — données tarifaires, taxes, accises et frais de prestataires (14/10/2026)

Sources officielles déposées dans `data/cote-d-ivoire/docs/` (URL + SHA-256 dans `legal_sources_tarifaires_2026-10-14.json`).

⚠ Deux de ces documents sont déjà au dépôt sous `data/cote-d-ivoire/docs_officiels/` avec la même empreinte : la circulaire n° 2258 (`CIRCULAIRE-2258-2023-TEC-CEDEAO-SH2022.pdf`) et la note DGI (`IMPOTS-ET-TAXES-CI-TABLEAU-SYNOPTIQUE-2025.pdf`). Le tarif officiel par position (`TEC-CEDEAO-ENRICHI-TAXATION-NATIONALE-27-03-2026.pdf`) et l'annexe fiscale 2026 (`ANNEXE-FISCALE-2026-LOI-2025-987.pdf`) y sont aussi ; le socle CIV est construit sur ce tarif (fiche `CIV_prelevements_TVA_2026-10-10.json`).

## 1. Droits et taxes à l'importation — TOUTES POSITIONS (TEC CEDEAO SH 2022, 6 381 lignes)
Circulaire n° 2258/MBPE/DGD du 31/07/2023 (fichier c_2258.pdf), TEC CEDEAO SH 2022 appliqué à compter du 08/08/2023 :
| Taxe | Taux | Assiette |
|---|---|---|
| Droit de douane (DD) TEC CEDEAO | cat. 0 biens sociaux essentiels 0 % (102 lignes) / cat. 1 première nécessité, matières premières, biens d'équipement 5 % (2 366) / cat. 2 intrants et produits intermédiaires 10 % (1 465) / cat. 3 consommation finale 20 % (2 317) / cat. 4 biens spécifiques pour le développement 35 % (131) | CAF (ad valorem) |
| Redevance Statistique (RS) | 1 % | CAF |
| Prélèvement Communautaire CEDEAO (PCC) | 0,5 % | CAF |
| Prélèvement Communautaire de Solidarité UEMOA (PCS) | 0,8 % | CAF |
| Prélèvement Union Africaine (PUA) | 0,2 % | CAF |
+ TVA 18 % (droit commun). Mesures complémentaires de protection : circulaire n° 1702/MPMB/DGD du 13/02/2015 (fichier 2549.pdf, Règlement C/REG.1/09/13) ; la TAI y est transitoire, 5 ans à compter du 01/01/2015 ; la TCP est temporaire (2 ans au plus en volume, 1 an en prix CAF). Le tarif de 2026 porte encore une TAI sur quelques lignes.

## 2. Accises et taxes spéciales — PAR PRODUIT (note DGI « Impôts et taxes en Côte d'Ivoire », édition 2025, art. 403-418 CGI)
Positions : celles où le tarif DGD du 27/03/2026 porte la taxe (colonnes TSBPT, TAB, TCB, TSM) ; pour les produits pétroliers, les cartouches et les véhicules, le tarif n'a pas de colonne correspondante et la position indiquée est le chapitre usuel.
| Produit | Positions (tarif du 27/03/2026) | Taux |
|---|---|---|
| Super carburant / essences spéciales | 2710 | 85 F/litre à 15°C |
| Essence auto | 2710 | 75 F/l |
| Gasoil | 2710 | 25 F/l |
| Huiles minérales | 2710 | 25 F/l |
| DDO | 2710 | 45 F/kg |
| Fuel-oil domestique/léger/lourd | 2710 | 10 F/kg |
| Graisses consistantes | 2710 | 20 F/kg |
| Champagnes, vins AC et assimilés, vins mousseux | 2204.10, 2204.21, 2204.22, 2204.29.90, 2205 | 40 % (valeur en douane + droits et taxes hors TVA) |
| Vins ordinaires (35 % à la note DGI) | 2204.30 (autres moûts de raisin) seule au tarif | 35 % |
| Bières et cidres | 2203, 2206.00.10, 2206.00.99 | 17 % |
| Autres boissons alcoolisées < 35° | aucune position au tarif | 40 % |
| Autres boissons alcoolisées ≥ 35° | 2207.10.90, 2208 | 45 % |
| Boissons énergétiques et autres boissons non alcoolisées | 2009, 2201.10.20, 2202 (pas l'eau minérale naturelle 2201.10.10) | 14 % |
| Tabacs (cigares, cigarillos, cigarettes, tabac à fumer, vape, chicha) | 2402, 2403, 2404, 8543.40, 8543.70, 8543.90, 9614 | 57 % ; valeur imposable des cigarettes au moins 20 000 F les 1 000 (union douanière) ou 25 000 F (hors union douanière), CGI art. 419 modifié par l'annexe fiscale 2026, art. 26. Taxe sport 7 % et taxe de solidarité SIDA/tabagisme 6 % (projet d'annexe fiscale 2025, art. 19) |
| Cartouches chargées, douilles amorcées | 9306 | 12 F/cartouche |
| Marbres (ouvrés) | 6802.21, 6802.23, 6802.29, 6802.91 | 10 % |
| Parfumerie et cosmétiques | 3303, 3304, 3305, 6704.11 | 10 % ; 15 % pour les produits contenant de l'hydroquinone (3304.99 au tarif) |
| Véhicules de tourisme ≥ 13 CV | 8703 (la puissance fiscale n'est pas dans la position) | 10 % |

## 3. Frais des prestataires (hors fiscalité)
| Prestation | Positions concernées | Frais |
|---|---|---|
| Vérification de la Conformité (VoC) — 4 prestataires mandatés (BIVAC/Bureau Veritas, Cotecna, Intertek, SGS), décret 2017-567 | Produits dont la valeur FOB est supérieure ou égale à 1 000 000 F CFA, **sauf** exclus (annexe de l'Avis : or/métaux précieux 7106-7113, pierres précieuses 7101-7105, armes 9301-9304, animaux vivants ch. 1, poissons/viandes/légumes/fruits frais ch. 2-3 et 7-8 non congelés, floriculture ch. 6, films ch. 37, journaux ch. 49, effets/véhicules usagés, colis postaux, pétrole brut/partiellement raffiné 2709, échantillons, missions diplomatiques, régimes francs, artisanat communautaire) | Route A : 0,45 % FOB ; Route B : 0,40 % FOB ; Route C : 0,30 % FOB + minima par prestataire ; à la charge de l'exportateur ; pénalité 50 % CAF + saisine si import sans certificat |
| RFCV (contrôle documentaire de la valeur, GUCE) | Tous produits dont valeur FOB ≥ 1 000 000 F CFA ; dispense ci-dessous | (montant de la redevance non publié sur la page PWIC — non consigné faute de texte officiel) |
| Produits dispensés de RFCV mais FDI obligatoire | Or, pierres précieuses, objets d'art, métaux de récupération, explosifs, armes, animaux vivants, frais/ch. 6, films, journaux, donations, diplomatiques | — |

## 4. Non obtenus (raisons)
- **Guichet tarifaire GUCE** (guce.gouv.ci/customs/tariff/rules) : accès SSO obligatoire.
- **Listes TAI par position en vigueur** : arrêtés annuels non publiés en ligne.
- **Annexe fiscale 2025 adoptée** : seul le projet (dgbf.ci) a été obtenu ; l'annexe fiscale 2026 (loi n° 2025-987) est déjà au dépôt.

## Compléments d'analyse (session du 14/10/2026, lecture coordonnées du tarif 27/03/2026)
- Concordance TSB ↔ positions établie ligne à ligne : bière 2203 = 17 % ; vins 2204/2205 = 40 % ; spiritueux 2207-2208 = 45 % ; jus 2009 = 14 % ; **tomates préparées 2002.10.00 et 2002.90.20 = DD 35 % + TSB 25 % + TVA 18 %** (p. 83 du tarif).
- Texte fondant le TSB 25 % sur les tomates préparées : **non identifié en ligne** (le tableau DGI ne cite pas la tomate à l'art. 418 ; CGI/CIBS en lecteur en ligne uniquement). À confirmer DGD/DGI.
- Légende officielle SYDAM (TUB, TUF, TUE, PSV, TMP, TCI, PSS) : **à demander à la DGD** — déductions dans `docs_officiels/CODES-SYDAM-SIGNIFICATION-BASES.md`.
- Ordonnance n° 2025-260 du 23/04/2025 (démantèlement ZLECAf, 10 ans, produits non sensibles) : texte intégral non public (J.O. 2025 pas en libre accès ; biblio.cndj.ci sur abonnement) ; ratification adoptée par le Parlement le 24/08/2026 (presse) ; loi de ratification et décrets d'application non téléchargés. NB : la page PWIC est une maquette de démonstration (PANEOTECH), informations indicatives.
- Un seul texte déposé est un projet : l'annexe fiscale 2025 (CIV-AF-LF2025-PROJET, « Projet d'annexe fiscale » sur chaque page) ; les autres sont des textes adoptés ou publiés.
