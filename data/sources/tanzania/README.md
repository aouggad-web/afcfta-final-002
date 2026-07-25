# Tanzanie — collecte initiale

Consultation : 2026-07-25 (Africa/Algiers).

Première collecte, délibérément restante : vérification de l'accessibilité des sources officielles et localisation des instruments clés. **Aucune donnée n'a encore été téléchargée ni archivée.**

## Sources localisées

La Tanzanie publie ses textes législatifs consolidés via **TanzLII** (Tanzania Legal Information Institute), du même écosystème AfricanLII que le Kenya et l'Afrique du Sud.

| Acte | Source | État |
|---|---|---|
| VAT Act 2021 | https://www.tanzlii.org/akn/tz/act/2021/8 | accessible |
| Excise Duty Act 2015 | https://www.tanzlii.org/akn/tz/act/2015/8 | accessible |
| Finance Act 2026 | https://www.tanzlii.org/akn/tz/act/2026/finance | accessible |
| Customs Tariff Guide 2026 | https://www.tra.go.tz/en/tariff-guide | à confirmer |

## Faits vérifiés

- **TVA standard** : 18%, Value Added Tax Act 2021 (Act No. 8 of 2021), effectif 1er juillet 2021. Aucun changement de taux signalé depuis.
- **Accises** : couvertes par Excise Duty Act 2015 ; texte consolidé accessible via TanzLII.
- **Prélèvements** : Finance Act 2026 enactée 2026-06-30, effectif année fiscale 2026/27.

## Ce qui reste à collecter

- Archives HTML : VAT Act, Excise Act, Finance Act (téléchargement et hachage SHA-256)
- Tariff Guide : vérifier accessibilité et formats disponibles auprès de TRA
- ZLECAf (niveau 2) : l'existence et localisation de l'offre nationale tanzanienne doivent être confirmées auprès de l'East African Community Secretariat

## Règles d'archivage

Même politique que le Kenya et l'Afrique du Sud :
- Archives HTML : texte consolidé, petit volume → archivé directement
- PDF lourds (> 5 Mo) : exemption décrite dans inventory.csv
- SHA-256 recalculé à chaque re-téléchargement pour détection d'altération

## État de l'enregistrement

Juridiction TZA : **non** enregistrée dans `SUPPORTED_JURISDICTIONS` (`backend/services/national_legal_calculation_service.py`) — source VAT seule, pas de couche complète. ZLECAf : **pas** d'offre nationale encore registrée dans `NATIONAL_OFFER_REGISTRY`.
