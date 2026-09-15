# État d'application de la ZLECAf entre pays

> Généré par `scripts/build_bilateral_application_matrix.py` — ne pas éditer à la main.
> Données : `reports/ETAT_APPLICATION_BILATERAL.json`, générées le 2026-09-15.

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
| `ADMISSION_PAR_REGLE` | 96 | La destination admet les origines par un CRITÈRE et non par une liste nominative. La règle est citée ; elle n'est pas résolue ici, car ses termes sont ambigus et la résoudre par supposition accorderait une préférence que personne n'a constatée. |
| `DESTINATION_NON_ETABLIE` | 2213 | Aucune liste d'origines admises n'a été vérifiée pour cette destination. Absence de recherche, PAS un refus de préférence. |
| `MEME_PAYS` | 54 | Origine et destination confondues. |
| `NON_ACCORDEE` | 179 | La destination publie une liste nominative vérifiée et cette origine n'y figure pas : la préférence ne lui est pas accordée à ce jour. |
| `ORIGINE_NON_RATIFIANTE` | 265 | L'origine n'a pas déposé ses instruments de ratification : aucune préférence ZLECAf ne peut lui être accordée, quelle que soit la destination. |

Les 2213 couples `DESTINATION_NON_ETABLIE` sont le déficit d'information que
ce travail vise à combler. Ils ne signifient **pas** qu'il n'y a pas de préférence :
ils signifient que personne ne l'a vérifié. Les afficher comme tels, plutôt que de les
remplir par défaut, est le seul traitement honnête.

## Les destinations qui admettent par règle, non par liste

Une troisième forme, qu'il serait faux de confondre avec les deux autres : la
destination énonce un **critère** sans nommer personne. L'information est utile à
un opérateur, mais elle n'est pas résolue ici — la résoudre par supposition
accorderait une préférence que personne n'a constatée.

| Destination | Règle énoncée | Fondement | Pourquoi elle reste non résolue |
|---|---|---|---|
| **Ghana** (GHA) | « Only imports from State Parties will qualify for preferential import tariff as per Ghana's tariff offers. » | AfCFTA National Coordination Office du Ghana (afcftagh.org) | « State Parties » ne distingue pas les 50 pays ayant ratifié de ceux ayant gazetté leur barème et accordant la réciprocité. L'écart entre les deux lectures dépasse vingt pays. |
| **Nigeria** (NGA) | « Bénéfice réciproque avec les États parties ayant également gazetté leur barème de concessions tarifaires. » | communiqués de l'Union africaine et de l'administration nigériane | La liste se déduit alors de l'état de gazettage des autres États parties, qui évolue dans le temps : la réponse dépend de la date de l'importation. |

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

✅ préférence accordée · ❌ origine absente de la liste vérifiée · ◐ admission par règle, non résolue · · non établi · — même pays

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

## Ce qu'il reste à collecter

Publier un barème et publier la liste de ses partenaires sont deux actes distincts, et le second est rare.

Là où aucune liste n'est publiée, aucune source documentaire ne peut trancher : seule une preuve de terrain le peut — une déclaration en douane effectivement liquidée sous régime ZLECAf, avec son certificat d'origine. C'est ce que ce chantier prépare.

| Pays | Statut | Ce qui manque | Document à obtenir |
|---|---|---|---|
| **ETH** | `INSTRUMENT_VERIFIE_PRIMAIRE_ORIGINES_NON_VERIFIEES` | La liste des origines, que l'article 3(2) délègue à un avis du Ministry of Trade and Regional Integration. Sans cet avis, le barème ne s'applique à personne. | Avis (notification) du Ministry of Trade and Regional Integration listant les États membres admis, avec son numéro et sa date. |
| **CIV** | `NOTIFICATION_PARTENAIRES_REQUISE` | La liste nominative des partenaires acceptés. L'ordonnance pose la réciprocité en condition sans nommer aucun pays. | Arrêté ou circulaire de la Direction générale des douanes ivoiriennes désignant les origines admises ; à défaut, le texte intégral de l'ordonnance publié au Journal officiel de la République de Côte d'Ivoire. |
| **NGA** | `NOTIFICATION_PARTENAIRES_REQUISE` | Le texte de la gazette lui-même, et la confirmation que la règle de réciprocité y est bien formulée ainsi — la formulation connue provient de communiqués, non du texte. | Federal Republic of Nigeria Official Gazette portant la PSTC, avril 2025. |
| **ZMB** | `NOTIFICATION_PARTENAIRES_REQUISE` | Le texte du Statutory Instrument n° 92 de 2024. Son intitulé officiel est désormais établi en source primaire — « Customs and Excise (General) (Amendment) Regulations, 2024 » — et il ne nomme pas la ZLECAf : l'attribution reste à vérifier dans le texte, ainsi que toute liste d'origines. | Texte intégral du Statutory Instrument n° 92 of 2024, pour vérifier s'il comporte une liste d'États parties admis. |
| **GHA** | `OFFRE_SEULE` | L'acte national ghanéen lui-même, et toute liste d'origines. Le dépôt ne tient à ce jour que l'instantané CEDEAO du e-Tariff Book. | Legislative Instrument ou Customs (AfCFTA) Regulations du Ghana, et la circulaire d'application de la Ghana Revenue Authority. |
| **CMR** | `OFFRE_SEULE` | L'acte national camerounais d'application à l'IMPORTATION et sa liste d'origines. Ce qui est établi concerne l'exportation. | Circulaire ou note de service de la Direction générale des douanes du Cameroun portant application du tarif ZLECAf à l'importation. |
| **RWA** | `OFFRE_SEULE` | L'acte national et la liste des origines admises. Aucune liste officielle n'a été retrouvée. | Ministerial Order ou Customs Regulations rwandais portant application du barème ZLECAf, et la liste d'États parties admis. |

**Preuve recherchée** — Une déclaration en douane effectivement liquidée sous régime ZLECAf : code accord ou régime préférentiel utilisé, certificat d'origine ZLECAf accepté, taux appliqué, et le détail des autres prélèvements maintenus.

**Pourquoi elle tranche** — Elle établit d'un coup les trois conditions que les textes laissent ouvertes : que la destination admet cette origine, à quel rythme de démantèlement, et ce qui reste dû à côté du droit de douane.

**Précaution** — Une déclaration isolée prouve qu'un bureau a liquidé ainsi, pas que la règle est générale. Elle vaut indice fort, à recouper, et doit être consignée comme telle — jamais promue en source de droit.

## Méthode

Trois conditions, dans cet ordre : acte national d'application lu en source primaire ; liste nominative des origines qu'il admet ; confrontation à la carte continentale du e-Tariff Book. Les listes sont lues à leur source d'autorité dans le dépôt, jamais recopiées.

## Avertissement

La ratification est continentale, l'application est bilatérale. Une case ACCORDEE atteste que l'acte national de la destination nomme cette origine ; elle ne dispense ni de la preuve d'origine ZLECAf ni de la vérification en douane.
