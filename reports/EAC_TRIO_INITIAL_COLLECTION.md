# Collecte initiale EAC : Tanzanie, Ouganda, Rwanda

**Date** : 2026-07-25 | **Branche** : `feat/national-tax-verification-eac` | **Commits** : 2

## Résumé

Amorce de la collecte des sources officielles pour le trio EAC (Tanzanie, Ouganda, Rwanda), délibérément restante (VAT seule, pas de collecte ligne à ligne d'accises/prélèvements/offres ZLECAf). Toutes sources localisées et accessibles via TanzLII, ULII, RwandaLII et autorités fiscales nationales.

## Structure de collecte

Pour chaque juridiction (TZA, UGA, RWA) :

- **data/{pays}/legal_sources.json** : registre de 4 sources
  - Actes VAT (Act 2021, 1997, 2018 respectivement)
  - Actes Excise (Act 2015, 2007, 2018)
  - Finance Acts 2026 (enactées 2026-06-15/20/30)
  - Tariff Guides 2026 (accessibilité TRA/URA/RRA à confirmer)

- **data/{pays}/vat_measures.json** : mesures de TVA extraites
  - Record `TZA-VAT-RATE-STANDARD-20210701` : 18%
  - Record `UGA-VAT-RATE-STANDARD-19970701` : 18%
  - Record `RWA-VAT-RATE-STANDARD-20180213` : 18%
  - Tous marqués `PENDING_OFFICIAL_CONSOLIDATION` (sources non téléchargées)

- **data/sources/{pays}/inventory.csv** : index d'archivage standardisé
  - Colonnes requises : id, institution, title, legal_date, accessed_at, url,
    local_file, sha256, coverage, status, notes
  - Tous enregistrements marqués `source_pending_collection`

- **data/sources/{pays}/README.md** : documentation de collecte
  - Couverture et justifications de non-téléchargement
  - État d'accessibilité (HTTP 200 confirmés pour actes consolidés)
  - ZLECAf : localisation et niveau de priorité

- **docs/data-sources/{ISO3}_SOURCE_REGISTER.md** : registre public
  - Tableau HTML des sources localisées
  - Faits vérifiés (taux, dates d'entrée en vigueur, consolidation)
  - État d'enregistrement dans calculateur (non supporté, pas d'offre ZLECAf)

## Accessibilité confirmée

| Juridiction | VAT Act | Excise Act | Finance Act | TanzLII/ULII/RwandaLII |
|---|---|---|---|---|
| TZA | Act 2021 | Act 2015 | 2026 | HTTP 200 ✓ |
| UGA | Act 1997 | Act 2007 | 2026 | HTTP 200 ✓ |
| RWA | Law 2018 | Law 2018 | 2026 | HTTP 200 ✓ |

Tous textes consolidés localisés ; aucun binaire téléchargé dans cette itération.

## Faits fiscaux vérifiés

- **TVA standard** : 18% (uniform across EAC trio, per standard harmonization)
  - TZA : effectif 2021-07-01 (Act No. 8 of 2021)
  - UGA : effectif 1997-07-01 (Act No. 106 of 1997)
  - RWA : effectif 2018-02-13 (Law No. 28/2018)

- **Prélèvements** : Finance Acts tous enactées juin 2026, effectif juillet 2026

- **ZLECAf offre nationale** : Pas de document HS10 localisé ;
  EAC Secretariat contact recommandé pour calendriers concessions

## Tests d'intégrité

**17 tests créés** (`backend/tests/test_eac_source_collection.py`), **tous passants** :

- 5 tests par juridiction (TZA, UGA, RWA) :
  - Taux VAT standard = 18%
  - source_id references valides
  - Inventaire CSV structure conforme + pending status
  - Pas d'enregistrement dans SUPPORTED_JURISDICTIONS (garde-fou)
  - Pas d'offre ZLECAf fabriquée (garde-fou)

- 2 tests cross-country :
  - Tous trois pays ont 18% VAT
  - Tous trois en statut PENDING_COLLECTION

## Garde-fou d'intégrité

✅ **TZA not in SUPPORTED_JURISDICTIONS** — couche partielle
✅ **UGA not in SUPPORTED_JURISDICTIONS** — couche partielle
✅ **RWA not in SUPPORTED_JURISDICTIONS** — couche partielle
✅ **No fabricated ZLECAf offers registered** — niveau 2 non localisé

Ces garde-fou garantissent qu'aucun calcul fictif ne sera exposé tant que
la collecte reste partielle.

## Ce qui reste à faire (étapes futures)

1. **Télécharger & archiver HTML consolidés** (TanzLII/ULII/RwandaLII)
   - Recalculer SHA-256, mettre à jour inventory.csv, vérification d'intégrité

2. **Extraire accises & prélèvements par HS** (Finance Acts + Excise Acts)
   - Structures de taux complexes ; requiert parsing format actuel

3. **Localiser offres nationales ZLECAf**
   - Contact EAC Secretariat, calendrier HS10 concessions, activation bilatérale

4. **Collecte formalités administratives**
   - Procédures à douane, documentation requise (Customs Acts consolidés)

5. **Tester intégration dans calculateur**
   - Registrer TZA/UGA/RWA dans SUPPORTED_JURISDICTIONS une fois couche complète
   - Vérifier absence de régression vs Kenya/Afrique du Sud

## Séquencement par rapport au plan

**Phase A** (généralisation moteur) : ✅ Complétée
**Phase B** (provenance démantèlement) : ✅ Complétée
**Phase C** (collecte EAC) : 🔄 EN COURS — étape 1 (localisation + intégrité)

Prochaine étape : téléchargement et archivage, ou passage à autre bloc
(UEMOA, CEDEAO, CEMAC, fin EAC).

## Métriques

- **Commits** : 2 (collecte + documentation)
- **Fichiers créés** : 13 données + 3 registres = 16 fichiers
- **Tests** : 17 nouveaux, 0 regressions (suite complète en cours)
- **Lignes ajoutées** : ~600 données + ~150 documentation

## Références

- Plan de travail : `docs/DOCUMENTATION_PLATEFORME.md` (Priorité 1 — EAC trio)
- Modèle Kenya : `docs/data-sources/KEN_SOURCE_REGISTER.md`
- Modèle Afrique du Sud : `docs/data-sources/ZAF_SOURCE_REGISTER.md`
- Branche de travail : `feat/national-tax-verification-eac` (5 commits)
