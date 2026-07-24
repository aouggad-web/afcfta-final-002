# Kenya — collecte officielle

Consultation : 2026-07-24 (Africa/Algiers).

Ce dossier contient une première collecte reproductible des sources officielles
relatives aux droits et formalités d'importation au Kenya. L'inventaire
machine-readable est dans `inventory.csv`; les fichiers téléchargés sont dans
`official/`.

## Règles de validation

- Aucun taux n'est considéré exploitable sans texte officiel daté et vérifiable.
- Le CET EAC doit être lu avec les mesures dérogatoires et corrigenda publiés
  dans les gazettes EAC postérieures.
- Les pages KRA sont des guides administratifs. Lorsqu'elles contredisent une
  loi consolidée plus récente, la loi prévaut et la page KRA est marquée
  `guide_stale_rate_warning`.
- Les PDF Kenya Law très courts sont des artefacts officiels téléchargés depuis
  l'URL `source.pdf`, mais doivent être complétés par la version HTML consolidée
  avant extraction exhaustive des annexes.

## Couverture initiale

1. CET et droits par position : CET EAC 2022 mis à jour en juin 2025.
2. VAT à l'importation : Value Added Tax Act, version du 1 juillet 2025.
3. Excises : Excise Duty Act, version du 1 juillet 2025.
4. IDF, RDL et autres prélèvements : Miscellaneous Fees and Levies Act,
   version du 1 janvier 2026.
5. Exemptions et régimes spéciaux : EACCMA, VAT Act, Excise Duty Act et
   Miscellaneous Fees and Levies Act.
6. Formalités et documents : guide KRA, EACCMA et National Electronic Single
   Window System Act.
7. Dates d'entrée en vigueur : consignées dans `inventory.csv`; les textes
   modificatifs et gazettes postérieurs au CET restent à inventorier
   exhaustivement avant production d'une table tarifaire opérationnelle.

8. Trésor : index officiel des Budget Statements archivé; les PDF budgétaires
   liés restent à valider individuellement.

## Résultat des tests d'accès

| Source | Résultat avec User-Agent navigateur |
|---|---|
| `https://new.kenyalaw.org/` | HTTP 200 |
| `https://www.kra.go.ke/` | HTTP 200 |
| `https://www.treasury.go.ke/` | HTTP 200 |
| `https://www.eac.int/` | HTTP 200 |

Le serveur EAC a ensuite renvoyé HTTP 403 sur certains liens PDF directs, alors
que le CET public avait été téléchargé avec succès. Aucun contournement n'a été
tenté.
