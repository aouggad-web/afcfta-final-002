# Afrique du Sud — registre des sources fiscales et ZLECAf

Date de consultation : 2026-07-25. Registre machine-readable :
`data/south_africa/legal_sources.json`. Archives : `data/sources/south_africa/`.

## Sources

| ID | Titre | Institution | Statut | SHA-256 |
|---|---|---|---|---|
| `ZAF-SARS-VAT-GUIDE-20260725` | Value-Added Tax (guide) | SARS | COLLECTED_ADMINISTRATIVE_GUIDE | `55642c16ad323d72418354b0c16614a6ad16e6da01b982b8c77a28114f9d1f7e` |
| `ZAF-SARS-SCHEDULES-INDEX-20260725` | Schedules to the Customs and Excise Act 1964 (index) | SARS | COLLECTED_INDEX | `4ce515034f6263c387bd16078c15574e8da3ec57098d167e88ad84caa1271f71` |
| `ZAF-SARS-SCH10-PART8-AFCFTA-20201231` | Agreement Establishing the AfCFTA (Schedule No. 10 Part 8) | SARS / National Treasury | COLLECTED_EXCERPT | `8b27435187a9429eb136fb21370095de34726e06c7904dd9fbe90220922fa570` |
| `ZAF-SARS-SCH1P1-AFCFTA-COLUMN` | Schedule No. 1 Part 1 — barème douanier complet, colonne ZLECAf | SARS | **SOURCE_PENDING_COLLECTION** | — |

## Faits vérifiés

- **TVA standard** : 15%, Value-Added Tax Act 1991 (Act 89 of 1991). Rate
  confirmée courante par les annonces SARS du 12, 25 et 27 avril 2025
  (annulation d'une hausse à 15.5%/16% initialement prévue).
- **ZLECAf, base légale** : Government Notice R. 1433, Government Gazette
  44049 du 31 décembre 2020, effectif 1er janvier 2021 — insère l'Accord
  ZLECAf comme Schedule No. 10 Part 8 du Customs and Excise Act 1964.

## Ce qui reste `PENDING`

Le barème de concessions ligne à ligne (« colonne AfCFTA » de Schedule
No. 1 Part 1, chapitres 1-99, mis à jour au 24 juillet 2026 selon l'index
SARS) est localisé et confirmé publiquement accessible, mais **non
téléchargé ni extrait**. C'est l'intégralité du tarif douanier national ;
son extraction ligne à ligne fiable constitue un chantier de collecte
distinct, non entrepris dans cette itération. Tant que ce barème n'est pas
ingéré, l'Afrique du Sud n'est pas enregistrée comme offre nationale
ZLECAf (`NATIONAL_OFFER_REGISTRY`, `backend/etl/afcfta_national_offers.py`) —
une classification y serait actuellement servie par le canevas générique
(`AFCFTA_CANVAS_HS2`), jamais fabriquée.

Accises, droits antidumping/sauvegarde, ristournes, formalités
administratives : non collectés. L'Afrique du Sud n'est donc pas non plus
enregistrée dans `SUPPORTED_JURISDICTIONS`
(`backend/services/national_legal_calculation_service.py`) — une couche
partielle (TVA seule) donnerait une fausse impression de calcul
entièrement vérifié.

## Règles de preuve

Mêmes règles que le Kenya (`docs/data-sources/KEN_SOURCE_REGISTER.md`) :
aucun taux sans texte officiel daté et vérifiable ; une source de niveau
« guide administratif » est signalée comme telle et ne prévaut jamais sur
un texte consolidé s'il devient disponible.
