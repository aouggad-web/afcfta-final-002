# Couverture des statistiques nationales, par pays

**Rapport GÉNÉRÉ** par `backend/scripts/report_national_stats_coverage.py`.
Ne pas éditer à la main — regénérer.

Dernière génération : 2026-09-21.

## Ce que le palier veut dire

La statistique d'un office national nous parvient de trois façons, de coût
croissant. Le palier dit **où porter l'effort**, jamais la qualité de l'office.

| Palier | Sens | Pays |
|---|---|---:|
| **A** | Collecte directe — un bloc adossé à une publication nommée et datée, dans `data/national_stats/` | 2 |
| **B** | Republiée harmonisée — l'enquête de l'office nous parvient via ILOSTAT ou l'UNSD, sans rien négocier | 46 |
| **C** | Non atteinte — ni republiée, ni collectée | 6 |

## Pourquoi le palier B ne suffit pas

Les republications harmonisées portent l'emploi et l'activité. Elles ne
portent **pas** la séparation entre exportations domestiques et
réexportations — que seul l'office national publie, et qui commande les
règles d'origine ZLECAf : une marchandise réexportée depuis une zone franche
n'acquiert pas l'origine locale.

Un pays en palier B est donc couvert pour l'emploi, et découvert pour
l'origine. C'est vers cette distinction que la collecte directe doit aller en
priorité, et vers les pays à zones franches actives d'abord.

## Détail

| ISO3 | Pays | Palier | Collecte directe | ILOSTAT (enquêtes emploi) | UNSD 9.2 (emploi manuf.) |
|---|---|:---:|:---:|:---:|:---:|
| AGO | Angola | B | — | oui | oui |
| BDI | Burundi | B | — | oui | oui |
| BEN | Bénin | B | — | oui | oui |
| BFA | Burkina Faso | B | — | oui | oui |
| BWA | Botswana | B | — | oui | oui |
| CAF | République centrafricaine | C | — | — | — |
| CIV | Côte d'Ivoire | B | — | oui | oui |
| CMR | Cameroun | B | — | oui | oui |
| COD | RD Congo | B | — | oui | oui |
| COG | Congo | C | — | — | — |
| COM | Comores | B | — | oui | oui |
| CPV | Cap-Vert | B | — | oui | oui |
| DJI | Djibouti | B | — | oui | oui |
| DZA | Algérie | B | — | oui | oui |
| EGY | Égypte | B | — | oui | oui |
| ERI | Érythrée | C | — | — | — |
| ETH | Éthiopie | B | — | oui | oui |
| GAB | Gabon | B | — | oui | — |
| GHA | Ghana | B | — | oui | oui |
| GIN | Guinée | C | — | — | — |
| GMB | Gambie | B | — | oui | oui |
| GNB | Guinée-Bissau | B | — | oui | oui |
| GNQ | Guinée équatoriale | B | — | oui | — |
| KEN | Kenya | B | — | oui | oui |
| LBR | Libéria | B | — | oui | oui |
| LBY | Libye | C | — | — | — |
| LSO | Lesotho | B | — | oui | oui |
| MAR | Maroc | B | — | oui | oui |
| MDG | Madagascar | B | — | oui | oui |
| MLI | Mali | B | — | oui | oui |
| MOZ | Mozambique | B | — | oui | oui |
| MRT | Mauritanie | B | — | oui | oui |
| MUS | Maurice | A | oui | oui | oui |
| MWI | Malawi | B | — | oui | oui |
| NAM | Namibie | B | — | oui | oui |
| NER | Niger | B | — | oui | oui |
| NGA | Nigéria | B | — | oui | oui |
| RWA | Rwanda | B | — | oui | oui |
| SDN | Soudan | B | — | oui | — |
| SEN | Sénégal | B | — | oui | oui |
| SLE | Sierra Leone | B | — | oui | oui |
| SOM | Somalie | B | — | oui | oui |
| SSD | Soudan du Sud | C | — | — | — |
| STP | Sao Tomé-et-Príncipe | B | — | oui | — |
| SWZ | Eswatini | B | — | oui | oui |
| SYC | Seychelles | B | — | oui | oui |
| TCD | Tchad | B | — | oui | oui |
| TGO | Togo | A | oui | oui | oui |
| TUN | Tunisie | B | — | oui | oui |
| TZA | Tanzanie | B | — | oui | oui |
| UGA | Ouganda | B | — | oui | oui |
| ZAF | Afrique du Sud | B | — | oui | oui |
| ZMB | Zambie | B | — | oui | oui |
| ZWE | Zimbabwe | B | — | oui | oui |

## Regénérer

```bash
python3 backend/scripts/report_national_stats_coverage.py
```
