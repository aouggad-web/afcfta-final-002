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
