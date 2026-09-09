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

## Lot réglementaire (2026-07-29) — formalités et contrôles à l'importation

Ce cycle ajoute `data/drc/regulatory_measures.json` : trois mesures réglementaires obligatoires à l'importation, distinctes des taux fiscaux (SEGUCE, OCC/CBCA, FERI/FERE).

**Statuts canoniques de vérification** appliqués à ce lot (aucune archive n'a pu être produite ce cycle) :
- `PARTIAL` : source officielle identifiable (portail gouvernemental / parastatal, référence d'ordonnance-loi ou de décret) mais **non archivée** sur texte primaire ;
- `UNVERIFIED` : information recoupée uniquement par des sources secondaires (aucune mesure de ce lot n'est en `UNVERIFIED`) ;
- `pending_primary_archive: true` : drapeau maintenu tant que l'extrait primaire daté n'est pas téléchargé et haché.

**Pourquoi aucune archive.** Les portails officiels (`commerce.gouv.cd/seguce`, `segucerdc.com`, `occ.cd`, `ogefremsite.org`) renvoient **HTTP 403 Forbidden** sur récupération automatique (WebFetch). Aucun contournement n'a été tenté ; les références légales ont été identifiées par recoupement de sources officielles sans lecture directe du texte primaire.

**BIVAC — prestataire mandaté, pas mesure autonome.** Un prestataire privé mandaté reste un acteur officiel d'exécution dans la limite de son mandat. BIVAC (Bureau Veritas) figure comme `mandated_actors[]` (type `MANDATED_SERVICE_PROVIDER`) **sous** la mesure OCC/CBCA (`COD-OCC-CBCA`), et non comme un enregistrement réglementaire distinct. Sa fiche d'acteur documente : statut juridique, autorité mandante (OCC), mission, base du mandat, durée (`NOT_AVAILABLE`), frais autorisés (`null`), document délivré.

**Frais / tarifs.** Tous les champs `fees` sont laissés à `null` (`fees_status: NOT_AVAILABLE`). **Aucun montant issu de source secondaire n'est renseigné** — aucun frais n'entre dans le calculateur tant qu'une source officielle actuelle ne le confirme pas.

| Mesure | Autorité | Statut |
|---|---|---|
| SEGUCE / GUICE (guichet unique) | SEGUCE RDC SA / Min. Commerce Extérieur | PARTIAL |
| OCC / CBCA (conformité, BIVAC opérateur) | Office Congolais de Contrôle | PARTIAL |
| FERI / FERE (suivi du fret) | OGEFREM | PARTIAL |

## État de l'enregistrement

Juridiction COD : **non** enregistrée dans `SUPPORTED_JURISDICTIONS` (`backend/services/national_legal_calculation_service.py`) — seule la TVA standard est vérifiée sur texte primaire ; il manque `excise_measures.json` et `import_levies.json` pour instancier `NationalFiscalStore` ; les mesures réglementaires ci-dessus sont documentaires (aucun taux/frais exploitable). ZLECAf : **pas** d'offre nationale encore registrée dans `NATIONAL_OFFER_REGISTRY`.
