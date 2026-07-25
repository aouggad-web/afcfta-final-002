# Rwanda — collecte (TVA + accises vérifiées)

Consultation : 2026-07-25 (Africa/Algiers).

**Correction de collecte.** Une première passe sur cette branche avait enregistré `data/rwanda/vat_measures.json` avec un statut `PENDING_OFFICIAL_CONSOLIDATION`, un SHA-256 `pending_collection`, et une référence légale incorrecte (« Value Added Tax Law 2018, Law No. 28/2018 of 13/02/2018 »). La loi TVA réellement en vigueur est la **Loi n°049/2023 du 05/09/2023 portant TVA**, publiée au Journal Officiel du 14/09/2023, qui abroge la Loi n°37/2012. Ce cycle remplace ces données par une collecte vérifiée sur texte primaire, archivée et hachée, et ajoute les accises.

## Ce qui a été vérifié sur texte primaire

**TVA** — Loi n°049/2023 du 05/09/2023, téléchargée directement depuis le portail de la Rwanda Revenue Authority (`rra.gov.rw`, source primaire directe, texte trilingue kinyarwanda/anglais/français) :
- **Taux standard 18%** et **taux zéro** — Article 4 : « (a) 0% [...] taux de zéro tels que prévus par la présente loi ; (b) ou de 18% pour les autres biens et services fournis au Rwanda ou importés. »
- **Taux zéro — liste** — Article 7(1) : exportations de biens et services (a, b), minerais vendus sur le marché intérieur (c), transport international (d), etc. 3 postes transcrits.

**Accises** — Loi n°011/2025 du 27/05/2025 portant instauration du droit d'accise, publiée au Journal Officiel n° Spécial du 29/05/2025 et téléchargée depuis le portail du Ministère de la Justice (source primaire gouvernementale directe). Cette loi **abroge et remplace** la précédente loi d'accise (Loi n°050/2023 du 05/09/2023) :
- Imposition : article liminaire de la loi.
- Annexe (barème par ligne SH) : 7 postes représentatifs transcrits (bière, vin, cigarettes, essence, gasoil, véhicules <1500cc).

**Note sur la TVA amendée en 2025** — Le même Journal Officiel du 29/05/2025 contient la Loi n°009/2025 du 27/05/2025 modifiant la Loi n°049/2023. Vérification faite : cette modification ne touche que l'Article 8 (exonérations), pas les articles de taux (4, 7) cités ci-dessus — le taux standard 18% et le mécanisme taux zéro restent donc à jour.

## Ce qui n'a PAS été vérifié — et pourquoi

- **Annexe de la loi d'accise non exhaustive** : la liste complète couvre environ 27 catégories de produits/services (jus, sodas, sirops aromatisés, bière, vin, spiritueux, cigarettes, cigarettes électroniques, carburants, lubrifiants, véhicules par cylindrée, cosmétiques, télécommunications, frais de transfert d'argent…) ; seules 7 lignes ont été transcrites ce cycle.
- **Finance Law 2026** et **Customs Tariff Guide (RRA)** : URLs localisées lors d'une passe antérieure, non re-téléchargées ni re-vérifiées ce cycle.
- **TEC EAC** : déjà archivé pour le Kenya, non relié ici sans vérification d'applicabilité identique.

## État de l'enregistrement

Juridiction RWA : **non** enregistrée dans `SUPPORTED_JURISDICTIONS` — accises non exhaustives, pas de Finance Law, pas de TEC. ZLECAf : **pas** d'offre nationale encore enregistrée dans `NATIONAL_OFFER_REGISTRY`.
