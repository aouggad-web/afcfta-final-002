# Mauritanie — collecte (TVA + taxe de consommation)

Consultation : 2026-07-25.

Collecte vérifiée sur texte primaire : TVA et taxe de consommation (équivalent accises), sur le Code Général des Impôts (version officielle janvier 2023, Loi n°2019-018 du 29 avril 2019).

## Ce qui a été vérifié sur texte primaire

- **TVA taux standard 16%** — Article 230 (LFI.2022).
- **TVA taux zéro** — exportations de biens et services (Art. 230-2).
- **Taxe de consommation** (Livre 2, Titre 2, Chapitre 1, Art. 258-265) — barème complet de 10 catégories de produits, taux mixtes ad valorem et spécifiques :
  - Produits pétroliers (8 sous-catégories, taux spécifiques en Ouguiya/litre ou /kg)
  - Alcools : bière 195%, vins ordinaires 209%, mousseux/champagne 229%, spiritueux 294%
  - Tabac 29%
  - Eaux minérales importées 80%
  - Produits laitiers : lait UHT 10%, yoghourt/autres 60% (codes SH 04.01, 04.03.10, 04.03.90)
  - Fer à béton 1500 MRU/tonne (codes SH 72.14.20.00.10/90)
  - Ciment 300 MRU/tonne (codes SH 25.23.10/90)
  - Emballages plastiques 30%
  - Cartes de recharge téléphonique 30% valeur en douane (code SH 49.11.99.91.00)
  - Téléphones portables importés 100 MRU/unité (code SH 85.17.12.00.00)

## Correction d'une affirmation non vérifiée

Une source secondaire (societegenerale.fr) affirme un taux TVA de 18% pour les produits pétroliers et la téléphonie, ainsi qu'un taux de 14% pour les opérations financières (TOF). **Aucune de ces affirmations n'a été retrouvée dans le texte primaire** (Article 230 ne mentionne que le taux normal 16% et le taux zéro export). La Taxe sur les Opérations Financières existe bien dans le CGI (Art. Livre 2, Titre 2, Chapitre 3) mais c'est une taxe distincte de la TVA, non collectée dans ce cycle. Conformément à la règle de sincérité, ces taux non vérifiés sur texte primaire ne sont **pas** inclus dans `vat_measures.json`.

## Ce qui n'a PAS été collecté

- **Taxe sur les Opérations Financières (TOF)** — Art. Livre 2, Titre 2, Chapitre 3 : non archivée.
- **Taxe spéciale sur les assurances** — Chapitre 4 : non archivée.
- **Taxe de circulation sur les viandes** — Chapitre 2 : non archivée.
- **Dates d'entrée en vigueur précises par ligne** de la taxe de consommation : Article 263 est marqué "(LFI2020, LFR2020)" — deux lois différentes (Loi n°2020-001 du 10 janvier 2020, Loi n°2020-006 du 4 juin 2020) ; la date retenue (2020-01-10) est celle de la LFI2020, sans confirmation ligne-par-ligne de quelles lignes viennent de la loi rectificative.
- **Tarif Extérieur Commun (TEC) UEMOA/CEDEAO** : la Mauritanie n'est ni membre UEMOA ni CEDEAO — régime tarifaire propre, non archivé dans ce cycle.

## État de l'enregistrement

Juridiction MRT : **non** enregistrée dans `SUPPORTED_JURISDICTIONS` — TVA et taxe de consommation vérifiées, mais TOF/assurances/viandes et dates précises par ligne manquants pour une couche complète. ZLECAf : **pas** d'offre nationale encore enregistrée dans `NATIONAL_OFFER_REGISTRY`.
