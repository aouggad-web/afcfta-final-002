# Règle B EAC — méthode d'application de la ZLECAf pour les États de l'EAC

Décision du propriétaire, 27/09/2026. La règle B **remplace** la règle A (26/09/2026) pour les États de l'EAC.

## 1. La règle

Pour un État de l'EAC, le taux ZLECAf est servi si **quatre conditions** sont réunies **et documentées par des sources archivées (sha256)** :

1. **Ratification** : l'État a ratifié l'Accord ZLECAf (`zlecaf_membership_status`) ;
2. **TEC + EACCMA** : il applique le tarif extérieur commun et la loi douanière EACCMA. Citation requise, depuis le texte primaire du Traité EAC, de l'article sur la **primauté du droit communautaire (art. 8(4), à vérifier — voir §4)** ;
3. **GTI** : il figure parmi les participants au Guided Trade Initiative **selon le Secrétariat de la ZLECAf** (source primaire archivée ; tralac sert seulement à repérer) ;
4. **Aucune source contraire** : aucune source n'indique le contraire.

## 2. Périmètre de l'instrument

- **Instrument** : avis EAC/321/2022 (Gazette EAC, 06/09/2022).
- **Barème** : l'annexe de cet avis (`data/zlecaf_ken/bareme_categorie_a.json` — colonnes annuelles 2021-2030, catégorie A).
- **Origines** : celles de l'Annexe 1 de la Directive ministérielle 1/2021, **traitées comme un plafond** (même liste et mêmes réserves que le Kenya, `KENYA_ORIGINS_RESERVES`).
- **La liste GTI ne sert JAMAIS de liste d'origines** : elle sert seulement à la condition 3, pour l'État destination.
- **Seul le droit de douane est réduit** : tous les autres prélèvements nationaux restent dus.
- **Origine intra-EAC** : une origine membre de l'union douanière EAC relève du régime EAC (intra-union), jamais de la ZLECAf.

## 3. Tableau des huit États de l'EAC

Valeur de chaque condition. « à vérifier » = information non vérifiée à ce jour ; elle n'est pas inventée. (Ratifications lues dans `zlecaf_membership_status` le 27/09/2026.)

| État | C1 ratification | C2 TEC + EACCMA | C3 GTI (Secrétariat) | C4 source contraire | Verdict règle B |
|---|---|---|---|---|---|
| Kenya (KEN) | RATIFIED | OUI — barème KRA applique le TEC sous l'EACCMA | **OUI — source primaire du Secrétariat archivée** (communiqué du 19/10/2022 : Kenya parmi les huit États participants ; sha `d53bbbd6…`) ; « actively trading » (tralac 05/2025, repérage) | aucune trouvée | **satisfaite** (APPLIQUE, PR #533) |
| Tanzanie (TZA) | RATIFIED | OUI — TEC EAC 2022 publié par la TRA (**archivé**, sha `9d894c29…`) | **OUI — source primaire du Secrétariat archivée** (communiqué 19/10/2022, sha `d53bbbd6…` : Tanzanie parmi les huit participants) | aucune trouvée — l'omission dtic est mentionnée comme telle | **satisfaite** (APPLIQUE, PR #531) |
| Rwanda (RWA) | RATIFIED | OUI — TEC EAC 2022 publié par la RRA (**archivé**, sha `9d894c29…`, identique à la copie TRA) | **OUI — source primaire du Secrétariat archivée** (communiqué 19/10/2022, sha `d53bbbd6…` : Rwanda nommé parmi les huit participants) | aucune trouvée — la concordance dtic n'est pas une preuve | **satisfaite** (APPLIQUE, PR #534) |
| Ouganda (UGA) | RATIFIED | OUI — TEC EAC 2022 publié (CET 2022, 560 p.) | listé participant (KAS 30/10/2023, secondaire) ; **absent** de la liste « actively trading » (tralac 05/2025) ; **source primaire Secrétariat à archiver — à vérifier** | absence de la liste « active » — à apprécier, pas une contre-indication formelle | à vérifier (PR #535) |
| Burundi (BDI) | RATIFIED (Loi n°1/17 du 17/06/2021, BOB n°6ter/2021, archivée) | OUI — TEC EAC 2022 publié | phase 2 (KAS 30/10/2023, secondaire) ; **absent** de la liste « actively trading » (tralac 05/2025) ; **à vérifier (source primaire)** | absence de la liste « active » — à apprécier | à vérifier (PR #536) |
| Soudan du Sud (SSD) | **SIGNED_NOT_RATIFIED** — non ratifié (`ratification_status('SSD')`, codes ISO3) | à vérifier | à vérifier | — | **non satisfaite** (condition 1) |
| RD Congo (COD) | RATIFIED (service) | **application du TEC à établir** (membre EAC depuis 2022) | à vérifier | à vérifier | non établie |
| Somalie (SOM) | RATIFIED — **valeur par défaut du service (pays non listé)**, à confirmer sur la liste de statut du dépôt AU | **application du TEC à établir** | à vérifier | à vérifier | non établie |

## 4. Réserves et points à vérifier

- **Art. 8(4) du Traité EAC (primauté du droit communautaire)** : la clause est couramment citée sous ce numéro, mais le **texte primaire** n'a pas pu être téléchargé à ce jour (eac.int : 403 ; eacj.org et foreign.go.tz : téléchargements vides). **À vérifier depuis le texte primaire avant toute application.**
- **Condition 3** : la participation au GTI doit être établie par une **source primaire du Secrétariat de la ZLECAf, archivée (sha256)**. Les listes tralac/KAS/UNECA servent seulement à repérer. Sources candidates : communiqués du Secrétariat (au-afcfta.org), page pays par pays (`au-afcfta.org/countries-report/<iso>/`) — fichiers xlsx en 404 au 26-27/09/2026.
- **Soudan du Sud** : `ratification_status('SSD')` → SIGNED_NOT_RATIFIED — non ratifié (interrogé avec les codes ISO3, 27/09/2026).
- **Somalie** : le service renvoie RATIFIED **par défaut** (pays non listé dans ses ensembles) — à confirmer sur la liste de statut du dépôt AU.
- **RDC et Somalie** : l'application du TEC y est à établir (double appartenance/adhésion récente) ; aucune application de la règle B avant établissement.
- La liste GTI ne sert **jamais** de liste d'origines ; les origines restent celles de l'Annexe 1 de la Directive 1/2021 (plafond).
- Seul le droit de douane est réduit ; tous les autres prélèvements nationaux restent dus.

## 5. Application dans le code (étape 1)

- `DESTINATIONS_REGLE_B_EAC = frozenset({"KEN"})` — défini une seule fois dans `services/zlecaf_schedule_ken.py` ; les étapes suivantes y ajouteront les États prouvés (TZA puis RWA, UGA, BDI, chacun avec sa PR).
- `services/preference.py`, `services/official_preferential_rates.py` et `services/authentic_tariff_service.py` testent l'appartenance à cet ensemble (plus de `"KEN"` en dur).
- `ligne_du_journal_officiel` prend la destination en paramètre (`destination_iso3`).
- **Aucun changement de comportement** : tous les tests existants passent tels quels.
