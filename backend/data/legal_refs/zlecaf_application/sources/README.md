# Sources primaires archivées — application nationale de la ZLECAf

Documents officiels sur lesquels reposent les fiches de vérification du
répertoire parent. Ils sont **archivés ici et non seulement référencés par une
URL** : un lien meurt, une administration réorganise son site, un portail
devient injoignable. Le portail douanier algérien, injoignable depuis
l'environnement de vérification au moment de cette collecte, en est la
démonstration immédiate.

Chaque fiche `ISO_application_*.json` porte le SHA-256 du document qui la
fonde. Le test `backend/tests/test_zlecaf_legal_sources.py` vérifie que le
fichier archivé correspond bien à cette empreinte : une fiche ne peut donc pas
citer un document que le dépôt ne contient pas, ni un document différent de
celui qui a été lu.

| Fichier | Pays | Autorité | Contenu |
|---|---|---|---|
| `MAR_circulaire_6530-223_2024-01-22.pdf` | Maroc | ADII | Circulaire de base : mise en œuvre douanière de la ZLECAf, listes P1 (27 pays, 5 ans) et P2 (13 pays, 10 ans), démantèlement depuis le 1er janvier 2021. 158 pages |
| `MAR_circulaire_6627-223_2025-01-09.pdf` | Maroc | ADII | Met à jour les codes tarifaires de la liste A pour la nomenclature 2025. **Ne modifie pas** les listes de pays |
| `MAR_circulaire_6705-222_2025-12-31.pdf` | Maroc | ADII | **Preuve négative** : concerne les accords Maroc/USA et Maroc/Royaume-Uni, sans aucune mention de la ZLECAf. Archivée pour établir qu'elle n'affecte pas la détermination |
| `EGY_manshour_ittifaqiyat_38.pdf` | Égypte | Douane égyptienne | Circulaire Accords n° 38 : 17 origines en deux groupes, 10 ans à 50 % de réduction au 1/1/2025 et 5 ans à 100 %. Listes B et C non entrées en vigueur |
| `EGY_manshour_ittifaqiyat_36_2024-12-22.pdf` | Égypte | Ministère de l'Investissement et du Commerce extérieur | Notifie l'entrée en échanges du Burundi, de l'Eswatini, du Lesotho, du Malawi, de la Gambie et de l'Ouganda. Référence le décret présidentiel n° 212 de 2023 |
| `SOM_customs_tariff_2020.preambule-extrait.txt` | Somalie | Ministère des Finances | Somali Customs Tariff 2020, règles générales concernant les droits (B.3) et applicables à la nomenclature et aux droits (C.1) : le droit ad valorem est liquidé sur la valeur en douane, déterminée sur la valeur de transaction. Extrait des pages 9-10 ; PDF de 341 p. non archivé |
| `SOM_somcas_sop_annexe-C.texte-extrait.txt` | Somalie | Somalia Revenue Directorate / Somali Customs | SOP SOMCAS, Annexe C « Customs Valuation » : valeur = « normal price » alignée sur la « transaction value » du WTO Valuation Agreement ; traitement FOB/CIF (fret + assurance). Extrait des pages 29-31 ; PDF de 35 p. non archivé |
| `DZA_ctca_TVA_extrait.txt` | Algérie | Direction Générale des Douanes | Code des taxes sur le chiffre d'affaires (CTCA), extraits TVA : taux normal 19 % (art. 21), taux réduit 9 % (art. 23), exonérations (art. 8/9/10/11) ; + art. 214 LF2025 (café vert) reconduit par la LF2026. Extrait du PDF de 83 p. non archivé |
| `SACU_assiette_DD.source-extrait.txt` | SACU (BWA/LSO/NAM/SWZ/ZAF) | SARS + BURS/LRA/NamRA/ERA | Customs and Excise Act 91/1964 s.65/67 + politique SARS SC-CR-A-03 : le droit de douane s'assied sur la valeur de transaction base FOB (fret/assurance internationaux exclus), pas CIF. PDF non archivés |

## Fichiers `.ocr-ara.txt`

Les circulaires égyptiennes sont des PDF scannés sans couche de texte. Elles ont
été lues à l'image, puis repassées à l'OCR arabe (`tesseract -l ara --psm 6`)
dont la sortie est archivée ici. Les deux méthodes donnent les mêmes listes de
pays ; l'OCR dégrade en revanche les chiffres arabo-indiens — `٥٠٪` en ressort
sous la forme `./5٠0`. **Les taux et les dates proviennent donc de la lecture
d'image, jamais de l'OCR seul.** La sortie OCR est conservée pour permettre une
recherche plein texte et une re-vérification mécanique des libellés.

## Ce qui manque

La circulaire algérienne n° 482/DGD/SP/D.042/24 du 22 octobre 2024 **est**
archivée ici, sous la forme de son texte intégral extrait
(`DZA_circulaire_482-DGD_2024-10-22.texte-extrait.txt`) ; le PDF de 8,5 Mo ne
l'est pas. `DZA_application_2026-09-14.json` classe donc la preuve algérienne au
niveau primaire, et non secondaire.

Restent à archiver : le PDF de cette circulaire, et la circulaire
interministérielle n° 02 du 26 septembre 2024, qui n'est ni l'une ni l'autre
présente.

Sur l'accès : le diagnostic d'un « échec réseau » était faux et est corrigé. Le
DNS résout, le tunnel s'établit et la chaîne TLS est valide — `openssl` rend
« Verify return code: 0 (ok) » avec le bundle fourni. Le serveur répond un 503 :
`douane.gov.dz` refuse le client, ce qui n'est ni un blocage réseau ni un défaut
de certificat.
