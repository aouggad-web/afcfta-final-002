# Accises CEMAC — manques à corriger

Tenu au fur et à mesure du traitement pays par pays (décision du propriétaire,
2026-10-05). Chaque ligne dit ce qui manque, son effet sur le calcul, et ce qui
le corrigerait.

## Commun aux six États

| Manque | Effet | Correction |
|---|---|---|
| Le crawl marquait l'accise « variable » (-1) sur 292 positions identiques dans les six pays, à partir d'un repère typographique (tissus de coton, médicaments, sel inclus ; voitures et cosmétiques omis) | Positions faussement PARTIEL, et produits soumis servis COMPLET sans accise | Table par pays tirée de son code des impôts — fait : CMR, GAB ; reste : COG, TCD, CAF, GNQ |
| Les socles CEMAC (nomenclature à 8 chiffres, ancienne numérotation SH) ont des trous de collecte : saumons frais 0302.1x, filets 0304, fumés 0305.41, foies et œufs 0303.90, boissons fermentées 22.06 (CMR) | Ces positions ne reçoivent ni droit ni accise | Recollecter le tarif CEMAC (TEC) à jour |
| L'âge des véhicules n'est dans aucune position (cylindrée et énergie seulement) | Accise des véhicules portée sans taux : PARTIEL | Champ « âge du véhicule » dans le calculateur, ou nomenclature nationale à 10-11 chiffres |
| Droits spécifiques (par litre, par centilitre, par paquet, par 1 000 tiges) et taux selon la gamme ou le prix d'achat des boissons | Accise portée sans taux : PARTIEL | Saisie du volume, de la contenance et de la gamme dans le calculateur |
| Composition des cosmétiques (hydroquinone : 50 % au Cameroun) | Taux général appliqué | Question à l'utilisateur dans le calculateur |

## Cameroun (CMR) — PR #596

| Manque | Effet | Correction |
|---|---|---|
| Source : CGI édition 2025 (compilation de cabinet) ; loi de finances 2026 non vérifiée | Taux 2026 possiblement différents | Lire la loi de finances 2026 (dgb.cm) |
| TCI retirée de l'assiette de la TVA selon l'art. 138 (1) du CGI (le crawl l'y incluait) | Écart d'environ 0,2 % de la valeur | Confirmer auprès de la DGI / douane |
| Emballages non retournables (droit spécifique par unité) | Non liquidé | Sans position tarifaire : hors calculateur |

## Gabon (GAB)

| Manque | Effet | Correction |
|---|---|---|
| Loi de finances 2026 (n° 041/2025 du 29/12/2025) et loi de finances rectificative 2026 non lues : taux des bières (200 F/l), vins, champagnes, tabacs modifiés ; champ étendu aux véhicules (5 % tourisme sauf neufs < 1 500 cm3, 1 % autres et motocycles), armes (10 %), emballages (1 %) | Ces droits sont portés sans taux : PARTIEL | Trouver le texte officiel des deux lois (Journal officiel, dgi.ga) |
| Jus de fruits : « boisson sucrée » ou non | Porté sans taux | Critère à préciser (DGI) |
| Désignations du crawl GAB décalées d'une ligne par rapport aux codes | Libellés faux à l'écran | Recollecte du tarif |
