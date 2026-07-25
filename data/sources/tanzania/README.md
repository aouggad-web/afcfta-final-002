# Tanzanie — collecte (TVA + accises partielles)

Consultation : 2026-07-25 (Africa/Algiers).

**Correction de collecte.** Une première passe sur cette branche avait enregistré `data/tanzania/vat_measures.json` avec un statut `PENDING_OFFICIAL_CONSOLIDATION`, un SHA-256 `pending_collection` et une référence légale incorrecte (« Value Added Tax Act 2021, Act No. 8 of 2021 »). Le texte primaire réellement consulté est la **Value Added Tax Act, 2014 (Act No. 5 of 2014)**, entrée en vigueur le 1er juillet 2015 — le taux de 18% était juste, mais la référence légale et le statut de vérification ne l'étaient pas. Ce cycle remplace ces données par une collecte vérifiée sur texte primaire, archivée et hachée, et ajoute les accises.

## Ce qui a été vérifié sur texte primaire

**TVA** — Value Added Tax Act, 2014 (Act No. 5 of 2014), consolidée au 30 novembre 2019 par TanzLII/Laws.Africa :
- **Taux standard 18%** — Section 5(1) : « the value added tax rate, which shall be eighteen percent ».
- **Taux zéro** — Section 5(2) (mécanisme) et Section 55 (exportations).

**Accises** — The Excise (Management and Tariff) Act, Cap. 147 (R.E. 2019), téléchargée directement depuis le portail du Ministère des Finances et de la Planification (`mof.go.tz`, source primaire gouvernementale) :
- Imposition de l'accise : Section 124(1).
- Sixième colonne (Fourth Schedule) : 6 lignes représentatives transcrites (cheveux humains bruts, jus de fruits/légumes, eaux minérales/gazeuses), avec codes SH.

## Ce qui n'a PAS été vérifié — et pourquoi

- **Fourth Schedule non exhaustif** : le barème couvre des dizaines de positions SH (tabac, boissons alcoolisées, carburants, véhicules, télécommunications…) ; seules 6 lignes ont été transcrites ce cycle. Les autres positions ne sont pas enregistrées, pas devinées.
- **Amendements 2020-2024** : TanzLII signale des amendements en attente d'application sur cette consolidation Cap.147 R.E. 2019 (Act 8/2020, 3/2021, 5/2022, 9/2022, 7/2023, 3/2023, 6/2024) — les taux ci-dessus peuvent avoir été modifiés depuis.
- **Finance Act 2026** et **Customs Tariff Guide 2026 (TRA)** : URLs localisées lors d'une passe antérieure, non re-téléchargées ni re-vérifiées ce cycle — restent `source_pending_collection`.
- **TEC EAC** : déjà archivé pour le Kenya (`data/sources/kenya/official/`) mais pas relié ici sans vérification que le texte s'applique identiquement à la Tanzanie dans cette collecte.

## État de l'enregistrement

Juridiction TZA : **non** enregistrée dans `SUPPORTED_JURISDICTIONS` — collecte TVA + accises partielle, pas de Finance Act, pas de TEC, accises non exhaustives. ZLECAf : **pas** d'offre nationale encore enregistrée dans `NATIONAL_OFFER_REGISTRY`.
