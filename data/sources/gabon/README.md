# Gabon — collecte (partielle)

Consultation : 2026-07-25 (Africa/Algiers).

Quatrième pays CEMAC abordé. Contrairement au Cameroun, au Tchad et au Congo-Brazzaville, **le taux normal de la TVA gabonaise n'a pas pu être vérifié sur texte primaire** dans ce cycle — collecte délibérément incomplète, documentée ci-dessous plutôt que comblée par une source secondaire.

## Ce qui a été vérifié sur texte primaire

Le Journal Officiel de la République Gabonaise n°51 Bis Spécial (20 janvier 2025), portant la Loi de Finances 2025 (Loi n°033/2024 du 30 décembre 2024), a été localisé et téléchargé — hébergé sur un miroir tiers (`directinfosgabon.com`) car le portail gouvernemental (`economie.gouv.ga`, `finances.gouv.ga`, `dgi.ga`) était injoignable depuis cet environnement au moment de la collecte. Le contenu porte l'entête et la pagination authentiques du Journal Officiel, ce qui en fait une republication d'un texte primaire plutôt qu'un résumé.

Deux mesures y ont été directement lues et vérifiées :
- **Article 221 nouveau** (Livre II, Titre 1, Chapitre 2, Section 3) : taux réduit de **5%** sur une liste de produits précise (eau minérale produite au Gabon, lessive, fer à béton, ordinateurs, conserves de légumes/fruits, fourniture d'eau/électricité sur compteurs sociaux, ciment).
- **Article 210 nouveau** (Livre II, Titre 1, Chapitre 1, Section 3) : exonération TVA sur les ventes de pétrole aux pêcheurs artisanaux, sous conditions cumulatives.

## Ce qui n'a PAS été vérifié — et pourquoi

Le **taux normal** de la TVA n'apparaît pas dans la Loi de Finances 2025 : cette loi ne modifie que les articles 210 et 221 (partie « nouveau »), pas l'article fixant le taux normal, qui n'est donc pas restaté dans ce texte. Des recoupements tertiaires (cabinets d'avocats, agrégateurs fiscaux — non faisant autorité) rapportent un taux normal de 18% au Code Général des Impôts, Article 221 (numérotation antérieure aux modifications). **Aucune entrée `VAT-RATE-STANDARD` n'a été créée** : conformément à la règle de sincérité, un taux répété par des tiers sans lecture directe du texte de loi n'est pas enregistré comme vérifié.

La source qui permettrait de lever ce doute est identifiée : `dgi.ga/787-procedures-et-avantages-fiscaux/1071-code-general-des-impots/1075-livre-2-taxes-sur-le-chiffre-daffaires/` — mais injoignable (HTTP 403/timeout) depuis cet environnement au moment de la collecte.

## Ce qui reste à collecter

- **Taux normal de la TVA** (priorité) : re-tenter le portail DGI, ou localiser une édition complète du Code Général des Impôts.
- Droit d'accises, prélèvements, TEC CEMAC : non abordés.
- Vérification indépendante du miroir `directinfosgabon.com` dès que le portail gouvernemental redevient accessible.

## État de l'enregistrement

Juridiction GAB : **non** enregistrée dans `SUPPORTED_JURISDICTIONS` — aucun taux TVA standard vérifié, seules deux mesures ponctuelles (taux réduit 5% sans code SH, exonération conditionnelle) le sont. ZLECAf : **pas** d'offre nationale encore enregistrée dans `NATIONAL_OFFER_REGISTRY`.

## Collecte du 2026-10-29

Deux Journaux Officiels archivés (`official/`, empreintes dans `inventory.csv`) :

- **JO n°96 Quater Spécial du 30 décembre 2025** — loi n°041/2025, loi de finances 2026 (miroir `directinfosgabon.com`, entête et pagination du JO). Art. 250 nouveau du CGI : tableau complet des droits d'accises (taux ad valorem et taxes spécifiques).
- **JO n°123 Bis du 17 juillet 2026** — loi n°002/2026, loi de finances rectificative 2026, publiée sur `budget.gouv.ga` (ministère de l'Économie et des Finances). Art. 250 nouveau : bières locales, vins d'importation, champagnes, tabacs et produits du vapotage. Art. 221 nouveau : **taux normal de TVA de 18 %**, lu sur texte primaire, et taux réduits de 10 %, 5 % et 3 %.

Droit d'accises intégré au socle : fiche `backend/data/legal_refs/zlecaf_application/GAB_droit_accises_2026-10-29.json`.

### Prélèvements à l'importation (2026-10-29)

- **DGDDI, « Présentation de la fiscalité douanière » (2021)** : CCI de la CEEAC 0,4 % (pays tiers), prélèvement OHADA 0,05 %, contribution UA 0,2 % (non membres de l'UA), « ajouter la css ».
- **JO n°331 Bis Spécial du 9 janvier 2017** (loi n°026/2016, copie FAOLEX) : contribution spéciale de solidarité, art. 13 à 25 — importations comprises, base comme en matière de TVA, 1 %.
- **Loi n°025/2022 (loi de finances 2023)**, journal-officiel.ga : art. 34, CCI, TCI, OHADA et contribution UA prélevés au cordon douanier.
- Redevance informatique : taux non trouvé sur texte primaire (1,5 % de la valeur en douane selon une page du Conseil gabonais des chargeurs, injoignable).

Fiche : `backend/data/legal_refs/zlecaf_application/GAB_prelevements_importation_2026-10-29.json`.
