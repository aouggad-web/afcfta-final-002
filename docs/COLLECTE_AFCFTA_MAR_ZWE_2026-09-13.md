# Collecte AfCFTA — Maroc et Zimbabwe, et l'étape qui manque

Collecte du 13 septembre 2026 depuis l'e-Tariff Book officiel de l'Union
africaine (`https://etariff.au-afcfta.org/`, API
`prod-afcfta-api.azurewebsites.net`).

## Ce qui a été collecté

| Offre | Barèmes | Lignes | Origines mappées | Fichier |
|---|---|---:|---:|---|
| **MAR** | 2 — démantèlement sur 5 ans et sur 10 ans | 14 510 par barème | 48 | `MAR_afcfta_etariff_2026-09-13.json.gz` |
| **ZWE** | 1 | 6 017 | toutes (barème unique) | `ZWE_afcfta_etariff_2026-09-13.json.gz` |

Le Maroc et le Zimbabwe étaient les **deux seules destinations** de l'e-Tariff
Book à publier un barème sans figurer dans les instantanés du dépôt. L'Égypte,
la Tunisie, l'Éthiopie, la Zambie et les trois unions douanières (EAC, CEDEAO,
CEMAC) étaient déjà collectées.

Les deux barèmes marocains sont réellement distincts : sur la même position,
le barème 1 démantèle en 5 ans (2,5 → 2 → 1,5 → 1 → 0,5 → 0) et le barème 2 en
10 ans (2,5 → 2,25 → … → 0). L'Union africaine les nomme « Schedule 1 - 5 year
Schedule » et « Schedule 2 - 10 year Schedule », et la carte des 48 origines
suit la distinction PMA / non-PMA en union douanière.

## Ce que l'Union africaine déclare — et ce que le dépôt en fait

**L'Union africaine ne qualifie pas ces barèmes d'offres en attente.** Sa notice,
citée mot pour mot dans les fichiers collectés :

> « Le Maroc a soumis son offre tarifaire, qui a été **adoptée et incluse dans la
> directive ministérielle** relative à la liste provisoire de concessions
> tarifaires. »

Sur les 52 entrées du portail, **45 portent cette même déclaration**. Une est
« provisoirement adoptée » (Angola), une « soumise » (Tunisie), une renvoie à
l'annexe 1 de la directive (Zimbabwe) ; les quatre dernières ne sont pas des
déclarations de statut mais des notices de composition (EAC, SACU, Afrique du
Sud) ou une légende de catégories (Mozambique).

Les instantanés portent désormais cette déclaration dans
`source_status_statement`, à côté du verdict du dépôt. Les deux doivent rester
distincts :

| | Position |
|---|---|
| **Union africaine** | Offre adoptée, incluse dans une directive ministérielle portant liste **provisoire** de concessions |
| **Dépôt** (`legal_effect_status`) | `OFFER_ONLY` — non exécutable seul |

Le dépôt est plus strict, et il a raison de l'être : une adoption provisoire au
niveau continental ne suffit pas à liquider un droit. Mais jusqu'ici seul son
verdict figurait dans les fichiers, ce qui laissait croire que la source
elle-même parlait d'une offre en attente. La nuance est désormais lisible sans
réinterroger l'API.

La matrice complète est dans
`backend/data/official_preferential/afcfta_status_matrix_2026-09-13.json`,
reproductible par `backend/scripts/build_afcfta_status_matrix.py`.

## L'étape qui manque : appliquer réellement

**Collecter un barème ne le rend pas applicable.** Le registre
`zlecaf_implementation_registry.py` exige quatre conditions cumulatives :

1. un instrument national ou régional d'application en vigueur ;
2. la liste officielle et réciproque des origines admises ;
3. un barème au niveau de la ligne tarifaire ;
4. la preuve d'origine ZLECAf, vérifiée en douane et non par l'application.

> **État au moment de la collecte, 13 septembre 2026.** Cette section décrit ce
> qui était établi ce jour-là. Elle a été dépassée le jour même par la
> vérification marocaine : `MAR_application_2026-09-13.json` établit
> l'instrument national (circulaire ADII 6530/223 du 22 janvier 2024, 158 pages
> lues) **et** les 40 origines admises, ce qui satisfait les conditions 1 et 2
> pour le Maroc. Les blocages marocains restants ne sont donc pas ceux listés
> ci-dessous, mais : la surcharge technique du sélecteur de barème par les
> listes P1/P2 — la carte de l'UA en désigne un autre pour 33 des 40 origines —,
> la restriction aux 40 origines nommées, et le traitement de la taxe
> parafiscale à l'importation. Le Zimbabwe, lui, reste bien à la seule
> condition 3.

Pour le Zimbabwe, **seule la condition 3 est remplie** ; pour le Maroc, la
vérification du jour même y ajoute les conditions 1 et 2 (voir l'encadré
ci-dessus).
Les deux destinations ont été inscrites dans `OFFER_DATASETS` : la décision
qu'elles produisent passe de `NOT_AVAILABLE` à `OFFER_ONLY` avec leur jeu de
données nommé. Ce n'est pas une application — c'est la différence entre
« aucune donnée » et « donnée collectée, portail juridique non franchi », deux
situations qui n'appellent pas le même travail.

État réel du calculateur après cette collecte :

| Destination | Statut | Ce qui manque |
|---|---|---|
| KEN | **`APPLIED`** | rien — 21 origines admises, Legal Notice EAC/321/2022 |
| ETH, ZMB, CIV, NGA | `PARTNER_NOTICE_REQUIRED` | la liste officielle des origines admises |
| CMR, EGY, GHA, RWA, TUN, **ZWE** | `OFFER_ONLY` | l'instrument national d'application **et** la liste des origines |
| **MAR** | `OFFER_ONLY` | instrument et origines désormais établis (voir l'encadré ci-dessus) ; reste la surcharge du sélecteur de barème P1/P2 |
| les 43 autres | `NOT_AVAILABLE` | le barème lui-même |

**Les deux documents que cette section réclamait ont été obtenus le jour même.**
Elle demandait l'instrument marocain d'application et la liste des origines
admises ; `MAR_application_2026-09-13.json` porte les deux, établis sur la
circulaire ADII 6530/223 du 22 janvier 2024 lue intégralement — 158 pages, 40
origines nommées en deux groupes. Relancer cette recherche juridique serait un
doublon.

Les blocages marocains réels, qui ne sont pas documentaires :

- **la surcharge du sélecteur de barème.** `official_preferential_rates.py`
  choisit le barème via la carte des origines de l'Union africaine, qui répartit
  selon le statut PMA ; les listes P1/P2 marocaines répartissent selon la
  réciprocité. Les deux divergent sur 33 des 40 origines ;
- **la restriction aux 40 origines nommées.** L'UA en mappe 48, dont 7 que le
  Maroc n'admet pas — les servir accorderait une préférence indue ;
- **le traitement de la taxe parafiscale à l'importation**, que la circulaire
  démantèle au même titre que le droit et que le calculateur ne traite pas.

Tant que ces trois points ne sont pas traités, le taux servi reste le NPF, et
c'est le comportement correct : une préférence mal calendée est aussi fausse
qu'une préférence non prouvée, et une absence de preuve n'est jamais convertie
en zéro.

## Corrections apportées au collecteur

- **Date de collecte codée en dur.** Le nom du fichier portait littéralement
  `2026-08-17` : un instantané pris aujourd'hui aurait affiché une date de
  collecte fausse. Un paramètre `--collected-at` la porte désormais, et son
  défaut est **la date du jour en UTC**. Garder la date d'août en défaut, comme
  c'était d'abord le cas, aurait daté du 17 août toute collecte future — le
  défaut même que ce paramètre existe pour empêcher, l'API ne pouvant reproduire
  une réponse passée à partir d'une date de nom de fichier. Reproduire un
  instantané existant demande donc de nommer sa date explicitement.
- **Déclaration de la source absente.** Les instantanés ne portaient que le
  verdict du dépôt. Ils portent maintenant aussi la notice de l'Union africaine
  et les intitulés officiels des barèmes.

## Reproduire

```bash
python3 backend/scripts/collect_afcfta_etariff_book.py \
    backend/data/official_preferential MAR ZWE --collected-at 2026-09-13

python3 backend/scripts/build_afcfta_status_matrix.py \
    backend/data/official_preferential --collected-at 2026-09-13
```
