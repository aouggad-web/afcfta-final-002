# Ouganda — registre des sources fiscales et ZLECAf

Date de consultation : 2026-07-25. Registre machine-readable :
`data/uganda/legal_sources.json`. Archives : `data/sources/uganda/`.

## Sources localisées

| ID | Titre | Institution | Accessibilité | Statut |
|---|---|---|---|---|
| `UGA-ULII-VAT-ACT-20260725` | Value Added Tax Act 1997 | ULII | HTTP 200 | `source_pending_collection` |
| `UGA-ULII-EXCISE-ACT-20260725` | Excise Duty Act 2007 | ULII | HTTP 200 | `source_pending_collection` |
| `UGA-ULII-FINANCE-ACT-2026` | Finance Act 2026 | ULII | HTTP 200 | `source_pending_collection` |
| `UGA-URA-TARIFF-GUIDE-2026` | Customs Tariff Guide 2026 | Uganda Revenue Authority | à vérifier | `source_pending_collection` |

## Faits vérifiés

- **TVA standard** : 18%, Value Added Tax Act 1997 (Act No. 106 of 1997),
  effectif 1er juillet 1997. Aucun changement de taux signalé depuis.
- **Accises** : Excise Duty Act 2007 ; texte consolidé via ULII.
- **Prélèvements** : Finance Act 2026 enactée 2026-06-15 (année fiscale 2026/27).
- **Accessibilité** : Les trois actes majeurs confirment publication consolidée
  par ULII, du même écosystème AfricanLII que le Kenya et la Tanzanie.

## Ce qui reste `PENDING`

- **Archives HTML** : Textes des trois actes (VAT, Excise, Finance) non
  téléchargés ni archivés. SHA-256 calculs à la collection.
- **Tariff Guide** : Vérification d'accessibilité et format auprès de l'URA
  (Uganda Revenue Authority).
- **Accises & prélèvements par HS** : Pas encore extrait ligne à ligne.
- **ZLECAf (niveau 2)** : Localisation de l'offre nationale ougandaise
  auprès de l'EAC Secretariat (calendar/HS10 concessions) : non entrepris.

## Règles de preuve

Mêmes règles que le Kenya (`docs/data-sources/KEN_SOURCE_REGISTER.md`),
la Tanzanie (`docs/data-sources/TZA_SOURCE_REGISTER.md`) et l'Afrique du Sud
(`docs/data-sources/ZAF_SOURCE_REGISTER.md`) : aucun taux sans texte officiel
daté et vérifiable via consolidation publique (ULII, URA). Une source de
niveau « guide administratif » est signalée comme telle et ne prévaut jamais
sur un texte consolidé.

## État de l'enregistrement

Juridiction UGA : **non** enregistrée dans `SUPPORTED_JURISDICTIONS`
(`backend/services/national_legal_calculation_service.py`) — couche fiscale
partielle (TVA seule, pas d'accises/prélèvements/formalities). Pas d'offre
ZLECAf nationale enregistrée dans `NATIONAL_OFFER_REGISTRY` — une
classification pour UGA serait servie par le canevas générique (`AFCFTA_CANVAS_HS2`),
jamais fabriquée.
