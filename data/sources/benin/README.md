# Bénin — collecte initiale UEMOA

Consultation : 2026-07-25 (Africa/Algiers).

Première collecte, délibérément restante : vérification de l'accessibilité des sources officielles. **Aucune donnée n'a encore été téléchargée ni archivée.**

## Sources localisées

Le Bénin publie son Code Général des Impôts et les lois de finances via JUTAB (Journal Officiel de la République du Bénin).

| Acte | Source | État |
|---|---|---|
| Code Général des Impôts | https://www.jutab.gouv.bj/ | à confirmer |
| Loi de Finances 2026 | https://www.jutab.gouv.bj/decrets-lois | à confirmer |
| Tariff Guide 2026 | https://www.douanes.gouv.bj/tarif | à confirmer |

## Faits vérifiés

- **TVA standard** : 18%, Code Général des Impôts, effectif 9 décembre 1992.
  Harmonisation UEMOA : taux commun à tous les États membres (18%).
  Aucun changement de taux signalé depuis.

## Ce qui reste à collecter

- Archives HTML : Code Général, Loi de Finances 2026 (téléchargement et hachage SHA-256)
- Tariff Guide : vérifier accessibilité auprès de la Direction des Douanes
- Prélèvements spéciaux : PCS, PCC, RS, TSI (Douanes, Finance Act)
- ZLECAf (niveau 2) : localisation de l'offre nationale béninoise

## Règles d'archivage

Même politique que Kenya, EAC trio, Afrique du Sud, Sénégal :
- Archives HTML : texte consolidé, petit volume → archivé directement
- PDF lourds : exemption décrite dans inventory.csv
- SHA-256 recalculé à chaque re-téléchargement

## État de l'enregistrement

Juridiction BEN : **non** enregistrée dans `SUPPORTED_JURISDICTIONS` — source VAT seule, pas de couche complète (pas d'accises/prélèvements/formalities ingérées). ZLECAf : **pas** d'offre nationale enregistrée.
