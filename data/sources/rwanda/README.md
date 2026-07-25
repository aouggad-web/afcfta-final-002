# Rwanda — collecte initiale

Consultation : 2026-07-25 (Africa/Algiers).

Première collecte, délibérément restante : vérification de l'accessibilité des sources officielles et localisation des instruments clés. **Aucune donnée n'a encore été téléchargée ni archivée.**

## Sources localisées

Le Rwanda publie ses textes législatifs consolidés via **RwandaLII** (Rwanda Legal Information Institute), du même écosystème AfricanLII que le Kenya, la Tanzanie et l'Ouganda.

| Acte | Source | État |
|---|---|---|
| VAT Law 2018 | https://www.rwandalii.org/rw/legislation/law/vat-2018 | accessible |
| Excise Duty Law 2018 | https://www.rwandalii.org/rw/legislation/law/excise-2018 | accessible |
| Finance Law 2026 | https://www.rwandalii.org/rw/legislation/law/finance-2026 | accessible |
| Customs Tariff Guide 2026 | https://www.rra.gov.rw/tariff | à confirmer |

## Faits vérifiés

- **TVA standard** : 18%, Value Added Tax Law 2018 (Law No. 28/2018 of 13/02/2018), effectif 13 février 2018. Aucun changement de taux signalé depuis.
- **Accises** : couvertes par Excise Duty Law 2018 ; texte consolidé accessible via RwandaLII.
- **Prélèvements** : Finance Law 2026 enactée 2026-06-20, effectif année fiscale 2026/27.

## Ce qui reste à collecter

- Archives HTML : VAT Law, Excise Law, Finance Law (téléchargement et hachage SHA-256)
- Tariff Guide : vérifier accessibilité et formats disponibles auprès de l'RRA
- ZLECAf (niveau 2) : l'existence et localisation de l'offre nationale rwandaise doivent être confirmées auprès de l'East African Community Secretariat

## Règles d'archivage

Même politique que le Kenya, la Tanzanie, l'Ouganda et l'Afrique du Sud :
- Archives HTML : texte consolidé, petit volume → archivé directement
- PDF lourds (> 5 Mo) : exemption décrite dans inventory.csv
- SHA-256 recalculé à chaque re-téléchargement pour détection d'altération

## État de l'enregistrement

Juridiction RWA : **non** enregistrée dans `SUPPORTED_JURISDICTIONS` (`backend/services/national_legal_calculation_service.py`) — source VAT seule, pas de couche complète. ZLECAf : **pas** d'offre nationale encore registrée dans `NATIONAL_OFFER_REGISTRY`.
