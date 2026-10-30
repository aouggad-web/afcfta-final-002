# Congo-Brazzaville (République du Congo) — collecte

Consultation : 2026-07-25 (Africa/Algiers).

Troisième pays CEMAC collecté. Le Ministère des Finances héberge directement le Code Général des Impôts en PDF sur son propre domaine officiel (`finances.gouv.cg`) — accessible en `curl` direct, bien que le portail bloque l'outil WebFetch (403).

## Source primaire

**Code Général des Impôts, Tome I (Impôts d'État)** — https://www.finances.gouv.cg/sites/default/files/documents/CGI%20Tome%20I.pdf (2,7 Mo, 332 pages, archivé intégralement).

## Faits vérifiés sur texte primaire

- **TVA taux normal : 18%** — Article 17, Section II (Taux), Chapitre IV : « taux normal : 18 % applicable sur toutes les opérations taxables à l'exclusion de celles visées ci-dessous ». Consolidé par Loi n°12-99 du 12 février 1999, Loi n°17-2000 du 30 décembre 2000, Loi n°10-2002 du 31 décembre 2002.
- **Taux zéro** — même article : exportations et accessoires, transports internationaux, filière eucalyptus.
- **Annexe 5 (liste de biens à taux réduit)** repérée dans le texte : poisson, viande, volaille, laits alimentaires, riz, pain, préparations pour l'alimentation des enfants (à l'importation), et semences/fumiers/engrais/aliments de bétail/animaux reproducteurs/poussins d'un jour. **Le pourcentage du taux réduit n'a pas pu être extrait de ce tome** (probablement défini dans une loi modificative non incluse dans ce Tome I) — aucune donnée n'a été fabriquée pour cette valeur.

## Ce qui reste à collecter

- **Pourcentage exact du taux réduit** de l'Annexe 5 (une source complémentaire — texte modificatif ultérieur — doit être localisée).
- **Droit d'accises** : non extrait dans ce cycle.
- **Tarif Extérieur Commun (TEC) CEMAC** : non archivé.
- Exploration approfondie du portail `finances.gouv.cg` (actualités, autres tomes du CGI).

## Règles d'archivage

PDF de 2,7 Mo, sous le seuil de poids toléré : archivé intégralement.

## État de l'enregistrement

Juridiction COG : **non** enregistrée dans `SUPPORTED_JURISDICTIONS` — seule la TVA (taux normal et zéro) est vérifiée ; il manque `excise_measures.json`, `import_levies.json` et le TEC CEMAC. ZLECAf : **pas** d'offre nationale encore enregistrée dans `NATIONAL_OFFER_REGISTRY`.

## Prélèvements à l'importation (relevé du 2026-10-30)

- **Redevance informatique : 2 %** à l'importation des marchandises mises à la consommation — loi n° 42-2025 du 31 décembre 2025 (loi de finances 2026), art. 48, point 25 (art. 44 nouveau) ; rédaction antérieure : loi n° 37-2021 (LFR 2021), art. 44, point 41. Assiette : valeur c.a.f. (OMC, WT/TPR/S/445, annexe Congo, § 3.17).
- **Contribution communautaire d'intégration de la CEEAC : 0,4 %** des importations hors CEEAC, « actuellement collectée par le Congo, le Gabon, la République centrafricaine et le Tchad » (OMC, WT/TPR/S/445, rapport commun, § 3.40 ; annexe Congo, § 3.48).
- **Prélèvement OHADA : 0,05 %** de la valeur CAF des produits originaires des pays tiers à l'OHADA ; exonérés notamment les produits originaires des communautés dont le Congo est membre et les produits pharmaceutiques et matériels médicaux (arrêté n° 5808 du 20 septembre 2005, art. 2 à 5).
- Fiche : `backend/data/legal_refs/zlecaf_application/COG_prelevements_importation_2026-10-30.json`.
