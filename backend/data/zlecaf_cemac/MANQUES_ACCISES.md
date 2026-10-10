# Accises CEMAC — manques à corriger

Tenu au fur et à mesure du traitement pays par pays (décision du propriétaire,
2026-10-05). Chaque ligne dit ce qui manque, son effet sur le calcul, et ce qui
le corrigerait.

## Commun aux six États

| Manque | Effet | Correction |
|---|---|---|
| Le crawl marquait l'accise « variable » (-1) sur 292 positions identiques dans les six pays, à partir d'un repère typographique (tissus de coton, médicaments, sel inclus ; voitures et cosmétiques omis) | Positions faussement PARTIEL, et produits soumis servis COMPLET sans accise | Table par pays tirée de son code des impôts — fait : CMR, GAB, COG, CAF, GNQ ; reste : TCD (bloqué) |
| Les socles CEMAC (nomenclature à 8 chiffres, ancienne numérotation SH) ont des trous de collecte : saumons frais 0302.1x, filets 0304, fumés 0305.41, foies et œufs 0303.90, boissons fermentées 22.06 (CMR) | Ces positions ne reçoivent ni droit ni accise | Recollecter le tarif CEMAC (TEC) à jour |
| L'âge des véhicules n'est dans aucune position (cylindrée et énergie seulement) | Accise des véhicules portée sans taux : PARTIEL | Champ « âge du véhicule » dans le calculateur, ou nomenclature nationale à 10-11 chiffres |
| Droits spécifiques (par litre, par centilitre, par paquet, par 1 000 tiges) et taux selon la gamme ou le prix d'achat des boissons | Accise portée sans taux : PARTIEL | Saisie du volume, de la contenance et de la gamme dans le calculateur |
| Composition des cosmétiques (hydroquinone : 50 % au Cameroun) | Taux général appliqué | Question à l'utilisateur dans le calculateur |

## Cameroun (CMR) — PR #596

| Manque | Effet | Correction |
|---|---|---|
| Source : CGI édition 2025 (compilation de cabinet), confrontée à l'édition officielle 2026 de la DGI | — | Fait (bouteilles à gaz ajoutées, droits spécifiques des alcools relevés, emballages supprimés) |
| TCI retirée de l'assiette de la TVA selon l'art. 138 (1) du CGI (le crawl l'y incluait) | Écart d'environ 0,2 % de la valeur | Confirmer auprès de la DGI / douane |
| Bouteilles à gaz domestique vides (12,5 %, LF 2026) : 7311.00.90 mêle d'autres récipients non visés | Accise portée sans taux : PARTIEL | Nomenclature nationale ou question à l'utilisateur |
| Annexe II en codes SH 2017 absents du socle (SH 2007) : ouvrages en bois 4418.73-4418.74, cercueils 4421.20 | Non soumis dans le socle | Concordance SH 2017 → SH 2007 ou recollecte du TEC |
| Positions partiellement visées (café 0901.11 hors certaines sous-positions nationales, cure-dents 3926.90.90, ouvrages en bois 4421.90, viandes salées 0210) | Accise portée sans taux : PARTIEL | Nomenclature nationale à 11 chiffres |
| « 324.90.00.0000 » (pipes, art. 142 (6) e) : coquille de la source, 3824.90 ou autre | Non retenu | Confirmer auprès de la DGI |
| Plage 0201 à 0210 de l'annexe : seules les espèces bovine, caprine, ovine et les volailles sont retenues (art. 142 (6) a) ; porc, cheval, gibier (0203, 0205, 0208, 0209) non soumis | À confirmer | DGI |

## Gabon (GAB) — PR #596

| Manque | Effet | Correction |
|---|---|---|
| Loi de finances 2026 (n° 041/2025 du 29/12/2025) et loi de finances rectificative 2026 non lues : taux des bières (200 F/l), vins, champagnes, tabacs modifiés ; champ étendu aux véhicules (5 % tourisme sauf neufs < 1 500 cm3, 1 % autres et motocycles), armes (10 %), emballages (1 %) | Ces droits sont portés sans taux : PARTIEL | Trouver le texte officiel des deux lois (Journal officiel, dgi.ga) |
| Jus de fruits : « boisson sucrée » ou non | Porté sans taux | Critère à préciser (DGI) |
| Désignations du crawl GAB décalées d'une ligne par rapport aux codes | Libellés faux à l'écran | Recollecte du tarif |

## Congo (COG)

| Manque | Effet | Correction |
|---|---|---|
| Source : loi de finances 2026 (loi n° 42-2025, art. 2 et 8 nouveaux), lue sur le PDF du ministère des Finances | — | Fait (fiche COG_droit_accises_2026-10-09.json) |
| « Produits alimentaires de luxe » : liste non donnée par la loi ; cosmétiques à l'hydroquinone (50 %) non distingués dans la position | Luxe : accise portée sans taux ; hydroquinone : taux général 25 % servi | Liste et composition à préciser (DGID / douane) |
| Alcool éthylique (22.07) : « boissons alcoolisées » du chapitre 22 ou non, la loi ne le dit pas | Accise portée sans taux : PARTIEL | Confirmer (DGID / douane) |
| Boissons des positions 22.02.10 et 22.02.90 : soda, boissons sucrées et énergisantes (10 %) mêlés à des eaux aromatisées et boissons non visées | Accise portée sans taux : PARTIEL | Nomenclature nationale ou question à l'utilisateur |
| Billards et autres jeux (95.04.20, 95.04.90) : appareils de jeux (25 %) ou articles de jeu, non dit | Accise portée sans taux : PARTIEL | Confirmer (DGID / douane) |
| Véhicules de tourisme : neufs ≤ 3 000 cm3 exonérés, l'état neuf ou d'occasion n'est pas dans la position | Accise portée sans taux sauf 8703.24 : PARTIEL | Champ « neuf / occasion » dans le calculateur |
| Base arrondie au millier de francs inférieur (art. 7 (2)) | Non appliqué : écart inférieur à 1 000 F | Arrondi dans le moteur si demandé |
| Position 22.06 absente du socle COG | Boissons fermentées sans droit ni accise | Recollecter le TEC |

## Centrafrique (CAF)

| Manque | Effet | Correction |
|---|---|---|
| Les taux du CGI 2023 sont des minimums ; la loi de finances fixe les taux (art. 292). Lois de finances 2024, 2025, 2026 et rectificatives 2024 et 2025 lues : aucune ne modifie les art. 289 bis à 293 | — | Fait (fiche CAF_droit_accises_2026-10-05.json) |
| Droit spécifique ajouté au taux ad valorem pour les bières, vins, spiritueux, cigares et cigarettes (art. 293) | Accise portée sans taux : PARTIEL | Saisie du volume ou du nombre dans le calculateur |
| Véhicules 87.02, 87.03, 87.04 : taux selon l'âge (0 à 15 ans, plus de 15 ans) et état neuf ou d'occasion | Accise portée sans taux : PARTIEL | Champ « âge du véhicule » (commun) |
| Eaux 22.01 : eau minérale exclue, eaux gazéifiées soumises, même position | Porté sans taux | Question à l'utilisateur |
| Base arrondie au millier de francs inférieur (art. 291 (2)) | Non appliqué | Arrondi dans le moteur si demandé |
| TVA : le crawl l'assoyait sur CIF + DD + TCI ; l'art. 253 dit valeur + DD + accise | Corrigé dans le socle | — |

## Tchad (TCD) — bloqué

| Manque | Effet | Correction |
|---|---|---|
| Le CGI 2025 et la loi de finances 2026 sont publiés sur finances.gouv.td, dont le certificat TLS ne correspond pas au nom d'hôte : téléchargement refusé (vérification TLS maintenue). Seuls le CGI 2016 et la loi de finances 2020 sont en ligne ailleurs (africa-laws.org), trop anciens | Le marquage du crawl reste en place | Le propriétaire télécharge le CGI 2025 et la LF 2026 depuis finances.gouv.td |

## Guinée équatoriale (GNQ)

| Manque | Effet | Correction |
|---|---|---|
| Source : guide fiscal du ministère (2020) ; texte de la loi de budget 2020 et des lois suivantes non lu ; la loi de budget 2023 (minfuncionpublica.gob.gq) échoue à la vérification TLS | Liste possiblement incomplète | Le propriétaire télécharge les lois de budget récentes |
| Tous les droits sont spécifiques (par litre, par degré, par unité) | Toutes les accises sans taux : PARTIEL | Saisie du volume, du degré et du nombre dans le calculateur (commun) |
| Derecho Especial de 30 % (loi 4/2004, art. 296) : annexe III introuvable, maintien après 2020 non vérifié | Cosmétiques portés sans taux | Trouver l'annexe III et la loi qui l'a abrogée ou maintenue |
| Impôt sur les véhicules selon la puissance en CV (loi de budget 2020) | Non retenu à l'importation | Confirmer son fait générateur |
| Le socle du crawl reprend le tarif du Cameroun (« réf. État membre CMR ») | Redevances camerounaises possiblement appliquées à tort | Recollecter le tarif propre à la Guinée équatoriale |
