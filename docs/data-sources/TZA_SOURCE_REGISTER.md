# Tanzanie — registre des sources fiscales et ZLECAf

Date de consultation : 2026-07-25. Registre machine-readable :
`data/tanzania/legal_sources.json`. Archives : `data/sources/tanzania/`.

## Sources localisées

| ID | Titre | Institution | Accessibilité | Statut |
|---|---|---|---|---|
| `TZA-TANZLII-VAT-ACT-20260725` | Value Added Tax Act 2021 | TanzLII | HTTP 200 | `source_pending_collection` |
| `TZA-TANZLII-EXCISE-ACT-20260725` | Excise Duty Act 2015 | TanzLII | HTTP 200 | `source_pending_collection` |
| `TZA-TANZLII-FINANCE-ACT-2026` | Finance Act 2026 | TanzLII | HTTP 200 | `source_pending_collection` |
| `TZA-TRA-TARIFF-GUIDE-2026` | Customs Tariff Guide 2026 | Tanzania Revenue Authority | à vérifier | `source_pending_collection` |

## Faits vérifiés

- **TVA standard** : 18%, Value Added Tax Act 2021 (Act No. 8 of 2021),
  effectif 1er juillet 2021. Aucun changement de taux signalé depuis.
- **Accises** : Excise Duty Act 2015 ; texte consolidé via TanzLII.
- **Prélèvements** : Finance Act 2026 enactée 2026-06-30 (année fiscale 2026/27).
- **Accessibilité** : Les trois actes majeurs confirment publication consolidée
  par TanzLII, du même écosystème AfricanLII que le Kenya.

## Ce qui reste `PENDING`

- **Archives HTML** : Textes des trois actes (VAT, Excise, Finance) non
  téléchargés ni archivés. SHA-256 calculs à la collection.
- **Tariff Guide** : Vérification d'accessibilité et format auprès de TRA
  (Tanzania Revenue Authority).
- **Accises & prélèvements par HS** : Pas encore extrait ligne à ligne.
- **ZLECAf (niveau 2)** : Localisation de l'offre nationale tanzanienne
  auprès de l'EAC Secretariat (calendar/HS10 concessions) : non entrepris.

## Règles de preuve

Mêmes règles que le Kenya (`docs/data-sources/KEN_SOURCE_REGISTER.md`) et
l'Afrique du Sud (`docs/data-sources/ZAF_SOURCE_REGISTER.md`) : aucun taux
sans texte officiel daté et vérifiable via consolidation publique (TanzLII,
TRA). Une source de niveau « guide administratif » est signalée comme telle
et ne prévaut jamais sur un texte consolidé.

## État de l'enregistrement

Juridiction TZA : **non** enregistrée dans `SUPPORTED_JURISDICTIONS`
(`backend/services/national_legal_calculation_service.py`) — couche fiscale
partielle (TVA seule, pas d'accises/prélèvements/formalities). Pas d'offre
ZLECAf nationale enregistrée dans `NATIONAL_OFFER_REGISTRY` — une
classification pour TZA serait servie par le canevas générique (`AFCFTA_CANVAS_HS2`),
jamais fabriquée.
