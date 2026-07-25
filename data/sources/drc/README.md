# République Démocratique du Congo (RDC) — collecte

Consultation : 2026-07-25 (Africa/Algiers).

RDC a rejoint l'East African Community en 2022 et applique le CET EAC (déjà archivé sous `data/sources/kenya/official/eac-cet-2022-updated-june-2025.pdf`). Contrairement à la Tanzanie/l'Ouganda/le Rwanda (écosystème AfricanLII), la RDC publie sa législation fiscale consolidée via **LEGANET.CD**, un portail de législation distinct mais du même type (texte consolidé, gratuit, accessible).

## Sources localisées et vérifiées

| Acte | Source | État |
|---|---|---|
| Ordonnance-loi n° 10/001 du 20 août 2010 (TVA) | https://www.leganet.cd/Legislation/Dfiscal/TVA/OL.10.001.20.2010.htm | **archivé et haché** |
| Décret n° 011/42 du 22 novembre 2011 (mesures d'exécution) | https://www.leganet.cd/Legislation/Dfiscal/TVA/D.11.42.22.11.2011.htm | localisé, non archivé |
| Ordonnance-loi n° 001/2012 du 21 septembre 2012 (modifications TVA) | droitcongolais.info (miroir) | localisé, texte intégral non encore lu |
| Portail DGI | https://dgi.gouv.cd/ | accessible, non exploré en profondeur |
| Portail DGDA (douanes) | https://douane.gouv.cd/ | accessible, non exploré en profondeur |

## Faits vérifiés sur texte primaire

- **TVA standard : 16%** — Ordonnance-loi n° 10/001 du 20 août 2010, **Article 35, alinéa 1er** : *« Le taux de la taxe sur la valeur ajoutée est fixé à 16 %. »* Entrée en vigueur effective : 1er janvier 2012.
- **Taux zéro sur les exportations** — même article, alinéa 2. Non encodé comme exonération automatique (`hs_codes_explicit` vide) : conforme à la règle « pas d'auto-application sans code SH explicite ».
- Archive HTML téléchargée et hachée SHA-256 le 2026-07-25 (`data/sources/drc/official/cod-ordonnance-loi-10-001-2010-tva.html`).

## Ce qui reste à collecter

- Lecture intégrale de l'Ordonnance-loi n° 001/2012 pour confirmer qu'elle ne modifie pas le taux de l'Article 35 (à ce stade, seuls des recoupements tertiaires — non faisant autorité — indiquent une continuité du taux à 16%)
- Décret n° 011/42/2011 : exonérations d'exécution à codes SH explicites
- Accises (Direction Générale des Douanes et Accises) : instrument à identifier
- Formalités douanières et régimes économiques particuliers (DGDA)
- Confirmation d'une éventuelle offre tarifaire ZLECAf nationale (niveau 2) déposée par la RDC

## Règles d'archivage

Même politique que le Kenya : archive HTML pour texte consolidé de faible poids ; SHA-256 recalculé à chaque re-téléchargement ; PDF lourds exemptés et documentés dans `inventory.csv`.

## État de l'enregistrement

Juridiction COD : **non** enregistrée dans `SUPPORTED_JURISDICTIONS` (`backend/services/national_legal_calculation_service.py`) — seule la TVA standard est vérifiée sur texte primaire ; il manque `excise_measures.json` et `import_levies.json` pour instancier `NationalFiscalStore`. ZLECAf : **pas** d'offre nationale encore registrée dans `NATIONAL_OFFER_REGISTRY`.
