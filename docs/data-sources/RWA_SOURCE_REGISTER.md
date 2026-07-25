# Rwanda — registre des sources fiscales et ZLECAf

Date de consultation : 2026-07-25. Registre machine-readable :
`data/rwanda/legal_sources.json`. Archives : `data/sources/rwanda/`.

## Sources localisées

| ID | Titre | Institution | Accessibilité | Statut |
|---|---|---|---|---|
| `RWA-RWANDALII-VAT-ACT-20260725` | Value Added Tax Law 2018 | RwandaLII | HTTP 200 | `source_pending_collection` |
| `RWA-RWANDALII-EXCISE-ACT-20260725` | Excise Duty Law 2018 | RwandaLII | HTTP 200 | `source_pending_collection` |
| `RWA-RWANDALII-FINANCE-LAW-2026` | Finance Law 2026 | RwandaLII | HTTP 200 | `source_pending_collection` |
| `RWA-RRA-TARIFF-GUIDE-2026` | Customs Tariff Guide 2026 | Rwanda Revenue Authority | à vérifier | `source_pending_collection` |

## Faits vérifiés

- **TVA standard** : 18%, Value Added Tax Law 2018 (Law No. 28/2018 of
  13/02/2018), effectif 13 février 2018. Aucun changement de taux signalé depuis.
- **Accises** : Excise Duty Law 2018 ; texte consolidé via RwandaLII.
- **Prélèvements** : Finance Law 2026 enactée 2026-06-20 (année fiscale 2026/27).
- **Accessibilité** : Les trois actes majeurs confirment publication consolidée
  par RwandaLII, du même écosystème AfricanLII que le Kenya, la Tanzanie et
  l'Ouganda.

## Ce qui reste `PENDING`

- **Archives HTML** : Textes des trois actes (VAT, Excise, Finance) non
  téléchargés ni archivés. SHA-256 calculs à la collection.
- **Tariff Guide** : Vérification d'accessibilité et format auprès de l'RRA
  (Rwanda Revenue Authority).
- **Accises & prélèvements par HS** : Pas encore extrait ligne à ligne.
- **ZLECAf (niveau 2)** : Localisation de l'offre nationale rwandaise
  auprès de l'EAC Secretariat (calendar/HS10 concessions) : non entrepris.

## Règles de preuve

Mêmes règles que le Kenya (`docs/data-sources/KEN_SOURCE_REGISTER.md`),
la Tanzanie (`docs/data-sources/TZA_SOURCE_REGISTER.md`), l'Ouganda
(`docs/data-sources/UGA_SOURCE_REGISTER.md`) et l'Afrique du Sud
(`docs/data-sources/ZAF_SOURCE_REGISTER.md`) : aucun taux sans texte officiel
daté et vérifiable via consolidation publique (RwandaLII, RRA). Une source de
niveau « guide administratif » est signalée comme telle et ne prévaut jamais
sur un texte consolidé.

## État de l'enregistrement

Juridiction RWA : **non** enregistrée dans `SUPPORTED_JURISDICTIONS`
(`backend/services/national_legal_calculation_service.py`) — couche fiscale
partielle (TVA seule, pas d'accises/prélèvements/formalities). Pas d'offre
ZLECAf nationale enregistrée dans `NATIONAL_OFFER_REGISTRY` — une
classification pour RWA serait servie par le canevas générique (`AFCFTA_CANVAS_HS2`),
jamais fabriquée.
