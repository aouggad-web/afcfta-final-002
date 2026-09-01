# Tchad — collecte

Consultation : 2026-07-25 (Africa/Algiers).

Deuxième pays CEMAC collecté. Le portail officiel du Ministère des Finances et du Budget (`finances.gouv.td`) existe et est référencé par la presse tchadienne, mais bloque les requêtes automatisées (HTTP 403 avec en-tête navigateur, HTTP 500 par ailleurs, constaté le 2026-07-25). Le texte du Code Général des Impôts a donc été vérifié via **Africa Laws**, un portail de législation africaine qui reproduit le Code officiel — pas l'autorité elle-même, mais dont le texte a été contrôlé article par article et correspond à la structure attendue d'un CGI CEMAC (base d'imposition, taux, déductions dans le même ordre que le Cameroun et le Congo).

## Source primaire

**Code Général des Impôts, édition 2016** — https://www.africa-laws.org/Chad/Tax%20Law/Code%20G%C3%A9n%C3%A9ral%20des%20imp%C3%B4ts%202016.pdf (2,4 Mo, archivé intégralement).

## Faits vérifiés sur texte primaire

- **TVA taux standard : 18%** — Article 238, I, 1° : « 18 % applicable à toutes les opérations taxables ».
- **Taux zéro sur les exportations** — Article 238, I, 2° et II-III : applicable aux exportations déclarées en douane, sous condition de rapatriement des fonds justifié par quittance du pays de destination.

## Ce qui reste à collecter

- **Loi de finances 2026** : la presse tchadienne (tchadinfos.com) rapporte une extension d'un taux réduit de 9% aux produits laitiers et viande produits localement, effective 2026 — **non confirmé sur texte primaire**, l'édition 2016 du CGI ne le mentionne pas. À vérifier dès que le texte de la loi de finances 2026 sera accessible.
- **Droit d'accises** : structure CEMAC habituelle attendue (comme le Cameroun), non extraite dans ce cycle.
- **Tarif Extérieur Commun (TEC) CEMAC** : non archivé.
- Re-tentative périodique de `finances.gouv.td` pour accéder directement au portail officiel.

## Règles d'archivage

PDF de 2,4 Mo, sous le seuil de poids déjà toléré (CET EAC Kenya : 4,6 Mo) : archivé intégralement, sans extraction.

## État de l'enregistrement

Juridiction TCD : **non** enregistrée dans `SUPPORTED_JURISDICTIONS` — seule la TVA est vérifiée ; il manque `excise_measures.json`, `import_levies.json` et le TEC CEMAC. ZLECAf : **pas** d'offre nationale encore enregistrée dans `NATIONAL_OFFER_REGISTRY`.
