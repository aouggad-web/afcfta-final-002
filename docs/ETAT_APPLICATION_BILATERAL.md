# État d'application de la ZLECAf entre pays

> Généré par `scripts/build_bilateral_application_matrix.py` — ne pas éditer à la main.
> Données : `reports/ETAT_APPLICATION_BILATERAL.json`, générées le 2026-09-14.

## Ce que ce tableau répond

Un opérateur ne demande pas « la ZLECAf est-elle en vigueur ? » mais « **puis-je
l'invoquer, moi, sur ce flux-là ?** ». La ratification est continentale, l'application
est bilatérale : chaque destination notifie sa propre liste d'origines admises, au
titre de la réciprocité. Le sens du flux change donc le droit.

## Ce qui est établi, et ce qui ne l'est pas

| | |
|---|---|
| Pays couverts | 54 |
| Couples possibles | 2916 |
| Destinations à liste vérifiée | **6** |
| Couples renseignés | **9.88 %** |

| État | Couples | Sens |
|---|---:|---|
| `ACCORDEE` | 109 | L'acte national de la destination nomme cette origine parmi celles qui bénéficient du tarif ZLECAf. |
| `DESTINATION_NON_ETABLIE` | 2309 | Aucune liste d'origines admises n'a été vérifiée pour cette destination. Absence de recherche, PAS un refus de préférence. |
| `MEME_PAYS` | 54 | Origine et destination confondues. |
| `NON_ACCORDEE` | 179 | La destination publie une liste nominative vérifiée et cette origine n'y figure pas : la préférence ne lui est pas accordée à ce jour. |
| `ORIGINE_NON_RATIFIANTE` | 265 | L'origine n'a pas déposé ses instruments de ratification : aucune préférence ZLECAf ne peut lui être accordée, quelle que soit la destination. |

Les 2309 couples `DESTINATION_NON_ETABLIE` sont le déficit d'information que
ce travail vise à combler. Ils ne signifient **pas** qu'il n'y a pas de préférence :
ils signifient que personne ne l'a vérifié. Les afficher comme tels, plutôt que de les
remplir par défaut, est le seul traitement honnête.

## Les 6 destinations établies

| Destination | Origines admises | Instrument | Niveau de preuve |
|---|---:|---|---|
| **Algérie** (DZA) | 9 | Circulaire 482/DGD/SP/D.042/24 du 22 octobre 2024 | primaire — texte intégral archivé |
| **Égypte** (EGY) | 17 | منشور اتفاقيات رقم 38 لسنة 2024 | primaire — PDF officiels douane égyptienne, OCR arabe |
| **Kenya** (KEN) | 21 | EAC/321/2022 | primaire (revue antérieure du dépôt) |
| **Maroc** (MAR) | 40 | Circulaire ADII n° 6530/223 du 2024-01-22 | primaire — circulaire lue intégralement, SHA-256 consigné |
| **Tunisie** (TUN) | 8 | Tarif Web 2026, douane.gov.tn | primaire — portail tarifaire officiel scellé dans le dépôt |
| **Afrique du Sud** (ZAF) | 14 | « Update on the AfCFTA », the dtic / SARS, newsletter mars 2026 | officielle — publication gouvernementale, non un acte réglementaire |

**Réserve — Tunisie** : Les origines sont établies, mais le SENS du taux préférentiel publié ne l'est pas (40 % affiché contre 36 % de NPF). Une case ACCORDEE dit ici que la Tunisie sert cette origine sous régime ZLECAf, pas quel droit en résulte.

**Réserve — Afrique du Sud** : Les membres de la SACU et de la SADC sont volontairement absents : l'Afrique du Sud échange avec eux sous ces régimes, pas sous la ZLECAf. Leur absence n'est donc pas un refus de préférence.

## Le tableau, entre destinations établies

Lecture : la **ligne** est le pays d'importation, la **colonne** le pays d'origine.

| Destination \ Origine | Algérie | Égypte | Kenya | Maroc | Tunisie | Afrique du Sud |
|---|---|---|---|---|---|---|
| **Algérie** | — | ✅ | ✅ | ❌ | ✅ | ✅ |
| **Égypte** | ✅ 5 ans | — | ✅ 10 ans | ✅ 5 ans | ✅ 5 ans | ✅ 10 ans |
| **Kenya** | ❌ | ❌ | — | ❌ | ❌ | ❌ |
| **Maroc** | ✅ 5 ans | ✅ 5 ans | ✅ 10 ans | — | ✅ 5 ans | ✅ 10 ans |
| **Tunisie** | ❌ | ❌ | ✅ | ❌ | — | ✅ |
| **Afrique du Sud** | ✅ | ✅ | ✅ | ✅ | ✅ | — |

✅ préférence accordée · ❌ origine absente de la liste vérifiée · — même pays

## Ce que le croisement révèle

**6 réciprocités confirmées** — les deux sens sont établis :

- Algérie ↔ Égypte
- Algérie ↔ Afrique du Sud
- Égypte ↔ Maroc
- Égypte ↔ Afrique du Sud
- Maroc ↔ Afrique du Sud
- Tunisie ↔ Afrique du Sud

**9 asymétries** — un sens accorde, l'autre non :

- **Algérie → Kenya** : DZA admet KEN à son tarif ZLECAf, KEN n'admet pas DZA.
- **Maroc → Algérie** : MAR admet DZA à son tarif ZLECAf, DZA n'admet pas MAR.
- **Algérie → Tunisie** : DZA admet TUN à son tarif ZLECAf, TUN n'admet pas DZA.
- **Égypte → Kenya** : EGY admet KEN à son tarif ZLECAf, KEN n'admet pas EGY.
- **Égypte → Tunisie** : EGY admet TUN à son tarif ZLECAf, TUN n'admet pas EGY.
- **Maroc → Kenya** : MAR admet KEN à son tarif ZLECAf, KEN n'admet pas MAR.
- **Tunisie → Kenya** : TUN admet KEN à son tarif ZLECAf, KEN n'admet pas TUN.
- **Afrique du Sud → Kenya** : ZAF admet KEN à son tarif ZLECAf, KEN n'admet pas ZAF.
- **Maroc → Tunisie** : MAR admet TUN à son tarif ZLECAf, TUN n'admet pas MAR.

Kenya est le receveur de 5 de ces 9 asymétries : ces pays l'admettent à leur tarif ZLECAf,
sa propre liste ne les admet pas. Un exportateur dans ce sens peut invoquer
la ZLECAf ; dans le sens inverse, en l'état des listes vérifiées, non.

Une asymétrie n'est pas nécessairement une faute : une liste peut simplement être
plus ancienne que l'autre. Elle signale où regarder ensuite.

## Contradictions entre sources primaires

Aucune : aucun acte national vérifié ne nomme une origine que le registre
continental donne pour non ratifiante.

## Méthode

Trois conditions, dans cet ordre : acte national d'application lu en source primaire ; liste nominative des origines qu'il admet ; confrontation à la carte continentale du e-Tariff Book. Les listes sont lues à leur source d'autorité dans le dépôt, jamais recopiées.

## Avertissement

La ratification est continentale, l'application est bilatérale. Une case ACCORDEE atteste que l'acte national de la destination nomme cette origine ; elle ne dispense ni de la preuve d'origine ZLECAf ni de la vérification en douane.
