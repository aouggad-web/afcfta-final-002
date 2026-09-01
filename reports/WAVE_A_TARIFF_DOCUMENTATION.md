# Documentation tarifaire — Vague A (2026-07-24)

> Synthèse locale en lecture seule. Aucune nouvelle source ni aucun taux n'a été collecté ou modifié.

| Pays | Fichier utilisé | Lignes | SH6 | Taux renseignés | Taux manquants | Version SH | Date effet | Archive officielle | Source | Statut | Simulables | Indisponibles | Conflits |
|---|---|---:|---:|---:|---:|---|---|---|---|---|---:|---:|---:|
| DZA | backend/data/crawled/DZA_tariffs.json | 17061 | 5515 | 16825 | 236 | HS2022 | None | False | conformepro.dz (données douane.gov.dz) | INFORMATIVE_PARTIAL | 139 | 0 | 16922 |
| MAR | backend/data/crawled/MAR_tariffs.json | 13114 | 5610 | 12972 | 142 | None | None | False | douane.gov.ma/adil | INFORMATIVE_PARTIAL | 0 | 0 | 13114 |
| TUN | backend/data/crawled/TUN_tariffs.json | 17512 | 5611 | 17512 | 0 | None | None | False | douane.gov.tn/tarifweb2025 | INFORMATIVE_PARTIAL | 12 | 0 | 17500 |
| EGY | backend/data/crawled/EGY_tariffs.json | 8746 | 5541 | 8746 | 0 | None | None | False | Egyptian Customs Authority (customs.gov.eg/Services/Tarif) | INFORMATIVE_PARTIAL | 38 | 0 | 8708 |
| ZAF | backend/data/crawled/ZAF_tariffs.json | 8589 | 5619 | 8588 | 1 | None | None | False | sars.gov.za | INFORMATIVE_PARTIAL | 4328 | 1 | 4260 |
| KEN | backend/data/crawled/KEN_tariffs.json | 5984 | 5604 | 5893 | 91 | HS 2022 | None | False | EAC Common External Tariff 2022 | INFORMATIVE_PARTIAL | 0 | 0 | 5984 |

## DZA — réconciliation

Les catégories peuvent se chevaucher; le runtime privilégie crawled pour les positions nationales, sans arbitrer les divergences.

- IDENTICAL : **139**
- ONLY_CANONICAL : **54**
- ONLY_CRAWLED : **0**
- RATE_DIFFERENCE : **15731**
- DESCRIPTION_DIFFERENCE : **16744**
- NATIONAL_CODE_DIFFERENCE : **0**
- MISSING_RATE_CANONICAL : **11**
- MISSING_RATE_CRAWLED : **236**

## Règles

Une position sans DD analysable est CALCULATION_UNAVAILABLE. Une divergence entre fichiers est REVIEW_REQUIRED. Aucune cause de DD manquant n'est convertie en taux.
