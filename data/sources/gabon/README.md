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

Juridiction GAB : **non** enregistrée dans `SUPPORTED_JURISDICTIONS` — aucun taux TVA standard vérifié, seules deux mesures ponctuelles (taux réduit 5% sans code SH, exonération conditionnelle) le sont. ZLECAf : **pas** d'offre nationale encore registrée dans `NATIONAL_OFFER_REGISTRY`.
