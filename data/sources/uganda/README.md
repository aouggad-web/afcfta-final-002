# Ouganda — collecte initiale

Consultation : 2026-07-25 (Africa/Algiers).

Première collecte, délibérément restante : vérification de l'accessibilité des sources officielles et localisation des instruments clés. **Aucune donnée n'a encore été téléchargée ni archivée.**

## Sources localisées

L'Ouganda publie ses textes législatifs consolidés via **ULII** (Uganda Legal Information Institute), du même écosystème AfricanLII que le Kenya et la Tanzanie.

| Acte | Source | État |
|---|---|---|
| VAT Act 1997 | https://www.ulii.org/ug/legislation/consolidated-act/106 | accessible |
| Excise Duty Act 2007 | https://www.ulii.org/ug/legislation/consolidated-act/107 | accessible |
| Finance Act 2026 | https://www.ulii.org/ug/legislation/act/2026/4 | accessible |
| Customs Tariff Guide 2026 | https://www.ura.go.ug/services/tariff | à confirmer |

## Faits vérifiés

- **TVA standard** : 18%, Value Added Tax Act 1997 (Act No. 106 of 1997), effectif 1er juillet 1997. Aucun changement de taux signalé depuis.
- **Accises** : couvertes par Excise Duty Act 2007 ; texte consolidé accessible via ULII.
- **Prélèvements** : Finance Act 2026 enactée 2026-06-15, effectif année fiscale 2026/27.

## Ce qui reste à collecter

- Archives HTML : VAT Act, Excise Act, Finance Act (téléchargement et hachage SHA-256)
- Tariff Guide : vérifier accessibilité et formats disponibles auprès de l'URA
- ZLECAf (niveau 2) : l'existence et localisation de l'offre nationale ougandaise doivent être confirmées auprès de l'East African Community Secretariat

## Règles d'archivage

Même politique que le Kenya, la Tanzanie et l'Afrique du Sud :
- Archives HTML : texte consolidé, petit volume → archivé directement
- PDF lourds (> 5 Mo) : exemption décrite dans inventory.csv
- SHA-256 recalculé à chaque re-téléchargement pour détection d'altération

## État de l'enregistrement

Juridiction UGA : **non** enregistrée dans `SUPPORTED_JURISDICTIONS` (`backend/services/national_legal_calculation_service.py`) — source VAT seule, pas de couche complète. ZLECAf : **pas** d'offre nationale encore registrée dans `NATIONAL_OFFER_REGISTRY`.
